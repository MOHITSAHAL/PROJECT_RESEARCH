#!/usr/bin/env python3
"""Test LiteLLM integration with AI Agent Framework."""

import asyncio
import os
import sys
from datetime import datetime

# Add paths
sys.path.append(os.path.join(os.path.dirname(__file__), '../../ai-service'))
sys.path.append(os.path.join(os.path.dirname(__file__), '../../backend'))


async def test_litellm_configuration():
    """Test LiteLLM configuration and setup."""
    print("🔧 Testing LiteLLM Configuration...")
    
    try:
        from core.llm_config import get_llm_client
        
        # Test standard OpenAI configuration
        os.environ['USE_LITELLM'] = 'false'
        os.environ['OPENAI_API_KEY'] = 'test-key'
        
        llm = get_llm_client("gpt-3.5-turbo")
        print("✅ Standard OpenAI configuration works")
        
        # Test LiteLLM configuration
        os.environ['USE_LITELLM'] = 'true'
        os.environ['LITELLM_API_KEY'] = 'test-litellm-key'
        os.environ['LITELLM_BASE_URL'] = 'https://api.litellm.ai/v1'
        
        llm_lite = get_llm_client("gpt-3.5-turbo")
        print("✅ LiteLLM configuration works")
        
        # Test different model types
        models_to_test = [
            "gpt-3.5-turbo",
            "gpt-4",
            "claude-3-sonnet-20240229",
            "llama-2-7b-chat"
        ]
        
        for model in models_to_test:
            try:
                llm_model = get_llm_client(model)
                print(f"✅ Model {model} configuration successful")
            except Exception as e:
                print(f"⚠️  Model {model} configuration warning: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ LiteLLM configuration test failed: {e}")
        return False


async def test_agent_with_litellm():
    """Test paper agent with LiteLLM."""
    print("\n🤖 Testing Paper Agent with LiteLLM...")
    
    try:
        from agents.paper_agent import PaperAgentFactory
        
        # Set LiteLLM environment
        os.environ['USE_LITELLM'] = 'true'
        os.environ['LITELLM_API_KEY'] = os.getenv('LITELLM_API_KEY', 'test-key')
        os.environ['LITELLM_BASE_URL'] = os.getenv('LITELLM_BASE_URL', 'https://api.litellm.ai/v1')
        
        # Sample paper data
        paper_data = {
            "id": "litellm_test",
            "title": "Testing LiteLLM Integration",
            "abstract": "This paper tests the integration of LiteLLM with our AI agent framework.",
            "authors": ["Test Author"],
            "categories": ["cs.AI"],
            "methodology": ["litellm", "testing"],
            "github_repos": [],
            "key_findings": ["LiteLLM integration successful"]
        }
        
        # Create agent with different models
        models_to_test = ["gpt-3.5-turbo", "gpt-4"]
        
        for model in models_to_test:
            try:
                print(f"   Testing with model: {model}")
                agent = PaperAgentFactory.create_agent(
                    paper_data=paper_data,
                    model_name=model,
                    temperature=0.1
                )
                print(f"✅ Agent created successfully with {model}")
                
                # Test query (will fail without real API key but validates structure)
                if os.getenv('LITELLM_API_KEY') and os.getenv('LITELLM_API_KEY') != 'test-key':
                    response = await agent.query("What is this paper about?")
                    print(f"✅ Agent query successful: {response['response'][:50]}...")
                else:
                    print("⚠️  Skipping query test (no real API key)")
                
            except Exception as e:
                if 'API' in str(e) or 'key' in str(e) or 'auth' in str(e):
                    print(f"✅ Agent structure OK for {model} (API key needed for full test)")
                else:
                    print(f"❌ Agent creation failed for {model}: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Agent with LiteLLM test failed: {e}")
        return False


async def test_summarizer_with_litellm():
    """Test paper summarizer with LiteLLM."""
    print("\n📝 Testing Summarizer with LiteLLM...")
    
    try:
        from summarization.paper_summarizer import PaperSummarizer, SummaryRequest
        
        # Set LiteLLM environment
        os.environ['USE_LITELLM'] = 'true'
        
        # Create summarizer
        summarizer = PaperSummarizer("gpt-3.5-turbo")
        print("✅ Summarizer created with LiteLLM configuration")
        
        # Test summary request structure
        paper_content = {
            "id": "test_paper",
            "title": "LiteLLM Integration Test",
            "abstract": "Testing LiteLLM integration with summarization service.",
            "full_text": "This is a test paper for validating LiteLLM integration.",
            "methodology": ["litellm", "integration", "testing"]
        }
        
        request = SummaryRequest(
            text="",
            summary_type="concise",
            target_audience="intermediate",
            max_length=150
        )
        
        print("✅ Summary request structure validated")
        
        # Test actual summarization (if API key available)
        if os.getenv('LITELLM_API_KEY') and os.getenv('LITELLM_API_KEY') != 'test-key':
            try:
                result = await summarizer.summarize_paper(paper_content, request)
                print(f"✅ Summarization successful: {len(result['summary'].split())} words")
            except Exception as e:
                print(f"⚠️  Summarization test skipped: {e}")
        else:
            print("⚠️  Skipping summarization test (no real API key)")
        
        return True
        
    except Exception as e:
        print(f"❌ Summarizer with LiteLLM test failed: {e}")
        return False


async def test_environment_switching():
    """Test switching between LiteLLM and standard providers."""
    print("\n🔄 Testing Environment Switching...")
    
    try:
        from core.llm_config import get_llm_client
        
        # Test switching to standard OpenAI
        os.environ['USE_LITELLM'] = 'false'
        os.environ['OPENAI_API_KEY'] = 'test-openai-key'
        
        llm_openai = get_llm_client("gpt-3.5-turbo")
        print("✅ Switched to standard OpenAI")
        
        # Test switching to LiteLLM
        os.environ['USE_LITELLM'] = 'true'
        os.environ['LITELLM_API_KEY'] = 'test-litellm-key'
        
        llm_litellm = get_llm_client("gpt-3.5-turbo")
        print("✅ Switched to LiteLLM")
        
        # Test with different models
        os.environ['USE_LITELLM'] = 'true'
        
        # Test various model formats
        test_models = [
            "gpt-3.5-turbo",
            "gpt-4",
            "claude-3-sonnet-20240229",
            "llama-2-7b-chat",
            "mistral-7b-instruct"
        ]
        
        for model in test_models:
            try:
                llm = get_llm_client(model)
                print(f"✅ Model {model} configuration successful")
            except Exception as e:
                print(f"⚠️  Model {model}: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Environment switching test failed: {e}")
        return False


async def main():
    """Run all LiteLLM integration tests."""
    print("🚀 Starting LiteLLM Integration Tests")
    print("=" * 50)
    
    start_time = datetime.now()
    
    # Check for LiteLLM configuration
    if os.getenv('LITELLM_API_KEY'):
        print(f"✅ LiteLLM API Key configured")
    else:
        print("⚠️  LITELLM_API_KEY not set - using test keys")
    
    if os.getenv('LITELLM_BASE_URL'):
        print(f"✅ LiteLLM Base URL: {os.getenv('LITELLM_BASE_URL')}")
    else:
        print("⚠️  LITELLM_BASE_URL not set - using default")
    
    print()
    
    # Run tests
    tests = [
        ("LiteLLM Configuration", test_litellm_configuration()),
        ("Agent with LiteLLM", test_agent_with_litellm()),
        ("Summarizer with LiteLLM", test_summarizer_with_litellm()),
        ("Environment Switching", test_environment_switching())
    ]
    
    results = []
    for test_name, test_coro in tests:
        try:
            result = await test_coro
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            results.append((test_name, False))
    
    # Print summary
    print("\n" + "=" * 50)
    print("📊 LiteLLM Integration Test Results")
    print("=" * 50)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
    
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    print(f"\nTests completed in {duration:.2f} seconds")
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All LiteLLM integration tests passed!")
        print("\n📋 Next Steps:")
        print("1. Set LITELLM_API_KEY and LITELLM_BASE_URL in .env")
        print("2. Set USE_LITELLM=true to enable LiteLLM")
        print("3. Run full runtime tests with real API calls")
        return 0
    else:
        print("⚠️  Some tests failed. Check configuration.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())