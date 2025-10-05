"""
Main Agent Orchestrator for Sales Development Representative System
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import workflow functions
from leads_finder.agent import run_lead_finder_workflow
from sdr.agents.sdr_main_agent import execute_sdr_main_workflow

class MainAgentOrchestrator:
    """
    Main orchestrator for the complete sales agent workflow.
    
    This class coordinates the entire sales pipeline:
    1. Lead Discovery (Lead Finder Agent)
    2. Lead Processing (SDR Agent for each lead)
    3. Results aggregation and reporting
    """
    
    def __init__(self, session_id: str = None):
        self.session_id = session_id or str(uuid.uuid4())
        logger.info(f"MainAgentOrchestrator initialized with session_id: {self.session_id}")
    
    async def execute_complete_workflow(
        self, 
        city: str, 
        business_type: str = "restaurants", 
        max_results: int = 3, 
        search_radius: int = 5000
    ) -> Dict[str, Any]:
        """
        Execute the complete sales agent workflow.
        
        Args:
            city: City name to search for business leads
            business_type: Type of business to search for
            max_results: Maximum number of leads to process
            search_radius: Search radius in meters
            
        Returns:
            Dictionary with complete workflow results
        """
        logger.info(f"Starting complete workflow for {city} - {business_type}")
        
        try:
            # Step 1: Lead Discovery
            logger.info("Step 1: Starting lead discovery")
            leads_result = self._execute_lead_discovery(city, business_type, max_results, search_radius)
            
            if not leads_result.get("success", False):
                return {
                    "success": False,
                    "error": "Lead discovery failed",
                    "session_id": self.session_id,
                    "leads_count": 0,
                    "sdr_results": []
                }
            
            # Step 2: Retrieve stored leads
            logger.info("Step 2: Retrieving stored leads")
            stored_leads = self._get_stored_leads_from_mongodb()
            
            if not stored_leads:
                logger.warning("No stored leads found, workflow cannot continue")
                return {
                    "success": False,
                    "error": "No leads found in database",
                    "session_id": self.session_id,
                    "leads_count": 0,
                    "sdr_results": []
                }
            
            # Step 3: SDR Processing
            logger.info(f"Step 3: Starting SDR processing for {len(stored_leads)} leads")
            sdr_results = await self._execute_sdr_processing(stored_leads)
            
            # Step 4: Generate summary
            logger.info("Step 4: Generating workflow summary")
            summary = self._generate_workflow_summary(leads_result, sdr_results)
            
            return {
                "success": True,
                "message": "Complete workflow executed successfully",
                "session_id": self.session_id,
                "leads_count": len(stored_leads),
                "sdr_results": sdr_results,
                "summary": summary,
                "status": "completed"
            }
            
        except Exception as e:
            logger.error(f"Workflow execution failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "session_id": self.session_id,
                "leads_count": 0,
                "sdr_results": []
            }
    
    def _execute_lead_discovery(
        self, 
        city: str, 
        business_type: str, 
        max_results: int, 
        search_radius: int
    ) -> Dict[str, Any]:
        """Execute lead discovery using the Lead Finder Agent."""
        try:
            result = run_lead_finder_workflow(
                city=city,
                business_type=business_type,
                max_results=max_results,
                search_radius=search_radius,
                session_id=self.session_id
            )
            
            logger.info(f"Lead discovery completed: {result.get('leads_found', 0)} leads found")
            return result
            
        except Exception as e:
            logger.error(f"Lead discovery failed: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def _get_stored_leads_from_mongodb(self) -> List[Dict[str, Any]]:
        """Retrieve stored leads from MongoDB for the current session."""
        try:
            from leads_finder.database import get_business_leads_collection
            
            collection = get_business_leads_collection()
            
            # Query for leads from current session
            query = {"session_id": self.session_id}
            leads = list(collection.find(query).sort("created_at", -1).limit(3))
            
            logger.info(f"Retrieved {len(leads)} leads from MongoDB for session {self.session_id}")
            return leads
            
        except Exception as e:
            logger.error(f"Error retrieving leads from MongoDB: {str(e)}")
            return []
    
    async def _execute_sdr_processing(self, leads: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Execute SDR processing for each lead."""
        sdr_results = []
        
        for i, lead in enumerate(leads):
            try:
                logger.info(f"Processing SDR for lead {i+1}/{len(leads)}: {lead.get('name', 'Unknown')}")
                
                result = await execute_sdr_main_workflow(lead)
                sdr_results.append(result)
                
                logger.info(f"SDR processing completed for lead {i+1}")
                
            except Exception as e:
                logger.error(f"SDR processing failed for lead {i+1}: {str(e)}")
                sdr_results.append({
                    "status": "error",
                    "error": str(e),
                    "lead_name": lead.get('name', 'Unknown')
                })
        
        return sdr_results
    
    def _generate_workflow_summary(self, leads_result: Dict[str, Any], sdr_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate a summary of the workflow execution."""
        successful_sdr = len([r for r in sdr_results if r.get("status") == "completed"])
        failed_sdr = len([r for r in sdr_results if r.get("status") == "error"])
        
        return {
            "leads_found": leads_result.get("leads_found", 0),
            "leads_processed": len(sdr_results),
            "sdr_successful": successful_sdr,
            "sdr_failed": failed_sdr,
            "success_rate": (successful_sdr / len(sdr_results) * 100) if sdr_results else 0,
            "message": f"Processed {len(sdr_results)} businesses with {successful_sdr} successful SDR executions"
        }


async def run_main_agent_workflow(
    city: str, 
    business_type: str = "restaurants", 
    max_results: int = 3, 
    search_radius: int = 5000
) -> Dict[str, Any]:
    """
    Run the main agent workflow without tracking.
    
    Args:
        city: City name to search for business leads
        business_type: Type of business to search for
        max_results: Maximum number of leads to process
        search_radius: Search radius in meters
        
    Returns:
        Dictionary with workflow results
    """
    orchestrator = MainAgentOrchestrator()
    return await orchestrator.execute_complete_workflow(city, business_type, max_results, search_radius)


async def run_main_agent_workflow_with_tracking(
    city: str, 
    business_type: str = "restaurants", 
    max_results: int = 3, 
    search_radius: int = 5000,
    step_tracker = None
) -> Dict[str, Any]:
    """
    Run the main agent workflow with step tracking for real-time updates.
    
    Args:
        city: City name to search for business leads
        business_type: Type of business to search for
        max_results: Maximum number of leads to process
        search_radius: Search radius in meters
        step_tracker: WorkflowStepTracker instance for real-time updates
        
    Returns:
        Dictionary with workflow results
    """
    logger.info(f"Starting main agent workflow with tracking for {city} - {business_type}")
    
    workflow_results = {
        "session_id": step_tracker.session_id if step_tracker else "unknown",
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
        # Set total steps for progress tracking
        if step_tracker:
            step_tracker.set_total_steps(5 + max_results * 4)  # 5 main steps + 4 SDR steps per business
        
        # Step 1: Lead Discovery
        if step_tracker:
            await step_tracker.start_step(
                "lead_discovery", 
                f"Discovering {business_type} businesses in {city}...",
                {"city": city, "business_type": business_type, "max_results": max_results}
            )
        
        leads_result = await run_lead_finder_workflow(
            city=city,
            business_type=business_type,
            max_results=max_results,
            search_radius=search_radius,
            session_id=step_tracker.session_id if step_tracker else None
        )
        
        workflow_results["leads_finder_results"] = leads_result
        
        if step_tracker:
            if leads_result.get("success", False):
                await step_tracker.complete_step(
                    "lead_discovery",
                    f"Found {leads_result.get('leads_found', 0)} business leads",
                    {"leads_found": leads_result.get('leads_found', 0)}
                )
            else:
                await step_tracker.fail_step(
                    "lead_discovery",
                    "Failed to discover leads",
                    {"error": leads_result.get("error", "Unknown error")}
                )
                workflow_results["status"] = "failed"
                workflow_results["error"] = leads_result.get("error", "Unknown error")
                return workflow_results
        
        # Step 2: Wait for MongoDB Upload Completion (with shorter timeout)
        if step_tracker:
            await step_tracker.start_step(
                "wait_for_upload",
                "Waiting for database upload to complete..."
            )
        
        # Wait for MongoDB upload to complete with comprehensive verification
        upload_completed = False
        if step_tracker and step_tracker.session_id:
            upload_completed = wait_for_mongodb_upload_completion(step_tracker.session_id, max_wait_seconds=30)
            if step_tracker:
                if upload_completed:
                    await step_tracker.complete_step(
                        "wait_for_upload",
                        "Database upload completed successfully"
                    )
                else:
                    await step_tracker.complete_step(
                        "wait_for_upload",
                        "Database upload timeout - proceeding with retrieval"
                    )
        
        # Step 3: Retrieve Leads from MongoDB
        if step_tracker:
            await step_tracker.start_step(
                "retrieve_leads",
                "Retrieving stored leads from database..."
            )
        
        stored_leads = get_stored_leads_from_mongodb(step_tracker.session_id if step_tracker else None)
        
        if step_tracker:
            await step_tracker.complete_step(
                "retrieve_leads",
                f"Retrieved {len(stored_leads)} leads from database",
                {"leads_retrieved": len(stored_leads)}
            )
        
        if not stored_leads:
            workflow_results["status"] = "completed"
            workflow_results["summary"] = {"leads_found": 0, "message": "No leads found"}
            if step_tracker:
                await step_tracker.complete_step(
                    "workflow_complete",
                    "Workflow completed - no leads to process",
                    {"leads_found": 0}
                )
            return workflow_results
        
        # Step 4: SDR Processing
        if step_tracker:
            await step_tracker.start_step(
                "sdr_processing",
                f"Processing SDR for {len(stored_leads)} businesses..."
            )
        
        sdr_results = []
        for i, lead in enumerate(stored_leads):
            try:
                if step_tracker:
                    await step_tracker.start_step(
                        f"sdr_business_{i+1}",
                        f"Processing SDR for business {i+1}/{len(stored_leads)}: {lead.get('name', 'Unknown')}"
                    )
                
                sdr_result = await execute_sdr_main_workflow(lead, step_tracker)
                sdr_results.append(sdr_result)
                
                if step_tracker:
                    await step_tracker.complete_step(
                        f"sdr_business_{i+1}",
                        f"SDR completed for {lead.get('name', 'Unknown')}",
                        {"status": sdr_result.get("status", "unknown")}
                    )
                
            except Exception as e:
                logger.error(f"SDR processing failed for business {i+1}: {str(e)}")
                sdr_results.append({
                    "status": "error",
                    "error": str(e),
                    "lead_name": lead.get('name', 'Unknown')
                })
                
                if step_tracker:
                    await step_tracker.fail_step(
                        f"sdr_business_{i+1}",
                        f"SDR failed for {lead.get('name', 'Unknown')}: {str(e)}"
                    )
        
        workflow_results["sdr_results"] = sdr_results
        
        if step_tracker:
            await step_tracker.complete_step(
                "sdr_processing",
                f"SDR processing completed for {len(stored_leads)} businesses",
                {"sdr_results": len(sdr_results)}
            )
        
        # Step 5: Generate Summary
        summary = generate_workflow_summary(leads_result, sdr_results)
        workflow_results["summary"] = summary
        workflow_results["status"] = "completed"
        workflow_results["end_time"] = datetime.now().isoformat()
        
        if step_tracker:
            await step_tracker.complete_step(
                "workflow_complete",
                "Main workflow completed successfully",
                summary
            )
        
        return workflow_results
        
    except Exception as e:
        logger.error(f"Main agent workflow failed: {str(e)}")
        workflow_results["status"] = "failed"
        workflow_results["error"] = str(e)
        workflow_results["end_time"] = datetime.now().isoformat()
        return workflow_results


def wait_for_mongodb_upload_completion(session_id: str, max_wait_seconds: int = 30) -> bool:
    """
    Wait for MongoDB upload to complete with comprehensive verification.
    
    Args:
        session_id: Session ID to check
        max_wait_seconds: Maximum time to wait in seconds
        
    Returns:
        True if upload completed successfully, False if timeout or failed
    """
    import time
    from leads_finder.database import get_sessions_collection, get_business_leads_collection
    
    try:
        sessions_collection = get_sessions_collection()
        business_leads_collection = get_business_leads_collection()
        
        logger.info(f"🔍 Starting upload verification for session {session_id}")
        
        for attempt in range(max_wait_seconds):
            # Check session record
            session_record = sessions_collection.find_one({"session_id": session_id})
            
            # Check if there are actual leads in the database for this session
            leads_count = business_leads_collection.count_documents({"session_id": session_id})
            
            # Get session status
            session_status = session_record.get("status", "unknown") if session_record else "not_found"
            
            logger.info(f"⏳ Attempt {attempt + 1}/{max_wait_seconds}: Status='{session_status}', Leads={leads_count}")
            
            # Check for completion conditions
            if session_status == "completed" and leads_count > 0:
                logger.info(f"✅ Upload completed successfully for session {session_id}")
                logger.info(f"📊 Final stats: {leads_count} leads, Status: {session_status}")
                return True
            
            # Check for failure conditions
            if session_status == "failed":
                error_msg = session_record.get("error", "Unknown error")
                logger.error(f"❌ Upload failed for session {session_id}: {error_msg}")
                return False
            
            # If we have leads but status is not completed, wait a bit more
            if leads_count > 0 and session_status in ["uploading", "unknown"]:
                logger.info(f"🔄 Found {leads_count} leads but status is '{session_status}', continuing to wait...")
            
            # Wait before next attempt
            time.sleep(1)
        
        # Final comprehensive check
        final_session_record = sessions_collection.find_one({"session_id": session_id})
        final_leads_count = business_leads_collection.count_documents({"session_id": session_id})
        final_status = final_session_record.get("status", "unknown") if final_session_record else "not_found"
        
        logger.info(f"🔍 Final check: Status='{final_status}', Leads={final_leads_count}")
        
        # Final decision logic
        if final_leads_count > 0:
            if final_status == "completed":
                logger.info(f"✅ Upload completed successfully (final verification)")
                return True
            elif final_status == "failed":
                logger.error(f"❌ Upload failed (final verification)")
                return False
            else:
                logger.warning(f"⚠️ Upload timeout but {final_leads_count} leads found - proceeding")
                return True
        else:
            logger.warning(f"⚠️ Upload timeout for session {session_id} - no leads found")
            return False
        
    except Exception as e:
        logger.error(f"❌ Error waiting for MongoDB upload: {str(e)}")
        return False


def get_stored_leads_from_mongodb(session_id: str = None, max_retries: int = 5) -> List[Dict[str, Any]]:
    """
    Retrieve stored leads from MongoDB with enhanced retry logic and fallback mechanisms.
    
    Args:
        session_id: Optional session ID to filter leads
        max_retries: Maximum number of retry attempts
        
    Returns:
        List of business data dictionaries from MongoDB
    """
    try:
        from leads_finder.database import get_business_leads_collection
        
        collection = get_business_leads_collection()
        
        # Debug logging
        logger.info(f"🔍 Retrieving leads for session_id: {session_id}")
        
        # Check total documents in collection
        total_docs = collection.count_documents({})
        logger.info(f"🔍 Total documents in collection: {total_docs}")
        
        # Check documents with this session_id
        session_docs = collection.count_documents({"session_id": session_id} if session_id else {})
        logger.info(f"🔍 Documents with session_id '{session_id}': {session_docs}")
        
        # Try multiple query strategies with increasing fallback
        query_strategies = []
        
        if session_id:
            # Strategy 1: Exact session match with email filter
            query_strategies.append({
                "query": {"session_id": session_id, "email": {"$nin": [None, "", "null", "N/A"]}},
                "description": f"Session {session_id} with valid emails"
            })
            
            # Strategy 2: Exact session match without email filter
            query_strategies.append({
                "query": {"session_id": session_id},
                "description": f"Session {session_id} (all records)"
            })
        
        # Strategy 3: Most recent records with email filter (fallback)
        query_strategies.append({
            "query": {"email": {"$nin": [None, "", "null", "N/A"]}},
            "description": "Most recent records with valid emails"
        })
        
        # Strategy 4: Most recent records without email filter (final fallback)
        query_strategies.append({
            "query": {},
            "description": "Most recent records (all)"
        })
        
        # Try each strategy until we get results
        leads = []
        for strategy_idx, strategy in enumerate(query_strategies):
            logger.info(f"🔍 Trying strategy {strategy_idx + 1}: {strategy['description']}")
            
            for attempt in range(max_retries):
                try:
                    leads = list(collection.find(strategy["query"]).sort("created_at", -1).limit(3))
                    logger.info(f"🔍 Strategy {strategy_idx + 1} attempt {attempt + 1}: Retrieved {len(leads)} leads")
                    
                    if leads:
                        logger.info(f"✅ Success with strategy {strategy_idx + 1}: {strategy['description']}")
                        break
                    
                    if attempt < max_retries - 1:
                        import time
                        time.sleep(1)
                        logger.info(f"⏳ Retrying strategy {strategy_idx + 1}... attempt {attempt + 2}/{max_retries}")
                
                except Exception as e:
                    logger.error(f"❌ Strategy {strategy_idx + 1} attempt {attempt + 1} error: {str(e)}")
                    if attempt == max_retries - 1:
                        logger.warning(f"⚠️ Strategy {strategy_idx + 1} failed after {max_retries} attempts")
            
            # If we got leads, stop trying other strategies
            if leads:
                break
        
        # Convert ObjectId to string for JSON serialization
        for lead in leads:
            if "_id" in lead:
                lead["_id"] = str(lead["_id"])
            
            # Convert datetime objects to strings for JSON serialization
            if "created_at" in lead and lead["created_at"]:
                lead["created_at"] = lead["created_at"].isoformat()
            if "updated_at" in lead and lead["updated_at"]:
                lead["updated_at"] = lead["updated_at"].isoformat()
        
        logger.info(f"✅ Successfully retrieved {len(leads)} leads from MongoDB")
        return leads
        
    except Exception as e:
        logger.error(f"❌ Error retrieving leads from MongoDB: {str(e)}")
        return []


def generate_workflow_summary(leads_result: Dict[str, Any], sdr_results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Generate a summary of the workflow execution.
    
    Args:
        leads_result: Results from the leads finder
        sdr_results: Results from SDR processing
        
    Returns:
        Dictionary with workflow summary
    """
    successful_sdr = len([r for r in sdr_results if r.get("status") == "completed"])
    failed_sdr = len([r for r in sdr_results if r.get("status") == "error"])
    
    return {
        "leads_found": leads_result.get("leads_found", 0),
        "leads_processed": len(sdr_results),
        "sdr_successful": successful_sdr,
        "sdr_failed": failed_sdr,
        "success_rate": (successful_sdr / len(sdr_results) * 100) if sdr_results else 0,
        "message": f"Processed {len(sdr_results)} businesses with {successful_sdr} successful SDR executions"
    }


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
        print(f"Success: {results.get('success')}")
        print(f"Leads Count: {results.get('leads_count', 0)}")
        print(f"SDR Results: {len(results.get('sdr_results', []))}")
        
        if results.get('summary'):
            summary = results['summary']
            print(f"\n📈 Summary:")
            print(f"  • Leads Found: {summary.get('leads_found', 0)}")
            print(f"  • Leads Processed: {summary.get('leads_processed', 0)}")
            print(f"  • SDR Successful: {summary.get('sdr_successful', 0)}")
            print(f"  • SDR Failed: {summary.get('sdr_failed', 0)}")
            print(f"  • Success Rate: {summary.get('success_rate', 0):.1f}%")
        
        if results.get('error'):
            print(f"\n❌ Error: {results['error']}")
        
        print(f"\n✅ Workflow completed!")
        
    except KeyboardInterrupt:
        print(f"\n⏹️ Workflow interrupted by user")
    except Exception as e:
        print(f"\n❌ Workflow failed: {str(e)}")
        import traceback
        traceback.print_exc()