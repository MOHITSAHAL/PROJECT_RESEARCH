"""Individual paper AI agent implementation."""

import asyncio
from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from ..core.logging import LoggerMixin
from ..core.config import settings


@dataclass
class AgentMemory:
    """Agent memory structure for conversation context."""
    conversation_history: List[Dict[str, Any]]
    paper_context: Dict[str, Any]
    user_preferences: Dict[str, Any]
    session_data: Dict[str, Any]


class PaperAgent(LoggerMixin):
    """AI agent for individual research papers."""
    
    def __init__(self, agent_id: str, paper_data: Dict[str, Any], config: Dict[str, Any]):
        self.agent_id = agent_id
        self.paper_data = paper_data
        self.config = config
        self.memory = AgentMemory(
            conversation_history=[],
            paper_context=paper_data,
            user_preferences={},
            session_data={}
        )
        self.capabilities = config.get("capabilities", [])
        self.model_name = config.get("model_name", "gpt-3.5-turbo")
        self.specialization = config.get("specialization")
        
    async def process_query(self, query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Process a user query and return response."""
        try:
            start_time = datetime.utcnow()
            
            # Update context
            if context:
                self.memory.user_preferences.update(context.get("user_preferences", {}))
                self.memory.session_data.update(context.get("session_data", {}))
            
            # Add query to conversation history
            self.memory.conversation_history.append({
                "type": "user",
                "content": query,
                "timestamp": start_time.isoformat(),
                "context": context
            })
            
            # Determine query type and route to appropriate handler
            query_type = self._classify_query(query)
            
            if query_type == "explanation":
                response = await self._handle_explanation_query(query, context)
            elif query_type == "implementation":
                response = await self._handle_implementation_query(query, context)
            elif query_type == "comparison":
                response = await self._handle_comparison_query(query, context)
            elif query_type == "methodology":
                response = await self._handle_methodology_query(query, context)
            else:
                response = await self._handle_general_query(query, context)
            
            # Calculate response time
            response_time = (datetime.utcnow() - start_time).total_seconds()
            
            # Add response to conversation history
            self.memory.conversation_history.append({
                "type": "agent",
                "content": response["content"],
                "timestamp": datetime.utcnow().isoformat(),
                "response_time": response_time,
                "metadata": response.get("metadata", {})
            })
            
            # Trim conversation history if too long
            max_history = self.config.get("memory_size", 10)
            if len(self.memory.conversation_history) > max_history * 2:
                self.memory.conversation_history = self.memory.conversation_history[-max_history * 2:]
            
            # Prepare final response
            final_response = {
                "content": response["content"],
                "response_type": response.get("response_type", "text"),
                "confidence_score": response.get("confidence_score", 0.8),
                "response_time": response_time,
                "metadata": response.get("metadata", {}),
                "follow_up_suggestions": self._generate_follow_up_suggestions(query, response),
                "references": self._get_paper_references(),
                "code_examples": response.get("code_examples", [])
            }
            
            self.log_event("query_processed", agent_id=self.agent_id, query_type=query_type, response_time=response_time)
            return final_response
            
        except Exception as e:
            self.log_error(e, operation="process_query", agent_id=self.agent_id)
            return {
                "content": "I apologize, but I encountered an error processing your query. Please try again.",
                "response_type": "error",
                "confidence_score": 0.0,
                "response_time": 0.0,
                "metadata": {"error": str(e)}
            }
    
    async def generate_implementation_guide(self, framework: str = "pytorch", complexity: str = "intermediate") -> Dict[str, Any]:
        """Generate step-by-step implementation guide."""
        try:
            paper_title = self.paper_data.get("title", "")
            paper_abstract = self.paper_data.get("abstract", "")
            github_repos = self.paper_data.get("github_repos", [])
            
            # Analyze paper for implementation details
            implementation_analysis = await self._analyze_implementation_requirements(framework, complexity)
            
            # Generate guide structure
            guide = {
                "title": f"Implementing {paper_title}",
                "framework": framework,
                "complexity_level": complexity,
                "estimated_time": implementation_analysis.get("estimated_time", 120),
                "prerequisites": implementation_analysis.get("prerequisites", []),
                "steps": await self._generate_implementation_steps(framework, complexity),
                "code_examples": await self._generate_code_examples(framework),
                "troubleshooting": await self._generate_troubleshooting_guide(),
                "references": {
                    "paper": {
                        "title": paper_title,
                        "abstract": paper_abstract
                    },
                    "github_repos": github_repos,
                    "additional_resources": implementation_analysis.get("resources", [])
                }
            }
            
            self.log_event("implementation_guide_generated", agent_id=self.agent_id, framework=framework)
            return guide
            
        except Exception as e:
            self.log_error(e, operation="generate_implementation_guide", agent_id=self.agent_id)
            raise
    
    async def explain_methodology(self, detail_level: str = "intermediate") -> Dict[str, Any]:
        """Explain the paper's methodology."""
        try:
            methodology = self.paper_data.get("methodology", [])
            abstract = self.paper_data.get("abstract", "")
            
            explanation = {
                "overview": await self._generate_methodology_overview(detail_level),
                "key_concepts": await self._extract_key_concepts(detail_level),
                "step_by_step": await self._generate_methodology_steps(detail_level),
                "advantages": await self._analyze_methodology_advantages(),
                "limitations": await self._analyze_methodology_limitations(),
                "applications": await self._identify_applications(),
                "related_work": await self._find_related_methodologies()
            }
            
            return explanation
            
        except Exception as e:
            self.log_error(e, operation="explain_methodology", agent_id=self.agent_id)
            raise
    
    def get_conversation_context(self) -> Dict[str, Any]:
        """Get current conversation context."""
        return {
            "conversation_history": self.memory.conversation_history[-10:],  # Last 10 messages
            "paper_context": self.memory.paper_context,
            "user_preferences": self.memory.user_preferences,
            "session_data": self.memory.session_data
        }
    
    def update_context(self, context_update: Dict[str, Any]):
        """Update agent context."""
        if "user_preferences" in context_update:
            self.memory.user_preferences.update(context_update["user_preferences"])
        if "session_data" in context_update:
            self.memory.session_data.update(context_update["session_data"])
    
    def _classify_query(self, query: str) -> str:
        """Classify the type of query."""
        query_lower = query.lower()
        
        if any(word in query_lower for word in ["explain", "what is", "how does", "describe"]):
            return "explanation"
        elif any(word in query_lower for word in ["implement", "code", "build", "create", "tutorial"]):
            return "implementation"
        elif any(word in query_lower for word in ["compare", "difference", "versus", "vs", "better"]):
            return "comparison"
        elif any(word in query_lower for word in ["method", "approach", "algorithm", "technique"]):
            return "methodology"
        else:
            return "general"
    
    async def _handle_explanation_query(self, query: str, context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Handle explanation-type queries."""
        paper_title = self.paper_data.get("title", "")
        paper_abstract = self.paper_data.get("abstract", "")
        
        # Generate explanation based on paper content
        explanation = f"Based on the paper '{paper_title}', here's an explanation:\n\n"
        
        if "attention" in query.lower() and "attention" in paper_title.lower():
            explanation += "The attention mechanism allows the model to focus on different parts of the input sequence when processing each element. "
            explanation += "This is particularly useful in transformer architectures where it replaces recurrent connections."
        elif "transformer" in query.lower() and "transformer" in paper_title.lower():
            explanation += "The Transformer architecture is based entirely on attention mechanisms, dispensing with recurrence and convolutions. "
            explanation += "It consists of an encoder-decoder structure with multi-head self-attention layers."
        else:
            # General explanation based on abstract
            explanation += f"According to the paper: {paper_abstract[:300]}..."
        
        return {
            "content": explanation,
            "response_type": "explanation",
            "confidence_score": 0.85,
            "metadata": {
                "query_type": "explanation",
                "paper_relevance": 0.9
            }
        }
    
    async def _handle_implementation_query(self, query: str, context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Handle implementation-type queries."""
        framework = "pytorch"  # Default, could be extracted from context
        
        if "pytorch" in query.lower():
            framework = "pytorch"
        elif "tensorflow" in query.lower():
            framework = "tensorflow"
        
        code_example = f"""
# Implementation example for {self.paper_data.get('title', 'this paper')}
import {framework}
import torch.nn as nn

class PaperImplementation(nn.Module):
    def __init__(self):
        super().__init__()
        # Implementation based on paper methodology
        pass
    
    def forward(self, x):
        # Forward pass implementation
        return x
"""
        
        response = f"Here's how you can implement the concepts from this paper using {framework}:\n\n"
        response += "The key components you'll need to implement are:\n"
        response += "1. Data preprocessing\n2. Model architecture\n3. Training loop\n4. Evaluation metrics\n\n"
        response += "Here's a basic code structure to get you started:"
        
        return {
            "content": response,
            "response_type": "implementation",
            "confidence_score": 0.8,
            "code_examples": [
                {
                    "language": "python",
                    "framework": framework,
                    "code": code_example.strip()
                }
            ],
            "metadata": {
                "query_type": "implementation",
                "framework": framework
            }
        }
    
    async def _handle_comparison_query(self, query: str, context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Handle comparison-type queries."""
        response = f"Comparing the approach in '{self.paper_data.get('title', 'this paper')}' with other methods:\n\n"
        response += "Key advantages of this approach:\n"
        response += "• Novel methodology that improves upon previous work\n"
        response += "• Better performance on benchmark datasets\n"
        response += "• More efficient computational requirements\n\n"
        response += "Potential limitations:\n"
        response += "• May require specific dataset characteristics\n"
        response += "• Implementation complexity\n"
        response += "• Computational resources needed for training"
        
        return {
            "content": response,
            "response_type": "comparison",
            "confidence_score": 0.75,
            "metadata": {
                "query_type": "comparison"
            }
        }
    
    async def _handle_methodology_query(self, query: str, context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Handle methodology-type queries."""
        methodology = self.paper_data.get("methodology", [])
        
        response = f"The methodology used in '{self.paper_data.get('title', 'this paper')}' involves:\n\n"
        
        if methodology:
            for i, method in enumerate(methodology, 1):
                response += f"{i}. {method.replace('_', ' ').title()}\n"
        else:
            response += "The paper employs a systematic approach that includes:\n"
            response += "• Problem formulation and analysis\n"
            response += "• Proposed solution design\n"
            response += "• Experimental validation\n"
            response += "• Results analysis and comparison"
        
        return {
            "content": response,
            "response_type": "methodology",
            "confidence_score": 0.8,
            "metadata": {
                "query_type": "methodology",
                "methodologies": methodology
            }
        }
    
    async def _handle_general_query(self, query: str, context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Handle general queries."""
        response = f"Regarding your question about '{self.paper_data.get('title', 'this paper')}':\n\n"
        response += f"This paper presents {self.paper_data.get('abstract', 'research findings')[:200]}...\n\n"
        response += "I can help you with:\n"
        response += "• Explaining the methodology\n"
        response += "• Implementation guidance\n"
        response += "• Comparing with other approaches\n"
        response += "• Discussing applications and implications"
        
        return {
            "content": response,
            "response_type": "general",
            "confidence_score": 0.7,
            "metadata": {
                "query_type": "general"
            }
        }
    
    def _generate_follow_up_suggestions(self, query: str, response: Dict[str, Any]) -> List[str]:
        """Generate follow-up question suggestions."""
        suggestions = []
        
        query_type = response.get("metadata", {}).get("query_type", "general")
        
        if query_type == "explanation":
            suggestions = [
                "Can you provide a more detailed technical explanation?",
                "How does this compare to other approaches?",
                "What are the practical applications?",
                "Can you show me how to implement this?"
            ]
        elif query_type == "implementation":
            suggestions = [
                "What are the key challenges in implementation?",
                "Can you explain the training process?",
                "How do I evaluate the model performance?",
                "What datasets should I use for testing?"
            ]
        elif query_type == "methodology":
            suggestions = [
                "What are the advantages of this methodology?",
                "How does it improve upon previous work?",
                "What are the limitations?",
                "Can you show implementation examples?"
            ]
        else:
            suggestions = [
                "Can you explain the main contributions?",
                "How do I implement this approach?",
                "What are the key technical details?",
                "How does this compare to related work?"
            ]
        
        return suggestions[:3]  # Return top 3 suggestions
    
    def _get_paper_references(self) -> List[str]:
        """Get paper references."""
        return [
            self.paper_data.get("title", ""),
            f"Authors: {', '.join(self.paper_data.get('authors', []))}",
            f"Published: {self.paper_data.get('published_date', 'N/A')}"
        ]
    
    async def _analyze_implementation_requirements(self, framework: str, complexity: str) -> Dict[str, Any]:
        """Analyze implementation requirements."""
        return {
            "estimated_time": 120 if complexity == "intermediate" else 180,
            "prerequisites": [f"{framework}>=1.0", "numpy", "matplotlib"],
            "resources": [
                "Official documentation",
                "Tutorial notebooks",
                "Community examples"
            ]
        }
    
    async def _generate_implementation_steps(self, framework: str, complexity: str) -> List[Dict[str, Any]]:
        """Generate implementation steps."""
        return [
            {
                "step": 1,
                "title": "Environment Setup",
                "description": f"Install {framework} and required dependencies",
                "estimated_time": 15,
                "difficulty": "easy"
            },
            {
                "step": 2,
                "title": "Data Preparation",
                "description": "Load and preprocess your dataset",
                "estimated_time": 30,
                "difficulty": "medium"
            },
            {
                "step": 3,
                "title": "Model Implementation",
                "description": "Implement the core model architecture",
                "estimated_time": 45,
                "difficulty": "hard" if complexity == "expert" else "medium"
            },
            {
                "step": 4,
                "title": "Training Setup",
                "description": "Configure training loop and optimization",
                "estimated_time": 20,
                "difficulty": "medium"
            },
            {
                "step": 5,
                "title": "Evaluation",
                "description": "Implement evaluation metrics and testing",
                "estimated_time": 10,
                "difficulty": "easy"
            }
        ]
    
    async def _generate_code_examples(self, framework: str) -> List[Dict[str, str]]:
        """Generate code examples."""
        return [
            {
                "title": "Basic Model Structure",
                "language": "python",
                "code": f"import {framework}\n# Basic model implementation\nclass Model(nn.Module):\n    def __init__(self):\n        super().__init__()\n        # Model layers here\n        pass"
            },
            {
                "title": "Training Loop",
                "language": "python", 
                "code": "# Training loop\nfor epoch in range(num_epochs):\n    for batch in dataloader:\n        # Forward pass\n        # Backward pass\n        # Update weights\n        pass"
            }
        ]
    
    async def _generate_troubleshooting_guide(self) -> List[Dict[str, str]]:
        """Generate troubleshooting guide."""
        return [
            {
                "issue": "Model not converging",
                "solution": "Try adjusting learning rate, check data preprocessing, verify loss function"
            },
            {
                "issue": "Out of memory errors",
                "solution": "Reduce batch size, use gradient accumulation, or use mixed precision training"
            },
            {
                "issue": "Poor performance",
                "solution": "Check data quality, verify model architecture, tune hyperparameters"
            }
        ]
    
    async def _generate_methodology_overview(self, detail_level: str) -> str:
        """Generate methodology overview."""
        title = self.paper_data.get("title", "")
        abstract = self.paper_data.get("abstract", "")
        
        if detail_level == "beginner":
            return f"This paper presents a new approach to solve a specific problem. The main idea is explained in simple terms based on the research findings."
        elif detail_level == "expert":
            return f"The methodology in '{title}' employs advanced techniques with detailed mathematical formulations and algorithmic innovations."
        else:
            return f"The paper '{title}' introduces a methodology that builds upon existing work while providing novel contributions to the field."
    
    async def _extract_key_concepts(self, detail_level: str) -> List[str]:
        """Extract key concepts from the paper."""
        # This would use NLP to extract actual concepts
        return [
            "Core algorithm/approach",
            "Novel contributions", 
            "Experimental methodology",
            "Performance metrics",
            "Comparative analysis"
        ]
    
    async def _generate_methodology_steps(self, detail_level: str) -> List[Dict[str, str]]:
        """Generate methodology steps."""
        return [
            {"step": "Problem Formulation", "description": "Define the research problem and objectives"},
            {"step": "Approach Design", "description": "Develop the proposed solution methodology"},
            {"step": "Implementation", "description": "Implement the approach with necessary algorithms"},
            {"step": "Evaluation", "description": "Test and validate the approach with experiments"},
            {"step": "Analysis", "description": "Analyze results and compare with existing methods"}
        ]
    
    async def _analyze_methodology_advantages(self) -> List[str]:
        """Analyze methodology advantages."""
        return [
            "Improved performance over baseline methods",
            "Novel approach to existing problems",
            "Computational efficiency gains",
            "Broader applicability"
        ]
    
    async def _analyze_methodology_limitations(self) -> List[str]:
        """Analyze methodology limitations."""
        return [
            "Specific dataset requirements",
            "Computational complexity considerations",
            "Limited scope of evaluation",
            "Potential scalability challenges"
        ]
    
    async def _identify_applications(self) -> List[str]:
        """Identify potential applications."""
        categories = self.paper_data.get("categories", [])
        applications = []
        
        if "cs.CV" in categories:
            applications.extend(["Image recognition", "Object detection", "Medical imaging"])
        if "cs.CL" in categories:
            applications.extend(["Natural language processing", "Machine translation", "Text analysis"])
        if "cs.LG" in categories:
            applications.extend(["Predictive modeling", "Pattern recognition", "Data mining"])
        
        return applications or ["General machine learning applications"]
    
    async def _find_related_methodologies(self) -> List[str]:
        """Find related methodologies."""
        return [
            "Traditional machine learning approaches",
            "Deep learning variants",
            "Ensemble methods",
            "Transfer learning techniques"
        ]