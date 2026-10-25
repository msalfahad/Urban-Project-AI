"""T-299 PART F: footing mesh populations printed as a rate ("n ø d/m"), read only, research only.

Builds on T-171 (research/agents_t171/t171_bar_population.py: notation parser and the max-spacing count) without
repeating it. Pure, stdlib only, NOT wired into any method; no engine quantity, candidate line or V2.9 cell changes.
It holds NO project data: a project's schedule rows are read from a JSON file in the private folder (--input).

What PART F adds to T-171 (owner 2026-10-25 13:16 F1 - F8, Checker emphasis C1 - C5, owner Q-71 footing answer 12:36):
  * COVER_RULE: a printed cover note is read with its WORDING (MINIMUM / EXACT) and its SCOPE (which faces). A cover
    governs a population's count and straight run only through the faces the bars are spread / run towards (the SIDE
    faces); the bottom / top cover moves the bar level only (and leg lengths). cover_effect() says which.
  * Clear cover is kept apart from the bar centre offset: first centre = cover + d_enclosing + d / 2 (F3).
  * Count readings kept side by side, never merged (F7, Q-71 points 2 / 8 / 9): MAX_SPACING (1/n is the largest
    centre-to-centre spacing, an edge bar at each side: ceil(L_eff / s) + 1) and DENSITY_IN_ZONE (n bars per metre of
    the zone inside the covers: ceil(n x (side - 2 cover))). A count is a whole number of physical bars; a fractional
    "count" is refused (F1). N = n x L + 1 and the beam 7.5 cm first-link offset are refused for footings (Q-71 7 / 8).
  * Developed length only from a cited end detail: STRAIGHT_DRAWN (a drawn straight bar between drawn limits), else
    HELD with the detail named; no automatic "- 2 x d_enclosing" (F4).
  * Count, diameter, developed length and weight carry SEPARATE statuses; a confirmed count never makes a confirmed
    weight (F5). An audit scenario range is never VERIFIED and never summed into a measured total (F6).
Statuses (WORKFLOW_CONTROLS s.5 vocabulary; VERIFIED is the Checker's word, never written here):
  PRINTED (read from the drawing), INVARIANT_AT_MIN_COVER (every defensible reading gives one value at the printed
  minimum cover: a Checker VERIFIED candidate), HELD (readings differ or an input is not printed), AUDIT_SCENARIO.

Usage: python3 -I t299_part_f.py --input <private json> [--csv <private csv>] [--json <summary json>]
"""
from __future__ import annotations

import argparse
import csv
import importlib.util
import json
import math
import os
import sys
from fractions import Fraction

_HERE = os.path.dirname(os.path.abspath(__file__))
_T171 = os.path.join(_HERE, "..", "agents_t171", "t171_bar_population.py")
_spec = importlib.util.spec_from_file_location("t171_bar_population_for_t299", _T171)
T171 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(T171)

UNIT_MM = T171.UNIT_MM
ENCLOSING_SCENARIO_MM = (0, 8, 10, 12, 14, 16)  # scenario envelope only (T-171): never a bound, never a value
FORBIDDEN_FOOTING_READINGS = {"N_TIMES_L_PLUS_1": "owner Q-71 (12:36) point 8: not universal",
                              "BEAM_FIRST_LINK_OFFSET_75": "owner Q-71 (12:36) point 7: beam offset, not footings"}


class RefusedError(ValueError):
    """A reading, total or status the PART F rules refuse."""


# ---------------------------------------------------------------- cover rule (F2 / F3, C1 / C2)
def cover_rule(wording, value_mm, faces_in_scope):
    """A printed cover note: wording MINIMUM ('not less than') or EXACT; faces_in_scope e.g. {'SIDE', 'TOP'}."""
    if wording not in ("MINIMUM", "EXACT"):
        raise RefusedError("cover wording must be MINIMUM or EXACT, got %r" % (wording,))
    if value_mm is None:
        raise RefusedError("cover value not printed: the population is HELD, never a default")
    return {"wording": wording, "value_mm": Fraction(value_mm), "faces": frozenset(faces_in_scope)}


def cover_effect(kind, face):
    """What a cover on one face changes for a footing mesh population (bars spread across a side, run along the
    other): SIDE faces -> the straight run of every bar and, for a RATE / SPACING population, the count; a printed
    COUNT is never re-counted (length only); BOTTOM / TOP faces -> the bar level (leg lengths) only."""
    if face == "SIDE":
        return {"count": kind in ("RATE", "SPACING"), "straight_run": True, "bar_level": False}
    if face in ("BOTTOM", "TOP"):
        return {"count": False, "straight_run": False, "bar_level": True}
    raise RefusedError("unknown face %r" % (face,))


def first_centre_offset_mm(cover_mm, d_mm, d_enclosing_mm):
    """Distance from the concrete face to the centre of the edge bar: clear cover + enclosing bar + half the bar."""
    if cover_mm is None or d_enclosing_mm is None:
        return None
    return Fraction(cover_mm) + Fraction(d_enclosing_mm) + Fraction(d_mm, 2)


# ---------------------------------------------------------------- counts (F1 / F7)
def _whole(n):
    if n is None:
        return None
    if isinstance(n, Fraction) and n.denominator != 1 or isinstance(n, float) and not float(n).is_integer():
        raise RefusedError("a fractional count is not a physical count: %r" % (n,))
    return int(n)


def count_max_spacing(spread_mm, cover_mm, d_mm, spacing_mm, d_enclosing_mm):
    le = T171.l_eff_mm(spread_mm, cover_mm, d_mm, d_enclosing_mm)
    return _whole(T171.count_max_spacing(le, spacing_mm))


def count_density_in_zone(spread_mm, cover_mm, rate_per_m):
    """n bars per metre of the zone inside the covers, rounded up to whole bars (Q-71 reading A)."""
    if cover_mm is None or rate_per_m is None:
        return None
    zone = Fraction(spread_mm) - 2 * Fraction(cover_mm)
    if zone <= 0:
        return None
    return _whole(math.ceil(Fraction(rate_per_m) * zone / 1000))


def refuse_reading(name):
    if name in FORBIDDEN_FOOTING_READINGS:
        raise RefusedError("%s refused for footing mesh: %s" % (name, FORBIDDEN_FOOTING_READINGS[name]))


def bar_positions_mm(spread_mm, cover_mm, d_mm, n, d_enclosing_mm):
    """Centres of n bars from one face, edge bars at the cover inside the enclosing bar, equal spacing (exact)."""
    n = _whole(n)
    a = first_centre_offset_mm(cover_mm, d_mm, d_enclosing_mm)
    if a is None or n is None or n < 2:
        return None
    le = Fraction(spread_mm) - 2 * a
    return [a + i * le / (n - 1) for i in range(n)]


# ---------------------------------------------------------------- one population (F1 - F6)
def population(mark, layer, comp, spread_mm, bar_mm, callout, cover, end_detail, enclosure,
               enclosing_scenario=ENCLOSING_SCENARIO_MM):
    """end_detail: STRAIGHT_DRAWN | NOT_DRAWN | CAGE_LEGS_UNDIMENSIONED (+ a citation in enclosure / detail text).
    enclosure: None when the drawing shows nothing between the bar and the face for this footing (d_enclosing 0),
    else a text naming why an enclosing bar of unprinted diameter may sit there (scenario envelope used)."""
    p = T171.parse(callout)
    row = {"mark": mark, "layer": layer, "component": comp, "printed": callout, "kind": p["kind"],
           "spread_mm": float(spread_mm), "bar_side_mm": float(bar_mm)}
    if p["kind"] in ("UNKNOWN",):
        row.update(diameter_mm=None, diameter_status="HELD", count_status="HELD", count_low=None, count_high=None,
                   length_status="HELD", weight_status="HELD", held_reason="unreadable cell: " + p["why"])
        return row
    d = p["d"]
    row.update(diameter_mm=d, diameter_status="PRINTED")
    c = cover["value_mm"] if cover and "SIDE" in cover["faces"] else None
    if c is None:
        row.update(count_status="HELD", count_low=None, count_high=None, length_status="HELD",
                   weight_status="HELD", held_reason="no printed cover on the side faces")
        return row
    encl = (0,) if enclosure is None else tuple(enclosing_scenario)
    reasons = []
    if p["kind"] == "COUNT":
        lo = hi = p["n"]
        row.update(count_status="PRINTED", readings={"PRINTED": p["n"]})
    else:
        ms = {e: count_max_spacing(spread_mm, c, d, p["spacing_mm"], e) for e in encl}
        dz = count_density_in_zone(spread_mm, c, p["rate"])
        readings = {"MAX_SPACING_e%d" % e: v for e, v in ms.items()}
        readings["DENSITY_IN_ZONE"] = dz
        vals = [v for v in readings.values() if v is not None]
        if len(vals) != len(readings):
            row.update(count_status="HELD", count_low=None, count_high=None, readings=readings,
                       length_status="HELD", weight_status="HELD", held_reason="no room for bars")
            return row
        lo, hi = min(vals), max(vals)
        if len(set(ms.values())) > 1:
            reasons.append("count depends on the unprinted enclosing-bar diameter (%s)" % enclosure)
        if dz != ms[encl[0]]:
            reasons.append("count depends on the meaning of 'n ø d/m' (max spacing %d vs density in zone %d): "
                           "not stated in the drawing set, designer RFI" % (ms[encl[0]], dz))
        if cover["wording"] == "MINIMUM":
            reasons.append("cover printed as a MINIMUM: counts are at the minimum cover (project basis); a larger "
                           "actual cover can only lower them, no upper cover printed")
        row.update(readings=readings,
                   count_status="INVARIANT_AT_MIN_COVER" if lo == hi else "HELD",
                   max_spacing_positions_e0=[float(x) for x in
                                             (bar_positions_mm(spread_mm, c, d, ms[encl[0]], encl[0]) or [])])
        row["achieved_spacing_mm_e0"] = (float((Fraction(spread_mm) - 2 * first_centre_offset_mm(c, d, encl[0]))
                                               / (ms[encl[0]] - 1)) if ms[encl[0]] > 1 else None)
        row["printed_max_spacing_mm"] = float(p["spacing_mm"])
    row.update(count_low=lo, count_high=hi)
    core_hi = Fraction(bar_mm) - 2 * c
    core_lo = Fraction(bar_mm) - 2 * c - 2 * max(encl)
    row.update(straight_core_scenario_m=(float(core_lo / 1000), float(core_hi / 1000)))
    if end_detail == "STRAIGHT_DRAWN" and enclosure is None and cover["wording"] == "EXACT":
        row["length_status"] = "INVARIANT_AT_MIN_COVER"
        row["developed_length_m"] = float(core_hi / 1000)
    else:
        row["length_status"] = "HELD"
        row["developed_length_m"] = None
        if end_detail != "STRAIGHT_DRAWN":
            reasons.append("bar ends / legs not drawn or not dimensioned (%s)" % end_detail)
        if enclosure is not None:
            reasons.append("straight run stops inside an enclosing bar of unprinted diameter")
        if cover["wording"] == "MINIMUM":
            reasons.append("side - 2 x minimum cover is the LONGEST straight run the note allows, not a length")
    kgm = T171.kg_per_m_d2_162(d)
    row["kg_audit_scenario"] = (float(lo * core_lo / 1000 * kgm), float(hi * core_hi / 1000 * kgm))
    row["weight_status"] = ("INVARIANT_AT_MIN_COVER" if row["count_status"] in ("PRINTED", "INVARIANT_AT_MIN_COVER")
                            and row["length_status"] == "INVARIANT_AT_MIN_COVER" else "HELD")
    row["held_reason"] = "; ".join(reasons) if reasons else ""
    return row


def footing_populations(f, cover, unit="cm"):
    k = UNIT_MM[unit]
    L, W = Fraction(f["L"]) * k, Fraction(f["W"]) * k
    encl = f.get("enclosure")
    out = []
    for layer in ("BOT", "TOP"):
        if layer not in f["layers"]:
            continue
        sc, lc = f["layers"][layer]
        end = f.get("end_detail", {}).get(layer, "NOT_DRAWN")
        for comp, callout, spread, bar in (("SHORT", sc, L, W), ("LONG", lc, W, L)):
            out.append(population(f["mark"], layer, comp, spread, bar, callout, cover, end,
                                  None if encl in (None, "NONE") else encl))
    return out


# ---------------------------------------------------------------- totals (F6, C4)
def measured_total_kg(rows):
    """A measured total exists only when every row's weight is INVARIANT_AT_MIN_COVER; else None (HELD), never 0."""
    if not rows:
        return None
    for r in rows:
        if r.get("weight_status") == "AUDIT_SCENARIO" or "kg_audit_scenario_only" in r:
            raise RefusedError("an audit scenario is never summed into a measured total")
        if r.get("weight_status") != "INVARIANT_AT_MIN_COVER":
            return None
        if r.get("kg") is None:
            raise RefusedError("a row without kg in a measured total (HELD as 0)")
    return sum(Fraction(str(r["kg"])) for r in rows)


def scenario_envelope_kg(rows):
    """Audit scenario only: (low, high) over the rows, unrounded; labelled, never a quantity."""
    lo = sum(Fraction(r["kg_audit_scenario"][0]) for r in rows if r.get("kg_audit_scenario"))
    hi = sum(Fraction(r["kg_audit_scenario"][1]) for r in rows if r.get("kg_audit_scenario"))
    return {"status": "AUDIT_SCENARIO", "low_kg": float(lo), "high_kg": float(hi),
            "low_t": float(lo / 1000), "high_t": float(hi / 1000)}


def check_status_claim(row, claimed):
    """A claim VERIFIED / DRAWING-CONFIRMED on a weight whose count or length is HELD is refused (F5, C4)."""
    if claimed in ("VERIFIED", "DRAWING-CONFIRMED", "DRAWING_CONFIRMED") and row.get("weight_status") != \
            "INVARIANT_AT_MIN_COVER":
        raise RefusedError("weight of %s %s %s cannot be %s: count %s, length %s" % (
            row.get("mark"), row.get("layer"), row.get("component"), claimed, row.get("count_status"),
            row.get("length_status")))
    return True


# ---------------------------------------------------------------- printed-count straight-run trace (C3)
def printed_count_straight_trace(rows, cover_mm, enclosing_scenario=ENCLOSING_SCENARIO_MM):
    """rows: [{"mark", "occurrences", "L", "W", "short": (n, d), "long": (n, d), "boxed_printed": bool}] in mm.
    Returns kg at side - 2 cover per enclosing scenario (straight bars stopping inside a boxed leg where printed)."""
    out = {}
    for e in enclosing_scenario:
        t = Fraction(0)
        for r in rows:
            ee = e if r["boxed_printed"] else 0
            ns, ds = r["short"]
            nl, dl = r["long"]
            t += r["occurrences"] * (ns * (Fraction(r["W"]) - 2 * Fraction(cover_mm) - 2 * ee) / 1000 *
                                     T171.kg_per_m_d2_162(ds) +
                                     nl * (Fraction(r["L"]) - 2 * Fraction(cover_mm) - 2 * ee) / 1000 *
                                     T171.kg_per_m_d2_162(dl))
        out[e] = t
    return out


# ---------------------------------------------------------------- runner
END_DETAIL_BY_ENCLOSURE = {
    # bottom layer: p.13 draws the bottom bars straight between the side legs, on a single-layer footing with a
    # boxed bar; its use for a two-layer footing is not stated -> the bottom end is still HELD (NOT_DRAWN for the
    # two-layer case); FF: p.14 closed cage, legs not dimensioned.
    "NOT_PRINTED_NO_REMARK": {"BOT": "NOT_DRAWN (p.13 is a single-layer detail)", "TOP": "NOT_DRAWN"},
    "CAGE_SYMBOL_NO_SECTION": {"BOT": "NOT_DRAWN (p.9 cage symbol, no section)", "TOP": "NOT_DRAWN (p.9 cage "
                                                                                       "symbol, no section)"},
    "CLOSED_CAGE_P14_LEGS_UNDIMENSIONED": {"BOT": "CAGE_LEGS_UNDIMENSIONED (p.14)",
                                           "TOP": "CAGE_LEGS_UNDIMENSIONED (p.14)"},
}


def run(path, csv_path=None, json_path=None):
    data = json.load(open(path, encoding="utf-8"))
    cover = cover_rule("MINIMUM", data["cover_min_mm"], {"SIDE", "TOP", "BOTTOM"})
    rows = []
    for f in data["footings"]:
        f = dict(f)
        f["end_detail"] = END_DETAIL_BY_ENCLOSURE.get(f.get("enclosure"), {})
        for r in footing_populations(f, cover, data.get("unit", "cm")):
            r["occurrences"] = f.get("occurrences")
            rows.append(r)
    summary = {"populations": len(rows),
               "count_invariant": sum(r["count_status"] == "INVARIANT_AT_MIN_COVER" for r in rows),
               "count_held": sum(r["count_status"] == "HELD" for r in rows),
               "length_held": sum(r["length_status"] == "HELD" for r in rows),
               "weight_held": sum(r["weight_status"] == "HELD" for r in rows),
               "measured_total_kg": None if measured_total_kg(rows) is None else float(measured_total_kg(rows)),
               "audit_scenario": scenario_envelope_kg(rows),
               "rows": [{k: r.get(k) for k in ("mark", "layer", "component", "diameter_mm", "diameter_status",
                                               "count_low", "count_high", "count_status", "readings",
                                               "printed_max_spacing_mm", "achieved_spacing_mm_e0",
                                               "length_status", "weight_status", "kg_audit_scenario",
                                               "held_reason")} for r in rows]}
    if csv_path:
        keys = sorted({k for r in rows for k in r})
        with open(csv_path, "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=keys)
            w.writeheader()
            w.writerows(rows)
    if json_path:
        with open(json_path, "w", encoding="utf-8") as fh:
            json.dump(summary, fh, indent=1, sort_keys=True, default=str)
    return summary


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--csv")
    ap.add_argument("--json")
    a = ap.parse_args()
    s = run(a.input, a.csv, a.json)
    for r in s["rows"]:
        print(r["mark"], r["layer"], r["component"], r["diameter_mm"], r["count_low"], r["count_high"],
              r["count_status"], r["length_status"], r["weight_status"],
              tuple(round(x, 3) for x in r["kg_audit_scenario"]))
    print({k: v for k, v in s.items() if k != "rows"})
    return 0


if __name__ == "__main__":
    sys.exit(main())
