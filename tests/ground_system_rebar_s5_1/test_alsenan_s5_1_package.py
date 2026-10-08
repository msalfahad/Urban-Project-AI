"""Alsenan S5.1 package (research/alsenan_ground_system_rebar_s5_1): a delta release over frozen S5.

Released numbers are re-derived here from the frozen S5 occurrence widths / depths / counts, the 70 mm soil cover
and the frozen S1 column sides - never against a reference total."""

from __future__ import annotations

import csv
import hashlib
import json
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
PKG = ROOT / "research" / "alsenan_ground_system_rebar_s5_1"
S5 = ROOT / "research" / "alsenan_ground_system_rebar_s5"
BRIEF_FIELDS = ("FROZEN_BASELINE", "BASELINE_COMPONENT_ID", "OLD_STATE", "OLD_KNOWN_QUANTITY", "NEW_PROJECT_SOURCE",
                "SOURCE_PAGE", "SOURCE_HANDLES", "GRAPHIC_EVIDENCE_CLASS", "NEW_COMPONENT_MODEL",
                "DELTA_KNOWN_QUANTITY", "NEW_BLOCKED_COMPONENTS", "NEW_RELEASE_STATE")


def J(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def rows(p):
    return list(csv.DictReader(open(p, encoding="utf-8")))


@pytest.fixture(scope="module")
def delta():
    return rows(PKG / "S5_1_DELTA_COMPONENTS.csv")


@pytest.fixture(scope="module")
def summary():
    return J(PKG / "S5_1_RELEASE_SUMMARY.json")


@pytest.fixture(scope="module")
def occ():
    return {o["occurrence_id"]: o for o in J(S5 / "GROUND_SYSTEM_REBAR_OCCURRENCE_REGISTER.json")["occurrences"]}


def kgm(d):
    return d * d / 162.0


def core(b, h, d, c=70.0):
    return 2 * (b - 2 * c - d) + 2 * (h - 2 * c - d)


# ------------------------------------------------------------------ package / freeze
def test_deliverables_exist():
    for n in ("S5_1_DELTA_COMPONENTS.csv", "S5_1_RELEASE_SUMMARY.json", "S5_1_UNRESOLVED.csv",
              "S5_1_PROVENANCE.jsonl", "S5_1_CHANGELOG.md", "S5_1_FREEZE_MANIFEST.json"):
        assert (PKG / n).is_file(), n


def test_s5_1_freeze_manifest_still_matches():
    m = J(PKG / "S5_1_FREEZE_MANIFEST.json")
    assert m["state"] == "FROZEN" and m["references_read_before_freeze"] == []
    for group, base in (("code", ROOT), ("inputs", ROOT), ("outputs", PKG)):
        for k, h in m[group].items():
            assert hashlib.sha256((base / k).read_bytes()).hexdigest() == h, (group, k)


def test_frozen_s5_baseline_is_immutable_and_order_kept(summary):
    m = J(S5 / "S5_FREEZE_MANIFEST.json")
    for group, base in (("code", ROOT), ("inputs", ROOT), ("outputs", S5)):
        for k, h in m[group].items():
            assert hashlib.sha256((base / k).read_bytes()).hexdigest() == h, (group, k)
    pre = summary["context"]["PRECEDING_FREEZES"]
    for name, path in (("S4.1", "research/alsenan_footing_rebar_s4_1/S4_1_FREEZE_MANIFEST.json"),
                       ("S6.1", "research/alsenan_superstructure_beam_rebar_s6_1/S6_1_FREEZE_MANIFEST.json")):
        assert pre[name]["manifest_sha256"] == hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


def test_rebuild_is_byte_identical():
    before = {k: (PKG / k).read_bytes() for k in J(PKG / "S5_1_FREEZE_MANIFEST.json")["outputs"]}
    subprocess.run([sys.executable, "-I", str(PKG / "build_ground_system_rebar_s5_1.py")], check=True,
                   capture_output=True, cwd=ROOT)
    for k, v in before.items():
        assert (PKG / k).read_bytes() == v, k


def test_builder_is_blind_and_registered():
    src = (PKG / "build_ground_system_rebar_s5_1.py").read_text(encoding="utf-8")
    for bad in ("christiannp", "UC4N", "U-C4N", "freelancer", "FREELANCER", "post_freeze", "multi_engine",
                "rebar_truth", "rough_rebar", "fitz", "pymupdf", "pdf_vector_evidence", "kg/m3"):
        assert bad not in src, bad
    sys.path.insert(0, str(ROOT / "tests" / "structural_comparison_engine"))
    import rebar_product_registry as RP
    assert "research/alsenan_ground_system_rebar_s5_1/build_ground_system_rebar_s5_1.py" in RP.ACCURATE_BUILDERS


# ------------------------------------------------------------------ delta shape / conservation
def test_every_frozen_component_is_covered_once_with_brief_fields(delta):
    assert set(BRIEF_FIELDS) <= set(delta[0])
    frozen = {f"{r['occurrence_id']}:{r['component']}" for r in rows(S5 / "GROUND_SYSTEM_REBAR_COMPONENTS.csv")}
    groups = defaultdict(list)
    for r in delta:
        groups[r["BASELINE_COMPONENT_ID"]].append(r)
    assert set(groups) == frozen
    assert all(sum(1 for r in rs if r["PRIMARY"] == "Y") == 1 for rs in groups.values())


def test_delta_conservation(delta, summary):
    frozen_known = J(S5 / "GROUND_SYSTEM_REBAR_RELEASE_SUMMARY.json")["known_source_derived_ground_system_rebar_kg"]
    assert abs(sum(float(r["OLD_KNOWN_QUANTITY"]) for r in delta) - frozen_known) < 1e-3
    d = sum(float(r["DELTA_KNOWN_QUANTITY"]) for r in delta)
    assert d > 0 and abs(d - summary["delta_known_kg"]) < 1e-3
    assert abs(summary["s5_1_known_kg"] - frozen_known - summary["delta_known_kg"]) < 1e-9
    assert summary["conservation"]["all_pass"]
    assert all(r["NEW_RELEASE_STATE"] == "LOWER_BOUND" for r in delta if float(r["DELTA_KNOWN_QUANTITY"]) > 0)
    assert not [r for r in delta if r["NEW_RELEASE_STATE"] == "VERIFIED" and r["OLD_STATE"] != "VERIFIED"]


# ------------------------------------------------------------------ links
def test_gb_two_leg_link_core_path(delta, occ, summary):
    secs = summary["gb_link_sections"]
    assert len(secs) == 4 and all(v["links"] == 1 for v in secs.values())
    gb = [r for r in delta if r["FAMILY"] == "GROUND_BEAM" and r["PORTION"] == "CORE_PATH" and
          r["CHANGE_KIND"] == "QUANTITY_RELEASED"]
    assert len(gb) == 4
    for r in gb:
        o = occ[r["OCCURRENCE_ID"]]
        f = json.loads(r["FACETS"])
        assert (f["TOPOLOGY"], f["LEGS"]) == ("SINGLE_CLOSED_LINK_2_LEG", 2)
        assert (o["width_state"], o["depth_state"]) == ("SOURCE_EXPLICIT", "SOURCE_EXPLICIT")
        cp = core(o["width_mm"], o["depth_mm"], 8.0)
        assert abs(f["CORE_PATH_MM"] - cp) < 1e-9
        assert abs(float(r["DELTA_KNOWN_QUANTITY"]) - f["COUNT"] * cp / 1000 * kgm(8)) < 1e-6
        bend = [x for x in delta if x["BASELINE_COMPONENT_ID"] == r["BASELINE_COMPONENT_ID"] and
                x["PORTION"] == "BEND_ARC"]
        assert len(bend) == 1 and float(bend[0]["NEW_KNOWN_QUANTITY"]) == 0
    hooks = [r for r in delta if r["COMPONENT"].startswith("STIRRUP_HOOK") and r["CHANGE_KIND"] == "FACET_ADDED"]
    assert hooks and all(r["PORTION_STATE"] == "SHAPE_FOUND_LENGTH_BLOCKED" and float(r["NEW_KNOWN_QUANTITY"]) == 0
                         for r in hooks)


def test_lt_2_5m_link_rate_blocked_and_follow_arch_blocked(delta, occ, summary):
    assert summary["gb_link_sections"]["GB_LT_2_5M (30x30)"]["label_leaders_on_link"] == 0
    topo = [r for r in delta if r["PORTION"] == "CORE_PATH" and r["CHANGE_KIND"] == "TOPOLOGY_RECORDED"]
    assert len(topo) == 27
    for r in topo:
        assert float(r["NEW_KNOWN_QUANTITY"]) == 0 and r["NEW_RELEASE_STATE"] == "BLOCKED_UNQUANTIFIED"
        o = occ[r["OCCURRENCE_ID"]]
        if o["detail_ids"] == ["P13-GB-EXTERIOR"]:
            assert "FOLLOW ARCH" in r["WHY"]
        else:
            assert "P13-GB-LT2_5M" in o["detail_ids"] and "<2.5 m" in r["WHY"]
    assert summary["stirrup_topology_only"] == {"total": 27, "follow_arch_depth": 19, "lt_2_5m_candidate": 8}


def test_sb1_sb3_str2_outer_link_only_sb2_untouched(delta, occ):
    straps = {r["MARK"]: r for r in delta if r["FAMILY"] == "STRAP_BEAM" and r["PORTION"] == "CORE_PATH"}
    assert set(straps) == {"SB1", "SB3"}
    for m, r in straps.items():
        o = occ[r["OCCURRENCE_ID"]]
        f = json.loads(r["FACETS"])
        assert (f["TOPOLOGY"], f["LEGS"]) == ("STR2_OUTER_PLUS_ONE_INNER_4_LEG", 4)
        assert abs(f["CORE_PATH_MM"] - core(o["width_mm"], o["depth_mm"], 8.0)) < 1e-9
        inner = [x for x in delta if x["BASELINE_COMPONENT_ID"] == r["BASELINE_COMPONENT_ID"] and
                 x["PORTION"] == "INNER_LINK"]
        assert len(inner) == 1 and inner[0]["PORTION_STATE"] == "SHAPE_FOUND_LENGTH_BLOCKED"
        assert float(inner[0]["NEW_KNOWN_QUANTITY"]) == 0
    sb2 = [r for r in delta if r["MARK"] == "SB2"]
    assert sb2 and all(r["CHANGE_KIND"] == "NO_CHANGE" for r in sb2)


# ------------------------------------------------------------------ through-support
def test_through_support_continuous_run(delta, occ, summary):
    runs = summary["continuous_bar_runs"]
    assert len(runs) == 3 and summary["through_support_interior_nodes"] == 6
    for run in runs:
        spans = run["SPANS"]
        assert len({tuple(occ[s]["geometry_handles"]) for s in spans}) == 1            # one drawn band
        for a, b in zip(spans, spans[1:]):
            assert occ[a]["end_node"] == occ[b]["start_node"] and occ[a]["end_node"]["kind"] == "COLUMN"
        assert all(occ[s]["occurrence_state"] == "LOWER_BOUND" for s in spans)
        f2f = sum(occ[s]["bar_straight_run_lower_bound_m"] for s in spans)
        assert run["CONTINUOUS_RUN_LOWER_BOUND_M"] > f2f                                # never shorter than its parts
    th = [r for r in delta if r["PORTION"].startswith("THROUGH_SUPPORT")]
    assert len(th) == 6 * 2 * 3
    for r in th:
        f = json.loads(r["FACETS"])
        n, d = None, int(r["DIA_MM"])
        frozen = next(x for x in rows(S5 / "GROUND_SYSTEM_REBAR_COMPONENTS.csv")
                      if f"{x['occurrence_id']}:{x['component']}" == r["BASELINE_COMPONENT_ID"])
        n = int(frozen["bar_count"])
        w = min(f["COLUMN"]["section_cm"]) * 10
        assert abs(float(r["DELTA_KNOWN_QUANTITY"]) - n * w / 2 / 1000 * kgm(d)) < 1e-6
        assert r["QUANTITY_BASIS"] == "SCHEDULE_AND_PLAN_GEOMETRY" and r["NEW_RELEASE_STATE"] == "LOWER_BOUND"
    na = [r for r in delta if r["CHANGE_KIND"] == "SEMANTIC_CORRECTION" and r["NEW_RELEASE_STATE"] == "NOT_APPLICABLE"]
    assert len(na) == 24 and {r["COMPONENT"][:-2] for r in na} == {"DEVELOPMENT_SUPPORT", "HOOK"}
    assert all(json.loads(r["FACETS"])["END_CLASS"] == "THROUGH_SUPPORT" for r in na)


def test_end_supports_stay_unresolved(delta, summary):
    assert summary["support_end_classes"]["THROUGH_SUPPORT"] == 12
    assert sum(summary["support_end_classes"].values()) == 59 * 2
    for r in delta:
        if r["COMPONENT"].startswith(("DEVELOPMENT_SUPPORT", "HOOK_")) and r["FAMILY"] == "GROUND_BEAM":
            cls = json.loads(r["FACETS"])["END_CLASS"]
            assert (r["NEW_RELEASE_STATE"] == "NOT_APPLICABLE") == (cls == "THROUGH_SUPPORT")
    footing_ends = [r for r in delta if r["COMPONENT"].startswith("DEVELOPMENT_FOOTING")]
    assert footing_ends and all(r["CHANGE_KIND"] == "NO_CHANGE" for r in footing_ends)


def test_unresolved_carries_every_s5_row(delta):
    u = rows(PKG / "S5_1_UNRESOLVED.csv")
    assert len([x for x in u if x["ORIGIN"] == "CARRIED_FROM_S5"]) == \
        len(rows(S5 / "GROUND_SYSTEM_REBAR_UNRESOLVED.csv"))
    assert Counter(x["S5_1_STATUS"] for x in u)["CLOSED (not applicable: through-support)"] == 24


def test_summary_flags(summary):
    assert summary["flags"]["pre_s7_started"] is False and summary["flags"]["verified_created"] is False
    assert summary["flags"]["plotted_scale_used"] is False and summary["s5_1_verified_kg"] == 0.0
    assert summary["sb2"].startswith("SOURCE_CONFLICT")
