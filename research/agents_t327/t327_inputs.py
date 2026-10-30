"""T-327: the URBAN_V3029_INPUTS_V1 project inputs of ARCH_TAKEOFF_V3.0.29 (engine.source.arch_v3029), built ONLY from
Checker-merged files, each pinned by sha256 (an edited file stops the build); nothing is typed:

  research/agents_t340/FILL_T327_T340.csv     T-340 (MERGED 25c1f52c, Verifier 2026-10-29 16:58 UTC Gate A PASS): the
      sills / thresholds FILL table bound to the candidate line ids (59 carriers: KEEP 23, FILL 27, RETYPE_FILL 5,
      ADD_ROW 1, HOLD 1, ADD_HELD_ROW 2);
  research/agents_t340/CLOSURE_TRACE_T340.csv  the same task: the five closure polygons reconciled to clear width x
      wall t by the wall-end nib and cross-wall terms (residual 0.000000 x 4, 0.000006); D-GF-10 traced on the drawn
      0.797039 gap, which the Checker did NOT adopt (wall line overrun 2.961 mm into the D315 frame jamb: the opening is
      the symbol's 0.800): the excess is re-stated on 0.800 here (nib from the frame end = nib - overrun);
  research/agents_t325/SILL_THRESHOLD_LEDGER_T325.csv  T-325 (MERGED 98f50f0f, Verifier 2026-10-29 04:59 UTC Gate A
      PASS): width, depth, m2, edge m.l, pcs, wet / dry / external material per opening; every FILL row must equal it;
  research/agents_t325/STRIP_FLOOR_OVERLAP_T325.csv  the same task: every strip polygon against the room floor
      polygons of its storey (the five closure polygons matched by floor and area).

Records:
  retype   the five BLOCKED closure strips (D-GF-02, D-GF-10, D-GF-14, D-1F-04 wet -> FIN.MARBLE.THRESHOLD 0.120;
           D-1F-03 dry -> FIN.FLOOR.PORCELAIN 0.150), clear width x wall t, the closure polygon superseded by its trace;
  held     gate D-GF-15: no threshold line, width / wall not established -> one BLANK ARCH.THRESHOLD line;
  carried  every other strip the candidate of record (V3.0.28) already carries, with the ledger's figure: the 23 KEEP
           lines, the 26 window strips V3.0.28 filled (T-326) and its W18 sill line, W17 blank (curved), W03 in the
           V3.0.28 held reveal lines, and A-GF-01 blank: the Lead's T-327 acceptance (ii) keeps the arched set's
           A-GF-01 HELD by name (T-377 held set; arch outline D-45), so T-340's 0.150 fill proposal is NOT applied.

    python3 -I research/agents_t327/t327_inputs.py [project_id]      # prints the counts and m2
"""

from __future__ import annotations

import csv
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
FILL = ROOT / "research/agents_t340/FILL_T327_T340.csv"
TRACE = ROOT / "research/agents_t340/CLOSURE_TRACE_T340.csv"
STL = ROOT / "research/agents_t325/SILL_THRESHOLD_LEDGER_T325.csv"
OVL = ROOT / "research/agents_t325/STRIP_FLOOR_OVERLAP_T325.csv"
PINS = {FILL: "6f9d326e18e62455d06165c6ed9ac234c3f87ca7dfab465aa88ccb746eb33b33",
        TRACE: "24124a433bfa23fa056ce5a37e76d200a229134da33c27457c9d74344a222ee7",
        STL: "ef6f2cb0c0d7619e37f985947a82f1834a948995033af12e73d129bae54e7b68",
        OVL: "bf6606bc39db5cb823839245d6af7d7ad510eb9a9762a45f902579599f3622c3"}
SOURCES = {
    "T-325": {"file": "research/agents_t325/SILL_THRESHOLD_LEDGER_T325.csv",
              "merge_commit": "98f50f0ff72bdf13d2ede3ee9ad5b91d17fbfbb4",
              "checker_run": "Verifier 2026-10-29 04:59 UTC: T-325 Gate A PASS, MERGED 98f50f0f (sills / thresholds "
                             "ledger; the five no-line doors re-located in their BLOCKED closure strips)"},
    "T-340": {"file": "research/agents_t340/FILL_T327_T340.csv",
              "merge_commit": "25c1f52c",
              "checker_run": "Verifier 2026-10-29 16:58 UTC, run session_01E6cPnc3RADugukdnxKWgYJ: T-340 Gate A PASS, "
                             "MERGED 25c1f52c (own re-measure D-1F-03 / D-1F-04 jambs; D-GF-10 0.800 kept: wall "
                             "line overrun 2.961 mm into the D315 frame jamb)"},
}
# T-326 r2 added lines in V3.0.28 (engine.source.arch_v3028.element_id / add_line): the id is a function of the
# project id and the element id only (rule R-T326-1 / T-326, m2), so it is re-derived here, never typed
V3028_ADDED = {"W18": ("1F", "OUT", "SILL", "VALUED"), "W03": ("GF", "OUT", "SILL", "HELD")}
W03_IN = ("GF", "IN", "SILL", "HELD")
D_GF_10_CHECKER_WIDTH = 0.800    # the Checker's T-340 verdict (h): the masonry gap is the D315 symbol's 0.800
TOL = 1e-6


class PinError(ValueError):
    pass


def _read(p):
    b = p.read_bytes()
    h = hashlib.sha256(b).hexdigest()
    if h != PINS[p]:
        raise PinError(f"{p.name}: sha256 {h[:12]} is not the merged {PINS[p][:12]} (edited ledger)")
    return list(csv.DictReader(b.decode("utf-8").splitlines()))


def _f(x):
    return None if x in (None, "") else float(x)


def _last_float(text):
    m = re.findall(r"(-?\d+\.\d+)", str(text or ""))
    return float(m[-1]) if m else None


def _v3028_id(pid, opening, key):
    from engine.source import arch_v3028 as A
    from engine.source import boq_line as BL
    fl, side, grp, st = key
    eid = A.element_id({"floor": fl, "opening": opening, "side": side, "group": grp, "status": st})
    return BL.line_id(pid, A.SILL_CODE, eid, A.RULE_ID, A.RULE_VERSION, A.UNIT)


def build(project_id):
    fill, trace, stl, ovl = (_read(p) for p in (FILL, TRACE, STL, OVL))
    led = {}
    for r in stl:
        led.setdefault(r["opening"], {})[r["component"]] = r
    trc = {r["door"]: r for r in trace}
    sources = [dict(SOURCES[t], task=t, sha256=PINS[FILL if t == "T-340" else STL]) for t in ("T-325", "T-340")]
    carried, retype, held, notes = [], [], [], []
    used_ovl = set()
    for r in fill:
        op, act, code = r["opening"], r["action"], r["item"]
        comps = r["components"].split(";")
        if act == "RETYPE_FILL":
            lr = led[op]["THRESHOLD"]
            w, d = float(lr["width_m"]), float(lr["depth_m"])
            if abs(float(r["m2"]) - float(lr["m2"])) > TOL or abs(w * d - float(lr["m2"])) > TOL or \
                    abs(float(r["ml"]) - w) > TOL or int(r["pcs"]) != 1:
                raise PinError(f"{op}: the FILL row {r['m2']} / {r['ml']} / {r['pcs']} is not the T-325 ledger "
                               f"{lr['m2']} = {w} x {d}")
            t = trc[op]
            poly = float(t["closure_polygon_m2"])
            drawn = float(t["drawn_width_m"])
            overrun = _r6(w - drawn)
            if abs(overrun) > TOL:   # D-GF-10: the Checker kept the symbol's 0.800; the nib starts at the frame end
                if op != "D-GF-10" or abs(w - D_GF_10_CHECKER_WIDTH) > TOL:
                    raise PinError(f"{op}: drawn width {drawn} != ledger {w} and no Checker decision names it")
                nib = _last_float(t["nib"]) - overrun
                cross = _last_float(t["cross_wall"]) or 0.0
                excess = _r6(poly - w * d)
                residual = _r6(excess - (nib + cross) * d)
                cause = (f"TRACED on the Checker's 0.800 (T-340 verdict h): the polygon runs {_r6(nib + cross)} m past "
                         f"the frame jamb (wall-end nib {_r6(nib)} = {_last_float(t['nib'])} less the {overrun} m wall "
                         f"line overrun into the D315 frame + cross wall {cross}): {excess} m2; residual {residual} m2")
            else:
                excess, residual = float(t["polygon_minus_clear_m2"]), float(t["residual_m2"])
                cause = t["cause"]
            cand = [o for o in ovl if o["floor"] == lr["floor"] and not o["openings"] and
                    abs(float(o["strip_m2"]) - poly) <= 1e-4 and o["strip_id"] not in used_ovl]
            if len(cand) != 1:
                raise PinError(f"{op}: {len(cand)} overlap rows match the closure polygon {poly} on {lr['floor']}")
            used_ovl.add(cand[0]["strip_id"])
            wet = lr["material"] == "MARBLE"
            retype.append({"opening": op, "kind": lr["kind"], "floor": lr["floor"], "line_id": r["carrier"],
                           "doorway": "WET" if wet else "DRY", "external": lr["external"] == "True",
                           "target_item": code, "material": r["material"], "material_source": lr["material_source"],
                           "width_m": w, "depth_m": d, "m2": float(lr["m2"]), "ml": float(lr["edge_ml"]),
                           "pcs": int(lr["pcs"]), "closure_polygon_m2": poly,
                           "trace": {"polygon_minus_clear_m2": excess, "residual_m2": residual, "cause": cause,
                                     "jamb_faces": t["jamb_faces"], "symbol": t["symbol"]},
                           "floor_overlap_m2": float(cand[0]["overlap_with_room_floors_m2"]),
                           "overlap_strip": cand[0]["strip_id"], "source_task": "T-340",
                           "note": r["note"]})
        elif act == "ADD_HELD_ROW" and code == "ARCH.THRESHOLD":
            lr = led[op]["THRESHOLD"]
            held.append({"opening": op, "floor": lr["floor"], "item_code": code, "component": "THRESHOLD",
                         "state": lr["state"], "material": r["material"],
                         "basis": "gate: clear width and host wall not established (T-325 UNRESOLVED; T-326 holds its "
                                  "jambs and head); material would be the floor porcelain continued (UP-THR-001) once "
                                  "the strip is drawn", "source_task": "T-340"})
        elif act == "ADD_HELD_ROW" and op == "W03":
            for key in (V3028_ADDED["W03"], W03_IN):
                carried.append({"opening": op, "component": f"{key[1]}_FLOOR_STRIP", "item_code": code,
                                "line_id": _v3028_id(project_id, op, key), "m2": None, "source_task": "T-340"})
        elif act == "ADD_ROW" and op == "W18":
            carried.append({"opening": op, "component": "SILL_OUT", "item_code": code,
                            "line_id": _v3028_id(project_id, op, V3028_ADDED["W18"]), "m2": float(r["m2"]),
                            "source_task": "T-340"})
        elif act == "FILL" and op == "A-GF-01":
            carried.append({"opening": op, "component": "THRESHOLD", "item_code": code, "line_id": r["carrier"],
                            "m2": None, "source_task": "T-340"})
            notes.append(f"{op}: T-340 FILL {r['m2']} m2 not applied (Lead T-327 acceptance ii: arched set held by "
                         f"name, T-377); line stays BLANK")
        elif act in ("KEEP", "FILL", "HOLD"):
            comp = [c for c in comps if c.endswith("_OUT")] or comps
            carried.append({"opening": op, "component": comp[0], "item_code": code, "line_id": r["carrier"],
                            "m2": _f(r["m2"]), "source_task": "T-340"})
        else:
            raise PinError(f"{op}: action {act} {code} not handled")
    return {"schema": "URBAN_V3029_INPUTS_V1", "project_id": project_id, "unit": "m2", "sources": sources,
            "carried": carried, "retype": retype, "sills": [], "held": held, "notes": notes}


def _r6(x):
    return round(float(x), 6)


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    pid = argv[0] if argv else "alsenan-p7757"
    d = build(pid)
    print(json.dumps({"carried": len(d["carried"]), "retype": [(r["opening"], r["target_item"], r["m2"],
                                                                r["trace"]["residual_m2"]) for r in d["retype"]],
                      "retype_m2": round(sum(r["m2"] for r in d["retype"]), 6), "held": [h["opening"] for h in d["held"]],
                      "notes": d["notes"]}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
