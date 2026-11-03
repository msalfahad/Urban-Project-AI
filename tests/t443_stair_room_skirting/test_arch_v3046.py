"""T-443: ARCH_TAKEOFF_V3.0.46 (stair-room skirting split) on a hand-calculated NON-Alsenan villa (K443).

Villa K443, by hand (own figures; nothing from the development villa). Room-local metres, origin = the room's
south-west inner corner.

  GF stair room RS (engine wall + column run 8.30 lm; its skirting line BLOCKED_RFI, no figure). Floor part HALL at
  +1.20 (floor line FIN.FLOOR.FINISH_HELD):
     S  y=0,  3.00: wall h1 0.00..1.80 | door D-1 1.80..2.70 (0.90) | wall h2 2.70..3.00          faces 2.10
     E  x=3,  2.00: wall h3 0.00..0.80 | passage P-1 0.80..1.70 (0.90) | wall h4 1.70..2.00       faces 1.10
                    jamb returns of P-1: 2 x 0.25 (reveal owner open) -> HELD BLANK child, 0.50 beside
     N  y=2,  3.00: open (flight foot) 0.00..1.20 | guard band 1.20..3.00 (role open) -> HELD BLANK child, 1.80 beside
     W  x=0,  2.00 (t from 2.00 down): stair side FL-A.W1 0.00..0.10 | wall h5 0.10..2.00         faces 1.90
     HALL: gross 5.10 + 1.80 = 6.90; deductions D-1 0.90 + P-1 0.90 = 1.80; net 5.10 lm.
     Closure: 5.10 (child) + flight FL-A west 2.90 (owned by the stair line) + strip face 0.30 (unread remainder)
     = 8.30 = run. Parent stays HELD BLANK with the 0.30 remainder.
  2F stair room RT (run 9.30 lm). Floor part LOBBY at +7.00 (floor line FIN.FLOOR.PORCELAIN, material Q-70 A style):
     S  y=0,    2.40: wall k1                                                                    faces 2.40
     E  x=2.4,  1.50: wall k2 0.00..0.30 | LIFT opening L-1 0.30..1.40 (1.10) | wall k3 1.40..1.50 faces 0.40
     N  y=1.5,  2.40: open (slab-opening edge)
     W  x=0,    1.50: wall k4                                                                    faces 1.50
     LOBBY: gross 4.30 + 1.10 = 5.40; deduction L-1 1.10 WHOLE (no jamb skirting); net 4.30 lm.
     Closure: 4.30 + faces beside the slab opening with no floor 5.00 = 9.30 = run. Parent NOT_APPLICABLE.
  Valued 5.10 + 4.30 = 9.40 lm (was 0, both parents blocked); held children 2 (band, P-1 jambs).
"""
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
from engine.source import arch_v3046 as A  # noqa: E402
from engine.source import boq_line as BL  # noqa: E402

PID, REV = "villa-k443", "f" * 64
DOCS = [{"file": "k443_arch.dxf", "sha256": "c" * 64}]


def _src(t):
    return {"task": t, "file": f"research/k443/{t}.csv", "sha256": t[-1] * 64, "merge_commit": "b" * 40,
            "checker_run": f"checker {t} Gate A PASS"}


def _line(code, unit, room, floor, ev, eid, net=None, gross=None, rfi=None):
    return BL.make_line(project_id=PID, revision_set_sha256=REV, item_code=code, unit=unit, evidence_state=ev,
                        measured_net=net, gross=gross, element_id=eid, floor=floor, room_id=room,
                        formula=f"{code} {room}", documents=DOCS, rule_id="G", rule_version="1", rfi=rfi, notes="k",
                        item_en=code, item_ar="بند", trade="FLOOR_FINISH")


def base_lines():
    q = {"question": "stair room skirting: material / form", "unlocks": "stair room"}
    return [
        _line("FIN.SKIRTING", "lm", "RS", "GF", "BLOCKED_RFI", "RS:skirting", rfi=q),
        _line("FIN.SKIRTING", "lm", "RT", "2F", "BLOCKED_RFI", "RT:skirting", rfi=q),
        _line("FIN.FLOOR.PORCELAIN", "m2", "RS", "GF", "MEASURED", "RS:HALL:floor", net=6.0, gross=6.0),
        _line("FIN.FLOOR.PORCELAIN", "m2", "RT", "2F", "MEASURED", "RT:LOBBY:floor", net=3.6, gross=3.6),
        _line("FIN.SKIRTING", "lm", "R9", "GF", "MEASURED", "R9:skirting", net=12.0, gross=12.0),
        _line("FIN.STAIR.SKIRTING", "lm", "RS", "GF", "BLOCKED_RFI", "FL-A:skirting", rfi=q),
    ]


def _id(lines, eid):
    return next(x["line_id"] for x in lines if x["location"]["element_id"] == eid)


def hall():
    return {"part": "HALL", "level": 1.20, "evidence_status": "DRAWING-CONFIRMED", "evidence_state": "MEASURED",
            "material": {"kind": "HELD_WITH_FLOOR", "basis": "hall floor finish not scheduled (designer item)"},
            "sides": [
                {"id": "S", "line": "GF:y=0", "t0": 0.0, "dir": 1, "length": 3.0, "stretches": [
                    {"s0": 0.0, "s1": 1.8, "kind": "WALL", "handles": "h1"},
                    {"s0": 1.8, "s1": 2.7, "kind": "DOOR", "opening_id": "D-1"},
                    {"s0": 2.7, "s1": 3.0, "kind": "WALL", "handles": "h2"}]},
                {"id": "E", "line": "GF:x=3", "t0": 0.0, "dir": 1, "length": 2.0, "stretches": [
                    {"s0": 0.0, "s1": 0.8, "kind": "WALL", "handles": "h3"},
                    {"s0": 0.8, "s1": 1.7, "kind": "PASSAGE", "opening_id": "P-1"},
                    {"s0": 1.7, "s1": 2.0, "kind": "WALL", "handles": "h4"}]},
                {"id": "N", "line": "GF:y=2", "t0": 3.0, "dir": -1, "length": 3.0, "stretches": [
                    {"s0": 0.0, "s1": 1.2, "kind": "OPEN", "note": "flight foot"},
                    {"s0": 1.2, "s1": 3.0, "kind": "GUARD_HELD", "group": "BAND",
                     "cause": "solid band between flights: guard or wall face not printed"}]},
                {"id": "W", "line": "GF:x=0", "t0": 2.0, "dir": -1, "length": 2.0, "stretches": [
                    {"s0": 0.0, "s1": 0.1, "kind": "STAIR_SIDE", "flight": "FL-A.W1"},
                    {"s0": 0.1, "s1": 2.0, "kind": "WALL", "handles": "h5"}]}],
            "jambs": [{"id": "P-1.J1", "opening_id": "P-1", "depth": 0.25, "group": "P-1-JAMBS",
                       "cause": "reveal owner (tile or skirting) not printed"},
                      {"id": "P-1.J2", "opening_id": "P-1", "depth": 0.25, "group": "P-1-JAMBS",
                       "cause": "reveal owner (tile or skirting) not printed"}]}


def lobby():
    return {"part": "LOBBY", "level": 7.00, "evidence_status": "VERIFIED", "evidence_state": "MEASURED",
            "material": {"kind": "OWNER_APPROVED", "basis": "porcelain skirting, ASSUMED - OWNER-APPROVED Q-70 A"},
            "sides": [
                {"id": "S", "line": "2F:y=0", "t0": 0.0, "dir": 1, "length": 2.4, "stretches": [
                    {"s0": 0.0, "s1": 2.4, "kind": "WALL", "handles": "k1"}]},
                {"id": "E", "line": "2F:x=2.4", "t0": 0.0, "dir": 1, "length": 1.5, "stretches": [
                    {"s0": 0.0, "s1": 0.3, "kind": "WALL", "handles": "k2"},
                    {"s0": 0.3, "s1": 1.4, "kind": "LIFT_OPENING", "opening_id": "L-1"},
                    {"s0": 1.4, "s1": 1.5, "kind": "WALL", "handles": "k3"}]},
                {"id": "N", "line": "2F:y=1.5", "t0": 2.4, "dir": -1, "length": 2.4, "stretches": [
                    {"s0": 0.0, "s1": 2.4, "kind": "OPEN", "note": "slab-opening edge"}]},
                {"id": "W", "line": "2F:x=0", "t0": 1.5, "dir": -1, "length": 1.5, "stretches": [
                    {"s0": 0.0, "s1": 1.5, "kind": "WALL", "handles": "k4"}]}]}


OWNERS = [{"id": "FL-A.W1", "line": "GF:x=0", "t0": 1.9, "t1": 4.8, "lo": 1.2, "hi": 3.0}]


def inputs(lines):
    gf = {"parent": _id(lines, "RS:skirting"), "room": "RS", "floor": "GF", "expect": {"evidence_state": "BLOCKED_RFI"},
          "engine_run_lm": 8.3, "source_tasks": ["T-A"],
          "parts": [dict(hall(), floor_line=_id(lines, "RS:HALL:floor"))],
          "held_groups": [
              {"group": "BAND", "part": "HALL", "cause": "guard band role not printed", "beside": "1.80 lm drawn",
               "rfi": "stair band: guard upstand or wall, finish"},
              {"group": "P-1-JAMBS", "part": "HALL", "cause": "reveal owner open", "beside": "2 x 0.25 = 0.50 lm",
               "rfi": "reveal of P-1: tile return or skirting"}],
          "owned_elsewhere": [{"what": "flight FL-A west face", "lm": 2.9, "owner": "FL-A.W1 (stair skirting)",
                               "owner_line": _id(lines, "FL-A:skirting")}],
          "remainder": [{"what": "strip north face (unread)", "lm": 0.3, "why": "strip not read",
                         "rfi": "strip under the winders: face or open"}]}
    f2 = {"parent": _id(lines, "RT:skirting"), "room": "RT", "floor": "2F", "expect": {"evidence_state": "BLOCKED_RFI"},
          "engine_run_lm": 9.3, "source_tasks": ["T-A"],
          "parts": [dict(lobby(), floor_line=_id(lines, "RT:LOBBY:floor"))],
          "no_floor": [{"what": "faces beside the slab opening", "lm": 5.0, "why": "no floor at +7.00"}]}
    return {"schema": A.INPUTS_SCHEMA, "project_id": PID, "sources": [_src("T-A")], "owners": OWNERS,
            "splits": [gf, f2]}


def run(lines=None, doc=None):
    lines = lines or base_lines()
    d = A.load_inputs(doc or inputs(lines), PID)
    ch, log = A.changes_for(d, lines)
    out, ident = A.integrate(lines, ch)
    return lines, ch, log, out, ident


def _by(out, eid):
    return next(x for x in out if x["location"]["element_id"] == eid)


# ------------------------------------------------------------------------------------------------ normal
def test_part_children_hand_figures():
    lines, ch, log, out, ident = run()
    h, lo = _by(out, "SKIRT-T443:HALL"), _by(out, "SKIRT-T443:LOBBY")
    assert (h["gross"], h["measured_net"]) == (pytest.approx(6.9), pytest.approx(5.1))
    assert sorted(d["opening_id"] for d in h["deductions"]) == ["D-1", "P-1"]
    assert (lo["gross"], lo["measured_net"]) == (pytest.approx(5.4), pytest.approx(4.3))
    d = lo["deductions"][0]
    assert d["opening_id"] == "L-1" and d["kind"] == "LIFT_OPENING" and d["jamb_skirting"] is False
    assert d["qty"] == pytest.approx(1.1) and not lo["additions"]
    assert log["valued_lm"] == pytest.approx(9.4) and ident["stair_rooms"]["parts_lm"] == pytest.approx(9.4)
    assert h["material_state"] == "BY_SPEC" and lo["material_state"] == "PROJECT_OWNER_FACT"
    assert h["calculation"]["inputs"][A.REC_KEY]["floor_line"] == _id(lines, "RS:HALL:floor")


def test_held_children_blank_never_zero():
    _, ch, log, out, ident = run()
    for eid, beside in (("SKIRT-T443:HALL:BAND", "1.80"), ("SKIRT-T443:HALL:P-1-JAMBS", "0.50")):
        x = _by(out, eid)
        assert x["evidence_state"] == "BLOCKED_RFI" and x["measured_net"] is None and x["gross"] is None
        assert beside in x["rfi"]["bound_beside"]
    assert ident["stair_rooms"]["held_children"] == 2 and log["held_groups"] == 2


def test_parents_remainder_and_not_applicable():
    lines, ch, log, out, ident = run()
    gf, f2 = _by(out, "RS:skirting"), _by(out, "RT:skirting")
    assert gf["evidence_state"] == "BLOCKED_RFI" and gf["measured_net"] is None
    assert "strip" in gf["rfi"]["question"] and gf["line_id"] == _id(lines, "RS:skirting")
    c = gf["calculation"]["inputs"][A.REC_KEY]["closure"]
    assert c["closure_lm"] == pytest.approx(8.3) and c["residual_lm"] == pytest.approx(0.0)
    assert f2["evidence_state"] == "NOT_APPLICABLE_WITH_EVIDENCE" and f2["rfi"] is None and f2["notes"]
    assert ident["stair_rooms"]["parents_held"] == 1 and ident["stair_rooms"]["parents_na"] == 1


def test_outside_lines_byte_identical_and_totals_only_skirting():
    lines, ch, log, out, ident = run()
    named = {c["after"]["line_id"] for c in ch}
    for ln in lines:
        if ln["line_id"] not in named:
            assert A30.line_sha(ln) == A30.line_sha(next(x for x in out if x["line_id"] == ln["line_id"]))
    t0, t1 = A304.code_totals(lines), A304.code_totals(out)
    assert {k.split("|")[0] for k in set(t0) | set(t1) if t0.get(k) != t1.get(k)} == {"FIN.SKIRTING"}
    assert ident["added"] == 4 and ident["replaced"] == 2


def test_mirror_invariance():
    """the hall mirrored about x = 1.5 (E <-> W sides, directions reversed): the same lengths and deductions."""
    lines = base_lines()
    doc = inputs(lines)
    h = doc["splits"][0]["parts"][0]
    for sd in h["sides"]:
        if sd["line"] == "GF:x=3":
            sd["line"] = "GF:x=0"
        elif sd["line"] == "GF:x=0":
            sd["line"] = "GF:x=3"
        elif sd["line"].startswith("GF:y="):
            sd["t0"], sd["dir"] = 3.0 - sd["t0"], -sd["dir"]
    doc["owners"] = [dict(OWNERS[0], line="GF:x=3")]
    out = run(lines, doc)[3]
    h1 = _by(run()[3], "SKIRT-T443:HALL")
    h2 = _by(out, "SKIRT-T443:HALL")
    assert h2["measured_net"] == pytest.approx(h1["measured_net"]) and h2["gross"] == pytest.approx(h1["gross"])


def test_write_files(tmp_path):
    lines, ch, log, out, ident = run()
    names, ident2, led = A.write(tmp_path, lines, ch, log)
    assert "V3_0_46_BOQ_LINES.json" in names
    assert ident2["diff"]["vs_base"] == {"ADDED": 4, "CHANGED": 2, "SAME": 4}
    run_doc = json.loads((tmp_path / "V3_0_46_RUN.json").read_text(encoding="utf-8"))
    assert set(k.split("|")[0] for k in run_doc["totals_moved_by_code"]) == {"FIN.SKIRTING"}
    assert led["released_default"] is False and all(r["release_status"] == "NOT RELEASED" for r in led["rows"])


# ------------------------------------------------------------------------------------------------ adverse
def _err(mut, match, lines=None):
    lines = lines or base_lines()
    doc = inputs(lines)
    mut(doc, lines)
    with pytest.raises(A.InputsError, match=match):
        A.changes_for(A.load_inputs(doc, PID), lines)


def test_lift_opening_skirted_as_passage_refused():
    def m(doc, _):
        doc["splits"][1]["parts"][0]["jambs"] = [{"id": "L-1.J", "opening_id": "L-1", "depth": 0.2, "cause": "x"}]
    _err(m, "lift-opening jamb")


def test_lift_jamb_skirting_caught_after_integration():
    lines, ch, log, out, ident = run()
    bad = copy.deepcopy(out)
    lo = _by(bad, "SKIRT-T443:LOBBY")
    lo["deductions"][0]["jamb_skirting"] = "LISTED_SEPARATELY"
    with pytest.raises(ValueError, match="skirted as a passage"):
        A.check_stair_rooms(bad)


def test_door_jamb_refused():
    def m(doc, _):
        doc["splits"][0]["parts"][0]["jambs"].append({"id": "D-1.J", "opening_id": "D-1", "depth": 0.2, "cause": "x"})
    _err(m, "door jamb")


def test_face_owned_by_flight_refused():
    def m(doc, _):
        w = doc["splits"][0]["parts"][0]["sides"][3]
        w["stretches"] = [{"s0": 0.0, "s1": 2.0, "kind": "WALL", "handles": "h5"}]
    _err(m, "one base, one owner")


def test_landing_at_other_level_is_not_an_overlap():
    lines = base_lines()
    doc = inputs(lines)
    doc["owners"] = OWNERS + [{"id": "FL-B.landing", "line": "GF:x=0", "t0": 0.0, "t1": 1.9, "lo": 3.5, "hi": 3.5}]
    assert _by(run(lines, doc)[3], "SKIRT-T443:HALL")["measured_net"] == pytest.approx(5.1)


def test_held_with_value_refused():
    def m(doc, _):
        doc["splits"][0]["held_groups"][0]["value"] = 1.8
    _err(m, "HELD_WITH_VALUE")


def test_held_stretch_carried_as_zero_refused():
    def m(doc, _):
        doc["splits"][0]["parts"][0]["sides"][2]["stretches"][1]["lm"] = 0
    _err(m, "never 0")


def test_held_stretch_without_line_refused():
    def m(doc, _):
        doc["splits"][0]["held_groups"] = doc["splits"][0]["held_groups"][1:]
    _err(m, "never dropped")


def test_closure_residual_refused():
    def m(doc, _):
        doc["splits"][0]["remainder"] = []           # the 0.30 strip face silently dropped
    _err(m, "closure")


def test_unit_slip_refused():
    def m(doc, _):
        doc["splits"][1]["parts"][0]["sides"][0]["length"] = 2400.0
    _err(m, "mm / cm")


def test_opening_without_id_refused():
    def m(doc, _):
        del doc["splits"][0]["parts"][0]["sides"][0]["stretches"][1]["opening_id"]
    _err(m, "opening id")


def test_gap_in_side_refused():
    def m(doc, _):
        doc["splits"][0]["parts"][0]["sides"][0]["stretches"][2]["s0"] = 2.8
    _err(m, "gap")


def test_face_without_handle_refused():
    def m(doc, _):
        del doc["splits"][0]["parts"][0]["sides"][0]["stretches"][0]["handles"]
    _err(m, "handle")


def test_same_face_in_two_parts_refused():
    def m(doc, lines):
        p2 = copy.deepcopy(doc["splits"][0]["parts"][0])
        p2["part"] = "HALL-B"
        p2["jambs"] = []
        for sd in p2["sides"]:
            for st in sd["stretches"]:
                if st.get("group") == "BAND":
                    st["group"] = "BAND-B"
        doc["splits"][0]["parts"].append(p2)
        doc["splits"][0]["held_groups"].append({"group": "BAND-B", "part": "HALL-B", "cause": "x", "beside": "x",
                                                "rfi": "x"})
        doc["splits"][0]["engine_run_lm"] = 13.4
    _err(m, "one face, one owner")


def test_stale_parent_refused():
    lines = base_lines()
    doc = inputs(lines)
    lines[0] = _line("FIN.SKIRTING", "lm", "RS", "GF", "MEASURED", "RS:skirting", net=8.3, gross=8.3)
    with pytest.raises(A.InputsError, match="stale binding"):
        A.changes_for(A.load_inputs(doc, PID), lines)


def test_floor_line_of_other_room_refused():
    def m(doc, lines):
        doc["splits"][0]["parts"][0]["floor_line"] = _id(lines, "RT:LOBBY:floor")
    lines = base_lines()
    doc = inputs(lines)
    m(doc, lines)
    with pytest.raises(A.InputsError, match="not a FIN.FLOOR / landing"):
        A.changes_for(A.load_inputs(doc, PID), lines)


def test_owner_approved_material_needs_owner_answer():
    def m(doc, _):
        doc["splits"][1]["parts"][0]["material"]["basis"] = "porcelain (assumed)"
    _err(m, "Q-nn")


def test_applied_once():
    lines, ch, log, out, ident = run()
    with pytest.raises(A.InputsError, match="applied once"):
        A.changes_for(A.load_inputs(inputs(lines), PID), out)
