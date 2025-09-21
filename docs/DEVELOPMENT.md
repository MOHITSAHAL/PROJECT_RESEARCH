# Development Guide

## Prerequisites

- Python 3.11+
- Node.js 18+
- Docker & Docker Compose
- PostgreSQL 15+
- Redis 7+
- Neo4j 5+ (for graph database)
- Jupyter Lab
- Git with LFS support

## Development Philosophy

This project prioritizes an exceptional development experience with:
- **Hot Reloading**: All services reload automatically on code changes
- **Integrated Testing**: Real AI models and data in development
- **Visual Debugging**: Interactive debugging for agent interactions
- **Rapid Iteration**: Minimal setup time for new features

## Complete Development Environment Setup

### 1. Quick Start (Recommended)
```bash
# Clone and setup everything
git clone <repository>
cd Project_research

# One-command setup with hot reloading
make dev-setup

# Start all services
make dev-start

# Access points:
# Frontend: http://localhost:3000
# API Docs: http://localhost:8000/docs
# Agent Playground: http://localhost:3000/playground
# Jupyter Lab: http://localhost:8888
# Development Dashboard: http://localhost:3001
# Database Admin: http://localhost:5432/admin
```

### 2. Manual Setup (Advanced)
```bash
# Environment setup
cp .env.example .env
cp development/.env.dev .env.local

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt
cd frontend && npm install

# Start infrastructure
docker-compose -f development/docker-compose.dev.yml up -d

# Database setup with sample AI papers
alembic upgrade head
python scripts/seed_ai_papers.py

# Start services with hot reloading
tilt up  # Orchestrates all services with hot reloading
```

### 3. Service-by-Service Startup
```bash
# Terminal 1: Backend API (with hot reload)
cd backend && uvicorn main:app --reload --port 8000

# Terminal 2: AI Service (with agent hot reload)
cd ai-service && python -m celery worker -A agents --reload

# Terminal 3: Data Pipeline
cd data-pipeline && python scheduler.py --dev-mode

# Terminal 4: Frontend (with fast refresh)
cd frontend && npm run dev

# Terminal 5: Jupyter Lab for experimentation
jupyter lab --port=8888 --allow-root
```

## AI Agent Development

### Creating Paper Agents
```python
# Development workflow for new paper agents
from ai_service.agents import PaperAgent
from development.testing import AgentTester

# Create agent from paper
agent = PaperAgent.from_arxiv_id("2017.06135")  # Attention Is All You Need

# Test agent interactively
tester = AgentTester(agent)
await tester.test_query("Explain the transformer architecture")
await tester.test_implementation_guide("pytorch")

# Hot reload agent on code changes
agent.reload()  # Automatically reloads on file changes
```

### Multi-Agent Development
```python
# Develop multi-agent interactions
from ai_service.multi_agent import ResearchNetwork

# Create research network
network = ResearchNetwork("transformer-architecture")
network.add_papers(["attention-is-all-you-need", "bert", "gpt-3"])

# Test agent collaboration
response = await network.synthesize_knowledge(
    "How did transformer architecture evolve from 2017 to 2023?"
)

# Debug agent interactions
network.enable_debug_mode()  # Visual debugging in browser
```

### Data Pipeline with AI Focus
```python
# AI-focused paper ingestion
import arxiv
from data_pipeline.ai_extractor import AIFieldExtractor

# Configure for AI research papers
AI_CATEGORIES = [
    "cs.AI", "cs.LG", "cs.CL", "cs.CV", "cs.RO",  # Core AI
    "stat.ML", "cs.NE", "cs.HC"                    # Related fields
]

client = arxiv.Client()
search = arxiv.Search(
    query=" OR ".join([f"cat:{cat}" for cat in AI_CATEGORIES]),
    max_results=1000,
    sort_by=arxiv.SortCriterion.SubmittedDate
)

# Enhanced processing for AI papers
for paper in client.results(search):
    # Extract AI-specific metadata
    ai_metadata = AIFieldExtractor.extract(paper)
    
    # Create paper agent
    agent = PaperAgent.create(paper, ai_metadata)
    
    # Process GitHub repositories
    if paper.links:
        github_repos = extract_github_links(paper.links)
        agent.analyze_repositories(github_repos)
```

## AI Model Development

### Agent Model Training
```python
# Train specialized models for paper agents
from ai_service.training import AgentTrainer

# Fine-tune models for research paper understanding
trainer = AgentTrainer()

# Train on AI research corpus
trainer.train_paper_understanding_model(
    dataset="ai_papers_corpus",
    model_base="microsoft/DialoGPT-large",
    specialization="research_methodology"
)

# Train implementation guidance model
trainer.train_code_generation_model(
    dataset="github_research_repos",
    model_base="microsoft/CodeBERT-base",
    task="research_to_code"
)
```

### Interactive Model Development
```python
# Develop models with immediate feedback
from development.model_playground import ModelPlayground

# Interactive model testing
playground = ModelPlayground()
playground.load_model("paper_summarization_v2")

# Test with real papers
result = playground.test_summarization(
    paper_id="attention-is-all-you-need",
    style="beginner-friendly"
)

# Immediate feedback loop
playground.adjust_parameters(temperature=0.7)
playground.retest()
```

### Clustering & Relationship Analysis
```python
# Advanced clustering for AI research
from ai_service.clustering import AIResearchClusterer

clusterer = AIResearchClusterer()

# Cluster by methodology, not just topic
clusters = clusterer.cluster_by_methodology(
    papers=recent_ai_papers,
    methods=["supervised_learning", "reinforcement_learning", "unsupervised_learning"]
)

# Build research evolution trees
evolution_tree = clusterer.build_evolution_tree(
    root_paper="perceptron-1957",
    target_papers=modern_ai_papers
)
```

## Comprehensive Testing

### Agent Testing
```bash
# Test individual paper agents
pytest ai-service/tests/test_paper_agents.py -v

# Test multi-agent interactions
pytest ai-service/tests/test_multi_agent.py -v

# Test MCP protocol implementation
pytest ai-service/tests/test_mcp_server.py -v

# Interactive agent testing
python development/test_agents_interactive.py
```

### Integration Testing with Real Data
```bash
# Test with real arXiv papers
pytest tests/integration/test_arxiv_integration.py --use-real-data

# Test GitHub integration
pytest tests/integration/test_github_analysis.py --with-repos

# End-to-end agent workflow tests
pytest tests/e2e/test_agent_workflows.py --slow
```

### Performance Testing
```bash
# Agent response time testing
pytest tests/performance/test_agent_latency.py

# Multi-agent collaboration performance
pytest tests/performance/test_collaboration_speed.py

# Memory usage testing for large paper sets
pytest tests/performance/test_memory_usage.py
```

### Frontend Testing
```bash
# Component tests with agent mocks
cd frontend && npm test

# Agent interaction UI tests
cd frontend && npm run test:agents

# E2E tests with real agents
cd frontend && npm run test:e2e:agents
```

## Development Performance Optimization

### Hot Reloading Configuration
```python
# development/hot_reload.py
class HotReloadManager:
    """Manages hot reloading for all services"""
    
    def __init__(self):
        self.watchers = {
            'backend': FileWatcher('backend/**/*.py', self.reload_backend),
            'ai_service': FileWatcher('ai-service/**/*.py', self.reload_agents),
            'frontend': FileWatcher('frontend/src/**/*', self.reload_frontend)
        }
    
    def reload_agents(self, changed_files):
        """Hot reload paper agents without losing state"""
        for agent_id in active_agents:
            agent = get_agent(agent_id)
            agent.reload_code(preserve_memory=True)
```

### Development Database Optimization
```sql
-- Development-specific indexes for fast iteration
CREATE INDEX CONCURRENTLY idx_papers_dev_search 
ON papers USING gin(to_tsvector('english', title || ' ' || abstract));

-- Fast agent lookup
CREATE INDEX idx_agents_paper_id ON paper_agents(paper_id);

-- Quick development queries
CREATE INDEX idx_papers_ai_category ON papers(category) 
WHERE category LIKE 'cs.AI%' OR category LIKE 'cs.LG%';
```

### Development Monitoring
```python
# Real-time development metrics
from development.monitoring import DevMonitor

monitor = DevMonitor()

# Track agent performance in development
@monitor.track_performance
async def test_agent_query(agent_id: str, query: str):
    start_time = time.time()
    response = await agent.query(query)
    monitor.log_response_time(agent_id, time.time() - start_time)
    return response

# Visual debugging dashboard
monitor.start_dashboard(port=3001)
```

### Interactive Development Tools
```bash
# Start interactive development session
make dev-interactive

# Available tools:
# - Agent REPL: Interactive agent testing
# - Paper Explorer: Browse and analyze papers
# - Code Generator: Generate implementation tutorials
# - Network Visualizer: See agent relationships
# - Performance Profiler: Real-time performance metrics
```