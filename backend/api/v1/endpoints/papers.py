"""Paper management endpoints."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session

from ....database.connection import get_db_session
from ....models.paper_models import (
    PaperCreate, PaperUpdate, PaperResponse, PaperSearchRequest, 
    PaperSearchResponse, PaperAnalysisRequest, PaperAnalysisResponse
)
from ....models.common_models import PaginationParams, PaginatedResponse
from ....services.paper_service import PaperService
from ....core.logging import get_logger

router = APIRouter()
logger = get_logger(__name__)


@router.post("/", response_model=PaperResponse, status_code=201)
async def create_paper(
    paper_data: PaperCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db_session)
):
    """Create a new research paper."""
    try:
        paper_service = PaperService(db)
        paper = await paper_service.create_paper(paper_data)
        
        # Schedule background processing
        background_tasks.add_task(paper_service.process_paper_async, paper.id)
        
        logger.info("paper_created", paper_id=paper.id, title=paper.title)
        return paper
    except Exception as e:
        logger.error("paper_creation_failed", error=str(e))
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/", response_model=PaginatedResponse[PaperResponse])
async def search_papers(
    query: Optional[str] = Query(None, description="Search query"),
    categories: Optional[List[str]] = Query(None, description="Paper categories"),
    has_github: Optional[bool] = Query(None, description="Filter papers with GitHub repos"),
    has_agent: Optional[bool] = Query(None, description="Filter papers with AI agents"),
    pagination: PaginationParams = Depends(),
    db: Session = Depends(get_db_session)
):
    """Search and filter research papers."""
    try:
        paper_service = PaperService(db)
        
        search_request = PaperSearchRequest(
            query=query,
            categories=categories,
            has_github=has_github,
            has_agent=has_agent,
            limit=pagination.limit,
            offset=pagination.offset
        )
        
        result = await paper_service.search_papers(search_request)
        
        return PaginatedResponse.create(
            items=result.papers,
            total_count=result.total_count,
            pagination=pagination
        )
    except Exception as e:
        logger.error("paper_search_failed", error=str(e))
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{paper_id}", response_model=PaperResponse)
async def get_paper(
    paper_id: str,
    db: Session = Depends(get_db_session)
):
    """Get a specific paper by ID."""
    try:
        paper_service = PaperService(db)
        paper = await paper_service.get_paper(paper_id)
        
        if not paper:
            raise HTTPException(status_code=404, detail="Paper not found")
        
        return paper
    except HTTPException:
        raise
    except Exception as e:
        logger.error("paper_retrieval_failed", paper_id=paper_id, error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/{paper_id}", response_model=PaperResponse)
async def update_paper(
    paper_id: str,
    paper_update: PaperUpdate,
    db: Session = Depends(get_db_session)
):
    """Update an existing paper."""
    try:
        paper_service = PaperService(db)
        paper = await paper_service.update_paper(paper_id, paper_update)
        
        if not paper:
            raise HTTPException(status_code=404, detail="Paper not found")
        
        logger.info("paper_updated", paper_id=paper_id)
        return paper
    except HTTPException:
        raise
    except Exception as e:
        logger.error("paper_update_failed", paper_id=paper_id, error=str(e))
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{paper_id}", status_code=204)
async def delete_paper(
    paper_id: str,
    db: Session = Depends(get_db_session)
):
    """Delete a paper."""
    try:
        paper_service = PaperService(db)
        success = await paper_service.delete_paper(paper_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Paper not found")
        
        logger.info("paper_deleted", paper_id=paper_id)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("paper_deletion_failed", paper_id=paper_id, error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/{paper_id}/analyze", response_model=PaperAnalysisResponse)
async def analyze_paper(
    paper_id: str,
    analysis_request: PaperAnalysisRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db_session)
):
    """Analyze a paper using AI."""
    try:
        paper_service = PaperService(db)
        
        # Check if paper exists
        paper = await paper_service.get_paper(paper_id)
        if not paper:
            raise HTTPException(status_code=404, detail="Paper not found")
        
        # Start analysis
        analysis_result = await paper_service.analyze_paper(paper_id, analysis_request)
        
        logger.info("paper_analysis_started", paper_id=paper_id, analysis_type=analysis_request.analysis_type)
        return analysis_result
    except HTTPException:
        raise
    except Exception as e:
        logger.error("paper_analysis_failed", paper_id=paper_id, error=str(e))
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{paper_id}/github-analysis")
async def get_github_analysis(
    paper_id: str,
    db: Session = Depends(get_db_session)
):
    """Get GitHub repository analysis for a paper."""
    try:
        paper_service = PaperService(db)
        analysis = await paper_service.get_github_analysis(paper_id)
        
        if not analysis:
            raise HTTPException(status_code=404, detail="No GitHub analysis found for this paper")
        
        return analysis
    except HTTPException:
        raise
    except Exception as e:
        logger.error("github_analysis_retrieval_failed", paper_id=paper_id, error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/batch-process")
async def batch_process_papers(
    background_tasks: BackgroundTasks,
    source: str = Query("arxiv", description="Source to fetch papers from"),
    categories: List[str] = Query(["cs.AI", "cs.LG"], description="Categories to fetch"),
    max_papers: int = Query(100, description="Maximum number of papers to process")
):
    """Trigger batch processing of papers from external sources."""
    try:
        # Schedule background task for batch processing
        background_tasks.add_task(
            batch_process_papers_task,
            source=source,
            categories=categories,
            max_papers=max_papers
        )
        
        logger.info("batch_processing_scheduled", source=source, categories=categories, max_papers=max_papers)
        
        return {
            "message": "Batch processing scheduled",
            "source": source,
            "categories": categories,
            "max_papers": max_papers
        }
    except Exception as e:
        logger.error("batch_processing_failed", error=str(e))
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/trending/ai")
async def get_trending_ai_papers(
    limit: int = Query(20, ge=1, le=100),
    time_period: str = Query("7d", regex="^(1d|7d|30d)$"),
    db: Session = Depends(get_db_session)
):
    """Get trending AI papers based on various metrics."""
    try:
        paper_service = PaperService(db)
        trending_papers = await paper_service.get_trending_papers(
            categories=["cs.AI", "cs.LG", "cs.CL", "cs.CV", "cs.RO"],
            limit=limit,
            time_period=time_period
        )
        
        return {
            "papers": trending_papers,
            "time_period": time_period,
            "total_count": len(trending_papers)
        }
    except Exception as e:
        logger.error("trending_papers_failed", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


async def batch_process_papers_task(source: str, categories: List[str], max_papers: int):
    """Background task for batch processing papers."""
    # This would be implemented in the service layer
    # For now, it's a placeholder
    logger.info("batch_processing_task_started", source=source, categories=categories, max_papers=max_papers)