"""
Authentication service for the Subscriber Manager Service
"""

import asyncpg
import bcrypt
import jwt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import uuid
import logging

from ..config.settings import get_settings
from ..database.connection import get_db_connection

logger = logging.getLogger(__name__)
settings = get_settings()


class AuthService:
    """Authentication service class"""
    
    async def authenticate_user(self, email: str, password: str) -> Optional[Dict[str, Any]]:
        """Authenticate user with email and password"""
        try:
            conn = await get_db_connection()
            
            # Get user by email
            user = await conn.fetchrow(
                "SELECT * FROM users WHERE email = $1 AND is_active = TRUE",
                email.lower()
            )
            
            await conn.close()
            
            if not user:
                return None
            
            # Verify password
            if not self._verify_password(password, user['password_hash']):
                return None
            
            return dict(user)
            
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return None
    
    async def create_user(
        self,
        email: str,
        password: str,
        first_name: str,
        last_name: str
    ) -> str:
        """Create a new user"""
        try:
            conn = await get_db_connection()
            
            # Hash password
            password_hash = self._hash_password(password)
            
            # Create user
            user_id = await conn.fetchval(
                """
                INSERT INTO users (email, password_hash, first_name, last_name, is_active)
                VALUES ($1, $2, $3, $4, TRUE)
                RETURNING id
                """,
                email.lower(), password_hash, first_name, last_name
            )
            
            await conn.close()
            return str(user_id)
            
        except Exception as e:
            logger.error(f"User creation error: {e}")
            raise
    
    async def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email"""
        try:
            conn = await get_db_connection()
            
            user = await conn.fetchrow(
                "SELECT * FROM users WHERE email = $1",
                email.lower()
            )
            
            await conn.close()
            
            return dict(user) if user else None
            
        except Exception as e:
            logger.error(f"Get user by email error: {e}")
            return None
    
    async def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID"""
        try:
            conn = await get_db_connection()
            
            user = await conn.fetchrow(
                "SELECT * FROM users WHERE id = $1",
                uuid.UUID(user_id)
            )
            
            await conn.close()
            
            return dict(user) if user else None
            
        except Exception as e:
            logger.error(f"Get user by ID error: {e}")
            return None
    
    async def create_access_token(self, user_id: str) -> str:
        """Create JWT access token"""
        try:
            expire = datetime.utcnow() + timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
            
            payload = {
                "user_id": user_id,
                "exp": expire,
                "iat": datetime.utcnow(),
                "type": "access"
            }
            
            token = jwt.encode(
                payload,
                settings.JWT_SECRET,
                algorithm=settings.JWT_ALGORITHM
            )
            
            return token
            
        except Exception as e:
            logger.error(f"Token creation error: {e}")
            raise
    
    async def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify JWT token"""
        try:
            payload = jwt.decode(
                token,
                settings.JWT_SECRET,
                algorithms=[settings.JWT_ALGORITHM]
            )
            
            return payload
            
        except jwt.ExpiredSignatureError:
            logger.warning("Token expired")
            return None
        except jwt.InvalidTokenError:
            logger.warning("Invalid token")
            return None
        except Exception as e:
            logger.error(f"Token verification error: {e}")
            return None
    
    def _hash_password(self, password: str) -> str:
        """Hash password using bcrypt"""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    def _verify_password(self, password: str, password_hash: str) -> bool:
        """Verify password against hash"""
        return bcrypt.checkpw(
            password.encode('utf-8'),
            password_hash.encode('utf-8')
        )