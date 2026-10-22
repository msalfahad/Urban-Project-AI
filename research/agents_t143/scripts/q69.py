"""T-143: owner Q-69 B wall-by-wall ledger, ground floor (research only). Usage: python3 -I q69.py <scratch> <out>"""
import csv, sys
from collections import defaultdict
S, OUT = sys.argv[1], sys.argv[2]
rows = [r for r in csv.DictReader(open(f"{OUT}/T143_BLOCK_BY_WALL_RUN.csv")) if r["floor"] == "GF" and r["group"] in ("EXTERNAL", "INTERNAL")]
fm = list(csv.DictReader(open(f"{S}/wb/research/agents_t103/FREELANCER_ROWS_MATCH.csv")))
his = defaultdict(float)
unm = []
for r in fm:
    if r["floor"] != "GF" or not r["his_length_m"] or r["section"].startswith("("):
        continue
    if r["matched_run"] and r["match"] in ("EXACT", "CLOSE"):
        his[r["matched_run"]] += float(r["his_length_m"])
    elif r["match"] == "UNMATCHED":
        unm.append(r)
out = csv.writer(open(f"{OUT}/T143_Q69_LEDGER_GF.csv", "w", newline=""))
out.writerow(["line", "group", "t_m", "L1_arch_run_m (owner manual, UP-WALL-GEOM-001)", "glass_line_out_m (Q-69 B)",
              "L2a_physical_candidate_m", "freelancer_matched_pieces_m", "L1_minus_freelancer_m", "note"])
T = defaultdict(float)
for r in rows:
    L1, L2 = float(r["L1_arch_run_m"]), float(r["L2a_q69_physical_m"])
    h = his.get(r["row_id"], 0.0)
    g = r["group"]
    T[(g, "L1")] += L1; T[(g, "L2")] += L2; T[(g, "his")] += h
    note = "full glazing span out of the physical run (owner Q-69 B); solid piece kept" if L1 != L2 else ""
    out.writerow([r["row_id"], g, r["t_m"], L1, round(L1 - L2, 3), L2, round(h, 3), round(L1 - h, 3), note])
for r in unm:
    g = "EXTERNAL" if r["section"] == "external" else "INTERNAL"
    L = float(r["his_length_m"])
    T[(g, "his")] += L
    out.writerow([f"freelancer row {r['workbook_row']} (no hand piece within 0.06 m)", g, r["section"], 0, 0, 0, L, -L, "his piece not paired (T-103)"])
for g in ("EXTERNAL", "INTERNAL"):
    out.writerow([f"TOTAL {g}", g, "", round(T[(g, 'L1')], 3), round(T[(g, 'L1')] - T[(g, 'L2')], 3), round(T[(g, 'L2')], 3),
                  round(T[(g, 'his')], 3), round(T[(g, 'L1')] - T[(g, 'his')], 3), ""])
a = T[("EXTERNAL", "L1")] + T[("INTERNAL", "L1")]; b = T[("EXTERNAL", "L2")] + T[("INTERNAL", "L2")]; c = T[("EXTERNAL", "his")] + T[("INTERNAL", "his")]
out.writerow(["TOTAL GF", "", "", round(a, 3), round(a - b, 3), round(b, 3), round(c, 3), round(a - c, 3), "physical - freelancer = %.3f m (%.1f %%)" % (b - c, 100 * (b - c) / c)])
print({k: round(v, 3) for k, v in T.items()}, a, b, c)
