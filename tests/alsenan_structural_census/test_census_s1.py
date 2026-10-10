"""ALSENAN STRUCTURAL CENSUS - Round S1 (source rules + occurrence census, no rebar).

1. Synthetic known-answer cases for engine.source.structural_census (the brief's 13 required behaviours).
2. Checks on the frozen S1 registers (counts that must hold, conservation, determinism, firewall).
3. Rebar registers of Rounds 3 / 4 untouched.
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

import pytest

from engine.source import structural_census as SC

ROOT = Path(__file__).resolve().parents[2]
S1 = ROOT / "research" / "alsenan_structural_census_s1"
LAB = ROOT / "research" / "external_engine_lab"
DXF = ROOT / "data/inputs/by_sha256/9f9d1179a5d2a6635f9b412915a72184b7db1ff7729f4ab39a72dc3391738079.dxf"
LEVELS = ["FOUNDATION", "GF", "1F", "2F"]


def _reg(n):
    return json.loads((S1 / f"{n}.json").read_text(encoding="utf-8"))


def _col(i, x, y, w=300, d=500, t=None, **kw):
    return {"id": i, "bbox": (x, y, x + w, y + d), "type": t, **kw}


# ============================================================================================ 1. synthetic
def test_same_column_coordinate_continues_across_floors():
    occ = {lv: [_col(f"{lv}-a", 0, 0, t="C1")] for lv in LEVELS}
    ch = SC.vertical_chains(LEVELS, occ)
    assert len(ch) == 1
    assert ch[0]["continues_through"] == LEVELS and ch[0]["starts_at"] == "FOUNDATION" and ch[0]["terminates_at"] == "2F"
    assert SC.chain_check(ch, LEVELS, occ) == []


def test_column_changing_type_is_an_event_not_a_new_column():
    occ = {"FOUNDATION": [_col("f", 0, 0, t="C3")], "GF": [_col("g", 0, 0, t="C3")], "1F": [_col("h", 0, 0, t="C5")]}
    ch = SC.vertical_chains(LEVELS[:3], occ)
    assert len(ch) == 1
    ev = [e for e in ch[0]["events"] if e["event"] == "TYPE_CHANGE"]
    assert ev == [{"event": "TYPE_CHANGE", "from_level": "GF", "to_level": "1F", "from": "C3", "to": "C5"}]


def test_column_disappearing_terminates_the_chain():
    occ = {"FOUNDATION": [_col("f1", 0, 0), _col("f2", 5000, 0)], "GF": [_col("g1", 0, 0), _col("g2", 5000, 0)],
           "1F": [_col("h1", 0, 0)]}
    ch = SC.vertical_chains(LEVELS[:3], occ)
    stops = sorted(c["terminates_at"] for c in ch)
    assert stops == ["1F", "GF"]
    assert SC.chain_check(ch, LEVELS[:3], occ) == []


def test_column_missing_on_one_plan_is_a_gap_not_a_new_column():
    occ = {"FOUNDATION": [_col("f", 0, 0)], "1F": [_col("h", 0, 0)]}
    ch = SC.vertical_chains(["FOUNDATION", "GF", "1F"], occ, max_skip=1)
    assert len(ch) == 1 and ch[0]["events"][0]["event"] == "GAP_IN_CHAIN"


def test_touching_columns_are_not_merged():
    occ = {"FOUNDATION": [_col("a", 0, 0), _col("b", 300, 0)], "GF": [_col("c", 0, 0), _col("d", 300, 0)]}
    ch = SC.vertical_chains(LEVELS[:2], occ)
    assert sorted(tuple(sorted(c["members"].values())) for c in ch) == [("a", "c"), ("b", "d")]


def test_planted_column_starts_on_slab():
    occ = {"GF": [_col("g", 0, 0)], "1F": [_col("p", 2000, 0, starts_here=True)]}
    ch = SC.vertical_chains(["GF", "1F"], occ)
    planted = [c for c in ch if "p" in c["members"].values()][0]
    assert planted["starts_at"] == "1F" and planted["events"][0]["event"] == "STARTS_ON_SLAB"


def test_schedule_row_does_not_create_an_occurrence():
    # a type defined in the schedule but drawn on no plan gives zero occurrences and no chain
    schedule = {"C1": {}, "C2": {}, "C99": {}}
    occ = {"FOUNDATION": [_col("f", 0, 0, t="C1")], "GF": [_col("g", 0, 0, t="C1")]}
    ch = SC.vertical_chains(LEVELS[:2], occ)
    types = {t for c in ch for t in c["types"].values()}
    assert types == {"C1"} and "C99" in schedule and not any("C99" in c["types"].values() for c in ch)
    assert _reg("COLUMN_DEFINITION_REGISTER")["summary"]["by_state"].get("DEFINED_NO_PLAN_OCCURRENCE", 0) >= 1
    assert _reg("FOOTING_DEFINITION_REGISTER")["summary"]["without_plan_occurrence"] == ["F7"]


def test_duplicate_column_tag_is_never_assigned_twice():
    sys.path.insert(0, str(LAB))
    import alsenan_structural_s1 as S
    outlines = [{"id": "o1", "centre": (0, 0)}, {"id": "o2", "centre": (4000, 0)}]
    tags = [{"handle": "t1", "text": "C1", "p": (-100, -400)}, {"handle": "t2", "text": "C1", "p": (-50, -450)},
            {"handle": "t3", "text": "C2", "p": (3900, -400)}]
    out, unbound = S.assign_tags(outlines, tags, max_d=1500)
    assert len(out) == 2 and len(unbound) == 1
    handles = [v["tag_handle"] for v in out.values()]
    assert len(handles) == len(set(handles))
    # real registers: every outline of every foundation plan carries exactly one tag
    for ch in _reg("COLUMN_VERTICAL_CHAIN_REGISTER")["rows"]:
        for sh, t in ch["tags_by_plan"].items():
            assert t["handle"]


def test_footing_column_mismatch_detected():
    sq = lambda x, y, s=1000: [(x, y), (x + s, y), (x + s, y + s), (x, y + s)]
    footings = [{"id": "F1", "ring": sq(0, 0)}, {"id": "F2", "ring": sq(5000, 0)}, {"id": "F3", "ring": sq(0, 0)}]
    cols = [{"id": "C-a", "centre": (500, 500)}, {"id": "C-b", "centre": (9000, 9000)}]
    col_f, f_col, mis = SC.footing_column_check(footings, cols)
    kinds = sorted(m["kind"] for m in mis)
    assert kinds == ["COLUMN_IN_SEVERAL_FOOTINGS", "COLUMN_WITHOUT_FOOTING", "DUPLICATE_FOOTING",
                     "FOOTING_WITHOUT_COLUMN"]


def test_same_beam_type_with_different_lengths_stays_two_occurrences():
    rows = [r for r in _reg("BEAM_OCCURRENCE_REGISTER")["rows"] if r.get("beam_type") == "B1" and r["binding"] == "BOUND"]
    lengths = {r["support_centreline_length_m"] for r in rows}
    assert len(rows) >= 10 and len(lengths) > 3  # one type, many different span lengths, each its own occurrence
    assert len({r["beam_id"] for r in rows}) == len(rows)


def test_beam_schedule_does_not_create_an_occurrence():
    d = _reg("BEAM_DEFINITION_REGISTER")
    no_occ = d["summary"]["schedule_rows_without_plan_occurrence"]
    assert {"B10", "B12", "B.W"} <= set(no_occ)
    occ_types = {r.get("beam_type") for r in _reg("BEAM_OCCURRENCE_REGISTER")["rows"]}
    assert not ({"B10", "B12", "B.W"} & occ_types)


def test_cb_span_mismatch_stays_blocked():
    assert SC.cb_match_state([3.3, 3.7], [2.724, 3.75]) == "SPAN_LENGTH_CONFLICT"
    assert SC.cb_match_state([3.7, 6.4, 6.8], [6.545, 6.95]) == "SPAN_COUNT_CONFLICT"
    assert SC.cb_match_state([7.5, 5.7], [5.6, 7.45]) == "MATCH_CONFIRMED"  # drawn in the reverse direction
    assert SC.cb_match_state([7.5], [7.5], has_member=False) == "TAG_WITH_NO_MEMBER"
    cb = {r["type"]: r for r in _reg("CONTINUOUS_BEAM_OCCURRENCE_REGISTER")["rows"]}
    assert cb["CB4"]["match_state"] == "SPAN_LENGTH_CONFLICT" and cb["CB4"]["terminal_state"] != "COUNTED_AND_DEFINED"
    assert cb["CB8"]["match_state"] == "SPAN_COUNT_CONFLICT"  # extension found, but never forced


def test_slab_default_160_overridden_by_local_note():
    proj = {"value": 160, "source": "P8-N18"}
    assert SC.effective_value(project=proj)["authority"] == "PROJECT_DEFAULT"
    e = SC.effective_value(local={"value": 180, "source": "T 18"}, project=proj)
    assert e["value"] == 180 and e["authority"] == "LOCAL_PANEL_NOTE" and e["overridden"][0]["value"] == 160
    assert SC.effective_value()["authority"] == "BLOCKED"
    p = {r["panel_id"]: r for r in _reg("SLAB_PANEL_REGISTER")["rows"]}
    assert p["SP-2F_ROOF_SLAB-01"]["effective_thickness_mm"] == 180
    assert p["SP-2F_ROOF_SLAB-01"]["thickness_authority"] == "LOCAL_PANEL_NOTE"
    defaults = [r for r in p.values() if r["class"] == "SLAB_PANEL" and r["sheet"] != "GBP"
                and r["thickness_authority"] == "PROJECT_DEFAULT"]
    assert defaults and all(r["effective_thickness_mm"] == 160 and not r["local_thickness_notes"] for r in defaults)


def test_temperature_table_never_interpolated():
    rows = {150: "Y10@200", 175: "Y12@200"}
    assert SC.table_lookup_exact(160, rows) == ("RULE_NOT_EXACT_MATCH", None)
    assert SC.table_lookup_exact(175, rows) == ("EXACT_RULE", "Y12@200")


def test_slab_annotation_must_bind_to_a_panel():
    sq = [(0, 0), (4000, 0), (4000, 3000), (0, 3000)]
    panels = [{"id": "P1", "ring": sq}, {"id": "P2", "ring": [(4000, 0), (8000, 0), (8000, 3000), (4000, 3000)]}]
    assert SC.bind_to_panel((1000, 1000), panels) == ("BOUND", ["P1"])
    assert SC.bind_to_panel((20000, 1000), panels) == ("UNBOUND", [])
    assert SC.bind_to_panel((1000, 3200), panels, near=450) == ("BOUND_NEAR_EDGE", ["P1"])
    s = _reg("SLAB_REBAR_SOURCE_REGISTER")
    assert s["summary"]["slab_annotations_unbound"] == []
    for r in s["rows"]:
        if r["owner"] == "SLAB":
            assert r["panel"], r["source_row_id"]


def test_t_and_b_preserved():
    rows = [r for r in _reg("SLAB_REBAR_SOURCE_REGISTER")["rows"] if r["TandB"]]
    assert len(rows) == 4 and all(r["layer"] == "T&B" and r["tb_text_handle"] for r in rows)
    assert SC.parse_slab_rebar("3%%c16/Top")["layer_qualifier"] == "TOP"
    assert SC.parse_slab_rebar("5%%c10/m")["count_mode"] == "BARS_PER_METRE"
    assert SC.parse_slab_rebar("%%c12/20cm")["spacing_mm"] == 200


def test_special_population_cannot_disappear():
    kinds = {r["kind"] for r in _reg("SPECIAL_STRUCTURAL_OCCURRENCE_REGISTER")["rows"]}
    required = {"STAIR_FLIGHT", "STAIR_BEAM", "LIFT_PIT", "LIFT_TIE_BEAM", "PLANTED_COLUMN", "TURN_COLUMN",
                "DEAD_COLUMN", "LINTEL_POPULATION", "BOUNDARY_WALL", "PARAPET", "DOME", "SWIMMING_POOL",
                "GROUND_SLAB", "WATER_TANK_SLAB"}
    assert required <= kinds
    for r in _reg("SPECIAL_STRUCTURAL_OCCURRENCE_REGISTER")["rows"]:
        assert r["terminal_state"] in SC.TERMINAL_STATES
    # mutation: drop one special row from the ledger -> SILENT_DISAPPEARANCE
    objs = [{"source_id": "S1", "family": "SPECIAL"}, {"source_id": "S2", "family": "SPECIAL"}]
    rows = [{"source_id": "S1", "register": "X", "terminal_state": "COUNTED_BLOCKED"}]
    assert SC.conservation(objs, rows)["violations"][0]["kind"] == "SILENT_DISAPPEARANCE"


def test_tie_band_boundary_gap_is_not_snapped():
    bands = [{"band_id": "B1", "lo": None, "lo_incl": False, "hi": 50, "hi_incl": True},
             {"band_id": "B2", "lo": 50, "lo_incl": False, "hi": 80, "hi_incl": False},
             {"band_id": "B3", "lo": 80, "lo_incl": False, "hi": 120, "hi_incl": False}]
    assert SC.tie_band(50, bands) == {"state": "EXACT_RULE", "band": "B1"}
    assert SC.tie_band(70, bands)["band"] == "B2"
    assert SC.tie_band(80, bands)["state"] == "BOUNDARY_GAP"
    assert SC.tie_band(130, bands)["state"] == "OUT_OF_RANGE"


def test_terminal_state_vocabulary():
    assert SC.terminal_state(counted=True, definition="FULL") == "COUNTED_AND_DEFINED"
    assert SC.terminal_state(counted=True, definition="PARTIAL") == "COUNTED_DEFINITION_PARTIAL"
    assert SC.terminal_state(counted=False, definition="FULL") == "COUNTED_BLOCKED"
    assert SC.terminal_state(counted=True, definition="NIS") == "NOT_IN_SCOPE"


# ============================================================================================ 2. frozen registers
def test_index_hashes_and_determinism_flag():
    idx = json.loads((S1 / "INDEX.json").read_text())
    assert idx["built_twice_identical"] is True and idx["no_rebar_kg_calculated"] is True
    assert idx["frozen_before_benchmark"] is True
    assert len(idx["registers"]) == 21
    for n, v in idx["registers"].items():
        assert hashlib.sha256((S1 / v["file"]).read_bytes()).hexdigest() == v["sha256"], n


def test_conservation_zero_silent_disappearance():
    c = _reg("STRUCTURAL_OCCURRENCE_CONSERVATION_REGISTER")["summary"]
    assert c["violations"] == [] and c["silent_disappearances"] == 0
    assert c["source_objects"] == c["register_rows"]
    assert set(c["by_state"]) <= set(SC.TERMINAL_STATES)


def test_column_census_counts():
    m = _reg("COLUMN_TYPE_FLOOR_MATRIX")
    assert m["summary"]["floor_totals"] == {"FOUNDATION": 36, "GF": 30, "1F": 20, "2F": 9}
    ch = _reg("COLUMN_VERTICAL_CHAIN_REGISTER")["summary"]
    assert ch["chains"] == 39
    assert ch["hard_invariant_every_outline_in_exactly_one_chain"]["state"] == "PASS"
    assert ch["outlines_per_sheet"] == {"FP": 36, "CAP": 35, "GBP": 36, "GFRS": 34, "FFRS": 21, "SFRS": 9}
    occ = _reg("COLUMN_OCCURRENCE_REGISTER")
    assert occ["summary"]["duplicate_column_ids"] == []


def test_footing_conflict_is_not_resolved_silently():
    rows = _reg("FOOTING_OCCURRENCE_REGISTER")["rows"]
    conf = [r for r in rows if r.get("competing_tags")]
    assert len(conf) == 1 and conf[0]["type"] is None and sorted(conf[0]["candidate_types"]) == ["F", "F10"]
    comp = [r for r in _reg("FOOTING_REQUIRED_COMPONENT_REGISTER")["rows"] if r["component"] == "BOXED"
            and r.get("BOXED_REQUIRED")]
    assert comp and all(r["BOXED_SEMANTICS"] == "BLOCKED" for r in comp)


def test_no_kg_or_bar_length_in_s1_outputs():
    for p in S1.glob("*.json"):
        txt = p.read_text(encoding="utf-8")
        assert not re.search(r'"(weight_kg|kg|total_kg|bar_length_m|cut_length_m|tonnes?)"\s*:', txt), p.name


@pytest.mark.skipif(not DXF.exists(), reason="client drawing not present (data/ is not in git)")
def test_rebuild_matches_frozen_registers():
    sys.path.insert(0, str(S1))
    import build_census_s1 as BC
    texts = BC.serialise(BC.build_all())
    idx = json.loads((S1 / "INDEX.json").read_text())
    for n, v in idx["registers"].items():
        assert hashlib.sha256(texts[n].encode("utf-8")).hexdigest() == v["sha256"], n


# ============================================================================================ 3. firewall
def test_benchmark_firewall():
    banned = ("44.19", "registers_b1", "freelancer_", "Alsenan_Quotation", "alsenan_pricing", "alsenan_demo",
              "ALRASHED", "kg/m³", "alsenan_b2a_evaluation", "alsenan_v3b_evaluation")
    for path in (LAB / "alsenan_structural_s1.py", S1 / "build_census_s1.py", S1 / "rules_s1.py",
                 ROOT / "engine/source/structural_census.py"):
        src = path.read_text(encoding="utf-8")
        for b in banned:
            assert b not in src, (path.name, b)
        assert not re.search(r"open\([^)]*benchmark", src, re.I), path.name


def test_rebar_untouched():
    for d in ("research/alsenan_rebar_truth_03/registers", "research/alsenan_rebar_source_exhaustion_04/registers"):
        idx = json.loads((ROOT / d / "INDEX.json").read_text())
        files = idx.get("files") or idx.get("registers")
        for n, h in files.items():
            h = h if isinstance(h, str) else h.get("sha256")
            assert hashlib.sha256((ROOT / d / f"{n}.json").read_bytes()).hexdigest() == h, (d, n)


# ============================================================================================ 4. human-review deliverables
def test_review_manifest_matches_frozen_census():
    man_p = S1 / "review" / "REVIEW_MANIFEST.json"
    if not man_p.exists():
        pytest.skip("review deliverables not generated")
    man = json.loads(man_p.read_text(encoding="utf-8"))
    idx = json.loads((S1 / "INDEX.json").read_text())
    assert man["registers_consumed"] == {k: v["sha256"] for k, v in idx["registers"].items()}
    assert man["no_rebar_kg"] is True
    for k, v in man["id_cross_check"].items():
        assert v["missing_on_drawing"] == [] and v["label_not_in_workbook"] == [], k
        assert v["workbook_ids"] == v["drawing_labels"], k
