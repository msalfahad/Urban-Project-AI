"""T-487: the URBAN_V3053_INPUTS_V1 project inputs of ARCH_TAKEOFF_V3.0.53 (engine.source.arch_v3053), built ONLY from
pinned, merged files (an edited file stops the build):

  research/agents_t453/out/MATERIAL_LEDGER_T453.json   T-453 r2 lintel ledger (MERGED b16f686b, Verifier Gate A
      2026-11-03 08:55): 60 openings in masonry walls, 16 REQUIRED / 42 HELD / 2 FLAGGED (R-T453-4 / R-T453-5); its host
      wall -> MAS.BLOCK line reconciliation (19 released split lines, residual 0);
  research/alsenan_lintels_s8_6/02_LINTEL_SCHEDULE_TRANSCRIPTION.csv   the printed structural LINTEL SCHEDULE (bands
      L1-L5, D per band) and the LINTEL DETAIL 'MIN.40cm' bearing (pinned by T-453 with the same sha256).

Nothing is typed: every quantity is recomputed by arch_v3053 from the printed band and asserted equal to the ledger.
Evidence status (WORKFLOW_CONTROLS s.5) per REQUIRED lintel, from the ledger's own bases: head printed and host wall
VERIFIED -> DRAWING-CONFIRMED (W14 / W15 / W18, re-measured by the Checker); a door head on the owner fallback height
(Q-55 C 2.20 m) -> ASSUMED - OWNER-APPROVED. HELD / FLAGGED -> HELD.

    python3 -I research/agents_t487/t487_inputs.py [project_id]      # prints the inputs summary
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

LEDGER = ROOT / "research/agents_t453/out/MATERIAL_LEDGER_T453.json"
SCHEDULE = ROOT / "research/alsenan_lintels_s8_6/02_LINTEL_SCHEDULE_TRANSCRIPTION.csv"
PINS = {LEDGER: "ad9bceee3bfdbc12218edec2a648e39104f3503bd73342c8ebb451b8394c13f9",
        SCHEDULE: "5d5baf166700d1d5968c5420f37118ae27836f61a2eeae88ed658f40e25936d7"}
# the Checker's own re-measure on T-453 (Verifier 2026-11-03 07:58 / 08:55): faces W14 / W15 / W18, W14 0.195 m3,
# D-GF-06 0.072 m3 / 0.92 m2
CHECKER_REMEASURED = ("W14", "W15", "W18", "D-GF-06")
SOURCES = {
    "T-453": {"task": "T-453", "file": "research/agents_t453/out/MATERIAL_LEDGER_T453.json", "sha256": PINS[LEDGER],
              "merge_commit": "b16f686b",
              "checker_run": "Verifier 2026-11-03T08:55Z Gate A PASS on e4e9742c (session_01E6cPndSU1uDLDo6S42cLVP): "
                             "own p.13 lintel schedule (D L1 0.20 / L2 0.20 / L3 0.30, MIN.40 cm each end), W14 2.4497 "
                             "m DXF; faces W14 0.975 + W15 0.470 + W18 0.260 = 1.705 m2 AGREE; W14 0.195 m3 / 2.44 m2, "
                             "D-GF-06 0.072 m3 / 0.92 m2 AGREE (07:58)"},
}
OPEN_CHECKS = ["bearing availability (MIN 40 cm) at both jambs not measured",
               "jamb against an RC column: connection not approved / not read",
               "FFL-to-structural-top build-up 0.06 m STAND-IN (Q-45 bed maximum) in the masonry-above-head test"]


def _load(p):
    b = p.read_bytes()
    if hashlib.sha256(b).hexdigest() != PINS[p]:
        raise SystemExit(f"{p.name}: sha256 differs from the pinned file (edited input)")
    return b.decode("utf-8")


def schedule():
    rows = list(csv.DictReader(io.StringIO(_load(SCHEDULE))))
    out = [{"row": r["ROW_ID"], "lo_m": round(float(r["WIDTH_LO_CM"]) / 100.0, 6),
            "hi_m": round(float(r["WIDTH_HI_CM"]) / 100.0, 6), "d_m": round(float(r["D_CM"]) / 100.0, 6)}
           for r in rows if r["RECORD"] == "SCHEDULE_ROW"]
    b = [r for r in rows if r["RECORD"] == "DETAIL_READING" and r["ROW_ID"] == "MIN-BEARING"]
    if len(b) != 1 or not out:
        raise SystemExit("the printed schedule needs its rows and one MIN-BEARING detail reading")
    m = re.search(r"(\d+(?:\.\d+)?)\s*cm", b[0]["WIDTH_PRINTED"])
    return {"source": "structural set LINTEL SCHEDULE + LINTEL DETAIL 'MIN.40cm' (S8.6 transcription, pinned)",
            "bearing_m": round(float(m.group(1)) / 100.0, 6), "rows": out}


def _evidence(x):
    if x["decision"] != "REQUIRED":
        return "HELD"
    if x.get("head_basis") == "PRINTED" and x.get("wall_status") == "VERIFIED":
        return "DRAWING-CONFIRMED"
    return "ASSUMED - OWNER-APPROVED"


def lintels():
    d = json.loads(_load(LEDGER))
    if d["lintel_reconciliation"]["summary"]["required_concrete_m3"] != 1.016:
        raise SystemExit("the ledger summary is not the merged 1.016 m3 (stale)")
    w2l = {}
    for r in d["reconciliation"]:
        for w in r["walls"]:
            w2l.setdefault(w, []).append((r["line_id"], r["line_net_m2"]))
    out = []
    for x in d["lintels"]:
        hosts = w2l.get(x["host"]) or []
        if len(hosts) > 1:
            raise SystemExit(f"{x['opening_id']}: host wall {x['host']} in two lines")
        hl, hn = hosts[0] if hosts else (None, None)
        e = {"opening_id": x["opening_id"], "floor": x["floor"], "host_wall": x["host"], "host_line": hl,
             "host_net_m2": hn, "kind": x["kind"], "wall_t_m": x["wall_t_m"], "block_type": x.get("block_type"),
             "width_m": x.get("width_m"), "decision": x["decision"], "schedule_row": x.get("schedule_row"),
             "evidence_status": _evidence(x), "head_basis": x.get("head_basis"),
             "spare_margin_m": x.get("spare_margin_m"),
             "checker_remeasured": x["opening_id"] in CHECKER_REMEASURED, "source_tasks": ["T-453"],
             "basis": (f"T-453 r2 {x.get('rule', 'R-T453-4')}: opening width {x.get('width_m')} m "
                       f"({x.get('width_basis')}), host {x['host']} ({x.get('wall_status')}), fill "
                       f"{x.get('fill_state')}, head basis {x.get('head_basis')}")}
        if x["decision"] == "REQUIRED":
            e.update(length_m=x["length_m"], concrete_m3=x["concrete_m3"], formwork_m2=x["formwork_m2"],
                     face_m2=x["face_m2"], open_checks=list(OPEN_CHECKS),
                     printed_bars={"bottom": x.get("bottom"), "top": x.get("top"), "stirrups": x.get("stirrups")},
                     precast_alternative_beside=x.get("precast_alternative_beside"))
        else:
            e["why"] = x["why"]
        out.append(e)
    return out


def build(project_id=None):
    from engine.source import arch_v3053 as A
    return {"schema": A.INPUTS_SCHEMA, "project_id": project_id, "sources": [SOURCES["T-453"]],
            "schedule": schedule(), "lintels": lintels()}


if __name__ == "__main__":
    doc = build(sys.argv[1] if len(sys.argv) > 1 else None)
    from collections import Counter
    print(json.dumps({"schedule": doc["schedule"], "decisions": Counter(x["decision"] for x in doc["lintels"]),
                      "evidence": Counter(x["evidence_status"] for x in doc["lintels"]),
                      "hosted_on_a_line": sum(1 for x in doc["lintels"] if x["host_line"])}, indent=1))
