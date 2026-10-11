"""M6 completeness engine, ledger by ledger, on one hand-built roof-slab plan (metres, no drawing file): what the
takeoff holds explains its lines; an outline on an unknown layer, a label no member uses, a schedule row no plan
uses, a storey without a plan, columns drawn but not itemized (and itemized but not drawn), two overlapping beam
bands, a dependency note beside a beam, the plot line and a level mark. Each fact is set by hand; each expected
finding is derived here."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from engine.source import concrete_completeness as CC     # noqa: E402
from engine.source import drawing_model as DM              # noqa: E402

BOX = (0.0, 0.0, 40.0, 30.0)                 # the sheet frame (world = sheet-local: origin 0, 0)


def _seg(i, a, b, layer):
    return {"id": f"S{i}", "layer": layer, "a": a, "b": b, "path": [], "kind": "LINE"}


def _text(i, value, x, y, layer="S-TEXT"):
    norm = DM.normalize(value)
    fam, mark = DM.mark_family(norm)
    return {"id": f"T{i}", "value": value, "norm": norm, "x": x, "y": y, "layer": layer, "height": 0.2,
            "rotation": 0.0, "sheet": "SH01", "mark_family": fam, "mark": mark}


def _band(bid, x0, y0, x1, y1):
    return {"band_id": bid, "polygon": [(x0, y0), (x1, y0), (x1, y1), (x0, y1)], "parent": None, "state": "BOUND"}


def build():
    """a 10 x 8 m building at (5, 5): four perimeter beams 0.2 wide, one panel, four corner columns."""
    bands = [_band("BAND0001", 5.0, 5.0, 15.0, 5.2), _band("BAND0002", 5.0, 12.8, 15.0, 13.0),
             _band("BAND0003", 5.0, 5.2, 5.2, 12.8), _band("BAND0004", 14.8, 5.2, 15.0, 12.8),
             _band("BAND0005", 9.0, 5.0, 9.2, 13.0)]                    # crosses BAND0001 / BAND0002: overlap
    beams = [{"band_id": b["band_id"], "mark": "B1", "depth_m": 0.5, "state": "BOUND"} for b in bands]
    face = {"face_id": "FACE1", "polygon": [(5.2, 5.2), (14.8, 5.2), (14.8, 12.8), (5.2, 12.8)], "class": "PANEL",
            "region": "STRUCTURAL_SLAB", "area_m2": 72.96, "t_m": 0.16, "volume_m3": 11.67, "hole_polygons": [],
            "tag_ids": [], "opening_labels": []}
    cols = [(5.0, 5.0, 5.3, 5.3), (14.7, 5.0, 15.0, 5.3), (5.0, 12.7, 5.3, 13.0), (14.7, 12.7, 15.0, 13.0)]
    segs, k = [], 0
    for b in bands:                                                    # beam faces on the edge layer
        p = b["polygon"]
        for i in range(4):
            k += 1
            segs.append(_seg(k, p[i], p[(i + 1) % 4], "S-BEAM"))
    tank = [(10.0, 8.0), (12.0, 8.0), (12.0, 9.5), (10.0, 9.5)]        # an outline on an unknown layer, in the panel
    for i in range(4):
        k += 1
        segs.append(_seg(k, tank[i], tank[(i + 1) % 4], "9"))
    plot = [(2.0, 2.0), (25.0, 2.0), (25.0, 18.0), (2.0, 18.0)]        # the plot line round the building
    for i in range(4):
        k += 1
        segs.append(_seg(k, plot[i], plot[(i + 1) % 4], "S-BOUN"))
    lvl = [(7.0, 7.0), (7.25, 7.25), (6.75, 7.25)]                      # a level mark (small triangle)
    for i in range(3):
        k += 1
        segs.append(_seg(k, lvl[i], lvl[(i + 1) % 3], "4"))
    texts = [_text(1, "B7", 11.0, 11.5), _text(2, "AS PER ARCH.", 7.0, 5.5), _text(3, "+3.50", 7.3, 7.1),
             _text(4, "B1", 7.0, 5.3)]
    sheet = {"sheet_id": "SH01", "box": BOX, "origin": (0.0, 0.0), "role": "SLAB_PLAN", "storey": "GF"}
    rec = {"sheet": sheet, "bands": bands, "beams": beams, "slab": {"faces": [face]}, "slab_column_boxes": cols,
           "column_presence": cols, "texts": texts,
           "marks": [{"text_id": "T4", "state": "BOUND", "mark": "B1"}]}
    rows = [{"family": "BEAM", "mark": "B1", "source": "INSERT 10", "sheet": "SH09", "dims_m": {"W": 0.2, "H": 0.5}},
            {"family": "BEAM", "mark": "B9", "source": "INSERT 11", "sheet": "SH09", "dims_m": {"W": 0.2, "H": 0.6}},
            {"family": "COLUMN", "mark": "C1", "source": "INSERT 12", "sheet": "SH09", "dims_m": {"W": 0.3, "H": 0.3},
             "by_storey": {"GF": {}, "1F": {}}}]
    D = {"unit_m": 1.0, "sheets": {"SH01": rec},
         "model": {"sheets": [sheet], "texts": texts, "sheet_of": lambda x, y: "SH01" if CC._in_box(BOX, x, y)
                   else None},
         "schedule": {"rows": rows, "warnings": []}, "lib": {("BEAM", "B1"): rows[0], ("BEAM", "B9"): rows[1],
                                                             ("COLUMN", "C1"): rows[2]}}
    intake = {"segments": segs, "arcs": [], "circles": [], "hatches": [], "inserts": []}
    items = [{"item_id": f"P-C:BEAMS:GF:{b['band_id']}", "component_id": f"BEAMS:GF:{b['band_id']}",
              "trade": "CONCRETE", "family": "BEAMS", "storey": "GF", "category": "PROVISIONAL", "base": 1.0,
              "source": "x.dxf SH01 band", "dimensions": {"depth_m": 0.5}} for b in bands]
    items.append({"item_id": "P-C:SLABS:GF:FACE1", "component_id": "SLABS:GF:FACE1", "trade": "CONCRETE",
                  "family": "SLABS", "storey": "GF", "category": "PROVISIONAL", "base": 11.67,
                  "source": "x.dxf SH01 face", "dimensions": {}})
    for n, (x, y) in enumerate([(5.15, 5.15), (14.85, 5.15), (5.15, 12.85)], 1):      # three of the four corners
        items.append({"item_id": f"P-C:COL:SH09:C1@{x * 1000:.0f},{y * 1000:.0f}|GF",
                      "component_id": f"COL:SH09:C1@{int(x)},{int(y)}|GF", "trade": "CONCRETE",
                      "family": "COLUMNS", "storey": "GF", "category": "PROVISIONAL", "base": 0.36,
                      "source": "x.dxf SH09 mark C1", "dimensions": {}})
    items.append({"item_id": "P-C:COL:SH09:C1@30,25|GF", "component_id": "COL:SH09:C1@30,25|GF",
                  "trade": "CONCRETE", "family": "COLUMNS", "storey": "GF", "category": "PROVISIONAL", "base": 0.36,
                  "source": "x.dxf SH09 mark C1", "dimensions": {}})        # counted where no column is drawn
    return D, intake, items


def _run():
    D, intake, items = build()
    return CC.assess(D, intake, items, heights={"GF": 4.0, "1F": 3.5})


def _kinds(rep):
    return sorted(f["KIND"] for f in rep["findings"])


def test_member_lines_are_explained_and_the_unknown_outline_is_found():
    rep = _run()
    dnm = [f for f in rep["findings"] if f["KIND"] == "DRAWN_NOT_MEASURED"]
    assert len(dnm) == 1
    f = dnm[0]
    assert f["BOX_M"] == (10.0, 8.0, 12.0, 9.5) and f["FAMILY"] == "UNKNOWN"
    assert abs(f["MAGNITUDE"]["area_m2"] - 3.0) < 1e-9 and f["VOLUME_HIGH_M3"] is None     # no thickness: no volume
    states = {s["STATE"] for s in rep["signals"] if s["LEDGER"] == "GEOMETRY"}
    assert "PLOT_OR_OUTLINE" in states                                     # the plot line: context, not a finding
    assert "ANNOTATION_SYMBOL" in states                                   # the level mark beside its text


def test_labels_schedule_storeys():
    rep = _run()
    lab = [f for f in rep["findings"] if f["KIND"] == "LABEL_NOT_CONSUMED"]
    assert [f["EVIDENCE"].split()[1] for f in lab] == ["B7"]
    assert any(f["KIND"] == "PLACED_NOT_SCHEDULED" and "B7" in f["EVIDENCE"] for f in rep["findings"])
    assert any(f["KIND"] == "SCHEDULED_NOT_PLACED" and "B9" in f["EVIDENCE"] for f in rep["findings"])
    assert not any(f["KIND"] == "SCHEDULED_NOT_PLACED" and " B1 " in f["EVIDENCE"] for f in rep["findings"])
    miss = [f for f in rep["findings"] if f["KIND"] == "STOREY_PLAN_MISSING"]
    assert [f["STOREY"] for f in miss] == ["1F"]


def test_columns_one_to_one_both_directions():
    rep = _run()
    pres = [f for f in rep["findings"] if f["KIND"] == "COLUMN_PRESENCE_NOT_ITEMIZED"]
    assert len(pres) == 1 and pres[0]["BOX_M"] == (14.7, 12.7, 15.0, 13.0)
    assert abs(pres[0]["VOLUME_LOW_M3"] - 0.3 * 0.3 * 4.0) < 1e-9          # drawn outline x storey height
    over = [f for f in rep["findings"] if f["KIND"] == "COLUMN_ITEM_WITHOUT_PRESENCE"]
    assert len(over) == 1 and "30,25" in over[0]["ITEMS"]


def test_overlap_and_dependency():
    rep = _run()
    ov = [f for f in rep["findings"] if f["KIND"] == "MEMBER_OVERLAP"]
    assert len(ov) == 2                                                    # the cross beam over both edge beams
    assert all(abs(f["MAGNITUDE"]["overlap_m2"] - 0.04) < 1e-9 and abs(f["VOLUME_LOW_M3"] - 0.02) < 1e-9
               for f in ov)
    dep = [f for f in rep["findings"] if f["KIND"] == "DEPENDENCY"]
    assert len(dep) == 1 and "BAND0001" in dep[0]["EVIDENCE"] and dep[0]["ITEMS"] == "P-C:BEAMS:GF:BAND0001"


def test_scores_scope_and_rule():
    rep = _run()
    sc = rep["scores"]
    assert sc["labels_consumed_pct"] == 50.0                              # B1 by reference, B7 not
    assert sc["schedule_rows_placed_pct"] is not None and sc["findings_without_volume"] >= 1
    states = {r["FAMILY"]: r["STATE"] for r in rep["scope"]}
    assert states["BEAMS"] in ("MEASURED", "PARTLY_MEASURED") and states["POOL"] == "NO_EVIDENCE_CONFIRM_ABSENT"
    pops = {p["population"]: p["state"] for p in rep["populations"]} if isinstance(rep["populations"], list) else {}
    assert all(v != "NOT_PRESENT" for v in pops.values())                  # absence is never assumed
    assert "never a quantity" in rep["rule"] and "never a ratio" in rep["rule"]


def test_a_finding_never_enters_a_total():
    D, intake, items = build()
    before = sum(i["base"] for i in items)
    CC.assess(D, intake, items, heights={"GF": 4.0, "1F": 3.5})
    assert sum(i["base"] for i in items) == before and len(items) == 10   # the pass reads, never writes
