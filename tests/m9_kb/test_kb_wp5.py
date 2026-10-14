"""Phase 2B-1 WP-5: the remaining cases of the owner's QA list under ARCH_TAKEOFF_V2.3 - conflicting opening
dimensions, a door symbol with no wall gap, a wall gap with no door symbol, millimetre and metre drawings, a balcony
(exterior space) door and its waterproofing, and the failing-before / passing-after regressions of the material
corrections found on the reference plan (several strip faces of one opening, a project INTERIOR decision)."""

from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

import kb_fixtures as KF                                      # noqa: E402
from engine.source import arch_measure as AM                  # noqa: E402
from engine.source import door_model as DM                    # noqa: E402
from engine.source import door_standards as DSTD              # noqa: E402
from engine.source import knowledge as K                      # noqa: E402
from engine.source import owner_finish_scope as OFS           # noqa: E402
from tools import arch_synth as AS                            # noqa: E402

V22, V23 = "ARCH_TAKEOFF_V2.2", "ARCH_TAKEOFF_V2.3"
CTX = {"project_id": "P", "revision_set_sha256": "0" * 64, "documents": []}


def test_conflicting_opening_dimensions_keep_both_values_and_hold_the_door():
    """the external door has a 0.90 m opening and a 1.00 m frame (F-18): the CAD opening (0.90) is the wall-opening
    measurement, the frame width is kept beside it, the door is held (not in the AS_DRAWN or OWNER_REQUIRED totals)
    and the owner standard is still stated for it (1.10)."""
    run = KF.door_floor()
    held = [e for e in run["model"]["elements"] if e.get("hold")]
    assert len(held) == 1
    r = KF.row_of(run, held[0])
    assert r["view"] == "UNRESOLVED" and any(f.startswith("WIDTH_HELD") for f in r["flags"])
    assert r["as_drawn"]["cad_wall_opening_m"] == pytest.approx(0.90)
    assert r["as_drawn"]["frame_width_m"] == pytest.approx(1.00)
    assert r["owner_required"]["owner_required_wall_opening_m"] == pytest.approx(1.10)
    assert run["scenarios"]["views"]["UNRESOLVED"].get("EXTERNAL_ALUMINIUM / CONFIRMED") == 1
    assert "EXTERNAL_ALUMINIUM" not in run["scenarios"]["views"]["OWNER_REQUIRED"]


def test_a_door_symbol_with_no_wall_gap_is_never_measured():
    """a swing that closes no wall gap has no CAD opening: no width, no area, never in a door total."""
    el = KF.door("D-X", "A", "B", state=DM.UNRESOLVED)
    el.update(structural_opening_width_m=None, released=False)
    out = DSTD.door_scenarios({"elements": [el]}, None, openings=[], rooms=[])
    (r,) = out["rows"]
    assert r["owner_required"]["state"] == "BLOCKED" and r["as_drawn"]["wall_opening_area"]["m2"] is None
    assert out["views"]["AS_DRAWN"] == {} and out["views"]["UNRESOLVED"] == {"INTERNAL_PVC / UNRESOLVED": 1}
    assert DSTD.required_opening(DSTD.INTERNAL, None)["state"] == "BLOCKED"


def test_a_wall_gap_without_a_door_symbol_is_a_passage_not_a_door(tmp_path):
    """a 1.20 m gap with no door symbol is a doorless passage: no door element, no door line, no owner door
    standard; its strip is floor porcelain and its jambs are skirted (both rooms dry)."""
    room, arch = KF.drawing_run(KF.dry_passage(tmp_path / "p.dxf"), V23)
    assert arch["doors"]["elements"] == [] and arch["door_scenarios"]["rows"] == []
    assert not [ln for ln in room["lines"] if ln["item_code"].startswith("DOOR.")]
    assert [o["kind"] for o in arch["openings"]] == ["PASSAGE"]
    (strip,) = [ln for ln in room["lines"] if ln.get("physical_element") == "doorway strip"]
    assert strip["measured_net"] == pytest.approx(1.20 * 0.20)


def test_millimetre_and_metre_drawings_give_the_same_v2_3_result(tmp_path):
    """the villa in millimetres and the same villa scaled to metres ($INSUNITS 6): the same lines, door views and
    question groups."""
    mm = tmp_path / "v_mm.dxf"
    AS.villa(mm)
    m = KF.metre_copy(mm, tmp_path / "v_m.dxf")
    a, b = KF.drawing_run(mm, V23), KF.drawing_run(m, V23)
    prof = lambda r: Counter((ln["item_code"], ln.get("physical_element") if "STRIP" in (                     # noqa
        ln["location"].get("room_id") or "") else "-", ln["evidence_state"], None if ln["measured_net"] is None
        else round(ln["measured_net"], 4)) for ln in r[0]["lines"])
    assert prof(a) == prof(b)
    assert a[1]["door_scenarios"]["views"] == b[1]["door_scenarios"]["views"]
    assert a[1]["owner_questions"]["summary"] == b[1]["owner_questions"]["summary"]


def test_a_balcony_door_is_aluminium_and_the_balcony_is_waterproofed(tmp_path):
    """a balcony is an exterior space: the door to it is external aluminium (1.00 / 1.10) and never a main-entrance
    candidate, the balcony floor gets PROVISIONAL waterproofing over its drawn area, its upturn is a specification
    request (B); V2.2 had neither."""
    p = KF.balcony(tmp_path / "b.dxf")
    room, arch = KF.drawing_run(p, V23, layer_roles=KF.ROLES)
    (d,) = arch["doors"]["elements"]
    assert d["boq_class"] == DM.ALU
    (r,) = arch["door_scenarios"]["rows"]
    assert r["category"] == DSTD.EXTERNAL and r["owner_required"]["owner_required_wall_opening_m"] == pytest.approx(1.10)
    wp = [ln for ln in room["lines"] if ln.get("physical_element") == "exterior wp_floor"]
    assert len(wp) == 1 and wp[0]["evidence_state"] == "PROVISIONAL" and wp[0]["measured_net"] == pytest.approx(8.0)
    b = {g["group"]: g["instances"] for g in arch["owner_questions"]["by_category"]["B_MISSING_DRAWING_EVIDENCE"]}
    assert b.get("WATERPROOFING_SPECIFICATION") == 1
    v22, a22 = KF.drawing_run(p, V22, layer_roles=KF.ROLES)
    assert not [ln for ln in v22["lines"] if ln.get("physical_element") == "exterior wp_floor"]
    # before: the only external door of the entrance floor opens from a living room, so V2.2 withheld it as a
    # main-entrance candidate; a balcony / roof door is never the main entrance (V2.3)
    assert [e["boq_class"] for e in a22["doors"]["elements"]] == ["MAIN_ENTRANCE_CANDIDATE"]
    assert d["released"] and arch["doors"]["main_entrance"]["candidates"] == []


def _strip(sid, oid, area, verified=True):
    return {"strip_id": sid, "floor": "GF", "area_m2": area, "opening_ids": [oid], "opening_kinds": ["PASSAGE"],
            "door_closures": [], "class": "THRESHOLD", "geometry_verified": verified,
            "geometry": {"opening_width_m": 3.0, "depth_m": 0.2}, "question": "THRESHOLD_FINISH_NOT_ESTABLISHED"}


def test_several_strip_faces_of_one_opening_make_one_line():
    """failing before (reference plan): three faces of one wide passage made three doorway-strip lines with one line
    id, counted twice in the ledger. Now one line per opening, the faces summed and named; an opening with an
    unverified face stays whole in the V2 strip register."""
    rooms = [{"room_id": "A", "doors": [], "passages": ["OP-1", "OP-2"], "class": "ROOM", "codes": ["LIVING"],
              "kind": "DRY", "name_en": "a"},
             {"room_id": "B", "doors": [], "passages": ["OP-1", "OP-2"], "class": "ROOM", "codes": ["DINING"],
              "kind": "DRY", "name_en": "b"}]
    strips = [_strip("S1", "OP-1", 0.2), _strip("S2", "OP-1", 0.3), _strip("S3", "OP-1", 0.1),
              _strip("S4", "OP-2", 0.2), _strip("S5", "OP-2", 0.1, verified=False)]
    lines, _unres, rest = OFS.threshold_lines(CTX, strips, rooms, "GF", line=AM._line)
    (ln,) = lines
    assert ln["measured_net"] == pytest.approx(0.6) and ln["calculation"]["inputs"]["strips"] == ["S1", "S2", "S3"]
    assert sorted(s["strip_id"] for s in rest) == ["S4", "S5"]
    assert all(s["question"].startswith("THRESHOLD_STRIP_NOT_ATTRIBUTED") for s in rest)
    assert K.classify_question({"reason": rest[0]["question"]})["category"] == "E_ENGINEERING_DEFECT"


def test_a_door_closure_strip_asks_for_the_door_not_the_finish():
    """a strip at a door symbol with no band opening: the finish is UP-THR-001's; what is missing is the door (B)."""
    s = dict(_strip("S9", "OP-9", 0.2), opening_ids=[], opening_kinds=[], door_closures=["CLOSURE|D1|D2"])
    _l, _u, (rest,) = OFS.threshold_lines(CTX, [s], [], "GF", line=AM._line)
    q = K.classify_question({"reason": rest["question"]})
    assert rest["question"].startswith("THRESHOLD_OF_PROVISIONAL_DOOR") and q["category"] == "B_MISSING_DRAWING_EVIDENCE"
