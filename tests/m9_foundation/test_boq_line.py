"""M9 S1 canonical BOQ line: validation, the two state axes, monotone adapters (never raise a state, refuse an unknown
one), no price field, an agent cannot approve, like-unit totals with bounded ranges kept apart, measure pairs priced on
one basis, and route G items adapted with their numbers unchanged."""

from __future__ import annotations

import pytest

from engine.source import boq_line as BL

BASE = dict(project_id="P", revision_set_sha256="0" * 64, unit="m2", element_id="E1", formula="L x W",
            rule_id="UP-CER-001", rule_version="1.0.0")


def mk(**kw):
    a = dict(BASE, item_code="FIN.FLOOR.PORCELAIN", evidence_state="SOURCE_DERIVED", measured_net=6.0)
    a.update(kw)
    return BL.make_line(**a)


def test_a_valid_line_is_bilingual_and_traceable():
    ln = mk(floor="GF", room_id="R1")
    assert ln["item_ar"] and ln["item_en"] and ln["trade"] == "FLOOR_FINISH" and ln["line_id"].startswith("L-")
    assert mk(floor="GF", room_id="R1")["line_id"] == ln["line_id"]                # deterministic
    assert ln["approval_state"] == "MACHINE_ONLY"


@pytest.mark.parametrize("kw", [dict(evidence_state="SOURCE_DERIVED", measured_net=None),
                                dict(evidence_state="BLOCKED_RFI", measured_net=1.0),
                                dict(evidence_state="BLOCKED_RFI", measured_net=None),           # no question
                                dict(evidence_state="BOUNDED_EXPOSURE", measured_net=None,
                                     bounded_range={"low": 2.0, "high": 1.0}),
                                dict(evidence_state="EXCLUDED_WITH_REASON", measured_net=None),   # no reason
                                dict(unit="ft2"), dict(formula=""), dict(evidence_state="GUESSED"),
                                dict(measured_net=-1.0)])
def test_invalid_lines_are_refused(kw):
    with pytest.raises(BL.LineError):
        mk(**kw)


@pytest.mark.parametrize("key", ["price", "unit_rate", "amount_kwd", "cost", "rate"])
def test_no_price_rate_or_amount_field(key):
    with pytest.raises(BL.LineError):
        mk(inputs={key: 1.0})


def test_approval_needs_a_human_reviewer_and_a_quantity():
    rv = {"reviewer": "QS-1", "role": "QS", "decision_sha256": "a" * 64}
    assert mk(approval_state="APPROVED", review=rv)["approval_state"] == "APPROVED"
    for bad in ({"reviewer": "x", "role": "AGENT", "decision_sha256": "a"}, {"reviewer": "x", "role": "LLM",
                                                                               "decision_sha256": "a"}, {}):
        with pytest.raises(BL.LineError):
            mk(approval_state="APPROVED", review=bad)
    with pytest.raises(BL.LineError):
        mk(approval_state="RELEASED_FOR_PRICING", review=rv, evidence_state="BOUNDED_EXPOSURE", measured_net=None,
           bounded_range={"low": 1, "high": 2})


def test_a_measure_pair_always_prices_one_basis():
    with pytest.raises(BL.LineError):
        mk(measure_pair={"pair_id": "S1", "price_one_basis": False})
    assert mk(measure_pair={"pair_id": "S1", "price_one_basis": True})


def test_adapters_never_raise_a_state_and_refuse_unknown_states():
    for voc, table in BL.LEGACY.items():
        for state, ev in table.items():
            for exp in (False, True):
                for sup in (None, "SOURCE_COMPLETE_UNREVIEWED", "CONVENTION_ONLY"):
                    got, ap = BL.adapt(voc, state, has_exposure=exp, support=sup)
                    if got is not None:
                        assert BL.RANK[got] <= BL.RANK[BL.CEILING[voc][state]], (voc, state, got)
                    assert ap in BL.APPROVAL and ap != "RELEASED_FOR_PRICING"
    with pytest.raises(BL.LineError):
        BL.adapt("provisional_estimate", "SOMETHING_NEW")
    with pytest.raises(BL.LineError):
        BL.adapt("unknown_vocab", "VERIFIED")
    assert BL.adapt("provisional_estimate", "PROVISIONAL", support="SOURCE_COMPLETE_UNREVIEWED")[0] == "SOURCE_DERIVED"
    assert BL.adapt("provisional_estimate", "PROVISIONAL", support="CONVENTION_ONLY")[0] == "PROVISIONAL"
    assert BL.adapt("boq_canonical", "RELEASED")[1] == "MACHINE_ONLY"
    assert BL.adapt("boq_canonical", "RELEASED", decision_valid=True)[1] == "RELEASED_FOR_PRICING"


def test_totals_are_like_unit_and_bounded_ranges_stay_apart():
    a = mk(floor="GF", element_id="A", measured_net=6.0)
    b = mk(floor="GF", element_id="B", measured_net=4.0)
    c = mk(floor="GF", element_id="C", unit="lm", item_code="FIN.SKIRTING", measured_net=9.0)
    d = mk(floor="1F", element_id="D", evidence_state="BOUNDED_EXPOSURE", measured_net=None,
           bounded_range={"low": 1.0, "high": 3.0}, rfi={"question": "q"})
    e = mk(floor="1F", element_id="E", evidence_state="BLOCKED_RFI", measured_net=None, rfi={"question": "q"})
    T = BL.totals([a, b, c, d, e])
    assert T[("GF",)]["m2"]["net"] == 10.0 and T[("GF",)]["lm"]["net"] == 9.0
    assert T[("1F",)]["m2"]["net"] == 0.0 and T[("1F",)]["m2"]["bounded_high"] == 3.0
    assert T[("1F",)]["m2"]["blocked_lines"] == 1


def test_never_additive_lines_are_summed_once():
    a = mk(element_id="A", measured_net=6.0)
    b = mk(element_id="B", measured_net=6.0, never_additive_with=[a["line_id"]])
    a2 = dict(a, never_additive_with=[b["line_id"]])
    assert BL.totals([a2, b])[(None,)]["m2"]["net"] == 6.0


ITEM = {"item_id": "C:FTG:1", "component_id": "FTG1", "trade": "CONCRETE", "family": "FOOTINGS", "storey": "FOUNDATION",
        "category": "PROVISIONAL", "unit": "m3", "low": 2.0, "base": 2.2, "high": 2.45, "dia_mm": None,
        "formula": "L x W x D", "dimensions": {"schedule_m": [2, 2, 0.55]}, "assumptions": ["X"],
        "support": "SOURCE_COMPLETE_UNREVIEWED", "limitations": "", "blocker": None}


def test_route_g_items_keep_their_numbers():
    k = dict(project_id="P", revision_set_sha256="0" * 64, conventions_set="V6", conventions_digest="d" * 64)
    ln = BL.from_route_g(ITEM, **k)
    assert ln["evidence_state"] == "SOURCE_DERIVED" and ln["measured_net"] == 2.2 and ln["item_code"] == "STR.CONC.FOOTING"
    assert ln["bounded_range"] == {"low": 2.0, "high": 2.45, "basis": "the item's own convention range"}
    neck = BL.from_route_g(dict(ITEM, family="COLUMNS", support="CONVENTION_ONLY"), **k)
    assert neck["item_code"] == "STR.CONC.NECK" and neck["evidence_state"] == "PROVISIONAL"
    un = BL.from_route_g(dict(ITEM, category="UNRESOLVED", exposure_low=1.0, exposure_high=3.0, blocker="depth?",
                              support="NO_GEOMETRY"), **k)
    assert un["evidence_state"] == "BOUNDED_EXPOSURE" and un["measured_net"] is None and un["rfi"]["question"] == "depth?"
    bl = BL.from_route_g(dict(ITEM, category="UNRESOLVED", blocker="depth?", support="NO_GEOMETRY"), **k)
    assert bl["evidence_state"] == "BLOCKED_RFI"
    st = BL.from_route_g(dict(ITEM, trade="REINFORCEMENT", unit="kg", dia_mm=12), **k)
    assert st["item_code"] == "STR.REBAR" and st["material_state"] == "SOURCE"
    rows = list(BL.csv_rows([ln, un]))
    assert set(rows[0]) == set(BL.CSV_COLUMNS)
    assert BL.dumps([ln]) == BL.dumps([ln])
