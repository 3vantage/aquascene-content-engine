"""
API routes for Content Manager service
"""

from .content_routes import router as content_router
from .newsletter_routes import router as newsletter_router
from .subscriber_routes import router as subscriber_router
from .workflow_routes import router as workflow_router

__all__ = [
    "content_router",
    "newsletter_router",
    "subscriber_router", 
    "workflow_router"
]