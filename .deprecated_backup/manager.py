"""
Orion ODA V2 - Object Manager (DEPRECATED)
==========================================

.. deprecated:: 3.0
    This module is deprecated and will be removed in a future release.
    Use the new Repository pattern instead:

    - ActionLogRepository for OrionActionLog
    - JobResultRepository for JobResult
    - InsightRepository for OrionInsight
    - PatternRepository for OrionPattern

    Migration Guide:
    ----------------
    # Before (ObjectManager):
    manager = ObjectManager()
    manager.save(action_log)
    obj = manager.get(OrionActionLog, obj_id)

    # After (Repository):
    from scripts.ontology.storage import ActionLogRepository, initialize_database
    db = await initialize_database()
    repo = ActionLogRepository(db)
    await repo.save(action_log, actor_id="system")
    obj = await repo.find_by_id(obj_id)

    For Observer pattern (subscribe), use EventBus:
    from scripts.infrastructure.event_bus import EventBus
    EventBus.get_instance().subscribe("OrionActionLog.*", callback)
"""

import warnings
from typing import Type, TypeVar, Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import select
from scripts.ontology.ontology_types import OntologyObject
from scripts.ontology.db import init_db, SessionLocal, objects_table

# Emit deprecation warning on import
warnings.warn(
    "ObjectManager is deprecated. Use Repository pattern (ActionLogRepository, etc.) instead. "
    "See scripts/ontology/storage/repositories.py for the new API.",
    DeprecationWarning,
    stacklevel=2
)


class ConcurrencyError(Exception):
    """
    Raised on optimistic locking failure.
    Aligned with Palantir's version-based concurrency control pattern.
    """
    def __init__(self, message: str, expected_version: int = None, actual_version: int = None):
        super().__init__(message)
        self.expected_version = expected_version
        self.actual_version = actual_version
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

        Optimistic Locking (Palantir AIP/Foundry Compliant):
        - If UPDATE: Uses Compare-And-Swap (CAS) pattern with version check.
        - Raises ConcurrencyError if version mismatch detected.
        - Atomic update via WHERE clause with expected version.
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

        # Check existence and current version
        stmt = select(objects_table.c.version).where(objects_table.c.id == obj.id)
        existing = active_session.execute(stmt).fetchone()

        if existing:
            # UPDATE with Optimistic Concurrency Control
            db_version = existing.version or 0
            expected_version = db_version
            new_version = db_version + 1

            # Version Conflict Detection:
            # The object's version should match DB version (caller just loaded it)
            # OR be db_version + 1 (caller already incremented via touch())
            if obj.version != db_version and obj.version != new_version:
                raise ConcurrencyError(
                    f"Object {obj.id} version mismatch. DB={db_version}, Object={obj.version}. "
                    f"Object may have been modified by another transaction.",
                    expected_version=db_version,
                    actual_version=obj.version
                )

            # Set new version and timestamp
            obj.version = new_version
            obj.updated_at = utc_now_helper()

            update_data = {
                "version": obj.version,
                "updated_at": obj.updated_at,
                "data": obj.model_dump(mode='json'),
                "fts_content": self._extract_fts(obj)
            }

            # Atomic CAS: WHERE clause includes expected version
            update_stmt = objects_table.update().where(
                objects_table.c.id == obj.id
            ).where(
                objects_table.c.version == expected_version  # OCC: Version guard
            ).values(**update_data)

            result = active_session.execute(update_stmt)

            # Check if update actually modified a row (CAS verification)
            if result.rowcount == 0:
                raise ConcurrencyError(
                    f"Object {obj.id} was modified by another transaction. "
                    f"Expected version {expected_version}, but row was not updated.",
                    expected_version=expected_version,
                    actual_version=obj.version
                )
            
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
