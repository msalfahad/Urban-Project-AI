"""BEAM REBAR COMPLETENESS SAFEGUARD V1 (task T-300) - detects and flags the beam reinforcement components that the
route G schedule reader does not carry: beam SIDE reinforcement (remark / MIDDLE REINT. columns), NESTED (multi-leg)
links and continuous-beam TOP CORNER bars. An unwired, opt-in producer (owner Stage C, 2026-10-25 11:51, safeguard
only): nothing in engine/ or tools/ imports it; no frozen module, released V2.9 cell or measured bar group changes.

Physical elements.
    SIDE_BARS     longitudinal bars on the vertical faces of a deep beam, between the top and bottom groups; printed as
                  a remark ('2Ø12/30cm') beside the row, or governed by a general note (e.g. 'side bars in beams deeper
                  than D unless stated otherwise'). One component per beam row.
    NESTED_LINKS  links inside the outer link (multi-leg shear reinforcement); printed as a link symbol of two or more
                  closed loops in the row. One component per beam row.
    TOP_CORNER    the top bars along a span of a continuous beam between the support bars; printed as a bar callout in
                  the span's column of the row (model-space text, not an attribute). One component per span. A simple
                  beam's top bars are its TOP attribute (already measured): the component is NOT_REQUIRED there.

Statuses per component (never a default, never 0):
    DETECTED       drawing evidence found and associated with exactly one row (handles / positions recorded)
    NOT_REQUIRED   evidence that the component does not apply (the evidence is named)
    UNRESOLVED     neither: the quantity is HELD with a BLANK value
A DETECTED component carries kg only when every input is supplied as printed (count, diameter, length and, for a
spaced notation, its count basis) through printed_inputs; otherwise kg is blank and the component is HELD. A beam is
COMPLETE only when every component is NOT_REQUIRED or DETECTED with kg, and no callout in its row is unclassified.

Text association (recorded in the result): rows of one schedule table (same sheet, attribute tag set and mark column)
are bands along the table's row axis (y), bounded half-way between neighbouring row anchors (the mark attribute); the
outer rows take half the neighbouring pitch. A text or symbol within max(its height, 5 % of the local pitch) of a band
boundary, or outside every band, is AMBIGUOUS and is never assigned. Texts owned by a row insert are the row's own
attribute glyphs and never a new bar group; a model-space callout lying on an attribute slot is the slot's glyph
(SLOT_GLYPH, ignored) - or, when that slot is empty, a FLAGGED value the reader drops (EMPTY_SLOT_TEXT_VALUE).

Generic: no project name, mark, coordinate, layer or handle in this module. Stdlib + engine.source helpers.
"""

from __future__ import annotations

import copy
import hashlib
import json
import re
from collections import defaultdict

from engine.source import drawing_model as DM
from engine.source import rebar_unit_mass as RUM
from engine.source import schedule_reader as SR

POLICY_ID = "BEAM_REBAR_COMPLETENESS_V1"
METHOD_ID = "BEAM_REBAR_COMPLETENESS_SAFEGUARD_V1"
DETECTED, NOT_REQUIRED, UNRESOLVED = "DETECTED", "NOT_REQUIRED", "UNRESOLVED"
STATUSES = (DETECTED, NOT_REQUIRED, UNRESOLVED)
COMPLETE, INCOMPLETE = "COMPLETE", "INCOMPLETE"
KINDS = ("SIDE_BARS", "NESTED_LINKS", "TOP_CORNER")
BEAM_FAMILIES = ("BEAM", "CONTINUOUS_BEAM")
SIDE_HEADER_WORDS = ("MIDDLE", "REINT", "REINT.", "SIDE", "REMARK", "REMARKS", "ملاحظات", "جانبي")
BOUNDARY_FRACTION = 0.05          # ambiguity band around a row boundary, fraction of the local pitch
JOIN_GAP_H = 3.0                  # split callout pieces on one baseline joined when the gap <= 3 text heights
CORNER_RISE_H = 1.5               # a corner callout lies above every bar slot of the row by more than 1.5 heights
SLOT_PAD_H = 1.5                  # slot footprint: the B..D attribute span padded by 1.5 text heights
CALLOUT = re.compile(r"^(\d+)\s*Ø\s*(\d+)\s*(?:/\s*(\d+(?:\.\d+)?)\s*(cm|mm|m)\b\.?)?\s*$", re.I)
RATE = re.compile(r"^(\d+)\s*Ø\s*(\d+)\s*/\s*m\s*$", re.I)
SPACING_PIECE = re.compile(r"^/?\s*(\d+(?:\.\d+)?)\s*(cm|mm)\s*$", re.I)


class SafeguardError(ValueError):
    pass


# ------------------------------------------------------------------ helpers
def _own(v):
    """'D2:10321' / 'INSERT 10321' / '10321' -> '10321'."""
    s = str(v or "")
    if s.startswith("INSERT "):
        s = s[7:]
    return s[3:] if s.startswith("D2:") else s


def _h(t, default):
    try:
        h = float(t.get("height") or 0.0)
    except (TypeError, ValueError):
        h = 0.0
    return h if h > 0 else default


def measured_digest(rows):
    """sha256 of every measured bar group the schedule reader carries (rows' bars and per-storey bars)."""
    out = []
    for r in rows:
        out.append([r.get("family"), r.get("mark"), r.get("source"),
                    [(b.get("role"), b.get("count"), b.get("dia_mm"), b.get("per_m")) for b in r.get("bars") or []],
                    sorted((k, [(b.get("role"), b.get("count"), b.get("dia_mm")) for b in v.get("bars") or []])
                           for k, v in (r.get("by_storey") or {}).items())])
    return hashlib.sha256(json.dumps(out, sort_keys=True, default=str).encode()).hexdigest()


def assert_measured_unchanged(digest_before, rows_after):
    """A measured bar group may never be altered by this safeguard: raises when the digest moved."""
    now = measured_digest(rows_after)
    if now != digest_before:
        raise SafeguardError(f"measured bar groups changed ({digest_before[:12]} -> {now[:12]}): refused")
    return True


# ------------------------------------------------------------------ tables and row bands
def _tables(rows, attrs_by_owner, families):
    """{table_key: [row records]}: rows of one sheet with one tag set and one mark column (x of the mark attribute)."""
    out = defaultdict(list)
    for r in rows:
        own = _own(r.get("source"))
        a = attrs_by_owner.get(own, {})
        mt = r.get("mark_tag")
        if mt not in a:
            continue
        x, y = a[mt]["x"], a[mt]["y"]
        out[(r.get("sheet"), tuple(r.get("tag_set") or ()), mt)].append(
            {"row": r, "owner": own, "anchor": (x, y), "evaluate": r.get("family") in families})
    tables = {}
    for k, rs in out.items():
        # one table = one mark column: split the group at x gaps larger than the row heights could explain
        rs.sort(key=lambda e: e["anchor"][0])
        cols, cur = [], [rs[0]]
        for e in rs[1:]:
            if abs(e["anchor"][0] - cur[-1]["anchor"][0]) > 1e-6 * max(1.0, abs(e["anchor"][0])) + 1e-3:
                cols.append(cur)
                cur = [e]
            else:
                cur.append(e)
        cols.append(cur)
        for i, c in enumerate(cols):
            tables[(k[0], k[1], k[2], i)] = sorted(c, key=lambda e: -e["anchor"][1])
    return tables


def _bands(tab):
    """Row bands (top -> bottom) {lo, hi, pitch_lo, pitch_hi}; None for a single-row table (no pitch)."""
    if len(tab) < 2:
        return None
    ys = [e["anchor"][1] for e in tab]
    if len(set(round(y, 6) for y in ys)) != len(ys):
        return None
    out = []
    for i, y in enumerate(ys):
        up = (ys[i - 1] - y) if i > 0 else (y - ys[i + 1])
        dn = (y - ys[i + 1]) if i + 1 < len(ys) else (ys[i - 1] - y)
        out.append({"hi": y + up / 2.0, "lo": y - dn / 2.0, "pitch_up": up, "pitch_dn": dn})
    return out


def _grid_bands(tab, segs, x_lo, x_hi):
    """Row bands from the table's own horizontal grid lines (each spanning at least 80 % of the table's attribute
    width): the nearest line above and below each row anchor. None unless every row has its own band (one anchor per
    band, no band shared)."""
    need = 0.8 * (x_hi - x_lo)
    lines = [s for s in segs if abs(s["a"][1] - s["b"][1]) <= 1e-6 * max(1.0, abs(s["a"][1]))
             and min(max(s["a"][0], s["b"][0]), x_hi) - max(min(s["a"][0], s["b"][0]), x_lo) >= need > 0]
    ys = sorted({round(s["a"][1], 6) for s in lines})
    if len(ys) < 2:
        return None
    out = []
    for e in tab:
        y = e["anchor"][1]
        above = [g for g in ys if g > y]
        below = [g for g in ys if g < y]
        if not above or not below:
            return None
        hi, lo = min(above), max(below)
        out.append({"hi": hi, "lo": lo, "pitch_up": hi - lo, "pitch_dn": hi - lo})
    keys = [(b["lo"], b["hi"]) for b in out]
    if len(set(keys)) != len(keys):
        return None
    ext = (min(min(s["a"][0], s["b"][0]) for s in lines), max(max(s["a"][0], s["b"][0]) for s in lines))
    for b in out:
        b["x_extent"] = ext
    return out


def _locate(y, half_h, bands, frac=BOUNDARY_FRACTION):
    """(row index or None, state, distance to the nearest boundary). half_h: half the extent of the item in y."""
    best = None
    for i, b in enumerate(bands):
        tol_hi = max(half_h, frac * b["pitch_up"])
        tol_lo = max(half_h, frac * b["pitch_dn"])
        if b["lo"] + tol_lo < y < b["hi"] - tol_hi:
            return i, "ASSIGNED", round(min(y - b["lo"], b["hi"] - y), 6)
        if b["lo"] - tol_lo <= y <= b["hi"] + tol_hi:
            best = (None, "AMBIGUOUS_BOUNDARY", round(min(abs(y - b["lo"]), abs(b["hi"] - y)), 6))
    return best or (None, "NO_MEMBER", None)


# ------------------------------------------------------------------ callouts
def _callouts(texts, excluded_owners):
    """Model-space bar callouts and spacing pieces: split pieces on one baseline joined (count, Ø, diameter)."""
    pool = [dict(t, norm=DM.normalize(t.get("value"))) for t in texts if _own(t.get("owner")) not in excluded_owners]
    pool = [t for t in pool if t["norm"]]
    pool.sort(key=lambda t: (round(t["y"], 3), t["x"]))
    used, out = set(), []
    for i, t in enumerate(pool):
        if i in used or "Ø" not in t["norm"] and not re.fullmatch(r"\d+", t["norm"]):
            continue
        h = _h(t, 1.0)
        line = [j for j, u in enumerate(pool) if j not in used and abs(u["y"] - t["y"]) <= 0.5 * h]
        line.sort(key=lambda j: pool[j]["x"])
        k = line.index(i)
        run = [line[k]]
        a = k
        while a > 0 and pool[line[a]]["x"] - pool[line[a - 1]]["x"] <= JOIN_GAP_H * h:
            a -= 1
            run.insert(0, line[a])
        b = k
        while b + 1 < len(line) and pool[line[b + 1]]["x"] - pool[line[b]]["x"] <= JOIN_GAP_H * h:
            b += 1
            run.append(line[b])
        joined = " ".join(pool[j]["norm"] for j in run)
        if "Ø" not in joined:
            continue
        used.update(run)
        pieces = [pool[j] for j in run]
        m = CALLOUT.match(joined)
        rec = {"text": joined, "ids": [p.get("id") for p in pieces], "x0": pieces[0]["x"], "x1": pieces[-1]["x"],
               "x": (pieces[0]["x"] + pieces[-1]["x"]) / 2.0, "y": sum(p["y"] for p in pieces) / len(pieces),
               "h": max(_h(p, 1.0) for p in pieces), "sheet": pieces[0].get("sheet")}
        if RATE.match(joined):
            rec.update(kind="RATE", count=int(RATE.match(joined)[1]), dia_mm=int(RATE.match(joined)[2]))
        elif m:
            sp = None
            if m[3]:
                sp = {"value": float(m[3]), "unit": m[4].lower(), "printed": "INLINE"}
            rec.update(kind="CALLOUT", count=int(m[1]), dia_mm=int(m[2]), spacing=sp)
        elif joined.strip() == "Ø":
            rec.update(kind="LONE_GLYPH")
        else:
            rec.update(kind="UNPARSED")
        out.append(rec)
    for t in pool:
        m = SPACING_PIECE.match(t["norm"])
        if m and not re.search(r"[A-Za-z]{3,}", t["norm"]):
            out.append({"kind": "SPACING_PIECE", "text": t["norm"], "ids": [t.get("id")], "x0": t["x"], "x1": t["x"],
                        "x": t["x"], "y": t["y"], "h": _h(t, 1.0), "sheet": t.get("sheet"),
                        "spacing": {"value": float(m[1]), "unit": m[2].lower()}})
    return out


def _slots(row, attrs):
    """Bar slots of a row: [{role, xb, xd, y, filled, count_tag, dia_tag}] from the attribute pairs of its tag set."""
    stems = [SR._split_tag(t)[1] for t in row.get("tag_set") or ()]
    out = []
    for base, cs, ds in SR._bar_pairs(stems):
        if cs not in attrs or ds not in attrs:
            continue
        b, d = attrs[cs], attrs[ds]
        out.append({"role": base, "xb": min(b["x"], d["x"]), "xd": max(b["x"], d["x"]), "y": (b["y"] + d["y"]) / 2.0,
                    "filled": bool(str(b["value"]).strip() and str(d["value"]).strip()),
                    "count_tag": cs, "dia_tag": ds})
    return out


def _on_slot(c, slots):
    h = c["h"]
    for s in slots:
        if s["xb"] - SLOT_PAD_H * h <= c["x"] <= s["xd"] + SLOT_PAD_H * h and abs(c["y"] - s["y"]) <= SLOT_PAD_H * h:
            return s
    return None


# ------------------------------------------------------------------ link symbols
def _loops(segments):
    """Closed 4-segment loops (one polyline entity) -> [{id, box}]."""
    by = defaultdict(list)
    for s in segments:
        sid = str(s.get("id") or "")
        if ":" not in sid:
            continue
        by[sid.rsplit(":", 1)[0]].append(s)
    out = []
    for stem, ss in by.items():
        if len(ss) != 4:
            continue
        pts = [tuple(round(c, 6) for c in p) for s in ss for p in (s["a"], s["b"])]
        if any(pts.count(p) != 2 for p in pts):
            continue
        xs, ys = [p[0] for p in pts], [p[1] for p in pts]
        out.append({"id": stem, "box": (min(xs), min(ys), max(xs), max(ys)),
                    "path": list(ss[0].get("path") or [])})
    return out


def _clusters(loops):
    """Loops whose boxes overlap form one link symbol; loops = number of closed loops in it."""
    n = len(loops)
    parent = list(range(n))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    for i in range(n):
        a = loops[i]["box"]
        for j in range(i + 1, n):
            b = loops[j]["box"]
            if a[0] <= b[2] and b[0] <= a[2] and a[1] <= b[3] and b[1] <= a[3]:
                parent[find(i)] = find(j)
    g = defaultdict(list)
    for i in range(n):
        g[find(i)].append(loops[i])
    out = []
    for ls in g.values():
        box = (min(l["box"][0] for l in ls), min(l["box"][1] for l in ls), max(l["box"][2] for l in ls),
               max(l["box"][3] for l in ls))
        out.append({"loops": len(ls), "box": box, "loop_ids": sorted(l["id"] for l in ls),
                    "inserts": sorted({p for l in ls for p in l["path"][:1]})})
    return sorted(out, key=lambda c: (-c["box"][3], c["box"][0]))


# ------------------------------------------------------------------ evidence records
def _evidence_index(evidence):
    note, nr, link_detail = None, {}, {}
    for e in evidence or ():
        if not e.get("source"):
            raise SafeguardError(f"evidence record without a source: {e}")
        k = e.get("kind")
        if k == "SIDE_BAR_NOTE":
            if e.get("depth_gt_m") is None:
                raise SafeguardError("SIDE_BAR_NOTE needs depth_gt_m (the printed depth threshold)")
            note = e
        elif k == "NOT_REQUIRED":
            if e.get("component") not in KINDS or not e.get("mark"):
                raise SafeguardError(f"NOT_REQUIRED record needs mark and component in {KINDS}: {e}")
            nr[(e.get("family"), e["mark"], e["component"], e.get("span"))] = e
        elif k == "LINK_DETAIL":
            if not e.get("loops"):
                raise SafeguardError("LINK_DETAIL needs loops (the printed number of closed links)")
            link_detail[(e.get("sheet"), e.get("family"))] = e
        else:
            raise SafeguardError(f"unknown evidence kind {k!r}")
    return note, nr, link_detail


def _nr(nr, row, kind, span=None):
    return nr.get((row["family"], row["mark"], kind, span)) or nr.get((None, row["mark"], kind, span))


def _kg(inputs, unit_mass):
    """kg = count x length x kg/m, only when every input is supplied with its source; else None."""
    if not inputs:
        return None, "NO_PRINTED_INPUTS"
    need = ("count", "dia_mm", "length_m", "source")
    miss = [k for k in need if inputs.get(k) in (None, "")]
    if miss:
        return None, "MISSING_INPUT:" + ",".join(miss)
    if inputs.get("spaced_notation") and not inputs.get("count_basis"):
        return None, "MISSING_INPUT:count_basis"
    if float(inputs["count"]) <= 0 or float(inputs["length_m"]) <= 0:
        return None, "NON_POSITIVE_INPUT"
    if unit_mass is None:
        return None, "NO_UNIT_MASS_METHOD"
    return float(inputs["count"]) * float(inputs["length_m"]) * RUM.kg_per_m(float(inputs["dia_mm"]), unit_mass), None


# ------------------------------------------------------------------ main
def evaluate(texts, attributes, segments, rows, *, evidence=(), occurrences=None, printed_inputs=None,
             unit_mass=None, families=BEAM_FAMILIES, header_words=SIDE_HEADER_WORDS):
    """texts: [{id, value, x, y, height, sheet, owner}] (sheet-labelled, e.g. drawing_model texts);
    attributes: [{owner, tag, value, x, y}]; segments: [{id, a, b, sheet?, path}] (loops per polyline entity);
    rows: schedule rows (schedule_reader). evidence: SIDE_BAR_NOTE / NOT_REQUIRED / LINK_DETAIL records, each with
    its source. occurrences: {(family, mark): [{floor, drawing, sheet}]} from the plans. printed_inputs:
    {(mark, kind, span): {count, dia_mm, length_m, source, spaced_notation?, count_basis?}}.
    Returns the per-beam safeguard records; the input rows are never modified (digest checked)."""
    digest_before = measured_digest(rows)
    rows_view = copy.deepcopy(rows)
    note, nr, link_detail = _evidence_index(evidence)
    printed_inputs = printed_inputs or {}
    attrs_by_owner = defaultdict(dict)
    for a in attributes:
        attrs_by_owner[_own(a["owner"])][a["tag"]] = a
    tables = _tables(rows_view, attrs_by_owner, families)
    all_row_owners = {_own(r.get("source")) for r in rows_view}
    beams, unassigned = [], []
    for tkey, tab in sorted(tables.items(), key=lambda kv: str(kv[0])):
        if not any(e["evaluate"] for e in tab):
            continue
        sheet = tkey[0]
        xs = [a["x"] for e in tab for a in attrs_by_owner[e["owner"]].values()]
        width = max(xs) - min(xs)
        xr = (min(xs) - 0.5 * width, max(xs) + 0.5 * width)
        segs = [s for s in segments if s.get("sheet") == sheet]
        bands = _grid_bands(tab, segs, min(xs), max(xs))
        rule = "ROW_GRID_LINES"
        if bands is None:
            bands, rule = _bands(tab), "ROW_PITCH_MIDLINE"
        else:                                    # the table's drawn width (its grid lines) bounds its columns too
            xr = (min(xr[0], bands[0]["x_extent"][0]), max(xr[1], bands[0]["x_extent"][1]))
        top = bands[0]["hi"] + bands[0]["pitch_up"] * BOUNDARY_FRACTION if bands else None
        sheet_texts = [t for t in texts if t.get("sheet") == sheet]
        headers = [dict(t, norm=DM.normalize(t.get("value")).upper()) for t in sheet_texts
                   if top is not None and t["y"] > top and xr[0] <= t["x"] <= xr[1]]
        items = [c for c in _callouts([t for t in sheet_texts if xr[0] <= t["x"] <= xr[1]], all_row_owners)]
        # a link symbol sits inside one row: loops taller than the smallest row band (frames, grid) are not symbols
        max_h = min(b["hi"] - b["lo"] for b in bands) if bands else None
        loops = [lp for lp in _loops(segs) if max_h is None or lp["box"][3] - lp["box"][1] < max_h]
        clusters = [c for c in _clusters(loops) if xr[0] <= (c["box"][0] + c["box"][2]) / 2 <= xr[1]]
        per_row = defaultdict(lambda: {"callouts": [], "pieces": [], "clusters": []})
        assoc_rule = {"rule": rule if bands else "NONE_SINGLE_ROW_TABLE",
                      "boundary_tolerance": f"max(item half height, {BOUNDARY_FRACTION} x band height / pitch)",
                      "table": {"sheet": sheet, "mark_tag": tkey[2], "rows": len(tab)}}
        for c in items:
            if bands is None:
                unassigned.append(dict(c, state="NO_PITCH_SINGLE_ROW_TABLE", table=assoc_rule["table"]))
                continue
            if top is not None and c["y"] > top:
                continue                                                # header area: not a row item
            i, st, dist = _locate(c["y"], c["h"] / 2.0, bands)
            if i is None:
                unassigned.append(dict(c, state=st, boundary_distance=dist, table=assoc_rule["table"]))
                continue
            per_row[i]["pieces" if c["kind"] == "SPACING_PIECE" else "callouts"].append(dict(c, boundary_distance=dist))
        for c in clusters:
            if bands is None:
                unassigned.append({"kind": "LINK_SYMBOL", "state": "NO_PITCH_SINGLE_ROW_TABLE", **c})
                continue
            yc, hh = (c["box"][1] + c["box"][3]) / 2.0, (c["box"][3] - c["box"][1]) / 2.0
            i, st, dist = _locate(yc, hh, bands)
            if i is None:
                if top is None or yc <= top:
                    unassigned.append({"kind": "LINK_SYMBOL", "state": st, "boundary_distance": dist, **c})
                continue
            per_row[i]["clusters"].append(dict(c, boundary_distance=dist))
        symbol_rows = sum(1 for v in per_row.values() if v["clusters"])
        for i, e in enumerate(tab):
            if not e["evaluate"]:
                continue
            beams.append(_row_record(e, i, per_row[i], attrs_by_owner[e["owner"]], headers, symbol_rows, sheet,
                                     tkey, assoc_rule, note, nr, link_detail, printed_inputs, unit_mass, occurrences,
                                     bands))
    assert_measured_unchanged(digest_before, rows)
    assert_measured_unchanged(digest_before, rows_view)
    res = {"policy": POLICY_ID, "method": METHOD_ID, "beams": beams, "unassigned": unassigned,
           "measured_digest": digest_before, "unit_mass": RUM.describe(unit_mass) if unit_mass else None,
           "summary": _summary(beams, unassigned)}
    validate(res)
    return res


def _row_record(e, i, got, attrs, headers, symbol_rows, sheet, tkey, assoc_rule, note, nr, link_detail,
                printed_inputs, unit_mass, occurrences, bands):
    row = e["row"]
    mark, fam = row["mark"], row["family"]
    slots = _slots(row, attrs)
    bar_slots = [s for s in slots]
    flags, comps = [], []
    side_c, corner_c = [], []
    max_slot_y = max((s["y"] for s in bar_slots), default=None)
    max_slot_x = max((s["xd"] for s in bar_slots), default=None)
    bot = sorted([s for s in bar_slots if re.fullmatch(r"(BOT|BOTTOM)(\d+)", s["role"])],
                 key=lambda s: int(re.sub(r"\D", "", s["role"])))
    centres = [((s["xb"] + s["xd"]) / 2.0, int(re.sub(r"\D", "", s["role"]))) for s in bot]
    for c in got["callouts"]:
        ev = {"text": c["text"], "ids": c["ids"], "position": [round(c["x"], 3), round(c["y"], 3)],
              "boundary_distance": c["boundary_distance"]}
        if c["kind"] in ("LONE_GLYPH", "CALLOUT", "RATE"):
            s = _on_slot(c, bar_slots)
            if s is not None:
                if s["filled"]:
                    continue                                            # the slot's own glyph: never a new group
                flags.append({"code": "EMPTY_SLOT_TEXT_VALUE", "slot": s["role"], **ev})
                continue
        if c["kind"] != "CALLOUT":
            flags.append({"code": "UNCLASSIFIED_CALLOUT", "callout_kind": c["kind"], **ev})
            continue
        if max_slot_x is not None and c["x0"] > max_slot_x + c["h"]:
            hdr = min(headers, key=lambda t: abs(t["x"] - c["x0"]), default=None)
            word = hdr["norm"] if hdr else None
            if word and any(w.upper() == word or word.startswith(w.upper()) for w in SIDE_HEADER_WORDS):
                side_c.append(dict(c, header=word, header_dx=round(abs(hdr["x"] - c["x0"]), 3), ev=ev))
            else:
                flags.append({"code": "UNCLASSIFIED_CALLOUT", "reason": f"right of the bar slots under header "
                              f"{word!r}", **ev})
            continue
        if fam == "CONTINUOUS_BEAM" and centres and max_slot_y is not None and c["y"] > max_slot_y + CORNER_RISE_H * c["h"]:
            ds = sorted((abs(c["x"] - x), k) for x, k in centres)
            gaps = [abs(centres[j + 1][0] - centres[j][0]) for j in range(len(centres) - 1)]
            reach = 0.5 * min(gaps) if gaps else None
            if reach is not None and ds[0][0] < reach and (len(ds) < 2 or ds[1][0] >= reach):
                corner_c.append(dict(c, span=ds[0][1], ev=ev))
            else:
                flags.append({"code": "AMBIGUOUS_SPAN_COLUMN", **ev})
            continue
        flags.append({"code": "UNCLASSIFIED_CALLOUT", "reason": "not on a slot, not a side remark, not a corner "
                      "callout", **ev})
    # ---- SIDE_BARS
    depth = (row.get("dims_m") or {}).get("H")
    if len(side_c) > 1:
        flags.append({"code": "DUPLICATE_SIDE_CALLOUT", "texts": [c["text"] for c in side_c]})
        comps.append(_comp("SIDE_BARS", None, UNRESOLVED, "DUPLICATE_SIDE_CALLOUT", [c["ev"] for c in side_c]))
    elif side_c:
        c = side_c[0]
        sp = c.get("spacing")
        pieces = [p for p in got["pieces"] if abs(p["x0"] - c["x0"]) <= JOIN_GAP_H * c["h"]]
        if sp is None and len(pieces) == 1:
            sp = dict(pieces[0]["spacing"], printed="SEPARATE_PIECE (separator not printed as text)",
                      ids=pieces[0]["ids"])
        elif sp is None and len(pieces) > 1:
            flags.append({"code": "AMBIGUOUS_SPACING_PIECES", "texts": [p["text"] for p in pieces]})
        reading = {"count": c["count"], "dia_mm": c["dia_mm"], "spacing": sp, "header": c["header"],
                   "header_dx": c["header_dx"],
                   "notation_meaning": "UNRESOLVED: a count with a spacing ('n Ø d / s') may be n bars in all or n "
                                       "per face per s of depth; the count basis must be printed or approved"
                   if sp else "count as printed; per face or in all is not stated"}
        inputs = printed_inputs.get((mark, "SIDE_BARS", None))
        kg, why = _kg(dict(inputs, spaced_notation=bool(sp)) if inputs else None, unit_mass)
        comps.append(_comp("SIDE_BARS", None, DETECTED, "REMARK_CALLOUT_IN_ROW", [c["ev"]], reading=reading,
                           kg=kg, kg_blank_reason=why, inputs=inputs))
    else:
        rec = _nr(nr, row, "SIDE_BARS")
        if rec:
            comps.append(_comp("SIDE_BARS", None, NOT_REQUIRED, "EVIDENCE_RECORD", [rec]))
        elif note and depth is not None and depth <= float(note["depth_gt_m"]) + 1e-9:
            comps.append(_comp("SIDE_BARS", None, NOT_REQUIRED, f"GENERAL_NOTE: depth {depth:.3f} m not greater "
                               f"than {float(note['depth_gt_m']):.3f} m", [note]))
        elif note and depth is not None:
            comps.append(_comp("SIDE_BARS", None, UNRESOLVED, f"GENERAL_NOTE_REQUIRES_SIDE_BARS_NOT_PRINTED: depth "
                               f"{depth:.3f} m > {float(note['depth_gt_m']):.3f} m and no remark in the row", [note]))
        else:
            comps.append(_comp("SIDE_BARS", None, UNRESOLVED, "NO_REMARK_AND_NO_GOVERNING_NOTE" if depth is not None
                               else "DEPTH_NOT_READ", []))
    # ---- NESTED_LINKS
    cl = got["clusters"]
    if len(cl) > 1:
        comps.append(_comp("NESTED_LINKS", None, UNRESOLVED, "MORE_THAN_ONE_LINK_SYMBOL_IN_ROW",
                           [{"loop_ids": c["loop_ids"], "inserts": c["inserts"]} for c in cl]))
    elif cl:
        c = cl[0]
        ev = [{"loop_ids": c["loop_ids"], "inserts": c["inserts"], "box": [round(v, 3) for v in c["box"]],
               "boundary_distance": c["boundary_distance"]}]
        if c["loops"] >= 2:
            inputs = printed_inputs.get((mark, "NESTED_LINKS", None))
            kg, why = _kg(inputs, unit_mass)
            comps.append(_comp("NESTED_LINKS", None, DETECTED, f"LINK_SYMBOL_{c['loops']}_LOOPS", ev,
                               reading={"loops": c["loops"], "legs": 2 * c["loops"],
                                        "inner_link_size": "not dimensioned in the symbol"},
                               kg=kg, kg_blank_reason=why or None, inputs=inputs))
        else:
            comps.append(_comp("NESTED_LINKS", None, NOT_REQUIRED, "LINK_SYMBOL_SINGLE_LOOP", ev))
    else:
        rec = _nr(nr, row, "NESTED_LINKS")
        ld = link_detail.get((sheet, fam)) or link_detail.get((None, fam))
        if rec:
            comps.append(_comp("NESTED_LINKS", None, NOT_REQUIRED, "EVIDENCE_RECORD", [rec]))
        elif symbol_rows:
            comps.append(_comp("NESTED_LINKS", None, NOT_REQUIRED, f"NOT_PRINTED: the table prints a link symbol on "
                               f"{symbol_rows} row(s), none on this row", []))
        elif ld and int(ld["loops"]) == 1:
            comps.append(_comp("NESTED_LINKS", None, NOT_REQUIRED, "LINK_DETAIL_SINGLE_LOOP", [ld]))
        elif ld:
            comps.append(_comp("NESTED_LINKS", None, UNRESOLVED, f"LINK_DETAIL_{ld['loops']}_LOOPS_NOT_DIMENSIONED",
                               [ld]))
        else:
            comps.append(_comp("NESTED_LINKS", None, UNRESOLVED, "NO_LINK_SYMBOL_IN_TABLE_AND_NO_LINK_DETAIL", []))
    # ---- TOP_CORNER
    if fam == "CONTINUOUS_BEAM":
        spans = [k for _, k in centres]
        tops = {s["role"]: s for s in bar_slots if re.fullmatch(r"TOP\d*", s["role"]) and s["filled"]}
        for k in spans:
            mine = [c for c in corner_c if c["span"] == k]
            if f"TOP{k}" in tops or "TOP" in tops:
                comps.append(_comp("TOP_CORNER", k, NOT_REQUIRED, "CARRIED_BY_TOP_ATTRIBUTE (measured group, "
                                   "unchanged)", []))
                for c in mine:
                    flags.append({"code": "CORNER_CALLOUT_BESIDE_TOP_ATTRIBUTE", **c["ev"]})
            elif len(mine) > 1:
                comps.append(_comp("TOP_CORNER", k, UNRESOLVED, "DUPLICATE_CORNER_CALLOUT", [c["ev"] for c in mine]))
            elif mine:
                c = mine[0]
                inputs = printed_inputs.get((mark, "TOP_CORNER", k))
                kg, why = _kg(inputs, unit_mass)
                comps.append(_comp("TOP_CORNER", k, DETECTED, "CORNER_CALLOUT_IN_SPAN_COLUMN", [c["ev"]],
                                   reading={"count": c["count"], "dia_mm": c["dia_mm"]}, kg=kg, kg_blank_reason=why,
                                   inputs=inputs))
            else:
                rec = _nr(nr, row, "TOP_CORNER", k)
                comps.append(_comp("TOP_CORNER", k, NOT_REQUIRED, "EVIDENCE_RECORD", [rec]) if rec else
                             _comp("TOP_CORNER", k, UNRESOLVED, "NO_CORNER_CALLOUT_IN_SPAN", []))
        if not spans:
            comps.append(_comp("TOP_CORNER", None, UNRESOLVED, "SPAN_COLUMNS_NOT_READ", []))
    else:
        tops = [s for s in bar_slots if re.fullmatch(r"TOP\d*", s["role"])]
        if any(s["filled"] for s in tops):
            comps.append(_comp("TOP_CORNER", None, NOT_REQUIRED, "SIMPLE_BEAM_TOP_ATTRIBUTE (measured group, "
                               "unchanged)", []))
        else:
            comps.append(_comp("TOP_CORNER", None, UNRESOLVED, "SIMPLE_BEAM_TOP_NOT_PRINTED", []))
    open_ = [f"{c['kind']}{'' if c['span'] is None else ' span ' + str(c['span'])}: {c['basis']}" for c in comps
             if c["status"] == UNRESOLVED or (c["status"] == DETECTED and c["quantity_kg"] is None)]
    open_ += [f"FLAG {f['code']}" for f in flags]
    b = bands[i] if bands else None
    return {"mark": mark, "family": fam, "schedule": {"sheet": sheet, "insert": e["owner"], "mark_tag": tkey[2],
                                                       "row_band": [round(b["lo"], 3), round(b["hi"], 3)] if b else None,
                                                       "depth_m": (row.get("dims_m") or {}).get("H"),
                                                       "width_m": (row.get("dims_m") or {}).get("W")},
            "association": assoc_rule, "floors": list((occurrences or {}).get((fam, mark), [])),
            "components": comps, "flags": flags, "completeness": INCOMPLETE if open_ else COMPLETE,
            "completeness_scope": "the three safeguard component kinds only; never a verification of the measured "
                                  "groups or a released quantity",
            "incomplete_because": open_}


def _comp(kind, span, status, basis, evidence, *, reading=None, kg=None, kg_blank_reason=None, inputs=None):
    if status == DETECTED:
        state = "MEASURED_FROM_PRINTED_INPUTS" if kg is not None else "HELD"
    elif status == UNRESOLVED:
        state = "HELD"
    else:
        state = "NOT_APPLICABLE"
    return {"kind": kind, "span": span, "status": status, "basis": basis, "evidence": evidence, "reading": reading,
            "quantity_kg": kg, "quantity_state": state,
            "kg_blank_reason": None if kg is not None else (kg_blank_reason or ("HELD" if status != NOT_REQUIRED
                                                                                  else None)),
            "inputs": inputs}


def _summary(beams, unassigned):
    out = {"beams": len(beams), "complete": sum(1 for b in beams if b["completeness"] == COMPLETE),
           "unassigned_items": len(unassigned)}
    for k in KINDS:
        for s in STATUSES:
            out[f"{k}.{s}"] = sum(1 for b in beams for c in b["components"] if c["kind"] == k and c["status"] == s)
    out["flags"] = sum(len(b["flags"]) for b in beams)
    out["kg_measured"] = sum(c["quantity_kg"] for b in beams for c in b["components"] if c["quantity_kg"] is not None)
    return out


def validate(result):
    """Invariants (refused, never repaired): an UNRESOLVED or NOT_REQUIRED component has no kg (never 0); a DETECTED
    component with kg has every input; kg is never 0; a COMPLETE beam has no HELD component and no flag."""
    for b in result["beams"]:
        held = False
        for c in b["components"]:
            if c["status"] not in STATUSES or c["kind"] not in KINDS:
                raise SafeguardError(f"{b['mark']}: unknown status / kind {c['status']} {c['kind']}")
            if c["status"] != DETECTED and c["quantity_kg"] is not None:
                raise SafeguardError(f"{b['mark']} {c['kind']}: a {c['status']} component reported as "
                                     f"{c['quantity_kg']} kg (a missing group is never 0): refused")
            if c["quantity_kg"] is not None:
                if c["quantity_kg"] <= 0:
                    raise SafeguardError(f"{b['mark']} {c['kind']}: kg {c['quantity_kg']} is not a quantity: refused")
                inp = c.get("inputs") or {}
                if any(inp.get(k) in (None, "") for k in ("count", "dia_mm", "length_m", "source")):
                    raise SafeguardError(f"{b['mark']} {c['kind']}: kg without every printed input: refused")
            if c["status"] == UNRESOLVED or (c["status"] == DETECTED and c["quantity_kg"] is None):
                held = True
                if c["quantity_state"] != "HELD":
                    raise SafeguardError(f"{b['mark']} {c['kind']}: unresolved component not HELD: refused")
        if b["completeness"] == COMPLETE and (held or b["flags"]):
            raise SafeguardError(f"{b['mark']}: marked COMPLETE with a HELD component or an open flag: refused")
        if b["completeness"] not in (COMPLETE, INCOMPLETE):
            raise SafeguardError(f"{b['mark']}: unknown completeness {b['completeness']}")
    return True


def policy_record():
    return {"policy_id": POLICY_ID, "method_id": METHOD_ID, "kinds": list(KINDS), "statuses": list(STATUSES),
            "association": "row bands half-way between row anchors of one table; max(half height, "
                           f"{BOUNDARY_FRACTION} x pitch) around a boundary or outside every band = AMBIGUOUS, never "
                           "assigned",
            "kg": "count x length x kg/m (rebar_unit_mass, the project's method) only from supplied printed inputs; "
                  "else blank and HELD",
            "complete": "every component NOT_REQUIRED or DETECTED with kg, and no flag",
            "wired": False, "changes_measured_groups": False}
