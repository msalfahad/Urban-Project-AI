"""T-687 inputs builder on the committed, Checker-merged ledgers (no drawing read): counts, hand figures of the lines
the Checker re-measured, code totals by hand, every entry accepted by the V3.0.69 loader, a tampered pin refused."""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t687"))

import t687_inputs as T  # noqa: E402
from engine.source import arch_v3069 as M  # noqa: E402


@pytest.fixture(scope="module")
def doc():
    return T.build()


def test_counts_and_loader(doc):
    acts = {}
    for e in doc["restate"]:
        acts[e["action"]] = acts.get(e["action"], 0) + 1
    assert acts == {"BOUND": 14, "VALUE": 1, "CAUSE": 1}
    assert len(doc["bands"]) == 18
    assert sum(1 for b in doc["bands"] if b["status"]["status"] == M.OA) == 4
    d = M.load_inputs(doc)
    assert len(d["_restate"]) == 16 and len(d["_bands"]) == 18


def test_hand_figures(doc):
    r = {e["line_id"]: e for e in doc["restate"]}
    assert r["L-418121a4b223cb4e8646"]["after"] == {"low": 47.342, "high": 48.772}       # 2F shaft plaster (T-680)
    assert r["L-5a7a5c6f070ec7142ca5"]["after"] == {"low": 45.392, "high": 46.822}       # 2F shaft paint
    k = r["L-595181aa140e7efb2ac7"]["after"]                                             # GF-06 kitchen (T-686)
    assert abs(k["low"] - (14.5 * 2.494 - 1.501 * 1.494 - 2.20)) < 1e-6
    assert abs(k["high"] - (14.5 * 3.25 - 1.501 * 1.50 - 2.20)) < 1e-6
    assert r[T.OP009]["after"] == {"value": 2 * 0.20 * 2.20 + 0.20 * 1.00} or \
        abs(r[T.OP009]["after"]["value"] - 1.08) < 1e-9
    b = {x["engine_room"]: x for x in doc["bands"]}
    assert abs(b["1F-R26FA0D"]["low"] - 16.94 * (3.99 - 3.35)) < 1e-6                   # 1F-07 laundry 10.8416
    assert (b["GF-RA3AD49"]["low"], b["GF-RA3AD49"]["high"]) == (8.545994, 8.555)        # GF-06 band
    assert abs(sum(x["low"] for x in doc["bands"]) - 78.83192) < 1e-6
    assert abs(sum(x["high"] for x in doc["bands"]) - 123.02493) < 1e-6


def test_expected_totals_by_hand(doc):
    p, q = doc["expect_totals"]["FIN.PLASTER|m2"], doc["expect_totals"]["FIN.PAINT|m2"]
    # T-686 after_round3 (holds T-680 and OP-009 at 1.08) - OP-009 moved to a value + the 14 held bands
    held = [b for b in doc["bands"] if b["status"]["status"] == "HELD"]
    assert abs(p["held_low"] - (1078.344516 - 1.08 + sum(b["low"] for b in held))) < 1e-5
    assert abs(p["held_high"] - (1202.87991 - 1.08 + sum(b["high"] for b in held))) < 1e-5
    assert p["blocked_lines"] == 3 and p["bounded_lines"] == 20 + 14
    assert (q["held_low"], q["held_high"], q["blocked_lines"], q["bounded_lines"]) == (601.645338, 682.3313, 0, 10)


def test_tampered_pin_refused(monkeypatch):
    f = dict(T.FILES)
    f["T-690"] = (f["T-690"][0], "0" * 64) + f["T-690"][2:]
    monkeypatch.setattr(T, "FILES", f)
    with pytest.raises(SystemExit, match="tampered"):
        T.band_entries()
