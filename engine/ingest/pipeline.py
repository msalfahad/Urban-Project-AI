"""PA06 pipeline: generic ingestion -> physical geometry -> topological
sites -> physical spaces -> semantic identity -> trade measurement regions
-> quantity bridge, with freeze barriers between the major stages.

Reuses the PA05 harness for sources, sheets, views, layer profile and
dimensions; adds the PA06 stages.  Nothing project-specific lives here.
"""

from __future__ import annotations

import hashlib
import json
import time
from collections import Counter

from engine.ingest import harness as H, ids, source_units as SU, primitive_roles as PRO, assemblies as AS, wall_continuity as WC, spaces_v2 as SP, space_boundary as SB
from engine.ingest import storeys as STY, semantics as SEM, bridge as BR, states as STS, sheet_roles as SR

STAGES_V2 = ("INGEST_PROJECT", "RESOLVE_UNITS", "CLASSIFY_SHEETS", "NORMALIZE_GEOMETRY", "BUILD_DIMENSIONS", "CLASSIFY_PRIMITIVES", "FREEZE_GEOMETRY",
             "BUILD_SITES", "BUILD_SPACES", "BUILD_SPACE_BOUNDARIES", "FREEZE_TOPOLOGY", "BUILD_STOREYS", "ATTACH_SEMANTICS", "BUILD_MEASUREMENT_REGIONS", "RUN_QA")
CONFIG_FIELDS_V2 = H.CONFIG_FIELDS + ("DECLARED_UNITS", "OWNER_PARAMETER_REGISTRY", "OWNER_STOREY_NAMES", "AI_LABELS", "SHEET_INDEX_OWNER", "TRADES")


def _digest(obj):
    return hashlib.sha256(json.dumps(obj, sort_keys=True, default=H._json_default).encode()).hexdigest()


class Pipeline(H.Run):
    def __init__(self, config):
        cfg = {k: config.get(k) for k in CONFIG_FIELDS_V2}
        unknown = set(config) - set(CONFIG_FIELDS_V2)
        if unknown:
            raise H.HarnessError(f"unknown configuration fields {sorted(unknown)}")
        super().__init__({k: v for k, v in cfg.items() if k in H.CONFIG_FIELDS})
        self.cfg.update({k: cfg.get(k) for k in CONFIG_FIELDS_V2 if k not in H.CONFIG_FIELDS})
        self.barriers = {}
        self.roles, self.sites, self.non_sites, self.bands, self.cells, self.regions, self.grids, self.edges, self.index, self.chains = {}, {}, {}, {}, {}, {}, {}, {}, {}, {}

    def run(self, until=None):
        t_all = time.perf_counter()
        for st in STAGES_V2:
            t = time.perf_counter()
            getattr(self, "stage_" + st.lower())()
            self.metrics["STAGES"][st] = {"RUNTIME_S": round(time.perf_counter() - t, 3)}
            self.stage_log.append(st)
            if until == st:
                break
        self.metrics["DETERMINISTIC_RUNTIME_S"] = round(time.perf_counter() - t_all, 3)
        self.metrics["ARTIFACT_COUNT"] = len(self.registers)
        return self

    # ---------------------------------------------------------------- units (WS1)
    def stage_resolve_units(self):
        rows = []
        declared = self.cfg.get("DECLARED_UNITS") or {}
        for path, n in list(self.normalized.items()):
            # a provisional door layer from arc statistics is only a secondary check here; the layer profile proper comes later
            from engine.ingest import views as V
            lp0 = V.layer_profile(n, linetypes=self.linetypes.get(path))
            row = SU.resolve(n, source_id=path, declared_unit=declared.get(path), door_layer=lp0.get("DOOR_LAYER"), wall_layers=lp0.get("WALL_LAYERS"))
            rows.append(row)
            if row["ACCEPTABLE_FOR_QUANTITIES"] and row["UNIT_SCALE_TO_MM"] not in (None, 1.0):
                self.normalized[path] = SU.scale_drawing(n, row["UNIT_SCALE_TO_MM"])
        self.registers["PA06_SOURCE_UNIT_REGISTER"] = SU.register(rows)
        self.units_ok = {r["SOURCE_ID"]: r["ACCEPTABLE_FOR_QUANTITIES"] for r in rows}

    # ---------------------------------------------------------------- roles (WS2, WS9)
    def stage_classify_primitives(self):
        role_rows, material, blocks, structural = [], [], [], []
        for v in self.views:
            lp = self.layers[v["SOURCE_PATH"]]
            n = self.normalized[v["SOURCE_PATH"]]
            level_layers = [l for l in lp.get("TEXT_LAYERS", []) if l not in lp["WALL_LAYERS"] and any(STY.LEVEL_RE.match(t.value.strip().replace(" ", "")) for t in v["TEXTS"] if t.provenance.layer == l)]
            rows = PRO.classify(v["PRIMITIVES"], lp, v["DIMS"], level_layers=level_layers)
            self.roles[v["VIEW_ID"]] = rows
            eids = self.entity_ids[v["VIEW_ID"]]
            for r in rows.values():
                r["ENTITY_ID"] = eids.get(r["OBJECT_ID"]); r["VIEW"] = v["VIEW_ID"]
                role_rows.append(r)
                if r["MATERIAL"]:
                    material.append({k: r[k] for k in ("ENTITY_ID", "VIEW", "KIND", "LAYER", "ROLE", "ROLE_STATUS", "ROLE_CONFIDENCE_CLASS", "LENGTH_MM", "ROLE_EVIDENCE")})
            x0, y0, x1, y1 = v["BBOX_MM"]
            inst = [i for i in n.instances if x0 <= i.transform.e <= x1 and y0 <= i.transform.f <= y1]
            for b in AS.block_objects(inst, v["PRIMITIVES"], rows):
                b["VIEW"] = v["VIEW_ID"]; blocks.append(b)
            structural.extend(dict(o, VIEW=v["VIEW_ID"]) for o in AS.structural_objects(v["PRIMITIVES"], rows, v["VIEW_ID"]))
        raw_faces = self.registers["ATOMIC_FACE_REGISTER"]["SUMMARY"]
        by_role = PRO.summarise({r["OBJECT_ID"] + r["VIEW"]: r for r in role_rows})
        self.registers["PA06_PRIMITIVE_ROLE_REGISTER"] = {"ARTIFACT": "PA06_PRIMITIVE_ROLE_REGISTER", "ROWS": role_rows, "BY_ROLE": by_role, "COUNT": len(role_rows),
                                                          "CONFIDENCE_CLASSES": ("HIGH", "MEDIUM", "LOW"), "NUMERIC_CONFIDENCE_USED": False}
        self.registers["PA06_MATERIAL_GEOMETRY_REGISTER"] = {"ARTIFACT": "PA06_MATERIAL_GEOMETRY_REGISTER", "ROWS": material, "COUNT": len(material),
                                                             "RAW_VS_ELIGIBLE": {"PA05_RAW_CANDIDATE_FACES": raw_faces, "ELIGIBLE_MATERIAL_ENTITIES": len(material),
                                                                                 "REJECTED_BY_ROLE": {k: v for k, v in by_role.items() if k not in PRO.MATERIAL_ROLES}}}
        self.registers["PA06_ASSEMBLY_OBJECT_REGISTER"] = {"ARTIFACT": "PA06_ASSEMBLY_OBJECT_REGISTER", "ROWS": blocks, "BY_ROLE": dict(Counter(b["ROLE"] for b in blocks))}
        self.registers["PA06_STRUCTURAL_OBJECT_REGISTER"] = {"ARTIFACT": "PA06_STRUCTURAL_OBJECT_REGISTER", "ROWS": structural, "BY_TYPE": dict(Counter(o["TYPE"] for o in structural))}

    def _barrier(self, name, register_names):
        body = {n: self.registers[n] for n in register_names if n in self.registers}
        self.barriers[name] = {"ARTIFACT": name, "REGISTERS": {n: _digest(r) for n, r in body.items()}, "DIGEST": _digest({n: _digest(r) for n, r in body.items()}),
                               "RULE": "downstream stages read these registers as frozen inputs; they never write back"}
        self.registers[name] = self.barriers[name]

    def stage_freeze_geometry(self):
        self._barrier("FREEZE_PA06_GEOMETRY", ["PA06_SOURCE_UNIT_REGISTER", "PA06_PRIMITIVE_ROLE_REGISTER", "PA06_MATERIAL_GEOMETRY_REGISTER", "PA06_ASSEMBLY_OBJECT_REGISTER",
                                               "PA06_STRUCTURAL_OBJECT_REGISTER", "DIMENSION_CHAIN_REGISTER", "CURVE_REGISTER", "VIEW_TRANSFORMS"])

    # ---------------------------------------------------------------- sites (WS3)
    def stage_build_sites(self):
        all_sites, all_non = [], []
        for v in self.views:
            if v["ROLE"]["FINAL_ROLE"] not in SR.PLAN_ROLES + ("UNKNOWN",):
                self.sites[v["VIEW_ID"]], self.non_sites[v["VIEW_ID"]], self.bands[v["VIEW_ID"]] = [], [], []
                continue
            s, n, b = WC.find_sites(v["VIEW_ID"], v["PRIMITIVES"], self.roles[v["VIEW_ID"]], self.entity_ids[v["VIEW_ID"]])
            self.sites[v["VIEW_ID"]], self.non_sites[v["VIEW_ID"]], self.bands[v["VIEW_ID"]] = s, n, b
            all_sites.extend(s); all_non.extend(n)
        self.registers["PA06_TOPOLOGICAL_SITE_REGISTER"] = {"ARTIFACT": "PA06_TOPOLOGICAL_SITE_REGISTER", "ROWS": all_sites, "NON_SITES": all_non, "SUMMARY": WC.summarise(all_sites),
                                                            "HOST_WALL_BANDS": sum(len(b) for b in self.bands.values()), "PRINCIPLE": "a gap is a site only inside a host-wall context; collinear stubs across a crossing wall are not sites"}

    # ---------------------------------------------------------------- spaces (WS3/WS4)
    def stage_build_spaces(self):
        cells_all, regions_all = [], []
        reg_views = {r["VIEW_ID"]: r for r in self.registers["SHEET_ROLE_REGISTER"]["VIEWS"]}
        for v in self.views:
            role = v["ROLE"]["FINAL_ROLE"]
            if v["VIEW_ID"] not in self.sites or role not in SR.PLAN_ROLES + ("UNKNOWN",):
                self.cells[v["VIEW_ID"]], self.regions[v["VIEW_ID"]], self.grids[v["VIEW_ID"]] = [], [], None
                continue
            cells, regions, grids = SP.build(v, v["PRIMITIVES"], self.roles[v["VIEW_ID"]], self.sites[v["VIEW_ID"]])
            if role == "UNKNOWN":
                # second pass: door swings (role-classified) and closed in-range cells complete the geometry hint; a view that stays UNKNOWN produces no spaces
                swings = sum(1 for r in self.roles[v["VIEW_ID"]].values() if r["ROLE"] == "DOOR_SWING")
                closed = sum(1 for c in cells if c["IN_RANGE"])
                ev = dict(reg_views[v["VIEW_ID"]]["EVIDENCE_INPUT"], DOOR_ARC_COUNT=swings, CLOSED_SPACE_COUNT=closed)
                r2 = SR.classify(ev)
                if r2["FINAL_ROLE"] in SR.PLAN_ROLES:
                    r2["ROLE_STATUS"] = "GEOMETRY_HINT_" + r2["ROLE_STATUS"]
                    v["ROLE"] = r2; reg_views[v["VIEW_ID"]].update(r2); reg_views[v["VIEW_ID"]]["EVIDENCE_INPUT"] = ev
                else:
                    reg_views[v["VIEW_ID"]]["EVIDENCE_INPUT"] = ev
                    self.cells[v["VIEW_ID"]], self.regions[v["VIEW_ID"]], self.grids[v["VIEW_ID"]] = [], [], None
                    continue
            for c in cells:
                c["VIEW_ROLE"] = v["ROLE"]["FINAL_ROLE"]; c["VIEW_ROLE_STATUS"] = v["ROLE"]["ROLE_STATUS"]
            self.cells[v["VIEW_ID"]], self.regions[v["VIEW_ID"]], self.grids[v["VIEW_ID"]] = cells, regions, grids
            cells_all.extend(cells); regions_all.extend(regions)
        self.registers["SHEET_ROLE_REGISTER"]["COUNTS"]["VIEWS"] = Counter(r["ROLE_STATUS"] for r in self.registers["SHEET_ROLE_REGISTER"]["VIEWS"])
        self.registers["PA06_PHYSICAL_SPACE_REGISTER"] = {"ARTIFACT": "PA06_PHYSICAL_SPACE_REGISTER", "REGIONS": regions_all, "CELLS": cells_all,
                                                          "COUNTS": {"REGIONS": len(regions_all), "REGIONS_IN_RANGE": sum(1 for r in regions_all if r["IN_RANGE"]), "CELLS": len(cells_all),
                                                                     "CELLS_IN_RANGE": sum(1 for c in cells_all if c["IN_RANGE"]), "OPEN_GROUPS": sum(1 for r in regions_all if r["IN_RANGE"] and r["CELL_COUNT"] > 1)},
                                                          "RULES": ["physical regions are bounded by physical separators only", "topology cells also stop at unresolved / passage sites", "UNKNOWN-role views produce no spaces"]}

    def stage_build_space_boundaries(self):
        edges_all, wl_all = [], []
        for v in self.views:
            if not self.grids.get(v["VIEW_ID"]):
                continue
            edges, index = SB.boundary_faces(v["VIEW_ID"], v["PRIMITIVES"], self.roles[v["VIEW_ID"]], self.cells[v["VIEW_ID"]], self.grids[v["VIEW_ID"]], self.sites[v["VIEW_ID"]], self.entity_ids[v["VIEW_ID"]])
            self.edges[v["VIEW_ID"]], self.index[v["VIEW_ID"]] = edges, index
            by_id = {e["BOUNDARY_EDGE_ID"]: e for e in edges}
            for c in self.cells[v["VIEW_ID"]]:
                if c["IN_RANGE"]:
                    self.chains[c["CELL_ID"]] = SB.boundary_chain(c, self.grids[v["VIEW_ID"]], index, by_id)
            edges_all.extend(edges); wl_all.extend(SB.wall_lengths(self.cells[v["VIEW_ID"]], self.regions[v["VIEW_ID"]], edges))
        self.registers["PA06_SPACE_BOUNDARY_FACE_REGISTER"] = {"ARTIFACT": "PA06_SPACE_BOUNDARY_FACE_REGISTER", "ROWS": edges_all, "COUNT": len(edges_all), "GEOMETRY_SOURCES": dict(Counter(e["GEOMETRY_SOURCE"] for e in edges_all))}
        self.registers["PA06_SPACE_WALL_LENGTH_REGISTER"] = {"ARTIFACT": "PA06_SPACE_WALL_LENGTH_REGISTER", "ROWS": wl_all,
                                                             "TOTALS_STRUCTURE_ONLY": {"VECTOR_MATERIAL_WALL_M_IN_RANGE_CELLS": round(sum(w["VECTOR_MATERIAL_WALL_M"] for w in wl_all if w["KIND"] == "TOPOLOGY_CELL" and w["IN_RANGE"]), 3),
                                                                                       "NOTE": "includes exterior cells (the building's outer faces seen from the plot); the interior-only figure is in PA06_QA_REPORT after the space class is known"},
                                                             "POLYGON_PERIMETER_USED": False, "RASTER_RUNS_USED_FOR_LENGTH": False}

    def stage_freeze_topology(self):
        self._barrier("FREEZE_PA06_TOPOLOGY", ["PA06_TOPOLOGICAL_SITE_REGISTER", "PA06_PHYSICAL_SPACE_REGISTER", "PA06_SPACE_BOUNDARY_FACE_REGISTER", "PA06_SPACE_WALL_LENGTH_REGISTER"])

    # ---------------------------------------------------------------- storeys (WS5)
    def stage_build_storeys(self):
        fams, links = STY.copy_families(self.views)
        by_view = {r["VIEW_ID"]: r for r in self.registers["SHEET_ROLE_REGISTER"]["VIEWS"]}
        rows = STY.storey_register(self.views, fams, sheet_roles_by_view=by_view, owner_storeys=self.cfg.get("OWNER_STOREY_NAMES") or {})
        self.storey_of_view = {r["PLAN_COPY_ID"]: ("HUMAN_REVIEW:STACKED_STOREYS" if r.get("STACKED_STOREYS_SUSPECTED") else (r["STOREY_NAME"] or r.get("GENERIC_NAME"))) for r in rows}
        self.registers["PA06_VIEW_COPY_FAMILY_REGISTER"] = {"ARTIFACT": "PA06_VIEW_COPY_FAMILY_REGISTER", "FAMILIES": fams, "LINKS": links}
        self.registers["PA06_STOREY_REGISTER"] = {"ARTIFACT": "PA06_STOREY_REGISTER", "ROWS": rows, "RULE": "names never from coordinate order alone; FLOOR_nn in level order or FLOOR_UNORDERED"}
        # sheet roles v2: deterministic / visual / final status with provenance
        sheets = []
        for s in self.registers["SHEET_ROLE_REGISTER"]["SHEETS"]:
            owner = (self.cfg.get("SHEET_INDEX_OWNER") or {}).get(s["SHEET_ID"])
            final_status = "OWNER_PROJECT_INPUT" if owner else ("DETERMINISTIC" if s["ROLE_STATUS"] == "DETERMINISTIC" else ("VISUAL_SEMANTIC" if s["AI_ROLE"] and s["DETERMINISTIC_ROLE"] == "UNKNOWN" else
                                                                                                                              ("HUMAN_REVIEW" if s["ROLE_STATUS"] == "CHALLENGE" else s["ROLE_STATUS"])))
            sheets.append({"SHEET_ID": s["SHEET_ID"], "PATH": s["PATH"], "PAGE": s["PAGE"], "DETERMINISTIC_ROLE": s["DETERMINISTIC_ROLE"], "VISUAL_ROLE": s["AI_ROLE"], "VISUAL_PROVENANCE": {"KIND": "AI_VISUAL_READ_RECORDED_AS_CONFIG_DATA", "EVIDENCE": s.get("EVIDENCE")},
                           "OWNER_ROLE": owner, "FINAL_ROLE": owner or s["FINAL_ROLE"], "FINAL_ROLE_STATUS": final_status, "GEOMETRY_MODIFIED_BY_ROLE": False})
        self.registers["PA06_SHEET_ROLE_REGISTER"] = {"ARTIFACT": "PA06_SHEET_ROLE_REGISTER", "SHEETS": sheets, "VIEWS": self.registers["SHEET_ROLE_REGISTER"]["VIEWS"],
                                                      "CONTRACT": ["raster-only title -> visual semantic role allowed, recorded with provenance", "owner sheet index -> OWNER_PROJECT_INPUT overrides semantic identity", "neither modifies geometry"]}

    # ---------------------------------------------------------------- semantics (WS7)
    def stage_attach_semantics(self):
        rows_all, zones_all = [], []
        for v in self.views:
            if not self.grids.get(v["VIEW_ID"]):
                continue
            x0, y0, x1, y1 = v["BBOX_MM"]
            owner = [o for o in (self.cfg.get("OWNER_ANCHORS") or []) if x0 <= o["X"] <= x1 and y0 <= o["Y"] <= y1]
            ai = [a for a in (self.cfg.get("AI_LABELS") or []) if x0 <= a["X"] <= x1 and y0 <= a["Y"] <= y1]
            rows, zones = SEM.anchors(v, self.cells[v["VIEW_ID"]], self.regions[v["VIEW_ID"]], self.grids[v["VIEW_ID"]], v["TEXTS"], owner, ai)
            # cell-level identity for the bridge
            by_cell = {}
            for z in zones:
                by_cell.setdefault(z["CELL_ID"], []).append(z)
            for c in self.cells[v["VIEW_ID"]]:
                zs = by_cell.get(c["CELL_ID"], [])
                undec = sum(1 for r in rows if r["ATTACHED_SPACE_ID"] == c["CELL_ID"] and r["TEXT_ROLE"] == "UNDECODABLE_TEXT")
                c["SEMANTIC_IDENTITY"] = {"ZONES": [(z["CANONICAL_CLASS"], z["IDENTITY_STATUS"]) for z in zs], "UNDECODABLE_LABELS": undec,
                                          "STATUS": "NONE" if not zs and not undec else ("UNRESOLVED" if (not zs or undec) else ("SINGLE" if len(zs) == 1 and zs[0]["IDENTITY_STATUS"] != "CONFLICT" else "MULTIPLE")),
                                          "NOTE": "an undecodable stamp in the cell keeps the identity UNRESOLVED even when one label reads" if undec else None}
            # space class: a cell holding site labels (neighbour / street / sea view) or bounded by plot-boundary lines is the exterior, never a room
            edge_roles = {}
            for e in self.edges.get(v["VIEW_ID"], []):
                edge_roles.setdefault(e["SPACE_ID"], set()).add(e["ROLE"])
            for c in self.cells[v["VIEW_ID"]]:
                has_rooms = bool((c.get("SEMANTIC_IDENTITY") or {}).get("ZONES"))
                ext = c.get("SITE_LABELS_INSIDE", 0) > 0 or "SITE_BOUNDARY" in edge_roles.get(c["CELL_ID"], set()) or c["TOUCHES_VIEW_EDGE"]
                if ext and has_rooms and not c["TOUCHES_VIEW_EDGE"]:
                    c["SPACE_CLASS"] = "HUMAN_REVIEW"            # room stamps and site labels in one cell: a merge or a mis-read, never decided here
                else:
                    c["SPACE_CLASS"] = "EXTERIOR_SITE" if ext else ("INTERIOR" if c["IN_RANGE"] else "OUT_OF_RANGE")
                c["QUANTITY_ELIGIBLE"] = c["SPACE_CLASS"] == "INTERIOR"
            rows_all.extend(rows); zones_all.extend(zones)
        self.registers["PA06_SEMANTIC_ANCHOR_REGISTER"] = {"ARTIFACT": "PA06_SEMANTIC_ANCHOR_REGISTER", "ROWS": rows_all, "FUNCTIONAL_ZONES": zones_all,
                                                           "COUNTS": {"ANCHORS": len(rows_all), "BY_TEXT_ROLE": dict(Counter(r["TEXT_ROLE"] for r in rows_all)), "BY_IDENTITY_STATUS": dict(Counter(r["IDENTITY_STATUS"] for r in rows_all)),
                                                                      "BY_LANGUAGE": dict(Counter(r["LANGUAGE"] for r in rows_all)), "ZONES": len(zones_all)},
                                                           "RULES": ["text never creates geometry", "AI reads are AI_INTERPRETED, never SOURCE_TEXT_ESTABLISHED", "several labels in one region stay several zones"]}

    # ---------------------------------------------------------------- bridge (WS8)
    def stage_build_measurement_regions(self):
        reg = self.cfg.get("OWNER_PARAMETER_REGISTRY") or {}
        units_ok = all(self.units_ok.values()) if self.units_ok else False
        cells_all = [c for v in self.views for c in self.cells.get(v["VIEW_ID"], [])]
        regions_all = [r for v in self.views for r in self.regions.get(v["VIEW_ID"], [])]
        edges_all = [e for v in self.views for e in self.edges.get(v["VIEW_ID"], [])]
        sites_by_id = {s["SITE_ID"]: s for v in self.views for s in self.sites.get(v["VIEW_ID"], [])}
        storey_of_cell = {c["CELL_ID"]: self.storey_of_view.get(c["VIEW"]) for c in cells_all}
        view_role = {c["CELL_ID"]: c.get("VIEW_ROLE") for c in cells_all}
        tmr, trace = BR.build(cells_all, regions_all, edges_all, self.chains, sites_by_id, storey_of_cell, reg, units_ok, view_role, trades=tuple(self.cfg.get("TRADES") or ("NORMAL_INTERNAL_PLASTER", "WET_ROOM_SPLATTER", "COLUMN_BONDING")))
        self.registers["PA06_TRADE_MEASUREMENT_REGION_REGISTER"] = tmr
        self.registers["PA06_QUANTITY_INPUT_TRACE"] = trace

    # ---------------------------------------------------------------- QA + manifest
    def stage_run_qa(self):
        tmr = self.registers["PA06_TRADE_MEASUREMENT_REGION_REGISTER"]["ROWS"]
        closure_rev = all(r["INVARIANTS"]["REVERSIBLE"] and r["INVARIANTS"]["ZERO_MATERIAL_CONTRIBUTION"] for r in tmr) if tmr else None
        roles = self.registers["PA06_PRIMITIVE_ROLE_REGISTER"]["BY_ROLE"]
        mat = self.registers["PA06_MATERIAL_GEOMETRY_REGISTER"]["ROWS"]
        qa = {"ARTIFACT": "PA06_QA_REPORT", "UNITS_ACCEPTABLE": self.units_ok, "CLOSURE_REVERSIBILITY": closure_rev,
              "CONTAMINATION": {"HATCH_STROKES_REJECTED": roles.get("HATCH_STROKE", {}).get("COUNT", 0), "DOOR_SWINGS_REJECTED": roles.get("DOOR_SWING", {}).get("COUNT", 0) + roles.get("DOOR_LEAF", {}).get("COUNT", 0),
                                "ANNOTATION_REJECTED": sum(roles.get(k, {}).get("COUNT", 0) for k in ("DIMENSION_LINE", "DIMENSION_EXTENSION", "GRID_OR_LEVEL", "TEXT_OR_LABEL")),
                                "MATERIAL_ENTITIES": len(mat), "MATERIAL_PROVISIONAL": sum(1 for m in mat if m["ROLE_STATUS"] != "ESTABLISHED"), "UNKNOWN_GEOMETRY": roles.get("UNKNOWN_GEOMETRY", {}).get("COUNT", 0)},
              "SITES": self.registers["PA06_TOPOLOGICAL_SITE_REGISTER"]["SUMMARY"], "SPACES": self.registers["PA06_PHYSICAL_SPACE_REGISTER"]["COUNTS"],
              "SPACE_CLASSES": dict(Counter(c.get("SPACE_CLASS") for c in self.registers["PA06_PHYSICAL_SPACE_REGISTER"]["CELLS"])),
              "VECTOR_MATERIAL_WALL_M_INTERIOR_CELLS": round(sum(w["VECTOR_MATERIAL_WALL_M"] for w in self.registers["PA06_SPACE_WALL_LENGTH_REGISTER"]["ROWS"] if w["KIND"] == "TOPOLOGY_CELL"
                                                              and any(c["CELL_ID"] == w["SPACE_ID"] and c.get("QUANTITY_ELIGIBLE") for c in self.registers["PA06_PHYSICAL_SPACE_REGISTER"]["CELLS"])), 3),
              "EXTERIOR_CELLS_EXCLUDED_FROM_QUANTITIES": [c["CELL_ID"] for c in self.registers["PA06_PHYSICAL_SPACE_REGISTER"]["CELLS"] if c.get("SPACE_CLASS") == "EXTERIOR_SITE"],
              "QUANTITY_LINES_BY_STATUS": self.registers["PA06_QUANTITY_INPUT_TRACE"]["BY_STATUS"], "VIEWS_WITHOUT_ROLE": [r["VIEW_ID"] for r in self.registers["SHEET_ROLE_REGISTER"]["VIEWS"] if r["FINAL_ROLE"] in ("UNKNOWN", "HUMAN_REVIEW")],
              "STOREYS_WITHOUT_NAME": [r["PLAN_COPY_ID"] for r in self.registers["PA06_STOREY_REGISTER"]["ROWS"] if not r["STOREY_NAME"]]}
        self.registers["PA06_QA_REPORT"] = qa
        from engine.ingest import owner_inputs as OI, source_inventory as SI
        store = OI.ParameterStore(self.cfg["PROJECT_ID"])
        for inp in self.cfg.get("OWNER_INPUTS") or []:
            store.set(OI.owner_input(**inp))
        self.registers["PROJECT_INGESTION_MANIFEST"] = SI.manifest(
            project_id=self.cfg["PROJECT_ID"], source_files=[s["PATH"] for s in self.cfg["SOURCES"]], drawing_family=self.cfg.get("DRAWING_FAMILY"), revision=self.cfg.get("REVISION"),
            sheet_index=[{k: s.get(k) for k in ("SHEET_ID", "PATH", "PAGE", "RASTER_ONLY", "TEXT_LAYER_AVAILABLE")} for s in self.sheets if "SHEET_ID" in s],
            view_roles=[{k: r[k] for k in ("VIEW_ID", "FINAL_ROLE", "ROLE_STATUS")} for r in self.registers["SHEET_ROLE_REGISTER"]["VIEWS"]],
            cad_units={r["SOURCE_ID"]: {"UNIT": r["UNIT_CANDIDATE"], "STATUS": r["STATUS"]} for r in self.registers["PA06_SOURCE_UNIT_REGISTER"]["ROWS"]}, transforms=self.registers["PA06_VIEW_COPY_FAMILY_REGISTER"]["LINKS"],
            available_schedules=[r["FINAL_ROLE"] for r in self.registers["SHEET_ROLE_REGISTER"]["SHEETS"] if r["FINAL_ROLE"].endswith("SCHEDULE")], missing_sources=self.registers["SOURCE_INVENTORY"]["MISSING"],
            owner_inputs={"COUNT": len(self.cfg.get("OWNER_INPUTS") or []), "SNAPSHOT_HASH": store.snapshot_hash(), "REGISTRY_ID": (self.cfg.get("OWNER_PARAMETER_REGISTRY") or {}).get("_REGISTRY_ID")},
            rule_version=self.cfg.get("RULE_VERSION"), extra={"STAGES": self.stage_log, "BARRIERS": {k: v["DIGEST"] for k, v in self.barriers.items()}})


def run(config, out_dir=None, until=None):
    r = Pipeline(config).run(until=until)
    if out_dir:
        r.write(out_dir)
    return r
