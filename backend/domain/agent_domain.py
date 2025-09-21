"""Agent domain logic and business rules."""

from typing import List, Optional, Dict, Any
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

from ..repositories.agent_repository import AgentRepository, ConversationRepository
from ..events.base import event_bus
from ..core.logging import LoggerMixin

class AgentCapability(Enum):
    """Agent capability types."""
    QUESTION_ANSWERING = "question_answering"
    CODE_GENERATION = "code_generation"
    METHODOLOGY_ANALYSIS = "methodology_analysis"
    IMPLEMENTATION_GUIDE = "implementation_guide"
    MULTI_AGENT_COLLABORATION = "multi_agent_collaboration"

class CollaborationMode(Enum):
    """Multi-agent collaboration modes."""
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    DEBATE = "debate"
    CONSENSUS = "consensus"

@dataclass
class AgentDomainModel:
    """Domain model for agent with business logic."""
    id: str
    paper_id: str
    agent_type: str
    model_name: str
    specialization: Optional[str]
    status: str
    conversation_count: int = 0
    response_time_avg: Optional[float] = None
    user_rating_avg: Optional[float] = None
    capabilities: List[str] = None
    
    def is_active(self) -> bool:
        """Check if agent is active."""
        return self.status == "active"
    
    def is_experienced(self) -> bool:
        """Check if agent has sufficient experience."""
        return self.conversation_count >= 10
    
    def has_capability(self, capability: AgentCapability) -> bool:
        """Check if agent has specific capability."""
        return capability.value in (self.capabilities or [])
    
    def get_performance_rating(self) -> str:
        """Get performance rating based on metrics."""
        if not self.user_rating_avg:
            return "unrated"
        
        if self.user_rating_avg >= 4.5:
            return "excellent"
        elif self.user_rating_avg >= 4.0:
            return "good"
        elif self.user_rating_avg >= 3.0:
            return "average"
        else:
            return "needs_improvement"
    
    def is_suitable_for_collaboration(self) -> bool:
        """Check if agent is suitable for collaboration."""
        return (
            self.is_active() and 
            self.is_experienced() and
            self.has_capability(AgentCapability.MULTI_AGENT_COLLABORATION)
        )

class AgentDomainService(LoggerMixin):
    """Domain service for agent business operations."""
    
    def __init__(self, agent_repository: AgentRepository, conversation_repository: ConversationRepository):
        self.agent_repository = agent_repository
        self.conversation_repository = conversation_repository
    
    async def create_specialized_agent(self, paper_id: str, agent_type: str, 
                                     specialization: str, model_name: str) -> AgentDomainModel:
        """Create specialized agent with domain validation."""
        # Business rule: One agent per type per paper
        existing = await self.agent_repository.find_by_paper_and_type(paper_id, agent_type)
        if existing:
            raise ValueError(f"Agent of type {agent_type} already exists for this paper")
        
        # Business rule: Validate specialization matches agent type
        valid_specializations = self._get_valid_specializations(agent_type)
        if specialization not in valid_specializations:
            raise ValueError(f"Invalid specialization {specialization} for agent type {agent_type}")
        
        # Create agent with appropriate capabilities
        capabilities = self._get_capabilities_for_type(agent_type)
        
        agent_data = {
            "paper_id": paper_id,
            "agent_type": agent_type,
            "model_name": model_name,
            "specialization": specialization,
            "capabilities": capabilities,
            "status": "initializing"
        }
        
        agent = await self.agent_repository.create(agent_data)
        
        # Publish domain event
        await event_bus.publish(
            event_bus.create_event(
                "agent.created",
                {"agent_id": agent.id, "paper_id": paper_id, "agent_type": agent_type},
                "agent_domain"
            )
        )
        
        return self._to_domain_model(agent)
    
    async def orchestrate_collaboration(self, agent_ids: List[str], task: str, 
                                      mode: CollaborationMode) -> Dict[str, Any]:
        """Orchestrate multi-agent collaboration with domain logic."""
        # Validate agents exist and are suitable
        agents = []
        for agent_id in agent_ids:
            agent = await self.agent_repository.get_by_id(agent_id)
            if not agent:
                raise ValueError(f"Agent {agent_id} not found")
            
            domain_agent = self._to_domain_model(agent)
            if not domain_agent.is_suitable_for_collaboration():
                raise ValueError(f"Agent {agent_id} is not suitable for collaboration")
            
            agents.append(domain_agent)
        
        # Business rule: Minimum 2 agents for collaboration
        if len(agents) < 2:
            raise ValueError("At least 2 agents required for collaboration")
        
        # Business rule: Maximum 5 agents to avoid complexity
        if len(agents) > 5:
            raise ValueError("Maximum 5 agents allowed for collaboration")
        
        collaboration_id = f"collab_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        
        # Publish collaboration start event
        await event_bus.publish(
            event_bus.create_event(
                "agent.collaboration_started",
                {
                    "collaboration_id": collaboration_id,
                    "agent_ids": agent_ids,
                    "task": task,
                    "mode": mode.value
                },
                "agent_domain"
            )
        )
        
        return {
            "collaboration_id": collaboration_id,
            "participating_agents": agent_ids,
            "collaboration_mode": mode.value,
            "task": task,
            "status": "initiated"
        }
    
    async def evaluate_agent_performance(self, agent_id: str) -> Dict[str, Any]:
        """Evaluate agent performance using domain logic."""
        agent = await self.agent_repository.get_by_id(agent_id)
        if not agent:
            raise ValueError("Agent not found")
        
        domain_agent = self._to_domain_model(agent)
        
        # Get performance metrics from repository
        metrics = await self.conversation_repository.get_performance_metrics(agent_id, "30d")
        
        # Apply domain logic for evaluation
        performance_rating = domain_agent.get_performance_rating()
        experience_level = "experienced" if domain_agent.is_experienced() else "novice"
        
        # Calculate improvement recommendations
        recommendations = self._generate_improvement_recommendations(domain_agent, metrics)
        
        return {
            "agent_id": agent_id,
            "performance_rating": performance_rating,
            "experience_level": experience_level,
            "metrics": metrics,
            "recommendations": recommendations,
            "is_collaboration_ready": domain_agent.is_suitable_for_collaboration()
        }
    
    def _get_valid_specializations(self, agent_type: str) -> List[str]:
        """Get valid specializations for agent type."""
        specialization_map = {
            "interactive": ["general", "beginner_friendly", "expert_level"],
            "implementation": ["pytorch", "tensorflow", "huggingface", "general"],
            "analysis": ["methodology", "impact", "comparison", "trends"],
            "collaboration": ["coordinator", "synthesizer", "facilitator"]
        }
        return specialization_map.get(agent_type, ["general"])
    
    def _get_capabilities_for_type(self, agent_type: str) -> List[str]:
        """Get capabilities for agent type."""
        capability_map = {
            "interactive": [
                AgentCapability.QUESTION_ANSWERING.value,
                AgentCapability.METHODOLOGY_ANALYSIS.value
            ],
            "implementation": [
                AgentCapability.CODE_GENERATION.value,
                AgentCapability.IMPLEMENTATION_GUIDE.value
            ],
            "analysis": [
                AgentCapability.METHODOLOGY_ANALYSIS.value
            ],
            "collaboration": [
                AgentCapability.MULTI_AGENT_COLLABORATION.value,
                AgentCapability.QUESTION_ANSWERING.value
            ]
        }
        return capability_map.get(agent_type, [AgentCapability.QUESTION_ANSWERING.value])
    
    def _generate_improvement_recommendations(self, agent: AgentDomainModel, 
                                           metrics: Dict[str, Any]) -> List[str]:
        """Generate improvement recommendations."""
        recommendations = []
        
        if metrics.get("average_response_time", 0) > 5.0:
            recommendations.append("Optimize response time - consider model fine-tuning")
        
        if metrics.get("average_user_rating", 0) < 3.5:
            recommendations.append("Improve response quality - review training data")
        
        if not agent.is_experienced():
            recommendations.append("Gain more experience through user interactions")
        
        if metrics.get("failed_queries", 0) > metrics.get("successful_queries", 1) * 0.1:
            recommendations.append("Reduce error rate - improve error handling")
        
        return recommendations
    
    def _to_domain_model(self, agent) -> AgentDomainModel:
        """Convert database model to domain model."""
        return AgentDomainModel(
            id=agent.id,
            paper_id=agent.paper_id,
            agent_type=agent.agent_type,
            model_name=agent.model_name,
            specialization=agent.specialization,
            status=agent.status,
            conversation_count=agent.conversation_count,
            response_time_avg=agent.response_time_avg,
            user_rating_avg=agent.user_rating_avg,
            capabilities=agent.capabilities
        )