"""Service for managing data pipeline operations."""

import asyncio
from typing import List, Optional, Dict, Any
from datetime import datetime
import structlog

from ..repositories.paper_repository import PaperRepository
from ..domain.paper_domain import PaperDomain
from ..models.paper_models import PaperCreate, PaperResponse

# Import data pipeline components
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../data-pipeline'))

from ingestion.arxiv_client import ArxivClient, ArxivPaper
from processing.pdf_processor import PDFProcessor, ProcessedPaper
from github_integration.repo_analyzer import GitHubRepoAnalyzer, RepoAnalysis

logger = structlog.get_logger()


class DataPipelineService:
    """Service for coordinating data pipeline operations."""
    
    def __init__(
        self,
        paper_repository: PaperRepository,
        paper_domain: PaperDomain,
        github_token: Optional[str] = None
    ):
        self.paper_repository = paper_repository
        self.paper_domain = paper_domain
        
        # Initialize pipeline components
        self.arxiv_client = ArxivClient(max_results=100, delay_seconds=3.0)
        self.pdf_processor = PDFProcessor()
        self.github_analyzer = GitHubRepoAnalyzer(github_token)
    
    async def fetch_and_process_papers(self, days_back: int = 7) -> Dict[str, Any]:
        """Fetch and process papers from arXiv."""
        try:
            logger.info(f"Fetching papers from last {days_back} days")
            
            # Fetch papers from arXiv
            arxiv_papers = await self.arxiv_client.fetch_ai_papers(days_back)
            
            results = {
                'total_fetched': len(arxiv_papers),
                'processed': 0,
                'failed': 0,
                'new_papers': [],
                'errors': []
            }
            
            for arxiv_paper in arxiv_papers:
                try:
                    # Check if paper already exists
                    existing_paper = await self.paper_repository.get_by_arxiv_id(
                        arxiv_paper.arxiv_id
                    )
                    
                    if existing_paper:
                        logger.info(f"Paper {arxiv_paper.arxiv_id} already exists, skipping")
                        continue
                    
                    # Process the paper
                    processed_paper = await self._process_arxiv_paper(arxiv_paper)
                    
                    if processed_paper:
                        results['processed'] += 1
                        results['new_papers'].append(processed_paper.id)
                        logger.info(f"Successfully processed paper: {arxiv_paper.arxiv_id}")
                    
                except Exception as e:
                    results['failed'] += 1
                    results['errors'].append(f"{arxiv_paper.arxiv_id}: {str(e)}")
                    logger.error(f"Failed to process paper {arxiv_paper.arxiv_id}: {e}")
            
            logger.info(f"Paper processing completed: {results}")
            return results
            
        except Exception as e:
            logger.error(f"Paper fetching and processing failed: {e}")
            raise
    
    async def process_paper_by_id(self, arxiv_id: str) -> Optional[PaperResponse]:
        """Process a specific paper by arXiv ID."""
        try:
            logger.info(f"Processing paper by ID: {arxiv_id}")
            
            # Check if paper already exists
            existing_paper = await self.paper_repository.get_by_arxiv_id(arxiv_id)
            if existing_paper:
                logger.info(f"Paper {arxiv_id} already exists")
                return existing_paper
            
            # Fetch paper from arXiv
            arxiv_paper = await self.arxiv_client.fetch_paper_by_id(arxiv_id)
            if not arxiv_paper:
                logger.error(f"Paper {arxiv_id} not found on arXiv")
                return None
            
            # Process the paper
            processed_paper = await self._process_arxiv_paper(arxiv_paper)
            
            logger.info(f"Successfully processed paper: {arxiv_id}")
            return processed_paper
            
        except Exception as e:
            logger.error(f"Failed to process paper {arxiv_id}: {e}")
            raise
    
    async def search_arxiv_papers(
        self, 
        query: str, 
        max_results: int = 50
    ) -> List[Dict[str, Any]]:
        """Search papers on arXiv and return metadata."""
        try:
            logger.info(f"Searching arXiv for: {query}")
            
            arxiv_papers = await self.arxiv_client.search_papers(query, max_results)
            
            # Convert to dict format for API response
            results = []
            for paper in arxiv_papers:
                results.append({
                    'arxiv_id': paper.arxiv_id,
                    'title': paper.title,
                    'abstract': paper.abstract,
                    'authors': paper.authors,
                    'categories': paper.categories,
                    'published_date': paper.published_date,
                    'pdf_url': paper.pdf_url,
                    'doi': paper.doi,
                    'journal': paper.journal
                })
            
            logger.info(f"Found {len(results)} papers for query: {query}")
            return results
            
        except Exception as e:
            logger.error(f"arXiv search failed for query '{query}': {e}")
            raise
    
    async def analyze_github_repository(self, github_url: str) -> Optional[Dict[str, Any]]:
        """Analyze a GitHub repository."""
        try:
            logger.info(f"Analyzing GitHub repository: {github_url}")
            
            analysis = await self.github_analyzer.analyze_repository(github_url)
            
            if analysis:
                return {
                    'url': analysis.url,
                    'name': analysis.name,
                    'description': analysis.description,
                    'stars': analysis.stars,
                    'forks': analysis.forks,
                    'language': analysis.language,
                    'topics': analysis.topics,
                    'key_files': analysis.key_files,
                    'has_requirements': analysis.has_requirements,
                    'has_dockerfile': analysis.has_dockerfile,
                    'has_notebook': analysis.has_notebook,
                    'last_updated': analysis.last_updated,
                    'license': analysis.license,
                    'implementation_complexity': analysis.implementation_complexity,
                    'tutorial_quality': analysis.tutorial_quality
                }
            
            return None
            
        except Exception as e:
            logger.error(f"GitHub repository analysis failed for {github_url}: {e}")
            raise
    
    async def _process_arxiv_paper(self, arxiv_paper: ArxivPaper) -> Optional[PaperResponse]:
        """Process an arXiv paper through the complete pipeline."""
        
        # Step 1: Process PDF content
        processed_content = None
        if arxiv_paper.pdf_url:
            try:
                processed_content = await self.pdf_processor.download_and_process_pdf(
                    arxiv_paper.pdf_url
                )
            except Exception as e:
                logger.warning(f"PDF processing failed for {arxiv_paper.arxiv_id}: {e}")
        
        # Step 2: Analyze GitHub repositories
        github_analyses = []
        github_urls = []
        
        if processed_content and processed_content.github_urls:
            try:
                github_analyses = await self.github_analyzer.analyze_repositories(
                    processed_content.github_urls
                )
                github_urls = processed_content.github_urls
            except Exception as e:
                logger.warning(f"GitHub analysis failed for {arxiv_paper.arxiv_id}: {e}")
        
        # Step 3: Create paper data
        paper_data = PaperCreate(
            title=arxiv_paper.title,
            abstract=arxiv_paper.abstract,
            authors=arxiv_paper.authors,
            categories=arxiv_paper.categories,
            arxiv_id=arxiv_paper.arxiv_id,
            doi=arxiv_paper.doi,
            published_date=arxiv_paper.published_date,
            pdf_url=arxiv_paper.pdf_url,
            journal=arxiv_paper.journal,
            full_text=processed_content.full_text if processed_content else None,
            github_repos=github_urls,
            keywords=self._extract_keywords(arxiv_paper, processed_content)
        )
        
        # Step 4: Validate and save paper
        validated_paper = self.paper_domain.create_paper(paper_data)
        saved_paper = await self.paper_repository.create(validated_paper)
        
        # Step 5: Update paper with processed content
        if processed_content:
            update_data = {
                'summary': self._generate_summary(processed_content),
                'methodology': processed_content.methodology,
                'processing_status': 'completed'
            }
            
            await self.paper_repository.update(saved_paper.id, update_data)
        
        # Step 6: Save GitHub analyses (if any)
        if github_analyses:
            # TODO: Save GitHub analyses to database
            # This could be a separate table or JSON field
            pass
        
        return await self.paper_repository.get_by_id(saved_paper.id)
    
    def _extract_keywords(
        self, 
        arxiv_paper: ArxivPaper, 
        processed_content: Optional[ProcessedPaper]
    ) -> List[str]:
        """Extract keywords from paper content."""
        keywords = []
        
        # Add categories as keywords
        keywords.extend(arxiv_paper.categories)
        
        # Add methodology keywords if available
        if processed_content and processed_content.methodology:
            keywords.extend(processed_content.methodology)
        
        # Extract keywords from title and abstract
        title_words = arxiv_paper.title.lower().split()
        abstract_words = arxiv_paper.abstract.lower().split()
        
        # Common AI/ML keywords
        ai_keywords = [
            'neural', 'network', 'learning', 'deep', 'machine', 'artificial',
            'intelligence', 'transformer', 'attention', 'bert', 'gpt',
            'classification', 'regression', 'clustering', 'optimization',
            'reinforcement', 'supervised', 'unsupervised', 'computer', 'vision'
        ]
        
        for keyword in ai_keywords:
            if keyword in title_words or keyword in abstract_words:
                keywords.append(keyword)
        
        return list(set(keywords))  # Remove duplicates
    
    def _generate_summary(self, processed_content: ProcessedPaper) -> str:
        """Generate a summary from processed content."""
        # Simple summary generation - can be enhanced with AI
        summary_parts = []
        
        if processed_content.sections.get('abstract'):
            summary_parts.append(processed_content.sections['abstract'][:500])
        
        if processed_content.methodology:
            methods = ', '.join(processed_content.methodology[:5])
            summary_parts.append(f"Methods: {methods}")
        
        if processed_content.key_findings:
            findings = '. '.join(processed_content.key_findings[:3])
            summary_parts.append(f"Key findings: {findings}")
        
        return ' | '.join(summary_parts)[:1000]  # Limit summary length