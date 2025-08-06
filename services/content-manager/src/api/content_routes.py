"""
Content management API routes
"""
import uuid
from datetime import datetime
from typing import List, Optional
from math import ceil

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ..database.session import get_async_session
from ..crud.content import content_crud, raw_content_crud, category_crud, tag_crud
from ..schemas.content import (
    GeneratedContentCreate, GeneratedContentUpdate, GeneratedContentResponse,
    RawContentCreate, RawContentResponse,
    ContentCategoryCreate, ContentCategoryResponse,
    ContentTagCreate, ContentTagResponse,
    ContentListResponse, ContentFilter
)
from ..services.content_lifecycle import content_lifecycle_service
from ..services.content_scheduler import content_scheduler

router = APIRouter(prefix="/api/v1/content", tags=["content"])


@router.post("/", response_model=GeneratedContentResponse)
async def create_content(
    content_data: GeneratedContentCreate,
    session: AsyncSession = Depends(get_async_session)
):
    """Create new generated content"""
    try:
        content = await content_crud.create(session, obj_in=content_data)
        return content
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/", response_model=ContentListResponse)
async def list_content(
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(50, ge=1, le=100, description="Number of items to return"),
    content_type: Optional[str] = Query(None, description="Filter by content type"),
    status: Optional[str] = Query(None, description="Filter by status"),
    search: Optional[str] = Query(None, description="Search in title and content"),
    session: AsyncSession = Depends(get_async_session)
):
    """List content with pagination and filtering"""
    try:
        # Create filter object
        filters = ContentFilter(
            content_type=content_type,
            status=status
        )
        
        if search:
            content_items = await content_crud.search_content(
                session, search, filters, skip, limit
            )
        else:
            filter_dict = {}
            if content_type:
                filter_dict['content_type'] = content_type
            if status:
                filter_dict['status'] = status
            
            content_items = await content_crud.get_multi(
                session, skip=skip, limit=limit, filters=filter_dict
            )
        
        # Get total count
        filter_dict = {}
        if content_type:
            filter_dict['content_type'] = content_type
        if status:
            filter_dict['status'] = status
        
        total = await content_crud.count(session, filters=filter_dict)
        
        return ContentListResponse(
            items=content_items,
            total=total,
            page=skip // limit + 1,
            size=limit,
            pages=ceil(total / limit)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{content_id}", response_model=GeneratedContentResponse)
async def get_content(
    content_id: uuid.UUID,
    session: AsyncSession = Depends(get_async_session)
):
    """Get content by ID"""
    content = await content_crud.get(session, content_id)
    if not content:
        raise HTTPException(status_code=404, detail="Content not found")
    return content


@router.put("/{content_id}", response_model=GeneratedContentResponse)
async def update_content(
    content_id: uuid.UUID,
    update_data: GeneratedContentUpdate,
    session: AsyncSession = Depends(get_async_session)
):
    """Update content"""
    content = await content_crud.get(session, content_id)
    if not content:
        raise HTTPException(status_code=404, detail="Content not found")
    
    try:
        updated_content = await content_crud.update(
            session, db_obj=content, obj_in=update_data
        )
        return updated_content
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{content_id}")
async def delete_content(
    content_id: uuid.UUID,
    session: AsyncSession = Depends(get_async_session)
):
    """Delete content"""
    content = await content_crud.delete(session, id=content_id)
    if not content:
        raise HTTPException(status_code=404, detail="Content not found")
    
    return {"message": "Content deleted successfully"}


@router.post("/{content_id}/status")
async def update_content_status(
    content_id: uuid.UUID,
    new_status: str,
    user_id: Optional[uuid.UUID] = None,
    notes: Optional[str] = None,
    session: AsyncSession = Depends(get_async_session)
):
    """Update content status with lifecycle management"""
    success, content, error = await content_lifecycle_service.transition_content_status(
        session, content_id, new_status, user_id, notes
    )
    
    if not success:
        raise HTTPException(status_code=400, detail=error)
    
    return {
        "success": True,
        "content_id": str(content_id),
        "new_status": new_status,
        "updated_content": content
    }


@router.post("/{content_id}/schedule")
async def schedule_content(
    content_id: uuid.UUID,
    scheduled_for: datetime,
    user_id: Optional[uuid.UUID] = None,
    session: AsyncSession = Depends(get_async_session)
):
    """Schedule content for publication"""
    success, content, error = await content_scheduler.schedule_content(
        session, content_id, scheduled_for, user_id
    )
    
    if not success:
        raise HTTPException(status_code=400, detail=error)
    
    return {
        "success": True,
        "content_id": str(content_id),
        "scheduled_for": scheduled_for.isoformat(),
        "content": content
    }


@router.get("/{content_id}/metrics")
async def get_content_metrics(
    content_id: uuid.UUID,
    session: AsyncSession = Depends(get_async_session)
):
    """Get content performance metrics"""
    metrics = await content_crud.get_content_metrics_summary(session, content_id)
    
    if not metrics:
        raise HTTPException(status_code=404, detail="Content not found or no metrics available")
    
    return metrics


@router.get("/status/{status}")
async def get_content_by_status(
    status: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    session: AsyncSession = Depends(get_async_session)
):
    """Get content by status"""
    try:
        content_items = await content_crud.get_by_status(
            session, status, skip, limit
        )
        
        return {
            "items": content_items,
            "status": status,
            "count": len(content_items)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Raw Content endpoints
@router.post("/raw", response_model=RawContentResponse)
async def create_raw_content(
    content_data: RawContentCreate,
    session: AsyncSession = Depends(get_async_session)
):
    """Create raw scraped content"""
    try:
        content = await raw_content_crud.create(session, obj_in=content_data)
        return content
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/raw/unprocessed")
async def get_unprocessed_raw_content(
    limit: int = Query(50, ge=1, le=100),
    session: AsyncSession = Depends(get_async_session)
):
    """Get unprocessed raw content"""
    try:
        content_items = await raw_content_crud.get_unprocessed(session, limit)
        return {
            "items": content_items,
            "count": len(content_items)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/raw/{content_id}/process")
async def mark_raw_content_processed(
    content_id: uuid.UUID,
    processing_status: str = "completed",
    processing_error: Optional[str] = None,
    session: AsyncSession = Depends(get_async_session)
):
    """Mark raw content as processed"""
    content = await raw_content_crud.mark_processed(
        session, content_id, processing_status, processing_error
    )
    
    if not content:
        raise HTTPException(status_code=404, detail="Raw content not found")
    
    return {
        "success": True,
        "content_id": str(content_id),
        "processing_status": processing_status
    }


# Category endpoints
@router.get("/categories", response_model=List[ContentCategoryResponse])
async def list_categories(
    active_only: bool = Query(True, description="Only return active categories"),
    session: AsyncSession = Depends(get_async_session)
):
    """List content categories"""
    if active_only:
        categories = await category_crud.get_active_categories(session)
    else:
        categories = await category_crud.get_multi(session, limit=1000)
    
    return categories


@router.post("/categories", response_model=ContentCategoryResponse)
async def create_category(
    category_data: ContentCategoryCreate,
    session: AsyncSession = Depends(get_async_session)
):
    """Create content category"""
    try:
        category = await category_crud.create(session, obj_in=category_data)
        return category
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# Tag endpoints
@router.get("/tags", response_model=List[ContentTagResponse])
async def list_tags(
    popular_only: bool = Query(False, description="Only return popular tags"),
    limit: int = Query(100, ge=1, le=500),
    session: AsyncSession = Depends(get_async_session)
):
    """List content tags"""
    if popular_only:
        tags = await tag_crud.get_popular_tags(session, limit)
    else:
        tags = await tag_crud.get_multi(session, limit=limit)
    
    return tags


@router.post("/tags", response_model=ContentTagResponse)
async def create_tag(
    tag_data: ContentTagCreate,
    session: AsyncSession = Depends(get_async_session)
):
    """Create content tag"""
    try:
        tag = await tag_crud.create(session, obj_in=tag_data)
        return tag
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/tags/batch")
async def create_tags_from_names(
    tag_names: List[str],
    session: AsyncSession = Depends(get_async_session)
):
    """Create multiple tags from names"""
    try:
        tags = await tag_crud.create_tags_from_names(session, tag_names)
        return {
            "created_tags": tags,
            "count": len(tags)
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# Bulk operations
@router.post("/bulk/status")
async def bulk_update_status(
    content_ids: List[uuid.UUID],
    new_status: str,
    user_id: Optional[uuid.UUID] = None,
    session: AsyncSession = Depends(get_async_session)
):
    """Bulk update content status"""
    results = await content_lifecycle_service.bulk_transition_content(
        session, content_ids, new_status, user_id
    )
    
    return results


@router.post("/bulk/schedule")
async def bulk_schedule_content(
    content_ids: List[uuid.UUID],
    start_date: Optional[datetime] = None,
    frequency_hours: int = Query(24, ge=1, le=168, description="Hours between publications"),
    session: AsyncSession = Depends(get_async_session)
):
    """Bulk schedule content for publication"""
    results = await content_scheduler.create_publishing_schedule(
        session, content_ids, start_date, frequency_hours
    )
    
    return results