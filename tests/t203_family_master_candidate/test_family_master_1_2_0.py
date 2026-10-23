"""T-203: BOQ_FAMILY_MASTER 1.2.0 - a candidate-level state per BOQ family beside the unchanged released states.

The file is read by no engine method (rule_store keeps 1.0.0, the census V2 reads 1.1.0), so no run or quantity changes.
Checks: 1.1.0 byte-identical; 1.2.0 equals its builder; every released-configuration field copied unchanged; every
candidate state names a merged package (merge commit on this head, checker verdict, tests); the counts and the
re-derived in-candidate split; and, on a synthetic registry of a small non-development villa ("villa K", hand values
below), a normal case plus the adverse cases (a state claimed without a verdict, a READY package, a merge commit not on
the head, a held family that releases, a base family naming a package, a future package, wrong counts).
r2 (Verifier 2026-10-23 13:03 rejection: the registry stated V3.0.6 while V3.0.7 had merged): the candidate is V3.0.7
(T-193, e866328a); a candidate module on the head newer than the registry's candidate is refused, and so is a family
left HELD_IN_CANDIDATE after a package released a quantity of it.
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
CHANGED_KEYS = {"in_v3_0_candidate", "v3_0_planned_tasks"}                 # re-derived for the V3.0.7 candidate
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
    assert new["candidate"]["method_version"] == "ARCH_TAKEOFF_V3.0.7"
    assert new["candidate"]["as_of_package"] == "T-193"
    assert new["candidate"]["released"] is False
    tasks = [p["task"] for p in new["candidate_packages"]]
    assert tasks == ["T-131", "T-133", "T-142", "T-151", "T-167", "T-179", "T-187", "T-193"]
    t193 = new["candidate_packages"][-1]
    assert t193["merge_commit"] == "e866328a66149abe881c0d1329f904170b631402"
    assert t193["integrates"] == ["T-183", "T-185"] and t193["releases"] == ["B10-09", "B10-10"]
    assert "T-199" not in tasks                      # TODO, not merged: never a source of a candidate state


def test_registry_candidate_is_the_newest_candidate_module_on_this_head(new):
    """r2 root cause: as_of must follow the newest merged candidate module (no newer arch_v30N.py on the head that the
    registry of record does not account for). T-231 (r3): 1.2.0 accounts for V3.0 .. V3.0.7; every newer candidate
    module on the head must be accounted for by a NEWER registry version (merged or pending), never left silent."""
    mods = FMC.head_candidate_modules(ROOT)
    assert FMC.version_key(new["candidate"]["method_version"]) == 7
    assert mods[7] == "engine/source/arch_v307.py"
    assert {p["module"] for p in new["candidate_packages"]} == {m for n, m in mods.items() if n <= 7}
    newer = FMC.newer_registry_modules(new, ROOT)
    assert all(m in newer for n, m in mods.items() if n > 7), (mods, newer)


def test_counts_and_the_re_derived_split(new, old):
    assert new["candidate_state_counts"] == {"INTEGRATED_IN_CANDIDATE_AND_TESTED": 13, "HELD_IN_CANDIDATE": 3,
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
    want = {"B3-01": ["T-131"], "B4-07": ["T-131"], "B5-01": ["T-142"], "B6-01": ["T-131"],
            "B7-12": ["T-187", "T-193"], "B8-05": ["T-131", "T-133", "T-142"],
            "B10-01": ["T-133", "T-142", "T-187", "T-193"], "B10-04": ["T-131"],
            "B10-06": ["T-133"], "B10-07": ["T-179"], "B11-01": ["T-142", "T-151", "T-167", "T-179"],
            "B7-14": ["T-179"], "B10-03": ["T-167"], "B10-09": ["T-187", "T-193"], "B10-10": ["T-187", "T-193"],
            "B11-03": ["T-179"]}
    assert {c: v["packages"] for c, v in fam.items() if v["packages"]} == want
    held = {c for c, v in fam.items() if v["state"] == "HELD_IN_CANDIDATE"}
    assert held == {"B7-14", "B10-03", "B11-03"}
    # the released states do not move with the candidate: the released default stays V2.9 + route G
    assert sum(f["capability"] == "INTEGRATED_AND_TESTED" for f in new["families"]) == 0


def test_v3_0_7_families_re_derived_by_the_definitions(new):
    """T-193 report s.3: pool 0 -> 7.202297 m3 (blocked 2 -> 1, steps), domes 0 -> 5.081362 (blocked 3 -> 1, DOME-3),
    the 1F 'winder' 4.450745 retired as DOME-B (stair blocked 5 -> 4). Hand: pool base (3.50 x 1.75 + pi 1.75^2 / 2)
    x 0.40 = 4.374226, walls (10.935564 - (3.10 x 1.55 + pi 1.55^2 / 2)) x 1.20 = 2.828071."""
    import math
    base = (3.50 * 1.75 + math.pi * 1.75 ** 2 / 2) * 0.40
    walls = (3.50 * 1.75 + math.pi * 1.75 ** 2 / 2 - (3.10 * 1.55 + math.pi * 1.55 ** 2 / 2)) * 1.20
    assert round(base, 6) == 4.374226 and round(walls, 6) == 2.828071
    fam = {f["code"]: f["candidate"] for f in new["families"]}
    pool, dome, stair = fam["B10-10"], fam["B10-09"], fam["B7-12"]
    for c in (pool, dome):
        assert c["state"] == "INTEGRATED_IN_CANDIDATE_AND_TESTED" and c["released_in_candidate"] == "yes"
        assert "NOT RELEASED" in c["open"]
    assert "0 -> 7.202297" in pool["changed"] and "blocked 2 -> 1" in pool["changed"]
    assert "4.374226" in pool["changed"] and "2.828071" in pool["changed"]
    assert "steps HELD" in pool["open"] and "T-193" not in pool["open"]
    assert "0 -> 5.081362" in dome["changed"] and "blocked 3 -> 1" in dome["changed"]
    assert "DOME-3" in dome["open"] and "T-193" not in dome["open"]
    assert "RETIRED" in stair["changed"] and "4.450745" in stair["changed"] and "blocked 5 -> 4" in stair["changed"]
    for f in new["families"]:                       # no family still waits for the merged package
        assert "T-193" not in f["v3_0_planned_tasks"], f["code"]
        assert "(READY)" not in f["candidate"]["open"], f["code"]


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
    assert FMC.check(villa_k(), is_ancestor=merged, scan_head=False) == []


def _bad(doc):
    # villa K is checked outside this repository's head (its candidate V3.0.2 is older than the modules here); the
    # head scan has its own tests below, on a tree made for villa K
    return FMC.check(doc, is_ancestor=merged, scan_head=False)


def _villa_k_tree(tmp_path, modules):
    for m in modules:
        (tmp_path / "engine/source").mkdir(parents=True, exist_ok=True)
        (tmp_path / "engine/source" / m).write_text("# stub\n", encoding="utf-8")
    for d in ("tests/t133_arch_v301", "tests/t142_arch_v302"):
        (tmp_path / d).mkdir(parents=True, exist_ok=True)
    return tmp_path


def test_villa_k_head_scan_normal_and_stale_as_of(tmp_path):
    root = _villa_k_tree(tmp_path / "ok", ["arch_v301.py", "arch_v302.py", "arch_vX.py"])
    assert FMC.check(villa_k(), root=root, is_ancestor=merged) == []
    # adverse (the r1 defect): a package V3.0.3 merged on the head, the registry still says V3.0.2
    root = _villa_k_tree(tmp_path / "stale", ["arch_v301.py", "arch_v302.py", "arch_v303.py"])
    bad = FMC.check(villa_k(), root=root, is_ancestor=merged)
    assert any("arch_v303.py" in b and "as_of is stale" in b for b in bad)
    # adverse: as_of names an older package than the candidate version
    d = villa_k()
    d["candidate"]["as_of_package"] = "T-901"
    assert any("is not the package of" in b for b in _bad(d))


def test_villa_k_held_after_a_release_is_refused():
    # normal: T-902 holds K-02, nothing releases it -> HELD stays valid
    d = villa_k()
    d["candidate_packages"][1]["holds"] = ["K-02"]
    assert _bad(d) == []
    # adverse (the r1 defect): a later package T-905 (V3.0.3) releases K-02 (pool 0.900 -> 1.080 m3 =
    # 3.00 x 1.20 x 0.30 printed) but the family stays HELD_IN_CANDIDATE
    d["candidate_packages"].append(copy.deepcopy(d["candidate_packages"][1]) | {
        "task": "T-905", "method_version": "ARCH_TAKEOFF_V3.0.3", "holds": [], "releases": ["K-02"]})
    for f in d["families"]:
        f["candidate"]["method_version"] = "ARCH_TAKEOFF_V3.0.3"
    d["families"][1]["candidate"]["packages"] = ["T-902", "T-905"]
    d["candidate"] = {"method_version": "ARCH_TAKEOFF_V3.0.3", "as_of_package": "T-905"}
    for f in d["families"]:
        f["candidate"]["as_of_package"] = "T-905"
    assert any("K-02: HELD_IN_CANDIDATE, but package T-905 released" in b for b in _bad(d))
    # its correction passes: integrated, released, open says what stays held
    d["families"][1]["candidate"].update(state="INTEGRATED_IN_CANDIDATE_AND_TESTED", released_in_candidate="yes")
    d["candidate_state_counts"] = {"INTEGRATED_IN_CANDIDATE_AND_TESTED": 2, "HELD_IN_CANDIDATE": 0,
                                   "IN_CANDIDATE_BASE_LINES": 0, "NOT_IN_CANDIDATE": 1}
    assert _bad(d) == []
    # adverse: a package names a family whose block does not name the package, or an unknown family
    e = villa_k()
    e["candidate_packages"][0]["releases"] = ["K-02"]
    assert any("does not name that package" in b for b in _bad(e))
    e = villa_k()
    e["candidate_packages"][0]["holds"] = ["K-99"]
    assert any("not a family of this registry" in b for b in _bad(e))


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
