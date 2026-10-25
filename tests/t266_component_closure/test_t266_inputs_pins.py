"""T-266: the development villa's V3.0.18 inputs, pinned to the merged ledgers (no drawing needed): the stair parts at
the T-258 r2 REVISION (2.864463 m3, never the r1 2.915089), MS2-LD 0.4696 DRAWING-CONFIRMED, ST-03 HELD on the T-289
row, the 1F landing marble 4.9225 m2 (Q-66 B) and the pantry piece 1.100 m2 (Q-37 A). Adverse: an edited ledger, the r1
figure, a closable piece named held, a mixed-status part stop the build."""
from __future__ import annotations

import csv
import io
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "research" / "agents_t266"))

import t266_inputs as T  # noqa: E402
from engine.source import arch_v3018 as A  # noqa: E402


@pytest.fixture(scope="module")
def doc():
    return A.load_inputs(T.build())


def _by(doc):
    return {(r["kind"], r.get("id") or r["line_id"]): r for r in doc["records"]}


def test_records_and_r2_revision(doc):
    kinds = [r["kind"] for r in doc["records"]]
    assert kinds == ["SPLIT", "SPLIT", "SPLIT", "REBASE", "HOLD", "MATERIAL", "PIECE_LINE"]
    parts = [p for r in doc["records"] if r["kind"] == "SPLIT" for p in r["parts"]]
    assert round(sum(p["value"] for p in parts), 6) == 2.864463          # r2, not the r1 2.915089
    by = {p["status"]: p["value"] for p in parts}
    assert by == {"VERIFIED": 1.227952, A.OA: 1.536225, "DRAWING-CONFIRMED": 0.100286}
    b = _by(doc)
    reb = b[("REBASE", "L-2416e65f053a14199cfc")]
    assert reb["value"] == 0.4696 and reb["status"] == "DRAWING-CONFIRMED"
    st3 = b[("HOLD", "L-061e18cf35a4b6b33d68")]
    assert st3["before"] == {"evidence_state": "PROVISIONAL", "measured_net": 0.948267}
    assert st3["cited_from"].startswith("T-289") and "0.355017" in st3["closable_named"]


def test_material_and_piece(doc):
    b = _by(doc)
    m = b[("MATERIAL", "1F-LANDING-MARBLE")]
    assert (m["item_code"], m["value"], m["status"], m["material_of"]) == (
        "FIN.MARBLE.LANDING", 4.9225, A.OA, "L-428b44ee2f5f1c1c118f")
    assert "Q-66 B" in m["owner_source"]
    p = b[("PIECE_LINE", "GF-PANTRY-DOORWAY-ZONE")]
    assert (p["value"], p["status"], p["piece"]["id"], p["piece"]["status"]) == (
        1.1, A.OA, "SITE-0a31aaa10796d33a", "DRAWING-CONFIRMED")
    assert "Q-37 A" in p["owner_source"]


def test_sources_hash_the_committed_ledgers(doc):
    for s in doc["sources"]:
        if s["task"] == "T-278":
            continue
        assert s["sha256"] == T._sha(ROOT / s["file"])


def test_adverse_r1_figure_refused(monkeypatch):
    monkeypatch.setattr(T, "DECLARED_R2", 2.915089)
    with pytest.raises(SystemExit, match="r2 revision"):
        T.stair_records()


def _edited_t258(tmp_path, pid, col, val):
    rows = list(csv.DictReader(io.StringIO(T.T258.read_text(encoding="utf-8"))))
    for r in rows:
        if r["id"] == pid:
            r[col] = val
    p = tmp_path / "LEDGER_T258.csv"
    with open(p, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    return p


def test_adverse_edited_piece_value_stops(tmp_path, monkeypatch):
    monkeypatch.setattr(T, "T258", _edited_t258(tmp_path, "ST02-RS-LD", "value_m3", "0.225600"))   # the pre-r2 value
    with pytest.raises(SystemExit, match="T-290 closable"):
        T.stair_records()


def test_adverse_mixed_status_part_stops(tmp_path, monkeypatch):
    monkeypatch.setattr(T, "T258", _edited_t258(tmp_path, "ST01-MS1-U", "evidence", "DRAWING-CONFIRMED"))
    with pytest.raises(SystemExit, match="mixed statuses"):
        T.stair_records()


def test_adverse_closable_piece_named_held(monkeypatch):
    bad = tuple((lid, ph, part, cl, held + (cl[0],)) for lid, ph, part, cl, held in T.SPLITS)
    monkeypatch.setattr(T, "SPLITS", bad)
    with pytest.raises(SystemExit, match="cannot be named held"):
        T.stair_records()
