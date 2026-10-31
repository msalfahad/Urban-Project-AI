"""T-398: stair / dome / pump-room reconciliation rules. Villa V398 (hand fixture, NOT Alsenan):

FLIGHT F1: 10 risers r 0.17, going 0.28, lane 1.10, drawn run 9 x 0.28 = 2.52 m, printed waist T 15.
  steps = 10 x 1/2 x 0.17 x 0.28 x 1.10 = 0.261800 m3
  sec = sqrt(0.17^2 + 0.28^2) / 0.28 = 0.327567 / 0.28 = 1.169881
  waist = 2.52 x 1.169881 x 0.15 x 1.10 = 0.486437 m3        gross = 0.748237 m3
LANDING L1: plate 1.20 x 1.10, T 15, its edge on beam BL 0.25 wide billed full depth: the beam owns
  0.25 x 1.10 x 0.15 = 0.041250; landing net (1.20 - 0.25) x 1.10 x 0.15 = 0.156750 m3.
OTHER SIDE (a plate method): flight 1.10 x 3.20 x 0.25 = 0.880 m3; landing 1.10 x 1.20 x 0.20 = 0.264 m3.
  flight terms (engine - other): WIDTH 0; LENGTH -(3.20 - 2.52) x 1.10 x 0.25 = -0.187000;
  THICKNESS_BASIS 0.748237 - 2.52 x 1.10 x 0.25 = +0.055237; sum -0.131763 = 0.748237 - 0.880.
DOME D1 (shallow): chord 3.00, rise 0.60, shell 0.08: R_o = (1.50^2 + 0.60^2) / 1.20 = 2.175, R_i 2.095, h_i 0.52;
  V = pi/3 [0.36 (6.525 - 0.60) - 0.2704 (6.285 - 0.52)] = 0.601242 m3; equivalent area V / t = 7.515527 m2;
  ring 0.20 x 0.30 under the springing is a beam item, never in the shell.
"""

import math
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t398"))
import t398_rules as R  # noqa: E402

F1 = dict(n_triangles=10, riser=0.17, going=0.28, width=1.10, run=2.52, waist=0.15)


# ---------------- normal cases

def test_flight_hand_figure():
    f = R.flight(**F1)
    assert f["steps_m3"] == pytest.approx(0.261800, abs=1e-6)
    assert f["waist_m3"] == pytest.approx(0.486437, abs=1e-6)
    assert f["gross_m3"] == pytest.approx(0.748237, abs=1e-6)


def test_run_from_riser_lines_rotation_and_mirror_invariant():
    segs = [((0.0, i * 280.0), (1100.0, i * 280.0)) for i in range(10)]
    assert R.run_from_risers(segs, unit=0.001) == pytest.approx((10, 2.52, 1.10))
    a = math.radians(37.0)
    rot = [tuple((x * math.cos(a) - y * math.sin(a), x * math.sin(a) + y * math.cos(a)) for x, y in s) for s in segs]
    mir = [tuple((-x, y) for x, y in s[::-1]) for s in rot]
    for s in (rot, mir):
        n, run, w = R.run_from_risers(s, unit=0.001)
        assert (n, round(run, 6), round(w, 6)) == (10, 2.52, 1.10)


def test_plate_terms_sum_to_contribution():
    g = R.flight(**F1)["gross_m3"]
    t = R.plate_terms(g, [], 2.52, 1.10, 3.20, 1.10, 0.25, drawn_lengths=(3.20,))
    d = {x["term"]: x for x in t}
    assert d["WIDTH"]["m3"] == 0.0
    assert d["LENGTH"]["m3"] == pytest.approx(-0.187, abs=1e-6) and d["LENGTH"]["traced"]
    assert d["THICKNESS_BASIS"]["m3"] == pytest.approx(0.055237, abs=1e-6)
    assert sum(x["m3"] for x in t) == pytest.approx(0.748237 - 0.880, abs=1e-6)


def test_landing_on_a_beam_owned_once():
    own = R.ownership([{"id": "L1-NET", "owners": ["STAIR"]}, {"id": "L1-BEAM-STRIP", "owners": ["BEAM"]}])
    assert own == {"L1-NET": "STAIR", "L1-BEAM-STRIP": "BEAM"}
    assert round((1.20 - 0.25) * 1.10 * 0.15 + 0.25 * 1.10 * 0.15, 6) == round(1.20 * 1.10 * 0.15, 6)   # union once


def test_dome_shell_hand_figure_and_terms():
    c = R.cap_shell(3.00, 0.60, 0.08)
    assert c["R_o"] == 2.175
    assert c["V_m3"] == pytest.approx(0.601242, abs=1e-6)
    assert c["equiv_area_m2"] == pytest.approx(7.515527, abs=1e-6)
    t = R.shell_terms(c["V_m3"], 0.08, 7.0, 0.08, drawn_areas=(c["outer_area_m2"],))
    assert t[0]["m3"] == pytest.approx((7.515527 - 7.0) * 0.08, abs=1e-6) and not t[0]["traced"]
    assert t[1]["m3"] == 0.0


def test_component_closure_traced_held_untraced():
    g = R.flight(**F1)["gross_m3"]
    comps = [
        {"id": "C-F1", "pieces": [{"id": "F1", "state": "VALUED", "m3": g}], "his_m3": 0.880, "verdict": "ENGINE_RIGHT",
         "cause": "drawn run and printed waist", "terms": R.plate_terms(g, [], 2.52, 1.10, 3.20, 1.10, 0.25)},
        {"id": "C-L1", "pieces": [{"id": "L1", "state": "HELD", "low": 0.15, "high": 0.17}], "his_m3": 0.264,
         "verdict": "HELD", "cause": "landing level not printed"},
    ]
    rows, fam = R.family("V398", comps, 0.880 + 0.264)
    assert fam["residual_m3"] == pytest.approx(0.748237 - 1.144, abs=1e-6)
    assert fam["named_m3"] == pytest.approx(0.055237, abs=1e-6)          # length untraced: 3.20 drawn nowhere
    assert fam["untraced_terms_m3"] == pytest.approx(-0.187, abs=1e-6)
    assert fam["held_named_m3"] == pytest.approx(-0.264, abs=1e-6)
    assert fam["named_m3"] + fam["held_named_m3"] + fam["unexplained_m3"] == pytest.approx(fam["residual_m3"], abs=1e-6)
    assert rows[1]["held_low_m3"] == 0.15 and rows[1]["engine_valued_m3"] == 0.0


def test_not_drawn_element_is_held_named_item():
    r = R.component({"id": "PUMP", "pieces": [], "held_named_item": "PUMP-ROOM (drawn on no sheet)", "his_m3": 2.0,
                     "verdict": "HELD", "cause": "drawn on no sheet"})
    assert r["engine_valued_m3"] == 0.0 and r["held_named_m3"] == -2.0 and r["unexplained_m3"] == 0.0


# ---------------- adverse cases

def test_landing_in_stair_and_slab_refused():
    with pytest.raises(R.Refused, match="DOUBLE"):
        R.ownership([{"id": "L1", "owners": ["STAIR", "SLAB"]}])


def test_orphan_piece_refused():
    with pytest.raises(R.Refused):
        R.ownership([{"id": "L1", "owners": []}])


def test_waist_to_nosing_plus_steps_refused():
    with pytest.raises(R.Refused, match="twice"):
        R.flight(**F1, waist_basis="TO_NOSING")


def test_held_as_zero_refused():
    with pytest.raises(R.Refused, match="never 0"):
        R.component({"id": "X", "pieces": [{"id": "L1", "state": "HELD", "m3": 0.0}], "his_m3": 0.264,
                     "verdict": "HELD", "cause": "landing level not printed"})


def test_held_called_agreement_refused():
    with pytest.raises(R.Refused):
        R.component({"id": "X", "pieces": [{"id": "L1", "state": "HELD"}], "his_m3": 0.0, "verdict": "AGREE",
                     "cause": "nothing"})


def test_traced_component_with_held_piece_refused():
    with pytest.raises(R.Refused, match="held piece"):
        R.component({"id": "X", "pieces": [{"id": "F1", "state": "VALUED", "m3": 0.5}, {"id": "T", "state": "HELD"}],
                     "his_m3": 0.6, "verdict": "ENGINE_RIGHT", "cause": "drawn run"})


def test_ring_inside_the_shell_refused():
    with pytest.raises(R.Refused, match="RING"):
        R.cap_shell(3.00, 0.60, 0.08, includes=("RING",))


def test_ratio_cause_and_row_share_refused():
    with pytest.raises(R.Refused, match="ratio"):
        R.component({"id": "X", "pieces": [{"id": "F1", "state": "VALUED", "m3": 0.5}], "his_m3": 0.6,
                     "verdict": "ENGINE_RIGHT", "cause": "his row scaled by 85 %"})
    with pytest.raises(R.Refused, match="own printed unit"):
        R.component({"id": "X", "pieces": [{"id": "F1", "state": "VALUED", "m3": 0.5}], "his_m3": 0.6,
                     "his_split": 0.3, "verdict": "UNRESOLVED", "cause": "his lump by length"})


def test_unbound_row_part_refused():
    with pytest.raises(R.Refused, match="unbound"):
        R.family("V398", [{"id": "C", "pieces": [{"id": "F1", "state": "VALUED", "m3": 0.5}], "his_m3": 0.6,
                           "verdict": "ENGINE_RIGHT", "cause": "drawn run"}], 1.144)


def test_terms_not_summing_refused():
    with pytest.raises(R.Refused, match="do not sum"):
        R.component({"id": "X", "pieces": [{"id": "F1", "state": "VALUED", "m3": 0.5}], "his_m3": 0.6,
                     "verdict": "ENGINE_RIGHT", "cause": "drawn run",
                     "terms": [{"term": "LENGTH", "m3": -0.2, "traced": True}]})


def test_units_and_non_parallel_risers_refused():
    with pytest.raises(R.Refused, match="millimetres"):
        R.flight(10, 0.17, 0.28, 1100, 2.52, 0.15)
    with pytest.raises(R.Refused, match="parallel"):
        R.run_from_risers([((0, 0), (1, 0)), ((0, 1), (1, 1.5))])
    with pytest.raises(R.Refused):
        R.flight(10, 0.17, 0.28, 1.10, None, 0.15)                     # missing run: never 0


def test_typed_closure_refused():
    with pytest.raises(R.Refused, match="computed"):
        R.component({"id": "X", "pieces": [], "his_m3": 0.6, "verdict": "UNRESOLVED", "cause": "x",
                     "unexplained_m3": 0.0})


# ---------------- Alsenan engine side (tracked inputs only; no private data)

def test_alsenan_engine_side_binding():
    import t398_alsenan as A
    lines, led = A.engine()
    assert len(lines) == 22
    val = {c: round(sum(l["measured_net"] or 0.0 for l in lines.values() if l["item_code"].endswith(c)), 6)
           for c in ("STAIR", "DOME")}
    assert val == {"STAIR": 5.368881, "DOME": 5.081362}            # T-385 r2 SD-STAIR / SD-DOME
    assert R.cap_shell(*A.DRAWN["dome"])["V_m3"] == float(led["DOME-A-SHELL"]["value_m3"])
    for pid, r in (("ST01-MS2-L", A.DRAWN["r_ms2"]), ("ST01-MS1-U", A.DRAWN["r_ms1"])):
        g = R.flight(12, r, 0.30, 1.20, 3.30, 0.16)
        assert g["steps_m3"] + g["waist_m3"] > float(led[pid]["value_m3"])   # net = gross less owned-elsewhere parts
