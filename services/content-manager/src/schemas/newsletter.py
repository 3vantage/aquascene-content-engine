"""
Newsletter-related Pydantic schemas
"""
import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class NewsletterIssueCreate(BaseModel):
    """Schema for creating newsletter issues"""
    issue_number: Optional[int] = None
    template_type: str = Field(..., description="Template type for newsletter")
    subject_line: str = Field(..., description="Email subject line")
    preview_text: Optional[str] = Field(None, description="Email preview text")
    content_ids: List[uuid.UUID] = Field(..., description="List of content IDs to include")
    personalization_data: Optional[Dict[str, Any]] = Field(default_factory=dict)
    design_template: Optional[str] = None
    scheduled_for: Optional[datetime] = None


class NewsletterIssueUpdate(BaseModel):
    """Schema for updating newsletter issues"""
    subject_line: Optional[str] = None
    preview_text: Optional[str] = None
    content_ids: Optional[List[uuid.UUID]] = None
    personalization_data: Optional[Dict[str, Any]] = None
    design_template: Optional[str] = None
    scheduled_for: Optional[datetime] = None
    status: Optional[str] = Field(None, regex="^(draft|scheduled|sent|cancelled)$")


class NewsletterIssueResponse(BaseModel):
    """Schema for newsletter issue responses"""
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    issue_number: Optional[int] = None
    template_type: str
    subject_line: str
    preview_text: Optional[str] = None
    content_ids: List[uuid.UUID]
    personalization_data: Optional[Dict] = None
    design_template: Optional[str] = None
    scheduled_for: Optional[datetime] = None
    sent_at: Optional[datetime] = None
    status: str
    recipient_count: int
    metrics: Optional[Dict] = None
    created_at: datetime
    updated_at: datetime
    created_by: Optional[uuid.UUID] = None


class NewsletterTemplateCreate(BaseModel):
    """Schema for creating newsletter templates"""
    name: str = Field(..., max_length=100, description="Template name")
    description: Optional[str] = None
    template_type: str = Field(..., description="Type of newsletter template")
    html_template: str = Field(..., description="HTML template content")
    text_template: Optional[str] = Field(None, description="Plain text template")
    default_subject: Optional[str] = Field(None, max_length=255)
    variables: Optional[List[Dict]] = Field(default_factory=list, description="Template variables")
    is_active: bool = Field(default=True)


class NewsletterTemplateResponse(BaseModel):
    """Schema for newsletter template responses"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    name: str
    description: Optional[str] = None
    template_type: str
    html_template: str
    text_template: Optional[str] = None
    default_subject: Optional[str] = None
    variables: Optional[List] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class NewsletterMetricCreate(BaseModel):
    """Schema for creating newsletter metrics"""
    issue_id: uuid.UUID
    metric_type: str
    sent_count: int = Field(default=0)
    delivered_count: int = Field(default=0)
    open_count: int = Field(default=0)
    click_count: int = Field(default=0)
    unsubscribe_count: int = Field(default=0)
    bounce_count: int = Field(default=0)
    complaint_count: int = Field(default=0)


class NewsletterMetricResponse(BaseModel):
    """Schema for newsletter metric responses"""
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    issue_id: uuid.UUID
    metric_type: str
    sent_count: int
    delivered_count: int
    open_count: int
    click_count: int
    unsubscribe_count: int
    bounce_count: int
    complaint_count: int
    unique_opens: int
    unique_clicks: int
    open_rate: Optional[float] = None
    click_rate: Optional[float] = None
    unsubscribe_rate: Optional[float] = None
    bounce_rate: Optional[float] = None
    recorded_at: datetime