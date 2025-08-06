"""
Base CRUD operations
"""
import uuid
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union
from uuid import UUID

from fastapi.encoders import jsonable_encoder
from sqlalchemy import select, update, delete, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from ..models.base import Base

ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType")
UpdateSchemaType = TypeVar("UpdateSchemaType")


class BaseCRUD(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """Base class for CRUD operations"""
    
    def __init__(self, model: Type[ModelType]):
        self.model = model
    
    # Async methods
    async def get(self, session: AsyncSession, id: Union[UUID, int, str]) -> Optional[ModelType]:
        """Get a single record by ID"""
        stmt = select(self.model).where(self.model.id == id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_multi(
        self, 
        session: AsyncSession, 
        *, 
        skip: int = 0, 
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[ModelType]:
        """Get multiple records with pagination"""
        stmt = select(self.model)
        
        if filters:
            for field, value in filters.items():
                if hasattr(self.model, field):
                    stmt = stmt.where(getattr(self.model, field) == value)
        
        stmt = stmt.offset(skip).limit(limit)
        result = await session.execute(stmt)
        return result.scalars().all()
    
    async def count(
        self, 
        session: AsyncSession,
        filters: Optional[Dict[str, Any]] = None
    ) -> int:
        """Count records with optional filters"""
        stmt = select(func.count(self.model.id))
        
        if filters:
            for field, value in filters.items():
                if hasattr(self.model, field):
                    stmt = stmt.where(getattr(self.model, field) == value)
        
        result = await session.execute(stmt)
        return result.scalar()
    
    async def create(self, session: AsyncSession, *, obj_in: CreateSchemaType) -> ModelType:
        """Create a new record"""
        obj_in_data = jsonable_encoder(obj_in)
        db_obj = self.model(**obj_in_data)
        session.add(db_obj)
        await session.commit()
        await session.refresh(db_obj)
        return db_obj
    
    async def update(
        self,
        session: AsyncSession,
        *,
        db_obj: ModelType,
        obj_in: Union[UpdateSchemaType, Dict[str, Any]]
    ) -> ModelType:
        """Update an existing record"""
        obj_data = jsonable_encoder(db_obj)
        
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.dict(exclude_unset=True)
        
        for field in obj_data:
            if field in update_data:
                setattr(db_obj, field, update_data[field])
        
        session.add(db_obj)
        await session.commit()
        await session.refresh(db_obj)
        return db_obj
    
    async def delete(self, session: AsyncSession, *, id: Union[UUID, int, str]) -> Optional[ModelType]:
        """Delete a record by ID"""
        db_obj = await self.get(session, id)
        if db_obj:
            await session.delete(db_obj)
            await session.commit()
        return db_obj
    
    async def bulk_create(self, session: AsyncSession, *, objs_in: List[CreateSchemaType]) -> List[ModelType]:
        """Create multiple records"""
        db_objs = []
        for obj_in in objs_in:
            obj_in_data = jsonable_encoder(obj_in)
            db_obj = self.model(**obj_in_data)
            db_objs.append(db_obj)
        
        session.add_all(db_objs)
        await session.commit()
        
        # Refresh all objects
        for db_obj in db_objs:
            await session.refresh(db_obj)
        
        return db_objs
    
    # Sync methods for compatibility
    def get_sync(self, session: Session, id: Union[UUID, int, str]) -> Optional[ModelType]:
        """Synchronous get by ID"""
        return session.query(self.model).filter(self.model.id == id).first()
    
    def get_multi_sync(
        self, 
        session: Session, 
        *, 
        skip: int = 0, 
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[ModelType]:
        """Synchronous get multiple records"""
        query = session.query(self.model)
        
        if filters:
            for field, value in filters.items():
                if hasattr(self.model, field):
                    query = query.filter(getattr(self.model, field) == value)
        
        return query.offset(skip).limit(limit).all()
    
    def create_sync(self, session: Session, *, obj_in: CreateSchemaType) -> ModelType:
        """Synchronous create"""
        obj_in_data = jsonable_encoder(obj_in)
        db_obj = self.model(**obj_in_data)
        session.add(db_obj)
        session.commit()
        session.refresh(db_obj)
        return db_obj