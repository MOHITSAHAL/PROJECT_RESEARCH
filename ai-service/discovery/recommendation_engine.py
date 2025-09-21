"""
Recommendation Engine for Personalized Paper Discovery
Provides AI-powered paper recommendations and research suggestions
"""

import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)

class RecommendationEngine:
    """AI-powered recommendation system for research papers"""
    
    def __init__(self):
        self.user_profiles = {}
        self.paper_embeddings = {}
        self.interaction_matrix = defaultdict(dict)
        self.vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
        
    def build_user_profile(self, user_id: str, interactions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Build user research profile from interactions"""
        try:
            profile = {
                "user_id": user_id,
                "interests": defaultdict(float),
                "preferred_authors": defaultdict(int),
                "research_areas": defaultdict(float),
                "interaction_history": interactions,
                "expertise_level": self._estimate_expertise_level(interactions)
            }
            
            # Analyze interactions to build profile
            for interaction in interactions:
                paper = interaction.get('paper', {})
                action = interaction.get('action', '')
                weight = self._get_action_weight(action)
                
                # Extract interests from paper content
                if paper.get('keywords'):
                    for keyword in paper['keywords']:
                        profile["interests"][keyword.lower()] += weight
                
                # Track preferred authors
                if paper.get('authors'):
                    for author in paper['authors']:
                        profile["preferred_authors"][author] += 1
                
                # Track research areas
                if paper.get('categories'):
                    for category in paper['categories']:
                        profile["research_areas"][category] += weight
            
            # Normalize scores
            profile["interests"] = dict(profile["interests"])
            profile["preferred_authors"] = dict(profile["preferred_authors"])
            profile["research_areas"] = dict(profile["research_areas"])
            
            self.user_profiles[user_id] = profile
            return profile
            
        except Exception as e:
            logger.error(f"Error building user profile: {e}")
            raise
    
    def _get_action_weight(self, action: str) -> float:
        """Get weight for different user actions"""
        weights = {
            "view": 1.0,
            "bookmark": 2.0,
            "download": 3.0,
            "cite": 4.0,
            "share": 2.5,
            "rate_positive": 3.5,
            "rate_negative": -1.0,
            "chat_with_agent": 2.0
        }
        return weights.get(action, 1.0)
    
    def _estimate_expertise_level(self, interactions: List[Dict[str, Any]]) -> str:
        """Estimate user expertise level from interactions"""
        if len(interactions) < 5:
            return "beginner"
        elif len(interactions) < 20:
            return "intermediate"
        else:
            # Check for advanced indicators
            advanced_actions = sum(1 for i in interactions 
                                 if i.get('action') in ['cite', 'download', 'rate_positive'])
            if advanced_actions > len(interactions) * 0.3:
                return "expert"
            return "intermediate"
    
    def recommend_papers(self, user_id: str, papers: List[Dict[str, Any]], 
                        top_k: int = 10, method: str = "hybrid") -> List[Dict[str, Any]]:
        """Generate personalized paper recommendations"""
        try:
            if user_id not in self.user_profiles:
                return self._cold_start_recommendations(papers, top_k)
            
            user_profile = self.user_profiles[user_id]
            
            if method == "content":
                return self._content_based_recommendations(user_profile, papers, top_k)
            elif method == "collaborative":
                return self._collaborative_recommendations(user_id, papers, top_k)
            else:  # hybrid
                return self._hybrid_recommendations(user_profile, papers, top_k)
                
        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            return []
    
    def _content_based_recommendations(self, user_profile: Dict[str, Any], 
                                     papers: List[Dict[str, Any]], 
                                     top_k: int) -> List[Dict[str, Any]]:
        """Content-based recommendations using user interests"""
        recommendations = []
        
        for paper in papers:
            score = self._calculate_content_score(user_profile, paper)
            
            if score > 0:
                recommendations.append({
                    **paper,
                    "recommendation_score": score,
                    "recommendation_reason": self._generate_content_reason(user_profile, paper)
                })
        
        # Sort by score and return top k
        recommendations.sort(key=lambda x: x["recommendation_score"], reverse=True)
        return recommendations[:top_k]
    
    def _calculate_content_score(self, user_profile: Dict[str, Any], 
                               paper: Dict[str, Any]) -> float:
        """Calculate content-based similarity score"""
        score = 0.0
        
        # Interest matching
        paper_keywords = [kw.lower() for kw in paper.get('keywords', [])]
        for keyword in paper_keywords:
            if keyword in user_profile["interests"]:
                score += user_profile["interests"][keyword] * 0.4
        
        # Research area matching
        paper_categories = paper.get('categories', [])
        for category in paper_categories:
            if category in user_profile["research_areas"]:
                score += user_profile["research_areas"][category] * 0.3
        
        # Author preference
        paper_authors = paper.get('authors', [])
        for author in paper_authors:
            if author in user_profile["preferred_authors"]:
                score += user_profile["preferred_authors"][author] * 0.2
        
        # Recency bonus (newer papers get slight boost)
        year = paper.get('published_year', 2020)
        if year >= 2023:
            score += 0.1
        
        return score
    
    def _generate_content_reason(self, user_profile: Dict[str, Any], 
                               paper: Dict[str, Any]) -> str:
        """Generate explanation for content-based recommendation"""
        reasons = []
        
        # Check interest matches
        paper_keywords = [kw.lower() for kw in paper.get('keywords', [])]
        matching_interests = [kw for kw in paper_keywords 
                            if kw in user_profile["interests"]]
        if matching_interests:
            reasons.append(f"matches your interests in {', '.join(matching_interests[:3])}")
        
        # Check author matches
        paper_authors = paper.get('authors', [])
        preferred_authors = [author for author in paper_authors 
                           if author in user_profile["preferred_authors"]]
        if preferred_authors:
            reasons.append(f"by preferred author {preferred_authors[0]}")
        
        # Check research area matches
        paper_categories = paper.get('categories', [])
        matching_areas = [cat for cat in paper_categories 
                         if cat in user_profile["research_areas"]]
        if matching_areas:
            reasons.append(f"in your research area: {matching_areas[0]}")
        
        return "Recommended because it " + " and ".join(reasons) if reasons else "Similar to your reading history"
    
    def _collaborative_recommendations(self, user_id: str, 
                                     papers: List[Dict[str, Any]], 
                                     top_k: int) -> List[Dict[str, Any]]:
        """Collaborative filtering recommendations"""
        # Simplified collaborative filtering
        # In production, this would use more sophisticated algorithms
        
        similar_users = self._find_similar_users(user_id)
        recommendations = []
        
        for paper in papers:
            score = 0.0
            for similar_user_id, similarity in similar_users:
                if paper.get('id') in self.interaction_matrix.get(similar_user_id, {}):
                    user_rating = self.interaction_matrix[similar_user_id][paper['id']]
                    score += similarity * user_rating
            
            if score > 0:
                recommendations.append({
                    **paper,
                    "recommendation_score": score,
                    "recommendation_reason": "Recommended by users with similar interests"
                })
        
        recommendations.sort(key=lambda x: x["recommendation_score"], reverse=True)
        return recommendations[:top_k]
    
    def _find_similar_users(self, user_id: str, top_k: int = 5) -> List[Tuple[str, float]]:
        """Find users with similar research interests"""
        if user_id not in self.user_profiles:
            return []
        
        target_profile = self.user_profiles[user_id]
        similarities = []
        
        for other_user_id, other_profile in self.user_profiles.items():
            if other_user_id == user_id:
                continue
            
            similarity = self._calculate_profile_similarity(target_profile, other_profile)
            similarities.append((other_user_id, similarity))
        
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:top_k]
    
    def _calculate_profile_similarity(self, profile1: Dict[str, Any], 
                                    profile2: Dict[str, Any]) -> float:
        """Calculate similarity between user profiles"""
        # Interest similarity
        interests1 = set(profile1["interests"].keys())
        interests2 = set(profile2["interests"].keys())
        
        if not interests1 or not interests2:
            return 0.0
        
        intersection = len(interests1.intersection(interests2))
        union = len(interests1.union(interests2))
        
        jaccard_similarity = intersection / union if union > 0 else 0.0
        
        return jaccard_similarity
    
    def _hybrid_recommendations(self, user_profile: Dict[str, Any], 
                              papers: List[Dict[str, Any]], 
                              top_k: int) -> List[Dict[str, Any]]:
        """Hybrid recommendations combining content and collaborative filtering"""
        # Get content-based recommendations
        content_recs = self._content_based_recommendations(user_profile, papers, top_k * 2)
        
        # Get collaborative recommendations
        collab_recs = self._collaborative_recommendations(user_profile["user_id"], papers, top_k * 2)
        
        # Combine and re-rank
        paper_scores = {}
        
        # Weight content-based scores
        for rec in content_recs:
            paper_id = rec.get('id', '')
            paper_scores[paper_id] = {
                "paper": rec,
                "content_score": rec["recommendation_score"] * 0.7,
                "collab_score": 0.0
            }
        
        # Add collaborative scores
        for rec in collab_recs:
            paper_id = rec.get('id', '')
            if paper_id in paper_scores:
                paper_scores[paper_id]["collab_score"] = rec["recommendation_score"] * 0.3
            else:
                paper_scores[paper_id] = {
                    "paper": rec,
                    "content_score": 0.0,
                    "collab_score": rec["recommendation_score"] * 0.3
                }
        
        # Calculate final scores
        final_recommendations = []
        for paper_id, scores in paper_scores.items():
            final_score = scores["content_score"] + scores["collab_score"]
            paper = scores["paper"]
            paper["recommendation_score"] = final_score
            paper["recommendation_reason"] = "Hybrid recommendation based on your interests and similar users"
            final_recommendations.append(paper)
        
        # Sort and return top k
        final_recommendations.sort(key=lambda x: x["recommendation_score"], reverse=True)
        return final_recommendations[:top_k]
    
    def _cold_start_recommendations(self, papers: List[Dict[str, Any]], 
                                  top_k: int) -> List[Dict[str, Any]]:
        """Recommendations for new users (cold start problem)"""
        # Recommend popular and recent papers
        recommendations = []
        
        for paper in papers:
            score = 0.0
            
            # Popularity score (citation count)
            citations = paper.get('citation_count', 0)
            score += min(citations / 100, 1.0) * 0.5  # Normalize and cap
            
            # Recency score
            year = paper.get('published_year', 2020)
            if year >= 2023:
                score += 0.3
            elif year >= 2022:
                score += 0.2
            elif year >= 2021:
                score += 0.1
            
            # Quality indicators
            if paper.get('venue_rank', 0) > 0.8:  # High-quality venue
                score += 0.2
            
            recommendations.append({
                **paper,
                "recommendation_score": score,
                "recommendation_reason": "Popular recent paper in AI research"
            })
        
        recommendations.sort(key=lambda x: x["recommendation_score"], reverse=True)
        return recommendations[:top_k]
    
    def update_user_interaction(self, user_id: str, paper_id: str, 
                              action: str, rating: Optional[float] = None):
        """Update user interaction data"""
        weight = self._get_action_weight(action)
        
        if rating is not None:
            weight = rating
        
        self.interaction_matrix[user_id][paper_id] = weight
        
        # Update user profile if it exists
        if user_id in self.user_profiles:
            # This would trigger profile update in a real system
            pass