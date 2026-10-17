"""Alsenan S6.1 package (research/alsenan_superstructure_beam_rebar_s6_1): a delta release over frozen S6.

Every released number is re-derived here from the frozen S1 schedule section, the note-22 cover and the frozen S6
counts - never against a reference total."""

from __future__ import annotations

import csv
import hashlib
import json
import math
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
PKG = ROOT / "research" / "alsenan_superstructure_beam_rebar_s6_1"
S6 = ROOT / "research" / "alsenan_superstructure_beam_rebar_s6"
S1 = ROOT / "research" / "alsenan_structural_census_s1"
BRIEF_FIELDS = ("FROZEN_BASELINE", "BASELINE_COMPONENT_ID", "OLD_STATE", "OLD_KNOWN_QUANTITY", "NEW_PROJECT_SOURCE",
                "SOURCE_PAGE", "SOURCE_HANDLES", "GRAPHIC_EVIDENCE_CLASS", "NEW_COMPONENT_MODEL",
                "DELTA_KNOWN_QUANTITY", "NEW_BLOCKED_COMPONENTS", "NEW_RELEASE_STATE")
B3S = ("BM-1F_ROOF-B3-BL023-6B9", "BM-GF_ROOF-B3-BL033-6B7")
B26 = "BM-GF_ROOF-B26-BL014-4CC"
STR2_ROWS = ("B17", "B19", "B20", "B21", "B22", "B23", "B24", "B25", "B26")


def J(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def rows(p):
    return list(csv.DictReader(open(p, encoding="utf-8")))


@pytest.fixture(scope="module")
def delta():
    return rows(PKG / "S6_1_DELTA_COMPONENTS.csv")


@pytest.fixture(scope="module")
def summary():
    return J(PKG / "S6_1_RELEASE_SUMMARY.json")


@pytest.fixture(scope="module")
def frozen():
    return {r["record_id"]: r for r in rows(S6 / "SUPERSTRUCTURE_BEAM_COMPONENTS.csv")}


@pytest.fixture(scope="module")
def section():
    defs = {r["definition_id"]: r for r in J(S1 / "BEAM_DEFINITION_REGISTER.json")["rows"]}
    reg = {o["occurrence_id"]: o for o in J(S6 / "SUPERSTRUCTURE_BEAM_OCCURRENCE_REGISTER.json")["occurrences"]}

    def f(oid):
        o = reg[oid]
        d = defs[f"BDEF-{o['mark']}-{o['identity']['SCHEDULE_ROW']}"]
        return d["B_cm"] * 10, d["H_cm"] * 10
    return f


def kgm(d):
    return d * d / 162.0


def core(b, h, d, c=25.0):
    return 2 * (b - 2 * c - d) + 2 * (h - 2 * c - d)


# ------------------------------------------------------------------ package / freeze
def test_deliverables_exist():
    for n in ("S6_1_DELTA_COMPONENTS.csv", "S6_1_STIRRUP_TOPOLOGY.csv", "S6_1_RELEASE_SUMMARY.json",
              "S6_1_UNRESOLVED.csv", "S6_1_PROVENANCE.jsonl", "S6_1_CHANGELOG.md", "S6_1_FREEZE_MANIFEST.json"):
        assert (PKG / n).is_file(), n


def test_s6_1_freeze_manifest_still_matches():
    m = J(PKG / "S6_1_FREEZE_MANIFEST.json")
    assert m["state"] == "FROZEN_BEFORE_S5_1" and m["references_read_before_freeze"] == []
    for group, base in (("code", ROOT), ("inputs", ROOT), ("outputs", PKG)):
        for k, h in m[group].items():
            assert hashlib.sha256((base / k).read_bytes()).hexdigest() == h, (group, k)


def test_frozen_s6_baseline_is_immutable_and_s4_1_preceded(summary):
    m = J(S6 / "S6_FREEZE_MANIFEST.json")
    for group, base in (("code", ROOT), ("inputs", ROOT), ("outputs", S6)):
        for k, h in m[group].items():
            assert hashlib.sha256((base / k).read_bytes()).hexdigest() == h, (group, k)
    fb = summary["context"]["FROZEN_BASELINE"]
    assert fb["manifest_sha256"] == hashlib.sha256((S6 / "S6_FREEZE_MANIFEST.json").read_bytes()).hexdigest()
    s41 = ROOT / "research/alsenan_footing_rebar_s4_1/S4_1_FREEZE_MANIFEST.json"
    assert summary["context"]["PRECEDING_FREEZE_S4_1"]["manifest_sha256"] == \
        hashlib.sha256(s41.read_bytes()).hexdigest()


def test_rebuild_is_byte_identical():
    before = {k: (PKG / k).read_bytes() for k in J(PKG / "S6_1_FREEZE_MANIFEST.json")["outputs"]}
    subprocess.run([sys.executable, "-I", str(PKG / "build_superstructure_beam_rebar_s6_1.py")], check=True,
                   capture_output=True, cwd=ROOT)
    for k, v in before.items():
        assert (PKG / k).read_bytes() == v, k


def test_builder_is_blind_and_registered():
    src = (PKG / "build_superstructure_beam_rebar_s6_1.py").read_text(encoding="utf-8")
    for bad in ("christiannp", "UC4N", "U-C4N", "freelancer", "FREELANCER", "post_freeze", "multi_engine",
                "rebar_truth", "rough_rebar", "fitz", "pymupdf", "pdf_vector_evidence", "kg/m3", "ACI"):
        assert bad not in src, bad
    sys.path.insert(0, str(ROOT / "tests" / "structural_comparison_engine"))
    import rebar_product_registry as RP
    assert "research/alsenan_superstructure_beam_rebar_s6_1/build_superstructure_beam_rebar_s6_1.py" in \
        RP.ACCURATE_BUILDERS
    assert "engine/source/link_geometry.py" in RP.ACCURATE_MODULES


# ------------------------------------------------------------------ delta shape and conservation
def test_every_frozen_component_is_covered_once_with_brief_fields(delta, frozen):
    assert set(BRIEF_FIELDS) <= set(delta[0])
    groups = defaultdict(list)
    for r in delta:
        groups[r["BASELINE_COMPONENT_ID"]].append(r)
    assert set(groups) == set(frozen)
    for cid, rs in groups.items():
        assert sum(1 for r in rs if r["PRIMARY"] == "Y") == 1, cid


def test_delta_conservation(delta, summary):
    s6 = J(S6 / "SUPERSTRUCTURE_BEAM_RELEASE_SUMMARY.json")
    frozen_known = s6["known_source_derived_superstructure_beam_rebar_kg"]
    assert abs(sum(float(r["OLD_KNOWN_QUANTITY"]) for r in delta) - frozen_known) < 1e-3
    d = sum(float(r["DELTA_KNOWN_QUANTITY"]) for r in delta)
    assert abs(d - summary["delta_known_kg"]) < 1e-3 and d > 0
    assert all(float(r["DELTA_KNOWN_QUANTITY"]) >= 0 for r in delta)
    assert abs(summary["s6_1_known_kg"] - frozen_known - summary["delta_known_kg"]) < 1e-9
    k = summary["delta_by_kind_kg"]
    assert abs(sum(k.values()) - summary["delta_known_kg"]) < 1e-9
    assert summary["conservation"]["all_pass"]
    assert not [r for r in delta if r["NEW_RELEASE_STATE"] == "VERIFIED"]
    assert all(r["NEW_RELEASE_STATE"] == "LOWER_BOUND" for r in delta if float(r["DELTA_KNOWN_QUANTITY"]) > 0)


def test_no_kg_from_shape_only_nts_or_unevidenced_derivation(delta):
    for r in delta:
        if float(r["DELTA_KNOWN_QUANTITY"]) > 0:
            assert r["QUANTITY_BASIS"] in ("GRAPHIC_SOURCE_GEOMETRY_DERIVATION", "SCHEDULE_AND_PLAN_GEOMETRY")
            if r["QUANTITY_BASIS"] == "GRAPHIC_SOURCE_GEOMETRY_DERIVATION":
                assert r["GRAPHIC_EVIDENCE_CLASS"] == "GRAPHIC_DERIVED_FROM_SOURCE_GEOMETRY"
        if r["GRAPHIC_EVIDENCE_CLASS"] == "GRAPHIC_NTS_OR_UNDIMENSIONED":
            assert float(r["DELTA_KNOWN_QUANTITY"]) == 0


# ------------------------------------------------------------------ links
def test_single_link_core_path_lower_bound(delta, section, frozen):
    cores = [r for r in delta if r["PORTION"] == "CORE_PATH" and r["CHANGE_KIND"] == "QUANTITY_RELEASED"]
    single = [r for r in cores if json.loads(r["FACETS"])["TOPOLOGY"] == "SINGLE_CLOSED_LINK_2_LEG"]
    assert len(single) == 80
    for r in single:
        b, h = section(r["OCCURRENCE_ID"])
        d = float(r["DIA_MM"])
        f = json.loads(r["FACETS"])
        assert abs(f["CORE_PATH_MM"] - core(b, h, d)) < 1e-9
        assert abs(float(r["DELTA_KNOWN_QUANTITY"]) - f["COUNT"] * core(b, h, d) / 1000 * kgm(d)) < 1e-5
        assert r["GRAPHIC_EVIDENCE_CLASS"] == "GRAPHIC_DERIVED_FROM_SOURCE_GEOMETRY"
        assert r["MARK"] not in STR2_ROWS
        hook = [x for x in delta if x["BASELINE_COMPONENT_ID"] == r["BASELINE_COMPONENT_ID"] and
                x["PORTION"] == "HOOK_EXTENSION"]
        assert len(hook) == 1 and hook[0]["PORTION_STATE"] == "SHAPE_FOUND_LENGTH_BLOCKED"
        assert float(hook[0]["NEW_KNOWN_QUANTITY"]) == 0


def test_core_path_released_only_with_a_released_count(delta):
    counts = {}
    for r in rows(S6 / "SUPERSTRUCTURE_BEAM_STIRRUP_COUNTS.csv"):
        if r["state"] == "LOWER_BOUND":
            counts[(r["occurrence_id"], r["span_index"])] = int(r["count_lower_bound"])
    for r in delta:
        if r["COMPONENT"] == "STIRRUP_COUNT" and r["CHANGE_KIND"] == "QUANTITY_RELEASED":
            counts[(r["OCCURRENCE_ID"], r["SPAN_INDEX"])] = int(r["DELTA_COUNT"])
    for r in delta:
        if r["PORTION"] == "CORE_PATH":
            key = (r["OCCURRENCE_ID"], r["SPAN_INDEX"])
            if r["CHANGE_KIND"] == "QUANTITY_RELEASED":
                assert json.loads(r["FACETS"])["COUNT"] == counts[key]
            else:
                assert key not in counts and float(r["NEW_KNOWN_QUANTITY"]) == 0


def test_str2_topology_four_legs_outer_link_only(delta, section, summary):
    assert summary["str2_icon"]["legs"] == 4 and summary["str2_icon"]["links"] == 2
    assert summary["str2_icon"]["inner_levels_shared"] is False
    str2 = [r for r in delta if r["PORTION"] == "CORE_PATH" and r["MARK"] in STR2_ROWS]
    assert len(str2) == 8
    for r in str2:
        f = json.loads(r["FACETS"])
        assert f["TOPOLOGY"] == "STR2_OUTER_PLUS_ONE_INNER_4_LEG"
        b, h = section(r["OCCURRENCE_ID"])
        assert abs(f["CORE_PATH_MM"] - core(b, h, float(r["DIA_MM"]))) < 1e-9     # outer link only
    topo = [t for t in rows(PKG / "S6_1_STIRRUP_TOPOLOGY.csv") if t["MARK"] in STR2_ROWS]
    assert topo and all(t["LEGS"] == "4" and t["LINKS"] == "2" for t in topo)


def test_str3_topology_six_legs(summary):
    s3 = summary["str3_icon"]
    assert (s3["links"], s3["legs"], s3["topology"]) == (3, 6, "STR3_OUTER_PLUS_TWO_INNER_6_LEG")


def test_inner_link_stays_unresolved(delta):
    inner = [r for r in delta if r["PORTION"] == "INNER_LINK"]
    assert len(inner) == 8
    for r in inner:
        assert r["PORTION_STATE"] == "SHAPE_FOUND_LENGTH_BLOCKED" and float(r["NEW_KNOWN_QUANTITY"]) == 0
        assert r["GRAPHIC_EVIDENCE_CLASS"] == "GRAPHIC_EXPLICIT_SHAPE_ONLY" and "no equal subdivision" in \
            r["NEW_COMPONENT_MODEL"]


def test_cb_downward_end_leg_recorded_not_released(delta, summary):
    legs = [r for r in delta if r["SUBFAMILY"] == "CONTINUOUS_BEAM" and r["COMPONENT"] in ("HOOK_1", "HOOK_2")
            and r["CHANGE_KIND"] == "TOPOLOGY_RECORDED"]
    assert len(legs) == 14
    for r in legs:
        f = json.loads(r["FACETS"])
        assert f["LEG_SHAPE"].startswith("SOURCE_FOUND") and f["BAR_ROLE"] == "CONFLICT (Q2)"
        assert f["COUNT_DIAMETER_INVARIANT"] is False and float(r["NEW_KNOWN_QUANTITY"]) == 0
        assert r["NEW_RELEASE_STATE"] == "BLOCKED_UNQUANTIFIED"
    prov = {json.loads(x)["delta_id"]: json.loads(x) for x in
            (PKG / "S6_1_PROVENANCE.jsonl").read_text(encoding="utf-8").splitlines()}
    for r in legs:
        assert prov[r["DELTA_ID"]]["derivation_conditions"]["NO_CONTRADICTING_PROJECT_SOURCE"] is False
    assert summary["cb_end_legs"]["released"] == 0


# ------------------------------------------------------------------ B3 / B26 / CB7
def test_b3_with_stair_base_release(delta):
    for o in B3S:
        rs = {(r["COMPONENT"], r["PORTION"]): r for r in delta if r["OCCURRENCE_ID"] == o}
        top, bot = rs[("TOP_MAIN", "STRAIGHT_RUN")], rs[("BOTTOM_MAIN", "STRAIGHT_RUN")]
        assert abs(float(top["DELTA_KNOWN_QUANTITY"]) - 2 * 2.5 * kgm(12)) < 1e-6
        assert abs(float(bot["DELTA_KNOWN_QUANTITY"]) - 4 * 2.5 * kgm(16)) < 1e-6
        assert int(rs[("STIRRUP_COUNT", "WHOLE_COMPONENT")]["DELTA_COUNT"]) == math.ceil(6 * 2.5)
        cp = rs[("STIRRUP_CORE_PATH", "CORE_PATH")]
        assert abs(float(cp["DELTA_KNOWN_QUANTITY"]) - 15 * core(200, 400, 8) / 1000 * kgm(8)) < 1e-6
        assert rs[("OTHER_EXPLICIT_EXTRA", "WHOLE_COMPONENT")]["NEW_RELEASE_STATE"] == "NOT_APPLICABLE"
        for p in ("CRANK_EXCESS", "END_BENDS"):
            assert float(rs[("TOP_MAIN", p)]["NEW_KNOWN_QUANTITY"]) == 0
        for c in ("HOOK_1", "HOOK_2", "DEVELOPMENT_1", "DEVELOPMENT_2"):
            assert rs[(c, "WHOLE_COMPONENT")]["NEW_RELEASE_STATE"] == "BLOCKED_UNQUANTIFIED"
    cb3 = [r for r in delta if r["OCCURRENCE_ID"] == "CBO-GFRS-CB3-BL022"]
    assert cb3 and all(r["CHANGE_KIND"] == "NO_CHANGE" for r in cb3)          # CB3 vs B3 stays a conflict


def test_b26_base_vs_planted_column_extra(delta, summary):
    rs = {(r["COMPONENT"], r["PORTION"]): r for r in delta if r["OCCURRENCE_ID"] == B26}
    assert abs(float(rs[("TOP_MAIN", "STRAIGHT_RUN")]["DELTA_KNOWN_QUANTITY"]) - 6 * 7.338 * kgm(14)) < 1e-6
    assert abs(float(rs[("BOTTOM_MAIN", "STRAIGHT_RUN")]["DELTA_KNOWN_QUANTITY"]) - 19 * 7.338 * kgm(18)) < 1e-6
    assert int(rs[("STIRRUP_COUNT", "WHOLE_COMPONENT")]["DELTA_COUNT"]) == 74
    assert abs(float(rs[("STIRRUP_CORE_PATH", "CORE_PATH")]["DELTA_KNOWN_QUANTITY"]) -
               74 * core(650, 850, 10) / 1000 * kgm(10)) < 1e-6
    ex = rs[("OTHER_EXPLICIT_EXTRA", "STRAIGHT_PROJECTION")]
    f = json.loads(ex["FACETS"])
    assert (f["COUNT_TOTAL"], f["DIA_MM"], f["DEPTH_MM"], f["COLUMN_WIDTH_LB_MM"]) == (4, 16, 850.0, 200.0)
    assert f["ROW_ALLOCATION"].startswith("NOT_ESTABLISHED")
    assert abs(float(ex["DELTA_KNOWN_QUANTITY"]) - 4 * (2 * 850 + 200) / 1000 * kgm(16)) < 1e-6
    for p in ("CRANK_DIAGONAL_EXCESS", "END_HOOK_1", "END_HOOK_2"):
        assert float(rs[("OTHER_EXPLICIT_EXTRA", p)]["NEW_KNOWN_QUANTITY"]) == 0
    assert rs[("SIDE_REBAR", "WHOLE_COMPONENT")]["NEW_RELEASE_STATE"] == "BLOCKED_UNQUANTIFIED"
    assert summary["b26"]["base_kg"] > 0
    assert abs(summary["b26"]["planted_column_extra_kg"] - float(ex["DELTA_KNOWN_QUANTITY"])) < 1e-5


def test_cb7_invariant_stirrup_count(delta, summary):
    cb7 = {r["SPAN_INDEX"]: r for r in delta if r["OCCURRENCE_ID"] == "CBO-GFRS-CB7-BL003" and
           r["COMPONENT"] == "STIRRUP_COUNT"}
    assert int(cb7["1"]["DELTA_COUNT"]) == 39 == math.ceil(7 * 5.45)
    assert int(cb7["2"]["DELTA_COUNT"]) == 41 == math.ceil(7 * 5.75)
    assert all(json.loads(r["FACETS"])["READINGS"] == ["FORWARD", "REVERSED"] for r in cb7.values())
    tested = {(t["occurrence_id"], t["span_index"]): t["invariant"] for t in summary["cb_invariance_tested"]}
    assert tested[("CBO-FFRS-CB13-BL004", 1)] is False and tested[("CBO-GFRS-CB7-BL003", 1)] is True
    cb13 = [r for r in delta if r["OCCURRENCE_ID"] == "CBO-FFRS-CB13-BL004" and r["COMPONENT"] == "STIRRUP_COUNT"]
    assert all(r["CHANGE_KIND"] == "NO_CHANGE" for r in cb13)


def test_brief_20_conflicts_untouched(delta):
    for o in ("BM-1F_ROOF-B6-BL014-6C5", "BM-GF_ROOF-B21-BL001-468", "BM-GF_ROOF-B29-BL039-465",
              "CBO-FFRS-CB10-BL001", "CBO-GFRS-CB2-BL038", "CBO-GFRS-CB4-BL016", "CBO-GFRS-CB5-BL008",
              "CBO-GFRS-CB8-BL024", "CBO-GFRS-CB3-BL022"):
        rs = [r for r in delta if r["OCCURRENCE_ID"] == o]
        assert rs and all(r["CHANGE_KIND"] == "NO_CHANGE" for r in rs), o


def test_unresolved_carries_every_s6_row_and_new_portions(delta):
    u = rows(PKG / "S6_1_UNRESOLVED.csv")
    carried = [x for x in u if x["ORIGIN"] == "CARRIED_FROM_S6"]
    assert len(carried) == len(rows(S6 / "SUPERSTRUCTURE_BEAM_UNRESOLVED.csv"))
    new = {(x["BASELINE_COMPONENT_ID"], x["PORTION"]) for x in u if x["ORIGIN"] == "NEW_IN_S6_1"}
    for r in delta:
        if r["PRIMARY"] == "N" and r["PORTION_STATE"] in ("SHAPE_FOUND_LENGTH_BLOCKED", "BLOCKED_UNQUANTIFIED"):
            assert (r["BASELINE_COMPONENT_ID"], r["PORTION"]) in new
    assert Counter(x["S6_1_STATUS"] for x in carried)["CLOSED (not applicable)"] == 2


def test_summary_flags(summary):
    assert summary["flags"] == {"frozen_outputs_changed": False, "plotted_scale_used": False,
                                "kg_from_shape_only_graphic": False, "verified_created": False,
                                "equal_inner_link_subdivision": False, "pre_s7_started": False,
                                "references_read": []}
    assert summary["s6_1_verified_kg"] == 0.0
