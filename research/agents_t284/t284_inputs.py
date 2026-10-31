"""T-284: the URBAN_V3032_INPUTS_V1 project inputs of ARCH_TAKEOFF_V3.0.32 (engine.source.arch_v3032), built ONLY from
Checker-merged files, each pinned by sha256 (an edited file stops the build); nothing is typed but the named causes:

  research/agents_t335/FILL_T284_T335.csv  T-335 (MERGED b59fb4db, Verifier 2026-10-29 11:41 UTC Gate A PASS): one row
      per V3.0.21 FIN.CEILING line key (= the V3.0.31 lines: no ceiling code in arch_v3022 .. arch_v3031) + the NEW 1F
      dressing line: before, decor DRAWING-CONFIRMED, owner bulkheads ASSUMED - OWNER-APPROVED apart, held by name;
  research/agents_t335/CANDIDATE_V3021_T335.json  the same task: the 36 FIN.CEILING lines as bound (id, element, state,
      quantity, gross): the stale-binding check of the module compares them with the candidate;
  research/agents_t283/CEILING_LEDGER_R3_EXPORT.json  T-283 (MERGED 6e141df6, Verifier 2026-10-25 05:32 UTC Gate A
      PASS): per face the HELD surfaces by name, the domes (disc, over pieces, S0 intrados beside);
  research/agents_t281/summary.json  T-281 (MERGED 40518c58, Verifier 2026-10-25 05:32 UTC Gate A PASS): per stair the
      soffit true area by method O and D (RULE_DIFFERENCE) and its held rows (beside only: the stair soffit stays HELD).

    python3 -I research/agents_t284/t284_inputs.py [project_id]      # prints the rows and the totals
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
BOUND = ROOT / "research/agents_t335/CANDIDATE_V3021_T335.json"
T283 = ROOT / "research/agents_t283/CEILING_LEDGER_R3_EXPORT.json"
T281 = ROOT / "research/agents_t281/summary.json"
PINS = {FILL: "31cf883848fe2a87e140b44d733731e2bbca2b77d00781705f15976dba9312b0",
        BOUND: "7ac4ca7373c94b0c3573f462f2262b84f700f21c59a12cf41a9dd0fda57e1f8e",
        T283: "fc8873cf2af6fef861cb12de93b04756939bb2906900672452a4dae820103149",
        T281: "8cce8bfc55b4c1a0ce878712073f2ed1c73b74b6ad4f2439e8b30299deca9c6d"}
SOURCES = {
    "T-335": {"task": "T-335", "file": "research/agents_t335/FILL_T284_T335.csv", "sha256": PINS[FILL],
              "merge_commit": "b59fb4db8256a8319614e35b132f2464b3458539",
              "checker_run": "Verifier 2026-10-29 11:41 UTC session_01E6cPndiVBrvsw1yUTJGs7D (Gate A PASS)"},
    "T-283": {"task": "T-283", "file": "research/agents_t283/CEILING_LEDGER_R3_EXPORT.json", "sha256": PINS[T283],
              "merge_commit": "6e141df67e9bc5559ab9fcc677fb4d97d0cb95f0",
              "checker_run": "Verifier 2026-10-25 05:32 UTC session_01GfxzQEADkKAYhzqGtSarUT (Gate A PASS)"},
    "T-281": {"task": "T-281", "file": "research/agents_t281/summary.json", "sha256": PINS[T281],
              "merge_commit": "40518c580ead0c10cb255a68707f64e468e247e6",
              "checker_run": "Verifier 2026-10-25 05:34 UTC session_01GfxzQEADkKAYhzqGtSarUT (Gate A PASS)"},
}
# owner rules of each surface (WORKFLOW_CONTROLS s.4: an ASSUMED — OWNER-APPROVED quantity names its source)
OA_BULKHEAD = "Q-48 A + Q-43 (owner method: free beam edge x 0.15 m decor depth, decor side only, R-CEIL-R3-2)"
OA_PAINT = "Q-57 A modified (6): actual paintable surface = horizontal gypsum + owner bulkhead faces"
# the physical cause of the 1F living group (T-335 s.3 f): one decor figure for two lines whose split is not drawn
GROUP_CAUSE = ("the decor ceiling of the room is one surface over the normal-level part and the double-height part "
               "over the light-well void; the split between the two lines is not established (never pro rata)")
# T-283 prints its pieces to 4 decimals (m2); a decor figure within half a unit of that place of the line's own figure is
# the same piece (the floor piece, nothing deducted): the line's unrounded figure is carried, never a rounding move
LEDGER_HALF_UNIT = 0.5e-4 + 1e-9
STAIR_ELEMENT = {"ST-01": ("GF", "STAIR:ST-01:soffit"), "ST-02": ("GF", "STAIR:ST-02:soffit")}
STAIR_CAUSE = ("true soffit area by method O (plane through the nosings) vs D (waist with kinks): RULE_DIFFERENCE, "
               "no owner rule; curved / winder / junction rows HELD (T-281)")


def _pinned(p):
    b = p.read_bytes()
    if hashlib.sha256(b).hexdigest() != PINS[p]:
        raise SystemExit(f"{p.relative_to(ROOT)}: sha256 differs from the merged file (edited input: stop)")
    return b.decode("utf-8")


def _f(x):
    return None if x in (None, "") else float(x)


def _held_of_record(r):
    """the HELD surfaces of one T-283 face, by name (blank; a figure beside only where the ledger prints one)."""
    out = []
    for s in r["surfaces"]:
        if s["status"] in ("HELD", "NOT SPECIFIED"):
            out.append({"what": s["surface"][:160], "unit": s["unit"], "beside": s["qty"], "why": s["basis"][:200],
                        "status": s["status"]})
    return out


def _held_of_fill(txt):
    """'id|name qty (why); name qty (why)' -> named held items."""
    if not txt:
        return []
    body = txt.split("|", 1)[1] if "|" in txt else txt
    out = []
    for part in body.split("; "):
        part = part.strip()
        if not part:
            continue
        name, _, rest = part.partition(" ")
        qty, _, why = rest.partition(" ")
        try:
            q = float(qty)
        except ValueError:
            q, why = None, rest
        out.append({"what": name, "unit": "m2", "beside": q, "why": why.strip(" ()")[:200], "status": "HELD"})
    return out


def build(project_id=None):
    fill = list(csv.DictReader(_pinned(FILL).splitlines()))
    bound = {ln["line_id"]: ln for ln in json.loads(_pinned(BOUND))["lines"] if ln["item_code"] == "FIN.CEILING"}
    t283 = json.loads(_pinned(T283))
    t281 = json.loads(_pinned(T281))
    recs = {}
    for r in t283["records"]:
        recs.setdefault(r["supersedes_engine"]["room_id"], []).append(r)
    rows = []
    for f in fill:
        keys = [k.strip() for k in f["line_key"].split("+")]
        role = f["role"]
        if role == "EXTERIOR":
            rows.append({"role": "EXTERIOR", "line_ids": keys, "action": "UNCHANGED", "why": f["action"]})
            continue
        els = [e.strip() for e in f["elements"].split("+")]
        room = els[0].split(":")[0]
        rr = recs.get(room) or []
        bl = [bound[k] for k in keys if k in bound]
        held = _held_of_fill(f["held_blank"])
        for r in rr:
            held += _held_of_record(r)
        decor, bulk = _f(f["decor_dc_m2"]), _f(f["bulkhead_aoa_m2"]) or 0.0
        before = _f(f["before_m2"])
        same_piece = (decor is not None and before is not None and len(keys) == 1
                      and abs(decor - before) <= LEDGER_HALF_UNIT)
        if same_piece:    # the ledger confirms the line's own piece to its printed precision: carry the line's figure
            decor = before
        row = {"role": role, "line_ids": keys if keys[0] != "NEW LINE NEEDED" else [], "elements": els,
               "room_id": room, "floor": room.split("-")[0], "before_m2": _f(f["before_m2"]),
               "bound": [{"line_id": b["line_id"], "element_id": b["element_id"], "evidence_state": b["evidence_state"],
                          "measured_net": b["measured_net"]} for b in bl],
               "decor_m2": decor, "decor_status": "DRAWING-CONFIRMED",
               "decor_confirms_line": same_piece,
               "bulkhead_m2": bulk if bulk > 0 else None, "bulkhead_source": OA_BULKHEAD if bulk > 0 else None,
               "paint_m2": (round(decor + bulk, 6) if decor else None),
               "paint_source": OA_PAINT,
               "stair_soffit_beside_m2": _f(f["stair_soffit_dc_m2"]),
               "classes": sorted({r["class"] for r in rr}), "held": held, "source_task": "T-335",
               "held_source_task": "T-283", "action": f["action"][:200]}
        if len(keys) > 1:
            row["group_cause"] = GROUP_CAUSE
        rows.append(row)
    domes = []
    for d in t283["domes"]:
        domes.append({"dome": d["DOME"], "element_id": f"DOME:{d['DOME'].upper()}:intrados", "floor": "1F",
                      "disc_m2": float(d["OPEN_DISC_M2"]), "over_pieces_m2": float(d["OVER_FLOOR_PIECES_M2"]),
                      "over_walls_m2": float(d["OVER_WALLS_OR_OUTSIDE_M2"]), "rooms": d["ROOMS"],
                      "intrados_s0_beside": d["S0_SHELL_INTRADOS_M2"], "held_reason": d["STATUS"],
                      "source_task": "T-283"})
    stairs = []
    for sid, t in sorted(t281["totals"].items()):
        fl, eid = STAIR_ELEMENT[sid]
        lo, hi = sorted((t["true_O_measured"], t["true_D_measured"]))
        stairs.append({"stair": sid, "element_id": eid, "floor": fl, "true_lo_m2": lo, "true_hi_m2": hi,
                       "range_cause": STAIR_CAUSE, "held_rows": t["true_O_held_rows"] + t["true_D_held_rows"],
                       "held_plan_m2": t["held_plan_m2"], "plan_O_m2": t["plan_O"], "source_task": "T-281",
                       "held_reason": "stair soffit finish: T-281 research ledger complete, not verified whole (Checker "
                                      "05:34: two sample flights only); curved / winder rows HELD; no finish line of "
                                      "its own until the soffit is verified whole (ELEMENT_REGISTER 2026-10-25)"})
    return {"schema": "URBAN_V3032_INPUTS_V1", "project_id": project_id,
            "sources": [SOURCES[k] for k in sorted(SOURCES)], "rows": rows, "domes": domes, "stairs": stairs}


if __name__ == "__main__":
    doc = build(sys.argv[1] if len(sys.argv) > 1 else None)
    tot = {"decor": 0.0, "bulkhead": 0.0, "paint": 0.0}
    for r in doc["rows"]:
        if r["role"] == "EXTERIOR":
            print("EXTERIOR", r["line_ids"])
            continue
        print(r["role"], r["room_id"], r["line_ids"], r["before_m2"], "->", r["decor_m2"], "bh", r["bulkhead_m2"],
              "paint", r["paint_m2"], "held", len(r["held"]))
        if r["role"] == "CEILING" or r["role"] == "STAIRWELL":
            tot["decor"] += r["decor_m2"] or 0.0
            tot["bulkhead"] += r["bulkhead_m2"] or 0.0
            tot["paint"] += r["paint_m2"] or 0.0
    print({k: round(v, 6) for k, v in tot.items()})
    print(json.dumps(doc["domes"], indent=1))
    print(json.dumps(doc["stairs"], indent=1))
