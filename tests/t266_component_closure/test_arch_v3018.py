"""T-266: ARCH_TAKEOFF_V3.0.18 component closure on a hand-calculated NON-Alsenan villa (K266), normal and adverse.

Villa K266 (hand calculation, m / m3):
  main stair line (HELD blank parent): half landing 1.20 x 1.10 x 0.15 = 0.198000 VERIFIED; upper flight 10 risers 0.17 /
      treads 0.30 / width 1.10, steps 10 x 0.5 x 0.30 x 0.17 x 1.10 = 0.280500, waist sqrt(3.00^2 + 1.70^2) = 3.448188
      x 0.15 x 1.10 = 0.568951 -> 0.849451 VERIFIED; part = 1.047451; the winder turn HELD (no detail);
  round stair line (HELD blank): straight flight by an owner riser rule 0.500000 ASSUMED - OWNER-APPROVED; curved part HELD;
  landing line BOUNDED 0.300 .. 0.320: plates 2.00 x 1.00 x 0.15 = 0.300000 DRAWING-CONFIRMED (0.320 retired);
  entrance flight PROVISIONAL 0.600 on a convention waist -> HELD blank;
  1F arrival landing ARCH.SPACE 2.00 x 2.00 = 4.0000 m2 -> its marble material line 4.0000 m2;
  pantry wet floor 10.0000 m2 + a confirmed piece 0.50 x 2.50 = 1.2500 m2 -> 11.2500 m2.
"""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engine.source import arch_v3018 as A  # noqa: E402
from engine.source import boq_line as BL  # noqa: E402

PID, REV = "villa-k266", "f" * 64
OA = A.OA
LANDING, UPPER = 1.20 * 1.10 * 0.15, 10 * 0.5 * 0.30 * 0.17 * 1.10 + (3.00 ** 2 + 1.70 ** 2) ** 0.5 * 0.15 * 1.10


def _ln(code, eid, ev, net=None, unit=None, br=None, rfi=None, floor="GF", formula="engine"):
    return BL.make_line(project_id=PID, revision_set_sha256=REV, item_code=code, unit=unit or BL.ITEMS[code][3],
                        evidence_state=ev, measured_net=net, element_id=eid, floor=floor, physical_element=eid,
                        bounded_range=br, formula=formula, rfi=rfi, documents=[{"file": "k266.dxf"}],
                        rule_id="R-K", rule_version="1", notes="k266")


def lines():
    q = {"question": "held", "unlocks": "x"}
    return [_ln("STR.CONC.STAIR", "K:ST1", "BLOCKED_RFI", rfi=q),
            _ln("STR.CONC.STAIR", "K:ST2", "BLOCKED_RFI", rfi=q),
            _ln("STR.CONC.STAIR", "K:LD", "BOUNDED_EXPOSURE", br={"low": 0.30, "high": 0.32, "basis": "two"}),
            _ln("STR.CONC.STAIR", "K:ST3", "PROVISIONAL", net=0.6, formula="convention waist 0.175"),
            _ln("ARCH.SPACE", "K:SPACE:LAND1F", "SOURCE_DERIVED", net=4.0, floor="1F"),
            _ln("FIN.FLOOR.WET_TILE", "K:PANTRY", "SOURCE_DERIVED", net=10.0),
            _ln("FIN.FLOOR.PORCELAIN", "K:LIVING", "SOURCE_DERIVED", net=22.2, floor="1F")]


def ids(ls):
    return {ln["location"]["element_id"]: ln["line_id"] for ln in ls}


def doc(ls=None):
    ls = ls or lines()
    i = ids(ls)
    src = {"file": "k266_ledger.csv", "sha256": "a" * 64, "task": "T-K", "merge_commit": "abc1234",
           "checker_run": "Checker K 1"}
    return {"schema": A.INPUTS_SCHEMA, "project": PID, "sources": [src], "records": [
        {"kind": "SPLIT", "line_id": i["K:ST1"], "item_code": "STR.CONC.STAIR", "element_id": "K:ST1", "task": "T-K",
         "physical_element": "main stair", "before": {"evidence_state": "BLOCKED_RFI", "measured_net": None},
         "still_held": [{"piece": "K-WINDER", "item": "no winder detail"}],
         "parts": [{"part": "VERIFIED LD + U", "status": "VERIFIED", "value": 1.047451, "verified_by": "Checker K 0",
                    "pieces": [{"id": "K-LD", "value": 0.198, "status": "VERIFIED"},
                               {"id": "K-U", "value": 0.849451, "status": "VERIFIED"}]}]},
        {"kind": "SPLIT", "line_id": i["K:ST2"], "item_code": "STR.CONC.STAIR", "element_id": "K:ST2", "task": "T-K",
         "physical_element": "round stair", "before": {"evidence_state": "BLOCKED_RFI", "measured_net": None},
         "still_held": [{"piece": "K-CURVE", "item": "curved part not dimensioned"}],
         "parts": [{"part": "OWNER S", "status": OA, "value": 0.5, "owner_source": "Q-K A",
                    "pieces": [{"id": "K-S", "value": 0.5, "status": OA}]}]},
        {"kind": "REBASE", "line_id": i["K:LD"], "item_code": "STR.CONC.STAIR", "element_id": "K:LD", "task": "T-K",
         "physical_element": "landing", "before": {"evidence_state": "BOUNDED_EXPOSURE", "measured_net": None},
         "status": "DRAWING-CONFIRMED", "value": 0.3,
         "pieces": [{"id": "K-LDW", "value": 0.15, "status": "DRAWING-CONFIRMED"},
                    {"id": "K-LDE", "value": 0.15, "status": "DRAWING-CONFIRMED"}]},
        {"kind": "HOLD", "line_id": i["K:ST3"], "item_code": "STR.CONC.STAIR", "element_id": "K:ST3", "task": "T-K",
         "physical_element": "entrance flight", "before": {"evidence_state": "PROVISIONAL", "measured_net": 0.6},
         "held_item": "waist not printed", "reasons": ["convention waist"], "closable_named": "steps 0.2"},
        {"kind": "MATERIAL", "id": "K-MARBLE-1F", "line_id": i["K:SPACE:LAND1F"], "material_of": i["K:SPACE:LAND1F"],
         "item_code": "FIN.MARBLE.LANDING", "element_id": "K:SPACE:LAND1F", "unit": "m2", "floor": "1F", "task": "T-K",
         "physical_element": "1F arrival landing marble", "status": "DRAWING-CONFIRMED", "value": 4.0,
         "item_en": "Stair landing marble", "item_ar": "رخام", "trade": "STAIR_FINISH", "owner_source": "Q-K B"},
        {"kind": "PIECE_IN", "line_id": i["K:PANTRY"], "item_code": "FIN.FLOOR.WET_TILE", "element_id": "K:PANTRY",
         "task": "T-K", "physical_element": "pantry floor", "before": {"evidence_state": "SOURCE_DERIVED",
                                                                       "measured_net": 10.0},
         "piece": {"id": "K-STRIP-9", "value": 1.25, "status": "DRAWING-CONFIRMED", "class": "WET",
                   "class_source": "owner Q-K C"}, "after": 11.25}]}


def run(d=None, ls=None):
    ls = ls or lines()
    d = A.load_inputs(d or doc(ls))
    ch, log = A.changes_for(d, ls)
    out, ident = A.integrate(ls, ch)
    return ls, ch, log, out, ident


def test_hand_values():
    assert round(LANDING, 6) == 0.198 and round(UPPER, 6) == 0.849451
    assert round(LANDING + UPPER, 6) == 1.047451


def test_normal_split_rebase_hold_material_piece():
    ls, ch, log, out, ident = run()
    by = {ln["location"]["element_id"]: ln for ln in out}
    p1 = by["K:ST1#CLOSABLE:VERIFIED_LD___U"]
    assert p1["evidence_state"] == "SOURCE_DERIVED" and p1["measured_net"] == 1.047451
    assert by["K:ST1"]["evidence_state"] == "BLOCKED_RFI" and by["K:ST1"]["measured_net"] is None
    assert "K-WINDER" in by["K:ST1"]["rfi"]["question"]
    p2 = [ln for e, ln in by.items() if e.startswith("K:ST2#")][0]
    assert p2["evidence_state"] == "PROVISIONAL" and p2["measured_net"] == 0.5 and "Q-K A" in p2["notes"]
    assert by["K:LD"]["evidence_state"] == "SOURCE_DERIVED" and by["K:LD"]["measured_net"] == 0.3
    assert by["K:LD"]["bounded_range"] is None
    assert by["K:ST3"]["evidence_state"] == "BLOCKED_RFI" and by["K:ST3"]["measured_net"] is None
    m = by["K:SPACE:LAND1F#MATERIAL:FIN_MARBLE_LANDING"]
    assert m["item_code"] == "FIN.MARBLE.LANDING" and m["measured_net"] == 4.0 and m["unit"] == "m2"
    assert by["K:SPACE:LAND1F"]["measured_net"] == 4.0                 # the area line unchanged
    assert by["K:PANTRY"]["measured_net"] == 11.25
    assert ident["replaced"] == 5 and ident["added"] == 3 and ident["split_parts"] == 2
    assert ident["outside_rows"] == 2                                  # living porcelain + the area line, byte-identical
    assert by["K:LIVING"] == ls[-1]
    # released concrete on stair lines: 0.6 before -> 1.047451 + 0.5 + 0.3 after
    rel = sum(ln["measured_net"] for ln in out if ln["item_code"] == "STR.CONC.STAIR" and ln["measured_net"])
    assert round(rel, 6) == 1.847451


def test_order_invariant_line_set():
    ls = lines()
    d = doc(ls)
    d2 = copy.deepcopy(d)
    d2["records"] = list(reversed(d2["records"]))
    o1 = run(d, ls)[3]
    o2 = run(d2, lines())[3]
    assert sorted(A.A30.line_sha(x) for x in o1) == sorted(A.A30.line_sha(x) for x in o2)


def test_write_files(tmp_path):
    ls, ch, log, out, ident = run()
    names, ident2, led = A.write(tmp_path, ls, ch, log, doc(ls))
    assert "V3_0_18_BOQ_LINES.json" in names and (tmp_path / "V3_0_18_DIFF.csv").exists()
    assert ident2["diff"]["vs_v3_0_17"] == {"SAME": 2, "CHANGED": 5, "ADDED": 3}
    kinds = sorted(r["kind"] for r in led["rows"])
    assert kinds == ["HOLD", "MATERIAL", "PIECE_IN", "REBASE", "SPLIT_PARENT", "SPLIT_PARENT", "SPLIT_PART",
                     "SPLIT_PART"]


def _bad(mut, match):
    ls = lines()
    d = doc(ls)
    mut(d, ls)
    with pytest.raises((A.InputsError, ValueError), match=match):
        run(d, ls)


def test_adverse_part_released_while_parent_carries_a_figure():
    def m(d, ls):
        ls[0]["evidence_state"], ls[0]["measured_net"], ls[0]["rfi"] = "PROVISIONAL", 1.2, None
        d["records"][0]["before"] = {"evidence_state": "PROVISIONAL", "measured_net": 1.2}
    _bad(m, "split parent is a HELD blank")


def test_adverse_parent_given_a_figure_after_split_is_refused_by_the_check():
    ls, ch, log, out, ident = run()
    par = [ln for ln in out if ln["location"]["element_id"] == "K:ST1"][0]
    par["evidence_state"], par["measured_net"], par["rfi"] = "PROVISIONAL", 1.0, None
    with pytest.raises(ValueError, match="double count"):
        A.check_splits(out)


def test_adverse_piece_in_two_parts():
    def m(d, ls):
        d["records"][1]["parts"][0]["pieces"][0]["id"] = "K-LD"
    _bad(m, "two lines")


def test_adverse_mixed_status_and_convention_piece():
    def m(d, ls):
        d["records"][0]["parts"][0]["pieces"][1]["status"] = "DRAWING-CONFIRMED"
    _bad(m, "one status per line")

    def m2(d, ls):
        d["records"][0]["parts"][0]["pieces"][1]["status"] = "CONVENTION"
    _bad(m2, "not closable")


def test_adverse_sum_and_mm_slip():
    def m(d, ls):
        d["records"][0]["parts"][0]["value"] = 1047.451
    _bad(m, "sum of its pieces")


def test_adverse_verified_without_checker_and_owner_approved_without_source():
    def m(d, ls):
        d["records"][0]["parts"][0].pop("verified_by")
    _bad(m, "checker run")

    def m2(d, ls):
        d["records"][1]["parts"][0].pop("owner_source")
    _bad(m2, "answered owner decision")


def test_adverse_held_with_zero_and_piece_value_zero():
    def m(d, ls):
        d["records"][3]["value"] = 0.0
    _bad(m, "no figure")

    def m2(d, ls):
        d["records"][0]["still_held"][0]["value"] = 0
    _bad(m2, "held piece carries no figure")

    def m3(d, ls):
        d["records"][2]["pieces"][0]["value"] = 0.0
        d["records"][2]["value"] = 0.15
    _bad(m3, "value > 0")


def test_adverse_second_marble_line_on_one_element():
    def m(d, ls):
        r = copy.deepcopy(d["records"][4])
        r["id"] = "K-MARBLE-1F-2"
        d["records"].append(r)
    _bad(m, "one element, one material line")


def test_adverse_material_value_or_unit_not_the_element_line():
    def m(d, ls):
        d["records"][4]["value"] = 4.875
    _bad(m, "not the element line")

    def m2(d, ls):
        d["records"][4]["unit"] = "m3"
    _bad(m2, "not the element line")


def test_adverse_piece_already_booked_elsewhere():
    def m(d, ls):
        x = _ln("ARCH.THRESHOLD" if "ARCH.THRESHOLD" in BL.ITEMS else "FIN.FLOOR.PORCELAIN", "K:STRIP",
                "SOURCE_DERIVED", net=1.25, formula="opening strip K-STRIP-9")
        ls.append(x)
    _bad(m, "already booked")


def test_adverse_stale_before_and_unknown_line():
    def m(d, ls):
        d["records"][3]["before"]["measured_net"] = 0.7
    _bad(m, "stale")

    def m2(d, ls):
        d["records"][2]["line_id"] = "L-00000000000000000000"
    _bad(m2, "does not carry")


def test_adverse_line_named_twice_and_unmerged_task():
    def m(d, ls):
        d["records"].append(copy.deepcopy(d["records"][3]))
    _bad(m, "named twice")

    def m2(d, ls):
        d["records"][2]["task"] = "T-NOT-MERGED"
    _bad(m2, "merged sources")


def test_adverse_new_material_line_never_verified():
    def m(d, ls):
        d["records"][4]["status"] = "VERIFIED"
        d["records"][4]["verified_by"] = "x"
    _bad(m, "never VERIFIED")


def test_no_input_changes_nothing():
    ls = lines()
    ch, log = A.changes_for(None, ls)
    out, ident = A.integrate(ls, ch)
    assert ch == [] and out == ls and log["state"] == "NO_PROJECT_INPUT"
    assert json.dumps(A.policy_record())
