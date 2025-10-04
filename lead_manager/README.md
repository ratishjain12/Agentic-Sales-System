# 🚀 Lead Manager Agent System

A sophisticated AI-powered email monitoring and lead management system that automatically processes Gmail emails, detects hot leads, schedules meetings, and manages customer interactions through a sequential agent workflow.

## 📋 Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Agent Flow](#agent-flow)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Database Schema](#database-schema)
- [API Integration](#api-integration)
- [Error Handling](#error-handling)
- [Testing](#testing)
- [Troubleshooting](#troubleshooting)

## 🎯 Overview

The Lead Manager system automatically monitors your Gmail inbox for unread emails, analyzes them using AI to detect hot leads and meeting requests, and takes appropriate actions including scheduling meetings and sending notifications. The system uses a sequential agent architecture to ensure reliable, step-by-step processing.

### Key Features

- **Real-time Email Monitoring**: Automatically checks Gmail for unread emails
- **AI-Powered Lead Detection**: Uses Cerebras LLM to analyze email content for hot lead signals
- **Meeting Request Analysis**: Detects and processes meeting requests from emails
- **Automatic Meeting Scheduling**: Integrates with Google Calendar and Google Meet
- **MongoDB Data Persistence**: Stores meeting data, email status, and lead analysis
- **Sequential Agent Workflow**: Ensures reliable, step-by-step processing
- **Business Email Filtering**: Automatically filters out system/automated emails

## 🏗️ Architecture

### System Components

```
📧 Gmail API → Email Checker → Email Analyzer → Calendar Organizer → Post Action
     ↓              ↓              ↓              ↓              ↓
  Real Emails   Hot Lead?    Meeting Req?   Schedule?    MongoDB Save
```

### Agent Hierarchy

1. **Email Checker Agent** - Retrieves unread emails from Gmail
2. **Email Analyzer Agent** - AI-powered analysis for hot leads and meeting requests
3. **Calendar Organizer Agent** - Schedules meetings for qualified leads
4. **Post Action Agent** - Finalizes workflow and saves data

### Database Architecture

- **Lead Manager Database**: `leads_manager_db` (separate from leads_finder)
- **Collections**: meetings, email_status, lead_analysis
- **Data Types**: Meeting details, email processing status, lead qualification scores

## 🔄 Agent Flow

### Sequential Processing Workflow

```
For each unread email:
1. Email Checker Agent → Retrieve email data
2. Email Analyzer Agent → AI analysis (hot lead + meeting request detection)
3. Decision: Hot Lead? → Yes: UI notification
4. Decision: Meeting Request + Hot Lead? → Yes: Calendar Organizer Agent
5. Calendar Organizer Agent → Check availability + Create meeting
6. Post Action Agent → Save data, mark email as read, send notifications
```

### Detailed Agent Responsibilities

#### 1. Email Checker Agent
- **File**: `lead_manager/sub_agents/email_checker_agent.py`
- **Purpose**: Retrieves unread emails from Gmail using OAuth2
- **Tools**: `CheckEmailTool` (Gmail API integration)
- **Output**: Structured email data with metadata
- **Database**: None (just retrieval)

#### 2. Email Analyzer Agent
- **File**: `lead_manager/sub_agents/email_analyzer_agent.py`
- **Purpose**: AI-powered analysis for hot leads and meeting requests
- **Tools**: `MeetingAnalysisTool` (Cerebras LLM)
- **AI Analysis**:
  - Hot lead detection (content-based, no DB queries)
  - Meeting request detection
  - Lead scoring (0-100)
  - Interest signals extraction
- **Output**: Analysis results with confidence scores

#### 3. Calendar Organizer Agent
- **File**: `lead_manager/sub_agents/calendar_organizer_agent.py`
- **Purpose**: Schedules meetings for hot leads with meeting requests
- **Tools**: 
  - `CheckAvailabilityTool` (Google Calendar API)
  - `CreateMeetingTool` (Google Meet integration)
- **Condition**: Only runs if BOTH hot lead AND meeting request detected
- **Output**: Meeting scheduled with Google Meet link

#### 4. Post Action Agent
- **File**: `lead_manager/sub_agents/post_action_agent.py`
- **Purpose**: Finalizes workflow and saves data
- **Tools**:
  - `SaveMeetingTool` (MongoDB)
  - `MarkEmailReadTool` (MongoDB)
  - `UINotificationTool` (UI alerts)
- **Database**: Saves meeting data and email status

## 🛠️ Installation

### Prerequisites

- Python 3.8+
- MongoDB instance
- Gmail account with API access
- Google Cloud Platform project
- Cerebras API key

### Dependencies

```bash
pip install -r requirements.txt
```

Key dependencies:
- `crewai` - Agent framework
- `pymongo` - MongoDB integration
- `google-auth` - Google API authentication
- `google-api-python-client` - Google services
- `litellm` - LLM integration
- `python-dotenv` - Environment management

## ⚙️ Configuration

### Environment Variables

Create a `.env` file with the following variables:

```env
# Cerebras AI Configuration
CEREBRAS_API_KEY=your_cerebras_api_key
CEREBRAS_BASE_URL=https://api.cerebras.ai/v1

# MongoDB Configuration
MONGODB_URI=mongodb://localhost:27017
LEAD_MANAGER_DATABASE_NAME=leads_manager_db

# Google API Configuration
GOOGLE_CREDENTIALS_FILE=path/to/credentials.json
GOOGLE_APPLICATION_CREDENTIALS=path/to/credentials.json

# Optional: Custom model settings
CEREBRAS_MODEL=cerebras/llama3.1-8b
CEREBRAS_TEMPERATURE=0.3
```

### Google API Setup

1. **Enable APIs**:
   - Gmail API
   - Google Calendar API
   - Google Meet API

2. **Create Service Account**:
   - Download credentials JSON
   - Set `GOOGLE_CREDENTIALS_FILE` path

3. **Gmail OAuth2**:
   - Configure OAuth2 consent screen
   - Generate OAuth2 credentials

### MongoDB Setup

1. **Install MongoDB** (local or cloud)
2. **Set Connection String**: Update `MONGODB_URI`
3. **Database**: System creates `leads_manager_db` automatically

## 🚀 Usage

### Running the Lead Manager

#### Option 1: Main Application
```bash
python main.py
# Select option 4: Run Lead Manager workflow
```

#### Option 2: Direct Execution
```bash
python -m lead_manager
```

#### Option 3: Individual Agent Testing
```bash
python test_lead_manager_flow.py
```

### Workflow Execution

The system automatically:
1. **Checks Gmail** for unread emails
2. **Filters** business-related emails
3. **Analyzes** each email for hot lead signals
4. **Detects** meeting requests
5. **Schedules** meetings for qualified leads
6. **Saves** data to MongoDB
7. **Sends** notifications

### Expected Output

```
🚀 Starting Lead Manager workflow...
📧 PROCESSING EMAIL:
   👤 From: John Doe (john@company.com)
   📝 Subject: Interested in your services
   📅 Date: 2024-01-15T10:30:00Z
   🔗 Message ID: msg_12345...

   ✅ DECISION: PROCESSING - Business email
   🔄 Starting Sequential Workflow...

🔄 STEP 1: Email Checker Agent ✅ COMPLETED
🔍 STEP 2: Email Analyzer Agent → ANALYZING...
🔥 STEP 3: HOT LEAD DETECTED! ✅ → UI Notification sent
🤖 STEP 4: Meeting Request Analysis ✅ COMPLETED
🚀 STEP 5: Meeting Request + Hot Lead → CALENDAR ORGANIZER
📅 STEP 6: Calendar Organizer Agent → SCHEDULING...
✅ STEP 6: Meeting scheduled successfully!
🔧 STEP 7: Post Action Agent → FINALIZING...
✅ SEQUENTIAL WORKFLOW COMPLETED for: john@company.com
```

## 🗄️ Database Schema

### MongoDB Collections

#### `meetings` Collection
```json
{
  "meeting_id": "meet_12345",
  "sender_email": "john@company.com",
  "sender_name": "John Doe",
  "subject": "Meeting Request",
  "meeting_time": "2024-01-15T14:00:00Z",
  "meeting_duration": 30,
  "meet_link": "https://meet.google.com/abc-def-ghi",
  "status": "scheduled",
  "created_at": "2024-01-15T10:30:00Z"
}
```

#### `email_status` Collection
```json
{
  "message_id": "msg_12345",
  "sender_email": "john@company.com",
  "subject": "Interested in your services",
  "processed_at": "2024-01-15T10:30:00Z",
  "status": "processed",
  "hot_lead_detected": true,
  "meeting_request_detected": true,
  "meeting_scheduled": true
}
```

#### `lead_analysis` Collection
```json
{
  "message_id": "msg_12345",
  "sender_email": "john@company.com",
  "analysis_timestamp": "2024-01-15T10:30:00Z",
  "hot_lead_score": 85,
  "meeting_request_detected": true,
  "interest_signals": ["urgent", "partnership", "discuss"],
  "confidence_score": 0.87,
  "ai_analysis": "Strong interest in partnership discussion"
}
```

## 🔌 API Integration

### Gmail API
- **Authentication**: OAuth2
- **Scope**: `https://www.googleapis.com/auth/gmail.readonly`
- **Operations**: List messages, get message details, mark as read

### Google Calendar API
- **Authentication**: Service Account
- **Scope**: `https://www.googleapis.com/auth/calendar`
- **Operations**: Check availability, create events

### Google Meet API
- **Integration**: Via Calendar API
- **Features**: Generate meeting links, set up video calls

### Cerebras AI API
- **Model**: `cerebras/llama3.1-8b`
- **Endpoint**: `https://api.cerebras.ai/v1`
- **Usage**: Hot lead detection, meeting request analysis

## 🛡️ Error Handling

### API Failures
- **Cerebras API**: Falls back to keyword-based analysis
- **Gmail API**: Retries with exponential backoff
- **Calendar API**: Graceful degradation, logs errors

### Email Processing
- **Invalid Emails**: Skipped with logging
- **Parse Errors**: Fallback to basic analysis
- **Authentication**: Automatic token refresh

### Database Errors
- **Connection Issues**: Retry with backoff
- **Write Failures**: Log and continue processing
- **Schema Validation**: Graceful error handling

## 🧪 Testing

### Test Suite

```bash
# Run all tests
python test_lead_manager_flow.py

# Test individual components
python -c "from lead_manager.sub_agents.email_checker_agent import run_email_checker; run_email_checker()"
```

### Test Coverage

- **Configuration Validation**: Environment variables, API keys
- **Agent Functionality**: Each agent's core functionality
- **Tool Integration**: Gmail, Calendar, MongoDB tools
- **Workflow Execution**: End-to-end processing
- **Error Scenarios**: API failures, invalid data

### Test Data

The system uses real Gmail emails for testing, ensuring:
- **Real-world Scenarios**: Actual email processing
- **Data Validation**: Proper email parsing
- **Integration Testing**: Full API integration

## 🔧 Troubleshooting

### Common Issues

#### 1. Cerebras API Errors
```
Error: 404 Not Found
Solution: Check CEREBRAS_API_KEY and model name
```

#### 2. Gmail Authentication
```
Error: Invalid credentials
Solution: Regenerate OAuth2 tokens, check scopes
```

#### 3. MongoDB Connection
```
Error: Connection refused
Solution: Check MONGODB_URI, ensure MongoDB is running
```

#### 4. Calendar API Issues
```
Error: Insufficient permissions
Solution: Check service account permissions, enable APIs
```

### Debug Mode

Enable detailed logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Health Checks

```bash
# Check configuration
python -c "from lead_manager.config import LeadManagerConfig; print('Config OK')"

# Check MongoDB
python -c "from lead_manager.tools.mongodb_lead_tools import get_lead_manager_mongodb_client; print('MongoDB OK')"

# Check Cerebras API
python -c "from leads_finder.llm_config import LLMConfig; LLMConfig.get_cerebras_llm(); print('Cerebras OK')"
```

## 📊 Performance

### Processing Speed
- **Email Retrieval**: ~2-3 seconds per batch
- **AI Analysis**: ~5-10 seconds per email
- **Meeting Scheduling**: ~3-5 seconds per meeting
- **Database Operations**: ~1-2 seconds per operation

### Scalability
- **Concurrent Processing**: Supports multiple emails
- **Rate Limiting**: Respects API limits
- **Memory Usage**: Optimized for large email volumes
- **Database**: Indexed for fast queries

## 🔒 Security

### Data Protection
- **Email Content**: Processed in memory, not stored
- **API Keys**: Environment variables only
- **Database**: Encrypted connections
- **Authentication**: OAuth2 + Service Account

### Privacy
- **Email Access**: Read-only, no modifications
- **Data Retention**: Configurable retention policies
- **Audit Logs**: Complete processing history
- **Access Control**: Role-based permissions

## 📈 Monitoring

### Logging
- **Agent Execution**: Step-by-step logging
- **API Calls**: Request/response logging
- **Database Operations**: Query performance
- **Error Tracking**: Detailed error logs

### Metrics
- **Processing Time**: Per-agent timing
- **Success Rate**: Processing success percentage
- **API Usage**: Rate limit monitoring
- **Database Performance**: Query execution time

## 🚀 Future Enhancements

### Planned Features
- **Email Templates**: Automated response generation
- **Lead Scoring**: Advanced qualification algorithms
- **Integration**: CRM system connectivity
- **Analytics**: Lead conversion tracking
- **Mobile**: Push notifications
- **Multi-language**: International email support

### Extensibility
- **Custom Agents**: Plugin architecture
- **Custom Tools**: Tool development framework
- **Custom Models**: Alternative LLM support
- **Custom Databases**: Database abstraction layer

## 📞 Support

### Documentation
- **Code Comments**: Inline documentation
- **Type Hints**: Full type annotations
- **Examples**: Usage examples in code
- **API Reference**: Tool and agent documentation

### Community
- **Issues**: GitHub issue tracking
- **Discussions**: Feature requests and questions
- **Contributions**: Pull request guidelines
- **Updates**: Release notes and changelog

---

**Lead Manager Agent System** - Automating lead management with AI-powered email analysis and intelligent meeting scheduling.