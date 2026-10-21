"""S6 independent reproductions on the current HEAD (read-only: the repository is imported, never modified).

usage: S6_METHOD=ARCH_TAKEOFF_V1|ARCH_TAKEOFF_V2 [S6_EXTRA="--strict-admission"] python3 -I s6_repro_v.py REPO WORK_DIR [case ...]

(S6 Phase 1 version of research/urban_m9_s6/repro/s6_repro.py: the method and extra CLI flags come from the
environment, and a run that stops reports its exit code, its stopping findings and the flags it published.)

Every fixture is generated from the repository's own synthetic villa (tools.arch_synth.villa, hand truth in
arch_synth.TRUTH) and then changed in ONE way that a real consultant drawing commonly shows. The production CLI
(`tools/urban_boq_m9.py arch`) is run as a separate process so that its real exit code is observed.

A case is
    METAMORPHIC  the change must not alter any quantity (compare with the baseline run)
    MUST_BLOCK   the input cannot be measured safely: the run must stop with a non-zero exit and a reason
    CONTROL      a nearby variant that should work (proves the harness, not the engine)
Result per case: FIXED (behaves as expected), REPRODUCED (silent or wrong result), NOT_REPRODUCED, BLOCKED (the
reproduction itself could not run).
"""
import hashlib, json, math, os, shutil, stat, subprocess, sys, textwrap
from pathlib import Path

REPO, WORK = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve()
ONLY = set(sys.argv[3:])
sys.path.insert(0, str(REPO))
import ezdxf                                                   # noqa: E402
from ezdxf.math import Matrix44                               # noqa: E402
from tools import arch_synth as AS                            # noqa: E402

PY = sys.executable
CLI = [PY, "-I", str(REPO / "tools" / "urban_boq_m9.py"), "arch"]
METHOD = os.environ.get("S6_METHOD", "ARCH_TAKEOFF_V1")
EXTRA = os.environ.get("S6_EXTRA", "").split()


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


# ------------------------------------------------------------------ fixture transforms (each: src dxf -> dst dxf)
def base(dst):
    AS.villa(str(dst))


def _scale_all(dst, s, insunits):
    base(dst)
    doc = ezdxf.readfile(str(dst))
    m = Matrix44.scale(s, s, s)
    for e in list(doc.modelspace()):
        e.transform(m)
    doc.header["$INSUNITS"] = insunits
    doc.saveas(str(dst))


def units_m(dst):
    _scale_all(dst, 0.001, 6)


def units_cm(dst):
    _scale_all(dst, 0.1, 5)


def units_inch(dst):
    _scale_all(dst, 1 / 25.4, 1)


def _header(dst, value):
    base(dst)
    doc = ezdxf.readfile(str(dst))
    if value is None:
        del doc.header["$INSUNITS"]
    else:
        doc.header["$INSUNITS"] = value
    doc.saveas(str(dst))


def insunits_0(dst):
    _header(dst, 0)


def insunits_absent(dst):
    _header(dst, None)


def insunits_declared_m_drawn_mm(dst):
    _header(dst, 6)


def paper_space_frames(dst):
    """the sheet frames and plan titles are on a paper-space layout (the plans stay in model space)."""
    base(dst)
    doc = ezdxf.readfile(str(dst))
    msp, ps = doc.modelspace(), doc.layouts.get("Layout1")
    for e in list(msp):
        if e.dxf.layer in ("A-FRAME", "A-TITLE"):
            msp.move_to_layout(e, ps)
    doc.saveas(str(dst))


def no_frame(dst):
    """model space holds the plans and their titles, with no drawn sheet frame (frames only on layouts, or none)."""
    base(dst)
    doc = ezdxf.readfile(str(dst))
    msp = doc.modelspace()
    for e in list(msp):
        if e.dxf.layer == "A-FRAME":
            msp.delete_entity(e)
    doc.saveas(str(dst))


def frame_exploded(dst):
    """each sheet frame drawn as four LINEs (an exploded polyline)."""
    base(dst)
    doc = ezdxf.readfile(str(dst))
    msp = doc.modelspace()
    for e in list(msp):
        if e.dxftype() == "LWPOLYLINE" and e.dxf.layer == "A-FRAME":
            pts = [tuple(p[:2]) for p in e.get_points()]
            for i in range(4):
                msp.add_line(pts[i], pts[(i + 1) % 4], dxfattribs={"layer": "A-FRAME"})
            msp.delete_entity(e)
    doc.saveas(str(dst))


def title_wording(dst):
    """the plan titles read 'GROUND FLOOR LAYOUT' / 'FIRST FLOOR LAYOUT' (a common wording)."""
    base(dst)
    doc = ezdxf.readfile(str(dst))
    for e in doc.modelspace().query("TEXT"):
        if e.dxf.text.endswith("FLOOR PLAN"):
            e.dxf.text = e.dxf.text.replace("FLOOR PLAN", "FLOOR LAYOUT")
    doc.saveas(str(dst))


def _two_in_one(dst, title_at, centred=False):
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
    from ezdxf.enums import TextEntityAlignment
    for title, p in title_at.items():
        t = msp.add_text(title, dxfattribs={"layer": "A-TITLE", "height": 500})
        t.set_placement(p, align=TextEntityAlignment.BOTTOM_CENTER if centred else None)
    doc.saveas(str(dst))


def two_plans_one_frame_left(dst):
    """both plans in ONE sheet frame, each title left-aligned under its plan (a common sheet layout)."""
    _two_in_one(dst, {"GROUND FLOOR PLAN": (0, -1500), "FIRST FLOOR PLAN": (14000, -1500)})


def two_plans_one_frame_centred(dst):
    """CONTROL: the same sheet, each title centred under its plan."""
    _two_in_one(dst, {"GROUND FLOOR PLAN": (6200, -1500), "FIRST FLOOR PLAN": (18700, -1500)}, centred=True)


def _wrap(dst, levels, inner_scale=1.0):
    """move every plan entity (not the frames / titles) into a block nested `levels` deep; the inner geometry may be
    drawn at 1/inner_scale and inserted at inner_scale (a plan pasted as a block from a metre drawing)."""
    base(dst)
    doc = ezdxf.readfile(str(dst))
    msp = doc.modelspace()
    names = [f"PLAN_L{i}" for i in range(1, levels + 1)]
    blocks = [doc.blocks.new(n) for n in names]
    m = Matrix44.scale(1 / inner_scale, 1 / inner_scale, 1 / inner_scale)
    for e in list(msp):
        if e.dxf.layer not in ("A-FRAME", "A-TITLE"):
            if inner_scale != 1.0:
                e.transform(m)
            msp.move_to_layout(e, blocks[0])
    for i in range(1, levels):
        blocks[i].add_blockref(names[i - 1], (0, 0), dxfattribs={"layer": "0"})
    msp.add_blockref(names[-1], (0, 0), dxfattribs={"layer": "0", "xscale": inner_scale, "yscale": inner_scale})
    doc.saveas(str(dst))


def nested_2(dst):
    _wrap(dst, 2)


def nested_3(dst):
    _wrap(dst, 3)


def nested_1_scaled_1000(dst):
    _wrap(dst, 1, inner_scale=1000.0)


def _columns_variant(dst, how, positions=((2000, 6000), (5000, 2000), (7600, 6600))):
    """the GF columns redrawn; the 1F has none. `how`:
       INSERT     a COL400 block (outline + hatch on layer A-COL) inserted once per column
       INSERT_L0  the same block with its outline and hatch on layer 0, the INSERT on A-COL (CAD inheritance)
       MINSERT    the same block as ONE MINSERT (1 row x n columns) per row of columns
       SOLID      outline polyline + a SOLID fill (no HATCH)
       SOLID_ONLY a SOLID fill only (no outline)
       CROSSED    outline + two diagonals (no fill)
       EXPLODED   four LINEs + a HATCH
    """
    base(dst)
    doc = ezdxf.readfile(str(dst))
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
                gaps = {round(b_ - a_, 6) for a_, b_ in zip(xs, xs[1:])}
                assert len(gaps) <= 1, "MINSERT needs equal spacing"
                ins = msp.add_blockref("COL400", (xs[0], y), dxfattribs={"layer": "A-COL"})
                if len(xs) > 1:
                    ins.dxf.column_count = len(xs)
                    ins.dxf.column_spacing = gaps.pop()
        else:
            for x, y in positions:
                msp.add_blockref("COL400", (x, y), dxfattribs={"layer": "A-COL"})
    else:
        for x, y in positions:
            pts = [(x + a, y + b_) for a, b_ in sq]
            if how in ("SOLID", "CROSSED", "POLY"):
                msp.add_lwpolyline(pts, close=True, dxfattribs={"layer": "A-COL"})
            if how in ("SOLID", "SOLID_ONLY"):
                # SOLID vertex order is 1-2-4-3 (a "bow-tie" order for a rectangle)
                msp.add_solid([pts[0], pts[1], pts[3], pts[2]], dxfattribs={"layer": "A-COL"})
            if how == "CROSSED":
                msp.add_line(pts[0], pts[2], dxfattribs={"layer": "A-COL"})
                msp.add_line(pts[1], pts[3], dxfattribs={"layer": "A-COL"})
            if how == "POLY":
                h = msp.add_hatch(dxfattribs={"layer": "A-COL"})
                h.set_solid_fill()
                h.paths.add_polyline_path(pts, is_closed=True)
            if how == "EXPLODED":
                for i in range(4):
                    msp.add_line(pts[i], pts[(i + 1) % 4], dxfattribs={"layer": "A-COL"})
                h = msp.add_hatch(dxfattribs={"layer": "A-COL"})
                h.set_solid_fill()
                h.paths.add_polyline_path(pts, is_closed=True)
    doc.saveas(str(dst))


MINSERT_POS = ((2000, 2000), (5000, 2000), (7600, 6600))      # two columns on one row (equal spacing) + one


def col_insert_control(dst):
    _columns_variant(dst, "INSERT", MINSERT_POS)


def col_minsert(dst):
    _columns_variant(dst, "MINSERT", MINSERT_POS)


def col_insert_layer0(dst):
    _columns_variant(dst, "INSERT_L0")


def col_solid(dst):
    _columns_variant(dst, "SOLID")


def col_solid_only(dst):
    _columns_variant(dst, "SOLID_ONLY")


def col_crossed(dst):
    _columns_variant(dst, "CROSSED")


def col_exploded(dst):
    _columns_variant(dst, "EXPLODED")


def col_two_only(dst):
    """GF with two columns (both in LIVING) instead of three."""
    _columns_variant(dst, "POLY", ((2000, 6000), (5000, 2000)))


def rotate_all_30(dst):
    """the whole drawing (frames included) rotated 30 degrees: a plan drawn on a site-north grid."""
    base(dst)
    doc = ezdxf.readfile(str(dst))
    m = Matrix44.z_rotate(math.radians(30))
    for e in list(doc.modelspace()):
        e.transform(m)
    doc.saveas(str(dst))


def rotate_plans_30(dst):
    """the plans rotated 30 degrees about their own centres inside axis-aligned sheet frames."""
    base(dst)
    doc = ezdxf.readfile(str(dst))
    for e in list(doc.modelspace()):
        if e.dxf.layer in ("A-FRAME", "A-TITLE"):
            continue
        p = e.dxf.insert if e.dxf.hasattr("insert") else None
        x = (p.x if p is not None else (e.dxf.start.x if e.dxftype() == "LINE" else
             (list(e.vertices_in_wcs())[0].x if e.dxftype() == "LWPOLYLINE" else 0.0)))
        cx = 6200 if x < 30000 else 40000 + 4700
        cy = 4700 if x < 30000 else 4000
        e.transform(Matrix44.chain(Matrix44.translate(-cx, -cy, 0), Matrix44.z_rotate(math.radians(30)),
                                   Matrix44.translate(cx, cy, 0)))
    doc.saveas(str(dst))


def layer_off_partition(dst):
    """a partition wall on a layer that is switched OFF and FROZEN (a demolished / option wall) splits LIVING."""
    base(dst)
    doc = ezdxf.readfile(str(dst))
    lay = doc.layers.add("A-WALL-DEMO")
    lay.off()
    lay.freeze()
    msp = doc.modelspace()
    for x in (3000, 3200):
        msp.add_line((x, 200), (x, 9200), dxfattribs={"layer": "A-WALL-DEMO"})
    doc.saveas(str(dst))


def nonuniform_door(dst):
    """every door block inserted with a non-uniform scale (leaf 1.0 x the width, swing 1.15 x): a stretched door."""
    base(dst)
    doc = ezdxf.readfile(str(dst))
    for e in doc.modelspace().query("INSERT"):
        if e.dxf.name == "DOOR1000":
            e.dxf.yscale = e.dxf.yscale * 1.15
    doc.saveas(str(dst))


def xref_missing(dst):
    """an external reference (XREF) to a file that is not supplied, inserted at the GF plan (e.g. the furniture or
    the structural grid kept in a separate file)."""
    base(dst)
    doc = ezdxf.readfile(str(dst))
    doc.add_xref_def("GF_PARTITIONS.dxf", "GF_PARTITIONS")
    doc.modelspace().add_blockref("GF_PARTITIONS", (0, 0), dxfattribs={"layer": "A-XREF"})
    doc.saveas(str(dst))


def mtext_labels(dst):
    """CONTROL: the room words as formatted MTEXT ({\\fArial|b1;LIVING})."""
    base(dst)
    doc = ezdxf.readfile(str(dst))
    msp = doc.modelspace()
    for e in list(msp.query("TEXT")):
        if e.dxf.layer == "A-TEXT" and e.dxf.text.isascii() and e.dxf.text.isupper():
            p = e.dxf.insert
            msp.add_mtext("{\\fArial|b1;" + e.dxf.text + "}", dxfattribs={
                "layer": "A-TEXT", "char_height": 200, "insert": (p.x, p.y)})
            msp.delete_entity(e)
    doc.saveas(str(dst))


def frozen_old_label(dst):
    """an older room word on a FROZEN + OFF annotation layer ('KITCHEN' inside the bedroom, from a superseded
    design option): CAD shows nothing there."""
    base(dst)
    doc = ezdxf.readfile(str(dst))
    lay = doc.layers.add("A-TEXT-OLD")
    lay.off()
    lay.freeze()
    doc.modelspace().add_text("KITCHEN", dxfattribs={"layer": "A-TEXT-OLD", "height": 200}).set_placement((7800, 6000))
    doc.saveas(str(dst))


def empty_drawing(dst):
    """a valid DXF with no entities (what a failed converter can leave)."""
    doc = ezdxf.new("R2018")
    doc.header["$INSUNITS"] = 4
    doc.saveas(str(dst))


CASES = {
    # name: (builder, kind, what the research claims / why it matters)
    "r00_baseline": (base, "CONTROL", "the synthetic villa as committed"),
    "r01_units_m": (units_m, "METAMORPHIC", "CAD-05/06: a metre drawing ($INSUNITS 6)"),
    "r02_units_cm": (units_cm, "METAMORPHIC", "a centimetre drawing ($INSUNITS 5)"),
    "r03_units_inch": (units_inch, "METAMORPHIC", "an inch drawing ($INSUNITS 1)"),
    "r04_insunits_0": (insunits_0, "MUST_BLOCK_OR_INFER", "CAD-04: $INSUNITS 0 (unitless)"),
    "r05_insunits_absent": (insunits_absent, "MUST_BLOCK_OR_INFER", "CAD-04: $INSUNITS missing from the header"),
    "r06_insunits_contradicted": (insunits_declared_m_drawn_mm, "MUST_BLOCK", "declared metres, drawn in mm"),
    "r07_paper_space_frames": (paper_space_frames, "MUST_BLOCK", "CAD-12 / r28: frames + titles on a layout"),
    "r08_no_frame": (no_frame, "MUST_BLOCK", "plans + titles in model space, no drawn sheet frame"),
    "r09_frame_exploded": (frame_exploded, "METAMORPHIC", "sheet frame as four LINEs"),
    "r10_title_wording": (title_wording, "MUST_BLOCK", "titles 'GROUND FLOOR LAYOUT' (no 'PLAN')"),
    "r11_two_plans_left_titles": (two_plans_one_frame_left, "METAMORPHIC", "CAD-11: two plans in one frame"),
    "r12_two_plans_centred_titles": (two_plans_one_frame_centred, "CONTROL", "CAD-11 control"),
    "r13_nested_2": (nested_2, "METAMORPHIC", "CAD-01: the plan inside a block nested 2 deep"),
    "r14_nested_3": (nested_3, "METAMORPHIC", "CAD-01: nested 3 deep"),
    "r15_nested_scaled_1000": (nested_1_scaled_1000, "METAMORPHIC", "a metre plan block inserted at x1000"),
    "r16_col_insert_control": (col_insert_control, "CONTROL", "columns as INSERTs (MINSERT control)"),
    "r17_col_minsert": (col_minsert, "METAMORPHIC", "CAD-02: columns as a MINSERT (same places as r16)"),
    "r18_col_insert_layer0": (col_insert_layer0, "METAMORPHIC", "column block content on layer 0"),
    "r19_col_solid": (col_solid, "METAMORPHIC", "column outline + SOLID fill"),
    "r20_col_solid_only": (col_solid_only, "METAMORPHIC", "column as a SOLID only"),
    "r21_col_crossed": (col_crossed, "METAMORPHIC", "column outline + diagonals"),
    "r22_col_exploded": (col_exploded, "METAMORPHIC", "column as four LINEs + HATCH"),
    "r23_col_two_only": (col_two_only, "TRUTH", "a plan with only two columns"),
    "r24_rotate_all_30": (rotate_all_30, "METAMORPHIC_OR_BLOCK", "r25: whole drawing rotated 30 degrees"),
    "r25_rotate_plans_30": (rotate_plans_30, "METAMORPHIC", "plans rotated 30 degrees inside upright frames"),
    "r26_layer_off_partition": (layer_off_partition, "METAMORPHIC", "CAD-07: a wall on an OFF + FROZEN layer"),
    "r27_nonuniform_door": (nonuniform_door, "METAMORPHIC", "CAD-09: door blocks with non-uniform scale"),
    "r28_xref_missing": (xref_missing, "MUST_FLAG", "r23: an unresolved XREF"),
    "r29_mtext_labels": (mtext_labels, "CONTROL", "room words as formatted MTEXT"),
    "r30_empty_drawing": (empty_drawing, "MUST_BLOCK", "a DXF with no entities"),
    "r31_frozen_old_label": (frozen_old_label, "METAMORPHIC", "CAD-07: a room word on a FROZEN + OFF layer"),
}


def _flags(out):
    """the admission evidence a run published: stopping findings, and the review / warning flags."""
    d = out / "DRAWING_DISCOVERY.json"
    if not d.exists():
        return {}
    D = json.loads(d.read_text())
    fs = [dict(f, stage=st) for st, v in D["stages"].items() for f in v["findings"]]
    return {"stopping": D.get("gates", {}).get("stopping"),
            "flags": sorted({f"{f['level']}:{f['code']}" for f in fs})}


def summarise(out, proc):
    s = {"exit": proc.returncode, "stderr_tail": proc.stderr.strip().splitlines()[-2:],
         "traceback": "Traceback (most recent call last)" in proc.stderr}
    s.update(_flags(out))
    fc = out / "FINISH_COVERAGE.json"
    if fc.exists():
        s["coverage_gates"] = {f["floor"]: f["gate"] for f in json.loads(fc.read_text())["floors"]}
    p = out / "ARCH_PLAN.json"
    if not p.exists():
        s["outputs"] = sorted(x.name for x in out.iterdir()) if out.exists() else []
        return s
    P = json.loads(p.read_text())
    R = json.loads((out / "ARCH_ROOMS.json").read_text())["rooms"]
    O = json.loads((out / "ARCH_OPENINGS.json").read_text())
    O = O["openings"] if isinstance(O, dict) else O
    L = json.loads((out / "BOQ_LINES.json").read_text())
    L = L["lines"] if isinstance(L, dict) else L
    U = json.loads((out / "UNRESOLVED.json").read_text())
    U = U.get("unresolved", U) if isinstance(U, dict) else U
    FA = {f["floor"]: f for f in json.loads((out / "ARCH_FLOOR_AREAS.json").read_text())["floors"]}
    run = P["run"]
    s.update(unit_m=run.get("unit_m"), insunits=run.get("insunits"), drawing_sha=run["drawing"]["sha256"][:12],
             other_frames=[(f.get("sheet_id"), f.get("why")) for f in P.get("other_frames") or ()],
             hatch_reader=run.get("hatch_reader"), lines=len(L), unresolved=len(U),
             regions=[])
    for reg in P["regions"]:
        fl = reg["floor"]
        rr = sorted((("+".join(r.get("codes") or []) or "-"), r["class"], round(r["gross_m2"] or 0, 3),
                     round(r["area_m2"] or 0, 3)) for r in R if r.get("region_id") == reg["region_id"])
        fa = FA.get(fl) or {}
        cat = {k: v for k, v in (fa.get("categories_m2") or {}).items() if v}
        s["regions"].append({"floor": fl, "state": reg["stage_state"], "warning": reg.get("warning"),
                             "roles": reg.get("layer_roles"), "columns": reg.get("columns"),
                             "openings": reg.get("openings"), "door_symbols": reg.get("door_symbols"),
                             "plate_m2": round((reg.get("plate") or {}).get("largest_m2") or 0, 3),
                             "rooms": rr, "categories_m2": cat})
    return s


def key(s):
    """the quantity fingerprint compared between a variant and the baseline."""
    return {r["floor"]: {"rooms": r["rooms"], "openings": r["openings"], "columns": r["columns"],
                         "plate_m2": r["plate_m2"]} for r in s.get("regions") or ()} | {"lines": s.get("lines")}


def judge(name, kind, s, b):
    if "regions" not in s:
        crashed = s["exit"] != 0
        unhandled = s.get("traceback")
        if crashed and not unhandled and s.get("stopping"):
            # an admission stop with its reason published (exit 2): loud for every kind
            return "FIXED", "blocked loudly: " + ",".join(x.split(":", 1)[1] for x in s["stopping"])
        return ("FIXED" if kind.startswith("MUST_BLOCK") and crashed and not unhandled
                else "REPRODUCED"), (("UNHANDLED CRASH: " if unhandled else "stopped: ") + s["stderr_tail"][-1]) \
            if crashed else "no outputs"
    same = key(s) == key(b)
    empty = s["lines"] == 0 or not s["regions"]
    if kind == "CONTROL":
        return ("NOT_REPRODUCED" if same and not empty else "REPRODUCED"), \
            "control " + ("matches baseline" if same else "DIFFERS from baseline (see detail)")
    if kind in ("METAMORPHIC", "METAMORPHIC_OR_BLOCK"):
        if same:
            return "NOT_REPRODUCED", "identical quantities"
        if s["exit"] != 0:
            return "FIXED", "blocked loudly"
        named = [f for f in s.get("flags") or () if f.split(":")[0] in ("REVIEW_REQUIRED", "BLOCKED_ITEM")
                 and f.split(":")[1] not in ("NO_SECTION_SOURCE",)]
        if named:
            return "FLAGGED", "quantity changed (exit 0) WITH a published review flag: " + ",".join(named)
        return "REPRODUCED", ("SILENT EMPTY BOQ (exit 0)" if empty else "SILENT QUANTITY CHANGE (exit 0)")
    if kind in ("MUST_BLOCK", "MUST_BLOCK_OR_INFER"):
        if s["exit"] != 0:
            return "FIXED", "blocked loudly"
        if kind == "MUST_BLOCK_OR_INFER" and same:
            return "NOT_REPRODUCED", "unit inferred, quantities identical"
        return "REPRODUCED", ("SILENT EMPTY BOQ (exit 0)" if empty else "measured without blocking (exit 0)")
    if kind == "TRUTH":
        return "SEE_DETAIL", "compare with the hand truth"
    if kind == "MUST_FLAG":
        return ("REPRODUCED" if s["exit"] == 0 else "FIXED"), "exit %d" % s["exit"]
    return "SEE_DETAIL", ""


def run_case(name):
    d = WORK / name
    if d.exists():
        shutil.rmtree(d)
    d.mkdir(parents=True)
    dxf = d / "plan.dxf"
    CASES[name][0](dxf)
    out = d / "out"
    proc = subprocess.run(CLI + ["--drawings", str(dxf), "--out", str(out), "--method", METHOD, "--no-svg"] + EXTRA,
                          capture_output=True, text=True, cwd=str(WORK))
    (d / "stdout.txt").write_text(proc.stdout)
    (d / "stderr.txt").write_text(proc.stderr)
    s = summarise(out, proc)
    s["fixture_sha256"] = sha(dxf)
    return s


def main():
    WORK.mkdir(parents=True, exist_ok=True)
    names = [n for n in CASES if not ONLY or n in ONLY or n == "r00_baseline"]
    res = {}
    for n in names:
        res[n] = run_case(n)
    b = res["r00_baseline"]
    rows = []
    for n in names:
        kind, why = CASES[n][1], CASES[n][2]
        verdict, note = judge(n, kind, res[n], b)
        res[n]["verdict"], res[n]["note"], res[n]["kind"], res[n]["claim"] = verdict, note, kind, why
        rows.append((n, kind, verdict, note))
        print(f"{n:32s} {kind:22s} {verdict:15s} exit={res[n]['exit']} {note}")
    (WORK / "S6_REPRO_RESULTS.json").write_text(json.dumps(res, indent=1, ensure_ascii=True))


if __name__ == "__main__":
    main()
