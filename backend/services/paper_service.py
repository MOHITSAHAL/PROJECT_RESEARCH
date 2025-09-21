"""Paper service for business logic operations."""

import asyncio
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session

from ..repositories.paper_repository import PaperRepository
from ..domain.paper_domain import PaperDomainService
from ..events.base import event_bus
from ..models.paper_models import (
    PaperCreate, PaperUpdate, PaperResponse, PaperSearchRequest, 
    PaperSearchResponse, PaperAnalysisRequest, PaperAnalysisResponse
)
from ..core.logging import LoggerMixin
from ..core.config import settings


class PaperService(LoggerMixin):
    """Service for paper management operations."""
    
    def __init__(self, db: Session):
        self.db = db
        self.paper_repository = PaperRepository(db)
        self.domain_service = PaperDomainService(self.paper_repository)
    
    async def create_paper(self, paper_data: PaperCreate) -> PaperResponse:
        """Create a new paper using domain service."""
        try:
            # Use domain service for business logic
            domain_paper = await self.domain_service.create_paper_with_validation(
                paper_data.dict()
            )
            
            # Get full paper from repository
            paper = await self.paper_repository.get_by_id(domain_paper.id)
            return self._to_response(paper)
            
        except Exception as e:
            self.log_error(e, operation="create_paper")
            raise
    
    async def get_paper(self, paper_id: str) -> Optional[PaperResponse]:
        """Get paper by ID."""
        paper = await self.paper_repository.get_by_id(paper_id)
        if not paper:
            return None
        
        # Increment view count and publish event
        await self.paper_repository.increment_view_count(paper_id)
        await event_bus.publish(
            event_bus.create_event(
                "paper.viewed",
                {"paper_id": paper_id},
                "paper_service"
            )
        )
        
        return self._to_response(paper)
    
    async def update_paper(self, paper_id: str, paper_update: PaperUpdate) -> Optional[PaperResponse]:
        """Update existing paper."""
        paper = self.db.query(Paper).filter(Paper.id == paper_id).first()
        if not paper:
            return None
        
        # Update fields
        update_data = paper_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(paper, field, value)
        
        self.db.commit()
        self.db.refresh(paper)
        
        return self._to_response(paper)
    
    async def delete_paper(self, paper_id: str) -> bool:
        """Delete paper."""
        paper = self.db.query(Paper).filter(Paper.id == paper_id).first()
        if not paper:
            return False
        
        self.db.delete(paper)
        self.db.commit()
        return True
    
    async def search_papers(self, search_request: PaperSearchRequest) -> PaperSearchResponse:
        """Search papers using repository."""
        # Use repository for search
        papers = await self.paper_repository.search_by_text(
            query=search_request.query or "",
            categories=search_request.categories,
            limit=search_request.limit,
            offset=search_request.offset
        )
        
        # For now, return simplified response (can be enhanced with more filters)
        return PaperSearchResponse(
            papers=[self._to_response(paper) for paper in papers],
            total_count=len(papers),
            page_info={
                "limit": search_request.limit,
                "offset": search_request.offset,
                "total": len(papers)
            }
        )
    
    async def analyze_paper(self, paper_id: str, analysis_request: PaperAnalysisRequest) -> PaperAnalysisResponse:
        """Analyze paper using AI."""
        paper = self.db.query(Paper).filter(Paper.id == paper_id).first()
        if not paper:
            raise ValueError("Paper not found")
        
        start_time = datetime.utcnow()
        analysis_results = {}
        
        # Simulate AI analysis (replace with actual AI service calls)
        if "methodology" in analysis_request.analysis_type:
            analysis_results["methodology"] = await self._analyze_methodology(paper)
        
        if "implementation" in analysis_request.analysis_type:
            analysis_results["implementation"] = await self._analyze_implementation(paper)
        
        if "impact" in analysis_request.analysis_type:
            analysis_results["impact"] = await self._analyze_impact(paper)
        
        # GitHub analysis
        github_analysis = None
        if analysis_request.include_github_analysis and paper.github_repos:
            github_analysis = await self._analyze_github_repos(paper.github_repos)
        
        processing_time = (datetime.utcnow() - start_time).total_seconds()
        
        return PaperAnalysisResponse(
            paper_id=paper_id,
            analysis_results=analysis_results,
            github_analysis=github_analysis,
            tutorial_generated=analysis_request.generate_tutorial,
            processing_time=processing_time
        )
    
    async def get_trending_papers(self, categories: List[str], limit: int, time_period: str) -> List[PaperResponse]:
        """Get trending papers using repository."""
        papers = await self.paper_repository.find_trending(categories, time_period, limit)
        return [self._to_response(paper) for paper in papers]
    
    async def process_paper_async(self, paper_id: str):
        """Background task to process paper."""
        try:
            paper = self.db.query(Paper).filter(Paper.id == paper_id).first()
            if not paper:
                return
            
            paper.processing_status = "processing"
            self.db.commit()
            
            # Simulate processing
            await asyncio.sleep(2)
            
            # Update paper with AI analysis
            if not paper.summary and paper.abstract:
                paper.summary = await self._generate_summary(paper.abstract)
            
            if not paper.methodology:
                paper.methodology = await self._extract_methodology(paper)
            
            paper.processing_status = "completed"
            self.db.commit()
            
            self.log_event("paper_processed", paper_id=paper_id)
            
        except Exception as e:
            paper.processing_status = "failed"
            self.db.commit()
            self.log_error(e, operation="process_paper", paper_id=paper_id)
    
    def _to_response(self, paper: Paper) -> PaperResponse:
        """Convert Paper model to response."""
        return PaperResponse(
            id=paper.id,
            title=paper.title,
            abstract=paper.abstract,
            authors=paper.authors,
            categories=paper.categories,
            arxiv_id=paper.arxiv_id,
            doi=paper.doi,
            published_date=paper.published_date,
            updated_date=paper.updated_date,
            journal=paper.journal,
            pdf_url=paper.pdf_url,
            citation_count=paper.citation_count,
            view_count=paper.view_count,
            download_count=paper.download_count,
            summary=paper.summary,
            keywords=paper.keywords,
            methodology=paper.methodology,
            github_repos=paper.github_repos,
            has_code=paper.has_code,
            processing_status=paper.processing_status,
            embedding_status=paper.embedding_status,
            agent_available=len(paper.agents) > 0,
            implementation_guide_available=paper.has_code,
            created_at=paper.created_at,
            updated_at=paper.updated_at
        )
    
    async def _analyze_methodology(self, paper: Paper) -> Dict[str, Any]:
        """Analyze paper methodology."""
        # Placeholder for AI analysis
        return {
            "approach": "deep_learning",
            "techniques": ["transformer", "attention_mechanism"],
            "datasets": ["custom"],
            "metrics": ["accuracy", "f1_score"]
        }
    
    async def _analyze_implementation(self, paper: Paper) -> Dict[str, Any]:
        """Analyze implementation details."""
        return {
            "complexity": "intermediate",
            "frameworks": ["pytorch", "tensorflow"],
            "requirements": ["python>=3.8", "torch>=1.9"],
            "estimated_time": 120  # minutes
        }
    
    async def _analyze_impact(self, paper: Paper) -> Dict[str, Any]:
        """Analyze paper impact."""
        return {
            "citation_velocity": paper.citation_count / max((datetime.utcnow() - paper.published_date).days, 1),
            "influence_score": min(paper.citation_count / 100, 1.0),
            "novelty_score": 0.8
        }
    
    async def _analyze_github_repos(self, repos: List[str]) -> Dict[str, Any]:
        """Analyze GitHub repositories."""
        # Placeholder for GitHub API integration
        return {
            "repositories": [
                {
                    "url": repo,
                    "stars": 1000,
                    "language": "Python",
                    "quality_score": 0.85
                } for repo in repos
            ]
        }
    
    async def _generate_summary(self, abstract: str) -> str:
        """Generate AI summary."""
        # Placeholder for AI summarization
        return f"AI-generated summary of: {abstract[:100]}..."
    
    async def _extract_methodology(self, paper: Paper) -> List[str]:
        """Extract methodology from paper."""
        # Placeholder for methodology extraction
        methodologies = []
        if "transformer" in paper.title.lower() or "attention" in paper.title.lower():
            methodologies.append("transformer_architecture")
        if "deep" in paper.title.lower():
            methodologies.append("deep_learning")
        return methodologies or ["machine_learning"]