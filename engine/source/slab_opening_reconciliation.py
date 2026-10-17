"""SLAB_OPENING_RECONCILIATION (generic): gross outline - openings = net plate, every removed m2 has an opening ID.

Each face of a slab arrangement has a role (PLATE / OPENING_*). Every OPENING_* face becomes an opening record with
its evidence. Conflicting evidence (a VOID label together with a printed thickness tag inside the same face) is not
silently deducted: it becomes OPENING_CONFLICT with two scenarios (deducted / kept as slab). Conservation:
gross = net + openings within tolerance. Two extraction routes can be compared opening by opening. Stdlib only.
"""

from __future__ import annotations

from engine.source import quantity_scenarios as QS

OPENING, OPENING_CONFLICT = "OPENING", "OPENING_CONFLICT"
MATCH, ONLY_A, ONLY_B, AREA_DIFFERENCE = "MATCH", "ONLY_ROUTE_A", "ONLY_ROUTE_B", "AREA_DIFFERENCE"


class OpeningError(ValueError):
    pass


def openings(faces, *, sheet):
    out = []
    for f in faces:
        if not f["role"].startswith("OPENING"):
            continue
        conflict = bool(f.get("tags_cm")) and "VOID" in f["role"]
        out.append({"opening_id": f"{sheet}:{f['face']}", "face": f["face"], "role": f["role"],
                    "area_m2": f["area_m2"], "evidence": f.get("why"), "thickness_tags_cm": f.get("tags_cm") or [],
                    "state": OPENING_CONFLICT if conflict else OPENING,
                    "why_conflict": "VOID label and a printed slab thickness tag in the same face" if conflict else None})
    return out


def reconcile(gross_m2, faces, *, sheet, tol_m2=0.01):
    """Net plate area scenario; every deduction is traceable to an opening ID."""
    ops = openings(faces, sheet=sheet)
    plate = sum(f["area_m2"] for f in faces if f["role"] == "PLATE")
    ded = sum(o["area_m2"] for o in ops)
    if abs(gross_m2 - plate - ded) > tol_m2:
        raise OpeningError(f"{sheet}: gross {gross_m2} != plate {plate} + openings {ded}")
    conflict = sum(o["area_m2"] for o in ops if o["state"] == OPENING_CONFLICT)
    parts = [QS.part(f"{sheet}:PLATE", "VERIFIED", plate, origin="SOURCE_FACT")]
    if conflict:
        parts.append(QS.part(f"{sheet}:CONFLICT_OPENINGS", "SOURCE_CONFLICT", 0.0, 0.0, conflict,
                             why="openings with contradictory evidence may be slab"))
    return {"sheet": sheet, "gross_m2": gross_m2, "plate_m2": plate, "openings": ops, "openings_m2": ded,
            "conflict_openings_m2": conflict, "net_area": QS.combine(parts, unit="m2"),
            "conservation_ok": True}


def compare_routes(route_a, route_b, *, match, area_tol_m2=0.5):
    """route_*: [{opening_id, area_m2, ...}]; match(a, b) -> bool. One record per opening pair / unmatched."""
    used_b, out = set(), []
    for a in route_a:
        hit = next((b for b in route_b if b["opening_id"] not in used_b and match(a, b)), None)
        if hit is None:
            out.append({"a": a["opening_id"], "b": None, "area_a": a["area_m2"], "area_b": None,
                        "difference_m2": a["area_m2"], "class": ONLY_A})
            continue
        used_b.add(hit["opening_id"])
        d = a["area_m2"] - hit["area_m2"]
        out.append({"a": a["opening_id"], "b": hit["opening_id"], "area_a": a["area_m2"], "area_b": hit["area_m2"],
                    "difference_m2": d, "class": MATCH if abs(d) <= area_tol_m2 else AREA_DIFFERENCE})
    for b in route_b:
        if b["opening_id"] not in used_b:
            out.append({"a": None, "b": b["opening_id"], "area_a": None, "area_b": b["area_m2"],
                        "difference_m2": -b["area_m2"], "class": ONLY_B})
    return out
