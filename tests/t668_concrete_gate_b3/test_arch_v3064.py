"""T-668: ARCH_TAKEOFF_V3.0.64 (CONCRETE_GATE_B_V3, R-T668-1) on the hand-calculated NON-Alsenan villa V668 (own
figures, no drawing). Printed: beam pieces breadth 0.20, schedule depths 0.40 .. 1.20; boundary band typical 0.20 x
0.40, B.W 0.20 x 0.60; pool blinding '10cm plain concrete' under a pool base 3.00 x 3.60 with a 0.10 wrap.

  P1 unlabelled piece carried 1.30 m face to face (0.104 .. 0.312); drawn to its outer end 1.50 m: 1.50 x 0.20 x 0.40 =
     0.12 .. 1.50 x 0.20 x 1.20 = 0.36 m3 (BOUND); squares: outer end -> P1 (PIECE), crossing band -> column K1 (owns
     its outline to the slab top); beside: 0 .. 0.20 x 0.20 x (0.75 - 0.40) = 0.014 m3 (gap under P1, never in range).
  K1 column HELD blank (datum open): CONFIRM (owner of the crossing square).
  W1 boundary band RELEASED 4.80 (one side lost), held at export by ONE applied Checker downgrade (engine_qty 4.80):
     drawn 50.0 m free x 0.20 x 0.40 = 4.00 .. 60.0 m closed x 0.20 x 0.60 = 7.20 m3 (BOUND, downgrade materialised).
  PIT footing blinding RELEASED 3.00. Pool blinding NEW: grown base 3.20 x 3.80 = 12.16 m2, shared with the pit layer
     2.16 m2 (a pool over a footing: one layer) -> 10.00 m2 x 0.10 = 1.00 m3 AT_LEAST beside, blank (ADD_LOWER_ONLY).
  ST pool steps HELD blank: CONFIRM.  A plaster line: not named, byte-identical.
Code totals (m3): BEAM held 0.104 .. 0.312 -> 0.12 .. 0.36; BOUNDARY_WALL released 4.80 -> 0, held 0 -> 4.00 .. 7.20;
BLINDING lines 1 -> 2 (released 3.00 unchanged, blocked 0 -> 1); COLUMN / POOL unchanged.
Adverse: one square claimed by two lines, a PIECE square owned by another line, an owner line not in the candidate,
an exposure with a floor, an added element already carried, an added line netting a stale line, an added line with a
value / without its AT_LEAST, a released band without its downgrade, an added line released (tampered), applied twice."""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engine.source import arch_v30 as A30  # noqa: E402
from engine.source import arch_v304 as A304  # noqa: E402
from engine.source import arch_v3064 as A  # noqa: E402
from engine.source import boq_line as BL  # noqa: E402

PID, REV = "V668-SYNTHETIC", "e" * 64
P1 = (round(1.50 * 0.20 * 0.40, 6), round(1.50 * 0.20 * 1.20, 6))
P1_GAP = round(0.20 * 0.20 * (0.75 - 0.40), 6)
W1 = (round(50.0 * 0.20 * 0.40, 6), round(60.0 * 0.20 * 0.60, 6))
POOL_PLAN = round(3.20 * 3.80, 6)
POOL_FLOOR = round((POOL_PLAN - 2.16) * 0.10, 6)


def _ln(code, eid, state, net=None, rng=None, unit="m3"):
    return BL.make_line(project_id=PID, revision_set_sha256=REV, item_code=code, unit=unit, evidence_state=state,
                        measured_net=net, gross=net, element_id=eid, floor="GF", room_id=None, bounded_range=rng,
                        formula=f"synthetic {code} {eid}", rule_id="R-SYN", rule_version="1",
                        geometry_source="SYNTHETIC_FIXTURE", material_state="BY_SPEC",
                        rfi={"question": "detail", "unlocks": eid} if state in ("BLOCKED_RFI", "BOUNDED_EXPOSURE")
                        else None, notes="synthetic")


def lines():
    w1 = _ln("STR.CONC.BOUNDARY_WALL", "W1", "PROVISIONAL", net=4.8)
    w1["bounded_range"] = {"low": 4.8, "high": 4.8, "basis": "one reading"}
    return [
        _ln("STR.CONC.BEAM", "P1", "BOUNDED_EXPOSURE", rng={"low": 0.104, "high": 0.312}),
        _ln("STR.CONC.COLUMN", "K1", "BLOCKED_RFI"),
        BL.validate(w1),
        _ln("STR.CONC.BLINDING", "PIT", "MEASURED", net=3.0),
        _ln("STR.CONC.POOL", "ST", "BLOCKED_RFI"),
        _ln("FIN.PLASTER", "R1:PLASTER", "PROVISIONAL", net=44.31, unit="m2"),
    ]


LN = lines()
ID = {ln["location"]["element_id"]: ln["line_id"] for ln in LN}
DG = {"downgrade_id": "DG-V668", "verdict_commit": "abcd1234", "checker_run": "Verifier synthetic",
      "file": "research/v668/DG.json", "sha256": "d" * 64, "line_ids": [ID["W1"]],
      "line_content_sha256": A.A3063._content_sha([LN[2]]), "engine_qty": 4.8}


def _src(t):
    return {"task": t, "file": f"research/v668/{t}.json", "sha256": t[-1] * 64, "merge_commit": "c" * 40,
            "checker_run": f"checker {t} Gate A PASS"}


def _x(eid, code, rng, cls="HELD"):
    return {"item_code": code, "element_id": eid, "unit": "m3", "class": cls,
            "low": rng[0] if rng else None, "high": rng[1] if rng else None}


def entries():
    return [
        {"action": "BOUND", "line_id": ID["P1"], "source_tasks": ["T-J"], "member": "beam P1 (unlabelled piece)",
         "expect": _x("P1", "STR.CONC.BEAM", (0.104, 0.312)), "after": {"low": P1[0], "high": P1[1]},
         "basis": "drawn 1.50 x 0.20 x 0.40 .. 1.20", "why_held": "no mark", "question": "Q-61 C(4)",
         "squares": [{"square": "outer end", "owner": ID["P1"], "owner_kind": "PIECE", "owner_line": ID["P1"],
                      "junction": "P1 outer end"},
                     {"square": "crossing band", "owner": "K1", "owner_kind": "COLUMN", "owner_line": ID["K1"],
                      "junction": "column K1 outline"}],
         "exposures_beside": [{"what": "gap under P1 at the corner", "low": 0.0, "high": P1_GAP, "why": "D-04"}]},
        {"action": "CONFIRM", "line_id": ID["K1"], "source_tasks": ["T-J"], "member": "column K1",
         "expect": _x("K1", "STR.CONC.COLUMN", None), "basis": "owns the crossing square"},
        {"action": "BOUND", "line_id": ID["W1"], "source_tasks": ["T-B", "T-J"], "member": "boundary band W1",
         "expect": _x("W1", "STR.CONC.BOUNDARY_WALL", (4.8, 4.8), "RELEASED"), "after": {"low": W1[0], "high": W1[1]},
         "basis": "50.0 free x 0.20 x 0.40 .. 60.0 closed x 0.20 x 0.60", "why_held": "section", "question": "Q-28",
         "downgrade": dict(DG)},
        {"action": "ADD_LOWER_ONLY", "key": "POOL-BLINDING", "source_tasks": ["T-P"], "template_line": ID["PIT"],
         "add": {"item_code": "STR.CONC.BLINDING", "unit": "m3", "element_id": "POOL:BLINDING", "floor": None,
                 "physical_element": "pool blinding 0.10"},
         "basis": "3.20 x 3.80 grown - 2.16 shared x 0.10", "why_held": "projection not dimensioned",
         "question": "C4 / C6", "beside": {"kind": "AT_LEAST_M3", "value": POOL_FLOOR, "basis": "10.00 m2 x 0.10"},
         "beside_also": [{"what": "own layer if two layers", "m3": "1.216", "status": "beside"}],
         "netted_against": [{"line_id": ID["PIT"], "item_code": "STR.CONC.BLINDING", "class": "RELEASED",
                             "value": 3.0, "overlap_m2": 2.16, "why": "one layer"}]},
        {"action": "CONFIRM", "line_id": ID["ST"], "source_tasks": ["T-P"], "member": "pool steps",
         "expect": _x("ST", "STR.CONC.POOL", None), "basis": "no step drawn"},
    ]


def doc(ents=None):
    return {"schema": A.INPUTS_SCHEMA, "project_id": PID, "sources": [_src("T-J"), _src("T-B"), _src("T-P")],
            "entries": entries() if ents is None else ents}


def run(d=None, prev=None):
    prev = prev if prev is not None else copy.deepcopy(LN)
    ch, log = A.changes_for(A.load_inputs(d or doc(), PID), prev)
    return prev, ch, log


def _by(out, eid):
    return next(x for x in out if x["location"]["element_id"] == eid)


def _mut(i, **kw):
    es = entries()
    for k, v in kw.items():
        if v is None:
            es[i].pop(k, None)
        else:
            es[i][k] = v
    return doc(es)


# ------------------------------------------------------------------------------------------------ normal
def test_hand_figures():
    assert P1 == (0.12, 0.36) and P1_GAP == 0.014 and W1 == (4.0, 7.2)
    assert POOL_PLAN == 12.16 and POOL_FLOOR == 1.0


def test_states_and_records():
    prev, ch, log = run()
    assert log["by_action"] == {"BOUND": 2, "CONFIRM": 2, "ADD_LOWER_ONLY": 1}
    assert log["lines"] == 3 and log["added"] == 1 and set(log["confirmed"]) == {ID["K1"], ID["ST"]}
    assert log["downgrades_materialised"] == {"DG-V668": {"lines": 1, "engine_qty": 4.8}}
    new, ident = A.integrate(prev, ch)
    p1, w1, pool = _by(new, "P1"), _by(new, "W1"), _by(new, "POOL:BLINDING")
    assert (p1["bounded_range"]["low"], p1["bounded_range"]["high"]) == P1
    r1 = p1["calculation"]["inputs"][A.REC_KEY]
    assert [s["owner_kind"] for s in r1["squares"]] == ["PIECE", "COLUMN"]
    assert r1["exposures_beside"][0]["high"] == 0.014 and "beside, not in the range" in p1["calculation"]["formula"]
    assert w1["evidence_state"] == "BOUNDED_EXPOSURE" and w1["measured_net"] is None
    assert (w1["bounded_range"]["low"], w1["bounded_range"]["high"]) == W1
    assert w1["calculation"]["inputs"][A.REC_KEY]["downgrade"]["downgrade_id"] == "DG-V668"
    assert pool["evidence_state"] == "BLOCKED_RFI" and pool["measured_net"] is None and pool["bounded_range"] is None
    assert pool["gross"] is None and pool["line_id"] not in {x["line_id"] for x in prev}
    rp = pool["calculation"]["inputs"][A.REC_KEY]
    assert rp["action"] == "ADD_LOWER_ONLY" and rp["beside"]["value"] == 1.0 and rp["was"] is None
    assert rp["netted_against"][0]["overlap_m2"] == 2.16
    assert "LOWER END ONLY" in pool["calculation"]["formula"] and "1 m3 at least" in pool["calculation"]["formula"]
    assert pool["item_en"] == _by(prev, "PIT")["item_en"]
    assert ident["concrete"]["BOUND"] == 2 and ident["concrete"]["ADD_LOWER_ONLY"] == 1
    assert ident["replaced"] == 2 and ident["added"] == 1 and ident["outside_rows"] == 4
    assert ident["v3_0_64_lines"] == len(prev) + 1
    for e in ("K1", "PIT", "ST", "R1:PLASTER"):
        assert A30.line_sha(_by(new, e)) == A30.line_sha(_by(prev, e)), e


def test_code_totals_hand(tmp_path):
    prev, ch, log = run()
    new, _ = A.integrate(prev, ch)
    t0, t1 = A304.code_totals(prev), A304.code_totals(new)
    b0, b1 = t0["STR.CONC.BEAM|m3"], t1["STR.CONC.BEAM|m3"]
    assert (b0["held_low"], b0["held_high"]) == (0.104, 0.312) and (b1["held_low"], b1["held_high"]) == P1
    w0, w1 = t0["STR.CONC.BOUNDARY_WALL|m3"], t1["STR.CONC.BOUNDARY_WALL|m3"]
    assert (w0["released"], w0["bounded_lines"]) == (4.8, 0)
    assert (w1["released"], w1["held_low"], w1["held_high"], w1["bounded_lines"]) == (0.0, 4.0, 7.2, 1)
    l0, l1 = t0["STR.CONC.BLINDING|m3"], t1["STR.CONC.BLINDING|m3"]
    assert (l0["lines"], l0["released"], l0["blocked_lines"]) == (1, 3.0, 0)
    assert (l1["lines"], l1["released"], l1["blocked_lines"], l1["held_low"]) == (2, 3.0, 1, 0.0)  # never a figure
    for k in ("STR.CONC.COLUMN|m3", "STR.CONC.POOL|m3", "FIN.PLASTER|m2"):
        assert t0[k] == t1[k], k
    moved = A.check_totals(t0, t1, ch, {"STR.CONC.BOUNDARY_WALL|m3": {"held_low": 4.0, "released": 0.0}})
    assert set(moved) == {"STR.CONC.BEAM|m3", "STR.CONC.BOUNDARY_WALL|m3", "STR.CONC.BLINDING|m3"}
    names, ident, led = A.write(tmp_path, prev, ch, log)
    assert "V3_0_64_BOQ_LINES.json" in names and led["integration_package"] is True
    r = json.loads((tmp_path / "V3_0_64_RUN.json").read_text(encoding="utf-8"))
    assert r["identity"]["diff"]["vs_base"] == {"SAME": 4, "CHANGED": 2, "ADDED": 1}
    assert r["identity"]["confirmed"] == 2 and r["released_default"] is False
    assert "T665_POOL_BLINDING_WIRING" not in r["waiting_pieces"] and "T668_POOL_STEPS" in r["waiting_pieces"]
    rows = {x["member"]: x for x in led["rows"]}
    assert rows["pool blinding 0.10"]["class"] == ["NEW", "HELD"]
    assert rows["boundary band W1"]["class"] == ["RELEASED", "HELD"]
    csv = (tmp_path / "V3_0_64_INTEGRATION_LEDGER.csv").read_text(encoding="utf-8")
    assert "m3 at least" in csv and "gap under P1" in csv


def test_reordered_villa_same_result():
    prev, ch, _ = run()
    new = A.integrate(prev, ch)[0]
    p2, ch2, _ = run(doc(list(reversed(entries()))), list(reversed(copy.deepcopy(LN))))
    new2 = A.integrate(p2, ch2)[0]
    assert sorted(A30.line_sha(x) for x in new) == sorted(A30.line_sha(x) for x in new2)


# ------------------------------------------------------------------------------------------------ adverse
SQ = entries()[0]["squares"]


@pytest.mark.parametrize("i,kw,msg", [
    (0, {"squares": SQ + [dict(SQ[0])]}, "named twice"),
    (0, {"squares": [dict(SQ[0], owner=ID["K1"], owner_line=ID["K1"])]}, "owned by this line"),
    (0, {"squares": [dict(SQ[1], owner_kind="NOBODY")]}, "owner kind"),
    (0, {"exposures_beside": [{"what": "gap", "low": 0.01, "high": 0.014, "why": "x"}]}, "runs from 0"),
    (0, {"exposures_beside": [{"what": "gap", "low": 0.0, "high": 14.0, "why": "x"}]}, "unit slip"),
    (0, {"exposures_beside": [{"what": "gap", "low": 0.0, "high": 0.014}]}, "what and why"),
    (2, {"downgrade": None}, "downgrade"),
    (2, {"action": "VALUE", "after": {"value": 4.8}, "remeasure": "x"}, "only to HELD"),
    (3, {"beside": None}, "beside"),
    (3, {"beside": {"kind": "AT_MOST_M3", "value": 1.0, "basis": "x"}}, "AT_LEAST"),
    (3, {"after": {"value": 1.0}}, "no quantity"),
    (3, {"netted_against": []}, "plan it shares"),
    (3, {"add": {"item_code": "FIN.PLASTER", "unit": "m2", "element_id": "X", "physical_element": "x"}}, "STR.CONC"),
    (3, {"source_tasks": ["T-X"]}, "no merged source"),
])
def test_adverse_inputs(i, kw, msg):
    with pytest.raises(A.InputsError, match=msg):
        run(_mut(i, **kw))


def test_adverse_square_claimed_by_two_lines():
    """a pool on a footing is one layer (netted); a square two pieces both claim is refused"""
    es = entries()
    es[1] = {"action": "BOUND", "line_id": ID["K1"], "source_tasks": ["T-J"], "member": "column K1 as a piece",
             "expect": _x("K1", "STR.CONC.COLUMN", None), "after": {"low": 0.1, "high": 0.2}, "basis": "x",
             "why_held": "x", "question": "x",
             "squares": [{"square": "crossing band", "owner": ID["K1"], "owner_kind": "PIECE", "owner_line": ID["K1"],
                          "junction": "column K1 outline"}]}
    es[0]["squares"] = [dict(SQ[1], owner_kind="PIECE", owner=ID["P1"], owner_line=ID["P1"])]
    with pytest.raises(A.InputsError, match="claimed by two owners"):
        run(doc(es))


def test_adverse_owner_not_in_candidate_and_added_already_carried():
    es = entries()
    es[0]["squares"] = [dict(SQ[1], owner_line="L-" + "0" * 20)]
    with pytest.raises(A.InputsError, match="not a candidate concrete line"):
        run(doc(es))
    es = entries()
    es[3]["add"] = dict(es[3]["add"], element_id="PIT")
    with pytest.raises(A.InputsError, match="already carried"):
        run(doc(es))


def test_adverse_netting_a_stale_line():
    es = entries()
    es[3]["netted_against"] = [dict(es[3]["netted_against"][0], value=2.5)]
    with pytest.raises(A.InputsError, match="stale"):
        run(doc(es))
    es = entries()
    es[3]["netted_against"] = [dict(es[3]["netted_against"][0], **{"class": "HELD"})]
    with pytest.raises(A.InputsError, match="netted line"):
        run(doc(es))


def test_adverse_applied_twice_and_tampered_added_line():
    prev, ch, _ = run()
    new = A.integrate(prev, ch)[0]
    with pytest.raises(A.InputsError, match="applied once"):
        run(prev=new)
    t = copy.deepcopy(new)
    p = _by(t, "POOL:BLINDING")
    p["evidence_state"], p["measured_net"], p["gross"] = "MEASURED", 1.0, 1.0
    with pytest.raises(ValueError, match="not in its state"):
        A.check_concrete(t)
    t = copy.deepcopy(new)
    p = _by(t, "POOL:BLINDING")
    p["evidence_state"], p["bounded_range"] = "BOUNDED_EXPOSURE", {"low": 0.0, "high": 1.0}
    with pytest.raises(ValueError, match="not in its state"):
        A.check_concrete(t)
    with pytest.raises(ValueError, match="already a candidate line"):
        A.check_concrete(new, new)
