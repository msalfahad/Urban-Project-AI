"""T-676 plaster / render / spatter / paint HELD census (R-T676-1 .. -3): synthetic villa W676 by hand (normal +
adverse) and the development villa pinned to the committed outputs.

Villa W676 (synthetic, not the development villa), by hand:
  face F1 4.00 m x 3.00 m with a FULL-HEIGHT opening 1.00 x 3.00 on F1   -> 12.00 - 3.00 = 9.00 m2
  stair-shaft wall 10.00 m, storey intervals 4.50 + 4.20, top exposed 3.80 (Q-72 continuous)
                                                                        -> 10.00 x 12.50 = 125.00 m2
    landing-slab edge band 2.40 x 0.20 deducted separately              -> 124.52 m2
  door reveal 0.20 wall, 2.20 high, 1.00 wide                           -> 2 x 0.20 x 2.20 + 0.20 x 1.00 = 1.08 m2
  internal plaster 0.02 m, 1:4, dry 1.33, 1,440 kg/m3, 50 kg bag        -> 0.153216 bags + 0.02128 m3 sand per m2
  spatter dash 0.005 m, 1:2                                             -> 0.06384 bags + 0.004433.. m3 sand per m2
"""
import json
import subprocess
import sys
from decimal import Decimal
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t676"))
import t676_rules as R  # noqa: E402

OUT = ROOT / "research" / "agents_t676" / "out" / "T676_PLASTER_PAINT_CENSUS.json"
SRC = "W676 plan"


def T(v):
    return (v, SRC)


def _op(**kw):
    o = {"id": "O1", "face": "F1", "width": T("1.00"), "height": T("3.00"), "exists": True}
    o.update(kw)
    return o


def _e(**kw):
    e = {"line_id": "L-w676-1", "item_code": "FIN.PLASTER", "unit": "m2", "element_id": "W676-R1",
         "held_low": "9", "held_high": "10", "measured_net": None, "class": "OPEN_BOUND", "queued_row": "none",
         "cause": "floor build-up b 0 .. 0.10", "source": "W676 ledger row 1"}
    e.update(kw)
    return e


FIX = {"status": "DRAWING-CONFIRMED", "terms": {"thickness": T("0.20"), "height": T("2.20"), "width": T("1.00")},
       "value": "1.08"}


# ---------------------------------------------------------------- normal cases (hand values)

def test_face_behind_full_height_opening():
    r = R.face_net("F1", T("4.00"), T("3.00"), [_op()])
    assert (r["gross"], r["deducted"], r["net"]) == ("12", "3", "9")


def test_face_mirror_and_rotation_invariant():
    # lengths and heights do not change under a mirrored or rotated plan: the same terms give the same net
    a = R.face_net("F1", T("4.00"), T("3.00"), [_op()])
    b = R.face_net("F1", T("4.000"), T("3.000"), [_op(width=T("1.000"), height=T("3.000"))])
    assert a["net"] == b["net"] == "9"


def test_stair_shaft_wall_full_exposed_height():
    r = R.shaft_face("SH1", T("10.00"), [T("4.50"), T("4.20")], T("3.80"), [(T("2.40"), T("0.20"))])
    assert (r["gross"], r["landing_bands"], r["net"]) == ("125", "0.48", "124.52")


def test_reveal_by_hand():
    assert R.reveal_area(T("0.20"), T("2.20"), T("1.00")) == Decimal("1.080000")
    assert R.reveal_area(T("0.15"), T("2.20"), T("0.90")) == Decimal("0.795000")


def test_coat_per_m2_q79_q53c():
    cb, sm = R.coat_per_m2("WALL_PLASTER", "0.02")
    assert R.q(cb) == Decimal("0.153216") and R.q(sm) == Decimal("0.021280")
    cb, sm = R.coat_per_m2("BOND_COAT", "0.005")
    assert R.q(cb) == Decimal("0.063840") and R.q(sm) == Decimal("0.004433")


def test_coat_materials_on_held_bound_and_minimum():
    r = R.coat_materials("100", "110", "WALL_PLASTER", "0.02")
    assert r["status"] == "HELD_BOUND" and r["cement_bags"] == ["15.3216", "16.85376"]
    assert r["sand_m3"] == ["2.128", "2.3408"]
    m = R.coat_materials("10", "10", "LEVELLING_RENDER", "0.015", "MINIMUM")
    assert m["status"] == "AT_LEAST" and m["cement_bags"] == ["1.14912", "1.14912"]


def test_census_normal_with_fix_row():
    fixed = _e(line_id="L-w676-2", element_id="W676-D1", held_low="1.08", held_high="1.2", fix=FIX)
    fixed["class"] = "MEASURABLE_NOW"
    es = [_e(), fixed]
    tot = R.census(es, ["L-w676-1", "L-w676-2"])
    t = tot["FIN.PLASTER|m2"]
    assert t["lines"] == 2 and t["fix_rows"] == 1 and (t["low"], t["high"]) == ("10.08", "11.2")


def test_blank_lines_never_summed_as_zero():
    tot = R.totals([_e(held_low=None, held_high=None)])
    t = tot["FIN.PLASTER|m2"]
    assert t["low"] is None and t["high"] is None and t["blank"] == 1


def test_scope_codes():
    assert R.code_in_scope("FIN.PAINT") and R.code_in_scope("FIN.SPATTER_DASH") and not R.code_in_scope("FIN.SKIRTING")


# ---------------------------------------------------------------- adverse cases

@pytest.mark.parametrize("op,why", [
    (_op(face="F2"), "not F1"),
    (_op(exists=False), "not physically built"),
    (_op(height=T("3.20")), "data error"),
    (_op(width=T("4.50")), "wider than the face"),
    (_op(width=("1.00", "")), "no source"),
])
def test_face_adverse(op, why):
    with pytest.raises(R.RuleError, match=why):
        R.face_net("F1", T("4.00"), T("3.00"), [op])


def test_face_unit_slip_and_zero():
    with pytest.raises(R.RuleError, match="unit slip"):
        R.face_net("F1", T("4.00"), T("300"))
    with pytest.raises(R.RuleError, match="never 0"):
        R.face_net("F1", T("1.00"), T("3.00"), [_op()])
    with pytest.raises(R.RuleError, match="held is never 0"):
        R.face_net("F1", T("0"), T("3.00"))


def test_shaft_adverse():
    with pytest.raises(R.RuleError, match="longer than the face"):
        R.shaft_face("SH1", T("2.00"), [T("4.50")], T("3.80"), [(T("2.40"), T("0.20"))])
    with pytest.raises(R.RuleError, match="unit slip"):
        R.shaft_face("SH1", T("10.00"), [T("4.50")], T("380"))


def test_reveal_adverse():
    with pytest.raises(R.RuleError, match="no source"):
        R.reveal_area(("0.20", ""), T("2.20"), T("1.00"))
    with pytest.raises(R.RuleError, match="unit slip"):
        R.reveal_area(T("20"), T("2.20"), T("1.00"))


def test_coat_adverse():
    with pytest.raises(R.RuleError, match="HELD"):
        R.coat_per_m2("BOND_COAT", None)
    with pytest.raises(R.RuleError, match="refused"):
        R.coat_per_m2("WALL_PLASTER", "2")
    with pytest.raises(R.RuleError, match="no owner mix"):
        R.coat_per_m2("GYPSUM", "0.01")
    r = R.coat_materials(None, None, "WALL_PLASTER", "0.02")
    assert r["status"] == "HELD" and r["cement_bags"] is None
    r = R.coat_materials("10", "12", "BOND_COAT", None)
    assert r["status"] == "HELD" and r["sand_m3"] is None


@pytest.mark.parametrize("kw,why", [
    ({"cause": "his row says 9"}, "freelancer"),
    ({"source": "freelancer workbook"}, "freelancer"),
    ({"measured_net": 9}, "carries a value"),
    ({"held_low": "0", "held_high": "0"}, "held as 0"),
    ({"held_low": "5", "held_high": None}, "half a bound"),
    ({"held_low": None, "held_high": None}, "OPEN_BOUND without a bound"),
    ({"class": "DESIGNER_ITEM"}, "D-nn"),
    ({"class": "OWNER_OPEN"}, "owner reference"),
    ({"class": "QUEUED_ROW"}, "name the row"),
    ({"class": "MEASURABLE_NOW"}, "without its fix row"),
    ({"fix": FIX}, "a fix row on a OPEN_BOUND"),
    ({"class": "MEASURABLE_NOW", "fix": dict(FIX, value="1.20")}, "recomputed"),
    ({"class": "MEASURABLE_NOW", "fix": dict(FIX, wired=True)}, "never wired"),
    ({"class": "MEASURABLE_NOW", "fix": dict(FIX, status="ASSUMED - OWNER-APPROVED")}, "owner Q-id"),
    ({"queued_row": "T-999"}, "queued row"),
    ({"item_code": "FIN.SKIRTING"}, "not a wall-coat"),
    ({"held_low": "1", "held_high": "2", "merged_bound": {"low": "1", "high": "2", "source": "x"}}, "BLANK"),
])
def test_entry_adverse(kw, why):
    with pytest.raises(R.RuleError, match=why):
        R.check_entry(_e(**kw))


def test_census_set_adverse():
    with pytest.raises(R.RuleError, match="misses"):
        R.census([_e()], ["L-w676-1", "L-w676-9"])
    with pytest.raises(R.RuleError, match="not HELD"):
        R.census([_e(), _e(line_id="L-w676-3")], ["L-w676-1"])
    with pytest.raises(R.RuleError, match="twice"):
        R.census([_e(), _e()], ["L-w676-1"])


def test_rules_module_leaves_global_decimal_context():
    import decimal
    before = decimal.getcontext().prec
    R.coat_materials("100", "110", "WALL_PLASTER", "0.02")
    assert decimal.getcontext().prec == before


# ---------------------------------------------------------------- development villa pins (committed outputs)

def _out():
    return json.loads(OUT.read_text())


def test_alsenan_outputs_rebuild_identically():
    p = subprocess.run([sys.executable, "-I", str(ROOT / "research/agents_t676/t676_alsenan.py"), "--check"],
                       capture_output=True, text=True, cwd=ROOT)
    assert p.returncode == 0, p.stdout + p.stderr


def test_alsenan_census_is_complete():
    o = _out()
    cand = json.loads((ROOT / "research/agents_t668/out/LINE_INDEX_V3_0_64.json").read_text())
    held = {l["line_id"] for l in cand["lines"] if l["class"] == "HELD" and R.code_in_scope(l["item_code"])}
    assert o["count"] == len(held) == 57 and {e["line_id"] for e in o["entries"]} == held
    assert o["by_class"] == {"DESIGNER_ITEM": 20, "MEASURABLE_NOW": 1, "OPEN_BOUND": 6, "OWNER_DECISION_HOLD": 6,
                             "OWNER_OPEN": 16, "PRINTED_VALUE_GAP": 2, "QUEUED_ROW": 6}
    assert o["by_queued_row"] == {"T-314": 7, "none": 50}


def test_alsenan_fix_row_op009():
    (f,) = _out()["fix_rows"]
    assert f["line_id"] == "L-f4175f9915208dc5f9f7" and f["value"] == "1.08" and f["before"] == ["1.08", "1.2"]
    assert f["status"] == "ASSUMED - OWNER-APPROVED" and f["owner_ref"] == "Q-55 C" and f["wired"] is False


def test_alsenan_totals_and_materials():
    o = _out()
    assert o["totals_m2"]["FIN.PLASTER|m2"]["low"] == "932.72581"
    assert o["totals_m2"]["FIN.PLASTER|m2"]["high"] == "1006.77641"
    assert o["totals_m2"]["FIN.PAINT|m2"]["low"] == "487.121" and o["totals_m2"]["FIN.PAINT|m2"]["high"] == "542.8606"
    for k in ("ARCH.FACADE|m2", "EXT.FENCE.PAINT|m2", "EXT.FENCE.PLASTER|m2", "FIN.EXT.FINISH|m2"):
        assert o["totals_m2"][k]["low"] is None  # held, never 0
    m = o["materials_totals"]["FIN.PLASTER|WALL_PLASTER (1:4)"]
    assert m["cement_bags"] == ["142.908518", "154.235867"] and m["bounded"] == 14
    assert o["materials_totals"]["FIN.PLASTER|BOND_COAT spatter dash (1:2)"]["cement_bags"] is None
    for e in o["entries"]:
        assert e["measured_net"] is None
