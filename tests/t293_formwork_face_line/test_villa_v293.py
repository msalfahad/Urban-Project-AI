"""T-293 face-to-line rules on a hand-calculated NON-Alsenan villa (V293). Every expected value is worked by hand below.

Villa V293 (invented, not a client drawing): one interior ground beam GB1 0.30 x 0.40 between column faces 4.00 m;
an exterior ground beam GB2 0.30 deep 0.95 (printed by two levels of the element: slab top +0.95, outer ground +-0.00,
the depth verified by a merged ledger) 5.00 m face to face; a stub GB3 whose depth is not printed; column C1 0.30 x 0.30
from the ground-beam top to a printed beam soffit, 3.00 m; footing F1 1.50 x 1.50 x 0.40 (cast on blinding).

Hand values (m2):
  GB1 side A / side B, OQ-10 FORMED alternative: 4.00 x 0.40 = 1.600 each
  tee GB3 into GB1 side A: cover 0.30 x min(0.40, 0.40) = -0.120 (deducted from GB1's face: GB1's line)
  GB2 outer face above N.G. (nothing to cast against): 5.00 x 0.95 = 4.750 CALCULATED
  C1 shaft: perimeter 4 x 0.30 = 1.20 x 3.00 = 3.600 CALCULATED
  F1 sides, OQ-10 FORMED alternative: 2 (1.50 + 1.50) x 0.40 = 2.400; EARTH_CAST alternative 0.000
  GB3 sides on an unprinted depth: 2 x 1.00 x d -> HELD blank (a 1.000 m2 figure offered on a borrowed 0.50 is refused
  as a quantity and kept only as the held source value)
GB1 line totals: OQ-10 FORMED 1.600 + 1.600 - 0.120 = 3.080 (never added to anything EARTH_CAST).
"""
from __future__ import annotations

import random
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t293"))
import face_line_ledger as F  # noqa: E402

LINES = {
    "L-GB1": {"item_code": "STR.CONC.GROUND_BEAM", "element_id": "V:GB1", "evidence_state": "PROVISIONAL"},
    "L-GB2": {"item_code": "STR.CONC.GROUND_BEAM", "element_id": "V:GB2", "evidence_state": "PROVISIONAL"},
    "L-GB3": {"item_code": "STR.CONC.GROUND_BEAM", "element_id": "V:GB3", "evidence_state": "BLOCKED_RFI"},
    "L-C1": {"item_code": "STR.CONC.COLUMN", "element_id": "V:C1", "evidence_state": "PROVISIONAL"},
    "L-F1": {"item_code": "STR.CONC.FOOTING", "element_id": "V:F1", "evidence_state": "PROVISIONAL"},
}
BIND = {"GB1": ["L-GB1"], "GB2": ["L-GB2"], "GB3": ["L-GB3"], "C1": ["L-C1"], "F1": ["L-F1"]}
R = "V293 formwork ledger r1"


def face(fid, member, m2=None, status="CALCULATED", alt="", contact="FORM", item="", **k):
    d = {"face_id": fid, "revision": R, "members": [member], "m2": m2, "status": status, "alternative": alt,
         "contact": contact, "item": item, "method": "G"}
    d.update(k)
    return d


def normal():
    return [
        face("GB1-A", "GB1", 1.6, "ALTERNATIVE", "OQ10_FORMED", "OQ10", "GB1 side A FORMED"),
        face("GB1-B", "GB1", 1.6, "ALTERNATIVE", "OQ10_FORMED", "OQ10", "GB1 side B FORMED"),
        face("GB1-A-EC", "GB1", 0.0, "ALTERNATIVE", "OQ10_EARTH_CAST", "EARTH", "GB1 side A EARTH_CAST"),
        face("TEE-GB3-GB1", "GB1", -0.12, "ALTERNATIVE", "OQ10_FORMED", "OQ10", "tee GB3 ends on GB1 FORMED"),
        face("GB2-OUT", "GB2", 4.75, item="GB2 outer face above N.G.", basis_task="T-ext", basis_task_merged=True),
        face("C1-SHAFT", "C1", 3.6, item="C1 shaft"),
        face("F1-S", "F1", 2.4, "ALTERNATIVE", "OQ10_FORMED", "OQ10", "F1 sides FORMED"),
        face("F1-S-EC", "F1", 0.0, "ALTERNATIVE", "OQ10_EARTH_CAST", "EARTH", "F1 sides EARTH_CAST"),
    ]


def test_normal_every_face_once_on_its_members_line_and_hand_totals():
    out = F.tie(normal(), BIND, LINES)
    assert all(r["tie"] == F.TIED for r in out["rows"])
    c = {x["concrete_line_id"]: x["totals"] for x in F.consumer(out["rows"], LINES, "V293", {})["lines"]}
    assert c["L-GB1"]["ALTERNATIVE|OQ10_FORMED|G"]["m2"] == pytest.approx(3.080, abs=1e-9)
    assert c["L-GB1"]["ALTERNATIVE|OQ10_EARTH_CAST|G"]["m2"] == pytest.approx(0.0, abs=1e-9)
    assert c["L-GB2"]["CALCULATED||G"]["m2"] == pytest.approx(4.750, abs=1e-9)
    assert c["L-C1"]["CALCULATED||G"]["m2"] == pytest.approx(3.600, abs=1e-9)
    assert c["L-F1"]["ALTERNATIVE|OQ10_FORMED|G"]["m2"] == pytest.approx(2.400, abs=1e-9)
    assert all(abs(k["residual_m2"]) < 1e-9 for k in out["closure"])


def test_tee_cover_goes_to_the_carriers_line_not_the_incoming_beam():
    out = F.tie(normal(), BIND, LINES)
    assert {r["face_id"]: r["line_id"] for r in out["rows"]}["TEE-GB3-GB1"] == "L-GB1"


def test_adverse_unprinted_depth_is_held_blank_with_the_source_value_kept():
    f = face("GB3-S", "GB3", 1.0, "CALCULATED", item="GB3 sides on a borrowed 0.50", basis=F.UNPRINTED, lo=0.6, hi=0.8)
    r = F.tie([f], BIND, LINES)["rows"][0]
    assert r["status"] == "HELD" and r["m2"] is None and r["held_from"] == 1.0 and (r["lo"], r["hi"]) == (0.6, 0.8)
    assert r["line_state"] == "BLOCKED_RFI"           # the concrete line's own state travels with the face


def test_adverse_face_booked_to_two_members_is_refused():
    f = face("X", "GB1", 1.0)
    f["members"] = ["GB1", "GB2"]
    with pytest.raises(F.Refused, match="2 members"):
        F.tie([f], BIND, LINES)


def test_adverse_earth_face_booked_as_formed_is_refused_but_the_oq10_alternative_is_not():
    with pytest.raises(F.Refused, match="earth"):
        F.tie([face("E", "F1", 2.4, "CALCULATED", "", "EARTH", "F1 sides FORMED")], BIND, LINES)
    F.tie([face("E", "F1", 2.4, "ALTERNATIVE", "OQ10_FORMED", "EARTH", "F1 sides FORMED")], BIND, LINES)
    F.tie([face("E", "F1", 2.4, "CALCULATED", "", "EARTH", "F1 sides FORMED", forming_detail="p.9 detail 3")],
          BIND, LINES)


def test_adverse_duplicate_face_held_with_a_number_and_reversed_range_are_refused():
    with pytest.raises(F.Refused, match="twice"):
        F.tie([face("A", "GB1", 1.0), face("A", "GB1", 1.0)], BIND, LINES)
    with pytest.raises(F.Refused, match="HELD with a quantity"):
        F.tie([face("A", "GB1", 1.0, "HELD")], BIND, LINES)
    with pytest.raises(F.Refused, match="range"):
        F.tie([face("A", "GB1", None, "HELD", lo=0.9, hi=0.5)], BIND, LINES)
    with pytest.raises(F.Refused, match="unit"):
        F.tie([face("A", "GB1", 1.0, unit="m3")], BIND, LINES)


def test_adverse_member_in_no_line_and_member_in_two_lines_are_listed_never_dropped_or_divided():
    b = dict(BIND, GB4=[], GB5=["L-GB1", "L-GB2"], _reason={"GB4": "drawn, no candidate band"})
    out = F.tie([face("G4", "GB4", 1.2), face("G5", "GB5", 2.0)], b, LINES)
    r = {x["face_id"]: x for x in out["rows"]}
    assert r["G4"]["tie"] == F.NO_LINE and r["G4"]["m2"] == 1.2 and r["G4"]["tie_reason"] == "drawn, no candidate band"
    assert r["G5"]["tie"] == F.SPLIT and r["G5"]["m2"] is None and r["G5"]["held_from"] == 2.0
    assert r["G5"]["split_lines"] == ["L-GB1", "L-GB2"]
    assert all(abs(k["residual_m2"]) < 1e-9 for k in out["closure"])


def test_adverse_unmerged_basis_is_pending_blank():
    r = F.tie([face("P", "GB2", 4.75, basis_task="T-999", basis_task_merged=False)], BIND, LINES)["rows"][0]
    assert r["status"] == "PENDING-VERIFICATION" and r["m2"] is None and r["pending_from"] == 4.75


def test_adverse_a_dropped_or_altered_row_fails_the_closure():
    src = normal()
    with pytest.raises(F.Refused, match="closure"):
        F.closure(src, F.tie(src[1:], BIND, LINES)["rows"])
    alt = normal()
    alt[0] = dict(alt[0], m2=1.5)
    with pytest.raises(F.Refused, match="closure"):
        F.closure(src, F.tie(alt, BIND, LINES)["rows"])


def test_split_per_member_counts_once_in_the_closure():
    src = [face("N", "F1", -0.45, "ALTERNATIVE", "OQ10_FORMED", "OQ10", "notch FORMED")]
    parts = [dict(src[0], face_id="N.a", split_of="N", m2=-0.225), dict(src[0], face_id="N.b", split_of="N", m2=-0.225,
                                                                       members=["GB1"])]
    out = F.tie(parts, BIND, LINES, source=src)
    assert out["closure"][0]["rows"] == 1 and abs(out["closure"][0]["residual_m2"]) < 1e-9


def test_order_and_mirror_invariance():
    """mirroring the villa swaps side A / B and reverses the record order: per-line totals are identical"""
    a = F.consumer(F.tie(normal(), BIND, LINES)["rows"], LINES, "V293", {})
    m = normal()
    random.Random(7).shuffle(m)
    for f in m:
        f["item"] = f["item"].replace("side A", "side X").replace("side B", "side A").replace("side X", "side B")
    b = F.consumer(F.tie(m, BIND, LINES)["rows"], LINES, "V293", {})
    assert {x["concrete_line_id"]: x["totals"] for x in a["lines"]} == {x["concrete_line_id"]: x["totals"]
                                                                        for x in b["lines"]}
