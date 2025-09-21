"""Pydantic models for AI agent operations."""

from datetime import datetime
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field, validator


class AgentBase(BaseModel):
    """Base agent model with common fields."""
    agent_type: str = Field(..., regex="^(interactive|implementation|analysis|collaboration)$")
    model_name: str = Field("gpt-3.5-turbo", regex="^(gpt-3.5-turbo|gpt-4|claude-3|claude-2)$")
    specialization: Optional[str] = Field(None, max_length=100)


class AgentCreate(AgentBase):
    """Model for creating a new paper agent."""
    paper_id: str = Field(..., min_length=1)
    capabilities: List[str] = Field(default_factory=list)
    memory_size: int = Field(10, ge=1, le=50)
    context_data: Optional[Dict[str, Any]] = None


class AgentUpdate(BaseModel):
    """Model for updating an existing agent."""
    status: Optional[str] = Field(None, regex="^(active|inactive|training|maintenance)$")
    specialization: Optional[str] = Field(None, max_length=100)
    capabilities: Optional[List[str]] = None
    memory_size: Optional[int] = Field(None, ge=1, le=50)
    context_data: Optional[Dict[str, Any]] = None


class AgentResponse(AgentBase):
    """Model for agent API responses."""
    id: str
    paper_id: str
    status: str
    conversation_count: int = 0
    last_interaction: Optional[datetime] = None
    
    # Performance metrics
    response_time_avg: Optional[float] = None
    user_rating_avg: Optional[float] = None
    success_rate: Optional[float] = None
    
    # Configuration
    memory_size: int
    capabilities: List[str]
    
    # Timestamps
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class AgentQueryRequest(BaseModel):
    """Model for querying an agent."""
    query: str = Field(..., min_length=1, max_length=2000)
    context: Optional[Dict[str, Any]] = None
    session_id: Optional[str] = None
    user_preferences: Optional[Dict[str, Any]] = None
    
    @validator("context")
    def validate_context(cls, v):
        if v and len(str(v)) > 10000:  # Limit context size
            raise ValueError("Context too large")
        return v


class AgentQueryResponse(BaseModel):
    """Model for agent query responses."""
    agent_id: str
    session_id: str
    response: str
    response_type: str = Field("text", regex="^(text|code|tutorial|analysis)$")
    
    # Metadata
    response_time: float  # seconds
    token_count: Optional[int] = None
    confidence_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    
    # Additional data
    code_examples: Optional[List[Dict[str, str]]] = None
    references: Optional[List[str]] = None
    follow_up_suggestions: Optional[List[str]] = None
    
    # Context for next interaction
    updated_context: Optional[Dict[str, Any]] = None
    
    class Config:
        from_attributes = True


class ConversationMessage(BaseModel):
    """Model for conversation messages."""
    id: str
    message_type: str = Field(..., regex="^(user|agent|system)$")
    content: str
    timestamp: datetime
    response_time: Optional[float] = None
    user_rating: Optional[int] = Field(None, ge=1, le=5)
    user_feedback: Optional[str] = None


class ConversationResponse(BaseModel):
    """Model for conversation history responses."""
    session_id: str
    agent_id: str
    user_id: str
    messages: List[ConversationMessage]
    total_messages: int
    started_at: datetime
    last_message_at: datetime
    
    class Config:
        from_attributes = True


class ImplementationGuideRequest(BaseModel):
    """Model for requesting implementation guides."""
    framework: str = Field("pytorch", regex="^(pytorch|tensorflow|jax|sklearn|huggingface)$")
    complexity_level: str = Field("beginner", regex="^(beginner|intermediate|expert)$")
    include_github_analysis: bool = True
    interactive_mode: bool = False
    target_environment: str = Field("jupyter", regex="^(jupyter|colab|local|cloud)$")


class ImplementationGuideResponse(BaseModel):
    """Model for implementation guide responses."""
    guide_id: str
    paper_id: str
    agent_id: str
    framework: str
    complexity_level: str
    
    # Guide content
    steps: List[Dict[str, Any]]
    code_examples: List[Dict[str, str]]
    requirements: List[str]
    estimated_time: int  # minutes
    
    # GitHub integration
    github_repos_analyzed: List[str]
    reference_implementations: List[Dict[str, str]]
    
    # Interactive features
    interactive_notebook_url: Optional[str] = None
    sandbox_environment_url: Optional[str] = None
    
    class Config:
        from_attributes = True


class MultiAgentRequest(BaseModel):
    """Model for multi-agent collaboration requests."""
    agent_ids: List[str] = Field(..., min_items=2, max_items=10)
    task: str = Field(..., regex="^(compare_architectures|synthesize_knowledge|research_evolution|gap_analysis)$")
    query: str = Field(..., min_length=1, max_length=2000)
    collaboration_mode: str = Field("sequential", regex="^(sequential|parallel|debate|consensus)$")
    max_iterations: int = Field(3, ge=1, le=10)


class MultiAgentResponse(BaseModel):
    """Model for multi-agent collaboration responses."""
    collaboration_id: str
    task: str
    participating_agents: List[str]
    
    # Results
    synthesized_response: str
    individual_responses: Dict[str, str]
    consensus_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    
    # Process metadata
    total_iterations: int
    processing_time: float  # seconds
    collaboration_quality: Optional[float] = Field(None, ge=0.0, le=1.0)
    
    # Additional insights
    key_agreements: List[str] = []
    key_disagreements: List[str] = []
    recommended_follow_up: Optional[str] = None
    
    class Config:
        from_attributes = True


class AgentPerformanceMetrics(BaseModel):
    """Model for agent performance metrics."""
    agent_id: str
    time_period: str  # "24h", "7d", "30d"
    
    # Usage metrics
    total_queries: int
    successful_queries: int
    failed_queries: int
    average_response_time: float
    
    # Quality metrics
    average_user_rating: Optional[float] = None
    user_satisfaction_rate: Optional[float] = None
    
    # Performance trends
    response_time_trend: List[Dict[str, Any]] = []
    usage_trend: List[Dict[str, Any]] = []
    
    class Config:
        from_attributes = True


class AgentCapability(BaseModel):
    """Model for agent capabilities."""
    name: str
    description: str
    enabled: bool = True
    confidence_level: float = Field(..., ge=0.0, le=1.0)
    last_updated: datetime


class AgentNetworkNode(BaseModel):
    """Model for agent network nodes."""
    agent_id: str
    paper_id: str
    agent_type: str
    specialization: Optional[str] = None
    capabilities: List[AgentCapability]
    connection_strength: Dict[str, float] = {}  # agent_id -> strength


class AgentNetworkResponse(BaseModel):
    """Model for agent network responses."""
    topic_id: str
    nodes: List[AgentNetworkNode]
    collaborations: List[Dict[str, Any]]
    network_metrics: Dict[str, Any]
    
    class Config:
        from_attributes = True