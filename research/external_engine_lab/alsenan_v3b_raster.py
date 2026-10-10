"""ALSENAN V3b - raster evidence lane for the architectural PDF elevations / sections (numpy / scipy adapter).

The twelve architectural PDF pages are 4672 x 6624 px raster scans of 1:100 sheets. This lane:

  1. loads each page image (from the hash-addressed PDF, rotated upright);
  2. calibrates the sheet scale by fitting the PRINTED level chain of the sheet (read once, below, from the printed
     dimensions: ±0.00 ground, +1.00 GF, +5.50 1F, +9.70 2F, +13.90 roof, +14.40 parapet) to the horizontal lines
     detected on the sheet; >= 3 matched levels (>= 2 independent printed dimensions) agreeing within 1 % are required
     (engine.source.raster_evidence.calibrate), else the sheet is NOT_SCALABLE;
  3. detects opening rectangles (enclosed white regions inside the drawing, rectangularity >= 0.85) and measures the
     outer frame around each; reports width / height / sill / head in cm at the calibrated scale, the floor band from
     the sill level, and grade SCALED;
  4. carries the printed values read on the sheets (domes, pool cut, curved glazing, fence) as PRINTED claims with their
     pixel boxes.

Nothing here chooses a quantity: the lab layer matches raster openings to plan openings (exact DXF widths) and the
width check of raster_evidence decides whether a height may be used.
"""

from __future__ import annotations

import glob
import hashlib
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage as ndi

from engine.source import raster_evidence as RE

ROOT = Path(__file__).resolve().parents[2]
PDF_A = "80b6a80428990db4dfa86aa343ed2c7cb429709459d564f0dac92362480a9b00"   # P7757 arch pages 01-06
PDF_B = "281a0c3f8c1cdd8f2a78528513b66d14ba4793e981e2d8059423faf6e6162f99"   # P7757 arch pages 07-12
LEVELS_CM = {"±0.00": 0, "+1.00": 100, "+5.50": 550, "+9.70": 970, "+13.90": 1390, "+14.40": 1440}
FLOOR_BANDS = [("GF", 0, 550), ("1F", 550, 970), ("2F", 970, 1390), ("ROOF", 1390, 1500)]
PX_TOL = 4.0                                      # line thickness / hatch edge on a short dimension
NOMINAL_PX_PER_CM = 4672 / 297.0 / 10.0          # A3 sheet width 297 mm across 4672 px, scale 1:100 (corroboration)
# sheet ref -> (pdf, page index, kind, printed levels drawn on the sheet as chain nodes)
SHEETS = {
    "ARCH-P06-SE-ELEV": (PDF_A, 5, "ELEVATION", ["±0.00", "+1.00", "+5.50", "+9.70", "+13.90", "+14.40"]),
    "ARCH-P07-SW-ELEV": (PDF_B, 0, "ELEVATION", ["±0.00", "+1.00", "+5.50", "+9.70", "+13.90", "+14.40"]),
    "ARCH-P08-NW-ELEV": (PDF_B, 1, "ELEVATION", ["±0.00", "+1.00", "+5.50", "+9.70", "+13.90", "+14.40"]),
    "ARCH-P09-NE-ELEV": (PDF_B, 2, "ELEVATION", ["±0.00", "+1.00", "+5.50", "+9.70", "+13.90", "+14.40"]),
    "ARCH-P10-SECTION-AA": (PDF_B, 3, "SECTION", ["±0.00", "+1.00", "+5.50", "+9.70", "+13.90", "+14.40"]),
    "ARCH-P11-SECTION-BB": (PDF_B, 4, "SECTION", ["±0.00", "+1.00", "+5.50", "+9.70", "+13.90", "+14.40"]),
}
# printed values read on the sheets (text + the located dimension), pixel boxes on the upright full-resolution page
PRINTED = [
    {"sheet": "ARCH-P08-NW-ELEV", "quantity": "CURVED_GLAZING_HEIGHT", "value_cm": 430, "box_px": [3000, 2400, 4400, 3500],
     "text": "430 (+ 20 head) over 269 wide", "binds": "MASTER BEDROOM CURVED GLAZING"},
    {"sheet": "ARCH-P08-NW-ELEV", "quantity": "SUNKEN_ELEMENT_DEPTH", "value_cm": 115, "box_px": [3700, 3300, 4300, 3800],
     "text": "115 pit + 70 step below the +0.15 deck", "binds": "POOL CANDIDATE (to be matched to the p.3 pool outline)"},
    {"sheet": "ARCH-P06-SE-ELEV", "quantity": "DOME_SPAN", "value_cm": 441, "box_px": [2600, 850, 3500, 1250],
     "text": "441 span / 215 rise", "binds": "TOWER ROOF DOME"},
    {"sheet": "ARCH-P06-SE-ELEV", "quantity": "DOME_RISE", "value_cm": 215, "box_px": [2600, 850, 3500, 1250],
     "text": "215", "binds": "TOWER ROOF DOME"},
    {"sheet": "ARCH-P08-NW-ELEV", "quantity": "DOME_RISE", "value_cm": 172, "box_px": [2600, 1450, 3400, 1900],
     "text": "172", "binds": "TERRACE DOME (2F)"},
    {"sheet": "ARCH-P12-FENCE", "quantity": "FENCE_HEIGHT", "value_cm": 265, "box_px": [4400, 1700, 5300, 2300],
     "text": "265 = 215 + 50", "binds": "BOUNDARY WALL (fence section)"},
    {"sheet": "ARCH-P12-FENCE", "quantity": "FENCE_FRONT_RUN", "value_cm": 1499, "box_px": [1400, 1300, 3900, 1800],
     "text": "580 + 250 + 81 + 195 + 115 + 195 + 83", "binds": "FRONT FENCE RUN (plan 1:100)"},
]
DOME_COUNT_EVIDENCE = {"value": 3, "sheets": ["ARCH-P11-SECTION-BB", "ARCH-P06-SE-ELEV", "ARCH-P07-SW-ELEV", "ARCH-P09-NE-ELEV"],
                       "text": "two domes on the 2F terrace (+9.70) and one on the tower roof (+13.90)"}


def _pdf(sha):
    return glob.glob(str(ROOT / "data/inputs/by_sha256" / f"{sha}*.pdf"))[0]


def sheet_sha(ref):
    return SHEETS[ref][0] if ref in SHEETS else PDF_B


def load(ref) -> np.ndarray:
    import pymupdf
    pdf, page, _, _ = SHEETS[ref]
    d = pymupdf.open(_pdf(pdf))
    x = d.extract_image(d[page].get_images()[0][0])
    im = Image.open(__import__("io").BytesIO(x["image"])).convert("L").rotate(90, expand=True)
    return np.array(im)


def h_rows(dark, min_run=60, x_lo=0, x_hi=None):
    """Rows holding a horizontal dark run >= min_run px (merged within 2 px): [(y, longest_run, x_start)]."""
    x_hi = x_hi or dark.shape[1]
    sub = dark[:, x_lo:x_hi].astype(np.int8)
    out = []
    for y in range(sub.shape[0]):
        d = np.diff(np.concatenate([[0], sub[y], [0]]))
        s, e = np.where(d == 1)[0], np.where(d == -1)[0]
        if len(s):
            L = (e - s).max()
            if L >= min_run:
                out.append((y, int(L), int(s[(e - s).argmax()]) + x_lo))
    merged = []
    for r in out:
        if merged and r[0] - merged[-1][-1][0] <= 2:
            merged[-1].append(r)
        else:
            merged.append([r])
    return [(int(round(np.mean([t[0] for t in g]))), max(t[1] for t in g), min(t[2] for t in g)) for g in merged]


def calibrate(ref, img=None) -> dict:
    """Fit the printed level chain to horizontal line rows: y = y0 - s * level_cm."""
    img = load(ref) if img is None else img
    dark = img < 150
    rows = [r[0] for r in h_rows(dark, min_run=80)]
    levels = [LEVELS_CM[k] for k in SHEETS[ref][3]]
    best = None
    lo, hi = NOMINAL_PX_PER_CM * 0.97, NOMINAL_PX_PER_CM * 1.03
    for yg in rows:                                   # candidate ground row
        for yt in rows:                               # candidate top-of-chain row (+14.40)
            if yt >= yg:
                continue
            s = (yg - yt) / float(levels[-1] - levels[0])
            if not (lo <= s <= hi):
                continue
            matched = []
            for L in levels:
                y = yg - s * L
                near = min(rows, key=lambda r: abs(r - y))
                if abs(near - y) <= 4:
                    matched.append((L, near))
            if best is None or len(matched) > len(best[2]) or (len(matched) == len(best[2]) and s < best[1]):
                best = (yg, s, matched)
    if best is None or len(best[2]) < 3:
        return {"sheet": ref, "state": RE.NOT_SCALABLE, "why": "fewer than 3 printed levels matched to drawn lines"}
    yg, _, matched = best
    g = next(m for m in matched if m[0] == 0) if any(m[0] == 0 for m in matched) else None
    if g is None:
        return {"sheet": ref, "state": RE.NOT_SCALABLE, "why": "ground level (±0.00) not matched"}
    obs = [{"ref": f"0 -> {L} cm", "printed_cm": L, "px": float(g[1] - y)} for L, y in matched if L > 0]
    cal = RE.calibrate(obs, nominal_px_per_cm=NOMINAL_PX_PER_CM, tol=0.01, px_tol=PX_TOL)
    cal.update(sheet=ref, ground_row=int(g[1]), matched_levels=[[L, int(y)] for L, y in matched])
    return cal


def _frame(dark, y0, y1, x0, x1, max_px=30):
    """Outer frame around a hole bbox: walk outward from each side's midpoint across dark pixels."""
    H, W = dark.shape
    ym, xm = (y0 + y1) // 2, (x0 + x1) // 2

    def walk(y, x, dy, dx):
        k, seen = 0, 0
        while k < max_px:
            yy, xx = y + dy * (k + 1), x + dx * (k + 1)
            if not (0 <= yy < H and 0 <= xx < W):
                break
            if dark[yy, xx]:
                seen = k + 1
            elif k - seen >= 3:
                break
            k += 1
        return seen
    return (y0 - walk(y0, xm, -1, 0), y1 + walk(y1 - 1, xm, 1, 0), x0 - walk(ym, x0, 0, -1), x1 + walk(ym, x1 - 1, 0, 1))


def openings(ref, cal, img=None) -> list:
    if cal.get("state") != RE.CALIBRATED:
        return []
    img = load(ref) if img is None else img
    dark = img < 160
    white = ~ndi.binary_dilation(dark, iterations=1)
    lab, _ = ndi.label(white)
    s = cal["px_per_cm"]
    out = []
    for i, sl in enumerate(ndi.find_objects(lab)):
        if sl is None:
            continue
        h, w = sl[0].stop - sl[0].start, sl[1].stop - sl[1].start
        if not (40 * s < w < 800 * s and 40 * s < h < 500 * s):
            continue
        rect = float((lab[sl] == i + 1).sum()) / (w * h)
        if rect < 0.85:
            continue
        y0, y1, x0, x1 = _frame(dark, sl[0].start, sl[0].stop, sl[1].start, sl[1].stop)
        sill = (cal["ground_row"] - y1) / s
        head = (cal["ground_row"] - y0) / s
        fl = next((f for f, a, b in FLOOR_BANDS if a - 20 <= sill < b - 20), None)
        out.append({"sheet": ref, "box_px": [int(x0), int(y0), int(x1), int(y1)],
                    "inner_w_cm": w / s, "inner_h_cm": h / s, "w_cm": (x1 - x0) / s, "h_cm": (y1 - y0) / s,
                    "sill_cm": sill, "head_cm": head, "floor": fl, "rectangularity": rect, "grade": RE.SCALED,
                    "uncertainty_cm": 3.0 / s + cal["worst_rel_dev"] * (y1 - y0) / s})
    out += composites(out, cal)
    return sorted(out, key=lambda o: (o["box_px"][1], o["box_px"][0], o.get("composite", False)))


def composites(ops, cal, gap_px=12):
    """Panes separated only by mullions / transoms form one opening: boxes whose frames touch (<= gap_px) and that
    share a side alignment are merged (union-find); every merged group of >= 2 panes is added as a composite opening."""
    n = len(ops)
    parent = list(range(n))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
    for i in range(n):
        a = ops[i]["box_px"]
        for j in range(i + 1, n):
            b = ops[j]["box_px"]
            if ops[i]["sheet"] != ops[j]["sheet"]:
                continue
            ox = min(a[2], b[2]) - max(a[0], b[0])
            oy = min(a[3], b[3]) - max(a[1], b[1])
            touch_h = ox > -gap_px and oy > 0.8 * min(a[3] - a[1], b[3] - b[1])   # side by side, same band
            touch_v = oy > -gap_px and ox > 0.8 * min(a[2] - a[0], b[2] - b[0])   # stacked, same columns
            if touch_h or touch_v:
                parent[find(i)] = find(j)
    groups = {}
    for i in range(n):
        groups.setdefault(find(i), []).append(i)
    s = cal["px_per_cm"]
    out = []
    for g in groups.values():
        if len(g) < 2:
            continue
        x0 = min(ops[i]["box_px"][0] for i in g)
        y0 = min(ops[i]["box_px"][1] for i in g)
        x1 = max(ops[i]["box_px"][2] for i in g)
        y1 = max(ops[i]["box_px"][3] for i in g)
        sill, head = (cal["ground_row"] - y1) / s, (cal["ground_row"] - y0) / s
        fl = next((f for f, a, b in FLOOR_BANDS if a - 20 <= sill < b - 20), None)
        out.append({"sheet": ops[g[0]]["sheet"], "box_px": [x0, y0, x1, y1], "w_cm": (x1 - x0) / s, "h_cm": (y1 - y0) / s,
                    "sill_cm": sill, "head_cm": head, "floor": fl, "composite": True, "panes": len(g), "grade": RE.SCALED,
                    "uncertainty_cm": 3.0 / s + cal["worst_rel_dev"] * (y1 - y0) / s})
    return out


def run() -> dict:
    sheets, ops = {}, []
    for ref in SHEETS:
        img = load(ref)
        cal = calibrate(ref, img)
        sheets[ref] = {k: cal.get(k) for k in ("state", "why", "px_per_cm", "worst_rel_dev", "nominal_rel_dev", "ground_row",
                                                "matched_levels", "observations")}
        sheets[ref]["sha256_pdf"] = SHEETS[ref][0]
        sheets[ref]["image_sha256"] = hashlib.sha256(img.tobytes()).hexdigest()
        ops += openings(ref, cal, img)
    claims = [RE.claim(sheet_sha256=sheet_sha(p["sheet"]), sheet_ref=p["sheet"], box_px=p["box_px"], quantity=p["quantity"],
                       value_cm=p["value_cm"], grade=RE.PRINTED, evidence=p["text"]) | {"binds": p["binds"]} for p in PRINTED]
    return {"policy": RE.policy_record(), "sheets": sheets, "raster_openings": ops, "printed_claims": claims,
            "dome_count": DOME_COUNT_EVIDENCE, "nominal_px_per_cm": NOMINAL_PX_PER_CM}
