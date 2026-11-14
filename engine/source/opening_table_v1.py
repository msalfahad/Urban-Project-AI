"""OPENING_TABLE_V1 (T-781, owner ACCURACY_PLAN_2026-11-14 change D): ONE opening table per project, every villa.

Every opening of the drawings becomes one row: id, floor, type, side (EXTERNAL / INTERNAL), W, H, wall thickness,
sill, head, and for each value its source label:

    MEASURED     read from the plan geometry (band opening jamb to jamb, block insert x |scale|)
    SCHEDULE     a schedule row bound to the opening's mark
    DRAWING-READ an elevation / section outline or printed chain bound to the opening (floor + width)
    DEFAULT      the company default (owner 2026-11-13): window sill 0.90 dry / 1.60 wet; window head = the most
                 common printed window head on the same floor, else 2.20; a door / passage stands on the floor
                 with head 2.20 unless printed (Q-55 C; a printed main-entrance head is never spread)
    HELD         nothing establishes the value: value None, never 0 (a missing plan width is never defaulted)

Derived per row (every unit separate): opening m2 = W x (head - sill) [Q-73: the full opening is deducted from
blockwork, so the masonry deduction m2 equals it]; lintel = the shortest precast standard 1.20 / 1.50 / 2.50 / 3.00 /
4.00 m that covers W + 2 x 0.15 bearing (owner 2026-11-02); longer than 4.00 -> FLAGGED, no length; one per opening.

Inputs (all plain dicts, project-agnostic; no project name, mark or id is written in this module):
  plan_openings   the geometry run's ARCH_OPENINGS.json "openings" records (opening_id, floor, kind, type, width_m,
                  wall_t_m, rooms, evidence{marks{blocks}, door_leaves, glazing_lm}); optional "layer", "block" and
                  "insert" {name, xscale, block_width} for a symbol read from a block insert
  schedule        the run's OPENING_SCHEDULE.json "openings" records (height / sill with "governing" and "mark")
  elevation_reads [{floor, width_m, sill_m, head_m, height_m?, source, kind?, type_hint?, arched?}] heights above the finished floor read from an
                  elevation outline, a section or a printed chain; bound by floor + width (+- WIDTH_TOL_M); a group of
                  plan openings with one width takes the reading only when every reading of that group agrees
                  (UNIFORM_GROUP), else the rows keep the default and carry the conflict; a reading with no plan
                  opening left to bind becomes an ELEVATION_ONLY row (an opening the plan reader did not detect)
                  (arched=True: head_m is the window's own arch crown; area = W x crown, owner Q-32 A)
  rooms           {room_id: {"kind": "WET" | "DRY" | ...}} from ARCH_ROOMS.json (wet sill default)

Classification, in this order: block / layer name (SHUTTER, GLASS_DOOR, DOOR, WINDOW, ARCH words), then geometry:
door leaves or a swing -> DOOR; a window whose sill is <= 0.05 above the floor and whose height is >= 2.00
stays a WINDOW marked glazing FLOOR_GLAZING (only a name or a leaf makes glazing a GLASS_DOOR); an elevation
reading may carry type_hint (e.g. SHUTTER for louvred leaves drawn on the elevation); a passage with an arch mark -> ARCH, else PASSAGE. Side: an opening with
fewer than two rooms bound on the plan opens to the outside (EXTERNAL); a lift opening is never counted as a door.
"""
from __future__ import annotations

import re
from collections import Counter, defaultdict

POLICY_ID = "OPENING_TABLE_V1"
MEASURED, SCHEDULE, DRAWING_READ, DEFAULT, HELD = "MEASURED", "SCHEDULE", "DRAWING-READ", "DEFAULT", "HELD"
LABELS = (MEASURED, SCHEDULE, DRAWING_READ, DEFAULT, HELD)
TYPES = ("WINDOW", "DOOR", "SHUTTER", "GLASS_DOOR", "ARCH", "PASSAGE", "LIFT")

SILL_DRY_M, SILL_WET_M, HEAD_DEFAULT_M = 0.90, 1.60, 2.20
LINTEL_STANDARD_M = (1.20, 1.50, 2.50, 3.00, 4.00)
LINTEL_BEARING_M = 0.15
WIDTH_TOL_M = 0.02
GLASS_DOOR_MAX_SILL_M, GLASS_DOOR_MIN_H_M = 0.05, 2.00
MAX_M = 20.0

# block / layer words -> type (first match wins; checked before geometry)
NAME_RULES = (
    ("SHUTTER", re.compile(r"SHUTTER|LOUV|SHTR|ROLL", re.I)),
    ("GLASS_DOOR", re.compile(r"GLASS.?DOOR|SLID|GL.?DR|CURTAIN", re.I)),
    ("LIFT", re.compile(r"LIFT|ELEV", re.I)),
    ("ARCH", re.compile(r"ARCH", re.I)),
    ("DOOR", re.compile(r"DOOR", re.I)),
    ("WINDOW", re.compile(r"WINDOW|GLAZ", re.I)),
)


def _m(v, what="value"):
    """metres; a value above MAX_M is millimetres (converted); negative refused."""
    if v is None:
        return None
    v = float(v)
    if v < 0:
        raise ValueError(f"{what}: negative ({v})")
    return v / 1000.0 if v > MAX_M else v


def lintel(width_m):
    """(standard length, label) - the shortest standard covering W + 2 bearings; FLAGGED over 4.00; HELD without W."""
    if width_m is None:
        return None, HELD
    need = width_m + 2 * LINTEL_BEARING_M
    for s in LINTEL_STANDARD_M:
        if s + 1e-9 >= need:
            return s, DEFAULT
    return None, "FLAGGED"


def _name_type(o):
    names = [o.get("block"), o.get("layer"), (o.get("insert") or {}).get("name")]
    names += list(((o.get("evidence") or {}).get("marks") or {}).get("blocks") or ())
    for n in names:
        if not n:
            continue
        for t, rx in NAME_RULES:
            if rx.search(str(n)):
                return t, f"name '{n}'"
    return None, None


def _plan_width(o):
    """(width, label, note): the band opening width, else the insert's block width x |xscale| (a mirrored insert has a
    negative scale: the width is its absolute value)."""
    if o.get("width_m") is not None:
        return round(_m(o["width_m"], "width"), 4), MEASURED, "plan band opening jamb to jamb"
    ins = o.get("insert") or {}
    if ins.get("block_width") is not None and ins.get("xscale") is not None:
        w = _m(abs(float(ins["xscale"])) * float(ins["block_width"]), "insert width")
        return round(w, 4), MEASURED, f"block insert width x |xscale| ({'mirrored' if float(ins['xscale']) < 0 else 'plain'})"
    return None, HELD, "no plan width: HELD (never defaulted, never 0)"


def _is_wet(o, rooms):
    return any((rooms.get(r) or {}).get("kind") == "WET" for r in (o.get("rooms") or ()))


def _read_vals(e):
    """(sill, head, height) of one read in metres; height = head - sill when both are given."""
    sl = None if e.get("sill_m") is None else round(_m(e["sill_m"]), 3)
    hd = None if e.get("head_m") is None else round(_m(e["head_m"]), 3)
    ht = round(hd - sl, 3) if sl is not None and hd is not None else (
        None if e.get("height_m") is None else round(_m(e["height_m"]), 3))
    return sl, hd, ht


def _bind_reads(rows, reads):
    """floor + width + kind binding of elevation reads to rows; returns the reads no row took (ELEVATION_ONLY).

    One group = the plan openings of one floor, kind and width (+- WIDTH_TOL_M) and the reads of the same key.
    - every read agrees (a height-only read agrees when its height equals the complete reads' head - sill):
      every opening of the group takes it (UNIQUE / UNIFORM_GROUP); reads beyond the openings stay ELEVATION_ONLY;
    - reads disagree but there is exactly one complete read per opening: the group's set of heights is established
      and, the widths being equal, every group sum (m2, deduction, reveal) is exact; which opening carries which
      height is not proven (GROUP_COUNT_MATCH, finding PER_OPENING_ORDER_UNPROVEN);
    - otherwise no read is chosen (ELEVATION_READS_DISAGREE) and the defaults apply."""
    left = []
    by_key = defaultdict(list)
    for e in reads:
        by_key[(e["floor"], round(_m(e["width_m"], "read width"), 2), e.get("kind") or "")].append(e)
    taken = set()
    for (fl, w, kd), es in sorted(by_key.items()):
        cands = [r for r in rows if r["floor"] == fl and r["W"] is not None and id(r) not in taken
                 and abs(r["W"] - w) <= WIDTH_TOL_M and r["type"] != "LIFT" and r.get("opening_id") is not None
                 and (not kd or r["kind_plan"] == kd)]
        if not cands:
            left += es
            continue
        vals = [_read_vals(e) for e in es]
        complete = {(sl, hd) for sl, hd, _ in vals if sl is not None and hd is not None}
        heights = {ht for _, _, ht in vals if ht is not None}
        src = "; ".join(sorted({e["source"] for e in es}))
        hints = {e.get("type_hint") for e in es}
        hint = next(iter(hints)) if len(hints) == 1 else None
        arch = {(_read_vals(e)[:2]) for e in es if e.get("arched")}
        if len(complete) <= 1 and len(heights) <= 1:
            sl, hd = next(iter(complete)) if complete else (None, None)
            ht = next(iter(heights)) if heights else None
            for r in cands:
                taken.add(id(r))
                r["_read"] = {"sill": sl, "head": hd, "height": ht if hd is None else None, "source": src,
                              "binding": "UNIFORM_GROUP" if len(cands) > 1 else "UNIQUE", "type_hint": hint,
                              "arched": (sl, hd) in arch}
            left += es[len(cands):] if len(es) > len(cands) else []
        elif len(es) == len(cands) and all(sl is not None and hd is not None for sl, hd, _ in vals):
            order = sorted(vals)
            for r, (sl, hd, _) in zip(sorted(cands, key=lambda r: r["id"]), order):
                taken.add(id(r))
                r["_read"] = {"sill": sl, "head": hd, "height": None, "source": src, "binding": "GROUP_COUNT_MATCH",
                              "type_hint": hint, "arched": (sl, hd) in arch}
                r["findings"].append({"code": "PER_OPENING_ORDER_UNPROVEN", "group_values": order,
                                      "why": "one read per opening of one width: the group sums are exact, the "
                                             "opening each height belongs to is not proven"})
        else:
            for r in cands:
                r["findings"].append({"code": "ELEVATION_READS_DISAGREE", "values": sorted(vals, key=str),
                                      "why": "one plan width, several drawn heights, counts differ: no read is "
                                             "chosen"})
    return left


def build(plan_openings, *, schedule=(), elevation_reads=(), rooms=None):
    """the opening table: list of rows (dicts), one per opening, every value labelled."""
    rooms = rooms or {}
    sched = {(s.get("floor"), s.get("opening_id")): s for s in schedule}
    rows = []
    for o in plan_openings:
        w, wl, wn = _plan_width(o)
        nt, nwhy = _name_type(o)
        kind = o.get("kind")
        ev = o.get("evidence") or {}
        geo = ("LIFT" if "LIFT" in str(o.get("type", "")).upper() else
               "DOOR" if kind == "DOOR" or ev.get("door_leaves") or o.get("door_symbol") else
               "WINDOW" if kind == "WINDOW" else
               "PASSAGE" if kind in ("PASSAGE", "OPENING") else None)
        t = nt or geo
        row = {"id": f"{o.get('floor')}:{o.get('opening_id')}", "floor": o.get("floor"),
               "opening_id": o.get("opening_id"), "kind_plan": kind, "type": t,
               "type_basis": nwhy or (f"geometry: plan kind {kind}" if t else "no symbol class: HELD"),
               "side": "EXTERNAL" if len(o.get("rooms") or ()) < 2 else "INTERNAL",
               "rooms": list(o.get("rooms") or ()), "wet": _is_wet(o, rooms),
               "W": w, "W_label": wl, "W_note": wn,
               "wall_t": None if o.get("wall_t_m") is None else round(_m(o["wall_t_m"]), 3),
               "wall_t_label": MEASURED if o.get("wall_t_m") is not None else HELD,
               "findings": []}
        s = sched.get((o.get("floor"), o.get("opening_id"))) or {}
        row["_sched"] = s
        rows.append(row)
    left = _bind_reads(rows, list(elevation_reads))
    for e in left:  # an opening drawn on an elevation that the plan reader did not detect
        w = round(_m(e["width_m"], "read width"), 4)
        rows.append({"id": f"{e['floor']}:ELEV-{len(rows) + 1:03d}", "floor": e["floor"], "opening_id": None,
                     "kind_plan": None, "type": e.get("kind") or "WINDOW",
                     "type_basis": "elevation outline (kind as read)", "side": "EXTERNAL", "rooms": [], "wet": False,
                     "W": w, "W_label": DRAWING_READ, "W_note": "elevation / printed chain width; no plan symbol "
                     "detected (PLAN_SYMBOL_NOT_DETECTED)", "wall_t": None, "wall_t_label": HELD,
                     "findings": [{"code": "PLAN_SYMBOL_NOT_DETECTED", "source": e["source"]}],
                     "_sched": {}, "_read": {"sill": _read_vals(e)[0], "head": _read_vals(e)[1],
                                             "height": None if _read_vals(e)[1] is not None else _read_vals(e)[2],
                                             "type_hint": e.get("type_hint"), "arched": bool(e.get("arched")),
                                             "source": e["source"], "binding": "ELEVATION_ONLY"}})
    _heights(rows)
    for r in rows:
        r.pop("_sched", None)
        r.pop("_read", None)
    return rows


def _sched_val(s, key):
    b = s.get(key) or {}
    if b.get("value_m") is None or b.get("governing") in (None, "URBAN_DEFAULT"):
        return None
    return float(b["value_m"])


def _heights(rows):
    # pass 1: what the sources establish
    for r in rows:
        s, rd = r["_sched"], r.get("_read") or {}
        sill = head = None
        sl = hl = None
        if r["type"] in ("DOOR", "PASSAGE", "ARCH", "LIFT"):
            sill, sl = 0.0, DEFAULT  # a door / passage stands on the floor
        sh, ss = _sched_val(s, "height"), _sched_val(s, "sill")
        if ss is not None and r["type"] not in ("DOOR",):
            sill, sl = ss, SCHEDULE
        if sh is not None and sill is not None:
            head, hl = round(sill + sh, 4), SCHEDULE
        if rd:
            if rd.get("sill") is not None and sl != SCHEDULE:
                sill, sl = rd["sill"], DRAWING_READ
            if rd.get("head") is not None and hl != SCHEDULE:
                head, hl = rd["head"], DRAWING_READ
            r["read_source"] = rd["source"]
            r["read_binding"] = rd["binding"]
        r["sill"], r["sill_label"], r["head"], r["head_label"] = sill, sl, head, hl
        if rd.get("type_hint") in TYPES and r["type"] in ("WINDOW", None):
            r["type"], r["type_basis"] = rd["type_hint"], r["type_basis"] + f"; elevation: {rd['type_hint'].lower()}"
        r["glazing"] = "ARCHED_HEAD" if rd.get("arched") else None
        if rd.get("arched"):
            r["head_note"] = "arched head: head = the window's own arch crown; area = W x crown (owner Q-32 A)"
        if r["type"] == "WINDOW" and not r["glazing"] and sill is not None and sill <= GLASS_DOOR_MAX_SILL_M and head is not None \
                and head - sill >= GLASS_DOOR_MIN_H_M:
            # floor-standing glazing stays a WINDOW (fixed or opening glazing) unless a name or a leaf makes it a door
            r["glazing"] = "FLOOR_GLAZING"
    # nearest printed head per (floor, type family) for the default
    printed = defaultdict(list)
    for r in rows:
        if r["head_label"] in (SCHEDULE, DRAWING_READ):
            printed[(r["floor"], "DOOR" if r["type"] in ("DOOR", "GLASS_DOOR") else r["type"])].append(r["head"])
    # pass 2: company defaults
    for r in rows:
        fam = "DOOR" if r["type"] in ("DOOR", "GLASS_DOOR") else r["type"]
        if r["sill"] is None:
            r["sill"], r["sill_label"] = (SILL_WET_M if r["wet"] else SILL_DRY_M), DEFAULT
            r["sill_note"] = "company default sill " + ("1.60 wet room" if r["wet"] else "0.90")
        rh = (r.get("_read") or {}).get("height")
        if r["head"] is None and rh is not None:
            r["head"], r["head_label"] = round(r["sill"] + rh, 4), DRAWING_READ
            r["head_note"] = f"drawn outline height {rh:.2f} on the sill (outline has no floor datum)"
        if r["head"] is None:
            ph = printed.get((r["floor"], fam)) if fam in ("WINDOW", "SHUTTER") else None
            if ph:
                h = Counter(ph).most_common(1)[0][0]
                r["head"], r["head_label"] = h, DEFAULT
                r["head_note"] = f"company default: the printed head of this floor's {fam.lower()}s ({h:.2f})"
            else:
                r["head"], r["head_label"] = HEAD_DEFAULT_M, DEFAULT
                r["head_note"] = ("company default head 2.20 (Q-55 C door / passage fallback)" if fam not in
                                  ("WINDOW", "SHUTTER") else "company default head 2.20 (none printed on this floor)")
        if r["head"] is not None and r["sill"] is not None and r["head"] <= r["sill"]:
            r["findings"].append({"code": "HEAD_NOT_ABOVE_SILL", "sill": r["sill"], "head": r["head"]})
            r["H"], r["H_label"] = None, HELD
        else:
            r["H"] = round(r["head"] - r["sill"], 4)
            r["H_label"] = min((r["sill_label"], r["head_label"]), key=_weak)
        r["area_m2"] = round(r["W"] * r["H"], 4) if r["W"] is not None and r["H"] is not None else None
        r["area_label"] = (min((r["W_label"], r["H_label"]), key=_weak) if r["area_m2"] is not None else HELD)
        r["masonry_deduction_m2"] = r["area_m2"]  # Q-73: full deduction of the actual opening
        ln, ll = lintel(r["W"]) if r["type"] != "LIFT" else (None, "NOT_APPLICABLE")
        r["lintel_m"], r["lintel_label"] = ln, ll


_RANK = {HELD: 0, DEFAULT: 1, DRAWING_READ: 2, SCHEDULE: 3, MEASURED: 4}


def _weak(label):
    return _RANK.get(label, 0)


def blanks(rows):
    """rows with W or H not filled (the acceptance count: 0)."""
    return [r["id"] for r in rows if r["W"] is None or r["H"] is None]


def summary(rows):
    out = defaultdict(lambda: {"pcs": 0, "m2": 0.0})
    for r in rows:
        k = f"{r['type']}|{r['side']}"
        out[k]["pcs"] += 1
        out[k]["m2"] = round(out[k]["m2"] + (r["area_m2"] or 0.0), 4)
    labels = Counter(r["area_label"] for r in rows)
    return {"policy": POLICY_ID, "rows": len(rows), "blank_W_or_H": len(blanks(rows)),
            "by_type_side": dict(sorted(out.items())), "area_labels": dict(labels)}
