"""arXiv API client for fetching research papers."""

import asyncio
import arxiv
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
import structlog

logger = structlog.get_logger()


@dataclass
class ArxivPaper:
    """Data class for arXiv paper information."""
    arxiv_id: str
    title: str
    abstract: str
    authors: List[str]
    categories: List[str]
    published_date: datetime
    updated_date: datetime
    pdf_url: str
    doi: Optional[str] = None
    journal: Optional[str] = None


class ArxivClient:
    """Client for fetching papers from arXiv API."""
    
    def __init__(self, max_results: int = 100, delay_seconds: float = 3.0):
        self.max_results = max_results
        self.delay_seconds = delay_seconds
        self.client = arxiv.Client(
            page_size=min(max_results, 100),
            delay_seconds=delay_seconds,
            num_retries=3
        )
    
    async def fetch_ai_papers(self, days_back: int = 7) -> List[ArxivPaper]:
        """Fetch recent AI papers from arXiv."""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        # AI-related categories
        ai_categories = [
            "cs.AI",  # Artificial Intelligence
            "cs.LG",  # Machine Learning
            "cs.CL",  # Computation and Language (NLP)
            "cs.CV",  # Computer Vision
            "cs.NE",  # Neural and Evolutionary Computing
            "cs.RO",  # Robotics
            "stat.ML"  # Machine Learning (Statistics)
        ]
        
        papers = []
        for category in ai_categories:
            try:
                category_papers = await self._fetch_by_category(
                    category, start_date, end_date
                )
                papers.extend(category_papers)
                logger.info(f"Fetched {len(category_papers)} papers from {category}")
            except Exception as e:
                logger.error(f"Error fetching from {category}: {e}")
        
        # Remove duplicates by arxiv_id
        unique_papers = {paper.arxiv_id: paper for paper in papers}
        return list(unique_papers.values())
    
    async def _fetch_by_category(
        self, 
        category: str, 
        start_date: datetime, 
        end_date: datetime
    ) -> List[ArxivPaper]:
        """Fetch papers by category and date range."""
        query = f"cat:{category} AND submittedDate:[{start_date.strftime('%Y%m%d')} TO {end_date.strftime('%Y%m%d')}]"
        
        search = arxiv.Search(
            query=query,
            max_results=self.max_results,
            sort_by=arxiv.SortCriterion.SubmittedDate,
            sort_order=arxiv.SortOrder.Descending
        )
        
        papers = []
        for result in self.client.results(search):
            try:
                paper = ArxivPaper(
                    arxiv_id=result.entry_id.split('/')[-1],
                    title=result.title.strip(),
                    abstract=result.summary.strip(),
                    authors=[author.name for author in result.authors],
                    categories=result.categories,
                    published_date=result.published,
                    updated_date=result.updated,
                    pdf_url=result.pdf_url,
                    doi=result.doi,
                    journal=result.journal_ref
                )
                papers.append(paper)
            except Exception as e:
                logger.error(f"Error processing paper {result.entry_id}: {e}")
        
        return papers
    
    async def fetch_paper_by_id(self, arxiv_id: str) -> Optional[ArxivPaper]:
        """Fetch a specific paper by arXiv ID."""
        try:
            search = arxiv.Search(id_list=[arxiv_id])
            result = next(self.client.results(search))
            
            return ArxivPaper(
                arxiv_id=result.entry_id.split('/')[-1],
                title=result.title.strip(),
                abstract=result.summary.strip(),
                authors=[author.name for author in result.authors],
                categories=result.categories,
                published_date=result.published,
                updated_date=result.updated,
                pdf_url=result.pdf_url,
                doi=result.doi,
                journal=result.journal_ref
            )
        except Exception as e:
            logger.error(f"Error fetching paper {arxiv_id}: {e}")
            return None
    
    async def search_papers(
        self, 
        query: str, 
        max_results: int = 50
    ) -> List[ArxivPaper]:
        """Search papers by query string."""
        search = arxiv.Search(
            query=query,
            max_results=max_results,
            sort_by=arxiv.SortCriterion.Relevance
        )
        
        papers = []
        for result in self.client.results(search):
            try:
                paper = ArxivPaper(
                    arxiv_id=result.entry_id.split('/')[-1],
                    title=result.title.strip(),
                    abstract=result.summary.strip(),
                    authors=[author.name for author in result.authors],
                    categories=result.categories,
                    published_date=result.published,
                    updated_date=result.updated,
                    pdf_url=result.pdf_url,
                    doi=result.doi,
                    journal=result.journal_ref
                )
                papers.append(paper)
            except Exception as e:
                logger.error(f"Error processing search result: {e}")
        
        return papers