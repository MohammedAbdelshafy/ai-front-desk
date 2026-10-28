"""Checks the versioned, explicit-readiness workflow registry used by Dr. Mia Clinic OS."""
import json

import pytest

from ai_front_desk.clinic_os.workflow_registry import (
    READINESS_STATES,
    load_workflow_skills,
)


def test_workflow_skill_catalog_contains_the_planned_outcome_modules():
    skills = load_workflow_skills()
    by_id = {item["skill_id"]: item for item in skills}

    assert {
        "pre-visit-history",
        "missed-opportunity-recovery",
        "appointment-reminders",
        "no-show-recovery",
        "patient-growth",
        "daily-operations-scorecard",
        "weekly-quality-scorecard",
        "recall-reactivation",
        "clinician-prescribing-assistant",
    }.issubset(by_id)
    assert by_id["pre-visit-history"]["readiness_status"] == "demo_only"
    assert by_id["daily-operations-scorecard"]["readiness_status"] == "limited_implementation"
    assert by_id["clinician-prescribing-assistant"]["readiness_status"] == "clinical_review_required"


def test_every_skill_has_outcome_inputs_outputs_and_safety_boundaries():
    skills = load_workflow_skills()
    required = {
        "skill_id", "version", "name", "outcome", "readiness_status",
        "required_inputs", "outputs", "guardrails", "activation_requirements",
    }

    assert skills
    for item in skills:
        assert required <= set(item)
        assert item["readiness_status"] in READINESS_STATES
        assert item["outcome"].strip()
        assert item["guardrails"]
        assert item["activation_requirements"]


def test_registry_rejects_duplicate_skill_ids(tmp_path):
    invalid = {
        "skill_id": "same-id",
        "version": "1.0.0",
        "name": "Example",
        "outcome": "Example outcome",
        "readiness_status": "design_only",
        "required_inputs": [],
        "outputs": [],
        "guardrails": ["Do not send messages."],
        "activation_requirements": ["Human approval."],
    }
    (tmp_path / "a.json").write_text(json.dumps(invalid), encoding="utf-8")
    (tmp_path / "b.json").write_text(json.dumps(invalid), encoding="utf-8")

    with pytest.raises(ValueError, match="duplicate workflow skill id"):
        load_workflow_skills(tmp_path)


def test_registry_rejects_unknown_readiness_state(tmp_path):
    invalid = {
        "skill_id": "bad-state",
        "version": "1.0.0",
        "name": "Example",
        "outcome": "Example outcome",
        "readiness_status": "production_ready",
        "required_inputs": [],
        "outputs": [],
        "guardrails": ["Do not send messages."],
        "activation_requirements": ["Human approval."],
    }
    (tmp_path / "bad.json").write_text(json.dumps(invalid), encoding="utf-8")

    with pytest.raises(ValueError, match="unknown readiness_status"):
        load_workflow_skills(tmp_path)
