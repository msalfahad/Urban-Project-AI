"""Benchmark anchoring protection: the number must not reach the eye.

A benchmark is the only independent check a project has of whether this
engine measures a real building. It stops being one the moment it
influences the interpretation it is meant to test — and influence does
not need intent. An interpreter who knows the expected area will find the
reading that produces it, and will experience that as having seen it.

So the work is split in two, and the split is enforced here rather than
remembered:

    BLIND INTERPRETATION   the geometry is read with NO human quantity,
                           no reconstructed quantity, no expected area,
                           no target dimension, and no previous numeric
                           correction whose value would reveal the
                           target. Then the candidate is FROZEN
    RECONCILIATION         only after the freeze may a benchmark be
                           opened, and only to explain a difference —
                           never to choose between readings

A NUMERICAL COINCIDENCE IS NOT GEOMETRIC EVIDENCE. Where two readings of
a curved boundary give different areas and one lands on the benchmark,
that landing is a FACT ABOUT ARITHMETIC and no part of the case for that
reading. What establishes a curve, an arc, a segment, a fraction or a
boundary is the drawing, a CAD entity, an authored dimension, the spatial
topology, the specification, independent visual evidence, or a human
saying so.

Hypotheses may be raised after a benchmark is revealed. They stay
UNCONFIRMED until independent geometric evidence supports them, and they
are never ordered by how close they come.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field

MODEL = "A_BENCHMARK_MAY_NOT_ANCHOR_AN_INTERPRETATION_V1"

# --- the two phases ------------------------------------------------------
BLIND = "BLIND_GEOMETRY_INTERPRETATION"
FROZEN = "CANDIDATE_GEOMETRY_FROZEN"
RECONCILIATION = "BENCHMARK_RECONCILIATION"
PHASES = (BLIND, FROZEN, RECONCILIATION)

# --- what a blind pass may never be handed -------------------------------
HUMAN_QUANTITY = "A_HUMAN_EXCEL_QUANTITY"
RECONSTRUCTED_QUANTITY = "A_MANUALLY_RECONSTRUCTED_QUANTITY"
EXPECTED_AREA = "AN_EXPECTED_BENCHMARK_AREA"
TARGET_DIMENSION = "A_DIMENSION_DERIVED_FROM_A_BENCHMARK"
REVEALING_CORRECTION = "A_PREVIOUS_ERROR_WHOSE_CORRECTION_REVEALS_THE_TARGET"
WITHHELD = (HUMAN_QUANTITY, RECONSTRUCTED_QUANTITY, EXPECTED_AREA,
            TARGET_DIMENSION, REVEALING_CORRECTION)

# Field names that carry one of those, whatever they are called locally.
# A key is checked by SHAPE, so that renaming it does not smuggle it in.
BENCHMARK_KEYS = re.compile(
    r"(benchmark|expected|target|human_?(excel|total|quantity|area)"
    r"|excel|qiyal|known_?total|takeoff_?total|take_?off_?total"
    r"|reference_?(area|total)|should_?be|correct_?(area|value))",
    re.I)

# --- what MAY establish a reading ---------------------------------------
EV_DRAWING_GEOMETRY = "DRAWING_GEOMETRY"
EV_CAD_ENTITY = "CAD_ENTITY"
EV_AUTHORED_DIMENSION = "AUTHORED_DIMENSION"
EV_SPATIAL_TOPOLOGY = "SPATIAL_TOPOLOGY"
EV_SPECIFICATION = "SPECIFICATION"
EV_INDEPENDENT_VISUAL = "INDEPENDENT_VISUAL_EVIDENCE"
EV_HUMAN_CLARIFICATION = "HUMAN_CLARIFICATION"
INDEPENDENT_EVIDENCE = (EV_DRAWING_GEOMETRY, EV_CAD_ENTITY,
                        EV_AUTHORED_DIMENSION, EV_SPATIAL_TOPOLOGY,
                        EV_SPECIFICATION, EV_INDEPENDENT_VISUAL,
                        EV_HUMAN_CLARIFICATION)

# --- and what may NEVER ---------------------------------------------------
EV_BENCHMARK_CLOSENESS = "CLOSENESS_TO_THE_BENCHMARK"
NOT_EVIDENCE = (EV_BENCHMARK_CLOSENESS,
                "IT_MAKES_THE_TOTAL_COME_OUT_RIGHT",
                "IT_ROUNDS_TO_THE_EXPECTED_FIGURE")

UNCONFIRMED = "UNCONFIRMED"
CONFIRMED = "CONFIRMED_ON_INDEPENDENT_GEOMETRIC_EVIDENCE"
UNRANKED = "UNRANKED_NO_EVIDENCE_SEPARATES_THESE"

A_COINCIDENCE_IS_NOT_EVIDENCE = (
    "a numerical coincidence with a benchmark is a fact about "
    "arithmetic. It is recorded, and it is no part of the case for any "
    "reading")


class BenchmarkLeak(RuntimeError):
    """Something tried to hand a blind pass the answer."""


def model_hash() -> str:
    parts = ([MODEL] + list(PHASES) + list(WITHHELD)
             + list(INDEPENDENT_EVIDENCE) + list(NOT_EVIDENCE)
             + [UNCONFIRMED, CONFIRMED, UNRANKED])
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:24]


def frozen_parameters() -> dict:
    return {
        "MODEL": MODEL,
        "PHASES": list(PHASES),
        "WITHHELD_FROM_A_BLIND_PASS": list(WITHHELD),
        "INDEPENDENT_EVIDENCE": list(INDEPENDENT_EVIDENCE),
        "NEVER_EVIDENCE": list(NOT_EVIDENCE),
        "why": {
            "influence_needs_no_intent": (
                "an interpreter who knows the expected area finds the "
                "reading that produces it, and experiences that as "
                "having seen it"),
            "a_check_that_is_read_is_spent": (
                "a benchmark tests whether the engine measures a real "
                "building. Once it has steered an interpretation it "
                "tests nothing"),
            "closeness_is_not_a_rank": (
                "hypotheses are ordered by the evidence behind them. "
                "Where no evidence separates them they stay unranked, "
                "however neatly one of them lands"),
        },
    }


# ------------------------------------------------------- the blind pass

def scan(payload) -> list:
    """Every place in a payload that carries, or names, a benchmark."""
    found = []

    def walk(node, path):
        if isinstance(node, dict):
            for k, v in node.items():
                here = f"{path}.{k}" if path else str(k)
                if BENCHMARK_KEYS.search(str(k)):
                    found.append({"at": here, "key": str(k),
                                  "withheld": EXPECTED_AREA})
                walk(v, here)
        elif isinstance(node, (list, tuple)):
            for i, v in enumerate(node):
                walk(v, f"{path}[{i}]")
        elif isinstance(node, str) and BENCHMARK_KEYS.search(node):
            found.append({"at": path, "key": node[:60],
                          "withheld": HUMAN_QUANTITY})

    walk(payload, "")
    return found


def withhold(payload, *, phase: str = BLIND) -> dict:
    """What a blind pass is allowed to see, with the rest taken out.

    Refuses rather than redacts when the caller is not in a blind phase
    by mistake: a reconciliation pass is allowed the benchmark and says
    so, and a blind pass never receives it under any name.
    """
    if phase != BLIND:
        return {"phase": phase, "payload": payload, "withheld": []}
    leaks = scan(payload)

    def strip(node):
        if isinstance(node, dict):
            return {k: strip(v) for k, v in node.items()
                    if not BENCHMARK_KEYS.search(str(k))}
        if isinstance(node, list):
            return [strip(v) for v in node]
        if isinstance(node, tuple):
            return tuple(strip(v) for v in node)
        return node

    return {"phase": BLIND, "payload": strip(payload),
            "withheld": leaks,
            "why": ("a blind interpretation receives the drawing and "
                    "nothing that could tell it the answer")}


def assert_blind(payload) -> None:
    """Raise if a benchmark reached a pass that must not have one."""
    leaks = scan(payload)
    if leaks:
        raise BenchmarkLeak(
            "a blind geometry pass was handed "
            + ", ".join(sorted({x["at"] or x["key"] for x in leaks})[:6])
            + ". " + A_COINCIDENCE_IS_NOT_EVIDENCE)


# ------------------------------------------------------------- the freeze

def freeze(candidate) -> dict:
    """The candidate geometry, hashed, before any benchmark is opened."""
    text = json.dumps(candidate, sort_keys=True, ensure_ascii=False,
                      default=str)
    return {
        "phase": FROZEN,
        "CANDIDATE_GEOMETRY_HASH": hashlib.sha256(
            text.encode("utf-8")).hexdigest()[:24],
        "frozen_fields": sorted(candidate) if isinstance(candidate, dict)
        else [],
        "why": ("reconciliation may begin only against a candidate that "
                "can no longer move"),
    }


def may_reconcile(frozen_block) -> bool:
    return bool(frozen_block and frozen_block.get(
        "CANDIDATE_GEOMETRY_HASH"))


# --------------------------------------------------------- the hypotheses

@dataclass
class Hypothesis:
    """A possible reading of the geometry, and what stands behind it."""

    hypothesis_id: str = ""
    name: str = ""
    claim: str = ""
    evidence: tuple = ()             # from INDEPENDENT_EVIDENCE only
    evidence_detail: tuple = ()
    what_would_settle_it: str = ""
    # Recorded, never ranked on. A hypothesis does not become likelier
    # because its arithmetic lands on the expected figure.
    numeric_effect: dict = field(default_factory=dict)
    status: str = UNCONFIRMED

    def independent(self) -> tuple:
        return tuple(e for e in self.evidence if e in INDEPENDENT_EVIDENCE)

    def record(self) -> dict:
        bad = [e for e in self.evidence if e in NOT_EVIDENCE]
        return {
            "id": self.hypothesis_id,
            "name": self.name,
            "claim": self.claim,
            "independent_evidence": list(self.independent()),
            "evidence_detail": list(self.evidence_detail),
            "rejected_as_evidence": bad,
            "numeric_effect": dict(self.numeric_effect),
            "numeric_effect_is_not_evidence": A_COINCIDENCE_IS_NOT_EVIDENCE,
            "what_would_settle_it": self.what_would_settle_it,
            "status": self.status,
        }


def confirm(h: Hypothesis, *, evidence, detail: str = "") -> Hypothesis:
    """Confirm a hypothesis, and only on evidence that may confirm one."""
    if evidence in NOT_EVIDENCE or evidence not in INDEPENDENT_EVIDENCE:
        raise BenchmarkLeak(
            f"{evidence} may not confirm a reading. "
            + A_COINCIDENCE_IS_NOT_EVIDENCE)
    h.evidence = tuple(dict.fromkeys(h.evidence + (evidence,)))
    if detail:
        h.evidence_detail = h.evidence_detail + (detail,)
    h.status = CONFIRMED
    return h


def rank(hypotheses) -> dict:
    """Order by EVIDENCE. Where none separates them, leave them unranked.

    Nothing here reads `numeric_effect`. That is the whole point: the
    ordering cannot depend on a number the hypotheses were never
    supposed to be measured against.
    """
    rows = list(hypotheses)
    counts = {h.hypothesis_id: len(h.independent()) for h in rows}
    spread = len({v for v in counts.values()})
    ordered = sorted(rows, key=lambda h: (-len(h.independent()),
                                          h.hypothesis_id))
    unranked = spread <= 1
    return {
        "model": MODEL,
        "ranked_by": "INDEPENDENT_GEOMETRIC_EVIDENCE",
        "never_ranked_by": list(NOT_EVIDENCE),
        "status": (UNRANKED if unranked else "RANKED_ON_EVIDENCE"),
        "hypotheses": [h.record() for h in ordered],
        "why": ("no independent evidence separates these, so none of "
                "them leads" if unranked else
                "ordered by how much independent geometric evidence "
                "stands behind each"),
    }
