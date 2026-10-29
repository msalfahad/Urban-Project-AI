"""T-319: the URBAN_V3023_INPUTS_V1 of the development villa, from checker-merged parapet ledgers only:

  T-311 MERGED bd7b8c23 (Verifier 2026-10-28 22:09 UTC, Gate A PASS): PARAPET_RUN_LEDGER_T311.csv (24 runs: chain,
      side, kind, drawn thickness, printed height above the finished roof or its HELD range, block alternative). The
      Checker's own reading confirmed >= 0.30 m RC above the structural slab top on ST p.14 P1 ('30' from the slab top up
      to the top of the upstand cage) and re-measured the whole 2F chain (8 / 8 components, 0.000).
  T-324 MERGED bc5df868 (Verifier 2026-10-29 01:28 UTC, Gate A PASS): COMPONENT_LEDGER_T324.csv TOP_SURFACE rows (each
      run's top = drawn centreline x drawn thickness, with the corrections C1 .. C6 of CORRECTIONS_T324.csv: C5 the
      1.400 m annex boundary-parapet run NE-6x on B34 (F-T321-02) that T-311 missed, C3 / C4 run ends, C1 / C2 / C6
      D-band ranges). The Checker re-measured the annex chain (top 5.997 .. 6.037 m2) and C3 / C4 / C5 from the handles.

Every value below is re-read from the merged files and asserted against the pins (an edited or stale ledger stops the
build). The parapet height of the C5 run is the annex chain's printed 0.50 (T-324 h 0.5, section '50'). No coordinate,
no client text here.

    python3 -I research/agents_t319/t319_inputs.py > <scratch>/v3023_inputs.json
"""

from __future__ import annotations

import csv
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RUNS = ROOT / "research/agents_t311/PARAPET_RUN_LEDGER_T311.csv"
COMP = ROOT / "research/agents_t324/COMPONENT_LEDGER_T324.csv"
CORR = ROOT / "research/agents_t324/CORRECTIONS_T324.csv"
T311_MERGE = "bd7b8c23c9c2737147a0699f191e311eac7b6a46"
T324_MERGE = "bc5df868d3dc042f6928653a92efb6703c3272dc"
T311_CHECKER = ("Verifier 2026-10-28 22:09 UTC (T-311 Gate A PASS, MERGED bd7b8c23; own ST7757.pdf p.14 P1 at 300 dpi: "
                "'30' from the slab top up to the top of the upstand cage = >= 0.30 m RC above the structural slab top "
                "CONFIRMED; 2F chain re-measured 8 / 8 components 0.000; F-T311-C1 lower bound max(0.30, b_edge + margin))")
T324_CHECKER = ("Verifier 2026-10-29 01:28 UTC (T-324 Gate A PASS, MERGED bc5df868; own P7757.dxf re-measure: annex chain "
                "top 5.997 .. 6.037 m2, C3 / C4 / C5 confirmed from the handles; NE-6x 1.400 m on B34 = F-T321-02)")
UPSTAND = 0.30
UPSTAND_SOURCE = ("ST7757 p.14 P1 'TYPICAL DETAIL OF PARAPET SECTION': an RC upstand '30' above the structural slab top, "
                  "'MUST BE MORE THAN THE HEIGHT OF ROOF FINISHING'; P2 / P3 all RC; architectural sections A-A / B-B "
                  "cut every parapet in the slab hatch (T-311 s.2, Checker own read)")
LOWER_RULE = ("lower bound = top x max(0.30, b_edge + margin) (P1 note; Checker F-T311-C1): only the floor top x 0.30 is "
              "established while b_edge (D-39) and the margin (not printed) are HELD; never the printed 0.30 alone as "
              "'the' lower bound")
MATERIAL_ITEM = "Q-65 C (designer: which parapet detail governs each run; material classification HELD)"
B_EDGE_ITEM = "D-39 (roof build-up depth at the parapet edge HELD; T-321 roof layers: no layer thickness printed)"
CHAINS = {  # chain -> (location floor, element id, the roof's WP line that carries the upturn on the inner face)
    "ANNEX": ("GF", "ANNEX_ROOF#PARAPET_RC", "L-d4c73babd2a275c28929"),
    "GF": ("GF", "GF_TERRACE#PARAPET_RC", "L-994b88140f2ea50f1b31"),
    "1F": ("1F", "1F_ROOF#PARAPET_RC", "L-5ce5ba49792e8f9d1f6f"),
    "2F": ("2F", "2F_ROOF#PARAPET_RC", "L-aac1f35e08f85b643692"),
}
PINS = {"runs": 25, "top_lo": 26.836476, "top_hi": 26.972520, "floor": 8.050943, "t311_runs": 24,
        "t311_block_hi": 60.596453}
EXCLUSIVE = [
    "parapet BLOCKWORK above the upstand (MAS.BLOCK, HELD 0 .. 60.596 m2 on the T-311 runs, T-333 binding READY): an "
    "EXCLUSIVE alternative of the same element under Q-65 C: a run is RC OR block above the upstand, never both, and "
    "the two are never added",
]
DOWNSTREAM = [
    "parapet FORMWORK faces of the RC reading (T-311 81.589 .. 202.782 m2, T-332 READY): the formwork family (T-199), "
    "not this line",
    "parapet REINFORCEMENT: HELD (type unkeyed; no rebar change before an approved stage)",
    "parapet outer face (FIN.EXT.FINISH, T-314), inner face above / in the upturn zone, top surface, arrises (T-324 "
    "items): finish families, never concrete",
    "membrane upturn on the inner face: the roof's FIN.WP.ROOF_UPTURN line (IN_LINE, unchanged)",
    "supporting edge beam to its scheduled depth (ends at the slab top): STR.CONC.BEAM, unchanged (R-T311-2)",
]
EXCLUDED = [
    {"what": "1F roof plan: a second 0.200 m strip 7.500 m long outside the outer face of the 1F SE-1 run (F-T311-C2; "
             "layer-5 lines 12C4 / 12C6 / 12C7, end lines 12CA / arc 19A5, cross lines 12E7 / 12E8)",
     "evidence": "own read of P7757.dxf (ab54dd55) this run: its inner line IS the parapet's outer face line 12C7 "
                 "(outer 7.500 / inner 12C9 7.100: run SE-1, centreline 7.300 x 0.200 = top 1.460 m2 = T-311 / "
                 "T-324), its outer line 12C4 lies 0.200 m further out; it bounds no roof on either side (the roof "
                 "lies inside 12C9), carries no inner face and stops at the parapet's outer corner (12C6 on the "
                 "outer line 127F level): a band projecting from the facade, not a parapet run and not a roof "
                 "upstand",
     "owner": "facade frames / projections item (T-172 frames: profile HELD; which frame, SE stair-tower or NW "
              "pool-court, not settled by the plan)",
     "status": "EXCLUDED from STR.CONC.PARAPET by drawing evidence; its material and profile UNKNOWN (frames item), "
               "never 0"},
    {"what": "the 0.200 x 1.300 m divider CEC / CED between the annex roof (+4.30) and the GF terrace (+5.50)",
     "evidence": "T-324 (MERGED): in no T-311 run; faces and top UNKNOWN (no top level printed); its upturn 2 x 1.300 "
                 "m inside both roof WP lines",
     "owner": "not settled (a wall between two roof levels, no detail keyed): named, not in this line",
     "status": "UNKNOWN by name, never 0"},
]


def _sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _rows(p):
    with p.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def _f(x):
    return float(x) if x not in (None, "") else None


def _sources():
    return [{"file": str(RUNS.relative_to(ROOT)), "sha256": _sha(RUNS), "task": "T-311", "merge_commit": T311_MERGE,
             "checker_run": T311_CHECKER},
            {"file": str(COMP.relative_to(ROOT)), "sha256": _sha(COMP), "task": "T-324", "merge_commit": T324_MERGE,
             "checker_run": T324_CHECKER, "also": {str(CORR.relative_to(ROOT)): _sha(CORR)}}]


def build(project_id=None):
    t311 = {(r["chain"], r["side"]): r for r in _rows(RUNS)}
    tops = {}
    for r in _rows(COMP):
        if r["component"] == "TOP_SURFACE":
            ch, side, _x = r["component_id"].split("/")
            tops[(ch, side)] = r
    corr = {}
    for r in _rows(CORR):
        corr.setdefault((r["chain"], r["run"]), []).append(f"{r['id']} ({r['component']}: {r['evidence']}; "
                                                           f"{r['status']})")
    if set(t311) - set(tops):
        raise SystemExit(f"T-311 runs without a T-324 top row: {sorted(set(t311) - set(tops))}")
    chains = []
    for ch, (floor, eid, wp) in CHAINS.items():
        runs = []
        for (c, side), tp in sorted(tops.items()):
            if c != ch:
                continue
            base = t311.get((c, side))
            tl, th = float(tp["qty_lo"]), float(tp["qty_hi"])
            if base is not None:
                t = float(base["t_m"])
                h = _f(base["h_above_finish_m"])
                hl, hh = (h, h) if h is not None else (float(base["h_held_lo"]), float(base["h_held_hi"]))
                hsrc = ("printed height above the finished roof (T-311 run ledger: sections A-A / B-B, elevations)"
                        if h is not None else "printed elevations disagree / not printed for this run end (T-311 / "
                                              "T-172): HELD range")
                blk = [float(base["block_m2_lo"]), float(base["block_m2_hi"])]
                note = None
                task = "T-311"
            else:      # T-324 C5: a run T-311 missed (annex B34 to the divider), t and h of the annex chain
                t = 0.200
                hl = hh = 0.500
                hsrc = "printed height above the finished roof of the annex chain (section '50'), as T-324 C5"
                blk = None
                note = ("run found after T-311 (T-324 C5): not in the merged block-alternative ledger; the blockwork "
                        "binding owes it (by the T-311 rule: centreline x (h - 0.30))")
                task = "T-324"
            kind = base["kind"] if base else "STRAIGHT"
            if any(x.startswith("C3 ") for x in corr.get((c, side), [])):
                kind = "STRAIGHT (T-324 C3: drawn straight at roof level; T-311 carried the floor-outline arc)"
            runs.append({"run": side, "kind": kind, "t_m": t,
                         "centreline_lo_m": round(tl / t, 6), "centreline_hi_m": round(th / t, 6),
                         "top_lo_m2": tl, "top_hi_m2": th, "h_lo_m": hl, "h_hi_m": hh, "h_source": hsrc,
                         "h_status": "HELD" if hh > hl else None,
                         "geometry_status": "HELD (D-band / run-end range, T-324)" if th > tl else
                         tp["status"], "material": "HELD", "block_alt_m2": blk, "block_alt_note": note,
                         "source_task": task, "corrections": corr.get((c, side), [])})
        chains.append({"chain": ch, "floor": floor, "roof_level": (t311.get((ch, runs[0]["run"])) or
                                                                    {"roof_level": "+4.30"})["roof_level"],
                       "element_id": eid, "roof_wp_line_id": wp, "task": "T-324", "material_status": "HELD",
                       "material_item": MATERIAL_ITEM, "b_edge_item": B_EDGE_ITEM, "runs": runs,
                       "exclusive": EXCLUSIVE, "downstream": DOWNSTREAM})
    allr = [u for c in chains for u in c["runs"]]
    pins = {"runs": len(allr), "top_lo": round(sum(u["top_lo_m2"] for u in allr), 6),
            "top_hi": round(sum(u["top_hi_m2"] for u in allr), 6),
            "floor": round(sum(u["top_lo_m2"] for u in allr) * UPSTAND, 6), "t311_runs": len(t311),
            "t311_block_hi": round(sum(float(r["block_m2_hi"]) for r in t311.values()), 6)}
    if pins != PINS:
        raise SystemExit(f"the merged ledgers are not the pinned ones: {pins} != {PINS}")
    declared = {"lines": len(chains), "top_lo_m2": sum(u["top_lo_m2"] for u in allr),
                "top_hi_m2": sum(u["top_hi_m2"] for u in allr),
                "floor_m3": sum(u["top_lo_m2"] * UPSTAND for u in allr),
                "all_rc_printed_lo_m3": sum(u["top_lo_m2"] * u["h_lo_m"] for u in allr),
                "all_rc_printed_hi_m3": sum(u["top_hi_m2"] * u["h_hi_m"] for u in allr)}
    sys.path.insert(0, str(ROOT / "research/agents_t193"))
    import t193_inputs as L7   # noqa: E402  (the V3.0.7 guard inputs, unchanged, as V3.0.8 .. V3.0.22)
    g = dict(L7.inputs(project_id)["guard"], new_records=[])
    return {"schema": "URBAN_V3023_INPUTS_V1", "project": project_id, "sources": _sources(),
            "upstand": {"floor_m": UPSTAND, "source": UPSTAND_SOURCE, "status": "DRAWING-CONFIRMED",
                        "checker_run": T311_CHECKER, "lower_bound_rule": LOWER_RULE},
            "chains": chains, "excluded": EXCLUDED, "declared": declared, "guard": g}


if __name__ == "__main__":
    json.dump(build(sys.argv[1] if len(sys.argv) > 1 else None), sys.stdout, ensure_ascii=False, indent=1)
