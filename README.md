# Agentic Sales Agent

A sophisticated AI-powered sales lead generation system using CrewAI and multiple LLM providers.

## 🚀 Features

- **Multi-LLM Support**: Cerebras llama3.1-8b/70b and OpenAI GPT-4o-mini
- **Dual Search Methods**: Foursquare Places API and OpenStreetMap cluster search
- **Intelligent Lead Analysis**: Automated lead qualification and scoring
- **Cost Optimization**: Flexible LLM selection based on task requirements
- **Modern Architecture**: Built with CrewAI for agent orchestration

## 📋 Requirements

- Python 3.9+
- API Keys for:
  - Cerebras Cloud (for llama3.1 models)
  - OpenAI (for GPT-4o-mini)
  - Foursquare Places API

## 🛠️ Installation

1. Clone the repository:

```bash
git clone <repository-url>
cd agentic-sales-agent
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Set up environment variables in `env.txt`:

```
CEREBRAS_API_KEY=your_cerebras_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
FOURSQUARE_API_KEY=your_foursquare_api_key_here
```

## 🎯 Usage

### Quick Start

Run the main application:

```bash
python main.py
```

### Demo Mode

Run the interactive demo:

```bash
python demo_lead_finder.py
```

### System Tests

Test your configuration:

```bash
python test_configuration.py
```

### API Testing

Test Foursquare API integration:

```bash
python test_foursquare_api.py
```

## 🏗️ Project Structure

```
agentic-sales-agent/
├── main.py                          # Main entry point
├── pyproject.toml                   # Modern Python packaging
├── requirements.txt                  # Dependencies
├── .python-version                   # Python version specification
├── env.txt                          # Environment variables
├── config/                          # Configuration modules
│   └── __init__.py
├── leads_finder/                    # Core lead finding system
│   ├── __init__.py
│   ├── llm_config.py               # Optimized LLM configuration
│   ├── prompts.py                  # Agent prompts
│   ├── sub_agents/                 # Individual agents
│   │   ├── cluster_search_agent.py
│   │   └── crewai_lead_finder_agent.py
│   ├── crew/                       # Crew orchestration
│   │   └── lead_finder_crew.py
│   ├── tasks/                      # Task definitions
│   │   └── lead_finder_tasks.py
│   └── tools/                      # External tools
│       ├── cluster_search.py
│       ├── foursquare_search.py
│       └── crewai_foursquare_tool.py
├── sdr/                            # Sales Development Rep module
└── tests/                          # Test files
    ├── test_configuration.py
    ├── test_foursquare_api.py
    └── demo_lead_finder.py
```

## 🔧 Configuration

### LLM Selection

The system supports multiple LLM configurations:

- **Cost-Effective**: OpenAI GPT-4o-mini (budget-friendly)
- **Default**: Cerebras llama3.1-8b (balanced performance)
- **High-Performance**: Cerebras llama3.1-70b (premium tasks)

### Search Methods

1. **Foursquare Places API**: Commercial business data with ratings and reviews
2. **OpenStreetMap Cluster Search**: Open-source geographic business intelligence

## 📊 API Reference

### Lead Finder Crew

```python
from leads_finder.crew.lead_finder_crew import get_lead_finder_crew

# Get crew instance
crew = get_lead_finder_crew(use_cost_effective=True)

# Search for leads
result = crew.search_leads(
    query="restaurants",
    location="New York",
    radius=2000,
    limit=10
)

# Analyze results
analysis = crew.analyze_leads(str(result))
```

### Cluster Search Agent

```python
from leads_finder.sub_agents.cluster_search_agent import run_cluster_search

# Search using OSM data
result = run_cluster_search("Ahmedabad")
```

## 🧪 Testing

Run the comprehensive test suite:

```bash
# Test system configuration
python test_configuration.py

# Test Foursquare API
python test_foursquare_api.py

# Run main application tests
python main.py
# Select option 4 for system tests
```

## 🚀 Development

### Adding New Agents

1. Create agent in `leads_finder/sub_agents/`
2. Add corresponding prompts in `prompts.py`
3. Update crew configuration in `leads_finder/crew/`

### Adding New Tools

1. Implement tool in `leads_finder/tools/`
2. Register with agents in `sub_agents/`
3. Update task definitions in `tasks/`

## 📈 Performance

- **Cost Optimization**: Smart LLM selection based on task complexity
- **Rate Limiting**: Built-in API rate limit handling
- **Caching**: Lazy loading of LLM instances
- **Timeout Management**: Configurable execution timeouts

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For issues and questions:

- Create an issue in the repository
- Check the test files for configuration examples
- Review the API documentation

## 🔄 Changelog

### v1.0.0

- Initial release
- Multi-LLM support
- Dual search methods
- Comprehensive lead analysis
- Modern Python packaging
