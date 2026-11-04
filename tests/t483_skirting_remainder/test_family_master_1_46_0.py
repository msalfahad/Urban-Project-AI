"""T-483 r2: rules/coverage/BOQ_FAMILY_MASTER_1.46.0.json = 1.45.0 + the promotion of its two merged pending packages
(T-443 V3.0.47 merge c814c55d, T-350b V3.0.48 merge 5de697ff; R-T485-1) with the families they changed re-derived from
the V3.0.48 census and line diff, + the pending ARCH_TAKEOFF_V3.0.49 package and the B3-06 text. No owner, capability,
item-code or quantity change; every family not touched by the line diff keeps its census and its state."""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
for p in (ROOT, ROOT / "research" / "agents_t483", ROOT / "research" / "agents_t485", ROOT / "research" / "agents_t479"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from engine.source import arch_v3049 as A  # noqa: E402
from tools import family_master_candidate as FMC  # noqa: E402
import build_master_1_46_0 as M  # noqa: E402
import build_master_1_43_0 as B43  # noqa: E402

OLD = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.45.0.json"
NEW = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.46.0.json"
I, H, BL, NI = FMC.STATES
MERGES = {"T-443": "c814c55d", "T-350b": "5de697ff"}


@pytest.fixture(scope="module")
def docs():
    return json.loads(OLD.read_text(encoding="utf-8")), json.loads(NEW.read_text(encoding="utf-8"))


def test_builder_reproduces_the_committed_file(docs):
    assert M.text(M.build(docs[1]["pending_packages"][-1]["task_commit"])) == NEW.read_text(encoding="utf-8")


def test_checks_clean_with_git(docs):
    assert FMC.check(docs[1], root=ROOT, is_ancestor=FMC.git_is_ancestor) == []
    assert B43.census_problems(docs[1]) == []


def test_both_merged_pending_packages_promoted_and_only_v3049_pending(docs):
    old, new = docs
    assert new["version"] == "1.46.0"
    assert [p["task"] for p in old["pending_packages"]] == ["T-443", "T-350b"]
    assert new["candidate_packages"][:-2] == old["candidate_packages"]
    for p, o in zip(new["candidate_packages"][-2:], old["pending_packages"]):
        assert p["task"] == o["task"] and p["task_commit"] == o["task_commit"]
        assert p["merge_commit"].startswith(MERGES[p["task"]]) and p["verdict"].startswith("MERGED")
        assert MERGES[p["task"]] in p["verdict"]
    assert new["candidate"]["method_version"] == "ARCH_TAKEOFF_V3.0.48" and new["candidate"]["as_of_package"] == "T-350b"
    (p,) = new["pending_packages"]
    assert (p["task"], p["method_version"], p["module"]) == ("T-483", A.METHOD, "engine/source/arch_v3049.py")
    assert "merge_commit" not in p and "verdict" not in p


def test_no_merged_package_stays_pending_normal_and_adverse(docs):
    old, new = docs
    merged = {p["task_commit"] for p in new["candidate_packages"]}
    assert B43.stale_pending(new, lambda c: c in merged) == []
    assert B43.stale_pending(old, lambda c: c in merged) == ["T-443", "T-350b"]   # the registry this one supersedes


def test_line_diff_names_only_the_families_the_packages_changed(docs):
    new = docs[1]
    by = {p["task"]: p for p in new["candidate_packages"]}
    assert by["T-443"]["families_changed_by_line_diff"] == ["B3-06"]
    assert by["T-350b"]["families_changed_by_line_diff"] == ["B1-02", "B1-03"]


def test_touched_families_rederived_from_the_census(docs):
    old, new = docs
    ob = {f["code"]: f for f in old["families"]}
    nb = {f["code"]: f for f in new["families"]}
    cc = new["candidate_census"]["families"]
    for code, task in (("B3-06", "T-443"), ("B1-02", "T-350b"), ("B1-03", "T-350b")):
        c = nb[code]["candidate"]
        assert task in c["packages"] and set(ob[code]["candidate"]["packages"]) <= set(c["packages"])
        assert c["state"] == (I if B43.releases(cc[code]) else H)
    assert nb["B3-06"]["candidate"]["state"] == I and nb["B1-02"]["candidate"]["state"] == I
    assert nb["B1-03"]["candidate"]["state"] == H and nb["B1-03"]["candidate"]["released_in_candidate"] == "none"
    assert cc["B1-02"]["units"]["m3"]["released"] == pytest.approx(225.941333)
    assert cc["B3-06"]["units"]["lm"]["released"] == pytest.approx(203.368752)


def test_untouched_families_keep_state_census_and_every_other_field(docs):
    old, new = docs
    ob = {f["code"]: f for f in old["families"]}
    oc, nc = old["candidate_census"]["families"], new["candidate_census"]["families"]
    for f in new["families"]:
        code = f["code"]
        o = ob[code]
        for k in set(f) | set(o):
            if k == "candidate" or (code == "B3-06" and k in ("evidence", "opt_in_readers", "missing", "note")):
                continue
            assert f.get(k) == o.get(k), (code, k)
        if code in ("B3-06", "B1-02", "B1-03"):
            continue
        assert nc[code] == oc[code], code
        assert f["candidate"]["state"] == o["candidate"]["state"] and \
            f["candidate"]["packages"] == o["candidate"]["packages"], code
        assert f["candidate"]["method_version"] == "ARCH_TAKEOFF_V3.0.48" and f["candidate"]["as_of_package"] == "T-350b"


def test_counts_agree_and_nothing_released_changed(docs):
    old, new = docs
    for k in ("capability_counts", "capability_change_counts", "released_configuration", "not_a_boq_line_codes"):
        assert new[k] == old[k]
    assert sum(new["candidate_state_counts"].values()) == len(new["families"])
    assert new["in_v3_0_candidate_counts"] == old["in_v3_0_candidate_counts"]
    assert new["candidate_census"]["previous"]["method_version"] == "ARCH_TAKEOFF_V3.0.46"
    nb = {f["code"]: f for f in new["families"]}
    assert A.METHOD in nb["B3-06"]["opt_in_readers"] and "HELD" in nb["B3-06"]["missing"]


def test_adverse_family_naming_the_pending_package_refused(docs):
    bad = copy.deepcopy(docs[1])
    b = next(f for f in bad["families"] if f["code"] == "B3-06")
    b["candidate"]["packages"] = list(b["candidate"]["packages"]) + ["T-483"]
    assert any("pending package T-483" in p for p in FMC.check(bad, root=ROOT, is_ancestor=None))


def test_adverse_held_family_claimed_integrated_is_caught(docs):
    bad = copy.deepcopy(docs[1])
    b = next(f for f in bad["families"] if f["code"] == "B1-03")
    b["candidate"]["state"] = I
    assert any("B1-03" in p for p in B43.census_problems(bad))


def test_adverse_pending_dropped_is_stale(docs, monkeypatch):
    bad = copy.deepcopy(docs[1])
    bad["pending_packages"] = []
    monkeypatch.setattr(FMC, "newer_registry_modules", lambda doc, root=ROOT: {})
    assert any("arch_v3049" in p for p in FMC.check(bad, root=ROOT, is_ancestor=None))
