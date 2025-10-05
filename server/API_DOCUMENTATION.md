# Sales Agent API Documentation

## Overview

The Sales Agent API provides a simplified REST interface for the Main Agent Workflow system. This API orchestrates the complete sales pipeline by combining Lead Finder and SDR workflows into a single, comprehensive endpoint.

## Base URL

```
http://localhost:8000
```

## Endpoints

### 1. Health Check

**GET** `/health`

Check if the API is running and healthy.

**Response:**
```json
{
  "status": "healthy",
  "message": "Sales Agent API is running",
  "version": "1.0.0"
}
```

### 2. Main Workflow (Synchronous)

**POST** `/api/v1/workflow/main`

Start the complete main agent workflow that orchestrates the entire sales pipeline:
1. **Lead Discovery**: Uses Lead Finder to discover business leads
2. **SDR Processing**: Processes each lead through the complete SDR workflow
3. **Comprehensive Results**: Returns detailed results from both workflows

**Request Body:**
```json
{
  "city": "New York",
  "business_type": "restaurants",
  "max_results": 3,
  "search_radius": 5000,
  "enable_sdr": true
}
```

**Parameters:**
- `city` (string, required): City name to search for leads
- `business_type` (string, optional): Type of business to find (default: "restaurants")
- `max_results` (integer, optional): Maximum number of leads to process (default: 3)
- `search_radius` (integer, optional): Search radius in meters (default: 5000)
- `enable_sdr` (boolean, optional): Enable SDR workflow for found leads (default: true)

**Response:**
```json
{
  "success": true,
  "message": "Main workflow completed",
  "session_id": "20241220_143022",
  "leads_count": 3,
  "sdr_results": [
    {
      "business_name": "The Coffee Shop",
      "status": "completed",
      "research_completed": true,
      "proposal_generated": true,
      "phone_call_made": true,
      "email_sent": true,
      "conversation_classification": "interested"
    }
  ],
  "workflow_duration": 180.5,
  "status": "completed",
  "timestamp": "2024-12-20T14:30:22Z"
}
```

### 3. Main Workflow (Asynchronous)

**POST** `/api/v1/workflow/main-async`

Start the complete main agent workflow asynchronously.

**Request Body:**
```json
{
  "city": "San Francisco",
  "business_type": "cafes",
  "max_results": 2,
  "search_radius": 3000,
  "enable_sdr": true
}
```

**Response:**
```json
{
  "success": true,
  "message": "Main workflow started in background",
  "task_id": "main_workflow_san_francisco_cafes_12345",
  "status": "running",
  "workflow_type": "main_agent",
  "parameters": {
    "city": "San Francisco",
    "business_type": "cafes",
    "max_results": 2,
    "search_radius": 3000,
    "enable_sdr": true
  }
}
```

### 4. Agent Status

**GET** `/api/v1/agents/status`

Get status of all agents and their configurations.

**Response:**
```json
{
  "success": true,
  "agents": {
    "email_sender": {
      "status": "available",
      "type": "OAuth2",
      "sender_email": "ratishjain10@gmail.com"
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
    "gmail_configured": true,
    "cerebras_configured": true,
    "mongodb_configured": true
  }
}
```

## Usage Examples

### cURL Example

```bash
# Main Workflow
curl -X POST "http://localhost:8000/api/v1/workflow/main" \
  -H "Content-Type: application/json" \
  -d '{
    "city": "New York",
    "business_type": "restaurants",
    "max_results": 3,
    "search_radius": 5000,
    "enable_sdr": true
  }'
```

### Python Example

```python
import requests

payload = {
    "city": "New York",
    "business_type": "restaurants",
    "max_results": 3,
    "search_radius": 5000,
    "enable_sdr": True
}

response = requests.post("http://localhost:8000/api/v1/workflow/main", json=payload)
data = response.json()

if data["success"]:
    print(f"Processed {data['leads_count']} leads")
    for result in data["sdr_results"]:
        print(f"- {result['business_name']}: {result['status']}")
```

## Error Responses

All endpoints return standardized error responses:

```json
{
  "detail": "Error message describing what went wrong"
}
```

**Common HTTP Status Codes:**
- `200`: Success
- `400`: Bad Request (invalid parameters)
- `500`: Internal Server Error

## Production Considerations

1. **Authentication**: Implement API key or OAuth2 authentication
2. **Rate Limiting**: Add rate limiting to prevent abuse
3. **Logging**: Implement comprehensive logging and monitoring
4. **Error Handling**: Add retry mechanisms and circuit breakers
5. **Database**: Use production MongoDB with proper indexing
6. **Security**: Implement HTTPS and input validation
7. **Scaling**: Consider using a task queue (Redis/Celery) for async workflows
