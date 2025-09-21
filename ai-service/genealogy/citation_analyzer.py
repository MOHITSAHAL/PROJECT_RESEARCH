"""
Citation Analysis Service for Research Genealogy
Provides paper influence and relationship analysis
"""

import networkx as nx
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from collections import defaultdict, deque
import logging

logger = logging.getLogger(__name__)

class CitationAnalyzer:
    """Advanced citation analysis for research genealogy"""
    
    def __init__(self):
        self.citation_graph = nx.DiGraph()
        self.paper_metadata = {}
        
    def build_citation_network(self, papers: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Build citation network from papers"""
        try:
            self.citation_graph.clear()
            self.paper_metadata = {}
            
            # Add papers as nodes
            for paper in papers:
                paper_id = paper.get('id') or paper.get('arxiv_id', '')
                if not paper_id:
                    continue
                
                self.citation_graph.add_node(paper_id)
                self.paper_metadata[paper_id] = paper
            
            # Add citation edges
            for paper in papers:
                paper_id = paper.get('id') or paper.get('arxiv_id', '')
                if not paper_id:
                    continue
                
                citations = paper.get('citations', [])
                references = paper.get('references', [])
                
                # Add outgoing citations (this paper cites others)
                for cited_id in citations:
                    if cited_id in self.citation_graph:
                        self.citation_graph.add_edge(paper_id, cited_id)
                
                # Add incoming citations (others cite this paper)
                for ref_id in references:
                    if ref_id in self.citation_graph:
                        self.citation_graph.add_edge(ref_id, paper_id)
            
            # Calculate network metrics
            metrics = self._calculate_network_metrics()
            
            return {
                "network_stats": {
                    "nodes": self.citation_graph.number_of_nodes(),
                    "edges": self.citation_graph.number_of_edges(),
                    "density": nx.density(self.citation_graph),
                    "connected_components": nx.number_weakly_connected_components(self.citation_graph)
                },
                "metrics": metrics,
                "influential_papers": self._find_influential_papers(),
                "research_lineages": self._trace_research_lineages()
            }
            
        except Exception as e:
            logger.error(f"Error building citation network: {e}")
            raise
    
    def _calculate_network_metrics(self) -> Dict[str, Dict[str, float]]:
        """Calculate various network centrality metrics"""
        metrics = {}
        
        try:
            # PageRank (paper influence)
            pagerank = nx.pagerank(self.citation_graph)
            
            # In-degree centrality (citation count)
            in_degree = dict(self.citation_graph.in_degree())
            
            # Out-degree centrality (reference count)
            out_degree = dict(self.citation_graph.out_degree())
            
            # Betweenness centrality (bridging papers)
            betweenness = nx.betweenness_centrality(self.citation_graph)
            
            # Closeness centrality (accessibility)
            closeness = nx.closeness_centrality(self.citation_graph)
            
            for paper_id in self.citation_graph.nodes():
                metrics[paper_id] = {
                    "pagerank": pagerank.get(paper_id, 0),
                    "citations": in_degree.get(paper_id, 0),
                    "references": out_degree.get(paper_id, 0),
                    "betweenness": betweenness.get(paper_id, 0),
                    "closeness": closeness.get(paper_id, 0)
                }
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error calculating network metrics: {e}")
            return {}
    
    def _find_influential_papers(self, top_k: int = 20) -> List[Dict[str, Any]]:
        """Find most influential papers based on multiple metrics"""
        try:
            paper_scores = []
            
            for paper_id in self.citation_graph.nodes():
                paper = self.paper_metadata.get(paper_id, {})
                
                # Calculate composite influence score
                pagerank = nx.pagerank(self.citation_graph).get(paper_id, 0)
                citations = self.citation_graph.in_degree(paper_id)
                betweenness = nx.betweenness_centrality(self.citation_graph).get(paper_id, 0)
                
                # Weighted composite score
                influence_score = (
                    0.5 * pagerank * 1000 +  # Scale PageRank
                    0.3 * citations +
                    0.2 * betweenness * 100  # Scale betweenness
                )
                
                paper_scores.append({
                    "paper_id": paper_id,
                    "title": paper.get('title', ''),
                    "authors": paper.get('authors', []),
                    "year": paper.get('published_year'),
                    "influence_score": influence_score,
                    "citations": citations,
                    "pagerank": pagerank,
                    "betweenness": betweenness
                })
            
            # Sort by influence score
            paper_scores.sort(key=lambda x: x["influence_score"], reverse=True)
            
            return paper_scores[:top_k]
            
        except Exception as e:
            logger.error(f"Error finding influential papers: {e}")
            return []
    
    def _trace_research_lineages(self) -> List[Dict[str, Any]]:
        """Trace research lineages from foundational to recent papers"""
        try:
            lineages = []
            
            # Find foundational papers (high out-degree, low in-degree, early years)
            foundational_candidates = []
            
            for paper_id in self.citation_graph.nodes():
                paper = self.paper_metadata.get(paper_id, {})
                in_degree = self.citation_graph.in_degree(paper_id)
                out_degree = self.citation_graph.out_degree(paper_id)
                year = paper.get('published_year', 2024)
                
                # Foundational criteria: early papers with many references but few citations
                if year < 2020 and out_degree > 10 and in_degree < 5:
                    foundational_candidates.append({
                        "paper_id": paper_id,
                        "year": year,
                        "out_degree": out_degree,
                        "in_degree": in_degree
                    })
            
            # Sort by year and influence
            foundational_candidates.sort(key=lambda x: (x["year"], -x["out_degree"]))
            
            # Trace lineages from foundational papers
            for foundation in foundational_candidates[:10]:  # Top 10 foundational papers
                lineage = self._trace_lineage_from_paper(foundation["paper_id"])
                if len(lineage) > 2:  # Only include substantial lineages
                    lineages.append({
                        "foundation_paper": foundation["paper_id"],
                        "lineage": lineage,
                        "length": len(lineage),
                        "span_years": self._calculate_year_span(lineage)
                    })
            
            return lineages
            
        except Exception as e:
            logger.error(f"Error tracing research lineages: {e}")
            return []
    
    def _trace_lineage_from_paper(self, start_paper_id: str, max_depth: int = 5) -> List[Dict[str, Any]]:
        """Trace research lineage from a starting paper"""
        lineage = []
        visited = set()
        queue = deque([(start_paper_id, 0)])
        
        while queue and len(lineage) < 20:  # Limit lineage length
            paper_id, depth = queue.popleft()
            
            if paper_id in visited or depth > max_depth:
                continue
            
            visited.add(paper_id)
            paper = self.paper_metadata.get(paper_id, {})
            
            lineage.append({
                "paper_id": paper_id,
                "title": paper.get('title', ''),
                "year": paper.get('published_year'),
                "depth": depth,
                "citations": self.citation_graph.in_degree(paper_id)
            })
            
            # Add papers that cite this one (research evolution)
            for successor in self.citation_graph.predecessors(paper_id):
                if successor not in visited:
                    queue.append((successor, depth + 1))
        
        # Sort by year to show chronological evolution
        lineage.sort(key=lambda x: x.get('year', 0))
        
        return lineage
    
    def _calculate_year_span(self, lineage: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate year span of a research lineage"""
        years = [paper.get('year') for paper in lineage if paper.get('year')]
        
        if not years:
            return {"start": None, "end": None, "span": 0}
        
        return {
            "start": min(years),
            "end": max(years),
            "span": max(years) - min(years)
        }
    
    def analyze_paper_impact(self, paper_id: str) -> Dict[str, Any]:
        """Analyze the impact and influence of a specific paper"""
        try:
            if paper_id not in self.citation_graph:
                return {"error": "Paper not found in citation network"}
            
            paper = self.paper_metadata.get(paper_id, {})
            
            # Direct metrics
            direct_citations = list(self.citation_graph.predecessors(paper_id))
            direct_references = list(self.citation_graph.successors(paper_id))
            
            # Indirect influence (papers citing papers that cite this one)
            indirect_citations = set()
            for citing_paper in direct_citations:
                indirect_citations.update(self.citation_graph.predecessors(citing_paper))
            indirect_citations.discard(paper_id)  # Remove self
            
            # Calculate metrics
            pagerank = nx.pagerank(self.citation_graph).get(paper_id, 0)
            betweenness = nx.betweenness_centrality(self.citation_graph).get(paper_id, 0)
            
            return {
                "paper_info": {
                    "id": paper_id,
                    "title": paper.get('title', ''),
                    "authors": paper.get('authors', []),
                    "year": paper.get('published_year')
                },
                "direct_impact": {
                    "citations": len(direct_citations),
                    "references": len(direct_references),
                    "citing_papers": [self.paper_metadata.get(pid, {}).get('title', pid) 
                                    for pid in direct_citations[:10]]
                },
                "indirect_impact": {
                    "indirect_citations": len(indirect_citations),
                    "influence_reach": len(direct_citations) + len(indirect_citations)
                },
                "network_position": {
                    "pagerank": pagerank,
                    "betweenness": betweenness,
                    "influence_rank": self._get_influence_rank(paper_id)
                }
            }
            
        except Exception as e:
            logger.error(f"Error analyzing paper impact: {e}")
            return {"error": str(e)}
    
    def _get_influence_rank(self, paper_id: str) -> int:
        """Get the influence rank of a paper among all papers"""
        pagerank_scores = nx.pagerank(self.citation_graph)
        sorted_papers = sorted(pagerank_scores.items(), key=lambda x: x[1], reverse=True)
        
        for rank, (pid, score) in enumerate(sorted_papers, 1):
            if pid == paper_id:
                return rank
        
        return len(sorted_papers) + 1