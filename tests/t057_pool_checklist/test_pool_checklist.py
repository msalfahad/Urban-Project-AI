"""T-057: POOL_CHECKLIST_V1 (engine.source.pool_checklist) - pool pump room, main manholes, pool type.

Rule: owner answer Q-19 (2026-10-19): whenever a villa has a pool, check for the pool pump room and for where the
house's main manholes are; UP-QTY-STATUS-001 (an unchecked or missing item is a HELD record, never absent).
Hand truth, written from the meaning of each label (Kuwait villa vocabulary) and hand geometry, not from engine
output. Synthetic villas only (no client drawing, no project layer or room names).
"""

from __future__ import annotations

import math

import ezdxf
import pytest

from engine.source import pool_checklist as PC


def T(text, sheet="A-101", x=0.0, y=0.0, handle=None):
    return {"text": text, "sheet": sheet, "x": x, "y": y, "handle": handle}


def B(name, sheet="A-101", x=0.0, y=0.0):
    return {"name": name, "sheet": sheet, "x": x, "y": y}


def rec(result, item):
    rs = [r for r in result["records"] if r["item"] == item]
    assert len(rs) == 1, item
    return rs[0]


# ---- 1. pool + labelled pump room ---------------------------------------------------------------------------------

def test_pool_with_english_pump_room_label_found():
    r = PC.check([T("SWIMMING POOL", "A-100"), T("PUMP ROOM", "A-100", 4, 2), T("BEDROOM 1")])
    assert r["pool"]["status"] == "DRAWN" and r["pool"]["sheets"] == ["A-100"]
    p = rec(r, "POOL_PUMP_ROOM")
    assert p["status"] == "FOUND" and p["reason"] is None
    assert [(f["value"], f["sheet"], f["kind"]) for f in p["found"]] == [("PUMP ROOM", "A-100", "LABEL")]
    assert p["found"][0]["pool_specific"] is False         # a pump room with no pool word: found, flagged generic


def test_pool_with_arabic_pump_room_label_found():
    r = PC.check([T("حمام سباحة", "م-1"), T("غرفة مضخات المسبح", "م-1")])
    assert r["pool"]["status"] == "DRAWN"
    p = rec(r, "POOL_PUMP_ROOM")
    assert p["status"] == "FOUND" and p["found"][0]["pool_specific"] is True


@pytest.mark.parametrize("label", ["POOL PUMP ROOM", "Pool plant room", "POOL FILTER ROOM", "FILTRATION ROOM",
                                   "PUMP HOUSE", "غرفة مضخات", "غرفه مضخة", "غرفة فلاتر المسبح",
                                   "غرفة معدات حمام السباحة"])
def test_pump_room_vocabulary(label):
    r = PC.check([T("POOL"), T(label)])
    assert rec(r, "POOL_PUMP_ROOM")["status"] == "FOUND", label


@pytest.mark.parametrize("label", ["ELECTRICAL ROOM", "غرفة كهرباء", "MECH. ROOM", "STORE", "PUMPKIN STORE",
                                   "LAUNDRY"])
def test_not_a_pump_room(label):
    r = PC.check([T("SWIMMING POOL"), T(label)])
    p = rec(r, "POOL_PUMP_ROOM")
    assert p["status"] == "HELD" and p["reason"] == "POOL_PUMP_ROOM_NOT_FOUND", label


def test_pool_pump_room_label_alone_is_not_a_pool():
    # ROOM_VOCAB_V2: 'POOL PUMP ROOM' types as PLANT, not POOL - the plant room alone does not make a pool
    r = PC.check([T("POOL PUMP ROOM"), T("MH1")])
    assert r["pool"]["status"] == "NOT_DRAWN" and r["records"] == []


# ---- 2. pool + pump block only ------------------------------------------------------------------------------------

@pytest.mark.parametrize("name", ["POOL_PUMP-01", "PUMP", "poolpump", "Swim-Filter", "pump_set_2"])
def test_pump_block_only_found(name):
    r = PC.check([T("بركة سباحة", "S-1")], blocks=[B(name, "S-1", 7, 3)])
    p = rec(r, "POOL_PUMP_ROOM")
    assert p["status"] == "FOUND" and [f["kind"] for f in p["found"]] == ["BLOCK"], name
    assert p["found"][0]["sheet"] == "S-1"


@pytest.mark.parametrize("name", ["DOOR_90", "PUMPKIN", "TREE-01", "WC"])
def test_not_a_pump_block(name):
    r = PC.check([T("POOL")], blocks=[B(name)])
    assert rec(r, "POOL_PUMP_ROOM")["status"] == "HELD", name


# ---- 3. pool with neither: every item HELD / NOT_ESTABLISHED, never absent -----------------------------------------

def test_pool_with_nothing_else_is_held_not_absent():
    r = PC.check([T("SWIMMING POOL"), T("MAJLIS"), T("KITCHEN")])
    assert [x["item"] for x in r["records"]] == ["POOL_PUMP_ROOM", "MAIN_MANHOLES", "POOL_TYPE"]
    assert rec(r, "POOL_PUMP_ROOM")["reason"] == "POOL_PUMP_ROOM_NOT_FOUND"
    m = rec(r, "MAIN_MANHOLES")
    assert m["status"] == "HELD" and m["reason"] == "MAIN_MANHOLES_NOT_FOUND"
    t = rec(r, "POOL_TYPE")
    assert t["status"] == "NOT_ESTABLISHED" and t["value"] is None     # never a default type
    rows = PC.census_rows(r)
    assert [(x["item"], x["status"], x["reason"]) for x in rows] == [
        ("POOL_PUMP_ROOM", "HELD", "POOL_PUMP_ROOM_NOT_FOUND"),
        ("MAIN_MANHOLES", "HELD", "MAIN_MANHOLES_NOT_FOUND"),
        ("POOL_TYPE", "NOT_ESTABLISHED", "POOL_TYPE_NOT_DRAWN")]


def test_route_pool_element_alone_makes_a_pool():
    r = PC.check([], pool_elements=[{"sheet": "S-04", "id": "PW1", "kind": "POOL_WALL"}])
    assert r["pool"]["status"] == "DRAWN" and r["pool"]["sheets"] == ["S-04"]
    assert len(r["records"]) == 3


# ---- 4. villa with no pool: no records ----------------------------------------------------------------------------

def test_no_pool_no_records():
    r = PC.check([T("PUMP ROOM"), T("MAIN MH"), T("حمام"), T("BALANCE TANK")], blocks=[B("MANHOLE")])
    assert r["pool"]["status"] == "NOT_DRAWN" and r["records"] == [] and PC.census_rows(r) == []


def test_bathroom_is_not_a_pool():
    r = PC.check([T("حمام ماستر"), T("POOL TABLE AREA" * 3)])       # long text is not a tag
    assert r["pool"]["status"] == "NOT_DRAWN"


# ---- 5. manholes ---------------------------------------------------------------------------------------------------

def test_main_manholes_found_others_kept():
    r = PC.check([T("POOL"), T("MH1", "SITE", 1, 1), T("M.H-2", "SITE", 2, 1), T("MAIN MH", "SITE", 9, 0),
                  T("غرفة تفتيش رئيسية", "SITE", 9, 5), T("ROOM H"), T("MECH")])
    m = rec(r, "MAIN_MANHOLES")
    assert m["status"] == "FOUND"
    assert sorted(f["value"] for f in m["found"]) == sorted(["MAIN MH", "غرفة تفتيش رئيسية"])
    assert sorted(f["value"] for f in m["other_manholes"]) == ["M.H-2", "MH1"]


def test_manholes_without_main_are_listed_none_picked():
    r = PC.check([T("POOL"), T("MH1"), T("MANHOLE 2")], blocks=[B("IC_CHAMBER")])
    m = rec(r, "MAIN_MANHOLES")
    assert m["status"] == "HELD" and m["reason"] == "MAIN_MANHOLE_NOT_IDENTIFIED" and m["found"] == []
    assert sorted(f["value"] for f in m["other_manholes"]) == ["IC_CHAMBER", "MANHOLE 2", "MH1"]


def test_main_manhole_block():
    r = PC.check([T("POOL")], blocks=[B("MAIN-MANHOLE", "P-01")])
    m = rec(r, "MAIN_MANHOLES")
    assert m["status"] == "FOUND" and m["found"][0]["kind"] == "BLOCK"


def test_long_note_is_a_note_not_a_find():
    note = "ALL MANHOLES SHALL BE OF PRECAST CONCRETE WITH HEAVY DUTY COVERS"
    r = PC.check([T("POOL"), T(note)])
    m = rec(r, "MAIN_MANHOLES")
    assert m["reason"] == "MAIN_MANHOLES_NOT_FOUND" and len(m["notes"]) == 1
    assert PC.census_rows(r)[1]["notes"] == 1


# ---- 6. pool type -------------------------------------------------------------------------------------------------

@pytest.mark.parametrize("labels,status,value,reason", [
    (["BALANCE TANK"], "FOUND", "OVERFLOW", None),
    (["OVERFLOW CHANNEL"], "FOUND", "OVERFLOW", None),
    (["خزان موازنة"], "FOUND", "OVERFLOW", None),
    (["SKIMMER"], "FOUND", "NORMAL", None),
    (["SKIMMER", "OVER-FLOW GRATING"], "HELD", None, "POOL_TYPE_CONFLICT"),
    ([], "NOT_ESTABLISHED", None, "POOL_TYPE_NOT_DRAWN"),
])
def test_pool_type(labels, status, value, reason):
    r = PC.check([T("SWIMMING POOL")] + [T(x) for x in labels])
    t = rec(r, "POOL_TYPE")
    assert (t["status"], t["value"], t["reason"]) == (status, value, reason)


# ---- 7. DXF intake: rotated, mirrored, nested, mm and m, paper space ----------------------------------------------

def _villa(path, scale, unit):
    doc = ezdxf.new("R2018")
    doc.header["$INSUNITS"] = unit
    msp = doc.modelspace()
    s = scale
    msp.add_text("SWIMMING POOL", dxfattribs={"insert": (12 * s, 3 * s), "height": 0.3 * s, "rotation": 37})
    t = msp.add_text("مسبح", dxfattribs={"insert": (13 * s, 2 * s), "height": 0.3 * s})
    t.dxf.text_generation_flag = 2                                   # backward (mirrored) text: same string
    pump = doc.blocks.new("RM_TAG")                                  # a room tag block, label inside
    pump.add_text("PUMP ROOM", dxfattribs={"insert": (2 * s, 1 * s), "height": 0.2 * s})
    msp.add_blockref("RM_TAG", (10 * s, 5 * s), dxfattribs={"rotation": 37, "xscale": -1})
    inner = doc.blocks.new("MH_SYM")
    inner.add_circle((0, 0), 0.3 * s)
    outer = doc.blocks.new("SITE_DRAIN")
    outer.add_blockref("MH_SYM", (1 * s, 0))
    outer.add_mtext("{\\fArial|b1;MAIN} MH", dxfattribs={"insert": (1 * s, 1 * s), "char_height": 0.2 * s})
    msp.add_blockref("SITE_DRAIN", (0, 20 * s))
    ps = doc.layouts.new("SHEET-02")
    ps.add_text("SKIMMER", dxfattribs={"insert": (5, 5), "height": 2.5})
    doc.saveas(path)
    return ezdxf.readfile(path)


@pytest.mark.parametrize("scale,unit", [(1.0, 6), (1000.0, 4)])     # metres and millimetres
def test_dxf_villa_rotated_mirrored_nested(tmp_path, scale, unit):
    doc = _villa(str(tmp_path / f"v{unit}.dxf"), scale, unit)
    texts, blocks = PC.items_from_dxf(doc)
    r = PC.check(texts, blocks)
    assert r["pool"]["status"] == "DRAWN" and len(r["pool"]["evidence"]) == 2
    p = rec(r, "POOL_PUMP_ROOM")
    assert p["status"] == "FOUND" and p["found"][0]["value"] == "PUMP ROOM" and p["found"][0]["sheet"] == "Model"
    # hand position: insert (10, 5) + R(37 deg) . (-2, 1)  (x mirrored, then rotated), times the drawing scale
    c, s_ = math.cos(math.radians(37)), math.sin(math.radians(37))
    hx, hy = 10 + (-2 * c - 1 * s_), 5 + (-2 * s_ + 1 * c)
    assert p["found"][0]["x"] == pytest.approx(hx * scale, abs=1e-6 * scale)
    assert p["found"][0]["y"] == pytest.approx(hy * scale, abs=1e-6 * scale)
    m = rec(r, "MAIN_MANHOLES")
    assert m["status"] == "FOUND" and [f["value"] for f in m["found"]] == ["MAIN MH"]
    assert [f["value"] for f in m["other_manholes"]] == ["MH_SYM"]          # nested symbol block kept, not main
    t = rec(r, "POOL_TYPE")
    assert t["value"] == "NORMAL" and t["found"][0]["sheet"] == "SHEET-02"


def test_dxf_sheet_of_callback(tmp_path):
    doc = _villa(str(tmp_path / "v.dxf"), 1.0, 6)
    texts, blocks = PC.items_from_dxf(doc, sheet_of=lambda lay, x, y: f"{lay}:{'N' if y >= 15 else 'S'}")
    r = PC.check(texts, blocks)
    assert rec(r, "MAIN_MANHOLES")["found"][0]["sheet"] == "Model:N"
    assert rec(r, "POOL_PUMP_ROOM")["found"][0]["sheet"] == "Model:S"


def test_arabic_presentation_forms_and_arabic_digits():
    # CAD exports sometimes store Arabic as presentation forms (NFKC folds them) and digits as Arabic-Indic
    r = PC.check([T("ﻣﺴﺒﺢ"), T("ﻏﺮﻓﺔ ﻣﻀﺨﺎﺕ"), T("منهول ١")])
    assert r["pool"]["status"] == "DRAWN"
    assert rec(r, "POOL_PUMP_ROOM")["status"] == "FOUND"
    assert rec(r, "MAIN_MANHOLES")["reason"] == "MAIN_MANHOLE_NOT_IDENTIFIED"


def test_empty_and_latin_shx_codes_match_nothing():
    # undecoded Arabic SHX (Latin keyboard codes, T-047) types nothing: no pool is invented
    r = PC.check([T(""), T("   "), T("lsfp")], blocks=[B("")])
    assert r["pool"]["status"] == "NOT_DRAWN" and r["records"] == []


def test_dxf_minus_z_insert_and_text_positions_are_world(tmp_path):
    # an entity mirrored by its extrusion (0, 0, -1) stores OCS points: OCS x (3) is world x -3 (hand)
    doc = ezdxf.new("R2018")
    msp = doc.modelspace()
    doc.blocks.new("MANHOLE").add_circle((0, 0), 0.3)
    msp.add_blockref("MANHOLE", (3, 4), dxfattribs={"extrusion": (0, 0, -1)})
    msp.add_text("POOL", dxfattribs={"insert": (5, 1), "height": 0.3, "extrusion": (0, 0, -1)})
    texts, blocks = PC.items_from_dxf(doc)
    assert (blocks[0]["x"], blocks[0]["y"]) == pytest.approx((-3, 4))
    assert (texts[0]["x"], texts[0]["y"]) == pytest.approx((-5, 1))
    r = PC.check(texts, blocks)
    assert rec(r, "MAIN_MANHOLES")["reason"] == "MAIN_MANHOLE_NOT_IDENTIFIED"
