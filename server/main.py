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

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import agent modules
from sdr.agents.sdr_main_agent import execute_sdr_main_workflow
from sdr.agents.outreach_email_agent.sub_agents.email_sender.email_agent import send_outreach_email
from sdr.tools.email_sender_tool import email_sender_tool

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
class BusinessData(BaseModel):
    name: str
    email: str
    phone: Optional[str] = None
    address: Optional[str] = None
    industry: Optional[str] = None
    business_type: Optional[str] = None
    website: Optional[str] = None
    additional_info: Optional[Dict[str, Any]] = None

class EmailRequest(BaseModel):
    to_email: str
    subject: str
    body: str
    is_html: bool = True

class EmailAgentRequest(BaseModel):
    business_data: BusinessData
    research_result: str
    proposal: str

class LeadSearchRequest(BaseModel):
    location: str
    business_type: Optional[str] = None
    radius: Optional[int] = 1000
    limit: Optional[int] = 20

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
            "leads": "/api/v1/leads",
            "email": "/api/v1/email",
            "workflow": "/api/v1/workflow"
        }
    }

# Lead Management Endpoints
@app.post("/api/v1/leads/search")
async def search_leads(request: LeadSearchRequest):
    """
    Search for business leads in a specific location
    
    Args:
        request: Lead search parameters
        
    Returns:
        List of found leads
    """
    try:
        # This would integrate with your leads_finder module
        # For now, returning a mock response
        return {
            "success": True,
            "message": "Lead search completed",
            "leads": [
                {
                    "name": "Sample Business",
                    "email": "contact@samplebusiness.com",
                    "phone": "+1-555-0123",
                    "address": "123 Main St, City, State",
                    "industry": request.business_type or "General",
                    "confidence_score": 0.85
                }
            ],
            "total_found": 1,
            "search_params": request.dict()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lead search failed: {str(e)}")

# Email Endpoints
@app.post("/api/v1/email/send")
async def send_email(request: EmailRequest):
    """
    Send a single email using the email sender tool
    
    Args:
        request: Email details
        
    Returns:
        Email sending result
    """
    try:
        result = email_sender_tool.send_email(
            to_email=request.to_email,
            subject=request.subject,
            body=request.body,
            is_html=request.is_html
        )
        
        return {
            "success": result.get("success", False),
            "message": result.get("message", "Unknown error"),
            "to_email": request.to_email,
            "subject": request.subject
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Email sending failed: {str(e)}")

@app.post("/api/v1/email/send-agent")
async def send_email_with_agent(request: EmailAgentRequest):
    """
    Send email using the email agent system (crafter + sender)
    
    Args:
        request: Business data, research, and proposal
        
    Returns:
        Email agent result
    """
    try:
        result = send_outreach_email(
            business_data=request.business_data.dict(),
            research_result=request.research_result,
            proposal=request.proposal
        )
        
        return {
            "success": result.get("success", False),
            "message": result.get("message", "Unknown error"),
            "business_name": result.get("business_name"),
            "email": result.get("email"),
            "result": result.get("result")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Email agent failed: {str(e)}")

# Workflow Endpoints
@app.post("/api/v1/workflow/execute")
async def execute_workflow(request: BusinessData, background_tasks: BackgroundTasks):
    """
    Execute the complete SDR workflow for a business
    
    Args:
        request: Business information
        background_tasks: FastAPI background tasks
        
    Returns:
        Workflow execution result
    """
    try:
        # Convert to dict for the workflow
        business_data = request.dict()
        
        # Execute workflow (this might take a while)
        result = execute_sdr_main_workflow(business_data)
        
        return {
            "success": result.get("status") == "completed",
            "message": "SDR workflow completed",
            "business_data": business_data,
            "results": {
                "research": result.get("research_result"),
                "proposal": result.get("proposal_result"),
                "call": result.get("call_result"),
                "classification": result.get("classification_result"),
                "email": result.get("email_result")
            },
            "workflow_status": result.get("status")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Workflow execution failed: {str(e)}")

@app.post("/api/v1/workflow/execute-async")
async def execute_workflow_async(request: BusinessData, background_tasks: BackgroundTasks):
    """
    Execute the complete SDR workflow asynchronously
    
    Args:
        request: Business information
        background_tasks: FastAPI background tasks
        
    Returns:
        Task ID for tracking
    """
    try:
        business_data = request.dict()
        
        # Generate a task ID (in production, use a proper task queue)
        task_id = f"workflow_{business_data['name'].replace(' ', '_').lower()}_{hash(str(business_data))}"
        
        # Add to background tasks
        background_tasks.add_task(execute_workflow_task, task_id, business_data)
        
        return {
            "success": True,
            "message": "Workflow started in background",
            "task_id": task_id,
            "status": "running"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start workflow: {str(e)}")

# Background task function
async def execute_workflow_task(task_id: str, business_data: Dict[str, Any]):
    """Background task to execute workflow"""
    try:
        result = execute_sdr_main_workflow(business_data)
        # In production, store result in database or cache
        print(f"Workflow {task_id} completed: {result.get('status')}")
    except Exception as e:
        print(f"Workflow {task_id} failed: {str(e)}")

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
