"""T-446 JOIN_RERUN_V1 (R-T446-1) on hand villa K446 (not Alsenan).

Villa K446, two storeys, hand figures:
  H1 GF hall 6.00 x 5.00 = 30.00 m2 dry (floor net 29.70 after the lift threshold's certain floor part 1.00 x 0.30),
     ceiling line 30.00 (face plan area), skirting 18.00 lm
  LT lift threshold at the GF landing door: 1.00 x 0.50 = 0.50 m2 (B6-07), lies in H1: ceiling = H1's ceiling (host),
     band part = door head; skirting none (spans the door)
  DT marble threshold in a bath door strip 0.80 x 0.15 = 0.12 m2: door head, door frame
  TS held passage strip (finish not established): m2 HELD (never 0); jambs 2 x 0.20 = 0.40 lm HELD (silent)
  NA threshold listed NOT_APPLICABLE (owned by LT): not a space
  SR stair room face 'S1' with two parts: P1 hall 2.40 x 2.00 = 4.80 m2, P2 lobby 1.20 x 1.10 = 1.32 m2
     parent ceiling C-S1 BLOCKED, parent skirting K-S1 BLOCKED; P2 lies under the half landing (soffit SO-1)
     P1 faces: S wall 2.40 - door 0.90 = 1.50; E wall 2.00; W along flight F1 2.00 (stair skirting, no part skirting);
               N divider 2.40 HELD  -> 3.50 lm DRAWING-CONFIRMED + 2.40 HELD
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t446"))
sys.path.insert(0, str(ROOT / "research" / "agents_t435"))
import ceiling_skirting_join_v1 as J  # noqa: E402
import join_rerun_v1 as R  # noqa: E402


def L(lid, code, room, q, unit="m2", state="SOURCE_DERIVED", bound=None, el=None, floor="GF"):
    return {"line_id": lid, "item_code": code, "room_id": room, "floor": floor, "unit": unit, "measured_net": q,
            "evidence_state": state, "bounded_range": bound, "trade": "", "element_id": el or f"{room}:x"}


def villa():
    return [
        L("F-H1", "FIN.FLOOR.PORCELAIN", "H1", 29.70), L("C-H1", "FIN.CEILING", "H1", 30.00),
        L("K-H1", "FIN.SKIRTING", "H1", 18.00, "lm"),
        L("LT", "FIN.MARBLE.LIFT_THRESHOLD", "H1", 0.50, state="PROVISIONAL", el="LIFT:L1-GF"),
        L("LT-E", "FIN.MARBLE.LIFT_THRESHOLD", "H1", 1.00, unit="lm", el="LIFT:L1-GF:edge"),
        L("DT", "FIN.MARBLE.THRESHOLD", "GF-STRIP-D1", 0.12, el="GF-STRIP-D1:marble threshold"),
        L("TS", "ARCH.THRESHOLD", "GF-STRIP-P1", None, state="BLOCKED_RFI", el="GF-STRIP-P1:threshold strip"),
        L("NA", "ARCH.THRESHOLD", None, None, state="NOT_APPLICABLE_WITH_EVIDENCE", el="HL:THRESHOLD:GF:OP-1"),
        L("F-P1", "FIN.FLOOR.FINISH_HELD", "S1~P1", 4.80), L("F-P2", "FIN.FLOOR.FINISH_HELD", "S1~P2", 1.32),
        L("C-S1", "FIN.CEILING", "S1", None, state="BLOCKED_RFI"), L("K-S1", "FIN.SKIRTING", "S1", None, "lm",
                                                                        state="BLOCKED_RFI"),
        L("SO-1", "FIN.STAIR.SOFFIT", None, None, state="BLOCKED_RFI", el="STAIR:ST-1:soffit"),
        L("B-H1", "FIN.FLOOR.BED.DRY", "H1", 29.70),
    ]


def reasons(extra=()):
    rs = [
        {"space_id": "H1~LIFT:L1-GF", "layer": "CEILING", "code": "CEILING_ON_HOST_FACE", "line_id": "C-H1"},
        {"space_id": "H1~LIFT:L1-GF", "layer": "CEILING", "code": "OPENING_SOFFIT_IN_WALL"},
        {"space_id": "H1~LIFT:L1-GF", "layer": "SKIRTING", "code": "DOORWAY_STRIP"},
        {"space_id": "GF-STRIP-D1", "layer": "CEILING", "code": "OPENING_SOFFIT_IN_WALL"},
        {"space_id": "GF-STRIP-D1", "layer": "SKIRTING", "code": "DOORWAY_STRIP"},
        {"space_id": "GF-STRIP-P1", "layer": "CEILING", "code": "OPENING_SOFFIT_IN_WALL"},
        {"space_id": "S1~P1", "layer": "CEILING", "code": "CEILING_ON_HOST_FACE", "line_id": "C-S1"},
        {"space_id": "S1~P1", "layer": "SKIRTING", "code": "SKIRTING_ON_HOST_FACE", "line_id": "K-S1"},
        {"space_id": "S1~P2", "layer": "CEILING", "code": "UNDER_FLIGHT_SOFFIT", "line_id": "SO-1"},
        {"space_id": "S1~P2", "layer": "SKIRTING", "code": "SKIRTING_ON_HOST_FACE", "line_id": "K-S1"},
    ]
    return rs + list(extra)


def run(lines=None, rs=None):
    lines = villa() if lines is None else lines
    base = J.census(lines)
    els = R.element_spaces(lines, set(base))
    for e in els:
        if e["space_id"] == "GF-STRIP-P1":
            e["wall_face_lm"], e["wall_face_status"] = 0.40, "HELD: jamb returns 2 x 0.20"
    sp = J.census(lines, els)
    rs = reasons() if rs is None else rs
    rows = R.apply_host_rule(J.join(sp, lines, rs), rs)
    return base, els, sp, rows


def get(rows, sid, layer):
    return next(r for r in rows if r["space_id"] == sid and r["layer"] == layer)


def test_normal_census_keys_and_statuses():
    base, els, sp, rows = run()
    assert sorted(base) == ["H1", "S1~P1", "S1~P2"]                    # bed line and NA threshold are not spaces
    assert sorted(e["space_id"] for e in els) == ["GF-STRIP-D1", "GF-STRIP-P1", "H1~LIFT:L1-GF"]
    assert sp["H1"].m2 == pytest.approx(29.70)                          # host m2 unchanged by its element
    assert sp["H1~LIFT:L1-GF"].m2 == pytest.approx(0.50)                # the lm edge line is no space
    got = {(r["space_id"], r["layer"]): r["status"] for r in rows}
    assert got == {
        ("H1", "CEILING"): "OWNED", ("H1", "SKIRTING"): "OWNED",
        ("H1~LIFT:L1-GF", "CEILING"): "REASON", ("H1~LIFT:L1-GF", "SKIRTING"): "REASON",
        ("GF-STRIP-D1", "CEILING"): "REASON", ("GF-STRIP-D1", "SKIRTING"): "REASON",
        ("GF-STRIP-P1", "CEILING"): "REASON", ("GF-STRIP-P1", "SKIRTING"): "SILENT_OMISSION",
        ("S1~P1", "CEILING"): "REASON", ("S1~P1", "SKIRTING"): "REASON",
        ("S1~P2", "CEILING"): "REASON", ("S1~P2", "SKIRTING"): "REASON",
    }
    # H1 ceiling 30.00 over floor 29.70: not partial; the threshold's ceiling is the host's, never a second m2
    assert get(rows, "H1", "CEILING")["line_qty"] == pytest.approx(30.00)
    assert J.overlap(rows) == []


def test_held_strip_stays_held_never_zero():
    _, _, sp, rows = run()
    assert sp["GF-STRIP-P1"].m2 is None
    r = get(rows, "GF-STRIP-P1", "SKIRTING")
    assert r["omission"] == {"unit": "lm", "value": 0.40, "status": "HELD: jamb returns 2 x 0.20"}


def test_census_re_adds_to_candidate_floor_total():
    lines = villa()
    base, _, sp, _ = run(lines)
    t = R.census_total({k: v for k, v in sp.items() if v.floor_lines}, lines)
    assert t["candidate_m2"] == pytest.approx(29.70 + 4.80 + 1.32)
    assert t["residual_m2"] == pytest.approx(0.0)
    # a held floor line is counted as held on both sides, never as 0 m2
    lines2 = villa() + [L("F-P3", "FIN.FLOOR.FINISH_HELD", "S1~P3", None, state="BOUNDED_EXPOSURE", bound={
        "low": 0.0, "high": 0.23})]
    _, _, sp2, _ = run(lines2)
    t2 = R.census_total({k: v for k, v in sp2.items() if v.floor_lines}, lines2)
    assert t2["candidate_held_lines"] == t2["census_held_lines"] == 1 and t2["residual_m2"] == pytest.approx(0.0)
    assert sp2["S1~P3"].m2 is None


def test_adverse_lift_threshold_given_a_room_ceiling():
    lines = villa() + [L("C-LT", "FIN.CEILING", "H1~LIFT:L1-GF", 0.50)]
    _, _, _, rows = run(lines)
    r = get(rows, "H1~LIFT:L1-GF", "CEILING")
    assert r["status"] == "DOUBLE_OWNED"            # the host ceiling already covers it: never summed
    # without R-T446-1 rule 2 the T-435 join alone would accept it as OWNED (the defect this rule closes)
    base = J.census(lines)
    sp = J.census(lines, R.element_spaces(lines, set(base)))
    plain = J.join(sp, lines, reasons())
    assert get(plain, "H1~LIFT:L1-GF", "CEILING")["status"] == "OWNED"


def test_adverse_stair_part_skirted_on_a_flight_side_face():
    faces = [
        {"side": "S", "kind": "WALL", "length_m": "1.4", "skirting_lm": "1.4"},
        {"side": "S", "kind": "DOOR", "length_m": "0.9", "skirting_lm": "0"},
        {"side": "S", "kind": "WALL", "length_m": "0.1", "skirting_lm": "0.1"},
        {"side": "E", "kind": "WALL", "length_m": "2.0", "skirting_lm": "2.0"},
        {"side": "W", "kind": "OPEN", "length_m": "2.0", "skirting_lm": "0.0000"},
        {"side": "N", "kind": "GUARD_HELD", "length_m": "2.4", "skirting_lm": ""},
    ]
    m = R.part_skirting(faces)
    assert m["drawn_lm"] == pytest.approx(3.50) and m["held_lm"] == [2.4]
    bad = [dict(f) for f in faces]
    bad[4]["skirting_lm"] = "2.0"                    # the flight side counted as the part's skirting
    with pytest.raises(ValueError, match="flight side or an opening"):
        R.part_skirting(bad)
    bad2 = [dict(f) for f in faces]
    bad2[1]["skirting_lm"] = "0.9"                   # skirting run across the door
    with pytest.raises(ValueError):
        R.part_skirting(bad2)
    # join level: a skirting line on the part AND the stair skirting reason -> DOUBLE_OWNED (T-435 rule kept)
    lines = villa() + [L("K-P1", "FIN.SKIRTING", "S1~P1", 5.50, "lm"), L("SK-F1", "FIN.STAIR.SKIRTING", None, 2.0,
                                                                          "lm", el="STAIR:F1:skirting")]
    rs = [r for r in reasons() if not (r["space_id"] == "S1~P1" and r["layer"] == "SKIRTING")]
    rs.append({"space_id": "S1~P1", "layer": "SKIRTING", "code": "STAIR_SKIRTING", "line_id": "SK-F1"})
    _, _, _, rows = run(lines, rs)
    assert get(rows, "S1~P1", "SKIRTING")["status"] == "DOUBLE_OWNED"


def test_adverse_part_with_own_skirting_and_host_reason():
    lines = villa() + [L("K-P2", "FIN.SKIRTING", "S1~P2", 2.30, "lm")]
    _, _, _, rows = run(lines)
    assert get(rows, "S1~P2", "SKIRTING")["status"] == "DOUBLE_OWNED"


def test_element_twice_and_unknown_stretch_refused():
    lines = villa() + [L("DT2", "FIN.MARBLE.THRESHOLD", "GF-STRIP-D1", 0.12, el="GF-STRIP-D1:marble threshold")]
    base = J.census(lines)
    with pytest.raises(ValueError, match="twice"):
        R.element_spaces(lines, set(base))
    with pytest.raises(ValueError, match="unknown stretch"):
        R.part_skirting([{"side": "X", "kind": "BALUSTRADE", "length_m": "1", "skirting_lm": "1"}])
    with pytest.raises(ValueError, match="without a skirting figure"):
        R.part_skirting([{"side": "X", "kind": "WALL", "length_m": "1", "skirting_lm": ""}])


def test_units_kept_apart_and_mirror_invariant():
    # the lm edge of the threshold never becomes a space; mirrored ids (rotated order of lines) give the same rows
    lines = villa()
    _, _, sp1, rows1 = run(lines)
    _, _, sp2, rows2 = run(list(reversed(lines)))
    assert sorted(sp1) == sorted(sp2)
    key = lambda rs: sorted((r["space_id"], r["layer"], r["status"]) for r in rs)  # noqa: E731
    assert key(rows1) == key(rows2)
    assert all(not s.endswith(":edge") for s in sp1)


def test_delta_split_new_owner_and_m2():
    before = [
        {"space_id": "S1", "layer": "CEILING", "status": "OWNED_HELD", "line_ids": ["C-S1"], "reasons": [],
         "floor_m2": 6.12},
        {"space_id": "H1", "layer": "CEILING", "status": "OWNED", "line_ids": ["C-H1"], "reasons": [],
         "floor_m2": 30.00},
        {"space_id": "R9", "layer": "SKIRTING", "status": "SILENT_OMISSION", "line_ids": [], "reasons": [],
         "floor_m2": 1.10, "omission": {"value": None}},
    ]
    after = [
        {"space_id": "S1~P1", "layer": "CEILING", "status": "REASON", "line_ids": [],
         "reasons": ["CEILING_ON_HOST_FACE"], "floor_m2": 4.80},
        {"space_id": "H1", "layer": "CEILING", "status": "OWNED", "line_ids": ["C-H1"], "reasons": [],
         "floor_m2": 29.70},
        {"space_id": "R9", "layer": "SKIRTING", "status": "REASON", "line_ids": [],
         "reasons": ["WET_WALL_TILE_TO_FLOOR"], "floor_m2": 1.10},
        {"space_id": "LT", "layer": "CEILING", "status": "REASON", "line_ids": [], "reasons": ["X"], "floor_m2": 0.5},
    ]
    d = R.delta(before, after, {"S1": ["S1~P1"]})
    ch = {(c["space_id"], c["change"]) for c in d["changes"]}
    assert ch == {("S1", "SPLIT"), ("S1~P1", "SPLIT_FROM"), ("H1", "FLOOR_M2_CHANGED"), ("R9", "OWNER_CHANGED"),
                  ("LT", "NEW")}
    assert d["silent_before"]["skirting_spaces"] == 1 and d["silent_after"]["skirting_spaces"] == 0


def test_committed_alsenan_tables_close():
    import t446_alsenan as T
    assert T.main(["--check"]) == 0
