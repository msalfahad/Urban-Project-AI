"""T-611: WIRING MANIFEST V13 + OVERLAY DRY RUN (R-T611-1).

Synthetic villa K611 (not the training villa; hand values):
  room line K-LIV (FIN.SKIRTING, RELEASED 30.000 lm) walks two walls along a stair void with no floor:
    Checker parts 2.000 + 4.000 + column returns 2 x 0.05 = 0.100 + straddling column void-side return 0.050 = 6.150 lm;
    worker 6.250 = Checker + 0.100 named (two returns that face the floor);
    after = 30.000 - 6.150 = 23.850 lm; second line K-BED 10.000 unchanged -> released 40.000 -> 33.850 lm (-15.38 %);
  an earlier package's TEXT_ONLY label on K-LIV is absorbed into the V13 row (one writer per line).
Adverse: an unmerged source; the same 6.15 deducted twice (by id, and as a stale base); components that do not re-add;
an unnamed or wrong worker difference; a deduction that would leave 0 or less; a HELD line; an m2 line; a wrong finding
id; absorbing a quantity op; two packages writing the line without the absorb: all refused. Then the training-villa
build must be the rebuild and close by hand on the Checker's 11.17 lm."""

import copy
from decimal import Decimal
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research/agents_t611"))
import manifest_v13 as M          # noqa: E402

M9, OV, M10 = M.M9, M.OV, M.M10
MK = {"T-606": {"merge": "k606", "verdict": "K611 floorless verdict"}}
PARTS = [("wall W1", "2.000"), ("wall W2", "4.000"), ("column C1 returns", "0.100"), ("column C2 void return", "0.050")]
DIFFS = [("columns C2 / C3 floor-side returns", "0.100")]
LIV = "L-" + "a" * 20
BED = "L-" + "b" * 20
P_OLD = "LABELS (K-old)"


def _line(lid, code, unit, elem, cls="RELEASED", v=None):
    return {"line_id": lid, "item_code": code, "unit": unit, "element_id": elem, "class": cls, "measured_net": v,
            "held_low": None, "held_high": None}


def _idx():
    L = [_line(LIV, "FIN.SKIRTING", "lm", "K1F-LIV:skirting", v=30.0),
         _line(BED, "FIN.SKIRTING", "lm", "K1F-BED:skirting", v=10.0)]
    return {l["line_id"]: l for l in L}


def _finding(**kw):
    f = {"id": "F-K611-1", "line": LIV, "line_net": "30", "lm": "6.25", "edges": ["W1", "W2"],
         "verdict_proposal": "ENGINE_WRONG", "why": "K611 stair void: no floor against W1 / W2",
         "released_V3_0_58": "40", "if_confirmed": "33.75", "pct": "-15.63"}
    f.update(kw)
    return f


def _row(idx=None, **kw):
    ck = M.checker_length(PARTS, "6.15")
    return M.floorless_row(_finding(**kw), _idx() if idx is None else idx, ck, merged=MK, parts=PARTS,
                           finding_id="F-K611-1")


def _label_order(idx):
    op = M9.row(P_OLD, "FR-K-3", "TEXT_ONLY", LIV, OV.state(idx[LIV]), None, "DRAWING-CONFIRMED", "K label",
                beside={"label_after": "LIFT LANDING DOOR"})
    return [(P_OLD, [op])]


# ---- normal --------------------------------------------------------------------------------------------------------

def test_checker_length_and_worker_reconciled():
    ck = M.checker_length(PARTS, "6.15")
    assert ck == Decimal("6.15")
    w = M.reconcile_worker(_finding(), ck, DIFFS)
    assert (w["worker_lm"], w["checker_lm"]) == ("6.25", "6.15")


def test_floorless_set_absorbs_label_and_moves_only_the_line():
    idx = _idx()
    r = _row(idx)
    assert r["kind"] == "SET" and r["line_id"] == LIV and r["after"]["class"] == "RELEASED"
    assert Decimal(str(r["after"]["measured_net"])) == Decimal("23.85")          # 30.000 - 6.150
    assert r["evidence"]["status"] == "PARTIALLY VERIFIED" and r["beside"]["deducted_lm"] == "6.15"
    old = _label_order(idx)
    with pytest.raises(OV.OverlayError, match="R1"):                              # two writers without the absorb
        OV.apply(idx, old + [(M.P_FLOOR, [r])])
    order, taken = M.absorb_label_pkg(old, P_OLD, LIV, r["before"])
    assert taken["row"] == "FR-K-3" and order == [(P_OLD, [])]
    after, rep = OV.apply(idx, order + [(M.P_FLOOR, [r])])
    assert [x["status"] for x in rep["rows"]] == ["APPLIED"]
    assert after[BED] == idx[BED]
    t0, t1 = OV.totals(idx)["FIN.SKIRTING|lm"], OV.totals(after)["FIN.SKIRTING|lm"]
    assert (t0["released"], t1["released"]) == ("40", "33.85")
    assert ((Decimal(t1["released"]) - Decimal(t0["released"])) / Decimal(t0["released"]) * 100).quantize(
        Decimal("0.01")) == Decimal("-15.38")
    assert (t1["released_n"], t1["held_n"], t1["excluded_n"]) == (2, 0, 0)


def test_no_row_sources_listed_unmerged_refused():
    m = {"T-A": {"merge": "a1", "verdict": "v"}}
    ok, refused = M.no_row_sources(m, {"T-A": "no quantity change"}, {"T-B": "TODO"})
    assert ok == {"T-A": {"merge": "a1", "rows": 0, "why": "no quantity change"}}
    assert "not MERGED" in refused["T-B"]["refusal"]


# ---- adverse --------------------------------------------------------------------------------------------------------

def test_unmerged_source_refused():
    ck = M.checker_length(PARTS, "6.15")
    with pytest.raises(M.ManifestError, match="not MERGED"):
        M.floorless_row(_finding(), _idx(), ck, merged={}, parts=PARTS, finding_id="F-K611-1")
    with pytest.raises(M.ManifestError, match="not MERGED"):
        M.no_row_sources({}, {"T-A": "x"}, {})
    with pytest.raises(M.ManifestError, match="listed as not merged"):
        M.no_row_sources({"T-B": {"merge": "b", "verdict": "v"}}, {}, {"T-B": "TODO"})


def test_same_deduction_twice_refused():
    ck = M.checker_length(PARTS, "6.15")
    with pytest.raises(M.ManifestError, match="already deducted once"):
        M.floorless_row(_finding(), _idx(), ck, merged=MK, parts=PARTS, finding_id="F-K611-1", done=("F-K611-1",))
    idx = _idx()
    r = _row(idx)
    after, _ = OV.apply(idx, [(M.P_FLOOR, [r])])
    with pytest.raises(M.ManifestError, match="stale or already deducted"):     # 23.85 is not the finding's base 30
        _row(after)
    r2 = copy.deepcopy(r)
    r2["op_id"] += "|again"
    with pytest.raises(OV.OverlayError, match="R1"):
        OV.apply(_idx(), [(M.P_FLOOR, [r]), ("SECOND", [dict(r2, package="SECOND")])])


@pytest.mark.parametrize("parts, total, msg", [
    (PARTS[:3], "6.15", "re-add"),
    (PARTS, "6.20", "re-add"),
    ([("x", "0")], "0", "0 or less"),
])
def test_checker_length_adverse(parts, total, msg):
    with pytest.raises(M.ManifestError, match=msg):
        M.checker_length(parts, total)


def test_worker_difference_adverse():
    ck = Decimal("6.15")
    with pytest.raises(M.ManifestError, match="unnamed"):
        M.reconcile_worker(_finding(), ck, [("", "0.10")])
    with pytest.raises(M.ManifestError, match="!= Checker"):
        M.reconcile_worker(_finding(), ck, [("one return only", "0.05")])


def test_line_adverse():
    idx = _idx()
    idx[LIV]["measured_net"] = 6.15
    with pytest.raises(M.ManifestError, match="EXCLUDED by rule"):
        _row(idx, line_net="6.15")
    idx = _idx()
    idx[LIV].update({"class": "HELD", "measured_net": None})
    with pytest.raises(M.ManifestError, match="only a released room line"):
        _row(idx)
    idx = _idx()
    idx[LIV]["unit"] = "m2"
    with pytest.raises(M.ManifestError, match="not a FIN.SKIRTING lm line"):
        _row(idx)
    with pytest.raises(M.ManifestError, match="ENGINE_WRONG finding"):
        _row(verdict_proposal="UNRESOLVED")
    with pytest.raises(M.ManifestError, match="ENGINE_WRONG finding"):
        _row(id="F-K611-9")


def test_absorb_quantity_op_refused():
    idx = _idx()
    op = M9.row(P_OLD, "FR-K-4", "SET", LIV, OV.state(idx[LIV]), M9.released(29.0), "DRAWING-CONFIRMED", "K")
    with pytest.raises(M.ManifestError, match="only a TEXT_ONLY"):
        M.absorb_label_pkg([(P_OLD, [op])], P_OLD, LIV, OV.state(idx[LIV]))
    with pytest.raises(M.ManifestError, match="no op on"):
        M.absorb_label_pkg([(P_OLD, [])], P_OLD, LIV, OV.state(idx[LIV]))


# ---- training villa: rebuild + hand closure ------------------------------------------------------------------------

@pytest.fixture(scope="module")
def built():
    return M.build()


def test_committed_output_is_the_rebuild(built):
    assert M.OUT_JSON.read_text(encoding="utf-8") == M.dumps(built)


def test_overlay_clean(built):
    o = built["overlay"]
    assert o["lines"] == {"base": 4999, "after_v12": 5125, "after_v13": 5125}
    assert o["stale"] == 0 and o["unexplained_conflicts"] == 0 and o["other_lines_changed_vs_v12_overlay"] == []
    assert [f["package"] for f in o["flagged_rows"]] == ["T-498"]          # T-580's own NO_BEFORE, not a V13 row
    assert list(o["v13_vs_v12_totals"]) == ["FIN.SKIRTING|lm"]


def test_skirting_after_total_by_hand(built):
    sk = built["skirting"]
    assert (sk["FIN.SKIRTING|lm"]["v12"]["released"], sk["FIN.SKIRTING|lm"]["v13"]["released"]) == \
        ("209.728592", "198.558592")
    assert Decimal("4.000") + Decimal("7.020") + Decimal("0.100") + Decimal("0.050") == Decimal("11.17")
    assert Decimal("209.728592") - Decimal("11.17") == Decimal("198.558592")
    assert Decimal("209.428592") - Decimal("11.17") == Decimal("198.258592")          # Checker, V3.0.58 base
    assert sk["released_delta_lm"] == "-11.17" and sk["pct_vs_v12"] == "-5.33"
    assert sk["line"] == {"id": "L-ba3599ec2dc82c221617", "net_before": "32.38536", "net_after": "21.21536"}
    v12, v13 = sk["FIN.SKIRTING|lm"]["v12"], sk["FIN.SKIRTING|lm"]["v13"]
    assert all(v12[k] == v13[k] for k in v12 if k != "released")                       # held 6, 0 .. 0 unchanged


def test_rows_sources_absorb(built):
    assert [r["row"] for r in built["rows"]] == ["FR-T606-1"]
    assert built["rows"][0]["absorbs"]["op_id"].endswith("|FR-T601-3|L-ba3599ec2dc82c221617")
    assert built["deduction"]["worker"]["worker_lm"] == "11.22" and built["deduction"]["checker_lm"] == "11.17"
    assert set(built["sources_no_row"]) == {"T-605", "T-607", "T-599"}
    assert set(built["sources_refused"]) == {"T-610"}
    assert built["stair_edge_census_after_v13"] == {"edges": 89, "doubles": 0, "orphans": 0}
    assert built["candidate_files_touched"] == 0 and built["released_quantities_changed"] == 0
