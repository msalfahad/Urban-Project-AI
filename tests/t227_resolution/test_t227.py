"""T-227: level-mark datum test (UP-MAS-DATUM-001), opening heads into block nets (UP-MAS-HEADS-002), lift tie beam
(UP-MAS-TIEBEAM-001), lift landing openings (UP-OPEN-LIFT-001), pieces under an open void (UP-MAS-VOID-001), bands
of no block family (UP-MAS-BAND-001), and the development-villa register delta.

Fixture villa T227-K (NOT Alsenan), hand truth:
  annex floor mark +0.50, dry layer 0.05 drawn in the cut -> slab top +0.45
  annex roof mark +4.60: (i) printed S.S.L +4.40 -> storey 4.40 - 0.45 = 3.95; under a 0.50 beam 3.45 m
                         (ii) printed build-up 0.25 -> slab top +4.35, storey 3.90
                         (iii) only a drawn constant 0.05 layer, falls printed -> HELD (never 4.60 - 0.50 = 4.10)
                         (iv) nothing printed -> HELD (a roof mark is never the slab)
  run 8.00 m x 3.20 m = 25.600 m2 gross; door 1.00 x 2.20 = 2.200 already deducted; windows K1 1.20 x 1.50 = 1.800 and
  K2 0.60 x 0.80 = 0.480 drawn -> deductions 4.480, net 21.120 m2
  lift: storey 4.50 > 4.30 -> tie beam required; clear run 5.00 m; no section -> strip HELD; printed 0.20 x 0.40 ->
  strip 2.000 m2; storey 4.20 -> not required
"""
from __future__ import annotations

import csv
import itertools
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "research" / "agents_t227"
sys.path.insert(0, str(HERE))

import datum_rules as R  # noqa: E402

FLOOR = dict(level_m=0.50, kind="FLOOR", drawn_layer_m=0.05, drawn_layer_zone_type="DRY", zone_type="DRY",
             falls_printed=False)


def roof(**k):
    base = dict(level_m=4.60, kind="ROOF")
    base.update(k)
    return base


# ------------------------------------------------------------------------------------------------ UP-MAS-DATUM-001
def test_floor_drawn_dry_layer_gives_slab_top():
    r = R.slab_top_from_mark(FLOOR)
    assert r["status"] == R.DC and r["rule"] == "R3" and r["slab_top_m"] == pytest.approx(0.45)


def test_printed_structural_level_governs():
    st = R.storey_structural_height(FLOOR, roof(printed_structural_level_m=4.40, drawn_layer_m=0.05,
                                                falls_printed=True))
    assert st["status"] == R.DC and st["height_m"] == pytest.approx(3.95)
    assert R.block_height_under_member(st, 0.50)["height_m"] == pytest.approx(3.45)


def test_printed_buildup_gives_slab_top():
    st = R.storey_structural_height(FLOOR, roof(printed_buildup_m=0.25))
    assert st["status"] == R.DC and st["height_m"] == pytest.approx(3.90)


def test_adverse_constant_layer_on_a_roof_with_falls_is_refused():
    st = R.storey_structural_height(FLOOR, roof(drawn_layer_m=0.05, drawn_layer_zone_type="ROOF", zone_type="ROOF",
                                                falls_printed=True))
    assert st["status"] == R.HELD and st["height_m"] is None
    assert "CONSTANT_LAYER_VS_FALLS" in st["reason"]
    assert R.block_height_under_member(st, 0.50) == {"status": R.HELD, "height_m": None}


def test_adverse_roof_mark_taken_as_slab_without_a_slab_level_is_refused():
    r = R.slab_top_from_mark(roof())
    assert r["status"] == R.HELD and r["slab_top_m"] is None and r["reason"] == "ROOF_MARK_NOT_SLAB"
    st = R.storey_structural_height(FLOOR, roof())
    assert st["height_m"] is None                       # never 4.60 - 0.50 = 4.10, never 0


def test_adverse_layer_from_another_zone_is_not_carried():
    m = dict(FLOOR, zone_type="WET")
    assert R.slab_top_from_mark(m)["status"] == R.HELD


def test_adverse_negative_buildup_and_missing_level():
    with pytest.raises(ValueError):
        R.slab_top_from_mark(roof(printed_buildup_m=-0.05))
    assert R.slab_top_from_mark({"kind": "ROOF"})["status"] == R.HELD


def test_sensitivity_is_information_not_a_quantity():
    assert R.held_sensitivity_m2_per_cm([9.9, 1.65]) == pytest.approx(0.1155)


# ------------------------------------------------------------------------------------------------ UP-MAS-HEADS-002
HEADS = {"K1": {"width_m": 1.20, "height_m": 1.50, "area_m2": 1.800, "status": R.DC},
         "K2": {"width_m": 0.60, "height_m": 0.80, "area_m2": 0.480, "status": R.VERIFIED},
         "K3": {"width_m": 1.00, "height_m": None, "area_m2": None, "status": R.HELD}}


def test_heads_close_the_net():
    r = R.apply_heads(25.600, R.SS, 2.200, ["K1", "K2"], HEADS)
    assert r["deductions_m2"] == pytest.approx(4.480) and r["net_m2"] == pytest.approx(21.120)
    assert r["still_held"] == []


def test_heads_order_does_not_matter():                 # mirror / rotation of the run: openings listed in any order
    nets = {R.apply_heads(25.600, R.SS, 2.200, list(p), HEADS)["net_m2"] for p in itertools.permutations(["K1", "K2"])}
    assert nets == {21.120}


def test_adverse_held_head_keeps_the_net_held():
    r = R.apply_heads(25.600, R.SS, 2.200, ["K1", "K3"], HEADS)
    assert r["net_m2"] is None and r["still_held"] == ["K3"] and r["deductions_m2"] == pytest.approx(4.000)


def test_adverse_held_gross_never_forms_a_net():
    r = R.apply_heads(25.600, R.HELD, 2.200, ["K1", "K2"], HEADS)
    assert r["net_m2"] is None and r["deductions_m2"] == pytest.approx(4.480)


def test_adverse_area_must_be_width_times_height():
    bad = {"K1": dict(HEADS["K1"], area_m2=2.400)}      # frame / fabrication size offered as the opening
    with pytest.raises(ValueError):
        R.apply_heads(25.600, R.SS, 0.0, ["K1"], bad)


def test_adverse_deductions_beyond_gross():
    with pytest.raises(ValueError):
        R.apply_heads(1.000, R.SS, 0.0, ["K1"], HEADS)


# ------------------------------------------------------------------------------------------------ lift, void, band
def test_tie_beam_without_section_is_held():
    t = R.tie_beam_strip(4.50, 4.30, 5.00)
    assert t["applies"] is True and t["status"] == R.HELD and t["strip_m2"] is None


def test_tie_beam_printed_and_not_required():
    assert R.tie_beam_strip(4.50, 4.30, 5.00, depth_m=0.40)["strip_m2"] == pytest.approx(2.000)
    assert R.tie_beam_strip(4.20, 4.30, 5.00)["applies"] is False
    assert R.tie_beam_strip(None, 4.30, 5.00, storey_status=R.HELD)["applies"] is None


def test_lift_opening_does_not_take_the_internal_door_fallback():
    fb = {"height_m": 2.20, "scope": "INTERNAL_DOOR"}
    assert R.opening_height("LIFT_LANDING", owner_fallback=fb)["status"] == R.HELD
    assert R.opening_height("INTERNAL_DOOR", owner_fallback=fb)["status"] == "ASSUMED — OWNER-APPROVED"
    assert R.opening_height("LIFT_LANDING", drawn_m=2.10, owner_fallback=fb) == \
        {"status": R.DC, "height_m": 2.10, "basis": "drawn"}


def test_piece_under_open_void_has_no_top():
    assert R.piece_top()["status"] == R.HELD
    assert R.piece_top(member_above="ring R1 0.20 x 0.50")["status"] == R.DC


def test_band_of_no_block_family_is_held():
    assert R.band_material(0.40)["status"] == R.HELD
    assert R.band_material(0.20)["status"] == "PROJECT-SPECIFIC"
    assert R.band_material(0.40, printed_material="RC wall")["status"] == R.DC


# ------------------------------------------------------------------------------------------------ development villa
def run(*a):
    return subprocess.run([sys.executable, "-I", str(HERE / "alsenan_t227.py"), *a], capture_output=True, text=True,
                          cwd=ROOT)


def test_builder_reproduces_committed_outputs():
    p = run("--check")
    assert p.returncode == 0 and "CHECK PASS" in p.stdout, p.stdout + p.stderr


def delta():
    return list(csv.DictReader(open(HERE / "register_delta.csv", encoding="utf-8")))


def test_every_new_net_reconciles_and_held_stays_held():
    for d in delta():
        if d["net_class"] == R.SS:
            assert float(d["net_m2"]) == pytest.approx(float(d["gross_m2"]) - float(d["deductions_m2"]), abs=1e-3)
            assert d["held_openings"] == "" and d["gross_class"] == R.SS
            assert float(d["net_m3"]) == pytest.approx(float(d["net_m2"]) * float(d["t_m"]), abs=1e-3)
        else:
            assert d["net_m2"] == ""                    # never 0, never a figure
            assert d["owner_status_class"] == "HELD"


def test_annex_and_lift_walls_stay_held():
    rows = {d["wall_id"]: d for d in delta()}
    for w in ("GF-W00", "GF-W02", "GF-W06", "GF-W17", "GF-W23", "GF-W24", "GF-W25", "GF-W27", "GF-W35",
              "GF-W08", "GF-W09", "GF-W13", "GF-W14", "GF-H01", "GF-H02"):
        assert rows[w]["net_class"] == "HELD" and "T-227" in rows[w]["unresolved_reason"]


def test_summary_figures():
    s = json.loads((HERE / "summary.json").read_text(encoding="utf-8"))
    assert s["nets_newly_source_supported"] == {"GF-W16": 15.404, "1F-W00": 11.979, "1F-W06": 54.487,
                                                "1F-W10": 44.929}
    assert s["nets_newly_source_supported_total_m2"] == pytest.approx(126.799)
    assert s["annex"]["storey_test"] == "HELD" and s["verified_by_checker_m2"] == 0.0
    assert s["dome_pieces_m"] == pytest.approx(10.29)
