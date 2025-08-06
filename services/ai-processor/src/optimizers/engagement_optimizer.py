"""
Engagement Optimizer

Optimizes content for audience engagement, interaction, and conversion
with aquascaping community-specific strategies.
"""

import re
from typing import Dict, List, Optional, Any
import structlog

from ..llm_clients.base_client import ContentType

logger = structlog.get_logger()


class EngagementOptimizer:
    """Optimizes content for audience engagement"""
    
    def __init__(self):
        # Engagement elements for different content types
        self.engagement_elements = {
            "questions": [
                "What's your experience with",
                "Have you tried",
                "Which method do you prefer",
                "What challenges have you faced",
                "How do you handle",
                "What's your favorite"
            ],
            "calls_to_action": [
                "Share your experience in the comments",
                "Let us know what you think",
                "Tag a friend who needs to see this",
                "Follow for more aquascaping tips",
                "Subscribe to our newsletter",
                "Join our community"
            ],
            "personal_touches": [
                "In my experience",
                "I've found that",
                "We recommend",
                "Our team suggests",
                "Based on our experience"
            ],
            "emotional_words": [
                "amazing", "beautiful", "stunning", "incredible", "gorgeous",
                "fascinating", "exciting", "rewarding", "satisfying", "peaceful"
            ]
        }
        
        # Content type specific engagement strategies
        self.engagement_strategies = {
            ContentType.NEWSLETTER_ARTICLE: {
                "questions": 2,
                "personal_touches": 3,
                "calls_to_action": 1,
                "storytelling": True,
                "community_references": True
            },
            ContentType.INSTAGRAM_CAPTION: {
                "questions": 1,
                "calls_to_action": 1,
                "emotional_words": 3,
                "hashtags": True,
                "visual_references": True
            },
            ContentType.COMMUNITY_POST: {
                "questions": 2,
                "personal_touches": 2,
                "discussion_starters": True,
                "community_references": True
            },
            ContentType.HOW_TO_GUIDE: {
                "encouragement": 2,
                "personal_touches": 1,
                "success_stories": True,
                "troubleshooting": True
            }
        }
    
    async def optimize(
        self,
        content: str,
        content_type: ContentType,
        target_audience: Optional[str] = None
    ) -> Dict[str, Any]:
        """Optimize content for engagement"""
        
        result = {
            "optimization_type": "engagement",
            "optimized_content": content,
            "improvement_score": 0.0,
            "scores": {},
            "suggestions": [],
            "warnings": []
        }
        
        # Analyze current engagement elements
        current_analysis = self._analyze_engagement_elements(content, content_type)
        
        # Apply engagement optimizations
        optimized_content = await self._apply_engagement_optimizations(
            content, content_type, current_analysis, target_audience
        )
        
        # Calculate improvement
        if optimized_content != content:
            result["optimized_content"] = optimized_content
            result["improvement_score"] = self._calculate_engagement_improvement(
                current_analysis, content_type
            )
        
        # Generate engagement scores and suggestions
        result["scores"] = self._calculate_engagement_scores(optimized_content, content_type)
        result["suggestions"] = self._generate_engagement_suggestions(current_analysis, content_type)
        
        return result
    
    def _analyze_engagement_elements(self, content: str, content_type: ContentType) -> Dict[str, Any]:
        """Analyze current engagement elements in content"""
        content_lower = content.lower()
        
        analysis = {
            "questions": len(re.findall(r'\?', content)),
            "calls_to_action": 0,
            "personal_touches": 0,
            "emotional_words": 0,
            "visual_references": 0,
            "community_references": 0,
            "storytelling_elements": 0,
            "encouragement_phrases": 0
        }
        
        # Count calls to action
        for cta in self.engagement_elements["calls_to_action"]:
            if any(word in content_lower for word in cta.lower().split()[:3]):
                analysis["calls_to_action"] += 1
        
        # Count personal touches
        for touch in self.engagement_elements["personal_touches"]:
            if touch.lower() in content_lower:
                analysis["personal_touches"] += 1
        
        # Count emotional words
        for word in self.engagement_elements["emotional_words"]:
            analysis["emotional_words"] += content_lower.count(word)
        
        # Visual references (for Instagram/visual content)
        visual_words = ["see", "look", "picture", "image", "photo", "visual", "beautiful", "stunning"]
        analysis["visual_references"] = sum(1 for word in visual_words if word in content_lower)
        
        # Community references
        community_words = ["community", "fellow", "together", "share", "discuss", "experience"]
        analysis["community_references"] = sum(1 for word in community_words if word in content_lower)
        
        # Storytelling elements
        story_indicators = ["when i", "last week", "recently", "story", "experience", "journey"]
        analysis["storytelling_elements"] = sum(1 for indicator in story_indicators if indicator in content_lower)
        
        # Encouragement phrases
        encouragement_words = ["you can", "don't worry", "it's okay", "great job", "well done", "keep going"]
        analysis["encouragement_phrases"] = sum(1 for phrase in encouragement_words if phrase in content_lower)
        
        return analysis
    
    async def _apply_engagement_optimizations(
        self,
        content: str,
        content_type: ContentType,
        analysis: Dict[str, Any],
        target_audience: Optional[str]
    ) -> str:
        """Apply engagement optimizations to content"""
        optimized = content
        strategy = self.engagement_strategies.get(content_type, {})
        
        # Add questions if needed
        target_questions = strategy.get("questions", 0)
        if analysis["questions"] < target_questions:
            questions_needed = target_questions - analysis["questions"]
            optimized = self._add_engaging_questions(optimized, content_type, questions_needed)
        
        # Add calls to action if needed
        target_ctas = strategy.get("calls_to_action", 0)
        if analysis["calls_to_action"] < target_ctas:
            optimized = self._add_call_to_action(optimized, content_type)
        
        # Add personal touches if needed
        target_personal = strategy.get("personal_touches", 0)
        if analysis["personal_touches"] < target_personal:
            touches_needed = target_personal - analysis["personal_touches"]
            optimized = self._add_personal_touches(optimized, content_type, touches_needed)
        
        # Add emotional words if needed
        target_emotional = strategy.get("emotional_words", 0)
        if analysis["emotional_words"] < target_emotional:
            optimized = self._enhance_emotional_language(optimized, content_type)
        
        # Content type specific optimizations
        if content_type == ContentType.INSTAGRAM_CAPTION:
            optimized = self._optimize_for_instagram_engagement(optimized, analysis)
        elif content_type == ContentType.NEWSLETTER_ARTICLE:
            optimized = self._optimize_for_newsletter_engagement(optimized, analysis)
        elif content_type == ContentType.HOW_TO_GUIDE:
            optimized = self._optimize_for_tutorial_engagement(optimized, analysis)
        
        return optimized
    
    def _add_engaging_questions(self, content: str, content_type: ContentType, count: int) -> str:
        """Add engaging questions to content"""
        if count <= 0:
            return content
        
        # Choose appropriate questions based on content type
        if content_type == ContentType.INSTAGRAM_CAPTION:
            questions = [
                "What's your take on this setup?",
                "Have you tried this technique?",
                "Which plant would you add next?"
            ]
        elif content_type == ContentType.NEWSLETTER_ARTICLE:
            questions = [
                "What's been your biggest aquascaping challenge?",
                "Have you experimented with this approach?",
                "Which technique has worked best for you?"
            ]
        else:
            questions = [
                "What's your experience with this?",
                "Have you encountered similar issues?",
                "What would you do differently?"
            ]
        
        # Add questions at strategic points
        paragraphs = content.split('\n\n')
        
        for i in range(min(count, len(questions))):
            if len(paragraphs) > i + 1:
                # Add question at the end of a paragraph
                paragraphs[i + 1] += f" {questions[i]}"
        
        return '\n\n'.join(paragraphs)
    
    def _add_call_to_action(self, content: str, content_type: ContentType) -> str:
        """Add appropriate call to action"""
        ctas = {
            ContentType.NEWSLETTER_ARTICLE: "What's your experience with this technique? Share your thoughts with our community!",
            ContentType.INSTAGRAM_CAPTION: "Double tap if you love this setup! 💚 What would you change?",
            ContentType.COMMUNITY_POST: "Join the discussion - what's your take on this?",
            ContentType.HOW_TO_GUIDE: "Try this technique and let us know how it works for you!"
        }
        
        cta = ctas.get(content_type, "Share your thoughts in the comments!")
        
        # Add CTA at the end
        if not content.endswith(('!', '?', '.')):
            content += '.'
        
        return f"{content}\n\n{cta}"
    
    def _add_personal_touches(self, content: str, content_type: ContentType, count: int) -> str:
        """Add personal touches to make content more relatable"""
        if count <= 0:
            return content
        
        personal_phrases = [
            "In our experience,",
            "We've found that",
            "Based on what we've seen,",
            "From our testing,",
            "Our community has shared that"
        ]
        
        sentences = content.split('. ')
        
        # Add personal touches to appropriate sentences
        for i in range(min(count, len(sentences) - 1)):
            # Find sentences that could benefit from personal touch
            sentence = sentences[i].strip()
            if (len(sentence) > 50 and 
                not sentence.lower().startswith(('in ', 'we ', 'our ', 'based '))):
                
                personal_phrase = personal_phrases[i % len(personal_phrases)]
                sentences[i] = f"{personal_phrase} {sentence.lower()}"
        
        return '. '.join(sentences)
    
    def _enhance_emotional_language(self, content: str, content_type: ContentType) -> str:
        """Enhance content with more emotional language"""
        # Replace neutral words with more emotional alternatives
        emotional_replacements = {
            "good": "amazing",
            "nice": "beautiful",
            "works": "works wonderfully",
            "effective": "incredibly effective",
            "useful": "incredibly useful",
            "results": "stunning results",
            "setup": "gorgeous setup",
            "tank": "beautiful aquarium"
        }
        
        enhanced = content
        
        for neutral, emotional in emotional_replacements.items():
            # Only replace whole words, case-insensitive
            pattern = r'\b' + re.escape(neutral) + r'\b'
            enhanced = re.sub(pattern, emotional, enhanced, flags=re.IGNORECASE)
        
        return enhanced
    
    def _optimize_for_instagram_engagement(self, content: str, analysis: Dict[str, Any]) -> str:
        """Apply Instagram-specific engagement optimizations"""
        optimized = content
        
        # Add visual references if missing
        if analysis["visual_references"] < 2:
            visual_phrases = [
                "Look at this gorgeous setup!",
                "The colors in this tank are incredible!",
                "Can you see the beautiful details?"
            ]
            
            # Add at the beginning
            optimized = f"{visual_phrases[0]} {optimized}"
        
        # Ensure emoji usage for Instagram
        if '💚' not in optimized and '🌱' not in optimized:
            optimized = optimized.replace('!', '! 🌱')
        
        return optimized
    
    def _optimize_for_newsletter_engagement(self, content: str, analysis: Dict[str, Any]) -> str:
        """Apply newsletter-specific engagement optimizations"""
        optimized = content
        
        # Add community elements if missing
        if analysis["community_references"] < 1:
            community_phrase = "Our aquascaping community has been sharing amazing results with this technique."
            
            # Insert in the middle of content
            paragraphs = optimized.split('\n\n')
            if len(paragraphs) > 2:
                paragraphs.insert(len(paragraphs) // 2, community_phrase)
                optimized = '\n\n'.join(paragraphs)
        
        return optimized
    
    def _optimize_for_tutorial_engagement(self, content: str, analysis: Dict[str, Any]) -> str:
        """Apply tutorial-specific engagement optimizations"""
        optimized = content
        
        # Add encouragement if missing
        if analysis["encouragement_phrases"] < 1:
            encouragement = "Don't worry if it doesn't look perfect at first - every aquascaper has been there!"
            
            # Add encouragement after the first section
            paragraphs = optimized.split('\n\n')
            if len(paragraphs) > 1:
                paragraphs.insert(1, encouragement)
                optimized = '\n\n'.join(paragraphs)
        
        return optimized
    
    def _calculate_engagement_improvement(self, analysis: Dict[str, Any], content_type: ContentType) -> float:
        """Calculate engagement improvement score"""
        strategy = self.engagement_strategies.get(content_type, {})
        improvements = 0
        total_checks = 0
        
        # Check each engagement element
        for element, target in strategy.items():
            if isinstance(target, int):
                current = analysis.get(element, 0)
                if current < target:
                    improvements += 1
                total_checks += 1
        
        return improvements / total_checks if total_checks > 0 else 0
    
    def _calculate_engagement_scores(self, content: str, content_type: ContentType) -> Dict[str, float]:
        """Calculate engagement scores"""
        analysis = self._analyze_engagement_elements(content, content_type)
        strategy = self.engagement_strategies.get(content_type, {})
        
        # Question engagement score
        target_questions = strategy.get("questions", 1)
        question_score = min(1.0, analysis["questions"] / target_questions) if target_questions > 0 else 1.0
        
        # Interaction potential score
        interaction_elements = (
            analysis["calls_to_action"] * 0.3 +
            analysis["questions"] * 0.4 +
            analysis["community_references"] * 0.3
        )
        interaction_score = min(1.0, interaction_elements / 2)
        
        # Personal connection score
        personal_score = min(1.0, (
            analysis["personal_touches"] * 0.4 +
            analysis["storytelling_elements"] * 0.3 +
            analysis["emotional_words"] * 0.1
        ) / 3)
        
        # Overall engagement score
        engagement_score = (question_score * 0.3 + interaction_score * 0.4 + personal_score * 0.3)
        
        return {
            "engagement_score": engagement_score,
            "question_score": question_score,
            "interaction_score": interaction_score,
            "personal_score": personal_score
        }
    
    def _generate_engagement_suggestions(self, analysis: Dict[str, Any], content_type: ContentType) -> List[str]:
        """Generate engagement improvement suggestions"""
        suggestions = []
        strategy = self.engagement_strategies.get(content_type, {})
        
        # Question suggestions
        target_questions = strategy.get("questions", 0)
        if analysis["questions"] < target_questions:
            suggestions.append("Add more engaging questions to encourage interaction")
        
        # Call to action suggestions
        if analysis["calls_to_action"] == 0 and strategy.get("calls_to_action", 0) > 0:
            suggestions.append("Include a call-to-action to encourage engagement")
        
        # Personal touch suggestions
        target_personal = strategy.get("personal_touches", 0)
        if analysis["personal_touches"] < target_personal:
            suggestions.append("Add more personal experiences or insights to build connection")
        
        # Emotional language suggestions
        if analysis["emotional_words"] < 2:
            suggestions.append("Use more emotional and descriptive language")
        
        # Content type specific suggestions
        if content_type == ContentType.INSTAGRAM_CAPTION:
            if analysis["visual_references"] < 1:
                suggestions.append("Add visual references to complement the image")
            if '💚' not in str(analysis) and '🌱' not in str(analysis):
                suggestions.append("Consider adding relevant emojis for social media")
        
        elif content_type == ContentType.NEWSLETTER_ARTICLE:
            if analysis["community_references"] < 1:
                suggestions.append("Reference the aquascaping community to build belonging")
        
        return suggestions