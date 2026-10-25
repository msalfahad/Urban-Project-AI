"""T-303 hand villa V-303 (not Alsenan): two wet rooms with upturns and thresholds (one door between them), one roof
with its parapet upturn, and the pool / tank presence ruling. Every value by hand:

  B1 bath 2.40 x 2.00 = 4.80 m2, boundary 2 (2.40 + 2.00) = 8.80 lm, door D1 0.80 to the corridor, door D2 0.80 to B2
     walls only 8.80 - 0.80 - 0.80 = 7.20 lm -> upturn 7.20 x 0.20 = 1.44 m2
  B2 W.C. 1.50 x 1.20 = 1.80 m2, boundary 5.40 lm, door D2 only: 5.40 - 0.80 = 4.60 lm -> 0.92 m2 (no upturn across D2
     on either side, Q-35 C)
  D1, D2 thresholds 0.80 x 0.15 = 0.12 m2 each; ONE element per physical door (D2 belongs to B1 and B2 once)
  R1 roof 10.00 x 6.00 = 60.00 m2 inside the parapet; parapet upturn 2 (10.00 + 6.00) = 32.00 lm
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "research/agents_t303"))

import t303_wp_families as F  # noqa: E402

W = F.W
WET, ROOF = "WP.WET_AREA", "WP.ROOF"


def el(fam, item, unit, element, face, qty, scope, floor="GF"):
    return {"family": fam, "item_code": item, "unit": unit, "element": element, "face": face, "floor": floor,
            "applicability": "APPLICABLE", "qty": qty, "source": "V-303 hand", "owner": scope}


def villa():
    up1 = round(F.walls_only_lm(8.80, [0.80, 0.80]) * F.UPTURN_M, 6)
    up2 = round(F.walls_only_lm(5.40, [0.80]) * F.UPTURN_M, 6)
    els = [el(WET, "FL", "m2", "B1", "FLOOR", 4.80, "B1"), el(WET, "FL", "m2", "B2", "FLOOR", 1.80, "B2"),
           el(WET, "UP", "m2", "B1", "WALLS", up1, "B1"), el(WET, "UP", "m2", "B2", "WALLS", up2, "B2"),
           el(WET, "DW", "m2", "DOOR:D1", "THRESHOLD", F.doorway_m2(0.80, 0.15), "B1"),
           el(WET, "DW", "m2", "DOOR:D2", "THRESHOLD", F.doorway_m2(0.80, 0.15), "B1|B2"),
           el(ROOF, "RF", "m2", "R1", "INSIDE_PARAPET", 60.00, "R1", "RF"),
           el(ROOF, "RU", "lm", "R1", "PARAPET", 32.00, "R1", "RF")]
    lines = [{"line_id": f"L{i}", "item_code": ic, "unit": u, "evidence_state": "SOURCE_DERIVED", "measured_net": q,
              "scope": s} for i, (ic, u, q, s) in enumerate([("FL", "m2", 4.80, "B1"), ("FL", "m2", 1.80, "B2"),
                                                             ("UP", "m2", 1.44, "B1"), ("UP", "m2", 0.92, "B2"),
                                                             ("DW", "m2", 0.12, "D1"), ("DW", "m2", 0.12, "D2"),
                                                             ("RF", "m2", 60.0, "R1"), ("RU", "lm", 32.0, "R1")])]
    links = {"L0": ["FL[m2]/B1/FLOOR"], "L1": ["FL[m2]/B2/FLOOR"], "L2": ["UP[m2]/B1/WALLS"], "L3": ["UP[m2]/B2/WALLS"],
             "L4": ["DW[m2]/DOOR:D1/THRESHOLD"], "L5": ["DW[m2]/DOOR:D2/THRESHOLD"],
             "L6": ["RF[m2]/R1/INSIDE_PARAPET"], "L7": ["RU[lm]/R1/PARAPET"]}
    return els, lines, links


def rows(els, lines, links):
    rep = F.join_family(els, lines, links)
    return rep, {r["line_id"]: r for r in F.line_rows(rep, lines, links, lambda ln: ln["scope"],
                                                       lambda r: r["owner"], tol=0.0005)}


def test_hand_values():
    assert F.walls_only_lm(8.80, [0.80, 0.80]) == 7.20 and F.walls_only_lm(5.40, [0.80]) == 4.60
    assert F.doorway_m2(0.80, 0.15) == 0.12


def test_normal_every_face_in_line_residual_zero_every_line_whole():
    els, lines, links = villa()
    rep, lr = rows(els, lines, links)
    assert rep["counts"] == {"IN_LINE": 8, "NOT_APPLICABLE": 0, "MISSING": 0}
    assert all(f["residual"] == 0.0 and f["whole_line_countable"] for f in rep["families"])
    assert {k: v["countability"] for k, v in lr.items()} == {f"L{i}": "WHOLE" for i in range(8)}


def test_the_door_between_two_wet_rooms_in_two_lines_is_refused_strictly_and_reported_as_a_double():
    els, lines, links = villa()
    lines.append({"line_id": "L8", "item_code": "DW", "unit": "m2", "evidence_state": "SOURCE_DERIVED",
                  "measured_net": 0.12, "scope": "D2"})
    links["L8"] = ["DW[m2]/DOOR:D2/THRESHOLD"]              # B2's side books the same threshold again
    with pytest.raises(W.InventoryError, match="double count"):
        W.join(els, lines, links)
    rep, lr = rows(els, lines, links)
    assert rep["double_carried"] == [{"key": "DW[m2]/DOOR:D2/THRESHOLD", "lines": ["L5", "L8"], "item": ("DW", "m2")}]
    fam = {f["item_code"]: f for f in rep["families"]}
    assert fam["DW"]["whole_line_countable"] is False and fam["DW"]["double_carried"] == 1
    assert lr["L5"]["countability"] == lr["L8"]["countability"] == "COMPONENT"
    assert "double count" in lr["L8"]["why"] and lr["L8"]["elements"] == 0


def test_an_upturn_face_in_two_lines_is_refused():
    els, lines, links = villa()
    links["L3"] = ["UP[m2]/B2/WALLS", "UP[m2]/B1/WALLS"]    # B2's line also books B1's walls
    with pytest.raises(W.InventoryError, match="double count"):
        W.join(els, lines, links)


def test_a_doorless_cell_taking_wet_scope_is_refused_D_C3():
    rooms = {"B1": {"doors": ["D1", "D2"]}, "B2": {"doors": ["D2"]}}
    assert F.check_wet_rooms(rooms, ["B1", "B2"])
    with pytest.raises(W.InventoryError, match="D-C3"):
        F.check_wet_rooms({**rooms, "C9": {"doors": [], "open_edges": []}}, ["B1"])   # a cell with no door
    with pytest.raises(W.InventoryError, match="D-C3"):
        F.check_wet_rooms(rooms, ["B1", "B2", "C9"])           # a line on a cell that is not a wet room
    assert F.check_wet_rooms({"L1": {"doors": [], "open_edges": [("OPEN", 1.2)]}}, ["L1"])  # open lobby: allowed


def test_not_applicable_without_evidence_is_refused():
    with pytest.raises(W.InventoryError, match="without evidence"):
        F.presence_ruling("WP.POOL_TANK", "PM", "m2", "TANK", "ALL", "RF", "hand", not_printed={"sheet": "S1"})
    els, lines, links = villa()
    els.append({**el(ROOF, "RF", "m2", "R2", "X", None, "R2"), "applicability": "NOT_APPLICABLE"})
    with pytest.raises(W.InventoryError, match="without evidence"):
        W.validate_inventory(els)


def test_missing_reported_as_zero_is_refused_and_missing_stays_blank():
    els, lines, links = villa()
    with pytest.raises(W.InventoryError, match="never 0"):
        W.validate_inventory(els + [el(WET, "FL", "m2", "B3", "FLOOR", 0, "B3")])
    rep, lr = rows(els + [el(WET, "FL", "m2", "B3", "FLOOR", None, "B3")], lines, links)
    b3 = next(r for r in rep["elements"] if r["element"] == "B3")
    assert b3["status"] == "MISSING" and b3["qty"] is None
    fam = {f["item_code"]: f for f in rep["families"]}
    assert fam["FL"]["missing"] == 1 and fam["FL"]["whole_line_countable"] is False
    assert lr["L0"]["countability"] == "WHOLE"                 # another room's omission does not hide B1's own line


def test_presence_ruling_pool_and_tank():
    pr = F.presence_ruling("WP.POOL_TANK", "PM", "m2", "POOL", "SHELL", "GF", "hand",
                           printed={"sheet": "S7 pool detail", "ref": "TEXT 'MEMBRANE'"})
    np_ = F.presence_ruling("WP.POOL_TANK", "TM", "m2", "TANK", "ALL", "RF", "hand",
                            not_printed={"sheet": "S9 roof", "ref": "tank place only, no WP layer"})
    rep = F.join_family([pr, np_], [], {})
    st = {r["element"]: (r["status"], r["qty"]) for r in rep["elements"]}
    assert st == {"POOL": ("MISSING", None), "TANK": ("NOT_APPLICABLE", None)}   # printed, no line: an omission, blank
    with pytest.raises(W.InventoryError, match="not established"):
        F.presence_ruling("WP.POOL_TANK", "PM", "m2", "POOL", "SHELL", "GF", "hand")
    with pytest.raises(W.InventoryError, match="disagree"):
        F.presence_ruling("WP.POOL_TANK", "PM", "m2", "POOL", "SHELL", "GF", "hand",
                          printed={"sheet": "a", "ref": "b"}, not_printed={"sheet": "c", "ref": "d"})


def test_scope_unknown_is_missing_blank_and_makes_its_roof_line_a_component():
    els, lines, links = villa()
    els.append(F.scope_unknown(ROOF, "RF", "m2", "R1", "DOME_FOOTPRINT", "RF", "hand", "dome build-up not settled",
                               scope="R1"))
    rep, lr = rows(els, lines, links)
    dome = next(r for r in rep["elements"] if r["face"] == "DOME_FOOTPRINT")
    assert dome["status"] == "MISSING" and dome["qty"] is None and dome["note"].startswith("SCOPE_UNKNOWN")
    assert lr["L6"]["countability"] == "COMPONENT" and "missing / held" in lr["L6"]["why"]
    with pytest.raises(W.InventoryError, match="reason"):
        F.scope_unknown(ROOF, "RF", "m2", "R1", "X", "RF", "hand", "")


def test_a_residual_is_named_never_absorbed_and_held_lines_stay_blank():
    els, lines, links = villa()
    lines[3] = {**lines[3], "measured_net": 0.82}             # B2 upturn short by 0.50 lm x 0.20 (a window taken as glazing)
    lines[6] = {**lines[6], "evidence_state": "BLOCKED_RFI", "measured_net": None}
    rep, lr = rows(els, lines, links)
    assert lr["L3"]["countability"] == "COMPONENT" and lr["L3"]["residual"] == 0.1 and "+0.100000 m2" in lr["L3"]["why"]
    assert lr["L6"]["countability"] == "HELD" and lr["L6"]["inventory_qty"] is None


def test_unit_and_geometry_guards_mirror_rotation_invariant():
    with pytest.raises(W.InventoryError, match="millimetres"):
        F.walls_only_lm(8800, [800])                          # mm input refused
    with pytest.raises(W.InventoryError, match="exceed"):
        F.walls_only_lm(1.50, [0.80, 0.80])
    with pytest.raises(W.InventoryError, match="never 0"):
        F.doorway_m2(0.80, None)                               # missing depth: HELD, never 0
    # mirror / rotation: the walls-only length depends on lengths only, not on the order or orientation of the gaps
    assert F.walls_only_lm(8.80, [0.80, 0.80]) == F.walls_only_lm(8.80, [0.80], [], [0.80])
