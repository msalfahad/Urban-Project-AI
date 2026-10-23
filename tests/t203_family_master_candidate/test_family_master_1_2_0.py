"""T-203: BOQ_FAMILY_MASTER 1.2.0 - a candidate-level state per BOQ family beside the unchanged released states.

The file is read by no engine method (rule_store keeps 1.0.0, the census V2 reads 1.1.0), so no run or quantity changes.
Checks: 1.1.0 byte-identical; 1.2.0 equals its builder; every released-configuration field copied unchanged; every
candidate state names a merged package (merge commit on this head, checker verdict, tests); the counts and the
re-derived in-candidate split; and, on a synthetic registry of a small non-development villa ("villa K", hand values
below), a normal case plus the adverse cases (a state claimed without a verdict, a READY package, a merge commit not on
the head, a held family that releases, a base family naming a package, a future package, wrong counts).
"""

from __future__ import annotations

import copy
import hashlib
import json
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from tools import family_master_candidate as FMC  # noqa: E402

OLD = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.1.0.json"
NEW = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.2.0.json"
OLD_SHA = "df4158800a67b0c1d5352042afa19bdccba8e47fd1f1ff1ec55add41ee5af42e"   # 1.1.0 as merged (T-130 r3, 3f23e232)
CHANGED_KEYS = {"in_v3_0_candidate", "v3_0_planned_tasks"}                 # re-derived for the V3.0.6 candidate
ADDED_KEYS = {"candidate", "in_v3_0_candidate_1_1_0"}


@pytest.fixture(scope="module")
def new():
    return json.loads(NEW.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def old():
    return json.loads(OLD.read_text(encoding="utf-8"))


def test_1_1_0_is_byte_identical():
    assert hashlib.sha256(OLD.read_bytes()).hexdigest() == OLD_SHA
    man = json.loads((ROOT / "rules/RULES_MANIFEST.json").read_text(encoding="utf-8"))["files"]
    assert man["coverage/BOQ_FAMILY_MASTER_1.1.0.json"]["sha256"] == OLD_SHA
    assert man["coverage/BOQ_FAMILY_MASTER_1.2.0.json"]["sha256"] == hashlib.sha256(NEW.read_bytes()).hexdigest()


def test_file_equals_its_builder():
    sys.path.insert(0, str(ROOT / "research/agents_t203"))
    import build_master_1_2_0 as B  # noqa: E402
    assert NEW.read_text(encoding="utf-8") == B.text(B.build())


def test_released_configuration_states_copied_unchanged(new, old):
    assert new["master"] == old["master"] and new["version"] == "1.2.0"
    for k in ("capability_states", "capability_definitions", "released_configuration", "run_evidence",
              "item_code_scan", "item_codes_without_family", "census_gaps", "capability_counts",
              "capability_change_counts"):
        assert new[k] == old[k], k
    assert [f["code"] for f in new["families"]] == [f["code"] for f in old["families"]]
    for a, b in zip(new["families"], old["families"]):
        assert set(a) == set(b) | ADDED_KEYS, a["code"]
        for k in b:
            if k not in CHANGED_KEYS:
                assert a[k] == b[k], (a["code"], k)
        assert a["in_v3_0_candidate_1_1_0"] == b["in_v3_0_candidate"], a["code"]


def test_every_candidate_state_names_a_merged_package_on_this_head(new):
    assert FMC.check(new, is_ancestor=FMC.git_is_ancestor) == []
    assert new["candidate"]["method_version"] == "ARCH_TAKEOFF_V3.0.6"
    assert new["candidate"]["released"] is False
    tasks = [p["task"] for p in new["candidate_packages"]]
    assert tasks == ["T-131", "T-133", "T-142", "T-151", "T-167", "T-179", "T-187"]
    assert "T-193" not in tasks                      # READY, not merged: never a source of a candidate state


def test_counts_and_the_re_derived_split(new, old):
    assert new["candidate_state_counts"] == {"INTEGRATED_IN_CANDIDATE_AND_TESTED": 11, "HELD_IN_CANDIDATE": 5,
                                             "IN_CANDIDATE_BASE_LINES": 34, "NOT_IN_CANDIDATE": 49}
    assert old["in_v3_0_candidate_counts"] == {"yes": 48, "no": 51}
    assert new["in_v3_0_candidate_counts"] == {"yes": 50, "no": 49}
    gained = sorted(f["code"] for f in new["families"]
                    if f["in_v3_0_candidate"] == "yes" and f["in_v3_0_candidate_1_1_0"] == "no")
    lost = [f["code"] for f in new["families"]
            if f["in_v3_0_candidate"] == "no" and f["in_v3_0_candidate_1_1_0"] == "yes"]
    assert gained == ["B11-03", "B7-14"] and lost == []          # stair / pool / tank steel lines of V3.0.5 (T-179)


def test_package_backed_families_and_their_packages(new):
    fam = {f["code"]: f["candidate"] for f in new["families"]}
    want = {"B3-01": ["T-131"], "B4-07": ["T-131"], "B5-01": ["T-142"], "B6-01": ["T-131"], "B7-12": ["T-187"],
            "B8-05": ["T-131", "T-133", "T-142"], "B10-01": ["T-133", "T-142", "T-187"], "B10-04": ["T-131"],
            "B10-06": ["T-133"], "B10-07": ["T-179"], "B11-01": ["T-142", "T-151", "T-167", "T-179"],
            "B7-14": ["T-179"], "B10-03": ["T-167"], "B10-09": ["T-187"], "B10-10": ["T-187"], "B11-03": ["T-179"]}
    assert {c: v["packages"] for c, v in fam.items() if v["packages"]} == want
    held = {c for c, v in fam.items() if v["state"] == "HELD_IN_CANDIDATE"}
    assert held == {"B7-14", "B10-03", "B10-09", "B10-10", "B11-03"}
    # the released states do not move with the candidate: the released default stays V2.9 + route G
    assert sum(f["capability"] == "INTEGRATED_AND_TESTED" for f in new["families"]) == 0


def test_no_benchmark_number_or_client_name_in_the_new_text(new, old):
    text = NEW.read_text(encoding="utf-8")
    assert not re.search(r"(?i:als[ey]?n[ya]?an)|YEARS 2013|7757-[A-Z]", text)
    added = json.dumps({k: new[k] for k in new if k not in old or k == "v3_0_candidate"}, ensure_ascii=False) + \
        json.dumps([f["candidate"] for f in new["families"]], ensure_ascii=False)
    assert "freelanc" not in added.lower()


# --------------------------------------------------------------------------- synthetic registry, "villa K"
# Villa K (not the development villa): 3 families. Package T-901 (V3.0.1) wires a verified strap piece: straps
# 2 x 4.00 m clear x 0.40 x 0.50 = 1.600 m3 by hand; package T-902 (V3.0.2) holds the pool (convention 0.25 where 0.30
# is printed). Family K-03 (site clearance) has no line.
SHA_A, SHA_B = "a" * 40, "b" * 40


def villa_k():
    pk = [
        {"task": "T-901", "method_version": "ARCH_TAKEOFF_V3.0.1", "module": "engine/source/arch_v301.py",
         "merge_commit": SHA_A, "verdict": "MERGED (verifier 2026-10-01 10:00 UTC, Gate B PASS)",
         "integrates": ["T-900"], "tests": ["tests/t133_arch_v301"]},
        {"task": "T-902", "method_version": "ARCH_TAKEOFF_V3.0.2", "module": "engine/source/arch_v302.py",
         "merge_commit": SHA_B, "verdict": "MERGED (Checker 2026-10-02 11:00 UTC, Gate B PASS)",
         "integrates": ["T-899"], "tests": ["tests/t142_arch_v302"]},
    ]
    fam = [
        {"code": "K-01", "in_v3_0_candidate": "yes", "candidate": {
            "state": "INTEGRATED_IN_CANDIDATE_AND_TESTED", "method_version": "ARCH_TAKEOFF_V3.0.2",
            "packages": ["T-901"], "as_of_package": "T-902", "changed": "straps 1.800 -> 1.600 m3 (2 x 4.00 x 0.40 x 0.50)",
            "open": "ground beams base lines", "released_in_candidate": "yes"}},
        {"code": "K-02", "in_v3_0_candidate": "yes", "candidate": {
            "state": "HELD_IN_CANDIDATE", "method_version": "ARCH_TAKEOFF_V3.0.2", "packages": ["T-902"],
            "as_of_package": "T-902", "changed": "pool floor 0.900 m3 HELD (0.25 convention, 0.30 printed)",
            "open": "pool", "released_in_candidate": "none"}},
        {"code": "K-03", "in_v3_0_candidate": "no", "candidate": {
            "state": "NOT_IN_CANDIDATE", "method_version": "ARCH_TAKEOFF_V3.0.2", "packages": [],
            "as_of_package": "T-902", "changed": "", "open": "", "released_in_candidate": "none"}},
    ]
    return {"candidate_states": list(FMC.STATES),
            "candidate_state_definitions": {s: "def" for s in FMC.STATES},
            "candidate": {"method_version": "ARCH_TAKEOFF_V3.0.2", "as_of_package": "T-902"},
            "candidate_packages": pk, "families": fam,
            "candidate_state_counts": {"INTEGRATED_IN_CANDIDATE_AND_TESTED": 1, "HELD_IN_CANDIDATE": 1,
                                       "IN_CANDIDATE_BASE_LINES": 0, "NOT_IN_CANDIDATE": 1},
            "in_v3_0_candidate_counts": {"yes": 2, "no": 1}}


def merged(c):
    return c in (SHA_A, SHA_B)


def test_villa_k_normal_case_passes():
    assert FMC.check(villa_k(), is_ancestor=merged) == []


def _bad(doc):
    return FMC.check(doc, is_ancestor=merged)


def test_villa_k_state_claimed_without_a_verdict_is_refused():
    d = villa_k()
    d["families"][0]["candidate"]["packages"] = ["T-903"]          # no such merged package
    assert any("claimed without a verdict" in b for b in _bad(d))
    d = villa_k()
    d["candidate_packages"][0]["verdict"] = "READY (worker 3, 2026-10-01 09:00 UTC)"
    assert any("no checker verdict" in b for b in _bad(d))
    d = villa_k()
    d["families"][0]["candidate"]["packages"] = []
    assert any("names no package" in b for b in _bad(d))


def test_villa_k_package_not_on_the_head_or_without_a_merge_is_refused():
    d = villa_k()
    d["candidate_packages"][1]["merge_commit"] = "c" * 40
    assert any("not on the checked head" in b for b in _bad(d))
    d = villa_k()
    d["candidate_packages"][1]["merge_commit"] = "bbbbbbb"
    assert any("not a full 40-hex sha" in b for b in _bad(d))
    d = villa_k()
    d["candidate_packages"][0]["tests"] = ["tests/no_such_folder"]
    assert any("does not exist" in b for b in _bad(d))


def test_villa_k_held_family_that_releases_and_base_family_with_a_package_are_refused():
    d = villa_k()
    d["families"][1]["candidate"]["released_in_candidate"] = "yes"
    assert any("released_in_candidate 'none'" in b for b in _bad(d))
    d = villa_k()
    d["families"][2]["candidate"]["packages"] = ["T-901"]
    assert any("must name no package" in b for b in _bad(d))
    d = villa_k()
    d["families"][2]["in_v3_0_candidate"] = "yes"
    assert any("disagrees with state" in b for b in _bad(d))


def test_villa_k_versions_and_counts():
    d = villa_k()
    d["candidate"]["method_version"] = "ARCH_TAKEOFF_V3.0.1"         # not the newest merged package
    assert any("not the newest" in b for b in _bad(d))
    d = villa_k()
    for f in d["families"]:
        f["candidate"]["method_version"] = "ARCH_TAKEOFF_V3.0.1"
    d["candidate"]["method_version"] = "ARCH_TAKEOFF_V3.0.1"
    d["candidate_packages"][1]["method_version"] = "ARCH_TAKEOFF_V3.0.1"
    d["candidate_packages"].append(copy.deepcopy(d["candidate_packages"][1]) | {"task": "T-904",
                                   "method_version": "ARCH_TAKEOFF_V3.0.3"})
    assert any("newest" in b for b in _bad(d))
    d = villa_k()
    d["candidate_state_counts"]["NOT_IN_CANDIDATE"] = 0
    assert any("candidate_state_counts" in b for b in _bad(d))
    d = villa_k()
    d["families"][0]["candidate"]["state"] = "INTEGRATED_AND_TESTED"   # the released vocabulary is not a candidate state
    assert any("not in the vocabulary" in b for b in _bad(d))


def test_villa_k_integrated_needs_what_changed_and_what_is_open():
    d = villa_k()
    d["families"][0]["candidate"]["open"] = ""
    assert any("'open'" in b for b in _bad(d))


def test_cli_check_on_the_merged_file(capsys):
    assert FMC.main(["x", "check", str(NEW)]) == 0
    assert "0 problem(s)" in capsys.readouterr().out
