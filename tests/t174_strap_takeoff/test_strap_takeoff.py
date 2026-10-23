"""T-174: STRAP_BEAM_TAKEOFF_V1 on a hand-calculated fixture that is NOT Alsenan (invented plan; local frame in m).

Local frame: the strap axis is the y axis; strap printed 0.40 wide x 0.50 deep, drawn edges x = -0.20 / +0.20 from
y = -0.50 (inside footing A) to y = L0 + 0.50 (inside footing B), L0 = 3.00.
  Footing A: x' -1 .. 1, y' -1.5 .. 0 (2.0 x 1.5, H 0.50), rotated by alpha about the origin: its strap face is the
             line y = x tan(alpha) through (0, 0).
  Footing B: x' -1 .. 1, y' 0 .. 1.5 (H 0.30 or 0.50), rotated by beta and moved to (0, L0): face y = L0 + x tan(beta).
Hand calculation, alpha = 30 deg, beta = -60 deg:
  axis face to face = L0 = 3.000 (the faces cut the axis at y 0 and y 3)
  edge runs: x -0.2: (3 + 0.2 tan 60) - (-0.2 tan 30) = 3.3464 + 0.1155 = 3.4619; x +0.2: 3 - 0.3464 - 0.1155 = 2.5381
  plan area outside the footings = trapezoids = 0.40 x 3.000 = 1.200 m2; concrete = 1.200 x 0.50 = 0.600 m3
  formwork sides = (3.4619 + 2.5381) x 0.50 = 3.000 m2; footing face chords 0.40 / cos 30 = 0.4619, 0.40 / cos 60 = 0.8
  projection gap = L0 - sin 30 (corner (1, 0) of A rotated) - sin 60 (corner (1, 0) of B rotated by -60) = 3 - 0.5 -
  0.8660 = 1.6340 m: the corners over-reach the faces by 0.500 / 0.866; the gap is NOT a built length (Q-74 A)
  inside A (H 0.50 = D): strip between the face and y = -0.5: 0.40 x 0.50 = 0.200 m2 -> footing concrete, 0 m3 here
alpha = beta = 0, footing B H 0.30, column x -0.15 .. 0.15, y L0 + 0.30 .. L0 + 0.60 inside B:
  inside B: 0.40 x 0.50 = 0.200 m2 less the column part 0.30 x 0.20 = 0.060 -> A_in 0.140 m2; D 0.50 > H 0.30:
  HELD range [(0.50 - 0.30) x 0.140, 0.50 x 0.140] = [0.028, 0.070] m3
Bars (bottom 4 T16, top 3 T12, links 6 T8 per m, anchorage 40 d .. 70 d, kg/m = d^2 / 162):
  bottom 4 x 3.000 x 1.580247 = 18.963 kg; top 3 x 3.0 x 0.888889 = 8.000 kg; anchorage bottom per bar 2 x 40 x 0.016 =
  1.28 .. 2.24 m -> 4 x 1.28 x 1.580247 = 8.091 .. 14.159 kg HELD; links A 6 x 3 = 18, B ceil(18) + 1 = 19 HELD
"""

import math

import pytest

from engine.source import strap_beam_takeoff_v1 as SB

L0, B, D = 3.0, 0.40, 0.50


def rot(p, a):
    c, s = math.cos(a), math.sin(a)
    return (p[0] * c - p[1] * s, p[0] * s + p[1] * c)


def fixture(alpha=30.0, beta=-60.0, hB=0.30, column=False, B_m=B, D_m=D, half_b=1.0):
    a, b = math.radians(alpha), math.radians(beta)
    fa = [rot(p, a) for p in [(-1, -1.5), (1, -1.5), (1, 0), (-1, 0)]]
    fb = [(q[0], q[1] + L0) for q in (rot(p, b) for p in [(-half_b, 0), (half_b, 0), (half_b, 1.5), (-half_b, 1.5)])]
    edges = [((-0.2, -0.5), (-0.2, L0 + 0.5)), ((0.2, -0.5), (0.2, L0 + 0.5))]
    cols = [[(-0.15, L0 + 0.3), (0.15, L0 + 0.3), (0.15, L0 + 0.6), (-0.15, L0 + 0.6)]] if column else []
    strap = {"strap_id": "S1", "mark": "SBX", "edges": edges, "B_m": B_m, "D_m": D_m,
             "bars": [{"position": "BOTTOM", "count": 4, "dia_mm": 16}, {"position": "TOP", "count": 3, "dia_mm": 12}],
             "links": {"per_m": 6, "dia_mm": 8}, "anchorage_d": (40, 70)}
    feet = [{"support_id": "FA", "polygon": fa, "H_m": 0.50}, {"support_id": "FB", "polygon": fb, "H_m": hB}]
    cols = [{"support_id": f"C{i}", "polygon": c} for i, c in enumerate(cols)]
    return strap, feet, cols


def transform(strap, feet, cols, angle_deg, mirror=False, shift=(0.0, 0.0), scale=1.0):
    a = math.radians(angle_deg)

    def T(p):
        x, y = (-p[0], p[1]) if mirror else (p[0], p[1])
        x, y = rot((x, y), a)
        return ((x + shift[0]) * scale, (y + shift[1]) * scale)
    s = dict(strap, edges=[tuple(T(p) for p in e) for e in strap["edges"]])
    f = [dict(x, polygon=[T(p) for p in x["polygon"]]) for x in feet]
    c = [dict(x, polygon=[T(p) for p in x["polygon"]]) for x in cols]
    return s, f, c


UM = lambda d: d * d / 162.0  # noqa: E731  (the project method D2_OVER_162, passed in as rebar_unit_mass gives it)


def run(*a, units="m", **kw):
    s, f, c = fixture(**kw)
    if a:
        s, f, c = transform(s, f, c, *a)
    return SB.takeoff_strap(s, f, c, units=units, unit_mass=UM)


# ------------------------------------------------------------------------------------------------ normal cases
def test_oblique_faces_hand_values():
    r = run()
    L = r["lengths"]
    assert L["axis_face_to_face_m"] == pytest.approx(3.0, abs=1e-4)
    assert sorted(L["edge_face_to_face_m"]) == pytest.approx([2.5381, 3.4619], abs=1e-4)
    assert L["projection_gap_m"] == pytest.approx(3 - 0.5 - math.sin(math.radians(60)), abs=1e-4)
    assert L["corner_overreach_m"] == pytest.approx([0.5, 0.8660], abs=1e-4)
    assert r["concrete"]["plan_area_outside_m2"] == pytest.approx(1.2, abs=1e-4)
    assert r["concrete"]["volume_m3"] == pytest.approx(0.6, abs=1e-4)
    assert r["concrete"]["status"] == SB.DRAWING_CONFIRMED
    assert r["formwork"]["side_faces_m2"] == pytest.approx(3.0, abs=1e-4)
    chords = {c["footing"]: c["chord_on_face_m"] for c in r["footing_face_covered"]}
    assert chords == {"FA": pytest.approx(0.4 / math.cos(math.radians(30)), abs=1e-4),
                      "FB": pytest.approx(0.8, abs=1e-4)}
    assert "SAME_FACE_BOTH_ENDS" in " ".join(r["flags"])
    assert "RUN_VARIES_ACROSS_WIDTH" in " ".join(r["flags"])
    ins = {o["footing"]: o for o in r["concrete_in_footings"]}
    assert ins["FA"]["A_in_m2"] == pytest.approx(0.2, abs=1e-4)
    assert ins["FA"]["owner"] == "FOOTING" and ins["FA"]["volume_m3"] == 0.0


@pytest.mark.parametrize("angle", [0.0, 30.0, 60.0, 127.0])
@pytest.mark.parametrize("mirror", [False, True])
def test_rotation_mirror_units_invariant(angle, mirror):
    base = run()
    for scale, units in ((1.0, "m"), (1000.0, "mm")):
        r = run(angle, mirror, (12.5, -7.0), scale, units=units)
        for key in ("axis_face_to_face_m", "projection_gap_m"):
            assert r["lengths"][key] == pytest.approx(base["lengths"][key], abs=1e-4)
        assert sorted(r["lengths"]["edge_face_to_face_m"]) == pytest.approx(
            sorted(base["lengths"]["edge_face_to_face_m"]), abs=1e-4)
        assert r["concrete"]["volume_m3"] == pytest.approx(0.6, abs=1e-4)
        assert r["formwork"]["side_faces_m2"] == pytest.approx(3.0, abs=1e-4)


@pytest.mark.parametrize("alpha,beta,gap", [(0.0, 0.0, 3.0), (30.0, 0.0, 2.5), (60.0, 0.0, 3.0 - math.sin(math.pi / 3)),
                                            (0.0, 30.0, 2.5)])
def test_strap_at_0_30_60_degrees_to_the_faces(alpha, beta, gap):
    r = run(alpha=alpha, beta=beta)
    assert r["lengths"]["axis_face_to_face_m"] == pytest.approx(3.0, abs=1e-4)
    assert r["lengths"]["projection_gap_m"] == pytest.approx(gap, abs=1e-4)
    assert r["concrete"]["volume_m3"] == pytest.approx(B * 3.0 * D, abs=1e-4)


def test_deeper_strap_than_footing_with_column_is_held_range():
    r = run(alpha=0.0, beta=0.0, hB=0.30, column=True)
    ins = {o["footing"]: o for o in r["concrete_in_footings"]}
    assert ins["FB"]["A_in_m2"] == pytest.approx(0.14, abs=1e-4)
    assert ins["FB"]["column_area_removed_m2"] == pytest.approx(0.06, abs=1e-4)
    assert ins["FB"]["status"] == SB.HELD
    assert ins["FB"]["range_m3"] == pytest.approx([0.028, 0.07], abs=1e-4)
    assert "volume_m3" not in ins["FB"]          # a held item never carries a value, never 0


def test_bars_runs_anchorage_and_links():
    r = run()
    g = {b["position"]: b for b in r["bars"]["groups"]}
    assert g["BOTTOM"]["kg_lb"] == pytest.approx(4 * 3.0 * 16 * 16 / 162, abs=1e-3)
    assert g["TOP"]["kg_lb"] == pytest.approx(8.0, abs=1e-3)
    assert g["BOTTOM"]["anchorage_kg"]["range"] == pytest.approx([4 * 1.28 * 256 / 162, 4 * 2.24 * 256 / 162],
                                                                 abs=1e-3)
    assert g["BOTTOM"]["anchorage_kg"]["status"] == SB.HELD
    assert r["bars"]["links"]["count_range"] == [pytest.approx(18.0), 19]
    assert r["bars"]["links"]["status"] == SB.HELD


def test_excavation_is_its_own_geometry_and_held():
    r = run()
    ex = r["excavation"]
    assert ex["status"] == SB.HELD and ex["volume_m3"] is None
    assert ex["trench_run_upper_bound_m"] == pytest.approx(3.0, abs=1e-4)


# ------------------------------------------------------------------------------------------------ adverse cases
def test_projection_gap_is_never_the_concrete_length():
    r = run(alpha=30.0, beta=-60.0)
    gap = r["lengths"]["projection_gap_m"]
    assert r["concrete"]["volume_m3"] != pytest.approx(B * gap * D, abs=1e-3)
    assert r["bars"]["groups"][0]["run_lb_m"] == pytest.approx(3.0, abs=1e-4)


def test_drawn_width_never_replaces_the_printed_section():
    r = run(B_m=0.45)
    assert "DRAWN_WIDTH_DIFFERS" in " ".join(r["flags"])
    assert r["concrete"]["volume_m3"] == pytest.approx(0.45 * 3.0 * 0.5, abs=1e-4)


def test_missing_section_is_held_not_zero():
    r = run(B_m=None, D_m=None)
    assert r["status"] == SB.HELD
    assert r["concrete"]["volume_m3"] is None and r["concrete"]["status"] == SB.HELD
    assert r["formwork"]["status"] == SB.HELD


def test_no_footing_at_one_end_is_held():
    s, f, c = fixture()
    r = SB.takeoff_strap(s, f[:1], c, units="m")
    assert r["status"] == SB.HELD and "concrete" not in r
    assert any("NO_FOOTING_AT_END" in h for h in r["held"])


def test_strap_passing_a_footing_corner_is_held():
    r = run(alpha=0.0, beta=0.0, half_b=0.1)        # footing B narrower than the strap: an edge misses it
    assert r["status"] == SB.HELD
    assert r["concrete"]["plan_area_outside_m2"] is None and r["concrete"]["volume_m3"] is None


def test_input_errors():
    s, f, c = fixture()
    with pytest.raises(SB.StrapError):
        SB.takeoff_strap(s, f, c, units="cm")
    bad = dict(s, edges=[((-0.2, -0.5), (-0.2, 3.5)), ((0.2, -0.5), (0.5, 3.5))])
    with pytest.raises(SB.StrapError):
        SB.takeoff_strap(bad, f, c, units="m")
    concave = [dict(f[0], polygon=[(-1, -1.5), (1, -1.5), (1, 0), (0, -0.5), (-1, 0)]), f[1]]
    with pytest.raises(SB.StrapError):
        SB.takeoff_strap(s, concave, c, units="m")


def test_open_outline_closed_by_its_chord_is_one_face():
    s, f, c = fixture(alpha=0.0, beta=0.0)
    # footing A drawn OPEN where the strap enters: the closing chord is collinear with the face
    f[0] = dict(f[0], polygon=[(-0.3, 0.0), (-1, 0.0), (-1, -1.5), (1, -1.5), (1, 0.0), (0.3, 0.0)])
    r = SB.takeoff_strap(s, f, c, units="m", unit_mass=UM)
    assert "SAME_FACE_BOTH_ENDS" in " ".join(r["flags"])
    assert r["concrete"]["volume_m3"] == pytest.approx(0.6, abs=1e-4)


def test_policy_record_names_the_owner_answer():
    p = SB.policy_record()
    assert p["default_guard_class"] == "UNWIRED_PRODUCER" and "Q-74" in p["rules"][0]
