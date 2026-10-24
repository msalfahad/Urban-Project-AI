"""T-232 (V3.0.10): the project inputs of ARCH_TAKEOFF_V3.0.10 (URBAN_V3010_INPUTS_V1) for the development villa.
Research code; it reads the merged opening ledgers as committed and changes none of their quantities except where a
later checker-merged piece names the change (T-238, below). Values, opening ids and BOQ ids only (no coordinates, no
names, no drawing content).

OPENINGS (doors and windows, pcs AND m2 from ONE opening list):
  T-198 census r3 (MERGED 57bb0411, Verifier 2026-10-23 03:57 UTC): OPENINGS_T198.csv, one row per drawn opening with
  its id, class, leaves, width and height and their sources. Heights of the windows the census left headless:
  T-201 (MERGED 5dade783, Verifier 2026-10-23 07:00 UTC, HEADS_T201.csv: vector DWF geometry re-datumed to the floor)
  and T-207 (MERGED e081911c, Verifier 2026-10-23 09:07 UTC, CLOSURE_T207.csv: W11 / W12 2.20 between the shutter
  leaves; W02 count HELD). Arched windows: T-238 (MERGED 242e50b2, Verifier 2026-10-23 22:50 UTC, DELTA_T238.csv):
  W15 / W16 window 1.55 x 3.00 = 4.650 (Q-32 A on the opening crown, not the 0.10 band crown 3.10; Checker
  FREELANCER_RIGHT), W26 1.20 x 1.70 = 2.040 confirmed, W17 HELD 9.870 .. 11.515 (opening crown 3.00 .. archivolt 3.50,
  owner item Q-76; never the larger end).
  One opening definition (owner 2026-10-23): the structural opening between the jambs (the census id, the same id the
  masonry / finish deductions carry); a double leaf is one opening; window m2 = Q-32 A enclosing rectangle on the
  opening line. Door heights: Q-55 C 2.20 (ASSUMED - OWNER-APPROVED) except the main entrance (2.50 printed).
  Lead 2026-10-24 00:10 (row T-232): W03 and W18 (in no window line of either run, T-236 F5) are carried from the
  census with their sources (both DRAWING-CONFIRMED, printed); the 10 doors the engine holds only in its door schedule
  (T-236 F4) stay HELD with the engine's cause (class candidate, element PROVISIONAL, width review), the census
  reading shown beside as information, never silently released.
  Engine lines superseded: the 17 door lines (pcs) and 27 window lines (pcs) of the candidate (= released route G),
  each named with the census opening it is; the census engine reference (door token / per-floor opening id) binds
  them.
"""

from __future__ import annotations

import csv
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
T198 = ROOT / "research/agents_t198"
T201 = ROOT / "research/agents_t201"
T207 = ROOT / "research/agents_t207"
T238 = ROOT / "research/agents_t238"
ALU, PVC, MAIN, WIN = "DOOR.EXTERNAL.ALUMINIUM", "DOOR.INTERNAL.PVC", "DOOR.MAIN_ENTRANCE", "ARCH.WINDOW"
CODES = [ALU, PVC, MAIN, WIN]
FLOORS = ["GF", "1F", "2F"]
DOOR_H = 2.20                    # Q-55 C owner fallback (no sheet prints a door head)
DC, AS = "DRAWING-CONFIRMED", "ASSUMED - OWNER-APPROVED"
Q55 = "Q-55 C / UP-DOOR-HGT-001: door head 2.20 m where no sheet prints one (ASSUMED - OWNER-APPROVED)"
SRC = {"T-198": ("research/agents_t198/OPENINGS_T198.csv", "T-198 r3", "57bb0411", "Verifier 2026-10-23 03:57 UTC"),
       "T-201": ("research/agents_t201/HEADS_T201.csv", "T-201", "5dade783", "Verifier 2026-10-23 07:00 UTC"),
       "T-207": ("research/agents_t207/CLOSURE_T207.csv", "T-207", "e081911c", "Verifier 2026-10-23 09:07 UTC"),
       "T-238": ("research/agents_t238/DELTA_T238.csv", "T-238", "242e50b2", "Verifier 2026-10-23 22:50 UTC")}

# The candidate's window lines: element id = <candidate room>:<opening id> (this run's ARCH_OPENINGS); the census
# ENGINE_REF names the per-floor opening id, the room is the line's own (read from the run, listed here).
WINDOW_ROOM = {("GF", "OP-004"): "GF-R51E127", ("GF", "OP-006"): "GF-RA3AD49", ("GF", "OP-014"): "GF-RDF7D28",
               ("GF", "OP-015"): "GF-RB28769", ("GF", "OP-016"): "GF-RD6F891", ("GF", "OP-019"): "GF-RC99C2A",
               ("GF", "OP-022"): "GF-R31F8AE", ("GF", "OP-023"): "GF-RC06FED", ("GF", "OP-024"): "GF-RC99C2A",
               ("GF", "OP-028"): "GF-R7512EA", ("GF", "OP-029"): "GF-R7512EA",
               ("1F", "OP-001"): "1F-R48AA46", ("1F", "OP-002"): "1F-R8BDA49", ("1F", "OP-003"): "1F-RED0D19",
               ("1F", "OP-012"): "1F-R78C367", ("1F", "OP-013"): "1F-R26FA0D", ("1F", "OP-014"): "1F-R52AC05",
               ("1F", "OP-015"): "1F-RED23B8", ("1F", "OP-016"): "1F-R78C367", ("1F", "OP-017"): "1F-R78C367",
               ("1F", "OP-021"): "1F-R78C367", ("1F", "OP-022"): "1F-RB72F22", ("1F", "COP-001"): "1F-R3CFCFD",
               ("2F", "OP-003"): "2F-R4D1B62", ("2F", "OP-004"): "2F-RE83BED", ("2F", "OP-005"): "2F-R1DB2D2",
               ("2F", "OP-008"): "2F-R4D1B62"}

# The 10 doors the engine holds only in its door schedule (T-236 F4; DOOR_SCHEDULE.json PROVISIONAL_NOT_RELEASED):
# engine cause -> what it holds here. classes: candidate classes when the engine's class differs from the census or
# is unresolved (T-181 rule 4: each candidate class answered once, from 0); width: the reading range the engine cause
# leaves open (engine leaf .. census structural opening).
ENGINE_HELD = {
    "D-GF-01": {"classes": [ALU, MAIN], "cause": "engine door schedule: MAIN_ENTRANCE_CANDIDATE (exterior adjacency); "
                "census T-198: aluminium external (UP-DOOR-CLS-002, court side): class held until the Checker rules"},
    "D-GF-05": {"classes": [ALU, PVC], "cause": "engine door schedule: CLASS_REVIEW; census T-198: class HELD (kitchen "
                "to the side passage: external only if the passage is open-air, owner Q-67 A conditional, designer "
                "D-48)"},
    "D-GF-06": {"classes": [ALU, PVC], "cause": "engine door schedule: CLASS_UNRESOLVED (sides UNKNOWN / SPACE); "
                "census T-198: aluminium external (UP-DOOR-CLS-002 'pantry external access' onto the entrance "
                "landing): class held until the Checker rules"},
    "D-GF-07": {"classes": [MAIN], "cause": "engine door schedule: MAIN_ENTRANCE_CANDIDATE; census T-198: main "
                "entrance HELD (T-161 F07c, WORKFLOW_CONTROLS s.8: the renders show a single leaf, the plan / SE "
                "elevation print a 2.00 x 2.50 double; designer D-53); 5.000 m2 is the candidate only"},
    "D-GF-09": {"width": [0.90, 1.00], "cause": "engine door schedule: CONFIRMED aluminium, not released (width "
                "review: band opening 0.90, door block frame 1.00); census T-198 0.90 jamb to jamb"},
    "D-GF-02": {"width": [0.69, 0.80], "cause": "engine door schedule: element PROVISIONAL, width 0.69 (leaf) .. 0.80 "
                "(closure); census T-198 0.80 closure (jamb hits)"},
    "D-GF-10": {"width": [0.69, 0.80], "cause": "engine door schedule: element PROVISIONAL, width 0.69 (leaf) .. 0.797 "
                "(closure); census T-198 0.80 closure (DXF 0.797)"},
    "D-GF-14": {"width": [0.69, 0.80], "cause": "engine door schedule: element PROVISIONAL, width 0.69 .. 0.80; census "
                "T-198 width HELD 0.69 .. 0.80 (no jamb-to-jamb band; loose swing arc r 0.69)"},
    "D-1F-03": {"width": [0.89, 1.00], "cause": "engine door schedule: element PROVISIONAL, width 0.89 (leaf) .. 1.00 "
                "(closure); census T-198 1.00 closure (jamb hits)"},
    "D-1F-04": {"width": [0.69, 0.80], "cause": "engine door schedule: element PROVISIONAL, width 0.69 (leaf) .. 0.80 "
                "(closure); census T-198 0.80 closure (jamb hits)"},
}

# Window heights the census r3 left headless, from the merged follow-ups (value, source key, basis)
HEADS = {"W11": (2.20, "T-207", "fence elevation: the opening between the louvred leaves 1.969 / 1.966 x 2.201; the frame "
                                "2.017 is a fabrication size (T-207)"),
         "W12": (2.20, "T-207", "as W11 (T-207)"),
         "W15": (3.00, "T-238", "opening crown 3.00 above the floor (Q-32 A on the opening line; the 3.10 of the census "
                                "is the 0.10 surround band crown, Checker 20:14 / 22:50)"),
         "W16": (3.00, "T-238", "twin of W15 (T-238; T-201 read 3.10 = band crown)")}
W17_H = [3.00, 3.50]            # opening crown .. archivolt crown (T-238; owner item Q-76)
NO_SUPPLY = {"OPENING": "no leaf, no glazing: not a door / window supply item (its masonry / finish deduction is the "
                        "finish packages')",
             "LIFT": "lift shaft opening (UP-DOOR-CLS-005): never a PVC / aluminium door; lift landing doors are the "
                     "lift supplier's item",
             "GATE": "court / boundary gate, not a building door: no Urban door class covers it (width not established)",
             "UNRESOLVED": "identity not established (no engine opening, no window tag, no freelancer row): UNKNOWN, "
                           "the tag-based inventory (T-249) decides; never a window line by default"}


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def _src(key):
    f, task, mc, run = SRC[key]
    return {"file": f, "sha256": sha(ROOT / f), "task": task, "merge_commit": mc, "checker_run": run}


def _rows(path):
    with open(path, encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def census():
    return {r["ID"]: r for r in _rows(T198 / "OPENINGS_T198.csv")}


def heads_t201():
    return {r["ID"]: r for r in _rows(T201 / "HEADS_T201.csv")}


def delta_t238():
    return {(r["opening"], r["line"]): r for r in _rows(T238 / "DELTA_T238.csv")}


def _f(x):
    return float(x) if str(x).strip() else None


def _engine_element(r):
    ref = r["ENGINE_REF"]
    if r["KIND"] == "DOOR":
        tok = ref.split("/")[0].strip()
        return tok if tok.startswith("DOOR-") else None
    op = ref.strip()
    if op.startswith("none"):
        return None
    room = WINDOW_ROOM[(r["FLOOR"], op)]
    return f"{room}:{op}"


def door_record(r):
    oid = r["ID"]
    eh = ENGINE_HELD.get(oid)
    code = r["BOQ_LINE"]
    w = _f(r["WIDTH_M"])
    o = {"id": oid, "kind": "DOOR", "floor": r["FLOOR"], "leaves": int(r["LEAVES"]),
         "opening_definition": f"structural opening {r['WIDTH_BASIS']} ({r['FORM']}); a double leaf is one opening",
         "sources": ["T-198"], "engine_element": _engine_element(r),
         "census": {"class": code, "class_status": r["CLASS_STATUS"], "width": r["WIDTH_M"],
                    "width_lo": r["WIDTH_LO_M"] or None, "height": r["HEIGHT_M"], "height_status": r["HEIGHT_STATUS"],
                    "verdict": r["VERDICT"] or None, "freelancer_key": r["FREELANCER_KEY"] or None}}
    h = _f(r["HEIGHT_M"])
    if oid == "D-GF-07":           # printed 2.00 x 2.50
        o["height"] = {"value": h, "status": DC, "source": r["HEIGHT_SOURCE"]}
    else:
        assert abs(h - DOOR_H) < 1e-9 and r["HEIGHT_STATUS"] == "ASSUMED", oid
        o["height"] = {"value": DOOR_H, "status": AS, "source": Q55}
        o["assumption"] = Q55
    if eh and eh.get("width"):
        o["width"] = {"range": eh["width"], "status": DC, "source": r["WIDTH_SOURCE"]}
    else:
        o["width"] = {"value": w, "status": DC, "source": f"{r['WIDTH_BASIS']}: {r['WIDTH_SOURCE']}"}
    if eh is None:
        assert code in (ALU, PVC) and r["CLASS_STATUS"] == DC and not r["WIDTH_LO_M"], oid
        o["classes"] = [code]
        o["pcs"] = {"state": "SETTLED", "count": 1}
        o["m2"] = {"state": "RELEASED", "value": round(w * DOOR_H, 4), "evidence_status": AS}
        return o
    o["classes"] = eh.get("classes") or [code]
    reasons = [eh["cause"]]
    if len(o["classes"]) > 1:
        o["class_hold"] = eh["cause"]
        o["pcs"] = {"state": "HELD", "range": [0, 1], "reasons": reasons}
        o["m2"] = {"state": "BOUNDED", "range": [0.0, round(w * o["height"]["value"], 4)], "evidence_status": "HELD",
                   "reasons": reasons, "range_basis": "class held: 0 in this class .. width x height in it"}
    else:
        o["pcs"] = {"state": "HELD", "range": [1, 1], "reasons": reasons}
        wl, wh = o["width"].get("range") or (w, w)
        o["m2"] = {"state": "BOUNDED", "range": [round(wl * o["height"]["value"], 4),
                                                 round(wh * o["height"]["value"], 4)],
                   "evidence_status": "HELD", "reasons": reasons}
    return o


def window_record(r, heads, delta):
    oid = r["ID"]
    w = _f(r["WIDTH_M"])
    o = {"id": oid, "kind": "WINDOW", "floor": r["FLOOR"], "classes": [WIN], "leaves": int(r["LEAVES"] or 1),
         "opening_definition": f"structural opening on the opening line ({r['FORM']}; width {r['WIDTH_BASIS']}); "
                               "area = Q-32 A enclosing rectangle to the opening crown",
         "sources": ["T-198"], "engine_element": _engine_element(r),
         "width": {"value": w, "status": DC, "source": r["WIDTH_SOURCE"]},
         "census": {"width": r["WIDTH_M"], "height": r["HEIGHT_M"], "height_status": r["HEIGHT_STATUS"],
                    "pcs_status": r["PCS_STATUS"], "verdict": r["VERDICT"] or None}}
    h, hsrc = None, None
    if oid in HEADS:
        h, key, basis = HEADS[oid]
        hsrc = basis
        o["sources"].append(key)
    elif oid == "W17":
        o["sources"].append("T-238")
    elif r["HEIGHT_STATUS"] == "PRINTED":
        h, hsrc = _f(r["HEIGHT_M"]), r["HEIGHT_SOURCE"]
    elif oid in heads and heads[oid]["STATUS"] == DC:
        h, hsrc = _f(heads[oid]["HEIGHT_M"]), f"T-201 {heads[oid]['VIEW']} vector geometry (DRAWING-CONFIRMED)"
        o["sources"].append("T-201")
    if oid in ("W15", "W16", "W26", "W17"):          # T-238 window rows, asserted against the delta
        d = delta[(oid, "WINDOW.ALUMINIUM")]
        if oid == "W17":
            assert d["new"] == "HELD", d
        else:
            assert abs(float(d["new"]) - w * h) < 5e-4, (oid, d["new"], w * h)
    if oid == "W02":                                  # count HELD (T-181 verdict, T-207), m2 no figure
        h2 = _f(heads["W02"]["HEIGHT_M"])
        o["sources"] += ["T-201", "T-207"]
        o["height"] = {"value": h2, "status": DC, "source": "T-201 section B-B cut (+1.00 .. +3.20)"}
        cause = ("count 1 (every drawing) vs 2 (render with a pier, T-161 F23): WORKFLOW_CONTROLS s.8 DIFFERS, "
                 "designer D-53 (T-181 Checker verdict faa04202; T-207)")
        o["pcs"] = {"state": "HELD", "range": [1, 2], "reasons": [cause]}
        o["m2"] = {"state": "UNQUANTIFIED", "evidence_status": "HELD",
                   "reasons": [cause + "; with a pier the glazed area is less by a width no sheet prints"],
                   "info": {"area_on_the_drawn_count_m2": round(w * h2, 3), "basis": "6.33 x 2.20 (T-207)"}}
        return o
    if oid == "W17":
        o["height"] = {"range": W17_H, "status": DC, "source": "T-238: chain 305 ends on the opening arch (3.00 .. "
                       "3.05), 45 on an archivolt (3.50 = archivolt crown, the owner's Q-32 / Q-39 example)"}
        cause = ("owner item Q-76: the window crown is the opening arch (3.00 .. 3.05 -> 9.870 .. 10.036 m2) or the "
                 "owner's example 3.29 x 3.50 = 11.515 m2 (archivolt); never the larger end")
        o["pcs"] = {"state": "SETTLED", "count": 1}
        o["m2"] = {"state": "BOUNDED", "range": [round(w * W17_H[0], 4), round(w * W17_H[1], 4)],
                   "evidence_status": "HELD", "reasons": [cause]}
        return o
    assert h is not None, f"{oid}: no established height"
    assert r["PCS_STATUS"] == "SETTLED", oid
    o["height"] = {"value": h, "status": DC, "source": hsrc}
    o["pcs"] = {"state": "SETTLED", "count": 1}
    o["m2"] = {"state": "RELEASED", "value": round(w * h, 4), "evidence_status": DC}
    return o


def openings():
    c, heads, delta = census(), heads_t201(), delta_t238()
    recs, excluded = [], []
    for oid, r in c.items():
        if r["KIND"] == "DOOR":
            recs.append(door_record(r))
        elif r["KIND"] == "WINDOW":
            recs.append(window_record(r, heads, delta))
        else:
            excluded.append({"id": oid, "kind": r["KIND"], "floor": r["FLOOR"], "census_line": r["BOQ_LINE"],
                             "why": NO_SUPPLY[r["KIND"]]})
    return recs, excluded


def piece():
    recs, excluded = openings()
    sup = []
    for o in recs:
        e = o.pop("engine_element")
        o["sources"] = [_src(k) for k in dict.fromkeys(o["sources"])]
        if e is None or o["id"] in ENGINE_HELD:     # no candidate line (the engine holds it in its door schedule)
            continue
        code = WIN if o["kind"] == "WINDOW" else o["census"]["class"]
        sup.append({"element_id": e, "floor": o["floor"], "item_code": code, "unit": "pcs", "carried": 1,
                    "opening": o["id"], "why": f"the same physical opening {o['id']} (census T-198 engine reference); "
                                               "its count moves to the type / floor pcs line and its area to the m2 "
                                               "line of the same opening ids"})
    tot = {}
    for o in recs:
        for code in o["classes"]:
            t = tot.setdefault(code, {"pcs": {"settled": 0.0, "held": [0.0, 0.0], "no_figure": 0},
                                      "m2": {"released": 0.0, "bounded": [0.0, 0.0], "unquantified": 0}})
            if o["pcs"]["state"] == "SETTLED":
                t["pcs"]["settled"] += 1
            else:
                t["pcs"]["held"][0] += o["pcs"]["range"][0]
                t["pcs"]["held"][1] += o["pcs"]["range"][1]
            m = o["m2"]
            if m["state"] == "RELEASED":
                t["m2"]["released"] += m["value"]
            elif m["state"] == "BOUNDED":
                t["m2"]["bounded"][0] += m["range"][0]
                t["m2"]["bounded"][1] += m["range"][1]
            else:
                t["m2"]["unquantified"] += 1
    for t in tot.values():
        t["m2"]["released"] = round(t["m2"]["released"], 4)
        t["m2"]["bounded"] = [round(x, 4) for x in t["m2"]["bounded"]]
    return {"piece": "OPENINGS", "item_codes": CODES, "source": _src("T-198"),
            "sources": [_src(k) for k in ("T-201", "T-207", "T-238")],
            "scope": {"floors": FLOORS, "supersede_lines": sup, "other_elements": []},
            "openings": recs, "excluded": excluded, "declared_totals": tot}


def inputs(project_id=None):
    import sys
    sys.path.insert(0, str(ROOT / "research" / "agents_t193"))
    import t193_inputs as L7   # noqa: E402  (the V3.0.7 guard inputs, unchanged, as V3.0.8 / V3.0.9)
    g = dict(L7.inputs(project_id)["guard"], new_records=[])
    return {"schema": "URBAN_V3010_INPUTS_V1", "project": project_id, "pieces": [piece()], "guard": g}


if __name__ == "__main__":
    pc = piece()
    for o in pc["openings"]:
        print(o["id"], o["floor"], o["classes"], o["pcs"].get("count", o["pcs"].get("range")), o["m2"]["state"],
              o["m2"].get("value", o["m2"].get("range")))
    import json
    print(json.dumps(pc["declared_totals"], indent=1))
    print(len(pc["scope"]["supersede_lines"]), "superseded;", len(pc["excluded"]), "excluded")
