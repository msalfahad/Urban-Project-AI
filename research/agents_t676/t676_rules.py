"""R-T676-1 / -2 / -3: PLASTER / RENDER / SPATTER / PAINT HELD-LINE CENSUS, face measure and coat materials
(every villa; research provenance, proposed; no new rule value, nothing wired or released).

R-T676-1 CENSUS. Every HELD line of the candidate whose code is a wall-coat or paint code (FIN.PLASTER, FIN.PAINT,
  FIN.EXT.FINISH, ARCH.FACADE, EXT.FENCE.PLASTER, EXT.FENCE.PAINT; any code holding SPATTER / RENDER) gets exactly ONE
  cause class, one primary source and the queued row that will wire it (T-314 exterior faces, T-364 spatter dash, or
  none). Classes:
    MEASURABLE_NOW       every term is printed on a sheet / the DXF or owner-fixed: a fix row with its own hand value
    OPEN_BOUND           a drawn low .. high bound exists; the open terms are named ranges (build-up b, contacts), no
                         single designer item closes it
    DESIGNER_ITEM        a designer clarification D-nn holds a term (opening height D-45, roof build-up D-39, ...)
    PRINTED_VALUE_GAP    a term is printed on no sheet and no D-nn of its own exists (named sheet / term)
    OWNER_DECISION_HOLD  an ANSWERED owner decision says HOLD (e.g. Q-54 B annex datum)
    OWNER_OPEN           an owner item still open (OWNER_NOTES_SIGMA item 3: site-wall finish scope)
    QUEUED_ROW           the quantity is measured face by face in merged ledgers and a queued integration row
                         REPLACES the line (T-314); an own figure here would count the faces twice
  Generic: one class per line; a freelancer figure is never a cause; HELD keeps measured_net None; a bound <= 0 is
  refused; the census count must equal the HELD lines of the candidate for these codes (no line missing, none twice).

R-T676-2 FACE MEASURE. A face = face length x the height the drawings fix (Q-72: a stair-shaft wall at its full
  exposed height, storey intervals added continuously; landing-slab edge bands deducted separately, never by lowering
  the height) - each opening ONLY where it physically exists on that face (Q-73), by its own width x its own height
  clipped to nothing: an opening higher than the face, wider than the face, or naming another face is refused (it is
  a data error, not a deduction). A full-height opening removes its whole strip. A door / opening reveal = 2 x wall
  thickness x height + wall thickness x width (UP-FIN-PLASTER-001); every term needs a source; an ASSUMED term needs
  its owner Q-id (Q-55 C: 2.20 m only where no sheet prints the height and the door is not the printed main entrance).

R-T676-3 COAT MATERIALS. cement bags / sand m3 per coat = area x thickness x dry factor x share / density (Q-53 C
  conversion: dry 1.33, cement 1,440 kg/m3, 50 kg bag), mix from Q-79 (internal plaster 1:4, external render 1:4,
  spatter dash 1:2). A HELD area gives a HELD material bound (low .. high from the area bound), never 0; a MINIMUM
  thickness gives an AT_LEAST figure; a coat with no thickness (spatter dash) or a face whose coat class is not
  established stays HELD by name; water stays HELD (no water : cement ratio is printed or owner-given).
"""
from __future__ import annotations

from decimal import Context, Decimal, localcontext

PREC = 40


def ctx40():
    """a local 40-digit Decimal context; importing this module never changes the process-global context."""
    return localcontext(Context(prec=PREC))


CODES = ("FIN.PLASTER", "FIN.PAINT", "FIN.EXT.FINISH", "ARCH.FACADE", "EXT.FENCE.PLASTER", "EXT.FENCE.PAINT")
CLASSES = ("MEASURABLE_NOW", "OPEN_BOUND", "DESIGNER_ITEM", "PRINTED_VALUE_GAP", "OWNER_DECISION_HOLD", "OWNER_OPEN",
           "QUEUED_ROW")
QUEUED = ("T-314", "T-364", "none")
FIX_STATUSES = ("DRAWING-CONFIRMED", "ASSUMED - OWNER-APPROVED")
FREELANCER_WORDS = ("freelancer", "his row", "his figure", "his total", "his sheet")
Q6 = Decimal("0.000001")

# Q-79 (owner 2026-11-09): cement : sand per coat; Q-53 C conversion (owner 2026-10-20)
MIX = {"WALL_PLASTER": (1, 4), "LEVELLING_RENDER": (1, 4), "EXTERNAL_RENDER": (1, 4), "BOND_COAT": (1, 2)}
DRY_FACTOR, CEMENT_KG_M3, BAG_KG = Decimal("1.33"), Decimal("1440"), Decimal("50")


class RuleError(Exception):
    pass


def D(x):
    return None if x is None or x == "" else Decimal(str(x))


def q(x):
    return D(x).quantize(Q6)


def S(x):
    if x is None:
        return None
    s = format(D(x).normalize(), "f")
    return "0" if s in ("-0", "0.0") else s


def code_in_scope(code):
    return code in CODES or "SPATTER" in code or "RENDER" in code


# ------------------------------------------------------------------ R-T676-1

def check_entry(e):
    lid = e.get("line_id")
    if not code_in_scope(e.get("item_code", "")):
        raise RuleError(f"{lid}: code {e.get('item_code')} not a wall-coat / paint code")
    if e.get("class") not in CLASSES:
        raise RuleError(f"{lid}: class {e.get('class')!r}")
    if e.get("queued_row") not in QUEUED:
        raise RuleError(f"{lid}: queued row {e.get('queued_row')!r}")
    if not e.get("cause") or not e.get("source"):
        raise RuleError(f"{lid}: no named cause / source")
    txt = (e["cause"] + " " + e["source"]).lower()
    for w in FREELANCER_WORDS:
        if w in txt:
            raise RuleError(f"{lid}: a freelancer figure is never a cause ({w!r})")
    if e.get("measured_net") is not None:
        raise RuleError(f"{lid}: a HELD line carries a value")
    lo, hi = D(e.get("held_low")), D(e.get("held_high"))
    if (lo is None) != (hi is None):
        raise RuleError(f"{lid}: half a bound")
    if lo is not None:
        if hi <= 0:
            raise RuleError(f"{lid}: bound {lo} .. {hi}: held as 0 refused")
        if lo > hi:
            raise RuleError(f"{lid}: low {lo} > high {hi}")
    mb = e.get("merged_bound")
    if mb:
        if lo is not None:
            raise RuleError(f"{lid}: a merged bound is only recorded beside a BLANK candidate line")
        if not mb.get("source") or D(mb["high"]) <= 0 or D(mb["low"]) > D(mb["high"]):
            raise RuleError(f"{lid}: merged bound {mb} refused")
    if e["class"] == "OPEN_BOUND" and lo is None and not mb:
        raise RuleError(f"{lid}: OPEN_BOUND without a bound")
    if e["class"] == "DESIGNER_ITEM" and not str(e.get("designer_ref", "")).startswith("D-"):
        raise RuleError(f"{lid}: DESIGNER_ITEM without its D-nn")
    if e["class"] in ("OWNER_DECISION_HOLD", "OWNER_OPEN") and not e.get("owner_ref"):
        raise RuleError(f"{lid}: owner class without its owner reference")
    if e["class"] == "QUEUED_ROW" and e["queued_row"] == "none":
        raise RuleError(f"{lid}: QUEUED_ROW must name the row that replaces the line")
    fx = e.get("fix")
    if e["class"] == "MEASURABLE_NOW" and not fx:
        raise RuleError(f"{lid}: MEASURABLE_NOW without its fix row")
    if fx:
        if e["class"] != "MEASURABLE_NOW":
            raise RuleError(f"{lid}: a fix row on a {e['class']} line")
        if fx.get("status") not in FIX_STATUSES:
            raise RuleError(f"{lid}: fix status {fx.get('status')!r}")
        if fx["status"] == "ASSUMED - OWNER-APPROVED" and not fx.get("owner_ref"):
            raise RuleError(f"{lid}: ASSUMED fix row without its owner Q-id")
        v = reveal_area(**{k: tuple(t) for k, t in fx["terms"].items()})
        if D(fx["value"]) != v:
            raise RuleError(f"{lid}: fix {fx['value']} != recomputed {v}")
        if fx.get("wired"):
            raise RuleError(f"{lid}: a fix row of this census is never wired")
    return True


def census(entries, held_ids):
    """entries vs the candidate's HELD line ids of the scope codes: same set, one class each."""
    seen = {}
    for e in entries:
        if e["line_id"] in seen:
            raise RuleError(f"{e['line_id']}: classed twice")
        check_entry(e)
        seen[e["line_id"]] = e
    missing = sorted(set(held_ids) - set(seen))
    extra = sorted(set(seen) - set(held_ids))
    if missing:
        raise RuleError(f"census misses HELD lines: {missing[:5]}")
    if extra:
        raise RuleError(f"census names lines that are not HELD in the candidate: {extra[:5]}")
    return totals(entries)


def totals(entries):
    with ctx40():
        out = {}
        for e in entries:
            k = f"{e['item_code']}|{e['unit']}"
            t = out.setdefault(k, {"lines": 0, "bounded": 0, "blank": 0, "low": Decimal(0), "high": Decimal(0),
                                   "by_class": {}, "fix_rows": 0})
            t["lines"] += 1
            t["by_class"][e["class"]] = t["by_class"].get(e["class"], 0) + 1
            if e.get("fix"):
                t["fix_rows"] += 1
            if e.get("held_low") is None:
                t["blank"] += 1
            else:
                t["bounded"] += 1
                t["low"] += D(e["held_low"])
                t["high"] += D(e["held_high"])
        for t in out.values():
            if t["bounded"]:
                t["low"], t["high"] = S(q(t["low"])), S(q(t["high"]))
                t["note"] = (f"{t['bounded']} bounded lines sum {t['low']} .. {t['high']}; {t['blank']} blank lines "
                             "HELD by name (not in the sum, never 0)")
            else:
                t["low"] = t["high"] = None
                t["note"] = f"no bounded line: {t['blank']} blank lines HELD by name (never 0)"
            t["by_class"] = dict(sorted(t["by_class"].items()))
        return dict(sorted(out.items()))


# ------------------------------------------------------------------ R-T676-2

def _term(name, t, lo=Decimal("0"), hi=Decimal("50")):
    val, src = t
    if not src:
        raise RuleError(f"term {name} has no source: HELD")
    d = D(val)
    if d is None or d <= lo:
        raise RuleError(f"term {name} = {val}: missing or <= 0 (held is never 0)")
    if d > hi:
        raise RuleError(f"term {name} = {val}: unit slip refused (mm or cm read as m)")
    return d


def reveal_area(thickness, height, width):
    """door / opening reveal (jambs + head): 2 x t x h + t x w; terms are (value_m, source)."""
    with ctx40():
        t = _term("thickness", thickness, hi=Decimal("1"))
        h = _term("height", height, hi=Decimal("10"))
        w = _term("width", width, hi=Decimal("20"))
        return q(2 * t * h + t * w)


def face_net(face_id, length, height, openings=()):
    """net face m2 = length x height - each opening on THIS face (w x h). openings: dicts {id, face, width, height,
    exists} with (value, source) terms; an opening that is not physically on this face, or exceeds it, is refused."""
    with ctx40():
        L = _term("length", length)
        H = _term("height", height, hi=Decimal("30"))
        gross = L * H
        ded, used = Decimal(0), Decimal(0)
        for o in openings:
            if o.get("face") != face_id:
                raise RuleError(f"opening {o.get('id')} is on face {o.get('face')}, not {face_id}: never deducted here")
            if not o.get("exists"):
                raise RuleError(f"opening {o.get('id')}: not physically built on this face (Q-73 deducts only actual "
                                "openings)")
            w = _term(f"{o['id']} width", o["width"])
            h = _term(f"{o['id']} height", o["height"], hi=Decimal("30"))
            if h > H:
                raise RuleError(f"opening {o['id']} height {h} > face height {H}: data error, refused")
            used += w
            if used > L:
                raise RuleError(f"openings on {face_id} are wider than the face ({used} > {L}): refused")
            ded += w * h
        net = gross - ded
        if net <= 0:
            raise RuleError(f"face {face_id}: net {net} <= 0 (a face is held, never 0)")
        return {"face": face_id, "gross": S(q(gross)), "deducted": S(q(ded)), "net": S(q(net))}


def shaft_face(face_id, length, storey_intervals, top_height, landing_bands=()):
    """Q-72: a stair-shaft wall measured continuously: length x (sum of the storey intervals below the top storey +
    the exposed height of the top storey); landing-slab edge bands (length, depth) deducted separately."""
    with ctx40():
        L = _term("length", length)
        hs = [_term(f"interval {i}", t, hi=Decimal("10")) for i, t in enumerate(storey_intervals)]
        top = _term("top exposed height", top_height, hi=Decimal("10"))
        gross = L * (sum(hs, Decimal(0)) + top)
        bands = Decimal(0)
        for i, (bl, bd) in enumerate(landing_bands):
            bl_, bd_ = _term(f"band {i} length", bl), _term(f"band {i} depth", bd, hi=Decimal("1"))
            if bl_ > L:
                raise RuleError(f"landing band {i} longer than the face: refused")
            bands += bl_ * bd_
        return {"face": face_id, "gross": S(q(gross)), "landing_bands": S(q(bands)), "net": S(q(gross - bands))}


# ------------------------------------------------------------------ R-T676-3

def coat_per_m2(layer, thickness_m):
    """(cement bags / m2, sand m3 / m2) of one coat, Q-79 mix + Q-53 C conversion."""
    if layer not in MIX:
        raise RuleError(f"layer {layer}: no owner mix")
    t = D(thickness_m)
    if t is None:
        raise RuleError(f"layer {layer}: thickness not given: HELD")
    if not (Decimal(0) < t <= Decimal("0.05")):
        raise RuleError(f"layer {layer}: thickness {t} m refused (mm / cm read as m, or 0)")
    c, s = MIX[layer]
    with ctx40():
        dry = t * DRY_FACTOR
        cement_m3 = dry * c / (c + s)
        sand_m3 = dry * s / (c + s)
        return cement_m3 * CEMENT_KG_M3 / BAG_KG, sand_m3


def coat_materials(area_low, area_high, layer, thickness_m, thickness_kind="EXACT"):
    """material bound of one coat on a HELD area bound; never 0. thickness_kind MINIMUM -> AT_LEAST."""
    if area_low is None or area_high is None:
        return {"status": "HELD", "why": "host area blank (HELD by name)", "cement_bags": None, "sand_m3": None,
                "water": "HELD (no water : cement ratio printed or owner-given)"}
    if thickness_m is None:
        return {"status": "HELD", "why": f"{layer}: thickness not given by the project, the owner or the rules",
                "cement_bags": None, "sand_m3": None, "water": "HELD (no water : cement ratio printed or owner-given)"}
    lo, hi = D(area_low), D(area_high)
    if hi <= 0 or lo > hi:
        raise RuleError(f"area bound {lo} .. {hi} refused")
    cb, sm = coat_per_m2(layer, thickness_m)
    with ctx40():
        r = {"status": "AT_LEAST" if thickness_kind == "MINIMUM" else "HELD_BOUND",
             "cement_bags": [S(q(lo * cb)), S(q(hi * cb))], "sand_m3": [S(q(lo * sm)), S(q(hi * sm))],
             "per_m2": {"cement_bags": S(q(cb)), "sand_m3": S(q(sm))},
             "water": "HELD (no water : cement ratio printed or owner-given)"}
    return r
