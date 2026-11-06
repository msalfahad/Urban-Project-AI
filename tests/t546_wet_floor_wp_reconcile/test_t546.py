"""T-546: wet-room floor waterproofing reconciliation room by room (research/agents_t546, R-T546-1).
Synthetic villa "W546" (not the training villa), hand calculations; adverse cases; then the development villa (the
drawing check is skipped when the private DXF is absent)."""
from __future__ import annotations

import json
import os
import sys
from decimal import Decimal
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t546"))
import t546_inputs as I  # noqa: E402
import t546_room_table as T  # noqa: E402

# ---- villa "W546" (hand). Bath A 2.00 x 1.50 = 3.000 m2, perimeter 7.00 lm, door 0.80; bath B 1.80 x 1.50 = 2.700 m2,
# perimeter 6.60 lm, door 0.80; A and B share one 0.10 m wall 1.50 long: each room keeps its own face, the wall's
# 0.15 m2 footprint is in neither. Utility 2.00 x 2.00 = 4.000 m2 wet by the owner rule, not in his list.
# Engine floor 3.000 + 2.700 + 4.000 = 9.700; freelancer A 3.00, B 2.74 (typed) = 5.74; gap +3.960 = +4.000 (utility,
# RULE_DIFFERENCE) - 0.040 (B: engine 2.700 printed - his typed 2.74, ENGINE_RIGHT).
# Upturn (rule height 0.20): A run 7.00 - 0.80 = 6.20 lm = 1.240 m2; B 6.60 - 0.80 = 5.80 lm = 1.160 m2; utility HELD.
# His perimeters 7.00 + 6.60 = 13.60 lm; engine 12.00 lm; gap -1.60 = two doorway segments (HELD rows).
S = "W546 A-101 plan"
H = {"rule_height": "0.20", "height_source": "W546 spec WP-1 (0.20 m upturn)"}


def frows():
    return [
        {"room": "A", "engine_lines": [{"line_id": "fA", "qty": "3.000", "unit": "m2"}], "freelancer": "3.00", "components": []},
        {"room": "B", "engine_lines": [{"line_id": "fB", "qty": "2.700", "unit": "m2"}], "freelancer": "2.74",
         "components": [{"name": "printed 1.80 x 1.50", "qty": "0.040", "sign": -1, "cause": "ENGINE_RIGHT", "basis": S}]},
        {"room": "U", "engine_lines": [{"line_id": "fU", "qty": "4.000", "unit": "m2"}], "freelancer": None,
         "components": [{"name": "utility wet by owner rule", "qty": "4.000", "sign": 1, "cause": "RULE_DIFFERENCE", "basis": S}]},
    ]


def urows():
    door = {"name": "doorway 0.80", "qty": "0.80", "sign": -1, "cause": "HELD", "basis": S + " door schedule"}
    return [
        {"room": "A", "engine_lines": [{"line_id": "uA", "qty": "1.240", "unit": "m2", **H}], "freelancer": "7.00", "components": [door]},
        {"room": "B", "engine_lines": [{"line_id": "uB", "qty": "1.160", "unit": "m2", **H}], "freelancer": "6.60", "components": [dict(door)]},
        {"room": "U", "engine_lines": [{"line_id": "uU", "qty": None, "unit": "m2", "state": "HELD"}], "freelancer": None},
    ]


def test_w546_floor_by_hand():
    assert Decimal("2.00") * Decimal("1.50") + Decimal("1.80") * Decimal("1.50") + 4 == Decimal("9.7000")
    t = T.room_table(unit="m2", rows=frows(), freelancer_total="5.74", freelancer_unit="m2", engine_total="9.700")
    assert t["gap_engine_minus_freelancer"] == "3.960" and Decimal(t["residual"]) == 0
    assert t["by_cause"] == {"ENGINE_RIGHT": "-0.040", "RULE_DIFFERENCE": "4.000"}


def test_w546_upturn_lm_by_hand():
    t = T.room_table(unit="lm", rows=urows(), freelancer_total="13.60", freelancer_unit="lm", engine_total="12.00")
    assert Decimal(t["gap_engine_minus_freelancer"]) == Decimal("-1.60") and Decimal(t["residual"]) == 0
    assert t["held_rooms"] == ["U"] and t["rows"][2]["engine"] is None and t["rows"][2]["state"] == "HELD"


def test_shared_wall_counted_once_per_face():
    # outer length 2.00 + 0.10 + 1.80 = 3.90 x 1.50 = 5.85 gross; less the shared wall 0.10 x 1.50 = the two rooms
    gross = Decimal("3.90") * Decimal("1.50")
    assert gross - Decimal("0.10") * Decimal("1.50") == Decimal("3.000") + Decimal("2.700")


def test_order_invariance_mirror():
    a = T.room_table(unit="m2", rows=frows(), freelancer_total="5.74", freelancer_unit="m2", engine_total="9.700")
    b = T.room_table(unit="m2", rows=frows()[::-1], freelancer_total="5.74", freelancer_unit="m2", engine_total="9.700")
    assert a["by_cause"] == b["by_cause"] and a["residual"] == b["residual"]


def test_residual_named_never_absorbed():
    r = frows(); r[1]["freelancer"] = "2.70"; r[1]["components"] = []
    t = T.room_table(unit="m2", rows=r, freelancer_total="5.70", freelancer_unit="m2", engine_total="9.700")
    assert t["by_cause"]["RULE_DIFFERENCE"] == "4.000" and Decimal(t["residual"]) == 0
    r = frows()
    with pytest.raises(T.TableError, match="components sum"):
        r[1]["components"][0]["qty"] = "0.030"
        T.room_table(unit="m2", rows=r, freelancer_total="5.74", freelancer_unit="m2", engine_total="9.700")


# ---- adverse
def test_adverse_his_lm_times_one_metre_adopted_as_m2_refused():
    with pytest.raises(T.TableError, match="not a height"):
        T.room_table(unit="m2", rows=frows(), freelancer_total="13.60", freelancer_unit="lm", engine_total="9.700")
    r = urows(); r[0]["freelancer_unit"] = "lm"
    with pytest.raises(T.TableError, match="refused in a m2 table"):
        T.room_table(unit="m2", rows=r, freelancer_total="13.60", freelancer_unit="m2", engine_total="12.00")


def test_adverse_engine_m2_into_lm_without_height_source_refused():
    r = urows(); r[0]["engine_lines"][0].pop("height_source")
    with pytest.raises(T.TableError, match="rule height"):
        T.room_table(unit="lm", rows=r, freelancer_total="13.60", freelancer_unit="lm", engine_total="12.00")


def test_adverse_held_never_zero():
    r = urows(); r[2]["engine_lines"][0]["qty"] = "0"
    with pytest.raises(T.TableError, match="never 0"):
        T.room_table(unit="lm", rows=r, freelancer_total="13.60", freelancer_unit="lm", engine_total="12.00")
    r = frows(); r[0]["components"] = [{"name": "x", "qty": None, "sign": 1, "cause": "HELD", "basis": S}]
    with pytest.raises(T.TableError, match="never 0"):
        T.room_table(unit="m2", rows=r, freelancer_total="5.74", freelancer_unit="m2", engine_total="9.700")


def test_adverse_held_against_his_cell_refused():
    r = urows(); r[2]["freelancer"] = "8.00"
    with pytest.raises(T.TableError, match="HELD against"):
        T.room_table(unit="lm", rows=r, freelancer_total="21.60", freelancer_unit="lm", engine_total="12.00")


def test_adverse_tolerance_and_scope():
    r = frows(); r[1]["components"][0]["cause"] = "TOLERANCE"
    with pytest.raises(T.TableError, match="name the cause"):
        T.room_table(unit="m2", rows=r, freelancer_total="5.74", freelancer_unit="m2", engine_total="9.700")
    r = frows(); r[2]["components"] = []
    with pytest.raises(T.TableError, match="scope"):
        T.room_table(unit="m2", rows=r, freelancer_total="5.74", freelancer_unit="m2", engine_total="9.700")


@pytest.mark.parametrize("field,value,msg", [
    ("cause", "UNRESOLVED", "residual"), ("cause", "GUESS", "not in"), ("basis", "", "no basis"),
    ("basis", "freelancer cell", "never a component"), ("sign", 0, "sign"), ("qty", "-0.04", "negative"),
    ("unit", "mm2", "refused in a m2")])
def test_adverse_component_fields(field, value, msg):
    r = frows(); r[1]["components"][0][field] = value
    with pytest.raises(T.TableError, match=msg):
        T.room_table(unit="m2", rows=r, freelancer_total="5.74", freelancer_unit="m2", engine_total="9.700")


def test_adverse_stale_totals_and_units():
    with pytest.raises(T.TableError, match="stale"):
        T.room_table(unit="m2", rows=frows(), freelancer_total="5.74", freelancer_unit="m2", engine_total="9.75")
    with pytest.raises(T.TableError, match="printed total"):
        T.room_table(unit="m2", rows=frows(), freelancer_total="5.80", freelancer_unit="m2", engine_total="9.700")
    with pytest.raises(T.TableError, match="m2 / lm"):
        T.room_table(unit="mm", rows=[], freelancer_total="0", freelancer_unit="mm", engine_total="0")


# ---- development villa
def _index():
    p = ROOT / "research" / "agents_t507" / "out" / "LINE_INDEX_V3_0_57.json"
    return {ln["line_id"]: ln for ln in json.loads(p.read_text())["lines"]}


def test_dev_villa_inputs_match_the_candidate_lines():
    idx = _index()
    floor = [ln for ln in idx.values() if ln["item_code"] == "FIN.WP.FLOOR"]
    up = [ln for ln in idx.values() if ln["item_code"] == "FIN.WP.WALL_UPTURN"]
    assert len(floor) == len(I.ROOMS) == 18 and len(up) == 18
    for key, lid, q, *_ in I.ROOMS:
        ln = idx[lid]
        assert ln["item_code"] == "FIN.WP.FLOOR" and Decimal(str(ln["measured_net"])) == Decimal(q), key
        ul, uq = I.UPTURN[key]
        u = idx[ul]
        assert u["item_code"] == "FIN.WP.WALL_UPTURN" and u["element_id"].split(":")[0] == ln["element_id"].split(":")[0], key
        assert (u["measured_net"] is None and uq is None and u["class"] == "HELD") or Decimal(str(u["measured_net"])) == Decimal(uq)


def test_dev_villa_freelancer_cells_match_his_sheet():
    raw = json.loads((ROOT / "tests" / "alsenan" / "registers_b1" / "FREELANCER_RAW_ROWS.json").read_text())
    rows = {r["row"]: r["cells"] for r in raw["rows"] if r["file"] == "FIN" and r["sheet"] == "العازل"}
    for key, _l, _q, _u, _x, frow, fd, fc, *_ in I.ROOMS:
        if frow is None:
            continue
        c = rows[frow]
        assert Decimal(str(c[f"D{frow}"]["v"])) == Decimal(fd) and Decimal(str(c[f"C{frow}"]["v"])) == Decimal(fc), key
        assert c[f"F{frow}"]["v"] == 1 and c[f"G{frow}"]["f"] == f"=C{frow}*F{frow}"
    assert Decimal(str(rows[39]["H39"]["v"])) == Decimal(I.FREELANCER_FLOOR_M2)
    assert Decimal(str(rows[40]["G40"]["v"])) == Decimal(I.FREELANCER_UPTURN_LM)
    assert rows[51]["I51"]["v"] == "م.ط" and rows[51]["H51"]["f"] == "=G43+G40"  # his upturn unit is lm


def test_dev_villa_floor_closes_room_by_room():
    t = T.room_table(unit="m2", rows=I.floor_rows(), freelancer_total=I.FREELANCER_FLOOR_M2, freelancer_unit="m2",
                     engine_total=I.engine_floor_total())
    assert t["engine_total"] == "85.575710" and t["gap_engine_minus_freelancer"] == "13.565710"
    assert Decimal(t["residual"]) == 0
    assert t["by_cause"] == {"TOLERANCE": "0.023416", "RULE_DIFFERENCE": "13.235", "ENGINE_RIGHT": "0.307294"}
    # restated on V3.0.41 (scoreboard 85.621): + the pantry column 0.045 that T-310 removed (ENGINE_WRONG then, fixed)
    assert Decimal(I.V3041_FLOOR_M2) - Decimal(t["engine_total"]) == Decimal("0.045000")
    assert Decimal(I.V3041_FLOOR_M2) - Decimal(I.FREELANCER_FLOOR_M2) == Decimal("13.610710")


def test_dev_villa_upturn_closes_room_by_room_in_lm():
    t = T.room_table(unit="lm", rows=I.upturn_rows(), freelancer_total=I.FREELANCER_UPTURN_LM, freelancer_unit="lm",
                     engine_total=I.engine_upturn_lm_total())
    assert Decimal(t["engine_total"]) == Decimal("126.072925") and Decimal(t["gap_engine_minus_freelancer"]) == Decimal("-18.537075")
    assert Decimal(t["residual"]) == 0 and t["held_rooms"] == ["GF pantry (wet zone, Q-37 A)"]
    bc = {k: Decimal(v) for k, v in t["by_cause"].items()}
    assert bc["HELD"] == Decimal("-15.50")            # 17 x 0.80 + 1.00 + 0.90 doorway segments
    assert bc["RULE_DIFFERENCE"] == Decimal("-3.556")  # open edges 1.256 + 0.90 + 1.00, basin reveal 0.40
    assert bc["ENGINE_RIGHT"] == Decimal("0.5183") and bc["TOLERANCE"] == Decimal("0.000625")
    # the hand boundary (T-074) less every segment = the engine run to 0.000425 lm
    hand = sum((Decimal(r[8]) for r in I.ROOMS if r[8]), Decimal(0))
    assert hand == Decimal("144.7285") and hand - Decimal("18.656") - Decimal(t["engine_total"]) == Decimal("-0.000425")


DXF = Path(os.environ.get("T546_DXF", ROOT.parents[1] / ".work" / "private" / "P7757_DXF_COMPRESSED" / "P7757.dxf"))


@pytest.mark.skipif(not DXF.exists(), reason="private drawing absent")
def test_dev_villa_pantry_box_and_column_from_the_drawing():
    ezdxf = pytest.importorskip("ezdxf")
    db = ezdxf.readfile(str(DXF)).entitydb
    assert round(db["5D5"].get_measurement(), 3) == 3000.0 and round(db["5E1"].get_measurement(), 3) == 4500.0
    col = [(p[0], p[1]) for p in db["2FAE"].get_points("xy")]
    w = (max(x for x, _ in col) - min(x for x, _ in col)) / 1000
    d = (max(y for _, y in col) - min(y for _, y in col)) / 1000
    assert sorted((round(w, 3), round(d, 3))) == [0.25, 1.1]
    assert Decimal("4.500") * Decimal("3.000") - Decimal("0.900") * Decimal("0.050") == Decimal("13.455")
