"""T-394: column height / section / count / scope reconciliation. Villa V394 (hand fixture, not Alsenan): two storeys,
structural levels GF slab top +0.95, GF roof (1F floor) slab top +4.15, 1F roof slab top +7.35 (intervals 3.20 m),
slab plates 0.15 net of every column outline (C1), no beam billed through a column.
  K1 0.25 x 0.50 (a 0.125 m2) on both storeys; on GF it meets a DEEPER beam 0.30 x 0.70 (D_ctrl 0.70), on 1F 0.50 beams.
  K2 0.20 x 0.40 (a 0.080 m2): one on GF (D_ctrl 0.50); on 1F the roof datum is not printed: HELD (blank).
  Hand figures: GF K1 0.125 x 3.20 = 0.400 m3; GF K2 0.080 x 3.20 = 0.256 m3; 1F K1 0.400 m3; 1F K2 HELD.
Freelancer V394: every column at a uniform 2.70 m (interval - 0.50): GF K1 x1 0.3375, GF K2 x2 0.432, 1F K1 x1 0.3375,
1F K2 x1 0.216 m3.
  GF K1: residual +0.0625 = joint + head 0.125 x 0.70 = +0.0875 and his uniform depth against the deeper beam
         0.125 x (0.50 - 0.70) = -0.025 (his column runs 0.20 m into the beam's depth).
  GF K2: residual -0.176 = count (1 - 2) x 0.080 x 2.70 = -0.216 + joint + head 0.080 x 0.50 = +0.040.
  1F K1: +0.0625 = joint + head 0.125 x 0.50; 1F K2: HELD -0.216 (never 0, never AGREE).
Lift ring V394: 1.80 x 1.80 outer, 1.40 x 1.40 inner = 1.280 m2 gross, two corner columns 0.20 x 0.40 in it = 0.160 m2:
net 1.120 m2; his ring gross x 1.20 counts the column pieces again 0.160 x 1.20 = 0.192 m3."""

import itertools
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "research" / "agents_t394"
sys.path.insert(0, str(HERE))
import t394_rules as R  # noqa: E402

GF = {"base": 0.95, "top": 4.15}
F1 = {"base": 4.15, "top": 7.35}


def m(id_, a, d_ctrl, st=GF, state="VALUED", sec="DRAWING-CONFIRMED"):
    return {"id": id_, "state": state, "a": a, "h": round(st["top"] - st["base"], 6), "base": st["base"],
            "d_ctrl": d_ctrl, "section_status": sec, "m3": None if state == "HELD" else round(a * (st["top"] - st["base"]), 6)}


def his(n, a, h, st=GF):
    return {"n": n, "a": a, "h": h, "base": st["base"]}


# ---------------- normal cases (hand figures above)

def test_solid_to_slab_top_when_slab_and_beams_are_net():
    assert R.column_solid(0.125, 0.95, 4.15, slab_top=4.15, slab_t=0.15, slab_bills_footprint=False) == 0.4
    assert R.column_solid(0.08, 0.95, 4.15, slab_top=4.15, slab_t=0.15, slab_bills_footprint=False) == 0.256


def test_solid_stops_at_beam_soffit_when_the_beam_is_billed_through():
    assert R.column_top(4.15, 0.15, False, beam_through_depth=0.70) == (3.45, "BEAM_SOFFIT")
    assert R.column_solid(0.125, 0.95, 3.45, slab_top=4.15, slab_t=0.15, slab_bills_footprint=False,
                          beam_through_depth=0.70) == 0.3125


def test_gf_k1_deeper_beam_split():
    t = R.decompose_mark([m("K1", 0.125, 0.70)], his(1, 0.125, 2.70))
    assert t["residual"] == pytest.approx(0.0625)
    assert t["HEIGHT_JOINT_HEAD"] == pytest.approx(0.0875)
    assert t["HEIGHT_GLOBAL_DEPTH"] == pytest.approx(-0.025)
    assert t["COUNT"] == 0 and t["HELD"] == 0 and t["bookkeeping_remainder"] == 0


def test_gf_k2_count():
    t = R.decompose_mark([m("K2", 0.08, 0.50)], his(2, 0.08, 2.70))
    assert t["COUNT"] == pytest.approx(-0.216)
    assert t["HEIGHT_JOINT_HEAD"] == pytest.approx(0.04)
    assert t["HEIGHT_GLOBAL_DEPTH"] == pytest.approx(0.0, abs=1e-9)
    assert t["residual"] == pytest.approx(-0.176)


def test_1f_held_member_is_a_named_held_term():
    t = R.decompose_mark([m("K2-1F", 0.08, None, st=F1, state="HELD")], his(1, 0.08, 2.70, st=F1))
    assert t["engine_m3"] == 0 and t["HELD"] == pytest.approx(-0.216) and t["residual"] == pytest.approx(-0.216)
    c = R.closure([{"term": k, "m3": t[k], "cause": k} for k in R.TERM_KEYS])
    assert c["HELD"] == pytest.approx(-0.216) and c["TRACED"] == 0


def test_split_open_when_the_controlling_depth_is_not_settled():
    t = R.decompose_mark([m("K1-1F", 0.125, None, st=F1)], his(1, 0.125, 2.70, st=F1))
    assert t["HEIGHT_SPLIT_OPEN"] == pytest.approx(0.0625)
    assert t["HEIGHT_JOINT_HEAD"] == 0 and t["HEIGHT_GLOBAL_DEPTH"] == 0
    c = R.closure([{"term": k, "m3": t[k], "cause": k} for k in R.TERM_KEYS])
    assert c["TRACED_SPLIT_OPEN"] == pytest.approx(0.0625) and c["TRACED"] == 0


def test_base_datum_term_two_ground_slab_levels():
    low = {"base": 0.25, "top": 4.15}
    t = R.decompose_mark([m("K3", 0.10, 0.50, st=low)], his(1, 0.10, 2.70))   # his height from the +0.95 storey
    assert t["HEIGHT_BASE"] == pytest.approx(0.07)               # 0.10 x (0.95 - 0.25)
    assert t["HEIGHT_JOINT_HEAD"] == pytest.approx(0.05)
    assert t["residual"] == pytest.approx(0.10 * 3.90 - 0.27)
    assert t["bookkeeping_remainder"] == 0


def test_conflict_section_is_unresolved_not_closed():
    t = R.decompose_mark([m("K9", 0.18, 0.75, sec="CONFLICT")], his(1, 0.20, 2.70))
    assert t["SECTION_CONFLICT"] == pytest.approx(-0.054) and t["SECTION_DIMENSION"] == 0
    c = R.closure([{"term": k, "m3": t[k], "cause": k} for k in R.TERM_KEYS])
    assert c["UNRESOLVED"] == pytest.approx(-0.054)


def test_mark_he_does_not_have_is_count_at_the_engine_figure():
    t = R.decompose_mark([m("K6", 0.12, 0.50)], None)
    assert t["COUNT"] == pytest.approx(0.384) and t["residual"] == pytest.approx(0.384)


def test_metamorphic_member_order():
    mem = [m("K1", 0.125, 0.70), m("K2", 0.08, 0.50), m("K2b", 0.08, None, state="HELD")]
    ref = R.decompose_mark(mem, his(3, 0.10, 2.70))
    for p in itertools.permutations(mem):
        assert R.decompose_mark(list(p), his(3, 0.10, 2.70)) == ref


def test_lift_ring_scope():
    gross = round(1.80 ** 2 - 1.40 ** 2, 6)
    r = R.ring_scope(gross, 0.16, gross, 1.20)
    assert r["net_m2"] == pytest.approx(1.12) and r["double_on_gross_m3"] == pytest.approx(0.192)
    assert r["net_m3"] is None                               # pit depth not printed: HELD, never 0
    assert R.ring_scope(gross, 0.16, 1.12, 1.20)["double_on_gross_m3"] is None   # his net ring: no double


# ---------------- adverse cases

def test_height_to_slab_top_under_a_slab_that_bills_the_footprint_is_refused():
    with pytest.raises(R.Refused, match="DOUBLE"):
        R.column_solid(0.125, 0.95, 4.15, slab_top=4.15, slab_t=0.15, slab_bills_footprint=True)
    assert R.column_solid(0.125, 0.95, 4.00, slab_top=4.15, slab_t=0.15, slab_bills_footprint=True) == 0.38125


def test_height_through_a_beam_billed_through_is_refused():
    with pytest.raises(R.Refused, match="DOUBLE"):
        R.column_solid(0.125, 0.95, 4.15, slab_top=4.15, slab_t=0.15, slab_bills_footprint=False,
                       beam_through_depth=0.70)


def test_held_as_zero_refused():
    bad = m("K2-1F", 0.08, None, st=F1, state="HELD")
    bad["m3"] = 0.0
    with pytest.raises(R.Refused, match="never 0"):
        R.decompose_mark([bad], his(1, 0.08, 2.70, st=F1))


def test_ratio_closure_refused():
    with pytest.raises(R.Refused, match="ratio"):
        R.closure([{"term": "HEIGHT_GLOBAL_DEPTH", "m3": 0.05, "cause": "his height is 84 % of the storey"}])
    with pytest.raises(R.Refused):
        R.closure([{"term": "COUNT", "m3": 0.05, "cause": "scaling factor 1.1"}])


def test_unknown_term_and_unknown_state_refused():
    with pytest.raises(R.Refused):
        R.closure([{"term": "PLUG", "m3": 0.1, "cause": "balance"}])
    with pytest.raises(R.Refused):
        R.decompose_mark([{**m("K1", 0.125, 0.7), "state": "GUESS"}], his(1, 0.125, 2.7))


def test_units_mm_refused():
    with pytest.raises(R.Refused, match="mm"):
        R.column_solid(0.125, 950, 4150, slab_top=4150, slab_t=150, slab_bills_footprint=False)


def test_top_below_base_and_bad_section_refused():
    with pytest.raises(R.Refused):
        R.column_solid(0.125, 4.15, 0.95, slab_top=4.15, slab_t=0.15, slab_bills_footprint=False)
    with pytest.raises(R.Refused):
        R.column_solid(125.0, 0.95, 4.15, slab_top=4.15, slab_t=0.15, slab_bills_footprint=False)


def test_ring_column_pieces_outside_refused():
    with pytest.raises(R.Refused):
        R.ring_scope(1.28, 1.30, 1.28, 1.20)


# ---------------- Alsenan (committed inputs only; the freelancer side needs the private workbook)

def test_alsenan_column_lines_equal_the_v3029_binding_and_bind_one_to_one():
    import t394_alsenan as A
    lines, st = A.load_lines()
    assert len(lines) == 72
    t248 = [r for r in __import__("csv").DictReader((ROOT / "research" / "agents_t248" / "LEDGER_T248.csv")
                                                    .open(encoding="utf-8")) if r["storey"] in ("GF", "1F")]
    b = A.bind(lines, t248)
    assert len(b) == 53                                       # GF 30 + 1F 23 lines
    real = [v for v in b.values() if v != "SUPERSEDED_BY_HL"]
    assert len(real) == len(set(real)) == 51                  # 30 GF + 20 1F drawn outlines + 1F NOT_DRAWN 10E4
    assert sum(1 for v in b.values() if v == "SUPERSEDED_BY_HL") == 2
    valued = {k for k, s in st.items() if s == "VALUED"}
    gf = sum(lines[k]["measured_net"] for k in valued if lines[k]["floor"] == "GF")
    f1 = sum(lines[k]["measured_net"] for k in valued if lines[k]["floor"] == "1F")
    assert round(gf, 6) == 17.9675 and round(f1, 6) == 10.248


SUMMARY = HERE / "summary_t394.json"


@pytest.mark.skipif(not SUMMARY.exists(), reason="engine-side summary not committed")
def test_alsenan_summary_pinned():
    s = json.loads(SUMMARY.read_text(encoding="utf-8"))
    t = s["terms_engine_minus_freelancer_m3"]
    for st in ("GF", "1F"):
        assert sum(t[st][k] for k in R.TERM_KEYS) == pytest.approx(t[st]["residual"], abs=1e-6)
    assert s["engine"]["GF"]["engine_valued_m3"] == 17.9675 and s["engine"]["1F"]["engine_valued_m3"] == 10.248
    assert s["closure"]["GF"]["HELD"] < 0 and s["engine"]["GF"]["held"] == 5
    assert s["lift"]["bookkeeping_remainder"] == 0 and s["lift"]["net_m2"] == 1.1
