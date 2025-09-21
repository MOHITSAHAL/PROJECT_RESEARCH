"""
Semantic Clustering Service for Research Papers
Provides AI-powered paper grouping and topic modeling
"""

import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from sklearn.cluster import KMeans, DBSCAN
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score
from sentence_transformers import SentenceTransformer
import logging

logger = logging.getLogger(__name__)

class SemanticClusterer:
    """AI-powered semantic clustering for research papers"""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)
        self.embeddings_cache = {}
        
    def generate_embeddings(self, texts: List[str]) -> np.ndarray:
        """Generate semantic embeddings for texts"""
        try:
            embeddings = self.model.encode(texts, convert_to_tensor=False)
            return np.array(embeddings)
        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            raise
    
    def cluster_papers(self, papers: List[Dict[str, Any]], 
                      method: str = "kmeans", 
                      n_clusters: Optional[int] = None) -> Dict[str, Any]:
        """Cluster papers using semantic similarity"""
        try:
            # Extract text for clustering
            texts = [f"{paper.get('title', '')} {paper.get('abstract', '')}" 
                    for paper in papers]
            
            # Generate embeddings
            embeddings = self.generate_embeddings(texts)
            
            # Perform clustering
            if method == "kmeans":
                clusters, labels = self._kmeans_clustering(embeddings, n_clusters)
            elif method == "dbscan":
                clusters, labels = self._dbscan_clustering(embeddings)
            else:
                raise ValueError(f"Unknown clustering method: {method}")
            
            # Organize results
            clustered_papers = self._organize_clusters(papers, labels)
            cluster_topics = self._extract_cluster_topics(clustered_papers, embeddings, labels)
            
            return {
                "clusters": clustered_papers,
                "topics": cluster_topics,
                "embeddings": embeddings.tolist(),
                "labels": labels.tolist(),
                "method": method,
                "n_clusters": len(set(labels))
            }
            
        except Exception as e:
            logger.error(f"Error clustering papers: {e}")
            raise
    
    def _kmeans_clustering(self, embeddings: np.ndarray, 
                          n_clusters: Optional[int] = None) -> Tuple[Any, np.ndarray]:
        """Perform K-means clustering"""
        if n_clusters is None:
            n_clusters = self._optimal_clusters(embeddings)
        
        kmeans = KMeans(n_clusters=n_clusters, random_state=42)
        labels = kmeans.fit_predict(embeddings)
        
        return kmeans, labels
    
    def _dbscan_clustering(self, embeddings: np.ndarray) -> Tuple[Any, np.ndarray]:
        """Perform DBSCAN clustering"""
        dbscan = DBSCAN(eps=0.5, min_samples=2)
        labels = dbscan.fit_predict(embeddings)
        
        return dbscan, labels
    
    def _optimal_clusters(self, embeddings: np.ndarray, max_k: int = 10) -> int:
        """Find optimal number of clusters using silhouette score"""
        best_k = 2
        best_score = -1
        
        for k in range(2, min(max_k + 1, len(embeddings))):
            kmeans = KMeans(n_clusters=k, random_state=42)
            labels = kmeans.fit_predict(embeddings)
            score = silhouette_score(embeddings, labels)
            
            if score > best_score:
                best_score = score
                best_k = k
        
        return best_k
    
    def _organize_clusters(self, papers: List[Dict[str, Any]], 
                          labels: np.ndarray) -> Dict[int, List[Dict[str, Any]]]:
        """Organize papers by cluster labels"""
        clusters = {}
        for paper, label in zip(papers, labels):
            if label not in clusters:
                clusters[label] = []
            clusters[label].append(paper)
        
        return clusters
    
    def _extract_cluster_topics(self, clustered_papers: Dict[int, List[Dict[str, Any]]], 
                               embeddings: np.ndarray, 
                               labels: np.ndarray) -> Dict[int, Dict[str, Any]]:
        """Extract topics for each cluster"""
        topics = {}
        
        for cluster_id, papers in clustered_papers.items():
            if cluster_id == -1:  # Noise cluster in DBSCAN
                topics[cluster_id] = {"name": "Uncategorized", "keywords": [], "description": ""}
                continue
            
            # Extract keywords from titles and abstracts
            cluster_texts = [f"{paper.get('title', '')} {paper.get('abstract', '')}" 
                           for paper in papers]
            
            # Simple keyword extraction (can be enhanced with more sophisticated NLP)
            all_text = " ".join(cluster_texts).lower()
            words = all_text.split()
            word_freq = {}
            for word in words:
                if len(word) > 3:  # Filter short words
                    word_freq[word] = word_freq.get(word, 0) + 1
            
            # Get top keywords
            top_keywords = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:10]
            keywords = [word for word, freq in top_keywords]
            
            # Generate cluster name from top keywords
            cluster_name = " & ".join(keywords[:3]).title()
            
            topics[cluster_id] = {
                "name": cluster_name,
                "keywords": keywords,
                "description": f"Cluster containing {len(papers)} papers related to {cluster_name}",
                "paper_count": len(papers)
            }
        
        return topics
    
    def find_similar_papers(self, target_paper: Dict[str, Any], 
                           papers: List[Dict[str, Any]], 
                           top_k: int = 5) -> List[Dict[str, Any]]:
        """Find papers similar to target paper"""
        try:
            target_text = f"{target_paper.get('title', '')} {target_paper.get('abstract', '')}"
            paper_texts = [f"{paper.get('title', '')} {paper.get('abstract', '')}" 
                          for paper in papers]
            
            # Generate embeddings
            all_texts = [target_text] + paper_texts
            embeddings = self.generate_embeddings(all_texts)
            
            # Calculate similarities
            target_embedding = embeddings[0]
            paper_embeddings = embeddings[1:]
            
            similarities = np.dot(paper_embeddings, target_embedding) / (
                np.linalg.norm(paper_embeddings, axis=1) * np.linalg.norm(target_embedding)
            )
            
            # Get top similar papers
            top_indices = np.argsort(similarities)[::-1][:top_k]
            similar_papers = []
            
            for idx in top_indices:
                paper = papers[idx].copy()
                paper['similarity_score'] = float(similarities[idx])
                similar_papers.append(paper)
            
            return similar_papers
            
        except Exception as e:
            logger.error(f"Error finding similar papers: {e}")
            raise