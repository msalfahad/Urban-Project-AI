"""T-211 (V3.0.9a): the project inputs of ARCH_TAKEOFF_V3.0.9 (URBAN_V309_INPUTS_V1) for the development villa.
Research code; it reads the merged files as committed and changes none of their quantities except where a later
checker-merged piece names the change (the two arched windows, below). Values, room ids and BOQ ids only (no
coordinates, no names, no drawing content).

WALL_FINISH (internal plaster and paint m2, room by room):
  T-128 r3 (MERGED a6ac2c66, Verifier 2026-10-22 18:05 UTC): ROOMS_T128_R3.csv / OPENINGS_T128_R3.csv, both methods
  room by room. The owner manual method is the figure of record (owner heights G1: GF 3.65, 1F / 2F 3.35, Q-43 /
  Q-48 A; door head 2.20 where none is printed, Q-55 C; every opening by its own area inside the wall height, Q-73);
  the drawing-derived method (floor to floor - slab - build-up b 0 .. 0.10 - decor 0.15; plaster may run to the
  soffit) is carried beside on every line. The owner net is re-derived here from the face length, the owner height
  and the opening table and asserted equal to the CSV (2 decimals), so a transcription slip cannot enter.
  Scope of this package: the DRY room faces and the stair shaft (the faces that take plaster + paint). The 17 WET
  rooms take wall tile to the decor ceiling (Q-48 A; UP-FIN-PAINT-001 no paint over full-height tile): their
  candidate lines are NOT touched here (V3.0.9b with the wet-wall tile records of T-209).
  Statuses (WORKFLOW_CONTROLS s.5, as the Checker ruled on T-128 r3): GF-15 and 1F-11 checker-VERIFIED (own walk of
  the drawn faces; GF-15 at 02:40 / 16:11, 1F-11 at 18:05; 1F-12, the third, is a wet room), the owner heights stay
  ASSUMED - OWNER-APPROVED on them; 1F-01 ASSUMED - OWNER-APPROVED; every room with an opening whose head is not
  printed is a HELD range (lower = full band deducted, upper = none); the annex rooms HELD on the roof datum (G2,
  owner 3.15 PROVISIONAL shown as information).
  Arched windows W15 / W16 (1F-13): T-227 r2 (MERGED ebce3d97, Verifier 2026-10-23 21:05 UTC) measured the true
  opening outline 4.3629 m2 each (jamb rectangle + arch segment, crown 3.00 above the floor; the T-144 head 3.10 is the
  crown of the 0.10 surround band); T-128 deducted W15 1.55 x 3.10 = 4.805 and held W16. Until T-238 (fix of the merged
  opening ledgers) merges, the Lead's ruling (board 20:10) applies: each is deducted as a HELD range 4.3629 .. 4.805,
  never 4.805 alone. 1F-13 net: 109.75 .. 118.29 (T-128) -> 110.13 .. 114.37 m2.
  Stair shaft ST-01: T-173 (MERGED 8b4d2c83, Verifier 2026-10-22 17:17 UTC, PARTIALLY VERIFIED 1 / 4 faces) supersedes
  the T-128 storey-interval rows for the shaft (actual exposed geometry, plaster and paint apart); no owner case for a
  shaft (Q-72 investigation): the owner room heights storey by storey (142.22 m2 gross) are shown beside, never a
  measurement. GF and 1F parts: HELD ranges (net_lo of the LO build-up case .. net_hi of the HI case, every held item
  bounded). 2F part (to the roof): HELD without a figure: the Checker's D-T173-1 (roof panel prints T 18, the ledger
  took the 0.16 general note) and the roof B3 contact must be applied before it is wired.
  Pantry (T-128 GF-07, open side to the dining): T-128 classes it WET (wall tile), the candidate's open-room lines
  class it dry; its face sits inside two candidate rooms. Its wall finish is a classification change and the wet-tile
  record is V3.0.9b: here a HELD line without a figure, never 0 and never silently dropped.
  Room identity (candidate room id <- T-128 row): own check of this run's ARCH_ROOMS polygons against the T-128 / T-147
  selection points and clip boxes (walk_r2.py): 1:1 for 11 rooms (area equal to 0.003 m2); the 1F open zone
  1F-R78C367 75.983 = 1F-13 63.011 + shaft box 12.972; the 2F stair room 2F-R4D1B62 18.600 = 2F-01 5.626 + shaft box
  12.974; the GF open room GF-RC99C2A (126.928, 8.925 of it in the pantry box) + GF-RC06FED (2.800, inside the pantry
  box) = T-128 GF-08 dining + GF-07 pantry.
"""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
T128 = ROOT / "research/agents_t128"
T173 = ROOT / "research/agents_t173"
T227 = ROOT / "research/agents_t227"
CODES = ("FIN.PLASTER", "FIN.PAINT")
H_OWNER = {"GF_MAIN": 3.65, "1F": 3.35, "2F": 3.35}
DOOR_H = 2.20
W_ARCH = 4.3629                 # T-227 r2 true outline (Checker 4.362)
W_BAND = 4.805                  # 1.55 x 3.10 (the band crown rectangle the merged ledgers carry)

# candidate room ids (this run) per T-128 row; the first is the line's room
ROUTE = {"GF-01": ["GF-R7512EA"], "GF-04": ["GF-R51E127"], "GF-08": ["GF-RC99C2A"],
         "GF-07": ["GF-RC06FED", "GF-RC99C2A"], "GF-15": ["GF-R75FBAE"], "ST-GF": ["GF-R31F8AE"],
         "1F-01": ["1F-RB72F22"], "1F-04": ["1F-RED0D19"], "1F-10": ["1F-R0E919A"], "1F-11": ["1F-R3CFCFD"],
         "1F-13": ["1F-R78C367"], "ST-1F": ["1F-R78C367"], "2F-03": ["2F-R1DB2D2"], "2F-01": ["2F-R4D1B62"],
         "ST-2F": ["2F-R4D1B62"]}
VERIFIED = {"GF-15": "Verifier 2026-10-22 02:40 + 16:11 (own walk of the drawn faces, owner gross 78.60 / net 56.02)",
            "1F-11": "Verifier 2026-10-22 18:05 (own polygon from layer 1 / W lines, contour 22.1507 m, net 59.447)"}
# the candidate's room-face lines of the scope rooms (V3.0.8 = released route: every one held without a figure)
SUPERSEDE = [("GF-R7512EA", "GF"), ("GF-R51E127", "GF"), ("GF-RC99C2A", "GF"), ("GF-RC06FED", "GF"),
             ("GF-R75FBAE", "GF"), ("1F-RB72F22", "1F"), ("1F-RED0D19", "1F"), ("1F-R0E919A", "1F"),
             ("1F-R3CFCFD", "1F"), ("1F-R78C367", "1F"), ("2F-R1DB2D2", "2F")]
STAIR_HALLS = [("GF-R31F8AE", "GF"), ("2F-R4D1B62", "2F")]
# hand totals of this package (m2, per item code; the two codes carry the same owner figures, the shaft parts differ
# only where T-173 gives plaster and paint apart, and they do not on GF / 1F): released GF-15 56.0131 + 1F-01 51.415
# + 1F-11 59.4511 = 166.8792; bounded low 152.0505 + 49.1375 + 48.94 + 110.1335 + 55.555 + 22.6502 + 48.52 + 42.48 =
# 529.4667, high 178.805 + 54.33 + 52.29 + 114.3677 + 59.575 + 26.0002 + 62.01 + 47.67 = 595.0479; no figure: the two
# annex rooms, the shaft below the roof and the pantry = 4
DECLARED = {"released": 166.8792, "bounded": [529.4667, 595.0479], "unquantified": 4}


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def _f(x):
    return None if x in ("", None) else float(x)


def _rng(s):
    """'12.3' -> (12.3, 12.3); '1 .. 2' -> (1, 2); 'HELD' -> None"""
    s = (s or "").strip()
    if not s or s.startswith("HELD"):
        return None
    if ".." in s:
        a, b = s.split("..")
        return float(a), float(b)
    return float(s), float(s)


def rows():
    with open(T128 / "ROOMS_T128_R3.csv", encoding="utf-8") as f:
        rr = {r["ROW"]: r for r in csv.DictReader(f)}
    ops = {}
    with open(T128 / "OPENINGS_T128_R3.csv", encoding="utf-8") as f:
        for o in csv.DictReader(f):
            ops.setdefault(o["ROOM_ROW"], []).append(o)
    return rr, ops


def owner_deductions(rid, ops, H):
    """the T-128 opening table as owner-method deductions (calc_r2.py `nets`: known band w x (min(head, H) - sill),
    a held opening 0 .. w x H); the two arched windows as the Lead's HELD range (T-238)."""
    out = []
    for o in ops:
        if o["CLASS"] in ("virtual", "wall"):
            continue
        w, sill, head = float(o["WIDTH_M"]), _f(o["SILL_M"]), _f(o["HEAD_M"])
        name = o["OPENING"]
        if rid == "1F-13" and name.startswith(("W15", "W16")):
            out.append({"opening": name, "range": [W_ARCH, W_BAND],
                        "basis": "arched window: true outline 4.3629 (T-227 r2, Checker 4.362) .. band rectangle "
                                 "1.55 x 3.10 = 4.805 (merged ledgers); HELD until T-238 (Lead 2026-10-23 20:10)"})
        elif sill is None or head is None:
            out.append({"opening": name, "range": [0.0, round(w * H, 6)], "basis": o["STATUS"]})
        else:
            out.append({"opening": name, "m2": round(w * max(0.0, min(head, H) - max(sill, 0.0)), 6),
                        "basis": o["STATUS"]})
    return out


def _net(gross, deds):
    lo = hi = gross
    for d in deds:
        if "m2" in d:
            lo -= d["m2"]
            hi -= d["m2"]
        else:
            lo -= d["range"][1]
            hi -= d["range"][0]
    return lo, hi


def room_record(rid, r, ops, code):
    floor = rid.split("-")[0]
    face = float(r["FACE_M"])
    dwg = {"paint_tile_height_m": r["DWG_PAINT_TILE_H_M"], "plaster_top_m": r["DWG_PLASTER_H_TOP_M"],
           "gross_m2": r["DWG_GROSS_M2"], "net_m2": r["DWG_NET_M2"],
           "plaster_gross_high_m2": r["DWG_PLASTER_GROSS_HI_M2"] or None, "net_status": r["DWG_STATUS"],
           "gross_status": r["DWG_GROSS_STATUS"], "source": "T-128 r3 ROOMS_T128_R3.csv"}
    if rid == "1F-13":
        dwg["note"] = ("the T-128 drawing-derived net deducts W15 at 4.805 and holds W16; the arched-window range of "
                       "the owner method (T-238) applies to it in the same way")
    base = {"room": rid, "item_code": code, "floor": floor, "route_rooms": ROUTE[rid], "drawing_method": dwg,
            "guard_element": {"element_id": f"ROOM_FACE:{rid}", "part": code.split(".")[-1]},
            "info": {"t128_owner_status": r["OWNER_STATUS"], "t128_owner_net_m2": r["OWNER_NET_M2"],
                     "freelancer_gross_same_room_m2": r["FREELANCER_GROSS_M2"] or None,
                     "contour_m": float(r["CONTOUR_M"]), "open_sides_m": float(r["OPEN_SIDES_M"] or 0),
                     "paintable_length_m": float(r["PAINTABLE_M"])}}
    if r["ZONE"] == "GF_ANNEX":
        return dict(base, state="UNQUANTIFIED", evidence_status="HELD",
                    reasons=["annex room under a finished roof mark (+4.30): the owner wall height for the annex is "
                             "not established (G2; owner 3.15 m shown as OWNER MANUAL METHOD - PROVISIONAL), the "
                             "drawing-derived height rests on the unprinted roof build-up (DCR-6)"],
                    owner_method={"height_m": 3.15, "status": "PROVISIONAL (G2)", "face_m": face,
                                  "gross_information_m2": float(r["OWNER_GROSS_M2"]),
                                  "net_information_m2": r["OWNER_NET_M2"]})
    H = H_OWNER[r["ZONE"] if r["ZONE"] == "GF_MAIN" else floor]
    if abs(float(r["OWNER_H_M"]) - H) > 1e-9:
        raise ValueError(f"{rid}: owner height {r['OWNER_H_M']} != G1 {H}")
    gross = round(face * H, 6)
    deds = owner_deductions(rid, ops, H)
    lo, hi = _net(gross, deds)
    want = _rng(r["OWNER_NET_M2"])
    if rid != "1F-13" and (abs(lo - want[0]) > 0.006 or abs(hi - want[1]) > 0.006):
        raise ValueError(f"{rid}: owner net {lo:.4f} .. {hi:.4f} != T-128 {r['OWNER_NET_M2']}")
    if abs(gross - float(r["OWNER_GROSS_M2"])) > 0.006:
        raise ValueError(f"{rid}: owner gross {gross} != T-128 {r['OWNER_GROSS_M2']}")
    om = {"height_m": H, "height_source": "G1 (OWNER_RECONCILIATION_2026-10-20), Q-43 / Q-48 A", "face_m": face,
          "gross": gross, "deductions": deds}
    held = [d["opening"] for d in deds if "range" in d]
    formula = (f"{face} m face x {H} m owner height = {round(gross, 4)} m2, less {len(deds)} opening(s) by their own "
               f"area (Q-73; door head 2.20 Q-55 C where none is printed)")
    if not held:
        ev = "VERIFIED" if rid in VERIFIED else "ASSUMED - OWNER-APPROVED"
        return dict(base, state="RELEASED", value=round(lo, 4), evidence_status=ev, verified_by=VERIFIED.get(rid),
                    assumption="owner wall height G1 (Q-43 / Q-48 A) and door head 2.20 (Q-55 C): ASSUMED - "
                               "OWNER-APPROVED", owner_method=om, formula=formula)
    return dict(base, state="BOUNDED", range=[round(lo, 4), round(hi, 4)], evidence_status="HELD",
                reasons=[f"net is a range: {', '.join(held)} not printed / not settled (lower bound deducts each at its "
                         "largest, upper bound none)"], owner_method=om, formula=formula,
                range_basis="owner manual method; held openings bounded")


def shaft_records(code):
    d = json.loads((T173 / "SHAFT_T173.json").read_text(encoding="utf-8"))
    fin = "plaster" if code == "FIN.PLASTER" else "paint"
    cases = [s for s in d["summary"] if s["finish"] == fin]
    om_note = ("no owner case for a stair shaft (Q-72 investigation, T-173): the owner room heights applied storey by "
               "storey give 142.22 m2 gross for the whole shaft, shown beside, never a measurement")
    out = []
    for rid, i in (("ST-GF", 0), ("ST-1F", 1), ("ST-2F", 2)):
        st = [c["storeys"][i] for c in cases]
        dwg = {"source": "T-173 SHAFT_T173.json (actual exposed geometry)", "finish": fin,
               "by_case": {c["case"]: {"gross": c["storeys"][i]["gross"], "net_lo": c["storeys"][i]["net_lo"],
                                       "net_hi": c["storeys"][i]["net_hi"]} for c in cases},
               "status": "geometry DRAWING-CONFIRMED (west face gross VERIFIED by the Checker); build-up and roof "
                         "datum PROVISIONAL; 7 items HELD with ranges"}
        base = {"room": rid, "item_code": code, "floor": rid.split("-")[1], "route_rooms": ROUTE[rid],
                "drawing_method": dwg, "owner_method": {"note": om_note},
                "guard_element": {"element_id": f"ROOM_FACE:{rid}", "part": code.split(".")[-1]}}
        if rid == "ST-2F":
            out.append(dict(base, state="UNQUANTIFIED", evidence_status="HELD",
                            reasons=["the shaft part below the roof is wired only after the Checker's T-173 "
                                     "corrections: the roof panel over the shaft prints T 18 (the ledger used the 0.16 "
                                     "general note, D-T173-1) and the roof B3 downstand contact on two faces"]))
            continue
        lo, hi = min(s["net_lo"] for s in st), max(s["net_hi"] for s in st)
        out.append(dict(base, state="BOUNDED", range=[lo, hi], evidence_status="HELD",
                        reasons=["shaft faces: floor build-up b 0 .. 0.10 and the held contacts / openings (winder "
                                 "turn, beam ends at the stair head, two window heads and a doorless passage head not "
                                 "printed) bound the net (T-173 s.1)"],
                        range_basis="T-173 drawing-derived: LO case net_lo .. HI case net_hi"))
    return out


def pantry_record(r, code):
    return {"room": "GF-07", "item_code": code, "floor": "GF", "route_rooms": ROUTE["GF-07"], "state": "UNQUANTIFIED",
            "evidence_status": "HELD",
            "reasons": ["pantry face open to the dining: T-128 classes it WET (wall tile to the decor ceiling, Q-48 A / "
                        "UP-WET-001), the candidate's open-room lines classed it dry; the wall-tile record is V3.0.9b "
                        "and whether plaster is laid under that tile is not an owner rule yet: held, never 0"],
            "owner_method": {"note": "WET room: tile, not plaster / paint", "tile_gross_information_m2":
                             r["OWNER_GROSS_M2"], "tile_net_information_m2": r["OWNER_NET_M2"]},
            "drawing_method": {"gross_m2": r["DWG_GROSS_M2"], "net_m2": r["DWG_NET_M2"],
                               "source": "T-128 r3 ROOMS_T128_R3.csv (wet-tile height)"},
            "guard_element": {"element_id": "ROOM_FACE:GF-07", "part": code.split(".")[-1]}}


def supersede_lines():
    out = []
    for code in CODES:
        fin = code.split(".")[-1].lower()
        for rid, fl in SUPERSEDE:
            out.append({"element_id": f"{rid}:{fin}", "floor": fl, "item_code": code, "carried": "NO_FIGURE",
                        "why": f"the same room wall face, measured room by room by T-128 r3 ({fin}; owner manual "
                               "method with the drawing-derived beside)"})
        for rid, fl in STAIR_HALLS:
            out.append({"element_id": f"{rid}:stair hall {fin}", "floor": fl, "item_code": code, "carried": "NO_FIGURE",
                        "why": f"the stair-hall faces = the T-173 shaft faces (+ the 2F lobby face of T-128 on "
                               f"2F-R4D1B62), {fin}"})
    return out


def wall_finish(project_id=None):
    rr, ops = rows()
    recs = []
    for code in CODES:
        for rid in ("GF-01", "GF-04", "GF-08", "GF-15", "1F-01", "1F-04", "1F-10", "1F-11", "1F-13", "2F-03", "2F-01"):
            recs.append(room_record(rid, rr[rid], ops.get(rid, []), code))
        recs.extend(shaft_records(code))
        recs.append(pantry_record(rr["GF-07"], code))
    rooms = sorted({x for r in recs for x in r["route_rooms"]})
    src = {"file": "research/agents_t128/ROOMS_T128_R3.csv", "sha256": sha(T128 / "ROOMS_T128_R3.csv"),
           "task": "T-128 r3", "merge_commit": "a6ac2c66", "checker_run": "Verifier 2026-10-22 18:05 UTC"}
    sources = [{"file": "research/agents_t128/OPENINGS_T128_R3.csv", "sha256": sha(T128 / "OPENINGS_T128_R3.csv"),
                "task": "T-128 r3", "merge_commit": "a6ac2c66", "checker_run": "Verifier 2026-10-22 18:05 UTC"},
               {"file": "research/agents_t173/SHAFT_T173.json", "sha256": sha(T173 / "SHAFT_T173.json"),
                "task": "T-173", "merge_commit": "8b4d2c83", "checker_run": "Verifier 2026-10-22 17:17 UTC"},
               {"file": "research/agents_t227/summary.json", "sha256": sha(T227 / "summary.json"),
                "task": "T-227 r2", "merge_commit": "ebce3d97", "checker_run": "Verifier 2026-10-23 21:05 UTC"}]
    return {"piece": "WALL_FINISH", "item_codes": list(CODES), "unit": "m2", "source": src, "sources": sources,
            "scope": {"floors": ["GF", "1F", "2F"], "rooms": rooms, "supersede_lines": supersede_lines(),
                      "other_elements": []},
            "records": recs, "declared_totals": {c: DECLARED for c in CODES}}


def inputs(project_id=None):
    import sys
    sys.path.insert(0, str(ROOT / "research" / "agents_t193"))
    import t193_inputs as L7   # noqa: E402  (the V3.0.7 guard inputs, unchanged, as V3.0.8)
    g = dict(L7.inputs(project_id)["guard"], new_records=[])
    return {"schema": "URBAN_V309_INPUTS_V1", "project": project_id, "pieces": [wall_finish(project_id)], "guard": g}


if __name__ == "__main__":
    doc = wall_finish()
    for r in doc["records"]:
        print(r["item_code"], r["room"], r["state"], r.get("value"), r.get("range"), r["evidence_status"])
