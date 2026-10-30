"""T-371 bar-shape source census: villa K371 by hand (not the development villa) + adverse cases + a regression on the
committed development-villa input. No kg, no count and no length is ever produced."""
import copy
import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "research/agents_t371"


def _load(name, file):
    spec = importlib.util.spec_from_file_location(name, HERE / file)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


c = _load("t371", "t371_shape_census.py")

P = lambda ref="S-4 sec 2", **kw: {"state": "PRINTED", "ref": ref, **kw}
T = lambda applies, ref="S-6 typical", **kw: {"state": "PRINTED_TYPICAL", "ref": ref, "applies_to": applies, **kw}
U = lambda ref="S-6 typical", **kw: {"state": "DRAWN_UNDIMENSIONED", "ref": ref, **kw}
N = lambda **kw: {"state": "NOT_PRINTED", **kw}
NA = {"state": "NOT_APPLICABLE"}
REG = {"rfi_register": ["RFI-K01", "RFI-K02"], "answered_rules": ["RULE-K"], "other_census": ["OTHER"]}


def straight(applies):
    return {"body": T(applies, value="straight"), "end_1": T(applies), "end_2": T(applies), "leg_length": NA,
            "hook": NA, "bend_diameter": NA, "crank": NA}


def villa():
    """Villa K371 (hand-built): a pad footing mesh drawn straight on its own typical; a beam top bar drawn as an L with an
    undimensioned leg (asked in RFI-K01); a column link drawn closed with a hook whose length is asked nowhere (gap);
    a beam whose schedule prints count only (RFI-K02); a lap owned by another census."""
    pops = [
        {"pop_id": "K-FTG-MESH", "element_class": "PAD_FOOTING", "description": "pad mesh", "attrs": straight("PAD_FOOTING")},
        {"pop_id": "K-BM-TOP-L", "element_class": "BEAM", "description": "top bar with end leg",
         "attrs": {"body": P(value="L"), "end_1": U("S-5 row 3", rfi="RFI-K01"), "end_2": P(value="straight"),
                   "leg_length": U("S-5 row 3", rfi="RFI-K01"), "hook": NA,
                   "bend_diameter": N(rfi="RFI-K01"), "crank": NA}},
        {"pop_id": "K-COL-LINK", "element_class": "COLUMN", "description": "closed link",
         "attrs": {"body": T("COLUMN", value="closed"), "end_1": U(gap="G-K-1"), "end_2": U(gap="G-K-1"),
                   "leg_length": T("COLUMN"), "hook": U(gap="G-K-1"), "bend_diameter": N(gap="G-K-0"), "crank": NA}},
        {"pop_id": "K-BM-BOT", "element_class": "BEAM", "description": "schedule only",
         "attrs": {a: N(rfi="RFI-K02") for a in c.ATTRS}},
        {"pop_id": "K-LAP", "element_class": "COLUMN", "description": "lap", "owned_by": "LAP-CENSUS",
         "attrs": {"body": P(), "end_1": NA, "end_2": NA, "leg_length": N(), "hook": NA, "bend_diameter": NA,
                   "crank": NA}},
    ]
    data = {"register": copy.deepcopy(REG), "populations": pops}
    lines = {"L1": "K-FTG-MESH", "L2": "K-FTG-MESH", "L3": "K-BM-TOP-L", "L4": "K-COL-LINK", "L5": "K-BM-BOT",
             "L6": "K-LAP", "L7": "OTHER"}
    return data, {"candidate_line_ids": sorted(lines), "lines": lines}


# ---- normal case (hand-checked statuses) ---------------------------------------------------------------------------
def test_villa_k371_statuses_by_hand():
    data, b = villa()
    out = c.run(data, b)
    st = {r["pop_id"]: (r["status"], r["blocking_ids"], r["candidate_lines"]) for r in out["rows"]}
    assert st["K-FTG-MESH"] == ("SCHEDULABLE_NOW", "", 2)
    assert st["K-BM-TOP-L"] == ("SCHEDULABLE_AFTER", "RFI-K01", 1)
    assert st["K-COL-LINK"] == ("GAP", "G-K-0;G-K-1", 1)
    assert st["K-BM-BOT"] == ("SCHEDULABLE_AFTER", "RFI-K02", 1)
    assert st["K-LAP"] == ("OWNED_ELSEWHERE", "LAP-CENSUS", 1)
    assert out["lines_bound"] == 7 and out["lines_to_other_census"] == {"OTHER": 1}
    assert out["status_counts"] == {"SCHEDULABLE_NOW": 1, "SCHEDULABLE_AFTER": 2, "GAP": 1, "OWNED_ELSEWHERE": 1}


def test_order_of_populations_does_not_change_statuses():
    data, b = villa()
    a = {r["pop_id"]: r["status"] for r in c.run(data, b)["rows"]}
    data["populations"].reverse()
    assert {r["pop_id"]: r["status"] for r in c.run(data, b)["rows"]} == a


# ---- adverse --------------------------------------------------------------------------------------------------------
def test_adverse_hook_borrowed_from_another_elements_typical_refused():
    data, b = villa()
    # the beam's hook taken from the COLUMN link typical: refused
    data["populations"][1]["attrs"]["hook"] = T("COLUMN", value="135 deg hook")
    with pytest.raises(ValueError, match="borrowed"):
        c.run(data, b)


def test_adverse_undimensioned_leg_given_a_length_refused():
    data, b = villa()
    data["populations"][1]["attrs"]["leg_length"]["value_m"] = 0.30
    with pytest.raises(ValueError, match="never gets a length"):
        c.run(data, b)


def test_adverse_minimum_used_as_an_exact_length_refused():
    data, b = villa()
    data["populations"][1]["attrs"]["leg_length"] = {"state": "PRINTED_MINIMUM", "ref": "S-6", "min_m": 0.30,
                                                     "value_m": 0.30, "rfi": "RFI-K01"}
    with pytest.raises(ValueError, match="never gets a length"):
        c.run(data, b)


@pytest.mark.parametrize("label", ["ø8/15cm", "6ø8/m", "2ø12/30cm", "ø8/20", "5%%c10/m"])
def test_adverse_spacing_or_rate_read_as_a_count_refused(label):
    with pytest.raises(ValueError, match="never read as a bar count"):
        c.count_from_label(label)
    data, b = villa()
    data["populations"][0]["count_label"] = label
    with pytest.raises(ValueError):
        c.run(data, b)


def test_explicit_count_label_is_a_count():
    assert c.count_from_label("4ø16") == 4 and c.parse_notation("ø8/20")["unit_printed"] is False


def test_adverse_kg_field_refused():
    data, b = villa()
    data["populations"][0]["mass_kg"] = 12.0
    with pytest.raises(ValueError, match="no kg"):
        c.run(data, b)


def test_adverse_unanswered_rule_and_unknown_rfi_refused():
    data, b = villa()
    data["populations"][0]["attrs"]["crank"] = {"state": "RULE", "rule": "RULE-PENDING"}
    with pytest.raises(ValueError, match="not an answered"):
        c.run(data, b)
    data, b = villa()
    data["populations"][1]["attrs"]["end_1"]["rfi"] = "RFI-K99"
    with pytest.raises(ValueError, match="not in the RFI register"):
        c.run(data, b)


def test_adverse_blocking_without_rfi_or_gap_and_conflict_without_refs_refused():
    data, b = villa()
    data["populations"][0]["attrs"]["hook"] = N()
    with pytest.raises(ValueError, match="names no RFI"):
        c.run(data, b)
    data, b = villa()
    data["populations"][0]["attrs"]["hook"] = {"state": "CONFLICT", "refs": ["S-6"], "gap": "G-K-2"}
    with pytest.raises(ValueError, match="both refs"):
        c.run(data, b)


def test_adverse_printed_without_ref_refused():
    data, b = villa()
    data["populations"][1]["attrs"]["end_2"] = {"state": "PRINTED"}
    with pytest.raises(ValueError, match="needs a sheet"):
        c.run(data, b)


def test_adverse_binding_unbound_twice_unknown_refused():
    data, b = villa()
    b["candidate_line_ids"].append("L8")
    with pytest.raises(ValueError, match="incomplete"):
        c.run(data, b)
    data, b = villa()
    b["lines"]["L2"] = "K-NOPE"
    with pytest.raises(ValueError, match="unknown population"):
        c.run(data, b)
    data, b = villa()
    data["populations"].append(copy.deepcopy(data["populations"][0]))
    with pytest.raises(ValueError, match="duplicate"):
        c.run(data, b)


def test_leg_bound_is_a_proposal_never_a_value():
    data, _ = villa()
    p = data["populations"][1]
    p["leg_bound_basis"] = "leg <= D - covers"
    out = c.leg_bound_proposal(p)
    assert out["value"] is None and out["status"] == "PROPOSAL_ONLY"
    with pytest.raises(ValueError, match="drawn, undimensioned"):
        c.leg_bound_proposal(data["populations"][0] | {"attrs": straight("PAD_FOOTING") | {"leg_length": P()}})


# ---- development villa regression (committed input) -----------------------------------------------------------------
def test_development_villa_committed_input():
    data = json.loads((HERE / "ALSENAN_BAR_SHAPE_INPUT.json").read_text("utf-8"))
    binding = json.loads((HERE / "LINE_BINDING_T371.json").read_text("utf-8"))
    out = c.run(data, binding)
    assert out["populations"] == 38
    assert out["status_counts"] == {"SCHEDULABLE_NOW": 7, "SCHEDULABLE_AFTER": 10, "GAP": 19, "OWNED_ELSEWHERE": 2}
    assert out["lines_bound"] == 2505 and out["lines_to_other_census"] == {"T-359": 88}
    st = {r["pop_id"]: r for r in out["rows"]}
    assert st["SLAB-TOP"]["status"] == "GAP" and "G-T371-7" in st["SLAB-TOP"]["blocking_ids"]
    assert st["CB-TOP-CORNER"]["leg_length"].startswith("DRAWN_UNDIMENSIONED")
    assert st["STARTER"]["leg_length"].startswith("PRINTED_MINIMUM")
    assert {p["pop_id"] for p in out["leg_bound_proposals"]} == {"SLAB-BOTTOM", "SLAB-TOP"}
    assert all(p["value"] is None for p in out["leg_bound_proposals"])


def test_development_villa_input_matches_its_builder():
    b = _load("t371in", "t371_alsenan_input.py")
    data, binding = b.build()
    assert json.loads(json.dumps(data)) == json.loads((HERE / "ALSENAN_BAR_SHAPE_INPUT.json").read_text("utf-8"))
    assert binding == json.loads((HERE / "LINE_BINDING_T371.json").read_text("utf-8"))
