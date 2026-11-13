"""T-654: WIRING MANIFEST V20 on ARCH_TAKEOFF_V3.0.61 + TRIAL BOQ r4 (R-T654-1 / R-T654-2).

Synthetic villa K654 (not the training villa; hand values):
  text-only version: a threshold line RELEASED 0.12 m2 that the merged version binds at 0.12 keeps its state; bound at
    0.13 it is refused (a text-only version moves no quantity).
  restatement: plaster line RELEASED 10.0 m2 (PROVISIONAL), merged after HELD 12.0 .. 12.5; the overlay carried it as
    a pre-merge SET 10.0 -> 12.0 .. 12.5 with a chained door-head row 12.0 .. 12.5 -> 12.1 .. 12.5: the pre-merge SET
    leaves, the chained row still applies, the rebuilt index is byte-equal; a pre-merge SET 10.0 -> 12.0 .. 12.6 (not
    the merged line) is refused; a merged before that is not the base, or a merged after with a value, is refused.
  cross-trade bound (F-T652-1 form): host contract 10.00 m2, REQUIRED faces K-D7 0.32 + K-D1 0.36, HELD face 0.34;
    Checker bound for K-D7 0.036 .. 0.04377 m3 in a 0.15 m wall -> face 0.24 .. 0.2918 m2 -> base 10 - 0.36 - 0.2918
    - 0.34 = 9.0082 .. 10 - 0.36 - 0.24 - 0.34 = 9.06 m2 -> units 9.0082 x 12.5 = 112.6025 .. 9.06 x 12.5 = 113.25 pcs
    (was RELEASED 8.98 x 12.5 = 112.25), panel 0.099653 .. 0.100226 m3 (was 0.099341).
Adverse: the released value inside the new bound (not this rule's case); a bound that is not the Checker's; no merged
verdict; a TEXT_ONLY carrier on a line the merged version does not name; a line diff with an unnamed line, or a quantity
moved by a merge already in the overlay. Then the training-villa build must be the committed rebuild and close by hand."""

import os
import sys
from decimal import Decimal
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research/agents_t654"))
import manifest_v20 as M          # noqa: E402
import trial_boq_r4 as R          # noqa: E402

M9, OV = M.M9, M.OV
BLANK = {"class": "HELD", "measured_net": None, "held_low": None, "held_high": None}


def L(c):
    return "L-" + c * 20


def _line(lid, code, unit, elem, cls="RELEASED", v=None, lo=None, hi=None):
    return {"line_id": lid, "item_code": code, "unit": unit, "element_id": elem, "class": cls, "measured_net": v,
            "held_low": lo, "held_high": hi}


# ---- (a) text-only version -----------------------------------------------------------------------------------------

def _thr_entry(net):
    return {"action": "MEASURE_PAIR", "line_id": L("t"),
            "expect": {"item_code": "FIN.MARBLE.THRESHOLD", "element_id": "K-THR-1", "unit": "m2",
                       "measured_net": net}}


def test_text_only_version_moves_no_quantity():
    base = {L("t"): _line(L("t"), "FIN.MARBLE.THRESHOLD", "m2", "K-THR-1", v=0.12)}
    assert M.text_only_60(base, [_thr_entry(0.12), dict(_thr_entry(0.12), action="MATERIAL_STATE")]) == \
        {L("t"): ["MATERIAL_STATE", "MEASURE_PAIR"]}
    with pytest.raises(M.ManifestError, match="moves no quantity"):
        M.text_only_60(base, [_thr_entry(0.13)])
    with pytest.raises(M.ManifestError, match="not in the V3.0.59 base"):
        M.text_only_60({}, [_thr_entry(0.12)])


# ---- (b) the restatement --------------------------------------------------------------------------------------------

def _t563(before=None, after=None, manifest=(12.0, 12.5)):
    return {"rows": [{"line_id": L("p"), "room": "K-01", "paint_line_id": L("q"), "paint_byte_identical": True,
                      "manifest_after": list(manifest),
                      "before": before or {"state": "PROVISIONAL", "value": 10.0, "low": None, "high": None},
                      "after": after or {"state": "BOUNDED_EXPOSURE", "value": None, "low": 12.0, "high": 12.5}}]}


def _base():
    return {L("p"): _line(L("p"), "FIN.PLASTER", "m2", "K:WALL_FINISH:K_01:PLASTER", v=10.0),
            L("q"): _line(L("q"), "FIN.PAINT", "m2", "K:WALL_FINISH:K_01:PAINT", cls="HELD")}


def _order(stage_after=(12.0, 12.5)):
    pre = M9.row("T-563", "PLASTER_HEIGHT_V1", "SET", L("p"), M9.released(10.0), M9.held(*stage_after), "HELD", "v")
    paint = M9.row("T-563", "PAINT_UNCHANGED", "TEXT_ONLY", L("q"), dict(BLANK), None, "HELD", "v")
    door = M9.row("T-563", "FR-K617", "SET", L("p"), M9.held(12.0, 12.5), M9.held(12.1, 12.5), "HELD", "v")
    return [("T-563", [pre, paint, door])]


def _stage(n=1):
    s = M.stage_61(_base(), _t563())
    assert len(s) == n
    return s


def test_restatement_is_an_identity(monkeypatch):
    with pytest.raises(M.ManifestError, match="names 11"):
        _stage()                                           # the training-villa guard: 11 lines
    monkeypatch.setattr(M, "stage_61", lambda base, t: {L("p"): {
        "before": M9.released(10.0), "after": M9.held(12.0, 12.5), "paint": L("q"), "room": "K-01"}})
    stage = M.stage_61(_base(), _t563())
    before, _ = OV.apply(_base(), _order())
    order_r, removed = M.rebase_563(_order(), stage)
    after, rep = OV.apply(M.base_v3061(_base(), stage), order_r)
    assert removed == ["T-563|PLASTER_HEIGHT_V1|" + L("p"), "T-563|PAINT_UNCHANGED|" + L("q")]
    assert after == before and after[L("p")]["held_low"] == 12.1 and after[L("p")]["held_high"] == 12.5
    assert all(r["status"] == "APPLIED" for r in rep["rows"])


def test_restatement_adverse(monkeypatch):
    with pytest.raises(M.ManifestError, match="not the base line"):
        M.stage_61(_base(), _t563(before={"state": "PROVISIONAL", "value": 9.0, "low": None, "high": None}))
    with pytest.raises(M.ManifestError, match="HELD only"):
        M.stage_61(_base(), _t563(after={"state": "PROVISIONAL", "value": 12.0, "low": None, "high": None}))
    with pytest.raises(M.ManifestError, match="never a value"):
        M.stage_61(_base(), _t563(after={"state": "BLOCKED_RFI", "value": 0.0, "low": None, "high": None}))
    stage = {L("p"): {"before": M9.released(10.0), "after": M9.held(12.0, 12.5), "paint": L("q"), "room": "K-01"}}
    with pytest.raises(M.ManifestError, match="refused"):
        M.rebase_563(_order(stage_after=(12.0, 12.6)), stage)          # the pre-merge row is not the merged line
    with pytest.raises(M.ManifestError, match="missing"):
        M.rebase_563([("T-563", [])], stage)


def test_text_only_carrier_adverse():
    base = {L("t"): _line(L("t"), "FIN.MARBLE.THRESHOLD", "m2", "K-THR-1", v=0.12)}
    op = M9.row("T-423 r2", "TEXT_ONLY_22", "TEXT_ONLY", L("t"), M9.released(0.12), None, "HELD", "v")
    out, removed = M.rebase_423([("T-423 r2", [op]), ("X", [])], base, [L("t")], [])
    assert removed == [op["op_id"]] and out == [("X", [])]
    with pytest.raises(M.ManifestError, match="refused"):
        M.rebase_423([("T-423 r2", [op])], base, [], [])                # a line the merged version does not name
    with pytest.raises(M.ManifestError, match="refused"):
        M.rebase_423([("T-423 r2", [op])], {L("t"): dict(base[L("t")], measured_net=0.13)}, [L("t")], [])


# ---- (c) cross-trade bound --------------------------------------------------------------------------------------------

def _f_inputs(units=112.25, mortar=0.099341, bound=("0.036", "0.04377")):
    lint = [{"opening_id": "K-D7", "kind": "REQUIRED", "face_m2": 0.32, "face_max_m2": None},
            {"opening_id": "K-D1", "kind": "REQUIRED", "face_m2": 0.36, "face_max_m2": None},
            {"opening_id": "K-D2", "kind": "HELD_RANGE", "face_m2": None, "face_max_m2": 0.34}]
    rows = [{"line_id": L(c), "item_code": code, "unit": u, "source_line_id": L("h"), "contract_net_m2": 10.0,
             "element_id": "MATERIAL:K:walls t=0.15#BLOCKWORK:A", "lintels": lint}
            for c, code, u in (("u", "MAS.UNITS.BLACK", "pcs"), ("m", "MAS.MORTAR.BLACK", "m3"))]
    t650 = {"per_opening": {"K-D7": {"low_m3": bound[0], "high_m3": bound[1]}}}
    idx = {L("h"): _line(L("h"), "MAS.BLOCK", "m2", "K:walls t=0.15", v=10.0),
           L("u"): _line(L("u"), "MAS.UNITS.BLACK", "pcs", "x", v=units),
           L("m"): _line(L("m"), "MAS.MORTAR.BLACK", "m3", "x", v=mortar)}
    order = [("T-498", [M9.row("T-498", "FR-K615", "SET", L(c), dict(BLANK), M9.released(v), "HELD", "v")
                        for c, v in (("u", units), ("m", mortar))])]
    return {"rows": rows}, t650, idx, order


MK = {"T-652": {"merge": "k652", "verdict": "K654 F-T652-1 accepted"}}


@pytest.fixture
def kvilla(monkeypatch):
    monkeypatch.setattr(M, "F_T652_1", {"opening": "K-D7", "host": L("h"), "units": L("u"), "mortar": L("m")})


def test_cross_trade_bound_by_hand(kvilla):
    rows, calc = M.f_t652_1_rows(*_f_inputs(), merged=MK)
    assert calc["face_m2"] == ["0.24", "0.2918"] and calc["base_m2"] == ["9.0082", "9.06"]
    assert Decimal("9.0082") * Decimal("12.5") == Decimal("112.6025") and Decimal("9.06") * 12 + Decimal("9.06") / 2 \
        == Decimal("113.25")
    assert calc["units"]["bound"] == ["112.6025", "113.25"] and calc["units"]["was"] == "112.25"
    assert calc["panel mortar"]["bound"] == ["0.099653", "0.100226"]
    for r in rows:
        assert r["kind"] == "SET" and r["after"]["class"] == "HELD" and r["after"]["measured_net"] is None
        assert r["after"]["held_low"] > 0 and r["before"]["class"] == "RELEASED" and r["package"] == "T-498"
    after, rep = OV.apply(_f_inputs()[2], [("T-498", rows)])
    assert after[L("u")]["held_low"] == 112.6025 and all(x["status"] == "APPLIED" for x in rep["rows"])


def test_cross_trade_bound_adverse(kvilla):
    with pytest.raises(M.ManifestError, match="inside the new bound"):
        M.f_t652_1_rows(*_f_inputs(units=113.0), merged=MK)              # the old point is inside: not this rule
    with pytest.raises(M.ManifestError, match="not the Checker's"):
        M.f_t652_1_rows(*_f_inputs(bound=("0.036", "0.048")), merged=MK)
    with pytest.raises(M.ManifestError, match="not MERGED"):
        M.f_t652_1_rows(*_f_inputs(), merged={})
    t498, t650, idx, order = _f_inputs()
    with pytest.raises(M.ManifestError, match="RELEASED"):
        M.f_t652_1_rows(t498, t650, dict(idx, **{L("u"): dict(idx[L("u")], **BLANK)}), order, merged=MK)
    with pytest.raises(M.ManifestError, match="written by"):
        M.f_t652_1_rows(t498, t650, idx, [("OTHER", order[0][1])], merged=MK)


# ---- trial r4 guards --------------------------------------------------------------------------------------------------

def _pl(lid, net=1.0, col="UNVERIFIED", cause=None):
    return {"line_id": lid, "item_code": "X", "unit": "m2", "class": "RELEASED", "measured_net": net,
            "held_low": None, "held_high": None, "column": col, "origin": "candidate V3.0.59", "cause": cause,
            "cause_source": None}


def test_line_diff_names_every_move():
    a = [_pl(L("a")), _pl(L("b")), _pl(L("c"), col=R.R3.WIRED59)]
    b = [_pl(L("a"), net=2.0), dict(_pl(L("b")), origin="candidate V3.0.61"), dict(_pl(L("c"), col=R.WIRED61),
                                                                                 origin="candidate V3.0.61")]
    d = R.line_diff(a, b, {L("a"): "V20 row"}, {L("a")})
    assert [x["line_id"] for x in d] == [L("a")] and d[0]["quantity_moved"]            # labels are not moves
    with pytest.raises(R.TrialError, match="no Gate B merge"):
        R.line_diff(a, [_pl(L("a")), _pl(L("b"), net=3.0), b[2]], {L("a"): "V20 row"}, {L("a")})
    with pytest.raises(R.TrialError, match="only a V20 row"):
        R.line_diff(a, b, {L("a"): "Gate B merge"}, set())                              # merge already in the overlay


def test_merged_cause_first():
    causes = {L("p"): {"source": "old census", "cause": "W24 not printed", "also_stated_by": ["x"]}}
    rec = R.T._rec(563, "candidate record V3.0.61 (T-563)", "roof build-up D-39 / DCR-6")
    out = R.merged_cause_first(causes, {L("p"): rec})
    assert out[L("p")]["cause"] == "roof build-up D-39 / DCR-6" and out[L("p")]["also_stated_by"] == ["old census", "x"]


# ---- the training villa (committed rebuild + hand closures) ---------------------------------------------------------

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
    assert o["lines"] == {"base_v3_0_61": 5073, "after_v19": 5152, "after_v20": 5152}
    assert o["stale"] == 0 and o["unexplained_conflicts"] == 0 and o["other_lines_changed_vs_v19_overlay"] == []
    bm = built["base_move"]
    assert bm["v3_0_60_text_only"]["lines"] == 22 and len(bm["v3_0_61_restated"]) == 11
    assert bm["overlay_rows_removed_n"] == 39 == 17 + 11 + 11
    assert sorted(bm["base_totals_moved"]) == ["FIN.PLASTER|m2"]
    pl = bm["base_totals_moved"]["FIN.PLASTER|m2"]
    assert (pl["before"]["released"], pl["after"]["released"]) == ("580.5819", "363.3738")
    four = [r for r in bm["v3_0_61_restated"] if r["v3_0_60"]["class"] == "RELEASED"]
    assert sum(Decimal(str(r["v3_0_60"]["measured_net"])) for r in four) == Decimal("217.2081")
    assert sum(Decimal(str(r["v3_0_61"]["held_low"])) for r in four) == Decimal("262.01799")
    door = {r["room"]: (Decimal(str(r["after_v20_overlay"]["held_low"])) - Decimal(str(r["v3_0_61"]["held_low"])))
            for r in bm["v3_0_61_restated"] if r["after_v20_overlay"] != r["v3_0_61"]}
    assert door == {"GF-08": Decimal("0.59"), "1F-13": Decimal("0.59"), "2F-01": Decimal("0.24")}   # FR-T617-1
    f = built["f_t652_1"]
    assert f["face_m2"] == ["0.24", "0.2918"] and f["base_m2"] == ["55.9211", "55.9729"]
    assert Decimal("58.2529") - Decimal("1.70") - Decimal("0.2918") - Decimal("0.34") == Decimal("55.9211")
    assert f["units"]["bound"] == ["699.01375", "699.66125"] and f["units"]["was"] == "698.66125"
    assert Decimal("55.9211") * Decimal("12.5") == Decimal("699.01375")
    assert f["panel mortar"]["bound"] == ["0.618627", "0.6192"]
    assert sorted(built["totals"]) == ["MAS.MORTAR.BLACK|m3", "MAS.UNITS.BLACK|pcs"]
    u = built["totals"]["MAS.UNITS.BLACK|pcs"]
    assert Decimal(u["v19"]["released"]) - Decimal(u["v20"]["released"]) == Decimal("698.66125")
    assert built["candidate_files_touched"] == 0


def test_trial_r4_is_the_committed_rebuild(trial):
    assert R.dumps(trial) == R.OUT_JSON.read_text(encoding="utf-8")
    assert R.render_md(trial) == R.OUT_MD.read_text(encoding="utf-8")
    assert R.T.render_csv(trial) == R.OUT_CSV.read_text(encoding="utf-8")


def test_trial_r4_closes_by_hand(trial):
    pl = trial["per_line"]
    held = [p for p in pl if p["class"] == "HELD"]
    assert len(pl) == trial["lines"]["after_v20"] == 5152
    assert trial["held"]["with_cause"] >= R.BASELINE_HELD_R3 and trial["held"]["lines"] == len(held)
    assert trial["held"]["with_cause"] + trial["held"]["finding_F_T636_1"] == len(held)
    assert all(p["measured_net"] is None for p in held)
    for unit, g in trial["unit_grand"].items():
        rel = sum((Decimal(str(p["measured_net"])) for p in pl if p["unit"] == unit and p["class"] == "RELEASED"),
                  Decimal(0))
        assert Decimal(g["released"]) == rel == Decimal(g["wired"]) + Decimal(g["overlay"]) + Decimal(g["unverified"])
        assert g["total"] is None
    sub = {(t["trade"], t["unit"]): t["subtotal"] for t in trial["trades"]}
    b9 = sub[("B9", "pcs")]
    assert (b9["released"], b9["wired"], b9["overlay"]) == ("2571.27625", "1075.8", "1495.47625")
    assert Decimal("2194.1375") - Decimal("698.66125") == Decimal("1495.47625")
    b9m = sub[("B9", "m3")]
    assert (b9m["wired"], b9m["overlay"], b9m["unverified"]) == ("1.269444", "1.402078", "0.098145")
    assert Decimal("2.020393") - Decimal("0.618315") == Decimal("1.402078")
    assert sub[("B11", "kg")]["released"] == "9628.462205"
    assert trial["diff_r3_r4_count"] == {"lines": 13, "quantity_moved": 2}
    assert sorted(trial["vs_r3"]["trade_unit"]) == ["B9|m3", "B9|pcs"]
    restated = trial["gate_b_restated_held_lines"]
    for p in pl:
        if p["line_id"] in restated:
            assert p["class"] == "HELD" and "D-39 / DCR-6" in p["cause"] and p["cause_kind"].startswith("candidate "
                                                                                                         "record V3.0.61")
    assert trial["stale_causes_F_T652_2"] == []
    assert trial["candidate_files_touched"] == 0 and trial["released_quantities_changed"] == 0


def test_write_outputs():
    if os.environ.get("URBAN_T654_WRITE") != "1":
        pytest.skip("writer: set URBAN_T654_WRITE=1")
    M.write_outputs()
    R.write_outputs()
