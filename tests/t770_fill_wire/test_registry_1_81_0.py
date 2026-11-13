"""T-770 r3 (Verifier FAULT 1 / FAULT 2 on r2): the 1.81.0 registry builder has both modes and the run check
classifies lines as the T-479 index does. Committed files only; no drawing, no Drive."""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "research" / "agents_t770"
for p in (ROOT, HERE, ROOT / "research" / "agents_t469"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

import build_master_1_81_0 as BM  # noqa: E402
import t469_trade_scoreboard as T469  # noqa: E402


def test_pending_registry_equals_its_builder_and_owns_the_safety_code_once():
    doc = BM.build()
    assert (ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.81.0.json").read_text(encoding="utf-8") == BM.text(doc)
    assert [p["task"] for p in doc["pending_packages"]] == ["T-770"]
    owners = [f["code"] for f in doc["families"] if "STR.CONC.SAFETY" in (f.get("item_codes") or ())]
    assert owners == ["B9-02"]
    assert BM.problems(doc) == []


def test_promote_mode_exists_and_refuses_without_its_merge_sources(tmp_path, monkeypatch):
    # adverse: no promotion source (no merge yet) -> refused, never a silently pending "promoted" file
    monkeypatch.setattr(BM, "PROMOTIONS", tmp_path / "absent.json")
    with pytest.raises((SystemExit, FileNotFoundError)):
        BM.build_promoted()
    assert "--promote" in Path(BM.__file__).read_text(encoding="utf-8")


def test_pending_refuses_a_base_with_a_pending_package(monkeypatch, tmp_path):
    old = json.loads(BM.OLD.read_text(encoding="utf-8"))
    bad = copy.deepcopy(old)
    bad["pending_packages"] = [{"task": "T-999"}]
    p = tmp_path / "BOQ_FAMILY_MASTER_1.80.0.json"
    p.write_text(json.dumps(bad), encoding="utf-8")
    monkeypatch.setattr(BM, "OLD", p)
    with pytest.raises(SystemExit):
        BM.build()


REV = "ab" * 32


def _line(lid, net, unit="kg"):
    return {"line_id": lid, "item_code": "STR.REBAR", "unit": unit, "evidence_state": "MEASURED",
            "measured_net": net, "project": {"project_id": "P", "revision_set_sha256": REV}}


def test_index_rule_downgrade_holds_released_lines_and_never_promotes():
    import v3081_run as R
    snap = json.loads(R.DOWNGRADES.read_text(encoding="utf-8"))
    assert R.hashlib.sha256(R.DOWNGRADES.read_bytes()).hexdigest() == R.DOWNGRADES_SHA
    # the committed V3.0.81 index applies exactly the downgrade the V3.0.79 index applies (38 rebar lines, same id)
    i79 = json.loads((ROOT / "research/agents_t314/out/LINE_INDEX_V3_0_79.json").read_text(encoding="utf-8"))
    i81 = json.loads(R.INDEX81.read_text(encoding="utf-8"))
    app = lambda d: sorted((r["downgrade_id"], r.get("lines_to_held")) for r in d["downgrades"]  # noqa: E731
                           if r.get("status") == "APPLIED")
    assert app(i79) == app(i81)
    assert sum(n for _i, n in app(i81)) >= 38
    # normal (synthetic): a binding downgrade on two RELEASED lines holds both; adverse: a HELD line stays HELD and a
    # quantity mismatch binds nothing (never promotes, never applies stale)
    lines = [_line("L-a", 10.0), _line("L-b", 5.0), dict(_line("L-c", None), evidence_state="HELD")]
    good = [r for r in snap["downgrades"] if r.get("downgrade_id") == "DG-1b0eacce2d68f2a5"]
    assert len(good) == 1, "the snapshot holds the rebar footing downgrade the index applies"
    rec = dict(good[0], downgrade_id="DG-test", line_ids=["L-a", "L-b"], engine_qty=15.0, unit="kg",
               project_id="P", revision_set_sha256=REV, resolved=False)
    rec.pop("binding", None)     # a whole-file (T-245) record: binds by quantity, not by its own lines' content
    held, status = T469.applied_downgrades(lines, [rec])
    assert status[0]["status"] == "APPLIED", status
    assert set(held) == {"L-a", "L-b"}
    held2, status2 = T469.applied_downgrades(lines, [dict(rec, engine_qty=99.0)])
    assert held2 == {} and status2[0]["status"].startswith("STALE_QTY")
