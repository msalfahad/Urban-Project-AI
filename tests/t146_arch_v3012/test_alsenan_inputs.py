"""T-146 + T-247: the development villa's V3.0.12 inputs (research/agents_t146/t146_inputs.py) as committed: built only
from checker-merged ledgers (T-252 r2, T-234) and the worker's V3.0.11 snapshot, all pinned by sha256; no drawing is
read here. Pins the accounting the Checker re-runs: every candidate beam line kept or superseded by name, one line per
replacing run, the 13 non-slab faces each with one home, the ring overlap removed once, held never 0."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "research" / "agents_t146"))

from engine.source import arch_v3012 as A  # noqa: E402

AP = pytest.approx
PID = "alsenan"


@pytest.fixture(scope="module")
def doc():
    import t146_inputs as L
    d = L.inputs(PID)
    d = dict(d, guard=None)          # the guard inputs are the V3.0.7 ones (their own tests); not re-checked here
    return A.load_inputs(d, PID)


def _piece(doc, name):
    return next(p for p in doc["pieces"] if p["piece"] == name)


def test_every_candidate_beam_line_accounted_once(doc):
    b = _piece(doc, "BEAM_LEDGER")
    snap = json.loads((ROOT / "research/agents_t146/CANDIDATE_V3011_BEAM_SLAB.json").read_text(encoding="utf-8"))
    cand = {x["element_id"] for x in snap["lines"] if x["item_code"] == "STR.CONC.BEAM"
            and x["evidence_state"] != "NOT_APPLICABLE_WITH_EVIDENCE"}
    keep = {x["element_id"] for x in b["scope"]["keep_lines"]}
    sup = {x["element_id"] for x in b["scope"]["supersede_lines"]}
    assert keep.isdisjoint(sup) and keep | sup == cand
    assert (len(keep), len(sup), len(b["records"])) == (84, 50, 53)
    runs = [r["run"] for r in b["records"]] + [x["run"] for x in b["scope"]["keep_lines"]]
    assert len(runs) == len(set(runs)) == 137                         # the ledger's 137 live runs, each once


def test_declared_totals_are_the_ledger_less_the_ring_overlap(doc):
    t = _piece(doc, "BEAM_LEDGER")["declared_totals"]
    assert t["measured"] == AP(66.320598 - 0.00342 * 0.75, abs=3e-6)
    assert t["conflict"] == [AP(5.144829), AP(6.11101)]
    assert t["held"] == [AP(4.1277 - 0.8997), AP(8.5682 - 0.8997)]  # the east ring is held with no value
    assert t["held_no_value"] == ["BM-1F-037", "BM-1F-038", "BM-1F-039", "BM-2F-019#2F-031", "BM-GF-061"]
    adj = [a for r in _piece(doc, "BEAM_LEDGER")["records"] for a in r.get("adjust") or ()]
    assert sum(a["m3"] for a in adj) == AP(0.002565, abs=2e-6) and len(adj) == 3


def test_held_runs_never_carry_a_value_or_zero(doc):
    for r in _piece(doc, "BEAM_LEDGER")["records"]:
        if r["status"] != "CALCULATED":
            assert r.get("value") is None and r["evidence_status"] == "HELD"
            assert r.get("range") is None or r["range"][0] > 0


def test_thirteen_slab_faces_each_with_one_home(doc):
    s = _piece(doc, "SLAB_FACE_HOME")
    assert len(s["faces"]) == 13
    kinds = [f["home"]["kind"] for f in s["faces"]]
    assert kinds.count("NOT_CONCRETE") == 3 and kinds.count("BEAM_RUN") == 10
    assert sum(f["carried"] for f in s["faces"]) == AP(0.639062, abs=2e-6)
    b = _piece(doc, "BEAM_LEDGER")
    runs = {r["run"] for r in b["records"]} | {x["run"] for x in b["scope"]["keep_lines"]}
    assert all(f["home"]["run"] in runs for f in s["faces"] if f["home"]["kind"] == "BEAM_RUN")
    assert {k: v["drawing"] for k, v in s["declared_after"].items()} == {
        "GF": AP(33.06952), "1F": AP(19.756576), "2F": AP(7.4543)}


def test_tampered_ledger_is_refused(monkeypatch):
    import t146_inputs as L
    monkeypatch.setattr(L, "T252_LEDGER_SHA", "0" * 64)
    with pytest.raises(SystemExit, match="changed"):
        L.inputs(PID)
