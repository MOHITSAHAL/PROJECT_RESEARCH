# AI Research Paper Intelligence System - Documentation

## 📁 Documentation Structure

### Phase Documentation
- **[phase1/](phase1/)** - Phase 1: Core Infrastructure & Data Pipeline
- **[phase2/](phase2/)** - Phase 2: AI Agent Framework  
- **phase3/** - Phase 3: Intelligent Organization (Coming Soon)

### Quick Links
- **[Project Overview](../README.md)** - Main project documentation
- **[Development Guide](DEVELOPMENT.md)** - Complete development setup
- **[API Documentation](API.md)** - REST and GraphQL APIs
- **[Architecture Guide](ARCHITECTURE.md)** - System design overview

## 🧪 Testing Structure

### Test Organization
- **[../tests/unit/](../tests/unit/)** - Unit tests for individual components
- **[../tests/integration/](../tests/integration/)** - Integration tests between services
- **[../tests/runtime/](../tests/runtime/)** - Runtime tests with real APIs

### Available Tests
- **[test_pipeline.py](../tests/runtime/test_pipeline.py)** - Phase 1 data pipeline testing
- **[test_ai_agents.py](../tests/runtime/test_ai_agents.py)** - Phase 2 AI agent testing
- **[test_litellm_integration.py](../tests/runtime/test_litellm_integration.py)** - LiteLLM integration testing

## 🚀 Quick Start

### 1. Development Setup
```bash
# Clone and setup
git clone <repository>
cd Project_research

# Configure environment
cp .env.example .env
# Edit .env with your API keys

# Start services
docker-compose up -d
```

### 2. Testing
```bash
# Test Phase 1 (Data Pipeline)
python tests/runtime/test_pipeline.py

# Test Phase 2 (AI Agents)
python tests/runtime/test_ai_agents.py

# Test LiteLLM Integration
python tests/runtime/test_litellm_integration.py
```

### 3. API Usage
```bash
# Access API documentation
open http://localhost:8000/docs

# Test endpoints
curl http://localhost:8000/data-pipeline/status
curl http://localhost:8000/ai-agents/capabilities
```

## 📋 Phase Status

| Phase | Status | Documentation | Tests | Features |
|-------|--------|---------------|-------|----------|
| Phase 1 | ✅ Complete | [📖 Docs](phase1/) | [🧪 Tests](../tests/runtime/test_pipeline.py) | Data Pipeline |
| Phase 2 | ✅ Complete | [📖 Docs](phase2/) | [🧪 Tests](../tests/runtime/test_ai_agents.py) | AI Agents |
| Phase 3 | 🚧 Planned | Coming Soon | Coming Soon | Intelligence |

## 🔧 Configuration

### Environment Variables
```bash
# Core APIs
OPENAI_API_KEY=your-openai-key
ANTHROPIC_API_KEY=your-anthropic-key

# LiteLLM (Development)
LITELLM_API_KEY=your-litellm-key
LITELLM_BASE_URL=https://api.litellm.ai/v1
USE_LITELLM=true

# Databases
DATABASE_URL=postgresql://user:pass@localhost:5432/research_papers
REDIS_URL=redis://localhost:6379/0
NEO4J_URI=bolt://localhost:7687
WEAVIATE_URL=http://localhost:8080
```

### LiteLLM Support
The project supports LiteLLM for development and testing:
- Set `USE_LITELLM=true` to enable
- Configure `LITELLM_API_KEY` and `LITELLM_BASE_URL`
- Supports multiple model providers through unified interface

## 📊 Architecture Overview

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Data Pipeline │───▶│   AI Agents      │───▶│  Intelligence   │
│                 │    │                  │    │                 │
│ • arXiv Fetch   │    │ • Paper Agents   │    │ • Clustering    │
│ • PDF Process   │    │ • Multi-Agent    │    │ • Timeline      │
│ • GitHub Analyze│    │ • MCP Protocol   │    │ • Trends        │
│ • Auto Schedule │    │ • Summarization  │    │ • Discovery     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## 🎯 Key Features

### ✅ Implemented
- **Automated Paper Discovery**: Daily arXiv ingestion with AI filtering
- **Interactive AI Agents**: Papers become queryable AI entities
- **Multi-Agent Conversations**: Papers can collaborate and discuss
- **Real-time Communication**: WebSocket-based agent networking
- **GitHub Integration**: Automatic repository analysis
- **Production APIs**: Complete RESTful interface

### 🚧 In Development
- **Semantic Clustering**: AI-powered paper grouping
- **Research Timeline**: Evolution mapping from first to latest papers
- **Trend Analysis**: Emerging research direction identification
- **User Personalization**: Adaptive content and recommendations

## 🔍 Troubleshooting

### Common Issues
1. **Import Errors**: Ensure all dependencies installed
2. **API Key Issues**: Verify keys are set in .env
3. **Docker Issues**: Check `docker-compose ps` for service status
4. **Port Conflicts**: Ensure ports 8000, 8765, 5432, 6379, 7474, 8080 are free

### Getting Help
- Check service logs: `docker-compose logs <service>`
- Review test output for specific error messages
- Ensure all environment variables are properly configured
- Verify API keys have sufficient credits/permissions

## 📈 Performance

### Expected Metrics
- **Paper Processing**: 100-500 papers/day
- **Agent Response**: 2-5 seconds
- **Multi-Agent Conversations**: 10-30 seconds
- **Memory Usage**: ~100MB per active agent
- **Concurrent Agents**: 50+ per instance

### Optimization
- Use LiteLLM for cost-effective development
- Enable caching for frequently accessed papers
- Scale horizontally with multiple Celery workers
- Monitor memory usage and implement agent cleanup

## 🚀 Next Steps

1. **Complete Runtime Testing**: Validate with real API keys
2. **Deploy Phase 3**: Implement intelligent organization
3. **Frontend Development**: Build interactive user interface
4. **Production Deployment**: Set up staging and production environments

The system is designed for production use with comprehensive monitoring, error handling, and scalability features.