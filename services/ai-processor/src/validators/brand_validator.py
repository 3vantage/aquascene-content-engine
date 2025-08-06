"""
Brand Voice Validator

Validates content for brand consistency, voice, and tone alignment
with AquaScene's brand guidelines.
"""

import re
from typing import Dict, List, Optional, Any
import structlog

from ..llm_clients.base_client import ContentType

logger = structlog.get_logger()


class BrandValidator:
    """Validates content against brand voice and guidelines"""
    
    def __init__(self):
        # Brand voice characteristics
        self.brand_characteristics = {
            "professional": {
                "positive_indicators": [
                    "expertise", "experience", "knowledge", "proven", "reliable",
                    "established", "trusted", "quality", "precision", "careful"
                ],
                "negative_indicators": [
                    "amateur", "basic", "simple", "cheap", "quick fix"
                ]
            },
            "educational": {
                "positive_indicators": [
                    "learn", "understand", "guide", "explain", "teach", "discover",
                    "explore", "master", "technique", "method", "principle"
                ],
                "negative_indicators": [
                    "boring", "complicated", "confusing", "difficult"
                ]
            },
            "friendly": {
                "positive_indicators": [
                    "you", "your", "we", "together", "community", "share",
                    "help", "support", "welcome", "enjoy"
                ],
                "negative_indicators": [
                    "must", "should", "never", "always", "wrong", "bad"
                ]
            },
            "enthusiastic": {
                "positive_indicators": [
                    "amazing", "beautiful", "stunning", "love", "excited",
                    "passionate", "wonderful", "fantastic", "incredible"
                ],
                "negative_indicators": [
                    "okay", "fine", "average", "mediocre", "boring"
                ]
            }
        }
        
        # Content type specific brand requirements
        self.content_brand_requirements = {
            ContentType.NEWSLETTER_ARTICLE: {
                "voice": ["professional", "educational", "friendly"],
                "tone": "informative and engaging",
                "avoid": ["overly casual", "salesy", "pushy"]
            },
            ContentType.INSTAGRAM_CAPTION: {
                "voice": ["friendly", "enthusiastic", "educational"],
                "tone": "casual and inspiring",
                "avoid": ["too formal", "lengthy explanations"]
            },
            ContentType.HOW_TO_GUIDE: {
                "voice": ["professional", "educational", "helpful"],
                "tone": "clear and instructional",
                "avoid": ["ambiguous", "overly complex"]
            }
        }
        
        # AquaScene specific terminology
        self.preferred_terminology = {
            "aquascaping": ["aquascaping", "nature aquarium design"],
            "planted_tank": ["planted aquarium", "planted tank"],
            "substrate": ["aquasoil", "substrate", "planted tank substrate"],
            "co2": ["CO2", "carbon dioxide injection"],
            "fertilizer": ["plant fertilizer", "aquarium fertilizer"]
        }
    
    async def validate_brand_voice(
        self, 
        content: str, 
        content_type: ContentType
    ) -> Dict[str, Any]:
        """Validate content against brand voice guidelines"""
        
        content_lower = content.lower()
        validation_result = {
            "score": 0.0,
            "details": {},
            "issues": [],
            "suggestions": []
        }
        
        # Get requirements for this content type
        requirements = self.content_brand_requirements.get(content_type, {})
        required_voices = requirements.get("voice", [])
        
        # Validate voice characteristics
        voice_scores = {}
        for voice in required_voices:
            score = self._validate_voice_characteristic(content_lower, voice)
            voice_scores[voice] = score
        
        # Calculate overall voice score
        if voice_scores:
            voice_score = sum(voice_scores.values()) / len(voice_scores)
        else:
            voice_score = 0.7  # Default neutral score
        
        # Validate terminology usage
        terminology_score = self._validate_terminology(content_lower)
        
        # Validate content appropriateness
        appropriateness_score = self._validate_content_appropriateness(
            content_lower, content_type
        )
        
        # Check for brand-specific issues
        brand_issues = self._check_brand_issues(content_lower, content_type)
        
        # Calculate final score
        final_score = (voice_score + terminology_score + appropriateness_score) / 3
        
        validation_result.update({
            "score": final_score,
            "details": {
                "voice_scores": voice_scores,
                "terminology_score": terminology_score,
                "appropriateness_score": appropriateness_score,
                "required_voices": required_voices
            },
            "issues": brand_issues,
            "suggestions": self._generate_brand_suggestions(
                voice_scores, terminology_score, brand_issues
            )
        })
        
        return validation_result
    
    def _validate_voice_characteristic(self, content: str, voice: str) -> float:
        """Validate a specific voice characteristic"""
        if voice not in self.brand_characteristics:
            return 0.5  # Neutral score for unknown characteristics
        
        char_data = self.brand_characteristics[voice]
        positive_indicators = char_data.get("positive_indicators", [])
        negative_indicators = char_data.get("negative_indicators", [])
        
        # Count positive indicators
        positive_count = sum(
            1 for indicator in positive_indicators 
            if indicator in content
        )
        
        # Count negative indicators
        negative_count = sum(
            1 for indicator in negative_indicators 
            if indicator in content
        )
        
        # Calculate score based on indicators
        total_words = len(content.split())
        positive_ratio = positive_count / max(total_words / 100, 1)  # per 100 words
        negative_ratio = negative_count / max(total_words / 100, 1)
        
        # Score calculation
        score = 0.5 + (positive_ratio * 0.3) - (negative_ratio * 0.4)
        return max(0.0, min(1.0, score))
    
    def _validate_terminology(self, content: str) -> float:
        """Validate use of preferred terminology"""
        score = 0.5  # Start with neutral score
        
        for concept, preferred_terms in self.preferred_terminology.items():
            # Check if concept is mentioned
            concept_mentioned = any(term in content for term in preferred_terms)
            
            if concept_mentioned:
                # Check if preferred terminology is used
                preferred_used = any(
                    term in content for term in preferred_terms[:1]  # First term is most preferred
                )
                
                if preferred_used:
                    score += 0.1
                else:
                    score -= 0.05
        
        return max(0.0, min(1.0, score))
    
    def _validate_content_appropriateness(self, content: str, content_type: ContentType) -> float:
        """Validate content appropriateness for the brand"""
        score = 0.8  # Start with good score
        
        # Check for inappropriate content
        inappropriate_patterns = [
            r'click here', r'buy now', r'limited time', r'act fast',
            r'guaranteed', r'miracle', r'secret', r'hack'
        ]
        
        for pattern in inappropriate_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                score -= 0.1
        
        # Check for overly promotional language
        promotional_words = ['sale', 'discount', 'deal', 'offer', 'promotion']
        promotional_count = sum(1 for word in promotional_words if word in content)
        
        if promotional_count > 2:  # Too promotional
            score -= 0.2
        
        # Content type specific checks
        if content_type == ContentType.NEWSLETTER_ARTICLE:
            # Should be informative, not salesy
            if 'subscribe' in content and content.count('subscribe') > 1:
                score -= 0.1
        
        elif content_type == ContentType.INSTAGRAM_CAPTION:
            # Should have engaging elements
            if not re.search(r'[!?]', content):  # No excitement or questions
                score -= 0.1
        
        return max(0.0, min(1.0, score))
    
    def _check_brand_issues(self, content: str, content_type: ContentType) -> List[str]:
        """Check for specific brand guideline violations"""
        issues = []
        
        # Check for competitor mentions
        competitors = ['ada', 'tropica', 'dennerle', 'seachem']
        for competitor in competitors:
            if competitor in content and 'better than' in content:
                issues.append(f"Avoid direct negative comparisons with {competitor}")
        
        # Check for medical claims
        medical_patterns = [
            r'cure', r'treat', r'medicine', r'therapy', r'healing'
        ]
        for pattern in medical_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                issues.append("Avoid medical claims about aquarium products")
        
        # Check for absolute statements
        absolute_patterns = [
            r'always', r'never', r'100%', r'guaranteed', r'perfect'
        ]
        absolute_count = sum(
            1 for pattern in absolute_patterns 
            if re.search(pattern, content, re.IGNORECASE)
        )
        
        if absolute_count > 2:
            issues.append("Reduce use of absolute statements")
        
        # Content length appropriateness
        word_count = len(content.split())
        if content_type == ContentType.INSTAGRAM_CAPTION and word_count > 100:
            issues.append("Instagram caption may be too long for optimal engagement")
        
        return issues
    
    def _generate_brand_suggestions(
        self, 
        voice_scores: Dict[str, float], 
        terminology_score: float, 
        issues: List[str]
    ) -> List[str]:
        """Generate suggestions for brand improvement"""
        suggestions = []
        
        # Voice-specific suggestions
        for voice, score in voice_scores.items():
            if score < 0.6:
                if voice == "professional":
                    suggestions.append("Add more expert insights and proven techniques")
                elif voice == "educational":
                    suggestions.append("Include more learning opportunities and explanations")
                elif voice == "friendly":
                    suggestions.append("Use more inclusive language and community-focused terms")
                elif voice == "enthusiastic":
                    suggestions.append("Add more positive and inspiring language")
        
        # Terminology suggestions
        if terminology_score < 0.6:
            suggestions.append("Use preferred aquascaping terminology consistently")
        
        # General brand suggestions
        if not any("community" in s.lower() for s in suggestions):
            suggestions.append("Consider adding community-building elements")
        
        if issues:
            suggestions.append("Address brand guideline violations noted in issues")
        
        return suggestions