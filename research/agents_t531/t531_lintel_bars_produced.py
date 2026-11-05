"""T-531: B9-02 LINTEL BARS on the measured lintel ends (research rule proposal R-T531-1; research only, nothing in
engine/ or tools/ imports it; no candidate or released quantity changes here). Successor of R-T515-1 for the ends that
T-516 / T-519 / T-524 / T-527 have now measured; R-T515-1 and every merged module are imported read-only, never edited.

Physical element (ERS s.2.1). One cast RC lintel per opening: bottom and top main bars of the printed band (bar marks
B1 / T1), closed links at the printed rate (mark S1). A main bar = its SPAN part over the lintel's own clear span
(w_net = opening width minus any strip of the span that lies inside a column outline), one straight EXTENSION beyond
each jamb, and one drawn END BEND at each end. The extension and the bend are what the structural detail leaves
open: the detail draws the bar running into the bearing and turned there, with no cover, no bend / hook length and no
first-link position printed (p.8 note 22 prints only a 'not less than' cover for columns, slabs and beams).

What the measured ends add (the question T-515 left open): a CEILING per end on how far a straight bar can run, from
what physically surrounds that end (never a value, never summed in):
  BOUNDED masonry end (a >= printed minimum)  the lintel rests on the pier and the detail applies: the bar stays in the
                                              lintel concrete, which cannot run past the pier: extension <= a.
  DEFICIT end at a COLUMN                     the detail does not apply (no masonry bearing). The lintel concrete stops
                                              at the column face (R-T524-1), but its bars may be anchored into the
                                              column (designer item): a bar cannot pass the column's far face, so
                                              extension <= a + column depth along the wall (frame registration: the
                                              larger of the two drawn gaps, so the ceiling holds in both frames).
  DEFICIT end at the end of the masonry       extension <= a (the far face of the cross wall / wall end).
  DEFICIT end at a shared pier                extension <= p (the pier; two lintels share it, a combined lintel is a
                                              designer item: the per-lintel ceiling p is still a ceiling of each).
  HELD end / search-capped pier               no ceiling: the straight ceiling of that lintel is HELD by name.
Values (COMPUTED) need printed sources: the extension = exact printed bearing - printed end cover (a 'MIN' bearing is
never exact); a bend = its printed length; links = printed spacing / rate + printed first-link offset (Q-71: the count
follows the drawing's positions; without them the count is PROVISIONAL with the interpretations shown) and their kg =
printed cover + printed hook. A default, a scaled length (ST7757 p.8 note 3: dimensions are read, never scaled) or a
borrowed value is refused.

Line figure: AT_LEAST = the COMPUTED parts (span parts here), split PRODUCED part + FLAGGED part (R-T519-1 states),
never one number; the straight ceiling beside where every end has one. kg/m: rebar_unit_mass D2_OVER_162 (owner kg = L x
d^2 / 162); laps: rebar_lap_rule_v2 on the straight ceiling (owner stock 12 m, class BEAM 60 d); t only at the boundary.

    python3 -I research/agents_t531/t531_lintel_bars_produced.py     # writes out/LINTEL_BARS_T531.json
"""
from __future__ import annotations

import hashlib
import json
import sys
from fractions import Fraction
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
for p in (ROOT, HERE.parent / "agents_t515", HERE.parent / "agents_t524", HERE.parent / "agents_t527"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from engine.source import rebar_lap_rule_v2 as LAP  # noqa: E402  (read only)
from engine.source import rebar_unit_mass as UM  # noqa: E402  (read only)
import t515_lintel_bars as T515  # noqa: E402  (read only)

RULE_ID = "R-T531-1"
UNIT_MASS = T515.UNIT_MASS
STOCK_M = T515.STOCK_M
LAP_KIND = T515.LAP_KIND
COMPUTED, HELD, NOT_REQUIRED, PROVISIONAL = "COMPUTED", "HELD", "NOT_REQUIRED", "PROVISIONAL"
AT_LEAST, COMPLETE = "AT_LEAST", "COMPLETE"
PRODUCED, FLAGGED = "PRODUCED", "FLAGGED"
END_KINDS = ("MASONRY", "COLUMN", "END_OF_MASONRY", "PIER", "HELD")
MAX_M = 20.0
EPS = Fraction(1, 10 ** 9)
DETAILS = ("end_cover_m", "bend_m", "link_cover_m", "link_hook_m", "first_link_m")


class LintelBarsError(ValueError):
    pass


def _f(x):
    return Fraction(str(x))


def _ceil(q):
    return -((-q.numerator) // q.denominator)


def _floor(q):
    return q.numerator // q.denominator


def _r(x, n=6):
    return None if x is None else round(float(x) + 0.0, n)


def _m(v, where, allow_zero=True):
    if v is None or isinstance(v, bool):
        raise LintelBarsError(f"{where}: length missing")
    q = _f(v)
    if q < 0 or q > MAX_M or (q == 0 and not allow_zero):
        raise LintelBarsError(f"{where}: {v!r} is not a length in metres")
    return q


def _printed(rec, key):
    """a detail length only with a printed source; a bare value is a default (refused)."""
    v = rec.get(key)
    if v is None:
        return None
    if not str(rec.get(key + "_source") or "").upper().startswith("PRINTED"):
        raise LintelBarsError(f"{rec.get('opening_id')}: {key} {v} has no printed source (a default, a scaled or a "
                              "borrowed length is refused; the part stays HELD)")
    q = _f(v)
    if q <= 0 or q > 1:
        raise LintelBarsError(f"{rec.get('opening_id')}: printed {key} {v} is not a detail length in metres")
    return q


def links_text(text, where):
    """'5Ø8/M' -> ('RATE', 5 per m, 8) ; 'Ø8@150' / 'R8@150' -> ('SPACING', 0.150 m, 8). Anything else refused."""
    import re
    t = (text or "").strip()
    m = re.fullmatch(r"(\d+)\s*[ØøRr×xX]\s*(\d+(?:\.\d+)?)\s*/\s*[Mm]", t)
    if m:
        return "RATE", Fraction(int(m.group(1))), float(m.group(2))
    m = re.fullmatch(r"[ØøRrTtYy]\s*(\d+(?:\.\d+)?)\s*@\s*(\d+)", t)
    if m:
        s = Fraction(int(m.group(2)), 1000)
        if not Fraction(1, 20) <= s <= Fraction(1, 2):
            raise LintelBarsError(f"{where}: link spacing {m.group(2)} mm outside 50 .. 500 mm")
        return "SPACING", s, float(m.group(1))
    raise LintelBarsError(f"{where}: link text {text!r} is neither '<n>Ø<d>/M' nor 'Ø<d>@<s mm>'")


def end_ceiling(end, where):
    """one end -> (extension lo, extension hi or None, kind, basis). lo / hi bound the lintel CONCRETE beyond the jamb;
    bar_hi bounds the straight BAR beyond the jamb (differs at a column end only)."""
    kind = end.get("kind")
    if kind not in END_KINDS:
        raise LintelBarsError(f"{where}: end kind {kind!r} not in {END_KINDS}")
    b_min = end.get("b_min_m")
    a = None if end.get("a_m") is None else _m(end["a_m"], f"{where} a")
    if kind == "HELD":
        return {"kind": kind, "conc_lo": Fraction(0), "conc_hi": None, "bar_hi": None,
                "basis": end.get("why") or "end junction not resolved: no ceiling (HELD by name)"}
    if a is None:
        raise LintelBarsError(f"{where}: a {kind} end needs its measured masonry a (or kind HELD)")
    if kind == "MASONRY":
        if b_min is None:
            raise LintelBarsError(f"{where}: a MASONRY bearing end needs the printed minimum bearing")
        b = _m(b_min, f"{where} b_min", allow_zero=False)
        if a + EPS < b:
            raise LintelBarsError(f"{where}: a = {float(a)} < printed minimum {float(b)} is a deficit, not a bearing end")
        if end.get("capped"):
            return {"kind": kind, "conc_lo": b, "conc_hi": None, "bar_hi": None,
                    "basis": f"pier at least {float(a)} m (search capped): no finite ceiling, HELD by name"}
        return {"kind": kind, "conc_lo": b, "conc_hi": a, "bar_hi": a,
                "basis": f"bearing on masonry in [{float(b)}, {float(a)}] m; the bar stays in the lintel concrete"}
    if b_min is not None and a + EPS >= _f(b_min):
        raise LintelBarsError(f"{where}: a {kind} end with a = {float(a)} >= the printed minimum is not a deficit")
    if kind == "COLUMN":
        col = end.get("column") or {}
        if col.get("along_m") is None:
            return {"kind": kind, "conc_lo": Fraction(0), "conc_hi": a, "bar_hi": None,
                    "basis": "column at the end not identified: the bar ceiling into the column is HELD by name"}
        along = _m(col["along_m"], f"{where} column depth", allow_zero=False)
        gaps = [a] + [_m(g, f"{where} gap") for g in (col.get("gap_alt_m"),) if g is not None]
        # a and the gaps are measured from the lintel's own end face (the jamb, or the column face where the span
        # strip lies inside the column), so the far face is max(gap) + depth beyond it
        reach = max(gaps) + along
        return {"kind": kind, "conc_lo": Fraction(0), "conc_hi": a, "bar_hi": reach,
                "basis": f"lintel stops at the face of {col.get('id')} (concrete <= a = {float(a)} m); its bars may be "
                         f"anchored into the column (designer item) and cannot pass its far face: bar <= "
                         f"{float(max(gaps))} + column depth {float(along)} m"
                         + (f" (from the column face: {end.get('strip_m')} m of the opening is inside the column)"
                            if end.get("strip_m") else "")}
    if kind == "END_OF_MASONRY":
        return {"kind": kind, "conc_lo": Fraction(0), "conc_hi": a, "bar_hi": a,
                "basis": f"masonry ends {float(a)} m beyond the jamb (cross-wall far face / wall end): bar <= a"}
    return {"kind": kind, "conc_lo": Fraction(0), "conc_hi": a, "bar_hi": a, "shared_with": end.get("shared_with"),
            "basis": f"shared pier {float(a)} m with {end.get('shared_with')}: each lintel's bar <= the pier"}


def _comp(mark, role, part, state, kg=None, **kw):
    if state in (HELD, PROVISIONAL) and kg is not None:
        raise LintelBarsError(f"{mark} {part}: a {state} component carries a number")
    if state == COMPUTED and (kg is None or kg <= 0):
        raise LintelBarsError(f"{mark} {part}: a COMPUTED component without a positive kg")
    return dict(mark=mark, role=role, part=part, state=state, kg=None if kg is None else float(kg), **kw)


def lintel_bars(rec, umass=UNIT_MASS):
    """one lintel {opening_id, piece_state PRODUCED / FLAGGED, width_m, span_in_column_m, schedule_row, bottom, top,
    links, B_m, D_m, ends: [{side, kind, a_m, b_min_m, [column], [strip_m], [capped], [shared_with]}], bearing_exact_m
    (+ _source PRINTED), detail lengths (+ _source PRINTED)} -> bar marks, segments, kg, ceilings."""
    oid = rec.get("opening_id")
    if rec.get("piece_state") not in (PRODUCED, FLAGGED):
        raise LintelBarsError(f"{oid}: piece state {rec.get('piece_state')!r} is not PRODUCED / FLAGGED (a HELD "
                              "opening carries no bar figure)")
    for k in DETAILS:
        _printed(rec, k)
    w = _m(rec.get("width_m"), f"{oid} width", allow_zero=False)
    strip = _m(rec.get("span_in_column_m", 0), f"{oid} span strip")
    w_net = w - strip
    if w_net <= 0:
        raise LintelBarsError(f"{oid}: net span {float(w_net)} <= 0")
    lo, hi = rec.get("band_lo_m"), rec.get("band_hi_m")
    if lo is not None and hi is not None and not (_f(lo) - EPS <= w <= _f(hi) + EPS):
        raise LintelBarsError(f"{oid}: width {float(w)} m outside its printed band {rec.get('schedule_row')}")
    ends = rec.get("ends") or []
    if len(ends) != 2 or {e.get("side") for e in ends} != {"START", "END"}:
        raise LintelBarsError(f"{oid}: needs exactly one START and one END")
    ends = sorted(ends, key=lambda e: e["side"] != "START")
    ec = [end_ceiling(e, f"{oid} {e['side']}") for e in ends]
    exact_b = None
    if rec.get("bearing_exact_m") is not None:
        if not str(rec.get("bearing_exact_m_source") or "").upper().startswith("PRINTED"):
            raise LintelBarsError(f"{oid}: an exact bearing needs a printed source (a 'MIN' bearing is never exact)")
        exact_b = _m(rec["bearing_exact_m"], f"{oid} exact bearing", allow_zero=False)
        for e, c in zip(ends, ec):
            if c["kind"] != "MASONRY" or (c["conc_hi"] is not None and c["conc_hi"] + EPS < exact_b):
                raise LintelBarsError(f"{oid} {e['side']}: the printed bearing {float(exact_b)} m does not fit the "
                                      f"measured end ({c['kind']}, a = {e.get('a_m')})")
    cover, bend = _printed(rec, "end_cover_m"), _printed(rec, "bend_m")
    if exact_b is not None and cover is not None and cover >= exact_b:
        raise LintelBarsError(f"{oid}: printed end cover leaves no bar in the bearing")
    conc_lo = w_net + sum(c["conc_lo"] for c in ec)
    conc_hi = None if any(c["conc_hi"] is None for c in ec) else w_net + sum(c["conc_hi"] for c in ec)
    if exact_b is not None:
        conc_lo = conc_hi = w_net + 2 * exact_b
    bar_hi = None if any(c["bar_hi"] is None for c in ec) else w_net + sum(c["bar_hi"] for c in ec)
    comps = []
    for role, key, mark in (("BOTTOM", "bottom", "B1"), ("TOP", "top", "T1")):
        try:
            n, d = T515.bars(rec.get(key), f"{oid} {role}")
        except T515.LintelBarError as exc:
            raise LintelBarsError(str(exc)) from exc
        kgm = _f(UM.kg_per_m(d, umass))
        base = dict(n=n, dia_mm=d, kg_per_m=_r(kgm))
        comps.append(_comp(mark, role, "SPAN", COMPUTED, n * w_net * kgm, length_each_m=_r(w_net),
                           basis=f"{n} x own clear span {float(w_net)} m x {_r(kgm)} kg/m (drawn across the opening)"
                                 + (f"; {float(strip)} m of the opening lies inside a column outline" if strip else ""),
                           **base))
        for e, c in zip(ends, ec):
            if exact_b is not None and cover is not None:
                seg = exact_b - cover
                comps.append(_comp(mark, role, f"EXTENSION_{e['side']}", COMPUTED, n * seg * kgm,
                                   length_each_m=_r(seg), basis=f"printed bearing {float(exact_b)} - printed end "
                                                                f"cover {float(cover)} m", **base))
            else:
                comps.append(_comp(mark, role, f"EXTENSION_{e['side']}", HELD, end_kind=c["kind"],
                                   ceiling_each_m=_r(c["bar_hi"]),
                                   ceiling_kg_beside=None if c["bar_hi"] is None else float(n * c["bar_hi"] * kgm),
                                   why=("end cover not printed (a 'not less than' minimum is not the value); "
                                        if exact_b is not None else
                                        "the built bearing is a range, the end cover is not printed; ")
                                   + c["basis"], **base))
            if bend is not None:
                comps.append(_comp(mark, role, f"BEND_{e['side']}", COMPUTED, n * bend * kgm, length_each_m=_r(bend),
                                   basis=f"printed bend {float(bend)} m", **base))
            else:
                comps.append(_comp(mark, role, f"BEND_{e['side']}", HELD,
                                   why="end bend drawn, its length not printed (no default, no scaling)", **base))
        if bar_hi is not None:
            lap = LAP.bar_with_laps(str(float(bar_hi)), d, LAP_KIND, stock=STOCK_M)
            if lap["state"] == NOT_REQUIRED:
                comps.append(dict(mark=mark, role=role, part="LAPS", state=NOT_REQUIRED, kg=0.0, laps=0, n=n,
                                  dia_mm=d, basis=f"straight bar at most {_r(bar_hi)} m within the {STOCK_M} m stock"))
            else:
                comps.append(_comp(mark, role, "LAPS", HELD, n=n, dia_mm=d, laps_per_bar=lap.get("laps"),
                                   why="the straight ceiling exceeds the stock: splice count beside, run HELD"))
        else:
            comps.append(_comp(mark, role, "LAPS", HELD, n=n, dia_mm=d,
                               why="no straight ceiling (an end is HELD / uncapped): laps HELD with it"))
    # links (mark S1): count by the drawing's positions (Q-71), kg by printed cover + hook
    kind, val, ld = links_text(rec.get("links"), f"{oid} LINKS")
    s = (1 / val) if kind == "RATE" else val
    first = _printed(rec, "first_link_m")
    lcov, lhook = _printed(rec, "link_cover_m"), _printed(rec, "link_hook_m")
    exact_L = conc_lo if (conc_hi is not None and conc_lo == conc_hi) else None
    link = dict(mark="S1", role="LINKS", dia_mm=ld, spacing_m=_r(s), notation=rec.get("links"))
    if exact_L is not None and first is not None:
        if 2 * first >= exact_L:
            raise LintelBarsError(f"{oid}: printed first-link offset leaves no link")
        N = 1 + _floor((exact_L - 2 * first) / s)
        link.update(count_state=COMPUTED, count=N, count_basis=f"1 + floor((L {float(exact_L)} - 2 x first link "
                                                                  f"{float(first)}) / {float(s)}) (Q-71)")
    else:
        alt_lo = None if conc_lo is None else _ceil(conc_lo / s)
        alt_hi = None if conc_hi is None else _ceil(conc_hi / s)
        link.update(count_state=PROVISIONAL, count=None,
                    count_lo=alt_lo, count_hi=alt_hi,
                    count_alt_lo=None if conc_lo is None else 1 + _floor(conc_lo / s),
                    count_alt_hi=None if conc_hi is None else 1 + _floor(conc_hi / s),
                    count_basis="first-link position not printed for the lintel and / or the length is a range "
                                "(Q-71: never N = n L + 1 by default): RATE_COUNT ceil(L / s) over the concrete "
                                "range, 1 + floor(L / s) (links at both end faces) beside")
    B, D = rec.get("B_m"), rec.get("D_m")
    if link["count_state"] == COMPUTED and lcov is not None and lhook is not None and B is not None and D is not None:
        Bq, Dq = _m(B, f"{oid} B", False), _m(D, f"{oid} D", False)
        if 2 * lcov >= min(Bq, Dq):
            raise LintelBarsError(f"{oid}: printed link cover leaves no link")
        cut = 2 * ((Bq - 2 * lcov) + (Dq - 2 * lcov)) + lhook
        kgm = _f(UM.kg_per_m(ld, umass))
        comps.append(_comp("S1", "LINKS", "LINKS", COMPUTED, link["count"] * cut * kgm,
                           cut_each_m=_r(cut), kg_per_m=_r(kgm), **{k: v for k, v in link.items()
                                                                     if k not in ("mark", "role")}))
    else:
        comps.append(_comp("S1", "LINKS", "LINKS", HELD,
                           why="link kg needs the printed count, cover and hook (not all printed): HELD; the count is "
                               "shown", **{k: v for k, v in link.items() if k not in ("mark", "role")}))
    computed = sum(_f(c["kg"]) for c in comps if c["state"] == COMPUTED)
    held = [f"{c['mark']} {c['part']}" for c in comps if c["state"] == HELD]
    span_kg = sum(_f(c["kg"]) for c in comps if c["part"] == "SPAN")
    ceil_kg = None
    if bar_hi is not None and exact_b is None:
        ceil_kg = span_kg + sum(_f(c["ceiling_kg_beside"]) for c in comps if c["part"].startswith("EXTENSION_"))
    out = {"opening_id": oid, "floor": rec.get("floor"), "rule": RULE_ID, "piece_state": rec["piece_state"],
           "schedule_row": rec.get("schedule_row"), "width_m": _r(w), "w_net_m": _r(w_net),
           "span_in_column_m": _r(strip), "concrete_length_lo_m": _r(conc_lo), "concrete_length_hi_m": _r(conc_hi),
           "bar_straight_hi_m": _r(bar_hi),
           "ends": [dict(side=e["side"], kind=c["kind"], a_m=e.get("a_m"), conc_hi_m=_r(c["conc_hi"]),
                         bar_hi_m=_r(c["bar_hi"]), basis=c["basis"]) for e, c in zip(ends, ec)],
           "state": COMPLETE if not held else AT_LEAST, "kg": float(computed) if not held else None,
           "at_least_kg": float(computed), "held_parts": held,
           "ceiling_straight_kg_beside": None if ceil_kg is None else float(ceil_kg),
           "components": comps}
    if ceil_kg is not None and ceil_kg + EPS < computed:
        raise LintelBarsError(f"{oid}: ceiling {float(ceil_kg)} below the computed parts {float(computed)} (inverted)")
    return check_row(out)


def check_row(row):
    for c in row["components"]:
        if c["state"] in (HELD, PROVISIONAL) and c.get("kg") is not None:
            raise LintelBarsError(f"{row['opening_id']} {c['mark']} {c['part']}: HELD summed as {c['kg']} (refused)")
    s = sum(_f(c["kg"]) for c in row["components"] if c["state"] == COMPUTED)
    if abs(float(s) - row["at_least_kg"]) > 1e-9:
        raise LintelBarsError(f"{row['opening_id']}: at_least {row['at_least_kg']} != computed parts {float(s)}")
    if row["state"] == COMPLETE and row["held_parts"]:
        raise LintelBarsError(f"{row['opening_id']}: COMPLETE with held parts")
    return row


def ledger(records, umass=UNIT_MASS):
    seen, rows = set(), []
    for r in records:
        if r.get("opening_id") in seen:
            raise LintelBarsError(f"{r.get('opening_id')}: a second record for one opening")
        seen.add(r.get("opening_id"))
        rows.append(lintel_bars(r, umass))
    return {"rule": RULE_ID, "unit_mass": UM.describe(umass), "rows": rows, "line": line(rows)}


def _part(rows):
    if not rows:
        return {"lintels": [], "state": "NONE"}
    complete = all(r["state"] == COMPLETE for r in rows)
    ceil_ok = all(r["ceiling_straight_kg_beside"] is not None for r in rows)
    return {"lintels": [r["opening_id"] for r in rows],
            "state": COMPLETE if complete else AT_LEAST,
            "at_least_kg": _r(sum(_f(r["at_least_kg"]) for r in rows)),
            "kg": _r(sum(_f(r["kg"]) for r in rows)) if complete else None,
            "ceiling_straight_kg_beside": _r(sum(_f(r["ceiling_straight_kg_beside"]) for r in rows)) if ceil_ok else None,
            "ceiling_held_on": [r["opening_id"] for r in rows if r["ceiling_straight_kg_beside"] is None],
            "ceiling_straight_kg_where_known_beside": _r(sum(_f(r["ceiling_straight_kg_beside"]) for r in rows
                                                            if r["ceiling_straight_kg_beside"] is not None)),
            "span_kg_where_ceiling_known": _r(sum(_f(r["at_least_kg"]) for r in rows
                                                  if r["ceiling_straight_kg_beside"] is not None)),
            "links_count_lo": sum(c.get("count_lo") or c.get("count") or 0 for r in rows for c in r["components"]
                                  if c["mark"] == "S1"),
            "held_parts": sorted({p for r in rows for p in r["held_parts"]})}


def line(rows):
    """the B9-02 lintel bar line: PRODUCED part + FLAGGED part, never one number."""
    for r in rows:
        check_row(r)
    p = _part([r for r in rows if r["piece_state"] == PRODUCED])
    f = _part([r for r in rows if r["piece_state"] == FLAGGED])
    states = {x["state"] for x in (p, f) if x["state"] != "NONE"}
    return {"produced": p, "flagged": f,
            "state": COMPLETE if states == {COMPLETE} else AT_LEAST,
            "at_least_kg_by_part": {"produced": p.get("at_least_kg"), "flagged": f.get("at_least_kg")},
            "note": "two parts, never summed into one figure while any part is HELD; HELD never 0"}


# ------------------------------------------------------------------------------------- training-villa builder
OUT = HERE / "out" / "LINTEL_BARS_T531.json"
T515_OUT = ROOT / "research/agents_t515/out/LINTEL_BAR_SPLIT_T515.json"


def villa_records():
    """the 16 REQUIRED lintels: bars / band / width from the pinned T-515 records (T-453 r2 ledger + printed schedule,
    asserted equal there), ends from the V3 jamb census (T-527, pinned evidence, merged T-516 rule), deficit-end hosts
    and the span strip from T-524 (merged inputs; a must agree with V3 to 1 mm or the build is refused)."""
    import t527_effect as E          # noqa: E402  (read only)
    import t524_lintel_end_ownership as T524  # noqa: E402  (read only)
    base = {r["opening_id"]: r for r in T515.records() if r["decision"] == T515.REQUIRED}
    v3 = {r["opening_id"]: r for r in E.census("V3")["rows"] if r["decision"] == "REQUIRED"}
    if set(base) != set(v3) or len(base) != 16:
        raise LintelBarsError("the T-515 records and the V3 census differ in their REQUIRED lintels")
    t524, pairs = T524.villa_inputs()
    host = {(l["id"], e["side"]): (l, e) for l in t524 for e in l["ends"]}
    pair_of = {}
    for a_id, b_id in pairs:
        pair_of[a_id], pair_of[b_id] = b_id, a_id
    b_min = float(T515.schedule()[1])
    out = []
    for oid, b in sorted(base.items()):
        row = v3[oid]
        strip = T524.SPAN_IN_COLUMN.get(oid, (0.0, None))[0]
        ends = []
        for e in row["ends"]:
            x = {"side": e["side"], "b_min_m": b_min}
            st, a = e["state"], e.get("available_trusted_m")
            if st == "BOUNDED":
                x.update(kind="MASONRY", a_m=a, capped=e.get("bearing_hi_m") is None)
            elif st == "FLAGGED_DEFICIT":
                l524, e524 = host[(oid, e["side"])]
                if abs(float(e524["available_m"]) - float(a)) > 0.0005:
                    raise LintelBarsError(f"{oid} {e['side']}: T-524 a {e524['available_m']} differs from V3 a {a}")
                x["a_m"] = a
                if e["stopper"] == "COLUMN":
                    h = e524.get("host") or {}
                    x.update(kind="COLUMN", strip_m=strip if h.get("id") == l524.get("span_column_id") else 0,
                             column={"id": h.get("id"), "along_m": h.get("along_m"),
                                     "gap_alt_m": max(0.0, h["gap_struct_frame_m"] + (strip if h.get("id") ==
                                                                                       l524.get("span_column_id")
                                                                                       else 0.0))
                                     if h.get("gap_struct_frame_m") is not None else None})
                elif e["stopper"] == "OPENING":
                    x.update(kind="PIER", shared_with=pair_of.get(oid))
                else:
                    x.update(kind="END_OF_MASONRY")
            else:
                x.update(kind="HELD", a_m=None, why=f"T-516 end HELD: {e.get('why')}")
            ends.append(x)
        out.append({"opening_id": oid, "floor": b.get("floor"),
                    "piece_state": PRODUCED if row["state"] == "BEARING_OK" else FLAGGED,
                    "width_m": b["width_m"], "span_in_column_m": strip, "schedule_row": b["schedule_row"],
                    "band_lo_m": b.get("band_lo_m"), "band_hi_m": b.get("band_hi_m"),
                    "bottom": b["bottom"], "top": b["top"], "links": b["stirrups"], "ends": ends})
    return out


def reconcile(doc):
    """against the merged T-515 AT_LEAST (span over the full width) and the T-516 straight ceilings, lintel by lintel."""
    import t527_effect as E          # noqa: E402
    t515 = {r["opening_id"]: r for r in json.loads(T515_OUT.read_text(encoding="utf-8"))["rows"]}
    t516 = {r["opening_id"]: r for r in E.census("V3")["rows"]}
    rows = []
    for r in doc["rows"]:
        o = r["opening_id"]
        rows.append({"opening_id": o, "piece_state": r["piece_state"],
                     "t515_at_least_kg": _r(t515[o]["at_least_kg"]), "t531_at_least_kg": _r(r["at_least_kg"]),
                     "delta_kg": _r(r["at_least_kg"] - t515[o]["at_least_kg"]),
                     "t516_v3_straight_ceiling_kg": _r(t516[o].get("straight_ceiling_kg")),
                     "t531_straight_ceiling_kg": _r(r["ceiling_straight_kg_beside"]),
                     "cause": ("span strip inside the column outline is not the lintel's own span"
                               if r["span_in_column_m"] else "")})
    return rows


def build():
    doc = ledger(villa_records())
    doc["reconciliation"] = reconcile(doc)
    t515 = json.loads(T515_OUT.read_text(encoding="utf-8"))["rows"]
    t = sum(_f(x["at_least_kg"]) for x in t515 if x["state"] != "HELD")
    n = sum(_f(x["at_least_kg"]) for x in doc["rows"])
    doc["reconciliation_total"] = {"t515_at_least_kg": _r(t), "t531_at_least_kg": _r(n), "delta_kg": _r(n - t)}
    doc["sources"] = {"t515_records": "research/agents_t515 (pinned T-453 r2 ledger + S8.6 schedule transcription)",
                      "ends": "research/agents_t527/out/JAMB_EVIDENCE_V3_T527.csv via t527_effect.census('V3')",
                      "hosts": "research/agents_t524 villa_inputs (crosswalk + census, merged)",
                      "drawing_read": "Drive 'Alsenan chalet project' / ST7757.pdf p.13 LINTEL DETAIL + SCHEDULE + "
                                      "SECT 2-2, p.8 notes 3 / 9 / 22 (re-read by worker 1 2026-11-05; no cover, bend, "
                                      "hook or first-link length printed for lintels; note 3: never scale)"}
    doc["freelancer"] = {"verdict": "UNRESOLVED", "why": "the freelancer RC workbook has one project rebar total and no "
                                                         "lintel row: no element figure to compare"}
    return doc


def render(doc):
    return json.dumps(doc, ensure_ascii=False, indent=1, sort_keys=True, default=str) + "\n"


def sha(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


if __name__ == "__main__":
    d = build()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(render(d), encoding="utf-8")
    print(json.dumps(d["line"], indent=1), json.dumps(d["reconciliation_total"]))
