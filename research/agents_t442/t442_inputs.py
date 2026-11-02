"""T-442: the URBAN_V3042_INPUTS_V1 project inputs of ARCH_TAKEOFF_V3.0.42 (engine.source.arch_v3042), built ONLY from
Checker-merged files, each pinned by sha256 (an edited file stops the build). Every panel id, area, thickness and owner
is READ from those files; typed here are only the line ids the merged files print (bound to the candidate by the
module: a stale binding stops), the new line's element id, the old / new designer item of the cause texts and the
wording of the reasons.

  research/agents_t444/PIECES_T444.json + summary_t444.json   T-444 (MERGED 1fb9dec6, Verifier 2026-11-01T23:58Z Gate A
      PASS on 28fe1fe0, own re-measure of ALL FOUR panels by handle: 35.605376 m2 x printed T 0.10 = 3.560538 m3;
      panel areas VERIFIED, T VERIFIED (T-206)): the held cell L-41cfb82e = panels OWN-007 / 009 / 010 / 047; the shaft
      (pit floor = raft top) and the ring (pit wall) named beside with their owners;
  research/agents_t436/summary_t436.json   T-436 (MERGED c943cabb, Verifier 2026-11-01T19:55Z Gate A PASS on 6b43c5ee,
      own handle read: panel 3.020 x 2.772294 = 8.372 m2, only HIDDEN flight lines inside, no void / pit / base, only a
      column footing below; the panel DRAWING-CONFIRMED, ENGINE_WRONG / FREELANCER_RIGHT): the stair-zone panel OWN-011
      8.372326 m2 of cell SITE-4df8fcd99d130701 (no GS line in the candidate);
  research/agents_t433/summary_t433.json   T-433 (MERGED 304b9af2, Verifier 2026-11-01T19:48Z Gate A PASS on fdf7fd6e,
      F-T433-1 / F-T433-2 checked as stated): item I-04 lists the 13 column CONFLICT lines whose basis text says 'D-63'
      where the designer list item is D-66 (RFI-S20); item I-18 the CL-LIFT pit-wall line held by the pit depth
      (supplier, RFI L-1) and the GF build-up, whose roll-up cause text cites D-43 (the lift tie-beam size);
  research/agents_t401/summary_t401.json   T-401 (MERGED 23f948bb): the pit-wall basis (pit depth + GF build-up, ST p.14).

    python3 -I research/agents_t442/t442_inputs.py [project_id]      # prints the inputs summary
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

T444P = ROOT / "research/agents_t444/PIECES_T444.json"
T444S = ROOT / "research/agents_t444/summary_t444.json"
T436 = ROOT / "research/agents_t436/summary_t436.json"
T433 = ROOT / "research/agents_t433/summary_t433.json"
T401 = ROOT / "research/agents_t401/summary_t401.json"
PINS = {T444P: "69851de04cb6408d82a5975c34c18bff0dbb281118c8d980c360f7b20ea26489",
        T444S: "6220de414b201709f98e639d00e86422f783d7b71cbceef7c2da795c2abf1b78",
        T436: "5f1937248a5cc1531a315348204f0bcce5ed7ddc60c715dc5b04106db6b98d57",
        T433: "9e0e4335074e69692b56678d8d706afe2f05115c43cd9d620b651ac1b87a6daa",
        T401: "b41187080641e5a34e986b2e3a5c13e8f7112428096c28d07f899a93fe969739"}
SOURCES = {
    "T-444": {"task": "T-444", "file": "research/agents_t444/PIECES_T444.json; research/agents_t444/summary_t444.json",
              "sha256": f"{PINS[T444P]}; {PINS[T444S]}", "merge_commit": "1fb9dec6",
              "checker_run": "Verifier 2026-11-01T23:58Z session_01E6cPnbzoeHFrukut5tTajN (Gate A PASS on 28fe1fe0; "
                             "own re-measure of all four panels 35.605376 m2 x T 0.10 = 3.560538 m3; areas and T "
                             "VERIFIED)"},
    "T-436": {"task": "T-436", "file": "research/agents_t436/summary_t436.json", "sha256": PINS[T436],
              "merge_commit": "c943cabb",
              "checker_run": "Verifier 2026-11-01T19:55Z session_01E6cPnciuxNnnDivYkfWWZ6 (Gate A PASS on 6b43c5ee; "
                             "own handle read of the stair-zone panel 3.020 x 2.772294 = 8.372 m2; panel part "
                             "verified, DRAWING-CONFIRMED)"},
    "T-433": {"task": "T-433", "file": "research/agents_t433/summary_t433.json", "sha256": PINS[T433],
              "merge_commit": "304b9af2",
              "checker_run": "Verifier 2026-11-01T19:48Z session_01E6cPneKQttYouw1QkpX3yH (Gate A PASS on fdf7fd6e; "
                             "F-T433-1 / F-T433-2 checked as stated)"},
    "T-401": {"task": "T-401", "file": "research/agents_t401/summary_t401.json", "sha256": PINS[T401],
              "merge_commit": "23f948bb", "checker_run": "Verifier (Gate A PASS, MERGED 23f948bb; pit-wall basis)"},
}
CELL_LINE = "L-41cfb82ed733f4d6e3a5"          # T-444 proposal.line_id (held cell SITE-c1089bdb4cfcdc4a; V3.0.33
#                                               HELD_BOUND: BOUNDED_EXPOSURE 0 .. 3.560540, T-397 = the T-444 m3)
STAIR_CELL = "SITE-4df8fcd99d130701"          # T-436 / T-442 row: the engine cell of the stair-zone panel
STAIR_EXCLUSION = "not counted: the cell is a stair zone (SLAB_STAIR_ZONE, U-C register)"
STAIR_ELEMENT_PREFIX = "GS-T442:GROUND_SLAB:GROUND:"   # the new line's element id = prefix + the cell
LIFT_LINE = "L-684fcad323adc0c8a267"          # T-433 I-18 (CL-LIFT)
D63, D66 = "D-63", "D-66 (RFI-S20)"
D43 = "D-43"
D43_NEW = "the T-401 pit-wall basis (pit depth below the lowest landing: lift supplier, RFI L-1; GF floor build-up " \
          "F.F.L. +1.00 -> slab-on-grade top, D-22 / D-40; ST p.14)"


def _read(p):
    b = p.read_bytes()
    if hashlib.sha256(b).hexdigest() != PINS[p]:
        raise SystemExit(f"{p.name}: sha256 differs from the merged file (edited input)")
    return json.loads(b.decode("utf-8"))


def build(project_id=None, lift_text=True):
    """lift_text False: the CL-LIFT line carries no 'D-43' in the candidate (the cause text lives in the roll-up
    record only): no CAUSE_TEXT row for it (the module would refuse a stale binding)."""
    pieces = _read(T444P)
    s444 = _read(T444S)
    prop = s444["tables"]["proposal"]
    if prop["line_id"] != CELL_LINE or prop["to"]["state"] != "VALUED" or prop["never_zero"] is not True:
        raise SystemExit("T-444 proposal is not the valued cell line")
    panels = [p for p in pieces["pieces"] if p["kind"] == "PANEL" and p["owner_line"] == CELL_LINE]
    ts = {p["t_m"] for p in panels}
    if len(ts) != 1 or ts != {prop["to"]["t_m"]}:
        raise SystemExit("T-444 panels do not share the one printed T")
    t = prop["to"]["t_m"]
    net = s444["tables"]["engine_net_by_kind_m2"]
    owners = prop["out_of_line_owner"]
    beside = [{"kind": k, "area": prop["out_of_line_m2"][k], "owner": owners[k],
               "why": {"SHAFT": "pit floor = raft top (T-401 ST p.14), no slab over the pit void",
                       "RING": "pit-wall band (T-401 P4), held with the pit walls"}[k]}
              for k in sorted(prop["out_of_line_m2"])]
    if any(abs(b["area"] - net[b["kind"]]) > 1e-9 for b in beside):
        raise SystemExit("T-444 out-of-line parts are not the engine net parts")
    cell = {"line_id": CELL_LINE, "cell": "SITE-c1089bdb4cfcdc4a", "floor": "GROUND",
            "expect": {"evidence_state": "BOUNDED_EXPOSURE", "high": prop["to"]["m3"]}, "t": t, "t_status": "VERIFIED",
            "area_status": "VERIFIED", "panels": [{"id": p["face"], "area": p["area_m2"]} for p in panels],
            "declared_m2": prop["to"]["area_m2"], "declared_m3": prop["to"]["m3"], "beside": beside,
            "source_tasks": ["T-444"]}
    s436 = _read(T436)
    sz = s436["stair_zone"]
    if sz["class"]["class"] != "SLAB" or sz["class"]["status"] != "DRAWING-CONFIRMED" or \
            abs(sz["class"]["area_m2"] - sz["area_m2"]) > 1e-12:
        raise SystemExit("T-436 stair zone is not a DRAWING-CONFIRMED slab panel")
    panel = {"cell": STAIR_CELL, "element_id": STAIR_ELEMENT_PREFIX + STAIR_CELL, "floor": "GROUND", "t": t,
             "t_status": "VERIFIED", "area_status": "DRAWING-CONFIRMED", "template_line": CELL_LINE,
             "exclusion_retired": STAIR_EXCLUSION, "panels": [{"id": sz["face"], "area": sz["area_m2"]}],
             "declared_m3": round(sz["area_m2"] * t, 6),
             "physical_element": "slab on grade, panel closed by four ground-beam band faces under / beside the foot "
                                 "of the GF curved flight (flight drawn hidden above the plan)",
             "source_tasks": ["T-436", "T-444"]}
    s433 = _read(T433)
    items = {i["id"]: i for i in s433["items"]}
    texts = [{"line_id": lid, "item_code": "STR.CONC.COLUMN", "old": D63, "new": D66,
              "why": "F-T433-2: the 13 columns whose plan outline and schedule band differ are the designer list's "
                     "D-66 = RFI-S20 (GF 3 + 1F 10); D-63 is the lift columns on the lift raft",
              "source_tasks": ["T-433"]} for lid in items["I-04"]["lines"]]
    if len(texts) != 13:
        raise SystemExit("T-433 I-04 does not list 13 column lines")
    _read(T401)
    if lift_text:
        if items["I-18"]["lines"] != [LIFT_LINE]:
            raise SystemExit("T-433 I-18 is not the CL-LIFT line")
        texts.append({"line_id": LIFT_LINE, "item_code": "STR.CONC.LIFT", "old": D43, "new": D43_NEW,
                      "why": "F-T433-1: D-43 is the GF lift tie-beam size; the pit-wall height is held by the pit "
                             "depth (supplier) and the GF build-up (T-401)", "source_tasks": ["T-433", "T-401"]})
    from engine.source import arch_v3042 as A
    return {"schema": A.INPUTS_SCHEMA, "project_id": project_id,
            "sources": [SOURCES[k] for k in ("T-444", "T-436", "T-433", "T-401")],
            "cells": [cell], "panels": [panel], "texts": texts}


if __name__ == "__main__":
    d = build(sys.argv[1] if len(sys.argv) > 1 else None)
    print(json.dumps({"cells": len(d["cells"]), "panels": len(d["panels"]), "texts": len(d["texts"]),
                      "cell_m3": round(sum(p["area"] for p in d["cells"][0]["panels"]) * d["cells"][0]["t"], 6),
                      "panel_m3": d["panels"][0]["declared_m3"]}, indent=1))
