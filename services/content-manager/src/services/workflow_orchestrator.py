"""
Workflow Orchestrator Service
Coordinates content workflows and integrates with AI processor
"""
import uuid
import logging
import httpx
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession

from ..crud.content import content_crud, raw_content_crud
from ..crud.newsletter import newsletter_crud
from ..models.content import GeneratedContent, RawContent
from ..schemas.content import GeneratedContentCreate
from ..services.content_lifecycle import content_lifecycle_service, ContentStatus
from ..services.content_scheduler import content_scheduler
from ..config.settings import get_settings

logger = logging.getLogger(__name__)


class WorkflowOrchestrator:
    """Service for orchestrating content workflows and AI processing"""
    
    def __init__(self):
        self.settings = get_settings()
        self.ai_processor_url = "http://ai-processor:8001"  # Default AI processor URL
    
    async def process_raw_content_batch(
        self,
        session: AsyncSession,
        batch_size: int = 10
    ) -> Dict[str, Any]:
        """Process a batch of raw content through the AI pipeline"""
        try:
            # Get unprocessed raw content
            raw_content_batch = await raw_content_crud.get_unprocessed(session, batch_size)
            
            if not raw_content_batch:
                return {
                    'processed': 0,
                    'failed': 0,
                    'message': 'No raw content to process'
                }
            
            processed_count = 0
            failed_count = 0
            
            for raw_content in raw_content_batch:
                success = await self._process_single_raw_content(session, raw_content)
                
                if success:
                    processed_count += 1
                else:
                    failed_count += 1
            
            logger.info(f"Processed batch: {processed_count} successful, {failed_count} failed")
            
            return {
                'processed': processed_count,
                'failed': failed_count,
                'total': len(raw_content_batch)
            }
            
        except Exception as e:
            logger.error(f"Failed to process raw content batch: {str(e)}")
            return {
                'processed': 0,
                'failed': 0,
                'error': str(e)
            }
    
    async def _process_single_raw_content(
        self,
        session: AsyncSession,
        raw_content: RawContent
    ) -> bool:
        """Process single raw content item through AI processor"""
        try:
            # Mark as processing
            await raw_content_crud.mark_processed(
                session, 
                raw_content.id, 
                'processing'
            )
            
            # Send to AI processor
            ai_response = await self._call_ai_processor(raw_content)
            
            if ai_response and ai_response.get('success'):
                generated_content_data = ai_response.get('content')
                
                # Create generated content
                content_create = GeneratedContentCreate(
                    content_type=generated_content_data.get('content_type', 'article'),
                    title=generated_content_data.get('title'),
                    content=generated_content_data.get('content'),
                    summary=generated_content_data.get('summary'),
                    excerpt=generated_content_data.get('excerpt'),
                    source_materials=[str(raw_content.id)],
                    quality_score=generated_content_data.get('quality_score'),
                    readability_score=generated_content_data.get('readability_score'),
                    seo_score=generated_content_data.get('seo_score'),
                    tags=generated_content_data.get('tags', []),
                    categories=generated_content_data.get('categories', []),
                    target_audience=generated_content_data.get('target_audience'),
                    tone=generated_content_data.get('tone')
                )
                
                generated_content = await content_crud.create(session, obj_in=content_create)
                
                # Mark raw content as processed
                await raw_content_crud.mark_processed(
                    session,
                    raw_content.id,
                    'completed'
                )
                
                logger.info(f"Generated content {generated_content.id} from raw content {raw_content.id}")
                return True
            else:
                error_message = ai_response.get('error', 'Unknown AI processing error')
                await raw_content_crud.mark_processed(
                    session,
                    raw_content.id,
                    'failed',
                    error_message
                )
                return False
                
        except Exception as e:
            logger.error(f"Failed to process raw content {raw_content.id}: {str(e)}")
            await raw_content_crud.mark_processed(
                session,
                raw_content.id,
                'failed',
                str(e)
            )
            return False
    
    async def _call_ai_processor(self, raw_content: RawContent) -> Optional[Dict]:
        """Call AI processor service to generate content"""
        try:
            async with httpx.AsyncClient() as client:
                payload = {
                    'source_content': {
                        'title': raw_content.title,
                        'content': raw_content.content,
                        'source_url': raw_content.source_url,
                        'source_domain': raw_content.source_domain,
                        'content_type': raw_content.content_type,
                        'metadata': raw_content.metadata
                    },
                    'generation_options': {
                        'target_formats': ['newsletter_article', 'social_post'],
                        'optimize_for_seo': True,
                        'include_summary': True,
                        'target_audience': 'aquascaping_enthusiasts'
                    }
                }
                
                response = await client.post(
                    f"{self.ai_processor_url}/api/v1/generate/content",
                    json=payload,
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    logger.error(f"AI processor returned {response.status_code}: {response.text}")
                    return None
                    
        except httpx.TimeoutException:
            logger.error("AI processor request timed out")
            return None
        except Exception as e:
            logger.error(f"Failed to call AI processor: {str(e)}")
            return None
    
    async def create_newsletter_workflow(
        self,
        session: AsyncSession,
        template_type: str = 'weekly_digest',
        content_filters: Optional[Dict] = None,
        user_id: Optional[uuid.UUID] = None
    ) -> Dict[str, Any]:
        """Create and schedule a newsletter workflow"""
        try:
            # Get published content for newsletter
            if not content_filters:
                content_filters = {
                    'status': 'published',
                    'content_type': 'newsletter_article'
                }
            
            content_items = await content_crud.get_multi(
                session, 
                limit=10,
                filters=content_filters
            )
            
            if not content_items:
                return {
                    'success': False,
                    'error': 'No suitable content found for newsletter'
                }
            
            # Create newsletter issue
            content_ids = [item.id for item in content_items[:5]]  # Top 5 articles
            
            issue_number = await newsletter_crud.get_next_issue_number(session)
            
            newsletter_create = {
                'issue_number': issue_number,
                'template_type': template_type,
                'subject_line': f'AquaScene Weekly Digest #{issue_number}',
                'preview_text': 'Your weekly dose of aquascaping inspiration and tips',
                'content_ids': content_ids,
                'created_by': user_id
            }
            
            newsletter_issue = await newsletter_crud.create(
                session, 
                obj_in=newsletter_create
            )
            
            # Schedule newsletter for optimal send time
            success, scheduled_issue, error = await content_scheduler.schedule_newsletter_campaign(
                session,
                newsletter_issue.id,
                frequency='weekly'
            )
            
            if not success:
                return {
                    'success': False,
                    'error': f'Failed to schedule newsletter: {error}'
                }
            
            return {
                'success': True,
                'newsletter_issue_id': str(newsletter_issue.id),
                'scheduled_for': scheduled_issue.scheduled_for.isoformat(),
                'content_count': len(content_ids)
            }
            
        except Exception as e:
            logger.error(f"Failed to create newsletter workflow: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def auto_approve_high_quality_content(
        self,
        session: AsyncSession,
        quality_threshold: float = 0.85,
        user_id: Optional[uuid.UUID] = None
    ) -> Dict[str, Any]:
        """Automatically approve content that meets quality thresholds"""
        try:
            # Get content in review status with high quality scores
            review_content = await content_crud.get_by_status(
                session, 
                ContentStatus.REVIEW.value
            )
            
            approved_count = 0
            
            for content in review_content:
                if (content.quality_score and 
                    content.quality_score >= quality_threshold and
                    content.readability_score and 
                    content.readability_score >= 70):
                    
                    success, _, error = await content_lifecycle_service.transition_content_status(
                        session,
                        content.id,
                        ContentStatus.APPROVED.value,
                        user_id,
                        notes=f"Auto-approved: quality_score={content.quality_score}"
                    )
                    
                    if success:
                        approved_count += 1
            
            return {
                'approved_count': approved_count,
                'reviewed_count': len(review_content),
                'quality_threshold': quality_threshold
            }
            
        except Exception as e:
            logger.error(f"Failed to auto-approve content: {str(e)}")
            return {
                'approved_count': 0,
                'error': str(e)
            }
    
    async def create_content_series_workflow(
        self,
        session: AsyncSession,
        series_topic: str,
        content_count: int = 5,
        publishing_frequency_days: int = 3,
        user_id: Optional[uuid.UUID] = None
    ) -> Dict[str, Any]:
        """Create a workflow for generating and scheduling a content series"""
        try:
            # This would typically call AI processor to generate a series
            # For now, we'll create placeholder content
            
            series_results = {
                'created_content': [],
                'scheduled_posts': [],
                'series_topic': series_topic
            }
            
            base_schedule_time = await content_scheduler.get_optimal_publish_time(
                session, 
                'article',
                'beginners'
            )
            
            for i in range(content_count):
                # Create content placeholder
                content_create = GeneratedContentCreate(
                    content_type='article',
                    title=f"{series_topic} - Part {i+1}",
                    content=f"Content for {series_topic} series, part {i+1}",
                    summary=f"Part {i+1} of our {series_topic} series",
                    tags=[series_topic.lower().replace(' ', '_'), 'series'],
                    target_audience='beginners'
                )
                
                content = await content_crud.create(session, obj_in=content_create)
                
                # Schedule for publishing
                schedule_time = base_schedule_time + timedelta(days=i * publishing_frequency_days)
                
                success, scheduled_content, error = await content_scheduler.schedule_content(
                    session,
                    content.id,
                    schedule_time,
                    user_id
                )
                
                if success:
                    series_results['created_content'].append({
                        'content_id': str(content.id),
                        'title': content.title,
                        'part_number': i + 1
                    })
                    
                    series_results['scheduled_posts'].append({
                        'content_id': str(content.id),
                        'scheduled_for': schedule_time.isoformat(),
                        'part_number': i + 1
                    })
            
            return series_results
            
        except Exception as e:
            logger.error(f"Failed to create content series workflow: {str(e)}")
            return {
                'error': str(e),
                'series_topic': series_topic
            }
    
    async def get_workflow_status(self, session: AsyncSession) -> Dict[str, Any]:
        """Get overall workflow status and metrics"""
        try:
            # Get content lifecycle statistics
            lifecycle_stats = await content_lifecycle_service.get_content_statistics(session)
            
            # Get processing queue status
            unprocessed_raw = await raw_content_crud.get_unprocessed(session, limit=1000)
            
            # Get scheduled content
            publishing_queue = await content_scheduler.get_publishing_queue(session, 48)
            
            return {
                'content_lifecycle': lifecycle_stats,
                'processing_queue': {
                    'unprocessed_raw_content': len(unprocessed_raw),
                    'publishing_queue_items': sum(len(items) for items in publishing_queue.values())
                },
                'scheduled_publications': publishing_queue,
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get workflow status: {str(e)}")
            return {
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }


# Global service instance
workflow_orchestrator = WorkflowOrchestrator()

# Import timedelta
from datetime import timedelta