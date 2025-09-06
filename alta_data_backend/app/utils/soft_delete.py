from sqlalchemy import and_
from sqlalchemy.orm import Query
from datetime import datetime, timezone
from typing import Type, TypeVar, Generic

T = TypeVar('T')


class SoftDeleteMixin:
    """Mixin to add soft delete functionality to models"""
    
    def soft_delete(self):
        """Mark the record as deleted by setting deleted_at timestamp"""
        self.deleted_at = datetime.now(timezone.utc)
    
    def restore(self):
        """Restore a soft-deleted record by clearing deleted_at"""
        self.deleted_at = None
    
    @classmethod
    def filter_active(cls, query: Query) -> Query:
        """Filter out soft-deleted records"""
        return query.filter(cls.deleted_at.is_(None))
    
    @classmethod
    def filter_deleted(cls, query: Query) -> Query:
        """Filter only soft-deleted records"""
        return query.filter(cls.deleted_at.is_not(None))
    
    @classmethod
    def filter_all(cls, query: Query) -> Query:
        """Include both active and deleted records"""
        return query


def get_active_records(model_class: Type[T], session) -> Query:
    """Get only active (non-deleted) records for a model"""
    return model_class.filter_active(session.query(model_class))


def get_deleted_records(model_class: Type[T], session) -> Query:
    """Get only deleted records for a model"""
    return model_class.filter_deleted(session.query(model_class))


def get_all_records(model_class: Type[T], session) -> Query:
    """Get all records (active and deleted) for a model"""
    return model_class.filter_all(session.query(model_class))
