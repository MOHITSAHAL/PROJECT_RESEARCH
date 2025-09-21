"""Service for managing AI agents and multi-agent interactions."""

import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime
import structlog

from ..repositories.paper_repository import PaperRepository
from ..repositories.agent_repository import AgentRepository
from ..domain.agent_domain import AgentDomain
from ..models.agent_models import AgentCreate, AgentResponse

# Import AI service components
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../ai-service'))

from agents.paper_agent import PaperAgentFactory, PaperAgent
from multi_agent.agent_coordinator import AgentCoordinator, ConversationType

logger = structlog.get_logger()


class AIAgentService:
    """Service for managing AI agents and interactions."""
    
    def __init__(
        self,
        paper_repository: PaperRepository,
        agent_repository: AgentRepository,
        agent_domain: AgentDomain
    ):
        self.paper_repository = paper_repository
        self.agent_repository = agent_repository
        self.agent_domain = agent_domain
        
        # Initialize agent coordinator
        self.agent_coordinator = AgentCoordinator()
        
        # Active agents cache
        self.active_agents: Dict[str, PaperAgent] = {}
    
    async def create_paper_agent(
        self,
        paper_id: str,
        model_name: str = "gpt-3.5-turbo",
        temperature: float = 0.1
    ) -> AgentResponse:
        """Create an AI agent for a research paper."""
        try:
            logger.info(f"Creating agent for paper: {paper_id}")
            
            # Get paper data
            paper = await self.paper_repository.get_by_id(paper_id)
            if not paper:
                raise ValueError(f"Paper {paper_id} not found")
            
            # Check if agent already exists
            existing_agent = await self.agent_repository.get_by_paper_id(paper_id)
            if existing_agent:
                logger.info(f"Agent already exists for paper: {paper_id}")
                return existing_agent
            
            # Prepare paper data for agent
            paper_data = {
                "id": paper.id,
                "title": paper.title,
                "abstract": paper.abstract,
                "full_text": paper.full_text,
                "authors": paper.authors,
                "categories": paper.categories,
                "methodology": paper.methodology or [],
                "github_repos": paper.github_repos or [],
                "key_findings": []  # TODO: Extract from processed content
            }
            
            # Create agent
            agent = PaperAgentFactory.create_agent(
                paper_data=paper_data,
                model_name=model_name,
                temperature=temperature
            )
            
            # Register with coordinator
            await self.agent_coordinator.register_agent(paper_data)
            
            # Cache active agent
            self.active_agents[paper_id] = agent
            
            # Save agent configuration to database
            agent_create = AgentCreate(
                paper_id=paper_id,
                agent_type="paper_agent",
                model_name=model_name,
                temperature=temperature,
                status="active",
                capabilities=[
                    "paper_summary",
                    "methodology_explanation",
                    "implementation_guidance",
                    "related_work_comparison",
                    "multi_agent_conversation"
                ]
            )
            
            validated_agent = self.agent_domain.create_agent(agent_create)
            saved_agent = await self.agent_repository.create(validated_agent)
            
            logger.info(f"Successfully created agent for paper: {paper_id}")
            return saved_agent
            
        except Exception as e:
            logger.error(f"Failed to create agent for paper {paper_id}: {e}")
            raise
    
    async def query_agent(
        self,
        agent_id: str,
        query: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Query a paper agent."""
        try:
            logger.info(f"Querying agent {agent_id}: {query}")
            
            # Get agent from database
            agent_config = await self.agent_repository.get_by_id(agent_id)
            if not agent_config:
                raise ValueError(f"Agent {agent_id} not found")
            
            paper_id = agent_config.paper_id
            
            # Get or create active agent
            if paper_id not in self.active_agents:
                await self._load_agent(paper_id, agent_config)
            
            agent = self.active_agents[paper_id]
            
            # Add context to query if provided
            if context:
                contextual_query = f"Context: {context}\n\nQuery: {query}"
            else:
                contextual_query = query
            
            # Query the agent
            response = await agent.query(contextual_query)
            
            # Update agent statistics
            await self.agent_repository.update(agent_id, {
                "query_count": agent_config.query_count + 1,
                "last_query_at": datetime.utcnow()
            })
            
            return {
                "agent_id": agent_id,
                "paper_id": paper_id,
                "query": query,
                "response": response["response"],
                "context": context,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to query agent {agent_id}: {e}")
            raise
    
    async def start_multi_agent_conversation(
        self,
        paper_ids: List[str],
        topic: str,
        conversation_type: str = "collaboration"
    ) -> Dict[str, Any]:
        """Start a multi-agent conversation."""
        try:
            logger.info(f"Starting {conversation_type} conversation: {topic}")
            
            # Validate papers exist and have agents
            for paper_id in paper_ids:
                paper = await self.paper_repository.get_by_id(paper_id)
                if not paper:
                    raise ValueError(f"Paper {paper_id} not found")
                
                # Ensure agent exists
                agent_config = await self.agent_repository.get_by_paper_id(paper_id)
                if not agent_config:
                    # Create agent if it doesn't exist
                    await self.create_paper_agent(paper_id)
                
                # Load agent if not active
                if paper_id not in self.active_agents:
                    await self._load_agent(paper_id, agent_config)
            
            # Convert conversation type
            conv_type = ConversationType(conversation_type.lower())
            
            # Start conversation
            conversation_id = await self.agent_coordinator.start_conversation(
                paper_ids=paper_ids,
                topic=topic,
                conversation_type=conv_type
            )
            
            return {
                "conversation_id": conversation_id,
                "topic": topic,
                "type": conversation_type,
                "participants": paper_ids,
                "status": "active"
            }
            
        except Exception as e:
            logger.error(f"Failed to start multi-agent conversation: {e}")
            raise
    
    async def send_message_to_conversation(
        self,
        conversation_id: str,
        message: str,
        sender_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Send message to multi-agent conversation."""
        try:
            response = await self.agent_coordinator.send_message_to_conversation(
                conversation_id=conversation_id,
                message=message,
                sender_id=sender_id or "user"
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Failed to send message to conversation {conversation_id}: {e}")
            raise
    
    async def get_conversation_summary(self, conversation_id: str) -> Dict[str, Any]:
        """Get conversation summary."""
        try:
            return await self.agent_coordinator.get_conversation_summary(conversation_id)
        except Exception as e:
            logger.error(f"Failed to get conversation summary: {e}")
            raise
    
    async def list_active_agents(self) -> List[Dict[str, Any]]:
        """List all active agents."""
        try:
            # Get from coordinator
            coordinator_agents = await self.agent_coordinator.list_active_agents()
            
            # Get from database
            db_agents = await self.agent_repository.get_all_active()
            
            # Combine information
            agents_info = []
            for db_agent in db_agents:
                agent_info = {
                    "agent_id": db_agent.id,
                    "paper_id": db_agent.paper_id,
                    "model_name": db_agent.model_name,
                    "status": db_agent.status,
                    "query_count": db_agent.query_count,
                    "created_at": db_agent.created_at,
                    "last_query_at": db_agent.last_query_at,
                    "is_active": db_agent.paper_id in self.active_agents
                }
                
                # Add coordinator info if available
                for coord_agent in coordinator_agents:
                    if coord_agent["paper_id"] == db_agent.paper_id:
                        agent_info.update({
                            "conversation_length": coord_agent.get("conversation_length", 0),
                            "has_github_repos": coord_agent.get("has_github_repos", False),
                            "has_methodology": coord_agent.get("has_methodology", False)
                        })
                        break
                
                agents_info.append(agent_info)
            
            return agents_info
            
        except Exception as e:
            logger.error(f"Failed to list active agents: {e}")
            raise
    
    async def deactivate_agent(self, agent_id: str) -> bool:
        """Deactivate an agent."""
        try:
            # Get agent config
            agent_config = await self.agent_repository.get_by_id(agent_id)
            if not agent_config:
                raise ValueError(f"Agent {agent_id} not found")
            
            paper_id = agent_config.paper_id
            
            # Remove from active agents
            if paper_id in self.active_agents:
                del self.active_agents[paper_id]
            
            # Remove from coordinator
            await self.agent_coordinator.remove_agent(paper_id)
            
            # Update database
            await self.agent_repository.update(agent_id, {
                "status": "inactive",
                "deactivated_at": datetime.utcnow()
            })
            
            logger.info(f"Deactivated agent: {agent_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to deactivate agent {agent_id}: {e}")
            raise
    
    async def get_agent_performance(self, agent_id: str) -> Dict[str, Any]:
        """Get agent performance metrics."""
        try:
            agent_config = await self.agent_repository.get_by_id(agent_id)
            if not agent_config:
                raise ValueError(f"Agent {agent_id} not found")
            
            # Calculate performance metrics
            total_queries = agent_config.query_count
            days_active = (datetime.utcnow() - agent_config.created_at).days or 1
            avg_queries_per_day = total_queries / days_active
            
            return {
                "agent_id": agent_id,
                "paper_id": agent_config.paper_id,
                "total_queries": total_queries,
                "days_active": days_active,
                "avg_queries_per_day": round(avg_queries_per_day, 2),
                "last_query_at": agent_config.last_query_at,
                "status": agent_config.status,
                "model_name": agent_config.model_name
            }
            
        except Exception as e:
            logger.error(f"Failed to get agent performance: {e}")
            raise
    
    async def _load_agent(self, paper_id: str, agent_config: Any):
        """Load an agent into active memory."""
        try:
            # Get paper data
            paper = await self.paper_repository.get_by_id(paper_id)
            if not paper:
                raise ValueError(f"Paper {paper_id} not found")
            
            # Prepare paper data
            paper_data = {
                "id": paper.id,
                "title": paper.title,
                "abstract": paper.abstract,
                "full_text": paper.full_text,
                "authors": paper.authors,
                "categories": paper.categories,
                "methodology": paper.methodology or [],
                "github_repos": paper.github_repos or [],
                "key_findings": []
            }
            
            # Create agent
            agent = PaperAgentFactory.create_agent(
                paper_data=paper_data,
                model_name=agent_config.model_name,
                temperature=agent_config.temperature
            )
            
            # Register with coordinator
            await self.agent_coordinator.register_agent(paper_data)
            
            # Cache agent
            self.active_agents[paper_id] = agent
            
            logger.info(f"Loaded agent for paper: {paper_id}")
            
        except Exception as e:
            logger.error(f"Failed to load agent for paper {paper_id}: {e}")
            raise
    
    async def compare_papers(
        self,
        paper_ids: List[str],
        comparison_aspect: str = "methodology"
    ) -> Dict[str, Any]:
        """Compare multiple papers using their agents."""
        try:
            if len(paper_ids) < 2:
                raise ValueError("Need at least 2 papers to compare")
            
            # Start comparison conversation
            conversation_id = await self.start_multi_agent_conversation(
                paper_ids=paper_ids,
                topic=f"Compare {comparison_aspect}",
                conversation_type="comparison"
            )
            
            # Send comparison prompt
            comparison_prompt = f"""
            Please compare your papers focusing on {comparison_aspect}.
            Each agent should:
            1. Describe your paper's approach to {comparison_aspect}
            2. Highlight unique contributions
            3. Identify similarities and differences with other papers
            4. Provide a brief assessment
            """
            
            response = await self.send_message_to_conversation(
                conversation_id=conversation_id,
                message=comparison_prompt
            )
            
            return {
                "comparison_id": conversation_id,
                "papers": paper_ids,
                "aspect": comparison_aspect,
                "responses": response.get("agent_responses", []),
                "status": "completed"
            }
            
        except Exception as e:
            logger.error(f"Failed to compare papers: {e}")
            raise
    
    async def synthesize_knowledge(
        self,
        paper_ids: List[str],
        topic: str
    ) -> Dict[str, Any]:
        """Synthesize knowledge from multiple papers."""
        try:
            # Start synthesis conversation
            conversation_id = await self.start_multi_agent_conversation(
                paper_ids=paper_ids,
                topic=topic,
                conversation_type="synthesis"
            )
            
            # Send synthesis prompt
            synthesis_prompt = f"""
            Let's synthesize knowledge about: {topic}
            
            Please work together to:
            1. Combine insights from all papers
            2. Identify complementary approaches
            3. Build a unified understanding
            4. Suggest future research directions
            
            Focus on creating a comprehensive synthesis.
            """
            
            response = await self.send_message_to_conversation(
                conversation_id=conversation_id,
                message=synthesis_prompt
            )
            
            return {
                "synthesis_id": conversation_id,
                "papers": paper_ids,
                "topic": topic,
                "synthesis": response.get("agent_responses", []),
                "status": "completed"
            }
            
        except Exception as e:
            logger.error(f"Failed to synthesize knowledge: {e}")
            raise