"""T-178: lessons into regression tests (ENGINEERING_REASONING_STANDARD section 4 C). One normal and at least one
adverse case per lesson on synthetic NON-Alsenan fixtures ('Villa Q'), and per lesson a deliberately broken variant
(the error the lesson resolved) that the same check rejects. Metres unless stated. Hand values (6 decimals):

L1 RING BEAM IN ITS BAY (T-160, b5da75b). Bay faces W / E 2.50, S / N 2.20 from the ring centre; ring r 2.00 / 2.30,
   depth 0.50. annulus = pi (2.30^2 - 2.00^2) = pi x 1.29 = 4.052655; acos(2.20 / 2.30) = acos(0.956522) = 0.295963;
   seg(2.30, 2.20) = 5.29 x 0.295963 - 2.20 x sqrt(0.45) = 1.565644 - 2.20 x 0.670820 = 1.565644 - 1.475805 = 0.089839;
   W / E 2.50 > 2.30 and inner 2.00 < 2.20: no other segment. Ring in bay 4.052655 - 2 x 0.089839 = 3.872977 m2,
   x 0.50 = 1.936488 m3. BROKEN (full annulus) 2.026327 m3 double counts 0.089839 m3 in the S / N beams.
   ADVERSE: ring tangent to the S / N faces (r 1.90 / 2.20, faces 2.20): nothing crosses, ring = annulus
   pi (4.84 - 3.61) = 3.864159 m2; a bay corner inside the ring (faces 1.50, r 2.30) is refused, never guessed.
L2 COLUMN TO ITS DEEPEST MEMBER (T-119 r2, 0f32ff8). Interval 3.60, slab t 0.18, column 0.30 x 0.30. Downstands
   0.60 and 0.45 frame in: height 3.60 - 0.60 = 3.00 m, 0.270 m3, joint 0.09 x (0.60 - 0.18) = 0.0378 m3.
   ADVERSE: the deepest member (1.00) is an UPSTAND tank wall: it hangs only t, the 0.60 downstand controls: 3.00
   (BROKEN 'deepest regardless of side' 2.60); nothing frames in: t controls, 3.42; side not shown for a 0.90 member,
   the rest 0.45: HELD 2.70 .. 3.15, no single value. BROKEN global depth 0.75 for every column: 2.85.
L3 FACE ON A LOWER ROOF (T-159, 349251f). GF 10.00 x 8.00 (outside 0.00, roof edge top +3.90, 1F floor +4.00); 1F
   6.00 x 8.00 over its west part (floor +4.00, edge top +7.70); the GF annex roof under the 1F east face is +3.40.
   1F east face 8.00 x (7.70 - 3.40) = 34.40 m2 (BROKEN from its floor: 8.00 x 3.70 = 29.60, -4.80 m2); 1F S / W / N
   flush with the GF faces below: 6.00 / 8.00 / 6.00 x 3.70 = 22.20 / 29.60 / 22.20; 1F total 108.40 m2. Mirrored
   and turned a quarter: the same. ADVERSE: lower roof level not printed (None): that face HELD (None), never its
   floor, the other three 74.00 m2 still measured.
L4 HELD RANGE MUST CONTAIN THE TRUTH (T-142 D3, 5de8657). Strap between footing A (outlined, 1.60 along the strap)
   and footing B (true 1.40; the schedule's largest B size 1.80), centres 6.00 apart, blinding 0.60 x 0.075 = 0.045
   m3/m. Both outlined: (6.00 - 0.80 - 0.70) x 0.045 = 4.50 x 0.045 = 0.2025 m3. B with no outline: HELD
   low (6.00 - 0.80 - 0.90) x 0.045 = 0.1935, high (6.00 - 0.80) x 0.045 = 0.2340: contains 0.2025. BROKEN (unmerged
   strip as the lower bound, the pre-T-142 'held lower bound 5.724 > hand 5.189'): low 0.2340 > 0.2025. ADVERSE: no
   window either: low None (NOT_ESTABLISHED), never 0 and never the high value. Units: the same in mm.
L5 EVERY COMPARISON NAMES ITS PINNED SPEC (T-165, 37124da). A spec without 'profile' is refused (a missing key is not
   'no profile'; null is); two manifests that differ only in the pinned profile report that difference (BROKEN: a
   comparison of figures alone calls them the same baseline).
L6 DOORWAY NIB >= 0.05 m STAYS WALL (T-169, c8a524f). L room: W1 0.20 along x (centre y 0) x 0.10 .. 5.00, W2 0.20
   along y x 0, y 0.10 .. 3.50, partition P 0.15 at x 2.00 drawn y 1.00 .. 3.50 (free end), 0.75 leaf hinged
   (2.00, 0.20): face-to-face gap 1.00 - 0.10 = 0.90. Arch run P = 3.50 - 0.10 = 3.40. Nib exactly 0.050 (both faces
   x 2.00 -/+ 0.075, y 0.10 .. 0.15): WALL, doorway 0.85, physical 3.40 - 0.85 = 2.55 (BROKEN, doorway = gap: 2.50).
   ADVERSE: nib 0.045 < 0.05 (L-P9-04): artefact, listed, doorway 0.90, physical 2.50.
L7 PORCH FLOOR AND SOFFIT ARE TWO SURFACES (T-157, merged). Porch 4.60 x 4.00 under a slab, two steps 2.00 x 0.90
   outside the slab edge, wall stub 0.40 x 1.40 in the corner, a 0.25 downstand beam along the back edge.
   Floor 18.40 + 1.80 - 0.56 = 19.64 m2; soffit 18.40 - 4.60 x 0.25 = 17.25 m2; floor only = steps 1.80 + under the
   beam 1.15 - 0.10 (stub under beam) = 2.85; soffit only = over the stub 0.56 - 0.10 = 0.46; 19.64 - 2.85 + 0.46 =
   17.25. BROKEN (soffit copied from the floor): 19.64, +2.39 m2.
"""
from __future__ import annotations

import importlib.util
import math
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))


def _load(folder, name):
    key = f"t178_{folder}_{name}"
    if key in sys.modules:
        return sys.modules[key]
    spec = importlib.util.spec_from_file_location(key, ROOT / "research" / folder / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[key] = mod
    spec.loader.exec_module(mod)
    return mod


LS = _load("agents_t178", "lessons")
DR = _load("agents_t160", "dome_ring")
FS = _load("agents_t159", "t159_sides")

from engine.source import masonry_centreline_v2 as V2  # noqa: E402
from tools import release_baseline as RB  # noqa: E402

TOL = 1e-6


# ======================================================================================== L1 ring beam in its bay
def _ring(faces, ri=2.00, ro=2.30, D=0.50, far=0.25):
    return {"r_inner_m": ri, "r_outer_m": ro, "ring_depth_m": D, "columns_rel_m": [],
            "faces": {k: {"d_m": v, "far_d_m": v + far} for k, v in faces.items()}}


FACES_Q = {"W": 2.50, "E": 2.50, "S": 2.20, "N": 2.20}


def _ring_full_annulus(rec):           # BROKEN: the whole annulus as ring concrete (the T-160 double count)
    return math.pi * (rec["r_outer_m"] ** 2 - rec["r_inner_m"] ** 2) * rec["ring_depth_m"]


def _ring_check(m3):
    return abs(m3 - 1.936488) <= 1.5e-6


def test_l1_ring_in_bay_by_hand():
    r = DR.ring(_ring(FACES_Q))
    assert r["annulus_full_m2"] == pytest.approx(4.052655, abs=1.5e-6)
    assert r["ring_in_bay_m2"] == pytest.approx(3.872977, abs=1.5e-6)
    assert _ring_check(r["ring_m3"])
    assert r["double_count_avoided_m3"] == pytest.approx(0.089839, abs=1.5e-6)
    assert r["max_method_diff_m2"] < 1e-6                     # closed form = shapely
    assert r["readd_m2"] == pytest.approx(r["annulus_full_m2"], abs=1e-9)


def test_l1_broken_full_annulus_is_rejected():
    assert not _ring_check(_ring_full_annulus(_ring(FACES_Q)))  # 2.026327 m3


@pytest.mark.parametrize("rot", [0.0, 30.0, -73.0])
def test_l1_rotation_and_units(rot):
    m = DR.ring(_ring({"W": 2.50, "E": 2.50, "S": 2.20, "N": 2.20}), rot_deg=rot)
    assert m["ring_in_bay_shapely_m2"] == pytest.approx(3.872977, abs=2e-6)
    mm = DR.ring({"r_inner_m": 2000.0, "r_outer_m": 2300.0, "ring_depth_m": 500.0, "columns_rel_m": [],
                  "faces": {k: {"d_m": v * 1000, "far_d_m": v * 1000 + 250} for k, v in FACES_Q.items()}}, unit=0.001)
    assert mm["ring_m3"] == pytest.approx(1.936488, abs=1.5e-6)


def test_l1_adverse_tangent_and_corner():
    t = DR.ring(_ring({"W": 2.50, "E": 2.50, "S": 2.20, "N": 2.20}, ri=1.90, ro=2.20))
    assert t["ring_in_bay_m2"] == pytest.approx(3.864159, abs=1.5e-6)
    assert t["double_count_avoided_m3"] == pytest.approx(0.0, abs=1e-12)
    with pytest.raises(ValueError):
        DR.ring(_ring({k: 1.50 for k in FACES_Q}))
    held = DR.ring(_ring(FACES_Q, D=None))
    assert held["status"] == "HELD" and held["ring_m3"] is None


# ======================================================================================== L2 column to deepest member
B60 = {"id": "B60", "depth_m": 0.60, "position": "DOWNSTAND"}
B45 = {"id": "B45", "depth_m": 0.45, "position": "DOWNSTAND"}


def _global_depth(interval, members, t):          # BROKEN: one depth for every column (freelancer's interval - 0.75)
    return {"status": "DRAWING-CONFIRMED", "height_m": interval - 0.75}


def _deepest_any_side(interval, members, t):      # BROKEN: the deepest member whatever side of the slab it is on
    return {"status": "DRAWING-CONFIRMED", "height_m": interval - max([t] + [m["depth_m"] for m in members])}


CASES_L2 = [([B60, B45], 3.00),
            ([B60, B45, {"id": "TW", "depth_m": 1.00, "position": "UPSTAND"}], 3.00),
            ([], 3.42)]


@pytest.mark.parametrize("members,want", CASES_L2)
def test_l2_column_height_by_hand(members, want):
    r = LS.column_height(3.60, members, 0.18)
    assert r["status"] == "DRAWING-CONFIRMED" and r["height_m"] == pytest.approx(want, abs=TOL)


def test_l2_volume_and_joint():
    r = LS.column_height(3.60, [B60, B45], 0.18)
    assert r["controlling"] == "B60"
    assert 0.09 * r["height_m"] == pytest.approx(0.270, abs=TOL)
    assert LS.joint_m3(0.09, r["hang_m"], 0.18) == pytest.approx(0.0378, abs=TOL)


def test_l2_adverse_side_not_shown_is_held():
    r = LS.column_height(3.60, [B45, {"id": "BX", "depth_m": 0.90, "position": None}], 0.18)
    assert r["status"] == "HELD" and r["height_m"] is None
    assert r["range_m"] == pytest.approx((2.70, 3.15), abs=TOL)
    assert LS.column_height(3.60, [{"id": "B?", "depth_m": None, "position": "DOWNSTAND"}], 0.18)["height_m"] is None
    assert LS.column_height(None, [B60], 0.18)["status"] == "HELD"


@pytest.mark.parametrize("broken", [_global_depth, _deepest_any_side])
def test_l2_broken_variants_rejected(broken):
    got = [broken(3.60, m, 0.18)["height_m"] for m, _ in CASES_L2]
    assert any(abs(g - w) > TOL for g, (_, w) in zip(got, CASES_L2))


# ======================================================================================== L3 face on a lower roof
AXES = {"+x": "E", "-x": "W", "+y": "N", "-y": "S"}


def _box(x0, y0, x1, y1, rot=0.0, mirror=False):
    pts = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
    c, s = math.cos(math.radians(rot)), math.sin(math.radians(rot))

    def X(p):
        x, y = (-p[0], p[1]) if mirror else p
        return (c * x - s * y, s * x + c * y)
    pts = [X(p) for p in pts]
    if mirror:
        pts = pts[::-1]                                       # keep the outline counter-clockwise
    return [{"a": pts[i], "b": pts[(i + 1) % 4], "len_m": math.dist(pts[i], pts[(i + 1) % 4]), "straight": True}
            for i in range(4)]


def _floors(rot=0.0, mirror=False, lower_roof=3.40):
    f1 = {"name": "1F", "edges": _box(0, 0, 6, 8, rot, mirror), "floor": 4.00, "edge_top": 7.70, "next_floor": None,
          "lower_roof": lower_roof}
    return [{"name": "GF", "edges": _box(0, 0, 10, 8, rot, mirror), "outside": 0.00, "floor": 0.15,
             "edge_top": 3.90, "next_floor": 4.00}, f1]


def _first_floor(rows):
    return sorted((r["area_m2"] for r in rows if r["floor"] == "1F"), key=lambda v: (v is None, v or 0))


def test_l3_face_on_lower_roof_by_hand():
    rows = FS.house_facade(_floors(), AXES)
    f1 = {r["side"]: r["area_m2"] for r in rows if r["floor"] == "1F"}
    assert f1["E-1"] == pytest.approx(34.40, abs=TOL)
    assert f1["S-1"] == pytest.approx(22.20, abs=TOL) and f1["N-1"] == pytest.approx(22.20, abs=TOL)
    assert f1["W-1"] == pytest.approx(29.60, abs=TOL)
    assert sum(f1.values()) == pytest.approx(108.40, abs=TOL)


@pytest.mark.parametrize("rot,mirror", [(90.0, False), (0.0, True), (-37.0, True)])
def test_l3_mirror_and_rotation(rot, mirror):
    got = _first_floor(FS.house_facade(_floors(rot, mirror), AXES))
    assert got == pytest.approx(sorted([22.20, 22.20, 29.60, 34.40]), abs=1e-6)


def test_l3_broken_from_floor_level_rejected():
    rows = FS.house_facade(_floors(lower_roof=4.00), AXES)   # BROKEN: the face starts at its own floor
    e = [r["area_m2"] for r in rows if r["floor"] == "1F" and r["side"] == "E-1"][0]
    assert e == pytest.approx(29.60, abs=TOL) and abs(e - 34.40) > 1.0


def test_l3_adverse_lower_roof_unknown_is_held():
    rows = FS.house_facade(_floors(lower_roof=None), AXES)
    f1 = {r["side"]: r["area_m2"] for r in rows if r["floor"] == "1F"}
    assert f1["E-1"] is None                                   # HELD, never its floor, never 0
    assert sum(v for k, v in f1.items() if k != "E-1") == pytest.approx(74.00, abs=TOL)


# ======================================================================================== L4 held range contains truth
def _broken_range(c2c, a_half, b_true, b_max, w, t):     # BROKEN: an unbound footing = the unmerged strip, low = high
    hi = (c2c - a_half) * w * t
    return {"status": "HELD", "m3": None, "low_m3": hi, "high_m3": hi}


def test_l4_both_outlined_by_hand():
    r = LS.strip_blinding_range(6.00, 0.80, 0.70, 0.90, 0.60, 0.075)
    assert r["status"] == "DRAWING-CONFIRMED" and r["m3"] == pytest.approx(0.2025, abs=TOL)


@pytest.mark.parametrize("k", [1.0, 1000.0])
def test_l4_unbound_footing_range_contains_hand(k):
    r = LS.strip_blinding_range(6.00 * k, 0.80 * k, None, 0.90 * k, 0.60 * k, 0.075 * k)
    lo, hi = r["low_m3"] / k ** 3, r["high_m3"] / k ** 3
    assert r["status"] == "HELD" and r["m3"] is None
    assert (lo, hi) == pytest.approx((0.1935, 0.2340), abs=TOL)
    assert LS.range_contains(lo, hi, 0.2025)


def test_l4_broken_lower_bound_rejected():
    b = _broken_range(6.00, 0.80, None, 0.90, 0.60, 0.075)
    assert not LS.range_contains(b["low_m3"], b["high_m3"], 0.2025)


def test_l4_adverse_no_window_low_not_established():
    r = LS.strip_blinding_range(6.00, 0.80, None, None, 0.60, 0.075)
    assert r["low_m3"] is None and r["high_m3"] == pytest.approx(0.2340, abs=TOL)
    assert LS.range_contains(r["low_m3"], r["high_m3"], 0.2025)
    assert not LS.range_contains(None, None, 0.2025)
    with pytest.raises(ValueError):
        LS.strip_blinding_range(1.00, 0.80, 0.70, 0.90, 0.60, 0.075)


# ======================================================================================== L5 pinned released spec
SHA_A, SHA_B, SHA_P = "a" * 64, "b" * 64, "c" * 64
METHODS = ("ARCH_TAKEOFF_V2.9",)


def _spec(**over):
    s = {"schema": RB.SPEC_SCHEMA, "baseline_id": "villa-q-released", "method": "ARCH_TAKEOFF_V2.9", "python": "3.11",
         "inputs": {"plan": {"sha256": SHA_A}, "structural": {"sha256": SHA_B}}, "conventions": None,
         "profile": {"path": "research/x/profile.json", "sha256": SHA_P}, "facts": None, "project": None,
         "as_of": "2026-10-22", "options": {"no_svg": True, "no_m9_xlsx": True, "no_completeness": False}}
    s.update(over)
    return s


def _manifest(profile_sha):
    row = {"item_code": "STR.CONC", "unit": "m3", "lines": 2, "released_lines": 2, "released_qty": 12.5,
           "held_lines": 0, "held_bounded_lines": 0, "held_low": None, "held_high": None, "held_unbounded_lines": 0,
           "excluded_lines": 0, "states": {"MEASURED": 2}}
    return {"baseline_id": "q", "method": "ARCH_TAKEOFF_V2.9", "python": "3.11", "inputs": [], "project": None,
            "as_of": "2026-10-22", "options": {}, "per_code": [row],
            "pinned_files": {"profile": None if profile_sha is None else {"sha256": profile_sha}},
            "run": {"line_count": 2, "outputs_sha256": {"BOQ_LINES.csv": SHA_A}}, "engine": {"commit": "x"}}


def _figures_only(a, b):                     # BROKEN: same figures -> 'same baseline', configuration never named
    return [] if a["per_code"] == b["per_code"] else ["figures"]


def test_l5_spec_states_every_choice():
    assert RB.validate_spec(_spec(), methods=METHODS) == []
    assert RB.validate_spec(_spec(profile=None), methods=METHODS) == []          # 'no profile' stated with null
    s = _spec()
    del s["profile"]
    assert any("'profile' missing" in p for p in RB.validate_spec(s, methods=METHODS))


def test_l5_comparison_names_the_profile_difference():
    same = RB.compare(_manifest(SHA_P), _manifest(SHA_P))
    assert same["config_differences"] == [] and same["codes_differing"] == 0
    d = RB.compare(_manifest(SHA_P), _manifest(None))
    assert [c["field"] for c in d["config_differences"]] == ["pinned_files"]
    assert _figures_only(_manifest(SHA_P), _manifest(None)) == []                # the broken check sees nothing


# ======================================================================================== L6 doorway jamb nib
def _floor_l6(nib):
    """walls / evidence of the L6 room in mm, nib (m) of both P faces on W1's face; None = no nib drawn."""
    bands = [("W1", 0.20, (0.10, 0.0), (5.00, 0.0)), ("W2", 0.20, (0.0, 0.10), (0.0, 3.50)),
             ("P", 0.15, (2.00, 1.00), (2.00, 3.50))]
    faces = []
    for _, t, p0, p1 in bands:
        L = math.dist(p0, p1)
        u = ((p1[0] - p0[0]) / L, (p1[1] - p0[1]) / L)
        n = (-u[1], u[0])
        for o in (t / 2, -t / 2):
            faces.append(((p0[0] + n[0] * o, p0[1] + n[1] * o), (p1[0] + n[0] * o, p1[1] + n[1] * o)))
    if nib:
        for side in (1, -1):
            faces.append(((2.00 + 0.075 * side, 0.10), (2.00 + 0.075 * side, 0.10 + nib)))
    k = 1000.0
    walls = [{"wall_id": w, "t_m": t, "family": f"{t:.2f}", "centreline": [(a[0] * k, a[1] * k), (b[0] * k, b[1] * k)],
              "gross_lm": round(math.dist(a, b), 9), "columns_in_wall_lm": 0.0} for w, t, a, b in bands]
    ev = {"face_segments": [((a[0] * k, a[1] * k), (b[0] * k, b[1] * k)) for a, b in faces],
          "glazing_segments": [], "glazing_arcs": [], "door_arcs": [{"c": (2000.0, 200.0), "r": 750.0}]}
    return V2.measure(walls, unit_m=0.001, openings=[], columns_m=[], floor="Q", evidence=ev)


def _p_phys(r):
    return {b["family"]: b["physical_blockwork_lm"] for b in r["by_thickness"]}["0.15"]


def test_l6_rule_constant_is_the_l_p9_04_value():
    assert V2.JAMB_STUB_MIN_M == 0.05


def test_l6_nib_at_threshold_stays_wall():
    r = _floor_l6(0.050)
    d = r["doorways"][0]
    assert d["face_to_face_m"] == pytest.approx(0.90, abs=1e-4)
    assert d["jamb_stub"]["status"] == "WALL" and d["gap_m"] == pytest.approx(0.85, abs=1e-4)
    assert _p_phys(r) == pytest.approx(2.55, abs=1e-6)
    assert {b["family"]: b["arch_run_lm"] for b in r["by_thickness"]}["0.15"] == pytest.approx(3.40, abs=1e-6)
    broken = 3.40 - d["face_to_face_m"]                      # BROKEN pre-T-169: the whole gap is doorway
    assert abs(broken - 2.55) > 0.04


def test_l6_adverse_nib_below_threshold_is_listed_artefact():
    r = _floor_l6(0.045)
    d = r["doorways"][0]
    assert d["jamb_stub"]["status"] == "BELOW_L-P9-04_LISTED"
    assert d["gap_m"] == pytest.approx(0.90, abs=1e-4) and _p_phys(r) == pytest.approx(2.50, abs=1e-6)
    assert [s["stub_m"] for s in r["jamb_stubs"]] == [pytest.approx(0.045, abs=1e-4)]   # listed, not dropped


# ======================================================================================== L7 porch floor vs soffit
PORCH = [(0, 0), (4.6, 0), (4.6, 4.0), (0, 4.0)]
FLOOR = [(0, -0.9), (2.0, -0.9), (2.0, 0), (4.6, 0), (4.6, 4.0), (0, 4.0)]
STUB = [(4.2, 2.6), (4.6, 2.6), (4.6, 4.0), (4.2, 4.0)]
BEAM = [(0, 3.75), (4.6, 3.75), (4.6, 4.0), (0, 4.0)]


def test_l7_two_surfaces_by_hand():
    r = LS.porch_surfaces(FLOOR, [STUB], PORCH, [BEAM])
    assert r["floor_m2"] == pytest.approx(19.64, abs=TOL)
    assert r["soffit_m2"] == pytest.approx(17.25, abs=TOL)
    assert r["floor_only_m2"] == pytest.approx(2.85, abs=TOL)
    assert r["soffit_only_m2"] == pytest.approx(0.46, abs=TOL)
    assert r["readd_m2"] == pytest.approx(r["soffit_m2"], abs=1e-9)


def test_l7_broken_copied_soffit_rejected():
    r = LS.porch_surfaces(FLOOR, [STUB], PORCH, [BEAM])
    assert abs(r["floor_m2"] - 17.25) > 1.0                   # BROKEN: soffit := floor = 19.64, +2.39 m2


def test_l7_adverse_same_outline_no_beam():
    r = LS.porch_surfaces(PORCH, [], PORCH, [])                # a flush slab over the same outline: equal by geometry
    assert r["floor_m2"] == pytest.approx(r["soffit_m2"], abs=TOL) == 18.40
    assert r["floor_only_m2"] == pytest.approx(0.0, abs=TOL) and r["soffit_only_m2"] == pytest.approx(0.0, abs=TOL)
