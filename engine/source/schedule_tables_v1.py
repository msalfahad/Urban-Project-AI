"""SCHEDULE TABLES (V1) - schedule-first structure: a structural schedule read as a TABLE, its marks bound to plan
symbols, quantity = count x B x D x H (owner ACCURACY_PLAN_2026-11-14 change B; T-784). Generic, no project data.

Beside the frozen SCHEDULE_READER_V1 (engine/source/schedule_reader.py, read only, never edited): that reader takes
attribute rows and axis-aligned text tables; this module adds
  read_text_table   a TEXT / MTEXT grid at ANY rotation (the table's own frame is the median text rotation; every
                    text is rotated into it), header words fix the columns: mark, B / W, D / L, H / T / DEPTH, and a
                    level range (FROM / TO, or one LEVEL cell 'a - b' / 'a to b'). One row = one mark.
  rows_from_reader  the frozen reader's attribute-row output normalised to the same row record, per storey band.
  bind              each mark bound to plan symbols. The PLAN gives count (and length) only; the SCHEDULE gives the
                    section. Lesson T-778 (Checker-verified C11 / F3): a mark tagged once may be drawn more than once,
                    so drawn outlines are counted, not tags:
                      TAGGED                 a tag whose nearest free outline (centre within tol) has the schedule size
                      TAGGED_SIZE_CONFLICT   the nearest outline has another size: counted, quantity by the schedule
                                             ('schedule governs a column'), the pair goes to the designer list
                      TAG_ONLY               a tag with no outline within tol: counted on the tag, listed
                      DRAWN_UNTAGGED         an untagged outline whose size fits exactly ONE schedule mark: counted
                      AMBIGUOUS_OUTLINE      an untagged outline fitting several marks: not counted, listed (HELD)
                      UNSCHEDULED_OUTLINE    an outline fitting no mark: listed
                      NOT_IN_SCHEDULE        a tag whose mark has no schedule row: listed
                      NO_PLAN_SYMBOL         a schedule row with no plan symbol: quantity None (HELD), never 0
  quantities        count x B x D x H per mark; a missing dimension or height -> volume None (HELD), never 0.

Designer list (no owner question): every TAGGED_SIZE_CONFLICT, TAG_ONLY, AMBIGUOUS_OUTLINE, UNSCHEDULED_OUTLINE,
NOT_IN_SCHEDULE and NO_PLAN_SYMBOL record. Rules: company default 'schedule governs a column' (owner 2026-11-13),
UP-QTY-STATUS-001 (held never 0), UP-QTY-MATERIALITY-001 (applied downstream, not here).
"""

from __future__ import annotations

import math
import re
from collections import defaultdict

from engine.source import drawing_model as DM
from engine.source import schedule_reader as SR

POLICY_ID = "SCHEDULE_TABLES_V1"
MARK_WORDS = ("MARK", "TYPE", "NAME", "REF", "TAG", "ID", "النوع", "الرمز")
HEAD_ROLES = {
    "B": ("B", "W", "WIDTH", "BREADTH", "BR", "عرض", "العرض"),
    "D": ("D", "L", "LENGTH", "LEN", "طول", "الطول"),
    "H": ("H", "T", "THK", "THICK", "THICKNESS", "DEPTH", "DEPHT", "HEIGHT", "HT", "عمق", "سمك", "ارتفاع"),
    "LEVEL_FROM": ("FROM", "LEVEL FROM", "BOTTOM LEVEL", "BOT LEVEL", "من"),
    "LEVEL_TO": ("TO", "LEVEL TO", "TOP LEVEL", "الى", "إلى"),
    "LEVEL": ("LEVEL", "LEVELS", "LEVEL RANGE", "منسوب"),
}
COUNTED = ("TAGGED", "TAGGED_SIZE_CONFLICT", "TAG_ONLY", "DRAWN_UNTAGGED")
DESIGNER = ("TAGGED_SIZE_CONFLICT", "TAG_ONLY", "AMBIGUOUS_OUTLINE", "UNSCHEDULED_OUTLINE", "NOT_IN_SCHEDULE",
            "NO_PLAN_SYMBOL")
_NUM = r"[-+]?[0-9]+(?:[.,][0-9]+)?"


def _f(t):
    m = re.fullmatch(r"\s*(" + _NUM + r")\s*", t or "")
    return float(m.group(1).replace(",", ".")) if m else None


def table_angle(texts):
    """the table's own rotation (degrees): the circular mean of the text rotations (reading direction, full circle:
    a table drawn upside down reads at 180, never folded onto 0)."""
    if not texts:
        return 0.0
    sx = sum(math.cos(math.radians(t.get("rotation") or 0.0)) for t in texts)
    sy = sum(math.sin(math.radians(t.get("rotation") or 0.0)) for t in texts)
    return math.degrees(math.atan2(sy, sx)) if (sx or sy) else 0.0


def to_local(texts, angle_deg):
    """rotate every text into the table frame (rows along local x)."""
    r = math.radians(-angle_deg)
    c, s = math.cos(r), math.sin(r)
    return [dict(t, lx=t["x"] * c - t["y"] * s, ly=t["x"] * s + t["y"] * c) for t in texts]


def _head_role(word):
    u = re.sub(r"\(.*?\)", "", DM.normalize(word)).upper().strip().rstrip(".:")
    if u in MARK_WORDS:
        return "MARK"
    for role, words in HEAD_ROLES.items():
        if u in (w.upper() for w in words):
            return role
    return None


def _level_range(cell):
    m = re.fullmatch(r"\s*(" + _NUM + r")\s*(?:-|–|TO|to|/|\.\.)\s*(" + _NUM + r")\s*", cell or "")
    return (float(m.group(1).replace(",", ".")), float(m.group(2).replace(",", "."))) if m else None


def read_text_table(texts, *, row_tol, col_pad=0.0, unit_m=None):
    """texts: [{value, x, y, rotation?}] of ONE schedule region -> {rows, warnings, angle_deg, unit}.

    unit_m: the unit of the printed sizes in metres when the drawing states it; None -> inferred per family by the
    frozen reader's plausibility test and recorded as an inference. Level values are taken in metres as printed."""
    T = [t for t in texts if DM.normalize(t.get("value", ""))]
    ang = table_angle(T)
    L = to_local(T, ang)
    lines = []
    for t in sorted(L, key=lambda t: (-t["ly"], t["lx"])):
        for ln in lines:
            if abs(ln["y"] - t["ly"]) <= row_tol:
                ln["t"].append(t)
                break
        else:
            lines.append({"y": t["ly"], "t": [t]})
    header = None
    for i, ln in enumerate(lines):
        roles = {}
        for t in ln["t"]:
            r = _head_role(t["value"])
            if r:
                roles[t["lx"]] = r
        if "MARK" in roles.values() and len(roles) >= 2:
            header = (i, sorted(roles.items()))
            break
    if header is None:
        return {"policy": POLICY_ID, "rows": [], "warnings": ["no header row with a mark word"], "angle_deg": ang}
    hi, cols = header
    xs = [x for x, _ in cols]
    edges = [(-1e18 if k == 0 else (xs[k - 1] + xs[k]) / 2.0, 1e18 if k == len(xs) - 1 else (xs[k] + xs[k + 1]) / 2.0)
             for k in range(len(xs))]
    rows, warnings, fam_vals = [], [], defaultdict(lambda: defaultdict(list))
    for ln in lines[hi + 1:]:
        cell = defaultdict(list)
        for t in sorted(ln["t"], key=lambda t: t["lx"]):
            for (x, role), (lo, up) in zip(cols, edges):
                if lo - col_pad <= t["lx"] < up + col_pad:
                    cell[role].append(DM.normalize(t["value"]))
                    break
        if "MARK" not in cell:
            continue
        raw = {k: " ".join(v) for k, v in cell.items()}
        for mk in [m.strip() for m in re.split(r"[/,]", raw["MARK"]) if m.strip()]:
            fam, mark = DM.mark_family(mk)
            if fam is None:
                warnings.append(f"row mark {mk!r} matches no member family: not read")
                continue
            dims = {}
            for role in ("B", "D", "H"):
                v = _f(raw.get(role))
                if v is None and role == "B":
                    m = re.fullmatch(r"\s*(" + _NUM + r")\s*[xX×*]\s*(" + _NUM + r")\s*", raw.get("B", ""))
                    if m:
                        dims["B"], dims["D"] = float(m.group(1)), float(m.group(2))
                        continue
                if v is not None:
                    dims.setdefault(role, v)
            lv = None
            if "LEVEL_FROM" in raw or "LEVEL_TO" in raw:
                a, b = _f(raw.get("LEVEL_FROM")), _f(raw.get("LEVEL_TO"))
                lv = (a, b) if a is not None and b is not None else None
            elif "LEVEL" in raw:
                lv = _level_range(raw["LEVEL"])
            rows.append({"mark": mark, "family": fam, "dims_raw": dims, "level": lv, "raw": raw,
                         "source": f"TEXT_TABLE local y={ln['y']:.3f}"})
            for role, v in dims.items():
                fam_vals[fam]["W" if role == "B" else ("H" if role == "D" else "D")].append(v)
    units = {}
    for fam, vals in fam_vals.items():
        if unit_m:
            units[fam] = {"unit_m": unit_m, "basis": "STATED"}
        else:
            u, share, _ = SR.infer_unit(fam, vals)
            units[fam] = {"unit_m": SR.UNITS_M[u], "basis": "INFERRED_FROM_PLAUSIBLE_MEMBER_SIZES",
                          "plausible_share": round(share, 3)}
            if share < 0.8:
                warnings.append(f"{fam}: no unit fits the schedule values cleanly (best {u}, {share:.0%})")
    for r in rows:
        u = units.get(r["family"], {}).get("unit_m")
        r["dims_m"] = {k: v * u for k, v in r["dims_raw"].items()} if u else {}
        if r["level"] and "H" not in r["dims_m"]:
            r["dims_m"]["H"] = round(r["level"][1] - r["level"][0], 6)
            r["h_basis"] = "LEVEL_RANGE"
    return {"policy": POLICY_ID, "rows": rows, "warnings": warnings, "angle_deg": round(ang, 6), "units": units}


def rows_from_reader(sched, *, band=None, families=None):
    """the frozen reader's rows -> table rows. band: a storey key of by_storey ('FOUNDATION', 'GF', ...) for banded
    schedules (columns / necks); None takes the row's own dims. W -> B, H -> D (section), D (footing depth) -> H."""
    out = []
    for r in sched["rows"]:
        if families and r["family"] not in families:
            continue
        dm = (r["by_storey"].get(band) or {}).get("dims_m", {}) if band else r.get("dims_m", {})
        dims = {}
        if "W" in dm:
            dims["B"] = dm["W"]
        if "H" in dm:
            dims["D"] = dm["H"]
        if "D" in dm and r["family"] == "FOOTING":
            dims["H"] = dm["D"]
        out.append({"mark": r["mark"], "family": r["family"], "dims_m": dims, "level": None, "band": band,
                    "source": r["source"]})
    return out


def _size_fit(row, a, b, size_tol):
    d = row["dims_m"]
    if "B" not in d or "D" not in d:
        return False
    p, q = sorted((d["B"], d["D"]))
    return abs(p - min(a, b)) <= size_tol and abs(q - max(a, b)) <= size_tol


def bind(rows, tags, outlines, *, tol, size_tol, unit_m=1.0, carried=False):
    """rows: table rows (dims in metres); tags: [{mark, x, y}] (a 'C3/F3' tag is split; only marks of the rows'
    families are bound); outlines: [{id, cx, cy, a, b}] in drawing units (a, b = side lengths). tol in drawing
    units, size_tol in metres. carried=True: the tags were carried from another plan (align_offset), so a tag is
    evidence of a MARK, never of a member: a carried tag with no outline is CARRIED_TAG_NO_OUTLINE (not counted,
    not listed) and a carried mark with no row in this band is dropped (its outline goes the untagged way).
    -> {by_mark, records, designer}."""
    lib = {}
    dup = set()
    for r in rows:
        if r["mark"] in lib and lib[r["mark"]]["dims_m"] != r["dims_m"]:
            dup.add(r["mark"])
        lib.setdefault(r["mark"], r)
    fams = {r["family"] for r in rows}
    free = {o["id"]: o for o in outlines}
    recs = []
    marks = []
    for t in tags:
        for mk in [m.strip() for m in re.split(r"[/,]", DM.normalize(t["mark"])) if m.strip()]:
            fam, mark = DM.mark_family(mk)
            if mark in lib or (fam in fams and not carried):
                marks.append((mark, t))
    s_tol = size_tol
    pairs = []
    for i, (mark, t) in enumerate(marks):
        for o in outlines:
            dist = math.hypot(o["cx"] - t["x"], o["cy"] - t["y"])
            if dist <= tol:
                fit = mark in lib and _size_fit(lib[mark], o["a"] * unit_m, o["b"] * unit_m, s_tol)
                pairs.append((not fit, dist, i, o["id"]))
    done = set()
    for nofit, dist, i, oid in sorted(pairs):
        if i in done or oid not in free:
            continue
        mark, t = marks[i]
        if mark not in lib:
            continue
        done.add(i)
        free.pop(oid)
        o = next(x for x in outlines if x["id"] == oid)
        recs.append({"mark": mark, "status": "TAGGED_SIZE_CONFLICT" if nofit else "TAGGED", "outline": oid,
                     "tag_xy": (t["x"], t["y"]), "dist": round(dist, 6),
                     "size_m": (round(o["a"] * unit_m, 4), round(o["b"] * unit_m, 4))})
    for i, (mark, t) in enumerate(marks):
        if i in done:
            continue
        st = ("CARRIED_TAG_NO_OUTLINE" if carried else "TAG_ONLY") if mark in lib else "NOT_IN_SCHEDULE"
        recs.append({"mark": mark, "status": st, "outline": None, "tag_xy": (t["x"], t["y"])})
    for oid, o in sorted(free.items(), key=lambda kv: str(kv[0])):
        fits = sorted(m for m, r in lib.items() if _size_fit(r, o["a"] * unit_m, o["b"] * unit_m, s_tol))
        if len(fits) == 1:
            recs.append({"mark": fits[0], "status": "DRAWN_UNTAGGED", "outline": oid})
        else:
            recs.append({"mark": None, "status": "AMBIGUOUS_OUTLINE" if fits else "UNSCHEDULED_OUTLINE",
                         "outline": oid, "candidates": fits,
                         "size_m": (round(o["a"] * unit_m, 4), round(o["b"] * unit_m, 4))})
    by = defaultdict(lambda: defaultdict(int))
    for r in recs:
        if r["mark"] and r["status"] in COUNTED:
            by[r["mark"]][r["status"]] += 1
    by_mark = {}
    for mark, row in sorted(lib.items()):
        c = dict(by.get(mark, {}))
        n = sum(c.values())
        by_mark[mark] = {"family": row["family"], "count": n if n else None, "by_status": c,
                         "status": "NO_PLAN_SYMBOL" if not n else ("SOURCE_CONFLICT_DUPLICATE_MARK" if mark in dup
                                                                    else "BOUND")}
    for r in recs:
        if r["status"] == "NOT_IN_SCHEDULE":
            by_mark.setdefault(r["mark"], {"family": None, "count": None, "by_status": {}, "status": "NOT_IN_SCHEDULE"})
    designer = [dict(r) for r in recs if r["status"] in DESIGNER]
    designer += [{"mark": m, "status": "NO_PLAN_SYMBOL", "outline": None} for m, v in by_mark.items()
                 if v["status"] == "NO_PLAN_SYMBOL"]
    designer += [{"mark": m, "status": "SOURCE_CONFLICT_DUPLICATE_MARK"} for m in sorted(dup)]
    return {"policy": POLICY_ID, "by_mark": by_mark, "records": recs, "designer": designer}


def quantities(rows, bound, *, height_m=None):
    """count x B x D x H per mark. height_m: {mark: H} or a number for a banded schedule whose rows print no height
    (the storey height of that band, labelled by the caller). Missing count / dimension -> volume None (HELD)."""
    lib = {}
    for r in rows:
        lib.setdefault(r["mark"], r)
    out, total = [], 0.0
    held = []
    for mark, b in sorted(bound["by_mark"].items()):
        r = lib.get(mark)
        d = dict(r["dims_m"]) if r else {}
        h_basis = r.get("h_basis", "SCHEDULE") if r and "H" in d else None
        if r and "H" not in d and height_m is not None:
            h = height_m.get(mark) if isinstance(height_m, dict) else height_m
            if h is not None:
                d["H"], h_basis = h, "CALLER_HEIGHT"
        missing = [k for k in ("B", "D", "H") if k not in d]
        n = b["count"]
        vol = None
        if r and n and not missing and b["status"] == "BOUND":
            vol = round(n * d["B"] * d["D"] * d["H"], 6)
            total += vol
        else:
            held.append(mark)
        out.append({"mark": mark, "family": b["family"], "count": n, "B": d.get("B"), "D": d.get("D"),
                    "H": d.get("H"), "h_basis": h_basis, "volume_m3": vol, "status": b["status"],
                    "missing": missing, "by_status": b["by_status"]})
    return {"policy": POLICY_ID, "lines": out, "total_m3": round(total, 6), "held_marks": held}


def align_offset(src, dst, *, snap, min_share=0.5):
    """the translation that carries a TAGGED plan's outlines onto an UNTAGGED plan of the same grid (an upper storey
    drawn beside the setting-out plan): the most voted (dx, dy) over all centre pairs, snapped to `snap` drawing
    units. Accepted only when at least min_share of the smaller plan's outlines land on an outline of the other
    (within snap); otherwise None (no tag is carried over, nothing is inferred)."""
    if not src or not dst:
        return None
    votes = defaultdict(int)
    for a in src:
        for b in dst:
            votes[(round((b["cx"] - a["cx"]) / snap), round((b["cy"] - a["cy"]) / snap))] += 1
    (kx, ky), _ = max(votes.items(), key=lambda kv: (kv[1], -abs(kv[0][0]) - abs(kv[0][1])))
    dx, dy = kx * snap, ky * snap
    hit = sum(1 for a in src if any(math.hypot(b["cx"] - a["cx"] - dx, b["cy"] - a["cy"] - dy) <= snap for b in dst))
    share = hit / min(len(src), len(dst))
    return {"dx": dx, "dy": dy, "matched": hit, "share": round(share, 4)} if share >= min_share else None


def policy_record():
    return {"policy": POLICY_ID, "forms": ["TEXT_TABLE (any rotation)", "ATTRIBUTE_ROWS via SCHEDULE_READER_V1"],
            "rule": "the schedule gives the section, the plan gives the count (drawn outlines, not tags); "
                    "unbound or conflicting symbols go to the designer list; held never 0"}
