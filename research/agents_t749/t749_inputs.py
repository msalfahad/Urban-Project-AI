"""T-749 (lane I, hub H1P, OWNER RULE PAINT 2026-11-12): the live after-state of every line the PAINT RULE WIRING
package wires, built from Checker-merged ledgers only (sha256-pinned below) as mapped by the merged T-748 readiness
(R6, hub H1P), checked against the candidate of record ARCH_TAKEOFF_V3.0.76 (T-736, merge 166fb1fd; line index of record
research/agents_t736/out/LINE_INDEX_V3_0_76.json). Nothing here opens a drawing or forms a quantity: every figure is a
merged ledger's.

  PAINT_RESTATE  T-740 (UP-FIN-PAINT-002 1.0.0, paint = plaster of the same face - band - tiled): the 5 room paint lines
                 T-748 maps CHANGE (GF_01, GF_08, 1F_11, 1F_13, 2F_01) restated HELD at the rule range; KEEP / released
                 lines untouched (GF_15 released 56.0131 stays: rule 56.01315 is ledger rounding, released lines move
                 only by a Checker record).
  RETURN_LM      T-746 (Lead ruling reading B): the 30 door / arch / gate RETURN_PAINT m2 lines leave the paint area
                 (EXCLUDED_WITH_REASON EDGE_AS_LM) and each opening's painted edge becomes its own FIN.PAINT.EDGE lm line
                 (27 HELD bounded, 3 HELD blank), bound to the return's plaster line.
  EXT_EDGE       T-747 openings + T-751 closures: exterior window edges by opening id (arched heads developed, T-751
                 ENGINE_RIGHT over the rectangles) and exterior corner groups by T-747 host key (T-751 parapet-end and
                 plinth closures, the stop-end bound kept, the NO_HOST mouth arris 1.40 m on its own line) as
                 FIN.EXT.PAINT.EDGE lm lines, HELD (the exterior paint face is HELD: its render host waits T-314 r3),
                 bound to the floor's facade line (the only live exterior finish line of that floor), the face key named.
                 Exterior DOOR edges are the same physical reveal as the T-746 return line of that door (asserted equal
                 per door id): counted once, under the return line (never a second line).

    python3 -I research/agents_t749/t749_inputs.py [--check] [--write]
"""
from __future__ import annotations

import csv
import hashlib
import json
import sys
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
OUT = HERE / "out" / "T749_ENTRIES.json"
SCHEMA = "URBAN_T749_ENTRIES_V1"
INDEX = "research/agents_t736/out/LINE_INDEX_V3_0_76.json"
T740 = "research/agents_t740/out/T740_PAINT_RULE.json"
T746 = "research/agents_t746/out/T746_PAINT_EDGES.json"
T747 = "research/agents_t747/out/T747_EXT_PAINT.json"
T751 = "research/agents_t751/out/T751_EDGE_BOUNDS.json"
T748 = "research/agents_t748/out/T748_ROWS.csv"
D = Decimal

PINS = {INDEX: "184e0e3c5cf381af", T740: "3918f7e4382728ea", T746: "96595bd2593afd3e", T747: "3c1566a9a08435d7",
        T751: "1964beae4be55fbb", T748: "f403d34bac956720"}
SOURCES = {
    "T-740": {"file": T740, "merge_commit": "0f0e0cd0",
              "checker_run": "Verifier 2026-11-12T14:29Z Gate A PASS on 49c6df83 (session_01E6cPnbViRyHAG6PKLTn5pu)"},
    "T-746": {"file": T746, "merge_commit": "faf8afcd",
              "checker_run": "Verifier 2026-11-12T17:53Z Gate A PASS on 3311d39d (lock checker)"},
    "T-747": {"file": T747, "merge_commit": "a3f62c52",
              "checker_run": "Verifier 2026-11-12T20:20Z Gate A PASS on cd76987b (session_01E6cPndH1Fg2P9McVaB87YY)"},
    "T-751": {"file": T751, "merge_commit": "79766703",
              "checker_run": "Verifier 2026-11-12T22:05Z Gate A PASS on 34520aeb (lock checker, PARTIALLY VERIFIED)"},
    "T-748": {"file": T748, "merge_commit": "071dc837",
              "checker_run": "Verifier 2026-11-12T17:58Z Gate A PASS on aa09b3ff (lock checker)"},
}
FLOOR_FACADE = {"GF": "L-b05f70c92405dbcfbe62", "1F": "L-8bb83e16cc7b104ab88b", "2F": "L-d52c4f763b19aedf8b8b"}
CHANGE_N, RETURN_N = 5, 30


class InputsError(ValueError):
    pass


def sha(p):
    return hashlib.sha256((ROOT / p).read_bytes()).hexdigest()


def load(p):
    want, got = PINS.get(p), sha(p)
    if want is not None and not got.startswith(want):
        raise InputsError(f"{p}: sha256 {got[:16]} is not the pinned {want} (stale input)")
    return json.loads((ROOT / p).read_text(encoding="utf-8")) if p.endswith(".json") else \
        list(csv.DictReader((ROOT / p).read_text(encoding="utf-8").splitlines()))


def _idx():
    return {ln["line_id"]: ln for ln in load(INDEX)["lines"]}


def _f(x):
    return None if x is None else float(D(str(x)))


def _expect(ln, held=True):
    if ln is None:
        raise InputsError("a mapped line is not in the V3.0.76 index (stale)")
    return {"item_code": ln["item_code"], "element_id": ln["element_id"], "unit": ln["unit"], "class": ln["class"],
            "low": ln["held_low"], "high": ln["held_high"]}


def _h1p():
    return [r for r in load(T748) if r["hub"] == "H1P" and r["package"] == "T-749"]


# ------------------------------------------------------------------------------------------------ PAINT_RESTATE
def restate_entries(ix):
    faces = {f["paint_line"]: f for f in load(T740)["faces"] if f.get("paint_line")}
    rows = [r for r in _h1p() if r["action"] == "CHANGE"]
    if len(rows) != CHANGE_N:
        raise InputsError(f"T-748 H1P CHANGE rows {len(rows)}, expected {CHANGE_N}")
    out = []
    for r in sorted(rows, key=lambda r: r["target"]):
        lid = r["target"]
        f, b = faces.get(lid), ix.get(lid)
        if f is None or b is None or b["item_code"] != "FIN.PAINT" or b["class"] != "HELD" or b["held_low"] is None:
            raise InputsError(f"{lid}: not a HELD bounded FIN.PAINT line of a T-740 face")
        if (D(f["engine_paint"][0]), D(f["engine_paint"][1])) != (D(str(b["held_low"])), D(str(b["held_high"]))):
            raise InputsError(f"{lid}: T-740 read {f['engine_paint']}, the index carries {b['held_low']} .. "
                              f"{b['held_high']} (stale)")
        lo, hi = D(f["rule_paint"][0]), D(f["rule_paint"][1])
        if not (0 < lo <= hi) or hi > D(f["plaster"][1]) or lo > D(f["plaster"][0]):
            raise InputsError(f"{lid}: rule paint {lo} .. {hi} is not inside its plaster {f['plaster']}")
        named = "; ".join(f"{n['end']} {n['cause']} {n['m2']} ({n['what']})" for n in f.get("named") or ())
        out.append({"piece": "PAINT_RESTATE", "action": "RANGE", "line_id": lid, "source_tasks": ["T-740", "T-748"],
                    "rule": "UP-FIN-PAINT-002 1.0.0 (R-T740-1)", "status": "HELD", "low": _f(lo), "high": _f(hi),
                    "plaster_line_id": f["plaster_line"], "plaster": [_f(f["plaster"][0]), _f(f["plaster"][1])],
                    "band": [_f(f["band"][0]), _f(f["band"][1])], "tiled": [_f(f["tiled"][0]), _f(f["tiled"][1])],
                    "why": (f"paint = plaster of the same face {f['plaster'][0]} .. {f['plaster'][1]} - band "
                            f"{f['band'][0]} .. {f['band'][1]} - tiled {f['tiled'][0]} .. {f['tiled'][1]} m2; engine "
                            f"line differed by the named item(s): {named or 'none'}")[:400],
                    "expect": _expect(b)})
    return out


# ------------------------------------------------------------------------------------------------ RETURN_LM
def return_entries(ix):
    t = load(T746)
    rows = t["return_rows"]
    live = {r["target"]: r for r in _h1p() if r["action"] == "PENDING"}
    if len(rows) != RETURN_N or set(live) != {r["paint_line"] for r in rows}:
        raise InputsError(f"T-746 return rows {len(rows)} / T-748 PENDING H1P rows {len(live)}: the same 30 lines "
                          "expected")
    out = []
    for r in sorted(rows, key=lambda r: r["paint_line"]):
        b, p = ix.get(r["paint_line"]), ix.get(r["plaster_line"])
        if b is None or b["item_code"] != "FIN.PAINT" or b["class"] != "HELD" or p is None or \
                p["item_code"] != "FIN.PLASTER":
            raise InputsError(f"{r['opening']}: return line / plaster host not as mapped")
        eng = r["paint_m2_before_engine"]
        if (eng is None) != (b["held_low"] is None) or (eng is not None and (D(eng[0]), D(eng[1])) != (
                D(str(b["held_low"])), D(str(b["held_high"])))):
            raise InputsError(f"{r['opening']}: T-746 read {eng}, the index carries {b['held_low']} .. {b['held_high']}")
        blank = r["status"] == "HELD"
        lm = r.get("edge_lm_after_B")
        if blank != (lm is None) or r["status"] not in ("BOUNDED", "HELD"):
            raise InputsError(f"{r['opening']}: status {r['status']} with lm {lm}")
        if not r["paint_element"].endswith(":RETURN_PAINT"):
            raise InputsError(f"{r['opening']}: return element {r['paint_element']}")
        out.append({"piece": "RETURN_LM", "action": "EDGE_BLANK" if blank else "EDGE", "line_id": r["paint_line"],
                    "opening": r["opening"], "kind": r["kind"], "floor": r["floor"],
                    "element_id": r["paint_element"].replace(":RETURN_PAINT", ":PAINT_EDGE"),
                    "host_line_id": r["plaster_line"], "source_tasks": ["T-746", "T-748"],
                    "rule": "R-T746-1 / R-T746-2 (UP-FIN-PAINT-002 edges LM_ITEMS_NOT_AREA, Lead ruling reading B)",
                    "status": "HELD" if blank else "DRAWING-CONFIRMED",
                    "low": None if blank else _f(lm[0]), "high": None if blank else _f(lm[1]),
                    "parts": [{"part": x["part"], "gross": x["gross"], "lm": x["lm"], "cause": x["cause"]}
                              for x in r.get("parts") or ()],
                    "cause": r["cause"], "frame": r.get("frame"),
                    "why": (f"{r['opening']} ({r['kind']}): the painted return is an lm item per opening (owner paint "
                            f"rule, reading B), never paint m2; {r['why']}; {r['cause']}")[:400],
                    "expect": _expect(b), "host_expect": _expect(p)})
    return out


# ------------------------------------------------------------------------------------------------ EXT_EDGE
def _floor_of(key):
    for fl, tok in (("2F", "2F"), ("1F", "1F"), ("GF", "GF"), ("GF", "ANNEX")):
        if f" {tok} " in f" {key} " or key.startswith(f"{tok}/"):
            return fl
    raise InputsError(f"{key}: no floor")


def exterior_entries(ix, returns):
    d7, d1 = load(T747), load(T751)
    arched = {a["opening"]: a for a in d1["windows"]["arched"]}
    held_w = set(d1["windows"]["held"])
    out, door_once = [], []
    ret = {e["opening"]: e for e in returns}
    for o in d7["edges"]["openings"]:
        if o["state"] == "PART_OF":
            if o["source"] not in held_w:
                raise InputsError(f"{o['opening']}: a frame-end part of a measured window")
            continue
        fl = o["face_id"].split("/")[0]
        host = FLOOR_FACADE[fl]
        if o["kind"] == "DOOR":
            r = ret.get(o["opening"])
            if r is None or r["low"] is None or (D(o["lm"][0]), D(o["lm"][1])) != (D(str(r["low"])), D(str(r["high"]))):
                raise InputsError(f"{o['opening']}: exterior door edge {o['lm']} is not its T-746 return line's "
                                  f"{None if r is None else (r['low'], r['high'])}: the reveal would count twice")
            door_once.append({"opening": o["opening"], "lm": o["lm"], "under": r["line_id"], "face_id": o["face_id"]})
            continue
        if o["kind"] != "WINDOW":
            raise InputsError(f"{o['opening']}: kind {o['kind']}")
        a = arched.get(o["opening"])
        blank = o["state"] == "HELD"
        if blank != (o["opening"] in held_w):
            raise InputsError(f"{o['opening']}: T-747 {o['state']} vs T-751 held {sorted(held_w)}")
        if blank:
            lo = hi = None
            basis, why = "HELD", "window outside edge HELD (T-746 / T-751: height or curved frame not printed)"
        elif a is not None:
            lo = hi = _f(a["lm"])
            basis = "ARC_DEVELOPED (T-751 own chain walk)"
            why = (f"arched head developed {a['head']} + jambs {a['jambs']} = {a['lm']} m (T-751 R-T751-2: the arc "
                   f"governs, the rectangle {a['rectangle_refused']} refused; T-747 ledger {a['ledger']}, "
                   f"diff {a['ledger_diff']})")
        else:
            if o["state"] != "POINT" or o["lm"][0] != o["lm"][1]:
                raise InputsError(f"{o['opening']}: a measured window edge is a point ({o['lm']})")
            lo = hi = _f(o["lm"][0])
            basis, why = o["basis"], "window outside jambs + head (T-313 / T-746 / T-747); sill is its own item"
        out.append({"piece": "EXT_EDGE", "action": "OPENING_BLANK" if blank else "OPENING", "opening": o["opening"],
                    "kind": "WINDOW", "floor": fl, "face_id": o["face_id"], "host_line_id": host,
                    "element_id": f"{fl}-FACADE:PAINT_EDGE:{o['opening']}", "source_tasks": ["T-747", "T-751"],
                    "rule": "R-T747-2 / R-T751-2 (UP-FIN-PAINT-002 edges LM_ITEMS_NOT_AREA)",
                    "status": "HELD" if blank else "DRAWING-CONFIRMED", "low": lo, "high": hi, "basis": basis,
                    "why": why[:400], "host_expect": _expect(ix.get(host))})
    # corners: one line per T-747 host key, T-751 closures applied
    c7 = d7["edges"]["corners"]["by_host"]
    cl = {c["item"].split(" ")[0]: c for c in d1["corners"]["closures"]}
    if set(cl) != {"EXT#1F-CONVEX-PARAPET-ENDS", "EXT#GF-CONVEX-PLINTH"}:
        raise InputsError(f"T-751 closures {sorted(cl)}")
    p1 = cl["EXT#1F-CONVEX-PARAPET-ENDS"]
    pl = cl["EXT#GF-CONVEX-PLINTH"]
    for key in sorted(c7):
        if key == "NO_HOST":
            continue
        v = c7[key]
        lo, hi = D(v["lm"][0]), D(v["lm"][1])
        closed = []
        if any(r.startswith("EXT#1F-CONVEX-PARAPET-ENDS") for r in v["rows"]):
            if (lo, hi) != (D(p1["before"][0]), D(p1["before"][1])) or len(v["rows"]) != 1:
                raise InputsError(f"{key}: the parapet-end group is not the T-751 closure's before bound")
            lo = hi = D(p1["after"])
            closed.append(f"T-751 parapet ends {p1['before'][0]} .. {p1['before'][1]} -> {p1['after']} (handles "
                          f"{' '.join(p1['handles'])})")
        if any(r.startswith("EXT#GF-CONVEX-PLINTH") for r in v["rows"]):
            b0, b1 = D(pl["before"][0]), D(pl["before"][1])
            if hi - lo != b1 - b0:
                raise InputsError(f"{key}: the plinth group's open part is not the T-751 plinth bound")
            lo, hi = lo - b0 + D(pl["after"]), hi - b1 + D(pl["after"])
            closed.append(f"T-751 plinth corners {pl['before'][0]} .. {pl['before'][1]} -> {pl['after']}")
        fl = _floor_of(key) if not key.startswith("L-") else \
            {v_: k_ for k_, v_ in FLOOR_FACADE.items()}[key]
        host = FLOOR_FACADE[fl]
        tag = key if not key.startswith("L-") else f"{fl}-STOREY"
        tag = tag.replace("NEW FIN.EXT.FINISH ", "").replace(" ", "_").replace("+", "")
        stop = any(r.startswith("EXT#GF-MOUTHS-STOP") for r in v["rows"])
        out.append({"piece": "EXT_EDGE", "action": "CORNER", "corner_group": key, "rows": v["rows"], "floor": fl,
                    "face_id": key, "host_line_id": host, "element_id": f"{fl}-FACADE:CORNER_EDGE:{tag}",
                    "source_tasks": ["T-747", "T-751"], "rule": "R-T747-2 / R-T751-1 (corners lm, arris once)",
                    "status": "DRAWING-CONFIRMED" if lo == hi else "HELD", "low": _f(lo), "high": _f(hi),
                    "basis": "T-747 corner rows by host" + ("; " + "; ".join(closed) if closed else ""),
                    "why": (f"outside corner arrises of face group {key} once (T-697 / T-737 rows: {', '.join(v['rows'])})"
                            + ("; stop-end 0 .. 1.20 HELD (free or abutting end shown on no vector view, T-751)"
                               if stop else "") + ("; " + "; ".join(closed) if closed else ""))[:400],
                    "host_expect": _expect(ix.get(host))})
    nh = d1["corners"]["no_host"]
    out.append({"piece": "EXT_EDGE", "action": "CORNER", "corner_group": "NO_HOST", "rows": [nh["row"]], "floor": "GF",
                "face_id": "GF passage-mouth wall end above the annex parapet top (+4.80 .. +5.50, T-737): face line "
                           "not in the candidate", "host_line_id": FLOOR_FACADE["GF"],
                "element_id": "GF-FACADE:CORNER_EDGE:PASSAGE_MOUTH_NO_HOST", "source_tasks": ["T-747", "T-751"],
                "rule": "R-T751-1 (an arris measured with no face line is wired on its own line, never dropped)",
                "status": "DRAWING-CONFIRMED", "low": _f(nh["lm"]), "high": _f(nh["lm"]),
                "basis": "T-751 corners.no_host", "why": nh["cause"][:400],
                "host_expect": _expect(ix.get(FLOOR_FACADE["GF"]))})
    return out, door_once


def inputs():
    ix = _idx()
    ch = restate_entries(ix)
    ret = return_entries(ix)
    ext, doors = exterior_entries(ix, ret)
    srcs = [dict({"task": k, "sha256": sha(v["file"])}, **v) for k, v in SOURCES.items()]
    return {"schema": "URBAN_V3077_INPUTS_V1", "project_id": "development-villa-t131", "sources": srcs,
            "entries": ch + ret + ext, "exterior_doors_counted_once": doors}


def projection(doc):
    """run-record figures per piece (never summed across codes or states)"""
    z = {}
    for e in doc["entries"]:
        k = f"{e['piece']}:{e['action']}"
        s = z.setdefault(k, {"n": 0, "low": D(0), "high": D(0)})
        s["n"] += 1
        if e.get("low") is not None:
            s["low"] += D(str(e["low"]))
            s["high"] += D(str(e["high"]))
    for k, s in z.items():
        s["low"], s["high"] = str(s["low"]), str(s["high"])
    return z


def build():
    doc = inputs()
    return {"schema": SCHEMA, "pins": {p: sha(p) for p in PINS}, "inputs": doc, "projection": projection(doc)}


def text(d):
    return json.dumps(d, ensure_ascii=False, indent=1, sort_keys=True) + "\n"


def main(argv):
    d = build()
    if "--check" in argv:
        ok = OUT.read_text(encoding="utf-8") == text(d)
        print("T749_ENTRIES equals its builder:", ok)
        return 0 if ok else 1
    if "--write" in argv:
        OUT.parent.mkdir(exist_ok=True)
        OUT.write_text(text(d), encoding="utf-8")
        print("written", OUT.relative_to(ROOT))
    print(json.dumps(d["projection"], sort_keys=True, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
