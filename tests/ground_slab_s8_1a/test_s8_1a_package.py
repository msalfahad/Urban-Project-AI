"""S8.1A (research/alsenan_ground_slab_s8_1a): ground-slab population recovery and cover-authority audit.

The checks below re-derive the package from its own outputs, the frozen S8.1 register and the S1 census, never from
an earlier ground-slab figure:

- S8.1 and every earlier frozen stage still match, and no S8.1 file changed;
- the unfaced face is the one S1 rejected at the strip gate (BL033), and its parts tile it exactly once;
- each part has one lane and one owner: candidate slab cells, the lift-pit opening, pit walls, beam bands, a stair;
- candidate cells get blocked records and no quantity; TT1 and cover stay unresolved;
- the drawn ground-slab domain closes against measured + blocked + excluded + conflicted + unclassified;
- the builder is blind and its rebuild is byte-identical."""

from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
import math
import subprocess
import sys
from collections import Counter
from pathlib import Path

import pytest
from shapely.geometry import Point, Polygon
from shapely.ops import unary_union

from engine.source import delta_release as DR
from engine.source import region_recovery as RR

ROOT = Path(__file__).resolve().parents[2]
PKG = ROOT / "research" / "alsenan_ground_slab_s8_1a"
S81 = ROOT / "research" / "alsenan_ground_slab_s8_1"
S1 = ROOT / "research" / "alsenan_structural_census_s1"
OUTPUTS = ["00_README.md", "01_RECOVERED_LIFT_PIT_REGION.csv", "02_POPULATION_OWNERSHIP_DELTA.csv",
           "03_TT1_ANNOTATION_SCOPE_AUDIT.csv", "04_TT1_INTERPRETATION_REGISTER.csv", "05_COVER_APPLICABILITY_AUDIT.csv",
           "06_S8_1_CORRECTION_LAYER.csv", "07_UNQUANTIFIED_AREA_ACCOUNTING.csv",
           "08_CONFLICT_AND_QUESTION_REGISTER.csv", "09_CONSERVATION_CHECKS.csv", "10_POPULATION_RECONCILIATION.csv",
           "11_FROZEN_MANIFEST_CHECKS.csv", "12_PROVENANCE.jsonl", "13_S8_1A_SUMMARY.json"]
S8_1_M3 = 3.78585231633975
S8_1_KG = 233.69458742837932
FACE = "RB-b5bf2906b114b4a7"


def J(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def rows(p):
    with open(p, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def f(v):
    return float(v)


@pytest.fixture(scope="module")
def mod():
    spec = importlib.util.spec_from_file_location("build_s8_1a", PKG / "build_s8_1a.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


@pytest.fixture(scope="module")
def parts():
    return rows(PKG / "01_RECOVERED_LIFT_PIT_REGION.csv")


@pytest.fixture(scope="module")
def summary():
    return J(PKG / "13_S8_1A_SUMMARY.json")


@pytest.fixture(scope="module")
def s81():
    return {r["ROW_ID"]: r for r in rows(S81 / "01_GROUND_SLAB_POPULATION_AND_ZONE_REGISTER.csv")}


def lane(parts, name):
    return [p for p in parts if p["LANE"] == name]


def poly(p):
    return Polygon(json.loads(p["POLYGON_MM"]))


# ------------------------------------------------------------------ freeze and frozen inputs
def test_freeze_manifest_still_matches():
    m = J(PKG / "14_S8_1A_FREEZE_MANIFEST.json")
    assert m["round"] == "S8_1A" and m["state"] == "FROZEN_NO_QUANTITY_RELEASED" and m["references_read"] == []
    assert set(m["outputs"]) == set(OUTPUTS)
    DR.verify_frozen(PKG / "14_S8_1A_FREEZE_MANIFEST.json", ROOT)


def test_every_frozen_stage_matches_and_s8_1_quantities_are_unchanged(mod, summary):
    assert "S8.1" in mod.MANIFESTS and len(mod.MANIFESTS) == 15
    for name, man in mod.MANIFESTS.items():
        assert DR.verify_frozen(man, ROOT)["manifest_sha256"] == summary["frozen_baselines"][name]
    fr = rows(PKG / "11_FROZEN_MANIFEST_CHECKS.csv")
    assert {r["STAGE"] for r in fr} == set(mod.MANIFESTS) and all(r["RESULT"] == "MATCH" for r in fr)
    s = J(S81 / "10_S8_1_SUMMARY.json")
    assert s["concrete_m3"] == summary["s8_1_quantities"]["concrete_m3"] == S8_1_M3
    assert s["total_kg"] == summary["s8_1_quantities"]["total_kg"] == S8_1_KG
    assert summary["s8_1_quantities"]["changed"] is False
    assert summary["released_quantity"] is None                         # this round releases nothing


# ------------------------------------------------------------------ root cause and the recovered face
def test_the_face_is_the_one_s1_dropped_at_the_strip_gate_on_bl033(parts, summary):
    rc = summary["root_cause"]
    assert rc["face"] == FACE and rc["s1_gate"] == "S1_REJECT_STRIP" and rc["s1_strip_line"] == "BL033"
    assert rc["area_m2"] == pytest.approx(49.074227, abs=1e-9)                       # as S1 prints it
    assert summary["recovered_gross_m2"] == pytest.approx(49.074227, abs=1e-6)       # the exact polygon
    beam07 = [p for p in parts if json.loads(p["EVIDENCE"]).get("s1_beam_line") == "BL033"]
    assert len(beam07) == 1 and poly(beam07[0]).contains(Point(rc["interior_point"]))   # the point S1 tested
    assert all(p["PARENT_FACE"] == FACE for p in parts)
    r = {(x["VIEW"], x["LANE"]): x for x in rows(PKG / "10_POPULATION_RECONCILIATION.csv")}
    assert r[("GBP_ARRANGEMENT", "RECOVERED_THIS_ROUND")]["RECORDS"] == "1"
    assert r[("GBP_ARRANGEMENT", "S1_PANEL")]["RECORDS"] == "23"


def test_the_parts_tile_the_face_once_and_touch_no_s8_1_record(parts, s81, summary):
    P = [poly(p) for p in parts]
    assert math.fsum(f(p["AREA_M2"]) for p in parts) == pytest.approx(49.074227, abs=1e-6)
    assert math.fsum(f(p["AREA_M2"]) for p in parts) == pytest.approx(summary["recovered_gross_m2"], abs=1e-9)
    over = math.fsum(P[i].intersection(P[j]).area for i in range(len(P)) for j in range(i + 1, len(P)))
    assert over < 1.0                                                   # mm2: shared edges only
    assert unary_union(P).area / 1e6 == pytest.approx(49.074227, abs=1e-4)
    for rid, r in s81.items():
        if r["POLYGON_MM"]:
            assert Polygon(json.loads(r["POLYGON_MM"])).intersection(unary_union(P)).area < 1.0, rid
    ids = [p["PART_ID"] for p in parts]
    assert len(ids) == len(set(ids)) == 16


def test_lanes_and_areas(parts, summary):
    assert Counter(p["LANE"] for p in parts) == {RR.GROUND_SLAB_CANDIDATE: 5, RR.STRUCTURAL_BEAM_OR_WALL: 8,
                                                 RR.STAIR_OR_SPECIAL_STRUCTURE: 1, RR.LIFT_PIT_OPENING: 1,
                                                 RR.CLASSIFICATION_BLOCKED: 1}
    area = {k: math.fsum(f(p["AREA_M2"]) for p in parts if p["LANE"] == k) for k in RR.LANES}
    assert area[RR.GROUND_SLAB_CANDIDATE] == pytest.approx(summary["candidate_slab_area_m2"], abs=1e-9)
    assert area[RR.GROUND_SLAB_CANDIDATE] == pytest.approx(29.059915, abs=1e-6)
    assert area[RR.LIFT_PIT_OPENING] == pytest.approx(1.8 * 1.8, abs=1e-6) == summary["lift_pit_opening_m2"]
    assert area[RR.STAIR_OR_SPECIAL_STRUCTURE] == pytest.approx(2.4 * 4.8, abs=1e-6)
    assert area[RR.STRUCTURAL_BEAM_OR_WALL] == pytest.approx(summary["excluded_structural_m2"], abs=1e-9)
    assert area[RR.OUTSIDE_BUILDING] == 0
    assert 0 < area[RR.CLASSIFICATION_BLOCKED] * 1e6 < 1.0              # the one sliver is under 1 mm2
    assert summary["confirmed_slab_area_m2"] == 0.0                      # a candidate is not a confirmed slab
    assert all(p["KIND"] == "CELL_BETWEEN_MEMBERS" for p in lane(parts, RR.GROUND_SLAB_CANDIDATE))


def test_the_pit_opening_and_its_walls_belong_to_the_lift_system(parts):
    pit = lane(parts, RR.LIFT_PIT_OPENING)
    assert len(pit) == 1 and pit[0]["OWNER"] == "SPC-LIFT_PIT"
    x0, y0, x1, y1 = json.loads(pit[0]["BBOX_MM"])
    assert (round(x1 - x0, 3), round(y1 - y0, 3)) == (1800.0, 1800.0)
    assert "7BE" in json.loads(pit[0]["EVIDENCE"])["evidence_id"]
    walls = [p for p in parts if p["KIND"] == "WALL"]
    assert len(walls) == 4 and all(p["OWNER"] == "PS8-LIFT-WALLS" for p in walls)
    for w in walls:                                                      # the 200 mm P14-LIFT ring
        x0, y0, x1, y1 = json.loads(w["BBOX_MM"])
        assert round(min(x1 - x0, y1 - y0), 3) == 200.0
        assert poly(w).touches(poly(pit[0])) or poly(w).distance(poly(pit[0])) < 1e-6


def test_the_stair_bay_is_excluded_and_no_tread_is_in_a_slab_cell(parts):
    st = lane(parts, RR.STAIR_OR_SPECIAL_STRUCTURE)
    assert len(st) == 1 and st[0]["OWNER"].startswith("S8 STAIR") and st[0]["STATE"].startswith("EXCLUDED_STAIR")
    assert len(json.loads(st[0]["EVIDENCE"])["treads"]) >= 4
    for p in lane(parts, RR.GROUND_SLAB_CANDIDATE):
        assert json.loads(p["EVIDENCE"])["treads"] == []
    blocked = rows(PKG / "02_POPULATION_OWNERSHIP_DELTA.csv")
    assert not any(st[0]["PART_ID"] in d["RECORD"] for d in blocked if d["ACTION"] == "ADD_BLOCKED_RECORD")


def test_beam_bands_link_to_the_s5_ground_beams(parts):
    occ = {b["beam_id"]: b.get("member") for b in J(S1 / "BEAM_OCCURRENCE_REGISTER.json")["rows"]}
    beams = [p for p in parts if p["KIND"] == "BEAM"]
    assert sorted(json.loads(p["EVIDENCE"])["s1_beam_line"] for p in beams) == ["BL010", "BL029", "BL030", "BL033"]
    for p in beams:
        e = json.loads(p["EVIDENCE"])
        assert p["OWNER"].startswith(f"S5 GROUND_BEAM line {e['s1_beam_line']}")
        assert e["s1_beam_occurrences"] and all(occ[o] == e["s1_beam_line"] for o in e["s1_beam_occurrences"])
        x0, y0, x1, y1 = json.loads(p["BBOX_MM"])
        assert round(min(x1 - x0, y1 - y0), 3) == 300.0                  # the paired-line band width


def test_two_blocked_records_per_candidate_and_no_quantity(parts, summary):
    cand = {p["PART_ID"]: f(p["AREA_M2"]) for p in lane(parts, RR.GROUND_SLAB_CANDIDATE)}
    delta = rows(PKG / "02_POPULATION_OWNERSHIP_DELTA.csv")
    nb = [d for d in delta if d["ACTION"] == "ADD_BLOCKED_RECORD"]
    assert {d["RECORD"] for d in nb} == {f"S8.1A-B-{c}-{k}" for c in cand for k in ("CONCRETE_THICKNESS", "MESH")}
    assert all(d["LANE"] == "BLOCKED_UNQUANTIFIED" and d["OWNER"] == "SPC-GROUND_SLAB" for d in nb)
    for d in nb:
        cell = d["RECORD"].removeprefix("S8.1A-B-").removesuffix("-CONCRETE_THICKNESS").removesuffix("-MESH")
        assert f(d["AREA_M2"]) == cand[cell]
    br = summary["blocked_records"]
    assert br["new"] == 10 and br["s8_1"] == 56
    assert br["lanes_after_correction"] == {"BLOCKED_UNQUANTIFIED": 66, "SOURCE_CONFLICT": 0}
    s = J(S81 / "10_S8_1_SUMMARY.json")
    assert summary["revised_blocked_ground_slab_m2"] == pytest.approx(s["blocked_area_m2"] + sum(cand.values()),
                                                                      abs=1e-9)
    for p in lane(parts, RR.GROUND_SLAB_CANDIDATE):
        assert p["OWNER"] == "SPC-GROUND_SLAB" and p["STATE"] == "BLOCKED_NO_SOURCE_THICKNESS_OR_MESH"


# ------------------------------------------------------------------ TT1 and cover
def test_tt1_scope_is_not_established_and_s8_1_stays_one_versioned_reading():
    i = {r["INTERPRETATION_ID"]: r for r in rows(PKG / "04_TT1_INTERPRETATION_REGISTER.csv")}
    assert i["VERDICT"]["STATUS"] == "ANNOTATION_SCOPE_NOT_ESTABLISHED"
    assert i["I1"]["STATUS"].startswith("CURRENT_VERSIONED_URBAN_PROJECT_BASIS")
    assert json.loads(i["I1"]["CELLS"]) == ["SP-GBP-08", "SP-GBP-14"]
    assert f(i["I1"]["AREA_M2"]) == pytest.approx(37.858523163397, abs=1e-9)
    assert i["I2"]["STATUS"] == "NOT_DETERMINABLE" and i["I3"]["STATUS"] == i["I4"]["STATUS"] == "NOT_ESTABLISHED"
    a = {r["CHECK_ID"]: r for r in rows(PKG / "03_TT1_ANNOTATION_SCOPE_AUDIT.csv")}
    assert a["TT1-04"]["RESULT"] == "CIRCLE_IN_ONE_CELL" and a["TT1-10"]["RESULT"] == "NOT_USED"
    assert a["TT1-08"]["RESULT"] == "LEVEL_SCOPE_NOT_ESTABLISHED"
    assert json.loads(a["TT1-01"]["EVIDENCE"]) == ["GROUND BEAMS PLAN"]
    assert not any("ESTABLISHED" in r["RESULT"] and "NOT_ESTABLISHED" not in r["RESULT"] for r in a.values())
    for m in json.loads(a["TT1-04"]["EVIDENCE"]):
        assert len(m["circle_within"]) == 1 and m["pointer_cells"] == m["circle_within"]


def test_cover_stays_unresolved_and_each_way_is_one_mesh(summary):
    c = {r["ITEM"]: r for r in rows(PKG / "05_COVER_APPLICABILITY_AUDIT.csv")}
    assert c["C-07"]["STATUS"] == "CONTACT_CONDITION_UNRESOLVED" and c["C-08"]["STATUS"] == "ONE_MESH"
    assert c["C-14"]["STATUS"] == "COVER_APPLICABILITY_UNRESOLVED" == summary["cover_verdict"]
    assert summary["contact_condition"] == "CONTACT_CONDITION_UNRESOLVED"
    assert c["C-03"]["STATUS"] == "NOT_APPLICABLE_TO_GROUND_SLAB"            # the build-up is the pool's
    fit = {k.split(" ")[0]: v for k, v in summary["cover_fit_mm"].items()}
    assert fit["F1"] == RR.mesh_cover_fit(100, (10, 10), 70, 25) and fit["F1"]["required_mm"] == 115
    assert fit["F2"] == RR.mesh_cover_fit(100, (10, 10), 25, 25) and fit["F2"]["margin_mm"] == 30
    assert fit["F3"]["fits"] is None
    for k in ("F4", "F5"):
        assert c[{"F4": "C-12", "F5": "C-13"}[k]]["STATUS"] == "REFERENCE_ONLY"   # T&B is not drawn


def test_the_correction_layer_changes_no_s8_1_file():
    corr = rows(PKG / "06_S8_1_CORRECTION_LAYER.csv")
    assert len(corr) == 3
    assert all(r["KG_EFFECT"] == "0" and r["M3_EFFECT"] == "0" and r["S8_1_FILE_CHANGED"] == "False" for r in corr)
    assert {r["CORRECTED_STATE"] for r in corr} == {"COVER_APPLICABILITY_UNRESOLVED"}
    old = {r["BLOCKED_ID"]: r for r in rows(S81 / "06_BLOCKED_UNRESOLVED_COMPONENTS.csv")}
    for r in corr:
        if r["S8_1_FILE"] == "06_BLOCKED_UNRESOLVED_COMPONENTS.csv":
            assert old[r["S8_1_RECORD"]]["LANE"] == r["S8_1_VALUE"] == "SOURCE_CONFLICT"   # still as frozen
    DR.verify_frozen(S81 / "11_S8_1_FREEZE_MANIFEST.json", ROOT)
    q = rows(PKG / "08_CONFLICT_AND_QUESTION_REGISTER.csv")
    assert [r["STATUS"] for r in q if r["ID"] == "CF-S8.1A-01"] == ["CORRECTED to COVER_APPLICABILITY_UNRESOLVED"]


# ------------------------------------------------------------------ conservation
def test_the_drawn_domain_closes(s81, summary):
    lanes = summary["domain_lanes_m2"]
    assert set(lanes) == {"MEASURED", "BLOCKED", "EXCLUDED", "CONFLICTED", "UNCLASSIFIED"}
    assert math.fsum(lanes.values()) == pytest.approx(summary["domain_m2"], abs=1e-9)
    faces = [r for r in s81.values() if r["ROW_KIND"] == "FACE"]
    stair = s81["SP-GBP-12"]
    dom = math.fsum(f(r["AREA_M2_EXACT"]) for r in faces) + f(stair["AREA_M2_EXACT"]) + summary["recovered_gross_m2"]
    assert summary["domain_m2"] == pytest.approx(dom, abs=1e-9)
    assert lanes["MEASURED"] == pytest.approx(37.858523163397, abs=1e-12) and lanes["CONFLICTED"] == 0.0
    assert lanes["EXCLUDED"] == pytest.approx(f(stair["AREA_M2_EXACT"]) + 3.24 + summary["excluded_stair_m2"]
                                              + summary["excluded_structural_m2"], abs=1e-9)


def test_the_s8_1_census_is_linked_not_rewritten(s81):
    delta = rows(PKG / "02_POPULATION_OWNERSHIP_DELTA.csv")
    link = {d["RECORD"]: d for d in delta if d["ACTION"] == "LINK_UNCHANGED"}
    with_poly = {k for k, r in s81.items() if r["POLYGON_MM"]}
    assert set(link) == with_poly and len(link) == 23
    assert sum(1 for k in link if s81[k]["ROW_KIND"] == "FACE") == 21
    for k, d in link.items():
        assert f(d["AREA_M2"]) == f(s81[k]["AREA_M2_EXACT"])
    assert Counter(d["ACTION"] for d in delta) == {"LINK_UNCHANGED": 23, "ADD_RECOVERED_PART": 16,
                                                  "ADD_BLOCKED_RECORD": 10}


def test_every_conservation_check_passes():
    c = rows(PKG / "09_CONSERVATION_CHECKS.csv")
    assert [r["CHECK_ID"] for r in c] == [f"CS-{i:02d}" for i in range(1, 15)]
    assert all(r["RESULT"] == "PASS" for r in c)
    e = {r["CHECK_ID"]: json.loads(r["EVIDENCE"]) for r in c}
    assert e["CS-10"]["markers_in_recovered_cells"] == [] and e["CS-10"]["new_records_with_kg_or_m3"] == 0
    assert e["CS-14"]["pit_opening_is_a_part_without_S-BW"] is False


def test_questions_go_to_the_engineer_not_the_owner():
    q = rows(PKG / "08_CONFLICT_AND_QUESTION_REGISTER.csv")
    assert {r["ID"] for r in q} >= {f"Q-S8.1A-0{i}" for i in range(1, 6)}
    assert not any("owner" in r["TO"].lower() for r in q)
    assert all(r["STATUS"].startswith(("OPEN", "CORRECTED")) for r in q)


# ------------------------------------------------------------------ hygiene
def test_no_forbidden_label_and_no_final_claim():
    from engine.source import slab_rebar_qto as SR
    for name in OUTPUTS:
        text = (PKG / name).read_text(encoding="utf-8")
        for bad in SR.FORBIDDEN_LABELS:
            assert bad not in text, (name, bad)


def test_builder_and_engine_are_blind():
    for src in (PKG / "build_s8_1a.py", ROOT / "engine" / "source" / "region_recovery.py"):
        text = src.read_text(encoding="utf-8")
        for tok in ("BOQ_LINES", "registers_v3b", "V3b", "coverage_recovery", "ground_slab_recovery", "freelancer",
                    "donor", "christ", "U-C4N", "kg/m3", "benchmark", "post_freeze"):
            assert tok not in text, (src.name, tok)


def test_registry_declares_the_engine_and_the_builder():
    sys.path.insert(0, str(ROOT / "tests" / "structural_comparison_engine"))
    import rebar_product_registry as RP
    assert "engine/source/region_recovery.py" in RP.ACCURATE_MODULES
    assert "research/alsenan_ground_slab_s8_1a/build_s8_1a.py" in RP.ACCURATE_BUILDERS


def test_rebuild_is_byte_identical():
    names = OUTPUTS + ["14_S8_1A_FREEZE_MANIFEST.json"]
    before = {o: hashlib.sha256((PKG / o).read_bytes()).hexdigest() for o in names}
    subprocess.run([sys.executable, "-I", str(PKG / "build_s8_1a.py")], check=True, cwd=ROOT, capture_output=True)
    after = {o: hashlib.sha256((PKG / o).read_bytes()).hexdigest() for o in names}
    assert before == after
