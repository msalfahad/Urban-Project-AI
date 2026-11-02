"""Per-project configuration: the DECLARED PROJECT FACTS of one villa (A1 class B).

Owner follow-up directive 2026-11-02 (MISSION.md, A1): every project-specific correction is one of
(A) a drawing-derived rule (reusable logic with tests), (B) a DECLARED PROJECT FACT kept in a per-project
config, or (C) an unexplained patch, which is removed. This module is the schema and the loader for
class B (T-450 part 1). It holds no project's data and nothing in the engine reads it yet: part 2 and
T-449 move project values out of engine code into files of this shape.

A config file is JSON:

    {
      "schema": "URBAN_PROJECT_CONFIG_V1",
      "project_id": "VILLA-SYNTH-01",          # generic id, A-Z 0-9 _ -
      "config_version": "1.0.0",               # semver; a changed fact is a new config version
      "facts": [ <fact>, ... ]
    }

and every fact carries exactly the fields the directive names:

    fact_id          stable id, upper case dotted (e.g. "WP.UPTURN.HEIGHT")
    version          integer >= 1; a corrected fact is a new version, the old one is SUPERSEDED
    quantity_kind    LENGTH / AREA / VOLUME / MASS / MASS_PER_AREA / COUNT / COUNT_PER_AREA /
                     RATIO / CATEGORY / BOOLEAN; fixes which units are legal
    value            the declared value; never null (an unknown fact is left out and every line
                     it affects stays HELD; it is never written as 0 or as a default)
    unit             one of the units legal for quantity_kind ("none" for CATEGORY / BOOLEAN)
    source           {"kind": DRAWING | SPECIFICATION | OWNER_DECISION | CONSULTANT_RFI |
                      SITE_RECORD | SUPPLIER_DATA, "reference": "<drawing / document ref>"}
    approval         {"status": APPROVED | PENDING | SUPERSEDED, "by": PROJECT_OWNER |
                      CONSULTANT | DESIGNER (required when APPROVED), "date": "YYYY-MM-DD"}
    affected_lines   non-empty list of BOQ line ids the fact moves
    confidence       CONFIRMED | PROVISIONAL
    supersedes       optional: the version of the same fact_id this one replaces
    note             optional free text

Refused at load (all problems are reported together, nothing is half-loaded):
- a freelancer workbook, a benchmark or an earlier engine result as a source (that is class C);
- a value of the wrong type for its kind, a non-finite number, a negative physical quantity;
- a unit that is not legal for the kind (e.g. a LENGTH in m2);
- CONFIRMED without an APPROVED approval (a PENDING value is PROVISIONAL; a SUPERSEDED version keeps the
  confidence it had);
- two active versions of one fact, a duplicate (fact_id, version), a "supersedes" that does not point
  at an earlier version of the same fact marked SUPERSEDED;
- an affected line not in `known_line_ids` when the caller passes that set.

Evidence status (WORKFLOW_CONTROLS_2026-10-21 section 5) of a looked-up fact:
- absent, PENDING or SUPERSEDED -> HELD (never 0);
- APPROVED + CONFIRMED with a DRAWING or SPECIFICATION source -> DRAWING-CONFIRMED;
- any other APPROVED fact -> ASSUMED — OWNER-APPROVED (its source stays attached);
- never VERIFIED: only the Checker verifies, on the board.

Standard library only; imports nothing from research/ and nothing from the rest of the engine.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping

SCHEMA = "URBAN_PROJECT_CONFIG_V1"
DEFAULT_GUARD_CLASS = "TOOLING"  # T-212: schema + loader of declared inputs; emits no BOQ quantity of its own

QUANTITY_KIND_UNITS: dict[str, dict[str, float | None]] = {
    # unit -> factor to the SI-style base unit of the kind (None: not numeric)
    "LENGTH": {"m": 1.0, "mm": 0.001, "cm": 0.01},
    "AREA": {"m2": 1.0},
    "VOLUME": {"m3": 1.0},
    "MASS": {"kg": 1.0, "t": 1000.0},
    "MASS_PER_AREA": {"kg/m2": 1.0},
    "COUNT": {"nr": 1.0},
    "COUNT_PER_AREA": {"nr/m2": 1.0},
    "RATIO": {"ratio": 1.0, "%": 0.01},
    "CATEGORY": {"none": None},
    "BOOLEAN": {"none": None},
}
BASE_UNIT = {"LENGTH": "m", "AREA": "m2", "VOLUME": "m3", "MASS": "kg", "MASS_PER_AREA": "kg/m2",
             "COUNT": "nr", "COUNT_PER_AREA": "nr/m2", "RATIO": "ratio"}
SOURCE_KINDS = ("DRAWING", "SPECIFICATION", "OWNER_DECISION", "CONSULTANT_RFI", "SITE_RECORD", "SUPPLIER_DATA")
REFUSED_SOURCE_KINDS = ("FREELANCER", "FREELANCER_WORKBOOK", "BENCHMARK", "REFERENCE_BOQ", "ENGINE_RESULT")
APPROVAL_STATUSES = ("APPROVED", "PENDING", "SUPERSEDED")
APPROVERS = ("PROJECT_OWNER", "CONSULTANT", "DESIGNER")
CONFIDENCES = ("CONFIRMED", "PROVISIONAL")

DRAWING_CONFIRMED = "DRAWING-CONFIRMED"
ASSUMED_OWNER_APPROVED = "ASSUMED — OWNER-APPROVED"
HELD = "HELD"

_PROJECT_ID = re.compile(r"^[A-Z0-9][A-Z0-9_-]{1,63}$")
_FACT_ID = re.compile(r"^[A-Z][A-Z0-9_-]*(\.[A-Z0-9_-]+)*$")
_LINE_ID = re.compile(r"^[A-Za-z][A-Za-z0-9_-]*(\.[A-Za-z0-9_-]+)*$")
_SEMVER = re.compile(r"^\d+\.\d+\.\d+$")
_DATE = re.compile(r"^\d{4}-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01])$")
_TOP_KEYS = {"schema", "project_id", "config_version", "facts", "note"}
_FACT_KEYS_REQUIRED = {"fact_id", "version", "quantity_kind", "value", "unit", "source", "approval",
                       "affected_lines", "confidence"}
_FACT_KEYS_OPTIONAL = {"supersedes", "note"}


class ProjectConfigError(ValueError):
    """Raised with every problem found; `problems` is a list of (code, where, message)."""

    def __init__(self, problems: list[tuple[str, str, str]]):
        self.problems = problems
        super().__init__("; ".join(f"{c} at {w}: {m}" for c, w, m in problems))

    @property
    def codes(self) -> list[str]:
        return [c for c, _, _ in self.problems]


@dataclass(frozen=True)
class DeclaredFact:
    fact_id: str
    version: int
    quantity_kind: str
    value: Any
    unit: str
    source_kind: str
    source_reference: str
    approval_status: str
    approved_by: str | None
    approval_date: str
    affected_lines: tuple[str, ...]
    confidence: str
    supersedes: int | None = None
    note: str | None = None

    @property
    def active(self) -> bool:
        return self.approval_status != "SUPERSEDED"

    def base_value(self) -> float:
        """The numeric value in the kind's base unit (mm -> m, % -> ratio, t -> kg)."""
        factor = QUANTITY_KIND_UNITS[self.quantity_kind][self.unit]
        if factor is None:
            raise TypeError(f"{self.fact_id}: a {self.quantity_kind} fact has no numeric value")
        return float(self.value) * factor

    def evidence_status(self) -> str:
        if self.approval_status != "APPROVED":
            return HELD
        if self.confidence == "CONFIRMED" and self.source_kind in ("DRAWING", "SPECIFICATION"):
            return DRAWING_CONFIRMED
        return ASSUMED_OWNER_APPROVED


@dataclass(frozen=True)
class FactLookup:
    """What a caller gets for a fact id: the fact when usable, otherwise HELD with the reason."""

    fact_id: str
    status: str
    fact: DeclaredFact | None
    reason: str

    @property
    def usable(self) -> bool:
        return self.status != HELD and self.fact is not None

    def value(self) -> Any:
        if not self.usable:
            raise LookupError(f"{self.fact_id} is HELD: {self.reason}")
        return self.fact.value

    def base_value(self) -> float:
        if not self.usable:
            raise LookupError(f"{self.fact_id} is HELD: {self.reason}")
        return self.fact.base_value()


@dataclass(frozen=True)
class ProjectConfig:
    project_id: str
    config_version: str
    facts: tuple[DeclaredFact, ...]
    content_sha256: str

    def active_facts(self) -> tuple[DeclaredFact, ...]:
        return tuple(f for f in self.facts if f.active)

    def history(self, fact_id: str) -> tuple[DeclaredFact, ...]:
        return tuple(sorted((f for f in self.facts if f.fact_id == fact_id), key=lambda f: f.version))

    def lookup(self, fact_id: str) -> FactLookup:
        active = [f for f in self.facts if f.fact_id == fact_id and f.active]
        if not active:
            if self.history(fact_id):
                return FactLookup(fact_id, HELD, None, "every declared version is SUPERSEDED")
            return FactLookup(fact_id, HELD, None, "not declared for this project")
        fact = active[0]
        if fact.approval_status == "PENDING":
            return FactLookup(fact_id, HELD, None, f"version {fact.version} is PENDING approval")
        return FactLookup(fact_id, fact.evidence_status(), fact, f"{fact.source_kind}: {fact.source_reference}")

    def facts_affecting(self, line_id: str) -> tuple[DeclaredFact, ...]:
        return tuple(f for f in self.active_facts() if line_id in f.affected_lines)


def _is_number(v: Any) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _check_fact(raw: Any, where: str, known: set[str] | None, out: list) -> DeclaredFact | None:
    if not isinstance(raw, Mapping):
        out.append(("FACT_NOT_OBJECT", where, "a fact is a JSON object"))
        return None
    n0 = len(out)
    keys = set(raw)
    for k in sorted(_FACT_KEYS_REQUIRED - keys):
        if k == "value":
            out.append(("MISSING_VALUE", where, "a fact without a value is not a fact: leave it out and the "
                                               "lines it affects stay HELD"))
        else:
            out.append(("MISSING_FIELD", where, f"'{k}' is required"))
    for k in sorted(keys - _FACT_KEYS_REQUIRED - _FACT_KEYS_OPTIONAL):
        out.append(("UNKNOWN_FIELD", where, f"'{k}' is not a field of {SCHEMA}"))
    if len(out) > n0:
        return None

    fid = raw["fact_id"]
    if not isinstance(fid, str) or not _FACT_ID.match(fid):
        out.append(("BAD_FACT_ID", where, f"{fid!r} is not an upper-case dotted id"))
    ver = raw["version"]
    if not (isinstance(ver, int) and not isinstance(ver, bool) and ver >= 1):
        out.append(("BAD_VERSION", where, f"version {ver!r} must be an integer >= 1"))

    kind, unit, value = raw["quantity_kind"], raw["unit"], raw["value"]
    if kind not in QUANTITY_KIND_UNITS:
        out.append(("BAD_KIND", where, f"quantity_kind {kind!r} is not one of {sorted(QUANTITY_KIND_UNITS)}"))
    else:
        legal = QUANTITY_KIND_UNITS[kind]
        if unit not in legal:
            out.append(("UNIT_KIND_MISMATCH", where, f"unit {unit!r} is not legal for {kind} (legal: {sorted(legal)})"))
        if value is None:
            out.append(("MISSING_VALUE", where, "value is null: leave the fact out and the lines it affects stay HELD"))
        elif kind == "BOOLEAN":
            if not isinstance(value, bool):
                out.append(("BAD_VALUE", where, "a BOOLEAN fact takes true or false"))
        elif kind == "CATEGORY":
            if not (isinstance(value, str) and value.strip()):
                out.append(("BAD_VALUE", where, "a CATEGORY fact takes a non-empty string"))
        elif not _is_number(value):
            out.append(("BAD_VALUE", where, f"a {kind} fact takes a number, not {type(value).__name__}"))
        elif not math.isfinite(value):
            out.append(("BAD_VALUE", where, "the value is not finite"))
        elif value < 0:
            out.append(("NEGATIVE_VALUE", where, f"a {kind} cannot be negative"))
        elif kind in ("COUNT",) and float(value) != int(value):
            out.append(("BAD_VALUE", where, "a COUNT is a whole number"))

    src = raw["source"]
    skind = sref = None
    if not isinstance(src, Mapping) or set(src) != {"kind", "reference"}:
        out.append(("BAD_SOURCE", where, "source is {'kind': ..., 'reference': ...}"))
    else:
        skind, sref = src["kind"], src["reference"]
        if skind in REFUSED_SOURCE_KINDS:
            out.append(("REFUSED_SOURCE", where, f"{skind} is a comparison reference, not a project fact: a value "
                                                 "taken from it is an unexplained patch (A1 class C)"))
        elif skind not in SOURCE_KINDS:
            out.append(("BAD_SOURCE", where, f"source kind {skind!r} is not one of {list(SOURCE_KINDS)}"))
        if not (isinstance(sref, str) and sref.strip()):
            out.append(("MISSING_REFERENCE", where, "a fact names its drawing / document reference"))

    appr = raw["approval"]
    astatus = aby = adate = None
    if not isinstance(appr, Mapping) or not {"status", "date"} <= set(appr) or set(appr) - {"status", "by", "date"}:
        out.append(("BAD_APPROVAL", where, "approval is {'status': ..., 'by': ..., 'date': 'YYYY-MM-DD'}"))
    else:
        astatus, aby, adate = appr["status"], appr.get("by"), appr["date"]
        if astatus not in APPROVAL_STATUSES:
            out.append(("BAD_APPROVAL", where, f"status {astatus!r} is not one of {list(APPROVAL_STATUSES)}"))
        if astatus == "APPROVED" and aby not in APPROVERS:
            out.append(("APPROVER_REQUIRED", where, f"an APPROVED fact names who approved it ({list(APPROVERS)})"))
        if aby is not None and aby not in APPROVERS:
            out.append(("BAD_APPROVAL", where, f"approver {aby!r} is not one of {list(APPROVERS)}"))
        if not (isinstance(adate, str) and _DATE.match(adate)):
            out.append(("BAD_DATE", where, f"date {adate!r} is not YYYY-MM-DD"))

    lines = raw["affected_lines"]
    if not (isinstance(lines, list) and lines):
        out.append(("NO_AFFECTED_LINES", where, "a fact names the BOQ lines it moves"))
        lines = []
    for ln in lines:
        if not (isinstance(ln, str) and _LINE_ID.match(ln)):
            out.append(("BAD_LINE_ID", where, f"{ln!r} is not a BOQ line id"))
        elif known is not None and ln not in known:
            out.append(("UNKNOWN_LINE", where, f"{ln} is not a line of the BOQ it is checked against"))
    if isinstance(lines, list) and len(set(map(str, lines))) != len(lines):
        out.append(("DUPLICATE_LINE", where, "an affected line is listed twice"))

    conf = raw["confidence"]
    if conf not in CONFIDENCES:
        out.append(("BAD_CONFIDENCE", where, f"confidence {conf!r} is not CONFIRMED or PROVISIONAL"))
    elif conf == "CONFIRMED" and astatus != "APPROVED" and astatus != "SUPERSEDED":
        out.append(("CONFIRMED_NOT_APPROVED", where, "CONFIRMED needs an APPROVED approval; a pending value is "
                                                     "PROVISIONAL"))

    sup = raw.get("supersedes")
    if sup is not None and not (isinstance(sup, int) and not isinstance(sup, bool) and isinstance(ver, int)
                                and 1 <= sup < ver):
        out.append(("BAD_SUPERSEDES", where, "supersedes names an EARLIER version of the same fact"))
    note = raw.get("note")
    if note is not None and not isinstance(note, str):
        out.append(("BAD_NOTE", where, "note is text"))

    if len(out) > n0:
        return None
    return DeclaredFact(fact_id=fid, version=ver, quantity_kind=kind, value=value, unit=unit, source_kind=skind,
                        source_reference=sref.strip(), approval_status=astatus, approved_by=aby, approval_date=adate,
                        affected_lines=tuple(lines), confidence=conf, supersedes=sup, note=note)


def canonical_sha256(data: Mapping) -> str:
    """Hash of the canonical JSON (sorted keys, no whitespace): key order and layout never change it."""
    text = json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def parse_project_config(data: Any, known_line_ids: Iterable[str] | None = None) -> ProjectConfig:
    """Validate a decoded config and return it; raise ProjectConfigError listing every problem."""
    out: list[tuple[str, str, str]] = []
    known = set(known_line_ids) if known_line_ids is not None else None
    if not isinstance(data, Mapping):
        raise ProjectConfigError([("NOT_OBJECT", "$", "a project config is a JSON object")])
    for k in sorted(_TOP_KEYS - {"note"} - set(data)):
        out.append(("MISSING_FIELD", "$", f"'{k}' is required"))
    for k in sorted(set(data) - _TOP_KEYS):
        out.append(("UNKNOWN_FIELD", "$", f"'{k}' is not a field of {SCHEMA}"))
    if data.get("schema", SCHEMA) != SCHEMA:
        out.append(("WRONG_SCHEMA", "$.schema", f"{data.get('schema')!r} is not {SCHEMA}"))
    pid = data.get("project_id")
    if "project_id" in data and not (isinstance(pid, str) and _PROJECT_ID.match(pid)):
        out.append(("BAD_PROJECT_ID", "$.project_id", f"{pid!r} is not an id of A-Z 0-9 _ -"))
    cver = data.get("config_version")
    if "config_version" in data and not (isinstance(cver, str) and _SEMVER.match(cver)):
        out.append(("BAD_CONFIG_VERSION", "$.config_version", f"{cver!r} is not semver"))
    raw_facts = data.get("facts", [])
    if not isinstance(raw_facts, list):
        out.append(("BAD_FACTS", "$.facts", "facts is a list"))
        raw_facts = []

    facts: list[DeclaredFact] = []
    for i, raw in enumerate(raw_facts):
        f = _check_fact(raw, f"$.facts[{i}]", known, out)
        if f is not None:
            facts.append(f)

    seen: dict[tuple[str, int], int] = {}
    for f in facts:
        key = (f.fact_id, f.version)
        if key in seen:
            out.append(("DUPLICATE_FACT", f.fact_id, f"version {f.version} is declared twice"))
        seen[key] = 1
    by_id: dict[str, list[DeclaredFact]] = {}
    for f in facts:
        by_id.setdefault(f.fact_id, []).append(f)
    for fid, group in sorted(by_id.items()):
        active = [f for f in group if f.active]
        if len(active) > 1:
            out.append(("TWO_ACTIVE_VERSIONS", fid, f"versions {sorted(f.version for f in active)} are both active: "
                                                    "mark the older one SUPERSEDED"))
        versions = {f.version: f for f in group}
        for f in group:
            if f.supersedes is not None:
                old = versions.get(f.supersedes)
                if old is None:
                    out.append(("BAD_SUPERSEDES", fid, f"version {f.version} supersedes version {f.supersedes}, "
                                                       "which is not declared"))
                elif old.active:
                    out.append(("BAD_SUPERSEDES", fid, f"version {f.supersedes} is superseded but not marked "
                                                       "SUPERSEDED"))
            if f.active and len(group) > 1 and f.version != max(versions):
                out.append(("STALE_ACTIVE_VERSION", fid, f"active version {f.version} is older than declared "
                                                         f"version {max(versions)}"))
        if len({f.quantity_kind for f in group}) > 1:
            out.append(("KIND_CHANGED", fid, "every version of one fact has the same quantity_kind"))
    if out:
        raise ProjectConfigError(out)
    try:
        digest = canonical_sha256(data)
    except ValueError as exc:  # NaN / infinity cannot be canonical JSON
        raise ProjectConfigError([("BAD_VALUE", "$", str(exc))]) from None
    return ProjectConfig(project_id=pid, config_version=cver, facts=tuple(facts), content_sha256=digest)


def load_project_config(path: str | Path, known_line_ids: Iterable[str] | None = None) -> ProjectConfig:
    """Read a UTF-8 JSON config file and validate it (see parse_project_config)."""
    p = Path(path)
    try:
        text = p.read_text(encoding="utf-8")
    except FileNotFoundError:
        raise ProjectConfigError([("NO_FILE", str(p), "no project config at this path: every line that needs a "
                                                      "declared fact stays HELD")]) from None

    def _no_dupes(pairs):
        keys = [k for k, _ in pairs]
        if len(set(keys)) != len(keys):
            raise ProjectConfigError([("DUPLICATE_KEY", str(p), f"a JSON object repeats a key: {sorted(keys)}")])
        return dict(pairs)

    def _no_constant(name):
        raise ProjectConfigError([("BAD_VALUE", str(p), f"{name} is not a number")])

    try:
        data = json.loads(text, object_pairs_hook=_no_dupes, parse_constant=_no_constant)
    except json.JSONDecodeError as exc:
        raise ProjectConfigError([("NOT_JSON", str(p), str(exc))]) from None
    return parse_project_config(data, known_line_ids)
