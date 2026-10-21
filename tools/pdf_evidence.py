"""PDF EVIDENCE (M3) - typical-detail evidence from a drawing PDF: native text first, then the vector check, then
optional local OCR; written in the engine.source.detail_evidence schema.

    python3 -I tools/pdf_evidence.py extract --pdf SET.pdf --out DIR [--pages 13 14] [--dpi 300]
                                            [--redact REGEX ...] [--no-ocr]
    python3 -I tools/pdf_evidence.py check --evidence DIR/DETAIL_EVIDENCE.json

Per page:
    native text   the PDF text layer (pymupdf words), method NATIVE_TEXT - exact, no OCR
    vector        the number of vector paths: a page with paths but no text layer draws its text as glyphs, and only
                  OCR (or a person) can read it - recorded, never guessed
    OCR           tesseract (local binary, optional), on raster pages and on vector-glyph pages (paths > 20 x
                  words): the page rendered at --dpi, words with confidence and box (TSV, page segmentation 11). A
                  word that parses as a bar notation is read three more times from its own crop re-rendered from the
                  PDF at twice the resolution (segmentations 7, 8, 13). On a vector-glyph page every stroked glyph is
                  classed by shape and a page-wide OCR vote gives each class its character
                  (detail_evidence.glyph_votes); the token's glyphs then check the reads (glyph_check). A record is
                  OCR_UNREVIEWED when the reads agree with the glyphs (VECTOR_GLYPH_CONSENSUS), or, with no glyph
                  check, when all reads give the same unique parse; else OCR_REJECTED_*. The region above each
                  detail caption is re-read for tokens the page pass missed.

Every record keeps the page, the region in PDF points and in pixels, the raw text, the confidence, both reads and
the crop file name. Crops are written under DIR/crops (never committed). Owner / title-block / file-path text is
dropped before anything is recorded (detail_evidence.redact plus --redact patterns); only the count is kept. When the
OCR binary is absent the page is recorded as OCR_UNAVAILABLE and the manual-transcription pathway applies
(detail_evidence.manual_record, same schema).
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import shutil
import subprocess
import sys
import tempfile
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.source import detail_evidence as DE     # noqa: E402

POLICY_ID = "PDF_EVIDENCE_V1"
DETAIL_FAMILIES = ("GROUND_BEAM", "STRAP_BEAM", "BEAM", "LINTEL")


def ocr_version():
    if not shutil.which("tesseract"):
        return None
    r = subprocess.run(["tesseract", "--version"], capture_output=True, text=True)
    return (r.stdout or r.stderr).splitlines()[0].strip() if (r.stdout or r.stderr) else "tesseract"


def _render(pdf, page, dpi, clip_pt=None, out_png=None):
    """PNG bytes of a page (or a clip in points) - pymupdf when installed, else poppler's pdftoppm."""
    try:
        import pymupdf
        d = pymupdf.open(str(pdf))
        pix = d[page - 1].get_pixmap(dpi=dpi, clip=pymupdf.Rect(*clip_pt) if clip_pt else None)
        data = pix.tobytes("png")
    except ImportError:
        if not shutil.which("pdftoppm"):
            raise RuntimeError("neither pymupdf nor pdftoppm is available to render the PDF")
        args = ["pdftoppm", "-png", "-r", str(dpi), "-f", str(page), "-l", str(page), "-singlefile"]
        if clip_pt:
            k = dpi / 72.0
            x0, y0, x1, y1 = clip_pt
            args += ["-x", str(int(x0 * k)), "-y", str(int(y0 * k)), "-W", str(int((x1 - x0) * k)),
                     "-H", str(int((y1 - y0) * k))]
        with tempfile.TemporaryDirectory() as td:
            subprocess.run(args + [str(pdf), str(Path(td) / "p")], check=True, capture_output=True)
            data = (Path(td) / "p.png").read_bytes()
    if out_png:
        Path(out_png).parent.mkdir(parents=True, exist_ok=True)
        Path(out_png).write_bytes(data)
    return data


def _tesseract_tsv(png_bytes, psm):
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "in.png"
        p.write_bytes(png_bytes)
        r = subprocess.run(["tesseract", str(p), "-", "--psm", str(psm), "tsv"], capture_output=True, text=True)
    rows = list(csv.DictReader(io.StringIO(r.stdout), delimiter="\t", quoting=csv.QUOTE_NONE))
    return [x for x in rows if (x.get("text") or "").strip()]


def _native_words(pdf, page):
    try:
        import pymupdf
    except ImportError:
        return None, None, None
    d = pymupdf.open(str(pdf))
    pg = d[page - 1]
    words = pg.get_text("words")            # x0, y0, x1, y1, text, block, line, word (points, y down)
    try:
        n_paths = len(pg.get_drawings())
    except Exception:                       # noqa: BLE001 - a page whose paths cannot be listed: recorded as unknown
        n_paths = None
    return words, n_paths, len(pg.get_images(full=True))


def _bez(p, t):
    if len(p) == 2:
        return p[0][0] + (p[1][0] - p[0][0]) * t, p[0][1] + (p[1][1] - p[0][1]) * t
    (ax, ay), (bx, by), (cx, cy), (ex, ey) = p
    u = 1 - t
    return (u ** 3 * ax + 3 * u * u * t * bx + 3 * u * t * t * cx + t ** 3 * ex,
            u ** 3 * ay + 3 * u * u * t * by + 3 * u * t * t * cy + t ** 3 * ey)


def glyphs(pdf, page, *, max_pt=12.0, grid=12, jaccard=0.7):
    """the vector glyphs of a page (pymupdf): small stroked paths merged where they overlap (a 'Ø' is a circle and a
    slash), each rasterised to a grid x grid cell set normalised by its height and grouped into shape classes
    (Jaccard >= jaccard, same aspect). [{box (displayed page points), cls}] or None without pymupdf."""
    try:
        import pymupdf
    except ImportError:
        return None
    pg = pymupdf.open(str(pdf))[page - 1]
    R = pg.rotation_matrix
    paths = []
    for p in pg.get_drawings():
        r = pymupdf.Rect(p["rect"]) * R
        if r.width > max_pt or r.height > max_pt or p.get("fill") is not None or not p["items"]:
            continue
        segs = []
        for it in p["items"]:
            if it[0] in ("l", "c"):
                segs.append([tuple(pymupdf.Point(q) * R) for q in it[1:(3 if it[0] == "l" else 5)]])
            else:
                segs = None
                break
        if segs:
            paths.append({"r": (r.x0, r.y0, r.x1, r.y1), "segs": segs})
    par = list(range(len(paths)))

    def root(i):
        while par[i] != i:
            par[i] = par[par[i]]
            i = par[i]
        return i
    cell = defaultdict(list)
    for i, p in enumerate(paths):
        cell[(int(p["r"][0] // 10), int(p["r"][1] // 10))].append(i)
    for i, p in enumerate(paths):
        a = p["r"]
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for j in cell.get((int(a[0] // 10) + dx, int(a[1] // 10) + dy), []):
                    if j <= i:
                        continue
                    b = paths[j]["r"]
                    w, h = min(a[2], b[2]) - max(a[0], b[0]), min(a[3], b[3]) - max(a[1], b[1])
                    if w <= 0 or h <= 0:
                        continue
                    small = max(min((a[2] - a[0]) * (a[3] - a[1]), (b[2] - b[0]) * (b[3] - b[1])), 1e-6)
                    if w * h >= 0.5 * small:
                        par[root(i)] = root(j)
    groups = defaultdict(list)
    for i in range(len(paths)):
        groups[root(i)].append(paths[i])
    out, classes = [], []
    for ps in groups.values():
        x0 = min(p["r"][0] for p in ps)
        y0 = min(p["r"][1] for p in ps)
        x1 = max(p["r"][2] for p in ps)
        y1 = max(p["r"][3] for p in ps)
        H = max(y1 - y0, 1e-6)
        cells = frozenset((int((x - x0) / H * (grid - 1) + 0.5), int((y - y0) / H * (grid - 1) + 0.5))
                          for p in ps for sg in p["segs"] for k in range(13) for x, y in [_bez(sg, k / 12)])
        asp = round((x1 - x0) / H, 1)
        cls = next((c["id"] for c in classes if abs(c["asp"] - asp) <= 0.15 and
                    len(c["cells"] & cells) / len(c["cells"] | cells) >= jaccard), None)
        if cls is None:
            cls = len(classes)
            classes.append({"id": cls, "cells": cells, "asp": asp})
        out.append({"box": (x0, y0, x1, y1), "cls": cls})
    return out


def _glyphs_in(gl, box):
    x0, y0, x1, y1 = box
    pad = (y1 - y0) * 0.2
    sel = [g for g in gl if x0 - pad <= (g["box"][0] + g["box"][2]) / 2 <= x1 + pad and
           y0 - pad <= (g["box"][1] + g["box"][3]) / 2 <= y1 + pad]
    return [g["cls"] for g in sorted(sel, key=lambda g: g["box"][0])]


def _lines(words):
    """[(text, box, h)] per text line, from tokens [{text, box, line_key}]."""
    by = defaultdict(list)
    for w in words:
        by[w["line_key"]].append(w)
    out = []
    for ws in by.values():
        ws.sort(key=lambda w: w["box"][0])
        box = (min(w["box"][0] for w in ws), min(w["box"][1] for w in ws), max(w["box"][2] for w in ws),
               max(w["box"][3] for w in ws))
        out.append({"text": " ".join(w["text"] for w in ws), "box": box,
                    "h": sorted(w["box"][3] - w["box"][1] for w in ws)[len(ws) // 2]})
    return out


def captions(lines, extra_redact=()):
    """detail captions: a line naming a member family, merged with the lines just under it (subtitle, span condition,
    scale) and with lines on its own baseline to the right."""
    lines = sorted(lines, key=lambda r: (r["box"][1], r["box"][0]))
    used, out = set(), []
    for i, ln in enumerate(lines):
        if i in used or DE.redact(ln["text"], extra_redact) or DE.caption_of(ln["text"]) is None:
            continue
        box, txt, h = list(ln["box"]), [ln["text"]], ln["h"]
        used.add(i)
        grew = True
        while grew:
            grew = False
            for j, o in enumerate(lines):
                if j in used or DE.redact(o["text"], extra_redact):
                    continue
                ob = o["box"]
                below = box[3] - 0.3 * h <= ob[1] <= box[3] + 1.6 * h and ob[0] < box[2] and ob[2] > box[0]
                beside = abs(ob[1] - box[1]) <= 0.6 * h and 0 <= ob[0] - box[2] <= 3.0 * h
                same_row = abs(ob[3] - box[3]) <= 0.6 * h and 0 <= ob[0] - box[2] <= 3.0 * h
                if below or beside or same_row:
                    if DE.caption_of(o["text"]) is not None and DE.caption_of(o["text"])["family"] and below and \
                            o["text"].strip().upper().startswith(("GROUND", "BEAM", "LINTEL", "TYP", "DETAIL")):
                        continue                   # the next caption, not a subtitle
                    used.add(j)
                    txt.append(o["text"])
                    box = [min(box[0], ob[0]), min(box[1], ob[1]), max(box[2], ob[2]), max(box[3], ob[3])]
                    grew = True
        out.append({"text": " ".join(txt), "box": tuple(box)})
    return out


def extract(pdf, out_dir, *, pages=None, dpi=300, redact_patterns=(), use_ocr=True):
    pdf, out = Path(pdf), Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    sha = hashlib.sha256(pdf.read_bytes()).hexdigest()
    ver = ocr_version() if use_ocr else None
    try:
        import pymupdf
        n_pages = len(pymupdf.open(str(pdf)))
    except ImportError:
        n_pages = None
    pages = pages or list(range(1, (n_pages or 0) + 1))
    ev = {"schema": DE.SCHEMA, "policy": POLICY_ID, "document": {"file": pdf.name, "sha256": sha, "pages": n_pages},
          "engine": {"ocr": ver, "dpi": dpi, "second_read_dpi": dpi * 2, "psm_page": 11, "psm_token": [7, 8, 13],
                     "image_check": "VECTOR_GLYPH_CONSENSUS (vector-glyph pages), else UNANIMOUS_READS"},
          "redact_patterns": list(redact_patterns), "pages": [], "records": [], "captions": [], "details": [],
          "notes": []}
    k = 0
    for pno in pages:
        words, n_paths, n_img = _native_words(pdf, pno)
        prec = {"page": pno, "native_words": len(words or []), "vector_paths": n_paths, "images": n_img,
                "dropped_tokens": 0}
        toks = []
        for w in words or []:                     # 1. the text layer, exact
            toks.append({"text": w[4], "box": (w[0], w[1], w[2], w[3]), "box_px": None, "conf": 100.0,
                         "line_key": ("N", w[5], w[6]), "method": "NATIVE_TEXT"})
        methods = ["NATIVE_TEXT"] if words else []
        # 2. vector glyphs: a page that draws more than it writes is read by OCR as well (native words win where
        # both exist); without the OCR binary the page is OCR_UNAVAILABLE and goes to manual transcription
        glyph_page = (n_paths or 0) > 20 * max(len(words or []), 1)
        raster_page = not words and bool(n_img)          # a scanned / image-only page: OCR, no glyph check
        if (glyph_page or raster_page or words is None) and ver:
            methods.append("OCR_TESSERACT")
            png = _render(pdf, pno, dpi)
            k_pt = 72.0 / dpi
            nat = [t["box"] for t in toks]
            for r in _tesseract_tsv(png, 11):
                x, y, w_, h_ = (int(r[c]) for c in ("left", "top", "width", "height"))
                b = (x * k_pt, y * k_pt, (x + w_) * k_pt, (y + h_) * k_pt)
                if any(b[0] < n[2] and b[2] > n[0] and b[1] < n[3] and b[3] > n[1] for n in nat):
                    continue
                toks.append({"text": r["text"].strip(), "box": b, "box_px": (x, y, x + w_, y + h_),
                             "conf": float(r["conf"]), "line_key": ("O", r["block_num"], r["par_num"], r["line_num"]),
                             "method": "OCR_TESSERACT"})
        elif glyph_page or raster_page:
            methods.append("OCR_UNAVAILABLE")
        prec["method"] = "+".join(methods) or "NO_TEXT"
        prec["vector_glyph_page"] = glyph_page
        prec["raster_page"] = raster_page
        kept = []
        for t in toks:
            if DE.redact(t["text"], redact_patterns):
                prec["dropped_tokens"] += 1
                continue
            kept.append(t)
        prec["tokens"] = len(kept)
        # 3. the image check of a vector-glyph page: one shape is one character, so the OCR words of the whole page
        # vote for each glyph class; a token's read is then checked glyph by glyph
        gl = glyphs(pdf, pno) if glyph_page and ver and words is not None else None
        gchars, ncls = {}, {}
        if gl:
            obs = []
            for t in kept:
                if t["method"] != "OCR_TESSERACT":
                    continue
                cl = _glyphs_in(gl, t["box"])
                ncls[id(t)] = cl
                if len(cl) == len(t["text"]):
                    obs += list(zip(cl, t["text"]))
            gchars = DE.glyph_votes(obs)
            prec["glyphs"] = {"n": len(gl), "classes": len({g["cls"] for g in gl}), "voting_words":
                              sum(1 for t in kept if len(ncls.get(id(t), ())) == len(t["text"])),
                              "known_classes": sum(1 for v in gchars.values() if v)}
        ev["pages"].append(prec)
        state = {"k": k}

        def process(t, cl):
            p1 = DE.parse_notation(t["text"])
            if p1["state"] == "UNPARSED":
                return None
            state["k"] += 1
            rid = f"EV-{state['k']:04d}"
            rec = {"record_id": rid, "page": pno, "region_pt": [round(v, 2) for v in t["box"]],
                   "region_px": list(t["box_px"]) if t["box_px"] else None, "dpi": t.get("dpi"),
                   "method": t["method"], "raw_text": t["text"], "confidence": t["conf"], "reads": [],
                   "parsed": p1, "crop": None, "found_by": t.get("found_by", "PAGE_READ")}
            if t["method"] == "NATIVE_TEXT":
                rec["state"] = "NATIVE_TEXT" if p1["state"] == "PARSED" else "OCR_REJECTED_AMBIGUOUS"
                return rec
            x0, y0, x1, y1 = t["box"]
            pad = (y1 - y0) * 0.35
            crop = out / "crops" / f"p{pno:02d}_{rid}.png"
            png2 = _render(pdf, pno, dpi * 2, clip_pt=(x0 - pad, y0 - pad, x1 + pad, y1 + pad), out_png=crop)
            reads = [{"text": t["text"], "psm": t.get("psm", 11), "dpi": t.get("dpi"), "conf": t["conf"],
                      "parsed": p1}]
            for psm in (7, 8, 13):               # independent re-reads of the token's own crop
                r2 = " ".join(x["text"].strip() for x in _tesseract_tsv(png2, psm))
                red = DE.redact(r2, redact_patterns)
                reads.append({"text": "" if red else r2, "psm": psm, "dpi": dpi * 2,
                              "parsed": DE.parse_notation(r2) if not red else {"state": "UNPARSED"}})
            for rd in reads:
                rd["glyph_check"] = DE.glyph_check(rd["text"], cl, gchars) if cl else "UNCHECKED"
            rec.update(reads=reads, glyph_classes=cl, crop=str(crop.relative_to(out)))
            ok = [rd for rd in reads if rd["glyph_check"] == "VERIFIED"]
            parsed = [rd["parsed"] for rd in reads]
            if ok and all(DE.agree(ok[0]["parsed"], rd["parsed"]) for rd in ok):
                rec.update(state="OCR_UNREVIEWED", parsed=ok[0]["parsed"], validation="VECTOR_GLYPH_CONSENSUS")
            elif any(x["state"] == "AMBIGUOUS" for x in parsed):
                rec["state"] = "OCR_REJECTED_AMBIGUOUS"
            elif all(DE.agree(parsed[0], x) for x in parsed[1:]) and not any(
                    rd["glyph_check"] == "CONTRADICTED" for rd in reads):
                rec.update(state="OCR_UNREVIEWED",
                           validation="UNANIMOUS_READS" if not gl else "UNANIMOUS_READS_GLYPHS_UNCHECKED")
            elif any(x["state"] == "UNPARSED" for x in parsed):
                rec["state"] = "OCR_REJECTED_UNPARSED"
            else:
                rec["state"] = "OCR_REJECTED_DISAGREE"
            return rec

        recs = [r for t in kept for r in [process(t, ncls.get(id(t)))] if r]
        for ln in _lines(kept):                  # typical-detail notes (a printed plain-concrete layer), cited only
            nt = DE.note_of(ln["text"])
            if nt and not DE.redact(ln["text"], redact_patterns):
                ev["notes"].append(dict(nt, note_id=f"P{pno:02d}N{len(ev['notes']) + 1:02d}", page=pno,
                                        region_pt=[round(v, 2) for v in ln["box"]], text=ln["text"],
                                        method="OCR_TESSERACT" if ln["box"] and glyph_page else "NATIVE_TEXT",
                                        state="OCR_UNREVIEWED"))
        caps = []
        for n, c in enumerate(captions(_lines(kept), redact_patterns), 1):
            cid = f"P{pno:02d}C{n:02d}"
            caps.append({"caption_id": cid, "box": c["box"], "caption": DE.caption_of(c["text"])})
            ev["captions"].append({"caption_id": cid, "page": pno, "region_pt": [round(v, 2) for v in c["box"]],
                                   "text": c["text"], "caption": DE.caption_of(c["text"])})
        # 4. recall: the drawing above each member caption (a detail is drawn over its title) is read again at the
        # crop resolution; a notation the page read missed goes through the same checks
        if ver and (glyph_page or raster_page):
            for c in caps:
                if (c["caption"] or {}).get("family") not in DETAIL_FAMILIES:
                    continue
                x0, y0, x1, y1 = c["box"]
                w = x1 - x0
                reg = (x0 - 0.25 * w, max(y0 - 1.2 * w, 0.0), x1 + 0.25 * w, y0)
                png3 = _render(pdf, pno, dpi * 2, clip_pt=reg)
                kk = 72.0 / (dpi * 2)
                for r in _tesseract_tsv(png3, 11):
                    txt = r["text"].strip()
                    if DE.redact(txt, redact_patterns) or DE.parse_notation(txt)["state"] == "UNPARSED":
                        continue
                    x, y, w_, h_ = (int(r[q]) for q in ("left", "top", "width", "height"))
                    b = (reg[0] + x * kk, reg[1] + y * kk, reg[0] + (x + w_) * kk, reg[1] + (y + h_) * kk)
                    if any(b[0] < q["region_pt"][2] and b[2] > q["region_pt"][0] and b[1] < q["region_pt"][3] and
                           b[3] > q["region_pt"][1] for q in recs):
                        continue
                    t = {"text": txt, "box": b, "box_px": None, "conf": float(r["conf"]), "method": "OCR_TESSERACT",
                         "psm": 11, "dpi": dpi * 2, "found_by": "DETAIL_REGION_READ"}
                    rr = process(t, _glyphs_in(gl, b) if gl else None)
                    if rr:
                        recs.append(rr)
        k = state["k"]
        ev["records"] += recs
        accepted = [{"record_id": r["record_id"], "box": tuple(r["region_pt"]), "parsed": r["parsed"]}
                    for r in recs if r["state"] in DE.USABLE]
        rejected = [{"record_id": r["record_id"], "box": tuple(r["region_pt"])} for r in recs
                    if r["state"] not in DE.USABLE]
        ev["details"] += [dict(d, page=pno) for d in DE.assemble(accepted, caps, rejected=rejected)
                          if d["bars"] or d.get("rejected_records")]
    problems = DE.validate(ev)
    ev["validation"] = problems
    (out / "DETAIL_EVIDENCE.json").write_text(json.dumps(ev, indent=1, ensure_ascii=False), encoding="utf-8")
    return ev


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    e = sub.add_parser("extract")
    e.add_argument("--pdf", required=True)
    e.add_argument("--out", required=True)
    e.add_argument("--pages", type=int, nargs="*")
    e.add_argument("--dpi", type=int, default=300)
    e.add_argument("--redact", nargs="*", default=[])
    e.add_argument("--no-ocr", action="store_true")
    c = sub.add_parser("check")
    c.add_argument("--evidence", required=True)
    a = ap.parse_args(argv)
    if a.cmd == "extract":
        ev = extract(a.pdf, a.out, pages=a.pages, dpi=a.dpi, redact_patterns=a.redact, use_ocr=not a.no_ocr)
        st = defaultdict(int)
        for r in ev["records"]:
            st[r["state"]] += 1
        print(json.dumps({"pages": [{k: v for k, v in p.items()} for p in ev["pages"]], "records": dict(st),
                          "captions": len(ev["captions"]), "details": [
                              {"detail_id": d["detail_id"], "condition": (d["caption"] or {}).get("condition"),
                               "state": d["state"], "bars": len(d["bars"])} for d in ev["details"]],
                          "validation": ev["validation"]}, indent=1))
        return 0 if not ev["validation"] else 2
    ev = json.loads(Path(a.evidence).read_text(encoding="utf-8"))
    bad = DE.validate(ev)
    print(json.dumps({"valid": not bad, "problems": bad}, indent=1))
    return 0 if not bad else 2


if __name__ == "__main__":
    raise SystemExit(main())
