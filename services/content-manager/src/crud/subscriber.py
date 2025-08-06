"""
Subscriber CRUD operations
"""
import uuid
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy import select, and_, or_, func, text
from sqlalchemy.ext.asyncio import AsyncSession

from .base import BaseCRUD
from ..models.subscriber import (
    Subscriber, SubscriberSegment, SubscriberSegmentMembership,
    SubscriptionPreference
)
from ..schemas.subscriber import (
    SubscriberCreate, SubscriberUpdate,
    SubscriberSegmentCreate, SubscriptionPreferenceCreate,
    SubscriptionPreferenceUpdate, SubscriberFilter
)


class SubscriberCRUD(BaseCRUD[Subscriber, SubscriberCreate, SubscriberUpdate]):
    """CRUD operations for subscribers"""
    
    def __init__(self):
        super().__init__(Subscriber)
    
    async def get_by_email(
        self,
        session: AsyncSession,
        email: str
    ) -> Optional[Subscriber]:
        """Get subscriber by email"""
        stmt = select(self.model).where(self.model.email == email)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_active_subscribers(
        self,
        session: AsyncSession,
        skip: int = 0,
        limit: int = 1000
    ) -> List[Subscriber]:
        """Get active subscribers"""
        stmt = (
            select(self.model)
            .where(self.model.status == 'active')
            .order_by(self.model.subscription_date.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await session.execute(stmt)
        return result.scalars().all()
    
    async def search_subscribers(
        self,
        session: AsyncSession,
        filters: Optional[SubscriberFilter] = None,
        search_query: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Subscriber]:
        """Search subscribers with filters"""
        stmt = select(self.model)
        
        # Apply search query
        if search_query:
            search_conditions = [
                self.model.email.ilike(f'%{search_query}%'),
                self.model.first_name.ilike(f'%{search_query}%'),
                self.model.last_name.ilike(f'%{search_query}%'),
                self.model.full_name.ilike(f'%{search_query}%')
            ]
            stmt = stmt.where(or_(*search_conditions))
        
        # Apply filters
        if filters:
            if filters.status:
                stmt = stmt.where(self.model.status == filters.status)
            if filters.source:
                stmt = stmt.where(self.model.source == filters.source)
            if filters.country:
                stmt = stmt.where(self.model.country == filters.country)
            if filters.tags:
                stmt = stmt.where(self.model.tags.op('&&')(filters.tags))
            if filters.subscribed_after:
                stmt = stmt.where(self.model.subscription_date >= filters.subscribed_after)
            if filters.subscribed_before:
                stmt = stmt.where(self.model.subscription_date <= filters.subscribed_before)
        
        stmt = stmt.order_by(self.model.subscription_date.desc()).offset(skip).limit(limit)
        result = await session.execute(stmt)
        return result.scalars().all()
    
    async def update_status(
        self,
        session: AsyncSession,
        subscriber_id: uuid.UUID,
        status: str
    ) -> Optional[Subscriber]:
        """Update subscriber status"""
        subscriber = await self.get(session, subscriber_id)
        if not subscriber:
            return None
        
        subscriber.status = status
        subscriber.last_activity_at = datetime.utcnow()
        
        if status == 'unsubscribed':
            subscriber.unsubscribed_at = datetime.utcnow()
        
        session.add(subscriber)
        await session.commit()
        await session.refresh(subscriber)
        return subscriber
    
    async def add_tags(
        self,
        session: AsyncSession,
        subscriber_id: uuid.UUID,
        tags: List[str]
    ) -> Optional[Subscriber]:
        """Add tags to subscriber"""
        subscriber = await self.get(session, subscriber_id)
        if not subscriber:
            return None
        
        current_tags = set(subscriber.tags or [])
        new_tags = set(tags)
        subscriber.tags = list(current_tags | new_tags)
        
        session.add(subscriber)
        await session.commit()
        await session.refresh(subscriber)
        return subscriber
    
    async def remove_tags(
        self,
        session: AsyncSession,
        subscriber_id: uuid.UUID,
        tags: List[str]
    ) -> Optional[Subscriber]:
        """Remove tags from subscriber"""
        subscriber = await self.get(session, subscriber_id)
        if not subscriber:
            return None
        
        current_tags = set(subscriber.tags or [])
        tags_to_remove = set(tags)
        subscriber.tags = list(current_tags - tags_to_remove)
        
        session.add(subscriber)
        await session.commit()
        await session.refresh(subscriber)
        return subscriber
    
    async def get_subscriber_stats(
        self,
        session: AsyncSession
    ) -> Dict[str, Any]:
        """Get subscriber statistics"""
        # Total counts by status
        stats_stmt = (
            select(
                self.model.status,
                func.count(self.model.id).label('count')
            )
            .group_by(self.model.status)
        )
        stats_result = await session.execute(stats_stmt)
        status_counts = {row.status: row.count for row in stats_result}
        
        # Recent subscription trends (last 30 days)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        recent_stmt = (
            select(
                func.date(self.model.subscription_date).label('date'),
                func.count(self.model.id).label('count')
            )
            .where(self.model.subscription_date >= thirty_days_ago)
            .group_by(func.date(self.model.subscription_date))
            .order_by(func.date(self.model.subscription_date))
        )
        recent_result = await session.execute(recent_stmt)
        daily_subscriptions = {str(row.date): row.count for row in recent_result}
        
        # Source distribution
        source_stmt = (
            select(
                self.model.source,
                func.count(self.model.id).label('count')
            )
            .where(self.model.source.isnot(None))
            .group_by(self.model.source)
            .order_by(func.count(self.model.id).desc())
        )
        source_result = await session.execute(source_stmt)
        source_distribution = {row.source: row.count for row in source_result}
        
        return {
            'status_counts': status_counts,
            'daily_subscriptions': daily_subscriptions,
            'source_distribution': source_distribution,
            'total_subscribers': sum(status_counts.values())
        }


class SubscriberSegmentCRUD(BaseCRUD[SubscriberSegment, SubscriberSegmentCreate, dict]):
    """CRUD operations for subscriber segments"""
    
    def __init__(self):
        super().__init__(SubscriberSegment)
    
    async def get_active_segments(
        self,
        session: AsyncSession
    ) -> List[SubscriberSegment]:
        """Get all active segments"""
        stmt = (
            select(self.model)
            .where(self.model.is_active == True)
            .order_by(self.model.name)
        )
        result = await session.execute(stmt)
        return result.scalars().all()
    
    async def add_subscriber_to_segment(
        self,
        session: AsyncSession,
        segment_id: int,
        subscriber_id: uuid.UUID,
        added_by: Optional[uuid.UUID] = None
    ) -> bool:
        """Add subscriber to segment"""
        # Check if already exists
        existing_stmt = select(SubscriberSegmentMembership).where(
            and_(
                SubscriberSegmentMembership.segment_id == segment_id,
                SubscriberSegmentMembership.subscriber_id == subscriber_id
            )
        )
        existing_result = await session.execute(existing_stmt)
        if existing_result.scalar_one_or_none():
            return False  # Already exists
        
        # Add membership
        membership = SubscriberSegmentMembership(
            segment_id=segment_id,
            subscriber_id=subscriber_id,
            added_by=added_by
        )
        session.add(membership)
        await session.commit()
        return True
    
    async def remove_subscriber_from_segment(
        self,
        session: AsyncSession,
        segment_id: int,
        subscriber_id: uuid.UUID
    ) -> bool:
        """Remove subscriber from segment"""
        stmt = select(SubscriberSegmentMembership).where(
            and_(
                SubscriberSegmentMembership.segment_id == segment_id,
                SubscriberSegmentMembership.subscriber_id == subscriber_id
            )
        )
        result = await session.execute(stmt)
        membership = result.scalar_one_or_none()
        
        if membership:
            await session.delete(membership)
            await session.commit()
            return True
        return False
    
    async def get_segment_subscribers(
        self,
        session: AsyncSession,
        segment_id: int,
        skip: int = 0,
        limit: int = 1000
    ) -> List[Subscriber]:
        """Get subscribers in a segment"""
        stmt = (
            select(Subscriber)
            .join(SubscriberSegmentMembership)
            .where(SubscriberSegmentMembership.segment_id == segment_id)
            .offset(skip)
            .limit(limit)
        )
        result = await session.execute(stmt)
        return result.scalars().all()


class SubscriptionPreferenceCRUD(BaseCRUD[SubscriptionPreference, SubscriptionPreferenceCreate, SubscriptionPreferenceUpdate]):
    """CRUD operations for subscription preferences"""
    
    def __init__(self):
        super().__init__(SubscriptionPreference)
    
    async def get_by_subscriber(
        self,
        session: AsyncSession,
        subscriber_id: uuid.UUID
    ) -> Optional[SubscriptionPreference]:
        """Get preferences by subscriber ID"""
        stmt = select(self.model).where(self.model.subscriber_id == subscriber_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def create_default_preferences(
        self,
        session: AsyncSession,
        subscriber_id: uuid.UUID
    ) -> SubscriptionPreference:
        """Create default preferences for new subscriber"""
        preferences_data = SubscriptionPreferenceCreate(
            subscriber_id=subscriber_id,
            newsletter_frequency="weekly",
            content_types=["all"],
            marketing_consent=False,
            analytics_consent=False
        )
        return await self.create(session, obj_in=preferences_data)
    
    async def update_consent(
        self,
        session: AsyncSession,
        subscriber_id: uuid.UUID,
        consent_type: str,
        consent_value: bool
    ) -> Optional[SubscriptionPreference]:
        """Update specific consent setting"""
        preferences = await self.get_by_subscriber(session, subscriber_id)
        if not preferences:
            return None
        
        if consent_type == 'marketing':
            preferences.marketing_consent = consent_value
        elif consent_type == 'analytics':
            preferences.analytics_consent = consent_value
        elif consent_type == 'gdpr':
            preferences.gdpr_consent = consent_value
            if consent_value:
                preferences.gdpr_consent_date = datetime.utcnow()
        elif consent_type == 'third_party':
            preferences.third_party_sharing = consent_value
        
        session.add(preferences)
        await session.commit()
        await session.refresh(preferences)
        return preferences


# Create global CRUD instances
subscriber_crud = SubscriberCRUD()
segment_crud = SubscriberSegmentCRUD()
preference_crud = SubscriptionPreferenceCRUD()