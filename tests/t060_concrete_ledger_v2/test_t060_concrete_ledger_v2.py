"""T-060: CONCRETE_LEDGER_V2 - the frozen route-G concrete ledger with its strips re-measured by the strip guard and the
curved-strip pairing (engine.source.concrete_ledger_v2). Synthetic plots, not a client drawing. Hand truth worked on
paper from the drawn faces, never from engine output:

RING (a closed boundary-wall band, plot 20.00 x 10.00 m, band 0.20 m inside the plot line)
  outer faces = the plot line, inner faces offset 0.20 m.
  centre line = (20 - 0.20) x 2 + (10 - 0.20) x 2 = 59.20 m; plan = 59.20 x 0.20 = 11.84 m2
  (check 20 x 10 - 19.60 x 9.60 = 11.84 m2).
  Footings cast against the plot line on TWO sides: south A (4.25, 0)-(5.75, 1.50), south B (12.00, 0)-(13.50, 1.50),
  east C (18.50, 4.00)-(20.00, 5.50); corner column NW (0, 9.70)-(0.30, 10.00).
    centre line inside members: south y = 0.10 through A and B: 1.50 + 1.50; east x = 19.90 through C (y 4.00-5.50):
    1.50; NW column: west x = 0.10 from y 9.70 to the corner 9.90 = 0.20, north y = 9.90 from x 0.10 to 0.30 = 0.20.
    held under members = 3.00 + 1.50 + 0.40 = 4.90 m (0.98 m2); the rest 59.20 - 4.90 = 54.30 m (10.86 m2).
  The frozen ledger removed the south plot line (EXPLAINED_BY_MEMBER) before pairing: the frozen strip is the paired
  overlap of the kept sides north 19.60 + east 9.60 + west 9.60 = 38.80 m (south side lost, 3 x 0.20 corner basis).
  Owner Q-12 (no member type identified): 54.30 m / 10.86 m2 HELD MEMBER_TYPE_PENDING, 4.90 m / 0.98 m2 HELD
  STRIP_UNDER_MEMBER, no volume. With a member type and the schedule row 20 x 60: 10.86 x 0.60 = 6.516 m3 measured.
  Face conservation: 2 x 20 + 2 x 10 + 2 x 19.60 + 2 x 9.60 = 118.40 m of faces, every metre in one record.

D-SHAPED POOL (straight side on y = 0, half circle on the far side, centre (0, 1.50))
  outer: line (-2, 0)-(2, 0), sides x = +-2 from y 0 to 1.50, arc r 2.00 from 0 to 180 deg;
  inner: line (-1.8, 0.2)-(1.8, 0.2), sides x = +-1.8 from 0.2 to 1.50, arc r 1.80.
  outer area = 4.00 x 1.50 + pi / 2 x 2.00^2 = 6.00 + 6.283185 = 12.283185 m2
  inner area = 3.60 x 1.30 + pi / 2 x 1.80^2 = 4.68 + 5.089380 = 9.769380 m2  -> ring 2.513805 m2
  strips: straight centre line 3.80 (long side, corners joined) + 1.40 + 1.40 = 6.60 m x 0.20 = 1.32 m2;
          curved pi / 2 x (2.00^2 - 1.80^2) = 1.193805 m2 on a centre line 1.90 x pi = 5.969026 m
  wall plan = 1.32 + 1.193805 = 2.513805 m2 = the ring (the frozen pass keeps the straight half only).
  printed "H=1.20" and "FLOOR 400 MM" beside it: walls 2.513805 x 1.20 = 3.016566 m3, floor 12.283185 x 0.40 =
  4.913274 m3. No printed note: walls and floor HELD (owner Q-19: no usual size), areas kept.

Every case runs in metres and in millimetres, mirrored and rotated 37 degrees: lengths and areas do not change.
"""

from __future__ import annotations

import json
import math
import tempfile
from pathlib import Path

import pytest

from engine.source import concrete_ledger_v2 as V2
from engine.source import provisional_estimate as PE

ROOT = Path(__file__).resolve().parents[2]
FID = "CC-band0001"
PID = "CC-pool0001"
ROW = {"FINDING_ID": "CC-row00001", "KIND": "SCHEDULE_ROW_UNREAD", "FAMILY": "BOUNDARY_WALL", "SHEET": "SH02",
       "MAGNITUDE": {"sizes": (20.0, 60.0)}}
MT = {FID: {"member_type": "BOUNDARY_WALL_FOOTING", "evidence": "boundary-wall detail sheet, base B.W 20 x 60"}}

TRANSFORMS = {
    "m": (1.0, False, 0.0),
    "mm": (1000.0, False, 0.0),
    "mirror_mm": (1000.0, True, 0.0),
    "rot37_m": (1.0, False, 37.0),
    "mirror_rot37_mm": (1000.0, True, 37.0),
}


def _tf(scale, mirror, deg):
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))

    def f(p):
        x, y = p[0] * scale, p[1] * scale
        if mirror:
            x = -x
        return (x * c - y * s + 5000.0 * scale, x * s + y * c - 3000.0 * scale)
    return f


def _line(eid, a, b, layer, state="UNEXPLAINED"):
    pts = [(a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t) for t in (0, .25, .5, .75, 1)]
    return {"eid": eid, "type": "LINE", "layer": layer, "a": a, "b": b, "pts": pts, "len": math.dist(a, b),
            "box": (min(a[0], b[0]), min(a[1], b[1]), max(a[0], b[0]), max(a[1], b[1])), "state": state}


def _arc(eid, c, r, a0, a1, layer, T, scale, state="UNEXPLAINED"):
    """an arc drawn counter-clockwise from a0 to a1 (deg) in the fixture frame, transformed point by point."""
    pt = lambda a: (c[0] + r * math.cos(math.radians(a)), c[1] + r * math.sin(math.radians(a)))   # noqa: E731
    s, m, e = T(pt(a0)), T(pt((a0 + a1) / 2)), T(pt(a1))
    pts = [s, m, e]
    return {"eid": eid, "type": "ARC", "layer": layer, "c": T(c), "r": r * scale, "pts": pts,
            "len": r * scale * math.radians(a1 - a0),
            "box": (min(x for x, _ in pts), min(y for _, y in pts), max(x for x, _ in pts), max(y for _, y in pts))}


def _box_m(ents, unit):
    xs = [x for e in ents for x, _ in e["pts"]]
    ys = [y for e in ents for _, y in e["pts"]]
    return [min(xs) * unit, min(ys) * unit, max(xs) * unit, max(ys) * unit]


def _frozen_item(fid, fam, part, base, storey="FOUNDATION"):
    cid = f"SCOPE:{fam}:{storey}:{fid}:{part}"
    return PE.item(item_id=f"P-C:{cid}", component_id=cid, trade="CONCRETE", family=fam, storey=storey,
                   category="PROVISIONAL", low=base, base=base, high=base, formula="frozen", assumptions=["X"],
                   support="CONVENTION_ONLY", confidence="LOW", source="fixture", part=part)


def _route(ents, group, findings, items, unit, footings=(), columns=(), texts=()):
    D = {"unit_m": unit, "model": {"texts": list(texts)},
         "sheets": {"SH01": {"sheet": {"sheet_id": "SH01", "role": "FOUNDATION_PLAN", "storey": "FOUNDATION",
                                       "origin": (0.0, 0.0)},
                             "footings": list(footings), "columns": list(columns)}}}
    CR = {"params": {"_ents": {"SH01": ents}, "_group_eids": group}, "findings": findings}
    other = PE.item(item_id="P-C:OTHER", component_id="OTHER", trade="CONCRETE", family="SLABS", storey="GF",
                    category="PROVISIONAL", low=1.0, base=1.0, high=1.0, formula="x", assumptions=["X"],
                    support="CONVENTION_ONLY", confidence="LOW", source="fixture")
    return {"generic": {"completeness": CR, "D": D}, "items": [other] + list(items), "conv": None, "inputs": []}


def ring_route(key, *, footings=True, column=True, drop_inner_south=False, remove_south=True, plot_layer="WALL-B"):
    scale, mirror, deg = TRANSFORMS[key]
    T = _tf(scale, mirror, deg)
    unit = 1.0 / scale
    outer = [(0, 0), (20, 0), (20, 10), (0, 10)]
    inner = [(0.2, 0.2), (19.8, 0.2), (19.8, 9.8), (0.2, 9.8)]
    ents, group = [], []
    for name, ring in (("o", outer), ("i", inner)):
        for k in range(4):
            if name == "i" and k == 0 and drop_inner_south:
                continue
            eid = f"L:{name}{k}"
            removed = name == "o" and k == 0 and remove_south
            ents.append(_line(eid, T(ring[k]), T(ring[(k + 1) % 4]), plot_layer,
                              state="EXPLAINED_BY_MEMBER" if removed else "UNEXPLAINED"))
            if not removed:
                group.append(eid)
    fts = []
    if footings:
        for k, (x0, y0, x1, y1) in enumerate(((4.25, 0, 5.75, 1.5), (12.0, 0, 13.5, 1.5), (18.5, 4.0, 20.0, 5.5))):
            fts.append({"member_id": f"FTG:{k}", "polygon": [T(p) for p in ((x0, y0), (x1, y0), (x1, y1), (x0, y1))],
                        "mark": "F1", "state": "CONFIRMED"})
        # a schedule-sized footprint round a mark is not drawn: never used to split the band
        fts.append({"member_id": "FTG:approx", "mark_at": T((10.0, 9.9)), "schedule_m": (1.5, 1.5), "mark": "F2"})
    if column:          # drawn as a footprint polygon, so that it can be mirrored and rotated with the plot
        fts.append({"member_id": "COL:NW", "polygon": [T(p) for p in ((0, 9.7), (0.3, 9.7), (0.3, 10), (0, 10))],
                    "mark": "C1", "state": "CONFIRMED"})
    f = {"FINDING_ID": FID, "KIND": "DRAWN_NOT_MEASURED", "FAMILY": "BOUNDARY_WALL", "SHEET": "SH01",
         "STOREY": "FOUNDATION", "BOX_M": _box_m([e for e in ents if e["eid"] in group], unit),
         "MAGNITUDE": {"strip_width_m": 0.2, "strip_length_m": 38.8}, "SCOPE_STATE": "MEASURED",
         "SCOPE_ITEMS": f"P-C:SCOPE:BOUNDARY_WALL:FOUNDATION:{FID}:BEAM"}
    frozen = _frozen_item(FID, "BOUNDARY_WALL", "BEAM", 38.8 * 0.2 * 0.6)
    return _route(ents, {FID: group}, [f, ROW], [frozen], unit, footings=fts)


def pool_route(key, *, notes=(), inner_arc=True, layer="S-POOL-SHELL"):
    scale, mirror, deg = TRANSFORMS[key]
    T = _tf(scale, mirror, deg)
    unit = 1.0 / scale
    ents = [_line("P:o0", T((-2, 0)), T((2, 0)), layer), _line("P:o1", T((2, 0)), T((2, 1.5)), layer),
            _line("P:o3", T((-2, 1.5)), T((-2, 0)), layer),
            _line("P:i0", T((-1.8, 0.2)), T((1.8, 0.2)), layer), _line("P:i1", T((1.8, 0.2)), T((1.8, 1.5)), layer),
            _line("P:i3", T((-1.8, 1.5)), T((-1.8, 0.2)), layer)]
    # mirroring reverses the turning direction: the arc is then drawn from the other end (still counter-clockwise)
    ents.append(_arc("P:o2", (0, 1.5), 2.0, 0, 180, layer, T, scale))
    if inner_arc:
        ents.append(_arc("P:i2", (0, 1.5), 1.8, 0, 180, layer, T, scale))
    if mirror:
        for e in ents:
            if e["type"] == "ARC":
                e["pts"] = [e["pts"][2], e["pts"][1], e["pts"][0]]
    texts = [{"sheet": "SH01", "x": T((0, -0.5))[0], "y": T((0, -0.5))[1], "norm": n} for n in notes]
    f = {"FINDING_ID": PID, "KIND": "DRAWN_NOT_MEASURED", "FAMILY": "POOL", "SHEET": "SH01", "STOREY": "GROUND",
         "BOX_M": _box_m(ents, unit), "MAGNITUDE": {"strip_width_m": 0.2, "strip_length_m": 6.2},
         "SCOPE_STATE": "MEASURED",
         "SCOPE_ITEMS": f"P-C:SCOPE:POOL:GROUND:{PID}:WALLS,P-C:SCOPE:POOL:GROUND:{PID}:FLOOR"}
    frozen = [_frozen_item(PID, "POOL", "WALLS", 1.984, "GROUND"), _frozen_item(PID, "POOL", "FLOOR", 1.511, "GROUND")]
    return _route(ents, {PID: [e["eid"] for e in ents]}, [f], frozen, unit, texts=texts)


def _rec(v, reason):
    return [r for f in v["findings"] for r in f["records"] if r.get("reason") == reason or
            (reason == "MEASURED" and r["status"] == "MEASURED")]


# ====================================================================== ring: footings on two sides
@pytest.mark.parametrize("key", list(TRANSFORMS))
def test_ring_every_face_kept_and_held_without_member_type(key):
    R = ring_route(key)
    v = V2.measure(R)
    assert v["supersedes"] == [f"P-C:SCOPE:BOUNDARY_WALL:FOUNDATION:{FID}:BEAM"]
    (pend,) = _rec(v, "MEMBER_TYPE_PENDING")
    (under,) = _rec(v, "STRIP_UNDER_MEMBER")
    assert pend["strip_length_m"] == pytest.approx(54.30, abs=1e-6)
    assert pend["area_m2"] == pytest.approx(10.86, abs=1e-6)
    assert under["strip_length_m"] == pytest.approx(4.90, abs=1e-6)
    assert under["area_m2"] == pytest.approx(0.98, abs=1e-6)
    assert "FTG:approx" not in under["members"]
    assert pend["rings"][0]["centre_line_m"] == pytest.approx(59.20, abs=1e-6)
    assert pend["rings"][0]["area_m2"] == pytest.approx(11.84, abs=1e-6)
    assert not _rec(v, "STRIP_FACE_UNPAIRED") and not _rec(v, "MEASURED")
    # the removed south plot line is recovered; the frozen basis is reproduced in the record
    (cen,) = [c for c in v["census"] if c["finding"] == FID]
    assert cen["removed_faces_recovered"] == ["L:o0"]
    assert cen["approx_members_not_used"] == ["FTG:approx"]
    assert pend["frozen_view"]["kept_overlap_length_m"] == pytest.approx(38.80, abs=1e-6)
    assert {o["id"] for o in pend["frozen_omissions"]} == {"L:o0", "L:i0"}
    c = pend["conservation"]
    assert c["face_length_m"] == pytest.approx(118.40, abs=1e-6) and abs(c["difference_m"]) < 1e-5
    # no volume anywhere, never 0: every v2 item is UNRESOLVED with its blocker
    for it in v["items"]:
        assert it["category"] == "UNRESOLVED" and it["base"] is None and it["blocker"]


@pytest.mark.parametrize("key", ["m", "mirror_rot37_mm"])
def test_ring_released_only_for_an_identified_member_type_with_the_schedule_depth(key):
    v = V2.measure(ring_route(key), member_types=MT)
    (m,) = _rec(v, "MEASURED")
    assert m["volume_m3"] == pytest.approx(10.86 * 0.60, abs=1e-6)
    assert m["section_depth_m"] == pytest.approx(0.60) and m["member_type"] == "BOUNDARY_WALL_FOOTING"
    (under,) = _rec(v, "STRIP_UNDER_MEMBER")                       # still held: may already be in the footing
    assert under["area_m2"] == pytest.approx(0.98, abs=1e-6)
    meas = [i for i in v["items"] if i["category"] == "PROVISIONAL"]
    assert len(meas) == 1 and meas[0]["base"] == pytest.approx(6.516, abs=1e-6)


def test_member_type_without_any_depth_source_stays_area_only():
    R = ring_route("m")
    R["generic"]["completeness"]["findings"] = [f for f in R["generic"]["completeness"]["findings"]
                                                if f["KIND"] != "SCHEDULE_ROW_UNREAD"]
    v = V2.measure(R, member_types=MT)
    (h,) = _rec(v, "SECTION_DEPTH_NOT_PRINTED")
    assert h["area_m2"] == pytest.approx(10.86, abs=1e-6) and "volume_m3" not in h
    assert all(i["base"] is None for i in v["items"])


def test_member_type_needs_a_known_type_and_its_evidence():
    with pytest.raises(V2.LedgerError):
        V2.measure(ring_route("m"), member_types={FID: {"member_type": "BOUNDARY_WALL_FOOTING"}})
    with pytest.raises(V2.LedgerError):
        V2.measure(ring_route("m"), member_types={FID: {"member_type": "GUESS", "evidence": "x"}})


@pytest.mark.parametrize("key", ["m", "rot37_m"])
def test_ring_without_members_is_the_exact_ring(key):
    v = V2.measure(ring_route(key, footings=False, column=False))
    (pend,) = _rec(v, "MEMBER_TYPE_PENDING")
    assert pend["strip_length_m"] == pytest.approx(59.20, abs=1e-6)
    assert pend["area_m2"] == pytest.approx(11.84, abs=1e-6)
    assert not _rec(v, "STRIP_UNDER_MEMBER")


@pytest.mark.parametrize("key", ["m", "mirror_mm"])
def test_a_missing_inner_face_is_held_never_lost(key):
    """south inner face not drawn: north 19.80 + east / west 9.70 each = 39.20 m in strips; the south plot line
    (20.00 m) and the outer east / west stubs below the inner face end (0.20 m each) HELD unpaired = 20.40 m."""
    v = V2.measure(ring_route(key, footings=False, column=False, drop_inner_south=True))
    (pend,) = _rec(v, "MEMBER_TYPE_PENDING")
    (unp,) = _rec(v, "STRIP_FACE_UNPAIRED")
    assert pend["strip_length_m"] == pytest.approx(39.20, abs=1e-6)
    assert unp["face_length_m"] == pytest.approx(20.40, abs=1e-6)
    assert "L:o0" in unp["faces"]
    assert abs(pend["conservation"]["difference_m"]) < 1e-5


def test_apply_replaces_only_the_superseded_items():
    R = ring_route("m")
    v = V2.measure(R)
    out = V2.apply(R, v)
    ids = [i["item_id"] for i in out]
    assert "P-C:OTHER" in ids and f"P-C:SCOPE:BOUNDARY_WALL:FOUNDATION:{FID}:BEAM" not in ids
    assert sum(1 for i in ids if i.startswith(f"P-C:V2:BOUNDARY_WALL:FOUNDATION:{FID}:")) == 2
    assert next(i for i in out if i["item_id"] == "P-C:OTHER") is R["items"][0]          # untouched
    PE.check(out)


# ====================================================================== D-shaped pool
@pytest.mark.parametrize("key", list(TRANSFORMS))
def test_d_pool_wall_plan_counts_the_curved_half(key):
    v = V2.measure(pool_route(key))
    walls = next(r for r in v["findings"][0]["records"] if r["part"] == "WALLS")
    assert walls["straight_strip_m2"] == pytest.approx(1.32, abs=1e-6)
    assert walls["curved_strip_m2"] == pytest.approx(math.pi / 2 * (4.0 - 3.24), abs=1e-6)
    assert walls["wall_plan_m2"] == pytest.approx(2.513805, abs=1e-6)
    assert walls["outer_m2"] == pytest.approx(6.0 + 2 * math.pi, abs=1e-6)
    rc = walls["ring_check"]
    assert rc["inner_m2"] == pytest.approx(4.68 + math.pi / 2 * 3.24, abs=1e-6) and abs(rc["difference_m2"]) < 1e-5
    c = walls["conservation"]
    assert c["face_length_m"] == pytest.approx(13.2, abs=1e-6) and abs(c["difference_m"]) < 1e-5
    assert c["arc_length_m"] == pytest.approx(3.8 * math.pi, abs=1e-6) and abs(c["arc_difference_m"]) < 1e-5
    # no printed depth / floor: held with the areas, never a convention size, never 0 (owner Q-19)
    assert {r["reason"] for r in v["findings"][0]["records"]} == {"POOL_WALL_HEIGHT_NOT_PRINTED",
                                                                    "POOL_FLOOR_THICKNESS_NOT_PRINTED_NEAR"}
    assert all(i["category"] == "UNRESOLVED" and i["base"] is None for i in v["items"])
    cen = next(c for c in v["census"] if c["finding"] == PID)
    assert cen["v2_centre_line_m"] == pytest.approx(6.6 + 1.9 * math.pi, abs=1e-6)


@pytest.mark.parametrize("key", ["m", "mm", "mirror_rot37_mm"])
def test_d_pool_released_from_printed_notes(key):
    v = V2.measure(pool_route(key, notes=("H=1.20", "FLOOR 400 MM")))
    vol = {i["part"]: i["base"] for i in v["items"]}
    assert vol["WALLS"] == pytest.approx(2.513805 * 1.20, abs=1e-5)
    assert vol["FLOOR"] == pytest.approx((6.0 + 2 * math.pi) * 0.40, abs=1e-5)


def test_d_pool_two_disagreeing_heights_are_held():
    v = V2.measure(pool_route("m", notes=("H=1.20", "H=1.50")))
    walls = next(r for r in v["findings"][0]["records"] if r["part"] == "WALLS")
    assert walls["status"] == "HELD" and walls["reason"] == "PRINTED_HEIGHTS_DISAGREE"


@pytest.mark.parametrize("key", ["m", "mirror_mm"])
def test_d_pool_missing_inner_arc_is_held_not_dropped(key):
    v = V2.measure(pool_route(key, notes=("H=1.20", "FLOOR 400 MM")))
    v_missing = V2.measure(pool_route(key, notes=("H=1.20",), inner_arc=False))
    walls = next(r for r in v_missing["findings"][0]["records"] if r["part"] == "WALLS")
    held = [h for h in walls["held_faces"] if h["reason"] == "CURVED_STRIP_UNPAIRED"]
    assert len(held) == 1 and held[0]["length_m"] == pytest.approx(2.0 * math.pi, abs=1e-6)
    assert walls["wall_plan_m2"] == pytest.approx(1.32, abs=1e-6) and walls["ring_check"] is None
    assert abs(walls["conservation"]["arc_difference_m"]) < 1e-5
    # the outer loop still closes: the floor area is the full D, floor thickness not printed -> held
    floor = next(r for r in v_missing["findings"][0]["records"] if r["part"] == "FLOOR")
    assert floor["status"] == "HELD" and floor["outer_m2"] == pytest.approx(6.0 + 2 * math.pi, abs=1e-6)
    assert v["items"][0]["base"] > 0


def test_loop_areas_exact_for_a_full_circle_of_two_arcs():
    T = _tf(1.0, False, 0.0)
    a1 = _arc("a1", (0, 0), 3.0, 0, 180, "X", T, 1.0)
    a2 = _arc("a2", (0, 0), 3.0, 180, 360, "X", T, 1.0)
    curves = [{"type": "ARC", "id": a["eid"], "c": a["c"], "r": a["r"], "s": a["pts"][0], "m": a["pts"][1],
               "e": a["pts"][2]} for a in (a1, a2)]
    (area, _), = V2.loop_areas([], curves, 1.0)
    assert area == pytest.approx(math.pi * 9.0, abs=1e-6)


def test_unknown_family_keeps_its_frozen_items():
    R = ring_route("m")
    f = R["generic"]["completeness"]["findings"][0]
    f["FAMILY"] = "SLAB_STEP"
    v = V2.measure(R)
    assert v["supersedes"] == [] and v["items"] == []
    assert V2.apply(R, v) == R["items"]


def test_missing_route_records_are_refused():
    with pytest.raises(V2.LedgerError):
        V2.measure({"generic": {}, "items": []})


# ====================================================================== whole route on synthetic villas (not Alsenan)
ezdxf = pytest.importorskip("ezdxf")
V6 = str(ROOT / "engine/profiles/URBAN_M8_GENERIC_CONVENTIONS_V6.json")


@pytest.mark.parametrize("seed", [1, 6, 9, 35])
def test_synthetic_villa_route_g(seed):
    """seed 1, 9, 35: printed pool notes -> v2 equals the frozen pool and the generator truth (to its rounding);
    seed 6: no printed note -> held with the drawn ring area (the frozen pass used convention sizes). The plot-line
    boundary-wall strips keep every face (conservation) and are re-measured on the centre line."""
    from tools import synthetic_villa_m8 as SM8
    from tools import urban_boq_m2 as CLI
    with tempfile.TemporaryDirectory() as td:
        dxf = SM8.generate(td, seed)
        R = CLI.compute([str(dxf)], profile=f"{td}/villa_m8_{seed}.profile.json", route="G", conventions=V6,
                        completeness=True)
        T = json.loads(Path(f"{td}/villa_m8_{seed}.truth.json").read_text(encoding="utf-8"))
    v = V2.measure(R)
    for c in v["census"]:
        assert abs(c["conservation"]["difference_m"]) < 1e-5 and abs(c["conservation"]["arc_difference_m"]) < 1e-5
    out = V2.apply(R, v)
    PE.check(out, R["conv"])
    pool = [e for e in T["m8"]["elements"] if e["kind"] == "POOL"]
    v2_pool = [i for i in v["items"] if i["family"] == "POOL"]
    if pool and v2_pool:
        p = pool[0]
        walls = next(i for i in v2_pool if i["part"] == "WALLS")
        frozen = sum(i["base"] for i in R["items"] if i["family"] == "POOL")
        if p.get("printed"):
            total = sum(i["base"] for i in v2_pool)
            assert total == pytest.approx(frozen, abs=1e-4)
            assert total == pytest.approx(p["truth_m3"], rel=2e-3)
        else:
            assert all(i["category"] == "UNRESOLVED" for i in v2_pool)
            assert walls["dimensions"]["wall_plan_m2"] > 0
    for it in v["items"]:
        assert it["base"] is None or it["base"] > 0
