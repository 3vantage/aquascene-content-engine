"""
Subscriber-related Pydantic schemas
"""
import uuid
from datetime import datetime, time
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, EmailStr, ConfigDict


class SubscriberCreate(BaseModel):
    """Schema for creating subscribers"""
    email: EmailStr = Field(..., description="Subscriber email address")
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=50)
    country: Optional[str] = Field(None, max_length=100)
    timezone: str = Field(default="UTC", max_length=50)
    language: str = Field(default="en", max_length=10)
    source: Optional[str] = Field(None, max_length=50)
    tags: Optional[List[str]] = Field(default_factory=list)
    custom_fields: Optional[Dict[str, Any]] = Field(default_factory=dict)


class SubscriberUpdate(BaseModel):
    """Schema for updating subscribers"""
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=50)
    country: Optional[str] = Field(None, max_length=100)
    timezone: Optional[str] = Field(None, max_length=50)
    language: Optional[str] = Field(None, max_length=10)
    status: Optional[str] = Field(None, regex="^(active|inactive|unsubscribed|bounced)$")
    tags: Optional[List[str]] = None
    custom_fields: Optional[Dict[str, Any]] = None


class SubscriberResponse(BaseModel):
    """Schema for subscriber responses"""
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    full_name: Optional[str] = None
    phone: Optional[str] = None
    country: Optional[str] = None
    timezone: str
    language: str
    source: Optional[str] = None
    status: str
    subscription_date: datetime
    confirmed_at: Optional[datetime] = None
    unsubscribed_at: Optional[datetime] = None
    bounce_count: int
    complaint_count: int
    last_activity_at: datetime
    preferences: Optional[Dict] = None
    custom_fields: Optional[Dict] = None
    tags: Optional[List[str]] = None
    created_at: datetime
    updated_at: datetime


class SubscriptionPreferenceCreate(BaseModel):
    """Schema for creating subscription preferences"""
    subscriber_id: uuid.UUID
    newsletter_frequency: str = Field(default="weekly", regex="^(daily|weekly|bi_weekly|monthly)$")
    content_types: List[str] = Field(default=["all"])
    preferred_send_time: time = Field(default=time(9, 0))
    preferred_send_days: List[int] = Field(default=[1, 2, 3, 4, 5])
    email_format: str = Field(default="html", regex="^(html|text)$")
    double_opt_in: bool = Field(default=True)
    marketing_consent: bool = Field(default=False)
    analytics_consent: bool = Field(default=False)
    third_party_sharing: bool = Field(default=False)
    gdpr_consent: bool = Field(default=False)


class SubscriptionPreferenceUpdate(BaseModel):
    """Schema for updating subscription preferences"""
    newsletter_frequency: Optional[str] = Field(None, regex="^(daily|weekly|bi_weekly|monthly)$")
    content_types: Optional[List[str]] = None
    preferred_send_time: Optional[time] = None
    preferred_send_days: Optional[List[int]] = None
    email_format: Optional[str] = Field(None, regex="^(html|text)$")
    double_opt_in: Optional[bool] = None
    marketing_consent: Optional[bool] = None
    analytics_consent: Optional[bool] = None
    third_party_sharing: Optional[bool] = None
    gdpr_consent: Optional[bool] = None


class SubscriptionPreferenceResponse(BaseModel):
    """Schema for subscription preference responses"""
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    subscriber_id: uuid.UUID
    newsletter_frequency: str
    content_types: List[str]
    preferred_send_time: time
    preferred_send_days: List[int]
    email_format: str
    double_opt_in: bool
    marketing_consent: bool
    analytics_consent: bool
    third_party_sharing: bool
    gdpr_consent: bool
    gdpr_consent_date: Optional[datetime] = None
    updated_at: datetime


class SubscriberSegmentCreate(BaseModel):
    """Schema for creating subscriber segments"""
    name: str = Field(..., max_length=100)
    description: Optional[str] = Field(None, max_length=255)
    segment_type: str = Field(default="manual", regex="^(manual|automatic|behavioral)$")
    filter_criteria: Optional[Dict[str, Any]] = Field(default_factory=dict)
    is_active: bool = Field(default=True)


class SubscriberSegmentResponse(BaseModel):
    """Schema for subscriber segment responses"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    name: str
    description: Optional[str] = None
    segment_type: str
    filter_criteria: Optional[Dict] = None
    subscriber_count: int
    is_active: bool
    created_at: datetime
    updated_at: datetime


class SubscriberListResponse(BaseModel):
    """Schema for paginated subscriber lists"""
    items: List[SubscriberResponse]
    total: int
    page: int
    size: int
    pages: int


class SubscriberFilter(BaseModel):
    """Schema for subscriber filtering"""
    status: Optional[str] = None
    source: Optional[str] = None
    country: Optional[str] = None
    tags: Optional[List[str]] = None
    subscribed_after: Optional[datetime] = None
    subscribed_before: Optional[datetime] = None