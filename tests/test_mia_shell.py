"""Tests for MiaShell: manifest integrity and honest task stages."""
import pytest

from ai_front_desk.clinical.mia_shell import (
    CharacterManifest, TaskStage, DENTAL_MIA, STAGES,
)


def test_dental_mia_manifest_safety_boundaries():
    m = DENTAL_MIA
    assert m.character_id == "dental-mia-v1"
    assert "guide_intake" in m.allowed_actions
    assert "prescribe" not in m.allowed_actions
    assert any("Never diagnose" in b for b in m.safety_boundaries)


def test_manifest_serializes():
    d = DENTAL_MIA.to_dict()
    assert d["name"] == "Dr. Mia"
    assert isinstance(d["allowed_actions"], list)


def test_stage_transitions_recorded_with_reason():
    t = TaskStage(DENTAL_MIA)
    t.transition("listening", reason="patient opened intake")
    t.transition("working", reason="validating answers")
    t.transition("completed", reason="submission saved")
    assert t.stage == "completed"
    assert [h["stage"] for h in t.history] == ["idle", "listening", "working", "completed"]
    assert all("at" in h and "reason" in h for h in t.history)


def test_unknown_stage_rejected():
    t = TaskStage(DENTAL_MIA)
    with pytest.raises(ValueError):
        t.transition("teleporting")


def test_all_expected_stages_defined():
    for s in ("idle", "listening", "planning", "working", "waiting_for_input",
              "awaiting_approval", "handing_off", "completed", "failed"):
        assert s in STAGES


def test_character_does_not_grant_permissions():
    # The manifest describes presentation; it must not contain data-access grants.
    d = DENTAL_MIA.to_dict()
    blob = str(d).lower()
    assert "bypass" not in blob
    assert "admin" not in blob
