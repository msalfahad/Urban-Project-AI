"""FINISH MATERIALS TABLE V2 (task T-456, owner directive 2026-11-02 C1; opt-in, UNWIRED_PRODUCER: read by no released
method and by no candidate V3.0.x; no released or candidate quantity changes).

ONE behaviour change against FINISH_MATERIALS_TABLE_V1 (engine/source/finish_materials_table.py, kept byte-identical):

    V1 _floor_like, branch 'area given' (finish_materials_table.py:112):   area_m2 * unit_m * unit_m
    V2 _floor_like, branch 'area given':                                   area_m2  (already square metres)

The key is named area_m2 and V1's own docstring says an area "comes from the caller" in m2, so multiplying it by the
drawing unit squared converts it a second time: 20 m2 with millimetre units (unit_m = 0.001) became 0.00002 m2, and the
bed mortar, cement bags, sand and adhesive bags derived from it shrank by the same 10^6 (reproduced in
research/agents_t456/t456_reproduce.py). With metre units (unit_m = 1.0) V1 and V2 agree to the last digit.

Unit contract of V2 (every other branch exactly as V1):
    area_m2                     square metres, never scaled
    candidate_m2                square metres, never scaled (as V1)
    polygon / holes             drawing units -> x unit_m ** 2 (as V1)
    length, width               drawing units -> x unit_m ** 2 (as V1)
    wet wall, stair flight      drawing units, each length x unit_m (as V1, via the V1 functions)
    unit_m missing / 0 / broken HELD 'UNIT_NOT_GIVEN' for every kind (as V1: a broken unit is a broken input, also when
                                the area itself needs no unit)

Owner values, statuses, held reasons, sums and purchase rounding are V1's own objects (imported, not copied), so V2 can
never drift from V1 anywhere but the one corrected line. Project-agnostic: no project, layer, room name or count."""

from __future__ import annotations

from engine.source import finish_materials_table as V1

METHOD_ID = "FINISH_MATERIALS_TABLE_V2"
SUPERSEDES = V1.METHOD_ID
DEFAULT_GUARD_CLASS = "UNWIRED_PRODUCER"
RULES = V1.RULES + ("T-456 C1: a given area_m2 is square metres and is never multiplied by the drawing unit",)
CHANGE = {
    "v1_ref": "engine/source/finish_materials_table.py:112 (_floor_like, area given: a * u * u)",
    "v2": "area given: a (square metres, unscaled)",
    "effect_metres": "none (unit_m = 1.0)",
    "effect_millimetres": "V1 gave area x 1e-6; V2 gives the area",
}

# the same constants, so a caller can switch module without renaming anything
KINDS = V1.KINDS
DRY_FLOOR, WET_FLOOR, WET_WALL = V1.DRY_FLOOR, V1.WET_FLOOR, V1.WET_WALL
STAIR_FLIGHT, STAIR_LANDING, ROOF, BALCONY = V1.STAIR_FLIGHT, V1.STAIR_LANDING, V1.ROOF, V1.BALCONY
PORCELAIN_CERAMIC, MARBLE_STONE = V1.PORCELAIN_CERAMIC, V1.MARBLE_STONE
DEFAULT_FINISH = V1.DEFAULT_FINISH
OWNER_VALUES = V1.OWNER_VALUES
polygon_area = V1.polygon_area
materials = V1.materials


def _floor_like(e, u):
    """DRY_FLOOR / WET_FLOOR / ROOF / BALCONY / STAIR_LANDING: area given (m2), polygon, or length x width."""
    if e.get("area_status") == "HELD" or e.get("area_m2") is None:
        return V1._floor_like(e, u)          # held, polygon and length x width branches: unchanged V1 code
    a = V1._num(e["area_m2"])
    if a is None or a == 0:
        return V1._held("AREA_INVALID (missing, zero or negative area given)", e.get("basis"))
    return {"area_m2": V1._r(a), "status": "RELEASED", "reason": None,
            "basis": e.get("basis") or "area given (m2, not scaled by the drawing unit)", "candidate_m2": None}


def surface(e):
    kind = e.get("kind")
    if kind not in KINDS:
        return V1._held(f"UNKNOWN_KIND {kind!r}")
    u = V1._num(e.get("unit_m", 1.0))
    if not u:
        return V1._held("UNIT_NOT_GIVEN")
    if kind == WET_WALL:
        return V1._wet_wall(e, u)
    if kind == STAIR_FLIGHT:
        return V1._flight(e, u)
    return _floor_like(e, u)


def row(e, values=OWNER_VALUES):
    s = surface(e)
    kind = e.get("kind")
    finish = e.get("finish", DEFAULT_FINISH.get(kind))
    m = materials(kind, finish, s["area_m2"], values)
    r = {"id": e.get("id"), "floor": e.get("floor"), "name": e.get("name"), "kind": kind, "finish": finish,
         "source": e.get("source"), "note": e.get("note")}
    r.update(s)
    r.update(m)
    return r


def table(elements, values=OWNER_VALUES):
    """Rows in input order, sums per floor, per kind and for the project (V1 sums: a held value is listed under
    not_in_sum, never added as 0; ids must be unique)."""
    ids = [e.get("id") for e in elements]
    dup = sorted({i for i in ids if ids.count(i) > 1}, key=str)
    if dup:
        raise ValueError(f"duplicate element ids (a surface is reported once): {dup}")
    rows = [row(e, values) for e in elements]
    floors, kinds = {}, {}
    for r in rows:
        floors.setdefault(r["floor"], []).append(r)
        kinds.setdefault(r["kind"], []).append(r)
    return {"method": METHOD_ID, "supersedes": SUPERSEDES, "rules": list(RULES), "owner_values": values, "rows": rows,
            "per_floor": {f: V1._sums(v) for f, v in floors.items()},
            "per_kind": {k: V1._sums(v) for k, v in kinds.items()},
            "project": V1._sums(rows)}
