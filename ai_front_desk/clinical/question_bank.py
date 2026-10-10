"""Versioned, conditional question bank with FHIR R4-compatible export.

A question bank is a versioned JSON document. Every question has a stable id,
a type, display text, and optional conditional display rules. Answers are
validated against the question definition. Nothing here performs clinical
reasoning — it only structures patient-reported information.
"""
from __future__ import annotations

import copy
import json
import math
from datetime import date
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


QUESTION_TYPES = {"text", "choice", "multi_choice", "yes_no", "number", "date"}

# Standard escape hatches every patient-facing question supports.
ESCAPE_OPTIONS = ("I don't know", "Not applicable", "Prefer not to answer")


@dataclass(frozen=True)
class Question:
    qid: str
    section: str
    text: str
    qtype: str = "text"
    required: bool = False
    options: tuple[str, ...] = ()
    # show_if: {"qid": <id>, "equals": <value>} or {"qid": <id>, "in": [...]}
    show_if: dict[str, Any] = field(default_factory=dict)
    allow_escape: bool = True
    fhir_code: str = ""
    review_status: str = "draft"  # draft | clinician_reviewed | approved

    def is_visible(self, answers: dict[str, Any]) -> bool:
        if not self.show_if:
            return True
        target = self.show_if.get("qid")
        if target not in answers:
            return False
        actual = answers[target]
        if "equals" in self.show_if:
            return actual == self.show_if["equals"]
        if "in" in self.show_if:
            return actual in self.show_if["in"]
        return False

    def validate(self, value: Any) -> list[str]:
        errors: list[str] = []
        if value is None or (isinstance(value, str) and not value.strip()) or value == []:
            if self.required:
                errors.append(f"{self.qid}: answer required")
            return errors
        if self.qtype not in QUESTION_TYPES:
            return [f"{self.qid}: unsupported question type '{self.qtype}'"]
        if isinstance(value, str) and value in ESCAPE_OPTIONS:
            # Date/number FHIR items cannot safely carry text escape values.
            if self.allow_escape and self.qtype not in ("date", "number"):
                return errors
            return [f"{self.qid}: escape answer is not allowed for this question type"]
        if self.qtype in ("choice", "yes_no"):
            allowed = set(self.options) | (set(ESCAPE_OPTIONS) if self.allow_escape else set())
            if not isinstance(value, str) or value not in allowed:
                errors.append(f"{self.qid}: answer is not an allowed option")
        elif self.qtype == "multi_choice":
            if not isinstance(value, (list, tuple)):
                return [f"{self.qid}: expected a list of selections"]
            allowed = set(self.options) | (set(ESCAPE_OPTIONS) if self.allow_escape else set())
            bad = [v for v in value if not isinstance(v, str) or v not in allowed]
            if bad:
                errors.append(f"{self.qid}: one or more selections are invalid")
            if any(v in ESCAPE_OPTIONS for v in value) and len(value) > 1:
                errors.append(f"{self.qid}: an escape answer cannot be combined with other selections")
        elif self.qtype in ("text", "date"):
            if not isinstance(value, str):
                errors.append(f"{self.qid}: expected text")
            elif self.qtype == "date":
                try:
                    date.fromisoformat(value)
                except ValueError:
                    errors.append(f"{self.qid}: expected an ISO date (YYYY-MM-DD)")
        elif self.qtype == "number":
            if isinstance(value, bool):
                return [f"{self.qid}: expected a finite number"]
            try:
                numeric = float(value)
                if not math.isfinite(numeric):
                    errors.append(f"{self.qid}: expected a finite number")
            except (TypeError, ValueError, OverflowError):
                errors.append(f"{self.qid}: expected a finite number")
        return errors


@dataclass(frozen=True)
class QuestionBank:
    bank_id: str
    version: str
    title: str
    specialty: str
    language: str
    reviewer: str
    review_status: str
    review_date: str
    questions: tuple[Question, ...]

    def visible_questions(self, answers: dict[str, Any]) -> list[Question]:
        return [q for q in self.questions if q.is_visible(answers)]

    def get(self, qid: str) -> Question | None:
        for q in self.questions:
            if q.qid == qid:
                return q
        return None

    def validate_answers(self, answers: dict[str, Any]) -> list[str]:
        if not isinstance(answers, dict):
            return ["answers: expected an object keyed by question id"]
        errors: list[str] = []
        known = {q.qid for q in self.questions}
        for qid in sorted(set(answers) - known):
            errors.append(f"{qid}: unknown question id")
        visible = {q.qid for q in self.visible_questions(answers)}
        for q in self.questions:
            if q.qid in visible:
                errors.extend(q.validate(answers.get(q.qid)))
            elif q.qid in answers and answers[q.qid] not in (None, "", []):
                errors.append(f"{q.qid}: answered but question not currently visible")
        return errors

    def missing_required(self, answers: dict[str, Any]) -> list[str]:
        missing = []
        for q in self.visible_questions(answers):
            v = answers.get(q.qid)
            if q.required and (v is None or (isinstance(v, str) and not v.strip())):
                missing.append(q.qid)
        return missing

    # -- FHIR R4 Questionnaire export -------------------------------------
    def to_fhir_questionnaire(self) -> dict[str, Any]:
        items = []
        for q in self.questions:
            item: dict[str, Any] = {
                "linkId": q.qid,
                "text": q.text,
                "type": _fhir_type(q.qtype),
                "required": q.required,
            }
            if q.options:
                item["answerOption"] = [
                    {"valueString": o} for o in q.options
                ] + ([{"valueString": e} for e in ESCAPE_OPTIONS] if q.allow_escape else [])
            if q.qtype == "multi_choice":
                item["repeats"] = True
            if q.show_if:
                values = [q.show_if["equals"]] if "equals" in q.show_if else list(q.show_if.get("in", []))
                item["enableWhen"] = [
                    {"question": q.show_if["qid"], "operator": "=", "answerString": str(value)}
                    for value in values
                ]
                if len(values) > 1:
                    item["enableBehavior"] = "any"
            if q.fhir_code:
                item["code"] = [{"code": q.fhir_code}]
            items.append(item)
        return {
            "resourceType": "Questionnaire",
            "id": f"{self.bank_id}-{self.version}",
            "url": f"https://mbm.example/fhir/Questionnaire/{self.bank_id}/{self.version}",
            "version": self.version,
            "title": self.title,
            "status": "active" if self.review_status == "approved" else "draft",
            "item": items,
        }


def _fhir_type(qtype: str) -> str:
    return {
        "text": "string",
        "choice": "choice",
        "multi_choice": "choice",
        "yes_no": "choice",
        "number": "decimal",
        "date": "date",
    }.get(qtype, "string")


def load_bank(path: str | Path) -> QuestionBank:
    raw = json.loads(Path(path).read_text())
    questions = tuple(
        Question(
            qid=q["qid"],
            section=q.get("section", ""),
            text=q["text"],
            qtype=q.get("qtype", "text"),
            required=bool(q.get("required", False)),
            options=tuple(q.get("options", ())),
            show_if=dict(q.get("show_if", {})),
            allow_escape=bool(q.get("allow_escape", True)),
            fhir_code=q.get("fhir_code", ""),
            review_status=q.get("review_status", "draft"),
        )
        for q in raw["questions"]
    )
    return QuestionBank(
        bank_id=raw["bank_id"],
        version=raw["version"],
        title=raw["title"],
        specialty=raw.get("specialty", ""),
        language=raw.get("language", "en"),
        reviewer=raw.get("reviewer", ""),
        review_status=raw.get("review_status", "draft"),
        review_date=raw.get("review_date", ""),
        questions=questions,
    )


def bank_snapshot(bank: QuestionBank) -> dict[str, Any]:
    """Immutable snapshot stored alongside each submission for provenance."""
    return {
        "bank_id": bank.bank_id,
        "version": bank.version,
        "title": bank.title,
        "review_status": bank.review_status,
        "review_date": bank.review_date,
        "question_count": len(bank.questions),
    }
