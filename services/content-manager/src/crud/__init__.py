"""
CRUD operations for Content Manager
"""

from .content import ContentCRUD
from .newsletter import NewsletterCRUD
from .subscriber import SubscriberCRUD

__all__ = [
    "ContentCRUD",
    "NewsletterCRUD", 
    "SubscriberCRUD"
]