"""PDF processing for research papers."""

import asyncio
import aiohttp
from typing import Optional, Dict, Any, List
import PyPDF2
import pdfplumber
import re
from dataclasses import dataclass
import structlog

logger = structlog.get_logger()


@dataclass
class ProcessedPaper:
    """Processed paper content."""
    full_text: str
    sections: Dict[str, str]
    references: List[str]
    github_urls: List[str]
    methodology: List[str]
    key_findings: List[str]
    figures_count: int
    tables_count: int


class PDFProcessor:
    """Process PDF papers to extract structured content."""
    
    def __init__(self):
        self.github_pattern = re.compile(
            r'https?://(?:www\.)?github\.com/[\w\-\.]+/[\w\-\.]+',
            re.IGNORECASE
        )
        self.section_patterns = {
            'abstract': re.compile(r'\babstract\b', re.IGNORECASE),
            'introduction': re.compile(r'\bintroduction\b', re.IGNORECASE),
            'methodology': re.compile(r'\b(?:methodology|method|approach)\b', re.IGNORECASE),
            'results': re.compile(r'\b(?:results|experiments|evaluation)\b', re.IGNORECASE),
            'conclusion': re.compile(r'\b(?:conclusion|discussion)\b', re.IGNORECASE),
            'references': re.compile(r'\b(?:references|bibliography)\b', re.IGNORECASE)
        }
    
    async def download_and_process_pdf(self, pdf_url: str) -> Optional[ProcessedPaper]:
        """Download PDF and extract structured content."""
        try:
            pdf_content = await self._download_pdf(pdf_url)
            if not pdf_content:
                return None
            
            return await self._process_pdf_content(pdf_content)
        except Exception as e:
            logger.error(f"Error processing PDF {pdf_url}: {e}")
            return None
    
    async def _download_pdf(self, pdf_url: str) -> Optional[bytes]:
        """Download PDF content."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(pdf_url) as response:
                    if response.status == 200:
                        return await response.read()
            return None
        except Exception as e:
            logger.error(f"Error downloading PDF {pdf_url}: {e}")
            return None
    
    async def _process_pdf_content(self, pdf_content: bytes) -> ProcessedPaper:
        """Extract structured content from PDF."""
        # Use pdfplumber for better text extraction
        full_text = ""
        sections = {}
        figures_count = 0
        tables_count = 0
        
        try:
            import io
            with pdfplumber.open(io.BytesIO(pdf_content)) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        full_text += page_text + "\n"
                    
                    # Count figures and tables
                    figures_count += len(page.images)
                    tables_count += len(page.extract_tables())
        except Exception as e:
            logger.warning(f"pdfplumber failed, trying PyPDF2: {e}")
            # Fallback to PyPDF2
            try:
                import io
                pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_content))
                for page in pdf_reader.pages:
                    full_text += page.extract_text() + "\n"
            except Exception as e2:
                logger.error(f"Both PDF processors failed: {e2}")
                full_text = ""
        
        # Extract sections
        sections = self._extract_sections(full_text)
        
        # Extract GitHub URLs
        github_urls = self._extract_github_urls(full_text)
        
        # Extract references
        references = self._extract_references(full_text)
        
        # Extract methodology keywords
        methodology = self._extract_methodology(sections.get('methodology', ''))
        
        # Extract key findings
        key_findings = self._extract_key_findings(sections.get('results', ''))
        
        return ProcessedPaper(
            full_text=full_text,
            sections=sections,
            references=references,
            github_urls=github_urls,
            methodology=methodology,
            key_findings=key_findings,
            figures_count=figures_count,
            tables_count=tables_count
        )
    
    def _extract_sections(self, text: str) -> Dict[str, str]:
        """Extract paper sections."""
        sections = {}
        lines = text.split('\n')
        current_section = None
        current_content = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Check if line is a section header
            section_found = None
            for section_name, pattern in self.section_patterns.items():
                if pattern.search(line) and len(line) < 50:  # Likely a header
                    section_found = section_name
                    break
            
            if section_found:
                # Save previous section
                if current_section and current_content:
                    sections[current_section] = '\n'.join(current_content)
                
                current_section = section_found
                current_content = []
            elif current_section:
                current_content.append(line)
        
        # Save last section
        if current_section and current_content:
            sections[current_section] = '\n'.join(current_content)
        
        return sections
    
    def _extract_github_urls(self, text: str) -> List[str]:
        """Extract GitHub repository URLs."""
        urls = self.github_pattern.findall(text)
        return list(set(urls))  # Remove duplicates
    
    def _extract_references(self, text: str) -> List[str]:
        """Extract paper references."""
        references = []
        
        # Look for reference section
        ref_section = None
        for section_name, content in self._extract_sections(text).items():
            if 'reference' in section_name.lower():
                ref_section = content
                break
        
        if ref_section:
            # Split by common reference patterns
            ref_lines = re.split(r'\n(?=\[\d+\]|\d+\.)', ref_section)
            references = [ref.strip() for ref in ref_lines if ref.strip()]
        
        return references[:50]  # Limit to first 50 references
    
    def _extract_methodology(self, methodology_text: str) -> List[str]:
        """Extract methodology keywords."""
        if not methodology_text:
            return []
        
        # Common ML/AI methodology terms
        method_keywords = [
            'neural network', 'deep learning', 'machine learning', 'transformer',
            'attention', 'convolution', 'lstm', 'gru', 'bert', 'gpt',
            'reinforcement learning', 'supervised learning', 'unsupervised learning',
            'classification', 'regression', 'clustering', 'optimization',
            'gradient descent', 'backpropagation', 'fine-tuning', 'pre-training'
        ]
        
        found_methods = []
        text_lower = methodology_text.lower()
        
        for keyword in method_keywords:
            if keyword in text_lower:
                found_methods.append(keyword)
        
        return found_methods
    
    def _extract_key_findings(self, results_text: str) -> List[str]:
        """Extract key findings from results section."""
        if not results_text:
            return []
        
        findings = []
        
        # Look for sentences with performance metrics
        metric_patterns = [
            r'accuracy of (\d+\.?\d*%?)',
            r'f1[- ]score of (\d+\.?\d*)',
            r'precision of (\d+\.?\d*%?)',
            r'recall of (\d+\.?\d*%?)',
            r'improved? by (\d+\.?\d*%?)',
            r'outperform[s]? .* by (\d+\.?\d*%?)',
            r'achieve[s]? (\d+\.?\d*%?) accuracy'
        ]
        
        for pattern in metric_patterns:
            matches = re.finditer(pattern, results_text, re.IGNORECASE)
            for match in matches:
                # Get surrounding context
                start = max(0, match.start() - 100)
                end = min(len(results_text), match.end() + 100)
                context = results_text[start:end].strip()
                findings.append(context)
        
        return findings[:10]  # Limit to top 10 findings