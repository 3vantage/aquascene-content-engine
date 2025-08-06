"""
Subscriber API routes for the Subscriber Manager Service
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, EmailStr
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

from ..services.subscriber_service import SubscriberService
from ..config.settings import get_settings

logger = logging.getLogger(__name__)
router = APIRouter()
settings = get_settings()

subscriber_service = SubscriberService()


class SubscribeRequest(BaseModel):
    """Subscribe request model"""
    email: EmailStr
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    interests: Optional[List[str]] = []


class UpdateSubscriberRequest(BaseModel):
    """Update subscriber request model"""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    interests: Optional[List[str]] = None
    is_active: Optional[bool] = None


@router.post("/subscribe")
async def subscribe(request: SubscribeRequest) -> Dict[str, Any]:
    """Subscribe a new user to the newsletter"""
    try:
        subscriber_id = await subscriber_service.subscribe(
            email=request.email,
            first_name=request.first_name,
            last_name=request.last_name,
            interests=request.interests or []
        )
        
        return {
            "message": "Successfully subscribed",
            "subscriber_id": subscriber_id,
            "email": request.email,
            "status": "pending"
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Subscribe error: {e}")
        raise HTTPException(status_code=500, detail="Subscription failed")


@router.post("/unsubscribe")
async def unsubscribe(email: EmailStr) -> Dict[str, Any]:
    """Unsubscribe a user from the newsletter"""
    try:
        success = await subscriber_service.unsubscribe(email)
        if not success:
            raise HTTPException(status_code=404, detail="Subscriber not found")
        
        return {
            "message": "Successfully unsubscribed",
            "email": email
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unsubscribe error: {e}")
        raise HTTPException(status_code=500, detail="Unsubscribe failed")


@router.get("/confirm/{token}")
async def confirm_subscription(token: str) -> Dict[str, Any]:
    """Confirm email subscription"""
    try:
        success = await subscriber_service.confirm_subscription(token)
        if not success:
            raise HTTPException(status_code=400, detail="Invalid or expired token")
        
        return {
            "message": "Subscription confirmed successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Confirm subscription error: {e}")
        raise HTTPException(status_code=500, detail="Confirmation failed")


@router.get("/{subscriber_id}")
async def get_subscriber(subscriber_id: str) -> Dict[str, Any]:
    """Get subscriber details"""
    try:
        subscriber = await subscriber_service.get_subscriber(subscriber_id)
        if not subscriber:
            raise HTTPException(status_code=404, detail="Subscriber not found")
        
        return subscriber
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get subscriber error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get subscriber")


@router.put("/{subscriber_id}")
async def update_subscriber(
    subscriber_id: str,
    request: UpdateSubscriberRequest
) -> Dict[str, Any]:
    """Update subscriber details"""
    try:
        success = await subscriber_service.update_subscriber(
            subscriber_id=subscriber_id,
            first_name=request.first_name,
            last_name=request.last_name,
            interests=request.interests,
            is_active=request.is_active
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="Subscriber not found")
        
        return {
            "message": "Subscriber updated successfully",
            "subscriber_id": subscriber_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update subscriber error: {e}")
        raise HTTPException(status_code=500, detail="Update failed")


@router.get("")
async def list_subscribers(
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(50, ge=1, le=1000),
    offset: int = Query(0, ge=0)
) -> Dict[str, Any]:
    """List subscribers with optional filtering"""
    try:
        subscribers, total = await subscriber_service.list_subscribers(
            status=status,
            limit=limit,
            offset=offset
        )
        
        return {
            "subscribers": subscribers,
            "total": total,
            "limit": limit,
            "offset": offset
        }
        
    except Exception as e:
        logger.error(f"List subscribers error: {e}")
        raise HTTPException(status_code=500, detail="Failed to list subscribers")


@router.get("/stats")
async def get_subscriber_stats() -> Dict[str, Any]:
    """Get subscriber statistics"""
    try:
        stats = await subscriber_service.get_stats()
        return stats
        
    except Exception as e:
        logger.error(f"Get subscriber stats error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get statistics")