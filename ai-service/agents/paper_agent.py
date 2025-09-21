"""Individual paper AI agent implementation."""

import asyncio
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain.tools import Tool
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema import BaseMessage, HumanMessage, AIMessage
import structlog

logger = structlog.get_logger()


@dataclass
class PaperContext:
    """Paper context for agent initialization."""
    paper_id: str
    title: str
    abstract: str
    full_text: Optional[str]
    authors: List[str]
    categories: List[str]
    methodology: List[str]
    github_repos: List[str]
    key_findings: List[str]


class PaperAgent:
    """AI agent representing a research paper."""
    
    def __init__(
        self,
        paper_context: PaperContext,
        model_name: str = "gpt-3.5-turbo",
        temperature: float = 0.1
    ):
        self.paper_context = paper_context
        self.model_name = model_name
        self.temperature = temperature
        self.conversation_history: List[BaseMessage] = []
        
        # Initialize LLM with LiteLLM support
        from backend.core.llm_config import get_llm_client
        self.llm = get_llm_client(
            model_name=model_name,
            temperature=temperature,
            max_tokens=1000
        )
        
        # Create agent tools
        self.tools = self._create_tools()
        
        # Create agent prompt
        self.prompt = self._create_prompt()
        
        # Create agent executor
        self.agent = create_openai_functions_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=self.prompt
        )
        self.agent_executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            verbose=True,
            max_iterations=3
        )
    
    def _create_tools(self) -> List[Tool]:
        """Create tools for the paper agent."""
        tools = [
            Tool(
                name="get_paper_summary",
                description="Get a summary of the paper's main contributions",
                func=self._get_paper_summary
            ),
            Tool(
                name="explain_methodology",
                description="Explain the methodology used in the paper",
                func=self._explain_methodology
            ),
            Tool(
                name="get_implementation_details",
                description="Get implementation details and code repositories",
                func=self._get_implementation_details
            ),
            Tool(
                name="compare_with_related_work",
                description="Compare this paper with related work",
                func=self._compare_with_related_work
            ),
            Tool(
                name="get_key_findings",
                description="Get the key findings and results from the paper",
                func=self._get_key_findings
            )
        ]
        return tools
    
    def _create_prompt(self) -> ChatPromptTemplate:
        """Create the agent prompt template."""
        system_message = f"""You are an AI agent representing the research paper:

Title: {self.paper_context.title}
Authors: {', '.join(self.paper_context.authors)}
Categories: {', '.join(self.paper_context.categories)}

You have deep knowledge of this paper's content, methodology, and contributions. 
You can explain concepts, discuss implementation details, and help users understand the research.

Key capabilities:
- Explain the paper's methodology and approach
- Discuss implementation details and code repositories
- Compare with related work in the field
- Provide step-by-step implementation guidance
- Answer questions about results and findings

Always be helpful, accurate, and cite specific parts of the paper when relevant.
If you don't know something, be honest about the limitations of your knowledge.
"""
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_message),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad")
        ])
        
        return prompt
    
    async def query(self, question: str) -> Dict[str, Any]:
        """Query the paper agent with a question."""
        try:
            logger.info(f"Paper agent query: {question}")
            
            # Prepare input with conversation history
            input_data = {
                "input": question,
                "chat_history": self.conversation_history
            }
            
            # Execute agent
            result = await asyncio.to_thread(
                self.agent_executor.invoke,
                input_data
            )
            
            # Update conversation history
            self.conversation_history.extend([
                HumanMessage(content=question),
                AIMessage(content=result["output"])
            ])
            
            # Keep history manageable
            if len(self.conversation_history) > 20:
                self.conversation_history = self.conversation_history[-20:]
            
            return {
                "response": result["output"],
                "paper_id": self.paper_context.paper_id,
                "paper_title": self.paper_context.title,
                "tools_used": result.get("intermediate_steps", [])
            }
            
        except Exception as e:
            logger.error(f"Paper agent query failed: {e}")
            return {
                "response": f"I encountered an error while processing your question: {str(e)}",
                "paper_id": self.paper_context.paper_id,
                "error": str(e)
            }
    
    def _get_paper_summary(self, query: str = "") -> str:
        """Get paper summary."""
        summary_parts = [
            f"Title: {self.paper_context.title}",
            f"Authors: {', '.join(self.paper_context.authors)}",
            f"Abstract: {self.paper_context.abstract[:500]}..."
        ]
        
        if self.paper_context.methodology:
            methods = ', '.join(self.paper_context.methodology[:5])
            summary_parts.append(f"Key Methods: {methods}")
        
        return "\n\n".join(summary_parts)
    
    def _explain_methodology(self, query: str = "") -> str:
        """Explain the paper's methodology."""
        if not self.paper_context.methodology:
            return "Methodology details are not available for this paper."
        
        methodology_text = f"This paper uses the following methodologies:\n"
        for i, method in enumerate(self.paper_context.methodology[:10], 1):
            methodology_text += f"{i}. {method}\n"
        
        if self.paper_context.full_text:
            # Extract methodology section if available
            text_lower = self.paper_context.full_text.lower()
            if "methodology" in text_lower or "method" in text_lower:
                methodology_text += "\nFor detailed methodology, please refer to the methodology section in the full paper."
        
        return methodology_text
    
    def _get_implementation_details(self, query: str = "") -> str:
        """Get implementation details and repositories."""
        if not self.paper_context.github_repos:
            return "No GitHub repositories are associated with this paper."
        
        impl_text = "Implementation repositories:\n"
        for i, repo in enumerate(self.paper_context.github_repos, 1):
            impl_text += f"{i}. {repo}\n"
        
        impl_text += "\nThese repositories contain the code implementation of the methods described in the paper. "
        impl_text += "You can explore them to understand the practical implementation details."
        
        return impl_text
    
    def _compare_with_related_work(self, query: str = "") -> str:
        """Compare with related work."""
        comparison_text = f"This paper ({self.paper_context.title}) contributes to the field of {', '.join(self.paper_context.categories)}.\n\n"
        
        if self.paper_context.key_findings:
            comparison_text += "Key contributions compared to prior work:\n"
            for i, finding in enumerate(self.paper_context.key_findings[:5], 1):
                comparison_text += f"{i}. {finding}\n"
        
        comparison_text += "\nFor a detailed comparison with related work, please refer to the related work section in the paper."
        
        return comparison_text
    
    def _get_key_findings(self, query: str = "") -> str:
        """Get key findings from the paper."""
        if not self.paper_context.key_findings:
            return "Key findings are not available for this paper."
        
        findings_text = "Key findings from this research:\n\n"
        for i, finding in enumerate(self.paper_context.key_findings, 1):
            findings_text += f"{i}. {finding}\n\n"
        
        return findings_text
    
    def get_agent_info(self) -> Dict[str, Any]:
        """Get information about this agent."""
        return {
            "paper_id": self.paper_context.paper_id,
            "title": self.paper_context.title,
            "authors": self.paper_context.authors,
            "categories": self.paper_context.categories,
            "model": self.model_name,
            "has_github_repos": len(self.paper_context.github_repos) > 0,
            "has_methodology": len(self.paper_context.methodology) > 0,
            "conversation_length": len(self.conversation_history)
        }
    
    def reset_conversation(self):
        """Reset the conversation history."""
        self.conversation_history = []
        logger.info(f"Reset conversation for paper agent: {self.paper_context.paper_id}")


class PaperAgentFactory:
    """Factory for creating paper agents."""
    
    @staticmethod
    def create_agent(
        paper_data: Dict[str, Any],
        model_name: str = "gpt-3.5-turbo",
        temperature: float = 0.1
    ) -> PaperAgent:
        """Create a paper agent from paper data."""
        
        paper_context = PaperContext(
            paper_id=paper_data.get("id", ""),
            title=paper_data.get("title", ""),
            abstract=paper_data.get("abstract", ""),
            full_text=paper_data.get("full_text"),
            authors=paper_data.get("authors", []),
            categories=paper_data.get("categories", []),
            methodology=paper_data.get("methodology", []),
            github_repos=paper_data.get("github_repos", []),
            key_findings=paper_data.get("key_findings", [])
        )
        
        return PaperAgent(
            paper_context=paper_context,
            model_name=model_name,
            temperature=temperature
        )