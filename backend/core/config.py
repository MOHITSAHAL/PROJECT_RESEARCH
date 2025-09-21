"""
Configuration management with environment-based settings.
Supports POC (SQLite) to Production (AWS) migration.
"""
import os
from typing import Optional, List
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    # Application
    app_name: str = "AI Research Paper Intelligence System"
    version: str = "1.0.0"
    debug: bool = Field(default=False, env="DEBUG")
    environment: str = Field(default="development", env="ENVIRONMENT")
    
    # API Configuration
    api_host: str = Field(default="0.0.0.0", env="API_HOST")
    api_port: int = Field(default=8000, env="API_PORT")
    api_prefix: str = "/api/v1"
    
    # Database Configuration (POC: SQLite → Production: PostgreSQL)
    database_url: str = Field(
        default="sqlite:///./research_papers.db",
        env="DATABASE_URL"
    )
    database_echo: bool = Field(default=False, env="DATABASE_ECHO")
    
    # Graph Database (Neo4j)
    neo4j_uri: str = Field(default="bolt://localhost:7687", env="NEO4J_URI")
    neo4j_user: str = Field(default="neo4j", env="NEO4J_USER")
    neo4j_password: str = Field(default="password", env="NEO4J_PASSWORD")
    
    # Cache (Redis)
    redis_url: str = Field(default="redis://localhost:6379/0", env="REDIS_URL")
    redis_password: Optional[str] = Field(default=None, env="REDIS_PASSWORD")
    
    # Vector Database
    vector_db_provider: str = Field(default="weaviate", env="VECTOR_DB_PROVIDER")  # weaviate|pinecone
    pinecone_api_key: Optional[str] = Field(default=None, env="PINECONE_API_KEY")
    pinecone_environment: Optional[str] = Field(default=None, env="PINECONE_ENVIRONMENT")
    weaviate_url: str = Field(default="http://localhost:8080", env="WEAVIATE_URL")
    
    # AI/ML APIs
    openai_api_key: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    anthropic_api_key: Optional[str] = Field(default=None, env="ANTHROPIC_API_KEY")
    
    # Message Queue
    celery_broker_url: str = Field(default="redis://localhost:6379/1", env="CELERY_BROKER_URL")
    celery_result_backend: str = Field(default="redis://localhost:6379/2", env="CELERY_RESULT_BACKEND")
    
    # AWS Configuration (Production)
    aws_region: str = Field(default="us-east-1", env="AWS_REGION")
    aws_access_key_id: Optional[str] = Field(default=None, env="AWS_ACCESS_KEY_ID")
    aws_secret_access_key: Optional[str] = Field(default=None, env="AWS_SECRET_ACCESS_KEY")
    s3_bucket_name: Optional[str] = Field(default=None, env="S3_BUCKET_NAME")
    
    # Security
    secret_key: str = Field(default="dev-secret-key-change-in-production", env="SECRET_KEY")
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Rate Limiting
    rate_limit_requests: int = Field(default=100, env="RATE_LIMIT_REQUESTS")
    rate_limit_window: int = Field(default=3600, env="RATE_LIMIT_WINDOW")  # seconds
    
    # Paper Processing
    arxiv_rate_limit: int = Field(default=3, env="ARXIV_RATE_LIMIT")  # requests per second
    max_papers_per_batch: int = Field(default=100, env="MAX_PAPERS_PER_BATCH")
    
    # Agent Configuration
    default_agent_model: str = Field(default="gpt-3.5-turbo", env="DEFAULT_AGENT_MODEL")
    max_agent_memory: int = Field(default=10, env="MAX_AGENT_MEMORY")  # conversation turns
    agent_timeout: int = Field(default=30, env="AGENT_TIMEOUT")  # seconds
    
    # Monitoring
    enable_metrics: bool = Field(default=True, env="ENABLE_METRICS")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    
    class Config:
        env_file = ".env"
        case_sensitive = False

    @property
    def is_production(self) -> bool:
        return self.environment.lower() == "production"
    
    @property
    def is_development(self) -> bool:
        return self.environment.lower() == "development"
    
    @property
    def database_config(self) -> dict:
        """Database configuration based on environment"""
        if self.is_production:
            return {
                "pool_size": 20,
                "max_overflow": 30,
                "pool_pre_ping": True,
                "pool_recycle": 3600,
            }
        return {
            "pool_size": 5,
            "max_overflow": 10,
            "pool_pre_ping": False,
        }


# Global settings instance
settings = Settings()