"""
Newsletter management API routes
"""
import uuid
from datetime import datetime
from typing import List, Optional
from math import ceil

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ..database.session import get_async_session
from ..crud.newsletter import newsletter_crud, newsletter_template_crud, newsletter_metric_crud
from ..schemas.newsletter import (
    NewsletterIssueCreate, NewsletterIssueUpdate, NewsletterIssueResponse,
    NewsletterTemplateCreate, NewsletterTemplateResponse,
    NewsletterMetricCreate, NewsletterMetricResponse
)
from ..services.content_scheduler import content_scheduler

router = APIRouter(prefix="/api/v1/newsletters", tags=["newsletters"])


@router.post("/issues", response_model=NewsletterIssueResponse)
async def create_newsletter_issue(
    issue_data: NewsletterIssueCreate,
    session: AsyncSession = Depends(get_async_session)
):
    """Create new newsletter issue"""
    try:
        # Auto-assign issue number if not provided
        if not issue_data.issue_number:
            issue_data.issue_number = await newsletter_crud.get_next_issue_number(session)
        
        issue = await newsletter_crud.create(session, obj_in=issue_data)
        return issue
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/issues", response_model=List[NewsletterIssueResponse])
async def list_newsletter_issues(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    status: Optional[str] = Query(None, description="Filter by status"),
    session: AsyncSession = Depends(get_async_session)
):
    """List newsletter issues with pagination"""
    try:
        if status:
            issues = await newsletter_crud.get_by_status(session, status, skip, limit)
        else:
            issues = await newsletter_crud.get_multi(session, skip=skip, limit=limit)
        
        return issues
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/issues/{issue_id}", response_model=NewsletterIssueResponse)
async def get_newsletter_issue(
    issue_id: uuid.UUID,
    session: AsyncSession = Depends(get_async_session)
):
    """Get newsletter issue by ID"""
    issue = await newsletter_crud.get(session, issue_id)
    if not issue:
        raise HTTPException(status_code=404, detail="Newsletter issue not found")
    return issue


@router.put("/issues/{issue_id}", response_model=NewsletterIssueResponse)
async def update_newsletter_issue(
    issue_id: uuid.UUID,
    update_data: NewsletterIssueUpdate,
    session: AsyncSession = Depends(get_async_session)
):
    """Update newsletter issue"""
    issue = await newsletter_crud.get(session, issue_id)
    if not issue:
        raise HTTPException(status_code=404, detail="Newsletter issue not found")
    
    try:
        updated_issue = await newsletter_crud.update(
            session, db_obj=issue, obj_in=update_data
        )
        return updated_issue
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/issues/{issue_id}")
async def delete_newsletter_issue(
    issue_id: uuid.UUID,
    session: AsyncSession = Depends(get_async_session)
):
    """Delete newsletter issue"""
    issue = await newsletter_crud.delete(session, id=issue_id)
    if not issue:
        raise HTTPException(status_code=404, detail="Newsletter issue not found")
    
    return {"message": "Newsletter issue deleted successfully"}


@router.post("/issues/{issue_id}/schedule")
async def schedule_newsletter_issue(
    issue_id: uuid.UUID,
    send_time: Optional[datetime] = None,
    frequency: str = Query("weekly", description="Newsletter frequency for optimal timing"),
    session: AsyncSession = Depends(get_async_session)
):
    """Schedule newsletter issue for sending"""
    success, issue, error = await content_scheduler.schedule_newsletter_campaign(
        session, issue_id, send_time, frequency
    )
    
    if not success:
        raise HTTPException(status_code=400, detail=error)
    
    return {
        "success": True,
        "issue_id": str(issue_id),
        "scheduled_for": issue.scheduled_for.isoformat(),
        "issue": issue
    }


@router.post("/issues/{issue_id}/send")
async def send_newsletter_issue(
    issue_id: uuid.UUID,
    recipient_count: Optional[int] = None,
    session: AsyncSession = Depends(get_async_session)
):
    """Mark newsletter issue as sent"""
    issue = await newsletter_crud.update_status(
        session, issue_id, "sent", datetime.utcnow(), recipient_count
    )
    
    if not issue:
        raise HTTPException(status_code=404, detail="Newsletter issue not found")
    
    return {
        "success": True,
        "issue_id": str(issue_id),
        "sent_at": issue.sent_at.isoformat(),
        "recipient_count": issue.recipient_count
    }


@router.get("/issues/{issue_id}/performance")
async def get_newsletter_performance(
    issue_id: uuid.UUID,
    session: AsyncSession = Depends(get_async_session)
):
    """Get newsletter issue performance summary"""
    performance = await newsletter_crud.get_performance_summary(session, issue_id)
    
    if not performance:
        raise HTTPException(status_code=404, detail="Newsletter issue not found or no metrics available")
    
    return performance


@router.get("/issues/status/{status}")
async def get_issues_by_status(
    status: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    session: AsyncSession = Depends(get_async_session)
):
    """Get newsletter issues by status"""
    try:
        issues = await newsletter_crud.get_by_status(session, status, skip, limit)
        
        return {
            "items": issues,
            "status": status,
            "count": len(issues)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/scheduled")
async def get_scheduled_newsletters(
    hours_ahead: int = Query(24, ge=1, le=168),
    session: AsyncSession = Depends(get_async_session)
):
    """Get newsletters scheduled for sending"""
    cutoff_time = datetime.utcnow() + timedelta(hours=hours_ahead)
    scheduled_issues = await newsletter_crud.get_scheduled_issues(session, cutoff_time)
    
    return {
        "scheduled_issues": scheduled_issues,
        "count": len(scheduled_issues),
        "hours_ahead": hours_ahead
    }


# Template endpoints
@router.post("/templates", response_model=NewsletterTemplateResponse)
async def create_newsletter_template(
    template_data: NewsletterTemplateCreate,
    session: AsyncSession = Depends(get_async_session)
):
    """Create newsletter template"""
    try:
        template = await newsletter_template_crud.create(session, obj_in=template_data)
        return template
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/templates", response_model=List[NewsletterTemplateResponse])
async def list_newsletter_templates(
    active_only: bool = Query(True, description="Only return active templates"),
    template_type: Optional[str] = Query(None, description="Filter by template type"),
    session: AsyncSession = Depends(get_async_session)
):
    """List newsletter templates"""
    try:
        if template_type:
            templates = await newsletter_template_crud.get_by_template_type(session, template_type)
        elif active_only:
            templates = await newsletter_template_crud.get_active_templates(session)
        else:
            templates = await newsletter_template_crud.get_multi(session, limit=100)
        
        return templates
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/templates/{template_id}", response_model=NewsletterTemplateResponse)
async def get_newsletter_template(
    template_id: int,
    session: AsyncSession = Depends(get_async_session)
):
    """Get newsletter template by ID"""
    template = await newsletter_template_crud.get(session, template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Newsletter template not found")
    return template


@router.get("/templates/name/{template_name}", response_model=NewsletterTemplateResponse)
async def get_template_by_name(
    template_name: str,
    session: AsyncSession = Depends(get_async_session)
):
    """Get newsletter template by name"""
    template = await newsletter_template_crud.get_by_name(session, template_name)
    if not template:
        raise HTTPException(status_code=404, detail="Newsletter template not found")
    return template


# Metrics endpoints
@router.post("/issues/{issue_id}/metrics", response_model=NewsletterMetricResponse)
async def create_newsletter_metrics(
    issue_id: uuid.UUID,
    metrics_data: NewsletterMetricCreate,
    session: AsyncSession = Depends(get_async_session)
):
    """Create or update newsletter metrics"""
    try:
        metrics_data.issue_id = issue_id
        metrics = await newsletter_metric_crud.create_or_update_metrics(
            session, issue_id, metrics_data.dict()
        )
        return metrics
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/metrics/summary")
async def get_campaign_summary(
    days: int = Query(30, ge=1, le=365, description="Number of days to include in summary"),
    session: AsyncSession = Depends(get_async_session)
):
    """Get newsletter campaign performance summary"""
    try:
        summary = await newsletter_metric_crud.get_campaign_summary(session, days)
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/recent")
async def get_recent_issues(
    days: int = Query(30, ge=1, le=90),
    limit: int = Query(10, ge=1, le=50),
    session: AsyncSession = Depends(get_async_session)
):
    """Get recent newsletter issues"""
    try:
        issues = await newsletter_crud.get_recent_issues(session, days, limit)
        return {
            "issues": issues,
            "period_days": days,
            "count": len(issues)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Import timedelta
from datetime import timedelta