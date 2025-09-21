"""API endpoints for AI agent operations."""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import structlog

from ....core.dependencies import get_ai_agent_service
from ....services.ai_agent_service import AIAgentService
from ....models.agent_models import AgentResponse

logger = structlog.get_logger()

router = APIRouter(prefix="/ai-agents", tags=["ai-agents"])


class CreateAgentRequest(BaseModel):
    """Request model for creating an agent."""
    paper_id: str
    model_name: str = "gpt-3.5-turbo"
    temperature: float = 0.1


class QueryAgentRequest(BaseModel):
    """Request model for querying an agent."""
    query: str
    context: Optional[Dict[str, Any]] = None


class StartConversationRequest(BaseModel):
    """Request model for starting multi-agent conversation."""
    paper_ids: List[str]
    topic: str
    conversation_type: str = "collaboration"


class ConversationMessageRequest(BaseModel):
    """Request model for sending message to conversation."""
    message: str
    sender_id: Optional[str] = None


class CompareRequest(BaseModel):
    """Request model for paper comparison."""
    paper_ids: List[str]
    comparison_aspect: str = "methodology"


class SynthesizeRequest(BaseModel):
    """Request model for knowledge synthesis."""
    paper_ids: List[str]
    topic: str


@router.post("/create", response_model=AgentResponse)
async def create_agent(
    request: CreateAgentRequest,
    background_tasks: BackgroundTasks,
    ai_service: AIAgentService = Depends(get_ai_agent_service)
):
    """
    Create an AI agent for a research paper.
    
    This endpoint creates an interactive AI agent that can:
    - Answer questions about the paper
    - Explain methodology and implementation
    - Participate in multi-agent conversations
    - Provide step-by-step guidance
    """
    try:
        logger.info(f"Creating agent for paper: {request.paper_id}")
        
        agent = await ai_service.create_paper_agent(
            paper_id=request.paper_id,
            model_name=request.model_name,
            temperature=request.temperature
        )
        
        return agent
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to create agent: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{agent_id}/query")
async def query_agent(
    agent_id: str,
    request: QueryAgentRequest,
    ai_service: AIAgentService = Depends(get_ai_agent_service)
) -> Dict[str, Any]:
    """
    Query a paper agent with a question.
    
    The agent will use its knowledge of the paper to provide
    detailed answers about methodology, results, implementation, etc.
    """
    try:
        logger.info(f"Querying agent {agent_id}: {request.query}")
        
        response = await ai_service.query_agent(
            agent_id=agent_id,
            query=request.query,
            context=request.context
        )
        
        return response
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to query agent: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/conversations/start")
async def start_conversation(
    request: StartConversationRequest,
    ai_service: AIAgentService = Depends(get_ai_agent_service)
) -> Dict[str, Any]:
    """
    Start a multi-agent conversation between paper agents.
    
    Conversation types:
    - collaboration: Agents work together to answer questions
    - comparison: Agents compare their papers' approaches
    - synthesis: Agents synthesize knowledge across papers
    - debate: Agents debate different approaches
    """
    try:
        logger.info(f"Starting {request.conversation_type} conversation: {request.topic}")
        
        conversation = await ai_service.start_multi_agent_conversation(
            paper_ids=request.paper_ids,
            topic=request.topic,
            conversation_type=request.conversation_type
        )
        
        return conversation
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to start conversation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/conversations/{conversation_id}/message")
async def send_message_to_conversation(
    conversation_id: str,
    request: ConversationMessageRequest,
    ai_service: AIAgentService = Depends(get_ai_agent_service)
) -> Dict[str, Any]:
    """
    Send a message to an active multi-agent conversation.
    
    All participating agents will respond to the message
    from their paper's perspective.
    """
    try:
        response = await ai_service.send_message_to_conversation(
            conversation_id=conversation_id,
            message=request.message,
            sender_id=request.sender_id
        )
        
        return response
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to send message: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/conversations/{conversation_id}/summary")
async def get_conversation_summary(
    conversation_id: str,
    ai_service: AIAgentService = Depends(get_ai_agent_service)
) -> Dict[str, Any]:
    """
    Get a summary of a multi-agent conversation.
    
    Returns conversation details, participants, and recent messages.
    """
    try:
        summary = await ai_service.get_conversation_summary(conversation_id)
        return summary
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to get conversation summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/compare")
async def compare_papers(
    request: CompareRequest,
    ai_service: AIAgentService = Depends(get_ai_agent_service)
) -> Dict[str, Any]:
    """
    Compare multiple papers using their AI agents.
    
    Agents will discuss similarities, differences, and
    relative strengths of their papers' approaches.
    """
    try:
        if len(request.paper_ids) < 2:
            raise HTTPException(
                status_code=400,
                detail="Need at least 2 papers to compare"
            )
        
        comparison = await ai_service.compare_papers(
            paper_ids=request.paper_ids,
            comparison_aspect=request.comparison_aspect
        )
        
        return comparison
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to compare papers: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/synthesize")
async def synthesize_knowledge(
    request: SynthesizeRequest,
    ai_service: AIAgentService = Depends(get_ai_agent_service)
) -> Dict[str, Any]:
    """
    Synthesize knowledge from multiple papers using their agents.
    
    Agents will work together to create a comprehensive
    understanding of the topic across all papers.
    """
    try:
        synthesis = await ai_service.synthesize_knowledge(
            paper_ids=request.paper_ids,
            topic=request.topic
        )
        
        return synthesis
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to synthesize knowledge: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/active")
async def list_active_agents(
    ai_service: AIAgentService = Depends(get_ai_agent_service)
) -> List[Dict[str, Any]]:
    """
    List all active AI agents.
    
    Returns information about each agent including
    performance metrics and current status.
    """
    try:
        agents = await ai_service.list_active_agents()
        return agents
        
    except Exception as e:
        logger.error(f"Failed to list active agents: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{agent_id}/performance")
async def get_agent_performance(
    agent_id: str,
    ai_service: AIAgentService = Depends(get_ai_agent_service)
) -> Dict[str, Any]:
    """
    Get performance metrics for a specific agent.
    
    Returns query statistics, usage patterns, and effectiveness metrics.
    """
    try:
        performance = await ai_service.get_agent_performance(agent_id)
        return performance
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to get agent performance: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{agent_id}")
async def deactivate_agent(
    agent_id: str,
    ai_service: AIAgentService = Depends(get_ai_agent_service)
) -> Dict[str, str]:
    """
    Deactivate an AI agent.
    
    The agent will be removed from active memory and
    marked as inactive in the database.
    """
    try:
        success = await ai_service.deactivate_agent(agent_id)
        
        if success:
            return {"status": "deactivated", "agent_id": agent_id}
        else:
            raise HTTPException(status_code=500, detail="Failed to deactivate agent")
            
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to deactivate agent: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/capabilities")
async def get_agent_capabilities() -> Dict[str, Any]:
    """
    Get information about AI agent capabilities.
    
    Returns available models, conversation types, and features.
    """
    return {
        "available_models": [
            "gpt-3.5-turbo",
            "gpt-4",
            "gpt-4-turbo-preview"
        ],
        "conversation_types": [
            "collaboration",
            "comparison", 
            "synthesis",
            "debate"
        ],
        "agent_capabilities": [
            "paper_summary",
            "methodology_explanation",
            "implementation_guidance",
            "related_work_comparison",
            "multi_agent_conversation",
            "code_analysis",
            "step_by_step_tutorials"
        ],
        "supported_features": [
            "real_time_chat",
            "multi_agent_conversations",
            "paper_comparison",
            "knowledge_synthesis",
            "github_integration",
            "contextual_responses"
        ]
    }