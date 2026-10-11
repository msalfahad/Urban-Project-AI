"""M4 continuous beams: span inheritance only on printed span evidence, the multi-span bar model with physical bar
groups, on a hand-made slab plan with hand-derived truth (mm drawing).

    CB1  0.30 x 0.60, one pair of faces through four 0.40 columns at x = 0, 4000, 9000, 15000: clear spans 3.6 / 4.6
         / 5.6 m, axis 4.0 / 5.0 / 6.0; printed L1-M 4.0 L2-M 5.0 L3-M 6.0; labels on spans 1 and 2 only
         -> span 3 is the schedule's span 3 (MATCH_FORWARD): bound, 0.3 x 5.6 x 0.6 = 1.008 m3
    CB2  printed 4.0 / 4.0 / 4.0, drawn two spans                                  -> SPAN_COUNT_CONFLICT, no bars
    CB3  printed 6.0 / 4.0 (L1 6.0), drawn 4.0 then 6.0 left to right              -> MATCH_REVERSED
    B1   0.20 x 0.50 simple beam, label on its first span only, second span across a column
         -> no inheritance: UNRESOLVED, exposure 0.2 x 4.6 x 0.5 = 0.46 m3, alternative = the neighbour's section
Bars of CB1 (V3 bases: anchorage 40 d, support bars 0.25 x clear span each side, bottom 0.15 m past the support):
    BOTTOM1 3Ø16: 3.6 + 0.64 + (0.40 + 0.15) = 4.79 m; SUPPORT_TOP1 4Ø16: 0.9 + 0.40 + 1.15 = 2.45 m (one group)
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import pytest

ezdxf = pytest.importorskip("ezdxf")

from engine.source import continuous_beams as CBM           # noqa: E402
from engine.source import generic_route as GR               # noqa: E402
from engine.source import provisional_estimate as PE        # noqa: E402
from tools import urban_intake as UI                        # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
V3 = ROOT / "engine/profiles/URBAN_M4_GENERIC_CONVENTIONS_V3.json"


def _set(path):
    doc = ezdxf.new("R2018")
    doc.header["$INSUNITS"] = 4
    m = doc.modelspace()

    def frame(x0, title):
        m.add_lwpolyline([(x0 - 3000, -9000), (x0 + 37000, -9000), (x0 + 37000, 21000), (x0 - 3000, 21000)],
                         close=True, dxfattribs={"layer": "FRAME"})
        m.add_text(title, dxfattribs={"layer": "S-TEXT", "height": 400}).set_placement((x0, 19500))

    def L(a, b, layer="S-BEAM"):
        m.add_line(a, b, dxfattribs={"layer": layer})

    def T(s, x, y, h=120):
        m.add_text(s, dxfattribs={"layer": "S-TEXT", "height": h}).set_placement((x, y))

    def col(cx, cy, s=400):
        m.add_lwpolyline([(cx - s / 2, cy - s / 2), (cx + s / 2, cy - s / 2), (cx + s / 2, cy + s / 2),
                          (cx - s / 2, cy + s / 2)], close=True, dxfattribs={"layer": "S-COL"})
        T("C1", cx - 100, cy - 50, 80)

    def beam(y, x0, x1, w):
        L((x0, y - w / 2), (x1, y - w / 2))
        L((x0, y + w / 2), (x1, y + w / 2))
    frame(0, "GROUND FLOOR ROOF SLAB")
    # CB1: columns at 0 / 4000 / 9000 / 15000 on y = 0
    for x in (0, 4000, 9000, 15000):
        col(x, 0)
    beam(0, 200, 15000 - 200, 300)
    T("CB1", 1500, -60)
    T("CB1", 6000, -60)
    # B1 simple beam on y = 6000: columns 0 / 5000 / 10000, faces through
    for x in (0, 5000, 10000):
        col(x, 6000)
    beam(6000, 200, 10000 - 200, 200)
    T("B1", 2000, 5960)
    # CB2: printed three spans, drawn two (columns 0 / 4000 / 8000 on y = 12000)
    for x in (0, 4000, 8000):
        col(x, 12000)
    beam(12000, 200, 8000 - 200, 300)
    T("CB2", 1500, 11940)
    T("CB2", 5500, 11940)
    # CB3: drawn 4.0 then 6.0, printed L1 6.0 L2 4.0 (columns 20000 / 24000 / 30000 on y = 0)
    for x in (20000, 24000, 30000):
        col(x, 0)
    beam(0, 20200, 30000 - 200, 300)
    T("CB3", 21500, -60)
    T("CB3", 26500, -60)
    frame(60000, "SCHEDULE OF BEAMS AND COLUMNS")

    def table(name, tags, rows, y0):
        blk = doc.blocks.new(name)
        for k, t in enumerate(tags):
            blk.add_attdef(t, (k * 800, 0), dxfattribs={"height": 150, "layer": "S-SCHED"})
        for n, vals in enumerate(rows):
            ins = m.add_blockref(name, (61000, y0 - 600 * n), dxfattribs={"layer": "S-SCHED"})
            ins.add_auto_attribs(dict(zip(tags, [str(v) for v in vals])))
    table("CB_ROW", ("BEAM-NAME", "W", "H", "L1-M", "L2-M", "L3-M", "BOT1-B", "BOT1-D", "BOT2-B", "BOT2-D", "BOT3-B",
                     "BOT3-D", "MID1-B", "MID1-D", "MID2-B", "MID2-D", "STR1-B", "STR1-D", "STR2-B", "STR2-D",
                     "STR3-B", "STR3-D"),
          [("CB1", 30, 60, "4.0", "5.0", "6.0", 3, 16, 4, 16, 4, 18, 4, 16, 5, 18, 6, 8, 6, 8, 7, 8),
           ("CB2", 30, 60, "4.0", "4.0", "4.0", 3, 16, 3, 16, 3, 16, 4, 16, 4, 16, 6, 8, 6, 8, 6, 8),
           ("CB3", 30, 60, "6.0", "4.0", "", 4, 18, 3, 16, "", "", 5, 18, "", "", 7, 8, 6, 8, "", "")], 19000)
    table("BEAM_ROW", ("BEAM", "W", "H", "BOT-B", "BOT-D", "TOP-B", "TOP-D", "STI-B", "D"),
          [("B1", 20, 50, 3, 14, 2, 12, 5, 8)], 12000)
    table("COL_ROW", ("COL-T", "GR.W", "GR.H", "GR.R", "GR.D"), [("C1", 40, 40, 4, 16)], 9000)
    doc.saveas(path)
    return path


@pytest.fixture(scope="module")
def run(tmp_path_factory):
    I = UI.read(_set(tmp_path_factory.mktemp("cb") / "cb.dxf"))
    conv = GR.merge_conventions(json.loads(V3.read_text()), {"profile": "T", "conventions": []})
    D = GR.detect(I)
    items, reg, risk = GR.items_from(D, conv, {})
    PE.check(items, conv)
    rec = next(r for r in D["sheets"].values() if r["sheet"]["role"] == "SLAB_PLAN")
    return D, rec, items, reg, risk


def _line(rec, mark):
    return next(ln for ln in rec["cb_lines"] if ln["mark"] == mark)


def test_printed_spans_and_roles():
    assert CBM.printed_spans({"raw": {"L1-M": "3.4", "L2-M": "3.3", "L3-M": "3.8"}}) == [3.4, 3.3, 3.8]
    assert CBM.printed_spans({"raw": {"L1-M": "3.4", "L3-M": "3.8"}}) is None          # a gap in the numbering
    assert CBM.printed_spans({"raw": {"L1": "340", "L2": "330"}}) is None              # bare and not metres
    assert CBM.printed_spans({"raw": {"L1-CM": "340"}}) == [3.4]
    rl, empty = CBM.roles({"bars": [{"role": "BOT1", "count": 3, "dia_mm": 16}, {"role": "MID", "count": 4,
                                                                                   "dia_mm": 16}],
                           "tag_set": ["BOT1-B", "BOT1-D", "MID-B", "MID-D", "MID2-B", "MID2-D"]})
    assert ("BOTTOM", 1) in rl and ("SUPPORT_TOP", 0) in rl and ("SUPPORT_TOP", 2) in empty


def test_unlabelled_span_takes_the_mark_only_on_printed_span_evidence(run):
    D, rec, items, reg, risk = run
    ln = _line(rec, "CB1")
    assert ln["state"] == "MATCH_FORWARD" and len(ln["spans"]) == 3 and len(ln["inherited"]) == 1
    span3 = next(s for s in ln["spans"] if s["index"] == 3)
    assert abs(span3["clear_m"] - 5.6) < 1e-6 and abs(span3["drawn_m"] - 6.0) < 1e-6
    pid = ln["inherited"][0]
    it = next(i for i in items if i["item_id"] == f"P-C:BEAMS:GF:{pid}")
    assert abs(it["base"] - 0.3 * 5.6 * 0.6) < 1e-6
    # the simple beam's unlabelled span across a support is never inherited
    b1 = [i for i in items if i["family"] == "BEAMS" and i["trade"] == "CONCRETE" and
          i["blocker"] == "UNLABELLED_SPAN_ACROSS_SUPPORT"]
    assert len(b1) == 1 and b1[0]["category"] == "UNRESOLVED"
    assert abs(b1[0]["exposure_low"] - 0.2 * 4.6 * 0.5) < 1e-6 and abs(b1[0]["exposure_high"] - 0.46) < 1e-6
    assert any(r["KIND"] == "BEAM_UNLABELLED_SPAN_ACROSS_SUPPORT" for r in risk)


def test_count_conflict_and_reversed_reading(run):
    D, rec, items, reg, risk = run
    assert _line(rec, "CB2")["state"] == "SPAN_COUNT_CONFLICT"
    cb2 = [r for r in reg if r["COMPONENT_ID"].startswith("BEAMS:GF:") and "SPAN_COUNT_CONFLICT" in r["REASON"]]
    assert len(cb2) == 2 and all(r["REBAR_STATE"] == "MISSING_DATA" for r in cb2)
    ln = _line(rec, "CB3")
    assert ln["state"] == "MATCH_REVERSED"
    # the left drawn span (4.0) is the schedule's span 2
    left = min(ln["spans"], key=lambda s: s["t0"])
    assert left["index"] == 2 and abs(left["printed_m"] - 4.0) < 1e-9


def test_physical_bar_groups_by_hand(run):
    D, rec, items, reg, risk = run
    ln = _line(rec, "CB1")
    g = {x["bar_id"]: x for x in ln["groups"]}
    kg16 = 16 * 16 / 162.0
    assert abs(g["CB1:BOTTOM1"]["length_m"][1] - 4.79) < 1e-6
    assert abs(g["CB1:BOTTOM1"]["mass_kg"][1] - 3 * 4.79 * kg16) < 1e-6
    sup = g["CB1:SUPPORT_TOP1"]
    assert abs(sup["length_m"][1] - 2.45) < 1e-6 and abs(sum(sup["share"].values()) - 1.0) < 1e-12
    assert abs(sup["share"][1] - 1.1 / 2.45) < 1e-9
    # one support group per interior support, one bottom group and one stirrup group per span
    roles = sorted((x["role"], x["k"]) for x in ln["groups"])
    assert roles == [("BOTTOM", 1), ("BOTTOM", 2), ("BOTTOM", 3), ("STIRRUP", 1), ("STIRRUP", 2), ("STIRRUP", 3),
                     ("SUPPORT_TOP", 1), ("SUPPORT_TOP", 2)]
    assert ("TOP_THROUGH", 0, "NOT_PRINTED") in [tuple(x) for x in ln["missing"]]


def test_bar_mass_is_conserved_and_partial_missing_recorded(run):
    D, rec, items, reg, risk = run
    ln = _line(rec, "CB1")
    groups = sum(x["mass_kg"][1] for x in ln["groups"])
    pieces = sum(i["base"] for i in items if i["trade"] == "REINFORCEMENT" and i["category"] == "PROVISIONAL" and
                 "CB_" in i["item_id"] and any(i["component_id"].endswith(p) for p in ln["pieces"]))
    assert abs(groups - pieces) < 1e-6
    st = {r["COMPONENT_ID"]: r["REBAR_STATE"] for r in reg}
    assert all(st[f"BEAMS:GF:{p}"] == "PARTIAL_MISSING" for p in ln["pieces"])        # no through top bars printed
    assert sum(1 for i in items if i["item_id"].startswith("U-S:") and "TOP_THROUGH" in i["item_id"]) >= 3
