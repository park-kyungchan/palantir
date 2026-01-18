from __future__ import annotations

import json
import re
import uuid
from dataclasses import dataclass
from hashlib import sha256
from typing import Any, Dict, Iterable, List, Optional

from lib.oda.ontology.job import Job
from lib.oda.ontology.plan import Plan


_ACTION_LINE_RE = re.compile(
    r"^(?:-\s*)?ACTION\s*:?\s*(?P<api>[A-Za-z][A-Za-z0-9_]*(?:\.[A-Za-z0-9_]+)*)"
    r"(?:\s+(?P<payload>\{.*\}))?\s*$",
    re.IGNORECASE,
)


def _stable_uuid(namespace: uuid.UUID, name: str) -> str:
    return str(uuid.uuid5(namespace, name))


def _first_nonempty_line(text: str) -> str:
    for line in text.splitlines():
        if line.strip():
            return line.strip()
    return ""


def _extract_objective(goal: str) -> str:
    for line in goal.splitlines():
        stripped = line.strip()
        if stripped.lower().startswith("objective:"):
            value = stripped.split(":", 1)[1].strip()
            return value or _first_nonempty_line(goal) or "unspecified"
    return _first_nonempty_line(goal) or "unspecified"


def _iter_action_specs(goal: str) -> Iterable[tuple[str, Dict[str, Any]]]:
    for line in goal.splitlines():
        match = _ACTION_LINE_RE.match(line.strip())
        if not match:
            continue

        action_api = (match.group("api") or "").strip().lower()
        payload = (match.group("payload") or "").strip()

        if not payload:
            yield action_api, {}
            continue

        try:
            parsed = json.loads(payload)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid ACTION JSON payload for {action_api}: {e}") from e

        if not isinstance(parsed, dict):
            raise ValueError(f"ACTION payload must be a JSON object for {action_api}")

        yield action_api, parsed


@dataclass(frozen=True)
class DeterministicPlan:
    plan: Plan
    mode: str
    sha256: str
    jobs_parsed: int


def generate_deterministic_plan(goal: str) -> DeterministicPlan:
    digest = sha256(goal.encode("utf-8")).hexdigest()
    namespace = uuid.uuid5(uuid.NAMESPACE_URL, "orion://deterministic-plan")
    plan_uuid = _stable_uuid(namespace, f"plan:{digest}")

    objective = _extract_objective(goal)

    jobs: List[Job] = []
    for idx, (action_api, action_args) in enumerate(_iter_action_specs(goal), start=1):
        job_id = _stable_uuid(namespace, f"{plan_uuid}:job:{idx}:{action_api}:{sha256(json.dumps(action_args, sort_keys=True).encode('utf-8')).hexdigest()}")
        jobs.append(
            Job(
                id=job_id,
                action_name=action_api,
                action_args=action_args,
                description=f"Deterministic action: {action_api}",
                evidence="deterministic_planner",
                role="kernel",
            )
        )

    if not jobs:
        raise ValueError(
            "No deterministic ACTION lines found; include lines like "
            "`ACTION learning.save_state {\"user_id\":\"u1\",\"theta\":0.1}`"
        )

    plan = Plan(
        id=plan_uuid,
        plan_id=f"PLAN-{digest[:8]}",
        objective=objective,
        ontology_impact=[],
        jobs=jobs,
        research_context={
            "mode": "deterministic",
            "sha256": digest,
            "jobs_parsed": len(jobs),
        },
    )

    return DeterministicPlan(
        plan=plan,
        mode="deterministic",
        sha256=digest,
        jobs_parsed=len(jobs),
    )

