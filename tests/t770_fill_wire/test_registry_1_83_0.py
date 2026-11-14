"""T-770 r6: the 1.83.0 registry builder (package T-770c, ARCH_TAKEOFF_V3.0.83) has both modes, the committed file
equals the builder in the mode it was written, every code the package moves keeps exactly one owner and no code is
added, and the pending package names its module and inputs. Committed files only; no drawing, no Drive."""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "research" / "agents_t770"
for p in (ROOT, HERE):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

import build_master_1_83_0 as BM  # noqa: E402

OLD_DOC = json.loads((ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.82.0.json").read_text(encoding="utf-8"))


def _assert_registry(text, bm=BM):
    cur = json.loads(text)
    promoted = not cur.get("pending_packages")
    doc = bm.build_promoted() if promoted else bm.build()
    mode = "promoted" if promoted else "pending"
    assert text == bm.text(doc), f"committed 1.83.0 differs from its builder ({mode})"
    if mode == "pending":
        p = doc["pending_packages"]
        assert [x["task"] for x in p] == ["T-770c"] and p[0]["module"] == "engine/source/arch_v3083.py"
        assert p[0]["integrates"] == ["T-757", "T-763", "T-765", "T-776"]
    else:
        assert doc["pending_packages"] == [] and doc["candidate"]["method_version"] == "ARCH_TAKEOFF_V3.0.83"
    owned = sorted(c for f in cur["families"] for c in (f.get("item_codes") or ()))
    assert owned == sorted(c for f in OLD_DOC["families"] for c in (f.get("item_codes") or ()))   # no code added
    for code in bm.CODES:
        assert len([f for f in cur["families"] if code in (f.get("item_codes") or ())]) == 1, code
    assert bm.problems(cur) == []
    return mode


def test_committed_registry_equals_its_builder_in_its_mode():
    _assert_registry((ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.83.0.json").read_text(encoding="utf-8"))


def test_promoted_file_differing_or_losing_an_owner_fails(monkeypatch):
    doc = copy.deepcopy(BM.build())
    doc["pending_packages"] = []
    doc["candidate"] = dict(doc["candidate"], method_version="ARCH_TAKEOFF_V3.0.83")
    monkeypatch.setattr(BM, "build_promoted", lambda: copy.deepcopy(doc))
    monkeypatch.setattr(BM, "problems", lambda d: [])
    assert _assert_registry(BM.text(doc)) == "promoted"
    bad = copy.deepcopy(doc)
    bad["as_of"] = str(bad.get("as_of")) + " edited"
    with pytest.raises(AssertionError, match="differs from its builder \\(promoted\\)"):
        _assert_registry(BM.text(bad))
    lost = copy.deepcopy(doc)
    for f in lost["families"]:
        if "MAS.BLOCK" in (f.get("item_codes") or ()):
            f["item_codes"] = [c for c in f["item_codes"] if c != "MAS.BLOCK"]
    monkeypatch.setattr(BM, "build_promoted", lambda: copy.deepcopy(lost))
    with pytest.raises(AssertionError):
        _assert_registry(BM.text(lost))


def test_promote_refuses_without_its_merge_sources(tmp_path, monkeypatch):
    monkeypatch.setattr(BM, "PROMOTIONS", tmp_path / "absent.json")
    with pytest.raises((SystemExit, FileNotFoundError)):
        BM.build_promoted()


def test_pending_refuses_a_base_with_a_pending_package_or_another_candidate(monkeypatch, tmp_path):
    old = json.loads(BM.OLD.read_text(encoding="utf-8"))
    bad = copy.deepcopy(old)
    bad["pending_packages"] = [{"task": "T-999"}]
    p = tmp_path / "base.json"
    p.write_text(json.dumps(bad), encoding="utf-8")
    monkeypatch.setattr(BM, "OLD", p)
    with pytest.raises(SystemExit):
        BM.build()
    other = copy.deepcopy(old)
    other["candidate"] = dict(other["candidate"], method_version="ARCH_TAKEOFF_V3.0.81")
    p.write_text(json.dumps(other), encoding="utf-8")
    with pytest.raises(SystemExit, match="candidate of record"):
        BM.build()


def test_package_codes_are_the_codes_the_index_moves():
    s = json.loads((HERE / "out/V3_0_83_SUMMARY.json").read_text(encoding="utf-8"))
    moved = sorted({k.split(" [")[0] for k in s["totals_moved"]})
    assert moved == BM.CODES
