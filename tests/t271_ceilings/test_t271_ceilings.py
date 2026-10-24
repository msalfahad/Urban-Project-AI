"""T-271 ceilings r2 on hand-calculated fixtures that are NOT the Alsenan villa (any villa), plus the Alsenan ledger
guard (the committed CSVs are rebuilt from the committed input, byte for byte).

Villa Z (fixture, metres; every geometric fixture is also mirrored, rotated 37 deg, translated and given in mm x 0.001):
HALL 6.00 x 4.00 = 24.00 crossed (along y, x 2.85 .. 3.15) by beam BX 0.30 x 0.90, ledger r2 CALCULATED:
    piece 0.30 x 4.00 = 1.20; free edge 2 x 4.00 = 8.00 m (its ends lie on the walls)
    owner face 8.00 x (0.90 - 0.60) = 2.40 m2; drawing-derived candidate 8.00 x (0.90 - 0.16) = 5.92 m2 (HELD, not in a total)
    beam BC 0.25 wide along the north wall (x 0 .. 2.00, y 3.75 .. 4.00), r2 CONFLICT, D 0.75:
        free edge 2.00 + 0.25 = 2.25 m HELD; owner candidate 2.25 x 0.15 = 0.3375 m2 named, never in a total
    horizontal ceiling 24.00; paint (owner) 24.00 + 2.40 = 26.40
BATH 2.50 x 2.00 = 5.00 (WET) crossed by a shallow beam BS 0.20 x 0.40 along x: no owner face (D <= 0.60); candidate
    2 x 2.50 x (0.40 - 0.16) = 1.20 HELD; horizontal 5.00; board type HELD
LIVING 8.00 x 5.00 = 40.00 with a light-well VOID 3.00 x 2.00 = 6.00 inside (edge 10.00 m) and a STAIR strip
    1.00 x 1.50 = 1.50 above: horizontal 40.00 - 6.00 - 1.50 = 32.50; drop edge 10.00 m HELD (height)
DOME ROOM 5.00 x 5.00 = 25.00 with an open dome r 1.00 at its centre inside a ring face 3.00 x 3.00:
    open pi = 3.1416 HELD; horizontal 25.00 - pi = 21.8584; edge at the opening 2 pi = 6.2832 m HELD
STAIR / SHAFT piece: no decor ceiling row at all; the stair zone is a stair soffit (HELD)
Adverse: two opening faces adding up to more than the piece -> refused; a piece in mm -> refused; a CONFLICT beam never
gives an owner face; an unregistered piece >= 0.10 m2 is HELD edge, below it a junction (count only); no HELD row is 0."""

from __future__ import annotations

import csv
import json
import math
import subprocess
import sys
from pathlib import Path

import pytest
from shapely import affinity
from shapely.geometry import Point, box

ROOT = Path(__file__).resolve().parents[2]
MOD = ROOT / "research" / "agents_t271"
sys.path.insert(0, str(MOD))
import ceilings_r2 as CR  # noqa: E402

CALC = {"member": "BM-Z-1", "mark": "BX", "r2_status": "CALCULATED", "r2_depth": "0.9"}
CONF = {"member": "BM-Z-2", "mark": "BC", "r2_status": "CONFLICT", "r2_depth": "0.75"}
SHAL = {"member": "BM-Z-3", "mark": "BS", "r2_status": "CALCULATED", "r2_depth": "0.4"}


def _tf(kind):
    """geometry transform: identity, mirror, rotation 37 deg, translation (all about a fixed origin)."""
    def f(g):
        if kind == "mirror":
            return affinity.scale(g, -1, 1, origin=(0, 0))
        if kind == "rotate":
            return affinity.rotate(g, 37, origin=(0, 0))
        if kind == "shift":
            return affinity.translate(g, 1234.5, -987.6)
        if kind == "mm":   # given in millimetres, converted by the caller's 0.001 before the overlay
            return affinity.scale(affinity.scale(g, 1000, 1000, origin=(0, 0)), 0.001, 0.001, origin=(0, 0))
        return g
    return f


def _face(name, room, slab, domes=(), tf=_tf("id")):
    rec = CR.overlay(tf(room), [(i, c, tf(p), m) for i, c, p, m in slab], domes=[tf(d) for d in domes])
    rec.update({"face": name, "floor": "GF", "name": name})
    return rec


def hall(tf=_tf("id")):
    room = box(0, 0, 6, 4)
    slab = [("s1", "SLAB", box(0, 0, 6, 4), None),
            ("b1", "BEAM", box(2.85, -0.2, 3.15, 4.2), CALC),
            ("b2", "BEAM_OR_COLUMN", box(0, 3.75, 2.0, 4.2), CONF)]
    return _face("hall", room, slab, tf=tf)


def bath(tf=_tf("id")):
    return _face("bath", box(0, 0, 2.5, 2.0), [("s", "SLAB", box(0, 0, 2.5, 2), None),
                                                ("b", "BEAM", box(-0.1, 0.9, 2.6, 1.1), SHAL)], tf=tf)


def living(tf=_tf("id")):
    return _face("living", box(0, 0, 8, 5), [("s", "SLAB", box(0, 0, 8, 5), None),
                                             ("v", "VOID+STAIR", box(2, 1.5, 5, 3.5), None),
                                             ("t", "STAIR", box(6, 0, 7, 1.5), None)], tf=tf)


def dome_room(tf=_tf("id")):
    return _face("dome", box(0, 0, 5, 5), [("s", "SLAB", box(0, 0, 5, 5), None),
                                           ("d", "DOME_OPENING+RING", box(1, 1, 4, 4), None)],
                 domes=[Point(2.5, 2.5).buffer(1.0, 512)], tf=tf)


def q(rows, prefix):
    got = [r["QTY"] for r in rows if r["SURFACE"].startswith(prefix)]
    assert len(got) == 1, (prefix, got)
    return got[0]


TF = ["id", "mirror", "rotate", "shift", "mm"]


@pytest.mark.parametrize("k", TF)
def test_hall_crossing_beam_and_conflict_beam(k):
    rows, t = CR.ledger(hall(_tf(k)), "DRY", CR.ST_DC, "fixture")
    assert q(rows, "horizontal decor") == pytest.approx(24.0, abs=1e-4)
    assert q(rows, "bulkhead vertical faces, owner method, total") == pytest.approx(2.40, abs=1e-3)
    assert q(rows, "bulkhead vertical faces, drawing-derived") == pytest.approx(5.92, abs=1e-3)
    held = [r for r in rows if r["SURFACE"].startswith("bulkhead edges on")]
    assert len(held) == 1 and held[0]["UNIT"] == "m" and held[0]["QTY"] == pytest.approx(2.25, abs=1e-3)
    assert "0.3375" in held[0]["NOTE"]
    assert t["own_bulk_m2"] == pytest.approx(2.40, abs=1e-3)       # the conflict candidate is not in the total
    assert q(rows, "paintable gypsum") == pytest.approx(26.40, abs=1e-3)
    assert q(rows, "cove / cornice") == pytest.approx(20.0, abs=1e-3)


@pytest.mark.parametrize("k", TF)
def test_wet_room_shallow_beam(k):
    rows, t = CR.ledger(bath(_tf(k)), "WET", CR.ST_DC, "fixture")
    assert q(rows, "horizontal decor") == pytest.approx(5.0, abs=1e-4)
    assert not [r for r in rows if r["SURFACE"].startswith("bulkhead vertical face, owner")]
    assert q(rows, "bulkhead vertical faces, drawing-derived") == pytest.approx(1.20, abs=1e-3)
    board = [r for r in rows if r["SURFACE"].startswith("ceiling board type")]
    assert board and board[0]["STATUS"] == CR.ST_H and "5.0000" in board[0]["NOTE"]
    assert t["horiz_WET"] == pytest.approx(5.0, abs=1e-4)


@pytest.mark.parametrize("k", TF)
def test_void_and_stair_strip_deducted_once(k):
    rows, t = CR.ledger(living(_tf(k)), "DRY", CR.ST_DC, "fixture", closed=False)
    assert q(rows, "no ceiling here") == pytest.approx(6.0, abs=1e-4)
    assert q(rows, "stair soffit above") == pytest.approx(1.5, abs=1e-4)
    assert q(rows, "horizontal decor") == pytest.approx(32.5, abs=1e-4)
    assert q(rows, "ceiling edge at an opening") == pytest.approx(10.0, abs=1e-3)
    assert q(rows, "cove / cornice") == ""          # open zone: no run invented, HELD with the reason
    assert t["deduct_no_ceiling"] + t["deduct_stair"] + t["horiz_DRY"] == pytest.approx(40.0, abs=1e-4)


@pytest.mark.parametrize("k", TF)
def test_open_dome_held_never_zero(k):
    rows, t = CR.ledger(dome_room(_tf(k)), "DRY", CR.ST_DC, "fixture")
    assert q(rows, "under an open dome") == pytest.approx(math.pi, abs=2e-3)
    assert q(rows, "horizontal decor") == pytest.approx(25 - math.pi, abs=2e-3)
    assert q(rows, "ceiling edge at an opening") == pytest.approx(2 * math.pi, abs=2e-3)


def test_stair_and_shaft_get_no_decor_ceiling():
    rec = _face("st", box(0, 0, 3, 5), [("t", "STAIR", box(0, 0, 3, 4), None), ("s", "SLAB", box(0, 4, 3, 5), None)])
    rows, t = CR.ledger(rec, "STAIR", CR.ST_DC, "fixture")
    assert not [r for r in rows if r["SURFACE"].startswith("horizontal decor")]
    assert q(rows, "stair soffit over the flights") == pytest.approx(12.0, abs=1e-4)
    assert q(rows, "stair top under the slab") == pytest.approx(3.0, abs=1e-4)
    assert t.get("horiz_STAIR") is None


def test_held_part_deducted_once_and_listed():
    rec = _face("hall2", box(0, 0, 4, 4), [("s", "SLAB", box(0, 0, 4, 4), None)])
    rows, t = CR.ledger(rec, "DRY", CR.ST_DC, "fixture", held_parts=[("stair well top", 6.0, "fixture")])
    assert q(rows, "held part of the ceiling") == 6.0
    assert q(rows, "horizontal decor") == pytest.approx(10.0, abs=1e-4)


def test_adverse_openings_counted_twice_refused():
    rec = _face("small", box(0, 0, 2, 2), [("v1", "VOID+STAIR", box(0, 0, 2, 2), None),
                                           ("v2", "OPENING", box(0, 0, 2, 2), None)])
    with pytest.raises(CR.LedgerError):
        CR.ledger(rec, "DRY", CR.ST_DC, "fixture")


def test_adverse_unit_and_class_refused():
    rec = hall()
    rec["unit"] = "mm"
    with pytest.raises(CR.LedgerError):
        CR.ledger(rec, "DRY", CR.ST_DC, "fixture")
    with pytest.raises(CR.LedgerError):
        CR.ledger(hall(), "BEDROOM", CR.ST_DC, "fixture")


def test_adverse_conflict_or_held_beam_never_gives_an_owner_face():
    for st in ("CONFLICT", "HELD", "NO_R2_ROW"):
        m = dict(CALC, r2_status=st)
        rec = _face("h", box(0, 0, 6, 4), [("s", "SLAB", box(0, 0, 6, 4), None),
                                           ("b", "BEAM", box(2.85, -0.2, 3.15, 4.2), m)])
        rows, t = CR.ledger(rec, "DRY", CR.ST_DC, "fixture")
        assert t["own_bulk_m2"] == 0.0
        assert q(rows, "bulkhead edges on") == pytest.approx(8.0, abs=1e-3)
    m = dict(CALC, r2_depth="0.75/0.9")          # two depths for one member: not a single value -> HELD
    rec = _face("h", box(0, 0, 6, 4), [("b", "BEAM", box(2.85, -0.2, 3.15, 4.2), m)])
    rows, t = CR.ledger(rec, "DRY", CR.ST_DC, "fixture")
    assert t["own_bulk_m2"] == 0.0


def test_unregistered_piece_held_or_junction():
    rec = _face("h", box(0, 0, 6, 4), [("b", "BEAM_OR_COLUMN", box(2.85, -0.2, 3.15, 4.2), None),
                                       ("j", "BEAM_OR_COLUMN", box(5.8, 3.8, 6.0, 4.0), None)])
    rows, t = CR.ledger(rec, "DRY", CR.ST_DC, "fixture")
    assert q(rows, "bulkhead edges on") == pytest.approx(8.0, abs=1e-3)
    assert q(rows, "beam / column junction pieces") == 1


def test_no_held_row_is_zero():
    for rec, cls, kw in ((hall(), "DRY", {}), (bath(), "WET", {}), (living(), "DRY", {"closed": False}),
                         (dome_room(), "DRY", {})):
        rows, _ = CR.ledger(rec, cls, CR.ST_DC, "fixture", **kw)
        for r in rows:
            if r["STATUS"] == CR.ST_H:
                assert r["QTY"] != 0, r
                if r["QTY"] == "":
                    assert r["NOTE"] or r["BASIS"], r


def test_reconcile_names_the_residual():
    res, rows = CR.reconcile(40.0, 32.5, [("light well", 6.0), ("stair strip", 1.5)])
    assert res == 0.0 and rows[-1] == ("horizontal ceiling", 32.5)
    res, _ = CR.reconcile(40.0, 32.0, [("light well", 6.0), ("stair strip", 1.5)])
    assert res == pytest.approx(0.5)


# ------------------------------------------------------------------------------------- Alsenan ledger guard
def test_alsenan_ledger_rebuilds_byte_identical(tmp_path):
    subprocess.run([sys.executable, "-I", str(MOD / "t271_alsenan_check.py"), "--out", str(tmp_path)], check=True,
                   capture_output=True)
    for name in ("CEILINGS_T271.csv", "RECONCILE_T271.csv", "FLOORS_T271.csv", "VS_FREELANCER_T271.csv",
                 "STRIPS_T271.csv", "summary.json"):
        assert (tmp_path / name).read_bytes() == (MOD / name).read_bytes(), name


def test_alsenan_key_figures():
    s = json.loads((MOD / "summary.json").read_text())
    assert s["engine_fin_ceiling_m2"] == pytest.approx(403.1628, abs=1e-3)
    assert s["horizontal_m2"] == pytest.approx(362.282, abs=1e-3)
    assert s["totals"]["held_dome"] == pytest.approx(29.0694, abs=1e-3)
    assert s["totals"]["deduct_no_ceiling"] == pytest.approx(23.2371, abs=1e-3)
    assert s["totals"]["own_bulk_m2"] == pytest.approx(29.2367, abs=1e-3)
    # hand check on the printed size: Majlis CB6 0.20 wide crosses the printed 4.00 room width -> 2 x 4.00 x 0.15
    rows = list(csv.DictReader(open(MOD / "CEILINGS_T271.csv")))
    cb6 = [r for r in rows if r["FACE"] == "GF-R7512EA" and "CB6" in r["SURFACE"]]
    assert len(cb6) == 1 and float(cb6[0]["QTY"]) == pytest.approx(1.200, abs=1e-3)
    rec = {r["FACE"]: r for r in csv.DictReader(open(MOD / "RECONCILE_T271.csv"))}
    # every floor piece of the released architectural run is in the ledger exactly once (pantry split in two)
    assert len(rec) == 39
    assert float(rec["GF-RC99C2A/open"]["R2_MINUS_ENGINE_M2"]) == pytest.approx(-9.6823, abs=1e-3)


def test_no_coordinates_or_texts_committed():
    d = json.loads((MOD / "ALSENAN_T271_INPUT.json").read_text())
    for f in d["faces"]:
        assert "wkt" not in json.dumps(f) and "texts" not in f
