"""
Content Queue Management System
Manages content pipeline, validation, approval workflows, and automated posting queue.
"""

import sqlite3
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Union
from dataclasses import dataclass, asdict
from enum import Enum
import logging
from pathlib import Path
import hashlib
import asyncio
from concurrent.futures import ThreadPoolExecutor

from ..api.instagram_client import InstagramPost, MediaType
from ..scheduler.content_scheduler import PostType, ScheduledPost
from ..utils.hashtag_optimizer import HashtagOptimizer, ContentCategory
from ..templates.visual.template_generator import VisualTemplateGenerator, TemplateType


class QueueStatus(Enum):
    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    SCHEDULED = "scheduled"
    PUBLISHED = "published"
    REJECTED = "rejected"
    FAILED = "failed"
    ARCHIVED = "archived"


class ContentSource(Enum):
    MANUAL = "manual"
    AI_GENERATED = "ai_generated"
    USER_SUBMISSION = "user_submission"
    PARTNERSHIP = "partnership"
    TEMPLATE = "template"
    IMPORTED = "imported"


class ValidationRule(Enum):
    CAPTION_LENGTH = "caption_length"
    HASHTAG_COUNT = "hashtag_count"
    IMAGE_QUALITY = "image_quality"
    DUPLICATE_CHECK = "duplicate_check"
    BRAND_COMPLIANCE = "brand_compliance"
    CONTENT_POLICY = "content_policy"


@dataclass
class ContentValidation:
    """Content validation result"""
    rule: ValidationRule
    passed: bool
    message: str
    severity: str  # 'error', 'warning', 'info'


@dataclass
class QueuedContent:
    """Content item in the queue"""
    id: str
    title: str
    content: InstagramPost
    post_type: PostType
    content_source: ContentSource
    status: QueueStatus
    priority: int  # 1-10, higher = more important
    target_publish_time: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    created_by: str
    approved_by: Optional[str] = None
    validation_results: List[ContentValidation] = None
    retry_count: int = 0
    tags: List[str] = None
    notes: str = ""
    performance_prediction: float = 0.0


class ContentValidator:
    """Validates content against various rules and policies"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Define validation rules
        self.rules = {
            ValidationRule.CAPTION_LENGTH: self._validate_caption_length,
            ValidationRule.HASHTAG_COUNT: self._validate_hashtag_count,
            ValidationRule.IMAGE_QUALITY: self._validate_image_quality,
            ValidationRule.DUPLICATE_CHECK: self._validate_duplicate_content,
            ValidationRule.BRAND_COMPLIANCE: self._validate_brand_compliance,
            ValidationRule.CONTENT_POLICY: self._validate_content_policy
        }
    
    def validate_content(self, content: InstagramPost, 
                        existing_content: List[QueuedContent] = None) -> List[ContentValidation]:
        """
        Run all validation rules on content.
        """
        results = []
        
        for rule, validator_func in self.rules.items():
            try:
                validation = validator_func(content, existing_content)
                results.append(validation)
            except Exception as e:
                self.logger.error(f"Validation error for {rule.value}: {e}")
                results.append(ContentValidation(
                    rule=rule,
                    passed=False,
                    message=f"Validation error: {str(e)}",
                    severity="error"
                ))
        
        return results
    
    def _validate_caption_length(self, content: InstagramPost, 
                                existing_content: List[QueuedContent] = None) -> ContentValidation:
        """Validate caption length"""
        
        caption_length = len(content.caption)
        
        # Calculate total length with hashtags
        if content.hashtags:
            hashtag_length = sum(len(tag) + 1 for tag in content.hashtags) + 2  # +2 for spacing
            total_length = caption_length + hashtag_length
        else:
            total_length = caption_length
        
        if total_length > 2200:
            return ContentValidation(
                rule=ValidationRule.CAPTION_LENGTH,
                passed=False,
                message=f"Caption too long: {total_length}/2200 characters",
                severity="error"
            )
        elif total_length > 2000:
            return ContentValidation(
                rule=ValidationRule.CAPTION_LENGTH,
                passed=True,
                message=f"Caption near limit: {total_length}/2200 characters",
                severity="warning"
            )
        elif caption_length < 50:
            return ContentValidation(
                rule=ValidationRule.CAPTION_LENGTH,
                passed=True,
                message="Caption is very short, consider adding more context",
                severity="warning"
            )
        else:
            return ContentValidation(
                rule=ValidationRule.CAPTION_LENGTH,
                passed=True,
                message=f"Caption length OK: {total_length} characters",
                severity="info"
            )
    
    def _validate_hashtag_count(self, content: InstagramPost, 
                               existing_content: List[QueuedContent] = None) -> ContentValidation:
        """Validate hashtag count and quality"""
        
        hashtag_count = len(content.hashtags) if content.hashtags else 0
        
        if hashtag_count > 30:
            return ContentValidation(
                rule=ValidationRule.HASHTAG_COUNT,
                passed=False,
                message=f"Too many hashtags: {hashtag_count}/30",
                severity="error"
            )
        elif hashtag_count < 5:
            return ContentValidation(
                rule=ValidationRule.HASHTAG_COUNT,
                passed=True,
                message=f"Consider adding more hashtags for better reach: {hashtag_count}/30",
                severity="warning"
            )
        elif hashtag_count > 25:
            return ContentValidation(
                rule=ValidationRule.HASHTAG_COUNT,
                passed=True,
                message=f"High hashtag count: {hashtag_count}/30",
                severity="warning"  
            )
        else:
            return ContentValidation(
                rule=ValidationRule.HASHTAG_COUNT,
                passed=True,
                message=f"Hashtag count OK: {hashtag_count}/30",
                severity="info"
            )
    
    def _validate_image_quality(self, content: InstagramPost, 
                               existing_content: List[QueuedContent] = None) -> ContentValidation:
        """Validate image quality and format"""
        
        # Basic validation - in production would analyze actual image
        if content.media_type == MediaType.IMAGE:
            if not content.media_url:
                return ContentValidation(
                    rule=ValidationRule.IMAGE_QUALITY,
                    passed=False,
                    message="Image URL missing for image post",
                    severity="error"
                )
            
            # Check if URL seems valid
            if not content.media_url.startswith(('http://', 'https://')):
                return ContentValidation(
                    rule=ValidationRule.IMAGE_QUALITY,
                    passed=False,
                    message="Invalid image URL format",
                    severity="error"
                )
        
        elif content.media_type == MediaType.CAROUSEL_ALBUM:
            if not content.media_urls or len(content.media_urls) < 2:
                return ContentValidation(
                    rule=ValidationRule.IMAGE_QUALITY,
                    passed=False,
                    message="Carousel needs at least 2 images",
                    severity="error"
                )
            
            if len(content.media_urls) > 10:
                return ContentValidation(
                    rule=ValidationRule.IMAGE_QUALITY,
                    passed=False,
                    message="Carousel limited to 10 images",
                    severity="error"
                )
        
        return ContentValidation(
            rule=ValidationRule.IMAGE_QUALITY,
            passed=True,
            message="Image validation passed",
            severity="info"
        )
    
    def _validate_duplicate_content(self, content: InstagramPost, 
                                   existing_content: List[QueuedContent] = None) -> ContentValidation:
        """Check for duplicate content"""
        
        if not existing_content:
            return ContentValidation(
                rule=ValidationRule.DUPLICATE_CHECK,
                passed=True,
                message="No existing content to compare",
                severity="info"
            )
        
        # Create content hash for comparison
        content_hash = self._generate_content_hash(content)
        
        # Check against existing content
        for existing in existing_content:
            if existing.status in [QueueStatus.PUBLISHED, QueueStatus.SCHEDULED, QueueStatus.APPROVED]:
                existing_hash = self._generate_content_hash(existing.content)
                
                if content_hash == existing_hash:
                    return ContentValidation(
                        rule=ValidationRule.DUPLICATE_CHECK,
                        passed=False,
                        message=f"Duplicate content detected (similar to {existing.id})",
                        severity="error"
                    )
                
                # Check caption similarity
                similarity = self._calculate_text_similarity(content.caption, existing.content.caption)
                if similarity > 0.8:
                    return ContentValidation(
                        rule=ValidationRule.DUPLICATE_CHECK,
                        passed=True,
                        message=f"Similar content detected ({similarity:.0%} similarity)",
                        severity="warning"
                    )
        
        return ContentValidation(
            rule=ValidationRule.DUPLICATE_CHECK,
            passed=True,
            message="No duplicate content found",
            severity="info"
        )
    
    def _validate_brand_compliance(self, content: InstagramPost, 
                                  existing_content: List[QueuedContent] = None) -> ContentValidation:
        """Validate brand compliance and messaging"""
        
        caption_lower = content.caption.lower()
        
        # Check for required brand elements
        brand_keywords = ["aquascene", "акваскейн", "aquarium", "аквариум", "aquascaping", "акваскейп"]
        has_brand_mention = any(keyword in caption_lower for keyword in brand_keywords)
        
        # Check for inappropriate content
        inappropriate_words = ["spam", "fake", "scam", "hack", "illegal"]
        has_inappropriate = any(word in caption_lower for word in inappropriate_words)
        
        if has_inappropriate:
            return ContentValidation(
                rule=ValidationRule.BRAND_COMPLIANCE,
                passed=False,
                message="Content contains inappropriate language",
                severity="error"
            )
        
        if not has_brand_mention and len(content.caption) > 100:
            return ContentValidation(
                rule=ValidationRule.BRAND_COMPLIANCE,
                passed=True,
                message="Consider adding brand mention for better brand awareness",
                severity="warning"
            )
        
        return ContentValidation(
            rule=ValidationRule.BRAND_COMPLIANCE,
            passed=True,
            message="Brand compliance check passed",
            severity="info"
        )
    
    def _validate_content_policy(self, content: InstagramPost, 
                                existing_content: List[QueuedContent] = None) -> ContentValidation:
        """Validate against Instagram's content policies"""
        
        caption_lower = content.caption.lower()
        
        # Check for policy violations
        restricted_terms = [
            "buy followers", "fake likes", "spam", "illegal", "drugs", 
            "violence", "hate", "discrimination"
        ]
        
        violations = [term for term in restricted_terms if term in caption_lower]
        
        if violations:
            return ContentValidation(
                rule=ValidationRule.CONTENT_POLICY,
                passed=False,
                message=f"Potential policy violation: {', '.join(violations)}",
                severity="error"
            )
        
        return ContentValidation(
            rule=ValidationRule.CONTENT_POLICY,
            passed=True,
            message="Content policy check passed",
            severity="info"
        )
    
    def _generate_content_hash(self, content: InstagramPost) -> str:
        """Generate hash for content comparison"""
        content_string = f"{content.caption}{content.media_url}{str(content.hashtags)}"
        return hashlib.md5(content_string.encode()).hexdigest()
    
    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """Calculate simple text similarity (Jaccard similarity)"""
        
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 and not words2:
            return 1.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union) if union else 0.0


class ContentQueueDatabase:
    """SQLite database for content queue management"""
    
    def __init__(self, db_path: str = "content_queue.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize queue database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS content_queue (
                id TEXT PRIMARY KEY,
                title TEXT,
                content_data TEXT,
                post_type TEXT,
                content_source TEXT,
                status TEXT,
                priority INTEGER,
                target_publish_time TEXT,
                created_at TEXT,
                updated_at TEXT,
                created_by TEXT,
                approved_by TEXT,
                validation_results TEXT,
                retry_count INTEGER DEFAULT 0,
                tags TEXT,
                notes TEXT,
                performance_prediction REAL DEFAULT 0.0
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS queue_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content_id TEXT,
                action TEXT,
                old_status TEXT,
                new_status TEXT,
                performed_by TEXT,
                timestamp TEXT,
                notes TEXT
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS content_templates (
                id TEXT PRIMARY KEY,
                name TEXT,
                template_type TEXT,
                template_data TEXT,
                created_at TEXT,
                usage_count INTEGER DEFAULT 0,
                average_performance REAL DEFAULT 0.0
            )
        """)
        
        conn.commit()
        conn.close()
    
    def save_queued_content(self, queued_content: QueuedContent):
        """Save queued content to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        content_data = {
            'caption': queued_content.content.caption,
            'media_type': queued_content.content.media_type.value,
            'media_url': queued_content.content.media_url,
            'media_urls': queued_content.content.media_urls,
            'hashtags': queued_content.content.hashtags
        }
        
        cursor.execute("""
            INSERT OR REPLACE INTO content_queue 
            (id, title, content_data, post_type, content_source, status, priority,
             target_publish_time, created_at, updated_at, created_by, approved_by,
             validation_results, retry_count, tags, notes, performance_prediction)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            queued_content.id,
            queued_content.title,
            json.dumps(content_data),
            queued_content.post_type.value,
            queued_content.content_source.value,
            queued_content.status.value,
            queued_content.priority,
            queued_content.target_publish_time.isoformat() if queued_content.target_publish_time else None,
            queued_content.created_at.isoformat(),
            queued_content.updated_at.isoformat(),
            queued_content.created_by,
            queued_content.approved_by,
            json.dumps([asdict(v) for v in queued_content.validation_results]) if queued_content.validation_results else None,
            queued_content.retry_count,
            json.dumps(queued_content.tags) if queued_content.tags else None,
            queued_content.notes,
            queued_content.performance_prediction
        ))
        
        conn.commit()
        conn.close()
    
    def get_queued_content(self, status: QueueStatus = None, limit: int = 50) -> List[QueuedContent]:
        """Get queued content by status"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if status:
            cursor.execute("""
                SELECT * FROM content_queue 
                WHERE status = ? 
                ORDER BY priority DESC, created_at ASC 
                LIMIT ?
            """, (status.value, limit))
        else:
            cursor.execute("""
                SELECT * FROM content_queue 
                ORDER BY priority DESC, created_at ASC 
                LIMIT ?
            """, (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        queued_items = []
        for row in rows:
            # Reconstruct QueuedContent object
            content_data = json.loads(row[2])
            instagram_post = InstagramPost(
                caption=content_data['caption'],
                media_type=MediaType(content_data['media_type']),
                media_url=content_data.get('media_url'),
                media_urls=content_data.get('media_urls'),
                hashtags=content_data.get('hashtags')
            )
            
            validation_results = []
            if row[12]:  # validation_results
                validation_data = json.loads(row[12])
                validation_results = [
                    ContentValidation(
                        rule=ValidationRule(v['rule']),
                        passed=v['passed'],
                        message=v['message'],
                        severity=v['severity']
                    ) for v in validation_data
                ]
            
            queued_content = QueuedContent(
                id=row[0],
                title=row[1],
                content=instagram_post,
                post_type=PostType(row[3]),
                content_source=ContentSource(row[4]),
                status=QueueStatus(row[5]),
                priority=row[6],
                target_publish_time=datetime.fromisoformat(row[7]) if row[7] else None,
                created_at=datetime.fromisoformat(row[8]),
                updated_at=datetime.fromisoformat(row[9]),
                created_by=row[10],
                approved_by=row[11],
                validation_results=validation_results,
                retry_count=row[13],
                tags=json.loads(row[14]) if row[14] else None,
                notes=row[15],
                performance_prediction=row[16]
            )
            
            queued_items.append(queued_content)
        
        return queued_items
    
    def update_status(self, content_id: str, new_status: QueueStatus, 
                     updated_by: str, notes: str = ""):
        """Update content status"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get current status
        cursor.execute("SELECT status FROM content_queue WHERE id = ?", (content_id,))
        result = cursor.fetchone()
        old_status = result[0] if result else None
        
        # Update status
        cursor.execute("""
            UPDATE content_queue 
            SET status = ?, updated_at = ? 
            WHERE id = ?
        """, (new_status.value, datetime.now().isoformat(), content_id))
        
        # Log history
        cursor.execute("""
            INSERT INTO queue_history 
            (content_id, action, old_status, new_status, performed_by, timestamp, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            content_id, "status_change", old_status, new_status.value,
            updated_by, datetime.now().isoformat(), notes
        ))
        
        conn.commit()
        conn.close()


class ContentQueueManager:
    """
    Main content queue management system.
    """
    
    def __init__(self, db_path: str = None):
        self.db = ContentQueueDatabase(db_path)
        self.validator = ContentValidator()
        self.hashtag_optimizer = HashtagOptimizer()
        self.logger = logging.getLogger(__name__)
    
    def add_content(self, title: str, content: InstagramPost, 
                   post_type: PostType, content_source: ContentSource,
                   created_by: str, priority: int = 5,
                   target_publish_time: datetime = None,
                   tags: List[str] = None, notes: str = "") -> str:
        """
        Add new content to the queue.
        """
        
        content_id = str(uuid.uuid4())
        
        # Get existing content for duplicate checking
        existing_content = self.db.get_queued_content()
        
        # Validate content
        validation_results = self.validator.validate_content(content, existing_content)
        
        # Determine initial status based on validation
        has_errors = any(v.passed == False for v in validation_results)
        initial_status = QueueStatus.PENDING_REVIEW if has_errors else QueueStatus.APPROVED
        
        # Optimize hashtags if not provided
        if not content.hashtags:
            content_category = self._determine_content_category(post_type)
            content.hashtags = self.hashtag_optimizer.generate_hashtag_set(
                content_category, target_language="bg", max_hashtags=25
            )
        
        # Create queued content
        queued_content = QueuedContent(
            id=content_id,
            title=title,
            content=content,
            post_type=post_type,
            content_source=content_source,
            status=initial_status,
            priority=priority,
            target_publish_time=target_publish_time,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            created_by=created_by,
            validation_results=validation_results,
            tags=tags,
            notes=notes,
            performance_prediction=self._predict_performance(content, post_type)
        )
        
        # Save to database
        self.db.save_queued_content(queued_content)
        
        self.logger.info(f"Added content to queue: {content_id} - {title}")
        return content_id
    
    def approve_content(self, content_id: str, approved_by: str, 
                       notes: str = "") -> bool:
        """Approve content for scheduling"""
        
        try:
            self.db.update_status(content_id, QueueStatus.APPROVED, approved_by, notes)
            self.logger.info(f"Content approved: {content_id} by {approved_by}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to approve content {content_id}: {e}")
            return False
    
    def reject_content(self, content_id: str, rejected_by: str, 
                      reason: str) -> bool:
        """Reject content"""
        
        try:
            self.db.update_status(content_id, QueueStatus.REJECTED, rejected_by, reason)
            self.logger.info(f"Content rejected: {content_id} by {rejected_by}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to reject content {content_id}: {e}")
            return False
    
    def get_pending_review(self) -> List[QueuedContent]:
        """Get content pending review"""
        return self.db.get_queued_content(QueueStatus.PENDING_REVIEW)
    
    def get_approved_content(self) -> List[QueuedContent]:
        """Get approved content ready for scheduling"""
        return self.db.get_queued_content(QueueStatus.APPROVED)
    
    def get_scheduled_content(self) -> List[QueuedContent]:
        """Get scheduled content"""
        return self.db.get_queued_content(QueueStatus.SCHEDULED)
    
    def mark_as_scheduled(self, content_id: str, scheduled_time: datetime):
        """Mark content as scheduled"""
        self.db.update_status(content_id, QueueStatus.SCHEDULED, "system", 
                             f"Scheduled for {scheduled_time}")
    
    def mark_as_published(self, content_id: str, published_id: str):
        """Mark content as published"""
        self.db.update_status(content_id, QueueStatus.PUBLISHED, "system",
                             f"Published with ID: {published_id}")
    
    def mark_as_failed(self, content_id: str, error_message: str):
        """Mark content as failed"""
        self.db.update_status(content_id, QueueStatus.FAILED, "system", error_message)
    
    def get_queue_statistics(self) -> Dict:
        """Get queue statistics"""
        
        all_content = self.db.get_queued_content(limit=1000)
        
        stats = {
            'total_items': len(all_content),
            'by_status': {},
            'by_type': {},
            'by_source': {},
            'avg_performance_prediction': 0.0,
            'pending_review_count': 0,
            'ready_to_schedule': 0
        }
        
        for content in all_content:
            # Count by status
            status = content.status.value
            stats['by_status'][status] = stats['by_status'].get(status, 0) + 1
            
            # Count by type
            post_type = content.post_type.value
            stats['by_type'][post_type] = stats['by_type'].get(post_type, 0) + 1
            
            # Count by source
            source = content.content_source.value
            stats['by_source'][source] = stats['by_source'].get(source, 0) + 1
            
            # Calculate averages
            stats['avg_performance_prediction'] += content.performance_prediction
            
            if content.status == QueueStatus.PENDING_REVIEW:
                stats['pending_review_count'] += 1
            elif content.status == QueueStatus.APPROVED:
                stats['ready_to_schedule'] += 1
        
        if all_content:
            stats['avg_performance_prediction'] /= len(all_content)
        
        return stats
    
    def _determine_content_category(self, post_type: PostType) -> ContentCategory:
        """Map post type to content category for hashtag optimization"""
        
        mapping = {
            PostType.EDUCATIONAL: ContentCategory.TUTORIAL,
            PostType.SHOWCASE: ContentCategory.AQUASCAPING,
            PostType.TUTORIAL: ContentCategory.TUTORIAL,
            PostType.COMMUNITY: ContentCategory.COMMUNITY,
            PostType.BEHIND_SCENES: ContentCategory.AQUASCAPING,
            PostType.PARTNERSHIP: ContentCategory.COMMUNITY
        }
        
        return mapping.get(post_type, ContentCategory.AQUASCAPING)
    
    def _predict_performance(self, content: InstagramPost, post_type: PostType) -> float:
        """
        Predict content performance based on various factors.
        This is a simplified implementation - in production would use ML models.
        """
        
        score = 50.0  # Base score
        
        # Caption length factor
        caption_length = len(content.caption)
        if 100 <= caption_length <= 500:
            score += 10
        elif caption_length > 1000:
            score -= 5
        
        # Hashtag count factor
        hashtag_count = len(content.hashtags) if content.hashtags else 0
        if 15 <= hashtag_count <= 25:
            score += 15
        elif hashtag_count < 5:
            score -= 10
        
        # Post type factor
        type_multipliers = {
            PostType.SHOWCASE: 1.2,
            PostType.EDUCATIONAL: 1.1,
            PostType.TUTORIAL: 1.15,
            PostType.COMMUNITY: 1.0,
            PostType.BEHIND_SCENES: 0.9,
            PostType.PARTNERSHIP: 0.95
        }
        
        score *= type_multipliers.get(post_type, 1.0)
        
        # Media type factor
        if content.media_type == MediaType.CAROUSEL_ALBUM:
            score += 5
        
        return min(max(score, 0), 100)  # Clamp between 0-100


# Usage example
if __name__ == "__main__":
    
    # Initialize queue manager
    queue_manager = ContentQueueManager()
    
    # Create sample content
    sample_content = InstagramPost(
        caption="Beautiful aquascape setup with Anubias and Java fern! 🌱 Perfect for beginners.",
        media_type=MediaType.IMAGE,
        media_url="https://example.com/aquascape.jpg",
        hashtags=["aquascaping", "plantedtank", "beginner", "аквариум", "растения"]
    )
    
    # Add to queue
    content_id = queue_manager.add_content(
        title="Beginner Aquascape Setup",
        content=sample_content,
        post_type=PostType.EDUCATIONAL,
        content_source=ContentSource.MANUAL,
        created_by="content_creator",
        priority=7,
        tags=["beginner", "tutorial", "plants"]
    )
    
    print(f"Added content with ID: {content_id}")
    
    # Get queue statistics
    stats = queue_manager.get_queue_statistics()
    print(f"Queue statistics: {stats}")
    
    # Get pending review items
    pending = queue_manager.get_pending_review()
    print(f"Pending review: {len(pending)} items")