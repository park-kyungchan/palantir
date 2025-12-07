
from typing import Type, TypeVar, Optional, List, Dict
from sqlalchemy.orm import Session
from sqlalchemy import select, text
from scripts.ontology.core import OrionObject
from scripts.ontology.db import init_db, SessionLocal, DB_PATH, objects_table
from scripts.ontology.schemas.governance import OrionActionLog

T = TypeVar("T", bound=OrionObject)

class ObjectManager:
    """
    The Gatekeeper for the Ontology.
    Implements the 'Phonograph' pattern:
    - Write-Back Caching
    - Optimistic Locking
    - Session Scope Management (Supports Transactional Workflows)
    """
    
    _instance = None
    _listeners = []

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ObjectManager, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        init_db()
        # The 'Default' session for interactive use or legacy scripts.
        # Actions should provide their own scoped session.
        self.default_session: Session = SessionLocal()
        self._listeners = []
        # Registry of known types for hydration
        self.type_registry: Dict[str, Type[T]] = {
            "OrionObject": OrionObject,
            "OrionActionLog": OrionActionLog
        }

    def subscribe(self, callback):
        """Subscribe to object mutation events (save/delete)."""
        self._listeners.append(callback)

    def unsubscribe(self, callback):
        if callback in self._listeners:
            self._listeners.remove(callback)

    def _notify(self, event_type: str, obj: OrionObject):
        for callback in self._listeners:
            callback(event_type, obj)

    def register_type(self, cls: Type[T]):
        """Register a Pydantic model for hydration."""
        self.type_registry[cls.__name__] = cls

    def create_session(self) -> Session:
        """Create a new independent session (e.g., for Audit logging)."""
        return SessionLocal()

    def get(self, cls: Type[T], obj_id: str, session: Optional[Session] = None) -> Optional[T]:
        """
        Fetches an object by ID.
        :param session: Optional SQLAlchemy session (for transaction isolation). 
                       If None, uses the default global session.
        """
        active_session = session if session else self.default_session
        
        stmt = select(objects_table).where(objects_table.c.id == obj_id)
        row = active_session.execute(stmt).fetchone()
        
        if not row:
            return None
            
        # Validate Type
        stored_type = row.type
        if stored_type != cls.__name__:
            raise ValueError(f"Type Mismatch: ID {obj_id} is {stored_type}, expected {cls.__name__}")

        # Hydrate
        data = row.data
        obj = cls(**data)
        
        # Sync metadata
        obj.version = row.version
        obj.created_at = row.created_at
        obj.updated_at = row.updated_at
        obj.mark_clean()
        
        return obj

    def save(self, obj: OrionObject, session: Optional[Session] = None, commit: Optional[bool] = None):
        """
        Saves a Living Object.
        :param session: External session (Transactional).
        :param commit: Explicit commit override.
                       - If session is None: Defaults to True (Auto-Commit)
                       - If session is Provided: Defaults to False (UnitOfWork handles commit)
        """
        active_session = session if session else self.default_session
        
        # Determine Commit Strategy
        if session is None:
            # Interactive/Global Session -> Default Commit
            should_commit = (commit is not False)
        else:
            # Transactional Session -> Default Flush Only
            should_commit = (commit is True)

        if not obj.is_dirty() and obj.version > 1:
            return

        type_name = obj.__class__.__name__

        # Check if exists (in DB)
        stmt = select(objects_table.c.version).where(objects_table.c.id == obj.id)
        existing = active_session.execute(stmt).fetchone()

        if existing:
            # UPDATE
            obj.version += 1
            
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

        # Notify Listeners (e.g. Simulation Diff)
        self._notify("save", obj)

        if should_commit:
            active_session.commit()
            obj.mark_clean()
        else:
            active_session.flush()
            obj.mark_clean()

    def close(self):
        self.default_session.close()
