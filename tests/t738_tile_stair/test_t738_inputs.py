"""T-738 development villa (merged ledgers only, no drawing): the entries rebuild equal to the committed
out/T738_ENTRIES.json; the T-730 H3 / H3S rows are wired once each (87 entries + 7 statements = 94); every figure is the
merged ledger's and re-derives by hand from its printed basis (riser n x width x (rise / count - t), pitch goings x
hypot(going, riser), tile run x height less openings, T-718 diameter ceilings); duplicate readings name a live carrier of
the same code; ORR-007 figures stay beside; the module accepts the inputs on the V3.0.77 index projection."""
from __future__ import annotations

import json
import math
import sys
from collections import Counter
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
for p in (ROOT, ROOT / "research" / "agents_t738"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

import t738_inputs as L  # noqa: E402
from engine.source import arch_v3078 as A  # noqa: E402

DOC = L.build()
E = DOC["entries"]
BY = {e.get("line_id") or e["add_key"]: e for e in E}


def test_rebuild_equal_to_committed():
    assert L.OUT.read_text(encoding="utf-8") == json.dumps(DOC, ensure_ascii=False, indent=1, sort_keys=True) + "\n"


def test_every_map_row_once():
    assert len(E) + len(DOC["statements"]) == L.ROWS_N == 94
    c = Counter(f"{e['piece']}:{e['action']}" for e in E)
    assert c == {"TILE_BOUND:BOUND": 2, "STAIR_WIRE:POINT": 15, "STAIR_WIRE:BOUND": 8, "STAIR_WIRE:EXCLUDE": 20,
                 "STAIR_WIRE:AT_LEAST": 3, "STAIR_WIRE:AT_MOST": 8, "STAIR_WIRE:CONDITIONAL": 27,
                 "STAIR_WIRE:NAMED": 3, "STAIR_WIRE:ADD_POINT": 1}
    st = Counter((s["map_action"], s["live"]) for s in DOC["statements"])
    assert st == {("KEEP", "STATEMENT"): 1, ("BESIDE", "SUPERSEDED"): 4, ("BESIDE", "DUPLICATE"): 2}


def _riser(n, rise, count, w=1.15, t=0.030):
    return round(n * w * (rise / count - t), 6)


def _pitch(n, rise, count, g=0.300):
    return round(n * math.hypot(g, rise / count), 6)


HAND = {  # line id prefix -> hand figure from the ledger's printed basis
    "L-0f060e99": _riser(12, 4.20, 25), "L-12f56cbf": _riser(12, 4.20, 25), "L-07e0855f": _riser(12, 4.50, 27),
    "L-ecc450d6": _riser(10, 4.50, 27), "L-8938aa3b": _riser(4, 0.70, 4), "L-099fe9fc": _riser(11, 4.50, 28),
    "L-16e0c668": _riser(5, 4.50, 28), "L-a08d67ca": _pitch(11, 4.20, 25), "L-48bb13e2": _pitch(11, 4.20, 25),
    "L-54eb280b": _pitch(11, 4.50, 27), "L-a1a0ab49": _pitch(9, 4.50, 27), "L-cccf54f7": _pitch(3, 0.70, 4),
    "L-509c6af3": _pitch(10, 4.50, 28), "L-406aae9a": _pitch(4, 4.50, 28), "L-b4660de0": round(1.150 * 1.150, 6),
}


def test_points_by_hand():
    pts = {k: e for k, e in BY.items() if e["action"] == "POINT"}
    assert len(pts) == len(HAND) == 15
    for k, e in pts.items():
        assert abs(e["value"] - HAND[k[:10]]) <= 1e-6, (k, e["value"], HAND[k[:10]])
    assert abs(BY["MS2-TR-closing-riser"]["value"] - _riser(1, 4.20, 25)) <= 1e-6       # 0.1587


def test_bounds_by_hand():
    d = math.hypot(1.150, 1.150)                                  # 1.626346: a winder front inside the 1.150 square
    want = {"L-1341e041": (6.2 * 2.2 - 2.24, 6.2 * 4.35 - 1.76), "L-de4088e7": (4.9 * 2.2 - 3.74, 4.9 * 4.35 - 1.76),
            "L-820baecf": (_riser(5, 4.50, 27), 5 * d * (4.50 / 27 - 0.030)), "L-e085c168": (5 * 1.150, 5 * d),
            "L-913cda8e": (13.798023 * (4.50 / 28 - 0.030), 16.304073 * (4.50 / 28 - 0.030)),
            "L-95b9555d": (13.800, 16.521440),
            "L-5f0bd2b4": (1.15, 1.15 + 5 * 4.50 / 27), "L-5bc4cea3": (1.20, 1.20 + 5 * 4.50 / 27)}
    sloped = {"L-28c33cd0": ("L-5f0bd2b4", 1.15), "L-2fae5d35": ("L-5bc4cea3", 1.20)}   # R-T715-4 corner: low = plan,
    for k, (zz, plan) in sloped.items():                                                # sloped high below zigzag high
        e, z = next(v for kk, v in BY.items() if kk.startswith(k)), next(v for kk, v in BY.items() if kk.startswith(zz))
        assert e["low"] == plan and plan < e["high"] < z["high"]
        want[k] = (e["low"], e["high"])
    bs = {k[:10]: e for k, e in BY.items() if e["action"] == "BOUND"}
    assert sorted(bs) == sorted(want)
    for k, (lo, hi) in want.items():
        assert abs(bs[k]["low"] - lo) <= 2e-6 and abs(bs[k]["high"] - hi) <= 2e-6, (k, bs[k]["low"], bs[k]["high"])


def test_t718_supersedes_t715():
    for k in ("L-820baecf", "L-e085c168", "L-913cda8e", "L-95b9555d"):
        e = next(v for kk, v in BY.items() if kk.startswith(k))
        assert e["source_tasks"][0] == "T-718" and e["supersedes"]["task"] == "T-715"
        assert e["low"] >= float(e["supersedes"]["low"]) - 1e-9          # the floor kept (rounding 1.803386 -> 1.803598)


def test_exclusions_name_live_carriers():
    ix = {ln["line_id"]: ln for ln in L.load(L.INDEX)["lines"]}
    ex = [e for e in E if e["action"] == "EXCLUDE"]
    excluded = {e["line_id"] for e in ex}
    dup = [e for e in ex if e["cause"] == "DUPLICATE_READING"]
    assert len(dup) == 15 and len(ex) - len(dup) == 5         # landing + 4 skirting stretches: no element
    for e in dup:
        c = ix[e["carrier_line_id"]]
        assert c["item_code"] == e["expect"]["item_code"] and c["class"] != "EXCLUDED"
        assert c["line_id"] not in excluded and c["element_id"] == e["carrier_element_id"]
    for k in ("L-6cf11c2d", "L-ea55ed31"):                         # T-733 closed the pending: ENGINE_RIGHT, then R-T715-3
        e = next(v for kk, v in BY.items() if kk.startswith(k))
        assert "T-733" in e["source_tasks"] and e["action"] == "EXCLUDE"


def test_orr007_conditional_pairs():
    cond = [e for e in E if e["action"] == "CONDITIONAL"]
    assert len(cond) == 27 and all(e["ruling"] == "ORR-007" for e in cond)
    paired = [e for e in cond if e["sibling_line_id"]]
    assert len(paired) == 27                                        # 13 pieces x 2 + MS2-TR zigzag (its sloped AT_LEAST)
    for e in paired:
        s = BY[e["sibling_line_id"]]
        assert s["expect"]["element_id"] == e["expect"]["element_id"] and \
            s["expect"]["item_code"] != e["expect"]["item_code"]
    sl = [e["value"] for e in cond if e["expect"]["item_code"].endswith("SLOPED")]
    zz = [e["value"] for e in cond if e["expect"]["item_code"].endswith("ZIGZAG")]
    assert (len(sl), len(zz)) == (13, 14)
    # T-715 form pair over the 13 walled pieces: sloped 17.009047, zigzag 23.300476 (6-dp line rounding <= 2e-6 x 13);
    # the 14th zigzag figure is the MS2-TR closing step 0.168 (sloped undefined over a zero run: AT_LEAST, not a form)
    assert abs(sum(sl) - 17.009047) <= 13 * 1e-6 and abs(sum(zz) - 0.168 - 23.300476) <= 13 * 1e-6


def test_module_accepts_inputs():
    d = A.load_inputs(L.inputs())
    assert len(d["_entries"]) == 87


def test_no_verified_and_never_zero():
    for e in E:
        assert e["status"] in A.STATUSES
        for k in ("value", "low", "high"):
            if e.get(k) is not None:
                assert e[k] > 0


def test_stale_pin_refused(monkeypatch):
    monkeypatch.setitem(L.PINS, L.T715, "0000000000000000")
    with pytest.raises(L.InputsError, match="stale"):
        L.build()
