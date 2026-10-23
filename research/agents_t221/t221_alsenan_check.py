"""T-221 on the development villa: the FFL -> structural-top relation of the zones T-214 held (roofs / terraces, wet
rooms, sunken panels), the falls rise of every roof with drawn outlets, the parapet bound, the section-cut search for wet
rooms and the D-44 sheet-by-sheet record. Reads ALSENAN_ROOF_INPUT.json (local metres, Drive titles / views only).

Run (Python 3.11, repository root):  python3 -I research/agents_t221/t221_alsenan_check.py [--write]
--write regenerates research/agents_t221/summary.json; tests/t221_roof_falls checks it byte for byte.
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import roof_falls_v1 as R  # noqa: E402

STEP = 0.05


def _outline(z):
    pts = []
    for p in z["outline"]:
        if p == "ARC":
            a = z["outline_arc_corner"]
            cx, cy = a["centre"]
            r = a["radius"]
            f, t = a["from"], a["to"]
            a0 = math.atan2(t[1] - cy, t[0] - cx)
            a1 = math.atan2(f[1] - cy, f[0] - cx)
            for i in range(1, 8):
                ang = a0 + (a1 - a0) * i / 8
                pts.append([round(cx + r * math.cos(ang), 4), round(cy + r * math.sin(ang), 4)])
        else:
            pts.append(p)
    return pts


# Section-cut search for wet rooms (closes T-214 s.8 item 1). Cut lines read on the DWF plan views (the dashed line
# between the section markers), wet-room walls from the same views; clearance = distance from the cut line to the
# nearest wet-room wall face, metres.
SECTION_CUTS = [
    {"floor": "GF", "section": "A-A", "cut": "x line through the stair and the +0.30 landing",
     "nearest_wet_room": "W.C (north group, west wall face)", "clearance_m": 0.58, "cuts_wet_room": False},
    {"floor": "GF", "section": "B-B", "cut": "y line through dining / saloon",
     "nearest_wet_room": "Wash / W.C (south group, north wall)", "clearance_m": 1.07, "cuts_wet_room": False},
    {"floor": "1F", "section": "A-A", "cut": "x line through the stair / void",
     "nearest_wet_room": "master BATH (south pair, east wall)", "clearance_m": 1.92, "cuts_wet_room": False},
    {"floor": "1F", "section": "B-B", "cut": "y line through the bedrooms / living area",
     "nearest_wet_room": "BATH (sea side, south wall)", "clearance_m": 0.93, "cuts_wet_room": False},
    {"floor": "2F", "section": "A-A", "cut": "x line through the stair flight",
     "nearest_wet_room": "W.C (wall shared with the stair)", "clearance_m": 0.235, "cuts_wet_room": False},
    {"floor": "2F", "section": "B-B", "cut": "y line south of the 2F block (terrace only)",
     "nearest_wet_room": "none on the cut side", "clearance_m": None, "cuts_wet_room": False},
]

# D-44 (consultant row 2): every sheet that could show B15 20 x 120 at the water tank as an upstand or a downstand.
D44_RECORD = [
    {"sheet": "ST7757.pdf p.6 SECOND FLOOR ROOF SLAB", "view": "plan", "finding":
     "B15 drawn on the street-side edge of the 'WATER TANK PLACE' panel (T18, 7/6 bars T&B) in the same double-line style "
     "as every other beam; size only, no level, no section mark", "drawn": False},
    {"sheet": "ST7757.pdf p.10 Schedule of Simple Beams", "view": "schedule", "finding": "B15 20 / 120, bars only; no "
     "upstand / inverted column or note", "drawn": False},
    {"sheet": "ST7757.pdf p.14 DETAILS (2)", "view": "parapet, boundary wall, lift details", "finding":
     "no tank or B15 detail; the typical parapet detail rises 0.30 RC above the slab", "drawn": False},
    {"sheet": "ST7757.pdf p.15 / p.16", "view": "beam / slab / stair details", "finding": "typical details only; no B15",
     "drawn": False},
    {"sheet": "architectural .dwf / p7757_arch_sheet09.pdf NORTH EAST ELEVATION and the NORTH WEST / SOUTH WEST "
              "ELEVATIONS", "view": "elevations", "finding":
     "the 2F block top is one coping line at +14.40 (0.50 above +13.90) over its full width on the face along which B15 "
     "runs; nothing is drawn above it but the dome; no tank is drawn either", "drawn": False},
    {"sheet": "architectural .dwf / p7757_arch_sheet10.pdf SECTION A-A", "view": "section (cut about 1.9 m inside the "
     "street-side face, looking toward it)", "finding":
     "roof band +13.90 uniform (0.05 / 0.20 lines); a 2.18 m box beyond, top at +14.40, lies 2.15 .. 4.33 m from the "
     "north face (outside the 0 .. 3.5 m tank panel): not B15; no deep beam drawn under the roof band", "drawn": False},
    {"sheet": "Alsenan_Architectural_P7757_Pages_11-12.pdf p.11 SECTION B-B", "view": "section (south of the block)",
     "finding": "the 2F block is seen beyond, top +14.40, dome; no tank, no B15", "drawn": False},
    {"sheet": "sanitary-7757.pdf p.1-3", "view": "drainage plans", "finding": "no roof plan at +13.90, no tank",
     "drawn": False},
]


def build():
    inp = json.loads((HERE / "ALSENAN_ROOF_INPUT.json").read_text(encoding="utf-8"))
    g = inp["fall"]["value"]
    roofs = []
    for z in inp["roofs"]:
        row = {"zone": z["zone_id"], "name": z["name"], "outline_ref": z["outline_ref"], "outlets_ref": z["outlets_ref"]}
        if not z["outlets"]:
            try:
                R.falls_field(_outline(z) if z["outline"] else [(0, 0), (1, 0), (1, 1)], [], g)
            except ValueError as e:
                row["falls"] = None
                row["falls_status"] = "HELD: " + str(e).split(":")[0]
            roofs.append(row)
            continue
        f = R.falls_field(_outline(z), z["outlets"], g, step=STEP)
        row["falls"] = f
        row["falls_status"] = "DRAWING-CONFIRMED range (FALL_LAYOUT_NOT_DRAWN)"
        ek, ax = f["models"]["EIKONAL"], f["models"]["AXIS"]
        row["rise_max_m"] = [ek["rise_max_m"], ax["rise_max_m"]]
        row["rise_mean_m"] = [ek["rise_mean_m"], ax["rise_mean_m"]]
        row["screed_volume_above_t0_m3"] = [ek["volume_above_t0_m3"], ax["volume_above_t0_m3"]]
        row["parapet"] = R.evaluate_parapet(row["rise_max_m"], inp["parapet_rule"]["upstand_above_slab_m"], t0=None,
                                            layers={"membrane / protection": None})
        if "scope_note" in z:
            row["scope_note"] = z["scope_note"]
        roofs.append(row)
    falls = {r["zone"]: r.get("falls") for r in roofs}
    owner_roof = [{"rule": "Q-41", "scope": "SCREED", "text": "roofs / balconies: screed over the membrane, own line, "
                   "thickness not given"},
                  {"rule": "Q-45", "scope": "MORTAR_BED", "text": "roof bed by the falls, 0.5 % per m (1 % where printed, "
                   "Lead 2026-10-20); t0 not given"}]
    owner_wet = [{"rule": "Q-45", "scope": "MORTAR_BED", "text": "bathrooms bed 0.04 .. 0.06 + tile, 1 % falls"},
                 {"rule": "Q-41", "scope": "MORTAR_BED", "text": "bathrooms: cement bed only, no separate screed"}]
    zone_in = [
        {"zone_id": "ROOF-970", "kind": "ROOF", "ffl": {"value": 9.70, "kind": "FINISHED_ROOF"}, "falls": falls["ROOF-970"],
         "t0": None, "owner": owner_roof, "layers_missing": ["membrane / insulation / protection (no specification, D-62)"]},
        {"zone_id": "TERRACE-550", "kind": "TERRACE", "ffl": {"value": 5.50, "kind": "FINISHED_ROOF"},
         "falls": falls["TERRACE-550"], "t0": None, "owner": owner_roof,
         "layers_missing": ["membrane / protection (no specification, D-62)"]},
        {"zone_id": "ROOF-430", "kind": "ROOF", "ffl": {"value": 4.30, "kind": "FINISHED_ROOF"}, "falls": falls["ROOF-430"],
         "t0": None, "owner": owner_roof, "layers_missing": ["membrane / insulation / protection (no specification, D-62)"]},
        {"zone_id": "ROOF-1390", "kind": "ROOF", "ffl": {"value": 13.90, "kind": "FINISHED_ROOF"}, "falls": None,
         "t0": None, "owner": owner_roof, "layers_missing": ["membrane / insulation / protection (no specification, D-62)"]},
        {"zone_id": "GF-WET", "kind": "WET", "ffl": {"value": 1.00, "kind": "FFL"}, "owner": owner_wet,
         "layers_missing": ["tile thickness", "membrane"]},
        {"zone_id": "ANNEX-WET", "kind": "WET", "ffl": {"value": 0.30, "kind": "FFL"}, "owner": owner_wet,
         "layers_missing": ["tile thickness", "membrane"]},
        {"zone_id": "1F-SUNKEN", "kind": "SUNKEN", "ffl": {"value": 5.50, "kind": "FFL"}, "drop": None, "owner": owner_wet},
        {"zone_id": "2F-SUNKEN", "kind": "SUNKEN", "ffl": {"value": 9.70, "kind": "FFL"}, "drop": None, "owner": owner_wet},
    ]
    zones = []
    for z in zone_in:
        s = R.zone_status(z)
        s.pop("owner_beside", None)
        s["owner_beside"] = [o["rule"] + " " + o["scope"] for o in z["owner"]]
        zones.append(s)
    return {
        "task": "T-221", "method": R.METHOD, "fall": inp["fall"], "parapet_rule": inp["parapet_rule"],
        "roofs": roofs, "zones": zones, "section_cuts": SECTION_CUTS, "d44_record": D44_RECORD,
        "d44_conclusion": "NOT DRAWN on any sheet of any format (8 sheets / views searched): D-44 consultant row 2 is "
                          "send-ready; the architect's elevations and sections draw neither the tank nor anything above "
                          "the +14.40 coping, so they neither show nor exclude an upstand",
        "drawn_roof_band": "every roof band of SECTION A-A / B-B (+4.30, +5.50 sea strip, +9.70, +13.90) draws the same "
                           "constant 0.05 / 0.20 lines as the dry floors (section_bands.py, T-214): refused as a roof "
                           "build-up (CONSTANT_LAYER_VS_FALLS); no slab step is drawn at any roof edge or on ST p.5 / p.6",
    }


def main(argv):
    res = build()
    text = json.dumps(res, indent=1, sort_keys=True, ensure_ascii=False) + "\n"
    if "--write" in argv:
        (HERE / "summary.json").write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main(sys.argv[1:])
