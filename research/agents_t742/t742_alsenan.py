"""T-742 development villa (research only, not a method, not wired): B9-05 parapet block walls drafted run by run.

    python3 -I research/agents_t742/t742_alsenan.py [--check]

Inputs are merged repository files only (no private input needed to rebuild):
  research/agents_t319/V3_0_23_RUNS_T319.csv      the candidate's parapet run set (T-311 ledger + T-324 corrections)
  research/agents_t311/PARAPET_RUN_LEDGER_T311.csv outer / inner top arris per run (T-172 geometry)
  research/agents_t311/FREELANCER_T311.csv         his three parapet rows (comparison only)
  research/agents_t737/out/T737_ROWS.csv           the exterior finish's parapet outer-face lines (T-737)
  research/agents_t742/in/T742_CENSUS.json         this task's own DXF census (handles, layers, lengths; no coordinate),
                                                   written by t742_census.py from the private plan DXF
Writes out/T742_PARAPET_BLOCKS.json and out/T742_PARAPET_BLOCKS.md; --check rebuilds and compares byte for byte.

Project facts (each with its drawing source; Alsenan only, never in t742_rules.py):
  material of every run UNKEYED: ST p.14 P1 'Brick Wall' on a 0.30 RC upstand vs P2 / P3 all RC vs sections A-A / B-B
  hatched all RC; no detail keyed to a run (T-311 s.2); owner Q-65 C: material HELD, designer; DESIGNER_QUESTIONS 5.
  upstand of the block reading 0.30 above the slab top (P1 '30'); b_edge (finish minus slab top) HELD 0 .. 0.30
  (D-39; P1 note: the upstand 'MUST BE MORE THAN THE HEIGHT OF ROOF FINISHING'); no cap on the architectural sections
  (plain top, T-311 s.2), P1 cap 'AS PER ARC.' unprinted -> cap 0 here, and the lower end of the block reading is
  the RC reading 0 anyway (UNKEYED).
"""
import csv
import json
import sys
from decimal import Decimal
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import t742_rules as R                                                         # noqa: E402

RUNS = ROOT / "research/agents_t319/V3_0_23_RUNS_T319.csv"
LEDGER = ROOT / "research/agents_t311/PARAPET_RUN_LEDGER_T311.csv"
FREEL = ROOT / "research/agents_t311/FREELANCER_T311.csv"
T737 = ROOT / "research/agents_t737/out/T737_ROWS.csv"
CENSUS = HERE / "in/T742_CENSUS.json"
OUT_J, OUT_M = HERE / "out/T742_PARAPET_BLOCKS.json", HERE / "out/T742_PARAPET_BLOCKS.md"

DESIGNER = "D-39 / Q-65 C (DESIGNER_QUESTIONS item 5: parapet material per run, roof build-up b_edge)"
UPSTAND, B_EDGE, CAP = ("0.30", "0.30"), ("0", "0.30"), ("0", "0")
T737_LINE = {"ANNEX": "PARAPET-OUTER ANNEX +4.30", "GF": "PARAPET-OUTER GF +5.50", "1F": "PARAPET-OUTER 1F +9.70",
             "2F": "PARAPET-OUTER 2F +13.90"}
NW_PROFILE_FACE = "12A7"           # 1F roof NW inner face on the 2F plan (census outer_profiles)
NW_GROUP = {("1F", x) for x in ("NW-1", "NW-2", "NW-3", "NE-1", "NW-4", "SW-1", "NW-5")}
H_PRINTED = {"ANNEX": "0.50", "GF": "0.50", "2F": "0.50"}      # T-172 TOP minus ROOF (printed levels)


def rng(cell):
    lo, hi = (x.strip() for x in cell.split(".."))
    return (lo, hi) if lo != hi else lo


def s6(x):
    return None if x is None else (f"{x[0]} .. {x[1]}" if isinstance(x, tuple) and x[0] != x[1] else
                                   str(x[0] if isinstance(x, tuple) else x))


def build():
    runs = list(csv.DictReader(open(RUNS, newline="", encoding="utf-8")))
    led = {(r["chain"], r["side"]): r for r in csv.DictReader(open(LEDGER, newline="", encoding="utf-8"))}
    cen = json.loads(CENSUS.read_text(encoding="utf-8"))
    cr = {(r["chain"], r["side"]): r for r in cen["runs"]}
    chains, rows = {}, []
    for r in runs:
        key = (r["chain"], r["run"])
        spec = {"id": f'{r["chain"]}/{r["run"]}', "centreline_m": rng(r["centreline_m"]),
                "h_above_finish_m": rng(r["h_above_finish_m"]), "t_m": r["t_m"], "material": "UNKEYED",
                "upstand_above_slab_top_m": UPSTAND, "b_edge_m": B_EDGE, "cap_m": CAP, "openings_m2": [],
                "designer_item": DESIGNER, "block_type": None}
        prof = NW_PROFILE_FACE in cen["outer_profiles"] and key in NW_GROUP
        if prof:
            # R-T742-3: the roof plan draws this group's inner face straight (one entity) with an outer profile of
            # varying depth; the body thickness is HELD between the ledger t and the deepest profile line
            deep = max(R.D(str(p["depth_m"])) for p in cen["outer_profiles"][NW_PROFILE_FACE]["profile"])
            spec["t_m"] = (r["t_m"], str(deep))
        chains.setdefault(r["chain"], []).append(spec)
        L = led.get(key)
        c = cr.get(key)
        if c:
            st = R.census_status(str(c["outer_line_m"]), str(c["outer_drawn_m"]), str(c["inner_drawn_m"]),
                                 L["inner_top_arris_m"] if L else "0")
        else:
            st = "NOT_IN_OUTLINE_CHAIN (run found after T-311: T-324 C5)"
        rows.append({"chain": r["chain"], "run": r["run"], "candidate_line": r["line_id"], "t_m": s6(
                     spec["t_m"] if isinstance(spec["t_m"], tuple) else (spec["t_m"], spec["t_m"])),
                     "centreline_m": r["centreline_m"], "h_above_finish_m": r["h_above_finish_m"],
                     "h_status": r["h_status"],
                     "outer_arris_m": L["outer_top_arris_m"] if L else None,
                     "inner_arris_m": L["inner_top_arris_m"] if L else None,
                     "census": st,
                     "outer_handles": [h["handle"] for h in c["outer_handles"]] if c else [],
                     "outer_drawn_m": c["outer_drawn_m"] if c else None,
                     "inner_handles": [h["handle"] for h in c["inner_handles"]] if c else [],
                     "inner_drawn_m": c["inner_drawn_m"] if c else None})
    lines = {}
    for ch, specs in chains.items():
        fl = R.family_line(ch, specs)
        # the P1 reading (block on the 0.30 upstand) at b_edge 0 and cap 0, T-311's convention: a reference figure
        p1l = R.family_line(ch, [dict(s, material="BLOCK", b_edge_m="0") for s in specs])["net_m2"]
        per_b = sum((R.D(s["centreline_m"][0] if isinstance(s["centreline_m"], tuple) else s["centreline_m"])
                     for s in specs), Decimal(0))
        lines[ch] = {"family": "B9-05 MAS.BLOCK.PARAPET", "status": fl["status"], "net_m2": s6(fl["net_m2"]),
                     "m3": s6(fl["m3"]), "p1_reading_at_b_edge_0_m2": s6(p1l),
                     "p1_increment_m2_per_m_b_edge": str(R.q(per_b)), "runs": len(specs),
                     "designer_item": DESIGNER, "procurement": "HELD (block type Q-65 C; black 12.5 / m2 only if keyed)"}
    # R-T742-2: face trade (T-737) against the masonry centreline, for the chains whose face is MEASURED / bounded
    face = {}
    for r in csv.DictReader(open(T737, newline="", encoding="utf-8")):
        for ch, tag in T737_LINE.items():
            if r["kind"] == "STAGE_LINE" and r["id"].endswith(tag):
                face[ch] = r["stage_after"]
    recon = {}
    for ch in ("ANNEX", "GF", "2F", "1F"):
        st = face.get(ch)
        val = st.split(" ", 1)[1]
        if ch == "1F":
            recon[ch] = {"t737": st, "verdict": "NOT_INVERTIBLE: the 1F face is the sum of per-run CAD-top heights "
                         "(0.448 .. 1.30, 3 runs HELD) so no single length follows from it; the census below checks "
                         "the 1F runs by handle instead"}
            continue
        h = R.D(H_PRINTED[ch])
        lo = val.split(" .. ")[0]
        chain_runs = [{"outer_m": led[(ch, s)]["outer_top_arris_m"], "inner_m": led[(ch, s)]["inner_top_arris_m"]}
                      for s in [x["run"] for x in runs if x["chain"] == ch] if (ch, s) in led]
        rc = R.reconcile_lengths(chain_runs, R.D(lo) / h)
        recon[ch] = {"t737": st, "face_length_from_face_m": str(rc["face_length_m"]),
                     "outer_sum_m": str(rc["outer_sum_m"]), "centreline_sum_t311_m": str(rc["centreline_sum_m"]),
                     "corner_term_m": str(rc["corner_term_m"]), "face_vs_outer_m": str(rc["face_vs_outer_m"]),
                     "closes": rc["closes"]}
    recon["ANNEX"]["upper_end"] = ("T-737 high end +0.600 m2 = 1.200 m x 0.50: the NE-6x run found after T-311 "
                                   "(T-324 C5, centreline 1.29995) and the SW-3 cut range; carried as the bound")
    recon["GF"]["sw9"] = ("SW-9 roof-plan pair BDB / BDC drawn 0.8948 m; + t/2 = 0.9948 = the V3.0.23 low end "
                          "0.99478; the outline reading 1.3999 is the high end (range kept, cause named)")
    nw_inner = sum((R.D(led[k]["inner_top_arris_m"]) for k in sorted(NW_GROUP) if k in led), Decimal(0))
    nw_t311_cl = sum((R.D(led[k]["centreline_m"]) for k in sorted(NW_GROUP) if k in led), Decimal(0))
    nw_v3023_cl = sum((R.D(rng(x["centreline_m"]) if not isinstance(rng(x["centreline_m"]), tuple) else
                       rng(x["centreline_m"])[0]) for x in runs if (x["chain"], x["run"]) in NW_GROUP), Decimal(0))
    face12 = R.D(str(cen["outer_profiles"][NW_PROFILE_FACE]["inner_face_m"]))
    recon["1F"]["nw_group"] = {
        "roof_plan_inner_face_m": str(face12), "t311_outline_inner_arrises_m": str(R.q(nw_inner)),
        "difference_m": str(R.q(face12 - nw_inner)),
        "t311_centreline_m": str(R.q(nw_t311_cl)), "v3023_centreline_m": str(R.q(nw_v3023_cl)),
        "v3023_minus_t311_m": str(R.q(nw_v3023_cl - nw_t311_cl)),
        "verdict": "AGREES: the roof plan draws the NW inner face straight (12A7); T-311 followed the wavy floor "
                   "outline (+0.4435 m on NW-2); T-324 C3 straightened NW-2 in V3.0.23 by the same 0.4435 m; this is "
                   "the 1F length difference T-550 named (49.676 vs 49.233)"}
    fr = [{"row": r["freelancer_row"].split(" ")[0] + " " + r["freelancer_row"].split(" ")[1],
           "his_m2": r["his_m2"], "his_length_m": r["his_length_m"], "his_height_m": r["his_height_m"]}
          for r in csv.DictReader(open(FREEL, newline="", encoding="utf-8"))]
    tot_lo = sum((R.D(lines[c]["net_m2"].split(" .. ")[0]) for c in lines), Decimal(0))
    tot_hi = sum((R.D(lines[c]["net_m2"].split(" .. ")[-1]) for c in lines), Decimal(0))
    p1t = (sum((R.D(lines[c]["p1_reading_at_b_edge_0_m2"].split(" .. ")[0]) for c in lines), Decimal(0)),
           sum((R.D(lines[c]["p1_reading_at_b_edge_0_m2"].split(" .. ")[-1]) for c in lines), Decimal(0)))
    his = sum((R.D(x["his_m2"]) for x in fr), Decimal(0))
    return {"rule": R.RULE, "task": "T-742", "status": "research only, not wired; no candidate line moved",
            "family_lines": lines, "total_net_m2": f"{R.q(tot_lo)} .. {R.q(tot_hi)}",
            "total_p1_reading_at_b_edge_0_m2": f"{R.q(p1t[0])} .. {R.q(p1t[1])}", "runs": rows, "length_reconciliation": recon,
            "outer_profiles_not_in_outline": cen["outer_profiles"], "registration": cen["registration"],
            "freelancer": {"rows": fr, "his_total_m2": str(R.q(his)),
                           "vs_ceiling_m2": str(R.q(his - tot_hi)), "vs_p1_m2": f"{R.q(his - p1t[1])} .. {R.q(his - p1t[0])}"}}


def md(d):
    L = ["# T-742 B9-05 parapet block walls (generated by t742_alsenan.py; research only)", "",
         "| Chain | Runs | Net m2 (HELD: RC reading .. block ceiling) | m3 | P1 reading at b_edge 0 | + m2 per m b_edge |",
         "|---|---|---|---|---|---|"]
    for c, v in d["family_lines"].items():
        L.append(f"| {c} | {v['runs']} | {v['net_m2']} | {v['m3']} | {v['p1_reading_at_b_edge_0_m2']} | "
                 f"{v['p1_increment_m2_per_m_b_edge']} |")
    L += ["", f"Total {d['total_net_m2']} m2; P1 reading {d['total_p1_reading_at_b_edge_0_m2']} m2. Freelancer "
          f"{d['freelancer']['his_total_m2']} m2 (vs ceiling {d['freelancer']['vs_ceiling_m2']}, vs P1 "
          f"{d['freelancer']['vs_p1_m2']}).", "", "| Run | Line | Centreline m | h m | Census | Outer handles (drawn m) | Inner handles (drawn m) |",
          "|---|---|---|---|---|---|---|"]
    for r in d["runs"]:
        L.append(f"| {r['chain']}/{r['run']} | {r['candidate_line']} | {r['centreline_m']} | {r['h_above_finish_m']} | "
                 f"{r['census']} | {'+'.join(r['outer_handles']) or '-'} ({r['outer_drawn_m']}) | "
                 f"{'+'.join(r['inner_handles']) or '-'} ({r['inner_drawn_m']}) |")
    L += ["", "Length reconciliation (R-T742-2):", ""]
    for c, v in d["length_reconciliation"].items():
        L.append(f"- {c}: " + "; ".join(f"{k} {v[k]}" for k in v))
    return "\n".join(L) + "\n"


def main():
    d = build()
    j = json.dumps(d, indent=1, ensure_ascii=False) + "\n"
    m = md(d)
    if "--check" in sys.argv:
        ok = OUT_J.read_text(encoding="utf-8") == j and OUT_M.read_text(encoding="utf-8") == m
        print("T742 check", "OK" if ok else "DIFFERS")
        sys.exit(0 if ok else 1)
    OUT_J.parent.mkdir(exist_ok=True)
    OUT_J.write_text(j, encoding="utf-8")
    OUT_M.write_text(m, encoding="utf-8")
    print(m)


if __name__ == "__main__":
    main()
