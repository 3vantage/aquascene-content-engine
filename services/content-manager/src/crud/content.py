"""
Content CRUD operations
"""
import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy import select, update, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from .base import BaseCRUD
from ..models.content import GeneratedContent, RawContent, ContentCategory, ContentTag
from ..schemas.content import (
    GeneratedContentCreate, GeneratedContentUpdate,
    RawContentCreate, ContentCategoryCreate,
    ContentTagCreate, ContentFilter
)


class ContentCRUD(BaseCRUD[GeneratedContent, GeneratedContentCreate, GeneratedContentUpdate]):
    """CRUD operations for generated content"""
    
    def __init__(self):
        super().__init__(GeneratedContent)
    
    async def get_by_status(
        self, 
        session: AsyncSession, 
        status: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[GeneratedContent]:
        """Get content by status"""
        stmt = (
            select(self.model)
            .where(self.model.status == status)
            .order_by(self.model.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await session.execute(stmt)
        return result.scalars().all()
    
    async def get_scheduled_content(
        self,
        session: AsyncSession,
        before_datetime: Optional[datetime] = None
    ) -> List[GeneratedContent]:
        """Get content scheduled for publishing"""
        stmt = select(self.model).where(
            and_(
                self.model.status == 'approved',
                self.model.scheduled_for.isnot(None)
            )
        )
        
        if before_datetime:
            stmt = stmt.where(self.model.scheduled_for <= before_datetime)
        
        result = await session.execute(stmt)
        return result.scalars().all()
    
    async def search_content(
        self,
        session: AsyncSession,
        query: str,
        filters: Optional[ContentFilter] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[GeneratedContent]:
        """Search content with full-text search and filters"""
        stmt = select(self.model)
        
        # Full-text search
        if query:
            search_vector = func.to_tsvector('english', self.model.title + ' ' + self.model.content)
            search_query = func.plainto_tsquery('english', query)
            stmt = stmt.where(search_vector.op('@@')(search_query))
        
        # Apply filters
        if filters:
            if filters.content_type:
                stmt = stmt.where(self.model.content_type == filters.content_type)
            if filters.status:
                stmt = stmt.where(self.model.status == filters.status)
            if filters.tags:
                stmt = stmt.where(self.model.tags.op('&&')(filters.tags))
            if filters.categories:
                stmt = stmt.where(self.model.categories.op('&&')(filters.categories))
            if filters.created_after:
                stmt = stmt.where(self.model.created_at >= filters.created_after)
            if filters.created_before:
                stmt = stmt.where(self.model.created_at <= filters.created_before)
        
        stmt = stmt.order_by(self.model.created_at.desc()).offset(skip).limit(limit)
        result = await session.execute(stmt)
        return result.scalars().all()
    
    async def update_status(
        self,
        session: AsyncSession,
        content_id: uuid.UUID,
        status: str,
        approved_by: Optional[uuid.UUID] = None
    ) -> Optional[GeneratedContent]:
        """Update content status with approval tracking"""
        content = await self.get(session, content_id)
        if not content:
            return None
        
        content.status = status
        
        if status == 'approved' and approved_by:
            content.approved_by = approved_by
            content.approved_at = datetime.utcnow()
        elif status == 'published':
            content.published_at = datetime.utcnow()
        
        session.add(content)
        await session.commit()
        await session.refresh(content)
        return content
    
    async def get_content_metrics_summary(
        self,
        session: AsyncSession,
        content_id: uuid.UUID
    ) -> Dict[str, Any]:
        """Get content performance metrics summary"""
        from ..models.metrics import ContentMetric
        
        # Get basic content info
        content = await self.get(session, content_id)
        if not content:
            return {}
        
        # Get metrics
        metrics_stmt = (
            select(
                ContentMetric.metric_name,
                func.sum(ContentMetric.metric_value).label('total_value')
            )
            .where(ContentMetric.content_id == content_id)
            .group_by(ContentMetric.metric_name)
        )
        
        metrics_result = await session.execute(metrics_stmt)
        metrics = {row.metric_name: float(row.total_value or 0) for row in metrics_result}
        
        return {
            'content_id': content_id,
            'title': content.title,
            'status': content.status,
            'published_at': content.published_at,
            'metrics': metrics
        }


class RawContentCRUD(BaseCRUD[RawContent, RawContentCreate, Dict]):
    """CRUD operations for raw scraped content"""
    
    def __init__(self):
        super().__init__(RawContent)
    
    async def get_unprocessed(
        self,
        session: AsyncSession,
        limit: int = 50
    ) -> List[RawContent]:
        """Get unprocessed raw content"""
        stmt = (
            select(self.model)
            .where(self.model.processed == False)
            .order_by(self.model.scraped_at.asc())
            .limit(limit)
        )
        result = await session.execute(stmt)
        return result.scalars().all()
    
    async def mark_processed(
        self,
        session: AsyncSession,
        content_id: uuid.UUID,
        processing_status: str = 'completed',
        processing_error: Optional[str] = None
    ) -> Optional[RawContent]:
        """Mark raw content as processed"""
        content = await self.get(session, content_id)
        if not content:
            return None
        
        content.processed = processing_status == 'completed'
        content.processing_status = processing_status
        content.processing_error = processing_error
        
        session.add(content)
        await session.commit()
        await session.refresh(content)
        return content
    
    async def get_by_source_domain(
        self,
        session: AsyncSession,
        domain: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[RawContent]:
        """Get raw content by source domain"""
        stmt = (
            select(self.model)
            .where(self.model.source_domain == domain)
            .order_by(self.model.scraped_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await session.execute(stmt)
        return result.scalars().all()


class ContentCategoryCRUD(BaseCRUD[ContentCategory, ContentCategoryCreate, Dict]):
    """CRUD operations for content categories"""
    
    def __init__(self):
        super().__init__(ContentCategory)
    
    async def get_active_categories(
        self,
        session: AsyncSession
    ) -> List[ContentCategory]:
        """Get all active categories"""
        stmt = (
            select(self.model)
            .where(self.model.is_active == True)
            .order_by(self.model.sort_order, self.model.name)
        )
        result = await session.execute(stmt)
        return result.scalars().all()
    
    async def get_by_slug(
        self,
        session: AsyncSession,
        slug: str
    ) -> Optional[ContentCategory]:
        """Get category by slug"""
        stmt = select(self.model).where(self.model.slug == slug)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()


class ContentTagCRUD(BaseCRUD[ContentTag, ContentTagCreate, Dict]):
    """CRUD operations for content tags"""
    
    def __init__(self):
        super().__init__(ContentTag)
    
    async def get_popular_tags(
        self,
        session: AsyncSession,
        limit: int = 20
    ) -> List[ContentTag]:
        """Get most popular tags by usage count"""
        stmt = (
            select(self.model)
            .order_by(self.model.usage_count.desc())
            .limit(limit)
        )
        result = await session.execute(stmt)
        return result.scalars().all()
    
    async def get_by_names(
        self,
        session: AsyncSession,
        names: List[str]
    ) -> List[ContentTag]:
        """Get tags by names"""
        stmt = select(self.model).where(self.model.name.in_(names))
        result = await session.execute(stmt)
        return result.scalars().all()
    
    async def create_tags_from_names(
        self,
        session: AsyncSession,
        tag_names: List[str]
    ) -> List[ContentTag]:
        """Create tags if they don't exist and return all tags"""
        # Get existing tags
        existing_tags = await self.get_by_names(session, tag_names)
        existing_names = {tag.name for tag in existing_tags}
        
        # Create missing tags
        new_tags = []
        for name in tag_names:
            if name not in existing_names:
                slug = name.lower().replace(' ', '-').replace('_', '-')
                tag_data = ContentTagCreate(name=name, slug=slug)
                new_tag = await self.create(session, obj_in=tag_data)
                new_tags.append(new_tag)
        
        return existing_tags + new_tags


# Create global CRUD instances
content_crud = ContentCRUD()
raw_content_crud = RawContentCRUD()
category_crud = ContentCategoryCRUD()
tag_crud = ContentTagCRUD()