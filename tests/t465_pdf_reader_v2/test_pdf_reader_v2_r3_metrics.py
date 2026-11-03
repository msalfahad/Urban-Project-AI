"""T-465 r3 (Checker 2026-11-02T12:04Z, Gate A (e)/(h)): the r2 reader took a simple TrueType font's ascender /
descender from the FontDescriptor but missed two things the V1 (PyMuPDF) reader does, so on a real drawing set the
cross-axis box of every vertical word differed (36 of 36 words, up to 9.27 pt):
  (1) a POSITIVE /Descent is read as below the baseline (-|Descent| / 1000);
  (2) PyMuPDF's quad correction: when ascender - descender < 1 em the glyph box height becomes the font size
      (ascender and descender rescaled in proportion), e.g. ArialMT 728 / -210 -> 0.938 em -> 1 em.
Also pinned here: a FontDescriptor governs whether the program is embedded or not (the program's hhea / OS/2 values
are not used, nor the built-in values of a standard font that carries a descriptor); Ascent <= 0 -> (0.8, -0.2); a
font with NO descriptor gets MuPDF's built-in font by exact /BaseFont name, Times-Roman otherwise.

Oracle: the pre-T-465 V1 reader (PyMuPDF 1.28.2), copied verbatim in test_pdf_reader_v2.py; equality is exact.
Pages are synthetic (built here, hermetic: the TrueType programs are generated with fontTools); not the training villa.
Adverse cases: an embedded TrueType whose descriptor differs from its hhea and OS/2 (normal and positive Descent), a
non-embedded ArialMT, horizontal / 90 / 180 / 270 / 45 degree / mirrored text, horizontal scaling, rise, a tiny
ascender, a missing ascender, a standard font WITH a descriptor, and ZapfDingbats (built-in, below 1 em).
"""
from __future__ import annotations

import io

import pytest

pymupdf = pytest.importorskip("pymupdf")
pytest.importorskip("fontTools")

from engine.source import opening_height_pdf_v2 as P2  # noqa: E402
from tests.t465_pdf_reader_v2.test_pdf_reader_v2 import oracle_page_primitives, same  # noqa: E402

TEXT = (b"BT /F1 20 Tf 100 300 Td (Hello 2.40) Tj ET\n"
        b"BT /F1 12 Tf 0 1 -1 0 300 100 Tm (1:100 SCALE) Tj ET\n"            # 90 degrees
        b"BT /F1 12 Tf 0 -1 1 0 350 400 Tm (STAIR) Tj ET\n"                   # 270 degrees
        b"BT /F1 9 Tf -1 0 0 -1 500 500 Tm (upside) Tj ET\n"                  # 180 degrees
        b"BT /F1 9 Tf -1 0 0 1 560 450 Tm (mirror) Tj ET\n"                   # mirrored: c == -1
        b"BT /F1 10 Tf 0.7071 0.7071 -0.7071 0.7071 150 150 Tm (45d) Tj ET\n"
        b"BT /F1 7 Tf 150 Tz 2 Ts 1 Tc 60 60 Td (175) Tj ET\n"
        b"q 0.5 0 0 2 0 0 cm BT /F1 8 Tf 400 100 Td [(W)-200(1)] TJ ET Q\n")


def ttf(hhea=(1900, -500), typo=(1500, -400), win=(1950, 550), upm=2048):
    """a small TrueType program (glyphs are boxes) with the given hhea / OS/2 vertical metrics."""
    from fontTools.fontBuilder import FontBuilder
    from fontTools.pens.ttGlyphPen import TTGlyphPen
    chars = [chr(c) for c in range(32, 127)]
    names = [".notdef"] + ["g%d" % ord(c) for c in chars]
    fb = FontBuilder(upm, isTTF=True)
    fb.setupGlyphOrder(names)
    fb.setupCharacterMap({ord(c): "g%d" % ord(c) for c in chars})
    glyphs = {}
    for n in names:
        pen = TTGlyphPen(None)
        if n not in (".notdef", "g32"):
            pen.moveTo((100, 0)), pen.lineTo((100, 1400)), pen.lineTo((1000, 1400)), pen.lineTo((1000, 0))
            pen.closePath()
        glyphs[n] = pen.glyph()
    fb.setupGlyf(glyphs)
    fb.setupHorizontalMetrics({n: (1200, 100) for n in names})
    fb.setupHorizontalHeader(ascent=hhea[0], descent=hhea[1])
    fb.setupOS2(sTypoAscender=typo[0], sTypoDescender=typo[1], usWinAscent=win[0], usWinDescent=win[1])
    fb.setupNameTable({"familyName": "T465", "styleName": "Regular"})
    fb.setupPost()
    b = io.BytesIO()
    fb.save(b)
    return b.getvalue()


def _pdf(objs):
    out = b"%PDF-1.4\n"
    offs = []
    for i, o in enumerate(objs, 1):
        offs.append(len(out))
        out += b"%d 0 obj\n" % i + o + b"\nendobj\n"
    x = len(out)
    out += b"xref\n0 %d\n0000000000 65535 f \n" % (len(objs) + 1)
    out += b"".join(b"%010d 00000 n \n" % o for o in offs)
    return out + b"trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (len(objs) + 1, x)


def _stream(d, data):
    return b"<< " + d + b" /Length %d >>\nstream\n" % len(data) + data + b"\nendstream"


def page(path, base, descriptor=None, program=None, subtype=b"TrueType", widths=True, content=TEXT):
    """one 600 x 600 page, font /F1; descriptor = (Ascent, Descent) or None for no FontDescriptor; program = the
    TrueType bytes to embed as /FontFile2, or None."""
    w = b" /FirstChar 32 /LastChar 126 /Widths [" + b" ".join(b"%d" % (500 + 7 * (c % 9)) for c in range(32, 127)) \
        + b"]" if widths else b""
    fd = b""
    if descriptor is not None:
        fd = b" /FontDescriptor 5 0 R"
    objs = [b"<< /Type /Catalog /Pages 2 0 R >>", b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
            b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 600 600] /Resources << /Font << /F1 4 0 R >> >> "
            b"/Contents 6 0 R >>",
            b"<< /Type /Font /Subtype /" + subtype + b" /BaseFont /" + base + w +
            b" /Encoding /WinAnsiEncoding" + fd + b" >>"]
    if descriptor is not None:
        a, d = descriptor
        objs.append(b"<< /Type /FontDescriptor /FontName /" + base + b" /Flags 32 /FontBBox [-200 -300 1200 1000] "
                    b"/ItalicAngle 0 /Ascent %d /Descent %d /CapHeight 700 /StemV 80" % (a, d) +
                    (b" /FontFile2 7 0 R" if program else b"") + b" >>")
    else:
        objs.append(b"<< >>")
    objs.append(_stream(b"", content))
    if program:
        objs.append(_stream(b"/Length1 %d" % len(program), program))
    path.write_bytes(_pdf(objs))
    return path


def spans(path):
    return [(round(s["ascender"], 4), round(s["descender"], 4)) for b in pymupdf.open(str(path))[0]
            .get_text("dict")["blocks"] for ln in b.get("lines", ()) for s in ln["spans"]]


# ------------------------------------------------------------------------------------------- normal cases
def test_embedded_truetype_descriptor_differs_from_hhea_and_os2(tmp_path):
    """(i) embedded TrueType: descriptor 728 / -210 (0.938 em) vs program hhea 1900 / -500 per 2048 (1.172 em)."""
    p = page(tmp_path / "e.pdf", b"ABCDEF+T465", (728, -210), ttf())
    assert set(spans(p)) == {(0.728, -0.21)}                     # MuPDF uses the descriptor, not hhea / OS/2
    got = same(p)
    assert got["reader"]["font_metrics"] == ["DESCRIPTOR"] and len(got["words"]) == 8
    w = next(w for w in got["words"] if w["value"] == "Hello 2.40")
    assert w["y1"] - w["y0"] == pytest.approx(20.0, abs=1e-4)      # corrected: box height = font size, not 18.76


def test_non_embedded_arialmt_with_descriptor_horizontal_and_vertical(tmp_path):
    """(ii) non-embedded TrueType ArialMT, descriptor 728 / -210: the class of the real drawing set's 36 words."""
    got = same(page(tmp_path / "a.pdf", b"ArialMT", (728, -210)))
    v = next(w for w in got["words"] if w["value"] == "1:100 SCALE")
    assert v["dir"] == (0.0, 1.0) and v["x1"] - v["x0"] == pytest.approx(12.0, abs=1e-4)   # cross-axis = size
    assert {w["dir"] for w in got["words"]} >= {(1.0, -0.0), (0.0, 1.0), (0.0, -1.0), (-1.0, -0.0)}


def test_ascent_descent_sum_at_or_above_one_em_is_not_rescaled(tmp_path):
    got = same(page(tmp_path / "n.pdf", b"ABCDEF+T465", (900, -250), ttf()))
    w = next(w for w in got["words"] if w["value"] == "Hello 2.40")
    assert w["y1"] - w["y0"] == pytest.approx(20.0 * 1.15, abs=1e-4)


# ------------------------------------------------------------------------------------------- adverse cases
@pytest.mark.parametrize("asc,dsc", [(760, 240), (728, 210), (0, -250), (0, 0), (-700, -200), (900, 0), (1, -1),
                                     (300, -100), (2000, -900), (500, -499)])
@pytest.mark.parametrize("embedded", [True, False])
def test_descriptor_values_read_as_mupdf_reads_them(tmp_path, asc, dsc, embedded):
    """positive Descent (the real StylusBT case, 760 / 240), missing or negative Ascent, zero Descent, a tiny ascender
    (MuPDF's 'glyphless font' branch), far below and far above 1 em."""
    got = same(page(tmp_path / "d.pdf", b"ABCDEF+T465", (asc, dsc), ttf() if embedded else None))
    want = "DESCRIPTOR" if asc > 0 else "DESCRIPTOR_DEFAULT"
    assert got["reader"]["font_metrics"] == [want]


def test_standard_font_with_a_descriptor_uses_the_descriptor(tmp_path):
    p = page(tmp_path / "h.pdf", b"Helvetica", (728, -210), subtype=b"Type1")
    assert set(spans(p)) == {(0.728, -0.21)}
    assert same(p)["reader"]["font_metrics"] == ["DESCRIPTOR"]


@pytest.mark.parametrize("name", sorted(P2.BUILTIN_NAMES) + ["ABCDEF+Helvetica", "Foo-Bold", "Helvetica-Narrow",
                                                              "Courier-Foo", "ArialNarrow"])
def test_no_descriptor_builtin_font_by_exact_name(tmp_path, name):
    p = page(tmp_path / "b.pdf", name.encode(), None, subtype=b"Type1")
    asc, dsc = P2.BASE14_ASC_DSC[P2.BUILTIN_NAMES.get(name, "Times-Roman")]
    assert set(spans(p)) == {(asc, dsc)}, name
    assert same(p)["reader"]["font_metrics"] == ["BUILTIN"]


def test_zapfdingbats_below_one_em_is_rescaled_like_v1(tmp_path):
    """built-in ZapfDingbats: 0.819 - (-0.144) = 0.963 em < 1: the r2 reader missed the correction here too."""
    got = same(page(tmp_path / "z.pdf", b"ZapfDingbats", None, subtype=b"Type1"))
    w = next(w for w in got["words"] if w["dir"] == (1.0, -0.0) and w["y1"] - w["y0"] > 19)
    assert w["y1"] - w["y0"] == pytest.approx(20.0, abs=1e-4)


def test_unit_change_scale_cm_and_kerning_do_not_break_identity(tmp_path):
    """a page drawn in a scaled user space (2.834646 pt per unit = mm) with the below-1-em descriptor."""
    content = b"q 2.834646 0 0 2.834646 0 0 cm\n" + TEXT.replace(b"cm BT", b"cm\nBT") + b"Q\n"
    got = same(page(tmp_path / "mm.pdf", b"ArialMT", (728, -210), content=content))
    assert got["words"]


def test_the_r2_reader_reproduces_the_checker_fault(tmp_path):
    """the fault is real: without (1) and (2) the boxes differ (guards against a vacuous oracle)."""
    p = page(tmp_path / "f.pdf", b"StylusBT", (760, 240), ttf())
    want = oracle_page_primitives(p)
    v = next(w for w in want["words"] if w["value"] == "1:100 SCALE")
    # r2: (asc, dsc) = (0.76, +0.24): the box spanned 0.76 - 0.24 = 0.52 em across the line; V1 spans 1.00 em
    assert v["x1"] - v["x0"] == pytest.approx(12.0, abs=1e-4)
    assert P2.page_primitives(p)["words"] == want["words"]


def test_random_rotation_mirror_size_and_metrics_read_identically(tmp_path):
    """30 seeded pages x 6 runs: any angle, mirrored or not, four sizes, descriptor values around 1 em, embedded or
    not. Found during r3: the r2 'dir' was normalised in double precision (differs in the 6th decimal from V1 at
    arbitrary angles); r3 normalises in single precision as MuPDF does."""
    import math
    import random
    rnd = random.Random(465)
    for k in range(30):
        runs = []
        for _ in range(6):
            a, s, sx = rnd.uniform(0, 2 * math.pi), rnd.choice([3, 7.5, 11, 23.3]), rnd.choice([1, 1, -1])
            c, si = math.cos(a), math.sin(a)
            runs.append(b"BT /F1 %.3f Tf %.5f %.5f %.5f %.5f %.2f %.2f Tm (%d.%02d x) Tj ET" % (
                s, c * sx, si * sx, -si, c, rnd.uniform(100, 500), rnd.uniform(100, 500), rnd.randint(0, 99),
                rnd.randint(0, 99)))
        desc = (rnd.choice([728, 760, 500, 900, 300, 1000]), rnd.choice([-210, 240, -100, -50, 0, -300]))
        p = page(tmp_path / ("r%d.pdf" % k), b"ArialMT", desc, ttf() if k % 2 else None, content=b"\n".join(runs))
        assert len(same(p)["words"]) == 6, k
