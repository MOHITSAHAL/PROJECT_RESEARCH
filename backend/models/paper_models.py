"""Pydantic models for paper-related API operations."""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator


class PaperBase(BaseModel):
    """Base paper model with common fields."""
    title: str = Field(..., min_length=1, max_length=1000)
    abstract: Optional[str] = Field(None, max_length=10000)
    authors: List[str] = Field(..., min_items=1)
    categories: List[str] = Field(..., min_items=1)
    journal: Optional[str] = Field(None, max_length=200)
    keywords: Optional[List[str]] = None


class PaperCreate(PaperBase):
    """Model for creating a new paper."""
    arxiv_id: Optional[str] = Field(None, regex=r"^\d{4}\.\d{4,5}(v\d+)?$")
    doi: Optional[str] = None
    published_date: Optional[datetime] = None
    pdf_url: Optional[str] = Field(None, regex=r"^https?://.*\.pdf$")
    full_text: Optional[str] = None
    github_repos: Optional[List[str]] = None


class PaperUpdate(BaseModel):
    """Model for updating an existing paper."""
    title: Optional[str] = Field(None, min_length=1, max_length=1000)
    abstract: Optional[str] = Field(None, max_length=10000)
    authors: Optional[List[str]] = None
    categories: Optional[List[str]] = None
    journal: Optional[str] = Field(None, max_length=200)
    summary: Optional[str] = None
    keywords: Optional[List[str]] = None
    methodology: Optional[List[str]] = None
    github_repos: Optional[List[str]] = None
    processing_status: Optional[str] = Field(None, regex="^(pending|processing|completed|failed)$")


class PaperResponse(PaperBase):
    """Model for paper API responses."""
    id: str
    arxiv_id: Optional[str] = None
    doi: Optional[str] = None
    published_date: Optional[datetime] = None
    updated_date: Optional[datetime] = None
    pdf_url: Optional[str] = None
    
    # Metrics
    citation_count: int = 0
    view_count: int = 0
    download_count: int = 0
    
    # AI Analysis
    summary: Optional[str] = None
    methodology: Optional[List[str]] = None
    
    # GitHub Integration
    github_repos: Optional[List[str]] = None
    has_code: bool = False
    
    # Processing status
    processing_status: str
    embedding_status: str
    
    # Agent availability
    agent_available: bool = False
    implementation_guide_available: bool = False
    
    # Timestamps
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class PaperSearchRequest(BaseModel):
    """Model for paper search requests."""
    query: Optional[str] = Field(None, max_length=500)
    categories: Optional[List[str]] = None
    authors: Optional[List[str]] = None
    date_range: Optional[Dict[str, datetime]] = None
    methodology: Optional[List[str]] = None
    has_github: Optional[bool] = None
    has_agent: Optional[bool] = None
    min_citations: Optional[int] = Field(None, ge=0)
    
    # Pagination
    limit: int = Field(50, ge=1, le=100)
    offset: int = Field(0, ge=0)
    
    # Sorting
    sort_by: str = Field("published_date", regex="^(published_date|citation_count|relevance|created_at)$")
    sort_order: str = Field("desc", regex="^(asc|desc)$")
    
    @validator("date_range")
    def validate_date_range(cls, v):
        if v and "start" in v and "end" in v:
            if v["start"] > v["end"]:
                raise ValueError("Start date must be before end date")
        return v


class PaperSearchResponse(BaseModel):
    """Model for paper search responses."""
    papers: List[PaperResponse]
    total_count: int
    page_info: Dict[str, Any]
    facets: Optional[Dict[str, Any]] = None  # Category counts, author counts, etc.
    
    class Config:
        from_attributes = True


class PaperAnalysisRequest(BaseModel):
    """Model for requesting paper analysis."""
    analysis_type: List[str] = Field(..., min_items=1)  # methodology, implementation, impact
    include_github_analysis: bool = False
    generate_tutorial: bool = False
    target_audience: str = Field("intermediate", regex="^(beginner|intermediate|expert)$")


class PaperAnalysisResponse(BaseModel):
    """Model for paper analysis results."""
    paper_id: str
    analysis_results: Dict[str, Any]
    github_analysis: Optional[Dict[str, Any]] = None
    tutorial_generated: bool = False
    tutorial_url: Optional[str] = None
    processing_time: float  # seconds
    
    class Config:
        from_attributes = True


class GitHubRepoAnalysis(BaseModel):
    """Model for GitHub repository analysis."""
    url: str
    stars: int
    forks: int
    language: Optional[str] = None
    description: Optional[str] = None
    key_files: List[str]
    implementation_quality: float = Field(..., ge=0.0, le=1.0)
    tutorial_available: bool = False
    complexity_score: float = Field(..., ge=0.0, le=1.0)
    last_updated: Optional[datetime] = None


class PaperTimelineEntry(BaseModel):
    """Model for research timeline entries."""
    paper_id: str
    title: str
    date: datetime
    breakthrough_score: float = Field(..., ge=0.0, le=1.0)
    influence_score: float = Field(..., ge=0.0, le=1.0)
    agent_available: bool = False
    implementation_complexity: str = Field(..., regex="^(beginner|intermediate|expert)$")
    key_innovations: List[str] = []


class ResearchTimelineResponse(BaseModel):
    """Model for research timeline responses."""
    topic_id: str
    topic_name: str
    timeline: List[PaperTimelineEntry]
    evolution_insights: Dict[str, Any]
    total_papers: int
    date_range: Dict[str, datetime]
    
    class Config:
        from_attributes = True