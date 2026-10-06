"""christiannp blind-run forensic package (v2): evidence classes, honesty and reproducibility."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
PKG = ROOT / "research" / "christiannp_blind_process"
OUTPUTS = ("process_log/EVIDENCE_INVENTORY.json", "intermediate_geometry/URBAN_CROSSCHECKS.json",
           "CHRISTIANNP_WALL_PAIRING_DIAGNOSTIC.json", "CHRISTIANNP_VS_URBAN_GAP_REGISTER.json",
           "CHRISTIANNP_ASSUMPTION_FORENSICS.json", "CHRISTIANNP_BEAM_RULES_R1_R5.json",
           "CHRISTIANNP_RASTER_METHOD_SPEC.json", "CHRISTIANNP_DONOR_AGREEMENT.json",
           "CHRISTIANNP_UNRESOLVED_REBAR.json")
CLASSES = {"REPORT_EXPLICIT", "URBAN_FROZEN", "ARITHMETIC_INFERENCE", "NOT_HELD"}


def J(name):
    return json.loads((PKG / name).read_text(encoding="utf-8"))


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_builder_reproduces_outputs_byte_for_byte():
    before = {n: (PKG / n).read_bytes() for n in OUTPUTS}
    _load("cnp_build", PKG / "scripts" / "build_crosschecks.py").main()
    assert before == {n: (PKG / n).read_bytes() for n in OUTPUTS}


def test_deliverables_present():
    for n in ("CHRISTIANNP_BLIND_PROCESS_HANDOFF.md", "CHRISTIANNP_DONOR_LESSONS.md", "CHRISTIANNP_RECOMMENDATIONS.md",
              *OUTPUTS):
        assert (PKG / n).exists(), n
    for d in ("tool_calls", "lisp", "scripts", "raw_extractions", "intermediate_geometry", "process_log",
              "failed_attempts"):
        assert (PKG / d / "README.md").exists(), d


def test_four_evidence_classes_only():
    inv = J("process_log/EVIDENCE_INVENTORY.json")
    assert set(inv["classes"]) == CLASSES
    for n in OUTPUTS:
        txt = (PKG / n).read_text(encoding="utf-8")
        assert '"RELAYED"' not in txt and '"INFERRED"' not in txt, n
    for k in ("chronological MCP session / tool-call transcript", "raw LISP history", "raw wall pairs",
              "raw raster cells", "raw beam allocations"):
        assert k in inv["NOT_HELD"], k


def test_all_fifteen_assumptions_imported_and_classified():
    rows = {r["id"]: r for r in J("CHRISTIANNP_ASSUMPTION_FORENSICS.json")["rows"]}
    assert list(rows) == [f"A{i}" for i in range(1, 16)]
    for r in rows.values():
        assert r["evidence"] == "REPORT_EXPLICIT" and r["assumption"]
        assert r["nature"] in ("SOURCE_SUPPORTED", "DERIVED", "ASSUMPTION")
        assert r["urban_review"] in ("SOURCE_SUPPORTED", "KNOWN_WRONG_AFTER_URBAN_REVIEW", "PLAUSIBLE_BUT_UNVERIFIED")
    for k in ("A1", "A5", "A8", "A14", "A15"):
        assert rows[k]["urban_review"] == "KNOWN_WRONG_AFTER_URBAN_REVIEW", k
    assert {k for k, r in rows.items() if r["production"] != "REJECT_FOR_PRODUCTION"} == {"A4", "A6"}


def test_beam_rules_r5_rejected_none_auto_adopted():
    rows = {r["id"]: r for r in J("CHRISTIANNP_BEAM_RULES_R1_R5.json")["rows"]}
    assert list(rows) == ["R1", "R2", "R3", "R4", "R5"]
    assert rows["R5"]["production_candidate"].startswith("NO") and rows["R5"]["oracle_only"] is True
    assert rows["R3"]["oracle_only"] is True
    for r in rows.values():
        assert r["tests"] and r["failure_modes"] and r["evidence"] == "REPORT_EXPLICIT"


def test_raster_spec_separates_report_from_not_held():
    s = J("CHRISTIANNP_RASTER_METHOD_SPEC.json")
    assert s["REPORT_EXPLICIT"]["cell_mm"] == 50
    assert s["REPORT_EXPLICIT"]["classes"] == ["SLAB_LABELLED", "BEAM_INTERIOR", "OPENING", "UNRESOLVED_ENCLOSED",
                                               "EDGE_LINE_CELLS"]
    for k in ("exact grid origin", "exact cell list", "raw script"):
        assert k in s["NOT_HELD"]
    assert s["urban_oracle_design"]["authority"].startswith("ORACLE_ONLY")


def test_donor_agreement_covers_required_elements():
    a = J("CHRISTIANNP_DONOR_AGREEMENT.json")
    classes = set(a["classes"])
    els = {r["element"]: r for r in a["rows"]}
    for e in ("COLUMNS", "SLABS (volume)", "GROUND BEAMS (volume)", "GROUND BEAMS (length)", "GROUND SLAB", "STAIRS"):
        assert e in els, e
        assert any(c in els[e]["class"] for c in classes), e
    assert els["COLUMNS"]["class"] == "SHARED_ASSUMPTION_AGREEMENT"
    assert els["GROUND BEAMS (length)"]["class"] == "INDEPENDENT_EXTRACTION_AGREEMENT"


def test_ground_beam_geometry_and_depth_kept_apart():
    gb = J("intermediate_geometry/URBAN_CROSSCHECKS.json")["ground_beams"]
    assert gb["REPORT_EXPLICIT"]["depth"]["status"] == "ASSUMPTION A5"
    assert "not a source-measured volume" in gb["REPORT_EXPLICIT"]["volume"]["status"]
    assert gb["ARITHMETIC_INFERENCE"]["matches_report"] is True
    assert abs(gb["length_difference_pct"]) < 1.0


def test_urban_values_are_version_stamped():
    for k, v in J("intermediate_geometry/URBAN_CROSSCHECKS.json")["versions"].items():
        assert set(v) == {"ENGINE_COMMIT", "REGISTER_VERSION", "DRAWING_SHA", "CALCULATION_ROUND"}, k
    for r in J("CHRISTIANNP_VS_URBAN_GAP_REGISTER.json")["rows"]:
        assert r["classification"] in "ABCDE" and r["christiannp"]["evidence"] == "REPORT_EXPLICIT"


def test_rebar_is_known_incomplete():
    r = J("CHRISTIANNP_UNRESOLVED_REBAR.json")
    assert r["label"] == "KNOWN_INCOMPLETE_NET_DRAWING_REBAR" and len(r["unresolved_items"]) >= 9


def test_quote_verifier(tmp_path, monkeypatch):
    v = _load("cnp_verify", PKG / "scripts" / "verify_report_quotes.py")
    monkeypatch.setattr(v, "REPORT", tmp_path / "missing.md")
    assert v.main() is None
    rep = tmp_path / "r.md"
    rep.write_text("## Assumptions\nA5 ground-beam depth 0.60 m\nR5 remaining length shared equally\n", encoding="utf-8")
    monkeypatch.setattr(v, "REPORT", rep)
    monkeypatch.setattr(v, "OUT", tmp_path / "out.json")
    out = v.main()
    assert out["checks"]["A5"]["status"] == "FOUND" and out["checks"]["R5"]["status"] == "FOUND"
    assert "A1" in out["not_found"]


def test_no_engine_module_reads_this_package():
    for p in (ROOT / "engine").rglob("*.py"):
        assert "christiannp_blind_process" not in p.read_text(encoding="utf-8", errors="ignore"), p
