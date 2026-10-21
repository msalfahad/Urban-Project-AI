"""M6 completeness engine V2 rules, one hand-built fixture each (the roof-slab plan of test_cc_ledgers plus what each
rule is about; every fact set by hand, every expected state derived here):

  - a mark the route could not bind (AMBIGUOUS) beside an unmarked, unresolved band is reported, never consumed by
    that band; beside a band that carries the same mark it is consumed; a scheduled type whose only plan mark is
    unbound is still placed (no SCHEDULED_NOT_PLACED for it)
  - fills are read on a hatch-named layer: the plan's column fill inside the columns is explained; another pattern on
    a measured beam is HATCH_ON_MEASURED_MEMBER naming the beam's item; a legend swatch off the building names the
    family of the fills with its pattern and layer, and the swatch itself is no finding
  - a footing explains only footing / column linework inside it: pit walls drawn inside a measured footing on a
    wall layer are a finding, and a pit-sized ring on a substructure plan is a lift or tank candidate
"""

from __future__ import annotations

import copy

from .test_cc_ledgers import _band, _seg, _text, build                  # noqa: I001 (puts the repo on sys.path)
from engine.source import concrete_completeness as CC                     # noqa: E402


def _rect(k, x0, y0, x1, y1, layer):
    p = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
    return [_seg(f"{k}{i}", p[i], p[(i + 1) % 4], layer) for i in range(4)]


def _hatch(hid, x0, y0, x1, y1, layer, pattern):
    return {"id": hid, "layer": layer, "pattern": pattern, "ring": [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]}


def test_an_unbound_mark_is_reported_beside_an_unresolved_band():
    D, intake, items = build()
    rec = D["sheets"]["SH01"]
    rec["bands"].append(_band("BAND0006", 13.0, 5.2, 13.2, 12.8))            # an unmarked band: route left it unbound
    rec["beams"].append({"band_id": "BAND0006", "mark": None, "depth_m": None, "state": "UNBOUND"})
    items.append({"item_id": "U-C:BEAMS:GF:BAND0006", "component_id": "BEAMS:GF:BAND0006", "trade": "CONCRETE",
                  "family": "BEAMS", "storey": "GF", "category": "UNRESOLVED", "base": 0.0,
                  "source": "x.dxf SH01 band", "dimensions": {}})
    t9 = _text(9, "B9", 13.35, 9.0)                                          # scheduled type, ambiguous on the plan
    t10 = _text(10, "B1", 7.0, 4.85)                                         # ambiguous beside a band measured as B1
    D["model"]["texts"] += [t9, t10]                                         # (the sheet record shares this list)
    rec["marks"] += [{"text_id": "T9", "state": "AMBIGUOUS", "mark": "B9"},
                     {"text_id": "T10", "state": "AMBIGUOUS", "mark": "B1"}]
    rep = CC.assess(D, intake, items, heights={"GF": 4.0, "1F": 3.5})
    lab = {s["TEXT_ID"]: s for s in rep["signals"] if s["LEDGER"] == "LABELS"}
    assert lab["T9"]["STATE"] == "NOT_CONSUMED"
    assert "route state AMBIGUOUS" in lab["T9"]["REASON"] and "BAND0006 held unresolved" in lab["T9"]["REASON"]
    assert lab["T10"]["STATE"] == "CONSUMED_BY_PROXIMITY" and "BAND0001" in lab["T10"]["REASON"]
    f = [f for f in rep["findings"] if f["KIND"] == "LABEL_NOT_CONSUMED" and f["REFS"] == "T9"]
    assert len(f) == 1 and f[0]["FAMILY"] == "BEAMS"
    assert not any(f["KIND"] == "SCHEDULED_NOT_PLACED" and " B9 " in f["EVIDENCE"] for f in rep["findings"])


def test_fills_column_fill_hatch_on_a_beam_and_a_legend():
    D, intake, items = build()
    hs = [_hatch(f"HC{n}", *c, "S-COL.HAT", "SOLID") for n, c in enumerate(D["sheets"]["SH01"]["column_presence"])]
    hs.append(_hatch("HB1", 6.0, 5.0, 7.5, 5.2, "S-HAT.BAT", "ANSI31"))        # on BAND0001, no legend for ANSI31
    hs.append(_hatch("HB2", 10.0, 12.8, 11.0, 13.0, "S-HAT.BAT", "ANSI37"))    # on BAND0002
    hs.append(_hatch("HL1", 17.0, 3.0, 17.6, 3.4, "S-HAT.BAT", "ANSI37"))      # legend swatch off the building
    t = _text(12, "CANTILEVER SLAB", 17.8, 3.1)
    D["model"]["texts"].append(t)
    intake["hatches"] = hs
    rep = CC.assess(D, intake, items, heights={"GF": 4.0, "1F": 3.5})
    hom = {f["REFS"]: f for f in rep["findings"] if f["KIND"] == "HATCH_ON_MEASURED_MEMBER"}
    assert set(hom) == {"HB1", "HB2"}                                       # column fills explained, swatch not found
    assert hom["HB1"]["FAMILY"] == "UNKNOWN" and "could be CANTILEVER" in hom["HB1"]["EVIDENCE"]
    assert hom["HB1"]["ITEMS"] == "P-C:BEAMS:GF:BAND0001" and abs(hom["HB1"]["MAGNITUDE"]["hatch_area_m2"] - 0.3) < 1e-9
    assert hom["HB2"]["FAMILY"] == "CANTILEVER" and "legend: CANTILEVER SLAB" in hom["HB2"]["EVIDENCE"]
    assert all(f["VOLUME_HIGH_M3"] is None for f in hom.values())          # a mark on a member, never a quantity
    assert rep["geometry_stats"]["fills_explained"] == 4


def _foundation(D, intake, items, pit_layer):
    """a second sheet: a foundation plan with one measured 4 x 4 m footing and pit walls drawn inside it."""
    D = copy.deepcopy({k: v for k, v in D.items() if k != "model"}) | {"model": D["model"]}
    box2 = (50.0, 0.0, 90.0, 30.0)
    sh2 = {"sheet_id": "SH02", "box": box2, "origin": (50.0, 0.0), "role": "FOUNDATION_PLAN", "storey": "FOUNDATION"}
    mid = "FTG:SH02:F1@62000,12000:a1"
    D["sheets"]["SH02"] = {"sheet": sh2, "footings": [{"member_id": mid, "mark": "F1", "state": "BOUND",
                                                       "polygon": [(60.0, 10.0), (64.0, 10.0), (64.0, 14.0),
                                                                   (60.0, 14.0)]}], "texts": [], "marks": []}
    D["model"] = dict(D["model"], sheets=D["model"]["sheets"] + [sh2],
                      sheet_of=lambda x, y: "SH01" if CC._in_box((0.0, 0.0, 40.0, 30.0), x, y) else
                      "SH02" if CC._in_box(box2, x, y) else None)
    intake = dict(intake, segments=intake["segments"] + _rect("F", 60.0, 10.0, 64.0, 14.0, "S-FTG") +
                  _rect("PO", 60.5, 10.5, 63.5, 13.5, pit_layer) + _rect("PI", 60.7, 10.7, 63.3, 13.3, pit_layer))
    items = items + [{"item_id": "P-C:FOOTINGS:FOUNDATION:" + mid, "component_id": "FOOTINGS:FOUNDATION:" + mid,
                      "trade": "CONCRETE", "family": "FOOTINGS", "storey": "FOUNDATION", "category": "PROVISIONAL",
                      "base": 4.0, "source": "x.dxf SH02 footing", "dimensions": {}}]
    return D, intake, items


def test_pit_walls_inside_a_footing_are_not_the_footing():
    D, intake, items = _foundation(*build(), pit_layer="S-BW")
    rep = CC.assess(D, intake, items, heights={"GF": 4.0, "1F": 3.5})
    pit = [f for f in rep["findings"] if f["KIND"] == "DRAWN_NOT_MEASURED" and f["SHEET"] == "SH02"]
    assert len(pit) == 1 and pit[0]["BOX_M"] == (10.5, 10.5, 13.5, 13.5)
    assert pit[0]["MAGNITUDE"].get("pit") is True and pit[0]["FAMILY"] == "UNKNOWN"
    assert "could be LIFT or WALLS or WATER_TANK" in pit[0]["EVIDENCE"]     # a wall layer and a pit-sized ring
    sig = [s for s in rep["signals"] if s["LEDGER"] == "GEOMETRY" and s["SHEET"] == "SH02"]
    assert {s["STATE"] for s in sig} == {"DRAWN_NOT_MEASURED"}              # the footing's own lines are explained


def test_footing_layer_content_is_still_the_footing():
    D, intake, items = _foundation(*build(), pit_layer="S-FTG")              # a stepped footing drawn on its layer
    rep = CC.assess(D, intake, items, heights={"GF": 4.0, "1F": 3.5})
    assert not [f for f in rep["findings"] if f["KIND"] == "DRAWN_NOT_MEASURED" and f["SHEET"] == "SH02"]
