"""
Workflow Step Tracker for Real-time Updates
Tracks workflow steps and sends updates to frontend via WebSocket
"""

import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
import json
import logging

logger = logging.getLogger(__name__)

class WorkflowStepTracker:
    """Tracks workflow steps and sends updates to frontend"""
    
    def __init__(self, session_id: str, websocket_manager=None):
        self.session_id = session_id
        self.websocket_manager = websocket_manager
        self.steps = []
        self.current_step = None
        self.progress = 0
        self.total_steps = 0
        
    async def start_step(self, step_name: str, message: str, data: Dict = None):
        """Start a new workflow step"""
        step = {
            "step": step_name,
            "status": "running",
            "message": message,
            "start_time": datetime.now().isoformat(),
            "data": data or {}
        }
        
        self.steps.append(step)
        self.current_step = step_name
        
        logger.info(f"Starting step: {step_name} - {message}")
        await self._send_update(step)
        
    async def complete_step(self, step_name: str, message: str, data: Dict = None):
        """Complete a workflow step"""
        step = {
            "step": step_name,
            "status": "completed",
            "message": message,
            "end_time": datetime.now().isoformat(),
            "data": data or {}
        }
        
        # Update the last step
        if self.steps:
            self.steps[-1].update(step)
        
        self.progress = min(100, self.progress + (100 / max(1, self.total_steps)))
        
        logger.info(f"Completed step: {step_name} - {message}")
        await self._send_update(step)
        
    async def fail_step(self, step_name: str, error_message: str, data: Dict = None):
        """Mark a step as failed"""
        step = {
            "step": step_name,
            "status": "failed",
            "message": error_message,
            "end_time": datetime.now().isoformat(),
            "data": data or {}
        }
        
        if self.steps:
            self.steps[-1].update(step)
            
        logger.error(f"Failed step: {step_name} - {error_message}")
        await self._send_update(step)
        
    async def update_step_progress(self, step_name: str, progress_percent: int, message: str = None):
        """Update progress within a step"""
        if self.steps and self.steps[-1]["step"] == step_name:
            self.steps[-1]["progress"] = progress_percent
            if message:
                self.steps[-1]["message"] = message
            
            await self._send_update(self.steps[-1])
        
    async def _send_update(self, step_data: Dict):
        """Send update to frontend via WebSocket"""
        update = {
            "session_id": self.session_id,
            **step_data,
            "progress": self.progress,
            "timestamp": datetime.now().isoformat(),
            "total_steps": len(self.steps),
            "current_step_index": len(self.steps) - 1
        }
        
        if self.websocket_manager:
            try:
                await self.websocket_manager.broadcast_to_session(
                    self.session_id, 
                    json.dumps(update)
                )
            except Exception as e:
                logger.error(f"Failed to send WebSocket update: {e}")
        
        # Also log the update
        logger.info(f"Step update: {step_data['step']} - {step_data['status']} - {step_data['message']}")
    
    def set_total_steps(self, total: int):
        """Set the total number of expected steps"""
        self.total_steps = total
        
    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of all steps"""
        return {
            "session_id": self.session_id,
            "total_steps": len(self.steps),
            "completed_steps": len([s for s in self.steps if s["status"] == "completed"]),
            "failed_steps": len([s for s in self.steps if s["status"] == "failed"]),
            "progress": self.progress,
            "steps": self.steps
        }
