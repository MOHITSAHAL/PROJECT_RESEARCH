# Implementation Guide

## Overview

This guide provides step-by-step instructions for setting up and running the AI Research Paper Intelligence System. The system is designed to transform research papers into interactive AI agents that can answer questions, provide implementation guidance, and collaborate with each other.

## Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend API   │    │   AI Agents     │
│   (React)       │◄──►│   (FastAPI)     │◄──►│   (LangChain)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   User Interface│    │   PostgreSQL    │    │   Redis Cache   │
│   Components    │    │   Database      │    │   & Sessions    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │                       │
                                ▼                       ▼
                     ┌─────────────────┐    ┌─────────────────┐
                     │   Neo4j Graph   │    │   Vector DB     │
                     │   Database      │    │   (Weaviate)    │
                     └─────────────────┘    └─────────────────┘
```

## Prerequisites

### System Requirements
- **Docker**: Version 20.10 or higher
- **Docker Compose**: Version 2.0 or higher
- **Memory**: Minimum 8GB RAM (16GB recommended)
- **Storage**: 10GB free space for development

### API Keys Required
- **OpenAI API Key**: For GPT models (required)
- **Anthropic API Key**: For Claude models (optional)
- **Pinecone API Key**: If using Pinecone instead of Weaviate (optional)

## Installation Steps

### 1. Clone and Setup

```bash
# Clone the repository
git clone <repository-url>
cd Project_research

# Copy environment configuration
cp .env.example .env
```

### 2. Configure Environment Variables

Edit the `.env` file with your configuration:

```bash
# Required: Add your API keys
OPENAI_API_KEY=your-openai-api-key-here
ANTHROPIC_API_KEY=your-anthropic-api-key-here  # Optional

# Database Configuration (defaults work for development)
DATABASE_URL=postgresql://postgres:password@postgres:5432/research_papers
NEO4J_URI=bolt://neo4j:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password
REDIS_URL=redis://redis:6379/0

# Vector Database (choose one)
VECTOR_DB_PROVIDER=weaviate
WEAVIATE_URL=http://weaviate:8080
# OR use Pinecone
# VECTOR_DB_PROVIDER=pinecone
# PINECONE_API_KEY=your-pinecone-key
# PINECONE_ENVIRONMENT=your-pinecone-environment

# Application Settings
ENVIRONMENT=development
DEBUG=true
SECRET_KEY=your-secret-key-change-in-production
```

### 3. Start the Development Environment

```bash
# Start all services
docker-compose up -d

# Check that all services are running
docker-compose ps

# View logs if needed
docker-compose logs -f backend
```

### 4. Initialize the Database

```bash
# Run database migrations
docker-compose exec backend alembic upgrade head

# Verify database is set up
docker-compose exec backend python -c "
from database.connection import db_manager
print('Database health:', db_manager.health_check())
"
```

### 5. Verify Installation

```bash
# Check API health
curl http://localhost:8000/health

# Check API documentation
open http://localhost:8000/docs

# Check Neo4j browser
open http://localhost:7474  # Login: neo4j/password

# Check Grafana dashboard
open http://localhost:3001  # Login: admin/admin
```

## Usage Examples

### 1. Create a User Account

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "researcher",
    "email": "researcher@example.com", 
    "password": "SecurePass123",
    "full_name": "Research User",
    "research_interests": ["machine_learning", "nlp"]
  }'
```

### 2. Login and Get Token

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "researcher",
    "password": "SecurePass123"
  }'
```

### 3. Create a Research Paper

```bash
curl -X POST http://localhost:8000/api/v1/papers/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "title": "Attention Is All You Need",
    "abstract": "The dominant sequence transduction models are based on complex recurrent or convolutional neural networks...",
    "authors": ["Ashish Vaswani", "Noam Shazeer", "Niki Parmar"],
    "categories": ["cs.CL", "cs.LG"],
    "arxiv_id": "1706.03762",
    "published_date": "2017-06-12T00:00:00"
  }'
```

### 4. Create an AI Agent for the Paper

```bash
curl -X POST http://localhost:8000/api/v1/agents/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "paper_id": "PAPER_ID_FROM_STEP_3",
    "agent_type": "interactive",
    "model_name": "gpt-3.5-turbo",
    "specialization": "research_assistant"
  }'
```

### 5. Query the Agent

```bash
curl -X POST http://localhost:8000/api/v1/agents/AGENT_ID/query \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "query": "Can you explain the main contributions of this paper?",
    "context": {
      "user_level": "intermediate",
      "focus": "methodology"
    }
  }'
```

### 6. Generate Implementation Guide

```bash
curl -X POST http://localhost:8000/api/v1/agents/AGENT_ID/implementation-guide \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "framework": "pytorch",
    "complexity_level": "intermediate",
    "include_github_analysis": true
  }'
```

### 7. Multi-Agent Collaboration

```bash
curl -X POST http://localhost:8000/api/v1/agents/multi-agent/collaborate \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "agent_ids": ["AGENT_ID_1", "AGENT_ID_2", "AGENT_ID_3"],
    "task": "compare_architectures",
    "query": "How do transformer architectures compare across different papers?",
    "collaboration_mode": "parallel"
  }'
```

## WebSocket Communication

### Real-time Agent Chat

```javascript
// Connect to agent WebSocket
const ws = new WebSocket('ws://localhost:8000/api/v1/agents/AGENT_ID/chat?user_id=USER_ID');

// Send message
ws.send(JSON.stringify({
  query: "Explain the attention mechanism",
  context: {
    user_level: "beginner"
  }
}));

// Receive response
ws.onmessage = function(event) {
  const response = JSON.parse(event.data);
  console.log('Agent response:', response);
};
```

## Development Workflow

### 1. Making Changes to the Backend

```bash
# The backend has hot reloading enabled
# Edit files in ./backend/ and changes will be reflected immediately

# View backend logs
docker-compose logs -f backend

# Restart backend if needed
docker-compose restart backend
```

### 2. Database Migrations

```bash
# Create a new migration
docker-compose exec backend alembic revision --autogenerate -m "Description of changes"

# Apply migrations
docker-compose exec backend alembic upgrade head

# Rollback if needed
docker-compose exec backend alembic downgrade -1
```

### 3. Adding New Agent Capabilities

```python
# Edit backend/agents/paper_agent.py
# Add new methods to the PaperAgent class

async def new_capability(self, params):
    """New agent capability."""
    # Implementation here
    pass

# Register the capability in agent_factory.py
capabilities = [
    "existing_capability",
    "new_capability"  # Add here
]
```

### 4. Testing

```bash
# Run backend tests
docker-compose exec backend pytest

# Run specific test file
docker-compose exec backend pytest tests/test_agents.py

# Run with coverage
docker-compose exec backend pytest --cov=.
```

## Monitoring and Debugging

### 1. Application Logs

```bash
# View all logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f backend
docker-compose logs -f postgres
docker-compose logs -f neo4j
```

### 2. Database Access

```bash
# PostgreSQL
docker-compose exec postgres psql -U postgres -d research_papers

# Neo4j Browser
open http://localhost:7474
# Login: neo4j/password

# Redis CLI
docker-compose exec redis redis-cli
```

### 3. Monitoring Dashboard

```bash
# Grafana Dashboard
open http://localhost:3001
# Login: admin/admin

# Prometheus Metrics
open http://localhost:9090
```

### 4. Health Checks

```bash
# Application health
curl http://localhost:8000/health

# Database health
curl http://localhost:8000/api/v1/health/databases

# Agent status
curl http://localhost:8000/api/v1/agents/health
```

## Troubleshooting

### Common Issues

#### 1. Services Won't Start

```bash
# Check Docker resources
docker system df
docker system prune  # Clean up if needed

# Check port conflicts
netstat -tulpn | grep :8000
netstat -tulpn | grep :5432
```

#### 2. Database Connection Issues

```bash
# Check PostgreSQL logs
docker-compose logs postgres

# Verify database is accessible
docker-compose exec postgres pg_isready -U postgres

# Reset database if needed
docker-compose down -v
docker-compose up -d postgres
docker-compose exec backend alembic upgrade head
```

#### 3. Agent Creation Fails

```bash
# Check if API keys are set
docker-compose exec backend env | grep API_KEY

# Check agent service logs
docker-compose logs -f backend | grep agent

# Verify paper exists
curl http://localhost:8000/api/v1/papers/PAPER_ID
```

#### 4. Memory Issues

```bash
# Check Docker memory usage
docker stats

# Increase Docker memory limit in Docker Desktop
# Or reduce services:
docker-compose up -d backend postgres redis  # Minimal setup
```

### Performance Optimization

#### 1. Database Optimization

```sql
-- Check slow queries in PostgreSQL
SELECT query, mean_time, calls 
FROM pg_stat_statements 
ORDER BY mean_time DESC 
LIMIT 10;

-- Analyze table statistics
ANALYZE papers;
ANALYZE paper_agents;
```

#### 2. Redis Optimization

```bash
# Check Redis memory usage
docker-compose exec redis redis-cli info memory

# Monitor Redis commands
docker-compose exec redis redis-cli monitor
```

#### 3. Agent Performance

```bash
# Check agent response times
curl http://localhost:8000/api/v1/agents/AGENT_ID/performance

# Monitor agent metrics
curl http://localhost:8000/metrics | grep agent
```

## Production Deployment

### AWS Deployment Preparation

```bash
# Build production images
docker build -t research-papers/backend:latest ./backend
docker build -t research-papers/frontend:latest ./frontend

# Tag for ECR
docker tag research-papers/backend:latest YOUR_ECR_URI/backend:latest

# Push to ECR
docker push YOUR_ECR_URI/backend:latest
```

### Environment Variables for Production

```bash
# Production .env
ENVIRONMENT=production
DEBUG=false
DATABASE_URL=postgresql://user:pass@rds-endpoint:5432/research_papers
NEO4J_URI=bolt://neo4j-cluster:7687
REDIS_URL=redis://elasticache-endpoint:6379
AWS_REGION=us-east-1
S3_BUCKET_NAME=research-papers-prod
```

## Next Steps

1. **Explore the API**: Visit http://localhost:8000/docs for interactive API documentation
2. **Create Agents**: Start with simple paper agents and experiment with different configurations
3. **Multi-Agent Collaboration**: Try different collaboration modes (sequential, parallel, debate, consensus)
4. **Custom Capabilities**: Extend agents with custom capabilities for your specific use case
5. **Integration**: Integrate with your existing research workflow or tools

## Support

- **Documentation**: Check the `/docs` directory for detailed documentation
- **API Reference**: http://localhost:8000/docs
- **Logs**: Use `docker-compose logs -f` to debug issues
- **Health Checks**: Monitor http://localhost:8000/health for system status