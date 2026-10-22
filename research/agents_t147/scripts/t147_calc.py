"""T-147: Alsenan ceilings per room and surface type (research only, NOT engine code; standard library only).

Input: rooms_geom.json (made by the scratchpad overlay of the architectural room regions and the roof-slab faces of
T-139, with the T-110 beam register depths; areas and lengths only, no coordinates). Output: CEILINGS_T147.csv (one row
per room and surface type), CEILINGS_T147_FLOORS.csv (totals per floor and type, with the freelancer's ceiling rows),
summary.json.

Rules (cited per row):
  Q-57 A mod   gypsum decor ceiling = finishing + paint, no cement plaster; measure apart: horizontal gypsum,
               moisture-resistant board where specified, other boards, vertical bulkhead faces, cove returns / drops,
               paintable surfaces, concrete-ceiling plaster only where specified; not blindly the floor area.
  Q-48 A       decor ceiling 0.15 m below the beam ("floor height minus beam minus ceiling 15 cm").
  Q-43 / G1    owner manual line: ceiling plane = slab top - 0.60 - 0.15 (his 0.60 beam allowance and 0.15 decor).
  Q-52 C mod   a beam lowers the ceiling only where it crosses the room; drawing-derived ceiling HELD / PROVISIONAL.
  Q-61 C       CONFLICT and HELD beam members stay held, never the larger value.
  Q-44 A       dome positions are open skylights (ring beam stays): no ceiling plane is drawn under the opening.
  Q-68 C       soffits over outside air kept apart (T-127), finish HELD.
  D-40         no reflected ceiling plan, no ceiling level: drawing-derived values PROVISIONAL.
  UP-QTY-STATUS-001  held is never 0.
Usage: python3 -I t147_calc.py rooms_geom.json <out_dir>
"""
import csv
import json
import os
import sys

FIXTURE = [  # synthetic villa (NOT Alsenan): hand-calculated expectations in SELFTEST below
    {"id": "F-01", "floor": "GF", "name": "fixture hall 5.00 x 4.00", "kind": "DRY", "dxf_area": 19.98, "ref_area": 20.0,
     "ref_src": "printed 500 x 400", "perimeter": 18.0, "above": {},
     "beams": [
        {"face": "x1", "cls": "BEAM", "piece_m2": 1.2, "w": 0.30, "l": 4.0, "free_edge_m": 8.0, "member": "M1", "mark": "BX",
         "b": "0.30", "D": "0.85", "status": "CALCULATED", "texts": []},
        {"face": "x2", "cls": "BEAM_OR_COLUMN", "piece_m2": 0.5, "w": 0.10, "l": 5.0, "free_edge_m": 5.0, "member": "M2",
         "mark": "BE", "b": "0.30", "D": "0.75", "status": "CALCULATED", "texts": []},
        {"face": "x3", "cls": "BEAM_OR_COLUMN", "piece_m2": 0.8, "w": 0.20, "l": 4.0, "free_edge_m": 8.0, "member": "M3",
         "mark": "BS", "b": "0.20", "D": "0.50", "status": "CALCULATED", "texts": []},
        {"face": "x4", "cls": "BEAM_OR_COLUMN", "piece_m2": 0.4, "w": 0.20, "l": 2.0, "free_edge_m": 4.0, "member": "M4",
         "mark": "BC", "b": "0.25 schedule / 0.2 drawn", "D": "0.75", "status": "CONFLICT", "texts": []},
        {"face": "x5", "cls": "BEAM_OR_COLUMN", "piece_m2": 0.05, "w": 0.2, "l": 0.25, "free_edge_m": 0.5, "member": None,
         "mark": None, "b": None, "D": None, "status": "NO REGISTER ROW", "texts": []}],
     "openings": [{"face": "d1", "cls": "DOME_OPENING+RING", "m2": 3.6, "open_m2": 3.0, "ring_m2": 0.6,
                   "edge_in_room_m": 7.0, "open_edge_in_room_m": 6.0, "texts": []}]},
    {"id": "F-02", "floor": "GF", "name": "fixture bath 2.00 x 2.00", "kind": "WET", "dxf_area": 4.0, "ref_area": 4.0,
     "ref_src": "printed", "perimeter": 8.0, "above": {}, "beams": [], "openings": []},
    {"id": "F-03", "floor": "1F", "name": "fixture living with a light well", "kind": "DRY", "dxf_area": 30.0, "ref_area": None,
     "ref_src": "-", "perimeter": 24.0, "above": {}, "beams": [],
     "openings": [{"face": "v1", "cls": "VOID+STAIR", "m2": 5.0, "edge_in_room_m": 9.0, "texts": []},
                  {"face": "s1", "cls": "STAIR", "m2": 1.0, "edge_in_room_m": 4.0, "texts": []}]},
    {"id": "F-04", "floor": "1F", "name": "fixture unlabelled face", "kind": "HELD", "dxf_area": 1.5, "ref_area": None,
     "ref_src": "-", "perimeter": 5.0, "above": {}, "beams": [], "openings": []},
]
SELFTEST = {  # (room, surface prefix) -> expected quantity, by hand
    ("F-01", "horizontal decor"): 17.0,            # 20.00 - 3.00 dome opening
    ("F-01", "under the open dome"): 3.0,
    ("F-01", "bulkhead vertical faces, owner method, total"): 2.75,   # 8.0 x 0.25 + 5.0 x 0.15
    ("F-01", "bulkhead undersides"): 1.7,         # 1.2 + 0.5
    ("F-01", "bulkhead vertical faces, drawing-derived"): 11.19,  # 8 x 0.69 + 5 x 0.59 + 8 x 0.34
    ("F-01", "bulkhead faces on held"): 4.0,
    ("F-01", "ceiling edge at an opening"): 6.0,
    ("F-01", "cove / cornice"): 18.0,
    ("F-01", "paintable gypsum"): 19.75,
    ("F-02", "horizontal decor"): 4.0,
    ("F-02", "paintable gypsum"): 4.0,
    ("F-03", "no ceiling here"): 5.0,
    ("F-03", "horizontal decor"): 24.0,           # 30 - 5 - 1
    ("F-03", "ceiling edge at an opening"): 9.0,
    ("F-04", "plan area (space not identified"): 1.5,
}
selftest = sys.argv[1] == "--selftest"
GEOM, OUT = (None, sys.argv[2]) if selftest else (sys.argv[1], sys.argv[2])
os.makedirs(OUT, exist_ok=True)
R = json.loads(json.dumps(FIXTURE)) if selftest else json.load(open(GEOM))

SLAB_T = 0.16            # ST p.8 general note 18 (all roof slabs 16 cm unless stated); T-139 read it by eye
OWNER_ALLOW = 0.60       # owner Q-43 beam allowance in his manual line
DECOR = 0.15             # owner Q-48 A decor depth under a beam
EDGE_STEP_W = 0.06       # beam piece narrower than this = beam face within 6 cm of the wall face (listed apart)

# freelancer ceiling rows (FIN workbook, decor sheet, rows 13-29 and 42-63; comparison only, Q-57)
FL = {
    "GF": {"DRY": 197.33, "WET": 35.48, "cornice_dry": 127.13, "cornice_wet": 77.33},
    "1F": {"DRY": 112.96, "WET": 30.91, "cornice_dry": 122.82, "cornice_wet": 57.53},
    "2F": {"DRY": 27.28, "WET": 5.62, "cornice_dry": 32.90, "cornice_wet": 9.75},
}
FL_ROOM = {  # freelancer row -> our room ids (only where the row names the same room)
    "GF-01": ("dewaneya", 24.84), "GF-04": ("driver", 7.87), "GF-15": ("master bed room", 16.66),
    "GF-06": ("kitchen", 9.55), "GF-07+GF-08": ("reception + dining 137.50 + entrance 10.46", 147.96),
    "1F-07": ("laundry", 10.00), "1F-13": ("living", 38.96), "2F-03": ("maid room", 19.58),
    "2F-02": ("roof-floor bath", 5.62),
    "1F-01+1F-04+1F-10+1F-11": ("bed rooms 1-4", 74.00),
}

rows = []
def add(r, surface, qty, unit, method, status, basis, note=""):
    rows.append({"ROW": f"{r['id']}.{len([x for x in rows if x['ROOM_ID'] == r['id']]) + 1:02d}",
                 "FLOOR": r["floor"], "ROOM_ID": r["id"], "ROOM": r["name"], "KIND": r["kind"], "SURFACE": surface,
                 "QTY": "" if qty is None else round(qty, 3), "UNIT": unit, "METHOD": method, "STATUS": status,
                 "BASIS": basis, "NOTE": note})

def depth(b):
    try:
        return float(b["D"])
    except (TypeError, ValueError):
        return None

S = {}
def tot(fl, key, v):
    S.setdefault(fl, {}).setdefault(key, 0.0)
    S[fl][key] += v

for r in R:
    if r["id"] == "ST-2F":   # the 2F part of the shaft has the 2F roof slab over its whole box: a room ceiling
        r["kind"] = "DRY"; r["name"] = "stair hall top, 2F (roof slab over the whole shaft box)"
    fl, kind = r["floor"], r["kind"]
    A_dxf = r["dxf_area"]
    A = r["ref_area"] if r["ref_area"] is not None else A_dxf
    src = r["ref_src"] if r["ref_area"] is not None else "DXF room region (this run)"
    diff = A_dxf - A
    opens = r["openings"]
    no_ceiling = 0.0
    dome_held = 0.0
    edge_open = 0.0
    stair_soffit = 0.0
    for o in opens:
        if o["cls"] == "OPENING":
            no_ceiling += o["m2"]
        elif o["cls"] in ("VOID+STAIR",):
            no_ceiling += o["m2"]; edge_open += o["edge_in_room_m"]
        elif o["cls"] == "STAIR":
            stair_soffit += o["m2"]
        elif o["cls"].startswith("DOME"):
            dome_held += o.get("open_m2", 0.0); edge_open += o.get("open_edge_in_room_m", 0.0)

    if kind in ("STAIR", "SHAFT") and r["id"] != "ST-2F":
        add(r, "plan area of the shaft", A, "m2", "both", "MEASURED", src, f"DXF region {A_dxf:.3f}")
        if stair_soffit:
            add(r, "stair soffit under the flights (not a decor ceiling)", stair_soffit, "m2", "both",
                "HELD", "T-139 STAIR faces; no soffit finish printed (T-091)", "stair finish line, not this table")
        if no_ceiling:
            add(r, "no ceiling: slab opening (lift shaft X box)", no_ceiling, "m2", "both", "MEASURED",
                "T-139 OPENING faces")
        rest = A - stair_soffit - no_ceiling
        if rest > 0.05:
            add(r, "landing / beam soffit pieces inside the shaft", rest, "m2", "both", "HELD",
                "stair ledger (T-111); no finish printed")
        tot(fl, "shaft_" + kind, A)
        continue

    if kind == "HELD":
        add(r, "plan area (space not identified on the plans: no label, no door)", A, "m2", "both", "HELD",
            src, "ceiling type not decidable; area measured, never 0")
        tot(fl, "held_space_m2", A)
        continue

    # --- horizontal ceiling -----------------------------------------------------------------------------------------
    add(r, "plan area under the roof slab (room polygon)", A, "m2", "both", "MEASURED", src,
        f"DXF region {A_dxf:.3f} m2 ({diff:+.3f} vs reference)" if r["ref_area"] is not None else
        "no printed size; DXF wall faces")
    if no_ceiling:
        add(r, "no ceiling here: opening in the slab above (light well with the round stair / lift)", no_ceiling,
            "m2", "both", "MEASURED", "T-139 faces GF-130 / OPENING", "deducted from the ceiling, not 0")
    if stair_soffit:
        add(r, "round-stair flight strips above (stair soffit, not a decor ceiling)", stair_soffit, "m2", "both",
            "HELD", "T-139 STAIR faces; stair finish line", "deducted from the decor ceiling")
    if dome_held:
        add(r, "under the open dome position: no ceiling plane designed", dome_held, "m2", "both", "HELD",
            "Q-44 A open skylight; designer DCR-4 (T-112)", "measured, held for the designer, never 0")
    horiz = A - no_ceiling - stair_soffit - dome_held
    board = ("gypsum board (dry room)" if kind == "DRY" else
             "board type HELD: moisture-resistant only where specified, and no sheet specifies a ceiling board (T-091)")
    st_h = "MEASURED" if kind == "DRY" else "MEASURED (area); board type HELD"
    add(r, "horizontal decor ceiling (gypsum), incl. bulkhead undersides", horiz, "m2", "both", st_h,
        "Q-57 A mod (1); Q-48 A", board)
    tot(fl, f"horiz_{kind}", horiz); tot(fl, "plan_" + kind, A); tot(fl, "dome_held", dome_held)
    tot(fl, "no_ceiling", no_ceiling); tot(fl, "stair_strip", stair_soffit)

    # --- bulkheads ----------------------------------------------------------------------------------------------------
    own_m2 = own_lm = own_under = 0.0
    dwg_m2 = 0.0
    held_lm = 0.0
    held_list = []
    step_m2 = 0.0
    for b in r["beams"]:
        D = depth(b)
        if b["member"] is None:
            if b["cls"] == "BEAM_HELD" or b["piece_m2"] >= 0.1:
                held_lm += b["free_edge_m"]; held_list.append(f"{b['face']} {b['cls']} no depth ({b['free_edge_m']:.2f} m)")
            continue  # beam / column junction piece with no register row (< 0.1 m2): listed in the json only
        if b["status"] in ("CONFLICT", "HELD") or D is None:
            cand = ""
            if D is not None and D > OWNER_ALLOW:
                cand = f", candidate {b['free_edge_m'] * (D - OWNER_ALLOW):.3f} m2 owner method"
            held_lm += b["free_edge_m"]
            held_list.append(f"{b['mark']} {b['member']} {b['status']} {b['b']} x {b['D']} ({b['free_edge_m']:.2f} m{cand})")
            continue
        if D > OWNER_ALLOW:
            h = D - OWNER_ALLOW
            m2 = b["free_edge_m"] * h
            if b["w"] < EDGE_STEP_W:
                step_m2 += m2
            own_m2 += m2; own_lm += b["free_edge_m"]; own_under += b["piece_m2"]
            add(r, f"bulkhead vertical face, owner method: {b['mark']} {b['b']} x {D:.2f} ({b['member']})", m2, "m2",
                "owner manual (Q-43 line, Q-48 A 0.15 under the beam)", "CALCULATED",
                f"free edge {b['free_edge_m']:.3f} m x (D - 0.60) {h:.2f} m; piece {b['w']:.2f} x {b['l']:.2f} m",
                "edge step: beam face within 6 cm of the wall face" if b["w"] < EDGE_STEP_W else
                ("crossing beam (two free sides)" if b["free_edge_m"] > 1.6 * b["l"] else "beam along the room edge"))
        if D > SLAB_T:
            dwg_m2 += b["free_edge_m"] * (D - SLAB_T)
    if own_m2:
        add(r, "bulkhead vertical faces, owner method, total", own_m2, "m2", "owner manual", "CALCULATED",
            f"{own_lm:.3f} m of free beam edge; Q-48 A", f"of which edge steps {step_m2:.3f} m2")
        add(r, "bulkhead undersides (in the horizontal total above), owner method", own_under, "m2",
            "owner manual", "CALCULATED", "beam pieces deeper than 0.60 m inside the room")
    else:
        add(r, "bulkhead vertical faces, owner method", None, "m2", "owner manual", "NONE DRAWN",
            "no registered beam deeper than 0.60 m inside the room (shallower beams sit above the 0.15 decor depth)")
    if dwg_m2:
        add(r, "bulkhead vertical faces, drawing-derived (ceiling 0.15 under the slab soffit)", dwg_m2, "m2",
            "drawing-derived", "PROVISIONAL", "every registered beam piece: free edge x (D - 0.16 slab)",
            "no ceiling level printed (D-40)")
    if held_lm:
        add(r, "bulkhead faces on held / conflict beams", held_lm, "m", "both", "HELD",
            "Q-61 C (never the larger value)", "; ".join(held_list))
    tot(fl, "own_bulk_m2", own_m2); tot(fl, "dwg_bulk_m2", dwg_m2); tot(fl, "held_bulk_lm", held_lm)

    # --- drops, coves, paint, plaster --------------------------------------------------------------------------------
    if edge_open:
        add(r, "ceiling edge at an opening (drop / return)", edge_open, "m", "both", "HELD (height)",
            "Q-57 A mod (5); no edge detail printed", "length measured from the drawn opening edge")
        tot(fl, "edge_open_lm", edge_open)
    closed = r["id"] not in ("GF-07", "GF-08", "GF-14", "1F-13", "2F-01")
    add(r, "cove / cornice run at the wall (if a detail is approved)", r["perimeter"] if closed else None, "m",
        "both", "HELD", "no cove or cornice detail drawn (T-091); never the freelancer's 0.10 m strips",
        "room perimeter at the wall faces" if closed else "open zone: the run is not closed")
    if closed:
        tot(fl, f"cove_lm_{kind}", r["perimeter"])
    paint = horiz + own_m2
    add(r, "paintable gypsum surfaces, owner method (horizontal + bulkhead faces)", paint, "m2", "owner manual",
        "CALCULATED" if kind == "DRY" else "CALCULATED (paint); board HELD",
        "Q-57 A mod (6): paint system on gypsum; moisture-resistant board may still be painted",
        "coves and opening drops HELD, not included")
    tot(fl, f"paint_own_{kind}", paint)
    add(r, "concrete ceiling plaster", None, "m2", "both", "NOT SPECIFIED",
        "Q-57 A mod (7): only where specifically required; no sheet requires it (T-091 census)")

if selftest:
    bad = 0
    for (rid, pre), exp in SELFTEST.items():
        got = [x["QTY"] for x in rows if x["ROOM_ID"] == rid and x["SURFACE"].startswith(pre)]
        ok = len(got) == 1 and abs(float(got[0]) - exp) < 0.0015
        bad += not ok
        print("PASS" if ok else "FAIL", rid, pre, got, exp)
    # held never 0: every HELD row carries a quantity or names why it has none
    for x in rows:
        if x["STATUS"].startswith("HELD") and x["QTY"] == 0:
            bad += 1; print("FAIL held shown as 0", x["ROW"])
    print("selftest failures:", bad)
    sys.exit(1 if bad else 0)

# --- floors -------------------------------------------------------------------------------------------------------
fr = []
for fl in ("GF", "1F", "2F"):
    s = S.get(fl, {})
    f = FL[fl]
    for kind in ("DRY", "WET"):
        h = s.get(f"horiz_{kind}", 0.0)
        p = s.get(f"paint_own_{kind}", 0.0)
        fr.append({"FLOOR": fl, "KIND": kind, "PLAN_M2": round(s.get(f"plan_{kind}", 0.0), 3),
                   "HORIZONTAL_GYPSUM_M2": round(h, 3), "PAINT_OWNER_M2": round(p, 3),
                   "FREELANCER_DECOR_M2": f[kind], "HORIZ_MINUS_FL_M2": round(h - f[kind], 3),
                   "HORIZ_VS_FL_PCT": round(100 * (h - f[kind]) / f[kind], 1),
                   "COVE_RUN_CLOSED_ROOMS_M": round(s.get(f"cove_lm_{kind}", 0.0), 3),
                   "FREELANCER_CORNICE_M": f["cornice_" + kind.lower()]})
    fr.append({"FLOOR": fl, "KIND": "BOTH", "PLAN_M2": "", "HORIZONTAL_GYPSUM_M2": "",
               "PAINT_OWNER_M2": "", "FREELANCER_DECOR_M2": "",
               "HORIZ_MINUS_FL_M2": "", "HORIZ_VS_FL_PCT": "",
               "COVE_RUN_CLOSED_ROOMS_M": "",
               "FREELANCER_CORNICE_M": "",
               "NOTE": (f"owner-method bulkhead faces {s.get('own_bulk_m2', 0):.3f} m2; drawing-derived "
                        f"{s.get('dwg_bulk_m2', 0):.3f} m2 PROVISIONAL; held bulkhead edges {s.get('held_bulk_lm', 0):.3f} m; "
                        f"dome openings HELD {s.get('dome_held', 0):.3f} m2; no ceiling (light well / lift) "
                        f"{s.get('no_ceiling', 0):.3f} m2; stair strips {s.get('stair_strip', 0):.3f} m2; "
                        f"opening edges {s.get('edge_open_lm', 0):.3f} m; unidentified spaces {s.get('held_space_m2', 0):.3f} m2")})

with open(f"{OUT}/CEILINGS_T147.csv", "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
keys = ["FLOOR", "KIND", "PLAN_M2", "HORIZONTAL_GYPSUM_M2", "PAINT_OWNER_M2", "FREELANCER_DECOR_M2",
        "HORIZ_MINUS_FL_M2", "HORIZ_VS_FL_PCT", "COVE_RUN_CLOSED_ROOMS_M", "FREELANCER_CORNICE_M", "NOTE"]
with open(f"{OUT}/CEILINGS_T147_FLOORS.csv", "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=keys); w.writeheader()
    for x in fr:
        w.writerow({k: x.get(k, "") for k in keys})

# room-to-row comparison
byid = {r["id"]: r for r in R}
def horiz_of(i):
    return sum(x["QTY"] for x in rows if x["ROOM_ID"] == i and x["SURFACE"].startswith("horizontal decor"))
def plan_of(i):
    return sum(x["QTY"] for x in rows if x["ROOM_ID"] == i and x["SURFACE"].startswith("plan area under"))
cmp_rows = []
for k, (lab, v) in FL_ROOM.items():
    ids = k.split("+")
    h = sum(horiz_of(i) for i in ids); p = sum(plan_of(i) for i in ids)
    cmp_rows.append({"ROOMS": k, "FREELANCER_ROW": lab, "FREELANCER_M2": v, "PLAN_M2": round(p, 3),
                     "HORIZONTAL_M2": round(h, 3), "HORIZ_MINUS_FL": round(h - v, 3),
                     "PCT": round(100 * (h - v) / v, 1)})
with open(f"{OUT}/CEILINGS_T147_VS_FREELANCER.csv", "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(cmp_rows[0].keys())); w.writeheader(); w.writerows(cmp_rows)
summ = {"floors": S, "freelancer": FL, "compare": cmp_rows}
json.dump(summ, open(f"{OUT}/summary.json", "w"), indent=1)
for x in fr:
    print(x)
for c in cmp_rows:
    print(c)
