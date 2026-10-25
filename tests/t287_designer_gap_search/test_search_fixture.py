"""T-287 sheet search on a synthetic villa (Villa G, not Alsenan): an item that IS printed is FOUND with its printed
value and handle; an item that is not printed is MISSING and carries no value (never a default).

Villa G, drawn by this test in a temporary DXF (mm), two plan sheets side by side at a 40 m pitch:
  sheet A (x 0 .. 30 m): a straight flight bounded by riser lines R1 (y 2.0) and R2 (y 4.7), lane x 10.0 .. 11.2;
           a second flight bounded by Q1 / Q2 (x 20.0 .. 21.2, y 2.0 .. 4.7) that prints nothing;
           a column outline C (x 5.0 .. 5.3, y 5.0 .. 5.5).
  sheet B (x 40 .. 70 m): the same plan one pitch to the right; the thickness tag 'T 15' (block 't') printed on the
           first flight only; a long dimension 6.00 m passing through the second flight; a callout circle r 0.40 at
           the column.
Hand values: flight 1 thickness printed = 'T 15' -> FOUND; flight 2 -> MISSING (no tag inside 1.20 x 2.70 + 0.15);
the 6.00 m dimension is not wholly inside flight 2's region (it runs y 1.0 .. 7.0) -> context only, not evidence.
"""

import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
_s = importlib.util.spec_from_file_location("t287_search", ROOT / "research" / "agents_t287" / "t287_search.py")
S = importlib.util.module_from_spec(_s)
sys.modules.setdefault("t287_search", S)
_s.loader.exec_module(S)

ezdxf = pytest.importorskip("ezdxf")
PITCH = 40000.0


def villa_g(tmp_path, *, tag_on_flight1=True, tag_offset=(0.0, 0.0), mirror=False, unit=1.0, rotate=False):
    doc = ezdxf.new()
    blk = doc.blocks.new("t")
    blk.add_circle((0, 0), 400)
    blk.add_text("T", dxfattribs={"height": 250}).set_placement((0, 100))
    blk.add_text("15", dxfattribs={"height": 250}).set_placement((0, -250))
    msp = doc.modelspace()

    def P(x, y):                                  # metres on sheet A -> drawing units, optional mirror / 90 deg turn
        if mirror:
            x = 30.0 - x
        if rotate:
            x, y = y, x
        return (x * 1000 * unit, y * 1000 * unit)

    def line(x1, y1, x2, y2, sheet, h):
        dx = sheet * PITCH * unit
        a, b = P(x1, y1), P(x2, y2)
        e = msp.add_line((a[0] + dx, a[1]), (b[0] + dx, b[1]))
        return e
    hs = {}
    hs["R1"] = line(10.0, 2.0, 11.2, 2.0, 0, "R1").dxf.handle
    hs["R2"] = line(10.0, 4.7, 11.2, 4.7, 0, "R2").dxf.handle
    hs["Q1"] = line(20.0, 2.0, 21.2, 2.0, 0, "Q1").dxf.handle
    hs["Q2"] = line(20.0, 4.7, 21.2, 4.7, 0, "Q2").dxf.handle
    c = msp.add_lwpolyline([P(5.0, 5.0), P(5.3, 5.0), P(5.3, 5.5), P(5.0, 5.5)], close=True)
    hs["C"] = c.dxf.handle
    if tag_on_flight1:
        x, y = P(10.6 + tag_offset[0], 3.3 + tag_offset[1])
        msp.add_blockref("t", (x + PITCH * unit, y), dxfattribs={"xscale": unit, "yscale": unit})
    a, b = P(20.6, 1.0), P(20.6, 7.0)
    d = msp.add_linear_dim(base=(a[0] + 500 * unit + PITCH * unit, a[1]), p1=(a[0] + PITCH * unit, a[1]),
                           p2=(b[0] + PITCH * unit, b[1]), angle=90 if not rotate else 0)
    d.render()
    cx, cy = P(5.15, 5.25)
    msp.add_circle((cx + PITCH * unit, cy), 400 * unit)
    path = tmp_path / "villa_g.dxf"
    doc.saveas(path)
    return path, hs


def read(path, unit=1.0):
    doc = ezdxf.readfile(str(path))

    def sheet_of(box):
        k = int(((box[0] + box[2]) / 2) // (PITCH * unit))
        return (("A", "B")[k], (-k * PITCH * unit, 0.0)) if k in (0, 1) else None
    return S._flatten(doc.modelspace(), sheet_of, 1000.0 * unit)


def waist_q(hs, flight):
    a, b = ("R1", "R2") if flight == 1 else ("Q1", "Q2")
    return S.Question(f"w{flight}", "waist printed", (("A", hs[a]), ("A", hs[b])), 0.15, (S.THICK_RE,),
                      sheets=("A", "B"), dims_settle=True)


@pytest.mark.parametrize("mirror,rotate,unit", [(False, False, 1.0), (True, False, 1.0), (False, True, 1.0),
                                                (False, False, 0.1)])
def test_printed_item_found_missing_item_missing(tmp_path, mirror, rotate, unit):
    path, hs = villa_g(tmp_path, mirror=mirror, rotate=rotate, unit=unit)
    ents = read(path, unit)
    v1 = S.verdict(S.search(ents, waist_q(hs, 1), ("A", "B")))
    assert v1["verdict"] == "FOUND"
    assert [(h[0], h[2], h[3]) for h in v1["hits"]] == [("B", "TAG", "T 15")]
    v2 = S.verdict(S.search(ents, waist_q(hs, 2), ("A", "B")))
    assert v2["verdict"] == "MISSING" and v2["hits"] == []
    assert dict(v2["sheets_searched"])["B"] >= 1          # the passing dimension was searched, not counted as evidence


def test_tag_just_outside_the_margin_is_not_borrowed(tmp_path):
    # tag centre 0.80 m beyond the flight's last riser: the 0.40 m bubble edge stays 0.40 m past R2, beyond the 0.15 margin
    path, hs = villa_g(tmp_path, tag_offset=(0.0, 2.2))
    v = S.verdict(S.search(read(path), waist_q(hs, 1), ("A", "B")))
    assert v["verdict"] == "MISSING" and v["hits"] == []


def test_missing_never_returns_a_value(tmp_path):
    path, hs = villa_g(tmp_path, tag_on_flight1=False)
    v = S.verdict(S.search(read(path), waist_q(hs, 1), ("A", "B")))
    assert v == {"verdict": "MISSING", "hits": [], "sheets_searched": v["sheets_searched"]}
    assert all(n >= 0 for _, n in v["sheets_searched"])


def test_callout_bubble_is_not_an_opening_but_a_ring_is(tmp_path):
    path, hs = villa_g(tmp_path)
    ents = read(path)
    q = S.Question("dome", "opening at the column", (("A", hs["C"]),), 0.3, (S.DOME_RE,), sheets=("B",),
                   shapes_settle=("CIRCLE", "ARC"))
    assert S.verdict(S.search(ents, q, ("B",)))["verdict"] == "MISSING"        # r 0.40 bubble < 1.0 m
    ring = S.Ent("B", "CIRCLE", "S-BOUN", "RING1", (3.9, 4.0, 6.4, 6.5))       # a 2.5 m ring drawn at the column
    v = S.verdict(S.search(ents + [ring], q, ("B",)))
    assert v["verdict"] == "FOUND" and v["hits"][0][1] == "RING1"


def test_an_anchor_that_does_not_exist_raises_never_reads_as_nothing_printed(tmp_path):
    path, hs = villa_g(tmp_path)
    q = S.Question("x", "?", (("A", "FFFF"),), 0.1, (S.THICK_RE,), sheets=("B",))
    with pytest.raises(KeyError):
        S.search(read(path), q, ("B",))
    with pytest.raises(ValueError):
        S.union([])


def test_registration_by_level_marks_recovers_the_offset_and_refuses_a_weak_one():
    a = [("+0.30", 1000.0, 2000.0), ("+1.00", 5000.0, 2500.0), ("+0.15", 9000.0, 100.0)]
    b = [(t, x - 250000.0, y + 840000.0) for t, x, y in a] + [("+1.00", 77.0, 88.0)]
    off, n, _ = S.register_by_marks(a, b, min_votes=3)
    assert off == (250000, -840000) and n == 3
    with pytest.raises(ValueError):
        S.register_by_marks(a, b, min_votes=4)
    with pytest.raises(ValueError):
        S.register_by_marks(a, [("+9.70", 0.0, 0.0)], min_votes=1)


def test_patterns():
    for t in ("T 16", "T=10cm 5%%c10/m E.W.", "T16", "THICK. 15", "WAIST 18 cm", "t = 0.15 m"):
        assert S.THICK_RE.match(t), t
    for t in ("THICK.", "Tower", "TOB BARS", "5%%c10/m", "T.C", "TOP"):
        assert not S.THICK_RE.match(t), t
    for t in ("+0.30", "-0.05", "%%p0.00", "+13.90"):
        assert S.LEVEL_RE.match(t), t
    assert not S.LEVEL_RE.match("30X60")
