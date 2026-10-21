"""T-019: the synthetic villa generator (tools/synth_villa) - hand truth, the DXF it writes, and the engine report.

Hand values (written from the coordinates in tools/synth_villa/villas.py before any engine run):
  SV-A GF  LIVING 6.0 x 8.0 = 48.0; KITCHEN 2.9 x 4.0 = 11.6; BATH 2.8 x 4.0 = 11.2; BEDROOM 5.8 x 3.8 = 22.04;
           outer 12.4 x 8.4 = 104.16; walls 0.20 = ring 40.8 + 8.0 + 5.8 = 54.6 gross, openings 8.4, net 46.2;
           0.10 = 4.0; mass 104.16 - 92.84 = 11.32 = 0.2 x 54.6 + 0.1 x 4.0
  SV-B GF  30.0 + 5.7 + 8.1225 + 24.0 + 18.24 = 86.0625; mass 101.76 - 86.0625 = 15.6975
           = 0.30 x 39.2 + 0.20 x 13.8 + 0.15 x 7.85
  SV-B 1F  12.75 + 31.5 + 24.0 + 18.24 = 86.49; mass 15.27 = 0.30 x 39.2 + 0.20 x 13.8 + 0.15 x 5.0
  SV-C GF  curved NE corner (inner r 2.0, outer r 2.2 about (10, 8)): LIVING 11.8 x 5.8 - 7.0 x 3.0 - 4 (1 - pi/4)
           = 47.44 - 4 + pi = 46.58159265; outer 124.44 - 4.84 (1 - pi/4) = 123.40132711;
           0.20 = 44.0 - 4.2 + 1.05 pi + 25.4 = 65.2 + 1.05 pi = 68.49867229
Adversarial variants: rotation 37 deg, mirror, metres instead of mm, Arabic layer names, a missing label, a mirrored
door block. Every test writes only under tmp_path.
"""

from __future__ import annotations

import json
import math

import pytest

from tools.synth_villa import build as B
from tools.synth_villa import compare as C
from tools.synth_villa import villas as V

TOL = 1e-6
VARIANTS = [
    {},
    {"rotate_deg": 37.0},
    {"mirror": True},
    {"units": "m"},
    {"layers": "ARABIC"},
    {"rotate_deg": -121.0, "mirror": True, "units": "m", "layers": "ARABIC"},
]


# ---- the hand truth, two ways
def test_hand_literals():
    assert V.HAND["SV-A"]["GF"]["walls"]["0.20"]["gross_lm"] == pytest.approx(54.6, abs=TOL)
    assert V.HAND["SV-C"]["GF"]["rooms_m2"]["C-LIV"] == pytest.approx(46.58159265, abs=1e-8)
    assert V.HAND["SV-C"]["GF"]["outer_m2"] == pytest.approx(123.40132711, abs=1e-8)
    assert V.HAND["SV-C"]["GF"]["walls"]["0.20"]["gross_lm"] == pytest.approx(68.49867229, abs=1e-8)
    t = B.truth_of("SV-A")
    assert t["floors"]["GF"]["walls_by_thickness"]["0.20"]["net_lm"] == pytest.approx(46.2, abs=TOL)
    assert t["floors"]["GF"]["walls_by_thickness"]["0.10"]["net_lm"] == pytest.approx(4.0, abs=TOL)


@pytest.mark.parametrize("vid", sorted(V.VILLAS))
def test_hand_truth_equals_spec_formulas_and_conserves_wall_mass(vid):
    for fl, f in V.VILLAS[vid]["floors"].items():
        h = V.HAND[vid][fl]
        assert B.area_m2(f["outer"]) == pytest.approx(h["outer_m2"], abs=TOL)
        assert set(h["rooms_m2"]) == set(f["rooms"])
        for rid, r in f["rooms"].items():
            assert B.area_m2(r["poly"]) == pytest.approx(h["rooms_m2"][rid], abs=TOL), (vid, fl, rid)
        mass = h["outer_m2"] - sum(h["rooms_m2"].values())
        assert sum(float(fam) * w["gross_lm"] for fam, w in h["walls"].items()) == pytest.approx(mass, abs=TOL)
        c = h["counts"]
        assert c["rooms"] == len(f["rooms"]) and c["wet"] == sum(r["wet"] for r in f["rooms"].values())
        for k in ("DOOR", "WINDOW", "PASSAGE"):
            assert c[k] == sum(o["kind"] == k for o in f["openings"])
        for o in f["openings"]:                   # every opening sits in a wall of a thickness the floor declares
            assert f"{o['hi'] - o['lo']:.2f}" in h["walls"], o["id"]


def test_formulas_on_known_shapes():
    disc = [(1.0, 0.0, 1.0), (-1.0, 0.0, 1.0)]                       # two half circles, r 1
    assert B.area_m2(disc) == pytest.approx(math.pi, abs=1e-12)
    assert B.perimeter_lm(disc) == pytest.approx(2 * math.pi, abs=1e-12)
    cw = [(-1.0, 0.0, -1.0), (1.0, 0.0, -1.0)]                       # the same disc drawn clockwise
    assert B.area_m2(cw) == pytest.approx(math.pi, abs=1e-12)
    notch = [(0, 0), (2, 0, -1.0), (4, 0), (4, 4), (0, 4)]          # a half-disc bite (r 1) out of a 4 x 4 square
    assert B.area_m2(notch) == pytest.approx(16 - math.pi / 2, abs=1e-12)
    assert B.perimeter_lm(V.SV_C["floors"]["GF"]["rooms"]["C-LIV"]["poly"]) == pytest.approx(
        4.8 + 3.8 + math.pi + 9.8 + 2.8 + 7.0 + 3.0, abs=1e-9)


# ---- the truth does not move with the drawing
@pytest.mark.parametrize("vid", sorted(V.VILLAS))
@pytest.mark.parametrize("var", VARIANTS[1:], ids=lambda v: "-".join(f"{k}={v[k]}" for k in v))
def test_truth_is_invariant_under_the_variants(vid, var):
    base, got = B.truth_of(vid), B.truth_of(vid, **var)
    for fl in base["floors"]:
        b, g = base["floors"][fl], got["floors"][fl]
        assert [round(r["area_m2"], 9) for r in b["rooms"]] == [round(r["area_m2"], 9) for r in g["rooms"]]
        assert [(o["kind"], o["width_m"]) for o in b["openings"]] == [(o["kind"], o["width_m"]) for o in g["openings"]]
        assert b["walls_by_thickness"] == g["walls_by_thickness"] and b["counts"] == g["counts"]
        pb = [r["point_m"] for r in b["rooms"]] + [o["centre_m"] for o in b["openings"]]
        pg = [r["point_m"] for r in g["rooms"]] + [o["centre_m"] for o in g["openings"]]
        for i in range(1, len(pb)):                                   # a rigid motion keeps every distance
            assert math.dist(pg[0], pg[i]) == pytest.approx(math.dist(pb[0], pb[i]), abs=1e-9)


def test_missing_label_keeps_the_room_in_the_truth():
    t = B.truth_of("SV-A", drop_labels=("A-BTH",))
    r = next(r for r in t["floors"]["GF"]["rooms"] if r["room_id"] == "A-BTH")
    assert r["labelled"] is False and r["code"] is None and r["area_m2"] == pytest.approx(11.2, abs=TOL)
    assert t["floors"]["GF"]["counts"]["unlabelled_rooms"] == 1
    assert B.truth_of("SV-C")["floors"]["GF"]["counts"]["unlabelled_rooms"] == 1


# ---- the DXF written
def _closed_leaf_end(ins, unit):
    """the end of the door block's swing arc (block point (0, 1 m)) in drawing coordinates, m."""
    x, y = ins.dxf.insert.x, ins.dxf.insert.y
    sx, sy, rot = ins.dxf.xscale, ins.dxf.yscale, math.radians(ins.dxf.rotation)
    bx, by = 0.0, unit * sy                                           # (0, unit) scaled
    del sx
    return ((x + bx * math.cos(rot) - by * math.sin(rot)) / unit, (y + bx * math.sin(rot) + by * math.cos(rot)) / unit)


@pytest.mark.parametrize("vid", sorted(V.VILLAS))
@pytest.mark.parametrize("var", VARIANTS, ids=lambda v: "-".join(f"{k}={v[k]}" for k in v) or "plain")
def test_dxf_holds_what_the_truth_says(tmp_path, vid, var):
    ezdxf = pytest.importorskip("ezdxf")
    got = B.write_villa(vid, tmp_path / "v.dxf", **var)
    doc = ezdxf.readfile(got["path"])
    unit, ins = B.UNITS[var.get("units", "mm")]
    L = B.LAYERS[var.get("layers", "AIA")]
    assert doc.header["$INSUNITS"] == ins
    msp = doc.modelspace()
    doors = [e for e in msp.query("INSERT") if e.dxf.layer == L["door"]]
    glaz = msp.query(f'LINE[layer=="{L["glaz"]}"]')
    texts = [e.dxf.text for e in msp.query("TEXT") if e.dxf.layer == L["text"]]
    t = got["truth"]["floors"]
    assert len(doors) == sum(f["counts"]["DOOR"] for f in t.values())
    assert len(glaz) == 2 * sum(f["counts"]["WINDOW"] for f in t.values())
    labelled = [r for f in t.values() for r in f["rooms"] if r["labelled"]]
    assert sorted(x for x in texts if not x.startswith("+")) == sorted(r["label"] for r in labelled)
    titles = sorted(e.dxf.text for e in msp.query("TEXT") if e.dxf.layer == L["title"])
    assert titles == sorted(f["title"] for f in t.values())
    arcs = msp.query(f'ARC[layer=="{L["wall"]}"]')
    assert len(arcs) == (2 if vid == "SV-C" else 0)
    for a in arcs:                                                    # the curved wall faces: r 2.0 and 2.2, 90 deg
        assert a.dxf.radius / unit in (pytest.approx(2.0, abs=1e-9), pytest.approx(2.2, abs=1e-9))
        assert (a.dxf.end_angle - a.dxf.start_angle) % 360 == pytest.approx(90.0, abs=1e-9)
    # every door's closed leaf ends at the far jamb of its own gap (hinge + width along the wall)
    ops = {o["opening_id"]: o for f in t.values() for o in f["openings"] if o["kind"] == "DOOR"}
    for d in doors:
        end = _closed_leaf_end(d, unit)
        hinge = (d.dxf.insert.x / unit, d.dxf.insert.y / unit)
        hits = [o for o in ops.values() if math.dist(end, hinge) == pytest.approx(o["width_m"], abs=1e-6) and
                math.dist(((end[0] + hinge[0]) / 2, (end[1] + hinge[1]) / 2), o["centre_m"]) ==
                pytest.approx(o["wall_t_m"] / 2, abs=1e-6)]
        assert len(hits) == 1, (vid, var, hinge)
        ops.pop(hits[0]["opening_id"])
        assert (d.dxf.xscale * d.dxf.yscale < 0) == (hits[0]["mirrored_block"] != bool(var.get("mirror")))
    assert not ops


def test_units_scale_every_coordinate(tmp_path):
    ezdxf = pytest.importorskip("ezdxf")
    a = ezdxf.readfile(B.write_villa("SV-A", tmp_path / "mm.dxf")["path"]).modelspace()
    b = ezdxf.readfile(B.write_villa("SV-A", tmp_path / "m.dxf", units="m")["path"]).modelspace()
    la = sorted((round(e.dxf.start.x, 6), round(e.dxf.start.y, 6)) for e in a.query("LINE"))
    lb = sorted((round(e.dxf.start.x * 1000, 6), round(e.dxf.start.y * 1000, 6)) for e in b.query("LINE"))
    assert la == lb and len(la) > 50


# ---- the engine on the villas: the silent-omission report (truth independent of the engine)
ENGINE_CASES = [(vid, var) for vid, var in V.FIRST_RUN.items()] + [
    ("SV-A", {"rotate_deg": 37.0}), ("SV-A", {"mirror": True}), ("SV-A", {"units": "m"}),
    ("SV-A", {"layers": "ARABIC"}), ("SV-A", {"drop_labels": ("A-BTH",)}),
    ("SV-C", {"rotate_deg": -121.0, "mirror": True, "units": "m"}),
]


@pytest.mark.parametrize("vid,var", ENGINE_CASES, ids=[f"{v}-" + ("-".join(f"{k}={x[k]}" for k in x) or "plain")
                                                        for v, x in ENGINE_CASES])
def test_engine_report_on_synthetic_villas(tmp_path, vid, var):
    pytest.importorskip("ezdxf")
    got = B.write_villa(vid, tmp_path / f"{vid}.dxf", **var)
    _room, arch, refusal = C.run_engine(got["path"])
    rep = C.compare(got["truth"], arch, refusal)
    (tmp_path / "report.json").write_text(json.dumps(rep, ensure_ascii=False, indent=1, default=str))
    s = rep["summary"]
    print(vid, var, json.dumps(s), rep["silent_omissions"], (refusal or {}).get("message"))
    # the report covers every truth item, each with a status; a missing engine value stays None (never 0)
    t = got["truth"]["floors"]
    assert s["truth_rooms"] == sum(len(f["rooms"]) for f in t.values())
    assert s["truth_openings"] == sum(len(f["openings"]) for f in t.values())
    for f in rep["floors"].values():
        for x in f["rooms"] + f["openings"] + list(f["walls_by_thickness"].values()):
            assert x["status"] in ("ANSWERED", "SILENT_OMISSION")
            if x["status"] == "SILENT_OMISSION":
                assert x["engine"] is None
    # the fixture set every later task must keep passing (T-019): no labelled room, door, window, passage or wall
    # thickness is silently lost; room gross areas, opening kinds and widths agree with the hand truth
    assert rep["silent_omissions"] == []
    assert s["room_gross_agrees"] == s["truth_rooms"]
    assert s["opening_kind_agrees"] == s["opening_width_agrees"] == s["truth_openings"]
    labelled = [x for f in rep["floors"].values() for x in f["rooms"] if x["labelled"]]
    assert all(x["code_agrees"] and x["wet_agrees"] for x in labelled)
