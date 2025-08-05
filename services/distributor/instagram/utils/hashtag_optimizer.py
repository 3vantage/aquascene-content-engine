"""
Hashtag Optimizer for Instagram Posts
Generates optimized hashtag combinations for Bulgarian and international aquascaping markets.
"""

import json
import sqlite3
import requests
import random
from typing import Dict, List, Set, Tuple, Optional
from dataclasses import dataclass
from enum import Enum
from datetime import datetime, timedelta
import logging
from collections import Counter, defaultdict
import re


class HashtagType(Enum):
    NICHE = "niche"  # 10K-100K posts
    MODERATE = "moderate"  # 100K-500K posts
    POPULAR = "popular"  # 500K+ posts
    BRANDED = "branded"  # Brand/location specific
    TRENDING = "trending"  # Currently trending


class ContentCategory(Enum):
    AQUASCAPING = "aquascaping"
    PLANTED_TANK = "planted_tank"
    FRESHWATER = "freshwater"
    SALTWATER = "saltwater"
    FISH_KEEPING = "fish_keeping"
    AQUARIUM_PLANTS = "aquarium_plants"
    AQUARIUM_DESIGN = "aquarium_design"
    MAINTENANCE = "maintenance"
    EQUIPMENT = "equipment"
    TUTORIAL = "tutorial"
    COMMUNITY = "community"


@dataclass
class HashtagData:
    """Data structure for hashtag information"""
    tag: str
    post_count: int
    engagement_rate: float
    hashtag_type: HashtagType
    language: str  # 'en', 'bg', 'universal'
    last_updated: datetime
    performance_score: float = 0.0


class HashtagDatabase:
    """SQLite database for storing hashtag performance data"""
    
    def __init__(self, db_path: str = "hashtag_database.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize hashtag database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS hashtags (
                tag TEXT PRIMARY KEY,
                post_count INTEGER,
                engagement_rate REAL,
                hashtag_type TEXT,
                language TEXT,
                performance_score REAL,
                last_updated TEXT,
                times_used INTEGER DEFAULT 0,
                avg_performance REAL DEFAULT 0.0
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS hashtag_combinations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                post_id TEXT,
                hashtags TEXT,
                engagement_score REAL,
                reach INTEGER,
                created_at TEXT
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS trending_hashtags (
                tag TEXT,
                trend_score REAL,
                date TEXT,
                region TEXT,
                PRIMARY KEY (tag, date, region)
            )
        """)
        
        conn.commit()
        conn.close()
    
    def save_hashtag(self, hashtag_data: HashtagData):
        """Save hashtag data to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO hashtags 
            (tag, post_count, engagement_rate, hashtag_type, language, performance_score, last_updated)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            hashtag_data.tag,
            hashtag_data.post_count,
            hashtag_data.engagement_rate,
            hashtag_data.hashtag_type.value,
            hashtag_data.language,
            hashtag_data.performance_score,
            hashtag_data.last_updated.isoformat()
        ))
        
        conn.commit()
        conn.close()
    
    def get_hashtags_by_type(self, hashtag_type: HashtagType, language: str = None) -> List[HashtagData]:
        """Get hashtags by type and language"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = "SELECT * FROM hashtags WHERE hashtag_type = ?"
        params = [hashtag_type.value]
        
        if language:
            query += " AND (language = ? OR language = 'universal')"
            params.append(language)
        
        query += " ORDER BY performance_score DESC"
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        hashtags = []
        for row in rows:
            hashtag = HashtagData(
                tag=row[0],
                post_count=row[1],
                engagement_rate=row[2],
                hashtag_type=HashtagType(row[3]),
                language=row[4],
                performance_score=row[5],
                last_updated=datetime.fromisoformat(row[6])
            )
            hashtags.append(hashtag)
        
        return hashtags
    
    def update_hashtag_performance(self, tag: str, engagement_score: float, reach: int):
        """Update hashtag performance based on actual results"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE hashtags 
            SET times_used = times_used + 1,
                avg_performance = (avg_performance * (times_used - 1) + ?) / times_used
            WHERE tag = ?
        """, (engagement_score, tag))
        
        conn.commit()
        conn.close()


class HashtagOptimizer:
    """
    Main hashtag optimization engine for Instagram posts.
    """
    
    def __init__(self, db_path: str = None):
        self.db = HashtagDatabase(db_path)
        self.logger = logging.getLogger(__name__)
        
        # Initialize hashtag database if empty
        self._initialize_hashtag_data()
    
    def _initialize_hashtag_data(self):
        """Initialize database with aquascaping hashtags"""
        
        # Bulgarian aquascaping hashtags
        bulgarian_hashtags = {
            # Popular Bulgarian tags
            "аквариум": (50000, 0.045, HashtagType.POPULAR),
            "аквариумистика": (15000, 0.065, HashtagType.MODERATE),
            "растения": (120000, 0.035, HashtagType.POPULAR),
            "природа": (800000, 0.025, HashtagType.POPULAR),
            "рибки": (25000, 0.055, HashtagType.MODERATE),
            "акваскейп": (8000, 0.085, HashtagType.NICHE),
            "подводенсвят": (12000, 0.070, HashtagType.MODERATE),
            "зеленаквариум": (3000, 0.090, HashtagType.NICHE),
            "софия": (300000, 0.030, HashtagType.POPULAR),
            "българия": (500000, 0.025, HashtagType.POPULAR),
            "пловдив": (150000, 0.035, HashtagType.POPULAR),
            "варна": (120000, 0.040, HashtagType.POPULAR),
            
            # Niche Bulgarian aquascaping
            "аквариумнирастения": (2000, 0.095, HashtagType.NICHE),
            "акваскейпинг": (1500, 0.100, HashtagType.NICHE),
            "подводнаградина": (800, 0.110, HashtagType.NICHE),
            "аквариумендизайн": (1200, 0.105, HashtagType.NICHE),
        }
        
        # International aquascaping hashtags
        international_hashtags = {
            # Core aquascaping tags
            "aquascaping": (850000, 0.045, HashtagType.POPULAR),
            "plantedtank": (420000, 0.055, HashtagType.POPULAR),
            "aquarium": (2800000, 0.025, HashtagType.POPULAR),
            "freshwateraquarium": (380000, 0.050, HashtagType.POPULAR),
            "aquascape": (650000, 0.048, HashtagType.POPULAR),
            "plantedaquarium": (220000, 0.065, HashtagType.MODERATE),
            
            # Niche aquascaping
            "natureaquarium": (180000, 0.070, HashtagType.MODERATE),
            "iwagumi": (45000, 0.085, HashtagType.NICHE),
            "dutchstyle": (25000, 0.090, HashtagType.NICHE),
            "aquascapedesign": (35000, 0.080, HashtagType.NICHE),
            "greenaquarium": (55000, 0.075, HashtagType.NICHE),
            "aquaticplants": (195000, 0.060, HashtagType.MODERATE),
            "co2aquarium": (18000, 0.095, HashtagType.NICHE),
            "aquascaper": (75000, 0.070, HashtagType.NICHE),
            
            # Plant specific
            "cryptocoryne": (12000, 0.100, HashtagType.NICHE),
            "anubias": (35000, 0.085, HashtagType.NICHE),
            "vallisneria": (8000, 0.105, HashtagType.NICHE),
            "java_fern": (15000, 0.095, HashtagType.NICHE),
            "amazon_sword": (10000, 0.100, HashtagType.NICHE),
            "carpetplants": (25000, 0.090, HashtagType.NICHE),
            
            # Equipment and techniques
            "ledlighting": (180000, 0.040, HashtagType.MODERATE),
            "aquasoil": (45000, 0.080, HashtagType.NICHE),
            "filtration": (120000, 0.045, HashtagType.MODERATE),
            "aquascapetools": (15000, 0.095, HashtagType.NICHE),
            
            # Community and inspiration
            "fishtank": (950000, 0.035, HashtagType.POPULAR),
            "aquariumhobby": (85000, 0.065, HashtagType.MODERATE),
            "aquariumlife": (195000, 0.055, HashtagType.MODERATE),
            "tankshot": (65000, 0.070, HashtagType.NICHE),
            "aquariumsofinstagram": (280000, 0.050, HashtagType.MODERATE),
            
            # Broader appeal
            "underwater": (1200000, 0.030, HashtagType.POPULAR),
            "nature": (85000000, 0.020, HashtagType.POPULAR),
            "green": (12000000, 0.025, HashtagType.POPULAR),
            "peaceful": (2500000, 0.028, HashtagType.POPULAR),
            "zen": (3200000, 0.030, HashtagType.POPULAR),
            "meditation": (8500000, 0.025, HashtagType.POPULAR),
        }
        
        # Save to database
        for tag, (post_count, engagement_rate, hashtag_type) in bulgarian_hashtags.items():
            hashtag_data = HashtagData(
                tag=tag,
                post_count=post_count,
                engagement_rate=engagement_rate,
                hashtag_type=hashtag_type,
                language="bg",
                last_updated=datetime.now(),
                performance_score=engagement_rate * 100  # Simple scoring
            )
            self.db.save_hashtag(hashtag_data)
        
        for tag, (post_count, engagement_rate, hashtag_type) in international_hashtags.items():
            hashtag_data = HashtagData(
                tag=tag,
                post_count=post_count,
                engagement_rate=engagement_rate,
                hashtag_type=hashtag_type,
                language="en",
                last_updated=datetime.now(),
                performance_score=engagement_rate * 100
            )
            self.db.save_hashtag(hashtag_data)
    
    def generate_hashtag_set(self, content_category: ContentCategory, 
                           target_language: str = "bg", 
                           max_hashtags: int = 30,
                           include_branded: bool = True) -> List[str]:
        """
        Generate optimized hashtag set for a specific content category.
        """
        hashtag_set = set()
        
        # Distribution strategy for optimal reach
        distribution = {
            HashtagType.NICHE: 8,      # High engagement, specific audience
            HashtagType.MODERATE: 12,   # Balanced reach and engagement
            HashtagType.POPULAR: 8,     # Broad reach
            HashtagType.BRANDED: 2 if include_branded else 0
        }
        
        # Get hashtags by type and language
        for hashtag_type, count in distribution.items():
            if hashtag_type == HashtagType.BRANDED:
                branded_tags = self._get_branded_hashtags(target_language)
                hashtag_set.update(random.sample(branded_tags, min(count, len(branded_tags))))
            else:
                type_hashtags = self.db.get_hashtags_by_type(hashtag_type, target_language)
                
                # Filter by content category relevance
                relevant_hashtags = self._filter_by_content_category(type_hashtags, content_category)
                
                if relevant_hashtags:
                    selected = random.sample(
                        relevant_hashtags, 
                        min(count, len(relevant_hashtags))
                    )
                    hashtag_set.update([h.tag for h in selected])
        
        # Fill remaining slots with high-performing hashtags
        if len(hashtag_set) < max_hashtags:
            remaining_slots = max_hashtags - len(hashtag_set)
            all_hashtags = self.db.get_hashtags_by_type(HashtagType.MODERATE, target_language)
            
            available_hashtags = [h for h in all_hashtags if h.tag not in hashtag_set]
            if available_hashtags:
                additional = random.sample(
                    available_hashtags, 
                    min(remaining_slots, len(available_hashtags))
                )
                hashtag_set.update([h.tag for h in additional])
        
        return list(hashtag_set)
    
    def _filter_by_content_category(self, hashtags: List[HashtagData], 
                                  category: ContentCategory) -> List[HashtagData]:
        """Filter hashtags based on content category relevance"""
        
        category_keywords = {
            ContentCategory.AQUASCAPING: ["aquascape", "акваскейп", "design", "дизайн"],
            ContentCategory.PLANTED_TANK: ["plant", "растения", "green", "зелен"],
            ContentCategory.FRESHWATER: ["freshwater", "пресновод", "tropical", "тропически"],
            ContentCategory.SALTWATER: ["saltwater", "морска", "reef", "риф"],
            ContentCategory.FISH_KEEPING: ["fish", "рибки", "keeping", "отглеждане"],
            ContentCategory.AQUARIUM_PLANTS: ["plant", "растения", "aquatic", "водни"],
            ContentCategory.MAINTENANCE: ["maintenance", "поддръжка", "cleaning", "почистване"],
            ContentCategory.EQUIPMENT: ["equipment", "оборудване", "filter", "филтър", "led"],
            ContentCategory.TUTORIAL: ["tutorial", "урок", "guide", "ръководство", "howto"],
            ContentCategory.COMMUNITY: ["community", "общност", "hobby", "хоби"]
        }
        
        keywords = category_keywords.get(category, [])
        if not keywords:
            return hashtags
        
        relevant_hashtags = []
        for hashtag in hashtags:
            tag_lower = hashtag.tag.lower()
            if any(keyword.lower() in tag_lower for keyword in keywords):
                relevant_hashtags.append(hashtag)
        
        # If no specific matches, return all (better than empty)
        return relevant_hashtags if relevant_hashtags else hashtags
    
    def _get_branded_hashtags(self, language: str) -> List[str]:
        """Get branded hashtags for AquaScene"""
        branded = ["aquascenebg", "aquascene", "greenaqua"]
        
        if language == "bg":
            branded.extend(["акваскейнбг", "зеленаквабг"])
        
        return branded
    
    def optimize_for_post_type(self, post_type: str, content_text: str, 
                             target_language: str = "bg") -> List[str]:
        """
        Generate hashtags optimized for specific post types and content.
        """
        
        # Analyze content for relevant keywords
        content_keywords = self._extract_keywords_from_content(content_text)
        
        # Determine content category from post type and content
        category = self._determine_content_category(post_type, content_keywords)
        
        # Generate base hashtag set
        hashtags = self.generate_hashtag_set(category, target_language)
        
        # Add content-specific hashtags
        content_hashtags = self._generate_content_specific_hashtags(content_keywords, target_language)
        
        # Merge and optimize
        all_hashtags = list(set(hashtags + content_hashtags))
        
        # Ensure we don't exceed Instagram's limit
        return all_hashtags[:30]
    
    def _extract_keywords_from_content(self, content: str) -> List[str]:
        """Extract relevant keywords from content text"""
        
        # Define aquascaping-related keywords
        aquascaping_keywords = {
            # Plants
            "anubias", "cryptocoryne", "vallisneria", "java", "moss", "fern", 
            "sword", "carpet", "stem", "floating",
            
            # Bulgarian plant names
            "растения", "мъх", "папрат", "анубиас",
            
            # Equipment
            "led", "co2", "filter", "substrate", "fertilizer", "light",
            "филтър", "светлина", "тор", "субстрат",
            
            # Techniques
            "trimming", "pruning", "aquascape", "layout", "design",
            "подрязване", "дизайн", "акваскейп",
            
            # Fish
            "tetra", "guppy", "shrimp", "snail", "beta", "angelfish",
            "рибки", "скариди", "охлюви",
            
            # Styles
            "iwagumi", "dutch", "nature", "biotope", "jungle",
            "природен", "джунгла"
        }
        
        # Extract keywords from content
        content_lower = content.lower()
        found_keywords = []
        
        for keyword in aquascaping_keywords:
            if keyword in content_lower:
                found_keywords.append(keyword)
        
        return found_keywords
    
    def _determine_content_category(self, post_type: str, keywords: List[str]) -> ContentCategory:
        """Determine content category based on post type and keywords"""
        
        # Map post types to categories
        type_mapping = {
            "educational": ContentCategory.TUTORIAL,
            "showcase": ContentCategory.AQUASCAPING,
            "tutorial": ContentCategory.TUTORIAL,
            "plant_spotlight": ContentCategory.AQUARIUM_PLANTS,
            "fish_spotlight": ContentCategory.FISH_KEEPING,
            "equipment_review": ContentCategory.EQUIPMENT,
            "maintenance": ContentCategory.MAINTENANCE,
            "community": ContentCategory.COMMUNITY
        }
        
        # Check post type first
        if post_type in type_mapping:
            return type_mapping[post_type]
        
        # Analyze keywords
        if any(k in ["plant", "растения", "moss", "мъх"] for k in keywords):
            return ContentCategory.AQUARIUM_PLANTS
        elif any(k in ["fish", "рибки", "shrimp", "скариди"] for k in keywords):
            return ContentCategory.FISH_KEEPING
        elif any(k in ["equipment", "filter", "led", "филтър"] for k in keywords):
            return ContentCategory.EQUIPMENT
        elif any(k in ["aquascape", "акваскейп", "design", "дизайн"] for k in keywords):
            return ContentCategory.AQUASCAPING
        
        # Default to general aquascaping
        return ContentCategory.AQUASCAPING
    
    def _generate_content_specific_hashtags(self, keywords: List[str], 
                                          language: str) -> List[str]:
        """Generate hashtags specific to content keywords"""
        
        content_hashtags = []
        
        # Map keywords to specific hashtags
        keyword_hashtag_map = {
            "anubias": ["anubias", "anubiasnana"],
            "cryptocoryne": ["cryptocoryne", "crypt"],
            "java": ["javafern", "javamoss"],
            "moss": ["aquariummoss", "мъх"],
            "растения": ["аквариумнирастения", "подводнирастения"],
            "led": ["ledlighting", "aquariumlighting"],
            "co2": ["co2injection", "plantedtankco2"],
            "filter": ["aquariumfilter", "filtration"],
            "iwagumi": ["iwagumi", "iwagumistyle"],
            "dutch": ["dutchstyle", "dutchaquascape"]
        }
        
        for keyword in keywords:
            if keyword in keyword_hashtag_map:
                content_hashtags.extend(keyword_hashtag_map[keyword])
        
        # Remove duplicates and limit
        return list(set(content_hashtags))[:5]
    
    def analyze_hashtag_performance(self, post_hashtags: List[str], 
                                  engagement_data: Dict) -> Dict:
        """
        Analyze performance of hashtags used in a post.
        """
        
        engagement_score = engagement_data.get('engagement_rate', 0)
        reach = engagement_data.get('reach', 0)
        
        # Update database with performance data
        for hashtag in post_hashtags:
            self.db.update_hashtag_performance(hashtag, engagement_score, reach)
        
        # Calculate performance metrics
        performance_analysis = {
            'total_hashtags': len(post_hashtags),
            'engagement_score': engagement_score,
            'reach': reach,
            'performance_per_hashtag': engagement_score / len(post_hashtags) if post_hashtags else 0,
            'top_performing_hashtags': self._identify_top_performers(post_hashtags),
            'recommendations': self._generate_recommendations(post_hashtags, engagement_score)
        }
        
        return performance_analysis
    
    def _identify_top_performers(self, hashtags: List[str]) -> List[str]:
        """Identify top performing hashtags from a set"""
        # This would analyze historical performance data
        # For now, return a simple implementation
        return hashtags[:5]  # Top 5
    
    def _generate_recommendations(self, hashtags: List[str], 
                                engagement_score: float) -> List[str]:
        """Generate recommendations for hashtag optimization"""
        
        recommendations = []
        
        if engagement_score < 0.03:
            recommendations.append("Consider using more niche hashtags for better engagement")
            recommendations.append("Add more Bulgarian hashtags for local audience")
        
        if len(hashtags) < 20:
            recommendations.append("Use more hashtags to increase reach (up to 30)")
        
        if not any("bg" in tag or any(c in "абвгдежзийклмнопрстуфхцчшщъьюя" for c in tag) for tag in hashtags):
            recommendations.append("Include Bulgarian hashtags for local market penetration")
        
        return recommendations
    
    def get_trending_hashtags(self, region: str = "bg", limit: int = 10) -> List[str]:
        """Get currently trending hashtags for the region"""
        
        # This would integrate with trending hashtag services
        # For now, return curated trending tags
        
        if region == "bg":
            trending = [
                "природа", "аквариум", "растения", "софия", "българия",
                "зелено", "вода", "релакс", "дом", "хоби"
            ]
        else:
            trending = [
                "aquascaping", "plantedtank", "aquarium", "nature", "green",
                "peaceful", "zen", "hobby", "freshwater", "aquascape"
            ]
        
        return trending[:limit]


# Usage example and testing
if __name__ == "__main__":
    optimizer = HashtagOptimizer()
    
    # Test hashtag generation
    hashtags = optimizer.generate_hashtag_set(
        ContentCategory.AQUASCAPING, 
        target_language="bg"
    )
    
    print("Generated hashtags:", hashtags)
    print(f"Total: {len(hashtags)}")
    
    # Test content-specific optimization
    content = "Beautiful Anubias nana plant in my new aquascape design with CO2 injection"
    optimized_hashtags = optimizer.optimize_for_post_type(
        "showcase", 
        content, 
        target_language="en"
    )
    
    print("Optimized hashtags:", optimized_hashtags)