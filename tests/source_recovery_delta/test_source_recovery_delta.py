"""Source recovery delta (research/source_recovery_delta): second-pass source exhaustion for S4 / S5 / S6.

The package is a register of findings, not a quantity. These tests hold it to the round's rules: the frozen S4 / S5 /
S6 packages are untouched, every item has exactly one of the six terminal states, F / F10 stays with the engineer,
SB2 stays a conflict, candidates never carry kg or VERIFIED, T/M never becomes steel, every graphic finding rests on
an asserted vector fact, and the builder is blind and reproducible without the engine PDF stack.
"""

from __future__ import annotations

import ast
import csv
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
PKG = ROOT / "research" / "source_recovery_delta"
TERMINAL = {"SOURCE_FOUND_EXPLICIT", "SOURCE_FOUND_DERIVED", "SOURCE_CONFLICT", "SOURCE_EXPECTED_NOT_LOCATED",
            "PENDING_ENGINEER_CLARIFICATION", "GENERIC_CODE_QA_ONLY"}
FROZEN = {"S4": "research/alsenan_footing_rebar_s4/S4_FREEZE_MANIFEST.json",
          "S5": "research/alsenan_ground_system_rebar_s5/S5_FREEZE_MANIFEST.json",
          "S6": "research/alsenan_superstructure_beam_rebar_s6/S6_FREEZE_MANIFEST.json"}
OUTPUTS = ("00_README.md", "01_ENGINEER_PROJECT_CLAIM.json", "02_UNRESOLVED_MASTER_REGISTER.csv",
           "03_UNRESOLVED_SOURCE_CONNECTION_GRAPH.csv", "04_S4_SOURCE_RECOVERY.csv", "05_S5_SOURCE_RECOVERY.csv",
           "06_S6_SOURCE_RECOVERY.csv", "07_S4_1_CANDIDATES.csv", "08_S5_1_CANDIDATES.csv", "09_S6_1_CANDIDATES.csv",
           "10_PENDING_ENGINEER_CONFLICTS.csv", "11_SOURCE_EXPECTED_NOT_LOCATED.csv", "12_RECOMMENDATION.md",
           "TEST_RUN.md")
BUILT = ("01_ENGINEER_PROJECT_CLAIM.json", "02_UNRESOLVED_MASTER_REGISTER.csv",
         "03_UNRESOLVED_SOURCE_CONNECTION_GRAPH.csv", "04_S4_SOURCE_RECOVERY.csv", "05_S5_SOURCE_RECOVERY.csv",
         "06_S6_SOURCE_RECOVERY.csv", "07_S4_1_CANDIDATES.csv", "08_S5_1_CANDIDATES.csv", "09_S6_1_CANDIDATES.csv",
         "10_PENDING_ENGINEER_CONFLICTS.csv", "11_SOURCE_EXPECTED_NOT_LOCATED.csv", "13_GRAPHIC_EVIDENCE.json",
         "SRD_SUMMARY.json")
CANDIDATE_COLS = ("FROZEN_BASELINE", "OLD_STATE", "NEW_SOURCE", "NEW_SOURCE_HANDLES", "NEW_AUTHORITY",
                  "PROPOSED_NEW_STATE", "EXPECTED_COMPONENTS_UNLOCKED")


def J(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def rows(name):
    with open(PKG / name, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


@pytest.fixture(scope="module")
def reg():
    return {r["ITEM_ID"]: r for r in rows("02_UNRESOLVED_MASTER_REGISTER.csv")}


@pytest.fixture(scope="module")
def ev():
    return J(PKG / "13_GRAPHIC_EVIDENCE.json")["evidence"]


def test_all_deliverables_exist():
    for f in OUTPUTS + ("13_GRAPHIC_EVIDENCE.json", "SRD_SUMMARY.json"):
        assert (PKG / f).exists(), f


def test_frozen_s4_s5_s6_untouched_and_recorded():
    s = J(PKG / "SRD_SUMMARY.json")
    for stage, man in FROZEN.items():
        m = J(ROOT / man)
        pkg = (ROOT / man).parent
        for group, base in (("code", ROOT), ("inputs", ROOT), ("outputs", pkg)):
            for k, h in m[group].items():
                assert hashlib.sha256((base / k).read_bytes()).hexdigest() == h, (stage, group, k)
        rec = s["frozen_baselines"][stage]
        assert rec["manifest_sha256"] == hashlib.sha256((ROOT / man).read_bytes()).hexdigest(), stage
        assert rec["engine_commit_stamp"] == m["engine_commit_stamp"], stage
    assert s["kg_recalculated"] is False and s["s7_started"] is False


def test_engineer_claim_is_versioned_and_authorises_nothing():
    c = J(PKG / "01_ENGINEER_PROJECT_CLAIM.json")
    assert c["kind"] == "PROJECT_ENGINEER_CLAIM" and c["version"] == 1 and c["authorises_assumptions"] is False
    assert "contained within the issued construction plan set" in c["statement"]
    assert c["workflow_old"] == "not found -> engineer required"
    assert c["workflow_new"].startswith("not found -> SOURCE_EXPECTED_NOT_LOCATED -> exhaust the issued plan set")
    assert c["frozen_quantities_changed"] is False


def test_every_item_has_exactly_one_terminal_state(reg):
    allr = rows("02_UNRESOLVED_MASTER_REGISTER.csv")
    assert len(allr) == len(reg)                                       # ids unique
    assert all(r["TERMINAL_STATE"] in TERMINAL for r in allr)
    per_stage = {}
    for f, st in (("04_S4_SOURCE_RECOVERY.csv", "S4"), ("05_S5_SOURCE_RECOVERY.csv", "S5"),
                  ("06_S6_SOURCE_RECOVERY.csv", "S6")):
        for r in rows(f):
            assert reg[r["ITEM_ID"]]["STAGE"] == st and reg[r["ITEM_ID"]]["TERMINAL_STATE"] == r["TERMINAL_STATE"]
            per_stage[r["ITEM_ID"]] = per_stage.get(r["ITEM_ID"], 0) + 1
    assert set(per_stage) == set(reg) and set(per_stage.values()) == {1}
    s = J(PKG / "SRD_SUMMARY.json")
    for st in ("S4", "S5", "S6"):
        got = {}
        for r in allr:
            if r["STAGE"] == st:
                got[r["TERMINAL_STATE"]] = got.get(r["TERMINAL_STATE"], 0) + 1
        assert got == s["terminal_by_stage"][st], st


def test_f_f10_pending_and_sb2_stays_a_conflict(reg):
    assert reg["S4-09"]["TERMINAL_STATE"] == "PENDING_ENGINEER_CLARIFICATION" and "F / F10" in reg["S4-09"]["TOPIC"]
    assert reg["S5-11"]["TERMINAL_STATE"] == "SOURCE_CONFLICT" and "SB2" in reg["S5-11"]["TOPIC"]
    pec = {r["ITEM_ID"]: r for r in rows("10_PENDING_ENGINEER_CONFLICTS.csv")}
    assert pec["S4-09"]["TERMINAL_STATE"] == "PENDING_ENGINEER_CLARIFICATION"
    assert "2ABA" not in pec["S5-11"]["SOURCE_A"] and "issued schedule sheet" in pec["S5-11"]["NEW_EVIDENCE_THIS_ROUND"]
    # no candidate touches a pending / conflicting item
    for f in ("07_S4_1_CANDIDATES.csv", "08_S5_1_CANDIDATES.csv", "09_S6_1_CANDIDATES.csv"):
        for c in rows(f):
            assert reg[c["ITEM_ID"]]["TERMINAL_STATE"] not in ("SOURCE_CONFLICT", "PENDING_ENGINEER_CLARIFICATION")


def test_every_conflict_and_pending_item_reaches_the_engineer_file(reg):
    pec = rows("10_PENDING_ENGINEER_CONFLICTS.csv")
    items = {r["ITEM_ID"] for r in pec}
    want = {k for k, r in reg.items() if r["TERMINAL_STATE"] in ("SOURCE_CONFLICT", "PENDING_ENGINEER_CLARIFICATION")}
    assert want == items
    affected = {r["AFFECTED"] for r in pec}
    for occ in ("BM-1F_ROOF-B6-BL014-6C5", "BM-GF_ROOF-B21-BL001-468", "BM-GF_ROOF-B29-BL039-465",
                "CBO-FFRS-CB10-BL001", "CBO-GFRS-CB2-BL038", "CBO-GFRS-CB4-BL016", "CBO-GFRS-CB5-BL008",
                "CBO-GFRS-CB8-BL024", "CBO-GFRS-CB3-BL022"):
        assert occ in affected, occ
    assert all(r["QUESTION"] for r in pec)


def test_not_located_file_mirrors_the_register(reg):
    nl = {r["ITEM_ID"] for r in rows("11_SOURCE_EXPECTED_NOT_LOCATED.csv")}
    assert nl == {k for k, r in reg.items() if r["TERMINAL_STATE"] == "SOURCE_EXPECTED_NOT_LOCATED"}
    assert all(r["ASK"] and r["WHERE_SEARCHED"] for r in rows("11_SOURCE_EXPECTED_NOT_LOCATED.csv"))


def test_no_kg_anywhere_and_candidates_never_verified(reg):
    for f in BUILT:
        if f.endswith(".csv"):
            head = rows(f)[0].keys()
            assert not [c for c in head if "KG" in c.upper() and c != "KG_RECALCULATED"], f
    for f in ("07_S4_1_CANDIDATES.csv", "08_S5_1_CANDIDATES.csv", "09_S6_1_CANDIDATES.csv"):
        rs = rows(f)
        assert rs and all(c in rs[0] for c in CANDIDATE_COLS), f
        for r in rs:
            assert r["KG_RECALCULATED"] == "NO" and all(r[c] for c in CANDIDATE_COLS), r["CANDIDATE_ID"]
            assert "VERIFIED" not in r["PROPOSED_NEW_STATE"], r["CANDIDATE_ID"]
            assert r["CHANGE_KIND"] in ("UNLOCK", "CORRECTION_DOWNGRADE", "FACET_ONLY")
            it = reg[r["ITEM_ID"]]
            if r["CHANGE_KIND"] == "UNLOCK":                       # only a found source unlocks a component
                assert it["TERMINAL_STATE"] in ("SOURCE_FOUND_EXPLICIT", "SOURCE_FOUND_DERIVED"), r["CANDIDATE_ID"]
            assert r["FROZEN_BASELINE"].endswith(")") and "+code:" in r["FROZEN_BASELINE"]


def test_tm_stays_design_load(reg):
    tm = reg["S6-25"]
    assert tm["TERMINAL_STATE"] == "SOURCE_FOUND_EXPLICIT" and "never" in tm["WHY"] and "t/m" in tm["WHY"]
    for f in ("07_S4_1_CANDIDATES.csv", "08_S5_1_CANDIDATES.csv", "09_S6_1_CANDIDATES.csv"):
        for r in rows(f):
            assert "T/M" not in " ".join(r.values()) and "t/m" not in " ".join(r.values())


def test_connection_graph_covers_every_item(reg):
    g = rows("03_UNRESOLVED_SOURCE_CONNECTION_GRAPH.csv")
    kinds = {"OCCURRENCE_COMPONENT", "SCHEDULE_CELL", "DETAIL_REFERENCE", "TYPICAL_DETAIL", "GENERAL_NOTE",
             "ARCHITECTURAL_REFERENCE"}
    assert {r["NODE_KIND"] for r in g} <= kinds and {r["LINK_STATE"] for r in g} <= {"FOUND", "NOT_FOUND"}
    for k in reg:
        hops = [r for r in g if r["ITEM_ID"] == k]
        assert hops[0]["HOP"] == "0" and hops[0]["NODE_KIND"] == "OCCURRENCE_COMPONENT" and len(hops) >= 2, k
    # a FOLLOW ARCH item reaches the architectural set
    assert any(r["ITEM_ID"] == "S5-06" and r["NODE_KIND"] == "ARCHITECTURAL_REFERENCE" and r["LINK_STATE"] == "FOUND"
               for r in g)


def test_derived_items_rest_on_asserted_evidence(reg, ev):
    for k, r in reg.items():
        for e in filter(None, r["EVIDENCE_IDS"].split(";")):
            assert e in ev, (k, e)
        if r["TERMINAL_STATE"] == "SOURCE_FOUND_DERIVED" and r["NEW_SOURCE_THIS_ROUND"] == "TRUE":
            assert any(e.startswith(("E-PDF", "E-DXF")) for e in r["EVIDENCE_IDS"].split(";")), k


def test_footing_detail_long_bar_is_a_u_and_boxed_bar_an_inverted_u(ev, reg):
    f = ev["E-PDF-01"]["facts"]
    for name in ("SHALLOW", "DEEP"):
        d = f[name]
        assert len(d["long_bar_U"]["legs"]) == 2 and len(d["long_bar_U"]["hooks_45deg"]) == 2
        assert len(d["boxed_inverted_U"]["legs"]) == 2 and d["boxed_inverted_U"]["hooks"] == 0
        assert len(d["leader_on_long_bar"]) == 1 and len(d["leader_on_boxed_bar"]) == 1
    # the frozen 'straight' reading is withdrawn as a candidate, not edited in S4
    assert reg["S4-12"]["TERMINAL_STATE"] == "SOURCE_FOUND_DERIVED" and reg["S4-12"]["OLD_STATE"].startswith("VERIFIED")
    c = {r["CANDIDATE_ID"]: r for r in rows("07_S4_1_CANDIDATES.csv")}
    assert c["S4.1-C01"]["CHANGE_KIND"] == "CORRECTION_DOWNGRADE" and c["S4.1-C01"]["PROPOSED_NEW_STATE"] == "LOWER_BOUND"


def test_gb_links_and_the_unlabelled_short_section(ev):
    s = ev["E-PDF-02"]["facts"]
    assert len(s) == 4 and all(v["links"] == 1 and v["hook_branches"] >= 1 for v in s.values())
    assert s["GB_LT_2_5M (30x30)"]["label_leaders_on_link"] == 0
    assert all(v["label_leaders_on_link"] == 1 for k, v in s.items() if "2_5" not in k)


def test_lift_footing_two_16_are_wall_base_bars(ev):
    f = ev["E-PDF-03"]["facts"]
    assert [(w["top"], w["bottom"]) for w in f["bars_per_cut_wall"]] == [(2, 2), (2, 2)]
    assert len(f["two_16_leaders"]) == 2 and all(len(x) == 2 for x in f["two_16_leaders"])
    assert ev["E-DXF-05"]["facts"]["walls"] == 4


def test_cb_end_legs_reach_the_bottom_bar_level_and_typicals_are_nts(ev):
    legs = ev["E-PDF-04"]["facts"]["end_support_top_bar_legs"]
    assert len(legs) == 6 and {x["page"] for x in legs} == {11, 12}
    assert all(x["gap_to_bottom_bar_pt"] < 3.0 for x in legs)
    r = ev["E-DXF-06"]["facts"]["drawn_ratio"]
    assert abs(r["0.22 Ln"] - 0.22) > 0.02 and abs(r["0.15L"] - 0.15) > 0.02


def test_stirrup_icons_and_sb2_sheet_extent(ev):
    ic = ev["E-DXF-03"]["facts"]
    assert ic["icons"]["STR2"]["closed_rectangles"] == 2 and ic["icons"]["str3"]["closed_rectangles"] == 3
    rows_b = sorted({p["row"] for p in ic["placements"] if p["row"].startswith("B")})
    assert rows_b == ["B17", "B19", "B20", "B21", "B22", "B23", "B24", "B25", "B26"]
    assert {p["row"] for p in ic["placements"] if p["row"].startswith("SB")} == {"SB1", "SB2", "SB3"}
    sb2 = ev["E-DXF-04"]["facts"]["rows"]
    assert sb2["2ABA"]["inside_sheet_frame"] and not sb2["1FBB"]["inside_sheet_frame"]


def test_with_stair_detail_equals_the_b3_row(ev, reg):
    f = ev["E-DXF-07"]["facts"]
    assert {v["tag"] for v in f["with_stair_tags"].values()} == {"6B7", "6B9", "1827"}
    assert f["B3_row"] == {"W": 20, "H": 40, "BOTTOM": "4Ø16", "TOP": "2Ø12", "STIRRUPS": "6Ø8/m"}
    p16 = ev["E-PDF-06"]["facts"]["p16_TYPICAL_DETAIL_OF_STAIR_BEAM"]["callouts"]
    assert any("2Ø12" in c for c in p16) and any("4Ø16" in c for c in p16) and any("6Ø8/m" in c for c in p16)
    assert reg["S6-14"]["TERMINAL_STATE"] == "SOURCE_FOUND_DERIVED"


def test_builder_is_blind_and_never_touches_the_engine_pdf_stack():
    for f in ("build_source_recovery_delta.py", "vector_pdf.py"):
        src = (PKG / f).read_text(encoding="utf-8")
        for bad in ("christiannp", "CHRISTIANNP", "freelancer", "FREELANCER", "UC4N", "multi_engine", "benchmark",
                    "post_freeze_comparison", "rough_rebar", "kg/m3", "donor"):
            assert bad not in src, (f, bad)
        mods = set()
        for n in ast.walk(ast.parse(src)):
            if isinstance(n, ast.Import):
                mods |= {a.name for a in n.names}
            elif isinstance(n, ast.ImportFrom):
                mods.add(n.module or "")
                mods |= {f"{n.module}.{a.name}" for a in n.names}
        assert not [m for m in mods if any(x in m for x in ("fitz", "pymupdf", "pdf_vector_evidence"))], (f, mods)


def test_builder_is_registered_on_the_accurate_side():
    sys.path.insert(0, str(ROOT / "tests" / "structural_comparison_engine"))
    import rebar_product_registry as RP
    assert "research/source_recovery_delta/build_source_recovery_delta.py" in RP.ACCURATE_BUILDERS


def test_rebuild_is_byte_identical():
    before = {k: (PKG / k).read_bytes() for k in BUILT}
    subprocess.run([sys.executable, "-I", str(PKG / "build_source_recovery_delta.py")], check=True,
                   capture_output=True, cwd=ROOT)
    for k, v in before.items():
        assert (PKG / k).read_bytes() == v, k
