"""T-736 inputs on the development villa (merged files only; no drawing): the entries rebuild equal to the committed
out/T736_ENTRIES.json, every input is the pinned one, the 73 interior arrises map once each onto 14 hosts, the bead
projection re-adds to the T-728 ledger by hand (294.0828 .. 294.4828 m.l = 9 BOUNDED 165.45 .. 165.65 + 5 AT_LEAST lows
128.6328), the ceiling exclusion names its released owner, and the downgrade entry is the Checker record's band.
Adverse on real rows: a stale host range, a moved arris, a record band changed."""
from __future__ import annotations

import copy
import json
import sys
from decimal import Decimal
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "research" / "agents_t736"))

import t736_inputs as L  # noqa: E402
from engine.source import arch_v3076 as A  # noqa: E402

DOC = json.loads((ROOT / "research/agents_t736/out/T736_ENTRIES.json").read_text(encoding="utf-8"))


def test_rebuild_equal_and_pins():
    assert L.text(L.build()) == (ROOT / "research/agents_t736/out/T736_ENTRIES.json").read_text(encoding="utf-8")
    for p, want in L.PINS.items():
        if want:
            assert L.sha(p).startswith(want)


def test_projection_by_hand():
    pr = DOC["bead_projection"]
    assert (pr["lines"], pr["bounded"], pr["at_least"], pr["arrises"], pr["arrises_blank"]) == (14, 9, 5, 73, 6)
    assert Decimal(pr["rows_low"]) == Decimal("294.0828") and Decimal(pr["rows_high"]) == Decimal("294.4828")
    assert Decimal(pr["low"]) + Decimal(pr["at_least_sum"]) == Decimal("294.0828")
    assert (Decimal(pr["low"]), Decimal(pr["high"])) == (Decimal("165.45"), Decimal("165.65"))
    # the one ranged arris (GF-08 0.20 m spread) sits on an AT_LEAST line: its high is open, not summed
    assert Decimal(pr["rows_high"]) - Decimal(pr["rows_low"]) == Decimal("0.4")


def test_entries_validate_and_arrises_once():
    d = A.load_inputs(DOC["inputs"], "development-villa-t131")
    beads = [e for e in d["_entries"] if e["piece"] == A.P_BEAD]
    assert len(beads) == 14 and len({e["host_line_id"] for e in beads}) == 14
    ids = [a["edge_id"] for e in beads for a in e["arrises"]]
    assert len(ids) == 73 == len(set(ids))
    blank = sorted(x for e in beads for x in e["_blank"])
    assert blank == sorted(["A-1F-01#1F-10", "A-GF-01#GF-01", "OPEN#GF-08-OP003", "OPEN#ST-GF-OP020", "W03#IN",
                            "W17#IN"])
    moved = [e for e in DOC["inputs"]["entries"] if e.get("host_change_since_t728")]
    assert sorted(e["host_line_id"][:10] for e in moved) == ["L-1ddc23d5", "L-b1529955"]


def test_ceiling_and_record():
    ents = {e["piece"]: e for e in DOC["inputs"]["entries"] if e["piece"] != A.P_BEAD}
    c = ents[A.P_CEIL]
    assert c["line_id"] == "L-35341ff2e6a848b9436b" and c["owner_line_id"] == "L-43bf1f869e1588f1d3bd"
    assert c["owner_expect"]["class"] == "RELEASED" and c["owner_expect"]["measured_net"] == 51.0496
    g = ents[A.P_DG]
    assert g["line_id"] == "L-636fd3ff1784a12e653b" and (g["low"], g["high"]) == (115.656474, 115.813974)
    assert g["record"]["downgrade_id"] == "DG-98cbadebaecc5ede" and g["record"]["engine_qty"] == 115.832
    assert g["expect"]["measured_net"] == 115.832


def test_adverse_real_rows():
    for mut, msg in ((lambda e: e[0]["expect"].update(high=99.0), None),
                     (lambda e: e[1]["arrises"].append(copy.deepcopy(e[0]["arrises"][0])), "two hosts"),
                     (lambda e: e[-1].update(high=115.832), "not the record's")):
        doc = copy.deepcopy(DOC["inputs"])
        mut(doc["entries"])
        if msg is None:          # a stale host range passes the loader and stops at binding (needs the lines)
            A.load_inputs(doc, "development-villa-t131")
            continue
        with pytest.raises(A.InputsError, match=msg):
            A.load_inputs(doc, "development-villa-t131")


def test_line_index_v3_0_76_against_v3_0_75():
    """the committed census index of the run of record: only the 2 named lines changed, 14 bead lines added; held
    stays held (no bead released, none 0), every other line's index entry equal to V3.0.75's."""
    i75 = {x["line_id"]: x for x in json.loads((ROOT / L.INDEX).read_text(encoding="utf-8"))["lines"]}
    i76 = {x["line_id"]: x for x in json.loads((ROOT / "research/agents_t736/out/LINE_INDEX_V3_0_76.json").read_text(
        encoding="utf-8"))["lines"]}
    added = sorted(set(i76) - set(i75))
    assert len(added) == 14 and not set(i75) - set(i76)
    beads = [i76[k] for k in added]
    assert all(b["item_code"] == "FIN.PLASTER.BEAD" and b["unit"] == "lm" and b["class"] == "HELD" and
               b["measured_net"] is None for b in beads)
    bounded = [b for b in beads if b["held_low"] is not None]
    assert len(bounded) == 9 and all(b["held_low"] > 0 for b in bounded)
    assert round(sum(b["held_low"] for b in bounded), 6) == 165.45
    assert round(sum(b["held_high"] for b in bounded), 6) == 165.65
    changed = sorted(k for k in i75 if i75[k] != i76[k])
    assert changed == ["L-35341ff2e6a848b9436b", "L-636fd3ff1784a12e653b"]
    assert i76["L-35341ff2e6a848b9436b"]["class"] == "EXCLUDED"
    w = i76["L-636fd3ff1784a12e653b"]
    assert (w["class"], w["held_low"], w["held_high"], w["measured_net"]) == ("HELD", 115.656474, 115.813974, None)
