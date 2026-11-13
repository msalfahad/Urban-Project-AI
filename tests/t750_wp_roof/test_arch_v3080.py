"""T-750: ARCH_TAKEOFF_V3.0.80 (WP_GATE_B_V1 + ROOF_LAYER_GATE_B_V1, R-T750-1) on the hand-calculated NON-Alsenan villa
W750 (own figures, no drawing; every figure below by hand):
  Room A (wet room, released floor membrane, its door keyed):
    P1  floor penetrations, 1 floor drain printed, no W.C.: 1 pcs, a HELD point (was HELD blank).
    P2  floor penetrations, 2 floor drains printed + 1 W.C. pan whose outlet (floor S-trap or wall P-trap) is printed
        nowhere: 2 .. 3 pcs HELD BOUNDED (was HELD blank).
    U1  wall upturn: run 4.000 m less the door gap 0.900 = 3.100 m x upturn 0.300 .. 0.450 m (sill not printed) =
        0.930 .. 1.395 m2 HELD BOUNDED (was HELD blank).
  Room B (pantry, no line of its own for the pieces below):
    DW  doorway membrane: gap 0.900 x wall 0.200 = 0.180 m2, ADDED HELD point (template: room A's released 0.180 line).
    NR  doorway transition count: one door = 1 pcs, ADDED HELD point.
    TM  open-side termination: 2.500 + 0.500 = 3.000 lm, ADDED HELD point (owner-approved box line).
    PB  floor penetration: 1 floor drain printed, no W.C. = 1 pcs, ADDED HELD point.
    TR  doorway transition m2: no threshold detail printed: ADDED HELD BLANK, cause named (never 0).
  Roof R1 (four V3.0.31 layer lines): falls screed area 50.000 m2, falls run 5.000 m at 1 % -> rise 0.050, mean 0.025:
    AT LEAST 50.000 x 0.025 = 1.250 m3 beside (t0 unprinted), the line stays HELD BLANK; insulation NAMED (unprinted);
    protection NAMED (carried by the one screed line); the finish 50.000 m2 RELEASED, untouched.
Totals by hand: FIN.WP.PENETRATION lines 2 -> 3, blocked 2 -> 0, bounded 0 -> 3, 4 .. 5 pcs (1 + 2 + 1 .. 1 + 3 + 1);
FIN.WP.WALL_UPTURN blocked 1 -> bounded 1, 0.930 .. 1.395 m2; FIN.WP.DOORWAY lines 1 -> 2, released 0.180 unchanged, held
0.180 .. 0.180; FIN.WP.DOORWAY_TRANSITION_NR lines 1 -> 2, released 1 unchanged, held 1 .. 1; FIN.WP.TERMINATION lines
1 -> 2, held 0 .. 1.000 -> 3.000 .. 4.000 lm; FIN.WP.DOORWAY_TRANSITION blocked 1 -> 2; roof-layer totals unchanged
(blank -> blank, the screed lower end beside only); released concrete 2.000 m3 and finish 50.000 m2 byte-identical.
Adverse: VERIFIED, a stale (already bounded) line, a released line named (a raise without a record), a count 1.5, a
point 0, a mm2 slip, an ADD into a room that already carries the code, an ADD_NAMED with a figure, a lower end on
insulation, a figure on a roof layer line, a line named twice, applied twice, an unknown source; mirror order gives the
same lines."""
from __future__ import annotations

import copy
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engine.source import arch_v304 as A304  # noqa: E402
from engine.source import arch_v3031 as A3031  # noqa: E402
from engine.source import arch_v3080 as A  # noqa: E402
from engine.source import boq_line as BL  # noqa: E402

PID, REV = "W750-SYNTHETIC", "f" * 64
PEN, UP, DW, NR, TM, TR = ("FIN.WP.PENETRATION", "FIN.WP.WALL_UPTURN", "FIN.WP.DOORWAY",
                           "FIN.WP.DOORWAY_TRANSITION_NR", "FIN.WP.TERMINATION", "FIN.WP.DOORWAY_TRANSITION")


def _ln(code, eid, state, net=None, unit="m2", rng=None, floor="GF", room=None, inputs=None):
    ln = BL.make_line(project_id=PID, revision_set_sha256=REV, item_code=code, unit=unit, evidence_state=state,
                      measured_net=net, gross=net, element_id=eid, floor=floor, room_id=room,
                      bounded_range=None if rng is None else {"low": rng[0], "high": rng[1], "basis": "synthetic"},
                      formula=f"synthetic {code} {eid}", inputs=inputs or {}, rule_id="R-SYN", rule_version="1",
                      geometry_source="SYNTHETIC_FIXTURE", material_state="BY_SPEC",
                      rfi={"question": f"not printed: {eid}", "unlocks": eid} if state in (
                          "BLOCKED_RFI", "BOUNDED_EXPOSURE") else None, notes="synthetic",
                      **({} if code in BL.ITEMS else {"item_en": code, "item_ar": code, "trade": "WATERPROOFING"}))
    return BL.validate(ln)


def _roof(layer, state, net=None):
    code, unit = A3031.LAYERS[layer]
    return _ln(code, f"ROOF:R1:{layer}", state, net=net, unit=unit, floor="ROOF",
               inputs={A3031.REC_KEY: {"roof": "R1", "layer": layer}})


def base():
    return [_ln(PEN, "GF-RA:wp_penetrations", "BLOCKED_RFI", unit="pcs", room="GF-RA"),
            _ln(PEN, "GF-RC:wp_penetrations", "BLOCKED_RFI", unit="pcs", room="GF-RC"),
            _ln(UP, "GF-RA:wp_wall_upturn:wet_zone", "BLOCKED_RFI", room="GF-RA"),
            _ln(DW, "GF-RA:doorway D-1", "MEASURED", net=0.18, room="GF-RA"),
            _ln(NR, "GF-RA:doorway transition nr D-1", "MEASURED", net=1.0, unit="pcs", room="GF-RA"),
            _ln(TM, "GF-RA:termination passage", "BOUNDED_EXPOSURE", unit="lm", rng=(0.0, 1.0), room="GF-RA"),
            _ln(TR, "GF-RA:doorway transition D-1", "BLOCKED_RFI", room="GF-RA"),
            _roof("FALLS_SCREED", "BLOCKED_RFI"), _roof("INSULATION", "BLOCKED_RFI"),
            _roof("PROTECTION", "BLOCKED_RFI"), _roof("FINISH", "MEASURED", net=50.0),
            _ln("STR.CONC.COLUMN", "COL:R1", "MEASURED", net=2.0, unit="m3")]


LN = base()
ID = {(ln["item_code"], ln["location"]["element_id"]): ln["line_id"] for ln in LN}
P1, P2, U1 = LN[0]["line_id"], LN[1]["line_id"], LN[2]["line_id"]
SCR, INS, PRO, FIN = LN[7]["line_id"], LN[8]["line_id"], LN[9]["line_id"], LN[10]["line_id"]
SRC = [{"task": "T-WP", "file": "research/w750/wp.json", "sha256": "a" * 64, "merge_commit": "c" * 40,
        "checker_run": "checker T-WP"},
       {"task": "T-ROOF", "file": "research/w750/roof.json", "sha256": "b" * 64, "merge_commit": "d" * 40,
        "checker_run": "checker T-ROOF"}]


def _ex(ln):
    r = ln.get("bounded_range")
    return {"item_code": ln["item_code"], "element_id": ln["location"]["element_id"], "unit": ln["unit"],
            "class": "HELD", "low": None if r is None else r["low"], "high": None if r is None else r["high"]}


def doc():
    by = {ln["line_id"]: ln for ln in LN}
    wp = {"piece": A.P_WP, "source_tasks": ["T-WP"], "rule": "R-SYN-WP"}
    rf = {"piece": A.P_ROOF, "source_tasks": ["T-ROOF"], "rule": "R-SYN-ROOF"}
    add = dict(wp, room="GF-RB", floor="GF")
    return {"schema": A.INPUTS_SCHEMA, "project_id": PID, "sources": copy.deepcopy(SRC), "entries": [
        dict(wp, action="POINT", line_id=P1, expect=_ex(by[P1]), value=1, status="DRAWING-CONFIRMED",
             why="1 floor drain printed, no W.C."),
        dict(wp, action="BOUND", line_id=P2, expect=_ex(by[P2]), low=2, high=3, status="HELD",
             why="2 floor drains printed + 1 W.C. pan outlet not printed", open="W.C. pan outlet: floor or wall"),
        dict(wp, action="BOUND", line_id=U1, expect=_ex(by[U1]), low=0.93, high=1.395, status="HELD",
             why="run 3.100 x upturn 0.300 .. 0.450 (sill not printed)"),
        dict(add, action="ADD_POINT", add_key="DOORWAY", host_line_id=ID[(DW, "GF-RA:doorway D-1")], item_code=DW,
             unit="m2", value=0.18, item="doorway membrane D-2", status="DRAWING-CONFIRMED", why="0.900 x 0.200"),
        dict(add, action="ADD_POINT", add_key="TRANSITION_NR", host_line_id=ID[(NR, "GF-RA:doorway transition nr D-1")],
             item_code=NR, unit="pcs", value=1, item="doorway transition D-2", status="DRAWING-CONFIRMED",
             why="one door"),
        dict(add, action="ADD_POINT", add_key="TERMINATION", host_line_id=ID[(TM, "GF-RA:termination passage")],
             item_code=TM, unit="lm", value=3.0, item="open-side termination", status="ASSUMED — OWNER-APPROVED",
             status_text="ASSUMED — OWNER-APPROVED (box line)", why="2.500 + 0.500"),
        dict(add, action="ADD_POINT", add_key="PENETRATION", host_line_id=P1, item_code=PEN, unit="pcs", value=1,
             item="pantry floor penetration", status="DRAWING-CONFIRMED", why="1 floor drain printed, no W.C."),
        dict(add, action="ADD_NAMED", add_key="TRANSITION", host_line_id=ID[(TR, "GF-RA:doorway transition D-1")],
             item_code=TR, unit="m2", item="doorway transition m2 D-2", status="HELD",
             why="no threshold detail printed"),
        dict(rf, action="AT_LEAST", line_id=SCR, expect=_ex(by[SCR]), value=1.25, status="ASSUMED — OWNER-APPROVED",
             why="50.000 x mean 0.025 (falls 1 % over 5.000); t0 unprinted"),
        dict(rf, action="NAMED", line_id=INS, expect=_ex(by[INS]), status="HELD", why="insulation printed nowhere"),
        dict(rf, action="NAMED", line_id=PRO, expect=_ex(by[PRO]), status="HELD",
             why="carried by the one screed line")]}


def run(d=None, lines=None):
    lines = copy.deepcopy(LN) if lines is None else lines
    inp = A.load_inputs(d or doc(), PID)
    ch, log = A.changes_for(inp, lines)
    out, ident = A.integrate(lines, ch)
    return lines, ch, out, ident


def tot(lines):
    return A304.code_totals(lines)


def test_hand_figures_and_totals():
    prev, ch, out, ident = run()
    t0, t1 = tot(prev), tot(out)
    assert t1["FIN.WP.PENETRATION|pcs"] == {"lines": 3, "released": 0.0, "held_low": 4.0, "held_high": 5.0,
                                            "bounded_lines": 3, "blocked_lines": 0}
    assert t1["FIN.WP.WALL_UPTURN|m2"]["held_low"] == pytest.approx(0.93)
    assert t1["FIN.WP.WALL_UPTURN|m2"]["held_high"] == pytest.approx(1.395)
    assert t1["FIN.WP.DOORWAY|m2"] == {"lines": 2, "released": 0.18, "held_low": 0.18, "held_high": 0.18,
                                       "bounded_lines": 1, "blocked_lines": 0}
    assert t1["FIN.WP.DOORWAY_TRANSITION_NR|pcs"]["released"] == 1.0
    assert t1["FIN.WP.DOORWAY_TRANSITION_NR|pcs"]["held_low"] == 1.0
    assert (t1["FIN.WP.TERMINATION|lm"]["held_low"], t1["FIN.WP.TERMINATION|lm"]["held_high"]) == (3.0, 4.0)
    assert t1["FIN.WP.DOORWAY_TRANSITION|m2"]["blocked_lines"] == 2
    for k in ("FIN.ROOF.SCREED|m3", "FIN.ROOF.INSULATION|m2", "FIN.ROOF.PROTECTION|m2", "FIN.ROOF.FINISH|m2",
              "STR.CONC.COLUMN|m3"):
        assert t0[k] == t1[k]
    moved = A.check_totals(t0, t1, ch)
    assert set(moved) == {"FIN.WP.PENETRATION|pcs", "FIN.WP.WALL_UPTURN|m2", "FIN.WP.DOORWAY|m2",
                          "FIN.WP.DOORWAY_TRANSITION_NR|pcs", "FIN.WP.TERMINATION|lm", "FIN.WP.DOORWAY_TRANSITION|m2"}
    assert ident["replaced"] == 6 and ident["added"] == 5
    assert ident["roof_buildup_v3_0_31"]["roofs"] == 1
    assert ident["wp_roof"] == {"WP_WIRE:POINT": 1, "WP_WIRE:BOUND": 2, "WP_WIRE:ADD_POINT": 4,
                                "WP_WIRE:ADD_NAMED": 1, "ROOF_WIRE:AT_LEAST": 1, "ROOF_WIRE:NAMED": 2}


def test_released_and_untouched_lines_byte_identical():
    prev, ch, out, _ = run()
    from engine.source import arch_v30 as A30
    named = {c["after"]["line_id"] for c in ch}
    by = {ln["line_id"]: ln for ln in out}
    for ln in prev:
        if ln["line_id"] not in named:
            assert A30.line_sha(ln) == A30.line_sha(by[ln["line_id"]])
    assert by[FIN]["measured_net"] == 50.0


def test_roof_screed_lower_end_beside_never_a_quantity():
    _, _, out, _ = run()
    s = next(ln for ln in out if ln["line_id"] == SCR)
    assert s["evidence_state"] == "BLOCKED_RFI" and s["measured_net"] is None and s["bounded_range"] is None
    assert A.beside_of(s) == ("AT_LEAST", 1.25)
    assert A.census(out)["FIN.ROOF.SCREED"]["at_least_sum_run_record_only"] == 1.25


def test_added_lines_are_their_rooms_held_never_zero():
    _, ch, out, _ = run()
    adds = [c["after"] for c in ch if c["action"] == "ADD"]
    assert {a["location"]["room_id"] for a in adds} == {"GF-RB"}
    assert all(a["location"]["element_id"].startswith("T750:ADD:GF-RB#") for a in adds)
    named = next(a for a in adds if a["item_code"] == TR)
    assert named["evidence_state"] == "BLOCKED_RFI" and named["bounded_range"] is None and named["measured_net"] is None
    for a in adds:
        assert A.line_class(a) == "HELD"


def test_mirror_order_same_lines():
    d = doc()
    d2 = copy.deepcopy(d)
    d2["entries"] = list(reversed(d2["entries"]))
    _, _, o1, _ = run(d)
    _, _, o2, _ = run(d2)
    k = sorted(BL.dumps([x]) for x in o1)
    assert k == sorted(BL.dumps([x]) for x in o2)


def _bad(mut, err=A.InputsError, match=None):
    d = doc()
    mut(d)
    with pytest.raises(err, match=match):
        run(d)


def test_adverse_verified():
    _bad(lambda d: d["entries"][0].update(status="VERIFIED"), match="never VERIFIED")


def test_adverse_stale_line():
    def m(d):
        d["entries"][0]["expect"]["low"], d["entries"][0]["expect"]["high"] = 0.0, 1.0
    _bad(m, match="stale")


def test_adverse_released_line_never_raised_without_record():
    def m(d):
        by = {ln["line_id"]: ln for ln in LN}
        lid = ID[(DW, "GF-RA:doorway D-1")]
        d["entries"].append({"piece": A.P_WP, "source_tasks": ["T-WP"], "rule": "R", "action": "POINT", "line_id": lid,
                             "expect": dict(_ex(by[lid]), **{"class": "RELEASED"}), "value": 0.19,
                             "status": "HELD", "why": "a raise"})
    _bad(m, match="Checker record")


def test_adverse_fractional_count():
    _bad(lambda d: d["entries"][1].update(high=2.5), match="whole number")


def test_adverse_point_zero_and_slip():
    _bad(lambda d: d["entries"][0].update(value=0), match="never 0")
    _bad(lambda d: d["entries"][2].update(high=1395.0), match="unit slip")


def test_adverse_add_into_room_that_carries_the_code():
    _bad(lambda d: d["entries"][6].update(room="GF-RA"), match="one physical piece")


def test_adverse_add_named_with_figure():
    _bad(lambda d: d["entries"][7].update(value=0.16), match="no figure")


def test_adverse_lower_end_on_insulation():
    def m(d):
        d["entries"][9].update(action="AT_LEAST", value=50.0)
    _bad(m, match="falls-screed")


def test_adverse_figure_on_roof_layer_line():
    _bad(lambda d: d["entries"][8].update(action="POINT"), match="piece / action")


def test_adverse_named_twice_and_unknown_source():
    _bad(lambda d: d["entries"].append(copy.deepcopy(d["entries"][0])), match="named twice")
    _bad(lambda d: d["entries"][0].update(source_tasks=["T-NONE"]), match="no merged source")


def test_adverse_applied_twice():
    _, _, out, _ = run()
    with pytest.raises(A.InputsError, match="applied once"):
        A.changes_for(A.load_inputs(doc(), PID), out)


def test_check_lines_refuses_a_zeroed_held_line():
    prev, _, out, _ = run()
    bad = copy.deepcopy(out)
    x = next(ln for ln in bad if ln["line_id"] == P2)
    x["bounded_range"] = {"low": 0.0, "high": 0.0, "basis": "zeroed"}
    with pytest.raises(ValueError, match="not in its state"):
        A.check_lines(bad, prev)
