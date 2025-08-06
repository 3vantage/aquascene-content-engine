"""
Airtable Integration Service
Connects Airtable data with database operations
"""
import uuid
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from sqlalchemy.ext.asyncio import AsyncSession

from ..crud.content import content_crud, raw_content_crud, category_crud, tag_crud
from ..crud.subscriber import subscriber_crud, segment_crud, preference_crud
from ..crud.newsletter import newsletter_crud, newsletter_template_crud
from ..schemas.content import GeneratedContentCreate, RawContentCreate
from ..schemas.subscriber import SubscriberCreate
from ..schemas.newsletter import NewsletterIssueCreate, NewsletterTemplateCreate
from ..config.settings import get_settings

logger = logging.getLogger(__name__)


class AirtableIntegrationService:
    """Service for integrating Airtable data with database operations"""
    
    def __init__(self):
        self.settings = get_settings()
    
    async def sync_content_from_airtable(
        self,
        session: AsyncSession,
        airtable_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Sync content from Airtable analysis to database
        
        Args:
            session: Database session
            airtable_data: Data from Airtable schema analysis
            
        Returns:
            Dictionary with sync results
        """
        results = {
            'content_created': 0,
            'subscribers_created': 0,
            'categories_created': 0,
            'tags_created': 0,
            'newsletters_created': 0,
            'errors': []
        }
        
        try:
            # Process content from Airtable
            if 'content' in airtable_data:
                content_results = await self._sync_content_records(
                    session, airtable_data['content']
                )
                results['content_created'] = content_results['created']
                results['errors'].extend(content_results['errors'])
            
            # Process subscribers
            if 'subscribers' in airtable_data:
                subscriber_results = await self._sync_subscriber_records(
                    session, airtable_data['subscribers']
                )
                results['subscribers_created'] = subscriber_results['created']
                results['errors'].extend(subscriber_results['errors'])
            
            # Process categories
            if 'categories' in airtable_data:
                category_results = await self._sync_category_records(
                    session, airtable_data['categories']
                )
                results['categories_created'] = category_results['created']
                results['errors'].extend(category_results['errors'])
            
            # Process newsletters
            if 'newsletters' in airtable_data:
                newsletter_results = await self._sync_newsletter_records(
                    session, airtable_data['newsletters']
                )
                results['newsletters_created'] = newsletter_results['created']
                results['errors'].extend(newsletter_results['errors'])
            
            logger.info(f"Airtable sync completed: {results}")
            return results
            
        except Exception as e:
            logger.error(f"Failed to sync Airtable data: {str(e)}")
            results['errors'].append(f"General sync error: {str(e)}")
            return results
    
    async def _sync_content_records(
        self,
        session: AsyncSession,
        content_records: List[Dict]
    ) -> Dict[str, Any]:
        """Sync content records from Airtable"""
        created_count = 0
        errors = []
        
        for record in content_records:
            try:
                # Map Airtable fields to database fields
                content_data = self._map_airtable_content(record)
                
                if content_data:
                    # Check if content already exists
                    existing = await content_crud.get_multi(
                        session, 
                        filters={'title': content_data['title']},
                        limit=1
                    )
                    
                    if not existing:
                        content_create = GeneratedContentCreate(**content_data)
                        await content_crud.create(session, obj_in=content_create)
                        created_count += 1
                        logger.debug(f"Created content: {content_data['title']}")
                    else:
                        logger.debug(f"Content already exists: {content_data['title']}")
                        
            except Exception as e:
                error_msg = f"Failed to create content from record {record.get('id', 'unknown')}: {str(e)}"
                errors.append(error_msg)
                logger.error(error_msg)
        
        return {'created': created_count, 'errors': errors}
    
    async def _sync_subscriber_records(
        self,
        session: AsyncSession,
        subscriber_records: List[Dict]
    ) -> Dict[str, Any]:
        """Sync subscriber records from Airtable"""
        created_count = 0
        errors = []
        
        for record in subscriber_records:
            try:
                subscriber_data = self._map_airtable_subscriber(record)
                
                if subscriber_data and subscriber_data.get('email'):
                    # Check if subscriber already exists
                    existing = await subscriber_crud.get_by_email(
                        session, subscriber_data['email']
                    )
                    
                    if not existing:
                        subscriber_create = SubscriberCreate(**subscriber_data)
                        subscriber = await subscriber_crud.create(
                            session, obj_in=subscriber_create
                        )
                        
                        # Create default preferences
                        await preference_crud.create_default_preferences(
                            session, subscriber.id
                        )
                        
                        created_count += 1
                        logger.debug(f"Created subscriber: {subscriber_data['email']}")
                    else:
                        logger.debug(f"Subscriber already exists: {subscriber_data['email']}")
                        
            except Exception as e:
                error_msg = f"Failed to create subscriber from record {record.get('id', 'unknown')}: {str(e)}"
                errors.append(error_msg)
                logger.error(error_msg)
        
        return {'created': created_count, 'errors': errors}
    
    async def _sync_category_records(
        self,
        session: AsyncSession,
        category_records: List[Dict]
    ) -> Dict[str, Any]:
        """Sync category records from Airtable"""
        created_count = 0
        errors = []
        
        for record in category_records:
            try:
                category_data = self._map_airtable_category(record)
                
                if category_data and category_data.get('name'):
                    # Check if category already exists
                    existing = await category_crud.get_multi(
                        session,
                        filters={'name': category_data['name']},
                        limit=1
                    )
                    
                    if not existing:
                        await category_crud.create(session, obj_in=category_data)
                        created_count += 1
                        logger.debug(f"Created category: {category_data['name']}")
                    else:
                        logger.debug(f"Category already exists: {category_data['name']}")
                        
            except Exception as e:
                error_msg = f"Failed to create category from record {record.get('id', 'unknown')}: {str(e)}"
                errors.append(error_msg)
                logger.error(error_msg)
        
        return {'created': created_count, 'errors': errors}
    
    async def _sync_newsletter_records(
        self,
        session: AsyncSession,
        newsletter_records: List[Dict]
    ) -> Dict[str, Any]:
        """Sync newsletter records from Airtable"""
        created_count = 0
        errors = []
        
        for record in newsletter_records:
            try:
                newsletter_data = self._map_airtable_newsletter(record)
                
                if newsletter_data and newsletter_data.get('subject_line'):
                    # Check if newsletter already exists
                    existing = await newsletter_crud.get_multi(
                        session,
                        filters={'subject_line': newsletter_data['subject_line']},
                        limit=1
                    )
                    
                    if not existing:
                        newsletter_create = NewsletterIssueCreate(**newsletter_data)
                        await newsletter_crud.create(session, obj_in=newsletter_create)
                        created_count += 1
                        logger.debug(f"Created newsletter: {newsletter_data['subject_line']}")
                    else:
                        logger.debug(f"Newsletter already exists: {newsletter_data['subject_line']}")
                        
            except Exception as e:
                error_msg = f"Failed to create newsletter from record {record.get('id', 'unknown')}: {str(e)}"
                errors.append(error_msg)
                logger.error(error_msg)
        
        return {'created': created_count, 'errors': errors}
    
    def _map_airtable_content(self, record: Dict) -> Optional[Dict]:
        """Map Airtable content record to database format"""
        try:
            fields = record.get('fields', {})
            
            # Extract common fields
            title = fields.get('Title') or fields.get('title') or fields.get('Name')
            content = fields.get('Content') or fields.get('content') or fields.get('Body')
            
            if not title or not content:
                return None
            
            return {
                'content_type': fields.get('Type', 'article').lower(),
                'title': str(title),
                'content': str(content),
                'summary': fields.get('Summary') or fields.get('summary'),
                'excerpt': fields.get('Excerpt') or fields.get('excerpt'),
                'tags': self._extract_tags(fields.get('Tags', [])),
                'categories': self._extract_categories(fields.get('Categories', [])),
                'target_audience': fields.get('Audience', 'general'),
                'tone': fields.get('Tone', 'educational'),
                'status': fields.get('Status', 'draft').lower()
            }
            
        except Exception as e:
            logger.error(f"Failed to map Airtable content record: {str(e)}")
            return None
    
    def _map_airtable_subscriber(self, record: Dict) -> Optional[Dict]:
        """Map Airtable subscriber record to database format"""
        try:
            fields = record.get('fields', {})
            
            email = fields.get('Email') or fields.get('email')
            if not email:
                return None
            
            return {
                'email': str(email),
                'first_name': fields.get('First Name') or fields.get('first_name'),
                'last_name': fields.get('Last Name') or fields.get('last_name'),
                'country': fields.get('Country') or fields.get('country'),
                'source': fields.get('Source', 'airtable'),
                'tags': self._extract_tags(fields.get('Tags', [])),
                'status': fields.get('Status', 'active').lower()
            }
            
        except Exception as e:
            logger.error(f"Failed to map Airtable subscriber record: {str(e)}")
            return None
    
    def _map_airtable_category(self, record: Dict) -> Optional[Dict]:
        """Map Airtable category record to database format"""
        try:
            fields = record.get('fields', {})
            
            name = fields.get('Name') or fields.get('name') or fields.get('Category')
            if not name:
                return None
            
            slug = str(name).lower().replace(' ', '-').replace('_', '-')
            
            return {
                'name': str(name),
                'slug': slug,
                'description': fields.get('Description') or fields.get('description'),
                'is_active': fields.get('Active', True)
            }
            
        except Exception as e:
            logger.error(f"Failed to map Airtable category record: {str(e)}")
            return None
    
    def _map_airtable_newsletter(self, record: Dict) -> Optional[Dict]:
        """Map Airtable newsletter record to database format"""
        try:
            fields = record.get('fields', {})
            
            subject = fields.get('Subject') or fields.get('subject') or fields.get('Subject Line')
            if not subject:
                return None
            
            # Extract content IDs if they exist
            content_ids = []
            content_refs = fields.get('Content', []) or fields.get('content', [])
            if isinstance(content_refs, list):
                # In a real implementation, you'd map Airtable record IDs to database UUIDs
                content_ids = [str(uuid.uuid4()) for _ in content_refs[:5]]  # Placeholder
            
            return {
                'template_type': fields.get('Type', 'weekly_digest'),
                'subject_line': str(subject),
                'preview_text': fields.get('Preview') or fields.get('preview_text'),
                'content_ids': content_ids,
                'status': fields.get('Status', 'draft').lower()
            }
            
        except Exception as e:
            logger.error(f"Failed to map Airtable newsletter record: {str(e)}")
            return None
    
    def _extract_tags(self, tags_field) -> List[str]:
        """Extract and clean tags from Airtable field"""
        if not tags_field:
            return []
        
        if isinstance(tags_field, str):
            # Split by common separators
            tags = tags_field.replace(',', ';').split(';')
            return [tag.strip().lower() for tag in tags if tag.strip()]
        elif isinstance(tags_field, list):
            return [str(tag).strip().lower() for tag in tags_field if str(tag).strip()]
        
        return []
    
    def _extract_categories(self, categories_field) -> List[str]:
        """Extract and clean categories from Airtable field"""
        if not categories_field:
            return []
        
        if isinstance(categories_field, str):
            categories = categories_field.replace(',', ';').split(';')
            return [cat.strip() for cat in categories if cat.strip()]
        elif isinstance(categories_field, list):
            return [str(cat).strip() for cat in categories_field if str(cat).strip()]
        
        return []
    
    async def export_database_to_airtable_format(
        self,
        session: AsyncSession,
        export_type: str = 'content'
    ) -> Dict[str, Any]:
        """
        Export database records to Airtable-compatible format
        
        Args:
            session: Database session
            export_type: Type of data to export ('content', 'subscribers', 'newsletters')
            
        Returns:
            Dictionary with exported data in Airtable format
        """
        try:
            if export_type == 'content':
                return await self._export_content_to_airtable_format(session)
            elif export_type == 'subscribers':
                return await self._export_subscribers_to_airtable_format(session)
            elif export_type == 'newsletters':
                return await self._export_newsletters_to_airtable_format(session)
            else:
                return {'error': f'Unsupported export type: {export_type}'}
                
        except Exception as e:
            logger.error(f"Failed to export {export_type} to Airtable format: {str(e)}")
            return {'error': str(e)}
    
    async def _export_content_to_airtable_format(self, session: AsyncSession) -> Dict[str, Any]:
        """Export content to Airtable format"""
        content_items = await content_crud.get_multi(session, limit=1000)
        
        records = []
        for content in content_items:
            records.append({
                'id': str(content.id),
                'fields': {
                    'Title': content.title,
                    'Content': content.content,
                    'Type': content.content_type,
                    'Status': content.status,
                    'Summary': content.summary,
                    'Excerpt': content.excerpt,
                    'Tags': content.tags or [],
                    'Categories': content.categories or [],
                    'Created': content.created_at.isoformat(),
                    'Updated': content.updated_at.isoformat(),
                    'Quality Score': float(content.quality_score or 0),
                    'Readability Score': content.readability_score or 0,
                    'SEO Score': float(content.seo_score or 0)
                }
            })
        
        return {
            'table_name': 'Content',
            'records': records,
            'total_records': len(records)
        }
    
    async def _export_subscribers_to_airtable_format(self, session: AsyncSession) -> Dict[str, Any]:
        """Export subscribers to Airtable format"""
        subscribers = await subscriber_crud.get_multi(session, limit=5000)
        
        records = []
        for subscriber in subscribers:
            records.append({
                'id': str(subscriber.id),
                'fields': {
                    'Email': subscriber.email,
                    'First Name': subscriber.first_name,
                    'Last Name': subscriber.last_name,
                    'Country': subscriber.country,
                    'Status': subscriber.status,
                    'Source': subscriber.source,
                    'Tags': subscriber.tags or [],
                    'Subscription Date': subscriber.subscription_date.isoformat(),
                    'Last Activity': subscriber.last_activity_at.isoformat()
                }
            })
        
        return {
            'table_name': 'Subscribers',
            'records': records,
            'total_records': len(records)
        }
    
    async def _export_newsletters_to_airtable_format(self, session: AsyncSession) -> Dict[str, Any]:
        """Export newsletters to Airtable format"""
        newsletters = await newsletter_crud.get_multi(session, limit=500)
        
        records = []
        for newsletter in newsletters:
            records.append({
                'id': str(newsletter.id),
                'fields': {
                    'Subject': newsletter.subject_line,
                    'Type': newsletter.template_type,
                    'Status': newsletter.status,
                    'Issue Number': newsletter.issue_number,
                    'Preview Text': newsletter.preview_text,
                    'Recipients': newsletter.recipient_count,
                    'Created': newsletter.created_at.isoformat(),
                    'Scheduled For': newsletter.scheduled_for.isoformat() if newsletter.scheduled_for else None,
                    'Sent At': newsletter.sent_at.isoformat() if newsletter.sent_at else None
                }
            })
        
        return {
            'table_name': 'Newsletters',
            'records': records,
            'total_records': len(records)
        }


# Global service instance
airtable_integration = AirtableIntegrationService()