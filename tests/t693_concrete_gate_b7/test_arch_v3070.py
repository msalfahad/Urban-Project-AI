"""T-693: ARCH_TAKEOFF_V3.0.70 (CONCRETE_GATE_B_V7, R-T693-1) on the hand-calculated NON-Alsenan villa K693 (own
figures, no drawing). Printed: a 1F roof beam B1 20 x 60 between columns C2 and C5; a window W1 drawn under B1 with its
head at +8.40 (read tolerance 0.010) and a second window W2 head +8.40 (tol 0.015); the 1F roof slab top is not
printed, the finished roof mark is +9.80; the 1F column base is +6.00 (approved).
  C2  0.20 x 0.40 (schedule = drawn), HELD 0.08 x 2.70 = 0.216 .. 0.08 x 3.80 = 0.304 (an older plate datum).
      B1 joint: top >= max(8.40 - 0.010, 8.40 - 0.015) + 0.60 = 8.99 -> h >= 2.99 -> NARROW 0.2392 .. 0.304.
  C5  blank; drawn outline 0.50 x 0.20 = 0.10 m2 vs schedule 20 x 40 = 0.08 m2 (CONFLICT): BOUND
      0.08 x 2.99 = 0.2392 .. 0.10 x 3.80 = 0.38.
  A1  annex column blank, drawn 0.20 x 0.30 = 0.06 vs schedule 25 x 30 = 0.075 m2; base +0.20, slab top >= 3.19 on one
      plane (R-T678-2 record), finished +3.60: h 2.99 .. 3.40 -> BOUND 0.06 x 2.99 = 0.1794 .. 0.075 x 3.40 = 0.255.
  C9  a 1F column NOT under B1 (HELD 0.216 .. 0.304): the B1 joint bound is refused for it (plate transfer, F-T689-1).
  W   a column whose only datum is a window head with NO printed beam over it: refused, the line stays HELD blank.
  GS  a released ground-slab face 0.114 m3 the detector labels BEAM_STRIP: OWNER record GROUND_SLAB, 0.114 unchanged.
  CR  a released column 0.36; a plaster line 44.31 m2: untouched.
COLUMN totals (m3): released 0.36 unchanged; held 0.432 .. 0.608 (C2 + C9, 2 bounded, 3 blank)
  -> 0.432 + 0.0232 + 0.2392 + 0.1794 = 0.8738 .. 0.608 + 0.38 + 0.255 = 1.243 (4 bounded, 1 blank: W).
Mirror order and metres: the same figures in any entry order; a section read in cm (20 for 0.20) is refused."""
from __future__ import annotations

import copy
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engine.source import arch_v30 as A30  # noqa: E402
from engine.source import arch_v304 as A304  # noqa: E402
from engine.source import arch_v3070 as A  # noqa: E402
from engine.source import boq_line as BL  # noqa: E402

PID, REV = "K693-SYNTHETIC", "e" * 64
H_LO = round(max(8.40 - 0.010, 8.40 - 0.015) + 0.60 - 6.00, 6)       # 2.99
H_HI = round(9.80 - 6.00, 6)                                           # 3.80
C2_OLD = (round(0.08 * 2.70, 6), round(0.08 * 3.80, 6))                # 0.216 .. 0.304
C2_NEW = (round(0.08 * H_LO, 6), C2_OLD[1])                            # 0.2392 .. 0.304
C5 = (round(0.08 * H_LO, 6), round(0.10 * H_HI, 6))                    # 0.2392 .. 0.38
A1 = (round(0.06 * (3.19 - 0.20), 6), round(0.075 * (3.60 - 0.20), 6))  # 0.1794 .. 0.255
LABEL = {"detector": "slab-region detector", "region": "BAND9", "from": "BEAM_STRIP", "to": "GROUND_SLAB"}


def _ln(code, eid, state, net=None, rng=None, unit="m3", rec=None, floor="1F"):
    ln = BL.make_line(project_id=PID, revision_set_sha256=REV, item_code=code, unit=unit, evidence_state=state,
                      measured_net=net, gross=net, element_id=eid, floor=floor, room_id=None, bounded_range=rng,
                      formula=f"synthetic {code} {eid}", rule_id="R-SYN", rule_version="1",
                      geometry_source="SYNTHETIC_FIXTURE", material_state="BY_SPEC",
                      inputs=rec, rfi={"question": "detail", "unlocks": eid}
                      if state in ("BLOCKED_RFI", "BOUNDED_EXPOSURE") else None, notes="synthetic")
    return BL.validate(ln)


def _rng(r):
    return {"low": r[0], "high": r[1], "basis": "older plate datum"}


V65 = {"concrete_ledger_v3065": {"action": "BOUND", "member": "earlier plate low"}}


def base():
    return [
        _ln("STR.CONC.COLUMN", "C2", "BOUNDED_EXPOSURE", rng=_rng(C2_OLD), rec=copy.deepcopy(V65)),
        _ln("STR.CONC.COLUMN", "C5", "BLOCKED_RFI"),
        _ln("STR.CONC.COLUMN", "A1", "BLOCKED_RFI", floor="GF"),
        _ln("STR.CONC.COLUMN", "C9", "BOUNDED_EXPOSURE", rng=_rng(C2_OLD)),
        _ln("STR.CONC.COLUMN", "W", "BLOCKED_RFI"),
        _ln("STR.CONC.COLUMN", "CR", "MEASURED", net=0.36),
        _ln("STR.CONC.GROUND_SLAB", "GS", "MEASURED", net=0.114, floor="GF"),
        _ln("STR.CONC.GROUND_BEAM", "GB", "BLOCKED_RFI", floor="GF"),
        _ln("FIN.PLASTER", "R1:PLASTER", "PROVISIONAL", net=44.31, unit="m2"),
    ]


LN = base()
ID = {ln["location"]["element_id"]: ln["line_id"] for ln in LN}


def _src(t):
    return {"task": t, "file": f"research/k693/{t}.json", "sha256": t[-1] * 64, "merge_commit": "b" * 40,
            "checker_run": f"checker {t} Gate A PASS"}


def _x(eid, rng=None, code="STR.CONC.COLUMN", cls="HELD", value=None):
    x = {"item_code": code, "element_id": eid, "unit": "m3", "class": cls,
         "low": rng[0] if rng else None, "high": rng[1] if rng else None}
    if value is not None:
        x["value"] = value
    return x


JOINT = {"kind": "BEAM_JOINT", "beam": "B1 1F roof", "beam_depth_m": 0.60, "depth_source": "schedule B1 20 x 60",
         "supports": ["C2", "C5"],
         "heads": [{"id": "W1", "head_abs_m": 8.40, "tol_m": 0.010, "status": "DRAWING-CONFIRMED"},
                   {"id": "W2", "head_abs_m": 8.40, "tol_m": 0.015, "status": "DRAWING-CONFIRMED"}]}
PLANE = {"kind": "PLANE", "plane": {"rule": "R-T682-1 1.0.0", "state": "ONE_PLANE", "outline": "annex roof",
                                    "sections_checked": ["A-A"], "steps_outside": [],
                                    "section_steps": [{"section": "A-A", "step_m": "0.20", "inside_plane": False,
                                                       "evidence": "outside"}], "s_lo_m": 3.19}}
CEIL = {"kind": "CEILING", "mark_abs_m": 9.80, "what": "1F roof finished mark"}
ST = {"low_end": "DRAWING-CONFIRMED", "high_end": "HELD", "basis": "low: head under printed B1; high: no slab top"}


def _h(datum=JOINT, base=6.00, ceil=CEIL):
    return {"base_m": base, "base_status": "APPROVED", "datum_lo": copy.deepcopy(datum), "datum_hi": dict(ceil)}


def entries():
    return [
        {"action": "NARROW", "line_id": ID["C2"], "source_tasks": ["T-P"], "member": "C2 1F", "member_mark": "C2",
         "expect": _x("C2", C2_OLD), "readings": [{"source": "schedule = drawn", "b_m": 0.20, "d_m": 0.40}],
         "height": _h(), "after": {"low": C2_NEW[0], "high": C2_NEW[1]}, "ends_moved": ["low"], "items": ["D-39"],
         "question": "slab top not printed", "basis": "B1 joint", "status": dict(ST)},
        {"action": "BOUND", "line_id": ID["C5"], "source_tasks": ["T-P"], "member": "C5 1F", "member_mark": "C5",
         "expect": _x("C5"), "readings": [{"source": "drawn outline", "b_m": 0.50, "d_m": 0.20},
                                          {"source": "schedule C5", "b_m": 0.20, "d_m": 0.40}],
         "height": _h(), "after": {"low": C5[0], "high": C5[1]}, "items": ["D-66", "D-39"],
         "question": "section conflict; slab top", "basis": "conflict bound", "status": dict(ST)},
        {"action": "BOUND", "line_id": ID["A1"], "source_tasks": ["T-P"], "member": "A1 annex", "member_mark": "A1",
         "expect": _x("A1"), "readings": [{"source": "drawn", "b_m": 0.20, "d_m": 0.30},
                                          {"source": "schedule", "b_m": 0.25, "d_m": 0.30}],
         "height": _h(PLANE, 0.20, {"kind": "CEILING", "mark_abs_m": 3.60, "what": "annex finished"}),
         "after": {"low": A1[0], "high": A1[1]}, "items": ["D-66", "Q-54 B"], "question": "annex slab top",
         "basis": "conflict bound on the plane", "status": dict(ST)},
        {"action": "OWNER", "line_id": ID["GS"], "source_tasks": ["T-Q"], "member": "GS face",
         "expect": _x("GS", code="STR.CONC.GROUND_SLAB", cls="RELEASED", value=0.114),
         "label": dict(LABEL),
         "ruling": "R-T688-3 (a): own level mark", "basis": "face is slab"},
    ]


def doc(ents=None, expect=None):
    d = {"schema": A.INPUTS_SCHEMA, "project_id": PID, "sources": [_src("T-P"), _src("T-Q")],
         "entries": entries() if ents is None else ents}
    if expect:
        d["expect_totals"] = expect
    return d


def run(ents=None, prev=None, expect=None):
    prev = LN if prev is None else prev
    d = A.load_inputs(doc(ents, expect), PID)
    ch, log = A.changes_for(d, prev)
    new, ident = A.integrate(prev, ch)
    moved = A.check_totals(A304.code_totals(prev), A304.code_totals(new), ch, expect)
    return new, ident, moved, ch


def _by(lines):
    return {ln["location"]["element_id"]: ln for ln in lines}


# ------------------------------------------------------------------------------------------------ normal
def test_normal_hand_figures():
    assert (H_LO, H_HI) == (2.99, 3.80)
    assert C2_NEW == (0.2392, 0.304) and C5 == (0.2392, 0.38) and A1 == (0.1794, 0.255)
    new, ident, moved, _ = run()
    b = _by(new)
    assert A30._qty(b["C2"])["low"] == C2_NEW[0] and A30._qty(b["C2"])["high"] == C2_NEW[1]
    assert (A30._qty(b["C5"])["low"], A30._qty(b["C5"])["high"]) == C5
    assert (A30._qty(b["A1"])["low"], A30._qty(b["A1"])["high"]) == A1
    assert b["GS"]["measured_net"] == 0.114 and b["GS"]["evidence_state"] == "MEASURED"
    assert b["GS"]["calculation"]["inputs"][A.REC_KEY]["label"]["to"] == "GROUND_SLAB"
    assert ident["replaced"] == 4 and ident["added"] == 0 and ident["outside_rows"] == 5
    assert ident["concrete"] == {"BOUND": 2, "NARROW": 1, "OWNER": 1}
    t = moved["STR.CONC.COLUMN|m3"]["v3_0_70"]
    assert t["released"] == pytest.approx(0.36) and t["bounded_lines"] == 4 and t["blocked_lines"] == 1
    assert t["held_low"] == pytest.approx(0.8738) and t["held_high"] == pytest.approx(1.243)
    assert set(moved) == {"STR.CONC.COLUMN|m3"}                 # the label moved no total


def test_lines_held_with_items_and_superseded_records():
    new, *_ = run()
    b = _by(new)
    for k in ("C2", "C5", "A1"):
        assert A.line_class(b[k]) == "HELD" and b[k]["rfi"]["question"]
        rec = b[k]["calculation"]["inputs"][A.REC_KEY]
        assert rec["status"]["low_end"] == "DRAWING-CONFIRMED" and rec["items"] and rec["release_status"] == \
            "NOT RELEASED"
    c2 = b["C2"]["calculation"]["inputs"]
    assert "concrete_ledger_v3065" not in c2 and "concrete_ledger_v3065" in c2[A.REC_KEY]["superseded"]
    assert b["C5"]["calculation"]["inputs"][A.REC_KEY]["height"]["top_lo_abs_m"] == 8.99
    assert A.line_class(b["W"]) == "HELD" and b["W"]["bounded_range"] is None    # untouched blank, never 0


def test_mirror_order_same_lines():
    a, *_ = run()
    b, *_ = run(list(reversed(entries())))
    assert [A30.line_sha(x) for x in a] == [A30.line_sha(x) for x in b]


def test_outside_lines_byte_identical():
    new, *_ = run()
    for o, n in zip(LN, new):
        if o["location"]["element_id"] in ("C9", "W", "CR", "GB", "R1:PLASTER"):
            assert A30.line_sha(o) == A30.line_sha(n)


def test_expect_totals_asserted():
    exp = {"STR.CONC.COLUMN|m3": {"held_low": 0.8738, "held_high": 1.243, "bounded_lines": 4, "blocked_lines": 1}}
    run(expect=exp)
    with pytest.raises(ValueError, match="not the inputs"):
        run(expect={"STR.CONC.COLUMN|m3": {"held_low": 0.9}})


def test_top_low_and_height_helpers():
    assert A.top_low(JOINT, "C5") == 8.99
    assert A.top_low(PLANE, "A1") == 3.19
    lo, hi, _ = A.height_range(_h(), "C2")
    assert (lo, hi) == (2.99, 3.80)


# ------------------------------------------------------------------------------------------------ adverse
def _one(i, **kw):
    e = entries()
    e[i] = dict(copy.deepcopy(e[i]), **kw)
    return e


def test_adverse_head_only_stays_held():
    """a column whose top datum is a window head only (no printed beam over it) is not bounded: the line stays HELD."""
    head_only = {"kind": "HEAD_ONLY", "heads": JOINT["heads"]}
    e = {"action": "BOUND", "line_id": ID["W"], "source_tasks": ["T-P"], "member": "W 1F", "member_mark": "W",
         "expect": _x("W"), "readings": [{"source": "drawn", "b_m": 0.20, "d_m": 0.40},
                                         {"source": "schedule", "b_m": 0.20, "d_m": 0.50}],
         "height": _h(head_only), "after": {"low": 0.2, "high": 0.4}, "items": ["D-39"], "question": "q",
         "basis": "b", "status": dict(ST)}
    with pytest.raises(A.InputsError, match="bounds no column top"):
        run(entries() + [e])
    new, *_ = run()
    assert A.line_class(_by(new)["W"]) == "HELD" and _by(new)["W"]["evidence_state"] == "BLOCKED_RFI"


def test_adverse_plate_transfer_refused():
    e = copy.deepcopy(entries()[0])
    e.update(line_id=ID["C9"], member="C9 1F", member_mark="C9", expect=_x("C9", C2_OLD))
    with pytest.raises(A.InputsError, match="not a support"):
        run(entries() + [e])


def test_adverse_ledger_not_recompute():
    with pytest.raises(A.InputsError, match="not the recomputed"):
        run(_one(1, after={"low": C5[0], "high": 0.40}))
    with pytest.raises(A.InputsError, match="not the recomputed"):
        run(_one(0, after={"low": 0.2393, "high": C2_NEW[1]}))


def test_adverse_one_reading_chosen():
    """a CONFLICT is never settled by picking one reading for a blank line"""
    with pytest.raises(A.InputsError, match="needs no conflict"):
        run(_one(1, readings=[{"source": "schedule", "b_m": 0.20, "d_m": 0.40}], after={"low": C5[0], "high": 0.304}))


def test_adverse_units_cm_refused():
    with pytest.raises(A.InputsError, match="not a quantity in range|unit slip"):
        run(_one(1, readings=[{"source": "drawn", "b_m": 50, "d_m": 20}, {"source": "schedule", "b_m": 20, "d_m": 40}]))
    with pytest.raises(A.InputsError, match="unit slip"):
        run(_one(1, readings=[{"source": "drawn", "b_m": 0.005, "d_m": 0.002},
                              {"source": "schedule", "b_m": 0.002, "d_m": 0.004}]))


def test_adverse_narrow_never_widens():
    e = _one(0, height=_h(dict(JOINT, heads=[{"id": "W1", "head_abs_m": 7.90, "tol_m": 0.0,
                                               "status": "DRAWING-CONFIRMED"}])),
             after={"low": round(0.08 * 2.50, 6), "high": C2_NEW[1]})
    with pytest.raises(A.InputsError, match="never widens"):
        run(e)
    with pytest.raises(A.InputsError, match="not the ledger"):
        run(_one(0, ends_moved=["low", "high"]))


def test_adverse_missing_datum_and_items():
    with pytest.raises(A.InputsError, match="printed ceiling"):
        run(_one(1, height=dict(_h(), datum_hi={"kind": "STOREY", "mark_abs_m": 9.80, "what": "typical"})))
    with pytest.raises(A.InputsError, match="designer items"):
        run(_one(1, items=[]))
    with pytest.raises(A.InputsError, match="not DRAWING-CONFIRMED"):
        run(_one(1, height=_h(dict(JOINT, heads=[dict(JOINT["heads"][0], status="ASSUMED")]))))
    with pytest.raises(A.InputsError, match="base status"):
        run(_one(1, height=dict(_h(), base_status="TYPICAL")))
    with pytest.raises(A.InputsError, match="ONE_PLANE|stepped"):
        run(_one(2, height=_h({"kind": "PLANE", "plane": dict(PLANE["plane"], state="STEPPED")}, 0.20,
                              {"kind": "CEILING", "mark_abs_m": 3.60, "what": "annex"})))


def test_adverse_status_never_verified():
    with pytest.raises(A.InputsError, match="never VERIFIED"):
        run(_one(1, status={"low_end": "VERIFIED", "high_end": "HELD", "basis": "x"}))


def test_adverse_owner_record_moves_no_quantity():
    with pytest.raises(A.InputsError, match="no quantity terms"):
        run(_one(3, after={"value": 0.2}))
    with pytest.raises(A.InputsError, match="stale binding"):
        run(_one(3, expect=_x("GS", code="STR.CONC.GROUND_SLAB", cls="RELEASED", value=0.120)))
    with pytest.raises(A.InputsError, match="not corrected"):
        run(_one(3, label=dict(LABEL, to="BEAM_STRIP")))
    with pytest.raises(A.InputsError, match="released value"):
        run(_one(3, expect=_x("GS", code="STR.CONC.GROUND_SLAB", cls="RELEASED")))


def test_adverse_owner_on_another_element_refused():
    """the ground-slab ruling never lands on a ground-beam line (one element, one owner)"""
    e = copy.deepcopy(entries()[3])
    e.update(line_id=ID["GB"], expect=_x("GB", code="STR.CONC.GROUND_BEAM"))
    with pytest.raises(A.InputsError, match="ruled owner"):
        run(entries()[:3] + [e])


def test_adverse_tampered_owner_state_fails_check():
    new, *_ = run()
    bad = [copy.deepcopy(x) for x in new]
    gs = next(x for x in bad if x["location"]["element_id"] == "GS")
    gs["measured_net"] = 0.2
    with pytest.raises(ValueError, match="not in its state"):
        A.check_concrete(bad)


def test_adverse_stale_binding_and_twice():
    with pytest.raises(A.InputsError, match="stale binding"):
        run(_one(0, expect=_x("C2", (0.215, 0.304))))
    with pytest.raises(A.InputsError, match="BOUND starts from a blank"):
        run(_one(1, action="NARROW", expect=_x("C5")))
    new, *_ = run()
    with pytest.raises(A.InputsError, match="applied once"):
        run(prev=new)
    with pytest.raises(A.InputsError, match="named twice"):
        run(entries() + [entries()[1]])


def test_adverse_released_or_other_code():
    e = copy.deepcopy(entries()[1])
    e.update(line_id=ID["CR"], expect=_x("CR", cls="RELEASED"))
    with pytest.raises(A.InputsError, match="HELD STR.CONC.COLUMN"):
        run([e])
    e = copy.deepcopy(entries()[1])
    e["expect"] = dict(e["expect"], item_code="FIN.PLASTER", unit="m2")
    with pytest.raises(A.InputsError, match="STR.CONC"):
        run([e])
    with pytest.raises(A.InputsError, match="BOUND, NARROW or OWNER"):
        run(_one(1, action="VALUE"))


def test_adverse_stray_change_refused():
    d = A.load_inputs(doc(), PID)
    ch, _ = A.changes_for(d, LN)
    bad = copy.deepcopy(ch)
    bad[0]["after"] = dict(bad[0]["after"], item_code="FIN.PLASTER", unit="m2")
    with pytest.raises(ValueError, match="not a code"):
        A.integrate(LN, bad)
