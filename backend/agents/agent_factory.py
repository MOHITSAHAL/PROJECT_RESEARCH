"""Agent factory for creating and managing paper agents."""

from typing import Dict, Any, Optional, List
from .paper_agent import PaperAgent
from .multi_agent import MultiAgentCoordinator
from ..core.logging import LoggerMixin
from ..core.config import settings


class AgentFactory(LoggerMixin):
    """Factory for creating and managing AI agents."""
    
    def __init__(self):
        self.active_agents: Dict[str, PaperAgent] = {}
        self.coordinator = MultiAgentCoordinator()
        
    def create_paper_agent(self, agent_id: str, paper_data: Dict[str, Any], 
                          agent_config: Optional[Dict[str, Any]] = None) -> PaperAgent:
        """Create a new paper agent."""
        try:
            # Default configuration
            default_config = {
                "model_name": settings.default_agent_model,
                "memory_size": settings.max_agent_memory,
                "timeout": settings.agent_timeout,
                "capabilities": self._get_default_capabilities(agent_config.get("agent_type", "interactive") if agent_config else "interactive")
            }
            
            # Merge with provided config
            if agent_config:
                default_config.update(agent_config)
            
            # Create agent
            agent = PaperAgent(agent_id, paper_data, default_config)
            
            # Store agent
            self.active_agents[agent_id] = agent
            
            # Register with coordinator
            self.coordinator.register_agent(agent_id, agent)
            
            self.log_event("agent_created", agent_id=agent_id, paper_title=paper_data.get("title", ""))
            return agent
            
        except Exception as e:
            self.log_error(e, operation="create_paper_agent", agent_id=agent_id)
            raise
    
    def get_agent(self, agent_id: str) -> Optional[PaperAgent]:
        """Get an existing agent."""
        return self.active_agents.get(agent_id)
    
    def remove_agent(self, agent_id: str) -> bool:
        """Remove an agent."""
        if agent_id in self.active_agents:
            # Unregister from coordinator
            self.coordinator.unregister_agent(agent_id)
            
            # Remove from active agents
            del self.active_agents[agent_id]
            
            self.log_event("agent_removed", agent_id=agent_id)
            return True
        return False
    
    def list_agents(self) -> List[str]:
        """List all active agent IDs."""
        return list(self.active_agents.keys())
    
    def get_agents_by_paper(self, paper_id: str) -> List[PaperAgent]:
        """Get all agents for a specific paper."""
        return [
            agent for agent in self.active_agents.values()
            if agent.paper_data.get("id") == paper_id
        ]
    
    def get_agents_by_type(self, agent_type: str) -> List[PaperAgent]:
        """Get all agents of a specific type."""
        return [
            agent for agent in self.active_agents.values()
            if agent.config.get("agent_type") == agent_type
        ]
    
    def create_specialized_agent(self, agent_id: str, paper_data: Dict[str, Any], 
                                specialization: str) -> PaperAgent:
        """Create a specialized agent for specific tasks."""
        specialized_configs = {
            "implementation_guide": {
                "agent_type": "implementation",
                "capabilities": ["code_generation", "tutorial_creation", "debugging", "framework_guidance"],
                "specialization": "implementation_guide",
                "model_name": "gpt-4"  # Use more capable model for implementation
            },
            "methodology_expert": {
                "agent_type": "analysis",
                "capabilities": ["methodology_analysis", "technical_explanation", "comparison", "evaluation"],
                "specialization": "methodology_expert",
                "model_name": "gpt-4"
            },
            "research_assistant": {
                "agent_type": "interactive",
                "capabilities": ["question_answering", "explanation", "discussion", "research_guidance"],
                "specialization": "research_assistant",
                "model_name": "gpt-3.5-turbo"
            },
            "code_reviewer": {
                "agent_type": "implementation",
                "capabilities": ["code_review", "optimization_suggestions", "best_practices", "debugging"],
                "specialization": "code_reviewer",
                "model_name": "gpt-4"
            }
        }
        
        config = specialized_configs.get(specialization, {})
        if not config:
            raise ValueError(f"Unknown specialization: {specialization}")
        
        return self.create_paper_agent(agent_id, paper_data, config)
    
    def create_multi_agent_network(self, network_id: str, paper_ids: List[str], 
                                  network_config: Optional[Dict[str, Any]] = None) -> List[str]:
        """Create a network of agents for collaborative analysis."""
        agent_ids = []
        
        for i, paper_id in enumerate(paper_ids):
            # Create different types of agents for diversity
            agent_types = ["interactive", "analysis", "implementation"]
            agent_type = agent_types[i % len(agent_types)]
            
            agent_id = f"{network_id}_agent_{i}"
            
            # Get paper data (this would come from database in real implementation)
            paper_data = {"id": paper_id, "title": f"Paper {paper_id}"}
            
            config = {
                "agent_type": agent_type,
                "network_id": network_id,
                "network_role": f"specialist_{agent_type}"
            }
            
            if network_config:
                config.update(network_config)
            
            agent = self.create_paper_agent(agent_id, paper_data, config)
            agent_ids.append(agent_id)
        
        self.log_event("multi_agent_network_created", network_id=network_id, agent_count=len(agent_ids))
        return agent_ids
    
    def update_agent_config(self, agent_id: str, config_update: Dict[str, Any]) -> bool:
        """Update agent configuration."""
        agent = self.get_agent(agent_id)
        if not agent:
            return False
        
        # Update configuration
        agent.config.update(config_update)
        
        # Update capabilities if provided
        if "capabilities" in config_update:
            agent.capabilities = config_update["capabilities"]
        
        self.log_event("agent_config_updated", agent_id=agent_id, updates=list(config_update.keys()))
        return True
    
    def get_agent_stats(self) -> Dict[str, Any]:
        """Get statistics about active agents."""
        stats = {
            "total_agents": len(self.active_agents),
            "agents_by_type": {},
            "agents_by_specialization": {},
            "agents_by_model": {}
        }
        
        for agent in self.active_agents.values():
            # Count by type
            agent_type = agent.config.get("agent_type", "unknown")
            stats["agents_by_type"][agent_type] = stats["agents_by_type"].get(agent_type, 0) + 1
            
            # Count by specialization
            specialization = agent.specialization or "general"
            stats["agents_by_specialization"][specialization] = stats["agents_by_specialization"].get(specialization, 0) + 1
            
            # Count by model
            model = agent.model_name
            stats["agents_by_model"][model] = stats["agents_by_model"].get(model, 0) + 1
        
        return stats
    
    def cleanup_inactive_agents(self, inactive_threshold_hours: int = 24) -> int:
        """Clean up agents that haven't been used recently."""
        from datetime import datetime, timedelta
        
        threshold = datetime.utcnow() - timedelta(hours=inactive_threshold_hours)
        inactive_agents = []
        
        for agent_id, agent in self.active_agents.items():
            # Check if agent has recent activity (this would check actual conversation data)
            # For now, we'll use a simple heuristic
            if len(agent.memory.conversation_history) == 0:
                inactive_agents.append(agent_id)
        
        # Remove inactive agents
        removed_count = 0
        for agent_id in inactive_agents:
            if self.remove_agent(agent_id):
                removed_count += 1
        
        if removed_count > 0:
            self.log_event("inactive_agents_cleaned", removed_count=removed_count)
        
        return removed_count
    
    def _get_default_capabilities(self, agent_type: str) -> List[str]:
        """Get default capabilities for agent type."""
        capability_map = {
            "interactive": [
                "question_answering",
                "explanation", 
                "discussion",
                "clarification"
            ],
            "implementation": [
                "code_generation",
                "tutorial_creation",
                "debugging",
                "framework_guidance",
                "best_practices"
            ],
            "analysis": [
                "methodology_analysis",
                "technical_explanation",
                "comparison",
                "evaluation",
                "critique"
            ],
            "collaboration": [
                "multi_agent_coordination",
                "consensus_building",
                "synthesis",
                "mediation"
            ]
        }
        
        return capability_map.get(agent_type, ["general_assistance"])
    
    def validate_agent_config(self, config: Dict[str, Any]) -> bool:
        """Validate agent configuration."""
        required_fields = ["agent_type"]
        
        for field in required_fields:
            if field not in config:
                return False
        
        # Validate agent_type
        valid_types = ["interactive", "implementation", "analysis", "collaboration"]
        if config["agent_type"] not in valid_types:
            return False
        
        # Validate model_name if provided
        if "model_name" in config:
            valid_models = ["gpt-3.5-turbo", "gpt-4", "claude-3", "claude-2"]
            if config["model_name"] not in valid_models:
                return False
        
        return True
    
    def get_coordinator(self) -> MultiAgentCoordinator:
        """Get the multi-agent coordinator."""
        return self.coordinator


# Global agent factory instance
agent_factory = AgentFactory()