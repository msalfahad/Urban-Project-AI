"""PRE-S6 package (research/pre_s6_superstructure_beam_readiness) on the committed registers.

* every output / code / input file matches INDEX.json; the package rebuilds byte for byte when ST7757.dxf is present;
* conservation: every tag, span, arc band, fragment and rule population terminates exactly once and every S1
  superstructure row is mapped;
* binding: every tag lists all its alternatives; no S1 binding changes silently; candidates never release;
* width conflicts keep the geometry and conflict the type rebar; CB span conflicts keep both lengths;
* T/M-n never feeds S6; MID releases only with a printed count and a bound typical rule; a CB bar crossing supports is
  one run; top bars, hangers, side bars, development, hooks and stirrup mass never release;
* openings: no source-identified beam opening, so no opening extra is triggered;
* provenance templates exist for exactly the released components; no kg anywhere; the builder is blind.
"""

from __future__ import annotations

import csv
import hashlib
import json
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path

import pytest

from engine.source import beam_rebar_readiness as BR

ROOT = Path(__file__).resolve().parents[2]
PKG = ROOT / "research" / "pre_s6_superstructure_beam_readiness"
DXF = ROOT / "data/inputs/by_sha256/9f9d1179a5d2a6635f9b412915a72184b7db1ff7729f4ab39a72dc3391738079.dxf"
RELEASED = ("READY", "READY_LOWER_BOUND")


def J(n):
    return json.loads((PKG / n).read_text(encoding="utf-8"))


def rows(n):
    return list(csv.DictReader(open(PKG / n, encoding="utf-8")))


def L(v):
    return json.loads(v) if v not in ("", None) else None


S = J("PRE_S6_SUMMARY.json")
READY = rows("10_SUPERSTRUCTURE_BEAM_REBAR_READINESS.csv")
CONS = rows("01_BEAM_OCCURRENCE_CONSERVATION.csv")
RUNS = rows("06_BEAM_BAR_RUN_READINESS.csv")


def test_outputs_match_index():
    idx = J("INDEX.json")
    assert idx["no_kg"] and idx["baseline"] == "3b36f2b"
    assert len(idx["outputs"]) == 15
    for n, h in idx["outputs"].items():
        assert hashlib.sha256((PKG / n).read_bytes()).hexdigest() == h, n
    for c, h in idx["code"].items():
        assert hashlib.sha256((ROOT / c).read_bytes()).hexdigest() == h, c
    for c, h in idx["inputs"].items():
        assert hashlib.sha256((ROOT / c).read_bytes()).hexdigest() == h, c


@pytest.mark.skipif(not DXF.exists(), reason="ST7757.dxf not present")
def test_rebuild_is_byte_identical():
    idx = J("INDEX.json")
    before = {k: (PKG / k).read_bytes() for k in list(idx["outputs"]) + ["INDEX.json"]}
    subprocess.run([sys.executable, "-I", str(PKG / "build_pre_s6.py"), str(DXF)], check=True, capture_output=True,
                   cwd=ROOT)
    for k, v in before.items():
        assert (PKG / k).read_bytes() == v, k


# ------------------------------------------------------------------------------------------------ conservation
def test_every_object_terminates_exactly_once():
    ids = [r["OBJECT_ID"] for r in CONS]
    assert len(ids) == len(set(ids)) == S["conservation"]["objects"]
    for r in CONS:
        allowed = BR.TAG_TERMINALS if r["OBJECT_KIND"] == "TAG" else BR.GEOMETRY_TERMINALS
        assert r["TERMINAL"] in allowed, r["OBJECT_ID"]
    assert S["conservation"]["all_terminate_once"] and not S["s1_rows_unmapped"]
    assert S["s1_rows_mapped"] == 146
    kinds = Counter(r["OBJECT_KIND"] for r in CONS)
    assert kinds["TAG"] == S["tag_count"] == 119


def test_tags_and_spans_reconcile():
    tags = {r["OBJECT_ID"]: r for r in CONS if r["OBJECT_KIND"] == "TAG"}
    geo = {r["OBJECT_ID"]: r for r in CONS if r["OBJECT_KIND"] in ("MEMBER_SPAN", "ARC_BAND")}
    for t in tags.values():
        if t["TERMINAL"].startswith("BOUND") or t["TERMINAL"] == "DUPLICATE_TAG":
            g = geo[t["BOUND_GEOMETRY"]]
            assert t["OBJECT_ID"].split(":", 2)[2] in L(g["BOUND_TAGS"])
    for g in geo.values():
        bt = L(g["BOUND_TAGS"]) or []
        assert (g["TERMINAL"] == "GEOMETRY_WITHOUT_TAG") == (not bt)
        for h in bt:
            assert tags[f"TAG:{g['SHEET']}:{h}"]["BOUND_GEOMETRY"] == g["OBJECT_ID"]


def test_silently_dropped_spans_now_terminate():
    new = S["geometry_not_in_s1"]
    assert new and all(o.startswith(("SPAN:", "ARC:")) for o in new)
    term = {r["OBJECT_ID"]: r["TERMINAL"] for r in CONS}
    assert all(term[o] in BR.GEOMETRY_TERMINALS for o in new)


# ------------------------------------------------------------------------------------------------ binding
def test_every_tag_lists_all_alternatives_and_the_bound_member():
    b = rows("02_BEAM_BINDING_READINESS.csv")
    by = defaultdict(list)
    for r in b:
        by[(r["SHEET"], r["TAG_HANDLE"])].append(r)
    assert len(by) == 119
    for k, rs in by.items():
        if rs[0]["BOUND_MEMBER"]:
            assert sum(r["IS_BOUND_MEMBER"] == "TRUE" for r in rs) == 1, k
    # nearest label alone never binds: a decision never cites distance as its reason
    assert not any("nearest" in (r["WHY"] or "").lower() for r in b)


def test_rotation_only_alternatives_leave_a_candidate():
    b = rows("02_BEAM_BINDING_READINESS.csv")
    for r in b:
        if r["ROTATION_ONLY_ALTERNATIVE"] == "TRUE":
            assert r["DECISION"] == "BOUND_CANDIDATE", r["TAG_HANDLE"]


def test_s1_binding_changes_are_listed():
    ch = {c[0]: c for c in S["s1_binding_changes"]}
    assert ch["474"][3] == "BOUND_CANDIDATE" and ch["474"][2] == "BL017" and ch["474"][4] == "BL008"
    assert all(c[1] == "AMBIGUOUS" for h, c in ch.items() if h in ("472", "6BD", "6D4", "6D7", "76C", "45D"))


def test_candidates_never_release():
    for r in READY:
        if "BOUND_CANDIDATE" in (r["BINDING_TERMINAL"] or ""):
            assert r["STATUS"] not in RELEASED, (r["OCCURRENCE_ID"], r["COMPONENT_FAMILY"])


# ------------------------------------------------------------------------------------------------ width / spans
def test_width_conflict_keeps_geometry_and_conflicts_type_rebar():
    assert sorted(map(tuple, S["width_conflicts"])) == [("FFRS", "B6"), ("FFRS", "CB10"), ("GFRS", "B21"),
                                                         ("GFRS", "B29"), ("GFRS", "CB2")]
    for r in READY:
        if r["SUBFAMILY"] == "SIMPLE_BEAM" and r["WIDTH_MATCH_STATE"] == "SOURCE_CONFLICT":
            assert r["GEOMETRY_OBJECT"] and r["STATUS"] not in RELEASED


def test_cb_span_conflicts_keep_both_values():
    sp = rows("05_CB_SPAN_SEQUENCE.csv")
    for r in sp:
        assert r["NEVER_SHARED"] == "TRUE" and r["NEVER_CAPPED"] == "TRUE"
        if r["SPAN_STATE"] == "SPAN_LENGTH_SOURCE_CONFLICT":
            assert r["PHYSICAL_LENGTH_CC_M"] and r["SCHEDULE_SPAN_M"]
    states = S["cb_sequence_states"]
    assert states["CBO-GFRS-CB8-BL024"] == "SPAN_COUNT_CONFLICT"
    assert states["CBO-FFRS-CB9-BL023"] == "MATCH"            # matches only read right to left
    cb9 = [r for r in sp if r["CB_OCCURRENCE_ID"] == "CBO-FFRS-CB9-BL023"]
    assert {r["ORIENTATION"] for r in cb9} == {"REVERSED"}


def test_conflicted_cb_occurrences_never_release():
    for r in READY:
        if r["SUBFAMILY"] == "CONTINUOUS_BEAM" and r["APPLICABILITY_STATE"] in ("SOURCE_CONFLICT", "BLOCKED"):
            assert r["STATUS"] not in RELEASED, (r["OCCURRENCE_ID"], r["COMPONENT_FAMILY"])


# ------------------------------------------------------------------------------------------------ semantics
def test_t_over_m_is_a_design_load_never_rebar():
    sem = rows("04_CONTINUOUS_BEAM_SCHEDULE_SEMANTICS.csv")
    tm = [r for r in sem if r["FIELD_FAMILY"] == "T/M"]
    assert tm and all(r["AUTHORITY"] == "SOURCE_EXPLICIT" and r["FEEDS_S6"] == "FALSE" for r in tm)
    tok = rows("09_BEAM_TOKEN_CORPUS.csv")
    assert all(r["TERMINAL"] == "NOT_REBAR" for r in tok if r["FIELD_FAMILY"] == "T/M")


def test_simple_schedule_fields_are_not_collapsed():
    sem = rows("03_SIMPLE_BEAM_SCHEDULE_SEMANTICS.csv")
    fams = {"TOP_MAIN", "BOTTOM_MAIN", "TOP_SUPPORT_EXTRA", "BOTTOM_EXTRA", "MID", "HANGER", "SIDE_REBAR",
            "STIRRUP", "OTHER"}
    by = defaultdict(set)
    for r in sem:
        by[r["TYPE"]].add(r["FIELD_FAMILY"])
    assert by and all(v == fams for v in by.values())
    for r in sem:
        if r["FIELD_FAMILY"] == "SIDE_REBAR" and r["PARSED"]:
            assert r["AUTHORITY"] == "UNRESOLVED" and r["FEEDS_S6"] == "FALSE"


def test_token_corpus_terminals():
    tok = rows("09_BEAM_TOKEN_CORPUS.csv")
    allowed = {"PARSED_BOUND", "PARSED_AMBIGUOUS", "SOURCE_CONFLICT", "BLOCKED_SEMANTICS", "DUPLICATE_SOURCE",
               "NOT_REBAR", "UNSUPPORTED"}
    assert tok and {r["TERMINAL"] for r in tok} <= allowed
    assert len({r["TOKEN_ID"] for r in tok}) == len(tok)


# ------------------------------------------------------------------------------------------------ bar runs
def test_mid_release_needs_count_and_bound_rule():
    for r in RUNS:
        if r["ROLE"] == "MID_SUPPORT_TOP" and r["STATUS"] in RELEASED:
            assert r["COUNT"] and r["DIA_MM"] and L(r["SOURCE_EXTENT"])["rules"]
            assert r["STRAIGHT_RUN_STATE"] == "VERIFIED" and r["COMPLETE_BAR_STATE"] == "VERIFIED"
        if r["ROLE"] == "MID_SUPPORT_TOP" and not r["COUNT"]:
            assert r["STATUS"] not in RELEASED and r["STRAIGHT_RUN_STATE"] == "BLOCKED_UNQUANTIFIED"


def test_cb_bar_crossing_supports_is_one_run():
    handles = [L(r["SOURCE_EXTENT"])["frame_handle"] + "|" + r["OCCURRENCE_ID"] for r in RUNS
               if r["SUBFAMILY"] == "CONTINUOUS_BEAM"]
    assert len(handles) == len(set(handles))
    for r in RUNS:
        segs = L(r["STRAIGHT_SEGMENTS"]) or []
        sup = [s["support"] for s in segs if s.get("kind") == "THROUGH_SUPPORT"]
        assert len(sup) == len(set(sup)), r["BAR_RUN_ID"]


def test_straight_run_kept_while_development_blocked():
    for r in RUNS:
        if r["SUBFAMILY"] == "SIMPLE_BEAM" and r["STATUS"] == "READY_LOWER_BOUND":
            assert r["STRAIGHT_RUN_STATE"] == "VERIFIED" and r["COMPLETE_BAR_STATE"] == "LOWER_BOUND"
            assert r["DEVELOPMENT_1"] == r["DEVELOPMENT_2"] == "BLOCKED_UNQUANTIFIED"
            assert float(r["STRAIGHT_RUN_M"]) > 0


def test_never_released_families():
    never = {"TOP", "HANGER", "SIDE_REBAR", "STIRRUP_MASS", "DEVELOPMENT_ANCHORAGE", "HOOKS", "LONGITUDINAL",
             "PLANTED_COLUMN_EXTRA", "STAIR_EXTRA"}
    for r in READY:
        if r["COMPONENT_FAMILY"] in never:
            assert r["STATUS"] not in RELEASED, (r["OCCURRENCE_ID"], r["COMPONENT_FAMILY"])
    assert not any(r["STATUS"] == "READY" and r["SUBFAMILY"] == "SIMPLE_BEAM" for r in READY)


def test_stirrup_count_released_only_as_lower_bound_count():
    for r in READY:
        if r["COMPONENT_FAMILY"] == "STIRRUP_COUNT" and r["STATUS"] in RELEASED:
            assert r["STATUS"] == "READY_LOWER_BOUND" and int(r["COUNT"]) > 0
            assert L(r["STIRRUP_DETAIL"])["MASS"]["state"] == "BLOCKED_UNQUANTIFIED"


def test_untagged_geometry_has_no_applicable_detail():
    u = [r for r in READY if r["SUBFAMILY"] == "UNTAGGED_GEOMETRY"]
    assert len(u) == S["untagged_geometry"] and all(r["STATUS"] == "NO_APPLICABLE_DETAIL" for r in u)


# ------------------------------------------------------------------------------------------------ openings
def test_no_source_identified_beam_opening():
    op = rows("08_BEAM_OPENING_OCCURRENCES.csv")
    assert op and all(r["OPENING_STATE"] == "NOT_APPLICABLE" for r in op)
    assert all(r["OUTLINE_KIND"] in ("CLOSED_OUTLINE", "OPEN_LINEWORK") for r in op)
    fams = {r["COMPONENT_FAMILY"] for r in READY}
    assert "OPENING_EXTRA_TOP" not in fams and "STIRRUP_EXTRA" not in fams
    assert all(r["STATUS"] == "NOT_APPLICABLE" for r in READY if r["COMPONENT_FAMILY"] == "OPENING_EXTRA")


# ------------------------------------------------------------------------------------------------ provenance / no kg
def test_provenance_templates_cover_exactly_the_released_components():
    t = J("S6_PROVENANCE_TEMPLATES.json")["templates"]
    rel = [r for r in READY if r["STATUS"] in RELEASED and r["COMPONENT_FAMILY"] != "STIRRUP_COUNT"]
    assert len(t) == len(rel) == S["provenance_templates"]
    assert {p["BAR_RUN_ID"] for p in t} == {r["BAR_RUN_ID"] for r in rel}
    for p in t:
        assert BR.provenance_ready(p) and p["ELEMENT_FAMILY"] == "BEAM"
        assert not any(k.startswith("FOOTING_") for k in p)


def test_no_kg_anywhere():
    assert S["no_kg"]
    for n in J("INDEX.json")["outputs"]:
        if n.endswith(".csv"):
            head = (PKG / n).read_text(encoding="utf-8").splitlines()[0].upper()
            assert "KG" not in head and "MASS_" not in head, n
    assert "kg" not in (PKG / "10_SUPERSTRUCTURE_BEAM_REBAR_READINESS.csv").read_text(encoding="utf-8").lower().replace(
        "kg/m", "")


def test_builder_is_blind():
    for f in ("build_pre_s6.py", "write_docs_pre_s6.py"):
        src = (PKG / f).read_text(encoding="utf-8").lower()
        for tok in ("christiannp", "freelancer", "post_freeze_comparison", "rebar_truth", "rough_rebar", "kg/m3",
                    "benchmark", "donor", "alsenan_ground_system_rebar_s5"):
            assert tok not in src, (f, tok)


def test_decision_is_restricted_go():
    sc = (PKG / "12_S6_SCOPE_RECOMMENDATION.md").read_text(encoding="utf-8")
    assert "RESTRICTED GO" in sc
    q = (PKG / "11_ENGINEERING_QUESTIONS.md").read_text(encoding="utf-8")
    assert "Q1" in q and "R1" in q
