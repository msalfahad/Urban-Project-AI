"""T-419 integration on a synthetic villa-Q candidate (hand fixture, not the development villa): the GF lift tie beam
added HELD BLANK per component (concrete, two form lines, bars) with its length beside, the house below-ground masonry
runs added HELD BLANK (an AT_LEAST plane beside; a CONFLICT run with no bound), the pit-wall held reasons restated to
name both facts, merged bindings re-checked; every other line byte-identical; adverse inputs refused.

Villa Q by hand: lift ring 2.30 x 2.10 outside, shaft 1.80 x 1.60, columns at the corners: clear runs S 1.80, N 1.80,
W 0.90, E 0.80 -> tie 5.300 m (beside, never the quantity). Neighbour-side run: axis 15.000 m less columns 1.000 m ->
net 14.000 m; soffit +-0.00, highest foundation top -0.70, blinding 0.10 max -> h >= 0.60 m; AT_LEAST 14.000 x 0.60 =
8.400 m2 net (gross 15.000 x 0.60 = 9.000). Band partition: house 30.00 + fence 26.50 + pool 3.50 = band 60.00 m."""
import copy

import pytest

from engine.source import arch_v30 as A30
from engine.source import arch_v304 as A304
from engine.source import arch_v3030 as A3030
from engine.source import arch_v3046 as M
from engine.source import boq_line as BL

PID, REV = "villa-q-t419", "0" * 64
PIT_DEPTH, BUILD_UP = "pit depth below the landing F.F.L. (supplier)", "GF build-up F.F.L. -> slab-on-grade top"


def mk(eid, code, unit, state, net=None, rfi=None, notes=""):
    inputs = None
    if code == "STR.FORMWORK":       # the formwork book record every formwork line carries (V3.0.30 guard)
        inputs = {A3030.REC_KEY: {"policy": A3030.PIECES[A3030.FW_PIECE]["policy"], "status": "HELD",
                                  "face_ids": [f"Q.{eid}"], "concrete_line": None}}
    return BL.make_line(inputs=inputs, project_id=PID, revision_set_sha256=REV, item_code=code, unit=unit, evidence_state=state,
                        measured_net=net, gross=net, element_id=eid, floor="GF", formula="synthetic", rule_id="R-X",
                        rule_version="1", rfi=rfi, notes=notes, item_en=code, item_ar=code,
                        trade="FORMWORK" if code == "STR.FORMWORK" else None)


def candidate():
    q = {"question": "pit depth as per lift manufacturer"}
    return [mk("PIT_WALLS", "STR.CONC.LIFT", "m3", "BLOCKED_RFI", rfi=q),
            mk("PIT_FORM", "STR.FORMWORK", "m2", "BLOCKED_RFI", rfi={"question": "no pit-wall line"}),
            mk("REBAR_ANY", "STR.REBAR", "kg", "PROVISIONAL", 120.0),
            mk("GF_LIFT_BLOCK", "MAS.BLOCK", "m2", "BLOCKED_RFI", rfi={"question": "lift tie beam size"}),
            mk("RING_1", "STR.CONC.BEAM", "m3", "PROVISIONAL", 0.207),      # 2.30 x 0.20 x 0.45
            mk("RING_2", "STR.CONC.BEAM", "m3", "PROVISIONAL", 0.189),      # 2.10 x 0.20 x 0.45
            mk("GB_S", "STR.CONC.GROUND_BEAM", "m3", "SOURCE_DERIVED", 3.99),   # 14.00 x 0.30 x 0.95
            mk("COL_1", "STR.CONC.COLUMN", "m3", "PROVISIONAL", 0.5)]


SRC = [{"task": "T-A", "file": "a.json", "sha256": "a" * 64, "merge_commit": "abcdef12", "checker_run": "run a"},
       {"task": "T-B", "file": "b.json", "sha256": "b" * 64, "merge_commit": "abcdef13", "checker_run": "run b"}]
LEN = {"kind": "LENGTH", "length_m": 5.3, "sheets": ["roof plan", "column plan"]}


def doc(c, **over):
    by = {ln["location"]["element_id"]: ln["line_id"] for ln in c}
    tie = {"piece": "LIFT_TIE_BEAM", "floor": "GF", "owner_trade": "STRUCTURE", "source_tasks": ["T-A"],
           "basis": "runs between the GF column faces"}
    d = {"schema": M.INPUTS_SCHEMA, "project_id": PID, "sources": SRC,
         "add": [dict(tie, key="TIE", item_code="STR.CONC.LIFT", unit="m3", element_id="TIE:GF",
                      template_line=by["PIT_WALLS"], beside=dict(LEN), physical_element="tie beam",
                      missing_facts=["section b x d"], tied_to=None),
                 dict(tie, key="SIDES", item_code="STR.FORMWORK", unit="m2", element_id="TIE:GF:SIDES",
                      template_line=by["PIT_FORM"], beside=dict(LEN), physical_element="tie sides",
                      missing_facts=["depth d"], tied_to="TIE"),
                 dict(tie, key="SOFFIT", item_code="STR.FORMWORK", unit="m2", element_id="TIE:GF:SOFFIT",
                      template_line=by["PIT_FORM"], beside=dict(LEN), physical_element="tie soffit",
                      missing_facts=["width b"], tied_to="TIE"),
                 dict(tie, key="BARS", item_code="STR.REBAR", unit="kg", element_id="TIE:GF:REBAR",
                      template_line=by["REBAR_ANY"], beside=dict(LEN), physical_element="tie bars",
                      missing_facts=["bar detail"], tied_to="TIE"),
                 {"key": "S", "piece": "HOUSE_BELOW_NG_MASONRY", "item_code": "MAS.BLOCK", "unit": "m2",
                  "element_id": "BELOW_NG:S", "floor": "FOUNDATION", "template_line": by["GF_LIFT_BLOCK"],
                  "owner_trade": "BLOCKWORK BELOW N.G.", "source_tasks": ["T-B"], "tied_to": None,
                  "physical_element": "block under the neighbour-side beam", "basis": "note prints block",
                  "beside": {"kind": "AT_LEAST_AREA", "run_m": 14.0, "height_at_least_m": 0.6, "area_m2": 8.4,
                             "gross_area_m2": 9.0},
                  "missing_facts": ["formation level", "block thickness"]},
                 {"key": "S2", "piece": "HOUSE_BELOW_NG_MASONRY", "item_code": "MAS.BLOCK", "unit": "m2",
                  "element_id": "BELOW_NG:S2", "floor": "FOUNDATION", "template_line": by["GF_LIFT_BLOCK"],
                  "owner_trade": "BLOCKWORK BELOW N.G.", "source_tasks": ["T-B"], "tied_to": None,
                  "physical_element": "block under the annex beam", "basis": "note prints block",
                  "beside": {"kind": "NO_BOUND", "why": "beam soffit CONFLICT"},
                  "missing_facts": ["annex beam depth", "formation level"]}],
         "restate": [{"line_id": by["PIT_WALLS"], "expect": {"item_code": "STR.CONC.LIFT",
                                                             "evidence_state": "BLOCKED_RFI"},
                      "facts": [PIT_DEPTH, BUILD_UP], "why": "both facts", "source_tasks": ["T-A"]},
                     {"line_id": by["PIT_FORM"], "expect": {"item_code": "STR.FORMWORK",
                                                            "evidence_state": "BLOCKED_RFI"},
                      "facts": [PIT_DEPTH, BUILD_UP], "why": "tied to the pit wall", "source_tasks": ["T-A"],
                      "tie_to": by["PIT_WALLS"]}],
         "bind": [{"what": "rings", "line_ids": [by["RING_1"], by["RING_2"]], "source_tasks": ["T-A"],
                   "expect": {"item_code": "STR.CONC.BEAM", "total": 0.396}},
                  {"what": "block paired", "line_ids": [by["GF_LIFT_BLOCK"]], "source_tasks": ["T-A"],
                   "expect": {"item_code": "MAS.BLOCK", "evidence_state": "BLOCKED_RFI", "text": "tie beam"}}],
         "partition": {"house_m": 30.0, "fence_m": 26.5, "pool_m": 3.5, "band_m": 60.0, "source_tasks": ["T-B"]},
         "register_only": [{"key": "E", "net_run_m": 6.0, "why": "existence unknown"}]}
    d.update(over)
    return d


def run(c, d):
    ch, log = M.changes_for(M.load_inputs(d, PID), c)
    return ch, log, M.integrate(c, ch)


def test_adds_restates_binds():
    c = candidate()
    ch, log, (out, ident) = run(c, doc(c))
    assert ident["added"] == 6 and ident["replaced"] == 2 and len(out) == len(c) + 6
    assert ident["tie_masonry"] == {"added_held": 6, "tie_lines": 4, "masonry_lines": 2, "restated": 2,
                                    "components_tied": 3}
    assert ident["outside_rows_identical_to_base"] == len(c) - 2
    new = {ln["location"]["element_id"]: ln for ln in out}
    for e in ("TIE:GF", "TIE:GF:SIDES", "TIE:GF:SOFFIT", "TIE:GF:REBAR", "BELOW_NG:S", "BELOW_NG:S2"):
        ln = new[e]
        assert ln["evidence_state"] == "BLOCKED_RFI" and ln["measured_net"] is None and ln["gross"] is None
        assert ln["bounded_range"] is None
    assert "5.3 m DRAWING-CONFIRMED" in new["TIE:GF"]["rfi"]["bound_beside"]
    assert "AT_LEAST 8.4 m2 net" in new["BELOW_NG:S"]["rfi"]["bound_beside"]
    assert new["BELOW_NG:S2"]["rfi"]["bound_beside"].startswith("no bound")
    tie_id = new["TIE:GF"]["line_id"]
    for e in ("TIE:GF:SIDES", "TIE:GF:SOFFIT", "TIE:GF:REBAR"):
        assert new[e]["calculation"]["inputs"][M.REC_KEY]["parent_line"] == tie_id
    pw = new["PIT_WALLS"]
    assert PIT_DEPTH in pw["rfi"]["question"] and BUILD_UP in pw["rfi"]["question"]
    old = {ln["location"]["element_id"]: ln for ln in c}["PIT_WALLS"]
    for k in M.QTY_KEYS:
        assert pw.get(k) == old.get(k)
    assert [b["result"] for b in log["binds"]] == ["BOUND", "BOUND"] and log["binds"][0]["total"] == 0.396
    assert log["register_only"][0]["key"] == "E"


def test_totals_move_only_blocked_counts():
    c = candidate()
    _ch, _log, (out, _i) = run(c, doc(c))
    moved = M.check_totals(A304.code_totals(c), A304.code_totals(out))
    assert set(moved) == {"STR.CONC.LIFT|m3", "STR.FORMWORK|m2", "STR.REBAR|kg", "MAS.BLOCK|m2"}
    assert moved["STR.REBAR|kg"]["v3_0_46"]["released"] == 120.0          # the existing bars line is untouched
    assert moved["MAS.BLOCK|m2"]["v3_0_46"]["blocked_lines"] == 3


def test_order_invariant_and_ids_stable():
    c = candidate()
    d = doc(c)
    d2 = copy.deepcopy(d)
    d2["add"] = list(reversed(d2["add"]))
    a = sorted(ln["line_id"] for ln in run(c, d)[2][0])
    b = sorted(ln["line_id"] for ln in run(c, d2)[2][0])
    assert a == b


# ------------------------------------------------------------------------------------------------ adverse
def _refused(c, d, msg):
    with pytest.raises(M.InputsError, match=msg):
        M.changes_for(M.load_inputs(d, PID), c)


@pytest.mark.parametrize("field", ["value", "measured_net", "low"])
def test_held_valued_refused(field):
    c = candidate()
    d = doc(c)
    d["add"][0][field] = 0
    with pytest.raises(M.InputsError, match="carries no"):
        M.load_inputs(d, PID)


def test_beside_value_zero_refused():
    c = candidate()
    d = doc(c)
    d["add"][0]["beside"] = dict(LEN, length_m=0)
    with pytest.raises(M.InputsError, match="never 0"):
        M.load_inputs(d, PID)


@pytest.mark.parametrize("code", ["STR.CONC.COLUMN", "STR.CONC.BEAM", "MAS.BLOCK"])
def test_tie_inside_column_beam_or_block_refused(code):
    c = candidate()
    d = doc(c)
    d["add"][0]["item_code"] = code
    with pytest.raises(M.InputsError, match="refused"):
        M.load_inputs(d, PID)


@pytest.mark.parametrize("code", ["EXT.FENCE.MASONRY_BELOW_NG", "STR.CONC.GROUND_BEAM"])
def test_house_masonry_in_fence_or_beam_refused(code):
    c = candidate()
    d = doc(c)
    d["add"][4]["item_code"] = code
    with pytest.raises(M.InputsError, match="refused"):
        M.load_inputs(d, PID)


def test_partition_overlap_refused():
    c = candidate()
    d = doc(c)
    d["partition"]["fence_m"] = 26.6              # house and fence masonry overlap by 0.10 m on the band
    with pytest.raises(M.InputsError, match="overlap or a gap"):
        M.load_inputs(d, PID)


def test_masonry_without_partition_refused():
    c = candidate()
    with pytest.raises(M.InputsError, match="partition"):
        M.load_inputs(doc(c, partition=None), PID)


def test_at_least_not_run_times_height_refused():
    c = candidate()
    d = doc(c)
    d["add"][4]["beside"]["area_m2"] = 9.0         # the gross figure presented as the net plane
    with pytest.raises(M.InputsError, match="is not run"):
        M.load_inputs(d, PID)


def test_conflict_run_given_a_bound_refused():
    c = candidate()
    d = doc(c)
    d["add"][5]["beside"]["area_m2"] = 5.6
    with pytest.raises(M.InputsError, match="no bound"):
        M.load_inputs(d, PID)


def test_mm_as_m_refused():
    c = candidate()
    d = doc(c)
    d["add"][0]["beside"] = dict(LEN, length_m=5300)
    with pytest.raises(M.InputsError, match="mm refused"):
        M.load_inputs(d, PID)


def test_unknown_existence_run_as_line_refused():
    c = candidate()
    d = doc(c)
    d["register_only"] = [{"key": "S", "why": "x"}]
    with pytest.raises(M.InputsError, match="never a line"):
        M.load_inputs(d, PID)


def test_restatement_naming_one_fact_refused():
    c = candidate()
    d = doc(c)
    d["restate"][0]["facts"] = [PIT_DEPTH]
    with pytest.raises(M.InputsError, match="every fact"):
        M.load_inputs(d, PID)


def test_stale_template_refused():
    c = candidate()
    d = doc(c)
    d["add"][0]["template_line"] = d["add"][1]["template_line"]       # a formwork line for a concrete component
    _refused(c, d, "stale binding")


def test_element_already_carried_refused():
    c = candidate()
    d = doc(c)
    d["add"][0]["element_id"] = "COL_1"
    _refused(c, d, "already has a line")


def test_bind_drift_refused():
    c = candidate()
    d = doc(c)
    d["bind"][0]["expect"]["total"] = 0.45
    _refused(c, d, "drift")


def test_pairing_lost_refused():
    c = candidate()
    d = doc(c)
    d["bind"][1]["expect"]["text"] = "ring beam size"
    _refused(c, d, "pairing lost")


def test_component_without_parent_refused():
    c = candidate()
    d = doc(c)
    d["add"][1]["tied_to"] = "NOPE"
    with pytest.raises(M.InputsError, match="parent"):
        M.load_inputs(d, PID)


def test_applied_once():
    c = candidate()
    _ch, _log, (out, _i) = run(c, doc(c))
    with pytest.raises(M.InputsError, match="applied once"):
        M.changes_for(M.load_inputs(doc(c), PID), out)


def test_check_refuses_held_line_valued_zero():
    c = candidate()
    _ch, _log, (out, _i) = run(c, doc(c))
    bad = copy.deepcopy(out)
    ln = next(x for x in bad if x["location"]["element_id"] == "TIE:GF")
    ln["measured_net"] = 0.0
    with pytest.raises(ValueError, match="never 0"):
        M.check_tie_masonry(bad, c)


def test_check_refuses_restated_quantity_move():
    c = candidate()
    _ch, _log, (out, _i) = run(c, doc(c))
    bad = copy.deepcopy(out)
    ln = next(x for x in bad if x["location"]["element_id"] == "PIT_WALLS")
    ln["evidence_state"] = "BOUNDED_EXPOSURE"
    with pytest.raises(ValueError, match="moved evidence_state"):
        M.check_tie_masonry(bad, c)


def test_line_sha_outside_identical():
    c = candidate()
    _ch, _log, (out, _i) = run(c, doc(c))
    b = {ln["line_id"]: A30.line_sha(ln) for ln in c}
    named = {ln["line_id"] for ln in out if (ln["calculation"]["inputs"] or {}).get(M.REC_KEY)}
    assert all(A30.line_sha(ln) == b[ln["line_id"]] for ln in out if ln["line_id"] in b and ln["line_id"] not in named)


def test_restated_form_face_tied_to_the_pit_wall_line():
    c = candidate()
    _ch, _log, (out, _i) = run(c, doc(c))
    by = {ln["location"]["element_id"]: ln for ln in out}
    q = by["PIT_FORM"]["rfi"]["question"]
    assert by["PIT_WALLS"]["line_id"] in q and "superseded" in q and "no pit-wall line" in q   # the old text kept as 'was'


def test_tie_to_non_concrete_refused():
    c = candidate()
    d = doc(c)
    d["restate"][1]["tie_to"] = {ln["location"]["element_id"]: ln["line_id"] for ln in c}["GF_LIFT_BLOCK"]
    _refused(c, d, "not a concrete line")
