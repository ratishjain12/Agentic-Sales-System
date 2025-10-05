"""
FastAPI Server for Sales Agent System
"""
from fastapi import FastAPI, HTTPException, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import asyncio
import os
import sys
import json
import uuid
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import agent modules
from main_agent import run_main_agent_workflow, run_main_agent_workflow_with_tracking
from workflow_step_tracker import WorkflowStepTracker

# Initialize FastAPI app
app = FastAPI(
    title="Sales Agent API",
    description="REST API for Sales Development Representative Agent System",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.workflow_sessions: Dict[str, Dict] = {}

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        try:
            await websocket.send_text(message)
        except:
            self.disconnect(websocket)

    async def broadcast_to_session(self, session_id: str, message: str):
        """Broadcast message to all connections following a specific session"""
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                self.disconnect(connection)

    def create_workflow_session(self, session_id: str, params: Dict[str, Any]):
        """Create a new workflow session"""
        self.workflow_sessions[session_id] = {
            "params": params,
            "status": "running",
            "current_step": "initializing",
            "progress": 0,
            "steps_completed": [],
            "created_at": datetime.now().isoformat()
        }

    def update_workflow_session(self, session_id: str, step: str, status: str, data: Dict = None):
        """Update workflow session progress"""
        if session_id in self.workflow_sessions:
            self.workflow_sessions[session_id].update({
                "current_step": step,
                "status": status,
                "progress": self.workflow_sessions[session_id]["progress"] + 10,
                "last_updated": datetime.now().isoformat()
            })
            if step not in self.workflow_sessions[session_id]["steps_completed"]:
                self.workflow_sessions[session_id]["steps_completed"].append(step)

manager = ConnectionManager()

# Pydantic models for request/response
class MainWorkflowRequest(BaseModel):
    """Main workflow request model"""
    city: str
    business_type: str = "restaurants"
    max_results: int = 3
    search_radius: int = 5000
    enable_sdr: bool = True

class MainWorkflowResponse(BaseModel):
    """Main workflow response model"""
    success: bool
    message: str
    session_id: str
    leads_count: int
    sdr_results: List[Dict[str, Any]]
    workflow_duration: float
    status: str
    timestamp: Optional[datetime] = None

class HealthResponse(BaseModel):
    status: str
    message: str
    version: str

# Health check endpoint
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        message="Sales Agent API is running",
        version="1.0.0"
    )

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Sales Agent API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
        "endpoints": {
            "main_workflow": "/api/v1/workflow/main",
            "main_workflow_stream": "/api/v1/workflow/main-stream",
            "main_workflow_async": "/api/v1/workflow/main-async",
            "websocket": "/ws",
            "agents_status": "/api/v1/agents/status",
            "leads_by_session": "/api/v1/leads/session/{session_id}",
            "all_leads": "/api/v1/leads/all",
            "leads_stats": "/api/v1/leads/stats"
        }
    }

# WebSocket endpoint for real-time updates
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time workflow updates"""
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive and handle client messages
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
                if message.get("type") == "ping":
                    await manager.send_personal_message(json.dumps({"type": "pong"}), websocket)
            except json.JSONDecodeError:
                pass
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# Streaming workflow endpoint
@app.post("/api/v1/workflow/main-stream")
async def start_main_workflow_stream(request: MainWorkflowRequest):
    """
    Start the main workflow with real-time streaming updates via Server-Sent Events
    """
    session_id = str(uuid.uuid4())
    
    async def generate_workflow_updates():
        try:
            # Create a real-time step tracker using asyncio.Queue
            class RealTimeStepTracker:
                def __init__(self, session_id: str, event_queue):
                    self.session_id = session_id
                    self.event_queue = event_queue
                    self.steps = []
                    self.progress = 0
                    self.total_steps = 0
                
                async def start_step(self, step_name: str, message: str, data: Dict = None):
                    step = {
                        "session_id": self.session_id,
                        "step": step_name,
                        "status": "running",
                        "message": message,
                        "timestamp": datetime.now().isoformat(),
                        "data": data or {}
                    }
                    self.steps.append(step)
                    # Send immediately to queue
                    await self.event_queue.put(step)
                    print(f"🚀 Step started: {step_name} - {message}")
                
                async def complete_step(self, step_name: str, message: str, data: Dict = None):
                    step = {
                        "session_id": self.session_id,
                        "step": step_name,
                        "status": "completed",
                        "message": message,
                        "timestamp": datetime.now().isoformat(),
                        "data": data or {}
                    }
                    if self.steps:
                        self.steps[-1].update(step)
                    # Send immediately to queue
                    await self.event_queue.put(step)
                    print(f"✅ Step completed: {step_name} - {message}")
                
                async def fail_step(self, step_name: str, error_message: str, data: Dict = None):
                    step = {
                        "session_id": self.session_id,
                        "step": step_name,
                        "status": "failed",
                        "message": error_message,
                        "timestamp": datetime.now().isoformat(),
                        "data": data or {}
                    }
                    if self.steps:
                        self.steps[-1].update(step)
                    # Send immediately to queue
                    await self.event_queue.put(step)
                    print(f"❌ Step failed: {step_name} - {error_message}")
                
                def set_total_steps(self, total: int):
                    self.total_steps = total
            
            # Send initial update
            initial_update = {
                "session_id": session_id,
                "step": "initializing",
                "status": "running",
                "message": "Starting main agent workflow...",
                "timestamp": datetime.now().isoformat(),
                "progress": 0,
                "data": request.dict()
            }
            yield f"data: {json.dumps(initial_update)}\n\n"
            
            # Create event queue for real-time communication
            event_queue = asyncio.Queue()
            step_tracker = RealTimeStepTracker(session_id, event_queue)
            
            # Start workflow execution in background
            async def run_workflow():
                try:
                    result = await run_main_agent_workflow_with_tracking(
                        city=request.city,
                        business_type=request.business_type,
                        max_results=request.max_results,
                        search_radius=request.search_radius,
                        step_tracker=step_tracker
                    )
                    # Signal completion
                    await event_queue.put({"type": "workflow_complete", "data": result})
                except Exception as e:
                    await event_queue.put({"type": "workflow_error", "error": str(e)})
            
            # Start workflow in background
            workflow_task = asyncio.create_task(run_workflow())
            
            # Process events from queue in real-time with non-blocking approach
            timeout_count = 0
            max_timeouts = 300  # 5 minutes max wait
            
            while True:
                try:
                    # Non-blocking check for events
                    try:
                        event = event_queue.get_nowait()
                        
                        # Reset timeout counter on successful event
                        timeout_count = 0
                        
                        if event.get("type") == "workflow_complete":
                            # Send final result
                            final_update = {
                                "session_id": session_id,
                                "step": "workflow_complete",
                                "status": "completed",
                                "message": "Main workflow completed successfully",
                                "progress": 100,
                                "timestamp": datetime.now().isoformat(),
                                "data": event["data"]
                            }
                            yield f"data: {json.dumps(final_update)}\n\n"
                            print(f"📡 Sending final event: {final_update['message']}")
                            break
                        elif event.get("type") == "workflow_error":
                            # Send error
                            error_update = {
                                "session_id": session_id,
                                "step": "workflow_error",
                                "status": "failed",
                                "message": f"Workflow failed: {event['error']}",
                                "timestamp": datetime.now().isoformat()
                            }
                            yield f"data: {json.dumps(error_update)}\n\n"
                            print(f"📡 Sending error event: {error_update['message']}")
                            break
                        else:
                            # Send step event immediately (REAL-TIME!)
                            yield f"data: {json.dumps(event)}\n\n"
                            print(f"📡 Sending step event: {event.get('step')} - {event.get('message')}")
                            
                    except asyncio.QueueEmpty:
                        # No events available, check if workflow is done
                        if workflow_task.done():
                            print(f"📡 Workflow task completed, ending stream")
                            break
                        
                        # Increment timeout counter
                        timeout_count += 1
                        if timeout_count >= max_timeouts:
                            print(f"📡 Max timeouts reached, ending stream")
                            break
                        
                        # Send heartbeat to keep connection alive
                        if timeout_count % 10 == 0:  # Every 10 timeouts (10 seconds)
                            heartbeat = {
                                "session_id": session_id,
                                "step": "heartbeat",
                                "status": "running",
                                "message": f"Workflow running... ({timeout_count}s elapsed)",
                                "timestamp": datetime.now().isoformat()
                            }
                            yield f"data: {json.dumps(heartbeat)}\n\n"
                            print(f"📡 Sending heartbeat: {timeout_count}s elapsed")
                        
                        # Short sleep to prevent busy waiting
                        await asyncio.sleep(0.1)
                        
                except Exception as e:
                    print(f"📡 Error in event processing: {str(e)}")
                    # Send error and break
                    error_update = {
                        "session_id": session_id,
                        "step": "stream_error",
                        "status": "failed",
                        "message": f"Stream error: {str(e)}",
                        "timestamp": datetime.now().isoformat()
                    }
                    yield f"data: {json.dumps(error_update)}\n\n"
                    break
            
            # Clean up
            if not workflow_task.done():
                workflow_task.cancel()
                
        except Exception as e:
            error_update = {
                "session_id": session_id,
                "step": "workflow_error",
                "status": "failed",
                "message": f"Workflow failed: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }
            yield f"data: {json.dumps(error_update)}\n\n"
    
    return StreamingResponse(
        generate_workflow_updates(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "*"
        }
    )

# Main Agent Workflow Endpoints
@app.post("/api/v1/workflow/main", response_model=MainWorkflowResponse)
async def start_main_workflow(request: MainWorkflowRequest):
    """
    Start the complete main agent workflow (Lead Finder + SDR)
    
    This is the primary endpoint that orchestrates the entire sales pipeline:
    1. Discovers business leads using Lead Finder
    2. Processes each lead through SDR workflow
    3. Returns comprehensive results
    
    Args:
        request: Main workflow parameters including city, business type, and SDR settings
        
    Returns:
        Complete workflow results including leads and SDR processing
    """
    try:
        start_time = datetime.now()
        
        # Execute main agent workflow
        result = await run_main_agent_workflow(
            city=request.city,
            business_type=request.business_type,
            max_results=request.max_results,
            search_radius=request.search_radius
        )
        
        execution_time = (datetime.now() - start_time).total_seconds()
        
        return MainWorkflowResponse(
            success=result.get("success", False),
            message=result.get("message", "Main workflow completed"),
            session_id=result.get("session_id", "unknown"),
            leads_count=result.get("leads_count", 0),
            sdr_results=result.get("sdr_results", []),
            workflow_duration=execution_time,
            status=result.get("status", "unknown"),
            timestamp=datetime.now()
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Main workflow failed: {str(e)}")

@app.post("/api/v1/workflow/main-async")
async def start_main_workflow_async(request: MainWorkflowRequest, background_tasks: BackgroundTasks):
    """
    Start the complete main agent workflow asynchronously
    
    This endpoint runs the same workflow as the synchronous version but in the background.
    Use this for long-running workflows to avoid timeout issues.
    
    Args:
        request: Main workflow parameters
        background_tasks: FastAPI background tasks
        
    Returns:
        Task ID for tracking the workflow progress
    """
    try:
        # Generate a task ID
        task_id = f"main_workflow_{request.city.replace(' ', '_').lower()}_{request.business_type}_{hash(str(request.dict()))}"
        
        # Add to background tasks
        background_tasks.add_task(execute_main_workflow_task, task_id, request.dict())
        
        return {
            "success": True,
            "message": "Main workflow started in background",
            "task_id": task_id,
            "status": "running",
            "workflow_type": "main_agent",
            "parameters": request.dict()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start main workflow: {str(e)}")

# Background task function for main workflow
async def execute_main_workflow_task(task_id: str, workflow_params: Dict[str, Any]):
    """Background task to execute main workflow"""
    try:
        result = await run_main_agent_workflow(
            city=workflow_params["city"],
            business_type=workflow_params["business_type"],
            max_results=workflow_params["max_results"],
            search_radius=workflow_params["search_radius"]
        )
        # In production, store result in database or cache
        print(f"Main workflow {task_id} completed: {result.get('status')}")
        print(f"Leads processed: {result.get('leads_count', 0)}")
    except Exception as e:
        print(f"Main workflow {task_id} failed: {str(e)}")

# Workflow Status Endpoint
@app.get("/api/v1/workflow/status/{session_id}")
async def get_workflow_status(session_id: str):
    """Get current status of a workflow session"""
    if session_id not in manager.workflow_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {
        "success": True,
        "session_id": session_id,
        "status": manager.workflow_sessions[session_id]
    }

# Lead Management Endpoints
@app.get("/api/v1/leads/session/{session_id}")
async def get_leads_by_session(session_id: str, limit: int = 10, offset: int = 0):
    """
    Get leads for a specific session ID
    
    Args:
        session_id: Session ID to filter leads
        limit: Maximum number of leads to return (default: 10)
        offset: Number of leads to skip for pagination (default: 0)
        
    Returns:
        List of leads for the specified session
    """
    try:
        from main_agent import get_stored_leads_from_mongodb
        
        # Get leads for the session
        leads = get_stored_leads_from_mongodb(session_id=session_id)
        
        # Apply pagination
        total_leads = len(leads)
        paginated_leads = leads[offset:offset + limit]
        
        return {
            "success": True,
            "session_id": session_id,
            "leads": paginated_leads,
            "pagination": {
                "total": total_leads,
                "limit": limit,
                "offset": offset,
                "has_more": offset + limit < total_leads
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch leads: {str(e)}")

@app.get("/api/v1/leads/all")
async def get_all_leads(limit: int = 50, offset: int = 0, with_email_only: bool = False):
    """
    Get all leads from MongoDB
    
    Args:
        limit: Maximum number of leads to return (default: 50)
        offset: Number of leads to skip for pagination (default: 0)
        with_email_only: If True, only return leads with valid emails (default: False)
        
    Returns:
        List of all leads with pagination
    """
    try:
        from leads_finder.database import get_business_leads_collection
        
        collection = get_business_leads_collection()
        
        # Build query
        query = {}
        if with_email_only:
            query["email"] = {"$nin": [None, "", "null", "N/A"]}
        
        # Get total count
        total_count = collection.count_documents(query)
        
        # Get leads with pagination
        leads = list(collection.find(query)
                    .sort("created_at", -1)
                    .skip(offset)
                    .limit(limit))
        
        # Convert ObjectId to string for JSON serialization
        for lead in leads:
            if "_id" in lead:
                lead["_id"] = str(lead["_id"])
        
        return {
            "success": True,
            "leads": leads,
            "pagination": {
                "total": total_count,
                "limit": limit,
                "offset": offset,
                "has_more": offset + limit < total_count
            },
            "filters": {
                "with_email_only": with_email_only
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch all leads: {str(e)}")

@app.get("/api/v1/leads/stats")
async def get_leads_stats():
    """
    Get statistics about leads in the database
    
    Returns:
        Lead statistics including counts by session, source, etc.
    """
    try:
        from leads_finder.database import get_business_leads_collection
        
        collection = get_business_leads_collection()
        
        # Get basic counts
        total_leads = collection.count_documents({})
        leads_with_email = collection.count_documents({"email": {"$nin": [None, "", "null", "N/A"]}})
        leads_without_email = total_leads - leads_with_email
        
        # Get counts by source
        source_stats = list(collection.aggregate([
            {"$group": {"_id": "$source", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]))
        
        # Get counts by session (recent sessions)
        session_stats = list(collection.aggregate([
            {"$group": {"_id": "$session_id", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 10}
        ]))
        
        # Get recent activity (last 7 days)
        from datetime import datetime, timedelta
        seven_days_ago = datetime.now() - timedelta(days=7)
        recent_leads = collection.count_documents({
            "created_at": {"$gte": seven_days_ago}
        })
        
        return {
            "success": True,
            "statistics": {
                "total_leads": total_leads,
                "leads_with_email": leads_with_email,
                "leads_without_email": leads_without_email,
                "recent_leads_7_days": recent_leads,
                "email_percentage": round((leads_with_email / total_leads * 100), 2) if total_leads > 0 else 0
            },
            "by_source": source_stats,
            "top_sessions": session_stats,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch lead statistics: {str(e)}")

# Agent Status Endpoints
@app.get("/api/v1/agents/status")
async def get_agents_status():
    """
    Get status of all agents and their configurations
    
    Returns:
        Agent status information
    """
    try:
        return {
            "success": True,
            "agents": {
                "email_sender": {
                    "status": "available",
                    "type": "OAuth2",
                    "sender_email": os.getenv("GMAIL_SENDER_EMAIL", "Not configured")
                },
                "sdr_main": {
                    "status": "available",
                    "description": "Main SDR workflow orchestrator"
                },
                "research": {
                    "status": "available",
                    "description": "Business research agent"
                },
                "proposal": {
                    "status": "available",
                    "description": "Proposal generation agents"
                },
                "calling": {
                    "status": "available",
                    "description": "Phone calling agent"
                }
            },
            "environment": {
                "gmail_configured": bool(os.getenv("GMAIL_CREDENTIALS_FILE")),
                "cerebras_configured": bool(os.getenv("CEREBRAS_API_KEY")),
                "mongodb_configured": bool(os.getenv("MONGODB_URI"))
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get agent status: {str(e)}")

# Error handlers
@app.exception_handler(404)
async def not_found_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={"success": False, "message": "Endpoint not found", "error": "404"}
    )

@app.exception_handler(500)
async def internal_error_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"success": False, "message": "Internal server error", "error": "500"}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)