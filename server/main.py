"""
FastAPI Server for Sales Agent System
"""
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import asyncio
import os
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import agent modules
from main_agent import run_main_agent_workflow
from models import MainWorkflowRequest, MainWorkflowResponse

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
            "main_workflow_async": "/api/v1/workflow/main-async",
            "agents_status": "/api/v1/agents/status"
        }
    }

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
        result = run_main_agent_workflow(
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
        result = run_main_agent_workflow(
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
