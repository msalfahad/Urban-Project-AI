"""T-228: wall register v2 (resolution ledger) and after-coverage.

Fixture villa M (NOT Alsenan), hand truth (m2):
  M1 0.20 WHITE  gross 10.000 SS, no opening                    -> a Checker ruling (length, height, deductions) VERIFIED
  M2 0.20 WHITE  gross 12.000 SS, window 1.00 x 1.50 = 1.500    -> merged package P-A gives the head: net 10.500 SS
  M3 0.15 BLACK  gross figure 8.000 HELD (member depth unprinted), door 0.90 x 2.20 = 1.980 booked on it -> net HELD
  Coverage: gross figure 30.000 = net VERIFIED 10.000 + net SS 10.500 + deductions on established nets 1.500
            + gross figure of held-net walls 8.000 (M3's 1.980 stays in the held scope).
  Pieces (lessons row, Checker 18:01): a 3.000 m run, 2.000 under a 0.40 beam (h 3.60) + 1.000 under the slab
  (h 3.84) = 7.200 + 3.840 = 11.040 m2; sampled pieces 2.02 + 0.98 with the last 0.10 m missing are refused.
"""
from __future__ import annotations

import csv
import json
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "research" / "agents_t228"
sys.path.insert(0, str(HERE))

import build_t228 as B     # noqa: E402
import register_v2 as R    # noqa: E402

SS, PS, VER, HELD = R.SS, R.PS, R.VER, R.HELD
COLS = ("wall_id", "floor", "group", "block_type", "type_class", "t_m", "length_m", "held_length_m", "length_class",
        "height_weighted_m", "gross_m2", "gross_class", "deductions_m2", "openings_in_run", "held_openings", "net_m2",
        "net_class", "net_bounds_m2", "net_m3", "owner_status_class", "held_cause_class", "next_package",
        "smallest_held_quantity", "unresolved_reason", "evidence", "calculation", "source_ledgers",
        "verified_by_checker", "held_increment_m2", "checker_remeasured", "v2_sources", "pending_findings_t228")


def w(wid, t, ty, L, h, g, gc, d, n, nc, fl="M0", why=""):
    r = {c: "" for c in COLS}
    r.update(wall_id=wid, floor=fl, group="EXTERNAL", block_type=ty, t_m=t, length_m=L, held_length_m="0.000",
             height_weighted_m=h, gross_m2=g, gross_class=gc, deductions_m2=d, net_m2=n, net_class=nc,
             owner_status_class=nc, unresolved_reason=why)
    return r


def villa_m():
    return [w("M1", "0.2", "WHITE", "4.000", "2.500", "10.000", SS, "0.000", "10.000", SS),
            w("M2", "0.2", "WHITE", "4.000", "3.000", "12.000", SS, "1.500", "", HELD, why="held opening WX"),
            w("M3", "0.15", "BLACK", "2.500", "3.200", "8.000", HELD, "1.980", "", HELD, why="beam depth")]


MERGED_M = {"P-A": "merged a1b2c3d4", "RULING M1": "Checker ruling (own re-measure)"}
CH_M = [{"wall_id": "M2", "source": "P-A", "set": {"net_m2": "10.500", "net_class": SS}, "why": "head drawn"},
        {"wall_id": "M1", "source": "RULING M1", "remeasured": {"length", "height", "deductions"},
         "set": {"gross_class": VER, "net_class": VER}}]


# ---------------------------------------------------------------- fixture villa M: normal
def test_villa_m_coverage_reconciles_to_gross():
    rows, log = R.apply(villa_m(), CH_M, MERGED_M)
    c = R.coverage(rows, key=lambda r: "ALL")["ALL"]
    assert c["net " + VER] == pytest.approx(10.0) and c["net " + SS] == pytest.approx(10.5)
    assert c["deductions_on_established_net_m2"] == pytest.approx(1.5)
    assert c["gross_figure_of_held_net_m2"] == pytest.approx(8.0)
    assert c["deductions_on_held_net_m2 (held scope)"] == pytest.approx(1.98)
    assert c["gross_figure_m2"] == pytest.approx(30.0) and c["reconciliation_residual_m2"] == pytest.approx(0.0)
    assert [x["source"] for x in log] == ["P-A", "RULING M1"]


def test_villa_m_v1_never_edited():
    v1 = villa_m()
    before = json.dumps(v1, sort_keys=True)
    R.apply(v1, CH_M, MERGED_M)
    assert json.dumps(v1, sort_keys=True) == before


def test_pieces_close_to_the_census_length():
    assert R.gross_from_pieces([(2.0, 3.6), (1.0, 3.84)], 3.0) == pytest.approx(11.04)
    # mirror / reversed order: same gross
    assert R.gross_from_pieces([(1.0, 3.84), (2.0, 3.6)], 3.0) == pytest.approx(11.04)


# ---------------------------------------------------------------- fixture villa M: adverse
def test_unmerged_worker_value_refused():
    bad = [{"wall_id": "M2", "source": "agents/task-T-999 (READY, not merged)", "set": {"net_m2": "11.000"}}]
    with pytest.raises(R.RegisterError) as e:
        R.apply(villa_m(), bad, MERGED_M)
    assert e.value.code == "UNMERGED_SOURCE"


def test_verified_only_by_a_complete_ruling():
    with pytest.raises(R.RegisterError) as e:
        R.apply(villa_m(), [{"wall_id": "M1", "source": "P-A", "set": {"gross_class": VER}}], MERGED_M)
    assert e.value.code == "VERIFIED_WITHOUT_RULING"
    part = [{"wall_id": "M1", "source": "RULING M1", "remeasured": {"length", "height"},
             "set": {"gross_class": VER, "net_class": VER}}]
    with pytest.raises(R.RegisterError) as e:
        R.apply(villa_m(), part, MERGED_M)
    assert e.value.code == "VERIFIED_INCOMPLETE"


def test_conflict_between_packages_needs_a_ruling():
    merged = {**MERGED_M, "P-B": "merged b2"}
    two = [{"wall_id": "M2", "source": "P-A", "set": {"gross_m2": "12.000"}},
           {"wall_id": "M2", "source": "P-B", "set": {"gross_m2": "12.300"}}]
    with pytest.raises(R.RegisterError) as e:
        R.apply(villa_m(), two, merged)
    assert e.value.code == "CONFLICT"
    ruled = two + [{"wall_id": "M2", "source": "RULING M1", "set": {"gross_m2": "12.100"}}]
    rows, _ = R.apply(villa_m(), ruled, merged)
    assert rows[1]["gross_m2"] == "12.100"


@pytest.mark.parametrize("change, code", [
    ({"wall_id": "M2", "source": "P-A", "set": {"net_m2": "11.000", "net_class": SS}}, "NET_MISMATCH"),
    ({"wall_id": "M3", "source": "P-A", "set": {"net_m2": "6.020", "net_class": SS}}, "NET_ON_HELD_GROSS"),
    ({"wall_id": "M3", "source": "P-A", "set": {"net_m2": "6.020"}}, "HELD_WITH_FIGURE"),
    ({"wall_id": "M1", "source": "P-A", "op": "add", "set": {}}, "DUPLICATE_WALL"),
    ({"wall_id": "M9", "source": "P-A", "set": {"gross_m2": "1.000"}}, "UNKNOWN_WALL"),
    ({"wall_id": "M1", "source": "P-A", "set": {"length_m": "4000.000"}}, "UNIT_GUARD"),
])
def test_inconsistent_rows_refused(change, code):
    with pytest.raises(R.RegisterError) as e:
        R.apply(villa_m(), [change], MERGED_M)
    assert e.value.code == code


def test_finding_only_holds():
    rows, _ = R.apply(villa_m(), CH_M, MERGED_M)
    rows, log = R.hold(rows, [{"wall_id": "M2", "source": "FINDING", "set": {"net_class": HELD, "net_m2": "",
                                                                           "owner_status_class": HELD}}])
    assert rows[1]["net_class"] == HELD and rows[1]["net_m2"] == "" and log[0]["op"] == "hold"
    for bad, code in (({"net_class": SS}, "FINDING_RAISES_CLASS"), ({"gross_m2": "1.0"}, "FINDING_WRITES_QUANTITY"),
                      ({"net_m2": "9.0"}, "FINDING_WRITES_QUANTITY")):
        with pytest.raises(R.RegisterError) as e:
            R.hold(rows, [{"wall_id": "M1", "source": "FINDING", "set": bad}])
        assert e.value.code == code


@pytest.mark.parametrize("pieces, L, code", [
    ([(2.02, 3.6), (0.88, 3.84)], 3.0, "PIECES_NOT_CLOSED"),       # sampled boundary, 0.10 m unsampled
    ([(2000.0, 3600.0), (1000.0, 3840.0)], 3000.0, "UNIT_GUARD"),  # millimetres
    ([(2.0, 3.6), (1.0, 0.0)], 3.0, "PIECE_HELD"),                 # a piece with no height is HELD, never 0
])
def test_pieces_adverse(pieces, L, code):
    with pytest.raises(R.RegisterError) as e:
        R.gross_from_pieces(pieces, L)
    assert e.value.code == code


# ---------------------------------------------------------------- Alsenan development villa (register v2)
def _csv(name):
    return list(csv.DictReader((HERE / name).open(encoding="utf-8")))


@pytest.fixture(scope="module")
def built():
    return B.build_register()


def test_committed_outputs_reproduce(built):
    for name, text in B.outputs().items():
        assert (HERE / name).read_text(encoding="utf-8") == text, name


def test_v2_is_v1_plus_merged_changes_only(built):
    v1, v2, log = built
    a = {r["wall_id"]: r for r in v1}
    logged = {c["wall_id"] for c in log}
    for r in v2:
        o = a.get(r["wall_id"])
        moved = o is None or any(r[k] != o[k] for k in R.NUMERIC + ("gross_class", "net_class"))
        if moved:
            assert r["wall_id"] in logged, r["wall_id"]
    for c in log:
        assert c["source"] in B.MERGED or c["op"] == "hold", c
    assert len(v1) == 74 and len(v2) == 76      # two pieces in no v1 row: bay ends, P-GF-05 above the lintel


def test_checker_numbers_not_worker_numbers(built):
    _, v2, _ = built
    r = {x["wall_id"]: x for x in v2}
    assert r["GF-W07"]["gross_m2"] == "4.458" and r["GF-W07"]["net_class"] == VER       # worker 4.468 refused
    assert r["1F-W05"]["gross_m2"] == "23.223" and r["1F-W05"]["gross_class"] == VER     # worker 23.254 refused
    assert r["1F-W05"]["net_m2"] == "19.303" and r["1F-W05"]["net_class"] == SS
    assert r["1F-W00"]["net_m2"] == "12.863"                                              # arched outline 4.363
    assert r["2F-W07"]["deductions_m2"] == "1.875" and r["2F-W07"]["net_class"] == HELD    # T-238 W26 outline
    assert r["2F-W08"]["gross_class"] == VER and r["2F-W08"]["net_class"] == PS           # Q-55 C stays visible
    # Checker pieces close to the census length (lessons row 18:01)
    assert R.gross_from_pieces([(0.950, 4.10), (0.150, 3.75)], 1.100) == pytest.approx(4.4575, abs=5e-4)
    assert R.gross_from_pieces([(2.300, 3.70), (3.652, 3.70), (0.348, 3.45)], 6.300) == pytest.approx(23.2234,
                                                                                                    abs=5e-4)


def test_without_the_ruling_the_worker_value_is_not_verified():
    base = B.v1()
    ch = B.delta_changes(base, "research/agents_t226/register_delta.csv", "T-226")
    rows, _ = R.apply(base, ch, B.MERGED)
    r = {x["wall_id"]: x for x in rows}
    assert r["GF-W07"]["gross_m2"] == "4.468" and r["GF-W07"]["net_class"] == SS


def test_gf_w10_held_by_finding_never_zero(built):
    _, v2, log = built
    r = {x["wall_id"]: x for x in v2}["GF-W10"]
    assert r["net_class"] == HELD and r["net_m2"] == "" and "47.425" in r["net_bounds_m2"]
    assert "+0.30" in r["pending_findings_t228"] and "1.350" in r["pending_findings_t228"]
    assert r["gross_m2"] == "50.845" and r["deductions_m2"] == "3.420"
    assert any(c["op"] == "hold" and c["wall_id"] == "GF-W10" for c in log)


def test_coverage_reconciles_every_group(built):
    v1, v2, _ = built
    for rows in (v1, v2):
        for k, a in R.coverage(rows, B.KEY).items():
            assert abs(a["reconciliation_residual_m2"]) <= 0.002, k


def test_length_change_is_exactly_the_listed_resolutions(built):
    v1, v2, _ = built
    listed = {"T-215 ends closed by area": 0.2855, "T-222 bay group": 0.4124, "T-222 junction piece": 0.077,
              "T-222 P-GF-05 piece above the lintel": 1.200}
    d = sum(R.f(r["length_m"]) for r in v2) - sum(R.f(r["length_m"]) for r in v1)
    assert d == pytest.approx(sum(listed.values()), abs=0.003)


def test_held_never_zero_and_every_blocker_named(built):
    _, v2, _ = built
    for r in v2:
        if r["net_class"] == HELD:
            assert r["net_m2"] == ""
    for b in _csv("BLOCKERS_V2.csv"):
        assert b["exact_missing_item"] and b["smallest_affected_quantity"], b["wall_id"]
    held = {r["wall_id"] for r in v2 if r["net_class"] == HELD or r["held_increment_m2"]}
    assert held == {b["wall_id"] for b in _csv("BLOCKERS_V2.csv")}


def test_freelancer_is_comparison_only(built):
    src = (HERE / "build_t228.py").read_text(encoding="utf-8")
    assert "FREELANCER_RAW_ROWS" not in src
    for r in _csv("FREELANCER_COMPARISON_V2.csv"):
        assert r["note"].startswith("comparison column only")


def test_no_coordinates_in_outputs():
    pat = re.compile(r"-?\d{5,}\.\d+|\b\d{6}\b")
    for p in HERE.glob("*.csv"):
        assert not pat.search(p.read_text(encoding="utf-8")), p.name


# ---------------------------------------------------------------- r2: R-T228-3 stair-line sibling check
# Fixture villa S (NOT Alsenan): a 3-storey shaft stair beside a wall line L1 (member X on every frame); the plans print
# '(With Stair)' on the GF and 1F frames, no floor-level mark; the 2F floor is printed (slab cut in the section).
# A second line L2 prints '(With Stair)' on GF with a floor-level band beside it: the 1F floor exists there.
def _lines_s():
    return [{"line_id": "L1", "members": {"GF": "X-GF", "1F": "X-1F", "2F": "X-2F"},
             "with_stair": {"GF": "text a", "1F": "text b"}, "floor_level_mark": {}, "floor_at_basis": {"2F": "cut"}},
            {"line_id": "L2", "members": {"GF": "Y-GF", "1F": "Y-1F"}, "with_stair": {"GF": "text c"},
             "floor_level_mark": {"GF": "band"}, "floor_at_basis": {"1F": "band"},
             "other_spans_m": {"1F": [4.0]}}]


def _p(wid, s, m, L="2.500"):
    return {"wall_id": wid, "storey": s, "member_top": m, "length_m": L, "height_m": "3.00"}


def test_stair_line_normal():
    fl = {x["wall_id"]: x for x in R.stair_line_flags(
        [_p("S-GF", "GF", "X-GF"), _p("S-1F", "1F", "X-1F"), _p("S-2F", "2F", "X-2F"), _p("T-1F", "1F", "Y-1F"),
         _p("T-1F-other", "1F", "Y-1F", "4.000"), _p("U-1F", "1F", "Z-1F")], _lines_s())}
    assert fl["S-GF"]["flagged"] and "top:" in fl["S-GF"]["reasons"] and "base:" in fl["S-GF"]["reasons"]
    assert fl["S-1F"]["flagged"] and "base frame GF" in fl["S-1F"]["reasons"] and "top:" in fl["S-1F"]["reasons"]
    assert not fl["S-2F"]["flagged"]                       # slab cut printed at the 2F basis, top is a plain member
    assert not fl["T-1F"]["flagged"]                       # floor-level band printed beside the stair mark
    assert "T-1F-other" not in fl and "U-1F" not in fl     # other span of the member / no stair line


def test_stair_line_adverse():
    lines = _lines_s()
    # without the printed 2F slab cut the 2F piece is HELD too ('any storey frame' of the line)
    lines[0]["floor_at_basis"] = {}
    fl = {x["wall_id"]: x for x in R.stair_line_flags([_p("S-2F", "2F", "X-2F")], lines)}
    assert fl["S-2F"]["flagged"] and "top:" not in fl["S-2F"]["reasons"]
    # mirrored / rotated: frame order and piece order do not change the result
    rev = [{**ln, "members": dict(reversed(list(ln["members"].items())))} for ln in reversed(_lines_s())]
    ps = [_p("S-GF", "GF", "X-GF"), _p("S-1F", "1F", "X-1F"), _p("T-1F", "1F", "Y-1F")]
    key = lambda out: sorted((x["wall_id"], x["flagged"]) for x in out)
    assert key(R.stair_line_flags(ps, _lines_s())) == key(R.stair_line_flags(list(reversed(ps)), rev))
    # millimetres: a piece that matches no other span stays on the line (conservative, checked, never dropped)
    assert [x["wall_id"] for x in R.stair_line_flags([_p("T-mm", "1F", "Y-1F", "4000.0")], _lines_s())] == ["T-mm"]
    for bad_lines, bad_p, code in (([{**_lines_s()[0], "with_stair": {}}], [], "NOT_A_STAIR_LINE"),
                                   (_lines_s(), [_p("S-B1", "B1", "X-GF")], "UNKNOWN_STOREY")):
        with pytest.raises(R.RegisterError) as e:
            R.stair_line_flags(bad_p, bad_lines)
        assert e.value.code == code
    # a register that keeps an established net on a flagged wall is caught
    rows = [w("S-1F", "0.2", "WHITE", "2.500", "3.000", "7.500", SS, "0.000", "7.500", SS, fl="1F")]
    flags = R.stair_line_flags([_p("S-1F", "1F", "X-1F")], _lines_s())
    assert R.stair_line_violations(rows, flags) == ["S-1F"]
    rows[0].update(net_class=HELD, net_m2="")
    assert R.stair_line_violations(rows, flags) == []


def test_alsenan_stair_line_sibling_check(built):
    _, v2, log = built
    assert B.line_positions_ok() == []                     # one plan position per line on every frame (T-110 x / y)
    fl = B.stair_check(v2)
    assert {x["wall_id"] for x in fl if x["flagged"]} == {"GF-W10", "1F-W10", "2F-W02", "GF-W03"}
    assert {x["wall_id"] for x in fl if not x["flagged"]} == {"1F-W06", "1F-W22"}
    assert R.stair_line_violations(v2, fl) == []
    r = {x["wall_id"]: x for x in v2}
    w10 = r["1F-W10"]
    assert w10["net_class"] == HELD and w10["gross_class"] == HELD and w10["net_m2"] == "" and w10["net_m3"] == ""
    assert "38.369" in w10["net_bounds_m2"] and "44.929" not in w10["net_bounds_m2"]
    assert "HELD pcs" in w10["t176_products"] and "net HELD" in w10["calculation"]
    assert "39.1525" in r["GF-W10"]["net_bounds_m2"] and r["GF-W10"]["gross_class"] == HELD
    assert "F4" in r["2F-W02"]["pending_findings_t228"] and r["2F-W02"]["net_class"] == HELD
    assert any(c["op"] == "hold" and c["wall_id"] == "1F-W10" for c in log)
    assert {b["wall_id"] for b in _csv("STAIR_LINE_CHECK.csv")} == {x["wall_id"] for x in fl}
