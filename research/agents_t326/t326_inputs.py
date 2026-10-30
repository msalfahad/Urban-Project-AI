"""T-326: the URBAN_V3028_INPUTS_V1 project inputs of ARCH_TAKEOFF_V3.0.28 (engine.source.arch_v3028), built ONLY from
the Checker-merged opening reveal ledger (T-313 r2) and the Checker-merged sills / thresholds ledger (T-325), each
file pinned by sha256 (an edited ledger stops the build):

  research/agents_t313/REVEAL_LEDGER_T313.csv     T-313 r2 (MERGED 5f2bf0d5, Verifier 2026-10-29 01:24 UTC Gate A
      PASS): every census opening once per side and component (234 rows): state MEASURED / NONE / HELD / UNRESOLVED,
      m2, m.l, depth, basis, evidence status, the candidate line it is bound to or NO_LINE;
  research/agents_t313/FAMILY_SEARCH_T313.csv     the same task's all-family search (every candidate line that
      carries an opening, with its physical role): the 22 FIN.PLASTER 'door jambs and head' carriers;
  research/agents_t313/DOOR_PLASTER_RECONCILIATION_T313.csv   per FIN.PLASTER door line: the line's own t / w / h
      against the ledger (20 EQUAL, D-GF-01 WITHIN_BOUND, D-GF-07 WITHIN_BOUND at the high end: h 2.50 printed);
  research/agents_t325/SILL_THRESHOLD_LEDGER_T325.csv   T-325 (MERGED 98f50f0f, Verifier 2026-10-29 04:59 UTC Gate A
      PASS): the second, independent read of every external sill / floor-level threshold (must equal T-313 row by
      row, else the build stops) and the T-325 correction of T-313's five 'no line' doors: each DOES carry a BLOCKED
      ARCH.THRESHOLD closure strip = the FLOOR face of that door; the reveal (jambs + head) faces stay unlined.

Records (nothing typed: every figure is read from the merged files):

  fills     the 26 ARCH.WINDOW_REVEAL lines bound to a measured outside sill / floor-level threshold: the line is
            filled with that external surface only (T-313 s.3: the w x 0.20 plan strip includes the 0.10 .. 0.12 m
            frame bed, which is not a finish); W17's line stays as it is (curved, UNRESOLVED);
  narrow    FIN.PLASTER D-GF-07: the line's bound 1.28 .. 1.40 (h class pending 2.20 / 2.50) -> 1.400 m2 at the
            printed 2.50 (T-313 r2 re-measure, Checker-confirmed);
  adds      missing scope by opening and side: window outside jambs + head (valued components in one line), W18's
            external sill (an ARCH.WINDOW_REVEAL line of its own), the five unlined doors' jambs + head (FIN.PLASTER
            'door jambs and head', UP-FIN-PLASTER-001, like the other 22), and one BLANK line per opening / side / item
            for every HELD / UNRESOLVED component that no line carries (never 0);
  carried   every (opening, component) a candidate line already carries: the 22 FIN.PLASTER door lines (jambs and
            head) and the T-325 closure / threshold lines (the door's floor face): a second carrier is refused.

    python3 -I research/agents_t326/t326_inputs.py         # prints the counts and m2
"""

from __future__ import annotations

import csv
import hashlib
import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LED = ROOT / "research/agents_t313/REVEAL_LEDGER_T313.csv"
FAM = ROOT / "research/agents_t313/FAMILY_SEARCH_T313.csv"
DPR = ROOT / "research/agents_t313/DOOR_PLASTER_RECONCILIATION_T313.csv"
STL = ROOT / "research/agents_t325/SILL_THRESHOLD_LEDGER_T325.csv"
PINS = {LED: "2cfa42112aa470c8792d4abe07c9b7471ceecd526974dcd2276dacbff5598730",
        FAM: "6cc2c8f5723d0473c470a0af40be8596441b20463f55103f2b35ca2f24570437",
        DPR: "9c010fc31a762c18cd9b6f0ed7d9b34603e70ea5486cc85a9d5e5c4735a61c63",
        STL: "ef6f2cb0c0d7619e37f985947a82f1834a948995033af12e73d129bae54e7b68"}
SOURCES = {
    "T-313": {"merge_commit": "5f2bf0d5b5b981b13ecc9e58ec07058f3644f7ae",
              "checker_run": "Verifier 2026-10-29 01:24 UTC: T-313 r2 Gate A PASS, MERGED 5f2bf0d5 (D-GF-07 at the "
                             "printed 2.50 and one no-line door re-measured; every family searched)"},
    "T-325": {"merge_commit": "98f50f0ff72bdf13d2ede3ee9ad5b91d17fbfbb4",
              "checker_run": "Verifier 2026-10-29 04:59 UTC: T-325 Gate A PASS, MERGED 98f50f0f (sills / thresholds "
                             "ledger; the five T-313 no-line doors re-located in their BLOCKED closure strips)"},
}
TOL = 1e-9
SILL_COMPONENTS = ("SILL", "THRESHOLD", "FLOOR_STRIP")
KIND_FLOOR = {"GF": "GF", "1F": "1F", "2F": "2F", "RF": "RF"}


class PinError(ValueError):
    pass


def _rows(p):
    h = hashlib.sha256(p.read_bytes()).hexdigest()
    if h != PINS[p]:
        raise PinError(f"{p.relative_to(ROOT)}: sha256 {h[:12]} is not the merged file {PINS[p][:12]} (edited ledger)")
    with p.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def _f(x):
    return float(x) if str(x).strip() != "" else None


def _floor(opening, rooms, fam_floor):
    if fam_floor:
        return fam_floor
    if opening.startswith(("D-", "A-")):
        return opening.split("-")[1]
    room = (rooms or "").split(";")[0]
    for part in room.split("-"):
        if part in KIND_FLOOR:
            return part
    raise PinError(f"{opening}: no floor in the ledger")


def _evidence(r):
    ev = r["evidence"]
    if ev.startswith("ASSUMED"):
        return ev
    return "DRAWING-CONFIRMED" if ev.startswith("DRAWING-CONFIRMED") else ev


def build(project_id=None):
    led, fam, dpr, stl = _rows(LED), _rows(FAM), _rows(DPR), _rows(STL)
    src = [dict(task="T-313", file=str(p.relative_to(ROOT)), sha256=PINS[p], **SOURCES["T-313"])
           for p in (LED, FAM, DPR)] + [dict(task="T-325", file=str(STL.relative_to(ROOT)), sha256=PINS[STL],
                                             **SOURCES["T-325"])]
    fam_floor = {}
    carried = []
    for f in fam:
        fam_floor.setdefault(f["opening"], f["floor"])
        if f["item_code"] == "FIN.PLASTER" and f["role"].startswith("BOUND: door reveal jambs + head"):
            for comp in ("JAMBS", "HEAD"):
                carried.append({"opening": f["opening"], "side": "THROUGH", "component": comp,
                                "line_id": f["line_id"], "item_code": "FIN.PLASTER", "source_task": "T-313",
                                "role": "door reveal jambs + head (UP-FIN-PLASTER-001)"})
    # T-325: the doors' floor face (threshold / closure strip) is carried by its threshold-family line
    t325 = {}
    for s in stl:
        if s["kind"] == "DOOR" and s["component"] == "THRESHOLD" and s["binding"] == "BOUND":
            carried.append({"opening": s["opening"], "side": "THROUGH", "component": "THRESHOLD",
                            "line_id": s["line_id"], "item_code": "ARCH.THRESHOLD / FIN.MARBLE.THRESHOLD / "
                            "FIN.FLOOR.PORCELAIN", "source_task": "T-325",
                            "role": f"the door's floor face: {s['physical_element']} (T-325)"})
        if s["component"] in ("SILL_OUT", "THRESHOLD_OUT"):
            t325[s["opening"]] = s
    by = defaultdict(list)
    for r in led:
        by[r["opening"]].append(r)
    dp = {d["opening"]: d for d in dpr}
    fills, adds, narrow = [], [], []
    for op, rows in sorted(by.items()):
        kind = rows[0]["kind"]
        floor = _floor(op, rows[0]["room"], fam_floor.get(op))
        groups = defaultdict(list)
        for r in rows:
            comp = r["component"]
            if r["line_id"] != "NO_LINE":
                if comp in SILL_COMPONENTS and r["side"] == "OUT" and r["state"] == "MEASURED":
                    s = t325.get(op)
                    if s is None or s["line_id"] != r["line_id"] or abs(float(s["m2"]) - float(r["m2"])) > TOL:
                        raise PinError(f"{op}: the T-325 external sill / threshold does not equal T-313 "
                                       f"({s and s['m2']} vs {r['m2']}, {s and s['line_id']} vs {r['line_id']})")
                    fills.append({"line_id": r["line_id"], "opening": op, "kind": kind, "floor": floor,
                                  "component": comp, "side": "OUT", "m2": float(r["m2"]), "ml": float(r["ml"]),
                                  "depth_m": float(r["depth_m"]), "basis": r["basis"], "evidence": _evidence(r),
                                  "material": s["material"], "source_task": "T-313",
                                  "cross_check": "T-325 SILL_THRESHOLD_LEDGER equal"})
                continue
            if r["state"] == "NONE":
                continue
            if kind == "DOOR":
                if op in dp:      # carried by its FIN.PLASTER line (T-313 bound): not added again
                    continue
                item = "FIN.PLASTER"
            else:
                item = "ARCH.WINDOW_REVEAL" if comp in SILL_COMPONENTS else "ARCH.REVEAL"
            valued = r["state"] == "MEASURED"
            groups[(r["side"], item, valued)].append(r)
        for (side, item, valued), rs in sorted(groups.items()):
            comps = [{"component": r["component"], "m2": _f(r["m2"]) if valued else None,
                      "ml": _f(r["ml"]) if valued else None, "depth_m": _f(r["depth_m"]), "basis": r["basis"],
                      "state": r["state"], "evidence": _evidence(r), "height_status": r["height_status"]}
                     for r in rs]
            adds.append({"opening": op, "kind": kind, "floor": floor, "side": side, "item_code": item,
                         "status": "VALUED" if valued else "HELD", "components": comps,
                         "rooms": rows[0]["room"], "source_task": "T-313"})
    for op in ("D-GF-07",):
        d = dp[op]
        jh = [r for r in by[op] if r["component"] in ("JAMBS", "HEAD")]
        if d["verdict"] != "WITHIN_BOUND" or any(r["height_status"] != "PRINTED" for r in jh if r["component"] == "JAMBS"):
            raise PinError(f"{op}: the narrowing needs a printed height inside the line's bound")
        narrow.append({"line_id": d["line_id"], "opening": op, "before": {"low": float(d["line_low"]),
                       "high": float(d["line_high"])}, "m2": float(d["ledger_m2"]),
                       "components": [{"component": r["component"], "m2": float(r["m2"]), "basis": r["basis"],
                                       "evidence": r["evidence"]} for r in jh],
                       "basis": f"door h {d['ledger_h']} PRINTED (T-313 r2 re-measure): 2 x {d['ledger_t']} x "
                                f"{d['ledger_h']} + {d['ledger_t']} x {d['ledger_w']}", "source_task": "T-313"})
    doc = {"schema": "URBAN_V3028_INPUTS_V1", "project_id": project_id, "unit": "m2", "sources": src,
           "fills": fills, "narrow": narrow, "adds": adds, "carried": carried}
    return doc


def summary(doc):
    s = {"fills": len(doc["fills"]), "fill_m2": round(sum(f["m2"] for f in doc["fills"]), 6),
         "narrow": [(n["opening"], n["before"], n["m2"]) for n in doc["narrow"]],
         "adds_valued": sum(a["status"] == "VALUED" for a in doc["adds"]),
         "adds_held": sum(a["status"] == "HELD" for a in doc["adds"]), "added_m2_by_item": {},
         "carried": len(doc["carried"])}
    for a in doc["adds"]:
        if a["status"] == "VALUED":
            k = a["item_code"]
            s["added_m2_by_item"][k] = round(s["added_m2_by_item"].get(k, 0.0)
                                             + sum(c["m2"] for c in a["components"]), 6)
    return s


if __name__ == "__main__":
    d = build()
    print(json.dumps(summary(d), indent=1))
    sys.exit(0)
