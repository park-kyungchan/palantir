from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, List, Optional

from pydantic import ValidationError

from .models import (
    ActionEditSpec,
    ActionLinkEditSpec,
    ActionObjectEditSpec,
    ActionTypeSpec,
    ChangeOperation,
    DeleteActionTypeOp,
    DeleteFunctionTypeOp,
    DeleteInterfaceTypeOp,
    DeleteLinkTypeOp,
    DeleteObjectTypeOp,
    OntologyChangeSet,
    OntologySpec,
    SchemaMigrationInstruction,
)


@dataclass(frozen=True)
class ValidationIssue:
    code: str
    message: str
    path: Optional[str] = None
    severity: str = "error"  # "error" | "warning"

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "message": self.message,
            "path": self.path,
            "severity": self.severity,
        }


def _repo_root() -> Path:
    # lib/oda/foundry_mimic/service.py -> parents[3] == repo root
    return Path(__file__).resolve().parents[3]


class OntologySpecStore:
    """
    File-backed store for Foundry-mimic ontology specs.

    This is intentionally simple and git-friendly (JSON files).
    """

    def __init__(self, root: Optional[Path] = None) -> None:
        self.root = (root or (_repo_root() / "ontology_specs")).resolve()

    def path_for(self, ontology_id: str) -> Path:
        return self.root / f"{ontology_id}.json"

    def load(self, ontology_id: str) -> OntologySpec:
        return load_ontology_spec(self.path_for(ontology_id))

    def save(self, spec: OntologySpec) -> Path:
        path = self.path_for(spec.ontology_id)
        save_ontology_spec(path, spec)
        return path


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _write_text_atomic(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(path)


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def load_ontology_spec(path: str | Path) -> OntologySpec:
    p = Path(path)
    data = json.loads(_read_text(p))
    return OntologySpec.model_validate(data)


def save_ontology_spec(path: str | Path, spec: OntologySpec) -> None:
    p = Path(path)
    payload = spec.model_dump(mode="json")
    _write_text_atomic(p, json.dumps(payload, indent=2, sort_keys=True) + "\n")


def validate_ontology_spec(spec: OntologySpec) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []

    object_types = {o.object_type_id: o for o in spec.object_types}
    link_types = {l.link_type_id: l for l in spec.link_types}
    interface_types = {i.interface_id: i for i in spec.interface_types}

    # Link type endpoints must exist in the same Ontology.
    for l in spec.link_types:
        if l.from_object_type_id not in object_types:
            issues.append(
                ValidationIssue(
                    code="unknown_object_type",
                    message=f"LinkType '{l.link_type_id}' references unknown from_object_type_id '{l.from_object_type_id}'",
                    path=f"link_types[{l.link_type_id}].from_object_type_id",
                )
            )
        if l.to_object_type_id not in object_types:
            issues.append(
                ValidationIssue(
                    code="unknown_object_type",
                    message=f"LinkType '{l.link_type_id}' references unknown to_object_type_id '{l.to_object_type_id}'",
                    path=f"link_types[{l.link_type_id}].to_object_type_id",
                )
            )

    # Interface inheritance must reference known interfaces (and avoid trivial cycles).
    for iface in spec.interface_types:
        for parent in iface.extends:
            if parent not in interface_types:
                issues.append(
                    ValidationIssue(
                        code="unknown_interface",
                        message=f"Interface '{iface.interface_id}' extends unknown interface '{parent}'",
                        path=f"interface_types[{iface.interface_id}].extends",
                    )
                )
        if iface.interface_id in iface.extends:
            issues.append(
                ValidationIssue(
                    code="interface_cycle",
                    message=f"Interface '{iface.interface_id}' cannot extend itself",
                    path=f"interface_types[{iface.interface_id}].extends",
                )
            )

    # ObjectType interface implementations must reference known interfaces.
    for ot in spec.object_types:
        for iface_id in ot.implements:
            if iface_id not in interface_types:
                issues.append(
                    ValidationIssue(
                        code="unknown_interface",
                        message=f"ObjectType '{ot.object_type_id}' implements unknown interface '{iface_id}'",
                        path=f"object_types[{ot.object_type_id}].implements",
                    )
                )

    # ActionTypes should reference known object types, link types, parameters, and properties.
    for action in spec.action_types:
        issues.extend(_validate_action(action, object_types, link_types))

    # Schema migrations: disallow targeting the primary key property.
    if spec.schema_migration_policy is not None:
        issues.extend(_validate_migration_plan(spec, spec.schema_migration_policy.instructions))

    return issues


def _validate_action(
    action: ActionTypeSpec,
    object_types: dict[str, Any],
    link_types: dict[str, Any],
) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []

    params = {p.parameter_id for p in action.parameters}
    targets = set(action.target_object_type_ids)

    for t in targets:
        if t not in object_types:
            issues.append(
                ValidationIssue(
                    code="unknown_object_type",
                    message=f"ActionType '{action.action_type_id}' references unknown target_object_type_id '{t}'",
                    path=f"action_types[{action.action_type_id}].target_object_type_ids",
                )
            )

    # Validate edits
    for idx, edit in enumerate(action.edits):
        issues.extend(_validate_action_edit(action, edit, idx, params, object_types, link_types))

    # Validate submission criteria ValueRefs
    if action.submission_criteria:
        for ridx, root in enumerate(action.submission_criteria.roots):
            issues.extend(
                _validate_criteria_node(
                    action_id=action.action_type_id,
                    node=root,
                    path=f"action_types[{action.action_type_id}].submission_criteria.roots[{ridx}]",
                    params=params,
                    targets=targets,
                    object_types=object_types,
                )
            )

    return issues


def _validate_action_edit(
    action: ActionTypeSpec,
    edit: ActionEditSpec,
    idx: int,
    params: set[str],
    object_types: dict[str, Any],
    link_types: dict[str, Any],
) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    base_path = f"action_types[{action.action_type_id}].edits[{idx}]"

    if isinstance(edit, ActionObjectEditSpec):
        if edit.object_type_id not in object_types:
            issues.append(
                ValidationIssue(
                    code="unknown_object_type",
                    message=f"Edit references unknown object_type_id '{edit.object_type_id}'",
                    path=f"{base_path}.object_type_id",
                )
            )
            return issues

        ot = object_types[edit.object_type_id]
        props = {p.property_id for p in ot.properties}
        for prop_id in edit.properties.keys():
            if prop_id not in props:
                issues.append(
                    ValidationIssue(
                        code="unknown_property",
                        message=f"Edit references unknown property '{prop_id}' on '{edit.object_type_id}'",
                        path=f"{base_path}.properties.{prop_id}",
                    )
                )

        # object_id should usually come from parameters; allow literal for testing.
        if edit.object_id and edit.object_id.source == "parameter" and edit.object_id.name not in params:
            issues.append(
                ValidationIssue(
                    code="unknown_parameter",
                    message=f"Edit references unknown parameter '{edit.object_id.name}'",
                    path=f"{base_path}.object_id",
                )
            )

        for prop_id, vref in edit.properties.items():
            if vref.source == "parameter" and vref.name not in params:
                issues.append(
                    ValidationIssue(
                        code="unknown_parameter",
                        message=f"Edit references unknown parameter '{vref.name}'",
                        path=f"{base_path}.properties.{prop_id}",
                    )
                )
    elif isinstance(edit, ActionLinkEditSpec):
        if edit.link_type_id not in link_types:
            issues.append(
                ValidationIssue(
                    code="unknown_link_type",
                    message=f"Edit references unknown link_type_id '{edit.link_type_id}'",
                    path=f"{base_path}.link_type_id",
                )
            )
        for side, ref in [("from_object_id", edit.from_object_id), ("to_object_id", edit.to_object_id)]:
            if ref.source == "parameter" and ref.name not in params:
                issues.append(
                    ValidationIssue(
                        code="unknown_parameter",
                        message=f"Edit references unknown parameter '{ref.name}'",
                        path=f"{base_path}.{side}",
                    )
                )
    else:
        issues.append(
            ValidationIssue(
                code="unknown_edit_type",
                message=f"Unknown edit type encountered in '{action.action_type_id}'",
                path=base_path,
            )
        )

    return issues


def _validate_criteria_node(
    *,
    action_id: str,
    node: Any,
    path: str,
    params: set[str],
    targets: set[str],
    object_types: dict[str, Any],
) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []

    def check_value(ref: Any, ref_path: str) -> None:
        if ref.source == "parameter":
            if ref.name not in params:
                issues.append(
                    ValidationIssue(
                        code="unknown_parameter",
                        message=f"Submission criteria references unknown parameter '{ref.name}'",
                        path=ref_path,
                    )
                )
        elif ref.source == "property":
            ot_id = ref.object_type_id
            if ot_id not in targets:
                issues.append(
                    ValidationIssue(
                        code="property_outside_target",
                        message=f"Submission criteria property reference '{ot_id}.{ref.name}' is outside action targets",
                        path=ref_path,
                    )
                )
                return
            ot = object_types.get(ot_id)
            if not ot:
                issues.append(
                    ValidationIssue(
                        code="unknown_object_type",
                        message=f"Submission criteria references unknown object_type_id '{ot_id}'",
                        path=ref_path,
                    )
                )
                return
            props = {p.property_id for p in ot.properties}
            if ref.name not in props:
                issues.append(
                    ValidationIssue(
                        code="unknown_property",
                        message=f"Submission criteria references unknown property '{ref.name}' on '{ot_id}'",
                        path=ref_path,
                    )
                )

    node_type = getattr(node, "node_type", None)
    if node_type == "condition":
        check_value(node.left, f"{path}.left")
        if getattr(node, "right", None) is not None:
            check_value(node.right, f"{path}.right")
        return issues

    if node_type == "logical":
        for i, child in enumerate(getattr(node, "children", []) or []):
            issues.extend(
                _validate_criteria_node(
                    action_id=action_id,
                    node=child,
                    path=f"{path}.children[{i}]",
                    params=params,
                    targets=targets,
                    object_types=object_types,
                )
            )
        return issues

    issues.append(
        ValidationIssue(
            code="unknown_criteria_node",
            message=f"Unknown submission criteria node type in '{action_id}'",
            path=path,
        )
    )
    return issues


def _validate_migration_plan(spec: OntologySpec, instructions: Iterable[SchemaMigrationInstruction]) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    object_types = {o.object_type_id: o for o in spec.object_types}
    for i, instr in enumerate(instructions):
        ot = object_types.get(instr.object_type_id)
        if not ot:
            issues.append(
                ValidationIssue(
                    code="unknown_object_type",
                    message=f"Schema migration references unknown object_type_id '{instr.object_type_id}'",
                    path=f"schema_migration_policy.instructions[{i}].object_type_id",
                )
            )
            continue
        if instr.property_id == ot.primary_key:
            issues.append(
                ValidationIssue(
                    code="unsupported_primary_key_migration",
                    message=(
                        "Schema migration framework does not support applying migration instructions on "
                        f"the primary key property ('{ot.primary_key}') of '{ot.object_type_id}'"
                    ),
                    path=f"schema_migration_policy.instructions[{i}].property_id",
                )
            )
    return issues


def validate_change_set(base_spec: OntologySpec, change_set: OntologyChangeSet) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    if change_set.ontology_id != base_spec.ontology_id:
        issues.append(
            ValidationIssue(
                code="ontology_id_mismatch",
                message=f"ChangeSet ontology_id '{change_set.ontology_id}' does not match spec '{base_spec.ontology_id}'",
                path="ontology_id",
            )
        )

    # Reuse spec validation plus operation-specific prechecks by applying to a copy.
    try:
        _ = apply_change_set(base_spec, change_set, validate_only=True)
    except ValueError as e:
        issues.append(ValidationIssue(code="invalid_change_set", message=str(e)))

    # Validate migration plan constraints against base spec (primary key targeting).
    if change_set.schema_migration_plan is not None:
        issues.extend(_validate_migration_plan(base_spec, change_set.schema_migration_plan.instructions))

    return issues


def apply_change_set(
    base_spec: OntologySpec,
    change_set: OntologyChangeSet,
    *,
    validate_only: bool = False,
) -> OntologySpec:
    """
    Apply an OntologyChangeSet to a base OntologySpec.

    When validate_only=True, no output is returned; instead, this raises on the
    first hard violation. This is used to preflight hazardous application.
    """

    if change_set.ontology_id != base_spec.ontology_id:
        raise ValueError(
            f"ChangeSet ontology_id '{change_set.ontology_id}' does not match base spec '{base_spec.ontology_id}'"
        )

    spec = base_spec.model_copy(deep=True)

    def obj_index() -> dict[str, int]:
        return {o.object_type_id: i for i, o in enumerate(spec.object_types)}

    def link_index() -> dict[str, int]:
        return {l.link_type_id: i for i, l in enumerate(spec.link_types)}

    def iface_index() -> dict[str, int]:
        return {it.interface_id: i for i, it in enumerate(spec.interface_types)}

    def action_index() -> dict[str, int]:
        return {a.action_type_id: i for i, a in enumerate(spec.action_types)}

    def function_index() -> dict[str, int]:
        return {f.function_type_id: i for i, f in enumerate(spec.function_types)}

    for op in change_set.operations:
        _apply_operation(spec, op)

    # Attach migration plan (as metadata) when provided.
    if change_set.schema_migration_plan is not None:
        spec.schema_migration_policy = change_set.schema_migration_plan

    # Re-validate by round-tripping through pydantic (catches invariants like primary_key in properties).
    try:
        spec = OntologySpec.model_validate(spec.model_dump(mode="json"))
    except ValidationError as e:
        raise ValueError(str(e)) from e

    errors = validate_ontology_spec(spec)
    hard = [i for i in errors if i.severity == "error"]
    if hard:
        raise ValueError("; ".join(f"{x.code}: {x.message}" for x in hard[:10]))

    if validate_only:
        return base_spec

    return spec


def _apply_operation(spec: OntologySpec, op: ChangeOperation) -> None:
    # Imports locally to avoid circular typing in the module top.
    from .models import (
        AddActionTypeOp,
        AddFunctionTypeOp,
        AddInterfaceTypeOp,
        AddLinkTypeOp,
        AddObjectTypeOp,
        DeleteLinkTypeOp,
        DeleteObjectTypeOp,
        SetDynamicSecurityOp,
        UpdateObjectTypeOp,
    )

    if isinstance(op, AddObjectTypeOp):
        if any(o.object_type_id == op.object_type.object_type_id for o in spec.object_types):
            raise ValueError(f"ObjectType already exists: {op.object_type.object_type_id}")
        spec.object_types.append(op.object_type)
        return

    if isinstance(op, UpdateObjectTypeOp):
        idx = next((i for i, o in enumerate(spec.object_types) if o.object_type_id == op.object_type_id), None)
        if idx is None:
            raise ValueError(f"ObjectType not found: {op.object_type_id}")
        ot = spec.object_types[idx]
        patch = op.patch

        if patch.primary_key is not None and patch.primary_key != ot.primary_key:
            raise ValueError(
                "Primary key changes are not supported by the current migration framework; "
                "keep the primary_key stable"
            )

        if patch.description is not None:
            ot.description = patch.description
        if patch.datasource_mode is not None:
            ot.datasource_mode = patch.datasource_mode

        existing_props = {p.property_id for p in ot.properties}
        for p in patch.add_properties:
            if p.property_id in existing_props:
                raise ValueError(f"Property already exists on '{ot.object_type_id}': {p.property_id}")
            ot.properties.append(p)
            existing_props.add(p.property_id)

        for pid in patch.remove_property_ids:
            if pid == ot.primary_key:
                raise ValueError(f"Cannot remove primary key property '{pid}' from '{ot.object_type_id}'")
            if pid not in existing_props:
                raise ValueError(f"Property not found on '{ot.object_type_id}': {pid}")
            ot.properties = [p for p in ot.properties if p.property_id != pid]
            existing_props.remove(pid)

        impl = set(ot.implements)
        impl |= set(patch.add_implements)
        impl -= set(patch.remove_implements)
        ot.implements = sorted(impl)

        spec.object_types[idx] = ot
        return

    if isinstance(op, DeleteObjectTypeOp):
        # For safety, block deletion if referenced by link types / actions.
        if any(l.from_object_type_id == op.object_type_id or l.to_object_type_id == op.object_type_id for l in spec.link_types):
            raise ValueError(f"Cannot delete ObjectType '{op.object_type_id}' while LinkTypes reference it")
        if any(op.object_type_id in a.target_object_type_ids for a in spec.action_types):
            raise ValueError(f"Cannot delete ObjectType '{op.object_type_id}' while ActionTypes reference it")
        spec.object_types = [o for o in spec.object_types if o.object_type_id != op.object_type_id]
        return

    if isinstance(op, AddLinkTypeOp):
        if any(l.link_type_id == op.link_type.link_type_id for l in spec.link_types):
            raise ValueError(f"LinkType already exists: {op.link_type.link_type_id}")
        spec.link_types.append(op.link_type)
        return

    if isinstance(op, DeleteLinkTypeOp):
        if any(isinstance(e, ActionLinkEditSpec) and e.link_type_id == op.link_type_id for a in spec.action_types for e in a.edits):
            raise ValueError(f"Cannot delete LinkType '{op.link_type_id}' while ActionTypes reference it")
        spec.link_types = [l for l in spec.link_types if l.link_type_id != op.link_type_id]
        return

    if isinstance(op, AddInterfaceTypeOp):
        if any(i.interface_id == op.interface_type.interface_id for i in spec.interface_types):
            raise ValueError(f"Interface already exists: {op.interface_type.interface_id}")
        spec.interface_types.append(op.interface_type)
        return

    if isinstance(op, DeleteInterfaceTypeOp):
        if any(op.interface_id in o.implements for o in spec.object_types):
            raise ValueError(f"Cannot delete Interface '{op.interface_id}' while ObjectTypes implement it")
        spec.interface_types = [i for i in spec.interface_types if i.interface_id != op.interface_id]
        return

    if isinstance(op, AddActionTypeOp):
        if any(a.action_type_id == op.action_type.action_type_id for a in spec.action_types):
            raise ValueError(f"ActionType already exists: {op.action_type.action_type_id}")
        spec.action_types.append(op.action_type)
        return

    if isinstance(op, DeleteActionTypeOp):
        spec.action_types = [a for a in spec.action_types if a.action_type_id != op.action_type_id]
        return

    if isinstance(op, AddFunctionTypeOp):
        if any(f.function_type_id == op.function_type.function_type_id for f in spec.function_types):
            raise ValueError(f"FunctionType already exists: {op.function_type.function_type_id}")
        spec.function_types.append(op.function_type)
        return

    if isinstance(op, DeleteFunctionTypeOp):
        spec.function_types = [f for f in spec.function_types if f.function_type_id != op.function_type_id]
        return

    if isinstance(op, SetDynamicSecurityOp):
        spec.dynamic_security = op.dynamic_security
        return

    raise ValueError(f"Unsupported change operation: {type(op).__name__}")


def parse_ontology_spec(data: Any) -> tuple[Optional[OntologySpec], list[ValidationIssue]]:
    """
    Helper for ActionTypes: parse + validate, returning (spec, issues).
    """
    try:
        spec = OntologySpec.model_validate(data)
    except ValidationError as e:
        return None, [ValidationIssue(code="schema_validation_error", message=str(e))]

    issues = validate_ontology_spec(spec)
    return spec, issues

