"""T-511: cement / sand producer census (research/agents_t511/t511_cement_sand_census.py).

Fixture villa P511 (not the training villa), by hand. One cement key (50 kg bags) and one sand key (loose m3)
shared by three trades:
  W1  black 0.20 block wall 20.00 m2 (masonry table): joint 0.01475 m3/m2 -> 0.295 m3; 1:4 x 8 / x 1.1 ->
      cement 2.36 bags, sand 0.3245 m3.
  W2  white AAC wall 15.00 m2: AAC glue, NOT a cement : sand key (NOT_APPLICABLE).
  PL1 wall plaster 40.00 m2 x 0.020 m = 0.800 m3; synthetic sourced 1:4 coat at the Q-53 C conversion 7.6608 bags /
      1.064 m3 per m3 -> cement 6.12864 bags, sand 0.8512 m3 (the plaster table's own figure: the census never
      converts).
  B1  dry bed under F1 (porcelain 10.00 m2): 0.30 .. 0.40 m3 -> cement 2.40 .. 3.20 bags, sand 0.33 .. 0.44 m3.
  Project installed: cement 2.36 + 6.12864 + 2.40 .. 3.20 = 10.88864 .. 11.68864 bags (whole bags 11 .. 12);
  sand 0.3245 + 0.8512 + 0.33 .. 0.44 = 1.5057 .. 1.6157 m3.
Adverse: one HELD bed -> its trade and the project HELD (known part AT_LEAST 8.48864 bags, never a partial total);
two producers on one physical bed; a reader that disagrees; a stale producer (line now HELD / other net); kg for
bags; HELD as 0; a cement key on a tile-wall line; an unclassified code; a host with no state; mirror / rotation /
millimetres leave every figure unchanged.
"""

import copy
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "research" / "agents_t511"))

import t511_cement_sand_census as M  # noqa: E402
from engine.source import finish_materials_table as V1  # noqa: E402

C, S, I = M.CEMENT, M.SAND, M.INSTALLED


def shoelace(pts, unit_m=1.0):
    a = 0.0
    for (x1, y1), (x2, y2) in zip(pts, pts[1:] + pts[:1]):
        a += x1 * y2 - x2 * y1
    return round(abs(a) / 2.0 * unit_m * unit_m, 6)


def _ln(i, code, cls, net=None, lo=None, hi=None, unit="m2"):
    return {"line_id": i, "item_code": code, "element_id": i, "class": cls, "unit": unit, "measured_net": net,
            "held_low": lo, "held_high": hi}


F1 = [(0, 0), (4.0, 0), (4.0, 2.5), (0, 2.5)]


def villa(f1=F1, unit_m=1.0, bed_held=False):
    a = shoelace(f1, unit_m)
    lines = [_ln("W1", "MAS.BLOCK", "RELEASED", 20.0), _ln("W2", "MAS.BLOCK", "RELEASED", 15.0),
             _ln("PL1", "FIN.PLASTER", "RELEASED", 40.0), _ln("F1", "FIN.FLOOR.PORCELAIN", "RELEASED", a),
             _ln("B1a", "FIN.FLOOR.BED.DRY", "RELEASED", a),
             _ln("B1v", "FIN.FLOOR.BED.DRY", "HELD", None, round(a * 0.03, 6), round(a * 0.04, 6), "m3"),
             _ln("WT1", "FIN.WALL.TILE", "RELEASED", 12.0)]
    rd = {"class": "RELEASED", "net": 20.0}
    rows = [M.prow("MASONRY", M.PRODUCER, "W1", None, M.MASONRY, C, I, 2.36, 2.36, read=rd, trade=M.MASONRY),
            M.prow("MASONRY", M.PRODUCER, "W1", None, M.MASONRY, S, I, 0.3245, 0.3245, read=rd, trade=M.MASONRY),
            M.prow("PLASTER", M.PRODUCER, "PL1", None, "WALL_PLASTER", C, I, 6.12864, 6.12864,
                   read={"class": "RELEASED", "net": 40.0}, trade=M.PLASTER),
            M.prow("PLASTER", M.PRODUCER, "PL1", None, "WALL_PLASTER", S, I, 0.8512, 0.8512,
                   read={"class": "RELEASED", "net": 40.0}, trade=M.PLASTER)]
    v1 = V1.materials(V1.DRY_FLOOR, None, a)
    w = 1 + V1.OWNER_VALUES["mortar_waste"]
    lo_c, hi_c = (None, None) if bed_held else (v1["cement_bags_low"] / w, v1["cement_bags_high"] / w)
    lo_s, hi_s = (None, None) if bed_held else (v1["sand_m3_low"] / w, v1["sand_m3_high"] / w)
    bd = {"class": "HELD", "net": None}
    rows += [M.prow("BED", M.PRODUCER, "B1v", "F1", M.TILE_BED, C, I, lo_c, hi_c, read=bd, trade=M.TILE_BED),
             M.prow("BED", M.PRODUCER, "B1v", "F1", M.TILE_BED, S, I, lo_s, hi_s, read=bd, trade=M.TILE_BED)]
    states = {"W2": (M.NA, M.MASONRY, "white AAC: glue"), "B1a": (M.NA, M.TILE_BED, "m2 partner of B1v")}
    return lines, rows, states


def _tot(c, scope, mat, stage=I):
    return c["subtotals"][scope][stage][mat]


# ------------------------------------------------------------------ normal case, by hand

def test_fixture_by_hand():
    c = M.census(*villa())
    assert c["fails"] == [] and c["stale"] == []
    e = _tot(c, "PROJECT", C)
    assert (e["status"], e["low"], e["high"]) == ("COMPUTED", 10.88864, 11.68864)
    assert (e["whole_bags_low"], e["whole_bags_high"]) == (11, 12)
    s = _tot(c, "PROJECT", S)
    assert (s["low"], s["high"]) == (1.5057, 1.6157)
    assert (_tot(c, M.TILE_BED, C)["low"], _tot(c, M.TILE_BED, C)["high"]) == (2.4, 3.2)
    assert _tot(c, M.MASONRY, C)["low"] == 2.36 and _tot(c, M.PLASTER, C)["low"] == 6.12864
    assert c["states"][("W2", C)] == M.NA and c["states"][("B1v", C)] == M.PRODUCED


@pytest.mark.parametrize("f1,unit_m", [
    ([(0, 0), (-4.0, 0), (-4.0, 2.5), (0, 2.5)], 1.0),                     # mirror
    ([(0, 0), (0, 4.0), (-2.5, 4.0), (-2.5, 0)], 1.0),                     # rotation 90 deg
    ([(0, 0), (4000.0, 0), (4000.0, 2500.0), (0, 2500.0)], 0.001)])        # millimetres
def test_mirror_rotation_units_change_nothing(f1, unit_m):
    a, b = M.census(*villa()), M.census(*villa(f1, unit_m))
    assert b["fails"] == [] and b["subtotals"] == a["subtotals"]


# ------------------------------------------------------------------ adverse cases

def test_one_held_bed_holds_trade_and_project_never_partial():
    c = M.census(*villa(bed_held=True))
    assert c["fails"] == []
    t, p = _tot(c, M.TILE_BED, C), _tot(c, "PROJECT", C)
    assert t["status"] == "HELD" and t["low"] is None and t["at_least_low"] is None
    assert p["status"] == "HELD" and p["low"] is None and p["high"] is None
    assert p["at_least_low"] == 8.48864 and "B1v|TILE_BED" in p["held"]
    assert "whole_bags_low" not in p                     # no bags to buy from a partial sum


def test_second_producer_on_the_same_physical_bed():
    lines, rows, st = villa()
    rows.append(M.prow("FINISH_TABLE", M.PRODUCER, "B1v", "F1", M.TILE_BED, C, I, 2.4, 3.2, trade=M.TILE_BED,
                       read={"class": "HELD", "net": None}))
    kinds = {f["kind"] for f in M.census(lines, rows, st)["fails"]}
    assert "TWO_PRODUCERS" in kinds


def test_reader_must_equal_producer_and_needs_one():
    lines, rows, st = villa()
    ok = rows + [M.prow("V1", M.READER, "B1v", "F1", M.TILE_BED, C, I, 2.4, 3.2)]
    assert M.census(lines, ok, st)["fails"] == []
    bad = rows + [M.prow("V1", M.READER, "B1v", "F1", M.TILE_BED, C, I, 2.52, 3.36)]   # waste folded in: wrong stage
    assert {f["kind"] for f in M.census(lines, bad, st)["fails"]} == {"READER_DIVERGENCE"}
    lone = rows + [M.prow("V1", M.READER, "B1v", "F1", M.TILE_BED, C, M.PROCUREMENT, 2.52, 3.36)]
    assert {f["kind"] for f in M.census(lines, lone, st)["fails"]} == {"LONE_READER"}


def test_wet_wall_tile_line_never_carries_cement():
    lines, rows, st = villa()
    rows.append(M.prow("V1_WET_WALL", M.PRODUCER, "WT1", None, "WET_WALL_BED", C, I, 1.92, 1.92, trade=M.TILE_BED,
                       read={"class": "RELEASED", "net": 12.0}))
    assert "KEY_ON_NON_HOST" in {f["kind"] for f in M.census(lines, rows, st)["fails"]}


@pytest.mark.parametrize("cls,net,why", [("HELD", None, "STALE_CLASS"), ("RELEASED", 18.0, "STALE_NET")])
def test_stale_producer_leaves_the_sum_and_stays_beside(cls, net, why):
    lines, rows, st = villa()
    lines[0].update({"class": cls, "measured_net": net})
    c = M.census(lines, rows, st)
    assert c["fails"] == []
    assert {s["line_id"] for s in c["stale"]} == {"W1"} and all(s["why"].startswith(why) for s in c["stale"])
    assert {(s["material"], s["beside_low"]) for s in c["stale"]} == {(C, 2.36), (S, 0.3245)}
    m = _tot(c, M.MASONRY, C)
    assert m["status"] == "HELD" and m["low"] is None and m["at_least_low"] is None
    assert c["states"][("W1", C)] == M.HELD


def test_stale_absent_line():
    lines, rows, st = villa()
    c = M.census(lines[1:], rows, st)
    assert {s["why"].split(":")[0] for s in c["stale"]} == {"STALE_ABSENT"}


def test_units_held_zero_and_range_order():
    lines, rows, st = villa()
    r = copy.deepcopy(rows)
    r[0]["unit"] = "kg"
    assert "UNIT" in {f["kind"] for f in M.census(lines, r, st)["fails"]}
    r = copy.deepcopy(rows)
    r[0].update(status="HELD", low=0.0, high=0.0)
    assert "ZERO_FOR_HELD" in {f["kind"] for f in M.census(lines, r, st)["fails"]}
    r = copy.deepcopy(rows)
    r[4].update(low=3.2, high=2.4)
    assert "RANGE_ORDER" in {f["kind"] for f in M.census(lines, r, st)["fails"]}


def test_unclassified_code_and_host_without_state():
    lines, rows, st = villa()
    kinds = {f["kind"] for f in M.census(lines + [_ln("X1", "FIN.NEW.LAYER", "RELEASED", 5.0)], rows, st)["fails"]}
    assert "UNCLASSIFIED_CODE" in kinds
    kinds = {f["kind"] for f in M.census(lines + [_ln("W3", "MAS.BLOCK", "RELEASED", 5.0)], rows, st)["fails"]}
    assert "HOST_STATE" in kinds
    held = dict(st, W3=(M.HELD, M.MASONRY, "NO_PRODUCER: test"))
    c = M.census(lines + [_ln("W3", "MAS.BLOCK", "RELEASED", 5.0)], rows, held)
    assert c["fails"] == [] and _tot(c, "PROJECT", C)["status"] == "HELD"


# ------------------------------------------------------------------ the candidate of record V3.0.56

@pytest.fixture(scope="module")
def built():
    return M.build()


def test_candidate_census_clean(built):
    assert built["fails"] == []
    assert built["keys_with_two_producers"] == 0 and built["reader_divergences"] == 0
    assert built["keys_bound_by_two_tables"] == 88              # 44 bed hosts x cement / sand, T-500 + V1 reader
    assert built["candidate"] == "ARCH_TAKEOFF_V3.0.57" and built["identity"]["v3_0_57_lines"] == 4994
    assert built["identity"]["t508_codes"] == ["FIN.SKIRTING", "FIN.STAIR.SKIRTING.SLOPED",
                                               "FIN.STAIR.SKIRTING.ZIGZAG"]
    assert built["identity"]["host_partner_lines_identical_55_56"] == 365
    assert ["ADD_POOL_LAYER", "WP.POOL.PROTECTION_SCREED", "HOST"] in built["identity"]["t310_rows"]
    assert built["host_states_cement"] == {"HELD": 160, "NOT_APPLICABLE": 74, "PRODUCED": 46}
    assert "UNCLASSIFIED" not in built["code_classes"]


def test_candidate_masonry_two_stale_lines_after_t488(built):
    st = {(s["line_id"], s["material"]): s for s in built["stale"]}
    assert set(st) == {("L-76a4d8e50423fb02b914", C), ("L-76a4d8e50423fb02b914", S),
                       ("L-a6eedf5e4adec6d07618", C), ("L-a6eedf5e4adec6d07618", S)}
    assert st[("L-76a4d8e50423fb02b914", C)]["beside_low"] == 2.55588
    m = built["subtotals"][M.MASONRY][I]
    assert m[C]["status"] == "HELD" and m[C]["at_least_low"] == round(2.8202 + 7.335352, 6) == 10.155552
    assert m[S]["at_least_low"] == round(0.387777 + 1.008611, 6)
    assert round(10.155552 / 8.0, 6) == 1.269444                  # = the fresh 0.20 m mortar on V3.0.56


def test_candidate_tile_bed_and_project_held_never_partial(built):
    t = built["subtotals"][M.TILE_BED][I][C]
    assert t["status"] == "HELD" and t["low"] is None
    assert (t["at_least_low"], t["at_least_high"]) == (99.748616, 137.562192)
    assert t["held"] == ["L-a788de4672b1f0d2e6c1|TILE_BED"]
    mb = built["missing_bed"][0]
    assert mb["effect_bags_at_most"] == round(0.23 * 0.06 * 8, 6)    # immaterial, still HELD
    p = built["subtotals"]["PROJECT"][I][C]
    assert p["status"] == "HELD" and p["low"] is None and "whole_bags_low" not in p
    assert (p["at_least_low"], p["at_least_high"]) == (round(10.155552 + 99.748616, 6), round(10.155552 + 137.562192, 6))
    for scope in built["subtotals"].values():                       # R-T499-1 on every group
        for stage in scope.values():
            for e in stage.values():
                assert (e["status"] == "HELD") == (e["low"] is None) and e["low"] != 0.0


def test_candidate_plaster_and_no_producer_hosts(built):
    p = built["subtotals"][M.PLASTER][I][C]
    assert p["status"] == "HELD" and p["at_least_low"] is None and p["rows"] == 159
    trades = {t for t, _, _ in built["held_contributors"]}
    assert {M.STONE_BED, M.SCREED, M.OUTDOOR_BED} <= trades
    bs = {b["line_id"]: b for b in built["beside"]}
    assert bs["L-ab44fbc79bed353bde99"]["cement_bags"] == [round(21.0142 * 0.03 * 8, 6), round(21.0142 * 0.04 * 8, 6)]
    assert bs["L-4ec54f9922da7281573a"]["installed_m3_released"] == 5.4925
    assert bs["L-e4789d76efedbc351bd4"]["installed_m3_released"] == 1.035
    assert bs["L-335ae7ca24030b8e9be4"]["installed_m3_released"] == 1.5245      # T-310 pool screed (V3.0.57)
    sc = built["subtotals"][M.SCREED][I][C]
    assert sc["status"] == "HELD" and sc["at_least_low"] is None and sc["rows"] == 8


def test_t310_identity_is_checked(monkeypatch):
    real = M._load

    def fake(p, pins=True):
        d = real(p, pins)
        if p == M.T310:
            d = copy.deepcopy(d)
            d["new_candidate"]["sha256_8"] = "00000000"
        return d
    monkeypatch.setattr(M, "_load", fake)
    with pytest.raises(M.CensusError, match="STALE_CANDIDATE"):
        M.candidate()


def test_t508_touching_a_host_code_is_refused(monkeypatch):
    real = M._load

    def fake(p, pins=True):
        d = real(p, pins)
        if p == M.T508:
            d = copy.deepcopy(d)
            d["rows"][0]["item_code"] = "MAS.BLOCK"
        return d
    monkeypatch.setattr(M, "_load", fake)
    with pytest.raises(M.CensusError, match="STALE_CANDIDATE"):
        M.candidate()


def test_pins(tmp_path, monkeypatch):
    bad = tmp_path / "x.json"
    bad.write_text(json.dumps({"lines": []}))
    monkeypatch.setitem(M.PINS, bad, "0" * 64)
    with pytest.raises(M.CensusError, match="PIN"):
        M._load(bad)


def test_committed_output_is_the_rebuild(tmp_path, built):
    M.write(built, tmp_path)
    for name in ("CEMENT_SAND_CENSUS_T511.json", "CEMENT_SAND_CENSUS_T511.csv"):
        assert (tmp_path / name).read_bytes() == (ROOT / "research/agents_t511/out" / name).read_bytes()
