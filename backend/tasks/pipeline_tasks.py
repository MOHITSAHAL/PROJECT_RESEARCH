"""Celery tasks for data pipeline operations."""

import asyncio
from typing import Dict, Any
from celery import current_task
import structlog

from ..core.celery_app import celery_app
from ..core.dependencies import get_data_pipeline_service

logger = structlog.get_logger()


@celery_app.task(bind=True, name="backend.tasks.pipeline_tasks.daily_paper_ingestion")
def daily_paper_ingestion(self) -> Dict[str, Any]:
    """Daily task to fetch and process new papers from arXiv."""
    try:
        logger.info("Starting daily paper ingestion task")
        
        # Update task state
        self.update_state(state="PROGRESS", meta={"status": "Initializing pipeline"})
        
        # Get pipeline service
        pipeline_service = get_data_pipeline_service()
        
        # Run async function in sync context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(
                pipeline_service.fetch_and_process_papers(days_back=1)
            )
        finally:
            loop.close()
        
        logger.info(f"Daily paper ingestion completed: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Daily paper ingestion failed: {e}")
        self.update_state(
            state="FAILURE",
            meta={"error": str(e), "status": "Failed"}
        )
        raise


@celery_app.task(bind=True, name="backend.tasks.pipeline_tasks.weekly_paper_backfill")
def weekly_paper_backfill(self) -> Dict[str, Any]:
    """Weekly task to backfill any missed papers."""
    try:
        logger.info("Starting weekly paper backfill task")
        
        # Update task state
        self.update_state(state="PROGRESS", meta={"status": "Starting backfill"})
        
        # Get pipeline service
        pipeline_service = get_data_pipeline_service()
        
        # Run async function in sync context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(
                pipeline_service.fetch_and_process_papers(days_back=7)
            )
        finally:
            loop.close()
        
        logger.info(f"Weekly paper backfill completed: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Weekly paper backfill failed: {e}")
        self.update_state(
            state="FAILURE",
            meta={"error": str(e), "status": "Failed"}
        )
        raise


@celery_app.task(bind=True, name="backend.tasks.pipeline_tasks.process_paper_by_id")
def process_paper_by_id(self, arxiv_id: str) -> Dict[str, Any]:
    """Process a specific paper by arXiv ID."""
    try:
        logger.info(f"Processing paper by ID: {arxiv_id}")
        
        # Update task state
        self.update_state(
            state="PROGRESS", 
            meta={"status": f"Processing paper {arxiv_id}"}
        )
        
        # Get pipeline service
        pipeline_service = get_data_pipeline_service()
        
        # Run async function in sync context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            paper = loop.run_until_complete(
                pipeline_service.process_paper_by_id(arxiv_id)
            )
        finally:
            loop.close()
        
        if paper:
            result = {
                "success": True,
                "arxiv_id": arxiv_id,
                "paper_id": paper.id,
                "title": paper.title
            }
        else:
            result = {
                "success": False,
                "arxiv_id": arxiv_id,
                "error": "Paper not found or processing failed"
            }
        
        logger.info(f"Paper processing completed: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Paper processing failed for {arxiv_id}: {e}")
        self.update_state(
            state="FAILURE",
            meta={"error": str(e), "status": "Failed"}
        )
        raise


@celery_app.task(bind=True, name="backend.tasks.pipeline_tasks.batch_process_papers")
def batch_process_papers(self, arxiv_ids: list) -> Dict[str, Any]:
    """Process multiple papers in batch."""
    try:
        logger.info(f"Processing {len(arxiv_ids)} papers in batch")
        
        results = {
            "total": len(arxiv_ids),
            "processed": 0,
            "failed": 0,
            "errors": []
        }
        
        # Get pipeline service
        pipeline_service = get_data_pipeline_service()
        
        # Run async function in sync context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            for i, arxiv_id in enumerate(arxiv_ids):
                try:
                    # Update progress
                    progress = int((i / len(arxiv_ids)) * 100)
                    self.update_state(
                        state="PROGRESS",
                        meta={
                            "status": f"Processing paper {i+1}/{len(arxiv_ids)}",
                            "progress": progress,
                            "current_paper": arxiv_id
                        }
                    )
                    
                    # Process paper
                    paper = loop.run_until_complete(
                        pipeline_service.process_paper_by_id(arxiv_id)
                    )
                    
                    if paper:
                        results["processed"] += 1
                        logger.info(f"Processed paper: {arxiv_id}")
                    else:
                        results["failed"] += 1
                        results["errors"].append(f"{arxiv_id}: Not found")
                        
                except Exception as e:
                    results["failed"] += 1
                    results["errors"].append(f"{arxiv_id}: {str(e)}")
                    logger.error(f"Failed to process paper {arxiv_id}: {e}")
        finally:
            loop.close()
        
        logger.info(f"Batch processing completed: {results}")
        return results
        
    except Exception as e:
        logger.error(f"Batch processing failed: {e}")
        self.update_state(
            state="FAILURE",
            meta={"error": str(e), "status": "Failed"}
        )
        raise


@celery_app.task(name="backend.tasks.pipeline_tasks.cleanup_old_tasks")
def cleanup_old_tasks() -> Dict[str, Any]:
    """Clean up old task results and temporary files."""
    try:
        logger.info("Starting cleanup of old tasks")
        
        # TODO: Implement cleanup logic
        # - Remove old Celery task results
        # - Clean up temporary PDF files
        # - Remove old log files
        # - Clean up failed processing artifacts
        
        result = {
            "cleaned_tasks": 0,
            "cleaned_files": 0,
            "freed_space_mb": 0
        }
        
        logger.info(f"Cleanup completed: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Cleanup failed: {e}")
        raise


@celery_app.task(bind=True, name="backend.tasks.pipeline_tasks.analyze_github_repos")
def analyze_github_repos(self, github_urls: list) -> Dict[str, Any]:
    """Analyze multiple GitHub repositories."""
    try:
        logger.info(f"Analyzing {len(github_urls)} GitHub repositories")
        
        results = {
            "total": len(github_urls),
            "analyzed": 0,
            "failed": 0,
            "analyses": [],
            "errors": []
        }
        
        # Get pipeline service
        pipeline_service = get_data_pipeline_service()
        
        # Run async function in sync context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            for i, github_url in enumerate(github_urls):
                try:
                    # Update progress
                    progress = int((i / len(github_urls)) * 100)
                    self.update_state(
                        state="PROGRESS",
                        meta={
                            "status": f"Analyzing repository {i+1}/{len(github_urls)}",
                            "progress": progress,
                            "current_repo": github_url
                        }
                    )
                    
                    # Analyze repository
                    analysis = loop.run_until_complete(
                        pipeline_service.analyze_github_repository(github_url)
                    )
                    
                    if analysis:
                        results["analyzed"] += 1
                        results["analyses"].append(analysis)
                        logger.info(f"Analyzed repository: {github_url}")
                    else:
                        results["failed"] += 1
                        results["errors"].append(f"{github_url}: Analysis failed")
                        
                except Exception as e:
                    results["failed"] += 1
                    results["errors"].append(f"{github_url}: {str(e)}")
                    logger.error(f"Failed to analyze repository {github_url}: {e}")
        finally:
            loop.close()
        
        logger.info(f"GitHub analysis completed: {results}")
        return results
        
    except Exception as e:
        logger.error(f"GitHub analysis failed: {e}")
        self.update_state(
            state="FAILURE",
            meta={"error": str(e), "status": "Failed"}
        )
        raise