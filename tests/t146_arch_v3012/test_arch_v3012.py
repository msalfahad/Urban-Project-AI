"""T-146 + T-247: ARCH_TAKEOFF_V3.0.12, the SAME opt-in candidate as V3.0 .. V3.0.11 extended (engine.source.arch_v3012):
ONE slab / beam partition. The checker-merged beam ledger replaces the candidate's beam lines run by run (kept where a
line already carries its run) and every slab face that is not slab leaves the slab line for its home in that ledger
(or no concrete). Synthetic data only (no client drawing).

VILLA V-146 (not the development villa), one storey GF, convention C1 (panel between beam faces, beam at full depth).
Candidate (V3.0.11) lines and the ledger, hand values:
  slab panels  P1 4.00 x 5.00 x 0.16 = 3.200 m3, P2 3.00 x 2.50 x 0.16 = 1.200 m3            -> slab left 4.400 m3
  slab faces that are NOT slab (each billed at 0.16 by the candidate):
      F-RNG  0.20 m2 piece inside the drawn ring           0.032  -> home: ring run R
      F-CB   0.20 x 3.00 band of beam CB billed as slab    0.096  -> home: run CB (in no beam line before)
      F-STR  0.30 m2 strip outside the outer beam          0.048  -> home: HELD run S (no depth printed)
      F-BRK  0.05 m2 drafting break mark                   0.008  -> no concrete
                                                           0.184 m3 leave the slab line (4.584 -> 4.400)
  beam lines -> runs:
      B1   0.20 x 0.40 x 4.00 = 0.320 live; run B1 0.320                    -> KEPT byte-identical
      B2   0.25 x 0.50 x 3.00 = 0.375 live; run B2: oblique end, edges 3.00 / 3.20 -> 0.25 x 0.50 x 3.10 =
           0.3875, less its overlap with the drawn ring 0.002 m2 x 0.50 = 0.001         -> 0.3865 (superseded)
      B3a  0.20 x 0.60 x 2.00 = 0.240, B3b 0.240: one continuous run B3 through the carried member,
           0.20 x 0.60 x 4.20 = 0.504                                               -> 0.504 (both superseded)
      R1   0.150 live, R2 bounded 0.02 .. 0.06: arc bands of a quarter ring R 1.25 / 1.00,
           pi / 4 x (1.5625 - 1.00) = 0.441786 m2 x D 0.50 = 0.220893               -> ring run R 0.220893
      CW   0.20 x 0.50 x 3.00 = 0.300 at the schedule width; drawn 0.25: CONFLICT 0.300 .. 0.375 (HELD)
      S0   bounded 0.04 .. 0.12 (a depth range); depth not printed: run S HELD with no value (never 0)
      H2   bounded 0.05 .. 0.15 = run H2 HELD 0.05 .. 0.15                           -> KEPT byte-identical
      run CB 0.20 x 0.40 x 3.00 = 0.240 (no beam line before: its band was billed as slab)
  beam totals: measured 0.320 + 0.3865 + 0.504 + 0.220893 + 0.240 = 1.671393 m3; CONFLICT 0.300 .. 0.375;
  HELD 0.05 .. 0.15 + S with no value. Slab + beam measured = 4.400 + 1.671393 = 6.071393 m3, each piece once.
  Unrelated lines (a column, a footing) stay byte-identical.
"""

from __future__ import annotations

import copy
import math
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engine.source import arch_v30 as A30                      # noqa: E402
from engine.source import arch_v3012 as A                      # noqa: E402
from engine.source import boq_line as BL                       # noqa: E402

AP = pytest.approx
PID = "synthetic-v3012-villa-v146"
DOCS = [{"file": "V-STR.dxf", "sha256": "4" * 64}]
SLAB, BEAM = "STR.CONC.SLAB", "STR.CONC.BEAM"
RING_M2 = math.pi / 4 * (1.25 ** 2 - 1.00 ** 2)
RING_M3 = round(RING_M2 * 0.50, 6)


def line(eid, item, q=1.0, ev="PROVISIONAL", br=None, floor="GF"):
    return BL.make_line(project_id=PID, revision_set_sha256="0" * 64, item_code=item, unit="m3", evidence_state=ev,
                        measured_net=None if ev in ("BOUNDED_EXPOSURE", "BLOCKED_RFI") else q, bounded_range=br,
                        element_id=eid, floor=floor, physical_element=eid.split(":")[1], formula="route",
                        documents=DOCS, rule_id="SV", rule_version="1",
                        rfi={"question": "q", "unlocks": eid} if ev in ("BOUNDED_EXPOSURE", "BLOCKED_RFI") else None)


def bnd(lo, hi):
    return {"low": lo, "high": hi, "basis": "route"}


def l3011():
    return [line("P-C:SLABS:GF:P1", SLAB, 3.200), line("P-C:SLABS:GF:P2", SLAB, 1.200),
            line("P-C:SLABS:GF:F-RNG", SLAB, 0.032), line("P-C:SLABS:GF:F-CB", SLAB, 0.096),
            line("P-C:SLABS:GF:F-STR", SLAB, 0.048), line("P-C:SLABS:GF:F-BRK", SLAB, 0.008),
            line("P-C:BEAMS:GF:B1", BEAM, 0.320), line("P-C:BEAMS:GF:B2", BEAM, 0.375),
            line("P-C:BEAMS:GF:B3a", BEAM, 0.240), line("P-C:BEAMS:GF:B3b", BEAM, 0.240),
            line("P-C:BEAMS:GF:R1", BEAM, 0.150), line("U-C:BEAMS:GF:R2", BEAM, ev="BOUNDED_EXPOSURE", br=bnd(0.02, 0.06)),
            line("P-C:BEAMS:GF:CW", BEAM, 0.300), line("U-C:BEAMS:GF:S0", BEAM, ev="BOUNDED_EXPOSURE", br=bnd(0.04, 0.12)),
            line("U-C:BEAMS:GF:H2", BEAM, ev="BOUNDED_EXPOSURE", br=bnd(0.05, 0.15)),
            line("P-C:COLS:GF:C1", "STR.CONC.COLUMN", 0.40), line("P-C:FTG:F1", "STR.CONC.FOOTING", 1.10,
                                                                     floor="FOUNDATION")]


def src(task="T-BEAM"):
    return {"file": f"research/{task}/LEDGER.csv", "sha256": "e" * 64, "task": task, "merge_commit": "abc1234",
            "checker_run": f"verifier run for {task}"}


def ge(run):
    return {"element_id": f"BEAM-RUN:GF:{run}", "part": "WHOLE"}


def runs():
    return [
        {"run": "B2", "floor": "GF", "mark": "B2", "status": "CALCULATED", "base": 0.3875,
         "adjust": [{"what": "overlap with the drawn ring 0.002 m2 x D 0.50", "m3": 0.001, "why": "ring once"}],
         "value": 0.3865, "supersedes": ["P-C:BEAMS:GF:B2"], "source": "edges 3.00 / 3.20 to the oblique face",
         "verified_by": "checker batch GF", "guard_element": ge("B2")},
        {"run": "B3", "floor": "GF", "mark": "B3", "status": "CALCULATED", "base": 0.504, "value": 0.504,
         "supersedes": ["P-C:BEAMS:GF:B3a", "P-C:BEAMS:GF:B3b"], "source": "continuous 4.20 m through the carried "
         "member", "verified_by": "checker batch GF", "guard_element": ge("B3")},
        {"run": "R", "floor": "GF", "mark": "R", "status": "CALCULATED", "base": RING_M3, "value": RING_M3,
         "supersedes": ["P-C:BEAMS:GF:R1", "U-C:BEAMS:GF:R2"], "source": "quarter ring between its own arcs",
         "guard_element": ge("R")},
        {"run": "CB", "floor": "GF", "mark": "CB", "status": "CALCULATED", "base": 0.240, "value": 0.240,
         "supersedes": [], "source": "CB span 2, edges 3.00 m, schedule 20 x 40", "verified_by": "checker batch GF",
         "guard_element": ge("CB")},
        {"run": "CW", "floor": "GF", "mark": "CW", "status": "CONFLICT", "range": [0.300, 0.375],
         "supersedes": ["P-C:BEAMS:GF:CW"], "reasons": ["schedule width 0.20 vs drawn 0.25 (designer)"],
         "evidence_status": "HELD", "source": "schedule row CW; drawn edges", "guard_element": ge("CW")},
        {"run": "S", "floor": "GF", "mark": "(none)", "status": "HELD", "supersedes": ["U-C:BEAMS:GF:S0"],
         "reasons": ["strip outside the outer beam, depth not printed (designer)"], "evidence_status": "HELD",
         "source": "partition face F-STR", "guard_element": ge("S")},
    ]


def beam_piece(**kw):
    p = {"piece": "BEAM_LEDGER", "item_code": BEAM, "unit": "m3", "source": src(),
         "scope": {"floors": ["GF"],
                   "keep_lines": [
                       {"element_id": "P-C:BEAMS:GF:B1", "floor": "GF", "run": "B1", "run_status": "CALCULATED",
                        "carried": 0.320, "ledger": 0.320, "why": "already the run"},
                       {"element_id": "U-C:BEAMS:GF:H2", "floor": "GF", "run": "H2", "run_status": "HELD",
                        "carried": [0.05, 0.15], "ledger": [0.05, 0.15], "why": "already the run's range"}],
                   "supersede_lines": [
                       {"element_id": e, "floor": "GF", "carried": c, "why": "band of a ledger run"}
                       for e, c in (("P-C:BEAMS:GF:B2", 0.375), ("P-C:BEAMS:GF:B3a", 0.240),
                                    ("P-C:BEAMS:GF:B3b", 0.240), ("P-C:BEAMS:GF:R1", 0.150),
                                    ("U-C:BEAMS:GF:R2", [0.02, 0.06]), ("P-C:BEAMS:GF:CW", 0.300),
                                    ("U-C:BEAMS:GF:S0", [0.04, 0.12]))]},
         "records": runs(),
         "declared_totals": {"measured": round(0.320 + 0.3865 + 0.504 + RING_M3 + 0.240, 6),
                             "conflict": [0.300, 0.375], "held": [0.05, 0.15], "held_no_value": ["S"]}}
    p.update(kw)
    return p


def slab_piece(**kw):
    def f(eid, carried, home, why="not slab"):
        return {"element_id": f"P-C:SLABS:GF:{eid}", "floor": "GF", "face": eid, "carried": carried, "why": why,
                "home": home}
    p = {"piece": "SLAB_FACE_HOME", "item_code": SLAB, "unit": "m3", "source": src("T-SLAB"),
         "faces": [f("F-RNG", 0.032, {"kind": "BEAM_RUN", "run": "R"}),
                   f("F-CB", 0.096, {"kind": "BEAM_RUN", "run": "CB"}),
                   f("F-STR", 0.048, {"kind": "BEAM_RUN", "run": "S"}),
                   f("F-BRK", 0.008, {"kind": "NOT_CONCRETE", "evidence": "drafting break mark"})],
         "declared_after": {"GF": {"drawing": 4.400, "tol_m3": 0.0005, "residual_why": "none"}}}
    p.update(kw)
    return p


def inputs(beam=None, slab=None, pieces=None):
    return {"schema": A.INPUTS_SCHEMA, "project": PID,
            "pieces": pieces if pieces is not None else [beam or beam_piece(), slab or slab_piece()]}


def run(inp=None, lines=None, earlier=()):
    lines = lines or l3011()
    doc = A.load_inputs(inp or inputs(), PID)
    ch, logs = A.changes_for(doc, lines, earlier)
    out, ident = A.integrate(lines, ch)
    return out, ch, logs, ident, lines


def by_eid(out):
    return {ln["location"]["element_id"]: ln for ln in out}


def live(out, item):
    return sum(ln["measured_net"] for ln in out if ln["item_code"] == item
               and ln["evidence_state"] in A.LIVE_EVIDENCE and ln["measured_net"] is not None)


# ------------------------------------------------------------------------------------------------ normal
def test_villa_v146_hand_values_slab_and_beam_once():
    assert RING_M2 == AP(0.441786, abs=1e-6)
    out, ch, logs, ident, lines = run()
    assert live(lines, SLAB) == AP(4.584)
    assert live(out, SLAB) == AP(4.400)
    assert live(out, BEAM) == AP(1.671393, abs=1e-6)
    assert live(out, SLAB) + live(out, BEAM) == AP(6.071393, abs=1e-6)
    beam = next(lg for lg in logs if lg["piece"] == "BEAM_LEDGER")
    assert beam["totals"]["measured"] == AP(1.671393, abs=1e-6)
    assert beam["totals"]["conflict"] == [AP(0.300), AP(0.375)]
    assert beam["totals"]["held"] == [AP(0.05), AP(0.15)]
    assert beam["totals"]["held_no_value"] == ["S"]
    slab = next(lg for lg in logs if lg["piece"] == "SLAB_FACE_HOME")
    assert slab["totals"]["retired_m3"] == AP(0.184)
    assert slab["totals"]["to_beam_run"] == AP(0.176) and slab["totals"]["not_concrete"] == AP(0.008)
    assert slab["by_floor"]["GF"]["residual_m3"] == AP(0.0, abs=1e-9)
    # 4 slab faces + 7 beam lines replaced; 6 runs added; 2 kept + 2 panels + 2 unrelated outside
    assert ident["replaced"] == 11 and ident["added"] == 6 and ident["outside_rows"] == 6


def test_kept_and_unrelated_lines_byte_identical():
    out, _ch, _lg, _id, lines = run()
    o, b = by_eid(out), by_eid(lines)
    for e in ("P-C:BEAMS:GF:B1", "U-C:BEAMS:GF:H2", "P-C:SLABS:GF:P1", "P-C:SLABS:GF:P2", "P-C:COLS:GF:C1",
              "P-C:FTG:F1"):
        assert A30.line_sha(o[e]) == A30.line_sha(b[e])


def test_superseded_lines_kept_as_information_never_summed():
    out, ch, *_ = run()
    o = by_eid(out)
    for e in ("P-C:BEAMS:GF:B2", "P-C:BEAMS:GF:B3a", "P-C:BEAMS:GF:B3b", "P-C:BEAMS:GF:R1", "U-C:BEAMS:GF:R2",
              "P-C:BEAMS:GF:CW", "U-C:BEAMS:GF:S0", "P-C:SLABS:GF:F-RNG", "P-C:SLABS:GF:F-CB",
              "P-C:SLABS:GF:F-STR", "P-C:SLABS:GF:F-BRK"):
        ln = o[e]
        assert ln["evidence_state"] == "NOT_APPLICABLE_WITH_EVIDENCE" and ln["measured_net"] is None
        assert A.METHOD in ln["notes"]
    homes = {c["before"]["location"]["element_id"]: c["codes"] for c in ch if c["piece"] == "SLAB_FACE_HOME"}
    assert "COUNTED_BY R" in homes["P-C:SLABS:GF:F-RNG"] and "HOME_NOT_CONCRETE" in homes["P-C:SLABS:GF:F-BRK"]


def test_run_lines_states_and_statuses():
    out, ch, *_ = run()
    o = by_eid(out)
    b2 = o["HL:BEAM_LEDGER:GF:B2"]
    assert b2["evidence_state"] == "SOURCE_DERIVED" and b2["measured_net"] == AP(0.3865)
    assert b2["calculation"]["inputs"]["base_m3"] == AP(0.3875)
    cw = o["HL:BEAM_LEDGER:GF:CW"]
    assert cw["evidence_state"] == "BOUNDED_EXPOSURE" and cw["measured_net"] is None
    assert (cw["bounded_range"]["low"], cw["bounded_range"]["high"]) == (AP(0.300), AP(0.375))
    assert cw["bounded_range"]["basis"].startswith("CONFLICT")
    s = o["HL:BEAM_LEDGER:GF:S"]
    assert s["evidence_state"] == "BLOCKED_RFI" and s["measured_net"] is None and s["bounded_range"] is None
    st = {c["after"]["location"]["element_id"]: c["evidence_status"] for c in ch if c["action"] == "ADD"}
    assert st["HL:BEAM_LEDGER:GF:B2"] == "VERIFIED" and st["HL:BEAM_LEDGER:GF:R"] == "DRAWING-CONFIRMED"
    assert st["HL:BEAM_LEDGER:GF:CW"] == "HELD" and st["HL:BEAM_LEDGER:GF:S"] == "HELD"


def test_slab_piece_alone_refused_when_a_face_goes_to_the_beam_lane():
    with pytest.raises(A.InputsError, match="SAME package"):
        A.load_inputs(inputs(pieces=[slab_piece()]), PID)


def test_beam_piece_alone_runs_and_leaves_slab_untouched():
    out, _ch, logs, ident, lines = run(inputs(pieces=[beam_piece()]))
    assert live(out, SLAB) == AP(live(lines, SLAB))
    assert ident["replaced"] == 7 and ident["added"] == 6


def test_no_project_input_changes_nothing():
    lines = l3011()
    ch, logs = A.changes_for(None, lines)
    out, ident = A.integrate(lines, ch)
    assert ident["replaced"] == 0 and ident["added"] == 0 and len(out) == len(lines)


def test_kept_blocked_held_run_counts_as_held_with_no_value():
    lines = l3011() + [line("HL:RING:EAST", BEAM, ev="BLOCKED_RFI")]
    bp = beam_piece()
    bp["scope"]["keep_lines"].append({"element_id": "HL:RING:EAST", "floor": "GF", "run": "E", "run_status": "HELD",
                                      "carried": "BLOCKED", "ledger": [0.9, 0.9], "ledger_info": "B4-size candidate",
                                      "why": "the candidate already holds it with no value"})
    bp["declared_totals"]["held_no_value"] = ["E", "S"]
    out, _ch, logs, *_ = run(inputs(beam=bp), lines)
    assert logs[0]["totals"]["held_no_value"] == ["E", "S"]


# ------------------------------------------------------------------------------------------------ adverse
def test_unaccounted_beam_line_refused():
    bp = beam_piece()
    bp["scope"]["keep_lines"] = bp["scope"]["keep_lines"][1:]          # B1 neither kept nor superseded
    bp["declared_totals"] = {}
    with pytest.raises(A.InputsError, match="only adds is refused"):
        run(inputs(beam=bp))


def test_kept_line_that_differs_from_its_run_refused():
    bp = beam_piece()
    bp["scope"]["keep_lines"][0]["ledger"] = 0.330
    with pytest.raises(A.InputsError, match="superseded"):
        A.load_inputs(inputs(beam=bp), PID)


def test_run_kept_and_added_refused():
    bp = beam_piece()
    bp["records"].append(dict(runs()[3], run="B1", supersedes=[], guard_element=ge("B1")))
    with pytest.raises(A.InputsError, match="counted twice"):
        A.load_inputs(inputs(beam=bp), PID)


def test_superseded_line_with_no_run_refused():
    bp = beam_piece()
    bp["records"][1]["supersedes"] = ["P-C:BEAMS:GF:B3a"]
    with pytest.raises(A.InputsError, match="no run that replaces them"):
        A.load_inputs(inputs(beam=bp), PID)


def test_face_home_not_a_run_of_this_package_refused():
    sp = slab_piece()
    sp["faces"][0]["home"] = {"kind": "BEAM_RUN", "run": "R-ELSEWHERE"}
    with pytest.raises(A.InputsError, match="for no line"):
        A.load_inputs(inputs(slab=sp), PID)


def test_not_concrete_without_evidence_refused():
    sp = slab_piece()
    sp["faces"][3]["home"] = {"kind": "NOT_CONCRETE"}
    with pytest.raises(A.InputsError, match="drawing evidence"):
        A.load_inputs(inputs(slab=sp), PID)


@pytest.mark.parametrize("rg,msg", [(None, "never one reading"), ([0.300, 0.300], "two distinct readings"),
                                    ([0.0, 0.375], "never 0"), ([300.0, 375.0], "unit slip")])
def test_conflict_must_carry_both_readings_in_m3(rg, msg):
    bp = beam_piece()
    bp["records"][4]["range"] = rg
    with pytest.raises(A.InputsError, match=msg):
        A.load_inputs(inputs(beam=bp), PID)


def test_held_run_with_a_value_refused():
    bp = beam_piece()
    bp["records"][5]["value"] = 0.0
    with pytest.raises(A.InputsError, match="no released value"):
        A.load_inputs(inputs(beam=bp), PID)


def test_calculated_value_must_equal_base_less_adjustments():
    bp = beam_piece()
    bp["records"][0]["value"] = 0.3875                                  # the overlap not removed
    with pytest.raises(A.InputsError, match="less its adjustments"):
        A.load_inputs(inputs(beam=bp), PID)


@pytest.mark.parametrize("v", [387.5, 387500.0])
def test_calculated_run_in_wrong_units_refused(v):
    bp = beam_piece()
    bp["records"][0].update(base=v, adjust=[], value=v)
    with pytest.raises(A.InputsError, match="unit slip"):
        A.load_inputs(inputs(beam=bp), PID)


def test_calculated_run_held_status_refused():
    bp = beam_piece()
    bp["records"][0]["evidence_status"] = "HELD"
    with pytest.raises(A.InputsError, match="cannot be HELD"):
        A.load_inputs(inputs(beam=bp), PID)


def test_slab_left_not_equal_to_the_ledger_refused():
    sp = slab_piece()
    sp["faces"] = sp["faces"][:3]                                       # the break mark stays in the slab line
    sp["declared_after"]["GF"]["drawing"] = 4.400
    with pytest.raises(ValueError, match="a face is missing"):
        run(inputs(slab=sp))


def test_slab_face_retired_twice_or_not_live_refused():
    lines = l3011()
    for ln in lines:
        if ln["location"]["element_id"] == "P-C:SLABS:GF:F-BRK":
            ln.update(evidence_state="BOUNDED_EXPOSURE", measured_net=None, bounded_range=bnd(0.0, 0.008),
                      rfi={"question": "q", "unlocks": "x"})
    with pytest.raises(A.InputsError, match="only a live slab line"):
        run(lines=lines)


def test_carried_figure_must_be_the_lines_own():
    bp = beam_piece()
    bp["scope"]["supersede_lines"][0]["carried"] = 0.400
    with pytest.raises(A.InputsError, match="the superseded figure must be the one the line carries"):
        run(inputs(beam=bp))
    sp = slab_piece()
    sp["faces"][1]["carried"] = 0.100
    with pytest.raises(A.InputsError, match="the inputs state"):
        run(inputs(slab=sp))


def test_declared_totals_must_match():
    bp = beam_piece()
    bp["declared_totals"]["measured"] = 1.700
    with pytest.raises(ValueError, match="declared"):
        run(inputs(beam=bp))


def test_approved_line_never_replaced():
    lines = l3011()
    for ln in lines:
        if ln["location"]["element_id"] == "P-C:BEAMS:GF:B2":
            ln["approval_state"] = "APPROVED"
    with pytest.raises(ValueError, match="never replaced"):
        run(lines=lines)


def test_earlier_change_must_be_named():
    lines = l3011()
    lid = next(ln["line_id"] for ln in lines if ln["location"]["element_id"] == "P-C:BEAMS:GF:CW")
    with pytest.raises(A.InputsError, match="earlier candidate version"):
        run(lines=lines, earlier={lid})
    bp = beam_piece()
    for x in bp["scope"]["supersede_lines"]:
        if x["element_id"] == "P-C:BEAMS:GF:CW":
            x["earlier_change"] = "V3.0.x held it; the ledger run replaces it"
    run(inputs(beam=bp), lines=lines, earlier={lid})


def test_run_twice_in_the_lines_refused():
    out, *_ = run()
    dup = copy.deepcopy(next(ln for ln in out if ln["location"]["element_id"] == "HL:BEAM_LEDGER:GF:B2"))
    dup["line_id"] = "L-duplicate"
    with pytest.raises(ValueError, match="appears twice"):
        A.check_partition(out + [dup])


def test_wrong_schema_or_project_refused():
    with pytest.raises(A.InputsError, match="schema"):
        A.load_inputs(dict(inputs(), schema="URBAN_V3011_INPUTS_V1"), PID)
    with pytest.raises(A.InputsError, match="are for"):
        A.load_inputs(inputs(), "another-project")
