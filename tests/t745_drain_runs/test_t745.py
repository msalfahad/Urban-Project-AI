"""T-745: B12-02 drainage runs in lm, research/agents_t745/t745_runs.py (not wired).

Hand-made synthetic villa N745 (not the development villa). Sheet units u; the plot is printed 20.00 x 10.00 m and
drawn 500 x 250 u, so 1 u = 0.04 m. Two bathrooms B1 / B2 mirrored about x = 250 u.
  K collector (6in printed) y = 20, from x = 50 to 440, drawn dash-dot: dashes 40 u, gaps 10 u, one dot per gap
      (8 dashes, 7 gaps) -> one run 390 u = 15.600 m
  M branch B1 WC  (100, 80) -> (100, 30) -> (90, 20)       50 + 14.142136 u = 2.565685 m, diameter not printed
  M branch B2 WC  mirrored: (400, 80) -> (400, 30) -> (410, 20)               = 2.565685 m, diameter not printed
  M branch B1 FD  (150, 80) -> (150, 60), dots at y 55 / 50 / 45, (150, 40) -> (150, 20)
      -> one run 60 u = 2.400 m (the dotted part is pipe), diameter not printed
  R waste B1 basin (130, 100) -> (150, 100) -> (150, 85)  35 u = 1.400 m, diameter not printed
  M symbol mark (300, 200) -> (301, 200) isolated, 0.04 m: not a pipe
Risers: RWP 4in from a printed roof +7.00 to a printed GF +-0.00 with 'free discharge 15 cm above FFL' = 6.850 m;
SS 4in 1F +3.60 to GF where the GF level is not printed: HELD (never 0); the same with printed neighbour levels
+0.30 / +1.00: BOUNDED 2.60 .. 3.30 m. Water supply is not drawn: HELD_NOT_DRAWN row, lm None.
HAND TRUTH plan lm: GF BUILDING_DRAIN 6in MEASURED 15.600; SOIL_WASTE_BRANCH unprinted 2.565685 x 2 + 2.400 =
7.531371 (HELD_DIAMETER_UNPRINTED, 3 runs); FIXTURE_WASTE unprinted 1.400 (1 run).
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t745"))
import t745_runs as R  # noqa: E402

K = 0.04


def dashed(x0, x1, y, dash=40, gap=10):
    segs, dots, x = [], [], x0
    while x < x1:
        e = min(x + dash, x1)
        segs.append(((x, y), (e, y)))
        if e < x1:
            dots.append((e + gap / 2, y))
        x = e + gap
    return segs, dots


def poly(*pts):
    return [(pts[i], pts[i + 1]) for i in range(len(pts) - 1)]


def villa(transform=lambda p: p):
    t = transform
    K_segs, K_dots = dashed(50, 440, 20)
    M_segs = (poly((100, 80), (100, 30), (90, 20)) + poly((400, 80), (400, 30), (410, 20))
              + poly((150, 80), (150, 60)) + poly((150, 40), (150, 20)) + poly((300, 200), (301, 200)))
    M_dots = [(150, 55), (150, 50), (150, 45)]
    R_segs = poly((130, 100), (150, 100), (150, 85))
    tt = lambda segs: [(t(a), t(b)) for a, b in segs]  # noqa: E731
    td = lambda ds: [t(d) for d in ds]  # noqa: E731
    k_runs = R.build_runs(tt(K_segs), td(K_dots), floor="GF", pen="K", scale=K)
    m_runs = R.build_runs(tt(M_segs), td(M_dots), floor="GF", pen="M", scale=K)
    r_runs = R.build_runs(tt(R_segs), [], floor="GF", pen="R", scale=K)
    for r in k_runs:
        r.system = R.BUILDING_DRAIN
    for r in m_runs:
        r.system = R.SOIL_WASTE_BRANCH
    for r in r_runs:
        r.system = R.FIXTURE_WASTE
    runs = k_runs + m_runs + r_runs
    R.flag_symbol_marks(runs, K)
    refused = R.label_runs(runs, [(t((250, 20)), 6)], tol=1.0)
    return runs, refused


def rows_of(runs, risers=(), not_drawn=()):
    rows, marks = R.table(runs, list(risers), K, not_drawn=not_drawn)
    return {(r["kind"], r["floor"], r["system"], r["diameter_in"], r["status"]): r for r in rows}, marks


# ------------------------------------------------------------------------------------------------- normal case
def test_hand_truth_plan_lm():
    runs, refused = villa()
    assert refused == []
    rows, marks = rows_of(runs)
    assert rows[("PLAN", "GF", R.BUILDING_DRAIN, 6, R.MEASURED)]["lm"] == pytest.approx(15.600, abs=1e-3)
    assert rows[("PLAN", "GF", R.BUILDING_DRAIN, 6, R.MEASURED)]["runs"] == 1
    br = rows[("PLAN", "GF", R.SOIL_WASTE_BRANCH, None, R.HELD_DIAMETER)]
    assert br["runs"] == 3
    assert br["lm"] == pytest.approx(2 * (50 + math.hypot(10, 10)) * K + 2.400, abs=1e-3)   # 7.531
    assert rows[("PLAN", "GF", R.FIXTURE_WASTE, None, R.HELD_DIAMETER)]["lm"] == pytest.approx(1.400, abs=1e-3)
    assert [m["len_m"] for m in marks] == [0.04]


def test_dash_dot_collector_is_one_run_with_its_gaps():
    runs, _ = villa()
    k = [r for r in runs if r.pen == "K"]
    assert len(k) == 1 and len(k[0].bridges) == 7 and len(k[0].segments) == 8
    assert k[0].length_units() == pytest.approx(390.0)


def test_dotted_branch_is_bridged_once():
    runs, _ = villa()
    fd = [r for r in runs if r.pen == "M" and any(a[0] == 150 for a, b in r.segments)]
    assert len(fd) == 1 and len(fd[0].bridges) == 1
    assert fd[0].length_units() * K == pytest.approx(2.400)


def test_mirrored_bathrooms_measure_alike():
    runs, _ = villa()
    wc = sorted(r.length_units() * K for r in runs if r.pen == "M" and len(r.segments) == 2 and not r.bridges)
    assert wc[0] == pytest.approx(wc[1]) == pytest.approx(2.565685, abs=1e-6)


@pytest.mark.parametrize("transform", [
    lambda p: (p[1], -p[0]),                         # sheet rotated 90 degrees
    lambda p: (500 - p[0], p[1]),                    # sheet mirrored
])
def test_rotated_or_mirrored_sheet_same_census(transform):
    a, _ = villa()
    b, refused = villa(transform)
    assert refused == []
    ra, _ = rows_of(a)
    rb, _ = rows_of(b)
    assert {k: v["lm"] for k, v in ra.items()} == pytest.approx({k: v["lm"] for k, v in rb.items()})


# ------------------------------------------------------------------------------------------------ adverse cases
def test_unprinted_diameter_is_never_defaulted():
    runs, _ = villa()
    for r in runs:
        if r.pen in ("M", "R"):
            assert r.diameter_in is None
            assert R.run_status(r) in (R.HELD_DIAMETER,) or r.symbol_mark


def test_gap_without_a_dot_is_not_bridged():
    runs = R.build_runs(poly((0, 0), (10, 0)) + poly((15, 0), (25, 0)), [], floor="GF", pen="M", scale=K)
    assert len(runs) == 2 and all(not r.bridges for r in runs)


def test_gap_off_line_is_not_bridged_even_with_a_dot():
    runs = R.build_runs(poly((0, 0), (10, 0)) + poly((15, 5), (25, 5)), [(12.5, 2.5)], floor="GF", pen="R",
                        scale=K)
    assert len(runs) == 2


def test_gap_longer_than_the_limit_is_not_bridged():
    far = R.BRIDGE_MAX_M / K + 5
    runs = R.build_runs(poly((0, 0), (10, 0)) + poly((10 + far, 0), (20 + far, 0)), [(10 + far / 2, 0)],
                        floor="GF", pen="M", scale=K)
    assert len(runs) == 2


def test_pipe_stopping_at_a_drain_body_is_not_bridged_without_a_dot():
    # the FD square sits in the 4.5 u gap between two runs of one pen (development-villa case 1F WC - FD - WC)
    runs = R.build_runs(poly((0, 0), (56, 0)) + poly((60.5, 0), (70.7, 0)), [], floor="1F", pen="M", scale=K)
    assert len(runs) == 2


def test_duplicate_segments_counted_once():
    s = poly((0, 0), (100, 0))
    runs = R.build_runs(s + [((100, 0), (0, 0))] + s, [], floor="GF", pen="K", scale=K)
    assert len(runs) == 1 and runs[0].length_units() == pytest.approx(100.0)


def test_label_in_wrong_units_lands_on_nothing_and_is_refused():
    runs, _ = villa()
    refused = R.label_runs(runs, [((250 * K, 20 * K), 6)], tol=1.0)   # metres passed as sheet units
    assert refused and refused[0][2] == 0


def test_label_on_two_runs_is_refused():
    runs, _ = villa()
    refused = R.label_runs(runs, [((150, 20), 4)], tol=1.0)             # FD branch meets the collector here
    assert refused and refused[0][2] == 2


def test_scale_refused_when_printed_sides_disagree():
    assert R.scale_from_dimensions([(20.0, 500.0), (10.0, 250.0)]) == pytest.approx(0.04)
    with pytest.raises(R.RefusedSheet):
        R.scale_from_dimensions([(20.0, 500.0), (10.0, 240.0)])     # distorted plot
    with pytest.raises(R.RefusedSheet):
        R.scale_from_dimensions([(20000.0, 500.0), (10.0, 250.0)])  # one side read in mm
    with pytest.raises(R.RefusedSheet):
        R.scale_from_dimensions([(20.0, 500.0)])


def test_risers_measured_bounded_held_never_zero():
    rwp = R.Riser("RWP-1", R.RAINWATER_PIPE, 4, top_level=7.00, bottom_level=0.00, bottom_offset_m=0.15, note="")
    ss_held = R.Riser("SS-1", R.SOIL_STACK, 4, top_level=3.60, bottom_level=None, note="")
    ss_b = R.Riser("SS-2", R.SOIL_STACK, 4, top_level=3.60, bottom_level=None, bottom_bounds=(1.00, 0.30), note="")
    assert rwp.lm() == (R.MEASURED, 6.85, 6.85)
    assert ss_held.lm() == (R.HELD_LEVEL, None, None)
    assert ss_b.lm() == (R.BOUNDED, 2.6, 3.3)
    assert R.Riser("x", R.SOIL_STACK, 4, None, 0.0).lm()[0] == R.HELD_LEVEL
    with pytest.raises(ValueError):
        R.Riser("bad", R.SOIL_STACK, 4, top_level=1.0, bottom_level=2.0).lm()


def test_table_keeps_held_unvalued_and_never_mixes_plan_with_risers():
    runs, _ = villa()
    risers = [R.Riser("RWP-1", R.RAINWATER_PIPE, 4, 7.00, 0.00, 0.15),
              R.Riser("SS-1", R.SOIL_STACK, 4, 3.60, None)]
    rows, _ = rows_of(runs, risers, not_drawn=[(R.COLD_SUPPLY, "drainage-only set")])
    assert rows[("RISER", "ALL", R.RAINWATER_PIPE, 4, R.MEASURED)]["lm"] == pytest.approx(6.85)
    assert rows[("RISER", "ALL", R.SOIL_STACK, 4, R.HELD_LEVEL)]["lm"] is None
    assert rows[("-", "ALL", R.COLD_SUPPLY, None, R.HELD_NOT_DRAWN)]["lm"] is None
    t = R.totals_by_state(list(rows.values()))
    assert t["PLAN|MEASURED"]["lm"] == pytest.approx(15.6)
    assert t["RISER|MEASURED"]["lm"] == pytest.approx(6.85)
    assert t["RISER|HELD_LEVEL_UNPRINTED"]["unvalued_rows"] == 1
    assert t["-|HELD_NOT_DRAWN"]["unvalued_rows"] == 1
    assert t["-|HELD_NOT_DRAWN"]["lm"] is None and t["RISER|HELD_LEVEL_UNPRINTED"]["lm"] is None


def test_symbol_mark_touching_a_run_is_a_pipe():
    runs = R.build_runs(poly((0, 0), (100, 0)), [], floor="GF", pen="M", scale=K)
    stub = R.build_runs(poly((100, 0), (101, 0.5)), [], floor="GF", pen="R", scale=K, prefix="GF-R")
    allr = R.flag_symbol_marks(runs + stub, K)
    assert not any(r.symbol_mark for r in allr)


def test_endpoint_coverage_names_a_drain_with_no_pipe():
    runs, _ = villa()
    cov = R.endpoint_coverage([(150, 82), (200, 200)], runs, tol=4.0)
    assert cov[0] and cov[1] == []


def test_committed_alsenan_output_re_adds():
    """the committed development-villa output (counts and lm only) is internally consistent: every row re-adds from
    its runs / risers, statuses never mixed, HELD never valued 0, no coordinates in the file. V2 (r2): every plan run of
    the not-to-scale sheets is HELD_SCHEMATIC_NOT_TO_SCALE with its scaled figure apart; risers keep printed levels."""
    import json
    out = json.loads((ROOT / "research" / "agents_t745" / "out" / "T745_ALSENAN_RUNS.json").read_text())
    assert out["method"] == R.METHOD_ID == "DRAIN_RUN_CENSUS_T745_V2"
    assert set(out["sheet_basis"].values()) == {R.BASIS_SCHEMATIC}
    for row in out["rows"]:
        if row["kind"] == "PLAN":
            assert row["status"] == R.HELD_SCHEMATIC and row["lm"] is None and row["lm_high"] is None
            assert row["info_label"] == R.SCALED_INFO_LABEL
            runs = [r for r in out["runs"] if (r["floor"], r["system"], r["diameter_in"], r["status"])
                    == (row["floor"], row["system"], row["diameter_in"], row["status"])]
            assert len(runs) == row["runs"] and all(r["lm"] is None for r in runs)
            assert sum(r["scaled_info_lm"] for r in runs) == pytest.approx(row["scaled_info_lm"], abs=0.002)
        elif row["kind"] == "RISER":
            zs = [z for z in out["risers"] if (z["system"], z["diameter_in"], z["lm"]["status"])
                  == (row["system"], row["diameter_in"], row["status"])]
            assert len(zs) == row["runs"]
            if row["status"] == R.HELD_LEVEL:
                assert row["lm"] is None
            else:
                assert sum(z["lm"]["low"] for z in zs) == pytest.approx(row["lm"])
                assert sum(z["lm"]["high"] for z in zs) == pytest.approx(row["lm_high"])
        else:
            assert row["status"] == R.HELD_NOT_DRAWN and row["lm"] is None
    t = out["totals_by_state"]
    assert "PLAN|MEASURED" not in t and "PLAN|HELD_DIAMETER_UNPRINTED" not in t
    assert t["PLAN|HELD_SCHEMATIC_NOT_TO_SCALE"]["lm"] is None
    assert t["PLAN|HELD_SCHEMATIC_NOT_TO_SCALE"]["scaled_info_lm"] == pytest.approx(119.163, abs=0.002)
    assert t["RISER|MEASURED"]["lm"] == pytest.approx(32.40) and t["RISER|BOUNDED"]["lm_high"] == pytest.approx(15.60)
    assert out["floor_drain_outlets"] == {"GF": {"floor_drains": 11, "with_a_drawn_pipe": 11, "without": 0},
                                          "1F": {"floor_drains": 7, "with_a_drawn_pipe": 7, "without": 0},
                                          "2F": {"floor_drains": 1, "with_a_drawn_pipe": 1, "without": 0}}
    text = json.dumps(out)
    assert "segs" not in text and "at_m" not in text


def test_committed_v2_is_the_restatement_of_the_checked_v1_census():
    """r2 changes the status, never the drawn lengths the Checker reproduced: restating the committed V1 records
    gives the committed V2 file exactly."""
    import json
    sys.path.insert(0, str(ROOT / "research" / "agents_t745"))
    import t745_restate_r2 as S
    d = ROOT / "research" / "agents_t745" / "out"
    v1 = json.loads((d / "T745_ALSENAN_RUNS_V1_REJECTED.json").read_text())
    v2 = json.loads((d / "T745_ALSENAN_RUNS.json").read_text())
    assert json.loads(json.dumps(S.restate(v1))) == v2
    old = {r["run_id"]: r["lm"] for r in v1["runs"]}
    for r in v2["runs"]:
        assert r["scaled_info_lm"] == old[r["run_id"]]           # same drawn length, now information only
    m03 = next(r for r in v2["runs"] if r["run_id"] == "1F-M03")
    assert "5.587" in m03["label_note"] and "0.467" in m03["label_note"]
    assert 5.587 + 0.467 == pytest.approx(m03["scaled_info_lm"], abs=0.002)


# ---------------------------------------------------------------------------------- r2: sheet length basis (R-T380-1)
NTS_NOTE = "NOTES:- THE BUILDER TO WORK WITH STATED DIMENSIONS NOT TO SCALE DRAWING."


@pytest.mark.parametrize("text,basis", [
    (NTS_NOTE, R.BASIS_SCHEMATIC),
    ("SCALE: N.T.S.", R.BASIS_SCHEMATIC),
    ("scale nts", R.BASIS_SCHEMATIC),
    ("DO NOT SCALE FROM THIS DRAWING", R.BASIS_SCHEMATIC),
    ("SCALE 1:100", R.BASIS_SCALED),
    ("ALL STATED DIMENSIONS ARE IN MM", R.BASIS_SCALED),        # 'stated dimensions' alone is no disclaimer
    ("PLANTS AND CONTENTS SCHEDULE", R.BASIS_SCALED),           # 'nts' inside a word is no disclaimer
])
def test_sheet_basis_read_from_the_notes(text, basis):
    assert R.sheet_basis(text) == basis


def test_unread_notes_box_gives_no_basis():
    with pytest.raises(R.RefusedSheet):
        R.sheet_basis(None)
    runs, _ = villa()
    with pytest.raises(R.RefusedSheet):
        R.table(runs, [], K, basis="GUESSED")


def test_not_to_scale_sheet_yields_no_measured_plan_lm():
    """ADVERSE (verdict FIX 3): the same villa drawn on a sheet carrying a not-to-scale note: no plan row is
    MEASURED, no plan row is valued, the scaled figures survive only as labelled information, never 0."""
    runs, _ = villa()
    rows, marks = rows_of_basis(runs, R.sheet_basis(NTS_NOTE))
    plan = [r for r in rows.values() if r["kind"] == "PLAN"]
    assert plan and all(r["status"] == R.HELD_SCHEMATIC and r["lm"] is None for r in plan)
    info = {(r["system"], r["diameter_in"]): r["scaled_info_lm"] for r in plan}
    assert info[(R.BUILDING_DRAIN, 6)] == pytest.approx(15.600, abs=1e-3)
    assert info[(R.SOIL_WASTE_BRANCH, None)] == pytest.approx(7.531, abs=1e-3)
    assert all(r["info_label"] == R.SCALED_INFO_LABEL for r in plan)
    t = R.totals_by_state(plan)
    assert "PLAN|MEASURED" not in t
    assert t["PLAN|HELD_SCHEMATIC_NOT_TO_SCALE"]["lm"] is None
    assert t["PLAN|HELD_SCHEMATIC_NOT_TO_SCALE"]["scaled_info_lm"] == pytest.approx(15.6 + 7.531 + 1.4, abs=2e-3)
    assert [m["len_m"] for m in marks] == [0.04]              # a symbol mark stays a mark


def test_stated_dimension_is_measured_even_on_a_not_to_scale_sheet():
    """NORMAL: a run whose length the sheet PRINTS (12.40 m) is MEASURED at the printed value, not the scaled one;
    without a printed diameter it is still HELD_DIAMETER but valued (the length is stated)."""
    runs, _ = villa()
    k = next(r for r in runs if r.pen == "K")
    k.stated_m = 12.40                                        # the drawn 15.60 m is not used
    wc = next(r for r in runs if r.pen == "M" and len(r.segments) == 2 and not r.bridges)
    wc.stated_m = 2.50
    rows, _ = rows_of_basis(runs, R.BASIS_SCHEMATIC)
    assert rows[("PLAN", "GF", R.BUILDING_DRAIN, 6, R.MEASURED)]["lm"] == pytest.approx(12.40)
    assert rows[("PLAN", "GF", R.SOIL_WASTE_BRANCH, None, R.HELD_DIAMETER)]["lm"] == pytest.approx(2.50)
    sch = rows[("PLAN", "GF", R.SOIL_WASTE_BRANCH, None, R.HELD_SCHEMATIC)]
    assert sch["runs"] == 2 and sch["lm"] is None and sch["scaled_info_lm"] == pytest.approx(2.565685 + 2.4, abs=1e-3)


def test_mixed_sheets_keep_their_own_basis_and_never_sum_across():
    """GF on a scaled sheet, 1F (mirrored bathrooms) on a not-to-scale sheet: GF MEASURED, 1F HELD; the risers on
    printed levels stay MEASURED whatever the plan sheets say."""
    gf, _ = villa()
    f1, _ = villa(lambda p: (500 - p[0], p[1]))
    for r in f1:
        r.floor = "1F"
    rwp = R.Riser("RWP-1", R.RAINWATER_PIPE, 4, 7.00, 0.00, 0.15)
    rows, _ = R.table(gf + f1, [rwp], K, basis={"GF": R.BASIS_SCALED, "1F": R.BASIS_SCHEMATIC})
    t = R.totals_by_state(rows)
    assert t["PLAN|MEASURED"]["lm"] == pytest.approx(15.6)
    assert t["PLAN|HELD_SCHEMATIC_NOT_TO_SCALE"]["lm"] is None
    assert t["PLAN|HELD_SCHEMATIC_NOT_TO_SCALE"]["scaled_info_lm"] == pytest.approx(15.6 + 7.531 + 1.4, abs=2e-3)
    assert t["RISER|MEASURED"]["lm"] == pytest.approx(6.85)


def test_schematic_record_carrying_a_value_is_refused():
    bad = {"run_id": "x", "floor": "GF", "system": R.SOIL_WASTE_BRANCH, "diameter_in": 4,
           "status": R.HELD_SCHEMATIC, "lm": 3.0, "scaled_info_lm": 3.0, "symbol_mark": False}
    with pytest.raises(ValueError):
        R.table_from_records([bad], [])
    bad2 = dict(bad, status=R.MEASURED, lm=None)
    with pytest.raises(ValueError):
        R.table_from_records([bad2], [])


def rows_of_basis(runs, basis):
    rows, marks = R.table(runs, [], K, basis=basis)
    return {(r["kind"], r["floor"], r["system"], r["diameter_in"], r["status"]): r for r in rows}, marks
