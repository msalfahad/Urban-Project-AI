"""T-406 Alsenan: CONCRETE RECONCILIATION ROLL-UP r3. The T-385 r2 cause closure (candidate ARCH_TAKEOFF_V3.0.29 vs
the freelancer's concrete workbook, 47 components, 9 families) restated component by component with the traces of the
Checker-MERGED tasks T-391, T-394, T-395, T-398, T-401 and T-403 (T-392 and T-402 merged: confirmations, no figure
moves), the plot-boundary concrete below N.G. moved to its own family row, and the V3.0.33 candidate moves of the
merged Gate B T-397 printed apart (research only: no quantity, line, state or released cell changes).

Inputs (committed unless marked):
  research/agents_t391/summary_t391.json, agents_t394/summary_t394.json, agents_t395/summary_t395.json,
  agents_t398/summary_t398.json, agents_t401/summary_t401.json, agents_t403/summary_t403.json,
  agents_t397/summary_t397.json     the merged traces / candidate moves, READ here (no figure is typed except the
                                     Checker's 2.35 / 0.28 m length split of the upper G.B, T-403 verdict 17:55)
  .work/private/t406/t385out/RECON_T385.csv   the T-385 r2 component table (freelancer-derived)     [private]
      rebuilt with research/agents_t385/t385_extract.py + t385_alsenan.py (see the report)
Outputs: research/agents_t406/summary_t406.json (per family before / after / current split, retraced components with
their parts; no freelancer row, dimension or count) and .work/private/t406/ROLLUP_T406.csv (every component) [private].

    python3 -I research/agents_t406/t406_alsenan.py --recon <private>/t406/t385out/RECON_T385.csv [--write]
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import t406_rules as R  # noqa: E402

RES = HERE.parent
PRIVATE = HERE.parents[2] / "private" / "t406"

# merged register: task -> merge commit on the working branch (every one checked as an ancestor by the tests)
MERGED = {
    "T-385": "5f99bfc3", "T-391": "c3fe8ec8", "T-392": "cc3c7f08", "T-394": "e27c5d78", "T-395": "8cf46e7d",
    "T-397": "4492fd59", "T-398": "fe6a238d", "T-401": "23f948bb", "T-402": "1b4c18fc", "T-403": "a72a7282",
}
NEW_FAMILY = "CONC.BOUNDARY_BELOW_NG"
FAMILY_MOVES = {"BW-BAND": NEW_FAMILY, "GB-BOUNDARY": NEW_FAMILY}
# the Checker's split of the upper G.B length term (T-403 verdict 2026-10-31T17:55Z): 2.35 m ENGINE_RIGHT, 0.28 m UNRESOLVED
UPPER_GB_LENGTH_SPLIT_M = (2.35, 0.28)

CONFIRMATIONS = [
    {"task": "T-392", "commit": MERGED["T-392"], "components": ["PL-BASE", "PL-WALLS", "BM-GF"],
     "effect": "no figure moves: the pool lines carry no part of the fourth side B7 / 8D outside the pool "
               "(pool_lines_carry_outside_part false; out-of-pool 1.6684 m = plot boundary wall, T-396 / T-403); "
               "the drawn ring B7 0.666406 m2 x 0.75 billed once by RING-B7 (own minus line 0.000093 m3); O-T385-1 closed"},
    {"task": "T-402", "commit": MERGED["T-402"], "components": ["BM-GF", "BM-1F", "BM-2F"],
     "effect": "no figure moves in the contractual view (research only): of the 27 held beam lines 8 BOUNDED "
               "(width conflicts 5.145035 .. 6.111856 m3 + two marks 0.21196 .. 0.397425), 18 HELD, 1 VALUE proposal "
               "(BM-GF-059 0.549284 m3, a lane I proposal, not in the candidate); the beam HELD parts stay HELD"},
]


def _j(name):
    return json.loads((RES / name).read_text(encoding="utf-8"))


def P(cause, m3, verdict, **kw):
    return {"cause": cause, "m3": round(float(m3), 6), "verdict": verdict, **kw}


def traces():
    """component id -> {source, parts, residual_in_source}: parts read from the merged summaries."""
    out = {}
    s391 = _j("agents_t391/summary_t391.json")
    sl, bm = s391["slab"]["cause_terms_m3"], s391["beams"]["cause_terms_m3"]
    out["GS-SLAB"] = {"source": "T-391", "residual_in_source": s391["slab"]["residual_m3"], "parts": [
        P("his plate covers the beam / column / lift strips the members already own (71.8821 m2 x 0.10)",
          sl["strips_under_other_plate"], "ENGINE_RIGHT"),
        P("own slab panels inside the engine's HELD cell L-41cfb82e (35.6054 m2 x 0.10)", sl["held_cell_panels"], "HELD"),
        P("stair-zone panel the engine routes out of the slab family (8.3723 m2, F2)",
          sl["panels_routed_to_other_family"], "UNRESOLVED"),
        P("his area beyond the whole drawn network (no drawn element)", sl["other_beyond_drawn_network"], "UNTRACED"),
        P("engine vs own on the valued faces (member overlap, court-side and lift-side panels)",
          sl["engine_vs_own_on_valued_faces"], "UNRESOLVED")]}
    out["GB-MAIN"] = {"source": "T-391", "residual_in_source": s391["beams"]["residual_m3"], "parts": [
        P("held runs: his section over the 53.8353 m the engine holds (D-34, D-35 annex, court)", bm["held_runs"], "HELD"),
        P("section on the valued runs: printed D 0.95 exterior / class 0.40 and 0.30 interior vs his one section",
          bm["section_on_valued_runs"], "ENGINE_RIGHT"),
        P("plan / end adjustments of the valued runs (net plan vs width x length)", bm["plan_end_adjustments"], "AGREE"),
        P("length basis: his lump length over the engine's 194.289 m (inside the drawn envelope 193.758 .. 231.908 m)",
          bm["length_basis_untraced"], "UNTRACED")]}
    s394 = _j("agents_t394/summary_t394.json")
    v394 = {"COUNT": ("count by mark against the drawn outlines", "ENGINE_RIGHT"),
            "HEIGHT_BASE": ("base datum of the CB5-line columns (+0.25) vs his one storey height", "ENGINE_RIGHT"),
            "HEIGHT_GLOBAL_DEPTH": ("height: uniform depth against the member's own D_ctrl", "ENGINE_RIGHT"),
            "HEIGHT_JOINT_HEAD": ("height: joint + head A x D_ctrl owned by the column line (beam counterpart once)",
                                  "RULE_DIFFERENCE"),
            "HEIGHT_SPLIT_OPEN": ("height on members whose owner split D_ctrl is open (traced as height, its "
                                  "joint / depth split open)", "RULE_DIFFERENCE"),
            "HELD": ("held members (blank lines): his section x his height", "HELD"),
            "SECTION_CONFLICT": ("C9 section: schedule vs drawn (designer item)", "UNRESOLVED"),
            "SECTION_DIMENSION": ("section dimension", "ENGINE_RIGHT")}
    for fl, cid in (("GF", "CL-GF"), ("1F", "CL-1F")):
        t = s394["terms_engine_minus_freelancer_m3"][fl]
        parts = [P(v394[k][0], t[k], v394[k][1], **({"split_open": True} if k == "HEIGHT_SPLIT_OPEN" else {}))
                 for k in v394 if abs(t.get(k, 0.0)) > 0.0000005]
        out[cid] = {"source": "T-394", "residual_in_source": t["residual"], "parts": parts}
    s401 = _j("agents_t401/summary_t401.json")["freelancer_reconciliation"]
    out["CL-LIFT"] = {"source": "T-401", "residual_in_source": s401["residual_m3"], "parts": [
        P("his ring runs through the four column pieces (0.500 m2 x his depth), columns owned once (R-CONC-OWN-1)",
          s401["columns_in_his_ring_m3"], "ENGINE_RIGHT"),
        P("net ring 1.100 m2 x his uniform depth: pit depth and GF build-up not printed (D-43)",
          s401["net_ring_at_his_height_m3"], "HELD")], "also": "T-394 (same split, e27c5d78)"}
    s395 = _j("agents_t395/summary_t395.json")
    v395 = {"THROUGH_SUPPORT": ("his length runs through the supports; engine runs end at the support face, the joint "
                                "counted once in the column line", "RULE_DIFFERENCE"),
            "RUN_COUNT": ("drawn runs of a mark beyond his rows", "ENGINE_RIGHT"),
            "COUNT_ENGINE_ONLY": ("labelled drawn marks with no row of his (B25 own hand)", "ENGINE_RIGHT"),
            "COUNT_HIS_ONLY": ("his rows with no drawn run", "FREELANCER_RIGHT"),
            "SCOPE": ("dome ring in-bay line valued in the beams; his dome rows are in the stair / dome sheet "
                      "(counterpart: T-398 SD-DOME)", "SCOPE"),
            "SECTION": ("section", "AGREE"),
            "HELD": ("held beam runs: his rows on the runs the engine holds", "HELD"),
            "LENGTH_UNTRACED": ("length beyond the drawn support allowance, not traced", "UNTRACED")}
    for fl in ("GF", "1F", "2F"):
        f = s395["floors"][fl]
        t = f["terms_m3"]
        out["BM-" + fl] = {"source": "T-395", "residual_in_source": f["residual_vs_his_rows_m3"], "parts": [
            P(v395[k][0], t[k], v395[k][1]) for k in v395 if abs(t.get(k, 0.0)) > 0.0000005]}
    s398 = _j("agents_t398/summary_t398.json")
    groups = {"SD-DOME": ("SD-DOMES-AB", "SD-DOME-3"),
              "SD-STAIR": ("SD-ST01-FLIGHTS", "SD-ST01-MS1L", "SD-ST01-LANDINGS", "SD-ST01-TURNS", "SD-D1-STEPS",
                           "SD-D1-WAIST", "SD-ST03-E1", "SD-ST02", "SD-NA")}
    comp = {c["id"]: c for c in s398["components"]}
    for cid, members in groups.items():
        parts = []
        for m in members:
            c = comp[m]
            if c["verdict"] == "UNRESOLVED":
                parts.append(P(f"{m}: {c['element']} (whole contribution unresolved)", c["contribution_m3"], "UNRESOLVED"))
                continue
            if abs(c["named_m3"]) > 0.0000005:
                parts.append(P(f"{m}: {c['element']} traced terms ({c['terms'] or 'whole'})", c["named_m3"],
                               c["verdict"] if c["verdict"] in R.TRACED else "ENGINE_RIGHT"))
            if abs(c["held_named_m3"]) > 0.0000005:
                parts.append(P(f"{m}: {c['element']} held named item", c["held_named_m3"], "HELD"))
            if abs(c["untraced_term_m3"]) > 0.0000005:
                parts.append(P(f"{m}: {c['element']} untraced term", c["untraced_term_m3"], "UNTRACED"))
        out[cid] = {"source": "T-398", "residual_in_source": round(sum(comp[m]["contribution_m3"] for m in members), 6),
                    "parts": parts}
    pp = s398["pump_part"]
    out["PL-PUMP"] = {"source": "T-398", "residual_in_source": pp["residual_m3"], "parts": [
        P("pool pump / plant room: drawn on no sheet (ST, architectural, sanitary searched)", pp["held_named_m3"], "HELD")]}
    s403 = _j("agents_t403/summary_t403.json")["freelancer"]
    ug = s403["upper_gb"]
    c = ug["causes"]
    length = c["length (44.07 vs 42.0) at his section"]
    ok_m, open_m = UPPER_GB_LENGTH_SPLIT_M
    per_m = length / (ok_m - open_m)
    out["GB-BOUNDARY"] = {"source": "T-403", "residual_in_source": round(-ug["his_m3"], 6), "parts": [
        P("upper G.B held in the candidate: engine gross 44.07 x 0.20 x 0.40 at most (net at the columns HELD)",
          -ug["ours_gross_m3"], "HELD"),
        P("width: printed 20 (p.14 A-A) vs his 0.30", c["width (printed 0.20 vs his 0.30)"], "ENGINE_RIGHT"),
        P("depth: printed 40 (p.14 A-A) vs his 0.60", c["depth (printed 0.40 vs his 0.60)"], "ENGINE_RIGHT"),
        P("length: 2.35 m of drawn run beyond his length (Checker own allocation)", per_m * ok_m, "ENGINE_RIGHT"),
        P("length: 0.28 m not traced to a drawn run", -per_m * open_m, "UNRESOLVED")]}
    lb = s403["lower_band_whole"]
    out["BW-BAND"] = {"source": "T-403", "residual_in_source": round(-lb["his_m3"], 6), "parts": [
        P("lower boundary band held (DG-6dd9f1caba1ca77d): owner method A 70.49 m free x 0.20 x 0.60, engine range "
          "5.6392 .. 11.0328, depth pending RFI-S03 / Q-28", -lb["owner_A_m3"], "HELD"),
        P("length: his run 1.21 m longer than the free drawn run (not traced)", lb["owner_A_minus_his_m3"],
          "UNRESOLVED")]}
    return out


def candidate_moves():
    """V3.0.29 -> V3.0.33 (merged Gate B T-397): engine-side changes of the concrete families, read from summary_t397."""
    f = _j("agents_t397/summary_t397.json")["families"]
    out = {}
    for fam, cid in (("CL-GF", "CL-GF"), ("CL-1F", "CL-1F")):
        a, b = f[fam]["v3_0_32"], f[fam]["v3_0_33"]
        withdrawn = round(b["valued"] - a["valued"], 6)
        out[cid] = {"source": "T-397", "parts": [P(
            f"{a['valued_lines'] - b['valued_lines']} CONFLICT column lines withdrawn from valued into ranges "
            f"{b['range_low']} .. {b['range_high']} m3 (schedule vs drawn section, designer item)", withdrawn, "HELD")]}
    a, b = f["BM-GF"]["v3_0_32"], f["BM-GF"]["v3_0_33"]
    out["BM-GF"] = {"source": "T-397", "parts": [P(
        "GF beams B8 / B7 / CB1 span 2 / CB8 re-measured (T-146 GAP 0.002566 + CB8 GAP 0.003406 - DOUBLE 0.002767, "
        "4-dp prints)", round(b["valued"] - a["valued"], 6), "ENGINE_RIGHT")]}
    notes = {
        "GS-SLAB": "held bound of L-41cfb82e 3.929788 .. 3.929788 -> 0 .. 3.560540 m3 (T-391 F1): held engine side "
                   "only, no residual move",
        "CL-LIFT": "one HELD blank line CONC.LIFT_PIT_WALL added (pit depth D-43): the engine side stays 0, no "
                   "residual move",
        "V3.0.29 = V3.0.32": "the concrete families are identical in V3.0.29 .. V3.0.32 (T-391 / T-394 / T-395 / "
                             "T-397 asserted)"}
    return out, notes


def before_from_recon(path):
    rows = list(csv.DictReader(Path(path).open(encoding="utf-8")))
    return [{"id": r["id"], "family": r["family"], "verdict": r["verdict"],
             "contribution_m3": float(r["contribution_m3"]), "traced_m3": float(r["traced_m3"]),
             "held_m3": float(r["held_named_m3"]), "unexplained_m3": float(r["unexplained_m3"])} for r in rows]


def build(before):
    tr = traces()
    by = {c["id"]: c for c in before}
    for cid, t in tr.items():           # each merged trace restates exactly the residual T-385 r2 carried
        if abs(t["residual_in_source"] - by[cid]["contribution_m3"]) > R.TOL:
            raise R.Refused(f"{cid}: merged source residual {t['residual_in_source']} != T-385 r2 "
                            f"{by[cid]['contribution_m3']}")
    moves, notes = candidate_moves()
    rows, fb, fa, fc, tot = R.rollup(before, tr, MERGED, FAMILY_MOVES, moves)
    return rows, fb, fa, fc, tot, notes


def public_summary(rows, fb, fa, fc, tot, notes):
    retraced = [{k: r[k] for k in ("id", "family_before", "family_after", "verdict_before", "contribution_m3",
                                   "before", "after", "trace_source", "trace_commit", "parts", "move",
                                   "move_source", "move_parts", "current")}
                for r in rows if r["trace_source"] or r["move_source"]]
    unchanged = [{"id": r["id"], "family": r["family_after"], "verdict": r["verdict_before"],
                  "class": max(r["before"], key=lambda k: abs(r["before"][k])) if any(r["before"].values()) else "ZERO"}
                 for r in rows if not (r["trace_source"] or r["move_source"])]
    return {"schema": "T406_SUMMARY_V1", "basis": "T-385 r2 (V3.0.29, merge 5f99bfc3) restated with merged traces; "
            "current = + V3.0.33 candidate moves (T-397 Gate B, 4492fd59)", "merged_register": MERGED,
            "family_moves": FAMILY_MOVES, "families_before": fb, "families_after_traces": fa,
            "families_current_v3_0_33": fc, "totals": tot, "retraced_components": retraced,
            "unchanged_components": unchanged, "confirmations": CONFIRMATIONS, "candidate_notes": notes,
            "note": "engine-side figures, residual splits in m3 and verdicts only; the per-component table of the "
                    "unchanged components is in .work/private/t406"}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--recon", default=str(PRIVATE / "t385out" / "RECON_T385.csv"))
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args(argv)
    rows, fb, fa, fc, tot, notes = build(before_from_recon(a.recon))
    pub = public_summary(rows, fb, fa, fc, tot, notes)
    text = json.dumps(pub, indent=1, sort_keys=True, ensure_ascii=False) + "\n"
    if a.write:
        (HERE / "summary_t406.json").write_text(text, encoding="utf-8")
        PRIVATE.mkdir(parents=True, exist_ok=True)
        with (PRIVATE / "ROLLUP_T406.csv").open("w", newline="", encoding="utf-8") as f:
            w = csv.writer(f, lineterminator="\n")
            w.writerow(["id", "family_before", "family_after", "verdict_before", "contribution_m3",
                        "before_traced", "before_held", "before_unexplained", "after_traced", "after_held",
                        "after_unexplained", "move_traced", "move_held", "current_traced", "current_held",
                        "current_unexplained", "source", "commit"])
            for r in rows:
                w.writerow([r["id"], r["family_before"], r["family_after"], r["verdict_before"], r["contribution_m3"],
                            r["before"]["TRACED"], r["before"]["HELD"], r["before"]["UNEXPLAINED"],
                            r["after"]["TRACED"], r["after"]["HELD"], r["after"]["UNEXPLAINED"],
                            r["move"]["TRACED"], r["move"]["HELD"], r["current"]["TRACED"], r["current"]["HELD"],
                            r["current"]["UNEXPLAINED"], r["trace_source"] or "", r["trace_commit"] or ""])
    return pub


if __name__ == "__main__":
    p = main()
    print(json.dumps(p["totals"], indent=1))
    for k in ("families_before", "families_after_traces", "families_current_v3_0_33"):
        print(k)
        for f, v in p[k].items():
            print(f"  {f:26s} res {v['residual_m3']:+11.6f}  traced {v['TRACED']:+11.6f}  held {v['HELD']:+11.6f}  "
                  f"unexpl {v['UNEXPLAINED']:+11.6f}  cause_closes {v['cause_closes']}")
