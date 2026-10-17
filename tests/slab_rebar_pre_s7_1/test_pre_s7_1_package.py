"""PRE-S7.1 / AD2 package (research/alsenan_slab_rebar_pre_s7_1): slab QTO authority over frozen PRE-S7, no kg.

Claims are re-derived here from the package's own registers, the frozen PRE-S7 registers and the frozen S1 panel
polygons - never against a reference total."""

from __future__ import annotations

import csv
import hashlib
import json
import math
import re
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path

import pytest

from engine.source import delta_release as DR
from engine.source import slab_qto_authority as Q
from engine.source import slab_rebar_readiness as SR

ROOT = Path(__file__).resolve().parents[2]
PKG = ROOT / "research" / "alsenan_slab_rebar_pre_s7_1"
PRE = ROOT / "research" / "alsenan_slab_rebar_pre_s7"
R = ROOT / "research"
S1 = R / "alsenan_structural_census_s1"
BUILDER = "research/alsenan_slab_rebar_pre_s7_1/build_pre_s7_1.py"
FROZEN = {"S4": R / "alsenan_footing_rebar_s4" / "S4_FREEZE_MANIFEST.json",
          "S4.1": R / "alsenan_footing_rebar_s4_1" / "S4_1_FREEZE_MANIFEST.json",
          "S5": R / "alsenan_ground_system_rebar_s5" / "S5_FREEZE_MANIFEST.json",
          "S6": R / "alsenan_superstructure_beam_rebar_s6" / "S6_FREEZE_MANIFEST.json",
          "S6.1": R / "alsenan_superstructure_beam_rebar_s6_1" / "S6_1_FREEZE_MANIFEST.json",
          "S5.1": R / "alsenan_ground_system_rebar_s5_1" / "S5_1_FREEZE_MANIFEST.json",
          "AD1": R / "ad1_authority_decisions" / "AD1_FREEZE_MANIFEST.json",
          "D1.1": R / "d1_1_stirrup_authority_audit" / "D1_1_FREEZE_MANIFEST.json",
          "D1.2": R / "d1_2_footing_cover_audit" / "D1_2_FREEZE_MANIFEST.json",
          "PRE-S7": PRE / "PRE_S7_FREEZE_MANIFEST.json"}
OUTPUTS = ["00_README.md", "01_AD2_DECISIONS.json", "02_OWNERSHIP_TRANSFERS.csv", "03_RATE_QTO_REGISTER.csv",
           "04_50_PERCENT_CURTAILMENT_REGISTER.csv", "05_TOP_RULE_IDENTITY.csv", "06_SUPPORT_MISMATCH_SPLITS.csv",
           "07_LOCAL_BAR_STRIPS.csv", "08_UPDATED_COMPONENT_READINESS.csv", "09_REMAINING_CONFLICTS.csv",
           "10_REMAINING_BLOCKERS.csv", "11_S7_RELEASE_CANDIDATES.csv", "12_PROVENANCE.jsonl",
           "PRE_S7_1_SUMMARY.json"]


def J(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def rows(name, base=PKG):
    with open(base / name, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def js(v):
    return json.loads(v) if v not in ("", None) else None


def f(v):
    return float(v) if v not in ("", None) else None


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


@pytest.fixture(scope="module")
def summary():
    return J(PKG / "PRE_S7_1_SUMMARY.json")


@pytest.fixture(scope="module")
def items():
    return rows("11_S7_RELEASE_CANDIDATES.csv") + rows("10_REMAINING_BLOCKERS.csv")


@pytest.fixture(scope="module")
def cands():
    return rows("11_S7_RELEASE_CANDIDATES.csv")


@pytest.fixture(scope="module")
def blocked():
    return rows("10_REMAINING_BLOCKERS.csv")


@pytest.fixture(scope="module")
def ready():
    return rows("08_UPDATED_COMPONENT_READINESS.csv")


@pytest.fixture(scope="module")
def census():
    return {c["SLAB_PANEL_ID"]: c for c in rows("01_SLAB_PANEL_CENSUS.csv", PRE)}


@pytest.fixture(scope="module")
def s1():
    return {r["panel_id"]: r for r in J(S1 / "SLAB_PANEL_REGISTER.json")["rows"]}


# ------------------------------------------------------------------ package / freeze / blindness
def test_deliverables_exist():
    for n in OUTPUTS + ["TEST_RUN.md", "PRE_S7_1_FREEZE_MANIFEST.json"]:
        assert (PKG / n).is_file(), n


def test_freeze_manifest_still_matches():
    m = J(PKG / "PRE_S7_1_FREEZE_MANIFEST.json")
    assert m["round"] == "PRE-S7.1" and m["state"] == "FROZEN" and set(m["outputs"]) == set(OUTPUTS)
    v = DR.verify_frozen(PKG / "PRE_S7_1_FREEZE_MANIFEST.json", ROOT)
    assert v["files_checked"] == len(m["code"]) + len(m["inputs"]) + len(m["outputs"])


def test_frozen_stages_including_pre_s7_are_immutable(summary):
    m = J(PKG / "PRE_S7_1_FREEZE_MANIFEST.json")
    for k, p in FROZEN.items():
        DR.verify_frozen(p, ROOT)
        assert m["frozen_baselines"][k] == sha(p), k
        assert summary["frozen"][k]["manifest_sha256"] == sha(p)
    pre = J(FROZEN["PRE-S7"])["outputs"]
    for name in ("04_COMPONENT_READINESS.csv", "05_SUPPORT_REGISTER.csv", "01_SLAB_PANEL_CENSUS.csv"):
        assert sha(PRE / name) == pre[name]


def test_rebuild_is_byte_identical():
    before = {o: sha(PKG / o) for o in OUTPUTS}
    subprocess.run([sys.executable, "-I", str(ROOT / BUILDER)], check=True, capture_output=True, cwd=ROOT)
    assert {o: sha(PKG / o) for o in OUTPUTS} == before


def test_builder_is_blind_and_registered():
    src = (ROOT / BUILDER).read_text(encoding="utf-8")
    for bad in ("christiannp", "UC4N", "U-C4N", "freelancer", "FREELANCER", "Chris", "post_freeze", "multi_engine",
                "rebar_truth", "rough_rebar", "fitz", "pymupdf", "pdf_vector_evidence", "kg/m", "BS 8666",
                "Eurocode", "EN 1992", "d * d / 162", "/ 162"):
        assert bad not in src, bad
    assert not re.search(r"\bACI\b", src)
    sys.path.insert(0, str(ROOT / "tests" / "structural_comparison_engine"))
    import rebar_product_registry as RP
    assert BUILDER in RP.ACCURATE_BUILDERS
    assert "engine/source/slab_qto_authority.py" in RP.ACCURATE_MODULES


# ------------------------------------------------------------------ §19 conservation
def test_every_pre_s7_component_terminates_once(ready):
    pre = [c["COMPONENT_ID"] for c in rows("04_COMPONENT_READINESS.csv", PRE)]
    mine = [r["COMPONENT_ID"] for r in ready if r["NEW_IN_AD2"] == "False"]
    assert sorted(pre) == sorted(mine) and len(set(mine)) == len(mine) == 440
    allowed = {"RELEASED_ALL", "RELEASED_PARTIAL", "BLOCKED", Q.TRANSFERRED_S8}
    assert {r["AD2_STATE"] for r in ready} <= allowed


def test_item_parents_and_component_states(items, ready):
    trans = rows("02_OWNERSHIP_TRANSFERS.csv")
    t_items = {t["object_id"] for t in trans}
    by = defaultdict(list)
    for i in items:
        by[i["PARENT_COMPONENT_ID"]].append(i["LANE"])
    for r in ready:
        lanes = by[r["COMPONENT_ID"]] + (["TRANSFERRED_S8"] * int(r["TRANSFERRED_ITEMS"]))
        assert int(r["ITEMS"]) == len(lanes), r["COMPONENT_ID"]
        assert int(r["RELEASED_ITEMS"]) == sum(x in Q.RELEASED_LANES for x in lanes)
        if r["AD2_STATE"] == Q.TRANSFERRED_S8:
            assert r["COMPONENT_ID"] in t_items and not by[r["COMPONENT_ID"]]
        if r["AD2_STATE"] == "RELEASED_ALL":
            assert all(x in Q.RELEASED_LANES for x in by[r["COMPONENT_ID"]])


def test_ownership_transfer_loses_nothing(ready, cands, summary):
    trans = rows("02_OWNERSHIP_TRANSFERS.csv")
    assert all(t["quantity_lost"] == "False" and t["state"] == Q.TRANSFERRED_S8 for t in trans)
    regions = {t["region"] for t in trans}
    assert "WATER_TANK_SUPPORT_REGION" in regions and "STAIR_LIGHTWELL_REGION" in regions
    panels = {t["object_id"]: t for t in trans if t["kind"] == "PANEL"}
    assert set(panels) == {"SP-2F_ROOF_SLAB-01", "SP-2F_ROOF_SLAB-02", "SP-GF_ROOF_SLAB-21"}
    assert panels["SP-GF_ROOF_SLAB-21"]["source_conflict_preserved"] == "True"
    assert panels["SP-2F_ROOF_SLAB-01"]["region"] == "WATER_TANK_SUPPORT_REGION"
    for r in ready:
        if r["OWNER"] in panels:
            assert r["AD2_STATE"] == Q.TRANSFERRED_S8, r["COMPONENT_ID"]
    s8 = set(panels)
    assert not [c for c in cands if c["OWNER"] in s8 or set(c["SIDE_PANEL"].split("|")) & s8 or c["S8_REGION"]]
    tok = {t["object_id"].split()[1] for t in trans if t["kind"] == "TOKEN"}
    assert {"5BC", "7A7", "7A8", "796", "798"} <= tok           # the light-well and tank callouts went with them


def test_rate_density_is_unrounded_and_never_plus_one():
    rr = rows("03_RATE_QTO_REGISTER.csv")
    released = [r for r in rr if r["LANE"] in Q.RELEASED_LANES]
    assert released and all(r["COUNT_BASIS"] == Q.COUNT_RATE_DENSITY for r in rr)
    for r in released:
        eq = f(r["RATE_PER_M"]) * f(r["DENSITY_FRACTION"]) * f(r["DISTRIBUTION_WIDTH_MM"]) / 1000.0
        assert abs(f(r["EQUIVALENT_BAR_COUNT"]) - eq) <= 1e-8 * max(1.0, eq), r["QTO_ITEM_ID"]
        assert r["PHYSICAL_BBS_BAR_COUNT"] == Q.UNRESOLVED
    assert any(abs(f(r["EQUIVALENT_BAR_COUNT"]) - round(f(r["EQUIVALENT_BAR_COUNT"]))) > 1e-3 for r in released)


def test_released_density_never_exceeds_one_and_covers_each_strip(cands, s1):
    """Per family: continuing-half + full-density widths = the curtailed-half + full-density widths = all strips."""
    strips = rows("07_LOCAL_BAR_STRIPS.csv")
    width = defaultdict(float)
    for x in strips:
        width[(x["PANEL"], x["BAR_DIRECTION"])] += f(x["STRIP_WIDTH_MM"])
    fam = defaultdict(lambda: defaultdict(float))
    for c in cands:
        if c["ITEM"] in ("BOTTOM_IN_PANEL", "BOTTOM_IN_PANEL_CONTINUING", "BOTTOM_IN_PANEL_CURTAILED"):
            fam[(c["OWNER"], c["DIRECTION"])][c["ITEM"]] += f(c["DISTRIBUTION_WIDTH_MM"])
    assert fam
    for k, v in fam.items():
        full = v["BOTTOM_IN_PANEL"]
        assert abs(full + v["BOTTOM_IN_PANEL_CONTINUING"] - width[k]) <= 0.5, k
        assert abs(full + v["BOTTOM_IN_PANEL_CURTAILED"] - width[k]) <= 0.5, k


def test_fifty_plus_fifty_is_one_hundred(cands):
    reg = rows("04_50_PERCENT_CURTAILMENT_REGISTER.csv")
    assert len(reg) == 70
    for r in reg:
        assert f(r["CONTINUOUS_DENSITY_FRACTION"]) + f(r["CURTAILED_DENSITY_FRACTION"]) == 1.0
        assert r["QTO_BASIS"] == Q.DENSITY_50_50 and r["PHYSICAL_SEQUENCING"] == Q.UNRESOLVED
        assert r["WHICH_50_PERCENT_SOURCE"] == "NOT_STATED"
    halves = [c for c in cands if c["ITEM"] in ("BOTTOM_IN_PANEL_CONTINUING", "BOTTOM_IN_PANEL_CURTAILED")]
    assert halves and all(f(c["DENSITY_FRACTION"]) == 0.5 for c in halves)


def test_curtailed_half_is_shortened_by_0125_L_on_rectangles(cands, census):
    """On a rectangular panel every bar line has run L; the continuing half runs L, the curtailed half
    L (1 - 0.125 n) with n the curtailing ends - so the curtailed mean run is L - 0.125 L x (0, 1 or 2)."""
    n = 0
    for c in cands:
        p = census.get(c["OWNER"])
        if not p or p["SPAN_STATE"] != "SINGLE_VALUED_FACE_TO_FACE" or f(p["RECTANGULARITY"]) < 0.9999:
            continue
        L = f(p["CLEAR_SPAN_X_MM"] if c["DIRECTION"] == "X" else p["CLEAR_SPAN_Y_MM"])
        if c["ITEM"] in ("BOTTOM_IN_PANEL", "BOTTOM_IN_PANEL_CONTINUING"):
            assert abs(f(c["MEAN_RUN_MM"]) - L) <= 1.0, c["QTO_ITEM_ID"]
            n += 1
        elif c["ITEM"] == "BOTTOM_IN_PANEL_CURTAILED":
            k = (L - f(c["MEAN_RUN_MM"])) / (0.125 * L)
            assert -0.01 <= k <= 2.01, c["QTO_ITEM_ID"]
            n += 1
    assert n > 50


def test_top_extension_is_one_third_of_the_local_span(cands, census):
    ext = [c for c in cands if c["ITEM"] == "TOP_EXTENSION"]
    assert ext and all("AD2-D06" in js(c["AUTHORITY"]) and js(c["EXTENT_BASES"]) == [Q.EXTENT_URBAN_RULE]
                       for c in ext)
    checked = 0
    for c in ext:
        p = census[c["SIDE_PANEL"]]
        if p["SPAN_STATE"] == "SINGLE_VALUED_FACE_TO_FACE" and f(p["RECTANGULARITY"]) >= 0.9999:
            L = f(p["CLEAR_SPAN_X_MM"] if c["DIRECTION"] == "X" else p["CLEAR_SPAN_Y_MM"])
            assert abs(f(c["MEAN_RUN_MM"]) - L / 3.0) <= 0.5, c["QTO_ITEM_ID"]
            assert f(c["RATE_PER_M"]) == 5 and int(c["DIA_MM"]) == 10
            checked += 1
    assert checked > 50


def test_local_strips_reconcile_to_panel_geometry(s1, census):
    strips = rows("07_LOCAL_BAR_STRIPS.csv")
    integ = defaultdict(float)
    for x in strips:
        integ[(x["PANEL"], x["BAR_DIRECTION"])] += f(x["RUN_INTEGRAL_M2"])
    ins = [p for p, c in census.items() if c["SCOPE"] == SR.IN_SCOPE]
    assert {p for p, _ in integ} == set(ins)
    for p in ins:
        ring = s1[p]["polygon_mm"]
        area = Q.polygon_area(ring) - sum(Q.polygon_area(h) for h in s1[p]["holes_mm"] or [])
        for d in ("X", "Y"):
            assert abs(integ[(p, d)] - area / 1e6) <= 1e-4 * max(1.0, area / 1e6), (p, d)


def test_irregular_panels_use_local_bar_lines(cands, census, summary):
    irr = {p for p, c in census.items() if c["SCOPE"] == SR.IN_SCOPE and c["SPAN_STATE"] != "SINGLE_VALUED_FACE_TO_FACE"}
    assert summary["irregular_panels"] == len(irr) == 16
    got = {c["OWNER"] for c in cands if c["OWNER"] in irr} | {c["SIDE_PANEL"] for c in cands if c["SIDE_PANEL"] in irr}
    assert got == irr
    strips = rows("07_LOCAL_BAR_STRIPS.csv")
    assert all(x["MEASUREMENT_RULE"] == Q.URBAN_LOCAL_BAR_LINE_RULE for x in strips if x["PANEL"] in irr)
    for c in cands:
        if c["OWNER"] in irr and c["ITEM"] == "BOTTOM_IN_PANEL_CURTAILED":
            assert "AD2-D14" in js(c["AUTHORITY"])


def test_mismatch_splits_do_not_overlap(cands, blocked):
    splits = rows("06_SUPPORT_MISMATCH_SPLITS.csv")
    assert splits
    keys = {(s["SUPPORT_ID"], s["LEFT_PANEL"], s["RIGHT_PANEL"], s["BAR_DIRECTION"]) for s in splits}
    for c in cands:
        if c["ITEM"] == "BOTTOM_SUPPORT_CROSSING":
            a, b = c["SIDE_PANEL"].split("|")
            assert (c["SUPPORT_ID"], a, b, c["DIRECTION"]) not in keys
    for s in splits:
        assert set(js(s["BLOCKED"])) == set(Q.TRANSITION_PARTS) and s["CROSSING_ITEM"] == "NONE"
        assert s["CHOSEN_BY"].startswith("NOTHING")
    trans = {b["SUPPORT_ID"] for b in blocked if b["ITEM"] == "BOTTOM_TRANSITION"}
    assert {s["SUPPORT_ID"] for s in splits} <= trans


def test_crossings_are_counted_once(cands):
    seen = Counter((c["ITEM"], c["SUPPORT_ID"], c["DIRECTION"], frozenset(c["SIDE_PANEL"].split("|")))
                   for c in cands if c["ITEM"].endswith("SUPPORT_CROSSING"))
    assert seen and all(v == 1 for v in seen.values())
    for c in cands:
        if c["ITEM"].endswith("SUPPORT_CROSSING"):
            a, b = c["SIDE_PANEL"].split("|")
            assert a < b                                           # from the lower-id face only
            assert 0 < f(c["MEAN_RUN_MM"]) < 1500


def test_local_top_override_supersedes_the_general_rule(items):
    ident = rows("05_TOP_RULE_IDENTITY.csv")
    ov = [r for r in ident if r["RULE_A"].startswith("token 1824")]
    assert len(ov) == 1 and ov[0]["OVERRIDDEN_STATE"] == Q.GENERAL_RULE_SUPERSEDED_FOR_ROLE
    assert "LOCAL_SOURCE_OVERRIDE" in ov[0]["GOVERNING"] and ov[0]["SUMMED"] == "False"
    sid = ov[0]["LOCATION"]
    at = [i for i in items if i["SUPPORT_ID"] == sid and i["ITEM"].startswith("TOP_")]
    assert [i["ITEM"] for i in at] == ["TOP_LOCAL_OVERRIDE_GROUP"]
    assert at[0]["EXPLICIT_COUNT"] == "3" and at[0]["COUNT_RELEASED"] == "True"
    assert at[0]["LANE"] == Q.BLOCKED_UNQUANTIFIED and at[0]["COUNT_BASIS"] == Q.COUNT_SOURCE_EXPLICIT


def test_top_rule_identity_same_family_note_governs():
    ident = {r["RULE_A"]: r for r in rows("05_TOP_RULE_IDENTITY.csv")}
    for rid in ("P15-TOP-NONCONT-0.25L1", "P15-TOP-CONT-0.30Lmax", "P15-TOP-EXTEND-50PCT"):
        r = ident[rid]
        assert r["IDENTITY"] == Q.SAME_FAMILY and r["GOVERNING"] == "P4-6-NOTE-2-TOP-OVER-BEAMS"
        assert js(r["OVERRIDDEN"]) == [rid] and r["OVERRIDDEN_STATE"] == Q.OVERRIDDEN_PROJECT_SOURCE
        assert r["SUMMED"] == "False"
    o = ident["P4-6-NOTE-2-TOP-OVER-BEAMS"]
    assert o["GOVERNING"] == Q.URBAN_TOP_EXTENT_RULE and Q.URBAN_OWNER_MEASUREMENT_RULE in o["AUTHORITY"]
    for t in ("token 79F (4%%C16/Top)", "token 7A2 (5%%C18/Top)"):
        assert ident[t]["IDENTITY"] == Q.IDENTITY_UNRESOLVED


def test_temperature_stays_blocked_and_separate(items, ready):
    temp = [r for r in ready if r["COMPONENT"].startswith("TEMPERATURE")]
    assert len(temp) == 98
    blocked_t = [r for r in temp if r["AD2_STATE"] == "BLOCKED"]
    assert len(blocked_t) == 94 and all(r["ITEMS"] == "1" for r in temp)
    assert all(js(r["QUESTIONS"]) == ["Q-TEMP"] for r in blocked_t)
    ti = [i for i in items if i["ITEM"] == "TEMPERATURE"]
    assert all(i["LANE"] == Q.BLOCKED_UNQUANTIFIED for i in ti)
    owners = {r["OWNER"] for r in blocked_t}                   # temperature blocked, the panel's bottom released
    rel_owners = {i["OWNER"] for i in items if i["LANE"] in Q.RELEASED_LANES and i["ITEM"].startswith("BOTTOM_IN")}
    assert len(owners & rel_owners) > 30


def test_sunken_mesh_retained_and_extras_blocked(items, census, summary):
    sunken = {p for p, c in census.items() if c["PANEL_CLASS"] == "SUNKEN_SLAB"}
    assert len(sunken) == 6 and set(summary["sunken_mesh"]) == sunken
    assert set(summary["sunken_mesh"].values()) == {"RETAINED_IN_S7"}
    for p in sunken:
        ex = [i for i in items if i["OWNER"] == p and i["ITEM"] in Q.SUNKEN_EXTRAS]
        assert sorted(i["ITEM"] for i in ex) == sorted(Q.SUNKEN_EXTRAS)
        assert all(i["LANE"] == Q.BLOCKED_UNQUANTIFIED for i in ex)
        assert any(i["OWNER"] == p and i["LANE"] in Q.RELEASED_LANES for i in items)


def test_dense_hatch_classified_by_geometry(summary):
    assert set(summary["dense_hatch"].values()) <= {Q.BEARING_WALL_CANDIDATE, Q.CANTILEVER_CANDIDATE,
                                                    SR.CLASSIFICATION_BLOCKED}
    lines = [json.loads(x) for x in (PKG / "12_PROVENANCE.jsonl").read_text(encoding="utf-8").splitlines()]
    hz = [x["record"] for x in lines if x["kind"] == "HATCH"]
    assert len(hz) == 8
    for h in hz:
        if h["state"] == Q.BEARING_WALL_CANDIDATE:
            assert min(h["evidence"]["line_cover"].values()) >= 0.8


def test_explicit_counts_release_with_blocked_lengths(items):
    corner = [i for i in items if i["ITEM"] == "CORNER_GROUP"]
    assert len(corner) == 4
    assert all(i["EXPLICIT_COUNT"] == "3" and i["COUNT_RELEASED"] == "True" and i["LANE"] == Q.BLOCKED_UNQUANTIFIED
               for i in corner)
    fam = [i for i in items if i["ITEM"] == "FAMILY_BLOCKED"]
    assert Counter(js(i["BLOCKERS"])[0] for i in fam) == Counter(
        {"COUNT_NOTATION_AMBIGUOUS_NO_PER_METRE": 3, "SOURCE_CONFLICT_TWO_CALLOUTS_ONE_DIRECTION": 2})


def test_lanes_and_labels(items, cands):
    assert all(c["LANE"] in Q.RELEASED_LANES for c in cands)
    assert all(js(c["AUTHORITY"]) and js(c["EXTENT_BASES"]) for c in cands)
    for i in items:
        for v in i.values():
            assert str(v).upper() not in Q.FORBIDDEN_LABELS
        assert i["KG"] == ""
    assert all(Q.EXTENT_MINIMUM_COVER not in (js(c["EXTENT_BASES"]) or []) for c in cands)
    assert not any("40 CL" in (c["RUN_RULE"] or "") for c in cands)
    assert "BAR_LENGTH" not in ",".join(rows("11_S7_RELEASE_CANDIDATES.csv")[0])


def test_physical_continuity_not_analysis_ownership(items, census):
    """An end facing an excluded / transferred physical slab is never released beyond its face."""
    strips = rows("07_LOCAL_BAR_STRIPS.csv")
    for x in strips:
        for nk, ck in (("START_NEIGHBOUR", "START_CONDITION"), ("END_NEIGHBOUR", "END_CONDITION")):
            nb = x[nk]
            if nb and census[nb]["SCOPE"] in (SR.EXCLUDED_SPECIAL, SR.CLASSIFICATION_BLOCKED):
                assert x[ck] in (Q.END_UNRESOLVED, Q.END_OBLIQUE, Q.END_NO_SUPPORT), x["LOCAL_BAR_STRIP_ID"]
            if nb and census[nb]["SCOPE"] in (SR.NOT_SLAB, SR.VOID_OR_OPENING):
                assert x[ck] in (Q.END_NON_CONTINUOUS, Q.END_OBLIQUE, Q.END_NO_SUPPORT), x["LOCAL_BAR_STRIP_ID"]


def test_conflicts_and_gates(summary):
    conf = {c["PRE_S7_CONFLICT_ID"]: c for c in rows("09_REMAINING_CONFLICTS.csv")}
    assert {f"C-{k:02d}" for k in range(1, 12)} <= set(conf)
    assert conf["C-02"]["TRUE_SOURCE_CONFLICT"] == "False" and "IDENTITY" in conf["C-02"]["AD2_STATE"]
    assert conf["C-11"]["AD2_STATE"].startswith("RESOLVED_BY_SPLIT")
    assert conf["C-01"]["AD2_STATE"].startswith("SOURCE_CONFLICT_PRESERVED")
    true = sorted(k for k, c in conf.items() if c["TRUE_SOURCE_CONFLICT"] == "True")
    assert [t.split()[0] for t in summary["remaining_true_source_conflicts"]] == true
    assert summary["gates"] and all(summary["gates"].values())
    assert summary["no_kg"] is True and summary["s7_started"] is False
    assert summary["flags"]["kg_calculated"] is False and summary["flags"]["bar_length_total_calculated"] is False
    d = J(PKG / "01_AD2_DECISIONS.json")
    assert [x["id"] for x in d["decisions"]] == [f"AD2-D{k:02d}" for k in range(1, 18)]


def test_provenance_covers_every_record(ready, items):
    lines = [json.loads(x) for x in (PKG / "12_PROVENANCE.jsonl").read_text(encoding="utf-8").splitlines()]
    k = Counter(x["kind"] for x in lines)
    assert k["COMPONENT"] == len(ready) and k["ITEM"] >= len(items) and k["DECISION"] == 17
    assert k["STRIP"] == len(rows("07_LOCAL_BAR_STRIPS.csv"))
    assert all(x["round"] == "PRE-S7.1" and x["decision_set"] == "AD2" for x in lines)
