"""GitHub repository analysis for research papers."""

import asyncio
import aiohttp
from github import Github
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime
import re
import structlog

logger = structlog.get_logger()


@dataclass
class RepoAnalysis:
    """GitHub repository analysis results."""
    url: str
    name: str
    description: Optional[str]
    stars: int
    forks: int
    language: Optional[str]
    topics: List[str]
    readme_content: Optional[str]
    key_files: List[str]
    has_requirements: bool
    has_dockerfile: bool
    has_notebook: bool
    last_updated: datetime
    license: Optional[str]
    implementation_complexity: str  # beginner, intermediate, expert
    tutorial_quality: float  # 0.0 to 1.0


class GitHubRepoAnalyzer:
    """Analyze GitHub repositories linked to research papers."""
    
    def __init__(self, github_token: Optional[str] = None):
        self.github = Github(github_token) if github_token else Github()
        self.complexity_keywords = {
            'beginner': ['tutorial', 'example', 'demo', 'simple', 'basic'],
            'intermediate': ['implementation', 'model', 'training', 'inference'],
            'expert': ['research', 'paper', 'sota', 'benchmark', 'framework']
        }
    
    async def analyze_repositories(self, github_urls: List[str]) -> List[RepoAnalysis]:
        """Analyze multiple GitHub repositories."""
        analyses = []
        
        for url in github_urls:
            try:
                analysis = await self.analyze_repository(url)
                if analysis:
                    analyses.append(analysis)
            except Exception as e:
                logger.error(f"Error analyzing repository {url}: {e}")
        
        return analyses
    
    async def analyze_repository(self, github_url: str) -> Optional[RepoAnalysis]:
        """Analyze a single GitHub repository."""
        try:
            # Extract owner and repo name from URL
            match = re.match(r'https?://github\.com/([^/]+)/([^/]+)', github_url)
            if not match:
                return None
            
            owner, repo_name = match.groups()
            repo = self.github.get_repo(f"{owner}/{repo_name}")
            
            # Get repository information
            readme_content = await self._get_readme_content(repo)
            key_files = await self._analyze_key_files(repo)
            complexity = self._assess_complexity(readme_content, key_files)
            tutorial_quality = self._assess_tutorial_quality(readme_content, key_files)
            
            return RepoAnalysis(
                url=github_url,
                name=repo.name,
                description=repo.description,
                stars=repo.stargazers_count,
                forks=repo.forks_count,
                language=repo.language,
                topics=repo.get_topics(),
                readme_content=readme_content,
                key_files=key_files,
                has_requirements=self._has_file(repo, ['requirements.txt', 'environment.yml', 'pyproject.toml']),
                has_dockerfile=self._has_file(repo, ['Dockerfile', 'docker-compose.yml']),
                has_notebook=self._has_file(repo, ['.ipynb']),
                last_updated=repo.updated_at,
                license=repo.license.name if repo.license else None,
                implementation_complexity=complexity,
                tutorial_quality=tutorial_quality
            )
        
        except Exception as e:
            logger.error(f"Error analyzing repository {github_url}: {e}")
            return None
    
    async def _get_readme_content(self, repo) -> Optional[str]:
        """Get README content from repository."""
        try:
            readme_files = ['README.md', 'README.rst', 'README.txt', 'README']
            
            for readme_file in readme_files:
                try:
                    content = repo.get_contents(readme_file)
                    return content.decoded_content.decode('utf-8')
                except:
                    continue
            
            return None
        except Exception as e:
            logger.error(f"Error getting README: {e}")
            return None
    
    async def _analyze_key_files(self, repo) -> List[str]:
        """Analyze key files in the repository."""
        key_files = []
        
        try:
            contents = repo.get_contents("")
            
            important_patterns = [
                r'.*\.py$',  # Python files
                r'.*\.ipynb$',  # Jupyter notebooks
                r'requirements\.txt$',
                r'environment\.yml$',
                r'Dockerfile$',
                r'.*\.md$',  # Documentation
                r'train.*\.py$',  # Training scripts
                r'model.*\.py$',  # Model files
                r'config.*\.(py|json|yaml)$'  # Configuration files
            ]
            
            for content_file in contents:
                if content_file.type == "file":
                    for pattern in important_patterns:
                        if re.match(pattern, content_file.name, re.IGNORECASE):
                            key_files.append(content_file.name)
                            break
            
            # Also check subdirectories for important files
            for content_file in contents:
                if content_file.type == "dir" and content_file.name in ['src', 'models', 'scripts', 'examples']:
                    try:
                        subdir_contents = repo.get_contents(content_file.path)
                        for subfile in subdir_contents:
                            if subfile.type == "file":
                                for pattern in important_patterns:
                                    if re.match(pattern, subfile.name, re.IGNORECASE):
                                        key_files.append(f"{content_file.name}/{subfile.name}")
                                        break
                    except:
                        continue
        
        except Exception as e:
            logger.error(f"Error analyzing key files: {e}")
        
        return key_files[:20]  # Limit to top 20 files
    
    def _has_file(self, repo, filenames: List[str]) -> bool:
        """Check if repository has any of the specified files."""
        try:
            contents = repo.get_contents("")
            repo_files = [f.name.lower() for f in contents if f.type == "file"]
            
            for filename in filenames:
                if filename.lower() in repo_files:
                    return True
                
                # Check for pattern matches (e.g., .ipynb extension)
                if filename.startswith('.'):
                    for repo_file in repo_files:
                        if repo_file.endswith(filename):
                            return True
            
            return False
        except:
            return False
    
    def _assess_complexity(self, readme_content: Optional[str], key_files: List[str]) -> str:
        """Assess implementation complexity based on content."""
        if not readme_content:
            readme_content = ""
        
        readme_lower = readme_content.lower()
        
        # Count complexity indicators
        beginner_score = sum(1 for keyword in self.complexity_keywords['beginner'] 
                           if keyword in readme_lower)
        intermediate_score = sum(1 for keyword in self.complexity_keywords['intermediate'] 
                               if keyword in readme_lower)
        expert_score = sum(1 for keyword in self.complexity_keywords['expert'] 
                         if keyword in readme_lower)
        
        # Adjust scores based on file structure
        if any('train' in f.lower() for f in key_files):
            intermediate_score += 2
        if any('model' in f.lower() for f in key_files):
            intermediate_score += 1
        if len(key_files) > 10:
            expert_score += 1
        if any('.ipynb' in f for f in key_files):
            beginner_score += 1
        
        # Determine complexity
        if beginner_score >= max(intermediate_score, expert_score):
            return "beginner"
        elif expert_score > intermediate_score:
            return "expert"
        else:
            return "intermediate"
    
    def _assess_tutorial_quality(self, readme_content: Optional[str], key_files: List[str]) -> float:
        """Assess tutorial quality (0.0 to 1.0)."""
        if not readme_content:
            return 0.0
        
        quality_score = 0.0
        readme_lower = readme_content.lower()
        
        # Check for tutorial elements
        tutorial_indicators = [
            'installation', 'usage', 'example', 'getting started',
            'quick start', 'tutorial', 'demo', 'how to', 'step by step'
        ]
        
        for indicator in tutorial_indicators:
            if indicator in readme_lower:
                quality_score += 0.1
        
        # Check for code examples
        if '```' in readme_content or '    ' in readme_content:  # Code blocks
            quality_score += 0.2
        
        # Check for images/diagrams
        if any(ext in readme_lower for ext in ['.png', '.jpg', '.gif', '.svg']):
            quality_score += 0.1
        
        # Check for example files
        if any('example' in f.lower() or 'demo' in f.lower() for f in key_files):
            quality_score += 0.2
        
        # Check for notebooks
        if any('.ipynb' in f for f in key_files):
            quality_score += 0.2
        
        # Check README length (longer usually means more detailed)
        if len(readme_content) > 1000:
            quality_score += 0.1
        if len(readme_content) > 3000:
            quality_score += 0.1
        
        return min(1.0, quality_score)