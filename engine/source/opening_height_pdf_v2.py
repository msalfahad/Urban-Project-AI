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
- Words: one word per run of shown text in one font, size, colour and direction whose glyphs follow on from each
  other (the next show starts where the previous one ended); text = the font's ToUnicode / encoding; box = union of the
  glyph boxes from the advance width and the font's ascender / descender (MuPDF's built-in values for the 14 standard
  fonts; the FontDescriptor Ascent / Descent otherwise, flagged "font_metrics: DESCRIPTOR" in "reader"). A glyph wholly
  outside the page is not read (V1 default). dir = the writing direction, y UP.
- state: VECTOR when it has words or segments, RASTER_ONLY when it has only images, EMPTY otherwise (V1's test).
What it does NOT do (and says so in "reader"): optional-content visibility, Type3 glyph boxes, vertical writing mode,
encrypted files it cannot open; such a page is read with the listed limitation or raises, never silently as empty.

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


# ------------------------------------------------------------------------------------------- single precision
def _f(x):
    """x rounded to IEEE single precision (an exact product / sum of two singles rounded once = the single result)."""
    return struct.unpack("f", struct.pack("f", float(x)))[0]


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
            self.default_w = float(d.get("/DW", 1000))
            w = list(d.get("/W", []))
            i = 0
            while i < len(w):
                a = int(w[i])
                b = w[i + 1]
                if isinstance(b, (list, tuple)) or hasattr(b, "__iter__"):
                    for k, v in enumerate(b.get_object() if hasattr(b, "get_object") else b):
                        self.widths[a + k] = float(v)
                    i += 2
                else:
                    for k in range(a, int(b) + 1):
                        self.widths[k] = float(w[i + 2])
                    i += 3
            desc = d.get("/FontDescriptor")
        else:
            first = int(fd.get("/FirstChar", 0))
            for k, v in enumerate(fd.get("/Widths", []) or []):
                self.widths[first + k] = float(v)
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
            self.default_w = float(desc["/MissingWidth"])
        base = BASE14_ALIAS.get(self.name, self.name)
        embedded = desc is not None and any(k in desc for k in ("/FontFile", "/FontFile2", "/FontFile3"))
        if not embedded and base in BASE14_ASC_DSC:
            self.asc, self.dsc = BASE14_ASC_DSC[base]
            self.metrics = "BASE14"
        elif desc is not None and float(desc.get("/Ascent", 0) or 0) > 0:
            self.asc, self.dsc = float(desc["/Ascent"]) / 1000.0, float(desc.get("/Descent", 0) or 0) / 1000.0
            self.metrics = "DESCRIPTOR"
        else:
            self.asc, self.dsc = 0.8, -0.2
            self.metrics = "DEFAULT"
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
           "drawn": []}

    def flush():
        r = out["run"]
        if r is not None:
            t = r["text"].strip()
            if t and r["box"] is not None:
                x0, y0, x1, y1 = r["box"]
                out["words"].append({"value": t, "x0": x0, "y0": H - y1, "x1": x1, "y1": H - y0,
                                     "dir": (round(r["dir"][0], 6), round(-r["dir"][1], 6))})
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
            L = math.hypot(trm[0], trm[1])
            d = (trm[0] / L, trm[1] / L) if L else (1.0, 0.0)
            visible = box[2] >= 0 and box[0] <= UW and box[3] >= 0 and box[1] <= UH
            ch = font.text(code)
            size_e = math.sqrt(abs(trm[0] * trm[3] - trm[1] * trm[2])) or 1e-9
            key = (id(font), round(size_e, 4), st["fill"])
            r = out["run"]
            if visible:
                join, space = False, False
                if r is not None and abs(d[0] * r["dir"][0] + d[1] * r["dir"][1]) > 0.999 and r["key"] == key:
                    dx_, dy_ = ox - r["pen"][0], oy - r["pen"][1]
                    along = (d[0] * dx_ + d[1] * dy_) / size_e
                    across = (-d[1] * dx_ + d[0] * dy_) / size_e
                    if abs(across) < 0.8:
                        if abs(along) < 0.15:
                            join = True
                        elif 0 < along < 0.8:
                            join = space = True
                if not join:
                    flush()
                    r = out["run"] = {"key": key, "text": "", "box": None, "dir": d, "pen": (ox, oy)}
                elif space and not r["text"].endswith(" ") and ch != " ":
                    r["text"] += " "
                r["text"] += ch
                b = r["box"]
                r["box"] = box if b is None else (min(b[0], box[0]), min(b[1], box[1]), max(b[2], box[2]),
                                                  max(b[3], box[3]))
            # pen advance in text space: w0 x size + Tc (+ Tw for a single-byte code 32), x Th
            sp = ts["tc"] + (ts["tw"] if (not font.cid and code == 32) else 0.0)
            tx = _f(_f(_f(adv * size) + _f(sp)) * th)
            ts["tm"] = _concat((1.0, 0.0, 0.0, 1.0, _f(tx), 0.0), ts["tm"])
            if r is not None and visible:
                r["pen"] = (qx, qy)
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
    words, segs = out["words"], out["segs"]
    has_img = bool(out["img"])
    state = "VECTOR" if (words or segs) else ("RASTER_ONLY" if has_img else "EMPTY")
    return {"page": page_no, "width_pt": W, "height_pt": H, "state": state, "words": words, "segments": segs,
            "has_image": has_img,
            "reader": {"policy": POLICY_ID, "library": "pypdf", "font_metrics": sorted(out["metrics"]),
                       "limits": sorted(out["limits"] | {"OPTIONAL_CONTENT_NOT_EVALUATED"})}}


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
                     "fill + stroke, TJ kerning, scan)"}
