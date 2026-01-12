from __future__ import annotations

import logging
from typing import List, Type, Any, Optional, Dict, TypeVar
from sqlalchemy import select, and_, desc, asc, text
from sqlalchemy.orm import class_mapper

from lib.oda.ontology.ontology_types import OntologyObject
from lib.oda.ontology.storage.database import Database, DatabaseManager
from lib.oda.ontology.storage.models import (
    ProposalModel, 
    OrionActionLogModel, 
    JobResultModel,
    OrionInsightModel,
    OrionPatternModel,
    LearnerModel
)
# Note: We need to import the Domain Objects to map them to Models.
# However, to avoid circular imports if those files import OSDK, we might pass types at runtime.
# For now, we assume standard naming conventions or specific registration.

from lib.oda.osdk.connector import DataConnector
from lib.oda.osdk.query import PropertyFilter

T = TypeVar("T", bound=OntologyObject)

logger = logging.getLogger(__name__)

class SQLiteConnector(DataConnector):
    """
    DataConnector implementation for the main SQLite Ontology DB.
    Uses SQLAlchemy Async Engine.
    """
    
    def __init__(self, db: Optional[Database] = None):
        self.db = db or DatabaseManager.get()
        
        # Mapping Domain Types -> SQLAlchemy Models
        # This is a manual registry for now. In robust implementations, use a registry system.
        # We match based on class name string to avoid importing all domain objects here.
        self._model_map = {
            "Proposal": ProposalModel,
            "OrionActionLog": OrionActionLogModel,
            "JobResult": JobResultModel,
            "OrionInsight": OrionInsightModel,
            "OrionPattern": OrionPatternModel,
            "Learner": LearnerModel,
            # Fallbacks or aliases
            "proposal": ProposalModel,
        }

    def _get_model_class(self, domain_type: Type[T]) -> Type:
        name = domain_type.__name__
        if name in self._model_map:
            return self._model_map[name]
        logger.warning(f"No explicit model mapping for {name}, trying to guess...")
        # Fallback: if domain is 'Task', try 'TaskModel'
        return self._model_map.get(f"{name}Model", None) or self._model_map.get(name)

    def _to_domain(self, model_instance: Any, domain_type: Type[T]) -> T:
        """Convert SQLAlchemy model to Pydantic domain object."""
        # This assumes Pydantic fields match Model columns.
        # We filter out internal SQLAlchemy state (`_sa_instance_state`).
        data = {
            k: v for k, v in model_instance.__dict__.items() 
            if not k.startswith("_sa_")
        }
        return domain_type(**data)

    async def query(
        self, 
        object_type: Type[T], 
        filters: List[PropertyFilter], 
        selected_properties: List[str],
        order_by: Optional[Dict[str, str]],
        limit: int
    ) -> List[T]:
        model_cls = self._get_model_class(object_type)
        if not model_cls:
            raise ValueError(f"No persistence model found for {object_type.__name__}")

        async with self.db.transaction() as session:
            stmt = select(model_cls)
            
            # Apply Filters
            conditions = []
            for f in filters:
                col = getattr(model_cls, f.property, None)
                if col is None:
                    logger.warning(f"Property {f.property} not found on {model_cls.__name__}")
                    continue
                    
                if f.operator == "eq":
                    conditions.append(col == f.value)
                elif f.operator == "gt":
                    conditions.append(col > f.value)
                elif f.operator == "lt":
                    conditions.append(col < f.value)
                elif f.operator == "gte":  # NEW
                    conditions.append(col >= f.value)
                elif f.operator == "lte":  # NEW
                    conditions.append(col <= f.value)
                elif f.operator == "between":  # NEW
                    conditions.append(col.between(f.value[0], f.value[1]))
                elif f.operator == "contains":
                    conditions.append(col.contains(f.value))
                elif f.operator == "startsWith":  # NEW
                    conditions.append(col.startswith(f.value))
                elif f.operator == "endsWith":  # NEW
                    conditions.append(col.endswith(f.value))
                elif f.operator == "in":
                    conditions.append(col.in_(f.value))
                elif f.operator == "is_null":  # NEW
                    conditions.append(col.is_(None) if f.value else col.isnot(None))
                elif f.operator == "regex":  # NEW
                    conditions.append(col.regexp_match(f.value))
                else:
                    logger.warning(f"Unknown operator: {f.operator}")
            
            if conditions:
                stmt = stmt.where(and_(*conditions))

            # Apply Ordering
            if order_by:
                col = getattr(model_cls, order_by["property"], None)
                if col:
                    direction = desc if order_by["direction"] == "desc" else asc
                    stmt = stmt.order_by(direction(col))
            
            # Apply Limit
            stmt = stmt.limit(limit)
            
            # Execute
            result = await session.execute(stmt)
            instances = result.scalars().all()
            
            # Convert to Domain
            return [self._to_domain(i, object_type) for i in instances]

    async def get_by_id(self, object_type: Type[T], object_id: str) -> Optional[T]:
        model_cls = self._get_model_class(object_type)
        if not model_cls:
            raise ValueError(f"No persistence model found for {object_type.__name__}")

        async with self.db.transaction() as session:
            stmt = select(model_cls).where(model_cls.id == object_id)
            result = await session.execute(stmt)
            instance = result.scalar_one_or_none()
            
            if instance:
                return self._to_domain(instance, object_type)
            return None

    async def bulk_get(self, object_type: Type[T], ids: List[str]) -> List[T]:
        """Retrieve multiple objects by ID."""
        model_class = self._get_model_class(object_type)
        if not model_class:
            return []

        async with self.db.transaction() as session:
            stmt = select(model_class).where(model_class.id.in_(ids))
            result = await session.execute(stmt)
            models = result.scalars().all()
            return [self._to_domain(m, object_type) for m in models]

    async def bulk_create(self, object_type: Type[T], objects: List[T]) -> List[str]:
        """Create multiple objects in single transaction."""
        model_class = self._get_model_class(object_type)
        if not model_class:
            raise ValueError(f"No model mapping for {object_type.__name__}")

        created_ids = []
        async with self.db.transaction() as session:
            for obj in objects:
                model = model_class(**obj.model_dump())
                session.add(model)
                created_ids.append(obj.id)

        return created_ids
