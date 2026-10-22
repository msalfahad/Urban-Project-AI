"""T-171: bar population of a footing mesh printed as a rate ("n ø d/m") or a spacing ("ø d/s cm"), research only.

Pure, stdlib only, NOT wired into any method. It holds NO project data: a project's schedule rows are read from a JSON
file kept in the private folder (--input). The synthetic fixture in tests/t171_bar_population is not any real villa.

Physical model (T-171 investigation, research/agents_t171/T-171_NOTATION_INVESTIGATION.md):
  * "n ø d/m" = bars of diameter d at a centre-to-centre spacing of 1/n m in the direction they are spread across
    (n per metre run). Placing fewer bars than that delivers less steel per metre than printed, so 1/n is the
    LARGEST spacing that complies (a maximum spacing).  "ø d/s cm" is the same with s printed directly.
  * The edge bars sit at the cover (printed note), inside any bar drawn between them and the face (the "boxed bar"
    legs of a typical isolated-footing detail). L_eff = centre-to-centre distance of the two edge bars:
        L_eff = side - 2 x cover - 2 x d_enclosing - d
  * Whole bars at a spacing not exceeding s, with a bar at each end:  N = ceil(L_eff / s) + 1.
    When L_eff / s is a whole number k, N = k + 1 (spacing exactly s). Exact arithmetic (Fraction, mm).
  * Straight core length of a bar = other side - 2 x cover - 2 x d_enclosing (it stops inside the legs).
  * A printed COUNT "n ø d" is never re-counted.
  * Missing cover, an unprinted enclosing-bar diameter (None), an unreadable cell or L_eff <= 0 -> HELD / UNKNOWN,
    the kg is None, never 0.
  * Area check (report only, never changes N): n x full side against N; a positive deficit is listed as a residual.
kg/m is supplied by the caller (the project's unit-mass method; Urban project default R3 is d^2/162).

Usage: python3 -I t171_bar_population.py --input <private json> [--csv <private csv>] [--enclosing 0,8,10,12,14,16]
Input JSON: {"cover_mm": 70, "unit": "cm", "unit_mass": "D2_OVER_162",
             "footings": [{"mark": "X1", "L": 400, "W": 300, "occurrences": 1, "enclosing_d_mm": null,
                           "layers": {"TOP": ["6 ø 14/m", "6 ø 14/m"], "BOT": ["9 ø 14/m", "9 ø 14/m"]}}]}
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import re
import sys
from fractions import Fraction

DIA = r"(?:ø|Ø|φ|Φ|%%c|%%C|T)"
_RATE = re.compile(r"^\s*(\d+)\s*" + DIA + r"\s*(\d+)\s*/\s*m\s*$", re.I)
_COUNT = re.compile(r"^\s*(\d+)\s*" + DIA + r"\s*(\d+)\s*$", re.I)
_SPACE = re.compile(r"^\s*" + DIA + r"\s*(\d+)\s*(?:@|/)\s*(\d+(?:\.\d+)?)\s*(cm|mm)\s*$", re.I)
UNIT_MM = {"m": Fraction(1000), "cm": Fraction(10), "mm": Fraction(1)}


def parse(callout):
    """-> {"kind": RATE | SPACING | COUNT | UNKNOWN, "d": mm, "spacing_mm": Fraction, "rate": Fraction, "n": int}."""
    if callout is None or not str(callout).strip():
        return {"kind": "UNKNOWN", "why": "empty cell"}
    s = str(callout)
    m = _RATE.match(s)
    if m:
        n = int(m.group(1))
        if n <= 0:
            return {"kind": "UNKNOWN", "why": "zero rate"}
        return {"kind": "RATE", "rate": Fraction(n), "d": int(m.group(2)), "spacing_mm": Fraction(1000, n)}
    m = _COUNT.match(s)
    if m:
        return {"kind": "COUNT", "n": int(m.group(1)), "d": int(m.group(2))}
    m = _SPACE.match(s)
    if m:
        sp = Fraction(m.group(2)) * UNIT_MM[m.group(3).lower()]
        if sp <= 0:
            return {"kind": "UNKNOWN", "why": "zero spacing"}
        return {"kind": "SPACING", "rate": Fraction(1000) / sp, "d": int(m.group(1)), "spacing_mm": sp}
    return {"kind": "UNKNOWN", "why": "unreadable: %r" % s}


def l_eff_mm(side_mm, cover_mm, d_mm, enclosing_d_mm):
    """Centre-to-centre distance of the two edge bars; None when the cover or the enclosing bar is not printed."""
    if cover_mm is None or enclosing_d_mm is None:
        return None
    return Fraction(side_mm) - 2 * Fraction(cover_mm) - 2 * Fraction(enclosing_d_mm) - Fraction(d_mm)


def count_max_spacing(leff_mm, spacing_mm):
    """N = ceil(L_eff / s) + 1, exact; None when L_eff is missing or not positive."""
    if leff_mm is None or leff_mm <= 0 or spacing_mm is None or spacing_mm <= 0:
        return None
    q = Fraction(leff_mm) / Fraction(spacing_mm)
    return math.ceil(q) + 1


def kg_per_m_d2_162(d_mm):
    return Fraction(d_mm * d_mm, 162)


def cell(side_spread_mm, side_bar_mm, cover_mm, callout, enclosing_d_mm, kg_per_m=kg_per_m_d2_162):
    """One bar population: bars run along side_bar, spread across side_spread. Returns a dict (floats rounded)."""
    p = parse(callout)
    out = {"printed": callout, "kind": p["kind"]}
    if p["kind"] == "UNKNOWN":
        out.update(status="UNKNOWN", why=p["why"], n=None, kg=None)
        return out
    if cover_mm is None:
        out.update(status="HELD", why="no printed cover", n=None, kg=None)
        return out
    d = p["d"]
    if p["kind"] == "COUNT":
        n = p["n"]
        if enclosing_d_mm is None:
            out.update(status="HELD", why="count printed; bar length waits on the enclosing-bar diameter",
                       n=n, kg=None)
            return out
        length = Fraction(side_bar_mm) - 2 * Fraction(cover_mm) - 2 * Fraction(enclosing_d_mm)
        out.update(status="COUNT_PRINTED", n=n, bar_length_m=float(length / 1000),
                   kg=float(n * length / 1000 * kg_per_m(d)))
        return out
    le = l_eff_mm(side_spread_mm, cover_mm, d, enclosing_d_mm)
    if le is None:
        out.update(status="HELD", why="enclosing-bar diameter not printed", n=None, kg=None)
        return out
    n = count_max_spacing(le, p["spacing_mm"])
    if n is None:
        out.update(status="UNKNOWN", why="no room for bars (L_eff <= 0)", n=None, kg=None)
        return out
    length = Fraction(side_bar_mm) - 2 * Fraction(cover_mm) - 2 * Fraction(enclosing_d_mm)
    achieved = le / (n - 1) if n > 1 else None
    area_need = p["rate"] * Fraction(side_spread_mm) / 1000  # bars for n per metre over the full side
    out.update(status="CALCULATED", d=d, n=n, l_eff_m=float(le / 1000), bar_length_m=float(length / 1000),
               printed_spacing_mm=float(p["spacing_mm"]),
               achieved_spacing_mm=None if achieved is None else float(achieved),
               area_check_bars=float(area_need), area_deficit_bars=float(max(Fraction(0), area_need - n)),
               kg=float(n * length / 1000 * kg_per_m(d)))
    return out


def footing(mark, L, W, cover_mm, layers, enclosing_d_mm, unit="cm", kg_per_m=kg_per_m_d2_162):
    """Short bars run along W and are spread across L; long bars run along L and are spread across W."""
    f = UNIT_MM[unit]
    Lmm, Wmm = Fraction(L) * f, Fraction(W) * f
    rows = []
    for layer, (short_c, long_c) in layers.items():
        for comp, callout, spread, bar in (("SHORT", short_c, Lmm, Wmm), ("LONG", long_c, Wmm, Lmm)):
            r = cell(spread, bar, cover_mm, callout, enclosing_d_mm, kg_per_m)
            r.update(mark=mark, layer=layer, component=comp)
            rows.append(r)
    return rows


def total(rows):
    """Sum of kg; None (never 0) when any row has no kg."""
    if not rows or any(r.get("kg") is None for r in rows):
        return None
    return round(sum(r["kg"] for r in rows), 6)


def threshold_enclosing_mm(side_spread_mm, cover_mm, callout, d_from=0, d_to=40):
    """Smallest whole-mm enclosing diameter at which N drops below its value at 0 mm (None if it never drops)."""
    n0 = cell(side_spread_mm, side_spread_mm, cover_mm, callout, 0)["n"]
    for e in range(d_from, d_to + 1):
        n = cell(side_spread_mm, side_spread_mm, cover_mm, callout, e)["n"]
        if n is not None and n0 is not None and n < n0:
            return e
    return None


def run(path, csv_path=None, enclosing_list=(0, 8, 10, 12, 14, 16)):
    data = json.load(open(path, encoding="utf-8"))
    cover, unit = data.get("cover_mm"), data.get("unit", "cm")
    allrows = []
    for e in enclosing_list:
        grand = 0.0
        for f in data["footings"]:
            rows = footing(f["mark"], f["L"], f["W"], cover, {k: tuple(v) for k, v in f["layers"].items()}, e, unit)
            t = total(rows)
            occ = f.get("occurrences")
            grand = None if (grand is None or t is None or occ is None) else grand + t * occ
            for r in rows:
                r["enclosing_d_mm"] = e
                print(e, r["mark"], r["layer"], r["component"], r["printed"], r.get("n"), r.get("l_eff_m"),
                      r.get("achieved_spacing_mm"), r.get("printed_spacing_mm"), r.get("area_deficit_bars"),
                      None if r.get("kg") is None else round(r["kg"], 2), r["status"])
            allrows += rows
            print("TOTAL", e, f["mark"], t)
        print("ALL", e, None if grand is None else round(grand, 2))
    f = UNIT_MM[unit]
    for ft in data["footings"]:
        for layer, (sc, lc) in ft["layers"].items():
            for comp, c, spread in (("SHORT", sc, Fraction(ft["L"]) * f), ("LONG", lc, Fraction(ft["W"]) * f)):
                print("THRESHOLD", ft["mark"], layer, comp, threshold_enclosing_mm(spread, cover, c))
    if csv_path:
        keys = sorted({k for r in allrows for k in r})
        with open(csv_path, "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=keys)
            w.writeheader()
            w.writerows(allrows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--csv")
    ap.add_argument("--enclosing", default="0,8,10,12,14,16")
    a = ap.parse_args()
    run(a.input, a.csv, tuple(int(x) for x in a.enclosing.split(",")))
    return 0


if __name__ == "__main__":
    sys.exit(main())
