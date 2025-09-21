# Development Environment

This directory contains all development-specific configurations, tools, and utilities for the AI Research Paper Intelligence System.

## Quick Start

```bash
# Complete setup and start
make dev-setup
make dev-start

# Access development tools
make dev-interactive
```

## Development Tools

### Hot Reloading System
- **Backend**: Automatic reload on Python file changes
- **AI Agents**: Hot reload agents without losing conversation state
- **Frontend**: Fast refresh with state preservation
- **Database**: Auto-migration on schema changes

### Interactive Development
- **Agent Playground**: Test paper agents interactively
- **Research Explorer**: Browse and analyze papers visually
- **Code Generator**: Generate implementation tutorials
- **Network Visualizer**: See agent relationships and interactions

### Debugging Tools
- **Agent Debugger**: Step through agent decision processes
- **Performance Profiler**: Real-time performance metrics
- **Memory Monitor**: Track memory usage across services
- **Request Tracer**: Trace requests through the system

## Directory Structure

```
development/
├── docker-compose.dev.yml    # Development infrastructure
├── .env.dev                  # Development environment variables
├── hot_reload.py            # Hot reloading configuration
├── interactive_session.py   # Interactive development session
├── agent_playground.py      # Agent testing playground
├── monitoring_dashboard.py  # Development monitoring
├── debug_agents.py          # Agent debugging tools
├── test_agents_interactive.py # Interactive agent testing
├── model_playground.py      # ML model development playground
├── data-fixtures/           # Sample data for development
│   ├── ai_papers.json      # Sample AI research papers
│   ├── foundational_papers.json # Historical AI papers
│   └── github_repos.json   # Sample GitHub repositories
├── testing/                 # Development testing utilities
│   ├── agent_tester.py     # Agent testing framework
│   ├── mock_data.py        # Mock data generators
│   └── performance_tests.py # Performance testing tools
└── local-setup/            # Local development configuration
    ├── jupyter_config.py   # Jupyter Lab configuration
    ├── vscode_settings.json # VS Code settings
    └── git_hooks/          # Development git hooks
```

## Development Workflow

### 1. Agent Development
```python
# Create new paper agent
from development.agent_playground import AgentPlayground

playground = AgentPlayground()
agent = playground.create_agent_from_arxiv("2017.06135")

# Test interactively
playground.test_query(agent, "Explain the transformer architecture")
playground.test_implementation_guide(agent, "pytorch")

# Hot reload on changes
agent.enable_hot_reload()
```

### 2. Multi-Agent Testing
```python
# Test agent collaboration
from development.multi_agent_tester import MultiAgentTester

tester = MultiAgentTester()
network = tester.create_research_network([
    "attention-is-all-you-need",
    "bert",
    "gpt-3"
])

# Test collaboration
result = tester.test_collaboration(
    network,
    "How did transformer architecture evolve?"
)
```

### 3. Performance Testing
```python
# Test agent performance
from development.performance_tests import AgentPerformanceTester

perf_tester = AgentPerformanceTester()
results = perf_tester.benchmark_agent_response_time(
    agent_id="transformer-agent",
    queries=["explain architecture", "show implementation"],
    iterations=100
)
```

## Configuration Files

### Development Environment Variables
```bash
# development/.env.dev
NODE_ENV=development
PYTHON_ENV=development
DEBUG=true
HOT_RELOAD=true

# Database
DATABASE_URL=postgresql://dev:dev@localhost:5432/research_papers_dev
REDIS_URL=redis://localhost:6379/0

# AI Services
OPENAI_API_KEY=your_key_here
ANTHROPIC_API_KEY=your_key_here

# Development Features
ENABLE_AGENT_DEBUGGING=true
ENABLE_PERFORMANCE_MONITORING=true
ENABLE_VISUAL_DEBUGGING=true

# Jupyter Lab
JUPYTER_ENABLE_LAB=true
JUPYTER_PORT=8888
```

### Docker Compose for Development
```yaml
# development/docker-compose.dev.yml
version: '3.8'
services:
  postgres-dev:
    image: postgres:15
    environment:
      POSTGRES_DB: research_papers_dev
      POSTGRES_USER: dev
      POSTGRES_PASSWORD: dev
    ports:
      - "5432:5432"
    volumes:
      - ./data/postgres:/var/lib/postgresql/data
  
  redis-dev:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - ./data/redis:/data
  
  neo4j-dev:
    image: neo4j:5
    environment:
      NEO4J_AUTH: neo4j/devpassword
    ports:
      - "7474:7474"
      - "7687:7687"
    volumes:
      - ./data/neo4j:/data
  
  elasticsearch-dev:
    image: elasticsearch:8.11.0
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
    ports:
      - "9200:9200"
    volumes:
      - ./data/elasticsearch:/usr/share/elasticsearch/data
```

## Development Scripts

### Seed AI Papers
```python
# scripts/seed_ai_papers.py
import arxiv
from backend.models import Paper, PaperAgent

def seed_foundational_ai_papers():
    """Seed database with foundational AI papers for research timeline"""
    foundational_papers = [
        "1943.12.01",  # McCulloch-Pitts Neuron
        "1957.07.01",  # Perceptron
        "1986.10.09",  # Backpropagation
        "1997.12.01",  # LSTM
        "2017.06.12",  # Attention Is All You Need
        "2018.10.11",  # BERT
        "2020.05.28",  # GPT-3
    ]
    
    for paper_id in foundational_papers:
        paper = fetch_paper_by_id(paper_id)
        create_paper_agent(paper)
```

### Interactive Agent Testing
```python
# development/test_agents_interactive.py
class InteractiveAgentTester:
    def __init__(self):
        self.agents = {}
        self.conversation_history = []
    
    def start_session(self):
        """Start interactive testing session"""
        print("🤖 AI Research Paper Agent Testing Session")
        print("Commands: create, query, compare, network, help, quit")
        
        while True:
            command = input("\n> ").strip().lower()
            
            if command == "create":
                self.create_agent_interactive()
            elif command == "query":
                self.query_agent_interactive()
            elif command == "compare":
                self.compare_agents_interactive()
            elif command == "network":
                self.create_network_interactive()
            elif command == "help":
                self.show_help()
            elif command == "quit":
                break
```

## Monitoring and Debugging

### Development Dashboard
Access at `http://localhost:3001` when running `make dev-start`

Features:
- **Real-time Metrics**: Agent response times, memory usage, request counts
- **Agent Status**: Active agents, conversation states, performance metrics
- **System Health**: Database connections, service status, error rates
- **Debug Console**: Interactive debugging interface for agents

### Visual Debugging
- **Agent Decision Trees**: Visualize how agents process queries
- **Conversation Flows**: See conversation state changes
- **Performance Graphs**: Real-time performance visualization
- **Network Topology**: Visual representation of agent relationships

## Best Practices

### Agent Development
1. **Test Early**: Use interactive playground for immediate feedback
2. **Hot Reload**: Enable hot reloading for rapid iteration
3. **Mock Data**: Use realistic mock data for consistent testing
4. **Performance Monitor**: Always monitor agent response times

### Code Quality
1. **Type Hints**: Use comprehensive type hints for all functions
2. **Documentation**: Document all agent behaviors and capabilities
3. **Testing**: Write tests for all agent interactions
4. **Linting**: Use automated linting and formatting

### Debugging
1. **Visual Debugging**: Use visual tools for complex agent interactions
2. **Logging**: Comprehensive logging for all agent decisions
3. **Profiling**: Regular performance profiling during development
4. **State Inspection**: Tools to inspect agent internal state