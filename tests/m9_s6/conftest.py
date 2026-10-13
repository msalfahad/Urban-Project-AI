"""M9 S6 Phase 1 fixtures: the synthetic villa (tools.arch_synth.villa, hand truth in arch_synth.TRUTH) changed in
ONE way a consultant drawing commonly shows - the transforms of research/urban_m9_s6/repro/s6_repro.py - and the
production CLI run in process (tools.urban_boq_m9.main), so the real exit code and the published files are tested."""

from __future__ import annotations

import json
import math

import pytest

ezdxf = pytest.importorskip("ezdxf")

from ezdxf.math import Matrix44                                # noqa: E402

from tools import arch_synth as AS                            # noqa: E402

V1, V2 = "ARCH_TAKEOFF_V1", "ARCH_TAKEOFF_V2"


def base(dst):
    AS.villa(str(dst))


def _edit(dst, fn):
    base(dst)
    doc = ezdxf.readfile(str(dst))
    fn(doc)
    doc.saveas(str(dst))


def scaled(dst, s, insunits):
    def fn(doc):
        m = Matrix44.scale(s, s, s)
        for e in list(doc.modelspace()):
            e.transform(m)
        doc.header["$INSUNITS"] = insunits
    _edit(dst, fn)


def header(dst, value):
    def fn(doc):
        if value is None:
            del doc.header["$INSUNITS"]
        else:
            doc.header["$INSUNITS"] = value
    _edit(dst, fn)


def paper_space_frames(dst):
    def fn(doc):
        msp, ps = doc.modelspace(), doc.layouts.get("Layout1")
        for e in list(msp):
            if e.dxf.layer in ("A-FRAME", "A-TITLE"):
                msp.move_to_layout(e, ps)
    _edit(dst, fn)


def no_frame(dst):
    def fn(doc):
        msp = doc.modelspace()
        for e in list(msp):
            if e.dxf.layer == "A-FRAME":
                msp.delete_entity(e)
    _edit(dst, fn)


def frame_exploded(dst):
    def fn(doc):
        msp = doc.modelspace()
        for e in list(msp):
            if e.dxftype() == "LWPOLYLINE" and e.dxf.layer == "A-FRAME":
                pts = [tuple(p[:2]) for p in e.get_points()]
                for i in range(4):
                    msp.add_line(pts[i], pts[(i + 1) % 4], dxfattribs={"layer": "A-FRAME"})
                msp.delete_entity(e)
    _edit(dst, fn)


def frame_on_wall_layer(dst):
    """each sheet frame drawn as four LINEs on the WALL layer (a real-plan variant showed the plate became the frame)."""
    def fn(doc):
        msp = doc.modelspace()
        for e in list(msp):
            if e.dxftype() == "LWPOLYLINE" and e.dxf.layer == "A-FRAME":
                pts = [tuple(p[:2]) for p in e.get_points()]
                for i in range(4):
                    msp.add_line(pts[i], pts[(i + 1) % 4], dxfattribs={"layer": "A-WALL"})
                msp.delete_entity(e)
    _edit(dst, fn)


def title_wording(dst):
    def fn(doc):
        for e in doc.modelspace().query("TEXT"):
            if e.dxf.text.endswith("FLOOR PLAN"):
                e.dxf.text = e.dxf.text.replace("FLOOR PLAN", "FLOOR LAYOUT")
    _edit(dst, fn)


def rotate_all_30(dst):
    def fn(doc):
        m = Matrix44.z_rotate(math.radians(30))
        for e in list(doc.modelspace()):
            e.transform(m)
    _edit(dst, fn)


def two_plans_one_frame(dst, centred=False):
    from ezdxf.enums import TextEntityAlignment
    doc = ezdxf.new("R2018")
    doc.header["$INSUNITS"] = 4
    blk = doc.blocks.new("DOOR1000")
    blk.add_line((0, 0), (1000, 0), dxfattribs={"layer": "0"})
    blk.add_arc((0, 0), 1000, 0, 90, dxfattribs={"layer": "0"})
    msp = doc.modelspace()
    msp.add_lwpolyline([(-6000, -8000), (32000, -8000), (32000, 18000), (-6000, 18000)], close=True,
                       dxfattribs={"layer": "A-FRAME"})
    common = dict(dx=0.0, dy=0.0, mirror=False, quarter_turns=0, variant=None)
    AS._plan(msp, rooms=AS.GF_ROOMS, outer=AS.GF_OUTER, labels=AS.GF_LABELS, words=AS.GF_WORDS,
             openings=AS.GF_OPENINGS, columns=AS.GF_COLUMNS, level="+0.00", treads=(), origin=(0, 0), **common)
    AS._plan(msp, rooms=AS.F1_ROOMS, outer=AS.F1_OUTER, labels=AS.F1_LABELS, words=AS.F1_WORDS,
             openings=AS.F1_OPENINGS, columns=(), level="+3.50", treads=AS.F1_TREADS, origin=(14000, 0), **common)
    titles = ({"GROUND FLOOR PLAN": (6200, -1500), "FIRST FLOOR PLAN": (18700, -1500)} if centred else
              {"GROUND FLOOR PLAN": (0, -1500), "FIRST FLOOR PLAN": (14000, -1500)})
    for title, p in titles.items():
        t = msp.add_text(title, dxfattribs={"layer": "A-TITLE", "height": 500})
        t.set_placement(p, align=TextEntityAlignment.BOTTOM_CENTER if centred else None)
    doc.saveas(str(dst))


def nested(dst, levels=2):
    def fn(doc):
        msp = doc.modelspace()
        names = [f"PLAN_L{i}" for i in range(1, levels + 1)]
        blocks = [doc.blocks.new(n) for n in names]
        for e in list(msp):
            if e.dxf.layer not in ("A-FRAME", "A-TITLE"):
                msp.move_to_layout(e, blocks[0])
        for i in range(1, levels):
            blocks[i].add_blockref(names[i - 1], (0, 0), dxfattribs={"layer": "0"})
        msp.add_blockref(names[-1], (0, 0), dxfattribs={"layer": "0"})
    _edit(dst, fn)


COLS = ((2000, 6000), (5000, 2000), (7600, 6600))
MINSERT_COLS = ((2000, 2000), (5000, 2000), (7600, 6600))


def columns(dst, how, positions=COLS):
    """the GF columns redrawn (the 1F has none): INSERT / INSERT_L0 / MINSERT / SOLID / SOLID_ONLY / EXPLODED / POLY"""
    def fn(doc):
        msp = doc.modelspace()
        for e in list(msp):
            if e.dxf.layer == "A-COL":
                msp.delete_entity(e)
        sq = [(0, 0), (400, 0), (400, 400), (0, 400)]
        if how in ("INSERT", "INSERT_L0", "MINSERT"):
            lay = "0" if how == "INSERT_L0" else "A-COL"
            b = doc.blocks.new("COL400")
            b.add_lwpolyline(sq, close=True, dxfattribs={"layer": lay})
            h = b.add_hatch(dxfattribs={"layer": lay})
            h.set_solid_fill()
            h.paths.add_polyline_path(sq, is_closed=True)
            if how == "MINSERT":
                rows = {}
                for x, y in positions:
                    rows.setdefault(y, []).append(x)
                for y, xs in rows.items():
                    xs = sorted(xs)
                    ins = msp.add_blockref("COL400", (xs[0], y), dxfattribs={"layer": "A-COL"})
                    if len(xs) > 1:
                        ins.dxf.column_count = len(xs)
                        ins.dxf.column_spacing = xs[1] - xs[0]
            else:
                for x, y in positions:
                    msp.add_blockref("COL400", (x, y), dxfattribs={"layer": "A-COL"})
            return
        for x, y in positions:
            pts = [(x + a, y + b_) for a, b_ in sq]
            if how in ("SOLID", "POLY"):
                msp.add_lwpolyline(pts, close=True, dxfattribs={"layer": "A-COL"})
            if how in ("SOLID", "SOLID_ONLY"):
                msp.add_solid([pts[0], pts[1], pts[3], pts[2]], dxfattribs={"layer": "A-COL"})
            if how == "EXPLODED":
                for i in range(4):
                    msp.add_line(pts[i], pts[(i + 1) % 4], dxfattribs={"layer": "A-COL"})
            if how in ("EXPLODED", "POLY"):
                h = msp.add_hatch(dxfattribs={"layer": "A-COL"})
                h.set_solid_fill()
                h.paths.add_polyline_path(pts, is_closed=True)
    _edit(dst, fn)


def layer_off_partition(dst):
    def fn(doc):
        lay = doc.layers.add("A-WALL-DEMO")
        lay.off()
        lay.freeze()
        for x in (3000, 3200):
            doc.modelspace().add_line((x, 200), (x, 9200), dxfattribs={"layer": "A-WALL-DEMO"})
    _edit(dst, fn)


def nonuniform_door(dst):
    def fn(doc):
        for e in doc.modelspace().query("INSERT"):
            if e.dxf.name == "DOOR1000":
                e.dxf.yscale = e.dxf.yscale * 1.15
    _edit(dst, fn)


def xref_missing(dst):
    def fn(doc):
        doc.add_xref_def("GF_PARTITIONS.dxf", "GF_PARTITIONS")
        doc.modelspace().add_blockref("GF_PARTITIONS", (0, 0), dxfattribs={"layer": "A-XREF"})
    _edit(dst, fn)


def empty_drawing(dst):
    doc = ezdxf.new("R2018")
    doc.header["$INSUNITS"] = 4
    doc.saveas(str(dst))


VARIANTS = {
    "base": base,
    "units_m": lambda d: scaled(d, 0.001, 6),
    "units_cm": lambda d: scaled(d, 0.1, 5),
    "units_in": lambda d: scaled(d, 1 / 25.4, 1),
    "insunits_0": lambda d: header(d, 0),
    "insunits_absent": lambda d: header(d, None),
    "insunits_contradicted": lambda d: header(d, 6),
    "paper_space_frames": paper_space_frames,
    "no_frame": no_frame,
    "frame_exploded": frame_exploded,
    "frame_on_wall_layer": frame_on_wall_layer,
    "title_wording": title_wording,
    "rotate_all_30": rotate_all_30,
    "two_plans_left": two_plans_one_frame,
    "two_plans_centred": lambda d: two_plans_one_frame(d, centred=True),
    "nested_2": lambda d: nested(d, 2),
    "nested_3": lambda d: nested(d, 3),
    "col_insert": lambda d: columns(d, "INSERT", MINSERT_COLS),
    "col_minsert": lambda d: columns(d, "MINSERT", MINSERT_COLS),
    "col_layer0": lambda d: columns(d, "INSERT_L0"),
    "col_solid": lambda d: columns(d, "SOLID"),
    "col_solid_only": lambda d: columns(d, "SOLID_ONLY"),
    "col_exploded": lambda d: columns(d, "EXPLODED"),
    "col_two_only": lambda d: columns(d, "POLY", COLS[:2]),
    "layer_off_partition": layer_off_partition,
    "nonuniform_door": nonuniform_door,
    "xref_missing": xref_missing,
    "empty": empty_drawing,
}


@pytest.fixture
def build(tmp_path):
    def _b(name):
        p = tmp_path / f"{name}.dxf"
        VARIANTS[name](p)
        return p
    return _b


@pytest.fixture
def cli(capsys):
    """the production CLI in process: -> (exit code, stdout, stderr)."""
    from tools import urban_boq_m9 as M9

    def _run(*args):
        code = M9.main(["arch", *map(str, args)])
        cap = capsys.readouterr()
        return code, cap.out, cap.err
    return _run


def read(out, name):
    return json.loads((out / name).read_text(encoding="utf-8"))


def lines_of(out):
    L = read(out, "BOQ_LINES.json")
    return L["lines"] if isinstance(L, dict) else L


def findings(report, level=None):
    return [dict(f, stage=s) for s, v in report["stages"].items() for f in v["findings"]
            if level is None or f["level"] == level]


def fingerprint(room, arch):
    """the unit-free quantity fingerprint (room ids and drawing coordinates excluded)."""
    q = sorted((ln["location"]["floor"], ln["item_code"], ln["unit"], ln["evidence_state"],
                "-" if ln.get("measured_net") is None else f"{ln['measured_net']:.6f}") for ln in room["lines"])
    rooms = sorted((r["floor"], r["class"], "+".join(r.get("codes") or []), round(r["area_m2"] or 0, 6),
                    round(r.get("gross_m2") or 0, 6)) for r in arch["rooms"])
    ops = sorted((o["floor"], o["kind"], round(o["width_m"], 6)) for o in arch["openings"])
    regs = sorted((r["floor"], r["stage_state"], r.get("columns"), round((r.get("plate") or {}).get("largest_m2") or 0, 6))
                  for r in arch["regions"])
    return {"lines": q, "rooms": rooms, "openings": ops, "regions": regs}


class _Helpers:
    read = staticmethod(read)
    lines_of = staticmethod(lines_of)
    findings = staticmethod(findings)
    fingerprint = staticmethod(fingerprint)
    variants = VARIANTS


@pytest.fixture
def h():
    return _Helpers
