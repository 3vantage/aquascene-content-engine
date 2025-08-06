"""
Data validation utilities for Content Manager
"""
import re
from typing import Dict, Any, List, Optional
from datetime import datetime
from email_validator import validate_email, EmailNotValidError

from .error_handler import ValidationException


def validate_content_data(content_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate content data before database operations
    
    Args:
        content_data: Dictionary containing content fields
        
    Returns:
        Validated and cleaned content data
        
    Raises:
        ValidationException: If validation fails
    """
    errors = []
    cleaned_data = content_data.copy()
    
    # Required fields
    required_fields = ['content_type', 'title', 'content']
    for field in required_fields:
        if not content_data.get(field):
            errors.append(f"{field} is required")
    
    # Title validation
    if 'title' in content_data:
        title = str(content_data['title']).strip()
        if len(title) < 5:
            errors.append("Title must be at least 5 characters long")
        elif len(title) > 500:
            errors.append("Title must be less than 500 characters")
        else:
            cleaned_data['title'] = title
    
    # Content validation
    if 'content' in content_data:
        content = str(content_data['content']).strip()
        if len(content) < 50:
            errors.append("Content must be at least 50 characters long")
        elif len(content) > 50000:
            errors.append("Content must be less than 50,000 characters")
        else:
            cleaned_data['content'] = content
            # Calculate word count
            cleaned_data['word_count'] = len(content.split())
            # Estimate reading time (average 200 words per minute)
            cleaned_data['estimated_reading_time'] = max(1, cleaned_data['word_count'] // 200)
    
    # Content type validation
    valid_content_types = [
        'article', 'blog_post', 'newsletter_article', 'social_post',
        'instagram_caption', 'product_review', 'how_to_guide', 'news'
    ]
    if content_data.get('content_type') and content_data['content_type'] not in valid_content_types:
        errors.append(f"Content type must be one of: {', '.join(valid_content_types)}")
    
    # Status validation
    valid_statuses = ['draft', 'review', 'approved', 'published', 'archived']
    if content_data.get('status') and content_data['status'] not in valid_statuses:
        errors.append(f"Status must be one of: {', '.join(valid_statuses)}")
    
    # Quality score validation
    if 'quality_score' in content_data:
        try:
            score = float(content_data['quality_score'])
            if not 0.0 <= score <= 1.0:
                errors.append("Quality score must be between 0.0 and 1.0")
            else:
                cleaned_data['quality_score'] = score
        except (ValueError, TypeError):
            errors.append("Quality score must be a valid number")
    
    # Readability score validation
    if 'readability_score' in content_data:
        try:
            score = int(content_data['readability_score'])
            if not 0 <= score <= 100:
                errors.append("Readability score must be between 0 and 100")
            else:
                cleaned_data['readability_score'] = score
        except (ValueError, TypeError):
            errors.append("Readability score must be a valid integer")
    
    # SEO score validation
    if 'seo_score' in content_data:
        try:
            score = float(content_data['seo_score'])
            if not 0.0 <= score <= 1.0:
                errors.append("SEO score must be between 0.0 and 1.0")
            else:
                cleaned_data['seo_score'] = score
        except (ValueError, TypeError):
            errors.append("SEO score must be a valid number")
    
    # Tags validation
    if 'tags' in content_data:
        if isinstance(content_data['tags'], list):
            cleaned_tags = []
            for tag in content_data['tags']:
                tag_str = str(tag).strip().lower()
                if tag_str and len(tag_str) <= 50:
                    cleaned_tags.append(tag_str)
            cleaned_data['tags'] = cleaned_tags[:10]  # Limit to 10 tags
        else:
            errors.append("Tags must be a list")
    
    # Categories validation
    if 'categories' in content_data:
        if isinstance(content_data['categories'], list):
            cleaned_categories = []
            for category in content_data['categories']:
                cat_str = str(category).strip()
                if cat_str and len(cat_str) <= 100:
                    cleaned_categories.append(cat_str)
            cleaned_data['categories'] = cleaned_categories[:5]  # Limit to 5 categories
        else:
            errors.append("Categories must be a list")
    
    # Target audience validation
    valid_audiences = ['beginners', 'intermediate', 'advanced', 'experts', 'general', 'enthusiasts']
    if content_data.get('target_audience') and content_data['target_audience'] not in valid_audiences:
        errors.append(f"Target audience must be one of: {', '.join(valid_audiences)}")
    
    # Tone validation
    valid_tones = ['educational', 'conversational', 'professional', 'casual', 'inspiring', 'technical']
    if content_data.get('tone') and content_data['tone'] not in valid_tones:
        errors.append(f"Tone must be one of: {', '.join(valid_tones)}")
    
    if errors:
        raise ValidationException(
            "Content validation failed",
            details={'validation_errors': errors}
        )
    
    return cleaned_data


def validate_subscriber_data(subscriber_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate subscriber data before database operations
    
    Args:
        subscriber_data: Dictionary containing subscriber fields
        
    Returns:
        Validated and cleaned subscriber data
        
    Raises:
        ValidationException: If validation fails
    """
    errors = []
    cleaned_data = subscriber_data.copy()
    
    # Email validation (required)
    if not subscriber_data.get('email'):
        errors.append("Email is required")
    else:
        try:
            validated_email = validate_email(subscriber_data['email'])
            cleaned_data['email'] = validated_email.email
        except EmailNotValidError as e:
            errors.append(f"Invalid email format: {str(e)}")
    
    # Name validation
    if 'first_name' in subscriber_data:
        first_name = str(subscriber_data['first_name']).strip()
        if len(first_name) > 100:
            errors.append("First name must be less than 100 characters")
        elif first_name:
            cleaned_data['first_name'] = first_name
    
    if 'last_name' in subscriber_data:
        last_name = str(subscriber_data['last_name']).strip()
        if len(last_name) > 100:
            errors.append("Last name must be less than 100 characters")
        elif last_name:
            cleaned_data['last_name'] = last_name
    
    # Generate full name if first/last names provided
    if cleaned_data.get('first_name') or cleaned_data.get('last_name'):
        parts = []
        if cleaned_data.get('first_name'):
            parts.append(cleaned_data['first_name'])
        if cleaned_data.get('last_name'):
            parts.append(cleaned_data['last_name'])
        cleaned_data['full_name'] = ' '.join(parts)
    
    # Phone validation
    if 'phone' in subscriber_data and subscriber_data['phone']:
        phone = str(subscriber_data['phone']).strip()
        # Basic phone validation (can be enhanced)
        if len(phone) > 50:
            errors.append("Phone number must be less than 50 characters")
        else:
            cleaned_data['phone'] = phone
    
    # Country validation
    if 'country' in subscriber_data and subscriber_data['country']:
        country = str(subscriber_data['country']).strip()
        if len(country) > 100:
            errors.append("Country must be less than 100 characters")
        else:
            cleaned_data['country'] = country
    
    # Language validation
    valid_languages = ['en', 'es', 'fr', 'de', 'it', 'pt', 'ru', 'ja', 'ko', 'zh']
    if subscriber_data.get('language'):
        language = str(subscriber_data['language']).lower()
        if language not in valid_languages:
            errors.append(f"Language must be one of: {', '.join(valid_languages)}")
        else:
            cleaned_data['language'] = language
    
    # Status validation
    valid_statuses = ['active', 'inactive', 'unsubscribed', 'bounced']
    if subscriber_data.get('status') and subscriber_data['status'] not in valid_statuses:
        errors.append(f"Status must be one of: {', '.join(valid_statuses)}")
    
    # Source validation
    valid_sources = ['website_signup', 'instagram', 'referral', 'social_media', 'airtable', 'import', 'api']
    if subscriber_data.get('source') and subscriber_data['source'] not in valid_sources:
        errors.append(f"Source must be one of: {', '.join(valid_sources)}")
    
    # Tags validation
    if 'tags' in subscriber_data:
        if isinstance(subscriber_data['tags'], list):
            cleaned_tags = []
            for tag in subscriber_data['tags']:
                tag_str = str(tag).strip().lower()
                if tag_str and len(tag_str) <= 50:
                    cleaned_tags.append(tag_str)
            cleaned_data['tags'] = cleaned_tags[:20]  # Limit to 20 tags
        else:
            errors.append("Tags must be a list")
    
    # Custom fields validation
    if 'custom_fields' in subscriber_data:
        if not isinstance(subscriber_data['custom_fields'], dict):
            errors.append("Custom fields must be a dictionary")
        else:
            # Limit custom fields size
            custom_fields = subscriber_data['custom_fields']
            if len(str(custom_fields)) > 5000:  # 5KB limit
                errors.append("Custom fields data too large (max 5KB)")
            else:
                cleaned_data['custom_fields'] = custom_fields
    
    if errors:
        raise ValidationException(
            "Subscriber validation failed",
            details={'validation_errors': errors}
        )
    
    return cleaned_data


def validate_newsletter_data(newsletter_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate newsletter data before database operations
    
    Args:
        newsletter_data: Dictionary containing newsletter fields
        
    Returns:
        Validated and cleaned newsletter data
        
    Raises:
        ValidationException: If validation fails
    """
    errors = []
    cleaned_data = newsletter_data.copy()
    
    # Required fields
    required_fields = ['template_type', 'subject_line', 'content_ids']
    for field in required_fields:
        if not newsletter_data.get(field):
            errors.append(f"{field} is required")
    
    # Subject line validation
    if 'subject_line' in newsletter_data:
        subject = str(newsletter_data['subject_line']).strip()
        if len(subject) < 5:
            errors.append("Subject line must be at least 5 characters long")
        elif len(subject) > 200:
            errors.append("Subject line must be less than 200 characters")
        else:
            cleaned_data['subject_line'] = subject
    
    # Preview text validation
    if 'preview_text' in newsletter_data and newsletter_data['preview_text']:
        preview = str(newsletter_data['preview_text']).strip()
        if len(preview) > 300:
            errors.append("Preview text must be less than 300 characters")
        else:
            cleaned_data['preview_text'] = preview
    
    # Template type validation
    valid_templates = ['digest', 'announcement', 'educational', 'showcase', 'promotional']
    if newsletter_data.get('template_type') and newsletter_data['template_type'] not in valid_templates:
        errors.append(f"Template type must be one of: {', '.join(valid_templates)}")
    
    # Content IDs validation
    if 'content_ids' in newsletter_data:
        if not isinstance(newsletter_data['content_ids'], list):
            errors.append("Content IDs must be a list")
        elif len(newsletter_data['content_ids']) == 0:
            errors.append("At least one content ID is required")
        elif len(newsletter_data['content_ids']) > 15:
            errors.append("Maximum 15 content items allowed per newsletter")
    
    # Status validation
    valid_statuses = ['draft', 'scheduled', 'sent', 'cancelled']
    if newsletter_data.get('status') and newsletter_data['status'] not in valid_statuses:
        errors.append(f"Status must be one of: {', '.join(valid_statuses)}")
    
    if errors:
        raise ValidationException(
            "Newsletter validation failed",
            details={'validation_errors': errors}
        )
    
    return cleaned_data


def validate_uuid(uuid_string: str) -> bool:
    """Validate UUID format"""
    uuid_pattern = re.compile(
        r'^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$'
    )
    return bool(uuid_pattern.match(uuid_string))


def sanitize_input(input_data: Any, max_length: int = 1000) -> str:
    """Sanitize input data to prevent injection attacks"""
    if input_data is None:
        return ""
    
    sanitized = str(input_data).strip()
    
    # Remove potentially dangerous characters
    dangerous_chars = ['<', '>', '"', "'", '&', '\x00']
    for char in dangerous_chars:
        sanitized = sanitized.replace(char, '')
    
    # Truncate to max length
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length]
    
    return sanitized