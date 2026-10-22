"""T-125 comparison tables: MASONRY_CENTRELINE_V2 (alsenan_v2_run.py output, in the scratchpad) vs V1 and the T-103 hand
table, run by run, with the five Q-69 B lengths. Reads the run JSON (outside the repository) and the verified research
tables already in the repository (T-103, T-117); writes CSVs into --outdir. Local metres only.
Usage: python3 -I research/agents_t125/t125_compare.py <scratch>/t125_v2.json --outdir research/agents_t125"""

from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
T117 = ROOT / "research" / "agents_t117" / "ENGINE_VS_HAND_BY_RUN.csv"
T103 = ROOT / "research" / "agents_t103" / "WALLS_BY_FLOOR_THICKNESS.csv"

# why V2 still differs from the hand table, by the T-117 cause letters (general causes, no project constant)
CAUSE = {
    "G": ("T stem: the hand runs the stem to the through-wall centreline (the T piece counted twice); V2 stops on the "
          "face (V1 rule, kept)", "ENGINE_RIGHT"),
    "H": ("45 deg junction: V2 holds the end (max listed) or cuts it square at the drawn end, as V1", "UNRESOLVED"),
    "C29": ("doorway at the free end measured from the drawn face of the wall across (x 17.80 local) to the wall end "
            "(x 18.65): 0.850 m; the hand row takes 0.649", "ENGINE_RIGHT"),
    "I": ("1F doorless 1.30 m opening with head lines drawn (V1 and V2 keep it; T-103's own basis keeps openings in "
          "the run)", "ENGINE_RIGHT"),
    "X": ("both walls drawn through one crossing: the piece is counted once (V1 counted it in both walls; so does "
          "the hand)", "ENGINE_RIGHT"),
    "BAY": ("curved glazed bay: the glass mid circle carried to the wall centreline, 3.747 m arc (+0.169 m curved "
            "masonry stub absorbed once); the hand takes 3.673 m", "UNRESOLVED"),
}


def num(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("run_json")
    ap.add_argument("--outdir", required=True)
    a = ap.parse_args(argv)
    J = json.loads(Path(a.run_json).read_text())
    hand_rows = {r["row_id"]: r for r in csv.DictReader(open(T103))}
    pairs = [r for r in csv.DictReader(open(T117)) if r["floor"] != "floor"]
    out = Path(a.outdir)
    runs_rows, tot = [], defaultdict(lambda: defaultdict(float))
    for fl, f in J["floors"].items():
        v2 = f["v2"]
        by_parent = defaultdict(list)
        for r in v2["runs"]:
            par = {m.split("#")[0] for m in r["members"]} or {r["run_id"]}
            if r["run_id"].startswith("BAY|"):
                par = {r["run_id"][4:]}
            for p in par:
                by_parent[p].append(r)
        for b in v2["by_thickness"]:
            T = tot[(fl, b["family"])]
            for kk in ("arch_run_lm", "physical_blockwork_lm", "openings_lm", "glass_aluminium_lm", "split_out_lm"):
                T[kk] += b[kk] or 0.0
        for b in f["v1_by_thickness"]:
            tot[(fl, b["family"])]["v1_run_lm"] += b["masonry_run_lm"]
        tot[(fl, "GLAZED")]["arch_run_lm"] += v2.get("glazed_lines_lm") or 0.0
        for p in pairs:
            if p["floor"] != fl or not p["engine_piece"] or p["engine_piece"] == "-":
                continue
            pid = p["engine_piece"] if p["engine_piece"].startswith(("ARCBAND", "1F-STUB")) else "WB-" + p["engine_piece"]
            rs = by_parent.get(pid, [])
            hrows = [h.strip() for h in p["hand_rows"].split("+") if h.strip()]
            hand = [hand_rows[h] for h in hrows if h in hand_rows]
            h_run = num(p["hand_run_m"])
            h_open = sum(num(h["opening_gap_widths_m"]) or 0.0 for h in hand) if hand else None
            h_solid = sum(num(h["solid_m"]) or 0.0 for h in hand) if hand else None
            v2_run = sum(r["arch_run_lm"] for r in rs)
            v2_phys = sum(r["physical_blockwork_lm"] for r in rs)
            v2_open = sum(r["openings_lm"] for r in rs)
            v1 = num(p["engine_run_m"]) or 0.0
            d = None if h_run is None else v2_run - h_run
            cause, verdict = "", ""
            if d is not None and abs(d) > 0.05:
                c = p["cause"].split(":")[0]
                if fl == "1F" and pid.endswith("FL0054-FL0055"):
                    cause, verdict = CAUSE["X"]
                elif c.startswith("BAND_ACROSS") and abs(d) <= 0.06:
                    cause, verdict = "split done (" + c + "); the rest is a 45 deg end V2 holds", "UNRESOLVED"
                elif "T stem" in p["cause"] or c == "JUNCTION":
                    cause, verdict = CAUSE["G"]
                elif c.startswith("45 DEG"):
                    cause, verdict = CAUSE["H"]
                elif pid.endswith("FL0038-FL0039"):
                    cause, verdict = CAUSE["C29"]
                elif c == "OPEN_DOORWAY_IN_HAND":
                    cause, verdict = CAUSE["I"]
                elif c == "CURVED_BAY_AS_CHORD":
                    cause, verdict = CAUSE["BAY"]
                elif c.startswith("DOORWAY_AT_FREE_END"):
                    cause, verdict = CAUSE["G"][0] + " (the doorway itself is now in the run)", "ENGINE_RIGHT"
                else:
                    cause, verdict = p["cause"][:160], p["verdict_proposal"]
            if pid.endswith("FL0027-FL0028") and fl == "1F":
                cause = (cause + "; " if cause else "") + CAUSE["X"][0]
                verdict = verdict or CAUSE["X"][1]
            runs_rows.append({
                "floor": fl, "band": pid, "t_m": p["t_m"], "hand_rows": p["hand_rows"],
                "v1_run_m": f"{v1:.3f}", "v2_arch_run_m": f"{v2_run:.3f}", "v2_openings_m": f"{v2_open:.3f}",
                "v2_physical_m": f"{v2_phys:.3f}", "hand_run_m": "" if h_run is None else f"{h_run:.3f}",
                "hand_openings_m": "" if h_open is None else f"{h_open:.3f}",
                "hand_solid_m": "" if h_solid is None else f"{h_solid:.3f}",
                "v2_minus_hand_m": "" if d is None else f"{d:+.3f}", "v2_minus_v1_m": f"{v2_run - v1:+.3f}",
                "v2_runs": " ".join(r["run_id"] for r in rs), "cause_if_over_0.05": cause, "verdict_proposal": verdict})
    keys = list(runs_rows[0])
    with open(out / "V2_VS_V1_VS_HAND_BY_RUN.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, keys)
        w.writeheader()
        w.writerows(runs_rows)
    with open(out / "V2_TOTALS_BY_FLOOR_THICKNESS.csv", "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["floor", "family", "v1_run_m", "v2_arch_run_m", "v2_physical_blockwork_m", "v2_openings_m",
                    "v2_glass_aluminium_m", "v2_split_out_m"])
        for (fl, fm), T in sorted(tot.items()):
            w.writerow([fl, fm, f"{T['v1_run_lm']:.3f}", f"{T['arch_run_lm']:.3f}", f"{T['physical_blockwork_lm']:.3f}",
                        f"{T['openings_lm']:.3f}", f"{T['glass_aluminium_lm']:.3f}", f"{T['split_out_lm']:.3f}"])
    # every stretch V2 judged, every doorway, bay, glazed line and held piece (the evidence of the split)
    with open(out / "V2_STRETCHES_AND_EVIDENCE.csv", "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["floor", "what", "band", "family", "from_m", "to_m", "length_m", "bridged_by_or_evidence", "ref",
                    "in_run"])
        for fl, f in J["floors"].items():
            v2 = f["v2"]
            for s in v2["stretches"]:
                w.writerow([fl, "UNDRAWN_STRETCH", s["wall_id"], s["family"], s["from_m"], s["to_m"], s["length_m"],
                            s["bridged_by"] or "NONE: SPLIT", s.get("ref") or "", s["in_run"]])
            for d in v2["doorways"]:
                w.writerow([fl, "DOORWAY_AT_FREE_END", d["wall_id"], "", "", "", d["gap_m"], d["evidence"],
                            f"leaf/width {d['width_or_leaf_m']} to {d['to_wall']}", True])
            for b in v2["bays"]:
                w.writerow([fl, "CURVED_GLAZED_BAY", b["wall_id"], b["family"], "", "", b["arc_m"], b["basis"],
                            f"chord {b['chord_m']} r {b['r_mid_m']} masonry {b.get('masonry_in_arc_m', 0)}", True])
            for g in v2["glazed_lines"]:
                w.writerow([fl, "GLAZED_LINE", "", "not drawn", "", "", g["length_m"], g["kind"],
                            f"glazing set {g['glazing_set_m']} m", "listed beside the families"])
            for h in v2["held"]:
                w.writerow([fl, "HELD_" + h.get("what", ""), h.get("wall_id") or ",".join(h.get("members", [])),
                            h.get("family", ""), "", "", h.get("max_lm", ""), "", h.get("reason", "")[:120], ""])
    print("wrote", len(runs_rows), "run rows")


if __name__ == "__main__":
    main()
