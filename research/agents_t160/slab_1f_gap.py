"""T-160 (3): can the 1F roof-slab gap against the freelancer's lump be traced to drawn pieces?

Freelancer: one lump 120.00 m2 x 0.16 (his slab sheet, 1F row; no breakdown). Hand (T-139 PANELS.csv, 1F SLAB rows):
sum of slab panel areas. Gap G = hand - 120.00. Hypotheses tested, each a set of drawn pieces he may have left out
(or added) whose area re-adds G within a tolerance:
  H1  he left out the eight dome-square corners (3.846 m2) -> remainder R1 = 120.00 - (hand - corners)
  H2  any 1 or 2 drawn 1F pieces (slab panels, edge strips held in the beam lane, openings, stair zone) re-add G
  H3  after H1, any 1 or 2 pieces re-add R1
A hypothesis supported by MORE than one combination is not a trace: the lump cannot tell which.
Usage: python -I slab_1f_gap.py <T-139 PANELS.csv> [--lump 120.00] [--tol 0.010]
"""
import csv
import itertools
import sys


def main(path, lump=120.00, tol=0.010):
    rows = [r for r in csv.DictReader(open(path)) if r["floor"] == "1F"]
    slab = [r for r in rows if r["cls"] == "SLAB"]
    hand = sum(float(r["area"]) for r in slab)
    corners = [r for r in slab if "dome square corner" in r["evidence"]]
    ca = sum(float(r["area"]) for r in corners)
    pieces = [(r["id"], r["cls"], float(r["area"])) for r in rows if r["cls"] in ("SLAB", "EDGE_HELD", "OPENING", "STAIR")]
    G = hand - lump
    R1 = lump - (hand - ca)
    print(f"1F hand slab {hand:.4f} m2 ({len(slab)} panels) x 0.16 = {hand * 0.16:.4f} m3; freelancer lump {lump:.2f} m2")
    print(f"gap G = {G:+.4f} m2 ({G * 0.16:+.4f} m3, {G / hand * 100:+.2f} % of the hand area)")
    print(f"H1 dome corners {len(corners)} pieces {ca:.4f} m2 -> remainder R1 = {R1:+.4f} m2 ({R1 * 0.16:+.4f} m3)")
    for name, target in (("H2 (re-add G)", G), ("H3 (re-add R1, after H1)", R1)):
        hits = []
        for n in (1, 2):
            for combo in itertools.combinations(pieces, n):
                for signs in itertools.product((1, -1), repeat=n):
                    s = sum(sg * p[2] for sg, p in zip(signs, combo))
                    if abs(abs(s) - abs(target)) <= tol and (s > 0) == (target > 0):
                        hits.append((round(s, 4), [f"{'+' if sg > 0 else '-'}{p[0]} {p[1]} {p[2]}" for sg, p in zip(signs, combo)]))
        print(f"{name}: {len(hits)} combination(s) within +/-{tol} m2")
        for h in hits[:12]:
            print("   ", h)
    return G, R1


if __name__ == "__main__":
    a = sys.argv[1:]
    lump = float(a[a.index("--lump") + 1]) if "--lump" in a else 120.00
    tol = float(a[a.index("--tol") + 1]) if "--tol" in a else 0.010
    main(a[0], lump, tol)
