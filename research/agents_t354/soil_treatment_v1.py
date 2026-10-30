"""SOIL_TREATMENT_V1 (T-354): scope and quantity rules for B1-05 soil treatment / anti-termite (every villa).

Research module, unwired, stdlib only. No engine module, method version, route G, rule / knowledge file or candidate
line uses it.

Physical element (ERS s.2.1): a chemical (termiticide) barrier applied to the soil BEFORE the structure is placed on
or against it: the top of the compacted fill under a slab on grade, and, when the source says so, the bottoms and sides
of footing pits and trenches and the backfill against buried faces. It is NOT: the waterproofing of earth-contact
concrete faces, the membrane / screed under footings, the blinding, the fill itself, a polythene sheet or DPM under a
slab, or a cement type for concrete in contact with soil. Those are other layers with their own lines.

Rules (scope: every villa; provenance T-354):
R-ST-1  A soil-treatment quantity exists only when a SOURCE requires it: a drawing note, a specification line or an
        answered owner rule, each cited (document, sheet / page, note or clause). Usual practice, a typical
        specification of another project, a reference book or the freelancer's row is not a source (refused).
R-ST-2  NOT_IN_DRAWN_SCOPE only when every sheet of the issued set was searched and none requires it; any unsearched
        sheet leaves the status UNKNOWN. Either way the area is None, never 0 and never a convention (plot area,
        footprint, GF area).
R-ST-3  The measurement basis follows the source's wording: PLAN (one plan area under the building, pits and trenches
        inside it NOT added again) or SURFACES (each named surface once, at its own level). A plan-overlap deduction
        between two surfaces is admissible only when they share a level (T-356 lesson); a pit bottom inside the slab
        plan is a second surface only under SURFACES.
R-ST-4  A zone whose area or level is not established is HELD by name: the determinate part and the held names are
        reported apart; a held zone written as 0 is refused.
"""
from __future__ import annotations

from typing import Iterable

RULE_ID = "SOIL_TREATMENT_V1"
SOURCE_KINDS = ("DRAWING_NOTE", "SPECIFICATION", "OWNER_RULE")
NOT_SOURCES = ("USUAL_PRACTICE", "TYPICAL_SPEC_OTHER_PROJECT", "REFERENCE_BOOK", "FREELANCER_ROW", "ASSUMED")
SURFACES = ("SLAB_ON_GRADE_FILL_TOP", "PIT_BOTTOM", "PIT_SIDE", "TRENCH_BOTTOM", "TRENCH_SIDE", "BACKFILL_FACE")
BASES = ("PLAN", "SURFACES")
UNIT_FACTOR = {"m": 1.0, "cm": 0.01, "mm": 0.001}


class RefusedInput(ValueError):
    """An input that would create, double or zero a quantity without evidence."""


def _check_source(src: dict) -> None:
    kind = src.get("kind")
    if kind in NOT_SOURCES:
        raise RefusedInput(f"{kind} is not a source for soil treatment (R-ST-1)")
    if kind not in SOURCE_KINDS:
        raise RefusedInput(f"unknown source kind {kind!r} (R-ST-1)")
    if not src.get("document") or not (src.get("sheet") or src.get("clause")) or not src.get("ref"):
        raise RefusedInput("a source must cite its document, sheet or clause and note / clause number (R-ST-1)")
    if src.get("basis") not in BASES:
        raise RefusedInput("a requiring source must state its basis PLAN or SURFACES (R-ST-3)")


def scope_status(sheet_search: Iterable[dict], set_sheets: Iterable[str], sources: Iterable[dict] = (),
                 convention_area_m2=None) -> dict:
    """sheet_search: {sheet, searched: bool, requires: [note ids]}; set_sheets: every sheet of the issued set;
    sources: requiring sources (drawing note / specification / owner rule). Returns REQUIRED / NOT_IN_DRAWN_SCOPE /
    UNKNOWN with area None (the area comes only from zones_quantity under a REQUIRED scope)."""
    set_sheets = list(set_sheets)
    rows = {r["sheet"]: r for r in sheet_search}
    srcs = list(sources)
    for s in srcs:
        _check_source(s)
    unsearched = [s for s in set_sheets if s not in rows or not rows[s].get("searched")]
    on_sheets = [f"{s} note {n}" for s in set_sheets if s in rows for n in rows[s].get("requires", [])]
    if on_sheets and not srcs:
        raise RefusedInput("a sheet marks a requiring note but no source record cites it (R-ST-1)")
    if srcs:
        bases = sorted({s["basis"] for s in srcs})
        return {"rule": RULE_ID, "status": "REQUIRED", "refs": [f"{s['document']} {s.get('sheet') or s.get('clause')}"
                f" {s['ref']}" for s in srcs], "bases": bases, "area_m2": None, "unsearched": unsearched}
    if convention_area_m2 is not None:
        raise RefusedInput("an area offered without a requiring source (convention, R-ST-2)")
    if unsearched:
        return {"rule": RULE_ID, "status": "UNKNOWN", "refs": [], "bases": [], "area_m2": None,
                "unsearched": unsearched, "reason": "not every sheet of the issued set was searched"}
    return {"rule": RULE_ID, "status": "NOT_IN_DRAWN_SCOPE", "refs": [], "bases": [], "area_m2": None,
            "unsearched": [], "reason": f"all {len(set_sheets)} sheets searched; no note, specification line or "
                                        "answered rule requires soil treatment"}


def polygon_area(points, unit: str = "m") -> float:
    """Shoelace area of a closed outline (points in `unit`), in m2; orientation-free (mirror / rotation invariant)."""
    if unit not in UNIT_FACTOR:
        raise RefusedInput(f"unit {unit!r} not stated as m / cm / mm")
    pts = [(float(x), float(y)) for x, y in points]
    if len(pts) < 3:
        raise RefusedInput("an outline needs at least 3 points")
    a = 0.0
    for (x1, y1), (x2, y2) in zip(pts, pts[1:] + pts[:1]):
        a += x1 * y2 - x2 * y1
    return abs(a) / 2.0 * UNIT_FACTOR[unit] ** 2


def _zone_area(z: dict):
    if z.get("area_m2") is not None and z.get("outline") is not None:
        raise RefusedInput(f"zone {z['id']}: area and outline both given (one source per zone)")
    if z.get("outline") is not None:
        return polygon_area(z["outline"], z.get("unit", "m"))
    return z.get("area_m2")


def zones_quantity(scope: dict, zones: Iterable[dict], basis: str, deductions: Iterable[dict] = ()) -> dict:
    """zones: {id, surface, level_m (None = HELD), area_m2 | outline (+unit), inside_plan_of (zone id or None),
    held_reason}. basis: PLAN or SURFACES (must be one the source states). deductions: {from, of, area_m2} plan
    overlaps between two zones. Returns determinate m2, held names, per-zone rows; never 0 for a held zone."""
    if scope.get("status") != "REQUIRED":
        raise RefusedInput(f"no quantity under scope {scope.get('status')} (R-ST-1 / R-ST-2)")
    if basis not in scope.get("bases", ()):
        raise RefusedInput(f"basis {basis} is not the one the source states {scope.get('bases')} (R-ST-3)")
    zones = list(zones)
    ids = [z["id"] for z in zones]
    if len(ids) != len(set(ids)):
        raise RefusedInput("a zone appears twice (one surface, one row)")
    by_id = {z["id"]: z for z in zones}
    rows, held, total = [], [], 0.0
    for z in zones:
        if z.get("surface") not in SURFACES:
            raise RefusedInput(f"zone {z['id']}: surface {z.get('surface')!r} is not a soil-treatment surface")
        area = _zone_area(z)
        if z.get("held_reason") and area == 0:
            raise RefusedInput(f"zone {z['id']}: a held zone written as 0 (R-ST-4)")
        if basis == "PLAN" and z["surface"] in ("PIT_SIDE", "TRENCH_SIDE", "BACKFILL_FACE"):
            raise RefusedInput(f"zone {z['id']}: a vertical face has no plan area under PLAN basis (R-ST-3)")
        if basis == "PLAN" and z["surface"] != "SLAB_ON_GRADE_FILL_TOP" and not z.get("outside_plan"):
            if not z.get("inside_plan_of"):
                raise RefusedInput(f"zone {z['id']}: a {z['surface']} under PLAN basis must say whether it lies "
                                   "inside a slab plan (not added) or outside every plan (R-ST-3)")
            if z["inside_plan_of"] not in by_id:
                raise RefusedInput(f"zone {z['id']}: inside_plan_of names a zone that is not in the list")
            rows.append({"id": z["id"], "surface": z["surface"], "m2": None, "state": "INSIDE_PLAN_NOT_ADDED",
                         "inside": z["inside_plan_of"]})
            continue
        if area is None or z.get("held_reason") or (basis == "SURFACES" and z.get("level_m") is None):
            held.append(z["id"])
            rows.append({"id": z["id"], "surface": z["surface"], "m2": None, "state": "HELD",
                         "reason": z.get("held_reason") or "area or level not established"})
            continue
        total += area
        rows.append({"id": z["id"], "surface": z["surface"], "m2": round(area, 6), "state": "DETERMINATE"})
    for d in deductions:
        a, b = by_id.get(d["from"]), by_id.get(d["of"])
        if a is None or b is None:
            raise RefusedInput("a deduction names a zone that is not in the list")
        if a.get("level_m") is None or b.get("level_m") is None or abs(a["level_m"] - b["level_m"]) > 1e-9:
            raise RefusedInput(f"overlap {d['from']} / {d['of']} deducted between different or unknown levels "
                               "(R-ST-3)")
        total -= float(d["area_m2"])
    return {"rule": RULE_ID, "basis": basis, "determinate_m2": round(total, 6), "held": held, "rows": rows,
            "status": "HELD" if held else "DETERMINATE"}
