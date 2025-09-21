"""AI-powered paper summarization service."""

import asyncio
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from langchain.chains.summarize import load_summarize_chain
from langchain_openai import ChatOpenAI
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
import structlog

logger = structlog.get_logger()


@dataclass
class SummaryRequest:
    """Summary request configuration."""
    text: str
    summary_type: str = "comprehensive"  # comprehensive, concise, technical
    target_audience: str = "intermediate"  # beginner, intermediate, expert
    max_length: int = 500
    focus_areas: List[str] = None


class PaperSummarizer:
    """AI-powered paper summarization service."""
    
    def __init__(self, model_name: str = "gpt-3.5-turbo"):
        self.model_name = model_name
        # Initialize LLM with LiteLLM support
        import sys
        import os
        sys.path.append(os.path.join(os.path.dirname(__file__), '../../backend'))
        from core.llm_config import get_llm_client
        self.llm = get_llm_client(
            model_name=model_name,
            temperature=0.1,
            max_tokens=1000
        )
        
        # Text splitter for long documents
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=4000,
            chunk_overlap=200,
            length_function=len
        )
    
    async def summarize_paper(
        self,
        paper_content: Dict[str, Any],
        summary_request: SummaryRequest
    ) -> Dict[str, Any]:
        """Generate AI-powered summary of a research paper."""
        try:
            logger.info(f"Generating {summary_request.summary_type} summary")
            
            # Extract content
            title = paper_content.get("title", "")
            abstract = paper_content.get("abstract", "")
            full_text = paper_content.get("full_text", "")
            methodology = paper_content.get("methodology", [])
            
            # Choose summarization strategy
            if summary_request.summary_type == "comprehensive":
                summary = await self._comprehensive_summary(
                    title, abstract, full_text, methodology, summary_request
                )
            elif summary_request.summary_type == "concise":
                summary = await self._concise_summary(
                    title, abstract, summary_request
                )
            elif summary_request.summary_type == "technical":
                summary = await self._technical_summary(
                    title, abstract, full_text, methodology, summary_request
                )
            else:
                summary = await self._default_summary(
                    title, abstract, summary_request
                )
            
            return {
                "summary": summary,
                "summary_type": summary_request.summary_type,
                "target_audience": summary_request.target_audience,
                "word_count": len(summary.split()),
                "focus_areas": summary_request.focus_areas or []
            }
            
        except Exception as e:
            logger.error(f"Failed to generate summary: {e}")
            raise
    
    async def _comprehensive_summary(
        self,
        title: str,
        abstract: str,
        full_text: str,
        methodology: List[str],
        request: SummaryRequest
    ) -> str:
        """Generate comprehensive summary."""
        
        # Prepare content for summarization
        content_parts = [
            f"Title: {title}",
            f"Abstract: {abstract}"
        ]
        
        if methodology:
            content_parts.append(f"Methodology: {', '.join(methodology)}")
        
        if full_text and len(full_text) > 1000:
            # Use full text for comprehensive summary
            content_parts.append(f"Full Content: {full_text[:8000]}")  # Limit for token constraints
        
        content = "\n\n".join(content_parts)
        
        # Create prompt based on audience
        if request.target_audience == "beginner":
            prompt_template = """
            Provide a comprehensive but accessible summary of this research paper for beginners.
            Explain technical concepts in simple terms and focus on:
            - What problem the paper solves
            - The main approach used
            - Key findings and their significance
            - Practical implications
            
            Content: {content}
            
            Summary:
            """
        elif request.target_audience == "expert":
            prompt_template = """
            Provide a detailed technical summary of this research paper for experts.
            Focus on:
            - Novel contributions and innovations
            - Methodological details and rigor
            - Experimental setup and results
            - Limitations and future work
            - Comparison with state-of-the-art
            
            Content: {content}
            
            Summary:
            """
        else:  # intermediate
            prompt_template = """
            Provide a balanced summary of this research paper for intermediate readers.
            Include:
            - Problem statement and motivation
            - Methodology and approach
            - Key results and findings
            - Significance and impact
            - Implementation considerations
            
            Content: {content}
            
            Summary:
            """
        
        # Generate summary
        prompt = prompt_template.format(content=content)
        
        # Split into chunks if too long
        if len(prompt) > 12000:  # Rough token limit
            docs = [Document(page_content=content)]
            texts = self.text_splitter.split_documents(docs)
            
            # Use map-reduce summarization for long content
            chain = load_summarize_chain(
                self.llm,
                chain_type="map_reduce",
                verbose=True
            )
            
            summary = await asyncio.to_thread(chain.run, texts)
        else:
            # Direct summarization for shorter content
            response = await asyncio.to_thread(
                self.llm.invoke,
                prompt
            )
            summary = response.content
        
        return summary
    
    async def _concise_summary(
        self,
        title: str,
        abstract: str,
        request: SummaryRequest
    ) -> str:
        """Generate concise summary."""
        
        prompt = f"""
        Create a concise summary (max {request.max_length} words) of this research paper:
        
        Title: {title}
        Abstract: {abstract}
        
        Focus on the most important points for {request.target_audience} audience.
        Include: main contribution, approach, and key result.
        
        Concise Summary:
        """
        
        response = await asyncio.to_thread(self.llm.invoke, prompt)
        return response.content
    
    async def _technical_summary(
        self,
        title: str,
        abstract: str,
        full_text: str,
        methodology: List[str],
        request: SummaryRequest
    ) -> str:
        """Generate technical summary focusing on methodology."""
        
        content_parts = [
            f"Title: {title}",
            f"Abstract: {abstract}"
        ]
        
        if methodology:
            content_parts.append(f"Methods: {', '.join(methodology)}")
        
        # Extract methodology section if available
        if full_text:
            text_lower = full_text.lower()
            if "methodology" in text_lower or "method" in text_lower:
                # Try to extract methodology section
                lines = full_text.split('\n')
                method_section = []
                in_method_section = False
                
                for line in lines:
                    line_lower = line.lower().strip()
                    if any(keyword in line_lower for keyword in ['methodology', 'method', 'approach']):
                        if len(line_lower) < 50:  # Likely a header
                            in_method_section = True
                            continue
                    elif any(keyword in line_lower for keyword in ['result', 'experiment', 'evaluation', 'conclusion']):
                        if len(line_lower) < 50:  # Likely a header
                            break
                    
                    if in_method_section and line.strip():
                        method_section.append(line)
                        if len(method_section) > 50:  # Limit section size
                            break
                
                if method_section:
                    content_parts.append(f"Methodology Section: {' '.join(method_section[:2000])}")
        
        content = "\n\n".join(content_parts)
        
        prompt = f"""
        Create a technical summary focusing on the methodology and implementation details:
        
        {content}
        
        Technical Summary should include:
        - Detailed methodology description
        - Technical innovations and contributions
        - Implementation approach
        - Experimental setup
        - Performance metrics and results
        - Technical limitations
        
        Technical Summary:
        """
        
        response = await asyncio.to_thread(self.llm.invoke, prompt)
        return response.content
    
    async def _default_summary(
        self,
        title: str,
        abstract: str,
        request: SummaryRequest
    ) -> str:
        """Generate default summary."""
        
        prompt = f"""
        Summarize this research paper for {request.target_audience} audience:
        
        Title: {title}
        Abstract: {abstract}
        
        Provide a clear summary that includes:
        - Main research question or problem
        - Approach or methodology
        - Key findings
        - Significance or impact
        
        Summary:
        """
        
        response = await asyncio.to_thread(self.llm.invoke, prompt)
        return response.content
    
    async def generate_multiple_summaries(
        self,
        paper_content: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate multiple types of summaries for a paper."""
        
        summaries = {}
        
        # Generate different summary types
        summary_types = [
            ("concise", "intermediate", 150),
            ("comprehensive", "intermediate", 500),
            ("technical", "expert", 400),
            ("beginner", "beginner", 300)
        ]
        
        for summary_type, audience, max_length in summary_types:
            try:
                request = SummaryRequest(
                    text="",  # Will be extracted from paper_content
                    summary_type=summary_type if summary_type != "beginner" else "comprehensive",
                    target_audience=audience,
                    max_length=max_length
                )
                
                summary_result = await self.summarize_paper(paper_content, request)
                summaries[f"{summary_type}_{audience}"] = summary_result
                
            except Exception as e:
                logger.error(f"Failed to generate {summary_type} summary: {e}")
                summaries[f"{summary_type}_{audience}"] = {
                    "error": str(e),
                    "summary": "Summary generation failed"
                }
        
        return {
            "paper_id": paper_content.get("id"),
            "title": paper_content.get("title"),
            "summaries": summaries,
            "generated_at": asyncio.get_event_loop().time()
        }
    
    async def extract_key_insights(
        self,
        paper_content: Dict[str, Any]
    ) -> List[str]:
        """Extract key insights from a paper."""
        
        title = paper_content.get("title", "")
        abstract = paper_content.get("abstract", "")
        
        prompt = f"""
        Extract the top 5 key insights from this research paper:
        
        Title: {title}
        Abstract: {abstract}
        
        Key insights should be:
        - Specific and actionable
        - Novel or surprising findings
        - Important implications
        - Technical breakthroughs
        - Practical applications
        
        List the insights as numbered points:
        """
        
        response = await asyncio.to_thread(self.llm.invoke, prompt)
        
        # Parse insights from response
        insights = []
        lines = response.content.split('\n')
        
        for line in lines:
            line = line.strip()
            if line and (line[0].isdigit() or line.startswith('-') or line.startswith('•')):
                # Clean up the insight
                insight = line.lstrip('0123456789.-• ').strip()
                if insight:
                    insights.append(insight)
        
        return insights[:5]  # Return top 5 insights