"""T-729 on the development villa (committed merged ledgers only, no drawing, no private file): the entries rebuild equal
to research/agents_t729/out/T729_ENTRIES.json; every pinned input; stale 0 on V3.0.74; one live statement per line with
the declared precedence; the formwork family after wiring equals the merged T-735 family (by class and m2); the T-730
hub rows all covered; the cap of 0 never wired; held never 0; the V3.0.75 inputs load. Adverse: a stale pin, a cap of 0
re-entered, an entry dropped (coverage), a T-714 figure picked over a declared restatement."""
from __future__ import annotations

import copy
import json
import sys
from decimal import Decimal
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
for p in (ROOT, ROOT / "research" / "agents_t729"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

import t729_inputs as T  # noqa: E402
from engine.source import arch_v3075 as A  # noqa: E402

DOC = T.build()
BY = {e["line_id"]: e for e in DOC["entries"] if e["line_id"]}


def test_rebuild_equals_committed():
    text = json.dumps(DOC, ensure_ascii=False, indent=1, sort_keys=True) + "\n"
    assert T.OUT.read_text(encoding="utf-8") == text


def test_counts_and_family_equal_t735():
    c = DOC["census"]
    assert c["STR.FORMWORK|RELEASE"]["lines"] == 54 and Decimal(c["STR.FORMWORK|RELEASE"]["value"]) == \
        Decimal("33.127058")
    assert (c["STR.FORMWORK|BOUND"]["lines"], c["STR.FORMWORK|BOUND"]["low"], c["STR.FORMWORK|BOUND"]["high"]) == \
        (32, "107.200712", "132.785507")
    assert (c["STR.FORMWORK|AT_LEAST"]["lines"], c["STR.FORMWORK|AT_LEAST"]["low"]) == (40, "122.484697")
    assert (c["STR.FORMWORK|CAP"]["lines"], c["STR.FORMWORK|CAP"]["cap"]) == (58, "59.379875")
    assert c["STR.FORMWORK|NAMED"]["lines"] == 186
    assert (c["STR.FORMWORK.STAIR|BOUND"]["low"], c["STR.FORMWORK.STAIR|BOUND"]["high"]) == ("2.583193", "3.223465")
    assert c["STR.FORMWORK.STAIR|AT_LEAST"]["low"] == "7.872094"
    assert (c["STR.FORMWORK.STAIR|CAP"]["lines"], c["STR.FORMWORK.STAIR|CAP"]["cap"]) == (12, "6.261899")
    assert DOC["family_check"]["got_by_class"] == DOC["family_check"]["t735_family"]["by_class"]


def test_precedence_named_lines():
    # T-735 decider: the cap-0 line is one point 0.102019, never 0, never the T-714 cap
    e = BY["L-867e155d6f8f0a452eba"]
    assert (e["source"], e["action"], e["low"], e["high"]) == ("T-735", "BOUND", "0.102019", "0.102019")
    assert e["supersedes"][0]["cause"] == "CAP_ZERO_FROM_HELD_DEPTH"
    # T-735 412: BOUNDED 4.183916 .. 5.532116 (never the T-707 4.3498 .. 5.698 upper-bound method)
    e = BY["L-6f83fc39933954d0e3e6"]
    assert (e["source"], e["low"], e["high"]) == ("T-735", "4.183916", "5.532116")
    assert {s["piece"] for s in e["supersedes"]} == {"T-707", "T-714"}
    # T-732: column restated; T-724: soffit low; T-731: stair high and cap
    assert (BY["L-fa037ca1982c83c29750"]["source"], BY["L-fa037ca1982c83c29750"]["low"]) == ("T-732", "3.720600")
    assert (BY["L-3280c42cb578a211045e"]["low"], BY["L-3280c42cb578a211045e"]["high"]) == ("3.559782", "3.733233")
    assert (BY["L-9c3643da524267bf47f6"]["source"], BY["L-9c3643da524267bf47f6"]["high"]) == ("T-731", "0.843465")
    assert (BY["L-d9790e457fd530487553"]["source"], BY["L-d9790e457fd530487553"]["cap"]) == ("T-731", "0.862807")
    # C10
    assert (BY["L-fb7a6431fede62e93fd5"]["action"], BY["L-fb7a6431fede62e93fd5"]["cap"]) == ("CAP", "3.525600")
    assert (BY["L-7863355dfcb68a681d2d"]["low"], BY["L-7863355dfcb68a681d2d"]["restates"]["value"]) == \
        ("1.213428", "1.213429")


def test_no_cap_zero_no_zero_figure_and_stale_none():
    for e in DOC["entries"]:
        for f in ("low", "high", "cap", "value"):
            if e.get(f) is not None:
                assert Decimal(e[f]) > 0, (e["line_id"], f)
        assert not e.get("cap_zero")
        if e["action"] != "ADD_NAMED":
            assert e["before"]["class"] == "HELD"
    assert DOC["t730_coverage"]["missing_hosts"] == []
    assert DOC["t730_coverage"]["keep_unchanged"] == ["T-724:L-ab37afa17f2ac5b0efd1"]


def test_v3075_inputs_load():
    d = T.inputs(DOC)
    inp = A.load_inputs(d)
    assert len(inp["_entries"]) == 396
    assert sum(1 for e in inp["_entries"] if e["action"] == "ADD_NAMED") == 4


# --------------------------------------------------------------------------------------------- adverse
def test_stale_pin_refused(monkeypatch):
    monkeypatch.setitem(T.PINS, "research/agents_t714/out/T714_FORMWORK_BOUNDS.json", "0" * 16)
    with pytest.raises(T.InputsError, match="stale input"):
        T.build()


def test_cap_zero_reentered_refused():
    d = copy.deepcopy(T.inputs(DOC))
    e = [x for x in d["entries"] if x["action"] == "CAP"][0]
    e["cap"] = "0.000000"
    with pytest.raises(A.InputsError, match="cap of 0"):
        A.load_inputs(d)


def test_dropped_entry_breaks_coverage():
    ents = [e for e in DOC["entries"] if e["line_id"] != "L-6f83fc39933954d0e3e6"]
    cov = T.check_t730(ents)
    assert "L-6f83fc39933954d0e3e6" in cov["missing_hosts"]


def test_picking_t714_over_declared_restatement_breaks_family(monkeypatch):
    real = T.formwork_live

    def picked():
        live, fam = real()
        live["L-6f83fc39933954d0e3e6"] = dict(live["L-6f83fc39933954d0e3e6"], action="NAMED", low=None, high=None)
        return live, fam
    monkeypatch.setattr(T, "formwork_live", picked)
    with pytest.raises(T.InputsError, match="T-735 family"):
        T.build()
