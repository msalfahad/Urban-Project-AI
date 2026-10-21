"""R8.6A — owner-review images (research lab; nothing here feeds a quantity).

1. QORTUBA_SECOND_FLOOR_PLAN_OWNER_REVIEW.png - the four 'SECOND FLOOR PLAN' layouts as they sit in the supplied
   DXF's model space (K2 geometry, drawn as stored, no clean-up), PLAN_VARIANT_1..3 and the bottom-most
   PLAN_VARIANT_4_SELECTED_CANDIDATE, then the candidate region alone with its id, bounds, the title text, the
   labels near it, and the entities that differ from the DWG the six rows were measured on.
2. QORTUBA_Q14_CEILING_OWNER_REVIEW.png - the ten Q-14 spaces (rectangles of the R8.6 canonical proof) over the
   K1 geometry of the measured DWG, with the one ceiling question.

    python3 research/external_engine_lab/r8_6a_owner_images.py <work_dir> <out_dir>

<work_dir> holds qortuba_k2.pkl and qortuba_index.json from the R8.6A intake (hash-addressed working copies).
"""

from __future__ import annotations

import json
import math
import pickle
import re
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

REG = ROOT / "tests/r8_6a/registers"
PROOF = ROOT / "tests/r8_6/registers/QORTUBA_ROUND1_PROOF.json"
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
QUESTION_REGION = "Is this the correct Qortuba second-floor plan view that Urban should use for quantity measurement?"
QUESTION_Q14 = ("In these ten second-floor spaces, is there any ceiling void, stair opening, shaft, open-to-above area or "
                "change of ceiling (bulkhead / drop) that is NOT the same as the floor area shown?")
INK, GREY, SEL, ADD, MISS, ROOMC = (40, 40, 40), (165, 165, 165), (0, 110, 200), (230, 120, 0), (210, 0, 0), (0, 140, 70)


def font(size, bold=False):
    try:
        return ImageFont.truetype(FONT_B if bold else FONT, size)
    except OSError:
        return ImageFont.load_default()


class View:
    """world (x, y) -> pixel inside a box; y up in the drawing, down in the image."""

    def __init__(self, world, box):
        (x0, y0, x1, y1), (px0, py0, px1, py1) = world, box
        self.world, self.box = world, box
        self.s = min((px1 - px0) / (x1 - x0), (py1 - py0) / (y1 - y0))
        self.ox = px0 + ((px1 - px0) - (x1 - x0) * self.s) / 2
        self.oy = py0 + ((py1 - py0) - (y1 - y0) * self.s) / 2

    def __call__(self, p):
        x0, y0, x1, y1 = self.world
        return (self.ox + (p[0] - x0) * self.s, self.oy + (y1 - p[1]) * self.s)

    def inside(self, p):
        x0, y0, x1, y1 = self.world
        return x0 <= p[0] <= x1 and y0 <= p[1] <= y1


def arc_points(a, n=16):
    cx, cy = a.center
    t0 = math.atan2(a.start[1] - cy, a.start[0] - cx)
    t1 = math.atan2(a.end[1] - cy, a.end[0] - cx)
    if a.direction == "CW":
        t0, t1 = t1, t0
    while t1 <= t0:
        t1 += 2 * math.pi
    return [(cx + a.radius * math.cos(t0 + (t1 - t0) * i / n), cy + a.radius * math.sin(t0 + (t1 - t0) * i / n))
            for i in range(n + 1)]


def ellipse_points(e, n=24):
    t0, t1 = (0.0, 2 * math.pi) if e.full else (e.t0, e.t1)
    while t1 <= t0:
        t1 += 2 * math.pi
    return [(e.center[0] + math.cos(t) * e.axis_u[0] + math.sin(t) * e.axis_v[0],
             e.center[1] + math.cos(t) * e.axis_u[1] + math.sin(t) * e.axis_v[1])
            for t in (t0 + (t1 - t0) * i / n for i in range(n + 1))]


def draw_geometry(d, v, rg, colour, width=1, pick=None):
    """Every realised primitive whose points fall in the view; pick(lineage) -> colour override or None."""
    def col(lin):
        return (pick(lin) if pick else None) or colour
    for s in rg.segments:
        if v.inside(s.a) or v.inside(s.b):
            d.line([v(s.a), v(s.b)], fill=col(s.lineage), width=width)
    for a in rg.arcs:
        if v.inside(a.center) or v.inside(a.start):
            d.line([v(p) for p in arc_points(a)], fill=col(a.lineage), width=width)
    for c in rg.circles:
        if v.inside(c.center):
            (x, y), r = v(c.center), c.radius * v.s
            d.ellipse([x - r, y - r, x + r, y + r], outline=col(c.lineage), width=width)
    for e in rg.elliptical_arcs:
        if v.inside(e.center):
            d.line([v(p) for p in ellipse_points(e)], fill=col(e.lineage), width=width)


def plain(text):
    """MTEXT formatting codes removed for display only (the register keeps the stored string)."""
    t = re.sub(r"\\[A-Za-z][^;\\{}]*;", "", text or "")
    t = t.replace("\\P", " ").replace("{", "").replace("}", "")
    return re.sub(r"\s+", " ", t).strip()


def qortuba_region_png(work: Path, out: Path):
    q = json.loads((REG / "QORTUBA_ROUND1_DXF_RESULTS.json").read_text())
    pv, rev = q["plan_variants"], q["revision_evidence"]
    rid, (bx0, by0, bx1, by1) = pv["tracked_dwg_region"]["region_id"], pv["tracked_dwg_region"]["bounds"]
    index = json.loads((work / "qortuba_index.json").read_text())
    rg = pickle.load(open(work / "qortuba_k2.pkl", "rb"))["rg"]
    labels = {v["label_handle"]: v for v in pv["variants"]}
    lx = [v["label_position"][0] for v in pv["variants"]]
    ly = sorted(v["label_position"][1] for v in pv["variants"])
    stack = (min(lx) - 3200, ly[0] - 500, max(lx) + 2200, ly[-1] + 3600)
    handseed = 0x84E          # HANDSEED of the measured DWG 2ec3a9c8 (D1 header); higher handles were added later
    added = {e["5"] for e in index["entities"] if int(e["5"], 16) > handseed}

    W, H = 2600, 1900
    img = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(img)
    d.text((30, 18), "QORTUBA - SECOND FLOOR PLAN - OWNER REVIEW (R8.6A)", fill=INK, font=font(34, True))
    d.text((30, 62), "Source: supplied DXF sha256 df0e1d69...f315 ('qurtoba villah.dxf'), model space, drawn as stored. "
                     "Nothing was cleaned, exploded or moved.", fill=INK, font=font(19))

    # left: the whole stack of four layouts
    left = View(stack, (30, 110, 980, 1700))
    draw_geometry(d, left, rg, GREY)
    for v in pv["variants"]:
        i = sorted(ly).index(v["label_position"][1])
        y_lo = ly[i] - 300
        y_hi = (ly[i + 1] - 300) if i + 1 < len(ly) else stack[3]
        sel = v["variant_id"].endswith("SELECTED_CANDIDATE")
        a, b = left((stack[0] + 60, y_hi - 60)), left((stack[2] - 60, y_lo + 60))
        d.rectangle([a, b], outline=SEL if sel else (120, 120, 120), width=6 if sel else 2)
        name = v["variant_id"].replace("_SELECTED_CANDIDATE", "  <- SELECTED (bottom-most)")
        d.text((a[0] + 8, a[1] + 6), name, fill=SEL if sel else INK, font=font(20, sel))
        d.text((a[0] + 8, a[1] + 30), f"title text handle {v['label_handle']}  |  {v['entities']} top-level entities",
               fill=INK, font=font(15))
    d.text((30, 1710), "Left: all four 'SECOND FLOOR PLAN' layouts, top (1) to bottom (4).", fill=INK, font=font(18))
    d.text((30, 1736), "Everything outside the four boxes is OUTSIDE_SELECTED_MEASUREMENT_REGION (kept as evidence).",
           fill=INK, font=font(18))

    # right: the selected candidate alone
    m = 250
    right = View((bx0 - m, by0 - m - 150, bx1 + m, by1 + m), (1020, 110, W - 30, 1500))
    in_region = lambda p: bx0 - m <= p[0] <= bx1 + m and by0 - m - 150 <= p[1] <= by1 + m  # noqa: E731

    def pick(lin):
        h = (lin.instance_path[0].split(":")[1] if lin.instance_path else lin.source_handle).upper()
        return ADD if h in added else None
    draw_geometry(d, right, rg, INK, pick=pick)
    d.rectangle([right((bx0, by1)), right((bx1, by0))], outline=SEL, width=5)
    lab = labels[pv["tracked_dwg_region"]["contains_label_handle"]]
    d.text(right(lab["label_position"]), "SECOND FLOOR PLAN", fill=SEL, font=font(26, True), anchor="lb")
    nearby = [e for e in index["entities"] if e["type"] in ("TEXT", "MTEXT") and e["5"] != lab["label_handle"]
              and in_region((float(e["10"]), float(e["20"])))]
    for e in nearby:
        t = plain(e.get("1"))
        if t:
            d.text(right((float(e["10"]), float(e["20"]))), t[:40], fill=(90, 40, 140), font=font(13), anchor="lb")
    y = 1515
    for line, f, c in (
            (f"Region id: {rid}", font(22, True), SEL),
            (f"Bounds (drawing units): x {bx0:.2f} .. {bx1:.2f}   y {by0:.2f} .. {by1:.2f}", font(19), INK),
            (f"Title text: 'SECOND FLOOR PLAN' (handle {lab['label_handle']});  nearby labels shown in purple: "
             f"{len(nearby)}", font(19), INK),
            (f"Orange = drawn after the DWG the six rows were measured on (2ec3a9c8): {rev['entities_added_inside_region']} "
             f"entities added here; {rev['source_entities_missing_from_dxf']} measured entities are not in this DXF.",
             font(19), ADD)):
        d.text((1020, y), line, fill=c, font=f)
        y += 32
    d.rectangle([30, 1790, W - 30, 1880], outline=INK, width=2)
    d.text((50, 1800), "QUESTION FOR MOHAMMAD:  " + QUESTION_REGION, fill=INK, font=font(24, True))
    d.text((50, 1842), "Answer:   YES   /   NO   /   NOT SURE", fill=SEL, font=font(24, True))
    p = out / "QORTUBA_SECOND_FLOOR_PLAN_OWNER_REVIEW.png"
    img.save(p, optimize=True)
    return p, {"region_id": rid, "bounds": [bx0, by0, bx1, by1], "nearby_labels": len(nearby),
               "title_handle": lab["label_handle"], "question": QUESTION_REGION, "choices": ["YES", "NO", "NOT SURE"]}


def q14_png(out: Path):
    from engine.source.cad import kernel, libredwg_map as L
    proof = json.loads(PROOF.read_text())
    row = next(r for r in proof["rows"] if r["row_id"].startswith("Q-14"))
    rooms = {r["room_id"]: r for r in proof["rooms"]}
    dec = json.loads((ROOT / "data/runs/cad_convert/QORTUBA_ARCHITECTURAL.json").read_text(encoding="utf-8", errors="replace"))
    rg = kernel.realise(L.to_document(dec))
    rects = [(rid["room_id"], r) for rid in row["rooms"] for r in rooms[rid["room_id"]]["canonical_native_geometry"]["rectangles_native"]]
    xs = [v for _, r in rects for v in (r[0], r[2])]
    ys = [v for _, r in rects for v in (r[1], r[3])]
    m = 120
    W, H = 2700, 1700
    palette = [(0, 140, 70), (200, 60, 60), (40, 90, 200), (210, 140, 0), (140, 60, 170), (0, 150, 160),
               (180, 90, 20), (90, 120, 30), (220, 70, 160), (90, 90, 90)]
    img = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(img)
    d.text((30, 18), "QORTUBA - Q-14 CEILING (gypsum decor) - OWNER REVIEW (R8.6A)", fill=INK, font=font(32, True))
    d.text((30, 60), "Geometry: DWG 2ec3a9c8 (the measured source), K1 realisation. Coloured = the ten spaces whose floor "
                     "area Q-14 uses as ceiling area (138.51 m2 preview); one colour per space.", fill=INK, font=font(18))
    v = View((min(xs) - m, min(ys) - m, max(xs) + m, max(ys) + m), (30, 100, 1880, 1420))
    draw_geometry(d, v, rg, GREY)
    colour = {x["room_id"]: palette[i] for i, x in enumerate(row["formula_inputs"])}
    number = {x["room_id"]: i for i, x in enumerate(row["formula_inputs"], 1)}
    over = Image.new("RGBA", img.size, (0, 0, 0, 0))
    od = ImageDraw.Draw(over)
    for rid, r in rects:
        od.rectangle([v((r[0], r[3])), v((r[2], r[1]))], fill=colour[rid] + (60,), outline=colour[rid] + (255,), width=3)
    img = Image.alpha_composite(img.convert("RGBA"), over).convert("RGB")
    d = ImageDraw.Draw(img)
    for rid, r in rects:                       # every rectangle carries its space number
        d.text(v(((r[0] + r[2]) / 2, (r[1] + r[3]) / 2)), str(number[rid]), fill=colour[rid], font=font(26, True),
               anchor="mm")
    lx, ly = 1920, 120
    d.text((lx, ly), "Spaces in Q-14", fill=INK, font=font(24, True))
    for i, x in enumerate(row["formula_inputs"], 1):
        yy = ly + 20 + 44 * i
        d.rectangle([lx, yy, lx + 30, yy + 30], fill=palette[i - 1])
        d.text((lx + 42, yy + 2), f"{i}. {x['room']}  {x['preview_area_m2']} m2", fill=INK, font=font(19))
    d.text((lx, ly + 20 + 44 * 11 + 10), "Total: 138.51 m2 (preview)", fill=INK, font=font(20, True))
    d.text((lx, ly + 20 + 44 * 12 + 10), "A space may be several rectangles;", fill=INK, font=font(16))
    d.text((lx, ly + 20 + 44 * 12 + 34), "every rectangle shows its space number.", fill=INK, font=font(16))
    y = 1430
    d.text((30, y), "Q-14 today: ceiling area = floor area of each space; VOID / STAIR_OPENING / SHAFT / OPEN_TO_ABOVE are "
                    "recorded as absent WITHOUT being tested (there is no reflected ceiling plan).", fill=INK, font=font(18))
    d.rectangle([30, 1480, W - 30, 1680], outline=INK, width=2)
    words, line, lines = QUESTION_Q14.split(), "", []
    for w_ in words:
        if len(line) + len(w_) > 150:
            lines.append(line)
            line = ""
        line = (line + " " + w_).strip()
    lines.append(line)
    d.text((50, 1490), "QUESTION FOR MOHAMMAD:", fill=INK, font=font(22, True))
    for k, ln in enumerate(lines):
        d.text((50, 1522 + 30 * k), ln, fill=INK, font=font(21))
    d.text((50, 1630), "Answer:   NO (ceiling = floor area)   /   YES (name the spaces)   /   NOT SURE",
           fill=ROOMC, font=font(22, True))
    p = out / "QORTUBA_Q14_CEILING_OWNER_REVIEW.png"
    img.save(p, optimize=True)
    return p, {"spaces": [[i, x["room_id"], x["room"], x["preview_area_m2"]] for i, x in enumerate(row["formula_inputs"], 1)],
               "question": QUESTION_Q14, "choices": ["NO", "YES", "NOT SURE"]}


def main(work, out):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    a = qortuba_region_png(Path(work), out)
    b = q14_png(out)
    print(a[0], a[1]["nearby_labels"], b[0], len(b[1]["spaces"]))
    return a, b


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
