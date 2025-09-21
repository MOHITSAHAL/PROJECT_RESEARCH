"""Multi-agent coordinator for paper agent collaboration."""

import asyncio
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass
from enum import Enum
import structlog

from ..agents.paper_agent import PaperAgent, PaperAgentFactory

logger = structlog.get_logger()


class ConversationType(Enum):
    """Types of multi-agent conversations."""
    COMPARISON = "comparison"
    SYNTHESIS = "synthesis"
    DEBATE = "debate"
    COLLABORATION = "collaboration"


@dataclass
class AgentConversation:
    """Multi-agent conversation context."""
    conversation_id: str
    conversation_type: ConversationType
    participating_agents: List[str]  # paper_ids
    topic: str
    messages: List[Dict[str, Any]]
    status: str = "active"


class AgentCoordinator:
    """Coordinates multi-agent conversations between paper agents."""
    
    def __init__(self):
        self.active_agents: Dict[str, PaperAgent] = {}
        self.conversations: Dict[str, AgentConversation] = {}
        self.agent_relationships: Dict[str, Set[str]] = {}  # paper_id -> related paper_ids
    
    async def register_agent(self, paper_data: Dict[str, Any]) -> str:
        """Register a new paper agent."""
        try:
            paper_id = paper_data["id"]
            
            if paper_id in self.active_agents:
                logger.info(f"Agent {paper_id} already registered")
                return paper_id
            
            # Create agent
            agent = PaperAgentFactory.create_agent(paper_data)
            self.active_agents[paper_id] = agent
            
            # Initialize relationships
            self.agent_relationships[paper_id] = set()
            
            logger.info(f"Registered agent for paper: {paper_id}")
            return paper_id
            
        except Exception as e:
            logger.error(f"Failed to register agent: {e}")
            raise
    
    async def start_conversation(
        self,
        paper_ids: List[str],
        topic: str,
        conversation_type: ConversationType = ConversationType.COLLABORATION
    ) -> str:
        """Start a multi-agent conversation."""
        try:
            # Validate agents exist
            missing_agents = [pid for pid in paper_ids if pid not in self.active_agents]
            if missing_agents:
                raise ValueError(f"Agents not found: {missing_agents}")
            
            # Create conversation
            conversation_id = f"conv_{len(self.conversations)}_{topic[:20]}"
            conversation = AgentConversation(
                conversation_id=conversation_id,
                conversation_type=conversation_type,
                participating_agents=paper_ids,
                topic=topic,
                messages=[]
            )
            
            self.conversations[conversation_id] = conversation
            
            # Initialize conversation
            await self._initialize_conversation(conversation)
            
            logger.info(f"Started {conversation_type.value} conversation: {conversation_id}")
            return conversation_id
            
        except Exception as e:
            logger.error(f"Failed to start conversation: {e}")
            raise
    
    async def _initialize_conversation(self, conversation: AgentConversation):
        """Initialize a multi-agent conversation."""
        
        if conversation.conversation_type == ConversationType.COMPARISON:
            await self._start_comparison_conversation(conversation)
        elif conversation.conversation_type == ConversationType.SYNTHESIS:
            await self._start_synthesis_conversation(conversation)
        elif conversation.conversation_type == ConversationType.DEBATE:
            await self._start_debate_conversation(conversation)
        else:  # COLLABORATION
            await self._start_collaboration_conversation(conversation)
    
    async def _start_comparison_conversation(self, conversation: AgentConversation):
        """Start a comparison conversation between papers."""
        
        # Get paper titles for context
        paper_titles = []
        for paper_id in conversation.participating_agents:
            agent = self.active_agents[paper_id]
            paper_titles.append(f"{paper_id}: {agent.paper_context.title}")
        
        # Initial prompt for comparison
        comparison_prompt = f"""
        Let's compare these research papers on the topic: {conversation.topic}
        
        Papers to compare:
        {chr(10).join(paper_titles)}
        
        Each agent should:
        1. Briefly describe your paper's approach to {conversation.topic}
        2. Highlight your key contributions
        3. Identify similarities and differences with other papers
        
        Let's start with the first paper.
        """
        
        # Add initial message
        conversation.messages.append({
            "type": "system",
            "content": comparison_prompt,
            "timestamp": asyncio.get_event_loop().time()
        })
    
    async def _start_synthesis_conversation(self, conversation: AgentConversation):
        """Start a synthesis conversation to combine insights."""
        
        synthesis_prompt = f"""
        Let's synthesize knowledge about: {conversation.topic}
        
        Each agent should contribute their paper's insights to build a comprehensive understanding.
        Focus on:
        1. Complementary approaches and methods
        2. Combined insights and findings
        3. Unified perspective on the topic
        4. Future research directions
        
        Work together to create a synthesis of knowledge.
        """
        
        conversation.messages.append({
            "type": "system",
            "content": synthesis_prompt,
            "timestamp": asyncio.get_event_loop().time()
        })
    
    async def _start_debate_conversation(self, conversation: AgentConversation):
        """Start a debate conversation between different approaches."""
        
        debate_prompt = f"""
        Let's have a scholarly debate about: {conversation.topic}
        
        Each agent should:
        1. Present your paper's position/approach
        2. Argue for the strengths of your method
        3. Respectfully challenge other approaches
        4. Respond to critiques with evidence
        
        Keep the debate constructive and evidence-based.
        """
        
        conversation.messages.append({
            "type": "system",
            "content": debate_prompt,
            "timestamp": asyncio.get_event_loop().time()
        })
    
    async def _start_collaboration_conversation(self, conversation: AgentConversation):
        """Start a collaborative conversation."""
        
        collaboration_prompt = f"""
        Let's collaborate on understanding: {conversation.topic}
        
        Each agent can:
        1. Share relevant insights from your paper
        2. Ask questions about other papers
        3. Build on each other's contributions
        4. Explore connections between papers
        
        Work together to provide comprehensive insights.
        """
        
        conversation.messages.append({
            "type": "system",
            "content": collaboration_prompt,
            "timestamp": asyncio.get_event_loop().time()
        })
    
    async def send_message_to_conversation(
        self,
        conversation_id: str,
        message: str,
        sender_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Send a message to a multi-agent conversation."""
        try:
            if conversation_id not in self.conversations:
                raise ValueError(f"Conversation {conversation_id} not found")
            
            conversation = self.conversations[conversation_id]
            
            if sender_id == "user":
                # User message to all agents
                return await self._handle_user_message(conversation, message)
            elif sender_id in conversation.participating_agents:
                # Agent-to-agent message
                return await self._handle_agent_message(conversation, message, sender_id)
            else:
                # Broadcast to all agents
                return await self._handle_broadcast_message(conversation, message)
                
        except Exception as e:
            logger.error(f"Failed to send message to conversation: {e}")
            raise
    
    async def _handle_user_message(
        self,
        conversation: AgentConversation,
        message: str
    ) -> Dict[str, Any]:
        """Handle user message in multi-agent conversation."""
        
        # Add user message to conversation
        conversation.messages.append({
            "type": "user",
            "content": message,
            "timestamp": asyncio.get_event_loop().time()
        })
        
        # Get responses from all participating agents
        responses = []
        for paper_id in conversation.participating_agents:
            agent = self.active_agents[paper_id]
            
            # Create context-aware prompt
            context_prompt = f"""
            In our multi-agent conversation about '{conversation.topic}', 
            a user asked: {message}
            
            Please respond from the perspective of your paper: {agent.paper_context.title}
            Consider the ongoing conversation context.
            """
            
            try:
                response = await agent.query(context_prompt)
                responses.append({
                    "agent_id": paper_id,
                    "paper_title": agent.paper_context.title,
                    "response": response["response"]
                })
                
                # Add agent response to conversation
                conversation.messages.append({
                    "type": "agent",
                    "agent_id": paper_id,
                    "content": response["response"],
                    "timestamp": asyncio.get_event_loop().time()
                })
                
            except Exception as e:
                logger.error(f"Agent {paper_id} failed to respond: {e}")
                responses.append({
                    "agent_id": paper_id,
                    "error": str(e)
                })
        
        return {
            "conversation_id": conversation.conversation_id,
            "user_message": message,
            "agent_responses": responses,
            "conversation_type": conversation.conversation_type.value
        }
    
    async def _handle_agent_message(
        self,
        conversation: AgentConversation,
        message: str,
        sender_id: str
    ) -> Dict[str, Any]:
        """Handle agent-to-agent message."""
        
        sender_agent = self.active_agents[sender_id]
        
        # Add sender message to conversation
        conversation.messages.append({
            "type": "agent",
            "agent_id": sender_id,
            "content": message,
            "timestamp": asyncio.get_event_loop().time()
        })
        
        # Get responses from other agents
        responses = []
        other_agents = [pid for pid in conversation.participating_agents if pid != sender_id]
        
        for paper_id in other_agents:
            agent = self.active_agents[paper_id]
            
            context_prompt = f"""
            In our conversation about '{conversation.topic}', 
            the paper '{sender_agent.paper_context.title}' said:
            
            {message}
            
            Please respond from the perspective of your paper: {agent.paper_context.title}
            """
            
            try:
                response = await agent.query(context_prompt)
                responses.append({
                    "agent_id": paper_id,
                    "paper_title": agent.paper_context.title,
                    "response": response["response"]
                })
                
                # Add response to conversation
                conversation.messages.append({
                    "type": "agent",
                    "agent_id": paper_id,
                    "content": response["response"],
                    "timestamp": asyncio.get_event_loop().time()
                })
                
            except Exception as e:
                logger.error(f"Agent {paper_id} failed to respond: {e}")
        
        return {
            "conversation_id": conversation.conversation_id,
            "sender": {
                "agent_id": sender_id,
                "paper_title": sender_agent.paper_context.title
            },
            "message": message,
            "responses": responses
        }
    
    async def _handle_broadcast_message(
        self,
        conversation: AgentConversation,
        message: str
    ) -> Dict[str, Any]:
        """Handle broadcast message to all agents."""
        return await self._handle_user_message(conversation, message)
    
    async def get_conversation_summary(self, conversation_id: str) -> Dict[str, Any]:
        """Get a summary of the conversation."""
        if conversation_id not in self.conversations:
            raise ValueError(f"Conversation {conversation_id} not found")
        
        conversation = self.conversations[conversation_id]
        
        # Get participating paper titles
        paper_info = []
        for paper_id in conversation.participating_agents:
            if paper_id in self.active_agents:
                agent = self.active_agents[paper_id]
                paper_info.append({
                    "paper_id": paper_id,
                    "title": agent.paper_context.title,
                    "authors": agent.paper_context.authors
                })
        
        return {
            "conversation_id": conversation_id,
            "topic": conversation.topic,
            "type": conversation.conversation_type.value,
            "status": conversation.status,
            "participating_papers": paper_info,
            "message_count": len(conversation.messages),
            "messages": conversation.messages[-10:]  # Last 10 messages
        }
    
    async def list_active_agents(self) -> List[Dict[str, Any]]:
        """List all active agents."""
        agents_info = []
        for paper_id, agent in self.active_agents.items():
            agents_info.append(agent.get_agent_info())
        return agents_info
    
    async def get_agent_relationships(self, paper_id: str) -> Dict[str, Any]:
        """Get relationships for a specific agent."""
        if paper_id not in self.active_agents:
            raise ValueError(f"Agent {paper_id} not found")
        
        related_papers = list(self.agent_relationships.get(paper_id, set()))
        
        return {
            "paper_id": paper_id,
            "related_papers": related_papers,
            "relationship_count": len(related_papers)
        }
    
    async def shutdown_conversation(self, conversation_id: str):
        """Shutdown a conversation."""
        if conversation_id in self.conversations:
            self.conversations[conversation_id].status = "completed"
            logger.info(f"Conversation {conversation_id} completed")
    
    async def remove_agent(self, paper_id: str):
        """Remove an agent from the coordinator."""
        if paper_id in self.active_agents:
            del self.active_agents[paper_id]
            if paper_id in self.agent_relationships:
                del self.agent_relationships[paper_id]
            logger.info(f"Removed agent: {paper_id}")