"""Dependency injection for FastAPI."""

from functools import lru_cache
from typing import Generator
import os

from sqlalchemy.orm import Session
from ..database.connection import get_db_session
from ..repositories.paper_repository import PaperRepository
from ..repositories.agent_repository import AgentRepository
from ..services.paper_service import PaperService
from ..services.agent_service import AgentService
from ..services.user_service import UserService
from ..services.data_pipeline_service import DataPipelineService
from ..services.ai_agent_service import AIAgentService
from ..domain.paper_domain import PaperDomain
from ..domain.agent_domain import AgentDomain


def get_db() -> Generator[Session, None, None]:
    """Get database session."""
    db = get_db_session()
    try:
        yield db
    finally:
        db.close()


@lru_cache()
def get_paper_repository() -> PaperRepository:
    """Get paper repository instance."""
    return PaperRepository()


@lru_cache()
def get_agent_repository() -> AgentRepository:
    """Get agent repository instance."""
    return AgentRepository()


@lru_cache()
def get_paper_domain() -> PaperDomain:
    """Get paper domain instance."""
    return PaperDomain()


@lru_cache()
def get_agent_domain() -> AgentDomain:
    """Get agent domain instance."""
    return AgentDomain()


def get_paper_service(
    paper_repository: PaperRepository = None,
    paper_domain: PaperDomain = None
) -> PaperService:
    """Get paper service instance."""
    if paper_repository is None:
        paper_repository = get_paper_repository()
    if paper_domain is None:
        paper_domain = get_paper_domain()
    
    return PaperService(paper_repository, paper_domain)


def get_agent_service(
    agent_repository: AgentRepository = None,
    agent_domain: AgentDomain = None
) -> AgentService:
    """Get agent service instance."""
    if agent_repository is None:
        agent_repository = get_agent_repository()
    if agent_domain is None:
        agent_domain = get_agent_domain()
    
    return AgentService(agent_repository, agent_domain)


def get_user_service() -> UserService:
    """Get user service instance."""
    return UserService()


def get_data_pipeline_service(
    paper_repository: PaperRepository = None,
    paper_domain: PaperDomain = None
) -> DataPipelineService:
    """Get data pipeline service instance."""
    if paper_repository is None:
        paper_repository = get_paper_repository()
    if paper_domain is None:
        paper_domain = get_paper_domain()
    
    # Get GitHub token from environment
    github_token = os.getenv("GITHUB_TOKEN")
    
    return DataPipelineService(paper_repository, paper_domain, github_token)


def get_ai_agent_service(
    paper_repository: PaperRepository = None,
    agent_repository: AgentRepository = None,
    agent_domain: AgentDomain = None
) -> AIAgentService:
    """Get AI agent service instance."""
    if paper_repository is None:
        paper_repository = get_paper_repository()
    if agent_repository is None:
        agent_repository = get_agent_repository()
    if agent_domain is None:
        agent_domain = get_agent_domain()
    
    return AIAgentService(paper_repository, agent_repository, agent_domain)