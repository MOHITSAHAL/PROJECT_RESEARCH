# LiteLLM Integration Guide

## Overview
The AI Research Paper Intelligence System supports LiteLLM for cost-effective development and testing with multiple LLM providers through a unified interface.

## Configuration

### Environment Variables
```bash
# Enable LiteLLM
USE_LITELLM=true

# LiteLLM Configuration
LITELLM_API_KEY=your-litellm-api-key
LITELLM_BASE_URL=https://api.litellm.ai/v1

# Fallback to standard providers
OPENAI_API_KEY=your-openai-key
ANTHROPIC_API_KEY=your-anthropic-key
```

### Installation
```bash
# Install LiteLLM dependency
pip install litellm==1.17.9

# Or install all AI dependencies
pip install -r backend/requirements.txt
```

## Usage

### 1. Standard Provider Mode (Default)
```bash
# In .env
USE_LITELLM=false
OPENAI_API_KEY=your-openai-key
```

### 2. LiteLLM Mode (Development)
```bash
# In .env
USE_LITELLM=true
LITELLM_API_KEY=your-litellm-key
LITELLM_BASE_URL=https://api.litellm.ai/v1
```

## Supported Models

### Via LiteLLM
- **OpenAI**: gpt-3.5-turbo, gpt-4, gpt-4-turbo-preview
- **Anthropic**: claude-3-sonnet-20240229, claude-3-opus-20240229
- **Open Source**: llama-2-7b-chat, mistral-7b-instruct
- **Others**: Any model supported by LiteLLM

### Direct Integration
- **OpenAI**: All GPT models via OpenAI API
- **Anthropic**: All Claude models via Anthropic API

## Implementation Details

### LLM Configuration Module
```python
# backend/core/llm_config.py
def get_llm_client(model_name, temperature, max_tokens):
    use_litellm = os.getenv("USE_LITELLM", "false").lower() == "true"
    
    if use_litellm:
        return ChatOpenAI(
            model=model_name,
            openai_api_key=os.getenv("LITELLM_API_KEY"),
            openai_api_base=os.getenv("LITELLM_BASE_URL")
        )
    # ... standard provider logic
```

### Agent Integration
```python
# ai-service/agents/paper_agent.py
from backend.core.llm_config import get_llm_client

class PaperAgent:
    def __init__(self, model_name="gpt-3.5-turbo"):
        self.llm = get_llm_client(model_name, temperature=0.1)
```

## Testing

### Configuration Test
```bash
# Test LiteLLM configuration
python tests/runtime/test_litellm_integration.py
```

### Manual Testing
```python
# Test configuration switching
import os
from backend.core.llm_config import get_llm_client

# Test standard mode
os.environ['USE_LITELLM'] = 'false'
llm = get_llm_client("gpt-3.5-turbo")

# Test LiteLLM mode
os.environ['USE_LITELLM'] = 'true'
os.environ['LITELLM_API_KEY'] = 'your-key'
llm = get_llm_client("gpt-3.5-turbo")
```

## Benefits

### Development Advantages
- **Cost Effective**: Reduced API costs during development
- **Model Flexibility**: Easy switching between providers
- **Unified Interface**: Same code works with different models
- **Rate Limiting**: Built-in rate limiting and retry logic

### Production Flexibility
- **Provider Independence**: Not locked to single provider
- **Fallback Options**: Multiple provider support
- **Cost Optimization**: Choose best price/performance ratio
- **Model Comparison**: Easy A/B testing between models

## Configuration Examples

### Development Setup
```bash
# .env for development
USE_LITELLM=true
LITELLM_API_KEY=sk-litellm-xxx
LITELLM_BASE_URL=https://api.litellm.ai/v1
DEFAULT_AGENT_MODEL=gpt-3.5-turbo
```

### Production Setup
```bash
# .env for production
USE_LITELLM=false
OPENAI_API_KEY=sk-xxx
ANTHROPIC_API_KEY=sk-ant-xxx
DEFAULT_AGENT_MODEL=gpt-4
```

### Hybrid Setup
```bash
# Use LiteLLM for some models, direct for others
USE_LITELLM=true
LITELLM_API_KEY=sk-litellm-xxx
OPENAI_API_KEY=sk-xxx  # Fallback for unsupported models
```

## Troubleshooting

### Common Issues

#### 1. Import Errors
```bash
Error: "No module named 'litellm'"
Solution: pip install litellm
```

#### 2. API Key Issues
```bash
Error: "Invalid API key"
Solution: Verify LITELLM_API_KEY is correct
```

#### 3. Base URL Issues
```bash
Error: "Connection failed"
Solution: Check LITELLM_BASE_URL is accessible
```

#### 4. Model Not Supported
```bash
Error: "Model not found"
Solution: Check LiteLLM documentation for supported models
```

### Debug Mode
```python
# Enable debug logging
import os
os.environ['LITELLM_LOG'] = 'DEBUG'

# Test configuration
from backend.core.llm_config import get_llm_client
llm = get_llm_client("gpt-3.5-turbo")
```

## Best Practices

### Development
1. **Use LiteLLM**: Enable for cost-effective development
2. **Test Multiple Models**: Validate with different providers
3. **Monitor Usage**: Track API costs and usage patterns
4. **Cache Responses**: Implement caching for repeated queries

### Production
1. **Direct APIs**: Use direct provider APIs for production
2. **Fallback Strategy**: Configure multiple providers
3. **Rate Limiting**: Implement proper rate limiting
4. **Monitoring**: Track performance and costs

### Security
1. **Environment Variables**: Never hardcode API keys
2. **Key Rotation**: Regularly rotate API keys
3. **Access Control**: Limit API key permissions
4. **Audit Logs**: Monitor API usage patterns

## Integration Status

### ✅ Implemented
- LLM configuration module with LiteLLM support
- Environment variable configuration
- Paper agent integration
- Summarization service integration
- Model switching capability

### ✅ Validated
- Configuration file structure
- Environment variable setup
- Requirements dependency
- Import path resolution
- Model selection logic

### 🧪 Testing Required
- Runtime API calls with real LiteLLM keys
- Multi-model switching validation
- Performance comparison testing
- Error handling validation
- Rate limiting behavior

## Next Steps

1. **Set API Keys**: Configure LiteLLM credentials
2. **Runtime Testing**: Test with real API calls
3. **Performance Benchmarking**: Compare response times
4. **Cost Analysis**: Monitor usage and costs
5. **Production Deployment**: Configure for production use

The LiteLLM integration provides flexible, cost-effective development while maintaining production-ready architecture.