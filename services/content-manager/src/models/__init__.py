"""
Database models for Content Manager service
"""

from .base import Base
from .content import (
    RawContent, 
    GeneratedContent, 
    ContentCategory, 
    ContentTag,
    ContentAsset,
    ContentAssetRelation
)
from .newsletter import NewsletterIssue, NewsletterTemplate
from .subscriber import Subscriber, SubscriberSegment, SubscriptionPreference
from .social import InstagramPost, SocialAccount
from .scraper import ScraperTarget, ScrapingJob
from .metrics import ContentMetric, NewsletterMetric, SystemMetric
from .admin import AdminUser, AdminSession
from .audit import AuditLog, SystemEvent

__all__ = [
    "Base",
    "RawContent",
    "GeneratedContent", 
    "ContentCategory",
    "ContentTag",
    "ContentAsset",
    "ContentAssetRelation",
    "NewsletterIssue",
    "NewsletterTemplate",
    "Subscriber",
    "SubscriberSegment", 
    "SubscriptionPreference",
    "InstagramPost",
    "SocialAccount",
    "ScraperTarget",
    "ScrapingJob",
    "ContentMetric",
    "NewsletterMetric",
    "SystemMetric",
    "AdminUser",
    "AdminSession",
    "AuditLog",
    "SystemEvent"
]