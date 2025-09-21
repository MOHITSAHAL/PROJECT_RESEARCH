"""
Topic Modeling Service for Research Area Identification
Provides advanced topic discovery and research area classification
"""

from typing import List, Dict, Any, Optional
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import LatentDirichletAllocation
import logging

logger = logging.getLogger(__name__)

class TopicModeler:
    """Advanced topic modeling for research area identification"""
    
    def __init__(self, n_topics: int = 10, max_features: int = 1000):
        self.n_topics = n_topics
        self.max_features = max_features
        self.vectorizer = None
        self.lda_model = None
        self.feature_names = None
        
    def fit_topics(self, papers: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Fit topic model on research papers"""
        try:
            # Prepare text data
            texts = self._prepare_texts(papers)
            
            # Vectorize texts
            self.vectorizer = TfidfVectorizer(
                max_features=self.max_features,
                stop_words='english',
                ngram_range=(1, 2),
                min_df=2,
                max_df=0.8
            )
            
            doc_term_matrix = self.vectorizer.fit_transform(texts)
            self.feature_names = self.vectorizer.get_feature_names_out()
            
            # Fit LDA model
            self.lda_model = LatentDirichletAllocation(
                n_components=self.n_topics,
                random_state=42,
                max_iter=100
            )
            
            self.lda_model.fit(doc_term_matrix)
            
            # Extract topics
            topics = self._extract_topics()
            
            # Assign papers to topics
            paper_topics = self._assign_paper_topics(papers, doc_term_matrix)
            
            return {
                "topics": topics,
                "paper_topics": paper_topics,
                "n_topics": self.n_topics,
                "perplexity": self.lda_model.perplexity(doc_term_matrix)
            }
            
        except Exception as e:
            logger.error(f"Error fitting topic model: {e}")
            raise
    
    def _prepare_texts(self, papers: List[Dict[str, Any]]) -> List[str]:
        """Prepare text data for topic modeling"""
        texts = []
        for paper in papers:
            text_parts = []
            
            if paper.get('title'):
                text_parts.append(paper['title'])
            if paper.get('abstract'):
                text_parts.append(paper['abstract'])
            if paper.get('keywords'):
                if isinstance(paper['keywords'], list):
                    text_parts.extend(paper['keywords'])
                else:
                    text_parts.append(paper['keywords'])
            
            texts.append(" ".join(text_parts))
        
        return texts
    
    def _extract_topics(self, n_words: int = 10) -> List[Dict[str, Any]]:
        """Extract topic information from fitted model"""
        topics = []
        
        for topic_idx, topic in enumerate(self.lda_model.components_):
            # Get top words for topic
            top_words_idx = topic.argsort()[-n_words:][::-1]
            top_words = [self.feature_names[i] for i in top_words_idx]
            top_weights = [topic[i] for i in top_words_idx]
            
            # Generate topic name from top words
            topic_name = " & ".join(top_words[:3]).title()
            
            topics.append({
                "id": topic_idx,
                "name": topic_name,
                "words": top_words,
                "weights": top_weights,
                "description": f"Research topic focusing on {topic_name.lower()}"
            })
        
        return topics
    
    def _assign_paper_topics(self, papers: List[Dict[str, Any]], 
                           doc_term_matrix) -> List[Dict[str, Any]]:
        """Assign papers to topics with probabilities"""
        topic_distributions = self.lda_model.transform(doc_term_matrix)
        
        paper_topics = []
        for i, paper in enumerate(papers):
            distribution = topic_distributions[i]
            
            # Get dominant topic
            dominant_topic = np.argmax(distribution)
            confidence = distribution[dominant_topic]
            
            # Get all topic probabilities
            topic_probs = {
                f"topic_{j}": float(prob) 
                for j, prob in enumerate(distribution)
            }
            
            paper_topics.append({
                "paper_id": paper.get('id', i),
                "title": paper.get('title', ''),
                "dominant_topic": int(dominant_topic),
                "confidence": float(confidence),
                "topic_probabilities": topic_probs
            })
        
        return paper_topics
    
    def predict_topics(self, new_papers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Predict topics for new papers"""
        if not self.vectorizer or not self.lda_model:
            raise ValueError("Model not fitted. Call fit_topics first.")
        
        try:
            texts = self._prepare_texts(new_papers)
            doc_term_matrix = self.vectorizer.transform(texts)
            
            return self._assign_paper_topics(new_papers, doc_term_matrix)
            
        except Exception as e:
            logger.error(f"Error predicting topics: {e}")
            raise
    
    def get_topic_evolution(self, papers_by_year: Dict[int, List[Dict[str, Any]]]) -> Dict[str, Any]:
        """Analyze topic evolution over time"""
        try:
            evolution = {}
            
            for year, papers in papers_by_year.items():
                if not papers:
                    continue
                
                # Fit topics for this year
                year_model = TopicModeler(n_topics=self.n_topics)
                year_results = year_model.fit_topics(papers)
                
                evolution[year] = {
                    "topics": year_results["topics"],
                    "paper_count": len(papers),
                    "dominant_topics": self._get_dominant_topics(year_results["paper_topics"])
                }
            
            return {
                "evolution": evolution,
                "trend_analysis": self._analyze_trends(evolution)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing topic evolution: {e}")
            raise
    
    def _get_dominant_topics(self, paper_topics: List[Dict[str, Any]]) -> Dict[int, int]:
        """Get count of papers per dominant topic"""
        topic_counts = {}
        for paper_topic in paper_topics:
            topic_id = paper_topic["dominant_topic"]
            topic_counts[topic_id] = topic_counts.get(topic_id, 0) + 1
        
        return topic_counts
    
    def _analyze_trends(self, evolution: Dict[int, Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze trends in topic evolution"""
        years = sorted(evolution.keys())
        if len(years) < 2:
            return {"message": "Insufficient data for trend analysis"}
        
        # Track topic popularity over time
        topic_trends = {}
        for year in years:
            dominant_topics = evolution[year]["dominant_topics"]
            total_papers = evolution[year]["paper_count"]
            
            for topic_id, count in dominant_topics.items():
                if topic_id not in topic_trends:
                    topic_trends[topic_id] = []
                
                percentage = (count / total_papers) * 100 if total_papers > 0 else 0
                topic_trends[topic_id].append({
                    "year": year,
                    "percentage": percentage,
                    "count": count
                })
        
        # Identify trending topics
        trending_up = []
        trending_down = []
        
        for topic_id, trend_data in topic_trends.items():
            if len(trend_data) >= 2:
                recent_trend = trend_data[-1]["percentage"] - trend_data[-2]["percentage"]
                if recent_trend > 5:  # 5% increase
                    trending_up.append({"topic_id": topic_id, "change": recent_trend})
                elif recent_trend < -5:  # 5% decrease
                    trending_down.append({"topic_id": topic_id, "change": recent_trend})
        
        return {
            "topic_trends": topic_trends,
            "trending_up": sorted(trending_up, key=lambda x: x["change"], reverse=True),
            "trending_down": sorted(trending_down, key=lambda x: x["change"])
        }