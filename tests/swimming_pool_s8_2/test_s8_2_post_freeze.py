"""S8.2 post-freeze comparison: downstream only, frozen first (git-proved), every reference figure split into classes
that close on its difference, findings recorded and never applied, nothing tuned."""

from __future__ import annotations

import csv
import hashlib
import json
import math
import shutil
import subprocess
from collections import defaultdict
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
PKG = ROOT / "research" / "alsenan_swimming_pool_s8_2"
PF = PKG / "post_freeze"
MANIFEST = PKG / "18_S8_2_FREEZE_MANIFEST.json"
CLASSES = {"GEOMETRY", "SOURCE_NOT_IN_S8_2", "DEPTH_ASSUMPTION", "SCOPE", "NOTATION_SCOPE", "COUNT_CONVENTION",
           "BAR_LENGTH", "REFERENCE_FORMULA_MISMATCH", "BLOCKED_IN_S8_2", "UNSEPARATED", "SANITY_RATIO",
           "REFERENCE_ROUNDING", "UNKNOWN"}


def J(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def rows(name):
    with open(PF / name, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


@pytest.fixture(scope="module")
def s():
    return J(PF / "S8_2_POST_FREEZE_SUMMARY.json")


def _git(*a):
    return subprocess.run(["git", *a], cwd=ROOT, check=True, capture_output=True)


def test_freeze_before_comparison_guarantee(s):
    if not shutil.which("git") or not (ROOT / ".git").exists():
        pytest.skip("no git checkout")
    full = _git("rev-parse", "ae6393b").stdout.decode().strip()
    assert s["freeze_commit"] == full
    at_freeze = _git("show", f"{full}:research/alsenan_swimming_pool_s8_2/18_S8_2_FREEZE_MANIFEST.json").stdout
    assert hashlib.sha256(at_freeze).hexdigest() == hashlib.sha256(MANIFEST.read_bytes()).hexdigest() \
        == s["freeze_manifest_sha256"]
    tree = _git("ls-tree", "-r", "--name-only", full, "research/alsenan_swimming_pool_s8_2/").stdout.decode().split()
    assert tree and not any("post_freeze" in t for t in tree)             # no comparison existed at the freeze
    m = J(MANIFEST)
    assert m["references_read"] == [] and m["state"] == "FROZEN_BEFORE_COMPARISON"


def test_frozen_outputs_are_untouched():
    m = J(MANIFEST)
    for name, h in m["outputs"].items():
        assert hashlib.sha256((PKG / name).read_bytes()).hexdigest() == h, name


def test_comparison_is_downstream_only(s):
    src = (PF / "post_freeze_comparison.py").read_text(encoding="utf-8")
    main = src[src.index("def main("):]
    first_ref = min(main.index(x) for x in ("v3b()", "r4()", "multi_engine()", "freelancer_rows()"))
    assert main.index("verify_freeze()") < main.index("s8_2()") < first_ref
    assert s["freeze_manifest_verified"] is True and s["tuned"] is False and s["s8_2_outputs_written"] is False
    assert s["frozen_engine_stamp"] == J(MANIFEST)["engine_commit_stamp"]
    for p in (PKG / "build_s8_2.py", ROOT / "engine/source/pool_qto.py"):
        assert "post_freeze" not in p.read_text(encoding="utf-8"), p.name
    assert "write_text" not in "".join(ln for ln in src.splitlines() if "PKG /" in ln)  # never writes the package
    reg = (ROOT / "tests/structural_comparison_engine/rebar_product_registry.py").read_text(encoding="utf-8")
    assert '"research/alsenan_swimming_pool_s8_2/post_freeze/post_freeze_comparison.py"' in reg


def test_nothing_released_so_every_reference_figure_is_a_difference(s):
    assert s["s8_2"]["released_m3"] == 0.0 and s["s8_2"]["released_kg"] == 0.0
    for t in rows("S8_2_POST_FREEZE_REFERENCE_TOTALS.csv"):
        assert float(t["S8_2_RELEASED"]) == 0.0 and float(t["DIFFERENCE"]) == pytest.approx(float(t["REFERENCE_VALUE"]))
        assert t["S8_2_STATE"].startswith("BLOCKED")


def test_every_difference_is_classified_and_closes(s):
    tot = {(t["REFERENCE"], t["QUANTITY"], t["COMPONENT"]): float(t["DIFFERENCE"])
           for t in rows("S8_2_POST_FREEZE_REFERENCE_TOTALS.csv")}
    got = defaultdict(float)
    for c in rows("S8_2_POST_FREEZE_DIFFERENCE_CAUSES.csv"):
        assert c["CLASS"] in CLASSES
        got[(c["REFERENCE"], c["QUANTITY"], c["COMPONENT"])] += float(c["QTY"])
    assert set(got) == set(tot)
    for k, v in tot.items():
        assert math.isclose(got[k], v, abs_tol=1e-6), k
    assert s["unknown_rows"] == [] and set(s["classes"]) == CLASSES


def test_reference_totals_equal_their_own_parts(s):
    assert all(v[2] for v in s["reference_consistency"].values())
    assert s["reference_totals"]["OLD_URBAN_V3B|CONCRETE_M3"] == pytest.approx(5.053)
    assert s["reference_totals"]["OLD_URBAN_V3B|REBAR_KG"] == pytest.approx(585.738272)
    assert s["reference_totals"]["FREELANCER_QS|CONCRETE_M3"] == pytest.approx(12.348)


def test_geometry_class_uses_the_frozen_footprint(s):
    c = {(r["REFERENCE"], r["COMPONENT"], r["CLASS"]): float(r["QTY"]) for r in rows("S8_2_POST_FREEZE_DIFFERENCE_CAUSES.csv")}
    A = s["s8_2"]["footprint_m2"]
    assert c[("OLD_URBAN_V3B", "POOL_BASE", "GEOMETRY")] == pytest.approx((3.50 * 1.95 - A) * 0.40)
    assert c[("OLD_URBAN_V3B", "POOL_BASE", "BLOCKED_IN_S8_2")] == pytest.approx(A * 0.40)
    assert c[("FREELANCER_QS", "I13 حوائط المضخة", "SCOPE")] == pytest.approx(1.08)


def test_findings_are_recorded_not_applied(s):
    f = {r["FINDING_ID"]: r for r in rows("S8_2_POST_FREEZE_FINDINGS.csv")}
    assert set(f) == {f"F-S8.2-PF-0{i}" for i in range(1, 8)} == set(s["findings"])
    assert f["F-S8.2-PF-01"]["CLASS"] == "SOURCE_NOT_IN_S8_2" and f["F-S8.2-PF-01"]["STATUS"].startswith("OPEN")
    assert "281a0c3f" in f["F-S8.2-PF-01"]["TEXT"]                     # the architectural PDF S8.2 did not hold
    summary = J(PKG / "17_S8_2_SUMMARY.json")
    assert summary["concrete"]["released_m3"] == 0.0 and summary["reinforcement"]["released_kg"] == 0.0


def test_rough_ratio_is_sanity_only_and_absent_references_are_recorded(s):
    t = {r["REFERENCE"]: r for r in rows("S8_2_POST_FREEZE_REFERENCE_TOTALS.csv")}
    assert t["ROUGH_RATIO"]["REFERENCE_ORIGIN"].startswith("SANITY_CHECK_ONLY")
    assert {r["REFERENCE"] for r in s["no_reference_quantity"]} == {"CHRISTIANNP", "U-C4N"}
