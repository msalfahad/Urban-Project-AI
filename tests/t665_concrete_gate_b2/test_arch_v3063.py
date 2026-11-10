"""T-665: ARCH_TAKEOFF_V3.0.63 (CONCRETE_GATE_B_V2, R-T665-1) on the hand-calculated NON-Alsenan villa V665 (own
figures, no drawing). Printed: ground-beam titles by span 30x30 (< 2.5 m), 30x40 (< 5 m), 30x60 (> 5 m), sections only
'without concentrated load'; main roof finished +13.90, structural base +9.65 an approved datum (not printed text).

  G1 ground beam, span 1.20 m, carried as the 30x30 point 0.108: both 30x30 and 30x40 hold (D-34):
      1.20 x 0.30 x 0.30 = 0.108 .. 1.20 x 0.30 x 0.40 = 0.144 m3 (BOUND).
  G2 oblique band, drawn outline 0.65 m2, carried 0.186592 (short edge x 0.30 x 0.30): 0.65 x 0.30 = 0.195 ..
      0.65 x 0.40 = 0.26 m3 (BOUND, R-T658-7).
  G3 run carrying a landing beam, drawn 1.50 m2, carried as the 0.9 point (30x60): the unloaded titles are a floor:
      AT_LEAST 1.50 x 0.40 = 0.60 m3 beside, blank (LOWER_ONLY), the old point set aside (R-T658-8).
  G4 annex exterior beam 2.40 m, blank: literal +0.25 .. N.G.: AT_LEAST 2.40 x 0.30 x 0.25 = 0.18 m3, blank.
  G5 court beam, blank, no printed section: CONFIRM.
  C1 column 0.20 x 0.50 = 0.10 m2, blank: ceiling 0.10 x (13.90 - 9.65) = 0.425 m3 AT_MOST beside, blank
      (UPPER_ONLY), datums PRINTED +13.90 and APPROVED_DATUM +9.65.
  C2 column HELD 0.756 .. 0.840 (section conflict): CONFIRM.  S1 strap HELD 0 .. 0.385 (existence open): CONFIRM.
  F1 footing HELD 2.176 .. 2.275 (one scenario): owner scenario set 2.80 x 1.40 x 0.50 = 1.96 .. 3.25 x 1.40 x 0.50
      = 2.275 m3 (BOUND).   N1 neck (a V3.0.62 restated line) and a plaster line: not named, byte-identical.
Code totals (m3): GROUND_BEAM held 1.194592 .. 1.194592 (3 bounded, 2 blocked) -> 0.303 .. 0.404 (2 bounded,
3 blocked); COLUMN 0.756 .. 0.84 (1 bounded, 1 blocked) unchanged; FOOTING 2.176 .. 2.275 -> 1.96 .. 2.275.
Adverse: an upper-only line without its AT_MOST figure, without / with a bad datum kind, an AT_MOST figure on a
blank or lower-only line, an upper-only line with a figure, an upper-only line retiring a bound with no set-aside,
a mm slip, the V3.0.62 adverse set on the new module (stale, HELD as 0, CONFIRM with an after, applied twice),
reordered villa (same result)."""
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
from engine.source import arch_v3063 as A  # noqa: E402
from engine.source import boq_line as BL  # noqa: E402

PID, REV = "V665-SYNTHETIC", "f" * 64
G1 = (round(1.20 * 0.30 * 0.30, 6), round(1.20 * 0.30 * 0.40, 6))
G2 = (round(0.65 * 0.30, 6), round(0.65 * 0.40, 6))
G3_FLOOR = round(1.50 * 0.40, 6)
G4_FLOOR = round(2.40 * 0.30 * 0.25, 6)
C1_CEIL = round(0.20 * 0.50 * (13.90 - 9.65), 6)
F1 = (round(2.80 * 1.40 * 0.50, 6), round(3.25 * 1.40 * 0.50, 6))


def _ln(code, eid, state, net=None, rng=None, unit="m3"):
    return BL.make_line(project_id=PID, revision_set_sha256=REV, item_code=code, unit=unit, evidence_state=state,
                        measured_net=net, gross=net, element_id=eid, floor="GF", room_id=None, bounded_range=rng,
                        formula=f"synthetic {code} {eid}", rule_id="R-SYN", rule_version="1",
                        geometry_source="SYNTHETIC_FIXTURE", material_state="BY_SPEC",
                        rfi={"question": "detail", "unlocks": eid} if state in ("BLOCKED_RFI", "BOUNDED_EXPOSURE")
                        else None, notes="synthetic")


def lines():
    return [
        _ln("STR.CONC.GROUND_BEAM", "G1", "BOUNDED_EXPOSURE", rng={"low": 0.108, "high": 0.108}),
        _ln("STR.CONC.GROUND_BEAM", "G2", "BOUNDED_EXPOSURE", rng={"low": 0.186592, "high": 0.186592}),
        _ln("STR.CONC.GROUND_BEAM", "G3", "BOUNDED_EXPOSURE", rng={"low": 0.9, "high": 0.9}),
        _ln("STR.CONC.GROUND_BEAM", "G4", "BLOCKED_RFI"),
        _ln("STR.CONC.GROUND_BEAM", "G5", "BLOCKED_RFI"),
        _ln("STR.CONC.COLUMN", "C1", "BLOCKED_RFI"),
        _ln("STR.CONC.COLUMN", "C2", "BOUNDED_EXPOSURE", rng={"low": 0.756, "high": 0.84}),
        _ln("STR.CONC.STRAP", "S1", "BOUNDED_EXPOSURE", rng={"low": 0.0, "high": 0.385}),
        _ln("STR.CONC.FOOTING", "F1", "BOUNDED_EXPOSURE", rng={"low": 2.176, "high": 2.275}),
        _ln("STR.CONC.NECK", "N1", "BOUNDED_EXPOSURE", rng={"low": 0.252, "high": 0.285}),
        _ln("FIN.PLASTER", "R1:PLASTER", "PROVISIONAL", net=44.31, unit="m2"),
    ]


LN = lines()
ID = {ln["location"]["element_id"]: ln["line_id"] for ln in LN}
DATUMS = [{"kind": "PRINTED", "what": "+13.90 finished mark"},
          {"kind": "APPROVED_DATUM", "what": "+9.65 structural base (not printed text)"}]


def _src(t):
    return {"task": t, "file": f"research/v665/{t}.json", "sha256": t[-1] * 64, "merge_commit": "c" * 40,
            "checker_run": f"checker {t} Gate A PASS"}


def _x(eid, code, rng):
    return {"item_code": code, "element_id": eid, "unit": "m3", "class": "HELD",
            "low": rng[0] if rng else None, "high": rng[1] if rng else None}


def entries():
    gb = "STR.CONC.GROUND_BEAM"
    return [
        {"action": "BOUND", "line_id": ID["G1"], "source_tasks": ["T-G"], "member": "ground beam G1",
         "expect": _x("G1", gb, (0.108, 0.108)), "after": {"low": G1[0], "high": G1[1]},
         "basis": "1.20 x 0.30 x 0.30 .. 0.40 (two titles hold)", "why_held": "titles", "question": "D-34"},
        {"action": "BOUND", "line_id": ID["G2"], "source_tasks": ["T-G"], "member": "oblique band G2",
         "expect": _x("G2", gb, (0.186592, 0.186592)), "after": {"low": G2[0], "high": G2[1]},
         "basis": "outline 0.65 m2 x 0.30 .. 0.40", "why_held": "titles", "question": "D-34"},
        {"action": "LOWER_ONLY", "line_id": ID["G3"], "source_tasks": ["T-G"], "member": "loaded run G3",
         "expect": _x("G3", gb, (0.9, 0.9)), "after": {}, "basis": "1.50 m2 x 0.40 floor",
         "why_held": "landing beam lands: no loaded section printed", "question": "D-33",
         "beside": {"kind": "AT_LEAST_M3", "value": G3_FLOOR, "basis": "1.50 x 0.40"},
         "set_aside": {"low": 0.9, "high": 0.9, "why": "unloaded titles are a floor, never a high"}},
        {"action": "LOWER_ONLY", "line_id": ID["G4"], "source_tasks": ["T-G"], "member": "annex beam G4",
         "expect": _x("G4", gb, None), "after": {}, "basis": "2.40 x 0.30 x 0.25 literal floor",
         "why_held": "annex depth", "question": "D-35",
         "beside": {"kind": "AT_LEAST_M3", "value": G4_FLOOR, "basis": "2.40 x 0.30 x 0.25"}},
        {"action": "CONFIRM", "line_id": ID["G5"], "source_tasks": ["T-G"], "member": "court beam G5",
         "expect": _x("G5", gb, None), "basis": "no printed section"},
        {"action": "UPPER_ONLY", "line_id": ID["C1"], "source_tasks": ["T-G"], "member": "column C1",
         "expect": _x("C1", "STR.CONC.COLUMN", None), "after": {}, "basis": "0.10 x (13.90 - 9.65) ceiling",
         "why_held": "slab-top datum not printed", "question": "D-39",
         "beside": {"kind": "AT_MOST_M3", "value": C1_CEIL, "basis": "0.10 x 4.25", "datums": DATUMS}},
        {"action": "CONFIRM", "line_id": ID["C2"], "source_tasks": ["T-G"], "member": "column C2",
         "expect": _x("C2", "STR.CONC.COLUMN", (0.756, 0.84)), "basis": "section conflict"},
        {"action": "CONFIRM", "line_id": ID["S1"], "source_tasks": ["T-G"], "member": "strap S1",
         "expect": _x("S1", "STR.CONC.STRAP", (0.0, 0.385)), "basis": "existence open"},
        {"action": "BOUND", "line_id": ID["F1"], "source_tasks": ["T-F", "T-G"], "member": "footing F1",
         "expect": _x("F1", "STR.CONC.FOOTING", (2.176, 2.275)), "after": {"low": F1[0], "high": F1[1]},
         "basis": "scenario set 2.80 .. 3.25 x 1.40 x 0.50", "why_held": "governing scenario",
         "question": "which scenario"},
    ]


def doc(ents=None):
    return {"schema": A.INPUTS_SCHEMA, "project_id": PID, "sources": [_src("T-G"), _src("T-F")],
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
    assert G1 == (0.108, 0.144) and G2 == (0.195, 0.26) and G3_FLOOR == 0.6 and G4_FLOOR == 0.18
    assert C1_CEIL == 0.425 and F1 == (1.96, 2.275)


def test_states_and_records():
    prev, ch, log = run()
    assert log["by_action"] == {"BOUND": 3, "LOWER_ONLY": 2, "UPPER_ONLY": 1, "CONFIRM": 3}
    assert log["lines"] == 6 and set(log["confirmed"]) == {ID["G5"], ID["C2"], ID["S1"]}
    new, ident = A.integrate(prev, ch)
    g1, g3, g4, c1, f1 = (_by(new, e) for e in ("G1", "G3", "G4", "C1", "F1"))
    assert (g1["bounded_range"]["low"], g1["bounded_range"]["high"]) == G1
    assert g3["evidence_state"] == "BLOCKED_RFI" and g3["bounded_range"] is None and g3["measured_net"] is None
    r3 = g3["calculation"]["inputs"][A.REC_KEY]
    assert r3["beside"]["value"] == 0.6 and r3["set_aside"]["low"] == 0.9 and r3["was"]["bounded_range"]
    assert g4["calculation"]["inputs"][A.REC_KEY]["set_aside"] is None
    assert c1["evidence_state"] == "BLOCKED_RFI" and c1["measured_net"] is None and c1["bounded_range"] is None
    rc = c1["calculation"]["inputs"][A.REC_KEY]
    assert rc["action"] == "UPPER_ONLY" and rc["beside"]["kind"] == "AT_MOST_M3" and rc["beside"]["value"] == 0.425
    assert [d["kind"] for d in rc["beside"]["datums"]] == ["PRINTED", "APPROVED_DATUM"]
    assert "UPPER END ONLY" in c1["calculation"]["formula"] and "m3 at most" in c1["calculation"]["formula"]
    assert (f1["bounded_range"]["low"], f1["bounded_range"]["high"]) == F1
    assert ident["concrete"] == {"BOUND": 3, "VALUE": 0, "HELD_BLANK": 0, "LOWER_ONLY": 2, "UPPER_ONLY": 1}
    assert ident["replaced"] == 6 and ident["outside_rows"] == 5
    for e in ("G5", "C2", "S1", "N1", "R1:PLASTER"):
        assert A30.line_sha(_by(new, e)) == A30.line_sha(_by(prev, e)), e


def test_code_totals_hand(tmp_path):
    prev, ch, log = run()
    new, _ = A.integrate(prev, ch)
    t0, t1 = A304.code_totals(prev), A304.code_totals(new)
    g0, g1 = t0["STR.CONC.GROUND_BEAM|m3"], t1["STR.CONC.GROUND_BEAM|m3"]
    assert (round(g0["held_low"], 6), g0["bounded_lines"], g0["blocked_lines"]) == (1.194592, 3, 2)
    assert (round(g1["held_low"], 6), round(g1["held_high"], 6), g1["bounded_lines"], g1["blocked_lines"]) == \
        (0.303, 0.404, 2, 3)
    assert t0["STR.CONC.COLUMN|m3"] == t1["STR.CONC.COLUMN|m3"]          # a ceiling is beside, never a total
    f = t1["STR.CONC.FOOTING|m3"]
    assert (f["held_low"], f["held_high"]) == F1
    for k in ("STR.CONC.STRAP|m3", "STR.CONC.NECK|m3", "FIN.PLASTER|m2"):
        assert t0[k] == t1[k], k
    moved = A.check_totals(t0, t1, ch, {"STR.CONC.FOOTING|m3": {"held_low": 1.96}})
    assert set(moved) == {"STR.CONC.GROUND_BEAM|m3", "STR.CONC.FOOTING|m3", "STR.CONC.COLUMN|m3"}
    names, ident, led = A.write(tmp_path, prev, ch, log)
    assert "V3_0_63_BOQ_LINES.json" in names and led["integration_package"] is True
    r = json.loads((tmp_path / "V3_0_63_RUN.json").read_text(encoding="utf-8"))
    assert r["identity"]["diff"]["vs_base"] == {"SAME": 5, "CHANGED": 4, "CHANGED_TEXT_ONLY": 2}   # G4 and C1: blank -> blank, figure beside
    assert r["identity"]["confirmed"] == 3 and r["released_default"] is False
    assert "T661_T658_COLUMNS_GROUND_BEAMS" not in r["waiting_pieces"] and "T661_BOUNDARY_BAND" in r["waiting_pieces"]
    rows = {x["member"]: x for x in led["rows"]}
    assert rows["column C1"]["beside"]["kind"] == "AT_MOST_M3" and rows["column C1"]["class"] == ["HELD", "HELD"]
    assert "m3 at most" in (tmp_path / "V3_0_63_INTEGRATION_LEDGER.csv").read_text(encoding="utf-8")


def test_reordered_villa_same_result():
    prev, ch, _ = run()
    new = A.integrate(prev, ch)[0]
    p2, ch2, _ = run(doc(list(reversed(entries()))), list(reversed(copy.deepcopy(LN))))
    new2 = A.integrate(p2, ch2)[0]
    assert sorted(A30.line_sha(x) for x in new) == sorted(A30.line_sha(x) for x in new2)


# ------------------------------------------------------------------------------------------------ adverse
B = {"kind": "AT_MOST_M3", "value": 0.425, "basis": "x"}


@pytest.mark.parametrize("i,kw,msg", [
    (5, {"beside": None}, "beside"),
    (5, {"beside": {"kind": "AT_LEAST_M3", "value": 0.425, "basis": "x"}}, "AT_MOST"),
    (5, {"beside": dict(B)}, "datum"),
    (5, {"beside": dict(B, datums=[{"kind": "ASSUMED", "what": "x"}])}, "datum"),
    (5, {"beside": dict(B, datums=[{"kind": "PRINTED"}])}, "datum"),
    (5, {"beside": dict(B, value=425.0, datums=DATUMS)}, "unit slip"),
    (5, {"beside": dict(B, value=0, datums=DATUMS)}, "HELD-as-0"),
    (5, {"after": {"high": 0.425}}, "no quantity"),
    (3, {"beside": dict(B, datums=DATUMS)}, "AT_LEAST"),
    (0, {"after": {"low": 0.0, "high": 0.144}}, "HELD-as-0"),
    (0, {"after": {"low": 0.144, "high": 0.108}}, "low"),
    (0, {"expect": _x("G1", "STR.CONC.GROUND_BEAM", (0.108, 0.144))}, "stale"),
    (6, {"after": {"low": 0.75, "high": 0.84}}, "CONFIRM"),
    (8, {"source_tasks": ["T-X"]}, "no merged source"),
])
def test_adverse_inputs(i, kw, msg):
    with pytest.raises(A.InputsError, match=msg):
        run(_mut(i, **kw))


def test_adverse_blank_line_with_at_most_and_upper_only_retiring_a_bound():
    es = entries()
    es.append({"action": "HELD_BLANK", "line_id": ID["N1"], "source_tasks": ["T-G"], "member": "neck N1",
               "expect": _x("N1", "STR.CONC.NECK", (0.252, 0.285)), "after": {}, "basis": "x", "why_held": "x",
               "question": "x", "beside": dict(B, datums=DATUMS),
               "set_aside": {"low": 0.252, "high": 0.285, "why": "x"}})
    with pytest.raises(A.InputsError, match="upper-only line"):
        run(doc(es))
    es = entries()
    es[6] = {"action": "UPPER_ONLY", "line_id": ID["C2"], "source_tasks": ["T-G"], "member": "column C2",
             "expect": _x("C2", "STR.CONC.COLUMN", (0.756, 0.84)), "after": {}, "basis": "x", "why_held": "x",
             "question": "x", "beside": dict(B, value=0.84, datums=DATUMS)}
    with pytest.raises(A.InputsError, match="set_aside"):
        run(doc(es))


def test_adverse_applied_twice_and_tampered_state():
    prev, ch, _ = run()
    new = A.integrate(prev, ch)[0]
    with pytest.raises(A.InputsError, match="applied once"):
        run(prev=new)
    t = copy.deepcopy(new)
    c1 = _by(t, "C1")
    c1["evidence_state"], c1["bounded_range"] = "BOUNDED_EXPOSURE", {"low": 0.0, "high": 0.425}
    with pytest.raises(ValueError, match="not in its state"):
        A.check_concrete(t)
    t = copy.deepcopy(new)
    c1 = _by(t, "C1")
    c1["evidence_state"], c1["measured_net"], c1["gross"] = "MEASURED", 0.425, 0.425
    with pytest.raises(ValueError, match="not in its state"):
        A.check_concrete(t)
