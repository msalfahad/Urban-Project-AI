"""T-627: B12 opening-area rows to drawing evidence (R-T627-1). Hand-calculated non-development fixtures (villa T627-V:
a window whose schedule and elevation disagree, a door seen in two views, a plan drawn in a temporary DXF), adverse
cases, and the development-villa build (committed drawing read + statement rows; the drawing re-read is skipped when
the private DXF / DWF are absent)."""
from __future__ import annotations

import json
import os
import sys
from decimal import Decimal as D
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "research" / "agents_t627"
sys.path.insert(0, str(HERE))
import t627_rules as R  # noqa: E402
import t627_extract as X  # noqa: E402

PRIV = ROOT.parents[1] / ".work" / "private"
DXF = Path(os.environ.get("T627_DXF", PRIV / "P7757_DXF_COMPRESSED" / "P7757.dxf"))
DWF = Path(os.environ.get("T627_DWF", PRIV / "arch.dwf"))


# ---- fixture villa T627-V: window WA 1.40 wide; schedule (2026-03-01) prints h 1.40, the re-issued elevation
# (2026-05-10) prints 1.50 -> the later sheet governs: 1.40 x 1.50 = 2.100 m2 (hand) ----------------------------------
def test_later_dated_sheet_governs_by_hand():
    g = R.governing([{"value": "1.40", "kind": "SCHEDULE", "sheet": "A-601 schedule", "date": "2026-03-01"},
                     {"value": "1.50", "kind": "ELEVATION", "sheet": "A-301 rev B", "date": "2026-05-10"}])
    assert g["value"] == D("1.50") and g["status"] == "PRINTED" and "later-dated" in g["basis"]
    assert R.opening_area("1.40", g["value"]) == D("2.100000")


def test_same_date_disagreement_is_a_conflict_never_a_pick():
    g = R.governing([{"value": "1.40", "kind": "SCHEDULE", "sheet": "A-601", "date": "2026-05-10"},
                     {"value": "1.50", "kind": "ELEVATION", "sheet": "A-301", "date": "2026-05-10"}])
    assert g["status"] == "CONFLICT" and g["value"] is None


def test_printed_beats_geometry_and_geometry_beats_fallback():
    geo = {"value": "2.199", "kind": "GEOMETRY", "bound": True, "sheet": "NE"}
    fb = {"value": "2.20", "kind": "OWNER_FALLBACK", "sheet": "Q-55 C"}
    assert R.governing([geo, fb, {"value": "2.10", "kind": "SECTION", "sheet": "B-B", "date": "2026-01-01"}])[
        "value"] == D("2.10")
    g = R.governing([geo, fb])
    assert g["status"] == "DRAWING_CONFIRMED" and g["value"] == D("2.20")       # read to the cm
    assert R.governing([fb])["status"] == "ASSUMED_OWNER_APPROVED"
    assert R.governing([dict(geo, bound=False)])["status"] == "HELD"               # a candidate is not a value
    assert R.governing([dict(geo, frame_only=True)])["status"] == "HELD"           # a frame is not the opening
    assert R.governing([geo, dict(geo, value="2.35", sheet="SW")])["status"] == "CONFLICT"
    assert R.governing([])["status"] == "HELD"


def test_adverse_assembly_or_glass_area_refused_as_opening_area():
    for m in ("ASSEMBLY", "GLASS", "NET_GLASS", "FRAME"):
        with pytest.raises(R.RuleError, match="not opening area"):
            R.opening_area("1.40", "1.50", measure=m)
    with pytest.raises(R.RuleError):
        R.governing([{"value": "1.2", "kind": "ASSEMBLY", "sheet": "supplier"}])


def test_adverse_zero_missing_and_millimetres_refused():
    with pytest.raises(R.RuleError, match="HELD"):
        R.opening_area("1.40", "0")
    with pytest.raises(R.RuleError, match="millimetres"):
        R.opening_area("1400", "1.50")
    with pytest.raises(R.RuleError):
        R.governing([{"value": "0", "kind": "PLAN", "sheet": "x", "date": "2026-01-01"}])


def test_door_height_two_views_by_hand():
    # door DB: head drawn at +3.20 in two views; it opens from the +1.00 landing (printed) -> 2.20 (hand)
    v = [{"sheet": "NE", "head_level": "3.201", "bottom_level": "0.999", "bound": True},
         {"sheet": "SW", "head_level": "3.199", "bottom_level": "0.151", "bound": True}]
    r = R.door_height_from_views(v, ["0.15", "1.00"])
    assert r["status"] == "DRAWING_CONFIRMED" and r["value"] == D("2.20") and r["ffl"] == D("1.00")
    assert R.door_height_from_views([dict(v[0], head_level="2.50"), v[1]], ["1.00"])["status"] == "CONFLICT"
    assert R.door_height_from_views([dict(v[0], frame_only=True)], ["1.00"])["status"] == "HELD"
    assert R.door_height_from_views(v, [])["status"] == "HELD"
    with pytest.raises(R.RuleError, match="below the floor"):
        R.door_height_from_views([dict(v[0], head_level="0.90")], ["1.00"])


def test_row_split_re_adds_exactly():
    t = R.split_terms("0.90", "2.20", "1.00", "2.40")
    assert [(x["term"], x["qty"]) for x in t] == [("WIDTH", D("0.240000")), ("HEIGHT", D("0.180000"))]
    assert sum(x["qty"] for x in t) == D("1.00") * D("2.40") - D("0.90") * D("2.20")
    assert R.split_terms("1.00", "2.20") == [{"term": "OMITTED", "qty": D("-2.200000")}]
    assert R.judge_row("0.240", "0.240000")[0] == "DRAWING_CONFIRMED"
    assert R.judge_row("0.240", "0.2425")[0] == "DIFFERS"
    rows = [{"delta": "0.5", "class": "ENGINE_RIGHT", "evidence": "DRAWING_CONFIRMED"},
            {"delta": "9.45", "class": "HELD", "evidence": "HELD"}]
    assert R.split_exact(rows, "9.95")["by_class"] == {"ENGINE_RIGHT": "0.5", "HELD": "9.45"}
    with pytest.raises(R.RuleError, match="re-add"):
        R.split_exact(rows, "9.96")
    with pytest.raises(R.RuleError, match="never 0"):
        R.split_exact([{"delta": "0", "class": "HELD", "evidence": "HELD"}], "0")


# ---- the extractor on a hand-drawn temporary DXF (mm): a 1.40 window in a horizontal wall and a 0.90 door in a
# vertical wall, then the same drawing rotated 90 deg; hand: window jambs 1.400 apart, door faces 0.900 on both faces --
def _plan(tmp_path, rot=False):
    import ezdxf
    doc = ezdxf.new(units=4)
    msp = doc.modelspace()
    P = (lambda x, y: (-y, x)) if rot else (lambda x, y: (x, y))
    L = (lambda a, b, layer: msp.add_line(P(*a), P(*b), dxfattribs={"layer": layer}))
    for c in (0, 40, 80, 120):                                   # window symbol 50 mm inside the jambs, 4 lines
        L((50, c), (1350, c), "W")
    L((0, -40), (0, 160), "1")                                   # jamb caps
    L((1400, -40), (1400, 160), "1")
    blk = doc.blocks.new("D120")
    blk.add_line((0, 0), (1000, 0))
    ins = msp.add_blockref("D120", P(5000, 2000), dxfattribs={"rotation": 90 + (90 if rot else 0)})
    L((5000, -1000), (5000, 1950), "1")                          # face x=5000: ends at 1950, restarts at 2850
    L((5000, 2850), (5000, 4000), "1")
    L((5200, -1000), (5200, 1950), "1")                          # face x=5200: same gap
    L((5200, 2850), (5200, 4000), "1")
    path = tmp_path / "v.dxf"
    doc.saveas(path)
    return ezdxf.readfile(path), ins.dxf.handle


@pytest.mark.parametrize("rot", [False, True])
def test_extractor_widths_by_hand_and_rotation(tmp_path, rot):
    doc, dh = _plan(tmp_path, rot)
    msp = doc.modelspace()
    seed = next(e.dxf.handle for e in msp.query("LINE[layer=='W']"))
    w = X.window_plan(doc, msp, seed)
    assert w["width"] == "1.400" and len(w["symbol_handles"]) == 4
    d = X.door_plan(doc, msp, dh)
    assert d["width"] == "0.900" and d["faces"] == 2


def test_extractor_adverse_one_jamb_and_faces_disagreeing(tmp_path):
    import ezdxf
    doc, dh = _plan(tmp_path)
    msp = doc.modelspace()
    for e in list(msp.query("LINE[layer=='1']")):
        s, t = e.dxf.start, e.dxf.end
        if abs(s.x - 1400) < 1 and abs(t.x - 1400) < 1:
            msp.delete_entity(e)                                 # one jamb cap missing
        if abs(s.x - 5200) < 1 and abs(min(s.y, t.y) - 2850) < 1:
            e.dxf.start, e.dxf.end = (5200, 2950), (5200, 4000)  # far face now 1.000: the faces disagree
    seed = next(e.dxf.handle for e in msp.query("LINE[layer=='W']"))
    with pytest.raises(ValueError, match="jamb"):
        X.window_plan(doc, msp, seed)
    with pytest.raises(ValueError, match="disagree"):
        X.door_plan(doc, msp, dh)


def test_bind_view_votes_mirror_and_refuses_wrong_width_and_shared_outline():
    # plan (mm, axis x): A 1000 wide at 0, B 600 at 3000, C 600 at 5000 (same wall), Z 600 at 5000 in another wall
    items = [{"id": i, "kind": "WINDOW", "_axis": "x", "_iv": iv, "_c": c} for i, iv, c in
             (("A", (0, 1000), 0), ("B", (3000, 3600), 0), ("C", (5000, 5600), 0), ("Z", (5000, 5600), 900))]
    y0 = 0.0
    # mirrored view (sign -1): x_el = 10000 - x_plan; outlines (left, width, bottom, head)
    rects = [(9000.0, 1000.0, 1000.0, 2500.0), (6400.0, 600.0, 1700.0, 2500.0), (4400.0, 600.0, 1700.0, 2500.0),
             (2000.0, 900.0, 0.0, 2200.0)]
    info, b = X.bind_view("V", {"axis": "x", "sign": -1}, rects, items, y0, (-0.5, 5.5))
    assert info["offset_votes"] >= 3
    assert b["A"][0][2] == "BOUND" and b["A"][0][1][3] - b["A"][0][1][2] == 1500.0          # 1.50 high (hand)
    assert b["C"][0][2] == "BOUND" and b["Z"][0][2] == "NOT_THIS_WALL"                      # same-wall support
    # the wrong sign finds nothing to bind consistently
    info2, _ = X.bind_view("V", {"axis": "x", "sign": 1}, rects, items, y0, (-0.5, 5.5))
    assert info2 is None or info2["offset_votes"] < info["offset_votes"]
    # an outline in another floor's band is never bound
    _, b3 = X.bind_view("V", {"axis": "x", "sign": -1}, rects, items, y0, (5.5, 9.7))
    assert b3 == {}


# ---- development villa ------------------------------------------------------------------------------------------
def _build():
    import t627_alsenan as B
    return B, B.build()


def test_dev_build_matches_committed_outputs():
    B, d = _build()
    assert (HERE / "out" / "T627_ROW_EVIDENCE.json").read_text(encoding="utf-8") == B.dumps(d)
    assert (HERE / "out" / "T627_ROW_EVIDENCE.md").read_text(encoding="utf-8") == B.render_md(d)


def test_dev_22_rows_own_readings_and_exact_splits():
    _, d = _build()
    w, a = d["sections"]["T-568/windows-m2"], d["sections"]["T-568/alu-doors-m2"]
    assert len(w["rows"]) == 16 and len(a["rows"]) == 8
    assert w["count"] == {"DRAWING_CONFIRMED": 14, "HELD": 2}
    assert a["count"] == {"ASSUMED_OWNER_APPROVED": 3, "DRAWING_CONFIRMED": 5}
    assert all(r["diff"] == "0.000000" or D(r["diff"]) == 0 for s in (w, a) for r in s["rows"] if "diff" in r)
    assert w["split_statement"] == {"total": "40.644", "by_class": {"ENGINE_RIGHT": "3.975", "HELD": "36.669"},
                                    "by_evidence": {"DRAWING_CONFIRMED": "3.975", "HELD": "36.669"}}
    assert a["split_proposed"]["by_class"] == {"ENGINE_RIGHT": "-1.140", "RULE_DIFFERENCE": "0.380"}
    assert a["split_statement"]["by_class"] == {"ENGINE_RIGHT": "-1.720", "RULE_DIFFERENCE": "0.960"}
    moved = [r["id"] for r in a["rows"] if r["class"] != r["proposed_class"]]
    assert moved == ["D-GF-01", "D-GF-06", "D-GF-03"]


def test_dev_own_equals_engine_on_every_settled_opening():
    _, d = _build()
    for o in d["openings_own_vs_engine"]:
        assert D(o["own_area"]) == D(o["engine_area"]), o


def test_dev_held_rows_named_never_zero():
    _, d = _build()
    held = [r for r in d["sections"]["T-568/windows-m2"]["rows"] if r["class"] == "HELD"]
    assert {r["id"]: r["delta"] for r in held} == {"W02": "27.219", "W17": "9.45"}
    assert held[0]["waits_on"].startswith("D-53") and "Q-76 A" in held[1]["waits_on"]


def test_dev_door_conflict_and_fallbacks_named():
    _, d = _build()
    f = d["door_findings"]
    assert f["D-GF-09"]["plan_masonry_width"] == "0.90" and f["D-GF-09"]["frame_width_drawn"] == ["1.001", "1.001"]
    assert f["D-GF-09"]["height_status"] == "ASSUMED_OWNER_APPROVED"
    rows = {r["name"]: r for r in d["sections"]["T-568/alu-doors-m2"]["rows"]}
    assert rows["GF D-GF-03 vs his 1 x 2.4 / height"]["own_height_basis"].startswith("DRAWING_CONFIRMED")


def test_dev_no_coordinates_or_client_text_in_committed_files():
    for p in (HERE / "T627_DRAWN.json", HERE / "out" / "T627_ROW_EVIDENCE.json"):
        txt = p.read_text(encoding="utf-8")
        assert all(ord(ch) < 128 for ch in txt)
        nums = []

        def walk(o, k=""):
            if isinstance(o, dict):
                for kk, v in o.items():
                    if "handle" not in kk and kk not in ("sha256",):
                        walk(v, kk)
            elif isinstance(o, list):
                for v in o:
                    walk(v, k)
            elif isinstance(o, (int, float)) or (isinstance(o, str) and o.replace(".", "", 1).lstrip("-").isdigit()):
                nums.append(abs(float(o)))
        walk(json.loads(txt))
        assert nums and max(nums) < 1000                                     # metres, no mm coordinate


@pytest.mark.skipif(not (DXF.exists() and DWF.exists()), reason="private drawings absent")
def test_dev_drawing_re_read_identical():
    assert (HERE / "T627_DRAWN.json").read_text(encoding="utf-8") == X.dumps(X.read(str(DXF), str(DWF)))
