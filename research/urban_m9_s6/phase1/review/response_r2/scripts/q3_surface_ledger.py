"""Q3 prototype (read-only, scratch): a minimal eligible-surface ledger over ARCH_TAKEOFF_V2 outputs.

One record per (element, surface, trade). The element is a space, an opening or a wall group. The trade comes from an
explicit eligibility table (ELIGIBILITY_V0 below, which would be a versioned rule file), keyed by space kind or
opening kind. Status:
  MEASURED        a line with a quantity from source geometry (SOURCE_DERIVED)
  PROVISIONAL     a line with a provisional / bounded quantity
  BLOCKED         a BLOCKED_RFI line exists; blocker = MISSING_SOURCE (sections / schedule / spec), OWNER_DECISION or
                  ENGINE (a software finding)
  EXCLUDED        the rule table excludes the pair (e.g. a lift shaft), with the rule
  NOT_APPLICABLE  a line says NOT_APPLICABLE_WITH_EVIDENCE
  MISSING         the pair is eligible but NO line and NO RFI exists: a silent gap (an NSD violation)
Optionally reads the Q2 door evidence (provisional / unresolved door elements without a line).
usage: python3 -I q3_surface_ledger.py V2_OUT [Q2_DOOR_EVIDENCE.json|-] OUT_JSON [OUT_CSV]"""
import csv, json, re, sys
from collections import Counter, defaultdict

D, Q2, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
OUT_CSV = sys.argv[4] if len(sys.argv) > 4 else None

ELIGIBILITY_V0 = {      # (surface, trade): item codes [, element-suffix pattern]
    "DRY": [("FLOOR", "FLOOR_FINISH", ["FIN.FLOOR.PORCELAIN", "FIN.FLOOR.MARBLE"], "floor"),
            ("CEILING", "CEILING", ["FIN.CEILING"], "ceiling"),
            ("WALLS", "PLASTER", ["FIN.PLASTER"], "plaster"),
            ("WALLS", "PAINT", ["FIN.PAINT"], "paint"),
            ("SKIRTING", "SKIRTING", ["FIN.SKIRTING"], "skirting")],
    "WET": [("FLOOR", "WET_FLOOR_TILE", ["FIN.FLOOR.WET_TILE"], "floor"),
            ("FLOOR", "WATERPROOFING_FLOOR", ["FIN.WP.FLOOR"], "wp_floor"),
            ("WALL_BASE", "WATERPROOFING_UPTURN", ["FIN.WP.UPTURN"], "wp_upturn"),
            ("CEILING", "CEILING", ["FIN.CEILING"], "ceiling"),
            ("WALLS", "PLASTER", ["FIN.PLASTER"], "plaster"),
            ("WALLS", "WALL_TILE", ["FIN.WALL.TILE"], "wall_tile"),
            ("WALLS_ABOVE_TILE", "PAINT_OR_TILE (Q7)", ["FIN.PAINT"], "above wall tile"),
            ("SKIRTING", "SKIRTING (UP-CER-004)", ["FIN.SKIRTING"], "skirting")],
    "STAIR": [("TREADS", "MARBLE_TREAD", ["FIN.MARBLE.TREAD"], "flight"),
              ("RISERS", "MARBLE_RISER", ["FIN.MARBLE.RISER"], "flight"),
              ("LANDINGS", "MARBLE_LANDING", ["FIN.MARBLE.LANDING"], "landing"),
              ("NOSINGS", "STEP_LM", ["FIN.STAIR.STEP_LM"], "flight"),
              ("BALUSTRADE", "RAILING", ["FIN.RAILING"], "flight"),
              ("SOFFIT_CEILING", "CEILING", ["FIN.CEILING"], "ceiling"),
              ("WALLS", "PLASTER", ["FIN.PLASTER"], "plaster"),
              ("WALLS", "PAINT", ["FIN.PAINT"], "paint"),
              ("SKIRTING", "SKIRTING", ["FIN.SKIRTING"], "skirting")],
    "EXTERIOR": [("GROUND", "EXTERIOR_SCOPE (Q1)", ["ARCH.EXTERIOR"], "")],
    "UNKNOWN": [("FLOOR", "UNKNOWN (space kind not established)", ["FIN.FLOOR.PORCELAIN", "FIN.FLOOR.WET_TILE", "ARCH.SPACE"], ""),
                ("CEILING", "CEILING", ["FIN.CEILING"], "ceiling"),
                ("WALLS", "UNKNOWN (space kind not established)", ["FIN.PLASTER", "FIN.PAINT"], ""),
                ("SKIRTING", "UNKNOWN (space kind not established)", ["FIN.SKIRTING"], "")],
    "SHAFT": "EXCLUDED: lift / service shaft carries no architectural finish in this scope",
    "DOOR": [("OPENING", "DOOR_ITEM", ["ARCH.DOOR"], "OP"), ("THRESHOLD", "THRESHOLD_FINISH (Q-S6-1)", ["ARCH.THRESHOLD"], "STRIP"),
             ("REVEAL_JAMBS", "REVEAL_FINISH", [], None), ("HEAD_SOFFIT", "REVEAL_FINISH", [], None)],
    "WINDOW": [("OPENING", "WINDOW_ITEM", ["ARCH.WINDOW"], "OP"), ("SILL_STRIP", "SILL / FLOOR (window schedule)", ["ARCH.WINDOW_REVEAL"], "STRIP"),
               ("REVEAL_JAMBS", "REVEAL_FINISH", [], None), ("HEAD_SOFFIT", "REVEAL_FINISH", [], None)],
    "PASSAGE": [("OPENING", "PASSAGE_ITEM", ["ARCH.PASSAGE"], "OP"), ("THRESHOLD", "FLOOR_STRIP (Q-S6-1)", ["ARCH.THRESHOLD"], "STRIP"),
                ("REVEAL_JAMBS", "REVEAL_FINISH", [], None), ("HEAD_SOFFIT", "REVEAL_FINISH", [], None)],
    "WALL_GROUP": [("WALL_LINE", "WALL_RUN", ["ARCH.WALL_RUN"], "walls"), ("WALL_BODY", "MASONRY", ["MAS.BLOCK"], "walls")],
}
KIND_OF = {"WET": "WET", "SERVICE": "WET", "DRY": "DRY", "STAIR": "STAIR", "SHAFT": "SHAFT", "EXTERIOR": "EXTERIOR"}


def blocker(q):
    q = q or ""
    if any(k in q for k in ("Q-S6-1", "Q-S6-4", "(Q7)", "Q1)", "Q-OPN-1")):
        return "OWNER_DECISION" + (" + MISSING_SOURCE (heights)" if "(Q7)" in q else "")
    if any(k in q for k in ("STRIP_NOT_ATTRIBUTED", "STAIR_DRAWN_ON_TWO_PLANS", "STAIR_LANDING_POLYGON")):
        return "ENGINE"
    if any(k in q for k in ("WALL_FINISH_HEIGHT", "UP-CER-004", "STAIR_RISER_NOT_ESTABLISHED", "STAIRWELL_CEILING")):
        return "MISSING_SOURCE (sections / heights)"
    if "WINDOW_REVEAL_FLOOR_STATUS" in q:
        return "MISSING_SOURCE (window schedule / elevations)"
    if "BLOCK_WALL_NOT_ESTABLISHED" in q:
        return "MISSING_SOURCE (wall specification / legend)"
    return "UNCLASSIFIED"


STATE = {"SOURCE_DERIVED": "MEASURED", "PROVISIONAL": "PROVISIONAL", "BOUNDED_EXPOSURE": "PROVISIONAL",
         "BLOCKED_RFI": "BLOCKED", "NOT_APPLICABLE_WITH_EVIDENCE": "NOT_APPLICABLE"}
L = json.load(open(f"{D}/BOQ_LINES.json"))
rooms = json.load(open(f"{D}/ARCH_ROOMS.json"))["rooms"]
ops = json.load(open(f"{D}/ARCH_OPENINGS.json"))["openings"]
UN = json.load(open(f"{D}/UNRESOLVED.json")); UN = UN.get("unresolved", UN) if isinstance(UN, dict) else UN
space_rfi = {u.get("room_id"): u.get("reason") for u in UN if u.get("item") == "ARCH.SPACE"}
by_room = defaultdict(list)
by_op = defaultdict(list)
walls = defaultdict(list)
for l in L:
    loc = l["location"]; el = loc.get("element_id") or ""
    by_room[loc.get("room_id")].append(l)
    for oid in re.findall(r"OP-\d+", el):
        by_op[(loc["floor"], oid)].append(l)
    if l["item_code"] in ("ARCH.WALL_RUN", "MAS.BLOCK"):
        walls[(loc["floor"], el.split(":")[-1])].append(l)
recs = []


def emit(element, ekind, floor, surface, trade, lines, rule=None, quantity_hint=None, space_record=None):
    if not lines and space_record:
        recs.append(dict(element=element, element_kind=ekind, floor=floor, surface=surface, trade=trade, status="BLOCKED",
                         blocker="SPACE_KIND_NOT_ESTABLISHED (one space-level record: label missing or unread)",
                         line_ids="", quantity=None, unit=None, note=(space_record or "")[:120])); return
    if rule:
        recs.append(dict(element=element, element_kind=ekind, floor=floor, surface=surface, trade=trade, status="EXCLUDED",
                         blocker=None, line_ids="", quantity=None, unit=None, note=rule)); return
    if not lines:
        recs.append(dict(element=element, element_kind=ekind, floor=floor, surface=surface, trade=trade, status="MISSING",
                         blocker="NO_EMITTER", line_ids="", quantity=None, unit=None, note=quantity_hint or "")); return
    states = [STATE.get(l["evidence_state"], l["evidence_state"]) for l in lines]
    order = ["BLOCKED", "PROVISIONAL", "MEASURED", "NOT_APPLICABLE"]
    st = next(s for s in order if s in states)
    q = sum(l["measured_net"] for l in lines if l.get("measured_net") is not None) if st in ("MEASURED", "PROVISIONAL") else None
    b = None
    if st == "BLOCKED":
        b = blocker(next((((l.get("rfi") or {}).get("question")) for l in lines if l["evidence_state"] == "BLOCKED_RFI"), ""))
    recs.append(dict(element=element, element_kind=ekind, floor=floor, surface=surface, trade=trade, status=st, blocker=b,
                     line_ids="+".join(l["line_id"] for l in lines), quantity=None if q is None else round(q, 4),
                     unit=lines[0]["unit"], note=""))


for r in rooms:
    if r["class"] not in ("ROOM", "MIXED", "MERGED", "UNLABELLED"):
        continue
    kind = KIND_OF.get(r.get("kind"), "UNKNOWN")
    elig = ELIGIBILITY_V0[kind]
    el = f'{r["room_id"]} ({r.get("name_en") or r["class"]})'
    if isinstance(elig, str):
        emit(el, "SPACE:" + kind, r["floor"], "ALL", "-", [], rule=elig); continue
    mine = by_room.get(r["room_id"], [])
    for surface, trade, codes, suf in elig:
        hit = [l for l in mine if l["item_code"] in codes and (not suf or suf in (l["location"].get("element_id") or ""))]
        if kind == "WET" and trade == "PAINT_OR_TILE (Q7)":
            hit = [l for l in mine if l["item_code"] == "FIN.PAINT"]
        if kind == "STAIR" and surface in ("WALLS", "SKIRTING", "SOFFIT_CEILING"):
            hit = [l for l in mine if l["item_code"] in codes]
        emit(el, "SPACE:" + kind, r["floor"], surface, trade, hit,
             space_record=space_rfi.get(r["room_id"]) if kind == "UNKNOWN" else None)
for o in ops:
    kind = o["kind"]
    lines = by_op.get((o["floor"], o["opening_id"]), [])
    for surface, trade, codes, suf in ELIGIBILITY_V0[kind]:
        if not codes:
            emit(f'{o["floor"]}:{o["opening_id"]} {kind} {o["width_m"]} m', "OPENING:" + kind, o["floor"], surface, trade, [],
                 quantity_hint=f'plan geometry known (width {o["width_m"]} m, wall {o["wall_t_m"]} m); height from schedule / sections')
            continue
        hit = [l for l in lines if l["item_code"] in codes and (suf != "STRIP" or "STRIP" in l["location"]["element_id"])]
        emit(f'{o["floor"]}:{o["opening_id"]} {kind} {o["width_m"]} m', "OPENING:" + kind, o["floor"], surface, trade, hit,
             quantity_hint=("no adjacent measured room and no strip" if not o.get("rooms") else ""))
    if kind == "DOOR":
        wp = [l for l in lines if l["item_code"] == "FIN.WP.DOORWAY"]
        if wp:
            emit(f'{o["floor"]}:{o["opening_id"]} DOOR', "OPENING:DOOR", o["floor"], "DOORWAY_WATERPROOFING", "WATERPROOFING", wp)
if Q2 != "-":
    E = json.load(open(Q2))
    for key, d in E["doors"].items():
        outcome = d["outcome"]
        if outcome == "CONFIRMED_DOOR_OPENING":          # a band opening only under V2.1: in these V2 outputs it has
            outcome = "PROVISIONAL_DOOR_ELEMENT"         # no line, so it is a provisional element here (not skipped)
        fl, ins = key.split(":", 1)
        tag = f'{key} {outcome}' + (" (CONFIRMED under V2.1)" if outcome != d["outcome"] else "")
        d = dict(d, outcome=outcome)
        strip = [l for l in L if l["location"]["floor"] == fl and ins.replace(":", "_") in (l["location"].get("element_id") or "")
                 and l["item_code"] == "ARCH.THRESHOLD"]
        wp = [l for l in L if l["location"]["floor"] == fl and ins in (l["location"].get("element_id") or "") and l["item_code"] == "FIN.WP.DOORWAY"]
        emit(tag, "OPENING:DOOR_" + d["outcome"].split("_")[0], fl, "OPENING", "DOOR_ITEM", [],
             quantity_hint=f'symbol + frame {d.get("frame_span_along_closure_mm")} mm; closure {d.get("closure_wall_to_wall_mm")} mm')
        emit(tag, "OPENING:DOOR_" + d["outcome"].split("_")[0], fl, "THRESHOLD", "THRESHOLD_FINISH (Q-S6-1)", strip)
        if wp:
            emit(tag, "OPENING:DOOR_" + d["outcome"].split("_")[0], fl, "DOORWAY_WATERPROOFING", "WATERPROOFING", wp)
        for s in ("REVEAL_JAMBS", "HEAD_SOFFIT"):
            emit(tag, "OPENING:DOOR_" + d["outcome"].split("_")[0], fl, s, "REVEAL_FINISH", [])
for (fl, grp), ls in sorted(walls.items()):
    for surface, trade, codes, suf in ELIGIBILITY_V0["WALL_GROUP"]:
        emit(f"{fl}:{grp}", "WALL_GROUP", fl, surface, trade, [l for l in ls if l["item_code"] in codes])
summ = {"records": len(recs), "by_status": dict(Counter(r["status"] for r in recs)),
        "blocked_by": dict(Counter(r["blocker"] for r in recs if r["status"] == "BLOCKED")),
        "missing_by_surface": dict(Counter(f'{r["element_kind"]}|{r["surface"]}' for r in recs if r["status"] == "MISSING")),
        "by_element_kind_status": dict(Counter(f'{r["element_kind"].split(":")[0]}|{r["status"]}' for r in recs))}
json.dump({"schema": "URBAN_SURFACE_LEDGER_PROTOTYPE_V0", "eligibility": {k: (v if isinstance(v, str) else [(s, t, c) for s, t, c, _ in v])
                                                                         for k, v in ELIGIBILITY_V0.items()},
           "summary": summ, "records": recs}, open(OUT, "w"), indent=1, ensure_ascii=False)
if OUT_CSV:
    with open(OUT_CSV, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(recs[0].keys())); w.writeheader(); w.writerows(recs)
print(json.dumps(summ, indent=1))
