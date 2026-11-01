"""T-406: reconciliation roll-up rules (R-T406-1 .. 8) and the Alsenan roll-up of T-385 r2.

Villa R406 (hand fixture, NOT Alsenan). Earlier closure (engine - other side, m3):
  FOOTING   A  AGREE         0.000  (traced 0)
            B  HELD         -2.000  (held: strap footing held, other side 2.000)
  BEAM      C  UNRESOLVED   -1.500  (two lumps compared)
            D  ENGINE_RIGHT +0.300  (traced: depth 0.60 vs 0.50 on 0.50 x 6.00 = +0.300)
  before: traced +0.300, held -2.000, unexplained -1.500, residual -3.200.
Merged task T-900 traces C: held runs 2.00 m x 0.30 x 0.60 = -0.360 HELD; section 0.75 vs 0.60 on 8.00 m x 0.30 =
  +0.360 ENGINE_RIGHT; his lump length 8.333 m beyond the drawn run: -1.500 + 0.360 - 0.360 = -1.500 -> untraced -1.500
  (kept unexplained, never closed by its sign).  -> after: traced +0.660, held -2.360, unexplained -1.500.
B moves to its own family row STRAP_BELOW_NG. Candidate move (merged Gate B T-901) on D: 0.300 m3 of engine valued
  withdrawn into a range -> HELD -0.300.  -> current: traced +0.660, held -2.660, unexplained -1.500, residual -3.500.
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t406"))
import t406_rules as R  # noqa: E402

PRIVATE_RECON = ROOT.parent / "private" / "t406" / "t385out" / "RECON_T385.csv"


def comp(i, fam, v, c, t=0.0, h=0.0, u=0.0):
    return {"id": i, "family": fam, "verdict": v, "contribution_m3": c, "traced_m3": t, "held_m3": h,
            "unexplained_m3": u}


BEFORE = [comp("A", "FOOTING", "AGREE", 0.0), comp("B", "FOOTING", "HELD", -2.0, h=-2.0),
          comp("C", "BEAM", "UNRESOLVED", -1.5, u=-1.5), comp("D", "BEAM", "ENGINE_RIGHT", 0.3, t=0.3)]
MERGED = {"T-900": "aaaa1111", "T-901": "bbbb2222"}
TRACE_C = {"source": "T-900", "parts": [
    {"cause": "held runs 2.00 m x 0.30 x 0.60", "m3": -0.36, "verdict": "HELD"},
    {"cause": "section 0.75 vs 0.60 on 8.00 m x 0.30", "m3": 0.36, "verdict": "ENGINE_RIGHT"},
    {"cause": "his lump length beyond the drawn run", "m3": -1.5, "verdict": "UNTRACED"}]}
MOVE_D = {"source": "T-901", "parts": [{"cause": "engine valued withdrawn into a range", "m3": -0.3, "verdict": "HELD"}]}


def run(traces=None, merged=MERGED, fm=None, moves=None, before=BEFORE):
    return R.rollup(before, {"C": TRACE_C} if traces is None else traces, merged,
                    {"B": "STRAP_BELOW_NG"} if fm is None else fm, {"D": MOVE_D} if moves is None else moves)


# ---------------- normal

def test_before_after_current_by_hand():
    rows, fb, fa, fc, tot = run()
    assert tot["before"] == {"residual_m3": -3.2, "TRACED": 0.3, "HELD": -2.0, "UNEXPLAINED": -1.5,
                             "families_cause_closing": 1, "families": 2}
    assert (tot["after_traces"]["TRACED"], tot["after_traces"]["HELD"], tot["after_traces"]["UNEXPLAINED"]) == \
        (0.66, -2.36, -1.5)
    assert tot["after_traces"]["residual_m3"] == -3.2
    assert (tot["current"]["TRACED"], tot["current"]["HELD"], tot["current"]["UNEXPLAINED"],
            tot["current"]["residual_m3"]) == (0.66, -2.66, -1.5, -3.5)


def test_family_move_prints_own_row_and_keeps_totals():
    _, fb, fa, _, tot = run()
    assert set(fb) == {"FOOTING", "BEAM"} and set(fa) == {"FOOTING", "BEAM", "STRAP_BELOW_NG"}
    assert fa["STRAP_BELOW_NG"]["HELD"] == -2.0 and fa["FOOTING"]["residual_m3"] == 0.0
    assert fa["FOOTING"]["cause_closes"] and not fa["BEAM"]["cause_closes"]


def test_untraced_stays_unexplained_never_closed_by_sign():
    rows, _, fa, _, _ = run()
    c = next(r for r in rows if r["id"] == "C")
    assert c["after"]["UNEXPLAINED"] == -1.5 and c["trace_commit"] == "aaaa1111"
    assert fa["BEAM"]["UNEXPLAINED"] == -1.5


def test_component_without_trace_carries_before_split():
    rows, *_ = run()
    b = next(r for r in rows if r["id"] == "B")
    assert b["after"] == b["before"] == {"TRACED": 0.0, "HELD": -2.0, "UNEXPLAINED": 0.0}


# ---------------- adverse

def test_unmerged_trace_refused():
    with pytest.raises(R.Refused, match="merged register"):
        run(traces={"C": dict(TRACE_C, source="T-902")})


def test_unmerged_candidate_move_refused():
    with pytest.raises(R.Refused, match="merged register"):
        run(moves={"D": dict(MOVE_D, source="T-903")})


def test_unresolved_counted_as_traced_refused():
    bad = {"source": "T-900", "parts": [dict(p) for p in TRACE_C["parts"]]}
    bad["parts"][2]["counted_as"] = "TRACED"
    with pytest.raises(R.Refused, match="counted as TRACED"):
        run(traces={"C": bad})


def test_held_counted_as_traced_refused():
    bad = {"source": "T-900", "parts": [dict(p) for p in TRACE_C["parts"]]}
    bad["parts"][0]["counted_as"] = "TRACED"
    with pytest.raises(R.Refused):
        run(traces={"C": bad})


def test_held_part_as_zero_refused():
    bad = {"source": "T-900", "parts": [{"cause": "held runs", "m3": 0.0, "verdict": "HELD"},
                                        {"cause": "lump length", "m3": -1.5, "verdict": "UNTRACED"}]}
    with pytest.raises(R.Refused, match="never 0"):
        run(traces={"C": bad})


def test_trace_that_moves_the_residual_refused():
    bad = {"source": "T-900", "parts": [{"cause": "section", "m3": 0.36, "verdict": "ENGINE_RIGHT"}]}
    with pytest.raises(R.Refused, match="never moves"):
        run(traces={"C": bad})


def test_ratio_cause_refused():
    bad = {"source": "T-900", "parts": [{"cause": "3 % of the residual", "m3": -1.5, "verdict": "ENGINE_RIGHT"}]}
    with pytest.raises(R.Refused, match="ratio"):
        run(traces={"C": bad})


def test_unknown_component_and_bad_before_refused():
    with pytest.raises(R.Refused, match="not a component"):
        run(traces={"Z": TRACE_C})
    with pytest.raises(R.Refused, match="split"):
        run(before=BEFORE[:3] + [comp("D", "BEAM", "ENGINE_RIGHT", 0.3)])
    with pytest.raises(R.Refused, match="twice"):
        run(before=BEFORE + [BEFORE[0]])


# ---------------- R-T406-8 (r3): class from the board verdict, never a moved figure
# Villa R406 shallow dome (hand, NOT Alsenan): spherical cap, base radius 1.50, rise 1.00, shell 0.10 (inner rise 0.90).
#   R_o = (1.50^2 + 1.00^2) / 2.00 = 1.625; R_i = 1.525; V = pi h^2 (3R - h) / 3
#   outer pi x 1.00 x 3.875 / 3 = 4.057890; inner pi x 0.81 x 3.675 / 3 = 3.117245; shell 0.940645 m3.
#   Other side: a hemisphere reading of the area (2 pi h^2 = 6.283185 m2) x 0.10 = 0.628319 -> term +0.312327.
#   The package printed that term UNTRACED; the merged Checker verdict rules it ENGINE_RIGHT (own cap calculation).

import math  # noqa: E402

DOME_TERM = round((math.pi * 1.0 * (3 * 1.625 - 1.0) / 3 - math.pi * 0.81 * (3 * 1.525 - 0.9) / 3)
                  - 2 * math.pi * 1.0 ** 2 * 0.10, 6)
BOARD = {"task": "T-900", "member": "DOME", "m3": DOME_TERM, "verdict": "ENGINE_RIGHT",
         "ref": "T-900 MERGED aaaa1111, Checker own cap calculation"}
PKG = {"cause": "DOME: shell area term untraced", "m3": DOME_TERM, "verdict": "UNTRACED"}


def test_board_verdict_reclasses_by_hand_and_keeps_the_figure():
    assert DOME_TERM == 0.312327
    p = R.board_reclass("DOME", PKG, BOARD, MERGED)
    assert p["m3"] == PKG["m3"] and p["verdict"] == "ENGINE_RIGHT" and p["package_verdict"] == "UNTRACED"
    before = [comp("E", "DOME", "UNRESOLVED", DOME_TERM - 1.0, u=DOME_TERM - 1.0)]
    held = {"cause": "second dome held named item", "m3": -1.0, "verdict": "HELD"}
    _, _, fa, _, tot = R.rollup(before, {"E": {"source": "T-900", "parts": [p, held]}}, MERGED, {}, {})
    assert (tot["after_traces"]["TRACED"], tot["after_traces"]["HELD"], tot["after_traces"]["UNEXPLAINED"]) == \
        (0.312327, -1.0, 0.0)
    _, _, _, _, tot0 = R.rollup(before, {"E": {"source": "T-900", "parts": [PKG, held]}}, MERGED, {}, {})
    assert tot0["after_traces"]["UNEXPLAINED"] == 0.312327          # without the board verdict it stays unexplained


@pytest.mark.parametrize("change, match", [
    ({"task": "T-950"}, "not in the merged register"),
    ({"member": "OTHER"}, "not the member"),
    ({"ref": " "}, "no reference"),
    ({"m3": DOME_TERM + 0.01}, "never moves a figure"),
    ({"verdict": "CLOSER_TO_FREELANCER"}, "unknown verdict"),
])
def test_board_verdict_adverse_refused(change, match):
    with pytest.raises(R.Refused, match=match):
        R.board_reclass("DOME", PKG, {**BOARD, **change}, MERGED)


def test_board_verdict_never_classes_a_held_part_as_traced():
    held = {"cause": "second dome held named item", "m3": -1.0, "verdict": "HELD"}
    with pytest.raises(R.Refused, match="HELD part"):
        R.board_reclass("DOME", held, {**BOARD, "m3": -1.0}, MERGED)


def test_unknown_verdict_refused():
    bad = {"source": "T-900", "parts": [{"cause": "lump", "m3": -1.5, "verdict": "CLOSER_TO_FREELANCER"}]}
    with pytest.raises(R.Refused, match="unknown verdict"):
        run(traces={"C": bad})


# ---------------- Alsenan (committed inputs only)

import t406_alsenan as A  # noqa: E402

SUMMARY = json.loads((ROOT / "research" / "agents_t406" / "summary_t406.json").read_text(encoding="utf-8"))


def test_every_trace_reads_a_merged_summary_and_re_adds_to_its_residual():
    tr = A.traces()
    assert set(tr) == {"GS-SLAB", "GB-MAIN", "CL-GF", "CL-1F", "CL-LIFT", "BM-GF", "BM-1F", "BM-2F", "SD-DOME",
                       "SD-STAIR", "PL-PUMP", "GB-BOUNDARY", "BW-BAND"}
    for cid, t in tr.items():
        assert t["source"] in A.MERGED
        s = R.split_of(t["parts"])
        assert abs(sum(s.values()) - t["residual_in_source"]) <= R.TOL, cid


def test_merge_commits_are_on_this_branch():
    for task, sha in A.MERGED.items():
        r = subprocess.run(["git", "-C", str(ROOT), "merge-base", "--is-ancestor", sha, "HEAD"], capture_output=True)
        if r.returncode == 128:
            pytest.skip("git history not available")
        assert r.returncode == 0, f"{task} {sha} not merged on this branch"


def test_summary_before_is_the_t385_r2_headline():
    b = SUMMARY["totals"]["before"]
    assert (b["TRACED"], b["HELD"], b["UNEXPLAINED"], b["residual_m3"]) == (0.252401, -77.593, -37.123829, -114.464428)


def test_summary_after_restates_the_same_residual_and_closes_by_family():
    t = SUMMARY["totals"]
    assert abs(t["after_traces"]["residual_m3"] - t["before"]["residual_m3"]) <= R.TOL
    for key, tk in (("families_after_traces", "after_traces"), ("families_current_v3_0_33", "current")):
        fams = SUMMARY[key]
        for k in ("TRACED", "HELD", "UNEXPLAINED", "residual_m3"):
            assert abs(sum(f[k] for f in fams.values()) - t[tk][k]) <= R.TOL
        assert all(f["bookkeeping_closes"] for f in fams.values())
    # r3 (R-T406-8): SD-DOME domes A + B +0.561362 traced by the T-398 board verdict
    assert (t["after_traces"]["TRACED"], t["after_traces"]["HELD"], t["after_traces"]["UNEXPLAINED"]) == \
        (4.125049, -107.021212, -11.568269)
    assert (t["current"]["TRACED"], t["current"]["HELD"], t["current"]["UNEXPLAINED"]) == \
        (4.128223, -115.460212, -11.568269)
    assert abs(t["current"]["residual_m3"] - t["after_traces"]["residual_m3"] - (-8.439 + 0.003174)) <= R.TOL


def test_boundary_family_row_and_held_never_zero():
    f = SUMMARY["families_after_traces"]["CONC.BOUNDARY_BELOW_NG"]
    assert f["components"] == 2 and f["HELD"] < 0 and not f["cause_closes"]
    for c in SUMMARY["retraced_components"]:
        for p in c["parts"] + c["move_parts"]:
            if p["verdict"] == "HELD":
                assert p["m3"] != 0.0
        assert c["trace_source"] in (None, *A.MERGED) and c["move_source"] in (None, *A.MERGED)


def test_no_unmerged_task_in_the_summary():
    text = json.dumps(SUMMARY)
    for unmerged in ("T-400", "T-408", "T-411", "T-412", "T-413", "T-414"):     # not merged at r3 (2026-11-01)
        assert f'"{unmerged}"' not in text


@pytest.mark.skipif(not PRIVATE_RECON.exists(), reason="private T-385 table not rebuilt in this run")
def test_private_rebuild_equals_committed_summary():
    pub = A.public_summary(*A.build(A.before_from_recon(PRIVATE_RECON)))
    assert json.loads(json.dumps(pub, sort_keys=True)) == SUMMARY


def test_sd_dome_class_from_the_board_verdict():
    c = next(c for c in SUMMARY["retraced_components"] if c["id"] == "SD-DOME")
    assert c["after"] == {"HELD": -2.26, "TRACED": 0.561362, "UNEXPLAINED": 0.0}
    p = next(p for p in c["parts"] if p.get("package_verdict"))
    assert p["package_verdict"] == "UNTRACED" and p["verdict"] == "ENGINE_RIGHT" and p["m3"] == 0.561362
    s398 = json.loads((ROOT / "research" / "agents_t398" / "summary_t398.json").read_text(encoding="utf-8"))
    pkg = next(x for x in s398["components"] if x["id"] == "SD-DOMES-AB")
    assert pkg["untraced_term_m3"] == p["m3"]                   # the package's own figure, never moved
    # the Checker's cap arithmetic (T-398 verdict) reproduces the engine's two shells
    ro = (2.21 ** 2 + 1.90 ** 2) / 3.80
    cap = lambda r, h: math.pi * h * h * (3 * r - h) / 3
    assert abs(2 * (cap(ro, 1.90) - cap(ro - 0.10, 1.80)) - pkg["engine_valued_m3"]) <= 0.001
    f = SUMMARY["families_after_traces"]["CONC.STAIR_DOME"]
    assert (f["TRACED"], f["HELD"], f["UNEXPLAINED"]) == (0.233217, -5.788, -5.827775)


def test_v3034_moved_no_concrete_line():
    note = SUMMARY["candidate_notes"]["V3.0.33 -> V3.0.34"]
    assert "none concrete" in note and A.MERGED["T-399"] in note
    assert A.v3034_note() == note
