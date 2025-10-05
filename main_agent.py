"""
Main Agent Orchestrator
Coordinates the leads finder and SDR components in a sequential workflow.
"""

import logging
import json
import re
from typing import Dict, Any, List, Optional
from datetime import datetime

# Import the components
from leads_finder.agent import find_leads, run_lead_finder_workflow
from sdr.agents.sdr_main_agent import execute_sdr_main_workflow

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MainAgentOrchestrator:
    """
    Main orchestrator that coordinates leads finder and SDR workflows.
    
    Workflow:
    1. Trigger leads finder to discover business leads
    2. Process leads finder results
    3. Trigger SDR workflow for each discovered lead
    4. Aggregate and return comprehensive results
    """
    
    def __init__(self):
        """Initialize the main orchestrator."""
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        logger.info(f"Initialized Main Agent Orchestrator with session ID: {self.session_id}")
    
    
    def execute_complete_workflow(self, city: str, business_type: str = "restaurants", 
                                max_results: int = 3, search_radius: int = 5000) -> Dict[str, Any]:
        """
        Execute the complete workflow: Leads Finder → SDR for each lead.
        
        Args:
            city: City name to search for business leads
            business_type: Type of business to search for
            max_results: Maximum number of leads to process
            search_radius: Search radius in meters
            
        Returns:
            Dictionary with comprehensive workflow results
        """
        logger.info(f"Starting complete workflow for {city} - {business_type}")
        
        workflow_results = {
            "session_id": self.session_id,
            "city": city,
            "business_type": business_type,
            "max_results": max_results,
            "search_radius": search_radius,
            "start_time": datetime.now().isoformat(),
            "leads_finder_results": None,
            "sdr_results": [],
            "summary": {},
            "status": "running"
        }
        
        try:
            # Step 1: Execute Leads Finder (this will store leads in MongoDB)
            logger.info("Step 1: Executing Leads Finder workflow")
            leads_result = self._execute_leads_finder(city, business_type, max_results, search_radius)
            workflow_results["leads_finder_results"] = leads_result
            
            if not leads_result.get("success", False):
                logger.error("Leads finder failed, stopping workflow")
                workflow_results["status"] = "failed"
                workflow_results["error"] = leads_result.get("error", "Unknown leads finder error")
                return workflow_results
            
            # Step 2: Get stored leads from MongoDB for SDR processing
            logger.info("Step 2: Retrieving stored leads from MongoDB")
            stored_leads = self._get_stored_leads_from_mongodb()
            
            if not stored_leads:
                logger.warning("No leads found in MongoDB")
                workflow_results["status"] = "completed"
                workflow_results["summary"] = {
                    "leads_found": 0,
                    "sdr_executions": 0,
                    "message": "No business leads found in MongoDB to process"
                }
                return workflow_results
            
            # Step 3: Execute SDR workflow for each stored lead
            logger.info(f"Step 3: Executing SDR workflow for {len(stored_leads)} businesses")
            sdr_results = []
            
            for i, business_data in enumerate(stored_leads[:max_results], 1):
                logger.info(f"Processing business {i}/{len(stored_leads)}: {business_data.get('name', 'Unknown')}")
                
                try:
                    # Prepare business data for SDR
                    sdr_business_data = self._prepare_business_data_for_sdr(business_data)
                    
                    # Execute SDR workflow
                    sdr_result = self._execute_sdr_workflow(sdr_business_data)
                    sdr_results.append(sdr_result)
                    
                    logger.info(f"SDR workflow completed for business {i}")
                    
                except Exception as e:
                    logger.error(f"SDR workflow failed for business {i}: {str(e)}")
                    sdr_results.append({
                        "business_data": business_data,
                        "status": "error",
                        "error": str(e)
                    })
            
            workflow_results["sdr_results"] = sdr_results
            
            # Step 4: Generate summary
            logger.info("Step 4: Generating workflow summary")
            workflow_results["summary"] = self._generate_workflow_summary(leads_result, sdr_results)
            workflow_results["status"] = "completed"
            workflow_results["end_time"] = datetime.now().isoformat()
            
            logger.info(f"Complete workflow finished successfully for {city} - {business_type}")
            return workflow_results
            
        except Exception as e:
            logger.error(f"Error in complete workflow: {str(e)}")
            workflow_results["status"] = "error"
            workflow_results["error"] = str(e)
            workflow_results["end_time"] = datetime.now().isoformat()
            return workflow_results
    
    def _get_stored_leads_from_mongodb(self) -> List[Dict[str, Any]]:
        """
        Retrieve stored leads from MongoDB.
        
        Returns:
            List of business data dictionaries from MongoDB
        """
        try:
            from leads_finder.database import get_business_leads_collection
            
            collection = get_business_leads_collection()
            
            # Get leads from the current session where email is not null
            leads = list(collection.find({
                "session_id": self.session_id,
                "email": {"$nin": [None, "", "null", "N/A"]}
            }).sort("created_at", -1).limit(3))
            
            # Convert ObjectId to string for JSON serialization
            for lead in leads:
                if "_id" in lead:
                    lead["_id"] = str(lead["_id"])
            
            logger.info(f"Retrieved {len(leads)} leads from MongoDB for session {self.session_id}")
            return leads
            
        except Exception as e:
            logger.error(f"Error retrieving leads from MongoDB: {str(e)}")
            return []
    
    def _execute_leads_finder(self, city: str, business_type: str, max_results: int, search_radius: int) -> Dict[str, Any]:
        """
        Execute the leads finder workflow.
        
        Args:
            city: City name to search
            business_type: Type of business to search for
            max_results: Maximum number of results
            search_radius: Search radius in meters
            
        Returns:
            Leads finder results dictionary
        """
        try:
            logger.info(f"Executing leads finder: {city} - {business_type} with session_id: {self.session_id}")
            # Pass session_id to the leads finder workflow
            result = run_lead_finder_workflow(city, business_type, max_results, search_radius, session_id=self.session_id)
            logger.info(f"Leads finder completed with success: {result.get('success', False)}")
            return result
            
        except Exception as e:
            logger.error(f"Leads finder execution failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "city": city,
                "business_type": business_type
            }
    
    def _prepare_business_data_for_sdr(self, business_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prepare business data for SDR workflow.
        
        Args:
            business_data: Raw business data from leads finder
            
        Returns:
            Formatted business data for SDR
        """
        return {
            "name": business_data.get("name", "Unknown Business"),
            "phone": business_data.get("phone", ""),
            "email": business_data.get("email", ""),
            "address": business_data.get("address", ""),
            "website": business_data.get("website", ""),
            "industry": business_data.get("category", business_data.get("business_type", "Local Business")),
            "description": f"{business_data.get('category', '')} business",
            "source": business_data.get("source", "leads_finder"),
            "rating": business_data.get("rating", None)
        }
    
    def _execute_sdr_workflow(self, business_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute SDR workflow for a single business.
        
        Args:
            business_data: Business data dictionary
            
        Returns:
            SDR workflow results
        """
        try:
            logger.info(f"Executing SDR workflow for: {business_data.get('name', 'Unknown')}")
            result = execute_sdr_main_workflow(business_data)
            logger.info(f"SDR workflow completed with status: {result.get('status', 'unknown')}")
            return result
            
        except Exception as e:
            logger.error(f"SDR workflow execution failed: {str(e)}")
            return {
                "business_data": business_data,
                "status": "error",
                "error": str(e)
            }
    
    def _generate_workflow_summary(self, leads_result: Dict[str, Any], sdr_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate a summary of the complete workflow.
        
        Args:
            leads_result: Results from leads finder
            sdr_results: List of SDR workflow results
            
        Returns:
            Summary dictionary
        """
        successful_sdr = [r for r in sdr_results if r.get("status") == "completed"]
        failed_sdr = [r for r in sdr_results if r.get("status") == "error"]
        
        # Count successful calls and emails
        successful_calls = 0
        successful_emails = 0
        
        for result in successful_sdr:
            if result.get("call_result") and "status" in str(result.get("call_result")):
                successful_calls += 1
            if result.get("email_result") and "sent" in str(result.get("email_result")).lower():
                successful_emails += 1
        
        return {
            "leads_found": len(sdr_results),
            "sdr_executions": len(sdr_results),
            "successful_sdr": len(successful_sdr),
            "failed_sdr": len(failed_sdr),
            "successful_calls": successful_calls,
            "successful_emails": successful_emails,
            "success_rate": len(successful_sdr) / len(sdr_results) if sdr_results else 0,
            "leads_finder_success": leads_result.get("success", False)
        }


# Create main orchestrator instance
main_orchestrator = MainAgentOrchestrator()


def run_main_agent_workflow(city: str, business_type: str = "restaurants", 
                          max_results: int = 3, search_radius: int = 5000) -> Dict[str, Any]:
    """
    Convenience function to run the main agent workflow.
    
    Args:
        city: City name to search for business leads
        business_type: Type of business to search for
        max_results: Maximum number of leads to process
        search_radius: Search radius in meters
        
    Returns:
        Dictionary with comprehensive workflow results
        
    Example:
        >>> results = run_main_agent_workflow("New York", "restaurants", 5)
        >>> print(f"Found {results['summary']['leads_found']} leads")
        >>> print(f"SDR success rate: {results['summary']['success_rate']:.2%}")
    """
    return main_orchestrator.execute_complete_workflow(city, business_type, max_results, search_radius)


if __name__ == "__main__":
    """Test the main agent orchestrator directly."""
    print("=== Main Agent Orchestrator Test ===")
    print("=" * 50)
    
    # Get parameters from user input
    print("\n📝 Enter Workflow Parameters:")
    city = input("City name (e.g., 'New York', 'Ahmedabad'): ").strip()
    business_type = input("Business type (e.g., 'restaurants', 'cafes'): ").strip() or "restaurants"
    
    try:
        max_results = int(input("Max results to process (default: 3): ").strip() or "3")
        search_radius = int(input("Search radius in meters (default: 5000): ").strip() or "5000")
    except ValueError:
        print("Invalid input. Using defaults.")
        max_results, search_radius = 3, 5000
    
    if not city:
        print("City name is required.")
        exit(1)
    
    print(f"\n🚀 Starting Complete Workflow...")
    print(f"City: {city}")
    print(f"Business Type: {business_type}")
    print(f"Max Results: {max_results}")
    print(f"Search Radius: {search_radius}m")
    print("\nWorkflow: Leads Finder → SDR for each lead")
    
    try:
        # Execute the complete workflow
        results = run_main_agent_workflow(city, business_type, max_results, search_radius)
        
        print(f"\n📊 Workflow Results:")
        print(f"Session ID: {results.get('session_id')}")
        print(f"Status: {results.get('status')}")
        
        if results.get('summary'):
            summary = results['summary']
            print(f"\n📈 Summary:")
            print(f"  Leads Found: {summary.get('leads_found', 0)}")
            print(f"  SDR Executions: {summary.get('sdr_executions', 0)}")
            print(f"  Successful SDR: {summary.get('successful_sdr', 0)}")
            print(f"  Failed SDR: {summary.get('failed_sdr', 0)}")
            print(f"  Success Rate: {summary.get('success_rate', 0):.2%}")
            print(f"  Successful Calls: {summary.get('successful_calls', 0)}")
            print(f"  Successful Emails: {summary.get('successful_emails', 0)}")
        
        if results.get('error'):
            print(f"\n❌ Error: {results['error']}")
        
        print(f"\n🎉 Main Agent Orchestrator test completed!")
        
    except Exception as e:
        print(f"❌ Error in main workflow: {e}")
        import traceback
        traceback.print_exc()
