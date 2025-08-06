"""
Subscriber management API routes
"""
import uuid
from typing import List, Optional
from math import ceil

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ..database.session import get_async_session
from ..crud.subscriber import subscriber_crud, segment_crud, preference_crud
from ..schemas.subscriber import (
    SubscriberCreate, SubscriberUpdate, SubscriberResponse,
    SubscriberSegmentCreate, SubscriberSegmentResponse,
    SubscriptionPreferenceCreate, SubscriptionPreferenceUpdate, SubscriptionPreferenceResponse,
    SubscriberListResponse, SubscriberFilter
)

router = APIRouter(prefix="/api/v1/subscribers", tags=["subscribers"])


@router.post("/", response_model=SubscriberResponse)
async def create_subscriber(
    subscriber_data: SubscriberCreate,
    session: AsyncSession = Depends(get_async_session)
):
    """Create new subscriber"""
    try:
        # Check if subscriber already exists
        existing = await subscriber_crud.get_by_email(session, subscriber_data.email)
        if existing:
            raise HTTPException(status_code=400, detail="Email already registered")
        
        # Create subscriber
        subscriber = await subscriber_crud.create(session, obj_in=subscriber_data)
        
        # Create default preferences
        await preference_crud.create_default_preferences(session, subscriber.id)
        
        return subscriber
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/", response_model=SubscriberListResponse)
async def list_subscribers(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    status: Optional[str] = Query(None, description="Filter by status"),
    source: Optional[str] = Query(None, description="Filter by source"),
    search: Optional[str] = Query(None, description="Search in name and email"),
    session: AsyncSession = Depends(get_async_session)
):
    """List subscribers with pagination and filtering"""
    try:
        filters = SubscriberFilter(
            status=status,
            source=source
        )
        
        subscribers = await subscriber_crud.search_subscribers(
            session, filters, search, skip, limit
        )
        
        # Get total count (simplified - in production you'd optimize this)
        filter_dict = {}
        if status:
            filter_dict['status'] = status
        if source:
            filter_dict['source'] = source
        
        total = await subscriber_crud.count(session, filters=filter_dict)
        
        return SubscriberListResponse(
            items=subscribers,
            total=total,
            page=skip // limit + 1,
            size=limit,
            pages=ceil(total / limit)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{subscriber_id}", response_model=SubscriberResponse)
async def get_subscriber(
    subscriber_id: uuid.UUID,
    session: AsyncSession = Depends(get_async_session)
):
    """Get subscriber by ID"""
    subscriber = await subscriber_crud.get(session, subscriber_id)
    if not subscriber:
        raise HTTPException(status_code=404, detail="Subscriber not found")
    return subscriber


@router.get("/email/{email}", response_model=SubscriberResponse)
async def get_subscriber_by_email(
    email: str,
    session: AsyncSession = Depends(get_async_session)
):
    """Get subscriber by email"""
    subscriber = await subscriber_crud.get_by_email(session, email)
    if not subscriber:
        raise HTTPException(status_code=404, detail="Subscriber not found")
    return subscriber


@router.put("/{subscriber_id}", response_model=SubscriberResponse)
async def update_subscriber(
    subscriber_id: uuid.UUID,
    update_data: SubscriberUpdate,
    session: AsyncSession = Depends(get_async_session)
):
    """Update subscriber"""
    subscriber = await subscriber_crud.get(session, subscriber_id)
    if not subscriber:
        raise HTTPException(status_code=404, detail="Subscriber not found")
    
    try:
        updated_subscriber = await subscriber_crud.update(
            session, db_obj=subscriber, obj_in=update_data
        )
        return updated_subscriber
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{subscriber_id}")
async def delete_subscriber(
    subscriber_id: uuid.UUID,
    session: AsyncSession = Depends(get_async_session)
):
    """Delete subscriber"""
    subscriber = await subscriber_crud.delete(session, id=subscriber_id)
    if not subscriber:
        raise HTTPException(status_code=404, detail="Subscriber not found")
    
    return {"message": "Subscriber deleted successfully"}


@router.post("/{subscriber_id}/status")
async def update_subscriber_status(
    subscriber_id: uuid.UUID,
    status: str,
    session: AsyncSession = Depends(get_async_session)
):
    """Update subscriber status"""
    valid_statuses = ['active', 'inactive', 'unsubscribed', 'bounced']
    if status not in valid_statuses:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
        )
    
    subscriber = await subscriber_crud.update_status(session, subscriber_id, status)
    if not subscriber:
        raise HTTPException(status_code=404, detail="Subscriber not found")
    
    return {
        "success": True,
        "subscriber_id": str(subscriber_id),
        "new_status": status,
        "updated_at": subscriber.updated_at.isoformat()
    }


@router.post("/{subscriber_id}/tags")
async def add_subscriber_tags(
    subscriber_id: uuid.UUID,
    tags: List[str],
    session: AsyncSession = Depends(get_async_session)
):
    """Add tags to subscriber"""
    subscriber = await subscriber_crud.add_tags(session, subscriber_id, tags)
    if not subscriber:
        raise HTTPException(status_code=404, detail="Subscriber not found")
    
    return {
        "success": True,
        "subscriber_id": str(subscriber_id),
        "added_tags": tags,
        "current_tags": subscriber.tags
    }


@router.delete("/{subscriber_id}/tags")
async def remove_subscriber_tags(
    subscriber_id: uuid.UUID,
    tags: List[str],
    session: AsyncSession = Depends(get_async_session)
):
    """Remove tags from subscriber"""
    subscriber = await subscriber_crud.remove_tags(session, subscriber_id, tags)
    if not subscriber:
        raise HTTPException(status_code=404, detail="Subscriber not found")
    
    return {
        "success": True,
        "subscriber_id": str(subscriber_id),
        "removed_tags": tags,
        "current_tags": subscriber.tags
    }


@router.get("/status/{status}")
async def get_subscribers_by_status(
    status: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    session: AsyncSession = Depends(get_async_session)
):
    """Get subscribers by status"""
    try:
        subscribers = await subscriber_crud.get_multi(
            session, skip=skip, limit=limit, filters={'status': status}
        )
        
        return {
            "subscribers": subscribers,
            "status": status,
            "count": len(subscribers)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/active/all")
async def get_active_subscribers(
    skip: int = Query(0, ge=0),
    limit: int = Query(1000, ge=1, le=5000),
    session: AsyncSession = Depends(get_async_session)
):
    """Get all active subscribers"""
    try:
        subscribers = await subscriber_crud.get_active_subscribers(session, skip, limit)
        return {
            "subscribers": subscribers,
            "count": len(subscribers)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats/overview")
async def get_subscriber_statistics(
    session: AsyncSession = Depends(get_async_session)
):
    """Get subscriber statistics overview"""
    try:
        stats = await subscriber_crud.get_subscriber_stats(session)
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Subscription Preferences
@router.get("/{subscriber_id}/preferences", response_model=SubscriptionPreferenceResponse)
async def get_subscriber_preferences(
    subscriber_id: uuid.UUID,
    session: AsyncSession = Depends(get_async_session)
):
    """Get subscriber preferences"""
    preferences = await preference_crud.get_by_subscriber(session, subscriber_id)
    if not preferences:
        # Create default preferences if they don't exist
        preferences = await preference_crud.create_default_preferences(session, subscriber_id)
    
    return preferences


@router.put("/{subscriber_id}/preferences", response_model=SubscriptionPreferenceResponse)
async def update_subscriber_preferences(
    subscriber_id: uuid.UUID,
    preference_update: SubscriptionPreferenceUpdate,
    session: AsyncSession = Depends(get_async_session)
):
    """Update subscriber preferences"""
    preferences = await preference_crud.get_by_subscriber(session, subscriber_id)
    if not preferences:
        raise HTTPException(status_code=404, detail="Subscriber preferences not found")
    
    try:
        updated_preferences = await preference_crud.update(
            session, db_obj=preferences, obj_in=preference_update
        )
        return updated_preferences
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{subscriber_id}/consent")
async def update_consent(
    subscriber_id: uuid.UUID,
    consent_type: str,
    consent_value: bool,
    session: AsyncSession = Depends(get_async_session)
):
    """Update specific consent setting"""
    valid_consent_types = ['marketing', 'analytics', 'gdpr', 'third_party']
    if consent_type not in valid_consent_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid consent type. Must be one of: {', '.join(valid_consent_types)}"
        )
    
    preferences = await preference_crud.update_consent(
        session, subscriber_id, consent_type, consent_value
    )
    
    if not preferences:
        raise HTTPException(status_code=404, detail="Subscriber not found")
    
    return {
        "success": True,
        "subscriber_id": str(subscriber_id),
        "consent_type": consent_type,
        "consent_value": consent_value,
        "updated_at": preferences.updated_at.isoformat()
    }


# Subscriber Segments
@router.post("/segments", response_model=SubscriberSegmentResponse)
async def create_subscriber_segment(
    segment_data: SubscriberSegmentCreate,
    session: AsyncSession = Depends(get_async_session)
):
    """Create subscriber segment"""
    try:
        segment = await segment_crud.create(session, obj_in=segment_data)
        return segment
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/segments", response_model=List[SubscriberSegmentResponse])
async def list_subscriber_segments(
    active_only: bool = Query(True, description="Only return active segments"),
    session: AsyncSession = Depends(get_async_session)
):
    """List subscriber segments"""
    try:
        if active_only:
            segments = await segment_crud.get_active_segments(session)
        else:
            segments = await segment_crud.get_multi(session, limit=100)
        
        return segments
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/segments/{segment_id}", response_model=SubscriberSegmentResponse)
async def get_subscriber_segment(
    segment_id: int,
    session: AsyncSession = Depends(get_async_session)
):
    """Get subscriber segment by ID"""
    segment = await segment_crud.get(session, segment_id)
    if not segment:
        raise HTTPException(status_code=404, detail="Subscriber segment not found")
    return segment


@router.post("/segments/{segment_id}/subscribers/{subscriber_id}")
async def add_subscriber_to_segment(
    segment_id: int,
    subscriber_id: uuid.UUID,
    added_by: Optional[uuid.UUID] = None,
    session: AsyncSession = Depends(get_async_session)
):
    """Add subscriber to segment"""
    success = await segment_crud.add_subscriber_to_segment(
        session, segment_id, subscriber_id, added_by
    )
    
    if not success:
        raise HTTPException(
            status_code=400, 
            detail="Subscriber already in segment or segment/subscriber not found"
        )
    
    return {
        "success": True,
        "segment_id": segment_id,
        "subscriber_id": str(subscriber_id),
        "message": "Subscriber added to segment"
    }


@router.delete("/segments/{segment_id}/subscribers/{subscriber_id}")
async def remove_subscriber_from_segment(
    segment_id: int,
    subscriber_id: uuid.UUID,
    session: AsyncSession = Depends(get_async_session)
):
    """Remove subscriber from segment"""
    success = await segment_crud.remove_subscriber_from_segment(
        session, segment_id, subscriber_id
    )
    
    if not success:
        raise HTTPException(
            status_code=404,
            detail="Subscriber not in segment or segment/subscriber not found"
        )
    
    return {
        "success": True,
        "segment_id": segment_id,
        "subscriber_id": str(subscriber_id),
        "message": "Subscriber removed from segment"
    }


@router.get("/segments/{segment_id}/subscribers")
async def get_segment_subscribers(
    segment_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    session: AsyncSession = Depends(get_async_session)
):
    """Get subscribers in a segment"""
    try:
        subscribers = await segment_crud.get_segment_subscribers(
            session, segment_id, skip, limit
        )
        
        return {
            "subscribers": subscribers,
            "segment_id": segment_id,
            "count": len(subscribers)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))