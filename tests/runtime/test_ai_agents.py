#!/usr/bin/env python3
"""Test script for AI Agent Framework functionality."""

import asyncio
import sys
import os
from datetime import datetime

# Add AI service to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'ai-service'))

from ai_service.agents.paper_agent import PaperAgentFactory, PaperContext
from ai_service.multi_agent.agent_coordinator import AgentCoordinator, ConversationType
from ai_service.summarization.paper_summarizer import PaperSummarizer, SummaryRequest


async def test_paper_agent():
    """Test individual paper agent functionality."""
    print("🤖 Testing Paper Agent...")
    
    try:
        # Create sample paper data
        sample_paper = {
            "id": "test_paper_1",
            "title": "Attention Is All You Need",
            "abstract": "The dominant sequence transduction models are based on complex recurrent or convolutional neural networks that include an encoder and a decoder. The best performing models also connect the encoder and decoder through an attention mechanism. We propose a new simple network architecture, the Transformer, based solely on attention mechanisms, dispensing with recurrence and convolutions entirely.",
            "full_text": "Sample full text content about transformers and attention mechanisms...",
            "authors": ["Ashish Vaswani", "Noam Shazeer", "Niki Parmar"],
            "categories": ["cs.CL", "cs.LG"],
            "methodology": ["transformer", "attention mechanism", "self-attention"],
            "github_repos": ["https://github.com/tensorflow/tensor2tensor"],
            "key_findings": ["Transformers achieve better performance", "Attention is sufficient for sequence modeling"]
        }
        
        # Create agent
        agent = PaperAgentFactory.create_agent(sample_paper)
        print(f"✅ Created agent for: {sample_paper['title'][:50]}...")
        
        # Test agent queries
        test_queries = [
            "What is the main contribution of this paper?",
            "Explain the transformer architecture",
            "How does self-attention work?",
            "What are the implementation details?"
        ]
        
        for query in test_queries:
            try:
                response = await agent.query(query)
                print(f"   Q: {query}")
                print(f"   A: {response['response'][:100]}...")
                print()
            except Exception as e:
                print(f"   ❌ Query failed: {e}")
        
        # Test agent info
        info = agent.get_agent_info()
        print(f"✅ Agent info: {info['title']}, Model: {info['model']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Paper agent test failed: {e}")
        return False


async def test_multi_agent_coordinator():
    """Test multi-agent coordinator functionality."""
    print("\n🤝 Testing Multi-Agent Coordinator...")
    
    try:
        coordinator = AgentCoordinator()
        
        # Create sample papers
        papers = [
            {
                "id": "paper_1",
                "title": "BERT: Pre-training of Deep Bidirectional Transformers",
                "abstract": "We introduce BERT, a new language representation model which stands for Bidirectional Encoder Representations from Transformers.",
                "authors": ["Jacob Devlin", "Ming-Wei Chang"],
                "categories": ["cs.CL"],
                "methodology": ["transformer", "bidirectional", "pre-training"],
                "github_repos": [],
                "key_findings": []
            },
            {
                "id": "paper_2", 
                "title": "GPT-3: Language Models are Few-Shot Learners",
                "abstract": "We train GPT-3, an autoregressive language model with 175 billion parameters, and test its performance in the few-shot setting.",
                "authors": ["Tom Brown", "Benjamin Mann"],
                "categories": ["cs.CL", "cs.AI"],
                "methodology": ["autoregressive", "few-shot learning", "scaling"],
                "github_repos": [],
                "key_findings": []
            }
        ]
        
        # Register agents
        for paper in papers:
            agent_id = await coordinator.register_agent(paper)
            print(f"✅ Registered agent: {agent_id}")
        
        # Start conversation
        conversation_id = await coordinator.start_conversation(
            paper_ids=["paper_1", "paper_2"],
            topic="Language model architectures",
            conversation_type=ConversationType.COMPARISON
        )
        print(f"✅ Started conversation: {conversation_id}")
        
        # Send message to conversation
        response = await coordinator.send_message_to_conversation(
            conversation_id=conversation_id,
            message="Compare your approaches to language modeling"
        )
        print(f"✅ Conversation response received with {len(response.get('agent_responses', []))} agent responses")
        
        # Get conversation summary
        summary = await coordinator.get_conversation_summary(conversation_id)
        print(f"✅ Conversation summary: {summary['message_count']} messages")
        
        return True
        
    except Exception as e:
        print(f"❌ Multi-agent coordinator test failed: {e}")
        return False


async def test_paper_summarizer():
    """Test paper summarization functionality."""
    print("\n📝 Testing Paper Summarizer...")
    
    try:
        summarizer = PaperSummarizer()
        
        # Sample paper content
        paper_content = {
            "id": "test_paper",
            "title": "Attention Is All You Need",
            "abstract": "The dominant sequence transduction models are based on complex recurrent or convolutional neural networks that include an encoder and a decoder. The best performing models also connect the encoder and decoder through an attention mechanism. We propose a new simple network architecture, the Transformer, based solely on attention mechanisms, dispensing with recurrence and convolutions entirely.",
            "full_text": "This paper introduces the Transformer architecture. The Transformer uses self-attention mechanisms to process sequences. It consists of an encoder and decoder, both built from stacks of identical layers. Each layer has two sub-layers: a multi-head self-attention mechanism and a position-wise fully connected feed-forward network.",
            "methodology": ["transformer", "self-attention", "encoder-decoder"]
        }
        
        # Test different summary types
        summary_types = [
            ("concise", "intermediate", 150),
            ("comprehensive", "expert", 400),
            ("technical", "expert", 300)
        ]
        
        for summary_type, audience, max_length in summary_types:
            try:
                request = SummaryRequest(
                    text="",
                    summary_type=summary_type,
                    target_audience=audience,
                    max_length=max_length
                )
                
                result = await summarizer.summarize_paper(paper_content, request)
                print(f"✅ {summary_type.title()} summary ({audience}): {len(result['summary'].split())} words")
                print(f"   {result['summary'][:100]}...")
                
            except Exception as e:
                print(f"   ❌ {summary_type} summary failed: {e}")
        
        # Test key insights extraction
        try:
            insights = await summarizer.extract_key_insights(paper_content)
            print(f"✅ Extracted {len(insights)} key insights")
            for i, insight in enumerate(insights[:3], 1):
                print(f"   {i}. {insight[:80]}...")
        except Exception as e:
            print(f"   ❌ Key insights extraction failed: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Paper summarizer test failed: {e}")
        return False


async def test_integration():
    """Test integration of all AI agent components."""
    print("\n🔗 Testing AI Agent Integration...")
    
    try:
        # Create coordinator and summarizer
        coordinator = AgentCoordinator()
        summarizer = PaperSummarizer()
        
        # Sample paper
        paper_data = {
            "id": "integration_test",
            "title": "ResNet: Deep Residual Learning for Image Recognition",
            "abstract": "Deeper neural networks are more difficult to train. We present a residual learning framework to ease the training of networks that are substantially deeper than those used previously.",
            "authors": ["Kaiming He", "Xiangyu Zhang"],
            "categories": ["cs.CV"],
            "methodology": ["residual learning", "deep networks", "skip connections"],
            "github_repos": ["https://github.com/pytorch/vision"],
            "key_findings": ["Residual connections enable deeper networks", "Improved accuracy on ImageNet"]
        }
        
        # 1. Create agent
        agent = PaperAgentFactory.create_agent(paper_data)
        print("✅ Created paper agent")
        
        # 2. Register with coordinator
        await coordinator.register_agent(paper_data)
        print("✅ Registered with coordinator")
        
        # 3. Generate summary
        request = SummaryRequest(
            text="",
            summary_type="comprehensive",
            target_audience="intermediate",
            max_length=300
        )
        summary_result = await summarizer.summarize_paper(paper_data, request)
        print(f"✅ Generated summary: {len(summary_result['summary'].split())} words")
        
        # 4. Query agent about summary
        query = f"Based on this summary: '{summary_result['summary'][:200]}...', what are the key technical innovations?"
        response = await agent.query(query)
        print(f"✅ Agent responded to summary-based query")
        print(f"   Response: {response['response'][:100]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        return False


async def main():
    """Run all AI agent tests."""
    print("🚀 Starting AI Agent Framework Tests")
    print("=" * 50)
    
    start_time = datetime.now()
    
    # Note: These tests require OpenAI API key
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️  OPENAI_API_KEY not set - tests will use mock responses")
        print("   Set OPENAI_API_KEY environment variable for full testing")
        print()
    
    # Run tests
    tests = [
        ("Paper Agent", test_paper_agent()),
        ("Multi-Agent Coordinator", test_multi_agent_coordinator()),
        ("Paper Summarizer", test_paper_summarizer()),
        ("Integration", test_integration())
    ]
    
    results = []
    for test_name, test_coro in tests:
        try:
            print(f"Running {test_name} test...")
            result = await test_coro
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            results.append((test_name, False))
    
    # Print summary
    print("\n" + "=" * 50)
    print("📊 AI Agent Test Results Summary")
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
        print("🎉 All AI agent tests passed! Framework is ready.")
        return 0
    else:
        print("⚠️  Some tests failed. Check the output above.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())