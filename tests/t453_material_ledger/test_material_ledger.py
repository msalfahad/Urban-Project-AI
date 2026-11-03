"""T-453 part 1: the blockwork material ledger beside the candidate. A synthetic villa (VILLA-SYNTH-53, not any client
project) hand-calculated, adverse cases (15 cm black face, held lines, unit error, schedule gaps, beam soffit at the
head, held openings, order), and the committed ledger rebuilt byte-identically from its pinned inputs."""

import copy
import json
import random
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
for p in (ROOT, ROOT / "research" / "agents_t453"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

import t453_material_ledger as T  # noqa: E402

SCHED = [
    {"RECORD": "SCHEDULE_ROW", "ROW_ID": "L1", "WIDTH_PRINTED": "0 -100", "WIDTH_LO_CM": "0", "WIDTH_HI_CM": "100",
     "D_CM": "20", "BOTTOM_PRINTED": "2Ø12", "TOP_PRINTED": "2Ø10", "STIRRUPS_PRINTED": "5Ø8/M"},
    {"RECORD": "SCHEDULE_ROW", "ROW_ID": "L2", "WIDTH_PRINTED": "101 - 200", "WIDTH_LO_CM": "101", "WIDTH_HI_CM": "200",
     "D_CM": "20", "BOTTOM_PRINTED": "2Ø14", "TOP_PRINTED": "2Ø12", "STIRRUPS_PRINTED": "5Ø8/M"},
    {"RECORD": "SCHEDULE_ROW", "ROW_ID": "L3", "WIDTH_PRINTED": "201 - 300", "WIDTH_LO_CM": "201", "WIDTH_HI_CM": "300",
     "D_CM": "30", "BOTTOM_PRINTED": "3Ø16", "TOP_PRINTED": "3Ø14", "STIRRUPS_PRINTED": "5Ø8/M"},
    {"RECORD": "DETAIL_READING", "ROW_ID": "MIN-BEARING", "WIDTH_PRINTED": "MIN.40cm", "WIDTH_LO_CM": "",
     "WIDTH_HI_CM": "", "D_CM": "", "BOTTOM_PRINTED": "", "TOP_PRINTED": "", "STIRRUPS_PRINTED": ""},
]


def _ln(lid, eid, cls, net):
    return {"line_id": lid, "item_code": "MAS.BLOCK", "element_id": eid, "class": cls, "measured_net": net,
            "unit": "m2", "held_low": None, "held_high": None, "binding": None, "unbound_records": []}


def _w(wid, bt, st, carried, ops=None, ps=None):
    return {"wall_id": wid, "block_type": bt, "status": st, "part_status": ps, "carried": carried, "openings": ops}


def _op(oid, kind, w, h, s, hs="PRINTED"):
    return {"ID": oid, "KIND": kind, "WIDTH_M": w, "WIDTH_BASIS": "printed", "HEIGHT_M": h, "SILL_M": s,
            "HEIGHT_STATUS": hs}


def villa():
    """GF 0.20: black VERIFIED wall S-1 (20.00 m2, door D1 1.00 m) + white DRAWING-CONFIRMED S-2 (10.00 m2, window
    X1 2.50 m, head 2.60) and S-3 (6.00 m2 established part, window X2 1.20 m, head 3.10); GF 0.15: black VERIFIED
    S-4 (8.00 m2); 1F 0.20: one HELD parent (no figure) hosting door D2 ON_HELD_WALL."""
    index = {"candidate_version": "SYNTH", "lines": [
        _ln("L-a", "GF-WALLS:walls t=0.20", "HELD", None),
        _ln("L-b", "GF-WALLS:walls t=0.20#BLOCKWORK:VERIFIED_BLACK", "RELEASED", 20.0),
        _ln("L-c", "GF-WALLS:walls t=0.20#BLOCKWORK:DRAWING_CONFIRMED_WHITE", "RELEASED", 16.0),
        _ln("L-d", "GF-WALLS:walls t=0.15#BLOCKWORK:VERIFIED_BLACK", "RELEASED", 8.0),
        _ln("L-e", "1F-WALLS:walls t=0.20", "HELD", None),
        {"line_id": "L-x", "item_code": "ARCH.PLASTER", "element_id": "x", "class": "RELEASED", "measured_net": 1.0,
         "unit": "m2"}]}
    fill = {"lines": [
        {"line_id": "L-a", "item_code": "MAS.BLOCK", "floor": "GF", "family": 0.2, "walls": [
            _w("S-1", "BLACK", "VERIFIED", 20.0, "D1 2.2000 DEDUCTED"),
            _w("S-2", "WHITE", "DRAWING-CONFIRMED", 10.0, "X1 3.5000 DEDUCTED"),
            _w("S-3", "WHITE", "ESTABLISHED PART + HELD", 6.0, "X2 1.2000 DEDUCTED", ps="DRAWING-CONFIRMED"),
            _w("S-9", "WHITE", "HELD", None)]},
        {"line_id": "L-z", "item_code": "MAS.BLOCK", "floor": "GF", "family": 0.15, "walls": [
            _w("S-4", "BLACK", "VERIFIED", 8.0)]},
        {"line_id": "L-e", "item_code": "MAS.BLOCK", "floor": "1F", "family": 0.2, "walls": [
            _w("S-5", "BLACK", "HELD", None, "D2 1.7600 ON_HELD_WALL")]},
        {"line_id": "L-p", "item_code": "ARCH.WALL_PANEL", "floor": "GF", "family": 0.2, "walls": [
            _w("S-1", "BLACK", "VERIFIED", 20.0, "D1 2.2000 DEDUCTED")]}]}
    register = {"entries": [
        {"item_code": "MAS.BLOCK", "floor": "GF", "element_id": "S-1",
         "rule_result": {"formula": "[5.0000 x 4.0000 + 0.5500 x 4.0000] - [D1 2.2000]"}},
        {"item_code": "MAS.BLOCK", "floor": "GF", "element_id": "S-2",
         "rule_result": {"formula": "[3.5000 x 3.5000 + 0.2000 x 3.2000] - [X1 3.5000]"}},
        {"item_code": "MAS.BLOCK", "floor": "GF", "element_id": "S-3",
         "rule_result": {"formula": "[2.0000 x 3.3000] - [X2 1.2000]"}},
        {"item_code": "MAS.BLOCK", "floor": "1F", "element_id": "S-5",
         "rule_result": {"formula": "[0.1000 x 3.0000] - [D2 1.7600]"}}]}
    census = [_op("D1", "DOOR", "1.00", "2.20", "0.00", "ASSUMED"), _op("X1", "WINDOW", "2.50", "1.40", "1.20"),
              _op("X2", "WINDOW", "1.20", "2.10", "1.00"), _op("D2", "DOOR", "0.80", "2.20", "0.00", "ASSUMED"),
              _op("G1", "GATE", "", "", "", "HELD")]
    mortar = [{"part_line_id_v3026": "L-b", "mortar_installed_m3": "0.295", "area_m2 (established)": "20.0000",
               "mortar_or_adhesive_status": "ASSUMED — OWNER-APPROVED"},
              {"part_line_id_v3026": "L-d", "mortar_installed_m3": "0.0885", "area_m2 (established)": "8.0000",
               "mortar_or_adhesive_status": "ASSUMED — OWNER-APPROVED"},
              {"part_line_id_v3026": "(parent: held)", "mortar_installed_m3": "", "area_m2 (established)": "",
               "mortar_or_adhesive_status": "HELD"}]
    return index, fill, register, census, SCHED, mortar


def run(v=None):
    return T.build_from(*(v or villa()))


def _mat(led, lid, item):
    return next(m for m in led["block_materials"] if m["line_id"] == lid and m["item"] == item)


def _lin(led, oid):
    return next(r for r in led["lintels"] if r["opening_id"] == oid)


# ------------------------------------------------------------------ hand values

def test_hand_black_blocks_and_mortar():
    led = run()
    # r2 (R-T453-5): S-1 hosts the REQUIRED RC lintel of D1, face (1.00 + 2 x 0.40) x 0.20 = 0.36 m2 of concrete:
    # material base 20.00 - 0.36 = 19.64 m2 (r1 counted 20.00, the lintel face twice: Checker F-C-T453-1)
    b = _mat(led, "L-b", "BLOCK_COUNT")
    assert b["status"] == "COMPUTED" and b["label"] == "VERIFIED-NET"
    assert b["net_m2"] == 20.0 and b["material_base_m2"] == 19.64
    assert b["theoretical_count"] == 245.5                      # 19.64 m2 x 12.5
    assert b["procurement_count"] is None and b["breakage"] == "HELD"
    m = _mat(led, "L-b", "LAYING_MATERIAL")
    assert m["status"] == "COMPUTED" and m["label"] == "PROVISIONAL-NET"   # owner-provisional joint, VERIFIED area
    # T-367 0.295 m3 on 20.00 m2 = 0.01475 m3/m2 x 19.64 = 0.28969 m3; x 8 = 2.31752 bags; x 1.1 = 0.318659 m3
    assert m["mortar_installed_m3"] == 0.28969 and m["cement_bags"] == 2.31752 and m["sand_m3_loose"] == 0.318659
    assert led["mortar"]["black_0_20_provisional_net"] == {"m3": 0.28969, "cement_bags": 2.31752,
                                                           "sand_m3_loose": 0.318659, "lines": 1}


def test_hand_white_glue_and_held_project_group():
    led = run()
    # r2 (R-T453-5): L-c = S-2 + S-3 = 16.00 m2. S-2 hosts X1 REQUIRED, face (2.50 + 0.80) x 0.30 = 0.99 m2 -> base
    # 15.01; S-3 hosts X2 FLAGGED (at most 1), face (1.20 + 0.80) x 0.20 = 0.40 m2 -> range 14.61 .. 15.01 m2
    g = _mat(led, "L-c", "LAYING_MATERIAL")
    assert g["status"] == "RANGE" and g["label"] == "RANGE-NET" and g["consumption_kg"] is None
    assert g["net_m2"] == 16.0 and g["lintel_deduction_m2"] == 0.99 and g["material_base_m2"] == 15.01
    assert g["material_base_range_m2"] == [14.61, 15.01]
    assert g["consumption_kg_range"] == [65.745, 67.545]                      # 14.61 x 4.5 ; 15.01 x 4.5
    assert g["bags_25kg_net_range"] == [2.6298, 2.7018]
    c = _mat(led, "L-c", "BLOCK_COUNT")
    assert c["status"] == "HELD" and c["alternatives_beside"] == {"62.5x25": 96.064, "60x20": 125.083333,
                                                                  "on_m2": 15.01}
    grp = led["glue_groups"]["PROJECT"]
    assert grp["status"] == "HELD" and grp["bags_to_buy"] is None             # held parents: never 0, never 3
    assert set(grp["held_lines"]) == {"L-a", "L-c", "L-e"} and grp["known_kg"] == 0.0
    assert led["glue_groups"]["known_part_by_label"]["RANGE-NET"]["kg_range"] == [65.745, 67.545]


def test_hand_lintels():
    led = run()
    d1 = _lin(led, "D1")       # 1.00 m door, head 2.20, pieces 4.00: margin 1.80 >= 0.20 + 0.06
    assert d1["decision"] == "REQUIRED" and d1["schedule_row"] == "L1"
    assert d1["length_m"] == 1.8 and d1["concrete_m3"] == 0.072 and d1["formwork_m2"] == 0.92
    assert d1["rebar_kg"] == "HELD" and "precast_alternative_beside" not in d1      # black wall: no atab
    assert d1["face_m2"] == 0.36 and d1["floor_buildup_m"] == 0.06 and d1["floor_buildup_status"] == "STAND-IN"
    assert d1["spare_margin_m"] == 1.54                                       # 1.80 - (0.20 + 0.06)
    x1 = _lin(led, "X1")       # 2.50 m window, head 2.60, pieces 3.50 / 3.20: margin 0.60 >= 0.30 + 0.06
    assert x1["decision"] == "REQUIRED" and x1["schedule_row"] == "L3" and x1["length_m"] == 3.3
    assert x1["concrete_m3"] == 0.198 and x1["formwork_m2"] == 2.48       # 0.2x0.3x3.3 ; 2x0.3x3.3 + 0.2x2.5
    assert x1["precast_alternative_beside"]["piece_m"] == 4.0 and "F-T453-1" in x1["conflict"]
    s = led["lintel_reconciliation"]["summary"]
    assert s["REQUIRED"] == 2 and s["required_concrete_m3"] == 0.27


# ------------------------------------------------------------------ adverse

def test_fifteen_cm_black_count_and_mortar_held_never_zero():
    led = run()
    for item in ("BLOCK_COUNT", "LAYING_MATERIAL"):
        m = _mat(led, "L-d", item)
        assert m["status"] == "HELD" and m.get("theoretical_count") is None and m.get("cement_bags") is None
    assert _mat(led, "L-d", "LAYING_MATERIAL")["beside_t367_40x20"]["mortar_installed_m3"] == 0.0885


def test_held_line_material_is_held_not_zero():
    led = run()
    for item in ("BLOCK_COUNT", "LAYING_MATERIAL"):
        m = _mat(led, "L-a", item)
        assert m["status"] == "HELD" and m["net_m2"] is None


def test_beam_soffit_at_head_flagged():
    led = run()
    x2 = _lin(led, "X2")      # head 3.10 under a 3.30 piece: 0.20 < D 0.20 + 0.06 bed
    assert x2["decision"] == "FLAGGED" and x2.get("concrete_m3") is None
    v = villa()
    v[3][2]["HEIGHT_M"] = "2.40"     # head 3.40 above the 3.30 soffit: the beam serves
    assert _lin(run(v), "X2")["decision"] == "FLAGGED"


def test_opening_on_held_wall_and_unknown_head_held():
    led = run()
    assert _lin(led, "D2")["decision"] == "HELD"
    assert {"opening_id": "G1", "kind": "GATE"}.items() <= led["lintel_reconciliation"][
        "census_openings_not_in_a_masonry_wall"][0].items()
    v = villa()
    v[3][0]["HEIGHT_STATUS"] = "HELD"
    assert _lin(run(v), "D1")["decision"] == "HELD"


def test_width_bands_gap_above_and_unit_error():
    v = villa()
    v[3][0]["WIDTH_M"] = "1.005"      # between the printed 100 and 101 cm bands
    assert _lin(run(v), "D1")["decision"] == "FLAGGED"
    v[3][0]["WIDTH_M"] = "3.20"       # above the last band of this schedule
    assert _lin(run(v), "D1")["decision"] == "FLAGGED"
    v[3][0]["WIDTH_M"] = "1000"       # millimetres passed as metres
    with pytest.raises(T.LedgerError, match="width"):
        run(v)
    v[3][0]["WIDTH_M"] = ""
    assert _lin(run(v), "D1")["decision"] == "HELD"


def test_reconciliation_refuses_a_line_that_does_not_close():
    v = villa()
    v[0]["lines"][2]["measured_net"] = 16.5
    with pytest.raises(T.LedgerError, match="L-c"):
        run(v)
    v = villa()
    v[1]["lines"][0]["walls"].append(_w("S-7", "BLACK", "DRAWING-CONFIRMED", 3.0))
    with pytest.raises(T.LedgerError, match="no split line"):
        run(v)


def test_held_line_with_a_figure_and_released_line_without_refused():
    v = villa()
    v[0]["lines"][0]["measured_net"] = 0.0
    with pytest.raises(T.LedgerError, match="HELD line"):
        run(v)
    v = villa()
    v[0]["lines"][1]["measured_net"] = None
    with pytest.raises(T.LedgerError, match="never 0"):
        run(v)


def test_opening_hosted_twice_refused():
    v = villa()
    v[1]["lines"][0]["walls"][1]["openings"] = "X1 3.5000 DEDUCTED; D1 2.2000 DEDUCTED"
    with pytest.raises(T.LedgerError, match="hosted twice"):
        run(v)


def test_mortar_area_mismatch_refused():
    v = villa()
    v[5][0]["area_m2 (established)"] = "19.0000"
    with pytest.raises(T.LedgerError, match="T-367"):
        run(v)


def test_order_invariance():
    base = json.dumps(run(), sort_keys=True)
    for seed in range(3):
        v = copy.deepcopy(villa())
        rnd = random.Random(seed)
        rnd.shuffle(v[0]["lines"])
        rnd.shuffle(v[3])
        rnd.shuffle(v[5])
        assert json.dumps(run(v), sort_keys=True) == base


def test_verified_net_only_from_verified_lines():
    led = run()
    for m in led["block_materials"]:
        if m["label"] == "VERIFIED-NET":
            assert m["source_label"] == "VERIFIED-NET"
    for r in led["lintels"]:
        assert r.get("label") in (None, "PROVISIONAL-NET")
    for m in led["block_materials"]:
        if m.get("lintel_held_faces"):
            assert m["label"] in ("RANGE-NET", "HELD")


# ------------------------------------------------------------------ committed ledger

def test_committed_ledger_rebuilds_byte_identically(tmp_path):
    led = T.build()
    T.write(led, tmp_path)
    for name in ("MATERIAL_LEDGER_T453.json", "BLOCK_MATERIALS_T453.csv", "LINTELS_T453.csv"):
        assert (tmp_path / name).read_bytes() == (ROOT / "research/agents_t453/out" / name).read_bytes(), name
    assert led["block_totals"]["black_0_20_by_label"]["VERIFIED-NET"]["theoretical_blocks"] == 1346.55
    assert led["glue_groups"]["PROJECT"]["status"] == "HELD"
    # r2 Checker hand case: L-2fdc 1F white 0.20 VERIFIED 101.976 m2 - W14 0.975 - W15 0.470 - W18 0.260 = 100.271 m2,
    # HELD W16 / W19 / W20 / W24 0 .. 1.50 m2: glue 444.4695 .. 451.2195 kg (not VERIFIED-NET)
    g = next(m for m in led["block_materials"] if m["line_id"] == "L-2fdc0f971a94348ec855"
             and m["item"] == "LAYING_MATERIAL")
    assert g["lintel_deduction_m2"] == 1.705 and g["consumption_kg_range"] == [444.4695, 451.2195]
    assert g["label"] == "RANGE-NET"


# ------------------------------------------------------------------ r2: R-T453-5 lintel faces leave the material base

def test_required_lintel_in_verified_wall_reduces_base_not_area():
    """normal: an RC lintel inside a VERIFIED panel leaves the material base by a named row; the contract area of the
    MAS.BLOCK line (net_m2) is untouched and the label stays VERIFIED-NET."""
    led = run()
    b = _mat(led, "L-b", "BLOCK_COUNT")
    assert b["contract_net_m2"] == 20.0 and b["net_m2"] == 20.0
    assert [(x["opening_id"], x["face_m2"], x["length_m"], x["depth_m"]) for x in b["lintel_deductions"]] == [
        ("D1", 0.36, 1.8, 0.2)]
    assert b["base_state"] == "EXACT" and b["lintel_held_faces"] == []
    assert led["source_lines"][[x["line_id"] for x in led["source_lines"]].index("L-b")]["net_m2"] == 20.0
    f = led["lintel_reconciliation"]["faces_on_host_lines"]
    assert f["L-b"] == {"required_m2": 0.36, "required": ["D1"], "held_max_m2": 0.0, "held": []}
    # no lintel in the panel: base = net (L-d, 0.15 black, still HELD for its module)
    assert _mat(led, "L-d", "BLOCK_COUNT")["material_base_m2"] == 8.0


def test_held_lintel_is_a_named_range_never_silent_never_zero():
    """adverse: a HELD lintel (head unknown) on a host line is neither deducted silently nor dropped (0): the material
    becomes a RANGE 0 .. face and a VERIFIED source line loses its VERIFIED-NET label."""
    v = villa()
    v[3][0]["HEIGHT_STATUS"] = "HELD"            # D1 head unknown -> lintel HELD (at most 1) on VERIFIED L-b
    led = run(v)
    assert _lin(led, "D1")["decision"] == "HELD" and _lin(led, "D1")["face_max_m2"] == 0.36
    b = _mat(led, "L-b", "BLOCK_COUNT")
    assert b["source_label"] == "VERIFIED-NET" and b["label"] == "RANGE-NET" and b["status"] == "RANGE"
    assert b["material_base_m2"] == 20.0 and b["material_base_range_m2"] == [19.64, 20.0]
    assert b["theoretical_count"] is None and b["theoretical_count_range"] == [245.5, 250.0]
    m = _mat(led, "L-b", "LAYING_MATERIAL")
    assert m["cement_bags"] is None and m["cement_bags_range"] == [2.31752, 2.36]
    assert led["mortar"]["range_net"]["lines"] == ["L-b"]
    assert "VERIFIED-NET" not in led["block_totals"]["black_0_20_by_label"]


def test_unbounded_lintel_face_holds_the_material():
    """adverse: a HELD lintel whose face cannot be bounded (width unknown) holds the material, upper end stated."""
    v = villa()
    v[3][0]["WIDTH_M"] = ""                      # D1 width unknown: no band, no face
    led = run(v)
    b = _mat(led, "L-b", "BLOCK_COUNT")
    assert b["status"] == "HELD" and b["label"] == "HELD" and b["material_base_range_m2"] == [None, 20.0]
    assert "D1" in b["why"]
    assert _mat(led, "L-b", "LAYING_MATERIAL")["status"] == "HELD"
    assert led["lintel_reconciliation"]["faces_on_host_lines"]["L-b"]["held_max_m2"] is None


def test_lintel_on_held_wall_deducts_nothing_and_faces_above_net_refused():
    led = run()
    assert [x["opening_id"] for x in led["lintel_reconciliation"]["faces_on_held_hosts"]] == ["D2"]
    v = villa()
    v[1]["lines"][0]["walls"][0]["carried"] = 0.3     # S-1 0.30 m2 cannot hold a 0.36 m2 lintel face
    v[0]["lines"][1]["measured_net"] = 0.3
    v[5][0]["area_m2 (established)"] = "0.3000"
    with pytest.raises(T.LedgerError, match="exceed"):
        run(v)
