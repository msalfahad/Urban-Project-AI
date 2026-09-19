"""E1's own input contract. E1 is not a blind pass, and must not pretend.

The blind contract of §99 refuses a previous pass's answer by path, which
is right for a pass being tested on whether it can SEE. E1 is the
opposite: it is told to use the frozen A18 records to know WHAT to look
for, while CAD establishes WHERE. Running E1 through the blind contract
would refuse the very records it is required to read, so E1 has its own
admitted set - and the same sealed-sandbox machinery, so a refused input
still cannot physically reach the run.

What E1 may have:

    CAD_GEOMETRY_SOURCE        the authoritative DWG/DXF-derived geometry
    CAD_SOURCE_METADATA        what is needed to interpret that CAD
    FROZEN_A18_PASS_B          semantic hypotheses: what to look for
    FROZEN_A18_PASS_C2         the valid local challenge records
    FROZEN_A18_PASS_D          the uniform challenge records
    GENERAL_GEOMETRY_RULE      approved GENERAL Urban geometry rules

What it may not, whatever it is called or where it sits:

    a human Excel quantity, a manual take-off, a benchmark file, a
    reconciliation, a corrected target area, an expected quantity, a
    previous numeric answer, a benchmark-informed hypothesis, or the
    external review's grading of the blind experiment
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from pathlib import Path

from engine import benchmark_protection as bp
from engine import blind_input_contract as bic
from engine import export_provenance as prov

MODEL = "E1_USES_THE_FROZEN_READING_AND_THE_CAD_AND_NOTHING_ELSE_V1"

# --- what E1 may receive -------------------------------------------------
CAD_GEOMETRY_SOURCE = "AUTHORITATIVE_CAD_DERIVED_GEOMETRY"
CAD_SOURCE_METADATA = "METADATA_REQUIRED_TO_INTERPRET_THAT_CAD"
FROZEN_PASS_B = "FROZEN_A18_PASS_B_SEMANTIC_HYPOTHESES"
FROZEN_PASS_C2 = "FROZEN_A18_PASS_C2_CHALLENGE_RECORDS"
FROZEN_PASS_D = "FROZEN_A18_PASS_D_CHALLENGE_RECORDS"
GENERAL_GEOMETRY_RULE = "APPROVED_GENERAL_URBAN_GEOMETRY_RULE"
ALLOWED_KINDS = (CAD_GEOMETRY_SOURCE, CAD_SOURCE_METADATA, FROZEN_PASS_B,
                 FROZEN_PASS_C2, FROZEN_PASS_D, GENERAL_GEOMETRY_RULE)

# --- and what it may not -------------------------------------------------
HUMAN_QUANTITY = "A_HUMAN_EXCEL_QUANTITY"
MANUAL_TAKEOFF = "A_MANUAL_TAKE_OFF"
BENCHMARK_FILE = "A_BENCHMARK_FILE"
RECONCILIATION = "A_RECONCILIATION_FILE"
CORRECTED_AREA = "A_CORRECTED_TARGET_AREA"
EXPECTED_QUANTITY = "AN_EXPECTED_QUANTITY"
PREVIOUS_NUMERIC_ANSWER = "A_PREVIOUS_NUMERIC_ANSWER"
BENCHMARK_HYPOTHESIS = "A_BENCHMARK_INFORMED_HYPOTHESIS"
REVIEW_GRADING = "THE_EXTERNAL_REVIEWS_GRADING_OF_THE_BLIND_EXPERIMENT"
PROHIBITED_KINDS = (HUMAN_QUANTITY, MANUAL_TAKEOFF, BENCHMARK_FILE,
                    RECONCILIATION, CORRECTED_AREA, EXPECTED_QUANTITY,
                    PREVIOUS_NUMERIC_ANSWER, BENCHMARK_HYPOTHESIS,
                    REVIEW_GRADING)

# Paths, by shape. A previous ROUND's measured export is a previous
# numeric answer; the frozen A18 records are not, and are named exactly so
# that the two cannot be confused.
PROHIBITED_PATHS = (
    (re.compile(r"reconcil", re.I), RECONCILIATION),
    (re.compile(r"benchmark|qiyal|known_?total|take_?off_?total", re.I),
     BENCHMARK_FILE),
    (re.compile(r"\.xlsx?$|workbook|excel", re.I), HUMAN_QUANTITY),
    (re.compile(r"(^|[/_-])sealed([/_-]|$)", re.I), BENCHMARK_FILE),
    (re.compile(r"corrected|correction", re.I), CORRECTED_AREA),
    (re.compile(r"external_?review", re.I), REVIEW_GRADING),
    (re.compile(r"round\d[a-z]?_export|ROUND\d", re.I),
     PREVIOUS_NUMERIC_ANSWER),
    (re.compile(r"hypothes", re.I), BENCHMARK_HYPOTHESIS),
    (re.compile(r"manual|takeoff|take_?off", re.I), MANUAL_TAKEOFF),
)

ADMITTED = "ADMITTED"
REFUSED = "REFUSED_AT_THE_DOOR"

WHY_E1_IS_NOT_BLIND = (
    "E1 is told to use the frozen reading to know WHAT to look for while "
    "CAD establishes WHERE. That is not a blind pass and this contract "
    "does not pretend it is: the frozen A18 records are admitted by name, "
    "and every measured quantity from any earlier round is refused")


class E1InputRefused(RuntimeError):
    """An input E1 may not have."""


def check_path(path) -> tuple:
    s = str(path).replace("\\", "/").lower()
    for pattern, kind in PROHIBITED_PATHS:
        hit = pattern.search(s)
        if hit:
            return kind, hit.group(0)
    return "", ""


@dataclass
class Decision:
    input_id: str = ""
    kind: str = ""
    status: str = ADMITTED
    refused_by: str = ""
    would_be: str = ""
    why: str = ""
    identity: dict = field(default_factory=dict)

    @property
    def admitted(self) -> bool:
        return self.status == ADMITTED

    def record(self) -> dict:
        out = {"status": self.status}
        out.update(self.identity)
        if not self.admitted:
            out["refused_by"] = self.refused_by
            out["it_would_have_been"] = self.would_be
        out["why"] = self.why
        return out


@dataclass
class E1Run:
    """The same interface the sealed sandbox expects, E1's rules inside."""

    run_id: str = ""
    pass_id: str = "E1"
    subject: str = ""
    floor: str = ""
    phase: str = "E1_CAD_PHYSICAL_GEOMETRY_ALIGNMENT"
    status: str = "E1_RUN_VALID"
    stopped: bool = False
    decisions: list = field(default_factory=list)
    notes: dict = field(default_factory=dict)

    def offer(self, item) -> Decision:
        ident = item.identity() if hasattr(item, "identity") else {}
        common = dict(input_id=getattr(item, "input_id", ""),
                      kind=getattr(item, "kind", ""), identity=ident)
        kind = common["kind"]
        if kind in PROHIBITED_KINDS:
            return Decision(status=REFUSED, refused_by="KIND_GATE",
                            would_be=kind,
                            why=f"{kind} is named as something E1 never "
                                "receives", **common)
        if kind not in ALLOWED_KINDS:
            return Decision(status=REFUSED, refused_by="KIND_GATE",
                            would_be="AN_UNDECLARED_KIND",
                            why=f"{kind!r} is not one of E1's admitted "
                                "kinds. A missing rule is not a permissive "
                                "rule", **common)
        path = getattr(item, "path", "")
        if path:
            bad, hit = check_path(path)
            if bad:
                return Decision(status=REFUSED, refused_by="PATH_GATE",
                                would_be=bad,
                                why=f"{path} matches {hit!r}, which is "
                                    f"where {bad} lives", **common)
        payload = getattr(item, "content", None)
        if payload is None and path and Path(path).suffix.lower() in (
                ".json", ".md", ".txt", ".csv"):
            try:
                payload = Path(path).read_text(encoding="utf-8",
                                               errors="replace")
            except OSError:
                payload = None
        if payload is not None and kind == GENERAL_GEOMETRY_RULE:
            leaks = bp.scan(payload)
            if leaks:
                where = ", ".join(sorted({x.get("matched") or x["key"][:40]
                                          for x in leaks})[:4])
                return Decision(status=REFUSED, refused_by="CONTENT_GATE",
                                would_be=EXPECTED_QUANTITY,
                                why=f"a rule carrying {where}", **common)
        return Decision(status=ADMITTED,
                        why=f"{common['input_id']} is {kind}", **common)

    @property
    def admitted(self) -> list:
        return [d for d in self.decisions if d.admitted]

    @property
    def refused(self) -> list:
        return [d for d in self.decisions if not d.admitted]

    def manifest(self) -> dict:
        body = {
            "MODEL": MODEL,
            "phase": self.phase,
            "run_id": self.run_id,
            "pass_id": self.pass_id,
            "subject": self.subject,
            "floor": self.floor,
            "status": self.status,
            "why_E1_is_not_blind": WHY_E1_IS_NOT_BLIND,
            "ALLOWED_KINDS": list(ALLOWED_KINDS),
            "PROHIBITED_KINDS": list(PROHIBITED_KINDS),
            "counts": {"offered": len(self.decisions),
                       "admitted": len(self.admitted),
                       "refused_at_the_door": len(self.refused)},
            "inputs_made_available": [d.record() for d in self.admitted],
            "refused_at_the_door": [d.record() for d in self.refused],
            "notes": dict(self.notes),
        }
        body["INPUT_MANIFEST_HASH"] = prov.canonical_sha256(body)
        return body

    def assert_running(self) -> None:
        if self.stopped:
            raise E1InputRefused("this E1 run was stopped")


# The sandbox places files through an Input object; E1 reuses the blind
# contract's Input dataclass unchanged, because it is only a description
# of a file and carries no policy of its own.
Input = bic.Input


def model_hash() -> str:
    parts = ([MODEL] + list(ALLOWED_KINDS) + list(PROHIBITED_KINDS))
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:24]


def frozen_parameters() -> dict:
    return {"MODEL": MODEL, "ALLOWED_KINDS": list(ALLOWED_KINDS),
            "PROHIBITED_KINDS": list(PROHIBITED_KINDS),
            "why_E1_is_not_blind": WHY_E1_IS_NOT_BLIND}
