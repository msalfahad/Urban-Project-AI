"""T-357 GROUND_REFERENCE_V1 (research, unwired, stdlib only): the existing-ground reference every below-grade quantity
measures from, the plot area and boundary from the drawings, and the site-clearance scope decision.

Physical elements (ERS s.2.1):

- EXISTING GROUND (EG): the natural / existing plot surface before any work. It is the top of the soil the excavation
  removes and the base of any fill placed above it. It is NOT a finished level (a court paving at +0.15, an annex
  floor at +0.30, a finished floor at +1.00 are finishes on top of EG and fill). A structural note that measures from
  "the existing plot level" NAMES this datum; it does not give its value.
- PLOT: the land parcel inside the plot boundary (the property line printed with its side lengths). Plot area is the
  plane area of that polygon.
- SITE CLEARANCE: removal of vegetation, debris, existing obstructions and topsoil before setting out. A quantity
  exists only if a drawing note, specification line or answered owner rule puts it in scope (MISSION.md drawing-first,
  UP-QTY-STATUS-001); its area is never invented from a convention (plot area, plot minus footprint, + 1 m margin).

Statuses (WORKFLOW_CONTROLS s.5 vocabulary, the reference-specific labels the task asks for):

- existing-ground reference: PRINTED (a level mark inside the plot that labels existing / natural ground), DERIVED
  (no such mark, but ground level marks at EVERY plot corner, all equal, plus agreeing ground lines on cuts: a flat
  plane through printed values), SLOPING (printed ground marks that differ: no single value; quantities need the
  per-corner surface), HELD (no printed ground value, or corners not covered). Never 0.00 by default.
- clearance scope: PRINTED_SCOPE (a note requires it, with sheet + note number), NOT_IN_DRAWN_SCOPE (every sheet in
  the set searched, none requires it), UNKNOWN (a sheet of the set not searched).

Rules (proposed, any villa; provenance T-357, T-170 R-EXC-LEDGER-1, T-200 UP-LEVEL-DATUM-001, Q-21 C, OQ-13):
R-EG-REF-1 the existing-ground value comes only from ground-class level marks; finished levels are refused.
R-EG-REF-2 one value only when every plot corner carries a ground mark and all printed ground values agree; otherwise
SLOPING (per-corner) or HELD; the value is never 0.00 unless printed or derived as above.
R-PLOT-1 plot area = shoelace area of the printed boundary polygon in declared metres; printed coverage percentages
cross-check it (each percentage reproduced by rounding or truncation to the printed decimals).
R-CLR-1 clearance scope only from a printed note / spec / answered rule; evidence of absence must list every sheet;
an area from a convention is refused.
R-EG-COEF-1 a quantity whose bottom (or top) is an ABSOLUTE printed level changes by its plan area per metre of EG
shift; one measured RELATIVE to EG (a 'not less than x below the existing plot level' bound, a beam 'at N.G.')
does not; a HELD reference gives no coefficient (None, never 0).
"""
from __future__ import annotations

from typing import Iterable

GROUND_KINDS = ("EXISTING_GROUND_SPOT", "PLOT_EDGE_GROUND", "CUT_GROUND_LINE")
FINISHED_KINDS = ("FINISHED_FLOOR", "FINISHED_GROUND", "FINISHED_ROOF")
UNIT_FACTOR = {"m": 1.0, "mm": 0.001, "cm": 0.01}


class RefusedInput(ValueError):
    """An input the rules refuse (finished level offered as ground, undeclared unit, convention area)."""


def _to_m(value, unit):
    if unit not in UNIT_FACTOR:
        raise RefusedInput(f"undeclared or unknown unit {unit!r}")
    return None if value is None else float(value) * UNIT_FACTOR[unit]


def existing_ground_reference(marks: Iterable[dict], corners: Iterable[str]) -> dict:
    """Classify the existing-ground reference from level marks.

    marks: dicts with kind, value (None if named without value), unit, sheet, handle, and for PLOT_EDGE_GROUND /
    EXISTING_GROUND_SPOT a 'corner' key (corner id) or 'corner': None for a mid-side mark. corners: the plot corner ids
    (e.g. 'C1'..'C4'). Returns status, value_m (or None), per_corner, refs, reasons."""
    marks = list(marks)
    corners = list(corners)
    reasons = []
    for mk in marks:
        if mk.get("offered_as_ground") and mk["kind"] in FINISHED_KINDS:
            raise RefusedInput(f"finished level {mk.get('handle')} ({mk['kind']}) offered as existing ground (R-EG-REF-1)")
    ground = [dict(mk, value_m=_to_m(mk.get("value"), mk.get("unit"))) for mk in marks if mk["kind"] in GROUND_KINDS]
    valued = [g for g in ground if g["value_m"] is not None]
    named_only = [g for g in ground if g["value_m"] is None]
    refs = [f"{g['sheet']}:{g['handle']}" for g in valued]
    if not valued:
        reasons.append("no ground-class mark prints a value" + (" (datum named only)" if named_only else ""))
        return {"status": "HELD", "value_m": None, "per_corner": {}, "refs": [], "reasons": reasons}
    per_corner = {}
    for c in corners:
        vals = sorted({round(g["value_m"], 4) for g in valued if g.get("corner") == c})
        per_corner[c] = vals[0] if len(vals) == 1 else (vals if vals else None)
    distinct = sorted({round(g["value_m"], 4) for g in valued})
    spots = [g for g in valued if g["kind"] == "EXISTING_GROUND_SPOT"]
    if len(distinct) > 1:
        reasons.append(f"printed ground values differ {distinct}: no single EG; quantities need the per-corner surface")
        return {"status": "SLOPING", "value_m": None, "per_corner": per_corner, "refs": refs, "reasons": reasons}
    value = distinct[0]
    if spots:
        reasons.append("an existing-ground spot level inside the plot is printed")
        return {"status": "PRINTED", "value_m": value, "per_corner": per_corner, "refs": refs, "reasons": reasons}
    missing = [c for c in corners if per_corner.get(c) is None]
    if missing:
        reasons.append(f"plot corners without a ground mark: {missing}")
        return {"status": "HELD", "value_m": None, "per_corner": per_corner, "refs": refs, "reasons": reasons}
    reasons.append("every plot corner carries a ground mark, all equal; no spot level inside the plot (flat plane "
                   "through printed values; interior undulation UNKNOWN)")
    return {"status": "DERIVED", "value_m": value, "per_corner": per_corner, "refs": refs, "reasons": reasons}


def polygon_area(vertices, unit: str) -> float:
    """Shoelace area (m2) of a closed polygon given as [(x, y), ...] in a declared unit; orientation-free."""
    f = UNIT_FACTOR.get(unit)
    if f is None:
        raise RefusedInput(f"undeclared or unknown unit {unit!r}")
    pts = [(x * f, y * f) for x, y in vertices]
    if len(pts) < 3:
        raise RefusedInput("a plot polygon needs at least 3 vertices")
    s = 0.0
    for i in range(len(pts)):
        x1, y1 = pts[i]
        x2, y2 = pts[(i + 1) % len(pts)]
        s += x1 * y2 - x2 * y1
    return abs(s) / 2.0


def _reproduces(pct_calc: float, pct_printed: float, decimals: int) -> str | None:
    q = 10 ** decimals
    if int(pct_calc * q + 1e-9) == round(pct_printed * q):
        return "TRUNCATED"
    if round(pct_calc * q) == round(pct_printed * q):
        return "ROUNDED"
    return None


def check_coverage_percentages(plot_area_m2: float, rows: Iterable[dict]) -> dict:
    """rows: {name, area_m2, pct, decimals}. Each printed percentage must be reproduced from area / plot area by
    rounding or truncation to its printed decimals; else CONFLICT (two printed values disagree)."""
    out = []
    for r in rows:
        calc = 100.0 * r["area_m2"] / plot_area_m2
        how = _reproduces(calc, r["pct"], r.get("decimals", 2))
        implied = 100.0 * r["area_m2"] / r["pct"]
        out.append({"name": r["name"], "area_m2": r["area_m2"], "pct_printed": r["pct"], "pct_calc": round(calc, 4),
                    "implied_plot_m2": round(implied, 3), "agreement": how or "CONFLICT"})
    status = "CONSISTENT" if all(o["agreement"] != "CONFLICT" for o in out) else "CONFLICT"
    return {"status": status, "rows": out}


def clearance_scope(sheet_search: Iterable[dict], set_sheets: Iterable[str], convention_area_m2=None) -> dict:
    """sheet_search: {sheet, searched: bool, clearance_notes: [note ids]}. set_sheets: every sheet of the issued set.
    convention_area_m2: refused when given without a printed scope (R-CLR-1)."""
    rows = {r["sheet"]: r for r in sheet_search}
    unsearched = [s for s in set_sheets if s not in rows or not rows[s].get("searched")]
    found = [(s, n) for s in set_sheets if s in rows for n in rows[s].get("clearance_notes", [])]
    if found:
        return {"status": "PRINTED_SCOPE", "refs": [f"{s} note {n}" for s, n in found], "area_m2": None,
                "unsearched": unsearched, "reason": "a note requires clearance: its area comes from that note's extent"}
    if convention_area_m2 is not None:
        raise RefusedInput("a clearance area offered without a printed scope (convention, R-CLR-1)")
    if unsearched:
        return {"status": "UNKNOWN", "refs": [], "area_m2": None, "unsearched": unsearched,
                "reason": "not every sheet of the set was searched"}
    return {"status": "NOT_IN_DRAWN_SCOPE", "refs": [], "area_m2": None, "unsearched": [],
            "reason": f"all {len(rows)} sheets searched; no note, specification line or answered rule requires it"}


def eg_shift_coefficients(components: Iterable[dict]) -> list[dict]:
    """m3 per metre of EG RISE (absolute printed levels fixed) per component.

    component: {id, plan_m2 (None if HELD), side: 'BELOW_EG' | 'ABOVE_EG', reference: 'ABSOLUTE' | 'RELATIVE_TO_EG' |
    'HELD'}. BELOW_EG with an ABSOLUTE far face: +plan (more depth below a higher EG); ABOVE_EG with an ABSOLUTE top:
    -plan; RELATIVE_TO_EG: 0 (the face moves with EG); HELD or plan None: None (never 0)."""
    out = []
    for c in components:
        if c["reference"] == "HELD" or c.get("plan_m2") is None:
            coef = None
        elif c["reference"] == "RELATIVE_TO_EG":
            coef = 0.0
        elif c["reference"] == "ABSOLUTE":
            coef = c["plan_m2"] if c["side"] == "BELOW_EG" else -c["plan_m2"]
        else:
            raise RefusedInput(f"unknown reference {c['reference']!r}")
        out.append({"id": c["id"], "side": c["side"], "reference": c["reference"], "plan_m2": c.get("plan_m2"),
                    "coef_m3_per_m": None if coef is None else round(coef, 6)})
    return out
