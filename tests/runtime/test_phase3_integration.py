#!/usr/bin/env python3
"""
Phase 3: Intelligent Organization - Integration Testing
Tests all Phase 3 components and their integration
"""

import asyncio
import sys
import os
import json
from typing import List, Dict, Any

# Add project paths
sys.path.append('/home/mohit/workspace/Project_research/backend')
sys.path.append('/home/mohit/workspace/Project_research/ai-service')

# Test data
SAMPLE_PAPERS = [
    {
        "id": "paper_1",
        "title": "Attention Is All You Need",
        "abstract": "We propose a new simple network architecture, the Transformer, based solely on attention mechanisms, dispensing with recurrence and convolutions entirely.",
        "authors": ["Ashish Vaswani", "Noam Shazeer", "Niki Parmar"],
        "keywords": ["transformer", "attention", "neural networks", "nlp"],
        "categories": ["cs.CL", "cs.LG"],
        "published_year": 2017,
        "citations": ["paper_2", "paper_3"],
        "references": [],
        "citation_count": 50000,
        "venue": "NIPS"
    },
    {
        "id": "paper_2", 
        "title": "BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding",
        "abstract": "We introduce a new language representation model called BERT, which stands for Bidirectional Encoder Representations from Transformers.",
        "authors": ["Jacob Devlin", "Ming-Wei Chang", "Kenton Lee"],
        "keywords": ["bert", "transformer", "language model", "nlp"],
        "categories": ["cs.CL"],
        "published_year": 2018,
        "citations": ["paper_4"],
        "references": ["paper_1"],
        "citation_count": 40000,
        "venue": "NAACL"
    },
    {
        "id": "paper_3",
        "title": "GPT-3: Language Models are Few-Shot Learners", 
        "abstract": "We show that scaling up language models greatly improves task-agnostic, few-shot performance.",
        "authors": ["Tom Brown", "Benjamin Mann", "Nick Ryder"],
        "keywords": ["gpt", "language model", "few-shot learning", "nlp"],
        "categories": ["cs.CL", "cs.AI"],
        "published_year": 2020,
        "citations": [],
        "references": ["paper_1", "paper_2"],
        "citation_count": 30000,
        "venue": "NeurIPS"
    },
    {
        "id": "paper_4",
        "title": "RoBERTa: A Robustly Optimized BERT Pretraining Approach",
        "abstract": "We present a replication study of BERT pretraining that carefully measures the impact of many key hyperparameters and training data size.",
        "authors": ["Yinhan Liu", "Myle Ott", "Naman Goyal"],
        "keywords": ["roberta", "bert", "pretraining", "nlp"],
        "categories": ["cs.CL"],
        "published_year": 2019,
        "citations": [],
        "references": ["paper_1", "paper_2"],
        "citation_count": 25000,
        "venue": "arXiv"
    },
    {
        "id": "paper_5",
        "title": "ResNet: Deep Residual Learning for Image Recognition",
        "abstract": "We present a residual learning framework to ease the training of networks that are substantially deeper than those used previously.",
        "authors": ["Kaiming He", "Xiangyu Zhang", "Shaoqing Ren"],
        "keywords": ["resnet", "residual learning", "computer vision", "cnn"],
        "categories": ["cs.CV"],
        "published_year": 2015,
        "citations": ["paper_6"],
        "references": [],
        "citation_count": 60000,
        "venue": "CVPR"
    },
    {
        "id": "paper_6",
        "title": "EfficientNet: Rethinking Model Scaling for Convolutional Neural Networks",
        "abstract": "We systematically study model scaling and identify that carefully balancing network depth, width, and resolution can lead to better performance.",
        "authors": ["Mingxing Tan", "Quoc V. Le"],
        "keywords": ["efficientnet", "model scaling", "computer vision", "cnn"],
        "categories": ["cs.CV", "cs.LG"],
        "published_year": 2019,
        "citations": [],
        "references": ["paper_5"],
        "citation_count": 15000,
        "venue": "ICML"
    }
]

SAMPLE_USER_INTERACTIONS = [
    {"paper": SAMPLE_PAPERS[0], "action": "view", "timestamp": "2024-01-01"},
    {"paper": SAMPLE_PAPERS[1], "action": "bookmark", "timestamp": "2024-01-02"},
    {"paper": SAMPLE_PAPERS[2], "action": "download", "timestamp": "2024-01-03"},
    {"paper": SAMPLE_PAPERS[0], "action": "cite", "timestamp": "2024-01-04"},
    {"paper": SAMPLE_PAPERS[3], "action": "rate_positive", "timestamp": "2024-01-05"}
]

def test_semantic_clustering():
    """Test semantic clustering functionality"""
    print("🧪 Testing Semantic Clustering...")
    
    try:
        from clustering.semantic_clusterer import SemanticClusterer
        
        clusterer = SemanticClusterer()
        
        # Test clustering
        result = clusterer.cluster_papers(SAMPLE_PAPERS, method="kmeans")
        
        assert "clusters" in result
        assert "topics" in result
        assert "embeddings" in result
        assert len(result["clusters"]) > 0
        
        print(f"   ✅ Created {len(result['clusters'])} clusters")
        print(f"   ✅ Generated embeddings for {len(SAMPLE_PAPERS)} papers")
        
        # Test similarity search
        similar_papers = clusterer.find_similar_papers(
            SAMPLE_PAPERS[0], SAMPLE_PAPERS[1:], top_k=3
        )
        
        assert len(similar_papers) <= 3
        assert all("similarity_score" in paper for paper in similar_papers)
        
        print(f"   ✅ Found {len(similar_papers)} similar papers")
        print("   ✅ Semantic clustering tests passed!")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Semantic clustering test failed: {e}")
        return False

def test_topic_modeling():
    """Test topic modeling functionality"""
    print("🧪 Testing Topic Modeling...")
    
    try:
        from clustering.topic_modeler import TopicModeler
        
        modeler = TopicModeler(n_topics=3)
        
        # Test topic fitting
        result = modeler.fit_topics(SAMPLE_PAPERS)
        
        assert "topics" in result
        assert "paper_topics" in result
        assert len(result["topics"]) == 3
        assert len(result["paper_topics"]) == len(SAMPLE_PAPERS)
        
        print(f"   ✅ Identified {len(result['topics'])} topics")
        print(f"   ✅ Assigned topics to {len(result['paper_topics'])} papers")
        
        # Test topic prediction
        new_papers = [SAMPLE_PAPERS[0]]  # Use first paper as "new"
        predictions = modeler.predict_topics(new_papers)
        
        assert len(predictions) == 1
        assert "dominant_topic" in predictions[0]
        
        print(f"   ✅ Predicted topics for new papers")
        
        # Test topic evolution
        papers_by_year = {
            2017: [SAMPLE_PAPERS[0]],
            2018: [SAMPLE_PAPERS[1]],
            2019: [SAMPLE_PAPERS[3], SAMPLE_PAPERS[5]],
            2020: [SAMPLE_PAPERS[2]]
        }
        
        evolution = modeler.get_topic_evolution(papers_by_year)
        
        assert "evolution" in evolution
        assert "trend_analysis" in evolution
        
        print(f"   ✅ Analyzed topic evolution over time")
        print("   ✅ Topic modeling tests passed!")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Topic modeling test failed: {e}")
        return False

def test_citation_analysis():
    """Test citation analysis functionality"""
    print("🧪 Testing Citation Analysis...")
    
    try:
        from genealogy.citation_analyzer import CitationAnalyzer
        
        analyzer = CitationAnalyzer()
        
        # Test network building
        result = analyzer.build_citation_network(SAMPLE_PAPERS)
        
        assert "network_stats" in result
        assert "metrics" in result
        assert "influential_papers" in result
        assert "research_lineages" in result
        
        stats = result["network_stats"]
        assert stats["nodes"] == len(SAMPLE_PAPERS)
        assert stats["edges"] >= 0
        
        print(f"   ✅ Built citation network with {stats['nodes']} nodes, {stats['edges']} edges")
        print(f"   ✅ Found {len(result['influential_papers'])} influential papers")
        print(f"   ✅ Traced {len(result['research_lineages'])} research lineages")
        
        # Test paper impact analysis
        impact = analyzer.analyze_paper_impact("paper_1")
        
        assert "paper_info" in impact
        assert "direct_impact" in impact
        assert "network_position" in impact
        
        print(f"   ✅ Analyzed impact for paper_1")
        
        # Test research paths
        paths = analyzer.find_research_paths("paper_1", "paper_3")
        
        print(f"   ✅ Found {len(paths)} research paths")
        print("   ✅ Citation analysis tests passed!")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Citation analysis test failed: {e}")
        return False

def test_recommendation_engine():
    """Test recommendation engine functionality"""
    print("🧪 Testing Recommendation Engine...")
    
    try:
        from discovery.recommendation_engine import RecommendationEngine
        
        engine = RecommendationEngine()
        
        # Test user profile building
        profile = engine.build_user_profile("test_user", SAMPLE_USER_INTERACTIONS)
        
        assert "user_id" in profile
        assert "interests" in profile
        assert "expertise_level" in profile
        assert profile["user_id"] == "test_user"
        
        print(f"   ✅ Built user profile with expertise level: {profile['expertise_level']}")
        print(f"   ✅ Identified {len(profile['interests'])} interests")
        
        # Test content-based recommendations
        content_recs = engine.recommend_papers("test_user", SAMPLE_PAPERS, top_k=3, method="content")
        
        assert len(content_recs) <= 3
        assert all("recommendation_score" in rec for rec in content_recs)
        assert all("recommendation_reason" in rec for rec in content_recs)
        
        print(f"   ✅ Generated {len(content_recs)} content-based recommendations")
        
        # Test cold start recommendations
        cold_recs = engine._cold_start_recommendations(SAMPLE_PAPERS, top_k=3)
        
        assert len(cold_recs) <= 3
        
        print(f"   ✅ Generated {len(cold_recs)} cold start recommendations")
        
        # Test interaction updates
        engine.update_user_interaction("test_user", "paper_1", "view", 4.5)
        
        print(f"   ✅ Updated user interactions")
        print("   ✅ Recommendation engine tests passed!")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Recommendation engine test failed: {e}")
        return False

def test_trend_analysis():
    """Test trend analysis functionality"""
    print("🧪 Testing Trend Analysis...")
    
    try:
        from discovery.trend_analyzer import TrendAnalyzer
        
        analyzer = TrendAnalyzer()
        
        # Test trend analysis
        result = analyzer.analyze_research_trends(SAMPLE_PAPERS, time_window=5)
        
        assert "keyword_trends" in result
        assert "author_trends" in result
        assert "venue_trends" in result
        assert "emerging_topics" in result
        assert "predictions" in result
        
        keyword_trends = result["keyword_trends"]
        assert "trending_up" in keyword_trends
        assert "trending_down" in keyword_trends
        assert "analysis_summary" in keyword_trends
        
        print(f"   ✅ Analyzed keyword trends")
        print(f"   ✅ Found {len(result['emerging_topics'])} emerging topics")
        print(f"   ✅ Generated predictions for future trends")
        
        author_trends = result["author_trends"]
        assert "productive_authors" in author_trends
        assert "collaboration_trends" in author_trends
        
        print(f"   ✅ Analyzed {len(author_trends['productive_authors'])} productive authors")
        
        venue_trends = result["venue_trends"]
        assert "trending_venues" in venue_trends
        
        print(f"   ✅ Analyzed {len(venue_trends['trending_venues'])} venue trends")
        print("   ✅ Trend analysis tests passed!")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Trend analysis test failed: {e}")
        return False

async def test_service_integration():
    """Test intelligent organization service integration"""
    print("🧪 Testing Service Integration...")
    
    try:
        # Mock repository for testing
        class MockPaperRepository:
            async def get_by_id(self, paper_id: str):
                for paper in SAMPLE_PAPERS:
                    if paper["id"] == paper_id:
                        # Create mock paper object
                        class MockPaper:
                            def __init__(self, data):
                                for key, value in data.items():
                                    setattr(self, key, value)
                                self.__dict__ = data
                        return MockPaper(paper)
                return None
            
            async def get_all(self, limit: int = 100):
                class MockPaper:
                    def __init__(self, data):
                        for key, value in data.items():
                            setattr(self, key, value)
                        self.__dict__ = data
                
                return [MockPaper(paper) for paper in SAMPLE_PAPERS[:limit]]
        
        # Import and test service
        sys.path.append('/home/mohit/workspace/Project_research/backend')
        from services.intelligent_organization_service import IntelligentOrganizationService
        
        mock_repo = MockPaperRepository()
        service = IntelligentOrganizationService(mock_repo)
        
        # Test semantic organization
        semantic_result = await service.organize_papers(SAMPLE_PAPERS, "semantic")
        
        assert "organization_type" in semantic_result
        assert "clusters" in semantic_result
        assert "summary" in semantic_result
        assert semantic_result["organization_type"] == "semantic"
        
        print(f"   ✅ Semantic organization: {len(semantic_result['clusters'])} clusters")
        
        # Test topic organization
        topic_result = await service.organize_papers(SAMPLE_PAPERS, "topic")
        
        assert topic_result["organization_type"] == "topic"
        assert "topics" in topic_result
        
        print(f"   ✅ Topic organization: {len(topic_result['clusters'])} clusters")
        
        # Test genealogy analysis
        genealogy_result = await service.analyze_research_genealogy(SAMPLE_PAPERS)
        
        assert "network_statistics" in genealogy_result
        assert "influential_papers" in genealogy_result
        assert "research_lineages" in genealogy_result
        
        print(f"   ✅ Genealogy analysis: {len(genealogy_result['influential_papers'])} influential papers")
        
        # Test recommendations
        rec_result = await service.generate_recommendations(
            "test_user", SAMPLE_USER_INTERACTIONS, SAMPLE_PAPERS, "hybrid"
        )
        
        assert "user_profile" in rec_result
        assert "recommendations" in rec_result
        assert "recommendation_type" in rec_result
        
        print(f"   ✅ Recommendations: {len(rec_result['recommendations'])} papers")
        
        # Test trend analysis
        trend_result = await service.analyze_research_trends(SAMPLE_PAPERS, time_window=5)
        
        assert "trend_analysis" in trend_result
        assert "topic_evolution" in trend_result
        assert "research_insights" in trend_result
        
        print(f"   ✅ Trend analysis with research insights")
        print("   ✅ Service integration tests passed!")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Service integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all Phase 3 integration tests"""
    print("🚀 Starting Phase 3: Intelligent Organization Integration Tests")
    print("=" * 60)
    
    tests = [
        ("Semantic Clustering", test_semantic_clustering),
        ("Topic Modeling", test_topic_modeling),
        ("Citation Analysis", test_citation_analysis),
        ("Recommendation Engine", test_recommendation_engine),
        ("Trend Analysis", test_trend_analysis),
        ("Service Integration", lambda: asyncio.run(test_service_integration()))
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n📋 Running {test_name} Tests...")
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"   ❌ {test_name} test failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 PHASE 3 INTEGRATION TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{test_name:.<30} {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All Phase 3 integration tests PASSED!")
        print("✅ Intelligent Organization system is ready for production!")
        return True
    else:
        print("⚠️  Some tests failed. Please review and fix issues.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)