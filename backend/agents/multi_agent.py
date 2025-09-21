"""Multi-agent coordination and collaboration system."""

import asyncio
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from enum import Enum
from dataclasses import dataclass

from .paper_agent import PaperAgent
from ..core.logging import LoggerMixin


class CollaborationMode(Enum):
    """Collaboration modes for multi-agent systems."""
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    DEBATE = "debate"
    CONSENSUS = "consensus"


@dataclass
class CollaborationTask:
    """Task definition for multi-agent collaboration."""
    task_id: str
    task_type: str
    query: str
    agents: List[str]
    mode: CollaborationMode
    max_iterations: int = 3
    timeout: int = 300  # seconds


@dataclass
class AgentResponse:
    """Response from an individual agent."""
    agent_id: str
    content: str
    confidence: float
    metadata: Dict[str, Any]
    timestamp: datetime


class MultiAgentCoordinator(LoggerMixin):
    """Coordinates collaboration between multiple paper agents."""
    
    def __init__(self):
        self.active_agents: Dict[str, PaperAgent] = {}
        self.active_collaborations: Dict[str, CollaborationTask] = {}
        
    def register_agent(self, agent_id: str, agent: PaperAgent):
        """Register an agent for collaboration."""
        self.active_agents[agent_id] = agent
        self.log_event("agent_registered", agent_id=agent_id)
    
    def unregister_agent(self, agent_id: str):
        """Unregister an agent."""
        if agent_id in self.active_agents:
            del self.active_agents[agent_id]
            self.log_event("agent_unregistered", agent_id=agent_id)
    
    async def start_collaboration(self, task: CollaborationTask) -> Dict[str, Any]:
        """Start a multi-agent collaboration."""
        try:
            self.active_collaborations[task.task_id] = task
            
            # Validate all agents are available
            missing_agents = [agent_id for agent_id in task.agents if agent_id not in self.active_agents]
            if missing_agents:
                raise ValueError(f"Agents not available: {missing_agents}")
            
            self.log_event("collaboration_started", 
                          task_id=task.task_id, 
                          mode=task.mode.value, 
                          agent_count=len(task.agents))
            
            # Route to appropriate collaboration method
            if task.mode == CollaborationMode.SEQUENTIAL:
                result = await self._sequential_collaboration(task)
            elif task.mode == CollaborationMode.PARALLEL:
                result = await self._parallel_collaboration(task)
            elif task.mode == CollaborationMode.DEBATE:
                result = await self._debate_collaboration(task)
            elif task.mode == CollaborationMode.CONSENSUS:
                result = await self._consensus_collaboration(task)
            else:
                raise ValueError(f"Unsupported collaboration mode: {task.mode}")
            
            # Clean up
            if task.task_id in self.active_collaborations:
                del self.active_collaborations[task.task_id]
            
            self.log_event("collaboration_completed", task_id=task.task_id)
            return result
            
        except Exception as e:
            self.log_error(e, operation="start_collaboration", task_id=task.task_id)
            raise
    
    async def _sequential_collaboration(self, task: CollaborationTask) -> Dict[str, Any]:
        """Sequential collaboration where agents build upon each other's responses."""
        responses = []
        current_context = task.query
        
        for i, agent_id in enumerate(task.agents):
            agent = self.active_agents[agent_id]
            
            # Add context from previous agents
            context = {
                "collaboration_context": {
                    "mode": "sequential",
                    "position": i + 1,
                    "total_agents": len(task.agents),
                    "previous_responses": responses[-3:] if responses else []  # Last 3 responses
                }
            }
            
            # Get response from current agent
            response = await agent.process_query(current_context, context)
            
            agent_response = AgentResponse(
                agent_id=agent_id,
                content=response["content"],
                confidence=response.get("confidence_score", 0.8),
                metadata=response.get("metadata", {}),
                timestamp=datetime.utcnow()
            )
            responses.append(agent_response)
            
            # Update context for next agent
            current_context = f"{task.query}\n\nPrevious agent ({agent_id}) responded: {response['content'][:200]}..."
        
        # Synthesize final response
        synthesized_response = await self._synthesize_sequential_responses(responses, task)
        
        return {
            "task_id": task.task_id,
            "mode": task.mode.value,
            "synthesized_response": synthesized_response,
            "individual_responses": {r.agent_id: r.content for r in responses},
            "collaboration_quality": self._calculate_collaboration_quality(responses),
            "consensus_score": self._calculate_consensus_score(responses),
            "total_iterations": 1,
            "participating_agents": task.agents
        }
    
    async def _parallel_collaboration(self, task: CollaborationTask) -> Dict[str, Any]:
        """Parallel collaboration where all agents respond simultaneously."""
        # Create tasks for all agents
        agent_tasks = []
        for agent_id in task.agents:
            agent = self.active_agents[agent_id]
            context = {
                "collaboration_context": {
                    "mode": "parallel",
                    "total_agents": len(task.agents)
                }
            }
            agent_tasks.append(agent.process_query(task.query, context))
        
        # Execute all tasks in parallel
        try:
            responses_data = await asyncio.wait_for(
                asyncio.gather(*agent_tasks, return_exceptions=True),
                timeout=task.timeout
            )
        except asyncio.TimeoutError:
            raise ValueError(f"Collaboration timed out after {task.timeout} seconds")
        
        # Process responses
        responses = []
        for i, response_data in enumerate(responses_data):
            if isinstance(response_data, Exception):
                self.log_error(response_data, operation="parallel_collaboration", agent_id=task.agents[i])
                continue
            
            agent_response = AgentResponse(
                agent_id=task.agents[i],
                content=response_data["content"],
                confidence=response_data.get("confidence_score", 0.8),
                metadata=response_data.get("metadata", {}),
                timestamp=datetime.utcnow()
            )
            responses.append(agent_response)
        
        # Synthesize responses
        synthesized_response = await self._synthesize_parallel_responses(responses, task)
        
        return {
            "task_id": task.task_id,
            "mode": task.mode.value,
            "synthesized_response": synthesized_response,
            "individual_responses": {r.agent_id: r.content for r in responses},
            "collaboration_quality": self._calculate_collaboration_quality(responses),
            "consensus_score": self._calculate_consensus_score(responses),
            "total_iterations": 1,
            "participating_agents": [r.agent_id for r in responses]
        }
    
    async def _debate_collaboration(self, task: CollaborationTask) -> Dict[str, Any]:
        """Debate collaboration where agents challenge each other's responses."""
        all_responses = []
        current_iteration = 0
        
        # Initial round - all agents respond to original query
        initial_responses = []
        for agent_id in task.agents:
            agent = self.active_agents[agent_id]
            context = {
                "collaboration_context": {
                    "mode": "debate",
                    "iteration": 1,
                    "total_agents": len(task.agents)
                }
            }
            response = await agent.process_query(task.query, context)
            
            agent_response = AgentResponse(
                agent_id=agent_id,
                content=response["content"],
                confidence=response.get("confidence_score", 0.8),
                metadata=response.get("metadata", {}),
                timestamp=datetime.utcnow()
            )
            initial_responses.append(agent_response)
        
        all_responses.extend(initial_responses)
        current_iteration += 1
        
        # Debate rounds
        while current_iteration < task.max_iterations:
            round_responses = []
            
            for i, agent_id in enumerate(task.agents):
                agent = self.active_agents[agent_id]
                
                # Get other agents' responses to challenge
                other_responses = [r for r in initial_responses if r.agent_id != agent_id]
                
                debate_query = f"Original query: {task.query}\n\n"
                debate_query += "Other agents have responded:\n"
                for other_response in other_responses:
                    debate_query += f"- {other_response.agent_id}: {other_response.content[:150]}...\n"
                debate_query += "\nPlease provide your counter-argument or refined response:"
                
                context = {
                    "collaboration_context": {
                        "mode": "debate",
                        "iteration": current_iteration + 1,
                        "other_responses": [r.content for r in other_responses]
                    }
                }
                
                response = await agent.process_query(debate_query, context)
                
                agent_response = AgentResponse(
                    agent_id=agent_id,
                    content=response["content"],
                    confidence=response.get("confidence_score", 0.8),
                    metadata=response.get("metadata", {}),
                    timestamp=datetime.utcnow()
                )
                round_responses.append(agent_response)
            
            all_responses.extend(round_responses)
            current_iteration += 1
            
            # Check for convergence
            if self._check_debate_convergence(round_responses, initial_responses):
                break
            
            initial_responses = round_responses  # Use latest responses for next round
        
        # Synthesize final debate outcome
        synthesized_response = await self._synthesize_debate_responses(all_responses, task)
        
        return {
            "task_id": task.task_id,
            "mode": task.mode.value,
            "synthesized_response": synthesized_response,
            "individual_responses": {r.agent_id: r.content for r in all_responses[-len(task.agents):]},
            "collaboration_quality": self._calculate_collaboration_quality(all_responses),
            "consensus_score": self._calculate_consensus_score(all_responses[-len(task.agents):]),
            "total_iterations": current_iteration,
            "participating_agents": task.agents,
            "debate_rounds": current_iteration,
            "key_agreements": self._extract_agreements(all_responses),
            "key_disagreements": self._extract_disagreements(all_responses)
        }
    
    async def _consensus_collaboration(self, task: CollaborationTask) -> Dict[str, Any]:
        """Consensus collaboration where agents work towards agreement."""
        all_responses = []
        current_iteration = 0
        
        # Initial responses
        current_responses = []
        for agent_id in task.agents:
            agent = self.active_agents[agent_id]
            context = {
                "collaboration_context": {
                    "mode": "consensus",
                    "iteration": 1,
                    "goal": "work towards consensus"
                }
            }
            response = await agent.process_query(task.query, context)
            
            agent_response = AgentResponse(
                agent_id=agent_id,
                content=response["content"],
                confidence=response.get("confidence_score", 0.8),
                metadata=response.get("metadata", {}),
                timestamp=datetime.utcnow()
            )
            current_responses.append(agent_response)
        
        all_responses.extend(current_responses)
        current_iteration += 1
        
        # Consensus building rounds
        while current_iteration < task.max_iterations:
            consensus_score = self._calculate_consensus_score(current_responses)
            
            if consensus_score > 0.8:  # High consensus reached
                break
            
            # Generate consensus-building query
            consensus_query = f"Original query: {task.query}\n\n"
            consensus_query += "Current responses from the team:\n"
            for response in current_responses:
                consensus_query += f"- {response.agent_id}: {response.content[:150]}...\n"
            consensus_query += "\nPlease work towards a consensus by finding common ground and addressing differences:"
            
            round_responses = []
            for agent_id in task.agents:
                agent = self.active_agents[agent_id]
                context = {
                    "collaboration_context": {
                        "mode": "consensus",
                        "iteration": current_iteration + 1,
                        "current_consensus_score": consensus_score,
                        "team_responses": [r.content for r in current_responses]
                    }
                }
                
                response = await agent.process_query(consensus_query, context)
                
                agent_response = AgentResponse(
                    agent_id=agent_id,
                    content=response["content"],
                    confidence=response.get("confidence_score", 0.8),
                    metadata=response.get("metadata", {}),
                    timestamp=datetime.utcnow()
                )
                round_responses.append(agent_response)
            
            all_responses.extend(round_responses)
            current_responses = round_responses
            current_iteration += 1
        
        # Generate final consensus
        final_consensus_score = self._calculate_consensus_score(current_responses)
        synthesized_response = await self._synthesize_consensus_responses(current_responses, task)
        
        return {
            "task_id": task.task_id,
            "mode": task.mode.value,
            "synthesized_response": synthesized_response,
            "individual_responses": {r.agent_id: r.content for r in current_responses},
            "collaboration_quality": self._calculate_collaboration_quality(all_responses),
            "consensus_score": final_consensus_score,
            "total_iterations": current_iteration,
            "participating_agents": task.agents,
            "consensus_achieved": final_consensus_score > 0.8
        }
    
    async def _synthesize_sequential_responses(self, responses: List[AgentResponse], task: CollaborationTask) -> str:
        """Synthesize sequential responses into a coherent answer."""
        synthesis = f"Based on sequential analysis by {len(responses)} specialized agents:\n\n"
        
        for i, response in enumerate(responses, 1):
            synthesis += f"Agent {i} Analysis: {response.content[:200]}...\n\n"
        
        synthesis += "Integrated Conclusion: "
        synthesis += "The sequential analysis reveals a comprehensive understanding that builds from "
        synthesis += f"initial insights to a refined conclusion addressing: {task.query}"
        
        return synthesis
    
    async def _synthesize_parallel_responses(self, responses: List[AgentResponse], task: CollaborationTask) -> str:
        """Synthesize parallel responses into a unified answer."""
        synthesis = f"Parallel analysis by {len(responses)} specialized agents reveals:\n\n"
        
        # Group similar insights
        high_confidence = [r for r in responses if r.confidence > 0.8]
        medium_confidence = [r for r in responses if 0.6 <= r.confidence <= 0.8]
        
        if high_confidence:
            synthesis += "High Confidence Insights:\n"
            for response in high_confidence:
                synthesis += f"• {response.content[:150]}...\n"
            synthesis += "\n"
        
        if medium_confidence:
            synthesis += "Additional Considerations:\n"
            for response in medium_confidence:
                synthesis += f"• {response.content[:150]}...\n"
            synthesis += "\n"
        
        synthesis += "Unified Conclusion: The parallel analysis provides multiple perspectives that "
        synthesis += f"collectively address the query: {task.query}"
        
        return synthesis
    
    async def _synthesize_debate_responses(self, responses: List[AgentResponse], task: CollaborationTask) -> str:
        """Synthesize debate responses into a balanced conclusion."""
        latest_responses = responses[-len(task.agents):]
        
        synthesis = f"After {len(responses) // len(task.agents)} rounds of debate:\n\n"
        
        agreements = self._extract_agreements(responses)
        disagreements = self._extract_disagreements(responses)
        
        if agreements:
            synthesis += "Points of Agreement:\n"
            for agreement in agreements:
                synthesis += f"• {agreement}\n"
            synthesis += "\n"
        
        if disagreements:
            synthesis += "Remaining Disagreements:\n"
            for disagreement in disagreements:
                synthesis += f"• {disagreement}\n"
            synthesis += "\n"
        
        synthesis += "Balanced Conclusion: Through rigorous debate, the agents have explored "
        synthesis += f"multiple facets of: {task.query}"
        
        return synthesis
    
    async def _synthesize_consensus_responses(self, responses: List[AgentResponse], task: CollaborationTask) -> str:
        """Synthesize consensus responses into an agreed-upon answer."""
        consensus_score = self._calculate_consensus_score(responses)
        
        synthesis = f"Consensus Analysis (Agreement Level: {consensus_score:.1%}):\n\n"
        
        # Find common themes
        common_themes = self._extract_common_themes(responses)
        
        if common_themes:
            synthesis += "Agreed-Upon Points:\n"
            for theme in common_themes:
                synthesis += f"• {theme}\n"
            synthesis += "\n"
        
        synthesis += "Consensus Conclusion: The agents have reached "
        if consensus_score > 0.8:
            synthesis += "strong consensus"
        elif consensus_score > 0.6:
            synthesis += "moderate consensus"
        else:
            synthesis += "partial consensus"
        
        synthesis += f" on the key aspects of: {task.query}"
        
        return synthesis
    
    def _calculate_collaboration_quality(self, responses: List[AgentResponse]) -> float:
        """Calculate overall collaboration quality score."""
        if not responses:
            return 0.0
        
        # Factors: response diversity, confidence levels, content quality
        avg_confidence = sum(r.confidence for r in responses) / len(responses)
        response_diversity = len(set(r.content[:100] for r in responses)) / len(responses)
        
        quality_score = (avg_confidence * 0.6) + (response_diversity * 0.4)
        return min(quality_score, 1.0)
    
    def _calculate_consensus_score(self, responses: List[AgentResponse]) -> float:
        """Calculate consensus score based on response similarity."""
        if len(responses) < 2:
            return 1.0
        
        # Simplified consensus calculation based on response length similarity
        # In practice, this would use semantic similarity
        lengths = [len(r.content) for r in responses]
        avg_length = sum(lengths) / len(lengths)
        variance = sum((l - avg_length) ** 2 for l in lengths) / len(lengths)
        
        # Lower variance indicates higher consensus
        consensus_score = max(0.0, 1.0 - (variance / (avg_length ** 2)))
        return min(consensus_score, 1.0)
    
    def _check_debate_convergence(self, current_responses: List[AgentResponse], previous_responses: List[AgentResponse]) -> bool:
        """Check if debate has converged."""
        if not current_responses or not previous_responses:
            return False
        
        # Simple convergence check based on response length stability
        current_avg_length = sum(len(r.content) for r in current_responses) / len(current_responses)
        previous_avg_length = sum(len(r.content) for r in previous_responses) / len(previous_responses)
        
        length_change = abs(current_avg_length - previous_avg_length) / previous_avg_length
        return length_change < 0.1  # Less than 10% change indicates convergence
    
    def _extract_agreements(self, responses: List[AgentResponse]) -> List[str]:
        """Extract points of agreement from responses."""
        # Placeholder implementation
        return [
            "Core methodology approach",
            "Problem definition accuracy",
            "Implementation feasibility"
        ]
    
    def _extract_disagreements(self, responses: List[AgentResponse]) -> List[str]:
        """Extract points of disagreement from responses."""
        # Placeholder implementation
        return [
            "Optimal parameter settings",
            "Performance evaluation metrics",
            "Scalability considerations"
        ]
    
    def _extract_common_themes(self, responses: List[AgentResponse]) -> List[str]:
        """Extract common themes from responses."""
        # Placeholder implementation
        return [
            "Importance of data quality",
            "Need for proper validation",
            "Consideration of computational resources"
        ]
    
    def get_active_collaborations(self) -> Dict[str, CollaborationTask]:
        """Get currently active collaborations."""
        return self.active_collaborations.copy()
    
    def get_registered_agents(self) -> List[str]:
        """Get list of registered agent IDs."""
        return list(self.active_agents.keys())