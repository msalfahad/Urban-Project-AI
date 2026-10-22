"""Synthetic villa Q (not the development villa): documents, printed records, drawn inventory and BOQ lines for the
default guard. Every number below is hand-calculated here, before any run.

POOL P1 (structural detail D-S05 prints floor 0.35 m and wall 0.25 m; pool section D-A05 prints the FINISHED water depth
1.40 m from coping to tile and the floor build-up 0.05 m, tile + screed, over the structure line)
  outer plan: rectangle 5.00 x 2.50 + half circle r 1.25 on one short end
              = 12.500000 + pi x 1.25^2 / 2 (2.454369)                    = 14.954369 m2
  inner plan: 4.75 x 2.00 + pi x 1.00^2 / 2 (1.570796)                    = 11.070796 m2
  wall ring plan = 14.954369 - 11.070796                                  =  3.883573 m2
      straight strip only (old behaviour): 2 x 5.00 x 0.25 + 2.00 x 0.25 =  3.000000 m2 (curved half 0.883573 lost:
      pi x (1.25^2 - 1.00^2) / 2 = 0.883573)
  structural wall height above the base top = finished depth 1.40 + build-up 0.05 = 1.45 m
  RIGHT:   floor 14.954369 x 0.35 = 5.234029 m3; walls 3.883573 x 1.45 = 5.631181 m3; pool 10.865210 m3
  OLD:     floor 12.500000 x 0.25 (convention) = 3.125000; walls 3.000000 x 1.60 (convention) = 4.800000; 7.925000 m3
  T-183 r2 adverse: walls 3.883573 x 1.40 (finished depth as RC height) = 5.437002 m3 (-0.194179 = 3.883573 x 0.05)
  junction adverse: walls 3.883573 x 1.80 (base bottom to rim, base counted again) = 6.990431 m3
                    (+1.359251 = 3.883573 x 0.35, the base under the wall already in the floor)

STAIRS (schedule D-S10 prints waist 0.15 m)
  flight: waist 1.20 x 3.00 sloped x 0.15 = 0.540 + 10 steps x (0.5 x 0.30 x 0.17 x 1.20 = 0.0306) = 0.306 -> 0.846 m3
  landing: 1.20 x 1.20 x 0.15 = 0.216 m3
  ST-A dog-leg GF -> 1F (F1, F2, L1) -> 2F (F3, F4, L2) = 4 x 0.846 + 2 x 0.216 = 3.816 m3; ST-B external, F1 = 0.846
  stairs 4.662 m3

DOME D1: shell drawn surface 12.00 m2 x printed 0.10 m (D-S05) = 1.200 m3 (approved design S0); the client asked for an
open skylight instead (S1: no shell, skylight glazing 7.07 m2); no consultant revision issued.

COLUMN C3 north face 0.60 m wide; beam B7 0.20 m wide runs through it (the open face width is 0.40 m, T-163 lesson).

WATER TANK T1: wall height printed nowhere; convention TANK_HEIGHT_M 1.50 with a SYNTHETIC approval id (the guard only
checks that one is cited): 2.40 m2 wall ring plan x 1.50 = 3.600 m3.
"""

import copy

DOCS = [{"doc": "D-A01", "role": "PLAN"}, {"doc": "D-A05", "role": "SECTION"},
        {"doc": "D-S05", "role": "STRUCTURAL_DETAIL"}, {"doc": "D-S10", "role": "SCHEDULE"},
        {"doc": "D-E01", "role": "ELEVATION"}]
ALL_SEARCHED = ["D-A01", "D-A05", "D-S05", "D-S10"]

PRINTED = [
    {"id": "PR-1", "element_kind": "POOL", "element_id": None, "param": "POOL_FLOOR_THICKNESS_M", "value": 0.35,
     "unit": "m", "doc": "D-S05", "note": "pool base 35", "basis": "STRUCTURAL"},
    {"id": "PR-2", "element_kind": "POOL", "element_id": None, "param": "POOL_WALL_THICKNESS_M", "value": 0.25,
     "unit": "m", "doc": "D-S05", "note": "pool wall 25", "basis": "STRUCTURAL"},
    {"id": "PR-3", "element_kind": "POOL", "element_id": "P1", "param": "POOL_WALL_HEIGHT_M", "value": 1.40,
     "unit": "m", "doc": "D-A05", "note": "water depth 1.40 coping to tile", "basis": "FINISHED"},
    {"id": "PR-4", "element_kind": "POOL", "element_id": "P1", "param": "POOL_FLOOR_BUILDUP_M", "value": 0.05,
     "unit": "m", "doc": "D-A05", "note": "tile + screed 5 cm over the structure line", "basis": "BUILD_UP"},
    {"id": "PR-5", "element_kind": "STAIR", "element_id": None, "param": "STAIR_WAIST_M", "value": 0.15,
     "unit": "m", "doc": "D-S10", "note": "waist 15", "basis": "STRUCTURAL"},
    {"id": "PR-7", "element_kind": "DOME", "element_id": "D1", "param": "DOME_SHELL_THICKNESS_M", "value": 0.10,
     "unit": "m", "doc": "D-S05", "note": "shell 10", "basis": "STRUCTURAL"},
]
PR_DISAGREE = {"id": "PR-6", "element_kind": "POOL", "element_id": "P1", "param": "POOL_FLOOR_THICKNESS_M",
               "value": 0.30, "unit": "m", "doc": "D-A05", "note": "base 30 on the section", "basis": "STRUCTURAL"}

RING, OUTER, STRAIGHT = 3.883573, 14.954369, 3.000000
FLIGHT, LANDING = 0.846, 0.216

INVENTORY = [
    {"id": "P1", "kind": "POOL", "parts": {"FLOOR": {"value": OUTER, "unit": "m2"},
                                            "WALLS": {"value": RING, "unit": "m2"}}},
    {"id": "ST-A", "kind": "STAIR", "parts": {"F1": None, "F2": None, "L1": None, "F3": None, "F4": None, "L2": None}},
    {"id": "ST-B", "kind": "STAIR", "parts": {"F1": None}},
    {"id": "D1", "kind": "DOME", "parts": {"SHELL": {"value": 12.0, "unit": "m2"}}},
    {"id": "C3", "kind": "COLUMN", "parts": {"FACE_N": None}},
    {"id": "T1", "kind": "WATER_TANK", "parts": {"WALLS": {"value": 2.40, "unit": "m2"}}},
]
MEMBERS = [{"id": "B7", "width_m": 0.20}]


def _ln(i, el, kind, part, qty, values, *, trade="CONCRETE", unit="m3", footprint=None, covers=None,
        searched=ALL_SEARCHED, **kw):
    d = {"id": i, "element_id": el, "element_kind": kind, "part": part, "trade": trade, "unit": unit, "qty": qty,
         "state": "PROVISIONAL", "values": values, "searched": list(searched), "covers": covers or []}
    if footprint is not None:
        d["footprint"] = {"value": footprint, "unit": "m2"}
    d.update(kw)
    return d


def right_lines():
    """The drawing-derived BOQ: every check passes."""
    st = {"STAIR_WAIST_M": {"value": 0.15, "source": "PRINTED", "ref": "PR-5"}}
    lines = [
        _ln("POOL-FLOOR", "P1", "POOL", "FLOOR", round(OUTER * 0.35, 6),
            {"POOL_FLOOR_THICKNESS_M": {"value": 0.35, "source": "PRINTED", "ref": "PR-1"}}, footprint=OUTER,
            covers=["P1:BASE_FIELD", "P1:BASE_UNDER_WALL"]),
        _ln("POOL-WALLS", "P1", "POOL", "WALLS", round(RING * 1.45, 6),
            {"POOL_WALL_HEIGHT_M": {"value": 1.45, "source": "DERIVED", "ref": ["PR-3", "PR-4"]},
             "POOL_WALL_THICKNESS_M": {"value": 0.25, "source": "PRINTED", "ref": "PR-2"}}, footprint=RING,
            covers=["P1:WALL_ABOVE_BASE"]),
    ]
    for p in ("F1", "F2", "F3", "F4"):
        lines.append(_ln(f"ST-A-{p}", "ST-A", "STAIR", p, FLIGHT, st, covers=[f"ST-A:{p}"]))
    for p in ("L1", "L2"):
        lines.append(_ln(f"ST-A-{p}", "ST-A", "STAIR", p, LANDING, st, covers=[f"ST-A:{p}"]))
    lines.append(_ln("ST-B-F1", "ST-B", "STAIR", "F1", FLIGHT, st, covers=["ST-B:F1"]))
    lines.append(_ln("SLAB-1F", "SL1", "SLAB", "WHOLE", 18.0,
                     {"SLAB_T_M": {"value": 0.16, "source": "DRAWN"}}, covers=["SL1:FIELD"]))
    lines.append(_ln("DOME-D1-SHELL", "D1", "DOME", "SHELL", 1.2,
                     {"DOME_SHELL_THICKNESS_M": {"value": 0.10, "source": "PRINTED", "ref": "PR-7"}},
                     footprint=12.0, covers=["D1:SHELL"]))
    lines.append(_ln("DOME-D1-SKYLIGHT", "D1", "DOME", "SKYLIGHT", 7.07, {}, trade="GLAZING", unit="m2",
                     scenario="S1", origin="CLIENT_REQUEST"))
    lines.append(_ln("C3-FACE-N", "C3", "COLUMN", "FACE_N", 1.2, {}, trade="FORMWORK", unit="m2",
                     deductions=[{"member": "B7", "width_m": 0.20, "face_width_m": 0.60}]))
    lines.append(_ln("T1-WALLS", "T1", "WATER_TANK", "WALLS", 3.6,
                     {"TANK_HEIGHT_M": {"value": 1.50, "source": "CONVENTION", "ref": "TANK_HEIGHT_M",
                                        "approval": "SYNTHETIC-OWNER-RULE-1"}}, footprint=2.40))
    return lines


def by_id(lines):
    return {ln["id"]: ln for ln in lines}


def replace(lines, line_id, **changes):
    out = copy.deepcopy(lines)
    for ln in out:
        if ln["id"] == line_id:
            ln.update(changes)
    return out


def drop(lines, *ids):
    return [ln for ln in copy.deepcopy(lines) if ln["id"] not in ids]


def old_pool(lines):
    """The old engine behaviour: conventions 0.25 / 1.60, straight strip and rectangle only."""
    out = replace(lines, "POOL-FLOOR", qty=3.125, footprint={"value": 12.5, "unit": "m2"}, searched=["D-A01"],
                  values={"POOL_FLOOR_THICKNESS_M": {"value": 0.25, "source": "CONVENTION",
                                                     "ref": "POOL_FLOOR_THICKNESS_M"}})
    return replace(out, "POOL-WALLS", qty=4.8, footprint={"value": STRAIGHT, "unit": "m2"}, searched=["D-A01"],
                   values={"POOL_WALL_HEIGHT_M": {"value": 1.60, "source": "CONVENTION", "ref": "POOL_WALL_HEIGHT_M"},
                           "POOL_WALL_THICKNESS_M": {"value": 0.25, "source": "PRINTED", "ref": "PR-2"}})


def guard_kwargs(**over):
    kw = {"documents": DOCS, "printed": PRINTED, "inventory": INVENTORY, "members": MEMBERS, "revisions": []}
    kw.update(over)
    return kw
