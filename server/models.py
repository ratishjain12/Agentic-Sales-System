"""
Database models for the server
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum

class WorkflowStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class EmailStatus(str, Enum):
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    BOUNCED = "bounced"

class BusinessLead(BaseModel):
    """Business lead model"""
    id: Optional[str] = None
    name: str
    email: str
    phone: Optional[str] = None
    address: Optional[str] = None
    industry: Optional[str] = None
    business_type: Optional[str] = None
    website: Optional[str] = None
    confidence_score: Optional[float] = None
    source: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    additional_info: Optional[Dict[str, Any]] = None

class WorkflowExecution(BaseModel):
    """Workflow execution model"""
    id: Optional[str] = None
    business_data: BusinessLead
    status: WorkflowStatus
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    results: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    retry_count: int = 0

class EmailRecord(BaseModel):
    """Email record model"""
    id: Optional[str] = None
    to_email: str
    subject: str
    body: str
    status: EmailStatus
    sent_at: Optional[datetime] = None
    business_id: Optional[str] = None
    workflow_id: Optional[str] = None
    error_message: Optional[str] = None
    message_id: Optional[str] = None

class APIResponse(BaseModel):
    """Standard API response model"""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    timestamp: Optional[datetime] = None

class PaginatedResponse(BaseModel):
    """Paginated response model"""
    success: bool
    message: str
    data: List[Dict[str, Any]]
    total: int
    page: int
    page_size: int
    total_pages: int
