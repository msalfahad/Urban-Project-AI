"""M3 WP5 / WP6 regression: the slab and beam bugs found on ST7757, re-created on a hand-made three-sheet set with
hand-derived truth.

GF roof slab (beams 0.20, cells A 5.7 x 7.6, B 5.7 x 4.7, C 5.7 x 2.7)
    C   a stair flight of nine treads (2.0 m, going 0.28) over 29 % of the cell   -> STAIR_ZONE, never slab
    A   five short tread lines over 2 % of the cell                               -> slab, coverage risk
    B   a free-standing 0.30 column on no beam                                    -> slab (flat-slab zone) 26.79 - 0.09,
                                                                                     coverage risk
1F roof slab
    CB1 0.30 strip whose faces enclose a 10 mm stub of B2's face (ST7757 CB11)    -> recovered 7.99 m
    B3  a face with 0.20 partners on both sides over half its length (ST7757 CB5) -> the other half bound, 4.0 m
    CB2 two pieces 1.4 m apart, a column outline filling the gap (ST7757 CB8)     -> the second piece inherits CB2
    B9  a 0.90 inclined beam alone on a layer named for beams (ST7757 B27)        -> found and bound
    B5  an edge beam with only its inner face drawn, slab behind, mark in front   -> 0.25 x 8.0 x 0.5, one assumed
                                                                                     dimension
    B7  a mark beside a lone face with no slab behind it                          -> left unbound
ground-beam plan (0.30 ring, typical sections)
    the interior band stops 0.5 m short of the ring; a 0.30 x 0.50 column outline (no schedule size) fills the gap
                                                                                  -> the two cells stay separate
    a C1 column stands free in the right cell                                     -> UNRESOLVED (not ground slab)
open-boundary recovery                                                            -> face - bands, junctions once
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import pytest

ezdxf = pytest.importorskip("ezdxf")

from engine.source import generic_route as GR              # noqa: E402
from engine.source import member_detection as MD           # noqa: E402
from engine.source import provisional_estimate as PE       # noqa: E402
from engine.source import slab_engine as SE                # noqa: E402
from tools import urban_intake as UI                       # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
X1F, XGB = 45000, 90000


def _set(path):
    doc = ezdxf.new("R2018")
    doc.header["$INSUNITS"] = 4
    m = doc.modelspace()

    def frame(x0, title):
        m.add_lwpolyline([(x0 - 2000, -2000), (x0 + 38000, -2000), (x0 + 38000, 30000), (x0 - 2000, 30000)],
                         close=True, dxfattribs={"layer": "FRAME"})
        m.add_text(title, dxfattribs={"layer": "S-TEXT", "height": 400}).set_placement((x0, 28500))

    def L(a, b, layer="1", x0=0):
        m.add_line((a[0] + x0, a[1]), (b[0] + x0, b[1]), dxfattribs={"layer": layer})

    def T(s, x, y, rot=0.0, h=150):
        m.add_text(s, dxfattribs={"layer": "S-TEXT", "height": h, "rotation": rot}).set_placement((x, y))

    def rect(x0, y0, x1, y1, layer="S-COL"):
        m.add_lwpolyline([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], close=True, dxfattribs={"layer": layer})
    # ---- GF roof slab
    frame(0, "GROUND FLOOR ROOF SLAB")
    for a, b in (((0, 0), (12000, 0)), ((12000, 0), (12000, 8000)), ((12000, 8000), (0, 8000)), ((0, 8000), (0, 0)),
                 ((200, 200), (11800, 200)), ((11800, 200), (11800, 7800)), ((11800, 7800), (200, 7800)),
                 ((200, 7800), (200, 200)), ((5900, 200), (5900, 7800)), ((6100, 200), (6100, 7800)),
                 ((6100, 4900), (11800, 4900)), ((6100, 5100), (11800, 5100))):
        L(a, b)
    for x, y, r in ((3000, 60, 0), (3000, 7860, 0), (60, 4000, 90), (11860, 2000, 90), (5960, 4000, 90),
                    (9000, 4960, 0)):
        T("B1", x, y, r, 80)
    for k in range(9):                                       # stair flight in C
        L((6500, 5300 + 280 * k), (8500, 5300 + 280 * k), "2")
    for k in range(5):                                       # tread lines in A
        L((1000, 1000 + 250 * k), (2000, 1000 + 250 * k), "2")
    rect(8850, 2350, 9150, 2650)                             # free-standing C1 in B
    T("C1", 8900, 2450, 0, 80)
    T("T=16", 3000, 4000)
    # ---- 1F roof slab
    frame(X1F, "FIRST FLOOR ROOF SLAB")
    L((1000, 1000), (11000, 1000), x0=X1F)                   # CB1 / B2 lower face
    L((1000, 1200), (3010, 1200), x0=X1F)                    # B2 upper face, 10 mm into CB1
    L((3000, 1300), (11000, 1300), x0=X1F)                   # CB1 upper face
    T("B2", X1F + 2000, 1050, 0, 80)
    T("CB1", X1F + 7000, 1100, 0, 100)
    L((20000, 0), (20000, 8000), x0=X1F)                     # shared-face case
    L((20200, 0), (20200, 8000), x0=X1F)
    L((20400, 4000), (20400, 8000), x0=X1F)
    T("B3", X1F + 19850, 2000, 90, 100)
    L((0, 15000), (5000, 15000), x0=X1F)                     # CB2 piece A
    L((0, 15300), (5000, 15300), x0=X1F)
    L((6400, 15000), (12000, 15000), x0=X1F)                 # CB2 piece B
    L((6400, 15300), (12000, 15300), x0=X1F)
    rect(X1F + 4990, 15000, X1F + 6410, 15300)               # a 1.42 m column outline across the gap
    rect(X1F + 30000, 15000, X1F + 30300, 15300)             # a C1 (so the column layer is known)
    T("CB2", X1F + 2500, 15100, 0, 100)
    a, d = math.radians(30.0), 900.0                          # B9 inclined, on its own beam layer
    ux, uy, nx, ny = math.cos(a), math.sin(a), -math.sin(a), math.cos(a)
    for s in (0.0, 1.0):
        L((24000 + nx * d * s, 2000 + ny * d * s), (24000 + nx * d * s + 5000 * ux, 2000 + ny * d * s + 5000 * uy),
          "S-BEAM", X1F)
    T("B9", X1F + 24000 + 2500 * ux + nx * 450, 2000 + 2500 * uy + ny * 450, 30.0, 120)
    L((0, 20000), (8000, 20000), x0=X1F)                     # single-face cell
    for a_, b_ in (((0, 24000), (8000, 24000)), ((0, 24200), (8000, 24200)), ((0, 20000), (0, 24200)),
                   ((200, 20000), (200, 24000)), ((7800, 20000), (7800, 24000)), ((8000, 20000), (8000, 24200))):
        L(a_, b_, x0=X1F)
    for x, y, r in ((4000, 24060, 0), (60, 22000, 90), (7860, 22000, 90)):
        T("B1", X1F + x, y, r, 80)
    T("B5", X1F + 4000, 19780, 0, 100)
    L((12000, 20000), (16000, 20000), x0=X1F)                # a lone face, no slab behind
    T("B7", X1F + 14000, 19780, 0, 100)
    # ---- ground-beam plan
    frame(XGB, "GROUND BEAMS PLAN")
    for a_, b_ in (((0, 0), (10000, 0)), ((10000, 0), (10000, 6000)), ((10000, 6000), (0, 6000)), ((0, 6000), (0, 0)),
                   ((300, 300), (9700, 300)), ((9700, 300), (9700, 5700)), ((9700, 5700), (300, 5700)),
                   ((300, 5700), (300, 300)), ((5000, 300), (5000, 5200)), ((5300, 300), (5300, 5200))):
        L(a_, b_, "S-GB", XGB)
    rect(XGB + 5000, 5200, XGB + 5300, 5700)                 # 0.30 x 0.50 outline closing the gap
    rect(XGB + 7350, 2850, XGB + 7650, 3150)                 # C1 free in the right cell
    T("T=10cm", XGB + 2500, 3000)
    # ---- schedules
    frame(135000, "SCHEDULE OF BEAMS AND COLUMNS")

    def table(name, tags, rows, y0):
        blk = doc.blocks.new(name)
        for k, t in enumerate(tags):
            blk.add_attdef(t, (k * 800, 0), dxfattribs={"height": 150, "layer": "S-SCHED"})
        for n, vals in enumerate(rows):
            ins = m.add_blockref(name, (136000, y0 - 600 * n), dxfattribs={"layer": "S-SCHED"})
            ins.add_auto_attribs(dict(zip(tags, [str(v) for v in vals])))
    table("BEAM_ROW", ("BEAM", "W", "H", "BOT-B", "BOT-D", "TOP-B", "TOP-D", "STI-B", "D"),
          [("B1", 20, 50, 3, 14, 2, 12, 5, 8), ("B2", 20, 50, 3, 14, 2, 12, 5, 8), ("B3", 20, 50, 3, 14, 2, 12, 5, 8),
           ("B5", 25, 50, 3, 16, 2, 12, 5, 8), ("B7", 25, 50, 3, 16, 2, 12, 5, 8), ("B9", 90, 85, 8, 20, 4, 16, 6, 10),
           ("CB1", 30, 60, 4, 16, 3, 16, 6, 8), ("CB2", 30, 60, 4, 16, 3, 16, 6, 8)], 24000)
    table("COL_ROW", ("COL-T", "GR.W", "GR.H", "GR.R", "GR.D"), [("C1", 30, 30, 4, 16)], 16000)
    doc.saveas(path)
    return path


def _conv():
    gen = json.loads((ROOT / "engine/profiles/URBAN_M3_GENERIC_CONVENTIONS_V2.json").read_text())
    prof = {"profile": "T", "conventions": [
        {"id": "GB_TYPICAL_SECTIONS", "title": "t", "kind": "choice", "options": ["T"], "base": "T",
         "classes": [{"max_span_m": None, "W": 0.3, "H": 0.6}], "provenance": "READING_OF_PRINTED_VALUE",
         "source": "test", "rationale": "test"}]}
    return GR.merge_conventions(gen, prof)


@pytest.fixture(scope="module")
def run(tmp_path_factory):
    I = UI.read(_set(tmp_path_factory.mktemp("sb") / "sb.dxf"))
    conv = _conv()
    D = GR.detect(I, typical_widths_m=GR.typical_gb_widths(conv))
    items, reg, risk = GR.items_from(D, conv, {})
    PE.check(items, conv)
    sh = {r["sheet"]["storey"] if r["sheet"]["role"] == "SLAB_PLAN" else r["sheet"]["role"]: r
          for r in D["sheets"].values()}
    return I, D, items, reg, risk, sh


def _face_at(rec, x, y):
    # the innermost face holding the point (a ring's outer cycle holds its holes too)
    # (faces carry their outer cycle only: a beam ring "holds" the cells it surrounds, so beam strips are skipped)
    return min((f for f in rec["slab"]["faces"] if f["class"] not in ("BEAM", "COLUMN") and
                MD.point_in_poly(x, y, f["polygon"])), key=lambda f: f["area_m2"])


def _beam(rec, mark):
    return [b for b in rec["beams"] if b.get("mark") == mark]


def test_stair_zone_is_not_slab(run):
    I, D, items, reg, risk, sh = run
    gf = sh["GF"]
    c = _face_at(gf, 9000, 6800)
    assert c["region"] == "STAIR_ZONE" and c["treads"]["kind"] == "FLIGHT" and c["treads"]["n"] == 9
    assert c["area_m2"] == pytest.approx(5.7 * 2.7)
    it = next(i for i in items if i["component_id"].endswith(c["face_id"]) and i["trade"] == "CONCRETE")
    assert it["category"] == "UNRESOLVED" and it["blocker"] == "SLAB_STAIR_ZONE"
    assert it["exposure_high"] == pytest.approx(5.7 * 2.7 * 0.16)
    a = _face_at(gf, 4000, 6000)
    assert a["region"] == "STRUCTURAL_SLAB" and a["treads"] and a["area_m2"] == pytest.approx(5.7 * 7.6)
    assert any(r["KIND"] == "SLAB_PANEL_STAIR_LINES" for r in risk)


def test_free_column_on_a_suspended_slab_is_counted_and_flagged(run):
    I, D, items, reg, risk, sh = run
    b = _face_at(sh["GF"], 7000, 1000)
    assert b["region"] == "STRUCTURAL_SLAB" and len(b["free_columns"]) == 1
    it = next(i for i in items if i["component_id"].endswith(b["face_id"]) and i["trade"] == "CONCRETE")
    assert it["category"] == "PROVISIONAL" and it["base"] == pytest.approx((5.7 * 4.7 - 0.09) * 0.16)
    assert any(r["KIND"] == "SLAB_PANEL_FREE_COLUMN" for r in risk)


def test_strip_with_a_10mm_intervening_stub_is_recovered(run):
    I, D, items, reg, risk, sh = run
    cb1 = _beam(sh["1F"], "CB1")
    assert len(cb1) == 1 and cb1[0]["length_m"] == pytest.approx(7.99) and cb1[0]["width_m"] == pytest.approx(0.3)
    assert _beam(sh["1F"], "B2")[0]["length_m"] == pytest.approx(2.01)
    band = next(b for b in sh["1F"]["bands"] if b["band_id"] == cb1[0]["band_id"])
    assert band["rule"] == "INTERVENING_FACE_PART"


def test_unambiguous_part_of_a_shared_face(run):
    I, D, items, reg, risk, sh = run
    b3 = _beam(sh["1F"], "B3")
    assert len(b3) == 1 and b3[0]["length_m"] == pytest.approx(4.0)
    band = next(b for b in sh["1F"]["bands"] if b["band_id"] == b3[0]["band_id"])
    assert band["rule"] == "SHARED_FACE_UNAMBIGUOUS_PART"


def test_inheritance_across_a_column_filled_gap(run):
    I, D, items, reg, risk, sh = run
    cb2 = _beam(sh["1F"], "CB2")
    assert len(cb2) == 2 and sorted(b["binding"] for b in cb2) == ["BOUND", "INHERITED_ALONG_LINE"]
    pieces = [b for b in sh["1F"]["bands"] if b["band_id"] in {x["band_id"] for x in cb2}]
    assert not MD.collinear_neighbours(pieces, 1.0 / D["unit_m"])          # 1.4 m: no inheritance without the column


def test_a_named_beam_layer_joins_on_one_mark(run):
    I, D, items, reg, risk, sh = run
    assert "S-BEAM" in sh["1F"]["edge_layers"]
    b9 = _beam(sh["1F"], "B9")
    assert len(b9) == 1 and b9[0]["width_m"] == pytest.approx(0.9) and b9[0]["length_m"] == pytest.approx(5.0)


def test_single_face_edge_beam(run):
    I, D, items, reg, risk, sh = run
    b5 = _beam(sh["1F"], "B5")
    assert len(b5) == 1 and b5[0]["length_m"] == pytest.approx(8.0) and b5[0]["width_m"] == pytest.approx(0.25)
    it = next(i for i in items if i["component_id"].endswith(":" + b5[0]["band_id"]) and i["trade"] == "CONCRETE")
    assert it["support"] == "ONE_ASSUMED_DIMENSION" and it["confidence"] == "LOW"
    assert it["blocker"] == "SINGLE_FACE_BEAM" and it["base"] == pytest.approx(0.25 * 8.0 * 0.5)
    b7 = next(m for m in sh["1F"]["marks"] if m["mark"] == "B7")
    assert b7["state"] == "TAG_UNBOUND"


def test_ground_slab_cells_closed_by_a_column_outline_and_free_column(run):
    I, D, items, reg, risk, sh = run
    g = sh["GROUND_BEAM_PLAN"]
    ox = XGB
    left = _face_at(g, ox + 2500, 3000)
    right = _face_at(g, ox + 8500, 3000)
    assert left is not right
    assert left["region"] == "GROUND_SLAB" and left["area_m2"] == pytest.approx(4.7 * 5.4)
    assert right["region"] == "UNRESOLVED" and right["area_m2"] == pytest.approx(4.4 * 5.4 - 0.09)
    it = next(i for i in items if i["component_id"].endswith(right["face_id"]) and i["trade"] == "CONCRETE")
    assert it["category"] == "UNRESOLVED" and it["blocker"] == "SLAB_CELL_FREE_COLUMNS"


def test_open_boundary_panel_is_face_minus_bands():
    # an L-shaped leaked face: a 4 x 3 panel plus a 6 x 0.3 strip along its bottom, two bands covering the strip
    # with a 0.3 x 0.3 junction overlap; the panel part is 12.0 exactly
    face = {"polygon": [(0, -0.3), (6, -0.3), (6, 0), (4, 0), (4, 3), (0, 3), (0, 0)]}
    bands = [{"kind": "STRAIGHT", "polygon": [(0, -0.3), (3.3, -0.3), (3.3, 0), (0, 0)]},
             {"kind": "STRAIGHT", "polygon": [(3.0, -0.3), (6, -0.3), (6, 0), (3.0, 0)]}]
    assert SE.open_boundary_panel(face, bands, [], 1.0) == pytest.approx(12.0)
