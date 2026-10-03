"""Synthetic dimensions for DIMENSION_OWNER_STATUS. No P7757 value."""

from __future__ import annotations

from PIL import Image, ImageDraw

from engine import dimension_owner as D


def _rect(x0, y0, x1, y1):
    return [[x0, y0], [x1, y0], [x1, y1], [x0, y1]]


def _wall(tid, poly, status="TRACE_ESTABLISHED", ct="WALL_SEGMENT"):
    return {"TRACE_ID": tid, "CLAIM_TYPE": ct, "EFFECTIVE_CLAIM_TYPE": ct,
            "SHEET_ID": "S", "PIXEL_POLYGON": poly, "VISUAL_TRACE_STATUS": status}


def _dim(tid, a, b, value=1.0, dstatus="ESTABLISHED", sheet="S"):
    return {"TRACE_ID": tid, "CLAIM_TYPE": "HEIGHT_DIMENSION",
            "EFFECTIVE_CLAIM_TYPE": "HEIGHT_DIMENSION", "SHEET_ID": sheet,
            "VALUE_M": value, "DIMENSION_STATUS": dstatus,
            "EXTENSION_LINE_A": a, "EXTENSION_LINE_B": b,
            "DIMENSION_LINE_TRACE": [[a[1][0], a[1][1]], [b[1][0], b[1][1]]]}


def test_owner_established_when_both_ends_land_on_one_element():
    par = _wall("PAR-1", _rect(0, 100, 100, 150), ct="PARAPET")   # top y=100, base y=150
    dim = _dim("DIM-1", [[100, 100], [140, 100]], [[100, 150], [140, 150]], 0.5)
    r = D.resolve([par, dim])[0]
    assert r["DIMENSION_OWNER_STATUS"] == "OWNER_ESTABLISHED"
    assert r["OWNER_OBJECTS"] == ["PO:PAR-1"]
    assert r["TEXT_READ_ESTABLISHED"] is True
    assert r["OWNER_IS_SEPARATE_FROM_TEXT_READ"] is True


def test_owner_not_established_when_an_end_lands_on_nothing():
    par = _wall("PAR-1", _rect(0, 100, 100, 150), ct="PARAPET")
    dim = _dim("DIM-1", [[100, 100], [140, 100]], [[100, 400], [140, 400]], 3.0)
    r = D.resolve([par, dim])[0]
    assert r["DIMENSION_OWNER_STATUS"] == "OWNER_NOT_ESTABLISHED"
    assert r["TEXT_READ_ESTABLISHED"] is True       # the text was still read


def test_owner_provisional_on_unresolved_feature_and_ambiguous_on_two_objects():
    par = _wall("PAR-1", _rect(0, 100, 100, 150), ct="PARAPET")
    unk = _wall("UNK-1", _rect(0, 60, 100, 100), status="TRACE_PROVISIONAL",
                ct="UNRESOLVED_FEATURE")
    dim = _dim("DIM-1", [[100, 62], [140, 62]], [[100, 150], [140, 150]], 0.9)
    r = D.resolve([par, unk, dim])[0]
    assert r["DIMENSION_OWNER_STATUS"] == "OWNER_PROVISIONAL"
    col = _wall("COL-1", _rect(100, 90, 130, 160), ct="COLUMN")
    wall = _wall("SEG-1", _rect(130, 90, 200, 160))
    dim2 = _dim("DIM-2", [[100, 90], [200, 90]], [[100, 160], [200, 160]], 0.7)
    r2 = D.resolve([col, wall, dim2])[0]
    assert r2["DIMENSION_OWNER_STATUS"] == "OWNER_AMBIGUOUS"
    # declared as one object the ambiguity resolves
    r3 = D.resolve([col, wall, dim2], object_map={"PO-X": ["COL-1", "SEG-1"]})[0]
    assert r3["DIMENSION_OWNER_STATUS"] == "OWNER_ESTABLISHED"


def test_level_mark_is_a_legitimate_datum_end():
    par = _wall("PAR-1", _rect(0, 100, 100, 150), ct="PARAPET")
    lvl = {"TRACE_ID": "LVL-1", "CLAIM_TYPE": "LEVEL_MARK",
           "EFFECTIVE_CLAIM_TYPE": "LEVEL_MARK", "SHEET_ID": "S",
           "PIXEL_POINT": [120, 150], "VISUAL_TRACE_STATUS": "TRACE_ESTABLISHED"}
    dim = _dim("DIM-1", [[100, 100], [140, 100]], [[100, 150], [140, 150]], 0.5)
    r = D.resolve([par, lvl, dim])[0]
    assert r["DIMENSION_OWNER_STATUS"] == "OWNER_ESTABLISHED"
    roles = {h["ROLE"] for h in r["ENDS"]["EXTENSION_LINE_B"]["LANDS_ON"]}
    assert "LEVEL_DATUM" in roles


def test_ink_check_reports_presence_without_touching_owner_status():
    img = Image.new("L", (200, 200), 255)
    ImageDraw.Draw(img).line([(100, 100), (140, 100)], fill=0, width=1)
    par = _wall("PAR-1", _rect(0, 100, 100, 150), ct="PARAPET")
    dim = _dim("DIM-1", [[100, 100], [140, 100]], [[100, 150], [140, 150]], 0.5)
    r = D.resolve([par, dim], images={"S": img})[0]
    assert r["ENDS"]["EXTENSION_LINE_A"]["INK_FRACTION_ALONG_LINE"] >= 0.9
    assert r["ENDS"]["EXTENSION_LINE_B"]["INK_FRACTION_ALONG_LINE"] < 0.5
    assert r["EXTENSION_LINE_INK_PRESENT"] is False
    assert r["DIMENSION_OWNER_STATUS"] == "OWNER_ESTABLISHED"
