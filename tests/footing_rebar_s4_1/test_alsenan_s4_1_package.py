"""Alsenan S4.1 package (research/alsenan_footing_rebar_s4_1): a delta release over frozen S4.

Checks the delta against the frozen S4 files themselves (re-read here), never against a reference total."""

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
PKG = ROOT / "research" / "alsenan_footing_rebar_s4_1"
S4 = ROOT / "research" / "alsenan_footing_rebar_s4"
BRIEF_FIELDS = ("FROZEN_BASELINE", "BASELINE_COMPONENT_ID", "OLD_STATE", "OLD_KNOWN_QUANTITY", "NEW_PROJECT_SOURCE",
                "SOURCE_PAGE", "SOURCE_HANDLES", "GRAPHIC_EVIDENCE_CLASS", "NEW_COMPONENT_MODEL",
                "DELTA_KNOWN_QUANTITY", "NEW_BLOCKED_COMPONENTS", "NEW_RELEASE_STATE")
LONG_PORTIONS = ["STRAIGHT_RUN", "UPTURN_LEG_1", "UPTURN_LEG_2", "END_HOOK_1", "END_HOOK_2", "BEND_ARC_1",
                 "BEND_ARC_2"]


def J(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def rows(p):
    return list(csv.DictReader(open(p, encoding="utf-8")))


@pytest.fixture(scope="module")
def delta():
    return rows(PKG / "S4_1_DELTA_COMPONENTS.csv")


@pytest.fixture(scope="module")
def frozen():
    return {f"{r['occurrence_id']}:{r['component']}": r for r in rows(S4 / "FOOTING_REBAR_COMPONENTS.csv")}


@pytest.fixture(scope="module")
def summary():
    return J(PKG / "S4_1_RELEASE_SUMMARY.json")


def by_component(delta):
    out = defaultdict(list)
    for r in delta:
        out[r["BASELINE_COMPONENT_ID"]].append(r)
    return out


def single_layer(frozen, comp):
    return [k for k, r in frozen.items() if r["component"] == comp and r["state"] == "VERIFIED"]


# ------------------------------------------------------------------ package / freeze
def test_deliverables_exist():
    for n in ("S4_1_DELTA_COMPONENTS.csv", "S4_1_RELEASE_SUMMARY.json", "S4_1_OWNERSHIP_TRANSFERS.csv",
              "S4_1_UNRESOLVED.csv", "S4_1_PROVENANCE.jsonl", "S4_1_CHANGELOG.md", "S4_1_FREEZE_MANIFEST.json"):
        assert (PKG / n).is_file(), n


def test_s4_1_freeze_manifest_still_matches():
    m = J(PKG / "S4_1_FREEZE_MANIFEST.json")
    assert m["state"] == "FROZEN_BEFORE_S6_1" and m["references_read_before_freeze"] == []
    for group, base in (("code", ROOT), ("inputs", ROOT), ("outputs", PKG)):
        for k, h in m[group].items():
            assert hashlib.sha256((base / k).read_bytes()).hexdigest() == h, (group, k)


def test_frozen_s4_baseline_is_immutable(summary):
    m = J(S4 / "S4_FREEZE_MANIFEST.json")
    for group, base in (("code", ROOT), ("inputs", ROOT), ("outputs", S4)):
        for k, h in m[group].items():
            assert hashlib.sha256((base / k).read_bytes()).hexdigest() == h, (group, k)
    fb = summary["context"]["FROZEN_BASELINE"]
    assert fb["manifest_sha256"] == hashlib.sha256((S4 / "S4_FREEZE_MANIFEST.json").read_bytes()).hexdigest()
    assert fb["engine_commit_stamp"] == m["engine_commit_stamp"]
    assert J(PKG / "S4_1_FREEZE_MANIFEST.json")["inputs"]["research/alsenan_footing_rebar_s4/S4_FREEZE_MANIFEST.json"] \
        == fb["manifest_sha256"]


def test_rebuild_is_byte_identical():
    before = {k: (PKG / k).read_bytes() for k in J(PKG / "S4_1_FREEZE_MANIFEST.json")["outputs"]}
    subprocess.run([sys.executable, "-I", str(PKG / "build_footing_rebar_s4_1.py")], check=True,
                   capture_output=True, cwd=ROOT)
    for k, v in before.items():
        assert (PKG / k).read_bytes() == v, k


def test_builder_is_blind_and_registered():
    src = (PKG / "build_footing_rebar_s4_1.py").read_text(encoding="utf-8")
    for bad in ("christiannp", "UC4N", "U-C4N", "freelancer", "FREELANCER", "post_freeze", "multi_engine",
                "rebar_truth", "rough_rebar", "fitz", "pymupdf", "pdf_vector_evidence", "kg/m3"):
        assert bad not in src, bad
    sys.path.insert(0, str(ROOT / "tests" / "structural_comparison_engine"))
    import rebar_product_registry as RP
    assert "research/alsenan_footing_rebar_s4_1/build_footing_rebar_s4_1.py" in RP.ACCURATE_BUILDERS
    assert {"engine/source/graphic_evidence.py", "engine/source/delta_release.py"} <= set(RP.ACCURATE_MODULES)


# ------------------------------------------------------------------ delta shape
def test_every_row_carries_the_brief_delta_fields(delta):
    assert set(BRIEF_FIELDS) <= set(delta[0])
    base = J(S4 / "S4_FREEZE_MANIFEST.json")["engine_commit_stamp"]
    assert all(base in r["FROZEN_BASELINE"] and r["GRAPHIC_EVIDENCE_CLASS"] for r in delta)


def test_every_frozen_component_is_covered_once(delta, frozen):
    groups = by_component(delta)
    assert set(groups) == set(frozen)
    for cid, rs in groups.items():
        whole = [r for r in rs if r["PORTION"] in ("WHOLE_COMPONENT", "STRAIGHT_RUN")]
        assert len(whole) == 1, cid
        assert len({r["NEW_RELEASE_STATE"] for r in rs}) == 1, cid


def test_delta_conservation(delta, frozen, summary):
    frozen_known = sum(float(r["kg"]) for r in frozen.values() if r["kg"])
    s4 = J(S4 / "FOOTING_REBAR_RELEASE_SUMMARY.json")
    assert abs(summary["frozen_s4"]["known_kg"] - (s4["verified_kg"] + s4["lower_bound_known_kg"])) < 1e-9
    assert abs(sum(float(r["OLD_KNOWN_QUANTITY"]) for r in delta) - frozen_known) < 1e-3
    assert all(float(r["DELTA_KNOWN_QUANTITY"]) == 0.0 for r in delta)
    assert summary["delta_known_kg"] == 0.0
    assert abs(summary["s4_1_known_kg"] - summary["frozen_s4"]["known_kg"]) < 1e-9
    assert summary["conservation"]["all_pass"]
    for cid, rs in by_component(delta).items():          # the frozen kg sits on the component's whole / straight row
        fk = float(frozen[cid]["kg"] or 0)
        assert abs(sum(float(r["NEW_KNOWN_QUANTITY"]) for r in rs) - fk) < 1e-5, cid


# ------------------------------------------------------------------ long bars: U decomposition
def test_footing_u_bar_decomposition(delta, frozen):
    groups = by_component(delta)
    longs = single_layer(frozen, "BOTTOM_LONG")
    assert len(longs) == 20
    for cid in longs:
        rs = groups[cid]
        assert [r["PORTION"] for r in rs] == LONG_PORTIONS
        straight = rs[0]
        assert straight["PORTION_STATE"] == "KNOWN_STRAIGHT_SEGMENT"
        assert abs(float(straight["OLD_KNOWN_QUANTITY"]) - float(frozen[cid]["kg"])) < 1e-5
        assert straight["FROZEN_NET_STRAIGHT_MM"] == frozen[cid]["net_straight_mm"]   # not subtracted, not changed
        for r in rs[1:]:
            assert r["GRAPHIC_EVIDENCE_CLASS"] == "GRAPHIC_EXPLICIT_SHAPE_ONLY"
            assert r["PORTION_STATE"] == "SHAPE_FOUND_LENGTH_BLOCKED"
            assert float(r["NEW_KNOWN_QUANTITY"]) == 0.0 and r["QUANTITY_BASIS"] == "NONE"
        assert all(r["NEW_RELEASE_STATE"] == "LOWER_BOUND" and r["COMPLETE_BAR"] == "LOWER_BOUND" for r in rs)
        assert sorted(json.loads(straight["NEW_BLOCKED_COMPONENTS"])) == sorted(f"{cid}:{p}" for p in LONG_PORTIONS[1:])


def test_upturn_leg_derivation_was_attempted_and_fails_on_the_endpoint():
    prov = [json.loads(x) for x in (PKG / "S4_1_PROVENANCE.jsonl").read_text(encoding="utf-8").splitlines()]
    legs = [p for p in prov if p["portion"].startswith("UPTURN_LEG")]
    assert len(legs) == 40
    for p in legs:
        d = p["derivation"]
        assert d["footing_depth_D_mm"] > 0 and d["cover_bottom_mm"] == 70.0
        assert d["conditions"]["ENDPOINTS_DETERMINISTIC"] is False
        assert d["conditions"]["DIMENSIONS_FROM_PROJECT_SOURCE"] is True
        assert "not used" in d["result"] and p["delta_kg"] == 0.0
        assert p["pdf_sha256"] == "74da1523f05eb3c6a4fe3ddebaef2c3d841891f003efc03bc32a3fb4553337e3"


def test_45_degree_hook_found_without_length(delta):
    hooks = [r for r in delta if r["PORTION"].startswith("END_HOOK")]
    assert len(hooks) == 40
    assert all(r["PORTION_STATE"] == "SHAPE_FOUND_LENGTH_BLOCKED" and float(r["NEW_KNOWN_QUANTITY"]) == 0 and
               "45°" in r["WHY"] for r in hooks)


def test_short_bars_do_not_get_the_u_shape(delta, frozen):
    groups = by_component(delta)
    shorts = single_layer(frozen, "BOTTOM_SHORT")
    assert len(shorts) == 20
    for cid in shorts:
        rs = groups[cid]
        assert [r["PORTION"] for r in rs] == ["STRAIGHT_RUN", "END_TREATMENT_1", "END_TREATMENT_2"]
        assert rs[0]["PORTION_STATE"] == "KNOWN_STRAIGHT_SEGMENT"
        assert all(r["PORTION_STATE"] == "BLOCKED_UNQUANTIFIED" and r["GRAPHIC_EVIDENCE_CLASS"] ==
                   "NO_GRAPHIC_EVIDENCE" for r in rs[1:])
        assert all(r["NEW_RELEASE_STATE"] == "LOWER_BOUND" for r in rs)
    assert not [r for r in delta if r["COMPONENT"] != "BOTTOM_LONG" and ("UPTURN" in r["PORTION"] or
                                                                          "HOOK" in r["PORTION"])]


def test_release_semantics_no_verified_complete(delta, summary):
    assert not [r for r in delta if r["NEW_RELEASE_STATE"] == "VERIFIED"]
    assert summary["s4_1_complete_bar_kg"]["VERIFIED"] == 0.0
    assert abs(summary["s4_1_known_straight_segment_kg_formerly_verified"] - J(
        S4 / "FOOTING_REBAR_RELEASE_SUMMARY.json")["verified_kg"]) < 1e-9
    assert summary["state_transitions"]["VERIFIED -> LOWER_BOUND"] == 40
    assert summary["flags"] == {"frozen_outputs_changed": False, "plotted_scale_used": False,
                                "kg_from_shape_only_graphic": False, "verified_created": False,
                                "pre_s7_started": False, "references_read": []}


def test_two_layer_bottoms_gain_the_end_treatment_facet(delta, frozen):
    ftb = [k for k, r in frozen.items() if r["component"].startswith("BOTTOM") and r["state"] == "LOWER_BOUND"]
    assert len(ftb) == 10
    groups = by_component(delta)
    for cid in ftb:
        rs = groups[cid]
        assert {r["CHANGE_KIND"] for r in rs} == {"FACET_ADDED"}
        assert all(json.loads(r["FACETS"])["END_TREATMENT"].startswith("END_TREATMENT_NOT_ESTABLISHED") for r in rs)
        assert all(r["NEW_RELEASE_STATE"] == "LOWER_BOUND" for r in rs)


# ------------------------------------------------------------------ BOXED and FF
def test_boxed_shape_found_count_blocked(delta, summary):
    boxed = [r for r in delta if r["COMPONENT"] == "BOXED" and r["OLD_STATE"] != "NOT_APPLICABLE"]
    assert len(boxed) == 21
    assert all(r["NEW_RELEASE_STATE"] == "BLOCKED_UNQUANTIFIED" and float(r["NEW_KNOWN_QUANTITY"]) == 0
               for r in boxed)
    facet = [r for r in boxed if r["CHANGE_KIND"] == "FACET_ADDED"]
    assert len(facet) == 20 and all(r["GRAPHIC_EVIDENCE_CLASS"] == "GRAPHIC_EXPLICIT_SHAPE_ONLY" for r in facet)
    for r in facet:
        f = json.loads(r["FACETS"])
        assert f["SHAPE"].startswith("SOURCE_FOUND_EXPLICIT") and f["BOXED_KG"] == "BLOCKED_UNQUANTIFIED"
        assert f["DIAMETER"].startswith("SOURCE_EXPECTED_NOT_LOCATED")
        assert f["EXISTENCE"].startswith("SOURCE_FOUND_EXPLICIT" if r["MARK"] != "FN" else "SOURCE_EXPECTED")
    assert summary["boxed"] == {"blocked": 21, "existence_explicit_shape_found": 16, "fn_existence_not_located": 4,
                                "pending_engineer": 1, "boxed_kg": "BLOCKED_UNQUANTIFIED"}


def test_ff_wall_base_bars_transfer_to_s8(delta, summary):
    t = rows(PKG / "S4_1_OWNERSHIP_TRANSFERS.csv")
    assert len(t) == 1
    t = t[0]
    assert (t["OLD_UNRESOLVED_OWNER"], t["NEW_OWNER"], t["TARGET_STAGE"]) == \
        ("FOOTING_CANDIDATE", "LIFT_PIT / SPECIAL_STRUCTURE", "S8")
    assert t["BASELINE_COMPONENT_ID"] == "FOCC-1B2B:OTHER_EXPLICIT_EXTRA" and float(t["KG_IN_S4_1"]) == 0.0
    r = next(r for r in delta if r["BASELINE_COMPONENT_ID"] == t["BASELINE_COMPONENT_ID"])
    assert r["CHANGE_KIND"] == "OWNERSHIP_TRANSFER" and r["NEW_RELEASE_STATE"] == "TRANSFERRED_OUT"
    assert float(r["NEW_KNOWN_QUANTITY"]) == 0.0
    assert not [x for x in delta if x["ACCURATE_COMPONENT"].startswith("FOOTING") and "Ø16" in x["NEW_COMPONENT_MODEL"]
                and x["NEW_RELEASE_STATE"] != "TRANSFERRED_OUT"]
    assert summary["transfers_to_s8"] == ["FOCC-1B2B:OTHER_EXPLICIT_EXTRA"]


def test_f_f10_is_not_resolved(delta):
    ff10 = [r for r in delta if r["MARK"] == "F|F10"]
    assert ff10 and all(r["CHANGE_KIND"] == "NO_CHANGE" and r["NEW_RELEASE_STATE"] == r["OLD_STATE"] for r in ff10
                        if r["OLD_STATE"] != "NOT_APPLICABLE")


def test_unresolved_register_names_every_blocked_portion(delta):
    u = rows(PKG / "S4_1_UNRESOLVED.csv")
    keys = {(x["BASELINE_COMPONENT_ID"], x["PORTION"]) for x in u}
    blocked = [r for r in delta if r["PORTION"] != "WHOLE_COMPONENT" and r["PORTION_STATE"] in
               ("SHAPE_FOUND_LENGTH_BLOCKED", "BLOCKED_UNQUANTIFIED")]
    assert len(blocked) == 180
    assert all((r["BASELINE_COMPONENT_ID"], r["PORTION"]) in keys for r in blocked)
    carried = [x for x in u if x["ORIGIN"] == "CARRIED_FROM_S4"]
    assert len(carried) == len(rows(S4 / "FOOTING_REBAR_UNRESOLVED.csv"))
    assert Counter(x["OWNER"] for x in carried)["S8 LIFT_PIT / SPECIAL_STRUCTURE"] == 1


def test_changelog_does_not_hide_the_semantic_corrections():
    t = (PKG / "S4_1_CHANGELOG.md").read_text(encoding="utf-8")
    for s in ("VERIFIED → KNOWN_STRAIGHT_SEGMENT", "COMPLETE_BAR = LOWER_BOUND", "OWNERSHIP_TRANSFER",
              "BOXED_KG = BLOCKED_UNQUANTIFIED", "**0 kg**", "NOT copied"):
        assert s in t, s
