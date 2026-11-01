"""T-400: BOQ_FAMILY_MASTER 1.30.0 = 1.29.0 + the pending ARCH_TAKEOFF_V3.0.35 package (rule r3 of
tools/family_master_candidate.py) + B13-04 owns the EXT.FENCE.* codes + B10-11 owns STR.CONC.BOUNDARY_PAD.

Normal: 1.30.0 equals its builder, copies every 1.29.0 field it does not name (every family but B13-04 / B10-11
identical), checks clean on the head; B13-04 NOT_IMPLEMENTED -> IMPLEMENTED_NOT_INTEGRATED with candidate state
NOT_IN_CANDIDATE (pending raises none); every code the V3.0.35 module writes is owned by exactly one family; every
UPPER.UPPER literal of arch_v3035.py is owned or listed apart. Adverse: the pending entry dropped, a pending entry
carrying a merge commit, B13-04 naming the pending package, and an EXT.FENCE code no family owns are each refused."""
from __future__ import annotations

import copy
import importlib.util
import json
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engine.source import arch_v3035 as A  # noqa: E402
from tools import family_master_candidate as FMC  # noqa: E402

OLD = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.29.0.json"
NEW = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.30.0.json"
_spec = importlib.util.spec_from_file_location("b130", ROOT / "research/agents_t400/build_master_1_30_0.py")
B = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(B)
NAMED = {"version", "supersedes", "source", "pending_packages", "item_code_scan", "families", "capability_counts",
         "capability_change_counts", "in_v3_0_candidate_counts", "candidate_state_counts"}
ANY_CODE = re.compile(r"\"([A-Z][A-Z0-9]*\.[A-Z0-9_.]*[A-Z0-9_])\"")


@pytest.fixture(scope="module")
def docs():
    return json.loads(OLD.read_text(encoding="utf-8")), json.loads(NEW.read_text(encoding="utf-8"))


def _owners(doc):
    out = {}
    for f in doc["families"]:
        for c in f.get("item_codes") or ():
            out.setdefault(c, []).append(f["code"])
    return out


def test_equals_builder(docs):
    old, new = docs
    assert NEW.read_text(encoding="utf-8") == B.text(B.build(new["pending_packages"][-1]["task_commit"]))


def test_copies_every_other_field(docs):
    old, new = docs
    assert set(old) == set(new)
    for k in set(old) - NAMED:
        assert old[k] == new[k], k
    assert new["pending_packages"][:-1] == old["pending_packages"]
    p = new["pending_packages"][-1]
    assert (p["task"], p["method_version"], p["module"]) == ("T-400", A.METHOD, "engine/source/arch_v3035.py")
    assert p["integrates"] == ["T-396", "T-403", "T-404", "T-361"] and p["changes_families_by_item_code"] == []
    assert len(old["families"]) == len(new["families"])
    for a, b in zip(old["families"], new["families"]):
        if a["code"] not in ("B13-04", "B10-11"):
            assert a == b, a["code"]


def test_b13_04_moved_and_b10_11_owns_the_pad(docs):
    old, new = docs
    f = {x["code"]: x for x in new["families"]}
    b = f["B13-04"]
    assert b["capability"] == "IMPLEMENTED_NOT_INTEGRATED" and b["capability_change"] == "RAISED"
    assert b["candidate"]["state"] == "NOT_IN_CANDIDATE" and "name_terms" not in b
    assert b["item_codes"] == sorted(c for c in A.NEW_ITEMS if c.startswith("EXT.FENCE."))
    p = f["B10-11"]
    o = {x["code"]: x for x in old["families"]}["B10-11"]
    assert p["item_codes"] == sorted(o["item_codes"] + [A.PAD]) and p["capability"] == o["capability"]
    assert p["candidate"] == o["candidate"]
    assert new["capability_counts"]["IMPLEMENTED_NOT_INTEGRATED"] == \
        old["capability_counts"]["IMPLEMENTED_NOT_INTEGRATED"] + 1
    assert new["capability_counts"]["NOT_IMPLEMENTED"] == old["capability_counts"]["NOT_IMPLEMENTED"] - 1


def test_every_written_code_owned_once(docs):
    own = _owners(docs[1])
    for c in list(A.NEW_ITEMS) + [A.UPPER_GB, "STR.CONC.BOUNDARY_WALL"]:
        assert len(own.get(c, [])) == 1, c
    assert own[A.UPPER_GB] == ["B10-04"] and own[A.PAD] == ["B10-11"]


def test_every_literal_of_the_module_owned_or_apart(docs):
    own, apart = _owners(docs[1]), docs[1]["item_codes_without_family"]
    lits = set(ANY_CODE.findall((ROOT / "engine/source/arch_v3035.py").read_text(encoding="utf-8")))
    assert {c for c in lits if c not in own and c not in apart} == set()


def test_evidence_lines_point_at_the_symbols(docs):
    f = next(f for f in docs[1]["families"] if f["code"] == "B13-04")
    src = (ROOT / "engine/source/arch_v3035.py").read_text(encoding="utf-8").splitlines()
    for ref, name in re.findall(r"engine/source/arch_v3035\.py:(\d+) (\w+)", f["evidence"][0]):
        line = src[int(ref) - 1]
        assert name.rstrip("()") in line, (ref, name, line)


def test_checks_clean_on_head(docs):
    assert FMC.check(docs[1], root=ROOT, is_ancestor=None) == []


def test_pending_dropped_is_stale(docs):
    bad = copy.deepcopy(docs[1])
    bad["pending_packages"] = bad["pending_packages"][:-1]
    probs = FMC.check(bad, root=ROOT, is_ancestor=None)
    # T-246 (1.31.0): a NEWER registry version on the head that declares arch_v3035 accounts for it (rule r3); then
    # that registry must carry the dropped entry unchanged (the pattern T-400 took in the 1.29.0 test).
    acc = FMC.newer_registry_modules(docs[1], ROOT).get("engine/source/arch_v3035.py")
    if acc is None:
        assert any("arch_v3035" in p for p in probs)
    else:
        assert FMC._semver(acc) > FMC._semver("1.30.0")
        gov = json.loads((ROOT / f"rules/coverage/BOQ_FAMILY_MASTER_{acc}.json").read_text(encoding="utf-8"))
        assert docs[1]["pending_packages"][-1] in gov["pending_packages"]


def test_pending_with_merge_commit_refused(docs):
    bad = copy.deepcopy(docs[1])
    bad["pending_packages"][-1]["merge_commit"] = "0" * 40
    assert any("merge commit" in p for p in FMC.check(bad, root=ROOT, is_ancestor=None))


def test_family_naming_pending_refused(docs):
    bad = copy.deepcopy(docs[1])
    f = next(f for f in bad["families"] if f["code"] == "B13-04")
    f["candidate"]["packages"] = list(f["candidate"].get("packages") or []) + ["T-400"]
    assert any("pending package T-400" in p for p in FMC.check(bad, root=ROOT, is_ancestor=None))


def test_adverse_an_unowned_fence_code_is_seen(docs):
    bad = copy.deepcopy(docs[1])
    f = next(f for f in bad["families"] if f["code"] == "B13-04")
    f["item_codes"] = [c for c in f["item_codes"] if c != A.WALL]
    own = _owners(bad)
    assert A.WALL not in own and A.WALL not in bad["item_codes_without_family"]


# ------------------------------------------------------------------ the ownership census at full strength on 1.30.0
_s127 = importlib.util.spec_from_file_location("t284_master", ROOT / "tests/t284_ceiling_integration/"
                                               "test_family_master_1_27_0.py")
_sys_path = list(sys.path)
sys.path.insert(0, str(ROOT / "research" / "agents_t284"))
M127 = importlib.util.module_from_spec(_s127)
_s127.loader.exec_module(M127)
sys.path[:] = _sys_path


def test_full_census_every_written_code_and_literal_owned(docs):
    new = docs[1]
    T130 = M127.T130
    own, apart = T130._owners(new), new["item_codes_without_family"]
    assert not set(own) & set(apart)
    written = M127._written_1_26()                      # every module on the head, nothing set aside
    assert set(T130._written_codes()) <= set(written)
    # T-420 (1.32.0): a code written by a module a NEWER registry version on the head accounts for (rule r3) is owned
    # there, not here (the pattern T-246 took for the pending entry); every other written code must be owned here.
    acc = FMC.newer_registry_modules(new, ROOT)

    def _later(code, mod):
        v = acc.get(mod)
        if v is None:
            return False
        gov = json.loads((ROOT / f"rules/coverage/BOQ_FAMILY_MASTER_{v}.json").read_text(encoding="utf-8"))
        return code in T130._owners(gov)
    assert {c: m for c, m in T130._unowned_written(new, written).items() if not _later(c, m)} == {}
    assert T130._not_implemented_hits(new, written) == []
    lits = M127._v30x_literals()
    assert {c: p for c, p in lits.items() if c not in own and c not in apart and not _later(c, p)} == {}
    assert {c.split(".")[0] for c in lits} <= set(M127.SCAN_1_26)
    assert {c: own[c] for c in A.NEW_ITEMS} == {c: ("B10-11" if c == A.PAD else "B13-04") for c in A.NEW_ITEMS}
