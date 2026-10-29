"""T-315: pins of the development villa's V3.0.21 inputs (research/agents_t315/t315_inputs.py), read from the merged
T-312 face ledger only. The Alsenan lines themselves are private (Drive); these tests pin the inputs (the hand
arithmetic of the records, from the merged values) and an edited ledger stops the build."""
from __future__ import annotations

import csv
import hashlib
import shutil
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "research" / "agents_t315"))

import t315_inputs as L  # noqa: E402
from engine.source import arch_v3021 as A  # noqa: E402

PID = "pins"


@pytest.fixture(scope="module")
def doc():
    return A.load_inputs(L.build(PID))


def _by(doc):
    return {r["room"]: r for r in doc["records"]}


def test_family_pins_fill_held_add(doc):
    assert doc["declared"] == {"FILL": {"lines": 11, "m2": 307.9616}, "HELD": {"lines": 6, "m2": 0.0},
                               "ADD": {"lines": 1, "m2": 32.3422}}
    kinds = sorted((r["kind"], r["room"]) for r in doc["records"])
    assert [k for k, _ in kinds].count("FILL") == 11 and [k for k, _ in kinds].count("HELD") == 6
    assert sorted(r for k, r in kinds if k == "HELD") == ["GF-02", "GF-03", "GF-05", "GF-06", "GF-10", "GF-11"]
    assert sum(len(r.get("faces") or ()) for r in doc["records"]) == 67 + 6       # 11 lines + the pantry
    # owner method total, determinate: 340.3038 m2 on 12 rooms (T-312 section 4)
    assert sum(r.get("value") or 0 for r in doc["records"]) == pytest.approx(340.3038, abs=1e-4)


def test_line_ids_are_the_t312_summary_ids(doc):
    rows = list(csv.DictReader(L.LINES.open(encoding="utf-8")))
    want = {r["rooms"]: r["line_id"] for r in rows if r["line_id"] != "NO_LINE"}
    got = {r["room"]: r["line_id"] for r in doc["records"] if r["kind"] != "ADD"}
    assert got == want and len(got) == 17


def test_1f12_by_hand(doc):
    r = _by(doc)["1F-12"]
    assert r["kind"] == "FILL" and r["evidence_status"] == A.OA and "Q-48 A" in r["assumption"]
    ops = sorted((o["id"], o["m2"]) for f in r["faces"] for o in f["openings"])
    assert ops == [("D-1F-10", 1.76), ("W18", 1.08)]
    run = sum(f["length_m"] for f in r["faces"])
    assert run == pytest.approx(8.70, abs=1e-9) and {f["height_m"] for f in r["faces"]} == {3.35}
    assert 8.70 * 3.35 - 0.80 * 2.20 - 0.50 * (3.00 - 0.84) == pytest.approx(r["value"], abs=1e-4)   # 26.305
    assert "split" in r["note"]


def test_pantry_new_line_by_hand(doc):
    r = _by(doc)["GF-07"]
    assert r["kind"] == "ADD" and r["engine_room"] == "GF-RC06FED" and r["floor"] == "GF" and "line_id" not in r
    assert len(r["faces"]) == 6 and {f["height_m"] for f in r["faces"]} == {3.65}
    run = sum(f["length_m"] for f in r["faces"])
    assert run == pytest.approx(10.491, abs=1e-9) and r["contour"]["open_m"] == pytest.approx(4.49)
    assert sorted((o["id"], o["m2"]) for f in r["faces"] for o in f["openings"]) == [
        ("D-GF-06", 2.2), ("W09", 2.25), ("W10", 1.5)]
    assert run * 3.65 - 2.20 - 1.50 - 2.25 == pytest.approx(32.3422, abs=1e-4)
    assert "UP-PANTRY" in r["assumption"]


def test_gf16_closure_correction_is_named(doc):
    r = _by(doc)["GF-16"]
    corr = [f for f in r["faces"] if f.get("correction")]
    assert len(corr) == 1 and corr[0]["length_m"] == pytest.approx(-0.524) and "T-074" in corr[0]["basis"]
    assert sum(f["length_m"] for f in r["faces"]) == pytest.approx(r["contour"]["contour_m"] - r["contour"]["open_m"])


def test_held_lines_carry_no_figure(doc):
    for r in doc["records"]:
        if r["kind"] == "HELD":
            assert r.get("value") is None and not r.get("faces") and r["reasons"]


def test_source_sha_is_the_merged_file(doc):
    s = doc["sources"][0]
    assert s["task"] == "T-312" and s["merge_commit"].startswith("8943b5ed")
    assert s["sha256"] == hashlib.sha256(L.FACES.read_bytes()).hexdigest()


def test_edited_ledger_stops_the_build(tmp_path, monkeypatch):
    d = tmp_path / "t312"
    shutil.copytree(L.T312, d)
    p = d / "FACE_LEDGER_T312.csv"
    rows = list(csv.DictReader(p.open(encoding="utf-8", newline="")))
    for r in rows:
        if r["face_id"] == "1F-12|1F-W13":
            r["owner_net_m2"] = "7.6375"                 # +0.10 m2 on one face
    with p.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    monkeypatch.setattr(L, "FACES", p)
    with pytest.raises((SystemExit, A.InputsError)):
        A.load_inputs(L.build(PID))
