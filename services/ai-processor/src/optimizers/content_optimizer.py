"""
Content Optimizer

Main content optimization coordinator that applies various optimization
strategies for SEO, engagement, and performance.
"""

import re
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import asyncio
import structlog

from ..llm_clients.base_client import ContentType
from .seo_optimizer import SEOOptimizer
from .engagement_optimizer import EngagementOptimizer
from .social_optimizer import SocialOptimizer

logger = structlog.get_logger()


class OptimizationStrategy(Enum):
    """Content optimization strategies"""
    SEO_FOCUSED = "seo_focused"
    ENGAGEMENT_FOCUSED = "engagement_focused"
    SOCIAL_FOCUSED = "social_focused"
    BALANCED = "balanced"
    CONVERSION_FOCUSED = "conversion_focused"


@dataclass
class OptimizationResult:
    """Result of content optimization"""
    original_content: str
    optimized_content: Optional[str] = None
    strategy_used: Optional[OptimizationStrategy] = None
    optimizations_applied: List[str] = field(default_factory=list)
    scores: Dict[str, float] = field(default_factory=dict)
    suggestions: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class ContentOptimizer:
    """Main content optimization engine"""
    
    def __init__(self):
        self.seo_optimizer = SEOOptimizer()
        self.engagement_optimizer = EngagementOptimizer()
        self.social_optimizer = SocialOptimizer()
        
        # Optimization weights by content type
        self.optimization_weights = {
            ContentType.NEWSLETTER_ARTICLE: {
                OptimizationStrategy.SEO_FOCUSED: {"seo": 0.6, "engagement": 0.25, "social": 0.15},
                OptimizationStrategy.ENGAGEMENT_FOCUSED: {"engagement": 0.6, "seo": 0.25, "social": 0.15},
                OptimizationStrategy.BALANCED: {"seo": 0.4, "engagement": 0.4, "social": 0.2}
            },
            ContentType.INSTAGRAM_CAPTION: {
                OptimizationStrategy.SOCIAL_FOCUSED: {"social": 0.7, "engagement": 0.25, "seo": 0.05},
                OptimizationStrategy.ENGAGEMENT_FOCUSED: {"engagement": 0.6, "social": 0.35, "seo": 0.05},
                OptimizationStrategy.BALANCED: {"social": 0.5, "engagement": 0.4, "seo": 0.1}
            },
            ContentType.SEO_BLOG_POST: {
                OptimizationStrategy.SEO_FOCUSED: {"seo": 0.7, "engagement": 0.2, "social": 0.1},
                OptimizationStrategy.BALANCED: {"seo": 0.5, "engagement": 0.35, "social": 0.15}
            },
            ContentType.HOW_TO_GUIDE: {
                OptimizationStrategy.SEO_FOCUSED: {"seo": 0.5, "engagement": 0.35, "social": 0.15},
                OptimizationStrategy.ENGAGEMENT_FOCUSED: {"engagement": 0.55, "seo": 0.3, "social": 0.15},
                OptimizationStrategy.BALANCED: {"seo": 0.4, "engagement": 0.45, "social": 0.15}
            }
        }
        
        # Content type specific optimization rules
        self.content_rules = {
            ContentType.NEWSLETTER_ARTICLE: {
                "max_length": 2500,
                "min_length": 300,
                "paragraph_max_sentences": 4,
                "require_cta": True,
                "heading_structure": True
            },
            ContentType.INSTAGRAM_CAPTION: {
                "max_length": 300,
                "min_length": 50,
                "hashtag_range": (5, 15),
                "require_cta": True,
                "emoji_friendly": True
            },
            ContentType.HOW_TO_GUIDE: {
                "max_length": 3000,
                "min_length": 500,
                "require_steps": True,
                "require_materials": True,
                "clear_structure": True
            }
        }
    
    async def optimize_content(
        self,
        content: str,
        content_type: ContentType,
        seo_keywords: List[str] = None,
        target_audience: str = None,
        optimization_strategy: OptimizationStrategy = OptimizationStrategy.BALANCED,
        **kwargs
    ) -> OptimizationResult:
        """Optimize content using specified strategy"""
        logger.info(
            "Starting content optimization",
            content_type=content_type.value,
            strategy=optimization_strategy.value,
            content_length=len(content)
        )
        
        result = OptimizationResult(
            original_content=content,
            strategy_used=optimization_strategy
        )
        
        # Get optimization weights for this content type and strategy
        weights = self._get_optimization_weights(content_type, optimization_strategy)
        
        # Run optimization components in parallel
        optimization_tasks = []
        
        if weights.get("seo", 0) > 0:
            optimization_tasks.append(
                self._apply_seo_optimization(content, content_type, seo_keywords or [])
            )
        
        if weights.get("engagement", 0) > 0:
            optimization_tasks.append(
                self._apply_engagement_optimization(content, content_type, target_audience)
            )
        
        if weights.get("social", 0) > 0:
            optimization_tasks.append(
                self._apply_social_optimization(content, content_type)
            )
        
        # Execute optimizations
        optimization_results = await asyncio.gather(*optimization_tasks, return_exceptions=True)
        
        # Process optimization results
        optimized_content = content
        applied_optimizations = []
        scores = {}
        suggestions = []
        warnings = []
        
        for opt_result in optimization_results:
            if isinstance(opt_result, Exception):
                warnings.append(f"Optimization error: {str(opt_result)}")
                continue
            
            if opt_result and isinstance(opt_result, dict):
                # Apply optimization if it improves the content
                if opt_result.get("optimized_content") and opt_result.get("improvement_score", 0) > 0.1:
                    optimized_content = opt_result["optimized_content"]
                    applied_optimizations.append(opt_result.get("optimization_type", "unknown"))
                
                # Collect scores and suggestions
                if "scores" in opt_result:
                    scores.update(opt_result["scores"])
                
                if "suggestions" in opt_result:
                    suggestions.extend(opt_result["suggestions"])
                
                if "warnings" in opt_result:
                    warnings.extend(opt_result["warnings"])
        
        # Apply content-type specific rules
        optimized_content, rule_optimizations = await self._apply_content_rules(
            optimized_content, content_type
        )
        applied_optimizations.extend(rule_optimizations)
        
        # Final quality check
        final_score = await self._calculate_final_score(
            optimized_content, content_type, scores, weights
        )
        
        result.optimized_content = optimized_content
        result.optimizations_applied = applied_optimizations
        result.scores = {**scores, "final_score": final_score}
        result.suggestions = suggestions
        result.warnings = warnings
        result.metadata = {
            "content_improved": optimized_content != content,
            "improvement_areas": applied_optimizations,
            "optimization_weights": weights
        }
        
        logger.info(
            "Content optimization completed",
            optimizations_applied=len(applied_optimizations),
            final_score=final_score,
            content_improved=result.metadata["content_improved"]
        )
        
        return result
    
    def _get_optimization_weights(
        self,
        content_type: ContentType,
        strategy: OptimizationStrategy
    ) -> Dict[str, float]:
        """Get optimization weights for content type and strategy"""
        type_weights = self.optimization_weights.get(content_type, {})
        return type_weights.get(strategy, {"seo": 0.33, "engagement": 0.33, "social": 0.34})
    
    async def _apply_seo_optimization(
        self,
        content: str,
        content_type: ContentType,
        keywords: List[str]
    ) -> Dict[str, Any]:
        """Apply SEO optimization"""
        try:
            return await self.seo_optimizer.optimize(content, content_type, keywords)
        except Exception as e:
            logger.error("SEO optimization failed", error=str(e))
            return {"optimization_type": "seo", "error": str(e)}
    
    async def _apply_engagement_optimization(
        self,
        content: str,
        content_type: ContentType,
        target_audience: Optional[str]
    ) -> Dict[str, Any]:
        """Apply engagement optimization"""
        try:
            return await self.engagement_optimizer.optimize(content, content_type, target_audience)
        except Exception as e:
            logger.error("Engagement optimization failed", error=str(e))
            return {"optimization_type": "engagement", "error": str(e)}
    
    async def _apply_social_optimization(
        self,
        content: str,
        content_type: ContentType
    ) -> Dict[str, Any]:
        """Apply social media optimization"""
        try:
            return await self.social_optimizer.optimize(content, content_type)
        except Exception as e:
            logger.error("Social optimization failed", error=str(e))
            return {"optimization_type": "social", "error": str(e)}
    
    async def _apply_content_rules(
        self,
        content: str,
        content_type: ContentType
    ) -> Tuple[str, List[str]]:
        """Apply content-type specific rules and constraints"""
        rules = self.content_rules.get(content_type, {})
        optimized_content = content
        applied_rules = []
        
        # Length constraints
        if "max_length" in rules and len(content) > rules["max_length"]:
            # Truncate content intelligently (at sentence boundaries)
            sentences = re.split(r'[.!?]+', content)
            truncated = ""
            for sentence in sentences:
                if len(truncated + sentence) <= rules["max_length"]:
                    truncated += sentence + "."
                else:
                    break
            optimized_content = truncated.strip()
            applied_rules.append("length_truncation")
        
        # Paragraph structure for articles
        if rules.get("paragraph_max_sentences") and content_type in [
            ContentType.NEWSLETTER_ARTICLE, ContentType.SEO_BLOG_POST
        ]:
            optimized_content = self._optimize_paragraph_structure(
                optimized_content, rules["paragraph_max_sentences"]
            )
            applied_rules.append("paragraph_optimization")
        
        # Call-to-action requirement
        if rules.get("require_cta"):
            if not self._has_call_to_action(optimized_content):
                cta = self._generate_cta(content_type)
                optimized_content += f"\n\n{cta}"
                applied_rules.append("cta_addition")
        
        # Instagram specific rules
        if content_type == ContentType.INSTAGRAM_CAPTION:
            if rules.get("hashtag_range"):
                optimized_content = self._optimize_hashtags(
                    optimized_content, rules["hashtag_range"]
                )
                applied_rules.append("hashtag_optimization")
        
        # How-to guide specific rules
        if content_type == ContentType.HOW_TO_GUIDE:
            if rules.get("require_steps") and not self._has_step_structure(optimized_content):
                optimized_content = self._add_step_structure(optimized_content)
                applied_rules.append("step_structure_addition")
        
        return optimized_content, applied_rules
    
    def _optimize_paragraph_structure(self, content: str, max_sentences: int) -> str:
        """Optimize paragraph structure by limiting sentences per paragraph"""
        paragraphs = content.split('\n\n')
        optimized_paragraphs = []
        
        for paragraph in paragraphs:
            sentences = re.split(r'[.!?]+', paragraph)
            sentences = [s.strip() for s in sentences if s.strip()]
            
            if len(sentences) > max_sentences:
                # Split into multiple paragraphs
                for i in range(0, len(sentences), max_sentences):
                    chunk = sentences[i:i + max_sentences]
                    optimized_paragraphs.append('. '.join(chunk) + '.')
            else:
                optimized_paragraphs.append(paragraph)
        
        return '\n\n'.join(optimized_paragraphs)
    
    def _has_call_to_action(self, content: str) -> bool:
        """Check if content has a call-to-action"""
        cta_patterns = [
            r'share.*thoughts', r'comment.*below', r'let.*know', r'follow.*for',
            r'subscribe', r'visit.*website', r'check.*out', r'learn.*more',
            r'try.*this', r'give.*try', r'what.*think'
        ]
        
        content_lower = content.lower()
        return any(re.search(pattern, content_lower) for pattern in cta_patterns)
    
    def _generate_cta(self, content_type: ContentType) -> str:
        """Generate appropriate call-to-action for content type"""
        ctas = {
            ContentType.NEWSLETTER_ARTICLE: "What's your experience with this technique? Share your thoughts in our community!",
            ContentType.INSTAGRAM_CAPTION: "What do you think? Share your aquascaping journey in the comments! 👇",
            ContentType.HOW_TO_GUIDE: "Try this technique in your own aquarium and let us know how it goes!",
            ContentType.PRODUCT_REVIEW: "Have you tried this product? Share your experience in the comments!",
            ContentType.SEO_BLOG_POST: "Want to learn more aquascaping techniques? Subscribe to our newsletter for weekly tips!"
        }
        
        return ctas.get(content_type, "Share your thoughts and experiences with the community!")
    
    def _optimize_hashtags(self, content: str, hashtag_range: Tuple[int, int]) -> str:
        """Optimize hashtag count and quality"""
        min_tags, max_tags = hashtag_range
        
        # Extract existing hashtags
        existing_hashtags = re.findall(r'#\w+', content)
        content_without_hashtags = re.sub(r'#\w+\s*', '', content).strip()
        
        # Aquascaping-relevant hashtags
        recommended_hashtags = [
            '#aquascape', '#plantedtank', '#aquascaping', '#aquaticplants',
            '#freshwateraquarium', '#natureaquarium', '#plantedaquarium',
            '#aquariumhobby', '#fishkeeping', '#aquadesign'
        ]
        
        # Filter out hashtags already in content
        existing_tags_lower = [tag.lower() for tag in existing_hashtags]
        new_hashtags = [
            tag for tag in recommended_hashtags
            if tag.lower() not in existing_tags_lower
        ]
        
        # Combine existing and new hashtags
        all_hashtags = existing_hashtags + new_hashtags
        
        # Limit to range
        if len(all_hashtags) > max_tags:
            final_hashtags = all_hashtags[:max_tags]
        elif len(all_hashtags) < min_tags:
            final_hashtags = all_hashtags + new_hashtags[:min_tags - len(all_hashtags)]
        else:
            final_hashtags = all_hashtags
        
        # Add hashtags to content
        if final_hashtags:
            return f"{content_without_hashtags}\n\n{' '.join(final_hashtags)}"
        
        return content
    
    def _has_step_structure(self, content: str) -> bool:
        """Check if content has a step-by-step structure"""
        step_patterns = [
            r'^\d+\.\s', r'^step\s+\d+', r'first.*second.*third',
            r'next.*then.*finally'
        ]
        
        return any(re.search(pattern, content.lower(), re.MULTILINE) for pattern in step_patterns)
    
    def _add_step_structure(self, content: str) -> str:
        """Add step structure to how-to content"""
        # This is a simplified implementation
        # In practice, this would use NLP to identify sequential actions
        paragraphs = content.split('\n\n')
        
        if len(paragraphs) >= 3:
            structured_content = []
            for i, paragraph in enumerate(paragraphs, 1):
                if i == 1:
                    structured_content.append(paragraph)  # Introduction
                elif i == len(paragraphs):
                    structured_content.append(paragraph)  # Conclusion
                else:
                    structured_content.append(f"Step {i-1}: {paragraph}")
            
            return '\n\n'.join(structured_content)
        
        return content
    
    async def _calculate_final_score(
        self,
        content: str,
        content_type: ContentType,
        component_scores: Dict[str, float],
        weights: Dict[str, float]
    ) -> float:
        """Calculate final optimization score"""
        weighted_score = 0.0
        total_weight = 0.0
        
        for component, weight in weights.items():
            if component in component_scores:
                weighted_score += component_scores[component] * weight
                total_weight += weight
        
        # Add base quality metrics
        base_score = self._calculate_base_quality_score(content, content_type)
        if total_weight > 0:
            final_score = (weighted_score / total_weight + base_score) / 2
        else:
            final_score = base_score
        
        return min(1.0, max(0.0, final_score))
    
    def _calculate_base_quality_score(self, content: str, content_type: ContentType) -> float:
        """Calculate base quality score based on content characteristics"""
        score = 0.0
        
        # Length appropriateness
        word_count = len(content.split())
        if content_type == ContentType.INSTAGRAM_CAPTION:
            if 10 <= word_count <= 50:
                score += 0.3
        elif content_type == ContentType.NEWSLETTER_ARTICLE:
            if 150 <= word_count <= 400:
                score += 0.3
        elif content_type == ContentType.HOW_TO_GUIDE:
            if 200 <= word_count <= 600:
                score += 0.3
        
        # Sentence variety
        sentences = re.split(r'[.!?]+', content)
        sentence_lengths = [len(s.split()) for s in sentences if s.strip()]
        if sentence_lengths:
            avg_length = sum(sentence_lengths) / len(sentence_lengths)
            if 10 <= avg_length <= 20:  # Good average sentence length
                score += 0.2
        
        # Readability indicators
        if not re.search(r'[^\w\s.!?,-]', content):  # Avoid complex punctuation
            score += 0.1
        
        # Aquascaping relevance
        aquascaping_terms = [
            'aquascape', 'plant', 'aquarium', 'tank', 'water', 'fish',
            'substrate', 'co2', 'light', 'fertilizer', 'trimming'
        ]
        
        content_lower = content.lower()
        relevant_terms = sum(1 for term in aquascaping_terms if term in content_lower)
        relevance_score = min(0.4, relevant_terms * 0.05)
        score += relevance_score
        
        return min(1.0, score)
    
    async def batch_optimize(
        self,
        content_list: List[Dict[str, Any]],
        max_concurrent: int = 5
    ) -> List[OptimizationResult]:
        """Optimize multiple pieces of content concurrently"""
        logger.info(f"Starting batch optimization of {len(content_list)} items")
        
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def optimize_single(item: Dict[str, Any]) -> OptimizationResult:
            async with semaphore:
                return await self.optimize_content(**item)
        
        tasks = [optimize_single(item) for item in content_list]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out exceptions and log errors
        successful_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Batch optimization item {i} failed", error=str(result))
            else:
                successful_results.append(result)
        
        logger.info(
            f"Batch optimization completed",
            total=len(content_list),
            successful=len(successful_results),
            failed=len(content_list) - len(successful_results)
        )
        
        return successful_results
    
    def get_optimization_suggestions(
        self,
        content: str,
        content_type: ContentType
    ) -> List[str]:
        """Get optimization suggestions without applying them"""
        suggestions = []
        
        # Length suggestions
        word_count = len(content.split())
        rules = self.content_rules.get(content_type, {})
        
        if "max_length" in rules and len(content) > rules["max_length"]:
            suggestions.append(f"Content exceeds recommended length of {rules['max_length']} characters")
        
        if "min_length" in rules and len(content) < rules["min_length"]:
            suggestions.append(f"Content is shorter than recommended minimum of {rules['min_length']} characters")
        
        # Structure suggestions
        if not self._has_call_to_action(content):
            suggestions.append("Consider adding a call-to-action to increase engagement")
        
        if content_type == ContentType.INSTAGRAM_CAPTION:
            hashtag_count = len(re.findall(r'#\w+', content))
            if hashtag_count < 5:
                suggestions.append("Add more relevant hashtags (5-15 recommended)")
            elif hashtag_count > 15:
                suggestions.append("Consider reducing hashtags (5-15 recommended)")
        
        # SEO suggestions
        if content_type in [ContentType.NEWSLETTER_ARTICLE, ContentType.SEO_BLOG_POST]:
            if not re.search(r'^.{1,60}', content):  # No clear title/heading
                suggestions.append("Consider adding a clear heading or title")
        
        return suggestions