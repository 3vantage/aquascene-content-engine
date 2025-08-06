"""
Template Manager

Manages and applies templates for different content types,
integrating with existing newsletter and Instagram templates.
"""

import os
import yaml
import json
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from enum import Enum
import asyncio
import aiofiles
from pathlib import Path
import structlog

from ..llm_clients.base_client import ContentType
from .newsletter_templates import NewsletterTemplates
from .instagram_templates import InstagramTemplates
from .content_formatter import ContentFormatter

logger = structlog.get_logger()


class TemplateFormat(Enum):
    """Supported template formats"""
    HTML = "html"
    TEXT = "text"
    MARKDOWN = "markdown"
    JSON = "json"
    YAML = "yaml"


@dataclass
class Template:
    """Template definition"""
    name: str
    content_type: ContentType
    format: TemplateFormat
    template_content: str
    variables: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    instructions: Optional[str] = None
    example_content: Optional[str] = None


@dataclass
class TemplateContext:
    """Context for template rendering"""
    variables: Dict[str, Any] = field(default_factory=dict)
    content_type: Optional[ContentType] = None
    target_audience: Optional[str] = None
    brand_voice: Optional[str] = None
    seo_keywords: List[str] = field(default_factory=list)
    additional_instructions: Optional[str] = None


class TemplateManager:
    """Manages content templates across different formats and types"""
    
    def __init__(self, template_dirs: Optional[List[str]] = None):
        self.template_dirs = template_dirs or []
        
        # Add default template directories
        current_dir = Path(__file__).parent
        self.template_dirs.extend([
            str(current_dir.parent.parent.parent / "distributor" / "templates"),
            str(current_dir / "builtin_templates")
        ])
        
        # Template registry
        self.templates: Dict[str, Template] = {}
        
        # Specialized template handlers
        self.newsletter_templates = NewsletterTemplates()
        self.instagram_templates = InstagramTemplates()
        self.content_formatter = ContentFormatter()
        
        # Template cache
        self._template_cache: Dict[str, str] = {}
        
        # Initialize templates
        asyncio.create_task(self._load_templates())
    
    async def _load_templates(self) -> None:
        """Load all templates from configured directories"""
        logger.info("Loading templates", directories=self.template_dirs)
        
        for template_dir in self.template_dirs:
            if os.path.exists(template_dir):
                await self._load_templates_from_directory(template_dir)
        
        logger.info(f"Loaded {len(self.templates)} templates")
    
    async def _load_templates_from_directory(self, directory: str) -> None:
        """Load templates from a specific directory"""
        try:
            for root, dirs, files in os.walk(directory):
                for file in files:
                    if file.endswith(('.html', '.txt', '.md', '.json', '.yml', '.yaml')):
                        file_path = os.path.join(root, file)
                        await self._load_template_file(file_path)
        except Exception as e:
            logger.error(f"Error loading templates from {directory}", error=str(e))
    
    async def _load_template_file(self, file_path: str) -> None:
        """Load a single template file"""
        try:
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                content = await f.read()
            
            # Determine template format
            file_ext = Path(file_path).suffix.lower()
            format_map = {
                '.html': TemplateFormat.HTML,
                '.txt': TemplateFormat.TEXT,
                '.md': TemplateFormat.MARKDOWN,
                '.json': TemplateFormat.JSON,
                '.yml': TemplateFormat.YAML,
                '.yaml': TemplateFormat.YAML
            }
            
            template_format = format_map.get(file_ext, TemplateFormat.TEXT)
            
            # Parse template metadata if it exists
            metadata = {}
            instructions = None
            variables = []
            
            if template_format in [TemplateFormat.JSON, TemplateFormat.YAML]:
                # Template definition file
                if template_format == TemplateFormat.JSON:
                    template_data = json.loads(content)
                else:
                    template_data = yaml.safe_load(content)
                
                metadata = template_data.get('metadata', {})
                instructions = template_data.get('instructions')
                variables = template_data.get('variables', [])
                content = template_data.get('template', content)
            
            # Extract template name and content type from file path
            file_name = Path(file_path).stem
            
            # Determine content type from file name or directory
            content_type = self._determine_content_type(file_path, file_name)
            
            if content_type:
                template = Template(
                    name=file_name,
                    content_type=content_type,
                    format=template_format,
                    template_content=content,
                    variables=variables,
                    metadata=metadata,
                    instructions=instructions
                )
                
                self.templates[file_name] = template
                logger.debug(f"Loaded template: {file_name}")
            
        except Exception as e:
            logger.error(f"Error loading template file {file_path}", error=str(e))
    
    def _determine_content_type(self, file_path: str, file_name: str) -> Optional[ContentType]:
        """Determine content type from file path and name"""
        path_lower = file_path.lower()
        name_lower = file_name.lower()
        
        # Check for content type indicators
        if 'newsletter' in path_lower or 'newsletter' in name_lower:
            return ContentType.NEWSLETTER_ARTICLE
        elif 'instagram' in path_lower or 'instagram' in name_lower:
            return ContentType.INSTAGRAM_CAPTION
        elif 'how-to' in path_lower or 'howto' in name_lower or 'guide' in name_lower:
            return ContentType.HOW_TO_GUIDE
        elif 'review' in path_lower or 'product' in name_lower:
            return ContentType.PRODUCT_REVIEW
        elif 'blog' in path_lower or 'seo' in name_lower:
            return ContentType.SEO_BLOG_POST
        elif 'community' in path_lower:
            return ContentType.COMMUNITY_POST
        elif 'digest' in path_lower or 'weekly' in name_lower:
            return ContentType.WEEKLY_DIGEST
        elif 'interview' in path_lower:
            return ContentType.EXPERT_INTERVIEW
        
        return None
    
    async def get_template(self, template_name: str) -> Optional[Template]:
        """Get a template by name"""
        return self.templates.get(template_name)
    
    async def get_templates_by_content_type(self, content_type: ContentType) -> List[Template]:
        """Get all templates for a specific content type"""
        return [
            template for template in self.templates.values()
            if template.content_type == content_type
        ]
    
    async def apply_template(
        self,
        template_name: str,
        content: str,
        content_type: ContentType,
        context: Dict[str, Any] = None
    ) -> str:
        """Apply a template to content"""
        template = await self.get_template(template_name)
        if not template:
            logger.warning(f"Template not found: {template_name}")
            return content
        
        # Use specialized handlers for specific content types
        if content_type == ContentType.NEWSLETTER_ARTICLE:
            return await self.newsletter_templates.apply_template(
                template_name, content, context or {}
            )
        elif content_type == ContentType.INSTAGRAM_CAPTION:
            return await self.instagram_templates.apply_template(
                template_name, content, context or {}
            )
        else:
            return await self._apply_generic_template(template, content, context or {})
    
    async def _apply_generic_template(
        self,
        template: Template,
        content: str,
        context: Dict[str, Any]
    ) -> str:
        """Apply a generic template"""
        try:
            # Prepare template variables
            template_vars = {
                'content': content,
                'title': context.get('title', ''),
                'author': context.get('author', 'AquaScene Team'),
                'date': context.get('date', ''),
                'brand_voice': context.get('brand_voice', 'professional and educational'),
                'target_audience': context.get('target_audience', 'aquascaping enthusiasts'),
                **context
            }
            
            # Apply template based on format
            if template.format == TemplateFormat.HTML:
                return await self.content_formatter.format_html(
                    template.template_content, template_vars
                )
            elif template.format == TemplateFormat.MARKDOWN:
                return await self.content_formatter.format_markdown(
                    template.template_content, template_vars
                )
            else:
                return await self.content_formatter.format_text(
                    template.template_content, template_vars
                )
        
        except Exception as e:
            logger.error(f"Error applying template {template.name}", error=str(e))
            return content
    
    async def get_template_context(
        self,
        template_name: str,
        content_type: ContentType
    ) -> Dict[str, Any]:
        """Get context and instructions for a template"""
        template = await self.get_template(template_name)
        if not template:
            return {}
        
        context = {
            'template_name': template_name,
            'template_format': template.format.value,
            'template_variables': template.variables,
            'template_metadata': template.metadata
        }
        
        if template.instructions:
            context['template_instructions'] = template.instructions
        
        return context
    
    async def validate_template_variables(
        self,
        template_name: str,
        variables: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate that all required template variables are provided"""
        template = await self.get_template(template_name)
        if not template:
            return {'valid': False, 'error': 'Template not found'}
        
        missing_variables = []
        for required_var in template.variables:
            if required_var not in variables:
                missing_variables.append(required_var)
        
        return {
            'valid': len(missing_variables) == 0,
            'missing_variables': missing_variables,
            'provided_variables': list(variables.keys()),
            'required_variables': template.variables
        }
    
    async def create_template_from_content(
        self,
        name: str,
        content_type: ContentType,
        content: str,
        format: TemplateFormat = TemplateFormat.TEXT,
        metadata: Dict[str, Any] = None
    ) -> Template:
        """Create a new template from content"""
        template = Template(
            name=name,
            content_type=content_type,
            format=format,
            template_content=content,
            metadata=metadata or {}
        )
        
        self.templates[name] = template
        logger.info(f"Created new template: {name}")
        
        return template
    
    async def save_template(self, template: Template, directory: str) -> bool:
        """Save a template to disk"""
        try:
            file_extension = {
                TemplateFormat.HTML: '.html',
                TemplateFormat.TEXT: '.txt',
                TemplateFormat.MARKDOWN: '.md',
                TemplateFormat.JSON: '.json',
                TemplateFormat.YAML: '.yml'
            }.get(template.format, '.txt')
            
            file_path = os.path.join(directory, f"{template.name}{file_extension}")
            
            # Prepare content to save
            if template.format in [TemplateFormat.JSON, TemplateFormat.YAML]:
                # Save as structured template definition
                template_data = {
                    'metadata': template.metadata,
                    'content_type': template.content_type.value,
                    'variables': template.variables,
                    'instructions': template.instructions,
                    'template': template.template_content
                }
                
                if template.format == TemplateFormat.JSON:
                    content_to_save = json.dumps(template_data, indent=2)
                else:
                    content_to_save = yaml.dump(template_data, default_flow_style=False)
            else:
                content_to_save = template.template_content
            
            async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
                await f.write(content_to_save)
            
            logger.info(f"Saved template {template.name} to {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving template {template.name}", error=str(e))
            return False
    
    def get_available_templates(self) -> Dict[str, Dict[str, Any]]:
        """Get list of all available templates"""
        return {
            name: {
                'content_type': template.content_type.value,
                'format': template.format.value,
                'variables': template.variables,
                'has_instructions': bool(template.instructions),
                'metadata': template.metadata
            }
            for name, template in self.templates.items()
        }
    
    async def generate_template_preview(
        self,
        template_name: str,
        sample_content: str = "This is sample content for preview.",
        context: Dict[str, Any] = None
    ) -> Optional[str]:
        """Generate a preview of how content would look with the template"""
        template = await self.get_template(template_name)
        if not template:
            return None
        
        # Use sample context if none provided
        if context is None:
            context = {
                'title': 'Sample Aquascaping Article',
                'author': 'AquaScene Team',
                'date': '2024-01-01',
                'topic': 'aquascaping'
            }
        
        try:
            return await self._apply_generic_template(template, sample_content, context)
        except Exception as e:
            logger.error(f"Error generating preview for {template_name}", error=str(e))
            return None
    
    async def refresh_templates(self) -> None:
        """Reload all templates from disk"""
        self.templates.clear()
        self._template_cache.clear()
        await self._load_templates()
        logger.info("Templates refreshed")