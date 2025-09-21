"""
Database connection management for SQLAlchemy and Neo4j.
Supports SQLite (POC) to PostgreSQL (Production) migration.
"""
from typing import Generator, Optional
from contextlib import contextmanager
from sqlalchemy import create_engine, Engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from neo4j import GraphDatabase, Driver, Session as Neo4jSession
import redis
from redis import Redis

from ..core.config import settings
from ..core.logging import get_logger

logger = get_logger(__name__)


class DatabaseManager:
    """Manages database connections for SQLAlchemy, Neo4j, and Redis."""
    
    def __init__(self):
        self._engine: Optional[Engine] = None
        self._session_factory: Optional[sessionmaker] = None
        self._neo4j_driver: Optional[Driver] = None
        self._redis_client: Optional[Redis] = None
    
    @property
    def engine(self) -> Engine:
        """Get SQLAlchemy engine (lazy initialization)."""
        if self._engine is None:
            self._engine = self._create_engine()
        return self._engine
    
    @property
    def session_factory(self) -> sessionmaker:
        """Get SQLAlchemy session factory."""
        if self._session_factory is None:
            self._session_factory = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self.engine
            )
        return self._session_factory
    
    @property
    def neo4j_driver(self) -> Driver:
        """Get Neo4j driver (lazy initialization)."""
        if self._neo4j_driver is None:
            self._neo4j_driver = GraphDatabase.driver(
                settings.neo4j_uri,
                auth=(settings.neo4j_user, settings.neo4j_password)
            )
            logger.info("Connected to Neo4j", uri=settings.neo4j_uri)
        return self._neo4j_driver
    
    @property
    def redis_client(self) -> Redis:
        """Get Redis client (lazy initialization)."""
        if self._redis_client is None:
            self._redis_client = redis.from_url(
                settings.redis_url,
                password=settings.redis_password,
                decode_responses=True
            )
            logger.info("Connected to Redis", url=settings.redis_url)
        return self._redis_client
    
    def _create_engine(self) -> Engine:
        """Create SQLAlchemy engine based on environment."""
        connect_args = {}
        
        # SQLite specific configuration (POC)
        if settings.database_url.startswith("sqlite"):
            connect_args = {
                "check_same_thread": False,
                "poolclass": StaticPool,
            }
            logger.info("Using SQLite database", path=settings.database_url)
        else:
            # PostgreSQL configuration (Production)
            logger.info("Using PostgreSQL database", url=settings.database_url.split("@")[-1])
        
        engine = create_engine(
            settings.database_url,
            echo=settings.database_echo,
            connect_args=connect_args,
            **settings.database_config
        )
        
        return engine
    
    def get_session(self) -> Session:
        """Get SQLAlchemy session."""
        return self.session_factory()
    
    @contextmanager
    def get_neo4j_session(self) -> Generator[Neo4jSession, None, None]:
        """Get Neo4j session context manager."""
        session = self.neo4j_driver.session()
        try:
            yield session
        finally:
            session.close()
    
    def close_connections(self):
        """Close all database connections."""
        if self._engine:
            self._engine.dispose()
            logger.info("Closed SQLAlchemy engine")
        
        if self._neo4j_driver:
            self._neo4j_driver.close()
            logger.info("Closed Neo4j driver")
        
        if self._redis_client:
            self._redis_client.close()
            logger.info("Closed Redis client")
    
    def health_check(self) -> dict:
        """Check health of all database connections."""
        health = {
            "sqlalchemy": False,
            "neo4j": False,
            "redis": False
        }
        
        # Check SQLAlchemy
        try:
            with self.engine.connect() as conn:
                conn.execute("SELECT 1")
            health["sqlalchemy"] = True
        except Exception as e:
            logger.error("SQLAlchemy health check failed", error=str(e))
        
        # Check Neo4j
        try:
            with self.get_neo4j_session() as session:
                session.run("RETURN 1")
            health["neo4j"] = True
        except Exception as e:
            logger.error("Neo4j health check failed", error=str(e))
        
        # Check Redis
        try:
            self.redis_client.ping()
            health["redis"] = True
        except Exception as e:
            logger.error("Redis health check failed", error=str(e))
        
        return health


# Global database manager instance
db_manager = DatabaseManager()


def get_db_session() -> Generator[Session, None, None]:
    """Dependency for getting SQLAlchemy session."""
    session = db_manager.get_session()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_neo4j_session() -> Generator[Neo4jSession, None, None]:
    """Dependency for getting Neo4j session."""
    with db_manager.get_neo4j_session() as session:
        yield session


def get_redis_client() -> Redis:
    """Dependency for getting Redis client."""
    return db_manager.redis_client