
from typing import Dict, Any, Optional, Set, Type, TypeVar
from datetime import datetime
import uuid6
from pydantic import BaseModel, Field, PrivateAttr, model_validator, ConfigDict

T = TypeVar("T", bound="OrionObject")

class OrionObject(BaseModel):
    """
    The Base Class for all Living Objects in Orion.
    Features:
    - UUIDv7 Identity (Time-sortable, Distributed-safe)
    - Dirty Checking (Tracks changes for efficient Write-Back)
    - Versioning (Optimistic Locking support)
    """
    
    # Standard Fields
    id: str = Field(default_factory=lambda: str(uuid6.uuid7()), description="UUIDv7 Primary Key")
    created_at: datetime = Field(default_factory=datetime.now, description="Creation Timestamp")
    updated_at: datetime = Field(default_factory=datetime.now, description="Last Update Timestamp")
    version: int = Field(default=1, description="Optimistic Locking Version")
    
    # Internal State for Dirty Checking
    _is_dirty: bool = PrivateAttr(default=False)
    _original_state: Dict[str, Any] = PrivateAttr(default_factory=dict)
    
    # Pydantic V2 Configuration
    model_config = ConfigDict(
        validate_assignment=True,  # Validate on set
        extra="ignore"            # Allow extra fields in DB but ignore in Model (Forward Compat)
    )

    def __init__(self, **data):
        super().__init__(**data)
        self._snapshot_state()

    def _snapshot_state(self):
        """Captures the current state as the baseline."""
        self._original_state = self.model_dump()
        self._is_dirty = False

    def __setattr__(self, name: str, value: Any):
        """Intercepts attribute setting to track dirty state."""
        # Allow private attributes or initialization to pass through
        if name.startswith("_"):
            super().__setattr__(name, value)
            return

        # Prevent Recursion: Don't track changes to modification metadata
        if name in {"updated_at", "version"}:
            super().__setattr__(name, value)
            return

        # Check for change
        current_value = getattr(self, name, None)
        if current_value != value:
            super().__setattr__(name, value)
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
