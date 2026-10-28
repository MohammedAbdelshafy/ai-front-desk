"""Dr. Mia Clinic OS workflow registry and clinic operations primitives.

The registry describes supported outcomes and their actual readiness state.
A listed workflow is not automatically enabled for a live clinic.
"""
from .workflow_registry import get_workflow_skill, load_workflow_skills

__all__ = ["get_workflow_skill", "load_workflow_skills"]
