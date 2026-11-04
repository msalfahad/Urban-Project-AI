"""T-500: tile bed mortar material table (research/agents_t500/t500_tile_bed_mortar.py).

Fixture villa P500 (not the training villa), by hand, owner Q-45 values (DRY 0.03 .. 0.04 m, WET 0.04 .. 0.06 m,
1:4 = 8 bags of 50 kg + 1.1 m3 loose sand per m3, waste 5 % separate):
  R1 dry living 6.00 x 4.50 = 27.00 m2: bed 0.81 .. 1.08 m3; cement 6.48 .. 8.64 bags; sand 0.891 .. 1.188 m3;
     waste 0.324 .. 0.432 bags / 0.04455 .. 0.0594 m3; procurement 6.804 .. 9.072 bags / 0.93555 .. 1.2474 m3.
  B1 wet bath 2.40 x 1.80 = 4.32 m2: bed 0.1728 .. 0.2592 m3; cement 1.3824 .. 2.0736 bags; sand 0.19008 .. 0.28512 m3;
     procurement 1.45152 .. 2.17728 bags.
  project: 0.9828 .. 1.3392 m3; cement 7.8624 .. 10.7136 bags; procurement 8.25552 .. 11.24928 -> to buy 9 .. 12 bags.
  WW1 the bath's tiled wet wall 12.00 m2 (FIN.WALL.TILE): NO bed (UPC-WETWALL-001), its render is the plaster trade's.
  ST1 a doorway strip, finish EXCLUDED: no bed, NOT_APPLICABLE. FH1 a finish-HELD floor with no bed pair: MISSING.
"""

import copy
import json
import math
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "research" / "agents_t500"))

import t500_tile_bed_mortar as M  # noqa: E402
from engine.source import finish_materials_table as V1  # noqa: E402


def shoelace(pts, unit_m=1.0):
    a = 0.0
    for (x1, y1), (x2, y2) in zip(pts, pts[1:] + pts[:1]):
        a += x1 * y2 - x2 * y1
    return round(abs(a) / 2.0 * unit_m * unit_m, 6)


def _ln(i, code, eid, cls, net=None, lo=None, hi=None, unit="m2"):
    return {"line_id": i, "item_code": code, "element_id": eid, "class": cls, "unit": unit, "measured_net": net,
            "held_low": lo, "held_high": hi}


def bed_pair(prefix, kind, eid, area):
    code = "FIN.FLOOR.BED.DRY" if kind == "DRY" else "FIN.FLOOR.BED.WET"
    lo, hi = (0.03, 0.04) if kind == "DRY" else (0.04, 0.06)
    return [_ln(prefix + "a", code, eid + ":bed", "RELEASED", area),
            _ln(prefix + "v", code, eid + ":bed", "HELD", None, round(area * lo, 6), round(area * hi, 6), "m3")]


R1 = [(0, 0), (6.0, 0), (6.0, 4.5), (0, 4.5)]
B1 = [(10.0, 0), (12.4, 0), (12.4, 1.8), (10.0, 1.8)]


def villa(r1=R1, b1=B1, unit_m=1.0):
    a1, a2 = shoelace(r1, unit_m), shoelace(b1, unit_m)
    return ([_ln("F1", "FIN.FLOOR.PORCELAIN", "GF-R1:floor", "RELEASED", a1),
             _ln("F2", "FIN.FLOOR.WET_TILE", "GF-B1:floor", "RELEASED", a2),
             _ln("WW1", "FIN.WALL.TILE", "GF-B1:wall", "RELEASED", 12.0),
             _ln("ST1", "FIN.FLOOR.PORCELAIN", "GF-ST1:doorway strip", "EXCLUDED"),
             _ln("FH1", "FIN.FLOOR.FINISH_HELD", "GF-FH1", "HELD", None, 0.0, 0.5)]
            + bed_pair("BR1", "DRY", "GF-R1:floor", a1) + bed_pair("BB1", "WET", "GF-B1:floor", a2))


def _row(t, i):
    return next(r for r in t["rows"] if r["id"] == i)


# ------------------------------------------------------------------ normal case, by hand

def test_fixture_by_hand():
    t = M.table(villa())
    assert t["fails"] == []
    r = _row(t, "BR1v")
    assert (r["area_m2"], r["installed_m3_low"], r["installed_m3_high"]) == (27.0, 0.81, 1.08)
    assert (r["cement_bags_low"], r["cement_bags_high"]) == (6.48, 8.64)
    assert (r["sand_m3_low"], r["sand_m3_high"]) == (0.891, 1.188)
    assert (r["waste_cement_bags_low"], r["waste_cement_bags_high"]) == (0.324, 0.432)
    assert (r["waste_sand_m3_low"], r["waste_sand_m3_high"]) == (0.04455, 0.0594)
    assert (r["procurement_cement_bags_low"], r["procurement_cement_bags_high"]) == (6.804, 9.072)
    assert (r["procurement_sand_m3_low"], r["procurement_sand_m3_high"]) == (0.93555, 1.2474)
    assert r["status"] == "BOUND" and r["evidence_status"] == "ASSUMED — OWNER-APPROVED"
    b = _row(t, "BB1v")
    assert (b["area_m2"], b["installed_m3_low"], b["installed_m3_high"]) == (4.32, 0.1728, 0.2592)
    assert (b["cement_bags_low"], b["cement_bags_high"]) == (1.3824, 2.0736)
    assert (b["sand_m3_low"], b["sand_m3_high"]) == (0.19008, 0.28512)
    assert (b["procurement_cement_bags_low"], b["procurement_cement_bags_high"]) == (1.45152, 2.17728)
    p = t["subtotals"]["PROJECT"]
    assert (p["installed_m3_low"]["value"], p["installed_m3_high"]["value"]) == (0.9828, 1.3392)
    assert (p["cement_bags_low"]["value"], p["cement_bags_high"]["value"]) == (7.8624, 10.7136)
    assert (p["procurement_cement_bags_low"]["value"], p["procurement_cement_bags_high"]["value"]) == (8.25552, 11.24928)
    assert (p["cement_bags_to_buy_low"], p["cement_bags_to_buy_high"]) == (9, 12)


def test_measure_pair_and_completeness():
    t = M.table(villa())
    assert {r["id"] for r in t["pair_rows"]} == {"BR1a", "BB1a"}
    assert all(r["binding"] == "NOT_APPLICABLE_WITH_EVIDENCE" for r in t["pair_rows"])
    states = {h["finish_line"]: h["state"] for h in t["hosts"]}
    assert states == {"F1": "BEDDED", "F2": "BEDDED", "ST1": "NOT_APPLICABLE_WITH_EVIDENCE", "FH1": "MISSING_BED_LINE"}
    assert [w["id"] for w in t["walls"]] == ["WW1"] and t["walls"][0]["binding"] == "NOT_APPLICABLE_WITH_EVIDENCE"


def test_no_mid_value_and_waste_separate():
    r = _row(M.table(villa()), "BR1v")
    assert r["installed_m3_low"] < r["installed_m3_high"]
    assert "installed_m3" not in r and "cement_bags" not in r       # never one chosen thickness
    assert math.isclose(r["procurement_cement_bags_low"], r["cement_bags_low"] + r["waste_cement_bags_low"])


def test_agrees_with_v1_owner_table():
    """Independent route: V1.materials folds the 5 % waste into the mortar; its cement = this table's procurement."""
    t = M.table(villa())
    for rid, kind, area in (("BR1v", V1.DRY_FLOOR, 27.0), ("BB1v", V1.WET_FLOOR, 4.32)):
        v = V1.materials(kind, V1.PORCELAIN_CERAMIC, area)
        r = _row(t, rid)
        assert math.isclose(v["cement_bags_low"], r["procurement_cement_bags_low"], abs_tol=1e-5)
        assert math.isclose(v["cement_bags_high"], r["procurement_cement_bags_high"], abs_tol=1e-5)
        assert math.isclose(v["sand_m3_high"], r["procurement_sand_m3_high"], abs_tol=1e-5)


# ------------------------------------------------------------------ geometry invariance and units

def _cement(t):
    p = t["subtotals"]["PROJECT"]
    return p["cement_bags_low"]["value"], p["cement_bags_high"]["value"]


def test_mirror_rotation_and_mm_give_the_same_materials():
    base = _cement(M.table(villa()))
    mirror = [(-x, y) for x, y in R1]
    rot = [(-y, x) for x, y in B1]
    assert _cement(M.table(villa(mirror, rot))) == base
    mm = [(x * 1000, y * 1000) for x, y in R1], [(x * 1000, y * 1000) for x, y in B1]
    assert _cement(M.table(villa(*mm, unit_m=0.001))) == base
    assert _cement(M.table(list(reversed(villa())))) == base       # input order


def test_wrong_unit_fails_and_yields_nothing():
    ls = villa()
    next(x for x in ls if x["line_id"] == "BR1v")["unit"] = "mm3"
    t = M.table(ls)
    assert any(f["kind"] == "UNIT" for f in t["fails"])
    assert all(r["id"] != "BR1v" or r["cement_bags_low"] is None for r in t["rows"])


def test_area_read_as_mm2_is_caught_by_the_band_check():
    ls = villa()
    next(x for x in ls if x["line_id"] == "BR1a")["measured_net"] = 27.0e6     # mm2 typed as m2
    t = M.table(ls)
    assert [f["kind"] for f in t["fails"]] == ["BAND_MISMATCH"]
    assert _row(t, "BR1v")["cement_bags_low"] is None


# ------------------------------------------------------------------ adverse: held, never 0

def test_held_bed_thickness_stays_held_and_subtotal_at_least():
    ls = villa()
    v = next(x for x in ls if x["line_id"] == "BB1v")
    v["held_low"] = v["held_high"] = None                       # bed thickness HELD on the wet bed
    t = M.table(ls)
    assert t["fails"] == []
    b = _row(t, "BB1v")
    assert b["status"] == "HELD" and b["cement_bags_low"] is None and b["procurement_cement_bags_high"] is None
    assert b["reason"].startswith("BED_RANGE_HELD")
    p = t["subtotals"]["PROJECT"]
    assert p["cement_bags_low"]["value"] is None and p["cement_bags_low"]["status"] == "HELD"
    assert p["cement_bags_low"]["at_least"] == 6.48 and p["cement_bags_low"]["held_rows"] == ["BB1v"]
    assert p["cement_bags_to_buy_low"] is None and p["cement_bags_to_buy_high"] is None
    # the dry group alone is determinate: procurement 6.804 .. 9.072 -> 7 .. 10 whole bags
    assert t["subtotals"]["FIN.FLOOR.BED.DRY"]["cement_bags_to_buy_low"] == 7
    assert t["subtotals"]["FIN.FLOOR.BED.DRY"]["cement_bags_to_buy_high"] == 10


def test_mix_without_per_m3_figure_is_held():
    vals = copy.deepcopy(V1.OWNER_VALUES)
    vals["per_m3_of_mortar"] = {}
    t = M.table(villa(), values=vals)
    r = _row(t, "BR1v")
    assert r["status"] == "HELD" and r["installed_m3_low"] == 0.81 and r["cement_bags_low"] is None
    assert r["reason"] == "MIX_1:4_PER_M3_NOT_GIVEN"


def test_no_held_row_prints_zero_on_candidate_and_fixture():
    for t in (M.table(villa()), M.run()):
        for r in t["rows"]:
            if r["status"] != "BOUND":
                assert all(r[k] is None for k in M.KEYS if k != "area_m2")
        assert not any(f["kind"] == "ZERO_FOR_HELD" for f in t["fails"])


# ------------------------------------------------------------------ adverse: double count, walls, scope

def test_tiled_wet_wall_never_takes_a_second_bed():
    assert M.wet_wall_bed({"id": "WW1"})["binding"] == "NOT_APPLICABLE_WITH_EVIDENCE"
    with pytest.raises(M.BedError):
        M.wet_wall_bed({"id": "WW1", "bed_m": 0.02})
    ls = villa() + bed_pair("BW1", "WET", "GF-B1:wall", 12.0)          # someone bedded the wet wall
    t = M.table(ls)
    assert any(f["kind"] == "WALL_BED" and f["where"] == "WW1" for f in t["fails"])


def test_double_and_lone_lines_fail():
    ls = villa() + [M_ for M_ in bed_pair("BX1", "DRY", "GF-R1:floor", 27.0)]
    assert any(f["kind"] == "DOUBLE_LINE" for f in M.table(ls)["fails"])
    lone = [x for x in villa() if x["line_id"] != "BB1v"]
    assert any(f["kind"] == "LONE_LINE" and f["where"] == "BB1a" for f in M.table(lone)["fails"])


def test_band_drift_fails():
    ls = villa()
    next(x for x in ls if x["line_id"] == "BR1v")["held_high"] = 1.20      # 4.44 cm: not the owner band
    t = M.table(ls)
    assert [f["kind"] for f in t["fails"]] == ["BAND_MISMATCH"]


def test_owned_elsewhere_and_orphan():
    ls = villa() + [_ln("SB1", "FIN.STAIR.BED", "GF-S1:bed", "HELD", None, 0.1, 0.1, "m3"),
                    _ln("OB1", "FIN.FLOOR.BED.DRY", "GF-NOFIN:floor:bed", "RELEASED", 5.0),
                    _ln("OB2", "FIN.FLOOR.BED.DRY", "GF-NOFIN:floor:bed", "HELD", None, 0.15, 0.2, "m3")]
    kinds = {f["kind"] for f in M.table(ls)["fails"]}
    assert {"OWNED_ELSEWHERE", "ORPHAN_BED"} <= kinds


# ------------------------------------------------------------------ the candidate V3.0.53 (training villa)

def test_candidate_census_88_of_88():
    m = M.run()
    c = m["census"]
    assert m["fails"] == []
    assert (c["bed_lines"], c["accounted"], c["bound"], c["held"], c["pair_m2_not_applicable"]) == (88, 88, 44, 0, 44)
    assert c["hosts_by_state"] == {"BEDDED": 44, "MISSING_BED_LINE": 1, "NOT_APPLICABLE_WITH_EVIDENCE": 13}
    assert c["wall_tile_lines_not_applicable"] == 18
    missing = [h for h in m["hosts"] if h["state"] == "MISSING_BED_LINE"]
    assert [h["item_code"] for h in missing] == ["FIN.FLOOR.FINISH_HELD"] and missing[0]["class"] == "HELD"


def test_candidate_totals():
    p = M.run()["subtotals"]
    assert p["FIN.FLOOR.BED.WET"]["area_m2"]["value"] == 85.575578            # = the T-420 wet total, unchanged
    assert p["FIN.FLOOR.BED.WET"]["installed_m3_low"]["value"] == 3.423023
    assert p["FIN.FLOOR.BED.WET"]["installed_m3_high"]["value"] == 5.134535
    P = p["PROJECT"]
    assert P["area_m2"]["value"] == 387.09405                                 # = T-471 matrix C-B3-05 387.094 m2
    assert (P["installed_m3_low"]["value"], P["installed_m3_high"]["value"]) == (12.468577, 17.195274)
    assert (P["cement_bags_low"]["value"], P["cement_bags_high"]["value"]) == (99.748616, 137.562192)
    assert (P["sand_m3_low"]["value"], P["sand_m3_high"]["value"]) == (13.715435, 18.914801)
    assert (P["cement_bags_to_buy_low"], P["cement_bags_to_buy_high"]) == (105, 145)


def test_candidate_two_lines_by_hand():
    rows = {r["element_id"]: r for r in M.run()["rows"]}
    d = rows["1F-R0E919A:floor:bed"]                  # dry 16.34 m2
    assert (d["installed_m3_low"], d["installed_m3_high"]) == (0.4902, 0.6536)
    assert (d["cement_bags_low"], d["cement_bags_high"]) == (3.9216, 5.2288)
    assert (d["sand_m3_low"], d["sand_m3_high"]) == (0.53922, 0.71896)
    w = rows["HL:FLOOR_SCOPE:WET:GF:GF-PANTRY-RC06FED:bed"]      # wet 2.800001 m2
    assert (w["installed_m3_low"], w["installed_m3_high"]) == (0.112, 0.168)
    assert (w["cement_bags_low"], w["cement_bags_high"]) == (0.896, 1.344)
    assert (w["sand_m3_low"], w["sand_m3_high"]) == (0.1232, 0.1848)


def test_candidate_agrees_with_v1_line_by_line():
    m = M.run()
    for r in m["rows"]:
        kind = V1.DRY_FLOOR if r["kind"] == M.DRY else V1.WET_FLOOR
        v = V1.materials(kind, None, r["area_m2"])
        assert math.isclose(v["cement_bags_low"], r["procurement_cement_bags_low"], abs_tol=1e-5), r["id"]
        assert math.isclose(v["cement_bags_high"], r["procurement_cement_bags_high"], abs_tol=1e-5), r["id"]


def test_pins_and_stale_candidate(tmp_path, monkeypatch):
    bad = tmp_path / "idx.json"
    bad.write_text(M.INDEX.read_text(encoding="utf-8").replace("RELEASED", "RELEASED ", 1), encoding="utf-8")
    monkeypatch.setattr(M, "INDEX", bad)
    monkeypatch.setitem(M.PINS, bad, M.PINS[ROOT / "research/agents_t487/out/LINE_INDEX_V3_0_51.json"])
    with pytest.raises(M.BedError, match="PIN"):
        M.candidate_lines()


def test_committed_output_is_the_rebuild(tmp_path):
    M.write(M.run(), tmp_path)
    for name in ("TILE_BED_MORTAR_T500.json", "TILE_BED_MORTAR_T500.csv"):
        assert (tmp_path / name).read_bytes() == (ROOT / "research/agents_t500/out" / name).read_bytes()
