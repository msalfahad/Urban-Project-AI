"""PDF_VECTOR_EVIDENCE_V1 - deterministic evidence from a drawing page whose text is vector glyphs or raster.

Three independent channels for one crop of one page, none of them an AI reading:

    render_crop(pdf, page, bbox, dpi)  the rendered crop + the sha256 of its pixel samples (the image a QS opens)
    ocr(png, lang, psm)                tesseract text of that crop (a deterministic machine reader; optional binary)
    bar_dots(...) / section_rects(...) PDF vector geometry: filled bar dots grouped into rows, closed section
                                       outlines measured in points and converted with a printed scale

The page box is the DISPLAYED (rotated) page box; vector items are read in unrotated space and mapped back.
pymupdf only; project-agnostic.
"""

from __future__ import annotations

import hashlib
import shutil
import subprocess
from pathlib import Path

POLICY_ID = "PDF_VECTOR_EVIDENCE_V1"
PT_MM = 25.4 / 72.0


def _doc(pdf):
    import pymupdf
    return pymupdf.open(str(pdf))


def render_crop(pdf, page: int, bbox, dpi: int = 200, out_png=None) -> dict:
    """Render the displayed-page box `bbox` (points) of 1-based `page`; the hash covers the raw pixel samples."""
    import pymupdf
    d = _doc(pdf)
    pix = d[page - 1].get_pixmap(dpi=dpi, clip=pymupdf.Rect(*bbox))
    h = hashlib.sha256(pix.samples).hexdigest()
    if out_png is not None:
        Path(out_png).parent.mkdir(parents=True, exist_ok=True)
        pix.save(str(out_png))
    return {"page": page, "bbox_pt": [round(v, 2) for v in bbox], "dpi": dpi, "width_px": pix.width,
            "height_px": pix.height, "crop_hash": h}


def ocr_available() -> bool:
    return shutil.which("tesseract") is not None


def ocr_engine_version() -> str | None:
    if not ocr_available():
        return None
    r = subprocess.run(["tesseract", "--version"], capture_output=True, text=True)
    return (r.stdout or r.stderr).splitlines()[0].strip()


def ocr(png, lang: str = "eng", psm: int = 11) -> str | None:
    """tesseract text of a rendered crop, or None when the binary is absent (never a silent empty string)."""
    if not ocr_available():
        return None
    r = subprocess.run(["tesseract", str(png), "-", "-l", lang, "--psm", str(psm)], capture_output=True, text=True)
    return r.stdout


def _items(page_obj, bbox):
    import pymupdf
    box = pymupdf.Rect(*bbox) * page_obj.derotation_matrix
    return [x for x in page_obj.get_drawings() if box.contains(x["rect"])], page_obj.rotation_matrix


def bar_dots(pdf, page: int, bbox, *, max_dot_pt=4.5, join_pt=2.6, row_tol_pt=2.2) -> dict:
    """Filled bar dots: small filled paths (a dot is often drawn as several quarter fills) clustered by centre, then
    grouped into rows of equal displayed y. Returns the dot centres and the per-row counts (top row first)."""
    d = _doc(pdf)
    p = d[page - 1]
    items, rot = _items(p, bbox)
    cs = []
    for x in items:
        if x.get("fill") is None:
            continue
        r = x["rect"] * rot
        if r.width > max_dot_pt or r.height > max_dot_pt:
            continue
        cs.append(((r.x0 + r.x1) / 2, (r.y0 + r.y1) / 2))
    dots = []
    for c in sorted(cs):
        for g in dots:
            if abs(g["x"] - c[0]) <= join_pt and abs(g["y"] - c[1]) <= join_pt:
                g["n"] += 1
                g["x"] += (c[0] - g["x"]) / g["n"]
                g["y"] += (c[1] - g["y"]) / g["n"]
                break
        else:
            dots.append({"x": c[0], "y": c[1], "n": 1})
    rows = []
    for dt in sorted(dots, key=lambda q: q["y"]):
        if rows and abs(rows[-1]["y"] - dt["y"]) <= row_tol_pt:
            rows[-1]["dots"].append(dt)
            rows[-1]["y"] = sum(q["y"] for q in rows[-1]["dots"]) / len(rows[-1]["dots"])
        else:
            rows.append({"y": dt["y"], "dots": [dt]})
    return {"dot_count": len(dots), "rows": [{"y_pt": round(r["y"], 2), "count": len(r["dots"])} for r in rows],
            "dots": [[round(q["x"], 2), round(q["y"], 2)] for q in dots]}


def section_rects(pdf, page: int, bbox, *, stroke=(0.6, 0.8), min_len_pt=20.0, tol_pt=1.5) -> list:
    """Closed axis-aligned rectangles formed by long straight strokes of the outline pen width: two verticals with the
    same y-extent joined by two horizontals at those ends. Width / height in points, largest first."""
    d = _doc(pdf)
    p = d[page - 1]
    items, rot = _items(p, bbox)
    V, H = [], []
    for x in items:
        w = x.get("width") or 0.0
        if not (stroke[0] <= w <= stroke[1]):
            continue
        for it in x["items"]:
            if it[0] != "l":
                continue
            a, b = it[1] * rot, it[2] * rot
            if abs(a.x - b.x) < 0.2 and abs(a.y - b.y) >= min_len_pt:
                V.append((a.x, min(a.y, b.y), max(a.y, b.y)))
            elif abs(a.y - b.y) < 0.2 and abs(a.x - b.x) >= min_len_pt:
                H.append((a.y, min(a.x, b.x), max(a.x, b.x)))
    out = []
    for i, v1 in enumerate(V):
        for v2 in V[i + 1:]:
            if abs(v1[1] - v2[1]) > tol_pt or abs(v1[2] - v2[2]) > tol_pt or abs(v1[0] - v2[0]) < min_len_pt / 2:
                continue
            x0, x1 = sorted((v1[0], v2[0]))
            ends = [y for y in (v1[1], v1[2]) if any(abs(h[0] - y) <= tol_pt and h[1] <= x0 + tol_pt and
                                                    h[2] >= x1 - tol_pt for h in H)]
            if len(ends) == 2:
                out.append({"x0": round(x0, 2), "y0": round(v1[1], 2), "w_pt": round(x1 - x0, 2),
                            "h_pt": round(v1[2] - v1[1], 2)})
    uniq = []
    for r in sorted(out, key=lambda r: -(r["w_pt"] * r["h_pt"])):
        if not any(abs(r["w_pt"] - u["w_pt"]) < tol_pt and abs(r["h_pt"] - u["h_pt"]) < tol_pt and
                   abs(r["x0"] - u["x0"]) < tol_pt for u in uniq):
            uniq.append(r)
    return uniq


def pt_to_mm(pt: float, scale: float) -> float:
    """Paper points -> real millimetres at a printed scale 1:scale (the sheet must be at its printed size)."""
    return pt * PT_MM * scale


def horizontal_rules(pdf, page: int, bbox, *, min_len_pt=40.0) -> list:
    """y of long horizontal strokes (table rules), top first - used to count table rows deterministically."""
    d = _doc(pdf)
    p = d[page - 1]
    items, rot = _items(p, bbox)
    ys = []
    for x in items:
        for it in x["items"]:
            if it[0] == "l":
                a, b = it[1] * rot, it[2] * rot
                if abs(a.y - b.y) < 0.2 and abs(a.x - b.x) >= min_len_pt:
                    ys.append(round(a.y, 1))
    out = []
    for y in sorted(ys):
        if not out or y - out[-1] > 1.0:
            out.append(y)
    return out


def lines(pdf, page: int, bbox, *, stroke=(0.0, 9.9), min_len_pt=10.0, orient="H") -> list:
    """Straight strokes of a pen-width range: orient 'H' (horizontal) or 'V' (vertical), displayed coordinates."""
    d = _doc(pdf)
    p = d[page - 1]
    items, rot = _items(p, bbox)
    out = set()
    for x in items:
        w = x.get("width") or 0.0
        if not (stroke[0] <= w <= stroke[1]):
            continue
        for it in x["items"]:
            if it[0] != "l":
                continue
            a, b = it[1] * rot, it[2] * rot
            if orient == "H" and abs(a.y - b.y) < 0.2 and abs(a.x - b.x) >= min_len_pt:
                out.add((round(a.y, 1), round(min(a.x, b.x), 1), round(max(a.x, b.x), 1), round(w, 2)))
            elif orient == "V" and abs(a.x - b.x) < 0.2 and abs(a.y - b.y) >= min_len_pt:
                out.add((round(a.x, 1), round(min(a.y, b.y), 1), round(max(a.y, b.y), 1), round(w, 2)))
    key = ("y_pt", "x0_pt", "x1_pt", "width") if orient == "H" else ("x_pt", "y0_pt", "y1_pt", "width")
    return [dict(zip(key, t)) for t in sorted(out)]
