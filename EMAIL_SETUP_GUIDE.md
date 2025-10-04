# Email Agent Setup Guide

## Prerequisites

1. **Gmail Service Account**: You need a Google Cloud Project with Gmail API enabled
2. **Service Account JSON File**: Download the service account credentials
3. **Environment Variables**: Configure the required environment variables

## Step 1: Create Gmail Service Account

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable the Gmail API:
   - Go to "APIs & Services" > "Library"
   - Search for "Gmail API" and enable it
4. Create Service Account:
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "Service Account"
   - Fill in the details and create
5. Generate Service Account Key:
   - Click on the created service account
   - Go to "Keys" tab
   - Click "Add Key" > "Create new key"
   - Choose JSON format and download

## Step 2: Configure Environment Variables

Add these to your `.env` file:

```bash
# Email Configuration
GMAIL_SERVICE_ACCOUNT_FILE=path/to/your/service-account.json
GMAIL_SENDER_EMAIL=your-email@yourdomain.com

# Test Configuration
TEST_EMAIL=test@example.com
```

## Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

## Step 4: Test the Email Agent

### Test Email Tool Only
```bash
python test_send_email.py --tool-only
```

### Test Full Email Agent
```bash
python test_send_email.py
```

## Usage Example

```python
from sdr.agents.outreach_email_agent.sub_agents.email_sender.email_agent import send_outreach_email

# Business data
business_data = {
    "name": "The Coffee Shop",
    "email": "owner@coffeeshop.com",
    "phone": "+1-555-0123",
    "industry": "Food & Beverage"
}

# Research and proposal (from your existing system)
research_result = "Great reviews, no website..."
proposal = "We can help you build a website..."

# Send email
result = send_outreach_email(business_data, research_result, proposal)
print(result)
```

## Troubleshooting

### Common Issues

1. **Service Account File Not Found**
   - Check the file path in `GMAIL_SERVICE_ACCOUNT_FILE`
   - Ensure the file exists and is readable

2. **Gmail API Not Enabled**
   - Go to Google Cloud Console
   - Enable Gmail API for your project

3. **Permission Denied**
   - Ensure the service account has Gmail API access
   - Check that the service account email is properly configured

4. **Authentication Error**
   - Verify the service account JSON file is valid
   - Check that the service account has the correct permissions

### Testing Steps

1. First test with `--tool-only` flag to verify Gmail API setup
2. Then test the full agent workflow
3. Check Gmail logs for delivery confirmation
4. Verify emails are received in the target inbox

## Security Notes

- Keep your service account JSON file secure
- Don't commit it to version control
- Use environment variables for all sensitive data
- Consider using a dedicated Gmail account for sending
