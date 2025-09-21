"""AI Agent management endpoints."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from ....database.connection import get_db_session
from ....models.agent_models import (
    AgentCreate, AgentUpdate, AgentResponse, AgentQueryRequest, AgentQueryResponse,
    ConversationResponse, MultiAgentRequest, MultiAgentResponse,
    ImplementationGuideRequest, ImplementationGuideResponse
)
from ....models.common_models import PaginationParams, PaginatedResponse
from ....services.agent_service import AgentService
from ....services.websocket_service import WebSocketManager
from ....core.logging import get_logger

router = APIRouter()
logger = get_logger(__name__)
websocket_manager = WebSocketManager()


@router.post("/", response_model=AgentResponse, status_code=201)
async def create_agent(
    agent_data: AgentCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db_session)
):
    """Create a new AI agent for a research paper."""
    try:
        agent_service = AgentService(db)
        agent = await agent_service.create_agent(agent_data)
        
        # Schedule agent initialization in background
        background_tasks.add_task(agent_service.initialize_agent_async, agent.id)
        
        logger.info("agent_created", agent_id=agent.id, paper_id=agent.paper_id, agent_type=agent.agent_type)
        return agent
    except Exception as e:
        logger.error("agent_creation_failed", error=str(e))
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/", response_model=PaginatedResponse[AgentResponse])
async def list_agents(
    paper_id: Optional[str] = None,
    agent_type: Optional[str] = None,
    status: Optional[str] = None,
    pagination: PaginationParams = Depends(),
    db: Session = Depends(get_db_session)
):
    """List AI agents with optional filtering."""
    try:
        agent_service = AgentService(db)
        agents, total_count = await agent_service.list_agents(
            paper_id=paper_id,
            agent_type=agent_type,
            status=status,
            limit=pagination.limit,
            offset=pagination.offset
        )
        
        return PaginatedResponse.create(
            items=agents,
            total_count=total_count,
            pagination=pagination
        )
    except Exception as e:
        logger.error("agent_listing_failed", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(
    agent_id: str,
    db: Session = Depends(get_db_session)
):
    """Get a specific agent by ID."""
    try:
        agent_service = AgentService(db)
        agent = await agent_service.get_agent(agent_id)
        
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        return agent
    except HTTPException:
        raise
    except Exception as e:
        logger.error("agent_retrieval_failed", agent_id=agent_id, error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/{agent_id}", response_model=AgentResponse)
async def update_agent(
    agent_id: str,
    agent_update: AgentUpdate,
    db: Session = Depends(get_db_session)
):
    """Update an existing agent."""
    try:
        agent_service = AgentService(db)
        agent = await agent_service.update_agent(agent_id, agent_update)
        
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        logger.info("agent_updated", agent_id=agent_id)
        return agent
    except HTTPException:
        raise
    except Exception as e:
        logger.error("agent_update_failed", agent_id=agent_id, error=str(e))
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{agent_id}", status_code=204)
async def delete_agent(
    agent_id: str,
    db: Session = Depends(get_db_session)
):
    """Delete an agent."""
    try:
        agent_service = AgentService(db)
        success = await agent_service.delete_agent(agent_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        logger.info("agent_deleted", agent_id=agent_id)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("agent_deletion_failed", agent_id=agent_id, error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/{agent_id}/query", response_model=AgentQueryResponse)
async def query_agent(
    agent_id: str,
    query_request: AgentQueryRequest,
    db: Session = Depends(get_db_session)
):
    """Query an AI agent with a question or request."""
    try:
        agent_service = AgentService(db)
        
        # Check if agent exists and is active
        agent = await agent_service.get_agent(agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        if agent.status != "active":
            raise HTTPException(status_code=400, detail=f"Agent is not active (status: {agent.status})")
        
        # Process query
        response = await agent_service.query_agent(agent_id, query_request)
        
        logger.info("agent_query_processed", agent_id=agent_id, query_length=len(query_request.query))
        return response
    except HTTPException:
        raise
    except Exception as e:
        logger.error("agent_query_failed", agent_id=agent_id, error=str(e))
        raise HTTPException(status_code=500, detail="Agent query failed")


@router.get("/{agent_id}/conversations", response_model=PaginatedResponse[ConversationResponse])
async def get_agent_conversations(
    agent_id: str,
    user_id: Optional[str] = None,
    pagination: PaginationParams = Depends(),
    db: Session = Depends(get_db_session)
):
    """Get conversation history for an agent."""
    try:
        agent_service = AgentService(db)
        conversations, total_count = await agent_service.get_conversations(
            agent_id=agent_id,
            user_id=user_id,
            limit=pagination.limit,
            offset=pagination.offset
        )
        
        return PaginatedResponse.create(
            items=conversations,
            total_count=total_count,
            pagination=pagination
        )
    except Exception as e:
        logger.error("conversation_retrieval_failed", agent_id=agent_id, error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/{agent_id}/implementation-guide", response_model=ImplementationGuideResponse)
async def generate_implementation_guide(
    agent_id: str,
    guide_request: ImplementationGuideRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db_session)
):
    """Generate step-by-step implementation guide for a paper."""
    try:
        agent_service = AgentService(db)
        
        # Check if agent exists
        agent = await agent_service.get_agent(agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        # Generate implementation guide
        guide = await agent_service.generate_implementation_guide(agent_id, guide_request)
        
        logger.info("implementation_guide_generated", agent_id=agent_id, framework=guide_request.framework)
        return guide
    except HTTPException:
        raise
    except Exception as e:
        logger.error("implementation_guide_failed", agent_id=agent_id, error=str(e))
        raise HTTPException(status_code=500, detail="Implementation guide generation failed")


@router.post("/multi-agent/collaborate", response_model=MultiAgentResponse)
async def multi_agent_collaboration(
    collaboration_request: MultiAgentRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db_session)
):
    """Initiate multi-agent collaboration for complex queries."""
    try:
        agent_service = AgentService(db)
        
        # Validate all agents exist and are active
        for agent_id in collaboration_request.agent_ids:
            agent = await agent_service.get_agent(agent_id)
            if not agent:
                raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
            if agent.status != "active":
                raise HTTPException(status_code=400, detail=f"Agent {agent_id} is not active")
        
        # Start collaboration
        collaboration_result = await agent_service.multi_agent_collaboration(collaboration_request)
        
        logger.info("multi_agent_collaboration_started", 
                   agent_count=len(collaboration_request.agent_ids),
                   task=collaboration_request.task)
        return collaboration_result
    except HTTPException:
        raise
    except Exception as e:
        logger.error("multi_agent_collaboration_failed", error=str(e))
        raise HTTPException(status_code=500, detail="Multi-agent collaboration failed")


@router.websocket("/{agent_id}/chat")
async def agent_chat_websocket(
    websocket: WebSocket,
    agent_id: str,
    user_id: str,
    db: Session = Depends(get_db_session)
):
    """WebSocket endpoint for real-time chat with an agent."""
    await websocket.accept()
    
    try:
        # Validate agent exists
        agent_service = AgentService(db)
        agent = await agent_service.get_agent(agent_id)
        if not agent:
            await websocket.close(code=4004, reason="Agent not found")
            return
        
        # Add connection to manager
        await websocket_manager.connect(websocket, f"agent_{agent_id}_{user_id}")
        
        logger.info("websocket_connected", agent_id=agent_id, user_id=user_id)
        
        while True:
            # Receive message from client
            data = await websocket.receive_json()
            
            # Process query through agent
            query_request = AgentQueryRequest(**data)
            response = await agent_service.query_agent(agent_id, query_request)
            
            # Send response back to client
            await websocket.send_json({
                "type": "agent_response",
                "data": response.dict(),
                "timestamp": response.created_at.isoformat()
            })
            
    except WebSocketDisconnect:
        logger.info("websocket_disconnected", agent_id=agent_id, user_id=user_id)
        websocket_manager.disconnect(websocket)
    except Exception as e:
        logger.error("websocket_error", agent_id=agent_id, user_id=user_id, error=str(e))
        await websocket.close(code=4000, reason="Internal server error")


@router.get("/{agent_id}/performance")
async def get_agent_performance(
    agent_id: str,
    time_period: str = "7d",
    db: Session = Depends(get_db_session)
):
    """Get performance metrics for an agent."""
    try:
        agent_service = AgentService(db)
        metrics = await agent_service.get_performance_metrics(agent_id, time_period)
        
        if not metrics:
            raise HTTPException(status_code=404, detail="Agent not found or no metrics available")
        
        return metrics
    except HTTPException:
        raise
    except Exception as e:
        logger.error("agent_performance_failed", agent_id=agent_id, error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/{agent_id}/feedback")
async def submit_agent_feedback(
    agent_id: str,
    session_id: str,
    rating: int,
    feedback: Optional[str] = None,
    db: Session = Depends(get_db_session)
):
    """Submit feedback for an agent interaction."""
    try:
        if not 1 <= rating <= 5:
            raise HTTPException(status_code=400, detail="Rating must be between 1 and 5")
        
        agent_service = AgentService(db)
        success = await agent_service.submit_feedback(agent_id, session_id, rating, feedback)
        
        if not success:
            raise HTTPException(status_code=404, detail="Agent or session not found")
        
        logger.info("agent_feedback_submitted", agent_id=agent_id, session_id=session_id, rating=rating)
        return {"message": "Feedback submitted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("agent_feedback_failed", agent_id=agent_id, error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")