"""PA04 workstreams A (first-floor physical face sets), B (wet / service
room wall lengths, project-wide), §4 (ceiling measurement regions) and §5
(floor measurement regions) from the three DWG plan copies.

Regions are flood-filled between wall and door lines (engine.plan_regions);
faces are boundary runs classified WALL / DOOR / OPEN.  Room identity: GF
from the DWG TEXT labels; FF from the primary read of the printed sheet
(PRIMARY_FF_NAMES) held PROVISIONAL until the cold challenge reconciles it.

    python3 -m research.qs_wall_treatment_01.pa04.rooms
"""

from __future__ import annotations

import numpy as np

from engine import plan_regions as PR
from engine import self_checks as SC
from research.qs_wall_treatment_01.pa04 import common as C

CELL = 50
BOX = {"GF": (-163000, -806000, -126000, -789500)}
WET_NAMES = ("BATH", "W.C", "WC", "KITCHEN", "PANTRY", "WASH", "LAUNDRY", "IRON", "SHOWER", "TOILET")
EXTERIOR_NAMES = ("NEIGHBOUR", "STREET", "SEA VIEW", "COURT", "GARDEN", "swimming pool", "ROOF", "EXTERIOR")
# printed English room names on the DWG GF copy; the Arabic twin labels decode as garbled Latin strings and are ignored
GF_LABEL_WHITELIST = ("BATH", "W.C", "KITCHEN", "PANTRY", "Wash", "DEWANEYA", "DRIVER", "SALOON", "RECEPTION", "DINING", "MASTER BED ROOM", "GARDEN", "COURT", "NEIGHBOUR", "STREET", "SEA VIEW", "swimming pool")
# primary read of the FIRST FLOOR sheet (page 2) against the region map; keyed by the READ id of the map given to the
# reader, resolved to the current region through a CAD anchor point (region ids are run-dependent, anchors are not)
PRIMARY_FF_ANCHORS = {2: (-199977.6, -802475.0), 3: (-195477.6, -794025.0), 1: (-189077.6, -790225.0), 9: (-181427.6, -803825.0), 7: (-193327.6, -802425.0), 10: (-191127.6, -802275.0),
                      8: (-192177.6, -798725.0), 11: (-188077.6, -801075.0), 13: (-180227.6, -797425.0), 25: (-185527.6, -794325.0), 31: (-184477.6, -792875.0), 36: (-182677.6, -792825.0),
                      47: (-176477.6, -797225.0), 52: (-174877.6, -794475.0), 55: (-173927.6, -794825.0), 35: (-183127.6, -800125.0), 41: (-181177.6, -801075.0), 34: (-182677.6, -801925.0),
                      29: (-184677.6, -800775.0), 22: (-186177.6, -799025.0), 23: (-186027.6, -796375.0), 19: (-188027.6, -792575.0), 21: (-186577.6, -795025.0), 26: (-185527.6, -802975.0), 28: (-185127.6, -801375.0)}
PRIMARY_FF_NAMES = {
    2: ("ROOF (annex, +4.30)", "EXTERIOR_ROOF", "printed ROOF, +4.30 marker", "HIGH"),
    3: ("exterior (street side)", "EXTERIOR", "outside the FF outline", "HIGH"),
    1: ("site exterior", "EXTERIOR", "outside the plot outline", "HIGH"),
    9: ("ROOF terrace (+5.50, sea-view side)", "EXTERIOR_ROOF", "printed ROOF at the sea-view corner, +5.50", "MEDIUM"),
    7: ("BATH", "WET", "printed BATH 245 x 205 (upper of the two)", "HIGH"),
    10: ("BATH", "WET", "printed BATH 245 x 205 (lower of the two)", "HIGH"),
    8: ("MASTER BED ROOM", "BEDROOM", "printed MASTER BED ROOM 450 x 425", "HIGH"),
    11: ("MASTER BED ROOM", "BEDROOM", "printed MASTER BED ROOM 365 wide (left-centre)", "MEDIUM"),
    13: ("OPEN GROUP: corridor / lobby + LIVING AREA + MASTER BED ROOM 430 x 380 + MASTER BED ROOM 400 x 420", "OPEN_GROUP", "one region: the DWG draws no closing door line on layer D between these; identity per room PROVISIONAL", "MEDIUM"),
    25: ("LAUNDRY", "WET", "printed LAUNDRY 300 x 347", "HIGH"),
    31: ("W.C", "WET", "printed W.C 147 beside the laundry", "MEDIUM"),
    36: ("BATH", "WET", "printed BATH 180 x 200 (right)", "MEDIUM"),
    47: ("BATH", "WET", "printed BATH 225 (bottom)", "MEDIUM"),
    35: ("VOID (reception opening, X quadrant)", "VOID", "part of the X-marked 587 x 400 zone", "HIGH"),
    41: ("VOID (reception opening, X quadrant)", "VOID", "part of the X-marked zone", "HIGH"),
    34: ("VOID (reception opening, X quadrant)", "VOID", "part of the X-marked zone", "HIGH"),
    29: ("VOID (reception opening, X quadrant)", "VOID", "part of the X-marked zone", "HIGH"),
    22: ("LIFT SHAFT (180 x 180, X-marked)", "SHAFT", "small square with X at the corridor head", "MEDIUM"),
    23: ("LIFT SHAFT (180 x 180, X-marked)", "SHAFT", "as R22", "MEDIUM"),
    19: ("block stair landing / well cell", "STAIR", "inside the 645 well", "LOW"),
    21: ("stair / shaft cell", "STAIR", "small cell beside the shaft", "LOW"),
    26: ("curved stair treads", "STAIR", "tread cells of the curved flight", "MEDIUM"),
    28: ("curved stair treads", "STAIR", "tread cells", "MEDIUM"),
}


def _regions(copy):
    dx = C.COPIES[copy]
    x0, y0, x1, y1 = BOX["GF"]
    box = (x0 + dx, y0, x1 + dx, y1)
    wall, door, meta = PR.rasterise(C.prims(), box, CELL)
    seeds, k = {}, 0
    for x in np.arange(box[0] + 500, box[2], 1000):
        for y in np.arange(box[1] + 500, box[3], 1000):
            seeds[k] = (float(x), float(y))
            k += 1
    label, _ = PR.flood(wall, door, seeds, meta, max_cells=3_000_000)
    return wall, door, meta, label


def _gf_names():
    n = C.norm()
    out = {}
    for t in n.texts:
        txt = (getattr(t, "value", None) or getattr(t, "text", None)) if not isinstance(t, dict) else t.get("text") or t.get("value")
        x, y = (t.x, t.y) if not isinstance(t, dict) else t["at_mm"]
        if txt and txt.strip() in GF_LABEL_WHITELIST:
            out.setdefault(txt.strip(), []).append((x, y))
    return out


def _columns_on_boundary(copy, rs, cs, meta):
    dx = C.COPIES[copy]
    xmin, xmax = meta["x0"] + cs.min() * CELL - 300, meta["x0"] + (cs.max() + 1) * CELL + 300
    ymin, ymax = meta["y1"] - (rs.max() + 1) * CELL - 300, meta["y1"] - rs.min() * CELL + 300
    loops = set()
    for p in C.prims():
        if p[2] == "S-COL.BON" and p[0] == "SEGMENT" and xmin <= p[3] <= xmax and ymin <= p[4] <= ymax:
            loops.add(p[1].split(".")[0])
    return sorted(loops)


def faces_for(copy, lab, wall, door, meta, label):
    raw = PR.merge_collinear(PR.boundary_faces(label, wall, door, lab, meta, min_run_cells=2))
    faces = []
    frag = {"WALL": 0.0, "OPEN": 0.0, "DOOR": 0.0, "EDGE": 0.0}
    for i, f in enumerate(sorted(raw, key=lambda f: -f["LENGTH_M"])):
        if f["LENGTH_M"] < 0.25:
            frag[f["CLASS"]] = round(frag[f["CLASS"]] + f["LENGTH_M"], 3)
            continue
        faces.append({"PHYSICAL_FACE_ID": f"{copy}-R{lab}-F{i:02d}", "FACE_LENGTH_M": f["LENGTH_M"], "FACE_GEOMETRY_TYPE": "STRAIGHT_AXIS_ALIGNED",
                      "FACE_CLASS": {"WALL": "PHYSICAL_HOST_WALL", "DOOR": "DOOR_LINE_ON_HOST_WALL", "OPEN": "OPEN_EDGE", "EDGE": "GRID_EDGE_UNRESOLVED"}[f["CLASS"]],
                      "SIDE": f["SIDE"], "HOST_WALL": (f["ENTITY_IDS"][:3] if f["CLASS"] == "WALL" else None), "OPENING_IDS": (f["ENTITY_IDS"][:3] if f["CLASS"] == "DOOR" else []),
                      "OPEN_EDGE": f["CLASS"] == "OPEN", "ADJACENT_SPACE": [f"R{r}" for r in f["OTHER_REGIONS"]] if f["CLASS"] == "OPEN" else None,
                      "SOURCE_ENTITY_IDS": f["ENTITY_IDS"], "GEOM_MM": f["GEOM"], "MEASUREMENT_BASIS": "clear internal face at the wall line, DWG plan copy rasterised at 50 mm",
                      "STATUS": "ESTABLISHED_FROM_DWG" if f["CLASS"] in ("WALL", "DOOR") else ("OPEN_EDGE_ESTABLISHED" if f["CLASS"] == "OPEN" else "UNRESOLVED")})
    return faces, frag


def room_records(copy, names, wall, door, meta, label, min_area=1.0, max_area=200.0):
    labs, counts = np.unique(label[label > 0], return_counts=True)
    rooms = []
    for lab, n in zip(labs, counts):
        area = round(float(n) * (CELL / 1000) ** 2, 3)
        if area < min_area or area > max_area:
            continue
        rs, cs = np.where(label == lab)
        lab = int(lab)
        nm = names.get(lab, ("unnamed region", "UNKNOWN", "no printed label maps to this region", "LOW"))
        faces, frag = faces_for(copy, lab, wall, door, meta, label)
        tot = {}
        for f in faces:
            tot[f["FACE_CLASS"]] = round(tot.get(f["FACE_CLASS"], 0.0) + f["FACE_LENGTH_M"], 3)
        rooms.append({"ROOM_ID": f"{copy}-R{lab}", "ROOM_NAME": nm[0], "ROOM_CLASS": nm[1], "IDENTITY_EVIDENCE": nm[2], "IDENTITY_CONFIDENCE": nm[3],
                      "IDENTITY_STATUS": "ESTABLISHED_FROM_DWG_TEXT" if copy == "GF" and lab in names else ("PROVISIONAL_PRIMARY_READ" if lab in names else "NOT_ESTABLISHED"),
                      "REGION_AREA_M2": area, "BBOX_MM": {"X": [round(meta["x0"] + cs.min() * CELL), round(meta["x0"] + (cs.max() + 1) * CELL)],
                                                         "Y": [round(meta["y1"] - (rs.max() + 1) * CELL), round(meta["y1"] - rs.min() * CELL)]},
                      "FACES": faces, "FACE_LM_BY_CLASS": tot, "FRAGMENTS_UNDER_0_25_M_LM": frag,
                      "COLUMN_RELATION": _columns_on_boundary(copy, rs, cs, meta), "SOURCE": f"DWG {copy} plan copy (layers 1/5/W/0 walls, D doors)"})
    return rooms


def wet_record(room):
    t = room["FACE_LM_BY_CLASS"]
    return {"ROOM_ID": room["ROOM_ID"], "ROOM_NAME": room["ROOM_NAME"], "GROSS_HOST_WALL_LM": t.get("PHYSICAL_HOST_WALL", 0.0),
            "OPEN_EDGE_LM": t.get("OPEN_EDGE", 0.0), "OPENING_HOST_LENGTHS": [{"OPENING_IDS": f["OPENING_IDS"], "LM": f["FACE_LENGTH_M"]} for f in room["FACES"] if f["FACE_CLASS"] == "DOOR_LINE_ON_HOST_WALL"],
            "UNRESOLVED_EDGE_LM": round(t.get("GRID_EDGE_UNRESOLVED", 0.0) + sum(room["FRAGMENTS_UNDER_0_25_M_LM"].values()), 3),
            "TILE_PREP_HEIGHT_STATUS": "NOT_ESTABLISHED (no finishes schedule; no universal tiled height invented)", "TILE_PREP_AREA_STATUS": "NOT_ESTABLISHED",
            "QUANTITY_STATE_LM": "SOURCE_ESTABLISHED_QUANTITY" if room["IDENTITY_STATUS"] == "ESTABLISHED_FROM_DWG_TEXT" else "PROVISIONAL_QUANTITY",
            "PERIMETER_NOT_USED": True, "SOURCE": room["SOURCE"]}


@C.timed("A_B_ceiling_floor")
def run():
    n = C.norm()
    gf_names_pts = _gf_names()
    out_rooms = {}
    grids = {}
    for copy in ("GF", "FF", "ROOF"):
        wall, door, meta, label = _regions(copy)
        grids[copy] = (wall, door, meta, label)
        names = {}
        if copy == "GF":
            for txt, pts in gf_names_pts.items():
                for x, y in pts:
                    r, c = int((meta["y1"] - y) / CELL), int((x - meta["x0"]) / CELL)
                    if 0 <= r < label.shape[0] and 0 <= c < label.shape[1] and label[r, c] > 0:
                        lab = int(label[r, c])
                        cls = "WET" if any(w in txt.upper() for w in WET_NAMES) else ("EXTERIOR" if txt in EXTERIOR_NAMES else ("BEDROOM" if "BED" in txt.upper() else "ROOM"))
                        if lab in names and txt in names[lab][0].split(" + "):
                            continue                      # the same label twice (e.g. COURT on both courts of one region)
                        if lab in names:
                            merged_cls = "OPEN_GROUP_WITH_WET" if "WET" in (names[lab][1], cls) or names[lab][1] == "OPEN_GROUP_WITH_WET" else "OPEN_GROUP"
                            names[lab] = (names[lab][0] + " + " + txt, merged_cls, names[lab][2] + "; " + txt, "MEDIUM")
                        else:
                            names[lab] = (txt, cls, f"DWG TEXT '{txt}' inside the region", "HIGH")
        elif copy == "FF":
            names, read_ids = {}, {}
            for old, (x, y) in PRIMARY_FF_ANCHORS.items():
                r, c = int((meta["y1"] - y) / CELL), int((x - meta["x0"]) / CELL)
                lab = int(label[r, c]) if 0 <= r < label.shape[0] and 0 <= c < label.shape[1] else 0
                if lab > 0 and old in PRIMARY_FF_NAMES:
                    names[lab] = PRIMARY_FF_NAMES[old]
                    read_ids[lab] = old
        out_rooms[copy] = room_records(copy, names, wall, door, meta, label)
        if copy == "FF":
            for r in out_rooms[copy]:
                r["READ_ID_ON_CHALLENGE_MAP"] = read_ids.get(int(r["ROOM_ID"].split("R")[-1]))
    ff = out_rooms["FF"]
    ff_lines = [{"ID": f["PHYSICAL_FACE_ID"], "UNIT": "lm", "VALUE": f["FACE_LENGTH_M"], "QUANTITY_STATE": "SOURCE_ESTABLISHED_QUANTITY" if f["FACE_CLASS"] != "GRID_EDGE_UNRESOLVED" else "NOT_ESTABLISHED",
                 "SOURCE": r["SOURCE"], "SOURCE_ENTITY_IDS": f["SOURCE_ENTITY_IDS"]} for r in ff for f in r["FACES"]]
    checks_a = SC.run_all({"ROOMS": ff}, ff_lines, provenance_keys=("SOURCE",))
    by_class = {}
    for r in ff:
        by_class.setdefault(r["ROOM_CLASS"], {"ROOMS": 0, "HOST_WALL_LM": 0.0, "OPEN_EDGE_LM": 0.0})
        by_class[r["ROOM_CLASS"]]["ROOMS"] += 1
        by_class[r["ROOM_CLASS"]]["HOST_WALL_LM"] = round(by_class[r["ROOM_CLASS"]]["HOST_WALL_LM"] + r["FACE_LM_BY_CLASS"].get("PHYSICAL_HOST_WALL", 0.0), 3)
        by_class[r["ROOM_CLASS"]]["OPEN_EDGE_LM"] = round(by_class[r["ROOM_CLASS"]]["OPEN_EDGE_LM"] + r["FACE_LM_BY_CLASS"].get("OPEN_EDGE", 0.0), 3)
    C.write("FF_PHYSICAL_FACE_REGISTER.json", {"ARTIFACT": "FF_PHYSICAL_FACE_REGISTER", "WORKSTREAM": "A", "NORMALIZATION_HASH": n.normalization_hash(),
                                               "IDENTITY_NOTE": "the DWG FF copy carries no room TEXT (one W.C only); names come from the printed sheet (primary read) and are PROVISIONAL until the cold challenge is reconciled",
                                               "ROOMS": ff, "BY_ROOM_CLASS": by_class, "PLASTER_AREA": "not computed: FIRST_NORMAL_INTERNAL height NOT_ESTABLISHED (height parameter table)",
                                               "SELF_CHECKS": checks_a})
    C.write("GF_ROOF_PHYSICAL_FACE_REGISTER.json", {"ARTIFACT": "GF_ROOF_PHYSICAL_FACE_REGISTER", "WORKSTREAM": "A (support)", "ROOMS": {"GF": out_rooms["GF"], "ROOF": out_rooms["ROOF"]}})
    # ---- B: wet rooms project-wide ---------------------------------------------------------------
    wet = [wet_record(r) for copy in ("GF", "FF", "ROOF") for r in out_rooms[copy] if r["ROOM_CLASS"] == "WET"]
    wet_lines = [{"ID": w["ROOM_ID"], "UNIT": "lm", "VALUE": w["GROSS_HOST_WALL_LM"], "QUANTITY_STATE": w["QUANTITY_STATE_LM"], "SOURCE": w["SOURCE"], "SOURCE_ENTITY_IDS": ["see face register"],
                  "TREATMENT_STATUS": "NOT_ESTABLISHED"} for w in wet]
    checks_b = SC.run_all({"WET": wet}, wet_lines)
    C.write("WET_ROOM_REGISTER_V2.json", {"ARTIFACT": "WET_ROOM_REGISTER_V2", "WORKSTREAM": "B", "ROOMS": wet,
                                          "TOTALS": {"GROSS_HOST_WALL_LM_BY_FLOOR": {c: round(sum(w["GROSS_HOST_WALL_LM"] for w in wet if w["ROOM_ID"].startswith(c)), 3) for c in ("GF", "FF", "ROOF")}},
                                          "RULES": ["open edge = 0 wall length", "door / window openings live in the opening register", "no room-polygon perimeter used", "no universal tiled height invented"],
                                          "SELF_CHECKS": checks_b})
    # ---- §4 ceiling regions ------------------------------------------------------------------------
    void = C.read("VOID_GEOMETRY_RECONCILIATION.json", C.OUT)["OBJECTS_PRESERVED"]
    ceil = []
    for copy in ("GF", "FF"):
        for r in out_rooms[copy]:
            base = r["REGION_AREA_M2"]
            ded_void = ded_stair = ded_other = 0.0
            status = "GEOMETRY_ONLY (treatment not decided)"
            note = None
            if r["ROOM_CLASS"] in ("VOID", "SHAFT"):
                ded_other = base
                note = "no ceiling: the region is an opening / shaft"
            elif r["ROOM_CLASS"] == "STAIR":
                ded_stair = base
                note = "stair region: soffit geometry belongs to the stair register"
            elif r["ROOM_CLASS"] in ("EXTERIOR", "EXTERIOR_ROOF"):
                ded_other = base
                note = "exterior: no ceiling"
            elif copy == "GF" and "RECEPTION" in r["ROOM_NAME"]:
                ded_void = void["SLAB_OPENING"]["AREA_M2"]
                ded_stair = round(void["STRAIGHT_FLIGHT_STRIP"]["WIDTH_M"] * void["STRAIGHT_FLIGHT_STRIP"]["DEPTH_M"], 3)
                note = "PA03 void reconciliation respected: SLAB_OPENING deducted (no slab), the straight-flight strip carries a stair soffit, the curved flight footprint (4.40 m2 PROVISIONAL) lies inside the slab opening"
                status = "PROVISIONAL (region merges RECEPTION + SALOON + DINING + MASTER BED ROOM through open edges)"
            net = round(base - ded_void - ded_stair - ded_other, 3)
            ceil.append({"ZONE_ID": r["ROOM_ID"], "ZONE_NAME": r["ROOM_NAME"], "BASE_FLOOR_REGION_M2": base, "VOID_DEDUCTION_M2": ded_void, "STAIR_DEDUCTION_M2": ded_stair,
                         "OTHER_DEDUCTION_M2": ded_other, "NET_CEILING_GEOMETRY_M2": net, "CEILING_TREATMENT_STATUS": "NOT_DECIDED (no gypsum / decor pricing)", "GEOMETRY_STATUS": status, "NOTE": note,
                         "CEILING_EQUALS_FLOOR": False})
    C.write("CEILING_MEASUREMENT_REGION_REGISTER.json", {"ARTIFACT": "CEILING_MEASUREMENT_REGION_REGISTER", "RULE": "ceiling starts from the floor region and deducts stair opening / void / double height / shaft / roof opening; it is never blindly equal to the floor",
                                                         "ZONES": ceil})
    # ---- §5 floor regions --------------------------------------------------------------------------
    floors = []
    for copy in ("GF", "FF", "ROOF"):
        for r in out_rooms[copy]:
            floors.append({"REGION_ID": r["ROOM_ID"], "PHYSICAL_SPACE": r["ROOM_NAME"], "FUNCTIONAL_ZONE": r["ROOM_CLASS"], "TRADE_MEASUREMENT_ZONE": "NOT_DECIDED (material not established; topology alone does not decide finish)",
                           "GEOMETRY_M2": r["REGION_AREA_M2"], "OPEN_TO": sorted({a for f in r["FACES"] if f["ADJACENT_SPACE"] for a in f["ADJACENT_SPACE"]}),
                           "MATERIAL_STATUS": "NOT_ESTABLISHED", "QUANTITY_STATE": "GEOMETRIC_REFERENCE_ONLY"})
    C.write("FLOOR_MEASUREMENT_REGION_REGISTER.json", {"ARTIFACT": "FLOOR_MEASUREMENT_REGION_REGISTER", "RULE": "PHYSICAL_SPACE != FUNCTIONAL_ZONE != TRADE_MEASUREMENT_ZONE; geometry only until a material is established",
                                                       "REGIONS": floors, "EXAMPLES": ["GF PANTRY is open to DINING (separate region only if a door line closes it)", "the GARDEN strip is its own region"]})
    C.METRICS.setdefault("A_B_ceiling_floor", {}).update({"DETERMINISTIC_OPS": sum(len(out_rooms[c]) for c in out_rooms), "AI_CALLS": 1, "AI_CALLS_NOTE": "one cold-challenge reader for FF room identity"})
    return {"FF_ROOMS": [(r["ROOM_ID"], r["ROOM_NAME"][:30], r["REGION_AREA_M2"], r["FACE_LM_BY_CLASS"]) for r in ff], "WET": [(w["ROOM_ID"], w["ROOM_NAME"], w["GROSS_HOST_WALL_LM"], w["OPEN_EDGE_LM"]) for w in wet],
            "CHECKS_A": checks_a["FAILED"], "CHECKS_B": checks_b["FAILED"]}


if __name__ == "__main__":
    import json
    print(json.dumps(run(), indent=1, default=str))
