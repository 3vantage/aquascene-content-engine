"""
Subscriber service for the Subscriber Manager Service
"""

import asyncpg
import uuid
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Tuple
import logging

from ..config.settings import get_settings
from ..database.connection import get_db_connection
from .email_service import EmailService

logger = logging.getLogger(__name__)
settings = get_settings()


class SubscriberService:
    """Subscriber service class"""
    
    def __init__(self):
        self.email_service = EmailService()
    
    async def subscribe(
        self,
        email: str,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        interests: List[str] = None
    ) -> str:
        """Subscribe a new user"""
        try:
            conn = await get_db_connection()
            
            # Check if already subscribed
            existing = await conn.fetchrow(
                "SELECT id, status FROM subscribers WHERE email = $1",
                email.lower()
            )
            
            if existing:
                if existing['status'] == 'active':
                    raise ValueError("Email already subscribed")
                elif existing['status'] == 'pending':
                    raise ValueError("Subscription pending confirmation")
            
            # Generate confirmation token
            confirmation_token = secrets.token_urlsafe(32)
            token_expires = datetime.utcnow() + timedelta(hours=settings.CONFIRM_EMAIL_EXPIRE_HOURS)
            
            # Insert or update subscriber
            if existing:
                subscriber_id = existing['id']
                await conn.execute(
                    """
                    UPDATE subscribers 
                    SET first_name = $2, last_name = $3, interests = $4, 
                        confirmation_token = $5, token_expires = $6,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = $1
                    """,
                    subscriber_id, first_name, last_name, interests or [],
                    confirmation_token, token_expires
                )
            else:
                subscriber_id = await conn.fetchval(
                    """
                    INSERT INTO subscribers (
                        email, first_name, last_name, interests, status,
                        confirmation_token, token_expires
                    )
                    VALUES ($1, $2, $3, $4, $5, $6, $7)
                    RETURNING id
                    """,
                    email.lower(), first_name, last_name, interests or [],
                    settings.DEFAULT_SUBSCRIPTION_STATUS, confirmation_token, token_expires
                )
            
            await conn.close()
            
            # Send confirmation email
            await self.email_service.send_confirmation_email(
                email=email,
                first_name=first_name or "Subscriber",
                confirmation_token=confirmation_token
            )
            
            return str(subscriber_id)
            
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Subscribe error: {e}")
            raise
    
    async def unsubscribe(self, email: str) -> bool:
        """Unsubscribe a user"""
        try:
            conn = await get_db_connection()
            
            result = await conn.execute(
                """
                UPDATE subscribers 
                SET status = 'unsubscribed', updated_at = CURRENT_TIMESTAMP
                WHERE email = $1 AND status IN ('active', 'pending')
                """,
                email.lower()
            )
            
            await conn.close()
            
            return result != "UPDATE 0"
            
        except Exception as e:
            logger.error(f"Unsubscribe error: {e}")
            return False
    
    async def confirm_subscription(self, token: str) -> bool:
        """Confirm email subscription"""
        try:
            conn = await get_db_connection()
            
            # Find subscriber by token
            subscriber = await conn.fetchrow(
                """
                SELECT id, email, first_name, token_expires
                FROM subscribers
                WHERE confirmation_token = $1 AND status = 'pending'
                """,
                token
            )
            
            if not subscriber:
                return False
            
            # Check token expiration
            if subscriber['token_expires'] < datetime.utcnow():
                return False
            
            # Update status
            await conn.execute(
                """
                UPDATE subscribers 
                SET status = 'active', confirmation_token = NULL, token_expires = NULL,
                    confirmed_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
                WHERE id = $1
                """,
                subscriber['id']
            )
            
            await conn.close()
            
            # Send welcome email
            await self.email_service.send_welcome_email(
                email=subscriber['email'],
                first_name=subscriber['first_name'] or "Subscriber"
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Confirm subscription error: {e}")
            return False
    
    async def get_subscriber(self, subscriber_id: str) -> Optional[Dict[str, Any]]:
        """Get subscriber by ID"""
        try:
            conn = await get_db_connection()
            
            subscriber = await conn.fetchrow(
                "SELECT * FROM subscribers WHERE id = $1",
                uuid.UUID(subscriber_id)
            )
            
            await conn.close()
            
            return dict(subscriber) if subscriber else None
            
        except Exception as e:
            logger.error(f"Get subscriber error: {e}")
            return None
    
    async def update_subscriber(
        self,
        subscriber_id: str,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        interests: Optional[List[str]] = None,
        is_active: Optional[bool] = None
    ) -> bool:
        """Update subscriber details"""
        try:
            conn = await get_db_connection()
            
            # Build update query dynamically
            updates = []
            params = [uuid.UUID(subscriber_id)]
            param_count = 1
            
            if first_name is not None:
                param_count += 1
                updates.append(f"first_name = ${param_count}")
                params.append(first_name)
            
            if last_name is not None:
                param_count += 1
                updates.append(f"last_name = ${param_count}")
                params.append(last_name)
            
            if interests is not None:
                param_count += 1
                updates.append(f"interests = ${param_count}")
                params.append(interests)
            
            if is_active is not None:
                param_count += 1
                status = "active" if is_active else "inactive"
                updates.append(f"status = ${param_count}")
                params.append(status)
            
            if not updates:
                return True
            
            updates.append("updated_at = CURRENT_TIMESTAMP")
            
            query = f"""
                UPDATE subscribers 
                SET {', '.join(updates)}
                WHERE id = $1
            """
            
            result = await conn.execute(query, *params)
            await conn.close()
            
            return result != "UPDATE 0"
            
        except Exception as e:
            logger.error(f"Update subscriber error: {e}")
            return False
    
    async def list_subscribers(
        self,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Tuple[List[Dict[str, Any]], int]:
        """List subscribers with optional filtering"""
        try:
            conn = await get_db_connection()
            
            # Build query
            where_clause = ""
            params = []
            param_count = 0
            
            if status:
                param_count += 1
                where_clause = f"WHERE status = ${param_count}"
                params.append(status)
            
            # Get total count
            count_query = f"SELECT COUNT(*) FROM subscribers {where_clause}"
            total = await conn.fetchval(count_query, *params)
            
            # Get subscribers
            query = f"""
                SELECT * FROM subscribers {where_clause}
                ORDER BY created_at DESC
                LIMIT ${param_count + 1} OFFSET ${param_count + 2}
            """
            params.extend([limit, offset])
            
            rows = await conn.fetch(query, *params)
            subscribers = [dict(row) for row in rows]
            
            await conn.close()
            
            return subscribers, total
            
        except Exception as e:
            logger.error(f"List subscribers error: {e}")
            return [], 0
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get subscriber statistics"""
        try:
            conn = await get_db_connection()
            
            # Get counts by status
            stats_query = """
                SELECT 
                    COUNT(*) as total,
                    COUNT(*) FILTER (WHERE status = 'active') as active,
                    COUNT(*) FILTER (WHERE status = 'pending') as pending,
                    COUNT(*) FILTER (WHERE status = 'unsubscribed') as unsubscribed,
                    COUNT(*) FILTER (WHERE status = 'inactive') as inactive
                FROM subscribers
            """
            
            stats = await conn.fetchrow(stats_query)
            
            # Get recent signups (last 30 days)
            recent_query = """
                SELECT COUNT(*) 
                FROM subscribers 
                WHERE created_at >= NOW() - INTERVAL '30 days'
            """
            recent_signups = await conn.fetchval(recent_query)
            
            await conn.close()
            
            return {
                "total_subscribers": stats['total'],
                "active_subscribers": stats['active'],
                "pending_subscribers": stats['pending'],
                "unsubscribed": stats['unsubscribed'],
                "inactive_subscribers": stats['inactive'],
                "recent_signups_30_days": recent_signups,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Get stats error: {e}")
            return {}