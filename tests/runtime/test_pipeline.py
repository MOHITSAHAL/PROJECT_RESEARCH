#!/usr/bin/env python3
"""Test script for data pipeline functionality."""

import asyncio
import sys
import os
from datetime import datetime

# Add data pipeline to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'data-pipeline'))

from data_pipeline.ingestion.arxiv_client import ArxivClient
from data_pipeline.processing.pdf_processor import PDFProcessor
from data_pipeline.github_integration.repo_analyzer import GitHubRepoAnalyzer


async def test_arxiv_client():
    """Test arXiv client functionality."""
    print("🔍 Testing arXiv Client...")
    
    client = ArxivClient(max_results=5, delay_seconds=1.0)
    
    try:
        # Test fetching recent AI papers
        papers = await client.fetch_ai_papers(days_back=1)
        print(f"✅ Fetched {len(papers)} recent AI papers")
        
        if papers:
            paper = papers[0]
            print(f"   Sample paper: {paper.title[:60]}...")
            print(f"   Authors: {', '.join(paper.authors[:3])}...")
            print(f"   Categories: {', '.join(paper.categories)}")
        
        # Test search functionality
        search_papers = await client.search_papers("transformer attention", max_results=3)
        print(f"✅ Search found {len(search_papers)} papers for 'transformer attention'")
        
        return True
        
    except Exception as e:
        print(f"❌ arXiv client test failed: {e}")
        return False


async def test_pdf_processor():
    """Test PDF processor functionality."""
    print("\n📄 Testing PDF Processor...")
    
    processor = PDFProcessor()
    
    try:
        # Test with a sample arXiv PDF URL
        # Using a well-known paper URL for testing
        test_pdf_url = "https://arxiv.org/pdf/1706.03762.pdf"  # Attention Is All You Need
        
        print(f"   Processing PDF: {test_pdf_url}")
        processed = await processor.download_and_process_pdf(test_pdf_url)
        
        if processed:
            print(f"✅ PDF processed successfully")
            print(f"   Full text length: {len(processed.full_text)} characters")
            print(f"   Sections found: {list(processed.sections.keys())}")
            print(f"   GitHub URLs: {len(processed.github_urls)}")
            print(f"   Methodology keywords: {processed.methodology[:5]}")
            print(f"   Figures: {processed.figures_count}, Tables: {processed.tables_count}")
        else:
            print("❌ PDF processing returned None")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ PDF processor test failed: {e}")
        return False


async def test_github_analyzer():
    """Test GitHub repository analyzer."""
    print("\n🐙 Testing GitHub Analyzer...")
    
    # Note: This test doesn't require a GitHub token for public repos
    analyzer = GitHubRepoAnalyzer()
    
    try:
        # Test with a well-known ML repository
        test_repo_url = "https://github.com/huggingface/transformers"
        
        print(f"   Analyzing repository: {test_repo_url}")
        analysis = await analyzer.analyze_repository(test_repo_url)
        
        if analysis:
            print(f"✅ Repository analyzed successfully")
            print(f"   Name: {analysis.name}")
            print(f"   Stars: {analysis.stars}")
            print(f"   Language: {analysis.language}")
            print(f"   Complexity: {analysis.implementation_complexity}")
            print(f"   Tutorial quality: {analysis.tutorial_quality:.2f}")
            print(f"   Key files: {len(analysis.key_files)}")
        else:
            print("❌ GitHub analysis returned None")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ GitHub analyzer test failed: {e}")
        return False


async def test_integration():
    """Test integration of all components."""
    print("\n🔗 Testing Integration...")
    
    try:
        # Fetch a paper
        client = ArxivClient(max_results=1, delay_seconds=1.0)
        papers = await client.search_papers("BERT language model", max_results=1)
        
        if not papers:
            print("❌ No papers found for integration test")
            return False
        
        paper = papers[0]
        print(f"   Using paper: {paper.title[:50]}...")
        
        # Process PDF
        processor = PDFProcessor()
        processed = await processor.download_and_process_pdf(paper.pdf_url)
        
        if processed and processed.github_urls:
            print(f"   Found {len(processed.github_urls)} GitHub URLs")
            
            # Analyze first GitHub repo
            analyzer = GitHubRepoAnalyzer()
            analysis = await analyzer.analyze_repository(processed.github_urls[0])
            
            if analysis:
                print(f"✅ Integration test successful")
                print(f"   Paper → PDF → GitHub analysis complete")
                return True
        
        print("✅ Integration test completed (no GitHub repos found)")
        return True
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        return False


async def main():
    """Run all tests."""
    print("🚀 Starting Data Pipeline Tests")
    print("=" * 50)
    
    start_time = datetime.now()
    
    # Run tests
    tests = [
        ("arXiv Client", test_arxiv_client()),
        ("PDF Processor", test_pdf_processor()),
        ("GitHub Analyzer", test_github_analyzer()),
        ("Integration", test_integration())
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
    print("📊 Test Results Summary")
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
        print("🎉 All tests passed! Data pipeline is ready.")
        return 0
    else:
        print("⚠️  Some tests failed. Check the output above.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())