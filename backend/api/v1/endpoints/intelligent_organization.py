"""
Intelligent Organization API Endpoints
Provides REST API for automatic categorization, genealogy, and discovery
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import logging

from ....core.dependencies import get_paper_repository
from ....services.intelligent_organization_service import IntelligentOrganizationService
from ....repositories.paper_repository import PaperRepository

logger = logging.getLogger(__name__)
router = APIRouter()

# Request/Response Models
class OrganizationRequest(BaseModel):
    paper_ids: List[str]
    organization_type: str = "semantic"  # semantic, topic, hybrid

class RecommendationRequest(BaseModel):
    user_id: str
    user_interactions: List[Dict[str, Any]]
    recommendation_type: str = "hybrid"  # content, collaborative, hybrid
    top_k: int = 10

class TrendAnalysisRequest(BaseModel):
    paper_ids: Optional[List[str]] = None
    time_window: int = 5
    include_predictions: bool = True

class OrganizationResponse(BaseModel):
    organization_type: str
    clusters: Dict[str, Any]
    summary: Dict[str, Any]

class RecommendationResponse(BaseModel):
    user_profile: Dict[str, Any]
    recommendations: List[Dict[str, Any]]
    recommendation_type: str
    total_recommendations: int

class GenealogyResponse(BaseModel):
    network_statistics: Dict[str, Any]
    influential_papers: List[Dict[str, Any]]
    research_lineages: List[Dict[str, Any]]
    evolution_paths: List[Dict[str, Any]]

class TrendResponse(BaseModel):
    trend_analysis: Dict[str, Any]
    topic_evolution: Dict[str, Any]
    research_insights: Dict[str, Any]

def get_organization_service(
    paper_repository: PaperRepository = Depends(get_paper_repository)
) -> IntelligentOrganizationService:
    """Get intelligent organization service instance"""
    return IntelligentOrganizationService(paper_repository)

@router.post("/organize", response_model=OrganizationResponse)
async def organize_papers(
    request: OrganizationRequest,
    service: IntelligentOrganizationService = Depends(get_organization_service)
):
    """
    Organize papers using AI-powered categorization
    
    - **paper_ids**: List of paper IDs to organize
    - **organization_type**: Type of organization (semantic, topic, hybrid)
    """
    try:
        # Fetch papers from repository
        papers = []
        for paper_id in request.paper_ids:
            paper = await service.paper_repository.get_by_id(paper_id)
            if paper:
                papers.append(paper.__dict__)
        
        if not papers:
            raise HTTPException(status_code=404, detail="No papers found")
        
        # Organize papers
        result = await service.organize_papers(papers, request.organization_type)
        
        return OrganizationResponse(**result)
        
    except Exception as e:
        logger.error(f"Error organizing papers: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/organize/all")
async def organize_all_papers(
    organization_type: str = Query("semantic", description="Organization type"),
    limit: int = Query(100, description="Maximum number of papers to organize"),
    service: IntelligentOrganizationService = Depends(get_organization_service)
):
    """
    Organize all papers in the database
    """
    try:
        # Get all papers (with limit)
        all_papers = await service.paper_repository.get_all(limit=limit)
        papers_data = [paper.__dict__ for paper in all_papers]
        
        if not papers_data:
            raise HTTPException(status_code=404, detail="No papers found in database")
        
        # Organize papers
        result = await service.organize_papers(papers_data, organization_type)
        
        return OrganizationResponse(**result)
        
    except Exception as e:
        logger.error(f"Error organizing all papers: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/genealogy", response_model=GenealogyResponse)
async def analyze_research_genealogy(
    request: OrganizationRequest,
    service: IntelligentOrganizationService = Depends(get_organization_service)
):
    """
    Analyze research genealogy and citation networks
    
    - **paper_ids**: List of paper IDs to analyze
    """
    try:
        # Fetch papers from repository
        papers = []
        for paper_id in request.paper_ids:
            paper = await service.paper_repository.get_by_id(paper_id)
            if paper:
                papers.append(paper.__dict__)
        
        if not papers:
            raise HTTPException(status_code=404, detail="No papers found")
        
        # Analyze genealogy
        result = await service.analyze_research_genealogy(papers)
        
        return GenealogyResponse(**result)
        
    except Exception as e:
        logger.error(f"Error analyzing research genealogy: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/genealogy/all")
async def analyze_all_genealogy(
    limit: int = Query(200, description="Maximum number of papers to analyze"),
    service: IntelligentOrganizationService = Depends(get_organization_service)
):
    """
    Analyze research genealogy for all papers
    """
    try:
        # Get all papers (with limit for performance)
        all_papers = await service.paper_repository.get_all(limit=limit)
        papers_data = [paper.__dict__ for paper in all_papers]
        
        if not papers_data:
            raise HTTPException(status_code=404, detail="No papers found in database")
        
        # Analyze genealogy
        result = await service.analyze_research_genealogy(papers_data)
        
        return GenealogyResponse(**result)
        
    except Exception as e:
        logger.error(f"Error analyzing all genealogy: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/recommendations", response_model=RecommendationResponse)
async def generate_recommendations(
    request: RecommendationRequest,
    service: IntelligentOrganizationService = Depends(get_organization_service)
):
    """
    Generate personalized paper recommendations
    
    - **user_id**: User identifier
    - **user_interactions**: List of user interactions with papers
    - **recommendation_type**: Type of recommendation algorithm
    - **top_k**: Number of recommendations to return
    """
    try:
        # Get available papers for recommendations
        all_papers = await service.paper_repository.get_all(limit=1000)
        papers_data = [paper.__dict__ for paper in all_papers]
        
        if not papers_data:
            raise HTTPException(status_code=404, detail="No papers available for recommendations")
        
        # Generate recommendations
        result = await service.generate_recommendations(
            request.user_id,
            request.user_interactions,
            papers_data,
            request.recommendation_type
        )
        
        return RecommendationResponse(**result)
        
    except Exception as e:
        logger.error(f"Error generating recommendations: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/trends", response_model=TrendResponse)
async def analyze_research_trends(
    request: TrendAnalysisRequest,
    service: IntelligentOrganizationService = Depends(get_organization_service)
):
    """
    Analyze research trends and predict future directions
    
    - **paper_ids**: Optional list of specific papers to analyze
    - **time_window**: Number of years to analyze for trends
    - **include_predictions**: Whether to include future predictions
    """
    try:
        # Get papers for analysis
        if request.paper_ids:
            papers = []
            for paper_id in request.paper_ids:
                paper = await service.paper_repository.get_by_id(paper_id)
                if paper:
                    papers.append(paper.__dict__)
        else:
            # Use all papers if no specific IDs provided
            all_papers = await service.paper_repository.get_all(limit=1000)
            papers = [paper.__dict__ for paper in all_papers]
        
        if not papers:
            raise HTTPException(status_code=404, detail="No papers found for trend analysis")
        
        # Analyze trends
        result = await service.analyze_research_trends(papers, request.time_window)
        
        return TrendResponse(**result)
        
    except Exception as e:
        logger.error(f"Error analyzing research trends: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/trends/keywords")
async def get_trending_keywords(
    time_window: int = Query(3, description="Years to analyze"),
    top_k: int = Query(20, description="Number of top keywords to return"),
    service: IntelligentOrganizationService = Depends(get_organization_service)
):
    """
    Get trending keywords in research
    """
    try:
        # Get all papers
        all_papers = await service.paper_repository.get_all(limit=1000)
        papers_data = [paper.__dict__ for paper in all_papers]
        
        if not papers_data:
            raise HTTPException(status_code=404, detail="No papers found")
        
        # Analyze trends
        result = await service.analyze_research_trends(papers_data, time_window)
        
        # Extract keyword trends
        keyword_trends = result["trend_analysis"]["keyword_trends"]
        
        return {
            "trending_up": keyword_trends["trending_up"][:top_k],
            "trending_down": keyword_trends["trending_down"][:top_k//2],
            "emerging_topics": result["trend_analysis"]["emerging_topics"][:top_k//2],
            "analysis_summary": keyword_trends["analysis_summary"]
        }
        
    except Exception as e:
        logger.error(f"Error getting trending keywords: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/similar/{paper_id}")
async def find_similar_papers(
    paper_id: str,
    top_k: int = Query(10, description="Number of similar papers to return"),
    service: IntelligentOrganizationService = Depends(get_organization_service)
):
    """
    Find papers similar to a specific paper
    """
    try:
        # Get target paper
        target_paper = await service.paper_repository.get_by_id(paper_id)
        if not target_paper:
            raise HTTPException(status_code=404, detail="Paper not found")
        
        # Get all papers for comparison
        all_papers = await service.paper_repository.get_all(limit=1000)
        papers_data = [paper.__dict__ for paper in all_papers if paper.id != paper_id]
        
        # Find similar papers
        similar_papers = service.semantic_clusterer.find_similar_papers(
            target_paper.__dict__, papers_data, top_k
        )
        
        return {
            "target_paper": {
                "id": target_paper.id,
                "title": target_paper.title,
                "authors": target_paper.authors
            },
            "similar_papers": similar_papers,
            "total_found": len(similar_papers)
        }
        
    except Exception as e:
        logger.error(f"Error finding similar papers: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/clusters/preview")
async def preview_clusters(
    organization_type: str = Query("semantic", description="Organization type"),
    max_papers: int = Query(50, description="Maximum papers to cluster"),
    service: IntelligentOrganizationService = Depends(get_organization_service)
):
    """
    Preview paper clustering with a small sample
    """
    try:
        # Get sample of papers
        sample_papers = await service.paper_repository.get_all(limit=max_papers)
        papers_data = [paper.__dict__ for paper in sample_papers]
        
        if not papers_data:
            raise HTTPException(status_code=404, detail="No papers found")
        
        # Organize papers
        result = await service.organize_papers(papers_data, organization_type)
        
        # Create preview with limited information
        preview_clusters = {}
        for cluster_id, cluster_data in result["clusters"].items():
            preview_clusters[cluster_id] = {
                "paper_count": cluster_data["paper_count"],
                "topic_name": cluster_data.get("topic_info", {}).get("name", f"Cluster {cluster_id}"),
                "sample_papers": [
                    {"id": p.get("id"), "title": p.get("title", "")} 
                    for p in cluster_data["papers"][:3]
                ],
                "keywords": cluster_data.get("keywords", [])[:5]
            }
        
        return {
            "preview_clusters": preview_clusters,
            "total_clusters": len(preview_clusters),
            "total_papers": len(papers_data),
            "organization_type": organization_type
        }
        
    except Exception as e:
        logger.error(f"Error creating cluster preview: {e}")
        raise HTTPException(status_code=500, detail=str(e))