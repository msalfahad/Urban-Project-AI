"""OPENING HEIGHT FROM A PDF, V2 (T-465 r2, owner directive 2026-11-02 D4): the same method as OPENING_HEIGHT_PDF_V1
(engine/source/opening_height_pdf.py, T-082), with ONE change: a PDF page is read by pypdf (BSD-3-Clause, pinned
pypdf==6.19.0, registered in the engine dependency register B-5) instead of PyMuPDF (AGPL-3.0 / commercial;
PLAN_READER.md 'not PyMuPDF'; T-210 (b)). Reading a view, binding a dimension, the merge rules, statuses and hold reasons
are V1's, called unchanged (view_from_page, measure_pdf are V1's functions).

    page_primitives(path, page_no=1)  -> {"page", "width_pt", "height_pt", "state", "words", "segments", "has_image",
                                          "reader"}  (the V1 record + "reader" diagnostics)

What "the same page reading" means (proved against the V1 reader in tests/t465_pdf_reader_v2, PyMuPDF used there as a
TEST ORACLE only, never by the engine):
- Coordinates: PDF points, origin at the lower-left corner of the visible page box (CropBox within MediaBox), y UP, the
  page /Rotate applied, exactly as V1 converts PyMuPDF's page space. Arithmetic is IEEE single precision step by step
  (the precision PyMuPDF / MuPDF compute in), so a coordinate is the same float, not merely a close one.
- Segments: every PAINTED path (stroke, fill or both; a clip-only or 'n' path is not drawn and gives none). A 're'
  rectangle and a closed run of four lines give the 4 sides (+ the closing repeat) as V1 does; a closepath adds its
  closing line; a Bezier ('c', 'v', 'y') gives 8 chords; a path filled and stroked with the same items is listed once.
  Form XObjects are followed with their /Matrix; q / Q / cm as the PDF says. Ids "pdf<n>.<i>" count path items as V1.
- Words: one word per span as PyMuPDF lists it (r4: MuPDF's text-device rules, measured and pinned in
  test_pdf_reader_v2_r4_widths): a glyph continues the LINE when its direction agrees and it is less than 0.8 em off
  the baseline and -0.8 < spacing < 0.8 em from the pen (end of the previous glyph); 0.15 .. 0.8 em forward adds a
  synthesized space, above 0.3 em a LARGE one that is a span of its own (so V1 lists the two sides as two words); the
  same character printed again within 0.1 em of the previous one is dropped (fake bold); a new SPAN starts on a font,
  size, colour or superscript change; a line with no glyph extent is skipped and its empty LAST span dropped. Glyph
  widths are read as MuPDF stores them: integers (r4, _pdf_int; /MissingWidth truncated); the word space Tw is its own
  translation step. Text = the font's ToUnicode / encoding (Unicode spaces as U+0020); box = union of the
  glyph boxes from the advance width and the font's ascender / descender as MuPDF reads them (r3): a FontDescriptor
  governs, embedded program or not (Ascent <= 0 -> 0.8 / -0.2; otherwise Ascent / 1000 and -|Descent| / 1000);
  without a descriptor, MuPDF's built-in font by exact /BaseFont name (BUILTIN_NAMES), Times-Roman otherwise; flagged
  "font_metrics" DESCRIPTOR / DESCRIPTOR_DEFAULT / BUILTIN in "reader". When ascender - descender is below 1 em the
  glyph box across the line is rescaled to the font size (PyMuPDF's quad correction, _quad_correction). A glyph wholly
  outside the page is not read (V1 default). dir = the writing direction normalised in single precision, y UP.
- state: VECTOR when it has words or segments, RASTER_ONLY when it has only images, EMPTY otherwise (V1's test).
What it does NOT do (and says so in "reader"): optional-content visibility, Type3 glyph boxes, vertical writing mode,
right-to-left text, encrypted files it cannot open; such a page is read with the listed limitation or raises, never
silently as empty. NAMED DIFFERENCE (r4, flagged "GLYPH_ACROSS_PAGE_EDGE" in "reader"): a glyph whose box crosses the
page edge is kept when any part of its advance x ascender..descender box is on the page, whereas MuPDF tests the
glyph OUTLINE's bounds; only such glyphs (and the word they belong to) can differ from V1.

Rules: those of V1 (UP-OPEN-SCHED-001, UP-DOOR-AREA-001, UP-DOOR-HGT-001, UP-QTY-STATUS-001, OWNER-Q32-A, OWNER-Q33-A,
OWNER-Q17-A, L-P9-02). Project-agnostic: no layer, title, sheet or project name is coded.
"""

from __future__ import annotations

import math
import struct

from engine.source import opening_height_pdf as V1

POLICY_ID = "OPENING_HEIGHT_PDF_V2"
DEFAULT_GUARD_CLASS = "UNWIRED_PRODUCER"  # T-212 / T-465: opening heights / m2; imported by no method or CLI
RULES = V1.RULES
BEZIER_CHORDS = 8
MILLI = struct.unpack("f", struct.pack("f", 0.001))[0]      # 0.001 in single precision (glyph space -> em)

# MuPDF's built-in substitutes for the 14 standard fonts: (ascender, descender) per em, as MuPDF reports them for a
# non-embedded standard font (the V1 reader's glyph boxes); read once from PyMuPDF 1.28.2 and pinned by the oracle test.
BASE14_ASC_DSC = {
    "Courier": (0.932, -0.317), "Courier-Bold": (1.007, -0.393), "Courier-BoldOblique": (0.997, -0.393),
    "Courier-Oblique": (0.920, -0.317), "Helvetica": (1.075, -0.299), "Helvetica-Bold": (1.070, -0.307),
    "Helvetica-BoldOblique": (1.073, -0.309), "Helvetica-Oblique": (1.070, -0.284), "Symbol": (1.010, -0.293),
    "Times-Bold": (1.044, -0.341), "Times-BoldItalic": (0.972, -0.324), "Times-Italic": (0.951, -0.270),
    "Times-Roman": (1.053, -0.281), "ZapfDingbats": (0.819, -0.144)}
BASE14_ALIAS = {"Arial": "Helvetica", "Arial,Bold": "Helvetica-Bold", "Arial,Italic": "Helvetica-Oblique",
                "Arial,BoldItalic": "Helvetica-BoldOblique", "CourierNew": "Courier", "TimesNewRoman": "Times-Roman"}
# r3: the /BaseFont names MuPDF loads as one of its 14 built-in fonts when a simple font has NO FontDescriptor (each
# pinned against PyMuPDF 1.28.2 in tests/t465_pdf_reader_v2); any other name gets Times-Roman.
BUILTIN_NAMES = {n: n for n in BASE14_ASC_DSC}
for _base, _names in (
        ("Courier", "CourierNew CourierNewPSMT"),
        ("Courier-Oblique", "CourierNew,Italic CourierNew-Italic CourierNewPS-ItalicMT"),
        ("Courier-Bold", "CourierNew,Bold CourierNew-Bold CourierNewPS-BoldMT"),
        ("Courier-BoldOblique", "CourierNew,BoldItalic CourierNew-BoldItalic CourierNewPS-BoldItalicMT"),
        ("Helvetica", "ArialMT Arial"),
        ("Helvetica-Oblique", "Arial-ItalicMT Arial,Italic Arial-Italic"),
        ("Helvetica-Bold", "Arial-BoldMT Arial,Bold Arial-Bold"),
        ("Helvetica-BoldOblique", "Arial-BoldItalicMT Arial,BoldItalic Arial-BoldItalic"),
        ("Times-Roman", "TimesNewRomanPSMT TimesNewRoman"),
        ("Times-Italic", "TimesNewRomanPS-ItalicMT TimesNewRoman,Italic TimesNewRoman-Italic"),
        ("Times-Bold", "TimesNewRomanPS-BoldMT TimesNewRoman,Bold TimesNewRoman-Bold"),
        ("Times-BoldItalic", "TimesNewRomanPS-BoldItalicMT TimesNewRoman,BoldItalic TimesNewRoman-BoldItalic")):
    for _n in _names.split():
        BUILTIN_NAMES[_n] = _base
FLT_EPSILON = 1.1920928955078125e-07

# ------------------------------------------------------------------------------------------- single precision
def _f(x):
    """x rounded to IEEE single precision (an exact product / sum of two singles rounded once = the single result)."""
    return struct.unpack("f", struct.pack("f", float(x)))[0]


def _pdf_int(v):
    """a PDF number read as MuPDF's pdf_to_int reads it (r4, T-465 Checker 19:57): an integer as is; a real is held in
    single precision and rounded as floorf(f + 0.5f) (x.5 up, -x.5 toward zero: 500.5 -> 501, -0.5 -> 0, -2.5 -> -2);
    anything else 0. MuPDF stores every glyph width (/Widths, /W, /DW, /MissingWidth) and FirstChar / LastChar so."""
    if hasattr(v, "get_object"):
        v = v.get_object()
    if isinstance(v, bool):
        return 0
    if isinstance(v, int):
        return int(v)
    try:
        x = float(v)
    except (TypeError, ValueError):
        return 0
    if x != x or x in (float("inf"), float("-inf")):
        return 0
    return int(math.floor(_f(_f(x) + 0.5)))


def _concat(one, two):
    a1, b1, c1, d1, e1, f1 = one
    a2, b2, c2, d2, e2, f2 = two
    return (_f(_f(a1 * a2) + _f(b1 * c2)), _f(_f(a1 * b2) + _f(b1 * d2)),
            _f(_f(c1 * a2) + _f(d1 * c2)), _f(_f(c1 * b2) + _f(d1 * d2)),
            _f(_f(_f(e1 * a2) + _f(f1 * c2)) + e2), _f(_f(_f(e1 * b2) + _f(f1 * d2)) + f2))


def _tp(x, y, m):
    return (_f(_f(_f(x * m[0]) + _f(y * m[2])) + m[4]), _f(_f(_f(x * m[1]) + _f(y * m[3])) + m[5]))


def _tv(x, y, m):
    return (_f(_f(x * m[0]) + _f(y * m[2])), _f(_f(x * m[1]) + _f(y * m[3])))


def _mat(ops):
    return tuple(_f(v) for v in ops[:6])


def _page_ctm(page):
    """PDF user space -> the reader's page space (y DOWN, origin top-left of the rotated visible box)."""
    mb = [_f(v) for v in page.mediabox]
    cb = [_f(v) for v in (page.cropbox if "/CropBox" in page else page.mediabox)]
    mb = [min(mb[0], mb[2]), min(mb[1], mb[3]), max(mb[0], mb[2]), max(mb[1], mb[3])]
    cb = [min(cb[0], cb[2]), min(cb[1], cb[3]), max(cb[0], cb[2]), max(cb[1], cb[3])]
    box = [max(mb[0], cb[0]), max(mb[1], cb[1]), min(mb[2], cb[2]), min(mb[3], cb[3])]
    rot = int(page.get("/Rotate", 0) or 0) % 360
    if rot % 90:
        raise ValueError(f"page /Rotate {rot} is not a multiple of 90")
    # the V1 reader's words and drawings are in the UNROTATED page space (y down from the box top), while its page
    # height is that of the ROTATED page: reproduced as it is (finding F-T465-2: on a /Rotate 90 / 270 page every V1
    # y is shifted by width - height; correcting it is a behaviour change for a later version, not this one)
    m = (1.0, 0.0, 0.0, -1.0, _f(-box[0]), box[3])
    w, h = _f(box[2] - box[0]), _f(box[3] - box[1])
    return m, (h if rot in (90, 270) else w), (w if rot in (90, 270) else h), (w, h)


# ------------------------------------------------------------------------------------------- paths
class _Path:
    """MuPDF's path tracing as the V1 reader sees it: items 'l' (p, q), 're' (rect), 'qu' (4 corners), 'c' (4 points)
    in page space."""

    def __init__(self):
        self.cmds = []                      # user-space construction: ("m", x, y) / ("l", x, y) / ("c", ...) / ("h",)
        self.cur = None
        self.start = None

    def moveto(self, x, y):
        if self.cmds and self.cmds[-1][0] == "m":
            self.cmds[-1] = ("m", x, y)
        else:
            self.cmds.append(("m", x, y))
        self.cur = self.start = (x, y)

    def lineto(self, x, y):
        if self.cur is None:
            return self.moveto(x, y)
        if self.cmds and self.cmds[-1][0] in ("l", "c", "h", "re") and self.cur == (x, y):
            return                          # a line to the current point after a drawn piece is a nop
        self.cmds.append(("l", x, y))
        self.cur = (x, y)

    def curveto(self, x1, y1, x2, y2, x3, y3):
        if self.cur is None:
            self.moveto(x1, y1)
        x0, y0 = self.cur
        if (x0, y0) == (x1, y1) and (x2, y2) == (x3, y3):
            if (x1, y1) == (x2, y2) and self.cmds and self.cmds[-1][0] != "m":
                return
            return self.lineto(x3, y3)
        self.cmds.append(("c", x1, y1, x2, y2, x3, y3))
        self.cur = (x3, y3)

    def closepath(self):
        if self.cur is None or not self.cmds or self.cmds[-1][0] == "h":
            return
        self.cmds.append(("h",))
        self.cur = self.start

    def rect(self, x, y, w, h):
        self.cmds.append(("re", x, y, x + w, y + h))
        self.cur = self.start = (x, y)

    def items(self, ctm, fill_only):
        """the traced item list (PyMuPDF's line-art device: rectangle and quad detection on consecutive lines)."""
        out = []
        st = {"last": (0.0, 0.0), "first": (0.0, 0.0), "move": False, "lines": 0}

        def move(x, y):
            st["last"] = st["first"] = _tp(x, y, ctm)
            st["move"], st["lines"] = True, 0

        def line(x, y):
            p = _tp(x, y, ctm)
            out.append(("l", st["last"], p))
            st["last"] = p
            st["lines"] += 1
            if st["lines"] == 4 and not fill_only:
                _checkquad(out, st)

        def close():
            if st["lines"] == 3 and _checkrect(out, st):
                return
            st["lines"] = 0
            if st["move"]:
                if st["last"] != st["first"]:
                    out.append(("l", st["last"], st["first"]))
                    st["last"] = st["first"]
            st["move"] = False

        for c in self.cmds:
            if c[0] == "m":
                move(c[1], c[2])
            elif c[0] == "l":
                line(c[1], c[2])
            elif c[0] == "c":
                st["lines"] = 0
                p1, p2, p3 = _tp(c[1], c[2], ctm), _tp(c[3], c[4], ctm), _tp(c[5], c[6], ctm)
                out.append(("c", st["last"], p1, p2, p3))
                st["last"] = p3
            elif c[0] == "h":
                close()
            elif c[0] == "re":
                x0, y0, x1, y1 = c[1:]
                move(x0, y0)
                line(x1, y0)
                line(x1, y1)
                line(x0, y1)
                close()
        return out


def _checkquad(items, st):
    ln = items[-4:]
    f = [v for it in ln for v in it[1]]
    lp = ln[3][2]
    if lp != (f[0], f[1]):
        return 0
    st["lines"] = 0
    items[-4:] = [("qu", ((f[0], f[1]), (f[6], f[7]), (f[2], f[3]), (f[4], f[5])))]     # ul, ur, ll, lr
    return 1


def _checkrect(items, st):
    st["lines"] = 0
    ll, lr = items[-3][1], items[-3][2]
    ur, ul = items[-1][1], items[-1][2]
    if ll[1] != lr[1] or ll[0] != ul[0] or ur[1] != ul[1] or ur[0] != lr[0]:
        return 0
    if ul[1] < lr[1]:
        r = (ul[0], ul[1], lr[0], lr[1])
    else:
        r = (ll[0], ll[1], ur[0], ur[1])
    items[-3:] = [("re", r)]
    return 1


def _segments_of(item):
    """V1's conversion of one traced item into point chains (page space, y DOWN)."""
    k = item[0]
    if k == "l":
        return [item[1], item[2]]
    if k == "re":
        x0, y0, x1, y1 = item[1]
        x0, x1 = min(x0, x1), max(x0, x1)
        y0, y1 = min(y0, y1), max(y0, y1)
        return [(x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0)]
    if k == "qu":
        ul, ur, ll, lr = item[1]
        return [ul, ur, lr, ll, ul]
    p0, c1, c2, p3 = item[1:]
    pts = []
    for j in range(BEZIER_CHORDS + 1):
        t = j / float(BEZIER_CHORDS)
        a, b, c, e = (1 - t) ** 3, 3 * (1 - t) ** 2 * t, 3 * (1 - t) * t * t, t ** 3
        pts.append((a * p0[0] + b * c1[0] + c * c2[0] + e * p3[0], a * p0[1] + b * c1[1] + c * c2[1] + e * p3[1]))
    return pts


# ------------------------------------------------------------------------------------------- fonts
class _Font:
    def __init__(self, fd):
        from pypdf._cmap import get_encoding                         # pypdf's own encoding / ToUnicode reader
        self.sub = str(fd.get("/Subtype", ""))
        self.name = str(fd.get("/BaseFont", "")).lstrip("/")
        self.encoding, self.tounicode = get_encoding(fd)
        self.cid = self.sub == "/Type0"
        enc_name = str(fd.get("/Encoding", ""))
        self.utf16 = self.cid and ("UTF16" in enc_name or "UCS2" in enc_name)
        self.widths, self.default_w = {}, 0.0
        desc = None
        if self.cid:
            d = fd["/DescendantFonts"][0].get_object()
            self.default_w = float(_pdf_int(d["/DW"]) if "/DW" in d else 1000)       # r4: integer, as MuPDF
            w = list(d.get("/W", []))
            i = 0
            while i < len(w):
                a = _pdf_int(w[i])
                b = w[i + 1]
                if isinstance(b, (list, tuple)) or hasattr(b, "__iter__"):
                    for k, v in enumerate(b.get_object() if hasattr(b, "get_object") else b):
                        self.widths[a + k] = float(_pdf_int(v))
                    i += 2
                else:
                    for k in range(a, _pdf_int(b) + 1):
                        self.widths[k] = float(_pdf_int(w[i + 2]))
                    i += 3
            desc = d.get("/FontDescriptor")
        else:
            wl = fd.get("/Widths")
            if wl is not None:
                # r4: MuPDF's simple-font table: FirstChar / LastChar and every width read as integers (_pdf_int);
                # codes FirstChar .. LastChar only (a missing entry = 0); FirstChar < 0, LastChar > 255 or
                # FirstChar > LastChar -> FirstChar = LastChar = 0; every other code takes the MissingWidth
                wl = list(wl.get_object() if hasattr(wl, "get_object") else wl)
                first, last = _pdf_int(fd.get("/FirstChar", 0)), _pdf_int(fd.get("/LastChar", 0))
                if first < 0 or last > 255 or first > last:
                    first = last = 0
                for k in range(last - first + 1):
                    self.widths[first + k] = float(_pdf_int(wl[k]) if k < len(wl) else 0)
            desc = fd.get("/FontDescriptor")
            base = BASE14_ALIAS.get(self.name, self.name.split("+")[-1])
            if not self.widths and base in BASE14_ASC_DSC:
                from pypdf._codecs.core_font_metrics import CORE_FONT_METRICS
                cw = CORE_FONT_METRICS[base].character_widths
                for code in range(256):
                    ch = self._enc(code)
                    if ch in cw:
                        self.widths[code] = float(cw[ch])
                self.default_w = float(cw.get("default", 0))
        desc = desc.get_object() if desc is not None else None
        if desc is not None and "/MissingWidth" in desc and not self.cid:
            mw = desc["/MissingWidth"]                                  # r4: MuPDF reads it as a real held in an
            mw = mw.get_object() if hasattr(mw, "get_object") else mw   # int field: truncated toward zero
            try:                                                        # (433.7 -> 433, -433.7 -> -433)
                mw = float(mw)
                self.default_w = float(int(_f(mw))) if math.isfinite(mw) else 0.0
            except (TypeError, ValueError):
                self.default_w = 0.0
        # r3: MuPDF's font ascender / descender (measured against PyMuPDF 1.28.2, tests/t465_pdf_reader_v2):
        # - a FontDescriptor, embedded program or not, governs: Ascent <= 0 -> (0.8, -0.2); otherwise
        #   (Ascent / 1000, -|Descent| / 1000): a POSITIVE Descent is read as below the baseline. The program's own
        #   hhea / OS/2 values are not used, nor the 14 standard fonts' built-in values.
        # - no FontDescriptor: MuPDF's built-in substitute named by BUILTIN_NAMES (exact /BaseFont, subset prefix
        #   kept), Times-Roman for any other name.
        if desc is not None:
            a = _f(float(desc.get("/Ascent", 0) or 0))
            d = _f(float(desc.get("/Descent", 0) or 0))
            if a <= 0:
                self.asc, self.dsc = 0.8, -0.2
                self.metrics = "DESCRIPTOR_DEFAULT"
            else:
                self.asc, self.dsc = a / 1000.0, -abs(d) / 1000.0
                self.metrics = "DESCRIPTOR"
        else:
            self.asc, self.dsc = BASE14_ASC_DSC[BUILTIN_NAMES.get(self.name, "Times-Roman")]
            self.metrics = "BUILTIN"
        self.asc, self.dsc = _f(self.asc), _f(self.dsc)

    def _enc(self, code):
        if isinstance(self.encoding, dict):
            return self.encoding.get(code, chr(code))
        try:
            return bytes([code]).decode(self.encoding)
        except (UnicodeDecodeError, LookupError):
            return chr(code)

    def codes(self, raw):
        if self.cid:
            return [(raw[i] << 8) | raw[i + 1] for i in range(0, len(raw) - 1, 2)]
        return list(raw)

    def text(self, code):
        if self.cid:
            key = chr(code)
            if key in self.tounicode:
                return self.tounicode[key]
            if self.utf16:
                return chr(code)
            return "\ufffd"
        key = chr(code)
        if key in self.tounicode:
            return self.tounicode[key]
        return self._enc(code)

    def width(self, code):
        return _f(_f(self.widths.get(code, self.default_w)) * MILLI)


# ------------------------------------------------------------------------------------------- the page
def page_primitives(path, page_no=1):
    """One PDF page -> V1's record: words (span text, box and direction, y UP) and segments (lines, rectangle sides and
    Bezier curves flattened into 8 chords; y UP); state VECTOR / RASTER_ONLY / EMPTY. Read with pypdf."""
    from pypdf import PdfReader
    from pypdf.generic import ContentStream

    reader = PdfReader(str(path))
    page = reader.pages[page_no - 1]
    ctm0, W, H, (UW, UH) = _page_ctm(page)
    out = {"segs": [], "n": 0, "words": [], "run": None, "metrics": set(), "limits": set(), "img": False,
           "drawn": [], "runs": [],
           "dev": {"line": None, "pen": None, "lag": None, "lastchar": None}}

    def flush():
        r = out["run"]
        if r is not None and r["box"] is not None:
            out["runs"].append(r)
        out["run"] = None

    def draw(p, ctm, fill_only, kind):
        items = p.items(ctm, fill_only)
        if not items:
            return
        prev = out["drawn"][-1] if out["drawn"] else None
        if kind == "s" and prev is not None and prev[0] == "f" and prev[1] == items:
            out["drawn"][-1] = ("fs", items)               # the same path filled then stroked: listed once
            return
        out["drawn"].append((kind, items))

    def show(st, ts, raw):
        font = ts["font"]
        if font is None:
            return
        size, th, rise = ts["size"], ts["scale"], ts["rise"]
        tsm = (_f(size * th), 0.0, 0.0, _f(size), 0.0, _f(rise))
        for code in font.codes(raw):
            trm = _concat(_concat(tsm, ts["tm"]), st["ctm"])
            adv = _f(font.width(code))
            ox, oy = trm[4], trm[5]
            ax, ay = _tv(0.0, font.asc, trm)
            dx, dy = _tv(0.0, font.dsc, trm)
            qx, qy = _tv(adv, 0.0, trm)
            qx, qy = _f(ox + qx), _f(oy + qy)
            pts = [(_f(ox + dx), _f(oy + dy)), (_f(ox + ax), _f(oy + ay)), (_f(qx + dx), _f(qy + dy)),
                   (_f(qx + ax), _f(qy + ay))]
            box = (min(p[0] for p in pts), min(p[1] for p in pts), max(p[0] for p in pts), max(p[1] for p in pts))
            visible = box[2] >= 0 and box[0] <= UW and box[3] >= 0 and box[1] <= UH
            if visible and (box[0] < 0 or box[2] > UW or box[1] < 0 or box[3] > UH):
                # NAMED DIFFERENCE (r4): MuPDF drops a glyph only when its OUTLINE bounds lie wholly outside the page;
                # this reader tests the advance x ascender..descender box, so a glyph across the page edge may be
                # kept here and dropped by V1 (or the reverse). Flagged on the page record; no other glyph is affected.
                out["limits"].add("GLYPH_ACROSS_PAGE_EDGE")
            fdir = _normalize(trm[0], trm[1])
            ch = font.text(code)
            size_e = math.sqrt(abs(trm[0] * trm[3] - trm[1] * trm[2])) or 1e-9
            key = (id(font), round(size_e, 4), st["fill"])
            r = out["run"]
            dev = out["dev"]
            if visible and len(ch) == 1 and ord(ch) in _WHITESPACE:
                ch = " "                                            # MuPDF maps the Unicode spaces to U+0020
            if visible and not _fake_bold(dev, ch, ox, oy, fdir, _expansion(trm) or 1e-9):
                # r4: MuPDF's text device (1.28.2), left-to-right writing, measured from the pen = the end of the
                # previous glyph: the same line when the direction agrees (dot >= 0.999) and the glyph is less
                # than 0.8 em off the baseline and -0.8 < spacing < 0.8 em; a synthesized space when the spacing is
                # 0.15 .. 0.8 em after a character that may take one; that space is LARGE above 0.3 em.
                ln, sz = dev["line"], (_expansion(trm) or 1e-9)
                new_line, add_space = True, 0
                if ln is not None and fdir[0] * ln["fdir"][0] + fdir[1] * ln["fdir"][1] >= 0.999:
                    dx_, dy_ = ox - dev["pen"][0], oy - dev["pen"][1]
                    along = (fdir[0] * dx_ + fdir[1] * dy_) / sz
                    across = (-fdir[1] * dx_ + fdir[0] * dy_) / sz
                    if abs(across) < 0.8:
                        if abs(along) < 0.15 or -0.8 < along < 0:
                            new_line = False
                        elif 0 < along < 0.8:
                            new_line = False
                            if _may_add_space(dev["lastchar"]):
                                add_space = 2 if along > 0.3 else 1
                if new_line:
                    ln = dev["line"] = {"id": (ln["id"] + 1) if ln else 1, "fdir": fdir, "oy": oy}
                # PyMuPDF's span: a new one when font / size / colour, its superscript flag (a line whose direction
                # is exactly (1, 0): origin more than 0.1 x size above the line's first glyph) or MuPDF's
                # SYNTHETIC_LARGE flag change; a large synthesized space is a span of its own (V1 strips it)
                sup = ln["fdir"] == (1.0, 0.0) and oy < _f(ln["oy"] - _f(sz * _f(0.1)))
                synth = add_space and ch != " "
                if (new_line or r is None or r["line"] != ln["id"] or r["key"] != key or r["sup"] != sup
                        or (synth and add_space == 2)):
                    flush()
                    r = out["run"] = {"key": key, "text": "", "box": None, "raw": None, "fdir": fdir,
                                      "line": ln["id"], "sup": sup}
                elif synth:
                    r["text"] += " "
                rawbox = box
                # r3: the glyph box the V1 reader reports (PyMuPDF's quad correction of a font whose
                # ascender - descender is below 1 em: the box height becomes the font size)
                fixed = _quad_correction(font, pts, (ox, oy), sz, r["fdir"], out["limits"])
                if fixed is not None:
                    box = fixed
                r["text"] += ch
                r["box"] = _union(r["box"], box)
                if not _empty(rawbox):
                    r["raw"] = _union(r["raw"], rawbox)
                dev["lastchar"], dev["lag"], dev["pen"] = ch, (ox, oy), (qx, qy)
            # pen advance in text space: (w0 x size + Tc) x Th; then, for a single-byte code 32, a SEPARATE
            # translation by Tw x Th (r4: MuPDF applies the word space as its own step, rounded on its own)
            tx = _f(_f(_f(adv * size) + ts["tc"]) * th)
            ts["tm"] = _concat((1.0, 0.0, 0.0, 1.0, tx, 0.0), ts["tm"])
            if not font.cid and code == 32:
                ts["tm"] = _concat((1.0, 0.0, 0.0, 1.0, _f(ts["tw"] * th), 0.0), ts["tm"])
            out["metrics"].add(font.metrics)

    def run(content, resources, ctm, depth=0, tstate=None):
        if depth > 12:
            out["limits"].add("FORM_DEPTH")
            return
        fonts = {}
        res_fonts = (resources or {}).get("/Font", {}) or {}
        xobjs = (resources or {}).get("/XObject", {}) or {}
        st = {"ctm": ctm, "fill": (0.0,), "clip": False}
        stack = []
        p = _Path()
        ts = {"font": None, "size": 0.0, "scale": 1.0, "rise": 0.0, "tc": 0.0, "tw": 0.0, "tl": 0.0,
              "tm": (1.0, 0.0, 0.0, 1.0, 0.0, 0.0), "tlm": (1.0, 0.0, 0.0, 1.0, 0.0, 0.0)}
        if tstate is not None:
            for k in ("font", "size", "scale", "rise", "tc", "tw", "tl"):
                ts[k] = tstate[k]
        for ops, op in content.operations:
            o = op.decode("latin-1") if isinstance(op, bytes) else str(op)
            if o == "q":
                stack.append((dict(st), dict(ts)))
            elif o == "Q":
                if stack:
                    s0, t0 = stack.pop()
                    st.update(s0)
                    for k in ("font", "size", "scale", "rise", "tc", "tw", "tl"):
                        ts[k] = t0[k]
            elif o == "cm":
                st["ctm"] = _concat(_mat(ops), st["ctm"])
            elif o in ("rg", "g", "k", "sc", "scn"):
                st["fill"] = tuple(round(float(v), 6) for v in ops if not isinstance(v, str))
            elif o == "m":
                p.moveto(_f(ops[0]), _f(ops[1]))
            elif o == "l":
                p.lineto(_f(ops[0]), _f(ops[1]))
            elif o == "c":
                p.curveto(*(_f(v) for v in ops[:6]))
            elif o == "v":
                if p.cur is not None:
                    p.curveto(p.cur[0], p.cur[1], _f(ops[0]), _f(ops[1]), _f(ops[2]), _f(ops[3]))
            elif o == "y":
                p.curveto(_f(ops[0]), _f(ops[1]), _f(ops[2]), _f(ops[3]), _f(ops[2]), _f(ops[3]))
            elif o == "h":
                p.closepath()
            elif o == "re":
                x, y, w, h = (_f(v) for v in ops[:4])
                p.rect(x, y, _f(w), _f(h))
            elif o in ("W", "W*"):
                st["clip"] = True
            elif o in ("S", "s", "f", "F", "f*", "B", "B*", "b", "b*", "n"):
                if o in ("s", "b", "b*"):
                    p.closepath()
                if o in ("f", "F", "f*", "B", "B*", "b", "b*"):
                    draw(p, st["ctm"], True, "f")
                if o in ("S", "s", "B", "B*", "b", "b*"):
                    draw(p, st["ctm"], False, "s")
                p = _Path()
                st["clip"] = False
            elif o == "BT":
                ts["tm"] = ts["tlm"] = (1.0, 0.0, 0.0, 1.0, 0.0, 0.0)
            elif o == "ET":
                pass
            elif o == "Tf":
                name = ops[0]
                if name not in fonts:
                    fd = res_fonts.get(name)
                    fonts[name] = _Font(fd.get_object()) if fd is not None else None
                ts["font"], ts["size"] = fonts[name], _f(ops[1])
            elif o == "Tc":
                ts["tc"] = _f(ops[0])
            elif o == "Tw":
                ts["tw"] = _f(ops[0])
            elif o == "Tz":
                ts["scale"] = _f(float(ops[0]) / 100.0)
            elif o == "TL":
                ts["tl"] = _f(ops[0])
            elif o == "Ts":
                ts["rise"] = _f(ops[0])
            elif o in ("Td", "TD"):
                if o == "TD":
                    ts["tl"] = _f(-float(ops[1]))
                ts["tlm"] = _concat((1.0, 0.0, 0.0, 1.0, _f(ops[0]), _f(ops[1])), ts["tlm"])
                ts["tm"] = ts["tlm"]
            elif o == "Tm":
                ts["tm"] = ts["tlm"] = _mat(ops)
            elif o in ("T*", "'", '"'):
                if o == '"':
                    ts["tw"], ts["tc"] = _f(ops[0]), _f(ops[1])
                ts["tlm"] = _concat((1.0, 0.0, 0.0, 1.0, 0.0, _f(-ts["tl"])), ts["tlm"])
                ts["tm"] = ts["tlm"]
                if o != "T*":
                    show(st, ts, _raw(ops[-1]))
            elif o == "Tj":
                show(st, ts, _raw(ops[0]))
            elif o == "TJ":
                for el in ops[0]:
                    if isinstance(el, (int, float)) and not isinstance(el, bool):
                        tx = _f(_f(_f(_f(-float(el)) * ts["size"]) * ts["scale"]) * MILLI)
                        ts["tm"] = _concat((1.0, 0.0, 0.0, 1.0, tx, 0.0), ts["tm"])
                    else:
                        show(st, ts, _raw(el))
            elif o == "Do":
                xo = xobjs.get(ops[0])
                xo = xo.get_object() if xo is not None else None
                if xo is None:
                    continue
                sub = xo.get("/Subtype")
                if sub == "/Image":
                    out["img"] = True
                elif sub == "/Form":
                    m = _mat(xo.get("/Matrix", [1, 0, 0, 1, 0, 0]))
                    flush()
                    run(ContentStream(xo, reader), xo.get("/Resources", resources), _concat(m, st["ctm"]), depth + 1,
                        ts)
            elif o == "INLINE IMAGE":
                pass                                                 # V1's image test lists XObject images only
            elif o in ("d0", "d1", "sh", "BX", "EX", "BMC", "BDC", "EMC", "MP", "DP", "ri", "i", "gs", "w", "J",
                       "j", "M", "d", "RG", "G", "K", "SC", "SCN", "CS", "cs", "Tr"):
                continue

    res = page.get("/Resources")
    res = res.get_object() if res is not None else {}
    contents = page.get_contents()
    if contents is not None:
        run(ContentStream(contents, reader), res, ctm0)
    flush()
    if not out["img"]:
        out["img"] = _has_image(res, 0)
    n = 0
    for _kind, items in out["drawn"]:
        for it in items:
            n += 1
            pts = _segments_of(it)
            for i, (a, b) in enumerate(zip(pts, pts[1:])):
                if a != b:
                    out["segs"].append((a[0], H - a[1], b[0], H - b[1], f"pdf{n}.{i}"))
    # r4: words from the spans as PyMuPDF lists them: a LINE none of whose glyphs has a non-empty box is skipped; in a
    # kept line the LAST span is dropped when its box is empty (zero advance), earlier spans stay (PyMuPDF 1.28.2
    # JM_make_text_block / JM_make_spanlist); V1 then keeps each span whose stripped text is not empty
    words, i, runs = [], 0, out["runs"]
    while i < len(runs):
        j = i
        while j < len(runs) and runs[j]["line"] == runs[i]["line"]:
            j += 1
        line = runs[i:j]
        if any(r["raw"] is not None for r in line):
            for k, r in enumerate(line):
                t = r["text"].strip()
                if not t or (k == len(line) - 1 and _empty(r["box"])):
                    continue
                x0, y0, x1, y1 = r["box"]
                words.append({"value": t, "x0": x0, "y0": H - y1, "x1": x1, "y1": H - y0,
                              "dir": (round(r["fdir"][0], 6), round(-r["fdir"][1], 6))})
        i = j
    segs = out["segs"]
    has_img = bool(out["img"])
    state = "VECTOR" if (words or segs) else ("RASTER_ONLY" if has_img else "EMPTY")
    return {"page": page_no, "width_pt": W, "height_pt": H, "state": state, "words": words, "segments": segs,
            "has_image": has_img,
            "reader": {"policy": POLICY_ID, "library": "pypdf", "font_metrics": sorted(out["metrics"]),
                       "limits": sorted(out["limits"] | {"OPTIONAL_CONTENT_NOT_EVALUATED"})}}


_WHITESPACE = {0x09, 0x20, 0xA0, 0x1680, 0x180E, *range(0x2000, 0x200B), 0x202F, 0x205F, 0x3000}


def _may_add_space(last):
    """MuPDF: a synthesized space only after a character that is not a space, in Basic Latin .. Hebrew / Arabic
    (below U+0700) or in General Punctuation .. Currency Symbols (U+2000 .. U+20CF)."""
    if not last or last == " ":
        return False
    c = ord(last[-1])
    return c < 0x700 or 0x2000 <= c <= 0x20CF


def _fake_bold(dev, ch, ox, oy, fdir, size):
    """MuPDF drops a glyph printed again on the previous one (fake bold): same character, the current line in the same
    direction, origin less than 0.1 em from the previous glyph's origin. The dropped glyph leaves the device state."""
    ln, lag = dev["line"], dev["lag"]
    if ln is None or lag is None or ch != dev["lastchar"] or fdir[0] * ln["fdir"][0] + fdir[1] * ln["fdir"][1] < 0.999:
        return False
    return _f(math.hypot(_f(ox - lag[0]), _f(oy - lag[1]))) / size < 0.1


def _empty(b):
    """MuPDF fz_is_empty_rect."""
    return b[0] >= b[2] or b[1] >= b[3]


def _union(a, b):
    return b if a is None else (min(a[0], b[0]), min(a[1], b[1]), max(a[2], b[2]), max(a[3], b[3]))


def _normalize(x, y):
    """MuPDF fz_normalize_vector in single precision (the text line direction)."""
    n = _f(_f(x * x) + _f(y * y))
    if n != 0:
        n = _f(math.sqrt(n))
        return _f(x / n), _f(y / n)
    return x, y


def _expansion(m):
    """MuPDF fz_matrix_expansion in single precision (a glyph's size in page space)."""
    return _f(math.sqrt(abs(_f(_f(m[0] * m[3]) - _f(m[1] * m[2])))))


def _quad_correction(font, pts, origin, size, direction, limits):
    """PyMuPDF 1.28.2 JM_char_quad (horizontal writing, default flags), single precision: when the font's ascender -
    descender is below 1 em, the glyph's box across the writing direction is rescaled so that its height is the font
    size (ascender and descender in proportion); along the writing direction the box is the glyph quad's, its start
    clamped to the origin. Returns the corrected (x0, y0, x1, y1) or None when the quad stands as it is.
    pts = the glyph quad as (ll, ul, lr, ur) in page space."""
    asc, dsc = font.asc, font.dsc
    ad = _f(_f(asc - dsc) + FLT_EPSILON)
    if ad >= 1:
        return None
    if asc < 1e-3:
        dsc, asc, ad = _f(-0.1), _f(0.9), 1.0
    if ad < 1:
        dsc, asc = _f(dsc / ad), _f(asc / ad)
    ad = _f(asc - dsc)
    asc, dsc = _f(_f(asc * size) / ad), _f(_f(dsc * size) / ad)
    c, s = direction
    d1 = d2 = c
    if c == -1:
        d1 = d2 = 1.0
    trm1, trm2 = (c, _f(-s), s, d1, 0.0, 0.0), (c, s, _f(-s), d2, 0.0, 0.0)
    ox, oy = origin
    xl1, xl2 = (1.0, 0.0, 0.0, 1.0, _f(-ox), _f(-oy)), (1.0, 0.0, 0.0, 1.0, ox, oy)
    ll, ul, lr, ur = ([*_tp(*_tp(p[0], p[1], xl1), trm1)] for p in pts)
    if c == 1 and ul[1] > 0:
        ul[1] = ur[1] = asc
        ll[1] = lr[1] = dsc
    else:
        ul[1] = ur[1] = _f(-asc)
        ll[1] = lr[1] = _f(-dsc)
    if ll[0] < 0:
        ll[0] = ul[0] = 0.0
    if _f(lr[0] - ll[0]) < FLT_EPSILON:
        limits.add("ZERO_WIDTH_GLYPH_BOX_NOT_WIDENED")          # PyMuPDF widens it from the font program's advance
    q = [_tp(*_tp(p[0], p[1], trm2), xl2) for p in (ul, ur, ll, lr)]
    return (min(p[0] for p in q), min(p[1] for p in q), max(p[0] for p in q), max(p[1] for p in q))


def _raw(s):
    if isinstance(s, bytes):
        return s
    if hasattr(s, "original_bytes"):
        return bytes(s.original_bytes)
    return str(s).encode("latin-1", "replace")


def _has_image(res, depth):
    if depth > 12 or not res:
        return False
    for xo in ((res.get("/XObject") or {}).values()):
        xo = xo.get_object()
        if xo.get("/Subtype") == "/Image":
            return True
        if xo.get("/Subtype") == "/Form" and _has_image(xo.get("/Resources"), depth + 1):
            return True
    return False


# ------------------------------------------------------------------------------------------- V1, unchanged
view_from_page = V1.view_from_page
measure_pdf = V1.measure_pdf
scale_of = V1.scale_of


def policy_record():
    return {"policy": POLICY_ID, "builds_on": V1.POLICY_ID, "rules": list(RULES),
            "change": "page_primitives reads the page with pypdf (BSD-3-Clause, B-5 registered) instead of PyMuPDF "
                      "(AGPL); view_from_page / measure_pdf are V1's, called unchanged",
            "proof": "tests/t465_pdf_reader_v2: words and segments equal to the V1 reader on the T-082 sheets and the "
                     "adverse pages (rotation, crop box, forms, rectangles, quads, closepath, curves, clip / n paths, "
                     "fill + stroke, TJ kerning, scan); r3 test_pdf_reader_v2_r3_metrics: simple TrueType embedded "
                     "(descriptor differs from hhea / OS/2) and non-embedded (ArialMT), positive Descent, Ascent <= 0, "
                     "below-1-em quad correction, built-in names, any angle / mirror; and the real drawing set "
                     "(36 of 36 words, 660,238 segments equal to V1); r4 test_pdf_reader_v2_r4_widths: fractional / "
                     "half / zero / negative glyph widths (simple /Widths, FirstChar / LastChar / MissingWidth; "
                     "composite /W + /DW), zero-advance lines and spans, pen motion back and forward, fake bold, "
                     "superscript and large-space span splits, a seeded corpus; named difference "
                     "GLYPH_ACROSS_PAGE_EDGE"}
