"""T-781 OPENING_TABLE_V1: a hand-calculated synthetic villa (not Alsenan), normal and adverse cases."""
import pytest

from engine.source import opening_table_v1 as OT


def op(oid, floor, kind, w, rooms, **kw):
    d = {"opening_id": oid, "floor": floor, "kind": kind, "type": kw.pop("type", kind), "width_m": w, "wall_t_m": 0.2,
         "rooms": rooms, "evidence": kw.pop("evidence", {})}
    d.update(kw)
    return d


ROOMS = {"F0-LIV": {"kind": "DRY"}, "F0-BATH": {"kind": "WET"}, "F0-BED": {"kind": "DRY"}, "F1-BED": {"kind": "DRY"}}


def villa():
    return [
        op("A1", "F0", "WINDOW", 1.80, ["F0-LIV"]),            # read: sill 0.90, head 2.40 -> 1.80 x 1.50 = 2.70
        op("A2", "F0", "WINDOW", 0.60, ["F0-BATH"]),           # no read, wet: sill 1.60, head default 2.40 -> 0.48
        op("A3", "F0", "DOOR", 0.90, ["F0-LIV", "F0-BED"]),    # door: 0.90 x 2.20 = 1.98
        op("A4", "F0", "DOOR", 1.00, ["F0-LIV"], layer="A-GLASS-DOOR"),  # name first: GLASS_DOOR, external
        op("A5", "F0", "PASSAGE", 5.20, ["F0-LIV"]),           # lintel > 4.00 -> FLAGGED
        op("B1", "F1", "WINDOW", 1.20, ["F1-BED"]),            # no read on F1: sill 0.90, head 2.20 -> 1.20 x 1.30
        op("B2", "F1", "WINDOW", 1.20, ["F1-BED"], layer="SHUTTER-ROLL"),  # name: SHUTTER
    ]


READS = [{"floor": "F0", "width_m": 1.80, "sill_m": 0.90, "head_m": 2.40, "kind": "WINDOW", "source": "N elev"}]


def table():
    return {r["id"]: r for r in OT.build(villa(), elevation_reads=READS, rooms=ROOMS)}


def test_normal_hand_calculation():
    t = table()
    a1, a2, a3, b1 = t["F0:A1"], t["F0:A2"], t["F0:A3"], t["F1:B1"]
    assert (a1["sill"], a1["head"], a1["H"], a1["area_m2"]) == (0.90, 2.40, 1.50, 2.70)
    assert a1["H_label"] == OT.DRAWING_READ and a1["W_label"] == OT.MEASURED
    assert (a2["sill"], a2["head"], a2["area_m2"]) == (1.60, 2.40, 0.48) and a2["head_label"] == OT.DEFAULT
    assert (a3["type"], a3["side"], a3["area_m2"], a3["lintel_m"]) == ("DOOR", "INTERNAL", 1.98, 1.20)
    assert (b1["sill"], b1["head"], b1["area_m2"]) == (0.90, 2.20, 1.56)  # no printed head on F1 -> 2.20
    assert t["F0:A4"]["type"] == "GLASS_DOOR" and t["F0:A4"]["side"] == "EXTERNAL"
    assert t["F1:B2"]["type"] == "SHUTTER"
    assert t["F0:A5"]["lintel_label"] == "FLAGGED" and t["F0:A5"]["lintel_m"] is None
    assert t["F0:A1"]["masonry_deduction_m2"] == 2.70  # Q-73 full deduction
    s = OT.summary(list(t.values()))
    assert s["blank_W_or_H"] == 0 and s["by_type_side"]["WINDOW|EXTERNAL"] == {"pcs": 3, "m2": 4.74}


def test_lintel_standards():
    assert OT.lintel(0.90) == (1.20, OT.DEFAULT)   # 0.90 + 2 x 0.15 = 1.20: the 1.20 standard just covers it
    assert OT.lintel(0.91) == (1.50, OT.DEFAULT)
    assert OT.lintel(3.70) == (4.00, OT.DEFAULT)
    assert OT.lintel(3.71) == (None, "FLAGGED")
    assert OT.lintel(None) == (None, OT.HELD)


def test_adverse_mirrored_insert_and_mm_units():
    o = op("M1", "F0", "WINDOW", None, ["F0-LIV"], insert={"name": "WIN-120", "xscale": -1.0, "block_width": 1200})
    r = OT.build([o], rooms=ROOMS)[0]
    assert r["W"] == 1.20 and r["W_label"] == OT.MEASURED and "mirrored" in r["W_note"]
    assert r["type"] == "WINDOW"


def test_adverse_missing_head_is_default_never_zero_and_missing_width_held():
    rows = OT.build([op("X1", "F2", "WINDOW", 1.00, ["F0-BED"]), op("X2", "F2", "WINDOW", None, ["F0-BED"])],
                    rooms=ROOMS)
    x1, x2 = rows
    assert x1["head"] == 2.20 and x1["head_label"] == OT.DEFAULT and x1["H"] == 1.30
    assert x2["W"] is None and x2["W_label"] == OT.HELD and x2["area_m2"] is None and x2["area_label"] == OT.HELD
    assert OT.blanks(rows) == ["F2:X2"]


def test_adverse_main_entrance_head_not_spread_to_doors():
    rows = OT.build([op("D1", "F0", "DOOR", 2.00, ["F0-LIV"]), op("D2", "F0", "DOOR", 0.90, ["F0-LIV", "F0-BED"])],
                    elevation_reads=[{"floor": "F0", "width_m": 2.00, "sill_m": 0.0, "head_m": 2.60, "kind": "DOOR",
                                      "source": "S elev"}], rooms=ROOMS)
    assert rows[0]["head"] == 2.60 and rows[1]["head"] == 2.20


def test_adverse_disagreeing_reads_and_group_count_match():
    ops = [op("G1", "F0", "WINDOW", 1.50, ["F0-LIV"]), op("G2", "F0", "WINDOW", 1.50, ["F0-BED"])]
    reads = [{"floor": "F0", "width_m": 1.50, "sill_m": 1.0, "head_m": 2.5, "kind": "WINDOW", "source": "a"},
             {"floor": "F0", "width_m": 1.50, "sill_m": 0.0, "head_m": 3.0, "kind": "WINDOW", "source": "b"}]
    rows = OT.build(ops, elevation_reads=reads, rooms=ROOMS)
    assert round(sum(r["area_m2"] for r in rows), 4) == round(1.5 * 1.5 + 1.5 * 3.0, 4)  # group sum exact
    assert all(f["code"] == "PER_OPENING_ORDER_UNPROVEN" for r in rows for f in r["findings"])
    # three reads for two openings that disagree: nothing is chosen, defaults apply, finding named
    rows = OT.build(ops, elevation_reads=reads + [dict(reads[0], sill_m=0.5)], rooms=ROOMS)
    assert all(r["head_label"] == OT.DEFAULT for r in rows)
    assert all(any(f["code"] == "ELEVATION_READS_DISAGREE" for f in r["findings"]) for r in rows)


def test_adverse_elevation_only_and_arched_head():
    reads = [{"floor": "F0", "width_m": 2.00, "sill_m": 0.0, "head_m": 2.80, "kind": "WINDOW", "arched": True,
              "source": "W elev arch crown"}]
    rows = OT.build([], elevation_reads=reads, rooms=ROOMS)
    assert len(rows) == 1 and rows[0]["area_m2"] == 5.60 and rows[0]["glazing"] == "ARCHED_HEAD"
    assert rows[0]["findings"][0]["code"] == "PLAN_SYMBOL_NOT_DETECTED"


def test_adverse_height_only_read_and_lift_not_a_door():
    ops = [op("S1", "F0", "WINDOW", 1.95, ["F0-LIV"]), op("L1", "F0", "PASSAGE", 1.00, ["F0-LIV"], type="LIFT_SHAFT")]
    reads = [{"floor": "F0", "width_m": 1.95, "height_m": 2.20, "kind": "WINDOW", "type_hint": "SHUTTER",
              "source": "fence elev"}]
    s1, l1 = OT.build(ops, elevation_reads=reads, rooms=ROOMS)
    assert s1["type"] == "SHUTTER" and s1["H"] == 2.20 and s1["sill_label"] == OT.DEFAULT
    assert l1["type"] == "LIFT" and l1["lintel_label"] == "NOT_APPLICABLE"


def test_refuses_negative():
    with pytest.raises(ValueError):
        OT.build([op("N", "F0", "WINDOW", -1.0, [])])
