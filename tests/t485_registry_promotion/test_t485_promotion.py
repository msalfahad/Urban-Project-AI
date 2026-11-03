"""T-485: rules/coverage/BOQ_FAMILY_MASTER_1.42.0.json = 1.41.0 + the promotion of the 38 merged pending packages
(merge commit + Checker verdict each) + every family's candidate block re-derived at ARCH_TAKEOFF_V3.0.45 from
candidate_census and the line diff of a reproduced chain run. No quantity, capability, owner or line change.

Synthetic cases by hand (villa K485, never the development villa) for the line-diff attribution, the state rules and
the stale-pending guard; then the committed registry, line diff and promotion source."""
from __future__ import annotations

import copy
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
for p in (ROOT, ROOT / "research" / "agents_t469", ROOT / "research" / "agents_t479", ROOT / "research" / "agents_t485"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from tools import family_master_candidate as FMC  # noqa: E402
import t479_registry_census as C  # noqa: E402
import t485_package_families as PF  # noqa: E402
import build_master_1_42_0 as B  # noqa: E402

OLD = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.41.0.json"
NEW = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.42.0.json"
I, H, BL, NI = FMC.STATES


@pytest.fixture(scope="module")
def docs():
    return json.loads(OLD.read_text(encoding="utf-8")), json.loads(NEW.read_text(encoding="utf-8"))


def _ln(i, code, net, **kw):
    return dict({"line_id": i, "item_code": code, "unit": "m2", "measured_net": net}, **kw)


# ---------- synthetic villa K485: line-diff attribution ----------

def test_diff_counts_added_removed_changed_by_item_code():
    prev = [_ln("L-1", "FIN.A", 10.0), _ln("L-2", "FIN.A", 5.0), _ln("L-3", "STR.B", 1.0)]
    new = [_ln("L-1", "FIN.A", 10.0), _ln("L-2", "FIN.A", 4.5), _ln("L-4", "STR.B", 0.4)]
    assert PF.diff_versions(prev, new) == {"FIN.A": {"added": 0, "removed": 0, "changed": 1, "record": 0},
                                           "STR.B": {"added": 1, "removed": 1, "changed": 0, "record": 0}}


def test_text_only_change_is_a_record_change_and_raises_no_family():
    prev = [_ln("L-1", "FIN.A", 10.0, notes="a")]
    master = {"families": [{"code": "F1", "item_codes": ["FIN.A"]}]}
    assert PF.diff_versions(prev, copy.deepcopy(prev)) == {}
    d = PF.diff_versions(prev, [_ln("L-1", "FIN.A", 10.0, notes="b")])
    assert d == {"FIN.A": {"added": 0, "removed": 0, "changed": 0, "record": 1}}
    assert PF.families_changed(d, master)[0] == {} and set(PF.families_changed(d, master, record=True)[0]) == {"F1"}


def test_adverse_state_field_change_is_a_quantity_change():
    """a line going HELD (evidence state) or re-bounded is a change even when its net stays"""
    prev = [_ln("L-1", "FIN.A", 10.0, evidence_state="MEASURED")]
    d = PF.diff_versions(prev, [_ln("L-1", "FIN.A", 10.0, evidence_state="BLOCKED_RFI")])
    assert d["FIN.A"]["changed"] == 1 and d["FIN.A"]["record"] == 0


def test_adverse_duplicate_line_id_is_refused():
    with pytest.raises(ValueError):
        PF.diff_versions([_ln("L-1", "FIN.A", 1.0), _ln("L-1", "FIN.A", 2.0)], [])


def test_doubly_owned_code_listed_under_both_and_unowned_apart():
    master = {"families": [{"code": "F1", "item_codes": ["X.A"]}, {"code": "F2", "item_codes": ["X.A", "X.B"]}],
              "not_a_boq_line_codes": {"X.INFO": {}}}
    d = {"X.A": {"added": 1, "removed": 0, "changed": 0, "record": 0},
         "X.INFO": {"added": 0, "removed": 0, "changed": 1, "record": 0},
         "X.Z": {"added": 1, "removed": 0, "changed": 0, "record": 0}}
    fams, apart = PF.families_changed(d, master)
    assert set(fams) == {"F1", "F2"} and fams["F1"]["X.A"]["added"] == 1
    assert sorted((a["item_code"], a["kind"]) for a in apart) == [("X.INFO", "NOT_A_BOQ_LINE"), ("X.Z", "NO_FAMILY")]


# ---------- synthetic: state rules ----------

def _unit(released_lines, held_lines=0):
    return {"released_lines": released_lines, "released": 3.0 * released_lines, "held_lines": held_lines,
            "held_unknown_lines": held_lines, "held_low": 0.0, "held_high": 0.0}


def _fam(code, codes, state=BL, packages=()):
    return {"code": code, "item_codes": codes, "in_v3_0_candidate": "yes",
            "candidate": {"state": state, "packages": list(packages), "changed": "", "open": "", "as_of_package": "T-193",
                          "method_version": "ARCH_TAKEOFF_V3.0.7", "released_in_candidate": "base lines"}}


BYF = {"_v": {"T-901": "V3.0.9"}, "_codes": {("T-901", "K1"): {"X.A": {"added": 1, "removed": 0, "changed": 0}},
                                             ("T-901", "K2"): {"X.B": {"added": 0, "removed": 0, "changed": 2}}},
       "K1": ["T-901"], "K2": ["T-901"], "_record": {"K3": ["T-901"]}}
PV = {"T-901": 9, "T-131": 0}


def test_changed_family_releasing_is_integrated_and_holding_only_is_held():
    c1, y1 = B.family_block(_fam("K1", ["X.A"]), {"in_candidate": "yes", "units": {"m2": _unit(2)}}, BYF, PV)
    c2, y2 = B.family_block(_fam("K2", ["X.B"]), {"in_candidate": "yes", "units": {"m2": _unit(0, 3)}}, BYF, PV)
    assert (c1["state"], c1["packages"], y1) == (I, ["T-901"], "yes")
    assert (c2["state"], c2["released_in_candidate"], y2) == (H, "none", "yes")      # held never released, never 0
    assert "3 lines (3 UNKNOWN)" in c2["open"]


def test_untouched_family_is_base_lines_and_keeps_old_packages_when_touched():
    c, _ = B.family_block(_fam("K3", ["X.C"]), {"in_candidate": "yes", "units": {"m2": _unit(1)}}, BYF, PV)
    assert c["state"] == BL and c["packages"] == [] and c["record_only_packages"] == ["T-901"]
    c, _ = B.family_block(_fam("K1", ["X.A"], I, ["T-131"]), {"in_candidate": "yes", "units": {"m2": _unit(1)}}, BYF, PV)
    assert c["packages"] == ["T-131", "T-901"]


def test_no_line_family_leaves_the_candidate_and_names_its_filling_row():
    f = _fam("B9-02", ["STR.CONC.LINTEL"])
    c, y = B.family_block(f, {"in_candidate": "no", "units": {}}, BYF, PV)
    assert (c["state"], y, c["no_line"]["filled_by"]) == (NI, "no", "T-487")


def test_adverse_no_line_family_with_a_package_is_refused():
    with pytest.raises(SystemExit):
        B.family_block(_fam("K1", ["X.A"]), {"in_candidate": "no", "units": {}}, BYF, PV)


def test_family_without_item_code_is_carried_and_labelled():
    f = _fam("K9", [], H, ["T-131"])
    c, y = B.family_block(f, {"in_candidate": C.NOT_LINE_ATTRIBUTABLE, "units": {}}, BYF, PV)
    assert c["state"] == H and c["packages"] == ["T-131"] and c["candidate_basis"].startswith("CARRIED") and y == "yes"


def test_adverse_census_problems_catch_each_wrong_state(docs):
    new = docs[1]
    assert B.census_problems(new) == []
    for code, state in (("B10-09", H), ("B9-02", BL), ("B8-08", NI)):
        bad = copy.deepcopy(new)
        f = next(x for x in bad["families"] if x["code"] == code)
        f["candidate"]["state"] = state
        assert any(p.startswith(code) for p in B.census_problems(bad)), code
    bad = copy.deepcopy(new)
    f = next(x for x in bad["families"] if x["code"] == "B10-01")
    f["candidate"]["packages"] = [t for t in f["candidate"]["packages"] if t != "T-478"]
    assert any("T-478" in p for p in B.census_problems(bad))


# ---------- stale pending guard ----------

def test_stale_pending_normal_and_adverse():
    doc = {"pending_packages": [{"task": "T-901", "task_commit": "a" * 40}, {"task": "T-902", "task_commit": "b" * 40}]}
    assert B.stale_pending(doc, lambda c: False) == []
    assert B.stale_pending(doc, lambda c: c == "a" * 40) == ["T-901"]


def _git(*a):
    return subprocess.run(["git", "-C", str(ROOT), *a], capture_output=True, text=True)


def _merged(commit):
    """the task commit is on the checked head (a READY package's commit is on its own branch only)"""
    return FMC.git_is_ancestor(commit, "HEAD", root=ROOT)


def test_a_merged_package_never_stays_pending_in_the_newest_registry():
    files = sorted((ROOT / "rules/coverage").glob("BOQ_FAMILY_MASTER_*.json"),
                   key=lambda p: tuple(int(x) for x in p.stem.split("_")[-1].split(".")))
    newest = json.loads(files[-1].read_text(encoding="utf-8"))
    assert B.stale_pending(newest, _merged) == []


def test_1_41_0_pending_are_stale_on_this_head(docs):
    """adverse on real data: the registry this task supersedes fails the guard (38 merged packages pending)"""
    assert len(B.stale_pending(docs[0], _merged)) == 38


# ---------- the committed registry ----------

def test_builder_reproduces_the_committed_file():
    assert B.text(B.build()) == NEW.read_text(encoding="utf-8")


def test_candidate_check_clean_with_git():
    new = json.loads(NEW.read_text(encoding="utf-8"))
    assert FMC.check(new, root=ROOT, is_ancestor=FMC.git_is_ancestor) == []


def test_every_pending_package_promoted_with_its_merge_and_verdict(docs):
    old, new = docs
    by = {p["task"]: p for p in new["candidate_packages"]}
    assert new["pending_packages"] == []
    assert new["candidate"]["method_version"] == "ARCH_TAKEOFF_V3.0.45" and new["candidate"]["as_of_package"] == "T-478"
    for p in old["pending_packages"]:
        q = by[p["task"]]
        assert q["method_version"] == p["method_version"] and q["task_commit"] == p["task_commit"]
        assert FMC.VERDICT.match(q["verdict"]) and q["merge_commit"][:8] in q["verdict"] + q["merge_commit"]
        parents = _git("rev-list", "--parents", "-n", "1", q["merge_commit"]).stdout.split()
        if len(parents) == 3:                    # full history: the merge brought exactly this package in
            assert _git("merge-base", "--is-ancestor", p["task_commit"], parents[2]).returncode == 0
            assert _git("merge-base", "--is-ancestor", p["task_commit"], parents[1]).returncode != 0
        assert FMC.git_is_ancestor(q["merge_commit"], "HEAD", root=ROOT)
    assert [p["task"] for p in new["candidate_packages"][:8]] == [p["task"] for p in old["candidate_packages"]]


def test_no_quantity_capability_or_census_change(docs):
    old, new = docs
    ob = {f["code"]: f for f in old["families"]}
    for f in new["families"]:
        o = ob[f["code"]]
        moved = {"candidate", "in_v3_0_candidate", "v3_0_planned_tasks"} | ({"note"} if f["code"] in B.STALE_NOTE else set())
        if f["code"] in B.STALE_NOTE:
            assert f["note"].startswith(o["note"]) and "T-485" in f["note"]
        assert {k: v for k, v in f.items() if k not in moved} == {k: v for k, v in o.items() if k not in moved}
    oc, nc = dict(old["candidate_census"]), dict(new["candidate_census"])
    assert oc.pop("stale_in_candidate_vs_registry") and nc.pop("stale_in_candidate_vs_registry") == []
    assert oc == nc
    assert new["candidate_census"]["issue_counts"] == {}
    for k in ("capability_counts", "capability_change_counts", "families", "item_codes_without_family"):
        if k != "families":
            assert new[k] == old[k]


def test_registry_census_on_the_committed_index_is_unchanged():
    idx = json.loads((ROOT / "research/agents_t479/out/LINE_INDEX_V3_0_45.json").read_text(encoding="utf-8"))
    new = json.loads(NEW.read_text(encoding="utf-8"))
    cen = C.census(idx, new)
    assert cen["issue_counts"] == {} and not cen["no_family"]
    assert C.compare_blocks(cen, new) == []


def test_no_line_families_and_their_rows(docs):
    new = docs[1]
    fams = {f["code"]: f for f in new["families"]}
    for code, row in (("B8-07", "T-486"), ("B9-02", "T-487")):
        f = fams[code]
        assert f["candidate"]["state"] == NI and f["in_v3_0_candidate"] == "no"
        assert f["candidate"]["no_line"]["filled_by"] == row and row in f["v3_0_planned_tasks"]
    pres = json.loads(B.ATTRIB.read_text(encoding="utf-8"))["item_code_presence"]
    assert pres.get("FIN.WP.BALCONY", []) == [] and pres.get("STR.CONC.LINTEL", []) == []


def test_line_diff_ends_on_the_candidate_of_record():
    a = json.loads(B.ATTRIB.read_text(encoding="utf-8"))
    v = a["versions"]
    assert v["ARCH_TAKEOFF_V3.0.45"]["lines_sha256"].startswith("5972888b")
    assert v["ARCH_TAKEOFF_V3.0.44"]["lines_sha256"].startswith("8b2fe2b6")
    assert v["ARCH_TAKEOFF_V3.0.45"]["lines"] == json.loads(NEW.read_text(encoding="utf-8"))["candidate_census"]["lines"]
    assert sorted(v["ARCH_TAKEOFF_V3.0.45"]["families"]) == ["B10-01"]        # T-478: blinding only (its own report)


def test_rebase_keeps_a_later_unmerged_package_pending(tmp_path, docs):
    """registry version allotted at merge: re-run on a base that also holds a package READY after this one"""
    base = copy.deepcopy(docs[0])
    base["pending_packages"].append({"task": "T-999", "method_version": "ARCH_TAKEOFF_V3.0.46",
                                     "module": "engine/source/arch_v3046.py", "status": "READY_FOR_GATE_B",
                                     "integrates": ["T-998"], "tests": ["tests/t999"], "task_commit": "c" * 40,
                                     "changes_families_by_item_code": [], "note": "synthetic"})
    p = tmp_path / "base.json"
    p.write_text(json.dumps(base), encoding="utf-8")
    new = B.build(p, "9.9.9")
    assert [q["task"] for q in new["pending_packages"]] == ["T-999"]
    assert len(new["candidate_packages"]) == len(docs[0]["candidate_packages"]) + 38
    assert B.census_problems(new) == []


def test_accounted_accepts_pending_or_promoted_and_nothing_weaker(docs):
    import t485_accounting as AC
    old, new = docs
    e = old["pending_packages"][-1]
    assert AC.accounted(e, old) and AC.accounted(e, new)                 # pending unchanged / promoted with its merge
    bad = copy.deepcopy(new)
    q = next(p for p in bad["candidate_packages"] if p["task"] == e["task"])
    q["merge_commit"] = "deadbeef"                                       # not a full merge commit
    assert not AC.accounted(e, bad)
    bad = copy.deepcopy(new)
    q = next(p for p in bad["candidate_packages"] if p["task"] == e["task"])
    q["task_commit"] = "0" * 40                                          # another package's content
    assert not AC.accounted(e, bad)
    assert not AC.accounted(e, {"pending_packages": [], "candidate_packages": []})
