"""Alsenan coverage-recovery round package: freeze integrity, blind firewall, conservation and scenario invariants."""

from __future__ import annotations

import ast
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
PKG = ROOT / "research" / "coverage_recovery_round"


def J(name):
    return json.loads((PKG / name).read_text(encoding="utf-8"))


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def numbers(o):
    if isinstance(o, dict):
        for v in o.values():
            yield from numbers(v)
    elif isinstance(o, list):
        for v in o:
            yield from numbers(v)
    elif isinstance(o, (int, float)) and not isinstance(o, bool):
        yield o


def donor_numbers():
    """The donor / reference figures, read from the post-freeze script by AST (never executed here)."""
    tree = ast.parse((PKG / "post_freeze_comparison.py").read_text(encoding="utf-8"))
    out = set()
    for n in tree.body:
        if isinstance(n, ast.Assign) and isinstance(n.targets[0], ast.Name) and n.targets[0].id in (
                "UC4N", "CNP", "FREELANCER"):
            out |= set(ast.literal_eval(n.value).values())
    return out


def hit(v, refs):
    return bool(v) and any(abs(v - x) <= 1e-4 * abs(x) for x in refs)


# V3b straps (3.392 m3) predates every donor run and comes straight from the V3b BOQ lines input; the freelancer
# figure happens to coincide. Allowed only where it is the V3b straps value.
V3B_STRAPS = 3.392


def test_index_hashes_match():
    idx = J("INDEX.json")
    for k, h in {**idx["outputs"], **idx["extracts"]}.items():
        assert sha(PKG / k) == h, k
    assert sha(PKG / idx["freeze"]) == idx["freeze_sha256"]
    assert set(idx["blind_outputs"]).isdisjoint(idx["post_freeze_outputs"])


def test_freeze_holds_and_was_blind():
    fz = J("COVERAGE_RECOVERY_FREEZE.json")
    assert fz["donor_values_read"] is False and fz["reference_qs_read"] is False
    for k, h in fz["outputs"].items():
        assert sha(PKG / k) == h, f"{k} changed after the freeze"
    assert "POST_FREEZE_MCP_COMPARISON.json" not in fz["outputs"]
    assert "ROOT_CAUSE_REGISTER.json" not in fz["outputs"]


def test_blind_outputs_hold_no_donor_numbers():
    refs = donor_numbers()
    assert refs, "donor dicts not found"
    for k in J("COVERAGE_RECOVERY_FREEZE.json")["outputs"]:
        for v in numbers(J(k)):
            if v == V3B_STRAPS:
                continue
            assert not hit(v, refs), f"{k}: {v}"
    straps = J("COVERAGE_BASELINE.json")["concrete_by_trade"]["STRAPS"]
    assert straps["technical_m3"] == V3B_STRAPS


@pytest.mark.parametrize("script", ["build_coverage_recovery.py", "extract_geometry.py", "build_review_workbook.py"])
def test_blind_scripts_hold_no_donor_numbers_or_names(script):
    src = (PKG / script).read_text(encoding="utf-8")
    refs = donor_numbers()
    for n in ast.walk(ast.parse(src)):
        if isinstance(n, ast.Constant) and isinstance(n.value, (int, float)) and not isinstance(n.value, bool):
            assert not hit(n.value, refs), f"{script}:{n.lineno} {n.value}"
    tree = ast.parse(src)
    for n in ast.walk(tree):
        if isinstance(n, (ast.Import, ast.ImportFrom)):
            mods = [a.name for a in n.names] + [getattr(n, "module", None) or ""]
            assert not any("post_freeze" in m for m in mods), f"{script}:{n.lineno} imports the post-freeze script"
        if isinstance(n, ast.Name):
            assert n.id not in ("UC4N", "CNP", "FREELANCER"), f"{script}:{n.lineno} {n.id}"
    if script != "build_review_workbook.py":       # the workbook shows the post-freeze sheets, read from JSON
        doc = ast.get_docstring(tree, clean=False) or ""
        code = src.replace(doc, "", 1)
        for name in ("UC4N", "christiannp", "FREELANCER"):
            assert name not in code, name


def test_engine_modules_hold_no_donor_numbers():
    refs = donor_numbers()
    mods = ["beam_occurrence_recovery", "blocker_remediation", "column_concrete_geometry", "coverage_anomaly",
            "coverage_metrics", "evidence_ladder", "ground_beam_recovery", "ground_slab_recovery",
            "multi_route_evidence", "physical_measurement_state", "physical_wall_faces", "population_conservation",
            "quantity_scenarios", "slab_opening_reconciliation", "wall_band_reconciliation", "rebar_sanity_qa"]
    for m in mods:
        tree = ast.parse((ROOT / "engine" / "source" / f"{m}.py").read_text(encoding="utf-8"))
        for n in ast.walk(tree):
            if isinstance(n, ast.Constant) and isinstance(n.value, (int, float)) and not isinstance(n.value, bool):
                assert not hit(n.value, refs), f"{m}:{n.lineno} {n.value}"


def test_population_conservation():
    b = J("BLOCKED_OCCURRENCE_ANALYSIS.json")["populations"]
    col = b["column_occurrences_without_technical_concrete"]["after"]
    assert sum(col.values()) == 95 and "UNQUANTIFIED" not in col
    gb = b["ground_beam_exterior_spans"]
    assert sum(gb["after"].values()) == gb["count"] == 28
    beams = b["beam_residue"]
    assert sum(beams["after"].values()) == beams["count"]
    anomalies = J("COVERAGE_METRICS.json")["anomalies"]
    text = json.dumps(anomalies)
    assert "CONSERVATION_FAILURE" in text      # the "before" column records


LAYERS = ("verified", "lower_bound", "low", "best_provisional", "high")


def test_dashboard_scenario_invariants():
    rows = J("QUANTITY_COVERAGE_DASHBOARD.json")["rows"]
    trades = {r["trade"] for r in rows}
    assert {"GROUND_BEAMS", "GROUND_SLAB"} <= trades
    for r in rows:
        chain = [r[k] for k in LAYERS if r[k] is not None]
        assert chain == sorted(chain), (r["trade"], chain)
        if r["unquantified"]:
            assert r["high"] is None, r["trade"]       # unbounded while any object is unquantified
        assert r["release"] and r["top_blocker"] is not None and r["how_to_fix"] is not None


def test_scenarios_never_publish_blocked_as_zero():
    q = J("QUANTITY_SCENARIOS.json")
    for trade in ("ground_beams", "ground_slab", "columns", "beams"):
        best = q[trade]
        best = best.get("BEST_PROVISIONAL_QUANTITY", best.get("total", {}).get("BEST_PROVISIONAL_QUANTITY")) \
            if isinstance(best, dict) else None
        if best is not None:
            assert best > 0, trade


def test_every_slab_deduction_has_an_opening_id():
    sheets = J("QUANTITY_SCENARIOS.json")["slabs"]["sheets"]
    assert sheets
    for floor, s in sheets.items():
        for o in s["openings"]:
            assert o["opening_id"] and o["opening_id"].startswith(f"{floor}:"), o
            assert o["area_m2"] > 0
            if o["state"] == "OPENING_CONFLICT":
                assert o["why_conflict"]


def test_post_freeze_registers_present():
    pf = J("POST_FREEZE_MCP_COMPARISON.json")
    assert pf["difference_register"]
    for r in pf["difference_register"]:
        assert r["reason_class"] and r["basis_match"] is not None
    assert J("ROOT_CAUSE_REGISTER.json")


def _inputs_present():
    fz = J("COVERAGE_RECOVERY_FREEZE.json")
    return all((ROOT / k).exists() for k in fz["inputs"])


@pytest.mark.skipif(not _inputs_present(), reason="local data/ inputs not present (gitignored)")
def test_rebuild_reproduces_frozen_outputs():
    spec = importlib.util.spec_from_file_location("ccr_build", PKG / "build_coverage_recovery.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    _, blobs = mod.main(write=False)
    fz = J("COVERAGE_RECOVERY_FREEZE.json")
    for k, h in fz["outputs"].items():
        assert hashlib.sha256(blobs[k]).hexdigest() == h, k
