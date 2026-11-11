"""T-693 inputs builder on the committed, Checker-merged ledgers (no drawing read): counts, the hand figures of every
restated line (section x height, the B8 joint 12.200 - 0.013 + 0.75 = 12.937), the code totals by hand, every entry
accepted by the V3.0.70 loader, a tampered pin refused, the plate transfer not wired."""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
for p in (ROOT / "research" / "agents_t693", ROOT / "research" / "agents_t682"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

import t693_inputs as T  # noqa: E402
from engine.source import arch_v3070 as M  # noqa: E402


@pytest.fixture(scope="module")
def doc():
    return T.build()


def test_counts_and_loader(doc):
    acts = {}
    for e in doc["entries"]:
        acts[e["action"]] = acts.get(e["action"], 0) + 1
    assert acts == {"NARROW": 1, "BOUND": 5, "RELABEL": 1}
    d = M.load_inputs(doc)
    assert len(d["_entries"]) == 7
    assert {e["source_tasks"][0] for e in doc["entries"]} == {"T-689", "T-688"}


def test_hand_figures(doc):
    r = {e["line_id"]: e for e in doc["entries"]}
    assert abs(12.200 - 0.013 + 0.75 - 12.937) < 1e-9
    c2 = r[T.C2_412]
    assert c2["after"] == {"low": round(0.10 * (12.937 - 9.65), 6), "high": round(0.10 * (13.90 - 9.65), 6)}
    assert c2["expect"]["low"] == 0.303 and c2["ends_moved"] == ["low"]
    c5 = r[T.C5_415]
    assert c5["after"] == {"low": round(0.10 * 3.287, 6), "high": round(0.60 * 0.20 * 4.25, 6)}   # 0.3287 .. 0.51
    annex = [e for e in doc["entries"] if e["action"] == "BOUND" and e["line_id"] != T.C5_415]
    assert len(annex) == 4
    for e in annex:
        assert e["height"]["h_lo_m"] == pytest.approx(3.294) and e["height"]["h_hi_m"] == pytest.approx(4.05)
        assert e["after"]["low"] == pytest.approx(0.08 * 3.294)
    assert sorted(e["after"]["high"] for e in annex) == pytest.approx([0.405, 0.405, 0.405, 0.125 * 4.05])
    b = [e for e in doc["entries"] if e["action"] == "BOUND"]
    assert sum(e["after"]["low"] for e in b) == pytest.approx(1.38278)
    assert sum(e["after"]["high"] for e in b) == pytest.approx(2.23125)


def test_expected_totals_by_hand(doc):
    t = doc["expect_totals"]["STR.CONC.COLUMN|m3"]
    assert t["held_low"] == pytest.approx(10.26435 + 0.0257 + 1.38278)
    assert t["held_high"] == pytest.approx(13.27025 + 2.23125)
    assert (t["bounded_lines"], t["blocked_lines"], t["lines"], t["released"]) == (27, 2, 59, 19.7765)


def test_relabel_and_not_wired(doc):
    r = {e["line_id"]: e for e in doc["entries"]}[T.SLAB]
    assert r["label"]["from"] == "BEAM_STRIP" and r["label"]["to"] == "GROUND_SLAB"
    assert r["expect"]["value"] == 0.114 and r["expect"]["class"] == "RELEASED"
    assert any("0.133640" in x["what"] for x in doc["not_wired"])


def test_joint_only_to_supports(doc):
    for e in doc["entries"]:
        d = (e.get("height") or {}).get("datum_lo") or {}
        if d.get("kind") == "BEAM_JOINT":
            assert d["supports"] == ["412", "415"] and e["member_mark"] in d["supports"]


def test_tampered_pin_refused(monkeypatch):
    p = dict(T.PINS)
    p[T.T689] = "0" * 64
    monkeypatch.setattr(T, "PINS", p)
    with pytest.raises(SystemExit, match="edited file"):
        T.build()
