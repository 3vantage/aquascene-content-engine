"""
Content Scheduler for Instagram
Handles optimal timing analysis, content scheduling, and automated posting.
"""

import sqlite3
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, time as dt_time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import pytz
import logging
from sklearn.cluster import KMeans
import asyncio
import schedule

from ..api.instagram_client import InstagramBusinessAPI, InstagramPost, MediaType


class PostStatus(Enum):
    SCHEDULED = "scheduled"
    PUBLISHED = "published"
    FAILED = "failed"
    CANCELLED = "cancelled"


class PostType(Enum):
    EDUCATIONAL = "educational"
    SHOWCASE = "showcase"
    TUTORIAL = "tutorial"
    COMMUNITY = "community"
    BEHIND_SCENES = "behind_scenes"
    PARTNERSHIP = "partnership"


@dataclass
class ScheduledPost:
    """Data class for scheduled posts"""
    id: str
    post: InstagramPost
    post_type: PostType
    scheduled_time: datetime
    status: PostStatus
    created_at: datetime
    attempts: int = 0
    error_message: str = None
    published_id: str = None


class OptimalTimingAnalyzer:
    """
    Analyzes engagement data to determine optimal posting times.
    """
    
    def __init__(self, instagram_api: InstagramBusinessAPI):
        self.instagram_api = instagram_api
        self.logger = logging.getLogger(__name__)
    
    def analyze_historical_performance(self, days_back: int = 30) -> Dict:
        """
        Analyze historical post performance to identify optimal posting times.
        """
        try:
            # Get recent media
            recent_media = self.instagram_api.get_recent_media(limit=100)
            
            if not recent_media:
                return self._get_default_optimal_times()
            
            # Analyze engagement by hour and day
            engagement_by_hour = {}
            engagement_by_day = {}
            
            for media in recent_media:
                timestamp = datetime.fromisoformat(media['timestamp'].replace('Z', '+00:00'))
                
                # Convert to target timezone (Bulgaria/Europe)
                bg_timezone = pytz.timezone('Europe/Sofia')
                local_time = timestamp.astimezone(bg_timezone)
                
                hour = local_time.hour
                day = local_time.strftime('%A')
                
                # Calculate engagement rate
                likes = media.get('like_count', 0)
                comments = media.get('comments_count', 0)
                engagement = likes + (comments * 3)  # Weight comments more
                
                # Group by hour
                if hour not in engagement_by_hour:
                    engagement_by_hour[hour] = []
                engagement_by_hour[hour].append(engagement)
                
                # Group by day
                if day not in engagement_by_day:
                    engagement_by_day[day] = []
                engagement_by_day[day].append(engagement)
            
            # Calculate average engagement
            avg_engagement_by_hour = {
                hour: np.mean(engagements) 
                for hour, engagements in engagement_by_hour.items()
            }
            
            avg_engagement_by_day = {
                day: np.mean(engagements) 
                for day, engagements in engagement_by_day.items()
            }
            
            # Find top performing hours and days
            top_hours = sorted(avg_engagement_by_hour.items(), 
                             key=lambda x: x[1], reverse=True)[:5]
            
            top_days = sorted(avg_engagement_by_day.items(), 
                            key=lambda x: x[1], reverse=True)[:3]
            
            return {
                'optimal_hours': [hour for hour, _ in top_hours],
                'optimal_days': [day for day, _ in top_days],
                'engagement_by_hour': avg_engagement_by_hour,
                'engagement_by_day': avg_engagement_by_day,
                'analysis_date': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing optimal times: {e}")
            return self._get_default_optimal_times()
    
    def _get_default_optimal_times(self) -> Dict:
        """
        Return default optimal posting times based on aquascaping community patterns.
        """
        return {
            'optimal_hours': [9, 13, 17, 19, 21],  # Morning, lunch, evening prime times
            'optimal_days': ['Monday', 'Wednesday', 'Friday', 'Saturday', 'Sunday'],
            'engagement_by_hour': {},
            'engagement_by_day': {},
            'analysis_date': datetime.now().isoformat()
        }
    
    def get_next_optimal_time(self, post_type: PostType, 
                            avoid_times: List[datetime] = None) -> datetime:
        """
        Get the next optimal posting time based on type and analysis.
        """
        optimal_data = self.analyze_historical_performance()
        optimal_hours = optimal_data['optimal_hours']
        optimal_days = optimal_data['optimal_days']
        
        # Different strategies for different post types
        if post_type == PostType.EDUCATIONAL:
            # Educational content performs better in the morning
            preferred_hours = [h for h in optimal_hours if 8 <= h <= 12]
        elif post_type == PostType.SHOWCASE:
            # Showcase content performs better in evening
            preferred_hours = [h for h in optimal_hours if 17 <= h <= 21]
        elif post_type == PostType.TUTORIAL:
            # Tutorials perform well on weekends
            preferred_hours = optimal_hours
        else:
            preferred_hours = optimal_hours
        
        if not preferred_hours:
            preferred_hours = optimal_hours
        
        # Find next available optimal time
        bg_timezone = pytz.timezone('Europe/Sofia')
        now = datetime.now(bg_timezone)
        
        for days_ahead in range(7):  # Look up to a week ahead
            target_date = now + timedelta(days=days_ahead)
            
            # Skip if not an optimal day
            if target_date.strftime('%A') not in optimal_days:
                continue
            
            for hour in preferred_hours:
                target_time = target_date.replace(
                    hour=hour, minute=0, second=0, microsecond=0
                )
                
                # Skip if time has passed today
                if target_time <= now:
                    continue
                
                # Skip if time conflicts with avoid_times
                if avoid_times and any(
                    abs((target_time - avoid_time).total_seconds()) < 3600 
                    for avoid_time in avoid_times
                ):
                    continue
                
                return target_time
        
        # Fallback: next available hour
        return now + timedelta(hours=2)


class ContentScheduler:
    """
    Main content scheduler that manages the posting queue and timing.
    """
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or "instagram_scheduler.db"
        self.logger = logging.getLogger(__name__)
        self.init_database()
        
        # Initialize timezone
        self.timezone = pytz.timezone('Europe/Sofia')
    
    def init_database(self):
        """Initialize SQLite database for scheduling"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS scheduled_posts (
                id TEXT PRIMARY KEY,
                post_data TEXT NOT NULL,
                post_type TEXT NOT NULL,
                scheduled_time TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL,
                attempts INTEGER DEFAULT 0,
                error_message TEXT,
                published_id TEXT
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS posting_history (
                id TEXT PRIMARY KEY,
                post_id TEXT,
                published_at TEXT,
                engagement_24h INTEGER,
                engagement_7d INTEGER,
                performance_score REAL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        conn.close()
    
    def schedule_post(self, post: InstagramPost, post_type: PostType, 
                     scheduled_time: datetime = None) -> str:
        """
        Schedule a post for publishing.
        """
        import uuid
        
        post_id = str(uuid.uuid4())
        
        if scheduled_time is None:
            # Get optimal time from analyzer
            analyzer = OptimalTimingAnalyzer(None)  # Would need API client
            scheduled_time = analyzer.get_next_optimal_time(post_type)
        
        scheduled_post = ScheduledPost(
            id=post_id,
            post=post,
            post_type=post_type,
            scheduled_time=scheduled_time,
            status=PostStatus.SCHEDULED,
            created_at=datetime.now(),
            attempts=0
        )
        
        # Save to database
        self._save_scheduled_post(scheduled_post)
        
        self.logger.info(f"Scheduled post {post_id} for {scheduled_time}")
        return post_id
    
    def _save_scheduled_post(self, scheduled_post: ScheduledPost):
        """Save scheduled post to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Convert post to JSON
        post_data = {
            'caption': scheduled_post.post.caption,
            'media_type': scheduled_post.post.media_type.value,
            'media_url': scheduled_post.post.media_url,
            'media_urls': scheduled_post.post.media_urls,
            'hashtags': scheduled_post.post.hashtags
        }
        
        cursor.execute("""
            INSERT OR REPLACE INTO scheduled_posts 
            (id, post_data, post_type, scheduled_time, status, created_at, attempts, error_message, published_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            scheduled_post.id,
            json.dumps(post_data),
            scheduled_post.post_type.value,
            scheduled_post.scheduled_time.isoformat(),
            scheduled_post.status.value,
            scheduled_post.created_at.isoformat(),
            scheduled_post.attempts,
            scheduled_post.error_message,
            scheduled_post.published_id
        ))
        
        conn.commit()
        conn.close()
    
    def get_due_posts(self) -> List[ScheduledPost]:
        """Get posts that are due for publishing"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        now = datetime.now().isoformat()
        cursor.execute("""
            SELECT * FROM scheduled_posts 
            WHERE status = ? AND scheduled_time <= ?
            ORDER BY scheduled_time ASC
        """, (PostStatus.SCHEDULED.value, now))
        
        rows = cursor.fetchall()
        conn.close()
        
        scheduled_posts = []
        for row in rows:
            post_data = json.loads(row[1])
            
            # Reconstruct InstagramPost
            instagram_post = InstagramPost(
                caption=post_data['caption'],
                media_type=MediaType(post_data['media_type']),
                media_url=post_data.get('media_url'),
                media_urls=post_data.get('media_urls'),
                hashtags=post_data.get('hashtags')
            )
            
            scheduled_post = ScheduledPost(
                id=row[0],
                post=instagram_post,
                post_type=PostType(row[2]),
                scheduled_time=datetime.fromisoformat(row[3]),
                status=PostStatus(row[4]),
                created_at=datetime.fromisoformat(row[5]),
                attempts=row[6],
                error_message=row[7],
                published_id=row[8]
            )
            
            scheduled_posts.append(scheduled_post)
        
        return scheduled_posts
    
    def update_post_status(self, post_id: str, status: PostStatus, 
                          error_message: str = None, published_id: str = None):
        """Update the status of a scheduled post"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE scheduled_posts 
            SET status = ?, error_message = ?, published_id = ?, attempts = attempts + 1
            WHERE id = ?
        """, (status.value, error_message, published_id, post_id))
        
        conn.commit()
        conn.close()
    
    def get_scheduled_posts(self, limit: int = 50) -> List[ScheduledPost]:
        """Get all scheduled posts"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM scheduled_posts 
            ORDER BY scheduled_time DESC 
            LIMIT ?
        """, (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        # Convert to ScheduledPost objects (similar to get_due_posts)
        # Implementation similar to get_due_posts method
        return []  # Simplified for brevity
    
    def cancel_post(self, post_id: str) -> bool:
        """Cancel a scheduled post"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE scheduled_posts 
            SET status = ? 
            WHERE id = ? AND status = ?
        """, (PostStatus.CANCELLED.value, post_id, PostStatus.SCHEDULED.value))
        
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        return success
    
    def get_posting_statistics(self) -> Dict:
        """Get posting statistics and performance metrics"""
        conn = sqlite3.connect(self.db_path)
        
        # Get basic stats
        stats_query = """
            SELECT 
                status,
                COUNT(*) as count
            FROM scheduled_posts 
            GROUP BY status
        """
        
        stats_df = pd.read_sql_query(stats_query, conn)
        
        # Get recent performance
        performance_query = """
            SELECT 
                AVG(performance_score) as avg_performance,
                COUNT(*) as total_posts
            FROM posting_history 
            WHERE created_at >= date('now', '-30 days')
        """
        
        performance_df = pd.read_sql_query(performance_query, conn)
        conn.close()
        
        return {
            'post_counts': stats_df.set_index('status')['count'].to_dict(),
            'avg_performance_30d': performance_df['avg_performance'].iloc[0] if not performance_df.empty else 0,
            'total_posts_30d': performance_df['total_posts'].iloc[0] if not performance_df.empty else 0
        }


class AutomatedPublisher:
    """
    Automated publisher that monitors the schedule and publishes content.
    """
    
    def __init__(self, instagram_api: InstagramBusinessAPI, scheduler: ContentScheduler):
        self.instagram_api = instagram_api
        self.scheduler = scheduler
        self.logger = logging.getLogger(__name__)
        self.is_running = False
    
    async def start_publishing_loop(self, check_interval: int = 300):
        """
        Start the automated publishing loop.
        Checks for due posts every check_interval seconds.
        """
        self.is_running = True
        self.logger.info("Starting automated publisher loop")
        
        while self.is_running:
            try:
                await self._publish_due_posts()
                await asyncio.sleep(check_interval)
            except Exception as e:
                self.logger.error(f"Error in publishing loop: {e}")
                await asyncio.sleep(60)  # Wait before retrying
    
    async def _publish_due_posts(self):
        """Check for and publish due posts"""
        due_posts = self.scheduler.get_due_posts()
        
        for scheduled_post in due_posts:
            try:
                self.logger.info(f"Publishing post {scheduled_post.id}")
                
                # Attempt to publish
                result = self.instagram_api.post_content(scheduled_post.post)
                
                # Update status on success
                published_id = result.get('id')
                self.scheduler.update_post_status(
                    scheduled_post.id, 
                    PostStatus.PUBLISHED,
                    published_id=published_id
                )
                
                self.logger.info(f"Successfully published post {scheduled_post.id}")
                
                # Add delay between posts
                await asyncio.sleep(30)
                
            except Exception as e:
                self.logger.error(f"Failed to publish post {scheduled_post.id}: {e}")
                
                # Update status on failure
                self.scheduler.update_post_status(
                    scheduled_post.id,
                    PostStatus.FAILED,
                    error_message=str(e)
                )
                
                # If too many attempts, mark as failed permanently
                if scheduled_post.attempts >= 3:
                    self.logger.error(f"Post {scheduled_post.id} failed after 3 attempts")
    
    def stop(self):
        """Stop the publishing loop"""
        self.is_running = False
        self.logger.info("Stopped automated publisher")


# Example usage
if __name__ == "__main__":
    import os
    
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    # Initialize components
    ACCESS_TOKEN = os.getenv('INSTAGRAM_ACCESS_TOKEN')
    BUSINESS_ACCOUNT_ID = os.getenv('INSTAGRAM_BUSINESS_ACCOUNT_ID')
    
    if ACCESS_TOKEN and BUSINESS_ACCOUNT_ID:
        instagram_api = InstagramBusinessAPI(ACCESS_TOKEN, BUSINESS_ACCOUNT_ID)
        scheduler = ContentScheduler()
        
        # Example: Schedule a test post
        test_post = InstagramPost(
            caption="Beautiful aquascape featuring Cryptocoryne plants! 🌱",
            media_type=MediaType.IMAGE,
            media_url="https://example.com/aquascape.jpg",
            hashtags=["aquascaping", "plantedtank", "aquarium", "природа"]
        )
        
        post_id = scheduler.schedule_post(test_post, PostType.SHOWCASE)
        print(f"Scheduled post: {post_id}")
        
        # Get statistics
        stats = scheduler.get_posting_statistics()
        print(f"Posting statistics: {stats}")