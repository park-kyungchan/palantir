
import logging
from typing import Dict, Any, Type, Optional
from datetime import datetime
from uuid import uuid4
import uuid_utils
from pydantic import BaseModel, PrivateAttr, Field

# Ensure logging constraint: Only use standard logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OrionObject(BaseModel):
    """
    The Base Class for all Living Objects in Orion.
    Features:
    - UUIDv7 Identity (Time-sorted)
    - Dirty Tracking (for Write-Back)
    - Versioning
    """
    id: str = Field(default_factory=lambda: str(uuid_utils.uuid7()))
    type: str = Field(default="OrionObject")
    version: int = 1
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    # Private attributes for tracking state changes logic
    _is_dirty: bool = PrivateAttr(default=False)
    _original_state: Dict[str, Any] = PrivateAttr(default_factory=dict)

    def __init__(self, **data):
        super().__init__(**data)
        # Snapshot state after initialization
        if not self.type or self.type == "OrionObject":
            self.type = self.__class__.__name__
        self._snapshot_state()

    def _snapshot_state(self):
        """Captures the current state as 'original' for dirty checking."""
        self._original_state = self.model_dump()
        self._is_dirty = False

    def __setattr__(self, name, value):
        # Handle PrivateAttrs first to avoid recursion during init
        if name.startswith('_'):
            return super().__setattr__(name, value)
            
        super().__setattr__(name, value)
        
        # Check against original state if initialized
        if hasattr(self, "_original_state") and name in self._original_state:
            if self._original_state[name] != value:
                self._is_dirty = True
                # Update timestamp without triggering recursion
            super().__setattr__("updated_at", datetime.now())

    def is_dirty(self) -> bool:
        return self._is_dirty

    def get_changes(self) -> Dict[str, Any]:
        """Returns a dictionary of changed fields and their new values."""
        if not self._is_dirty:
            return {}
        
        current = self.model_dump()
        changes = {}
        for key, value in current.items():
            if key not in self._original_state or self._original_state[key] != value:
                changes[key] = value
        return changes

    def mark_clean(self):
        """Resets dirty flag and updates snapshot (called after Commit)."""
        self._snapshot_state()

    def get_searchable_text(self) -> str:
        """
        Generates a flat string for Full-Text Search.
        Override this in subclasses to prioritize specific fields.
        """
        # Default: content of all string fields
        terms = []
        for val in self.model_dump().values():
            if isinstance(val, str):
                terms.append(val)
            elif isinstance(val, (list, tuple)):
                for item in val:
                    if isinstance(item, str):
                        terms.append(item)
        return " ".join(terms)
