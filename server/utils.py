"""
Utility functions for the server
"""
import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class RateLimiter:
    """Simple rate limiter for API endpoints"""
    
    def __init__(self, max_requests: int, window_seconds: int):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = {}
    
    def is_allowed(self, client_id: str) -> bool:
        """Check if request is allowed based on rate limit"""
        now = datetime.now()
        window_start = now.timestamp() - self.window_seconds
        
        # Clean old requests
        if client_id in self.requests:
            self.requests[client_id] = [
                req_time for req_time in self.requests[client_id]
                if req_time > window_start
            ]
        else:
            self.requests[client_id] = []
        
        # Check rate limit
        if len(self.requests[client_id]) >= self.max_requests:
            return False
        
        # Add current request
        self.requests[client_id].append(now.timestamp())
        return True

def validate_business_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate and clean business data"""
    required_fields = ['name', 'email']
    
    for field in required_fields:
        if field not in data or not data[field]:
            raise ValueError(f"Missing required field: {field}")
    
    # Clean email
    data['email'] = data['email'].strip().lower()
    
    # Clean phone
    if 'phone' in data and data['phone']:
        data['phone'] = ''.join(filter(str.isdigit, data['phone']))
    
    return data

def format_api_response(
    success: bool,
    message: str,
    data: Optional[Dict[str, Any]] = None,
    error: Optional[str] = None
) -> Dict[str, Any]:
    """Format standard API response"""
    response = {
        "success": success,
        "message": message,
        "timestamp": datetime.now().isoformat()
    }
    
    if data:
        response["data"] = data
    
    if error:
        response["error"] = error
    
    return response

async def execute_with_timeout(coro, timeout: int = 300):
    """Execute coroutine with timeout"""
    try:
        return await asyncio.wait_for(coro, timeout=timeout)
    except asyncio.TimeoutError:
        logger.error(f"Operation timed out after {timeout} seconds")
        raise Exception(f"Operation timed out after {timeout} seconds")

def log_api_call(endpoint: str, method: str, client_ip: str, status_code: int):
    """Log API call details"""
    logger.info(f"API Call: {method} {endpoint} from {client_ip} - Status: {status_code}")

def sanitize_error_message(error: Exception) -> str:
    """Sanitize error messages for API responses"""
    error_msg = str(error)
    
    # Remove sensitive information
    sensitive_patterns = [
        'password', 'secret', 'key', 'token', 'credential'
    ]
    
    for pattern in sensitive_patterns:
        if pattern in error_msg.lower():
            error_msg = "Internal error occurred"
            break
    
    return error_msg
