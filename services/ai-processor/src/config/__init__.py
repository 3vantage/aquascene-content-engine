"""
Configuration Management Package

Handles application configuration, environment variables, and settings
for the AI content processor service.
"""

from .settings import Settings, get_settings

__all__ = ["Settings", "get_settings"]