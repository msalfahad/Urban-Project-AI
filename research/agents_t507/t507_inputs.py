"""T-507: the URBAN_V3058_INPUTS_V1 document for ARCH_TAKEOFF_V3.0.58 on the development villa, built ONLY from the
merged, Checker-verified T-494 pieces (merge cddfdf7f, Verifier 2026-11-04 08:54 Gate A PASS, own DXF re-measure AGREE:
flat 4.907 m2, upturn 5.194 lm / 1.039 m2), sha-pinned. No drawing is read here: each zone's geometry is restated from
the merged rows file (lengths and areas only, no coordinate) and the engine recomputes the component rows from it with
wp_applicability_rules_v1.component_rows; they must equal the merged rows, row by row (asserted there and here).

One addition to the merged zone dicts, F-C-T494-1: every edge is stated. The ledge zone's slab edge is 0 BY EVIDENCE
(T-494 s.3 partition: the ledge is bounded by the bay face, the void edge and the wall-line continuation it shares with
the open-sky zone; no slab edge), so no row is created and none is silently missing.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ROWS = ROOT / "research" / "agents_t494" / "T494_COMPONENT_ROWS.json"
ROWS_SHA = "b87f8325b4bff8c4eb0214a112fb1cf53c7f6810e1a7f2e9c92c83c5f6bd892a"
SOURCE = {"task": "T-494", "file": "research/agents_t494/T494_COMPONENT_ROWS.json", "sha256": ROWS_SHA,
          "merge_commit": "cddfdf7f74ba93a690ad1fdef81a6a6b6fe45cd8",
          "checker_run": "Verifier 2026-11-04 08:54 UTC (Gate A PASS, commit f53bda97; own DXF re-measure AGREE: flat "
                         "4.907 m2, upturn 5.194 lm / 1.039 m2; HELD window 0.500 lm, ledge 0.640 m2, edges 11.19 lm, "
                         "drains RFI)"}
TEMPLATE = "L-2f7502be6f501baf49b1"      # FIN.WP.ROOF 1F TERRACE-550 (same storey and level +5.50): documents / trade
ROOF_LINES = {"L-d57d2dc2": "L-d57d2dc2fafac8bc72d8", "L-2f7502be": "L-2f7502be6f501baf49b1",
              "L-636fd3ff": "L-636fd3ff1784a12e653b", "L-3e8fe55d": "L-3e8fe55da71851816dd4"}
FLOOR = "1F"                              # the slab top printed +5.50 = the 1F roof-slab level (TERRACE-550 beside)
KINDS = {"north_pier": "SOLID", "south_pier": "SOLID", "southwest_pier": "SOLID", "parapet_face": "PARAPET",
         "parapet_end": "PARAPET", "window_face": "UNDER_WINDOW", "bay_face": "WALL"}
LEDGE_NO_SLAB_EDGE = ("T-494 s.3 partition: the ledge is bounded by the bay outer face (upturn run), the void edge "
                      "(termination) and the 1F wall-line continuation shared with the open-sky zone (0.562437 lm, "
                      "not an edge); no slab edge on the ledge")


def load():
    raw = ROWS.read_bytes()
    if hashlib.sha256(raw).hexdigest() != ROWS_SHA:
        raise SystemExit("T494_COMPONENT_ROWS.json is not the merged file (sha256)")
    return json.loads(raw)


def _geometry(zone_id, rows, exposure, edges):
    """the wp_applicability_rules_v1 zone dict restated from the merged rows of one zone (lengths / areas only)."""
    ev, runs, g = {}, [], {"zone_id": zone_id, "exposure": exposure, "doors": 0, "doorways": [], "carried": [],
                            "outlet_printed": False, "membrane_m2": None}
    for r in rows:
        c = r["component"]
        if c == "FLAT_MEMBRANE":
            g["membrane_m2"] = r["qty"] if r["status"] == "MEASURED" else r["held_bound"]
            ev[c] = r["evidence"]
        elif c == "UPTURN":
            u = {"run": r["run"], "lm": r["length_lm"], "kind": KINDS[r["run"]]}
            if u["kind"] == "UNDER_WINDOW":
                u["sill_above_slab_m"] = None
            runs.append(u)
            ev[r["run"]] = r["evidence"]
        elif c == "SLAB_EDGE_TERMINATION":
            g["open_edge_lm"] = r["held_bound"]
            ev[c] = r["evidence"]
        elif c == "VOID_EDGE_TERMINATION":
            g["void_edge_lm"] = r["held_bound"]
            ev[c] = r["evidence"]
        elif c == "DRAINAGE_FALLS":
            ev[c] = r["evidence"]
        else:
            raise SystemExit(f"{zone_id}: component {c} not expected in the merged rows")
    g["upturn_runs"] = runs
    for k, (v, why) in edges.items():
        g[k] = v
        if why:
            ev["SLAB_EDGE_TERMINATION" if k == "open_edge_lm" else "VOID_EDGE_TERMINATION"] = [why]
    g["evidence"] = ev
    return g


def zones(doc=None):
    d = doc or load()
    by = {}
    for r in d["rows"]:
        by.setdefault(r["zone_id"], []).append(r)
    if sorted(by) != ["POOLCOURT-550", "POOLCOURT-550-LEDGE"]:
        raise SystemExit(f"merged rows name zones {sorted(by)}")
    open_sky = _geometry("POOLCOURT-550", by["POOLCOURT-550"], "EXPOSED", {})
    ledge = _geometry("POOLCOURT-550-LEDGE", by["POOLCOURT-550-LEDGE"], "COVERED_OPEN_SIDE",
                      {"open_edge_lm": (0.0, LEDGE_NO_SLAB_EDGE)})
    out = []
    for g in (open_sky, ledge):
        out.append({"zone_id": g["zone_id"], "floor": FLOOR, "geometry": g,
                    "expected_rows": by[g["zone_id"]], "source_tasks": ["T-494"],
                    "evidence_status": "DRAWING-CONFIRMED",
                    "basis": "T-494 component rows under WP_APPLICABILITY_RULES_V1 (T-486 geometry, Checker AGREE)"})
    return out


def build(project_id):
    d = load()
    ov = []
    for o in d["overlap"]:
        ov.append({"line_id": ROOF_LINES[o["line_id"]], "overlap_m2": o["overlap_m2"],
                   "evidence": f"{o['zone']} {o['level']}: {o['evidence']}"})
    # the default guard re-check at integration (T-212 P2), the V3.0.7 guard inputs unchanged (as T-310 V3.0.57), no
    # new printed record
    sys.path.insert(0, str(ROOT / "research" / "agents_t193"))
    import t193_inputs as L7   # noqa: E402
    g = dict(L7.inputs(project_id)["guard"], new_records=[])
    return {"schema": "URBAN_V3058_INPUTS_V1", "project_id": project_id, "sources": [SOURCE],
            "template_line": TEMPLATE, "zones": zones(d), "overlap": ov, "guard": g}
