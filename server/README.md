# Sales Agent API Documentation

## Quick Start

1. **Install dependencies:**
   ```bash
   pip install -r server/requirements.txt
   ```

2. **Set environment variables:**
   ```bash
   export GMAIL_CREDENTIALS_FILE=credentials/oauth2_credentials.json
   export GMAIL_SENDER_EMAIL=your-email@gmail.com
   export CEREBRAS_API_KEY=your_cerebras_api_key
   ```

3. **Run server:**
   ```bash
   python server/run.py
   ```

4. **Access API docs:**
   - Swagger UI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

## API Endpoints

### Health Check
- `GET /health` - Check API status

### Lead Management
- `POST /api/v1/leads/search` - Search for business leads

### Email Operations
- `POST /api/v1/email/send` - Send single email
- `POST /api/v1/email/send-agent` - Send email using agent system

### Workflow Execution
- `POST /api/v1/workflow/execute` - Execute complete SDR workflow
- `POST /api/v1/workflow/execute-async` - Execute workflow asynchronously

### Agent Status
- `GET /api/v1/agents/status` - Get agent status and configuration

## Example Usage

### Send Email
```bash
curl -X POST "http://localhost:8000/api/v1/email/send" \
  -H "Content-Type: application/json" \
  -d '{
    "to_email": "test@example.com",
    "subject": "Test Email",
    "body": "<h1>Hello World</h1>",
    "is_html": true
  }'
```

### Execute Workflow
```bash
curl -X POST "http://localhost:8000/api/v1/workflow/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Coffee Shop",
    "email": "owner@coffeeshop.com",
    "phone": "+1-555-0123",
    "industry": "Food & Beverage"
  }'
```

### Send Email with Agent
```bash
curl -X POST "http://localhost:8000/api/v1/email/send-agent" \
  -H "Content-Type: application/json" \
  -d '{
    "business_data": {
      "name": "Coffee Shop",
      "email": "owner@coffeeshop.com",
      "industry": "Food & Beverage"
    },
    "research_result": "Great coffee shop with limited online presence",
    "proposal": "We can help you build a professional website"
  }'
```

## Environment Variables

```bash
# Server Configuration
SERVER_HOST=0.0.0.0
SERVER_PORT=8000
DEBUG=False

# Gmail OAuth2 Configuration
GMAIL_CREDENTIALS_FILE=credentials/oauth2_credentials.json
GMAIL_TOKEN_FILE=credentials/token.json
GMAIL_SENDER_EMAIL=your-email@gmail.com

# AI Configuration
CEREBRAS_API_KEY=your_cerebras_api_key

# Database Configuration
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/
MONGODB_DATABASE_NAME=sales_leads_db

# Rate Limiting
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=60
EMAIL_RATE_LIMIT=10
```

## Features

- ✅ **Complete REST API** with all agent endpoints
- ✅ **Health monitoring** and status checks
- ✅ **Async workflow execution** for long-running tasks
- ✅ **Email sending** (both simple and agent-based)
- ✅ **Lead search** capabilities
- ✅ **Error handling** and validation
- ✅ **API documentation** with Swagger UI
- ✅ **CORS support** for web applications
- ✅ **Background task processing**
- ✅ **Rate limiting** and security features
