"""Overlays, drawn from stored trace coordinates and from nothing else.

A feature is never redrawn afterwards because the text said it exists. If
a claim has no geometry it does not appear on the drawing - it appears in
the register as TRACE_NOT_ESTABLISHED, which is the honest outcome and
the one the whole schema exists to make possible.

Line STYLE plus a short label carries the meaning, never colour alone, so
the overlay survives greyscale printing and colour-blind review.

    python3 -m research.a21_trace_sufficiency_01.overlays
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from research.a21_trace_sufficiency_01 import protocol as P
from research.a21_trace_sufficiency_01 import source_sufficiency as S

OUT = Path("data/experiments/A21_TRACE_SUFFICIENCY_01")
OVERLAYS = OUT / "overlays"

FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

# style carries the meaning; colour is a second, redundant channel
STYLE = {
    "WALL_SEGMENT":       {"dash": None,     "width": 5, "rgb": (0, 90, 200)},
    "OPEN_EDGE":          {"dash": (14, 14), "width": 5, "rgb": (200, 90, 0)},
    "DOOR":               {"dash": (4, 8),   "width": 4, "rgb": (0, 140, 60)},
    "WINDOW":             {"dash": (4, 8),   "width": 4, "rgb": (0, 140, 60)},
    "GLAZING":            {"dash": (2, 6),   "width": 4, "rgb": (0, 140, 60)},
    "COLUMN":             {"dash": (10, 4),  "width": 5, "rgb": (130, 0, 160)},
    "STAIR":              {"dash": (18, 6),  "width": 4, "rgb": (0, 90, 200)},
    "PARAPET":            {"dash": None,     "width": 5, "rgb": (0, 90, 200)},
    "BALUSTRADE":         {"dash": (6, 6),   "width": 5, "rgb": (200, 90, 0)},
    "PRINTED_DIMENSION":  {"dash": (8, 4),   "width": 3, "rgb": (190, 0, 0)},
    "LEVEL_MARK":         {"dash": (8, 4),   "width": 3, "rgb": (190, 0, 0)},
    "HEIGHT_DIMENSION":   {"dash": (8, 4),   "width": 3, "rgb": (190, 0, 0)},
    "SECTION_REFERENCE":  {"dash": (20, 8),  "width": 3, "rgb": (90, 90, 90)},
    "ELEVATION_REFERENCE": {"dash": (20, 8), "width": 3, "rgb": (90, 90, 90)},
    "ROOM_IDENTITY":      {"dash": (3, 7),   "width": 3, "rgb": (90, 90, 90)},
    "UNRESOLVED_FEATURE": {"dash": (2, 10),  "width": 5, "rgb": (200, 0, 120)},
}
DEFAULT_STYLE = {"dash": (5, 5), "width": 4, "rgb": (0, 0, 0)}

STATUS_MARK = {
    "TRACE_ESTABLISHED": "",
    "TRACE_PROVISIONAL": " ?",
    "TRACE_AMBIGUOUS": " ??",
    "TRACE_NOT_ESTABLISHED": " x",
}


def _dashed(d, pts, dash, width, rgb):
    if not dash:
        d.line(pts, fill=rgb, width=width, joint="curve")
        return
    on, off = dash
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        dx, dy = x1 - x0, y1 - y0
        ln = max(1e-6, (dx * dx + dy * dy) ** 0.5)
        ux, uy = dx / ln, dy / ln
        t = 0.0
        while t < ln:
            t2 = min(ln, t + on)
            d.line([(x0 + ux * t, y0 + uy * t), (x0 + ux * t2, y0 + uy * t2)],
                   fill=rgb, width=width)
            t = t2 + off


def _label(d, xy, text, rgb, font):
    x, y = xy
    box = d.textbbox((x, y), text, font=font)
    pad = 4
    d.rectangle([box[0] - pad, box[1] - pad, box[2] + pad, box[3] + pad],
                fill=(255, 255, 255), outline=rgb, width=2)
    d.text((x, y), text, fill=rgb, font=font)


def _draw_one(d, geom, g, dash, width, rgb):
    """Draw one geometry and return a label anchor for it."""
    if geom.endswith("_BBOX"):
        x0, y0, x1, y1 = g
        pts = [(x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0)]
        anchor = (x0, max(0, y0 - 34))
    elif geom.endswith("_POINT"):
        x, y = g
        r = 16
        pts = [(x - r, y - r), (x + r, y - r), (x + r, y + r),
               (x - r, y + r), (x - r, y - r)]
        anchor = (x + r + 4, y - r)
    elif geom.endswith("_POLYGON"):
        pts = [tuple(q) for q in g] + [tuple(g[0])]
        anchor = (min(q[0] for q in g), max(0, min(q[1] for q in g) - 34))
    else:
        pts = [tuple(q) for q in g]
        anchor = (pts[0][0], max(0, pts[0][1] - 34))
    _dashed(d, pts, dash, width, rgb)
    return anchor


def render(register: dict) -> dict:
    """Draw from stored coordinates. Nothing is redrawn from prose."""
    from research.a21_trace_sufficiency_01 import visual_trace as VT
    idx = json.loads((OUT / "SHEET_INDEX.json").read_text("utf-8"))["SHEETS"]
    OVERLAYS.mkdir(parents=True, exist_ok=True)
    font = ImageFont.truetype(FONT, 26)
    small = ImageFont.truetype(FONT, 20)

    by_sheet, undrawable = {}, []
    for t in register["TRACES"]:
        fields = [g for g in VT.geometry_fields_for(t["CLAIM_TYPE"])
                  if t.get(g)]
        if not fields:
            undrawable.append({
                "TRACE_ID": t.get("TRACE_ID"),
                "CLAIM_TYPE": t.get("CLAIM_TYPE"),
                "VISUAL_TRACE_STATUS": t.get("VISUAL_TRACE_STATUS"),
                "WHY_NOT_DRAWN": ("the trace carries no geometry, so there "
                                  "is nowhere honest to draw it")})
            continue
        by_sheet.setdefault((t["CASE_ID"], t["SHEET_ID"]), []).append(
            (t, fields))

    made = []
    for (case_id, sheet_id), traces in sorted(by_sheet.items()):
        rec = idx[sheet_id]
        img = Image.open(S.INDEX_BOX / rec["PREPARED_FILE"]).convert("RGB")
        d = ImageDraw.Draw(img)
        for t, fields in traces:
            st = STYLE.get(t["CLAIM_TYPE"], DEFAULT_STYLE)
            anchor = None
            for i, geom in enumerate(fields):
                # an extension line is thinner and finer-dashed: it is
                # evidence about WHERE a dimension terminates, not the
                # claim itself, and it must not outshout the claim
                ext = geom.startswith("EXTENSION_LINE")
                a = _draw_one(d, geom, t[geom],
                              (3, 5) if ext else st["dash"],
                              max(2, st["width"] - 2) if ext else st["width"],
                              st["rgb"])
                if i == 0:
                    anchor = a
            _label(d, anchor,
                   t["TRACE_ID"] + STATUS_MARK.get(
                       t.get("VISUAL_TRACE_STATUS"), ""),
                   st["rgb"], font)

        legend = sorted({t["CLAIM_TYPE"] for t, _ in traces})
        ly = 14
        d.rectangle([10, 10, 520, 24 + 30 * (len(legend) + 2)],
                    fill=(255, 255, 255), outline=(0, 0, 0), width=2)
        d.text((22, ly), f"{case_id}  {sheet_id}", fill=(0, 0, 0), font=small)
        ly += 30
        d.text((22, ly), "? provisional   ?? ambiguous   x not established",
               fill=(0, 0, 0), font=small)
        ly += 30
        for ct in legend:
            st = STYLE.get(ct, DEFAULT_STYLE)
            _dashed(d, [(22, ly + 10), (110, ly + 10)], st["dash"],
                    st["width"], st["rgb"])
            d.text((120, ly), ct, fill=st["rgb"], font=small)
            ly += 30

        name = f"{case_id}__{sheet_id}.png"
        img.save(OVERLAYS / name)
        made.append({"FILE": name, "CASE_ID": case_id, "SHEET_ID": sheet_id,
                     "TRACES_DRAWN": len(traces),
                     "GEOMETRIES_DRAWN": sum(len(f) for _, f in traces),
                     "SHA256": hashlib.sha256(
                         (OVERLAYS / name).read_bytes()).hexdigest()})

    body = {
        "PHASE_ID": P.PHASE_ID,
        "ARTIFACT": "OVERLAY_IMAGES",
        "OVERLAY_RULES": list(P.OVERLAY_RULES),
        "DERIVED_FROM": "TRACE_REGISTER.json, coordinates only",
        "NOTHING_WAS_REDRAWN_FROM_PROSE": True,
        "EXTENSION_LINES_ARE_DRAWN_TOO": (
            "a dimension is drawn as its text box, its dimension line and "
            "both extension lines, because the extension lines are what "
            "show which faces it actually runs between"),
        "IMAGES": made,
        "TRACES_WITH_NO_GEOMETRY_NOT_DRAWN": undrawable,
    }
    p2 = OUT / "OVERLAY_INDEX.json"
    p2.write_text(json.dumps(body, indent=2, ensure_ascii=False) + "\n",
                  encoding="utf-8")
    return {"images": len(made), "undrawable": len(undrawable),
            "SHA256": hashlib.sha256(p2.read_bytes()).hexdigest()}


if __name__ == "__main__":
    reg = json.loads((OUT / "TRACE_REGISTER.json").read_text("utf-8"))
    print(json.dumps(render(reg), indent=2))
