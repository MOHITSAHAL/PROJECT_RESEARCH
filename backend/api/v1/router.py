"""Main API router for v1 endpoints."""

from fastapi import APIRouter
from .endpoints import papers, agents, users, auth, research, data_pipeline, ai_agents, intelligent_organization

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(papers.router, prefix="/papers", tags=["Papers"])
api_router.include_router(agents.router, prefix="/agents", tags=["AI Agents"])
api_router.include_router(research.router, prefix="/research", tags=["Research Analysis"])
api_router.include_router(data_pipeline.router, tags=["Data Pipeline"])
api_router.include_router(ai_agents.router, tags=["AI Agents"])
api_router.include_router(intelligent_organization.router, prefix="/organization", tags=["Intelligent Organization"])