
from typing import Type, TypeVar, Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import select
from scripts.ontology.ontology_types import OntologyObject
from scripts.ontology.db import init_db, SessionLocal, objects_table
# Schemas might be Pydantic models that inherit from different bases, 
# or they inherit from OntologyObject. We import them for registry.
from scripts.ontology.schemas.governance import OrionActionLog
from scripts.ontology.schemas.result import JobResult
from scripts.ontology.schemas.memory import OrionInsight, OrionPattern

# Alias for backward compatibility with Action definitions
OrionObject = OntologyObject
T = TypeVar("T", bound=OntologyObject)

class ObjectManager:
    """
    The Gatekeeper for the Ontology.
    
    Refactoring Status (2025-12-21):
    - Removed 'Phonograph' Write-Back Caching (Over-engineered).
    - Now operates as a stateless Data Access Object (DAO) pattern.
    - Supports Transactional Workflows via explicit Session injection.
    - Retains Observer Pattern for Simulation Engine (ScenarioFork).
    
    Alignment:
    - Palantir OSDK: Stateless, direct persistence.
    - Optimistic Locking: Handled via 'version' field.
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
        # Note: In a pure stateless design, we might prefer transient sessions, 
        # but for compatibility with existing scripts, we keep a default one.
        self.default_session: Session = SessionLocal()
        self._listeners = []
        
        # Registry of known types for hydration
        # Usage: row.type (str) -> Class
        self.type_registry: Dict[str, Type[OntologyObject]] = {
            "OntologyObject": OntologyObject,
            "OrionObject": OntologyObject, # Alias
            "OrionActionLog": OrionActionLog,
            "JobResult": JobResult,
            "OrionInsight": OrionInsight,
            "OrionPattern": OrionPattern
        }

    def subscribe(self, callback):
        """Subscribe to object mutation events (save/delete). Used by Simulation."""
        self._listeners.append(callback)

    def unsubscribe(self, callback):
        if callback in self._listeners:
            self._listeners.remove(callback)

    def _notify(self, event_type: str, obj: OntologyObject):
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
        Fetches an object by ID directly from the database.
        
        Args:
            cls: The expected Type of the object.
            obj_id: The UUID.
            session: Optional SQL Session for transaction isolation.
        """
        active_session = session if session else self.default_session
        
        # Direct DB Fetch
        stmt = select(objects_table).where(objects_table.c.id == obj_id)
        row = active_session.execute(stmt).fetchone()
        
        if not row:
            return None
            
        # Type Validation
        stored_type = row.type
        # If registry has a mapping, resolve expected class logic here? 
        # For now, strict name matching or flexible hydration.
        # We strictly check if the stored type matches the requested class or subclass?
        # Simpler: just ensure we can hydrate it using the requested class or look up the specific class.
        
        # Strategy: Use the Registry to find the ACTUAL class to instantiate, 
        # then check if it's compatible with requested 'cls'.
        target_cls = self.type_registry.get(stored_type, cls)
        
        # Hydrate Pydantic Model from JSON Data column
        # objects_table definition: Column("data", JSON, nullable=False)
        data = row.data
        obj = target_cls(**data)
        
        # Sync Metadata from Columns (Source of Truth) to Object
        obj.version = row.version
        obj.created_at = row.created_at
        obj.updated_at = row.updated_at
        
        return obj

    def save(self, obj: OntologyObject, session: Optional[Session] = None, commit: Optional[bool] = None):
        """
        Persists an object to the database.
        Upsert Logic: Checks existence by ID -> Insert or Update.
        
        Optimistic Locking:
        - If UPDATE: Object version must match DB version (if strictly enforced), 
          or we simply increment. 
        - Current Logic: We blindly increment version here on save, assuming the caller's object is strictly linear.
        """
        active_session = session if session else self.default_session
        
        # Determine Commit Strategy
        if session is None:
            # Interactive/Global Session -> Default Commit (True)
            should_commit = (commit is not False)
        else:
            # Transactional Session -> Default Flush Only (False)
            should_commit = (commit is True)

        type_name = obj.__class__.__name__

        # Check existence
        stmt = select(objects_table.c.version).where(objects_table.c.id == obj.id)
        existing = active_session.execute(stmt).fetchone()

        if existing:
            # UPDATE
            # In stateless mode, we retrieve the version from the object provided.
            # If we want to guard against conflicts, we could check existing.version == obj.version.
            # For this refactor, we keep the previous behavior: Increment and Overwrite.
            
            # Note: Ideally, the object should have been 'touched' by business logic before saving.
            # But the manager guarantees a version bump on persistence.
            obj.version = (existing.version or 0) + 1
            obj.updated_at = utc_now_helper() 
            
            update_data = {
                "version": obj.version,
                "updated_at": obj.updated_at,
                "data": obj.model_dump(mode='json'),
                "fts_content": self._extract_fts(obj) # Helper for FTS extraction
            }
            
            update_stmt = objects_table.update().where(
                objects_table.c.id == obj.id
            ).values(**update_data)
            
            active_session.execute(update_stmt)
            
        else:
            # INSERT
            # Ensure version is set
            if not obj.version:
                obj.version = 1
                
            insert_data = {
                "id": obj.id,
                "type": type_name,
                "version": obj.version,
                "created_at": obj.created_at,
                "updated_at": obj.updated_at,
                "data": obj.model_dump(mode='json'),
                "fts_content": self._extract_fts(obj)
            }
            
            insert_stmt = objects_table.insert().values(**insert_data)
            active_session.execute(insert_stmt)

        # Notify Listeners (Simulation)
        self._notify("save", obj)

        if should_commit:
            active_session.commit()
        else:
            active_session.flush()

    def delete(self, obj_id: str, session: Optional[Session] = None, commit: Optional[bool] = None):
        """
        Hard deletion of an object by ID.
        """
        active_session = session if session else self.default_session
        
        # Determine Commit Strategy
        if session is None:
            should_commit = (commit is not False)
        else:
            should_commit = (commit is True)
            
        delete_stmt = objects_table.delete().where(objects_table.c.id == obj_id)
        result = active_session.execute(delete_stmt)
        
        self._notify("delete", obj_id)
        
        if should_commit:
            active_session.commit()
        else:
            active_session.flush()

    def close(self):
        self.default_session.close()

    def _extract_fts(self, obj: OntologyObject) -> str:
        """Helper to safely extract FTS content if method exists."""
        if hasattr(obj, "get_searchable_text"):
            return obj.get_searchable_text()
        return ""

# Helper to avoid circular import issues with types
from datetime import datetime, timezone
def utc_now_helper() -> datetime:
    return datetime.now(timezone.utc)
