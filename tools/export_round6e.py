"""Export round 6E: the bundle an auditor can reproduce.

§21. Nineteen tables in CSV and JSON, a report, and a manifest whose
provenance block answers the two questions the audit of the 6C and 6D
bundles could not:

    WAS THIS BUILT FROM COMMITTED CODE   SOURCE_COMMIT, GIT_TREE_HASH,
                                         WORKTREE_STATUS=CLEAN, and the
                                         test run that passed first
    IS THIS FILE WHAT THAT COMMIT MAKES  RAW_FILE_SHA256 per file, and
                                         CANONICAL_CONTENT_SHA256 beside
                                         it, which survives re-indenting
                                         and answers the other question

The tables:

    SPACE_REGISTER            one row per candidate, with BOTH ids
    RELEASE_STATE             the one authoritative state, and why
    SPACE_LINEAGE             what happened to each space in this round
    LINEAGE_HISTORY           what happened between 6C and 6D
    STABLE_SPACE_INDEX        stable id <-> run candidate id, per round
    DRAWING_REGION_ROLE       what each region of the sheet is
    FLOOR_ASSIGNMENT          which floor each region draws
    FUNCTIONAL_ZONE           a zone creates no wall and no quantity
    PANTRY_ANALYSIS           openness, host walls, what is not known
    PHYSICAL_STAIR            one row per STAIRCASE
    STAIR_PLAN_INSTANCE       one row per drawing OF a staircase
    STAIR_FLIGHT              one row per flight
    STAIR_TREAD               one row per tread, from its own polygon
    STAIR_RISER               one row per riser, NOT ESTABLISHED
    STAIR_PIECE_BETWEEN_FLIGHTS  landing, void, plate or circulation
    STAIR_OBSERVATION         every stair-like thing the drawing shows
    STAIR_QUANTITY            each figure in its own unit, never summed
    VERTICAL_EVIDENCE         the search for a rise, and its refusal
    EXCEPTIONS                every refusal anywhere in the run

and beside them the two the owner rule addendum adds — RULE_LIBRARY, the
versioned owner rules as applied, and ELEVATOR_MARBLE, the declared
landing objects and the questions they still carry — and the six carried
from round 6D: FITTING_BAND, WALL_STRETCH_OWNERSHIP, BOUNDARY, OPENING,
IDENTITY, DIMENSION.
"""

from __future__ import annotations

import argparse
import json
import tarfile
from pathlib import Path

from engine import elevator_marble as elev
from engine import export_provenance as xp
from engine import fitting_band as fband
from engine import functional_zone as fz
from engine import physical_wall as pwall
from engine import report_consistency as rcons
from engine import round6e_selftest as r6e
from engine import rule_library as rlib
from engine import single_line_partition as slp
from engine import space_lineage as slin
from engine import space_register as sreg
from engine import stair_assembly as stair
from engine import vertical_evidence as ve
from engine import wall_face_ownership as wface
from tools import export_round6b as x6b
from tools import export_round6c as x6c
from tools import export_round6d as x6d
from tools import run_round6c as r6c
from tools import run_round6e as r6er

EXPORT = "P7757_ROUND6E_EXPORT_V1"
NAMED = 19


def register_rows(register, rows, stable_of) -> list:
    """§4. BOTH ids on every row, and never one pretending to be both."""
    out = []
    for row in x6c.register_rows(register, rows):
        run_id = row["physical_space_id"]
        out.insert(len(out), dict(
            {"stable_physical_space_id": stable_of.get(run_id, ""),
             "run_candidate_id": run_id}, **row))
    return out


def release_rows(register) -> list:
    return [{
        "physical_space_id": e.space_id,
        "drawing_region_id": e.region_id,
        "floor": e.floor_level,
        "candidate_role": e.candidate_role,
        "is_physical_space": e.is_space,
        "may_release": e.may_release,
        "geometry_gate_status": e.geometry_gate_status,
        "RELEASE_STATUS": e.release_status,
        "withheld_because": " ".join(e.withheld_because),
        "area_m2": round(e.area_m2, 4),
    } for e in register.entries]


def lineage_rows(rep) -> list:
    return [x.record() for x in rep.links] + [
        dict(r, run_candidate_id="", stable_space_id=r["stable_space_id"])
        for r in rep.removed]


def stable_index_rows(chain, rep) -> list:
    out = []
    for step in chain["steps"]:
        for link in step["report"].links:
            out.append({"round": step["to"],
                        "stable_space_id": link.stable_space_id,
                        "run_candidate_id": link.run_candidate_id,
                        "lineage": link.lineage,
                        "predecessors": " ".join(link.predecessor_ids)})
    for link in rep.links:
        out.append({"round": "ROUND_6E",
                    "stable_space_id": link.stable_space_id,
                    "run_candidate_id": link.run_candidate_id,
                    "lineage": link.lineage,
                    "predecessors": " ".join(link.predecessor_ids)})
    return out


def physical_stair_rows(stairs) -> list:
    out = []
    for x in stairs["physical_stairs"]:
        rec = x.record()
        net = rec.pop("MEASURED_NET")
        rec["plan_instances"] = " ".join(
            f"{p['drawing_region_id']}:{p['stair_id']}"
            for p in rec.pop("plan_instances"))
        rec.update({f"NET_{k}": v for k, v in net.items()
                    if k != "this_is"})
        rec["floors_it_is_drawn_on"] = " ".join(
            rec.pop("floors_it_is_drawn_on"))
        rec["role_evidence"] = " ".join(rec.pop("role_evidence"))
        rec["exceptions"] = " ".join(rec.pop("exceptions"))
        out.append(rec)
    return out


def observation_rows(rep, coverage) -> list:
    out = []
    floor_of = {r["floor"]: r for r in coverage["per_floor"]}
    region_floor = {}
    for row in coverage["per_floor"]:
        for region in row["drawing_regions"]:
            region_floor[region] = row["floor"]
    for s in rep.stairs:
        for o in s.observations:
            rec = o.record()
            rec["floor"] = region_floor.get(o.region_id, "")
            rec["covers_m2"] = round(stair._extent_m2(o), 4)
            rec["evidence"] = " ".join(rec.pop("evidence"))
            rec["at_mm"] = " ".join(str(v) for v in rec.pop("at_mm"))
            rec["extent_mm"] = " ".join(str(v)
                                        for v in rec.pop("extent_mm"))
            out.append(rec)
    return out


def coverage_rows(coverage) -> list:
    out = []
    for row in coverage["per_floor"]:
        rec = {k: v for k, v in row.items()
               if k != "unresolved_observations"}
        rec["drawing_regions"] = " ".join(rec.pop("drawing_regions"))
        rec["exceptions"] = " ".join(rec.pop("exceptions"))
        rec["unresolved_listed"] = len(row["unresolved_observations"])
        out.append(rec)
    return out


def quantity_rows(quantities) -> list:
    out = []
    for row in quantities["rows"]:
        rec = {"physical_stair_id": row["physical_stair_id"],
               "stair_role": row["stair_role"],
               "finish": row["finish"],
               "configuration": row["configuration"],
               "floor_from": row["floor_from"],
               "floor_to": row["floor_to"]}
        for key, val in row.items():
            if isinstance(val, dict) and "unit" in val:
                rec[f"{key}_value"] = val["value"]
                rec[f"{key}_unit"] = val["unit"]
                rec[f"{key}_status"] = val["status"]
        rec["exceptions"] = " ".join(row["exceptions"])
        out.append(rec)
    return out


def rule_rows(library, project) -> list:
    """Every owner rule that was available to this run, as applied."""
    out = []
    for rule in sorted(library.rules.values(), key=lambda r: r.rule_id):
        rec = rule.record()
        rec["required_geometry"] = " | ".join(rec.pop("required_geometry"))
        rec["exceptions"] = " | ".join(rec.pop("exceptions"))
        rec["rule_hash"] = rule.rule_hash()
        rec["project_override_in_this_run"] = json.dumps(
            {k: v for k, v in (project or {}).items()
             if isinstance(v, dict)
             and rule.scope.lower() in k.lower()},
            ensure_ascii=False, sort_keys=True)
        out.append(rec)
    return out


def elevator_rows(elevators) -> list:
    """The declared elevator objects, and what each one still needs."""
    out = []
    for st in elevators.get("stations", ()):
        sur, thr = st["surround"], st["threshold"]
        out.append({
            "elevator_station_id": st["elevator_station_id"],
            "elevator_id": st["elevator_id"],
            "floor": st["floor"],
            "door_index": st["door_index"],
            "door_clear_width_mm": sur["door_clear_width_mm"],
            "door_clear_height_mm": sur["door_clear_height_mm"],
            "left_surround_width_mm": sur["left_surround_width_mm"],
            "top_surround_width_mm": sur["top_surround_width_mm"],
            "right_surround_width_mm": sur["right_surround_width_mm"],
            "surround_width_source": sur["surround_width_source"],
            "ELEVATOR_SURROUND_AREA_M2": sur["ELEVATOR_SURROUND_AREA_M2"],
            "ELEVATOR_SURROUND_EDGE_LM": sur["ELEVATOR_SURROUND_EDGE_LM"],
            "surround_status": sur["status"],
            "threshold_width_mm": thr["threshold_width_mm"],
            "threshold_depth_mm": thr["threshold_depth_mm"],
            "ELEVATOR_THRESHOLD_AREA_M2": thr[
                "ELEVATOR_THRESHOLD_AREA_M2"],
            "threshold_status": thr["status"],
            "measurement_basis": sur["measurement_basis"],
            "exceptions": " ".join(st["exceptions"]),
        })
    for ex in elevators.get("exceptions", ()):
        out.append({"elevator_station_id": ex.get("exact_term", ""),
                    "surround_status": ex.get("exception", ""),
                    "exceptions": ex.get("question_for_the_owner", "")})
    return out


def vertical_rows(vertical) -> list:
    return list(vertical.get("findings", []))


def piece_rows(rep) -> list:
    out = []
    for s in rep.stairs:
        for a in s.assemblies:
            for x in a.landings:
                rec = x.record()
                rec["stair_id"] = a.stair_id
                rec["drawing_region_id"] = a.region_id
                rec["role_evidence"] = " ".join(rec.pop("role_evidence"))
                out.append(rec)
    return out


def exception_rows(rep, register, roles, zones, report, lrep, coverage):
    out = x6d.exception_rows(rep, register, roles, zones, {
        "C_register_changes_since_round_6c": {
            "false_negative_candidates": r6c._false_negative_analysis(
                report["_rows"], register)}})
    for link in lrep.links:
        if link.lineage == slin.UNRESOLVED_LINEAGE:
            out.append({"exception": slin.UNRESOLVED_LINEAGE,
                        "subject": link.run_candidate_id,
                        "drawing_region_id": link.region_id,
                        "floor": link.floor_level,
                        "reason": link.reason,
                        "what_was_refused": "a stable physical-space id"})
    for row in coverage["per_floor"]:
        if row["coverage"] in (stair.COVERAGE_FAILED,
                               stair.COVERAGE_INCOMPLETE):
            out.append({"exception": row["coverage"],
                        "subject": f"FLOOR {row['floor']}",
                        "drawing_region_id": " ".join(
                            row["drawing_regions"]),
                        "floor": row["floor"], "reason": row["why"],
                        "what_was_refused": "a complete stair coverage"})
    return out


def _metrics(report, tables) -> dict:
    """§7. Every headline number, recomputed from the rows written."""
    areas = report["B_register"]["round_6e"]
    stairs = report["C_stairs"]
    quantities = stairs["quantities"]["totals"]
    checks = [
        ("RELEASE_ELIGIBLE_GEOMETRY", "P7757_ROUND6E_RELEASE_STATE",
         areas["RELEASE_ELIGIBLE_GEOMETRY"],
         {"where": {"RELEASE_STATUS": sreg.RELEASED}, "op": "count"}),
        ("RELEASE_ELIGIBLE_GEOMETRY_AREA_M2",
         "P7757_ROUND6E_RELEASE_STATE",
         areas["RELEASE_ELIGIBLE_GEOMETRY_AREA_M2"],
         {"where": {"RELEASE_STATUS": sreg.RELEASED}, "column": "area_m2"}),
        ("PHYSICAL_SPACES", "P7757_ROUND6E_SPACE_REGISTER",
         areas["PHYSICAL_SPACES"],
         {"where": {"is_physical_space": True}, "op": "count"}),
        ("PHYSICAL_SPACE_AREA_M2", "P7757_ROUND6E_SPACE_REGISTER",
         areas["PHYSICAL_SPACE_AREA_M2"],
         {"where": {"is_physical_space": True}, "column": "area_m2"}),
        ("PHYSICAL_STAIRCASES", "P7757_ROUND6E_PHYSICAL_STAIR",
         stairs["counts"]["physical_stair_assemblies"], {"op": "count"}),
        ("NOSING_LENGTH_LM", "P7757_ROUND6E_PHYSICAL_STAIR",
         quantities["NOSING_LENGTH"]["value"],
         {"column": "NET_NOSING_LM"}),
        ("LANDING_AREA_M2", "P7757_ROUND6E_PHYSICAL_STAIR",
         quantities["LANDING_AREA"]["value"],
         {"column": "NET_LANDING_M2"}),
        ("STAIR_OBSERVATIONS", "P7757_ROUND6E_STAIR_OBSERVATION",
         sum(r["stair_observations"]
             for r in stairs["coverage"]["per_floor"]), {"op": "count"}),
        ("UNRESOLVED_STAIR_OBSERVATIONS",
         "P7757_ROUND6E_STAIR_OBSERVATION",
         stairs["coverage"]["unresolved_in_total"],
         {"where": {"status": stair.UNRESOLVED_OBSERVATION},
          "op": "count"}),
        ("SPACE_LINEAGE_LINKS", "P7757_ROUND6E_SPACE_LINEAGE",
         report["A_lineage"]["this_run"]["counts"]["links"],
         {"where": {"lineage": [slin.UNCHANGED, slin.RESHAPED,
                                slin.SPLIT, slin.MERGED, slin.NEW,
                                slin.IDENTITY_CHANGED, slin.ROLE_CHANGED,
                                slin.UNRESOLVED_LINEAGE]},
          "op": "count"}),
    ]
    return rcons.check(checks, tables)


def run(decode_json: str, out_dir: str, *, supervised_json: str = "",
        sections_json: str = "", dwf: str = "", pdfs=(),
        tests=None, allow_dirty: bool = False,
        why_dirty: str = "") -> dict:
    frozen = r6e.assert_frozen()

    # §1. THE GATE FIRST. Nothing is written from an unclean worktree or
    # a failing test run, and the refusal happens before any file exists.
    provenance = xp.gate(
        input_sources=[decode_json] + ([dwf] if dwf else []),
        engine_hashes={
            "PHYSICAL_WALL_BAND_HASH": pwall.wall_band_hash(),
            "WALL_FACE_OWNERSHIP_HASH": wface.model_hash(),
            "SINGLE_LINE_PARTITION_HASH": slp.model_hash(),
            "FITTING_BAND_HASH": fband.model_hash(),
            "FUNCTIONAL_ZONE_HASH": fz.model_hash(),
            "STAIR_ASSEMBLY_HASH": stair.model_hash(),
            "SPACE_REGISTER_HASH": sreg.model_hash(),
            "SPACE_LINEAGE_HASH": slin.model_hash(),
            "RULE_LIBRARY_MODEL_HASH": rlib.model_hash(),
            "ELEVATOR_MARBLE_HASH": elev.model_hash(),
            "VERTICAL_EVIDENCE_HASH": ve.model_hash(),
            "REPORT_CONSISTENCY_HASH": rcons.model_hash(),
            "EXPORT_PROVENANCE_HASH": xp.model_hash(),
        },
        tests=tests or {}, allow_dirty=allow_dirty,
        why_dirty_is_allowed=why_dirty)

    report, ctx = r6er.run_full(
        decode_json, supervised_json=supervised_json,
        sections_json=sections_json, dwf=dwf, pdfs=pdfs)
    rep, register, roles = ctx["rep"], ctx["register"], ctx["roles"]
    rows, zones = ctx["rows"], ctx["zones"]
    report["_rows"] = rows

    out = Path(out_dir)
    w, name = x6b._write, "P7757_ROUND6E_"
    tables = {
        f"{name}SPACE_REGISTER": (
            register_rows(register, rows, ctx["stable_of"]),
            {"one_row_per": "candidate polygon, with BOTH of its ids"}),
        f"{name}RELEASE_STATE": (
            release_rows(register),
            {"one_row_per": "candidate",
             "note": ("RELEASE_STATUS is the only release answer. It "
                      "never coexists with may_release=false, "
                      "is_physical_space=false or a role that may not "
                      "release a room quantity")}),
        f"{name}SPACE_LINEAGE": (
            lineage_rows(ctx["lineage"]),
            {"one_row_per": "space of this run, and every space gone",
             "note": ("a split gives no child the parent's id, and a "
                      "merge keeps every predecessor")}),
        f"{name}LINEAGE_HISTORY": (
            [dict(x.record(), round=step["to"])
             for step in ctx["chain"]["steps"]
             for x in step["report"].links],
            {"one_row_per": "space, in each earlier round",
             "note": "computed against the bundles as they were exported"}),
        f"{name}STABLE_SPACE_INDEX": (
            stable_index_rows(ctx["chain"], ctx["lineage"]),
            {"one_row_per": "stable id, per round"}),
        f"{name}DRAWING_REGION_ROLE": (
            x6c.region_role_rows(roles),
            {"one_row_per": "drawing region on the sheet"}),
        f"{name}FLOOR_ASSIGNMENT": (
            x6c.floor_rows(roles, ctx["supervised"]),
            {"one_row_per": "region, and the floor it draws"}),
        f"{name}FUNCTIONAL_ZONE": (
            x6d.zone_rows(zones),
            {"one_row_per": "functional zone",
             "note": "a zone creates no wall, no room and no quantity"}),
        f"{name}PANTRY_ANALYSIS": (
            x6d.pantry_rows(zones),
            {"one_row_per": "pantry"}),
        f"{name}PHYSICAL_STAIR": (
            physical_stair_rows(ctx["stairs"]),
            {"one_row_per": "STAIRCASE, however many plans draw it"}),
        f"{name}STAIR_PLAN_INSTANCE": (
            x6d.assembly_rows(rep),
            {"one_row_per": "drawing OF a staircase",
             "note": ("the same stair drawn on two plans is one "
                      "quantity and two rows here")}),
        f"{name}STAIR_FLIGHT": (x6d.flight_rows(rep),
                                {"one_row_per": "flight"}),
        f"{name}STAIR_TREAD": (
            x6d.tread_rows(rep),
            {"one_row_per": "tread, measured from its own polygon"}),
        f"{name}STAIR_RISER": (
            x6d.riser_rows(rep),
            {"one_row_per": "riser",
             "note": ("a plan carries no height: without evidence the "
                      "riser quantity is NOT ESTABLISHED")}),
        f"{name}STAIR_PIECE_BETWEEN_FLIGHTS": (
            piece_rows(rep),
            {"one_row_per": "piece of floor between the flights",
             "note": ("STAIR_LANDING, OPEN_VOID, FLOOR_PLATE or "
                      "CIRCULATION_FLOOR. Only the first is stair")}),
        f"{name}STAIR_OBSERVATION": (
            observation_rows(rep, ctx["coverage"]),
            {"one_row_per": "stair-like thing the drawing shows",
             "note": ("MAPPED_TO_STAIR_ASSEMBLY, "
                      "STAIR_OBSERVATION_UNRESOLVED or refused on "
                      "evidence. Nothing is left silent")}),
        f"{name}STAIR_COVERAGE": (
            coverage_rows(ctx["coverage"]),
            {"one_row_per": "floor",
             "note": "COMPLETE, INCOMPLETE or FAILED, per floor"}),
        f"{name}STAIR_QUANTITY": (
            quantity_rows(ctx["quantities"]),
            {"one_row_per": "staircase, each figure in its own unit",
             "note": "m2, lm and pcs are never added together"}),
        f"{name}VERTICAL_EVIDENCE": (
            vertical_rows(report["D_vertical_evidence"]),
            {"one_row_per": "level mark, riser note or sheet found",
             "note": ("PLACED, a LEAD in a representation this project "
                      "cannot place, or refused as a take-off total")}),
        f"{name}RULE_LIBRARY": (
            rule_rows(ctx["library"], ctx["project_rules"]),
            {"one_row_per": "Urban Projects owner rule, as versioned",
             "note": ("PROJECT DRAWING > PROJECT OWNER OVERRIDE > "
                      "URBAN PROJECTS STANDARD > UNKNOWN. A default "
                      "never bypasses geometry")}),
        f"{name}ELEVATOR_MARBLE": (
            elevator_rows(ctx["elevators"]),
            {"one_row_per": "elevator landing station, or a question",
             "note": ("declared for the later trade phase. The surround "
                      "is the UNION area of its polygon, the threshold "
                      "is its own object, and no elevator is detected "
                      "in any drawing here")}),
        f"{name}FITTING_BAND": (
            x6d.fitting_rows(rep),
            {"one_row_per": "band that stands on another band"}),
        f"{name}WALL_STRETCH_OWNERSHIP": (
            x6d.stretch_rows(rep),
            {"one_row_per": "stretch of its two lines that a wall owns"}),
        f"{name}BOUNDARY": (x6b.boundary_rows(rep),
                            {"one_row_per": "side of a space polygon"}),
        f"{name}OPENING": (x6b.opening_rows(rep),
                           {"one_row_per": "opening hypothesis"}),
        f"{name}IDENTITY": (x6b.identity_rows(rep),
                            {"one_row_per": "reconciled place"}),
        f"{name}DIMENSION": (x6b.dimension_rows(rep),
                             {"one_row_per": "authored dimension"}),
        f"{name}EXCEPTIONS": (
            exception_rows(rep, register, roles, zones, report,
                           ctx["lineage"], ctx["coverage"]),
            {"one_row_per": "refusal, of any kind, anywhere in the run"}),
    }
    report.pop("_rows", None)

    exports, files = [], []
    for table, (rws, notes) in tables.items():
        entry = w(out, table, rws, notes)
        exports.append(entry)
        for key in ("csv", "json"):
            files.append(xp.file_hashes(entry[key]))

    # §7. The report against the rows that were just written.
    consistency = _metrics(report, {k: v[0] for k, v in tables.items()})
    report["G_report_against_export"] = consistency

    rep_path = out / "P7757_ROUND6E_REPORT.json"
    rep_path.write_text(json.dumps(report, indent=2, ensure_ascii=False,
                                   default=str) + "\n", encoding="utf-8")
    files.append(xp.file_hashes(rep_path, content=report))

    manifest = {
        "export": EXPORT,
        "provenance": xp.seal(provenance, files),
        "source": {"file": "P7757_ARCHITECTURAL.dwg",
                   "sha256_16": "7f61f3acdd62d62d", "decode": decode_json},
        "supervised_floor_assignment": ctx["supervised"],
        "section_evidence": sections_json or "none supplied",
        "synthetic": {
            "ROUND_6E_SYNTHETIC_HASH": frozen["ROUND_6E_SYNTHETIC_HASH"],
            "cases": f"{frozen['passed']}/{frozen['cases']}"},
        "tables": [{k: e[k] for k in ("export", "rows")}
                   for e in exports],
        "named_tables": NAMED,
        "report_hash": report["ROUND_6E_REPORT_HASH"],
        "report_against_export": consistency["status"],
        "areas_kept_apart": register.areas(),
        "owner_rules": {
            "RULE_LIBRARY_HASH": ctx["library"].library_hash(),
            "library_version": ctx["library"].library_version,
            "rules": len(ctx["library"].rules),
            "project_rules": r6er.PROJECT_RULES_PATH,
            "pantry_openness": report["F_pantry"]["counts"]["by_openness"],
            "stair_finish_rule": report["C_stairs"][
                "project_finish_rule"]["rule_id"],
            "elevator": report["H_elevator_marble"]["status"],
        },
        "stair_coverage": ctx["coverage"]["stair_coverage"],
        "riser_height": report["D_vertical_evidence"][
            "riser_height_status"],
        "MARBLE_INTERSECT_PORCELAIN_M2": report["E_marble_and_porcelain"][
            "MARBLE_INTERSECT_PORCELAIN_M2"],
        "how_to_reproduce": [
            f"git checkout {provenance['SOURCE_COMMIT']}",
            "python -m pytest",
            "python -m tools.export_round6e --decode-json <decode> "
            "--out-dir <dir> --supervised <file> --dwf <file>",
            "compare CANONICAL_CONTENT_SHA256 per file",
        ],
        "what_this_is_not": (
            "no TradeMeasurementZone, no floor ceramic, no wall ceramic, "
            "no waste rule, no pricing and no contractor rates"),
    }
    man = out / "ROUND6E_EXPORT_MANIFEST.json"
    man.write_text(json.dumps(manifest, indent=2, ensure_ascii=False,
                              default=str) + "\n", encoding="utf-8")

    archive = out / "P7757_ROUND6E_EXPORT.tar.gz"
    with tarfile.open(archive, "w:gz") as tar:
        for e in exports:
            for key in ("csv", "json"):
                p = Path(e[key])
                tar.add(p, arcname=f"P7757_ROUND6E_EXPORT/{p.name}")
        for p in (man, rep_path):
            tar.add(p, arcname=f"P7757_ROUND6E_EXPORT/{p.name}")
    manifest["archive"] = str(archive)
    manifest["archive_sha256"] = xp.raw_sha256(archive)
    man.write_text(json.dumps(manifest, indent=2, ensure_ascii=False,
                              default=str) + "\n", encoding="utf-8")
    return manifest


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--decode-json", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--supervised", default="")
    ap.add_argument("--sections", default="")
    ap.add_argument("--dwf", default="")
    ap.add_argument("--pdf", action="append", default=[])
    ap.add_argument("--tests-passed", type=int, default=0)
    ap.add_argument("--tests-failed", type=int, default=0)
    ap.add_argument("--tests-command", default="python -m pytest")
    ap.add_argument("--allow-dirty", action="store_true")
    ap.add_argument("--why-dirty", default="")
    a = ap.parse_args(argv)
    man = run(a.decode_json, a.out_dir, supervised_json=a.supervised,
              sections_json=a.sections, dwf=a.dwf, pdfs=a.pdf,
              tests={"passed": a.tests_passed, "failed": a.tests_failed,
                     "command": a.tests_command},
              allow_dirty=a.allow_dirty, why_dirty=a.why_dirty)
    print(json.dumps({
        "archive": man["archive"],
        "archive_sha256": man["archive_sha256"],
        "provenance": {k: man["provenance"][k]
                       for k in ("SOURCE_COMMIT", "GIT_TREE_HASH",
                                 "WORKTREE_STATUS", "PROVENANCE_HASH")},
        "tests": man["provenance"]["TESTS"],
        "report_against_export": man["report_against_export"],
        "stair_coverage": man["stair_coverage"],
        "tables": man["tables"],
    }, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
