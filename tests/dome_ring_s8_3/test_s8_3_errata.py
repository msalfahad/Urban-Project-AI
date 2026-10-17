"""S8.3 errata: a dated correction layer that names what the frozen package mis-stated or missed, and moves nothing.

The frozen S8.3 package still verifies; the released quantities are the frozen ones; the unlabelled junction bar is
added as a blocked family; the mirrored-block evidence on the real drawings is recorded."""

from __future__ import annotations

import csv
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

from engine.source import delta_release as DR

ROOT = Path(__file__).resolve().parents[2]
PKG = ROOT / "research" / "alsenan_dome_ring_s8_3"
ER = PKG / "errata"
ST = ROOT / "data/inputs/by_sha256/9f9d1179a5d2a6635f9b412915a72184b7db1ff7729f4ab39a72dc3391738079.dxf"
AR = ROOT / "data/inputs/by_sha256/ab54dd554c31fe4a6a63ff773dc6d034159a736c7dd78158483b473a4ed31cc4.dxf"


def J(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def test_the_freeze_is_untouched_and_nothing_is_released_or_withdrawn():
    s = J(ER / "02_ERRATA_SUMMARY.json")
    assert s["frozen_manifest_sha256"] == DR.verify_frozen(PKG / "16_S8_3_FREEZE_MANIFEST.json", ROOT)["manifest_sha256"]
    assert s["released_unchanged"] == J(PKG / "15_S8_3_SUMMARY.json")["released"]
    assert s["references_read"] == [] and s["post_freeze_comparison_affected"] is False


def test_the_errata():
    rows = {r["ERRATUM_ID"]: r for r in csv.DictReader(open(ER / "01_S8_3_ERRATA.csv", encoding="utf-8"))}
    assert set(rows) == {"S8.3-E01", "S8.3-E02", "S8.3-E03"}
    assert rows["S8.3-E02"]["LANE"] == "BLOCKED_UNQUANTIFIED" and set(json.loads(rows["S8.3-E02"]["EVIDENCE"])) >= {"1A4D", "1A4F"}
    s = J(ER / "02_ERRATA_SUMMARY.json")
    assert all(c["labelled"] == 10 and c["by_row"] == [3, 2, 2, 3] for c in s["cuts"]) and all(s["small_bar_touches_shell_bar_leg"])
    assert s["added_blocked_families"] == {"DOME-A": ["UNLABELLED_JUNCTION_BAR"], "DOME-B": ["UNLABELLED_JUNCTION_BAR"]}
    m = s["mirror_census"]
    assert m["structural_non_plus_z"] == 0 and m["structural_mirrored_inserts"] == 0
    assert m["architectural_mirrored_inserts"] > 0 and m["architectural_mirrored_near_domes"] == 0


def test_registry_declares_the_errata_builder():
    sys.path.insert(0, str(ROOT / "tests" / "structural_comparison_engine"))
    import rebar_product_registry as RP
    assert "research/alsenan_dome_ring_s8_3/errata/build_errata.py" in RP.ACCURATE_BUILDERS


@pytest.mark.skipif(not (ST.exists() and AR.exists()), reason="private client drawings not restored in data/inputs/by_sha256")
def test_rebuild_is_byte_identical():
    names = sorted(p.name for p in ER.iterdir() if p.suffix in (".csv", ".json", ".md"))
    before = {n: hashlib.sha256((ER / n).read_bytes()).hexdigest() for n in names}
    subprocess.run([sys.executable, "-I", str(ER / "build_errata.py")], check=True, cwd=ROOT, capture_output=True)
    assert before == {n: hashlib.sha256((ER / n).read_bytes()).hexdigest() for n in names}
