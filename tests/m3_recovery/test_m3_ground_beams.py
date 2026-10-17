"""M3 WP3 regression: strap and ground-beam binding bugs found on ST7757, re-created on a hand-made two-sheet set
with hand-derived (or independently clipped) truth.

    foundation plan  F1, F2 1.5 x 1.5, F3 1.8 x 1.8 and two more F1 1.0 m apart (a strap-width gap, never a strap);
                     strap 'S.B1' (dotted label) straight, 0.70 wide, entering F1 and F2 by 0.70 m each;
                     strap 'S.B2' inclined, drawn 0.99 wide, with two schedule rows (W 80 and W 100)
    ground-beam plan a 10 x 6 m ring of 0.30 bands, one interior 0.30 band, and a 0.95 strip of slab between two
                     faces drawn as four collinear pieces each (a drawn width mode, never a beam width here)

    SB1  clear 12.0 - 6.5 = 5.5 m;  0.70 x 5.5 x 0.50                                    = 1.925 m3
    SB2  the row whose width the drawing shows (100) is the base; plan = band - footings (shapely, independent)
    ring bands are perimeter (one side outside), the interior band is not
    interior band 0.3 x 5.4, class > 5 m (c/c 5.7) -> H 0.60                              = 0.972 m3
    bottom ring band 0.3 x 9.4 = 2.82 m2: exterior depth 1.00 - 0.10 - 0.00 = 0.90 -> 2.538 (low 2.82 x 0.60 class,
    high 2.82 x 1.00)
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import pytest

ezdxf = pytest.importorskip("ezdxf")

from engine.source import bar_shapes as BS                 # noqa: E402
from engine.source import detail_evidence as DE            # noqa: E402
from engine.source import drawing_model as DM              # noqa: E402
from engine.source import generic_route as GR              # noqa: E402
from engine.source import member_detection as MD           # noqa: E402
from engine.source import provisional_estimate as PE       # noqa: E402
from tools import urban_intake as UI                       # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
F = {"F1": (5000, 5000, 1500), "F2": (12000, 5000, 1500), "F3": (16000, 12000, 1800), "F1b": (22000, 5000, 1500),
     "F1c": (24500, 5000, 1500)}
C2 = ((13000.0, 6000.0), (16900.0, 12900.0))                # SB2 centreline


def _sb2_faces(w=990.0):
    (x0, y0), (x1, y1) = C2
    L = math.hypot(x1 - x0, y1 - y0)
    nx, ny = -(y1 - y0) / L, (x1 - x0) / L
    return [((x0 + s * nx * w / 2, y0 + s * ny * w / 2), (x1 + s * nx * w / 2, y1 + s * ny * w / 2)) for s in (1, -1)]


def _set(path):
    doc = ezdxf.new("R2018")
    doc.header["$INSUNITS"] = 4
    m = doc.modelspace()

    def frame(x0, title):
        m.add_lwpolyline([(x0, 0), (x0 + 40000, 0), (x0 + 40000, 28000), (x0, 28000)], close=True,
                         dxfattribs={"layer": "FRAME"})
        m.add_text(title, dxfattribs={"layer": "S-TEXT", "height": 400}).set_placement((x0 + 1000, 26500))

    def txt(s, x, y, h=200):
        m.add_text(s, dxfattribs={"layer": "S-TEXT", "height": h}).set_placement((x, y))

    def line(a, b, layer):
        m.add_line(a, b, dxfattribs={"layer": layer})
    frame(0, "FOUNDATION PLAN")
    for mk, (x, y, s) in F.items():
        m.add_lwpolyline([(x, y), (x + s, y), (x + s, y + s), (x, y + s)], close=True,
                         dxfattribs={"layer": "S-FOOTINGS"})
        txt(mk[:2], x + 100, y + 100)
    line((5800, 5400), (12700, 5400), "S-FOOTINGS")          # SB1 faces, 0.70 apart
    line((5800, 6100), (12700, 6100), "S-FOOTINGS")
    txt("S.B1", 9000, 5650, 150)
    for a, b in _sb2_faces():
        line(a, b, "S-FOOTINGS")
    sb2 = m.add_text("S.B2", dxfattribs={"layer": "S-TEXT", "height": 150,
                                         "rotation": math.degrees(math.atan2(6900, 3900))})
    sb2.set_placement((14900, 9400))
    # ground-beam plan: a ring of 0.30 bands, an interior band, a 0.95 slab strip in four pieces per face
    X = 45000
    frame(X, "GROUND BEAMS PLAN")
    ox, oy = X + 3000, 3000
    for (a, b) in (((0, 0), (10000, 0)), ((10000, 0), (10000, 6000)), ((10000, 6000), (0, 6000)), ((0, 6000), (0, 0)),
                   ((300, 300), (9700, 300)), ((9700, 300), (9700, 5700)), ((9700, 5700), (300, 5700)),
                   ((300, 5700), (300, 300)), ((5000, 300), (5000, 5700)), ((5300, 300), (5300, 5700))):
        line((ox + a[0], oy + a[1]), (ox + b[0], oy + b[1]), "S-GB")
    for k in range(4):
        y0, y1 = 300 + k * 1350, 300 + (k + 1) * 1350
        line((ox + 7000, oy + y0), (ox + 7000, oy + y1), "S-GB")
        line((ox + 7950, oy + y0), (ox + 7950, oy + y1), "S-GB")
    frame(90000, "SCHEDULE OF FOOTINGS AND STRAP BEAMS")

    def table(name, tags, rows, y0):
        blk = doc.blocks.new(name)
        for k, t in enumerate(tags):
            blk.add_attdef(t, (k * 800, 0), dxfattribs={"height": 150, "layer": "S-SCHED"})
        for n, vals in enumerate(rows):
            ins = m.add_blockref(name, (91000, y0 - 600 * n), dxfattribs={"layer": "S-SCHED"})
            ins.add_auto_attribs(dict(zip(tags, [str(v) for v in vals])))
    table("FTG_ROW", ("FO-TY", "W", "H", "DEPHT", "SH-B", "SH-D", "LO-B", "LO-D"),
          [("F1", 150, 150, 50, 7, 12, 7, 12), ("F2", 150, 150, 50, 7, 12, 7, 12), ("F3", 180, 180, 50, 8, 12, 8, 12)],
          24000)
    table("SB_ROW", ("BEAM", "W", "H", "BOT-B", "BOT-D", "TOP-B", "TOP-D", "STI-B", "D"),
          [("SB1", 70, 50, 4, 16, 4, 16, 5, 10), ("SB2", 80, 50, 4, 18, 4, 18, 5, 10),
           ("SB2", 100, 50, 6, 18, 6, 18, 5, 10)], 20000)
    doc.saveas(path)
    return path


def _conv():
    gen = json.loads((ROOT / "engine/profiles/URBAN_M3_GENERIC_CONVENTIONS_V2.json").read_text())
    num = lambda i, b, lo, hi: {"id": i, "title": i, "kind": "number", "unit": "m", "base": b, "low": lo, "high": hi,
                                "provenance": "PRINTED_VALUE", "source": "test", "rationale": "test"}
    prof = {"profile": "T", "conventions": [
        {"id": "GB_TYPICAL_SECTIONS", "title": "t", "kind": "choice", "options": ["T"], "base": "T",
         "classes": [{"max_span_m": 2.5, "W": 0.3, "H": 0.3}, {"max_span_m": 5.0, "W": 0.3, "H": 0.4},
                     {"max_span_m": None, "W": 0.3, "H": 0.6}],
         "provenance": "READING_OF_PRINTED_VALUE", "source": "test", "rationale": "test"},
        num("GF_FLOOR_LEVEL_M", 1.0, 1.0, 1.0), num("OUTER_GROUND_LEVEL_M", 0.0, 0.0, 0.15),
        {"id": "GB_EXTERIOR_DETAIL", "title": "e", "kind": "choice", "options": ["E"], "base": "E", "W": 0.3,
         "provenance": "READING_OF_PRINTED_VALUE", "source": "test", "rationale": "test"}]}
    return GR.merge_conventions(gen, prof)


def _evidence(ocr=False):
    recs, k = [], [0]

    def r(text):
        k[0] += 1
        x = DE.manual_record(f"EV-{k[0]:04d}", page=13, region=(0, 0, 10, 5), text=text, by="test", on="2026-10-11")
        if ocr:
            x.update(method="OCR_TESSERACT", state="OCR_UNREVIEWED", confirmed_by=None, confirmed_on=None,
                     reads=[{"text": text}, {"text": text}])
        recs.append(x)
        return x
    dets = [DE.manual_detail("D1", "Ground Beams. More than 5m length (1:20)",
                             [("TOP", r("3Ø16")), ("LINKS", r("Ø8/15")), ("BOTTOM", r("6Ø16"))], page=13),
            DE.manual_detail("D2", "Ground Beams. Less than 5m length (1:20)",
                             [("TOP", r("3Ø14")), ("BOTTOM", r("6Ø14"))], page=13),
            DE.manual_detail("D3", "Ground Beams. for exterior walls (1:20)",
                             [("TOP", r("3Ø16")), ("SIDE", r("2Ø12/30cm")), ("LINKS", r("Ø8/15")),
                              ("BOTTOM", r("6Ø16"))], page=13)]
    return {"schema": DE.SCHEMA, "records": recs, "details": dets}


@pytest.fixture(scope="module")
def drawing(tmp_path_factory):
    p = _set(tmp_path_factory.mktemp("gb") / "gb.dxf")
    I = UI.read(p)
    return I, GR.detect(I, typical_widths_m=GR.typical_gb_widths(_conv()))


def _sheet(D, role):
    return next(r for r in D["sheets"].values() if r["sheet"]["role"] == role)


def test_dotted_marks_and_duplicate_row_widths():
    assert DM.mark_family("S.B2") == ("STRAP_BEAM", "SB2") and DM.mark_family("G.B.1") == ("GROUND_BEAM", "GB1")
    assert DM.mark_family("C.L")[0] is None and DM.mark_family("F.F.L+1.00")[0] is None
    band = {"band_id": "B", "width_native": 1000.0, "kind": "STRAIGHT", "u": (1.0, 0.0),
            "polygon": [(0, 0), (5000, 0), (5000, 1000), (0, 1000)]}
    m = {"mark": "SB2", "family": "STRAP_BEAM", "x": 2500, "y": 500, "h": 150, "rot": 0.0}
    assert MD.bind_marks([band], [m], {("STRAP_BEAM", "SB2"): (0.8, 1.0)}, 0.001)[0]["state"] == "BOUND"
    assert MD.bind_marks([band], [m], {("STRAP_BEAM", "SB2"): 0.8}, 0.001)[0]["state"] == "BOUND_WIDTH_CONFLICT"


def test_straps_between_footings(drawing):
    I, D = drawing
    st = _sheet(D, "FOUNDATION_PLAN")["straps"]
    by = {b["mark"]: b for b in st["bands"]}
    assert set(by) == {"SB1", "SB2"} and st["between_footings"] >= 1 and not st["unbound_candidates"]
    assert by["SB1"]["state"] == "BOUND" and by["SB1"]["length_m"] == pytest.approx(5.5)
    assert by["SB2"]["state"] == "BOUND_ROW_BY_DRAWN_WIDTH" and by["SB2"]["schedule_width_m"] == pytest.approx(1.0)
    shapely = pytest.importorskip("shapely.geometry")
    a, b = _sb2_faces()                                     # the band lies between the drawn faces (0.99)
    band = shapely.Polygon([a[0], a[1], b[1], b[0]])
    for mk in ("F2", "F3"):
        x, y, s = F[mk]
        band = band.difference(shapely.box(x, y, x + s, y + s))
    assert by["SB2"]["net_plan_m2"] == pytest.approx(band.area * 1e-6, rel=1e-3)
    items, reg, risk = GR.items_from(D, _conv(), {})
    PE.check(items, _conv())
    c = {i["component_id"]: i for i in items if i["trade"] == "CONCRETE" and i["storey"] == "FOUNDATION" and
         i["family"] == "GROUND_BEAMS"}
    sb1 = next(i for i in c.values() if "SB1" in i["source"])
    sb2 = next(i for i in c.values() if "SB2" in i["source"])
    assert (sb1["low"], sb1["base"], sb1["high"]) == pytest.approx((1.925, 1.925, 1.925))
    v = by["SB2"]["net_plan_m2"] * 0.5
    assert sb2["base"] == pytest.approx(v) and sb2["low"] == pytest.approx(v * 0.8 / 1.0)
    assert sb2["blocker"] == "SCHEDULE_DUPLICATE_MARK" and sb2["confidence"] == "LOW"


def test_ground_beam_widths_are_source_supported(drawing, tmp_path_factory):
    I, D = drawing
    g = _sheet(D, "GROUND_BEAM_PLAN")
    assert 0.95 in g["width_basis"]["REJECTED_DRAWN_MODES"]
    assert {round(b["width_m"], 2) for b in g["beams"]} == {0.3}
    D0 = GR.detect(I)                                       # M2 behaviour: no printed typical width
    g0 = _sheet(D0, "GROUND_BEAM_PLAN")
    assert 0.95 in {round(b["width_m"], 2) for b in g0["beams"]}
    panel = sum(f["area_m2"] for f in g["slab"]["faces"] if f["class"] == "PANEL")
    panel0 = sum(f["area_m2"] for f in g0["slab"]["faces"] if f["class"] == "PANEL")
    assert panel - panel0 == pytest.approx(0.95 * 5.4, rel=1e-3)         # the strip is slab again


def test_perimeter_bands_take_the_exterior_detail(drawing):
    I, D = drawing
    g = _sheet(D, "GROUND_BEAM_PLAN")
    sides = g["band_sides"]
    long_ = {b["band_id"]: b for b in g["beams"]}
    interior = [k for k, b in long_.items() if abs(b["length_m"] - 5.4) < 1e-6 and b["width_m"] == pytest.approx(0.3)
                and "OUTSIDE" not in sides[k]]
    assert len(interior) == 1
    assert sum(1 for k in long_ if "OUTSIDE" in sides[k]) == 4
    conv = _conv()
    items, reg, risk = GR.items_from(D, conv, {})
    PE.check(items, conv)
    c = {i["component_id"].split(":")[-1]: i for i in items if i["family"] == "GROUND_BEAMS" and
         i["storey"] == "GROUND" and i["trade"] == "CONCRETE"}
    assert c[interior[0]]["base"] == pytest.approx(0.3 * 5.4 * 0.6)
    bottom = next(k for k, b in long_.items() if abs(b["length_m"] - 9.4) < 1e-6 and
                  min(y for _, y in b["polygon"]) == pytest.approx(3000.0))
    it = c[bottom]
    assert (it["low"], it["base"], it["high"]) == pytest.approx((2.82 * 0.6, 2.82 * 0.9, 2.82 * 1.0))
    assert it["blocker"] == "GB_EXTERIOR_DEPTH" and "OUTER_GROUND_LEVEL_M" in it["assumptions"]


def test_typical_bars_from_detail_evidence(drawing):
    I, D = drawing
    conv = _conv()
    g = _sheet(D, "GROUND_BEAM_PLAN")
    interior = next(b for b in g["beams"] if abs(b["length_m"] - 5.4) < 1e-6 and "OUTSIDE" not in
                    g["band_sides"][b["band_id"]])
    items, reg, risk = GR.items_from(D, conv, {}, evidence=_evidence())
    PE.check(items, conv)
    cid = f"GROUND_BEAMS:GROUND:{interior['band_id']}"
    s = {i["item_id"].split(":")[-2] + ":" + i["item_id"].split(":")[-1]: i for i in items
         if i["component_id"] == cid and i["trade"] == "REINFORCEMENT"}
    L = 5.4
    assert s["TOP:D16"]["base"] == pytest.approx(3 * (L + 2 * 40 * 0.016) * 16 ** 2 / 162, rel=1e-3)
    assert s["BOTTOM:D16"]["base"] == pytest.approx(6 * (L + 2 * 40 * 0.016) * 16 ** 2 / 162, rel=1e-3)
    link = BS.closed_link(0.3, 0.6, 0.025, 8, table="ACI_318_19")["developed_m"]
    assert s["LINKS:D8"]["base"] == pytest.approx((L / 0.15 + 1) * BS.mass_kg(link, 8), rel=1e-6)
    assert all(i["blocker"] != "OCR_DERIVED_UNREVIEWED" for i in s.values())      # a person transcribed them
    st = {r["COMPONENT_ID"]: r["REBAR_STATE"] for r in reg}
    assert st[cid] == "PROVISIONAL_MODEL"
    # the < 5 m class prints no links: the link steel is UNRESOLVED, never zero
    short = [b for b in g["beams"] if b["length_m"] + 0.3 < 5.0 and "OUTSIDE" not in g["band_sides"][b["band_id"]]]
    for b in short:
        c2 = f"GROUND_BEAMS:GROUND:{b['band_id']}"
        assert st[c2] == "PARTIAL_MISSING"
        assert any(i["item_id"] == f"U-S:{c2}:LINKS" and i["category"] == "UNRESOLVED" for i in items)
    # OCR-derived records stay provisional / low / unreviewed
    items2, _, _ = GR.items_from(D, conv, {}, evidence=_evidence(ocr=True))
    ocr = [i for i in items2 if i["component_id"] == cid and i["trade"] == "REINFORCEMENT"]
    assert ocr and all(i["category"] == "PROVISIONAL" and i["confidence"] == "LOW" and
                       i["blocker"] == "OCR_DERIVED_UNREVIEWED" for i in ocr)


def test_without_evidence_ground_beam_bars_stay_missing(drawing):
    I, D = drawing
    items, reg, risk = GR.items_from(D, _conv(), {})
    gb = [r for r in reg if r["FAMILY"] == "GROUND_BEAMS" and r["STOREY"] == "GROUND"]
    assert gb and all(r["REBAR_STATE"] == "MISSING_DATA" for r in gb)
    assert not any(i["trade"] == "REINFORCEMENT" and i["storey"] == "GROUND" and i["family"] == "GROUND_BEAMS"
                   for i in items)
