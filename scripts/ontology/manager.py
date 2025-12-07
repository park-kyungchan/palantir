
import os
import json
from typing import Type, TypeVar, Optional, List, Dict, Any
from sqlalchemy.orm import Session
from scripts.ontology.core import OrionObject
from scripts.ontology.db import init_db, ObjectTable, SessionLocal, DB_PATH

T = TypeVar("T", bound=OrionObject)

class ObjectManager:
    """
    The Singleton Kernel for managing Living Objects.
    Handles: Hydration, Persistence, Write-Back, Transaction Management.
    """
    
    def __init__(self):
        # Ensure DB schema exists
        if not os.path.exists(DB_PATH):
            init_db()
        else:
            # Idempotent init (create tables if missing)
            init_db()
            
        # Registry of known types for hydration
        self.type_registry: Dict[str, Type[T]] = {
            "OrionObject": OrionObject
        }
        
        # Observers for Event Bus
        self._subscribers = []
        
        # Create a default session for simple operations
        self.default_session = SessionLocal()

    def subscribe(self, callback):
        """Register a callback for object changes (save/delete)."""
        self._subscribers.append(callback)

    def unsubscribe(self, callback):
        try:
            self._subscribers.remove(callback)
        except ValueError:
            pass

    def _notify(self, event_type: str, result: Any):
        """Notify subscribers of changes."""
        for callback in self._subscribers:
            callback(event_type, result)

    def register_type(self, cls: Type[T]):
        """Register a Pydantic model for hydration."""
        self.type_registry[cls.__name__] = cls

    def get(self, cls: Type[T], obj_id: str, session: Optional[Session] = None) -> Optional[T]:
        """Retrieve an object by ID from SQLite."""
        active_session = session or self.default_session
        
        row = active_session.query(ObjectTable).filter_by(id=obj_id).first()
        if not row:
            return None
            
        # Hydrate
        data = row.data # JSON Dict
        # Determine strict class
        target_cls = self.type_registry.get(row.type, cls)
        
        obj = target_cls(**data)
        obj.mark_clean() # Loaded from DB, so clean
        return obj

    def save(self, obj: OrionObject, session: Optional[Session] = None, commit: bool = True):
        """
        Persist object to SQLite.
        If session is provided (Transactional), it uses that session.
        If commit=True (default), it commits immediately.
        """
        active_session = session or self.default_session
        objects_table = ObjectTable.__table__
        
        # Notify subscribers (Phase 3 Simulation Capture)
        # We do this BEFORE commit to capture the dirty state/intent.
        # But actually for simulation we want to capture 'ChangeEvents'.
        self._notify("save", obj)

        # Check if exists (Upsert logic using SQLAlchemy Core for speed)
        # We can implement a naive check first
        exists = active_session.query(ObjectTable.id).filter_by(id=obj.id).scalar() is not None
        
        type_name = obj.__class__.__name__

        if exists:
            # UPDATE
            # Only update if dirty (Optimization)
            # But client might force save.
            
            update_data = {
                "version": obj.version,
                "updated_at": obj.updated_at,
                "data": obj.model_dump(mode='json'),
                "fts_content": obj.get_searchable_text()
            }
            
            update_stmt = objects_table.update().where(
                objects_table.c.id == obj.id
            ).values(**update_data)
            
            active_session.execute(update_stmt)
            
        else:
            # INSERT
            insert_data = {
                "id": obj.id,
                "type": type_name,
                "version": obj.version,
                "created_at": obj.created_at,
                "updated_at": obj.updated_at,
                "data": obj.model_dump(mode='json'),
                "fts_content": obj.get_searchable_text()
            }
            
            insert_stmt = objects_table.insert().values(**insert_data)
            active_session.execute(insert_stmt)
            
        if commit:
            active_session.commit()
            obj.mark_clean()
        else:
            active_session.flush() # Ensure ID availability/constraints but don't commit
            # Do NOT mark clean yet? Or do we?
            # If we don't commit, we shouldn't mark clean if we rely on is_dirty for retry.
            # But usually flush means "sent to DB".
            # Let's say we mark clean AFTER the transaction wraps up.
            # But UnitOfWork might handle that.
            pass

    def delete(self, obj_id: str, session: Optional[Session] = None, commit: bool = True):
        active_session = session or self.default_session
        objects_table = ObjectTable.__table__
        
        # Notify
        self._notify("delete", obj_id)

        delete_stmt = objects_table.delete().where(objects_table.c.id == obj_id)
        active_session.execute(delete_stmt)
        
        if commit:
            active_session.commit()

    def close(self):
        self.default_session.close()
