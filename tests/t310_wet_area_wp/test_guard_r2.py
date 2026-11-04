"""T-310 r2: ARCH_TAKEOFF_V3.0.57 wires the quantity producer waterproofing policy V3 (and through it V2), so the
default guard runs AT integration (T-212 P2 / P4): the stage is a GUARD_HOST that re-runs the merged V3.0.6 guard
(arch_v307.guard_changes) over the V3.0.50 lines with its changes + its added lines; the two policy modules leave the
UNWIRED_PRODUCER class. Synthetic NON-Alsenan villa W310 of test_arch_v3057 (its figures, no drawing).

Normal: no guard block -> NO_PROJECT_INPUT in the log, the changes unchanged; a guard block with a drawn inventory that
every line carries -> RUN, no finding, the same changes byte for byte; every added line names its register element.
Adverse: a drawn part no line carries refuses the run (DG-5, never a silent 0); a guard hold on a line this version does
not change refuses the run (nothing outside the waterproofing codes moves); a malformed guard block is refused at load;
the live guard property keeps refusing a candidate that imports a producer still labelled UNWIRED_PRODUCER."""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(ROOT / "research" / "agents_t212"))
sys.path.insert(0, str(ROOT / "research" / "agents_t202"))

import guard_property as GP                                    # noqa: E402
import guard_sweep as GS                                       # noqa: E402
import test_arch_v3057 as W                                    # noqa: E402
from engine.source import arch_v307 as A307                    # noqa: E402
from engine.source import arch_v3057 as A                      # noqa: E402

V3057 = "engine/source/arch_v3057.py"
WP2, WP3 = "engine/source/waterproofing_policy_v2.py", "engine/source/waterproofing_policy_v3.py"


def guard(inventory=()):
    return {"source": W._src("T-G"),
            "evidence": {"documents": [{"doc": "W310-AR.dxf", "role": "PLAN"}], "printed": [], "doc_alias": {},
                         "inventory": list(inventory), "mapping": {}},
            "evidence_file": "ev.json", "evidence_sha256": "f" * 64,
            "conventions": [{"id": "WP_UPTURN_M", "kind": "dimension", "base": 0.20}],
            "conventions_file": "conv.json", "conventions_sha256": "c" * 64,
            "holding_checks": ["DG-1", "DG-3", "DG-5", "DG-6"], "recorded_checks": ["DG-2"], "new_records": []}


def with_guard(g):
    return dict(W.doc(), guard=g)


def _dump(ch):
    return json.dumps(ch, sort_keys=True, ensure_ascii=False, default=str)


def test_no_guard_block_is_logged_not_run_and_changes_unchanged():
    _p, ch, log = W.run()
    assert log["default_guard"] == {"piece": "DEFAULT_GUARD", "state": "NO_PROJECT_INPUT"}
    assert len(ch) == 9


def test_guard_runs_with_no_finding_and_the_same_changes():
    _p, ch0, _ = W.run()
    _p, ch1, log = W.run(with_guard(guard()))
    g = log["default_guard"]
    assert g["state"] == "RUN" and g["findings_by_code"] == {} and g["held_live_new"] == []
    assert g["lines_checked"] == len(W.LINES) + 3                      # every candidate line + the 3 added lines
    assert _dump(ch1) == _dump(ch0)


def test_every_added_line_names_its_register_element():
    _p, ch, _ = W.run()
    adds = [c for c in ch if c["action"] == "ADD"]
    assert len(adds) == 3
    assert all(c["guard_element"] == {"element_id": c["after"]["location"]["element_id"], "part": "WHOLE"}
               for c in adds)
    assert all("guard_element" not in c for c in ch if c["action"] != "ADD")


def test_adverse_drawn_part_no_line_carries_refuses_the_run():
    g = guard([{"id": "TK-1", "kind": "TANK", "parts": {"WALLS": None}}])
    with pytest.raises(A307.InputsError, match="carried by no line"):
        W.run(with_guard(g))


def test_adverse_guard_hold_outside_this_version_refuses(monkeypatch):
    other = next(ln for ln in W.LINES if ln["item_code"] == "FIN.FLOOR.CERAMIC")

    def fake(_doc, lines, added=(), touched=()):
        ln = next(x for x in lines if x["line_id"] == other["line_id"])
        return [{"piece": "DEFAULT_GUARD", "action": "REPLACE", "before": ln, "after": copy.deepcopy(ln)}], {}
    monkeypatch.setattr(A307, "guard_changes", fake)
    with pytest.raises(ValueError, match="does not change"):
        W.run(with_guard(guard()))


def test_adverse_malformed_guard_is_refused_at_load():
    g = guard()
    g["holding_checks"] = ["DG-3"]                                    # DG-1 and DG-5 always hold
    with pytest.raises(ValueError, match="always hold"):
        A.load_inputs(with_guard(g), W.PID)
    g = guard()
    del g["evidence"]["inventory"]
    with pytest.raises(ValueError, match="inventory"):
        A.load_inputs(with_guard(g), W.PID)


def test_guard_classes_on_the_live_tree():
    src = GP.live_sources()
    tab = GP.table()
    assert GP.classify(V3057, src[V3057], tab) == (GS.GUARD_HOST, "declared in module")
    for m in (WP2, WP3):
        assert GP.classify(m, src[m], tab) == (GS.GUARDED_VIA_V306, "declared in module")
    rep, problems = GP.check(src, [("A", V3057), ("A", WP3), ("M", WP2)], tab)
    assert rep["guard_hosts"][V3057] is True
    assert not [p for p in problems if "waterproofing_policy" in p or V3057 in p]


def test_adverse_candidate_importing_a_producer_still_unwired_is_refused():
    src = GP.live_sources()
    tree = {V3057: src[V3057], WP3: src[WP3].replace('"GUARDED_VIA_V3.0.6"', '"UNWIRED_PRODUCER"', 1),
            WP2: src[WP2]}
    _r, problems = GP.check(tree, [("A", V3057), ("A", WP3)], {})
    assert any(p.startswith(f"{V3057} (a candidate or released method) reaches the unwired producer {WP3}")
               for p in problems)
