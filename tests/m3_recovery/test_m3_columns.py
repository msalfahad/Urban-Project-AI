"""M3 WP2 regression: column association bugs found on ST7757, re-created on a hand-made four-sheet set with
hand-derived truth.

    column plan     C1 x2, C2 x2 drawn at their FOUNDATION size, each outline drawn twice (polyline + its four lines),
                    labels 0.7 m beside the outline
    GF roof plan    all four columns, at the GF band size
    1F roof plan    only C1 @ (2,2) and C2 @ (2,6): the other two stop below 1F
    foundation plan footing F1 (1.2 x 1.2 x 0.4) under every column, combined labels "C1/F1"
    schedule        C1: FOU 30x50, GR 25x50, 1ST 20x50 (8 / 8 / 6 Y16); C2: 30x30 at every band (4 Y16)
                    a beam table holding B1 and CA (CA is a column by pattern, a beam by its table) and SB1 (strap)

    GF  = 2 x 0.25 x 0.50 x 4.0 + 2 x 0.30 x 0.30 x 4.0              = 1.72   (no false section conflict)
    1F  = 0.20 x 0.50 x 3.5 + 0.30 x 0.30 x 3.5                       = 0.665  (two columns absent: never counted)
    neck height = 0.8 (top) + 1.5 (founding) - 0.4 (footing)          = 1.9;  high with founding 2.0 -> 2.4
    necks = (2 x 0.30 x 0.50 + 2 x 0.30 x 0.30) x 1.9                 = 0.912
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

ezdxf = pytest.importorskip("ezdxf")

from engine.source import generic_route as GR              # noqa: E402
from engine.source import provisional_estimate as PE       # noqa: E402
from engine.source import schedule_reader as SR            # noqa: E402
from tools import urban_intake as UI                       # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
COLS = [("C1", 2000, 2000), ("C1", 6000, 2000), ("C2", 2000, 6000), ("C2", 6000, 6000)]
SIZE = {"C1": {"FOU": (300, 500), "GR": (250, 500), "1ST": (200, 500)},
        "C2": {"FOU": (300, 300), "GR": (300, 300), "1ST": (300, 300)}}


def _set(path):
    doc = ezdxf.new("R2018")
    doc.header["$INSUNITS"] = 4
    m = doc.modelspace()

    def frame(k, title):
        x0 = k * 45000
        m.add_lwpolyline([(x0, 0), (x0 + 40000, 0), (x0 + 40000, 28000), (x0, 28000)], close=True,
                         dxfattribs={"layer": "FRAME"})
        m.add_text(title, dxfattribs={"layer": "S-TEXT", "height": 400}).set_placement((x0 + 1000, 26500))
        return x0

    def rect(x0, cx, cy, w, h, layer, lines=False):
        pts = [(x0 + cx - w / 2, cy - h / 2), (x0 + cx + w / 2, cy - h / 2), (x0 + cx + w / 2, cy + h / 2),
               (x0 + cx - w / 2, cy + h / 2)]
        m.add_lwpolyline(pts, close=True, dxfattribs={"layer": layer})
        if lines:
            for i in range(4):
                m.add_line(pts[i], pts[(i + 1) % 4], dxfattribs={"layer": layer})

    def txt(s, x, y, h=200):
        m.add_text(s, dxfattribs={"layer": "S-TEXT", "height": h}).set_placement((x, y))
    x = frame(0, "COLUMNS PLAN")
    for mk, cx, cy in COLS:
        w, h = SIZE[mk]["FOU"]
        rect(x, cx, cy, w, h, "S-COL", lines=True)
        txt(mk, x + cx + w / 2 + 700, cy)
    x = frame(1, "GROUND FLOOR ROOF SLAB")
    for mk, cx, cy in COLS:
        rect(x, cx, cy, *SIZE[mk]["GR"], "S-COL")
    x = frame(2, "FIRST FLOOR ROOF SLAB")
    for mk, cx, cy in COLS:
        if cx == 2000:
            rect(x, cx, cy, *SIZE[mk]["1ST"], "S-COL")
    x = frame(3, "FOUNDATION PLAN")
    for mk, cx, cy in COLS:
        rect(x, cx, cy, 1200, 1200, "S-FTG")
        rect(x, cx, cy, *SIZE[mk]["FOU"], "S-COL")
        txt(f"{mk}/F1", x + cx - 550, cy - 500, 150)
    x = frame(4, "SCHEDULE OF COLUMNS AND FOOTINGS")

    def table(name, tags, rows, y0):
        blk = doc.blocks.new(name)
        for k, t in enumerate(tags):
            blk.add_attdef(t, (k * 800, 0), dxfattribs={"height": 150, "layer": "S-SCHED"})
        for n, vals in enumerate(rows):
            ins = m.add_blockref(name, (x + 1000, y0 - 600 * n), dxfattribs={"layer": "S-SCHED"})
            ins.add_auto_attribs(dict(zip(tags, [str(v) for v in vals])))
    ctags = ("COL-T", "FOU.W", "FOU.H", "FOU.R", "FOU.D", "GR.W", "GR.H", "GR.R", "GR.D", "1ST.W", "1ST.H",
             "1ST.R", "1ST.D")
    table("COL_ROW", ctags, [("C1", 30, 50, 8, 16, 25, 50, 8, 16, 20, 50, 6, 16),
                             ("C2", 30, 30, 4, 16, 30, 30, 4, 16, 30, 30, 4, 16)], 24000)
    table("FTG_ROW", ("FO-TY", "W", "H", "DEPHT", "SH-B", "SH-D", "LO-B", "LO-D"),
          [("F1", 120, 120, 40, 7, 12, 7, 12)], 20000)
    table("BEAM_ROW", ("BEAM", "W", "H", "BOT-B", "BOT-D", "TOP-B", "TOP-D", "STI-B", "D"),
          [("B1", 20, 50, 3, 16, 2, 12, 5, 8), ("B2", 25, 60, 3, 16, 2, 12, 5, 8), ("CA", 30, 50, 5, 18, 5, 18, 8, 8),
           ("SB1", 70, 80, 4, 16, 4, 16, 5, 10)], 17000)
    doc.saveas(path)
    return path


def _conv(with_neck=True):
    gen = json.loads((ROOT / "engine/profiles/URBAN_M3_GENERIC_CONVENTIONS_V2.json").read_text())
    prof = {"profile": "T", "conventions": [
        {"id": "STOREY_HEIGHT_GF", "title": "GF", "kind": "number", "unit": "m", "base": 4.0, "low": 4.0, "high": 4.0,
         "provenance": "PRINTED_VALUE", "source": "test", "rationale": "test"},
        {"id": "STOREY_HEIGHT_1F", "title": "1F", "kind": "number", "unit": "m", "base": 3.5, "low": 3.5, "high": 3.5,
         "provenance": "PRINTED_VALUE", "source": "test", "rationale": "test"}]}
    if with_neck:
        prof["conventions"] += [
            {"id": "FOUNDING_DEPTH_M", "title": "f", "kind": "number", "unit": "m", "base": 1.5, "low": 1.5,
             "high": 2.0, "provenance": "PRINTED_MINIMUM", "source": "test", "rationale": "test"},
            {"id": "NECK_TOP_LEVEL_M", "title": "t", "kind": "number", "unit": "m", "base": 0.8, "low": 0.8,
             "high": 0.8, "provenance": "PRINTED_VALUE", "source": "test", "rationale": "test"}]
    return GR.merge_conventions(gen, prof)


@pytest.fixture(scope="module")
def drawing(tmp_path_factory):
    p = _set(tmp_path_factory.mktemp("cols") / "cols.dxf")
    I = UI.read(p)
    return I, GR.detect(I)


def _run(D, with_neck=True):
    conv = _conv(with_neck)
    items, reg, risk = GR.items_from(D, conv, GR.storey_heights(conv))
    PE.check(items, conv)
    return items, reg, risk


def _sum(items, storey, trade="CONCRETE"):
    sel = [i for i in items if i["family"] == "COLUMNS" and i["trade"] == trade and i["storey"] == storey and
           i["category"] == "PROVISIONAL"]
    return sum(i["low"] for i in sel), sum(i["base"] for i in sel), sum(i["high"] for i in sel), len(sel)


def test_twin_outlines_do_not_make_labels_ambiguous(drawing):
    I, D = drawing
    plan = next(r for r in D["sheets"].values() if r["sheet"]["role"] == "COLUMN_PLAN")
    assert {o["outline_binding"] for o in plan["columns"]} == {"NEAREST"}


def test_column_plan_size_is_no_false_conflict(drawing):
    I, D = drawing
    items, reg, risk = _run(D)
    lo, b, hi, n = _sum(items, "GF")
    assert n == 4 and (lo, b, hi) == pytest.approx((1.72, 1.72, 1.72))


def test_storey_presence_from_the_roof_plan(drawing):
    I, D = drawing
    items, reg, risk = _run(D)
    lo, b, hi, n = _sum(items, "1F")
    assert n == 2 and b == pytest.approx(0.2 * 0.5 * 3.5 + 0.3 * 0.3 * 3.5)
    absent = [r for r in reg if r["FAMILY"] == "COLUMNS" and r["STOREY"] == "1F" and r["REBAR_STATE"] == "EXPLICIT_NONE"]
    assert len(absent) == 2 and sum(1 for r in risk if r["KIND"] == "COLUMN_ABSENT_ON_STOREY_PLAN") == 2


def test_necks_over_their_own_footing(drawing):
    I, D = drawing
    items, reg, risk = _run(D)
    lo, b, hi, n = _sum(items, "FOUNDATION")
    a = 2 * 0.3 * 0.5 + 2 * 0.3 * 0.3
    assert n == 4 and (lo, b, hi) == pytest.approx((a * 1.9, a * 1.9, a * 2.4))
    steel = [i for i in items if i["family"] == "COLUMNS" and i["storey"] == "FOUNDATION" and
             i["trade"] == "REINFORCEMENT"]
    assert steel and all(i["dia_mm"] == 16 for i in steel)


def test_necks_without_printed_levels_stay_unresolved(drawing):
    I, D = drawing
    items, reg, risk = _run(D, with_neck=False)
    necks = [i for i in items if i["family"] == "COLUMNS" and i["storey"] == "FOUNDATION"]
    assert len(necks) == 4 and all(i["category"] == "UNRESOLVED" and i["exposure_high"] for i in necks)


def test_a_column_mark_in_a_beam_table_is_a_beam(drawing):
    I, D = drawing
    S = SR.from_attribute_rows(I["attributes"])
    fam = {r["mark"]: r["family"] for r in S["rows"]}
    assert fam["CA"] == "BEAM" and fam["SB1"] == "STRAP_BEAM" and fam["C1"] == "COLUMN"
