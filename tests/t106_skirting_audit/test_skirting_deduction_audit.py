"""T-106: every skirting line re-adds from its own trail, or the difference is HELD (engine/source/
skirting_deduction_audit.py, check-only, not wired). Synthetic data only (no client drawing).

HAND fixture (written from the coordinates, not from engine output): room 4.00 x 3.00 m, corners (0,0) (4,0) (4,3) (0,3)
    gross = 2 x (4.00 + 3.00) = 14.00 m; door 0.90 + passage 1.00 = 1.90 m (UP-CER-003) -> net 14.00 - 1.90 = 12.10 m
    a 0.60 m window frame on the room face, sill not known (F-17): the edge is skirted under one reading only ->
        certain net 12.10 - 0.60 = 11.50 m; the line lists door / passage 1.90 and the glazing half 0.30 m only, so
        14.00 - 2.20 = 11.80 != 11.50: 0.30 m taken off and not listed = the equal-split credit 0.60 / 2; the edge
        0.60 m is held whole in the range line [0, 0.60]
    an unlisted 0.30 m with no range line -> one HELD record, no candidate
Every case runs in metres, in millimetres (line unit mm), mirrored and turned 30 degrees (gross from the transformed
corners). SV-A / SV-B / SV-C (tools/synth_villa, T-019) through ARCH_TAKEOFF_V2.12 with the synthetic S2 facts: every
dry / partly tiled room with a window holds its window threshold in the range line (sill not established), so each
skirting line is short of its listing by exactly its window width. SV-A by hand: LIV gross 2 x (6.0 + 8.0) = 28.00,
doors 1.00 + 0.90 + 0.90 = 2.80, window 1.50 -> net 23.70, unlisted 1.50; BED 2 x (5.8 + 3.8) = 19.20, doors 0.90 +
0.80, window 1.50 -> 16.00, 1.50; KIT 2 x (2.9 + 4.0) = 13.80, door 0.90, window 1.20 -> 11.70, 1.20; BTH 2 x (2.8 +
4.0) = 13.60, door 0.80, window 0.60 -> 12.20, 0.60 (S2 wall tile 2.40 m < 3.00 m: not full height, UP-CER-004).
"""

from __future__ import annotations

import copy
import json
import math
from pathlib import Path

import pytest

from engine.source import skirting_deduction_audit as A

ROOT = Path(__file__).resolve().parents[2]
TOL = 1e-6
CORNERS = [(0.0, 0.0), (4.0, 0.0), (4.0, 3.0), (0.0, 3.0)]
TRANSFORMS = ["none", "mirror", "rot30", "mm", "rot30_mirror_mm"]


def _xf(pts, t):
    out = []
    for x, y in pts:
        if "mirror" in t:
            x = -x
        if "rot30" in t:
            a = math.radians(30.0)
            x, y = x * math.cos(a) - y * math.sin(a), x * math.sin(a) + y * math.cos(a)
        out.append((x, y))
    return out


def _perimeter(pts):
    return sum(math.dist(pts[i], pts[(i + 1) % len(pts)]) for i in range(len(pts)))


def _line(t, *, net, deductions, room="R1", inputs=None, line_id="L-1"):
    f = 1000.0 if "mm" in t else 1.0
    gross = _perimeter(_xf(CORNERS, t))
    ln = {"schema": "URBAN_CANONICAL_BOQ_LINE_V1", "line_id": line_id, "item_code": "FIN.SKIRTING",
          "unit": "mm" if "mm" in t else "lm", "evidence_state": "SOURCE_DERIVED", "gross": gross * f,
          "measured_net": net * f, "deductions": [{"what": w, "lm": v * f} for w, v in deductions], "additions": [],
          "location": {"floor": "GF", "room_id": room, "room_name_en": "Room", "element_id": f"{room}:skirting"}}
    if inputs is not None:
        ln["calculation"] = {"inputs": {k: v * f for k, v in inputs.items()}}
    return ln


def _range(t, *, room="R1", credit, high, by=None, line_id="L-R"):
    f = 1000.0 if "mm" in t else 1.0
    return {"line_id": line_id, "item_code": "FIN.SKIRTING", "unit": "mm" if "mm" in t else "lm",
            "evidence_state": "BOUNDED_EXPOSURE", "gross": None, "measured_net": None, "deductions": [],
            "bounded_range": {"low": 0.0, "high": high * f},
            "calculation": {"inputs": {"unresolved_by_roles": {k: v * f for k, v in (by or {}).items()},
                                       "v1_equal_split_credit_lm": credit * f}},
            "location": {"floor": "GF", "room_id": room, "element_id": f"{room}:skirting, boundary role unresolved"}}


def test_hand_literals():
    for t in TRANSFORMS:
        assert _perimeter(_xf(CORNERS, t)) == pytest.approx(14.0, abs=1e-12)
    assert 14.0 - 0.9 - 1.0 == pytest.approx(12.10, abs=1e-12)


@pytest.mark.parametrize("t", TRANSFORMS)
def test_a_clean_line_readds(t):
    ln = _line(t, net=12.10, deductions=[("door / passage openings", 1.90)],
               inputs={"boundary": 14.0, "wall": 12.10, "column": 0.0, "door": 0.90, "passage": 1.0,
                       "glazing_edge": 0.0, "other": 0.0, "window_threshold": 0.0})
    res = A.audit([ln])
    (r,) = res["records"]
    assert r["status"] == "READDS" and "reason" not in r
    assert (r["gross_lm"], r["listed_deductions_lm"], r["net_lm"]) == pytest.approx((14.0, 1.9, 12.1), abs=TOL)
    assert r["decomposition"]["differs"] is False
    assert res["summary"]["readds"] == 1 and res["summary"]["held"] == 0 and res["summary"]["unexplained_lm"] == 0


@pytest.mark.parametrize("t", TRANSFORMS)
def test_the_f17_credit_is_found_and_held_with_its_cause(t):
    ln = _line(t, net=11.50, deductions=[("door / passage openings", 1.90),
                                         ("glazing edge (floor-level window line)", 0.30)],
               inputs={"boundary": 14.0, "wall": 11.50, "column": 0.0, "door": 0.90, "passage": 1.0,
                       "glazing_edge": 0.30, "other": 0.0, "window_threshold": 0.30})
    rg = _range(t, credit=0.30, high=0.60, by={"WINDOW+WINDOW_THRESHOLD": 0.60})
    lines = [ln, rg]
    before = copy.deepcopy(lines)
    res = A.audit(lines)
    assert lines == before                                        # the audit changes no line
    (r,) = res["records"]
    assert (r["status"], r["reason"]) == ("HELD", "SKIRTING_UNEXPLAINED")
    assert r["unexplained_lm"] == pytest.approx(0.30, abs=TOL) and r["readd_lm"] == pytest.approx(11.80, abs=TOL)
    c = r["candidate"]
    assert c["matches"] and c["complete"] and c["total_lm"] == pytest.approx(0.30, abs=TOL)
    assert [x["what"] for x in c["components"]] == ["F17_EQUAL_SPLIT_CREDIT"] and c["components"][0]["range_line_ids"] == ["L-R"]
    p = r["proposed_listing"]
    assert p["readds"] and p["deductions_lm"] == pytest.approx(2.50, abs=TOL)        # 14.00 - 2.50 = 11.50
    s = res["summary"]
    assert s["unexplained_lines"] == 1 and s["explained_by_components"]["lm"] == pytest.approx(0.30, abs=TOL)
    assert s["not_net_lines"] == 1 and s["unmatched_line_ids"] == []


@pytest.mark.parametrize("t", TRANSFORMS)
def test_an_unlisted_difference_without_a_range_line_is_one_held_record(t):
    ln = _line(t, net=11.80, deductions=[("door / passage openings", 1.90)])
    res = A.audit([ln])
    (r,) = res["records"]
    assert (r["status"], r["reason"]) == ("HELD", "SKIRTING_UNEXPLAINED")
    assert r["unexplained_lm"] == pytest.approx(0.30, abs=TOL) and r["candidate"] is None
    assert "proposed_listing" not in r and res["summary"]["unmatched_line_ids"] == ["L-1"]


def test_a_listed_but_not_taken_off_difference_is_negative_and_held():
    ln = _line("none", net=12.10, deductions=[("door / passage openings", 1.90), ("glazing edge", 0.30)])
    (r,) = A.audit([ln])["records"]
    assert r["reason"] == "SKIRTING_UNEXPLAINED" and r["unexplained_lm"] == pytest.approx(-0.30, abs=TOL)
    assert "listed but not taken off" in r["basis"]


def test_a_range_credit_that_does_not_match_explains_nothing():
    ln = _line("none", net=11.50, deductions=[("door / passage openings", 1.90)])     # 0.60 unlisted
    (r,) = A.audit([ln, _range("none", credit=0.30, high=0.60, by={"WINDOW+WINDOW_THRESHOLD": 0.60})])["records"]
    assert r["unexplained_lm"] == pytest.approx(0.60, abs=TOL)
    assert r["candidate"]["matches"] is False and "proposed_listing" not in r


def test_missing_lengths_are_never_zero():
    a = _line("none", net=12.10, deductions=[("door / passage openings", 1.90)])
    a["gross"] = None
    b = _line("none", net=12.10, deductions=[("door / passage openings", 1.90)], line_id="L-2")
    b["deductions"].append({"what": "passage", "lm": None})
    c = _line("none", net=12.10, deductions=[], line_id="L-3")
    c["measured_net"] = float("nan")
    res = A.audit([a, b, c])
    got = {r["line_id"]: r for r in res["records"]}
    assert got["L-1"]["reason"] == got["L-2"]["reason"] == got["L-3"]["reason"] == "SKIRTING_NOT_READDABLE"
    assert got["L-1"]["missing"] == ["gross"] and got["L-2"]["missing"] == ["deductions[1].lm"]
    assert got["L-3"]["missing"] == ["measured_net"]
    assert all("unexplained_lm" not in r for r in res["records"]) and res["summary"]["held"] == 3


def test_an_unknown_unit_is_held_not_assumed():
    ln = _line("none", net=12.10, deductions=[("door / passage openings", 1.90)])
    ln["unit"] = "ft"
    (r,) = A.audit([ln])["records"]
    assert (r["status"], r["reason"], r["unit"]) == ("HELD", "SKIRTING_UNIT_UNKNOWN", "ft")


def test_a_role_split_that_does_not_add_up_is_a_second_held_record():
    ln = _line("none", net=12.10, deductions=[("door / passage openings", 1.90)],
               inputs={"boundary": 14.0, "wall": 11.80, "column": 0.0, "door": 0.90, "passage": 1.0,
                       "glazing_edge": 0.0, "other": 0.0, "window_threshold": 0.0})        # roles 13.70 != 14.00
    recs = A.audit([ln])["records"]
    assert [r["status"] for r in recs] == ["READDS", "HELD"]
    assert recs[1]["reason"] == "SKIRTING_DECOMPOSITION_MISMATCH"
    assert recs[1]["role_sum_lm"] == pytest.approx(13.70, abs=TOL)


def test_v28_floor_glazing_comes_from_the_room_record():
    # 0.60 sill-unknown window moved whole to the range (V2.8 to_range) + 0.40 floor-level glazing never skirted
    ln = _line("none", net=11.10, deductions=[("door / passage openings", 1.90)])          # 14 - 1.9 - 1.0
    rg = _range("none", credit=0.0, high=0.60, by={"WINDOW_SILL_NOT_ESTABLISHED": 0.60})
    room = {"room_id": "R1", "skirting_windows_v28": {"to_range_lm": 0.60, "floor_glazing_lm": 0.40,
                                                      "range_out_credit_lm": 0.0}}
    (alone,) = A.audit([ln, rg])["records"]                     # the lines alone do not carry the floor glazing
    assert alone["candidate"]["matches"] is False and alone["candidate"]["complete"] is False
    (r,) = A.audit([ln, rg], [room])["records"]
    c = r["candidate"]
    assert c["matches"] and c["complete"] and c["total_lm"] == pytest.approx(1.0, abs=TOL)
    assert sorted(x["what"] for x in c["components"]) == ["F17_EQUAL_SPLIT_CREDIT", "V28_FLOOR_GLAZING",
                                                         "V28_TO_RANGE"]
    assert r["proposed_listing"]["readds"]


def test_other_items_and_range_lines_are_not_audited():
    other = dict(_line("none", net=1.0, deductions=[]), item_code="FIN.PLASTER", line_id="L-9")
    blocked = {"line_id": "L-B", "item_code": "FIN.SKIRTING", "evidence_state": "BLOCKED_RFI",
               "location": {"room_id": "R2"}}
    res = A.audit([other, blocked])
    assert res["records"] == [] and res["summary"]["not_net_lines"] == 1
    assert res["summary"]["not_net"][0]["evidence_state"] == "BLOCKED_RFI"


def test_policy_and_not_wired():
    p = A.policy_record()
    assert p["policy"] == "SKIRTING_DEDUCTION_AUDIT_V1" and p["wired"] is False
    assert "UP-QTY-STATUS-001" in p["rules"] and "UP-CER-003" in p["rules"]
    for f in (ROOT / "tools" / "urban_boq_m9.py", ROOT / "engine" / "source" / "arch_measure.py"):
        assert "skirting_deduction_audit" not in f.read_text(encoding="utf-8")


# ------------------------------------------------------------------------------------------------ SV-A / SV-B / SV-C
SV_A_HAND = {   # room name -> (gross, listed door / passage, net, unlisted window threshold), see the module docstring
    "Living / saloon": (28.0, 2.8, 23.7, 1.5), "Bedroom": (19.2, 1.7, 16.0, 1.5),
    "Kitchen": (13.8, 0.9, 11.7, 1.2), "Bathroom / W.C.": (13.6, 0.8, 12.2, 0.6)}


def _villa(tmp_path, vid):
    from tools import urban_boq_m9 as M9
    from tools.synth_villa import build as B
    from tools.synth_villa import villas as V
    p = tmp_path / f"{vid}.dxf"
    B.write_villa(vid, p, **V.FIRST_RUN[vid])
    facts = json.loads((ROOT / "research" / "urban_m9_s2" / "SYNTHETIC_FACTS_S2.json").read_text(encoding="utf-8"))
    try:
        room, arch, _e = M9.arch_compute(str(p), method="ARCH_TAKEOFF_V2.12", facts=facts)
    except M9.CompletenessFailed as ex:
        room, arch = ex.room_boq, ex.arch
    return room["lines"], arch["rooms"]


def test_sv_a_every_line_traced_to_its_window_by_hand(tmp_path):
    pytest.importorskip("ezdxf")
    lines, rooms = _villa(tmp_path, "SV-A")
    res = A.audit(lines, rooms)
    recs = {r["room_name_en"]: r for r in res["records"]}
    assert set(recs) == set(SV_A_HAND)
    for name, (g, d, n, u) in SV_A_HAND.items():
        r = recs[name]
        assert (r["gross_lm"], r["listed_deductions_lm"], r["net_lm"]) == pytest.approx((g, d, n), abs=1e-4), name
        assert r["reason"] == "SKIRTING_UNEXPLAINED" and r["unexplained_lm"] == pytest.approx(u, abs=1e-4), name
        assert r["candidate"]["matches"] and r["candidate"]["complete"] and r["proposed_listing"]["readds"], name
    assert res["summary"]["unexplained_lm"] == pytest.approx(4.8, abs=1e-4)      # 1.5 + 1.5 + 1.2 + 0.6


@pytest.mark.parametrize("vid, n_held, total", [("SV-B", 6, 10.2), ("SV-C", 4, 5.6)])
def test_mirrored_metric_and_turned_villas_every_difference_explained(tmp_path, vid, n_held, total):
    # SV-B: metres, Arabic layer names, mirrored; SV-C: turned 37 degrees. Window widths per room from
    # tools/synth_villa/villas.py: SV-B GF majlis 2.0, living 2.0, W.C. 0.6; 1F bedroom 1.5, master 1.5 + 2.0, bath 0.6
    # = 10.2 (the stair windows 1.5 / 1.0 sit on a BLOCKED stair-hall line); SV-C living 2.0, bedroom 1.5, kitchen 1.5,
    # bath 0.6 = 5.6 (the unlabelled dining room's 1.5 has no skirting line: it is HELD by the room census)
    pytest.importorskip("ezdxf")
    lines, rooms = _villa(tmp_path, vid)
    s = A.audit(lines, rooms)["summary"]
    assert s["unexplained_lines"] == n_held and s["unmatched_line_ids"] == []
    assert s["unexplained_lm"] == pytest.approx(total, abs=1e-4)
    assert s["explained_by_components"]["lm"] == pytest.approx(total, abs=1e-4)
