"""
Instagram Performance Analytics and Tracking System
Comprehensive analytics for tracking post performance, engagement metrics, and optimization insights.
"""

import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import json
import logging
from collections import defaultdict
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, r2_score

from ..api.instagram_client import InstagramBusinessAPI


class MetricType(Enum):
    ENGAGEMENT_RATE = "engagement_rate"
    REACH = "reach"
    IMPRESSIONS = "impressions"
    LIKES = "likes"
    COMMENTS = "comments"
    SAVES = "saves"
    SHARES = "shares"
    PROFILE_VISITS = "profile_visits"
    WEBSITE_CLICKS = "website_clicks"


class PostPerformanceLevel(Enum):
    EXCELLENT = "excellent"  # Top 10% of posts
    GOOD = "good"           # Top 25% of posts
    AVERAGE = "average"     # Middle 50% of posts
    POOR = "poor"          # Bottom 25% of posts


@dataclass
class PostMetrics:
    """Data structure for post performance metrics"""
    post_id: str
    timestamp: datetime
    likes: int
    comments: int
    saves: int
    shares: int
    reach: int
    impressions: int
    profile_visits: int
    website_clicks: int
    hashtags: List[str]
    post_type: str
    caption_length: int
    has_location: bool
    posting_hour: int
    posting_day: str
    engagement_rate: float = 0.0
    performance_score: float = 0.0


@dataclass
class AnalyticsReport:
    """Comprehensive analytics report"""
    period_start: datetime
    period_end: datetime
    total_posts: int
    avg_engagement_rate: float
    total_reach: int
    total_impressions: int
    follower_growth: int
    top_performing_posts: List[Dict]
    worst_performing_posts: List[Dict]
    optimal_posting_times: List[int]
    best_hashtags: List[str]
    content_insights: Dict
    recommendations: List[str]


class PerformanceDatabase:
    """SQLite database for storing performance analytics"""
    
    def __init__(self, db_path: str = "instagram_analytics.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize analytics database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS post_metrics (
                post_id TEXT PRIMARY KEY,
                timestamp TEXT,
                likes INTEGER,
                comments INTEGER,
                saves INTEGER,
                shares INTEGER,
                reach INTEGER,
                impressions INTEGER,
                profile_visits INTEGER,
                website_clicks INTEGER,
                hashtags TEXT,
                post_type TEXT,
                caption_length INTEGER,
                has_location BOOLEAN,
                posting_hour INTEGER,
                posting_day TEXT,
                engagement_rate REAL,
                performance_score REAL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS account_metrics (
                date TEXT PRIMARY KEY,
                follower_count INTEGER,
                following_count INTEGER,
                posts_count INTEGER,
                avg_engagement_rate REAL,
                total_reach INTEGER,
                total_impressions INTEGER,
                profile_views INTEGER,
                website_clicks INTEGER
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS content_insights (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                metric_type TEXT,
                metric_value TEXT,
                performance_score REAL,
                sample_size INTEGER,
                date_range_start TEXT,
                date_range_end TEXT,
                insights TEXT
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS hashtag_performance (
                hashtag TEXT,
                total_posts INTEGER,
                avg_engagement_rate REAL,
                avg_reach INTEGER,
                last_used TEXT,
                performance_trend TEXT,
                PRIMARY KEY (hashtag)
            )
        """)
        
        conn.commit()
        conn.close()
    
    def save_post_metrics(self, metrics: PostMetrics):
        """Save post metrics to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO post_metrics 
            (post_id, timestamp, likes, comments, saves, shares, reach, impressions,
             profile_visits, website_clicks, hashtags, post_type, caption_length,
             has_location, posting_hour, posting_day, engagement_rate, performance_score)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            metrics.post_id,
            metrics.timestamp.isoformat(),
            metrics.likes,
            metrics.comments,
            metrics.saves,
            metrics.shares,
            metrics.reach,
            metrics.impressions,
            metrics.profile_visits,
            metrics.website_clicks,
            json.dumps(metrics.hashtags),
            metrics.post_type,
            metrics.caption_length,
            metrics.has_location,
            metrics.posting_hour,
            metrics.posting_day,
            metrics.engagement_rate,
            metrics.performance_score
        ))
        
        conn.commit()
        conn.close()
    
    def get_post_metrics(self, days_back: int = 30) -> pd.DataFrame:
        """Get post metrics as pandas DataFrame"""
        conn = sqlite3.connect(self.db_path)
        
        query = """
            SELECT * FROM post_metrics 
            WHERE timestamp >= date('now', '-{} days')
            ORDER BY timestamp DESC
        """.format(days_back)
        
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        if not df.empty:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df['hashtags'] = df['hashtags'].apply(json.loads)
        
        return df
    
    def get_hashtag_performance(self) -> pd.DataFrame:
        """Get hashtag performance data"""
        conn = sqlite3.connect(self.db_path)
        df = pd.read_sql_query("SELECT * FROM hashtag_performance", conn)
        conn.close()
        return df


class PerformanceTracker:
    """
    Main performance tracking and analytics engine.
    """
    
    def __init__(self, instagram_api: InstagramBusinessAPI, db_path: str = None):
        self.instagram_api = instagram_api
        self.db = PerformanceDatabase(db_path)
        self.logger = logging.getLogger(__name__)
    
    def collect_post_metrics(self, days_back: int = 7) -> List[PostMetrics]:
        """
        Collect metrics for recent posts from Instagram API.
        """
        try:
            # Get recent media
            recent_media = self.instagram_api.get_recent_media(limit=50)
            
            collected_metrics = []
            
            for media in recent_media:
                post_id = media['id']
                
                # Get detailed insights for the post
                try:
                    insights = self.instagram_api.get_media_insights(
                        post_id, 
                        metrics=['impressions', 'reach', 'engagement', 'saved', 'profile_visits']
                    )
                    
                    # Parse timestamp
                    timestamp = datetime.fromisoformat(media['timestamp'].replace('Z', '+00:00'))
                    
                    # Skip if older than requested period
                    if timestamp < datetime.now() - timedelta(days=days_back):
                        continue
                    
                    # Extract metrics
                    metrics = PostMetrics(
                        post_id=post_id,
                        timestamp=timestamp,
                        likes=media.get('like_count', 0),
                        comments=media.get('comments_count', 0),
                        saves=self._extract_insight_value(insights, 'saved'),
                        shares=0,  # Not available in API
                        reach=self._extract_insight_value(insights, 'reach'),
                        impressions=self._extract_insight_value(insights, 'impressions'),
                        profile_visits=self._extract_insight_value(insights, 'profile_visits'),
                        website_clicks=0,  # Would need website click tracking
                        hashtags=self._extract_hashtags(media.get('caption', '')),
                        post_type=media.get('media_type', 'IMAGE').lower(),
                        caption_length=len(media.get('caption', '')),
                        has_location=bool(media.get('location')),
                        posting_hour=timestamp.hour,
                        posting_day=timestamp.strftime('%A')
                    )
                    
                    # Calculate derived metrics
                    metrics.engagement_rate = self._calculate_engagement_rate(metrics)
                    metrics.performance_score = self._calculate_performance_score(metrics)
                    
                    collected_metrics.append(metrics)
                    
                    # Save to database
                    self.db.save_post_metrics(metrics)
                    
                except Exception as e:
                    self.logger.warning(f"Failed to get insights for post {post_id}: {e}")
                    continue
            
            self.logger.info(f"Collected metrics for {len(collected_metrics)} posts")
            return collected_metrics
            
        except Exception as e:
            self.logger.error(f"Failed to collect post metrics: {e}")
            return []
    
    def _extract_insight_value(self, insights: Dict, metric_name: str) -> int:
        """Extract metric value from insights data"""
        if not insights or 'data' not in insights:
            return 0
        
        for insight in insights['data']:
            if insight.get('name') == metric_name:
                return insight.get('values', [{}])[0].get('value', 0)
        
        return 0
    
    def _extract_hashtags(self, caption: str) -> List[str]:
        """Extract hashtags from caption text"""
        import re
        hashtags = re.findall(r'#(\w+)', caption.lower())
        return hashtags
    
    def _calculate_engagement_rate(self, metrics: PostMetrics) -> float:
        """Calculate engagement rate for a post"""
        if metrics.reach == 0:
            return 0.0
        
        engagement = metrics.likes + metrics.comments + metrics.saves
        return (engagement / metrics.reach) * 100
    
    def _calculate_performance_score(self, metrics: PostMetrics) -> float:
        """Calculate overall performance score (0-100)"""
        
        # Weighted scoring system
        engagement_weight = 0.4
        reach_weight = 0.3
        saves_weight = 0.2
        profile_visits_weight = 0.1
        
        # Normalize metrics (would need historical data for proper normalization)
        engagement_score = min(metrics.engagement_rate * 10, 100)  # Cap at 10% engagement
        reach_score = min(metrics.reach / 100, 100)  # Cap at 10k reach
        saves_score = min(metrics.saves * 5, 100)  # Cap at 20 saves
        profile_score = min(metrics.profile_visits * 2, 100)  # Cap at 50 visits
        
        performance_score = (
            engagement_score * engagement_weight +
            reach_score * reach_weight +
            saves_score * saves_weight +
            profile_score * profile_visits_weight
        )
        
        return min(performance_score, 100)
    
    def analyze_optimal_posting_times(self, days_back: int = 30) -> Dict:
        """
        Analyze optimal posting times based on historical performance.
        """
        df = self.db.get_post_metrics(days_back)
        
        if df.empty:
            return {"error": "No data available"}
        
        # Group by hour and calculate average engagement
        hourly_performance = df.groupby('posting_hour').agg({
            'engagement_rate': 'mean',
            'reach': 'mean',
            'performance_score': 'mean'
        }).round(2)
        
        # Group by day and calculate average engagement
        daily_performance = df.groupby('posting_day').agg({
            'engagement_rate': 'mean',
            'reach': 'mean',
            'performance_score': 'mean'
        }).round(2)
        
        # Find optimal times
        best_hours = hourly_performance.nlargest(3, 'engagement_rate').index.tolist()
        best_days = daily_performance.nlargest(3, 'engagement_rate').index.tolist()
        
        return {
            'optimal_hours': best_hours,
            'optimal_days': best_days,
            'hourly_performance': hourly_performance.to_dict(),
            'daily_performance': daily_performance.to_dict()
        }
    
    def analyze_hashtag_performance(self, min_usage: int = 3) -> Dict:
        """
        Analyze hashtag performance and effectiveness.
        """
        df = self.db.get_post_metrics(days_back=90)  # 3 months of data
        
        if df.empty:
            return {"error": "No data available"}
        
        # Expand hashtags and analyze performance
        hashtag_data = []
        
        for _, row in df.iterrows():
            for hashtag in row['hashtags']:
                hashtag_data.append({
                    'hashtag': hashtag,
                    'engagement_rate': row['engagement_rate'],
                    'reach': row['reach'],
                    'performance_score': row['performance_score']
                })
        
        hashtag_df = pd.DataFrame(hashtag_data)
        
        # Group by hashtag and calculate metrics
        hashtag_performance = hashtag_df.groupby('hashtag').agg({
            'engagement_rate': ['mean', 'count'],
            'reach': 'mean',
            'performance_score': 'mean'
        }).round(2)
        
        # Flatten column names
        hashtag_performance.columns = ['avg_engagement', 'usage_count', 'avg_reach', 'avg_performance']
        
        # Filter by minimum usage
        hashtag_performance = hashtag_performance[hashtag_performance['usage_count'] >= min_usage]
        
        # Sort by performance
        top_hashtags = hashtag_performance.nlargest(20, 'avg_engagement')
        worst_hashtags = hashtag_performance.nsmallest(10, 'avg_engagement')
        
        return {
            'top_hashtags': top_hashtags.to_dict('index'),
            'worst_hashtags': worst_hashtags.to_dict('index'),
            'total_unique_hashtags': len(hashtag_performance),
            'avg_hashtags_per_post': hashtag_df.groupby('hashtag').size().mean()
        }
    
    def analyze_content_performance(self) -> Dict:
        """
        Analyze performance by content type and characteristics.
        """
        df = self.db.get_post_metrics(days_back=60)
        
        if df.empty:
            return {"error": "No data available"}
        
        analysis = {}
        
        # Performance by post type
        type_performance = df.groupby('post_type').agg({
            'engagement_rate': 'mean',
            'reach': 'mean',
            'performance_score': 'mean'
        }).round(2)
        
        analysis['by_post_type'] = type_performance.to_dict('index')
        
        # Performance by caption length
        df['caption_length_bin'] = pd.cut(
            df['caption_length'], 
            bins=[0, 100, 300, 500, 1000, float('inf')],
            labels=['Very Short', 'Short', 'Medium', 'Long', 'Very Long']
        )
        
        length_performance = df.groupby('caption_length_bin').agg({
            'engagement_rate': 'mean',
            'reach': 'mean'
        }).round(2)
        
        analysis['by_caption_length'] = length_performance.to_dict('index')
        
        # Performance with/without location
        location_performance = df.groupby('has_location').agg({
            'engagement_rate': 'mean',
            'reach': 'mean'
        }).round(2)
        
        analysis['by_location'] = location_performance.to_dict('index')
        
        return analysis
    
    def generate_performance_report(self, days_back: int = 30) -> AnalyticsReport:
        """
        Generate comprehensive performance report.
        """
        df = self.db.get_post_metrics(days_back)
        
        if df.empty:
            return AnalyticsReport(
                period_start=datetime.now() - timedelta(days=days_back),
                period_end=datetime.now(),
                total_posts=0,
                avg_engagement_rate=0.0,
                total_reach=0,
                total_impressions=0,
                follower_growth=0,
                top_performing_posts=[],
                worst_performing_posts=[],
                optimal_posting_times=[],
                best_hashtags=[],
                content_insights={},
                recommendations=["Insufficient data for analysis"]
            )
        
        # Basic metrics
        total_posts = len(df)
        avg_engagement_rate = df['engagement_rate'].mean()
        total_reach = df['reach'].sum()
        total_impressions = df['impressions'].sum()
        
        # Top and worst performing posts
        top_posts = df.nlargest(5, 'performance_score')[
            ['post_id', 'engagement_rate', 'reach', 'performance_score', 'post_type']
        ].to_dict('records')
        
        worst_posts = df.nsmallest(3, 'performance_score')[
            ['post_id', 'engagement_rate', 'reach', 'performance_score', 'post_type']
        ].to_dict('records')
        
        # Optimal posting times
        optimal_times_data = self.analyze_optimal_posting_times(days_back)
        optimal_posting_times = optimal_times_data.get('optimal_hours', [])
        
        # Best hashtags
        hashtag_data = self.analyze_hashtag_performance()
        best_hashtags = list(hashtag_data.get('top_hashtags', {}).keys())[:10]
        
        # Content insights
        content_insights = self.analyze_content_performance()
        
        # Generate recommendations
        recommendations = self._generate_recommendations(df, optimal_times_data, hashtag_data)
        
        return AnalyticsReport(
            period_start=df['timestamp'].min(),
            period_end=df['timestamp'].max(),
            total_posts=total_posts,
            avg_engagement_rate=round(avg_engagement_rate, 2),
            total_reach=total_reach,
            total_impressions=total_impressions,
            follower_growth=0,  # Would need account metrics tracking
            top_performing_posts=top_posts,
            worst_performing_posts=worst_posts,
            optimal_posting_times=optimal_posting_times,
            best_hashtags=best_hashtags,
            content_insights=content_insights,
            recommendations=recommendations
        )
    
    def _generate_recommendations(self, df: pd.DataFrame, 
                                optimal_times: Dict, hashtag_data: Dict) -> List[str]:
        """Generate actionable recommendations based on analytics"""
        
        recommendations = []
        
        # Engagement rate recommendations
        avg_engagement = df['engagement_rate'].mean()
        if avg_engagement < 2.0:
            recommendations.append(
                "Engagement rate is below average (2%). Focus on more interactive content and better hashtags."
            )
        elif avg_engagement > 5.0:
            recommendations.append(
                "Excellent engagement rate! Continue with current content strategy."
            )
        
        # Posting time recommendations
        if optimal_times.get('optimal_hours'):
            best_hour = optimal_times['optimal_hours'][0]
            recommendations.append(
                f"Best posting time is {best_hour}:00. Schedule more posts during this hour."
            )
        
        # Content type recommendations
        type_performance = df.groupby('post_type')['engagement_rate'].mean()
        if not type_performance.empty:
            best_type = type_performance.idxmax()
            worst_type = type_performance.idxmin()
            
            recommendations.append(
                f"'{best_type.title()}' posts perform best. Consider creating more of this content type."
            )
            
            if type_performance[worst_type] < avg_engagement * 0.7:
                recommendations.append(
                    f"'{worst_type.title()}' posts underperform. Review and optimize this content type."
                )
        
        # Hashtag recommendations
        if hashtag_data.get('top_hashtags'):
            recommendations.append(
                "Use top-performing hashtags more frequently in future posts."
            )
            
        if hashtag_data.get('worst_hashtags'):
            recommendations.append(
                "Replace underperforming hashtags with more relevant alternatives."
            )
        
        # Caption length recommendations
        if 'caption_length' in df.columns:
            optimal_length = df.loc[df['engagement_rate'].idxmax(), 'caption_length']
            avg_length = df['caption_length'].mean()
            
            if optimal_length > avg_length * 1.5:
                recommendations.append(
                    "Longer captions tend to perform better. Consider adding more detail to posts."
                )
            elif optimal_length < avg_length * 0.5:
                recommendations.append(
                    "Shorter captions perform better. Keep posts concise and engaging."
                )
        
        return recommendations
    
    def export_analytics_data(self, format: str = 'csv', days_back: int = 90) -> str:
        """Export analytics data in specified format"""
        
        df = self.db.get_post_metrics(days_back)
        
        if format.lower() == 'csv':
            filename = f"instagram_analytics_{datetime.now().strftime('%Y%m%d')}.csv"
            df.to_csv(filename, index=False)
            return filename
        
        elif format.lower() == 'json':
            filename = f"instagram_analytics_{datetime.now().strftime('%Y%m%d')}.json"
            
            # Convert DataFrame to JSON-serializable format
            data = {
                'export_date': datetime.now().isoformat(),
                'period_days': days_back,
                'total_posts': len(df),
                'posts': df.to_dict('records')
            }
            
            with open(filename, 'w') as f:
                json.dump(data, f, indent=2, default=str)
            
            return filename
        
        else:
            raise ValueError("Unsupported format. Use 'csv' or 'json'")


# Usage example
if __name__ == "__main__":
    import os
    
    # Setup
    ACCESS_TOKEN = os.getenv('INSTAGRAM_ACCESS_TOKEN')
    BUSINESS_ACCOUNT_ID = os.getenv('INSTAGRAM_BUSINESS_ACCOUNT_ID')
    
    if ACCESS_TOKEN and BUSINESS_ACCOUNT_ID:
        instagram_api = InstagramBusinessAPI(ACCESS_TOKEN, BUSINESS_ACCOUNT_ID)
        tracker = PerformanceTracker(instagram_api)
        
        # Collect recent metrics
        print("Collecting post metrics...")
        metrics = tracker.collect_post_metrics(days_back=7)
        print(f"Collected data for {len(metrics)} posts")
        
        # Generate report
        print("Generating performance report...")
        report = tracker.generate_performance_report(days_back=30)
        
        print(f"Report Summary:")
        print(f"- Total Posts: {report.total_posts}")
        print(f"- Avg Engagement Rate: {report.avg_engagement_rate}%")
        print(f"- Total Reach: {report.total_reach:,}")
        print(f"- Recommendations: {len(report.recommendations)}")
        
        for i, rec in enumerate(report.recommendations, 1):
            print(f"  {i}. {rec}")
    else:
        print("Please set Instagram API credentials to run analytics")