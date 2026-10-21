"""T-141: GROUND_SYSTEM_SPANS_V2 on a hand-calculated fixture that is NOT Alsenan (invented plan, mm).

Fixture (hand calculation in the comments; every length is support face to face along the band axis):

  Band A  faces y = 0 / 300, x 0 .. 10,000 (300 mm ground beam)
          C0  x -300 .. 0, y 0 .. 300           column at the start, touching the band end
          C1  x 4,000 .. 4,400, y -100 .. 400    column drawn ON the band, no footing under it      -> split
          C2  x 7,000 .. 8,100, y 0 .. 300       column whose edges are collinear with the band faces -> split
          F1  x 9,000 .. 11,000, y -500 .. 800   footing under the free east end (no column)        -> footing face
          spans: 0 -> 4,000 = 4.000 (LT5M); 4,400 -> 7,000 = 2.600 (LT5M); 8,100 -> 9,000 = 0.900 (LT2_5M + LT5M)
          (the frozen S5 rule would have run 0 -> 10,000 across C1 / C2 as one span, or centre - 0.30)
  Band B  faces x = 12,000 / 12,300, y 0 .. 5,400; column P x 12,100 .. 12,500, y 2,000 .. 2,400 covers 0.67 of
          the band width -> split, flagged PARTIAL_WIDTH: 0 -> 2,000 = 2.000 (FREE_END at y 0: HELD) and
          2,400 -> 5,400 = 3.000 (free end at 5,400: HELD)
  Band C  faces y = 20,000 / 20,300, x 0 .. 5,300; band D faces x = 5,000 / 5,300, y 20,000 .. 26,000 (L corner:
          C runs into the corner square, D too). Column Q x 5,000 .. 5,300, y 26,000 .. 26,300; column R x -300 .. 0,
          y 20,000 .. 20,300. C: R face 0 -> D face 5,000 = 5.000 (exactly 5 m: neither "more than" nor "less than":
          ON_LIMIT, HELD); D: C face 20,300 -> Q face 26,000 = 5.700 (GT5M)
  Band E  faces y = 30,000 / 30,300, x 0 .. 6,000, columns at both ends (x -300 .. 0 and 6,000 .. 6,300); band G
          faces x = 3,000 / 3,300, y 30,300 .. 32,000 ends on E's face (a tee): E is NOT split = 6.000 (GT5M)
  Band K  faces y = 40,000 / 40,300, x 0 .. 3,000; column X x -300 .. 0; column Y x 2,950 .. 3,500, y 39,650 .. 39,950
          (drawn 50 mm beside the band, reaching 550 mm past its end) -> GAP_TO_COLUMN, HELD with the candidates
          band end 3.000 and column face 2.950
  Strap   footing FA x 0 .. 2,000, y 0 .. 1,500 and FB x 1,500 .. 3,500, y 4,000 .. 5,500 (plan 2); strap 500 wide,
          axis 30 deg off the y axis through (1,000, 1,500): axis face to face 2,500 / cos 30 = 2,886.75 mm; S5-style
          projection gap 4,214.10 - 2,299.04 = 1,915.06 mm; footing centre to centre 5,363.59 - 1,149.52 = 4,214.07
"""

import math

import pytest

from engine.source import ground_beam_network as GN
from engine.source import ground_system_spans_v2 as V2

CLASSES = [{"detail_id": "GT5M", "op": ">", "limit_m": 5.0}, {"detail_id": "LT5M", "op": "<", "limit_m": 5.0},
           {"detail_id": "LT2_5M", "op": "<", "limit_m": 2.5}]


def rect(x0, y0, x1, y1):
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


def band_faces(name, p0, p1, q0, q1):
    return [{"handle": name + "a", "layer": "1", "p0": p0, "p1": p1}, {"handle": name + "b", "layer": "1", "p0": q0,
                                                                      "p1": q1}]


FACES = (band_faces("A", (0, 0), (10000, 0), (0, 300), (10000, 300)) +
         band_faces("B", (12000, 0), (12000, 5400), (12300, 0), (12300, 5400)) +
         band_faces("C", (0, 20000), (5300, 20000), (0, 20300), (5300, 20300)) +
         band_faces("D", (5000, 20000), (5000, 26000), (5300, 20000), (5300, 26000)) +
         band_faces("E", (0, 30000), (6000, 30000), (0, 30300), (6000, 30300)) +
         band_faces("G", (3000, 30300), (3000, 32000), (3300, 30300), (3300, 32000)) +
         band_faces("K", (0, 40000), (3000, 40000), (0, 40300), (3000, 40300)))
SUPPORTS = [("C0", "COLUMN", rect(-300, 0, 0, 300)), ("C1", "COLUMN", rect(4000, -100, 4400, 400)),
            ("C2", "COLUMN", rect(7000, 0, 8100, 300)), ("F1", "FOOTING", rect(9000, -500, 11000, 800)),
            ("P", "COLUMN", rect(12100, 2000, 12500, 2400)),
            ("Q", "COLUMN", rect(5000, 26000, 5300, 26300)), ("R", "COLUMN", rect(-300, 20000, 0, 20300)),
            ("E0", "COLUMN", rect(-300, 30000, 0, 30300)), ("E1", "COLUMN", rect(6000, 30000, 6300, 30300)),
            ("X", "COLUMN", rect(-300, 40000, 0, 40300)), ("Y", "COLUMN", rect(2950, 39650, 3500, 39950))]
FA, FB = rect(0, 0, 2000, 1500), rect(1500, 4000, 3500, 5500)

HAND = {  # band letter -> [(face to face m, status, start kind, end kind)]
    "A": [(4.000, "RELEASED", "COLUMN", "COLUMN"), (2.600, "RELEASED", "COLUMN", "COLUMN"),
          (0.900, "RELEASED", "COLUMN", "FOOTING_FACE")],
    "B": [(2.000, "HELD", "FREE_END", "COLUMN"), (3.000, "HELD", "COLUMN", "FREE_END")],
    "C": [(5.000, "HELD", "COLUMN", "BEAM_JUNCTION")],
    "D": [(5.700, "RELEASED", "BEAM_JUNCTION", "COLUMN")],
    "E": [(6.000, "RELEASED", "COLUMN", "COLUMN")],
    "G": [(1.700, "HELD", "BEAM_JUNCTION", "FREE_END")],
    "K": [(3.000, "HELD", "COLUMN", "GAP_TO_COLUMN")],
}


def transform(pt, *, rot_deg=0.0, mirror=False, scale=1.0):
    x, y = pt
    if mirror:
        x = -x
    a = math.radians(rot_deg)
    return ((x * math.cos(a) - y * math.sin(a)) * scale, (x * math.sin(a) + y * math.cos(a)) * scale)


def run(rot_deg=0.0, mirror=False, units="mm"):
    sc = 1.0 if units == "mm" else 0.001
    T = lambda p: transform(p, rot_deg=rot_deg, mirror=mirror, scale=sc)  # noqa: E731
    faces = [{**f, "p0": T(f["p0"]), "p1": T(f["p1"])} for f in FACES]
    res = GN.pair_straight(faces, width=300 * sc, tol=12 * sc, admitted_layers={"1"}, min_face=300 * sc,
                           min_overlap=300 * sc, join_tol=1.0 * sc)
    bands = [{"band_id": b["handles"][0][0], "u": b["u"], "lo_off": b["lo_off"], "hi_off": b["hi_off"],
              "t0": b["t0"], "t1": b["t1"], "handles": b["handles"]} for b in res["bands"]]
    sup = [{"support_id": i, "kind": k, "polygon": [T(p) for p in poly]} for i, k, poly in SUPPORTS]
    out = V2.split_ground_beams(bands, sup, units=units, classes=CLASSES)
    S = lambda e: [T(p) for p in e]  # noqa: E731
    u = (math.sin(math.radians(30)), math.cos(math.radians(30)))
    n = (-u[1], u[0])
    P0 = (1000.0, 1500.0)
    edge = lambda off: ((P0[0] - 1000 * u[0] + off * n[0], P0[1] - 1000 * u[1] + off * n[1]),  # noqa: E731
                        (P0[0] + 3500 * u[0] + off * n[0], P0[1] + 3500 * u[1] + off * n[1]))
    straps = V2.measure_straps([{"strap_id": "S1", "mark": "SBX", "edges": [S(edge(-250)), S(edge(250))]}],
                               [{"support_id": "FA", "kind": "FOOTING", "polygon": S(FA)},
                                {"support_id": "FB", "kind": "FOOTING", "polygon": S(FB)}], units=units)
    return out, straps


def by_band(out):
    d = {}
    for s in out["spans"]:
        d.setdefault(s["band_id"], []).append(s)
    for v in d.values():
        v.sort(key=lambda s: s["lengths"]["face_to_face_m"])
    return d


def check(out, straps):
    got = by_band(out)
    assert sorted(got) == sorted(HAND)
    for k, want in HAND.items():
        w = sorted(want)
        g = got[k]
        assert len(g) == len(w), k
        for s, (L, st, *kinds) in zip(g, w):
            assert s["lengths"]["face_to_face_m"] == pytest.approx(L, abs=1e-4), (k, s["span_id"])
            assert s["status"] == st, (k, s["span_id"], s["held_reasons"])
            assert sorted([s["start"]["kind"], s["end"]["kind"]]) == sorted(kinds), (k, s["start"], s["end"])
            assert (s["lengths"]["bar_run_lb_m"] is None) == (st == "HELD")
    assert out["conservation"]["all_pass"]
    (st,) = straps
    c = st["candidates"]
    assert st["status"] == "HELD" and any("STRAP_LENGTH_BASIS_NOT_SET" in h for h in st["held_reasons"])
    assert c["axis_face_to_face_m"] == pytest.approx(2.5 / math.cos(math.radians(30)), abs=1e-4)
    assert c["edge_face_to_face_m"] == pytest.approx([2.88675, 2.88675], abs=1e-4)
    assert c["projection_gap_m"] == pytest.approx(1.91506, abs=1e-4)
    assert c["footing_centre_to_centre_m"] == pytest.approx(4.21407, abs=1e-4)
    assert any("PROJECTION_GAP_DIFFERS" in f for f in st["flags"])
    assert st["width_m"] == pytest.approx(0.5, abs=1e-6)


def test_hand_fixture_mm():
    check(*run())


@pytest.mark.parametrize("rot", [30.0, 37.0, 90.0, 180.0, 233.0])
@pytest.mark.parametrize("mirror", [False, True])
def test_mirror_rotation_invariant(rot, mirror):
    check(*run(rot_deg=rot, mirror=mirror))


def test_units_metres_equal_mm():
    check(*run(units="m"))
    check(*run(rot_deg=37.0, mirror=True, units="m"))


def test_details_of_the_defects():
    out, _ = run()
    g = by_band(out)
    a = {round(s["lengths"]["face_to_face_m"], 3): s for s in g["A"]}
    # defect 1: the column on the band splits it, both pieces measured to its faces
    assert a[4.0]["end"]["refs"] == ["C1"] and a[2.6]["start"]["refs"] == ["C1"]
    # defect 2: collinear column edges: face to face 1.100 m column, never centre - 0.30
    assert a[2.6]["end"]["face_station_m"] - a[2.6]["start"]["face_station_m"] == pytest.approx(2.6)
    assert {r["support_id"]: r["along_m"] for r in out["bands"] if r["band_id"] == "A"
            for r in r["interior_supports"]} == {"C1": 0.4, "C2": 1.1}
    # free end over a footing ends at the footing face; class from the split span
    assert a[0.9]["end"]["kind"] == "FOOTING_FACE" and a[0.9]["class_face_to_face"] == ["LT2_5M", "LT5M"]
    assert a[4.0]["class_face_to_face"] == ["LT5M"]
    # partial-width support flagged, still a split
    assert any("PARTIAL_WIDTH_SUPPORT P" in f for s in g["B"] for f in s["flags"])
    # 5.00 m exactly: no printed title applies, both stay candidates, HELD (never a pick)
    (c,) = g["C"]
    assert c["class_state"] == "ON_LIMIT" and c["class_face_to_face"] == ["GT5M", "LT5M"]
    # the tee does not split the carrier, it is listed as intermediate
    (e,) = g["E"]
    assert [i["band_id"] for i in e["intermediate"]] == ["G"]
    # a column drawn beside the band end: HELD with the candidates stored apart, no bar run
    (k,) = g["K"]
    assert k["lengths"]["bar_run_lb_m"] is None
    cands = {key.split(":", 1)[1]: v["face_to_face_m"] for key, v in k["lengths"]["end_candidates"].items()}
    assert cands == {"band_end": pytest.approx(3.0), "column_face Y": pytest.approx(2.95)}


def test_missing_data_is_never_zero():
    # strap with a footing at one end only: HELD, no axis value (None, not 0)
    st = V2.measure_straps([{"strap_id": "S", "edges": [((0, 0), (0, 4000)), ((500, 0), (500, 4000))]}],
                           [{"support_id": "F", "kind": "FOOTING", "polygon": rect(-500, -1000, 1000, 500)}])
    assert st[0]["status"] == "HELD" and st[0]["candidates"]["axis_face_to_face_m"] is None
    assert any("NO_FOOTING_AT_END" in h for h in st[0]["held_reasons"])
    # a curved band is listed UNSUPPORTED, never measured as 0
    out = V2.split_ground_beams([{"band_id": "ARC1", "kind": "ARC", "handles": ["a", "b"]}], [], units="mm")
    assert out["spans"] == [] and out["unsupported"][0]["status"] == "UNSUPPORTED"
    # a band with nothing at either end: HELD
    out = V2.split_ground_beams([{"band_id": "Z", "u": (1.0, 0.0), "lo_off": 0, "hi_off": 300, "t0": 0, "t1": 2000}],
                                [], units="mm")
    assert out["spans"][0]["status"] == "HELD" and out["spans"][0]["lengths"]["bar_run_lb_m"] is None


def test_input_errors():
    with pytest.raises(V2.SpanError):
        V2.split_ground_beams([], [], units="cm")
    b = {"band_id": "Z", "u": (1.0, 0.0), "lo_off": 0, "hi_off": 300, "t0": 0, "t1": 2000}
    with pytest.raises(V2.SpanError):
        V2.split_ground_beams([b, dict(b)], [], units="mm")
    with pytest.raises(V2.SpanError):
        V2.split_ground_beams([dict(b, u=(2.0, 0.0))], [], units="mm")
    with pytest.raises(V2.SpanError):
        V2.split_ground_beams([b], [{"support_id": "x", "kind": "WALL", "polygon": rect(0, 0, 1, 1)}], units="mm")
