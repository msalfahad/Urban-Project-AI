"""DRAWING DISCOVERY AND ADMISSION (M9 S6) - what a drawing holds and whether it may be measured, BEFORE any quantity.

    new_report(documents)                          a URBAN_DRAWING_DISCOVERY_V1 report, every stage NOT_RUN
    finding(level, code, message, **evidence)      one finding (FATAL / BLOCKED_ITEM / REVIEW_REQUIRED / WARNING)
    set_stage(report, stage, findings, **data)     a stage's findings + state (worst finding decides)
    inventory_findings(census, k2, accepted_xrefs) stage 1 from a source census (plain data)
    unit_findings(declared_m, inferred, override)  stage 4
    legacy_tolerance_findings(unit_m)              stage 4, V1 strict only: a unit too coarse for V1's 1-unit tolerances
    region_findings(regions, ...)                  stages 2 and 5
    gate(report)                                   the admission decision: stopping findings, counts, exit code

The rule (schema research/urban_m9_s6/S6_02_DRAWING_DISCOVERY_SCHEMA.json): a FATAL finding anywhere, or a
BLOCKED_ITEM in the admission stages 0-5, stops the run - no BOQ is published, the report and the reason are; a
BLOCKED_ITEM in a later stage blocks only the items it names; REVIEW_REQUIRED and WARNING findings travel with the BOQ
as flags. A reviewer input (declared units, a plan region, an accepted missing XREF) is recorded in the report, never
silently applied. Nothing here infers a quantity, a height, a finish or a material. Project-agnostic; stdlib only.
"""

from __future__ import annotations

SCHEMA = "URBAN_DRAWING_DISCOVERY_V1"
POLICY_ID = "DRAWING_DISCOVERY_V1"
FATAL, BLOCKED_ITEM, REVIEW, WARNING = "FATAL", "BLOCKED_ITEM", "REVIEW_REQUIRED", "WARNING"
LEVELS = (FATAL, BLOCKED_ITEM, REVIEW, WARNING)
STAGES = ("0_intake", "1_inventory", "2_sheets", "3_identity", "4_units", "5_floors", "6_geometry_readiness",
          "7_vertical_model", "8_features", "9_finish_zones", "10_boq_readiness")
ADMISSION_STAGES = STAGES[:6]
EXIT_ADMISSION_BLOCKED = 2          # a fatal admission finding: nothing is measured, no BOQ is published
EXIT_COMPLETENESS_FAILED = 3        # measured, but a surface or category has no line / exclusion / RFI: not published
# entity kinds the architectural route turns into geometry, and how (S6 audit, S6_03_SOURCE_ENTITY_CENSUS.md)
ARCH_SUPPORT = {"LINE": "READ", "LWPOLYLINE": "READ", "ARC": "READ", "CIRCLE": "READ", "ELLIPSE": "READ_AS_CHORDS",
                "SPLINE": "READ_AS_CHORDS", "POLYLINE": "READ_2D_ONLY", "MLINE": "READ", "INSERT": "READ_NESTED",
                "HATCH": "READ_ONE_BLOCK_LEVEL", "TEXT": "READ", "MTEXT": "READ", "ATTRIB": "READ", "ATTDEF": "TEMPLATE",
                "SOLID": "CARRIED_NOT_GEOMETRY", "VIEWPORT": "LAYOUT_OBJECT", "POINT": "NOT_READ",
                "DIMENSION": "NOT_READ", "LEADER": "NOT_READ", "MLEADER": "NOT_READ", "RTEXT": "NOT_READ",
                "WIPEOUT": "NOT_READ", "IMAGE": "NOT_READ", "OLE2FRAME": "NOT_READ", "ACAD_PROXY_ENTITY": "NOT_READ",
                "3DFACE": "NOT_READ", "TRACE": "NOT_READ", "ACAD_TABLE": "NOT_READ", "REGION": "NOT_READ",
                "3DSOLID": "NOT_READ", "MESH": "NOT_READ", "BODY": "NOT_READ", "SURFACE": "NOT_READ"}
SILENT_KINDS = ("READ", "READ_AS_CHORDS", "READ_2D_ONLY", "READ_NESTED", "TEMPLATE", "LAYOUT_OBJECT")
GEOMETRY_KINDS = ("LINE", "LWPOLYLINE", "POLYLINE", "ARC", "CIRCLE", "ELLIPSE", "SPLINE", "HATCH", "SOLID", "INSERT",
                  "MLINE")


class AdmissionBlocked(Exception):
    """the run stops at admission; `report` carries every finding and the reviewer inputs that could resolve it."""

    def __init__(self, report):
        super().__init__("; ".join(f"{f['code']}: {f['message']}" for f in stops(report))[:2000])
        self.report = report


def finding(level, code, message, **evidence):
    if level not in LEVELS:
        raise ValueError(f"finding level must be one of {LEVELS}")
    return {"level": level, "code": code, "message": message, "evidence": evidence}


def new_report(documents, *, method=None, reviewer_inputs=None):
    return {"schema": SCHEMA, "policy": POLICY_ID, "method": method, "documents": list(documents),
            "reviewer_inputs": dict(reviewer_inputs or {}),
            "stages": {s: {"state": "NOT_RUN", "findings": []} for s in STAGES}, "gates": {}}


def _state(findings, default="PASSED"):
    lv = {f["level"] for f in findings}
    if FATAL in lv:
        return "FAILED"
    if BLOCKED_ITEM in lv:
        return "BLOCKED"
    if REVIEW in lv or WARNING in lv:
        return "PROVISIONAL"
    return default


def set_stage(report, stage, findings, *, state=None, **data):
    if stage not in STAGES:
        raise ValueError(f"unknown stage {stage}")
    report["stages"][stage] = {"state": state or _state(findings), "findings": list(findings), **data}
    return report["stages"][stage]


def all_findings(report):
    return [dict(f, stage=s) for s in STAGES for f in report["stages"][s]["findings"]]


def stops(report):
    return [f for f in all_findings(report)
            if f["level"] == FATAL or (f["level"] == BLOCKED_ITEM and f["stage"] in ADMISSION_STAGES)]


def gate(report):
    fs = all_findings(report)
    st = stops(report)
    report["gates"] = {"fatal": sum(1 for f in fs if f["level"] == FATAL),
                       "blocked_items": sum(1 for f in fs if f["level"] == BLOCKED_ITEM),
                       "review_required": sum(1 for f in fs if f["level"] == REVIEW),
                       "warnings": sum(1 for f in fs if f["level"] == WARNING),
                       "architectural_boq_may_run": not st,
                       "stopping": [f"{f['stage']}:{f['code']}" for f in st],
                       "exit_code": EXIT_ADMISSION_BLOCKED if st else 0,
                       "rule": "FATAL anywhere, or a BLOCKED_ITEM in stages 0-5, stops the run (no BOQ is published; "
                               "exit 2); a BLOCKED_ITEM in a later stage blocks the items it names; REVIEW_REQUIRED and "
                               "WARNING findings travel with the BOQ as flags"}
    return report["gates"]


# ====================================================================== stage rules on plain data
def inventory_findings(census, k2=None, *, accepted_xrefs=()):
    """census (tools.arch_discovery.census): layouts, blocks, xrefs, minserts, nesting, hidden layers, hatches in
    nested blocks, entity kinds; k2: {"missing_top_level": [...], "dispositions": {...}} from the K2 kernel."""
    out = []
    model = next(x for x in census["layouts"] if x["kind"] == "MODEL")
    n_geo = sum(v for k, v in model["entities_by_type"].items() if k in GEOMETRY_KINDS)
    if n_geo == 0:
        out.append(finding(FATAL, "EMPTY_MODEL_SPACE", "model space holds no geometry: there is nothing to measure",
                           entities=model["entities_by_type"]))
    for p in (x for x in census["layouts"] if x["kind"] == "PAPER"):
        n = sum(v for k, v in p["entities_by_type"].items() if k != "VIEWPORT")
        if n:
            out.append(finding(REVIEW, "PAPER_SPACE_CONTENT",
                               f"layout '{p['name']}' holds {n} entities: frames, titles or notes there are not read by "
                               "the plan reader (a plan shown only through a viewport is not measured)",
                               layout=p["name"], entities=p["entities_by_type"], viewports=p["viewports"]))
    acc = set(accepted_xrefs or ())
    for x in census["xrefs"]:
        if not x["inserted"]:
            continue
        if x["block"] in acc:
            out.append(finding(REVIEW, "XREF_ACCEPTED_MISSING", f"external reference {x['block']} -> {x['path']} is not "
                               "read; a reviewer accepted measuring without it (recorded)", **x))
        else:
            out.append(finding(BLOCKED_ITEM, "XREF_NOT_SUPPLIED",
                               f"external reference {x['block']} -> {x['path']} is inserted but not read: what it draws "
                               "is missing from the regions it covers (bind it in CAD, or accept it explicitly with "
                               "--accept-missing-xref)", **x))
    if census["minserts"]:
        out.append(finding(WARNING, "MINSERT_PRESENT", f"{census['minserts']} MINSERT(s): the architectural hatch and "
                           "insert readers read the first cell only (the K2 line reader expands every cell)",
                           count=census["minserts"]))
    if census.get("hatches_below_first_level"):
        out.append(finding(WARNING, "HATCH_IN_NESTED_BLOCK",
                           f"{census['hatches_below_first_level']} hatch(es) inside blocks nested 2+ levels deep are not "
                           "read by the architectural hatch reader (column fills, finish hatches)",
                           count=census["hatches_below_first_level"]))
    for h in census["hidden_layers"]:
        out.append(finding(REVIEW, "HIDDEN_LAYER_CONTENT",
                           f"layer {h['layer']} is {'frozen' if h['frozen'] else 'off'} and holds {h['entities']} "
                           "entities; the readers do not read layer state, so they are measured as if visible", **h))
    for kind, n in sorted(census["kinds"].items()):
        sup = ARCH_SUPPORT.get(kind, "UNKNOWN_KIND")
        if sup not in SILENT_KINDS:
            out.append(finding(WARNING, "ENTITY_KIND_NOT_MEASURED", f"{n} {kind}: {sup}", kind=kind, count=n,
                               support=sup))
    if k2 is not None and k2.get("missing_top_level"):
        out.append(finding(FATAL, "ENTITY_DISPOSITION_MISSING",
                           f"{len(k2['missing_top_level'])} model-space entities have no reader disposition "
                           "(realised / carried / hidden / finding): a reader dropped them without saying so",
                           handles=k2["missing_top_level"][:50]))
    return out


def unit_findings(declared_m, inferred, override_m=None, override_name=None):
    """inferred: drawing_model.infer_units on all closed rectangles (member-sized outlines under each unit)."""
    out = []
    if override_m is not None:
        out.append(finding(REVIEW, "UNITS_DECLARED_BY_REVIEWER", f"units {override_name} ({override_m} m per drawing "
                           "unit) given by a reviewer (--units); recorded", declared_m=declared_m,
                           inferred_m=inferred.get("unit_m"), member_fit=inferred.get("member_fit")))
        return out
    if declared_m is None:
        out.append(finding(BLOCKED_ITEM, "UNITS_NOT_DECLARED",
                           f"$INSUNITS declares no unit; the drawn geometry suggests {inferred.get('unit_m')} m per unit "
                           "- a reviewer must confirm it (--units mm|cm|m|in) before anything is measured",
                           member_fit=inferred.get("member_fit")))
    elif inferred.get("warning"):
        out.append(finding(BLOCKED_ITEM, "UNITS_CONTRADICTED", inferred["warning"] + " - confirm the unit with --units",
                           declared_m=declared_m, member_fit=inferred.get("member_fit")))
    return out


LEGACY_GAP_KEEP_M = 0.03           # the jamb tolerance of the opening census: a smaller gap must stay open


def legacy_tolerance_findings(unit_m):
    """ARCH_TAKEOFF_V1 behind --strict-admission: its two geometry tolerances are 1.0 drawing unit (S6 defect); a
    unit coarser than the gap the opening census must keep (LEGACY_GAP_KEEP_M) closes door gaps, drops column outlines
    and merges rooms, so V1 must not measure it (ARCH_TAKEOFF_V2 uses unit-relative tolerances)."""
    if unit_m is None or unit_m <= LEGACY_GAP_KEEP_M:
        return []
    return [finding(BLOCKED_ITEM, "LEGACY_TOLERANCE_TOO_COARSE",
                    f"ARCH_TAKEOFF_V1 closes every gap under 1 drawing unit = {unit_m} m, above the {LEGACY_GAP_KEEP_M} m "
                    "an opening jamb needs: doors, columns and rooms would be lost - measure with ARCH_TAKEOFF_V2",
                    unit_m=unit_m, gap_keep_m=LEGACY_GAP_KEEP_M)]


def region_findings(regions, *, other_frames=(), blocked_frames=(), unassigned=(), crossings=None, titles_found=0,
                    titles_in_frames=0, paper_space_content=False, frames_from_lines=False, overrides=False):
    """stages 2 (sheets) and 5 (floors)."""
    sheets, floors = [], []
    if frames_from_lines:
        sheets.append(finding(REVIEW, "FRAME_DRAWN_AS_LINES", "no sheet frame is a closed polyline; the frames drawn as "
                              "separate lines were used"))
    for o in other_frames:
        sheets.append(finding(WARNING, "FRAME_NOT_A_FLOOR_PLAN", f"frame {o['sheet_id']}: {o['why']}",
                              sheet_id=o["sheet_id"], titles_seen=o.get("titles_seen")))
    for b in blocked_frames:
        floors.append(finding(BLOCKED_ITEM, "REGION_CUT_CROSSES_GEOMETRY", b["why"], sheet_id=b["sheet_id"],
                              titles=b.get("titles")))
    for sid, n in sorted((crossings or {}).items()):
        if n:
            floors.append(finding(BLOCKED_ITEM, "REGION_CUT_CROSSES_GEOMETRY",
                                  f"frame {sid} is divided between its floor titles and {n} drawn segment(s) cross the "
                                  "cut: a plan would be measured in pieces or on the wrong floor", sheet_id=sid,
                                  crossing_segments=n))
    for u in unassigned:
        floors.append(finding(REVIEW, "GEOMETRY_OUTSIDE_EVERY_PLAN", f"frame {u['sheet_id']}: {u['segments']} drawn "
                              "segment(s) in a part of the frame with no floor-plan title are not measured",
                              **{k: u[k] for k in ("sheet_id", "box", "segments")}))
    if overrides:
        floors.append(finding(REVIEW, "PLAN_REGIONS_FROM_REVIEWER", "the plan regions were given by a reviewer "
                              "(--region); recorded", regions=[r["region_id"] for r in regions]))
    if not regions:
        if paper_space_content and not titles_in_frames:
            floors.append(finding(FATAL, "PAPER_SPACE_SHEETS", "no model-space frame holds a floor-plan title while a "
                                  "paper-space layout holds content: the sheets are on layouts, which the plan reader "
                                  "does not read (give the regions with --region, or export the plans to model space)"))
        if titles_found and not titles_in_frames:
            floors.append(finding(FATAL, "PLAN_TITLES_OUTSIDE_ANY_FRAME", f"{titles_found} floor-plan title(s) found, "
                                  "none inside a sheet frame: no plan region can be formed (--region)"))
        if not titles_found:
            floors.append(finding(FATAL, "NO_FLOOR_PLAN_TITLE", "no text reads as a floor-plan title (GROUND FLOOR "
                                  "PLAN, 1ST FLOOR PLAN, ... or the Arabic equivalents): no floor can be identified"))
        floors.append(finding(FATAL, "NO_PLAN_REGION", "no floor-plan region: the architectural BOQ must not run"))
    dup = {}
    for r in regions:
        dup[r["floor"]] = dup.get(r["floor"], 0) + 1
    for fl, n in sorted(dup.items()):
        if n > 1:
            floors.append(finding(REVIEW, "FLOOR_TITLE_REPEATED", f"{n} plans titled {fl}", floor=fl))
    return sheets, floors


def policy_record():
    return {"policy_id": POLICY_ID, "schema": SCHEMA, "levels": list(LEVELS), "stages": list(STAGES),
            "admission_stages": list(ADMISSION_STAGES), "exit_codes": {"ADMISSION_BLOCKED": EXIT_ADMISSION_BLOCKED,
                                                                       "COMPLETENESS_FAILED": EXIT_COMPLETENESS_FAILED},
            "arch_support": ARCH_SUPPORT,
            "never": ["a quantity, height, finish or material inferred at admission",
                      "a reviewer input applied without being recorded",
                      "a BOQ published after a stopping finding"]}
