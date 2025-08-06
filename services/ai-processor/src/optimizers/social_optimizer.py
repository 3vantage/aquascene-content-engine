"""
Social Media Optimizer

Optimizes content specifically for social media platforms with 
platform-specific best practices and engagement strategies.
"""

import re
from typing import Dict, List, Optional, Any
import structlog

from ..llm_clients.base_client import ContentType

logger = structlog.get_logger()


class SocialOptimizer:
    """Optimizes content for social media platforms"""
    
    def __init__(self):
        # Platform-specific optimization rules
        self.platform_rules = {
            "instagram": {
                "max_caption_length": 2200,
                "optimal_caption_length": 125,
                "max_hashtags": 30,
                "optimal_hashtags": 5,
                "emoji_usage": "encouraged",
                "call_to_action": "required",
                "visual_references": "required"
            },
            "facebook": {
                "max_caption_length": 63206,
                "optimal_caption_length": 80,
                "max_hashtags": 3,
                "optimal_hashtags": 2,
                "emoji_usage": "moderate",
                "call_to_action": "optional",
                "visual_references": "optional"
            },
            "twitter": {
                "max_caption_length": 280,
                "optimal_caption_length": 250,
                "max_hashtags": 2,
                "optimal_hashtags": 1,
                "emoji_usage": "moderate",
                "call_to_action": "optional",
                "visual_references": "optional"
            }
        }
        
        # Aquascaping-specific hashtags by category
        self.aquascaping_hashtags = {
            "general": [
                "#aquascaping", "#plantedtank", "#natureaquarium", "#aquascapers",
                "#freshwateraquarium", "#aquascape", "#plantedaquarium"
            ],
            "plants": [
                "#aquaticplants", "#aquaplants", "#plantedtanklife", "#liveplants",
                "#anubias", "#bucephalandra", "#cryptocoryne", "#rotala"
            ],
            "hardscape": [
                "#driftwood", "#dragonstone", "#ohkostone", "#hardscape",
                "#aquascapedesign", "#layoutdesign"
            ],
            "technique": [
                "#dutchstyle", "#iwagumi", "#naturestyle", "#aquascapetutorial",
                "#plantcare", "#trimming", "#aquascapingguide"
            ],
            "equipment": [
                "#co2injection", "#aquariumlighting", "#plantfertilizer",
                "#aquasoil", "#canisterfilter"
            ],
            "community": [
                "#aquascapingcommunity", "#plantedtankcommunity", "#aquariumhobby",
                "#aquarists", "#plantkeepers"
            ]
        }
        
        # Visual reference words that work well on social media
        self.visual_words = [
            "look", "see", "gorgeous", "stunning", "beautiful", "amazing",
            "check out", "feast your eyes", "incredible", "mesmerizing",
            "vibrant", "lush", "pristine", "crystal clear"
        ]
        
        # Call-to-action phrases optimized for social media
        self.social_ctas = {
            "engagement": [
                "What do you think?",
                "Drop a 💚 if you love this!",
                "Tag someone who needs to see this!",
                "Double tap if you're inspired!",
                "Share your thoughts below!",
                "Which plant would you add next?"
            ],
            "community": [
                "Join our aquascaping community!",
                "Follow for daily aquascape inspiration!",
                "Connect with fellow aquascapers!",
                "Share your setup with us!",
                "Be part of our plant-loving family!"
            ],
            "educational": [
                "Save this for your next aquascape!",
                "Swipe for the step-by-step guide!",
                "Link in bio for the full tutorial!",
                "DM us for plant recommendations!",
                "Comment 'GUIDE' for our free setup checklist!"
            ]
        }
        
        # Best posting times and frequency recommendations
        self.posting_guidelines = {
            "instagram": {
                "best_times": ["6-9 AM", "12-2 PM", "5-7 PM"],
                "frequency": "1-2 posts per day",
                "story_frequency": "3-5 stories per day"
            },
            "facebook": {
                "best_times": ["9 AM", "1-3 PM", "3 PM"],
                "frequency": "3-5 posts per week",
                "engagement_window": "2-4 hours"
            }
        }
    
    async def optimize_for_social(
        self,
        content: str,
        platform: str = "instagram",
        content_type: ContentType = ContentType.INSTAGRAM_CAPTION,
        topic: Optional[str] = None
    ) -> Dict[str, Any]:
        """Optimize content for social media platform"""
        
        platform_rules = self.platform_rules.get(platform, self.platform_rules["instagram"])
        
        result = {
            "optimization_type": "social_media",
            "platform": platform,
            "optimized_content": content,
            "hashtags": [],
            "improvement_score": 0.0,
            "recommendations": [],
            "warnings": []
        }
        
        # Analyze current content
        current_analysis = self._analyze_social_content(content, platform_rules)
        
        # Apply social media optimizations
        optimized_content = await self._apply_social_optimizations(
            content, platform, platform_rules, current_analysis, topic
        )
        
        # Generate hashtags
        hashtags = self._generate_hashtags(content, topic, platform)
        
        # Calculate improvement score
        improvement_score = self._calculate_social_improvement(
            current_analysis, platform_rules
        )
        
        # Generate recommendations
        recommendations = self._generate_social_recommendations(
            current_analysis, platform_rules, platform
        )
        
        # Check for warnings
        warnings = self._check_social_warnings(content, platform_rules)
        
        result.update({
            "optimized_content": optimized_content,
            "hashtags": hashtags,
            "improvement_score": improvement_score,
            "recommendations": recommendations,
            "warnings": warnings,
            "analysis": current_analysis
        })
        
        return result
    
    def _analyze_social_content(self, content: str, platform_rules: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze content for social media metrics"""
        analysis = {
            "length": len(content),
            "word_count": len(content.split()),
            "hashtag_count": len(re.findall(r'#\w+', content)),
            "emoji_count": len(re.findall(r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F700-\U0001F77F\U0001F780-\U0001F7FF\U0001F800-\U0001F8FF\U0001F900-\U0001F9FF\U0001FA00-\U0001FA6F\U0001FA70-\U0001FAFF\U00002600-\U000026FF\U00002700-\U000027BF]', content)),
            "question_count": content.count('?'),
            "exclamation_count": content.count('!'),
            "mention_count": content.count('@'),
            "visual_words": 0,
            "cta_present": False,
            "engagement_elements": 0
        }
        
        # Count visual reference words
        content_lower = content.lower()
        analysis["visual_words"] = sum(
            1 for word in self.visual_words if word in content_lower
        )
        
        # Check for call-to-action
        all_ctas = []
        for cta_list in self.social_ctas.values():
            all_ctas.extend(cta_list)
        
        analysis["cta_present"] = any(
            cta.lower() in content_lower for cta in all_ctas
        )
        
        # Calculate engagement elements
        analysis["engagement_elements"] = (
            analysis["question_count"] + 
            analysis["exclamation_count"] + 
            (1 if analysis["cta_present"] else 0) +
            min(analysis["emoji_count"], 3)  # Cap emoji contribution
        )
        
        return analysis
    
    async def _apply_social_optimizations(
        self,
        content: str,
        platform: str,
        platform_rules: Dict[str, Any],
        analysis: Dict[str, Any],
        topic: Optional[str]
    ) -> str:
        """Apply platform-specific optimizations"""
        optimized = content
        
        # Optimize length
        if analysis["length"] > platform_rules["max_caption_length"]:
            optimized = self._truncate_intelligently(
                optimized, platform_rules["max_caption_length"]
            )
        
        # Add visual references if missing
        if analysis["visual_words"] == 0 and platform_rules.get("visual_references") == "required":
            optimized = self._add_visual_hook(optimized)
        
        # Add call-to-action if missing
        if not analysis["cta_present"] and platform_rules.get("call_to_action") == "required":
            optimized = self._add_social_cta(optimized, platform)
        
        # Optimize for engagement
        if analysis["engagement_elements"] < 2:
            optimized = self._enhance_engagement(optimized, platform)
        
        # Platform-specific optimizations
        if platform == "instagram":
            optimized = self._optimize_for_instagram(optimized, analysis)
        elif platform == "facebook":
            optimized = self._optimize_for_facebook(optimized, analysis)
        elif platform == "twitter":
            optimized = self._optimize_for_twitter(optimized, analysis)
        
        return optimized
    
    def _generate_hashtags(
        self, 
        content: str, 
        topic: Optional[str], 
        platform: str
    ) -> List[str]:
        """Generate relevant hashtags for the content"""
        hashtags = []
        content_lower = content.lower()
        
        # Always include general aquascaping hashtags
        hashtags.extend(self.aquascaping_hashtags["general"][:2])
        
        # Add category-specific hashtags based on content
        if any(plant in content_lower for plant in ["anubias", "plant", "vegetation", "green"]):
            hashtags.extend(self.aquascaping_hashtags["plants"][:2])
        
        if any(term in content_lower for term in ["stone", "wood", "rock", "hardscape"]):
            hashtags.extend(self.aquascaping_hashtags["hardscape"][:1])
        
        if any(term in content_lower for term in ["dutch", "iwagumi", "nature", "tutorial", "guide"]):
            hashtags.extend(self.aquascaping_hashtags["technique"][:1])
        
        if any(term in content_lower for term in ["co2", "light", "filter", "equipment"]):
            hashtags.extend(self.aquascaping_hashtags["equipment"][:1])
        
        # Add community hashtags
        hashtags.extend(self.aquascaping_hashtags["community"][:1])
        
        # Remove duplicates and limit based on platform
        hashtags = list(dict.fromkeys(hashtags))  # Remove duplicates while preserving order
        
        platform_rules = self.platform_rules.get(platform, self.platform_rules["instagram"])
        max_hashtags = platform_rules["optimal_hashtags"]
        
        return hashtags[:max_hashtags]
    
    def _truncate_intelligently(self, content: str, max_length: int) -> str:
        """Truncate content while preserving meaning"""
        if len(content) <= max_length:
            return content
        
        # Try to truncate at sentence boundaries
        sentences = re.split(r'[.!?]+', content)
        truncated = ""
        
        for sentence in sentences:
            if len(truncated + sentence + ".") <= max_length - 20:  # Leave space for "..."
                truncated += sentence + "."
            else:
                break
        
        if not truncated:  # If even first sentence is too long
            truncated = content[:max_length-3] + "..."
        else:
            truncated += ".."
        
        return truncated.strip()
    
    def _add_visual_hook(self, content: str) -> str:
        """Add visual reference to content"""
        hooks = [
            "Look at this stunning setup! ",
            "Check out this gorgeous aquascape! ",
            "Feast your eyes on this beauty! "
        ]
        
        import random
        hook = random.choice(hooks)
        return hook + content
    
    def _add_social_cta(self, content: str, platform: str) -> str:
        """Add platform-appropriate call-to-action"""
        if platform == "instagram":
            ctas = self.social_ctas["engagement"]
        else:
            ctas = self.social_ctas["community"]
        
        import random
        cta = random.choice(ctas)
        
        # Add CTA at the end
        if not content.endswith(('!', '?', '.')):
            content += '.'
        
        return f"{content}\n\n{cta}"
    
    def _enhance_engagement(self, content: str, platform: str) -> str:
        """Enhance content for better engagement"""
        enhanced = content
        
        # Add emoji if appropriate
        if platform == "instagram" and "🌱" not in enhanced and "💚" not in enhanced:
            enhanced = enhanced.replace("!", "! 🌱", 1)
        
        # Add question if missing
        if "?" not in enhanced:
            questions = [
                " What's your favorite part about this setup?",
                " Have you tried something similar?",
                " What would you change about this aquascape?"
            ]
            
            import random
            enhanced += random.choice(questions)
        
        return enhanced
    
    def _optimize_for_instagram(self, content: str, analysis: Dict[str, Any]) -> str:
        """Instagram-specific optimizations"""
        optimized = content
        
        # Ensure visual language
        if analysis["visual_words"] < 2:
            visual_phrases = [
                "The colors are absolutely stunning! ",
                "This view is breathtaking! ",
                "Look at those gorgeous details! "
            ]
            
            import random
            optimized = random.choice(visual_phrases) + optimized
        
        # Add line breaks for readability on mobile
        if "\n" not in optimized and len(optimized) > 100:
            # Add break after first sentence
            first_sentence_end = re.search(r'[.!?]', optimized)
            if first_sentence_end:
                pos = first_sentence_end.end()
                optimized = optimized[:pos] + "\n\n" + optimized[pos:].strip()
        
        return optimized
    
    def _optimize_for_facebook(self, content: str, analysis: Dict[str, Any]) -> str:
        """Facebook-specific optimizations"""
        optimized = content
        
        # Facebook prefers shorter, more concise content
        if len(optimized) > 200:  # Optimal Facebook length
            optimized = self._truncate_intelligently(optimized, 200)
        
        # Add community element
        if "community" not in optimized.lower():
            community_phrases = [
                "Our aquascaping community loves setups like this! ",
                "Fellow aquascapers, what do you think? ",
                "The planted tank community is amazing! "
            ]
            
            import random
            optimized = random.choice(community_phrases) + optimized
        
        return optimized
    
    def _optimize_for_twitter(self, content: str, analysis: Dict[str, Any]) -> str:
        """Twitter-specific optimizations"""
        optimized = content
        
        # Ensure content fits Twitter length limits
        if len(optimized) > 250:  # Leave room for hashtags
            optimized = self._truncate_intelligently(optimized, 250)
        
        # Make content more punchy for Twitter
        optimized = re.sub(r'\s+', ' ', optimized)  # Remove extra whitespace
        optimized = optimized.replace('. ', '. ')  # Ensure proper spacing
        
        return optimized
    
    def _calculate_social_improvement(
        self, 
        analysis: Dict[str, Any], 
        platform_rules: Dict[str, Any]
    ) -> float:
        """Calculate improvement score for social optimization"""
        improvements = 0
        total_checks = 0
        
        # Length optimization
        if analysis["length"] > platform_rules["max_caption_length"]:
            improvements += 1
        total_checks += 1
        
        # Hashtag optimization
        optimal_hashtags = platform_rules["optimal_hashtags"]
        if analysis["hashtag_count"] < optimal_hashtags:
            improvements += 1
        total_checks += 1
        
        # Visual references
        if platform_rules.get("visual_references") == "required" and analysis["visual_words"] == 0:
            improvements += 1
        total_checks += 1
        
        # Call-to-action
        if platform_rules.get("call_to_action") == "required" and not analysis["cta_present"]:
            improvements += 1
        total_checks += 1
        
        # Engagement elements
        if analysis["engagement_elements"] < 2:
            improvements += 1
        total_checks += 1
        
        return improvements / total_checks if total_checks > 0 else 0
    
    def _generate_social_recommendations(
        self, 
        analysis: Dict[str, Any], 
        platform_rules: Dict[str, Any], 
        platform: str
    ) -> List[str]:
        """Generate social media optimization recommendations"""
        recommendations = []
        
        # Length recommendations
        if analysis["length"] > platform_rules["max_caption_length"]:
            recommendations.append(f"Content is too long for {platform}. Consider shortening.")
        elif analysis["length"] < platform_rules["optimal_caption_length"]:
            recommendations.append(f"Content could be longer for better {platform} engagement.")
        
        # Hashtag recommendations
        optimal_hashtags = platform_rules["optimal_hashtags"]
        if analysis["hashtag_count"] < optimal_hashtags:
            recommendations.append(f"Add {optimal_hashtags - analysis['hashtag_count']} more relevant hashtags.")
        elif analysis["hashtag_count"] > platform_rules["max_hashtags"]:
            recommendations.append(f"Reduce hashtags to {platform_rules['max_hashtags']} or fewer.")
        
        # Visual recommendations
        if platform_rules.get("visual_references") == "required" and analysis["visual_words"] < 2:
            recommendations.append("Add more visual language to complement the image.")
        
        # Engagement recommendations
        if analysis["engagement_elements"] < 2:
            recommendations.append("Add questions, calls-to-action, or emojis to boost engagement.")
        
        # Platform-specific recommendations
        if platform == "instagram":
            if analysis["emoji_count"] == 0:
                recommendations.append("Consider adding relevant emojis for Instagram.")
            if "\n" not in analysis and len(analysis) > 100:
                recommendations.append("Add line breaks for better mobile readability.")
        
        elif platform == "facebook":
            if "community" not in analysis:
                recommendations.append("Reference your community to build connection.")
        
        elif platform == "twitter":
            if analysis["length"] > 200:
                recommendations.append("Keep Twitter content punchy and concise.")
        
        return recommendations
    
    def _check_social_warnings(self, content: str, platform_rules: Dict[str, Any]) -> List[str]:
        """Check for potential social media issues"""
        warnings = []
        
        # Check for spammy content
        if content.count('#') > 10:
            warnings.append("Too many hashtags may appear spammy")
        
        # Check for excessive capitalization
        if re.search(r'[A-Z]{5,}', content):
            warnings.append("Excessive capitalization may reduce engagement")
        
        # Check for repetitive punctuation
        if re.search(r'[!]{3,}|[?]{3,}', content):
            warnings.append("Excessive punctuation may appear unprofessional")
        
        # Check for potential policy violations
        prohibited_terms = ['guaranteed results', 'instant success', 'click here now']
        for term in prohibited_terms:
            if term.lower() in content.lower():
                warnings.append(f"Avoid promotional language like '{term}'")
        
        return warnings
    
    def get_posting_recommendations(self, platform: str) -> Dict[str, Any]:
        """Get posting time and frequency recommendations"""
        return self.posting_guidelines.get(platform, {})
    
    def get_trending_hashtags(self, category: str = "general") -> List[str]:
        """Get trending hashtags for a category"""
        return self.aquascaping_hashtags.get(category, self.aquascaping_hashtags["general"])