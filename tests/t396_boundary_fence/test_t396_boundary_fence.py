"""T-396: boundary / fence masonry above N.G., run by run (BOUNDARY_FENCE_V1 rules R-T396-1 .. -5, any villa).

Synthetic 'Villa K' (not the development villa): an L-shaped plot fence, 0.20 thick, printed section height 2.40 m
above N.G.; side run A 20.00 m (owns the corner square), street run B 12.00 m outer (corner 0.20 owned by A) with a
3.50 m gate; 3 printed columns 20 x 30 (2 on A, 1 on B). Hand values:
  A: plane 20.00 x 2.40 = 48.000 m2; columns 2 x 0.30 x 2.40 = 1.440; block net 46.560 m2
  B: solid 12.00 - 0.20 - 3.50 = 8.300 m; plane 8.30 x 2.40 = 19.920 m2; 1 column 0.720; block net 19.200 m2
  total plane 67.920 m2, block net 65.760 m2 (DRAWING-CONFIRMED); a 0.30 m concrete plinth on A: 46.560 - 6.000 = 40.560
Adverse: a gate counted as wall, a gate outside its run, a height invented / unsourced / only drawn, a pool back
counted in the fence and the pool line, mm passed as m, a HELD run summed as 0, an unknown column count released,
an undimensioned dip released, a freelancer corner double count hidden. Development villa: the committed values-only
outputs reproduce from the committed input (no private file needed) and the pinned figures hold.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
DIR = ROOT / "research" / "agents_t396"


def _load(name):
    spec = importlib.util.spec_from_file_location(name, DIR / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


BF = _load("boundary_fence")


def _h(v=2.40):
    return BF.height(v, "PRINTED", "Villa K fence section '240'")


def _villa_k():
    a = BF.ledger_row("A", 20.00, [], [], _h(), 2)
    b = BF.ledger_row("B", 12.00, [3.50], [], _h(), 1, corner_owned_elsewhere_m=0.20)
    return a, b


# ---------------------------------------------------------------- normal
def test_villa_k_hand_values():
    a, b = _villa_k()
    assert a["solid_m"] == pytest.approx(20.00)
    assert a["plane_m2"] == pytest.approx(48.000) and a["plane_status"] == BF.DC
    assert a["block_net_m2"] == pytest.approx(46.560) and a["block_status"] == BF.DC
    assert b["solid_m"] == pytest.approx(8.300)
    assert b["plane_m2"] == pytest.approx(19.920)
    assert b["block_net_m2"] == pytest.approx(19.200)
    t = BF.totals([a, b])
    assert t["plane_dc_m2"] == pytest.approx(67.920) and t["block_dc_m2"] == pytest.approx(65.760)
    assert t["plane_held_runs"] == [] and t["block_held_runs"] == []
    assert a["block_type"].startswith("HELD") and a["block_count"].startswith("HELD")


def test_concrete_plinth_is_deducted_only_when_its_material_is_known():
    a = BF.ledger_row("A", 20.00, [], [], _h(), 2, lower_band=(0.30, "NOT_BLOCK"))
    assert a["block_net_m2"] == pytest.approx(40.560)
    u = BF.ledger_row("A", 20.00, [], [], _h(), 2, lower_band=(0.30, "UNRESOLVED"))
    assert u["block_net_m2"] is None and u["block_status"] == BF.HELD
    assert u["block_at_most_m2"] == pytest.approx(46.560)
    assert u["plane_m2"] == pytest.approx(48.000) and u["plane_status"] == BF.DC


def test_mirror_and_rotation_do_not_change_a_run():
    # runs are measured along the band: the same lengths in any order / orientation give the same ledger
    a, b = _villa_k()
    b2 = BF.ledger_row("B", 12.00, [3.50], [], _h(), 1, corner_owned_elsewhere_m=0.20)
    a2 = BF.ledger_row("A", 20.00, [], [], _h(), 2)
    assert BF.totals([b2, a2])["block_dc_m2"] == pytest.approx(BF.totals([a, b])["block_dc_m2"])


# ---------------------------------------------------------------- adverse
def test_gate_is_never_wall():
    b = BF.run_solid(12.00, [3.50], corner_owned_elsewhere_m=0.20)
    assert b == pytest.approx(8.30) and b != pytest.approx(11.80)
    with pytest.raises(BF.FenceError):
        BF.run_solid(3.00, [3.50])                       # a gate outside (longer than) its run
    with pytest.raises(BF.FenceError):
        BF.run_solid(12.00, [0.0])                        # a zero gate is a missing value, not a gate


def test_height_is_never_invented():
    with pytest.raises(BF.FenceError):
        BF.height(2.00, "NONE", "freelancer")            # a value with no printed source
    with pytest.raises(BF.FenceError):
        BF.height(2.40, "PRINTED", "")                   # a printed height must name its sheet
    with pytest.raises(BF.FenceError):
        BF.height(2.40, "GUESS", "x")
    drawn = BF.height(2.65, "DRAWN", "elevation lines")
    r = BF.ledger_row("D", 10.0, [], [], drawn, 0)
    assert r["plane_m2"] is None and r["plane_status"] == BF.HELD
    assert r["plane_comparison_only_m2"] == pytest.approx(26.5)  # shown for comparison, never a quantity
    none = BF.height(None, "NONE", "no printed top")
    r = BF.ledger_row("E", 1.20, [], [], none, None)
    assert r["plane_m2"] is None and r["plane_comparison_only_m2"] is None and r["block_at_most_m2"] is None


def test_owner_held_element_stays_held_even_with_a_printed_height():
    r = BF.ledger_row("SEA", 6.90, [1.00], [3.50], _h(2.65), 0, element_held=True)
    assert r["solid_m"] == pytest.approx(2.40)
    assert r["plane_m2"] is None and r["plane_status"] == BF.HELD and r["block_net_m2"] is None


def test_pool_back_counted_twice_refused():
    assert BF.run_solid(6.90, [1.00], [3.50]) == pytest.approx(2.40)
    with pytest.raises(BF.FenceError):
        BF.run_solid(4.00, [1.00], [3.50])               # exclusion + gate larger than the run
    BF.bind_once([("sea pool back 3.50", "POOL wall"), ("sea 0.9184 S", "BOUNDARY WORKS")])
    with pytest.raises(BF.FenceError):
        BF.bind_once([("sea pool back 3.50", "POOL wall"), ("sea pool back 3.50", "BOUNDARY WORKS")])
    with pytest.raises(BF.FenceError):
        BF.bind_once([("x", "")])


def test_units_are_metres_once():
    with pytest.raises(BF.FenceError):
        BF.run_solid(12000, [3500])                       # mm passed as m
    with pytest.raises(BF.FenceError):
        BF.run_solid(12.0, [3.5], unit="mm")
    with pytest.raises(BF.FenceError):
        BF.height(240, "PRINTED", "cm passed as m")
    with pytest.raises(BF.FenceError):
        BF.run_solid(None, [])                           # missing is HELD, never 0


def test_held_is_never_zero_and_unknowns_never_released():
    unk = BF.ledger_row("A", 20.00, [], [], _h(), None)  # column count not printed
    assert unk["block_net_m2"] is None and unk["block_status"] == BF.HELD
    assert unk["block_at_most_m2"] == pytest.approx(48.000)
    dip = BF.ledger_row("B", 12.00, [3.50], [], _h(), 1, profile_cut="UNDIMENSIONED", corner_owned_elsewhere_m=0.20)
    assert dip["block_net_m2"] is None and dip["block_at_most_m2"] == pytest.approx(19.200)
    held = BF.ledger_row("E", 1.20, [], [], BF.height(None, "NONE", "x"), None)
    t = BF.totals([unk, dip, held])
    assert t["block_dc_m2"] == 0.0 and t["block_held_runs"] == ["A", "B", "E"]
    assert t["plane_held_runs"] == ["E"] and t["plane_dc_m2"] == pytest.approx(48.000 + 19.920)
    with pytest.raises(BF.FenceError):
        BF.ledger_row("A", 20.00, [], [], _h(), -1)
    with pytest.raises(BF.FenceError):
        BF.ledger_row("A", 1.00, [], [], _h(), 10)        # column faces larger than the plane


def test_freelancer_corner_double_count_is_named():
    fr = BF.map_freelancer(12.20, 2.00, [12.00, 0.20], 0.20, 12.00, 2.40)  # his 12.20 = 12.00 + 0.20 corner
    assert fr["corner_twice_m"] == pytest.approx(0.20) and fr["length_unexplained_m"] == pytest.approx(0.0)
    assert fr["residual_m2"] == pytest.approx(0.0)
    assert fr["height_m2"] == pytest.approx((2.00 - 2.40) * 12.00)
    with pytest.raises(BF.FenceError):
        BF.map_freelancer(12.20, 2.00, [12.0, 0.20], 0.10, 12.00, 2.40)   # the corner must be the shared square


# ---------------------------------------------------------------- development villa (committed values only)
def test_development_villa_reproduces_and_pins():
    A = _load("t396_alsenan")
    outs = A.outputs()
    for p, s in outs.items():
        assert p.read_text(encoding="utf-8") == s, p.name
    s = json.loads((DIR / "summary.json").read_text(encoding="utf-8"))
    r = s["runs"]
    assert r["F-NORTH (upper neighbour)"]["plane_m2"] == pytest.approx(83.1305)
    assert r["F-STREET"]["solid_m"] == pytest.approx(5.60) and r["F-STREET"]["plane_m2"] == pytest.approx(14.84)
    assert r["F-SEA (Q-63 C element)"]["solid_m"] == pytest.approx(2.40)
    assert r["F-SEA (Q-63 C element)"]["plane_m2"] is None
    assert r["F-LOWER passage closure"]["plane_m2"] is None
    assert all(v["block_status"] == "HELD" for v in r.values())
    assert s["totals"]["plane_dc_m2"] == pytest.approx(97.9705) and s["totals"]["block_dc_m2"] == 0.0
    assert s["band_conservation_m"]["total"] == pytest.approx(44.07) == s["band_conservation_m"]["t253_total"]
    f = s["freelancer"]
    assert f["his_m2"] == pytest.approx(74.40) and f["diff_m2"] == pytest.approx(-23.5705)
    assert f["corner_twice_m2"] == pytest.approx(0.40) and f["height_m2"] == pytest.approx(-24.0305)
    assert f["residual_m2"] == pytest.approx(0.0)
    assert s["candidate_lines_changed"] == 0


def test_committed_input_has_no_coordinates():
    d = json.loads((DIR / "ALSENAN_FENCE_INPUT.json").read_text(encoding="utf-8"))

    def nums(x):
        if isinstance(x, dict):
            for v in x.values():
                yield from nums(v)
        elif isinstance(x, list):
            for v in x:
                yield from nums(v)
        elif isinstance(x, (int, float)) and not isinstance(x, bool):
            yield x
    assert all(abs(v) < 100 for v in nums(d))
    assert sum(len(v) for v in d["layer1_wall_lines_on_fence_bands"].values()) == 0
