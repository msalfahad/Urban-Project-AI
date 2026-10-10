"""S7 post-freeze comparison: downstream only, frozen first (git-proved), every difference classified, nothing tuned."""

from __future__ import annotations

import csv
import hashlib
import json
import math
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
PKG = ROOT / "research" / "alsenan_slab_rebar_s7"
PF = PKG / "post_freeze"
CLASSES = {"SCOPE", "TEMPERATURE_EXCLUDED", "SPECIAL_STRUCTURE_EXCLUDED", "ANCHORAGE_EXCLUDED", "COVER_BASIS",
           "CURTAILMENT", "TOP_SUPPORT_RULE", "COUNT_CONVENTION", "OPENING", "TRANSITION", "REFERENCE_ASSUMPTION",
           "GEOMETRY", "OTHER_KNOWN"}


def J(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def rows(p):
    with open(p, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


@pytest.fixture(scope="module")
def s():
    return J(PF / "S7_POST_FREEZE_SUMMARY.json")


def _git(*a):
    return subprocess.run(["git", *a], cwd=ROOT, check=True, capture_output=True)


def test_freeze_before_reference_guarantee(s):
    if not shutil.which("git") or not (ROOT / ".git").exists():
        pytest.skip("no git checkout")
    full = _git("rev-parse", "16741ec").stdout.decode().strip()
    assert s["freeze_commit"] == full
    at_freeze = _git("show", f"{full}:research/alsenan_slab_rebar_s7/12_S7_FREEZE_MANIFEST.json").stdout
    assert hashlib.sha256(at_freeze).hexdigest() == hashlib.sha256(
        (PKG / "12_S7_FREEZE_MANIFEST.json").read_bytes()).hexdigest() == s["freeze_manifest_sha256"]
    tree = _git("ls-tree", "-r", "--name-only", full, "research/alsenan_slab_rebar_s7/").stdout.decode().split()
    assert tree and not any("post_freeze" in t for t in tree)             # no comparison existed at the freeze
    assert _git("merge-base", "--is-ancestor", full, "HEAD").returncode == 0
    m = J(PKG / "12_S7_FREEZE_MANIFEST.json")
    assert m["references_read_before_freeze"] == [] and m["state"] == "FROZEN_BEFORE_REFERENCE_COMPARISON"


def test_post_freeze_comparison_is_downstream_only(s):
    src = (PF / "post_freeze_comparison.py").read_text(encoding="utf-8")
    main = src[src.index("def main("):]
    first_ref = min(main.index(x) for x in ("r4_components(", "_j(R3)", "_j(V3B)", "_j(LINEAGE)", "_j(ORACLES)",
                                            "christiannp(", "_j(ROUGH)"))
    assert main.index("verify_freeze()") < main.index("s7()") < first_ref
    assert s["freeze_manifest_verified"] is True and s["tuned"] is False and s["s7_outputs_written"] is False
    assert s["frozen_engine_stamp"] == J(PKG / "12_S7_FREEZE_MANIFEST.json")["engine_commit_stamp"]
    for p in [PKG / "build_s7.py", ROOT / "engine/source/slab_rebar_qto.py"]:
        assert "post_freeze_comparison" not in p.read_text(encoding="utf-8"), p.name
    assert "write_text" not in "".join(l for l in src.splitlines() if "PKG /" in l)    # never writes the package
    reg = (ROOT / "tests/structural_comparison_engine/rebar_product_registry.py").read_text(encoding="utf-8")
    assert '"research/alsenan_slab_rebar_s7/post_freeze/post_freeze_comparison.py"' in reg


def test_nothing_tuned(s):
    assert s["s7_totals_kg"] == J(PKG / "09_S7_PROJECT_SUMMARY.json")["totals_kg"]
    for t in s["reference_totals"]:
        assert t["S7_KG"] == s["s7_totals_kg"]["RESTRICTED_S7_PROJECT_BASIS_KG"]


def test_every_difference_is_classified_and_closes(s):
    assert set(s["classes"]) >= CLASSES and s["unknown_rows"] == []
    for t in s["reference_totals"]:
        assert set(t["CLASSES"]) <= CLASSES, t["REFERENCE"]
        assert t["CLASSES_CLOSE"] is True, t["REFERENCE"]
        if t["DIFF_KG"] is not None:
            assert abs(math.fsum(t["CLASSES"].values()) - t["DIFF_KG"]) <= 1e-6, t["REFERENCE"]
    causes = rows(PF / "S7_POST_FREEZE_DIFFERENCE_CAUSES.csv")
    assert causes and {c["CLASS"] for c in causes} <= CLASSES and all(c["BASIS"] for c in causes)


def test_old_urban_matched_token_by_token(s):
    toks = rows(PF / "S7_POST_FREEZE_OLD_URBAN_R4_TOKENS.csv")
    assert len({t["TOKEN"] for t in toks}) == len(toks)
    rel = rows(PKG / "01_S7_RELEASE_ITEMS.csv")
    s7_tokens = {json.loads(r["SOURCE_RULE_IDS"])[0].split()[1] for r in rel if r["LAYER"] == "BOTTOM"}
    by = {t["TOKEN"]: t for t in toks}
    assert s7_tokens <= set(by)
    assert all(by[k]["STATUS"] == "MATCHED" for k in s7_tokens)
    for t in toks:
        cls = json.loads(t["CLASSES"])
        assert abs(math.fsum(c["kg"] for c in cls) - float(t["DIFF_KG_R4_MINUS_S7"])) <= 1e-6, t["TOKEN"]
        assert {c["class"] for c in cls} <= CLASSES
    r4 = next(t for t in s["reference_totals"] if t["REFERENCE"] == "OLD_URBAN_R4")
    assert abs(r4["CLASSES"]["TOP_SUPPORT_RULE"] + s["s7_totals_kg"]["TOP_SUPPORT_PROJECT_BASIS_KG"]) <= 1e-6
    assert r4["CLASSES"]["SPECIAL_STRUCTURE_EXCLUDED"] > 0          # tank T&B, light-well 8Ø16/m, dome / stair


def test_freelancer_uc4n_christiannp_and_rough(s):
    tot = {t["REFERENCE"]: t for t in s["reference_totals"]}
    fr = tot["FREELANCER"]
    assert fr["MATCHING"] == "CATEGORY" and fr["REFERENCE_KG"] == 5400.0
    assert set(fr["CLASSES"]) == {"SPECIAL_STRUCTURE_EXCLUDED", "GEOMETRY", "REFERENCE_ASSUMPTION"}
    assert tot["UC4N"]["MATCHING"] == "NOT_COMPARABLE" and tot["UC4N"]["DIFF_KG"] is None
    if "CHRISTIANNP" in tot:
        assert tot["CHRISTIANNP"]["REFERENCE_KG"] == 0.0 and set(tot["CHRISTIANNP"]["CLASSES"]) == {"SCOPE"}
    ro = tot["ROUGH_90_KG_PER_M3"]
    assert ro["MATCHING"] == "SANITY_ONLY" and s["rough"]["use"] == "SANITY_CHECK_ONLY" and \
        s["rough"]["promoted"] is False
    v = sum(s["s7_scope_concrete_m3"].values())
    assert abs(ro["REFERENCE_KG"] - 90 * v) <= 1e-6


def test_floor_comparison_reconciles(s):
    fl = rows(PF / "S7_POST_FREEZE_FLOOR_COMPARISON.csv")
    s7fl = {r["FLOOR"]: r for r in rows(PKG / "07_S7_FLOOR_SUMMARY.csv")}
    assert len(fl) == 3
    for r in fl:
        assert abs(float(r["S7_KG"]) - float(s7fl[r["FLOOR"]]["PROJECT_BASIS_KG"])) <= 1e-6
    r4 = next(t for t in s["reference_totals"] if t["REFERENCE"] == "OLD_URBAN_R4")
    assert abs(sum(float(r["R4_KG"]) for r in fl) - r4["REFERENCE_KG"]) <= 1e-3
