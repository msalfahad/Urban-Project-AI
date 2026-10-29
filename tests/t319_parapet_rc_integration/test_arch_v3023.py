"""T-319: ARCH_TAKEOFF_V3.0.23 (the RC part of every roof / terrace parapet run as its own concrete line family,
STR.CONC.PARAPET, one HELD BLANK line per roof chain with its bound) on a hand-calculated NON-Alsenan villa (P319),
normal and adverse.

Villa P319, by hand (upstand printed 0.30 m above the structural slab top in every alternative; b_edge HELD):
  roof R1 (+7.00):
    N   straight, centreline 10.000 x t 0.20 = top 2.000 m2; printed h 1.00 above the finished roof:
        floor 0.30 x 2.000 = 0.600 m3; all RC at b_edge 0: 2.000 x 1.00 = 2.000 m3; +2.000 m3 per m of b_edge.
    E   quarter arc r 2.0: centreline pi = 3.141593 x 0.20 = top 0.628319 m2; h 1.00: floor 0.188496, all RC 0.628319.
    S   centreline 6.000 x t 0.15 = top 0.900 m2; h HELD 0.80 .. 1.20 (elevations disagree): floor 0.270, all RC
        0.720 .. 1.080.
    R1: top 3.528319 m2, floor 1.058496 m3, all RC 3.348319 .. 3.708319 m3 + 3.528319 m3 per m of b_edge.
  roof R2 (+10.20):
    W   centreline 4.000 x t 0.25 = top 1.000 m2; h 0.60: floor 0.300, all RC 0.600; block alternative 0 .. 4.000 x
        (0.60 - 0.30) = 1.200 m2 (exclusive, never added).
    N   end on a D band: centreline 2.000 .. 2.200 x 0.20 = top 0.400 .. 0.440 (HELD); h 0.60: floor 0.120, all RC
        0.240 .. 0.264.
    R2: top 1.400 .. 1.440 m2, floor 0.420 m3, all RC 0.840 .. 0.864 m3 + 1.440 m3 per m of b_edge.
  Both lines BLOCKED (HELD, blank: no figure, no range); floor total 1.478496 m3 (AT_LEAST, any b_edge).
"""
from __future__ import annotations

import copy
import math
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engine.source import arch_v30 as A30  # noqa: E402
from engine.source import arch_v3023 as A  # noqa: E402
from engine.source import boq_line as BL  # noqa: E402
from tools import t334_line_state_check as LS  # noqa: E402

PID, REV = "villa-p319", "e" * 64
DOCS = [{"file": "p319_st.dxf", "sha256": "d" * 64}]
PRINTED = "printed height above the finished roof (section S1)"


def _ln(code, eid, ev, net=None, floor="1F", unit="m3", notes="p319", formula="p319 candidate"):
    return BL.make_line(project_id=PID, revision_set_sha256=REV, item_code=code, unit=unit, evidence_state=ev,
                        measured_net=net, element_id=eid, floor=floor, physical_element="member", formula=formula,
                        documents=DOCS, rule_id="R", rule_version="1",
                        rfi={"question": "block type not read"} if ev == "BLOCKED_RFI" else None, notes=notes)


def lines_3022():
    return [_ln("STR.CONC.BEAM", "B1", "SOURCE_DERIVED", 3.2, notes="edge beam to its scheduled depth"),
            _ln("STR.CONC.SLAB", "S1", "SOURCE_DERIVED", 12.5),
            _ln("MAS.BLOCK", "W1", "BLOCKED_RFI", unit="m2", floor="GF")]


def _run(run, cl, t, h, kind="STRAIGHT", held_h=False, block=None, note=None, cl_hi=None, task="T-P1"):
    cl_hi = cl if cl_hi is None else cl_hi
    hl, hh = (h, h) if not isinstance(h, tuple) else h
    return {"run": run, "kind": kind, "t_m": t, "centreline_lo_m": cl, "centreline_hi_m": cl_hi,
            "top_lo_m2": round(cl * t, 6), "top_hi_m2": round(cl_hi * t, 6), "h_lo_m": hl, "h_hi_m": hh,
            "h_source": PRINTED if not held_h else "elevations disagree: HELD range",
            "h_status": "HELD" if held_h else None,
            "geometry_status": "HELD (D band)" if cl_hi > cl else "DRAWING-CONFIRMED", "material": "HELD",
            "block_alt_m2": block if block is not None else [0.0, round(cl_hi * (hh - 0.30), 6)],
            "block_alt_note": note, "source_task": task, "corrections": []}


def doc():
    r1 = [_run("N", 10.0, 0.20, 1.00), _run("E", round(math.pi, 6), 0.20, 1.00, kind="ARC"),
          _run("S", 6.0, 0.15, (0.80, 1.20), held_h=True)]
    r2 = [_run("W", 4.0, 0.25, 0.60), _run("N", 2.0, 0.20, 0.60, cl_hi=2.2)]
    chains = [{"chain": "R1", "floor": "1F", "roof_level": "+7.00", "element_id": "R1#PARAPET_RC", "task": "T-P1",
               "material_status": "HELD", "material_item": "designer: detail per run", "b_edge_item": "build-up HELD",
               "runs": r1, "exclusive": ["block above the upstand: MAS.BLOCK, never added"], "downstream": ["formwork"]},
              {"chain": "R2", "floor": "2F", "roof_level": "+10.20", "element_id": "R2#PARAPET_RC", "task": "T-P1",
               "material_status": "HELD", "material_item": "designer: detail per run", "b_edge_item": "build-up HELD",
               "runs": r2}]
    allr = r1 + r2
    return {"schema": A.INPUTS_SCHEMA, "project": PID,
            "sources": [{"file": "p319_runs.csv", "sha256": "c" * 64, "task": "T-P1", "merge_commit": "m1",
                         "checker_run": "checker c1"}],
            "upstand": {"floor_m": 0.30, "source": "detail P: RC upstand 30 above the slab top", "status": A.DC,
                        "checker_run": "checker c1", "lower_bound_rule": "top x max(0.30, b_edge + margin)"},
            "chains": chains,
            "excluded": [{"what": "a band outside the outer face", "evidence": "no roof on either side",
                          "owner": "facade frames", "status": "UNKNOWN"}],
            "declared": {"lines": 2, "top_lo_m2": sum(u["top_lo_m2"] for u in allr),
                         "top_hi_m2": sum(u["top_hi_m2"] for u in allr),
                         "floor_m3": sum(u["top_lo_m2"] * 0.30 for u in allr),
                         "all_rc_printed_lo_m3": sum(u["top_lo_m2"] * u["h_lo_m"] for u in allr),
                         "all_rc_printed_hi_m3": sum(u["top_hi_m2"] * u["h_hi_m"] for u in allr)}}


def run(d=None, ls=None):
    ls = ls or lines_3022()
    d = A.load_inputs(d or doc())
    ch, logs, rows = A.changes_for(d, ls)
    out, ident = A.integrate(ls, ch)
    return ls, ch, logs, rows, out, ident


def _par(out):
    return {ln["location"]["element_id"]: ln for ln in out if ln["item_code"] == A.PARAPET}


# ------------------------------------------------------------------------------------------------ normal
def test_hand_fixture_two_chains_held_blank_with_bound():
    ls, ch, logs, rows, out, ident = run()
    p = _par(out)
    assert set(p) == {"R1#PARAPET_RC", "R2#PARAPET_RC"}
    for ln in p.values():
        assert ln["evidence_state"] == "BLOCKED_RFI"
        assert ln["measured_net"] is None and ln["bounded_range"] is None and ln["gross"] is None
        assert ln["unit"] == "m3" and ln["trade"] == "CONCRETE" and ln["rfi"]["question"]
    b1 = p["R1#PARAPET_RC"]["calculation"]["inputs"]["parapet_rc_v3023"]["bound"]
    assert b1["top_m2"] == [3.528319, 3.528319]
    assert b1["floor_at_least_m3"] == pytest.approx(1.058496, abs=1e-6)
    assert b1["all_rc_printed_part_m3"] == [pytest.approx(3.348319, abs=1e-6), pytest.approx(3.708319, abs=1e-6)]
    assert b1["held_increment_m3_per_m_b_edge"] == pytest.approx(3.528319, abs=1e-6)
    assert b1["floor_status"] == A.DC and "max(" in b1["lower_bound"]
    b2 = p["R2#PARAPET_RC"]["calculation"]["inputs"]["parapet_rc_v3023"]["bound"]
    assert b2["top_m2"] == [1.4, 1.44]
    assert b2["floor_at_least_m3"] == pytest.approx(0.42, abs=1e-9)
    assert b2["all_rc_printed_part_m3"] == [pytest.approx(0.84), pytest.approx(0.864)]
    assert b2["block_alternative_m2"] == [0.0, pytest.approx(1.2 + 0.66)]      # W 1.200 + N 2.2 x 0.30
    assert logs[0]["floor_at_least_m3"] == pytest.approx(1.478496, abs=1e-6)
    assert ident["added"] == 2 and ident["replaced"] == 0
    assert ident["parapet_family"] == {"lines": 2, "blank": 2, "floor_at_least_m3": pytest.approx(1.478496, abs=1e-6),
                                       "runs": 5}
    assert len(rows) == 5 and {r["chain"] for r in rows} == {"R1", "R2"}


def test_every_v3_0_22_line_byte_identical_and_totals_do_not_move():
    ls, ch, logs, rows, out, ident = run()
    assert [A30.line_sha(x) for x in out[:len(ls)]] == [A30.line_sha(x) for x in ls]
    t = BL.totals(out, by=("floor",))
    t0 = BL.totals(ls, by=("floor",))
    assert t[("1F",)]["m3"]["net"] == t0[("1F",)]["m3"]["net"]               # held lines never summed
    assert t[("1F",)]["m3"]["blocked_lines"] == 1 and t[("2F",)]["m3"]["blocked_lines"] == 1
    assert t[("2F",)]["m3"]["net"] == 0.0 and t[("2F",)]["m3"]["lines"] == 0


def test_line_state_check_reads_the_parapet_lines_ok():
    _ls, _ch, _logs, _rows, out, _i = run()
    for ln in _par(out).values():
        res = LS.check_line(ln)
        assert res["category"] == LS.OK, res
        assert LS.formula_figure(ln["calculation"]["formula"], "m3") == (None, None)   # no concluding figure


def test_mirror_and_order_do_not_move_the_result():
    _ls, _ch, _l, _r, out, _i = run()
    d = doc()
    d["chains"] = list(reversed(d["chains"]))
    for c in d["chains"]:
        c["runs"] = list(reversed(c["runs"]))
    _ls2, _ch2, _l2, _r2, out2, _i2 = run(d)
    p1, p2 = _par(out), _par(out2)
    assert set(p1) == set(p2)
    for k in p1:
        assert p1[k]["line_id"] == p2[k]["line_id"]
        b1 = p1[k]["calculation"]["inputs"]["parapet_rc_v3023"]["bound"]
        b2 = p2[k]["calculation"]["inputs"]["parapet_rc_v3023"]["bound"]
        assert b1 == b2


def test_dimensions_in_metres_only_mm_refused():
    d = doc()
    d["chains"][0]["runs"][0]["h_lo_m"] = d["chains"][0]["runs"][0]["h_hi_m"] = 1000.0
    with pytest.raises(A.InputsError, match="outside"):
        A.load_inputs(d)
    d = doc()
    d["chains"][0]["runs"][0]["t_m"] = 200.0
    with pytest.raises(A.InputsError, match="thickness"):
        A.load_inputs(d)


# ------------------------------------------------------------------------------------------------ adverse
def test_run_in_two_lines_refused():
    d = doc()
    d["chains"][1]["runs"].append(copy.deepcopy(d["chains"][1]["runs"][0]))
    with pytest.raises(A.InputsError, match="named twice"):
        A.load_inputs(d)


def test_defaulted_height_refused():
    d = doc()
    d["chains"][0]["runs"][0]["h_source"] = ""
    with pytest.raises(A.InputsError, match="h_source"):
        A.load_inputs(d)
    d = doc()
    d["chains"][0]["runs"][0]["h_lo_m"] = None
    with pytest.raises(A.InputsError, match="never a default"):
        A.load_inputs(d)


def test_height_range_not_held_refused():
    d = doc()
    d["chains"][0]["runs"][2]["h_status"] = None
    with pytest.raises(A.InputsError, match="HELD"):
        A.load_inputs(d)


def test_top_not_centreline_times_thickness_refused():
    d = doc()
    d["chains"][0]["runs"][0]["top_lo_m2"] = d["chains"][0]["runs"][0]["top_hi_m2"] = 2.2
    with pytest.raises(A.InputsError, match="plan footprint"):
        A.load_inputs(d)


def test_missing_top_refused_never_zero():
    d = doc()
    r = d["chains"][0]["runs"][0]
    r["top_lo_m2"] = r["top_hi_m2"] = r["centreline_lo_m"] = r["centreline_hi_m"] = 0.0
    with pytest.raises(A.InputsError, match="never 0"):
        A.load_inputs(d)


def test_rc_and_block_on_one_run_refused():
    d = doc()
    d["chains"][1]["runs"][0]["material"] = "RC"           # its block alternative 0 .. 1.200 m2 stays
    with pytest.raises(A.InputsError, match="RC OR block"):
        A.load_inputs(d)
    d = doc()
    d["chains"][1]["runs"][0]["material"] = "BLOCK"         # the upstand would vanish from the concrete
    with pytest.raises(A.InputsError, match="upstand"):
        A.load_inputs(d)


def test_block_alternative_missing_without_reason_refused():
    d = doc()
    d["chains"][1]["runs"][0]["block_alt_m2"] = None
    with pytest.raises(A.InputsError, match="block_alt_note"):
        A.load_inputs(d)
    d["chains"][1]["runs"][0]["block_alt_note"] = "found after the block ledger; the blockwork binding owes it"
    _ls, _ch, _l, _r, out, _i = run(d)
    rec = _par(out)["R2#PARAPET_RC"]["calculation"]["inputs"]["parapet_rc_v3023"]
    assert rec["bound"]["block_alternative_not_booked"] == ["W"]
    assert [r["block_alternative_m2"] for r in rec["runs"] if r["run"] == "W"] == [None]


def test_parapet_already_in_a_beam_line_refused():
    ls = lines_3022()
    ls[0] = _ln("STR.CONC.BEAM", "B1", "SOURCE_DERIVED", 3.9, notes="edge beam + parapet upstand to the coping")
    with pytest.raises(A.InputsError, match="names a parapet"):
        run(ls=ls)


def test_second_parapet_carrier_refused():
    ls = lines_3022() + [_ln("STR.CONC.PARAPET", "X#PARAPET", "SOURCE_DERIVED", 1.0)]
    with pytest.raises(A.InputsError, match="second carrier"):
        run(ls=ls)


def test_held_line_summed_into_a_total_refused():
    ls, ch, _logs, _rows, _out, _i = run()
    bad = copy.deepcopy(ch)
    bad[0]["after"]["evidence_state"] = "PROVISIONAL"
    bad[0]["after"]["measured_net"] = 2.0                  # a midpoint written as the quantity
    bad[0]["after"]["rfi"] = None
    with pytest.raises(ValueError, match="never summed"):
        A.integrate(ls, bad)


def test_floor_without_checker_run_refused():
    d = doc()
    d["upstand"]["checker_run"] = None
    with pytest.raises(A.InputsError, match="checker run"):
        A.load_inputs(d)
    d = doc()
    d["upstand"]["source"] = ""
    with pytest.raises(A.InputsError, match="printed source"):
        A.load_inputs(d)


def test_declared_total_edited_refused():
    d = doc()
    d["declared"]["floor_m3"] += 0.01
    with pytest.raises(A.InputsError, match="declared floor_m3"):
        A.load_inputs(d)


def test_material_settled_without_detail_refused():
    d = doc()
    d["chains"][0]["material_status"] = "RC"
    with pytest.raises(A.InputsError, match="Q-65 C"):
        A.load_inputs(d)


def test_excluded_item_without_evidence_refused():
    d = doc()
    d["excluded"][0]["evidence"] = ""
    with pytest.raises(A.InputsError, match="excluded 0"):
        A.load_inputs(d)


def test_v3022_line_changed_refused():
    ls, ch, _logs, _rows, _out, _i = run()
    bad = ch + [{"piece": "DEFAULT_GUARD", "action": "REPLACE", "before": ls[0],
                 "after": dict(copy.deepcopy(ls[0]), notes="changed")}]
    with pytest.raises(ValueError, match="byte-identical"):
        A.integrate(ls, bad)


def test_no_project_input_changes_nothing():
    ch, logs, rows = A.changes_for(None, lines_3022())
    assert ch == [] and rows == [] and logs[0]["state"] == "NO_PROJECT_INPUT"
