"""R8.9 §19-§22: GEOS cross-check V2 (all phases, no repair), the door-closure reach audit, and the authority
class of the 1 mm authored precision."""

from __future__ import annotations

import math

from engine.source import room_topology as RT, topology as T, topology_crosscheck as XC, topology_policy as TP
from tests.r8_8 import helpers as H

LABELS = [H.text(5, "A", 250, 200), H.text(6, "B", 750, 200)]


def run(parts, texts=()):
    return RT.run(H.inp(parts, texts=texts), frame_insert=None)


def test_crosscheck_all_phases_agree_is_strong_agreement():
    r = run(H.two_rooms(), LABELS)
    assert r["crosscheck"]["state"] == XC.ALL_PHASES_AGREE
    assert all(r["crosscheck"]["counts"][k] == 0 for k in (XC.PHASE_SENSITIVE_INCONCLUSIVE, XC.ALL_PHASES_DISAGREE))
    assert all(s["crosscheck"] == XC.ALL_PHASES_AGREE for s in r["sites"])


def test_crosscheck_all_phases_disagree_blocks(monkeypatch):
    real = T.analyse

    def grow(*a, **kw):
        res = real(*a, **kw)
        max(res["sites"], key=lambda z: z["area"])["area"] *= 1.01
        return res
    monkeypatch.setattr(T, "analyse", grow)
    r = run(H.two_rooms(), LABELS)
    bad = [s for s in r["sites"] if s["crosscheck"] == XC.ALL_PHASES_DISAGREE]
    assert len(bad) == 1 and XC.GEOS_CROSSCHECK_DISAGREES in bad[0]["physical_issues"]


def test_an_invalid_ts01_polygon_is_reported_not_repaired():
    # an inner loop joined to the outer wall by ONE line (a bridge): the face walk is not a simple polygon
    parts = H.box(1, 0, 0, 500, 400) + H.box(10, 200, 150, 300, 250) + [H.seg(20, 0, 200, 200, 200)]
    r = run(parts, [H.text(5, "A", 100, 100)])
    room = next(s for s in r["sites"] if s["labels"])
    assert room["crosscheck"] == XC.CHECK_INPUT_INVALID
    assert XC.GEOS_CROSSCHECK_DISAGREES not in room["issues"]
    import inspect
    assert "buffer(0)" not in inspect.getsource(XC.check) and "buffer(0)" not in inspect.getsource(XC._site_polygon)


def test_interior_stubs_are_removed_exactly_not_repaired():
    nib = H.seg(51, 250, 0, 250, 150)
    r = run(H.box(1, 0, 0, 500, 400) + [nib], [H.text(5, "A", 100, 100)])
    assert r["sites"][0]["crosscheck"] == XC.ALL_PHASES_AGREE


# ------------------------------------------------------------------------------- door closure audit
def _door(extra=()):
    walls = [H.seg(1, 0, 0, 1000, 0), H.seg(2, 1000, 0, 1000, 400), H.seg(3, 1000, 400, 0, 400), H.seg(4, 0, 400, 0, 0),
             H.seg(5, 495, 0, 495, 150), H.seg(6, 505, 0, 505, 150), H.seg(7, 495, 150, 505, 150),
             H.seg(8, 495, 250, 495, 400), H.seg(9, 505, 250, 505, 400), H.seg(10, 495, 250, 505, 250)]
    door = [H.part(20, "ARC", (495, 150, 100, 0.0, math.pi / 2), layer="DOOR", path=("70",)),
            H.seg(21, 495, 150, 495, 250, layer="DOOR", path=("70",))]
    return walls + door + list(extra)


def test_door_audit_reports_the_reach_the_evidence_uses():
    r = run(_door(), LABELS)
    a = r["roles"]["door_audit"]["I70"]
    assert a["decision"] == "CLOSED" and a["policy_ratio"] == TP.JAMB_ALLOWANCE_RATIO
    assert a["accepted_ratio_needed"] == 0.0                    # hinge and leaf end lie on the jamb caps
    assert r["openings"]["I70"]["state"] == "CLOSED"


def test_a_false_wall_within_reach_of_the_wrong_leaf_makes_the_door_unresolved_not_guessed():
    # a wall stub (connected to the outer wall) ending exactly where the OTHER leaf hypothesis lands: both
    # hypotheses close -> OPENING_CLOSURE_UNRESOLVED, the rooms it touches are blocked; nothing is guessed
    r = run(_door([H.seg(40, 595, 0, 595, 150)]), LABELS)
    assert r["openings"]["I70"]["state"] == T.OPENING_CLOSURE_UNRESOLVED
    a = r["roles"]["door_audit"]["I70"]
    assert a["decision"] == T.OPENING_CLOSURE_UNRESOLVED and all(h["within_policy"] for h in a["hypotheses"])
    # an UNCONNECTED false wall (a cross touching nothing) is not even admitted (R8.9 grade CANDIDATE)
    r = run(_door([H.seg(41, 595, 140, 595, 160), H.seg(42, 585, 150, 605, 150)]), LABELS)
    assert r["openings"]["I70"]["state"] == "CLOSED"


# ------------------------------------------------------------------------------- §22 authority class
def test_the_one_millimetre_band_is_an_engine_method_parameter_not_a_source_fact():
    c = TP.authority_classes()
    assert c["AUTHORED_PRECISION_MM"]["class"] == "ENGINE_METHOD_PARAMETER"
    assert c["AUTHORED_PRECISION_MM"]["owner_approval"].startswith("RECOMMENDED_LATER")
    assert TP.record()["digest"] == "263d2adf1d1770e1db963ac9bfde852dcedbdbd77e0040730322848c49acb450"
