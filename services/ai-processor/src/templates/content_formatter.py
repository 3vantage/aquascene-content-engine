"""
Content Formatter

Handles formatting of content for different output formats and templates.
"""

import re
from typing import Dict, Any, Optional
from jinja2 import Template, Environment, DictLoader
import structlog

logger = structlog.get_logger()


class ContentFormatter:
    """Handles content formatting across different formats"""
    
    def __init__(self):
        self.jinja_env = Environment(
            loader=DictLoader({}),
            autoescape=False
        )
        
        # Add custom filters
        self.jinja_env.filters['truncate_words'] = self._truncate_words
        self.jinja_env.filters['add_line_breaks'] = self._add_line_breaks
        self.jinja_env.filters['strip_html'] = self._strip_html
        self.jinja_env.filters['title_case'] = self._title_case
    
    async def format_html(self, template_content: str, variables: Dict[str, Any]) -> str:
        """Format content as HTML using Jinja2 template"""
        try:
            template = Template(template_content, environment=self.jinja_env)
            return template.render(**variables)
        except Exception as e:
            logger.error("Error formatting HTML template", error=str(e))
            # Fallback to simple variable substitution
            return self._simple_substitution(template_content, variables)
    
    async def format_markdown(self, template_content: str, variables: Dict[str, Any]) -> str:
        """Format content as Markdown using Jinja2 template"""
        try:
            template = Template(template_content, environment=self.jinja_env)
            formatted = template.render(**variables)
            
            # Clean up markdown formatting
            formatted = self._clean_markdown(formatted)
            return formatted
        except Exception as e:
            logger.error("Error formatting Markdown template", error=str(e))
            return self._simple_substitution(template_content, variables)
    
    async def format_text(self, template_content: str, variables: Dict[str, Any]) -> str:
        """Format content as plain text using Jinja2 template"""
        try:
            template = Template(template_content, environment=self.jinja_env)
            formatted = template.render(**variables)
            
            # Clean up text formatting
            formatted = self._clean_text(formatted)
            return formatted
        except Exception as e:
            logger.error("Error formatting text template", error=str(e))
            return self._simple_substitution(template_content, variables)
    
    def _simple_substitution(self, template_content: str, variables: Dict[str, Any]) -> str:
        """Simple variable substitution fallback"""
        result = template_content
        for key, value in variables.items():
            placeholder = f"{{{{{key}}}}}"
            result = result.replace(placeholder, str(value))
        return result
    
    def _clean_markdown(self, content: str) -> str:
        """Clean up markdown formatting"""
        # Remove excessive line breaks
        content = re.sub(r'\n\s*\n\s*\n', '\n\n', content)
        
        # Ensure proper heading spacing
        content = re.sub(r'\n(#{1,6})', r'\n\n\1', content)
        content = re.sub(r'^(#{1,6})', r'\1', content)
        
        # Clean up list formatting
        content = re.sub(r'\n-\s+', '\n- ', content)
        content = re.sub(r'\n\*\s+', '\n* ', content)
        
        return content.strip()
    
    def _clean_text(self, content: str) -> str:
        """Clean up text formatting"""
        # Remove excessive whitespace
        content = re.sub(r'\s+', ' ', content)
        
        # Remove excessive line breaks
        content = re.sub(r'\n\s*\n\s*\n', '\n\n', content)
        
        # Trim whitespace from lines
        lines = [line.strip() for line in content.split('\n')]
        content = '\n'.join(lines)
        
        return content.strip()
    
    def _truncate_words(self, text: str, max_words: int = 50, suffix: str = "...") -> str:
        """Jinja2 filter: Truncate text to maximum number of words"""
        if not text:
            return ""
        
        words = str(text).split()
        if len(words) <= max_words:
            return text
        
        truncated = " ".join(words[:max_words])
        return f"{truncated}{suffix}"
    
    def _add_line_breaks(self, text: str, every: int = 80) -> str:
        """Jinja2 filter: Add line breaks every N characters"""
        if not text or len(text) <= every:
            return str(text)
        
        result = []
        current_line = ""
        
        for word in str(text).split():
            if len(current_line) + len(word) + 1 > every:
                if current_line:
                    result.append(current_line)
                    current_line = word
                else:
                    result.append(word)
            else:
                if current_line:
                    current_line += " " + word
                else:
                    current_line = word
        
        if current_line:
            result.append(current_line)
        
        return "\n".join(result)
    
    def _strip_html(self, text: str) -> str:
        """Jinja2 filter: Strip HTML tags from text"""
        if not text:
            return ""
        
        # Remove HTML tags
        clean = re.sub(r'<[^>]+>', '', str(text))
        
        # Convert common HTML entities
        replacements = {
            '&amp;': '&',
            '&lt;': '<',
            '&gt;': '>',
            '&quot;': '"',
            '&#39;': "'",
            '&nbsp;': ' '
        }
        
        for entity, replacement in replacements.items():
            clean = clean.replace(entity, replacement)
        
        return clean
    
    def _title_case(self, text: str) -> str:
        """Jinja2 filter: Convert text to title case"""
        if not text:
            return ""
        
        # Words that should not be capitalized in title case
        articles = {'a', 'an', 'the', 'and', 'but', 'or', 'for', 'nor', 'on', 'at', 
                   'to', 'from', 'by', 'of', 'in', 'into', 'with', 'without'}
        
        words = str(text).lower().split()
        result = []
        
        for i, word in enumerate(words):
            if i == 0 or word not in articles:
                result.append(word.capitalize())
            else:
                result.append(word)
        
        return " ".join(result)
    
    def format_for_platform(self, content: str, platform: str, **kwargs) -> str:
        """Format content for specific social media platforms"""
        if platform.lower() == "instagram":
            return self._format_for_instagram(content, **kwargs)
        elif platform.lower() == "twitter":
            return self._format_for_twitter(content, **kwargs)
        elif platform.lower() == "linkedin":
            return self._format_for_linkedin(content, **kwargs)
        elif platform.lower() == "facebook":
            return self._format_for_facebook(content, **kwargs)
        else:
            return content
    
    def _format_for_instagram(self, content: str, **kwargs) -> str:
        """Format content specifically for Instagram"""
        max_length = kwargs.get('max_length', 2200)
        
        # Add line breaks for readability
        paragraphs = content.split('\n\n')
        formatted_paragraphs = []
        
        for para in paragraphs:
            if len(para) > 150:  # Break long paragraphs
                sentences = para.split('. ')
                current_para = ""
                for sentence in sentences:
                    if len(current_para) + len(sentence) + 2 > 150:
                        if current_para:
                            formatted_paragraphs.append(current_para.strip())
                            current_para = sentence
                        else:
                            formatted_paragraphs.append(sentence)
                    else:
                        if current_para:
                            current_para += ". " + sentence
                        else:
                            current_para = sentence
                if current_para:
                    formatted_paragraphs.append(current_para.strip())
            else:
                formatted_paragraphs.append(para)
        
        formatted_content = '\n\n'.join(formatted_paragraphs)
        
        # Truncate if too long
        if len(formatted_content) > max_length:
            formatted_content = formatted_content[:max_length-3] + "..."
        
        return formatted_content
    
    def _format_for_twitter(self, content: str, **kwargs) -> str:
        """Format content specifically for Twitter"""
        max_length = kwargs.get('max_length', 280)
        
        if len(content) <= max_length:
            return content
        
        # Create a thread-friendly format
        return content[:max_length-3] + "..."
    
    def _format_for_linkedin(self, content: str, **kwargs) -> str:
        """Format content specifically for LinkedIn"""
        max_length = kwargs.get('max_length', 3000)
        
        # Add professional formatting
        if len(content) > max_length:
            content = content[:max_length-3] + "..."
        
        return content
    
    def _format_for_facebook(self, content: str, **kwargs) -> str:
        """Format content specifically for Facebook"""
        max_length = kwargs.get('max_length', 63206)  # Facebook's limit
        
        if len(content) > max_length:
            content = content[:max_length-3] + "..."
        
        return content
    
    def extract_metadata(self, content: str) -> Dict[str, Any]:
        """Extract metadata from content"""
        metadata = {
            'word_count': len(content.split()),
            'character_count': len(content),
            'paragraph_count': len([p for p in content.split('\n\n') if p.strip()]),
            'estimated_reading_time': max(1, len(content.split()) // 200),  # ~200 WPM
            'has_hashtags': '#' in content,
            'has_mentions': '@' in content,
            'has_urls': bool(re.search(r'https?://', content))
        }
        
        # Extract hashtags
        hashtags = re.findall(r'#\w+', content)
        metadata['hashtags'] = hashtags
        metadata['hashtag_count'] = len(hashtags)
        
        # Extract mentions
        mentions = re.findall(r'@\w+', content)
        metadata['mentions'] = mentions
        metadata['mention_count'] = len(mentions)
        
        # Extract URLs
        urls = re.findall(r'https?://[^\s]+', content)
        metadata['urls'] = urls
        metadata['url_count'] = len(urls)
        
        return metadata