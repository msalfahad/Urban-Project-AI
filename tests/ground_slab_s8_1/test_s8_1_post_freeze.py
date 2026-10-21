"""S8.1 post-freeze comparison: downstream only, frozen first (git-proved), every reference item placed on an S8.1
record, every difference classified and closed, nothing tuned."""

from __future__ import annotations

import csv
import hashlib
import json
import math
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
PKG = ROOT / "research" / "alsenan_ground_slab_s8_1"
PF = PKG / "post_freeze"
CLASSES = {"MARKER_CELL_GEOMETRY", "ZONE_EXTENT_SCOPE", "OTHER_OWNER_CELL", "POPULATION_GAP", "ZONE_POLYGON_RESIDUAL",
           "COUNT_CONVENTION", "GROSS_AREA_UNSEPARATED", "SCOPE_UNSEPARATED", "REFERENCE_ROUNDING", "SANITY_RATIO"}
MARKERS = ["SP-GBP-08", "SP-GBP-14"]


def J(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def rows(p):
    with open(p, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


@pytest.fixture(scope="module")
def s():
    return J(PF / "S8_1_POST_FREEZE_SUMMARY.json")


@pytest.fixture(scope="module")
def tot(s):
    return {(t["REFERENCE"], t["QUANTITY"]): t for t in s["reference_totals"]}


def _git(*a):
    return subprocess.run(["git", *a], cwd=ROOT, check=True, capture_output=True)


def test_freeze_before_comparison_guarantee(s):
    if not shutil.which("git") or not (ROOT / ".git").exists():
        pytest.skip("no git checkout")
    full = _git("rev-parse", "201f441").stdout.decode().strip()
    assert s["freeze_commit"] == full
    at_freeze = _git("show", f"{full}:research/alsenan_ground_slab_s8_1/11_S8_1_FREEZE_MANIFEST.json").stdout
    assert hashlib.sha256(at_freeze).hexdigest() == hashlib.sha256(
        (PKG / "11_S8_1_FREEZE_MANIFEST.json").read_bytes()).hexdigest() == s["freeze_manifest_sha256"]
    tree = _git("ls-tree", "-r", "--name-only", full, "research/alsenan_ground_slab_s8_1/").stdout.decode().split()
    assert tree and not any("post_freeze" in t for t in tree)             # no comparison existed at the freeze
    assert _git("merge-base", "--is-ancestor", full, "HEAD").returncode == 0
    m = J(PKG / "11_S8_1_FREEZE_MANIFEST.json")
    assert m["references_read"] == [] and m["state"] == "FROZEN_BEFORE_COMPARISON"


def test_frozen_outputs_are_untouched():
    m = J(PKG / "11_S8_1_FREEZE_MANIFEST.json")
    for name, h in m["outputs"].items():
        assert hashlib.sha256((PKG / name).read_bytes()).hexdigest() == h, name


def test_post_freeze_comparison_is_downstream_only(s):
    src = (PF / "post_freeze_comparison.py").read_text(encoding="utf-8")
    main = src[src.index("def main("):]
    first_ref = min(main.index(x) for x in ("cr_cells(", "_j(R4)", "_j(R3)", "v3b_ground_slab_rows(", "_j(CONCRETE)",
                                            "christiannp(", "_j(LINEAGE)", "_j(REBAR_ME)", "_j(ROUGH)", "_j(CR_DASH)"))
    assert main.index("verify_freeze()") < main.index("s8_1()") < first_ref
    assert s["freeze_manifest_verified"] is True and s["tuned"] is False and s["s8_1_outputs_written"] is False
    assert s["frozen_engine_stamp"] == J(PKG / "11_S8_1_FREEZE_MANIFEST.json")["engine_commit_stamp"]
    for p in [PKG / "build_s8_1.py", ROOT / "engine/source/ground_slab_qto.py"]:
        assert "post_freeze_comparison" not in p.read_text(encoding="utf-8"), p.name
    assert "write_text" not in "".join(ln for ln in src.splitlines() if "PKG /" in ln)  # never writes the package
    reg = (ROOT / "tests/structural_comparison_engine/rebar_product_registry.py").read_text(encoding="utf-8")
    assert '"research/alsenan_ground_slab_s8_1/post_freeze/post_freeze_comparison.py"' in reg


def test_nothing_tuned(s, tot):
    f = J(PKG / "10_S8_1_SUMMARY.json")
    assert s["s8_1"]["total_kg"] == f["total_kg"] and s["s8_1"]["concrete_m3"] == f["concrete_m3"]
    assert s["s8_1"]["included_area_m2"] == f["included_area_m2"] and s["s8_1"]["marker_cells"] == MARKERS
    for (ref, q), t in tot.items():
        assert t["S8_1_VALUE"] == (f["concrete_m3"] if q == "CONCRETE_M3" else f["total_kg"]), ref
        assert t["S8_1_MEASUREMENT_ORIGIN"] == "SOURCE_VERIFIED_CURRENT_MEASUREMENT"
    assert s["s8_1"]["measurement_origin"] == "SOURCE_VERIFIED_CURRENT_MEASUREMENT"
    assert tot[("OLD_URBAN_V3B", "REBAR_KG")]["MEASUREMENT_ORIGIN"].startswith("OLD_V3B_CALCULATED")


def test_every_difference_is_classified_and_closes(s):
    assert set(s["classes"]) >= CLASSES and s["unknown_rows"] == []
    for t in s["reference_totals"]:
        assert set(t["CLASSES"]) <= CLASSES, t["REFERENCE"]
        if t["DIFF"] is None:
            assert t["MATCHING"] == "NOT_COMPARABLE" and t["CLASSES"] == {}
        else:
            assert abs(math.fsum(t["CLASSES"].values()) - t["DIFF"]) <= 1e-6, (t["REFERENCE"], t["QUANTITY"])
    causes = rows(PF / "S8_1_POST_FREEZE_DIFFERENCE_CAUSES.csv")
    assert causes and {c["CLASS"] for c in causes} <= CLASSES and all(c["BASIS"] for c in causes)


def test_equal_scope_is_the_two_marker_cells_and_differs_only_by_boundary(s, tot):
    eq = {e["S8_1_ROW_ID"]: e for e in s["equal_scope"]}
    assert sorted(eq) == MARKERS
    for e in eq.values():
        assert e["CLASS"] == "MARKER_CELL_GEOMETRY" and len(e["OLD_URBAN_CELL"]) == 1
        assert -0.2 < e["OLD_URBAN_MINUS_S8_1_M2"] < 0                    # old Urban cuts 300 mm bands
        if e["CHRISTIANNP_FACE"] is not None:
            assert len(e["CHRISTIANNP_FACE"]) == 1 and abs(e["CHRISTIANNP_MINUS_S8_1_M2"]) < 1e-3
    k = s["s8_1"]["kg_per_m2"]
    for ref in ("OLD_URBAN_R4", "OLD_URBAN_R3", "OLD_URBAN_V3B"):
        t = tot[(ref, "REBAR_KG")]
        assert abs(t["REFERENCE_ON_S8_1_SCOPE"] - sum(e["OLD_URBAN_AREA_M2"] for e in eq.values()) * k) <= 1e-9
        assert abs(t["EQUAL_SCOPE_DIFF"]) < 1.0                            # under 1 kg on equal scope
        assert abs(t["CLASSES"]["MARKER_CELL_GEOMETRY"] - t["EQUAL_SCOPE_DIFF"]) <= 1e-9


def test_crosswalk_places_every_reference_item_once(s):
    cross = rows(PF / "S8_1_POST_FREEZE_CELL_CROSSWALK.csv")
    recs = [r for r in cross if r["S8_1_ROW_ID"]]
    reg = [r for r in rows(PKG / "01_GROUND_SLAB_POPULATION_AND_ZONE_REGISTER.csv") if r["POLYGON_MM"]]
    assert sorted(r["S8_1_ROW_ID"] for r in recs) == sorted(r["ROW_ID"] for r in reg)
    cr = [c for r in cross for c in json.loads(r["OLD_URBAN_CELLS"] or "[]")]
    assert len(cr) == len(set(cr)) == len(J(ROOT / "research/coverage_recovery_round/GROUND_SLAB_CELL_EXTRACT.json")
                                          ["cells"])
    ch = [f for r in cross for f in json.loads(r["CHRISTIANNP_FACES"] or "[]")]
    assert len(ch) == len(set(ch))
    by = {r["S8_1_ROW_ID"]: r for r in recs}
    for k in MARKERS:
        assert by[k]["CLASS_IF_A_REFERENCE_QUANTIFIES_IT"] == "MARKER_CELL_GEOMETRY"
    faces = [r for r in recs if r["S8_1_ROW_KIND"] == "FACE" and r["S8_1_ROW_ID"] not in MARKERS]
    assert len(faces) == 19
    assert all(r["CLASS_IF_A_REFERENCE_QUANTIFIES_IT"] == "ZONE_EXTENT_SCOPE" for r in faces)   # every blocked face
    assert by["SP-GBP-12"]["CLASS_IF_A_REFERENCE_QUANTIFIES_IT"] == "OTHER_OWNER_CELL"
    assert by["SP-GBP-01"]["OLD_URBAN_CELLS"] == "[]"                      # nothing lands outside the building


def test_old_urban_zones_and_conventions(s, tot):
    ou = s["old_urban"]
    assert len(ou["zone_cells"]["ZONE-1"]) == len(ou["zone_cells"]["ZONE-2"]) == 7
    assert "SP-GBP-08" in ou["zone_cells"]["ZONE-1"] and "SP-GBP-14" in ou["zone_cells"]["ZONE-2"]
    assert "SP-GBP-12" in ou["zone_cells"]["ZONE-1"]                      # the stair cell, owned by S8 STAIR
    r4, v3b = tot[("OLD_URBAN_R4", "REBAR_KG")], tot[("OLD_URBAN_V3B", "REBAR_KG")]
    assert abs(r4["REFERENCE_VALUE"] - 712.277099) <= 1e-6 and abs(v3b["REFERENCE_VALUE"] - 720.691428) <= 1e-6
    assert "COUNT_CONVENTION" not in r4["CLASSES"]
    assert abs(v3b["CLASSES"]["COUNT_CONVENTION"] - ou["v3b_count_convention_kg"]) <= 1e-12
    assert 8.41 < ou["v3b_count_convention_kg"] < 8.42                   # one extra 6.816 m bar per direction
    assert tot[("OLD_URBAN_R3", "REBAR_KG")]["CLASSES"] == r4["CLASSES"]  # R4 carried R3 unchanged
    assert abs(ou["cr_released_m2"] - 115.2751) <= 1e-9 and abs(ou["cr_best_m2"] - 217.0116) <= 1e-9
    assert tot[("OLD_URBAN_CR_LOWER_BOUND", "CONCRETE_M3")]["REFERENCE_VALUE"] == 11.528
    assert tot[("OLD_URBAN_V3B", "CONCRETE_M3")]["REFERENCE_VALUE"] == 11.539


def test_findings_are_recorded_not_applied(s):
    f = {x["ID"]: x for x in s["findings"]}
    assert set(f) == {"S8.1-PF-01", "S8.1-PF-02", "S8.1-PF-03", "S8.1-PF-04"}
    assert f["S8.1-PF-01"]["KIND"] == "POPULATION_GAP" and "7BE" in f["S8.1-PF-01"]["WHAT"]
    assert all(x["EFFECT_ON_S8_1"].startswith("none") for x in s["findings"])
    gap = [r for r in rows(PF / "S8_1_POST_FREEZE_CELL_CROSSWALK.csv") if r["S8_1_ROW_KIND"] == "NO_S8_1_RECORD"]
    assert gap and all(r["CLASS_IF_A_REFERENCE_QUANTIFIES_IT"] == "POPULATION_GAP" for r in gap)
    assert any(json.loads(r["OLD_URBAN_CELLS"] or "[]") == ["FP1-C99368_44772:X"] for r in gap)


def test_one_figure_references_and_rough(s, tot):
    assert tot[("FREELANCER", "CONCRETE_M3")]["MATCHING"] == "CATEGORY"
    assert tot[("FREELANCER", "CONCRETE_M3")]["REFERENCE_VALUE"] == 29.55
    for ref in ("FREELANCER", "UC4N"):
        t = tot[(ref, "REBAR_KG")]
        assert t["MATCHING"] == "NOT_COMPARABLE" and t["DIFF"] is None
    for ref in ("UC4N", "CHRISTIANNP_ORIGINAL"):
        assert set(tot[(ref, "CONCRETE_M3")]["CLASSES"]) == {"SCOPE_UNSEPARATED"}
    ro = tot[("ROUGH_130_KG_PER_M3", "REBAR_KG")]
    assert ro["MATCHING"] == "SANITY_ONLY" and s["rough"]["use"] == "SANITY_CHECK_ONLY" and \
        s["rough"]["promoted"] is False
    assert abs(ro["REFERENCE_VALUE"] - 130 * s["s8_1"]["concrete_m3"]) <= 1e-9


def test_christiannp_rerun_when_supplied(s, tot):
    if ("CHRISTIANNP_FORENSIC", "REBAR_KG") not in tot:
        pytest.skip("christiannp rerun not supplied to this comparison run")
    c = s["christiannp"]
    assert c["slab_m2"] == 217.6826 and c["kg"] == 1343.72 and c["slab_faces_without_s8_1_record"] == 11
    t = tot[("CHRISTIANNP_FORENSIC", "REBAR_KG")]
    assert t["MATCHING"] == "CELL" and abs(t["EQUAL_SCOPE_DIFF"]) < 0.01
    assert {"ZONE_EXTENT_SCOPE", "POPULATION_GAP", "OTHER_OWNER_CELL"} <= set(t["CLASSES"])
