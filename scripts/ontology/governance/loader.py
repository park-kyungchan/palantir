"""
Orion ODA V3 - Declarative Governance Loader
=============================================
Load action governance rules from YAML configuration.

P-05: Declarative Governance YAML

ODA Alignment:
    - Maps YAML to ActionType metadata
    - Submission criteria from declarative config
    - Side effects defined declaratively

Usage:
    loader = GovernanceLoader()
    actions = loader.load("governance/actions.yaml")
    registry.register_from_governance(actions)
"""

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Type

import yaml

logger = logging.getLogger(__name__)


@dataclass
class SubmissionCriteriaConfig:
    """Configuration for a submission criterion."""
    type: str  # RangeValidator, StringLengthValidator, etc.
    field: str
    min: Optional[float] = None
    max: Optional[float] = None
    required: bool = False
    pattern: Optional[str] = None
    message: Optional[str] = None


@dataclass
class SideEffectConfig:
    """Configuration for a side effect."""
    type: str  # AuditLogSideEffect, EventBusSideEffect, etc.
    event_type: Optional[str] = None
    params: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ActionMetadata:
    """
    Metadata for an action loaded from governance YAML.
    
    Maps to ActionType registration parameters.
    """
    api_name: str
    description: str = ""
    hazardous: bool = False
    requires_proposal: bool = False
    submission_criteria: List[SubmissionCriteriaConfig] = field(default_factory=list)
    side_effects: List[SideEffectConfig] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    version: str = "1.0.0"
    
    @classmethod
    def from_dict(cls, api_name: str, data: Dict[str, Any]) -> "ActionMetadata":
        """Create from dictionary."""
        criteria = []
        for c in data.get("submission_criteria", []):
            criteria.append(SubmissionCriteriaConfig(
                type=c.get("type", ""),
                field=c.get("field", ""),
                min=c.get("min"),
                max=c.get("max"),
                required=c.get("required", False),
                pattern=c.get("pattern"),
                message=c.get("message"),
            ))
        
        effects = []
        for e in data.get("side_effects", []):
            effects.append(SideEffectConfig(
                type=e.get("type", ""),
                event_type=e.get("event_type"),
                params=e.get("params", {}),
            ))
        
        return cls(
            api_name=api_name,
            description=data.get("description", ""),
            hazardous=data.get("hazardous", False),
            requires_proposal=data.get("requires_approval", data.get("requires_proposal", False)),
            submission_criteria=criteria,
            side_effects=effects,
            tags=data.get("tags", []),
            version=data.get("version", "1.0.0"),
        )
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "api_name": self.api_name,
            "description": self.description,
            "hazardous": self.hazardous,
            "requires_proposal": self.requires_proposal,
            "submission_criteria": [
                {"type": c.type, "field": c.field, "min": c.min, "max": c.max}
                for c in self.submission_criteria
            ],
            "side_effects": [
                {"type": e.type, "event_type": e.event_type}
                for e in self.side_effects
            ],
            "tags": self.tags,
            "version": self.version,
        }


class GovernanceLoader:
    """
    Loads action governance configuration from YAML files.
    
    P-05: Declarative Governance YAML
    
    YAML Format:
        actions:
          proposal.create:
            hazardous: true
            requires_approval: true
            description: Create a new proposal
            submission_criteria:
              - type: RangeValidator
                field: priority
                min: 0
                max: 3
            side_effects:
              - type: AuditLogSideEffect
              - type: EventBusSideEffect
                event_type: proposal.created
    
    Usage:
        loader = GovernanceLoader()
        actions = loader.load("governance/actions.yaml")
    """
    
    def __init__(self, base_dir: str = "."):
        self.base_dir = Path(base_dir)
        self._cache: Dict[str, ActionMetadata] = {}
    
    def load(self, path: str) -> Dict[str, ActionMetadata]:
        """
        Load governance configuration from YAML file.
        
        Args:
            path: Path to YAML file (relative to base_dir)
            
        Returns:
            Dict mapping api_name to ActionMetadata
        """
        full_path = self.base_dir / path
        
        if not full_path.exists():
            logger.warning(f"Governance file not found: {full_path}")
            return {}
        
        logger.info(f"Loading governance from: {full_path}")
        
        with open(full_path) as f:
            config = yaml.safe_load(f)
        
        if not config or "actions" not in config:
            logger.warning(f"No actions defined in: {full_path}")
            return {}
        
        actions = {}
        for api_name, spec in config["actions"].items():
            try:
                metadata = ActionMetadata.from_dict(api_name, spec)
                actions[api_name] = metadata
                self._cache[api_name] = metadata
                logger.debug(f"Loaded action: {api_name}")
            except Exception as e:
                logger.error(f"Failed to load action {api_name}: {e}")
        
        logger.info(f"Loaded {len(actions)} actions from governance")
        return actions
    
    def load_all(self, patterns: List[str] = None) -> Dict[str, ActionMetadata]:
        """
        Load all governance files matching patterns.
        
        Args:
            patterns: Glob patterns (default: ["governance/*.yaml", "governance/*.yml"])
        """
        if patterns is None:
            patterns = ["governance/*.yaml", "governance/*.yml"]
        
        all_actions = {}
        
        for pattern in patterns:
            for path in self.base_dir.glob(pattern):
                relative_path = path.relative_to(self.base_dir)
                actions = self.load(str(relative_path))
                all_actions.update(actions)
        
        return all_actions
    
    def get(self, api_name: str) -> Optional[ActionMetadata]:
        """Get cached action metadata by api_name."""
        return self._cache.get(api_name)
    
    def build_submission_criteria(
        self,
        metadata: ActionMetadata,
    ) -> List:
        """
        Build SubmissionCriteria instances from config.
        
        Returns:
            List of SubmissionCriteria instances
        """
        from scripts.ontology.actions.submission_criteria import (
            RangeValidator,
            ArraySizeValidator,
            RequiredFieldValidator,
            StringLengthValidator,
        )
        
        VALIDATORS = {
            "RangeValidator": RangeValidator,
            "ArraySizeValidator": ArraySizeValidator,
            "RequiredFieldValidator": RequiredFieldValidator,
            "StringLengthValidator": StringLengthValidator,
        }
        
        criteria = []
        
        for config in metadata.submission_criteria:
            validator_class = VALIDATORS.get(config.type)
            if not validator_class:
                logger.warning(f"Unknown validator type: {config.type}")
                continue
            
            try:
                if config.type == "RangeValidator":
                    validator = validator_class(
                        field_name=config.field,
                        min_value=config.min,
                        max_value=config.max,
                    )
                elif config.type == "ArraySizeValidator":
                    validator = validator_class(
                        field_name=config.field,
                        min_size=int(config.min or 0),
                        max_size=int(config.max or 100),
                    )
                elif config.type == "RequiredFieldValidator":
                    validator = validator_class(field_name=config.field)
                elif config.type == "StringLengthValidator":
                    validator = validator_class(
                        field_name=config.field,
                        min_length=int(config.min or 0),
                        max_length=int(config.max or 10000),
                    )
                else:
                    continue
                
                criteria.append(validator)
                
            except Exception as e:
                logger.error(f"Failed to create validator {config.type}: {e}")
        
        return criteria
    
    def build_side_effects(
        self,
        metadata: ActionMetadata,
    ) -> List:
        """
        Build SideEffect instances from config.
        
        Returns:
            List of SideEffect instances
        """
        from scripts.ontology.actions.side_effects import (
            AuditLogSideEffect,
            EventBusSideEffect,
        )
        
        SIDE_EFFECTS = {
            "AuditLogSideEffect": AuditLogSideEffect,
            "EventBusSideEffect": EventBusSideEffect,
        }
        
        effects = []
        
        for config in metadata.side_effects:
            effect_class = SIDE_EFFECTS.get(config.type)
            if not effect_class:
                logger.warning(f"Unknown side effect type: {config.type}")
                continue
            
            try:
                if config.type == "EventBusSideEffect":
                    effect = effect_class(event_type=config.event_type)
                else:
                    effect = effect_class()
                
                effects.append(effect)
                
            except Exception as e:
                logger.error(f"Failed to create side effect {config.type}: {e}")
        
        return effects


# Global loader instance
_global_loader: Optional[GovernanceLoader] = None


def get_governance_loader(base_dir: str = ".") -> GovernanceLoader:
    """Get or create the global governance loader."""
    global _global_loader
    
    if _global_loader is None:
        _global_loader = GovernanceLoader(base_dir)
    
    return _global_loader
