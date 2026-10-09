"""S8.2A (research/alsenan_swimming_pool_s8_2a): architectural elevation source recovery and pool depth authority.

A dated correction layer on the frozen S8.2. The checks re-derive it from its own outputs and the frozen stages:

- S8.2 and every earlier stage still verify, and S8.2 is not written;
- the re-supplied architectural PDF is one 12-sheet set in two upload parts, registered as additional evidence (not
  a replacement); each part matches its earlier registered part apart from wrapper metadata;
- the elevation's '115' binds to the swimming pool on label, dimension and feature criteria; '70' is the building;
- the depth holds at one drawn plane only: the floor profile conflicts across sources, so nothing is released;
- every S8.2 concrete row and bar family is carried with its lane; conflicts and questions are carried and extended;
- no client drawing is in the package, the builder is blind and its rebuild is byte-identical."""

from __future__ import annotations

import csv
import hashlib
import json
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

import pytest

from engine.source import delta_release as DR
from engine.source import elevation_binding as EB
from engine.source import source_identity as SI

ROOT = Path(__file__).resolve().parents[2]
PKG = ROOT / "research" / "alsenan_swimming_pool_s8_2a"
S82 = ROOT / "research" / "alsenan_swimming_pool_s8_2"
MANIFEST = PKG / "12_S8_2A_FREEZE_MANIFEST.json"
OUTPUTS = ["00_README.md", "01_ARCH_PDF_IDENTITY_COMPARISON.csv", "02_ELEVATION_TO_PLAN_BINDING_AUDIT.csv",
           "03_DIMENSION_SOURCE_REGISTER.csv", "04_POOL_DEPTH_AND_ZONE_INTERPRETATION.csv",
           "05_QUANTITY_READINESS_DELTA.csv", "06_BLOCKED_REGISTER_DELTA.csv",
           "07_CONFLICT_AND_QUESTION_REGISTER_DELTA.csv", "08_SENSITIVITY_CASES.csv", "09_CONSERVATION_CHECKS.csv",
           "10_PROVENANCE.jsonl", "11_S8_2A_SUMMARY.json"]
NEW = {"cd3b8669d55998cb638bd8e2b572da4992ed64babcecacd73753d6a2f0c68b97": "80b6a80428990db4dfa86aa343ed2c7cb429709459d564f0dac92362480a9b00",
       "1e7087d3e61bbb682c9107193c97550a2837e5198bde0ee311319bf7f4a08459": "281a0c3f8c1cdd8f2a78528513b66d14ba4793e981e2d8059423faf6e6162f99"}
BY_SHA = ROOT / "data/inputs/by_sha256"
needs_inputs = pytest.mark.skipif(not all((BY_SHA / f"{s}.pdf").exists() for s in NEW) or not
                                  (BY_SHA / "ab54dd554c31fe4a6a63ff773dc6d034159a736c7dd78158483b473a4ed31cc4.dxf").exists(),
                                  reason="private client drawings not restored in data/inputs/by_sha256")


def J(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def rows(name, pkg=PKG):
    with open(pkg / name, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


@pytest.fixture(scope="module")
def s():
    return J(PKG / "11_S8_2A_SUMMARY.json")


# ------------------------------------------------------------------ freeze, S8.2 untouched
def test_frozen_correction_layer():
    m = J(MANIFEST)
    assert m["round"] == "S8_2A" and m["state"] == "FROZEN_CORRECTION_LAYER" and m["references_read"] == []
    assert set(m["outputs"]) == set(OUTPUTS) and m["released"] == {"concrete_m3": 0.0, "reinforcement_kg": 0.0,
                                                                   "rows_released": 0}
    DR.verify_frozen(MANIFEST, ROOT)


def test_s8_2_and_every_earlier_stage_still_verify(s):
    assert len(s["frozen_baselines"]) == 17 and "S8.2" in s["frozen_baselines"]
    for name in s["frozen_baselines"]:
        man = {"S8.2": S82 / "18_S8_2_FREEZE_MANIFEST.json"}.get(name)
        if man:
            assert DR.verify_frozen(man, ROOT)["manifest_sha256"] == s["frozen_baselines"][name]
    m82 = J(S82 / "18_S8_2_FREEZE_MANIFEST.json")
    for o, h in m82["outputs"].items():
        assert hashlib.sha256((S82 / o).read_bytes()).hexdigest() == h, o
    s82 = J(S82 / "17_S8_2_SUMMARY.json")
    assert s82["plan_m2"]["structural_footprint"] == pytest.approx(10.935563750809475, abs=1e-12)
    assert s82["reinforcement"]["families"] == 21 and len(rows("13_REBAR_EVIDENCE_BINDING.csv", S82)) == 26


# ------------------------------------------------------------------ source identity: one 12-sheet set
SHEETS = [f"{i:02d}" for i in range(1, 13)]


def test_the_set_is_additional_evidence_and_each_part_matches_its_earlier_part(s):
    r01 = rows("01_ARCH_PDF_IDENTITY_COMPARISON.csv")
    sets = [r for r in r01 if r["RELATION"] == "DRAWING_SET"]
    assert len(sets) == 1 and sets[0]["SOURCE_KEY"] == "P7757_ARCH_PDF_SET_01-12" and sets[0]["SET_SHEET"] == "01-12"
    assert sets[0]["PAGES"] == "12" and sets[0]["NEW_SHA256"] == "" and sets[0]["EARLIER_SHA256"] == ""
    ident = {r["NEW_SHA256"]: r for r in r01 if r["RELATION"] not in ("PAGE_IMAGE", "DRAWING_SET")}
    assert set(ident) == set(NEW)
    for (new, old), sheets in zip(NEW.items(), ("01-06", "07-12")):
        r = ident[new]
        assert r["RELATION"] == SI.WRAPPER_METADATA_ONLY and r["EARLIER_SHA256"] == old and r["SET_SHEET"] == sheets
        assert r["RECONSTRUCTED_SHA256"] == old and r["REMOVED_INFO_BYTES"] == r["BYTE_DELTA"] == "134"
        assert r["PAGE_CENSUS_MATCHES_EARLIER"] == "True"
        assert r["FINDING"].startswith("byte-identical to the earlier registered") and old[:12] in r["FINDING"]
    for r in sets + list(ident.values()):                     # registered as additional evidence, never a replacement
        assert r["REGISTERED_AS"].startswith("ADDITIONAL_SOURCE") and "not a replacement" in r["REGISTERED_AS"]
    assert "EARLIER_RESTORED_ON_DISK" not in r01[0]           # the outputs never depend on keeping the earlier copies
    assert s["pdf_set"]["sheets"] == 12 and s["pdf_set"]["parts"] == {"ARCH_PART_1_PAGES_01-06": "01-06",
                                                                       "ARCH_PART_2_PAGES_07-12": "07-12"}
    pages = [r for r in r01 if r["RELATION"] == "PAGE_IMAGE"]
    assert [p["SET_SHEET"] for p in pages] == SHEETS
    assert all(json.loads(p["NEW_METADATA"])["image_px"] == [[4672, 6624]] for p in pages)


def test_every_visual_record_and_dimension_row_names_its_set_sheet():
    d = {r["DIM_ID"]: r for r in rows("03_DIMENSION_SOURCE_REGISTER.csv")}
    assert all(r["SET_SHEET"] in SHEETS + ["01-12"] for r in d.values())
    vis = {k: r for k, r in d.items() if r["HANDLE"] == "raster"}
    assert {k: r["SET_SHEET"] for k, r in vis.items()} == {
        "VR-01": "08", "VR-02": "03", "VR-03": "03", "VR-04": "07", "VR-05": "09", "VR-06": "10", "VR-07": "11",
        "VR-08": "12", "VR-09": "01-12"}
    assert "ARCH_PART_2_PAGES_07-12 p.2" in vis["VR-01"]["SOURCE"] and "ARCH_PART_1_PAGES_01-06 p.3" in vis["VR-02"]["SOURCE"]
    assert d["D-02"]["SET_SHEET"] == "08" and d["D-P-WIDTH_350"]["SET_SHEET"] == "03"
    prov = [json.loads(x) for x in (PKG / "10_PROVENANCE.jsonl").read_text(encoding="utf-8").splitlines()]
    by = {p["record"]: p for p in prov if p["output"] == "03_DIMENSION_SOURCE_REGISTER.csv"}
    assert by["VR-01"]["drawing_sha256"] == "1e7087d3e61bbb682c9107193c97550a2837e5198bde0ee311319bf7f4a08459"
    assert by["VR-02"]["drawing_sha256"] == "cd3b8669d55998cb638bd8e2b572da4992ed64babcecacd73753d6a2f0c68b97"
    assert sorted(by["VR-09"]["drawing_sha256"]) == sorted(NEW)


def test_the_re_freeze_names_the_first_freeze_and_changes_no_finding():
    m = J(MANIFEST)
    a = m["amends_s8_2a_freeze"]
    assert a["freeze_commit"] == "1900650" and re.fullmatch(r"[0-9a-f]{64}", a["manifest_sha256"])
    first = subprocess.run(["git", "show", f"{a['freeze_commit']}:{MANIFEST.relative_to(ROOT)}"], cwd=ROOT,
                           capture_output=True)
    if first.returncode != 0:
        pytest.skip("first S8.2A freeze commit not in this clone's history")
    assert hashlib.sha256(first.stdout).hexdigest() == a["manifest_sha256"]
    old = json.loads(first.stdout)["outputs"]
    for o in ("02_ELEVATION_TO_PLAN_BINDING_AUDIT.csv", "04_POOL_DEPTH_AND_ZONE_INTERPRETATION.csv",
              "05_QUANTITY_READINESS_DELTA.csv", "06_BLOCKED_REGISTER_DELTA.csv",
              "07_CONFLICT_AND_QUESTION_REGISTER_DELTA.csv", "08_SENSITIVITY_CASES.csv"):
        assert m["outputs"][o] == old[o], o


@needs_inputs
def test_identity_recomputes_from_the_restored_files():
    for new, old in NEW.items():
        assert SI.relation((BY_SHA / f"{new}.pdf").read_bytes(), old)["relation"] == SI.WRAPPER_METADATA_ONLY


# ------------------------------------------------------------------ binding
def test_115_binds_to_the_pool_and_70_to_the_building(s):
    b = {r["CRITERION"]: r for r in rows("02_ELEVATION_TO_PLAN_BINDING_AUDIT.csv")}
    assert b["VERDICT"]["SATISFIED"] == "True" and b["VERDICT"]["EVIDENCE"].startswith(EB.BOUND)
    kinds = Counter(r["KIND"] for k, r in b.items() if k != "VERDICT" and r["SATISFIED"] == "True")
    assert kinds[EB.IDENTITY_LABEL] == 1 and kinds[EB.DIMENSION_MATCH] == 3 and kinds[EB.FEATURE_MATCH] == 3
    assert kinds[EB.LEVEL_MATCH] == 1 and kinds[EB.CONTRADICTION] == 0
    assert s["binding"]["115"]["state"] == EB.BOUND and s["binding"]["115"]["levels_m"] == [0.3, -0.85]
    assert s["binding"]["70"]["object"] == "BUILDING" and s["binding"]["70"]["levels_m"] == [0.3, 1.0]


def test_the_plan_115_is_a_homonym_never_a_depth():
    d = {r["DIM_ID"]: r for r in rows("03_DIMENSION_SOURCE_REGISTER.csv")}
    assert d["D-02"]["HANDLE"] == "2E5E" and d["D-02"]["MEASUREMENT_MM"] == "1150"
    assert json.loads(d["D-02"]["WITNESS_LEVELS_M"]) == [-0.85, 0.3]
    assert d["D-P-PLAN_115"]["PRINTED"] == "115" and d["D-P-PLAN_115"]["USE"].startswith("none")
    assert d["D-03"]["USE"].startswith("none for the pool")


# ------------------------------------------------------------------ depth scope: no uniform application, nothing released
def test_the_depth_holds_at_one_plane_and_the_profile_conflicts(s):
    z = {r["ITEM_ID"]: r for r in rows("04_POOL_DEPTH_AND_ZONE_INTERPRETATION.csv")}
    assert (z["Z-01"]["VALUE"], z["Z-01"]["STATE"]) == ("0.3", "ESTABLISHED")
    assert z["Z-04"]["STATE"] == "STATED_AT_DRAWN_PLANE_ONLY"
    for k in ("Z-06", "Z-07", "Z-08", "Z-10"):
        assert z[k]["VALUE"] == "" and z[k]["STATE"] == "NOT_ESTABLISHED"
    assert s["floor_profile"] == EB.PROFILE_CONFLICT and z["Z-11"]["STATE"] == "INFERENCE_ONLY"


def test_nothing_is_released_and_every_s8_2_row_is_carried(s):
    r = rows("05_QUANTITY_READINESS_DELTA.csv")
    assert Counter(x["KIND"] for x in r) == {"CONCRETE": 7, "REINFORCEMENT": 21}
    assert all(x["M3"] == "" and x["KG"] == "" and x["RELEASED"] == "False" and x["S8_2_LANE"] == x["S8_2A_LANE"]
               for x in r)
    assert s["released"] == {"concrete_m3": 0.0, "reinforcement_kg": 0.0, "rows_released": 0}
    assert s["s8_2_lanes_after"] == {"BLOCKED_UNQUANTIFIED": 23, "SOURCE_CONFLICT": 5}


def test_conflicts_carried_and_extended_questions_to_architect_or_engineer():
    cq = {r["ID"]: r for r in rows("07_CONFLICT_AND_QUESTION_REGISTER_DELTA.csv")}
    s82 = [r for r in rows("16_CONFLICT_AND_QUESTION_REGISTER.csv", S82) if r["KIND"] != "QUESTION"]
    assert all(cq[r["ID"]]["S8_2A_STATUS"] == r["STATUS"] for r in s82)              # nothing silently resolved
    assert {"CF-S8.2A-01", "CF-S8.2A-02", "CF-S8.2A-03", "CF-S8.2A-04"} <= set(cq)
    assert cq["Q-S8.2-01"]["S8_2A_STATUS"] == "PARTLY_ANSWERED"
    assert all(re.match(r"(Architect|Engineer)", cq[q]["NOTE"]) for q in ("Q-S8.2A-01", "Q-S8.2A-02", "Q-S8.2A-03"))


def test_sensitivity_never_enters_a_total():
    sen = rows("08_SENSITIVITY_CASES.csv")
    assert sen and all(r["LANE"] == "SENSITIVITY_ONLY" and r["IN_OFFICIAL_TOTAL"] == "False" for r in sen)


def test_every_conservation_check_passes():
    c = rows("09_CONSERVATION_CHECKS.csv")
    assert [r["CHECK_ID"] for r in c] == [f"A-{i:02d}" for i in range(1, 14)] and all(r["RESULT"] == "PASS" for r in c)


# ------------------------------------------------------------------ hygiene
def test_no_client_drawing_or_plot_stamp_path_in_the_package():
    assert not [p for p in PKG.iterdir() if p.suffix.lower() in (".png", ".jpg", ".jpeg", ".pdf", ".dxf", ".dwg")]
    for o in OUTPUTS:
        text = (PKG / o).read_text(encoding="utf-8")
        assert not re.search(r"YEARS 2013|7757-[A-Z]", text), o


def test_builder_and_engine_are_blind():
    for src in (PKG / "build_s8_2a.py", ROOT / "engine/source/elevation_binding.py",
                ROOT / "engine/source/source_identity.py"):
        text = src.read_text(encoding="utf-8")
        for tok in ("BOQ_LINES", "registers_v3b", "V3b", "coverage_recovery", "freelancer", "donor", "christ", "U-C4N",
                    "kg/m3", "benchmark", "post_freeze"):
            assert tok not in text, (src.name, tok)


def test_registry_declares_the_builder():
    sys.path.insert(0, str(ROOT / "tests" / "structural_comparison_engine"))
    import rebar_product_registry as RP
    assert "research/alsenan_swimming_pool_s8_2a/build_s8_2a.py" in RP.ACCURATE_BUILDERS


@needs_inputs
def test_rebuild_is_byte_identical():
    names = OUTPUTS + [MANIFEST.name]
    before = {o: hashlib.sha256((PKG / o).read_bytes()).hexdigest() for o in names}
    subprocess.run([sys.executable, "-I", str(PKG / "build_s8_2a.py")], check=True, cwd=ROOT, capture_output=True)
    after = {o: hashlib.sha256((PKG / o).read_bytes()).hexdigest() for o in names}
    assert before == after
