"""M6 package (research/urban_engine_m6_completeness): what is committed is what the frozen engines produce.

  - hygiene: no owner name, no title-block text, no Arabic run in any package file or in the engine and tools
  - each engine freeze manifest holds the hashes of the files as committed at its freeze commit (read with git)
  - each run manifest holds the hashes of its own output files; the V2 run is POST_DISCOVERY and left V1 untouched
  - the held-out V2 summary is the summary of its own run records; the V1 held-out seeds re-run on V2 equal V1's
  - live (needs the private ST7757 drawings and git): the V1 blind files rebuild byte for byte with the V1 engine
    read from git, the V2 files with the V2 engine read from git; the reconciliation rebuilds from both frozen runs
"""

from __future__ import annotations

import csv
import hashlib
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
PKG = ROOT / "research/urban_engine_m6_completeness"
DXF = ROOT / "data/inputs/by_sha256/9f9d1179a5d2a6635f9b412915a72184b7db1ff7729f4ab39a72dc3391738079.dxf"
ARCH = ROOT / "data/inputs/by_sha256/ab54dd554c31fe4a6a63ff773dc6d034159a736c7dd78158483b473a4ed31cc4.dxf"
HYGIENE = re.compile(r"YEARS 2013|7757-[A-Z]|[؀-ۿ]{3,}|(?i:als[ey]?n[ya]?an)")
GIT = bool(shutil.which("git")) and (ROOT / ".git").exists()
TEXT = (".py", ".json", ".csv", ".md")


def _git_bytes(commit, path):
    return subprocess.run(["git", "-C", str(ROOT), "show", f"{commit}:{path}"], capture_output=True,
                          check=True).stdout


def _pkg_module(name):
    for p in (str(ROOT), str(PKG)):
        if p not in sys.path:
            sys.path.insert(0, p)
    return __import__(name)


def test_package_files_are_clean():
    files = [p for p in PKG.rglob("*") if p.suffix in TEXT and "__pycache__" not in p.parts]
    files += [ROOT / "engine/source/concrete_completeness.py", ROOT / "tools/synthetic_villa_m6.py",
              ROOT / "tools/m6_evaluate.py", ROOT / "tools/m6_completeness_report.py"]
    assert len(files) > 15
    bad = [(str(p.relative_to(ROOT)), m.group(0)[:12]) for p in files
           for m in HYGIENE.finditer(p.read_text(encoding="utf-8"))]
    assert bad == []
    for name in ("README.md", "04_EXECUTIVE_REPORT.md", "05_WEAKNESS_REGISTER.csv", "00_ENGINE_FREEZE.json",
                 "01_BLIND_RUN_FREEZE.json", "02_ENGINE_FREEZE_V2.json", "03_V2_RUN_FREEZE.json"):
        assert (PKG / name).exists(), name


@pytest.mark.skipif(not GIT, reason="prerequisite: the git history")
@pytest.mark.parametrize("manifest,commit", [("00_ENGINE_FREEZE.json", "090a470"),
                                             ("02_ENGINE_FREEZE_V2.json", "6c20879")])
def test_engine_freezes_hold_the_committed_files(manifest, commit):
    man = json.loads((PKG / manifest).read_text(encoding="utf-8"))
    for path, sha in man["files_sha256"].items():
        assert hashlib.sha256(_git_bytes(commit, path)).hexdigest() == sha, path
    assert man["policy"] == ("CONCRETE_COMPLETENESS_V1" if commit == "090a470" else "CONCRETE_COMPLETENESS_V2")


def test_run_manifests_hold_their_files_and_v1_is_untouched():
    v1 = json.loads((PKG / "01_BLIND_RUN_FREEZE.json").read_text(encoding="utf-8"))
    v2 = json.loads((PKG / "03_V2_RUN_FREEZE.json").read_text(encoding="utf-8"))
    for man in (v1, v2):
        for name, sha in man["files_sha256"].items():
            assert hashlib.sha256((PKG / name).read_text(encoding="utf-8").encode("utf-8")).hexdigest() == sha, name
    assert v1["engine_commit"] == "090a470" and v1["phase"] == "BLIND_GEOMETRY_INTERPRETATION"
    assert v2["engine_commit"] == "6c20879" and v2["run_phase"] == "POST_DISCOVERY"
    assert v2["v1_blind_run"]["untouched"] and v2["inputs_sha256"] == v1["inputs_sha256"]
    assert all(k.startswith("post_discovery_v2/") for k in v2["files_sha256"])
    rows = list(csv.DictReader(open(PKG / "post_discovery_v2/COMPLETENESS_FINDINGS.csv", encoding="utf-8")))
    assert len(rows) == v2["findings"] and all(r["ACTION"] for r in rows)


def test_heldout_v2_summary_is_its_own_records():
    S = json.loads((PKG / "heldout/HELDOUT_V2_SUMMARY.json").read_text(encoding="utf-8"))
    for cfg, name in (("A2", "HELDOUT_V2_DEV_VOCABULARY.json"), ("B2", "HELDOUT_V2_HELDOUT_VOCABULARY_HARD.json")):
        rec = json.loads((PKG / "heldout" / name).read_text(encoding="utf-8"))
        assert [d["seed"] for d in rec["drawings"]] == list(range(201, 241))
        assert all(d["m6v2"] for d in rec["drawings"])
        for k in ("elements", "detected", "false_findings", "family_of_detected"):
            assert S["V2_engine"][cfg][k] == rec["summary"][k], (cfg, k)
        assert len([c for c in S["false_findings_classified_post_hoc"] if c["config"] == cfg]) == \
            rec["summary"]["false_findings"]
    re1 = S["V1_heldout_seeds_101_140_rerun_on_V2"]
    for a, b in (("A1_dev_vocabulary", "A1"), ("B1_heldout_vocabulary_hard", "B1")):
        for k in ("elements", "detected", "false_findings", "false_findings_by_kind"):
            assert re1[a][k] == re1["recorded_V1"][b][k], (a, k)


def test_reconciliation_tallies():
    S = json.loads((PKG / "reconciliation/01_RECONCILIATION_SUMMARY.json").read_text(encoding="utf-8"))
    R = S["results"]
    assert set(R) == {"V1_M1", "V1_M2", "V2_M1", "V2_M2"}
    for k, v in R.items():
        assert v["detected"] + v["detected_unidentified"] + len(v["missed"]) == v["completeness_cases"], k
    assert R["V1_M1"]["engine_commit"] == "090a470" and R["V2_M2"]["engine_commit"] == "6c20879"
    assert R["V2_M2"]["run_phase"] == "POST_DISCOVERY" and "not blind" in S["rule"]


LIVE = pytest.mark.skipif(not (GIT and DXF.exists() and ARCH.exists()),
                          reason="prerequisite: the private ST7757 drawings and the git history")


@LIVE
def test_both_runs_rebuild_byte_for_byte_from_the_frozen_engines():
    V = _pkg_module("v2_run")
    assert V.reproduce_v1() == []
    assert V.reproduce_v2() == []


M5 = ROOT / "research/urban_engine_m5_concrete_reconciliation"


@pytest.mark.skipif(not ((M5 / "03A_ELEMENT_MEMBERSHIP.csv").exists() and
                         (ROOT / "research/christiannp_blind_process").exists()),
                    reason="prerequisite: the M5 element crosswalk and the MCP records")
def test_reconciliation_rebuilds_from_the_frozen_runs():
    RC = _pkg_module("reconcile")
    out = RC.outputs()
    assert [k for k, v in out.items() if (PKG / k).read_text(encoding="utf-8") != v] == []
