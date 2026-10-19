"""T-078: door and window areas from the plan width and a PRINTED elevation height (engine/source/opening_area.py),
against hand truth. Hand villa SV-T078 (not a client drawing), two storeys, plan in metres:

    East facade (wall along the plan y axis, x = 12): GF W1 centre y 2.0, 1.20 wide; GF W2 centre y 6.5, 2.40 wide;
        1F W3 centre y 2.0, 1.20 wide (over W1); 1F W4 centre y 6.0, 1.80 wide, arched head.
    West facade (x = 0): GF door D1 centre y 4.5, 1.00 wide, outdoor aluminium; 1F W5 centre y 7.0, 0.60 wide.
    North facade (wall along x): GF W6 centre x 6.0, 1.50 wide: no elevation of that face is drawn.
    Inside: GF door D2 0.90 (a space on both sides); GF passage P1 1.40.

EAST elevation, drawn in MILLIMETRES, seen from +x (x_view = y + 50 m, not mirrored), dimensions printed in
centimetres (DIMLFAC 0.1), GF floor line at Y = 10000, 1F floor line at Y = 14200:
    W1 jambs x 51400 / 52600, foot 10900, top 12900; printed "90" (10000-10900) and "200" (10900-12900)
    W3 jambs x 51400 / 52600, foot 15200, top 16700; printed "150" (15200-16700)
    a surround pair x 51400 / 52600 from 10900 to 16700 (one line over both storeys: not an opening)
    W2 jambs x 55300 / 57700, foot 10000, top 12603; printed "260" (10000-12603: 2603 mm rounds to 260 cm)
    W4 jambs x 55100 / 56900, foot 15200, top 16400 (springing); arch drawn as chords up to the crown Y 16900;
       printed "120" (15200-16400) and "50" (16400-16900): to the top of the arch (owner Q-32 = A)
    printed widths on the 1F row: "120" over W3 and "180" over W4 (two places: the view is mapped)
WEST elevation, drawn in METRES, seen from -x (x_view = -y + 30 m, MIRRORED), printed in centimetres (DIMLFAC 100),
GF floor line Y = 0, 1F floor line Y = 4.2:
    D1 jambs x 25.0 / 26.0, foot 0, top 2.5; printed "250"
    W5 jambs x 22.7 / 23.3, foot 5.8, top 6.4; printed "60"; printed widths "100" over D1 and "60" over W5

Hand areas (width x printed height, m2):
    W1 1.20 x 2.00 = 2.400    W3 1.20 x 1.50 = 1.800    W2 2.40 x 2.60 = 6.240
    W4 1.80 x (1.20 + 0.50) = 1.80 x 1.70 = 3.060      W5 0.60 x 0.60 = 0.360
    windows 2.400 + 1.800 + 6.240 + 3.060 + 0.360 = 13.860 (aluminium, owner Q-33 = A)
    D1 1.00 x 2.50 = 2.500 (AS_DRAWN, outdoor aluminium door)
    W6 HELD (no elevation of its face), D2 HELD (interior), P1 EXCLUDED; no area of 0 anywhere.
Variants: plan rotated 30 degrees, plan mirrored, both; adversarial: stale print, width conflict, one width only (no
mapping), arch top not printed, a missing storey jamb pair, front and back windows on one range, schedule height
over the elevation, curved-on-plan window with and without the owner's basis, no dimensions at all, missing width.
"""

from __future__ import annotations

import copy
import math
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engine.source import opening_area as OA  # noqa: E402

FLOORS = ["GF", "1F"]


def _dim(h, p2, p3, shown, *, angle=90.0, text=""):
    return {"handle": h, "type": "LINEAR", "p2": list(p2), "p3": list(p3), "angle": angle, "style_dimlfac": None,
            "override_dimlfac": None, "measurement": None, "text": text, "shown_text": shown}


def _jambs(x0, x1, foot, top, tag):
    return [(x0, foot, x0, top, f"{tag}L"), (x1, foot, x1, top, f"{tag}R"),
            (x0, foot, x1, foot, f"{tag}S"), (x0, top, x1, top, f"{tag}H")]


def east_view():
    seg = []
    seg += _jambs(51400, 52600, 10900, 12900, "W1")
    seg += _jambs(51400, 52600, 15200, 16700, "W3")
    seg += [(51400, 10900, 51400, 16700, "SURL"), (52600, 10900, 52600, 16700, "SURR")]
    seg += _jambs(55300, 57700, 10000, 12603, "W2")
    seg += [(55100, 15200, 55100, 16400, "W4L"), (56900, 15200, 56900, 16400, "W4R"),
            (55100, 15200, 56900, 15200, "W4S")]
    arch = [(55100 + 900 - 900 * math.cos(math.radians(a)), 16400 + 500 * math.sin(math.radians(a)))
            for a in range(0, 181, 15)]
    seg += [(a[0], a[1], b[0], b[1], f"W4A{i}") for i, (a, b) in enumerate(zip(arch, arch[1:]))]
    dims = [
        _dim("e1", (51800, 10000), (51800, 10900), "90"),
        _dim("e2", (51800, 10900), (51700, 12900), "200"),
        _dim("e3", (51900, 15200), (51900, 16700), "150"),
        _dim("e4", (56000, 10000), (56500, 12603), "260"),
        _dim("e5", (55600, 15200), (55600, 16400), "120"),
        _dim("e6", (55600, 16400), (56000, 16900), "50"),
        _dim("w3", (51400, 16000), (52600, 16000), "120", angle=0.0),
        _dim("w4", (55100, 16000), (56900, 16000), "180", angle=0.0),
    ]
    return {"view_id": "EAST", "unit_m": 0.001, "header_dimlfac": 0.1, "dims": dims, "segments": seg}


def west_view():
    seg = _jambs(25.0, 26.0, 0.0, 2.5, "D1") + _jambs(22.7, 23.3, 5.8, 6.4, "W5")
    dims = [_dim("d1", (25.5, 0.0), (25.5, 2.5), "250"), _dim("d5", (23.0, 5.8), (23.0, 6.4), "60"),
            _dim("wd", (25.0, 1.0), (26.0, 1.0), "100", angle=0.0),
            _dim("ww", (22.7, 6.0), (23.3, 6.0), "60", angle=0.0)]
    return {"view_id": "WEST", "unit_m": 1.0, "header_dimlfac": 100.0, "dims": dims, "segments": seg}


def plan():
    Y = (0.0, 1.0)
    X = (1.0, 0.0)
    return [
        {"id": "W1", "floor": "GF", "kind": "WINDOW", "xy": (12.0, 2.0), "axis": Y, "width_m": 1.20},
        {"id": "W2", "floor": "GF", "kind": "WINDOW", "xy": (12.0, 6.5), "axis": Y, "width_m": 2.40},
        {"id": "W3", "floor": "1F", "kind": "WINDOW", "xy": (12.0, 2.0), "axis": Y, "width_m": 1.20},
        {"id": "W4", "floor": "1F", "kind": "WINDOW", "xy": (12.0, 6.0), "axis": Y, "width_m": 1.80},
        {"id": "D1", "floor": "GF", "kind": "DOOR", "xy": (0.0, 4.5), "axis": Y, "width_m": 1.00,
         "door_class": "DOOR.EXTERNAL.ALUMINIUM", "faces_outside": True},
        {"id": "W5", "floor": "1F", "kind": "WINDOW", "xy": (0.0, 7.0), "axis": Y, "width_m": 0.60},
        {"id": "W6", "floor": "GF", "kind": "WINDOW", "xy": (6.0, 9.0), "axis": X, "width_m": 1.50},
        {"id": "D2", "floor": "GF", "kind": "DOOR", "xy": (6.0, 4.0), "axis": X, "width_m": 0.90,
         "door_class": "DOOR.INTERNAL.PVC", "faces_outside": False},
        {"id": "P1", "floor": "GF", "kind": "PASSAGE", "xy": (3.0, 3.0), "axis": X, "width_m": 1.40},
    ]


HAND = {"W1": (1.20, 2.00, 2.400), "W3": (1.20, 1.50, 1.800), "W2": (2.40, 2.60, 6.240),
        "W4": (1.80, 1.70, 3.060), "W5": (0.60, 0.60, 0.360), "D1": (1.00, 2.50, 2.500)}


def run(ops=None, views=None, **kw):
    res = OA.measure(plan() if ops is None else ops, [east_view(), west_view()] if views is None else views,
                     floors=FLOORS, **kw)
    return res, {r["id"]: r for r in res["records"]}


def _transform(ops, rot_deg=0.0, mirror=False):
    out = copy.deepcopy(ops)
    c, s = math.cos(math.radians(rot_deg)), math.sin(math.radians(rot_deg))
    for p in out:
        x, y = p["xy"]
        ax, ay = p["axis"]
        if mirror:
            y, ay = -y, -ay
        p["xy"] = (c * x - s * y + 100.0, s * x + c * y - 40.0)
        p["axis"] = (c * ax - s * ay, s * ax + c * ay)
    return out


def _check_hand(rec):
    for k, (w, h, a) in HAND.items():
        r = rec[k]
        assert r["status"] == "MEASURED", (k, r["reason"], r["evidence"])
        assert r["width_m"] == pytest.approx(w, abs=1e-9)
        assert r["height_m"] == pytest.approx(h, abs=1e-9)
        assert r["area_m2"] == pytest.approx(a, abs=5e-4)
    assert rec["W6"]["status"] == "HELD" and rec["W6"]["reason"] == "NO_ELEVATION_OF_THIS_FACE"
    assert rec["D2"]["status"] == "HELD" and rec["D2"]["reason"] == "INTERIOR_OPENING"
    assert rec["P1"]["status"] == "EXCLUDED"
    for r in rec.values():
        if r["status"] != "MEASURED":
            assert r["area_m2"] is None                       # never 0


def test_hand_villa():
    res, rec = run()
    _check_hand(rec)
    assert rec["W4"]["evidence"]["shape"] == "ARCHED" and rec["W4"]["evidence"]["parts_m"] == [1.2, 0.5]
    assert rec["W1"]["evidence"]["shape"] == "RECTANGULAR"
    assert res["summary"]["measured_m2"] == {"WINDOW:ALUMINIUM": pytest.approx(13.860, abs=5e-4),
                                             "DOOR:ALUMINIUM": pytest.approx(2.500, abs=5e-4)}
    m = {v["view_id"]: v["mapping"] for v in res["views"]}
    assert m["EAST"]["state"] == "MAPPED" and m["EAST"]["s"] == 1 and m["EAST"]["c_m"] == pytest.approx(50.0, abs=1e-6)
    assert m["WEST"]["state"] == "MAPPED" and m["WEST"]["mirrored"] and m["WEST"]["c_m"] == pytest.approx(30.0)
    assert rec["W1"]["material"] == "ALUMINIUM" and "Q33" in rec["W1"]["source"]
    assert rec["D1"]["view"] == "AS_DRAWN"
    assert len(res["records"]) == len(plan())                 # every opening reported once


@pytest.mark.parametrize("rot,mirror", [(30.0, False), (0.0, True), (30.0, True), (-123.0, False)])
def test_rotated_and_mirrored_plans(rot, mirror):
    res, rec = run(_transform(plan(), rot, mirror))
    _check_hand(rec)


def test_a_rounded_print_is_used_a_stale_print_is_not():
    p = OA.printed(_dim("x", (0, 0), (0, 2603), "260"), 0.1, 0.001)
    assert p["usable"] and p["value_m"] == pytest.approx(2.60)
    q = OA.printed(_dim("y", (0, 0), (0, 2620), "260"), 0.1, 0.001)      # 20 mm off: more than half a cm
    assert not q["usable"] and q["why_not"].startswith("STALE")
    o = OA.printed(_dim("z", (0, 0), (0, 2400), "", text="250"), 0.1, 0.001)  # text override disagreeing
    assert not o["usable"]
    d = OA.printed(_dim("d", (0, 0), (0, 2.345), "234.5"), 100.0, 1.0)      # a printed decimal, metres
    assert d["usable"] and d["value_m"] == pytest.approx(2.345)


def test_stale_height_holds_the_window():
    ev = east_view()
    for d in ev["dims"]:
        if d["handle"] == "e4":
            d["p3"] = [56500, 12640]                       # print 260 kept, geometry 2640: stale
    ev["segments"] = [s for s in ev["segments"] if not s[4].startswith("W2")] + _jambs(55300, 57700, 10000,
                                                                                         12640, "W2")
    _, rec = run(views=[ev, west_view()])
    assert rec["W2"]["status"] == "HELD" and rec["W2"]["reason"] == "NO_PRINTED_HEIGHT"
    assert rec["W2"]["area_m2"] is None


def test_width_conflict_holds():
    ev = east_view()
    # printed 245 between witnesses 25 mm outside each drawn jamb: the elevation says 2.45, the plan 2.40
    ev["dims"].append(_dim("wc", (55275, 11000), (57725, 11000), "245", angle=0.0))
    _, rec = run(views=[ev, west_view()])
    assert rec["W2"]["status"] == "HELD" and rec["W2"]["reason"] == "WIDTH_CONFLICT"
    assert rec["W1"]["status"] == "MEASURED"


def test_one_printed_width_gives_no_mapping():
    ev = east_view()
    ev["dims"] = [d for d in ev["dims"] if d["handle"] != "w4"]
    res, rec = run(views=[ev, west_view()])
    assert {v["view_id"]: v["mapping"]["state"] for v in res["views"]}["EAST"] == "NO_MAPPING"
    for k in ("W1", "W2", "W3", "W4"):
        assert rec[k]["status"] == "HELD" and rec[k]["area_m2"] is None
    assert rec["D1"]["status"] == "MEASURED" and rec["W5"]["status"] == "MEASURED"


def test_arch_top_not_printed():
    ev = east_view()
    ev["dims"] = [d for d in ev["dims"] if d["handle"] != "e6"]
    _, rec = run(views=[ev, west_view()])
    r = rec["W4"]
    assert r["status"] == "HELD" and r["reason"] == "ARCH_TOP_NOT_PRINTED"
    n = r["evidence"]["elevations"]["EAST"]
    assert n["arch_top_above_foot_m"] == pytest.approx(1.70, abs=1e-6)


def _w4_single_dim(ev):
    ev["dims"] = [d for d in ev["dims"] if d["handle"] not in ("e5", "e6")] + [
        _dim("e7", (55600, 15200), (55700, 16900), "170")]
    return ev


def test_arch_printed_as_one_dimension_from_the_foot():
    _, rec = run(views=[_w4_single_dim(east_view()), west_view()])
    assert rec["W4"]["status"] == "MEASURED" and rec["W4"]["area_m2"] == pytest.approx(3.06)
    assert rec["W4"]["evidence"]["shape"] == "ARCHED"


def test_head_above_jambs_without_an_arch_holds():
    ev = _w4_single_dim(east_view())
    ev["segments"] = [s for s in ev["segments"] if not s[4].startswith("W4A")]
    _, rec = run(views=[ev, west_view()])
    assert rec["W4"]["reason"] == "HEAD_ABOVE_JAMBS_NO_ARCH" and rec["W4"]["area_m2"] is None


def test_springing_printed_but_no_arch_drawn_is_rectangular():
    ev = east_view()
    ev["segments"] = [s for s in ev["segments"] if not s[4].startswith("W4A")]
    _, rec = run(views=[ev, west_view()])
    assert rec["W4"]["status"] == "MEASURED" and rec["W4"]["area_m2"] == pytest.approx(1.80 * 1.20)


def test_curved_lines_above_that_do_not_spring_from_the_jambs():
    ev = east_view()
    # a railing drawn 0.60 m above W3's head, inside its width: not W3's arch
    ev["segments"] += [(51500, 17300, 52500, 17500, "RAIL1"), (51500, 17500, 52500, 17300, "RAIL2")]
    _, rec = run(views=[ev, west_view()])
    assert rec["W3"]["status"] == "MEASURED" and rec["W3"]["area_m2"] == pytest.approx(1.80)


def test_missing_storey_pair_holds_the_whole_stack():
    ev = east_view()
    ev["segments"] = [s for s in ev["segments"] if not s[4].startswith("W1")]
    _, rec = run(views=[ev, west_view()])
    assert rec["W1"]["reason"] == "STACK_NOT_BOUND" and rec["W3"]["reason"] == "STACK_NOT_BOUND"


def test_front_and_back_windows_on_one_range_hold():
    ops = plan() + [{"id": "W7", "floor": "GF", "kind": "WINDOW", "xy": (0.0, 2.0), "axis": (0.0, 1.0),
                     "width_m": 1.20}]
    _, rec = run(ops)
    assert rec["W1"]["status"] == "HELD" and rec["W1"]["reason"] == "STACK_NOT_BOUND"
    assert rec["W7"]["status"] == "HELD"
    assert rec["W3"]["status"] == "HELD"                     # same range, so the stack is not bound either


def test_schedule_height_governs_with_a_review():
    ops = plan()
    next(p for p in ops if p["id"] == "D1").update(schedule_height_m=2.20, schedule_source="door schedule row D1")
    _, rec = run(ops)
    r = rec["D1"]
    assert r["status"] == "MEASURED" and r["height_m"] == 2.20 and r["height_source"] == "SCHEDULE"
    assert r["area_m2"] == pytest.approx(2.20)
    assert "REVIEW" in r["evidence"]["finding"]


def test_schedule_height_without_an_elevation():
    ops = plan()
    next(p for p in ops if p["id"] == "W6").update(schedule_height_m=1.40, schedule_source="window schedule W6")
    _, rec = run(ops)
    assert rec["W6"]["status"] == "MEASURED" and rec["W6"]["area_m2"] == pytest.approx(2.10)


def test_curved_window_needs_the_owner_basis():
    ops = plan()
    w4 = next(p for p in ops if p["id"] == "W4")
    w4.update(width_m=2.10, curved={"chord_m": 1.80, "bases_m": {"MIN_RADIUS_ARC": 2.00, "MAX_RADIUS_ARC": 2.10}})
    _, rec = run(ops)
    r = rec["W4"]
    assert r["status"] == "HELD" and r["reason"] == "CURVED_WIDTH_BASIS" and r["area_m2"] is None
    assert r["evidence"]["candidates_m2"] == {"MIN_RADIUS_ARC": 3.4, "MAX_RADIUS_ARC": 3.57, "CHORD": 3.06}
    _, rec = run(ops, curved_width_basis="CHORD")
    assert rec["W4"]["status"] == "MEASURED" and rec["W4"]["area_m2"] == pytest.approx(3.06)


def test_no_dimensions_and_missing_data():
    ev, wv = east_view(), west_view()
    ev["dims"], wv["dims"] = [], []
    ops = plan() + [{"id": "W8", "floor": "1F", "kind": "WINDOW", "xy": (12.0, 4.0), "axis": (0.0, 1.0),
                     "width_m": None},
                    {"id": "S1", "floor": "1F", "kind": "SKYLIGHT", "xy": (5.0, 5.0), "axis": (1.0, 0.0),
                     "width_m": 1.0}]
    res, rec = run(ops, views=[ev, wv])
    assert res["summary"]["by_status"].get("MEASURED") is None
    assert rec["W8"]["reason"] == "WIDTH_MISSING" and rec["S1"]["status"] == "UNSUPPORTED"
    assert all(r["area_m2"] is None for r in res["records"])
    _, rec = run(views=[])
    assert rec["W1"]["reason"] == "NO_ELEVATION_OF_THIS_FACE"


def test_held_twin_is_evidence_only():
    ev = east_view()
    # a second 1.20 window beside W3 on 1F, drawn alike but with no printed height
    ev["segments"] += _jambs(53400, 54600, 15200, 16700, "W9")
    ops = plan() + [{"id": "W9", "floor": "1F", "kind": "WINDOW", "xy": (12.0, 4.0), "axis": (0.0, 1.0),
                     "width_m": 1.20}]
    _, rec = run(ops, views=[ev, west_view()])
    r = rec["W9"]
    assert r["status"] == "HELD" and r["reason"] == "NO_PRINTED_HEIGHT" and r["area_m2"] is None
    assert r["evidence"]["elevations"]["EAST"]["same_drawn_size_as"] == ["W3@1F"]


def test_jamb_drawn_in_pieces_is_one_jamb():
    ev = east_view()
    ev["segments"] = [s for s in ev["segments"] if s[4] not in ("W3L",)] + [
        (51400, 15200, 51400, 16000, "W3La"), (51400, 16000, 51400, 16700, "W3Lb")]
    _, rec = run(views=[ev, west_view()])
    assert rec["W3"]["status"] == "MEASURED" and rec["W3"]["area_m2"] == pytest.approx(1.80)


def test_dxf_reader_round_trip(tmp_path):
    ezdxf = pytest.importorskip("ezdxf")
    doc = ezdxf.new("R2010", setup=True)
    doc.header["$DIMLFAC"] = 1.0
    msp = doc.modelspace()
    for (x1, y1, x2, y2, _) in east_view()["segments"]:
        msp.add_line((x1, y1), (x2, y2))
    for d in east_view()["dims"]:
        p2, p3 = d["p2"], d["p3"]
        base = (p2[0] - 300, p3[1]) if d["angle"] == 90.0 else (p2[0], p2[1] + 300)
        dim = msp.add_linear_dim(base=base, p1=p2, p2=p3, angle=d["angle"], override={"dimlfac": 0.1,
                                                                                       "dimdec": 0})
        dim.render()
    f = tmp_path / "east.dxf"
    doc.saveas(f)
    v = OA.read_view(ezdxf.readfile(f), (40000, 0, 70000, 30000), 0.001, "EAST")
    assert len(v["dims"]) == len(east_view()["dims"])
    ops = [p for p in plan() if p["id"] in ("W1", "W2", "W3", "W4")]
    res = OA.measure(ops, [v], floors=FLOORS)
    rec = {r["id"]: r for r in res["records"]}
    for k in ("W1", "W2", "W3", "W4"):
        assert rec[k]["status"] == "MEASURED", (k, rec[k]["reason"], rec[k]["evidence"])
        assert rec[k]["area_m2"] == pytest.approx(HAND[k][2], abs=5e-4)
