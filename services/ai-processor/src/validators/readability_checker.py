"""
Readability Checker

Analyzes content readability, sentence structure, and vocabulary
to ensure content is accessible to the target audience.
"""

import re
import math
from typing import Dict, List, Optional, Any
import structlog

logger = structlog.get_logger()


class ReadabilityChecker:
    """Analyzes content readability and provides improvement suggestions"""
    
    def __init__(self):
        # Complex words that might need simplification
        self.complex_aquascaping_terms = {
            "photosynthetically": "for photosynthesis",
            "nitrification": "nitrogen cycle process",
            "denitrification": "nitrate removal process",
            "phytoplankton": "microscopic plants",
            "rhizomatous": "growing from rhizomes",
            "epiphytic": "growing on other plants"
        }
        
        # Common transition words that improve readability
        self.transition_words = [
            "however", "therefore", "meanwhile", "furthermore", "moreover",
            "consequently", "additionally", "similarly", "likewise", "thus",
            "first", "second", "finally", "next", "then", "also", "but",
            "and", "or", "so", "because", "since", "while", "although"
        ]
    
    async def analyze_readability(self, content: str) -> Dict[str, Any]:
        """Analyze content readability and provide scores"""
        
        # Basic text statistics
        sentences = self._split_into_sentences(content)
        words = content.split()
        syllables = sum(self._count_syllables(word) for word in words)
        
        # Calculate readability scores
        flesch_score = self._calculate_flesch_score(len(sentences), len(words), syllables)
        grade_level = self._calculate_grade_level(len(sentences), len(words), syllables)
        
        # Analyze sentence structure
        sentence_analysis = self._analyze_sentence_structure(sentences)
        
        # Analyze vocabulary
        vocabulary_analysis = self._analyze_vocabulary(words)
        
        # Calculate component scores
        grade_score = self._score_grade_level(grade_level)
        sentence_score = sentence_analysis["score"]
        vocabulary_score = vocabulary_analysis["score"]
        
        # Identify issues and suggestions
        issues = []
        suggestions = []
        
        # Grade level issues
        if grade_level > 12:
            issues.append(f"Content reading level is grade {grade_level:.1f} (may be too complex)")
            suggestions.append("Simplify sentence structure and vocabulary")
        elif grade_level < 6:
            issues.append(f"Content reading level is grade {grade_level:.1f} (may be too simple)")
            suggestions.append("Add more sophisticated vocabulary and concepts")
        
        # Sentence structure issues
        if sentence_analysis["avg_length"] > 25:
            issues.append("Average sentence length is high (>25 words)")
            suggestions.append("Break up long sentences for better readability")
        
        if sentence_analysis["variety_score"] < 0.5:
            issues.append("Limited sentence length variety")
            suggestions.append("Vary sentence lengths for better flow")
        
        # Vocabulary issues
        if vocabulary_analysis["complex_ratio"] > 0.3:
            issues.append("High proportion of complex words")
            suggestions.append("Consider simplifying technical terms")
        
        # Transition word usage
        transition_score = self._calculate_transition_score(content)
        if transition_score < 0.3:
            suggestions.append("Add more transition words to improve flow")
        
        return {
            "flesch_score": flesch_score,
            "grade_level": grade_level,
            "sentence_score": sentence_score,
            "vocabulary_score": vocabulary_score,
            "transition_score": transition_score,
            "overall_readability": (grade_score + sentence_score + vocabulary_score) / 3,
            "statistics": {
                "sentences": len(sentences),
                "words": len(words),
                "syllables": syllables,
                "avg_sentence_length": sentence_analysis["avg_length"],
                "sentence_variety": sentence_analysis["variety_score"],
                "complex_word_ratio": vocabulary_analysis["complex_ratio"]
            },
            "issues": issues,
            "suggestions": suggestions
        }
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences"""
        # Simple sentence splitting - could be improved with NLP library
        sentences = re.split(r'[.!?]+', text)
        return [s.strip() for s in sentences if s.strip()]
    
    def _count_syllables(self, word: str) -> int:
        """Estimate syllable count for a word"""
        word = word.lower().strip(".,!?;:")
        if not word:
            return 0
        
        # Simple syllable counting heuristic
        vowels = "aeiouy"
        syllable_count = 0
        previous_was_vowel = False
        
        for char in word:
            is_vowel = char in vowels
            if is_vowel and not previous_was_vowel:
                syllable_count += 1
            previous_was_vowel = is_vowel
        
        # Handle silent 'e'
        if word.endswith('e') and syllable_count > 1:
            syllable_count -= 1
        
        # Ensure at least 1 syllable
        return max(1, syllable_count)
    
    def _calculate_flesch_score(self, sentences: int, words: int, syllables: int) -> float:
        """Calculate Flesch Reading Ease score"""
        if sentences == 0 or words == 0:
            return 0
        
        avg_sentence_length = words / sentences
        avg_syllables_per_word = syllables / words
        
        score = 206.835 - (1.015 * avg_sentence_length) - (84.6 * avg_syllables_per_word)
        return max(0, min(100, score))
    
    def _calculate_grade_level(self, sentences: int, words: int, syllables: int) -> float:
        """Calculate Flesch-Kincaid Grade Level"""
        if sentences == 0 or words == 0:
            return 0
        
        avg_sentence_length = words / sentences
        avg_syllables_per_word = syllables / words
        
        grade_level = (0.39 * avg_sentence_length) + (11.8 * avg_syllables_per_word) - 15.59
        return max(0, grade_level)
    
    def _analyze_sentence_structure(self, sentences: List[str]) -> Dict[str, Any]:
        """Analyze sentence structure and variety"""
        if not sentences:
            return {"score": 0, "avg_length": 0, "variety_score": 0}
        
        lengths = [len(sentence.split()) for sentence in sentences]
        avg_length = sum(lengths) / len(lengths)
        
        # Calculate variety score based on standard deviation
        if len(lengths) > 1:
            variance = sum((x - avg_length) ** 2 for x in lengths) / len(lengths)
            std_dev = math.sqrt(variance)
            variety_score = min(1.0, std_dev / 10)  # Normalize to 0-1
        else:
            variety_score = 0
        
        # Score sentence structure
        length_score = 1.0
        if avg_length > 25:
            length_score = max(0.3, 1.0 - (avg_length - 25) * 0.05)
        elif avg_length < 8:
            length_score = max(0.5, avg_length / 8)
        
        overall_score = (length_score + variety_score) / 2
        
        return {
            "score": overall_score,
            "avg_length": avg_length,
            "variety_score": variety_score,
            "lengths": lengths
        }
    
    def _analyze_vocabulary(self, words: List[str]) -> Dict[str, Any]:
        """Analyze vocabulary complexity"""
        if not words:
            return {"score": 0, "complex_ratio": 0}
        
        complex_words = 0
        total_words = len(words)
        
        for word in words:
            clean_word = word.lower().strip(".,!?;:\"'")
            
            # Check if word is complex
            if self._is_complex_word(clean_word):
                complex_words += 1
        
        complex_ratio = complex_words / total_words if total_words > 0 else 0
        
        # Score vocabulary (lower complex ratio is better for readability)
        vocabulary_score = max(0, 1.0 - (complex_ratio * 2))
        
        return {
            "score": vocabulary_score,
            "complex_ratio": complex_ratio,
            "complex_words": complex_words,
            "total_words": total_words
        }
    
    def _is_complex_word(self, word: str) -> bool:
        """Determine if a word is complex"""
        # Skip short words and common words
        if len(word) <= 4:
            return False
        
        # Common aquascaping terms that are acceptable
        common_aquascaping = [
            "aquarium", "aquascape", "aquascaping", "substrate", "fertilizer",
            "plants", "lighting", "filter", "bacteria", "nutrients", "trimming"
        ]
        
        if word in common_aquascaping:
            return False
        
        # Check syllable count (>3 syllables might be complex)
        syllables = self._count_syllables(word)
        if syllables > 3:
            return True
        
        # Check for technical suffixes
        technical_suffixes = [
            "tion", "sion", "ment", "ness", "ity", "ous", "ive", "ful", "ism"
        ]
        
        for suffix in technical_suffixes:
            if word.endswith(suffix) and len(word) > 8:
                return True
        
        return False
    
    def _calculate_transition_score(self, content: str) -> float:
        """Calculate how well the content uses transition words"""
        content_lower = content.lower()
        transition_count = 0
        
        for transition in self.transition_words:
            if transition in content_lower:
                transition_count += 1
        
        # Score based on transition word usage
        words = content.split()
        transition_ratio = transition_count / len(words) if words else 0
        
        # Optimal range is around 2-5% transition words
        if 0.02 <= transition_ratio <= 0.05:
            return 1.0
        elif transition_ratio < 0.02:
            return transition_ratio / 0.02
        else:
            return max(0.3, 1.0 - (transition_ratio - 0.05) * 10)
    
    def _score_grade_level(self, grade_level: float) -> float:
        """Score grade level appropriateness"""
        # Target grade level 8-12 for aquascaping content
        if 8 <= grade_level <= 12:
            return 1.0
        elif grade_level < 8:
            return 0.7 + (grade_level / 8) * 0.3
        else:
            return max(0.3, 1.0 - (grade_level - 12) * 0.1)
    
    def get_readability_interpretation(self, flesch_score: float) -> str:
        """Get human-readable interpretation of Flesch score"""
        if flesch_score >= 90:
            return "Very Easy (5th grade)"
        elif flesch_score >= 80:
            return "Easy (6th grade)"
        elif flesch_score >= 70:
            return "Fairly Easy (7th grade)"
        elif flesch_score >= 60:
            return "Standard (8th-9th grade)"
        elif flesch_score >= 50:
            return "Fairly Difficult (10th-12th grade)"
        elif flesch_score >= 30:
            return "Difficult (college level)"
        else:
            return "Very Difficult (graduate level)"
    
    def suggest_improvements(self, analysis: Dict[str, Any]) -> List[str]:
        """Generate specific improvement suggestions"""
        suggestions = []
        
        # Grade level suggestions
        grade_level = analysis.get("grade_level", 0)
        if grade_level > 12:
            suggestions.extend([
                "Break up long, complex sentences",
                "Replace complex words with simpler alternatives",
                "Use active voice instead of passive voice"
            ])
        
        # Sentence structure suggestions
        stats = analysis.get("statistics", {})
        avg_sentence_length = stats.get("avg_sentence_length", 0)
        
        if avg_sentence_length > 20:
            suggestions.append("Aim for average sentence length of 15-20 words")
        
        sentence_variety = stats.get("sentence_variety", 0)
        if sentence_variety < 0.4:
            suggestions.append("Mix short and long sentences for better rhythm")
        
        # Vocabulary suggestions
        complex_ratio = stats.get("complex_word_ratio", 0)
        if complex_ratio > 0.25:
            suggestions.extend([
                "Explain technical terms when first introduced",
                "Consider simpler alternatives for complex words"
            ])
        
        # Transition suggestions
        transition_score = analysis.get("transition_score", 0)
        if transition_score < 0.4:
            suggestions.append("Add transition words to connect ideas smoothly")
        
        return suggestions