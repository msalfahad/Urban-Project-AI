"""Validation / ingestion harness (PA05 §17).

Stages: INGEST_PROJECT, CLASSIFY_SHEETS, NORMALIZE_GEOMETRY, BUILD_DIMENSIONS,
BUILD_OPENING_SITES, BUILD_PHYSICAL_SPACES, ATTACH_SEMANTICS,
BUILD_MEASUREMENT_REGIONS, RUN_QA.

Everything project-specific arrives in the configuration dictionary (paths,
sheet metadata, view assignments as points-in-view, layer overrides, owner
inputs, printed labels).  This module holds no coordinates, entity ids,
room names, file paths or dimensions of any project.
"""

from __future__ import annotations

import json
import math
import re
import time
from collections import Counter
from pathlib import Path

from engine import cad_adapter as CA
from engine.ingest import ENGINE_VERSION, ids, views as V, dimensions as D, faces as F, opening_sites as O, spaces as S, measurement_regions as M
from engine.ingest import sheet_roles as SR, source_inventory as SI, owner_inputs as OI, status as ST

STAGES = ("INGEST_PROJECT", "CLASSIFY_SHEETS", "NORMALIZE_GEOMETRY", "BUILD_DIMENSIONS", "BUILD_OPENING_SITES", "BUILD_PHYSICAL_SPACES",
          "ATTACH_SEMANTICS", "BUILD_MEASUREMENT_REGIONS", "RUN_QA")
CONFIG_FIELDS = ("PROJECT_ID", "SOURCES", "SHEET_METADATA", "VIEW_ASSIGNMENTS", "LAYER_OVERRIDES", "OWNER_INPUTS", "PRINTED_LABELS", "OWNER_ANCHORS",
                 "CAD_UNITS", "RULE_VERSION", "REVISION", "DRAWING_FAMILY", "MAX_RUNTIME_S")
LEVEL_RE = re.compile(r"^(%%p|[+\-±])\s*\d+([.,]\d+)?$")


class HarnessError(RuntimeError):
    pass


def _cfg(config):
    unknown = set(config) - set(CONFIG_FIELDS)
    if unknown:
        raise HarnessError(f"unknown configuration fields {sorted(unknown)}")
    if not config.get("PROJECT_ID") or not config.get("SOURCES"):
        raise HarnessError("PROJECT_ID and SOURCES are required")
    return {k: config.get(k) for k in CONFIG_FIELDS}


class Run:
    def __init__(self, config):
        self.cfg = _cfg(config)
        self.registers, self.metrics, self.stage_log = {}, {"STAGES": {}, "AI_CALLS": 0, "AI_WALL_CLOCK_S": 0.0}, []
        self.normalized, self.sheets, self.views, self.layers, self.linetypes = {}, [], [], {}, {}
        self.entity_ids, self.copy_offsets = {}, []

    # ---------------------------------------------------------------- stage runner
    def run(self, until=None):
        t_all = time.perf_counter()
        for st in STAGES:
            t = time.perf_counter()
            getattr(self, "stage_" + st.lower())()
            self.metrics["STAGES"][st] = {"RUNTIME_S": round(time.perf_counter() - t, 3)}
            self.stage_log.append(st)
            if until == st:
                break
        self.metrics["DETERMINISTIC_RUNTIME_S"] = round(time.perf_counter() - t_all, 3)
        self.metrics["ARTIFACT_COUNT"] = len(self.registers)
        return self

    # ---------------------------------------------------------------- 1
    def stage_ingest_project(self):
        sheets = []
        for src in self.cfg["SOURCES"]:
            path = Path(src["PATH"])
            rec = {"PATH": str(path), "KIND": src["KIND"], "FAMILY": src.get("FAMILY"), "PRESENT": path.exists(), "SHA256": SI.sha(path) if path.exists() else None}
            if not path.exists():
                rec["STATUS"] = "MISSING"; sheets.append(rec); continue
            if src["KIND"] == "CAD_DECODE_JSON":
                decoded = json.loads(path.read_text("utf-8"))
                n = CA.normalize(decoded, source_file=path.name, source_hash=rec["SHA256"])
                self.normalized[str(path)] = n
                self.linetypes[str(path)] = V.linetypes_from_decode(decoded)
                del decoded
                sid = ids.sheet_id(rec["SHA256"], "MODEL")
                sheets.append(dict(rec, SHEET_ID=sid, PAGE="MODEL", TEXT_LAYER_AVAILABLE=bool(n.texts), COUNTS={"PRIMITIVES": len(n.primitives), "TEXTS": len(n.texts), "DIMENSIONS": len(n.dimensions)}))
            elif src["KIND"] == "PRIMITIVE_JSON":
                n = primitives_from_json(json.loads(path.read_text("utf-8")), source_file=path.name, source_hash=rec["SHA256"])
                self.normalized[str(path)] = n
                self.linetypes[str(path)] = n.notes.get("LINETYPES", {})
                sid = ids.sheet_id(rec["SHA256"], "MODEL")
                sheets.append(dict(rec, SHEET_ID=sid, PAGE="MODEL", TEXT_LAYER_AVAILABLE=bool(n.texts), COUNTS={"PRIMITIVES": len(n.primitives), "TEXTS": len(n.texts), "DIMENSIONS": len(n.dimensions)}))
            elif src["KIND"] == "PDF":
                import pymupdf
                doc = pymupdf.open(str(path))
                for i, pg in enumerate(doc):
                    page = i + 1
                    txt = pg.get_text("text") or ""
                    big = []
                    for b in pg.get_text("dict")["blocks"]:
                        for l in b.get("lines", []):
                            for sp in l.get("spans", []):
                                if sp["size"] >= 9 and re.search(r"[A-Za-z]{4}", sp["text"]):
                                    big.append(sp["text"].strip())
                    sheets.append(dict(rec, SHEET_ID=ids.sheet_id(rec["SHA256"], page), PAGE=page, TEXT_LAYER_AVAILABLE=len(txt.strip()) > 0,
                                       RASTER_ONLY=(len(pg.get_drawings()) == 0 and len(pg.get_images()) > 0), TITLE_TEXTS=sorted(set(big)),
                                       COUNTS={"VECTOR_PATHS": len(pg.get_drawings()), "IMAGES": len(pg.get_images()), "TEXT_CHARS": len(txt)}))
            else:
                rec["STATUS"] = "UNSUPPORTED_KIND"; sheets.append(rec)
        self.sheets = sheets
        self.registers["SHEET_REGISTER"] = {"ARTIFACT": "SHEET_REGISTER", "ROWS": [{k: v for k, v in s.items()} for s in sheets]}

    # ---------------------------------------------------------------- 2
    def stage_classify_sheets(self):
        meta = self.cfg.get("SHEET_METADATA") or {}
        rows = []
        for s in self.sheets:
            if "SHEET_ID" not in s or s["KIND"] == "CAD_DECODE_JSON":
                continue           # a CAD model space is classified per view below
            m = (meta.get(s["PATH"]) or {}).get(str(s["PAGE"]), {})
            ev = SR.evidence(TITLE_TEXTS=(s.get("TITLE_TEXTS") or []) + list(m.get("TITLE_TEXTS") or []), SCHEDULE_TABLE=any("SCHEDULE" in t.upper() for t in s.get("TITLE_TEXTS") or []),
                             METADATA_ROLE=m.get("METADATA_ROLE"), TEXT_LAYER_AVAILABLE=s.get("TEXT_LAYER_AVAILABLE"), RASTER_ONLY=s.get("RASTER_ONLY"),
                             CUT_HATCH_PRESENT=m.get("CUT_HATCH_PRESENT"), LEVEL_SYMBOL_COUNT=m.get("LEVEL_SYMBOL_COUNT"))
            r = SR.classify(ev, ai_role=m.get("AI_ROLE"), ai_evidence=m.get("AI_EVIDENCE"))
            if m.get("AI_ROLE"):
                self.metrics["AI_CALLS"] += 0     # AI roles arrive as recorded data; the call itself is metered by the caller
            rows.append(dict(SHEET_ID=s["SHEET_ID"], PATH=s["PATH"], PAGE=s["PAGE"], EVIDENCE_INPUT=ev, **r))
        # CAD model-space views
        view_rows = []
        for path, n in self.normalized.items():
            sheet = next(s for s in self.sheets if s["PATH"] == path)
            vs = V.find_views(n.primitives, sheet["SHEET_ID"])
            lp = V.layer_profile(n, overrides=self.cfg.get("LAYER_OVERRIDES"), linetypes=self.linetypes.get(path))
            self.layers[path] = lp
            assignments = [a for a in (self.cfg.get("VIEW_ASSIGNMENTS") or []) if a.get("SOURCE_PATH") in (None, path)]
            for v in vs:
                x0, y0, x1, y1 = v["BBOX_MM"]
                texts = [t for t in n.texts if x0 <= t.x <= x1 and y0 <= t.y <= y1]
                levels = sum(1 for t in texts if LEVEL_RE.match(t.value.strip().replace(" ", "")))
                dims = [d for d in n.dimensions if x0 <= d.x1 <= x1 and y0 <= d.y1 <= y1]
                hor = sum(1 for d in dims if abs(d.y1 - d.y2) < 60); ver = sum(1 for d in dims if abs(d.x1 - d.x2) < 60)
                orient = "VERTICAL_DOMINANT" if ver > 1.5 * max(hor, 1) else ("HORIZONTAL_DOMINANT" if hor > 1.5 * max(ver, 1) else "MIXED")
                doors = sum(1 for p in v["PRIMITIVES"] if p.kind == "ARC" and lp.get("DOOR_LAYER") and p.provenance.layer == lp["DOOR_LAYER"])
                assigned = [a for a in assignments if x0 <= a["POINT_MM"][0] <= x1 and y0 <= a["POINT_MM"][1] <= y1]
                ev = SR.evidence(TITLE_TEXTS=[], LEVEL_SYMBOL_COUNT=levels, DIMENSION_ORIENTATION=orient, DOOR_ARC_COUNT=doors, CLOSED_SPACE_COUNT=None,
                                 METADATA_ROLE=assigned[0]["ROLE"] if assigned else None, TEXT_LAYER_AVAILABLE=bool(texts), ROOM_LABEL_COUNT=len(texts))
                r = SR.classify(ev, ai_role=(assigned[0].get("AI_ROLE") if assigned else None), ai_evidence=(assigned[0].get("AI_EVIDENCE") if assigned else None))
                v["ROLE"] = r; v["STOREY"] = assigned[0].get("STOREY") if assigned else None
                v["STOREY_STATUS"] = ("OWNER_ESTABLISHED" if assigned and assigned[0].get("SOURCE") == "OWNER_PROJECT_INPUT" else ("SOURCE_ESTABLISHED" if assigned else "NOT_ESTABLISHED"))
                v["SHEET_ID"] = sheet["SHEET_ID"]; v["TEXTS"] = texts; v["DIMS"] = dims; v["SOURCE_PATH"] = path
                view_rows.append({"VIEW_ID": v["VIEW_ID"], "SHEET_ID": sheet["SHEET_ID"], "BBOX_MM": v["BBOX_MM"], "ENTITY_COUNT": v["ENTITY_COUNT"], "EVIDENCE_INPUT": ev,
                                  "STOREY": v["STOREY"], "STOREY_STATUS": v["STOREY_STATUS"], **r})
            self.views.extend(vs)
        self.registers["SHEET_ROLE_REGISTER"] = {"ARTIFACT": "SHEET_ROLE_REGISTER", "SHEETS": rows, "VIEWS": view_rows,
                                                "COUNTS": {"SHEETS": Counter(r["ROLE_STATUS"] for r in rows), "VIEWS": Counter(r["ROLE_STATUS"] for r in view_rows)}}
        self.registers["SOURCE_INVENTORY"] = SI.inventory(rows + view_rows, extra_kinds=(["CAD_MODEL"] if self.normalized else []) + (["OWNER_INPUTS"] if self.cfg.get("OWNER_INPUTS") else []))

    # ---------------------------------------------------------------- 3
    def stage_normalize_geometry(self):
        faces_all, offsets_all = [], []
        for v in self.views:
            lp = self.layers[v["SOURCE_PATH"]]
            eids = {}
            for p in v["PRIMITIVES"]:
                if p.kind == "SEGMENT":
                    eids[p.object_id] = ids.entity_id(v["VIEW_ID"], p.provenance.layer, "SEGMENT", ((p.x1, p.y1), (p.x2, p.y2)), p.provenance.handle)
                elif p.kind in ("ARC", "CIRCLE"):
                    eids[p.object_id] = ids.entity_id(v["VIEW_ID"], p.provenance.layer, p.kind, (p.cx, p.cy, p.radius, p.start_angle, p.end_angle), p.provenance.handle)
            self.entity_ids[v["VIEW_ID"]] = eids
            v["FACES"] = F.atomic_faces(v["VIEW_ID"], v["PRIMITIVES"], lp["WALL_LAYERS"], eids)
            faces_all.extend(v["FACES"])
        by_path = {}
        for v in self.views:
            by_path.setdefault(v["SOURCE_PATH"], []).append(v)
        for path, vs in by_path.items():
            offsets_all.extend(V.copy_offsets(vs))
        self.copy_offsets = offsets_all
        self.registers["LAYER_PROFILE"] = {"ARTIFACT": "LAYER_PROFILE", "BY_SOURCE": self.layers}
        self.registers["VIEW_TRANSFORMS"] = {"ARTIFACT": "VIEW_TRANSFORMS", "COPY_OFFSETS": offsets_all, "NOTE": "translations between plan copies recovered by endpoint voting; refined to the exact median delta"}
        self.registers["ATOMIC_FACE_REGISTER"] = {"ARTIFACT": "ATOMIC_FACE_REGISTER", "ROWS": faces_all, "SUMMARY": F.summarise(faces_all), "NO_AXIS_ALIGNMENT_ASSUMED": True}
        # every curved entity of every view, whatever its layer role: the curve engine's developed lengths as source facts
        from engine.ingest import curves as CV
        curve_rows = []
        for v in self.views:
            for p in v["PRIMITIVES"]:
                if p.kind == "ARC":
                    a = CV.arc_from_primitive(p)
                    curve_rows.append({"ENTITY_ID": self.entity_ids[v["VIEW_ID"]][p.object_id], "VIEW": v["VIEW_ID"], "KIND": "ARC", "LAYER": p.provenance.layer, "R_MM": round(p.radius, 2),
                                       "SWEEP_RAD": round(a["SWEEP_RAD"], 6), "DEVELOPED_LENGTH_MM": round(a["LENGTH"], 2), "CHORD_MM": round(a["CHORD"], 2), "CENTRE_MM": [round(p.cx, 1), round(p.cy, 1)]})
                elif p.kind == "CIRCLE":
                    curve_rows.append({"ENTITY_ID": self.entity_ids[v["VIEW_ID"]][p.object_id], "VIEW": v["VIEW_ID"], "KIND": "CIRCLE", "LAYER": p.provenance.layer, "R_MM": round(p.radius, 2),
                                       "SWEEP_RAD": round(2 * math.pi, 6), "DEVELOPED_LENGTH_MM": round(2 * math.pi * p.radius, 2), "CHORD_MM": 0.0, "CENTRE_MM": [round(p.cx, 1), round(p.cy, 1)]})
        self.registers["CURVE_REGISTER"] = {"ARTIFACT": "CURVE_REGISTER", "ROWS": curve_rows, "COUNT": len(curve_rows), "BOUNDING_BOX_USED": False}

    # ---------------------------------------------------------------- 4
    def stage_build_dimensions(self):
        per_view = []
        for v in self.views:
            lp = self.layers[v["SOURCE_PATH"]]
            # ownership is a geometric fact: any drawn entity may terminate an extension line, whatever its layer role
            owners = [p for p in v["PRIMITIVES"] if p.object_id in self.entity_ids[v["VIEW_ID"]] and p.provenance.layer not in lp["DIMENSION_LAYERS"]]
            rows = D.walk(v["VIEW_ID"], v["DIMS"], owners, self.entity_ids[v["VIEW_ID"]], unit=self.cfg.get("CAD_UNITS") or "mm")
            per_view.append(rows)
        self.registers["DIMENSION_CHAIN_REGISTER"] = D.register(per_view)

    # ---------------------------------------------------------------- 5
    def stage_build_opening_sites(self):
        all_sites = []
        for v in self.views:
            lp = self.layers[v["SOURCE_PATH"]]
            v["SITES"] = O.find_sites(v["VIEW_ID"], v["PRIMITIVES"], lp, self.entity_ids[v["VIEW_ID"]])
            all_sites.extend(v["SITES"])
        self.registers["OPENING_SITE_REGISTER"] = {"ARTIFACT": "OPENING_SITE_REGISTER", "ROWS": all_sites, "SUMMARY": O.summarise(all_sites),
                                                  "PRINCIPLE": "absence of a door leaf is a site with UNRESOLVED status, never a merge of the rooms on both sides"}

    # ---------------------------------------------------------------- 6
    def stage_build_physical_spaces(self):
        all_spaces = []
        for v in self.views:
            plan_like = v["ROLE"]["FINAL_ROLE"] in SR.PLAN_ROLES or v["ROLE"]["FINAL_ROLE"] == "UNKNOWN"
            if not plan_like:
                v["SPACES"], v["GRID"] = [], None
                continue
            lp = self.layers[v["SOURCE_PATH"]]
            v["SPACES"], v["GRID"] = S.build(v, lp, v["SITES"], v["FACES"], self.entity_ids[v["VIEW_ID"]])
            for s in v["SPACES"]:
                s["STOREY"] = v["STOREY"]; s["STOREY_STATUS"] = v["STOREY_STATUS"]; s["VIEW_ROLE"] = v["ROLE"]["FINAL_ROLE"]; s["VIEW_ROLE_STATUS"] = v["ROLE"]["ROLE_STATUS"]
            all_spaces.extend(v["SPACES"])
        # second pass: closed-space evidence completes the geometry hint for views the first pass left UNKNOWN (never overriding a decided role)
        reg_views = {r["VIEW_ID"]: r for r in self.registers["SHEET_ROLE_REGISTER"]["VIEWS"]}
        for v in self.views:
            closed = sum(1 for s in v.get("SPACES", []) if s["TOPOLOGY_STATUS"] != "PARTIALLY_OPEN")
            v["ROLE"]["EVIDENCE_INPUT_CLOSED_SPACE_COUNT"] = closed
            if v["ROLE"]["FINAL_ROLE"] == "UNKNOWN":
                ev = dict(reg_views[v["VIEW_ID"]]["EVIDENCE_INPUT"], CLOSED_SPACE_COUNT=closed)
                r2 = SR.classify(ev)
                if r2["FINAL_ROLE"] != "UNKNOWN":
                    r2["ROLE_STATUS"] = "GEOMETRY_HINT_" + r2["ROLE_STATUS"]
                    v["ROLE"] = r2
                    reg_views[v["VIEW_ID"]].update(r2); reg_views[v["VIEW_ID"]]["EVIDENCE_INPUT"] = ev
                    for s in v.get("SPACES", []):
                        s["VIEW_ROLE"] = r2["FINAL_ROLE"]; s["VIEW_ROLE_STATUS"] = r2["ROLE_STATUS"]
        self.registers["SHEET_ROLE_REGISTER"]["COUNTS"]["VIEWS"] = Counter(r["ROLE_STATUS"] for r in self.registers["SHEET_ROLE_REGISTER"]["VIEWS"])
        self.registers["PHYSICAL_SPACE_REGISTER"] = {"ARTIFACT": "PHYSICAL_SPACE_REGISTER", "ROWS": all_spaces,
                                                    "COUNTS": Counter(s["TOPOLOGY_STATUS"] for s in all_spaces), "IDENTITY_RULE": "PHYSICAL_SPACE_ID from interior anchor + bounding entities; flood label is not a key"}

    # ---------------------------------------------------------------- 7
    def stage_attach_semantics(self):
        all_anchors = []
        for v in self.views:
            if not v.get("GRID"):
                continue
            texts = [{"TEXT": t.value, "X": t.x, "Y": t.y, "LAYER": t.provenance.layer, "HANDLE": t.provenance.handle} for t in v["TEXTS"]]
            x0, y0, x1, y1 = v["BBOX_MM"]
            printed = [p for p in (self.cfg.get("PRINTED_LABELS") or []) if x0 <= p["X"] <= x1 and y0 <= p["Y"] <= y1]
            owner = [o for o in (self.cfg.get("OWNER_ANCHORS") or []) if x0 <= o["X"] <= x1 and y0 <= o["Y"] <= y1]
            all_anchors.extend(S.anchors(v, v["SPACES"], v["GRID"], texts, printed, owner))
        self.registers["SEMANTIC_ANCHOR_REGISTER"] = {"ARTIFACT": "SEMANTIC_ANCHOR_REGISTER", "ROWS": all_anchors, "COUNTS": Counter(a["STATUS"] for a in all_anchors),
                                                     "PRINCIPLE": "GEOMETRY_ID and SEMANTIC_IDENTITY are separate objects; an anchor never renames geometry"}

    # ---------------------------------------------------------------- 8
    def stage_build_measurement_regions(self):
        proofs, regions = [], []
        for v in self.views:
            if not v.get("SPACES"):
                continue
            proof, regs = M.prove_reversible(v["SPACES"], v["FACES"], v["SITES"])
            proofs.append(dict(VIEW_ID=v["VIEW_ID"], **proof)); regions.extend(regs)
        self.registers["MEASUREMENT_REGION_REGISTER"] = {"ARTIFACT": "MEASUREMENT_REGION_REGISTER", "ROWS": regions, "REVERSIBILITY_PROOFS": proofs,
                                                        "ALL_REVERSIBLE": all(p["REVERSIBLE"] for p in proofs) if proofs else None, "CLOSURE_STAMP": M.CLOSURE_STAMP}

    # ---------------------------------------------------------------- 9
    def stage_run_qa(self):
        qa = {}
        qa["CLOSURE_REVERSIBILITY"] = self.registers["MEASUREMENT_REGION_REGISTER"]["ALL_REVERSIBLE"]
        # id stability: re-derive entity ids from a shuffled copy of one view's primitives
        import random
        stable = True
        for v in self.views[:3]:
            prims = list(v["PRIMITIVES"]); random.Random(7).shuffle(prims)
            for p in prims:
                if p.kind == "SEGMENT":
                    e = ids.entity_id(v["VIEW_ID"], p.provenance.layer, "SEGMENT", ((p.x2, p.y2), (p.x1, p.y1)), None)     # reversed endpoints, no handle
                    stable &= e == self.entity_ids[v["VIEW_ID"]][p.object_id]
        qa["ID_STABILITY_SHUFFLE_AND_REVERSE"] = stable
        qa["UNOWNED_DIMENSIONS"] = self.registers["DIMENSION_CHAIN_REGISTER"]["COUNTS"]["BY_OWNER_STATUS"]["UNOWNED"]
        qa["UNRESOLVED_OPENING_SITES"] = self.registers["OPENING_SITE_REGISTER"]["SUMMARY"]["UNRESOLVED_OPENING_SITE"]
        qa["VIEWS_WITHOUT_ROLE"] = [r["VIEW_ID"] for r in self.registers["SHEET_ROLE_REGISTER"]["VIEWS"] if r["FINAL_ROLE"] in ("UNKNOWN", "HUMAN_REVIEW")]
        qa["SHEETS_WITHOUT_ROLE"] = [r["SHEET_ID"] for r in self.registers["SHEET_ROLE_REGISTER"]["SHEETS"] if r["FINAL_ROLE"] in ("UNKNOWN", "HUMAN_REVIEW")]
        qa["SPACES_WITH_MULTIPLE_LABELS"] = sum(1 for s in self.registers["PHYSICAL_SPACE_REGISTER"]["ROWS"] if (s["SEMANTIC_IDENTITY"] or {}).get("STATUS") == "MULTIPLE_LABELS_ONE_TOPOLOGY_CELL")
        qa["MISSING_SOURCES"] = self.registers["SOURCE_INVENTORY"]["MISSING"]
        limit = self.cfg.get("MAX_RUNTIME_S")
        qa["PERFORMANCE_WITHIN_LIMIT"] = None if not limit else sum(s["RUNTIME_S"] for s in self.metrics["STAGES"].values()) <= limit
        self.registers["QA_REPORT"] = {"ARTIFACT": "QA_REPORT", **qa}
        # manifest
        store = OI.ParameterStore(self.cfg["PROJECT_ID"])
        for inp in self.cfg.get("OWNER_INPUTS") or []:
            store.set(OI.owner_input(**inp))
        self.registers["PROJECT_INGESTION_MANIFEST"] = SI.manifest(
            project_id=self.cfg["PROJECT_ID"], source_files=[s["PATH"] for s in self.cfg["SOURCES"]], drawing_family=self.cfg.get("DRAWING_FAMILY"), revision=self.cfg.get("REVISION"),
            sheet_index=[{k: s.get(k) for k in ("SHEET_ID", "PATH", "PAGE", "RASTER_ONLY", "TEXT_LAYER_AVAILABLE")} for s in self.sheets if "SHEET_ID" in s],
            view_roles=[{k: r[k] for k in ("VIEW_ID", "FINAL_ROLE", "ROLE_STATUS", "STOREY", "STOREY_STATUS")} for r in self.registers["SHEET_ROLE_REGISTER"]["VIEWS"]]
            + [{k: r[k] for k in ("SHEET_ID", "FINAL_ROLE", "ROLE_STATUS")} for r in self.registers["SHEET_ROLE_REGISTER"]["SHEETS"]],
            cad_units=self.cfg.get("CAD_UNITS") or "mm", transforms=self.copy_offsets, available_schedules=[r["FINAL_ROLE"] for r in self.registers["SHEET_ROLE_REGISTER"]["SHEETS"] if r["FINAL_ROLE"].endswith("SCHEDULE")],
            missing_sources=self.registers["SOURCE_INVENTORY"]["MISSING"], owner_inputs={"COUNT": len(self.cfg.get("OWNER_INPUTS") or []), "SNAPSHOT_HASH": store.snapshot_hash()},
            rule_version=self.cfg.get("RULE_VERSION"), extra={"LAYER_PROFILE_HASHES": {p: l["EVIDENCE"]["profile_hash"] for p, l in self.layers.items()}, "STAGES": self.stage_log})

    # ---------------------------------------------------------------- output
    def write(self, out_dir):
        out = Path(out_dir); out.mkdir(parents=True, exist_ok=True)
        written = {}
        for name, reg in self.registers.items():
            p = out / f"{name}.json"
            p.write_text(json.dumps(reg, indent=1, default=_json_default, sort_keys=False), "utf-8")
            written[name] = str(p)
        (out / "HARNESS_METRICS.json").write_text(json.dumps(self.metrics, indent=1, default=_json_default), "utf-8")
        return written


def primitives_from_json(doc, *, source_file="", source_hash=""):
    """A NormalizedDrawing from a plain JSON document: {"insunits": 4, "dimlfac": 1.0, "linetypes": {layer: name},
    "primitives": [{"kind": "SEGMENT"|"ARC"|"CIRCLE", "layer", "handle", "x1","y1","x2","y2" | "cx","cy","r","a0","a1"}],
    "texts": [{"value","x","y","height","layer","handle"}], "dimensions": [{"x1","y1","x2","y2","display","user_text","layer","handle","type"}]}."""
    prims, texts, dims = [], [], []
    for i, p in enumerate(doc.get("primitives", [])):
        prov = CA.Provenance(handle=int(p.get("handle", i + 1)), entity_type=p["kind"], layer=str(p.get("layer", "0")), source_hash=source_hash[:16])
        if p["kind"] == "SEGMENT":
            prims.append(CA.Primitive(kind="SEGMENT", provenance=prov, x1=float(p["x1"]), y1=float(p["y1"]), x2=float(p["x2"]), y2=float(p["y2"])))
        elif p["kind"] == "ARC":
            prims.append(CA.Primitive(kind="ARC", provenance=prov, cx=float(p["cx"]), cy=float(p["cy"]), radius=float(p["r"]), start_angle=float(p.get("a0", 0.0)), end_angle=float(p.get("a1", 6.283185307))))
        elif p["kind"] == "CIRCLE":
            prims.append(CA.Primitive(kind="CIRCLE", provenance=prov, cx=float(p["cx"]), cy=float(p["cy"]), radius=float(p["r"])))
    for i, t in enumerate(doc.get("texts", [])):
        prov = CA.Provenance(handle=int(t.get("handle", 100000 + i)), entity_type="TEXT", layer=str(t.get("layer", "TEXT")), source_hash=source_hash[:16])
        texts.append(CA.TextObservation(value=str(t["value"]), x=float(t["x"]), y=float(t["y"]), height=float(t.get("height", 250.0)), provenance=prov))
    dimlfac = float(doc.get("dimlfac", 1.0))
    for i, d in enumerate(doc.get("dimensions", [])):
        prov = CA.Provenance(handle=int(d.get("handle", 200000 + i)), entity_type=str(d.get("type", "21")), layer=str(d.get("layer", "DIM")), source_hash=source_hash[:16])
        geom = math.hypot(float(d["x2"]) - float(d["x1"]), float(d["y2"]) - float(d["y1"]))
        dims.append(CA.DimensionObservation(geometry_mm=geom, display_value=(None if d.get("display") is None else float(d["display"])), dimlfac=dimlfac, user_text=str(d.get("user_text", "")),
                                            x1=float(d["x1"]), y1=float(d["y1"]), x2=float(d["x2"]), y2=float(d["y2"]), provenance=prov))
    ins = doc.get("insunits")
    n = CA.NormalizedDrawing(source_file=source_file, source_hash=source_hash, drawing_unit=("millimetre" if ins == 4 else "NOT_ESTABLISHED" if ins in (None, 0) else f"insunits_code_{ins}"),
                             insunits_code=ins, dimlfac=dimlfac, primitives=prims, texts=texts, dimensions=dims)
    n.notes["LINETYPES"] = doc.get("linetypes", {})
    return n


def _json_default(o):
    if isinstance(o, Counter):
        return dict(o)
    if hasattr(o, "tolist"):
        return o.tolist()
    if isinstance(o, (set, frozenset)):
        return sorted(o)
    if isinstance(o, float) and (math.isnan(o) or math.isinf(o)):
        return None
    return str(o)


def run(config, out_dir=None, until=None):
    r = Run(config).run(until=until)
    if out_dir:
        r.write(out_dir)
    return r
