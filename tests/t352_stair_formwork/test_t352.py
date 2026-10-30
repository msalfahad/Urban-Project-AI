"""T-352 stair formwork: rules on a hand-calculated villa K (not the development villa) + the development villa pinned
from the committed inputs (no private file is read here).

Villa K (hand figures, m; riser 0.175, going 0.28, waist 0.15, width 1.10):
  F1 straight flight, 8 riser lines (7 goings), east side open to the stair well, west side on a block wall:
     sec = hypot(0.28, 0.175) / 0.28 = 1.179247; sloped 7 x 0.330189 = 2.311324
     side profile = 7 x 1/2 x 0.175 x 0.28 + 0.15 x 2.311324 = 0.171500 + 0.346699 = 0.518199 m2 (FORMED, well side)
     wall side: HELD 0 .. 0.518199 (sequence not printed)
  LQ quarter landing 1.10 x 1.10 x 0.15: open edge 1.10 x 0.15 = 0.165 m2 FORMED; wall edge HELD 0 .. 0.165
  F2 flight off the landing, 5 riser lines: 4 x 0.0245 + 0.15 x 4 x 0.330189 = 0.098 + 0.198114 = 0.296114 m2
  last 0.05 m of F1 (s 1.91 .. 1.96): 0.05 x (7 x 0.175 + 0.176887) - 0.625 x (1.96^2 - 1.91^2) / 2 = 0.009626 m2
"""

import csv
import io
import json
import math
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "research" / "agents_t352"
sys.path.insert(0, str(HERE))
import t352_alsenan as A  # noqa: E402
import t352_rules as R  # noqa: E402

r, g, t, w = 0.175, 0.28, 0.15, 1.10


def face(fid, **kw):
    base = dict(face_id=fid, stair="K-1", piece="F1", kind="FLIGHT_SIDE", side="east", contact="VOID",
                status="CALCULATED", evidence="DRAWING-CONFIRMED", line_id="L-K1", m2=0.5)
    base.update(kw)
    return R.Face(**base)


# ---------------------------------------------------------------- villa K, normal cases
def test_flight_side_profile_by_hand():
    assert R.flight_profile(r, g, t, 8) == pytest.approx(0.518199, abs=1e-6)
    assert R.flight_profile(r, g, t, 5) == pytest.approx(0.296114, abs=1e-6)


def test_side_area_equals_volume_over_width():
    steps = 7 * 0.5 * r * g * w
    waist = t * w * math.hypot(7 * g, 7 * r)
    assert R.flight_profile(r, g, t, 8) == pytest.approx((steps + waist) / w, abs=1e-9)


def test_head_strip_by_hand_and_strips_sum_to_the_whole():
    assert R.profile_strip(r, g, t, 8, 1.91, 1.96) == pytest.approx(0.009626, abs=1e-6)
    parts = sum(R.profile_strip(r, g, t, 8, a, b) for a, b in ((0, 0.4), (0.4, 1.37), (1.37, 1.96)))
    assert parts == pytest.approx(R.flight_profile(r, g, t, 8), abs=1e-12)


def test_units_mm_cm_m_and_unknown_refused():
    assert R.flight_profile(R.to_m(175, "mm"), R.to_m(28, "cm"), R.to_m(0.15, "m"), 8) == pytest.approx(0.518199, abs=1e-6)
    with pytest.raises(R.StairFormworkError):
        R.to_m(175, "in")


def test_villa_k_ledger_and_fill():
    fs = R.check_faces([
        face("K-01", m2=R.flight_profile(r, g, t, 8)),
        face("K-02", side="west", contact="WALL", status="HELD", evidence="HELD", m2=None, lo=0.0,
             hi=R.flight_profile(r, g, t, 8)),
        face("K-03", piece="LQ", kind="LANDING_EDGE", side="south open", m2=1.10 * 0.15),
        face("K-04", piece="LQ", kind="LANDING_EDGE", side="west wall", contact="WALL", status="HELD",
             evidence="HELD", m2=None, lo=0.0, hi=1.10 * 0.15),
        face("K-05", piece="F2", m2=R.flight_profile(r, g, t, 5)),
    ])
    tot = R.totals(fs)
    assert tot["calculated_m2"] == pytest.approx(0.518199 + 0.165 + 0.296114, abs=1e-6)
    rows = {x["status"]: x for x in R.fill_rows(fs)}
    assert rows["HELD"]["m2"] is None and rows["HELD"]["hi"] == pytest.approx(0.683199, abs=1e-6)
    text = R.write_fill_csv(R.fill_rows(fs))
    held = [x for x in csv.DictReader(io.StringIO(text)) if x["status"] == "HELD"]
    assert held and all(x["m2"] == "" for x in held)


# ---------------------------------------------------------------- adverse
def test_adverse_generated_winder_refused():
    with pytest.raises(R.StairFormworkError, match="S-9"):
        face("K-W", kind="WINDER", drawn=False).check()
    with pytest.raises(R.StairFormworkError, match="S-9"):
        face("K-W", kind="WINDER", count_agrees=False).check()


def test_adverse_side_form_on_a_wall_bearing_side_refused():
    with pytest.raises(R.StairFormworkError, match="never CALCULATED"):
        face("K-02", contact="WALL").check()
    with pytest.raises(R.StairFormworkError, match="never CALCULATED"):
        face("K-02", contact="MEMBER").check()


def test_adverse_stair_soffit_counted_with_the_slab_soffit_refused():
    soffit = face("K-S", kind="SOFFIT", plane="1F-soffit:K-PANEL-7")
    with pytest.raises(R.StairFormworkError, match="already measured"):
        R.claim_existing_planes([soffit], {"1F-soffit:K-PANEL-7": "SLAB-SOFFIT-K7"})
    with pytest.raises(R.StairFormworkError, match="one surface"):
        R.check_faces([soffit, face("K-S2", kind="SOFFIT", plane="1F-soffit:K-PANEL-7")])


def test_adverse_held_face_as_zero_refused():
    with pytest.raises(R.StairFormworkError, match="never 0"):
        face("K-H", status="HELD", evidence="HELD", contact="WALL", m2=0.0).check()
    with pytest.raises(R.StairFormworkError, match="hidden 0"):
        face("K-H", status="HELD", evidence="HELD", contact="WALL", m2=None, lo=0.0, hi=0.0).check()
    with pytest.raises(R.StairFormworkError, match="hi 0"):
        R.write_fill_csv([{"line_id": "L-K", "status": "HELD", "faces": 1, "m2": None, "lo": 0.0, "hi": 0.0,
                           "face_ids": "K-H"}])
    with pytest.raises(R.StairFormworkError, match="m2"):
        R.write_fill_csv([{"line_id": "L-K", "status": "HELD", "faces": 1, "m2": 0.0, "lo": None, "hi": None,
                           "face_ids": "K-H"}])


def test_adverse_missing_waist_or_riser_never_computed():
    with pytest.raises(R.StairFormworkError, match="never computed"):
        R.flight_profile(r, g, None, 8)
    with pytest.raises(R.StairFormworkError):
        R.flight_profile(0.0, g, t, 8)


def test_adverse_face_twice_or_from_the_existing_ledger_refused():
    with pytest.raises(R.StairFormworkError, match="twice"):
        R.check_faces([face("K-01"), face("K-01")])
    with pytest.raises(R.StairFormworkError, match="never added again"):
        R.check_faces([face("R4-321")], existing_ids=["R4-321"])


def test_adverse_conflict_collapsed_to_one_end_refused():
    with pytest.raises(R.StairFormworkError, match="both readings"):
        face("K-C", status="CONFLICT", evidence="HELD", m2=None, lo=0.70, hi=None).check()


def test_adverse_strip_outside_the_flight_refused():
    with pytest.raises(R.StairFormworkError, match="outside"):
        R.profile_strip(r, g, t, 8, 1.90, 2.10)


# ---------------------------------------------------------------- development villa (pinned)
@pytest.fixture(scope="module")
def BUILT():
    return A.build()


def test_committed_outputs_are_a_fresh_build():
    for path, text in A.outputs().items():
        assert path.read_text(encoding="utf-8") == text, path.name


def test_alsenan_valued_faces(BUILT):
    faces, existing, xcheck = BUILT
    calc = {f.face_id: f for f in faces if f.status == "CALCULATED"}
    assert len(calc) == 7 and all(f.contact == "VOID" for f in calc.values())
    assert sum(f.m2 for f in calc.values()) == pytest.approx(4.105400, abs=1e-6)
    pinned = {"T352-04": 0.831293, "T352-08": 0.851277, "T352-15": 0.834477, "T352-21": 0.775865,
              "T352-24": 0.184000, "T352-26": 0.314244, "T352-27": 0.314244}
    for k, v in pinned.items():
        assert calc[k].m2 == pytest.approx(v, abs=1e-6), k


def test_alsenan_side_profiles_agree_with_the_verified_concrete(BUILT):
    _, _, xc = BUILT
    for k in ("ST01-MS1-U", "ST01-MS2-U", "ST02-RS-S", "ST02-RS-A"):
        assert xc[k][0] == pytest.approx(xc[k][1], abs=1e-5), k
    for rd in ("A", "B"):
        assert xc["ST01-MS1-L"][rd][0] == pytest.approx(xc["ST01-MS1-L"][rd][1], abs=1e-5)
    # MS2-L: named residual = the 12th-triangle sliver below the MS2-LD-W plate (T-258), 0.000057 m2
    assert xc["ST01-MS2-L"][1] - xc["ST01-MS2-L"][0] == pytest.approx(0.000057, abs=2e-6)
    assert xc["ST01-MS2-L"][2]["foot_geo"] == pytest.approx(xc["ST01-MS2-L"][2]["foot_t192"], abs=1e-6)


def test_alsenan_held_never_zero_and_conflict_kept(BUILT):
    faces, _, _ = BUILT
    by = {f.face_id: f for f in faces}
    assert by["T352-01"].status == "CONFLICT" and by["T352-01"].lo < by["T352-01"].hi
    for f in faces:
        if f.status != "CALCULATED":
            assert f.m2 is None and (f.hi is None or f.hi > 0)
    fill = list(csv.DictReader(io.StringIO((HERE / "T199_FILL_T352_ADDENDUM.csv").read_text(encoding="utf-8"))))
    assert all(x["m2"] == "" for x in fill if x["status"] != "CALCULATED")
    assert all(x["hi"] != "0.000000" for x in fill)


def test_alsenan_no_face_twice_and_r4_339_superseded(BUILT):
    faces, existing, _ = BUILT
    ex = {r["face_id"] for r in existing}
    assert not ex & {f.face_id for f in faces}
    rows = {r["face_id"]: r for r in csv.DictReader(io.StringIO(
        (HERE / "EXISTING_STAIR_FACES_T332.csv").read_text(encoding="utf-8")))}
    assert rows["R4-339"]["t352_treatment"].startswith("SUPERSEDED")
    assert "R4-321" in rows and "R4-327" in rows and "R4-337.LANE" in rows


def test_alsenan_bound_to_candidate_stair_lines(BUILT):
    faces, _, _ = BUILT
    cand = json.loads((ROOT / "research" / "agents_t332" / "CANDIDATE_V3021_CONCRETE_LINES.json").read_text())
    lines = cand["lines"]
    ids = {l["line_id"]: l for l in (lines if isinstance(lines, list) else lines.values())}
    for f in faces:
        assert f.line_id in ids and ids[f.line_id]["item_code"] == "STR.CONC.STAIR", f.face_id
