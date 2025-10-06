from fastapi import FastAPI, Request, BackgroundTasks, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import hmac, hashlib, time, json
from typing import Optional

app = FastAPI(title="Webhook Receiver")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*", "null"],  # Allows all origins including null
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],  # Explicit methods
    allow_headers=[
        "accept",
        "accept-language", 
        "content-type",
        "origin",
        "priority",
        "sec-ch-ua",
        "sec-ch-ua-mobile", 
        "sec-ch-ua-platform",
        "sec-fetch-dest",
        "sec-fetch-mode",
        "sec-fetch-site",
        "user-agent",
        "x-signature",
        "x-timestamp"
    ],
)

# --- Optional: simple idempotency memory (use Redis/DB in prod) ---
PROCESSED_IDS: set[str] = set()

# --- Store events for polling (use Redis/DB in prod) ---
EVENTS_STORE: list[dict] = []

class Event(BaseModel):
    id: str
    type: str
    data: dict

def handle_event(event: Event):
    # Do your real work here (DB writes, API calls, etc.)
    # This runs *after* we've already returned 2xx to the sender.
    print(f"Processed {event.type=} {event.id=}")
    
    # Store event for polling
    event_data = {
        "id": event.id,
        "type": event.type,
        "data": event.data,
        "timestamp": time.time(),
        "processed": True
    }
    EVENTS_STORE.append(event_data)
    
    # Keep only last 100 events to prevent memory issues
    if len(EVENTS_STORE) > 100:
        EVENTS_STORE.pop(0)

@app.post("/webhook")
async def webhook(
    request: Request,
    background: BackgroundTasks,
    # Example header names—replace with your provider's actual headers:
    x_signature: Optional[str] = Header(default=None),
    x_timestamp: Optional[str] = Header(default=None),
):
    raw = await request.body()

    # --- Optional: verify HMAC signature (adjust to your provider's scheme) ---
    # Replace with your secret from the provider dashboard.
    secret = b"replace-with-your-webhook-secret"
    if x_signature:
        computed = hmac.new(secret, raw, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(computed, x_signature):
            raise HTTPException(status_code=400, detail="Invalid signature")
    if x_timestamp:
        try:
            ts = int(x_timestamp)
            if abs(time.time() - ts) > 300:  # 5 minutes drift
                raise HTTPException(status_code=400, detail="Stale timestamp")
        except ValueError:
            raise HTTPException(status_code=400, detail="Bad timestamp")

    # Parse after verification
    try:
        payload = json.loads(raw)
        event = Event.model_validate(payload)
    except Exception:
        raise HTTPException(status_code=400, detail="Bad payload")

    # Idempotency: skip duplicates
    if event.id in PROCESSED_IDS:
        return {"ok": True, "duplicate": True}
    PROCESSED_IDS.add(event.id)

    # Return quickly; process in the background
    background.add_task(handle_event, event)
    return {"ok": True}

@app.get("/webhook")
async def webhook_get(challenge: str | None = None):
    return {"challenge": challenge} if challenge else {"status": "ok"}

@app.options("/events")
async def events_options():
    """Handle preflight requests for /events endpoint"""
    return {"message": "OK"}

@app.options("/webhook")
async def webhook_options():
    """Handle preflight requests for /webhook endpoint"""
    return {"message": "OK"}

@app.get("/events")
async def get_events(since: Optional[str] = None, limit: int = 10):
    """
    Polling endpoint for frontend to get events
    - since: event ID to get events after (optional)
    - limit: max number of events to return (default 10)
    """
    events = EVENTS_STORE.copy()
    
    # Filter events after 'since' if provided
    if since:
        try:
            since_index = next(i for i, event in enumerate(events) if event["id"] == since)
            events = events[since_index + 1:]
        except StopIteration:
            # If 'since' not found, return all events
            pass
    
    # Limit results
    events = events[-limit:] if limit > 0 else events
    
    return {
        "events": events,
        "count": len(events),
        "total": len(EVENTS_STORE)
    }

@app.get("/events/latest")
async def get_latest_event():
    """Get the most recent event"""
    if not EVENTS_STORE:
        return {"event": None}
    
    return {"event": EVENTS_STORE[-1]}

@app.get("/debug")
async def debug_info():
    """Debug endpoint to check server status"""
    return {
        "status": "running",
        "total_events": len(EVENTS_STORE),
        "processed_ids": len(PROCESSED_IDS),
        "events": EVENTS_STORE
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
