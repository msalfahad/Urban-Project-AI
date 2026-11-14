"""T-789 fix rows (Alsenan application of R-T789-1). Inputs: merged repository files only.
  python3 -I research/agents_t789/t789_fill.py [--check]
"""
import json, sys, pathlib
HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
from t789_rules import run_split  # noqa: E402

T742 = ROOT / "research/agents_t742/out/T742_PARAPET_BLOCKS.json"
T761 = ROOT / "research/agents_t761/out/FIX_ROWS.json"
IDX = ROOT / "research/agents_t770/out/LINE_INDEX_V3_0_84.json"
UPSTAND = 0.30   # ST p.14 P1 printed RC upstand above the slab top
FREELANCER = {"ANNEX+GF": (66.00, 1.00), "1F": (42.85, 1.80), "2F": (29.80, 1.00)}  # parsed rows BLK 172/177/178


def lo(s):
    return float(str(s).split("..")[0].strip())


def build():
    runs = json.load(open(T742))["runs"]
    t761 = {r["line_id"]: r for r in json.load(open(T761))["rows"]}
    idx = {r["line_id"]: r for r in json.load(open(IDX))["lines"]}
    chains = {}
    for r in runs:
        L = lo(r["centreline_m"])
        t = lo(r["t_m"]) if str(r["t_m"]).strip() else None
        hp = lo(r["h_above_finish_m"]) if r["h_status"] == "PRINTED" else None
        rc = run_split(L, t, "ALL_RC", hp)
        p1 = run_split(L, t, "P1_UPSTAND", hp, upstand=UPSTAND)
        p1_b0 = run_split(L, t, "P1_UPSTAND", hp, b_edge=0.0, upstand=UPSTAND)
        c = chains.setdefault(r["chain"], {"line": r["candidate_line"], "runs": [], "L": 0, "rc_m3": 0, "p1_conc_m3": 0,
                                            "p1_block_m2": 0, "p1_block_m2_b0": 0, "default_runs": []})
        c["runs"].append(r["run"]); c["L"] += L
        c["rc_m3"] += rc["conc_m3"]; c["p1_conc_m3"] += p1["conc_m3"]
        c["p1_block_m2"] += p1["block_m2"]; c["p1_block_m2_b0"] += p1_b0["block_m2"]
        if rc["h_label"] == "DEFAULT":
            c["default_runs"].append(r["run"])
    rows, tot = [], {"L": 0, "rc_m3": 0, "p1_block_m2": 0, "p1_block_m2_b0": 0, "p1_conc_m3": 0}
    for name, c in chains.items():
        cand = idx[c["line"]]
        assert cand["item_code"] == "STR.CONC.PARAPET" and cand["class"] == "RELEASED"
        # the wired concrete line must equal the ALL_RC split of the same runs (no double count possible)
        assert abs(cand["measured_net"] - round(c["rc_m3"], 4)) < 2e-3, (name, cand["measured_net"], c["rc_m3"])
        for k in tot: tot[k] += c[k]
        rows.append({
            "id": f"F-T789-{len(rows) + 1}", "line_id": None, "item_code": "MAS.BLOCK.PARAPET", "unit": "m2",
            "element_id": f"{name}#PARAPET_BLOCK", "action": "NO_LINE",
            "before": {"class": "HELD (T-742 draft, never wired)", "low": 0.0, "high": None},
            "after": {"class": "RELEASED", "net": 0.0, "label": "DRAWING-READ"},
            "basis": (f"{name}: {len(c['runs'])} runs, centreline {c['L']:.2f} m; this villa's sections A-A / B-B cut every "
                      f"parapet in the slab / beam hatch (block walls unhatched, T-311 s.2): the whole run is billed as "
                      f"{c['line']} STR.CONC.PARAPET {cand['measured_net']} m3 (T-761, wired; = R-T789-1 ALL_RC "
                      f"{c['rc_m3']:.4f}); masonry is its complement = 0, never both"
                      + (f"; height DEFAULT 1.20 on {', '.join(c['default_runs'])}" if c['default_runs'] else "")),
            "alternative_P1": {"block_m2": round(c["p1_block_m2"], 2), "concrete_m3": round(c["p1_conc_m3"], 4),
                               "concrete_change_m3": round(c["p1_conc_m3"] - cand["measured_net"], 4),
                               "basis": "ST p.14 P1 typical: RC upstand 0.30 above slab top + block above, H = h + 0.175"},
            "designer_item": "D-39 / Q-65 C (DESIGNER_QUESTIONS item 5)"})
    fl = sum(a * b for a, b in FREELANCER.values())
    rows.append({
        "id": f"F-T789-{len(rows) + 1}", "line_id": "L-7503af7cc1eea4e6735d", "item_code": "MAS.BLOCK", "unit": "m2",
        "element_id": "HOUSE_BELOW_NG:MAIN_S", "action": "BASIS_TEXT (supersedes F-T779-1 text)",
        "before": {"class": "RELEASED", "net": 11.389, "label": "ESTIMATE"},
        "after": {"class": "RELEASED", "net": 11.389, "label": "ESTIMATE"},
        "basis": ("MAIN_S run 16.27 x 0.70 m = 11.389: 0.70 = slab -0.10 down to the governing ground-beam band top -0.80 "
                  "(T-407 lower bound h >= 0.70; the footing top -0.85 does not govern, Checker F-V779-2); not a printed "
                  "depth; block under the neighbour-side beam printed (ST p.1 n.2); formation unprinted (Q-21 C)")})
    out = {"schema": "URBAN_FIX_ROWS_V1", "task": "T-789", "rule": "R-T789-1 (t789_rules.py, every villa)",
           "base": "ARCH_TAKEOFF_V3.0.84 (LINE_INDEX_V3_0_84.json)", "rows": rows,
           "totals": {"centreline_m": round(tot["L"], 3), "concrete_all_rc_m3": round(tot["rc_m3"], 4),
                      "masonry_m2": 0.0, "alt_P1_block_m2": round(tot["p1_block_m2"], 2),
                      "alt_P1_block_m2_b_edge_0": round(tot["p1_block_m2_b0"], 2),
                      "alt_P1_concrete_m3": round(tot["p1_conc_m3"], 4)},
           "freelancer": {"parapet_block_m2": round(fl, 2),
                          "vs_ours_m2": round(fl - 0.0, 2),
                          "split": "material RULE_DIFFERENCE (he books block, this villa's sections draw RC; designer item 5); "
                                   "his 0.50 m below the finish = edge member concrete ENGINE_RIGHT 68.42 (T-550); "
                                   "his flat 1.80 vs printed 1F heights ENGINE_RIGHT 7.63 (T-550)"}}
    return out


if __name__ == "__main__":
    out = build()
    p = HERE / "out/FIX_ROWS.json"
    text = json.dumps(out, indent=1) + "\n"
    if "--check" in sys.argv:
        assert p.read_text() == text, "FIX_ROWS.json stale"; print("check OK")
    else:
        p.write_text(text); print(json.dumps(out["totals"]))
