"""
Intelligent Organization Service
Orchestrates automatic categorization, research genealogy, and discovery
"""

from typing import List, Dict, Any, Optional
import logging
from ..repositories.paper_repository import PaperRepository
from ..core.config import get_settings

# Import Phase 3 components
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../ai-service'))

from clustering.semantic_clusterer import SemanticClusterer
from clustering.topic_modeler import TopicModeler
from genealogy.citation_analyzer import CitationAnalyzer
from discovery.recommendation_engine import RecommendationEngine
from discovery.trend_analyzer import TrendAnalyzer

logger = logging.getLogger(__name__)
settings = get_settings()

class IntelligentOrganizationService:
    """Service for intelligent paper organization and discovery"""
    
    def __init__(self, paper_repository: PaperRepository):
        self.paper_repository = paper_repository
        self.semantic_clusterer = SemanticClusterer()
        self.topic_modeler = TopicModeler()
        self.citation_analyzer = CitationAnalyzer()
        self.recommendation_engine = RecommendationEngine()
        self.trend_analyzer = TrendAnalyzer()
        
    async def organize_papers(self, papers: List[Dict[str, Any]], 
                            organization_type: str = "semantic") -> Dict[str, Any]:
        """Organize papers using AI-powered categorization"""
        try:
            if organization_type == "semantic":
                return await self._semantic_organization(papers)
            elif organization_type == "topic":
                return await self._topic_organization(papers)
            elif organization_type == "hybrid":
                return await self._hybrid_organization(papers)
            else:
                raise ValueError(f"Unknown organization type: {organization_type}")
                
        except Exception as e:
            logger.error(f"Error organizing papers: {e}")
            raise
    
    async def _semantic_organization(self, papers: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Organize papers using semantic clustering"""
        try:
            # Perform semantic clustering
            clustering_result = self.semantic_clusterer.cluster_papers(
                papers, method="kmeans"
            )
            
            # Enhance clusters with additional metadata
            enhanced_clusters = {}
            for cluster_id, cluster_papers in clustering_result["clusters"].items():
                enhanced_clusters[cluster_id] = {
                    "papers": cluster_papers,
                    "topic_info": clustering_result["topics"].get(cluster_id, {}),
                    "paper_count": len(cluster_papers),
                    "representative_paper": self._find_representative_paper(cluster_papers),
                    "keywords": self._extract_cluster_keywords(cluster_papers)
                }
            
            return {
                "organization_type": "semantic",
                "clusters": enhanced_clusters,
                "summary": {
                    "total_clusters": len(enhanced_clusters),
                    "total_papers": len(papers),
                    "clustering_method": clustering_result["method"]
                }
            }
            
        except Exception as e:
            logger.error(f"Error in semantic organization: {e}")
            raise
    
    async def _topic_organization(self, papers: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Organize papers using topic modeling"""
        try:
            # Fit topic model
            topic_result = self.topic_modeler.fit_topics(papers)
            
            # Organize papers by dominant topics
            topic_clusters = {}
            for paper_topic in topic_result["paper_topics"]:
                topic_id = paper_topic["dominant_topic"]
                
                if topic_id not in topic_clusters:
                    topic_clusters[topic_id] = {
                        "papers": [],
                        "topic_info": None,
                        "confidence_scores": []
                    }
                
                # Find the original paper
                paper = next((p for p in papers if p.get('id') == paper_topic["paper_id"]), None)
                if paper:
                    topic_clusters[topic_id]["papers"].append(paper)
                    topic_clusters[topic_id]["confidence_scores"].append(paper_topic["confidence"])
            
            # Add topic information
            for topic in topic_result["topics"]:
                topic_id = topic["id"]
                if topic_id in topic_clusters:
                    topic_clusters[topic_id]["topic_info"] = topic
            
            return {
                "organization_type": "topic",
                "clusters": topic_clusters,
                "topics": topic_result["topics"],
                "summary": {
                    "total_topics": len(topic_result["topics"]),
                    "total_papers": len(papers),
                    "model_perplexity": topic_result.get("perplexity")
                }
            }
            
        except Exception as e:
            logger.error(f"Error in topic organization: {e}")
            raise
    
    async def _hybrid_organization(self, papers: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Combine semantic and topic-based organization"""
        try:
            # Get both organizations
            semantic_org = await self._semantic_organization(papers)
            topic_org = await self._topic_organization(papers)
            
            # Create hybrid organization
            hybrid_clusters = {}
            
            # Start with semantic clusters as base
            for cluster_id, cluster_data in semantic_org["clusters"].items():
                cluster_papers = cluster_data["papers"]
                
                # Find dominant topics for papers in this cluster
                topic_distribution = {}
                for paper in cluster_papers:
                    paper_id = paper.get('id')
                    # Find topic assignment for this paper
                    for paper_topic in topic_org.get("paper_topics", []):
                        if paper_topic["paper_id"] == paper_id:
                            topic_id = paper_topic["dominant_topic"]
                            topic_distribution[topic_id] = topic_distribution.get(topic_id, 0) + 1
                            break
                
                # Find dominant topic for cluster
                dominant_topic = max(topic_distribution.items(), key=lambda x: x[1])[0] if topic_distribution else None
                
                hybrid_clusters[f"hybrid_{cluster_id}"] = {
                    "papers": cluster_papers,
                    "semantic_info": cluster_data["topic_info"],
                    "dominant_topic": dominant_topic,
                    "topic_distribution": topic_distribution,
                    "paper_count": len(cluster_papers)
                }
            
            return {
                "organization_type": "hybrid",
                "clusters": hybrid_clusters,
                "semantic_summary": semantic_org["summary"],
                "topic_summary": topic_org["summary"]
            }
            
        except Exception as e:
            logger.error(f"Error in hybrid organization: {e}")
            raise
    
    async def analyze_research_genealogy(self, papers: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze research genealogy and citation networks"""
        try:
            # Build citation network
            network_analysis = self.citation_analyzer.build_citation_network(papers)
            
            # Find research evolution paths
            evolution_paths = []
            influential_papers = network_analysis.get("influential_papers", [])
            
            # Trace evolution from top influential papers
            for paper in influential_papers[:5]:
                paper_id = paper["paper_id"]
                impact_analysis = self.citation_analyzer.analyze_paper_impact(paper_id)
                evolution_paths.append({
                    "source_paper": paper,
                    "impact_analysis": impact_analysis,
                    "research_lineage": network_analysis.get("research_lineages", [])
                })
            
            return {
                "network_statistics": network_analysis["network_stats"],
                "influential_papers": influential_papers,
                "research_lineages": network_analysis["research_lineages"],
                "evolution_paths": evolution_paths,
                "citation_metrics": network_analysis["metrics"]
            }
            
        except Exception as e:
            logger.error(f"Error analyzing research genealogy: {e}")
            raise
    
    async def generate_recommendations(self, user_id: str, 
                                    user_interactions: List[Dict[str, Any]],
                                    available_papers: List[Dict[str, Any]],
                                    recommendation_type: str = "hybrid") -> Dict[str, Any]:
        """Generate personalized paper recommendations"""
        try:
            # Build user profile
            user_profile = self.recommendation_engine.build_user_profile(user_id, user_interactions)
            
            # Generate recommendations
            recommendations = self.recommendation_engine.recommend_papers(
                user_id, available_papers, top_k=20, method=recommendation_type
            )
            
            # Find similar papers for each recommendation
            enhanced_recommendations = []
            for rec in recommendations:
                similar_papers = self.semantic_clusterer.find_similar_papers(
                    rec, available_papers, top_k=3
                )
                
                enhanced_recommendations.append({
                    **rec,
                    "similar_papers": similar_papers
                })
            
            return {
                "user_profile": user_profile,
                "recommendations": enhanced_recommendations,
                "recommendation_type": recommendation_type,
                "total_recommendations": len(recommendations)
            }
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            raise
    
    async def analyze_research_trends(self, papers: List[Dict[str, Any]], 
                                   time_window: int = 5) -> Dict[str, Any]:
        """Analyze research trends and predict future directions"""
        try:
            # Perform trend analysis
            trend_analysis = self.trend_analyzer.analyze_research_trends(papers, time_window)
            
            # Enhance with topic evolution
            papers_by_year = {}
            for paper in papers:
                year = paper.get('published_year')
                if year:
                    if year not in papers_by_year:
                        papers_by_year[year] = []
                    papers_by_year[year].append(paper)
            
            topic_evolution = self.topic_modeler.get_topic_evolution(papers_by_year)
            
            return {
                "trend_analysis": trend_analysis,
                "topic_evolution": topic_evolution,
                "research_insights": self._generate_research_insights(trend_analysis, topic_evolution)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing research trends: {e}")
            raise
    
    def _find_representative_paper(self, papers: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Find the most representative paper in a cluster"""
        if not papers:
            return None
        
        # Simple heuristic: paper with most citations or most recent
        best_paper = papers[0]
        best_score = 0
        
        for paper in papers:
            score = 0
            
            # Citation count (if available)
            citations = paper.get('citation_count', 0)
            score += citations * 0.7
            
            # Recency bonus
            year = paper.get('published_year', 2020)
            if year >= 2023:
                score += 10
            elif year >= 2022:
                score += 5
            
            if score > best_score:
                best_score = score
                best_paper = paper
        
        return best_paper
    
    def _extract_cluster_keywords(self, papers: List[Dict[str, Any]]) -> List[str]:
        """Extract representative keywords from cluster papers"""
        keyword_counts = {}
        
        for paper in papers:
            keywords = paper.get('keywords', [])
            if isinstance(keywords, str):
                keywords = [keywords]
            
            for keyword in keywords:
                if isinstance(keyword, str) and len(keyword) > 2:
                    keyword_counts[keyword.lower()] = keyword_counts.get(keyword.lower(), 0) + 1
        
        # Sort by frequency and return top keywords
        sorted_keywords = sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True)
        return [keyword for keyword, count in sorted_keywords[:10]]
    
    def _generate_research_insights(self, trend_analysis: Dict[str, Any], 
                                  topic_evolution: Dict[str, Any]) -> Dict[str, Any]:
        """Generate research insights from trend and topic analysis"""
        insights = {
            "key_findings": [],
            "emerging_opportunities": [],
            "research_recommendations": []
        }
        
        # Analyze trending keywords
        trending_keywords = trend_analysis.get("keyword_trends", {}).get("trending_up", [])
        if trending_keywords:
            top_trend = trending_keywords[0]
            insights["key_findings"].append(
                f"'{top_trend['keyword']}' is the fastest growing research area with {top_trend['growth_rate']:.1%} growth rate"
            )
        
        # Analyze emerging topics
        emerging_topics = trend_analysis.get("emerging_topics", [])
        if emerging_topics:
            top_emerging = emerging_topics[0]
            insights["emerging_opportunities"].append(
                f"'{top_emerging['topic']}' shows {top_emerging['emergence_ratio']:.1f}x increase in recent research"
            )
        
        # Generate recommendations
        predictions = trend_analysis.get("predictions", {})
        hot_topics = predictions.get("hot_topics", [])
        if hot_topics:
            insights["research_recommendations"].append(
                f"Consider research in '{hot_topics[0]['topic']}' - predicted to grow significantly"
            )
        
        return insights