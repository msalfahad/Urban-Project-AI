"""CONTINUOUS BEAMS (M4) - the multi-span model of a continuous-beam mark: its axis line, its supports, its spans
matched to the schedule's PRINTED span lengths, and the physical bars that follow from the schedule's per-span roles
(generic; stdlib + engine.source geometry helpers).

A continuous-beam schedule row prints its spans in order (L1, L2, ...) and its bars per role:

    BOTk             bottom bars of span k
    STRk / STIk      stirrups of span k, a count per metre
    MID / MIDk       top bars over interior support k (MID alone: the one interior support of a two-span beam)
    TOP / TOPk       top bars along the whole beam / of span k

The plan draws the beam as bands cut by the columns. Nothing here reads a coordinate, a layer name or a mark of any
project.

    printed_spans(row)          the span lengths the row prints (tags L1 / L1-M / SPAN1 ...) in metres, or None
    lines(rec, mark, unit_m)    the beam lines of a mark on one plan: its bound pieces and the collinear pieces of the
                                same width beyond them across SUPPORT-FILLED gaps (a column outline at any size or a
                                crossing beam band covers the whole gap), ordered along the axis, with every support
                                that crosses the band strip
    match(line, printed, ...)   the span sequence: the window of pieces and the interior supports whose span lengths
                                equal the printed spans in order, forward or reversed, within the tolerance
                                    MATCH_FORWARD / MATCH_REVERSED   one reading fits, or one fits clearly better
                                    MATCH_SYMMETRIC                  the printed sequence reads the same both ways
                                    AMBIGUOUS_DIRECTION              both readings fit and neither clearly better
                                    AMBIGUOUS_SPANS                  two different span sets fit
                                    SPAN_COUNT_CONFLICT              the drawn line cannot hold the printed count
                                    SPAN_LENGTH_CONFLICT             the count fits, a length does not
                                    NO_PRINTED_SPANS                 the row prints no span lengths
    physical_bars(spans, row, conv)
                                one record per PHYSICAL bar group (role, count, diameter, length low / base / high,
                                the span(s) it lies in with the share in each). A through bar is ONE group over the
                                whole line, a support bar ONE group over its support - never one per span. A role the
                                row does not print is returned as missing, never invented.

Inheritance: an unlabelled piece takes the mark only when it is one of the matched spans. Alignment alone never
carries a section across a support.
"""

from __future__ import annotations

import itertools
import math
import re

POLICY_ID = "CONTINUOUS_BEAMS_V1"
SPAN_TAG = re.compile(r"^(?:L|SPAN)\s*(\d+)(?:[-_ ]?(M|CM|MM))?$", re.I)
ROLE = re.compile(r"^(BOT|BOTTOM|STR|STI|LINK|MID|SUP|TOP)(\d*)$", re.I)
STATES = ("MATCH_FORWARD", "MATCH_REVERSED", "MATCH_SYMMETRIC", "AMBIGUOUS_DIRECTION", "AMBIGUOUS_SPANS",
          "SPAN_COUNT_CONFLICT", "SPAN_LENGTH_CONFLICT", "NO_PRINTED_SPANS")
MAPPED = ("MATCH_FORWARD", "MATCH_REVERSED", "MATCH_SYMMETRIC", "AMBIGUOUS_DIRECTION")


# ------------------------------------------------------------------ schedule
def printed_spans(row):
    """[L1, L2, ...] in metres from the row's raw cells, or None. A tag without a unit suffix is read in metres only
    when its values look like metres (all below 30); otherwise None (the unit is not stated)."""
    raw = row.get("raw") or {}
    got = {}
    for k, v in raw.items():
        m = SPAN_TAG.match(str(k).strip())
        if not m or v in (None, ""):
            continue
        try:
            x = float(str(v).replace(",", "."))
        except ValueError:
            continue
        unit = (m.group(2) or "").upper()
        got[int(m.group(1))] = x / {"M": 1.0, "CM": 100.0, "MM": 1000.0}.get(unit, 1.0) if unit else (x, None)
    if not got:
        return None
    ks = sorted(got)
    if ks != list(range(1, len(ks) + 1)):
        return None
    vals = [got[k] for k in ks]
    if any(isinstance(v, tuple) for v in vals):
        bare = [v[0] if isinstance(v, tuple) else v for v in vals]
        if max(bare) >= 30:
            return None
        vals = bare
    return [float(v) for v in vals]


def roles(row):
    """{('BOTTOM', k) / ('STIRRUP', k) / ('SUPPORT_TOP', j) / ('TOP_THROUGH', 0) / ('TOP_SPAN', k): bar} and the set of
    roles whose cells the row's format carries but leaves empty."""
    out, empty = {}, set()
    for b in row.get("bars") or []:
        key = _role_key(b.get("role") or "")
        if key and b.get("dia_mm") and b.get("count"):
            out[key] = b
    for tag in row.get("tag_set") or ():
        base = re.sub(r"-(B|D)$", "", str(tag).upper())
        key = _role_key(base)
        if key and key not in out:
            empty.add(key)
    return out, empty


def _role_key(role):
    m = ROLE.match(role.strip().upper())
    if not m:
        return None
    kind, k = m.group(1), int(m.group(2)) if m.group(2) else 0
    if kind in ("BOT", "BOTTOM"):
        return ("BOTTOM", k)
    if kind in ("STR", "STI", "LINK"):
        return ("STIRRUP", k)
    if kind in ("MID", "SUP"):
        return ("SUPPORT_TOP", k)
    return ("TOP_SPAN", k) if k else ("TOP_THROUGH", 0)


# ------------------------------------------------------------------ geometry
def _proj(poly, u, n):
    ts = [x * u[0] + y * u[1] for x, y in poly]
    ns = [x * n[0] + y * n[1] for x, y in poly]
    return min(ts), max(ts), min(ns), max(ns)


def _cross(a, b):
    return a[0] * b[1] - a[1] * b[0]


def lines(rec, mark, unit_m, *, family="CONTINUOUS_BEAM", width_tol_m=0.005, offset_frac=0.1, slack_frac=0.25):
    """The beam lines of `mark` on one plan record (generic_route.detect sheet record). -> [line]."""
    bands = {b["band_id"]: b for b in rec.get("bands", [])}
    bound = set()
    for m in rec.get("marks", []):
        if m.get("family") == family and m.get("mark") == mark and str(m.get("state", "")).startswith("BOUND"):
            bound.update(m.get("bands") or ([m["band"]] if m.get("band") else []))
    bound = {b for b in bound if b in bands and bands[b]["kind"] == "STRAIGHT"}
    if not bound:
        return []
    owner = {}
    for m in rec.get("marks", []):
        if str(m.get("state", "")).startswith("BOUND"):
            for bid in m.get("bands") or ([m["band"]] if m.get("band") else []):
                owner.setdefault(bid, set()).add((m.get("family"), m.get("mark")))
    out, done = [], set()
    for seed_id in sorted(bound):
        if seed_id in done:
            continue
        seed = bands[seed_id]
        u = seed["u"]
        n = (-u[1], u[0])
        t0s, t1s, n0s, n1s = _proj(seed["polygon"], u, n)
        w = n1s - n0s
        tol_n, tol_w = offset_frac * w, width_tol_m / unit_m
        pieces = []
        for b in bands.values():
            if b["kind"] != "STRAIGHT" or abs(abs(_cross(b["u"], u))) > math.sin(math.radians(1.0)):
                continue
            a0, a1, c0, c1 = _proj(b["polygon"], u, n)
            if abs((c1 - c0) - w) > tol_w or abs(c0 - n0s) > tol_n or abs(c1 - n1s) > tol_n:
                continue
            pieces.append({"band_id": b["band_id"], "t0": a0, "t1": a1, "bound": b["band_id"] in bound,
                           "owners": sorted(owner.get(b["band_id"], ()))})
        pieces.sort(key=lambda p: p["t0"])
        sup = []
        polys = [("COLUMN", c) for c in rec.get("column_boxes", [])] + \
                [("COLUMN_OUTLINE", c) for c in rec.get("column_presence", [])]
        for kind, c in polys:
            x0, y0, x1, y1 = c
            sup.append((kind, [(x0, y0), (x1, y0), (x1, y1), (x0, y1)], None))
        for b in bands.values():
            if b["kind"] == "STRAIGHT" and abs(_cross(b["u"], u)) > math.sin(math.radians(10.0)):
                sup.append(("BEAM", b["polygon"], b["band_id"]))
        groups = _support_groups(sup, u, n, n0s, n1s)
        slack = slack_frac * w
        # connected chains through support-filled gaps
        chains, cur = [], [pieces[0]] if pieces else []
        for a, b in zip(pieces, pieces[1:]):
            if b["t0"] - a["t1"] <= slack or _gap_group(groups, a["t1"], b["t0"], slack):
                cur.append(b)
            else:
                chains.append(cur)
                cur = [b]
        if cur:
            chains.append(cur)
        for ch in chains:
            if not any(p["bound"] for p in ch):
                continue
            done.update(p["band_id"] for p in ch if p["bound"])
            gaps = [_gap_group(groups, a["t1"], b["t0"], slack) if b["t0"] - a["t1"] > slack else
                    {"kind": "CONTINUOUS", "t_lo": a["t1"], "t_hi": b["t0"], "members": []}
                    for a, b in zip(ch, ch[1:])]
            ends = [_end_group(groups, ch[0]["t0"], slack, -1), _end_group(groups, ch[-1]["t1"], slack, +1)]
            inner = [[g for g in groups if g["t_lo"] > p["t0"] + slack and g["t_hi"] < p["t1"] - slack] for p in ch]
            out.append({"mark": mark, "family": family, "u": u, "n": n, "width_m": w * unit_m, "unit_m": unit_m,
                        "pieces": ch, "gap_supports": gaps, "end_supports": ends, "inner_supports": inner})
    return out


def _support_groups(sup, u, n, n0, n1):
    """Supports along the strip. Column outlines cluster among themselves and give the support its faces and centre;
    a crossing beam band is its own support only where no column is (an inclined beam crossing the strip over a long
    stretch never bridges two columns into one support)."""
    cols, beams = [], []
    for kind, poly, ref in sup:
        a0, a1, c0, c1 = _proj(poly, u, n)
        if c0 < n1 - 1e-9 and c1 > n0 + 1e-9:
            (cols if kind.startswith("COLUMN") else beams).append([a0, a1, kind, ref])
    groups = []
    for a0, a1, kind, ref in sorted(cols):
        if groups and a0 <= groups[-1]["t_hi"]:
            g = groups[-1]
            g["t_hi"] = max(g["t_hi"], a1)
            g["members"].append((kind, a0, a1, ref))
        else:
            groups.append({"t_lo": a0, "t_hi": a1, "members": [(kind, a0, a1, ref)], "kind": "COLUMN"})
    free = []
    for a0, a1, kind, ref in sorted(beams):
        hit = [g for g in groups if a0 < g["t_hi"] and a1 > g["t_lo"]]
        for g in hit:
            g["members"].append((kind, a0, a1, ref))          # recorded, never widening the column support
        if not hit:
            if free and a0 <= free[-1]["t_hi"]:
                free[-1]["t_hi"] = max(free[-1]["t_hi"], a1)
                free[-1]["members"].append((kind, a0, a1, ref))
            else:
                free.append({"t_lo": a0, "t_hi": a1, "members": [(kind, a0, a1, ref)], "kind": "BEAM"})
    groups = sorted(groups + free, key=lambda g: g["t_lo"])
    for g in groups:
        ref = [m for m in g["members"] if m[0].startswith("COLUMN")] or g["members"]
        g["centre"] = sum((m[1] + m[2]) / 2 for m in ref) / len(ref)
        g["r_lo"] = min(m[1] for m in g["members"])           # reach: faces plus the attached crossing beams
        g["r_hi"] = max(m[2] for m in g["members"])
    return groups


def _gap_group(groups, t_lo, t_hi, slack):
    for g in groups:
        if g["r_lo"] <= t_lo + slack and g["r_hi"] >= t_hi - slack:
            return g
    return None


def _end_group(groups, t, slack, side):
    best = None
    for g in groups:
        if g["r_lo"] - slack <= t <= g["r_hi"] + slack:
            if best is None or abs(g["centre"] - t) < abs(best["centre"] - t):
                best = g
    return best


# ------------------------------------------------------------------ span sequence
def match(line, printed, *, tol_m=0.40, tol_rel=0.10, margin_m=0.25, basis="AXIS"):
    """-> {state, direction, spans: [{index, printed_m, drawn_m, clear_m, t0, t1, pieces, left, right}],
    inherited: [band ids], residuals, alternatives}. index = the schedule span number of each drawn span."""
    if not printed:
        return {"state": "NO_PRINTED_SPANS", "spans": [], "inherited": []}
    P, u_m = list(printed), line["unit_m"]
    pcs = line["pieces"]
    bound_ix = [i for i, p in enumerate(pcs) if p["bound"]]
    lo_i, hi_i = min(bound_ix), max(bound_ix)
    sols, tried = [], []
    for i in range(0, lo_i + 1):
        for j in range(hi_i, len(pcs)):
            win = pcs[i:j + 1]
            if any(p["owners"] and not p["bound"] for p in win):       # a piece bound to another mark
                continue
            left = line["gap_supports"][i - 1] if i > 0 else line["end_supports"][0]
            right = line["gap_supports"][j] if j < len(pcs) - 1 else line["end_supports"][1]
            inner = [g for k in range(i, j + 1) for g in line["inner_supports"][k]]
            need = len(P) - len(win)
            if need < 0 or need > len(inner):
                tried.append({"window": (i, j), "why": "count"})
                continue
            for pick in itertools.combinations(inner, need):
                cuts = [left] + sorted(list(pick) + list(line["gap_supports"][i:j]), key=lambda g: g["centre"]) + \
                       [right]
                spans = _spans(cuts, win, u_m, basis)
                for direction, seq in (("FORWARD", P), ("REVERSED", P[::-1])):
                    res = [s["drawn_m"] - q for s, q in zip(spans, seq)]
                    ok = all(abs(r) <= max(tol_m, tol_rel * q) for r, q in zip(res, seq))
                    rec = {"window": (i, j), "cuts": [round(c["centre"], 3) if c else None for c in cuts],
                           "direction": direction, "residuals": [round(r, 3) for r in res],
                           "sum_abs": sum(abs(r) for r in res), "spans": spans, "ok": ok}
                    tried.append(rec)
                    if ok:
                        sols.append(rec)
    if not sols:
        counts = [t for t in tried if t.get("why") == "count"]
        state = "SPAN_COUNT_CONFLICT" if len(counts) == len(tried) else "SPAN_LENGTH_CONFLICT"
        best = min((t for t in tried if "sum_abs" in t), key=lambda t: t["sum_abs"], default=None)
        return {"state": state, "spans": [], "inherited": [], "best_attempt": _public(best) if best else None,
                "printed_m": P}
    geo = {(s["window"], tuple(s["cuts"])) for s in sols}
    if len(geo) > 1:
        return {"state": "AMBIGUOUS_SPANS", "spans": [], "inherited": [], "printed_m": P,
                "alternatives": [_public(s) for s in sols]}
    fw = [s for s in sols if s["direction"] == "FORWARD"]
    rv = [s for s in sols if s["direction"] == "REVERSED"]
    if fw and rv:
        if P == P[::-1]:
            state, best = "MATCH_SYMMETRIC", fw[0]
        elif abs(fw[0]["sum_abs"] - rv[0]["sum_abs"]) >= margin_m:
            best = min(fw[0], rv[0], key=lambda s: s["sum_abs"])
            state = "MATCH_" + best["direction"]
        else:
            state, best = "AMBIGUOUS_DIRECTION", min(fw[0], rv[0], key=lambda s: s["sum_abs"])
    else:
        best = (fw or rv)[0]
        state = "MATCH_" + best["direction"]
    order = list(range(1, len(P) + 1)) if best["direction"] == "FORWARD" else list(range(len(P), 0, -1))
    spans = []
    for k, (s, idx) in enumerate(zip(best["spans"], order)):
        spans.append(dict(s, index=idx, printed_m=P[idx - 1]))
    i, j = best["window"]
    inherited = [p["band_id"] for p in pcs[i:j + 1] if not p["bound"]]
    alt = None
    if state == "AMBIGUOUS_DIRECTION":
        other = rv[0] if best is fw[0] else fw[0]
        o_order = list(range(1, len(P) + 1)) if other["direction"] == "FORWARD" else list(range(len(P), 0, -1))
        alt = [dict(s, index=idx, printed_m=P[idx - 1]) for s, idx in zip(other["spans"], o_order)]
    return {"state": state, "direction": best["direction"], "spans": spans, "alternative_spans": alt,
            "inherited": inherited, "residuals": best["residuals"], "printed_m": P,
            "decided_by": "LOWER_RESIDUAL" if (fw and rv and state.startswith("MATCH_") and state != "MATCH_SYMMETRIC")
            else ("ONE_READING_FITS" if state.startswith("MATCH_") else None)}


def _spans(cuts, win, u_m, basis):
    out = []
    for a, b in zip(cuts, cuts[1:]):
        lo = a["t_hi"] if a else None
        hi = b["t_lo"] if b else None
        # a free end (no support found) is the piece face
        if lo is None:
            lo = min(p["t0"] for p in win)
        if hi is None:
            hi = max(p["t1"] for p in win)
        ca = a["centre"] if a else lo
        cb = b["centre"] if b else hi
        drawn = (cb - ca) if basis == "AXIS" else (hi - lo)
        cover = [p for p in win if min(p["t1"], hi) - max(p["t0"], lo) > 1e-9]
        out.append({"drawn_m": drawn * u_m, "clear_m": (hi - lo) * u_m, "t0": lo, "t1": hi,
                    "pieces": [p["band_id"] for p in cover],
                    "piece_extents": {p["band_id"]: (p["t0"], p["t1"]) for p in cover},
                    "left": _gpub(a, u_m), "right": _gpub(b, u_m)})
    return out


def _gpub(g, u_m):
    if not g:
        return {"kind": "FREE_END", "width_m": 0.0}
    return {"kind": g["kind"], "width_m": (g["t_hi"] - g["t_lo"]) * u_m, "centre": g["centre"],
            "members": [m[0] for m in g["members"]]}


def _public(s):
    return {k: v for k, v in s.items() if k != "spans"} | {"drawn_m": [round(x["drawn_m"], 3) for x in s["spans"]]}


# ------------------------------------------------------------------ physical bars
def physical_bars(m, row, *, anchorage_d=(0, 40, 50), support_frac=(0.20, 0.25, 0.33), support_basis="CLEAR",
                  bottom_ext_m=(0.075, 0.15, 0.30), lap_d=(40, 50, 60), stock_m=12.0):
    """m: a match() result with spans; row: the schedule row. -> {groups, missing}.
    Lengths are (low, base, high) triples in metres; a group's 'share' gives the length of the group in each span
    (by schedule span index) so that it can be allocated to the span's pieces once. support_basis: the span a support
    bar's fraction is taken of - CLEAR (face to face) or AXIS (support centre to support centre)."""
    span_of = (lambda s: s["clear_m"]) if support_basis == "CLEAR" else (lambda s: s["drawn_m"])
    rl, empty = roles(row)
    spans = sorted(m["spans"], key=lambda s: s["index"])
    n = len(spans)
    by_ix = {s["index"]: s for s in spans}
    groups, missing = [], []

    def add(role, k, bar, length3, share, basis):
        L3 = tuple(_with_laps(L, bar["dia_mm"], lap_d[i], stock_m) for i, L in enumerate(length3))
        groups.append({"bar_id": f"{row['mark']}:{role}{k or ''}", "role": role, "k": k, "count": bar["count"],
                       "dia_mm": bar["dia_mm"], "length_m": L3, "share": share, "basis": basis})

    for k in range(1, n + 1):
        s = by_ix[k]
        bar = rl.get(("BOTTOM", k)) or (rl.get(("BOTTOM", 0)) if n == 1 else None)
        if bar:
            d = bar["dia_mm"] / 1000.0
            ext = []
            for side in ("left", "right"):
                g = s[side]
                interior = g["kind"] != "FREE_END" and _is_interior(s, side, n)
                ext.append([g["width_m"] + e for e in bottom_ext_m] if interior else [a * d for a in anchorage_d])
            L3 = tuple(s["clear_m"] + ext[0][i] + ext[1][i] for i in range(3))
            add("BOTTOM", k, bar, L3, {k: 1.0}, "clear span + extension each side (interior: support width + "
                                                  "extension; end: anchorage)")
        else:
            missing.append(("BOTTOM", k, "EMPTY_CELL" if ("BOTTOM", k) in empty else "NOT_PRINTED"))
        st = rl.get(("STIRRUP", k)) or (rl.get(("STIRRUP", 0)) if n == 1 else None)
        if st:
            groups.append({"bar_id": f"{row['mark']}:STIRRUP{k}", "role": "STIRRUP", "k": k, "rate_per_m": st["count"],
                           "count": st["count"] * s["clear_m"] + 1, "dia_mm": st["dia_mm"], "length_m": None,
                           "share": {k: 1.0}, "basis": "rate x clear span + 1, closed link"})
        else:
            missing.append(("STIRRUP", k, "EMPTY_CELL" if ("STIRRUP", k) in empty else "NOT_PRINTED"))
    for j in range(1, n):
        a, b = by_ix[j], by_ix[j + 1]
        bar = rl.get(("SUPPORT_TOP", j)) or (rl.get(("SUPPORT_TOP", 0)) if n == 2 else None)
        if not bar:
            why = "EMPTY_CELL" if (("SUPPORT_TOP", j) in empty or (n == 2 and ("SUPPORT_TOP", 0) in empty)) else \
                ("AMBIGUOUS_UNINDEXED" if ("SUPPORT_TOP", 0) in rl else "NOT_PRINTED")
            missing.append(("SUPPORT_TOP", j, why))
            continue
        sw = _shared_support_width(a, b)
        L3 = tuple(f * span_of(a) + sw + f * span_of(b) for f in support_frac)
        la, lb = support_frac[1] * span_of(a) + sw / 2, support_frac[1] * span_of(b) + sw / 2
        add("SUPPORT_TOP", j, bar, L3, {j: la / (la + lb), j + 1: lb / (la + lb)},
            "support width + fraction x clear span on each side")
    top = rl.get(("TOP_THROUGH", 0))
    if top:
        tot = sum(s["clear_m"] for s in spans) + sum(_shared_support_width(by_ix[j], by_ix[j + 1])
                                                       for j in range(1, n))
        d = top["dia_mm"] / 1000.0
        L3 = tuple(tot + 2 * a * d for a in anchorage_d)
        share = {s["index"]: s["clear_m"] / sum(x["clear_m"] for x in spans) for s in spans}
        add("TOP_THROUGH", 0, top, L3, share, "whole beam + anchorage at both ends, laps at the stock length")
    elif not any(r == "TOP_SPAN" for r, _ in rl):
        missing.append(("TOP_THROUGH", 0, "EMPTY_CELL" if ("TOP_THROUGH", 0) in empty else "NOT_PRINTED"))
    for k in range(1, n + 1):
        bar = rl.get(("TOP_SPAN", k))
        if bar:
            d = bar["dia_mm"] / 1000.0
            s = by_ix[k]
            L3 = tuple(s["clear_m"] + 2 * a * d for a in anchorage_d)
            add("TOP_SPAN", k, bar, L3, {k: 1.0}, "clear span + anchorage")
    return {"groups": groups, "missing": missing, "n_spans": n}


def _is_interior(s, side, n):
    return (side == "left" and s["index"] > 1) or (side == "right" and s["index"] < n) if s.get("index") else False


def _shared_support_width(a, b):
    for g in (a["right"], a["left"]):
        for h in (b["left"], b["right"]):
            if g.get("centre") is not None and g.get("centre") == h.get("centre"):
                return g["width_m"]
    return max(a["right"]["width_m"], b["left"]["width_m"])


def _with_laps(L, d_mm, lap_d, stock_m):
    if L <= stock_m:
        return L
    n = math.ceil(L / stock_m) - 1
    return L + n * lap_d * d_mm / 1000.0


def allocate(groups, spans, link_mass_kg=None):
    """mass of each group shared out to the span pieces: -> {band_id: {(role, dia): [low, base, high]}} and the
    per-group totals (so that the sum over pieces equals the sum over groups - a conservation check)."""
    by_ix = {s["index"]: s for s in spans}
    alloc, totals = {}, []
    for g in groups:
        if g["role"] == "STIRRUP":
            if link_mass_kg is None:
                continue
            m3 = tuple(g["count"] * x for x in link_mass_kg(g))
        else:
            kg_m = g["dia_mm"] ** 2 / 162.0
            m3 = tuple(g["count"] * kg_m * L for L in g["length_m"])
        totals.append((g["bar_id"], m3))
        for k, f in g["share"].items():
            s = by_ix[k]
            span_len = s["t1"] - s["t0"]
            pcs = s["pieces"]
            ov = {}
            for pid, (t0, t1) in s.get("piece_extents", {}).items():
                ov[pid] = max(0.0, min(t1, s["t1"]) - max(t0, s["t0"]))
            if not ov:
                ov = {pid: 1.0 for pid in pcs}
            tot = sum(ov.values()) or 1.0
            for pid in pcs:
                w = f * ov.get(pid, 0.0) / tot
                r = alloc.setdefault(pid, {}).setdefault((g["role"], g["dia_mm"]), [0.0, 0.0, 0.0])
                for i in range(3):
                    r[i] += w * m3[i]
            _ = span_len
    return alloc, totals


def policy_record():
    return {"policy": POLICY_ID, "states": list(STATES),
            "rule": "an unlabelled piece takes a continuous-beam mark only when it is one of the spans whose lengths "
                    "match the schedule's printed span sequence; bars are physical groups (a through bar once per "
                    "line); a role the schedule does not print is missing, never invented"}
