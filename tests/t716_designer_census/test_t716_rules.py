"""T-716 R-T716-1: one cause bucket per HELD line, per-unit sums only, blank never 0 (synthetic, not the training villa)."""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t716"))

import t716_rules as R  # noqa: E402


def _ix(lid, code, unit, lo=None, hi=None, cls="HELD", eid=None):
    return {"line_id": lid, "item_code": code, "unit": unit, "held_low": lo, "held_high": hi, "class": cls,
            "element_id": eid or f"E:{lid}"}


def _rec(rfi=None, notes=None, still=None):
    r = {"rfi": {"question": rfi} if rfi else None, "notes": notes}
    if still:
        r["calculation"] = {"inputs": {"fill": {"still_held": [{"item": still, "wall": "W1"}]}}}
    return r


def _k(rec):
    return R.classify_own(rec)


def test_own_classification_order_and_ids():
    assert _k(_rec("beam depth not printed (D-4, Q-61)"))["bucket"] == "D-04"
    assert _k(_rec("blinding: RFI S08 / S23 open"))["bucket"] == "RFI-S08+RFI-S23"
    assert _k(_rec("owner Q-34 open"))["bucket"] == "Q-34"
    assert _k(_rec("HELD on owner question OQ-31 (blank)"))["bucket"] == "Q-31"
    assert _k(_rec("ORR-007: form not chosen"))["bucket"] == "ORR-007"
    assert _k(_rec("STAIR_RISER_NOT_ESTABLISHED: flight 1"))["bucket"] == "STAIR_RISER_NOT_ESTABLISHED"
    assert _k(_rec("face R4-1 SPLIT_UNRESOLVED: member in 2 lines"))["bucket"] == "SPLIT_UNRESOLVED"
    assert _k(_rec("the waist thickness (designer)"))["kind"] == "DESIGNER_TAG"
    assert _k(_rec("engine method gap at the junction end; not printed"))["kind"] == "METHOD_GAP"
    assert _k(_rec("waist thickness not printed"))["kind"] == "NOT_PRINTED"
    assert _k(_rec(None, ["held: datum"]))["kind"] == "NAMED_TEXT"
    assert _k(_rec())["kind"] == "UNNAMED"
    # fill lines: the still_held items are part of the cause text
    assert _k(_rec(None, "HELD walls", still="wall top at the unlabelled span D-04"))["bucket"] == "D-04"


def test_identifiers_that_are_not_items():
    assert _k(_rec(None, "AD-39 HOLD"))["kind"] == "NAMED_TEXT"                   # inside a word
    assert _k(_rec(None, "junction END at D-1F-06 and D-GF-04"))["kind"] == "NAMED_TEXT"   # door ids
    assert _k(_rec(None, "P-C:GROUND_BEAMS:GROUND:BAND0001 held"))["kind"] == "NAMED_TEXT"  # an element id, not a code
    assert _k(_rec(None, "HIDDEN_2CC_2CD faces"))["kind"] == "NAMED_TEXT"         # DXF handles, not a reason code


def test_normal_census_per_unit_never_mixed_and_dependents_follow_the_host():
    ix = [
        _ix("L-00000000000000000001", "STR.CONC.BEAM", "m3", 1.0, 2.0),
        _ix("L-00000000000000000002", "STR.CONC.BEAM", "m3"),
        _ix("L-00000000000000000003", "FIN.PLASTER", "m2", 10.0, 12.5),
        _ix("L-00000000000000000004", "STR.CONC.BEAM", "m3", 0.5, None),
        _ix("L-00000000000000000005", "MAS.BLOCK", "m2", None, 7.25),
        _ix("L-00000000000000000006", "FIN.PAINT", "m2"),
        _ix("L-00000000000000000007", "STR.FORMWORK", "m2", eid="FW:L-00000000000000000002:FACES:HELD"),
        _ix("L-00000000000000000008", "MAS.UNITS.BLACK", "pcs"),
        _ix("L-00000000000000000009", "STR.CONC.BEAM", "m3", cls="RELEASED"),
        _ix("L-00000000000000000010", "STR.FORMWORK", "m2", eid="FW:L-00000000000000000009:FACES:HELD"),
    ]
    recs = {
        "L-00000000000000000001": _rec("section not printed D-04"),
        "L-00000000000000000002": _rec("section not printed D-04"),
        "L-00000000000000000003": _rec(None, "ceiling level D-40"),
        "L-00000000000000000004": _rec("D-04 and D-30"),
        "L-00000000000000000005": _rec(None, "Q-34 top roof"),
        "L-00000000000000000006": _rec(),
        "L-00000000000000000007": _rec("formwork faces HELD"),
        "L-00000000000000000008": _rec(None, "materials wait for L-00000000000000000005: walls"),
        "L-00000000000000000009": _rec(),
        "L-00000000000000000010": _rec("formwork face R4-9: depth not dimensioned"),
    }
    c = R.census(ix, recs)
    assert c["held_lines"] == 9                                   # the RELEASED line is not counted
    assert sum(b["lines"] for b in c["buckets"]) == 9
    b = {x["bucket"]: x for x in c["buckets"]}
    d04 = {(r["item_code"], r["unit"]): r for r in b["D-04"]["by_family_unit"]}
    assert d04[("STR.CONC.BEAM", "m3")] == {"item_code": "STR.CONC.BEAM", "unit": "m3", "lines": 2, "dependent": 0,
                                            "range": 1, "range_low": 1.0, "range_high": 2.0, "at_least": 0,
                                            "at_least_sum": 0.0, "at_most": 0, "at_most_sum": 0.0, "blank": 1}
    # the formwork line of a HELD host takes the host's item, flagged dependent; a RELEASED host gives nothing
    assert d04[("STR.FORMWORK", "m2")]["dependent"] == 1
    assert c["assignment"]["L-00000000000000000007"]["host"] == "L-00000000000000000002"
    assert c["assignment"]["L-00000000000000000010"]["kind"] == "NOT_PRINTED"
    assert c["assignment"]["L-00000000000000000008"]["bucket"] == "Q-34"
    assert b["D-04+D-30"]["lines"] == 1 and b["Q-34"]["by_family_unit"][0]["at_most_sum"] == 7.25
    assert b["UNNAMED"]["line_ids"] == ["L-00000000000000000006"] and b["UNNAMED"]["finding"]
    # per D-id view: the shared line is under D-04 and D-30 as SHARED, never in their SOLE counts
    assert c["per_d_id"]["D-04"]["sole_lines"] == 3 and c["per_d_id"]["D-04"]["shared_lines"] == 1
    assert c["per_d_id"]["D-30"]["sole_lines"] == 0
    assert [r["unit"] for r in b["D-40"]["by_family_unit"]] == ["m2"]


def test_adverse_blank_never_zero_cycles_and_duplicates():
    ix = [_ix("L-00000000000000000001", "STR.CONC.STAIR", "m3"),
          _ix("L-00000000000000000002", "STR.CONC.STAIR", "m3", 0.0, 0.0),
          _ix("L-00000000000000000003", "X", "m2"), _ix("L-00000000000000000004", "X", "m2")]
    recs = {"L-00000000000000000001": _rec("D-08"), "L-00000000000000000002": _rec("D-08"),
            "L-00000000000000000003": _rec(None, "waits for L-00000000000000000004"),
            "L-00000000000000000004": _rec(None, "waits for L-00000000000000000003")}
    c = R.census(ix, recs)
    r = [x for x in c["buckets"] if x["bucket"] == "D-08"][0]["by_family_unit"][0]
    assert r["blank"] == 1 and r["range"] == 1               # a printed 0 .. 0 bound stays a bound; a blank stays blank
    assert c["assignment"]["L-00000000000000000003"]["kind"] == "NAMED_TEXT"     # a host cycle ends, never loops
    with pytest.raises(AssertionError):
        R.census(ix + [ix[0]], recs)
