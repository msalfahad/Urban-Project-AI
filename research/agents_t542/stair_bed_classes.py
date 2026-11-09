"""T-542 STAIR_BED_CLASSES_V1 (research, UNWIRED; every villa): every stair marble surface classed to the bed rule
that governs it, checked once against the floor-bed family, and turned into installed mortar, theoretical cement and
sand, and the procurement own account (FINISH_MATERIALS_TABLE_V7, R-T528-1), per component.

Physical element (ERS s.2.1). Under each marble piece of a stair lies a cement-sand layer:
  TREAD    horizontal stone on a bed over the concrete going;
  RISER    a vertical plate set against the concrete riser face: the mortar behind it is a vertical BACKING, not a
           bed under load; it is in the stair bed scope only when a named source puts it there;
  LANDING  a flat stair surface; what it is depends on its level and flights (T-493 R-T493-1):
             STAIR_LANDING     between storeys, reached by one flight and left by another: only stair (UP-STAIR-005);
             STAIR_ARRIVAL     at a storey floor at a flight end, made stair marble by a named owner answer;
             FLOOR_OR_LANDING  at a floor, own zone, no material source: floor or landing undecided (R-T490-1);
             FLOOR             inside a room floor line: the room's floor finish (OWNER_RULE_STAIRS A6).
The bed is physically ONE layer per surface: a surface whose bed is already produced by the floor-bed family (a
FIN.FLOOR.BED.* line on its element) is never also a stair bed, and a stair landing lying inside a floor host is
measured once only if that host deducts it.

Rules (R-T542-1 .. R-T542-3, every villa; no villa constant in this module):
  R-T542-1 BED CLASS. TREAD -> STAIR_BED (kind STAIR_FLIGHT). RISER -> STAIR_BED only with a named riser-bed source,
           else HELD RISER_BED_SOURCE_NOT_GIVEN (the riser marble stays measured). STAIR_LANDING -> STAIR_BED (kind
           STAIR_LANDING) only with a named landing-bed source, else HELD LANDING_BED_SOURCE_NOT_GIVEN (the floor 1:4
           bed is never borrowed). STAIR_ARRIVAL -> as STAIR_LANDING, and only when its marble material source is
           named, else HELD ARRIVAL_MATERIAL_NOT_GIVEN. FLOOR_OR_LANDING and FLOOR -> FLOOR_BED_FAMILY (not a stair
           bed; the floor host decides; reported beside, never in a stair sum). A HELD part is never 0.
  R-T542-2 ONE BED PER SURFACE. (a) a part whose element id carries a floor-bed line goes to FLOOR_BED_FAMILY (counted
           there, named here; a stair class on it is refused as a double count unless the part is FLOOR /
           FLOOR_OR_LANDING); (b) a part declared inside a floor host must name that host's deduction (amount and
           source), or lie over a void / outside every host; an undeducted host refuses the part (DOUBLE_COUNT);
           (c) a surface keyed twice is refused.
  R-T542-3 MATERIALS. Each STAIR_BED part -> one V7 element (its own kind): installed mortar = area x the V1 owner bed
           (Q-45: stairs 0.03 m), theoretical cement / sand = installed x UP-STAIR-017 (Q-53 C, recomputed by V7),
           procurement = installed + the Q-45 5 % loss as its own account (V6 / V7), the UP-STAIR-017 purchasing
           allowance a separate layer. Sums per class and per scope list every HELD part and print AT_LEAST.
"""

from __future__ import annotations

import math

from engine.source import finish_materials_table_v7 as V7

TREAD, RISER, LANDING = "TREAD", "RISER", "LANDING"
STAIR_LANDING, STAIR_ARRIVAL = "STAIR_LANDING", "STAIR_ARRIVAL"
FLOOR_OR_LANDING, FLOOR = "FLOOR_OR_LANDING", "FLOOR"
LANDING_CLASSES = (STAIR_LANDING, STAIR_ARRIVAL, FLOOR_OR_LANDING, FLOOR)
STAIR_BED, FLOOR_BED_FAMILY, HELD = "STAIR_BED", "FLOOR_BED_FAMILY", "HELD"
TREAD_RULE = "Q-45 B stairs 0.03 m 1:3 (V1 OWNER_VALUES bed_m / mix STAIR_FLIGHT) + UP-STAIR-017@1.0.0 (Q-53 C)"
LANDING_RULE = "Q-45 B stairs 0.03 m 1:3 (V1 OWNER_VALUES bed_m / mix STAIR_LANDING) + UP-STAIR-017@1.0.0 (Q-53 C)"
KEYS = ("mortar_m3_low", "cement_bags_low", "sand_m3_low", "bed_loss_m3_low", "bed_procurement_m3_low",
        "cement_bags_procurement_low", "sand_m3_procurement_low")


class BedClassError(ValueError):
    pass


def _r(x, n=6):
    return None if x is None else round(x + 0.0, n)


def _area(name, v):
    if isinstance(v, bool) or not isinstance(v, (int, float)) or math.isnan(v) or v <= 0:
        raise BedClassError(f"{name}: area must be a number > 0, got {v!r}")
    return float(v)


def classify(p, sources, floor_bed_elements):
    """R-T542-1 / R-T542-2 for one marble part. p: key, surface, m2 (None when the marble part is HELD), status,
    optional element_id, landing_class (LANDING only), arrival_source (STAIR_ARRIVAL), floor_host (None, or
    {'host', 'deducted_m2' or 'void' or 'outside', 'source'}), beside, reason. sources: {'riser': str or None,
    'landing': str or None}. floor_bed_elements: {element_id: floor-bed line id}."""
    key, s = p["key"], p["surface"]
    out = {"key": key, "surface": s, "element_id": p.get("element_id"), "marble_m2": p.get("m2"),
           "marble_status": p.get("status"), "landing_class": p.get("landing_class"), "bed_class": None,
           "kind": None, "bed_m2": None, "rule": None, "status_label": None, "reason": None,
           "beside_m2": p.get("beside"), "floor_bed_line": None, "floor_host": p.get("floor_host")}
    if s not in (TREAD, RISER, LANDING):
        raise BedClassError(f"{key}: unknown surface {s!r}")
    lc = p.get("landing_class")
    if s == LANDING and lc not in LANDING_CLASSES:
        raise BedClassError(f"{key}: landing class {lc!r} not one of {LANDING_CLASSES}")
    if s != LANDING and lc:
        raise BedClassError(f"{key}: a {s} carries no landing class")
    el = p.get("element_id")
    fb = floor_bed_elements.get(el) if el else None
    # R-T542-2 (a): the floor-bed family already beds this element
    if fb:
        if s == LANDING and lc in (FLOOR_OR_LANDING, FLOOR):
            out.update(bed_class=FLOOR_BED_FAMILY, floor_bed_line=fb, beside_m2=p.get("m2") or p.get("beside"),
                       reason=f"bed produced by the floor-bed family on {el} ({fb}); never a stair bed as well")
            return out
        raise BedClassError(f"DOUBLE_COUNT: {key} {s} ({lc or s}) element {el} already bedded by floor-bed line {fb}")
    if s == LANDING and lc in (FLOOR_OR_LANDING, FLOOR):
        out.update(bed_class=FLOOR_BED_FAMILY, beside_m2=p.get("m2") or p.get("beside"),
                   reason=f"{lc}: the floor host decides the bed (R-T490-1 / A6); no floor-bed line named here")
        return out
    # R-T542-2 (b): a stair surface inside a floor host must be deducted from it, lie over a void or outside
    fh = p.get("floor_host")
    if fh is not None:
        if not fh.get("source"):
            raise BedClassError(f"{key}: floor host {fh.get('host')!r} given without its source")
        if fh.get("void") or fh.get("outside"):
            pass
        elif fh.get("deducted_m2") is None:
            raise BedClassError(f"DOUBLE_COUNT: {key} lies inside floor host {fh.get('host')!r} with no deduction")
        elif p.get("m2") is not None and abs(fh["deducted_m2"] - p["m2"]) > 1e-3:
            raise BedClassError(f"{key}: host deduction {fh['deducted_m2']} differs from the part {p['m2']} by more "
                                "than 1e-3 m2 (a partial deduction is a double count)")
    if p.get("status") == HELD or p.get("m2") is None:
        out.update(bed_class=HELD, reason=p.get("reason") or "MARBLE_PART_HELD", beside_m2=p.get("beside"))
        return out
    a = _area(f"{key} {s}", p["m2"])
    if s == TREAD:
        out.update(bed_class=STAIR_BED, kind=V7.STAIR_FLIGHT, bed_m2=a, rule=TREAD_RULE,
                   status_label="OWNER (Q-45 B, PROVISIONAL) + CALCULATED PROVISIONAL (Q-53 C)")
    elif s == RISER:
        if not sources.get("riser"):
            out.update(bed_class=HELD, beside_m2=a, reason="RISER_BED_SOURCE_NOT_GIVEN (riser marble measured; the "
                                                          "backing is not a stair bed without a named source)")
        else:
            out.update(bed_class=STAIR_BED, kind=V7.STAIR_FLIGHT, bed_m2=a, rule=TREAD_RULE + "; riser scope: "
                       + sources["riser"], status_label="ASSUMED - OWNER-APPROVED (riser in the stair bed scope)")
    else:
        if lc == STAIR_ARRIVAL and not p.get("arrival_source"):
            out.update(bed_class=HELD, beside_m2=a, reason="ARRIVAL_MATERIAL_NOT_GIVEN (an arrival is stair marble "
                                                          "only by a named owner answer; floor or landing undecided)")
        elif not sources.get("landing"):
            out.update(bed_class=HELD, beside_m2=a, reason="LANDING_BED_SOURCE_NOT_GIVEN (the floor 1:4 bed is never "
                                                          "borrowed for a stair landing)")
        else:
            src = sources["landing"] + ("" if lc == STAIR_LANDING else f"; arrival marble: {p['arrival_source']}")
            out.update(bed_class=STAIR_BED, kind=V7.STAIR_LANDING, bed_m2=a, rule=LANDING_RULE + "; landing scope: "
                       + src, status_label="ASSUMED - OWNER-APPROVED (landing in the stair bed scope)")
    return out


def classify_all(parts, sources, floor_bed_elements):
    seen = set()
    rows = []
    for p in parts:
        kk = (p["key"], p["surface"])
        if kk in seen:
            raise BedClassError(f"surface counted twice: {kk}")
        seen.add(kk)
        rows.append(classify(p, sources, floor_bed_elements))
    return rows


def materials(rows):
    """R-T542-3: V7 on every STAIR_BED row (one element each); returns rows with their material keys + sums."""
    bed = [r for r in rows if r["bed_class"] == STAIR_BED]
    els = [{"id": f"{r['key']}:{r['surface']}", "floor": "STAIR", "kind": V7.STAIR_LANDING, "area_m2": r["bed_m2"]}
           for r in bed]
    # V1 gives STAIR_FLIGHT and STAIR_LANDING the same bed and mix; an area-given part uses the landing row form
    ov = V7.OWNER_VALUES
    if ov["bed_m"][V7.STAIR_FLIGHT] != ov["bed_m"][V7.STAIR_LANDING] or \
            ov["mix"][V7.STAIR_FLIGHT] != ov["mix"][V7.STAIR_LANDING]:
        raise BedClassError("V1 stair flight and landing beds differ: rows must be built per kind")
    t = V7.table(els) if els else {"rows": []}
    by_id = {r["id"]: r for r in t["rows"]}
    out = []
    for r in rows:
        q = dict(r)
        if r["bed_class"] == STAIR_BED:
            v = by_id[f"{r['key']}:{r['surface']}"]
            if v.get("cement_sand_status") != V7.STATUS_Q53 or v.get("mortar_m3_low") is None:
                raise BedClassError(f"{r['key']} {r['surface']}: V7 did not produce the stair bed "
                                    f"({v.get('cement_sand_reason') or v.get('mortar_reason')})")
            q.update({k: _r(v[k]) for k in KEYS})
            q["bed_m"] = v["bed_low_m"]
            q["mix"] = v["mix"]
            q["allowance_cement_bags"] = _r(v["bed_purchasing_allowance"]["cement_bags_low"])
            q["allowance_sand_m3"] = _r(v["bed_purchasing_allowance"]["sand_m3_low"])
        out.append(q)
    return out


def summarise(rows, select=None, label=""):
    """sums of the STAIR_BED rows (optionally filtered); HELD rows listed, FLOOR_BED_FAMILY rows listed beside."""
    sel = [r for r in rows if select is None or select(r)]
    det = [r for r in sel if r["bed_class"] == STAIR_BED]
    held = [{"key": r["key"], "surface": r["surface"], "reason": r["reason"], "beside_m2": r["beside_m2"]}
            for r in sel if r["bed_class"] == HELD]
    floor = [{"key": r["key"], "surface": r["surface"], "floor_bed_line": r["floor_bed_line"],
              "beside_m2": r["beside_m2"]} for r in sel if r["bed_class"] == FLOOR_BED_FAMILY]
    s = {"label": label, "area_m2": _r(sum(r["bed_m2"] for r in det)), "parts": len(det)}
    for k in KEYS + ("allowance_cement_bags", "allowance_sand_m3"):
        s[k] = _r(sum(r[k] for r in det))
    s["held"] = held
    s["floor_bed_family_beside"] = floor
    s["state"] = "PARTIAL" if held else "COMPLETE"
    s["print"] = (f"AT_LEAST {s['area_m2']:.4f} m2 + HELD ({len(held)} parts)" if held else f"{s['area_m2']:.4f} m2")
    if floor:
        s["print"] += f"; {len(floor)} floor-bed family part(s) beside"
    return s
