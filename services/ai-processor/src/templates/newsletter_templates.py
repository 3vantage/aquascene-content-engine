"""
Newsletter Templates

Manages newsletter-specific template handling and formatting.
"""

from typing import Dict, Any, Optional
import structlog

logger = structlog.get_logger()


class NewsletterTemplates:
    """Handles newsletter-specific template processing"""
    
    def __init__(self):
        self.templates = self._load_builtin_templates()
    
    def _load_builtin_templates(self) -> Dict[str, Dict[str, Any]]:
        """Load built-in newsletter templates"""
        return {
            "weekly-digest": {
                "structure": [
                    "header",
                    "featured_article",
                    "quick_tips",
                    "community_highlight",
                    "product_spotlight",
                    "footer"
                ],
                "format": "html",
                "metadata": {
                    "type": "newsletter",
                    "frequency": "weekly"
                }
            },
            "how-to-guide": {
                "structure": [
                    "header",
                    "introduction",
                    "materials_needed",
                    "step_by_step",
                    "tips_and_tricks",
                    "conclusion",
                    "footer"
                ],
                "format": "html",
                "metadata": {
                    "type": "educational",
                    "difficulty": "beginner"
                }
            },
            "product-announcement": {
                "structure": [
                    "header",
                    "product_introduction",
                    "key_features",
                    "benefits",
                    "availability",
                    "call_to_action",
                    "footer"
                ],
                "format": "html",
                "metadata": {
                    "type": "commercial",
                    "purpose": "product_launch"
                }
            }
        }
    
    async def apply_template(
        self, 
        template_name: str, 
        content: str, 
        context: Dict[str, Any]
    ) -> str:
        """Apply newsletter template to content"""
        template = self.templates.get(template_name)
        if not template:
            logger.warning(f"Newsletter template not found: {template_name}")
            return content
        
        try:
            # Format content based on template structure
            if template["format"] == "html":
                return await self._format_html_newsletter(content, template, context)
            else:
                return await self._format_text_newsletter(content, template, context)
                
        except Exception as e:
            logger.error(f"Error applying newsletter template {template_name}", error=str(e))
            return content
    
    async def _format_html_newsletter(
        self, 
        content: str, 
        template: Dict[str, Any], 
        context: Dict[str, Any]
    ) -> str:
        """Format content as HTML newsletter"""
        structure = template.get("structure", [])
        
        # Basic HTML newsletter wrapper
        html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{context.get('title', 'AquaScene Newsletter')}</title>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .newsletter-container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ text-align: center; border-bottom: 2px solid #4CAF50; padding-bottom: 20px; }}
        .content-section {{ margin: 20px 0; padding: 15px; }}
        .footer {{ text-align: center; border-top: 1px solid #ddd; padding-top: 20px; margin-top: 30px; }}
        .cta-button {{ display: inline-block; padding: 12px 24px; background-color: #4CAF50; color: white; text-decoration: none; border-radius: 5px; }}
    </style>
</head>
<body>
    <div class="newsletter-container">
        <div class="header">
            <h1>🌿 AquaScene Newsletter</h1>
            <p>Your source for aquascaping excellence</p>
        </div>
        
        <div class="content-section">
            {content}
        </div>
        
        <div class="footer">
            <p>Happy Aquascaping!<br>
            The AquaScene Team</p>
            <p><small>© {context.get('year', '2024')} AquaScene. All rights reserved.</small></p>
        </div>
    </div>
</body>
</html>
        """.strip()
        
        return html_content
    
    async def _format_text_newsletter(
        self, 
        content: str, 
        template: Dict[str, Any], 
        context: Dict[str, Any]
    ) -> str:
        """Format content as text newsletter"""
        formatted_content = f"""
🌿 AQUASCENE NEWSLETTER
{'=' * 50}

{content}

{'=' * 50}
Happy Aquascaping!
The AquaScene Team

© {context.get('year', '2024')} AquaScene. All rights reserved.
        """.strip()
        
        return formatted_content
    
    def get_template_metadata(self, template_name: str) -> Optional[Dict[str, Any]]:
        """Get metadata for a newsletter template"""
        template = self.templates.get(template_name)
        return template.get("metadata") if template else None
    
    def get_available_templates(self) -> Dict[str, Dict[str, Any]]:
        """Get list of available newsletter templates"""
        return {
            name: {
                "structure": template.get("structure", []),
                "format": template.get("format", "html"),
                "metadata": template.get("metadata", {})
            }
            for name, template in self.templates.items()
        }