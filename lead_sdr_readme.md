# Sales Agent System - Lead Finder & SDR

A comprehensive AI-powered sales automation system that combines lead discovery and sales development representative (SDR) workflows using CrewAI framework.

## 🚀 Overview

This system automates the entire sales pipeline from lead discovery to outreach, featuring:

- **Lead Finder Agent**: Discovers business leads using Foursquare and OpenStreetMap APIs
- **SDR Agent**: Handles research, proposal generation, phone calls, and email outreach
- **Main Agent Orchestrator**: Coordinates the entire workflow seamlessly

## 📋 Table of Contents

- [Architecture](#architecture)
- [Features](#features)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [API Reference](#api-reference)
- [Database Schema](#database-schema)
- [Troubleshooting](#troubleshooting)

## 🏗️ Architecture

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│                    Main Agent Orchestrator                  │
│                     (main_agent.py)                         │
└─────────────────────┬───────────────────────────────────────┘
                      │
        ┌─────────────┴─────────────┐
        │                         │
┌───────▼────────┐    ┌──────────▼──────────┐
│  Lead Finder    │    │     SDR Agent       │
│    Agent        │    │                     │
│                 │    │ ┌─────────────────┐ │
│ • Foursquare    │    │ │ Research Agent  │ │
│ • OSM Search    │    │ └─────────────────┘ │
│ • MongoDB       │    │ ┌─────────────────┐ │
│   Storage       │    │ │ Proposal Gen.   │ │
└─────────────────┘    │ └─────────────────┘ │
        │               │ ┌─────────────────┐ │
        │               │ │ Phone Caller    │ │
        │               │ └─────────────────┘ │
        │               │ ┌─────────────────┐ │
        │               │ │ Email Outreach │ │
        │               │ └─────────────────┘ │
        │               └─────────────────────┘
        │                         │
        └─────────────┬───────────┘
                      │
            ┌─────────▼─────────┐
            │   MongoDB         │
            │   Database        │
            │                   │
            │ • business_leads  │
            │ • sessions        │
            └───────────────────┘
```

### Workflow Process

1. **Main Agent** initializes with unique session ID
2. **Lead Finder** discovers business leads and stores in MongoDB
3. **Main Agent** retrieves leads with valid email addresses
4. **SDR Agent** processes each lead through complete sales workflow
5. **Results** are stored and tracked by session

## ✨ Features

### Lead Finder Agent

- **Multi-Source Discovery**: Uses Foursquare Places API and OpenStreetMap
- **Smart Filtering**: Finds businesses with valid email addresses
- **Geographic Search**: Configurable search radius and location targeting
- **Data Validation**: Validates business information before storage
- **Session Tracking**: Links all leads to specific workflow sessions

### SDR Agent

- **Business Research**: Comprehensive business analysis and research
- **Proposal Generation**: AI-powered personalized business proposals
- **Phone Calling**: Automated phone calls with conversation tracking
- **Email Outreach**: Professional follow-up emails with Gmail integration
- **Conversation Analysis**: Classifies call outcomes and determines next steps

### Main Agent Orchestrator

- **Workflow Coordination**: Manages the entire sales pipeline
- **Session Management**: Tracks workflow sessions with unique IDs
- **Error Handling**: Robust error handling and recovery
- **Progress Tracking**: Monitors and reports workflow progress
- **Data Integration**: Seamlessly connects lead finder and SDR workflows

## 🛠️ Installation

### Prerequisites

- Python 3.8+
- MongoDB
- Gmail OAuth2 credentials
- Foursquare API key

### Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd sales-agent
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   ```bash
   # Create .env file
   cp .env.example .env
   
   # Edit .env with your credentials
   FOURSQUARE_API_KEY=your_foursquare_api_key
   MONGODB_URI=mongodb://localhost:27017/sales_agent
   GMAIL_CREDENTIALS_FILE=credentials/oauth2_credentials.json
   GMAIL_SENDER_EMAIL=your_email@gmail.com
   ```

4. **Set up MongoDB**
   ```bash
   # Start MongoDB service
   sudo systemctl start mongod
   
   # Create database and collections
   python scripts/setup_database.py
   ```

5. **Set up Gmail OAuth2**
   ```bash
   # Place your OAuth2 credentials in credentials/oauth2_credentials.json
   # Run authentication flow
   python scripts/setup_gmail_auth.py
   ```

## ⚙️ Configuration

### Lead Finder Configuration

```python
# leads_finder/config.py
LEAD_FINDER_CONFIG = {
    "max_results": 3,           # Maximum leads per search
    "search_radius": 5000,     # Search radius in meters
    "email_required": True,     # Only return leads with emails
    "session_tracking": True   # Enable session tracking
}
```

### SDR Configuration

```python
# sdr/config/sdr_config.py
SDR_CONFIG = {
    "llm_model": "cerebras/gpt-oss-120b",
    "temperature": 0.3,
    "max_iterations": 2,
    "execution_timeout": 120,
    "email_signature": "Best regards,\nRatish Jain"
}
```

### Main Agent Configuration

```python
# main_agent.py
MAIN_AGENT_CONFIG = {
    "session_format": "%Y%m%d_%H%M%S",
    "max_leads_per_session": 3,
    "email_filter": True,
    "workflow_timeout": 1800
}
```

## 🚀 Usage

### Basic Usage

```python
from main_agent import run_main_agent_workflow

# Run complete workflow
results = run_main_agent_workflow(
    city="New York",
    business_type="restaurants",
    max_results=3,
    search_radius=5000
)

print(f"Session ID: {results['session_id']}")
print(f"Leads Found: {results['leads_count']}")
print(f"SDR Results: {results['sdr_results']}")
```

### Advanced Usage

```python
from main_agent import MainAgentOrchestrator

# Create orchestrator instance
orchestrator = MainAgentOrchestrator()

# Execute workflow with custom parameters
results = orchestrator.execute_complete_workflow(
    city="San Francisco",
    business_type="cafes",
    max_results=5,
    search_radius=10000
)

# Access detailed results
for lead_result in results['sdr_results']:
    print(f"Lead: {lead_result['business_name']}")
    print(f"Status: {lead_result['status']}")
    print(f"Email Sent: {lead_result['email_sent']}")
```

### Individual Agent Usage

#### Lead Finder Only

```python
from leads_finder.agent import run_lead_finder_workflow

# Find leads only
leads_result = run_lead_finder_workflow(
    city="Chicago",
    business_type="jewelry",
    max_results=5,
    search_radius=7500,
    session_id="20241220_143022"
)
```

#### SDR Only

```python
from sdr.agents.sdr_main_agent import SDRAgent

# Process specific leads
sdr_agent = SDRAgent()
business_data = {
    "name": "The Coffee Shop",
    "email": "info@coffeeshop.com",
    "phone": "+1234567890",
    "address": "123 Main St, City, State"
}

sdr_result = sdr_agent.execute_workflow(business_data)
```

## 📊 API Reference

### Main Agent Orchestrator

#### `run_main_agent_workflow(city, business_type, max_results, search_radius)`

**Parameters:**
- `city` (str): City name to search for leads
- `business_type` (str): Type of business to find
- `max_results` (int): Maximum number of leads to process
- `search_radius` (int): Search radius in meters

**Returns:**
```python
{
    "session_id": "20241220_143022",
    "success": True,
    "leads_count": 3,
    "sdr_results": [...],
    "workflow_duration": 120.5,
    "status": "completed"
}
```

### Lead Finder Agent

#### `run_lead_finder_workflow(city, business_type, max_results, search_radius, session_id)`

**Parameters:**
- `city` (str): City name to search
- `business_type` (str): Business type to find
- `max_results` (int): Maximum results to return
- `search_radius` (int): Search radius in meters
- `session_id` (str): Session identifier

**Returns:**
```python
{
    "success": True,
    "leads_found": 3,
    "session_id": "20241220_143022",
    "search_summary": {...}
}
```

### SDR Agent

#### `execute_workflow(business_data)`

**Parameters:**
- `business_data` (dict): Business information dictionary

**Returns:**
```python
{
    "success": True,
    "business_name": "The Coffee Shop",
    "research_completed": True,
    "proposal_generated": True,
    "phone_call_made": True,
    "email_sent": True,
    "conversation_classification": "interested"
}
```

## 🗄️ Database Schema

### business_leads Collection

```javascript
{
  "_id": ObjectId,
  "name": "Business Name",
  "email": "business@email.com",
  "phone": "+1234567890",
  "address": "123 Main St, City, State",
  "website": "https://business.com",
  "category": "restaurants",
  "rating": 4.5,
  "source": "map_search",
  "session_id": "20241220_143022",
  "created_at": ISODate,
  "updated_at": ISODate
}
```

### sessions Collection

```javascript
{
  "_id": ObjectId,
  "session_id": "20241220_143022",
  "created_at": ISODate,
  "leads_count": 3,
  "insert_count": 2,
  "upsert_count": 1,
  "status": "completed",
  "workflow_duration": 120.5
}
```

## 🔧 Troubleshooting

### Common Issues

#### 1. MongoDB Connection Error
```
Error: Could not connect to MongoDB
```
**Solution:** Ensure MongoDB is running and connection string is correct.

#### 2. Foursquare API Error
```
Error: FOURSQUARE_API_KEY not found
```
**Solution:** Set the FOURSQUARE_API_KEY environment variable.

#### 3. Gmail Authentication Error
```
Error: Gmail OAuth2 authentication failed
```
**Solution:** Run the Gmail authentication flow and ensure credentials are valid.

#### 4. No Leads Found
```
Warning: No leads found with valid email addresses
```
**Solution:** Check search parameters and ensure businesses in the area have email addresses.

### Debug Mode

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Run workflow with debug output
results = run_main_agent_workflow("New York", "restaurants")
```

### Performance Optimization

1. **Reduce Search Radius**: Smaller radius = faster searches
2. **Limit Results**: Fewer leads = faster processing
3. **Database Indexing**: Add indexes on frequently queried fields
4. **Parallel Processing**: Process multiple leads simultaneously

## 📈 Monitoring and Analytics

### Session Tracking

Each workflow run is tracked with:
- Unique session ID
- Lead discovery metrics
- SDR processing results
- Performance metrics

### Logging

The system provides comprehensive logging:
- Lead discovery progress
- SDR workflow steps
- Email delivery status
- Error tracking and debugging

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- Create an issue in the repository
- Check the troubleshooting section
- Review the API documentation

---

**Built with ❤️ using CrewAI, MongoDB, and Gmail API**
