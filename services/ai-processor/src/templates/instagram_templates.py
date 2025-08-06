"""
Instagram Templates

Manages Instagram-specific template handling and formatting.
"""

from typing import Dict, Any, Optional, List
import structlog

logger = structlog.get_logger()


class InstagramTemplates:
    """Handles Instagram-specific template processing"""
    
    def __init__(self):
        self.templates = self._load_builtin_templates()
        self.hashtag_groups = self._load_hashtag_groups()
    
    def _load_builtin_templates(self) -> Dict[str, Dict[str, Any]]:
        """Load built-in Instagram templates"""
        return {
            "aquascape-showcase": {
                "structure": [
                    "hook",
                    "description", 
                    "technical_details",
                    "inspiration",
                    "hashtags",
                    "call_to_action"
                ],
                "max_length": 2200,
                "emoji_style": "nature",
                "metadata": {
                    "type": "showcase",
                    "engagement_style": "educational"
                }
            },
            "plant-spotlight": {
                "structure": [
                    "plant_intro",
                    "care_requirements",
                    "aquascaping_tips",
                    "pro_tips",
                    "hashtags",
                    "question"
                ],
                "max_length": 2200,
                "emoji_style": "plants",
                "metadata": {
                    "type": "educational",
                    "focus": "plant_care"
                }
            },
            "technique-tutorial": {
                "structure": [
                    "technique_name",
                    "difficulty_level",
                    "materials_needed",
                    "key_steps",
                    "pro_tips",
                    "hashtags",
                    "engagement_hook"
                ],
                "max_length": 2200,
                "emoji_style": "tools",
                "metadata": {
                    "type": "tutorial",
                    "skill_level": "intermediate"
                }
            },
            "community-feature": {
                "structure": [
                    "community_spotlight",
                    "tank_description",
                    "aquascaper_story",
                    "inspiration_message",
                    "hashtags",
                    "community_call"
                ],
                "max_length": 2200,
                "emoji_style": "community",
                "metadata": {
                    "type": "community",
                    "purpose": "engagement"
                }
            }
        }
    
    def _load_hashtag_groups(self) -> Dict[str, List[str]]:
        """Load categorized hashtag groups"""
        return {
            "aquascaping": [
                "#aquascaping", "#plantedtank", "#aquascape", "#natureaquarium",
                "#aquascaper", "#plantedaquarium", "#aquascapedesign", "#aquaticplants"
            ],
            "brands": [
                "#ada", "#tropica", "#greenaqua", "#chihiros", "#oase",
                "#eheim", "#fluval", "#jbl", "#seachem", "#dennerle"
            ],
            "techniques": [
                "#iwagumistyle", "#dutchstyle", "#naturestyle", "#junglestyle",
                "#hardscape", "#driftwood", "#dragonstone", "#seiryu"
            ],
            "plants": [
                "#aquaticplants", "#stemplants", "#carpetplants", "#mosses",
                "#anubias", "#bucephalandra", "#cryptocoryne", "#rotala"
            ],
            "community": [
                "#aquariumhobby", "#fishtank", "#aquariumlife", "#plantedtanklife",
                "#aquascapingcommunity", "#aquariumlove", "#underwaterworld"
            ],
            "general": [
                "#aquarium", "#fish", "#plants", "#nature", "#water", "#green",
                "#peaceful", "#zen", "#hobby", "#passion"
            ]
        }
    
    async def apply_template(
        self, 
        template_name: str, 
        content: str, 
        context: Dict[str, Any]
    ) -> str:
        """Apply Instagram template to content"""
        template = self.templates.get(template_name)
        if not template:
            logger.warning(f"Instagram template not found: {template_name}")
            return self._add_basic_formatting(content, context)
        
        try:
            # Format content based on template
            formatted_content = await self._format_instagram_post(content, template, context)
            
            # Add hashtags
            formatted_content = self._add_hashtags(formatted_content, template, context)
            
            # Ensure length compliance
            formatted_content = self._ensure_length_compliance(formatted_content, template)
            
            return formatted_content
                
        except Exception as e:
            logger.error(f"Error applying Instagram template {template_name}", error=str(e))
            return self._add_basic_formatting(content, context)
    
    async def _format_instagram_post(
        self, 
        content: str, 
        template: Dict[str, Any], 
        context: Dict[str, Any]
    ) -> str:
        """Format content according to Instagram template structure"""
        emoji_style = template.get("emoji_style", "nature")
        emojis = self._get_emoji_set(emoji_style)
        
        # Add appropriate emojis and formatting
        lines = content.split('\n')
        formatted_lines = []
        
        for i, line in enumerate(lines):
            if not line.strip():
                formatted_lines.append(line)
                continue
                
            # Add emoji to first line (hook)
            if i == 0 and emojis:
                formatted_lines.append(f"{emojis[0]} {line.strip()}")
            else:
                formatted_lines.append(line)
        
        formatted_content = '\n'.join(formatted_lines)
        
        # Add call-to-action based on template type
        cta = self._get_call_to_action(template)
        if cta:
            formatted_content += f"\n\n{cta}"
        
        return formatted_content
    
    def _get_emoji_set(self, style: str) -> List[str]:
        """Get emoji set based on style"""
        emoji_sets = {
            "nature": ["🌿", "🌱", "💚", "🍃", "🌊", "✨"],
            "plants": ["🌱", "🌿", "🍀", "🌾", "🌳", "💚"],
            "tools": ["🔧", "⚡", "🎨", "📐", "✨", "💡"],
            "community": ["👥", "💬", "❤️", "🙌", "👏", "🌟"],
            "fish": ["🐠", "🐟", "🌊", "💙", "🌀", "✨"]
        }
        return emoji_sets.get(style, emoji_sets["nature"])
    
    def _get_call_to_action(self, template: Dict[str, Any]) -> Optional[str]:
        """Get appropriate call-to-action based on template type"""
        template_type = template.get("metadata", {}).get("type", "general")
        
        ctas = {
            "showcase": "💭 What's your favorite element in this aquascape? Let me know in the comments!",
            "educational": "💡 Found this helpful? Save this post and share it with fellow aquascapers!",
            "tutorial": "🎯 Give this technique a try and tag us in your results!",
            "community": "👥 Tag a fellow aquascaper who would love this setup!",
            "general": "💚 Double tap if you love planted tanks like we do!"
        }
        
        return ctas.get(template_type)
    
    def _add_hashtags(
        self, 
        content: str, 
        template: Dict[str, Any], 
        context: Dict[str, Any]
    ) -> str:
        """Add relevant hashtags to the post"""
        # Get hashtags from context or generate based on template
        custom_hashtags = context.get("hashtags", [])
        
        if custom_hashtags:
            hashtag_text = " ".join(custom_hashtags)
        else:
            # Generate hashtags based on template type and content
            hashtag_text = self._generate_hashtags(template, context)
        
        # Add hashtags section
        if hashtag_text:
            content += f"\n\n{hashtag_text}"
        
        return content
    
    def _generate_hashtags(self, template: Dict[str, Any], context: Dict[str, Any]) -> str:
        """Generate relevant hashtags based on template and context"""
        template_type = template.get("metadata", {}).get("type", "general")
        
        # Select hashtag groups based on template type
        selected_hashtags = []
        
        # Always include core aquascaping hashtags
        selected_hashtags.extend(self.hashtag_groups["aquascaping"][:3])
        
        # Add template-specific hashtags
        if template_type == "educational":
            selected_hashtags.extend(self.hashtag_groups["plants"][:2])
            selected_hashtags.extend(self.hashtag_groups["techniques"][:2])
        elif template_type == "showcase":
            selected_hashtags.extend(self.hashtag_groups["techniques"][:2])
            selected_hashtags.extend(self.hashtag_groups["brands"][:1])
        elif template_type == "community":
            selected_hashtags.extend(self.hashtag_groups["community"][:3])
        
        # Add general hashtags
        selected_hashtags.extend(self.hashtag_groups["general"][:2])
        
        # Remove duplicates and limit to 20 hashtags
        unique_hashtags = list(dict.fromkeys(selected_hashtags))[:20]
        
        return " ".join(unique_hashtags)
    
    def _ensure_length_compliance(self, content: str, template: Dict[str, Any]) -> str:
        """Ensure content meets Instagram length requirements"""
        max_length = template.get("max_length", 2200)
        
        if len(content) <= max_length:
            return content
        
        # If too long, truncate while preserving hashtags
        lines = content.split('\n')
        hashtag_lines = [line for line in lines if line.strip().startswith('#')]
        content_lines = [line for line in lines if not line.strip().startswith('#')]
        
        # Calculate space for hashtags
        hashtag_text = '\n'.join(hashtag_lines)
        available_space = max_length - len(hashtag_text) - 10  # buffer
        
        # Truncate content
        current_length = 0
        truncated_lines = []
        
        for line in content_lines:
            if current_length + len(line) + 1 <= available_space:
                truncated_lines.append(line)
                current_length += len(line) + 1
            else:
                break
        
        # Combine truncated content with hashtags
        if hashtag_lines:
            return '\n'.join(truncated_lines) + '\n\n' + hashtag_text
        else:
            return '\n'.join(truncated_lines)
    
    def _add_basic_formatting(self, content: str, context: Dict[str, Any]) -> str:
        """Add basic Instagram formatting when no template is available"""
        # Add basic emoji and hashtags
        basic_hashtags = " ".join(self.hashtag_groups["aquascaping"][:5])
        return f"🌿 {content}\n\n{basic_hashtags}"
    
    def get_template_metadata(self, template_name: str) -> Optional[Dict[str, Any]]:
        """Get metadata for an Instagram template"""
        template = self.templates.get(template_name)
        return template.get("metadata") if template else None
    
    def get_available_templates(self) -> Dict[str, Dict[str, Any]]:
        """Get list of available Instagram templates"""
        return {
            name: {
                "structure": template.get("structure", []),
                "max_length": template.get("max_length", 2200),
                "emoji_style": template.get("emoji_style", "nature"),
                "metadata": template.get("metadata", {})
            }
            for name, template in self.templates.items()
        }
    
    def get_hashtag_groups(self) -> Dict[str, List[str]]:
        """Get available hashtag groups"""
        return self.hashtag_groups.copy()