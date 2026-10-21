"""WALL-HEIGHT AUTHORITY (R8.18) - the usable wall-finish height of ONE measurement scope (project, revision, floor /
zone, trade) as an EVIDENCE OBJECT, never a company constant.

Ranked candidates (lower rank wins; a blocked candidate never wins):
  1 SOURCE_FINISH_HEIGHT        an explicit source wall / finish height
  2 SECTION_CLEAR_HEIGHT        a section / elevation clear height
  3 DERIVED_CLEAR_HEIGHT        gross vertical height MINUS every required deduction, each component with its own
                                source authority; one unknown required component -> this candidate is BLOCKED
  4 OWNER_PROJECT_FACT          a source-bound owner / project fact for this scope
  5 PERMITTED_PROJECT_DEFAULT   a default the project's own rules permit for this scope
  otherwise BLOCKED
A floor-to-floor (or level) height alone is NEVER a wall height. An owner rationale (example arithmetic) is stored as
rationale only: it is not a formula and its components are not source facts.

Project-agnostic; stdlib only.
"""

from __future__ import annotations

import hashlib
import json
import math

POLICY_ID = "WALL_HEIGHT_AUTHORITY_POLICY_V1"
RANKS = {"SOURCE_FINISH_HEIGHT": 1, "SECTION_CLEAR_HEIGHT": 2, "DERIVED_CLEAR_HEIGHT": 3, "OWNER_PROJECT_FACT": 4,
         "PERMITTED_PROJECT_DEFAULT": 5}
NOT_A_WALL_HEIGHT = ("FLOOR_TO_FLOOR", "LEVEL", "SLAB_TO_SLAB")
DERIVATION_COMPONENTS = ("beam_or_soffit_zone", "ceiling_service_decor_zone", "floor_buildup", "other")
ESTABLISHED, BLOCKED = "ESTABLISHED", "BLOCKED"


def derive(gross_m, gross_authority, components: dict) -> dict:
    """A derived clear height: gross vertical height minus every REQUIRED deduction. components:
    {name: {"value_m", "authority", "required": bool}}; any required component without value or authority -> BLOCKED."""
    missing = [k for k, c in components.items() if c.get("required", True) and
               (c.get("value_m") is None or not c.get("authority"))]
    if gross_m is None or not gross_authority:
        missing.insert(0, "gross_vertical_height")
    rec = {"kind": "DERIVED_CLEAR_HEIGHT", "gross_m": gross_m, "gross_authority": gross_authority,
           "components": components, "formula": "gross - " + " - ".join(components) if components else "gross"}
    if missing:
        return dict(rec, state=BLOCKED, value_m=None, missing=missing)
    v = gross_m - math.fsum(c["value_m"] for c in components.values() if c.get("value_m") is not None)
    return dict(rec, state=ESTABLISHED, value_m=round(v, 6), missing=[])


def candidate(kind, value_m, authority, **extra) -> dict:
    if kind in NOT_A_WALL_HEIGHT:
        return dict(kind=kind, value_m=value_m, authority=authority, state=BLOCKED,
                    why="a floor-to-floor / level height alone is never a wall height", **extra)
    ok = kind in RANKS and value_m is not None and value_m > 0 and bool(authority)
    return dict(kind=kind, rank=RANKS.get(kind), value_m=value_m, authority=authority,
                state=ESTABLISHED if ok else BLOCKED, **extra)


def resolve(scope: dict, candidates: list) -> dict:
    """The governing height of ONE scope: the best-ranked ESTABLISHED candidate; every candidate is kept."""
    ok = sorted((c for c in candidates if c.get("state") == ESTABLISHED and c.get("rank")), key=lambda c: c["rank"])
    out = {"scope": scope, "candidates": candidates, "policy": POLICY_ID}
    if not ok:
        return dict(out, state=BLOCKED, value_m=None, authority=None, governing=None)
    g = ok[0]
    return dict(out, state=ESTABLISHED, value_m=g["value_m"], authority=g["authority"], governing=g["kind"])


def conflict(finish_heights: dict, available) -> list:
    """Finish heights above a PROVEN available height are a physical conflict; above an unproven one only a
    POTENTIAL conflict. Nothing is clipped."""
    out = []
    for trade, h in finish_heights.items():
        if available.get("value_m") is not None and h is not None and h > available["value_m"] + 1e-9:
            out.append({"trade": trade, "finish_height_m": h, "available_m": available["value_m"],
                        "state": "PHYSICAL_CONFLICT" if available.get("proven") else
                        "POTENTIAL_PHYSICAL_CONFLICT_NOT_PROVEN", "basis": available.get("basis"),
                        "action": "flag only - never clipped"})
    return out


def policy_record() -> dict:
    rec = {"policy_id": POLICY_ID, "ranks": RANKS, "not_a_wall_height": list(NOT_A_WALL_HEIGHT),
           "derivation_components": list(DERIVATION_COMPONENTS),
           "derivation": "gross vertical height - each required deduction, each with its own source authority; one "
                         "unknown required component -> BLOCKED at rank 3 (never filled by a default)",
           "scope": "project + revision + floor / zone + trade (+ space classes)",
           "never": ["a company-wide wall height constant", "floor-to-floor alone as a wall height",
                     "an owner rationale as a formula", "one trade's height clipped to another's",
                     "a height transferred to another floor, revision or project"]}
    rec["digest"] = hashlib.sha256(json.dumps(rec, sort_keys=True).encode()).hexdigest()
    return rec
