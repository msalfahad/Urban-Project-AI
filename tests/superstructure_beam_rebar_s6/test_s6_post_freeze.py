"""S6 post-freeze comparison: downstream only, classified, never a source of an S6 quantity."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PKG = ROOT / "research" / "alsenan_superstructure_beam_rebar_s6"


def J(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def test_post_freeze_comparison_is_downstream_only():
    src = (PKG / "post_freeze_comparison.py").read_text(encoding="utf-8")
    main = src[src.index("def main("):]
    assert main.index("verify_freeze()") < main.index("old_simple(") < main.index("chris(") < main.index("freelancer(")
    s = J(PKG / "post_freeze" / "S6_POST_FREEZE_SUMMARY.json")
    assert s["freeze_manifest_verified"] is True
    assert s["frozen_engine_stamp"] == J(PKG / "S6_FREEZE_MANIFEST.json")["engine_commit_stamp"]
    for k in ("class_counts_old_urban", "class_counts_christiannp", "class_counts_freelancer_occurrences"):
        assert set(s[k]) <= set(s["classes"]) and "UNKNOWN" not in s[k], k
    assert s["unknown_rows"] == []
    for p in list(PKG.glob("*.py")) + [ROOT / "engine/source/superstructure_beam_rebar.py"]:
        if p.name != "post_freeze_comparison.py":
            assert "post_freeze_comparison" not in p.read_text(encoding="utf-8"), p.name


def test_comparison_scope_and_classes_match_the_brief():
    s = J(PKG / "post_freeze" / "S6_POST_FREEZE_SUMMARY.json")
    want = {"SCOPE_DIFFERENCE", "OCCURRENCE_DIFFERENCE", "BINDING_DIFFERENCE", "WIDTH_SOURCE_CONFLICT",
            "BAR_RUN_CONVENTION", "DETAIL_APPLICABILITY", "MID_EXTENT", "HANGER_MISSING", "ANCHORAGE_MISSING",
            "HOOK_MISSING", "STIRRUP_GEOMETRY_MISSING", "SIDE_REBAR_SEMANTICS", "ASSUMED_COMPONENT", "UNKNOWN"}
    assert want <= set(s["classes"])
    t = s["totals"]
    s6 = J(PKG / "SUPERSTRUCTURE_BEAM_RELEASE_SUMMARY.json")
    assert t["S6_TOTAL_KNOWN_KG"] == s6["known_source_derived_superstructure_beam_rebar_kg"]   # nothing tuned
    assert t["CHRIS"]["cb"].startswith("EXCLUDED") and s["class_counts_christiannp"]["SCOPE_DIFFERENCE"] == 13
    assert t["FREELANCER"]["class"].startswith("SCOPE_DIFFERENCE")
    assert "MID_EXTENT" in s["class_counts_old_urban"] and "HANGER_MISSING" in s["class_counts_old_urban"]
