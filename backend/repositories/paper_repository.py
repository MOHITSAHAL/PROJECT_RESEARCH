"""Paper repository for data access operations."""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func
from datetime import datetime, timedelta

from .base import SQLAlchemyRepository
from ..database.models import Paper, PaperEmbedding

class PaperRepository(SQLAlchemyRepository[Paper]):
    """Repository for paper data access operations."""
    
    def __init__(self, db: Session):
        super().__init__(db, Paper)
    
    async def find_by_arxiv_id(self, arxiv_id: str) -> Optional[Paper]:
        """Find paper by arXiv ID."""
        return self.db.query(Paper).filter(Paper.arxiv_id == arxiv_id).first()
    
    async def find_by_doi(self, doi: str) -> Optional[Paper]:
        """Find paper by DOI."""
        return self.db.query(Paper).filter(Paper.doi == doi).first()
    
    async def search_by_text(self, query: str, categories: List[str] = None, 
                           limit: int = 50, offset: int = 0) -> List[Paper]:
        """Search papers by text query."""
        db_query = self.db.query(Paper).filter(
            or_(
                Paper.title.ilike(f"%{query}%"),
                Paper.abstract.ilike(f"%{query}%")
            )
        )
        
        if categories:
            db_query = db_query.filter(Paper.categories.op("&&")(categories))
        
        return db_query.offset(offset).limit(limit).all()
    
    async def find_trending(self, categories: List[str], time_period: str, limit: int) -> List[Paper]:
        """Find trending papers."""
        if time_period == "1d":
            threshold = datetime.utcnow() - timedelta(days=1)
        elif time_period == "7d":
            threshold = datetime.utcnow() - timedelta(days=7)
        else:
            threshold = datetime.utcnow() - timedelta(days=30)
        
        return self.db.query(Paper).filter(
            and_(
                Paper.categories.op("&&")(categories),
                Paper.published_date >= threshold
            )
        ).order_by(
            desc(Paper.citation_count + Paper.view_count)
        ).limit(limit).all()
    
    async def find_by_authors(self, authors: List[str]) -> List[Paper]:
        """Find papers by authors."""
        query = self.db.query(Paper)
        for author in authors:
            query = query.filter(Paper.authors.op("@>")(f'["{author}"]'))
        return query.all()
    
    async def increment_view_count(self, paper_id: str) -> bool:
        """Increment view count for a paper."""
        paper = await self.get_by_id(paper_id)
        if paper:
            paper.view_count += 1
            self.db.commit()
            return True
        return False