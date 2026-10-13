"""Investigation B: audit every BLOCKED_RFI line ARCH_TAKEOFF_V2 adds over V1 on one drawing.
usage: python3 -I rfi_audit.py V1_OUT V2_OUT CSV_OUT JSON_OUT [FLOAT_MISSED_DOOR_BLOCKS]
  FLOAT_MISSED_DOOR_BLOCKS  comma list of door-block ids whose opening the float-threshold defect drops (Investigation A)
Classes:
  G  GENUINE_MISSING_SOURCE_INFO   the drawing set does not contain what is needed
  D  GEOMETRY_OR_READER_DEFECT     the engine misread the drawing (the RFI asks the wrong question)
  O  UNAPPROVED_OWNER_RULE         geometry is measured; a finish / measurement rule is not approved
  I  MISSING_IMPLEMENTATION        the evidence is in the drawing; a check or reader is not implemented
  X  DUPLICATE_OR_UNNECESSARY      the question is already asked by another record, or the record should not exist
"""
import csv, json, sys
from collections import Counter, defaultdict
V1, V2, CSV_OUT, JSON_OUT = sys.argv[1:5]
L1 = json.load(open(f"{V1}/BOQ_LINES.json")); L2 = json.load(open(f"{V2}/BOQ_LINES.json"))
ids1 = {l["line_id"] for l in L1}
added = [l for l in L2 if l["line_id"] not in ids1]
O = json.load(open(f"{V2}/ARCH_OPENINGS.json"))["openings"]
ops = {(o["floor"], o["opening_id"]): o for o in O}
rooms = {r["room_id"]: r for r in json.load(open(f"{V2}/ARCH_ROOMS.json"))["rooms"]}
C = json.load(open(f"{V2}/FINISH_COVERAGE.json"))
strips = {(f["floor"], s["strip_id"]): s for f in C["floors"] for s in f["physical_regions"]["strips"]}
P = json.load(open(f"{V2}/ARCH_PLAN.json"))
closed_doors = {}
for r in P["regions"]:
    closed_doors[r["floor"]] = r.get("door_status")
# the opening ids that carry two strip lines (a verified threshold line and an unattributed line)
per_op = defaultdict(list)
for l in added:
    for oid in (l["calculation"]["inputs"].get("opening_ids") or []):
        per_op[(l["location"]["floor"], oid)].append(l["line_id"])
wall_tile_rfi_rooms = {l["location"]["room_id"] for l in L2 if l["item_code"] == "FIN.WALL.TILE" and l["evidence_state"] == "BLOCKED_RFI"}
DOOR_MISSED_BY_FLOAT = set(sys.argv[5].split(",")) if len(sys.argv) > 5 else set()   # from Investigation A


def rname(rid):
    r = rooms.get(rid) or {}
    return f'{r.get("name_en") or rid} [{r.get("kind") or "-"}]'


rows = []
for n, l in enumerate(sorted(added, key=lambda x: (["GF", "1F", "2F"].index(x["location"]["floor"]), x["item_code"],
                                                   x["location"]["element_id"])), 1):
    loc, inp = l["location"], l["calculation"]["inputs"]
    fl, code = loc["floor"], l["item_code"]
    q = l["rfi"]["question"]; key = q.split(":")[0]
    st = [strips.get((fl, s)) for s in inp.get("strips") or []]
    failed = sorted({c for s in st if s for c in (s.get("geometry") or {}).get("failed_checks") or []})
    oids = inp.get("opening_ids") or []
    adj = sorted({rname(x) for oid in oids for x in (ops.get((fl, oid)) or {}).get("rooms", [])})
    closures = inp.get("door_closures") or []
    rec = {"no": n, "line_id": l["line_id"], "floor": fl, "family": code, "element": loc["element_id"],
           "room_or_strip": loc["room_id"], "room_name": loc.get("room_name_en"), "adjacent_rooms": "; ".join(adj),
           "opening_ids": "+".join(oids), "opening_kinds": "+".join(inp.get("opening_kinds") or []),
           "opening_width_m": inp.get("opening_width_m"), "wall_t_m": inp.get("wall_t_m"),
           "source_entities": "; ".join([*(inp.get("strips") or []), *closures]),
           "geometry_verified": inp.get("geometry_verified"), "failed_checks": "+".join(failed),
           "measured_in_inputs": inp.get("measured_strip_m2") if "measured_strip_m2" in inp else inp.get("wall_lm"),
           "measured_unit": "m2 (strip plan area)" if "measured_strip_m2" in inp else ("lm (wall run)" if "wall_lm" in inp else ""),
           "question_key": key}
    # ---- classification
    if code == "ARCH.WINDOW_REVEAL":
        cls, missing = "G", "sill height / window type (window schedule or elevations): wall below the sill or floor (French window)"
        why = "the plan does not say whether the strip is a sill (wall) or floor"
        qty = "NO: the strip plan area is measured; its classification (sill vs floor) and finish are missing"
        auto = "YES after one window schedule: every window reveal resolves from its sill height"
        group = "RFI-G1 window schedule / sill heights"
    elif key.startswith("THRESHOLD_FINISH") and oids:
        o = ops.get((fl, oids[0])) or {}
        if (o.get("width_m") or 0) > 6 and o.get("jambs") == ["COLUMN_JAMB", "COLUMN_JAMB"]:
            cls = "D"
            missing = "none for a threshold: a column-jambed 11 m gap is an open boundary (colonnade / zone edge), not a doorway"
            why = "the census reads a row of columns in an open plan as one wall opening; its strip is open-plan floor"
            qty = "NO: the area is measured (and belongs to the open-plan floor)"
            auto = "YES: an open boundary between floor zones takes the adjacent floor's finish; needs the semantic rule, not an owner RFI"
            group = "ENG-D3 wide column-jambed gaps read as passages"
        else:
            cls, missing = "O", "owner rule Q-S6-1: threshold piece vs the room floor continued, and its measurement (m2 / lm)"
            why = "no approved rule for the finish of the floor strip inside a doorway"
            qty = "NO: the strip plan area is measured"
            auto = "YES after Q-S6-1: one rule resolves every verified threshold"
            group = "RFI-O1 Q-S6-1 threshold finish"
    elif key.startswith("THRESHOLD_FINISH") and not oids:
        cls = "D"
        missing = "none from the owner: a door is drawn (door block closure) but no wall opening was measured (door state CLOSED)"
        why = "the door's wall gap was not found by the band census; the strip exists only through the door closure"
        if any(c.split("|")[1] in DOOR_MISSED_BY_FLOAT for c in closures):
            why += " (Investigation A float defect)"
        qty = "NO: the strip is measured; the DOOR itself (count, width, lintel, deductions) is missing"
        auto = "YES from geometry: width from the swing radius / closure; becomes a door opening + verified threshold"
        group = "ENG-D1 drawn doors without a measured opening (CLOSED)"
    elif key == "STRIP_NOT_ATTRIBUTED":
        if any(c.split("|")[1] in DOOR_MISSED_BY_FLOAT for c in closures):
            cls, why = "D", "the strip of the door the float defect drops (Investigation A) is pinned to the nearest opening instead"
            group = "ENG-D2 Investigation A (S6R-A1)"
        elif "NO_OPENING" in failed:
            cls, why = "D", "a sliver between a wall end and a drawn zone line: not a doorway; open-plan floor"
            group = "ENG-D4 zone-line slivers"
        elif "SPANS_SEVERAL_OPENINGS" in failed:
            cls, why = "I", "one face spans two adjacent doors; the check cannot split a face between openings"
            group = "ENG-I1 strip check: split faces across adjacent openings"
        elif (fl, oids[0]) in per_op and len(per_op[(fl, oids[0])]) > 1 and "ZONE" in json.dumps((st[0] or {}).get("bounded_by_lm") or {}):
            cls, why = "D", "the opening's remaining faces are cut by drawn zone lines"
            group = "ENG-D3 wide column-jambed gaps read as passages"
        else:
            cls, why = "I", "strip deeper than the wall (set-back door / frame, or a column beside the passage): the opening-box check is too strict"
            group = "ENG-I2 strip check: set-back doors, columns at jambs"
        missing = "none from the owner"
        qty = "NO: the strip area is measured; its attribution failed"
        auto = "YES from geometry once the check is refined"
    elif key.startswith("STAIR_HALL"):
        cls = "O"
        missing = "owner rule Q-S6-4 (stair enclosure finishes, raking skirting) AND the stairwell wall heights (sections)"
        why = "no rule scopes stair-hall wall finishes; heights of multi-storey stairwell walls are not in the plan"
        qty = "YES: the wall run is measured but the height is not, so the area is missing"
        auto = "PARTLY: the rule resolves all 6; the heights need sections"
        group = "RFI-O2 Q-S6-4 stair hall finishes (+ heights)"
    elif key.startswith("FINISH_ABOVE_WALL_TILE"):
        cls = "O"
        missing = "owner rule Q7 (finish in the band above partial tile) AND the tile and finished-ceiling heights"
        why = ("wet room: tile height and finish height are both NOT_ESTABLISHED, so the band is unknown. Rule conflict: "
               "URBAN-WET-WALL-TILE-FULL-HEIGHT@v1 (tile to the finished ceiling: no band) vs owner-approved UP-CER-009 "
               "(tile height derived per face, never a constant)")
        qty = "YES: the band height is unknown, so its area is missing"
        auto = "PARTLY: if full-height tile is confirmed for wet rooms, all 16 close as NOT_APPLICABLE"
        group = "RFI-O3 Q7 finish above wet-room tile (+ heights)"
    else:
        cls, missing, why, qty, auto, group = "?", "", "", "", "", "UNCLASSIFIED"
    dup = []
    if oids and len(per_op.get((fl, oids[0]), [])) > 1:
        dup.append("the same opening has another strip line: " + "+".join(x for x in per_op[(fl, oids[0])] if x != l["line_id"]))
    if key.startswith("FINISH_ABOVE_WALL_TILE") and loc["room_id"] in wall_tile_rfi_rooms:
        dup.append("the height part repeats the room's FIN.WALL.TILE height RFI (UP-CER-009)")
    if "e3b5" in loc["element_id"]:
        dup.append("probably unnecessary (not a doorway)")
    rec.update({"class": cls, "missing_information": missing, "why_blocked": why, "actual_missing_quantity": qty,
                "duplicate_or_overlap": "; ".join(dup), "auto_resolvable": auto, "group": group})
    rows.append(rec)
with open(CSV_OUT, "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
summary = {"records": len(rows), "by_class": dict(Counter(r["class"] for r in rows)),
           "by_group": dict(Counter(r["group"] for r in rows)),
           "by_family": dict(Counter(r["family"] for r in rows)),
           "with_duplicate_or_overlap": sum(bool(r["duplicate_or_overlap"]) for r in rows),
           "owner_or_client_questions": sorted({r["group"] for r in rows if r["group"].startswith("RFI-")}),
           "engineering_findings_not_rfis": sorted({r["group"] for r in rows if r["group"].startswith("ENG-")}),
           "door_status_by_floor": closed_doors}
json.dump({"summary": summary, "records": rows}, open(JSON_OUT, "w"), indent=1, ensure_ascii=False)
print(json.dumps(summary, indent=1))
