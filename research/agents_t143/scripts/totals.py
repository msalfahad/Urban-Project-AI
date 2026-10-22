"""T-143 totals per floor, block type and thickness; freelancer comparison; Q-69 ledger (research only).
Usage: python3 -I totals.py <scratch> <out_dir>"""
import csv
import json
import sys
from collections import defaultdict

S, OUT = sys.argv[1], sys.argv[2]
rows = list(csv.DictReader(open(f"{OUT}/T143_BLOCK_BY_WALL_RUN.csv")))
raw = json.load(open(f"{S}/wb/tests/alsenan/registers_b1/FREELANCER_RAW_ROWS.json"))
d12 = list(csv.DictReader(open(f"{S}/wb/research/agents_t117/D12_CONFLICT_RUNS.csv")))


def f(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return 0.0


# ---- freelancer blockwork workbook, sheet of quantities: H = length x height x count per row ----------------------
H = {}
for r in raw["rows"]:
    if r["file"] == "BLK" and r["sheet"] != raw["rows"][0]["sheet"]:
        c = r["cells"]
        if f"H{r['row']}" in c:
            H[r["row"]] = c[f"H{r['row']}"]["v"]
sm = lambda a, b: round(sum(f(H.get(i)) for i in range(a, b + 1)), 4)
FL = {
    ("GF", "EXTERNAL"): dict(gross=sm(14, 36), ded=sm(41, 51)),
    ("1F", "EXTERNAL"): dict(gross=round(sm(63, 77), 4), ded=sm(84, 90), extra="projections row 78: 7.50 x 5.50 = 41.25 m2 (not a wall run)"),
    ("2F", "EXTERNAL"): dict(gross=sm(101, 107), ded=sm(111, 115)),
    ("GF", "INTERNAL 0.15"): dict(gross=sm(133, 149), ded=sm(185, 186), extra="fence row 150: 37.20 x 2.00 = 74.40 m2 (fence, HELD here)"),
    ("1F", "INTERNAL 0.15"): dict(gross=sm(154, 170), ded=sm(188, 189), extra="ground-roof parapet row 172: 66.00 x 1.00 = 66.00 m2 (HELD here)"),
    ("2F", "INTERNAL 0.15"): dict(gross=sm(176, 176), ded=sm(191, 192), extra="first-roof parapet row 177 42.85 x 1.80 = 77.13 and top roof row 178 29.80 x 1.00 (HELD here)"),
    ("GF", "INTERNAL 0.20"): dict(gross=sm(203, 206), ded=None),
    ("1F", "INTERNAL 0.20"): dict(gross=sm(208, 211), ded=None),
    ("2F", "INTERNAL 0.20"): dict(gross=sm(213, 216), ded=None, extra="20 cm deduction 9.84 m2 is not split by floor (rows 222-223)"),
}
check = {"ext_total": sm(14, 36) + sm(63, 78) + sm(101, 107), "fl15_total": sm(133, 178), "fl20_total": sm(203, 216)}

# ---- our totals -------------------------------------------------------------------------------------------------
def sect(r):
    if r["group"] == "EXTERNAL":
        return "EXTERNAL"
    return f"INTERNAL {float(r['t_m']):.2f}" if r["group"] == "INTERNAL" else r["group"]


T = defaultdict(lambda: defaultdict(float))
TT = defaultdict(lambda: defaultdict(float))
for r in rows:
    k = (r["floor"], sect(r))
    k2 = (r["floor"], r["block_type"] or "-", r["t_m"])
    for K, D in ((k, T), (k2, TT)):
        D[K]["L1"] += f(r["L1_arch_run_m"])
        D[K]["L2a"] += f(r["L2a_q69_physical_m"])
        D[K]["held_len"] += f(r["held_len_m"])
        D[K]["m2_owner"] += f(r["gross_m2_owner_run"])
        D[K]["m2_q69"] += f(r["gross_m2_q69_physical"])
        D[K]["m3"] += f(r["m3_q69_physical"])
        D[K]["prov_m2"] += f(r["gross_m2_q69_physical"]) if r["status"] in ("PROVISIONAL",) else 0
        D[K]["w64"] += f(r["white_blocks_6.4"]) if r["block_type"] == "WHITE" else 0
        D[K]["w833"] += f(r["white_blocks_8.33"]) if r["block_type"] == "WHITE" else 0
        D[K]["rows"] += 1
        hc = r["held_m2_candidate"] or ""
        lo = hi = nc = 0.0
        if hc:
            a, _, b = hc.partition(" + ")
            p = a.split("-")
            lo, hi = float(p[0]), float(p[-1])
            nc = float(b.split(" m")[0]) if b else 0.0
        elif r["status"] == "HELD" and f(r["held_len_m"]):
            nc = f(r["held_len_m"])
        D[K]["cand_lo"] += lo
        D[K]["cand_hi"] += hi
        D[K]["no_cand_len"] += nc

with open(f"{OUT}/T143_TOTALS_VS_FREELANCER.csv", "w", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["floor", "freelancer_section", "runs", "L1_arch_run_m", "L2a_q69_physical_m", "held_len_m",
                "hand_gross_m2_owner_run", "hand_gross_m2_q69_physical (measured part)", "of_which_provisional_m2",
                "freelancer_gross_m2", "diff_m2 (hand q69 - freelancer)", "diff_pct", "freelancer_deduction_m2",
                "freelancer_net_m2", "hand_net_m2", "hand_gross_with_held_candidates_m2", "length_with_no_candidate_m",
                "diff_with_candidates_pct", "note"])
    for fl in ("GF", "1F", "2F"):
        for s in ("EXTERNAL", "INTERNAL 0.15", "INTERNAL 0.20"):
            D = T[(fl, s)]
            F = FL[(fl, s)]
            g = F["gross"]
            diff = D["m2_q69"] - g
            w.writerow([fl, s, int(D["rows"]), round(D["L1"], 3), round(D["L2a"], 3), round(D["held_len"], 3),
                        round(D["m2_owner"], 3), round(D["m2_q69"], 3), round(D["prov_m2"], 3), g, round(diff, 3),
                        f"{100 * diff / g:+.1f} %" if g else "", F["ded"] if F["ded"] is not None else "not split",
                        round(g - F["ded"], 3) if F["ded"] is not None else "", "HELD",
                        f"{D['m2_q69'] + D['cand_lo']:.3f}" + (f" .. {D['m2_q69'] + D['cand_hi']:.3f}" if D['cand_hi'] - D['cand_lo'] > 1e-6 else ""),
                        round(D["no_cand_len"], 3),
                        f"{100 * (D['m2_q69'] + D['cand_lo'] - g) / g:+.1f} %" + (f" .. {100 * (D['m2_q69'] + D['cand_hi'] - g) / g:+.1f} %" if D['cand_hi'] - D['cand_lo'] > 1e-6 else ""),
                        "not like-for-like while held length > 0 (held is not 0, it is missing from the hand m2)"
                        + ("; " + F["extra"] if F.get("extra") else "")])

with open(f"{OUT}/T143_TOTALS_BY_TYPE_THICKNESS.csv", "w", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["floor", "block_type", "t_m", "runs", "L1_arch_run_m", "L2a_q69_physical_m", "held_len_m",
                "gross_m2_q69_measured", "of_which_provisional_m2", "m3_measured", "white_blocks_at_6.4",
                "white_blocks_at_8.33", "note"])
    for k in sorted(TT):
        D = TT[k]
        w.writerow([*k, int(D["rows"]), round(D["L1"], 3), round(D["L2a"], 3), round(D["held_len"], 3),
                    round(D["m2_q69"], 3), round(D["prov_m2"], 3), round(D["m3"], 4),
                    round(D["w64"], 0) if k[1] == "WHITE" else "", round(D["w833"], 0) if k[1] == "WHITE" else "",
                    "gross before opening deduction (net HELD); black: no supplier face size -> count HELD"
                    if k[1] == "BLACK" else "gross before opening deduction (net HELD); product face size not chosen"])

# ---- T-stem overlap in m3 (T-103 junction census): centreline runs carry each stem t_through/2 into the through wall
CENSUS = {"GF": {"0.200": 0.475, "0.150": 1.450}, "1F": {"0.200": 0.375, "0.150": 1.500}, "2F": {"0.200": 0.375, "0.150": 0.100}}
ov = []
for fl, dd in CENSUS.items():
    for t, m in dd.items():
        rs = [r for r in rows if r["floor"] == fl and r["t_m"] == t and f(r["height_m_weighted"])]
        L = sum(f(r["L2a_q69_physical_m"]) - f(r["held_len_m"]) for r in rs)
        hm = sum(f(r["gross_m2_q69_physical"]) for r in rs) / L if L else 0
        ov.append((fl, t, m, round(hm, 3), round(m * float(t) * hm, 4)))

# ---- D-12: walls containing columns (structural p.8 note 20) at the column thickness, m3 side by side -------------
d12rows = []
for c in d12:
    for hr in [x.strip() for x in c["hand_rows"].split("+")]:
        r = next((x for x in rows if x["row_id"] == hr), None)
        if r and f(r["gross_m2_q69_physical"]):
            d12rows.append((hr, c["t_drawn_m"], c["t_by_note_s2_m"], r["gross_m2_q69_physical"],
                            round(f(r["gross_m2_q69_physical"]) * float(c["t_drawn_m"]), 4),
                            round(f(r["gross_m2_q69_physical"]) * float(c["t_by_note_s2_m"]), 4)))
json.dump({"freelancer": {"|".join(k): v for k, v in FL.items()}, "check": check, "tstem": ov, "d12": d12rows,
           "totals": {f"{k[0]}|{k[1]}": v for k, v in T.items()},
           "by_type": {"|".join(k): v for k, v in TT.items()}}, open(f"{S}/t143_totals.json", "w"), indent=1)
print(json.dumps(check))
for k in sorted(T):
    print(k, {a: round(b, 3) for a, b in T[k].items()})
for k in sorted(TT):
    print(k, {a: round(b, 3) for a, b in TT[k].items()})
print("tstem", ov)
print("d12", d12rows)
