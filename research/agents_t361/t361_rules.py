"""T-361 fencing / gates (B13-04) and posts / glass panels (B7-11): census rules (research only, any villa).

Pure functions, standard library only. Nothing here is wired into a method; no engine, rule, knowledge or registry file
is touched. A quantity is returned only where the drawing establishes it; everything else is HELD / NOT_DRAWN /
UNKNOWN by name and never 0.

Rules (research, proposed for the lessons register; scope: every villa):

R-T361-1 GATE vs GATE OPENING. A gate leaf is counted (pcs) only where a leaf is DRAWN in the opening: a door block or
    swing arc on the plan, or a leaf outline in an elevation. An opening in a boundary line with no leaf drawn is a
    GATE OPENING: its width is the drawn gap; the leaf count, type, height and material are HELD (never 0, never an
    assumed single or double leaf).
R-T361-2 ONE ELEMENT, ONE QUANTITY. A boundary line = solid parts + gate openings (conservation to the drawn line
    length); a gate width never adds to the solid fence metres and a gate seen on the plan AND an elevation is ONE gate.
R-T361-3 OPEN EDGES. An open edge (roof, terrace, void, stair side, landing) carries its guard as DRAWN (railing band,
    elevation rail, parapet) or NONE_DRAWN with its drawn plan length. A NONE_DRAWN edge is a finding for the Lead /
    designer list (guard requirement CODE NOT VERIFIED); it never produces a guard quantity.
R-T361-4 RENDERS. A render never creates a gate, a fence infill, a railing or a guard (WORKFLOW_CONTROLS s.8).
R-T361-5 POSTS AND GLASS. Glass panels exist only where a glass element is drawn or specified (hatch, text, schedule,
    detail); posts drawn in an elevation railing are components of that railing's lm: reported as a drawn count, never
    a separate priced line without a specification (B7-11 needs a spec).
"""

from __future__ import annotations

import math

TOL_M = 0.005

EVIDENCE = ("PLAN_LEAF", "ELEVATION_LEAF", "PLAN_GAP", "ELEVATION_GAP", "RENDER", "TEXT_SPEC")
GUARD_STATES = ("DRAWN", "NONE_DRAWN", "HELD", "UNKNOWN", "WALL")


class CensusError(ValueError):
    """Input that would make a quantity from nothing (refused, never 0)."""


def _num(v, name):
    if v is None:
        raise CensusError(f"{name}: missing value (None is HELD, never 0)")
    if isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) or v <= 0:
        raise CensusError(f"{name}: not a positive finite number: {v!r}")
    return float(v)


def gate_record(gate_id, opening_width_m, evidence, leaf_count=None, leaf_size_m=None):
    """R-T361-1 / R-T361-4. evidence: set of EVIDENCE tags for THIS opening.

    Returns a dict: GATE (leaf drawn: pcs 1 per opening, leaf count as drawn) or GATE_OPENING (no leaf drawn: width
    only, leaves HELD). A render alone is refused; an opening with no width is refused (it would be a 0)."""
    ev = set(evidence)
    unknown = ev - set(EVIDENCE)
    if unknown:
        raise CensusError(f"{gate_id}: unknown evidence {sorted(unknown)}")
    if not ev - {"RENDER"}:
        raise CensusError(f"{gate_id}: a render alone never makes a gate (R-T361-4)")
    w = _num(opening_width_m, f"{gate_id} opening width")
    leaf_drawn = bool(ev & {"PLAN_LEAF", "ELEVATION_LEAF"})
    if not leaf_drawn and not (ev & {"PLAN_GAP", "ELEVATION_GAP"}):
        raise CensusError(f"{gate_id}: neither a leaf nor a gap is drawn")
    if leaf_drawn:
        if leaf_count is None:
            raise CensusError(f"{gate_id}: a drawn leaf needs its drawn leaf count")
        if leaf_count not in (1, 2):
            raise CensusError(f"{gate_id}: leaf count {leaf_count!r} not drawn as 1 or 2")
        return {"id": gate_id, "kind": "GATE", "gates_pcs": 1, "leaves_pcs": leaf_count, "opening_width_m": w,
                "leaf_size_m": leaf_size_m, "status": "DRAWING-CONFIRMED (count, width)",
                "held": ["material", "hardware", "structure"] + ([] if leaf_size_m else ["leaf size"])}
    if leaf_count is not None:
        raise CensusError(f"{gate_id}: leaf count given but no leaf is drawn (an assumed leaf, R-T361-1)")
    return {"id": gate_id, "kind": "GATE_OPENING", "gates_pcs": None, "leaves_pcs": None, "opening_width_m": w,
            "leaf_size_m": None, "status": "DRAWING-CONFIRMED (opening width); leaf HELD (not drawn)",
            "held": ["leaf count", "leaf type", "height", "material", "hardware", "structure"]}


def gate_count(records):
    """R-T361-2: one gate per opening id, whatever the number of views that show it. Returns (pcs, held_ids)."""
    seen, pcs, held = set(), 0, []
    for r in records:
        if r["id"] in seen:
            raise CensusError(f"{r['id']}: the same gate entered twice (plan + elevation are ONE gate, R-T361-2)")
        seen.add(r["id"])
        if r["gates_pcs"] is None:
            held.append(r["id"])
        else:
            pcs += r["gates_pcs"]
    return pcs, held


def boundary_line(line_id, drawn_length_m, solid_parts_m, gate_widths_m):
    """R-T361-2: solid + gates must close on the drawn line; returns the split. A gate is never solid fence."""
    L = _num(drawn_length_m, f"{line_id} drawn length")
    solid = sum(_num(v, f"{line_id} solid part") for v in solid_parts_m)
    gates = sum(_num(v, f"{line_id} gate") for v in gate_widths_m)
    if abs(solid + gates - L) > TOL_M:
        raise CensusError(f"{line_id}: solid {solid:.3f} + gates {gates:.3f} != drawn {L:.3f} (a gate counted as "
                          f"fence, or a part missing)")
    return {"id": line_id, "drawn_m": round(L, 3), "solid_m": round(solid, 3), "gates_m": round(gates, 3)}


def open_edge(edge_id, plan_length_m, guard, guard_ref=None, drop_m=None):
    """R-T361-3. guard in GUARD_STATES. DRAWN / WALL need the drawn reference; NONE_DRAWN keeps the length and gives
    no guard quantity (guard_lm None). A plan length must be drawn (None -> HELD row with length None)."""
    if guard not in GUARD_STATES:
        raise CensusError(f"{edge_id}: unknown guard state {guard!r}")
    if guard in ("DRAWN", "WALL") and not guard_ref:
        raise CensusError(f"{edge_id}: guard {guard} without the drawn reference (an invented guard)")
    if guard == "NONE_DRAWN" and guard_ref:
        raise CensusError(f"{edge_id}: NONE_DRAWN edge given a guard reference")
    length = None if plan_length_m is None else _num(plan_length_m, f"{edge_id} plan length")
    return {"id": edge_id, "plan_length_m": length, "guard": guard, "guard_ref": guard_ref, "drop_m": drop_m,
            "guard_lm": None if guard != "DRAWN" else "see the railing / parapet line (T-164 / T-162)",
            "finding": guard == "NONE_DRAWN"}


def posts_from_lines(xs_mm, pair_gap_mm=70.0):
    """R-T361-5: group the vertical lines of an elevation railing into posts (a post is drawn as two close lines).
    Input: x positions (mm) of the vertical lines under one top rail. Returns the post centres (mm), sorted. Single
    lines (no partner within pair_gap_mm) are NOT posts (they belong to something else: a dome, a parapet edge)."""
    xs = sorted(float(x) for x in xs_mm)
    groups, cur = [], []
    for x in xs:
        if cur and x - cur[-1] <= pair_gap_mm:
            cur.append(x)
        else:
            if cur:
                groups.append(cur)
            cur = [x]
    if cur:
        groups.append(cur)
    return [sum(g) / len(g) for g in groups if len(g) >= 2]


def glass_panels(drawn_glass_elements):
    """R-T361-5: m2 only from drawn / specified glass panels; none drawn -> NOT_DRAWN (never a default)."""
    if not drawn_glass_elements:
        return {"status": "NOT_DRAWN", "m2": None}
    total = 0.0
    for g in drawn_glass_elements:
        total += _num(g.get("width_m"), "glass width") * _num(g.get("height_m"), "glass height")
    return {"status": "DRAWN", "m2": round(total, 4)}


def cross_check_zero(element_ids_a, element_ids_b):
    """(d): the ids this census carries must not also be carried by another ledger (fence blockwork, B7-10)."""
    shared = sorted(set(element_ids_a) & set(element_ids_b))
    return {"shared": shared, "count": len(shared)}


def check():
    """Synthetic 'Villa F' (not the development villa): hand values. Returns PASS / FAIL lines."""
    out = []

    def ok(name, cond):
        out.append(("PASS " if cond else "FAIL ") + name)

    # street fence 12.00 m drawn = 8.50 solid + 3.50 sliding-gate gap (no leaf drawn) -> opening only
    b = boundary_line("VF-STREET", 12.00, [5.00, 3.50], [3.50])
    ok("boundary conserves 5.00 + 3.50 + 3.50 = 12.00", b["solid_m"] == 8.5 and b["gates_m"] == 3.5)
    g1 = gate_record("VF-G1", 3.50, {"PLAN_GAP", "ELEVATION_GAP"})
    ok("gap with no leaf = GATE_OPENING, pcs None", g1["kind"] == "GATE_OPENING" and g1["gates_pcs"] is None)
    # side gate 1.10 m, single leaf drawn on plan (swing) and elevation
    g2 = gate_record("VF-G2", 1.10, {"PLAN_LEAF", "ELEVATION_LEAF"}, leaf_count=1, leaf_size_m=(1.00, 2.10))
    ok("drawn leaf = GATE 1 pcs", g2["gates_pcs"] == 1 and g2["leaves_pcs"] == 1)
    pcs, held = gate_count([g1, g2])
    ok("gate count 1 pcs + 1 opening HELD", pcs == 1 and held == ["VF-G1"])
    # adverse
    for name, fn in [
        ("render-only gate refused", lambda: gate_record("X", 1.0, {"RENDER"})),
        ("assumed leaf count on a gap refused", lambda: gate_record("X", 3.5, {"PLAN_GAP"}, leaf_count=2)),
        ("gate entered twice refused", lambda: gate_count([g2, dict(g2)])),
        ("gate counted as solid fence refused", lambda: boundary_line("X", 12.0, [8.5, 3.5], [3.5])),
        ("invented guard refused", lambda: open_edge("X", 2.0, "DRAWN")),
        ("missing width refused (never 0)", lambda: gate_record("X", None, {"PLAN_GAP"})),
    ]:
        try:
            fn()
            ok(name, False)
        except CensusError:
            ok(name, True)
    e = open_edge("VF-E1", 1.20, "NONE_DRAWN", drop_m=(0.0, 0.85))
    ok("undrawn guard edge keeps 1.20 m, no guard lm", e["guard_lm"] is None and e["finding"])
    ok("posts: 3 pairs + 1 single -> 3 posts", len(posts_from_lines([0, 36, 1000, 1036, 1500, 2000, 2036])) == 3)
    ok("glass not drawn -> NOT_DRAWN, m2 None", glass_panels([]) == {"status": "NOT_DRAWN", "m2": None})
    ok("cross-check 0", cross_check_zero(["G1"], ["W1"])["count"] == 0)
    return out


if __name__ == "__main__":
    for line in check():
        print(line)
