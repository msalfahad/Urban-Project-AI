"""T-266: the URBAN_V3018_INPUTS_V1 of the development villa, built from checker-merged files only, line id by line id:

  research/agents_t290/BASIS_LEDGER_T290.csv   T-290 MERGED 891dbd4d (Verifier 2026-10-25 11:05, Gate A PASS): every
                                                stair / dome concrete line bound to the T-258 r2 pieces, its closable
                                                part by status (2.864463 m3 on 3 held lines + MS2-LD 0.4696 DC)
  research/agents_t258/LEDGER_T258.csv          T-258 r2 MERGED b1b72a50 (Verifier 2026-10-24 13:57, Gate A r2 PASS):
                                                the piece values and statuses (the r2 REVISION, never the r1 2.915089)
  research/agents_t289/BASIS_LEDGER_T289.csv    T-289 MERGED 455c93c4 (Verifier 2026-10-25 09:33): ST-03 row (cited,
                                                booked once there; downgrade DG-5678660edb059395 on V3.0.17)
  research/agents_t286/summary_t286.json        T-286 MERGED e861e390 (Verifier 2026-10-25 09:51): the GF pantry piece
                                                SITE-0a31aaa10796d33a 1.100 m2, DRAWING-CONFIRMED, WET by Q-37 A
  T-278 MERGED 6366b754 (Verifier 2026-10-25 01:28): the 1F arrival landing is owned once by ARCH.SPACE L-428b44ee
                                                (4.9225 m2); its marble (Q-66 B) has no material line: add it as a
                                                material line of that element

Nothing is re-derived here: every figure is read from those files and asserted against them (a stale or edited ledger
stops the build). The em dash of the ledgers' 'ASSUMED — OWNER-APPROVED' is the module's 'ASSUMED - OWNER-APPROVED'.

    python3 -I research/agents_t266/t266_inputs.py > <scratch>/v3018_inputs.json
"""

from __future__ import annotations

import csv
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
T290 = ROOT / "research/agents_t290/BASIS_LEDGER_T290.csv"
T258 = ROOT / "research/agents_t258/LEDGER_T258.csv"
T289 = ROOT / "research/agents_t289/BASIS_LEDGER_T289.csv"
T286 = ROOT / "research/agents_t286/summary_t286.json"
STAIR = "STR.CONC.STAIR"
OA = "ASSUMED - OWNER-APPROVED"
OWNER_Q50 = "Q-50 A cond (owner: round-stair riser 4.50 / 28 where no riser is printed; OWNER_QUESTIONS_ANSWERED.md)"
VERIFIED_BY = {"ST01-MS1-LD": "Checker 2026-10-22 17:18 (0.2304)",
               "ST01-MS1-U": "Checker own 0.9976 2026-10-22 17:18, D-CHK-T180-1 rev2 (T-189 MERGED 3369f30e)"}
# the three held parents T-290 s.4 names (r2 revision) and the line whose pieces are all closable (T-290 s.3)
SPLITS = (("L-7863355dfcb68a681d2d", "ST-01 GF -> 1F main stair (MS1)", "VERIFIED MS1-LD + MS1-U",
           ("ST01-MS1-LD", "ST01-MS1-U"), ("ST01-MS1-L", "ST01-MS1-T", "ST01-MS1-T-SLAB")),
          ("L-b6b0354b7842f0ed6e41", "ST-02 round stair", "OWNER-APPROVED RS-S + RS-LD + RS-A",
           ("ST02-RS-S", "ST02-RS-LD", "ST02-RS-A"), ("ST02-RS-C", "ST02-RS-C-SOFFIT", "ST02-CA", "ST02-2CC")),
          ("L-821032bc04a0b0d02133", "ST-01b lobby flight D1", "DRAWING-CONFIRMED D1 steps",
           ("ST01b-D1-STEPS",), ("ST01b-D1-WAIST",)))
REBASE = ("L-2416e65f053a14199cfc", "ST-01 MS2 half landing (two plates)", ("ST01-MS2-LD-W", "ST01-MS2-LD-E"))
ST03 = "L-061e18cf35a4b6b33d68"
DECLARED_R2 = 2.864463           # T-290 s.4: the r2 closable parts on the three held lines
D1_WIDTH_NOTE = ("Checker 2026-10-25 11:05 named residual: the D1 riser lines are 1.150 long; at 1.150 the steps would be "
                 "0.096107 (-0.004179 m3, -4.2 %); the concrete width is not printed (no RFI, carried as a note)")


def _sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def _rows(p):
    with open(p, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _st(s):
    return s.replace("—", "-").strip()


def sources():
    return [
        {"file": "research/agents_t290/BASIS_LEDGER_T290.csv", "sha256": _sha(T290), "task": "T-290",
         "merge_commit": "891dbd4d", "checker_run": "Verifier 2026-10-25 11:05 UTC (Gate A PASS, own MS2-LD re-measure)"},
        {"file": "research/agents_t258/LEDGER_T258.csv", "sha256": _sha(T258), "task": "T-258",
         "merge_commit": "b1b72a50", "checker_run": "Verifier 2026-10-24 13:57 UTC (Gate A r2 PASS)"},
        {"file": "research/agents_t289/BASIS_LEDGER_T289.csv", "sha256": _sha(T289), "task": "T-289",
         "merge_commit": "455c93c4", "checker_run": "Verifier 2026-10-25 09:33 UTC (Gate A PASS)"},
        {"file": "research/agents_t286/summary_t286.json", "sha256": _sha(T286), "task": "T-286",
         "merge_commit": "e861e390", "checker_run": "Verifier 2026-10-25 09:51 UTC (Gate A PASS)"},
        {"file": "docs/agents/BOARD.md (T-278 verdict, agents/control)", "sha256": "verdict-text", "task": "T-278",
         "merge_commit": "6366b754", "checker_run": "Verifier 2026-10-25 01:28 UTC (Gate A PASS, own re-sum 4.9225)"},
    ]


def pieces():
    return {r["id"]: r for r in _rows(T258)}


def ledger290():
    return {r["line_id"]: r for r in _rows(T290)}


def _piece(pc, pid):
    r = pc[pid]
    if r["cls"] != "CLOSABLE" or r["owner_line"] != "STAIR":
        raise SystemExit(f"T-258 piece {pid} is {r['cls']} / {r['owner_line']}: not a closable stair piece")
    return {"id": pid, "value": round(float(r["value_m3"]), 6), "status": _st(r["evidence"])}


def _held(pc, pid):
    r = pc[pid]
    if r["cls"] == "CLOSABLE":
        raise SystemExit(f"T-258 piece {pid} is closable: it cannot be named held")
    rng = f" (CONFLICT readings {r['low_m3']} .. {r['high_m3']} m3, never summed, never a midpoint)" \
        if r["cls"] == "CONFLICT" else ""
    return {"piece": pid, "item": f"{r['cls']}: {r['blocker'][:220]}{rng}"}


def stair_records(l290=None, pc=None):
    l290 = l290 or ledger290()
    pc = pc or pieces()
    recs = []
    total = 0.0
    for lid, phys, part, closable, held in SPLITS:
        row = l290[lid]
        if row["status"] != "HELD" or row["engine_state"] != "BLOCKED_RFI":
            raise SystemExit(f"T-290 row {lid}: {row['status']} / {row['engine_state']}, expected a HELD blank parent")
        ps = [_piece(pc, p) for p in closable]
        st = {p["status"] for p in ps}
        if len(st) != 1:
            raise SystemExit(f"{lid}: mixed statuses {st} in one part")
        st = st.pop()
        v = round(sum(p["value"] for p in ps), 6)
        if abs(v - float(row["closable_component_m3"])) > 1e-6 or _st(row["closable_by_status"]) != f"{st} {v:.6f}":
            raise SystemExit(f"{lid}: pieces {v} {st} != T-290 closable {row['closable_by_status']}")
        total += v
        p = {"part": part, "status": st, "value": v, "pieces": ps,
             "formula": " + ".join(f"{x['id']} {x['value']:.6f}" for x in ps) + f" = {v:.6f} m3 ({st}; T-258 r2 "
                                                                                     "pieces, T-290 binding)"}
        if st == "VERIFIED":
            p["verified_by"] = "; ".join(f"{x['id']}: {VERIFIED_BY[x['id']]}" for x in ps)
        if st == OA:
            p["owner_source"] = OWNER_Q50
        if lid == "L-821032bc04a0b0d02133":
            p["note"] = D1_WIDTH_NOTE
        recs.append({"kind": "SPLIT", "group": "STAIR_SPLIT", "line_id": lid, "item_code": STAIR,
                     "element_id": row["element_id"], "task": "T-290", "physical_element": phys,
                     "before": {"evidence_state": "BLOCKED_RFI", "measured_net": None},
                     "still_held": [_held(pc, h) for h in held], "parts": [p]})
    if abs(total - DECLARED_R2) > 1e-6:
        raise SystemExit(f"closable parts {total} != the T-258 r2 revision {DECLARED_R2} (never the r1 2.915089)")
    lid, phys, ids = REBASE
    row = l290[lid]
    ps = [_piece(pc, p) for p in ids]
    v = round(sum(p["value"] for p in ps), 6)
    if row["status"] != "DRAWING-CONFIRMED" or abs(v - float(row["drawing_qty_m3"])) > 1e-6:
        raise SystemExit(f"T-290 row {lid}: {row['status']} {row['drawing_qty_m3']} != pieces {v}")
    recs.append({"kind": "REBASE", "group": "STAIR_REBASE", "line_id": lid, "item_code": STAIR,
                 "element_id": row["element_id"], "task": "T-290", "physical_element": phys,
                 "before": {"evidence_state": "BOUNDED_EXPOSURE", "measured_net": None},
                 "status": "DRAWING-CONFIRMED", "value": v, "pieces": ps,
                 "retired": "0.480 high reading (T-111 0.16 x 3.000 m2: the 1.30 x 0.05 strip double count, T-258 s.3)",
                 "formula": " + ".join(f"{x['id']} {x['value']:.6f}" for x in ps) + f" = {v:.6f} m3 (plates 1.495 + "
                            "1.440 m2 x T 16 printed; Checker own 2026-10-25 11:05)"})
    row = l290[ST03]
    if row["status"] != "HELD" or not row["ledger_owner"].startswith("T-289"):
        raise SystemExit(f"T-290 row ST-03: {row['status']} / {row['ledger_owner']}")
    t289 = [r for r in _rows(T289) if r["line_id"] == ST03]
    if len(t289) != 1 or t289[0]["status"] != "HELD":
        raise SystemExit("T-289 row ST03 must be one HELD row")
    recs.append({"kind": "HOLD", "group": "STAIR_HOLD", "line_id": ST03, "item_code": STAIR,
                 "element_id": row["element_id"], "task": "T-289", "physical_element": "ST-03 entrance flight E1",
                 "before": {"evidence_state": "PROVISIONAL", "measured_net": float(row["engine_qty_m3"])},
                 "held_item": "S-9 / G2-w: the E1 waist thickness is not printed",
                 "reasons": ["the line rests on a convention riser 0.165 and waist 0.175 (no printed value: UNSUPPORTED "
                             "BASIS, owner 2026-10-24 23:57 (2)); drawn riser 0.170 (5 over 0.85)",
                             "section B-B draws the waist on ground with no thickness (Checker 2026-10-25 11:05: waist "
                             "concrete HELD, soffit form NOT_APPLICABLE)"],
                 "cited_from": "T-289 BASIS_LEDGER_T289.csv row ST03 (booked once there)",
                 "closable_named": "E1 steps 0.355017 m3 DRAWING-CONFIRMED (T-258 r2 ST03-E1-STEPS), not released here",
                 "resolves": "downgrade DG-5678660edb059395 (V3.0.17 record set: 'left to T-266')"})
    return recs


def build(extra=()):
    return {"schema": "URBAN_V3018_INPUTS_V1", "project": None, "sources": sources(),
            "records": stair_records() + list(extra)}


if __name__ == "__main__":
    json.dump(build(), sys.stdout, ensure_ascii=False, indent=1)
