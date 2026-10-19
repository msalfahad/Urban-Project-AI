"""SCHEDULE TEXT ROWS (V1) - schedule rows drawn as plain TEXT / MTEXT inside a block-attribute table, and struck-out
cells, read by position; beside the frozen SCHEDULE_READER_V1 (engine/source/schedule_reader.py, never edited).

Why: a CAD office often draws a schedule as one block insert per row (values as ATTRIBs) and then types a late row as
plain TEXT in the same table, or strikes out the cells of a level where a member type does not exist. The frozen route
reads attribute rows only (text tables only when fewer than 3 attribute rows exist), so such a row is silently
dropped and its plan marks become TYPE_NOT_IN_SCHEDULE; a struck cell and a blank cell both read as "no band".

Method (per attribute table = owners sharing one tag set with a mark field, >= 2 rows):
  local frame  the row direction is the mean direction from each row's mark attribute to its other attributes; every
               entity is rotated into that frame (any rotation; a mirrored table keeps the mark column first). Column
               positions = median local x of each tag; row pitch = median spacing of the attribute rows. Tolerances are
               fractions of the pitch, so units (mm, cm, m) never enter.
  frame        the table's own drawn frame: the lines that run across every tag column end on its left and right
               border; the border verticals drawn there that cross every attribute row give its height (their common
               span; an inner column separator is never taken for the border). No frame drawn -> FRAME_NOT_FOUND,
               no text row is read (nothing is inferred).
  bands        horizontal lines inside the frame that run across every tag column cut it into bands; bands thinner
               than 0.3 x pitch (double border lines) are skipped.
  cells        a text in a band is bound to the tag column whose grid cell (vertical lines crossing the band) holds
               it, nearest tag x when a grid cell holds several tags (count + diameter under one REINF header). A text
               in no tag cell is UNBOUND and reported; a TEXT drawn over an attribute row is reported, never read.
               Symbol-only texts (the diameter sign) are separators.
  rows         a band without attribute rows whose mark-column cell parses as a member mark becomes a row; it is parsed
               by the frozen attribute parser itself (one synthetic attribute per tag), so units, storey prefixes,
               bars and family logic are identical to the attribute rows of the same table.
  strike-out   a line drawn through the middle half of a band (not a band rule: both ends inside the band, or a
               corner-to-corner diagonal) that runs at least 25 % into a tag's grid cell is a strike of that cell (a
               strike drawn by hand often starts part-way into the first cell; touching a cell edge is not enough). A storey whose size
               cells are all struck and carry no value is STRUCK (= no member of this type at this level, drawn
               evidence). Never inferred from a blank cell: blank stays EMPTY (held), a half-filled band is
               MISSING_CELL (held), a struck cell that also carries a value is CONFLICT (held).

Nothing here creates or releases a quantity: neck heights stay with the founding datum (owner Q-21 = C). Rules:
UP-KB-PREC-001 (printed value wins), UP-QTY-STATUS-001 (held never 0), owner answers Q-16, Q-19, Q-21.
"""

from __future__ import annotations

import math
import re
from collections import defaultdict

from engine.source import drawing_model as DM
from engine.source import schedule_reader as SR

POLICY_ID = "SCHEDULE_TEXT_ROWS_V1"
SIZE_ROLES = ("W", "H")
BAND_MIN_SHARE = 0.3          # of the row pitch: thinner bands are double border lines
LINE_TOL_SHARE = 0.02         # of the row pitch: a line within this of horizontal / vertical is one
EDGE_SHARE = 0.08             # of the band height: a strike must stay this far inside the band edges
STRIKE_COVER_SHARE = 0.25     # of a grid cell's width: a strike must run this far into the cell (not touch its edge)


# ------------------------------------------------------------------ geometry helpers
def _rot(p, ox, oy, c, s):
    x, y = p[0] - ox, p[1] - oy
    return (x * c + y * s, -x * s + y * c)


def _median(v):
    v = sorted(v)
    n = len(v)
    return (v[n // 2] if n % 2 else (v[n // 2 - 1] + v[n // 2]) / 2.0) if n else None


def _has_content(value):
    t = DM.normalize(value or "")
    return bool(re.search(r"[0-9A-Za-z؀-ۿ]", t))


# ------------------------------------------------------------------ tables
def attribute_tables(attributes):
    """[{owner, tag, value, x, y}] -> [{tags, mark_tag, owners: {owner: {tag: (value, x, y)}}}] for every tag set with
    a mark field (one row is enough: its pitch then comes from the band rules drawn round it)."""
    by_owner = defaultdict(dict)
    for a in attributes:
        by_owner[a["owner"]][a["tag"]] = (a["value"], float(a["x"]), float(a["y"]))
    groups = defaultdict(dict)
    for owner, vals in by_owner.items():
        groups[tuple(sorted(vals))][owner] = vals
    out = []
    for tags, owners in sorted(groups.items()):
        if len(tags) < 3 or not owners:
            continue
        mf, _ = SR.mark_field([{t: v[0] for t, v in vals.items()} for vals in owners.values()], tags)
        if mf is None:
            continue
        out.append({"tags": list(tags), "mark_tag": mf, "owners": dict(sorted(owners.items(), key=lambda kv:
                                                                                  str(kv[0])))})
    return out


def _frame_of(table, segs):
    """row direction, local transform, tag x, row y, pitch."""
    mf = table["mark_tag"]
    vx = vy = 0.0
    for vals in table["owners"].values():
        mx, my = vals[mf][1], vals[mf][2]
        for t, (_, x, y) in vals.items():
            d = math.hypot(x - mx, y - my)
            if t != mf and d > 0:
                vx += x - mx                    # length-weighted: the far columns fix the direction best
                vy += y - my
    if math.hypot(vx, vy) == 0:
        return None
    ang = math.atan2(vy, vx)
    return _frame_of_angle(table, ang, math.cos(ang), math.sin(ang), segs)


def _frame_of_angle(table, ang, c, s, segs):
    mf = table["mark_tag"]
    first = next(iter(table["owners"].values()))
    ox, oy = first[mf][1], first[mf][2]
    tag_x = {t: _median([_rot(v[t][1:], ox, oy, c, s)[0] for v in table["owners"].values()]) for t in table["tags"]}
    row_y = {o: _median([_rot(p[1:], ox, oy, c, s)[1] for p in v.values()]) for o, v in table["owners"].items()}
    ys = sorted(row_y.values())
    gaps = [b - a for a, b in zip(ys, ys[1:]) if b - a > 0]
    pitch = _median(gaps)
    if not pitch and len(ys) == 1:                  # one row: the band the drawn rules make round it
        xs = sorted(tag_x.values())
        tol = 0.002 * max(xs[-1] - xs[0], 1e-9)
        above, below = [], []
        for sg in segs:
            a, b = _rot(sg["a"], ox, oy, c, s), _rot(sg["b"], ox, oy, c, s)
            if abs(a[1] - b[1]) > tol or min(a[0], b[0]) > xs[0] + tol or max(a[0], b[0]) < xs[-1] - tol:
                continue
            ym = (a[1] + b[1]) / 2
            (above if ym > ys[0] else below).append(ym)
        pitch = (min(above) - max(below)) if above and below else None
    if not pitch:
        return None
    return {"table": table, "angle_deg": math.degrees(ang) % 360.0, "o": (ox, oy), "cs": (c, s), "tag_x": tag_x,
            "row_y": row_y, "pitch": pitch}


SNAP_DEG = 2.0                # the drawn grid lines fix the row direction when they lie within this of the attributes'


def _snap(F, segs):
    """refine the row direction to the table's own drawn lines (attribute insertion points are not exactly aligned:
    a 0.4 deg error tilts a 10 m frame line by 70 mm). Long segments near the attribute rows within SNAP_DEG of the
    row direction or of its normal vote by length; without such lines the attribute direction stays."""
    ang0 = math.radians(F["angle_deg"])
    (ox, oy), (c, s) = F["o"], F["cs"]
    xs, ys = sorted(F["tag_x"].values()), sorted(F["row_y"].values())
    x0, x1, y0, y1 = xs[0] - F["pitch"], xs[-1] + F["pitch"], ys[0] - F["pitch"], ys[-1] + F["pitch"]
    num = den = 0.0
    for sg in segs:
        a, b = _rot(sg["a"], ox, oy, c, s), _rot(sg["b"], ox, oy, c, s)
        ln = math.hypot(b[0] - a[0], b[1] - a[1])
        if ln < 2 * F["pitch"]:
            continue
        mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
        if not (x0 <= mx <= x1 and y0 <= my <= y1):
            continue
        d = math.degrees(math.atan2(b[1] - a[1], b[0] - a[0])) % 90.0
        d = d - 90.0 if d > 45.0 else d
        if abs(d) <= SNAP_DEG:
            num += d * ln
            den += ln
    if not den:
        return F
    ang = ang0 + math.radians(num / den)
    c2, s2 = math.cos(ang), math.sin(ang)
    return _frame_of_angle(F["table"], ang, c2, s2, segs) or F


def read(intake, *, sheet_of=None):
    """intake (tools/urban_intake record: attributes, texts, segments) -> {policy, schedule (SR form, attribute rows +
    text rows), lib, tables: [...], cell_status: {(family, mark): {storey: status}}, unbound: [...], warnings}."""
    attrs = list(intake.get("attributes", []))
    texts = [t for t in intake.get("texts", []) if _has_content(t.get("value"))]
    segs = intake.get("segments", [])
    tables, synth, status, unbound, warnings = [], [], {}, [], []
    for k, tb in enumerate(attribute_tables(attrs)):
        F = _frame_of(tb, segs)
        if F is not None:
            F = _snap(F, segs)
        rec = {"table": k, "tags": tb["tags"], "mark_tag": tb["mark_tag"], "n_attribute_rows": len(tb["owners"]),
               "text_rows": [], "struck_cells": [], "bands_without_mark": []}
        tables.append(rec)
        if F is None:
            rec["state"] = "NO_ROW_DIRECTION"
            warnings.append(f"table {k}: no row direction or pitch")
            continue
        (ox, oy), (c, s), p = F["o"], F["cs"], F["pitch"]
        rec.update(angle_deg=round(F["angle_deg"], 4) % 360.0, pitch=round(p, 6))
        tol = LINE_TOL_SHARE * p
        L = []
        for sg in segs:
            a, b = _rot(sg["a"], ox, oy, c, s), _rot(sg["b"], ox, oy, c, s)
            L.append((a, b, sg))
        hz = [(a, b, sg) for a, b, sg in L if abs(a[1] - b[1]) <= tol]
        vt = [(a, b, sg) for a, b, sg in L if abs(a[0] - b[0]) <= tol]
        xs = sorted(F["tag_x"].values())
        xmin, xmax = xs[0], xs[-1]
        ry = sorted(F["row_y"].values())
        # the frame: the rules that run across every tag column end on the table's border lines; the border
        # verticals drawn there, crossing every attribute row, give the frame's height (an inner column separator
        # is never taken for the border)
        full = [(min(a[0], b[0]), max(a[0], b[0])) for a, b, _ in hz
                if min(a[0], b[0]) <= xmin + tol and max(a[0], b[0]) >= xmax - tol]
        frame = None
        if full:
            L0, R0 = _median([f[0] for f in full]), _median([f[1] for f in full])
            near = 0.1 * p

            def side(x0):
                vs = [(min(a[1], b[1]), max(a[1], b[1])) for a, b, _ in vt
                      if abs((a[0] + b[0]) / 2 - x0) <= near and min(a[1], b[1]) <= ry[0] + tol and
                      max(a[1], b[1]) >= ry[-1] - tol]
                return max(vs, key=lambda v: v[1] - v[0]) if vs else None
            lv, rv = side(L0), side(R0)
            if lv and rv:
                frame = (L0, max(lv[0], rv[0]), R0, min(lv[1], rv[1]))
        if frame is None:
            rec["state"] = "FRAME_NOT_FOUND"
            warnings.append(f"table {k} ({tb['mark_tag']}): no drawn frame round the attribute rows; text rows not "
                            "read")
            continue
        fx0, fy0, fx1, fy1 = frame
        rec["frame_local"] = [fx0, fy0, fx1, fy1]
        rules = sorted({round((a[1] + b[1]) / 2, 6) for a, b, _ in hz
                        if min(a[0], b[0]) <= xmin + tol and max(a[0], b[0]) >= xmax - tol and
                        fy0 - tol <= (a[1] + b[1]) / 2 <= fy1 + tol})
        yb = []
        for y in [fy0] + rules + [fy1]:
            if not yb or y - yb[-1] > tol:
                yb.append(y)
        bands = [(lo, hi) for lo, hi in zip(yb, yb[1:]) if hi - lo >= BAND_MIN_SHARE * p]
        own_band = {}
        for o, y in F["row_y"].items():
            for i, (lo, hi) in enumerate(bands):
                if lo < y < hi:
                    own_band[o] = i
        att_bands = set(own_band.values())
        tl = [(t, _rot((t["x"], t["y"]), ox, oy, c, s)) for t in texts]
        tl = [(t, q) for t, q in tl if fx0 < q[0] < fx1 and fy0 < q[1] < fy1]

        def grid_cell(x, lo, hi):
            mid = (lo + hi) / 2
            vs = sorted({(a[0] + b[0]) / 2 for a, b, _ in vt if min(a[1], b[1]) <= mid <= max(a[1], b[1]) and
                         fx0 - tol <= (a[0] + b[0]) / 2 <= fx1 + tol})
            left_ = [v for v in vs if v <= x]
            right_ = [v for v in vs if v > x]
            return (left_[-1] if left_ else fx0, right_[0] if right_ else fx1)

        def strikes(lo, hi):
            e = EDGE_SHARE * (hi - lo)
            out = []
            mid, h = (lo + hi) / 2, hi - lo
            for a, b, sg in L:
                y0, y1 = min(a[1], b[1]), max(a[1], b[1])
                if abs(a[0] - b[0]) <= tol or abs((a[1] + b[1]) / 2 - mid) > 0.25 * h:
                    continue                    # a vertical separator, or a line off the band middle: not a strike
                if max(a[0], b[0]) < fx0 or min(a[0], b[0]) > fx1:
                    continue
                if y0 >= lo + e and y1 <= hi - e:
                    out.append((min(a[0], b[0]), max(a[0], b[0]), sg))
                elif abs(a[1] - b[1]) > tol and lo - e <= y0 and y1 <= hi + e and \
                        lo + e < (a[1] + b[1]) / 2 < hi - e:            # a diagonal from corner to corner
                    out.append((min(a[0], b[0]), max(a[0], b[0]), sg))
            return out

        def cell_strikes(lo, hi):
            st = strikes(lo, hi)
            out = {}
            for t in tb["tags"]:
                g0, g1 = grid_cell(F["tag_x"][t], lo, hi)
                w = max(g1 - g0, tol)
                out[t] = [sg["id"] for x0, x1, sg in st if min(x1, g1) - max(x0, g0) >= STRIKE_COVER_SHARE * w]
            return out

        for i, (lo, hi) in enumerate(bands):
            cs_ = cell_strikes(lo, hi)
            here = [(t, q) for t, q in tl if lo < q[1] < hi]
            if i in att_bands:
                for o in [o for o, b in own_band.items() if b == i]:
                    vals = {t: v[0] for t, v in tb["owners"][o].items()}
                    _status(status, rec, tb, vals, cs_, f"INSERT {o}")
                for t, q in here:                # a TEXT typed over an attribute row is never read, but reported
                    unbound.append({"table": k, "text_id": t["id"], "value": t["value"], "band": i,
                                    "why": "TEXT_IN_ATTRIBUTE_ROW"})
                continue
            if not here:
                continue
            cells, loose = defaultdict(list), []
            for t, q in sorted(here, key=lambda tq: tq[1][0]):
                g0, g1 = grid_cell(q[0], lo, hi)
                cand = [tg for tg in tb["tags"] if g0 <= F["tag_x"][tg] <= g1]
                if not cand:
                    loose.append(t)
                    continue
                tg = min(cand, key=lambda tg: (abs(F["tag_x"][tg] - q[0]), tg))
                for part in DM.normalize(t["value"]).split():
                    if _has_content(part):
                        cells[tg].append((part, t["id"]))
            mark_txt = " ".join(v for v, _ in cells.get(tb["mark_tag"], []))
            fam, mk = DM.mark_family(mark_txt.replace(" ", "")) if mark_txt else (None, None)
            for t in loose:
                unbound.append({"table": k, "text_id": t["id"], "value": t["value"], "band": i,
                                "why": "TEXT_OUTSIDE_EVERY_TAG_COLUMN"})
            if fam is None:
                rec["bands_without_mark"].append({"band": i, "texts": [t["value"] for t, _ in here]})
                continue
            vals = {}
            for tg in tb["tags"]:
                parts = cells.get(tg, [])
                if len(parts) > 1 and tg != tb["mark_tag"]:
                    unbound.append({"table": k, "band": i, "tag": tg, "values": [v for v, _ in parts],
                                    "why": "SEVERAL_VALUES_IN_ONE_CELL"})
                    vals[tg] = ""
                    continue
                vals[tg] = " ".join(v for v, _ in parts)
            owner = f"TEXTROW:{k}:{i}"
            q0 = next(q for t, q in here if any(tid == t["id"] for _, tid in cells.get(tb["mark_tag"], [])))
            wx = ox + q0[0] * c - q0[1] * s
            wy = oy + q0[0] * s + q0[1] * c
            for tg in tb["tags"]:
                synth.append({"owner": owner, "tag": tg, "value": vals[tg], "x": wx, "y": wy})
            rec["text_rows"].append({"band": i, "mark": mk, "owner": owner, "values": vals,
                                     "text_ids": sorted({tid for ps in cells.values() for _, tid in ps})})
            _status(status, rec, tb, vals, cs_, owner)
        rec["state"] = "READ"
    sched = SR.from_attribute_rows(attrs + synth, sheet_of=sheet_of)
    by_owner = {}
    for r in sched["rows"]:
        by_owner.setdefault(str(r["source"].split(" ", 1)[1] if r["source"].startswith("INSERT ") else
                                r["source"]), []).append(r)
    cell_status = {}
    for (src, mark_raw), st in status.items():
        for r in by_owner.get(str(src), []):
            r["cell_status"] = st
            r["form"] = "TEXT_ROW" if str(src).startswith("TEXTROW:") else "ATTRIBUTE_ROW"
            cell_status[(r["family"], r["mark"])] = st
    for r in sched["rows"]:
        if str(r["source"]).startswith("INSERT TEXTROW:"):
            r["source"] = "TEXT_ROW " + r["source"].split(" ", 1)[1]
    _row_unit_check(sched, warnings)
    return {"policy": POLICY_ID, "schedule": sched, "lib": SR.library(sched), "tables": tables,
            "cell_status": cell_status, "unbound": unbound, "warnings": warnings}


def _status(status, rec, tb, vals, cell_strikes, src):
    """per storey prefix of the table: PRESENT / STRUCK / EMPTY / MISSING_CELL / CONFLICT (drawn evidence only)."""
    groups = defaultdict(list)
    for t in tb["tags"]:
        p, stem = SR._split_tag(t)
        if SR._size_role(stem) in SIZE_ROLES and t != tb["mark_tag"]:
            groups[SR.STOREY_PREFIX.get(p, p) if p else "ALL"].append(t)
    out = {}
    for storey, tags in sorted(groups.items()):
        has = [t for t in tags if _has_content(vals.get(t))]
        struck = [t for t in tags if cell_strikes.get(t)]
        if struck and has:
            st = {"status": "CONFLICT", "why": "a struck cell carries a value", "tags": sorted(set(struck) & set(has))
                  or struck}
        elif len(struck) == len(tags):
            st = {"status": "STRUCK", "segments": sorted({s for t in tags for s in cell_strikes[t]})}
        elif len(has) == len(tags):
            st = {"status": "PRESENT"}
        elif not has and not struck:
            st = {"status": "EMPTY", "why": "blank cells, no strike drawn: not read as 'none'"}
        else:
            st = {"status": "MISSING_CELL", "missing": sorted(set(tags) - set(has) - set(struck)),
                  "struck": sorted(struck)}
        out[storey] = st
        if st["status"] == "STRUCK":
            rec["struck_cells"].append({"source": src, "storey": storey, "segments": st["segments"]})
    status[(str(src.split(" ", 1)[1] if src.startswith("INSERT ") else src), vals.get(tb["mark_tag"]))] = out


def _row_unit_check(sched, warnings):
    """a text row whose own sizes fit a different unit than its family's: CONFLICT kept on the row (held)."""
    for r in sched["rows"]:
        if r.get("form") != "TEXT_ROW":
            continue
        fam = sched["families"].get(r["family"]) or {}
        vals = defaultdict(list)
        for b in list(r.get("by_storey", {}).values()) + [{"dims_raw": r.get("dims_raw", {})}]:
            for role, v in b.get("dims_raw", {}).items():
                vals[role].append(v)
        if not vals or not fam:
            continue
        u, share, shares = SR.infer_unit(r["family"], vals)
        if shares.get(fam["unit"], 0.0) < 1.0:
            r["unit_conflict"] = {"table_unit": fam["unit"], "row_fits": u, "row_share_in_table_unit":
                                  shares.get(fam["unit"], 0.0)}
            warnings.append(f"{r['family']} {r['mark']}: text row sizes do not fit the table unit {fam['unit']} "
                            f"(fit {u}); row held")


# ------------------------------------------------------------------ what the reading means for plan occurrences
UPPER = ("GF", "1F", "2F", "3F", "ROOF")


def type_kind(row):
    """COLUMN schedule row -> NECK_ONLY (FOUNDATION present, every upper storey of the table STRUCK) /
    HAS_UPPER / HELD (with why) / None (no cell status: the row came from no table this reader saw)."""
    cs = (row or {}).get("cell_status")
    if not cs:
        return None, "no cell status"
    if row.get("unit_conflict"):
        return "HELD", "text row unit conflicts with the table"
    found = cs.get("FOUNDATION", {}).get("status")
    upper = {s: v["status"] for s, v in cs.items() if s in UPPER}
    if any(v == "PRESENT" for v in upper.values()):
        return "HAS_UPPER", None
    if found == "PRESENT" and upper and all(v == "STRUCK" for v in upper.values()):
        return "NECK_ONLY", "every level above the foundation struck out on the schedule"
    return "HELD", "schedule cells not readable: " + held_levels(row)


def held_levels(row):
    """the storeys of a row whose cells cannot be read (blank, half-filled, struck with a value), as text."""
    cs = (row or {}).get("cell_status") or {}
    return ", ".join(f"{s} {v['status']}" for s, v in sorted(cs.items())
                     if v["status"] in ("EMPTY", "MISSING_CELL", "CONFLICT"))


def classify(detected, ext):
    """detected: generic_route.detect(...) output (sheets -> columns); ext: read(...). -> census lines, one per column
    occurrence of a type whose reading this reader changes or confirms (a text row, or a struck storey)."""
    lib, u = ext["lib"], detected.get("unit_m")
    out = []
    for sid, rec in sorted(detected["sheets"].items()):
        role = rec["sheet"]["role"]
        if role not in ("COLUMN_PLAN", "FOUNDATION_PLAN"):
            continue
        for o in rec.get("columns", []):
            row = lib.get(("COLUMN", o["mark"]))
            if row is None:
                if ("COLUMN", o["mark"]) in lib:
                    out.append(_line(o, sid, role, "HELD", "SCHEDULE_CONFLICT", "two schedule rows disagree"))
                continue
            text_row = row.get("form") == "TEXT_ROW"
            struck = sorted(s for s, v in (row.get("cell_status") or {}).items() if v["status"] == "STRUCK")
            if not text_row and not struck:
                continue
            kind, why = type_kind(row)
            band = (row.get("by_storey") or {}).get("FOUNDATION") or {}
            sec = band.get("dims_m") or {}
            area = sec["W"] * sec["H"] if sec.get("W") and sec.get("H") else None
            if not text_row:                 # an attribute row read before: only the struck levels are new evidence
                out.append(_line(o, sid, role, "UNCHANGED", "STRUCK_LEVELS_NOT_PRESENT",
                                 "levels struck out on the schedule: " + ", ".join(struck), struck=struck,
                                 text_row=False))
                continue
            if role == "COLUMN_PLAN":
                if kind == "NECK_ONLY":
                    out.append(_line(o, sid, role, "NOT_PRESENT", "NECK_ONLY_TYPE",
                                     f"schedule row {o['mark']}: {why}; the plan symbol is the neck, measured on the "
                                     "foundation plan", struck=struck, text_row=text_row))
                elif kind == "HAS_UPPER":
                    held = held_levels(row)
                    out.append(_line(o, sid, role, "PARTLY_HELD" if held else "SCHEDULE_ROW_READ", "TEXT_ROW_READ",
                                     "row read from text" + ("; levels struck out: " + ", ".join(struck) if struck
                                                             else "") + ("; held levels: " + held if held else ""),
                                     struck=struck, text_row=True))
                else:
                    out.append(_line(o, sid, role, "HELD", "SCHEDULE_CELLS", why, struck=struck, text_row=text_row))
            else:
                if area and kind != "HELD":
                    out.append(_line(o, sid, role, "HELD", "FOUNDATION_DATUM_NOT_VERIFIED",
                                     "neck section from the schedule; height waits on the founding level (owner Q-21 "
                                     "= C)", section_m=[sec["W"], sec["H"]], section_m2=round(area, 6),
                                     struck=struck, text_row=text_row))
                else:
                    out.append(_line(o, sid, role, "HELD", "NECK_SECTION_NOT_READ", why or "no foundation band",
                                     struck=struck, text_row=text_row))
    return out


def _line(o, sid, role, status, code, why, **kw):
    return dict({"member_id": o["member_id"], "sheet": sid, "role": role, "mark": o["mark"],
                 "before_in_schedule": bool(o.get("in_schedule")), "status": status, "code": code, "why": why}, **kw)


def policy_record():
    return {"policy": POLICY_ID, "beside": SR.POLICY_ID,
            "rule": "schedule rows typed as TEXT / MTEXT inside a block-attribute table are read by drawn position; "
                    "a cell is 'none at this level' only where a strike-out line is drawn; blank or half-filled "
                    "cells stay held; never 0"}
