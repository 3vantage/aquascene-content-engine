"""
Content-related Pydantic schemas
"""
import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class ContentBase(BaseModel):
    """Base schema for content"""
    content_type: str = Field(..., description="Type of content")
    title: str = Field(..., description="Content title")
    content: str = Field(..., description="Main content body")
    

class GeneratedContentCreate(ContentBase):
    """Schema for creating generated content"""
    summary: Optional[str] = None
    excerpt: Optional[str] = None
    template_used: Optional[str] = None
    source_materials: Optional[List[Dict]] = Field(default_factory=list)
    tags: Optional[List[str]] = Field(default_factory=list)
    categories: Optional[List[str]] = Field(default_factory=list)
    target_audience: Optional[str] = None
    tone: Optional[str] = None
    scheduled_for: Optional[datetime] = None
    

class GeneratedContentUpdate(BaseModel):
    """Schema for updating generated content"""
    title: Optional[str] = None
    content: Optional[str] = None
    summary: Optional[str] = None
    excerpt: Optional[str] = None
    status: Optional[str] = Field(None, regex="^(draft|review|approved|published|archived)$")
    tags: Optional[List[str]] = None
    categories: Optional[List[str]] = None
    scheduled_for: Optional[datetime] = None
    

class GeneratedContentResponse(ContentBase):
    """Schema for generated content responses"""
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    summary: Optional[str] = None
    excerpt: Optional[str] = None
    template_used: Optional[str] = None
    quality_score: Optional[float] = None
    readability_score: Optional[int] = None
    seo_score: Optional[float] = None
    engagement_prediction: Optional[float] = None
    status: str
    tags: Optional[List[str]] = None
    categories: Optional[List[str]] = None
    target_audience: Optional[str] = None
    tone: Optional[str] = None
    word_count: Optional[int] = None
    estimated_reading_time: Optional[int] = None
    scheduled_for: Optional[datetime] = None
    published_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    created_by: Optional[uuid.UUID] = None
    approved_by: Optional[uuid.UUID] = None
    approved_at: Optional[datetime] = None


class RawContentCreate(BaseModel):
    """Schema for creating raw content"""
    source_url: str = Field(..., description="Source URL")
    source_domain: str = Field(..., description="Source domain")
    content_type: str = Field(..., description="Type of content")
    title: Optional[str] = None
    content: Optional[str] = None
    html_content: Optional[str] = None
    images: Optional[List[Dict]] = Field(default_factory=list)
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    language: str = Field(default="en", description="Content language")


class RawContentResponse(BaseModel):
    """Schema for raw content responses"""
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    source_url: str
    source_domain: str
    content_type: str
    title: Optional[str] = None
    content: Optional[str] = None
    html_content: Optional[str] = None
    images: Optional[Dict] = None
    metadata: Optional[Dict] = None
    scraped_at: datetime
    processed: bool
    processing_status: str
    processing_error: Optional[str] = None
    content_hash: Optional[str] = None
    language: str
    word_count: Optional[int] = None
    created_at: datetime
    updated_at: datetime


class ContentCategoryCreate(BaseModel):
    """Schema for creating content categories"""
    name: str = Field(..., max_length=100, description="Category name")
    slug: str = Field(..., max_length=100, description="URL-friendly slug")
    description: Optional[str] = None
    parent_id: Optional[int] = None
    sort_order: int = Field(default=0, description="Sort order for display")
    is_active: bool = Field(default=True, description="Whether category is active")


class ContentCategoryResponse(BaseModel):
    """Schema for content category responses"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    name: str
    slug: str
    description: Optional[str] = None
    parent_id: Optional[int] = None
    sort_order: int
    is_active: bool
    created_at: datetime
    updated_at: datetime


class ContentTagCreate(BaseModel):
    """Schema for creating content tags"""
    name: str = Field(..., max_length=100, description="Tag name")
    slug: str = Field(..., max_length=100, description="URL-friendly slug")
    description: Optional[str] = None


class ContentTagResponse(BaseModel):
    """Schema for content tag responses"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    name: str
    slug: str
    description: Optional[str] = None
    usage_count: int
    created_at: datetime
    updated_at: datetime


class ContentListResponse(BaseModel):
    """Schema for paginated content lists"""
    items: List[GeneratedContentResponse]
    total: int
    page: int
    size: int
    pages: int


class ContentFilter(BaseModel):
    """Schema for content filtering"""
    content_type: Optional[str] = None
    status: Optional[str] = None
    tags: Optional[List[str]] = None
    categories: Optional[List[str]] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None