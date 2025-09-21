"""Scheduler for automated paper ingestion and processing."""

import asyncio
from datetime import datetime, timedelta
from typing import List, Optional
from celery import Celery
from celery.schedules import crontab
import structlog

from ..ingestion.arxiv_client import ArxivClient, ArxivPaper
from ..processing.pdf_processor import PDFProcessor
from ..github_integration.repo_analyzer import GitHubRepoAnalyzer

logger = structlog.get_logger()


class PaperIngestionScheduler:
    """Scheduler for automated paper discovery and processing."""
    
    def __init__(
        self,
        arxiv_client: ArxivClient,
        pdf_processor: PDFProcessor,
        github_analyzer: GitHubRepoAnalyzer,
        celery_app: Celery
    ):
        self.arxiv_client = arxiv_client
        self.pdf_processor = pdf_processor
        self.github_analyzer = github_analyzer
        self.celery_app = celery_app
        
        # Register periodic tasks
        self._register_periodic_tasks()
    
    def _register_periodic_tasks(self):
        """Register periodic tasks with Celery Beat."""
        
        @self.celery_app.task(name="daily_paper_ingestion")
        def daily_paper_ingestion():
            """Daily task to fetch and process new papers."""
            return asyncio.run(self.process_daily_papers())
        
        @self.celery_app.task(name="weekly_paper_backfill")
        def weekly_paper_backfill():
            """Weekly task to backfill any missed papers."""
            return asyncio.run(self.process_weekly_backfill())
        
        @self.celery_app.task(name="process_single_paper")
        def process_single_paper(arxiv_id: str):
            """Process a single paper by arXiv ID."""
            return asyncio.run(self.process_paper_by_id(arxiv_id))
        
        # Schedule periodic tasks
        self.celery_app.conf.beat_schedule = {
            'daily-paper-ingestion': {
                'task': 'daily_paper_ingestion',
                'schedule': crontab(hour=2, minute=0),  # Daily at 2 AM
            },
            'weekly-paper-backfill': {
                'task': 'weekly_paper_backfill',
                'schedule': crontab(hour=3, minute=0, day_of_week=1),  # Monday at 3 AM
            },
        }
    
    async def process_daily_papers(self) -> dict:
        """Process papers from the last 24 hours."""
        try:
            logger.info("Starting daily paper ingestion")
            
            # Fetch papers from last 24 hours
            papers = await self.arxiv_client.fetch_ai_papers(days_back=1)
            
            results = {
                'total_fetched': len(papers),
                'processed': 0,
                'failed': 0,
                'errors': []
            }
            
            for paper in papers:
                try:
                    await self._process_paper(paper)
                    results['processed'] += 1
                    logger.info(f"Processed paper: {paper.arxiv_id}")
                except Exception as e:
                    results['failed'] += 1
                    results['errors'].append(f"{paper.arxiv_id}: {str(e)}")
                    logger.error(f"Failed to process paper {paper.arxiv_id}: {e}")
            
            logger.info(f"Daily ingestion completed: {results}")
            return results
            
        except Exception as e:
            logger.error(f"Daily paper ingestion failed: {e}")
            return {'error': str(e)}
    
    async def process_weekly_backfill(self) -> dict:
        """Process papers from the last week to catch any missed ones."""
        try:
            logger.info("Starting weekly paper backfill")
            
            # Fetch papers from last 7 days
            papers = await self.arxiv_client.fetch_ai_papers(days_back=7)
            
            results = {
                'total_fetched': len(papers),
                'new_papers': 0,
                'updated_papers': 0,
                'failed': 0,
                'errors': []
            }
            
            for paper in papers:
                try:
                    # Check if paper already exists (implement in service layer)
                    is_new = await self._is_new_paper(paper.arxiv_id)
                    
                    await self._process_paper(paper)
                    
                    if is_new:
                        results['new_papers'] += 1
                    else:
                        results['updated_papers'] += 1
                        
                    logger.info(f"Backfilled paper: {paper.arxiv_id}")
                except Exception as e:
                    results['failed'] += 1
                    results['errors'].append(f"{paper.arxiv_id}: {str(e)}")
                    logger.error(f"Failed to backfill paper {paper.arxiv_id}: {e}")
            
            logger.info(f"Weekly backfill completed: {results}")
            return results
            
        except Exception as e:
            logger.error(f"Weekly paper backfill failed: {e}")
            return {'error': str(e)}
    
    async def process_paper_by_id(self, arxiv_id: str) -> dict:
        """Process a specific paper by arXiv ID."""
        try:
            logger.info(f"Processing paper by ID: {arxiv_id}")
            
            paper = await self.arxiv_client.fetch_paper_by_id(arxiv_id)
            if not paper:
                return {'error': f'Paper {arxiv_id} not found'}
            
            await self._process_paper(paper)
            
            logger.info(f"Successfully processed paper: {arxiv_id}")
            return {'success': True, 'arxiv_id': arxiv_id}
            
        except Exception as e:
            logger.error(f"Failed to process paper {arxiv_id}: {e}")
            return {'error': str(e)}
    
    async def _process_paper(self, paper: ArxivPaper) -> None:
        """Process a single paper through the complete pipeline."""
        
        # Step 1: Process PDF content
        processed_content = None
        if paper.pdf_url:
            processed_content = await self.pdf_processor.download_and_process_pdf(
                paper.pdf_url
            )
        
        # Step 2: Analyze GitHub repositories
        github_analyses = []
        if processed_content and processed_content.github_urls:
            github_analyses = await self.github_analyzer.analyze_repositories(
                processed_content.github_urls
            )
        
        # Step 3: Save to database (implement in service layer)
        await self._save_paper_to_database(paper, processed_content, github_analyses)
        
        # Step 4: Generate embeddings (implement in AI service)
        await self._generate_paper_embeddings(paper.arxiv_id)
        
        # Step 5: Update citation network (implement in graph service)
        await self._update_citation_network(paper.arxiv_id)
    
    async def _is_new_paper(self, arxiv_id: str) -> bool:
        """Check if paper is new (not in database)."""
        # TODO: Implement database check
        # This should query the paper repository to check if paper exists
        return True
    
    async def _save_paper_to_database(
        self, 
        paper: ArxivPaper, 
        processed_content: Optional[any], 
        github_analyses: List[any]
    ) -> None:
        """Save paper and processed content to database."""
        # TODO: Implement database saving
        # This should use the paper service to save:
        # - Basic paper metadata
        # - Processed content (full text, sections, etc.)
        # - GitHub repository analyses
        # - Processing status
        pass
    
    async def _generate_paper_embeddings(self, arxiv_id: str) -> None:
        """Generate embeddings for paper content."""
        # TODO: Implement embedding generation
        # This should:
        # - Generate embeddings for title, abstract, full text
        # - Store embeddings in vector database
        # - Update paper status
        pass
    
    async def _update_citation_network(self, arxiv_id: str) -> None:
        """Update citation network in graph database."""
        # TODO: Implement citation network update
        # This should:
        # - Extract citations from paper
        # - Create/update nodes and relationships in Neo4j
        # - Calculate influence scores
        pass


# Celery task definitions for direct use
def create_celery_tasks(
    arxiv_client: ArxivClient,
    pdf_processor: PDFProcessor,
    github_analyzer: GitHubRepoAnalyzer,
    celery_app: Celery
):
    """Create Celery tasks for paper processing."""
    
    scheduler = PaperIngestionScheduler(
        arxiv_client, pdf_processor, github_analyzer, celery_app
    )
    
    return scheduler