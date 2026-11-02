"""T-465 r2 (owner directive 2026-11-02, D4; T-210 (b)): OPENING_HEIGHT_PDF_V2 reads a PDF page with pypdf (BSD-3-Clause,
B-5 registered) instead of PyMuPDF (AGPL), and gives the SAME words and segments as the former reader.

Reference: the pre-T-465 V1 page_primitives (PyMuPDF), copied verbatim below as a TEST ORACLE (tests are outside the
engine dependency register; the engine never imports PyMuPDF). Equality is exact: the same values, the same floats, the
same ids, in the same order -- not "close".

Pages (all synthetic, built here in a temporary folder; not the training villa):
- the three T-082 sheets (south 1:100, north in mm, section) and the T-082 hand result through measure_pdf;
- an adverse page: closepath, a 're' rectangle, a closed run of four lines (quad), 'v' / 'y' curves, a degenerate
  curve and zero-length lines, an 'n' path and a clip path (not drawn), fill only, fill + stroke ('B', 'b': listed
  once), a rotated + scaled cm, q / Q, a Form XObject with /Matrix drawn twice, TJ kerning, Tc / Tz / Ts carried
  across BT blocks and into the form, text rotated 90 and 45 degrees, text outside the page, a second standard font;
  read with /Rotate 0 / 90 / 180 / 270, with an offset CropBox and both;
- composite fonts: a UTF-16 CMap font without ToUnicode, an embedded Identity-H font with ToUnicode;
- a scanned page (image only: RASTER_ONLY) and an empty page (EMPTY);
- missing file / page out of range raise (never an empty page).
"""
from __future__ import annotations

import ast
from pathlib import Path

import pytest

pymupdf = pytest.importorskip("pymupdf")

from engine.source import opening_height_pdf as P1  # noqa: E402
from engine.source import opening_height_pdf_v2 as P2  # noqa: E402
from tests.t082_opening_height_pdf import test_opening_height_pdf as T82  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]


# ------------------------------------------------------------------------------------------- the oracle
def oracle_page_primitives(path, page_no=1):
    """VERBATIM the pre-T-465 engine/source/opening_height_pdf.py page_primitives (merge 2dee9544 .. 8239c309)."""
    doc = pymupdf.open(str(path))
    pg = doc[page_no - 1]
    H = pg.rect.height
    words = []
    for blk in pg.get_text("dict").get("blocks", ()):
        for line in blk.get("lines", ()):
            d = line.get("dir", (1.0, 0.0))
            for sp in line.get("spans", ()):
                t = (sp.get("text") or "").strip()
                if not t:
                    continue
                x0, y0, x1, y1 = sp["bbox"]
                words.append({"value": t, "x0": x0, "y0": H - y1, "x1": x1, "y1": H - y0,
                              "dir": (round(d[0], 6), round(-d[1], 6))})
    segs = []
    n = 0
    for dr in pg.get_drawings():
        for it in dr.get("items", ()):
            n += 1
            if it[0] == "l":
                pts = [it[1], it[2]]
            elif it[0] == "re":
                r = it[1]
                pts = [r.tl, r.tr, r.br, r.bl, r.tl]
            elif it[0] == "qu":
                q = it[1]
                pts = [q.ul, q.ur, q.lr, q.ll, q.ul]
            elif it[0] == "c":
                p0, c1, c2, p3 = it[1], it[2], it[3], it[4]
                pts = []
                for k in range(9):
                    t = k / 8.0
                    a, b, c, e = (1 - t) ** 3, 3 * (1 - t) ** 2 * t, 3 * (1 - t) * t * t, t ** 3
                    pts.append(pymupdf.Point(a * p0.x + b * c1.x + c * c2.x + e * p3.x,
                                             a * p0.y + b * c1.y + c * c2.y + e * p3.y))
            else:
                continue
            for i, (p, q) in enumerate(zip(pts, pts[1:])):
                if (p.x, p.y) != (q.x, q.y):
                    segs.append((p.x, H - p.y, q.x, H - q.y, f"pdf{n}.{i}"))
    has_img = bool(pg.get_images())
    state = "VECTOR" if (words or segs) else ("RASTER_ONLY" if has_img else "EMPTY")
    return {"page": page_no, "width_pt": pg.rect.width, "height_pt": H, "state": state, "words": words,
            "segments": segs, "has_image": has_img}


def same(path, page_no=1):
    want, got = oracle_page_primitives(path, page_no), P2.page_primitives(path, page_no)
    assert {k: got[k] for k in want} == want                    # every V1 field equal, float for float, id for id
    assert got["reader"]["library"] == "pypdf" and got["reader"]["policy"] == "OPENING_HEIGHT_PDF_V2"
    return got


# ------------------------------------------------------------------------------------------- pages
ADVERSE = b"""q 1 w 10 10 m 50 10 l 50 40 l h S
20 60 30 20 re S
100 10 m 140 10 l 140 40 l 100 40 l 100 10 l S
150 10 m 170 30 190 30 v S 150 50 m 170 70 190 50 y S
5 5 m 6 6 l n
0 0 100 100 re W n 200 100 m 250 150 l S
1 0 0 rg 210 10 30 30 re f
0 0 1 rg 20 100 40 20 re B
20 140 m 60 140 l 60 160 l 20 160 l h b
0.8 0.6 -0.6 0.8 120 120 cm 0 0 30 20 re S 0 0 m 10 0 l 10 10 l 0 10 l 0 0 l S Q
q 2 0 0 2 0 0 cm 120 60 m 130 70 l S 70 70 m 70 70 l S 75 75 m 76 76 l 76 76 l S Q
q 10 300 m 10 300 10 300 10 300 c 20 310 l S 30 300 m 30 300 40 310 40 310 c S Q
BT /F1 9 Tf 30 200 Td (1:100) Tj ( SCALE) Tj [(2)-120(40)] TJ ET
BT /F1 7 Tf 150 Tz 2 Ts 1 Tc 30 220 Td (175) Tj 0 -12 Td (36 0) Tj ET
BT /F1 8 Tf 0 1 -1 0 250 200 Tm (210) Tj ET
BT /F1 8 Tf 0.7071 0.7071 -0.7071 0.7071 250 250 Tm (45d) Tj ET
BT /F1 8 Tf -50 -50 Td (out) Tj 2000 2000 Td (far) Tj ET
q 1 0 0 1 300 100 cm /X1 Do Q
q 0.5 0 0 0.5 400 100 cm /X1 Do Q
BT /F2 10 Tf 40 380 Td (90) Tj ET
"""
FORM = b"0 0 m 40 0 l 40 30 l S 0 0 20 10 re S BT /F1 6 Tf 5 15 Td (125) Tj ET"


def adverse_pdf(path, rotate=0, crop=None):
    d = pymupdf.open()
    p = d.new_page(width=600, height=420)
    f1 = d.get_new_xref()
    d.update_object(f1, "<</Type/Font/Subtype/Type1/BaseFont/Helvetica/Encoding/WinAnsiEncoding>>")
    f2 = d.get_new_xref()
    d.update_object(f2, "<</Type/Font/Subtype/Type1/BaseFont/Times-Bold>>")
    fx = d.get_new_xref()
    d.update_object(fx, "<</Type/XObject/Subtype/Form/BBox[0 0 60 40]/Matrix[1 0 0 1 5 5]"
                        "/Resources<</Font<</F1 %d 0 R>>>>>>" % f1)
    d.update_stream(fx, FORM)
    c = d.get_new_xref()
    d.update_object(c, "<<>>")
    d.update_stream(c, ADVERSE)
    d.xref_set_key(p.xref, "Contents", f"{c} 0 R")
    d.xref_set_key(p.xref, "Resources", "<</Font<</F1 %d 0 R/F2 %d 0 R>>/XObject<</X1 %d 0 R>>>>" % (f1, f2, fx))
    if rotate:
        d.xref_set_key(p.xref, "Rotate", str(rotate))
    if crop:
        d.xref_set_key(p.xref, "CropBox", "[%g %g %g %g]" % crop)
    d.save(str(path))
    return path


# ------------------------------------------------------------------------------------------- normal cases
@pytest.mark.parametrize("name", ["south", "north", "sect"])
def test_t082_sheets_read_identically(tmp_path, name):
    sheet = {"south": T82.south_sheet, "north": T82.north_sheet_mm, "sect": T82.section_sheet}[name]()
    sheet.pdf(tmp_path / f"{name}.pdf")
    got = same(tmp_path / f"{name}.pdf")
    assert got["state"] == "VECTOR" and got["segments"] and got["words"]


def test_t082_hand_result_through_v2_equals_the_oracle_reading(tmp_path):
    files = {}
    for name, sheet in (("south", T82.south_sheet()), ("north", T82.north_sheet_mm()), ("sect", T82.section_sheet())):
        files[name] = tmp_path / f"{name}.pdf"
        sheet.pdf(files[name])

    def result(read):
        pr = {k: read(f, 1) for k, f in files.items()}
        elev = [P1.view_from_page(pr["south"], T82.BOX, "SOUTH"), P1.view_from_page(pr["north"], T82.BOX, "NORTH")]
        sec = [P1.view_from_page(pr["sect"], T82.BOX, "A-A", kind="SECTION")]
        return P1.measure_pdf(T82.plan(), floors=T82.FLOORS, elevation_views=elev, section_views=sec)
    got = result(P2.page_primitives)
    assert got == result(oracle_page_primitives)
    T82._check_hand(got)
    r = T82.by_id(got)
    assert r["W4"]["area_m2"] == pytest.approx(0.960, abs=1e-3) and r["W5"]["area_m2"] == pytest.approx(0.600, abs=1e-3)


def test_v1_page_primitives_is_the_v2_reader(tmp_path):
    T82.south_sheet().pdf(tmp_path / "s.pdf")
    assert P1.page_primitives(tmp_path / "s.pdf", 1) == P2.page_primitives(tmp_path / "s.pdf", 1)
    assert P2.view_from_page is P1.view_from_page and P2.measure_pdf is P1.measure_pdf


# ------------------------------------------------------------------------------------------- adverse cases
@pytest.mark.parametrize("rotate,crop", [(0, None), (90, None), (180, None), (270, None), (0, (15, 25, 520, 400)),
                                         (90, (15, 25, 520, 400))])
def test_adverse_page_reads_identically(tmp_path, rotate, crop):
    got = same(adverse_pdf(tmp_path / "a.pdf", rotate, crop))
    values = [w["value"] for w in got["words"]]
    assert "1:100 SCALE240" in values                     # kerned TJ pieces joined as one printed run
    assert "1 7 5" in values and "1 2 5" in values         # Tc carried across BT and into the form: spaced glyphs
    assert "out" not in values and "far" not in values    # glyphs wholly outside the page are not read
    assert len(got["segments"]) == 64
    assert {w["dir"] for w in got["words"]} >= {(1.0, -0.0), (0.0, 1.0)}


def test_rotated_page_keeps_the_v1_quirk_f_t465_2(tmp_path):
    """F-T465-2 (reproduced, not corrected): on /Rotate 90 the reader's coordinates stay in the unrotated page space
    while height_pt is the rotated page's, so every y is shifted by width - height against /Rotate 0."""
    a = same(adverse_pdf(tmp_path / "r0.pdf", 0))
    b = same(adverse_pdf(tmp_path / "r90.pdf", 90))
    assert (a["width_pt"], a["height_pt"]) == (600.0, 420.0) and (b["width_pt"], b["height_pt"]) == (420.0, 600.0)
    s0, s90 = a["segments"][0], b["segments"][0]
    assert s0[0] == s90[0] and s90[1] - s0[1] == pytest.approx(600.0 - 420.0)


def test_composite_fonts_read_identically(tmp_path):
    d = pymupdf.open()
    p = d.new_page(width=500, height=300)
    p.insert_text((50, 100), "2.40 1:50", fontname="china-s", fontsize=11)        # UTF-16 CMap, no ToUnicode
    p.insert_text((50, 150), "315", fontname="tiro", fontsize=10, rotate=90)
    p.insert_font(fontname="F0", fontbuffer=pymupdf.Font("cour").buffer)          # embedded, Identity-H + ToUnicode
    p.insert_text((200, 150), "1/100 270", fontname="F0", fontsize=9)
    d.save(str(tmp_path / "cid.pdf"))
    got = same(tmp_path / "cid.pdf")
    assert [w["value"] for w in got["words"]] == ["2.40 1:50", "315", "1/100 270"]


def test_scanned_page_is_raster_only_and_empty_page_is_empty(tmp_path):
    from PIL import Image
    Image.new("L", (200, 140), 255).save(tmp_path / "scan.png")
    d = pymupdf.open()
    pg = d.new_page(width=842, height=595)
    pg.insert_image(pg.rect, filename=str(tmp_path / "scan.png"))
    d.new_page(width=842, height=595)
    d.save(str(tmp_path / "scan.pdf"))
    a = same(tmp_path / "scan.pdf", 1)
    assert a["state"] == "RASTER_ONLY" and a["words"] == [] and a["segments"] == [] and a["has_image"]
    b = same(tmp_path / "scan.pdf", 2)
    assert b["state"] == "EMPTY" and not b["has_image"]


def test_missing_file_and_page_out_of_range_raise(tmp_path):
    with pytest.raises(Exception):
        P2.page_primitives(tmp_path / "absent.pdf", 1)
    T82.south_sheet().pdf(tmp_path / "s.pdf")
    with pytest.raises(IndexError):
        P2.page_primitives(tmp_path / "s.pdf", 2)


def test_base14_metrics_are_the_oracle_s(tmp_path):
    """the pinned ascender / descender of the 14 standard fonts are MuPDF's (what the V1 reader used)."""
    for name, (asc, dsc) in P2.BASE14_ASC_DSC.items():
        d = pymupdf.open()
        p = d.new_page()
        x = d.get_new_xref()
        d.update_object(x, "<</Type/Font/Subtype/Type1/BaseFont/%s>>" % name)
        c = d.get_new_xref()
        d.update_object(c, "<<>>")
        d.update_stream(c, b"BT /F1 10 Tf 10 10 Td (12) Tj ET")
        d.xref_set_key(p.xref, "Contents", "%d 0 R" % c)
        d.xref_set_key(p.xref, "Resources", "<</Font<</F1 %d 0 R>>>>" % x)
        sp = pymupdf.open("pdf", d.tobytes())[0].get_text("dict")["blocks"][0]["lines"][0]["spans"][0]
        assert (round(sp["ascender"], 3), round(sp["descender"], 3)) == (asc, dsc), name


# ------------------------------------------------------------------------------------------- boundary
def _imports(p):
    out = set()
    for n in ast.walk(ast.parse(p.read_text(encoding="utf-8"))):
        if isinstance(n, ast.Import):
            out |= {a.name for a in n.names}
        elif isinstance(n, ast.ImportFrom) and n.module and not n.level:
            out.add(n.module)
    return out


def test_no_engine_source_module_imports_pymupdf_and_v2_imports_only_pypdf():
    bad = [str(p.relative_to(ROOT)) for p in sorted((ROOT / "engine" / "source").rglob("*.py"))
           if any(n.split(".")[0] in ("pymupdf", "fitz") for n in _imports(p))]
    assert bad == []
    third = {n.split(".")[0] for n in _imports(ROOT / "engine/source/opening_height_pdf_v2.py")} - set(
        __import__("sys").stdlib_module_names) - {"engine", "__future__"}
    assert third == {"pypdf"}
