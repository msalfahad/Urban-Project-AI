"""T-155: footing bars printed per metre or at a spacing, counted by hand under each reading (research only, not wired).

Generic tool. It holds NO project data: a project's schedule rows are read from a JSON file kept outside the
repository (the private folder), passed with --input. The synthetic fixture below (--check) is not any real villa.

Notations it reads (cell text as printed):
  "n ø d"            count                 -> the count, never re-counted
  "n ø d/m"          rate, n bars per metre -> three readings, none chosen here
  "ø d @ s cm", "ø d/s cm"  spacing (unit must be printed) -> rate = 1/s, same three readings
Readings of a rate r spread over a footing side S with cover c:
  R1  ceil(r x (S - 2c))        bars inside the covers, rounded up          (Q-71 option A)
  R2  R1 + 1                    spaces inside the covers + 1 (edge bars)    (Q-71 option B)
  R3  r x S, kept fractional    rate x full side                            (Q-71 option C)
Short bars: length W - 2c, spread along L; long bars: length L - 2c, spread along W.
kg = count x length x d^2/162 (Urban rebar rule). Missing cover or unreadable cell -> HELD / UNKNOWN, never 0.

Usage: python3 -I t155_footing_notation.py --check
       python3 -I t155_footing_notation.py --input <private json> [--csv <private csv>]
Input JSON: {"cover_m": 0.07, "unit": "cm", "footings": [{"mark": "X1", "L": 400, "W": 300, "occurrences": 1,
             "layers": {"TOP": ["6 ø 14/m", "6 ø 14/m"], "BOT": ["9 ø 14/m", "9 ø 14/m"]}}],
             "count_rows": [{"mark": "X2", "L": 190, "W": 170, "short": "13 ø 12", "long": "13 ø 12"}]}
"""
import argparse, csv, json, math, re, sys

DIA = r"(?:ø|%%c|Ø|T)"
_RATE = re.compile(r"^\s*(\d+)\s*" + DIA + r"\s*(\d+)\s*/\s*m\s*$", re.I)
_COUNT = re.compile(r"^\s*(\d+)\s*" + DIA + r"\s*(\d+)\s*$", re.I)
_SPACE = re.compile(r"^\s*" + DIA + r"\s*(\d+)\s*(?:@|/)\s*(\d+(?:\.\d+)?)\s*(cm|mm|m)\s*$", re.I)


def kg_per_m(d_mm):
    return d_mm * d_mm / 162.0


def parse(callout):
    """-> dict(kind=RATE|COUNT|SPACING|UNKNOWN, d, n|rate)."""
    if callout is None or not str(callout).strip():
        return {"kind": "UNKNOWN", "why": "empty cell"}
    s = str(callout)
    m = _RATE.match(s)
    if m:
        return {"kind": "RATE", "rate": float(m.group(1)), "d": int(m.group(2))}
    m = _COUNT.match(s)
    if m:
        return {"kind": "COUNT", "n": int(m.group(1)), "d": int(m.group(2))}
    m = _SPACE.match(s)
    if m:
        f = {"cm": 0.01, "mm": 0.001, "m": 1.0}[m.group(3).lower()]
        return {"kind": "SPACING", "rate": 1.0 / (float(m.group(2)) * f), "d": int(m.group(1))}
    return {"kind": "UNKNOWN", "why": "unreadable: %r" % s}


def counts(rate, side_m, cover_m):
    """Three readings of a rate over a side; rounded to 1e-9 before ceil so 5 x 1.40 = 7 stays exact."""
    inside = side_m - 2 * cover_m
    r1 = math.ceil(round(rate * inside, 9))
    return {"R1": r1, "R2": r1 + 1, "R3": round(rate * side_m, 9), "inside": inside,
            "spacing_R1": inside / (r1 - 1) if r1 > 1 else None,
            "spacing_R2": inside / r1 if r1 > 0 else None}


def layer_rows(mark, L_m, W_m, cover_m, layer, short_callout, long_callout):
    out = []
    for comp, callout, bar_side, spread_side in (("SHORT", short_callout, W_m, L_m), ("LONG", long_callout, L_m, W_m)):
        p = parse(callout)
        row = {"mark": mark, "layer": layer, "component": comp, "printed": callout, "kind": p["kind"]}
        if p["kind"] == "UNKNOWN":
            row.update(status="UNKNOWN", why=p["why"]); out.append(row); continue
        if cover_m is None:
            row.update(status="HELD", why="no printed cover"); out.append(row); continue
        length = bar_side - 2 * cover_m
        km = kg_per_m(p["d"])
        row.update(d=p["d"], bar_length_m=round(length, 4))
        if p["kind"] == "COUNT":
            row.update(status="COUNT_PRINTED", n_R1=p["n"], n_R2=p["n"], n_R3=p["n"])
        else:
            c = counts(p["rate"], spread_side, cover_m)
            row.update(status="HELD_READING", rate_per_m=round(p["rate"], 6), spread_inside_m=round(c["inside"], 4),
                       rate_x_inside=round(p["rate"] * c["inside"], 4), n_R1=c["R1"], n_R2=c["R2"], n_R3=c["R3"],
                       printed_spacing_cm=round(100.0 / p["rate"], 2),
                       spacing_R1_cm=round(100 * c["spacing_R1"], 2) if c["spacing_R1"] else None,
                       spacing_R2_cm=round(100 * c["spacing_R2"], 2) if c["spacing_R2"] else None)
        for k in ("R1", "R2", "R3"):
            row["kg_" + k] = row["n_" + k] * length * km  # rounded only in totals and output
        out.append(row)
    return out


def footing(mark, L, W, cover_m, layers, unit="m"):
    f = {"m": 1.0, "cm": 0.01, "mm": 0.001}[unit]
    rows = []
    for layer, (sc, lc) in layers.items():
        rows += layer_rows(mark, L * f, W * f, cover_m, layer, sc, lc)
    return rows


def total(rows, k):
    """Sum of kg under reading k; None (not 0) when any row is HELD or UNKNOWN."""
    if any(r["status"] in ("UNKNOWN", "HELD") for r in rows):
        return None
    return round(sum(r["kg_" + k] for r in rows), 4)


def check():
    """Synthetic fixture (not any real villa); every expected value is a hand calculation, written out in
    T-155_FOOTING_NOTATION.md section 6."""
    fails = []

    def eq(name, got, exp, tol=0.0001):
        ok = (got is None and exp is None) or (got is not None and exp is not None and abs(got - exp) <= tol)
        if not ok:
            fails.append("%s: got %r expected %r" % (name, got, exp))

    sq = footing("SQ", 2.00, 2.00, 0.07, {"BOT": ("8 ø 12/m", "8 ø 12/m")})
    eq("SQ n R1", sq[0]["n_R1"], 15); eq("SQ n R2", sq[0]["n_R2"], 16); eq("SQ n R3", sq[0]["n_R3"], 16.0)
    eq("SQ kg R1", total(sq, "R1"), 49.6000); eq("SQ kg R2", total(sq, "R2"), 52.9067); eq("SQ kg R3", total(sq, "R3"), 52.9067)
    eq("SQ R1 spacing", sq[0]["spacing_R1_cm"], 13.29); eq("SQ R2 spacing", sq[0]["spacing_R2_cm"], 12.40)
    rc = footing("RE", 3.00, 1.50, 0.07, {"BOT": ("ø 14 @ 15 cm", "ø 14 @ 15 cm")})
    eq("RE short R1", rc[0]["n_R1"], 20); eq("RE long R1", rc[1]["n_R1"], 10)
    eq("RE short R2", rc[0]["n_R2"], 21); eq("RE long R2", rc[1]["n_R2"], 11)
    eq("RE kg R1", total(rc, "R1"), 67.5111); eq("RE kg R2", total(rc, "R2"), 72.6168); eq("RE kg R3", total(rc, "R3"), 67.5111)
    eq("RE slash", total(footing("R2", 3.00, 1.50, 0.07, {"BOT": ("ø 14/15cm", "ø 14/15cm")}), "R2"), 72.6168)
    eq("RE rotated", total(footing("RR", 1.50, 3.00, 0.07, {"BOT": ("ø 14 @ 15 cm", "ø 14 @ 15 cm")}), "R2"), 72.6168)
    eq("RE in cm", total(footing("RC", 300, 150, 0.07, {"BOT": ("ø 14 @ 15 cm", "ø 14 @ 15 cm")}, unit="cm"), "R1"), 67.5111)
    eq("RE in mm", total(footing("RM", 3000, 1500, 0.07, {"BOT": ("ø 14 @ 150 mm", "ø 14 @ 150 mm")}, unit="mm"), "R1"), 67.5111)
    co = footing("CO", 5.00, 2.00, 0.07, {"TOP": ("6 ø 16/m", "6 ø 16/m"), "BOT": ("10 ø 16/m", "10 ø 16/m")})
    eq("CO top short R1", co[0]["n_R1"], 30); eq("CO top long R1", co[1]["n_R1"], 12)
    eq("CO bot short R1", co[2]["n_R1"], 49); eq("CO bot long R1", co[3]["n_R1"], 19)
    eq("CO kg R1", total(co, "R1"), 470.2815); eq("CO kg R2", total(co, "R2"), 491.5200); eq("CO kg R3", total(co, "R3"), 480.9007)
    ex = footing("EX", 1.54, 1.54, 0.07, {"BOT": ("5 ø 10/m", "5 ø 10/m")})
    eq("EX n R1", ex[0]["n_R1"], 7); eq("EX n R2", ex[0]["n_R2"], 8); eq("EX n R3", ex[0]["n_R3"], 7.7)
    eq("EX kg R1", total(ex, "R1"), 12.0988); eq("EX kg R2", total(ex, "R2"), 13.8272); eq("EX kg R3", total(ex, "R3"), 13.3086)
    eq("no cover", total(footing("NC", 2, 2, None, {"BOT": ("8 ø 12/m", "8 ø 12/m")}), "R1"), None)
    eq("unreadable", total(footing("UR", 2, 2, 0.07, {"BOT": ("ø 14/m", "8 ø 12/m")}), "R1"), None)
    eq("spacing no unit", total(footing("NU", 2, 2, 0.07, {"BOT": ("ø 14 @ 15", "8 ø 12/m")}), "R1"), None)
    eq("empty cell", total(footing("EM", 2, 2, 0.07, {"BOT": ("", "8 ø 12/m")}), "R1"), None)
    cn = footing("CN", 2.20, 2.00, 0.07, {"BOT": ("18 ø 12", "17 ø 12")})
    eq("count kept", cn[0]["n_R2"], 18); eq("count kg", total(cn, "R1"), 60.8889)
    eq("autocad diameter", parse("9%%C16/m")["rate"], 9.0)
    return fails


def run(path, csv_path=None):
    data = json.load(open(path, encoding="utf-8"))
    cover, unit = data.get("cover_m"), data.get("unit", "cm")
    rows = []
    for f in data["footings"]:
        rr = footing(f["mark"], f["L"], f["W"], cover, {k: tuple(v) for k, v in f["layers"].items()}, unit=unit)
        for r in rr:
            r["occurrences"] = f.get("occurrences")
        rows += rr
    for r in rows:
        print(r["mark"], r["layer"], r["component"], r["printed"], r.get("bar_length_m"), r.get("rate_x_inside"),
              r.get("n_R1"), r.get("n_R2"), r.get("n_R3"), r.get("printed_spacing_cm"), r.get("spacing_R1_cm"),
              r.get("spacing_R2_cm"), *(None if r.get("kg_" + k) is None else round(r["kg_" + k], 2) for k in ("R1", "R2", "R3")),
              r["status"])
    for f in data["footings"]:
        rr = [r for r in rows if r["mark"] == f["mark"]]
        occ = f.get("occurrences")
        print("TOTAL", f["mark"], "x%s" % occ, *(total(rr, k) for k in ("R1", "R2", "R3")),
              "| BOT", *(total([r for r in rr if r["layer"] == "BOT"], k) for k in ("R1", "R2", "R3")))
    for lay in ("BOT", "TOP", None):
        rr = [r for r in rows if lay is None or r["layer"] == lay]
        if any(r.get("occurrences") is None for r in rr):
            print("ALL", lay or "BOTH", "UNKNOWN (occurrences missing)"); continue
        print("ALL", lay or "BOTH", *(round(sum(r["kg_" + k] * r["occurrences"] for r in rr), 2) for k in ("R1", "R2", "R3")))
    for c in data.get("count_rows", []):
        ps, pl = parse(c["short"]), parse(c["long"])
        f = {"m": 1.0, "cm": 0.01, "mm": 0.001}[unit]
        print("DENSITY", c["mark"], c["short"], round(ps["n"] / (c["L"] * f), 2), "/m along L;",
              c["long"], round(pl["n"] / (c["W"] * f), 2), "/m along W")
    if csv_path:
        keys = sorted({k for r in rows for k in r})
        with open(csv_path, "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=keys); w.writeheader(); w.writerows(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--input")
    ap.add_argument("--csv")
    a = ap.parse_args()
    if a.check:
        f = check()
        print("CHECK", "PASS" if not f else "FAIL", "(%d failures)" % len(f))
        for x in f:
            print("  ", x)
        return 1 if f else 0
    if not a.input:
        ap.error("--input or --check")
    run(a.input, a.csv)
    return 0


if __name__ == "__main__":
    sys.exit(main())
