"""T-670: held B9 material lines restated through the merged ARCH_TAKEOFF_V3.0.59 producer (R-T670-1, research only).

Hand fixture (not the development villa): a 0.15 m black block wall 6.00 x 3.00 m with one 1.20 x 1.00 m window,
net 18.00 - 1.20 = 16.80 m2; its RC lintel (1.20 + 2 x 0.40) x 0.20 = 0.40 m2 face, 0.15 x 0.40 = 0.060 m3 concrete;
material base 16.40 m2 -> 16.40 x 12.5 = 205.0 units; joint 0.15 x (1 - 0.39 x 0.19 / 0.08) = 0.0110625 m3/m2 ->
16.40 x 0.0110625 = 0.181425 m3. A 0.20 m AAC wall 5.00 x 3.00 = 15.00 m2 x 4.5 = 67.5 kg glue.
"""
import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
_spec = importlib.util.spec_from_file_location("t670", ROOT / "research/agents_t670/t670_masonry_materials.py")
T = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(T)

JOINT = {"module_m": [0.40, 0.20], "unit_m": [0.39, 0.19], "joint_mm": 10}


def rb(mods):
    return {"method": "COMPANY_RULEBOOK_V1", "version": "x", "digest": "d" * 64, "records": {
        "UPC-BLACK-BLOCK-001": {"status": "OWNER_CONFIRMED",
                                "params": {"blocks_per_m2_40x20_module": 12.5, "confirmed_modules_m": mods}},
        "UPC-AAC-GLUE-001": {"status": "OWNER_CONFIRMED",
                             "params": {"kg_per_m2_by_thickness_m": {"0.15": 3.5, "0.20": 4.5}, "bag_kg": 25.0}},
        "UPC-BLACK-MORTAR-001": {"status": "OWNER_CONFIRMED",
                                 "params": {"cement_bags_per_m3": 8.0, "loose_sand_m3_per_m3": 1.1}}}}


OLD = rb({"0.20": [0.4, 0.2]})
NEW = rb({"0.15": [0.4, 0.2], "0.20": [0.4, 0.2]})


def ln(lid, code, eid, cls, net=None, lo=None, hi=None, unit="m2"):
    return {"line_id": lid, "item_code": code, "element_id": eid, "class": cls, "measured_net": net,
            "held_low": lo, "held_high": hi, "unit": unit, "binding": None, "unbound_records": []}


HB = "XX-WALLS:walls t=0.15#BLOCKWORK:VERIFIED_BLACK"
HW = "XX-WALLS:walls t=0.20#BLOCKWORK:VERIFIED_WHITE"
HH = "YY-WALLS:walls t=0.20"


def villa(black_state=("HELD", None), lintel_cls="RELEASED"):
    lines = [ln("L-hb", "MAS.BLOCK", HB, "RELEASED", 16.8), ln("L-hw", "MAS.BLOCK", HW, "RELEASED", 15.0),
             ln("L-hh", "MAS.BLOCK", HH, "HELD"),
             ln("L-li", "STR.CONC.LINTEL", "LINTEL:D-01", lintel_cls, 0.06 if lintel_cls == "RELEASED" else None,
                unit="m3")]
    v = black_state[1] if black_state[0] == "VALUE" else None
    lines += [ln("L-ub", "MAS.UNITS.BLACK", "MATERIAL:" + HB, "RELEASED" if v else "HELD", v, unit="pcs"),
              ln("L-mb", "MAS.MORTAR.BLACK", "MATERIAL:" + HB, "HELD", unit="m3"),
              ln("L-gw", "MAS.GLUE.AAC", "MATERIAL:" + HW, "RELEASED", 67.5, unit="kg"),
              ln("L-uw", "MAS.UNITS.WHITE", "MATERIAL:" + HW, "HELD", unit="pcs")]
    for c, u in (("MAS.UNITS.BLACK", "pcs"), ("MAS.MORTAR.BLACK", "m3"), ("MAS.GLUE.AAC", "kg"), ("MAS.UNITS.WHITE", "pcs")):
        lines.append(ln("L-h-" + c, c, "MATERIAL:" + HH, "HELD", unit=u))
    return lines


FACES = {"L-hb": {"required": [{"opening_id": "D-01", "face_m2": 0.40}], "held": []}}
CAUSES = {"L-hh": "MASONRY_HEIGHT_NOT_IN_THE_DRAWING (fixture)"}


def rows_by_id(rows):
    return {r["material_line_id"]: r for r in rows}


def test_normal_015_black_restated_by_hand():
    r = rows_by_id(T.statement(villa(), FACES, OLD, NEW, JOINT, CAUSES))
    assert r["L-ub"]["before"] == ["HELD", None] and r["L-ub"]["after"] == ["VALUE", 205.0]
    assert r["L-mb"]["after"] == ["VALUE", 0.181425]
    assert r["L-ub"]["material_base_m2"] == 16.4 and r["L-ub"]["lintels"][0]["lintel_line_id"] == "L-li"
    assert r["L-gw"]["after"] == ["VALUE", 67.5] and not r["L-gw"]["changed"]
    # white units: HELD with a cause, the two supplier faces BESIDE only
    assert r["L-uw"]["after"] == ["HELD", None] and r["L-uw"]["cause"]
    assert r["L-uw"]["beside_aac_units"] == {"62.5x25": [96.0, 96.0], "60x20": [125.0, 125.0]}
    # lintel face and lintel concrete are one piece: face x t = lintel m3
    assert [c["face_x_t_m3"] for c in T.lintel_face_check(list(r.values()))] == [0.06]


def test_held_host_stays_blank_with_its_cause_never_zero():
    r = rows_by_id(T.statement(villa(), FACES, OLD, NEW, JOINT, CAUSES))
    for c in ("MAS.UNITS.BLACK", "MAS.MORTAR.BLACK", "MAS.GLUE.AAC", "MAS.UNITS.WHITE"):
        x = r["L-h-" + c]
        assert x["after"] == ["HELD", None] and x["cause"] == CAUSES["L-hh"]
    t = T.totals(list(r.values()), "after")
    assert t["MAS.UNITS.BLACK"]["blank_n"] == 1 and t["MAS.UNITS.BLACK"]["valued"] == 205.0


def test_adverse_held_lintel_gives_a_named_range():
    faces = {"L-hb": {"required": [], "held": [{"opening_id": "D-01", "face_max_m2": 0.40, "why": "head unknown"}]}}
    r = rows_by_id(T.statement(villa(lintel_cls="HELD"), faces, OLD, NEW, JOINT, CAUSES))
    assert r["L-ub"]["after"] == ["RANGE", [205.0, 210.0]]
    assert r["L-mb"]["after"] == ["RANGE", [0.181425, 0.185850]]


def test_adverse_unconfirmed_thickness_is_not_borrowed():
    lines = [dict(x, element_id=x["element_id"].replace("t=0.15", "t=0.25")) for x in villa()]
    r = rows_by_id(T.statement(lines, FACES, OLD, NEW, JOINT, CAUSES))
    assert r["L-ub"]["after"] == ["HELD", None] and "0.25" in r["L-ub"]["cause"]


def test_adverse_reproduction_mismatch_stops():
    with pytest.raises(T.T670Error, match="does not reproduce"):
        T.statement(villa(black_state=("VALUE", 210.0)), FACES, OLD, NEW, JOINT, CAUSES)


def test_adverse_millimetre_face_refused():
    faces = {"L-hb": {"required": [{"opening_id": "D-01", "face_m2": 400.0}], "held": []}}
    with pytest.raises(Exception, match="exceed"):
        T.statement(villa(), faces, OLD, NEW, JOINT, CAUSES)


def test_adverse_face_on_held_host_refused():
    faces = {"L-hh": {"required": [{"opening_id": "D-01", "face_m2": 0.40}], "held": []}}
    with pytest.raises(T.T670Error, match="HELD host"):
        T.statement(villa(), faces, OLD, NEW, JOINT, CAUSES)


def test_adverse_held_without_cause_refused():
    with pytest.raises(T.T670Error, match="no named cause"):
        T.statement(villa(), FACES, OLD, NEW, JOINT, {})


def test_adverse_valued_lintel_missing_refused():
    lines = [x for x in villa() if x["item_code"] != "STR.CONC.LINTEL"]
    with pytest.raises(Exception, match="no valued"):
        T.statement(lines, FACES, OLD, NEW, JOINT, CAUSES)


def test_development_villa_pins():
    """the committed statement equals a fresh build from the pinned merged files (no private data needed)."""
    got = T.build()
    ref = json.loads((ROOT / "research/agents_t670/out/T670_MATERIALS.json").read_text(encoding="utf-8"))
    assert json.loads(json.dumps(got, sort_keys=True)) == ref
    b, a = got["totals_before"], got["totals_after"]
    assert b["MAS.UNITS.BLACK"]["valued"] == 1075.8 and b["MAS.UNITS.BLACK"]["blank_n"] == 18
    assert a["MAS.UNITS.BLACK"]["valued"] == 2571.27625 and a["MAS.UNITS.BLACK"]["range"] == [698.66125, 702.91125]
    assert a["MAS.UNITS.BLACK"]["blank_n"] == 12
    assert a["MAS.MORTAR.BLACK"]["valued"] == 2.59294 and a["MAS.MORTAR.BLACK"]["range"] == [0.618315, 0.622076]
    assert a["MAS.GLUE.AAC"] == b["MAS.GLUE.AAC"] and a["MAS.UNITS.WHITE"]["blank_n"] == 17
    assert sum(r["changed"] for r in got["rows"]) == 12
    assert all(abs(x) <= 1e-4 for c in got["cross_check_t615"] for x in c["residual"])
    assert all(r["cause"] for r in got["rows"] if r["after"][0] == "HELD")
