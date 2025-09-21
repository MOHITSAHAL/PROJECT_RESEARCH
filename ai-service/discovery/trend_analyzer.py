"""
Trend Analysis Service for Research Direction Prediction
Provides emerging research identification and trend forecasting
"""

import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from collections import defaultdict, Counter
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class TrendAnalyzer:
    """Advanced trend analysis for research direction prediction"""
    
    def __init__(self):
        self.trend_cache = {}
        self.keyword_trends = defaultdict(list)
        self.author_trends = defaultdict(list)
        
    def analyze_research_trends(self, papers: List[Dict[str, Any]], 
                              time_window: int = 5) -> Dict[str, Any]:
        """Analyze research trends over time"""
        try:
            # Group papers by year
            papers_by_year = self._group_papers_by_year(papers)
            
            # Analyze keyword trends
            keyword_trends = self._analyze_keyword_trends(papers_by_year, time_window)
            
            # Analyze author productivity trends
            author_trends = self._analyze_author_trends(papers_by_year)
            
            # Analyze venue trends
            venue_trends = self._analyze_venue_trends(papers_by_year)
            
            # Identify emerging topics
            emerging_topics = self._identify_emerging_topics(papers_by_year, time_window)
            
            # Predict future trends
            predictions = self._predict_future_trends(keyword_trends, time_window)
            
            return {
                "keyword_trends": keyword_trends,
                "author_trends": author_trends,
                "venue_trends": venue_trends,
                "emerging_topics": emerging_topics,
                "predictions": predictions,
                "analysis_period": {
                    "start_year": min(papers_by_year.keys()) if papers_by_year else None,
                    "end_year": max(papers_by_year.keys()) if papers_by_year else None,
                    "total_papers": len(papers)
                }
            }
            
        except Exception as e:
            logger.error(f"Error analyzing research trends: {e}")
            raise
    
    def _group_papers_by_year(self, papers: List[Dict[str, Any]]) -> Dict[int, List[Dict[str, Any]]]:
        """Group papers by publication year"""
        papers_by_year = defaultdict(list)
        
        for paper in papers:
            year = paper.get('published_year')
            if year and isinstance(year, int) and 2000 <= year <= 2024:
                papers_by_year[year].append(paper)
        
        return dict(papers_by_year)
    
    def _analyze_keyword_trends(self, papers_by_year: Dict[int, List[Dict[str, Any]]], 
                              time_window: int) -> Dict[str, Any]:
        """Analyze keyword popularity trends over time"""
        keyword_counts = defaultdict(lambda: defaultdict(int))
        
        # Count keywords per year
        for year, papers in papers_by_year.items():
            for paper in papers:
                keywords = paper.get('keywords', [])
                if isinstance(keywords, str):
                    keywords = [keywords]
                
                for keyword in keywords:
                    if isinstance(keyword, str) and len(keyword) > 2:
                        keyword_counts[keyword.lower()][year] += 1
        
        # Calculate trends
        trending_keywords = []
        declining_keywords = []
        stable_keywords = []
        
        current_year = max(papers_by_year.keys()) if papers_by_year else 2024
        
        for keyword, year_counts in keyword_counts.items():
            if len(year_counts) < 2:
                continue
            
            # Calculate trend slope
            years = sorted(year_counts.keys())
            counts = [year_counts[year] for year in years]
            
            if len(years) >= 2:
                trend_slope = self._calculate_trend_slope(years, counts)
                total_count = sum(counts)
                
                trend_data = {
                    "keyword": keyword,
                    "trend_slope": trend_slope,
                    "total_mentions": total_count,
                    "recent_mentions": year_counts.get(current_year, 0),
                    "year_data": dict(year_counts),
                    "growth_rate": self._calculate_growth_rate(counts)
                }
                
                if trend_slope > 0.5 and total_count > 5:
                    trending_keywords.append(trend_data)
                elif trend_slope < -0.5:
                    declining_keywords.append(trend_data)
                else:
                    stable_keywords.append(trend_data)
        
        # Sort by trend strength
        trending_keywords.sort(key=lambda x: x["trend_slope"], reverse=True)
        declining_keywords.sort(key=lambda x: x["trend_slope"])
        
        return {
            "trending_up": trending_keywords[:20],
            "trending_down": declining_keywords[:10],
            "stable": stable_keywords[:10],
            "analysis_summary": {
                "total_keywords": len(keyword_counts),
                "trending_count": len(trending_keywords),
                "declining_count": len(declining_keywords)
            }
        }
    
    def _calculate_trend_slope(self, years: List[int], counts: List[int]) -> float:
        """Calculate trend slope using linear regression"""
        if len(years) < 2:
            return 0.0
        
        n = len(years)
        sum_x = sum(years)
        sum_y = sum(counts)
        sum_xy = sum(x * y for x, y in zip(years, counts))
        sum_x2 = sum(x * x for x in years)
        
        denominator = n * sum_x2 - sum_x * sum_x
        if denominator == 0:
            return 0.0
        
        slope = (n * sum_xy - sum_x * sum_y) / denominator
        return slope
    
    def _calculate_growth_rate(self, counts: List[int]) -> float:
        """Calculate average growth rate"""
        if len(counts) < 2:
            return 0.0
        
        growth_rates = []
        for i in range(1, len(counts)):
            if counts[i-1] > 0:
                rate = (counts[i] - counts[i-1]) / counts[i-1]
                growth_rates.append(rate)
        
        return np.mean(growth_rates) if growth_rates else 0.0
    
    def _analyze_author_trends(self, papers_by_year: Dict[int, List[Dict[str, Any]]]) -> Dict[str, Any]:
        """Analyze author productivity and collaboration trends"""
        author_stats = defaultdict(lambda: defaultdict(int))
        collaboration_stats = defaultdict(list)
        
        for year, papers in papers_by_year.items():
            for paper in papers:
                authors = paper.get('authors', [])
                if not authors:
                    continue
                
                # Track individual author productivity
                for author in authors:
                    author_stats[author][year] += 1
                
                # Track collaboration (number of co-authors)
                collaboration_stats[year].append(len(authors))
        
        # Find most productive authors
        productive_authors = []
        for author, year_counts in author_stats.items():
            total_papers = sum(year_counts.values())
            if total_papers >= 3:  # Minimum threshold
                recent_activity = sum(count for year, count in year_counts.items() 
                                    if year >= max(papers_by_year.keys()) - 2)
                
                productive_authors.append({
                    "author": author,
                    "total_papers": total_papers,
                    "recent_activity": recent_activity,
                    "active_years": len(year_counts),
                    "productivity_trend": self._calculate_author_trend(year_counts)
                })
        
        productive_authors.sort(key=lambda x: x["total_papers"], reverse=True)
        
        # Calculate collaboration trends
        collab_trends = {}
        for year, collab_counts in collaboration_stats.items():
            collab_trends[year] = {
                "avg_authors": np.mean(collab_counts),
                "max_authors": max(collab_counts),
                "single_author_papers": sum(1 for c in collab_counts if c == 1)
            }
        
        return {
            "productive_authors": productive_authors[:20],
            "collaboration_trends": collab_trends,
            "summary": {
                "total_unique_authors": len(author_stats),
                "avg_collaboration_size": np.mean([np.mean(counts) for counts in collaboration_stats.values()])
            }
        }
    
    def _calculate_author_trend(self, year_counts: Dict[int, int]) -> str:
        """Calculate author productivity trend"""
        years = sorted(year_counts.keys())
        counts = [year_counts[year] for year in years]
        
        if len(counts) < 2:
            return "stable"
        
        slope = self._calculate_trend_slope(years, counts)
        
        if slope > 0.1:
            return "increasing"
        elif slope < -0.1:
            return "decreasing"
        else:
            return "stable"
    
    def _analyze_venue_trends(self, papers_by_year: Dict[int, List[Dict[str, Any]]]) -> Dict[str, Any]:
        """Analyze publication venue trends"""
        venue_stats = defaultdict(lambda: defaultdict(int))
        
        for year, papers in papers_by_year.items():
            for paper in papers:
                venue = paper.get('venue', '').strip()
                if venue:
                    venue_stats[venue][year] += 1
        
        # Find trending venues
        trending_venues = []
        for venue, year_counts in venue_stats.items():
            total_papers = sum(year_counts.values())
            if total_papers >= 5:  # Minimum threshold
                
                years = sorted(year_counts.keys())
                counts = [year_counts[year] for year in years]
                trend_slope = self._calculate_trend_slope(years, counts)
                
                trending_venues.append({
                    "venue": venue,
                    "total_papers": total_papers,
                    "trend_slope": trend_slope,
                    "recent_papers": year_counts.get(max(years), 0) if years else 0,
                    "year_data": dict(year_counts)
                })
        
        trending_venues.sort(key=lambda x: x["trend_slope"], reverse=True)
        
        return {
            "trending_venues": trending_venues[:15],
            "total_venues": len(venue_stats)
        }
    
    def _identify_emerging_topics(self, papers_by_year: Dict[int, List[Dict[str, Any]]], 
                                time_window: int) -> List[Dict[str, Any]]:
        """Identify emerging research topics"""
        current_year = max(papers_by_year.keys()) if papers_by_year else 2024
        recent_years = [year for year in papers_by_year.keys() 
                       if year >= current_year - time_window + 1]
        
        if len(recent_years) < 2:
            return []
        
        # Get keywords from recent papers
        recent_keywords = defaultdict(int)
        older_keywords = defaultdict(int)
        
        # Count keywords in recent years
        for year in recent_years:
            for paper in papers_by_year[year]:
                keywords = paper.get('keywords', [])
                if isinstance(keywords, str):
                    keywords = [keywords]
                
                for keyword in keywords:
                    if isinstance(keyword, str) and len(keyword) > 2:
                        recent_keywords[keyword.lower()] += 1
        
        # Count keywords in older years
        older_years = [year for year in papers_by_year.keys() 
                      if year < current_year - time_window + 1]
        
        for year in older_years:
            for paper in papers_by_year[year]:
                keywords = paper.get('keywords', [])
                if isinstance(keywords, str):
                    keywords = [keywords]
                
                for keyword in keywords:
                    if isinstance(keyword, str) and len(keyword) > 2:
                        older_keywords[keyword.lower()] += 1
        
        # Find emerging topics (high recent activity, low historical activity)
        emerging_topics = []
        
        for keyword, recent_count in recent_keywords.items():
            older_count = older_keywords.get(keyword, 0)
            
            # Emergence criteria
            if recent_count >= 3:  # Minimum recent mentions
                emergence_ratio = recent_count / max(older_count, 1)
                
                if emergence_ratio >= 2.0:  # At least 2x increase
                    emerging_topics.append({
                        "topic": keyword,
                        "recent_mentions": recent_count,
                        "historical_mentions": older_count,
                        "emergence_ratio": emergence_ratio,
                        "emergence_score": recent_count * emergence_ratio
                    })
        
        # Sort by emergence score
        emerging_topics.sort(key=lambda x: x["emergence_score"], reverse=True)
        
        return emerging_topics[:15]
    
    def _predict_future_trends(self, keyword_trends: Dict[str, Any], 
                             time_window: int) -> Dict[str, Any]:
        """Predict future research trends"""
        predictions = {
            "hot_topics": [],
            "declining_topics": [],
            "stable_growth": [],
            "confidence_level": "medium"
        }
        
        # Analyze trending keywords for predictions
        trending_keywords = keyword_trends.get("trending_up", [])
        
        for trend in trending_keywords[:10]:
            keyword = trend["keyword"]
            slope = trend["trend_slope"]
            growth_rate = trend["growth_rate"]
            
            # Predict next year's mentions
            recent_mentions = trend["recent_mentions"]
            predicted_mentions = max(1, int(recent_mentions * (1 + growth_rate)))
            
            prediction = {
                "topic": keyword,
                "current_mentions": recent_mentions,
                "predicted_mentions": predicted_mentions,
                "confidence": min(0.9, slope / 2.0),  # Cap confidence at 90%
                "trend_strength": "strong" if slope > 1.0 else "moderate"
            }
            
            if slope > 1.0:
                predictions["hot_topics"].append(prediction)
            else:
                predictions["stable_growth"].append(prediction)
        
        # Add declining predictions
        declining_keywords = keyword_trends.get("trending_down", [])
        for trend in declining_keywords[:5]:
            predictions["declining_topics"].append({
                "topic": trend["keyword"],
                "current_mentions": trend["recent_mentions"],
                "trend_direction": "declining",
                "decline_rate": abs(trend["trend_slope"])
            })
        
        return predictions