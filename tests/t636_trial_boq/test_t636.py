"""T-636: THE 10 NOV TRIAL BOQ (R-T636-1).

Synthetic villa K636 (not the training villa; hand values):
  B10 m3  L1 slab 10.5 (VERIFIED_WHOLE binding, no op)        -> WIRED 10.5
          L2 slab 4.25 (no binding, no op)                      -> UNVERIFIED 4.25; slab BOQ line 14.75 TOTAL
          L5 beam HELD 1.0 .. 1.4, cause on its overlay op (beside.cause 'D-43 section not printed')
          -> trade m3 released 14.75 = 10.5 + 0 + 4.25, NO TOTAL (1 HELD bounded 1.0 .. 1.4)
  B4 m2   L3 plaster 20 SET by a merged fix row stamped DRAWING-CONFIRMED -> OVERLAY 20, TOTAL 20
  B11 kg  L4 HELD blank, cause from a census record ('Q-71 counting open') -> NO TOTAL (1 HELD blank), never 0
  UNCODED (NOT_A_BOQ_LINE): L6 ARCH.WALL_PANEL 12 m2 (register code, reported apart, no trade figure)
Adverse: a HELD line with a measured 0 refused; an overlay line counted as WIRED refused; a base line with a status
but no binding refused; a HELD line with no record -> F-T636-1 (listed, never a typed cause); latest task wins; a
material line takes its host's cause by name (one step); a stale T-297 bound is not used.
Then the training-villa build must equal the committed outputs and close by hand."""

import copy
import json
import os
import sys
from decimal import Decimal
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research/agents_t636"))
import trial_boq as T          # noqa: E402


def _l(lid, code, unit, cls="RELEASED", v=None, lo=None, hi=None):
    return {"line_id": lid, "item_code": code, "unit": unit, "element_id": "K636:" + lid, "class": cls,
            "measured_net": v, "held_low": lo, "held_high": hi}


def _fam(code, grp, codes):
    return {"code": code, "group": grp, "item_en": code, "unit": None, "item_codes": codes, "capability": "PARTIAL",
            "candidate": {"state": "INTEGRATED_IN_CANDIDATE_AND_TESTED"}}


def _villa():
    L = [_l("L1", "STR.CONC.SLAB", "m3", v=10.5), _l("L2", "STR.CONC.SLAB", "m3", v=4.25),
         _l("L3", "FIN.PLASTER", "m2", v=20), _l("L4", "STR.REBAR", "kg", "HELD"),
         _l("L5", "STR.CONC.BEAM", "m3", "HELD", lo=1.0, hi=1.4), _l("L6", "ARCH.WALL_PANEL", "m2", v=12)]
    after = {l["line_id"]: l for l in L}
    bound = {"L1": ({"binding": "VERIFIED_WHOLE", "verdict_id": "K-1"}, T.OV.state(after["L1"]))}
    order = [("K-PKG (T-901)", [
        {"op_id": "K|SET|L3", "package": "K-PKG (T-901)", "row": "FR-T901-1", "kind": "SET", "line_id": "L3",
         "evidence": {"status": "DRAWING-CONFIRMED", "verdict_line": "BOARD T-901 VERIFIER: own re-measure AGREE"}},
        {"op_id": "K|SET|L5", "package": "K-PKG (T-901)", "row": "FR-T901-2", "kind": "SET", "line_id": "L5",
         "evidence": {"status": "HELD", "verdict_line": "BOARD T-901 VERIFIER"},
         "beside": {"cause": "beam section D-43 not printed: depth 0.50 .. 0.70"}}])]
    master = {"families": [_fam("B10-08", "B10 Concrete", ["STR.CONC.SLAB"]),
                           _fam("B10-07", "B10 Concrete", ["STR.CONC.BEAM"]), _fam("B11-01", "B11 Rebar", ["STR.REBAR"]),
                           _fam("B4-03", "B4 Walls", ["FIN.PLASTER"]), _fam("B12-01", "B12 MEP", [])],
              "not_a_boq_line_codes": {"ARCH.WALL_PANEL": {"evidence": ["register line"]}}}
    src = {"records": {"L4": [T._rec(639, "K census", "bars of L4: Q-71 counting open", kind="K census")]}}
    return after, order, master, bound, src


def _build(after, order, master, bound, src):
    return T.build(after=after, order=order, master=master, bound=bound, src=src, base_ids=set(after))


@pytest.fixture
def k():
    b = _build(*_villa())
    return b, {l["line_id"]: l for l in b["per_line"]}


def _trade(b, grp, unit):
    return next(t for t in b["trades"] if (t["trade"], t["unit"]) == (grp, unit))


def test_hand_values_and_columns(k):
    b, pl = k
    b10 = _trade(b, "B10", "m3")["subtotal"]
    assert (b10["released"], b10["wired"], b10["overlay"], b10["unverified"]) == ("14.75", "10.5", "0", "4.25")
    assert b10["total"] is None and b10["held_bounded_n"] == 1 and (b10["held_low"], b10["held_high"]) == ("1", "1.4")
    slab = _trade(b, "B10", "m3")["families"]
    slab = next(f for f in slab if f["family"] == "B10-08")["boq_lines"][0]
    assert slab["total"] == "14.75" and slab["verified_whole_lines"] == 1
    b4 = _trade(b, "B4", "m2")["subtotal"]
    assert (b4["total"], b4["overlay"], b4["wired"], b4["unverified"]) == ("20", "20", "0", "0")
    b11 = _trade(b, "B11", "kg")["subtotal"]
    assert b11["total"] is None and b11["held_blank_n"] == 1 and b11["held_low"] is None and b11["released"] == "0"
    assert (pl["L1"]["column"], pl["L2"]["column"], pl["L3"]["column"]) == (T.WIRED, T.UNVERIFIED, T.OVERLAY)
    reg = _trade(b, T.E.UNCODED_NOT_A_LINE, "m2")["subtotal"]
    assert reg["released"] == "12" and not any(t["trade"] == "B9" for t in b["trades"])
    assert all(c["re_add_exact"] for c in b["column_proof"])


def test_held_causes(k):
    b, pl = k
    assert pl["L4"]["cause"] == "bars of L4: Q-71 counting open" and pl["L4"]["cause_ids"] == ["Q-71"]
    assert pl["L5"]["cause"].startswith("beam section D-43 not printed") and "D-43" in pl["L5"]["cause_ids"]
    assert pl["L5"]["cause_source"].startswith("overlay op")
    assert b["held"] == {"lines": 2, "with_cause": 2, "finding_F_T636_1": 0}


def test_held_without_record_is_a_finding_never_a_typed_cause():
    after, order, master, bound, src = _villa()
    src["records"] = {}
    b = _build(after, order, master, bound, src)
    pl = {l["line_id"]: l for l in b["per_line"]}
    assert pl["L4"]["cause"] is None and pl["L4"]["finding"] == "F-T636-1"
    assert b["held"]["finding_F_T636_1"] == 1 and b["held"]["lines"] == 2       # listed, never dropped


def test_adverse_held_shown_as_zero_refused():
    after, order, master, bound, src = _villa()
    after["L4"]["measured_net"] = 0.0
    with pytest.raises(T.TrialError, match="HELD line carries a measured quantity"):
        _build(after, order, master, bound, src)


def test_adverse_overlay_counted_as_wired_refused(k):
    b, pl = k
    bad = copy.deepcopy(b["per_line"])
    next(p for p in bad if p["line_id"] == "L3")["column"] = T.WIRED
    with pytest.raises(T.TrialError, match="overlay quantity counted as WIRED"):
        T.guard_columns(bad, {"L3": {"op_id": "K|SET|L3"}})
    # an overlay op stamped VERIFIED stays in the OVERLAY column
    assert T.column_of("X", {"class": "RELEASED"}, {"op_id": "x"}, "VERIFIED") == T.OVERLAY


def test_adverse_base_status_without_binding_refused():
    with pytest.raises(T.TrialError, match="no Checker binding"):
        T.column_of("X", {"class": "RELEASED"}, None, "DRAWING-CONFIRMED")


def test_adverse_total_over_held_refused(k):
    b, _ = k
    bad = copy.deepcopy(b["trades"])
    t = next(t for t in bad if (t["trade"], t["unit"]) == ("B10", "m3"))
    t["subtotal"]["total"] = "14.75"
    with pytest.raises(T.TrialError, match="total printed over a HELD line"):
        T.guard_totals(bad)


def test_latest_task_wins_and_host_chain():
    H, M = "L-" + "a" * 20, "L-" + "b" * 20
    after = {H: _l(H, "MAS.BLOCK", "m2", "HELD"), M: _l(M, "MAS.UNITS.BLACK", "pcs", "HELD")}
    recs = {H: [T._rec(449, "old", "old reason D-12"), T._rec(615, "new", "height not printed D-43")]}
    ops = {M: {"op_id": "K|ADD|M", "kind": "ADD", "line_id": M, "note": "host " + H, "package": "T-498", "row": "S"}}
    c = T.resolve_causes(after, ops, recs)
    assert c[H]["cause"] == "height not printed D-43" and c[H]["also_stated_by"] == ["old"]
    assert c[M]["cause"] == "host MAS.BLOCK line HELD: height not printed D-43"
    after[H]["class"] = "RELEASED"
    after[H]["measured_net"] = 1.0
    assert T.resolve_causes(after, ops, recs)[M] is None          # a RELEASED host gives no cause


def test_stale_t297_bound_not_used():
    after = {"R": _l("R", "STR.REBAR", "kg", "HELD", lo=15.17, hi=15.881),
             "S": _l("S", "STR.REBAR", "kg", "HELD", lo=20.0, hi=25.0)}
    rec = lambda lid, lo, hi: {"line_id": lid, "evidence_state": "BOUNDED_EXPOSURE", "bounded_range": {
        "low": lo, "high": hi, "basis": "readings"}, "inputs": {"reasons": ["count rule Q-71 open"]}, "rfi": None,
        "formula": "f", "rule_id": "UP-REBAR-COUNT-001"}
    src = {"T297": {"lines": [rec("R", 15.17, 15.881), rec("S", 15.17, 15.881)]}, "T311": {"lines": []}}
    out, stale = T.extract_records(src, after)
    assert out["R"][0]["cause"].startswith("count rule Q-71 open") and stale == ["S"]


# ---- the training villa ---------------------------------------------------------------------------------------------

@pytest.fixture(scope="module")
def real():
    return T.build()


def test_training_build_equals_committed(real):
    assert T.dumps(real) == T.OUT_JSON.read_text(encoding="utf-8")
    assert T.render_md(real) == T.OUT_MD.read_text(encoding="utf-8")
    assert T.render_csv(real) == T.OUT_CSV.read_text(encoding="utf-8")


def test_training_closes_by_hand(real):
    pl = real["per_line"]
    held = [p for p in pl if p["class"] == "HELD"]
    assert len(pl) == real["lines"]["after_v17"] == 5151 and len({p["line_id"] for p in pl}) == len(pl)
    assert real["held"]["with_cause"] + real["held"]["finding_F_T636_1"] == len(held)
    assert all((p["cause"] is None) == (p["finding"] == "F-T636-1") for p in held)
    assert all(p["measured_net"] is None for p in held)
    listed = {i for v in real["findings"]["F-T636-1"]["by_item_code"].values() for i in v["line_ids"]}
    assert listed == {p["line_id"] for p in held if p["cause"] is None}
    for unit, g in real["unit_grand"].items():
        rel = sum((Decimal(str(p["measured_net"])) for p in pl if p["unit"] == unit and p["class"] == "RELEASED"),
                  Decimal(0))
        assert Decimal(g["released"]) == rel
        assert Decimal(g["wired"]) + Decimal(g["overlay"]) + Decimal(g["unverified"]) == rel
        assert g["total"] is None                                    # every unit carries HELD lines
    assert all(c["re_adds_exactly"] for c in real["aggregation_proof"])
    assert real["findings"]["F-T636-2"]["lines"] == 0                # master 1.56.0: no NO_FAMILY line
    for p in pl:
        if p["column"] == T.WIRED:
            assert p["origin"] == "candidate V3.0.58" and p["evidence"] in T.CHECKER_STATUSES
    assert real["candidate_files_touched"] == 0 and real["released_quantities_changed"] == 0


def test_write_outputs():
    if os.environ.get("URBAN_T636_WRITE") != "1":
        pytest.skip("writer: set URBAN_T636_WRITE=1")
    T.write_outputs()
