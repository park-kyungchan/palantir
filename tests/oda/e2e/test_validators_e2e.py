from __future__ import annotations

import json

import pytest

from lib.oda.ontology.types.status_types import ResourceLifecycleStatus
from lib.oda.ontology.validators import StatusTransitionError, StatusTransitionValidator
from lib.oda.ontology.validators.schema_validator import (
    SchemaValidationError,
    SchemaValidator,
    ValidationMode,
)


def _write_schema(tmp_path):
    schema = {
        "version": "3.0.1",
        "objects": {
            "Task": {
                "properties": {
                    "title": {
                        "type": "string",
                        "required": True,
                        "constraints": {"min_length": 1, "max_length": 10},
                    },
                    "priority": {
                        "type": "integer",
                        "required": False,
                        "constraints": {"ge": 1, "le": 5},
                    },
                }
            }
        },
    }
    path = tmp_path / "ontology_registry.json"
    path.write_text(json.dumps(schema), encoding="utf-8")
    return path


def test_schema_validator_strict_mode_raises_on_invalid_payload(tmp_path) -> None:
    validator = SchemaValidator(schema_path=_write_schema(tmp_path), mode=ValidationMode.STRICT)

    with pytest.raises(SchemaValidationError):
        validator.validate("Task", payload={})


def test_schema_validator_warn_mode_returns_errors_and_partial_skips_required(tmp_path) -> None:
    validator = SchemaValidator(schema_path=_write_schema(tmp_path), mode=ValidationMode.WARN)

    result = validator.validate("Task", payload={"title": ""})
    assert result.is_valid is False
    assert any("at least" in e.message for e in result.errors)

    partial = validator.validate("Task", payload={}, partial=True)
    assert partial.is_valid is True


def test_schema_validator_off_mode_disables_validation(tmp_path) -> None:
    validator = SchemaValidator(schema_path=_write_schema(tmp_path), mode=ValidationMode.OFF)
    result = validator.validate("Task", payload={})
    assert result.is_valid is True


def test_status_transition_validator_warnings_and_invalid_transition() -> None:
    validator = StatusTransitionValidator()

    result = validator.validate_transition(
        ResourceLifecycleStatus.DRAFT,
        ResourceLifecycleStatus.ACTIVE,
        raise_on_invalid=False,
    )
    assert result.is_valid is True
    assert any("skips intermediate" in w.lower() for w in result.warnings)

    with pytest.raises(StatusTransitionError):
        validator.validate_transition(ResourceLifecycleStatus.DELETED, ResourceLifecycleStatus.ACTIVE)
