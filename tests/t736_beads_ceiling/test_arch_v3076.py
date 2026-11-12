"""T-736: ARCH_TAKEOFF_V3.0.76 (BEADS_GATE_B_V1 + CEILING_GATE_B_V3 + CHECKER_DOWNGRADE_MATERIALISE_V1, R-T736-1) on
the hand-calculated NON-Alsenan villa W736 (own figures, no drawing; every figure below by hand):
  H1  room plaster HELD 40.000 .. 44.000 m2; its convex arrises: corner C1 2.900 m, door D1 jambs + head 2 x 2.100 +
      0.900 = 5.100 m, corner C2 2.900 .. 3.100 m (own held bound) + the two-trade corner X1 3.000 m (H3) -> bead BOUND 13.900 .. 14.100 m.l.
  H2  hall plaster HELD 30.000 .. 30.000 m2 (a point); arrises: corner C3 3.000 m, arch A1 blank (springing not
      printed) -> bead HELD blank, AT_LEAST 3.000 m.l beside (upper end open), never a closed range.
  H3  two-trade corner: the arris X1 3.000 m between plaster H1 and a tiled face is counted once (under H1 only); the
      same arris named again under H2 is refused.
  K1  ceiling-over-void line HELD blank, its face inside the released room ceiling K0 25.000 m2 -> EXCLUDED
      DUPLICATE_FACE of K0 (never valued, never 0).
  W1  roof membrane RELEASED 100.010 m2 under a Checker record whose band is 99.900 .. 100.000 m2 -> HELD 99.900 ..
      100.000 m2 (downgrade only).
  R*  released plaster 50.000 m2 and released column 2.000 m3: byte-identical.
Totals by hand: FIN.PLASTER.BEAD lm new: lines 2, bounded 1 (13.900 .. 14.100), blocked 1; FIN.CEILING lines -1,
blocked -1, released unchanged 25.000; FIN.WP.ROOF released -100.010, held +99.900 .. +100.000, bounded +1; nothing else.
Adverse: a held host released / stale range / not plaster, a blank arris on a BOUND line, a figure on a blank arris, an
arris twice / under two hosts, no measured arris, a record band that is not the entry's, a record on another line, a
record whose content binding is stale, an owner that is held / of another code, VERIFIED status, applied twice, mirror
order of entries gives the same lines."""
from __future__ import annotations

import copy
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engine.source import arch_v304 as A304  # noqa: E402
from engine.source import arch_v3063 as A3063  # noqa: E402
from engine.source import arch_v3076 as A  # noqa: E402
from engine.source import boq_line as BL  # noqa: E402

PID, REV = "W736-SYNTHETIC", "f" * 64


def _ln(code, eid, state, net=None, unit="m2", rng=None, floor="GF"):
    ln = BL.make_line(project_id=PID, revision_set_sha256=REV, item_code=code, unit=unit, evidence_state=state,
                      measured_net=net, gross=net, element_id=eid, floor=floor, room_id=None,
                      bounded_range=None if rng is None else {"low": rng[0], "high": rng[1], "basis": "synthetic"},
                      formula=f"synthetic {code} {eid}", inputs={}, rule_id="R-SYN", rule_version="1",
                      geometry_source="SYNTHETIC_FIXTURE", material_state="BY_SPEC",
                      rfi={"question": f"not printed: {eid}", "unlocks": eid} if state in (
                          "BLOCKED_RFI", "BOUNDED_EXPOSURE") else None, notes="synthetic",
                      **({} if code in BL.ITEMS else {"item_en": code, "item_ar": code, "trade": "WATERPROOFING"}))
    return BL.validate(ln)


def base():
    return [
        _ln("FIN.PLASTER", "HL:WALL_FINISH:R1:PLASTER", "BOUNDED_EXPOSURE", rng=(40.0, 44.0)),
        _ln("FIN.PLASTER", "HL:WALL_FINISH:R2:PLASTER", "BOUNDED_EXPOSURE", rng=(30.0, 30.0)),
        _ln("FIN.CEILING", "R3:ceiling over void", "BLOCKED_RFI"),
        _ln("FIN.CEILING", "R3:ceiling#ROOM", "MEASURED", net=25.0),
        _ln("FIN.WP.ROOF", "ROOF-1:wp_membrane", "MEASURED", net=100.01),
        _ln("FIN.PLASTER", "HL:WALL_FINISH:R9:PLASTER", "MEASURED", net=50.0),
        _ln("STR.CONC.COLUMN", "COL:R1", "MEASURED", net=2.0, unit="m3"),
    ]


LN = base()
ID = {ln["location"]["element_id"]: ln["line_id"] for ln in LN}
BY = {ln["line_id"]: ln for ln in LN}
SRC = [{"task": t, "file": f"research/w736/{t}.json", "sha256": "a" * 64, "merge_commit": "b" * 40,
        "checker_run": f"checker {t}"} for t in ("T-B", "T-C", "T-M", "DG-1")]


def _arr(eid, lo=None, hi=None, state="HELD_BOUND"):
    return {"edge_id": eid, "class": "EXTERNAL_CORNER", "state": state, "low": lo, "high": hi, "why": "synthetic"}


def bead(host, action, arrises, lo, hi):
    eid = host
    return {"piece": A.P_BEAD, "action": action, "host_line_id": ID[eid], "element_id": eid.replace(":PLASTER", "#BEAD"),
            "source_tasks": ["T-B", "T-M"], "rule": "R-T728-1", "status": "HELD", "why": "host HELD",
            "expect": {"item_code": "FIN.PLASTER", "element_id": eid, "unit": "m2", "class": "HELD", "low": lo,
                       "high": hi}, "arrises": arrises}


def dg_record(line=None, band="99.900000 .. 100.000000"):
    line = line or BY[ID["ROOF-1:wp_membrane"]]
    return {"downgrade_id": "DG-0000000000000001", "line_ids": [line["line_id"]],
            "line_content_sha256": A3063._content_sha([line]), "engine_qty": line["measured_net"], "unit": "m2",
            "state": "HELD", "reason": f"UNSUPPORTED BASIS: above its same-basis band {band} m2", "file": "x.json",
            "file_sha256": "c" * 64, "checker": {"routine": "Verifier"}}


def entries():
    return [
        bead("HL:WALL_FINISH:R1:PLASTER", "BOUND", [_arr("C1", 2.9, 2.9), _arr("D1", 5.1, 5.1), _arr("C2", 2.9, 3.1),
                                                     _arr("X1", 3.0, 3.0)], 40.0, 44.0),
        bead("HL:WALL_FINISH:R2:PLASTER", "AT_LEAST", [_arr("C3", 3.0, 3.0), _arr("A1", state="HELD_BLANK")],
             30.0, 30.0),
        {"piece": A.P_CEIL, "action": "EXCLUDE", "line_id": ID["R3:ceiling over void"],
         "owner_line_id": ID["R3:ceiling#ROOM"], "cause": "DUPLICATE_FACE", "source_tasks": ["T-C", "T-M"],
         "rule": "R-T727-2", "status": "DRAWING-CONFIRMED", "why": "the void face is inside the room face",
         "expect": {"item_code": "FIN.CEILING", "element_id": "R3:ceiling over void", "unit": "m2", "class": "HELD",
                    "low": None, "high": None},
         "owner_expect": {"item_code": "FIN.CEILING", "element_id": "R3:ceiling#ROOM", "unit": "m2",
                          "class": "RELEASED", "measured_net": 25.0}},
        {"piece": A.P_DG, "action": "HOLD", "line_id": ID["ROOF-1:wp_membrane"], "source_tasks": ["DG-1"],
         "rule": "R-SYN", "status": "HELD", "why": "Checker record", "low": 99.9, "high": 100.0,
         "expect": {"item_code": "FIN.WP.ROOF", "element_id": "ROOF-1:wp_membrane", "unit": "m2", "class": "RELEASED",
                    "measured_net": 100.01}, "record": dg_record()},
    ]


def doc(ents=None):
    return {"schema": A.INPUTS_SCHEMA, "project_id": PID, "sources": SRC, "entries": entries() if ents is None else ents}


def run(ents=None, lines=None):
    lines = base() if lines is None else lines
    d = A.load_inputs(doc(ents), PID)
    ch, log = A.changes_for(d, lines)
    out, ident = A.integrate(lines, ch)
    return out, ident, ch, lines


def test_bead_by_hand():
    out, ident, ch, _ = run()
    beads = {ln["location"]["element_id"]: ln for ln in out if ln["item_code"] == A.BEAD}
    b1 = beads["HL:WALL_FINISH:R1#BEAD"]
    assert b1["unit"] == "lm" and b1["evidence_state"] == "BOUNDED_EXPOSURE"
    assert b1["bounded_range"]["low"] == pytest.approx(13.9) and b1["bounded_range"]["high"] == pytest.approx(14.1)
    b2 = beads["HL:WALL_FINISH:R2#BEAD"]
    assert b2["evidence_state"] == "BLOCKED_RFI" and b2["bounded_range"] is None and b2["measured_net"] is None
    rec = b2["calculation"]["inputs"][A.REC_KEY]
    assert rec["beside"] == {"kind": "AT_LEAST_LM", "value": 3.0, "basis": rec["beside"]["basis"]}
    assert rec["blank_arrises"] == ["A1"]
    assert ident["added"] == 2 and ident["replaced"] == 2 and ident["outside_rows"] == 5
    assert ident["beads_ceiling"] == {"BEAD_ADD:BOUND": 1, "BEAD_ADD:AT_LEAST": 1, "CEIL_EXCL:EXCLUDE": 1,
                                      "DG_HOLD:HOLD": 1}


def test_totals_by_hand():
    out, _i, ch, lines = run()
    moved = A.check_totals(A304.code_totals(lines), A304.code_totals(out), ch)
    assert set(moved) == {"FIN.PLASTER.BEAD|lm", "FIN.CEILING|m2", "FIN.WP.ROOF|m2"}
    b = moved["FIN.PLASTER.BEAD|lm"]["v3_0_76"]
    assert (b["lines"], b["bounded_lines"], b["blocked_lines"], b["released"]) == (2, 1, 1, 0.0)
    assert b["held_low"] == pytest.approx(13.9) and b["held_high"] == pytest.approx(14.1)
    c0, c1 = moved["FIN.CEILING|m2"]["base"], moved["FIN.CEILING|m2"]["v3_0_76"]
    assert (c1["lines"], c1["blocked_lines"], c1["released"]) == (c0["lines"] - 1, c0["blocked_lines"] - 1, 25.0)
    w = moved["FIN.WP.ROOF|m2"]["v3_0_76"]
    assert w["released"] == 0.0 and w["held_low"] == pytest.approx(99.9) and w["held_high"] == pytest.approx(100.0)


def test_ceiling_excluded_and_dg_held():
    out, *_ = run()
    by = {ln["line_id"]: ln for ln in out}
    k1 = by[ID["R3:ceiling over void"]]
    assert k1["evidence_state"] == "EXCLUDED_WITH_REASON" and k1["measured_net"] is None and "DUPLICATE_FACE" in k1["notes"]
    w = by[ID["ROOF-1:wp_membrane"]]
    assert w["evidence_state"] == "BOUNDED_EXPOSURE" and w["measured_net"] is None
    assert (w["bounded_range"]["low"], w["bounded_range"]["high"]) == (99.9, 100.0)
    assert w["calculation"]["inputs"][A.REC_KEY]["downgrade"]["downgrade_id"] == "DG-0000000000000001"


def test_outside_byte_identical_and_mirror():
    out, *_ = run()
    out2, *_ = run(list(reversed(entries())))
    assert sorted(A.A30.line_sha(x) for x in out) == sorted(A.A30.line_sha(x) for x in out2)
    old = {ln["line_id"]: A.A30.line_sha(ln) for ln in base()}
    for ln in out:
        if ln["location"]["element_id"] in ("HL:WALL_FINISH:R9:PLASTER", "COL:R1", "R3:ceiling#ROOM",
                                            "HL:WALL_FINISH:R1:PLASTER", "HL:WALL_FINISH:R2:PLASTER"):
            assert A.A30.line_sha(ln) == old[ln["line_id"]]


def _bad(mut, msg):
    ents = entries()
    mut(ents)
    with pytest.raises((A.InputsError, ValueError), match=msg):
        run(ents)


def test_adverse_blank_arris_on_bound():
    _bad(lambda e: e[1].update(action="BOUND"), "AT_LEAST")


def test_adverse_figure_on_blank_arris():
    _bad(lambda e: e[1]["arrises"][1].update(low=1.0), "blank is never numbered")


def test_adverse_arris_twice_and_two_hosts():
    _bad(lambda e: e[0]["arrises"].append(_arr("C1", 1.0, 1.0)), "counted once")
    _bad(lambda e: e[1]["arrises"].append(_arr("X1", 3.0, 3.0)), "two hosts")


def test_adverse_released_bead_state_refused():
    _bad(lambda e: e[0]["arrises"][0].update(state="RELEASED"), "never yields a released bead")


def test_adverse_no_measured_arris():
    _bad(lambda e: e[1].update(arrises=[_arr("A1", state="HELD_BLANK")]), "no measured arris")


def test_adverse_stale_host_range():
    _bad(lambda e: e[0]["expect"].update(high=45.0), "stale binding")


def test_adverse_host_released():
    lines = base()
    lines[0] = _ln("FIN.PLASTER", "HL:WALL_FINISH:R1:PLASTER", "MEASURED", net=42.0)
    d = A.load_inputs(doc(), PID)
    with pytest.raises(A.InputsError, match="stale binding"):
        A.changes_for(d, lines)


def test_adverse_host_not_plaster():
    _bad(lambda e: e[0]["expect"].update(item_code="FIN.PAINT"), "HELD FIN.PLASTER")


def test_adverse_record_band_and_line():
    _bad(lambda e: e[3].update(high=100.01), "not the record's")
    _bad(lambda e: e[3].update(record=dg_record(band="99.9 .. 100.0 m2 or band 99.8 .. 100.0")), "band")
    _bad(lambda e: e[3]["record"].update(line_ids=[ID["R3:ceiling#ROOM"]]), "does not hold this line")


def test_adverse_record_stale_content():
    _bad(lambda e: e[3]["record"].update(line_content_sha256="0" * 64), "stale record")
    _bad(lambda e: e[3]["record"].update(engine_qty=100.5), "not the record's")


def test_adverse_owner_held_or_other_code():
    _bad(lambda e: e[2].update(owner_line_id=ID["R3:ceiling over void"]), "never the line itself")
    _bad(lambda e: e[2]["owner_expect"].update(class_x=1, **{"class": "HELD"}), "RELEASED")
    _bad(lambda e: e[2].update(owner_line_id=ID["ROOF-1:wp_membrane"]), "stale binding")


def test_adverse_verified_and_twice():
    _bad(lambda e: e[0].update(status="VERIFIED"), "never VERIFIED")
    out, *_ = run()
    with pytest.raises(A.InputsError, match="applied once"):
        A.changes_for(A.load_inputs(doc(), PID), out)


def test_adverse_downgrade_on_held_line():
    _bad(lambda e: e[3]["expect"].update(**{"class": "HELD"}), "RELEASED FIN.WP.ROOF")


def test_held_never_zero():
    out, *_ = run()
    for ln in out:
        if ln["item_code"] == A.BEAD:
            q = A.A30._qty(ln)
            assert q["value"] is None and (q["low"] is None or q["low"] > 0)
