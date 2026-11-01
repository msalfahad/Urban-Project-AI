"""T-438 straight-part reading test on a non-Alsenan hand fixture (Villa K438) with adverse cases.

Villa K438 (hand-made, every figure computed by hand):
- GF FFL +0.15 -> 1F FFL +2.47: rise 2.32 m. Nosing projection 0.040, going 0.280.
- Flight S (axis s, rising toward +s): riser faces at 0.10 + 0.28 k, k = 0 .. 9 (10 edges): 0.10, 0.38, ..., 2.62;
  nosings 0.040 downhill (0.06, 0.34, ..., 2.58).
- Corner landing, then flight A (axis y, rising toward +y): faces 0.00, 0.28, 0.56, 0.84, 1.12, 1.40 (6 edges, the
  last is the 1F floor edge); nosings -0.04, 0.24, ..., 1.36.
- 1F PLAN (cut above the whole stair, VISIBLE): every edge as a nosing + face pair -> 10 + 6 = 16 risers.
- STRUCTURAL plan: faces only, the same 16.
- GF PLAN: flight S edges 1 .. 6 as pairs (below its cut), edges 7 .. 10 as single OVERHEAD nosings 1.74 / 2.02 / 2.30
  / 2.58; flight A as single overhead nosings 0.24 .. 1.36 (5): the first A edge is NOT drawn -> 15 risers.
- Riser check: 2.32 / 16 = 0.145 (FAIL, below 0.150); 2.32 / 15 = 0.154667 (PASS). The governing count is still 16:
  checks never select (R-T438-4); the drawn stair's riser is flagged, never replaced (owner S-8).
- A reader who mixes the line families on the GF plan gets a 'short tread' 1.74 - 1.50 = 0.24 = 0.28 - 0.04 and a run
  0.10 -> 2.58 = 2.48 instead of 2.52 (R-T438-1).
"""

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t438"))
import t438_rules as R  # noqa: E402

E = R.Edge
P, G = 0.04, 0.28
S_FACES = [round(0.10 + G * k, 6) for k in range(10)]
A_FACES = [round(G * k, 6) for k in range(6)]


def pairs(faces):
    return tuple([E(f, R.FACE) for f in faces] + [E(round(f - P, 6), R.NOSING) for f in faces])


def s_readings():
    gf = tuple([E(f, R.FACE) for f in S_FACES[:6]] + [E(round(f - P, 6), R.NOSING) for f in S_FACES[:6]] +
               [E(x, R.NOSING) for x in (1.74, 2.02, 2.30, 2.58)])
    return [R.Reading("PLAN_1F", R.VISIBLE, pairs(S_FACES)),
            R.Reading("STRUCT", R.STRUCTURAL, tuple(E(f, R.FACE) for f in S_FACES)),
            R.Reading("PLAN_GF", R.OVERHEAD, gf)]


def a_readings(gf_lines=(0.24, 0.52, 0.80, 1.08, 1.36), struct=A_FACES):
    return [R.Reading("PLAN_1F", R.VISIBLE, pairs(A_FACES)),
            R.Reading("STRUCT", R.STRUCTURAL, tuple(E(f, R.FACE) for f in struct)),
            R.Reading("PLAN_GF", R.OVERHEAD, tuple(E(x, R.NOSING) for x in gf_lines))]


# ---------------- normal ----------------

def test_flight_s_all_three_agree_once_families_are_kept():
    g = R.governing(s_readings(), P, +1)
    assert g["status"] == "GOVERNED" and g["governing"] == "PLAN_1F" and g["risers"] == 10
    assert g["table"]["STRUCT"]["class"] == R.AGREES
    assert g["table"]["PLAN_GF"]["class"] == R.AGREES and g["table"]["PLAN_GF"]["missing_faces"] == []
    assert R.goings(g["faces"]) == [0.28] * 9
    assert g["faces"][-1] - g["faces"][0] == pytest.approx(2.52)


def test_mixed_family_reading_explains_the_short_tread():
    gf = s_readings()[2]
    # the hidden layer of the GF plan carries the FACES below the cut and the overhead NOSINGS beyond it
    hid = sorted(e.s for e in gf.edges if e.family == R.FACE) + [1.74, 2.02, 2.30, 2.58]
    assert R.goings(hid) == [0.28] * 5 + [0.24] + [0.28] * 3   # 1.50 face -> 1.74 nosing = 0.28 - 0.04
    fn = [x for x in R.mixed_family_goings(gf) if x[1] == R.FACE and x[2] == R.NOSING]
    assert fn and all(round(x[0], 6) == 0.24 for x in fn)       # every face -> next nosing step is going - projection
    assert round(hid[-1] - hid[0], 6) == 2.48                 # the misread run, 0.04 short of 2.52


def test_flight_a_overhead_is_a_partial_projection_not_a_count():
    g = R.governing(a_readings(), P, +1)
    assert g["status"] == "GOVERNED" and g["risers"] == 6
    t = g["table"]["PLAN_GF"]
    assert t["class"] == R.PARTIAL and t["edges"] == 5 and t["missing_faces"] == [0.0]


def test_checks_are_reported_and_never_select():
    whole_gov = 10 + 6
    whole_gf = 10 + 5
    c16 = R.checks(whole_gov, 2.32, G)
    c15 = R.checks(whole_gf, 2.32, G)
    assert c16["riser_m"] == pytest.approx(0.145) and c16["riser_check"] == "FAIL"
    assert c15["riser_m"] == pytest.approx(0.154667, abs=1e-6) and c15["riser_check"] == "PASS"
    # the governing reading does not change because the other one passes the check
    g = R.governing(a_readings(), P, +1)
    assert g["risers"] == 6 and g["governing"] == "PLAN_1F"


def test_quantity_effects_by_hand():
    # sec = sqrt(1 + (0.17 / 0.28)^2) = sqrt(1.368622) = 1.169881; 2.0 x (0.15 x 1.169881 + 0.085) = 0.520964
    assert R.flight_m3(2.0, 0.15, 0.17, 0.28) == pytest.approx(0.520964, abs=1e-6)
    assert R.plate_m3(1.5, 0.15) == pytest.approx(0.225)
    assert R.steps_m3(2.0, 0.17) == pytest.approx(0.17)


def test_mirror_and_walking_direction_invariance():
    m = [R.Reading(r.name, r.view, tuple(E(-e.s, e.family) for e in r.edges)) for r in a_readings()]
    g = R.governing(m, P, -1)
    assert g["risers"] == 6 and g["table"]["PLAN_GF"]["class"] == R.PARTIAL
    assert g["table"]["PLAN_GF"]["missing_faces"] == [0.0]
    rev = [R.Reading(r.name, r.view, tuple(reversed(r.edges))) for r in s_readings()]
    assert R.governing(rev, P, +1)["risers"] == 10


# ---------------- adverse ----------------

def test_riser_count_taken_from_the_plan_that_fits_best_is_refused():
    with pytest.raises(R.ReadingError, match="never chosen by fit"):
        R.choose_by_fit(a_readings(), rise=2.32)
    # and with no visible reading the overhead count (which passes the check) is NOT taken: HELD
    g = R.governing(a_readings()[1:], P, +1)
    assert g["status"] == R.HELD and g["faces"] is None and g["cause"] == "NO_VISIBLE_READING"


def test_overhead_line_where_the_governing_view_has_none_is_a_conflict():
    g = R.governing(a_readings(gf_lines=(0.10, 0.52, 0.80, 1.08, 1.36)), P, +1)
    assert g["status"] == R.HELD and g["faces"] is None and g["cause"] == "OVERHEAD_DIFFERENT_LAYOUT"
    assert g["table"]["PLAN_GF"]["class"] == R.CONFLICT


def test_visible_and_structural_disagree_is_held():
    g = R.governing(a_readings(struct=A_FACES[1:]), P, +1)
    assert g["status"] == R.HELD and g["faces"] is None and "VISIBLE_AND_STRUCTURAL_DISAGREE" in g["cause"]


def test_no_structural_reading_is_held():
    g = R.governing([a_readings()[0], a_readings()[2]], P, +1)
    assert g["status"] == R.HELD and "no structural" in g["cause"]


@pytest.mark.parametrize("bad", [
    lambda: R.governing([R.Reading("X", R.VISIBLE, (E(1400.0, R.FACE),))], P, +1),       # mm as m
    lambda: R.governing(a_readings(), 40, +1),                                             # projection in mm
    lambda: R.governing(a_readings(), P, 0),                                               # no direction
    lambda: R.governing([R.Reading("X", R.VISIBLE, (E(0.1, R.FACE), E(0.1, R.FACE)))], P, +1),  # edge twice
    lambda: R.governing([R.Reading("X", "PHOTO", (E(0.1, R.FACE),))], P, +1),            # unknown view
    lambda: R.governing([R.Reading("X", R.VISIBLE, (E(0.1, "RISER"),))], P, +1),          # unknown family
    lambda: R.governing([R.Reading("X", R.VISIBLE, ())], P, +1),                          # empty
    lambda: R.governing(a_readings() + a_readings()[:1], P, +1),                          # reading twice
    lambda: R.checks(15.0, 2.32, G),                                                      # float count
    lambda: R.checks(16, None, G),                                                        # missing rise
    lambda: R.checks(16, 2320, G),                                                        # rise in mm
    lambda: R.flight_m3(2.0, None, 0.17, 0.28),                                           # waist missing: never 0
    lambda: R.plate_m3(1.5, 150),                                                         # t in mm
])
def test_refused(bad):
    with pytest.raises(R.ReadingError):
        bad()
