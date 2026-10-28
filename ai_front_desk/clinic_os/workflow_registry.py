"""Load and validate versioned, readiness-labelled clinic workflow skills."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


READINESS_STATES = frozenset({
    "demo_only",
    "design_only",
    "limited_implementation",
    "clinical_review_required",
})
REQUIRED_FIELDS = frozenset({
    "skill_id",
    "version",
    "name",
    "outcome",
    "readiness_status",
    "required_inputs",
    "outputs",
    "guardrails",
    "activation_requirements",
})


def _validate_skill(raw: Any, source: Path) -> dict[str, Any]:
    if not isinstance(raw, dict):
        raise ValueError(f"{source.name}: workflow skill must be a JSON object")
    missing = sorted(REQUIRED_FIELDS - set(raw))
    if missing:
        raise ValueError(f"{source.name}: missing required fields: {', '.join(missing)}")
    for key in ("skill_id", "version", "name", "outcome", "readiness_status"):
        if not isinstance(raw[key], str) or not raw[key].strip():
            raise ValueError(f"{source.name}: {key} must be non-empty text")
    for key in ("required_inputs", "outputs", "guardrails", "activation_requirements"):
        values = raw[key]
        if not isinstance(values, list) or any(
            not isinstance(value, str) or not value.strip() for value in values
        ):
            raise ValueError(f"{source.name}: {key} must be a list of non-empty strings")
    if raw["readiness_status"] not in READINESS_STATES:
        raise ValueError(
            f"{source.name}: unknown readiness_status {raw['readiness_status']!r}"
        )
    if raw["skill_id"].strip() != raw["skill_id"] or " " in raw["skill_id"]:
        raise ValueError(f"{source.name}: skill_id must be a stable, space-free identifier")
    return raw


def load_workflow_skills(directory: str | Path | None = None) -> list[dict[str, Any]]:
    """Return validated workflow definitions, sorted by ID, without enabling any."""
    root = Path(directory) if directory is not None else Path(__file__).resolve().parent / "skills"
    if not root.exists() or not root.is_dir():
        raise ValueError(f"workflow skill directory does not exist: {root}")
    skills: list[dict[str, Any]] = []
    seen: set[str] = set()
    for path in sorted(root.glob("*.json")):
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ValueError(f"{path.name}: could not read workflow skill JSON") from exc
        skill = _validate_skill(raw, path)
        skill_id = skill["skill_id"]
        if skill_id in seen:
            raise ValueError(f"duplicate workflow skill id: {skill_id}")
        seen.add(skill_id)
        skills.append(skill)
    return sorted(skills, key=lambda item: item["skill_id"])


def get_workflow_skill(skill_id: str, directory: str | Path | None = None) -> dict[str, Any]:
    """Retrieve a single workflow definition by stable ID; never activates it."""
    if not isinstance(skill_id, str) or not skill_id.strip():
        raise ValueError("skill_id must be non-empty text")
    for skill in load_workflow_skills(directory):
        if skill["skill_id"] == skill_id:
            return skill
    raise KeyError(f"unknown workflow skill: {skill_id}")
