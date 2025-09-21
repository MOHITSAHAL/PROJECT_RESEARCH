# API Documentation

## Core Endpoints

### Paper Management

#### GET /api/papers
Retrieve papers with AI-focused filtering and pagination
```json
{
  "query": "transformer architecture",
  "categories": ["cs.AI", "cs.LG", "cs.CL"],
  "date_range": {"start": "2017-01-01", "end": "2024-12-31"},
  "methodology": ["deep_learning", "attention_mechanism"],
  "has_github": true,
  "limit": 50,
  "offset": 0
}
```

#### GET /api/papers/{paper_id}
Get comprehensive paper information including agent capabilities
```json
{
  "paper_id": "attention-is-all-you-need",
  "title": "Attention Is All You Need",
  "summary": "AI-generated contextual summary",
  "github_repos": ["https://github.com/tensorflow/tensor2tensor"],
  "agent_available": true,
  "implementation_guide_available": true,
  "related_papers": [...],
  "research_lineage": [...]
}
```

#### POST /api/papers/batch-process
Trigger batch processing for new AI papers from multiple sources

### AI Research Topics & Evolution

#### GET /api/topics
List AI research topics with evolution metrics and agent networks
```json
{
  "topics": [
    {
      "id": "transformer-architecture",
      "name": "Transformer Architecture",
      "paper_count": 1247,
      "agent_network_size": 15,
      "evolution_score": 0.92,
      "trending": true,
      "foundational_paper": "attention-is-all-you-need",
      "latest_breakthrough": "gpt-4-architecture"
    }
  ]
}
```

#### GET /api/topics/{topic_id}/timeline
Get complete research evolution timeline with breakthrough analysis
```json
{
  "topic_id": "transformer-architecture",
  "timeline": [
    {
      "paper_id": "attention-is-all-you-need",
      "title": "Attention Is All You Need",
      "date": "2017-06-12",
      "breakthrough_score": 0.98,
      "influence_score": 0.95,
      "agent_available": true,
      "implementation_complexity": "intermediate"
    }
  ],
  "evolution_insights": {
    "key_innovations": [...],
    "methodology_progression": [...],
    "research_gaps": [...]
  }
}
```

#### GET /api/topics/{topic_id}/agent-network
Get network of paper agents for collaborative analysis

### AI Agent Endpoints

#### POST /api/agents/create
Create a paper agent from research paper
```json
{
  "paper_id": "attention-is-all-you-need",
  "agent_type": "interactive",
  "specialization": "implementation_guide",
  "model": "gpt-4"
}
```

#### POST /api/agents/{agent_id}/query
Query a paper agent with contextual understanding
```json
{
  "query": "Explain the multi-head attention mechanism",
  "context": {
    "user_level": "intermediate",
    "focus": "implementation",
    "framework_preference": "pytorch"
  }
}
```

#### POST /api/agents/{agent_id}/implementation-guide
Generate step-by-step implementation guide
```json
{
  "framework": "pytorch",
  "complexity_level": "beginner",
  "include_github_analysis": true,
  "interactive_mode": true
}
```

#### POST /api/agents/multi-agent/collaborate
Initiate multi-agent collaboration for complex queries
```json
{
  "agent_ids": ["transformer-agent", "bert-agent", "gpt-agent"],
  "task": "compare_architectures",
  "query": "How did transformer architecture evolve from 2017 to 2023?"
}
```

### Paper Analysis & Intelligence

#### POST /api/papers/{paper_id}/analyze
Comprehensive AI analysis of research paper
```json
{
  "analysis_type": ["methodology", "implementation", "impact"],
  "include_github_analysis": true,
  "generate_tutorial": true
}
```

#### GET /api/papers/{paper_id}/github-analysis
Analyze associated GitHub repositories
```json
{
  "repositories": [
    {
      "url": "https://github.com/tensorflow/tensor2tensor",
      "analysis": {
        "key_files": [...],
        "implementation_quality": 0.87,
        "tutorial_available": true,
        "complexity_score": 0.65
      }
    }
  ]
}
```

#### GET /api/papers/trending-ai
Get trending AI papers with agent availability

### Research Networks & Collaboration

#### POST /api/research-networks/create
Create research network for topic exploration
```json
{
  "topic": "transformer-evolution",
  "papers": ["attention-is-all-you-need", "bert", "gpt-3", "gpt-4"],
  "analysis_depth": "comprehensive"
}
```

#### GET /api/research-networks/{network_id}/synthesize
Synthesize knowledge across multiple papers
```json
{
  "query": "What are the key innovations in transformer architecture?",
  "synthesis_type": "evolutionary",
  "include_implementation_details": true
}
```

### User Dashboard & Personalization

#### GET /api/users/{user_id}/dashboard
AI-curated research dashboard
```json
{
  "personalized_papers": [...],
  "active_agents": [...],
  "research_progress": {...},
  "trending_in_interests": [...],
  "implementation_tutorials": [...]
}
```

#### POST /api/users/{user_id}/interests
Update AI research interests and agent preferences
```json
{
  "research_areas": ["transformer_architecture", "reinforcement_learning"],
  "experience_level": "intermediate",
  "preferred_frameworks": ["pytorch", "tensorflow"],
  "notification_preferences": {
    "new_papers": true,
    "agent_updates": true,
    "implementation_guides": true
  }
}
```

## Development & Testing Endpoints

### Agent Development
- `GET /dev/agents/playground` - Interactive agent testing interface
- `POST /dev/agents/hot-reload` - Hot reload agent code
- `GET /dev/agents/debug/{agent_id}` - Agent debugging interface

### Performance Monitoring
- `GET /dev/metrics/agents` - Agent performance metrics
- `GET /dev/metrics/collaboration` - Multi-agent collaboration metrics
- `GET /dev/health/agents` - Agent health status

## WebSocket Endpoints

### Real-time Agent Communication
- `/ws/agents/{agent_id}/chat` - Real-time conversation with paper agents
- `/ws/agents/multi-agent/{session_id}` - Multi-agent collaboration sessions
- `/ws/research-networks/{network_id}` - Research network updates

### Live Research Updates
- `/ws/papers/ai-live` - Live AI paper ingestion updates
- `/ws/topics/ai-trending` - Real-time AI research trending topics
- `/ws/implementations/new` - New implementation guides and tutorials

## GraphQL Endpoint

### Complex Research Queries
```graphql
# GET /graphql
query ResearchEvolution($topic: String!, $timeRange: DateRange!) {
  researchTopic(name: $topic) {
    timeline(range: $timeRange) {
      papers {
        id
        title
        breakthroughScore
        agent {
          available
          capabilities
        }
        githubRepos {
          url
          analysisScore
        }
      }
    }
    agentNetwork {
      nodes {
        paperId
        agentId
        capabilities
      }
      collaborations {
        agents
        successRate
      }
    }
  }
}
```

## MCP (Model Context Protocol) Endpoints

### Agent-to-Agent Communication
- `/mcp/agents/register` - Register agent for MCP communication
- `/mcp/agents/message` - Send messages between agents
- `/mcp/agents/broadcast` - Broadcast to agent network
- `/mcp/agents/collaborate` - Initiate collaborative tasks

## Authentication & Rate Limiting

### API Keys
```bash
# Header format
Authorization: Bearer your_api_key_here
```

### Rate Limits
- **Standard API**: 1000 requests/hour
- **Agent Queries**: 100 requests/hour
- **Multi-Agent Collaboration**: 20 sessions/hour
- **Implementation Generation**: 10 requests/hour

## Error Handling

### Standard Error Format
```json
{
  "error": {
    "code": "AGENT_UNAVAILABLE",
    "message": "Paper agent is currently being updated",
    "details": {
      "paper_id": "attention-is-all-you-need",
      "estimated_availability": "2024-01-15T10:30:00Z"
    }
  }
}
```

### Agent-Specific Errors
- `AGENT_CREATION_FAILED`: Failed to create paper agent
- `AGENT_QUERY_TIMEOUT`: Agent query exceeded timeout
- `MULTI_AGENT_SYNC_ERROR`: Multi-agent synchronization failed
- `IMPLEMENTATION_GENERATION_ERROR`: Failed to generate implementation guide