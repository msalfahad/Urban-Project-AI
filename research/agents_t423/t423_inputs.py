"""T-423: the URBAN_V3058_INPUTS_V1 project inputs of ARCH_TAKEOFF_V3.0.58 (engine.source.arch_v3058), built ONLY from
Checker-merged files, each pinned by sha256 (an edited file stops the build). Read from those files: every line id,
element, gross, net, dome piece and its print, every face / opening id and the pantry paint line; typed here are only
the entry selection, the line states the candidate of record carries (asserted by the module's binding: a different
candidate refuses), the set-aside names and their reasons:

  research/agents_t335/FILL_T284_T335.csv          T-335 (MERGED b59fb4db, Verifier 2026-10-29 11:41 UTC Gate A PASS):
      per FIN.CEILING line key the before (= gross) and the decor (= the V3.0.32 net), DRAWING-CONFIRMED;
  research/agents_t283/CEILING_LEDGER_R3_EXPORT.json  T-283 (MERGED 6e141df6, Verifier 2026-10-25 05:32 UTC Gate A
      PASS): the dome table, each dome's open disc split over the floor pieces it covers, 4-decimal print per room;
  research/agents_t388/FINDINGS_T388.csv           T-388 (MERGED df170b8d, Checker 2026-10-31 07:51 UTC): F1
      OPENING_OFF_ITS_FACE (opening, face, family, the room's OFF:DOORWAY piece) and F3 PAINT_LINE_ON_FULL_TILE.

    python3 -I research/agents_t423/t423_inputs.py [project_id]      # prints the inputs summary
"""

from __future__ import annotations

import csv
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

FILL = ROOT / "research/agents_t335/FILL_T284_T335.csv"
T283 = ROOT / "research/agents_t283/CEILING_LEDGER_R3_EXPORT.json"
T388 = ROOT / "research/agents_t388/FINDINGS_T388.csv"
PINS = {FILL: "31cf883848fe2a87e140b44d733731e2bbca2b77d00781705f15976dba9312b0",
        T283: "fc8873cf2af6fef861cb12de93b04756939bb2906900672452a4dae820103149",
        T388: "65bf17aed99bab35e0db6565534c9f5d39e1f1a14a018bc71d6eab1517a16828"}
SOURCES = {
    "T-335": {"task": "T-335", "file": "research/agents_t335/FILL_T284_T335.csv", "sha256": PINS[FILL],
              "merge_commit": "b59fb4db8256a8319614e35b132f2464b3458539",
              "checker_run": "Verifier 2026-10-29 11:41 UTC session_01E6cPndiVBrvsw1yUTJGs7D (Gate A PASS)"},
    "T-283": {"task": "T-283", "file": "research/agents_t283/CEILING_LEDGER_R3_EXPORT.json", "sha256": PINS[T283],
              "merge_commit": "6e141df67e9bc5559ab9fcc677fb4d97d0cb95f0",
              "checker_run": "Verifier 2026-10-25 05:32 UTC session_01GfxzQEADkKAYhzqGtSarUT (Gate A PASS)"},
    "T-388": {"task": "T-388", "file": "research/agents_t388/FINDINGS_T388.csv", "sha256": PINS[T388],
              "merge_commit": "df170b8d1edac3b9336d7cae80cb5acbca234454",
              "checker_run": "Checker 2026-10-31 07:51 UTC (Gate A PASS, MERGED df170b8d)"},
}
# the line state the candidate of record carries on each listed ceiling line (V3.0.32 restated them; asserted by the
# module's binding against the candidate, never a value): read on the V3.0.57 lines of this task's chain run
CEILING_STATE = "PROVISIONAL"
# lines the ledger cannot close by id: set aside by name (T-246 s.4, the Lead's T-423 row)
SET_ASIDE = {
    "L-eb3be58fc760b39f0e38": "GF open-plan ceiling 110.922696 -> 101.137092 m2: the 9.785604 m2 gap closes only through "
                              "still-held stair-zone / no-ceiling pieces that do not close by id (stair zone 9.8536 + "
                              "1.7719 vs 9.7856, plus the Checker's 0.777392 slab): a T-284 ledger row by id is needed",
    "L-fc116bb666b184740090": "1F open-plan ceiling parent: held by V3.0.32, no measured_net, nothing to list",
}


def _pinned(p):
    b = p.read_bytes()
    if hashlib.sha256(b).hexdigest() != PINS[p]:
        raise SystemExit(f"{p.relative_to(ROOT)}: sha256 differs from the merged file (edited input: stop)")
    return b.decode("utf-8")


def _dome_prints():
    """room -> (dome, print m2) from the T-283 dome table ('1F-R48AA46 1.2410; ...')."""
    out = {}
    for d in json.loads(_pinned(T283))["domes"]:
        for part in d["ROOMS"].split(";"):
            room, q = part.split()
            if room in out:
                raise SystemExit(f"{room}: under two domes (one piece per line)")
            out[room] = (d["DOME"], float(q), d["STATUS"])
    return out


def ceiling_entries():
    domes = _dome_prints()
    ents = []
    for f in csv.DictReader(_pinned(FILL).splitlines()):
        if f["role"] != "CEILING" or "+" in f["line_key"] or f["line_key"] in SET_ASIDE:
            continue
        room = f["elements"].split(":")[0]
        if room not in domes:
            continue
        gross, net = float(f["before_m2"]), float(f["decor_dc_m2"])
        dome, pr, status = domes[room]
        if abs((gross - net) - pr) > 0.5e-4 + 1e-9:
            raise SystemExit(f"{room}: gap {gross - net:.6f} is not the dome piece {pr} (ledger does not close)")
        ents.append({"action": "LIST_CEILING", "line_id": f["line_key"], "source_tasks": ["T-335", "T-283"],
                     "expect": {"item_code": "FIN.CEILING", "element_id": f["elements"], "unit": "m2",
                                "evidence_state": CEILING_STATE, "gross": gross, "measured_net": net},
                     "items": [{"id": f"DOME:{dome.upper()}:over:{room}", "print_m2": pr,
                                "source": f"T-283 dome table ({dome} dome over {room} {pr} m2)",
                                "note": f"open dome position HELD, never ceiling: {status}"[:300]}]})
    return ents


def findings():
    return list(csv.DictReader(_pinned(T388).splitlines()))


def build(project_id=None, extra=()):
    ents = ceiling_entries() + list(extra)
    used = {e["line_id"] for e in ents}
    return {"schema": "URBAN_V3058_INPUTS_V1", "project_id": project_id,
            "sources": [SOURCES[k] for k in sorted(SOURCES)],
            "set_aside": [{"line_id": k, "why": v} for k, v in SET_ASIDE.items() if k not in used],
            "entries": ents}


if __name__ == "__main__":
    doc = build(sys.argv[1] if len(sys.argv) > 1 else None)
    for e in doc["entries"]:
        print(e["action"], e["line_id"], e["expect"]["element_id"], e["expect"]["gross"], "->",
              e["expect"]["measured_net"], [(i["id"], i["print_m2"]) for i in e["items"]])
    print("set aside:", [s["line_id"] for s in doc["set_aside"]])
