"""One large crop per unresolved opening, drawn so a person can recognise the place and answer in one word.

The whole-plan image was too small to point at.  These are five separate crops, each centred on one opening, each
showing enough surrounding wall to read the room, with the adjacent rooms named and the questioned opening marked by a
single large red number and its measured clear width.

Nothing here infers what the opening is.  The gap is drawn where the frozen registers put it - the band's own centreline
and thickness, and the jamb line the opening register names - and the question below the image lists the choices without
ranking them.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from research.qs_wall_treatment_01 import protocol as PR
from research.qs_wall_treatment_01.pa08.qortuba.boq import opening_source_search as OS

OUT = Path(PR.OUT_DIR) / "pa08_qortuba_boq" / "owner_question_crops"
QS = Path(PR.OUT_DIR) / "pa08_qortuba_qs01"
R1 = Path(PR.OUT_DIR) / "pa08_qortuba_r1"
R3 = Path(PR.OUT_DIR) / "pa08_qortuba_r3"
DWG_JSON = Path("data/runs/cad_convert/QORTUBA_ARCHITECTURAL.json")

DWG_UNITS_TO_MM = 10.0          # INSUNITS 5: the drawing is authored in centimetres
CHOICES = "Door  /  Open passage  /  Window  /  Sliding door  /  Not an opening  /  Other?"
# US-16: this one is settled as an open passage, so it is never offered the type choice again.  What is still open is
# the vertical condition, and that is the only thing this crop asks.
PASSAGE_CHOICES = "Open to the ceiling  /  Wall above it - what is the opening height?"
ASK = {"TYPE": ("What is this opening?", CHOICES),
       "PASSAGE_HEIGHT": ("Open passage - is it open to the ceiling?", PASSAGE_CHOICES)}

NAVY = (31, 58, 95)
RED = (192, 57, 43)
INK = (51, 71, 91)
ROOMFILL = (238, 243, 249)
GREY = (150, 160, 172)


def reg(folder, name):
    return json.loads((folder / f"{name}.json").read_text("utf-8"))


def _font(sz, bold=False):
    for p in ("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else
              "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
              "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"):
        try:
            return ImageFont.truetype(p, sz)
        except OSError:
            continue
    return ImageFont.load_default()


# ---------------------------------------------------------------------------- where each jamb line actually is
def jamb_points():
    """Resolve the jamb object ids the opening register names back to coordinates in the DWG decode.

    The id is the entity handle plus, for one span of a polyline, a hash of that span's own end points.  Reading it back
    is a lookup in the source, not a new measurement: no coordinate is moved, created or rounded.
    """
    d = json.loads(DWG_JSON.read_text("utf-8"))
    out = {}
    for o in d["OBJECTS"]:
        h = o.get("handle")
        h = h[-1] if isinstance(h, list) and h else None
        if h is None or not o.get("entity"):
            continue
        if o["entity"] == "LINE":
            a, b = o["start"][:2], o["end"][:2]
            out[f"CAD-{h}"] = ((a[0] * DWG_UNITS_TO_MM, a[1] * DWG_UNITS_TO_MM),
                               (b[0] * DWG_UNITS_TO_MM, b[1] * DWG_UNITS_TO_MM))
        elif o["entity"] == "LWPOLYLINE":
            pts = [(p[0], p[1]) if isinstance(p, (list, tuple)) else (p["x"], p["y"]) for p in o.get("points", [])]
            for i in range(len(pts) - 1):
                a, b = pts[i], pts[i + 1]
                key = f"{a[0]:.4f},{a[1]:.4f}->{b[0]:.4f},{b[1]:.4f}"
                sub = hashlib.sha256(key.encode("utf-8")).hexdigest()[:8]
                out[f"CAD-{h}.{sub}"] = ((a[0] * DWG_UNITS_TO_MM, a[1] * DWG_UNITS_TO_MM),
                                         (b[0] * DWG_UNITS_TO_MM, b[1] * DWG_UNITS_TO_MM))
    return out


def bands():
    mb = {b["BAND_ID"]: b for b in reg(R1, "PA08_QORTUBA_R1_MATERIAL_BAND_REGISTER")["ROWS"]}
    out = {}
    for w in reg(QS, "QORTUBA_QS01_BLOCK_WALL_TAKEOFF")["ROWS"]:
        c = mb[w["BAND_ID"]].get("CENTERLINE_IF_DERIVED")
        if not c or c.get("KIND") != "LINE":
            continue
        a = round(c["ANGLE_DEG"], 1)
        if a not in (0.0, 90.0):
            continue
        e0, e1 = c["EXTENT_MM"]
        axis = "H" if a == 0.0 else "V"
        off = c["AXIS_OFFSET_MM"] if axis == "H" else -c["AXIS_OFFSET_MM"]
        out[w["WALL_ID"]] = {"AXIS": axis, "OFF": off, "E0": min(e0, e1), "E1": max(e0, e1),
                             "T": w["THICKNESS_MM"], "ROOMS": sorted({r for r in w["ROOM_SIDE_A"] + w["ROOM_SIDE_B"]
                                                                      if r in OS.APARTMENT_ROOMS})}
    return out


def gap_interval(site, band, jp):
    """The stretch of wall line the opening occupies, from the jamb the register names and the recorded span."""
    pts = None
    for k in (site["JAMB_A"] or []) + (site["JAMB_B"] or []):
        if k in jp:
            pts = jp[k]
            break
    span = site["SPAN_MM"]
    if pts is None:
        mid = (band["E0"] + band["E1"]) / 2
        return mid - span / 2, mid + span / 2, "the band centre: the jamb line is inside a block and was not resolved"
    (ax, ay), (bx, by) = pts
    along = ((ax + bx) / 2) if band["AXIS"] == "H" else ((ay + by) / 2)
    # an end gap runs outward from the band, an interior gap runs inward
    if site["IS_END_GAP"]:
        out_dir = -1.0 if abs(along - band["E0"]) < abs(along - band["E1"]) else 1.0
    else:
        out_dir = 1.0 if abs(along - band["E0"]) < abs(along - band["E1"]) else -1.0
    lo, hi = sorted((along, along + out_dir * span))
    return lo, hi, "from the jamb line the register names, along the wall"


# ---------------------------------------------------------------------------- drawing
def _rooms():
    rows = reg(R3, "PA08_QORTUBA_R3_FLOOR_MEASUREMENT_REGION_REGISTER")["ROWS"]
    floors = {}
    for f in reg(QS, "QORTUBA_QS01_FLOOR_CALCULATIONS")["ROWS"]:
        floors.setdefault(f["ROOM"], []).append(f["METHOD_A_CAD_POLYGON_AREA_M2"])
    out = []
    for r in rows:
        rects = [(x["X_MM"][0], x["Y_MM"][0], x["X_MM"][1], x["Y_MM"][1]) for x in r["FORMULA"]["RECTANGLES"]]
        area = r["AREA_M2"]["VALUE"]
        out.append({"ROOM": r["ROOM"], "RECTS": rects, "AREA": area,
                    "LABEL": OS.friendly(r["ROOM"].split(" /")[0], area)})
    return out


def draw_crop(n, q, band, lo, hi, rooms, allbands, hint=None, half_w=4200, half_h=2900, px=1600):
    heading, choices = ASK[q["ASKS_FOR"]]
    ax = band["AXIS"]
    cx = (lo + hi) / 2 if ax == "H" else band["OFF"]
    cy = band["OFF"] if ax == "H" else (lo + hi) / 2
    x0, x1 = cx - half_w, cx + half_w
    y0, y1 = cy - half_h, cy + half_h
    # half the frame is empty when the opening sits on the edge of the apartment: there is nothing drawn beyond the
    # outer wall.  The window is pulled back to the drawing that is actually there, keeping a margin and keeping the
    # questioned gap inside it.  This trims blank paper, it does not move any geometry.
    ys = [z for b in allbands.values() for z in
          ((b["OFF"] - b["T"], b["OFF"] + b["T"]) if b["AXIS"] == "H" else (b["E0"], b["E1"]))
          if (b["E0"] < x1 and b["E1"] > x0) if b["AXIS"] == "H" or x0 < b["OFF"] < x1]
    ys += [z for r in rooms for (rx0, ry0, rx1, ry1) in r["RECTS"] if rx0 < x1 and rx1 > x0 for z in (ry0, ry1)]
    if ys:
        pad = 700
        y0 = max(y0, min(min(ys) - pad, (lo if ax == "V" else cy) - 900))
        y1 = min(y1, max(max(ys) + pad, (hi if ax == "V" else cy) + 900))
    sc = px / (x1 - x0)
    W, H = px, int((y1 - y0) * sc)
    top, bot = 86, ((202 if len(hint) > 110 else 176) if hint else 150)
    img = Image.new("RGB", (W, H + top + bot), "white")
    d = ImageDraw.Draw(img)

    def P(x, y):
        return (int((x - x0) * sc), int(top + H - (y - y0) * sc))

    for r in rooms:
        for (rx0, ry0, rx1, ry1) in r["RECTS"]:
            if rx1 < x0 or rx0 > x1 or ry1 < y0 or ry0 > y1:
                continue
            d.rectangle([P(rx0, ry1), P(rx1, ry0)], fill=ROOMFILL)
    for wid, b in allbands.items():
        t = max(3, int(b["T"] * sc))
        if b["AXIS"] == "H":
            d.line([P(b["E0"], b["OFF"]), P(b["E1"], b["OFF"])], fill=NAVY, width=t)
        else:
            d.line([P(b["OFF"], b["E0"]), P(b["OFF"], b["E1"])], fill=NAVY, width=t)
    # the room names, placed in the largest rectangle of each room inside the window
    f_room = _font(22, True)
    for r in rooms:
        vis = [t for t in r["RECTS"] if not (t[2] < x0 or t[0] > x1 or t[3] < y0 or t[1] > y1)]
        if not vis:
            continue
        t = max(vis, key=lambda z: (z[2] - z[0]) * (z[3] - z[1]))
        mx, my = P((t[0] + t[2]) / 2, (t[1] + t[3]) / 2)
        lab = r["LABEL"]
        w = d.textlength(lab, font=f_room)
        # a label that runs off the crop tells the owner nothing, so it is nudged back inside the frame
        mx = min(max(mx, int(w / 2) + 14), W - int(w / 2) - 14)
        my = min(max(my, top + 24), top + H - 24)
        d.rectangle([mx - w / 2 - 7, my - 17, mx + w / 2 + 7, my + 17], fill=(255, 255, 255))
        d.text((mx - w / 2, my - 13), lab, fill=INK, font=f_room)
    # the questioned opening: erase the wall over the gap, then mark it
    t = max(5, int(band["T"] * sc))
    if band["AXIS"] == "H":
        d.line([P(lo, band["OFF"]), P(hi, band["OFF"])], fill="white", width=t + 2)
        d.line([P(lo, band["OFF"]), P(hi, band["OFF"])], fill=RED, width=max(7, t))
        mx, my = P((lo + hi) / 2, band["OFF"])
    else:
        d.line([P(band["OFF"], lo), P(band["OFF"], hi)], fill="white", width=t + 2)
        d.line([P(band["OFF"], lo), P(band["OFF"], hi)], fill=RED, width=max(7, t))
        mx, my = P(band["OFF"], (lo + hi) / 2)
    R = 46
    d.ellipse([mx - R, my - R, mx + R, my + R], fill=RED, outline="white", width=5)
    f_num = _font(58, True)
    nw = d.textlength(str(n), font=f_num)
    d.text((mx - nw / 2, my - 36), str(n), fill="white", font=f_num)
    f_w = _font(26, True)
    wl = f"clear width {q['WIDTH_M']:.3f} m"
    ww = d.textlength(wl, font=f_w)
    d.rectangle([mx - ww / 2 - 10, my + R + 8, mx + ww / 2 + 10, my + R + 48], fill=RED)
    d.text((mx - ww / 2, my + R + 15), wl, fill="white", font=f_w)

    d.rectangle([0, 0, W, top - 1], fill=NAVY)
    d.text((22, 14), f"OPENING #{n}" + ("  -  OPEN PASSAGE" if q["ASKS_FOR"] == "PASSAGE_HEIGHT" else ""),
           fill="white", font=_font(34, True))
    d.text((22, 54), q["LOCATION"][0].upper() + q["LOCATION"][1:], fill=(210, 222, 236), font=_font(21))
    d.rectangle([0, top + H, W, top + H + bot], fill=(245, 247, 250))
    d.text((22, top + H + 16), heading, fill=INK, font=_font(28, True))
    d.text((22, top + H + 58), choices, fill=NAVY, font=_font(27, True))
    d.text((22, top + H + 104),
           "Measured clear width "
           f"{q['WIDTH_M']:.3f} m.  Height not in the drawing set.  "
           + ("Type confirmed by the owner: open passage.  No height has been assumed."
              if q["ASKS_FOR"] == "PASSAGE_HEIGHT" else "No type has been assumed."),
           fill=GREY, font=_font(19))
    # the hint goes last, over the footer band rather than under it, wrapped so no word runs off the page
    if hint:
        f_h = _font(19, True)
        line, y = "", top + H + 132
        for word in hint.split():
            trial = (line + " " + word).strip()
            if d.textlength(trial, font=f_h) > W - 44 and line:
                d.text((22, y), line, fill=RED, font=f_h)
                line, y = word, y + 24
            else:
                line = trial
        if line:
            d.text((22, y), line, fill=RED, font=f_h)
    OUT.mkdir(parents=True, exist_ok=True)
    p = OUT / f"QORTUBA_OPENING_{n}.png"
    img.save(p)
    return p


def finish():
    qs = [q for q in reg(Path(PR.OUT_DIR) / "pa08_qortuba_boq", "QORTUBA_OWNER_QUESTIONS")["ROWS"]
          if q["ASKS_FOR"] in ASK]
    sites = {r["SITE_ID"]: r for r in reg(R1, "PA08_QORTUBA_R1_OPENING_REGISTER")["ROWS"]}
    hosts = {o["OPENING_ID"]: o["HOST_WALL_ID"] for o in reg(Path(PR.OUT_DIR) / "pa08_qortuba_boq",
                                                             "QORTUBA_OPENING_REGISTER_COMPLETED")["ROWS"]}
    jp, bs, rooms = jamb_points(), bands(), _rooms()
    out = []
    for q in qs:
        sid = q["AUDIT_OPENING_ID"]
        band = bs[hosts[sid]]
        lo, hi, basis = gap_interval(sites[sid], band, jp)
        hint = None
        same = [z for z in qs if hosts[z["AUDIT_OPENING_ID"]] == hosts[sid] and z["ASKS_FOR"] == q["ASKS_FOR"]]
        if len(same) > 1:
            other = [z["#"] for z in same if z["#"] != q["#"]]
            hint = (f"This short wall has a gap at BOTH ends: this one, and opening #{other[0]} at the other end. "
                    f"They may be the same kind of thing or different - please answer each.")
        p = draw_crop(q["#"], q, band, lo, hi, rooms, bs, hint)
        out.append({"#": q["#"], "ROOM": q["ROOM"], "LOCATION": q["LOCATION"], "WIDTH_M": q["WIDTH_M"],
                    "ASKS_FOR": q["ASKS_FOR"], "QUESTION": ASK[q["ASKS_FOR"]][1],
                    "IMAGE": str(p), "MARKER_BASIS": basis,
                    "ADJACENT_ROOMS": band["ROOMS"], "AUDIT_OPENING_ID": sid})
    rec = {"ARTIFACT": "QORTUBA_OWNER_QUESTION_CROPS",
           "RULE": "one crop per unresolved opening, numbered as in the question table.  No CAD or hash identifier "
                   "appears on any image; the id is carried here for the audit trail only",
           "CHOICES": CHOICES, "PASSAGE_CHOICES": PASSAGE_CHOICES, "ROWS": out, "COUNT": len(out),
           "NO_TYPE_INFERRED": True,
           "A_SETTLED_TYPE_IS_NEVER_ASKED_AGAIN": "a crop for a confirmed open passage asks only the vertical "
                                                  "condition; it does not offer door / window / sliding door again",
           "GEOMETRY_MODIFIED": "NONE"}
    (Path(PR.OUT_DIR) / "pa08_qortuba_boq" / "QORTUBA_OWNER_QUESTION_CROPS.json").write_text(
        json.dumps(rec, indent=1, ensure_ascii=False, default=str), "utf-8")
    return rec


if __name__ == "__main__":
    r = finish()
    for x in r["ROWS"]:
        print(f"#{x['#']}  {x['WIDTH_M']:.3f} m  {x['LOCATION']}\n     {x['IMAGE']}  ({x['MARKER_BASIS']})")
