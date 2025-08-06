"""
Content Scheduling Service
Handles scheduling content for publication and distribution
"""
import uuid
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from ..crud.content import content_crud
from ..crud.newsletter import newsletter_crud
from ..models.content import GeneratedContent
from ..models.newsletter import NewsletterIssue
from ..models.social import InstagramPost

logger = logging.getLogger(__name__)


class ContentScheduler:
    """Service for scheduling content publication and distribution"""
    
    def __init__(self):
        self.default_publishing_hours = [9, 12, 15]  # 9 AM, 12 PM, 3 PM
        self.newsletter_send_times = {
            'weekly': {'day': 1, 'hour': 10},  # Monday 10 AM
            'bi_weekly': {'day': 3, 'hour': 10},  # Wednesday 10 AM  
            'monthly': {'day': 1, 'hour': 10}  # 1st of month, 10 AM
        }
    
    async def schedule_content(
        self,
        session: AsyncSession,
        content_id: uuid.UUID,
        scheduled_for: datetime,
        user_id: Optional[uuid.UUID] = None
    ) -> tuple[bool, Optional[GeneratedContent], Optional[str]]:
        """Schedule content for publication at specified time"""
        try:
            content = await content_crud.get(session, content_id)
            if not content:
                return False, None, "Content not found"
            
            # Validate scheduling constraints
            if scheduled_for <= datetime.utcnow():
                return False, None, "Cannot schedule content in the past"
            
            if content.status not in ['approved', 'draft']:
                return False, None, f"Cannot schedule content with status: {content.status}"
            
            # Update content with schedule
            update_data = {
                'scheduled_for': scheduled_for,
                'status': 'approved' if content.status == 'draft' else content.status
            }
            
            updated_content = await content_crud.update(
                session,
                db_obj=content,
                obj_in=update_data
            )
            
            logger.info(f"Content {content_id} scheduled for {scheduled_for}")
            
            return True, updated_content, None
            
        except Exception as e:
            logger.error(f"Failed to schedule content {content_id}: {str(e)}")
            return False, None, str(e)
    
    async def get_optimal_publish_time(
        self,
        session: AsyncSession,
        content_type: str,
        target_audience: Optional[str] = None
    ) -> datetime:
        """
        Calculate optimal publish time based on content type and audience
        
        This is a simplified version - in production you'd use analytics data
        """
        now = datetime.utcnow()
        
        # Get next business day if it's weekend
        next_publish = now
        while next_publish.weekday() > 4:  # Monday = 0, Sunday = 6
            next_publish += timedelta(days=1)
        
        # Set optimal hour based on content type
        if content_type == 'newsletter_article':
            optimal_hour = 9  # Morning for newsletters
        elif content_type == 'social_media':
            optimal_hour = 12  # Lunch time for social
        elif content_type == 'blog_post':
            optimal_hour = 10  # Mid-morning for blogs
        else:
            optimal_hour = 9  # Default to morning
        
        # If we've passed the optimal hour today, schedule for tomorrow
        if next_publish.date() == now.date() and now.hour >= optimal_hour:
            next_publish += timedelta(days=1)
        
        return next_publish.replace(hour=optimal_hour, minute=0, second=0, microsecond=0)
    
    async def create_publishing_schedule(
        self,
        session: AsyncSession,
        content_ids: List[uuid.UUID],
        start_date: Optional[datetime] = None,
        frequency_hours: int = 24
    ) -> Dict[str, Any]:
        """Create a publishing schedule for multiple content items"""
        if not start_date:
            start_date = datetime.utcnow() + timedelta(hours=1)
        
        results = {
            'scheduled': [],
            'failed': [],
            'total': len(content_ids)
        }
        
        current_schedule_time = start_date
        
        for i, content_id in enumerate(content_ids):
            # Skip weekends for business content
            while current_schedule_time.weekday() > 4:
                current_schedule_time += timedelta(days=1)
                current_schedule_time = current_schedule_time.replace(hour=9)
            
            success, content, error = await self.schedule_content(
                session, content_id, current_schedule_time
            )
            
            if success:
                results['scheduled'].append({
                    'content_id': str(content_id),
                    'title': content.title,
                    'scheduled_for': current_schedule_time.isoformat()
                })
                
                # Move to next time slot
                current_schedule_time += timedelta(hours=frequency_hours)
            else:
                results['failed'].append({
                    'content_id': str(content_id),
                    'error': error
                })
        
        return results
    
    async def get_publishing_queue(
        self,
        session: AsyncSession,
        hours_ahead: int = 24
    ) -> Dict[str, List[Dict]]:
        """Get content scheduled for publishing in the next N hours"""
        cutoff_time = datetime.utcnow() + timedelta(hours=hours_ahead)
        
        scheduled_content = await content_crud.get_scheduled_content(
            session, cutoff_time
        )
        
        # Group by time slots
        queue = {}
        for content in scheduled_content:
            time_slot = content.scheduled_for.strftime("%Y-%m-%d %H:00")
            if time_slot not in queue:
                queue[time_slot] = []
            
            queue[time_slot].append({
                'id': str(content.id),
                'title': content.title,
                'content_type': content.content_type,
                'status': content.status,
                'scheduled_for': content.scheduled_for.isoformat()
            })
        
        return queue
    
    async def schedule_newsletter_campaign(
        self,
        session: AsyncSession,
        issue_id: uuid.UUID,
        send_time: Optional[datetime] = None,
        frequency: str = 'weekly'
    ) -> tuple[bool, Optional[NewsletterIssue], Optional[str]]:
        """Schedule newsletter campaign for sending"""
        try:
            issue = await newsletter_crud.get(session, issue_id)
            if not issue:
                return False, None, "Newsletter issue not found"
            
            if not send_time:
                send_time = self._calculate_newsletter_send_time(frequency)
            
            updated_issue = await newsletter_crud.update(
                session,
                db_obj=issue,
                obj_in={
                    'scheduled_for': send_time,
                    'status': 'scheduled'
                }
            )
            
            logger.info(f"Newsletter issue {issue_id} scheduled for {send_time}")
            
            return True, updated_issue, None
            
        except Exception as e:
            logger.error(f"Failed to schedule newsletter {issue_id}: {str(e)}")
            return False, None, str(e)
    
    async def schedule_social_media_posts(
        self,
        session: AsyncSession,
        content_id: uuid.UUID,
        platforms: List[str],
        schedule_times: Optional[List[datetime]] = None
    ) -> Dict[str, Any]:
        """Schedule social media posts across platforms"""
        content = await content_crud.get(session, content_id)
        if not content:
            return {'error': 'Content not found'}
        
        if not schedule_times:
            # Generate optimal times for each platform
            schedule_times = self._generate_social_media_schedule(platforms)
        
        results = {
            'scheduled_posts': [],
            'failed': []
        }
        
        for i, platform in enumerate(platforms):
            try:
                schedule_time = schedule_times[i] if i < len(schedule_times) else schedule_times[0]
                
                # Create social media post record
                if platform.lower() == 'instagram':
                    post = InstagramPost(
                        content_id=content_id,
                        post_type='feed',
                        caption=content.excerpt or content.title,
                        scheduled_for=schedule_time,
                        status='scheduled'
                    )
                    session.add(post)
                    await session.commit()
                    
                    results['scheduled_posts'].append({
                        'platform': platform,
                        'scheduled_for': schedule_time.isoformat(),
                        'post_id': str(post.id)
                    })
                
            except Exception as e:
                results['failed'].append({
                    'platform': platform,
                    'error': str(e)
                })
        
        return results
    
    def _calculate_newsletter_send_time(self, frequency: str) -> datetime:
        """Calculate optimal newsletter send time based on frequency"""
        now = datetime.utcnow()
        schedule_config = self.newsletter_send_times.get(frequency, self.newsletter_send_times['weekly'])
        
        if frequency == 'weekly':
            # Next Monday at 10 AM
            days_ahead = (0 - now.weekday()) % 7
            if days_ahead == 0 and now.hour >= schedule_config['hour']:
                days_ahead = 7
            
            send_time = now + timedelta(days=days_ahead)
            send_time = send_time.replace(
                hour=schedule_config['hour'], 
                minute=0, 
                second=0, 
                microsecond=0
            )
            
        elif frequency == 'bi_weekly':
            # Next Wednesday at 10 AM
            days_ahead = (2 - now.weekday()) % 7
            if days_ahead == 0 and now.hour >= schedule_config['hour']:
                days_ahead = 7
            
            send_time = now + timedelta(days=days_ahead)
            send_time = send_time.replace(
                hour=schedule_config['hour'],
                minute=0,
                second=0,
                microsecond=0
            )
            
        elif frequency == 'monthly':
            # 1st of next month at 10 AM
            if now.day == 1 and now.hour < schedule_config['hour']:
                send_time = now.replace(
                    hour=schedule_config['hour'],
                    minute=0,
                    second=0,
                    microsecond=0
                )
            else:
                # Next month
                next_month = now.replace(day=1) + timedelta(days=32)
                send_time = next_month.replace(
                    day=1,
                    hour=schedule_config['hour'],
                    minute=0,
                    second=0,
                    microsecond=0
                )
        else:
            # Default: tomorrow at 10 AM
            send_time = (now + timedelta(days=1)).replace(
                hour=10, minute=0, second=0, microsecond=0
            )
        
        return send_time
    
    def _generate_social_media_schedule(self, platforms: List[str]) -> List[datetime]:
        """Generate optimal posting schedule for social media platforms"""
        base_time = datetime.utcnow() + timedelta(hours=1)
        
        # Different optimal times for different platforms
        platform_hours = {
            'instagram': [9, 12, 17],  # 9 AM, 12 PM, 5 PM
            'twitter': [9, 12, 15, 18],  # Multiple times throughout day
            'facebook': [10, 14, 16],  # 10 AM, 2 PM, 4 PM
            'linkedin': [8, 12, 17]  # Business hours
        }
        
        schedule_times = []
        hour_index = 0
        
        for platform in platforms:
            platform_name = platform.lower()
            hours = platform_hours.get(platform_name, [9, 12, 15])
            
            # Use different hours for each platform to spread out posts
            hour = hours[hour_index % len(hours)]
            hour_index += 1
            
            # Schedule for next available day at optimal hour
            schedule_time = base_time.replace(hour=hour, minute=0, second=0, microsecond=0)
            
            # If this hour has passed today, schedule for tomorrow
            if schedule_time <= datetime.utcnow():
                schedule_time += timedelta(days=1)
            
            schedule_times.append(schedule_time)
            
            # Add some spacing between posts
            base_time += timedelta(minutes=30)
        
        return schedule_times


# Global service instance
content_scheduler = ContentScheduler()