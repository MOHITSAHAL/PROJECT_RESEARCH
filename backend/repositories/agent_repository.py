"""Agent repository for data access operations."""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, func
from datetime import datetime, timedelta

from .base import SQLAlchemyRepository
from ..database.models import PaperAgent, AgentConversation

class AgentRepository(SQLAlchemyRepository[PaperAgent]):
    """Repository for agent data access operations."""
    
    def __init__(self, db: Session):
        super().__init__(db, PaperAgent)
    
    async def find_by_paper_and_type(self, paper_id: str, agent_type: str) -> Optional[PaperAgent]:
        """Find agent by paper ID and type."""
        return self.db.query(PaperAgent).filter(
            and_(
                PaperAgent.paper_id == paper_id,
                PaperAgent.agent_type == agent_type
            )
        ).first()
    
    async def find_by_paper(self, paper_id: str) -> List[PaperAgent]:
        """Find all agents for a paper."""
        return self.db.query(PaperAgent).filter(PaperAgent.paper_id == paper_id).all()
    
    async def find_active_agents(self, limit: int = 50) -> List[PaperAgent]:
        """Find active agents."""
        return self.db.query(PaperAgent).filter(
            PaperAgent.status == "active"
        ).order_by(desc(PaperAgent.last_interaction)).limit(limit).all()
    
    async def update_interaction_metrics(self, agent_id: str, response_time: float) -> bool:
        """Update agent interaction metrics."""
        agent = await self.get_by_id(agent_id)
        if not agent:
            return False
        
        agent.conversation_count += 1
        agent.last_interaction = datetime.utcnow()
        
        if agent.response_time_avg:
            agent.response_time_avg = (agent.response_time_avg + response_time) / 2
        else:
            agent.response_time_avg = response_time
        
        self.db.commit()
        return True

class ConversationRepository(SQLAlchemyRepository[AgentConversation]):
    """Repository for conversation data access operations."""
    
    def __init__(self, db: Session):
        super().__init__(db, AgentConversation)
    
    async def find_by_session(self, session_id: str) -> List[AgentConversation]:
        """Find conversations by session ID."""
        return self.db.query(AgentConversation).filter(
            AgentConversation.session_id == session_id
        ).order_by(AgentConversation.created_at).all()
    
    async def find_by_agent(self, agent_id: str, limit: int = 50, offset: int = 0) -> List[AgentConversation]:
        """Find conversations by agent ID."""
        return self.db.query(AgentConversation).filter(
            AgentConversation.agent_id == agent_id
        ).order_by(desc(AgentConversation.created_at)).offset(offset).limit(limit).all()
    
    async def get_performance_metrics(self, agent_id: str, time_period: str) -> Dict[str, Any]:
        """Get performance metrics for an agent."""
        if time_period == "24h":
            threshold = datetime.utcnow() - timedelta(hours=24)
        elif time_period == "7d":
            threshold = datetime.utcnow() - timedelta(days=7)
        else:
            threshold = datetime.utcnow() - timedelta(days=30)
        
        conversations = self.db.query(AgentConversation).filter(
            and_(
                AgentConversation.agent_id == agent_id,
                AgentConversation.created_at >= threshold,
                AgentConversation.message_type == "agent"
            )
        ).all()
        
        total_queries = len(conversations)
        successful_queries = len([c for c in conversations if c.response_time is not None])
        failed_queries = total_queries - successful_queries
        
        avg_response_time = sum(c.response_time for c in conversations if c.response_time) / max(successful_queries, 1)
        avg_rating = sum(c.user_rating for c in conversations if c.user_rating) / max(len([c for c in conversations if c.user_rating]), 1)
        
        return {
            "total_queries": total_queries,
            "successful_queries": successful_queries,
            "failed_queries": failed_queries,
            "average_response_time": avg_response_time,
            "average_user_rating": avg_rating,
            "user_satisfaction_rate": avg_rating / 5.0 if avg_rating else None
        }