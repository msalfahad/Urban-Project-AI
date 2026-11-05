"""T-519 on the training villa: the 60 masonry openings of the merged T-453 r2 ledger, the 16 REQUIRED lintels' jamb
masonry from the merged T-516 census (sha-pinned; no private file is needed).

System (hand): the structural set prints a LINTEL SCHEDULE (ST7757 p.13, L1-L5, 0-750 cm) for 'the block wall' (note
'B-WIDTH OF THE BLOCK WALL', no block type excluded) and a LINTEL DETAIL 'MIN.40cm'. Every one of the 16 widths
(0.50 .. 2.45 m) is inside a band -> PROJECT_RC governs all 16 (level 1 over the company precast rule). Stock length:
NOT_APPLICABLE (cast to length).
RC pieces (hand, from T-516): BEARING_OK 6 (D-1F-02, D-1F-08, D-2F-01, D-GF-13, W14, W15) -> 6 nr PRODUCED; 10 with a
deficit end -> count HELD by name. W14 L in [2.45 + 0.80 = 3.25, 2.45 + 0.618 + 1.032 = 4.10].
Precast BESIDE, white walls only (Q-60), project bearing 0.40 (the detail's scope is every block wall):
  D-2F-01 w 1.00: 1.80 -> 2.50; piers 0.615 / >= 3.0 -> FITS (each >= 0.40; 3.615 >= 1.50)
  D-GF-06 w 1.00: 1.80 -> 2.50; END pier 0.140 < 0.40 -> DOES_NOT_FIT
  W14     w 2.45: 3.25 -> 4.00; 0.618 / 1.032, 1.650 >= 1.55 -> FITS
  W15     w 1.55: 2.35 -> 2.50; END pier 0.493 shared with W16 (HELD): < 2 x 0.40 -> CONDITIONAL, HELD by name
  W18     w 0.50: 1.30 -> 1.50; START 0.000 (jamb on the column face) -> DOES_NOT_FIT
Reconciliation: T-453 beside pieces 2.50 / 2.50 / 4.00 / 2.50 / 1.50 = this record 5 / 5 (same 0.40 basis; T-453 did no
fit test). T-516 beside (company 0.15 on all 16): 11 black-wall pieces are not applicable (Q-60); on the 5 white
D-2F-01 1.50 -> 2.50, D-GF-06 1.50 -> 2.50, W14 3.00 -> 4.00, W18 1.20 -> 1.50 (bearing basis), W15 2.50 same.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "research" / "agents_t519"))

import t519_lintel_pieces as P  # noqa: E402

WHITE = ["D-2F-01", "D-GF-06", "W14", "W15", "W18"]


@pytest.fixture(scope="module")
def doc():
    return P.build()


def by(doc):
    return {r["opening_id"]: r for r in doc["rows"]}


def test_system_all_16_project_rc(doc):
    s = doc["summary"]
    assert s["openings"] == 60 and s["required"] == 16
    assert s["system_count"] == {"PROJECT_RC": 16, "OWNER_PRECAST": 0, "HELD": 0}
    t453 = {r["opening_id"]: r["schedule_row"] for r in json.loads(P.T453.read_text())["lintels"]}
    for r in doc["rows"]:                     # the same printed band as the merged T-453 for all 60
        assert r["schedule_row"] == t453[r["opening_id"]], r["opening_id"]
    assert by(doc)["W14"]["schedule_row"] == "L3" and by(doc)["W15"]["schedule_row"] == "L2"


def test_rc_pieces(doc):
    s = doc["summary"]
    assert s["rc_produced_nr"] == 6
    assert sorted(s["rc_produced"]) == ["D-1F-02", "D-1F-08", "D-2F-01", "D-GF-13", "W14", "W15"]
    assert sorted(s["rc_held"]) == ["D-1F-03", "D-1F-04", "D-1F-07", "D-1F-10", "D-2F-03", "D-GF-06", "D-GF-10",
                                    "D-GF-11", "D-GF-12", "W18"]
    w14 = by(doc)["W14"]["rc"]
    assert (w14["length_lo_m"], w14["length_hi_m"]) == (3.25, 4.1)
    assert by(doc)["D-2F-01"]["rc"]["length_hi_m"] is None          # pier >= 3.0 m: ceiling HELD
    assert by(doc)["D-GF-12"]["rc"]["length_hi_m"] is None          # oblique junction end HELD


def test_rc_length_ceilings_equal_t516(doc):
    t516 = {r["opening_id"]: r for r in json.loads(P.T516_OUT.read_text())["rows"]}
    for r in doc["rows"]:
        if r["decision"] == "REQUIRED":
            assert r["rc"]["length_hi_m"] == t516[r["opening_id"]]["length_hi_m"], r["opening_id"]


def test_precast_beside_white_only(doc):
    b = by(doc)
    for r in doc["rows"]:
        if r["decision"] == "REQUIRED" and r["block_type"] == "BLACK":
            assert r["precast_beside"]["state"] == "NOT_APPLICABLE"
    got = {k: (b[k]["precast_beside"]["piece_m"], b[k]["precast_beside"]["fit"]) for k in WHITE}
    assert got == {"D-2F-01": (2.5, P.FITS), "D-GF-06": (2.5, P.NO_FIT), "W14": (4.0, P.FITS),
                   "W15": (2.5, P.CONDITIONAL), "W18": (1.5, P.NO_FIT)}
    by_len = doc["summary"]["precast_beside_by_length"]
    assert by_len["2.50"] == {"produced_nr": 1, "produced": ["D-2F-01"], "held": ["W15"], "flagged": ["D-GF-06"]}
    assert by_len["4.00"]["produced"] == ["W14"] and by_len["1.50"]["flagged"] == ["W18"]
    assert by_len["1.20"]["produced_nr"] == 0 and not by_len["1.20"]["held"] and not by_len["3.00"]["flagged"]


def test_no_governing_precast_and_held_named(doc):
    s = doc["summary"]
    assert all(v["produced_nr"] == 0 and not v["held"] and not v["flagged"]
               for v in s["precast_governing_by_length"].values())
    assert len(s["not_required_held_by_name"]) == 44 and "W13" in s["not_required_held_by_name"]
    assert s["label"].startswith("PARTIAL")
    w13 = by(doc)["W13"]
    assert w13["state"] == P.HELD and w13["system"] == P.PROJECT_RC and w13["schedule_row"] == "L2"


def test_reconciliation_t453_t516(doc):
    rec = {r["opening_id"]: r for r in doc["reconciliation"]}
    assert len(rec) == 16
    for k in WHITE:
        assert rec[k]["t453_precast_beside_m"] == rec[k]["t519_precast_beside_m"]
    assert {k: rec[k]["t516_precast_beside_m"] for k in WHITE} == \
        {"D-2F-01": 1.5, "D-GF-06": 1.5, "W14": 3.0, "W15": 2.5, "W18": 1.2}
    assert sum(1 for r in rec.values() if r["block_type"] == "BLACK") == 11
    assert all("Q-60" in r["cause"] for r in rec.values() if r["block_type"] == "BLACK")


def test_edited_input_refused(tmp_path, monkeypatch):
    p = tmp_path / "j.json"
    p.write_text(P.T516_OUT.read_text(encoding="utf-8").replace("0.618", "0.718"), encoding="utf-8")
    monkeypatch.setitem(P.PINS, p, P.PINS[P.T516_OUT])
    monkeypatch.setattr(P, "T516_OUT", p)
    with pytest.raises(P.LintelPiecesError):
        P.build()
