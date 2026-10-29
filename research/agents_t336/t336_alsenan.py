"""T-336 Alsenan (development villa): the Checker-verified T-303 wet-area waterproofing inventory and the T-309 pool
membrane / screed ledger bound to the CANDIDATE OF RECORD ARCH_TAKEOFF_V3.0.21 WP line ids by physical face and
physical door (R-T336-WP-BIND-1), with the FILL table lane I (T-310) consumes unchanged. Research only: no engine
module, candidate line or released line changes.

    python3 -I research/agents_t336/t336_alsenan.py --extract <run>/v3021   # writes CANDIDATE_V3021_WP.json
    python3 -I research/agents_t336/t336_alsenan.py --write                 # writes the ledger files
    python3 -I research/agents_t336/t336_alsenan.py --check                 # rebuilds in memory, compares bytes

Inputs (committed, merged): research/agents_t303 (inventory core + adapter, imported read-only; its EXTRACT path is
pointed at the V3.0.21 extract in memory only), research/agents_t301/CANDIDATE_V3017_WP.json (the V3.0.17 WP lines
T-303 was verified on), research/agents_t309/POOL_MEMBRANE_LINES_T309.json, and CANDIDATE_V3021_WP.json (extracted
here from an own V3.0.21 run: ids, item codes, element ids, units, states, quantities; no coordinates, no names).
Drawing readings added by this task are cited by DXF entity handle on Drive 'Alsenan chalet project' /
P7757_DXF_COMPRESSED.zip (P7757.dxf sha256 ab54dd55..).
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
for p in (HERE, ROOT, ROOT / "research" / "agents_t301", ROOT / "research" / "agents_t303"):
    sys.path.insert(0, str(p))
import t336_wp_binding as B  # noqa: E402

CAND21 = HERE / "CANDIDATE_V3021_WP.json"
CAND17 = ROOT / "research" / "agents_t301" / "CANDIDATE_V3017_WP.json"
POOL = ROOT / "research" / "agents_t309" / "POOL_MEMBRANE_LINES_T309.json"
OUT = {"rebind": HERE / "LINE_REBIND_T336.csv", "pieces": HERE / "WP_PIECES_T336.csv",
       "fill": HERE / "FILL_T310_T336.csv", "summary": HERE / "summary.json"}
WET, POOLF = "WP.WET_AREA", "WP.POOL_TANK"
DXF = "Drive 'Alsenan chalet project' / P7757_DXF_COMPRESSED.zip, P7757.dxf"
T303V = "T-303 MERGED 1d3f69b0 (Checker 2026-10-26 01:06, own re-measure)"
KIND = {"FIN.WP.FLOOR": "FLOOR", "FIN.WP.WALL_UPTURN": "WALL_UPTURN", "FIN.WP.DOORWAY": "THRESHOLD",
        "FIN.WP.DOORWAY_TRANSITION": "TRANSITION", "FIN.WP.DOORWAY_TRANSITION_NR": "TRANSITION_NR",
        "FIN.WP.PENETRATION": "PENETRATION", "FIN.WP.TERMINATION": "TERMINATION",
        "FIN.WP.MEMBRANE_ROLLS": "MEMBRANE_ROLLS"}
HELD_STATES = ("BOUNDED_EXPOSURE", "BLOCKED_RFI")

# ---- drawing readings (rule 3 / rule 4 / thresholds): each a correction of a candidate line or a NEW row ------------
UPTURN_1F12 = B.upturn_m2(8.700, doors=[0.800], windows=[(0.500, 0.84)])        # (1.58, 7.9): W18 sill above 0.20
CORRECT = {
    "FIN.WP.WALL_UPTURN[m2]/1F-12/WALLS": (
        UPTURN_1F12[0],
        "walls only (Q-35 C) 8.700 - 0.800 door = 7.900 lm x 0.20; the 0.500 east opening is window W18 (glazing "
        "lines C36 .. C39 / C3A / C3E, no leaf), sill 0.84 printed (NW elevation DIMENSION 2EEC / 2EFA, T-144): sill "
        "above the 0.20 upturn -> not deducted (rule 3); " + T303V),
    "FIN.WP.DOORWAY[m2]/DOOR:D-GF-14/THRESHOLD_FLOOR": (
        B.threshold_m2(0.800, 0.150),
        DXF + ": loose swing arc 334 (r 0.690); wall-face lines 2E5 / 2E6 end at the jambs (gap 0.800) and 2E7 / 2E8 "
        "on the other face (wall depth 0.150), frame lines 32B .. 32F / 330 / 331: 0.800 x 0.150 (own read T-336; "
        "T-303 UNRESOLVED closure reading 0.218846 not drawn)"),
    "FIN.WP.DOORWAY[m2]/DOOR:D-1F-04/THRESHOLD_FLOOR": (
        B.threshold_m2(0.800, 0.150),
        DXF + ": insert C2E block D315 rot 90; wall lines C1B / C1D (faces 0.150 apart) end at the south jamb and C1C "
              "/ C1E start at the north jamb, gap 0.800: 0.800 x 0.150 (own read T-336; T-303 UNRESOLVED closure "
              "reading 0.131977 not drawn)"),
    "FIN.WP.FLOOR[m2]/GF-07/FLOOR": (
        B.floor_net_m2(4.500 * 3.000, [0.900 * 0.050]),
        DXF + ": printed box DIMENSION 5E1 4500 / 5D5 3000 runs to the wall faces 158 (north) / A6 (south), AE / B3; "
              "column 2FAE (LWPOLYLINE, S-COL.BON, with hatch 2FAD and cross 2FAC) is 0.250 deep in the 0.200 north "
              "wall (faces 158 / 15A) and stands 0.050 proud of face 158 over 0.900 from face AE: 13.500 - 0.045 = "
              "13.455 (rule 4; T-286 MERGED closes the same box 13.455; O-T303-01 ruled)"),
}
PANTRY_DOOR = ("DOOR:D-GF-07-PANTRY",
               DXF + ": insert 33E block D120 rot 180 (leaf into the pantry); wall-face lines 158 / 159 (pantry side) "
                     "and 15A / 15B stop at the jambs, gap 1.000; faces 0.200 apart: 1.000 x 0.200")
PANTRY_THRESHOLD = B.threshold_m2(1.000, 0.200)
# windows in wet-room walls whose sill is printed on no sheet (T-144 s.5 'W05-07', 'W08', 'W19-23', 'W28'; widths and
# rooms T-128 r3 ROOMS_T128_R3.csv). Owner method: the upturn runs on the whole wall boundary less doors only (Q-30
# kitchen example, Q-35 C) -> the line keeps its quantity as ASSUMED - OWNER-APPROVED; drawing method: the part under
# the window depends on the unprinted sill (rule 3) -> HELD 0 .. width x 0.20 beside it.
WIN_NO_SILL = {"GF-06": [("W08", 1.50)], "GF-16": [("W05-07", 0.60)], "GF-10": [("W05-07", 0.60)],
               "GF-13": [("W05-07", 0.60)], "1F-07": [("W19-23", 0.60)], "1F-08": [("W19-23", 0.60)],
               "1F-02": [("W19-23", 0.60)], "1F-03": [("W19-23", 0.60)], "1F-09": [("W19-23", 0.60)],
               "2F-02": [("W28", 0.60)]}
Q30 = ("OWNER METHOD (OWNER_QUESTIONS_ANSWERED Q-30 kitchen example: 0.20 upturn on the whole wall boundary; Q-35 C: "
       "doors only left out) keeps the part under the window")
W18_TERM = ("window W18 (east wall of 1F-12): sill 0.84 printed (DIMENSION 2EEC / 2EFA, T-144) above the 0.20 upturn; "
            "the upturn runs under the window, the membrane has no edge there (rule 3; " + T303V + ")")


def _sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def _jload(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


# ------------------------------------------------------------------------------------------------ extraction
def extract(run_dir):
    """the waterproofing lines of a V3.0.21 run, same fields as the T-301 extract."""
    import engine.source.trade_completeness_v1 as TC
    p = Path(run_dir) / "V3_0_21_BOQ_LINES.json"
    raw = json.loads(p.read_text(encoding="utf-8"))
    lines = raw["lines"] if isinstance(raw, dict) else raw
    out = []
    for ln in lines:
        if TC.line_trade(ln) != "WATERPROOFING" and "WP" not in (ln.get("item_code") or ""):
            continue
        inp = (ln.get("calculation") or {}).get("inputs") or {}
        f = inp.get("foundation_wp_v3015") or {}
        out.append({"line_id": ln["line_id"], "item_code": ln["item_code"], "unit": ln["unit"],
                    "evidence_state": ln["evidence_state"], "measured_net": ln.get("measured_net"),
                    "floor": (ln.get("location") or {}).get("floor"),
                    "element_id": (ln.get("location") or {}).get("element_id"), "trade": ln.get("trade"),
                    "subtrade": ln.get("subtrade"), "record_element": f.get("element"),
                    "components": [{"id": c["id"], "value": c.get("value")} for c in f.get("components") or []]})
    out.sort(key=lambda x: (x["item_code"], x["unit"], x["line_id"]))
    return {"source": f"{p.name} (ARCH_TAKEOFF_V3.0.21 run)", "lines": out}


# ------------------------------------------------------------------------------------------------ rebind
def rebind():
    a = {x["line_id"]: x for x in _jload(CAND17)["lines"]}
    b = {x["line_id"]: x for x in _jload(CAND21)["lines"]}
    rows = []
    f = ("item_code", "unit", "evidence_state", "measured_net", "element_id", "floor", "components")
    for lid in sorted(set(a) | set(b)):
        x, y = a.get(lid), b.get(lid)
        v = "ADDED" if x is None else ("REMOVED" if y is None else
                                       ("SAME" if all(x[k] == y[k] for k in f) else "CHANGED"))
        z = y or x
        rows.append({"line_id": lid, "item_code": z["item_code"], "unit": z["unit"],
                     "element_id": z["element_id"], "v3017_state": x and x["evidence_state"],
                     "v3017_qty": x and x["measured_net"], "v3021_state": y and y["evidence_state"],
                     "v3021_qty": y and y["measured_net"], "verdict": v})
    return rows


# ------------------------------------------------------------------------------------------------ binding
def _t303():
    import t303_alsenan as A
    A.EXTRACT = CAND21                      # in memory only: the T-303 adapter reads the V3.0.21 WP lines
    return A


def build():
    A = _t303()
    els, lines, lk, rep = A.family_report(A.WET)
    by_id = {x["line_id"]: x for x in lines}
    cand_ids = {x["line_id"] for x in _jload(CAND21)["lines"]}
    carried = {}
    for lid, ks in lk.items():
        for k in ks:
            carried.setdefault(k, []).append(lid)
    room_of_face = {f: r for r, (_i, f) in A.ROOMS.items()}
    pieces = []
    for e in sorted(els, key=lambda x: (x["item_code"], x["element"], x["face"])):
        key = f"{e['item_code']}[{e['unit']}]/{e['element']}/{e['face']}"
        kind = KIND[e["item_code"]]
        room = e["owner"]
        ls = sorted(carried.get(key, []))
        inv = e["qty"]
        if kind == "TRANSITION" and len(ls) != 1:
            # rule 2: one transition per physical door; 2 room-side lines -> both replaced; none -> a door row
            for lid in ls:
                ln = by_id[lid]
                pieces.append(B.piece(f"{key}|RETIRED:{lid}", WET, kind, e["unit"], room, None, "HELD", line_id=lid,
                                      action="REPLACE_BY_DOOR_ROW", before=ln["measured_net"],
                                      before_state=ln["evidence_state"],
                                      evidence="Q-35 C one transition per physical door; " + T303V,
                                      note=f"room-side line {ln['element_id']}: the door is carried twice"))
            pieces.append(B.piece(key, WET, kind, e["unit"], room, None, "HELD",
                                  new_row=B.door_row_key(e["item_code"], e["unit"], e["element"][5:], e["face"]),
                                  action="ADD_ROW", evidence="Q-35 C; transition detail not printed (as the 11 "
                                                             "BOUNDED lines)",
                                  note=("replaces the two room-side lines " + " / ".join(ls)) if ls else
                                  ("pantry door (Q-37 A): no doorway, transition or number line" if
                                   e["element"] == PANTRY_DOOR[0] else
                                   "door with a doorway line and no transition line")))
            continue
        if len(ls) > 1:
            raise B.BindingError(f"{key} carried by {ls}")
        if not ls:                                   # MISSING in T-303: the pantry's door, drain, open side
            if key.startswith("FIN.WP.DOORWAY[m2]/" + PANTRY_DOOR[0]):
                pieces.append(B.piece(key, WET, kind, e["unit"], room, PANTRY_THRESHOLD, "DRAWING-CONFIRMED",
                                      new_row=key, action="ADD_ROW", evidence=PANTRY_DOOR[1],
                                      note="Q-37 A pantry wet; T-303 MISSING (depth not tabled) -> read"))
            elif kind == "TRANSITION_NR" and e["element"] == PANTRY_DOOR[0]:
                pieces.append(B.piece(key, WET, kind, e["unit"], room, 1, "DRAWING-CONFIRMED", new_row=key,
                                      action="ADD_ROW", evidence=PANTRY_DOOR[1] + " (one physical door)"))
            else:
                pieces.append(B.piece(key, WET, kind, e["unit"], room, None, "HELD", new_row=key, action="ADD_ROW",
                                      evidence="T-303 MISSING (Q-37 A)", note=e.get("note")))
            continue
        lid = ls[0]
        ln = by_id[lid]
        before, st = ln["measured_net"], ln["evidence_state"]
        if key in CORRECT:
            q, ev = CORRECT[key]
            pieces.append(B.piece(key, WET, kind, e["unit"], room, q, "DRAWING-CONFIRMED", line_id=lid,
                                  action="CORRECT", before=before, before_state=st, evidence=ev,
                                  note=f"ENGINE_WRONG {round(before - q, 6):+} {e['unit']}"))
        elif kind == "MEMBRANE_ROLLS":
            pieces.append(B.piece(key, WET, kind, e["unit"], room, before, "PROCUREMENT", line_id=lid, before=before,
                                  before_state=st, evidence="procurement count (Q-49 / UP-WP-005), not a face"))
        elif st in HELD_STATES or before is None:
            pieces.append(B.piece(key, WET, kind, e["unit"], room, None, "HELD", line_id=lid, before=before,
                                  before_state=st, evidence="line held in the candidate", note=e.get("note")))
        elif kind == "WALL_UPTURN" and room in WIN_NO_SILL:
            w = WIN_NO_SILL[room]
            hp = round(sum(x for _n, x in w) * B.UPTURN_M, 6)
            pieces.append(B.piece(key, WET, kind, e["unit"], room, before, "ASSUMED - OWNER-APPROVED", line_id=lid,
                                  before=before, before_state=st,
                                  evidence=f"T-303 inventory {inv} ({e['source']}); " + Q30,
                                  bound=f"DRAWING METHOD: {round(before - hp, 6)} determinate + HELD 0 .. {hp} under "
                                        + " / ".join(f"{n} {x:.2f}" for n, x in w) + " (sill printed on no sheet, "
                                        "T-144 s.5; rule 3)"))
        else:
            res = None if inv is None else round(before - inv, 6)
            pieces.append(B.piece(key, WET, kind, e["unit"], room, before, "DRAWING-CONFIRMED", line_id=lid,
                                  before=before, before_state=st,
                                  evidence=f"T-303 inventory {inv} ({e['source']}); " + T303V,
                                  note=None if res is None or abs(res) <= B.TOL else
                                  f"reading residual {res:+} {e['unit']} named in T-303 (drawn gap vs hand table)"))
    # lines the inventory does not carry (terminations on W18, the core W.C. 'other' face)
    for lid, ks in sorted(lk.items()):
        if not all(k.split("/", 1)[1].startswith("?/") for k in ks):
            continue
        ln = by_id[lid]
        base = (ln["element_id"] or "").split(":", 1)[0]
        room = room_of_face.get(base, base)
        key = f"{ln['item_code']}[{ln['unit']}]/LINE:{lid}"
        kind = KIND[ln["item_code"]]
        if kind == "TERMINATION" and room == "1F-12" and "glazing" in (ln["element_id"] or ""):
            pieces.append(B.piece(key, WET, kind, ln["unit"], room, None, "NOT_APPLICABLE_WITH_EVIDENCE",
                                  line_id=lid, action="SET_NOT_APPLICABLE", before=ln["measured_net"],
                                  before_state=ln["evidence_state"], evidence=W18_TERM,
                                  note=f"engine element {ln['element_id']}"))
        else:
            pieces.append(B.piece(key, WET, kind, ln["unit"], room, None, "HELD", line_id=lid,
                                  before=ln["measured_net"], before_state=ln["evidence_state"],
                                  evidence="T-303 finding (5): T-128 r3 reads that face as wall; not re-measured "
                                           "by a Checker",
                                  note=f"engine element {ln['element_id']}: register-only, stays held by name"))
    # pool / tank (T-309 MERGED 834ada3e; tank T-303 NOT_APPLICABLE)
    for x in _jload(POOL):
        kind = "POOL_MEMBRANE" if x["unit"] == "m2" else "POOL_SCREED"
        fn = "; membrane FUNCTION HELD (S8.2: printed '5cm INSULATION MEMBRANE.')" if kind == "POOL_MEMBRANE" else ""
        pieces.append(B.piece(x["key"], POOLF, kind, x["unit"], "POOL-1", x["quantity"], "DRAWING-CONFIRMED",
                              new_row=x["key"], action="ADD_ROW", evidence="T-309 MERGED 834ada3e: " + x["source"],
                              bound=f"+ HELD {x['held_part_bound'][0]} .. {x['held_part_bound'][1]} {x['unit']} "
                                    "(0.15 upstand above the deck, C9)" + fn))
    pieces.append(B.piece("WP.POOL_TANK.TANK_MEMBRANE[m2]/TANK-01/ALL_FACES", POOLF, "TANK", "m2", "TANK-01", None,
                          "NOT_APPLICABLE_WITH_EVIDENCE", new_row="WP.POOL_TANK.TANK_MEMBRANE[m2]/TANK-01/ALL_FACES",
                          action="SET_NOT_APPLICABLE",
                          evidence="'ST7757 dxf.dxf' TEXT 1A85 'WATER TANK PLACE' only: no tank base, wall or WP layer "
                                   "(S8.4, T-204; " + T303V + "); register only, no row"))
    B.validate_pieces(pieces, cand_ids)
    rows = B.fill_rows(pieces)
    B.check_fill(rows)
    return pieces, rows, lines, rep


def _csv(rows, cols):
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=cols, lineterminator="\n")
    w.writeheader()
    for r in rows:
        w.writerow({k: ("" if r.get(k) is None else (f"{r[k]:.6f}" if isinstance(r[k], float) else r[k]))
                    for k in cols})
    return buf.getvalue()


def outputs():
    rb = rebind()
    pieces, rows, lines, rep = build()
    wp21 = _jload(CAND21)["lines"]
    t = B.totals(rows, "m2", families=(WET,))
    changed = [r for r in rows if r["action"] != "KEEP"]
    summ = {
        "schema": B.SCHEMA, "rule": B.RULE_ID,
        "inputs": {"CANDIDATE_V3021_WP.json": _sha(CAND21)[:8], "CANDIDATE_V3017_WP.json": _sha(CAND17)[:8],
                   "POOL_MEMBRANE_LINES_T309.json": _sha(POOL)[:8]},
        "candidate_wp_lines": len(wp21),
        "rebind": {v: sum(1 for r in rb if r["verdict"] == v) for v in ("SAME", "CHANGED", "ADDED", "REMOVED")},
        "wet_area_lines": len(lines), "pieces": len(pieces),
        "actions": {a: sum(1 for r in rows if r["action"] == a) for a in B.ACTIONS},
        "statuses": {s: sum(1 for r in rows if r["after_status"] == s) for s in B.STATUSES},
        "wet_m2_by_kind": t,
        "upturn_under_unprinted_sills": {
            "rooms": sorted(WIN_NO_SILL), "lm": round(sum(x for w in WIN_NO_SILL.values() for _n, x in w), 6),
            "m2_owner_method_kept": round(sum(x for w in WIN_NO_SILL.values() for _n, x in w) * B.UPTURN_M, 6),
            "drawing_method": "HELD 0 .. that m2 (rule 3, sill printed on no sheet)"},
        "pool": {r["unit"]: r["after"] for r in rows if r["family"] == POOLF and r["after"] is not None},
        "changes": [{"row": r["row"], "piece": r["piece"], "action": r["action"], "before": r["before"],
                     "after": r["after"], "change": r["change"], "status": r["after_status"]} for r in changed],
    }
    pc = ["key", "family", "kind", "unit", "room", "qty", "bound", "status", "line_id", "new_row", "action", "evidence",
          "note"]
    fc = ["row", "piece", "family", "kind", "unit", "room", "action", "before_state", "before", "after_status", "after",
          "change", "bound", "evidence", "note"]
    rc = ["line_id", "item_code", "unit", "element_id", "v3017_state", "v3017_qty", "v3021_state", "v3021_qty",
          "verdict"]
    return {"rebind": _csv(rb, rc), "pieces": _csv(pieces, pc), "fill": _csv(rows, fc),
            "summary": json.dumps(summ, indent=1, sort_keys=True) + "\n"}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--extract", help="a V3.0.21 run directory (writes CANDIDATE_V3021_WP.json)")
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args(argv)
    if a.extract:
        CAND21.write_text(json.dumps(extract(a.extract), indent=1, sort_keys=True) + "\n", encoding="utf-8")
    if a.write or a.check:
        out = outputs()
        bad = []
        for k, txt in out.items():
            if a.write:
                OUT[k].write_text(txt, encoding="utf-8")
            elif OUT[k].read_text(encoding="utf-8") != txt:
                bad.append(OUT[k].name)
        if bad:
            print("DIFFERS:", ", ".join(bad))
            return 1
        print(json.loads(out["summary"])["actions"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
