"""Agent service for AI agent management and operations."""

import asyncio
import json
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple
from uuid import uuid4
from sqlalchemy.orm import Session

from ..repositories.agent_repository import AgentRepository, ConversationRepository
from ..domain.agent_domain import AgentDomainService, CollaborationMode
from ..events.base import event_bus
from ..models.agent_models import (
    AgentCreate, AgentUpdate, AgentResponse, AgentQueryRequest, AgentQueryResponse,
    ConversationResponse, MultiAgentRequest, MultiAgentResponse,
    ImplementationGuideRequest, ImplementationGuideResponse, AgentPerformanceMetrics
)
from ..core.logging import LoggerMixin
from ..core.config import settings


class AgentService(LoggerMixin):
    """Service for AI agent management and operations."""
    
    def __init__(self, db: Session):
        self.db = db
        self.agent_repository = AgentRepository(db)
        self.conversation_repository = ConversationRepository(db)
        self.domain_service = AgentDomainService(self.agent_repository, self.conversation_repository)
    
    async def create_agent(self, agent_data: AgentCreate) -> AgentResponse:
        """Create a new AI agent using domain service."""
        try:
            # Use domain service for business logic
            domain_agent = await self.domain_service.create_specialized_agent(
                paper_id=agent_data.paper_id,
                agent_type=agent_data.agent_type,
                specialization=agent_data.specialization or "general",
                model_name=agent_data.model_name
            )
            
            # Get full agent from repository
            agent = await self.agent_repository.get_by_id(domain_agent.id)
            return self._to_response(agent)
            
        except Exception as e:
            self.log_error(e, operation="create_agent")
            raise
    
    async def get_agent(self, agent_id: str) -> Optional[AgentResponse]:
        """Get agent by ID."""
        agent = self.db.query(PaperAgent).filter(PaperAgent.id == agent_id).first()
        if not agent:
            return None
        return self._to_response(agent)
    
    async def list_agents(self, paper_id: Optional[str] = None, agent_type: Optional[str] = None, 
                         status: Optional[str] = None, limit: int = 50, offset: int = 0) -> Tuple[List[AgentResponse], int]:
        """List agents with filtering."""
        query = self.db.query(PaperAgent)
        
        if paper_id:
            query = query.filter(PaperAgent.paper_id == paper_id)
        if agent_type:
            query = query.filter(PaperAgent.agent_type == agent_type)
        if status:
            query = query.filter(PaperAgent.status == status)
        
        total_count = query.count()
        agents = query.offset(offset).limit(limit).all()
        
        return [self._to_response(agent) for agent in agents], total_count
    
    async def update_agent(self, agent_id: str, agent_update: AgentUpdate) -> Optional[AgentResponse]:
        """Update existing agent."""
        agent = self.db.query(PaperAgent).filter(PaperAgent.id == agent_id).first()
        if not agent:
            return None
        
        update_data = agent_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(agent, field, value)
        
        self.db.commit()
        self.db.refresh(agent)
        
        return self._to_response(agent)
    
    async def delete_agent(self, agent_id: str) -> bool:
        """Delete agent."""
        agent = self.db.query(PaperAgent).filter(PaperAgent.id == agent_id).first()
        if not agent:
            return False
        
        self.db.delete(agent)
        self.db.commit()
        return True
    
    async def query_agent(self, agent_id: str, query_request: AgentQueryRequest) -> AgentQueryResponse:
        """Process a query through an AI agent."""
        start_time = datetime.utcnow()
        
        try:
            agent = await self.agent_repository.get_by_id(agent_id)
            if not agent:
                raise ValueError("Agent not found")
            
            # Publish query received event
            await event_bus.publish(
                event_bus.create_event(
                    "agent.query_received",
                    {"agent_id": agent_id, "query": query_request.query},
                    "agent_service"
                )
            )
            
            # Generate session ID if not provided
            session_id = query_request.session_id or str(uuid4())
            
            # Store user message using repository
            user_message_data = {
                "agent_id": agent_id,
                "user_id": query_request.context.get("user_id", "anonymous") if query_request.context else "anonymous",
                "session_id": session_id,
                "message_type": "user",
                "content": query_request.query,
                "context": query_request.context
            }
            await self.conversation_repository.create(user_message_data)
            
            # Process query
            response_content = await self._process_agent_query(agent, query_request)
            response_time = (datetime.utcnow() - start_time).total_seconds()
            
            # Store agent response
            agent_message_data = {
                "agent_id": agent_id,
                "user_id": user_message_data["user_id"],
                "session_id": session_id,
                "message_type": "agent",
                "content": response_content["response"],
                "context": response_content.get("context"),
                "response_time": response_time,
                "token_count": response_content.get("token_count")
            }
            await self.conversation_repository.create(agent_message_data)
            
            # Update agent metrics using repository
            await self.agent_repository.update_interaction_metrics(agent_id, response_time)
            
            # Publish response generated event
            await event_bus.publish(
                event_bus.create_event(
                    "agent.response_generated",
                    {"agent_id": agent_id, "response_time": response_time},
                    "agent_service"
                )
            )
            
            return AgentQueryResponse(
                agent_id=agent_id,
                session_id=session_id,
                response=response_content["response"],
                response_type=response_content.get("response_type", "text"),
                response_time=response_time,
                token_count=response_content.get("token_count"),
                confidence_score=response_content.get("confidence_score"),
                code_examples=response_content.get("code_examples"),
                references=response_content.get("references"),
                follow_up_suggestions=response_content.get("follow_up_suggestions"),
                updated_context=response_content.get("updated_context")
            )
            
        except Exception as e:
            self.log_error(e, operation="query_agent", agent_id=agent_id)
            raise
    
    async def multi_agent_collaboration(self, request: MultiAgentRequest) -> MultiAgentResponse:
        """Coordinate multi-agent collaboration using domain service."""
        start_time = datetime.utcnow()
        
        try:
            # Use domain service for collaboration orchestration
            collaboration_mode = CollaborationMode(request.collaboration_mode)
            collaboration_result = await self.domain_service.orchestrate_collaboration(
                agent_ids=request.agent_ids,
                task=request.task,
                mode=collaboration_mode
            )
            
            # Process actual collaboration (simplified for now)
            result = await self._process_collaboration(request, collaboration_mode)
            
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            # Publish completion event
            await event_bus.publish(
                event_bus.create_event(
                    "agent.collaboration_completed",
                    {
                        "collaboration_id": collaboration_result["collaboration_id"],
                        "processing_time": processing_time
                    },
                    "agent_service"
                )
            )
            
            return MultiAgentResponse(
                collaboration_id=collaboration_result["collaboration_id"],
                task=request.task,
                participating_agents=request.agent_ids,
                synthesized_response=result["synthesized_response"],
                individual_responses=result["individual_responses"],
                consensus_score=result.get("consensus_score"),
                total_iterations=result.get("iterations", 1),
                processing_time=processing_time,
                collaboration_quality=result.get("quality_score"),
                key_agreements=result.get("agreements", []),
                key_disagreements=result.get("disagreements", [])
            )
            
        except Exception as e:
            self.log_error(e, operation="multi_agent_collaboration")
            raise
    
    async def generate_implementation_guide(self, agent_id: str, request: ImplementationGuideRequest) -> ImplementationGuideResponse:
        """Generate implementation guide for a paper."""
        agent = self.db.query(PaperAgent).filter(PaperAgent.id == agent_id).first()
        if not agent:
            raise ValueError("Agent not found")
        
        paper = agent.paper
        guide_id = str(uuid4())
        
        # Generate guide content (placeholder)
        guide_content = await self._generate_guide_content(paper, request)
        
        return ImplementationGuideResponse(
            guide_id=guide_id,
            paper_id=paper.id,
            agent_id=agent_id,
            framework=request.framework,
            complexity_level=request.complexity_level,
            steps=guide_content["steps"],
            code_examples=guide_content["code_examples"],
            requirements=guide_content["requirements"],
            estimated_time=guide_content["estimated_time"],
            github_repos_analyzed=paper.github_repos or [],
            reference_implementations=guide_content.get("reference_implementations", [])
        )
    
    async def get_conversations(self, agent_id: str, user_id: Optional[str] = None, 
                              limit: int = 50, offset: int = 0) -> Tuple[List[ConversationResponse], int]:
        """Get conversation history for an agent."""
        query = self.db.query(AgentConversation).filter(AgentConversation.agent_id == agent_id)
        
        if user_id:
            query = query.filter(AgentConversation.user_id == user_id)
        
        total_count = query.count()
        
        # Group by session_id
        conversations = {}
        messages = query.order_by(AgentConversation.created_at).offset(offset).limit(limit).all()
        
        for message in messages:
            session_id = message.session_id
            if session_id not in conversations:
                conversations[session_id] = {
                    "session_id": session_id,
                    "agent_id": agent_id,
                    "user_id": message.user_id,
                    "messages": [],
                    "started_at": message.created_at,
                    "last_message_at": message.created_at
                }
            
            conversations[session_id]["messages"].append({
                "id": message.id,
                "message_type": message.message_type,
                "content": message.content,
                "timestamp": message.created_at,
                "response_time": message.response_time,
                "user_rating": message.user_rating,
                "user_feedback": message.user_feedback
            })
            
            if message.created_at > conversations[session_id]["last_message_at"]:
                conversations[session_id]["last_message_at"] = message.created_at
        
        conversation_responses = [
            ConversationResponse(**conv_data) for conv_data in conversations.values()
        ]
        
        return conversation_responses, total_count
    
    async def get_performance_metrics(self, agent_id: str, time_period: str) -> Optional[AgentPerformanceMetrics]:
        """Get performance metrics for an agent."""
        agent = self.db.query(PaperAgent).filter(PaperAgent.id == agent_id).first()
        if not agent:
            return None
        
        # Calculate date threshold
        if time_period == "24h":
            threshold = datetime.utcnow() - timedelta(hours=24)
        elif time_period == "7d":
            threshold = datetime.utcnow() - timedelta(days=7)
        else:  # 30d
            threshold = datetime.utcnow() - timedelta(days=30)
        
        # Query conversations in time period
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
        
        return AgentPerformanceMetrics(
            agent_id=agent_id,
            time_period=time_period,
            total_queries=total_queries,
            successful_queries=successful_queries,
            failed_queries=failed_queries,
            average_response_time=avg_response_time,
            average_user_rating=avg_rating,
            user_satisfaction_rate=avg_rating / 5.0 if avg_rating else None
        )
    
    async def submit_feedback(self, agent_id: str, session_id: str, rating: int, feedback: Optional[str] = None) -> bool:
        """Submit feedback for an agent interaction."""
        # Find the latest agent message in the session
        message = self.db.query(AgentConversation).filter(
            and_(
                AgentConversation.agent_id == agent_id,
                AgentConversation.session_id == session_id,
                AgentConversation.message_type == "agent"
            )
        ).order_by(desc(AgentConversation.created_at)).first()
        
        if not message:
            return False
        
        message.user_rating = rating
        message.user_feedback = feedback
        
        # Update agent's average rating
        agent = self.db.query(PaperAgent).filter(PaperAgent.id == agent_id).first()
        if agent:
            ratings = self.db.query(AgentConversation.user_rating).filter(
                and_(
                    AgentConversation.agent_id == agent_id,
                    AgentConversation.user_rating.isnot(None)
                )
            ).all()
            
            if ratings:
                agent.user_rating_avg = sum(r[0] for r in ratings) / len(ratings)
        
        self.db.commit()
        return True
    
    async def initialize_agent_async(self, agent_id: str):
        """Background task to initialize agent."""
        try:
            agent = self.db.query(PaperAgent).filter(PaperAgent.id == agent_id).first()
            if not agent:
                return
            
            # Initialize agent context with paper data
            paper = agent.paper
            context_data = {
                "paper_title": paper.title,
                "paper_abstract": paper.abstract,
                "paper_categories": paper.categories,
                "paper_authors": paper.authors,
                "initialization_date": datetime.utcnow().isoformat()
            }
            
            agent.context_data = context_data
            agent.status = "active"
            self.db.commit()
            
            self.log_event("agent_initialized", agent_id=agent_id)
            
        except Exception as e:
            self.log_error(e, operation="initialize_agent", agent_id=agent_id)
    
    def _to_response(self, agent: PaperAgent) -> AgentResponse:
        """Convert PaperAgent model to response."""
        return AgentResponse(
            id=agent.id,
            paper_id=agent.paper_id,
            agent_type=agent.agent_type,
            model_name=agent.model_name,
            specialization=agent.specialization,
            status=agent.status,
            conversation_count=agent.conversation_count,
            last_interaction=agent.last_interaction,
            response_time_avg=agent.response_time_avg,
            user_rating_avg=agent.user_rating_avg,
            success_rate=agent.success_rate,
            memory_size=agent.memory_size,
            capabilities=agent.capabilities,
            created_at=agent.created_at,
            updated_at=agent.updated_at
        )
    
    def _get_default_capabilities(self, agent_type: str) -> List[str]:
        """Get default capabilities for agent type."""
        capabilities_map = {
            "interactive": ["question_answering", "explanation", "discussion"],
            "implementation": ["code_generation", "tutorial_creation", "debugging"],
            "analysis": ["methodology_analysis", "impact_assessment", "comparison"],
            "collaboration": ["multi_agent_coordination", "consensus_building", "synthesis"]
        }
        return capabilities_map.get(agent_type, ["general_assistance"])
    
    async def _process_agent_query(self, agent, query_request: AgentQueryRequest) -> Dict[str, Any]:
        """Process query through AI model (placeholder)."""
        # This would integrate with actual AI models (OpenAI, Anthropic, etc.)
        paper = agent.paper
        
        response = f"Based on the paper '{paper.title}', here's my response to your query: {query_request.query[:100]}..."
        
        return {
            "response": response,
            "response_type": "text",
            "token_count": len(response.split()),
            "confidence_score": 0.85,
            "references": [paper.title],
            "follow_up_suggestions": [
                "Can you explain the methodology in more detail?",
                "How does this compare to other approaches?",
                "What are the practical applications?"
            ]
        }
    
    async def _process_collaboration(self, request: MultiAgentRequest, mode: CollaborationMode) -> Dict[str, Any]:
        """Process collaboration based on mode."""
        # Get agents from repository
        agents = []
        for agent_id in request.agent_ids:
            agent = await self.agent_repository.get_by_id(agent_id)
            if agent:
                agents.append(agent)
        
        if mode == CollaborationMode.SEQUENTIAL:
            return await self._sequential_collaboration(agents, request)
        elif mode == CollaborationMode.PARALLEL:
            return await self._parallel_collaboration(agents, request)
        else:
            return await self._consensus_collaboration(agents, request)
    
    async def _sequential_collaboration(self, agents, request: MultiAgentRequest) -> Dict[str, Any]:
        """Sequential collaboration between agents."""
        responses = {}
        current_context = request.task
        
        for agent in agents:
            query_req = AgentQueryRequest(query=current_context)
            response = await self._process_agent_query(agent, query_req)
            responses[agent.id] = response["response"]
            current_context = f"{current_context}\n\nPrevious agent response: {response['response']}"
        
        synthesized = f"Synthesized response from {len(agents)} agents: " + " ".join(responses.values())[:500]
        
        return {
            "synthesized_response": synthesized,
            "individual_responses": responses,
            "consensus_score": 0.8,
            "iterations": 1
        }
    
    async def _parallel_collaboration(self, agents, request: MultiAgentRequest) -> Dict[str, Any]:
        """Parallel collaboration between agents."""
        tasks = []
        for agent in agents:
            query_req = AgentQueryRequest(query=request.task)
            tasks.append(self._process_agent_query(agent, query_req))
        
        results = await asyncio.gather(*tasks)
        responses = {agents[i].id: results[i]["response"] for i in range(len(agents))}
        
        synthesized = f"Combined insights from {len(agents)} agents: " + " ".join(responses.values())[:500]
        
        return {
            "synthesized_response": synthesized,
            "individual_responses": responses,
            "consensus_score": 0.75,
            "iterations": 1
        }
    
    async def _consensus_collaboration(self, agents, request: MultiAgentRequest) -> Dict[str, Any]:
        """Consensus-building collaboration between agents."""
        # Simplified consensus mechanism
        return await self._parallel_collaboration(agents, request)
    
    async def _generate_guide_content(self, paper: Paper, request: ImplementationGuideRequest) -> Dict[str, Any]:
        """Generate implementation guide content."""
        return {
            "steps": [
                {"step": 1, "title": "Setup Environment", "description": f"Install {request.framework} and dependencies"},
                {"step": 2, "title": "Load Data", "description": "Prepare your dataset"},
                {"step": 3, "title": "Implement Model", "description": f"Implement the model from {paper.title}"},
                {"step": 4, "title": "Train Model", "description": "Train the model with your data"},
                {"step": 5, "title": "Evaluate Results", "description": "Evaluate model performance"}
            ],
            "code_examples": [
                {"language": "python", "code": f"import {request.framework}\n# Implementation code here"},
                {"language": "python", "code": "# Training loop\nfor epoch in range(num_epochs):\n    # training code"}
            ],
            "requirements": [f"{request.framework}>=1.0", "numpy", "matplotlib"],
            "estimated_time": 180  # minutes
        }