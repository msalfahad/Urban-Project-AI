"""T-704: the URBAN_V3071_INPUTS_V1 builder on the committed, sha-pinned T-699 ledger and the V3.0.70 index (no
drawing): 16 AT_MOST + 3 DATUM_NAMED entries, the 2 V3.0.67 AT_LEAST lines confirmed, the hand rows of T-699 s.2, the
family AT_MOST with the W11 / W12 pier once, and every entry accepted by the module (recomputed from its terms)."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
for p in (ROOT, ROOT / "research" / "agents_t704"):
    sys.path.insert(0, str(p))

import t704_inputs as I  # noqa: E402
from engine.source import arch_v3071 as A  # noqa: E402

DOC = I.build()
BY = {e["opening"]: e for e in DOC["entries"]}


def test_counts():
    acts = [e["action"] for e in DOC["entries"]]
    assert acts.count("AT_MOST") == 16 and acts.count("DATUM_NAMED") == 3
    assert sorted(c["opening"] for c in DOC["confirm"]) == ["D-1F-06", "D-GF-04"]
    assert sorted(o for o, e in BY.items() if e["action"] == "DATUM_NAMED") == ["A-GF-01", "D-GF-05", "D-GF-14"]


def test_hand_rows():
    # T-699 s.2 by hand: m3 = B x D x (w + taken bearings)
    assert BY["W08"]["at_most_m3"] == 0.1 and [t["taken_m"] for t in BY["W08"]["end_terms"]] == [0.45, 0.55]
    assert BY["D-2F-02"]["at_most_m3"] == 0.056 and BY["D-2F-02"]["convention"] == "MIN_BEARING"
    assert BY["L-GF-01"]["at_most_m3"] == 0.072 and BY["L-GF-01"]["if_required"]["value_m3"] == 0.072
    assert BY["D-GF-09"]["width_m"] == 1.0 and BY["D-GF-09"]["at_most_m3"] == 0.061876
    assert BY["W11"]["at_most_m3"] == 0.14916 and BY["W12"]["at_most_m3"] == 0.14036
    assert BY["W04"]["existence"] == "CONDITIONAL_EXCLUSION" and BY["W04"]["excluded_by"]


def test_family_and_module_accepts():
    d = A.load_inputs(DOC, "any")
    assert d["_family"]["at_most_m3"] == 1.321826 and d["_family"]["lines"] == 16
    assert DOC["family"]["at_least_m3"] == 0.084
    assert sum(1 for e in d["_entries"] if e["_hi"] is not None) == 16


def test_tampered_pin_refused(monkeypatch):
    monkeypatch.setitem(I.PINS, I.T699, "0" * 64)
    with pytest.raises(SystemExit, match="edited file"):
        I.build()
