"""
SQLAlchemy models for research papers and AI agents.
Designed for SQLite (POC) to PostgreSQL (Production) migration.
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import uuid4
from sqlalchemy import (
    Column, String, Text, DateTime, Integer, Float, Boolean, 
    JSON, ForeignKey, Index, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

Base = declarative_base()


class TimestampMixin:
    """Mixin for created_at and updated_at timestamps."""
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)


class Paper(Base, TimestampMixin):
    """Research paper model."""
    __tablename__ = "papers"
    
    # Primary key
    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    
    # Paper identifiers
    arxiv_id = Column(String(50), unique=True, nullable=True, index=True)
    doi = Column(String(100), unique=True, nullable=True, index=True)
    
    # Basic information
    title = Column(Text, nullable=False, index=True)
    abstract = Column(Text, nullable=True)
    authors = Column(JSON, nullable=False)  # List of author names
    
    # Publication details
    published_date = Column(DateTime, nullable=True, index=True)
    updated_date = Column(DateTime, nullable=True)
    journal = Column(String(200), nullable=True)
    categories = Column(JSON, nullable=False)  # List of categories (cs.AI, cs.LG, etc.)
    
    # Content
    full_text = Column(Text, nullable=True)
    pdf_url = Column(String(500), nullable=True)
    
    # Metrics
    citation_count = Column(Integer, default=0, nullable=False)
    view_count = Column(Integer, default=0, nullable=False)
    download_count = Column(Integer, default=0, nullable=False)
    
    # AI Analysis
    summary = Column(Text, nullable=True)  # AI-generated summary
    keywords = Column(JSON, nullable=True)  # Extracted keywords
    methodology = Column(JSON, nullable=True)  # Detected methodologies
    
    # GitHub Integration
    github_repos = Column(JSON, nullable=True)  # Associated GitHub repositories
    has_code = Column(Boolean, default=False, nullable=False)
    
    # Processing status
    processing_status = Column(String(50), default="pending", nullable=False)  # pending, processing, completed, failed
    embedding_status = Column(String(50), default="pending", nullable=False)
    
    # Relationships
    agents = relationship("PaperAgent", back_populates="paper", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index("idx_papers_category_date", "categories", "published_date"),
        Index("idx_papers_status", "processing_status", "embedding_status"),
    )


class PaperAgent(Base, TimestampMixin):
    """AI agent associated with a research paper."""
    __tablename__ = "paper_agents"
    
    # Primary key
    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    
    # Foreign key to paper
    paper_id = Column(String(36), ForeignKey("papers.id"), nullable=False, index=True)
    
    # Agent configuration
    agent_type = Column(String(50), nullable=False)  # interactive, implementation, analysis
    model_name = Column(String(100), nullable=False)  # gpt-4, gpt-3.5-turbo, claude-3
    specialization = Column(String(100), nullable=True)  # implementation_guide, methodology_expert
    
    # Agent state
    status = Column(String(50), default="active", nullable=False)  # active, inactive, training
    conversation_count = Column(Integer, default=0, nullable=False)
    last_interaction = Column(DateTime, nullable=True)
    
    # Performance metrics
    response_time_avg = Column(Float, nullable=True)  # Average response time in seconds
    user_rating_avg = Column(Float, nullable=True)  # Average user rating (1-5)
    success_rate = Column(Float, nullable=True)  # Success rate percentage
    
    # Agent memory and context
    memory_size = Column(Integer, default=10, nullable=False)  # Number of conversation turns to remember
    context_data = Column(JSON, nullable=True)  # Agent-specific context and memory
    
    # Capabilities
    capabilities = Column(JSON, nullable=False)  # List of agent capabilities
    
    # Relationships
    paper = relationship("Paper", back_populates="agents")
    conversations = relationship("AgentConversation", back_populates="agent", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index("idx_agents_paper_type", "paper_id", "agent_type"),
        Index("idx_agents_status", "status", "last_interaction"),
    )


class AgentConversation(Base, TimestampMixin):
    """Conversation history between users and paper agents."""
    __tablename__ = "agent_conversations"
    
    # Primary key
    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    
    # Foreign keys
    agent_id = Column(String(36), ForeignKey("paper_agents.id"), nullable=False, index=True)
    user_id = Column(String(36), nullable=False, index=True)  # User identifier
    
    # Conversation details
    session_id = Column(String(36), nullable=False, index=True)  # Groups related messages
    message_type = Column(String(20), nullable=False)  # user, agent, system
    content = Column(Text, nullable=False)
    
    # Context and metadata
    context = Column(JSON, nullable=True)  # Additional context for the message
    response_time = Column(Float, nullable=True)  # Response time in seconds
    token_count = Column(Integer, nullable=True)  # Number of tokens used
    
    # User feedback
    user_rating = Column(Integer, nullable=True)  # 1-5 rating
    user_feedback = Column(Text, nullable=True)
    
    # Relationships
    agent = relationship("PaperAgent", back_populates="conversations")
    
    __table_args__ = (
        Index("idx_conversations_session", "session_id", "created_at"),
        Index("idx_conversations_user", "user_id", "created_at"),
    )


class ResearchTopic(Base, TimestampMixin):
    """Research topics and categories."""
    __tablename__ = "research_topics"
    
    # Primary key
    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    
    # Topic information
    name = Column(String(200), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)
    category = Column(String(100), nullable=False, index=True)  # cs.AI, cs.LG, etc.
    
    # Hierarchy
    parent_topic_id = Column(String(36), ForeignKey("research_topics.id"), nullable=True)
    level = Column(Integer, default=0, nullable=False)  # Hierarchy level
    
    # Metrics
    paper_count = Column(Integer, default=0, nullable=False)
    agent_count = Column(Integer, default=0, nullable=False)
    popularity_score = Column(Float, default=0.0, nullable=False)
    
    # Evolution tracking
    first_paper_date = Column(DateTime, nullable=True)
    latest_paper_date = Column(DateTime, nullable=True)
    growth_rate = Column(Float, nullable=True)  # Papers per month
    
    # Relationships
    parent_topic = relationship("ResearchTopic", remote_side=[id])
    child_topics = relationship("ResearchTopic", back_populates="parent_topic")
    
    __table_args__ = (
        Index("idx_topics_category_popularity", "category", "popularity_score"),
        Index("idx_topics_hierarchy", "parent_topic_id", "level"),
    )


class User(Base, TimestampMixin):
    """User model for authentication and preferences."""
    __tablename__ = "users"
    
    # Primary key
    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    
    # Authentication
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    hashed_password = Column(String(100), nullable=False)
    
    # Profile
    full_name = Column(String(200), nullable=True)
    affiliation = Column(String(200), nullable=True)
    research_interests = Column(JSON, nullable=True)  # List of research areas
    
    # Preferences
    preferred_frameworks = Column(JSON, nullable=True)  # pytorch, tensorflow, etc.
    experience_level = Column(String(20), default="intermediate", nullable=False)  # beginner, intermediate, expert
    notification_preferences = Column(JSON, nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    last_login = Column(DateTime, nullable=True)
    
    # Usage metrics
    total_queries = Column(Integer, default=0, nullable=False)
    total_agents_created = Column(Integer, default=0, nullable=False)
    
    __table_args__ = (
        Index("idx_users_active", "is_active", "last_login"),
    )


class PaperEmbedding(Base, TimestampMixin):
    """Vector embeddings for papers (for vector database sync)."""
    __tablename__ = "paper_embeddings"
    
    # Primary key
    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    
    # Foreign key
    paper_id = Column(String(36), ForeignKey("papers.id"), nullable=False, unique=True, index=True)
    
    # Embedding metadata
    embedding_model = Column(String(100), nullable=False)  # sentence-transformers/all-MiniLM-L6-v2
    embedding_dimension = Column(Integer, nullable=False)
    
    # Vector database references
    vector_db_id = Column(String(100), nullable=True)  # ID in Pinecone/Weaviate
    vector_db_provider = Column(String(50), nullable=False)  # pinecone, weaviate
    
    # Processing status
    status = Column(String(50), default="pending", nullable=False)  # pending, completed, failed
    error_message = Column(Text, nullable=True)
    
    # Relationships
    paper = relationship("Paper")
    
    __table_args__ = (
        Index("idx_embeddings_status", "status", "created_at"),
    )