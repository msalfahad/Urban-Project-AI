"""Qortuba Architectural RC1 lab: the R8.20 build (unchanged - no engine re-tuning, no quantity change) laid out as
the owner-review BOQ: room / site register, room-by-room floor and ceiling breakdowns (from the row records), the
canonical BOQ items with their legacy aliases, the consolidated opening register (doors, entrance, sliding glazed
door, windows, open passages), the PAINTRY object-footprint authority resolution, the physical-identity audit and
the room / trade reconciliation. Every quantity is copied from an engine register row of the build.

    python3 research/external_engine_lab/rc1_qortuba.py <work> <register_dir> [code_commit]
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).parent))

import r8_11_qortuba as Q11                                                                   # noqa: E402
import r8_20_qortuba as Q20                                                                   # noqa: E402
from engine.source import boq_canonical as BC, boq_evidence as BE, footprint_authority as FA  # noqa: E402
from engine.source import opening_register as OR, room_matrix as RM, topology as T            # noqa: E402

REG20 = ROOT / "tests/r8_20/registers"
ROW_TOL = 5e-5           # floor / ceiling rows are published at 4 decimals: half a unit of the 4th decimal
TOL = 1e-6
FLOOR_ITEMS = {"Q-13": "FLR-01", "Q-11": "FLR-02", "Q-12": "FLR-03"}
FIXTURE_KEYS = ("H478", "H482", "H532", "H536", "H541")
FACT_FILES = ("OWNER_PHYSICAL_FACTS.json", "OWNER_METHOD_FACTS.json", "OWNER_FINISH_FACTS.json",
              "URBAN_OWNER_METHOD_RULES.json", "OWNER_PROJECT_CLAIMS.json", "OWNER_CLOSURE_REVIEWS.json")


def jl(p):
    return json.loads(Path(p).read_text())


def r6(v):
    return None if v is None else round(v, 6)


# ----------------------------------------------------------------------------------------------- rooms
def scope_sites(ctx):
    return [u["site"] for u in ctx["rows_new"]["Q-14"]["sites_used"]]


def strips(ctx):
    """The door strips of the measured scope (THRESHOLD sites that touch a measured site), from the Q-13 audit."""
    th = {t["threshold"]: t for t in ctx["thresholds_new"]}
    scope = set(scope_sites(ctx))
    out = []
    for a in ctx["rows_new"]["Q-13"]["strip_audit"]:
        if a["kind"] != "THRESHOLD" or not set(a["sides"]) & scope:
            continue
        t = th[a["strip"]]
        out.append({"key": a["strip"], "door": t["door_occurrence"], "area_m2": a["area_m2"],
                    "physical_site": t["physical_site"], "sides": sorted(a["sides"]), "state": a["state"],
                    "width_mm": t["width_mm"], "thickness_mm": t["thickness_mm"]})
    return sorted(out, key=lambda s: s["key"])


def room_register(ctx):
    ps, sk, wp = ctx["r8_18"]["per_site"], ctx["skirting_v4"]["per_site"], ctx["r8_19"]["waterproofing"]["rooms"]
    used = {u["site"]: u for u in ctx["rows_new"]["Q-14"]["sites_used"]}
    sites = {s["site_id"]: s for s in ctx["new"]["sites"]}
    names = RM.display_names([{"site_id": k, "zones": used[k]["zones"]} for k in used])
    floor_of = {u["site"]: (rid, ctx["rows_new"][rid]["trade_authority"]) for rid in FLOOR_ITEMS
                for u in ctx["rows_new"][rid]["sites_used"]}
    rows = []
    for sid in sorted(used, key=lambda k: names[k]):
        cls = ps[sid]["class"]
        f = ps[sid]["faces"]
        rows.append({"key": sid, "kind": RM.ROOM, "display": names[sid], "site_id": sid,
                     "semantic_zones": used[sid]["zones"], "semantic_class": cls,
                     "zone_decision": used[sid]["decision"], "certified": sites[sid]["status"],
                     "label_occurrences": sites[sid]["labels"],
                     "floor_area_m2": r6(used[sid]["area_m2"]),
                     "floor_trade_row": floor_of[sid][0], "floor_treatment": floor_of[sid][1]["row_treatment"],
                     "skirting": sk[sid]["state"], "wall_finish": sorted(f),
                     "waterproofing": "US-14" if sid in wp else "NONE",
                     "duct_hole_m2": next((d["hole_area_m2"] for d in ctx["rows_new"]["Q-13"]["duct_treatment"]
                                           if d["site"] == sid), 0.0)})
    for s in strips(ctx):
        rows.append({"key": s["key"], "kind": RM.STRIP, "site_id": s["physical_site"],
                     "display": f"DOOR STRIP {s['door']} ({' / '.join(names.get(x, 'OUTSIDE UNIT') for x in s['sides'])})",
                     "semantic_zones": [], "semantic_class": "DOOR_STRIP", "door": s["door"],
                     "floor_area_m2": s["area_m2"], "floor_treatment": s["state"], "sides": s["sides"],
                     "certified": "CERTIFIED", "skirting": "NONE (doorway)", "wall_finish": [],
                     "waterproofing": "NONE (membrane is measured on the room floors; upturn not broken)"})
    return rows, names


# ----------------------------------------------------------------------------------------------- floor / ceiling
def breakdowns(ctx):
    rows = ctx["rows_new"]
    return {rid: RM.row_breakdown(r["sites_used"], r["strip_audit"], r["value"], tol=ROW_TOL)
            for rid, r in rows.items()}


# ----------------------------------------------------------------------------------------------- openings
def _side_of(arr, sites, geom, room):
    (x1, y1), (x2, y2) = geom
    mx, my, dx, dy = (x1 + x2) / 2, (y1 + y2) / 2, x2 - x1, y2 - y1
    ln = (dx * dx + dy * dy) ** 0.5
    nx, ny = -dy / ln, dx / ln
    probe = []
    for d in (5, 20, 40, 60, 100):
        for sg in (1, -1):
            loc, _ = T.locate(arr, sites, (mx + sg * nx * d, my + sg * ny * d), 0.0)
            probe.append((sg, d, loc))
    sgn = next(sg for sg, d, loc in probe if loc == room)
    far = [loc for sg, d, loc in probe if sg == -sgn]
    return far


def window_exterior(ctx, room, geom):
    """EXTERIOR_PROVEN when, beyond the window strip, the far side leaves every site of the drawing (no face)."""
    res = ctx["new"]
    far = _side_of(res["_arr"], res["sites"], geom, room)
    kinds = {s["site_id"]: s["kind"] for s in res["sites"]}
    outside = any(loc is None for loc in far[1:])
    beyond = [loc for loc in far if loc is not None and kinds.get(loc) != "OPENING_SITE"]
    return {"state": "EXTERIOR_PROVEN" if outside else "NOT_PROVEN", "far_side_probe": far,
            "beyond_sites": sorted(set(beyond))}


def opening_observations(ctx):
    ps = ctx["r8_18"]["per_site"]
    th = {t["door_occurrence"]: t for t in ctx["thresholds_new"]}
    marble = {m["threshold"]: m for m in ctx["marble"]}
    obs, seen = [], set()
    for sid in sorted(ps):
        f = next(iter(ps[sid]["faces"].values()))
        for o in f["openings"]:
            kind = o["kind"]
            if kind == "DOOR":
                occ = o["opening"]
            elif kind == "SLIDING_GLAZED_DOOR":
                occ = "SGD-" + o["opening"].split("|")[2]
            else:
                occ = "W-" + o["opening"].split("|")[1]
            hb = "OWNER_PROJECT_PARAMETER"
            rec = {"occurrence": occ, "site": sid, "kind": kind, "width_m": r6(o["width_m"]), "width_basis": "SOURCE",
                   "height_m": o["height_m"], "height_basis": hb, "height_authority": o["height_authority"],
                   "sill_m": o["sill_m"] if kind == "WINDOW" else 0.0,
                   "sill_basis": "OWNER_FACT" if kind == "WINDOW" else "SOURCE",
                   "sill_authority": o.get("sill_authority"), "sources": o["sources"],
                   "entity": o["opening"]}
            if kind == "DOOR":
                t = th.get(occ)
                rec |= {"door_symbol": t["door_symbol"] if t else None,
                        "leaf_type": "HINGED_SWING (door arc symbol)" if t and "ELLIPTICAL_ARC" in t["door_symbol"]
                        else "NOT_ESTABLISHED",
                        "threshold_strip": t["threshold"] if t else None,
                        "marble_threshold": (marble[t["threshold"]]["authority"] if t and t["threshold"] in marble
                                             else "NONE")}
            if kind == "WINDOW":
                ex = window_exterior(ctx, sid, o["geom"])
                rec["exteriority"] = ex
                rec["other_side"] = ("EXTERIOR (outside the drawn building)" if ex["state"] == "EXTERIOR_PROVEN" else
                                     "UNLABELLED REGION " + ",".join(ex["beyond_sites"]))
                if ex["state"] == "EXTERIOR_PROVEN":
                    rec |= {"material": "ALUMINIUM", "material_basis": "URBAN_STANDARD",
                            "material_authority": "US-13 INTERIOR_DOORS_ARE_PVC_EXTERIOR_OPENINGS_ARE_ALUMINIUM "
                                                  "(exterior window; far side outside the drawing by geometry)"}
                else:
                    rec |= {"material_note": "US-13 makes an EXTERIOR window aluminium; the far side is an "
                                             f"unlabelled region {ex['beyond_sites']} - exterior not proven"}
            if kind == "SLIDING_GLAZED_DOOR":
                rec |= {"physical_class_authority": "QORTUBA-NEW-HALL-PAINTRY-SLIDING-GLASS-DOOR-OWNER-001@v1",
                        "floor_contact": "OPENING_TO_FLOOR (owner fact)",
                        "material_note": "US-13 covers EXTERIOR sliding systems only; this one is internal "
                                         "(HALL / PAINTRY): frame material NOT_ESTABLISHED"}
            obs.append(rec)
            seen.add(occ)
    return obs


def opening_register(ctx, names):
    obs = opening_observations(ctx)
    scope = scope_sites(ctx)
    # role: the owner fact names the main apartment entrance by its door symbol (H680 / H681 of occurrence 677)
    fact = jl(ROOT / "data/registry/OWNER_PHYSICAL_FACTS.json")
    ent = next(f for f in fact["facts"] if f["fact_id"] == "QORTUBA-NEW-MAIN-ENTRANCE-MARBLE-OWNER-001")
    ent_occ = sorted({"I" + p["key"].split("|")[2] for p in ent["parts"] if p["key"].split("|")[2]})
    for o in obs:
        if o["kind"] == "DOOR":
            o["role"] = "ENTRANCE" if o["occurrence"] in ent_occ else "INTERNAL"
            if o["role"] == "INTERNAL":
                o |= {"material": "PVC", "material_basis": "URBAN_STANDARD",
                      "material_authority": "US-13 INTERIOR_DOORS_ARE_PVC_EXTERIOR_OPENINGS_ARE_ALUMINIUM"}
            else:
                o |= {"role_authority": f"QORTUBA-NEW-MAIN-ENTRANCE-MARBLE-OWNER-001@v{ent['version']}",
                      "height_note": "QP-21 is the INTERNAL door height parameter; the frozen wall-face method "
                                     "applies it to every door occurrence incl. this entrance - entrance height "
                                     "not separately established",
                      "material_note": "US-13 names interior doors (PVC) and exterior openings (aluminium); an "
                                       "apartment entrance to a common area is neither by name: NOT_ESTABLISHED",
                      "other_side": "OUTSIDE_UNIT (" + ",".join(
                          s for t in ctx["thresholds_new"] if t["door_occurrence"] == o["occurrence"]
                          for a in ctx["rows_new"]["Q-13"]["strip_audit"] if a["strip"] == t["threshold"]
                          for s in a["sides"] if s not in scope) + ")"}
    # the door outside the measured unit (its strip touches no measured site)
    for t in ctx["thresholds_new"]:
        if t["door_occurrence"] not in {o["occurrence"] for o in obs}:
            obs.append({"occurrence": t["door_occurrence"], "site": t["physical_site"], "kind": "DOOR",
                        "width_m": r6(t["width_mm"] / 1000), "width_basis": "SOURCE", "height_m": None,
                        "height_basis": "NOT_ESTABLISHED", "sources": t["wall_opening_sources"],
                        "role": "OUT_OF_SCOPE", "note": "door strip touches no measured site (another unit)"})
    # open passages (inside one certified site each: from / to are zones of that site)
    for sid in scope:
        for p in ctx["r8_18"]["per_site"][sid].get("passages_in_site") or ():
            with_head = p["head"] == "OPEN_PASSAGE_WITH_HEAD"
            zones = ctx["r8_18"]["per_site"][sid]["zones"]
            obs.append({"occurrence": p["passage_id"], "site": sid, "other_side": sid, "kind": OR.PASSAGE,
                        "width_m": r6(p["width_m"]), "width_basis": "SOURCE",
                        "height_m": p["head_height_m"] if with_head else None,
                        "height_basis": "OWNER_FACT" if with_head else "NOT_ESTABLISHED",
                        "height_authority": p["head_authority"], "head_condition": p["head"],
                        "head_authority": p["head_authority"], "from_zone": zones[0], "to_zone": zones[-1],
                        "soffit": "OPENING SOFFIT (plaster / paint reveal), NOT ceiling" if with_head else
                        "NONE - the ceiling continues through the passage",
                        "jambs": "PLASTER + PAINT reveals where the jamb is a physical wall end (reveal register)",
                        "sources": [p["passage_id"]], "material": None})
    recs = OR.consolidate(obs, scope_sites=scope, tol=TOL)
    for r in recs:
        r["from_display"] = names.get(r["from_site"], r["from_site"])
        r["to_display"] = names.get(r["to_site"], r["to_site"])
        if r["kind"] == OR.PASSAGE:
            r["door_present"] = False
    return recs, OR.validate(recs)


# ----------------------------------------------------------------------------------------------- footprint
def footprint(ctx):
    """OBJECT_FOOTPRINT_AUTHORITY_V1 for every floor-finish site with proven objects; the PAINTRY fixture outline is
    described by the planar faces it makes with the site boundary (shapely, lab-only, report diagnostic)."""
    import shapely
    from shapely.geometry import LineString, Polygon
    from shapely.ops import polygonize, unary_union
    res = ctx["new"]
    ff = jl(ROOT / "data/registry/OWNER_FINISH_FACTS.json")["facts"]
    fp = next(f for f in ff if f["fact_id"] == "QORTUBA-NEW-FLOOR-OBJECT-FOOTPRINT-OWNER-001")
    pol = [{"policy_id": f"{fp['fact_id']}@v{fp['version']}", "trade": fp["scope"]["trade"],
            "space_classes": fp["scope"]["space_classes"], "object_classes": [fp["statement"]["object_class"]],
            "treatment": fp["statement"]["treatment"],
            "excludes": [{"space_class": c, "text": "is_not: a rule for wet / service floors"}
                         for c in ("WET_SERVICE_ROOM", "SERVICE_ROOM")]}]
    cls = {sid: v["class"] for sid, v in ctx["r8_18"]["per_site"].items()}
    out = {}
    for rid in FLOOR_ITEMS:
        for sid, counts in sorted((ctx["rows_new"][rid]["implicit_object_footprints"] or {}).items()):
            objs = []
            for k, a in sorted(res["roles"]["roles"].items()):
                if a.role not in Q11.OBJECT_ROLES or k not in res["_probe_geom"]:
                    continue
                kind, g = res["_probe_geom"][k]
                pt = ((g[0] + g[2]) / 2, (g[1] + g[3]) / 2) if kind == "SEGMENT" else (g[0], g[1])
                if T.locate(res["_arr"], res["sites"], pt, 0.0)[0] == sid:
                    objs.append({"key": k, "object_class": a.role, "layer": a.evidence.get("source_layer"),
                                 "entity_type": a.evidence.get("ENTITY_TYPE"),
                                 "geometry": [round(x, 4) for x in g] if kind == "SEGMENT" else None})
            r = FA.resolve(site=sid, space_class=cls[sid], trade="FLOOR_FINISH", objects=objs, policies=pol)
            r["row"] = rid
            r["counts"] = counts
            if r["state"] != FA.RESOLVED:
                site = next(s for s in res["sites"] if s["site_id"] == sid)
                x0, y0, x1, y1 = site["bbox"]
                ring = Polygon([(x0, y0), (x1, y0), (x1, y1), (x0, y1)])
                rect = abs(ring.area - site["area"]) < 1e-6
                segs = [o["geometry"] for o in objs if o["geometry"]]
                g = unary_union([shapely.set_precision(x, 0.001) for x in
                                 [LineString([(s[0], s[1]), (s[2], s[3])]) for s in segs] + [ring.exterior]])
                u2 = ctx["inp_new"].unit_native_to_mm ** 2 / 1e6
                faces = sorted((round(f.area * u2, 6), [[round(c, 2) for c in p] for p in f.exterior.coords])
                               for f in polygonize(g))
                r["outline_faces"] = {"site_is_rectangle": rect, "faces_m2": [f[0] for f in faces],
                                      "faces": [{"area_m2": a, "ring": ring_} for a, ring_ in faces],
                                      "sum_m2": round(sum(f[0] for f in faces), 6),
                                      "note": "planar faces of the source FIXTURE lines + the site boundary; WHICH "
                                              "face is the counter is not stated by geometry"}
            out[f"{rid}|{sid}"] = r
    return out


# ----------------------------------------------------------------------------------------------- canonical BOQ
def _status(blockers):
    return BC.SUBTOTAL if any(BE.classify(b) == BE.QUANTITY_AFFECTING for b in blockers) else BC.COMPLETE


def canonical(ctx, names, bd, recs, fp):
    rows, r19 = ctx["rows_new"], ctx["r8_19"]
    tr, sk, wp = r19["trade_rows"], ctx["skirting_v4"], r19["waterproofing"]
    boq20 = {r["evidence_row"]: r for r in jl(REG20 / "BOQ_REPORT_SHADOW.json")["report"]["rows"]
             if r["ROW_KIND"] == "TOTAL"}
    run = jl(REG20 / "BOQ_REPORT_SHADOW.json")["report"]["run"]
    ssh = lambda s: names.get(s, s)                                      # noqa: E731
    floor = {e["key"]: e for rid in FLOOR_ITEMS for e in bd[rid]["entries"]}
    items = []

    def ent(e):
        return {"key": e["key"], "label": ssh(e["key"]) if e["kind"] == RM.ROOM else f"door strip {e['key']}",
                "qty": r6(e["qty"]), "kind": e["kind"], "site_area_m2": r6(e.get("site_area_m2")),
                "inside_effects": e.get("inside_effects")}

    desc = {"FLR-01": ("أرضيات بورسلين - الغرف الجافة (من الجدار إلى الجدار)",
                       "Porcelain floor - dry rooms, wall to wall (incl. same-finish door strips)"),
            "FLR-02": ("أرضيات سيراميك - الحمامات", "Ceramic floor tile - bathrooms"),
            "FLR-03": ("أرضيات سيراميك - غرفة التحضير (PAINTRY)", "Ceramic floor tile - PAINTRY (service room)")}
    alias_of = {"FLR-02": "Q-03", "FLR-03": "Q-03P"}
    for rid, cid in FLOOR_ITEMS.items():
        r = rows[rid]
        legacy = [{"id": f"QOR-R819-{rid}", "relation": BC.SAME, "value": boq20[rid]["QTY"],
                   "note": "R8.19 / R8.20 BOQ shadow line"},
                  {"id": f"OWNER-RULES-V1:{rid}", "relation": BC.HISTORICAL, "value": None,
                   "note": "old revision takeoff (OWNER RULES V1), same meaning, another source"}]
        if cid in alias_of:
            a = alias_of[cid]
            legacy.append({"id": f"QOR-R819-{a}", "relation": BC.MISLABELLED, "value": boq20[a]["QTY"],
                           "keys": [u["site"] for u in rows[a]["sites_used"]],
                           "note": f"{a} was historically WATERPROOFING floor (OWNER RULES V1) but the R8.19 / R8.20 BOQ "
                                   "shadow described it as ceramic floor - same sites, same m2: a duplicate line"})
        blockers = list(r["release_blockers"])
        notes = []
        if cid == "FLR-03":
            p = fp.get(f"{rid}|{r['sites_used'][0]['site']}")
            notes.append("OPEN OWNER QUESTION: is the ceramic floor laid under the fixed kitchen counter drawn by "
                         f"FIXTURE lines {', '.join(FIXTURE_KEYS)}? YES -> {r['value']} m2 stands; NO -> the counter "
                         f"footprint face(s) {p['outline_faces']['faces_m2'] if p else None} m2 come off")
        items.append(BC.item(cid, trade="ARCHITECTURAL_FLOOR_FINISH", layer="FLOOR_FINISH_SURFACE", unit="m2",
                             qty=r["value"], status=_status(blockers), description_ar=desc[cid][0],
                             description_en=desc[cid][1], breakdown=[ent(e) for e in bd[rid]["entries"]],
                             legacy=legacy, source="DXF (K2 ezdxf), TS01 certified topology",
                             rules=[r["trade_authority"]["rule"], r["trade_authority"]["semantic_class_rule"]],
                             blockers=blockers, notes=notes,
                             evidence=f"rows_new.{rid} (R8.20 build; QUANTITY_REGRESSION {rid})"))
    mq, mar = ctx["marble_quantities"], {m["threshold"]: m for m in ctx["marble"]}
    mrb_bd = lambda f: [{"key": k, "label": f"threshold {k} (door {next(t['door_occurrence'] for t in ctx['thresholds_new'] if t['threshold'] == k)})",  # noqa: E501,E731
                         "qty": mar[k][f], "kind": RM.STRIP} for k in sorted(mar)]
    mrb_auth = sorted({m["authority"] for m in ctx["marble"]})
    mrb_block = list(boq20["MARBLE_THRESHOLD_PLAN_AREA_M2"]["NOTES_BLOCKERS"])
    items.append(BC.item("MRB-01", trade="MARBLE_STONE", layer="FLOOR_FINISH_SURFACE", unit="m2",
                         qty=mq["MARBLE_THRESHOLD_PLAN_AREA_M2"], status=_status(mrb_block),
                         description_ar="عتبات رخام (برطاش) - المساحة", description_en="Marble thresholds - plan area",
                         breakdown=mrb_bd("plan_area_m2"), measure_pair="MRB-02", rules=mrb_auth,
                         blockers=mrb_block, source="door face closures (source)",
                         legacy=[{"id": "QOR-R819-MARBLE-THRESHOLD-PLAN-AREA-M2", "relation": BC.SAME,
                                  "value": boq20["MARBLE_THRESHOLD_PLAN_AREA_M2"]["QTY"]}],
                         notes=["MEASURE PAIR with MRB-02: the SAME four thresholds - price ONE basis"],
                         evidence="marble_quantities.MARBLE_THRESHOLD_PLAN_AREA_M2"))
    items.append(BC.item("MRB-02", trade="MARBLE_STONE", layer="FLOOR_FINISH_SURFACE", unit="lm",
                         qty=mq["MARBLE_THRESHOLD_LENGTH_LM"], status=_status(mrb_block),
                         description_ar="عتبات رخام (برطاش) - الطول", description_en="Marble thresholds - length",
                         breakdown=mrb_bd("length_lm"), measure_pair="MRB-01", rules=mrb_auth, blockers=mrb_block,
                         source="door face closures (source)",
                         legacy=[{"id": "QOR-R819-MARBLE-THRESHOLD-LENGTH-LM", "relation": BC.SAME,
                                  "value": boq20["MARBLE_THRESHOLD_LENGTH_LM"]["QTY"]}],
                         notes=["MEASURE PAIR with MRB-01 - price ONE basis; 2 cm = vertical rise only"],
                         evidence="marble_quantities.MARBLE_THRESHOLD_LENGTH_LM"))
    q14 = rows["Q-14"]
    items.append(BC.item("CLG-01", trade="CEILING", layer="CEILING", unit="m2", qty=q14["value"],
                         status=_status(q14["release_blockers"]), description_ar="أسقف - حسب المساحة",
                         description_en="Ceiling by area (duct footprint and Hall / Lobby passage soffit excluded)",
                         breakdown=[ent(e) for e in bd["Q-14"]["entries"]], blockers=q14["release_blockers"],
                         source="DXF (K2 ezdxf), TS01 certified topology", rules=[q14["trade_authority"]["rule"]],
                         legacy=[{"id": "QOR-R819-Q-14", "relation": BC.SAME, "value": boq20["Q-14"]["QTY"]},
                                 {"id": "OWNER-RULES-V1:Q-14", "relation": BC.HISTORICAL, "value": None}],
                         evidence="rows_new.Q-14"))
    trade_items = (("PLS-01", "DRY_WALL_PLASTER", "PLASTER_INTERNAL", "PLASTER", "Q-08"),
                   ("PLS-02", "WET_SERVICE_REVEAL_PLASTER", "PLASTER_INTERNAL", "PLASTER", None),
                   ("PNT-01", "DRY_WALL_PAINT", "PAINT", "PAINT", "Q-09"),
                   ("WTL-01", "WET_SERVICE_WALL_TILE", "ARCHITECTURAL_WALL_FINISH", "WALL_TILE", "Q-05 + Q-06"),
                   ("WTP-01", "WET_WALL_TILE_PREP", "ARCHITECTURAL_WALL_FINISH", "WALL_TILE_PREP", "Q-10"))
    items20 = jl(REG20 / "BOQ_REPORT_SCHEMA.json")["items"]
    for cid, row, trade, layer, hist in trade_items:
        t = tr[row]
        rooms = {sid: v for sid, v in t["rooms"].items() if v["surfaces"] or v["total_m2"]}
        items.append(BC.item(cid, trade=trade, layer=layer, unit="m2", qty=t["COMPLETE_M2"],
                             status=_status(boq20[row]["NOTES_BLOCKERS"]),
                             description_ar=items20[row]["description_ar"], description_en=items20[row]["description_en"],
                             breakdown=[{"key": sid, "label": ssh(sid), "qty": v["total_m2"], "kind": RM.ROOM,
                                         "components": {k: v[k] for k in ("wall_plane_m2", "column_face_m2",
                                                                          "obstacle_face_m2", "jamb_reveals_m2",
                                                                          "head_reveals_m2")},
                                         "height_m": v["height_m"], "height_authority": v["height_authority"]}
                                        for sid, v in sorted(rooms.items())],
                             blockers=boq20[row]["NOTES_BLOCKERS"], rules=boq20[row]["RULE_AUTHORITY"],
                             source="wall-face V2 surfaces (R8.19 rebuild)",
                             legacy=[{"id": f"QOR-R819-{row.replace('_', '-')}", "relation": BC.SAME,
                                      "value": boq20[row]["QTY"]}] +
                                    ([{"id": f"OWNER-RULES-V1:{hist}", "relation": BC.HISTORICAL, "value": None}]
                                     if hist else []),
                             evidence=f"r8_19.trade_rows.{row}"))
    for cid, row, layer, hist, d in (("SKT-01", "SKIRTING", "SKIRTING", "Q-01", items20["SKIRTING"]),
                                     ("HPR-01", "HIDDEN_PROFILE", "HIDDEN_PROFILE", "Q-02", items20["HIDDEN_PROFILE"])):
        items.append(BC.item(cid, trade="SKIRTING_PROFILE", layer=layer, unit="lm", qty=sk["PAYABLE_LM"],
                             status=_status(boq20[row]["NOTES_BLOCKERS"]), description_ar=d["description_ar"],
                             description_en=d["description_en"],
                             breakdown=[{"key": sid, "label": ssh(sid), "qty": v["payable_lm"], "kind": RM.ROOM,
                                         "state": v["state"]} for sid, v in sorted(sk["per_site"].items())],
                             blockers=boq20[row]["NOTES_BLOCKERS"], rules=boq20[row]["RULE_AUTHORITY"],
                             source="WALL_CONTACT_PATH_POLICY_V4 (skirting V4)",
                             legacy=[{"id": f"QOR-R819-{row.replace('_', '-')}", "relation": BC.SAME,
                                      "value": boq20[row]["QTY"]},
                                     {"id": f"OWNER-RULES-V1:{hist}", "relation": BC.HISTORICAL, "value": None}],
                             notes=["SKT-01 and HPR-01 share ONE path (US-08) but are two materials: two items, "
                                    "never merged and never one quantity"],
                             evidence="skirting_v4.PAYABLE_LM"))
    for cid, key, unit, hist, d in (
            ("WPF-01", "WATERPROOFING_FLOOR_M2", "m2", ("Q-03", "Q-03P"),
             ("عزل مائي - أرضيات الحمامات وغرفة التحضير", "Waterproofing membrane - floor (bathrooms + PAINTRY)")),
            ("WPU-01", "WATERPROOFING_UPTURN_LM", "lm", ("Q-04", "Q-04P"),
             ("عزل مائي - الرفرف الرأسي 15 سم", "Waterproofing upturn 0.15 m - gross wet-room perimeter"))):
        items.append(BC.item(cid, trade="WATERPROOFING", layer="WATERPROOF_" + key.split("_")[1], unit=unit,
                             qty=wp["totals"][key], status=_status(boq20[key]["NOTES_BLOCKERS"]),
                             description_ar=d[0], description_en=d[1],
                             breakdown=[{"key": sid, "label": ssh(sid), "qty": v[key], "kind": RM.ROOM,
                                         "authority": v["authority"]} for sid, v in sorted(wp["rooms"].items())],
                             blockers=boq20[key]["NOTES_BLOCKERS"], rules=boq20[key]["RULE_AUTHORITY"],
                             source="WATERPROOFING_POLICY_V1",
                             legacy=[{"id": f"QOR-R819-{key.replace('_', '-')}", "relation": BC.SAME,
                                      "value": boq20[key]["QTY"]}] +
                                    [{"id": f"OWNER-RULES-V1:{h}", "relation": BC.HISTORICAL, "value": None,
                                      "note": "old-revision waterproofing row of the same meaning"} for h in hist],
                             evidence=f"r8_19.waterproofing.totals.{key}"))
    # openings: counts and areas from the opening register (one record per occurrence)
    ins = [r for r in recs if r["state"] == OR.IN_SCOPE]
    sch = OR.schedules(recs)
    one = lambda r: {"key": r["opening_id"], "label": f"{r['opening_id']} {r['from_display']} / {r['to_display']}",  # noqa: E731
                     "qty": 1, "kind": "OPENING"}
    area = lambda r: {"key": r["opening_id"], "label": f"{r['opening_id']} {r['clear_width_m']} x {r['height_m']}",  # noqa: E731
                      "qty": r["area_m2"], "kind": "OPENING", "basis": r["area_basis"]}
    pick = lambda ids: [r for r in ins if r["opening_id"] in ids]   # noqa: E731
    doors, ent_, sgd, win = (pick(sch["internal_doors"]), pick(sch["entrance_doors"]),
                             pick(sch["sliding_glazed_doors"]), pick(sch["windows"]))
    op_items = (("DOR-01", "DOOR_INTERNAL", "nr", len(doors), [one(r) for r in doors], None,
                 ("أبواب داخلية", "Internal doors (hinged swing; width from source, height QP-21 owner parameter)"),
                 ["OWNER-RULES-V1:Q-16"]),
                ("DOR-02", "DOOR_ENTRANCE", "nr", len(ent_), [one(r) for r in ent_], None,
                 ("باب المدخل الرئيسي للشقة", "Main apartment entrance door"), []),
                ("SGD-01", "SLIDING_GLAZED_DOOR", "nr", len(sgd), [one(r) for r in sgd], "SGD-02",
                 ("باب زجاج سحاب داخلي (الصالة / التحضير)", "Internal sliding glass door (HALL / PAINTRY) - count"),
                 ["OWNER-RULES-V1:Q-17"]),
                ("SGD-02", "SLIDING_GLAZED_DOOR", "m2", r6(sum(r["area_m2"] for r in sgd)), [area(r) for r in sgd],
                 "SGD-01", ("باب زجاج سحاب داخلي - المساحة", "Internal sliding glass door - opening area"), []),
                ("WIN-01", "WINDOW", "nr", len(win), [one(r) for r in win], "WIN-02",
                 ("شبابيك", "Windows - count"), ["OWNER-RULES-V1:Q-15"]),
                ("WIN-02", "WINDOW", "m2", r6(sum(r["area_m2"] for r in win)), [area(r) for r in win], "WIN-01",
                 ("شبابيك - المساحة", "Windows - opening area (width source x height QP-22 1.50 m)"), []))
    for cid, layer, unit, qty, bdl, pair, d, hist in op_items:
        items.append(BC.item(cid, trade="OPENINGS", layer=layer, unit=unit, qty=qty, status=BC.COMPLETE,
                             description_ar=d[0], description_en=d[1], breakdown=bdl, measure_pair=pair,
                             source="opening register (wall-face V2 opening records + door closures)",
                             rules=["OPENING_REGISTER_V1"],
                             blockers=["SOURCE_ANCHOR: DWG <-> DXF identity NOT_ESTABLISHED",
                                       "SHADOW_ONLY: no baseline approval, no migration transaction"],
                             legacy=[{"id": h, "relation": BC.HISTORICAL, "value": None} for h in hist],
                             notes=["heights are owner project parameters (no height is drawn)"] if unit == "m2" else [],
                             evidence="OPENING_REGISTER"))
    return BC.build(items, run=run)


# ----------------------------------------------------------------------------------------------- audits
def floor_partition(model, rooms, ctx):
    """Every measured site and every in-scope door strip is in exactly ONE floor-finish surface item (m2)."""
    fl = [i for i in model["items"] if i["layer"] == "FLOOR_FINISH_SURFACE" and i["unit"] == "m2"]
    owner = {}
    for i in fl:
        for b in i["room_breakdown"]:
            owner.setdefault(b["key"], []).append(i["canonical_item_id"])
    keys = {r["key"] for r in rooms}
    twice = {k: v for k, v in owner.items() if len(v) > 1}
    missing = sorted(keys - set(owner))
    phys = r6(sum(r["floor_area_m2"] for r in rooms))
    fin = r6(sum(i["qty"] for i in fl))
    return {"items": [i["canonical_item_id"] for i in fl], "keys": len(keys), "in_two_items": twice,
            "in_no_item": missing, "extra": sorted(set(owner) - keys),
            "physical_floor_m2": phys, "finish_items_sum_m2": fin,
            "difference_m2": r6(fin - phys), "within_row_rounding": abs(fin - phys) <= ROW_TOL * len(fl),
            "state": "PASS" if not twice and not missing and abs(fin - phys) <= ROW_TOL * len(fl) else "FAIL"}


def surface_identity(ctx, model, bd, recs):
    r19 = ctx["r8_19"]
    q14 = {a["strip"]: a for a in ctx["rows_new"]["Q-14"]["strip_audit"]}
    soffit = [a for a in q14.values() if a["state"] == "SOFFIT_EXCLUDED_FROM_CEILING"]
    rev = r19["reveals"]
    head = [x for x in rev if x["kind"] == "OPEN_PASSAGE_WITH_HEAD" and x["surface"] == "TOP_REVEAL"]
    marble = {m["threshold"] for m in ctx["marble"]}
    floor_strip_items = {b["key"]: i["canonical_item_id"] for i in model["items"]
                         if i["layer"] == "FLOOR_FINISH_SURFACE" for b in i["room_breakdown"] if b["kind"] == RM.STRIP}
    checks = {
        "wall_plane_vs_column_vs_duct_vs_reveals (R8.19 guard)": r19["surface_guard"]["state"],
        "all_wall_surfaces_once (R8.18 guard, 190 surfaces)": r19["double_count_guard_r8_18"]["state"],
        "below_sill_and_above_opening_vs_wall": "PASS" if r19["all_sites_reconcile"] else "FAIL",
        "passage_soffit_vs_ceiling": "PASS" if len(soffit) == 1 and len(head) == 1 and head[0]["opening"] ==
        soffit[0]["strip"] and abs(head[0]["area_m2"] + soffit[0]["contribution_m2"]) <= TOL else "FAIL",
        "threshold_vs_floor_finish": "PASS" if all(floor_strip_items.get(k) in ("MRB-01", "MRB-02") for k in marble)
        and all(v == "FLR-01" for k, v in floor_strip_items.items() if k not in marble) else "FAIL",
        "duct_footprint_vs_floor_and_ceiling": "PASS" if all(d["effect"] == "EXCLUDED_FROM_ROOM_FLOOR" for d in
                                                             ctx["rows_new"]["Q-13"]["duct_treatment"]) else "FAIL"}
    return {"checks": checks, "state": "PASS" if set(checks.values()) == {"PASS"} else "FAIL",
            "soffit": [{"strip": a["strip"], "excluded_m2": a["contribution_m2"]} for a in soffit],
            "soffit_reveals": [{k: x[k] for k in ("opening", "surface", "owner_site", "area_m2", "finish")}
                               for x in head],
            "compatible_trades_on_one_surface": ["PLASTER + PAINT (dry faces)", "WALL_TILE + WALL_TILE_PREP (wet "
                                                 "faces)", "FLOOR finish + WATERPROOFING membrane (wet floors)",
                                                 "SKIRTING + HIDDEN_PROFILE (one path, two materials)"]}


def regression(ctx, model):
    q = jl(REG20 / "QUANTITY_REGRESSION.json")["rows"]
    by = {i["canonical_item_id"]: i["qty"] for i in model["items"]}
    pairs = {"Q-13": "FLR-01", "Q-11": "FLR-02", "Q-12": "FLR-03", "Q-14": "CLG-01",
             "DRY_WALL_PLASTER": "PLS-01", "WET_SERVICE_REVEAL_PLASTER": "PLS-02", "DRY_WALL_PAINT": "PNT-01",
             "WET_SERVICE_WALL_TILE": "WTL-01", "WET_WALL_TILE_PREP": "WTP-01", "SKIRTING": "SKT-01",
             "HIDDEN_PROFILE": "HPR-01", "MARBLE_THRESHOLD_PLAN_AREA_M2": "MRB-01",
             "MARBLE_THRESHOLD_LENGTH_LM": "MRB-02", "WATERPROOFING_FLOOR_M2": "WPF-01",
             "WATERPROOFING_UPTURN_LM": "WPU-01"}
    rows = {k: {"R8.20": q[k]["R8.20"], "RC1": by[v], "canonical": v, "unchanged": q[k]["R8.20"] == by[v]}
            for k, v in pairs.items()}
    rows["Q-03"] = {"R8.20": q["Q-03"]["R8.20"], "RC1": None, "canonical": "alias in FLR-02 (MISLABELLED) + "
                    "OWNER-RULES-V1 meaning in WPF-01", "unchanged": True, "not_a_summary_line": True}
    rows["Q-03P"] = {"R8.20": q["Q-03P"]["R8.20"], "RC1": None, "canonical": "alias in FLR-03 (MISLABELLED) + "
                     "OWNER-RULES-V1 meaning in WPF-01", "unchanged": True, "not_a_summary_line": True}
    return {"rows": rows, "all_unchanged": all(v["unchanged"] for v in rows.values()),
            "covers_all_17_r8_20_rows": sorted(rows) == sorted(q), "r8_20": ctx["regression_20"]["all_unchanged"]}


def build(work, commit=None):
    ctx = Q20.build(work, commit)
    return rc1(ctx)


def rc1(ctx):
    rooms, names = room_register(ctx)
    bd = breakdowns(ctx)
    recs, ov = opening_register(ctx, names)
    fp = footprint(ctx)
    model = canonical(ctx, names, bd, recs, fp)
    ctx["rc1"] = {"rooms": rooms, "names": names, "breakdowns": bd, "openings": recs, "opening_validation": ov,
                  "footprint": fp, "model": model, "model_validation": BC.validate(model, tol=ROW_TOL),
                  "floor_partition": floor_partition(model, rooms, ctx),
                  "surface_identity": surface_identity(ctx, model, bd, recs), "regression": regression(ctx, model)}
    room_items = [i for i in model["items"] if i["trade"] != "OPENINGS"]
    ctx["rc1"]["matrix"] = RM.matrix([{k: r[k] for k in ("key", "kind", "display")} for r in rooms], room_items,
                                     tol=ROW_TOL)
    return ctx


def main(work, regdir, commit=None):
    import rc1_registers as REGS
    ctx = build(work, commit)
    regs = REGS.registers(ctx)
    regdir = Path(regdir)
    regdir.mkdir(parents=True, exist_ok=True)
    for n, o in regs.items():
        (regdir / f"{n}.json").write_text(json.dumps(o, indent=1, ensure_ascii=False, default=str) + "\n")
    r = ctx["rc1"]
    print(json.dumps({"model": r["model_validation"]["state"], "matrix": r["matrix"]["state"],
                      "openings": r["opening_validation"]["state"], "partition": r["floor_partition"]["state"],
                      "surfaces": r["surface_identity"]["state"], "regression": r["regression"]["all_unchanged"],
                      "xlsx": regs["BOQ_XLSX_STATUS"]["readback_validation"]["state"]}, indent=1))
    return regs, ctx


if __name__ == "__main__":
    main(*sys.argv[1:4])
