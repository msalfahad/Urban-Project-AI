"""T-075: column schedule rows typed as TEXT / MTEXT inside a block-attribute table, and struck-out cells
(engine/source/column_schedule_text_rows.py), against hand truth. Synthetic drawing, not a client drawing.

Hand schedule (drawing units mm, schedule values in cm; storey prefixes FDN. / GF. / 1F., mark tag TYPE):
    columns (tag x): TYPE 500 | FDN.W 1500 FDN.H 2500 FDN.R 3400 FDN.D 3900 | GF.W 5000 GF.H 6000 GF.R 6900 GF.D 7400 |
                     1F.W 8500 1F.H 9500 1F.R 10400 1F.D 10900 | NOTES column 11500..13000 with no tag
    grid verticals 0 1000 2000 3000 4500 5500 6500 8000 9000 10000 11500 13000 (the R and D of a level share one
    REINF cell); frame 0..13000 x 3000..7000; header band 6000..7000; data bands 500 high from y = 6000 down.
    band 0  SC1  ATTRIBUTE row: FDN 30x60 6/16, GF 25x60 6/16, 1F 20x50 6/16
    band 1  empty
    band 2  SC2  TEXT row: FDN 30x40 4/16, GF 25x40 4/16, 1F 20x40 4/14, NOTES 'SEE NOTE 3' (in no tag column)
    band 3  SC9  TEXT row: FDN 30x30 4/14; GF and 1F struck by ONE line y = 4250 from x = 4700 (80 % into the
                GF.W cell 4500..5500) to x = 11000 (in the 1F REINF cell 10000..11500)
    band 4  SC4  MTEXT cells (top-left attachment: insert at the text's top-left, near the band top): FDN 30x50, GF 25x50, 1F 20x50, bars 6/16
    band 5  SC5  TEXT row: FDN 30x45, GF.W 25 with GF.H BLANK and not struck, 1F 20x45
Hand results (metres):
    SC9  NECK_ONLY: neck section 0.30 x 0.30 = 0.090 m2, height HELD (founding datum, owner Q-21 = C);
        its column-plan symbol is NOT_PRESENT (no column above the foundation, struck cells as evidence)
    SC2  GF section 0.25 x 0.40 = 0.100 m2; 1F 0.20 x 0.40 = 0.080 m2; FDN 0.30 x 0.40 = 0.120 m2
    SC4  FDN 0.30 x 0.50 = 0.150 m2 (MTEXT read like TEXT)
    SC5  GF MISSING_CELL -> HELD, never 0 (FDN 0.30 x 0.45 = 0.135 m2 read)
    'SEE NOTE 3' reported UNBOUND; the frozen reader (attribute rows only) sees SC1 alone.
Variants: metres instead of mm, rotated 90 deg, mirrored, a 1e6 offset, all combined; the whole table in mm values;
adversarial: a mm text row in a cm table (held), a struck cell that carries a value (CONFLICT, held), a diagonal
strike, a strike that only touches a cell edge, no drawn frame (nothing read), a text row with two values in one cell.
"""

from __future__ import annotations

import copy
import math
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engine.source import column_schedule_text_rows as X  # noqa: E402
from engine.source import schedule_reader as SR  # noqa: E402

TAGS_X = {"TYPE": 500, "FDN.W": 1500, "FDN.H": 2500, "FDN.R": 3400, "FDN.D": 3900, "GF.W": 5000, "GF.H": 6000,
          "GF.R": 6900, "GF.D": 7400, "1F.W": 8500, "1F.H": 9500, "1F.R": 10400, "1F.D": 10900}
VERT = [0, 1000, 2000, 3000, 4500, 5500, 6500, 8000, 9000, 10000, 11500, 13000]
TOP, HEAD, BOTTOM, PITCH = 7000, 6000, 3000, 500


def band_mid(i):
    return HEAD - PITCH * i - PITCH / 2


def row_vals(mark, fdn, gf, f1):
    v = {"TYPE": mark}
    for p, cells in (("FDN", fdn), ("GF", gf), ("1F", f1)):
        for k, c in zip(("W", "H", "R", "D"), cells or (None,) * 4):
            if c is not None:
                v[f"{p}.{k}"] = str(c)
    return v


def base_drawing(values_scale=1):
    """the hand schedule above; values_scale 10 writes every size in mm instead of cm (bars unchanged)."""
    s = values_scale

    def sz(*v):
        return tuple(x * s if i < 2 and x is not None else x for i, x in enumerate(v))
    segs, texts, attrs = [], [], []

    def seg(a, b, sid):
        segs.append({"id": sid, "layer": "SCH-LINES", "a": a, "b": b, "kind": "LINE"})
    for x in VERT:
        if x in (0, 13000):
            seg((x, BOTTOM), (x, TOP), f"V{x}")
        else:
            seg((x, BOTTOM), (x, HEAD), f"V{x}")
    for k, y in enumerate([TOP, HEAD] + [HEAD - PITCH * i for i in range(1, 7)]):
        seg((0, y), (13000, y), f"H{k}")
    seg((-50, BOTTOM - 50), (13050, BOTTOM - 50), "HB2")                  # double border, outside the frame
    for x, t in ((500, "TYPE"), (2000, "FOUNDATION"), (6000, "GROUND"), (9500, "FIRST"), (12000, "NOTES")):
        texts.append({"id": f"HD{x}", "value": t, "x": x, "y": 6500, "layer": "SCH-TEXT", "height": 200,
                      "rotation": 0.0, "owner": None})
    k1 = row_vals("SC1", sz(30, 60, 6, 16), sz(25, 60, 6, 16), sz(20, 50, 6, 16))
    for tag, x in TAGS_X.items():
        attrs.append({"owner": "INS-SC1", "tag": tag, "value": k1.get(tag, ""), "x": x - 150, "y": band_mid(0) - 80})

    def text_row(band, vals, kind="TEXT"):
        for tag, v in vals.items():
            x = TAGS_X[tag]
            if kind == "MTEXT":                   # top-left attachment: the insert is the text's top-left corner
                p = (x - 60, HEAD - PITCH * band - 40)
            else:
                p = (x - 60, band_mid(band) - 70)
            texts.append({"id": f"{kind}{band}:{tag}", "value": v, "x": p[0], "y": p[1], "layer": "SCH-TEXT",
                          "height": 200, "rotation": 0.0, "owner": None})
    text_row(2, row_vals("SC2", sz(30, 40, 4, 16), sz(25, 40, 4, 16), sz(20, 40, 4, 14)))
    texts.append({"id": "NOTE2", "value": "SEE NOTE 3", "x": 11700, "y": band_mid(2), "layer": "SCH-TEXT",
                  "height": 150, "rotation": 0.0, "owner": None})
    text_row(3, row_vals("SC9", sz(30, 30, 4, 14), None, None))
    texts.append({"id": "DIA3", "value": "%%C", "x": 3650, "y": band_mid(3), "layer": "SCH-TEXT", "height": 200,
                  "rotation": 0.0, "owner": None})                          # the diameter sign: a separator only
    seg((4700, band_mid(3)), (11000, band_mid(3)), "STRIKE-SC9")
    text_row(4, row_vals("SC4", sz(30, 50, 6, 16), sz(25, 50, 6, 16), sz(20, 50, 6, 16)), kind="MTEXT")
    k5 = row_vals("SC5", sz(30, 45, 4, 16), sz(25, None, 4, 16), sz(20, 45, 4, 16))
    text_row(5, k5)
    return {"segments": segs, "texts": texts, "attributes": attrs}


def transform(d, *, scale=1.0, rot_deg=0.0, mirror=False, offset=(0.0, 0.0)):
    c, s = math.cos(math.radians(rot_deg)), math.sin(math.radians(rot_deg))

    def f(p):
        x, y = p[0] * scale, p[1] * scale
        if mirror:
            x = -x
        return (x * c - y * s + offset[0], x * s + y * c + offset[1])
    out = copy.deepcopy(d)
    for sg in out["segments"]:
        sg["a"], sg["b"] = f(sg["a"]), f(sg["b"])
    for t in out["texts"] + out["attributes"]:
        t["x"], t["y"] = f((t["x"], t["y"]))
    return out


def rows_by_mark(R):
    return {r["mark"]: r for r in R["schedule"]["rows"] if r["family"] == "COLUMN"}


def m2(band):
    d = band["dims_m"]
    return round(d["W"] * d["H"], 6)


VARIANTS = {"mm": {}, "metres": {"scale": 0.001}, "rot90": {"rot_deg": 90.0}, "mirror": {"mirror": True},
            "offset": {"offset": (1.0e6, -2.5e6)},
            "all": {"scale": 0.001, "rot_deg": 90.0, "mirror": True, "offset": (1234.5, 987.6)},
            "rot_37": {"rot_deg": 37.0}}


@pytest.mark.parametrize("name", sorted(VARIANTS))
def test_hand_schedule_every_variant(name):
    R = X.read(transform(base_drawing(), **VARIANTS[name]))
    rows = rows_by_mark(R)
    assert sorted(rows) == ["SC1", "SC2", "SC4", "SC5", "SC9"], name
    assert R["schedule"]["families"]["COLUMN"]["unit"] == "cm"
    kn = rows["SC9"]
    assert kn["form"] == "TEXT_ROW" and kn["source"].startswith("TEXT_ROW ")
    assert m2(kn["by_storey"]["FOUNDATION"]) == 0.09
    assert kn["by_storey"]["FOUNDATION"]["bars"][0]["count"] == 4 and kn["by_storey"]["FOUNDATION"]["bars"][0][
        "dia_mm"] == 14
    assert set(kn["by_storey"]) == {"FOUNDATION"}
    assert {s: v["status"] for s, v in kn["cell_status"].items()} == {"FOUNDATION": "PRESENT", "GF": "STRUCK",
                                                                        "1F": "STRUCK"}
    assert X.type_kind(kn)[0] == "NECK_ONLY"
    k2 = rows["SC2"]
    assert (m2(k2["by_storey"]["FOUNDATION"]), m2(k2["by_storey"]["GF"]), m2(k2["by_storey"]["1F"])) == \
        (0.12, 0.1, 0.08)
    assert k2["by_storey"]["1F"]["bars"][0]["dia_mm"] == 14
    assert X.type_kind(k2)[0] == "HAS_UPPER"
    assert m2(rows["SC4"]["by_storey"]["FOUNDATION"]) == 0.15
    k5 = rows["SC5"]
    assert k5["cell_status"]["GF"]["status"] == "MISSING_CELL" and k5["cell_status"]["GF"]["missing"] == ["GF.H"]
    assert X.type_kind(k5)[0] == "HAS_UPPER" and X.held_levels(k5) == "GF MISSING_CELL"
    assert "H" not in k5["by_storey"]["GF"]["dims_m"]                   # never a 0 depth
    assert m2(k5["by_storey"]["FOUNDATION"]) == 0.135
    assert rows["SC1"]["form"] == "ATTRIBUTE_ROW" and X.type_kind(rows["SC1"])[0] == "HAS_UPPER"
    assert [u["value"] for u in R["unbound"]] == ["SEE NOTE 3"]
    assert R["unbound"][0]["why"] == "TEXT_OUTSIDE_EVERY_TAG_COLUMN"
    tb = R["tables"][0]
    assert tb["state"] == "READ" and sorted(t["mark"] for t in tb["text_rows"]) == ["SC2", "SC4", "SC5", "SC9"]
    assert [b["texts"] for b in tb["bands_without_mark"]] == [["TYPE", "FOUNDATION", "GROUND", "FIRST", "NOTES"]]


def test_frozen_reader_drops_the_text_rows():
    """the defect this reader fixes: the frozen attribute reader sees SC1 alone (a single-row table)."""
    A = SR.from_attribute_rows(base_drawing()["attributes"])
    assert [r["mark"] for r in A["rows"]] == ["SC1"]


def test_mm_values_whole_table():
    R = X.read(transform(base_drawing(values_scale=10), scale=0.001, rot_deg=90.0))
    rows = rows_by_mark(R)
    assert R["schedule"]["families"]["COLUMN"]["unit"] == "mm"
    assert m2(rows["SC9"]["by_storey"]["FOUNDATION"]) == 0.09 and X.type_kind(rows["SC9"])[0] == "NECK_ONLY"
    assert m2(rows["SC2"]["by_storey"]["GF"]) == 0.1


def test_mm_text_row_in_a_cm_table_is_held():
    d = base_drawing()
    for t in d["texts"]:
        if t["id"] in ("TEXT3:FDN.W", "TEXT3:FDN.H"):
            t["value"] = "300"
    R = X.read(d)
    kn = rows_by_mark(R)["SC9"]
    assert R["schedule"]["families"]["COLUMN"]["unit"] == "cm"
    assert kn["unit_conflict"]["table_unit"] == "cm"
    assert X.type_kind(kn) == ("HELD", "text row unit conflicts with the table")
    assert any("SC9" in w for w in R["warnings"])


def test_struck_cell_with_a_value_is_a_conflict():
    d = base_drawing()
    d["segments"].append({"id": "STRIKE-SC2", "layer": "SCH-LINES", "a": (8100, band_mid(2)),
                          "b": (10900, band_mid(2)), "kind": "LINE"})
    R = X.read(d)
    k2 = rows_by_mark(R)["SC2"]
    assert k2["cell_status"]["1F"]["status"] == "CONFLICT"
    assert X.type_kind(k2)[0] == "HAS_UPPER" and X.held_levels(k2) == "1F CONFLICT"
    det = {"unit_m": 0.001, "sheets": {"SH01": {"sheet": {"role": "COLUMN_PLAN"},
                                                "columns": [{"member_id": "C:SC2", "mark": "SC2"}]}}}
    assert X.classify(det, R)[0]["status"] == "PARTLY_HELD"


def test_diagonal_strike_and_an_edge_touch():
    d = base_drawing()
    d["segments"] = [s for s in d["segments"] if s["id"] != "STRIKE-SC9"]
    lo, hi = HEAD - PITCH * 4, HEAD - PITCH * 3
    d["segments"].append({"id": "DIAG", "layer": "SCH-LINES", "a": (4500, lo + 10), "b": (11500, hi - 10),
                          "kind": "LINE"})
    R = X.read(d)
    assert X.type_kind(rows_by_mark(R)["SC9"])[0] == "NECK_ONLY"
    d2 = base_drawing()
    for s in d2["segments"]:
        if s["id"] == "STRIKE-SC9":
            s["a"] = (5400, band_mid(3))                # only 10 % into the GF.W cell 4500..5500
    k = rows_by_mark(X.read(d2))["SC9"]
    assert k["cell_status"]["GF"]["status"] == "MISSING_CELL"     # GF.W not struck, GF.H struck: held
    assert X.type_kind(k)[0] == "HELD"


def test_no_strike_drawn_means_blank_not_none():
    d = base_drawing()
    d["segments"] = [s for s in d["segments"] if s["id"] != "STRIKE-SC9"]
    kn = rows_by_mark(X.read(d))["SC9"]
    assert kn["cell_status"]["GF"]["status"] == "EMPTY" and kn["cell_status"]["1F"]["status"] == "EMPTY"
    kind, why = X.type_kind(kn)
    assert kind == "HELD" and "GF EMPTY" in why


def test_no_frame_reads_nothing():
    d = base_drawing()
    d["segments"] = [s for s in d["segments"] if not s["id"].startswith("V")]
    R = X.read(d)
    assert sorted(rows_by_mark(R)) == ["SC1"]
    assert R["tables"][0]["state"] == "FRAME_NOT_FOUND" and R["warnings"]


def test_two_values_in_one_cell_are_reported():
    d = base_drawing()
    d["texts"].append({"id": "EXTRA", "value": "35", "x": 1700, "y": band_mid(2), "layer": "SCH-TEXT",
                       "height": 200, "rotation": 0.0, "owner": None})
    R = X.read(d)
    k2 = rows_by_mark(R)["SC2"]
    assert "W" not in k2["by_storey"]["FOUNDATION"]["dims_raw"]
    assert k2["cell_status"]["FOUNDATION"]["status"] == "MISSING_CELL"
    assert any(u["why"] == "SEVERAL_VALUES_IN_ONE_CELL" and u["tag"] == "FDN.W" for u in R["unbound"])


def test_classify_plan_occurrences():
    R = X.read(transform(base_drawing(), rot_deg=90.0, mirror=True))
    det = {"unit_m": 0.001, "sheets": {
        "SH01": {"sheet": {"role": "COLUMN_PLAN"}, "columns": [
            {"member_id": "C:SC9@1", "mark": "SC9", "in_schedule": False},
            {"member_id": "C:SC2@1", "mark": "SC2", "in_schedule": False},
            {"member_id": "C:SC5@1", "mark": "SC5", "in_schedule": False},
            {"member_id": "C:SC1@1", "mark": "SC1", "in_schedule": True},
            {"member_id": "C:ZZ@1", "mark": "ZZ", "in_schedule": False}]},
        "SH02": {"sheet": {"role": "FOUNDATION_PLAN"}, "columns": [
            {"member_id": "F:SC9@1", "mark": "SC9", "in_schedule": False},
            {"member_id": "F:SC5@1", "mark": "SC5", "in_schedule": False}]},
        "SH03": {"sheet": {"role": "SLAB_PLAN"}, "columns": [{"member_id": "S:SC9", "mark": "SC9"}]}}}
    out = {c["member_id"]: c for c in X.classify(det, R)}
    assert sorted(out) == ["C:SC2@1", "C:SC5@1", "C:SC9@1", "F:SC5@1", "F:SC9@1"]   # SC1 unchanged, ZZ not a row
    assert (out["C:SC9@1"]["status"], out["C:SC9@1"]["code"]) == ("NOT_PRESENT", "NECK_ONLY_TYPE")
    assert out["F:SC9@1"]["status"] == "HELD" and out["F:SC9@1"]["code"] == "FOUNDATION_DATUM_NOT_VERIFIED"
    assert out["F:SC9@1"]["section_m2"] == 0.09
    assert out["C:SC2@1"]["status"] == "SCHEDULE_ROW_READ"
    assert out["C:SC5@1"]["status"] == "PARTLY_HELD" and "GF MISSING_CELL" in out["C:SC5@1"]["why"]
    assert out["F:SC5@1"]["status"] == "HELD" and out["F:SC5@1"]["code"] == "FOUNDATION_DATUM_NOT_VERIFIED"
    assert all(c.get("section_m2") != 0 for c in out.values())


def test_empty_and_degenerate_inputs():
    assert X.read({"segments": [], "texts": [], "attributes": []})["schedule"]["rows"] == []
    d = base_drawing()
    d["segments"] = []
    R = X.read(d)                                       # one attribute row, no rules: no pitch, no frame
    assert sorted(rows_by_mark(R)) == ["SC1"] and R["warnings"]
    assert X.type_kind(None) == (None, "no cell status")
    assert X.policy_record()["policy"] == "SCHEDULE_TEXT_ROWS_V1"


def test_texts_outside_the_frame_or_over_an_attribute_row():
    d = base_drawing()
    for k, (tag, v) in enumerate((("TYPE", "SC7"), ("FDN.W", "30"), ("FDN.H", "35"))):     # a row BELOW the frame
        d["texts"].append({"id": f"OUT{k}", "value": v, "x": TAGS_X[tag], "y": BOTTOM - 250, "layer": "SCH-TEXT",
                           "height": 200, "rotation": 0.0, "owner": None})
    d["texts"].append({"id": "OVER", "value": "65", "x": TAGS_X["FDN.H"] + 200, "y": band_mid(0),
                       "layer": "SCH-TEXT", "height": 200, "rotation": 0.0, "owner": None})   # typed over SC1
    R = X.read(d)
    assert "SC7" not in rows_by_mark(R)
    assert m2(rows_by_mark(R)["SC1"]["by_storey"]["FOUNDATION"]) == 0.18          # 0.30 x 0.60, the attribute
    assert [(u["text_id"], u["why"]) for u in R["unbound"] if u["why"] == "TEXT_IN_ATTRIBUTE_ROW"] == \
        [("OVER", "TEXT_IN_ATTRIBUTE_ROW")]

