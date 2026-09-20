"""PA05 regression tests for the generic ingestion package (engine.ingest).

Synthetic drawings prove the engine; P7757 enters only as input data
(tests/data/p7757_pa05_expectations.json and the project configuration)
and its tests are skipped when the sources are not on disk.
"""

from __future__ import annotations

import json
import math
import random
from pathlib import Path
from types import SimpleNamespace

import pytest

from engine.ingest import curves, dimensions as D, faces as F, gates as G, ids, measurement_regions as M, opening_sites as O, owner_inputs as OI
from engine.ingest import rules as R, sheet_roles as SR, spaces as S, status as ST, units as U, views as V

EXP = json.loads((Path(__file__).parent / "data" / "p7757_pa05_expectations.json").read_text("utf-8"))
ENGINE_FILES = sorted(str(p) for p in Path("engine/ingest").glob("*.py"))


# ------------------------------------------------------------------ synthetic primitives
def seg(oid, layer, a, b, handle=None):
    return SimpleNamespace(kind="SEGMENT", object_id=oid, x1=a[0], y1=a[1], x2=b[0], y2=b[1], cx=None, cy=None, radius=None, start_angle=None, end_angle=None,
                           provenance=SimpleNamespace(layer=layer, handle=handle or oid, entity_type="LINE"))


def arc(oid, layer, c, r, a0, a1, handle=None):
    return SimpleNamespace(kind="ARC", object_id=oid, x1=None, y1=None, x2=None, y2=None, cx=c[0], cy=c[1], radius=r, start_angle=a0, end_angle=a1,
                           provenance=SimpleNamespace(layer=layer, handle=handle or oid, entity_type="ARC"))


def dim(handle, a, b, value, etype="21", text=""):
    return SimpleNamespace(x1=a[0], y1=a[1], x2=b[0], y2=b[1], geometry_mm=value, display_value=str(int(round(value))), user_text=text,
                           provenance=SimpleNamespace(layer="4", handle=handle, entity_type=etype))


def two_rooms(with_leaf=True, door_gap=900.0):
    """Two 4 x 3 m rooms side by side, a shared wall with an opening in it (leaf optional); walls are single lines on layer W."""
    W = "W"
    prims = [seg("s", W, (0, 0), (8000, 0)), seg("n", W, (0, 3000), (8000, 3000)), seg("w", W, (0, 0), (0, 3000)), seg("e", W, (8000, 0), (8000, 3000)),
             seg("m1", W, (4000, 0), (4000, 1000)), seg("m2", W, (4000, 1000 + door_gap), (4000, 3000))]
    if with_leaf:
        prims.append(arc("leaf", "D", (4000, 1000), door_gap, 0.0, math.pi / 2))
    return prims


def entity_ids(view_id, prims):
    out = {}
    for p in prims:
        if p.kind == "SEGMENT":
            out[p.object_id] = ids.entity_id(view_id, p.provenance.layer, "SEGMENT", ((p.x1, p.y1), (p.x2, p.y2)), p.provenance.handle)
        else:
            out[p.object_id] = ids.entity_id(view_id, p.provenance.layer, p.kind, (p.cx, p.cy, p.radius, p.start_angle, p.end_angle), p.provenance.handle)
    return out


LAYERS = {"WALL_LAYERS": ["W"], "DOOR_LAYER": "D", "GLAZING_LAYERS": []}
VIEW = {"VIEW_ID": ids.view_id("SH-test", "FLOOR_PLAN", (0, 0, 8000, 3000)), "BBOX_MM": [0, 0, 8000, 3000]}


def pipeline(prims):
    view = dict(VIEW, PRIMITIVES=prims)
    eids = entity_ids(view["VIEW_ID"], prims)
    faces = F.atomic_faces(view["VIEW_ID"], prims, LAYERS["WALL_LAYERS"], eids)
    sites = O.find_sites(view["VIEW_ID"], prims, LAYERS, eids)
    spaces, grid = S.build(view, LAYERS, sites, faces, eids)
    return view, eids, faces, sites, spaces, grid


# ------------------------------------------------------------------ §2 stable ids
def test_stable_ids_same_source_same_ids():
    a = entity_ids("VW-x", two_rooms()); b = entity_ids("VW-x", two_rooms())
    assert a == b


def test_stable_ids_shuffle_and_endpoint_order_invariant():
    prims = two_rooms()
    base = entity_ids("VW-x", prims)
    shuffled = list(prims); random.Random(3).shuffle(shuffled)
    assert entity_ids("VW-x", shuffled) == base
    rev = ids.entity_id("VW-x", "W", "SEGMENT", ((8000, 0), (0, 0)), "s")
    assert rev == base["s"]
    # ids never depend on a handle when the geometry is identical
    assert ids.entity_id("VW-x", "W", "SEGMENT", ((0, 0), (8000, 0)), "other-handle") == base["s"]
    # spaces: same set of PHYSICAL_SPACE_IDs after shuffling the input order
    _, _, _, _, sp1, _ = pipeline(prims)
    _, _, _, _, sp2, _ = pipeline(shuffled)
    assert {s["PHYSICAL_SPACE_ID"] for s in sp1} == {s["PHYSICAL_SPACE_ID"] for s in sp2} and len(sp1) == 2


def test_stable_ids_tolerance_noise_and_material_change():
    base = ids.entity_id("VW-x", "W", "SEGMENT", ((0, 0), (8000, 0)))
    assert ids.entity_id("VW-x", "W", "SEGMENT", ((0.9, -0.9), (8000.8, 0.4))) == base          # inside the 5 mm quantum
    assert ids.entity_id("VW-x", "W", "SEGMENT", ((0, 0), (8050, 0))) != base                    # a real geometry change
    assert ids.entity_id("VW-x", "W2", "SEGMENT", ((0, 0), (8000, 0))) != base                   # a layer (material evidence) change
    assert ids.entity_id("VW-y", "W", "SEGMENT", ((0, 0), (8000, 0))) != base                    # another view


def test_reclassification_keeps_geometry_id():
    _, eids, _, sites_leaf, _, _ = pipeline(two_rooms(True))
    _, _, _, sites_none, _, _ = pipeline(two_rooms(False))
    a = next(s for s in sites_leaf if s["CLASS"] == "CONFIRMED_DOOR_OPENING")
    b = next(s for s in sites_none if s["CLASS"] == "UNRESOLVED_OPENING_SITE")
    assert a["OPENING_SITE_ID"] == b["OPENING_SITE_ID"] and a["CLASS"] != b["CLASS"]


def test_id_constructors_refuse_unknown_kind_and_never_take_indices():
    with pytest.raises(ValueError):
        ids.make_id("ROW", 1)
    assert ids.region_id("VW-x", (1000, 1000), 12.3) == ids.region_id("VW-x", (1100, 950), 12.4)   # anchor quantised to 250 mm, area bucket 0.5


# ------------------------------------------------------------------ §12 units
def test_units_m2_and_lm_never_add():
    with pytest.raises(U.UnitError):
        U.Q(1.0, "m2") + U.Q(1.0, "lm")
    assert (U.Q(1.0, "m") + U.Q(1.0, "lm")).v == 2.0          # lm is a presentation alias of m (PA06 WS10)
    with pytest.raises(U.UnitError):
        U.total([U.Q(1, "m2"), U.Q(2, "lm")])
    assert (U.Q(3.0, "lm") * U.Q(2.5, "m")).u == "m2" and abs((U.Q(3.0, "lm") * U.Q(2.5, "m")).v - 7.5) < 1e-9
    assert (U.Q(2000, "mm") + U.Q(1, "m")).to("m").v == 3.0
    tb = U.totals_by_unit([U.Q(1, "m2"), U.Q(2, "m2"), U.Q(5, "lm")])
    assert (tb["m2"]["VALUE"], tb["m2"]["UNIT"], tb["lm"]["VALUE"], tb["lm"]["UNIT"]) == (3.0, "m2", 5.0, "lm")


# ------------------------------------------------------------------ §11 status
def test_status_model_and_forward_adapters():
    assert ST.from_legacy("OWNER_PARAMETRIC_QUANTITY")["QUANTITY_STATUS"] == "OWNER_ESTABLISHED"
    assert ST.from_legacy("GEOMETRIC_REFERENCE_ONLY")["QUANTITY_STATUS"] == "NOT_APPLICABLE"
    assert ST.from_legacy("something new")["QUANTITY_STATUS"] == "HUMAN_REVIEW"
    assert ST.weakest(["SOURCE_ESTABLISHED", "PROVISIONAL", "OWNER_ESTABLISHED"]) == "PROVISIONAL"
    assert ST.weakest(["SOURCE_ESTABLISHED", "CONFLICT"]) == "CONFLICT"
    assert ST.quantity_status_from("SOURCE_ESTABLISHED", "SOURCE_ESTABLISHED", "NOT_ESTABLISHED", "SOURCE_ESTABLISHED") == "NOT_ESTABLISHED"
    with pytest.raises(ValueError):
        ST.status(QUANTITY_STATUS="ESTABLISHED_QUANTITY")


# ------------------------------------------------------------------ §14 rules
def test_rule_priority_conflict_and_no_automatic_promotion():
    c = [R.rule(rule_id="u1", scope="URBAN_STANDARD", parameter="SKIRTING_H", value=100, unit="mm", source="std", approval={"BY": "x", "DATE": "d", "BASIS": "b"}),
         R.rule(rule_id="p1", scope="PROJECT_OWNER_OVERRIDE", parameter="SKIRTING_H", value=120, unit="mm", project_id="X1", source="owner"),
         R.rule(rule_id="t1", scope="TEMPORARY_DEFAULT", parameter="SKIRTING_H", value=80, unit="mm", source="tmp")]
    assert R.resolve("SKIRTING_H", c, "X1")["RESOLVED"]["RULE_ID"] == "p1"
    assert R.resolve("SKIRTING_H", c, "X2")["RESOLVED"]["RULE_ID"] == "u1"
    c2 = c + [R.rule(rule_id="p2", scope="PROJECT_OWNER_OVERRIDE", parameter="SKIRTING_H", value=150, unit="mm", project_id="X1", source="owner")]
    assert R.resolve("SKIRTING_H", c2, "X1")["STATUS"] == "CONFLICT"
    with pytest.raises(ValueError):
        R.rule(rule_id="bad", scope="URBAN_STANDARD", parameter="Z", value=1, unit="mm", source="s")
    promoted = R.promote_to_standard(c[1], approval={"BY": "owner", "DATE": "2026-09-20", "BASIS": "three projects"})
    assert promoted["SCOPE"] == "URBAN_STANDARD" and c[1]["SCOPE"] == "PROJECT_OWNER_OVERRIDE"
    with pytest.raises(ValueError):
        R.promote_to_standard(c[1], approval={"BY": "owner"})


# ------------------------------------------------------------------ §13 owner inputs
def test_owner_input_recalculates_dependents_only():
    store = OI.ParameterStore("X1")
    facts = {"wall_lm": 10.0, "floor_m2": 20.0}
    rc = OI.Recalculator(facts, store)
    store.set(OI.owner_input(OWNER_INPUT_ID="i1", PROJECT_ID="X1", QUESTION_ID="Q1", PARAMETER_OR_RULE="PLASTER_H", VALUE=3.0, UNIT="m", SCOPE="FF", EFFECTIVE_FROM_REVISION=0,
                             OWNER_CONFIRMED=True, TIMESTAMP="t"))
    rc.register("plaster", lambda f, s: f["wall_lm"] * s.value("PLASTER_H"), ["PLASTER_H"])
    rc.register("floor", lambda f, s: f["floor_m2"], [])
    n = rc.evaluations
    r = rc.apply(OI.owner_input(OWNER_INPUT_ID="i2", PROJECT_ID="X1", QUESTION_ID="Q1", PARAMETER_OR_RULE="PLASTER_H", VALUE=2.5, UNIT="m", SCOPE="FF", EFFECTIVE_FROM_REVISION=0,
                                OWNER_CONFIRMED=True, TIMESTAMP="t2"))
    assert r["RECOMPUTED"] == ["plaster"] and rc.values["plaster"] == 25.0 and rc.values["floor"] == 20.0 and rc.evaluations == n + 1
    assert r["INPUT"]["SUPERSEDES"] == "i1" and store.revision == 2
    with pytest.raises(ValueError):
        OI.owner_input(OWNER_INPUT_ID="i3", PROJECT_ID="X1", QUESTION_ID="Q", PARAMETER_OR_RULE="P", VALUE=1, UNIT="m", SCOPE="S", EFFECTIVE_FROM_REVISION=0, OWNER_CONFIRMED=False, TIMESTAMP="t")


# ------------------------------------------------------------------ §7 curves
def test_curve_engine_synthetic():
    assert abs(curves.arc_length(2.0, math.pi) - 2 * math.pi) < 1e-12
    s = curves.segment_from_chord_rise(2.0, 1.0)
    assert s["KIND"] == "SEMICIRCLE" and abs(s["AREA"] - math.pi / 2) < 1e-9
    seg_ = curves.segment_from_chord_rise(2.0, 0.5)
    assert seg_["KIND"] == "SEGMENT_LESS_THAN_SEMICIRCLE" and 0 < seg_["AREA"] < math.pi / 2 and abs(seg_["R"] - 1.25) < 1e-9
    assert abs(curves.polyarc_length([{"KIND": "LINE", "LENGTH": 1.0}, {"KIND": "ARC", "R": 1.0, "SWEEP_RAD": math.pi}]) - (1 + math.pi)) < 1e-12
    assert abs(curves.offset_arc(1.0, math.pi, 0.5)["ARC_LENGTH"] - 1.5 * math.pi) < 1e-12
    with pytest.raises(ValueError):
        curves.arc_length(-1, 1)


def test_curve_engine_p7757_regression_as_data():
    w = EXP["NW_ARCHED_WINDOW"]
    assert abs(curves.arched_opening(w["WIDTH_M"], w["RECT_HEIGHT_M"])["TOTAL_M2"] - w["EXPECTED_TOTAL_M2"]) < 1e-3
    t = EXP["NW_TOWER_ARCH"]
    a = curves.arched_opening(t["CHORD_M"], t["RECT_HEIGHT_M"], rise=t["RISE_M"])
    assert abs(a["HEAD_M2"] - t["EXPECTED_SEGMENT_M2"]) < 1e-3 and abs(a["TOTAL_M2"] - t["EXPECTED_TOTAL_M2_PA04"]) < 1e-3


# ------------------------------------------------------------------ §4 sheet roles
def test_sheet_role_deterministic_ai_agreement_and_challenge():
    ev = SR.evidence(TITLE_TEXTS=["GROUND FLOOR PLAN"], TEXT_LAYER_AVAILABLE=True)
    assert SR.classify(ev)["FINAL_ROLE"] == "FLOOR_PLAN" and SR.classify(ev)["ROLE_STATUS"] == "DETERMINISTIC"
    ev2 = SR.evidence(TITLE_TEXTS=["NORTH ELEVATION"], TEXT_LAYER_AVAILABLE=True, CUT_HATCH_PRESENT=True)
    assert SR.classify(ev2)["FINAL_ROLE"] == "SECTION_ELEVATION"
    r = SR.classify(SR.evidence(TITLE_TEXTS=["ROOF PLAN"], TEXT_LAYER_AVAILABLE=True), ai_role="FLOOR_PLAN", ai_evidence="looks like a floor")
    assert r["ROLE_STATUS"] == "CHALLENGE" and r["FINAL_ROLE"] == "HUMAN_REVIEW"
    r2 = SR.classify(SR.evidence(TITLE_TEXTS=[], RASTER_ONLY=True), ai_role="SECTION_ELEVATION", ai_evidence="ground storey cut")
    assert r2["ROLE_STATUS"] == "AI_FILLED_UNKNOWN" and r2["DETERMINISTIC_ROLE"] == "UNKNOWN"
    r3 = SR.classify(SR.evidence(TITLE_TEXTS=[], DOOR_ARC_COUNT=12, CLOSED_SPACE_COUNT=9), ai_role="FLOOR_PLAN")
    assert r3["ROLE_STATUS"] == "AGREED"
    with pytest.raises(ValueError):
        SR.classify(ev, ai_role="PLAN")


# ------------------------------------------------------------------ §5 dimension owner
def test_dimension_owner_by_extension_termination():
    prims = two_rooms()
    eids = entity_ids("VW-x", prims)
    dims = [dim("d1", (0, -500), (4000, -500), 4000.0),          # origins 500 mm off the walls: nothing terminates there
            dim("d2", (0, 0), (4000, 0), 4000.0),                # origins exactly on wall endpoints
            dim("d3", (4000, 0), (6500, 0), 2500.0),             # one endpoint, one origin mid-wall (ON_LINE); contiguous with d2 -> same chain
            dim("d4", (0, 6000), (4000, 6000), 4000.0),          # nowhere near any entity
            dim("r1", (0, 0), (0, 0), 900.0, etype="25")]
    rows = D.walk("VW-x", dims, prims, eids)
    by = {r["SOURCE_ENTITY_ID"]: r for r in rows}
    assert by["handle:d2"]["OWNER_STATUS"] == "BOTH_OWNED" and by["handle:d2"]["START_EXTENSION_OWNER"]["TERMINATION"] == "ENDPOINT"
    assert by["handle:d3"]["START_EXTENSION_OWNER"]["TERMINATION"] == "ENDPOINT" and by["handle:d3"]["END_EXTENSION_OWNER"]["TERMINATION"] == "ON_LINE"
    assert by["handle:d3"]["OWNER_STATUS"] == "BOTH_OWNED"
    assert by["handle:d4"]["OWNER_STATUS"] == "UNOWNED" and by["handle:d1"]["OWNER_STATUS"] == "UNOWNED"
    assert by["handle:r1"]["OWNER_STATUS"] == "NOT_SUPPORTED"
    assert by["handle:d2"]["CHAIN_ID"] == by["handle:d3"]["CHAIN_ID"] is not None and by["handle:d2"]["CHAIN_ID"] != by["handle:d4"]["CHAIN_ID"]
    reg = D.register([rows])
    assert reg["COUNTS"]["BY_OWNER_STATUS"] == {"BOTH_OWNED": 2, "ONE_OWNED": 0, "UNOWNED": 2, "NOT_SUPPORTED": 1}


# ------------------------------------------------------------------ §8 opening sites / §9 doorless
def test_opening_site_classes():
    _, _, _, sites, _, _ = pipeline(two_rooms(True))
    assert O.summarise(sites)["CONFIRMED_DOOR_OPENING"] == 1 and all(s["MERGES_ROOMS_AUTOMATICALLY"] is False for s in sites)
    prims = two_rooms(False)
    prims[4] = seg("m1", "W", (4000, 0), (4000, 1900)); prims[5] = seg("m2", "W", (4000, 1950), (4000, 3000))    # 50 mm gap: a CAD junction gap
    _, _, _, s2, _, _ = pipeline(prims)
    assert O.summarise(s2)["CAD_JUNCTION_GAP"] == 1 and O.summarise(s2)["UNRESOLVED_OPENING_SITE"] == 0
    prims[5] = seg("m2", "W", (4000, 2300), (4000, 3000))    # 400 mm: too narrow for a passage
    _, _, _, s3, _, _ = pipeline(prims)
    assert O.summarise(s3)["MATERIAL_CONTINUITY_GAP"] == 1


def test_doorless_opening_site_does_not_merge_rooms():
    _, _, faces, sites, spaces, _ = pipeline(two_rooms(False))
    assert len(spaces) == 2, "a missing leaf must not merge the two rooms"
    site = next(s for s in sites if s["CLASS"] == "UNRESOLVED_OPENING_SITE")
    for sp in spaces:
        rel = [r for r in sp["OPENING_SITES"] if r["OPENING_SITE_ID"] == site["OPENING_SITE_ID"]]
        assert rel and rel[0]["CLASS"] == "UNRESOLVED_OPENING_SITE" and sp["TOPOLOGY_STATUS"] == "CLOSED_WITH_SITES"
        assert 11.0 < sp["AREA_M2"] < 13.0
    # the shared wall's two faces see two different spaces
    shared = [f for f in faces if f["SOURCE"]["HANDLE"] == "m1"]
    assert shared[0]["SIDE_A_SPACE"] != shared[1]["SIDE_A_SPACE"] and None not in (shared[0]["SIDE_A_SPACE"], shared[1]["SIDE_A_SPACE"])
    _, _, _, _, spaces_leaf, _ = pipeline(two_rooms(True))
    assert len(spaces_leaf) == 2


def test_twin_sites_across_wall_face_lines():
    W = "W"
    prims = [seg("s0", W, (0, 0), (8000, 0)), seg("n0", W, (0, 3000), (8000, 3000)), seg("w0", W, (0, 0), (0, 3000)), seg("e0", W, (8000, 0), (8000, 3000)),
             seg("a1", W, (3900, 0), (3900, 1000)), seg("a2", W, (3900, 1900), (3900, 3000)), seg("b1", W, (4100, 0), (4100, 1000)), seg("b2", W, (4100, 1900), (4100, 3000)),
             arc("leaf", "D", (3900, 1000), 900, 0.0, math.pi / 2)]
    _, _, _, sites, _, _ = pipeline(prims)
    doors = [s for s in sites if s["CLASS"] == "CONFIRMED_DOOR_OPENING"]
    assert len(doors) == 2 and doors[0]["TWIN_SITE"] == doors[1]["OPENING_SITE_ID"]


# ------------------------------------------------------------------ §10 reversibility
def test_measurement_closure_reversibility_by_hash():
    _, _, faces, sites, spaces, _ = pipeline(two_rooms(False))
    proof, regions = M.prove_reversible(spaces, faces, sites)
    assert proof["REVERSIBLE"] and proof["PHYSICAL_HASH_BEFORE"] == proof["PHYSICAL_HASH_AFTER"] and proof["CLOSURES"] > 0
    for r in regions:
        for c in r["VIRTUAL_CLOSURES"]:
            assert c["MATERIAL_PRESENT"] is False and c["PHYSICAL_WALL"] is False and c["GEOMETRY_AUTHORITY"] is False and c["REVERSIBLE"] is True
        assert M.remove_closures(r)["PHYSICAL_EDGES"] == next(s for s in spaces if s["PHYSICAL_SPACE_ID"] == r["PHYSICAL_SPACE_ID"])["BOUNDARY_CHAIN"]
    # editing a region's closure list never touches the physical record
    regions[0]["VIRTUAL_CLOSURES"].clear(); regions[0]["PHYSICAL_EDGES"].append("EN-fake")
    assert M.physical_hash(spaces, faces) == proof["PHYSICAL_HASH_BEFORE"]


# ------------------------------------------------------------------ §6 faces
def test_atomic_faces_any_orientation_and_arcs():
    prims = [seg("d", "W", (0, 0), (3000, 4000)), arc("a", "W", (0, 0), 1000, 0.0, math.pi)]
    eids = entity_ids("VW-x", prims)
    faces = F.atomic_faces("VW-x", prims, ["W"], eids)
    assert len(faces) == 4
    d = [f for f in faces if f["ENTITY_ID"] == eids["d"]]
    assert d[0]["GEOMETRY_TYPE"] == "ANGLED" and abs(d[0]["DEVELOPED_LENGTH_MM"] - 5000) < 0.1 and d[0]["NORMAL_DIRECTION"] == [-d[1]["NORMAL_DIRECTION"][0], -d[1]["NORMAL_DIRECTION"][1]]
    a = [f for f in faces if f["ENTITY_ID"] == eids["a"]]
    assert a[0]["GEOMETRY_TYPE"] == "ARC" and abs(a[0]["DEVELOPED_LENGTH_MM"] - math.pi * 1000) < 0.1 and {a[0]["NORMAL_DIRECTION"], a[1]["NORMAL_DIRECTION"]} == {"RADIAL_OUT", "RADIAL_IN"}
    assert all(f["BOUNDING_BOX_USED"] is False for f in faces)


# ------------------------------------------------------------------ §21 gates / §17 harness purity
def test_no_project_constants_in_engine():
    hits = G.scan_engine(ENGINE_FILES)
    assert hits == [], hits


def test_gate_evaluation_shape():
    r = G.evaluate({"ENGINE_PATHS": ENGINE_FILES, "TEST_RESULTS": {"test_stable_ids_x": True}, "HARNESS": {"QA_REPORT": {"CLOSURE_REVERSIBILITY": True}, "METRICS": {"DETERMINISTIC_RUNTIME_S": 1.0}},
                    "BENCHMARK_SCAN": {"CLEAN": True}, "BLIND": {}, "RUNTIME_LIMIT_S": 10})
    assert [g["GATE"] for g in r["GATES"]] == list(G.GATES) and r["ALL_PASS"] is False and "P7757_BLIND_REBUILD_PASS" in r["FAILED"]
    assert next(g for g in r["GATES"] if g["GATE"] == "STABLE_IDS_PASS")["PASS"] is True


def test_views_gap_clustering_and_copy_offsets():
    a = two_rooms(); b = [seg(p.object_id + "'", p.provenance.layer, (p.x1 + 20000, p.y1 + 5), (p.x2 + 20000, p.y2 + 5)) for p in a if p.kind == "SEGMENT"]
    # enough short entities for a view: add a grid of stubs
    a += [seg(f"g{i}", "G", (i * 100, 500), (i * 100 + 50, 500)) for i in range(60)]
    b += [seg(f"h{i}", "G", (20000 + i * 100, 505), (20000 + i * 100 + 50, 505)) for i in range(60)]
    views = V.find_views(a + b, "SH-test", gap_mm=3000, min_entities=50)
    assert len(views) == 2
    off = V.copy_offsets(views, min_matches=10)
    assert off and abs(off[0]["DX_MM"] - 20000) < 1 and abs(off[0]["DY_MM"] - 5) < 1


# ------------------------------------------------------------------ P7757 as input data (skipped without the sources)
@pytest.fixture(scope="module")
def p7757_run():
    try:
        from research.qs_wall_treatment_01.pa05 import config_p7757 as CF
        from engine.ingest import harness as H
    except Exception as e:      # pragma: no cover
        pytest.skip(f"P7757 configuration unavailable: {e}")
    cfg = CF.config()
    if not all(Path(s["PATH"]).exists() for s in cfg["SOURCES"]):
        pytest.skip("P7757 sources not on disk")
    return H.run(cfg)


def test_p7757_sheet_roles_regression(p7757_run):
    rows = p7757_run.registers["SHEET_ROLE_REGISTER"]["SHEETS"]
    arch = {str(r["PAGE"]): r for r in rows if r["PATH"].endswith("P7757_DRAWINGS.pdf")}
    for page, role in EXP["ARCH_PDF_EXPECTED_ROLES"].items():
        assert arch[page]["FINAL_ROLE"] == role and arch[page]["ROLE_STATUS"] == "AI_FILLED_UNKNOWN", (page, arch[page])
    st = {str(r["PAGE"]): r for r in rows if "ST7757" in r["PATH"]}
    for page, role in EXP["ST_PDF_DETERMINISTIC_ROLES"].items():
        assert st[page]["DETERMINISTIC_ROLE"] == role and st[page]["ROLE_STATUS"] == "DETERMINISTIC"
    views = p7757_run.registers["SHEET_ROLE_REGISTER"]["VIEWS"]
    assert sum(1 for v in views if v["FINAL_ROLE"] in ("FLOOR_PLAN", "ROOF_PLAN")) == EXP["MODEL_SPACE_PLAN_VIEWS_EXPECTED"]


def test_p7757_authored_void_dimensions_recovered_with_owners(p7757_run):
    rows = p7757_run.registers["DIMENSION_CHAIN_REGISTER"]["ROWS"]
    for v in EXP["AUTHORED_VOID_DIMENSIONS"]:
        hits = [r for r in rows if r["DISPLAY_TEXT"] == v["DISPLAY_TEXT"] and abs(r["MEASURED_VALUE_MM"] - v["MEASURED_MM"]) < 1.0]
        assert hits and any(r["OWNER_STATUS"] == "BOTH_OWNED" for r in hits), v


def test_p7757_plan_copy_offsets_recovered(p7757_run):
    dx = sorted({round(abs(o["DX_MM"]), 1) for o in p7757_run.copy_offsets})
    for v in EXP["PLAN_COPY_OFFSETS_MM"]:
        assert any(abs(d - v) < 0.1 for d in dx), (v, dx)


def test_p7757_closures_reversible_and_ids_stable(p7757_run):
    qa = p7757_run.registers["QA_REPORT"]
    assert qa["CLOSURE_REVERSIBILITY"] is True and qa["ID_STABILITY_SHUFFLE_AND_REVERSE"] is True
    reg = p7757_run.registers["OPENING_SITE_REGISTER"]
    assert reg["SUMMARY"]["UNRESOLVED_OPENING_SITE"] > 0 and all(r["MERGES_ROOMS_AUTOMATICALLY"] is False for r in reg["ROWS"])
