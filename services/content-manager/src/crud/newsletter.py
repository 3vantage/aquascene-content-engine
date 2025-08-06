"""
Newsletter CRUD operations
"""
import uuid
from datetime import datetime
from typing import List, Optional
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from .base import BaseCRUD
from ..models.newsletter import NewsletterIssue, NewsletterTemplate
from ..models.metrics import NewsletterMetric
from ..schemas.newsletter import (
    NewsletterIssueCreate, NewsletterIssueUpdate,
    NewsletterTemplateCreate, NewsletterMetricCreate
)


class NewsletterCRUD(BaseCRUD[NewsletterIssue, NewsletterIssueCreate, NewsletterIssueUpdate]):
    """CRUD operations for newsletter issues"""
    
    def __init__(self):
        super().__init__(NewsletterIssue)
    
    async def get_scheduled_issues(
        self,
        session: AsyncSession,
        before_datetime: Optional[datetime] = None
    ) -> List[NewsletterIssue]:
        """Get issues scheduled for sending"""
        stmt = select(self.model).where(
            and_(
                self.model.status == 'scheduled',
                self.model.scheduled_for.isnot(None)
            )
        )
        
        if before_datetime:
            stmt = stmt.where(self.model.scheduled_for <= before_datetime)
        
        result = await session.execute(stmt)
        return result.scalars().all()
    
    async def get_by_status(
        self,
        session: AsyncSession,
        status: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[NewsletterIssue]:
        """Get issues by status"""
        stmt = (
            select(self.model)
            .where(self.model.status == status)
            .order_by(self.model.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await session.execute(stmt)
        return result.scalars().all()
    
    async def update_status(
        self,
        session: AsyncSession,
        issue_id: uuid.UUID,
        status: str,
        sent_at: Optional[datetime] = None,
        recipient_count: Optional[int] = None
    ) -> Optional[NewsletterIssue]:
        """Update issue status"""
        issue = await self.get(session, issue_id)
        if not issue:
            return None
        
        issue.status = status
        
        if status == 'sent':
            issue.sent_at = sent_at or datetime.utcnow()
            if recipient_count is not None:
                issue.recipient_count = recipient_count
        
        session.add(issue)
        await session.commit()
        await session.refresh(issue)
        return issue
    
    async def get_next_issue_number(
        self,
        session: AsyncSession
    ) -> int:
        """Get the next available issue number"""
        stmt = select(func.coalesce(func.max(self.model.issue_number), 0) + 1)
        result = await session.execute(stmt)
        return result.scalar()
    
    async def get_recent_issues(
        self,
        session: AsyncSession,
        days: int = 30,
        limit: int = 10
    ) -> List[NewsletterIssue]:
        """Get recent issues within specified days"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        stmt = (
            select(self.model)
            .where(self.model.created_at >= cutoff_date)
            .order_by(self.model.created_at.desc())
            .limit(limit)
        )
        result = await session.execute(stmt)
        return result.scalars().all()
    
    async def get_performance_summary(
        self,
        session: AsyncSession,
        issue_id: uuid.UUID
    ) -> dict:
        """Get issue performance summary with metrics"""
        issue = await self.get(session, issue_id)
        if not issue:
            return {}
        
        # Get latest metrics
        metrics_stmt = (
            select(NewsletterMetric)
            .where(NewsletterMetric.issue_id == issue_id)
            .order_by(NewsletterMetric.recorded_at.desc())
            .limit(1)
        )
        metrics_result = await session.execute(metrics_stmt)
        metrics = metrics_result.scalar_one_or_none()
        
        summary = {
            'issue_id': issue_id,
            'subject_line': issue.subject_line,
            'status': issue.status,
            'sent_at': issue.sent_at,
            'recipient_count': issue.recipient_count
        }
        
        if metrics:
            summary.update({
                'sent_count': metrics.sent_count,
                'delivered_count': metrics.delivered_count,
                'open_count': metrics.open_count,
                'click_count': metrics.click_count,
                'open_rate': float(metrics.open_rate or 0),
                'click_rate': float(metrics.click_rate or 0),
                'unsubscribe_count': metrics.unsubscribe_count,
                'bounce_count': metrics.bounce_count
            })
        
        return summary


class NewsletterTemplateCRUD(BaseCRUD[NewsletterTemplate, NewsletterTemplateCreate, dict]):
    """CRUD operations for newsletter templates"""
    
    def __init__(self):
        super().__init__(NewsletterTemplate)
    
    async def get_active_templates(
        self,
        session: AsyncSession
    ) -> List[NewsletterTemplate]:
        """Get all active templates"""
        stmt = (
            select(self.model)
            .where(self.model.is_active == True)
            .order_by(self.model.name)
        )
        result = await session.execute(stmt)
        return result.scalars().all()
    
    async def get_by_template_type(
        self,
        session: AsyncSession,
        template_type: str
    ) -> List[NewsletterTemplate]:
        """Get templates by type"""
        stmt = (
            select(self.model)
            .where(
                and_(
                    self.model.template_type == template_type,
                    self.model.is_active == True
                )
            )
            .order_by(self.model.name)
        )
        result = await session.execute(stmt)
        return result.scalars().all()
    
    async def get_by_name(
        self,
        session: AsyncSession,
        name: str
    ) -> Optional[NewsletterTemplate]:
        """Get template by name"""
        stmt = select(self.model).where(self.model.name == name)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()


class NewsletterMetricCRUD(BaseCRUD[NewsletterMetric, NewsletterMetricCreate, dict]):
    """CRUD operations for newsletter metrics"""
    
    def __init__(self):
        super().__init__(NewsletterMetric)
    
    async def create_or_update_metrics(
        self,
        session: AsyncSession,
        issue_id: uuid.UUID,
        metrics_data: dict
    ) -> NewsletterMetric:
        """Create or update newsletter metrics"""
        # Try to get existing metrics
        existing_stmt = select(self.model).where(self.model.issue_id == issue_id)
        existing_result = await session.execute(existing_stmt)
        existing_metric = existing_result.scalar_one_or_none()
        
        if existing_metric:
            # Update existing metrics
            for key, value in metrics_data.items():
                if hasattr(existing_metric, key):
                    setattr(existing_metric, key, value)
            
            # Recalculate rates
            if existing_metric.sent_count > 0:
                existing_metric.open_rate = existing_metric.open_count / existing_metric.sent_count
                existing_metric.click_rate = existing_metric.click_count / existing_metric.sent_count
                existing_metric.unsubscribe_rate = existing_metric.unsubscribe_count / existing_metric.sent_count
                existing_metric.bounce_rate = existing_metric.bounce_count / existing_metric.sent_count
            
            session.add(existing_metric)
            await session.commit()
            await session.refresh(existing_metric)
            return existing_metric
        else:
            # Create new metrics
            metric_create = NewsletterMetricCreate(
                issue_id=issue_id,
                metric_type='email_campaign',
                **metrics_data
            )
            return await self.create(session, obj_in=metric_create)
    
    async def get_campaign_summary(
        self,
        session: AsyncSession,
        days: int = 30
    ) -> dict:
        """Get newsletter campaign performance summary"""
        from datetime import timedelta
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        stmt = (
            select(
                func.count(NewsletterMetric.id).label('total_campaigns'),
                func.sum(NewsletterMetric.sent_count).label('total_sent'),
                func.sum(NewsletterMetric.delivered_count).label('total_delivered'),
                func.sum(NewsletterMetric.open_count).label('total_opens'),
                func.sum(NewsletterMetric.click_count).label('total_clicks'),
                func.avg(NewsletterMetric.open_rate).label('avg_open_rate'),
                func.avg(NewsletterMetric.click_rate).label('avg_click_rate')
            )
            .where(NewsletterMetric.recorded_at >= cutoff_date)
        )
        
        result = await session.execute(stmt)
        row = result.first()
        
        return {
            'period_days': days,
            'total_campaigns': row.total_campaigns or 0,
            'total_sent': row.total_sent or 0,
            'total_delivered': row.total_delivered or 0,
            'total_opens': row.total_opens or 0,
            'total_clicks': row.total_clicks or 0,
            'average_open_rate': float(row.avg_open_rate or 0),
            'average_click_rate': float(row.avg_click_rate or 0)
        }


# Create global CRUD instances
newsletter_crud = NewsletterCRUD()
newsletter_template_crud = NewsletterTemplateCRUD()
newsletter_metric_crud = NewsletterMetricCRUD()

# Import timedelta at the top
from datetime import timedelta