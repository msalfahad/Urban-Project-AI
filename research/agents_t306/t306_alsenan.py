"""T-306 Alsenan run: decompose the 294 BOUND suspended-slab reinforcement lines of the candidate (T-297 r2 basis
ledger, MERGED 1647711d; lines from T-152 MERGED 798e3b9 via T-179 / V3.0.5) by cause. Reads only merged research
files (numbers, no drawing content). Writes SLAB_SPREAD_DECOMPOSITION_T306.csv, SLAB_SPREAD_SUMMARY_T306.json.

    python3 -I research/agents_t306/t306_alsenan.py --write | --check
"""

import csv
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
import t306_slab_bounds as sb  # noqa: E402

BASIS = os.path.join(ROOT, "research", "agents_t297", "LINE_BASIS_T297.csv")
T152 = os.path.join(ROOT, "research", "agents_t152", "T152_SLAB_STEEL.csv")
SPREAD_EXPECTED = 2188.560          # kg, T-297 r2: 6,832.326 - 4,643.766


def rows(p):
    with open(p, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


T152_INPUT = os.path.join(ROOT, "research", "agents_t152", "T152_INPUT.csv")


def end_census(dec):
    """p.15 TYP. SLAB ON BEAMS DETAIL (drawing-derived reading): a bottom bar END at a CONTINUOUS support either stops
    0.125 L short of the face (50 %) or runs on across the beam (50 %, already booked as the crossing half of the
    bottom line): no development length exists there. At a NON-CONTINUOUS support the bar runs into the edge beam to
    40 mm of its far face and turns up (hook leg not dimensioned). An end on an opening edge has no detail.
    The candidate's development line books 2 x 40 d .. 2 x 70 d on every bar (2 ends per bar). This census counts the
    ends of every bar line segment of readings A and B from the merged T-152 input and books the candidate's own
    per-end figure (40 d at A for the low, 70 d at B for the high) on each end kind. Information for lane I and the
    Checker: no candidate kg is changed."""
    csv.field_size_limit(10 ** 9)
    inp = {(f"SLAB:{r['panel']}", r["dir"]): r for r in rows(T152_INPUT)}
    T = dict(cont_low=0.0, noncont_low=0.0, cont_high=0.0, noncont_high=0.0, model_low=0.0, model_high=0.0,
             extra_segment_ends_A=0, extra_segment_ends_B=0, ends_A=0, cont_A=0, ends_B=0, cont_B=0)
    extra = []
    for r in dec:
        if r["population"] != "DEVELOPMENT / ANCHORAGE":
            continue
        mesh = json.loads(inp[(r["element"], r["direction"])]["mesh"])
        u = sb.kgm(r["d_mm"]) * r["layers"]
        res = {}
        for tag in ("A", "B"):
            n = c = 0
            for segs in mesh[tag]:
                for _ln, e0, e1 in segs:
                    n += 2
                    c += int(e0[0]) + int(e1[0])
            res[tag] = (n, c, len(mesh[tag]))
        (nA, cA, bA), (nB, cB, bB) = res["A"], res["B"]
        lo_end, hi_end = 0.040 * r["d_mm"] * u, 0.070 * r["d_mm"] * u
        T["cont_low"] += cA * lo_end
        T["noncont_low"] += (nA - cA) * lo_end
        T["cont_high"] += cB * hi_end
        T["noncont_high"] += (nB - cB) * hi_end
        T["model_low"] += 2 * bA * lo_end
        T["model_high"] += 2 * bB * hi_end
        T["ends_A"] += nA
        T["cont_A"] += cA
        T["ends_B"] += nB
        T["cont_B"] += cB
        T["extra_segment_ends_A"] += nA - 2 * bA
        T["extra_segment_ends_B"] += nB - 2 * bB
        if nA != 2 * bA or nB != 2 * bB:
            extra.append(dict(line=r["line_id"], element=r["element"], direction=r["direction"],
                              ends_A=nA, bars_A=bA, ends_B=nB, bars_B=bB))
    out = {k: (round(v, 3) if isinstance(v, float) else v) for k, v in T.items()}
    out["lines_with_opening_segment_ends"] = extra
    return out


def run():
    basis = rows(BASIS)
    dec, outside = sb.build(basis, rows(T152))
    T, by = sb.totals(dec)
    slab = [r for r in basis if r["family"] == "SLABS"]
    lo = sum(r["low_kg"] for r in dec)
    hi = sum(r["high_kg"] for r in dec)
    # continuous-end share of the development low bound (count A, 40 d): ends where the bottom bar either stops
    # 0.125 L short (50 %) or already runs across the beam in the crossing half of the bottom line
    dev_cont = sum(r["low_kg"] * r["ends_continuous_A"] / r["ends_A"] for r in dec
                   if r["population"] == "DEVELOPMENT / ANCHORAGE")
    ends = end_census(dec)
    tb_low = sum(r["low_kg"] for r in dec if r["population"] == "TOP BARS OVER SUPPORTS" and r["layers"] == 2)
    summ = dict(
        lines=len(dec), statuses={s: sum(1 for r in slab if r["basis_status"] == s)
                                  for s in sorted({r["basis_status"] for r in slab})},
        bound_low_kg=round(lo, 3), bound_high_kg=round(hi, 3), spread_kg=round(hi - lo, 3),
        causes_kg={k: round(v, 3) for k, v in sorted(T.items())},
        causes_sum_kg=round(sum(T.values()), 6),
        residual_kg=round((hi - lo) - sum(T.values()), 6),
        by_population={p: {k: round(v, 3) for k, v in sorted(c.items())} for p, c in sorted(by.items())},
        skew_B_below_A=[r["line_id"] for r in dec if "SKEW_B_BELOW_A" in r["flags"]],
        readings_outside_bound=outside,
        dev_low_at_continuous_ends_kg=round(dev_cont, 3),
        tb_top_low_kg=round(tb_low, 3),
        dev_end_census=ends,
        drawing_confirmed_components=0,
        cause_text=sb.CAUSES,
    )
    return dec, summ


def main(argv):
    dec, summ = run()
    assert summ["lines"] == 294, summ["lines"]
    assert abs(summ["spread_kg"] - SPREAD_EXPECTED) < 1e-6, summ["spread_kg"]
    assert abs(summ["residual_kg"]) < 1e-6, summ["residual_kg"]
    if "--write" in argv:
        keys = []
        for r in dec:
            for k in r:
                if k not in keys:
                    keys.append(k)
        with open(os.path.join(HERE, "SLAB_SPREAD_DECOMPOSITION_T306.csv"), "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=keys, restval="0")
            w.writeheader()
            w.writerows(dec)
        with open(os.path.join(HERE, "SLAB_SPREAD_SUMMARY_T306.json"), "w", encoding="utf-8") as f:
            json.dump(summ, f, indent=1, ensure_ascii=False)
    print(json.dumps({k: v for k, v in summ.items() if k not in ("cause_text", "readings_outside_bound")},
                     indent=1, ensure_ascii=False))
    print("readings outside bound:", len(summ["readings_outside_bound"]))
    for o in summ["readings_outside_bound"]:
        print("  ", o)


if __name__ == "__main__":
    main(sys.argv[1:])
