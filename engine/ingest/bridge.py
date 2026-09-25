"""Quantity bridge (PA06 WS8): PA06 registers -> the tested deterministic
engines (engine.qs_measurement_region, engine.plaster_trade_engine,
engine.quantity_state, engine.opening_register) through explicit
adapters.  No new quantity logic lives here.  Every line carries
references to its length geometry, height source, opening deduction
source, trade rule, measurement basis, state and provenance; nothing is
a bare number, and no total is produced.
"""

from __future__ import annotations

from collections import Counter

from engine import plaster_trade_engine as PTE, qs_measurement_region as QMR
from engine.ingest import ids, states as STS
from engine.ingest.semantics import WET, HEIGHT_NOT_NORMAL, INTERIOR_ROOM_CLASSES

SITE_TYPE_MAP = {"CONFIRMED_DOOR_OPENING": "CONFIRMED_DOOR_OPENING", "CONFIRMED_WINDOW_OPENING": "CONFIRMED_WINDOW_OPENING", "CONFIRMED_OPEN_PASSAGE": "CONFIRMED_OPEN_PASSAGE",
                 "MATERIAL_CONTINUITY_GAP": "MATERIAL_CONTINUITY", "CAD_JUNCTION_GAP": "MATERIAL_CONTINUITY", "UNRESOLVED_SITE": "UNRESOLVED_GAP"}
TRADES = {"NORMAL_INTERNAL_PLASTER": ("NORMAL_INTERNAL_PLASTER", "WALL_FACE_PLASTER"), "WET_ROOM_SPLATTER": ("TILE_PREP_TARTUSHA", "WALL_FACE_PLASTER"),
          "COLUMN_BONDING": ("COLUMN_BONDING_PLUS_PLASTER", QMR.LINEAR_RUN), "EXTERNAL_PLASTER": ("EXTERNAL_PLASTER", QMR.LINEAR_RUN), "PARAPET": ("ROOF_PARAPET_EXTERNAL_FACE", QMR.LINEAR_RUN)}
INTERIOR_CLASSES_FOR_AREA = INTERIOR_ROOM_CLASSES
HEIGHT_EXCLUDED_CLASSES = HEIGHT_NOT_NORMAL
STOREY_TOKENS = {"GROUND_FLOOR": "GROUND", "FIRST_FLOOR": "FIRST", "SECOND_FLOOR": "SECOND", "ROOF": "SECOND_ROOF_ROOM", "BASEMENT": "BASEMENT"}


def _param(reg, pid):
    p = reg.get(pid) or {}
    return p.get("VALUE"), p.get("SOURCE_TYPE") or "UNKNOWN", pid


def _height_for_cell(cell_sem, storey_name, reg, trade):
    """Which height parameter governs this cell for this trade, and why.  Returns (value, source_type, parameter id, note)."""
    classes = [z[0] for z in (cell_sem or {}).get("ZONES", [])]
    status = (cell_sem or {}).get("STATUS")
    if trade == "WET_ROOM_SPLATTER":
        v, st, pid = _param(reg, "TARTUSHA_HEIGHT")
        return v, st, pid, "tartusha height is a trade parameter; not the storey height"
    if trade == "EXTERNAL_PLASTER":
        tok = STOREY_TOKENS.get(storey_name or "", None)
        if tok is None:
            return None, "UNKNOWN", None, "storey name not established: external storey height cannot be selected"
        v, st, pid = _param(reg, f"EXTERNAL_STOREY_HEIGHT_{tok}")
        return v, st, pid, "external face height by storey"
    if trade == "PARAPET":
        v, st, pid = _param(reg, "ROOF_PARAPET_RULE")
        return None if not isinstance(v, (int, float)) else v, st, pid, "parapet heights come from the parapet rule / sections, never a storey height"
    if status not in ("SINGLE",):
        return None, "UNKNOWN", None, f"identity {status}: the normal internal height applies only to a single established dry / circulation room"
    if any(c in HEIGHT_EXCLUDED_CLASSES for c in classes):
        return None, "UNKNOWN", None, f"class {classes} may be double height / stair well / exterior: a section or an owner scope is required"
    v, st, pid = _param(reg, "NORMAL_INTERNAL_PLASTER_HEIGHT")
    return v, st, pid, "normal internal plaster height (owner project input) for a single normal room"


def build(cells, regions, edges, chains_by_cell, sites_by_id, storey_of_cell, reg, unit_status_ok, view_role_of_cell, trades=("NORMAL_INTERNAL_PLASTER", "WET_ROOM_SPLATTER", "COLUMN_BONDING")):
    """TRADE_MEASUREMENT_REGION_REGISTER + QUANTITY_INPUT_TRACE for every in-range topology cell."""
    region_rows, trace = [], []
    edges_by_id = {e["BOUNDARY_EDGE_ID"]: e for e in edges}
    for c in cells:
        if not c["IN_RANGE"]:
            continue
        if not c.get("QUANTITY_ELIGIBLE", c["IN_RANGE"]):
            trace.append({"LINE_ID": ids.make_id("TRADE_ZONE", c["CELL_ID"], "EXTERIOR", "LINE"), "CELL_ID": c["CELL_ID"], "PHYSICAL_SPACE_ID": c.get("PHYSICAL_SPACE_ID"), "STOREY": storey_of_cell.get(c["CELL_ID"]),
                          "TRADE": "NONE", "TREATMENT": None, "MEASUREMENT_BASIS": None, "REGION_STATUS": "NOT_A_ROOM", "REGION_REASONS": [{"REASON": "EXTERIOR_SITE_CELL", "EVIDENCE": {"SITE_LABELS_INSIDE": c.get("SITE_LABELS_INSIDE"), "SPACE_CLASS": c.get("SPACE_CLASS")}}],
                          "LENGTH_GEOMETRY": None, "HEIGHT_SOURCE": None, "OPENING_DEDUCTION_SOURCE": [], "TRADE_RULE": None, "SEMANTIC_IDENTITY": c.get("SEMANTIC_IDENTITY"), "AREA_M2_PRINCIPAL": None,
                          "QUANTITY_STATE_ENGINE": None, "QUANTITY_STATUS": "NOT_APPLICABLE", "STATUS_DIMENSIONS": STS.record(TOPOLOGY_STATUS="SOURCE_ESTABLISHED", QUANTITY_STATUS="NOT_APPLICABLE"),
                          "PROVENANCE": {"REGISTERS": ["PA06_PHYSICAL_SPACE_REGISTER", "PA06_SEMANTIC_ANCHOR_REGISTER"]}, "ENGINE_SHEET": None, "BARE_NUMBER": False,
                          "NOTE": "exterior cell (site labels inside / plot boundary / view edge): external faces belong to the EXTERNAL_PLASTER adapter, no internal or floor line"})
            continue
        chains = chains_by_cell.get(c["CELL_ID"], [])
        sem = c.get("SEMANTIC_IDENTITY")
        storey = storey_of_cell.get(c["CELL_ID"])
        # fail-safes: a cell that sees BOTH sides of one material entity has merged through a wall interior (jamb-less opening);
        # a cell in a view with stacked level marks may be an overlay of storeys.  Either -> HUMAN_REVIEW, no number.
        cell_edges = [e for e in edges if e["SPACE_ID"] == c["CELL_ID"] and e["MATERIAL_PRESENT"]]
        sides = {}
        for e in cell_edges:
            sides.setdefault(e["ENTITY_ID"], set()).add(e["SIDE"])
        two_sided = sorted(k for k, v in sides.items() if len(v) == 2)
        review = []
        if two_sided:
            review.append({"REASON": "CELL_SEES_BOTH_SIDES_OF_A_MATERIAL_ENTITY", "ENTITIES": two_sided[:10], "COUNT": len(two_sided)})
        if isinstance(storey, str) and storey.startswith("HUMAN_REVIEW"):
            review.append({"REASON": "STACKED_STOREYS_SUSPECTED_IN_VIEW"})
        if review:
            for trade in trades:
                trace.append({"LINE_ID": ids.make_id("TRADE_ZONE", c["CELL_ID"], trade, "REVIEW"), "CELL_ID": c["CELL_ID"], "PHYSICAL_SPACE_ID": c.get("PHYSICAL_SPACE_ID"), "STOREY": storey, "TRADE": trade,
                              "TREATMENT": TRADES[trade][0], "MEASUREMENT_BASIS": TRADES[trade][1], "REGION_STATUS": "HUMAN_REVIEW", "REGION_REASONS": review, "LENGTH_GEOMETRY": None, "HEIGHT_SOURCE": None,
                              "OPENING_DEDUCTION_SOURCE": [], "TRADE_RULE": None, "SEMANTIC_IDENTITY": sem, "AREA_M2_PRINCIPAL": None, "QUANTITY_STATE_ENGINE": None, "QUANTITY_STATUS": "HUMAN_REVIEW",
                              "STATUS_DIMENSIONS": STS.record(TOPOLOGY_STATUS="HUMAN_REVIEW", QUANTITY_STATUS="HUMAN_REVIEW"), "PROVENANCE": {"REGISTERS": ["PA06_SPACE_BOUNDARY_FACE_REGISTER", "PA06_STOREY_REGISTER"]},
                              "ENGINE_SHEET": None, "BARE_NUMBER": False})
            c["REVIEW_FLAGS"] = review
            continue
        # physical edges and sites from the traced chain(s)
        phys, sites, openings = [], [], []
        for chain in chains:
            for e in chain:
                if e["KIND"] == "SITE_CHORD":
                    src = edges_by_id.get(e["SOURCE_EDGE_ID"], {})
                    s = sites_by_id.get(src.get("OPENING_SITE_ID"), {})
                    st = SITE_TYPE_MAP.get(s.get("CLASS"))
                    if st is None:
                        phys.append({"EDGE_ID": e["EDGE_ID"], "KIND": "UNRESOLVED_EDGE", "length_m": e.get("length_m"), "length_source": "SITE_CHORD_UNMAPPED", "a": e["a"], "b": e["b"], "trace_ids": []})
                        continue
                    sid = f"{s['SITE_ID']}@{c['CELL_ID']}" if s.get("SITE_ID") in {x["SITE_ID"] for x in sites} else s.get("SITE_ID")
                    sites.append({"SITE_ID": sid or e["EDGE_ID"], "SITE_TYPE": st, "termination_a": e["a"], "termination_b": e["b"], "span_m": round((s.get("GAP_SPAN_MM") or 0) / 1000, 4),
                                  "evidence": s.get("WHY"), "trace_ids": [s.get("FACE_A"), s.get("FACE_B")]})
                    if st in ("CONFIRMED_DOOR_OPENING", "CONFIRMED_WINDOW_OPENING"):
                        openings.append({"OPENING_ID": f"OP-{sid}", "TYPE": "DOOR" if st == "CONFIRMED_DOOR_OPENING" else "WINDOW", "HOSTED_IN": s.get("HOST_WALL_ID"),
                                         "width_m": round((s.get("GAP_SPAN_MM") or 0) / 1000, 4), "width_source": "DRAWING_CAD_GEOMETRY", "height_m": None, "height_source": None,
                                         "trace_ids": [s.get("FACE_A"), s.get("FACE_B")]})
                else:
                    phys.append({"EDGE_ID": e["EDGE_ID"], "KIND": e["KIND"], "length_m": e.get("length_m"), "length_source": e.get("length_source"), "a": e["a"], "b": e["b"],
                                 "trace_ids": e.get("trace_ids", [])})
        for trade in trades:
            treatment, basis = TRADES[trade]
            if trade == "WET_ROOM_SPLATTER" and not any(z[0] in WET for z in (sem or {}).get("ZONES", [])):
                continue
            if trade == "COLUMN_BONDING" and not any(p["KIND"] == "EXPOSED_COLUMN_FACE" for p in phys):
                continue
            rid = ids.make_id("TRADE_ZONE", c["CELL_ID"], trade)
            phys_t = [p for p in phys if p["KIND"] == "EXPOSED_COLUMN_FACE"] if trade == "COLUMN_BONDING" else phys
            sites_t, openings_t = ([], []) if trade == "COLUMN_BONDING" else (sites, openings)
            region = QMR.build_region(region_id=rid, physical_edges=phys_t, sites=sites_t, openings=openings_t, trade=treatment, basis=basis)
            region["TRADE_MEASUREMENT_REGION_ID"] = rid; region["CELL_ID"] = c["CELL_ID"]; region["PHYSICAL_SPACE_ID"] = c.get("PHYSICAL_SPACE_ID"); region["TRADE"] = trade
            region["CLOSURE_STAMP"] = QMR.CLOSURE_CONSTANTS
            region_rows.append(region)
            # height + engine sheet
            H, H_src, pid, why = _height_for_cell(sem, storey, reg, trade)
            local_reg = dict(reg)
            local_reg["APPLICABLE_PLASTER_HEIGHT"] = {"VALUE": H, "SOURCE_TYPE": H_src, "PARAMETER_ID": pid, "WHY": why}
            if not unit_status_ok:
                local_reg["APPLICABLE_PLASTER_HEIGHT"] = {"VALUE": None, "SOURCE_TYPE": "UNKNOWN", "WHY": "source unit not established: no physical length may be consumed"}
            sheet = PTE.calculate(region, local_reg, treatment=treatment)
            gross = region.get("GROSS_BASIS", {})
            contributing = gross.get("CONTRIBUTING_EDGES", []) if isinstance(gross, dict) else []
            lm = round(sum(x["length_m"] for x in contributing if isinstance(x.get("length_m"), (int, float))), 4) if contributing else None
            qstate = sheet.get("QUANTITY_STATE")
            if isinstance(qstate, dict):
                qstate = qstate.get("PRINCIPAL_WALL_FACE")
            qstate = qstate or "NOT_ESTABLISHED"
            canonical = STS.adapt(qstate, "quantity_state")
            principal = next((l.get("AREA_M2") for l in sheet.get("SHEET", []) if l.get("LINE") == "PRINCIPAL_WALL_FACE"), None)
            if not unit_status_ok:
                canonical, principal, lm = "SOURCE_REQUIRED", None, None
            trace.append({"LINE_ID": ids.make_id("TRADE_ZONE", rid, "LINE"), "CELL_ID": c["CELL_ID"], "PHYSICAL_SPACE_ID": c.get("PHYSICAL_SPACE_ID"), "STOREY": storey, "TRADE": trade, "TREATMENT": treatment,
                          "MEASUREMENT_BASIS": basis, "REGION_STATUS": region["MEASUREMENT_REGION_STATUS"], "REGION_REASONS": region.get("NOT_ESTABLISHED_BECAUSE"),
                          "LENGTH_GEOMETRY": {"EDGE_IDS": [x["EDGE_ID"] for x in contributing], "VECTOR_LM": lm, "LENGTH_SOURCE": "DRAWING_CAD_GEOMETRY"},
                          "HEIGHT_SOURCE": {"PARAMETER_ID": pid, "VALUE_M": H, "SOURCE_TYPE": H_src, "WHY": why},
                          "OPENING_DEDUCTION_SOURCE": [{"OPENING_ID": o["OPENING_ID"], "WIDTH_M": o["width_m"], "WIDTH_SOURCE": o["width_source"], "HEIGHT_SOURCE": "PARAMETER_OR_SOURCE_REQUIRED"} for o in openings],
                          "TRADE_RULE": {"ENGINE": "engine.plaster_trade_engine", "REGION_RULE": QMR.RULE_VERSION, "TREATMENT": treatment},
                          "SEMANTIC_IDENTITY": sem, "AREA_M2_PRINCIPAL": principal, "QUANTITY_STATE_ENGINE": qstate, "QUANTITY_STATUS": canonical,
                          "STATUS_DIMENSIONS": STS.record(IDENTITY_STATUS=("SOURCE_ESTABLISHED" if (sem or {}).get("STATUS") == "SINGLE" else "NOT_ESTABLISHED"),
                                                          GEOMETRY_STATUS="SOURCE_ESTABLISHED" if unit_status_ok else "SOURCE_REQUIRED",
                                                          TOPOLOGY_STATUS="SOURCE_ESTABLISHED" if region["MEASUREMENT_REGION_STATUS"] in ("MEASUREMENT_REGION_CLOSED", "MEASUREMENT_RUN_ESTABLISHED") else "NOT_ESTABLISHED",
                                                          MEASUREMENT_STATUS="SOURCE_ESTABLISHED" if lm is not None else "NOT_ESTABLISHED", QUANTITY_STATUS=canonical),
                          "PROVENANCE": {"REGISTERS": ["PA06_SPACE_BOUNDARY_FACE_REGISTER", "PA06_TOPOLOGICAL_SITE_REGISTER", "PA06_SEMANTIC_ANCHOR_REGISTER", "PA06_STOREY_REGISTER"], "OWNER_REGISTRY": reg.get("_REGISTRY_ID")},
                          "ENGINE_SHEET": sheet, "BARE_NUMBER": False})
    # floor / ceiling area lines (raster cell area; provisional by construction)
    for c in cells:
        if not c["IN_RANGE"] or not c.get("QUANTITY_ELIGIBLE", c["IN_RANGE"]):
            continue
        sem = c.get("SEMANTIC_IDENTITY") or {}
        if c.get("REVIEW_FLAGS"):
            continue
        void_like = any(z[0] in ("VOID", "STAIR", "ELEVATOR") for z in sem.get("ZONES", []))
        zones = [z[0] for z in sem.get("ZONES", [])]
        identified = sem.get("STATUS") in ("SINGLE", "MULTIPLE") and zones and all(z in INTERIOR_CLASSES_FOR_AREA for z in zones)
        for trade in ("FLOOR_AREA", "CEILING_AREA"):
            state = "PROVISIONAL" if (identified and (trade == "FLOOR_AREA" or not void_like)) else "NOT_ESTABLISHED"
            if not unit_status_ok:
                state = "SOURCE_REQUIRED"
            trace.append({"LINE_ID": ids.make_id("TRADE_ZONE", c["CELL_ID"], trade, "LINE"), "CELL_ID": c["CELL_ID"], "PHYSICAL_SPACE_ID": c.get("PHYSICAL_SPACE_ID"), "STOREY": storey_of_cell.get(c["CELL_ID"]),
                          "TRADE": trade, "TREATMENT": trade, "MEASUREMENT_BASIS": "RASTER_CELL_AREA_50MM", "REGION_STATUS": "CELL_CLOSED_BY_FLOOD",
                          "LENGTH_GEOMETRY": None, "HEIGHT_SOURCE": None, "OPENING_DEDUCTION_SOURCE": [], "TRADE_RULE": {"ENGINE": "engine.ingest.spaces_v2", "NOTE": "cell area from the closed flood mask; a polygon area would need a vector ring"},
                          "SEMANTIC_IDENTITY": sem, "AREA_M2_PRINCIPAL": c["AREA_M2"] if state == "PROVISIONAL" else None, "QUANTITY_STATE_ENGINE": None, "QUANTITY_STATUS": state,
                          "STATUS_DIMENSIONS": STS.record(GEOMETRY_STATUS="PROVISIONAL", TOPOLOGY_STATUS="SOURCE_ESTABLISHED", MEASUREMENT_STATUS="PROVISIONAL", QUANTITY_STATUS=state),
                          "PROVENANCE": {"REGISTERS": ["PA06_PHYSICAL_SPACE_REGISTER"]}, "ENGINE_SHEET": None, "BARE_NUMBER": False,
                          "NOTE": "area lines carry a value only for a cell whose identity is an established interior room class; unlabelled loops, exterior classes and void / stair / shaft cells stay NOT_ESTABLISHED"})
    counts = Counter(t["QUANTITY_STATUS"] for t in trace)
    return {"ARTIFACT": "PA06_TRADE_MEASUREMENT_REGION_REGISTER", "ROWS": region_rows, "COUNT": len(region_rows),
            "REVERSIBILITY": {"ALL_REVERSIBLE": all(r["INVARIANTS"]["REVERSIBLE"] for r in region_rows) if region_rows else None,
                              "ALL_ZERO_MATERIAL": all(r["INVARIANTS"]["ZERO_MATERIAL_CONTRIBUTION"] for r in region_rows) if region_rows else None,
                              "FORMED": sum(1 for r in region_rows if r["MEASUREMENT_REGION_STATUS"] != "MEASUREMENT_REGION_NOT_ESTABLISHED"), "NOT_FORMED": sum(1 for r in region_rows if r["MEASUREMENT_REGION_STATUS"] == "MEASUREMENT_REGION_NOT_ESTABLISHED")},
            "CLOSURE_CONSTANTS": QMR.CLOSURE_CONSTANTS}, \
           {"ARTIFACT": "PA06_QUANTITY_INPUT_TRACE", "LINES": trace, "COUNT": len(trace), "BY_STATUS": dict(counts), "TOTALS": None,
            "RULE": "no total: every line is an input trace with its own state; a total across states or units is refused by design"}
