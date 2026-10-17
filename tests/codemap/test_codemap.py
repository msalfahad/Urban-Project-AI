"""Tests for tools/codemap.py (the navigation maps and the task router).

Every test builds a small synthetic repository in a temporary folder: no private drawing, no network, and nothing is
written inside this repository. The last test checks that this repository's own maps are current.
"""

import hashlib
import importlib.util
import json
import os
import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
_spec = importlib.util.spec_from_file_location("codemap_under_test", REPO / "tools" / "codemap.py")
cm = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(cm)


def _w(root, rel, text):
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text if isinstance(text, str) else json.dumps(text, indent=1), encoding="utf-8")


TOPICS = {
    "shared_threshold": 2,
    "defect_sources": ["research/old/REGISTER.md", "research/new/REGISTER.md"],
    "topics": [
        {"id": "doors", "title": "Doors", "keywords": ["door", "opening"], "start": ["engine/source/door_model.py"],
         "modules": ["engine/source/door_[a-z_]+\\.py$"], "rules": ["^UP-DOOR"], "families": ["^B6-"],
         "tests": ["tests/fx/"], "defect_terms": ["door"], "related": ["formwork"]},
        {"id": "units", "title": "Units", "keywords": ["unit", "metre"], "modules": ["engine/source/frame\\.py$"],
         "rules": [], "families": [], "tests": ["tests/fx/"], "defect_terms": ["unit"], "risk": "HIGH"},
        {"id": "formwork", "title": "Formwork", "keywords": ["formwork"], "modules": ["formwork"], "rules": [],
         "families": ["^B10-13$"], "tests": ["formwork"], "defect_terms": ["formwork"]},
    ],
}


@pytest.fixture
def repo(tmp_path):
    r = tmp_path / "repo"
    _w(r, "engine/__init__.py", "")
    _w(r, "engine/source/__init__.py", "")
    _w(r, "engine/source/knowledge.py",
       'VERSIONS = {"1.0.0": ROOT / "knowledge" / "URBAN_ENGINEERING_KNOWLEDGE_1.0.0.json"}       # ARCH_TAKEOFF_V2.3\n')
    _w(r, "engine/source/rule_store.py", 'LATEST_APPROVED = "1.5.0"\n')
    _w(r, "engine/source/frame.py", '"""Units and drawing frame."""\n\ndef unit_m(x):\n    return x\n')
    _w(r, "engine/source/door_model.py",
       '"""Door model."""\nfrom engine.source import frame\nfrom engine.source.frame import unit_m\n\n\ndef door_width(d):\n    return frame.unit_m(d)\n')
    _w(r, "engine/source/door_report.py", "from engine.source import door_model\n")
    _w(r, "tests/fx/test_door.py", "from engine.source import door_model\n\ndef test_x():\n    assert door_model\n")
    _w(r, "knowledge/URBAN_ENGINEERING_KNOWLEDGE_1.0.0.json", {"rules": [
        {"rule_id": "UP-DOOR-OPEN-001", "title": "Door opening", "status": "OWNER_APPROVED", "effective_version": "1.0.0",
         "supersedes": [], "superseded_by": None, "code": ["engine/source/door_model.py::door_width"],
         "tests": ["tests/fx/test_door.py::test_x"]}]})
    _w(r, "rules/owner_library/URBAN_PROJECTS_RULE_LIBRARY_1.4.0.json", {"rules": [
        {"rule_id": "UP-STAIR-001", "rule_name": "Stair rule", "trade": "STAIR", "version": "1.0.0"}]})
    _w(r, "rules/owner_decisions/URBAN_RULES_1.5.0.json", {"records": []})
    _w(r, "rules/coverage/BOQ_FAMILY_MASTER_1.0.0.json", {"families": [
        {"code": "B6-01", "group": "B6", "item_en": "Doors", "unit": "nr", "capability": "PARTIAL"},
        {"code": "B6-02", "group": "B6", "item_en": "Door frames", "unit": "nr", "capability": "EXPERIMENTAL"},
        {"code": "B6-03", "group": "B6", "item_en": "Door count", "unit": "nr", "capability": "INTEGRATED_AND_TESTED"},
        {"code": "B10-13", "group": "B10", "item_en": "Formwork", "unit": "m2", "capability": "NOT_IMPLEMENTED"}]})
    _w(r, "research/freeze_integrity/FREEZE_BASELINE_INDEX.jsonl",
       json.dumps({"pinned_code": ["engine/source/frame.py"]}) + "\n")
    _w(r, "research/old/REGISTER.md", "# Old\n\nSnapshot 2026-01-02.\n\n## Known bugs\n\n| id | Defect | Status |\n|---|---|---|\n"
       "| B1 | door width read in the wrong unit | OPEN |\n| B2 | door swing mirrored | fixed |\n"
       "| B3 | unit conflict | OPEN |\n| B4 | door leaf missing | - |\n")
    _w(r, "research/new/REGISTER.md", "# New\n\n## Still open\n\n| id | Status |\n|---|---|\n| B3 / B5 | open |\n\n"
       "## Found\n\n| id | Defect | Status |\n|---|---|---|\n| D-P9-01 | door threshold wrong | open: fix pending |\n"
       "| D-P9-02 | door lintel short | fixed in V2.8 |\n")
    _w(r, "tools/routing_topics.json", TOPICS)
    env = dict(os.environ, GIT_AUTHOR_DATE="2026-01-02T00:00:00", GIT_COMMITTER_DATE="2026-01-02T00:00:00")
    for cmd in (["init", "-q"], ["add", "-A"], ["-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "fixture"]):
        subprocess.run(["git", "-C", str(r)] + cmd, check=True, env=env, capture_output=True)
    return r


def run(root, *argv):
    return cm.main(list(argv), root=root)


def hashes(root):
    return {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(root.rglob("*")) if p.is_file() and ".git" not in p.parts}


def test_regeneration_is_deterministic(repo):
    a, pa, *_ = cm.build(cm.Repo(repo))
    b, pb, *_ = cm.build(cm.Repo(repo))
    assert a == b and not pa.errors and not pb.errors
    assert set(a) == set(cm.MAPS)


def test_check_is_read_only(repo, capsys):
    assert run(repo) == 0
    before = hashes(repo)
    assert run(repo, "check") == 0
    assert hashes(repo) == before
    assert "stale: none" in capsys.readouterr().out


def test_stale_map_is_detected(repo, capsys):
    assert run(repo) == 0
    _w(repo, "engine/source/door_hinge.py", '"""A new module."""\n')
    assert run(repo, "check") == 1
    assert "stale:" in capsys.readouterr().out
    assert run(repo) == 0 and run(repo, "check") == 0


def test_missing_required_path_fails_and_writes_nothing(repo, capsys):
    t = json.loads((repo / "tools/routing_topics.json").read_text())
    t["topics"][0]["start"] = ["engine/source/no_such_module.py"]
    _w(repo, "tools/routing_topics.json", t)
    assert run(repo) == 1
    out = capsys.readouterr().out
    assert "start module does not exist" in out and "not written" in out
    assert not (repo / "docs/ROUTING.md").exists()
    t["defect_sources"].append("research/missing.md")
    _w(repo, "tools/routing_topics.json", t)
    assert run(repo, "check") == 1
    assert "defect source missing" in capsys.readouterr().out


def test_malformed_topic_definitions_are_errors(repo, capsys):
    t = json.loads((repo / "tools/routing_topics.json").read_text())
    t["topics"].append(dict(t["topics"][1]))                         # duplicate id
    t["topics"].append({"id": "broken", "title": "x"})               # missing keys
    t["topics"][2]["modules"] = ["engine/(unclosed"]                  # malformed regex
    t["topics"][0]["related"] = ["nowhere"]                          # unknown related topic
    _w(repo, "tools/routing_topics.json", t)
    assert run(repo, "check") == 1
    out = capsys.readouterr().out
    for msg in ("duplicate topic id units", "missing keys", "malformed regex", "related topic does not exist"):
        assert msg in out


def test_broken_rule_references_are_errors(repo, capsys):
    t = json.loads((repo / "tools/routing_topics.json").read_text())
    t["topics"][0]["rule_ids"] = ["UP-DOOR-NOPE-999"]
    t["topics"][1]["rules"] = ["^UP-UNITS"]
    _w(repo, "tools/routing_topics.json", t)
    assert run(repo, "check") == 1
    out = capsys.readouterr().out
    assert "rule id not in the knowledge registry" in out and "matches no rule" in out


def test_historical_defect_status_handling(repo):
    r = cm.Repo(repo)
    allc, by_topic = cm.defects_by_topic(r, json.loads((repo / "tools/routing_topics.json").read_text()))
    cls = {k: v["defect_class"] for k, v in allc.items()}
    assert cls["B1"] == "HISTORICAL_UNVERIFIED"   # open in the older register, not restated: never VERIFIED_OPEN
    assert cls["B2"] == "REGRESSION_RISK"         # fixed in an older register
    assert cls["B3"] == "VERIFIED_OPEN"           # carried forward in a multi-id row of the newest register
    assert cls["B5"] == "VERIFIED_OPEN"
    assert cls["B4"] == "UNKNOWN"                 # no status recorded
    assert cls["D-P9-01"] == "VERIFIED_OPEN" and cls["D-P9-02"] == "VERIFIED_FIXED"
    assert allc["B3"]["summary"] == "unit conflict"   # the carry-forward row keeps the older description
    assert allc["B3"]["history"] and "OPEN" in allc["B3"]["history"][0]
    assert "B1" in {d["id"] for d in by_topic["doors"]} and "B3" in {d["id"] for d in by_topic["units"]}
    assert allc["B1"]["evidence"].startswith("research/old/REGISTER.md") and allc["B1"]["evidence_date"] == "2026-01-02"
    assert allc["D-P9-01"]["evidence_date"] == "phase new"   # undated register: its phase folder, never git history


def test_capability_status_is_exact(repo):
    out, P, *_ = cm.build(cm.Repo(repo))
    row = next(ln for ln in out["docs/ROUTE_QUICK.md"].splitlines() if ln.startswith("| [doors]"))
    assert row.rstrip().endswith("| 1 / 3 |")       # only INTEGRATED_AND_TESTED counts as integrated
    routing = out["docs/ROUTING.md"]
    assert "INTEGRATED_AND_TESTED 1, PARTIAL 1, EXPERIMENTAL 1" in routing


def test_unsupported_topic_is_reported_not_failed(repo):
    out, P, *_ = cm.build(cm.Repo(repo))
    assert not P.errors
    assert "**No module implements this topic.** BOQ families: B10-13 Formwork (NOT_IMPLEMENTED)" in out["docs/ROUTING.md"]
    assert "**not implemented**" in out["docs/ROUTE_QUICK.md"]


def test_stable_output_after_repeated_runs(repo):
    seen = set()
    for _ in range(3):
        assert run(repo) == 0 and run(repo, "check") == 0
        seen.add(tuple(sorted((k, v) for k, v in hashes(repo).items() if "docs" in k.parts)))
    assert len(seen) == 1


def test_route_and_impact(repo, capsys):
    assert run(repo, "route", "door opening width is wrong in metres", "--json") == 0
    res = json.loads(capsys.readouterr().out)
    assert res["primary"] == "doors" and "units" in res["secondary"] and res["related"] == ["formwork"]
    d = res["topics"]["doors"]
    assert d["open_first"][0] == "engine/source/door_model.py" and "UP-DOOR-OPEN-001" in d["rules"]
    assert any(x.startswith("B1 HISTORICAL_UNVERIFIED") for x in d["defects_unresolved"])
    assert run(repo, "impact", "engine/source/frame.py", "--json") == 0
    imp = json.loads(capsys.readouterr().out)
    assert imp["risk"] == "CRITICAL" and imp["frozen"]
    assert imp["imported_by_direct"] == ["engine/source/door_model.py"]
    assert imp["imported_by_transitive_count"] == 3 and "tests/fx" in imp["test_folders_transitive"]
    assert run(repo, "route", "something unrelated entirely") == 2


def test_repository_maps_are_current():
    """This repository's own maps: run `python3 -I tools/codemap.py` when this fails."""
    assert cm.main(["check"], root=REPO) == 0
