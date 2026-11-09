"""T-649: WIRING MANIFEST V18 + overlay dry run + TRIAL BOQ r2 (R-T649-1 / R-T649-2).

Synthetic villa K649 (not the training villa; hand values):
  strip: HELD 0.04 .. 0.12 m3; drawn 0.20 x 0.50 = 0.100 m2; depths B4 0.50 / B7 0.75: RELEASED 0.050 + companion HELD
    0 .. 0.025 (0.100 x 0.25); the band stamp line RELEASED 0.282743 gets a TEXT_ONLY stamp.
  downgrades: two column bar lines RELEASED 39.822 kg each, Checker-validated -> HELD blank; B11 100.0 -> 20.356 kg.
  stair: riser HELD blank -> RELEASED 12 x (0.166667 - 0.03) x 1.15 = 1.886 m2 (DRAWING-CONFIRMED); flight HELD blank ->
    HELD 9 x 0.343188 = 3.088689 .. 11 x = 3.775064 lm; a tread 9 x 0.30 x 1.15 = 3.105 m2 on the same flight is ruled
    DOWNGRADE PROPOSED (its goings are the disputed edges), proposal 3.105 .. 3.795, never applied.
  roof: screed HELD blank -> AT_LEAST 2.512672 m3 (high OPEN).
  lintels: X-1 NEW bound 0.054 .. 0.1185; pair X-2 + X-3 0.06 .. 0.07914 carried once on X-2, X-3 names it; X-4 pending
    re-measure stays HELD blank with its withheld bound named.
Adverse: a downgrade that promotes / names a HELD line / is not validated; a strip companion that does not re-add to B7;
a stale stair before; a release from a C_OPEN row; HELD as 0; a riser beside a second riser on one flight (double count);
an AT_LEAST row with a high end; a lintel bound that does not re-add to the census summary; a 'not merged' task with a
merge. Then the training-villa build must be the committed rebuild and close by hand."""

import copy
import os
import sys
from decimal import Decimal
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research/agents_t649"))
import manifest_v18 as M          # noqa: E402
import trial_boq_r2 as R          # noqa: E402

M9, OV = M.M9, M.OV
MK = {t: {"merge": "k" + t[-3:], "verdict": f"K649 {t} verdict"} for t in ("T-642", "T-645", "T-646", "T-650")}
MK["T-643"] = {"merge": "k643", "verdict": "K649 T-643 CHECKER-VALIDATED downgrade-only proposals DGP-T643-aaaaaaaa / "
                                           "bbbbbbbb (HELD, never 0)"}


def _line(lid, code, unit, elem, cls="RELEASED", v=None, lo=None, hi=None):
    return {"line_id": lid, "item_code": code, "unit": unit, "element_id": elem, "class": cls, "measured_net": v,
            "held_low": lo, "held_high": hi}


def L(c):
    return "L-" + c * 20


# ---- T-642 strip --------------------------------------------------------------------------------------------------

def _t642(b7=0.75, chi=0.025):
    return {"fix_rows": [{"id": "FR-T642-2", "line_id": M.STRIP_LINE, "change_m3": 0.05,
                          "companion": {"cause": "depth B4 vs B7 unmarked", "element": "K:BAND~DEPTH", "held_m3": [0.0, chi]}},
                         {"id": "FR-T642-4", "line_id": M.BAND49_LINE, "change_m3": 0.0}],
            "items": {"b": {"engine": {"line": {"held_low_m3": 0.04, "held_high_m3": 0.12}},
                            "drawn": {"width_m": 0.2, "length_m": 0.5, "depths_allowed_by_the_drawing": {"B4": 0.5, "B7": b7}}},
                      "d": {"engine": {"line_value_m3": 0.282743}, "delta_own_minus_line_m3": 0.0,
                            "printed_mark": {"text_handle": "K1"}}}}


def _strip_idx():
    return {M.STRIP_LINE: _line(M.STRIP_LINE, "STR.CONC.BEAM", "m3", "K:BAND", "HELD", lo=0.04, hi=0.12),
            M.BAND49_LINE: _line(M.BAND49_LINE, "STR.CONC.BEAM", "m3", "K:ARC", v=0.282743)}


def test_strip_low_end_and_companion():
    idx = _strip_idx()
    rows, out = M.strip_rows(_t642(), idx, [], merged=MK)
    assert out["released_m3"] == "0.05" and out["companion_m3"] == ["0", "0.025"]
    after, rep = OV.apply(idx, [(M.P_STRIP, rows)])
    assert after[M.STRIP_LINE]["class"] == "RELEASED" and after[M.STRIP_LINE]["measured_net"] == 0.05
    comp = [l for l in after.values() if l["element_id"] == "K:BAND~DEPTH"][0]
    assert comp["class"] == "HELD" and (comp["held_low"], comp["held_high"]) == (0.0, 0.025)
    assert after[M.BAND49_LINE] == idx[M.BAND49_LINE]                      # stamp only, no quantity
    assert all(r["status"] == "APPLIED" for r in rep["rows"])


def test_strip_adverse():
    with pytest.raises(M.ManifestError, match="is not"):
        M.strip_rows(_t642(chi=0.03), _strip_idx(), [], merged=MK)      # 0.05 + 0.03 is not 0.100 x 0.75
    idx = _strip_idx()
    idx[M.STRIP_LINE]["held_high"] = 0.10
    with pytest.raises(M.ManifestError, match="stale"):
        M.strip_rows(_t642(), idx, [], merged=MK)
    with pytest.raises(M.ManifestError, match="R1"):
        M.strip_rows(_t642(), _strip_idx(), [("OTHER", [{"line_id": M.STRIP_LINE}])], merged=MK)


# ---- T-643 downgrades -------------------------------------------------------------------------------------------

def _t643(ids=("DGP-T643-aaaaaaaa11111111", "DGP-T643-bbbbbbbb22222222"), state="HELD"):
    props = [{"proposal_id": p, "line_ids": [L(c)], "engine_qty": "39.822", "unit": "kg", "state": state,
              "reason": "UNSUPPORTED BASIS: roof datum undeclared (D-39)", "evidence": []} for p, c in zip(ids, "ab")]
    return {"part1": {"downgrade_proposals": props, "kg_proposed_held": "79.644",
                      "released_B11_before_kg": "100.0", "released_B11_if_downgrades_applied_kg": "20.356"}}


def _bars(cls="RELEASED"):
    return {L(c): _line(L(c), "STR.REBAR", "kg", f"K:COL-{c}", cls, v=39.822 if cls == "RELEASED" else None)
            for c in "ab"}


def test_downgrade_normal():
    idx = _bars()
    rows, out = M.downgrade_rows(_t643(), idx, [], merged=MK)
    assert out == {"kg": "79.644", "n": 2, "t643_base_kg": ["100.0", "20.356"]}
    after, _ = OV.apply(idx, [(M.P_DG, rows)])
    assert all(after[L(c)]["class"] == "HELD" and after[L(c)]["held_low"] is None and after[L(c)]["measured_net"] is None
               for c in "ab")
    assert rows[0]["beside"]["cause"].startswith("UNSUPPORTED BASIS")


def test_downgrade_adverse():
    with pytest.raises(M.ManifestError, match="never promotes"):
        M.downgrade_rows(_t643(), _bars("HELD"), [], merged=MK)          # a downgrade never moves a HELD line
    with pytest.raises(M.ManifestError, match="did not validate"):
        M.downgrade_rows(_t643(ids=("DGP-T643-cccccccc1", "DGP-T643-aaaaaaaa1")), _bars(), [], merged=MK)
    with pytest.raises(M.ManifestError, match="HELD only"):
        M.downgrade_rows(_t643(state="RELEASED"), _bars(), [], merged=MK)  # promoting record refused
    with pytest.raises(OV.OverlayError, match="HELD_AS"):
        OV.validate([M9.row("K", "k", "SET", L("a"), M9.released(39.822), M9.held(0.0, 0.0), "HELD", "v")])


# ---- T-645 stair ----------------------------------------------------------------------------------------------------

BLANK = {"class": "HELD", "held_high": None, "held_low": None, "measured_net": None}


def _t645(release_cls="A_DRAWN", before=BLANK):
    lines = [{"class": release_cls, "flight": "MS1-L", "item_code": "FIN.MARBLE.RISER", "line_id": L("1"),
              "element_id": "K-S:flight 1",
              "fix": {"kind": "SET", "before": before, "basis": "12 x (0.166667 - 0.03) x 1.15",
                      "after": {"class": "RELEASED", "evidence": "DRAWING-CONFIRMED", "measured_net": "1.886"}}},
             {"class": "C_OPEN", "flight": "MS1-L", "item_code": "FIN.STAIR.FLIGHT", "line_id": L("2"),
              "element_id": "K-S:flight 1", "cause": "C-ST-4 riser count conflict",
              "fix": {"kind": "SET", "before": BLANK, "basis": "9 .. 11 goings",
                      "after": {"class": "HELD", "held_low": "3.088689", "held_high": "3.775064", "measured_net": None}}}]
    return {"lines": lines, "counts": {"fix_rows": 2},
            "released_by_code": {"FIN.MARBLE.RISER": "1.886"},
            "bounded_by_code": {"FIN.STAIR.FLIGHT": {"low": "3.088689", "high": "3.775064", "n": 1, "open_n": 0}},
            "flights": {"MS1-L": {"R": "0.166667", "goings": 9, "risers": 10, "widths_lm": "11.45"}}}


def _stair_idx(tread=3.105):
    return {L("1"): _line(L("1"), "FIN.MARBLE.RISER", "m2", "K-S:flight 1", "HELD"),
            L("2"): _line(L("2"), "FIN.STAIR.FLIGHT", "lm", "K-S:flight 1", "HELD"),
            L("3"): _line(L("3"), "FIN.MARBLE.TREAD", "m2", "K-S:flight 1", v=tread),
            L("4"): _line(L("4"), "FIN.STAIR.STEP_LM", "lm", "K-S:flight 1", v=10.35)}


def test_stair_rows_rulings_and_f_t645_1(monkeypatch):
    monkeypatch.setitem(M.F_T645_1, "element", "K-S:flight 1")
    idx = _stair_idx()
    rows, out = M.stair_rows(_t645(), idx, [], merged=MK)
    assert out["released"] == {"FIN.MARBLE.RISER": "1.886"}
    assert out["bounded"]["FIN.STAIR.FLIGHT"] == {"low": "3.088689", "high": "3.775064", "n": 1}
    rul = M.stair_rulings(rows, idx)
    after, rep = OV.apply(idx, [(M.P_STAIR, rows)], rul)
    assert all(c["status"] == "EXPLAINED" for c in rep["conflicts"]) and len(rep["conflicts"]) == 2
    assert after[L("1")]["measured_net"] == 1.886 and after[L("2")]["held_high"] == 3.775064
    ruling, props = M.mstair_ruling(_t645(), idx, [], rows)
    assert [x["goings_disputed"] for x in ruling] == [[9, 11], [9, 11]]
    assert {p["line_ids"][0]: p["proposed_bound"] for p in props} == {L("3"): ["3.105", "3.795"],
                                                                       L("4"): ["10.35", "12.65"]}
    assert all(p["checker"] is None and p["state"] == "HELD" for p in props)
    assert after[L("3")]["class"] == "RELEASED"                            # proposal only, never applied


def test_stair_adverse(monkeypatch):
    with pytest.raises(M.ManifestError, match="stale"):
        M.stair_rows(_t645(before={"class": "HELD", "held_low": "1", "held_high": "2", "measured_net": None}),
                     _stair_idx(), [], merged=MK)
    with pytest.raises(M.ManifestError, match="A_DRAWN"):
        M.stair_rows(_t645(release_cls="C_OPEN"), _stair_idx(), [], merged=MK)
    idx = _stair_idx()
    idx[L("5")] = _line(L("5"), "FIN.MARBLE.RISER", "m2", "K-S:flight 1", v=1.0)    # a second riser on the flight
    rows, _ = M.stair_rows(_t645(), idx, [], merged=MK)
    with pytest.raises(M.ManifestError, match="double count"):
        M.stair_rulings(rows, idx)
    monkeypatch.setitem(M.F_T645_1, "element", "K-S:flight 1")
    idx = _stair_idx(tread=3.45)                                             # 10 goings: not the counted 9
    rows, _ = M.stair_rows(_t645(), idx, [], merged=MK)
    with pytest.raises(M.ManifestError, match="goings"):
        M.mstair_ruling(_t645(), idx, [], rows)


# ---- T-646 roof ---------------------------------------------------------------------------------------------------

def _t646(hi=None):
    return {"lines": [{"line_id": L("r"), "element_id": "K:ROOF:FALLS", "item_code": "FIN.ROOF.SCREED",
                       "fix": {"before": BLANK, "basis": "V - strip",
                               "after": {"class": "HELD", "held_low": "2.512672", "held_high": hi, "measured_net": None}}},
                      {"line_id": L("f"), "element_id": "K:FENCE", "item_code": "EXT.FENCE.FACE", "cause": "Q-63 C"}],
            "bounded_by_code": {"FIN.ROOF.SCREED": {"low": "2.512672", "high": "OPEN", "n": 1}}, "counts": {"fix_rows": 1}}


def test_roof_at_least_and_adverse():
    idx = {L("r"): _line(L("r"), "FIN.ROOF.SCREED", "m3", "K:ROOF:FALLS", "HELD")}
    rows, out = M.roof_rows(_t646(), idx, [], merged=MK)
    after, _ = OV.apply(idx, [(M.P_ROOF, rows)])
    assert (after[L("r")]["held_low"], after[L("r")]["held_high"]) == (2.512672, None) and out["low_m3"] == "2.512672"
    with pytest.raises(M.ManifestError, match="AT_LEAST"):
        M.roof_rows(_t646(hi="3.0"), idx, [], merged=MK)


# ---- T-650 lintels ------------------------------------------------------------------------------------------------

def _op(oid, c, state, lo, hi, change, now=(None, None)):
    return {"line_id": L(c), "state": state, "low_m3": lo, "high_m3": hi, "change": change, "form": "RC_CAST_M3",
            "why": f"{oid} why", "line_class_now": "HELD", "line_low_now": now[0], "line_high_now": now[1]}


def _t650(x1_lo=0.054):
    po = {"X-1": _op("X-1", "w", "BOUNDED", x1_lo, 0.1185, "NEW_BOUND"),
          "X-2": _op("X-2", "x", "HELD_BY_NAME", None, None, "NEW_BOUND (pair, R-T524-1)"),
          "X-3": _op("X-3", "y", "HELD_BY_NAME", None, None, "NEW_BOUND (pair, R-T524-1)"),
          "X-4": _op("X-4", "z", "HELD_BY_NAME", 0.036, 0.04377, "NEW_BOUND"),
          "X-5": _op("X-5", "v", "HELD", None, None, "CAUSE_RESTATED (still HELD blank)")}
    return {"per_opening": po, "pairs": {"X-2+X-3": {"ids": ["X-2", "X-3"], "low_m3": 0.06, "high_m3": 0.07914,
                                                     "pier_m": 0.238}},
            "summary": {"m3_bounded_set": {"low_m3": 0.15, "high_known_part_m3": 0.24141, "high_open_on": []}}}


def _lint_idx():
    return {L(c): _line(L(c), "STR.CONC.LINTEL", "m3", f"K:LIN-{c}", "HELD") for c in "wxyzv"}


def test_lintels_pending_and_pair():
    idx = _lint_idx()
    order = [(M.P498, [{"line_id": L("x")}, {"line_id": L("y")}])]
    ch, own, out = M.lintel_rows(_t650(), idx, order, merged=MK, pending=("X-4",))
    assert out["low_m3"] == "0.114" and out["high_known_part_m3"] == "0.19764"            # 0.054 + 0.06 .. 0.1185 + 0.07914
    assert out["withheld_low_high_m3"] == ["0.036", "0.04377"]
    kinds = {r["line_id"]: r["kind"] for r in ch + own}
    assert kinds == {L("w"): "SET", L("x"): "SET", L("y"): "TEXT_ONLY", L("z"): "TEXT_ONLY"}
    assert {r["line_id"] for r in ch} == {L("x"), L("y")}                  # chained in T-498 (R1)
    after, _ = OV.apply(idx, [(M.P498, ch), (M.P_LINT, own)])
    assert after[L("z")]["held_low"] is None and "re-measure pending" in [r for r in own if r["line_id"] == L("z")][0][
        "beside"]["cause"]
    assert (after[L("x")]["held_low"], after[L("x")]["held_high"]) == (0.06, 0.07914) and after[L("y")]["held_low"] is None


def test_lintels_adverse():
    with pytest.raises(M.ManifestError, match="re-add"):
        M.lintel_rows(_t650(x1_lo=0.05), _lint_idx(), [], merged=MK, pending=("X-4",))
    idx = _lint_idx()
    idx[L("w")]["held_low"] = 0.01
    with pytest.raises(M.ManifestError, match="stale"):
        M.lintel_rows(_t650(), idx, [], merged=MK, pending=("X-4",))


def test_not_merged_refused_by_name():
    _, refused = M.no_row_sources(merged={"T-1": {"merge": "x", "verdict": "y"}}, no_row={"T-1": "k"},
                                  not_merged={"T-2": "READY"})
    assert refused["T-2"]["refusal"].startswith("T-2 is not MERGED")
    with pytest.raises(M.ManifestError, match="carries a merge"):
        M.no_row_sources(merged={"T-2": {"merge": "x", "verdict": "y"}}, no_row={}, not_merged={"T-2": "READY"})
    with pytest.raises(M.ManifestError, match="not MERGED"):
        M.require_merged("T-647", merged={})


def test_b8_06_reader_correction_and_relabel():
    m = {"families": [{"code": "B8-06", "candidate": {"open": R.STALE_B8_06 + " (x); held m2 1 | held V3.0.58: m2 2"}}]}
    c = R.b8_06_correction(m)
    assert c["reads_as"] == "held V3.0.58: m2 2" and c["stale_part"].startswith(R.STALE_B8_06)
    with pytest.raises(R.TrialError, match="no longer"):
        R.b8_06_correction({"families": [{"code": "B8-06", "candidate": {"open": "held V3.0.58: m2 2"}}]})
    assert R.relabel({R.OP_KIND_V17: [R.OP_KIND_V17]}) == {R.OP_KIND_V18: [R.OP_KIND_V18]}


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
    assert o["lines"] == {"base": 4999, "after_v17": 5151, "after_v18": 5152}         # + 1 strip companion
    assert o["stale"] == 0 and o["unexplained_conflicts"] == 0 and o["other_lines_changed_vs_v17_overlay"] == []
    rb = built["downgrades"]["totals"]["STR.REBAR|kg"]
    assert rb["v17"]["released"] == "9787.750205" and rb["v18"]["released"] == "9628.462205"
    assert Decimal("9216.017760") + Decimal("412.444445") == Decimal(rb["v18"]["released"])
    assert rb["v18"]["held_blank_n"] - rb["v17"]["held_blank_n"] == 4
    st = built["stair"]["totals"]
    assert st["FIN.MARBLE.RISER|m2"]["v17"]["released"] == "1.96" and st["FIN.MARBLE.RISER|m2"]["v18"]["released"] == "8.796036"
    assert st["FIN.STAIR.FLIGHT|lm"]["v18"]["released"] == "13.36392"
    assert built["roof"]["low_m3"] == "10.628996" and built["roof"]["high"] == "OPEN"
    li = built["lintels"]
    assert li["low_m3"] == "0.955692" and li["withheld_low_high_m3"] == ["0.036", "0.04377"]
    assert Decimal(li["low_m3"]) + Decimal("0.036") == Decimal("0.991692")             # the T-650 summary low
    assert sorted(li["held_named"]) == ["D-1F-07", "D-GF-12", "L-GF-01"]
    s = built["strip"]
    assert s["released_m3"] == "0.05" and s["companion_m3"] == ["0", "0.025"] and s["replaced"] == ["0.04", "0.12"]
    assert [x["line_id"] for x in built["f_t645_1"]["lines"]] == ["L-151d92470a81dd1c450b", "L-d4d764ae7bb07b474b6f"]
    assert [p["proposed_bound"] for p in built["f_t645_1"]["proposals"]] == [["3.105", "3.795"], ["10.35", "12.65"]]
    assert built["stair_edge_census_after_v18"]["doubles"] == 0 and built["candidate_files_touched"] == 0


def test_trial_r2_is_the_committed_rebuild(trial):
    assert R.dumps(trial) == R.OUT_JSON.read_text(encoding="utf-8")
    assert R.render_md(trial) == R.OUT_MD.read_text(encoding="utf-8")
    assert R.T.render_csv(trial) == R.OUT_CSV.read_text(encoding="utf-8")


def test_trial_r2_closes_by_hand(trial):
    pl = trial["per_line"]
    held = [p for p in pl if p["class"] == "HELD"]
    assert len(pl) == trial["lines"]["after_v18"] == 5152
    assert trial["held"]["with_cause"] >= 2314 and trial["held"]["lines"] == len(held)
    assert trial["held"]["with_cause"] + trial["held"]["finding_F_T636_1"] == len(held)
    assert all(p["measured_net"] is None for p in held)
    for unit, g in trial["unit_grand"].items():
        rel = sum((Decimal(str(p["measured_net"])) for p in pl if p["unit"] == unit and p["class"] == "RELEASED"),
                  Decimal(0))
        assert Decimal(g["released"]) == rel == Decimal(g["wired"]) + Decimal(g["overlay"]) + Decimal(g["unverified"])
        assert g["total"] is None
    assert all(c["re_adds_exactly"] for c in trial["aggregation_proof"])
    b11 = [t for t in trial["trades"] if t["trade"] == "B11"][0]["subtotal"]
    assert b11["released"] == "9628.462205" and b11["total"] is None
    dg = {p["line_id"] for p in pl if p.get("downgrade_proposed")}
    assert dg == {"L-151d92470a81dd1c450b", "L-d4d764ae7bb07b474b6f"}
    assert all(p["class"] == "RELEASED" for p in pl if p["line_id"] in dg)
    pend = {p["line_id"]: p["cause"] for p in held if p["line_id"] in ("L-3111418b702ac80f0ade", "L-8f69c40749d579c14bf1")}
    assert len(pend) == 2 and all("re-measure pending" in c for c in pend.values())
    assert trial["registry_text_corrections"][0]["family"] == "B8-06"
    assert trial["candidate_files_touched"] == 0 and trial["released_quantities_changed"] == 0


def test_write_outputs():
    if os.environ.get("URBAN_T649_WRITE") != "1":
        pytest.skip("writer: set URBAN_T649_WRITE=1")
    M.write_outputs()
    R.write_outputs()
