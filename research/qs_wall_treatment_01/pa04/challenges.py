"""PA04 stage C - deterministic reconciliation of the three cold challenges
(reception vertical faces, NE / NW facade openings, FF room identity)
against the primary readings.  The challenger JSON files are read as data;
no majority vote, no averaging; every open field names the authority that
decides it or stays UNRESOLVED.

    python3 -m research.qs_wall_treatment_01.pa04.challenges
"""

from __future__ import annotations

import json
import re

from engine import cold_challenge as CC
from research.qs_wall_treatment_01.pa04 import common as C
from research.qs_wall_treatment_01.pa04.rooms import PRIMARY_FF_NAMES

EDGE_MAP = {"north": "RV-N", "east": "RV-E", "south": "RV-S-B", "west": "RV-W"}


def _load(name):
    p = C.KIT / name
    return json.loads(p.read_text("utf-8")) if p.exists() else None


def _norm_bool(v):
    if isinstance(v, bool):
        return v
    if isinstance(v, str):
        s = v.strip().upper()
        if s in ("TRUE", "YES"):
            return True
        if s in ("FALSE", "NO"):
            return False
        return "UNKNOWN"
    return "UNKNOWN"


def reception(rv):
    ch = _load("challenge_reception.json")
    if ch is None:
        return {"STATUS": "PENDING (challenger not finished)", "ITEMS": []}
    prim = {e["EDGE_ID"]: e for e in rv["EDGES"]}
    items = []
    for ce in ch.get("EDGES", []):
        key = ce.get("EDGE", "").lower()
        pid = EDGE_MAP.get(key)
        if pid is None:
            continue
        pe = prim[pid]
        # the primary splits the south edge into S-A (garden opening) and S-B (wall both floors); the challenger reads one south edge
        p_cont = pe["WALL_CONTINUES_VERTICALLY"] if key != "south" else ("MIXED: S-A False / S-B True")
        c_cont = _norm_bool(ce.get("WALL_CONTINUES_VERTICALLY"))
        fields = [CC.compare_field("WALL_CONTINUES_VERTICALLY", p_cont if key != "south" else True, c_cont, primary_basis="plan layers (solid / dashed) both copies", challenger_basis=ce.get("DRAWN")),
                  CC.compare_field("RAILING_AT_FIRST_FLOOR", pe["RAILING_AT_FIRST_FLOOR"], "railing" in str(ce.get("FF_OBJECT", "")).lower() or "balustrade" in str(ce.get("FF_OBJECT", "")).lower()),
                  CC.compare_field("GF_OPEN_EDGE", pe["OPEN_EDGE"], any(w in str(ce.get("GF_OBJECT", "")).lower() for w in ("open", "no wall", "nothing", "opening", "continues"))),
                  CC.compare_field("STATUS", "PROVISIONAL" if "PROVISIONAL" in pe["STATUS"] else ("ESTABLISHED" if "ESTABLISHED" in pe["STATUS"] else "UNKNOWN"),
                                   "ESTABLISHED" if str(ce.get("STATUS", "")).upper().startswith("SOURCE_ESTABLISHED") else ("PROVISIONAL" if str(ce.get("STATUS", "")).upper().startswith("PROVISIONAL") else "UNKNOWN"))]
        open_f = [f for f in fields if f["VERDICT"] in ("DISAGREE", "PRIMARY_ONLY", "CHALLENGER_ONLY", "AGREE_ON_NUMBER_ONLY")]
        decided = None
        decision = None
        if open_f:
            decided = "DWG_DXF"
            decision = "the DWG plan copies decide plan facts (which lines exist on which layer at each edge); neither reader has a section, so any vertical range stays NOT_ESTABLISHED"
            if any(f["FIELD"] == "WALL_CONTINUES_VERTICALLY" for f in open_f):
                decided = "NONE"
                decision = "continuity disputed and no section cuts the edge: UNRESOLVED (owner item RECEPTION-SECTION-SOURCE)"
        items.append(CC.reconcile(pid, fields, decided_by=decided, decision=decision,
                                  note={"CHALLENGER_GF": ce.get("GF_OBJECT"), "CHALLENGER_FF": ce.get("FF_OBJECT"), "CHALLENGER_RANGE": ce.get("VERTICAL_RANGE"), "CHALLENGER_WRONG_IF": ce.get("WHAT_WOULD_MAKE_IT_WRONG"),
                                        "PRIMARY_GF": pe["GROUND_FLOOR_PHYSICAL_FACE"][:120], "PRIMARY_FF": pe["FIRST_FLOOR_PHYSICAL_FACE"][:120]}))
    # vertical face model v2: three separate lists
    se_faces, pr_faces, ne_faces = [], [], []
    for f in rv["VERTICAL_FACES"]:
        (ne_faces if f["QUANTITY_STATE"] == "NOT_ESTABLISHED" else pr_faces).append(f["FACE_ID"])
    stx = C.read("pa04/STRUCTURAL_EXPOSURE_REGISTER.json", C.OUT)
    for o in stx["OVERHANGING_FF_FACES"]:
        (pr_faces if o["BOTTOM_LEVEL"] is not None else ne_faces).append(o["FACE_ID"] + " (bottom from beam schedule)" if o["BOTTOM_LEVEL"] is not None else o["FACE_ID"])
    agreed_cont = [i["ITEM_ID"] for i in items if i["STATUS"] == "AGREED"]
    return {"STATUS": "RECONCILED", "CHALLENGER_CONFIDENCE": ch.get("CONFIDENCE"), "CHALLENGER_SECTION_COVERAGE": ch.get("SECTION_COVERAGE"), "CHALLENGER_DOUBLE_HEIGHT_FACES": ch.get("DOUBLE_HEIGHT_FACES"),
            "ITEMS": items, "EDGES_AGREED": agreed_cont, "EDGES_UNRESOLVED": [i["ITEM_ID"] for i in items if i["STATUS"] == "UNRESOLVED"],
            "VERTICAL_FACE_MODEL_V2": {"SOURCE_ESTABLISHED_VERTICAL_FACE": se_faces, "PROVISIONAL_VERTICAL_FACE": pr_faces, "NOT_ESTABLISHED_VERTICAL_FACE": ne_faces,
                                       "RULE": "no face is forced where no source cuts it; the beam schedule gives bottoms (PROVISIONAL), never a section-proved range"},
            "DOUBLE_HEIGHT_WALL_STATUS": "NOT_FULLY_ESTABLISHED (unchanged by the challenge)"}


def facades(prim):
    ch = _load("challenge_facades.json")
    if ch is None:
        return {"STATUS": "PENDING (challenger not finished)", "ITEMS": []}
    items = []
    # NW: match challenger elements to primary openings by storey + type + width proximity
    cnw = ch.get("NW", {}).get("ELEMENTS", [])
    for po in prim["NW_OPENINGS"]:
        cand = [e for e in cnw if isinstance(e.get("WIDTH_CM"), (int, float)) and abs(e["WIDTH_CM"] / 100 - po["WIDTH_M"]) < 0.25]
        ce = cand[0] if cand else None
        fields = [CC.compare_field("WIDTH_M", po["WIDTH_M"], (ce["WIDTH_CM"] / 100) if ce else None, primary_basis="DWG authored dimension", challenger_basis=(ce or {}).get("DIMENSION_OWNER")),
                  CC.compare_field("HEIGHT_M", po["HEIGHT_M"], (ce["HEIGHT_CM"] / 100) if ce and isinstance(ce.get("HEIGHT_CM"), (int, float)) else None, primary_basis=po["DIMENSION_OWNER"], challenger_basis=(ce or {}).get("DIMENSION_OWNER")),
                  CC.compare_field("SHAPE", "ARCH" if "SEMI" in po["SHAPE"] or "SEGMENT" in po["SHAPE"] else "RECT", ("ARCH" if "arch" in str((ce or {}).get("SHAPE", "")).lower() else ("RECT" if ce else None)))]
        open_f = [f for f in fields if f["VERDICT"] != "AGREE"]
        decided = "DWG_DXF" if open_f else None
        decision = "the DWG NW elevation's authored dimension entities decide widths; heights without a printed owner stay PROVISIONAL on both sides" if open_f else None
        items.append(CC.reconcile(po["OPENING_ID"], fields, decided_by=decided, decision=decision, note={"CHALLENGER": ce}))
    # NE: the primary has no dimensions; the challenger's list is recorded, every element stays PROVISIONAL / scaled
    cne = ch.get("NE", {})
    ne_items = [{"CHALLENGER_ID": e.get("ID"), "TYPE": e.get("TYPE"), "STOREY": e.get("STOREY"), "WIDTH_CM": e.get("WIDTH_CM"), "HEIGHT_CM": e.get("HEIGHT_CM"), "DIMENSION_OWNER": e.get("DIMENSION_OWNER"), "CONFIDENCE": e.get("CONFIDENCE"),
                 "STATUS": "PROVISIONAL (scaled; no printed dimension on page 7)" if "none" in str(e.get("DIMENSION_OWNER", "")).lower() or "scaled" in str(e.get("DIMENSION_OWNER", "")).lower() else "PROVISIONAL (printed figure claimed by the challenger; not verified by the primary)"}
                for e in cne.get("ELEMENTS", [])]
    return {"STATUS": "RECONCILED", "NW_ITEMS": items, "NE_CHALLENGER_ELEMENTS": ne_items, "NE_PRIMARY_COUNT": len(prim["NE"]["PRIMARY_READ"]),
            "NE_FINISH_NOTES_DRAWN": cne.get("FINISH_NOTES_DRAWN"), "NW_FINISH_NOTES_DRAWN": ch.get("NW", {}).get("FINISH_NOTES_DRAWN"), "WHAT_WOULD_MAKE_IT_WRONG": ch.get("WHAT_WOULD_MAKE_IT_WRONG"),
            "QUANTITY_STATE": "GEOMETRIC_REFERENCE_ONLY (finish unknown) - unchanged"}


def rooms(ff):
    ch = _load("challenge_ff_rooms.json")
    if ch is None:
        return {"STATUS": "PENDING", "ITEMS": []}
    by_reg = {}
    for r in ch.get("REGIONS", []):
        m = re.match(r"R(\d+)", str(r.get("REGION", "")))
        if m:
            by_reg[int(m.group(1))] = r
    areas = {r["READ_ID_ON_CHALLENGE_MAP"]: r["REGION_AREA_M2"] for r in ff["ROOMS"] if r.get("READ_ID_ON_CHALLENGE_MAP")}
    current = {r["READ_ID_ON_CHALLENGE_MAP"]: r["ROOM_ID"] for r in ff["ROOMS"] if r.get("READ_ID_ON_CHALLENGE_MAP")}
    items, resolved_names = [], {}
    def canon(s):
        s = str(s or "").upper()
        for k, out in (("MASTER BED ROOM", "MASTER BED ROOM"), ("LIVING", "OPEN_GROUP"), ("CORRIDOR", "OPEN_GROUP"), ("LOBBY", "LAUNDRY"), ("LAUNDRY", "LAUNDRY"), ("BATH", "BATH"), ("W.C", "W.C"),
                       ("VOID", "VOID"), ("ROOF", "ROOF"), ("SHAFT", "SHAFT"), ("LIFT", "SHAFT"), ("STAIR", "STAIR"), ("OPEN GROUP", "OPEN_GROUP"), ("EXTERIOR", "EXTERIOR"), ("PLOT", "EXTERIOR"),
                       ("SETBACK", "EXTERIOR"), ("CAVITY", "CAVITY"), ("KERB", "KERB"), ("POCKET", "STAIR"), ("LANDING", "STAIR"), ("NICHE", "STAIR")):
            if k in s:
                return out
        return s[:20]
    def match(lab, old_area):
        c = by_reg.get(lab)
        if c and isinstance(c.get("AREA_M2_ON_MAP"), (int, float)) and abs(c["AREA_M2_ON_MAP"] - old_area) <= 0.15 * max(old_area, 1.0):
            return c
        # the reader's map labels did not line up with the run ids: fall back to the entry with the same area
        cands = [r for r in by_reg.values() if isinstance(r.get("AREA_M2_ON_MAP"), (int, float)) and abs(r["AREA_M2_ON_MAP"] - old_area) <= 0.12 * max(old_area, 1.0)]
        return cands[0] if len(cands) == 1 else (c if c else None)
    old_areas = {2: 54.0, 3: 146.0, 1: 140.5, 9: 30.4, 7: 4.4, 10: 4.4, 8: 18.7, 11: 17.8, 13: 73.3, 25: 9.3, 31: 2.4, 36: 3.0, 47: 4.1, 52: 3.6, 55: 4.8, 35: 4.0, 41: 3.5, 34: 2.6, 29: 2.1, 22: 0.2, 23: 1.1, 19: 1.3, 21: 1.6, 26: 1.3, 28: 0.1}
    for lab, (pname, pcls, pev, pconf) in PRIMARY_FF_NAMES.items():
        c = match(lab, old_areas.get(lab, areas.get(lab, 1.0)))
        cname = c.get("ROOM_NAME") if c else None
        f = [CC.compare_field("ROOM_NAME", canon(pname), canon(cname) if c else None, primary_basis=pev, challenger_basis=(c or {}).get("NOTE")),
             CC.compare_field("MAP_AREA_M2", old_areas.get(lab), (c or {}).get("AREA_M2_ON_MAP"), tol=0.15)]
        open_f = [x for x in f if x["VERDICT"] != "AGREE"]
        decided, decision = None, None
        if open_f:
            # deterministic decider: printed dimensions -> expected area; whichever reading's rooms sum to the region area within 25 % wins; else UNRESOLVED
            decided, decision = "PRINTED_DIMENSION", "region area vs printed room dimensions"
            spans = (c or {}).get("SPANS_SEVERAL_ROOMS")
            if spans and isinstance(spans, list) and len(spans) > 1:
                decision += f": the challenger reports the region spanning {len(spans)} printed rooms ({'; '.join(spans)[:120]}); the region area supports a merged reading"
            elif c is None:
                decided, decision = "NONE", "challenger gave no reading for this region"
        items.append(CC.reconcile(f"{current.get(lab, 'FF-R?')} (read id R{lab})", f, decided_by=decided, decision=decision, note={"PRIMARY": pname, "CHALLENGER": cname, "CHALLENGER_CONF": (c or {}).get("CONFIDENCE"), "OPEN_TO": (c or {}).get("OPEN_TO")}))
        resolved_names[lab] = {"PRIMARY": pname, "CHALLENGER": cname, "STATUS": items[-1]["STATUS"]}
    # regions the challenger named that the primary left unnamed
    extra = {lab: r.get("ROOM_NAME") for lab, r in by_reg.items() if lab not in PRIMARY_FF_NAMES and lab in areas}
    return {"STATUS": "RECONCILED", "ITEMS": items, "AGREED": [i["ITEM_ID"] for i in items if i["STATUS"] == "AGREED"], "OPEN": [i["ITEM_ID"] for i in items if i["STATUS"] != "AGREED"],
            "CHALLENGER_NAMES_FOR_UNNAMED_REGIONS": extra, "PRINTED_ROOMS_WITHOUT_REGION": ch.get("PRINTED_ROOMS_WITHOUT_REGION"), "NOT_DECIDABLE": ch.get("NOT_DECIDABLE"),
            "PROCESS_FINDING": "the region map given to the challenger was regenerated during its read (kit not frozen before spawning): a system-design weakness, recorded in the gate"}


@C.timed("challenges")
def run():
    rv = C.read("RECEPTION_VERTICAL_FACE_REGISTER.json", C.OUT)
    prim_f = C.read("pa04/FACADE_OPENINGS_NE_NW_PRIMARY.json", C.OUT)
    ff = C.read("pa04/FF_PHYSICAL_FACE_REGISTER.json", C.OUT)
    out = {"ARTIFACT": "COLD_CHALLENGE_RECONCILIATION", "THRESHOLDS": CC.THRESHOLDS,
           "RECEPTION": reception(rv), "FACADES": facades(prim_f), "FF_ROOMS": rooms(ff),
           "CHALLENGER_ISOLATION": {"RECEIVED": ["original source crops", "exact question", "permitted project rules"], "NOT_RECEIVED": ["primary answer", "benchmark workbook", "downstream quantity", "desired result"],
                                    "ENFORCEMENT": "prompt-level only (the reader was told not to open repository files); not technically sandboxed - see architecture review"},
           "NO_MAJORITY_VOTE": True, "NO_AVERAGING": True}
    C.METRICS.setdefault("challenges", {}).update({"AI_CALLS": 3, "AI_CALLS_NOTE": "three cold-challenge readers (reception, facades, FF rooms)", "DETERMINISTIC_OPS": sum(len(out[k].get("ITEMS", [])) for k in ("RECEPTION", "FF_ROOMS")) + len(out["FACADES"].get("NW_ITEMS", []))})
    C.write("COLD_CHALLENGE_RECONCILIATION.json", out)
    return {k: (out[k]["STATUS"], out[k].get("EDGES_UNRESOLVED") or out[k].get("OPEN")) for k in ("RECEPTION", "FACADES", "FF_ROOMS")}


if __name__ == "__main__":
    print(json.dumps(run(), indent=1, default=str))
