"""SPECIAL STRUCTURAL POPULATION REGISTER (generic).

Every project is checked against the SAME population list. Each population ends as
    PRESENT / NOT_PRESENT / BLOCKED / UNKNOWN
- never silently absent. NOT_PRESENT needs positive evidence of absence (a searched source that would show it);
no evidence at all is UNKNOWN.

Parapet stiffeners / top ring beams: a spacing or section is taken from (1) the drawing / detail, (2) a consultant /
project rule; if neither exists an Urban STANDARD CANDIDATE (owner practice, supplied as data) may drive a PROVISIONAL
scenario only, flagged PARAPET_STIFFENER_SPACING_REQUIRED - it is never a verified quantity.
Stdlib only.
"""

from __future__ import annotations

import math

PRESENT, NOT_PRESENT, BLOCKED, UNKNOWN = "PRESENT", "NOT_PRESENT", "BLOCKED", "UNKNOWN"
STATES = (PRESENT, NOT_PRESENT, BLOCKED, UNKNOWN)

POPULATIONS = (
    ("FOUNDATIONS", ("RAFT", "ISOLATED_FOOTING", "COMBINED_FOOTING", "STRIP_FOOTING", "PILE_CAP", "NECK_PEDESTAL")),
    ("GROUND", ("STRAP_BEAM", "GROUND_BEAM", "GROUND_SLAB")),
    ("VERTICAL", ("COLUMN", "STRUCTURAL_WALL", "PLANTED_COLUMN", "TURNED_COLUMN")),
    ("BEAMS", ("SIMPLE_BEAM", "CONTINUOUS_BEAM", "RING_BEAM", "LINTEL", "BEAM_OPENING")),
    ("SLABS", ("SOLID_SLAB", "FLAT_SLAB", "RIBBED_HORDI_SLAB", "CANTILEVER")),
    ("STAIRS", ("STAIR", "LANDING")),
    ("LIFT", ("LIFT_PIT", "LIFT_WALL", "LIFT_TIE_BEAM")),
    ("SPECIAL", ("POOL", "WATER_TANK", "DOME")),
    ("BOUNDARY", ("BOUNDARY_WALL", "BOUNDARY_RC_COLUMN", "BOUNDARY_GROUND_BEAM")),
    ("ROOF", ("PARAPET", "PARAPET_RC_STIFFENER_COLUMN", "PARAPET_TOP_RING_BEAM")),
    ("OTHER", ("EQUIPMENT_BASE", "PLANTER_STRUCTURAL_ELEMENT", "OTHER_SPECIAL_RC_DETAIL")),
)
ALL_POPULATIONS = tuple(p for _, ps in POPULATIONS for p in ps)


def discover(evidence):
    """evidence: {population: {state, refs[], why}} from the project adapter. Every population in ALL_POPULATIONS
    appears in the output; a population without evidence is UNKNOWN; NOT_PRESENT without refs is downgraded to
    UNKNOWN (absence must be shown, not assumed). Unknown keys are rejected."""
    extra = set(evidence) - set(ALL_POPULATIONS)
    if extra:
        raise ValueError(f"unknown populations: {sorted(extra)}")
    rows = []
    for group, pops in POPULATIONS:
        for p in pops:
            e = evidence.get(p) or {}
            st = e.get("state", UNKNOWN)
            if st not in STATES:
                raise ValueError(f"{p}: state {st}")
            why = e.get("why")
            if st == NOT_PRESENT and not e.get("refs"):
                st, why = UNKNOWN, "NOT_PRESENT claimed without a searched source - downgraded to UNKNOWN"
            rows.append({"group": group, "population": p, "state": st, "refs": list(e.get("refs", [])),
                         "why": why, "quantity_state": e.get("quantity_state"), "flags": list(e.get("flags", []))})
    return {"register": "SPECIAL_STRUCTURAL_POPULATION_REGISTER", "rows": rows,
            "counts": {s: sum(1 for r in rows if r["state"] == s) for s in STATES},
            "complete_list": len(rows) == len(ALL_POPULATIONS)}


def parapet_stiffener_scenario(parapet_length_m, *, drawing_spacing_m=None, project_rule_spacing_m=None,
                               urban_candidate=None):
    """Stiffener columns along a parapet run. Authority ladder: drawing -> project / consultant rule -> Urban standard
    candidate (provisional scenario only). Returns the count and its authority; never VERIFIED from the candidate."""
    if drawing_spacing_m:
        sp, auth, state = drawing_spacing_m, "SOURCE_FACT", "VERIFIED"
    elif project_rule_spacing_m:
        sp, auth, state = project_rule_spacing_m, "PROJECT_RULE", "VERIFIED"
    elif urban_candidate and urban_candidate.get("max_spacing_m"):
        sp, auth, state = urban_candidate["max_spacing_m"], "URBAN_STANDARD_CANDIDATE", "PROVISIONAL"
    else:
        return {"state": BLOCKED, "count": None, "flag": "PARAPET_STIFFENER_SPACING_REQUIRED",
                "why": "no spacing in drawing, project rule or Urban candidate"}
    n_bays = math.ceil(parapet_length_m / sp - 1e-9) if parapet_length_m > 0 else 0
    out = {"state": state, "authority": auth, "spacing_m": sp, "bays": n_bays,
           "intermediate_stiffeners": max(0, n_bays - 1),
           "flag": None if state == "VERIFIED" else "PARAPET_STIFFENER_SPACING_REQUIRED"}
    if auth == "URBAN_STANDARD_CANDIDATE":
        out["scenario_only"] = True
        out["why"] = "Urban owner practice, not printed on the drawing - provisional scenario, never verified"
    return out


def parapet_ring_beam_requirement(sources):
    """A parapet top ring beam needs section, longitudinal bars, stirrups, path and connections from a source.
    Missing any -> BLOCKED (a provisional scenario may still be shown separately)."""
    need = ("section", "longitudinal_bars", "stirrups", "path", "connections")
    missing = [k for k in need if not (sources or {}).get(k)]
    return {"state": BLOCKED if missing else "DEFINED", "missing": missing,
            "flag": "PARAPET_TOP_RING_BEAM_DETAIL_REQUIRED" if missing else None}
