"""christiannp blind-run forensic package: honesty and reproducibility of the Urban-side cross-checks."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PKG = ROOT / "research" / "christiannp_blind_process"
OUTPUTS = ("process_log/EVIDENCE_INVENTORY.json", "intermediate_geometry/URBAN_CROSSCHECKS.json",
           "CHRISTIANNP_WALL_PAIRING_DIAGNOSTIC.json", "CHRISTIANNP_VS_URBAN_GAP_REGISTER.json",
           "CHRISTIANNP_ASSUMPTION_FORENSICS.json")


def J(name):
    return json.loads((PKG / name).read_text(encoding="utf-8"))


def _builder():
    spec = importlib.util.spec_from_file_location("cnp_build", PKG / "scripts" / "build_crosschecks.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_builder_reproduces_outputs_byte_for_byte():
    mod = _builder()
    before = {n: (PKG / n).read_bytes() for n in OUTPUTS}
    mod.main()
    after = {n: (PKG / n).read_bytes() for n in OUTPUTS}
    assert before == after


def test_deliverables_present():
    for n in ("CHRISTIANNP_BLIND_PROCESS_HANDOFF.md", "CHRISTIANNP_DONOR_LESSONS.md", "CHRISTIANNP_RECOMMENDATIONS.md",
              *OUTPUTS):
        assert (PKG / n).exists(), n
    for d in ("tool_calls", "lisp", "scripts", "raw_extractions", "intermediate_geometry", "process_log",
              "failed_attempts"):
        assert (PKG / d / "README.md").exists(), d


def test_donor_pairs_are_never_presented_as_held():
    w = J("CHRISTIANNP_WALL_PAIRING_DIAGNOSTIC.json")
    assert w["christiannp_pairs"].startswith("NOT_PRESERVED")
    assert set(w["christiannp_parameters"].values()) == {"NOT_HELD"}
    for r in w["rows"]:
        assert r["face_handle_a"].startswith("ALSENAN_P7757_DXF|") and r["face_handle_b"].startswith("ALSENAN_P7757_DXF|")
        assert r["accepted_reason"] in ("PAIRED_WALL", "OPENING_SPAN", "COLUMN_OVERLAP_POLICY", "DUPLICATE_FACE")


def test_every_gap_row_is_classified():
    g = J("CHRISTIANNP_VS_URBAN_GAP_REGISTER.json")
    trades = {r["trade"] for r in g["rows"]}
    assert {"GROUND_BEAMS", "GROUND_SLAB", "COLUMN_CONCRETE", "BEAMS", "SLAB_NET_AREA", "SLAB_OPENINGS", "WALLS_150",
            "WALLS_200", "PLASTER", "FOOTINGS", "STAIRS"} <= trades
    for r in g["rows"]:
        assert r["classification"] in g["classification_key"], r["trade"]
        assert r["must_not_hardcode"], r["trade"]


def test_unrelayed_assumptions_are_not_invented():
    rows = {r["id"]: r for r in J("CHRISTIANNP_ASSUMPTION_FORENSICS.json")["rows"]}
    assert sorted(rows, key=lambda k: int(k[1:])) == [f"A{i}" for i in range(1, 16)]
    for k, r in rows.items():
        if k in ("A1", "A5", "A7", "A8"):
            assert r["text_status"] == "RELAYED" and r["adopt"].startswith("NO")
        else:
            assert r["text_status"] == "NOT_HELD" and r["assumption"] is None


def test_ground_beam_reproduction_and_population():
    gb = J("intermediate_geometry/URBAN_CROSSCHECKS.json")["ground_beams"]
    assert gb["inferred_reproduction"]["matches_relayed"] is True
    assert abs(gb["length_difference_pct"]) < 1.0          # same population; the gap is the section


def test_no_engine_module_reads_this_package():
    for p in (ROOT / "engine").rglob("*.py"):
        assert "christiannp_blind_process" not in p.read_text(encoding="utf-8", errors="ignore"), p
