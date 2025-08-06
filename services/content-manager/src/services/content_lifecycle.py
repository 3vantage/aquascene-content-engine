"""
Content Lifecycle Management Service
Handles content state transitions and workflow automation
"""
import uuid
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
from sqlalchemy.ext.asyncio import AsyncSession

from ..crud.content import content_crud
from ..models.content import GeneratedContent
from ..models.audit import AuditLog, SystemEvent
from ..schemas.content import GeneratedContentUpdate

logger = logging.getLogger(__name__)


class ContentStatus(Enum):
    """Content lifecycle states"""
    DRAFT = "draft"
    REVIEW = "review"  
    APPROVED = "approved"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class ContentLifecycleService:
    """Service for managing content lifecycle and state transitions"""
    
    def __init__(self):
        self.valid_transitions = {
            ContentStatus.DRAFT: [ContentStatus.REVIEW, ContentStatus.ARCHIVED],
            ContentStatus.REVIEW: [ContentStatus.DRAFT, ContentStatus.APPROVED, ContentStatus.ARCHIVED],
            ContentStatus.APPROVED: [ContentStatus.PUBLISHED, ContentStatus.REVIEW, ContentStatus.ARCHIVED],
            ContentStatus.PUBLISHED: [ContentStatus.ARCHIVED],
            ContentStatus.ARCHIVED: [ContentStatus.DRAFT]
        }
    
    async def transition_content_status(
        self,
        session: AsyncSession,
        content_id: uuid.UUID,
        new_status: str,
        user_id: Optional[uuid.UUID] = None,
        notes: Optional[str] = None
    ) -> tuple[bool, Optional[GeneratedContent], Optional[str]]:
        """
        Transition content to new status with validation and audit logging
        
        Returns: (success, content, error_message)
        """
        try:
            # Get current content
            content = await content_crud.get(session, content_id)
            if not content:
                return False, None, "Content not found"
            
            current_status = ContentStatus(content.status)
            target_status = ContentStatus(new_status)
            
            # Validate transition
            if target_status not in self.valid_transitions[current_status]:
                valid_states = [s.value for s in self.valid_transitions[current_status]]
                return False, None, f"Invalid transition from {current_status.value} to {new_status}. Valid transitions: {valid_states}"
            
            # Store old data for audit
            old_data = {
                'status': content.status,
                'approved_by': content.approved_by,
                'approved_at': content.approved_at,
                'published_at': content.published_at
            }
            
            # Perform status-specific logic
            update_data = {'status': new_status}
            
            if target_status == ContentStatus.APPROVED:
                update_data.update({
                    'approved_by': user_id,
                    'approved_at': datetime.utcnow()
                })
                
                # Auto-schedule if no schedule date set
                if not content.scheduled_for:
                    # Schedule for immediate publication or next business day
                    update_data['scheduled_for'] = datetime.utcnow()
            
            elif target_status == ContentStatus.PUBLISHED:
                if not content.published_at:
                    update_data['published_at'] = datetime.utcnow()
            
            elif target_status == ContentStatus.REVIEW:
                # Clear approval data when moving back to review
                update_data.update({
                    'approved_by': None,
                    'approved_at': None
                })
            
            # Update content
            updated_content = await content_crud.update(
                session, 
                db_obj=content, 
                obj_in=update_data
            )
            
            # Create audit log
            await self._create_audit_log(
                session,
                table_name='generated_content',
                record_id=str(content_id),
                action='status_change',
                old_data=old_data,
                new_data={k: getattr(updated_content, k) for k in update_data.keys()},
                changed_by=user_id,
                notes=notes
            )
            
            # Create system event
            await self._create_system_event(
                session,
                event_type='content_lifecycle',
                event_name=f'content_{new_status}',
                event_data={
                    'content_id': str(content_id),
                    'title': updated_content.title,
                    'from_status': current_status.value,
                    'to_status': new_status,
                    'user_id': str(user_id) if user_id else None,
                    'notes': notes
                },
                severity='info'
            )
            
            logger.info(f"Content {content_id} transitioned from {current_status.value} to {new_status}")
            
            return True, updated_content, None
            
        except Exception as e:
            logger.error(f"Failed to transition content {content_id} to {new_status}: {str(e)}")
            return False, None, str(e)
    
    async def bulk_transition_content(
        self,
        session: AsyncSession,
        content_ids: List[uuid.UUID],
        new_status: str,
        user_id: Optional[uuid.UUID] = None
    ) -> Dict[str, Any]:
        """
        Bulk transition multiple content items
        
        Returns summary of successes and failures
        """
        results = {
            'successful': [],
            'failed': [],
            'total': len(content_ids)
        }
        
        for content_id in content_ids:
            success, content, error = await self.transition_content_status(
                session, content_id, new_status, user_id
            )
            
            if success:
                results['successful'].append({
                    'content_id': str(content_id),
                    'title': content.title if content else None
                })
            else:
                results['failed'].append({
                    'content_id': str(content_id),
                    'error': error
                })
        
        # Create summary event
        await self._create_system_event(
            session,
            event_type='content_lifecycle',
            event_name='bulk_status_change',
            event_data={
                'new_status': new_status,
                'successful_count': len(results['successful']),
                'failed_count': len(results['failed']),
                'user_id': str(user_id) if user_id else None
            },
            severity='info'
        )
        
        return results
    
    async def get_content_ready_for_review(
        self,
        session: AsyncSession,
        limit: int = 50
    ) -> List[GeneratedContent]:
        """Get content that needs review"""
        return await content_crud.get_by_status(session, ContentStatus.DRAFT.value, limit=limit)
    
    async def get_content_ready_for_approval(
        self,
        session: AsyncSession,
        limit: int = 50
    ) -> List[GeneratedContent]:
        """Get content that needs approval"""
        return await content_crud.get_by_status(session, ContentStatus.REVIEW.value, limit=limit)
    
    async def get_approved_content_for_publishing(
        self,
        session: AsyncSession,
        limit: int = 50
    ) -> List[GeneratedContent]:
        """Get approved content ready for publishing"""
        return await content_crud.get_scheduled_content(session, datetime.utcnow())
    
    async def auto_publish_scheduled_content(
        self,
        session: AsyncSession,
        user_id: Optional[uuid.UUID] = None
    ) -> Dict[str, Any]:
        """
        Automatically publish content that's scheduled for publication
        
        This should be run periodically by a background task
        """
        scheduled_content = await self.get_approved_content_for_publishing(session)
        
        published_count = 0
        failed_count = 0
        
        for content in scheduled_content:
            success, _, error = await self.transition_content_status(
                session, 
                content.id, 
                ContentStatus.PUBLISHED.value, 
                user_id,
                notes="Automatically published on schedule"
            )
            
            if success:
                published_count += 1
            else:
                failed_count += 1
                logger.error(f"Failed to auto-publish content {content.id}: {error}")
        
        # Log summary
        if published_count > 0 or failed_count > 0:
            await self._create_system_event(
                session,
                event_type='content_lifecycle',
                event_name='auto_publish_batch',
                event_data={
                    'published_count': published_count,
                    'failed_count': failed_count,
                    'total_scheduled': len(scheduled_content)
                },
                severity='info' if failed_count == 0 else 'warning'
            )
        
        return {
            'published_count': published_count,
            'failed_count': failed_count,
            'total_scheduled': len(scheduled_content)
        }
    
    async def get_content_statistics(
        self,
        session: AsyncSession
    ) -> Dict[str, Any]:
        """Get content lifecycle statistics"""
        stats = {}
        
        for status in ContentStatus:
            count = await content_crud.count(session, filters={'status': status.value})
            stats[status.value] = count
        
        # Get scheduled content count
        scheduled_count = await content_crud.count(
            session, 
            filters={'status': ContentStatus.APPROVED.value}
        )
        stats['scheduled_for_publishing'] = scheduled_count
        
        return stats
    
    async def _create_audit_log(
        self,
        session: AsyncSession,
        table_name: str,
        record_id: str,
        action: str,
        old_data: Optional[Dict] = None,
        new_data: Optional[Dict] = None,
        changed_by: Optional[uuid.UUID] = None,
        notes: Optional[str] = None
    ):
        """Create audit log entry"""
        audit_log = AuditLog(
            table_name=table_name,
            record_id=record_id,
            action=action,
            old_data=old_data or {},
            new_data=new_data or {},
            changed_by=changed_by,
            user_agent=notes  # Using user_agent field for notes temporarily
        )
        session.add(audit_log)
        await session.commit()
    
    async def _create_system_event(
        self,
        session: AsyncSession,
        event_type: str,
        event_name: str,
        event_data: Dict[str, Any],
        severity: str = 'info'
    ):
        """Create system event entry"""
        event = SystemEvent(
            event_type=event_type,
            event_name=event_name,
            event_data=event_data,
            severity=severity,
            service_name='content-manager'
        )
        session.add(event)
        await session.commit()


# Global service instance
content_lifecycle_service = ContentLifecycleService()