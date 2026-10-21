"""M3 WP1 regression: footing occurrences the M2 generic route lost on ST7757, re-created generically on a hand-made
foundation plan with hand-derived truth (schedule sizes x depth; polygon area by hand):

    F1   outline drawn, label inside                                  -> CONFIRMED 1.5 x 1.3 x 0.45 = 0.8775
    FF   doubled-letter type mark (M2's mark pattern refused it)      -> CONFIRMED 2.4 x 2.2 x 0.50 = 2.64
    F3   1.0 x 1.0 polyline clipped 0.3 x 0.2 where it meets F1       -> CONFIRMED (1 - 0.06) x 0.30 = 0.282
    F4   2.6 x 1.2 outline open where a strap enters; label 1.0 m off -> CONFIRMED 2.6 x 1.2 x 0.40 = 1.248
    F2   label only, no outline anywhere                              -> PROVISIONAL schedule size 2.0 x 2.0 x 0.5 = 2.0
    F5 / F6 two labels 1.0 m apart, no outline                         -> ONE footing, larger type base (F6 1.215),
                                                                          smaller (F5 0.405) as the low bound
    F1 nested twin outline (a 0.6 x 0.6 pedestal inside F1)           -> never counted
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

ezdxf = pytest.importorskip("ezdxf")

from engine.source import generic_route as GR              # noqa: E402
from engine.source import provisional_estimate as PE       # noqa: E402
from tools import urban_intake as UI                       # noqa: E402

SCHED = [("F1", 150, 130, 45), ("F2", 200, 200, 50), ("FF", 240, 220, 50), ("F3", 100, 100, 30),
         ("F4", 260, 120, 40), ("F5", 90, 100, 45), ("F6", 180, 150, 45)]


def _plan(path):
    doc = ezdxf.new("R2018")
    doc.header["$INSUNITS"] = 4
    m = doc.modelspace()
    for lay in ("S-FOOTINGS", "S-STRAP", "S-TEXT", "S-SCHED", "FRAME"):
        doc.layers.add(lay)

    def frame(x0):
        m.add_lwpolyline([(x0, 0), (x0 + 40000, 0), (x0 + 40000, 28000), (x0, 28000)], close=True,
                         dxfattribs={"layer": "FRAME"})

    def txt(s, x, y, h=200):
        m.add_text(s, dxfattribs={"layer": "S-TEXT", "height": h}).set_placement((x, y))

    def rect(x, y, w, h):
        m.add_lwpolyline([(x, y), (x + w, y), (x + w, y + h), (x, y + h)], close=True,
                         dxfattribs={"layer": "S-FOOTINGS"})
    frame(0)
    frame(45000)
    txt("FOUNDATION PLAN", 1000, 26500, 400)
    txt("SCHEDULE OF FOOTINGS", 46000, 26500, 400)
    # F1 with its label, and a nested 0.6 x 0.6 pedestal outline inside it
    rect(5000, 5000, 1500, 1300)
    rect(5450, 5350, 600, 600)
    txt("F1", 5100, 5100)
    # F3: 1.0 x 1.0 clipped 0.3 x 0.2 at its lower-left corner where it meets F1's upper-right corner region
    x0, y0 = 6200, 6100
    m.add_lwpolyline([(x0 + 300, y0), (x0 + 1000, y0), (x0 + 1000, y0 + 1000), (x0, y0 + 1000), (x0, y0 + 200),
                      (x0 + 300, y0 + 200)], close=True, dxfattribs={"layer": "S-FOOTINGS"})
    txt("F3", x0 + 500, y0 + 500)
    # FF
    rect(10000, 5000, 2400, 2200)
    txt("FF", 10200, 5200)
    # F4: open along its top side where a strap (two inclined lines) enters; label 0.8 m left of the outline
    X, Y = 15000, 5000
    for a, b in (((X, Y), (X + 2600, Y)), ((X + 2600, Y), (X + 2600, Y + 1200)), ((X + 2600, Y + 1200),
                                                                                   (X + 1600, Y + 1200)),
                 ((X + 1000, Y + 1200), (X, Y + 1200)), ((X, Y + 1200), (X, Y))):
        m.add_line(a, b, dxfattribs={"layer": "S-FOOTINGS"})
    m.add_line((X + 1000, Y + 1200), (X + 1000, Y + 4200), dxfattribs={"layer": "S-FOOTINGS"})   # strap faces
    m.add_line((X + 1600, Y + 1200), (X + 1600, Y + 4200), dxfattribs={"layer": "S-FOOTINGS"})
    txt("F4", X - 1000, Y + 500)
    # F2: label only
    txt("F2", 20000, 12000)
    # F5 / F6: two labels 1.0 m apart, no outline
    txt("F5", 26000, 12000)
    txt("F6", 27000, 12000)
    # the schedule as attribute rows
    tags = ("FO-TY", "W", "H", "DEPHT", "SH-B", "SH-D", "LO-B", "LO-D")
    blk = doc.blocks.new("FTG_ROW")
    for k, t in enumerate(tags):
        blk.add_attdef(t, (k * 800, 0), dxfattribs={"height": 150, "layer": "S-SCHED"})
    for n, (mk, W, H, D) in enumerate(SCHED):
        ins = m.add_blockref("FTG_ROW", (46000, 24000 - 600 * n), dxfattribs={"layer": "S-SCHED"})
        ins.add_auto_attribs(dict(zip(tags, [mk, str(W), str(H), str(D), "7", "12", "7", "12"])))
    doc.saveas(path)
    return path


@pytest.fixture(scope="module")
def run(tmp_path_factory):
    p = _plan(tmp_path_factory.mktemp("ftg") / "ftg.dxf")
    D = GR.detect(UI.read(p))
    root = Path(__file__).resolve().parents[2]
    conv = GR.merge_conventions(json.loads((root / "engine/profiles/URBAN_M3_GENERIC_CONVENTIONS_V2.json").read_text()))
    items, reg, risk = GR.items_from(D, conv, {})
    PE.check(items, conv)
    sheet = next(r for r in D["sheets"].values() if r.get("footings"))
    return sheet["footings"], [i for i in items if i["family"] == "FOOTINGS" and i["trade"] == "CONCRETE"], risk


def _by(fts, mark):
    return [f for f in fts if f["mark"] == mark]


def test_every_footing_label_is_quantified_once(run):
    fts, items, risk = run
    states = {f["mark"]: f["state"] for f in fts}
    assert states["F1"] == "CONFIRMED" and states["FF"] == "CONFIRMED" and states["F3"] == "CONFIRMED"
    assert states["F4"] == "CONFIRMED" and states["F2"] == "LABEL_ONLY"
    assert {states["F5"], states["F6"]} == {"LABEL_TYPE_CONFLICT", "LABEL_TYPE_CONFLICT_SECONDARY"}
    assert len(items) == 6                                       # F1, FF, F3, F4, F2, the F5/F6 footing (once)
    assert not any(i["category"] == "UNRESOLVED" for i in items)


def test_quantities_by_hand(run):
    fts, items, risk = run
    by = {}
    for i in items:
        f = next(f for f in fts if f["member_id"] == i["component_id"])
        by[f["mark"]] = i
    assert by["F1"]["base"] == pytest.approx(1.5 * 1.3 * 0.45)
    assert by["FF"]["base"] == pytest.approx(2.4 * 2.2 * 0.50)
    assert by["F3"]["base"] == pytest.approx((1.0 - 0.3 * 0.2) * 0.30)          # the clipped corner is F1's
    assert by["F4"]["base"] == pytest.approx(2.6 * 1.2 * 0.40)
    assert by["F2"]["base"] == pytest.approx(2.0 * 2.0 * 0.50) and by["F2"]["confidence"] == "LOW"
    pair = by.get("F5") or by.get("F6")
    assert (pair["low"], pair["base"], pair["high"]) == pytest.approx((0.9 * 1.0 * 0.45, 1.8 * 1.5 * 0.45,
                                                                       1.8 * 1.5 * 0.45))


def test_bindings_and_risk_records(run):
    fts, items, risk = run
    assert _by(fts, "F4")[0]["binding"] == "LABEL_OUTSIDE_NEAREST_OUTLINE"
    assert _by(fts, "F3")[0]["outline_kind"] == "POLYGON"
    kinds = [r["KIND"] for r in risk]
    assert "FOOTING_LABEL_ONLY" in kinds and "FOOTING_LABEL_TYPE_CONFLICT" in kinds
