"""T-561: wall paint vs the freelancer by face class (research/agents_t561, R-T561-1).
Synthetic villa "P561" (not the training villa), hand calculations; adverse cases; then the development villa pins
(repository inputs only: candidate line index, T-128 / T-173 / T-281 / T-552 merged ledgers, the parsed freelancer
cells)."""
from __future__ import annotations

import json
import subprocess
import sys
from decimal import Decimal
from itertools import permutations
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t561"))
import t561_paint_rules as R  # noqa: E402

Dc = Decimal
SRC = {"interval": "P561 section S-1 marks +0.00 / +4.00", "beam": "owner G1 0.60", "decor": "P561 RCP decor 0.15",
       "floor": "owner G1 0.10", "slab": "P561 S-0 note: slabs 16 cm", "buildup": "P561 F-1 not printed 0 .. 0.10",
       "level": "P561 RCP ceiling +3.00"}
DOOR = {"id": "D1", "width": "0.90", "height": "2.20", "sill": "0"}


# ---- villa "P561" bedroom (hand): 4.00 x 5.00 m, run 18.00 lm, finished ceiling printed at 3.00 m, one door
# 0.90 x 2.20 = 1.98; two coats. Area = 18.00 x 3.00 - 1.98 = 52.02 m2 (NOT 104.04: coats are a rate).
def test_room_paint_area_by_hand_two_coats_is_a_rate():
    h = R.paint_height(basis="PRINTED_CEILING_LEVEL", level="3.00", sources=SRC)
    assert h == (Dc("3.00"), Dc("3.00"))
    out = R.net_wall_paint(run_lm="18.00", height=h[0], openings=[DOOR], coats=2)
    assert (out["gross"], out["deductions"], out["net"], out["coats_rate"]) == (Dc("54.00"), Dc("1.98"), Dc("52.02"), 2)
    assert out["net"] != Dc("104.04")


def test_coats_multiplied_into_area_refused():
    with pytest.raises(R.PaintError, match="coats"):
        R.net_wall_paint(run_lm="18.00", height="3.00", openings=[DOOR], area_multiplier=2)
    comp = {"name": "his two coats", "qty": "52.02", "sign": 1, "cause": "RULE_DIFFERENCE", "source": "P561 spec",
            "coats_multiplier": 2}
    with pytest.raises(R.PaintError, match="coats"):
        R.bridge(pair_class="DRY", freelancer_gross="104.04", engine_lines=[], components=[comp], residual_name="r")


def test_two_methods_owner_g1_and_drawing_derived_by_hand():
    # owner G1: 4.00 - 0.60 - 0.15 - 0.10 = 3.15; drawing: 4.00 - 0.16 - (0 .. 0.10) - 0.15 = 3.59 .. 3.69
    assert R.paint_height(basis="OWNER_G1_ROOM_FORMULA", interval="4.00", beam="0.60", decor="0.15", floor="0.10",
                          sources=SRC) == (Dc("3.15"), Dc("3.15"))
    assert R.paint_height(basis="DRAWING_FINISHED_CEILING", interval="4.00", slab="0.16", buildup=("0", "0.10"),
                          decor="0.15", sources=SRC) == (Dc("3.59"), Dc("3.69"))


@pytest.mark.parametrize("basis", ["SLAB_UNDERSIDE", "ROOF_UNDERSIDE", "PLASTER_HEIGHT"])
def test_plaster_height_basis_refused_for_paint(basis):
    with pytest.raises(R.PaintError, match="plaster height"):
        R.paint_height(basis=basis, interval="4.00", slab="0.16", buildup="0.10", decor="0.15", sources=SRC)
    comp = {"name": "height", "qty": "1.0", "sign": 1, "cause": "RULE_DIFFERENCE", "source": "P561",
            "height_basis": basis}
    with pytest.raises(R.PaintError, match="plaster height basis"):
        R.bridge(pair_class="DRY", freelancer_gross="1.0", engine_lines=[], components=[comp], residual_name="r")


def test_missing_term_or_source_is_held_never_default():
    with pytest.raises(R.PaintError, match="decor not given"):
        R.paint_height(basis="DRAWING_FINISHED_CEILING", interval="4.00", slab="0.16", buildup="0", sources=SRC)
    with pytest.raises(R.PaintError, match="no source"):
        R.paint_height(basis="OWNER_G1_ROOM_FORMULA", interval="4.00", beam="0.60", decor="0.15", floor="0.10",
                       sources={"interval": "x", "beam": "y", "decor": "z"})


# ---- P561 kitchen: run 14.00 lm, ceiling 3.00, wall tile to +1.20 (printed): paint band 1.80 x 14.00 = 25.20;
# window 1.20 wide, sill 1.00, head 2.50 -> inside the band 1.20 .. 2.50 = 1.30 x 1.20 = 1.56; door 0.90 x 2.20 ->
# 1.20 .. 2.20 = 1.00 x 0.90 = 0.90. Net 25.20 - 1.56 - 0.90 = 22.74 m2.
def test_paint_band_above_a_part_height_tile_by_hand():
    w = {"id": "W1", "width": "1.20", "height": "1.50", "sill": "1.00"}
    out = R.net_wall_paint(run_lm="14.00", height="3.00", openings=[w, DOOR], tile_top="1.20")
    assert (out["band_height"], out["gross"], out["deductions"], out["net"]) == (Dc("1.80"), Dc("25.20"), Dc("2.46"),
                                                                                  Dc("22.74"))


def test_full_height_tile_is_never_painted():
    with pytest.raises(R.PaintError, match="UP-FIN-PAINT-001"):
        R.net_wall_paint(run_lm="10", height="3.00", openings=[], full_height_tile=True)
    with pytest.raises(R.PaintError, match="no paint band"):
        R.net_wall_paint(run_lm="10", height="3.00", openings=[], tile_top="3.00")
    with pytest.raises(R.PaintError, match="painted and tiled"):
        R.check_face_classes([{"face_id": "F1", "cls": "WET", "painted": True, "tiled_full": True}])


def test_window_sill_unknown_inside_a_band_is_held():
    with pytest.raises(R.PaintError, match="sill not established"):
        R.net_wall_paint(run_lm="14", height="3.00", openings=[{"id": "W2", "width": "1.0", "height": "1.5"}],
                         tile_top="1.20")
    with pytest.raises(R.PaintError, match="height not established"):
        R.net_wall_paint(run_lm="14", height="3.00", openings=[{"id": "W3", "width": "1.0", "height": None}])


def _comps():
    return [{"name": "openings", "qty": "1.98", "sign": 1, "cause": "RULE_DIFFERENCE", "source": "P561 Q-73"},
            {"name": "height his 3.10 vs 3.00", "qty": "1.80", "sign": 1, "cause": "RULE_DIFFERENCE",
             "source": "P561 RCP"},
            {"name": "length his 17.50 vs 18.00", "qty": "1.55", "sign": -1, "cause": "ENGINE_RIGHT",
             "source": "P561 plan"}]


def test_bridge_exact_and_order_invariant():
    # his 17.50 x 3.10 = 54.25 gross; engine 52.02: gap 2.23 = 1.98 + 1.80 - 1.55; residual 0
    eng = [{"line_id": "P-1", "cls": "DRY", "qty": "52.02", "unit": "m2"}]
    outs = set()
    for p in permutations(_comps()):
        b = R.bridge(pair_class="DRY", freelancer_gross="54.25", engine_lines=eng, components=list(p),
                     residual_name="r")
        outs.add((b["gap"], b["residual"], tuple(sorted(b["by_cause"].items()))))
    assert outs == {("2.23", "0.00", (("ENGINE_RIGHT", "-1.55"), ("RULE_DIFFERENCE", "3.78")))}


def test_soffit_in_a_wall_pair_refused_and_held_never_zero():
    c = {"name": "stair soffit", "qty": "4.0", "sign": 1, "cause": "HELD", "source": "P561 stair", "face_class": "CEILING"}
    with pytest.raises(R.PaintError, match="ceiling face"):
        R.bridge(pair_class="DRY", freelancer_gross="4.0", engine_lines=[], components=[c], residual_name="r")
    assert R.bridge(pair_class="CEILING", freelancer_gross="4.0", engine_lines=[], components=[c],
                    residual_name="r")["residual"] == "0.0"
    with pytest.raises(R.PaintError, match="never 0"):
        R.bridge(pair_class="DRY", freelancer_gross="4.0", engine_lines=[],
                 components=[dict(c, face_class=None, qty=None)], residual_name="r")
    with pytest.raises(R.PaintError, match="HELD lines"):
        R.bridge(pair_class="DRY", freelancer_gross="4.0",
                 engine_lines=[{"line_id": "P-2", "cls": "DRY", "qty": None, "unit": "m2"}], components=[],
                 residual_name="r")


def test_freelancer_figure_as_component_and_lm_refused():
    with pytest.raises(R.PaintError, match="source"):
        R.bridge(pair_class="DRY", freelancer_gross="1", engine_lines=[],
                 components=[{"name": "x", "qty": "1", "sign": 1, "cause": "HELD", "source": "freelancer row 7"}],
                 residual_name="r")
    with pytest.raises(R.PaintError, match="m2"):
        R.bridge(pair_class="DRY", freelancer_gross="1", engine_lines=[],
                 components=[{"name": "x", "qty": "1", "sign": 1, "cause": "HELD", "source": "P561", "unit": "lm"}],
                 residual_name="r")


# ---- development villa pins (repository inputs only)
OUT = ROOT / "research" / "agents_t561" / "out" / "T561_PAINT_RECONCILE.json"


@pytest.fixture(scope="module")
def dev():
    return json.loads(OUT.read_text())


def test_dev_rebuild_byte_identical():
    r = subprocess.run([sys.executable, "-I", str(ROOT / "research/agents_t561/t561_alsenan.py"), "--check"],
                       capture_output=True, text=True)
    assert r.returncode == 0 and "byte-identical" in r.stdout, r.stdout + r.stderr


def test_dev_bridge_sums_exactly(dev):
    i = dev["internal"]
    assert (i["freelancer_gross"], i["engine_valued"], i["gap_gross"]) == ("1249.375", "217.2081", "1032.1669")
    assert sum(Dc(v) for v in i["by_cause"].values()) == Dc(i["gap_gross"])
    assert Dc(i["freelancer_gross"]) - Dc(i["his_half_deduction"]) == Dc(i["freelancer_net"])
    for p in i["pairs"].values():
        assert sum(Dc(r["delta"]) for r in p["rows"]) == Dc(p["gap"])
    assert sum(Dc(p["freelancer_gross"]) for p in i["pairs"].values()) == Dc("1249.375")


def test_dev_paint_is_his_plaster_plus_stair_soffits(dev):
    c = dev["cross_check_T552"]
    assert c["dry_pair_identical_to_T552"] is True
    assert Dc(c["paint_minus_plaster_his_gross"]) == Dc("39.99") == Dc(c["equals_his_soffit_rows"])
    so = dev["internal"]["pairs"]["CEILING (stair soffits in his wall paint)"]
    assert so["class"] == "CEILING" and so["by_cause"]["HELD"] == "22.149034"


def test_dev_wet_row_and_returns_and_shaft(dev):
    p = dev["internal"]["pairs"]
    wet = [r for r in p["DRY"]["rows"] if r["name"].startswith("GF-02 wet space")]
    assert len(wet) == 1 and wet[0]["cause"] == "RULE_DIFFERENCE" and "UP-FIN-PAINT-001" in wet[0]["source"]
    assert p["RETURN"]["engine_valued"] == "0" and p["RETURN"]["residual"] == "-7.110"
    assert "ENGINE_OMISSION" in p["RETURN"]["rows"][0]["name"]
    assert p["SHAFT"]["by_cause"] == {"ENGINE_RIGHT": "13.85", "HELD": "175.14", "RULE_DIFFERENCE": "1.93",
                                      "UNRESOLVED": "54.000"}


def test_dev_census_no_paint_under_full_height_porcelain(dev):
    c = dev["census_FIN_PAINT"]
    wet = c["EXCLUDED (wet: paint above wall tile, none under full-height porcelain)"]
    assert wet["valued_m2"] == "0" and wet["lines"] == 17
    assert c["DRY room line"] == {"held_lines": 7, "lines": 11, "valued_m2": "217.2081"}


def test_dev_two_methods_and_external_and_ceiling_kept_apart(dev):
    t = dev["internal"]["pairs"]["DRY"]["two_methods"]
    assert t["owner_G1_gross_11_lines"] == "847.22810" and t["drawing_derived_gross_11_lines"] == ["956.43", "981.24"]
    assert len(t["released_lines"]) == 4 and all(Dc(r["difference"][0]) > 0 for r in t["released_lines"])
    e = dev["external"]
    assert e["freelancer_paint_workbook_external_m2"] == "0" and e["engine_valued_m2"] == "0"
    assert dev["ceiling_paint_beside"]["reconciled_here"] is False
    assert all(r["paint_height"]["m"] != r["plaster_height"]["m"][0] for r in dev["plaster_vs_paint_height"]["rows"])
