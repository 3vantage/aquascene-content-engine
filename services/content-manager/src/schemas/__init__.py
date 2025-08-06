"""
Pydantic schemas for request/response validation
"""

from .content import (
    GeneratedContentCreate,
    GeneratedContentUpdate,
    GeneratedContentResponse,
    RawContentCreate,
    RawContentResponse,
    ContentCategoryCreate,
    ContentCategoryResponse
)
from .newsletter import (
    NewsletterIssueCreate,
    NewsletterIssueUpdate,
    NewsletterIssueResponse,
    NewsletterTemplateCreate,
    NewsletterTemplateResponse
)
from .subscriber import (
    SubscriberCreate,
    SubscriberUpdate,
    SubscriberResponse,
    SubscriptionPreferenceCreate,
    SubscriptionPreferenceResponse
)

__all__ = [
    "GeneratedContentCreate",
    "GeneratedContentUpdate", 
    "GeneratedContentResponse",
    "RawContentCreate",
    "RawContentResponse",
    "ContentCategoryCreate",
    "ContentCategoryResponse",
    "NewsletterIssueCreate",
    "NewsletterIssueUpdate",
    "NewsletterIssueResponse",
    "NewsletterTemplateCreate",
    "NewsletterTemplateResponse",
    "SubscriberCreate",
    "SubscriberUpdate",
    "SubscriberResponse",
    "SubscriptionPreferenceCreate",
    "SubscriptionPreferenceResponse"
]