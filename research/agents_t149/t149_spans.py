"""T-149 span preparation: continuous-beam span order, support widths and axis-to-axis spans (Ln) from the drawing.

Research helper (NO REPO CODE task): it imports nothing from engine/ and changes no released quantity.

    .work/venv/bin/python -I research/agents_t149/t149_spans.py <structural DXF> <T-110 register CSV> <out CSV>

What it does, for every beam-register row (T-110 BEAM_MEMBER_REGISTER.csv, plus the T-145 CB5 span 2 row typed below):
  * passes the row through (mark, floor, status, b, D, clear length L = register length, face to face);
  * for the continuous beams (schedule mark CB1 .. CB13) orders the spans along the beam axis, takes each interior
    support width as the gap between two consecutive spans (face to face), and measures each end-support width on the
    DXF: from the span's outer end it walks along the axis and records the perpendicular lines of layers 1 / 2 / 5 /
    S-COL.BON that cross the axis; the first line within 10 mm is the support face, the next one beyond 50 mm the far
    face. If no face line lies within 10 mm of the register end, the end is flagged GEOMETRY_CHECK and the width is
    reported as a range (0 .. distance to the far line), never one value;
  * Ln (the typical details on ST p.11 / p.12 dimension Ln between the support axes) = L + w_left / 2 + w_right / 2;
  * a beam that runs as one register band through an interior column (GF CB7) is split at the column faces found
    inside the band;
  * span order evidence: the beams that frame into each span (register rows of the same floor ending on the CB face)
    are listed with their distance from the span start, to be compared by hand with the concentrated loads that the
    schedule prints per span (p.11 / p.12 "1.6|27" arrows).
No drawing content is written except member ids, floors, marks and lengths (no client name, no text strings).
"""

import csv
import math
import sys

import ezdxf

LAYERS = ("1", "5", "S-COL.BON")   # beam edges (1 / 5) and columns; layer 2 carries hatch / cantilever lines
CB_MARKS = tuple("CB%d" % i for i in range(1, 14))
# axis orientation of each continuous beam on its slab plan (H = along x, V = along y), read on the plan
AXIS = {"CB1": "V", "CB2": "H", "CB3": "H", "CB4": "V", "CB5": "V", "CB6": "H", "CB7": "H", "CB8": "H",
        "CB9": "H", "CB10": "V", "CB11": "H", "CB12": "V", "CB13": "V"}
# T-145 (agents/task-T-145 d540270, ITEMS.csv): CB5 span 2, band x 52.693 - 52.893, faces y 41.248 .. 44.948 (B20 south face)
T145_ROWS = [dict(member_id="BM-GF-035.2", floor="GF", component="T-145 CB5 span 2", mark="CB5", type="beam span",
                  status="CALCULATED", width_m="0.2", depth_m="0.4", length_m="3.7", m3="0.2960", m3_low="0.2960",
                  m3_high="0.2960", m3_calc="0.2960", section="schedule row (no section cuts it)",
                  schedule="CB5 20x40 (continuous 2-span schedule, p.11)",
                  evidence="T-145: second CB5 label parallel at y 42.680; column / B1 face 41.248 to B20 south face 44.948",
                  conflict="", designer="", x="52.793", y="43.098")]


def load_segments(path):
    doc = ezdxf.readfile(path)
    segs = []

    def add(e):
        t = e.dxftype()
        if e.dxf.layer not in LAYERS:
            return
        if t == "LINE":
            a, b = e.dxf.start, e.dxf.end
            segs.append((e.dxf.layer, a.x / 1000, a.y / 1000, b.x / 1000, b.y / 1000))
        elif t == "LWPOLYLINE":
            pts = [(p[0], p[1]) for p in e.get_points("xy")]
            if e.closed:
                pts.append(pts[0])
            for p, q in zip(pts, pts[1:]):
                segs.append((e.dxf.layer, p[0] / 1000, p[1] / 1000, q[0] / 1000, q[1] / 1000))

    def walk(ents, depth=0):
        for e in ents:
            if e.dxftype() == "INSERT" and depth < 8:
                try:
                    walk(list(e.virtual_entities()), depth + 1)
                except Exception:
                    pass
            else:
                try:
                    add(e)
                except Exception:
                    pass

    walk(doc.modelspace())
    return segs


def crossings(segs, px, py, horiz, sign, lo=-0.012, hi=1.6):
    """signed distances (along the axis, in direction sign) of perpendicular lines crossing the axis line."""
    out = set()
    for _l, x1, y1, x2, y2 in segs:
        if horiz:
            if abs(x1 - x2) > 0.002 or not (min(y1, y2) - 0.001 <= py <= max(y1, y2) + 0.001):
                continue
            d = (x1 - px) * sign
        else:
            if abs(y1 - y2) > 0.002 or not (min(x1, x2) - 0.001 <= px <= max(x1, x2) + 0.001):
                continue
            d = (y1 - py) * sign
        if lo < d < hi:
            out.add(round(d, 4))
    return sorted(out)


def end_column_inside(segs, px, py, horiz, sign, L):
    """depth of a column (layer S-COL.BON) that lies INSIDE the register span at this end: a column face on the
    register end and the column's other face inside the span (0.10 m .. min(0.95, L - 0.05)). The register length
    then runs to the outer face of an end column; the clear span stops at its inner face."""
    cols = [s for s in segs if s[0] == "S-COL.BON"]
    at = crossings(cols, px, py, horiz, sign, -0.012, 0.012)
    inner = crossings(cols, px, py, horiz, -sign, 0.10, min(0.95, L - 0.05))
    if at:
        return inner[0] if inner else 0.0
    # the register end lies INSIDE a column (no face at the end, column lines on both sides of it within one column)
    if crossings(segs, px, py, horiz, sign, -0.012, 0.012):
        return 0.0
    outer = crossings(cols, px, py, horiz, sign, 0.012, 0.95)
    inner2 = crossings(cols, px, py, horiz, -sign, 0.012, min(0.95, L - 0.05))
    if outer and inner2 and outer[0] + inner2[0] <= 1.2:
        return inner2[0]
    return 0.0


def orientation(segs, x, y, L):
    """H or V: the axis along which both register ends sit on a perpendicular drawn line (more faces wins)."""
    best = None
    for horiz in (True, False):
        f = 0
        for s in (-1, 1):
            px, py = (x + s * L / 2, y) if horiz else (x, y + s * L / 2)
            if crossings(segs, px, py, horiz, s, -0.012, 0.012):
                f += 1
        if best is None or f > best[0]:
            best = (f, horiz)
    return best


def end_support(segs, px, py, horiz, sign):
    c = crossings(segs, px, py, horiz, sign)
    face = [d for d in c if abs(d) <= 0.010]
    far = [d for d in c if d > 0.10]   # 50 mm drafting offsets (wall faces) are not a support face
    if face and far:
        return far[0] - face[0], far[0] - face[0], "FACE_FOUND"
    if far:
        return 0.0, far[0], "GEOMETRY_CHECK (no face line within 10 mm of the register end; first line at %.3f)" % far[0]
    return None, None, "NO_SUPPORT_LINE_FOUND"


def main(dxf_path, reg_path, out_path):
    segs = load_segments(dxf_path)
    reg = list(csv.DictReader(open(reg_path, encoding="utf-8")))
    reg = reg + [dict(r) for r in T145_ROWS]
    groups = {}
    for i, r in enumerate(reg):
        sch = r["schedule"].split()[0] if r["schedule"] else ""
        if sch in CB_MARKS and r["x"] and r["length_m"].replace(".", "", 1).isdigit():
            groups.setdefault((r["floor"], sch), []).append(i)
    extra = {}
    for (floor, cb), idx in groups.items():
        h = AXIS[cb] == "H"
        spans = []
        for i in idx:
            r = reg[i]
            x, y, L = float(r["x"]), float(r["y"]), float(r["length_m"])
            c = x if h else y
            spans.append([c - L / 2, c + L / 2, i, x, y])
        spans.sort()
        # split a single band that runs through an interior column (faces found inside the band)
        if len(spans) == 1:
            s0, s1, i, x, y = spans[0]
            px, py = (s0, y) if h else (x, s0)
            inside = [d for d in crossings(segs, px, py, h, 1, 0.3, (s1 - s0) - 0.3)]
            if len(inside) >= 2:
                a, b = inside[0], inside[-1]
                extra[i] = dict(split=[(s0, s0 + a), (s0 + b, s1)], column=(a, b))
        rows = []
        if extra.get(spans[0][2]):
            s0, s1, i, x, y = spans[0]
            for k, (a, b) in enumerate(extra[i]["split"]):
                rows.append([a, b, i, x, y, k])
        else:
            rows = [s + [None] for s in spans]
        n = len(rows)
        # an end column inside the register span at the member's outer end: the clear span stops at its inner face
        endcol = {}
        a0, b0 = rows[0][0], rows[-1][1]
        x0, y0 = rows[0][3], rows[0][4]
        d0 = end_column_inside(segs, *((a0, y0) if h else (x0, a0)), h, -1, rows[0][1] - a0)
        d1 = end_column_inside(segs, *((b0, y0) if h else (x0, b0)), h, 1, rows[-1][1] - rows[-1][0])
        cols = [sg for sg in segs if sg[0] == "S-COL.BON"]
        if d0:
            rows[0][0] = a0 + d0
            beyond = crossings(cols, *((a0, y0) if h else (x0, a0)), h, -1, 0.012, 0.95)
            endcol["L"] = d0 + (beyond[0] if beyond and not crossings(segs, *((a0, y0) if h else (x0, a0)), h, -1, -0.012, 0.012) else 0.0)
            endcol["Ld"] = d0
        if d1:
            rows[-1][1] = b0 - d1
            beyond = crossings(cols, *((b0, y0) if h else (x0, b0)), h, 1, 0.012, 0.95)
            endcol["R"] = d1 + (beyond[0] if beyond and not crossings(segs, *((b0, y0) if h else (x0, b0)), h, 1, -0.012, 0.012) else 0.0)
            endcol["Rd"] = d1
        for k, (a, b, i, x, y, part) in enumerate(rows):
            r = reg[i]
            if k == 0 and "L" in endcol:
                wl_lo = wl_hi = endcol["L"]
                fl = "END_COLUMN_INSIDE_REGISTER_SPAN (register runs to the column's outer face; clear span -%.3f)" % endcol["Ld"]
            elif k == 0:
                px, py = (a, y) if h else (x, a)
                wl_lo, wl_hi, fl = end_support(segs, px, py, h, -1)
            else:
                wl_lo = wl_hi = round(a - rows[k - 1][1], 4)
                fl = "INTERIOR (gap between spans)"
            if k == n - 1 and "R" in endcol:
                wr_lo = wr_hi = endcol["R"]
                fr = "END_COLUMN_INSIDE_REGISTER_SPAN (register runs to the column's outer face; clear span -%.3f)" % endcol["Rd"]
            elif k == n - 1:
                px, py = (b, y) if h else (x, b)
                wr_lo, wr_hi, fr = end_support(segs, px, py, h, 1)
            else:
                wr_lo = wr_hi = round(rows[k + 1][0] - b, 4)
                fr = "INTERIOR (gap between spans)"
            L = b - a
            key = (i, part)
            extra[key] = dict(cb=cb, span_index=k + 1, n_spans=n, L=round(L, 4), start=round(a, 4), end=round(b, 4),
                              w_left=(wl_lo, wl_hi), w_right=(wr_lo, wr_hi), flag_left=fl, flag_right=fr)
    fields = ["row_id", "member_id", "floor", "mark", "schedule_mark", "type", "status", "width_m", "depth_m",
              "length_m", "span_index", "n_spans", "axis", "span_start", "span_end", "w_left_lo", "w_left_hi",
              "w_right_lo", "w_right_hi", "Ln_lo", "Ln_hi", "clear_length_m", "geometry_left", "geometry_right", "framing_beams", "m3_low"]
    out = []
    for i, r in enumerate(reg):
        parts = [p for (ii, p) in [k for k in extra if isinstance(k, tuple)] if ii == i]
        base = dict(member_id=r["member_id"], floor=r["floor"], mark=r["mark"],
                    schedule_mark=r["schedule"].split()[0] if r["schedule"] else "", type=r["type"],
                    status=r["status"], width_m=r["width_m"], depth_m=r["depth_m"], length_m=r["length_m"],
                    m3_low=r["m3_low"])
        if not parts:
            row = dict(base, row_id="R%03d" % (i + 1))
            try:
                L, x, y = float(r["length_m"]), float(r["x"]), float(r["y"])
            except ValueError:
                out.append(row)
                continue
            faces, h = orientation(segs, x, y, L)
            row["axis"] = "H" if h else "V"
            dl = end_column_inside(segs, *((x - L / 2, y) if h else (x, y - L / 2)), h, -1, L)
            dr = end_column_inside(segs, *((x + L / 2, y) if h else (x, y + L / 2)), h, 1, L)
            if faces < 2 and (dl or dr):   # orientation not confirmed by two drawn end faces: report, do not correct
                row["framing_beams"] = "END_COLUMN_CANDIDATE %.3f / %.3f (not applied: %d of 2 end faces)" % (dl, dr, faces)
                dl = dr = 0.0
            row["geometry_left"] = ("END_COLUMN_INSIDE_REGISTER_SPAN %.3f" % dl) if dl else ("FACE" if faces else "")
            row["geometry_right"] = ("END_COLUMN_INSIDE_REGISTER_SPAN %.3f" % dr) if dr else ""
            if faces < 2:
                row["geometry_right"] = (row["geometry_right"] + " ends on a drawn face: %d of 2 (length is the "
                                         "register's, not re-measured)" % faces).strip()
            row["clear_length_m"] = round(L - dl - dr, 4)
            out.append(row)
            continue
        for p in sorted(parts, key=lambda v: -1 if v is None else v):
            e = extra[(i, p)]
            h = AXIS[e["cb"]] == "H"
            fx = framing(reg, i, r["floor"], h, e["start"], e["end"], float(r["y"] if h else r["x"]),
                         float(r["width_m"].split()[0]))
            row = dict(base, row_id="R%03d%s" % (i + 1, "" if p is None else "abc"[p]), span_index=e["span_index"],
                       n_spans=e["n_spans"], axis="H" if h else "V", span_start=e["start"], span_end=e["end"],
                       w_left_lo=e["w_left"][0], w_left_hi=e["w_left"][1], w_right_lo=e["w_right"][0],
                       w_right_hi=e["w_right"][1], geometry_left=e["flag_left"], geometry_right=e["flag_right"],
                       framing_beams=fx)
            row["clear_length_m"] = e["L"]
            if p is not None:
                row["length_m"] = e["L"]
                row["type"] = r["type"] + " (split at the interior column found inside the band)"
            L = e["L"]
            if None not in (e["w_left"][0], e["w_right"][0]):
                row["Ln_lo"] = round(L + e["w_left"][0] / 2 + e["w_right"][0] / 2, 4)
                row["Ln_hi"] = round(L + e["w_left"][1] / 2 + e["w_right"][1] / 2, 4)
            out.append(row)
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for row in out:
            w.writerow({k: row.get(k, "") for k in fields})
    print("rows", len(out), "continuous spans", sum(1 for k in extra if isinstance(k, tuple)))


def framing(reg, self_i, floor, horiz, a, b, axis_coord, width):
    """beams of the same floor whose register end lies on this span's side face: distance from the span start."""
    hits = []
    for j, r in enumerate(reg):
        if j == self_i or r["floor"] != floor or not r["x"]:
            continue
        try:
            L = float(r["length_m"])
        except ValueError:
            continue
        X, Y = float(r["x"]), float(r["y"])
        along, across = (X, Y) if horiz else (Y, X)
        for s in (-1, 1):
            e = across + s * L / 2
            if abs(abs(e - axis_coord) - width / 2) < 0.06 and a - 0.01 < along < b + 0.01:
                hits.append("%s@%.2f" % (r["mark"], along - a))
    return " ".join(sorted(set(hits)))


if __name__ == "__main__":
    main(*sys.argv[1:4])
