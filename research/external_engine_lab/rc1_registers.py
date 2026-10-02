"""Qortuba RC1 registers + the owner-review workbook model. Every number comes from the rc1_qortuba build (no number
typed in); the workbook is built by engine/boq_rc1_xlsx.py and read back against the registers.
"""

from __future__ import annotations

import datetime
import hashlib
import json
import tempfile
from pathlib import Path

import rc1_qortuba as Q
from engine import boq_rc1_xlsx as BX
from engine.source import boq_canonical as BC, footprint_authority as FA, opening_register as OR
from engine.source import room_matrix as RM

ROOT = Path(__file__).resolve().parents[2]
REG20 = ROOT / "tests/r8_20/registers"
CREATED = datetime.datetime(2026, 10, 2)
XLSX_NAME = "URBAN_QTO_QORTUBA_ARCHITECTURAL_RC1.xlsx"
GATES = {"QORTUBA_RC1_REFERENCE_READY": None, "FULL_VILLA_BLIND_TEST_READY": "YES (intake contract + plan ready; "
         "awaiting the owner's files)", "MIGRATION_PLANNING_READY": "YES", "MIGRATION_EXECUTION_READY": "NO",
         "PRODUCTION_MIGRATION": "NO"}
DXF = "df0e1d690285f5455b3b5acebe7e20eaee2d1c8aa3743b633a9fd257c6d6f315"
DWG = "e4babbc2ded1"


def jl(p):
    return json.loads(Path(p).read_text())


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def dg(o):
    return hashlib.sha256(json.dumps(o, sort_keys=True, ensure_ascii=False, default=str).encode()).hexdigest()


def items_by(model):
    return {i["canonical_item_id"]: i for i in model["items"]}


# ------------------------------------------------------------------------------------------- workbook model
def workbook(ctx):
    r = ctx["rc1"]
    model, rooms, recs, names = r["model"], r["rooms"], r["openings"], r["names"]
    it = items_by(model)
    cells = {row["key"]: row["cells"] for row in r["matrix"]["rows"]}
    src = []
    sheets = {}

    def add(sheet, rows, row, col, value, ref):
        src.append({"sheet": sheet, "row": row, "col": col, "value": value, "ref": ref})

    sheets["00_READ_ME"] = {"role": "INFO", "header": ["URBAN QTO - QORTUBA ARCHITECTURAL RC1 (owner review)"],
                            "rows": [[x] for x in (
                                "This workbook is a VIEW over the engine registers. It calculates nothing: no "
                                "formula, no sum, no correction factor. Every quantity is copied from one register row.",
                                "01_BOQ_SUMMARY is the ONLY additive sheet: one line per canonical BOQ item.",
                                "Every other sheet is a BREAKDOWN or SCHEDULE of summary lines - never add it to the "
                                "summary, and never add two sheets together.",
                                "LEGACY IDS (Q-03, Q-11 ...) are shown as attributes of their canonical item. They are "
                                "NOT separate quantities.",
                                "A MEASURE PAIR (marble m2 / lm, windows nr / m2, sliding door nr / m2) is ONE item "
                                "measured two ways: price ONE basis.",
                                "STATUS: COMPUTED_SHADOW_COMPLETE = complete shadow quantity, NOT approved; "
                                "AUTHORISED_SUBTOTAL = an open owner question can still change it; BLOCKED = no "
                                "quantity; RELEASED = only with a release record (none exists).",
                                "Attribute basis: SOURCE (drawn geometry) / OWNER_FACT / OWNER_PROJECT_PARAMETER "
                                "(owner-confirmed project value, e.g. door height 2.20 m) / URBAN_STANDARD / "
                                "NOT_ESTABLISHED (left empty, never guessed).",
                                f"Canonical measurement source: DXF sha256 {DXF}. DWG <-> DXF identity: "
                                "NOT_ESTABLISHED (a provenance / release blocker, not a quantity blocker).",
                                "No prices. Release status: SHADOW / RC1_REFERENCE - not a contractual BOQ. "
                                "Production migration: NO.")]}
    hdr = ["ITEM CODE", "TRADE", "DESCRIPTION AR", "DESCRIPTION EN", "QUANTITY", "UNIT", "STATUS",
           "MEASURE PAIR (price one basis)", "LEGACY IDS (not additive)", "BREAKDOWN LINES", "SOURCE",
           "RULES / AUTHORITY", "BLOCKERS / NOTES", "APPROVED FOR BOQ"]
    rows = []
    for n, i in enumerate(model["items"]):
        rows.append([i["canonical_item_id"], i["trade"], i["description_ar"], i["description_en"], i["qty"], i["unit"],
                     i["status"], i["measure_pair"] or "", "; ".join(f"{a['id']} ({a['relation']})"
                                                                     for a in i["legacy_row_ids"]),
                     len(i["room_breakdown"]), i["source"], "; ".join(str(x) for x in i["rules"]),
                     " | ".join([str(b) for b in i["blockers"]] + list(i["notes"])),
                     "YES" if i["approved_for_boq"] else "NO - SHADOW"])
        add("01_BOQ_SUMMARY", rows, n, 4, i["qty"], f"CANONICAL_BOQ.items.{i['canonical_item_id']}.qty")
    sheets["01_BOQ_SUMMARY"] = {"role": "ADDITIVE_SUMMARY", "header": hdr, "rows": rows, "qty_cols": [4],
                                "status_col": 6, "wrap_cols": [2, 3, 8, 11, 12],
                                "widths": {0: 10, 2: 34, 3: 40, 8: 34, 11: 30, 12: 60}}

    def one(key, ids):
        v = [(c, cells[key].get(c)) for c in ids if cells[key].get(c) is not None]
        return v[0] if v else (None, None)

    mh = ["ROOM / SITE", "SITE ID", "KIND", "ROOM CLASS", "FLOOR AREA M2 (physical)", "FLOOR FINISH", "FLOOR FINISH M2",
          "CEILING M2", "SKIRTING LM", "HIDDEN PROFILE LM", "PLASTER M2", "PAINT M2", "WALL TILE M2", "TILE PREP M2",
          "WATERPROOFING FLOOR M2", "WATERPROOFING UPTURN LM", "DOORS (connections - not additive)",
          "WINDOWS", "NOTES / BLOCKERS"]
    cols = {6: ("FLR-01", "FLR-02", "FLR-03", "MRB-01"), 7: ("CLG-01",), 8: ("SKT-01",), 9: ("HPR-01",),
            10: ("PLS-01", "PLS-02"), 11: ("PNT-01",), 12: ("WTL-01",), 13: ("WTP-01",), 14: ("WPF-01",),
            15: ("WPU-01",)}
    mrows = []
    for n, rm in enumerate(rooms):
        k = rm["key"]
        doors = sorted(o["opening_id"] for o in recs if o["kind"] in ("DOOR", "SLIDING_GLAZED_DOOR") and
                       o["state"] == OR.IN_SCOPE and k in (o["from_site"], o["to_site"]))
        if rm["kind"] == RM.STRIP:
            doors = [rm["door"]]
        wins = sorted(o["opening_id"] for o in recs if o["kind"] == "WINDOW" and o["from_site"] == k)
        row = [rm["display"], rm["site_id"], rm["kind"], rm["semantic_class"], rm["floor_area_m2"]]
        add("02_ROOM_MATRIX", mrows, n, 4, rm["floor_area_m2"], f"ROOM_REGISTER.{k}.floor_area_m2")
        fin_item, fin = one(k, cols[6])
        row += [{"FLR-01": "PORCELAIN (dry)", "FLR-02": "CERAMIC (wet)", "FLR-03": "CERAMIC (PAINTRY)",
                 "MRB-01": "MARBLE THRESHOLD"}.get(fin_item, ""), fin]
        if fin is not None:
            add("02_ROOM_MATRIX", mrows, n, 6, fin, f"CANONICAL_BOQ.items.{fin_item}.room_breakdown.{k}")
        for c in range(7, 16):
            ci, v = one(k, cols[c])
            row.append(v)
            if v is not None:
                add("02_ROOM_MATRIX", mrows, n, c, v, f"CANONICAL_BOQ.items.{ci}.room_breakdown.{k}")
        notes = []
        if fin_item and it[fin_item]["status"] != BC.COMPLETE:
            notes.append(f"{fin_item} {it[fin_item]['status']}: OBJECT_FOOTPRINT_IMPLICIT (open owner question)")
        if rm.get("duct_hole_m2"):
            notes.append(f"duct footprint {rm['duct_hole_m2']} m2 excluded from floor and ceiling")
        if rm["kind"] == RM.ROOM and len(rm["semantic_zones"]) > 1:
            notes.append(f"one physical site, zones {rm['semantic_zones']} (no physical boundary between them)")
        row += [" ".join(doors), " ".join(wins), "; ".join(notes)]
        mrows.append(row)
    sheets["02_ROOM_MATRIX"] = {"role": "BREAKDOWN", "header": mh, "rows": mrows, "qty_cols": list(range(4, 16)),
                                "wrap_cols": [0, 16, 17, 18], "widths": {0: 34, 1: 24, 18: 50}}
    fc = []
    for n, rm in enumerate(rooms):
        k = rm["key"]
        fi, fv = one(k, cols[6])
        cv = cells[k].get("CLG-01")
        eff = next((e for e in ctx["rc1"]["breakdowns"]["Q-14"]["entries"] if e["key"] == k), None)
        note = "; ".join(f"{x['strip']} {x['state']} {x['effect_m2']} m2" for x in (eff or {}).get("inside_effects", []))
        if rm["kind"] == RM.STRIP:
            note = "door strip: its top is the door head reveal, never room ceiling"
        fc.append([rm["display"], rm["site_id"], rm["kind"], rm["floor_area_m2"], fi or "", it[fi]["description_en"]
                   if fi else "", fv, it[fi]["status"] if fi else "NOT_APPLICABLE", cv,
                   "COMPUTED_SHADOW_COMPLETE" if cv is not None else "NOT_APPLICABLE", note])
        add("03_FLOOR_CEILING", fc, n, 3, rm["floor_area_m2"], f"ROOM_REGISTER.{k}.floor_area_m2")
        if fv is not None:
            add("03_FLOOR_CEILING", fc, n, 6, fv, f"FLOOR_REGISTER.{fi}.{k}")
        if cv is not None:
            add("03_FLOOR_CEILING", fc, n, 8, cv, f"CEILING_REGISTER.{k}")
    sheets["03_FLOOR_CEILING"] = {"role": "BREAKDOWN", "header": [
        "ROOM / SITE", "SITE ID", "KIND", "FLOOR AREA M2", "FLOOR ITEM", "FLOOR FINISH", "FLOOR FINISH M2",
        "FLOOR STATUS", "CEILING M2", "CEILING STATUS", "NOTE"], "rows": fc, "qty_cols": [3, 6, 8], "status_col": 7,
        "wrap_cols": [0, 5, 10], "widths": {0: 34, 5: 40, 10: 50}}
    wf = []
    for cid in ("PLS-01", "PLS-02", "PNT-01", "WTL-01", "WTP-01"):
        i = it[cid]
        for b in i["room_breakdown"]:
            c = b["components"]
            n = len(wf)
            wf.append([names[b["key"]], b["key"], cid, i["trade"], b["height_m"], c["wall_plane_m2"],
                       c["column_face_m2"], c["obstacle_face_m2"], c["jamb_reveals_m2"], c["head_reveals_m2"],
                       b["qty"], i["status"], b["height_authority"] or ""])
            for col, f in ((5, "wall_plane_m2"), (6, "column_face_m2"), (7, "obstacle_face_m2"),
                           (8, "jamb_reveals_m2"), (9, "head_reveals_m2")):
                add("04_WALL_FINISHES", wf, n, col, c[f], f"{cid}.{b['key']}.{f}")
            add("04_WALL_FINISHES", wf, n, 10, b["qty"], f"CANONICAL_BOQ.items.{cid}.room_breakdown.{b['key']}")
    sheets["04_WALL_FINISHES"] = {"role": "BREAKDOWN", "header": [
        "ROOM", "SITE ID", "ITEM", "TRADE", "HEIGHT M", "WALL PLANE M2", "EXPOSED COLUMN FACES M2",
        "DUCT / OBSTACLE FACES M2", "JAMB REVEALS M2", "HEAD REVEALS M2", "ROOM TOTAL M2", "STATUS", "HEIGHT AUTHORITY"],
        "rows": wf, "qty_cols": list(range(4, 11)), "status_col": 11, "wrap_cols": [12], "widths": {0: 30, 12: 50}}
    sk = []
    for b in it["SKT-01"]["room_breakdown"]:
        h = next(x for x in it["HPR-01"]["room_breakdown"] if x["key"] == b["key"])
        n = len(sk)
        sk.append([names[b["key"]], b["key"], b["state"], b["qty"], h["qty"], it["SKT-01"]["status"]])
        add("05_SKIRTING_PROFILE", sk, n, 3, b["qty"], f"SKT-01.{b['key']}")
        add("05_SKIRTING_PROFILE", sk, n, 4, h["qty"], f"HPR-01.{b['key']}")
    sheets["05_SKIRTING_PROFILE"] = {"role": "BREAKDOWN", "header": [
        "ROOM", "SITE ID", "PATH STATE", "SKIRTING LM", "HIDDEN PROFILE LM (same path, separate material)", "STATUS"],
        "rows": sk, "qty_cols": [3, 4], "status_col": 5, "widths": {0: 30, 2: 46, 4: 30}}
    ohdr = ["OPENING ID", "TYPE", "ROLE", "FROM", "TO", "CLEAR WIDTH M", "WIDTH BASIS", "HEIGHT M", "HEIGHT BASIS",
            "AREA M2", "AREA BASIS", "SILL M", "SILL BASIS", "LEAF / CLASS", "MATERIAL", "MATERIAL BASIS",
            "THRESHOLD", "SOURCE ENTITIES", "AUTHORITY / NOTES", "STATUS"]

    def orow(o, sheet, n, rows_):
        row = [o["opening_id"], o["kind"], o.get("role") or "", o["from_display"], o["to_display"], o["clear_width_m"],
               o["width_basis"], o["height_m"], o["height_basis"], o["area_m2"], o["area_basis"], o["sill_m"],
               o["sill_basis"], o.get("leaf_type") or o.get("head_condition") or o.get("floor_contact") or "",
               o["material"] or "", o["material_basis"], o.get("marble_threshold") or "",
               " ".join(o["sources"]), " | ".join(x for x in (o.get("height_authority"), o.get("material_authority"),
                                                             o.get("material_note"), o.get("height_note"),
                                                             o.get("role_authority"), o.get("note"),
                                                             o.get("soffit")) if x),
               o["state"]]
        for col, f in ((5, "clear_width_m"), (7, "height_m"), (9, "area_m2"), (11, "sill_m")):
            if o[f] is not None:
                add(sheet, rows_, n, col, o[f], f"OPENING_REGISTER.{o['opening_id']}.{f}")
        return row

    for sheet, kinds in (("06_DOORS", ("DOOR",)), ("07_WINDOWS_GLAZING", ("WINDOW", "SLIDING_GLAZED_DOOR"))):
        rows_ = []
        for o in recs:
            if o["kind"] in kinds:
                rows_.append(orow(o, sheet, len(rows_), rows_))
        sheets[sheet] = {"role": "SCHEDULE", "header": ohdr, "rows": rows_, "qty_cols": [5, 7, 9, 11],
                         "status_col": 19, "wrap_cols": [3, 4, 17, 18], "widths": {3: 26, 4: 26, 17: 40, 18: 70}}
    rv = []
    for o in recs:
        if o["kind"] == OR.PASSAGE:
            rv.append(orow(o, "08_OPENINGS_REVEALS", len(rv), rv))
    rv.append(["REVEAL RECORDS (included inside the plaster / paint items above - NOT additive)"] + [""] * 19)
    for x in ctx["r8_19"]["reveals"]:
        n = len(rv)
        rv.append([x["opening"], x["kind"], x["surface"], names.get(x["owner_site"] or "", x["owner_site"] or ""),
                   x["finish"], x.get("depth_m"), "SOURCE", x.get("height_m"), "", x.get("area_m2"), "",
                   "", "", (x.get("physicality") or {}).get("state", ""), "", "", "", "",
                   x.get("authority") or "", "COMPUTED_SHADOW_COMPLETE" if x["state"] == "COMPUTED" else
                   "OUT_OF_MEASURED_SCOPE"])
        if x.get("area_m2") is not None:
            add("08_OPENINGS_REVEALS", rv, n, 9, x["area_m2"], f"REVEAL_REGISTER.{x['opening']}.{x['surface']}")
    sheets["08_OPENINGS_REVEALS"] = {"role": "SCHEDULE", "header": ohdr, "rows": rv, "qty_cols": [5, 7, 9],
                                     "wrap_cols": [3, 18], "widths": {0: 36, 3: 26, 18: 70}}
    wp = []
    rooms_wp = ctx["r8_19"]["waterproofing"]["rooms"]
    for b in it["WPF-01"]["room_breakdown"]:
        u = next(x for x in it["WPU-01"]["room_breakdown"] if x["key"] == b["key"])
        rr = rooms_wp[b["key"]]
        n = len(wp)
        wp.append([names[b["key"]], b["key"], rr["class_"], b["qty"], u["qty"], rr["upturn_height_m"],
                   json.dumps(rr["perimeter_by_class_m"], sort_keys=True), "NO" if not rr["doorways_deducted"] else "YES",
                   rr["authority"], it["WPF-01"]["status"]])
        add("09_WATERPROOFING", wp, n, 3, b["qty"], f"WPF-01.{b['key']}")
        add("09_WATERPROOFING", wp, n, 4, u["qty"], f"WPU-01.{b['key']}")
    sheets["09_WATERPROOFING"] = {"role": "BREAKDOWN", "header": [
        "ROOM", "SITE ID", "CLASS", "FLOOR MEMBRANE M2", "UPTURN LM", "UPTURN HEIGHT M", "PERIMETER BY CLASS M",
        "DOORWAYS DEDUCTED", "AUTHORITY", "STATUS"], "rows": wp, "qty_cols": [3, 4, 5], "status_col": 9,
        "wrap_cols": [6, 8], "widths": {0: 30, 6: 50, 8: 40}}
    mb = []
    for m in sorted(ctx["marble"], key=lambda m: m["threshold"]):
        door = next(t["door_occurrence"] for t in ctx["thresholds_new"] if t["threshold"] == m["threshold"])
        n = len(mb)
        mb.append([m["threshold"], door, m["clear_width_mm"] / 1000, m["depth_mm"] / 1000, m["plan_area_m2"],
                   m["length_lm"], str(m["vertical_rise_mm"]), m["authority_kind"], m["authority"],
                   it["MRB-01"]["status"]])
        add("10_MARBLE_THRESHOLDS", mb, n, 4, m["plan_area_m2"], f"MRB-01.{m['threshold']}")
        add("10_MARBLE_THRESHOLDS", mb, n, 5, m["length_lm"], f"MRB-02.{m['threshold']}")
    sheets["10_MARBLE_THRESHOLDS"] = {"role": "BREAKDOWN", "header": [
        "THRESHOLD", "DOOR", "CLEAR WIDTH M", "DEPTH M", "PLAN AREA M2 (MRB-01)", "LENGTH LM (MRB-02)",
        "VERTICAL RISE MM (rise only)", "AUTHORITY KIND", "AUTHORITY", "STATUS"], "rows": mb, "qty_cols": [2, 3, 4, 5],
        "status_col": 9, "widths": {0: 30, 8: 46}}
    tr = []
    for i in model["items"]:
        tr.append([i["canonical_item_id"], i["evidence"], i["source"], "; ".join(str(x) for x in i["rules"]),
                   json.dumps([{k: a.get(k) for k in ("id", "relation", "value", "keys", "note")}
                               for a in i["legacy_row_ids"]], ensure_ascii=False),
                   json.dumps([b["key"] for b in i["room_breakdown"]]), model["run"]["run_id"],
                   model["run"]["source_revision"], dg(i)])
    sheets["11_TRACEABILITY"] = {"role": "INFO", "header": [
        "ITEM CODE", "ENGINE REGISTER ROW", "SOURCE", "RULES", "LEGACY IDS (relation, value)", "BREAKDOWN KEYS",
        "RUN ID", "SOURCE REVISION", "ITEM DIGEST"], "rows": tr, "wrap_cols": [3, 4, 5],
        "widths": {1: 40, 3: 40, 4: 70, 5: 50, 8: 30}}
    bl = []
    for i in model["items"]:
        for b in list(i["blockers"]) + list(i["notes"]):
            bl.append([i["canonical_item_id"], i["status"], str(b)])
    for k, v in sorted(ctx["rc1"]["footprint"].items()):
        if v["state"] != FA.RESOLVED:
            bl.append([k, "OPEN", "OBJECT_FOOTPRINT_IMPLICIT: " + ", ".join(o["key"] for o in v["objects"]) +
                       f" (faces {v['outline_faces']['faces_m2']} m2)"])
    sheets["12_BLOCKERS"] = {"role": "INFO", "header": ["ITEM / SITE", "STATUS", "BLOCKER / NOTE"], "rows": bl,
                             "status_col": 1, "wrap_cols": [2], "widths": {2: 110}}
    qa = ctx["rc1"]
    run = [["run_id", model["run"]["run_id"]], ["source_revision", model["run"]["source_revision"]],
           ["canonical_dxf_sha256", DXF], ["dwg_dxf_identity", "NOT_ESTABLISHED"], ["scope", model["run"]["floor"]],
           ["canonical_boq_digest", model["digest"]], ["canonical_model_validation", qa["model_validation"]["state"]],
           ["room_matrix_reconciliation", qa["matrix"]["state"]], ["floor_partition", qa["floor_partition"]["state"]],
           ["physical_surface_identity", qa["surface_identity"]["state"]],
           ["opening_register_validation", qa["opening_validation"]["state"]],
           ["quantity_regression_vs_r8_20", "UNCHANGED" if qa["regression"]["all_unchanged"] else "CHANGED"],
           ["pricing", "NONE"], ["workbook_calculates", "NO"], ["release_status", "SHADOW / RC1_REFERENCE"],
           ["production_migration", "NO"]]
    sheets["13_RUN_QA"] = {"role": "INFO", "header": ["KEY", "VALUE"], "rows": run, "widths": {0: 34, 1: 90}}
    legacy = sorted({a["id"] for i in model["items"] for a in i["legacy_row_ids"]})
    return sheets, src, legacy


def xlsx(ctx):
    sheets, src, legacy = workbook(ctx)
    ids = [i["canonical_item_id"] for i in ctx["rc1"]["model"]["items"]]
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / XLSX_NAME
        w = BX.write(sheets, p, created=CREATED)
        v = BX.validate(p, sheets, sources=src, approved_col=13, canonical_ids=ids, legacy_ids=legacy, tol=0.0)
        w2 = BX.write(sheets, Path(d) / ("2_" + XLSX_NAME), created=CREATED)
    return sheets, src, legacy, w, v, w2


# ------------------------------------------------------------------------------------------- registers
def registers(ctx):
    r = ctx["rc1"]
    model, rooms, recs, names = r["model"], r["rooms"], r["openings"], r["names"]
    it = items_by(model)
    rec = jl(ROOT / "research/external_engine_lab/rc1_recommendation.json")
    sheets, src, legacy, w, xv, w2 = xlsx(ctx)
    regs = {}
    open_items = sorted(i["canonical_item_id"] for i in model["items"] if i["status"] != BC.COMPLETE)
    rc1_ready = (r["model_validation"]["state"] == r["matrix"]["state"] == r["floor_partition"]["state"] ==
                 r["surface_identity"]["state"] == r["opening_validation"]["state"] == xv["state"] == "PASS" and
                 r["regression"]["all_unchanged"])
    gates = dict(GATES, QORTUBA_RC1_REFERENCE_READY="YES" if rc1_ready else "NO")
    regs["ROOM_REGISTER"] = {"SCHEMA": "URBAN_QORTUBA_RC1_ROOM_REGISTER_V1", "policy": RM.policy_record(),
                             "rooms": [x for x in rooms if x["kind"] == RM.ROOM],
                             "door_strips": [x for x in rooms if x["kind"] == RM.STRIP],
                             "counts": {"rooms": sum(x["kind"] == RM.ROOM for x in rooms),
                                        "door_strips": sum(x["kind"] == RM.STRIP for x in rooms)},
                             "physical_floor_m2": r["floor_partition"]["physical_floor_m2"],
                             "label_is_not_authority": "sites are certified topology faces; labels only name them; "
                                                       "equal labels get ordinals (never merged)",
                             "hall_lobby": "ONE certified site with zones HALL + whgm; the Hall / Lobby open passage "
                                           "lies inside it"}
    regs["ROOM_QUANTITY_MATRIX"] = {"SCHEMA": "URBAN_QORTUBA_RC1_ROOM_QUANTITY_MATRIX_V1", **r["matrix"]}
    for name, rid, cid in (("FLOOR_REGISTER", None, None), ("CEILING_REGISTER", "Q-14", "CLG-01")):
        pass
    regs["FLOOR_REGISTER"] = {"SCHEMA": "URBAN_QORTUBA_RC1_FLOOR_REGISTER_V1",
                              "items": {c: {k: it[c][k] for k in ("qty", "unit", "status", "room_breakdown",
                                                                  "blockers", "notes")}
                                        for c in ("FLR-01", "FLR-02", "FLR-03", "MRB-01")},
                              "row_breakdowns": {rid: r["breakdowns"][rid] for rid in ("Q-13", "Q-11", "Q-12")},
                              "partition": r["floor_partition"],
                              "dry_rule": "QORTUBA-NEW-FLOOR-OBJECT-FOOTPRINT-OWNER-001@v1: porcelain wall to wall, "
                                          "wardrobes / joinery / loose furniture NOT deducted (dry rooms only)",
                              "wet_rule": "US-01 / QP-07 / QORTUBA-NEW-WET-SERVICE-FINISH-OWNER-001@v1: bathrooms + "
                                          "PAINTRY ceramic; marble thresholds are their own regions"}
    regs["CEILING_REGISTER"] = {"SCHEMA": "URBAN_QORTUBA_RC1_CEILING_REGISTER_V1",
                                "item": {k: it["CLG-01"][k] for k in ("qty", "unit", "status", "room_breakdown")},
                                "row_breakdown": r["breakdowns"]["Q-14"],
                                "handled": {"BED.ROOM duct": "0.84 m2 footprint outside the site (built obstacle)",
                                            "Hall / Lobby passage soffit": "excluded from the ceiling, counted once "
                                                                           "as the passage TOP_REVEAL",
                                            "M.B.ROOM / DRESS passage": "full height: the ceiling continues",
                                            "door strips": "their top is the door head reveal, never ceiling"},
                                "regression_target_not_calibration": it["CLG-01"]["qty"]}
    for name, cid in (("SKIRTING_REGISTER", "SKT-01"), ("HIDDEN_PROFILE_REGISTER", "HPR-01"),
                      ("PLASTER_REGISTER", ("PLS-01", "PLS-02")), ("PAINT_REGISTER", "PNT-01"),
                      ("WALL_TILE_REGISTER", "WTL-01"), ("WALL_TILE_PREP_REGISTER", "WTP-01"),
                      ("WATERPROOFING_REGISTER", ("WPF-01", "WPU-01"))):
        ids = cid if isinstance(cid, tuple) else (cid,)
        regs[name] = {"SCHEMA": f"URBAN_QORTUBA_RC1_{name}_V1",
                      "items": {c: {k: it[c][k] for k in ("qty", "unit", "status", "room_breakdown", "rules",
                                                          "blockers", "notes", "evidence")} for c in ids}}
    regs["SKIRTING_REGISTER"]["path"] = {"policy": ctx["skirting_v4"]["policy"]["policy_id"]
                                         if isinstance(ctx["skirting_v4"]["policy"], dict) else
                                         ctx["skirting_v4"]["policy"],
                                         "components_lm": ctx["skirting_v4"]["components_lm"],
                                         "excluded_lm": ctx["skirting_v4"]["excluded_lm"]}
    regs["MARBLE_THRESHOLD_REGISTER"] = {"SCHEMA": "URBAN_QORTUBA_RC1_MARBLE_THRESHOLD_REGISTER_V1",
                                         "thresholds": ctx["marble"], "quantities": ctx["marble_quantities"],
                                         "measure_pair": ["MRB-01", "MRB-02"],
                                         "rule": "plan area and length are two measures of the same 4 thresholds - "
                                                 "price one basis; 2 cm = vertical rise only"}
    sch = OR.schedules(recs)
    regs["OPENING_REGISTER"] = {"SCHEMA": "URBAN_QORTUBA_RC1_OPENING_REGISTER_V1", "policy": OR.policy_record(),
                                "records": recs, "validation": r["opening_validation"], "schedules": sch}
    pk = lambda ids: [o for o in recs if o["opening_id"] in ids]       # noqa: E731
    regs["DOOR_REGISTER"] = {"SCHEMA": "URBAN_QORTUBA_RC1_DOOR_REGISTER_V1",
                             "internal_doors": pk(sch["internal_doors"]), "internal_door_count": sch["internal_door_count"],
                             "entrance": pk(sch["entrance_doors"]), "out_of_scope": pk(sch["out_of_scope"]),
                             "width_fallback_used": False,
                             "height_basis": "QP-21 OWNER_CONFIRMED_PROJECT_PARAMETER 2.20 m (no door height is drawn)"}
    regs["WINDOW_REGISTER"] = {"SCHEMA": "URBAN_QORTUBA_RC1_WINDOW_REGISTER_V1", "windows": pk(sch["windows"]),
                               "count": sch["window_count"], "area_m2": it["WIN-02"]["qty"],
                               "sill": "1.00 m above floor (QORTUBA-NEW-NORMAL-WINDOWS-ABOVE-FLOOR-OWNER-001@v2); the "
                                       "wall below is physical and skirting continues below every normal window",
                               "height": "QP-22 owner project parameter 1.50 m"}
    regs["GLAZING_REGISTER"] = {"SCHEMA": "URBAN_QORTUBA_RC1_GLAZING_REGISTER_V1",
                                "sliding_glazed_doors": pk(sch["sliding_glazed_doors"]),
                                "aluminium_windows": [o["opening_id"] for o in pk(sch["windows"])
                                                      if o["material"] == "ALUMINIUM"],
                                "material_not_established": [o["opening_id"] for o in recs
                                                             if o["kind"] in ("WINDOW", "SLIDING_GLAZED_DOOR") and
                                                             o["state"] == OR.IN_SCOPE and not o["material"]],
                                "rule": "glazed is not aluminium: US-13 is applied only to windows whose far side is "
                                        "outside the drawn building (geometry probe)"}
    regs["REVEAL_REGISTER"] = {"SCHEMA": "URBAN_QORTUBA_RC1_REVEAL_REGISTER_V1", "reveals": ctx["r8_19"]["reveals"],
                               "counts": {s: sum(1 for x in ctx["r8_19"]["reveals"] if x["state"] == s)
                                          for s in sorted({x["state"] for x in ctx["r8_19"]["reveals"]})},
                               "unresolved": [x for x in ctx["r8_19"]["reveals"]
                                              if x["state"] not in ("COMPUTED", "OUT_OF_MEASURED_SCOPE")],
                               "sliding_door_physicality": ctx["r8_19"]["sliding_door_physicality"],
                               "rules": "physical reveal before reveal finish; default PLASTER; paint only where dry "
                                        "painted ownership applies; H480 fixture rejected as reveal evidence"}
    regs["CANONICAL_BOQ"] = {"SCHEMA": "URBAN_QORTUBA_RC1_CANONICAL_BOQ_V1", "policy": BC.policy_record(), **model,
                             "validation": r["model_validation"]}
    regs["BOQ_ALIAS_REGISTER"] = {
        "SCHEMA": "URBAN_QORTUBA_RC1_BOQ_ALIAS_REGISTER_V1",
        "aliases": [{"alias": a["id"], "canonical": i["canonical_item_id"], **{k: a.get(k) for k in
                                                                                ("relation", "value", "keys", "note")}}
                    for i in model["items"] for a in i["legacy_row_ids"]],
        "q03_q11": rec["4_q03_q11"], "q03p_q12": rec["5_q03p_q12"],
        "r8_20_xlsx_duplicate_risk": rec["6_xlsx_duplicate_risk"],
        "r8_20_floor_lines_sum_m2": round(sum(jl(REG20 / "QUANTITY_REGRESSION.json")["rows"][k]["R8.20"]
                                              for k in ("Q-03", "Q-03P", "Q-11", "Q-12", "Q-13")), 6),
        "physical_floor_finish_m2": r["floor_partition"]["finish_items_sum_m2"],
        "summary_lines_now": [i["canonical_item_id"] for i in model["items"]], "aliases_in_summary": []}
    fp = r["footprint"]
    regs["OBJECT_FOOTPRINT_REGISTER"] = {
        "SCHEMA": "URBAN_QORTUBA_RC1_OBJECT_FOOTPRINT_REGISTER_V1", "policy": FA.policy_record(), "sites": fp,
        "resolved": sorted(k for k, v in fp.items() if v["state"] == FA.RESOLVED),
        "unresolved": sorted(k for k, v in fp.items() if v["state"] != FA.RESOLVED),
        "facts_searched": rec["9_existing_fact"], "why_not_paintry": rec["10_why_not_paintry"],
        "owner_question": rec["10b_exact_question"], "assumed": "NOTHING (no zero, no full-room assumption)",
        "effect_bounds_m2": {"if_included": it["FLR-03"]["qty"],
                             "if_excluded_candidates": {f"minus face {a}": round(it["FLR-03"]["qty"] - a, 6)
                                                        for a in sorted(next(iter(
                                                            v["outline_faces"]["faces_m2"] for v in fp.values()
                                                            if v["state"] != FA.RESOLVED)))[:-1]},
                             "largest_face": "the largest face is the open floor in front of the counter "
                                             "(it holds the sliding-door side) - not a counter candidate"},
        "waterproofing": "not affected (US-14: membrane over the whole measured room floor)"}
    regs["BOQ_XLSX_STATUS"] = {"SCHEMA": "URBAN_QORTUBA_RC1_BOQ_XLSX_STATUS_V1", "policy": BX.policy_record(),
                               "file": XLSX_NAME, "sheets": list(sheets), "roles": {k: v["role"] for k, v in sheets.items()},
                               "content_digest": w["content_digest"], "file_sha256": w["file_sha256"],
                               "second_write_identical_bytes": w["file_sha256"] == w2["file_sha256"],
                               "readback_validation": xv, "formulas": xv["formulas"],
                               "quantity_cells_checked": xv["quantity_cells_checked"],
                               "rows_per_sheet": xv["rows_per_sheet"], "summary_lines": len(model["items"]),
                               "legacy_ids_not_in_summary": legacy, "replaces": "URBAN_QTO_R8_20_SHADOW_BOQ.xlsx"}
    regs["SOURCE_ANCHOR_STATUS"] = {"SCHEMA": "URBAN_QORTUBA_RC1_SOURCE_ANCHOR_STATUS_V1",
                                    "QORTUBA_RC1_CANONICAL_MEASUREMENT_SOURCE": {"dxf_sha256": DXF,
                                                                                 "revision": "QORTUBA_REV_NEW"},
                                    "dwg_known_sha256_prefix": DWG, "dwg_dxf_identity": "NOT_ESTABLISHED",
                                    "blocks_rc1_reference_freeze": False, "blocks_release_authority": True,
                                    "protocol_ready": jl(REG20 / "SOURCE_ANCHOR_PLAN.json").get("protocol") or
                                    "SOURCE_ANCHOR_PLAN (R8.20)",
                                    "next": "controlled owner re-export (DXF 2018 + DWG AC1027 + hashes + AutoCAD "
                                            "build), in parallel or after RC1"}
    regs["DONOR_REUSE_REGISTER"] = {
        "SCHEMA": "URBAN_QORTUBA_RC1_DONOR_REUSE_REGISTER_V1", "lock": "research/external_engine_lab/DONORS.lock",
        "searched_before_writing": ["UC4N labels.plain / snapshot / diff", "BM readback diff / digests",
                                    "SL COM readback", "PW server", "OT schedule scan / scale gating / detectRooms"],
        "COPY_ADAPT": [], "CLEAN_REIMPLEMENTED": rec["18_clean_reimplement"], "BENCHMARK_ONLY": [
            "OpenTakeoff detectRooms / One-Click", "puran-water/autocad-mcp server"],
        "REJECTED": rec["19_reject"], "DEFERRED": {"UC4N labels.plain": rec["17_copy_adapt_now"],
                                                   "BM / SL native readback oracle": "route B lab oracle only",
                                                   "OT PDF lane": "after the first blind-villa intake"},
        "duplicating_full_engines": False}
    regs["LEGACY_PATH_REGISTER"] = {
        "SCHEMA": "URBAN_QORTUBA_RC1_LEGACY_PATH_REGISTER_V1",
        "rc1_quantities_from_legacy": rec["14_legacy_supplied_quantities"],
        "paths": [{"legacy": "research/qs_wall_treatment_01/pa08/qortuba/boq/owner_rules.py takeoff rows Q-01..Q-17 "
                             "(OWNER RULES V1, old revision)", "replacement": "the R8 evidence -> topology -> trade "
                                                                              "chain (rc1_qortuba)",
                   "reconciles": "not comparable (old revision, different source)", "status": "SUPERSEDED - kept as "
                   "rule store (US / QP identities) and provenance; its takeoff is never read for a quantity",
                   "retirement": "freeze as historical; no new consumer"},
                  {"legacy": "engine/source/wall_faces.py (WALL_FACE_SURFACE_POLICY_V1)", "replacement":
                   "engine/source/wall_faces_v2.py (V2, governing since R8.18)", "reconciles": "V2 supersedes by "
                   "policy; V1 kept only for the frozen R8.17 regressions", "status": "SUPERSEDED",
                   "retirement": "remove with the R8.17 regression set at migration"},
                  {"legacy": "engine/*.py (pre-R8 production modules), engine/qs_core, engine/ingest",
                   "replacement": "engine/source + the RC1 chain", "reconciles": "not used by RC1",
                   "status": "LEGACY (production app path)", "retirement": "migration programme (not this round)"},
                  {"legacy": "engine/boq_xlsx.py (BOQ_XLSX_EXPORT_V1, R8.20 shadow workbook)",
                   "replacement": "engine/boq_rc1_xlsx.py (V2)", "reconciles": "same report values; V1 exposed the "
                   "alias duplicates", "status": "SUPERSEDED for owner review", "retirement": "keep for R8.20 regression"}],
        "one_authoritative_path": "SOURCE (K2 DXF) -> claims / facts -> topology -> trade regions -> rules -> rows "
                                  "(engine/source policies, lab orchestration) -> canonical BOQ -> RC1 XLSX view"}
    inv = [("SOURCE ENGINE", "ACTIVE", "engine/source/canonical_input.py, canonical_build.py"),
           ("CAD K1/K2", "ACTIVE (K2 measures REV_NEW; K1 cross-route pending the AC1027 export)", "engine/source/cad/"),
           ("UNIT / FRAME", "ACTIVE", "engine/source/frame.py, cad/unit_evidence.py"),
           ("EVIDENCE ENGINE", "ACTIVE", "engine/source/observations.py, findings.py, role_authority.py"),
           ("CLAIM / FACT POLICY", "ACTIVE", "engine/source/owner_claims.py, owner_facts.py, owner_method_facts.py"),
           ("ROOM / SEMANTIC ENGINE", "ACTIVE", "engine/source/semantic_zones.py, room_topology.py, text_role.py"),
           ("GEOMETRY ENGINE", "ACTIVE", "engine/source/geometry_role.py, region_membership.py"),
           ("WALL BAND ENGINE", "ACTIVE (WALL_BAND_POLICY_V5)", "engine/source/wall_bands.py"),
           ("TOPOLOGY CLOSURE", "ACTIVE", "engine/source/topology.py, topology_closures.py"),
           ("OPENING ENGINE", "ACTIVE (+ OPENING_REGISTER_V1 new)", "engine/source/opening_facts.py, door_transition.py, "
                                                                    "opening_register.py"),
           ("FLOOR QTO", "SHADOW", "engine/source/trade_regions.py, trade_strips.py (+ lab rows)"),
           ("CEILING QTO", "SHADOW", "engine/source/trade_regions.py (+ lab rows)"),
           ("SKIRTING", "SHADOW (V4)", "engine/source/wall_contact_path.py"),
           ("PROFILE", "SHADOW (same path, separate item)", "engine/source/wall_contact_path.py"),
           ("WALL SURFACE", "SHADOW (V2 governing; V1 SUPERSEDED)", "engine/source/wall_faces_v2.py | wall_faces.py"),
           ("PLASTER", "SHADOW", "engine/source/wall_faces_v2.py, wall_height.py"),
           ("PAINT", "SHADOW", "engine/source/wall_faces_v2.py"), ("WALL TILE", "SHADOW", "engine/source/wall_faces_v2.py"),
           ("TILE PREP", "SHADOW", "engine/source/wall_faces_v2.py"),
           ("COLUMN / DUCT FINISH", "SHADOW", "engine/source/exposed_finish.py, obstacle_authority.py"),
           ("REVEAL", "SHADOW", "engine/source/reveal_physicality.py, reveal_finish.py, opening_reveals.py"),
           ("WATERPROOFING", "SHADOW", "engine/source/waterproofing.py"),
           ("MARBLE", "SHADOW", "engine/source/marble_thresholds.py"),
           ("BOQ REPORT", "SHADOW (canonical model new; BOQ_REPORT_LAYER_V1 kept)",
            "engine/source/boq_canonical.py, boq_report.py, boq_evidence.py, room_matrix.py, footprint_authority.py"),
           ("XLSX EXPORT", "SHADOW (V2 new; V1 SUPERSEDED)", "engine/boq_rc1_xlsx.py | engine/boq_xlsx.py"),
           ("QA / BLIND", "ACTIVE (lab)", "research/external_engine_lab/*blind*.py, tests/"),
           ("RELEASE", "BLOCKED (no released level; source anchor NOT_ESTABLISHED)",
            "engine/source/closure_release.py, closure_review.py, source_anchor.py"),
           ("LEGACY PRE-R8 ENGINE", "LEGACY", "engine/*.py, engine/qs_core, engine/ingest")]
    files = sorted({f.strip() for _, _, p in inv for f in p.replace("|", ",").split(",")
                    if f.strip().endswith(".py") and (ROOT / f.strip()).exists()})
    regs["ENGINE_INVENTORY"] = {"SCHEMA": "URBAN_QORTUBA_RC1_ENGINE_INVENTORY_V1",
                                "components": [{"component": c, "state": s, "modules": m} for c, s, m in inv],
                                "duplicates": rec["15_duplicate_engines"],
                                "orchestration": "research/external_engine_lab r8_10 -> r8_20 -> rc1 chain (lab; "
                                                 "moves into engine at migration)",
                                "module_sha256": {f: sha(ROOT / f) for f in files}}
    recon = {"canonical_model": r["model_validation"], "room_matrix": {k: r["matrix"][k] for k in
                                                                       ("state", "not_reconciled", "unplaced",
                                                                        "reconciliation")},
             "floor_partition": r["floor_partition"], "physical_surface_identity": r["surface_identity"],
             "openings": r["opening_validation"], "regression_vs_r8_20": r["regression"],
             "trade_breakdowns": {i["canonical_item_id"]: {"qty": i["qty"], "breakdown_sum": round(sum(
                 b["qty"] for b in i["room_breakdown"] if b["qty"] is not None), 6)} for i in model["items"]},
             "per_room_wall_conservation": ctx["r8_19"]["all_sites_reconcile"],
             "door_count_cross_check": {"thresholds": len(ctx["thresholds_new"]), "entrance": len(sch["entrance_doors"]),
                                        "out_of_scope": len(sch["out_of_scope"]), "internal": sch["internal_door_count"],
                                        "consistent": len(ctx["thresholds_new"]) == sch["internal_door_count"] +
                                        len(sch["entrance_doors"]) + len(sch["out_of_scope"])},
             "xlsx": xv["state"], "rc1_blocked": not rc1_ready}
    recon["state"] = "PASS" if rc1_ready and recon["door_count_cross_check"]["consistent"] else "FAIL"
    regs["QA_RECONCILIATION"] = {"SCHEMA": "URBAN_QORTUBA_RC1_QA_RECONCILIATION_V1", **recon}
    facts = {f: sha(ROOT / "data/registry" / f) for f in Q.FACT_FILES}
    surf = dg({sid: v["faces"] for sid, v in ctx["r8_18"]["per_site"].items()})
    regs["QORTUBA_RC1_FREEZE"] = {
        "SCHEMA": "URBAN_QORTUBA_RC1_FREEZE_V1", "name": "URBAN_ARCHITECTURAL_QTO_QORTUBA_RC1",
        "frozen": rc1_ready, "release_status": "SHADOW / RC1_REFERENCE", "contractual_approval": False,
        "canonical_dxf_sha256": DXF, "dwg_known_sha256_prefix": DWG, "dwg_dxf_anchor": "NOT_ESTABLISHED",
        "selected_plan_scope": model["run"]["floor"], "run_id": model["run"]["run_id"],
        "room_register_digest": dg(rooms), "owner_fact_and_rule_files_sha256": facts,
        "engine_policies": {p["policy_id"]: p["digest"] for p in (BC.policy_record(), RM.policy_record(),
                                                                  OR.policy_record(), FA.policy_record(),
                                                                  BX.policy_record())},
        "inherited_freezes": {"R8.19": jl(ROOT / "tests/r8_19/registers/R8_19_FREEZE.json").get("frozen_commit"),
                              "R8.18": jl(ROOT / "tests/r8_18/registers/R8_18_FREEZE.json").get("frozen_commit")},
        "row_digests": {k: v for k, v in ctx["regression_20"]["digests"].items()},
        "topology_digest": ctx["reproduces"].get("topology_digest"), "opening_digest": r["opening_validation"]["digest"],
        "surface_digest": surf, "trade_item_digests": {i["canonical_item_id"]: dg(i) for i in model["items"]},
        "canonical_boq_digest": model["digest"], "xlsx_content_digest": w["content_digest"],
        "xlsx_file_sha256": w["file_sha256"], "open_items": open_items,
        "open_owner_question": rec["10b_exact_question"],
        "test_results": "TEST_RESULTS.json of the package (one full suite from the final commit)",
        "after_freeze": "NO MORE QORTUBA-SPECIFIC TUNING: a generic fix found on an unseen villa is versioned, "
                        "implemented generically and Qortuba is rerun as regression; never tuned to restore a number"}
    regs["BLIND_VILLA_INTAKE_SCHEMA"] = {
        "SCHEMA": "URBAN_BLIND_VILLA_INTAKE_SCHEMA_V1",
        "files": [{"role": "ORIGINAL_DWG", "required": True}, {"role": "CONTROLLED_DXF", "required": "preferred",
                                                               "protocol": "AutoCAD SAVEAS DXF 2018, no edits"},
                  {"role": "CONTROLLED_DWG_AC1027", "required": "preferred", "protocol": "SAVEAS AutoCAD 2013"},
                  {"role": "ARCHITECTURAL_PDF", "required": True}, {"role": "SECTIONS", "required": True},
                  {"role": "ELEVATIONS", "required": True}, {"role": "DOOR_SCHEDULE", "required": "if it exists"},
                  {"role": "WINDOW_SCHEDULE", "required": "if it exists"},
                  {"role": "FINISH_SCHEDULE", "required": "if it exists"}, {"role": "GENERAL_NOTES", "required": True},
                  {"role": "STRUCTURAL_PACKAGE", "required": "later"}],
        "per_file_record": ["file name", "sha256", "role", "revision / date", "who exported it", "AutoCAD build"],
        "owner_statements_needed_before_run": ["drawing unit (or confirm $INSUNITS)", "which plan / floor is in scope",
                                               "project wall finish heights if not drawn (asked only if absent)"],
        "never_before_freeze": ["expected quantities", "a QS BOQ", "any target total"],
        "admission": "intake -> hash -> admission class -> unit / frame / region records -> engine + method FROZEN and "
                     "committed -> blind run -> result committed -> THEN the sealed gold is opened"}
    regs["BLIND_VALIDATION_PLAN"] = {
        "SCHEMA": "URBAN_BLIND_VALIDATION_PLAN_V1",
        "gold_protocol": ["the owner seals the manual QS BOQ (file hash recorded) BEFORE Urban sees any file",
                          "Urban / Claude never opens it until source admitted + engine frozen + blind result "
                          "committed", "then compare; no tuning after gold"],
        "metrics": ["ROOM_DETECTION_COMPLETENESS", "ROOM_CLASSIFICATION", "FLOOR_AREA_ERROR", "CEILING_AREA_ERROR",
                    "SKIRTING_ERROR", "PLASTER_ERROR", "PAINT_ERROR", "WALL_TILE_ERROR", "TILE_PREP_ERROR",
                    "WATERPROOFING_ERROR", "MARBLE_ERROR", "DOOR_DETECTION", "DOOR_SIZE_ACCURACY", "WINDOW_DETECTION",
                    "WINDOW_AREA_ACCURACY", "OPENING_CLASSIFICATION", "SILENT_ERROR_COUNT", "BLOCKED_ITEM_COUNT",
                    "OWNER_QUESTION_COUNT"],
        "reporting": "per metric, per room and per trade - NO single global accuracy percentage",
        "defect_classes": ["SOURCE_DECODER_DEFECT", "UNIT_FRAME_DEFECT", "GEOMETRY_DEFECT", "TOPOLOGY_DEFECT",
                           "ROOM_SEMANTIC_DEFECT", "OPENING_DEFECT", "HEIGHT_EVIDENCE_GAP", "TRADE_RULE_GAP",
                           "PROJECT_FACT_GAP", "DOCUMENT_EVIDENCE_GAP", "REPORTING_DEFECT", "GOLD/MANUAL_QS_QUESTION"],
        "after_result": ["classify every mismatch with exactly one defect class", "fix the GENERIC system (versioned)",
                         "rerun Qortuba RC1 as regression", "never fix the test villa"]}
    regs["BOQ_XLSX_MODEL"] = {"SCHEMA": "URBAN_QORTUBA_RC1_BOQ_XLSX_MODEL_V1", "sheets": sheets, "cell_sources": src,
                              "legacy_ids": legacy, "canonical_ids": [i["canonical_item_id"] for i in model["items"]],
                              "created": CREATED.isoformat(), "approved_col": 13}
    regs["RC1_DECISION_REGISTER"] = decision(ctx, regs, gates, rec)
    return regs


def decision(ctx, regs, gates, rec):
    r = ctx["rc1"]
    it = items_by(r["model"])
    names = r["names"]
    bd = lambda c: {names.get(b["key"], b["label"]): b["qty"] for b in it[c]["room_breakdown"]}  # noqa: E731
    sch = regs["OPENING_REGISTER"]["schedules"]
    ops = {o["opening_id"]: o for o in r["openings"]}
    sched = lambda ids: [{k: ops[i][k] for k in ("opening_id", "from_display", "to_display", "clear_width_m",  # noqa: E731
                                                 "height_m", "height_basis", "area_m2", "material")} for i in ids]
    fr = regs["QORTUBA_RC1_FREEZE"]
    a = {
        "1_rc1_complete": "YES - frozen as URBAN_ARCHITECTURAL_QTO_QORTUBA_RC1 (SHADOW / RC1_REFERENCE) with ONE open "
                          "item: FLR-03 PAINTRY ceramic floor AUTHORISED_SUBTOTAL (counter footprint question)"
                          if fr["frozen"] else "NO",
        "2_blocked": {"quantity": fr["open_items"], "release": ["SOURCE_ANCHOR (DWG <-> DXF NOT_ESTABLISHED)",
                                                                 "CROSS_ROUTE_AGREEMENT", "SHADOW_ONLY"]},
        "3_total_physical_floor_m2": r["floor_partition"]["physical_floor_m2"],
        "4_room_floor_areas": {x["display"]: x["floor_area_m2"] for x in r["rooms"]},
        "5_room_floor_finish": {c: bd(c) for c in ("FLR-01", "FLR-02", "FLR-03", "MRB-01")},
        "6_room_ceilings": bd("CLG-01"), "7_total_ceiling": it["CLG-01"]["qty"],
        "8_room_skirting": bd("SKT-01"), "9_total_skirting": it["SKT-01"]["qty"],
        "10_hidden_profile": {"total": it["HPR-01"]["qty"], "rooms": bd("HPR-01")},
        "11_room_plaster": {"PLS-01": bd("PLS-01"), "PLS-02": bd("PLS-02")},
        "12_total_plaster": {"PLS-01": it["PLS-01"]["qty"], "PLS-02": it["PLS-02"]["qty"]},
        "13_room_paint": bd("PNT-01"), "14_total_paint": it["PNT-01"]["qty"],
        "15_bath_wall_tile": {k: v for k, v in bd("WTL-01").items() if "BATH" in k},
        "16_paintry_wall_tile": bd("WTL-01").get("PAINTRY"), "17_total_wall_tile": it["WTL-01"]["qty"],
        "18_tile_prep": {"total": it["WTP-01"]["qty"], "rooms": bd("WTP-01")},
        "19_waterproofing_floor": bd("WPF-01"), "20_waterproofing_upturn": bd("WPU-01"),
        "21_marble": {"area_m2": it["MRB-01"]["qty"], "length_lm": it["MRB-02"]["qty"], "thresholds": bd("MRB-01"),
                      "pair": "price one basis"},
        "22_internal_door_count": sch["internal_door_count"], "23_internal_doors": sched(sch["internal_doors"]),
        "24_entrance": sched(sch["entrance_doors"]), "25_sliding_glass_door": sched(sch["sliding_glazed_doors"]),
        "26_window_count": sch["window_count"], "27_windows": sched(sch["windows"]) + [{"total_area_m2":
                                                                                         it["WIN-02"]["qty"]}],
        "28_other_glazing": regs["GLAZING_REGISTER"]["material_not_established"],
        "29_open_passages": [{k: ops[i].get(k) for k in ("opening_id", "from_zone", "to_zone", "clear_width_m",
                                                          "head_condition", "height_m", "soffit", "door_present")}
                             for i in sch["open_passages"]],
        "30_unresolved_reveal": regs["REVEAL_REGISTER"]["unresolved"] or "NONE",
        "31_column_treatment": "YES: dry exposed column faces in PLS-01 / PNT-01 (+ skirting on the V4 path), wet "
                               "exposed column faces in WTL-01 / WTP-01 only (no paint, no skirting); hidden faces zero",
        "32_duct_treatment": "YES: H2060 / H2061 outer faces in BED.ROOM plaster + paint + skirting; inner lining zero; "
                             "0.84 m2 footprint outside floor and ceiling",
        "33_q03_q11": rec["4_q03_q11"], "34_q03p_q12": rec["5_q03p_q12"],
        "35_excel_double_count": "NO in RC1: every legacy id is an attribute of its canonical line (readback refuses "
                                 "an alias line); R8.20 XLSX: YES (see BOQ_ALIAS_REGISTER)",
        "36_footprint_resolved": "NO for PAINTRY (FLR-03); YES for the dry rooms (fact scope covers them)",
        "37_authority": regs["OBJECT_FOOTPRINT_REGISTER"]["resolved"],
        "38_remaining_blocker": rec["10b_exact_question"],
        "39_every_room_reconciles": r["matrix"]["state"] == "PASS" and ctx["r8_19"]["all_sites_reconcile"],
        "40_trade_totals_equal_breakdowns": r["model_validation"]["state"] == "PASS",
        "41_duplicate_physical_surface": "NONE (" + ", ".join(f"{k}: {v}" for k, v in
                                                              r["surface_identity"]["checks"].items()) + ")",
        "42_duplicate_calculation_path": "NONE for RC1 quantities; superseded parallel code listed in "
                                         "LEGACY_PATH_REGISTER",
        "43_legacy_engines": [p["legacy"] for p in regs["LEGACY_PATH_REGISTER"]["paths"]],
        "44_copy_adapted": "NONE (labels.plain deferred: " + rec["17_copy_adapt_now"] + ")",
        "45_clean_reimplemented": rec["18_clean_reimplement"], "46_rejected": rec["19_reject"],
        "47_xlsx_formulas": "NO" if not regs["BOQ_XLSX_STATUS"]["formulas"] else "YES",
        "48_xlsx_equals_engine": regs["BOQ_XLSX_STATUS"]["readback_validation"]["state"] == "PASS",
        "49_xlsx_content_digest": regs["BOQ_XLSX_STATUS"]["content_digest"],
        "50_canonical_source": f"DXF sha256 {DXF} (QORTUBA_REV_NEW)", "51_dwg_dxf_identity": "NOT_ESTABLISHED",
        "52_blocks_rc1_reference": "NO", "53_blocks_release_authority": "YES",
        "55_deterministic_regeneration": "registers regenerated twice from the committed code and compared; the "
                                         "workbook writes byte-identical (fixed zip timestamps)",
        "56_frozen": fr["frozen"], "57_blind_files": [f["role"] for f in regs["BLIND_VILLA_INTAKE_SCHEMA"]["files"]],
        "58_blind_measures": regs["BLIND_VALIDATION_PLAN"]["metrics"],
        "59_after_blind": regs["BLIND_VALIDATION_PLAN"]["after_result"],
        "60_disagreements": rec["21_disagreements_with_chatgpt"]}
    return {"SCHEMA": "URBAN_QORTUBA_RC1_DECISION_REGISTER_V1", "answers": a, "gates": gates,
            "owner_actions": [{"id": "PAINTRY_COUNTER_FOOTPRINT", "question": rec["10b_exact_question"],
                               "changes": "FLR-03 only (and nothing else)"},
                              {"id": "QORTUBA_CONTROLLED_REEXPORT", "when": "in parallel or after RC1 (not blocking)",
                               "protocol": "R8.20 SOURCE_ANCHOR_PLAN"},
                              {"id": "UNSEEN_VILLA_FILES", "what": "files per BLIND_VILLA_INTAKE_SCHEMA; seal the QS "
                                                                   "BOQ (hash) before sending anything"}]}
