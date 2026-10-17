"""ALSENAN ROUND 5 - architectural BOQ truth engine.

1. KNOWN-ANSWER fixtures (15): expected values are hand-derived in the test (never produced by the code under test).
2. MUTATIONS (16): each corrupts one thing and must be caught by a named check - on a synthetic case AND, where the
   object exists, on a copy of the frozen Round-5 registers.
3. GATES A01-A12 on the frozen registers, freeze integrity, benchmark firewall, rebar untouched.
"""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

import pytest

from engine.source import arch_quantity_truth as AQ
from engine.source import planar_shadow_topology as PT

ROOT = Path(__file__).resolve().parents[2]
R5 = ROOT / "research" / "alsenan_arch_truth_05"
REGS = R5 / "registers"
VC, LB, PROV, BLK, NIS = AQ.VC, AQ.LB, AQ.PROV, AQ.BLK, AQ.NIS


def _reg(n):
    return json.loads((REGS / f"{n}.json").read_text())


def rect(x0, y0, x1, y1, tag):
    return [(x0, y0, x1, y0, tag + "s"), (x1, y0, x1, y1, tag + "e"), (x1, y1, x0, y1, tag + "n"), (x0, y1, x0, y0, tag + "w")]


# =============================================================================================== 1. known answers
def test_ka01_rectangular_dry_room():
    r = PT.build(rect(0, 0, 4000, 3000, "r"))
    assert len(r["faces"]) == 1
    f = r["faces"][0]
    assert f["net_area_m2"] == pytest.approx(12.0) and f["perimeter_m"] == pytest.approx(14.0)
    sk = AQ.skirting_path([{"kind": "WALL", "length_m": 4.0}, {"kind": "WALL", "length_m": 3.0},
                           {"kind": "WALL", "length_m": 4.0}, {"kind": "WALL", "length_m": 2.1},
                           {"kind": "DOOR", "length_m": 0.9}])
    assert sk["included_m"] == pytest.approx(13.1) and sk["state"] == VC
    assert sk["excluded_m_by_reason"] == {"door opening (doors excluded)": pytest.approx(0.9)}


def test_ka02_wet_room():
    edges = [{"kind": "WALL", "length_m": 2.0}, {"kind": "WALL", "length_m": 2.5}, {"kind": "WALL", "length_m": 2.0},
             {"kind": "WALL", "length_m": 1.7}, {"kind": "DOOR", "length_m": 0.8}]
    wp = AQ.waterproofing(floor_m2=2.0 * 2.5, edges=edges)
    assert wp["floor_membrane_m2"] == pytest.approx(5.0) and wp["upturn_path_m"] == pytest.approx(9.0)
    assert wp["upturn_area_reference_m2"] == pytest.approx(1.35) and wp["door_crossings_deducted"] is False
    t = AQ.wall_tile(face_m=8.2, height_m=2.8, height_state=VC,
                     openings=[{"id": "W", "width_m": 0.6, "width_state": VC, "height_m": 0.6, "height_state": VC}])
    assert t["gross_m2"] == pytest.approx(22.96) and t["opening_deduction_m2"] == pytest.approx(0.36)
    assert t["reveal_addition_m2"] == pytest.approx(0.45) and t["net_m2"] == pytest.approx(23.05)
    sk = AQ.skirting_path(edges, region_wet_full_tile=True)
    assert sk["included_m"] == 0.0 and sk["state"] == NIS


def test_ka03_open_plan_two_semantic_zones():
    segs = rect(0, 0, 6000, 4000, "o") + [(2000, 0, 2000, 4000, "thin")]
    faces = sorted(f["net_area_m2"] for f in PT.build(segs)["faces"])
    assert faces == [pytest.approx(8.0), pytest.approx(16.0)]
    out = AQ.assign_split([{"id": "a", "area_m2": 8.0, "classes": ["SERVICE"]}, {"id": "b", "area_m2": 16.0, "classes": ["DRY"]}])
    assert [(o["cls"], o["state"]) for o in out] == [("SERVICE", PROV), ("DRY", PROV)]
    whole = AQ.assign_split([{"id": "z", "area_m2": 24.0, "classes": ["SERVICE", "DRY"]}])
    assert whole[0]["cls"] == "MIXED_UNRESOLVED" and whole[0]["state"] == BLK


def test_ka04_orphan_wet_label():
    segs = [(0, 0, 3000, 0, "s"), (3000, 0, 3000, 2000, "e"), (0, 2000, 0, 0, "w"),
            (3000, 2000, 1950, 2000, "n1"), (1050, 2000, 0, 2000, "n2")]           # 900 mm gap in the north wall
    assert PT.build(segs)["faces"] == []
    br = PT.bridge_gaps(segs, min_gap=300, max_gap=3600)
    assert len(br) == 1
    f = PT.build(segs + br)["faces"]
    assert len(f) == 1 and f[0]["net_area_m2"] == pytest.approx(6.0)
    assert AQ.orphan_outcome(in_route_a_space=False, in_plate=True, recovered=True) == "RECOVERED_PHYSICAL_REGION"
    assert AQ.orphan_outcome(in_route_a_space=False, in_plate=True, recovered=False) == "BLOCKED_TOPOLOGY"
    assert AQ.orphan_outcome(in_route_a_space=False, in_plate=False, recovered=False) == "NOT_IN_SCOPE_EXTERNAL"


def test_ka05_150_masonry_wall_with_door():
    segs = [("a1", (0, 0), (1500, 0)), ("a2", (2400, 0), (4000, 0)),
            ("b1", (0, 150), (1500, 150)), ("b2", (2400, 150), (4000, 150))]
    pcs = AQ.pair_wall_faces(segs)
    assert all(p["partner"] is not None and p["width"] == pytest.approx(150.0) for p in pcs)
    assert sum(p["length"] for p in pcs) / 2 == pytest.approx(3100.0)              # centreline 3.10 m
    cls, auth, _ = AQ.wall_class(width_mm=150, paired=True, on_wall_layer=True, rc_overlap=False, structural_checked=True)
    assert cls == "MASONRY_150" and auth
    br = PT.bridge_gaps([(a[0], a[1], b[0], b[1], s) for s, a, b in segs], min_gap=300, max_gap=3600)
    assert len(br) == 2 and all(abs(((x1 - x0) ** 2 + (y1 - y0) ** 2) ** 0.5 - 900) < 1e-6 for x0, y0, x1, y1, _ in br)
    admitted = {"a1": 1.5, "a2": 1.6, "b1": 1.5, "b2": 1.6, "d1": 0.9, "d2": 0.9}
    pieces = [{"piece_id": k, "parent": k, "length_m": v, "class": "MASONRY_150" if k[0] != "d" else "DOOR_OPENING"}
              for k, v in admitted.items()]
    chk = AQ.ledger_check(admitted, pieces)
    assert chk["violations"] == [] and chk["unaccounted_m"] == pytest.approx(0.0)


def test_ka06_200_masonry_wall_with_window():
    a = AQ.blockwork_area(length_m=5.0 - 1.2, height_m=3.0, height_state=VC, material_state=VC)
    assert a["net_m2"] == pytest.approx(11.4)
    m = AQ.masonry_around_opening(width_m=1.2, wall_h_m=3.0, opening_h_m=1.0, lintel_m=0.2, sill_m=0.9)
    assert m["above_m2"] == pytest.approx(1.2 * 0.9) and m["below_m2"] == pytest.approx(1.2 * 0.9)
    assert m["total_m2"] == pytest.approx(2.16)                                       # 1.2 x (3.0 - 1.0 - 0.2)
    assert AQ.opening_area(width_m=1.2, width_state=VC, height_m=1.0, height_state=VC)["area_m2"] == pytest.approx(1.2)


def test_ka07_rc_column_interrupting_masonry():
    a = AQ.blockwork_area(length_m=5.0, height_m=3.0, height_state=VC, material_state=VC, rc_overlap_m=0.3)
    assert a["net_m2"] == pytest.approx(14.1)
    assert AQ.wall_class(width_mm=200, paired=True, on_wall_layer=True, rc_overlap=True,
                         structural_checked=True)[0] == "RC_COLUMN_INTERFACE"


def test_ka08_open_passage():
    edges = [{"kind": "WALL", "length_m": 3.0}, {"kind": "WALL", "length_m": 3.0}, {"kind": "WALL", "length_m": 2.0},
             {"kind": "OPEN_PASSAGE", "length_m": 1.0}]
    sk = AQ.skirting_path(edges)
    assert sk["included_m"] == pytest.approx(8.0) and sk["excluded_m_by_reason"]["open passage"] == pytest.approx(1.0)
    assert AQ.waterproofing(floor_m2=4.5, edges=edges)["upturn_path_m"] == pytest.approx(9.0)


def test_ka09_hidden_skirting_path():
    edges = [{"kind": "WALL", "length_m": 4.0}, {"kind": "WALL", "length_m": 3.0}, {"kind": "WALL", "length_m": 1.4},
             {"kind": "WINDOW", "length_m": 1.2}, {"kind": "WALL", "length_m": 1.4}, {"kind": "WALL", "length_m": 2.1},
             {"kind": "DOOR", "length_m": 0.9}]
    sk = AQ.skirting_path(edges)
    assert sk["included_m"] == pytest.approx(13.1) and sk["path_total_m"] == pytest.approx(14.0)
    assert sum(sk["excluded_m_by_reason"].values()) == pytest.approx(0.9)


def test_ka10_void_railing_boundary():
    edges = [{"kind": "WALL", "length_m": 5.0}, {"kind": "WALL", "length_m": 4.0}, {"kind": "VOID_EDGE", "length_m": 3.0},
             {"kind": "WALL", "length_m": 2.0}]
    sk = AQ.skirting_path(edges)
    assert sk["included_m"] == pytest.approx(11.0)
    assert sk["excluded_m_by_reason"]["void edge / railing (no wall)"] == pytest.approx(3.0)
    assert AQ.skirting_check(sk["segments"]) == []


def test_ka11_wall_tile_with_reveals():
    t = AQ.wall_tile(face_m=6.0, height_m=2.7, height_state=VC,
                     openings=[{"id": "W1", "width_m": 1.0, "width_state": VC, "height_m": 1.2, "height_state": VC}])
    assert (t["gross_m2"], t["opening_deduction_m2"], t["reveal_addition_m2"], t["net_m2"]) == \
        (pytest.approx(16.2), pytest.approx(1.2), pytest.approx(0.85), pytest.approx(15.85))
    assert AQ.reveal_area(width_m=1.0, height_m=1.2) == pytest.approx(0.25 * (2 * 1.2 + 1.0))    # no sill


def test_ka12_plaster_vs_paint_different_heights():
    door = [{"id": "D", "width_m": 0.9, "width_state": VC, "height_m": 2.1, "height_state": VC}]
    pp = AQ.plaster_paint(face_m=10.0, plaster_h=3.6, plaster_state=VC, paint_h=3.2, paint_state=PROV, openings=door)
    assert pp["plaster"]["net_m2"] == pytest.approx(36.0 - 1.89 + 1.275) and pp["plaster"]["state"] == VC
    assert pp["paint"]["net_m2"] == pytest.approx(32.0 - 1.89 + 1.275) and pp["paint"]["state"] == PROV
    tiled = AQ.plaster_paint(face_m=10.0, plaster_h=3.6, plaster_state=VC, paint_h=3.2, paint_state=VC, wet_tiled=True)
    assert tiled["plaster"]["state"] == NIS and tiled["paint"]["state"] == NIS


def test_ka13_waterproofing_upturn_crossing_door():
    edges = [{"kind": "WALL", "length_m": 2.0}] * 3 + [{"kind": "WALL", "length_m": 1.2}, {"kind": "DOOR", "length_m": 0.8}]
    wp = AQ.waterproofing(floor_m2=4.0, edges=edges)
    assert wp["upturn_path_m"] == pytest.approx(8.0) and wp["door_crossings_m"] == pytest.approx(0.8)
    assert wp["upturn_area_reference_m2"] == pytest.approx(1.2)


def test_ka14_glazed_door_with_unknown_height():
    h = AQ.opening_height([{"authority": "BUDGET", "height_m": 2.2}], kind="GLAZED_DOOR_CANDIDATE")
    assert h["state"] == BLK and h["height_m"] is None
    assert AQ.opening_area(width_m=2.4, width_state=VC, height_m=None, height_state=BLK)["area_m2"] is None
    assert AQ.opening_height([{"authority": "URBAN_FALLBACK", "height_m": 1.2}], kind="WINDOW")["state"] == BLK
    d = AQ.opening_height([{"authority": "BUDGET", "height_m": 2.2}], kind="DOOR")
    assert d["state"] == PROV and d["height_m"] == 2.2


def test_ka15_ceiling_with_open_to_below_void():
    c = AQ.ceiling_area(area_m2=20.0, region_class="DRY", covered_state=VC, double_height_m2=6.0)
    assert c["area_m2"] == pytest.approx(14.0) and c["state"] == VC
    v = AQ.ceiling_area(area_m2=16.0, region_class="VOID", covered_state=VC)
    assert v["area_m2"] == 0.0 and v["state"] == NIS


def test_floor_conservation_known_answer():
    parts = [{"id": "r", "component": "INTERNAL_SPACE", "area_m2": 60.0}, {"id": "w", "component": "WALL_BAND", "area_m2": 10.0},
             {"id": "c", "component": "COLUMN", "area_m2": 5.0}, {"id": "u", "component": "UNRESOLVED_BLOCKED", "area_m2": 25.0}]
    assert AQ.floor_conservation(100.0, parts)["violations"] == []


def test_trade_state_never_more_certain_than_dependencies():
    t = AQ.trade_state("SKIRTING", {"dry_region": VC, "boundary_path": VC, "opening_transitions": PROV})
    assert t["state"] == BLK and t["missing"] == ["void_railing_exclusion"]


# =============================================================================================== 2. mutations
def test_mut01_mixed_wash_salon_as_dry():
    assert AQ.region_class_check([{"region_id": "x", "class": "DRY", "label_classes": ["DRY", "WET"]}])
    regs = copy.deepcopy(_reg("TRADE_REGION_REGISTER_V2")["rows"])
    mixed = [r for r in regs if r["class"] == "MIXED_UNRESOLVED"]
    assert mixed and AQ.region_class_check(regs) == []
    mixed[0]["class"] = "DRY"
    assert AQ.region_class_check(regs)


def test_mut02_delete_orphan_wet_label():
    w = _reg("WET_SERVICE_COMPLETENESS_REGISTER")["labels"]
    src = [f"{x['floor']}|{x['occurrence']}" for x in w]
    rec = [{"occurrence": s} for s in src]
    assert AQ.label_conservation(src, rec) == []
    orphan = next(i for i, x in enumerate(w) if x["state"] == "BLOCKED" and x["region"] is None)
    assert AQ.label_conservation(src, rec[:orphan] + rec[orphan + 1:])[0][0] == "LABEL_MISSING"


def test_mut03_drop_ambiguous_wall_segment():
    L = _reg("WALL_SEGMENT_LEDGER_V2")
    pieces = [dict(p) for p in L["pieces"]]
    assert AQ.ledger_check(L["admitted_m"], pieces)["violations"] == []
    i = next(i for i, p in enumerate(pieces) if p["class"] == "AMBIGUOUS_BLOCKED")
    v = AQ.ledger_check(L["admitted_m"], pieces[:i] + pieces[i + 1:])["violations"]
    assert v and v[0][0] == "LENGTH_NOT_CONSERVED"


def test_mut04_masonry_from_thickness_alone():
    assert AQ.wall_class(width_mm=150, paired=True, on_wall_layer=False, rc_overlap=False,
                         structural_checked=True)[0] == "BLOCKED_MATERIAL"
    assert AQ.wall_class(width_mm=200, paired=True, on_wall_layer=True, rc_overlap=False,
                         structural_checked=False)[0] == "BLOCKED_MATERIAL"
    pieces = copy.deepcopy(_reg("WALL_SEGMENT_LEDGER_V2")["pieces"])
    assert AQ.masonry_identity_check(pieces) == []
    amb = next(p for p in pieces if p["class"] == "AMBIGUOUS_BLOCKED")
    amb["class"] = "MASONRY_150"                                  # thickness-only promotion of a single line
    assert AQ.masonry_identity_check(pieces)


def test_mut05_masonry_through_rc_column():
    pieces = copy.deepcopy(_reg("WALL_SEGMENT_LEDGER_V2")["pieces"])
    assert AQ.masonry_rc_check(pieces, lambda p: bool(p.get("rc_at_centre"))) == []
    rc = next(p for p in pieces if p.get("rc_at_centre"))
    rc["class"] = "MASONRY_200"
    assert AQ.masonry_rc_check(pieces, lambda p: bool(p.get("rc_at_centre")))


def test_mut06_blocked_opening_height_produces_area():
    ops = copy.deepcopy(_reg("OPENING_EVIDENCE_REGISTER_V3")["rows"])
    o = next(o for o in ops if o["height"]["state"] == BLK)
    rows = lambda: [{"id": x["id"], "count_state": x["count"]["state"], "area_m2": x["area"]["area_m2"],
                     "width_state": x["width"]["state"], "height_state": x["height"]["state"]} for x in ops]
    assert AQ.cross_trade_check(regions=[], openings=rows(), walls=[], faces=[]) == []
    o["area"]["area_m2"] = 2.0
    assert AQ.cross_trade_check(regions=[], openings=rows(), walls=[], faces=[])[0][0] == \
        "OPENING_AREA_WITHOUT_WIDTH_AND_HEIGHT"


def test_mut07_glazed_door_as_window_without_evidence():
    ops = copy.deepcopy(_reg("OPENING_EVIDENCE_REGISTER_V3")["rows"])
    assert AQ.opening_function_check(ops) == []
    g = next(o for o in ops if o["type"] == "GLAZED_DOOR_CANDIDATE" and "GLAZED_DOOR_CANDIDATE" in o["flags"])
    g["type"] = "WINDOW"
    assert AQ.opening_function_check(ops)


def test_mut08_skirting_along_void_edge():
    rows = copy.deepcopy(_reg("SKIRTING_PATH_REGISTER_V3")["rows"])
    segs = [s for r in rows for s in r["segments"]]
    assert AQ.skirting_check(segs) == []
    v = next(s for s in segs if s["kind"] == "VOID_EDGE")
    v["use"] = "INCLUDED"
    assert AQ.skirting_check(segs)[0][2] == "VOID_EDGE"


def test_mut09_door_width_in_skirting():
    segs = [s for r in copy.deepcopy(_reg("SKIRTING_PATH_REGISTER_V3")["rows"]) for s in r["segments"]]
    d = next(s for s in segs if s["kind"] == "DOOR" and s["use"] == "EXCLUDED")
    d["use"] = "INCLUDED"
    assert AQ.skirting_check(segs)[0][2] == "DOOR"


def test_mut10_omit_waterproofing_for_wet_room():
    reg = {"id": "r", "indoor": True, "internal_area_m2": 4.0, "wet": True,
           "trades": {"FLOOR_FINISH": {"qty": 4.0}, "CEILING": {"qty": 4.0}, "WATERPROOFING": {"qty": 4.0},
                      "WALL_TILE": {"qty": 20.0}}}
    assert AQ.cross_trade_check(regions=[reg], openings=[], walls=[], faces=[]) == []
    del reg["trades"]["WATERPROOFING"]
    assert AQ.cross_trade_check(regions=[reg], openings=[], walls=[], faces=[]) == [("WET_TRADE_MISSING", "r", "WATERPROOFING")]
    wp = {r["region"] for r in _reg("WATERPROOFING_REGISTER_V2")["rows"]}
    wet = {r["region_id"] for r in _reg("TRADE_REGION_REGISTER_V2")["rows"] if r["class"] in ("WET", "SERVICE")}
    assert wet and wet == wp


def test_mut11_paint_a_full_ceramic_wall():
    faces = copy.deepcopy(_reg("PLASTER_PAINT_REGISTER_V2")["faces"])
    f = [{"id": x["id"], "treatments": x.get("treatments")} for x in faces]
    assert AQ.cross_trade_check(regions=[], openings=[], walls=[], faces=f) == []
    t = next(x for x in f if "WALL_TILE_FULL" in x["treatments"])
    t["treatments"] = t["treatments"] + ["PAINT"]
    assert AQ.cross_trade_check(regions=[], openings=[], walls=[], faces=f)[0][0] == "FACE_DOUBLE_TREATED"


def test_mut12_one_global_wall_height():
    faces = copy.deepcopy(_reg("PLASTER_PAINT_REGISTER_V2")["faces"])
    assert AQ.height_consistency(faces) == []
    assert len({(f["interval_m"], f["D_cm"]) for f in faces if f.get("D_cm") is not None}) > 1
    for f in faces:
        if f.get("height_m") is not None:
            f["height_m"] = 3.0
    assert AQ.height_consistency(faces)


def test_mut13_external_garden_in_internal_flooring():
    rows = copy.deepcopy(_reg("FLOOR_FINISH_REGISTER_V2")["rows"])
    assert AQ.internal_floor_check(rows) == []
    g = next(r for r in rows if r["cls"] == "EXTERNAL")
    g["internal"] = True
    assert AQ.internal_floor_check(rows)


def test_mut14_omit_a_physical_space_from_conservation():
    fc = _reg("FLOOR_AREA_CONSERVATION_REGISTER")
    comps = [c for c in fc["components"] if c["floor"] == "GF"]
    plate = fc["floors"]["GF"]["plate_m2"]
    assert AQ.floor_conservation(plate, comps, tol_m2=0.05)["violations"] == []
    big = max(range(len(comps)), key=lambda i: comps[i]["area_m2"])
    assert AQ.floor_conservation(plate, comps[:big] + comps[big + 1:], tol_m2=0.05)["violations"][0][0] == "PLATE_NOT_CONSERVED"


def test_mut15_duplicate_a_room_polygon():
    fc = _reg("FLOOR_AREA_CONSERVATION_REGISTER")
    comps = [c for c in fc["components"] if c["floor"] == "1F"]
    dup = comps + [dict(next(c for c in comps if c["component"] == "INTERNAL_SPACE"))]
    kinds = {v[0] for v in AQ.floor_conservation(fc["floors"]["1F"]["plate_m2"], dup, tol_m2=0.05)["violations"]}
    assert {"DUPLICATE_COMPONENT", "PLATE_NOT_CONSERVED"} <= kinds


def test_mut16_double_count_one_wall_face():
    faces = _reg("PLASTER_PAINT_REGISTER_V2")["faces"]
    assert AQ.face_uniqueness(faces) == []
    assert AQ.face_uniqueness(faces + [faces[0]]) == [("WALL_FACE_DOUBLE_COUNTED", faces[0]["id"])]


# =============================================================================================== 3. gates
def test_A01_every_source_object_terminates():
    c = _reg("ARCHITECTURAL_SOURCE_COVERAGE_REGISTER")
    assert c["unterminated"] == 0 and sum(c["counts_total"].values()) == c["objects_total"] == len(c["objects"])
    assert {o["state"] for o in c["objects"]} <= set(c["states"])
    assert all(d["state"] in c["states"] for d in c["documents"])


def test_A02_floor_plate_conserved():
    fc = _reg("FLOOR_AREA_CONSERVATION_REGISTER")
    for fl, d in fc["floors"].items():
        assert abs(d["conservation"]["unaccounted_m2"]) <= 0.05, fl
        assert d["internal_reconciles"], fl
        assert abs(d["plate_m2"] - d["architect_area_sheet_m2"]) < 6.0, fl        # Route C cross-check
    assert all(r["state"] == "UNRESOLVED_BLOCKED" and r["area_m2"] > 0 for r in fc["residuals"])


def test_A03_wall_ledger_conserved():
    L = _reg("WALL_SEGMENT_LEDGER_V2")
    chk = AQ.ledger_check(L["admitted_m"], L["pieces"])
    assert chk["violations"] == [] and chk["unaccounted_m"] == pytest.approx(0.0, abs=1e-6)
    assert L["ledger_check"]["unaccounted_m"] == pytest.approx(0.0, abs=1e-6)
    assert {p["class"] for p in L["pieces"]} <= set(AQ.WALL_CLASSES)


def test_A04_masonry_never_from_thickness_alone():
    for p in _reg("WALL_SEGMENT_LEDGER_V2")["pieces"]:
        if p["class"] in AQ.MASONRY_CLASSES:
            assert p["paired"] and p["material_authority"], p["piece_id"]
    bl = _reg("BLOCKWORK_LENGTH_REGISTER_V2")["floors"]
    assert all(v["material_state"] == PROV for v in bl.values())


def test_A05_mixed_zone_never_fully_dry():
    regs = _reg("TRADE_REGION_REGISTER_V2")["rows"]
    z04 = [r for r in regs if "67547ed37daadb5a" in r["region_id"]]
    by = {}
    for r in z04:
        for l in r["labels"]:
            by[l] = r["class"]
    assert by["GARDEN"] == "EXTERNAL" and by["PANTRY"] == "SERVICE"
    assert by["SALOON"] == by["Wash"] == "MIXED_UNRESOLVED"
    assert all(r["class"] != "DRY" for r in z04)
    assert AQ.region_class_check(regs) == []
    for r in regs:
        if r["split_face"]:
            assert r["semantic_state"] in (PROV, BLK)


@pytest.mark.xfail(strict=True, reason="GF-Z04 basin lobby (Wash) has no source boundary inside SALOON / RECEPTION / "
                                       "DINING - owner decision (review queue #3)")
def test_GF_Z04_wash_zone_resolved():
    regs = _reg("TRADE_REGION_REGISTER_V2")["rows"]
    assert not any(r["class"] == "MIXED_UNRESOLVED" and r["floor"] == "GF" for r in regs)


def test_A06_orphans_never_deleted():
    o = _reg("ORPHAN_SEMANTIC_LABEL_REGISTER")["rows"]
    outcomes = {"RECOVERED_PHYSICAL_REGION", "LABEL_BELONGS_TO_EXISTING_REGION", "STALE_LABEL", "BLOCKED_TOPOLOGY",
                "SOURCE_CONFLICT", "NOT_IN_SCOPE_EXTERNAL"}
    assert o and all(r["outcome"] in outcomes for r in o)
    got = {(r["floor"], r["text"]): r["outcome"] for r in o}
    assert got[("1F", "BATH")] == "RECOVERED_PHYSICAL_REGION"
    assert got[("1F", "W.C")] == "BLOCKED_TOPOLOGY"
    assert got[("GF", "DRIVER")] == "RECOVERED_PHYSICAL_REGION"


@pytest.mark.xfail(strict=True, reason="1F W.C shares an unclosed opening with the corridor in both routes - no wall is "
                                       "invented")
def test_1F_wc_closed():
    got = {(r["floor"], r["text"]): r["outcome"] for r in _reg("ORPHAN_SEMANTIC_LABEL_REGISTER")["rows"]}
    assert got[("1F", "W.C")] == "RECOVERED_PHYSICAL_REGION"


def test_A07_openings():
    o = _reg("OPENING_EVIDENCE_REGISTER_V3")
    assert len(o["rows"]) == 60 and all(r["count"]["state"] == VC for r in o["rows"])
    for r in o["rows"]:
        if r["area"]["area_m2"] is not None:
            assert r["width"]["state"] != BLK and r["height"]["state"] != BLK
        if r["type"] == "WINDOW":
            assert r["height"]["authority"] not in ("URBAN_FALLBACK", "BUDGET")
    assert o["types"]["GLAZED_DOOR_CANDIDATE"] == 24 and AQ.opening_function_check(o["rows"]) == []


def test_A08_skirting_paths():
    for r in _reg("SKIRTING_PATH_REGISTER_V3")["rows"]:
        assert AQ.skirting_check(r["segments"]) == []
        assert r["included_m"] + r["blocked_m"] + sum(r["excluded_m_by_reason"].values()) == \
            pytest.approx(r["path_total_m"], abs=1e-5)
        if r["cls"] in ("WET", "SERVICE"):
            assert r["included_m"] == 0.0 and r["state"] == NIS


def test_A09_every_wet_region_has_floor_wp_tile():
    wet = {r["region_id"] for r in _reg("TRADE_REGION_REGISTER_V2")["rows"] if r["class"] in ("WET", "SERVICE")}
    for name, key in (("FLOOR_FINISH_REGISTER_V2", "region"), ("WATERPROOFING_REGISTER_V2", "region"),
                      ("WALL_TILE_REGISTER_V2", "region")):
        assert wet <= {r[key] for r in _reg(name)["rows"]}, name
    w = _reg("WET_SERVICE_COMPLETENESS_REGISTER")
    assert w["unaccounted"] == [] and set(w["counts"]) <= {"BOUND", "BLOCKED", "NOT_IN_SCOPE", "STALE_WITH_EVIDENCE"}


def test_A10_no_face_tiled_and_painted():
    f = [{"id": x["id"], "treatments": x.get("treatments")} for x in _reg("PLASTER_PAINT_REGISTER_V2")["faces"]]
    assert AQ.cross_trade_check(regions=[], openings=[], walls=[], faces=f) == []


def test_A11_external_never_internal():
    rows = _reg("FLOOR_FINISH_REGISTER_V2")["rows"]
    assert AQ.internal_floor_check(rows) == []
    assert any(r["cls"] == "EXTERNAL" and not r["internal"] for r in rows)


def test_A12_route_b_is_shadow_only():
    t = _reg("TOPOLOGY_SHADOW_COMPARISON")
    assert t["rows"] and set(t["summary"]) == {"GF", "1F", "2F"}
    for r in _reg("TRADE_REGION_REGISTER_V2")["rows"]:
        assert r["host_kind"] in ("ROUTE_A_SITE", "RECOVERED")
    for r in _reg("PHYSICAL_SPACE_REGISTER")["rows"]:
        assert r["route"] in ("A", "B_RECOVERED")


def test_conservation_register_and_provenance():
    c = _reg("ARCHITECTURAL_QUANTITY_CONSERVATION_REGISTER")
    assert c["pass"] and c["violations"] == [] and c["silent_disappearances"] == 0
    assert all(v["pass"] for v in c["mutation_proof_checks"].values())
    assert c["provenance"]["coverage_pct"] == 100.0


def test_scorecard_has_no_aggregate_accuracy():
    m = _reg("ARCH_ACCURACY_SCORECARD_V3")["metrics"]
    assert "accuracy_pct" not in m and "overall" not in " ".join(m)
    assert m["wall_length_accounting_pct"] == 100.0 and m["opening_count_coverage_pct"] == 100.0


def test_index_hashes_hold_and_twice_identical():
    idx = json.loads((REGS / "INDEX.json").read_text())
    assert idx["built_twice_identical"] is True and idx["frozen_before_benchmark"] is True
    for n, h in idx["files"].items():
        assert hashlib.sha256((REGS / f"{n}.json").read_bytes()).hexdigest() == h, n


def test_post_freeze_benchmark_after_freeze():
    out = json.loads((R5 / "POST_FREEZE_ARCH_BENCHMARK.json").read_text())
    assert out["frozen_index_sha256"] == hashlib.sha256((REGS / "INDEX.json").read_bytes()).hexdigest()
    assert out["use"] == "FINDING_ONLY"
    allowed = {"AGREES", "ENGINE_HIGH", "ENGINE_LOW", "DIFFERENT_SCOPE", "DIFFERENT_METHOD", "HUMAN_FORMULA_ERROR",
               "UNRESOLVED"}
    assert all(r["classification"] in allowed for r in out["rows"])


@pytest.mark.parametrize("path", ["research/external_engine_lab/alsenan_arch_r5.py",
                                  "research/alsenan_arch_truth_05/build_arch_r5.py",
                                  "engine/source/arch_quantity_truth.py", "engine/source/planar_shadow_topology.py"])
def test_benchmark_firewall(path):
    src = (ROOT / path).read_text()
    for banned in ("registers_v3b_eval", "BENCHMARK_EVALUATION", "registers_b1", ".xlsx", "409.58", "72.01", "433.83",
                   "freelancer", "44.19"):
        assert banned not in src, (path, banned)


def test_rebar_untouched():
    for d in ("research/alsenan_rebar_truth_03/registers", "research/alsenan_rebar_source_exhaustion_04/registers"):
        idx = json.loads((ROOT / d / "INDEX.json").read_text())
        files = idx.get("files") or idx.get("registers")
        for n, h in files.items():
            assert hashlib.sha256((ROOT / d / f"{n}.json").read_bytes()).hexdigest() == h, (d, n)
    for path in ("research/external_engine_lab/alsenan_arch_r5.py", "research/alsenan_arch_truth_05/build_arch_r5.py"):
        src = (ROOT / path).read_text()
        assert "rebar" not in src.replace("Rebar is not touched", "").replace("Rebar registers are not read or written", "")
