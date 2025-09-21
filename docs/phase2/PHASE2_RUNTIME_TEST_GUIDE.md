# Phase 2: AI Agent Framework - Runtime Testing Guide

## Quick Runtime Testing Setup

### Prerequisites
```bash
# Required API Keys (set in .env)
OPENAI_API_KEY=your-openai-api-key
ANTHROPIC_API_KEY=your-anthropic-api-key  # Optional
GITHUB_TOKEN=your-github-token            # Optional

# Minimum for testing
OPENAI_API_KEY=sk-...  # Only this is required for basic testing
```

### 1. Environment Setup
```bash
# Navigate to project
cd Project_research

# Copy and configure environment
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY

# Start core services (without full AI dependencies)
docker-compose up -d postgres redis neo4j weaviate
```

### 2. Install AI Dependencies (Local Testing)
```bash
# Install core AI dependencies for testing
pip install openai==1.6.1 langchain==0.1.0 langchain-openai==0.0.5

# Optional: Install all AI dependencies
pip install -r ai-service/requirements.txt
```

### 3. Quick Agent Test
```bash
# Test basic agent creation (mock mode)
python3 -c "
import os
os.environ['OPENAI_API_KEY'] = 'test-key'  # Mock for structure test

# Test agent structure
from ai_service.agents.paper_agent import PaperAgentFactory

sample_paper = {
    'id': 'test_1',
    'title': 'Test Paper',
    'abstract': 'Test abstract',
    'authors': ['Test Author'],
    'categories': ['cs.AI'],
    'methodology': ['test'],
    'github_repos': [],
    'key_findings': []
}

try:
    # This will fail on API call but validates structure
    agent = PaperAgentFactory.create_agent(sample_paper)
    print('✅ Agent structure validation passed')
except Exception as e:
    if 'API' in str(e) or 'key' in str(e):
        print('✅ Agent structure OK (API key needed for full test)')
    else:
        print(f'❌ Agent structure error: {e}')
"
```

## Full Runtime Testing (With API Keys)

### 1. Complete Environment Setup
```bash
# Start all services
docker-compose up -d

# Verify services are running
docker-compose ps

# Check backend is accessible
curl http://localhost:8000/docs
```

### 2. Test Paper Agent Creation
```bash
# Create a paper first (using Phase 1 pipeline)
curl -X POST "http://localhost:8000/data-pipeline/process-paper/1706.03762" \
  -H "Content-Type: application/json"

# Create AI agent for the paper
curl -X POST "http://localhost:8000/ai-agents/create" \
  -H "Content-Type: application/json" \
  -d '{
    "paper_id": "paper_id_from_above",
    "model_name": "gpt-3.5-turbo",
    "temperature": 0.1
  }'
```

### 3. Test Agent Querying
```bash
# Query the agent
curl -X POST "http://localhost:8000/ai-agents/{agent_id}/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is the main contribution of this paper?",
    "context": null
  }'
```

### 4. Test Multi-Agent Conversation
```bash
# Start conversation between multiple agents
curl -X POST "http://localhost:8000/ai-agents/conversations/start" \
  -H "Content-Type: application/json" \
  -d '{
    "paper_ids": ["paper_1", "paper_2"],
    "topic": "transformer architectures",
    "conversation_type": "comparison"
  }'

# Send message to conversation
curl -X POST "http://localhost:8000/ai-agents/conversations/{conv_id}/message" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Compare your approaches to attention mechanisms"
  }'
```

### 5. Test Paper Comparison
```bash
# Compare multiple papers
curl -X POST "http://localhost:8000/ai-agents/compare" \
  -H "Content-Type: application/json" \
  -d '{
    "paper_ids": ["paper_1", "paper_2"],
    "comparison_aspect": "methodology"
  }'
```

## Simplified Testing Script

### Create Test Script
```bash
# Create simple test script
cat > test_runtime.py << 'EOF'
#!/usr/bin/env python3
import asyncio
import os
import sys

# Add paths
sys.path.append('ai-service')
sys.path.append('backend')

async def test_basic_functionality():
    """Test basic AI agent functionality with real API."""
    
    if not os.getenv('OPENAI_API_KEY'):
        print("❌ OPENAI_API_KEY not set")
        return False
    
    try:
        from agents.paper_agent import PaperAgentFactory
        
        # Sample paper data
        paper_data = {
            "id": "test_paper",
            "title": "Attention Is All You Need",
            "abstract": "We propose a new simple network architecture, the Transformer, based solely on attention mechanisms.",
            "authors": ["Ashish Vaswani"],
            "categories": ["cs.CL"],
            "methodology": ["transformer", "attention"],
            "github_repos": [],
            "key_findings": []
        }
        
        # Create agent
        print("🤖 Creating paper agent...")
        agent = PaperAgentFactory.create_agent(paper_data)
        print("✅ Agent created successfully")
        
        # Test query
        print("💬 Testing agent query...")
        response = await agent.query("What is the main contribution?")
        print(f"✅ Agent responded: {response['response'][:100]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    result = asyncio.run(test_basic_functionality())
    exit(0 if result else 1)
EOF

chmod +x test_runtime.py
```

### Run Test
```bash
# Set API key and run test
export OPENAI_API_KEY="your-key-here"
python3 test_runtime.py
```

## Expected Test Results

### ✅ Successful Test Output
```
🤖 Creating paper agent...
✅ Agent created successfully
💬 Testing agent query...
✅ Agent responded: The main contribution of this paper is the introduction of the Transformer architecture...
```

### ❌ Common Issues and Solutions

#### 1. API Key Issues
```
Error: "Invalid API key"
Solution: Verify OPENAI_API_KEY is correctly set
```

#### 2. Import Errors
```
Error: "No module named 'langchain'"
Solution: pip install langchain langchain-openai
```

#### 3. Database Connection
```
Error: "Database connection failed"
Solution: Ensure docker-compose services are running
```

#### 4. Port Conflicts
```
Error: "Port already in use"
Solution: Check docker-compose ps and stop conflicting services
```

## Performance Benchmarks

### Expected Response Times
- **Agent Creation**: 5-10 seconds
- **Simple Query**: 2-5 seconds  
- **Complex Query**: 5-15 seconds
- **Multi-Agent**: 10-30 seconds

### Memory Usage
- **Per Agent**: ~50-100MB
- **Base System**: ~500MB
- **With 10 Agents**: ~1-2GB

### API Rate Limits
- **OpenAI**: 3 requests/minute (free tier)
- **OpenAI**: 3500 requests/minute (paid tier)
- **Recommended**: Start with 1-2 agents for testing

## Troubleshooting Guide

### 1. Agent Creation Fails
```bash
# Check paper exists
curl http://localhost:8000/papers/{paper_id}

# Check API key
echo $OPENAI_API_KEY

# Check logs
docker-compose logs backend
```

### 2. Query Timeout
```bash
# Increase timeout in .env
AGENT_TIMEOUT=120

# Restart services
docker-compose restart backend
```

### 3. Memory Issues
```bash
# Check memory usage
docker stats

# Reduce concurrent agents
# Limit to 2-3 agents for testing
```

### 4. WebSocket Connection Issues
```bash
# Check MCP server
docker-compose logs mcp-server

# Test WebSocket connection
curl -i -N -H "Connection: Upgrade" \
     -H "Upgrade: websocket" \
     -H "Sec-WebSocket-Key: test" \
     -H "Sec-WebSocket-Version: 13" \
     http://localhost:8765/
```

## Validation Checklist

### ✅ Basic Functionality
- [ ] Agent creation succeeds
- [ ] Agent responds to queries
- [ ] Responses are relevant and coherent
- [ ] Error handling works properly

### ✅ Multi-Agent Features
- [ ] Multiple agents can be created
- [ ] Conversations can be started
- [ ] Agents respond in conversations
- [ ] Message routing works correctly

### ✅ Performance
- [ ] Response times are acceptable
- [ ] Memory usage is reasonable
- [ ] No memory leaks observed
- [ ] Concurrent operations work

### ✅ Integration
- [ ] Backend APIs work correctly
- [ ] Database integration functions
- [ ] Error responses are proper
- [ ] Logging is comprehensive

## Success Criteria

### Minimum Viable Test
✅ **PASS**: Agent creation + single query response

### Full Feature Test  
✅ **PASS**: Multi-agent conversation + paper comparison

### Performance Test
✅ **PASS**: <10s agent creation, <5s query response

### Integration Test
✅ **PASS**: End-to-end pipeline → agent → query workflow

## Next Steps After Testing

### If Tests Pass ✅
1. **Document Results**: Record performance metrics
2. **Optimize Configuration**: Tune timeouts and limits
3. **Prepare Production**: Set up production API keys
4. **Begin Phase 3**: Start intelligent organization implementation

### If Tests Fail ❌
1. **Debug Issues**: Use troubleshooting guide
2. **Check Dependencies**: Verify all requirements installed
3. **Review Configuration**: Validate environment setup
4. **Seek Support**: Check logs and error messages

The AI Agent Framework is ready for runtime testing and should perform excellently with proper API key configuration!