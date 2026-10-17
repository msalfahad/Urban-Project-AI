"""M7 geometry and intake rules, each on a hand-built fixture (the expected value is the fixture's own geometry, never
an engine output): OCS / MTEXT direction, drawn rectangles under crossing outlines, unit-aware polyline rectangles,
the drawing-local origin, touch versus overlap, per-layer stair treads, column layer evidence, and continuous-beam
end anchorage on a line read in reverse."""

from __future__ import annotations

import math

import pytest

ezdxf = pytest.importorskip("ezdxf")

from engine.source import continuous_beams as CBM          # noqa: E402
from engine.source import drawing_model as DM              # noqa: E402
from engine.source import generic_route as GR              # noqa: E402
from engine.source import member_detection as MD           # noqa: E402
from engine.source import slab_engine as SE                # noqa: E402
from tools import urban_intake as UI                       # noqa: E402


def _doc(units=4):
    d = ezdxf.new("R2010")
    d.header["$INSUNITS"] = units
    return d


def test_mirrored_text_is_read_in_world_coordinates(tmp_path):
    d = _doc()
    d.modelspace().add_text("B7", dxfattribs={"height": 150, "insert": (5000, 2000), "rotation": 0})
    d.saveas(tmp_path / "a.dxf")
    for e in d.modelspace():
        e.transform(ezdxf.math.Matrix44.scale(-1, 1, 1))
    d.saveas(tmp_path / "b.dxf")
    t0 = UI.read(tmp_path / "a.dxf")["texts"][0]
    t1 = UI.read(tmp_path / "b.dxf")["texts"][0]
    assert math.isclose(t1["x"], -t0["x"], abs_tol=1e-6) and math.isclose(t1["y"], t0["y"], abs_tol=1e-6)
    assert round(t1["rotation"]) % 360 == 180                   # the mirrored reading direction


def test_mtext_direction_vector_gives_the_rotation(tmp_path):
    d = _doc()
    d.modelspace().add_mtext("B1", dxfattribs={"char_height": 150, "insert": (0, 0), "rotation": 90})
    for e in d.modelspace():
        e.transform(ezdxf.math.Matrix44.translate(1000, 0, 0))     # a transformed MTEXT stores text_direction
    d.saveas(tmp_path / "m.dxf")
    assert d.modelspace().query("MTEXT")[0].dxf.hasattr("text_direction")
    t = UI.read(tmp_path / "m.dxf")["texts"][0]
    assert round(t["rotation"]) == 90


def _rect(x0, y0, x1, y1, k):
    return [(f"{k}a", x0, y0, x1, y0), (f"{k}b", x1, y0, x1, y1), (f"{k}c", x1, y1, x0, y1), (f"{k}d", x0, y1, x0, y0)]


def test_crossing_outlines_keep_both_drawn_rectangles():
    segs = _rect(0, 0, 1000, 250, "A") + _rect(400, -375, 600, 625, "B")
    got = {tuple(round(v) for v in r["box"]) for r in MD.drawn_rectangles(segs, eps=0.5)}
    assert got == {(0, 0, 1000, 250), (400, -375, 600, 625)}


def _seg(i, layer, a, b):
    return {"id": i, "layer": layer, "a": a, "b": b, "path": [], "kind": "LINE"}


def test_polyline_rectangles_in_metres_need_the_unit_aware_minimum():
    segs = [_seg(f"P1:{k}", "S-COL", a, b) for k, (a, b) in enumerate(
        [((0, 0), (0.3, 0)), ((0.3, 0), (0.3, 0.5)), ((0.3, 0.5), (0, 0.5)), ((0, 0.5), (0, 0))])]
    assert DM.closed_rectangles(segs) == []                                  # the frozen 1.0-unit minimum
    assert [r["box"] for r in DM.closed_rectangles(segs, eps=1e-3 / 1.0)] == [(0.0, 0.0, 0.3, 0.5)]


def test_local_origin_moves_everything_and_records_the_shift():
    I = {"segments": [_seg("1:0", "L", (1e6 + 5, 2e6 + 7), (1e6 + 9, 2e6 + 7))],
         "arcs": [{"c": (1e6, 2e6), "s": (1e6 + 1, 2e6), "m": (1e6, 2e6 + 1), "e": (1e6 - 1, 2e6)}],
         "circles": [{"c": (1e6 + 3, 2e6 + 3)}], "ellipses": [],
         "texts": [{"x": 1e6 + 2, "y": 2e6 + 2, "value": "B1"}], "attributes": [], "inserts": [], "hatches": []}
    L = GR.to_local_origin(I)
    assert L["local_origin"]["x"] == 1e6 - 1 and L["local_origin"]["y"] == 2e6
    assert L["segments"][0]["a"] == (6.0, 7.0) and L["texts"][0]["x"] == 3.0 and L["arcs"][0]["c"] == (1.0, 0.0)
    assert I["segments"][0]["a"] == (1e6 + 5, 2e6 + 7)                      # the intake itself is not touched


def _band(bid, x0, x1, y0, y1):
    return {"band_id": bid, "kind": "STRAIGHT", "u": (1.0, 0.0), "n": (0.0, 1.0), "t0": x0, "t1": x1,
            "lo_off": y0, "hi_off": y1, "length": x1 - x0, "width_native": y1 - y0,
            "polygon": [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]}


def test_a_flush_column_touches_but_does_not_cut():
    b = _band("B1", 0.0, 6000.0, 0.0, 250.0)
    flush = (2000.0, 250.0, 2300.0, 550.0)                   # its face on the band face: overlap area 0
    through = (4000.0, -25.0, 4300.0, 275.0)
    out = MD.split_at_supports([b], [flush, through], 50.0, (1e-2 / 1e-3) ** 2)
    assert [p["band_id"] for p in out] == ["B1.1", "B1.2"]
    assert all(p["cut_by"] == [tuple(round(v, 1) for v in through)] for p in out)


def test_treads_are_read_per_layer():
    face = [(0, 0), (3000, 0), (3000, 3000), (0, 3000)]
    treads = [_seg(f"T{k}:0", "A-STAIR", (500, 300 + 280 * k), (1500, 300 + 280 * k)) for k in range(9)]
    noise = [_seg(f"N{k}:0", "Z-FURN", (600, 300 + 280 * k + 120), (1400, 300 + 280 * k + 120)) for k in range(8)]
    assert SE.tread_family(face, treads + noise, 1e-3) is None               # the interleaved lines break the going
    got = SE.tread_family(face, treads + noise, 1e-3, per_layer=True)
    assert got and got["kind"] == "FLIGHT" and got["n"] == 9


def test_a_furniture_rectangle_at_a_column_size_is_not_a_column():
    lib = {("COLUMN", "C1"): {"by_storey": {}, "dims_m": {"W": 0.3, "H": 0.3}}}
    rects = [{"box": (k * 5000.0, 0.0, k * 5000.0 + 300.0, 300.0), "layer": "S-COLUMN", "source": f"c{k}"}
             for k in range(4)]
    rects += [{"box": (1000.0 + 700 * k, 2000.0, 1000.0 + 700 * k + 300 + 90 * k, 2000.0 + 300 + 40 * k),
               "layer": "Z-FURNITURE", "source": f"f{k}"} for k in range(6)]     # f0 is exactly 300 x 300
    ents = {"rects": rects, "segments": [], "texts": [], "arcs": []}
    old = GR.column_boxes(ents, lib, 1e-3)
    new = GR.column_boxes(ents, lib, 1e-3, layer_evidence=True)
    assert (1000.0, 2000.0, 1300.0, 2300.0) in old
    assert (1000.0, 2000.0, 1300.0, 2300.0) not in new and len(new) == 4


def _span(index, left, right, clear):
    return {"index": index, "clear_m": clear, "drawn_m": clear + 0.5, "left": left, "right": right,
            "pieces": [f"P{index}"]}


def test_continuous_beam_end_anchorage_does_not_depend_on_drawing_direction():
    row = {"mark": "CB1", "raw": {}, "dims_m": {"W": 0.2, "H": 0.6}}
    A = {"kind": "COLUMN", "width_m": 0.2, "centre": 0.0}
    B = {"kind": "COLUMN", "width_m": 0.9, "centre": 6.0}
    C = {"kind": "COLUMN", "width_m": 0.25, "centre": 11.5}
    fwd = {"spans": [_span(1, A, B, 5.45), _span(2, B, C, 4.925)], "direction": "FORWARD"}
    # the same beam drawn the other way: span 1 lies on the right of the axis, its free end is its RIGHT support
    rev = {"spans": [_span(2, C, B, 4.925), _span(1, B, A, 5.45)], "direction": "REVERSED"}
    orig = CBM.roles
    CBM.roles = lambda r: ({("BOTTOM", 1): {"count": 5, "dia_mm": 18}, ("BOTTOM", 2): {"count": 3, "dia_mm": 16}},
                           set())
    try:
        L = lambda m, f: {g["bar_id"]: tuple(round(x, 9) for x in g["length_m"])                 # noqa: E731
                          for g in CBM.physical_bars(m, row, ends_by_shared_support=f)["groups"]}
        assert L(fwd, True) == L(rev, True) == L(fwd, False)
        assert L(rev, False) != L(fwd, False)                    # the frozen rule read 'left' as towards span 1
    finally:
        CBM.roles = orig


def test_an_exploded_clipped_outline_is_still_a_polygon():
    L = [((0, 0), (1000, 0)), ((1000, 0), (1000, 600)), ((1000, 600), (700, 600)), ((700, 600), (700, 1000)),
         ((700, 1000), (0, 1000)), ((0, 1000), (0, 0))]
    segs = [_seg(f"L{k}:0", "S-FOOTING", b if k % 2 else a, a if k % 2 else b) for k, (a, b) in enumerate(L)]
    r = MD.line_rings(segs, 0.5)
    assert len(r) == 1 and MD.poly_area(r[0]["polygon"]) == 880000.0          # 1.0 x 1.0 less the 0.3 x 0.4 notch
    assert MD.line_rings(segs + [_seg("X:0", "S-FOOTING", (700, 600), (700, 0))], 0.5) == []   # a third line: no ring
    assert MD.line_rings([dict(s, layer=f"L{k}") for k, s in enumerate(segs)], 0.5) == []      # one layer only


class _Conv:
    """the two lookups _gb_class makes: the class table and which conventions are on"""
    def __init__(self, extra=()):
        self.items = {"GB_TYPICAL_SECTIONS": {"classes": [{"max_span_m": 5.0, "W": 0.3, "H": 0.4},
                                                          {"max_span_m": None, "W": 0.3, "H": 0.6}]}}
        self.items.update({k: {} for k in extra})

    def __getitem__(self, k):
        return self.items[k]

    def base(self, k):
        return None


def test_a_length_on_a_class_limit_is_read_at_the_millimetre():
    b = {"width_m": 0.3, "net_plan_m2": 1.5}
    low = lambda conv, L: round(GR._gb_class(conv, dict(b, length_m=L))["volumes"][0], 6)        # noqa: E731
    assert {low(_Conv(), 5.0 - 1e-9), low(_Conv(), 5.0 + 1e-9)} == {0.6, 0.9}     # float noise picks the class
    on = _Conv(["LENGTH_CLASS_AT_MILLIMETRE"])
    assert low(on, 5.0 - 1e-9) == low(on, 5.0 + 1e-9) == 0.9                     # 5.000 m is not below 5.0 m
