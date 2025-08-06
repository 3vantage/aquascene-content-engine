"""
Template Management Package

Provides template integration for different content types and formats:
- Newsletter template integration
- Instagram content templates
- How-to guide templates
- Product review templates
- SEO blog post templates
"""

from .template_manager import TemplateManager
from .newsletter_templates import NewsletterTemplates
from .instagram_templates import InstagramTemplates
from .content_formatter import ContentFormatter

__all__ = [
    "TemplateManager", 
    "NewsletterTemplates",
    "InstagramTemplates",
    "ContentFormatter"
]