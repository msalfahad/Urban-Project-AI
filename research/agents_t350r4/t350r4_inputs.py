"""T-350 r4: the URBAN_V3048_INPUTS_V1 project inputs of ARCH_TAKEOFF_V3.0.48 (engine.source.arch_v3048), built ONLY from
Checker-merged files, each pinned by sha256 (an edited file stops the build). Every figure, status, basis, sensitivity
and held item is READ from those files; typed here are only the zone selection, the action per zone and the one
reconciliation below (named, both ends read from the merged files).

  research/agents_t350r2/FILL_T350R2.csv     T-350 r2 (MERGED 42a99508, Verifier 2026-11-03 06:05 UTC Gate A PASS,
      run session_01E6cPneKXaTiPHWUkotZDvM: own re-measure zone plan 124.649020 m2, excavation 208.163863 m3 AGREE,
      pool 17.775419 AGREE, F-T350R2-1 / -2 CONFIRMED);
  research/agents_t484/summary_t484.json     T-484 (MERGED 12395ea4, Verifier 2026-11-03 09:56 UTC Gate A PASS, run
      session_01E6cPnbiYbetGbSQytw2hyr: necks 5.154 and strap ends 0.179618 VERIFIED by own re-measure; pits backfill
      119.963 .. 128.644 m3 PARTIALLY VERIFIED 6 / 8; F10 + F union ENDORSED).

RECONCILIATION (ext main GB trench, B1-02): r2 printed 1.391722 .. 1.418002 m3 (route-G dL per run, no plot clip);
T-484 closes the same cut to 1.432834 m3 on its own strip (27.919513 m2 less 13.591177 m2 inside the pits, x 0.10),
of which 0.229565 m3 lies beyond the plot line (S06 / D-14, held like every beyond-plot strip). Neither figure was
re-measured by the Checker. The line therefore carries the admissible envelope of the two merged readings, in-plot
T-484 (1.432834 - 0.229565 = 1.203269) .. T-484 with the beyond-plot strip (1.432834), status HELD (the plot clip is a
designer item); the r2 range lies inside it. Never the larger, never a pick.

    python3 -I research/agents_t350r4/t350r4_inputs.py [project_id]      # prints the inputs summary
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

FILL = ROOT / "research/agents_t350r2/FILL_T350R2.csv"
S484 = ROOT / "research/agents_t484/summary_t484.json"
PINS = {FILL: "d09982f6cea0d5c145fd47f404af98efe5379de28bb7040edbaa212ee39424af",
        S484: "a0b952d0d642502480cac9c7c538f5fc37e59ef8b3c3e8a41a4f9c446d638659"}
SOURCES = {
    "T-350r2": {"task": "T-350r2", "file": "research/agents_t350r2/FILL_T350R2.csv", "sha256": PINS[FILL],
                "merge_commit": "42a99508",
                "checker_run": "Verifier 2026-11-03 06:05 UTC session_01E6cPneKXaTiPHWUkotZDvM (Gate A PASS; own "
                               "zone plan 124.649020 m2, excavation 208.163863 m3 AGREE, pool 17.775419 m3 AGREE, "
                               "printed-minimum bound 186.973529 m3; F-T350R2-1 / -2 CONFIRMED)"},
    "T-484": {"task": "T-484", "file": "research/agents_t484/summary_t484.json", "sha256": PINS[S484],
              "merge_commit": "12395ea4",
              "checker_run": "Verifier 2026-11-03 09:56 UTC session_01E6cPnbiYbetGbSQytw2hyr (Gate A PASS; necks "
                             "5.154000 and strap ends 0.179618 m3 VERIFIED by own re-measure; pits backfill PARTIALLY "
                             "VERIFIED 6 / 8; F10 + F union ENDORSED)"},
}
PREFIX = "EW-T350:"
PITS_BACKFILL_STATUS = "PARTIALLY VERIFIED 6 / 8"   # the T-484 verdict's words (blinding, underlay, footings, plan,
#                                                     necks, strap ends; beam solids and ext trench not re-measured)


def _bytes(p):
    b = p.read_bytes()
    if hashlib.sha256(b).hexdigest() != PINS[p]:
        raise SystemExit(f"{p.name}: sha256 differs from the merged file (edited input)")
    return b.decode("utf-8")


def _fill():
    return {r["row_id"]: r for r in csv.DictReader(io.StringIO(_bytes(FILL)))}


def _el(fam, zone):
    return f"{PREFIX}{fam}:{zone}"


def zones():
    f = _fill()
    s = json.loads(_bytes(S484))
    out = []
    p = f["B1-02 EXCAVATION|Z1-PITS-24 (24 neat footing pits)"]
    if p["status"] != "ESTIMATED" or p["proposed_state"] != "VALUED":
        raise SystemExit("pits excavation row is not VALUED / ESTIMATED")
    sens = p["sensitivity"]
    out.append({"action": "VALUE", "family": "B1-02", "zone": "Z1-PITS-24 (24 neat footing pits)",
                "element_id": _el("B1-02", "Z1-PITS-24"), "value": float(p["value_m3"]),
                "evidence_status": p["status"], "basis": p["basis"],
                "sensitivity": sens.split(",printed-minimum")[0].split("; printed-minimum")[0].strip(),
                "printed_minimum_bound": sens[sens.index("printed-minimum"):] + " (F-T350R2-1, Checker 186.973529)",
                "held_items": p["held_beside"], "source_tasks": ["T-350r2"]})
    q = f["B1-02 EXCAVATION|Z1-POOL (pool envelope to the printed -1.50)"]
    if q["status"] != "DRAWING-CONFIRMED" or q["proposed_state"] != "VALUED":
        raise SystemExit("pool excavation row is not VALUED / DRAWING-CONFIRMED")
    out.append({"action": "VALUE", "family": "B1-02", "zone": "Z1-POOL (pool envelope to the printed -1.50)",
                "element_id": _el("B1-02", "Z1-POOL"), "value": float(q["value_m3"]), "evidence_status": q["status"],
                "basis": q["basis"], "held_items": q["held_beside"], "source_tasks": ["T-350r2"]})
    t = f["B1-02 EXCAVATION|Z1-TRENCH-EXT-GB-MAIN (17 runs, cut for the blinding only)"]
    g = s["ext_gb_trench"]
    beyond = round(g["own_strip"]["beyond_plot_m2"] * 0.10, 6)
    hi = g["own_outside_pits_m3"]
    lo = round(hi - beyond, 6)
    if not (lo <= float(t["lo_m3"]) <= float(t["hi_m3"]) <= hi):
        raise SystemExit("the r2 trench range is not inside the T-484 envelope (reconciliation changed)")
    out.append({"action": "RANGE", "family": "B1-02", "zone": "Z1-TRENCH-EXT-GB-MAIN (17 runs, cut for the blinding only)",
                "element_id": _el("B1-02", "Z1-TRENCH-EXT-GB-MAIN"), "low": lo, "high": hi, "evidence_status": "HELD",
                "basis": (f"envelope of the merged readings: T-484 own strip {g['own_strip']['strip_total_m2']} m2 less "
                          f"{g['own_strip']['in_zone_m2']} m2 inside the pits x 0.10 = {hi} m3, of it {beyond} m3 beyond "
                          f"the plot line (low end in plot only); r2 route-G read {t['lo_m3']} .. {t['hi_m3']} inside it"),
                "held_items": f"plot-line clip S06 / D-14 ({beyond} m3); {t['held_beside']}",
                "scenarios_beside": f"r2 {t['lo_m3']} .. {t['hi_m3']} m3; T-484 in plot {lo}, with beyond-plot {hi} m3",
                "source_tasks": ["T-350r2", "T-484"]})
    x = s["f10f"]["excavation_m3"]
    lo, hi = x["all scenarios"]
    out.append({"action": "RANGE", "family": "B1-02", "zone": "Z1-PIT-F10F (open outline 1B1B)",
                "element_id": _el("B1-02", "Z1-PIT-F10F"), "low": lo, "high": hi, "evidence_status": "ESTIMATED",
                "basis": (f"S02 three readings, each one scenario, S01 depth {s['f10f']['depth_m']} m: F10 alone "
                          f"{x['F10 alone']}, F10 + F as a UNION of plans {x['F10 + F (union)']} (T-484 F-T484-4, "
                          f"replaces the r2 sum 8.7675 .. 9.352), drawn outline {x['drawn outline']}"),
                "held_items": f["B1-02 EXCAVATION|Z1-PIT-F10F (open outline 1B1B)"]["held_beside"],
                "scenarios_beside": "; ".join(f"{k} {v[0]} .. {v[1]}" for k, v in x.items() if k != "all scenarios"),
                "source_tasks": ["T-350r2", "T-484"]})
    b = s["pits_backfill"]
    lo, hi = b["backfill_t484_m3"]
    if abs(b["excavation_m3"] - out[0]["value"]) > 1e-9:
        raise SystemExit("T-484 backfill is not on the r2 excavation")
    br = f["B1-03 BACKFILL|Z1-PITS-24"]
    if "11 layers at 0.15" not in br["unit_extra"] or "zone depth 1.57 m" not in br["unit_extra"]:
        raise SystemExit("r2 layer basis changed")
    res = "; ".join(f"{k}: {v} m3" for k, v in b["named_residual_range"].items())
    out.append({"action": "RANGE", "family": "B1-03", "zone": "Z1-PITS-24", "element_id": _el("B1-03", "Z1-PITS-24"),
                "low": lo, "high": hi, "evidence_status": PITS_BACKFILL_STATUS,
                "basis": (f"excavation {b['excavation_m3']} m3 - displacement below EG at actual positions, once: "
                          f"Checker-verified {b['verified_displacement_m3']} (blinding, underlay, footings net, necks, "
                          f"strap ends) + re-measured {b['remeasured_displacement_m3'][0]} .. "
                          f"{b['remeasured_displacement_m3'][1]} (beam solids over the pits, C8 conflict) (T-484)"),
                "held_items": f"{res}; working space HELD; pits beyond the plot line HELD",
                "displacement": {"verified_m3": b["verified_displacement_m3"],
                                 "remeasured_low_m3": b["remeasured_displacement_m3"][0],
                                 "remeasured_high_m3": b["remeasured_displacement_m3"][1], "residual": res},
                "excavation_element_id": _el("B1-02", "Z1-PITS-24"),
                "layers": {"depth_m": 1.57, "lift_m": 0.15, "status": "OWNER-PROVISIONAL lift (owner 2026-11-02 18:00)",
                           "count": 11},
                "sensitivity": br["sensitivity"].replace("[", "").replace("]", ""),
                "source_tasks": ["T-350r2", "T-484"]})
    gaps = {k: r for k, r in f.items() if k.startswith("B1-03 BACKFILL|GAP Z1-PIT-F10F")}
    sc = "; ".join(f"{k.split('[')[1].rstrip(']')} {r['lo_m3']} .. {r['hi_m3']}" for k, r in gaps.items()
                   if "F10 + F" not in k)
    out.append({"action": "ADD_HELD", "family": "B1-03", "zone": "Z1-PIT-F10F (open outline 1B1B)",
                "element_id": _el("B1-03", "Z1-PIT-F10F"), "evidence_status": "HELD",
                "basis": "coverage gap: B1-02 has the zone, B1-03 had no line (r2 PROPOSED_NEW_LINE_HELD)",
                "held_items": ("S02 outline reading (three scenarios); necks C10 / C (Q-31 C); SB1 in F10 + F; the "
                               "F10 + F backfill not restated on the T-484 union"),
                "scenarios_beside": sc + " (before the C10 / C necks)", "source_tasks": ["T-350r2", "T-484"]})
    ff = f["B1-03 BACKFILL|GAP Z1-PIT-FF"]
    out.append({"action": "ADD_HELD", "family": "B1-03", "zone": "Z1-PIT-FF (lift raft and pit)",
                "element_id": _el("B1-03", "Z1-PIT-FF"), "evidence_status": "HELD", "basis": ff["basis"],
                "held_items": ff["held_beside"], "source_tasks": ["T-350r2"]})
    return out


def build(project_id=None):
    from engine.source import arch_v3048 as A
    return {"schema": A.INPUTS_SCHEMA, "project_id": project_id,
            "sources": [SOURCES[k] for k in ("T-350r2", "T-484")], "zones": zones()}


if __name__ == "__main__":
    d = build(sys.argv[1] if len(sys.argv) > 1 else None)
    print(json.dumps([{k: z.get(k) for k in ("action", "family", "element_id", "value", "low", "high",
                                            "evidence_status")} for z in d["zones"]], indent=1))
