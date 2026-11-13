"""T-740 paint area rule UP-FIN-PAINT-002 1.0.0 (R-T740-1 .. -3): synthetic villa V740 by hand (normal + adverse) and
the development villa pinned to the committed outputs.

Villa V740 (synthetic, not the development villa), by hand:
  room A (NORMAL): face 12.00 lm, plaster top 3.00, no false ceiling (paint top 3.00), one door 0.90 x 2.10 = 1.89
      plaster = 12.00 x 3.00 - 1.89 = 34.11; band 0; tiled 0 -> paint 34.11 = plaster
  room B (ADVERSE, false ceiling): face 14.00 lm, plaster to the soffit 3.20, false ceiling 2.80 (band height 0.40);
      window w 1.50 sill 1.00 head 3.00 -> plaster 3.00, band part 1.50 x (3.00 - 2.80) = 0.30;
      one beam b 0.25 x 0.60 below the soffit, 2 ends -> plaster 0.30, in band 2 x 0.25 x 0.40 = 0.20,
      below the ceiling 2 x 0.25 x 0.20 = 0.10
      plaster = 14.00 x 3.20 - 3.00 - 0.30 = 41.50; band = 14.00 x 0.40 - 0.30 - 0.20 = 5.10 -> paint 36.40
      check from below: 14.00 x 2.80 - 1.50 x 1.80 - 0.10 = 39.20 - 2.70 - 0.10 = 36.40
      an engine paint line of 36.50 (beam end not deducted) -> named BEAM_END_BELOW_CEILING 0.10, residual 0
  room C (ADVERSE, wet): face 8.00 lm, render to the tile top = ceiling 2.60, door 0.80 x 2.10 = 1.68
      plaster (render) 20.80 - 1.68 = 19.12 = tiled 19.12 -> NO paint face (0 by the rule)
  room D (ADVERSE, tile on part height): face 10.00 lm, plaster 3.00 no ceiling = 30.00; splashback 4.00 lm x
      (1.50 - 0.90) = 2.40 tiled -> paint 27.60
  HELD plaster -> HELD paint (never 0); band not established -> AT_MOST plaster high; ranges paired low / high:
      plaster 40 .. 44, band 5 .. 6 -> paint 35 .. 38; mirror / rotation cannot change an area: the same face read in
      the other direction (sill / head swapped by a mirrored section) is refused, not silently reversed.
"""
import hashlib
import json
import subprocess
import sys
from decimal import Decimal
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "research" / "agents_t740"
sys.path.insert(0, str(HERE))
import t740_rules as R  # noqa: E402

OUT = HERE / "out" / "T740_PAINT_RULE.json"
D = Decimal


def p(res):
    return tuple(str(x) for x in res["paint"]) if res["paint"] else None


# ---------------------------------------------------------------- R-T740-1 normal
def test_normal_room_without_ceiling_or_tile_paint_equals_plaster():
    plaster = D("12.00") * D("3.00") - D("0.90") * D("2.10")
    assert plaster == D("34.1100")
    _, b = R.band("12.00", "3.00", "3.00", [])
    assert b == 0
    res = R.paint_face(plaster, b, 0)
    assert res["status"] == "RULE" and p(res) == ("34.110000", "34.110000")


def test_edges_are_lm_beside_the_area_never_added():
    res = R.paint_face("30", edges_lm="12")
    assert p(res) == ("30.000000", "30.000000") and res["edges_lm"] == "12.000000"


# ---------------------------------------------------------------- R-T740-1 / -2 adverse
def test_false_ceiling_band_with_window_and_beam_end():
    w_pl = D("1.50") * R.overlap("1.00", "3.00", 0, "3.20")
    w_band = R.opening_band_part("1.50", "1.00", "3.00", "2.80", "3.20")
    inb, below = R.beam_end_split("0.25", "0.60", "0.40", 2)
    assert (w_pl, w_band, inb, below) == (D("3.00"), D("0.30"), D("0.200000"), D("0.100000"))
    plaster = D("14.00") * D("3.20") - w_pl - (inb + below)
    assert plaster == D("41.500000")
    gross, band = R.band("14.00", "3.20", "2.80", [w_band, inb])
    assert (gross, band) == (D("5.600000"), D("5.100000"))
    res = R.paint_face(plaster, band, 0)
    assert p(res) == ("36.400000", "36.400000")
    # the same paint from below the ceiling
    assert D("14.00") * D("2.80") - R.opening_paint_part("1.50", "1.00", "3.00", "2.80") - below == D("36.400000")
    al = R.allocate(plaster, "36.50", band, 0, [("BEAM_END_BELOW_CEILING", below)])
    assert al["rule_paint"] == D("36.400000") and al["residual"] == 0
    assert al["gap"] == D("5.000000")


def test_wholly_tiled_wet_face_has_no_paint_face():
    render = D("8.00") * D("2.60") - D("0.80") * D("2.10")
    res = R.paint_face(render, 0, render)
    assert res["status"] == "NO_PAINT_FACE" and p(res) == ("0.000000", "0.000000")


def test_tile_on_part_height_is_deducted():
    tiled = D("4.00") * (D("1.50") - D("0.90"))
    res = R.paint_face(D("10.00") * D("3.00"), 0, tiled)
    assert p(res) == ("27.600000", "27.600000")


def test_held_plaster_face_stays_held_never_zero():
    res = R.paint_face(None, 0, 0)
    assert res["status"] == "HELD" and res["paint"] is None and res["high"] is None
    res = R.paint_face((None, "40"), 0, 0)
    assert res["status"] == "HELD"


def test_unknown_band_gives_at_most():
    res = R.paint_face(("40", "44"), None, 0)
    assert res["status"] == "AT_MOST" and res["paint"] is None and res["high"] == D("44.000000")
    res = R.paint_face(("40", "44"), (None, "6"), 0)
    assert res["status"] == "AT_MOST" and res["high"] == D("38.000000")


def test_ranges_pair_low_with_low():
    res = R.paint_face(("40", "44"), ("5", "6"), 0)
    assert p(res) == ("35.000000", "38.000000")


def test_refusals():
    with pytest.raises(R.RuleError):
        R.paint_face("10", "8", "3")                      # band + tile exceed the face
    with pytest.raises(R.RuleError):
        R.paint_face("-1")                                # negative area
    with pytest.raises(R.RuleError):
        R.opening_band_part("1.5", "1000", "3000", "2.8", "3.2")   # mm, not m
    with pytest.raises(R.RuleError):
        R.overlap("3.00", "1.00", 0, "3.2")               # mirrored section: head below sill is refused
    with pytest.raises(R.RuleError):
        R.band("10", "2.8", "3.2", [])                    # paint top above the plaster top
    with pytest.raises(R.RuleError):
        R.band("10", "3.2", "2.8", ["5"])                 # deductions bigger than the band
    with pytest.raises(R.RuleError):
        R.beam_end_split("0.25", "0.6", "0.4", "1.5")     # ends are a whole count
    with pytest.raises(R.RuleError):
        R.allocate("10", "9", "1", "0", [("GUESS", "1")])  # unknown cause
    with pytest.raises(R.RuleError):
        R.paint_faces({"A": "10"}, {"B": "1"})             # paint band on a face with no plaster: refused
    with pytest.raises(R.RuleError):
        R.D(None)


def test_paint_faces_many():
    out = R.paint_faces({"A": "34.11", "B": "41.5", "C": "19.12", "H": None}, {"B": "5.1"}, {"C": "19.12"})
    assert p(out["A"]) == ("34.110000", "34.110000")
    assert p(out["B"]) == ("36.400000", "36.400000")
    assert out["C"]["status"] == "NO_PAINT_FACE"
    assert out["H"]["status"] == "HELD"


# ---------------------------------------------------------------- rule version file
BOOKS = {"rules/rulebook/URBAN_COMPANY_RULEBOOK_1.0.0.json": "4e9c57cef33d32ede26bea4eaf3823e2dc3880d56708dd18ec5df3760b84c055",
         "rules/rulebook/URBAN_COMPANY_RULEBOOK_1.1.0.json": "da38d121eec33c00ff3c8b524ed022be6a66f5789fdd9a0cd37f216f84dcde35",
         "knowledge/URBAN_ENGINEERING_KNOWLEDGE_1.7.0.json": "22e2cdf5ddf4044d52d9961f2c218e7c76d955d26b7f835d24c0552547010c56"}


def test_existing_version_files_untouched():
    for rel, h in BOOKS.items():
        assert hashlib.sha256((ROOT / rel).read_bytes()).hexdigest() == h, rel


def test_rulebook_1_2_0_is_1_1_0_plus_one_record():
    old = json.loads((ROOT / "rules/rulebook/URBAN_COMPANY_RULEBOOK_1.1.0.json").read_text(encoding="utf-8"))
    new = json.loads((ROOT / "rules/rulebook/URBAN_COMPANY_RULEBOOK_1.2.0.json").read_text(encoding="utf-8"))
    assert new["version"] == "1.2.0" and new["supersedes"] == "1.1.0"
    assert new["records"][:-1] == old["records"]
    rec = new["records"][-1]
    assert rec["rule_id"] == R.RULE_ID and rec["version"] == R.RULE_VERSION and rec["status"] == "OWNER_CONFIRMED"
    assert "the Area is the same" in rec["source"] and rec["supersedes_in_scope"].startswith("UP-FIN-PAINT-001@1.0.0")
    r = subprocess.run([sys.executable, "-I", str(HERE / "build_rulebook_1_2_0.py"), "--check"],
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr


# ---------------------------------------------------------------- development villa (pinned)
@pytest.fixture(scope="module")
def out():
    return json.loads(OUT.read_text(encoding="utf-8"))


def test_builder_reproduces_committed_outputs():
    r = subprocess.run([sys.executable, "-I", str(HERE / "t740_alsenan.py"), "--check"], capture_output=True, text=True)
    assert r.returncode == 0 and "match" in r.stdout, r.stdout + r.stderr


def test_census_is_the_board_figures(out):
    c = out["census_board"]
    assert c["FIN.PLASTER"]["held"] == ["1106.948597", "1302.168817"] and c["FIN.PLASTER"]["released"] == "388.584360"
    assert c["FIN.PAINT"]["held"] == ["604.990059", "710.006421"] and c["FIN.PAINT"]["released"] == "217.208100"
    assert out["totals"]["plaster"] == c["FIN.PLASTER"]["total"]
    assert out["totals"]["engine_paint"] == c["FIN.PAINT"]["total"]


def test_gap_fully_allocated(out):
    for e in ("low", "high"):
        assert out["allocation"][e]["residual"] == "0.000000"
    for r in out["dry_rooms"]:
        for e in r["ends"]:
            assert e["residual"] == Decimal(0) or e["residual"] == "0.000000"


def test_rule_paint_totals(out):
    assert out["totals"]["rule_paint"] == ["841.260635", "929.204847"]
    s = out["paint_by_engine_class"]
    assert s["RELEASED"]["lines"] == 4 and s["RELEASED"]["rule_paint"] == ["217.208150", "217.208150"]
    assert s["HELD"]["lines"] == 38 and s["HELD"]["rule_paint"] == ["624.052485", "711.996697"]


def test_named_findings(out):
    rooms = {r["room"]: r for r in out["dry_rooms"]}
    w17 = [n for e in rooms["1F-11"]["ends"] for n in e["named"]]
    assert [n["m2"] for n in w17] == ["0.861450", "-4.305350"]
    assert rooms["1F-11"]["rule_paint"] == ["60.601150", "66.023050"]
    gf01 = [n["m2"] for e in rooms["GF-01"]["ends"] for n in e["named"]]
    assert gf01 == ["0.010824", "2.314774"]
    beams = sorted(n["m2"] for r in out["dry_rooms"] for e in r["ends"] for n in e["named"]
                   if n["cause"] == "BEAM_END_BELOW_CEILING")
    assert beams == ["0.065000", "0.090000", "0.160000"]
    cls = out["by_class"]
    assert cls["RETURN"]["rule_paint"] == ["20.250000", "24.150000"]
    assert cls["WET_RENDER"]["rule_paint"] == ["0.000000", "0.000000"]
    assert cls["SHAFT"]["band"] == ["1.950000", "1.950000"]


def test_no_held_face_became_zero(out):
    for f in out["faces"]:
        if f["plaster"] is None:
            assert f["rule_paint"] is None, f["plaster_element"]
