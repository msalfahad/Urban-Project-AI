"""PA07 pipeline: geometry + topology safety on top of the PA05/PA06 harness.

Serial freeze barriers (the directive's order): 1 source / unit resolution, 2 primitive roles + display semantics,
3 material bands, 4 topological sites, 5 planar faces / physical spaces, 6 semantic attachment, 7 quantity safety
bridge.  Every downstream stage reads frozen registers; none writes back.  Stages 8-12 (project regression, validation
protocol, validation result, final freeze, cold review) live in the research runner.

Principle: FAIL VISIBLY BEFORE MEASURING.  Every register row carries its state; the bridge emits a number only for a
space that passes every gate, and the safety register names the gate that blocked every other line.
"""

from __future__ import annotations

import hashlib
import json
import time
from collections import Counter, defaultdict

from engine import plaster_trade_engine as PTE, qs_measurement_region as QMR
from engine.ingest import harness as H, ids, states as STS, sheet_roles as SR, semantics as SEM, storeys as STY
from engine.ingest import pipeline as PL, material_bands as MB, band_topology as BT, planar_faces as PF, junctions as JN
from engine.ingest.bridge import TRADES, _height_for_cell, _param

STAGES7 = ("INGEST_PROJECT", "RESOLVE_UNITS", "CLASSIFY_SHEETS", "NORMALIZE_GEOMETRY", "BUILD_DIMENSIONS", "FREEZE7_1_SOURCE_UNITS",
           "CLASSIFY_PRIMITIVES", "BUILD_DISPLAY_SEMANTICS", "FREEZE7_2_PRIMITIVE_ROLES",
           "BUILD_MATERIAL_BANDS", "FREEZE7_3_MATERIAL_BANDS",
           "BUILD_BAND_TOPOLOGY", "FREEZE7_4_TOPOLOGICAL_SITES",
           "BUILD_PLANAR_FACES", "BUILD_STOREYS", "FREEZE7_5_PLANAR_FACES",
           "ATTACH_SEMANTICS7", "FREEZE7_6_SEMANTIC_ATTACHMENT",
           "BUILD_QUANTITY_SAFETY", "FREEZE7_7_QUANTITY_BRIDGE", "RUN_QA7")
PLAN_LIKE = SR.PLAN_ROLES + ("UNKNOWN",)
SITE_TYPE_MAP = {"CONFIRMED_DOOR_OPENING": "CONFIRMED_DOOR_OPENING", "CONFIRMED_WINDOW_OPENING": "CONFIRMED_WINDOW_OPENING", "CONFIRMED_GLAZED_OPENING": "CONFIRMED_WINDOW_OPENING",
                 "CONFIRMED_OPEN_PASSAGE": "CONFIRMED_OPEN_PASSAGE", "MATERIAL_CONTINUITY": "MATERIAL_CONTINUITY", "CAD_JUNCTION": "MATERIAL_CONTINUITY",
                 "PROBABLE_DOOR_OPENING": "UNRESOLVED_GAP", "UNRESOLVED": "UNRESOLVED_GAP"}
GATES = ("VIEW_ROLE", "UNIT_STATUS", "SCALE_STATUS", "SPACE_STATUS", "MATERIAL_BANDS", "OPENING_SITE_STATUS", "IDENTITY_STATUS", "STOREY_STATUS", "HEIGHT_STATUS", "RULE_STATUS")
THICKNESS_SUPPORT_MIN_COUNT = 3       # PA07R3: an authored thickness repeated at least this often in a view is project thickness evidence
SCALE_RATIO_MAX = 1.3             # PA07R2 (FM-R1-03): a plan view whose wall-thickness or door-span median differs from the source-wide median by more than this factor (either way) is a scale question
SEM_EXTERIOR_CLASSES = ("ROOF", "COURT", "GARDEN", "POOL", "BALCONY", "TERRACE")
WET_LABEL_TOKENS = tuple(sorted({k.upper() for k, v in list(SEM.AR.items()) + list(SEM.EN.items()) if v in SEM.WET}))      # every vocabulary key of a wet class (no literal room names here)
SNAP_MM = 3.0


def _digest(obj):
    return hashlib.sha256(json.dumps(obj, sort_keys=True, default=H._json_default).encode()).hexdigest()


class Pipeline7(PL.Pipeline):
    def __init__(self, config):
        super().__init__(config)
        self.bands7, self.band_rows, self.intervals, self.sites7, self.seals, self.faces, self.grids7, self.brows, self.spaces, self.qa_issues, self.cols = ({} for _ in range(11))
        self.storey_of_view = {}

    def run(self, until=None):
        t_all = time.perf_counter()
        for st in STAGES7:
            t = time.perf_counter()
            getattr(self, "stage_" + st.lower())()
            self.metrics["STAGES"][st] = {"RUNTIME_S": round(time.perf_counter() - t, 3)}
            self.stage_log.append(st)
            if until == st:
                break
        self.metrics["DETERMINISTIC_RUNTIME_S"] = round(time.perf_counter() - t_all, 3)
        self.metrics["ARTIFACT_COUNT"] = len(self.registers)
        return self

    # ------------------------------------------------------------ freeze barriers
    def _barrier7(self, name, register_names):
        self._barrier(name, register_names)
        self.registers[name]["ORDER"] = int(name.split("_")[1])

    def stage_freeze7_1_source_units(self):
        self._barrier7("FREEZE7_1_SOURCE_UNITS", ["PA06_SOURCE_UNIT_REGISTER", "SOURCE_INVENTORY", "SHEET_ROLE_REGISTER", "DIMENSION_CHAIN_REGISTER", "VIEW_TRANSFORMS"])

    def stage_freeze7_2_primitive_roles(self):
        self._barrier7("FREEZE7_2_PRIMITIVE_ROLES", ["PA06_PRIMITIVE_ROLE_REGISTER", "PA07_DISPLAY_SEMANTICS_REGISTER", "PA06_ASSEMBLY_OBJECT_REGISTER", "PA06_STRUCTURAL_OBJECT_REGISTER"])

    def stage_freeze7_3_material_bands(self):
        self._barrier7("FREEZE7_3_MATERIAL_BANDS", ["PA07_MATERIAL_BAND_REGISTER"])

    def stage_freeze7_4_topological_sites(self):
        self._barrier7("FREEZE7_4_TOPOLOGICAL_SITES", ["PA07_BAND_INTERVAL_REGISTER", "PA07_OPENING_SITE_REGISTER"])

    def stage_freeze7_5_planar_faces(self):
        self._barrier7("FREEZE7_5_PLANAR_FACES", ["PA07_PLANAR_FACE_REGISTER", "PA07_PHYSICAL_SPACE_REGISTER", "PA07_SPACE_BOUNDARY_FACE_REGISTER", "PA07_COLUMN_JUNCTION_REGISTER", "PA07_STOREY_REGISTER"])

    def stage_freeze7_6_semantic_attachment(self):
        self._barrier7("FREEZE7_6_SEMANTIC_ATTACHMENT", ["PA07_SEMANTIC_ANCHOR_REGISTER", "PA07_MISSING_SPACE_QA"])

    def stage_freeze7_7_quantity_bridge(self):
        self._barrier7("FREEZE7_7_QUANTITY_BRIDGE", ["PA07_QUANTITY_SAFETY_REGISTER", "PA07_TRADE_MEASUREMENT_REGION_REGISTER", "PA07_QUANTITY_INPUT_TRACE"])

    # ------------------------------------------------------------ PA07F display semantics
    def stage_build_display_semantics(self):
        rows, by_key = [], Counter()
        for v in self.views:
            for p in v["PRIMITIVES"]:
                pr = p.provenance
                lt = str(getattr(pr, "linetype", "BYLAYER") or "BYLAYER")
                row = {"OBJECT_ID": p.object_id, "VIEW_ID": v["VIEW_ID"], "ENTITY_TYPE": pr.entity_type, "KIND": p.kind, "LAYER": pr.layer, "LINETYPE": lt,
                       "LINETYPE_SOURCE": getattr(pr, "linetype_source", "UNRESOLVED"), "INVISIBLE": bool(getattr(pr, "invisible", False)), "LINEWEIGHT": getattr(pr, "lineweight", None),
                       "BLOCK_DEPTH": len(pr.block_path), "BLOCK_PATH": list(pr.block_path), "NON_MATERIAL_LINETYPE": any(t in lt.upper() for t in MB.NON_MATERIAL_LINETYPES),
                       "PA06_ROLE": self.roles[v["VIEW_ID"]].get(p.object_id, {}).get("ROLE")}
                rows.append(row)
                by_key[(lt, row["LINETYPE_SOURCE"])] += 1
        self.registers["PA07_DISPLAY_SEMANTICS_REGISTER"] = {
            "ARTIFACT": "PA07_DISPLAY_SEMANTICS_REGISTER", "ROWS": rows, "COUNT": len(rows),
            "BY_LINETYPE_AND_SOURCE": [{"LINETYPE": k[0], "SOURCE": k[1], "COUNT": n} for k, n in sorted(by_key.items(), key=lambda kv: -kv[1])],
            "INVISIBLE": sum(1 for r in rows if r["INVISIBLE"]), "NON_MATERIAL_LINETYPE": sum(1 for r in rows if r["NON_MATERIAL_LINETYPE"]),
            "BY_BLOCK_DEPTH": dict(Counter(r["BLOCK_DEPTH"] for r in rows)),
            "RULE": "per-entity display semantics (linetype resolved BYLAYER / BYBLOCK / override, visibility, lineweight, block transform depth) are evidence for the band engine; a hidden or invisible entity is never a material face; layer names decide nothing"}

    # ------------------------------------------------------------ PA07A bands
    def _thickness_support(self, view_id):
        """PA07R3 (PA08-R1): wall thicknesses the source repeats as authored dimensions in this view (>= THICKNESS_SUPPORT_MIN_COUNT entities of one
        displayed value within the wall-thickness range).  Evidence only; it never creates a band."""
        rows = [r for r in self.registers.get("DIMENSION_CHAIN_REGISTER", {}).get("ROWS", []) if r.get("VIEW") == view_id and r.get("DISPLAY_TEXT")]
        vals = Counter()
        for r in rows:
            try:
                v = float(str(r["DISPLAY_TEXT"]).replace(",", ".")) * (r.get("DISPLAY_FACTOR") or 1.0)
            except ValueError:
                continue
            unit = self.registers.get("PA06_SOURCE_UNIT_REGISTER", {}).get("ROWS", [])
            scale = {"cm": 10.0, "m": 1000.0, "mm": 1.0}.get(unit[0]["UNIT_CANDIDATE"] if unit else "mm", 1.0)
            mm = v * scale
            if MB.WALL_MIN_MM <= mm <= MB.THICKNESS[1]:
                vals[round(mm)] += 1
        sup = sorted(v for v, n in vals.items() if n >= THICKNESS_SUPPORT_MIN_COUNT)
        self.registers.setdefault("PA07_THICKNESS_SUPPORT", {"ARTIFACT": "PA07_THICKNESS_SUPPORT", "BY_VIEW": {}})["BY_VIEW"][view_id] = {"SUPPORTED_MM": sup, "COUNTS": dict(vals)}
        return sup

    def stage_build_material_bands(self):
        rows_all = []
        for v in self.views:
            role = v["ROLE"]["FINAL_ROLE"]
            if role not in PLAN_LIKE:
                self.bands7[v["VIEW_ID"]], self.band_rows[v["VIEW_ID"]] = [], []
                continue
            rows, bands = MB.build(v["VIEW_ID"], v["PRIMITIVES"], self.roles[v["VIEW_ID"]], storey_id=None, source_id=v["SOURCE_PATH"], view_bbox=v["BBOX_MM"], thickness_support=self._thickness_support(v["VIEW_ID"]))
            for r in rows:
                r["VIEW_ROLE_AT_BUILD"] = role
            self.bands7[v["VIEW_ID"]], self.band_rows[v["VIEW_ID"]] = bands, rows
            rows_all.extend(rows)
        self.registers["PA07_MATERIAL_BAND_REGISTER"] = {"ARTIFACT": "PA07_MATERIAL_BAND_REGISTER", "ROWS": rows_all, "COUNT": len(rows_all), "SUMMARY": MB.summarise(rows_all),
                                                         "BY_VIEW": {vid: MB.summarise(rs) for vid, rs in self.band_rows.items()},
                                                         "THRESHOLDS": {"THICKNESS_CANDIDATE_MM": MB.THICKNESS, "WALL_MIN_MM": MB.WALL_MIN_MM, "MIN_OVERLAP_MM": MB.MIN_OVERLAP_MM, "MAX_BAND_GAP_MM": MB.MAX_BAND_GAP_MM,
                                                                        "COLUMN_FREE_MAX_MM": MB.COLUMN_FREE_MAX, "COLUMN_SIDE_MAX_MM": MB.COLUMN_SIDE_MAX, "STRUCTURE_MIN_MM": MB.STRUCTURE_MIN_MM, "FAMILY_MIN": MB.FAMILY_MIN},
                                                         "PRINCIPLE": "a face is quantity-eligible only through an ACCEPTED band; every rejected or unresolved candidate keeps its reason; layers decide nothing; no raster repair"}

    # ------------------------------------------------------------ PA07B / PA07C topology
    def stage_build_band_topology(self):
        iv_all, site_all, short_rows, arb_rows = [], [], [], []
        for v in self.views:
            bands = self.bands7.get(v["VIEW_ID"], [])
            if not bands:
                self.intervals[v["VIEW_ID"]], self.sites7[v["VIEW_ID"]], self.seals[v["VIEW_ID"]] = [], [], []
                continue
            ivs, sites, seals = BT.build_view(v["VIEW_ID"], v["PRIMITIVES"], self.roles[v["VIEW_ID"]], bands, source_id=v["SOURCE_PATH"])
            seals = seals + PF.glazing_separators(v["PRIMITIVES"], self.roles[v["VIEW_ID"]])
            self.intervals[v["VIEW_ID"]], self.sites7[v["VIEW_ID"]], self.seals[v["VIEW_ID"]] = ivs, sites, seals
            short_rows.extend(BT.short_element_rows(bands, sites, v["PRIMITIVES"], self.roles[v["VIEW_ID"]]))
            arb_rows.extend(MB.arbitration_rows(bands))
            iv_all.extend(ivs); site_all.extend(sites)
        self.registers["PA07_BAND_INTERVAL_REGISTER"] = {"ARTIFACT": "PA07_BAND_INTERVAL_REGISTER", "ROWS": iv_all, "COUNT": len(iv_all), "SUMMARY": BT.summarise(iv_all, site_all),
                                                         "RULE": "every accepted band is cut into MATERIAL / OPENING / JUNCTION / UNRESOLVED intervals from the coverage of its two faces; seals close every interval end with zero-material chords"}
        self.registers["PA07_OPENING_SITE_REGISTER"] = {"ARTIFACT": "PA07_OPENING_SITE_REGISTER", "ROWS": site_all, "COUNT": len(site_all), "BY_CLASS": dict(Counter(s["CLASS"] for s in site_all)),
                                                        "BY_STATUS": dict(Counter(s["STATUS"] for s in site_all)), "CLASSES": BT.SITE_CLASSES,
                                                        "RULES": ["a single-face gap is never a doorway", "both faces interrupted -> candidate; jambs + leaf / swing -> CONFIRMED; jambs only at door span -> PROBABLE",
                                                                  "insufficient evidence -> UNRESOLVED, never merged", "CONFIRMED_OPEN_PASSAGE only after the space layer finds interior spaces on both sides",
                                                                  "PA07R3: a band end that stops short of an accepted wall hosts an END GAP interval classified by the same evidence (corner doors, doorless openings)"]}
        self.registers["PA07_SHORT_ELEMENT_REGISTER"] = {"ARTIFACT": "PA07_SHORT_ELEMENT_REGISTER", "ROWS": short_rows, "COUNT": len(short_rows), "BY_CLASS": dict(Counter(r["CONTEXT_CLASS"] for r in short_rows)),
                                                         "CLASSES": BT.SHORT_ELEMENT_CLASSES, "RULE": "PA07R3 (PA08-R1 §5): short transverse candidates are classified by context (junction, site, loop, block, family); no global relaxation of the short-pair guard"}
        self.registers["PA07_FACE_SIDE_ARBITRATION_REGISTER"] = {"ARTIFACT": "PA07_FACE_SIDE_ARBITRATION_REGISTER", "ROWS": arb_rows, "COUNT": len(arb_rows), "BY_DECISION": dict(Counter(r["DECISION"] for r in arb_rows)),
                                                                 "BY_RULE": dict(Counter(r["RULE"] for r in arb_rows)), "RULES": MB.ARBITRATION_RULES,
                                                                 "RULE": "PA07R3 (PA08-R1 §6): every face-side conflict is decided by fill, end faces, authored thickness support and continuity, deterministically; room closure is never an input; undecided conflicts stay UNRESOLVED on both sides"}

    # ------------------------------------------------------------ PA07D / PA07E faces, spaces, junctions
    def stage_build_planar_faces(self):
        faces_all, spaces_all, brows_all, cols_all, beams_all = [], [], [], [], []
        reg_views = {r["VIEW_ID"]: r for r in self.registers["SHEET_ROLE_REGISTER"]["VIEWS"]}
        for v in self.views:
            bands = self.bands7.get(v["VIEW_ID"], [])
            if not bands:
                self.faces[v["VIEW_ID"]], self.spaces[v["VIEW_ID"]], self.brows[v["VIEW_ID"]], self.cols[v["VIEW_ID"]], self.grids7[v["VIEW_ID"]] = [], [], [], [], None
                continue
            texts = self._texts(v)
            faces, grids = PF.build(v["VIEW_ID"], v["BBOX_MM"], self.seals[v["VIEW_ID"]], bands, texts, source_id=v["SOURCE_PATH"])
            brows = PF.boundary_faces(v["VIEW_ID"], faces, grids, bands, self.intervals[v["VIEW_ID"]], self.seals[v["VIEW_ID"]])
            # open passages: both sides interior planar faces
            face_of_label = {f["RUN_LABEL_NOT_A_KEY"]: f for f in faces}
            by_site = defaultdict(set)
            for r in brows:
                if r["SITE_ID"] and r["SPACE_FACE_ID"]:
                    by_site[r["SITE_ID"]].add(r["SPACE_ELIGIBILITY"])
            def sides(site):
                # PA07R1 (FM-P7-04): the two sides must be two DIFFERENT eligible planar faces
                fs = {r["SPACE_FACE_ID"]: r["SPACE_ELIGIBILITY"] for r in brows if r["SITE_ID"] == site["SITE_ID"] and r["SPACE_FACE_ID"]}
                return ("INTERIOR", "INTERIOR") if len(fs) >= 2 and all(e == "ELIGIBLE" for e in fs.values()) else ("NOT_INTERIOR", "NOT_INTERIOR")
            BT.promote_open_passages(self.sites7[v["VIEW_ID"]], sides)
            spaces = PF.space_register(v["VIEW_ID"], faces, brows)
            # second pass on the sheet role: door sites and enclosed spaces complete the geometry hint (as PA06 did); an UNKNOWN view produces no spaces
            role = v["ROLE"]["FINAL_ROLE"]
            if role == "UNKNOWN":
                # only CONFIRMED door sites count as door evidence here: a swing arc alone (PA06 role) appears on sections and elevations too
                doors = sum(1 for s in self.sites7[v["VIEW_ID"]] if s["CLASS"] == "CONFIRMED_DOOR_OPENING")
                room_labels = sum(1 for t in texts if t["ROLE"] == "ROOM_NAME")
                ev = dict(reg_views[v["VIEW_ID"]]["EVIDENCE_INPUT"], DOOR_ARC_COUNT=doors, CLOSED_SPACE_COUNT=len(spaces), ROOM_LABELS=room_labels)
                r2 = SR.classify(ev)
                if r2["FINAL_ROLE"] in SR.PLAN_ROLES and room_labels >= 1 and doors >= 1 and len(spaces) >= 2:   # PA07R1 (FM-P7-18): a plan hint needs a room label too
                    r2["ROLE_STATUS"] = "GEOMETRY_HINT_" + r2["ROLE_STATUS"]
                    v["ROLE"] = r2; reg_views[v["VIEW_ID"]].update(r2); reg_views[v["VIEW_ID"]]["EVIDENCE_INPUT"] = ev
                else:
                    reg_views[v["VIEW_ID"]]["EVIDENCE_INPUT"] = ev
            for s in spaces:
                s["VIEW_ROLE"] = v["ROLE"]["FINAL_ROLE"]; s["VIEW_ROLE_STATUS"] = v["ROLE"]["ROLE_STATUS"]
                if s["VIEW_ROLE"] == "ROOF_PLAN":
                    s["ROOF_PLAN_REVIEW"] = True
            for f in faces:
                f["VIEW_ROLE"] = v["ROLE"]["FINAL_ROLE"]
            cols, beams, ext = JN.build(v["VIEW_ID"], bands, brows, v["PRIMITIVES"], self.roles[v["VIEW_ID"]], [o for o in self.registers["PA06_STRUCTURAL_OBJECT_REGISTER"]["ROWS"] if o.get("VIEW") == v["VIEW_ID"]])
            beams["VIEW_ID"] = v["VIEW_ID"]
            self.faces[v["VIEW_ID"]], self.spaces[v["VIEW_ID"]], self.brows[v["VIEW_ID"]], self.cols[v["VIEW_ID"]], self.grids7[v["VIEW_ID"]] = faces, spaces, brows, cols, grids
            faces_all.extend(faces); spaces_all.extend(spaces); brows_all.extend(brows); cols_all.extend(cols); beams_all.append(beams)
        self.registers["SHEET_ROLE_REGISTER"]["COUNTS"]["VIEWS"] = Counter(r["ROLE_STATUS"] for r in self.registers["SHEET_ROLE_REGISTER"]["VIEWS"])
        slim = [{k: v for k, v in f.items() if k != "SEAL_INDEXES"} for f in faces_all]
        self.registers["PA07_PLANAR_FACE_REGISTER"] = {"ARTIFACT": "PA07_PLANAR_FACE_REGISTER", "ROWS": slim, "COUNT": len(slim), "BY_ELIGIBILITY": dict(Counter(f["SPACE_ELIGIBILITY"] for f in faces_all)),
                                                       "BY_VIEW_ROLE": [{"VIEW_ROLE": k[0], "ELIGIBILITY": k[1], "COUNT": n} for k, n in sorted(Counter((f["VIEW_ROLE"], f["SPACE_ELIGIBILITY"]) for f in faces_all).items())], "CELL_MM": PF.CELL_MM,
                                                       "RULE": "connected components of the whole free mask; no seed grid; a component inside an accepted band strip is wall interior; touching the view border is exterior-connected"}
        self.registers["PA07_PHYSICAL_SPACE_REGISTER"] = {"ARTIFACT": "PA07_PHYSICAL_SPACE_REGISTER", "ROWS": spaces_all, "COUNT": len(spaces_all),
                                                          "BY_VIEW_ROLE": dict(Counter(s["VIEW_ROLE"] for s in spaces_all)), "BY_GEOMETRY_STATUS": dict(Counter(s["GEOMETRY_STATUS"] for s in spaces_all))}
        self.registers["PA07_SPACE_BOUNDARY_FACE_REGISTER"] = {"ARTIFACT": "PA07_SPACE_BOUNDARY_FACE_REGISTER", "ROWS": brows_all, "COUNT": len(brows_all), "BY_KIND": dict(Counter(r["SEAL_KIND"] for r in brows_all)),
                                                               "LENGTH_SOURCE": "band developed geometry cut at junctions and column footprints; never raster runs, never polygon perimeters"}
        candidates = [{"BAND_ID": b["BAND_ID"], "VIEW_ID": vid, "REASON": (b["REASON"] or "").split(" (")[0], "SIDES_MM": [round(b["LENGTH"], 1), round(b["THK"], 1)]}
                      for vid, bl in self.bands7.items() for b in bl if b["STATUS"] == "UNRESOLVED" and (b["REASON"] or "").split(" (")[0] in ("COLUMN_CANDIDATE", "WALL_NIB_OR_PIER")]
        self.registers["PA07_COLUMN_JUNCTION_REGISTER"] = {"ARTIFACT": "PA07_COLUMN_JUNCTION_REGISTER", "ROWS": cols_all, "BEAMS": beams_all, "COUNT": len(cols_all),
                                                           "CANDIDATES_UNCONFIRMED": candidates, "CANDIDATES_RULE": "PA07R2: a free-standing crossed outline or a wall nib is listed here for structural / owner confirmation; no face of it is counted",
                                                           "SUMMARY": JN.summarise(cols_all, {"COUNT": sum(b["COUNT"] for b in beams_all)}),
                                                           "FIELDS": ["OBJECT_EXISTS", "OBJECT_GEOMETRY", "EXPOSED_TO_SPACE", "HOSTS_WALL", "TERMINATES_WALL", "CLEAR_FACE_OWNERSHIP", "TRADE_ELIGIBILITY"]}

    def _texts(self, v):
        out = []
        for t in v["TEXTS"]:
            cls = SEM.classify_text(t.value)
            out.append({"TEXT": t.value, "X": t.x, "Y": t.y, "ROLE": cls["TEXT_ROLE"], "CLASS": cls["CANONICAL_CLASS"], "LANGUAGE": cls["LANGUAGE"], "SOURCE": {"KIND": "CAD_TEXT", "LAYER": t.provenance.layer, "HANDLE": t.provenance.handle}, "SOURCE_KIND": "CAD_TEXT"})
        x0, y0, x1, y1 = v["BBOX_MM"]
        for o in (self.cfg.get("OWNER_ANCHORS") or []):
            if x0 <= o["X"] <= x1 and y0 <= o["Y"] <= y1:
                cls = SEM.classify_text(o["TEXT"]); out.append({"TEXT": o["TEXT"], "X": o["X"], "Y": o["Y"], "ROLE": cls["TEXT_ROLE"], "CLASS": cls["CANONICAL_CLASS"], "LANGUAGE": cls["LANGUAGE"], "SOURCE": {"KIND": "OWNER_PROJECT_INPUT", "ID": o.get("ID")}, "SOURCE_KIND": "OWNER_PROJECT_INPUT"})
        for a in (self.cfg.get("AI_LABELS") or []):
            if x0 <= a["X"] <= x1 and y0 <= a["Y"] <= y1:
                cls = SEM.classify_text(a["TEXT"]); out.append({"TEXT": a["TEXT"], "X": a["X"], "Y": a["Y"], "ROLE": cls["TEXT_ROLE"], "CLASS": cls["CANONICAL_CLASS"], "LANGUAGE": cls["LANGUAGE"], "SOURCE": {"KIND": "AI_VISUAL_READ", "MODEL": a.get("MODEL")}, "SOURCE_KIND": "AI_VISUAL_READ"})
        return out

    def stage_build_storeys(self):
        super().stage_build_storeys()
        # PA07R2 (FM-R1-04): a storey name taken from floor words is a HUMAN_REVIEW when the view carries floor words of more than one storey
        by_view = {v["VIEW_ID"]: v for v in self.views}
        for r in self.registers["PA06_STOREY_REGISTER"]["ROWS"]:
            if r.get("NAME_SOURCE") == "FLOOR_LABEL_TEXT":
                words = STY._floor_words(by_view.get(r["PLAN_COPY_ID"], {}))
                if len(words) > 1:
                    r["FLOOR_WORDS_IN_VIEW"] = dict(words)
                    r["STOREY_NAME"] = "HUMAN_REVIEW:CONFLICTING_FLOOR_WORDS"; r["NAME_STATUS"] = "HUMAN_REVIEW"
                    r["REVIEW"] = "PA07R2: floor words of more than one storey inside one plan view (notes such as 'UP TO FIRST FLOOR'); the owner names the storey"
                    self.storey_of_view[r["PLAN_COPY_ID"]] = r["STOREY_NAME"]
        # PA07R2 (FM-R1-02): copies of one plan that carry the same storey name (or none) are duplicates: only an owner input may pick the measured copy
        self.duplicate_copy_views = {}
        for fam in self.registers["PA06_VIEW_COPY_FAMILY_REGISTER"]["FAMILIES"]:
            by_name = defaultdict(list)
            for m in fam["MEMBERS"]:
                if m in self.storey_of_view:
                    by_name[self.storey_of_view.get(m)].append(m)
            for name, members in by_name.items():
                if len(members) > 1:
                    for m in members:
                        self.duplicate_copy_views[m] = {"FAMILY_ID": fam["FAMILY_ID"], "STOREY": name, "COPIES": sorted(members)}
        self.registers["PA07_STOREY_REGISTER"] = dict(self.registers["PA06_STOREY_REGISTER"], ARTIFACT="PA07_STOREY_REGISTER", DUPLICATE_PLAN_COPIES=self.duplicate_copy_views)

    # ------------------------------------------------------------ PA07 semantics
    def stage_attach_semantics7(self):
        rows_all, issues_all = [], []
        for v in self.views:
            faces = self.faces.get(v["VIEW_ID"], [])
            if not faces:
                continue
            texts = self._texts(v)
            spaces = self.spaces[v["VIEW_ID"]]
            face_of = {f["FACE_ID"]: f for f in faces}
            for s in spaces:
                f = face_of[s["FACE_ID"]]
                anchors = f["CONTAINS_SEMANTIC_ANCHOR"]
                rooms = [a for a in anchors if a.get("ROLE") == "ROOM_NAME"]
                undec = [a for a in anchors if a.get("ROLE") in ("UNDECODABLE_TEXT", "UNCLASSIFIED_TEXT")]
                site = [a for a in anchors if a.get("ROLE") == "SITE_LABEL"]
                classes = sorted({a["CLASS"] for a in rooms if a.get("CLASS")})
                status = "NONE" if not rooms and not undec else ("UNRESOLVED" if (not rooms or undec) else ("SINGLE" if len(classes) == 1 and len(rooms) == 1 else ("SINGLE_CLASS_REPEATED" if len(classes) == 1 else "MULTIPLE")))
                # PA07R2 (FM-R1-08): a label carrying a wet-room word whose class is not a wet class ('MASTER BATH' -> MASTER_BEDROOM) is ambiguous: HUMAN_REVIEW
                ambiguous = [a["TEXT"] for a in rooms if any(tok in str(a.get("TEXT", "")).upper() for tok in WET_LABEL_TOKENS) and a.get("CLASS") not in SEM.WET]
                if ambiguous and status in ("SINGLE", "SINGLE_CLASS_REPEATED", "MULTIPLE"):
                    status = "UNRESOLVED"
                kinds = {a.get("SOURCE_KIND", "CAD_TEXT") for a in rooms}
                if status == "SINGLE" and "AI_VISUAL_READ" in kinds:
                    status = "AI_INTERPRETED"          # PA07R1 (FM-P7-09): an AI read never becomes an established identity
                zone_status = "OWNER_ESTABLISHED" if kinds == {"OWNER_PROJECT_INPUT"} else ("AI_INTERPRETED" if "AI_VISUAL_READ" in kinds else "SOURCE_TEXT_ESTABLISHED")
                s["SEMANTIC_IDENTITY"] = {"ZONES": [(c, zone_status) for c in classes], "STATUS": status, "UNDECODABLE_LABELS": len(undec), "SITE_LABELS_INSIDE": len(site), "SOURCE_KINDS": sorted(kinds),
                                          "AMBIGUOUS_LABELS": ambiguous,
                                          "NOTE": "an undecodable stamp keeps the identity UNRESOLVED even when one label reads" if undec else ("PA07R2: wet-room word in a label whose class is not a wet class; the owner decides the identity" if ambiguous else None)}
                s["IDENTITY_STATUS"] = status
                exterior_classes = [c for c in classes if c in SEM_EXTERIOR_CLASSES]
                # PA07R2 (gate Q10): a cell whose every room label is an exterior class (GARDEN, COURT, ROOF, POOL, BALCONY, TERRACE) is not an interior room
                s["SPACE_CLASS"] = ("EXTERIOR_SITE" if site and not rooms else ("EXTERIOR_LABELLED" if (rooms and classes and len(exterior_classes) == len(classes)) else
                                    ("HUMAN_REVIEW" if (site and rooms) or s.get("ROOF_PLAN_REVIEW") or exterior_classes else "INTERIOR")))
                s["STOREY"] = self.storey_of_view.get(v["VIEW_ID"])
                for a in anchors:
                    rows_all.append({"ANCHOR_ID": ids.anchor_id(v["VIEW_ID"], a.get("ROLE"), a["TEXT"], (0.0, 0.0)), "RAW_TEXT": a["TEXT"], "TEXT_ROLE": a.get("ROLE"), "CANONICAL_CLASS": a.get("CLASS"),
                                     "ATTACHED_SPACE_ID": s["SPACE_ID"], "ATTACHED_FACE_ID": s["FACE_ID"], "IDENTITY_STATUS": status, "CREATES_GEOMETRY": False, "VIEW_ID": v["VIEW_ID"]})
            issues = PF.missing_space_qa(faces, spaces, texts)
            for i in issues:
                i["VIEW_ID"] = v["VIEW_ID"]
            issues_all.extend(issues)
        self.registers["PA07_SEMANTIC_ANCHOR_REGISTER"] = {"ARTIFACT": "PA07_SEMANTIC_ANCHOR_REGISTER", "ROWS": rows_all, "COUNT": len(rows_all),
                                                           "BY_IDENTITY_STATUS": dict(Counter(r["IDENTITY_STATUS"] for r in rows_all)), "BY_TEXT_ROLE": dict(Counter(r["TEXT_ROLE"] for r in rows_all)),
                                                           "RULES": ["text never creates geometry", "a label is not geometry proof", "several labels in one planar face stay several zones; no split, no merge"]}
        self.registers["PA07_MISSING_SPACE_QA"] = {"ARTIFACT": "PA07_MISSING_SPACE_QA", "ROWS": issues_all, "COUNT": len(issues_all), "BY_KIND": dict(Counter(i["KIND"] for i in issues_all)),
                                                   "RULE": "never invent a room for an anchor; the anchor is reported without a space"}

    # ------------------------------------------------------------ PA07H quantity safety bridge
    def stage_build_quantity_safety(self):
        reg = self.cfg.get("OWNER_PARAMETER_REGISTRY") or {}
        units_ok = all(self.units_ok.values()) if self.units_ok else False
        trades = tuple(self.cfg.get("TRADES") or ("NORMAL_INTERNAL_PLASTER", "WET_ROOM_SPLATTER", "COLUMN_BONDING"))
        safety, regions, trace = [], [], []
        self.scale_evidence = self._scale_evidence()
        for v in self.views:
            spaces = self.spaces.get(v["VIEW_ID"], [])
            if not spaces:
                continue
            bands_by_id = {b["BAND_ID"]: b for b in self.bands7[v["VIEW_ID"]]}
            sites_by_id = {s["SITE_ID"]: s for s in self.sites7[v["VIEW_ID"]]}
            brows_by_space = defaultdict(list)
            for r in self.brows[v["VIEW_ID"]]:
                if r["SPACE_FACE_ID"]:
                    brows_by_space[r["SPACE_FACE_ID"]].append(r)
            space_by_face = {x["FACE_ID"]: x for x in spaces}
            rows_by_band = defaultdict(list)
            for r in self.brows[v["VIEW_ID"]]:
                rows_by_band[r["BAND_ID"]].append(r)
            for s in spaces:
                rows = brows_by_space.get(s["FACE_ID"], [])
                s["UNLABELLED_NEIGHBOUR_ACROSS_UNEVIDENCED_BAND"] = self._unlabelled_neighbours(s, rows, rows_by_band, bands_by_id, space_by_face)
                for trade in trades:
                    gates = self._gates(s, rows, bands_by_id, sites_by_id, reg, trade, v, units_ok)
                    blocked = [g for g in GATES if gates[g]["STATUS"] != "PASS"]
                    if trade == "WET_ROOM_SPLATTER" and not any(z[0] in SEM.WET for z in s["SEMANTIC_IDENTITY"]["ZONES"]) and gates["IDENTITY_STATUS"]["STATUS"] == "PASS":
                        continue
                    if trade == "COLUMN_BONDING" and not any(r["SEAL_KIND"] == "COLUMN_FACE" for r in rows):
                        continue
                    row = {"SAFETY_ID": ids.make_id("TRADE_ZONE", s["SPACE_ID"], trade, "SAFETY"), "SPACE_ID": s["SPACE_ID"], "FACE_ID": s["FACE_ID"], "VIEW_ID": v["VIEW_ID"], "STOREY": s.get("STOREY"), "TRADE": trade,
                           "GATES": gates, "BLOCKED_BY": blocked, "BRIDGE_ALLOWED": not blocked, "QUANTITY_STATUS": None}
                    if blocked:
                        worst = "SOURCE_REQUIRED" if any(gates[g]["STATUS"] == "SOURCE_REQUIRED" for g in blocked) else ("HUMAN_REVIEW" if any(gates[g]["STATUS"] == "HUMAN_REVIEW" for g in blocked) else "NOT_ESTABLISHED")
                        row["QUANTITY_STATUS"] = worst
                        trace.append({"LINE_ID": ids.make_id("TRADE_ZONE", s["SPACE_ID"], trade, "LINE7"), "SPACE_ID": s["SPACE_ID"], "STOREY": s.get("STOREY"), "TRADE": trade, "TREATMENT": TRADES[trade][0],
                                      "MEASUREMENT_BASIS": TRADES[trade][1], "REGION_STATUS": "NOT_FORMED_GATE_BLOCKED", "BLOCKED_BY": blocked, "GATE_DETAIL": {g: gates[g] for g in blocked},
                                      "LENGTH_GEOMETRY": None, "HEIGHT_SOURCE": None, "OPENING_DEDUCTION_SOURCE": [], "TRADE_RULE": None, "SEMANTIC_IDENTITY": s["SEMANTIC_IDENTITY"], "AREA_M2_PRINCIPAL": None,
                                      "QUANTITY_STATE_ENGINE": None, "QUANTITY_STATUS": worst, "STATUS_DIMENSIONS": STS.record(QUANTITY_STATUS=worst), "ENGINE_SHEET": None, "BARE_NUMBER": False,
                                      "PROVENANCE": {"REGISTERS": ["PA07_QUANTITY_SAFETY_REGISTER"]}})
                        safety.append(row); continue
                    try:
                        region, line = self._bridge(s, rows, bands_by_id, sites_by_id, reg, trade, units_ok)
                    except Exception as e:          # PA07R2 (FM-R1-07): a bridge failure is one loud line, never a dead run
                        row["BLOCKED_BY"] = ["BRIDGE_EXCEPTION"]; row["BRIDGE_ALLOWED"] = False; row["QUANTITY_STATUS"] = "NOT_ESTABLISHED"; row["BRIDGE_EXCEPTION"] = repr(e)[:300]
                        trace.append({"LINE_ID": ids.make_id("TRADE_ZONE", s["SPACE_ID"], trade, "LINE7"), "SPACE_ID": s["SPACE_ID"], "STOREY": s.get("STOREY"), "TRADE": trade, "TREATMENT": TRADES[trade][0],
                                      "MEASUREMENT_BASIS": TRADES[trade][1], "REGION_STATUS": "NOT_FORMED_BRIDGE_EXCEPTION", "BLOCKED_BY": ["BRIDGE_EXCEPTION"], "GATE_DETAIL": {"BRIDGE_EXCEPTION": repr(e)[:300]},
                                      "LENGTH_GEOMETRY": None, "HEIGHT_SOURCE": None, "OPENING_DEDUCTION_SOURCE": [], "TRADE_RULE": None, "SEMANTIC_IDENTITY": s["SEMANTIC_IDENTITY"], "AREA_M2_PRINCIPAL": None,
                                      "QUANTITY_STATE_ENGINE": None, "QUANTITY_STATUS": "NOT_ESTABLISHED", "STATUS_DIMENSIONS": STS.record(QUANTITY_STATUS="NOT_ESTABLISHED"), "ENGINE_SHEET": None, "BARE_NUMBER": False,
                                      "PROVENANCE": {"REGISTERS": ["PA07_QUANTITY_SAFETY_REGISTER"]}})
                        safety.append(row); continue
                    row["QUANTITY_STATUS"] = line["QUANTITY_STATUS"]; row["REGION_STATUS"] = region["MEASUREMENT_REGION_STATUS"]
                    safety.append(row); regions.append(region); trace.append(line)
        self.registers["PA07_QUANTITY_SAFETY_REGISTER"] = {"ARTIFACT": "PA07_QUANTITY_SAFETY_REGISTER", "ROWS": safety, "COUNT": len(safety), "GATES": GATES,
                                                           "BLOCKED_BY_GATE": dict(Counter(g for r in safety for g in r["BLOCKED_BY"])), "BRIDGE_ALLOWED": sum(1 for r in safety if r["BRIDGE_ALLOWED"]),
                                                           "BY_QUANTITY_STATUS": dict(Counter(r["QUANTITY_STATUS"] for r in safety)),
                                                           "RULE": "a line reaches the existing engines only when every gate passes; otherwise the blocking gate is named and no number exists"}
        self.registers["PA07_TRADE_MEASUREMENT_REGION_REGISTER"] = {"ARTIFACT": "PA07_TRADE_MEASUREMENT_REGION_REGISTER", "ROWS": regions, "COUNT": len(regions),
                                                                    "REVERSIBILITY": {"ALL_REVERSIBLE": all(r["INVARIANTS"]["REVERSIBLE"] for r in regions) if regions else None,
                                                                                      "ALL_ZERO_MATERIAL": all(r["INVARIANTS"]["ZERO_MATERIAL_CONTRIBUTION"] for r in regions) if regions else None},
                                                                    "CLOSURE_CONSTANTS": QMR.CLOSURE_CONSTANTS}
        self.registers["PA07_QUANTITY_INPUT_TRACE"] = {"ARTIFACT": "PA07_QUANTITY_INPUT_TRACE", "LINES": trace, "COUNT": len(trace), "BY_STATUS": dict(Counter(t["QUANTITY_STATUS"] for t in trace)), "TOTALS": None,
                                                       "RULE": "no total: every line is an input trace with its own state; a total across states or units is refused by design"}

    def _unlabelled_neighbours(self, s, rows, rows_by_band, bands_by_id, space_by_face):
        """PA07R2 (gate Q11): a labelled space separated from an unlabelled eligible cell by an accepted band that carries no fill evidence and hosts no
        opening: a beam drawn with continuous lines, a counter or a screen would split one room exactly so; the owner confirms the partition."""
        out = []
        for r in rows:
            if r["SEAL_KIND"] != "FACE":
                continue
            b = bands_by_id.get(r["BAND_ID"])
            if b is None or b.get("LOOP") or b["EVIDENCE"].get("MATERIAL_FILL", {}).get("FILL") == "EVIDENCED":
                continue
            if any(x["SEAL_KIND"] == "OPENING_CHORD" for x in rows_by_band.get(b["BAND_ID"], [])):
                continue
            for x in rows_by_band.get(b["BAND_ID"], []):
                if x["SIDE"] == r["SIDE"] or x["SEAL_KIND"] != "FACE" or not x["SPACE_FACE_ID"] or x["SPACE_FACE_ID"] == s["FACE_ID"]:
                    continue
                n = space_by_face.get(x["SPACE_FACE_ID"])
                if n is not None and n["SEMANTIC_IDENTITY"]["STATUS"] == "NONE" and s["SEMANTIC_IDENTITY"]["STATUS"] != "NONE":
                    out.append({"BAND_ID": b["BAND_ID"], "NEIGHBOUR_SPACE_ID": n["SPACE_ID"], "NEIGHBOUR_AREA_M2": n["AREA_GEOMETRIC_M2"]})
        return out

    def _scale_evidence(self):
        """PA07R2 (FM-R1-03): per plan view, the median accepted straight-band thickness and the median confirmed door span, against the source-wide medians."""
        import statistics
        per = {}
        for v in self.views:
            if not self.spaces.get(v["VIEW_ID"]):
                continue
            thk = [b["THK"] for b in self.bands7.get(v["VIEW_ID"], []) if b["STATUS"] == "ACCEPTED" and not b.get("LOOP")]
            doors = [s["SPAN_MM"] for s in self.sites7.get(v["VIEW_ID"], []) if s["CLASS"] == "CONFIRMED_DOOR_OPENING" and s["STATUS"] == "ESTABLISHED"]
            per[v["VIEW_ID"]] = {"THK_MEDIAN_MM": statistics.median(thk) if thk else None, "DOOR_MEDIAN_MM": statistics.median(doors) if doors else None}
        all_thk = [x["THK_MEDIAN_MM"] for x in per.values() if x["THK_MEDIAN_MM"]]
        all_door = [x["DOOR_MEDIAN_MM"] for x in per.values() if x["DOOR_MEDIAN_MM"]]
        ref = {"THK_MEDIAN_MM": statistics.median(all_thk) if all_thk else None, "DOOR_MEDIAN_MM": statistics.median(all_door) if all_door else None, "PLAN_VIEWS": len(per)}
        for vid, x in per.items():
            ratios = {}
            for k in ("THK_MEDIAN_MM", "DOOR_MEDIAN_MM"):
                if x[k] and ref[k]:
                    ratios[k] = round(x[k] / ref[k], 3)
            x["RATIOS"] = ratios
            x["STATUS"] = "HUMAN_REVIEW" if any(max(r, 1.0 / r) > SCALE_RATIO_MAX for r in ratios.values() if r > 0) else ("PASS" if len(per) > 1 else "PASS_SINGLE_VIEW")
        return {"PER_VIEW": per, "REFERENCE": ref, "RULE": "only a cross-view comparison; one plan view alone cannot be checked for an enlarged copy"}

    def _gates(self, s, rows, bands_by_id, sites_by_id, reg, trade, v, units_ok):
        g = {}
        role = s.get("VIEW_ROLE")
        dup = self.duplicate_copy_views.get(v["VIEW_ID"]) if hasattr(self, "duplicate_copy_views") else None
        g["VIEW_ROLE"] = {"STATUS": ("HUMAN_REVIEW" if dup else ("PASS" if role in SR.PLAN_ROLES else "NOT_ESTABLISHED")), "VALUE": role, "DUPLICATE_PLAN_COPY": dup,
                          "WHY": "spaces are measured on plan views only; PA07R2: copies of one plan under one storey name are measured once only after the owner picks the copy"}
        g["UNIT_STATUS"] = {"STATUS": "PASS" if units_ok else "SOURCE_REQUIRED", "VALUE": self.units_ok, "WHY": "no physical length without an established source unit"}
        sc = (getattr(self, "scale_evidence", None) or {}).get("PER_VIEW", {}).get(v["VIEW_ID"], {"STATUS": "PASS_SINGLE_VIEW"})
        g["SCALE_STATUS"] = {"STATUS": "HUMAN_REVIEW" if sc.get("STATUS") == "HUMAN_REVIEW" else "PASS", "VALUE": sc, "WHY": "PA07R2: a plan view drawn at another scale than the rest of the source (enlarged detail) is a scale question"}
        unl = s.get("UNLABELLED_NEIGHBOUR_ACROSS_UNEVIDENCED_BAND") or []
        g["SPACE_STATUS"] = {"STATUS": ("HUMAN_REVIEW" if (unl and s["GEOMETRY_STATUS"] == "ESTABLISHED" and s.get("SPACE_CLASS") == "INTERIOR") else
                                        ("PASS" if (s["GEOMETRY_STATUS"] == "ESTABLISHED" and s.get("SPACE_CLASS") == "INTERIOR") else ("HUMAN_REVIEW" if s.get("SPACE_CLASS") in ("HUMAN_REVIEW", "EXTERIOR_LABELLED") else "NOT_ESTABLISHED"))),
                             "VALUE": {"GEOMETRY_STATUS": s["GEOMETRY_STATUS"], "SPACE_CLASS": s.get("SPACE_CLASS"), "UNRESOLVED_MM": s["UNRESOLVED_MM"], "UNLABELLED_NEIGHBOUR_ACROSS_UNEVIDENCED_BAND": unl},
                             "WHY": "boundary must be established material and opening chords only; exterior and provisional boundaries stay out; PA07R2: an unlabelled cell across an unevidenced band (beam, counter, screen) needs the owner"}
        bad_bands = sorted({r["BAND_ID"] for r in rows if r["MATERIAL"] and (bands_by_id.get(r["BAND_ID"], {}).get("STATUS") != "ACCEPTED" or r["FACE_POSITION_STATUS"] != "ESTABLISHED")})
        g["MATERIAL_BANDS"] = {"STATUS": "PASS" if rows and not bad_bands else ("NOT_ESTABLISHED" if rows else "NOT_ESTABLISHED"), "VALUE": {"BANDS_WITH_DOUBLED_OR_UNACCEPTED_FACES": bad_bands, "MATERIAL_MM": s["MATERIAL_BOUNDARY_MM"]},
                               "WHY": "every material stretch must come from an ACCEPTED band with an established face position (no FACE_DOUBLING ambiguity)"}
        site_ids = sorted({r["SITE_ID"] for r in rows if r["SITE_ID"]})
        bad_sites = [(sid, sites_by_id.get(sid, {}).get("CLASS"), sites_by_id.get(sid, {}).get("STATUS")) for sid in site_ids if sites_by_id.get(sid, {}).get("STATUS") not in ("ESTABLISHED",)]
        g["OPENING_SITE_STATUS"] = {"STATUS": "PASS" if not bad_sites else "NOT_ESTABLISHED", "VALUE": {"SITES": site_ids, "NOT_ESTABLISHED": bad_sites}, "WHY": "every site on the boundary must be an ESTABLISHED class; PROBABLE and UNRESOLVED block"}
        ident = s["SEMANTIC_IDENTITY"]
        needs_identity = trade in ("NORMAL_INTERNAL_PLASTER", "WET_ROOM_SPLATTER")
        g["IDENTITY_STATUS"] = {"STATUS": "PASS" if (not needs_identity or ident["STATUS"] == "SINGLE") else ("HUMAN_REVIEW" if ident["STATUS"] in ("MULTIPLE", "UNRESOLVED", "SINGLE_CLASS_REPEATED", "AI_INTERPRETED") else "NOT_ESTABLISHED"),
                                "VALUE": ident, "WHY": "the trade rule and the height selection depend on a single established room identity" if needs_identity else "column bonding needs no room identity"}
        storey = s.get("STOREY")
        g["STOREY_STATUS"] = {"STATUS": "PASS" if (isinstance(storey, str) and storey and not storey.startswith("HUMAN_REVIEW") and "UNORDERED" not in storey) else ("HUMAN_REVIEW" if isinstance(storey, str) and storey.startswith("HUMAN_REVIEW") else "NOT_ESTABLISHED"),
                              "VALUE": storey, "WHY": "storey identity from the copy-family / level register; stacked storeys in one view need review"}
        Hv, Hsrc, pid, why = _height_for_cell(ident, storey, reg, trade)
        g["HEIGHT_STATUS"] = {"STATUS": "PASS" if (Hv is not None and Hsrc in ("OWNER_PROJECT_INPUT", "SOURCE_ESTABLISHED")) else "SOURCE_REQUIRED",   # PA07R1 (FM-P7-11): a temporary default never passes
                              "VALUE": {"PARAMETER_ID": pid, "VALUE_M": Hv, "SOURCE_TYPE": Hsrc}, "WHY": why}
        g["RULE_STATUS"] = {"STATUS": "PASS" if (trade in TRADES and self.cfg.get("RULE_VERSION")) else "NOT_ESTABLISHED", "VALUE": {"RULE_VERSION": self.cfg.get("RULE_VERSION"), "TREATMENT": TRADES.get(trade, (None,))[0]},
                            "WHY": "a declared rule version and a known treatment for the trade"}
        return g

    def _bridge(self, s, rows, bands_by_id, sites_by_id, reg, trade, units_ok):
        """Physical edges and sites for the existing engines from the PA07 boundary rows; endpoints snapped so the ring closes."""
        treatment, basis = TRADES[trade]
        pts = []

        def snap(p):
            for q in pts:
                if abs(q[0] - p[0]) <= SNAP_MM and abs(q[1] - p[1]) <= SNAP_MM:
                    return q
            pts.append((round(p[0], 1), round(p[1], 1))); return pts[-1]
        phys, sites, openings = [], [], []
        for r in rows:
            b = bands_by_id[r["BAND_ID"]]
            sign = -1 if r["SIDE"] == "A" else (+1 if r["SIDE"] == "B" else 0)
            if r["SIDE"] in ("START", "END"):
                t = r["AXIAL_START"]; a = snap(MB.band_point(b, t, -b["THK"] / 2)); c = snap(MB.band_point(b, t, +b["THK"] / 2))
            else:
                a = snap(MB.band_point(b, r["AXIAL_START"], sign * b["THK"] / 2)); c = snap(MB.band_point(b, r["AXIAL_END"], sign * b["THK"] / 2))
            eid = f"BE-{r['BAND_ID']}-{r['SIDE']}-{round(r['AXIAL_START'])}"
            if r["SEAL_KIND"] in ("FACE", "COLUMN_FACE"):
                kind = "EXPOSED_COLUMN_FACE" if r["SEAL_KIND"] == "COLUMN_FACE" else ("CURVED_MATERIAL_FACE" if r["CURVATURE_TYPE"] == "ARC" else "PHYSICAL_WALL_FACE")
                phys.append({"EDGE_ID": eid, "KIND": kind, "length_m": round(r["LENGTH_MM"] / 1000, 4), "length_source": "BAND_DEVELOPED_GEOMETRY", "a": list(a), "b": list(c),
                             "trace_ids": [t for t in (r["BAND_ID"], r["INTERVAL_ID"] or (r["BAND_ID"].replace("MB-", "CO-") if r["SEAL_KIND"] == "COLUMN_FACE" else None)) if t]})
            elif r["SEAL_KIND"] == "OPENING_CHORD":
                site = sites_by_id.get(r["SITE_ID"], {})
                st = SITE_TYPE_MAP.get(site.get("CLASS"), "UNRESOLVED_GAP")
                sites.append({"SITE_ID": f"{r['SITE_ID']}@{r['SIDE']}", "SITE_TYPE": st, "termination_a": list(a), "termination_b": list(c), "span_m": round(r["LENGTH_MM"] / 1000, 4), "evidence": site.get("REASON"), "trace_ids": [r["BAND_ID"]]})
                if st in ("CONFIRMED_DOOR_OPENING", "CONFIRMED_WINDOW_OPENING"):
                    openings.append({"OPENING_ID": f"OP-{r['SITE_ID']}@{r['SIDE']}", "TYPE": "DOOR" if st == "CONFIRMED_DOOR_OPENING" else "WINDOW", "HOSTED_IN": r["BAND_ID"], "width_m": round(r["LENGTH_MM"] / 1000, 4),
                                     "width_source": "BAND_DEVELOPED_GEOMETRY", "height_m": None, "height_source": None, "trace_ids": [r["BAND_ID"]]})
            else:
                phys.append({"EDGE_ID": eid, "KIND": "UNRESOLVED_EDGE", "length_m": round(r["LENGTH_MM"] / 1000, 4), "length_source": "BAND_DEVELOPED_GEOMETRY", "a": list(a), "b": list(c), "trace_ids": [r["BAND_ID"]]})
        rid = ids.make_id("TRADE_ZONE", s["SPACE_ID"], trade, "R7")
        phys_t = [p for p in phys if p["KIND"] == "EXPOSED_COLUMN_FACE"] if trade == "COLUMN_BONDING" else phys
        sites_t, openings_t = ([], []) if trade == "COLUMN_BONDING" else (sites, openings)
        region = QMR.build_region(region_id=rid, physical_edges=phys_t, sites=sites_t, openings=openings_t, trade=treatment, basis=basis)
        region.update({"TRADE_MEASUREMENT_REGION_ID": rid, "SPACE_ID": s["SPACE_ID"], "TRADE": trade, "CLOSURE_STAMP": QMR.CLOSURE_CONSTANTS})
        Hv, Hsrc, pid, why = _height_for_cell(s["SEMANTIC_IDENTITY"], s.get("STOREY"), reg, trade)
        local = dict(reg); local["APPLICABLE_PLASTER_HEIGHT"] = {"VALUE": Hv, "SOURCE_TYPE": Hsrc, "PARAMETER_ID": pid, "WHY": why}
        sheet = PTE.calculate(region, local, treatment=treatment)
        gross = region.get("GROSS_BASIS", {})
        contributing = gross.get("CONTRIBUTING_EDGES", []) if isinstance(gross, dict) else []
        lm = round(sum(x["length_m"] for x in contributing if isinstance(x.get("length_m"), (int, float))), 4) if contributing else None
        qstate = sheet.get("QUANTITY_STATE")
        if isinstance(qstate, dict):
            qstate = qstate.get("PRINCIPAL_WALL_FACE")
        canonical = STS.adapt(qstate or "NOT_ESTABLISHED", "quantity_state")
        principal = next((l.get("AREA_M2") for l in sheet.get("SHEET", []) if l.get("LINE") == "PRINCIPAL_WALL_FACE"), None)
        line = {"LINE_ID": ids.make_id("TRADE_ZONE", rid, "LINE7"), "SPACE_ID": s["SPACE_ID"], "STOREY": s.get("STOREY"), "TRADE": trade, "TREATMENT": treatment, "MEASUREMENT_BASIS": basis,
                "REGION_STATUS": region["MEASUREMENT_REGION_STATUS"], "REGION_REASONS": region.get("NOT_ESTABLISHED_BECAUSE"), "BLOCKED_BY": [],
                "LENGTH_GEOMETRY": {"EDGE_IDS": [x["EDGE_ID"] for x in contributing], "VECTOR_LM": lm, "LENGTH_SOURCE": "BAND_DEVELOPED_GEOMETRY"},
                "HEIGHT_SOURCE": {"PARAMETER_ID": pid, "VALUE_M": Hv, "SOURCE_TYPE": Hsrc, "WHY": why},
                "OPENING_DEDUCTION_SOURCE": [{"OPENING_ID": o["OPENING_ID"], "WIDTH_M": o["width_m"], "WIDTH_SOURCE": o["width_source"], "HEIGHT_SOURCE": "PARAMETER_OR_SOURCE_REQUIRED"} for o in openings_t],
                "TRADE_RULE": {"ENGINE": "engine.plaster_trade_engine", "REGION_RULE": QMR.RULE_VERSION, "TREATMENT": treatment}, "SEMANTIC_IDENTITY": s["SEMANTIC_IDENTITY"],
                "AREA_M2_PRINCIPAL": principal, "QUANTITY_STATE_ENGINE": qstate, "QUANTITY_STATUS": canonical,
                "STATUS_DIMENSIONS": STS.record(IDENTITY_STATUS="SOURCE_ESTABLISHED" if s["SEMANTIC_IDENTITY"]["STATUS"] == "SINGLE" else "NOT_ESTABLISHED", GEOMETRY_STATUS="SOURCE_ESTABLISHED",
                                                TOPOLOGY_STATUS="SOURCE_ESTABLISHED" if region["MEASUREMENT_REGION_STATUS"] in ("MEASUREMENT_REGION_CLOSED", "MEASUREMENT_RUN_ESTABLISHED") else "NOT_ESTABLISHED",
                                                MEASUREMENT_STATUS="SOURCE_ESTABLISHED" if lm is not None else "NOT_ESTABLISHED", QUANTITY_STATUS=canonical),
                "PROVENANCE": {"REGISTERS": ["PA07_SPACE_BOUNDARY_FACE_REGISTER", "PA07_OPENING_SITE_REGISTER", "PA07_SEMANTIC_ANCHOR_REGISTER", "PA07_STOREY_REGISTER", "PA07_QUANTITY_SAFETY_REGISTER"], "OWNER_REGISTRY": reg.get("_REGISTRY_ID")},
                "ENGINE_SHEET": sheet, "BARE_NUMBER": False}
        return region, line

    # ------------------------------------------------------------ QA + manifest
    def stage_run_qa7(self):
        bands = self.registers["PA07_MATERIAL_BAND_REGISTER"]["SUMMARY"]
        faces = self.registers["PA07_PLANAR_FACE_REGISTER"]
        spaces = self.registers["PA07_PHYSICAL_SPACE_REGISTER"]["ROWS"]
        plan_spaces = [s for s in spaces if s.get("VIEW_ROLE") in SR.PLAN_ROLES]
        qa = {"ARTIFACT": "PA07_QA_REPORT", "UNITS_ACCEPTABLE": self.units_ok, "BANDS": bands, "SITES": self.registers["PA07_OPENING_SITE_REGISTER"]["BY_CLASS"], "SITE_STATUS": self.registers["PA07_OPENING_SITE_REGISTER"]["BY_STATUS"],
              "PLANAR_FACES": faces["BY_ELIGIBILITY"], "SPACES_ON_PLAN_VIEWS": len(plan_spaces), "SPACES_ON_NON_PLAN_VIEWS": len(spaces) - len(plan_spaces),
              "SPACES_BY_GEOMETRY_STATUS": dict(Counter(s["GEOMETRY_STATUS"] for s in plan_spaces)), "SPACES_BY_IDENTITY": dict(Counter(s.get("IDENTITY_STATUS") for s in plan_spaces)),
              "SPACES_BY_CLASS": dict(Counter(s.get("SPACE_CLASS") for s in plan_spaces)),
              "MATERIAL_BOUNDARY_M_PLAN_INTERIOR_STRUCTURE_ONLY": round(sum(s["MATERIAL_BOUNDARY_MM"] for s in plan_spaces if s.get("SPACE_CLASS") == "INTERIOR") / 1000, 3),
              "MATERIAL_BOUNDARY_M_PLAN_INTERIOR_ESTABLISHED_ONLY": round(sum(s["MATERIAL_BOUNDARY_MM"] for s in plan_spaces if s.get("SPACE_CLASS") == "INTERIOR" and s["GEOMETRY_STATUS"] == "ESTABLISHED") / 1000, 3),
              "MISSING_SPACE_QA": self.registers["PA07_MISSING_SPACE_QA"]["BY_KIND"], "COLUMNS": self.registers["PA07_COLUMN_JUNCTION_REGISTER"]["SUMMARY"],
              "QUANTITY_SAFETY": {"BLOCKED_BY_GATE": self.registers["PA07_QUANTITY_SAFETY_REGISTER"]["BLOCKED_BY_GATE"], "BRIDGE_ALLOWED": self.registers["PA07_QUANTITY_SAFETY_REGISTER"]["BRIDGE_ALLOWED"],
                                  "LINES_BY_STATUS": self.registers["PA07_QUANTITY_INPUT_TRACE"]["BY_STATUS"]},
              "VIEWS_WITHOUT_ROLE": [r["VIEW_ID"] for r in self.registers["SHEET_ROLE_REGISTER"]["VIEWS"] if r["FINAL_ROLE"] in ("UNKNOWN", "HUMAN_REVIEW")],
              "BARRIERS": {k: v["DIGEST"] for k, v in self.barriers.items()}}
        self.registers["PA07_QA_REPORT"] = qa
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
            rule_version=self.cfg.get("RULE_VERSION"), extra={"STAGES": self.stage_log, "BARRIERS": {k: v["DIGEST"] for k, v in self.barriers.items()}, "PIPELINE": "PA07"})


def run(config, out_dir=None, until=None):
    r = Pipeline7(config).run(until=until)
    if out_dir:
        r.write(out_dir)
    return r
