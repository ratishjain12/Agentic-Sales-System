# Foursquare Places Agent

A powerful lead finding agent that uses the Foursquare Places API to discover and analyze businesses for sales prospecting.

## Features

- **Location-based Business Search**: Find businesses near specific locations
- **Detailed Business Information**: Extract contact details, ratings, hours, and more
- **Category Filtering**: Search by business categories and types
- **Distance-based Results**: Filter results by proximity to target location
- **Free Tier Compatible**: Optimized for Foursquare's free API tier

## Setup

### 1. Get Foursquare API Key

1. Visit the [Foursquare Developer Console](https://foursquare.com/developers/orgs/68de853467bf093d3e59bafa/projects/68de853567bf093d3e59bb08/settings)
2. Create a new project or use an existing one
3. Copy your API key

### 2. Environment Configuration

Create a `.env` file in your project root:

```bash
FOURSQUARE_API_KEY=your_api_key_here
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

## Usage

### Basic Search

```python
from leads_finder.tools.foursquare_search_tools import foursquare_search_nearby

# Search for restaurants in New York
results = foursquare_search_nearby(
    query="restaurants",
    location="New York, NY",
    radius=2000,  # 2km radius
    limit=10
)

for restaurant in results:
    print(f"{restaurant['name']} - {restaurant.get('phone', 'No phone')}")
```

### Using the Agent

```python
from leads_finder.sub_agents.foursquare_agent import foursquare_agent

# Create a task for lead finding
task = foursquare_agent.create_task(
    "Find 5 high-rated restaurants in downtown Chicago that would be good prospects for a food delivery service partnership."
)

# Execute the task
result = foursquare_agent.execute_task(task)
```

### Get Detailed Information

```python
from leads_finder.tools.foursquare_search_tools import foursquare_get_place_details

# Get detailed info about a specific business
details = foursquare_get_place_details("fsq_id_here")
print(f"Business hours: {details.get('hours', {})}")
```

## API Limits (Free Tier)

- **1,000 requests per day**
- **60 requests per minute**
- **Maximum 50 results per search**
- **Search radius up to 100km**

## Available Data Fields

- Business name and ID
- Full address and coordinates
- Phone number and website
- Business categories
- Rating and price level
- Business hours
- Distance from search center

## Examples

See `leads_finder/examples/foursquare_example.py` for comprehensive usage examples including:

- Restaurant search
- Coffee shop discovery
- Detailed place information retrieval
- Agent-based lead finding

## Error Handling

The agent includes comprehensive error handling for:

- Missing API keys
- Rate limit exceeded
- Invalid locations
- Network timeouts
- API response errors

## Integration with Sales Workflows

The Foursquare agent is designed to integrate seamlessly with CRM systems and sales workflows:

1. **Lead Qualification**: Use ratings and business information to qualify prospects
2. **Contact Information**: Extract phone numbers and websites for outreach
3. **Location Analysis**: Understand business density and competition in target areas
4. **Category Targeting**: Focus on specific business types relevant to your product/service

## Support

For issues related to:

- **Foursquare API**: Check the [Foursquare Documentation](https://docs.foursquare.com/)
- **Agent Implementation**: Review the code in `leads_finder/sub_agents/foursquare_agent.py`
- **Search Tools**: Check `leads_finder/tools/foursquare_search_tools.py`
