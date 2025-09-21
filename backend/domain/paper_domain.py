"""Paper domain logic and business rules."""

from typing import List, Optional, Dict, Any
from datetime import datetime
from dataclasses import dataclass

from ..repositories.paper_repository import PaperRepository
from ..events.base import event_bus
from ..core.logging import LoggerMixin

@dataclass
class PaperDomainModel:
    """Domain model for paper with business logic."""
    id: str
    title: str
    abstract: str
    authors: List[str]
    categories: List[str]
    arxiv_id: Optional[str] = None
    doi: Optional[str] = None
    published_date: Optional[datetime] = None
    citation_count: int = 0
    view_count: int = 0
    
    def is_recent(self, days: int = 30) -> bool:
        """Check if paper is recent."""
        if not self.published_date:
            return False
        return (datetime.utcnow() - self.published_date).days <= days
    
    def is_highly_cited(self, threshold: int = 100) -> bool:
        """Check if paper is highly cited."""
        return self.citation_count >= threshold
    
    def is_trending(self) -> bool:
        """Check if paper is trending based on views and citations."""
        return self.view_count > 50 and self.is_recent(7)
    
    def get_research_area(self) -> str:
        """Determine primary research area."""
        if not self.categories:
            return "general"
        
        # Map arXiv categories to research areas
        category_map = {
            "cs.AI": "artificial_intelligence",
            "cs.LG": "machine_learning", 
            "cs.CV": "computer_vision",
            "cs.CL": "natural_language_processing",
            "cs.RO": "robotics"
        }
        
        for category in self.categories:
            if category in category_map:
                return category_map[category]
        
        return "computer_science"

class PaperDomainService(LoggerMixin):
    """Domain service for paper business operations."""
    
    def __init__(self, paper_repository: PaperRepository):
        self.paper_repository = paper_repository
    
    async def create_paper_with_validation(self, paper_data: Dict[str, Any]) -> PaperDomainModel:
        """Create paper with business validation."""
        # Business rule: Check for duplicates
        if paper_data.get("arxiv_id"):
            existing = await self.paper_repository.find_by_arxiv_id(paper_data["arxiv_id"])
            if existing:
                raise ValueError("Paper with this arXiv ID already exists")
        
        if paper_data.get("doi"):
            existing = await self.paper_repository.find_by_doi(paper_data["doi"])
            if existing:
                raise ValueError("Paper with this DOI already exists")
        
        # Business rule: Validate required fields
        if not paper_data.get("title") or len(paper_data["title"]) < 10:
            raise ValueError("Title must be at least 10 characters")
        
        if not paper_data.get("abstract") or len(paper_data["abstract"]) < 50:
            raise ValueError("Abstract must be at least 50 characters")
        
        # Create paper
        paper = await self.paper_repository.create(paper_data)
        
        # Publish domain event
        await event_bus.publish(
            event_bus.create_event(
                "paper.created",
                {"paper_id": paper.id, "title": paper.title},
                "paper_domain"
            )
        )
        
        return self._to_domain_model(paper)
    
    async def analyze_paper_impact(self, paper_id: str) -> Dict[str, Any]:
        """Analyze paper impact using domain logic."""
        paper = await self.paper_repository.get_by_id(paper_id)
        if not paper:
            raise ValueError("Paper not found")
        
        domain_paper = self._to_domain_model(paper)
        
        # Calculate impact metrics using domain logic
        impact_score = self._calculate_impact_score(domain_paper)
        research_influence = self._assess_research_influence(domain_paper)
        
        return {
            "impact_score": impact_score,
            "research_influence": research_influence,
            "is_trending": domain_paper.is_trending(),
            "is_highly_cited": domain_paper.is_highly_cited(),
            "research_area": domain_paper.get_research_area()
        }
    
    async def recommend_related_papers(self, paper_id: str, limit: int = 10) -> List[PaperDomainModel]:
        """Recommend related papers using domain logic."""
        paper = await self.paper_repository.get_by_id(paper_id)
        if not paper:
            raise ValueError("Paper not found")
        
        # Find papers in same categories
        related_papers = await self.paper_repository.search_by_text(
            query="", 
            categories=paper.categories,
            limit=limit * 2  # Get more to filter
        )
        
        # Apply domain logic for filtering and ranking
        domain_papers = [self._to_domain_model(p) for p in related_papers if p.id != paper_id]
        
        # Sort by relevance using domain logic
        domain_papers.sort(key=lambda p: (
            p.citation_count * 0.4 + 
            p.view_count * 0.3 + 
            (100 if p.is_recent() else 0) * 0.3
        ), reverse=True)
        
        return domain_papers[:limit]
    
    def _calculate_impact_score(self, paper: PaperDomainModel) -> float:
        """Calculate impact score using domain logic."""
        base_score = min(paper.citation_count / 100, 1.0)  # Normalize to 0-1
        
        # Boost for recent papers
        if paper.is_recent(30):
            base_score *= 1.2
        
        # Boost for trending papers
        if paper.is_trending():
            base_score *= 1.5
        
        return min(base_score, 1.0)
    
    def _assess_research_influence(self, paper: PaperDomainModel) -> str:
        """Assess research influence level."""
        if paper.citation_count > 1000:
            return "groundbreaking"
        elif paper.citation_count > 500:
            return "highly_influential"
        elif paper.citation_count > 100:
            return "influential"
        elif paper.citation_count > 20:
            return "moderate"
        else:
            return "emerging"
    
    def _to_domain_model(self, paper) -> PaperDomainModel:
        """Convert database model to domain model."""
        return PaperDomainModel(
            id=paper.id,
            title=paper.title,
            abstract=paper.abstract,
            authors=paper.authors,
            categories=paper.categories,
            arxiv_id=paper.arxiv_id,
            doi=paper.doi,
            published_date=paper.published_date,
            citation_count=paper.citation_count,
            view_count=paper.view_count
        )