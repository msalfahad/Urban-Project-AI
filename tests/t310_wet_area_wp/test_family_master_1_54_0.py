"""T-310 r7: rules/coverage/BOQ_FAMILY_MASTER_1.54.0.json = 1.53.0 + the promotion of its merged pending package
(T-508 V3.0.56, merge 40ab9061; R-T485-1) with the families it changed (B3-06 skirting, B7-07 / B7-08 stair skirting
forms) re-derived from the V3.0.56 census and the line diff V3.0.55 -> V3.0.56, + the pending ARCH_TAKEOFF_V3.0.57
package (T-310) and the waterproofing family text (B8-01 / B8-02 / B8-03 / B8-09), B8-09 owning the two pool layer
codes. No owner, capability or quantity change; every family the line diff does not name keeps its census and its
state."""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
for p in (ROOT, ROOT / "research" / "agents_t310", ROOT / "research" / "agents_t485", ROOT / "research" / "agents_t479"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from engine.source import arch_v3057 as A  # noqa: E402
from tools import family_master_candidate as FMC  # noqa: E402
import build_master_1_54_0 as M  # noqa: E402
import build_master_1_43_0 as B43  # noqa: E402

OLD = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.53.0.json"
NEW = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.54.0.json"
I, H, BL, NI = FMC.STATES
FAMS = {"B8-01", "B8-02", "B8-03", "B8-09"}
TEXT = ("evidence", "opt_in_readers", "missing", "note")


@pytest.fixture(scope="module")
def docs():
    return json.loads(OLD.read_text(encoding="utf-8")), json.loads(NEW.read_text(encoding="utf-8"))


def test_builder_reproduces_the_committed_file(docs):
    assert M.text(M.build(docs[1]["pending_packages"][-1]["task_commit"])) == NEW.read_text(encoding="utf-8")


def test_checks_clean_with_git(docs):
    assert FMC.check(docs[1], root=ROOT, is_ancestor=FMC.git_is_ancestor) == []
    assert B43.census_problems(docs[1]) == []


def test_merged_t508_promoted_and_only_v3057_pending(docs):
    old, new = docs
    assert new["version"] == "1.54.0"
    assert [p["task"] for p in old["pending_packages"]] == ["T-508"]
    assert new["candidate_packages"][:-1] == old["candidate_packages"]
    p, o = new["candidate_packages"][-1], old["pending_packages"][0]
    assert p["task"] == "T-508" and p["task_commit"] == o["task_commit"]
    assert p["merge_commit"].startswith("40ab9061") and p["verdict"].startswith("MERGED") and "40ab9061" in p["verdict"]
    assert new["candidate"]["method_version"] == "ARCH_TAKEOFF_V3.0.56" and new["candidate"]["as_of_package"] == "T-508"
    (q,) = new["pending_packages"]
    assert (q["task"], q["method_version"], q["module"]) == ("T-310", A.METHOD, "engine/source/arch_v3057.py")
    assert "merge_commit" not in q and "verdict" not in q


def test_no_merged_package_stays_pending_normal_and_adverse(docs):
    old, new = docs
    merged = {p.get("task_commit") for p in new["candidate_packages"]} - {None}
    assert B43.stale_pending(new, lambda c: c in merged) == []
    assert B43.stale_pending(old, lambda c: c in merged) == ["T-508"]      # the registry this one supersedes


STAIR = ("B3-06", "B7-07", "B7-08")


def test_line_diff_names_only_the_skirting_families(docs):
    p = docs[1]["candidate_packages"][-1]
    assert p["families_changed_by_line_diff"] == list(STAIR)
    assert p["lines_touched"] == 52                     # T-508: FIN.SKIRTING 2 changed + 6 added, 22 + 22 form lines


def test_skirting_rederived_from_the_v3056_census(docs):
    old, new = docs
    nb = {f["code"]: f for f in new["families"]}
    cc, oc = new["candidate_census"]["families"], old["candidate_census"]["families"]
    c = nb["B3-06"]["candidate"]
    assert "T-508" in c["packages"] and c["state"] == I and c["method_version"] == "ARCH_TAKEOFF_V3.0.56"
    rel = cc["B3-06"]["units"]["lm"]["released"] - oc["B3-06"]["units"]["lm"]["released"]
    assert rel == pytest.approx(-2.950)                 # T-508: 9.050 lm shaft stretches retired, 6.100 lm landings
    for code in ("B7-07", "B7-08"):                     # every form line blank (ORR-007 form not chosen): HELD
        assert (oc[code]["lines"], cc[code]["lines"]) == (0, 22)
        assert cc[code]["units"]["lm"]["released"] == 0.0 and cc[code]["units"]["lm"]["held_lines"] == 22
        assert nb[code]["candidate"]["state"] == H and nb[code]["in_v3_0_candidate"] == "yes"
    assert new["candidate_census"]["lines"] == 4989 and new["candidate_census"]["lines_sha256"].startswith("4e25c54f")


def test_untouched_families_keep_state_census_and_every_other_field(docs):
    old, new = docs
    ob = {f["code"]: f for f in old["families"]}
    oc, nc = old["candidate_census"]["families"], new["candidate_census"]["families"]
    for f in new["families"]:
        code = f["code"]
        o = ob[code]
        for k in set(f) | set(o):
            if k == "candidate" or (code in FAMS and k in TEXT) or (code == "B8-09" and k == "item_codes") or \
                    (code in STAIR and k == "in_v3_0_candidate"):     # B7-07 / B7-08 enter the candidate (asserted above)
                continue
            assert f.get(k) == o.get(k), (code, k)
        if code in STAIR:
            continue
        assert nc[code] == oc[code], code
        assert f["candidate"]["state"] == o["candidate"]["state"] and \
            f["candidate"]["packages"] == o["candidate"]["packages"], code
        assert f["candidate"]["method_version"] == "ARCH_TAKEOFF_V3.0.56" and f["candidate"]["as_of_package"] == "T-508"


def test_waterproofing_text_and_pool_codes(docs):
    old, new = docs
    ob = {f["code"]: f for f in old["families"]}
    nb = {f["code"]: f for f in new["families"]}
    for c in FAMS:
        assert A.METHOD in nb[c]["opt_in_readers"]
        assert nb[c]["evidence"][:-1] == ob[c]["evidence"]
    assert (ob["B8-09"]["item_codes"], nb["B8-09"]["item_codes"]) == ([], ["WP.POOL.MEMBRANE",
                                                                         "WP.POOL.PROTECTION_SCREED"])
    for code in (A.POOL_MEMBRANE, A.POOL_SCREED):
        assert [f["code"] for f in new["families"] if code in f["item_codes"]] == ["B8-09"]


def test_counts_agree_and_nothing_released_changed(docs):
    old, new = docs
    for k in ("capability_counts", "capability_change_counts", "released_configuration", "not_a_boq_line_codes"):
        assert new[k] == old[k]
    assert sum(new["candidate_state_counts"].values()) == len(new["families"])
    o, n = old["in_v3_0_candidate_counts"], new["in_v3_0_candidate_counts"]
    assert (n["yes"] - o["yes"], n["no"] - o["no"], n["N/A"] - o["N/A"]) == (2, -2, 0)   # B7-07 / B7-08 enter
    assert new["candidate_census"]["previous"]["method_version"] == "ARCH_TAKEOFF_V3.0.55"


def test_adverse_family_naming_the_pending_package_refused(docs):
    bad = copy.deepcopy(docs[1])
    b = next(f for f in bad["families"] if f["code"] == "B8-03")
    b["candidate"]["packages"] = list(b["candidate"]["packages"]) + ["T-310"]
    assert any("pending package T-310" in p for p in FMC.check(bad, root=ROOT, is_ancestor=None))


def test_adverse_pending_package_with_a_verdict_refused(docs):
    bad = copy.deepcopy(docs[1])
    bad["pending_packages"][-1]["merge_commit"] = "a" * 40
    assert any("pending package T-310" in p for p in FMC.check(bad, root=ROOT, is_ancestor=None))


def test_adverse_pending_dropped_is_stale(docs, monkeypatch):
    bad = copy.deepcopy(docs[1])
    bad["pending_packages"] = []
    monkeypatch.setattr(FMC, "newer_registry_modules", lambda doc, root=ROOT: {})
    assert any("arch_v3057" in p for p in FMC.check(bad, root=ROOT, is_ancestor=None))
