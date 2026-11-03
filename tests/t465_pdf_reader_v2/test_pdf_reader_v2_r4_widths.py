"""T-465 r4 (Checker 2026-11-02T19:57Z, Gate A (e)/(h)): the r3 reader summed a simple font's /Widths as given, while
MuPDF stores every glyph width as an INTEGER (pdf_to_int: single precision, floorf(f + 0.5f)), so on an embedded font
with fractional widths (the Checker's DejaVu subset) 3 of 15 words differed by up to 0.0073 pt.

r4 reads the widths as MuPDF does and pins it here, every value taken from the oracle (PyMuPDF 1.28.2), not assumed:
  - /Widths, /W (both forms), /DW, /FirstChar, /LastChar: pdf_to_int (500.5 -> 501, 499.5 -> 500, -0.5 -> 0,
    -2.5 -> -2, 333.50001 -> 334); only codes FirstChar .. LastChar take the array (missing LastChar,
    LastChar > 255 or FirstChar > LastChar -> FirstChar = LastChar = 0); other codes take the MissingWidth;
  - /MissingWidth: truncated toward zero (433.7 -> 433, -433.7 -> -433, 0.9 -> 0);
and two text-grouping rules found while testing zero / negative advances:
  - a backward pen motion of less than 0.8 em on the same line continues the span (no space);
  - a text LINE whose box is empty (every glyph advance zero) is dropped; a zero-advance span inside a line with
    extent stays.
Oracle: the pre-T-465 V1 reader (PyMuPDF), copied verbatim in test_pdf_reader_v2.py; equality is exact.
Pages are synthetic and hermetic (built here; TrueType programs from fontTools); not the training villa.
"""
from __future__ import annotations

import math
import random

import pytest

pymupdf = pytest.importorskip("pymupdf")
pytest.importorskip("fontTools")

from engine.source import opening_height_pdf_v2 as P2  # noqa: E402
from tests.t465_pdf_reader_v2.test_pdf_reader_v2 import oracle_page_primitives, same  # noqa: E402
from tests.t465_pdf_reader_v2.test_pdf_reader_v2_r3_metrics import _pdf, _stream, ttf  # noqa: E402

DESC = (b"<< /Type /FontDescriptor /FontName /ABCDEF+T465 /Flags 32 /FontBBox [0 -200 1000 900] /ItalicAngle 0 "
        b"/Ascent 800 /Descent -200 /CapHeight 700 /StemV 80%s%s >>")
TOU = (b"/CIDInit /ProcSet findresource begin 12 dict begin begincmap /CMapName /U def 1 begincodespacerange <0000> "
       b"<FFFF> endcodespacerange 1 beginbfrange <0020> <007E> <0020> endbfrange endcmap CMapName currentdict /CMap "
       b"defineresource pop end end")
WORDS = b"BT /F1 20 Tf 10 20 Td (Room 3.20 x 4.15 H=2.75) Tj ET\n" \
        b"BT /F1 12 Tf 0 1 -1 0 300 100 Tm (Sec A-A 1:50 DVS) Tj ET\n" \
        b"BT /F1 12 Tf 0 -1 1 0 350 500 Tm (ang 0) Tj ET\n" \
        b"BT /F1 9 Tf -1 0 0 -1 550 560 Tm (upside 1.80) Tj ET\n"


def simple(path, widths, first=b"32", last=b"126", missing=None, content=WORDS, program=None):
    """one 600 x 600 page, simple TrueType /F1 with the given /Widths (bytes, as written), FirstChar / LastChar
    (None = key absent) and MissingWidth; program = TrueType bytes to embed, or None."""
    fl = (b" /FirstChar " + first if first is not None else b"") + (b" /LastChar " + last if last is not None else b"")
    objs = [b"<< /Type /Catalog /Pages 2 0 R >>", b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
            b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 600 600] /Resources << /Font << /F1 4 0 R >> >> "
            b"/Contents 6 0 R >>",
            b"<< /Type /Font /Subtype /TrueType /BaseFont /ABCDEF+T465" + fl + b" /Widths [" + b" ".join(widths) +
            b"] /Encoding /WinAnsiEncoding /FontDescriptor 5 0 R >>",
            DESC % (b" /MissingWidth " + missing if missing else b"", b" /FontFile2 7 0 R" if program else b""),
            _stream(b"", content)]
    if program:
        objs.append(_stream(b"/Length1 %d" % len(program), program))
    path.write_bytes(_pdf(objs))
    return path


def composite(path, w, dw=None, content=None):
    """a Type0 / Identity-H font with /W (bytes) and /DW (None = key absent), ToUnicode for ASCII."""
    objs = [b"<< /Type /Catalog /Pages 2 0 R >>", b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
            b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 600 600] /Resources << /Font << /F1 4 0 R >> >> "
            b"/Contents 6 0 R >>",
            b"<< /Type /Font /Subtype /Type0 /BaseFont /ArialMT /Encoding /Identity-H /DescendantFonts [5 0 R] "
            b"/ToUnicode 7 0 R >>",
            b"<< /Type /Font /Subtype /CIDFontType2 /BaseFont /ArialMT /CIDSystemInfo << /Registry (Adobe) "
            b"/Ordering (Identity) /Supplement 0 >> /FontDescriptor 8 0 R" + (b" /DW " + dw if dw else b"") +
            b" /W [" + w + b"] /CIDToGIDMap /Identity >>",
            _stream(b"", content), _stream(b"", TOU), DESC % (b"", b"")]
    path.write_bytes(_pdf(objs))
    return path


def hx(s):
    return b"<" + s.encode("utf-16-be").hex().encode() + b">"


def advances(path):
    """the oracle's per-glyph pen advance, in 1/1000 em at 100 pt (each glyph on its own text line)."""
    out = {}
    for b in pymupdf.open(str(path))[0].get_text("rawdict")["blocks"]:
        for ln in b.get("lines", ()):
            for s in ln["spans"]:
                ch = s["chars"]
                if len(ch) > 1:
                    out[ch[0]["c"]] = round((ch[1]["origin"][0] - ch[0]["origin"][0]) * 10, 3)
    return out


FRACTIONAL = [b"500.5", b"500.4999", b"499.5", b"0.5", b"-0.5", b"-1.5", b"-2.5", b"0", b"-300.7", b"831.0547",
              b"666.992", b"1000.5", b"0.49", b"333.50001", b"2.5", b"-0.4999"]
ROUNDED = [501, 500, 500, 1, 0, -1, -2, 0, -301, 831, 667, 1001, 0, 334, 3, 0]


# ------------------------------------------------------------------------------------------- the rounding itself
def test_mupdf_stores_widths_as_integers_rounded_half_up_the_oracle_s_values(tmp_path):
    """each fractional width as the oracle advances it (one glyph + a 1000 glyph per line, 100 pt): x.5 goes up,
    -x.5 toward zero, single precision first (333.50001 -> 333.5 -> 334)."""
    content = b"".join(b"BT /F1 100 Tf 10 %d Td (%cZ) Tj ET\n" % (20 + 30 * i, 65 + i) for i in range(16))
    p = simple(tmp_path / "r.pdf", FRACTIONAL + [b"1000"] * 10, first=b"65", last=b"90", content=content)
    adv = advances(p)
    assert adv == {chr(65 + i): float(ROUNDED[i]) for i in range(16)}
    assert [P2._pdf_int(float(v)) for v in FRACTIONAL] == ROUNDED
    same(p)


@pytest.mark.parametrize("v,want", [(7, 7), (-7, -7), (0.5, 1), (-0.5, 0), (1.5, 2), (-1.5, -1), (2.4999, 2),
                                    (float("nan"), 0), (float("inf"), 0), ("x", 0), (None, 0), (True, 0)])
def test_pdf_int_unit(v, want):
    assert P2._pdf_int(v) == want


# ------------------------------------------------------------------------------------------- simple fonts
@pytest.mark.parametrize("embedded", [False, True])
def test_fractional_widths_horizontal_vertical_and_upside_down(tmp_path, embedded):
    """the Checker's class: every width fractional (as a DejaVu subset writes them), 0, 90, -90 and 180 degrees."""
    w = [b"%.4f" % (300 + (c * 37.0547) % 700) for c in range(32, 127)]
    got = same(simple(tmp_path / "f.pdf", w, program=ttf() if embedded else None))
    assert len(got["words"]) == 4
    assert {w_["dir"] for w_ in got["words"]} == {(1.0, -0.0), (0.0, 1.0), (0.0, -1.0), (-1.0, -0.0)}


def test_the_r3_sum_as_given_differs_from_the_oracle(tmp_path):
    """non-vacuous: summing the fractional widths unrounded gives another word end than the oracle."""
    w = [b"%.4f" % (300 + (c * 37.0547) % 700) for c in range(32, 127)]
    p = simple(tmp_path / "v.pdf", w)
    want = next(x for x in oracle_page_primitives(p)["words"] if x["value"].startswith("Room"))
    raw = sum(300 + (ord(ch) * 37.0547) % 700 for ch in "Room 3.20 x 4.15 H=2.75") * 0.02
    ints = sum(math.floor(300 + (ord(ch) * 37.0547) % 700 + 0.5) for ch in "Room 3.20 x 4.15 H=2.75") * 0.02
    assert abs(want["x1"] - 10 - ints) < 1e-3 < abs(want["x1"] - 10 - raw)


def test_half_zero_and_negative_widths(tmp_path):
    same(simple(tmp_path / "h.pdf", [b"0", b"-0.5", b"0.5", b"-250.5"] * 24))


@pytest.mark.parametrize("first,last,missing", [
    (b"32", b"60", b"433.5"),        # array longer than LastChar: codes above take MissingWidth (truncated: 433)
    (b"32", b"60", b"433.7"), (b"32", b"60", b"-433.7"), (b"32", b"60", b"0.9"),
    (b"32.6", b"126", None),         # FirstChar read as an integer, rounded: 33
    (b"32", None, b"300"),           # no LastChar -> FirstChar = LastChar = 0
    (b"32", b"256", b"300"), (b"-1", b"126", b"300"), (b"100", b"40", b"300"),
    (b"32", b"200", None),           # array shorter than LastChar - FirstChar + 1: missing entries are 0
])
def test_first_last_char_and_missing_width(tmp_path, first, last, missing):
    w = [b"%.3f" % (400 + (c * 13.25) % 500) for c in range(32, 127)]
    same(simple(tmp_path / "m.pdf", w, first=first, last=last, missing=missing))


# ------------------------------------------------------------------------------------------- composite fonts
@pytest.mark.parametrize("w,dw", [
    (b"65 [500.5 499.5 0.5 -0.5 -2.5] 48 57 556.7 32 [277.5]", b"1000.5"),
    (b"46 [348.145]", b"666.992"),
    (b"65 70 0 120 [0 -300.7 831.0547]", None),
    (b"32.6 126 600.5", b"0.5"),
])
def test_composite_w_and_dw_read_as_integers(tmp_path, w, dw):
    content = b"".join(b"BT /F1 20 Tf 10 %d Td %s Tj ET\n" % (20 + 25 * i, hx(t))
                       for i, t in enumerate(["ABC 12", "Room 3.20", "xyz", "AB.5", "neg -1"]))
    content += b"BT /F1 12 Tf 0 1 -1 0 300 100 Tm " + hx("Sec A-A 1:50") + b" Tj ET\n"
    assert same(composite(tmp_path / "c.pdf", w, dw, content))["words"]


# ------------------------------------------------------------------------------------------- zero / negative advance
ZW = [b"0" if c in (65, 66, 67, 71) else (b"500" if c in (68, 69, 70) else b"600") for c in range(32, 127)]


@pytest.mark.parametrize("content,n", [
    (b"BT /F1 20 Tf 10 20 Td (ABC) Tj ET\n", 0),                                   # zero-advance line: dropped
    (b"BT /F1 20 Tf 0 1 -1 0 300 100 Tm (ABC) Tj ET\n", 0),                        # the same, vertical
    (b"BT /F1 20 Tf 10 20 Td (G) Tj ET\nBT /F1 20 Tf 10 200 Td (DEF) Tj ET\n", 1),
    (b"BT /F1 20 Tf 10 20 Td (ABC) Tj (DEF) Tj ET\n", 1),
    (b"BT /F1 20 Tf 10 20 Td (DEF) Tj 1 0 0 rg (ABC) Tj 0 0 1 rg (DE) Tj ET\n", 3),  # zero span in a line: kept
    (b"BT /F1 20 Tf 0 -1 1 0 300 500 Tm (DEF) Tj 1 0 0 rg (ABC) Tj ET\n", 1),         # zero span LAST: dropped
    (b"BT /F1 20 Tf 10 20 Td (A B) Tj ET\n", 1),
])
def test_zero_advance_lines_and_spans(tmp_path, content, n):
    assert len(same(simple(tmp_path / "z.pdf", ZW, content=content))["words"]) == n


@pytest.mark.parametrize("em,spans", [(-0.1, 1), (-0.3, 1), (-0.5, 1), (-0.79, 1), (-0.81, 4), (-1.2, 3), (0.1, 1),
                                      (0.2, 1), (0.29, 1), (0.31, 4), (0.5, 4), (0.79, 4), (0.9, 4)])
@pytest.mark.parametrize("vertical", [False, True])
def test_backward_and_forward_pen_motion(tmp_path, em, spans, vertical):
    """Tc moves the pen: back by less than 0.8 em continues the span (MuPDF); forward 0.15 .. 0.3 em adds a space in
    the span; above 0.3 em the synthesized space is LARGE, a span of its own, so V1 lists the glyphs as separate words;
    0.8 em or more either way starts a new line."""
    tm = b"0 1 -1 0 300 30 Tm" if vertical else b"30 20 Td"
    content = b"BT /F1 20 Tf %.4f Tc %s (DEFG) Tj ET\n" % (20 * em, tm)
    got = same(simple(tmp_path / "t.pdf", [b"500"] * 95, content=content))
    assert len(got["words"]) == spans


# ------------------------------------------------------------------------------------------- seeded corpus
def test_seeded_corpus_fractional_widths_any_angle_spacing_and_scaling(tmp_path):
    """24 pages x 8 runs: fractional, half, zero and negative widths, any angle, Tc / Tw / Tz, embedded or not."""
    rnd = random.Random(4654)
    for k in range(24):
        w = [rnd.choice([b"%.4f" % rnd.uniform(200, 1100), b"%d.5" % rnd.randint(-3, 900), b"0", b"-%.2f" %
                         rnd.uniform(0, 300), b"%d" % rnd.randint(250, 900)]) for _ in range(95)]
        runs = []
        for _ in range(8):
            a, s = rnd.choice([0, 0, math.pi / 2, -math.pi / 2, math.pi, rnd.uniform(0, 2 * math.pi)]), \
                rnd.choice([5, 7.5, 10, 13.3, 20])
            c, si = math.cos(a), math.sin(a)
            runs.append(b"BT /F1 %.2f Tf %.2f Tc %.2f Tw %d Tz %.5f %.5f %.5f %.5f %.2f %.2f Tm (%s) Tj ET" % (
                s, rnd.choice([0, 0, 0.5, -0.7, -2]), rnd.choice([0, 0, 1.5]), rnd.choice([100, 100, 80, 130]),
                c, si, -si, c, rnd.uniform(80, 520), rnd.uniform(80, 520),
                rnd.choice([b"Room 3.20 x 4.15", b"WC 1.80x2.10", b"D1 0.90/2.10", b"+3.45 FFL", b"Sec A-A"])))
        p = simple(tmp_path / ("s%d.pdf" % k), w, program=ttf() if k % 2 else None, content=b"\n".join(runs))
        same_inside(p)


def _inside(w, W=600.0, H=600.0, m=26.0):
    """the word stays more than the largest glyph (20 pt at 130 % scaling) inside the page"""
    return m <= w["x0"] and w["x1"] <= W - m and m <= w["y0"] and w["y1"] <= H - m


def same_inside(p):
    """identity, except the NAMED page-edge difference: on a page the reader flags GLYPH_ACROSS_PAGE_EDGE, the words
    that come within one glyph of the page edge are excluded (from both readers) and every other word must be equal."""
    got = P2.page_primitives(p)
    if "GLYPH_ACROSS_PAGE_EDGE" not in got["reader"]["limits"]:
        return same(p)
    want = oracle_page_primitives(p)
    assert want["segments"] == got["segments"]
    assert [w for w in want["words"] if _inside(w)] == [w for w in got["words"] if _inside(w)]
    return got


def test_named_difference_glyph_across_the_page_edge(tmp_path):
    """NAMED DIFFERENCE GLYPH_ACROSS_PAGE_EDGE (bound: only glyphs whose box crosses the page edge): MuPDF keeps a
    glyph unless its OUTLINE lies wholly outside the page; this reader tests the advance x ascender..descender box.
    Here the last glyph '0' of a downward line hangs below the page: its box reaches 4 pt inside the page, the
    embedded program's outline (glyphs drawn 0 .. 1400 units of 2048 above the baseline, rotated) does not.
    The page is flagged, the other words are identical."""
    content = (b"BT /F1 20 Tf 0 -1 1 0 300 60 Tm (WC 1.80x2.10) Tj ET\n"
               b"BT /F1 12 Tf 100 300 Td (Room 3.20) Tj ET\n")
    p = simple(tmp_path / "e.pdf", [b"500"] * 95, program=ttf(), content=content)
    got = P2.page_primitives(p)
    assert "GLYPH_ACROSS_PAGE_EDGE" in got["reader"]["limits"]
    same_inside(p)
    inner = simple(tmp_path / "i.pdf", [b"500"] * 95, program=ttf(), content=content.replace(b"300 60 Tm", b"300 560 Tm"))
    assert "GLYPH_ACROSS_PAGE_EDGE" not in P2.page_primitives(inner)["reader"]["limits"]
    same(inner)


# ------------------------------------------------------------------------------------------- span rules found in r4
@pytest.mark.parametrize("glyph,dx,dy", [(g, dx, dy) for g in (b"D", b"E") for dx in (0, 0.05, 0.099, 0.101, 0.3)
                                         for dy in (0, 0.05, 0.1)])
def test_fake_bold_same_glyph_within_a_tenth_em_is_dropped(tmp_path, glyph, dx, dy):
    """MuPDF drops the same character printed again within 0.1 em (fake bold); another character is kept."""
    content = b"BT /F1 20 Tf 100 300 Td (D) Tj %.4f %.4f Td (%s) Tj ET\n" % (20 * dx, 20 * dy, glyph)
    got = same(simple(tmp_path / "b.pdf", [b"500"] * 95, content=content))
    dropped = glyph == b"D" and math.hypot(dx, dy) < 0.1
    assert "".join(w["value"] for w in got["words"]) == ("D" if dropped else "D" + glyph.decode())


@pytest.mark.parametrize("rise", [-0.3, -0.1, 0.05, 0.1, 0.11, 0.3, 0.7])
@pytest.mark.parametrize("vertical", [False, True])
def test_superscript_splits_the_span_only_on_a_horizontal_line(tmp_path, rise, vertical):
    """PyMuPDF flags a glyph more than 0.1 x size above the line's first glyph as superscript, only on a line whose
    direction is exactly (1, 0); the flag change starts a new span (a new V1 word)."""
    tm = b"0 1 -1 0 300 100 Tm" if vertical else b"1 0 0 1 100 300 Tm"
    content = b"BT /F1 20 Tf %s (AB) Tj %.4f %.4f Td (CD) Tj ET\n" % (tm, 20.0, 20 * rise)
    got = same(simple(tmp_path / "s.pdf", [b"500"] * 95, content=content))
    assert len(got["words"]) == (2 if (not vertical and rise > 0.1 + 1e-6) else 1)


def test_unicode_no_break_space_reads_as_a_space(tmp_path):
    """WinAnsi code 160 = U+00A0: MuPDF maps it to U+0020 (no synthesized space after it)."""
    content = b"BT /F1 20 Tf 100 300 Td (3.20\xa0x 4.15) Tj ET\n"
    got = same(simple(tmp_path / "n.pdf", [b"500"] * 95, first=b"32", last=b"255", content=content))
    assert got["words"][0]["value"] == "3.20 x 4.15"
