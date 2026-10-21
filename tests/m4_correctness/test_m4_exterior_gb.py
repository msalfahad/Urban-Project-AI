"""M4 exterior ground beams: the printed 'for exterior walls' detail applies where the architectural plan shows a
wall on the band, never because the band lies on the perimeter. Hand-made structural ground-beam plan and an
architectural ground-floor plan drawn in another frame (shifted by -1234 / +567 mm), hand-derived truth.

    ring of 0.30 ground beams 10 x 6 m, 0.30 columns at the four corners; one interior band (no outside side)
    long bands 9.4 m (class > 5 m: H 0.60), short bands 5.4 m (class > 5 m by c/c 5.7: H 0.60)
    architectural walls (0.20) on the bottom, left and right bands and on the interior band; none on the top band
    printed levels: +1.00 inside near the bottom-left, +0.30 inside next to the right band

    bottom  EXTERIOR_WALL, inside level 1.00 -> depth 1.00 - 0.10 - 0.00 = 0.90: 2.82 x 0.90  = 2.538 (EVIDENCED)
    left    EXTERIOR_WALL, inside level 1.00 -> 1.62 x 0.90                                  = 1.458
    right   EXTERIOR_WALL, inside level 0.30 -> 0.20 m, not deeper than the class 0.60: class 1.62 x 0.6 = 0.972,
            blocker GB_EXTERIOR_LEVEL_CONFLICT (source conflict, never the shallower depth)
    top     PERIMETER_NO_WALL -> class 2.82 x 0.60 = 1.692, risk GB_PERIMETER_NO_WALL
    interior INTERIOR_WALL -> class 0.972
    without the architectural plan every perimeter band is a CANDIDATE: class base, exterior depth the high end
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

ezdxf = pytest.importorskip("ezdxf")

from engine.source import arch_evidence as AE               # noqa: E402
from engine.source import generic_route as GR               # noqa: E402
from engine.source import provisional_estimate as PE        # noqa: E402
from tools import urban_intake as UI                        # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
OX, OY = 3000, 3000
COLS = [(0, 0), (9700, 0), (9700, 5700), (0, 5700)]
DX, DY = -1234.0, 567.0                                     # architectural frame = structural + (DX, DY)


def _frame(m, title, layer):
    m.add_lwpolyline([(0, 0), (40000, 0), (40000, 28000), (0, 28000)], close=True, dxfattribs={"layer": "FRAME"})
    m.add_text(title, dxfattribs={"layer": layer, "height": 400}).set_placement((1000, 26500))


def _struct(path):
    doc = ezdxf.new("R2018")
    doc.header["$INSUNITS"] = 4
    m = doc.modelspace()
    _frame(m, "GROUND BEAMS PLAN", "S-TEXT")
    for a, b in (((0, 0), (10000, 0)), ((10000, 0), (10000, 6000)), ((10000, 6000), (0, 6000)), ((0, 6000), (0, 0)),
                 ((300, 300), (9700, 300)), ((9700, 300), (9700, 5700)), ((9700, 5700), (300, 5700)),
                 ((300, 5700), (300, 300)), ((5000, 300), (5000, 5700)), ((5300, 300), (5300, 5700))):
        m.add_line((OX + a[0], OY + a[1]), (OX + b[0], OY + b[1]), dxfattribs={"layer": "S-GB"})
    for x, y in COLS:
        m.add_lwpolyline([(OX + x, OY + y), (OX + x + 300, OY + y), (OX + x + 300, OY + y + 300),
                          (OX + x, OY + y + 300)], close=True, dxfattribs={"layer": "S-COL"})
        m.add_text("C1", dxfattribs={"layer": "S-TEXT", "height": 60}).set_placement((OX + x + 100, OY + y + 120))
    doc.saveas(path)
    return path


def _arch(path):
    doc = ezdxf.new("R2018")
    doc.header["$INSUNITS"] = 4
    m = doc.modelspace()
    _frame(m, "GROUND FLOOR PLAN", "A-TEXT")

    def P(x, y):
        return OX + x + DX, OY + y + DY
    for x, y in COLS:
        m.add_lwpolyline([P(x, y), P(x + 300, y), P(x + 300, y + 300), P(x, y + 300)], close=True,
                         dxfattribs={"layer": "A-COL"})
    for a, b in (((300, 50), (9700, 50)), ((300, 250), (9700, 250)),            # bottom: exterior wall
                 ((50, 300), (50, 5700)), ((250, 300), (250, 5700)),            # left
                 ((9750, 300), (9750, 5700)), ((9950, 300), (9950, 5700)),      # right (low floor inside)
                 ((5050, 300), (5050, 5700)), ((5250, 300), (5250, 5700))):     # interior wall
        m.add_line(P(*a), P(*b), dxfattribs={"layer": "A-WALL"})
    for s, x, y in (("+1.00", 2000, 1500), ("+0.30", 9000, 3000)):
        m.add_text(s, dxfattribs={"layer": "A-TEXT", "height": 150}).set_placement(P(x, y))
    doc.saveas(path)
    return path


def _conv(**over):
    gen = json.loads((ROOT / "engine/profiles/URBAN_M4_GENERIC_CONVENTIONS_V3.json").read_text())

    def num(i, b, lo, hi):
        return {"id": i, "title": i, "kind": "number", "unit": "m", "base": b, "low": lo, "high": hi,
                "provenance": "PRINTED_VALUE", "source": "test", "rationale": "test"}
    prof = {"profile": "T", "conventions": [
        {"id": "GB_TYPICAL_SECTIONS", "title": "t", "kind": "choice", "options": ["T"], "base": "T",
         "classes": [{"max_span_m": 2.5, "W": 0.3, "H": 0.3}, {"max_span_m": 5.0, "W": 0.3, "H": 0.4},
                     {"max_span_m": None, "W": 0.3, "H": 0.6}],
         "provenance": "READING_OF_PRINTED_VALUE", "source": "test", "rationale": "test"},
        num("GF_FLOOR_LEVEL_M", 1.0, 1.0, 1.0), num("OUTER_GROUND_LEVEL_M", 0.0, 0.0, 0.15),
        {"id": "GB_EXTERIOR_DETAIL", "title": "e", "kind": "choice", "options": ["E"], "base": "E", "W": 0.3,
         "provenance": "READING_OF_PRINTED_VALUE", "source": "test", "rationale": "test"}]}
    return GR.merge_conventions(gen, prof, over)


@pytest.fixture(scope="module")
def drawing(tmp_path_factory):
    d = tmp_path_factory.mktemp("gbx")
    I, A = UI.read(_struct(d / "s.dxf")), UI.read(_arch(d / "a.dxf"))
    D = GR.detect(I, typical_widths_m=GR.typical_gb_widths(_conv()))
    return D, A


def _bands(D):
    g = next(r for r in D["sheets"].values() if r["sheet"]["role"] == "GROUND_BEAM_PLAN")
    out = {}
    for b in g["beams"]:
        xs, ys = [p[0] for p in b["polygon"]], [p[1] for p in b["polygon"]]
        if b["length_m"] > 9:
            out["bottom" if min(ys) < OY + 100 else "top"] = b["band_id"]
        elif "OUTSIDE" not in g["band_sides"][b["band_id"]]:
            out["interior"] = b["band_id"]
        else:
            out["left" if min(xs) < OX + 100 else "right"] = b["band_id"]
    return out


def test_registration_and_wall_classes(drawing):
    D, A = drawing
    ae = AE.gb_exterior(D, A)
    reg = ae["registration"]
    assert reg["state"] == "REGISTERED" and reg["landed"] == 4
    assert (reg["dx"], reg["dy"]) == pytest.approx((-DX, -DY))
    k = _bands(D)
    cls = {n: ae["bands"][b]["class"] for n, b in k.items()}
    assert cls == {"bottom": "EXTERIOR_WALL", "left": "EXTERIOR_WALL", "right": "EXTERIOR_WALL",
                   "top": "PERIMETER_NO_WALL", "interior": "INTERIOR_WALL"}
    lv = {n: ae["bands"][b].get("floor_level_m") for n, b in k.items()}
    assert lv["bottom"] == 1.0 and lv["left"] == 1.0 and lv["right"] == 0.3   # the inside level, not the nearest


def test_exterior_depth_only_where_a_wall_is_evidenced(drawing):
    D, A = drawing
    conv = _conv()
    ae = AE.gb_exterior(D, A)
    items, reg, risk = GR.items_from(D, conv, {}, arch=ae)
    PE.check(items, conv)
    k = _bands(D)
    c = {n: next(i for i in items if i["component_id"] == f"GROUND_BEAMS:GROUND:{b}" and i["trade"] == "CONCRETE")
         for n, b in k.items()}
    assert c["bottom"]["base"] == pytest.approx(2.82 * 0.9) and "GB_EXTERIOR_EVIDENCE" in c["bottom"]["assumptions"]
    assert c["left"]["base"] == pytest.approx(1.62 * 0.9)
    assert "GF_FLOOR_LEVEL_M" not in c["left"]["assumptions"]            # the level is the plan's, not the profile's
    r = c["right"]
    assert (r["low"], r["base"], r["high"]) == pytest.approx((0.972, 0.972, 0.972))
    assert r["blocker"] == "GB_EXTERIOR_LEVEL_CONFLICT"
    assert c["top"]["base"] == pytest.approx(2.82 * 0.6) and c["top"]["blocker"] == "GB_TITLES_AND_LENGTH_BASIS"
    assert c["interior"]["base"] == pytest.approx(1.62 * 0.6)
    kinds = [x["KIND"] for x in risk]
    assert kinds.count("GB_PERIMETER_NO_WALL") == 1 and kinds.count("GB_EXTERIOR_SHALLOWER_THAN_CLASS") == 1


def test_without_architectural_plan_perimeter_is_only_a_candidate(drawing):
    D, A = drawing
    conv = _conv()
    items, reg, risk = GR.items_from(D, conv, {}, arch=None)
    k = _bands(D)
    b = next(i for i in items if i["component_id"] == f"GROUND_BEAMS:GROUND:{k['bottom']}" and
             i["trade"] == "CONCRETE")
    # class section base, the exterior detail (floor 1.00 - build-up 0 - ground 0) the high alternative
    assert (b["low"], b["base"], b["high"]) == pytest.approx((2.82 * 0.6, 2.82 * 0.6, 2.82 * 1.0))
    assert b["blocker"] == "GB_EXTERIOR_NOT_EVIDENCED"
    # the M3 rule (PERIMETER) is still selectable and takes the exterior depth as base
    conv2 = _conv(GB_EXTERIOR_EVIDENCE="PERIMETER", GB_EXTERIOR_CANDIDATE="EXTERIOR")
    items2, _, _ = GR.items_from(D, conv2, {}, arch=None)
    b2 = next(i for i in items2 if i["component_id"] == b["component_id"] and i["trade"] == "CONCRETE")
    assert b2["base"] == pytest.approx(2.82 * 0.9)


def test_wall_cover_counts_two_faces_or_a_frame():
    U = 0.001
    axis = ((0.0, 0.0), (4000.0, 0.0))
    wall = [{"a": (0, -100), "b": (2000, -100)}, {"a": (0, 100), "b": (2000, 100)}]
    assert AE.wall_cover(axis, wall, U, beam_w_m=0.3) == pytest.approx(0.5)
    frame = [{"a": (2000, -60), "b": (3000, -60)}, {"a": (2000, 60), "b": (3000, 60)}]
    assert AE.wall_cover(axis, wall + frame, U, beam_w_m=0.3) == pytest.approx(0.75)
    far = [{"a": (0, 600), "b": (4000, 600)}, {"a": (0, 800), "b": (4000, 800)}]     # beyond the beam + reach
    wide = [{"a": (0, -300), "b": (4000, -300)}, {"a": (0, 300), "b": (4000, 300)}]   # 0.60 apart: not a wall
    one = [{"a": (0, 0), "b": (4000, 0)}]
    for neg in (far, wide, one):
        assert AE.wall_cover(axis, neg, U, beam_w_m=0.3) == 0.0


def test_registration_refuses_a_tie_and_other_sizes():
    U = 0.001

    def box(x, y, s=400):
        return (x - s / 2, y - s / 2, x + s / 2, y + s / 2)
    struct = [box(x, y) for x, y in ((0, 0), (4000, 0), (9000, 0), (0, 6000), (9000, 6000))]
    arch = [box(x + 1234.0, y - 567.0) for x, y in ((0, 0), (4000, 0), (9000, 0), (0, 6000))]
    r = AE.register(arch, struct, U)
    assert r["state"] == "REGISTERED" and (r["dx"], r["dy"]) == pytest.approx((-1234.0, 567.0))
    row = [box(x, 0) for x in (0, 5000, 10000)]
    tie = AE.register([box(x, 0) for x in (0, 5000)], row, U)          # shift 0 and shift 5 m both land twice
    assert tie["state"] == "NOT_REGISTERED"
    assert AE.register([box(0, 0, 300)], struct, U)["state"] == "NO_COMMON_COLUMNS"


def test_levels_parse_printed_marks_only():
    lv = AE.levels([{"value": "+1.00", "x": 0, "y": 0}, {"norm": "%%p0.00", "x": 1, "y": 1},
                    {"value": "3700", "x": 2, "y": 2}, {"value": "1:100", "x": 3, "y": 3}])
    assert [v["level_m"] for v in lv] == [1.0, 0.0]
