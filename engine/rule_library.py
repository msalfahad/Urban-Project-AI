"""The Urban Projects rule library: owner knowledge, versioned.

An owner rule is not a constant in an engine file. It is a RECORD, with
a version, a date, a source, a scope and — above all — a place in a
priority order, because an owner standard is what applies when the
drawing does not say otherwise:

    PROJECT DRAWING / SPECIFICATION     what this building actually is
    PROJECT-SPECIFIC OWNER OVERRIDE     what the owner said about THIS one
    URBAN PROJECTS OWNER STANDARD       what the company does by default
    UNKNOWN / ASK OWNER                 and nothing below it is invented

A default never bypasses geometry. Where a rule carries a dimension —
0.50 m of marble around an elevator door, a tile height, a riser — and
the drawing establishes another, the DRAWING wins and the resolution says
so. Where the geometry a rule needs is not established, the answer is not
the default: it is the rule's own `unknown_behavior`, which is either a
named refusal or an OWNER_RULE_REQUEST carrying the exact question.

Nothing here measures anything. This module says what rule applies, at
what version, from what source, and what to do when nobody knows.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path

MODEL = "URBAN_PROJECTS_RULE_LIBRARY_V1"

# --- the priority order, highest first -----------------------------------
SRC_DRAWING = "PROJECT_DRAWING_OR_SPECIFICATION"
SRC_PROJECT = "PROJECT_SPECIFIC_OWNER_OVERRIDE"
SRC_STANDARD = "URBAN_PROJECTS_OWNER_STANDARD"
SRC_UNKNOWN = "UNKNOWN_ASK_OWNER"
PRIORITY = (SRC_DRAWING, SRC_PROJECT, SRC_STANDARD, SRC_UNKNOWN)

OWNER_RULE_REQUEST = "OWNER_RULE_REQUEST"
NO_SUCH_RULE = "NO_APPROVED_RULE_EXISTS_FOR_THIS"
GEOMETRY_NOT_ESTABLISHED = "THE_GEOMETRY_THIS_RULE_NEEDS_IS_NOT_ESTABLISHED"

DEFAULT = "DEFAULT"
MANDATORY = "MANDATORY"

# Every field a rule record must carry. A rule missing one of these is
# not a rule: it is a habit somebody typed in, and it is refused.
REQUIRED_FIELDS = (
    "rule_id", "rule_name", "trade", "scope", "default_or_mandatory",
    "owner_confirmed", "version", "effective_date", "source",
    "project_override_allowed", "required_geometry", "calculation_method",
    "unit", "exceptions", "unknown_behavior",
)

LIBRARY_PATH = "data/trade_rules/URBAN_PROJECTS_RULE_LIBRARY.json"


class RuleRefused(ValueError):
    """A record that does not carry what a rule has to carry."""


@dataclass
class Rule:
    rule_id: str = ""
    rule_name: str = ""
    trade: str = ""
    scope: str = ""
    country_context: str = ""
    default_or_mandatory: str = DEFAULT
    owner_confirmed: bool = False
    version: str = ""
    effective_date: str = ""
    source: str = ""
    project_override_allowed: bool = True
    required_geometry: tuple = ()
    calculation_method: str = ""
    unit: str = ""
    value: object = None
    exceptions: tuple = ()
    unknown_behavior: str = OWNER_RULE_REQUEST
    notes: str = ""

    def record(self) -> dict:
        return {
            "rule_id": self.rule_id,
            "rule_name": self.rule_name,
            "trade": self.trade,
            "scope": self.scope,
            "country_context": self.country_context,
            "default_or_mandatory": self.default_or_mandatory,
            "owner_confirmed": self.owner_confirmed,
            "version": self.version,
            "effective_date": self.effective_date,
            "source": self.source,
            "project_override_allowed": self.project_override_allowed,
            "required_geometry": list(self.required_geometry),
            "calculation_method": self.calculation_method,
            "unit": self.unit,
            "value": self.value,
            "exceptions": list(self.exceptions),
            "unknown_behavior": self.unknown_behavior,
            "notes": self.notes,
        }

    def rule_hash(self) -> str:
        return hashlib.sha256(
            json.dumps(self.record(), sort_keys=True, default=str)
            .encode("utf-8")).hexdigest()[:16]


@dataclass
class Resolution:
    """What applies, where it came from, and what is still missing."""

    rule_id: str = ""
    value: object = None
    unit: str = ""
    source: str = SRC_UNKNOWN
    rule_version: str = ""
    established: bool = False
    what_is_missing: tuple = ()
    question_for_the_owner: str = ""
    why: str = ""

    def record(self) -> dict:
        return {
            "rule_id": self.rule_id,
            "value": self.value,
            "unit": self.unit,
            "applied_from": self.source,
            "rule_version": self.rule_version,
            "established": self.established,
            "what_is_missing": list(self.what_is_missing),
            "question_for_the_owner": self.question_for_the_owner,
            "why": self.why,
        }


@dataclass
class Library:
    rules: dict = field(default_factory=dict)
    library_version: str = ""
    notes: dict = field(default_factory=dict)

    def get(self, rule_id: str):
        return self.rules.get(rule_id)

    def by_scope(self, scope: str) -> list:
        return [r for r in self.rules.values() if r.scope == scope]

    def record(self) -> dict:
        return {
            "model": MODEL,
            "RULE_LIBRARY_HASH": self.library_hash(),
            "library_version": self.library_version,
            "priority": list(PRIORITY),
            "rules": [r.record() for r in sorted(
                self.rules.values(), key=lambda r: r.rule_id)],
            "rule_hashes": {r.rule_id: r.rule_hash()
                            for r in self.rules.values()},
            "notes": dict(self.notes),
        }

    def library_hash(self) -> str:
        parts = [MODEL, self.library_version] + [
            f"{r.rule_id}:{r.rule_hash()}"
            for r in sorted(self.rules.values(), key=lambda r: r.rule_id)]
        return hashlib.sha256("|".join(parts).encode(
            "utf-8")).hexdigest()[:24]


def model_hash() -> str:
    parts = ([MODEL] + list(PRIORITY) + list(REQUIRED_FIELDS)
             + [OWNER_RULE_REQUEST, NO_SUCH_RULE, GEOMETRY_NOT_ESTABLISHED,
                DEFAULT, MANDATORY])
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:24]


def build(records, *, library_version: str = "", notes=None) -> Library:
    """Every record checked for the fields a rule has to carry."""
    lib = Library(library_version=library_version, notes=dict(notes or {}))
    for rec in records:
        missing = [f for f in REQUIRED_FIELDS if f not in rec]
        if missing:
            raise RuleRefused(
                f"{rec.get('rule_id', '<no id>')} is missing "
                + ", ".join(missing)
                + ". A rule nobody can date, version or source is not a "
                  "rule this project applies")
        rule = Rule(
            rule_id=rec["rule_id"], rule_name=rec["rule_name"],
            trade=rec["trade"], scope=rec["scope"],
            country_context=rec.get("country_context", ""),
            default_or_mandatory=rec["default_or_mandatory"],
            owner_confirmed=bool(rec["owner_confirmed"]),
            version=str(rec["version"]),
            effective_date=str(rec["effective_date"]),
            source=rec["source"],
            project_override_allowed=bool(rec["project_override_allowed"]),
            required_geometry=tuple(rec["required_geometry"]),
            calculation_method=rec["calculation_method"],
            unit=rec["unit"], value=rec.get("value"),
            exceptions=tuple(rec["exceptions"]),
            unknown_behavior=rec["unknown_behavior"],
            notes=rec.get("notes", ""))
        if rule.rule_id in lib.rules:
            raise RuleRefused(f"{rule.rule_id} is declared twice")
        lib.rules[rule.rule_id] = rule
    return lib


def load(path: str = LIBRARY_PATH) -> Library:
    p = Path(path)
    if not p.exists():
        return Library()
    data = json.loads(p.read_text(encoding="utf-8"))
    return build(data.get("rules", []),
                 library_version=data.get("library_version", ""),
                 notes=data.get("notes", {}))


def resolve(library: Library, rule_id: str, *, drawing=None,
            project=None, geometry_established=True,
            missing=()) -> Resolution:
    """What applies here, in the priority order, and never a guess.

    `drawing` is what the project's own drawing or specification
    establishes; `project` is what the owner said about THIS project.
    Either overrides the standard — and a rule marked MANDATORY with
    project_override_allowed false is not overridden by a project note,
    only by the drawing.
    """
    rule = library.get(rule_id)
    if rule is None:
        return Resolution(
            rule_id=rule_id, source=SRC_UNKNOWN, established=False,
            what_is_missing=(NO_SUCH_RULE,),
            question_for_the_owner=(
                f"no approved rule exists for {rule_id}. What is the "
                "Urban Projects standard, and is it a default or "
                "mandatory?"),
            why="nothing in the library covers this")

    if drawing is not None:
        return Resolution(
            rule_id=rule_id, value=drawing, unit=rule.unit,
            source=SRC_DRAWING, rule_version=rule.version,
            established=True,
            why=("the drawing or specification establishes this, and a "
                 "default never overrides what the project documents"))
    if project is not None:
        if not rule.project_override_allowed:
            return Resolution(
                rule_id=rule_id, value=rule.value, unit=rule.unit,
                source=SRC_STANDARD, rule_version=rule.version,
                established=rule.value is not None,
                why=(f"{rule_id} is {MANDATORY} and does not take a "
                     "project override. Only the drawing changes it"))
        return Resolution(
            rule_id=rule_id, value=project, unit=rule.unit,
            source=SRC_PROJECT, rule_version=rule.version,
            established=True,
            why="the owner gave this project its own answer")
    if not geometry_established:
        return Resolution(
            rule_id=rule_id, value=None, unit=rule.unit,
            source=SRC_UNKNOWN, rule_version=rule.version,
            established=False,
            what_is_missing=tuple(missing or rule.required_geometry),
            question_for_the_owner=(
                f"{rule.rule_name}: the geometry it needs is not "
                "established (" + ", ".join(
                    missing or rule.required_geometry) + ")"),
            why=(f"{rule.unknown_behavior}. A default dimension is not "
                 "applied to geometry nobody has established"))
    if rule.value is None:
        return Resolution(
            rule_id=rule_id, value=None, unit=rule.unit,
            source=SRC_UNKNOWN, rule_version=rule.version,
            established=False,
            what_is_missing=(rule.unknown_behavior,),
            question_for_the_owner=(
                f"{rule.rule_name}: the library carries the method and no "
                "value. What does Urban Projects use?"),
            why=rule.unknown_behavior)
    return Resolution(
        rule_id=rule_id, value=rule.value, unit=rule.unit,
        source=SRC_STANDARD, rule_version=rule.version, established=True,
        why=(f"the Urban Projects standard, {rule.default_or_mandatory} "
             f"since {rule.effective_date}"))


def owner_rule_request(term: str, *, where: str, question: str,
                       kind: str = "TERM") -> dict:
    """An unknown term is a question with an address, never a guess."""
    return {
        "exception": OWNER_RULE_REQUEST,
        "kind": kind,
        "exact_term": term,
        "where_in_the_drawing": where,
        "question_for_the_owner": question,
        "what_was_refused": ("any classification, rule or quantity "
                             "resting on this term"),
    }
