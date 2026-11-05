"""T-507: ARCH_TAKEOFF_V3.0.58 wires the producer wp_applicability_rules_v1, so the default guard runs AT integration
(T-212 P2 / P4): the stage is a GUARD_HOST that re-runs the merged V3.0.6 guard (arch_v307.guard_changes) over the
V3.0.57 lines + its added lines; the rule module leaves the UNWIRED_PRODUCER class. Synthetic NON-Alsenan villa R507.

Normal: a guard block with a drawn inventory -> RUN, no finding, the same changes; every added line names its register
element. Adverse: a drawn part no line carries refuses the run; a guard hold on a candidate line refuses the run; a
candidate importing the rule module while it is still labelled UNWIRED_PRODUCER is refused by the live property."""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
for p in (ROOT, Path(__file__).resolve().parent, ROOT / "research" / "agents_t212", ROOT / "research" / "agents_t202"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

import guard_property as GP                                    # noqa: E402
import guard_sweep as GS                                       # noqa: E402
import test_arch_v3058 as W                                    # noqa: E402
from engine.source import arch_v307 as A307                    # noqa: E402

V3058, WPA = "engine/source/arch_v3058.py", "engine/source/wp_applicability_rules_v1.py"


def guard(inventory=()):
    return {"source": W._src("T-G"),
            "evidence": {"documents": [{"doc": "R507-AR.dxf", "role": "PLAN"}], "printed": [], "doc_alias": {},
                         "inventory": list(inventory), "mapping": {}},
            "evidence_file": "ev.json", "evidence_sha256": "f" * 64,
            "conventions": [{"id": "WP_UPTURN_M", "kind": "dimension", "base": 0.20}],
            "conventions_file": "conv.json", "conventions_sha256": "c" * 64,
            "holding_checks": ["DG-1", "DG-3", "DG-5", "DG-6"], "recorded_checks": ["DG-2"], "new_records": []}


def with_guard(g):
    return dict(W.doc(), guard=g)


def _dump(ch):
    return json.dumps(ch, sort_keys=True, ensure_ascii=False, default=str)


def test_guard_runs_with_no_finding_and_the_same_changes():
    _p, ch0, _ = W.run()
    _p, ch1, log = W.run(with_guard(guard()))
    g = log["default_guard"]
    assert g["state"] == "RUN" and g["findings_by_code"] == {} and g["held_live_new"] == []
    assert g["lines_checked"] == len(W.LINES) + 5                      # every candidate line + the 5 added lines
    assert _dump(ch1) == _dump(ch0)


def test_every_added_line_names_its_register_element():
    _p, ch, _ = W.run()
    assert len(ch) == 5 and all(c["action"] == "ADD" for c in ch)
    assert all(c["guard_element"] == {"element_id": c["after"]["location"]["element_id"], "part": "WHOLE"}
               for c in ch)


def test_adverse_drawn_part_no_line_carries_refuses_the_run():
    g = guard([{"id": "TK-1", "kind": "TANK", "parts": {"WALLS": None}}])
    with pytest.raises(A307.InputsError, match="carried by no line"):
        W.run(with_guard(g))


def test_adverse_guard_hold_on_a_candidate_line_refuses(monkeypatch):
    other = W.LINES[0]

    def fake(_doc, lines, added=(), touched=()):
        ln = next(x for x in lines if x["line_id"] == other["line_id"])
        return [{"piece": "DEFAULT_GUARD", "action": "REPLACE", "before": ln, "after": copy.deepcopy(ln)}], {}
    monkeypatch.setattr(A307, "guard_changes", fake)
    with pytest.raises(ValueError, match="an earlier stage owns"):
        W.run(with_guard(guard()))


def test_guard_classes_on_the_live_tree():
    src = GP.live_sources()
    tab = GP.table()
    assert GP.classify(V3058, src[V3058], tab) == (GS.GUARD_HOST, "declared in module")
    assert GP.classify(WPA, src[WPA], tab) == (GS.GUARDED_VIA_V306, "declared in module")
    rep, problems = GP.check(src, [("A", V3058), ("M", WPA)], tab)
    assert rep["guard_hosts"][V3058] is True
    assert not [p for p in problems if "wp_applicability" in p or V3058 in p]


def test_adverse_candidate_importing_a_producer_still_unwired_is_refused():
    src = GP.live_sources()
    tree = {V3058: src[V3058], WPA: src[WPA].replace('"GUARDED_VIA_V3.0.6"', '"UNWIRED_PRODUCER"', 1)}
    _r, problems = GP.check(tree, [("A", V3058), ("A", WPA)], {})
    assert any(p.startswith(f"{V3058} (a candidate or released method) reaches the unwired producer {WPA}")
               for p in problems)
