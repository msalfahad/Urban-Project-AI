"""T-552: wall plaster vs the freelancer by face class (research/agents_t552, R-T552-1).
Synthetic villa "P552" (not the training villa), hand calculations; adverse cases; then the development villa pins
(repository inputs only: candidate line index, T-128 / T-173 / T-337 merged ledgers, the parsed freelancer cells)."""
from __future__ import annotations

import json
import subprocess
import sys
from decimal import Decimal
from itertools import permutations
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t552"))
import t552_plaster_rules as R  # noqa: E402

Dc = Decimal
SRC = {"interval": "P552 section S-1 marks +0.00 / +4.00", "slab": "P552 S-0 note: slabs 16 cm",
       "buildup": "P552 F-1 floor build-up 10 cm"}

# ---- villa "P552" bedroom (hand): 4.00 x 3.00 m, wall run 14.00 lm; storey interval 4.00, slab 0.16, build-up
# 0.10 -> plaster height to the slab underside 4.00 - 0.16 - 0.10 = 3.74 m (paint would stop at a 2.90 ceiling).
# Door 0.90 x 2.20 = 1.98; window 1.20 x 1.50 = 1.80; one beam 0.30 wide, 0.60 deep (0.44 below the slab) crosses
# the 3.00 m span and frames into both long walls: 2 end sections 0.30 x 0.44 = 0.264 are concrete, not wall.
# Gross 14.00 x 3.74 = 52.36; net 52.36 - 1.98 - 1.80 - 0.264 = 48.316 m2.
# Beam band (CEILING item, Q-57): sides 2 x 0.44 x 3.00 = 2.64 + soffit 0.30 x 3.00 = 0.90 = 3.54 m2, never in the wall.
OPEN = [{"id": "D1", "width": "0.90", "height": "2.20"}, {"id": "W1", "width": "1.20", "height": "1.50"}]
BEAM_ENDS = [{"width": "0.30", "depth_below_slab": "0.44"}] * 2


def test_plaster_height_to_slab_underside_by_hand():
    assert R.plaster_height(basis="SLAB_UNDERSIDE", interval="4.00", slab="0.16", buildup="0.10",
                            sources=SRC) == (Dc("3.74"), Dc("3.74"))
    assert R.plaster_height(basis="SLAB_UNDERSIDE", interval="4.00", slab="0.16", buildup=("0", "0.10"),
                            sources=SRC) == (Dc("3.74"), Dc("3.84"))


def test_net_plaster_room_with_door_window_and_beam_band():
    out = R.net_wall_plaster(run_lm="14.00", height="3.74", openings=OPEN, beam_ends=BEAM_ENDS, beam_band="3.54")
    assert out["gross"] == Dc("52.3600")
    assert out["deductions"] == Dc("1.98") + Dc("1.80") + Dc("0.264")
    assert out["net"] == Dc("48.316")
    assert out["ceiling_beam_band"] == Dc("3.54")      # reported beside, not in the wall net


def test_net_plaster_invariant_to_opening_order_mirror():
    nets = {R.net_wall_plaster(run_lm="14.00", height="3.74", openings=list(p), beam_ends=BEAM_ENDS)["net"]
            for p in permutations(OPEN)}
    assert nets == {Dc("48.316")}


def test_opening_taller_than_the_face_capped():
    out = R.net_wall_plaster(run_lm="2.00", height="2.50", openings=[{"id": "G", "width": "1.00", "height": "3.00"}])
    assert out["net"] == Dc("2.50")


def _p552_bridge(**over):
    # his row: 14.20 x 3.60 = 51.12 gross; engine valued line 48.316 (above). his - engine = 2.804 =
    # openings + beam ends 4.044 (Q-73 full, in his gross) + length (14.20 - 14.00) x 3.60 = 0.72
    # - height 14.00 x (3.74 - 3.60) = 1.96 -> 4.044 + 0.72 - 1.96 = 2.804, residual 0.
    kw = dict(pair_class="DRY", freelancer_gross="51.12",
              engine_lines=[{"line_id": "P-1", "cls": "DRY", "qty": "48.316", "unit": "m2"}],
              components=[{"name": "openings + beam ends", "qty": "4.044", "sign": 1, "cause": "RULE_DIFFERENCE",
                           "source": "P552 hand"},
                          {"name": "length", "qty": "0.72", "sign": 1, "cause": "ENGINE_RIGHT", "source": "P552 A-1"},
                          {"name": "height", "qty": "1.96", "sign": -1, "cause": "RULE_DIFFERENCE",
                           "source": "P552 S-1"}], residual_name="R")
    kw.update(over)
    return R.bridge(**kw)


def test_bridge_closes_exactly_by_hand():
    b = _p552_bridge()
    assert b["gap"] == "2.804" and Dc(b["residual"]) == 0
    assert b["by_cause"] == {"RULE_DIFFERENCE": "2.084", "ENGINE_RIGHT": "0.72"}


def test_bridge_names_a_residual_never_absorbs():
    b = _p552_bridge(freelancer_gross="51.62")
    assert b["residual"] == "0.500" and b["rows"][-1]["cause"] == "UNRESOLVED" and b["rows"][-1]["name"] == "R"


# ---- adverse --------------------------------------------------------------------------------------------------
@pytest.mark.parametrize("basis", ["PAINT_HEIGHT", "FINISHED_CEILING", "OWNER_G1_ROOM_FORMULA"])
def test_paint_height_used_for_plaster_refused(basis):
    with pytest.raises(R.PlasterError, match="paint"):
        R.plaster_height(basis=basis, interval="4.00", slab="0.16", buildup="0.10", sources=SRC)


def test_missing_buildup_or_source_refused():
    with pytest.raises(R.PlasterError, match="HELD"):
        R.plaster_height(basis="SLAB_UNDERSIDE", interval="4.00", slab="0.16", buildup=None, sources=SRC)
    with pytest.raises(R.PlasterError, match="no source"):
        R.plaster_height(basis="SLAB_UNDERSIDE", interval="4.00", slab="0.16", buildup="0.10",
                         sources={"interval": "x", "slab": "y"})


def test_tiled_face_also_counted_as_plaster_coat_refused():
    with pytest.raises(R.PlasterError, match="one finish owner"):
        R.check_face_classes([{"face_id": "B1-N", "cls": "WET"}, {"face_id": "B1-N", "cls": "DRY"}])
    R.check_face_classes([{"face_id": "B1-N", "cls": "WET"}, {"face_id": "R1-N", "cls": "DRY"}])


def test_wet_render_line_in_a_dry_pair_refused():
    with pytest.raises(R.PlasterError, match="never enters"):
        _p552_bridge(engine_lines=[{"line_id": "P-1", "cls": "DRY", "qty": "48.316", "unit": "m2"},
                                   {"line_id": "P-W", "cls": "WET", "qty": "20.0", "unit": "m2"}])


def test_held_line_as_zero_or_none_refused():
    with pytest.raises(R.PlasterError):
        _p552_bridge(engine_lines=[{"line_id": "P-1", "cls": "DRY", "qty": None, "unit": "m2"}])
    with pytest.raises(R.PlasterError, match="never 0"):
        R.D(None)
    with pytest.raises(R.PlasterError, match="carries a figure"):
        _p552_bridge(outside=[{"line_id": "P-H", "qty": "0"}])


def test_freelancer_figure_as_component_refused():
    with pytest.raises(R.PlasterError, match="source"):
        _p552_bridge(components=[{"name": "x", "qty": "1", "sign": 1, "cause": "HELD", "source": "freelancer row 7"}])


def test_his_scope_row_needs_rule_cause():
    with pytest.raises(R.PlasterError, match="his-scope"):
        _p552_bridge(components=[{"name": "domes", "qty": "1", "sign": 1, "cause": "ENGINE_RIGHT",
                                  "source": "owner note", "his_scope_row": True}])


def test_tolerance_limit_units_and_classes():
    with pytest.raises(R.PlasterError, match="TOLERANCE"):
        _p552_bridge(components=[{"name": "t", "qty": "0.010", "sign": 1, "cause": "TOLERANCE", "source": "s"}])
    with pytest.raises(R.PlasterError, match="m2"):
        _p552_bridge(components=[{"name": "u", "qty": "14", "sign": 1, "cause": "HELD", "source": "s", "unit": "lm"}])
    with pytest.raises(R.PlasterError, match="UNRESOLVED"):
        _p552_bridge(components=[{"name": "u", "qty": "1", "sign": 1, "cause": "UNRESOLVED", "source": "s"}])
    with pytest.raises(R.PlasterError):
        R.bridge(pair_class="ROOF", freelancer_gross="1", engine_lines=[], components=[], residual_name="R")


def test_opening_height_unknown_refused():
    with pytest.raises(R.PlasterError, match="height not established"):
        R.net_wall_plaster(run_lm="14.00", height="3.74", openings=[{"id": "W9", "width": "1.0", "height": None}])


# ---- development villa (repository inputs only) ----------------------------------------------------------------
OUT = ROOT / "research" / "agents_t552" / "out" / "T552_PLASTER_RECONCILE.json"


@pytest.fixture(scope="module")
def built():
    import t552_alsenan as A
    return A.build()


def test_alsenan_rebuild_byte_identical(built):
    assert OUT.read_text() == json.dumps(built, indent=1, ensure_ascii=True, sort_keys=True) + "\n"


def test_alsenan_census_and_totals(built):
    c = built["census_FIN_PLASTER"]
    assert built["candidate_valued_FIN_PLASTER_m2"] == "580.5819"
    assert (c["DRY room line"]["lines"], c["DRY room line"]["valued_m2"]) == (11, "217.2081")
    assert (c["RETURN"]["lines"], c["RETURN"]["valued_m2"]) == (30, "23.070")
    assert (c["WET render line"]["lines"], c["WET render line"]["valued_m2"]) == (18, "340.3038")
    assert sum(v["lines"] for v in c.values()) == 75


def test_alsenan_internal_bridge(built):
    i = built["internal"]
    assert (i["freelancer_gross"], i["freelancer_net"], i["his_half_deduction"]) == ("1209.385", "1151.1375", "58.2475")
    assert i["engine_valued_dry_plus_returns"] == "240.2781"
    assert Dc(i["gap_gross"]) == Dc("969.1069") and Dc(i["gap_net"]) == Dc("910.8594")
    p = i["pairs"]
    assert Dc(p["DRY"]["residual"]) == 0 and Dc(p["DRY"]["gap"]) == Dc("731.2969")
    assert Dc(p["DRY"]["by_cause"]["HELD"]) == Dc("587.71805")
    assert Dc(p["SHAFT"]["residual"]) == Dc("54.000") and Dc(p["RETURN"]["residual"]) == Dc("-7.110")
    assert sum(Dc(x["gap"]) for x in p.values()) == Dc(i["gap_gross"])
    # wet render lines never in the dry pair: the 12 valued wet lines are not among the DRY rooms' lines
    idx = json.loads((ROOT / "research/agents_t507/out/LINE_INDEX_V3_0_57.json").read_text())["lines"]
    dry_ids = {r["line_id"] for r in p["DRY"]["rooms"] if r.get("line_id")}
    wet_ids = {ln["line_id"] for ln in idx if ln["item_code"] == "FIN.PLASTER" and
               ln["class"] != "EXCLUDED" and
               (ln["element_id"].endswith(":plaster") or ln["element_id"].endswith("GF_07:PLASTER"))}
    assert len(wet_ids) == 18 and not (dry_ids & wet_ids)   # 12 valued (340.3038) + 6 HELD blank


def test_alsenan_external_bridge(built):
    e = built["external"]
    assert e["engine_valued"] == "0" and e["freelancer_net"] == "1469.9675"
    for k in ("bridge_lo", "bridge_hi"):
        assert Dc(e[k]["gap"]) == Dc("1502.84") and Dc(e[k]["residual"]) == Dc("93.15")
    assert Dc(e["bridge_lo"]["by_cause"]["HELD"]) == Dc("1119.7147")
    assert Dc(e["bridge_hi"]["by_cause"]["HELD"]) == Dc("1125.2857")


def test_alsenan_q72_height_correction(built):
    q = built["q72_dry_plaster_height"]
    assert q["verdict"].startswith("ENGINE_WRONG")
    assert [Dc(x) for x in q["missing_total"]] == [Dc("146.41440"), Dc("171.23040")]
    gf15 = next(r for r in q["rows"] if r["room"] == "GF-15")
    # 21.537 x (4.24 - 3.65) = 12.70683 .. 21.537 x (4.34 - 3.65) = 14.86053 on the released 56.0131
    assert gf15["missing_m2"] == ["12.70683", "14.86053"] and gf15["corrected_net"] == ["68.71993", "70.87363"]
    assert all(r["status"].startswith("HELD") for r in q["rows"])


def test_alsenan_output_carries_no_text_from_the_drawings_or_workbook():
    t = OUT.read_text()
    assert t.isascii()
    for bad in ("Alsenan", "dxf", "x=", "y=", "E+", "insert"):
        assert bad not in t


def test_alsenan_check_mode():
    r = subprocess.run([sys.executable, "-I", str(ROOT / "research/agents_t552/t552_alsenan.py"), "--check"],
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr
