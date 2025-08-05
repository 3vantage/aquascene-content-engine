"""
Quality Validator

Validates generated content for accuracy, relevance, and quality
specific to aquascaping topics and audience needs.
"""

import re
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import asyncio
import structlog

from ..llm_clients.base_client import ContentType
from ..knowledge.aquascaping_kb import AquascapingKnowledgeBase
from .brand_validator import BrandValidator
from .fact_checker import FactChecker
from .readability_checker import ReadabilityChecker

logger = structlog.get_logger()


class ValidationResult(Enum):
    """Validation result levels"""
    EXCELLENT = "excellent"      # 90-100%
    GOOD = "good"               # 75-89%
    ACCEPTABLE = "acceptable"   # 60-74%
    NEEDS_IMPROVEMENT = "needs_improvement"  # 40-59%
    POOR = "poor"              # 0-39%


@dataclass
class ValidationScore:
    """Individual validation component score"""
    component: str
    score: float  # 0.0 to 1.0
    details: Dict[str, Any] = field(default_factory=dict)
    issues: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)


@dataclass
class QualityReport:
    """Comprehensive quality validation report"""
    overall_score: float
    overall_result: ValidationResult
    component_scores: Dict[str, ValidationScore] = field(default_factory=dict)
    content_type: Optional[ContentType] = None
    word_count: int = 0
    character_count: int = 0
    
    # Detailed analysis
    strengths: List[str] = field(default_factory=list)
    weaknesses: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    
    # Content-specific metrics
    aquascaping_accuracy: Optional[float] = None
    brand_consistency: Optional[float] = None
    readability_score: Optional[float] = None
    seo_optimization: Optional[float] = None
    engagement_potential: Optional[float] = None


class QualityValidator:
    """Main quality validation coordinator"""
    
    def __init__(
        self,
        knowledge_base: AquascapingKnowledgeBase,
        brand_validator: Optional[BrandValidator] = None,
        fact_checker: Optional[FactChecker] = None,
        readability_checker: Optional[ReadabilityChecker] = None
    ):
        self.knowledge_base = knowledge_base
        self.brand_validator = brand_validator or BrandValidator()
        self.fact_checker = fact_checker or FactChecker(knowledge_base)
        self.readability_checker = readability_checker or ReadabilityChecker()
        
        # Validation weights by content type
        self.validation_weights = {
            ContentType.NEWSLETTER_ARTICLE: {
                "accuracy": 0.25,
                "readability": 0.20,
                "brand_consistency": 0.20,
                "structure": 0.15,
                "engagement": 0.20
            },
            ContentType.INSTAGRAM_CAPTION: {
                "brand_consistency": 0.30,
                "engagement": 0.30,
                "accuracy": 0.20,
                "hashtag_quality": 0.20
            },
            ContentType.HOW_TO_GUIDE: {
                "accuracy": 0.35,
                "structure": 0.25,
                "clarity": 0.25,
                "completeness": 0.15
            },
            ContentType.PRODUCT_REVIEW: {
                "accuracy": 0.30,
                "objectivity": 0.25,
                "completeness": 0.25,
                "brand_consistency": 0.20
            },
            ContentType.SEO_BLOG_POST: {
                "seo_optimization": 0.25,
                "accuracy": 0.25,
                "readability": 0.20,
                "structure": 0.15,
                "engagement": 0.15
            }
        }
        
        # Quality thresholds
        self.quality_thresholds = {
            ValidationResult.EXCELLENT: 0.90,
            ValidationResult.GOOD: 0.75,
            ValidationResult.ACCEPTABLE: 0.60,
            ValidationResult.NEEDS_IMPROVEMENT: 0.40,
            ValidationResult.POOR: 0.0
        }
    
    async def validate_content(
        self,
        content: str,
        content_type: ContentType,
        topic: str,
        requirements: Dict[str, Any] = None
    ) -> QualityReport:
        """Comprehensive content quality validation"""
        logger.info(
            "Starting content validation",
            content_type=content_type.value,
            topic=topic,
            content_length=len(content)
        )
        
        requirements = requirements or {}
        
        # Initialize report
        report = QualityReport(
            overall_score=0.0,
            overall_result=ValidationResult.POOR,
            content_type=content_type,
            word_count=len(content.split()),
            character_count=len(content)
        )
        
        # Get validation weights for this content type
        weights = self.validation_weights.get(content_type, {
            "accuracy": 0.25,
            "readability": 0.25,
            "brand_consistency": 0.25,
            "structure": 0.25
        })
        
        # Run validation components in parallel
        validation_tasks = [
            self._validate_accuracy(content, topic, content_type),
            self._validate_readability(content, content_type),
            self._validate_brand_consistency(content, content_type),
            self._validate_structure(content, content_type, requirements),
            self._validate_engagement_potential(content, content_type),
            self._validate_seo_optimization(content, requirements.get('seo_keywords', [])),
            self._validate_content_type_specific(content, content_type, requirements)
        ]
        
        validation_results = await asyncio.gather(*validation_tasks)
        
        # Process validation results
        component_scores = {}
        for result in validation_results:
            if result:
                component_scores[result.component] = result
                report.component_scores[result.component] = result
        
        # Calculate weighted overall score
        total_weight = 0
        weighted_score = 0
        
        for component, weight in weights.items():
            if component in component_scores:
                score = component_scores[component].score
                weighted_score += score * weight
                total_weight += weight
        
        # Handle unweighted components
        remaining_components = [
            comp for comp in component_scores.keys() 
            if comp not in weights
        ]
        
        if remaining_components and total_weight < 1.0:
            remaining_weight = (1.0 - total_weight) / len(remaining_components)
            for component in remaining_components:
                score = component_scores[component].score
                weighted_score += score * remaining_weight
                total_weight += remaining_weight
        
        report.overall_score = weighted_score if total_weight > 0 else 0.0
        report.overall_result = self._determine_quality_level(report.overall_score)
        
        # Set specific metrics
        report.aquascaping_accuracy = component_scores.get('accuracy', ValidationScore('accuracy', 0.0)).score
        report.brand_consistency = component_scores.get('brand_consistency', ValidationScore('brand_consistency', 0.0)).score
        report.readability_score = component_scores.get('readability', ValidationScore('readability', 0.0)).score
        report.seo_optimization = component_scores.get('seo_optimization', ValidationScore('seo_optimization', 0.0)).score
        report.engagement_potential = component_scores.get('engagement', ValidationScore('engagement', 0.0)).score
        
        # Generate summary insights
        await self._generate_summary_insights(report)
        
        logger.info(
            "Content validation completed",
            overall_score=report.overall_score,
            result=report.overall_result.value,
            component_count=len(report.component_scores)
        )
        
        return report
    
    async def _validate_accuracy(self, content: str, topic: str, content_type: ContentType) -> ValidationScore:
        """Validate factual accuracy and aquascaping knowledge"""
        score_components = []
        issues = []
        suggestions = []
        
        # Use fact checker for detailed accuracy validation
        fact_check_result = await self.fact_checker.check_facts(content, topic)
        accuracy_score = fact_check_result.get('accuracy_score', 0.5)
        
        if fact_check_result.get('issues'):
            issues.extend(fact_check_result['issues'])
        
        if fact_check_result.get('suggestions'):
            suggestions.extend(fact_check_result['suggestions'])
        
        # Check for aquascaping-specific accuracy
        aquascaping_score = await self._check_aquascaping_accuracy(content, topic)
        
        # Combine scores
        final_score = (accuracy_score + aquascaping_score) / 2
        
        return ValidationScore(
            component="accuracy",
            score=final_score,
            details={
                "fact_check_score": accuracy_score,
                "aquascaping_accuracy": aquascaping_score,
                "topic_relevance": self._calculate_topic_relevance(content, topic)
            },
            issues=issues,
            suggestions=suggestions
        )
    
    async def _check_aquascaping_accuracy(self, content: str, topic: str) -> float:
        """Check accuracy of aquascaping-specific information"""
        content_lower = content.lower()
        topic_lower = topic.lower()
        accuracy_points = 0
        total_checks = 0
        
        # Check plant information accuracy
        for plant_name, plant in self.knowledge_base.plants.items():
            if plant_name in content_lower or plant.scientific_name.lower() in content_lower:
                total_checks += 1
                
                # Check if care requirements are mentioned correctly
                if plant.difficulty.value in content_lower:
                    accuracy_points += 0.5
                
                if plant.light_requirement in content_lower or "light" in content_lower:
                    # Simple heuristic - more sophisticated checking could be added
                    accuracy_points += 0.5
        
        # Check equipment mentions
        for equipment_name, equipment in self.knowledge_base.equipment.items():
            if equipment_name in content_lower or equipment.brand.lower() in content_lower:
                total_checks += 1
                accuracy_points += 0.7  # Assume mostly accurate for equipment mentions
        
        # Check for common misconceptions or errors
        error_patterns = [
            (r"bury.*anubias.*rhizome", "Anubias rhizome should not be buried"),
            (r"high.*light.*anubias", "Anubias prefers low to medium light"),
            (r"co2.*required.*anubias", "Anubias does not require CO2"),
        ]
        
        for pattern, issue in error_patterns:
            if re.search(pattern, content_lower):
                total_checks += 1
                accuracy_points -= 0.3  # Penalty for misinformation
        
        # Return score based on checks performed
        if total_checks == 0:
            return 0.7  # Neutral score if no specific checks possible
        
        return max(0.0, min(1.0, accuracy_points / total_checks))
    
    def _calculate_topic_relevance(self, content: str, topic: str) -> float:
        """Calculate how relevant the content is to the topic"""
        topic_words = set(topic.lower().split())
        content_words = set(content.lower().split())
        
        # Calculate overlap
        overlap = len(topic_words.intersection(content_words))
        relevance = overlap / len(topic_words) if topic_words else 0.0
        
        return min(1.0, relevance)
    
    async def _validate_readability(self, content: str, content_type: ContentType) -> ValidationScore:
        """Validate content readability and clarity"""
        readability_result = await self.readability_checker.analyze_readability(content)
        
        # Content-type specific readability expectations
        readability_targets = {
            ContentType.NEWSLETTER_ARTICLE: {"min_grade": 8, "max_grade": 12},
            ContentType.INSTAGRAM_CAPTION: {"min_grade": 6, "max_grade": 10},
            ContentType.HOW_TO_GUIDE: {"min_grade": 7, "max_grade": 11},
            ContentType.PRODUCT_REVIEW: {"min_grade": 8, "max_grade": 12},
            ContentType.SEO_BLOG_POST: {"min_grade": 8, "max_grade": 12}
        }
        
        target = readability_targets.get(content_type, {"min_grade": 8, "max_grade": 12})
        grade_level = readability_result.get('grade_level', 10)
        
        # Score based on whether grade level is in target range
        if target['min_grade'] <= grade_level <= target['max_grade']:
            grade_score = 1.0
        else:
            # Penalty for being outside target range
            distance = min(
                abs(grade_level - target['min_grade']),
                abs(grade_level - target['max_grade'])
            )
            grade_score = max(0.0, 1.0 - (distance * 0.1))
        
        # Combine with other readability metrics
        sentence_score = readability_result.get('sentence_score', 0.7)
        vocabulary_score = readability_result.get('vocabulary_score', 0.7)
        
        final_score = (grade_score + sentence_score + vocabulary_score) / 3
        
        issues = readability_result.get('issues', [])
        suggestions = readability_result.get('suggestions', [])
        
        return ValidationScore(
            component="readability",
            score=final_score,
            details={
                "grade_level": grade_level,
                "target_range": f"{target['min_grade']}-{target['max_grade']}",
                "sentence_score": sentence_score,
                "vocabulary_score": vocabulary_score
            },
            issues=issues,
            suggestions=suggestions
        )
    
    async def _validate_brand_consistency(self, content: str, content_type: ContentType) -> ValidationScore:
        """Validate brand voice and consistency"""
        brand_result = await self.brand_validator.validate_brand_voice(content, content_type)
        
        return ValidationScore(
            component="brand_consistency",
            score=brand_result.get('score', 0.7),
            details=brand_result.get('details', {}),
            issues=brand_result.get('issues', []),
            suggestions=brand_result.get('suggestions', [])
        )
    
    async def _validate_structure(self, content: str, content_type: ContentType, requirements: Dict[str, Any]) -> ValidationScore:
        """Validate content structure and formatting"""
        structure_score = 0.0
        issues = []
        suggestions = []
        details = {}
        
        # Content type specific structure validation
        if content_type == ContentType.NEWSLETTER_ARTICLE:
            structure_score = self._validate_newsletter_structure(content)
        elif content_type == ContentType.INSTAGRAM_CAPTION:
            structure_score = self._validate_instagram_structure(content)
        elif content_type == ContentType.HOW_TO_GUIDE:
            structure_score = self._validate_howto_structure(content)
        elif content_type == ContentType.PRODUCT_REVIEW:
            structure_score = self._validate_review_structure(content)
        else:
            structure_score = self._validate_generic_structure(content)
        
        # Check length requirements
        if 'min_length' in requirements:
            min_length = requirements['min_length']
            if len(content) < min_length:
                issues.append(f"Content is shorter than required minimum of {min_length} characters")
                structure_score *= 0.8
        
        if 'max_length' in requirements:
            max_length = requirements['max_length']
            if len(content) > max_length:
                issues.append(f"Content exceeds maximum length of {max_length} characters")
                structure_score *= 0.9
        
        return ValidationScore(
            component="structure",
            score=structure_score,
            details=details,
            issues=issues,
            suggestions=suggestions
        )
    
    def _validate_newsletter_structure(self, content: str) -> float:
        """Validate newsletter article structure"""
        score = 0.0
        
        # Check for key components
        has_hook = bool(re.search(r'^.{1,200}', content, re.MULTILINE))  # Opening hook
        has_body = len(content.split('\n\n')) >= 2  # Multiple paragraphs
        has_conclusion = 'conclusion' in content.lower() or content.endswith('.')
        
        if has_hook:
            score += 0.4
        if has_body:
            score += 0.4
        if has_conclusion:
            score += 0.2
        
        return score
    
    def _validate_instagram_structure(self, content: str) -> float:
        """Validate Instagram caption structure"""
        score = 0.0
        
        # Check for hashtags
        hashtag_count = len(re.findall(r'#\w+', content))
        if 5 <= hashtag_count <= 15:  # Optimal hashtag range
            score += 0.4
        elif hashtag_count > 0:
            score += 0.2
        
        # Check for call to action
        cta_patterns = [r'comment', r'like', r'share', r'follow', r'tag', r'what.*think']
        has_cta = any(re.search(pattern, content.lower()) for pattern in cta_patterns)
        if has_cta:
            score += 0.3
        
        # Check length (Instagram captions should be concise but engaging)
        if 50 <= len(content) <= 300:
            score += 0.3
        elif len(content) <= 500:
            score += 0.2
        
        return score
    
    def _validate_howto_structure(self, content: str) -> float:
        """Validate how-to guide structure"""
        score = 0.0
        
        # Check for numbered steps or bullet points
        has_steps = bool(re.search(r'^\d+\.|\*|-', content, re.MULTILINE))
        if has_steps:
            score += 0.4
        
        # Check for materials/requirements section
        has_materials = any(word in content.lower() for word in ['materials', 'requirements', 'needed', 'tools'])
        if has_materials:
            score += 0.3
        
        # Check for clear structure
        sections = len(content.split('\n\n'))
        if sections >= 3:  # Introduction, steps, conclusion
            score += 0.3
        
        return score
    
    def _validate_review_structure(self, content: str) -> float:
        """Validate product review structure"""
        score = 0.0
        
        # Check for pros/cons or similar evaluation
        has_evaluation = any(word in content.lower() for word in ['pros', 'cons', 'advantages', 'disadvantages', 'rating'])
        if has_evaluation:
            score += 0.4
        
        # Check for specific details
        has_details = any(word in content.lower() for word in ['price', 'features', 'specifications', 'performance'])
        if has_details:
            score += 0.3
        
        # Check for recommendation
        has_recommendation = any(word in content.lower() for word in ['recommend', 'suggest', 'worth', 'conclusion'])
        if has_recommendation:
            score += 0.3
        
        return score
    
    def _validate_generic_structure(self, content: str) -> float:
        """Validate generic content structure"""
        score = 0.0
        
        # Check for paragraphs
        paragraphs = len(content.split('\n\n'))
        if paragraphs >= 2:
            score += 0.5
        
        # Check for variety in sentence length
        sentences = re.split(r'[.!?]+', content)
        if len(sentences) >= 3:
            lengths = [len(s.split()) for s in sentences if s.strip()]
            if lengths and max(lengths) - min(lengths) > 5:  # Variety in sentence length
                score += 0.5
        
        return score
    
    async def _validate_engagement_potential(self, content: str, content_type: ContentType) -> ValidationScore:
        """Validate potential for audience engagement"""
        engagement_score = 0.0
        details = {}
        
        # Check for engaging elements
        has_questions = bool(re.search(r'\?', content))
        has_personal_touch = any(word in content.lower() for word in ['you', 'your', 'we', 'our', 'i'])
        has_action_words = any(word in content.lower() for word in ['discover', 'learn', 'try', 'create', 'build'])
        has_emotional_words = any(word in content.lower() for word in ['beautiful', 'stunning', 'amazing', 'love', 'enjoy'])
        
        if has_questions:
            engagement_score += 0.25
        if has_personal_touch:
            engagement_score += 0.25
        if has_action_words:
            engagement_score += 0.25
        if has_emotional_words:
            engagement_score += 0.25
        
        details = {
            "has_questions": has_questions,
            "has_personal_touch": has_personal_touch,
            "has_action_words": has_action_words,
            "has_emotional_words": has_emotional_words
        }
        
        return ValidationScore(
            component="engagement",
            score=engagement_score,
            details=details,
            issues=[],
            suggestions=[]
        )
    
    async def _validate_seo_optimization(self, content: str, keywords: List[str]) -> ValidationScore:
        """Validate SEO optimization"""
        if not keywords:
            return ValidationScore(
                component="seo_optimization",
                score=0.5,  # Neutral score if no keywords provided
                details={"keywords_provided": False},
                issues=[],
                suggestions=["Provide SEO keywords for optimization"]
            )
        
        content_lower = content.lower()
        seo_score = 0.0
        used_keywords = []
        
        # Check keyword usage
        for keyword in keywords:
            if keyword.lower() in content_lower:
                used_keywords.append(keyword)
        
        keyword_usage_score = len(used_keywords) / len(keywords) if keywords else 0
        seo_score += keyword_usage_score * 0.6
        
        # Check keyword density (should be natural, not stuffed)
        total_words = len(content.split())
        keyword_density = sum(content_lower.count(kw.lower()) for kw in keywords) / total_words if total_words > 0 else 0
        
        if 0.01 <= keyword_density <= 0.03:  # 1-3% is generally good
            seo_score += 0.4
        elif keyword_density > 0:
            seo_score += 0.2
        
        return ValidationScore(
            component="seo_optimization",
            score=seo_score,
            details={
                "keyword_usage_score": keyword_usage_score,
                "used_keywords": used_keywords,
                "keyword_density": keyword_density,
                "total_keywords": len(keywords)
            },
            issues=[],
            suggestions=[]
        )
    
    async def _validate_content_type_specific(self, content: str, content_type: ContentType, requirements: Dict[str, Any]) -> Optional[ValidationScore]:
        """Content type specific validation"""
        if content_type == ContentType.INSTAGRAM_CAPTION:
            return await self._validate_instagram_specific(content)
        elif content_type == ContentType.HOW_TO_GUIDE:
            return await self._validate_howto_specific(content)
        # Add more content type specific validations as needed
        return None
    
    async def _validate_instagram_specific(self, content: str) -> ValidationScore:
        """Instagram-specific validation"""
        score = 0.0
        issues = []
        suggestions = []
        
        # Check hashtag quality
        hashtags = re.findall(r'#(\w+)', content)
        aquascaping_hashtags = [
            'aquascape', 'plantedtank', 'aquascaping', 'aquaticplants',
            'freshwateraquarium', 'natureaquarium', 'plantedaquarium'
        ]
        
        relevant_hashtags = [h for h in hashtags if h.lower() in aquascaping_hashtags]
        if relevant_hashtags:
            score += 0.5
        else:
            suggestions.append("Add relevant aquascaping hashtags")
        
        # Check for visual references
        visual_words = ['see', 'look', 'picture', 'image', 'photo', 'beautiful', 'stunning']
        has_visual_reference = any(word in content.lower() for word in visual_words)
        if has_visual_reference:
            score += 0.5
        else:
            suggestions.append("Add visual references to complement the image")
        
        return ValidationScore(
            component="instagram_specific",
            score=score,
            details={
                "hashtag_count": len(hashtags),
                "relevant_hashtags": len(relevant_hashtags),
                "has_visual_reference": has_visual_reference
            },
            issues=issues,
            suggestions=suggestions
        )
    
    async def _validate_howto_specific(self, content: str) -> ValidationScore:
        """How-to guide specific validation"""
        score = 0.0
        issues = []
        suggestions = []
        
        # Check for clear step-by-step structure
        step_patterns = [r'step \d+', r'^\d+\.', r'first', r'then', r'next', r'finally']
        step_indicators = sum(1 for pattern in step_patterns if re.search(pattern, content.lower()))
        
        if step_indicators >= 3:
            score += 0.5
        elif step_indicators > 0:
            score += 0.3
        else:
            issues.append("Lacks clear step-by-step structure")
        
        # Check for actionable language
        action_verbs = ['add', 'remove', 'place', 'cut', 'trim', 'plant', 'fill', 'adjust', 'wait', 'check']
        action_count = sum(1 for verb in action_verbs if verb in content.lower())
        
        if action_count >= 5:
            score += 0.5
        elif action_count > 0:
            score += 0.3
        else:
            suggestions.append("Use more actionable language with clear instructions")
        
        return ValidationScore(
            component="howto_specific",
            score=score,
            details={
                "step_indicators": step_indicators,
                "action_verbs_count": action_count
            },
            issues=issues,
            suggestions=suggestions
        )
    
    def _determine_quality_level(self, score: float) -> ValidationResult:
        """Determine quality level based on score"""
        for level, threshold in self.quality_thresholds.items():
            if score >= threshold:
                return level
        return ValidationResult.POOR
    
    async def _generate_summary_insights(self, report: QualityReport) -> None:
        """Generate summary insights for the quality report"""
        # Identify strengths
        strong_components = [
            comp for comp, score in report.component_scores.items()
            if score.score >= 0.8
        ]
        
        if strong_components:
            report.strengths.append(f"Strong performance in: {', '.join(strong_components)}")
        
        # Identify weaknesses
        weak_components = [
            comp for comp, score in report.component_scores.items()
            if score.score < 0.6
        ]
        
        if weak_components:
            report.weaknesses.append(f"Needs improvement in: {', '.join(weak_components)}")
        
        # Generate recommendations
        if report.overall_score < 0.7:
            report.recommendations.append("Consider regenerating content with more specific requirements")
        
        if report.aquascaping_accuracy and report.aquascaping_accuracy < 0.7:
            report.recommendations.append("Review aquascaping facts and ensure accuracy")
        
        if report.readability_score and report.readability_score < 0.7:
            report.recommendations.append("Simplify language and improve readability")
        
        if report.engagement_potential and report.engagement_potential < 0.6:
            report.recommendations.append("Add more engaging elements like questions or personal touches")