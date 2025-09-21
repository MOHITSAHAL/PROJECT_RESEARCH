"""API endpoints for data pipeline operations."""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import structlog

from ....core.dependencies import get_data_pipeline_service
from ....services.data_pipeline_service import DataPipelineService
from ....models.paper_models import PaperResponse

logger = structlog.get_logger()

router = APIRouter(prefix="/data-pipeline", tags=["data-pipeline"])


class PaperIngestionRequest(BaseModel):
    """Request model for paper ingestion."""
    days_back: int = 7
    max_papers: Optional[int] = None


class ArxivSearchRequest(BaseModel):
    """Request model for arXiv search."""
    query: str
    max_results: int = 50


class GitHubAnalysisRequest(BaseModel):
    """Request model for GitHub repository analysis."""
    github_url: str


class IngestionResponse(BaseModel):
    """Response model for ingestion operations."""
    total_fetched: int
    processed: int
    failed: int
    new_papers: List[str]
    errors: List[str]


@router.post("/ingest-papers", response_model=IngestionResponse)
async def ingest_papers(
    request: PaperIngestionRequest,
    background_tasks: BackgroundTasks,
    pipeline_service: DataPipelineService = Depends(get_data_pipeline_service)
):
    """
    Fetch and process papers from arXiv.
    
    This endpoint triggers the paper ingestion pipeline that:
    1. Fetches recent AI papers from arXiv
    2. Processes PDF content
    3. Analyzes GitHub repositories
    4. Saves to database
    """
    try:
        logger.info(f"Starting paper ingestion for last {request.days_back} days")
        
        # Run ingestion in background for large requests
        if request.days_back > 3:
            background_tasks.add_task(
                pipeline_service.fetch_and_process_papers,
                request.days_back
            )
            return IngestionResponse(
                total_fetched=0,
                processed=0,
                failed=0,
                new_papers=[],
                errors=["Ingestion started in background. Check logs for progress."]
            )
        
        # Run synchronously for small requests
        result = await pipeline_service.fetch_and_process_papers(request.days_back)
        
        return IngestionResponse(
            total_fetched=result['total_fetched'],
            processed=result['processed'],
            failed=result['failed'],
            new_papers=result['new_papers'],
            errors=result['errors']
        )
        
    except Exception as e:
        logger.error(f"Paper ingestion failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/process-paper/{arxiv_id}", response_model=PaperResponse)
async def process_paper_by_id(
    arxiv_id: str,
    pipeline_service: DataPipelineService = Depends(get_data_pipeline_service)
):
    """
    Process a specific paper by arXiv ID.
    
    This endpoint:
    1. Fetches the paper from arXiv
    2. Processes PDF content
    3. Analyzes GitHub repositories
    4. Saves to database
    5. Returns the processed paper
    """
    try:
        logger.info(f"Processing paper: {arxiv_id}")
        
        paper = await pipeline_service.process_paper_by_id(arxiv_id)
        
        if not paper:
            raise HTTPException(
                status_code=404, 
                detail=f"Paper {arxiv_id} not found on arXiv"
            )
        
        return paper
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Paper processing failed for {arxiv_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/search-arxiv")
async def search_arxiv_papers(
    request: ArxivSearchRequest,
    pipeline_service: DataPipelineService = Depends(get_data_pipeline_service)
) -> List[Dict[str, Any]]:
    """
    Search papers on arXiv without processing them.
    
    This endpoint allows users to search arXiv and preview papers
    before deciding to process them.
    """
    try:
        logger.info(f"Searching arXiv for: {request.query}")
        
        papers = await pipeline_service.search_arxiv_papers(
            request.query, 
            request.max_results
        )
        
        return papers
        
    except Exception as e:
        logger.error(f"arXiv search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze-github")
async def analyze_github_repository(
    request: GitHubAnalysisRequest,
    pipeline_service: DataPipelineService = Depends(get_data_pipeline_service)
) -> Dict[str, Any]:
    """
    Analyze a GitHub repository for implementation quality and tutorial availability.
    
    This endpoint provides detailed analysis of GitHub repositories
    linked to research papers.
    """
    try:
        logger.info(f"Analyzing GitHub repository: {request.github_url}")
        
        analysis = await pipeline_service.analyze_github_repository(request.github_url)
        
        if not analysis:
            raise HTTPException(
                status_code=404,
                detail="Repository not found or analysis failed"
            )
        
        return analysis
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"GitHub analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def get_pipeline_status():
    """
    Get the current status of the data pipeline.
    
    Returns information about recent ingestion runs,
    processing statistics, and system health.
    """
    try:
        # TODO: Implement pipeline status tracking
        # This could include:
        # - Last ingestion run time and results
        # - Processing queue status
        # - Error rates and recent failures
        # - System resource usage
        
        return {
            "status": "operational",
            "last_ingestion": None,
            "papers_processed_today": 0,
            "processing_queue_size": 0,
            "error_rate": 0.0,
            "message": "Pipeline status tracking not yet implemented"
        }
        
    except Exception as e:
        logger.error(f"Failed to get pipeline status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/categories")
async def get_arxiv_categories() -> Dict[str, List[str]]:
    """
    Get available arXiv categories for AI research.
    
    Returns the categories that the pipeline monitors
    for automatic paper ingestion.
    """
    return {
        "ai_categories": [
            "cs.AI",   # Artificial Intelligence
            "cs.LG",   # Machine Learning
            "cs.CL",   # Computation and Language (NLP)
            "cs.CV",   # Computer Vision
            "cs.NE",   # Neural and Evolutionary Computing
            "cs.RO",   # Robotics
            "stat.ML"  # Machine Learning (Statistics)
        ],
        "descriptions": {
            "cs.AI": "Artificial Intelligence",
            "cs.LG": "Machine Learning",
            "cs.CL": "Computation and Language (NLP)",
            "cs.CV": "Computer Vision and Pattern Recognition",
            "cs.NE": "Neural and Evolutionary Computing",
            "cs.RO": "Robotics",
            "stat.ML": "Machine Learning (Statistics)"
        }
    }