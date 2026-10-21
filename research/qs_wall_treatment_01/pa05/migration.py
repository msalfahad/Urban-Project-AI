"""P7757 migration adapter (PA05 §18): frozen PA01-PA04 artifacts read as
history and mapped onto the new schemas.  Every item is classified
MIGRATED_WITHOUT_LOSS / MIGRATED_WITH_INFORMATION_LOSS / NOT_MIGRATABLE /
HISTORICAL_ONLY.  Nothing frozen is edited; nothing here feeds the blind
rebuild.
"""

from __future__ import annotations

import json
import math
from collections import Counter
from pathlib import Path

from engine.ingest import owner_inputs as OI, rules as R, status as ST
from research.qs_wall_treatment_01.pa05 import config_p7757 as CF

CLASSES = ("MIGRATED_WITHOUT_LOSS", "MIGRATED_WITH_INFORMATION_LOSS", "NOT_MIGRATABLE", "HISTORICAL_ONLY")
STOREY_OF_OLD_REGISTER = {"FF_PHYSICAL_FACE_REGISTER.json": {"FF": "FF"}, "GF_ROOF_PHYSICAL_FACE_REGISTER.json": {"GF": "GF", "ROOF": "ROOF", "SECOND_ROOF": "ROOF"}}


def _read(rel):
    p = CF.OUT / rel
    return json.loads(p.read_text("utf-8")) if p.exists() else None


def _item(artifact, old_id, cls, new_id=None, note=None, **extra):
    assert cls in CLASSES
    return dict(ARTIFACT=artifact, OLD_ID=old_id, CLASS=cls, NEW_ID=new_id, NOTE=note, **extra)


def migrate_rooms(run):
    """Old flood regions (run-dependent ids R1.. with a bbox and an area) -> PHYSICAL_SPACE by anchor containment."""
    out = []
    spaces = run.registers["PHYSICAL_SPACE_REGISTER"]["ROWS"]
    for art in ("pa04/FF_PHYSICAL_FACE_REGISTER.json", "pa04/GF_ROOF_PHYSICAL_FACE_REGISTER.json"):
        d = _read(art)
        if not d:
            continue
        rooms = d["ROOMS"] if isinstance(d["ROOMS"], list) else [r for fl in d["ROOMS"].values() for r in (fl if isinstance(fl, list) else fl.get("ROOMS", []))]
        for r in rooms:
            bb = r.get("BBOX_MM")
            if not bb:
                out.append(_item(art, r["ROOM_ID"], "NOT_MIGRATABLE", note="no geometry anchor in the frozen record (region id only)")); continue
            xs, ys = bb["X"], bb["Y"]
            inside = [s for s in spaces if xs[0] <= s["ANCHOR_MM"][0] <= xs[1] and ys[0] <= s["ANCHOR_MM"][1] <= ys[1]]
            if not inside:
                out.append(_item(art, r["ROOM_ID"], "NOT_MIGRATABLE", note="no new physical space anchors inside the old bbox", OLD_NAME=r.get("ROOM_NAME"))); continue
            best = min(inside, key=lambda s: abs(s["AREA_M2"] - (r.get("REGION_AREA_M2") or 0)))
            rel = abs(best["AREA_M2"] - (r.get("REGION_AREA_M2") or 0)) / max(r.get("REGION_AREA_M2") or 1, 1)
            cls = "MIGRATED_WITHOUT_LOSS" if rel <= 0.15 and len(inside) == 1 else "MIGRATED_WITH_INFORMATION_LOSS"
            out.append(_item(art, r["ROOM_ID"], cls, new_id=best["PHYSICAL_SPACE_ID"], OLD_NAME=r.get("ROOM_NAME"), OLD_AREA_M2=r.get("REGION_AREA_M2"), NEW_AREA_M2=best["AREA_M2"],
                             CANDIDATES_IN_BBOX=len(inside), NEW_TOPOLOGY_STATUS=best["TOPOLOGY_STATUS"],
                             note=None if cls == "MIGRATED_WITHOUT_LOSS" else "topology changed: the old region was merged / split by opening-site closures or the layer profile; old ROOM_NAME stays a historical semantic claim",
                             SEMANTIC_CLAIM_STATUS="HISTORICAL_READ (PA04 primary / challenger); re-anchoring needs a printed-label transform or owner confirmation"))
    return out


def migrate_cad_curves(run):
    out = []
    d = _read("CAD_CURVE_REGISTER.json")
    if not d:
        return out
    all_eids = {}
    for v in run.views:
        all_eids.update(run.entity_ids[v["VIEW_ID"]])
    faces = {f["ENTITY_ID"]: f for f in run.registers["ATOMIC_FACE_REGISTER"]["ROWS"]}
    for cs in d["CURVE_SETS"]:
        for a in cs["ARCS"]:
            eid = all_eids.get(a["CAD_ID"])
            if eid is None:
                out.append(_item("CAD_CURVE_REGISTER.json", a["CAD_ID"], "NOT_MIGRATABLE", note="CAD id not present in the normalised views")); continue
            f = faces.get(eid)
            if f and abs(f["GEOMETRY"].get("R_MM", -1) - a["RADIUS_MM"]) < 1.0:
                out.append(_item("CAD_CURVE_REGISTER.json", a["CAD_ID"], "MIGRATED_WITHOUT_LOSS", new_id=eid, RADIUS_MM=a["RADIUS_MM"], ARC_LENGTH_M_OLD=a["ARC_LENGTH_M"], ARC_LENGTH_M_NEW=round(f["DEVELOPED_LENGTH_MM"] / 1000, 4)))
            else:
                out.append(_item("CAD_CURVE_REGISTER.json", a["CAD_ID"], "MIGRATED_WITH_INFORMATION_LOSS", new_id=eid, note="entity exists but is not on a wall layer in the new layer profile (no atomic face)"))
    return out


def migrate_parapet_components(run):
    out = []
    d = _read("PARAPET_ASSEMBLY_REGISTER.json")
    if not d:
        return out
    all_eids = {}
    for v in run.views:
        all_eids.update(run.entity_ids[v["VIEW_ID"]])
    for c in d["COMPONENTS"]:
        if c.get("GEOMETRY_TYPE") == "LEVEL" or c.get("MATERIAL_STATUS") == "NOT_A_MATERIAL":
            out.append(_item("PARAPET_ASSEMBLY_REGISTER.json", c["ASSEMBLY_ID"], "HISTORICAL_ONLY", note="datum / level record, not a geometric feature")); continue
        cid = c.get("CAD_OBJECT_ID")
        cids = [x for x in (cid if isinstance(cid, list) else [cid]) if x]
        found = [all_eids[x] for x in cids if x in all_eids]
        if cids and len(found) == len(cids):
            out.append(_item("PARAPET_ASSEMBLY_REGISTER.json", c["ASSEMBLY_ID"], "MIGRATED_WITHOUT_LOSS", new_id=found if len(found) > 1 else found[0], LENGTH=c.get("LENGTH"), HEIGHT=c.get("HEIGHT"),
                             HEIGHT_STATUS=ST.from_legacy(c.get("MATERIAL_STATUS"))["QUANTITY_STATUS"]))
        elif cids and found:
            out.append(_item("PARAPET_ASSEMBLY_REGISTER.json", c["ASSEMBLY_ID"], "MIGRATED_WITH_INFORMATION_LOSS", new_id=found, note=f"{len(found)} of {len(cids)} CAD ids resolved in the normalised views"))
        elif c.get("START_POINT") and c.get("END_POINT"):
            out.append(_item("PARAPET_ASSEMBLY_REGISTER.json", c["ASSEMBLY_ID"], "MIGRATED_WITH_INFORMATION_LOSS", note="raster-derived endpoints: geometry carried, no CAD entity identity"))
        else:
            out.append(_item("PARAPET_ASSEMBLY_REGISTER.json", c["ASSEMBLY_ID"], "NOT_MIGRATABLE", note="no CAD id and no endpoints"))
    return out


def migrate_owner_parameters():
    out, inputs, rules = [], [], []
    d = _read("P7757_OWNER_PARAMETERS.json")
    if d:
        reg = d["REGISTRY"]
        items = reg.values() if isinstance(reg, dict) else reg
        for p in items:
            pid = p["PARAMETER_ID"]
            if p.get("OWNER_CONFIRMED") and p.get("VALUE") is not None:
                inp = OI.owner_input(OWNER_INPUT_ID=f"P7757:{pid}:v{p.get('VERSION', 1)}", PROJECT_ID="P7757", QUESTION_ID=pid, PARAMETER_OR_RULE=pid, VALUE=p["VALUE"], UNIT=p.get("UNIT"),
                                     SCOPE="PROJECT", SOURCE="OWNER_PROJECT_INPUT", EFFECTIVE_FROM_REVISION=p.get("VERSION", 1), OWNER_CONFIRMED=True, TIMESTAMP="migrated", NOTES=p.get("SOURCE_REFERENCE"))
                inputs.append(inp); out.append(_item("P7757_OWNER_PARAMETERS.json", pid, "MIGRATED_WITHOUT_LOSS", new_id=inp["OWNER_INPUT_ID"]))
            elif p.get("VALUE") is not None and p.get("DEFAULT_OR_ACTUAL") == "DEFAULT":
                rl = R.rule(rule_id=f"P7757:{pid}:TEMP", scope="TEMPORARY_DEFAULT", parameter=pid, value=p["VALUE"], unit=p.get("UNIT"), source=p.get("SOURCE_REFERENCE"))
                rules.append(rl); out.append(_item("P7757_OWNER_PARAMETERS.json", pid, "MIGRATED_WITHOUT_LOSS", new_id=rl["RULE_ID"], note="temporary default carried as a TEMPORARY_DEFAULT rule, never as an owner input"))
            else:
                out.append(_item("P7757_OWNER_PARAMETERS.json", pid, "NOT_MIGRATABLE", note=f"no value ({p.get('STATUS')}); stays an open owner question"))
    h = _read("pa04/HEIGHT_PARAMETER_TABLE.json")
    if h:
        for p in h["PARAMETERS"]:
            st = ST.from_legacy(p["STATUS"])["QUANTITY_STATUS"]
            scope = {"OWNER_ESTABLISHED": "PROJECT_OWNER_OVERRIDE", "SOURCE_ESTABLISHED": "PROJECT_DRAWING_SPEC", "TEMPORARY_DEFAULT": "TEMPORARY_DEFAULT", "PROVISIONAL": "TEMPORARY_DEFAULT"}.get(st, "UNKNOWN")
            if p.get("VALUE") is None:
                out.append(_item("pa04/HEIGHT_PARAMETER_TABLE.json", p["SCOPE"], "NOT_MIGRATABLE", note="no value; the scope stays lm-only")); continue
            rl = R.rule(rule_id=f"P7757:HEIGHT:{p['SCOPE']}", scope=scope, parameter=f"HEIGHT:{p['SCOPE']}", value=p["VALUE"], unit="m", project_id="P7757" if scope.startswith("PROJECT") else None,
                        source=p.get("SOURCE"), effective_from_revision=p.get("REVISION", 1))
            rules.append(rl); out.append(_item("pa04/HEIGHT_PARAMETER_TABLE.json", p["SCOPE"], "MIGRATED_WITHOUT_LOSS" if st != "HUMAN_REVIEW" else "MIGRATED_WITH_INFORMATION_LOSS", new_id=rl["RULE_ID"], NEW_SCOPE=scope, OLD_STATUS=p["STATUS"], NEW_STATUS=st))
    return out, inputs, rules


def migrate_openings():
    out = []
    d = _read("pa04/OPENING_REGISTER_V2.json")
    if not d:
        return out
    for o in d["OPENINGS"]:
        st = {k: ST.from_legacy(v)["QUANTITY_STATUS"] for k, v in (o.get("SOURCE") or {}).items()} if isinstance(o.get("SOURCE"), dict) else {}
        out.append(_item("pa04/OPENING_REGISTER_V2.json", o["OPENING_ID"], "MIGRATED_WITH_INFORMATION_LOSS", note="statuses carried by adapter; no plan coordinates in the record, so no OPENING_SITE identity can be attached",
                         NEW_STATUS=st, HOST_FACE_OLD=o.get("HOST_FACE"), TYPE=o.get("TYPE")))
    return out


def migrate_statuses():
    """Every legacy state token in the estimate v4 and the A22 v7 register through the forward adapter."""
    out = []
    for art in ("P7757_WALL_TREATMENT_ESTIMATE_v4.json", "pa04/A22_RECONCILIATION_REGISTER_v7.json", "pa04/WET_ROOM_REGISTER_V2.json", "COLUMN_FACE_REGISTER.json"):
        d = _read(art)
        if not d:
            continue
        tokens = Counter()
        def walk(n):
            if isinstance(n, dict):
                for k, v in n.items():
                    if isinstance(v, str) and (k.endswith("STATE") or k.endswith("STATUS") or k == "QUANTITY_STATE_LM"):
                        tokens[v] += 1
                    walk(v)
            elif isinstance(n, list):
                for v in n:
                    walk(v)
        walk(d)
        mapped = {t: ST.from_legacy(t.split(" (")[0])["QUANTITY_STATUS"] for t in tokens}
        review = {t: m for t, m in mapped.items() if m == "HUMAN_REVIEW"}
        out.append(_item(art, "STATE_TOKENS", "MIGRATED_WITHOUT_LOSS" if not review else "MIGRATED_WITH_INFORMATION_LOSS", TOKENS=dict(tokens), MAPPED=mapped,
                         note=None if not review else f"{len(review)} token(s) have no adapter and become HUMAN_REVIEW: {sorted(review)}"))
    return out


HISTORICAL = ["A22_RECONCILIATION_REGISTER_v6.json", "pa04/A22_RECONCILIATION_REGISTER_v7.json", "BENCHMARK_RECONCILIATION.json", "DUAL_BASIS_v3.json", "pa04/OWNER_DECISION_QUEUE_V4.json",
              "pa04/CHALLENGER_READINGS.json", "pa04/COLD_CHALLENGE_RECONCILIATION.json", "DIMENSION_OWNER_REGISTER.json", "QS_MEASUREMENT_REGION_REGISTER.json", "PLASTER_QUANTITY_TRACE.json",
              "pa04/OWNER_REPORT_V8.md", "OWNER_REPORT_V7.md", "VOID_GEOMETRY_RECONCILIATION.json", "pa04/STAIR_GEOMETRY_V3.json", "pa04/STRUCTURAL_EXPOSURE_REGISTER.json"]


def run(harness_run):
    items = []
    items += migrate_rooms(harness_run)
    items += migrate_cad_curves(harness_run)
    items += migrate_parapet_components(harness_run)
    own, inputs, rules = migrate_owner_parameters()
    items += own
    items += migrate_openings()
    items += migrate_statuses()
    for h in HISTORICAL:
        items.append(_item(h, "*", "HISTORICAL_ONLY", note="quantities, reconciliations, challenger readings and reports are history: the new engine recomputes from geometry + parameters; never migrated as facts"))
    by_class = Counter(i["CLASS"] for i in items)
    by_art = {}
    for i in items:
        by_art.setdefault(i["ARTIFACT"], Counter())[i["CLASS"]] += 1
    return {"ARTIFACT": "P7757_MIGRATION_REPORT", "PHASE": "PA05", "CLASSES": CLASSES, "COUNTS": dict(by_class), "BY_ARTIFACT": {k: dict(v) for k, v in by_art.items()},
            "ITEMS": items, "MIGRATED_OWNER_INPUTS": inputs, "MIGRATED_RULES": rules, "FROZEN_ARTIFACTS_EDITED": False,
            "NOTE": "frozen artifacts are read as history only; the blind rebuild never sees this report"}
