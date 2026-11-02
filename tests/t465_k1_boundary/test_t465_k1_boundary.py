"""T-465 (owner directive 2026-11-02, D4): the five ezdxf imports outside the K2 route removed, behaviour unchanged.

Hand / reference cases (synthetic drawings built here, not the training villa):
- arch_v30.strap_changes, arch_v302.schedule_rows_from_drawing, concrete_ledger_v3.read_section_drawing read the DXF
  through the K2 route (kernel_ezdxf.load); a file that cannot be read still RAISES (never 0 straps / rows / dims).
- plot_edge_members._xclipped answers exactly as ezdxf.xclip.XClip(ins).has_clipping_path on every case: no
  extension dictionary, a dictionary without ACAD_FILTER, ACAD_FILTER without SPATIAL, ACAD_FILTER that is not a
  dictionary, a real XCLIP (in memory and after a save / reload), a DictionaryWithDefault ACAD_FILTER.
- opening_area.read_view with the caller's flatten gives the same segments as the pre-T-465 call
  (ezdxf.path.make_path(e).flattening(d)) on a bulged LWPOLYLINE, a POLYLINE, an ARC, a mirrored and a rotated
  nested INSERT, in millimetre and metre drawings; without flatten a curve raises FlattenNotGiven, also inside a block
  (never swallowed into an 'unreadable block'), while a lines-only view still reads.
- boundary: no engine/source module but the K2 route imports ezdxf; the released V2.9 + route G code imports no
  pymupdf / fitz (no AGPL dependency on the released path).
"""
from __future__ import annotations

import ast
import json
import math
from pathlib import Path

import pytest

ezdxf = pytest.importorskip("ezdxf")
from ezdxf import path as ezpath  # noqa: E402
from ezdxf.xclip import XClip  # noqa: E402

from engine.source import arch_v30 as A30  # noqa: E402
from engine.source import arch_v302 as A302  # noqa: E402
from engine.source import concrete_ledger_v3 as CL3  # noqa: E402
from engine.source import opening_area as OA  # noqa: E402
from engine.source import plot_edge_members as PEM  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]


def _imports(p):
    out = set()
    for n in ast.walk(ast.parse(p.read_text(encoding="utf-8"))):
        if isinstance(n, ast.Import):
            out |= {a.name for a in n.names}
        elif isinstance(n, ast.ImportFrom) and n.module and not n.level:
            out.add(n.module)
    return out


# ------------------------------------------------------------------------------------------- boundary
def test_no_engine_source_module_but_the_k2_route_imports_ezdxf():
    bad = [str(p.relative_to(ROOT)) for p in sorted((ROOT / "engine" / "source").rglob("*.py"))
           if p.name != "kernel_ezdxf.py" and any(n == "ezdxf" or n.startswith("ezdxf.") for n in _imports(p))]
    assert bad == []


def test_released_path_agpl_pdf_reader_is_only_the_known_frozen_intake():
    """F-T465-1: the released V2.9 + route G closure (T-467 trace) imports PyMuPDF (AGPL) in ONE place, the frozen
    tools/urban_intake.py read_pdf (lazy `import fitz`, reached only for a .pdf input). It cannot be removed in place
    (released code, freeze index V2); it needs a new released-path version. Pinned so a NEW AGPL import on the
    released path fails, and so this one is never silently counted as closed."""
    spec = json.loads((ROOT / "research/freeze_integrity/RELEASED_PATH_V2_9_ROUTE_G.json").read_text(encoding="utf-8"))
    code = [c for c in spec["code"] if c.endswith(".py")]
    assert len(code) > 50                                           # the traced closure, not an empty list
    hits = sorted(c for c in code if any(n.split(".")[0] in ("pymupdf", "fitz") for n in _imports(ROOT / c)))
    assert hits == ["tools/urban_intake.py"]
    assert "engine/source/opening_height_pdf.py" not in code       # the engine's pymupdf user is off the released path


# ------------------------------------------------------------------------------------------- K2 readers
def _bad_dxf(tmp_path):
    f = tmp_path / "broken.dxf"
    f.write_text("0\nSECTION\n2\nHEADER\n9\n$ACADVER\n1\nAC1015\n0\nENDSEC\n0\nSECTION\n2\nENTITIES\n0\nLINE\n",
                 encoding="utf-8")                                  # truncated: no ENDSEC / EOF
    return f


def _strap_route():
    band = {"band_id": "BAND0001", "family": "STRAP_BEAM", "mark": "SB1", "handles": [], "state": "BOUND"}
    return {"generic": {"D": {"unit_m": 0.001, "sheets": {"SH1": {"straps": {"layers": ["S-FTG"], "bands": [band]}}}}}}


@pytest.mark.parametrize("which", ["missing", "broken"])
def test_strap_changes_unreadable_drawing_raises_never_zero(tmp_path, which):
    f = tmp_path / "absent.dxf" if which == "missing" else _bad_dxf(tmp_path)
    base = [{"item_code": "STR.CONC.STRAP", "location": {"element_id": "BAND0001"}}]
    with pytest.raises(OSError, match="strap_changes"):
        A30.strap_changes(_strap_route(), f, base)


def test_schedule_rows_read_through_k2(tmp_path):
    doc = ezdxf.new("R2010")
    blk = doc.blocks.new("FROW")
    for i, tag in enumerate(("FO-TY", "W", "L", "DEPTH", "SH-B", "SH-D", "LO-B", "LO-D")):
        blk.add_attdef(tag, (i * 100, 0))
    msp = doc.modelspace()
    cells = {"FO-TY": "F1", "W": "150", "L": "200", "DEPTH": "60", "SH-B": "8", "SH-D": "16", "LO-B": "10",
             "LO-D": "16"}
    ins = msp.add_blockref("FROW", (0, 0))
    ins.add_auto_attribs(cells)
    msp.add_blockref("FROW", (0, 500))                              # a block without attributes: not a row
    f = tmp_path / "sched.dxf"
    doc.saveas(f)
    rows = A302.schedule_rows_from_drawing(f, "cm")
    from engine.source import footing_rebar_population_v1 as P
    want = P.rows_from_block_attributes(cells, "cm", source=f"INSERT {ins.dxf.handle} block FROW")
    assert rows == [want]


@pytest.mark.parametrize("which", ["missing", "broken"])
def test_schedule_rows_unreadable_drawing_raises_never_zero(tmp_path, which):
    f = tmp_path / "absent.dxf" if which == "missing" else _bad_dxf(tmp_path)
    with pytest.raises(OSError, match="schedule_rows_from_drawing"):
        A302.schedule_rows_from_drawing(f, "cm")


@pytest.mark.parametrize("override", [None, 0.1])
def test_section_drawing_read_through_k2(tmp_path, override):
    doc = ezdxf.new("R2010", setup=True)
    doc.header["$DIMLFAC"] = 1.0
    msp = doc.modelspace()
    msp.add_lwpolyline([(0, 0), (2500, 0), (2500, 400), (0, 400)], close=True)
    msp.add_lwpolyline([(0, 1000), (100, 1000), (100, 1100)])                 # 3 vertices: not an outline
    dim = msp.add_linear_dim(base=(0, -300), p1=(0, 0), p2=(2500, 0),
                             override={"dimlfac": override} if override else None)
    dim.render()
    style_lfac = doc.dimstyles.get(dim.dimension.dxf.dimstyle).dxf.get("dimlfac")
    lfac = override or style_lfac or 1.0                             # entity override > style > header
    f = tmp_path / "sec.dxf"
    doc.saveas(f)
    dims, outl = CL3.read_section_drawing(str(f))
    assert len(dims) == 1 and len(outl) == 1
    d = dims[0]
    assert d["axis"] == "x" and abs(d["hi"] - d["lo"] - 2500.0) < 1e-9
    assert abs(d["shown"] - 2500.0 * lfac) < 1e-6
    assert outl[0]["pts"] == [(0.0, 0.0), (2500.0, 0.0), (2500.0, 400.0), (0.0, 400.0)]


@pytest.mark.parametrize("which", ["missing", "broken"])
def test_section_drawing_unreadable_raises_never_zero(tmp_path, which):
    f = tmp_path / "absent.dxf" if which == "missing" else _bad_dxf(tmp_path)
    with pytest.raises(OSError, match="read_section_drawing"):
        CL3.read_section_drawing(str(f))


# ------------------------------------------------------------------------------------------- XCLIP
def _xclip_cases():
    doc = ezdxf.new("R2010")
    blk = doc.blocks.new("B")
    blk.add_line((0, 0), (10, 0))
    msp = doc.modelspace()
    plain = msp.add_blockref("B", (0, 0))
    empty_x = msp.add_blockref("B", (20, 0))
    empty_x.new_extension_dict()
    filt_no_spatial = msp.add_blockref("B", (40, 0))
    filt_no_spatial.new_extension_dict().add_dictionary("ACAD_FILTER")
    filt_not_dict = msp.add_blockref("B", (60, 0))
    filt_not_dict.new_extension_dict().add_xrecord("ACAD_FILTER")
    clipped = msp.add_blockref("B", (80, 0))
    XClip(clipped).set_block_clipping_path([(0, -1), (5, -1), (5, 1), (0, 1)])
    wdflt = msp.add_blockref("B", (100, 0))
    xd = wdflt.new_extension_dict()
    d = doc.objects.add_dictionary_with_default(owner=xd.dictionary.dxf.handle, default=doc.rootdict)
    xd.dictionary["ACAD_FILTER"] = d
    assert d.dxftype() == "ACDBDICTIONARYWDFLT"
    tmp = msp.add_blockref("B", (120, 0))
    XClip(tmp).set_block_clipping_path([(0, -1), (5, -1), (5, 1), (0, 1)])
    sf = tmp.get_extension_dict()["ACAD_FILTER"]["SPATIAL"]
    d["SPATIAL"] = sf
    return doc, {"plain": plain, "empty_xdict": empty_x, "filter_without_spatial": filt_no_spatial,
                 "filter_not_a_dictionary": filt_not_dict, "xclipped": clipped, "dict_with_default": wdflt,
                 "xclipped_2": tmp}


def test_xclip_same_answer_as_ezdxf_on_every_case(tmp_path):
    doc, cases = _xclip_cases()
    got = {k: PEM._xclipped(v) for k, v in cases.items()}
    want = {k: (bool(XClip(v).has_clipping_path) if v.has_extension_dict else False) for k, v in cases.items()}
    assert got == want
    assert got == {"plain": False, "empty_xdict": False, "filter_without_spatial": False,
                   "filter_not_a_dictionary": False, "xclipped": True, "dict_with_default": True, "xclipped_2": True}
    f = tmp_path / "x.dxf"
    doc.saveas(f)
    re = ezdxf.readfile(f)
    ins = sorted(re.modelspace().query("INSERT"), key=lambda e: e.dxf.insert.x)
    assert [PEM._xclipped(e) for e in ins] == [bool(XClip(e).has_clipping_path) if e.has_extension_dict else False
                                               for e in ins]
    assert [PEM._xclipped(e) for e in ins] == [False, False, False, False, True, True, True]


def test_unreadable_filter_is_held_as_clipped():
    class Broken:
        has_extension_dict = True

        def dxftype(self):
            return "INSERT"

        def get_extension_dict(self):
            raise RuntimeError("corrupt extension dictionary")

    assert PEM._xclipped(Broken()) is True                          # HELD, never measured


# ------------------------------------------------------------------------------------------- read_view flatten
def _flatten(e, d):
    return ezpath.make_path(e).flattening(d)


def _curvy_doc(scale):
    doc = ezdxf.new("R2010", setup=True)
    msp = doc.modelspace()
    s = scale
    msp.add_line((0, 0), (10 * s, 0))
    msp.add_lwpolyline([(0, 0, 0, 0, 0.5), (4 * s, 0, 0, 0, 0), (4 * s, 3 * s)], format="xyseb")
    msp.add_polyline2d([(5 * s, 0), (7 * s, 1 * s), (9 * s, 0)])
    msp.add_arc((5 * s, 5 * s), 2 * s, 10, 170)
    blk = doc.blocks.new("WIN")
    blk.add_arc((0, 0), 0.6 * s, 0, 180)
    blk.add_lwpolyline([(0, 0, 0, 0, -0.3), (0.5 * s, 0.2 * s)], format="xyseb")
    inner = doc.blocks.new("OUTER")
    inner.add_blockref("WIN", (0.2 * s, 0.1 * s))
    msp.add_blockref("OUTER", (3 * s, 6 * s), dxfattribs={"xscale": -1.0})                    # mirrored
    msp.add_blockref("OUTER", (7 * s, 6 * s), dxfattribs={"rotation": 33.0})                  # rotated
    return doc


def _old_segments(doc, box, unit_m):
    """the pre-T-465 read_view segment walk with ezdxf.path called directly (reference)."""
    segs = []

    def inb(x, y):
        return box[0] <= x <= box[2] and box[1] <= y <= box[3]

    def take(e, depth=0):
        kind = e.dxftype()
        if kind == "INSERT" and depth < 4:
            for v in e.virtual_entities():
                take(v, depth + 1)
            return
        if kind == "LINE":
            pts = [(e.dxf.start.x, e.dxf.start.y), (e.dxf.end.x, e.dxf.end.y)]
        elif kind in ("LWPOLYLINE", "POLYLINE", "ARC"):
            pts = [(q.x, q.y) for q in ezpath.make_path(e).flattening(0.005 / unit_m)]
        else:
            return
        if all(inb(*q) for q in pts):
            for a, b in zip(pts, pts[1:]):
                if a != b:
                    segs.append((a[0], a[1], b[0], b[1], f"{kind}:{e.dxf.handle}"))

    for e in doc.modelspace():
        if e.dxftype() in ("LINE", "LWPOLYLINE", "POLYLINE", "ARC", "INSERT"):
            take(e)
    return segs


@pytest.mark.parametrize("scale,unit_m", [(1000.0, 0.001), (1.0, 1.0)])
def test_read_view_segments_identical_to_the_pre_t465_call(scale, unit_m):
    doc = _curvy_doc(scale)
    box = (-20 * scale, -20 * scale, 20 * scale, 20 * scale)
    v = OA.read_view(doc, box, unit_m, "EAST", _flatten)
    want = _old_segments(doc, box, unit_m)
    assert len(want) > 40                                           # curves really flattened, not 1 chord each
    assert v["segments"] == want and v["unreadable"] == 0


def test_read_view_curve_without_flatten_raises_also_inside_a_block():
    doc = _curvy_doc(1000.0)
    with pytest.raises(OA.FlattenNotGiven):
        OA.read_view(doc, (-1e9, -1e9, 1e9, 1e9), 0.001, "EAST")
    only_blocks = ezdxf.new("R2010", setup=True)
    b = only_blocks.blocks.new("W")
    b.add_arc((0, 0), 600, 0, 180)
    only_blocks.modelspace().add_line((0, 0), (1000, 0))
    only_blocks.modelspace().add_blockref("W", (0, 0))
    with pytest.raises(OA.FlattenNotGiven):                         # not swallowed as an 'unreadable block'
        OA.read_view(only_blocks, (-1e9, -1e9, 1e9, 1e9), 0.001, "EAST")


def test_read_view_lines_only_needs_no_flatten():
    doc = ezdxf.new("R2010", setup=True)
    doc.modelspace().add_line((0, 0), (1000, 0))
    doc.modelspace().add_line((1000, 0), (1000, 2100))
    v = OA.read_view(doc, (-10, -10, 2000, 3000), 0.001, "EAST")
    assert len(v["segments"]) == 2
    assert not any(math.isnan(c) for s in v["segments"] for c in s[:4])
