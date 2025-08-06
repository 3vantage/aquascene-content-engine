"""
SEO Optimizer

Optimizes content for search engine visibility and ranking
with aquascaping-specific SEO strategies.
"""

import re
from typing import Dict, List, Optional, Any
import structlog

from ..llm_clients.base_client import ContentType

logger = structlog.get_logger()


class SEOOptimizer:
    """Optimizes content for search engine optimization"""
    
    def __init__(self):
        # Aquascaping-specific keywords and their variations
        self.keyword_variations = {
            "aquascaping": ["aquascaping", "aquascape", "aquascaped", "aquascaper"],
            "planted tank": ["planted tank", "planted aquarium", "plant tank", "aquatic plants"],
            "co2": ["co2", "carbon dioxide", "co2 injection", "co2 system"],
            "substrate": ["substrate", "aquasoil", "plant substrate", "aquarium soil"],
            "lighting": ["lighting", "aquarium light", "plant light", "led lighting"],
            "fertilizer": ["fertilizer", "plant fertilizer", "aquarium fertilizer", "liquid fertilizer"]
        }
        
        # SEO best practices for different content types
        self.seo_guidelines = {
            ContentType.NEWSLETTER_ARTICLE: {
                "title_length": (30, 60),
                "meta_description_length": (120, 160),
                "keyword_density": (0.01, 0.03),
                "heading_structure": True,
                "internal_links": True
            },
            ContentType.SEO_BLOG_POST: {
                "title_length": (30, 60),
                "meta_description_length": (120, 160),
                "keyword_density": (0.015, 0.025),
                "heading_structure": True,
                "word_count": (800, 2000)
            },
            ContentType.HOW_TO_GUIDE: {
                "title_length": (40, 70),
                "keyword_density": (0.01, 0.02),
                "heading_structure": True,
                "step_structure": True
            }
        }
    
    async def optimize(
        self,
        content: str,
        content_type: ContentType,
        keywords: List[str]
    ) -> Dict[str, Any]:
        """Optimize content for SEO"""
        
        result = {
            "optimization_type": "seo",
            "optimized_content": content,
            "improvement_score": 0.0,
            "scores": {},
            "suggestions": [],
            "warnings": []
        }
        
        if not keywords:
            result["warnings"].append("No SEO keywords provided")
            result["scores"]["seo_score"] = 0.5
            return result
        
        # Analyze current SEO state
        current_analysis = self._analyze_seo_state(content, keywords, content_type)
        
        # Optimize based on analysis
        optimized_content = await self._apply_seo_optimizations(
            content, keywords, content_type, current_analysis
        )
        
        # Calculate improvement
        if optimized_content != content:
            result["optimized_content"] = optimized_content
            result["improvement_score"] = self._calculate_improvement_score(
                current_analysis, keywords, content_type
            )
        
        # Generate SEO scores and suggestions
        result["scores"] = self._calculate_seo_scores(optimized_content, keywords, content_type)
        result["suggestions"] = self._generate_seo_suggestions(current_analysis, content_type)
        
        return result
    
    def _analyze_seo_state(self, content: str, keywords: List[str], content_type: ContentType) -> Dict[str, Any]:
        """Analyze current SEO state of content"""
        analysis = {
            "word_count": len(content.split()),
            "character_count": len(content),
            "keyword_usage": {},
            "keyword_density": {},
            "heading_structure": self._analyze_heading_structure(content),
            "title_present": self._has_title(content),
            "meta_elements": self._analyze_meta_elements(content)
        }
        
        # Analyze keyword usage
        content_lower = content.lower()
        total_words = analysis["word_count"]
        
        for keyword in keywords:
            variations = self.keyword_variations.get(keyword.lower(), [keyword])
            
            usage_count = 0
            for variation in variations:
                usage_count += content_lower.count(variation.lower())
            
            analysis["keyword_usage"][keyword] = usage_count
            analysis["keyword_density"][keyword] = usage_count / total_words if total_words > 0 else 0
        
        return analysis
    
    async def _apply_seo_optimizations(
        self,
        content: str,
        keywords: List[str],
        content_type: ContentType,
        analysis: Dict[str, Any]
    ) -> str:
        """Apply SEO optimizations to content"""
        optimized = content
        
        # Add title if missing
        if not analysis["title_present"] and content_type in [ContentType.NEWSLETTER_ARTICLE, ContentType.SEO_BLOG_POST]:
            title = self._generate_seo_title(keywords, content_type)
            optimized = f"# {title}\n\n{optimized}"
        
        # Optimize keyword density
        optimized = self._optimize_keyword_density(optimized, keywords, analysis)
        
        # Add heading structure if needed
        if content_type in [ContentType.NEWSLETTER_ARTICLE, ContentType.SEO_BLOG_POST, ContentType.HOW_TO_GUIDE]:
            optimized = self._improve_heading_structure(optimized, keywords)
        
        # Add meta description for blog posts
        if content_type == ContentType.SEO_BLOG_POST:
            meta_description = self._generate_meta_description(content, keywords)
            optimized = f"{optimized}\n\n<!-- Meta Description: {meta_description} -->"
        
        return optimized
    
    def _optimize_keyword_density(self, content: str, keywords: List[str], analysis: Dict[str, Any]) -> str:
        """Optimize keyword density in content"""
        guidelines = self.seo_guidelines.get(ContentType.SEO_BLOG_POST, {})
        target_density_range = guidelines.get("keyword_density", (0.01, 0.03))
        
        optimized = content
        
        for keyword in keywords:
            current_density = analysis["keyword_density"].get(keyword, 0)
            
            # If keyword density is too low, suggest natural integration points
            if current_density < target_density_range[0]:
                # Find good integration points (end of paragraphs, before examples)
                integration_points = self._find_keyword_integration_points(optimized, keyword)
                
                # Add keyword naturally where appropriate
                for point in integration_points[:2]:  # Limit to 2 additions
                    variation = self._get_natural_keyword_variation(keyword)
                    optimized = self._insert_keyword_naturally(optimized, point, variation)
        
        return optimized
    
    def _find_keyword_integration_points(self, content: str, keyword: str) -> List[int]:
        """Find natural points to integrate keywords"""
        integration_points = []
        
        # Look for paragraph endings
        paragraphs = content.split('\n\n')
        for i, paragraph in enumerate(paragraphs):
            if len(paragraph) > 100 and keyword.lower() not in paragraph.lower():
                # This paragraph could benefit from keyword integration
                integration_points.append(i)
        
        return integration_points
    
    def _get_natural_keyword_variation(self, keyword: str) -> str:
        """Get a natural variation of the keyword"""
        variations = self.keyword_variations.get(keyword.lower(), [keyword])
        return variations[0] if variations else keyword
    
    def _insert_keyword_naturally(self, content: str, paragraph_index: int, keyword: str) -> str:
        """Insert keyword naturally into content"""
        paragraphs = content.split('\n\n')
        
        if paragraph_index < len(paragraphs):
            paragraph = paragraphs[paragraph_index]
            
            # Add keyword in a natural way at the end of paragraph
            if not paragraph.endswith('.'):
                paragraph += '.'
            
            # Simple natural integration (could be more sophisticated)
            keyword_phrases = [
                f" {keyword} is essential for success.",
                f" Understanding {keyword} helps achieve better results.",
                f" {keyword} plays a crucial role in this process."
            ]
            
            # Choose appropriate phrase based on keyword
            if "aquascaping" in keyword.lower():
                phrase = f" {keyword} enthusiasts will find this particularly useful."
            elif "plant" in keyword.lower():
                phrase = f" Proper {keyword} care is essential for success."
            else:
                phrase = keyword_phrases[0]
            
            paragraphs[paragraph_index] = paragraph + phrase
        
        return '\n\n'.join(paragraphs)
    
    def _analyze_heading_structure(self, content: str) -> Dict[str, Any]:
        """Analyze heading structure in content"""
        headings = {
            "h1": len(re.findall(r'^# ', content, re.MULTILINE)),
            "h2": len(re.findall(r'^## ', content, re.MULTILINE)),
            "h3": len(re.findall(r'^### ', content, re.MULTILINE)),
            "h4": len(re.findall(r'^#### ', content, re.MULTILINE))
        }
        
        return {
            "headings": headings,
            "total_headings": sum(headings.values()),
            "has_h1": headings["h1"] > 0,
            "has_hierarchy": headings["h2"] > 0 or headings["h3"] > 0
        }
    
    def _has_title(self, content: str) -> bool:
        """Check if content has a title"""
        lines = content.split('\n')
        return len(lines) > 0 and (lines[0].startswith('# ') or len(lines[0]) < 100)
    
    def _analyze_meta_elements(self, content: str) -> Dict[str, Any]:
        """Analyze meta elements in content"""
        return {
            "meta_description": bool(re.search(r'<!-- Meta Description:', content)),
            "meta_keywords": bool(re.search(r'<!-- Keywords:', content)),
            "structured_data": bool(re.search(r'schema\.org', content))
        }
    
    def _generate_seo_title(self, keywords: List[str], content_type: ContentType) -> str:
        """Generate SEO-optimized title"""
        primary_keyword = keywords[0] if keywords else "Aquascaping"
        
        title_templates = {
            ContentType.NEWSLETTER_ARTICLE: [
                f"Complete Guide to {primary_keyword}",
                f"{primary_keyword}: Essential Tips and Techniques",
                f"Master {primary_keyword} with Expert Advice"
            ],
            ContentType.SEO_BLOG_POST: [
                f"Ultimate {primary_keyword} Guide for Beginners",
                f"{primary_keyword}: Everything You Need to Know",
                f"Professional {primary_keyword} Tips and Tricks"
            ],
            ContentType.HOW_TO_GUIDE: [
                f"How to {primary_keyword}: Step-by-Step Guide",
                f"{primary_keyword} Tutorial for Beginners",
                f"Complete {primary_keyword} Instructions"
            ]
        }
        
        templates = title_templates.get(content_type, title_templates[ContentType.NEWSLETTER_ARTICLE])
        return templates[0]
    
    def _improve_heading_structure(self, content: str, keywords: List[str]) -> str:
        """Improve heading structure for SEO"""
        # This is a simplified implementation
        # In practice, this would use NLP to identify logical sections
        
        paragraphs = content.split('\n\n')
        improved_paragraphs = []
        
        for i, paragraph in enumerate(paragraphs):
            # Add headings for longer sections that could benefit
            if (len(paragraph) > 300 and 
                not paragraph.startswith('#') and 
                i > 0 and 
                len(improved_paragraphs) > 0):
                
                # Generate section heading based on content
                heading = self._generate_section_heading(paragraph, keywords)
                if heading:
                    improved_paragraphs.append(f"## {heading}")
            
            improved_paragraphs.append(paragraph)
        
        return '\n\n'.join(improved_paragraphs)
    
    def _generate_section_heading(self, paragraph: str, keywords: List[str]) -> Optional[str]:
        """Generate appropriate section heading"""
        # Simple keyword-based heading generation
        paragraph_lower = paragraph.lower()
        
        if any(word in paragraph_lower for word in ['step', 'how to', 'method']):
            return "Implementation Steps"
        elif any(word in paragraph_lower for word in ['benefit', 'advantage', 'important']):
            return "Key Benefits"
        elif any(word in paragraph_lower for word in ['problem', 'issue', 'mistake']):
            return "Common Issues"
        elif any(word in paragraph_lower for word in ['tip', 'advice', 'recommend']):
            return "Expert Tips"
        
        return None
    
    def _generate_meta_description(self, content: str, keywords: List[str]) -> str:
        """Generate SEO-optimized meta description"""
        # Extract first meaningful sentence that includes keywords
        sentences = re.split(r'[.!?]+', content)
        
        for sentence in sentences[:3]:  # Check first 3 sentences
            sentence = sentence.strip()
            if (len(sentence) > 50 and 
                any(keyword.lower() in sentence.lower() for keyword in keywords)):
                
                # Truncate to meta description length
                if len(sentence) > 160:
                    sentence = sentence[:157] + "..."
                
                return sentence
        
        # Fallback meta description
        primary_keyword = keywords[0] if keywords else "aquascaping"
        return f"Learn everything about {primary_keyword} with expert tips, techniques, and step-by-step guidance for success."
    
    def _calculate_improvement_score(
        self,
        analysis: Dict[str, Any],
        keywords: List[str],
        content_type: ContentType
    ) -> float:
        """Calculate SEO improvement score"""
        improvements = 0
        total_checks = 0
        
        # Check keyword density improvements
        for keyword in keywords:
            density = analysis["keyword_density"].get(keyword, 0)
            if density < 0.01:  # Was too low
                improvements += 1
            total_checks += 1
        
        # Check structure improvements
        if not analysis["title_present"]:
            improvements += 1
        total_checks += 1
        
        if not analysis["heading_structure"]["has_hierarchy"]:
            improvements += 1
        total_checks += 1
        
        return improvements / total_checks if total_checks > 0 else 0
    
    def _calculate_seo_scores(self, content: str, keywords: List[str], content_type: ContentType) -> Dict[str, float]:
        """Calculate various SEO scores"""
        analysis = self._analyze_seo_state(content, keywords, content_type)
        
        # Keyword optimization score
        keyword_score = 0
        for keyword in keywords:
            density = analysis["keyword_density"].get(keyword, 0)
            if 0.01 <= density <= 0.03:
                keyword_score += 1
            elif density > 0:
                keyword_score += 0.5
        
        keyword_score = keyword_score / len(keywords) if keywords else 0
        
        # Structure score
        structure_score = 0
        if analysis["title_present"]:
            structure_score += 0.4
        if analysis["heading_structure"]["has_hierarchy"]:
            structure_score += 0.3
        if analysis["heading_structure"]["total_headings"] >= 2:
            structure_score += 0.3
        
        # Content length score
        guidelines = self.seo_guidelines.get(content_type, {})
        word_count_range = guidelines.get("word_count", (200, 2000))
        word_count = analysis["word_count"]
        
        if word_count_range[0] <= word_count <= word_count_range[1]:
            length_score = 1.0
        elif word_count < word_count_range[0]:
            length_score = word_count / word_count_range[0]
        else:
            length_score = max(0.5, 1.0 - (word_count - word_count_range[1]) / word_count_range[1])
        
        # Overall SEO score
        seo_score = (keyword_score * 0.4 + structure_score * 0.4 + length_score * 0.2)
        
        return {
            "seo_score": seo_score,
            "keyword_score": keyword_score,
            "structure_score": structure_score,
            "length_score": length_score
        }
    
    def _generate_seo_suggestions(self, analysis: Dict[str, Any], content_type: ContentType) -> List[str]:
        """Generate SEO improvement suggestions"""
        suggestions = []
        
        # Title suggestions
        if not analysis["title_present"]:
            suggestions.append("Add a descriptive title with primary keyword")
        
        # Heading structure suggestions
        if not analysis["heading_structure"]["has_hierarchy"]:
            suggestions.append("Add subheadings (H2, H3) to improve content structure")
        
        # Keyword density suggestions
        low_density_keywords = [
            keyword for keyword, density in analysis["keyword_density"].items()
            if density < 0.01
        ]
        
        if low_density_keywords:
            suggestions.append(f"Increase usage of keywords: {', '.join(low_density_keywords)}")
        
        # Content length suggestions
        guidelines = self.seo_guidelines.get(content_type, {})
        word_count_range = guidelines.get("word_count")
        
        if word_count_range:
            word_count = analysis["word_count"]
            if word_count < word_count_range[0]:
                suggestions.append(f"Expand content to at least {word_count_range[0]} words")
            elif word_count > word_count_range[1]:
                suggestions.append(f"Consider condensing content to under {word_count_range[1]} words")
        
        return suggestions