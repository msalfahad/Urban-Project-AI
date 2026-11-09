"""T-652: WIRING MANIFEST V19 on ARCH_TAKEOFF_V3.0.59 + TRIAL BOQ r3 (R-T652-1 / R-T652-2).

Synthetic villa K652 (not the training villa; hand values):
  base move: stage line L-a HELD blank, the overlay ADDs it HELD blank and a later row of the same package releases it
    12.5 pcs: the ADD leaves the overlay and the rebuilt index is byte-equal; an ADD that differs from the stage
    (RELEASED 10.0 vs HELD blank) is refused; a stage line the overlay never added is refused.
  0.15 m host: contract 10.00 m2, REQUIRED lintel face 0.36 m2, HELD face 0.34 m2 -> base 9.64, low 9.30 m2 ->
    units 9.30 x 12.5 = 116.25 .. 9.64 x 12.5 = 120.5 pcs, panel 9.30 x 0.0110625 = 0.102881 .. 0.106643 m3.
  re-measure: D-1F-07 pending HELD blank -> HELD 0.036 .. 0.04377 m3 (0.15 x 0.20 x 1.20 .. 1.459); L-GF-01 keeps
    HELD blank, its cause names the register and the 0.072 m3 beside.
  CN: 2 HELD column lines -> EXCLUDED (printed absence); threshold 1.000 x 0.150 = 0.150 m2 RELEASED;
  downgrade: tread RELEASED 3.105 -> HELD 3.105 .. 3.795 m2.
Adverse: a freelancer figure as source; HELD as 0; NOT_APPLICABLE on a released line; an unvalidated downgrade; a
re-measure bound that is not the Checker's; a stale cause on an answered decision (flagged); a Gate B line with no
status. Then the training-villa build must be the committed rebuild and close by hand."""

import os
import sys
from decimal import Decimal
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research/agents_t652"))
import manifest_v19 as M          # noqa: E402
import trial_boq_r3 as R          # noqa: E402

M9, OV = M.M9, M.OV
MK = {t: {"merge": "k" + t[-3:], "verdict": f"K652 {t} verdict"} for t in ("T-650", "T-647", "T-648", "T-635")}
MK["T-649"] = {"merge": "k649", "verdict": "K652 DGP-T649-1111111111111111 CHECKER-VALIDATED"}
BLANK = {"class": "HELD", "measured_net": None, "held_low": None, "held_high": None}


def L(c):
    return "L-" + c * 20


def _line(lid, code, unit, elem, cls="RELEASED", v=None, lo=None, hi=None):
    return {"line_id": lid, "item_code": code, "unit": unit, "element_id": elem, "class": cls, "measured_net": v,
            "held_low": lo, "held_high": hi}


# ---- (a) the base move --------------------------------------------------------------------------------------------

def _stage_row(state="BLOCKED_RFI", value=None):
    return {"line_id": L("a"), "item_code": "MAS.UNITS.BLACK", "unit": "pcs", "element_id": "MATERIAL:K:walls t=0.15",
            "after": {"state": state, "value": value, "low": None, "high": None}}


def _order(add_after=None):
    add = {"op_id": "T-498|STAGE|a", "package": "T-498", "row": "STAGE", "kind": "ADD", "line_id": L("a"),
           "before": None, "after": add_after or dict(BLANK), "source": "T-498", "item_code": "MAS.UNITS.BLACK",
           "unit": "pcs", "element_id": "MATERIAL:K:walls t=0.15"}
    st = M9.row("T-498", "FR-K", "SET", L("a"), dict(BLANK), M9.released(12.5), "DRAWING-CONFIRMED", "v")
    return [("T-498", [add, st])]


def test_base_move_is_an_identity():
    stage = M.stage_lines({"rows": [_stage_row()]})
    idx58 = {L("b"): _line(L("b"), "MAS.BLOCK", "m2", "K:walls t=0.15", v=1.0)}
    before, _ = OV.apply(idx58, _order())
    order_r, removed = M.rebase(_order(), stage)
    after, _ = OV.apply(M.base_v3059(idx58, stage), order_r)
    assert removed == ["T-498|STAGE|a"] and after == before and after[L("a")]["measured_net"] == 12.5


def test_base_move_adverse():
    stage = M.stage_lines({"rows": [_stage_row()]})
    with pytest.raises(M.ManifestError, match="refused"):
        M.rebase(_order(M9.released(10.0)), stage)                      # the ADD is not the merged line
    with pytest.raises(M.ManifestError, match="never added"):
        M.rebase([("T-498", [])], stage)
    with pytest.raises(M.ManifestError, match="never a value"):
        M.stage_lines({"rows": [_stage_row(value=3.0)]})                 # a blank stage line with a figure
    with pytest.raises(M.ManifestError, match="no index class"):
        M.stage_lines({"rows": [_stage_row(state="GUESSED")]})
    with pytest.raises(M.ManifestError, match="already"):
        M.base_v3059({L("a"): {}}, stage)


# ---- F-C-T498-1: 0.15 m host re-derivation -------------------------------------------------------------------------

def _host(units=116.25, mortar=0.102881, net=10.0, why="the installed module ... is not stated"):
    lint = [{"face_m2": 0.36, "face_max_m2": None, "kind": "REQUIRED", "opening_id": "K-D1"},
            {"face_m2": None, "face_max_m2": 0.34, "kind": "HELD_RANGE", "opening_id": "K-D2"}]
    rows = [{"line_id": L(c), "item_code": code, "unit": u, "element_id": "MATERIAL:K:walls t=0.15#BLOCKWORK:V",
             "source_line_id": L("h"), "contract_net_m2": 10.0, "lintels": lint, "why": why,
             "after": {"state": "BLOCKED_RFI"}} for c, code, u in (("u", "MAS.UNITS.BLACK", "pcs"),
                                                                  ("m", "MAS.MORTAR.BLACK", "m3"))]
    idx = {L("h"): _line(L("h"), "MAS.BLOCK", "m2", "K:walls t=0.15", v=net)}
    after = {L("u"): _line(L("u"), "MAS.UNITS.BLACK", "pcs", "x", v=units),
             L("m"): _line(L("m"), "MAS.MORTAR.BLACK", "m3", "x", v=mortar)}
    return {"rows": rows}, idx, after


def test_host_015_by_hand():
    rows, tot = M.hosts_015(*_host())
    assert rows[0]["units"] == ["116.25", "120.5"] and rows[0]["panel_mortar_m3"] == ["0.102881", "0.106643"]
    assert tot["base_m2"] == "9.64" and tot["low_m2"] == "9.3"
    assert Decimal("9.30") * Decimal("12.5") == Decimal("116.25") and Decimal("9.64") * Decimal("12.5") == Decimal("120.5")


def test_host_015_adverse():
    with pytest.raises(M.ManifestError, match="re-derivation"):
        M.hosts_015(*_host(units=125.0))                                  # 10.00 x 12.5: the lintel face not taken out
    with pytest.raises(M.ManifestError, match="stale"):
        M.hosts_015(*_host(net=10.5))
    with pytest.raises(M.ManifestError, match="module not stated"):
        M.hosts_015(*_host(why="host held D-39"))


# ---- (b) re-measure ------------------------------------------------------------------------------------------------

def _t650(lo=0.036, hi=0.04377):
    return {"per_opening": {"D-1F-07": {"line_id": L("d"), "why": "FLAGGED_DEFICIT", "low_m3": lo, "high_m3": hi},
                            "L-GF-01": {"line_id": L("g"), "why": "existence HELD_REGISTER", "low_m3": None,
                                        "high_m3": None}}}


def _lintels():
    idx = {L(c): _line(L(c), "STR.CONC.LINTEL", "m3", f"K:{c}", "HELD") for c in "dg"}
    order = [("PKG", [M9.row("PKG", f"R-T650-1/{c}", "TEXT_ONLY", L(c), dict(BLANK), None, "HELD", "v",
                             beside={"cause": "x; Checker re-measure pending"}) for c in "dg"])]
    return idx, order


def test_remeasure_replaces_the_pending_rows():
    idx, order = _lintels()
    repl, replaced = M.remeasure_rows(_t650(), order, idx, merged=MK)
    order2 = M.replace_ops(order, repl)
    after, rep = OV.apply(idx, order2)
    assert (after[L("d")]["held_low"], after[L("d")]["held_high"]) == (0.036, 0.04377)
    assert after[L("g")] == idx[L("g")] and "0.072" in repl[order[0][1][1]["op_id"]]["beside"]["cause"]
    assert all(r["status"] == "APPLIED" for r in rep["rows"]) and len(replaced) == 2
    assert Decimal("0.15") * Decimal("0.20") * Decimal("1.20") == Decimal("0.036")
    assert Decimal("0.15") * Decimal("0.20") * Decimal("1.459") == Decimal("0.04377")


def test_remeasure_adverse():
    idx, order = _lintels()
    with pytest.raises(M.ManifestError, match="Checker's"):
        M.remeasure_rows(_t650(hi=0.048), order, idx, merged=MK)
    with pytest.raises(M.ManifestError, match="pending rows"):
        M.remeasure_rows(_t650(), [("PKG", [])], idx, merged=MK)
    with pytest.raises(M.ManifestError, match="not MERGED"):
        M.remeasure_rows(_t650(), order, idx, merged={})


# ---- (c) CN NOT_APPLICABLE, threshold, downgrade -------------------------------------------------------------------

def _t647(printed=True):
    return {"fix_rows": [{"id": f"FR-K-{i}", "line_id": L(c), "proposed_state": "NOT_APPLICABLE_WITH_EVIDENCE",
                          "inputs_printed": printed, "hand_calculation": "CN cells struck: no column", "evidence": "p.9",
                          "verdict_proposal": "ENGINE_WRONG"} for i, c in enumerate("12345", 1)]}


def _cols(cls="HELD"):
    return {L(c): _line(L(c), "STR.CONC.COLUMN", "m3", f"K:CN{c}", cls, v=0.378 if cls == "RELEASED" else None)
            for c in "12345"}


def test_cn_not_applicable():
    rows = M.cn_rows(_t647(), _cols(), [], merged=MK)
    after, _ = OV.apply(_cols(), [(M.P_CN, rows)])
    assert all(after[L(c)]["class"] == "EXCLUDED" for c in "12345")


def test_cn_adverse():
    with pytest.raises(M.ManifestError, match="only moves a HELD line"):
        M.cn_rows(_t647(), _cols("RELEASED"), [], merged=MK)
    with pytest.raises(M.ManifestError, match="printed-absence"):
        M.cn_rows(_t647(printed=False), _cols(), [], merged=MK)


def _t648(value="0.15"):
    return {"fix_rows": [{"line_id": L("t"), "kind": "SET", "unit": "m2", "value": value, "basis": "1.000 x 0.150",
                          "terms": {"clear_width_m": ["1.0", "own read"], "wall_depth_m": ["0.15", "own read"]}}]}


def test_threshold_and_freelancer_refused():
    idx = {L("t"): _line(L("t"), "ARCH.THRESHOLD", "m2", "K:strip", "HELD")}
    r = M.threshold_row(_t648(), idx, [], merged=MK)
    assert r["after"]["measured_net"] == 0.15 and r["evidence"]["status"] == "DRAWING-CONFIRMED"
    with pytest.raises(M.ManifestError, match="is not"):
        M.threshold_row(_t648("0.18"), idx, [], merged=MK)
    with pytest.raises(M.ManifestError, match="freelancer"):
        M.row("K", "k", "SET", L("t"), dict(BLANK), M9.released(72.01), "DRAWING-CONFIRMED", "v",
              beside={"basis": "freelancer workbook 72.01 m2"})
    with pytest.raises(OV.OverlayError, match="HELD_AS"):
        OV.validate([M.row("K", "k", "SET", L("t"), M9.released(0.15), M9.held(0.0, 0.0), "HELD", "v")])


def test_downgrade(monkeypatch):
    monkeypatch.setattr(M, "DGV", {"DGP-T649-1111111111111111": (L("r"), "FIN.MARBLE.TREAD", "m2", "3.105", "3.795")})
    idx = {L("r"): _line(L("r"), "FIN.MARBLE.TREAD", "m2", "K:flight", v=3.105)}
    rows, chained = M.downgrade_rows(idx, [], merged=MK)
    after, _ = OV.apply(idx, [(M.P_DGV, rows)])
    assert after[L("r")]["class"] == "HELD" and (after[L("r")]["held_low"], after[L("r")]["held_high"]) == (3.105, 3.795)
    with pytest.raises(M.ManifestError, match="did not validate"):
        M.downgrade_rows(idx, [], merged=MK, validated=())
    idx[L("r")]["measured_net"] = 3.0
    with pytest.raises(M.ManifestError, match="low end"):
        M.downgrade_rows(idx, [], merged=MK)


# ---- R-T652-2 ------------------------------------------------------------------------------------------------------

def test_stale_cause_flagged_and_gate_b_column():
    pl = [{"line_id": L("x"), "item_code": "MAS.UNITS.BLACK", "class": "HELD", "cause": "0.15 m module not stated",
           "cause_source": "K"},
          {"line_id": L("y"), "item_code": "STR.CONC.LINTEL", "class": "HELD", "cause": "x; Checker re-measure pending",
           "cause_source": "K"},
          {"line_id": L("z"), "item_code": "MAS.UNITS.BLACK", "class": "HELD", "cause": "host held D-39",
           "cause_source": "K"}]
    assert [f["line_id"] for f in R.stale_causes(pl)] == [L("x"), L("y")]
    line = _line(L("w"), "MAS.UNITS.BLACK", "pcs", "x", v=1.0)
    assert R.column_r3(L("w"), line, None, "DRAWING-CONFIRMED", {L("w")}) == R.T.WIRED
    with pytest.raises(R.TrialError, match="Gate B"):
        R.column_r3(L("w"), line, None, "UNKNOWN", {L("w")})


# ---- the training villa -------------------------------------------------------------------------------------------

@pytest.fixture(scope="module")
def built():
    return M.build()


@pytest.fixture(scope="module")
def trial():
    return R.build()


def test_training_villa_is_the_committed_rebuild(built):
    assert M.OUT_JSON.read_text(encoding="utf-8") == M.dumps(built)


def test_training_villa_closes_by_hand(built):
    o = built["overlay"]
    assert o["lines"] == {"base_v3_0_59": 5073, "after_v18": 5152, "after_v19": 5152}
    assert o["stale"] == 0 and o["unexplained_conflicts"] == 0 and o["other_lines_changed_vs_v18_overlay"] == []
    bm = built["base_move"]
    assert bm["stage_lines"] == 74 and bm["overlay_adds_removed"] == 74
    assert bm["stage_by_code"] == {"MAS.GLUE.AAC": 17, "MAS.MORTAR.BLACK": 20, "MAS.UNITS.BLACK": 20,
                                   "MAS.UNITS.WHITE": 17}
    f = built["f_c_t498_1"]["totals"]
    assert (f["contract_m2"], f["base_m2"], f["low_m2"]) == ("178.571", "175.871", "175.531")
    assert (f["units_low"], f["units_high"]) == ("2194.1375", "2198.3875")
    assert Decimal("175.531") * Decimal("12.5") == Decimal("2194.1375")
    t = built["totals"]
    li = t["STR.CONC.LINTEL|m3"]
    assert (li["v18"]["held_low"], li["v19"]["held_low"]) == ("0.955692", "0.991692")
    assert (li["v18"]["held_high"], li["v19"]["held_high"]) == ("1.379112", "1.422882")
    assert t["STR.CONC.COLUMN|m3"]["v19"]["excluded_n"] - t["STR.CONC.COLUMN|m3"]["v18"]["excluded_n"] == 5
    assert t["ARCH.THRESHOLD|m2"]["v19"]["released"] == "0.15"
    assert Decimal(t["FIN.MARBLE.TREAD|m2"]["v18"]["released"]) - Decimal(t["FIN.MARBLE.TREAD|m2"]["v19"]["released"]) \
        == Decimal("3.105")
    assert Decimal(t["FIN.STAIR.STEP_LM|lm"]["v18"]["released"]) - Decimal(t["FIN.STAIR.STEP_LM|lm"]["v19"]["released"]) \
        == Decimal("10.35")
    g = built["count_convention_gaps"]
    assert g["n"] == 17 and g["kg_A"] == g["kg_A_plus_1"] == "51.574073"
    assert [s["to"] for s in built["statement_only_ops"]] == ["PARTIALLY VERIFIED"] * 2
    assert built["candidate_files_touched"] == 0 and built["released_quantities_changed"] == 0


def test_trial_r3_is_the_committed_rebuild(trial):
    assert R.dumps(trial) == R.OUT_JSON.read_text(encoding="utf-8")
    assert R.render_md(trial) == R.OUT_MD.read_text(encoding="utf-8")
    assert R.T.render_csv(trial) == R.OUT_CSV.read_text(encoding="utf-8")


def test_trial_r3_closes_by_hand(trial):
    pl = trial["per_line"]
    held = [p for p in pl if p["class"] == "HELD"]
    assert len(pl) == trial["lines"]["after_v19"] == 5152
    assert trial["held"]["with_cause"] >= R.BASELINE_HELD_R2 and trial["held"]["lines"] == len(held)
    assert trial["held"]["with_cause"] + trial["held"]["finding_F_T636_1"] == len(held)
    assert all(p["measured_net"] is None for p in held)
    for unit, g in trial["unit_grand"].items():
        rel = sum((Decimal(str(p["measured_net"])) for p in pl if p["unit"] == unit and p["class"] == "RELEASED"),
                  Decimal(0))
        assert Decimal(g["released"]) == rel == Decimal(g["wired"]) + Decimal(g["overlay"]) + Decimal(g["unverified"])
        assert g["total"] is None
    sub = {(t["trade"], t["unit"]): t["subtotal"] for t in trial["trades"]}
    b9 = sub[("B9", "pcs")]
    assert (b9["released"], b9["wired"], b9["overlay"]) == ("3269.9375", "1075.8", "2194.1375")
    assert Decimal("777.05") + Decimal("298.75") == Decimal(b9["wired"])
    b9m = sub[("B9", "m3")]
    assert (b9m["wired"], b9m["overlay"], b9m["unverified"]) == ("1.269444", "2.020393", "0.098145")
    assert sub[("B11", "kg")]["released"] == "9628.462205" and sub[("B11", "kg")]["total"] is None
    assert trial["stale_causes_F_T652_2"] == []
    assert trial["candidate_files_touched"] == 0 and trial["released_quantities_changed"] == 0


def test_write_outputs():
    if os.environ.get("URBAN_T652_WRITE") != "1":
        pytest.skip("writer: set URBAN_T652_WRITE=1")
    M.write_outputs()
    R.write_outputs()
