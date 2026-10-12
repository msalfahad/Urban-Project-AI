"""URBAN BOQ M9 (S1) - canonical BOQ lines, room material plans and the room-by-room workbook, on top of route G.

    python3 -I tools/urban_boq_m9.py run --drawings NEW.dxf --out OUT [every urban_boq_m2 run option]
                                         [--rooms ROOMS.json] [--no-m9-xlsx]
    python3 -I tools/urban_boq_m9.py rooms --rooms ROOMS.json --out OUT [--no-m9-xlsx]
    python3 -I tools/urban_boq_m9.py rooms-check --rooms ROOMS.json
    python3 -I tools/urban_boq_m9.py tiles --length 3 --width 2 --joint 0.002 [--min-cut 0.1] [--min-reusable 0.1]
                                           [--kerf 0] [--rotation] [--selected TILE-120x60] [--custom 0.9x0.9] [--wet]
    python3 -I tools/urban_boq_m9.py membrane --length 3 --width 2 --door 0.8:0.2 [--detail NOT_ESTABLISHED]
                                              [--direction MIN_MATERIAL] [--min-reusable 0.3]
                                              [--data-sheet-side-lap 0.15 --data-sheet-source "TDS rev 2"]
    python3 -I tools/urban_boq_m9.py rules [--check]
    python3 -I tools/urban_boq_m9.py arch --drawings ARCH.dxf --out OUT --method ARCH_TAKEOFF_V1 [--facts FACTS.json]
                                          [--layer-roles LAYER=WALL ...] [--reference-areas GF=120.5 ...]
                                          [--project NAME] [--no-m9-xlsx] [--no-svg]

`run` calls urban_boq_m2's compute and writer exactly as `urban_boq_m2 run` does (tools/urban_boq_m2.py is frozen and
not edited), so every file it writes in OUT is the route G output unchanged; the M9 outputs go to OUT/m9/:

    BOQ_LINES.json / .csv     canonical lines (URBAN_CANONICAL_BOQ_LINE_V1): the route G items adapted (numbers and
                              states never raised) + the room lines of --rooms
    MATERIAL_RESULTS.json     tile / membrane material results per room (waste, offcuts, packs: views of a line)
    COVERAGE.json / .csv      the 99 BOQ families with this run's terminal state
    RUN_RULES.json            rule-set version and digest, superseded rules, conventions set and digest, specs used
    URBAN_ROOM_BOQ.xlsx       the room-by-room workbook (formulas; recalculate before reading cached values)
    ROOMS_DIAGNOSTIC.json     with --rooms: the room schedule check (no BOQ line)

`arch` (M9 S2, behind the versioned method flag ARCH_TAKEOFF_V1) measures the architectural plans themselves:
DXF (urban_intake + the arch hatch reader) -> plan regions by floor title -> layer roles from the geometry (walls,
columns, windows, doors; --layer-roles overrides, recorded) -> rooms (TS01 faces closed at jambed openings and door
symbols, named from the room words inside) -> per-room lines (floor finish, ceiling, skirting, wet-room
waterproofing, wall finishes when their heights are established) -> tile / membrane material per room. OUT gets the
M9 files above plus ARCH_PLAN.json, ARCH_ROOMS.json, ARCH_OPENINGS.json, UNRESOLVED.json and one SVG overlay per
plan region; the workbook gains the ROOM BY ROOM BOQ sheet. Route G and every structural output are untouched.

No prices. MACHINE_ONLY: nothing here is reviewed, approved or quotation-ready.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.source import boq_line as BL              # noqa: E402
from engine.source import coverage_census as CS       # noqa: E402
from engine.source import material_spec as MS         # noqa: E402
from engine.source import membrane_layout as ML       # noqa: E402
from engine.source import room_boq as RB              # noqa: E402
from engine.source import rule_store as RS            # noqa: E402
from engine.source import tile_layout as TL           # noqa: E402

POLICY_ID = "URBAN_BOQ_M9_S1"
ARCH_POLICY_ID = "URBAN_BOQ_M9_S2_ARCH"
ARCH_METHODS = ("ARCH_TAKEOFF_V1",)
M9_DIR = "m9"
CREATED = datetime(2026, 1, 1)


def _j(obj):
    return json.dumps(obj, indent=1, sort_keys=True, ensure_ascii=False, default=str) + "\n"


def _csv(rows, cols):
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=list(cols), extrasaction="ignore", lineterminator="\n")
    w.writeheader()
    for r in rows:
        w.writerow({k: (json.dumps(v, ensure_ascii=False, sort_keys=True) if isinstance(v, (dict, list)) else v)
                    for k, v in r.items()})
    return buf.getvalue()


def revision_set_sha256(inputs):
    return hashlib.sha256("|".join(sorted(i["sha256"] for i in inputs)).encode("utf-8")).hexdigest()


def structural_lines(R):
    """the route's items as canonical lines (route G and the M1 routes share the provisional_estimate item)."""
    s = R["summary"]
    pid = s.get("project") or "new project"
    rev = revision_set_sha256(R.get("inputs") or [])
    docs = [{"file": i.get("file"), "sha256": i["sha256"]} for i in R.get("inputs") or []]
    return [BL.from_route_g(it, project_id=pid, revision_set_sha256=rev, conventions_set=s["conventions"]["set"],
                            conventions_digest=s["conventions"]["digest"], documents=docs) for it in R["items"]]


def run_rules(*, conventions=None, specs=()):
    rs = RS.rule_set()
    return {"policy": POLICY_ID, "rule_store": RS.policy_record(), "rule_set": rs["version"], "rule_set_digest": rs["digest"],
            "superseded": rs["superseded"], "proposed_excluded": True, "store_drift": RS.check(),
            "conventions": conventions, "material_specs_used": sorted(set(specs))}


def write_m9(out, *, s_lines=(), room=None, family_coverage=None, project_id, conventions=None, xlsx=True, rooms_check=None,
             arch=None):
    from engine import boq_room_workbook as WB
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    lines = list(s_lines) + (room["lines"] if room else [])
    mats = room["materials"] if room else []
    rows = CS.census(lines, family_coverage=family_coverage, structural_run=bool(s_lines) or family_coverage is not None,
                     rooms_run=room is not None and arch is None, material_results=mats, arch_run=arch is not None)
    specs = [(m.get("material_spec") or {}).get("spec_id") for m in mats if (m.get("material_spec") or {}).get("spec_id")]
    rr = run_rules(conventions=conventions, specs=specs)
    if arch is not None:
        rr["arch"] = arch["run"]
    files = {"BOQ_LINES.json": BL.dumps(lines), "BOQ_LINES.csv": _csv(list(BL.csv_rows(lines)), BL.CSV_COLUMNS),
             "MATERIAL_RESULTS.json": _j({"policy": POLICY_ID, "results": mats,
                                          "comparisons": room["comparisons"] if room else [],
                                          "unresolved": room["unresolved"] if room else []}),
             "COVERAGE.json": _j({"summary": CS.summary(rows), "families": rows}),
             "COVERAGE.csv": _csv(rows, ("code", "group", "item_en", "item_ar", "unit", "capability", "run_state", "lines",
                                         "reason", "next_slice")),
             "RUN_RULES.json": _j(rr)}
    if rooms_check is not None:
        files["ROOMS_DIAGNOSTIC.json"] = _j(rooms_check)
    if arch is not None:
        files["ARCH_PLAN.json"] = _j({k: arch[k] for k in ("run", "regions", "other_frames", "reference_areas")})
        files["ARCH_ROOMS.json"] = _j({"run": arch["run"], "rooms": arch["rooms"]})
        files["ARCH_OPENINGS.json"] = _j({"run": arch["run"], "openings": arch["openings"]})
        if arch.get("walls") is not None:
            files["ARCH_WALLS.json"] = _j({"run": arch["run"], "floors": arch["walls"]})
        files["UNRESOLVED.json"] = _j({"run": arch["run"], "unresolved": room["unresolved"]})
    for name, text in files.items():
        (out / name).write_text(text, encoding="utf-8")
    res = {"files": sorted(files)}
    if xlsx:
        res["xlsx"] = WB.write(out / "URBAN_ROOM_BOQ.xlsx", room_boq=room, structural_lines=list(s_lines), census_rows=rows,
                               meta={"project_id": project_id, "rule_set": rr["rule_set"],
                                     "rule_set_digest": rr["rule_set_digest"]}, created=CREATED, arch=arch)
    return res, rows


def cmd_run(a):
    from tools import urban_boq_m2 as M2
    from tools import urban_structural_boq as M1
    R = M2.compute(a.drawings, conventions=a.conventions, overrides=M1.parse_sets(a.set), profile=a.profile,
                   route=a.route, cache_dir=a.cache, evidence=a.evidence, arch=a.arch,
                   evidence_review=a.evidence_review, completeness=not a.no_completeness)
    writer = M2.write_all if R.get("generic") else M1.write_all
    writer(R, a.out, as_of=a.as_of, pdf=not a.no_pdf, xlsx=not a.no_xlsx)
    s_lines = structural_lines(R)
    room = RB.build(a.rooms) if a.rooms else None
    chk = RB.check(a.rooms) if a.rooms else None
    cov = (R.get("generic") or {}).get("family_coverage")
    res, rows = write_m9(Path(a.out) / M9_DIR, s_lines=s_lines, room=room, family_coverage=cov,
                         project_id=R["summary"].get("project") or "new project",
                         conventions={"set": R["summary"]["conventions"]["set"],
                                      "digest": R["summary"]["conventions"]["digest"]},
                         xlsx=not a.no_m9_xlsx, rooms_check=chk)
    print(json.dumps({"route": R["summary"]["route"], "structural_lines": len(s_lines),
                      "room_lines": len(room["lines"]) if room else 0, "coverage": CS.summary(rows)["by_run_state"],
                      "m9_outputs": res["files"] + (["URBAN_ROOM_BOQ.xlsx"] if "xlsx" in res else [])}, indent=1))
    return 0


def cmd_rooms(a):
    room = RB.build(a.rooms)
    res, rows = write_m9(a.out, room=room, project_id=room["project_id"], xlsx=not a.no_m9_xlsx,
                         rooms_check=RB.check(a.rooms))
    print(json.dumps({"room_lines": len(room["lines"]), "materials": len(room["materials"]),
                      "unresolved": len(room["unresolved"]), "outputs": res["files"]}, indent=1))
    return 0


def _kv(items, what):
    out = {}
    for it in items or []:
        k, sep, v = it.partition("=")
        if not sep or not k or not v:
            raise SystemExit(f"{what}: expected KEY=VALUE, got {it!r}")
        out[k] = v
    return out


def arch_compute(drawing, *, method, facts=None, layer_roles=None, reference_areas=None, project_id=None, intake=None):
    """the architectural route on one plan drawing: every stage recorded, nothing silently skipped. `intake` (the
    urban_intake.read result of this same drawing) skips the read for repeated runs / tests."""
    from engine.source import arch_measure as AM
    from engine.source import arch_plan as AP
    from engine.source import arch_rooms as AR
    from engine.source import arch_walls as AW
    from tools import arch_intake as AI
    from tools import urban_intake as UI
    if method not in ARCH_METHODS:
        raise SystemExit(f"--method must be one of {ARCH_METHODS} (the architectural route is behind a versioned flag)")
    facts = AM.validate_facts(facts)
    path = Path(drawing)
    sha = hashlib.sha256(path.read_bytes()).hexdigest()
    docs = [{"file": path.name, "sha256": sha}]
    rev = revision_set_sha256(docs)
    pid = project_id or (facts or {}).get("project_id") or "new project"
    E = intake if intake is not None else UI.read(str(path))
    A = AI.read_arch(path, unit_m=E.get("unit_m"))
    hs = A["hatches"]
    # the architectural route reads its own texts (style, font, SHX decoding, ATTRIB), nested inserts (room tags,
    # fixtures) and the entities K2 leaves to findings (MLINE / SPLINE / 2D POLYLINE); route G keeps the intake as is
    chords = AI.ellipse_chords(E.get("ellipses") or [], E["unit_m"])
    A["report"]["ellipses_as_chords"] = {"ellipses": len(E.get("ellipses") or []), "chords": len(chords)}
    E = dict(E, hatches=[dict(h, ring=h["rings"][0]) for h in hs if h["rings"]], texts=A["texts"],
             inserts=A["inserts"], segments=E["segments"] + A["extra_segments"] + chords,
             arcs=E["arcs"] + A["extra_arcs"])
    u = E["unit_m"]
    P = AP.plan_regions(E)
    regs = P["regions"]
    ents_of = {r["region_id"]: AP.region_entities(E, r["box"]) for r in regs}
    level = {r["region_id"]: AR.dominant_level(ents_of[r["region_id"]]["texts"]) for r in regs}
    lines, mats, comps, unresolved, rooms, openings, regions, walls_of = [], [], [], [], [], [], [], []
    roles_of = {r["region_id"]: AP.layer_roles(ents_of[r["region_id"]], u, override=layer_roles) for r in regs}
    spaces_of = {r["region_id"]: AR.spaces(ents_of[r["region_id"]], roles_of[r["region_id"]]["roles"], u,
                                           region_id=r["region_id"])
                 for r in regs if roles_of[r["region_id"]]["state"] != "BLOCKED"}
    # one stair drawn on two plans: the plans are aligned on their column grid, and a flight lying over a flight of
    # the plan below is counted once (the repeat is exposure until a reviewer says which it is)
    stacked = sorted((r for r in regs if r["region_id"] in spaces_of and not r.get("warning")), key=lambda r: r["order"])
    cross = AR.cross_plan_flights([(r["floor"], spaces_of[r["region_id"]]["column_boxes"],
                                    [fl for f in spaces_of[r["region_id"]]["spaces"]
                                     for fl in (f.get("symbols_inside") or {}).get("stair_flights") or ()],
                                    AR.void_marks(ents_of[r["region_id"]], spaces_of[r["region_id"]]["faces"]))
                                   for r in stacked], u)
    for i, reg in enumerate(regs):
        rid = reg["region_id"]
        ents = ents_of[rid]
        floor = reg["floor"] if not reg.get("warning") else rid.replace(":", "-")
        above = next((level[r["region_id"]] for r in regs[i + 1:] if r["order"] > reg["order"]
                      and level[r["region_id"]] is not None), None)
        L = roles_of[rid]
        rec = {"region_id": rid, "floor": floor, "sheet_id": reg["sheet_id"], "title_text_id": reg["title_text_id"],
               "box": reg["box"], "evidence": reg["evidence"], "warning": reg.get("warning"),
               "layer_roles": L["roles"], "layer_evidence": L["evidence"], "roles_source": L["source"],
               "roles_state": L["state"], "level_m": level[rid], "floor_above_level_m": above,
               "entities": {k: len(v) for k, v in ents.items()}}
        if L["state"] == "BLOCKED":
            rec["stage_state"] = "BLOCKED_AT_LAYER_ROLES"
            unresolved.append({"room_id": "-", "floor": floor, "item": "plan region " + rid,
                               "reason": L.get("why") or "NO_WALL_LAYER: no layer behaves like walls"})
            regions.append(rec)
            continue
        S = spaces_of[rid]
        S["walls"] = AW.walls(ents, L["roles"], u, S["faces"], S["openings"], columns=S["column_boxes"])
        M = AM.measure(S, floor=floor, project_id=pid, revision_set_sha256=rev, facts=facts,
                       floor_above_level_m=above, floor_level_m=level[rid], documents=docs)
        X = AM.materials(M, facts)
        ref = (reference_areas or {}).get(floor)
        rec.update(stage_state="MEASURED", face_counts=S["counts"], space_counts=M["counts"],
                   plate=S["plate"], warnings=S["warnings"], columns=S["columns"], arrangement=S["arrangement"],
                   openings=dict(Counter(o["kind"] for o in S["openings"])), openings_rejected=len(S["openings_rejected"]),
                   door_symbols=len(S["doors"]), door_status=dict(Counter(v.get("state") for v in S["door_status"].values())),
                   lines=len(M["lines"]), rooms_measured=sum(1 for r in M["rooms"] if r["class"] in ("ROOM", "MIXED")))
        if ref is not None:
            plate = S["plate"]["largest_m2"]
            rec["reference"] = {"area_m2": ref, "plate_m2": round(plate, 4), "diff_m2": round(plate - ref, 4),
                                "diff_pct": round(100.0 * (plate - ref) / ref, 3) if ref else None,
                                "basis": "the outer boundary of the wall network vs the reference area given on the "
                                         "command line (an independent schedule, e.g. the architect's area table)"}
        walls_of.append({"floor": floor, "region_id": rid, **{k: S["walls"][k] for k in
                                                               ("walls", "by_thickness", "graph", "conservation")}})
        for rm in M["rooms"]:
            rm["region_id"] = rid
        rooms += M["rooms"]
        openings += M["openings"]
        lines += M["lines"]
        mats += X["materials"]
        comps += X["comparisons"]
        unresolved += M["unresolved"] + X["unresolved"]
        regions.append(rec)
    by_room = {r["room_id"]: r for r in rooms}
    reg_of = {r["floor"]: r for r in regions}
    unresolved = [AM.flag(u_, drawing=path.name, region=reg_of.get(u_.get("floor")), room=by_room.get(u_.get("room_id")))
                  for u_ in unresolved]
    run = {"policy": ARCH_POLICY_ID, "method": method, "drawing": docs[0], "revision_set_sha256": rev,
           "project_id": pid, "unit_m": u, "insunits": E.get("insunits"), "intake_findings": E.get("intake_findings"),
           "hatch_reader": {"hatches": len(hs), "with_islands": sum(1 for h in hs if h["islands"]),
                            "inside_blocks": sum(1 for h in hs if h["owner"])},
           "arch_reader": A["report"], "cross_plan_stairs": cross,
           "facts": {"schema": (facts or {}).get("schema"), "given": sorted(k for k in (facts or {}) if k != "schema")},
           "layer_roles_override": layer_roles or {}, "policies": {"plan": AP.policy_record(), "rooms": AR.policy_record(),
                                                                    "measure": AM.policy_record(),
                                                                    "walls": AW.policy_record()}}
    room_boq = {"project_id": pid, "lines": lines, "materials": mats, "comparisons": comps, "unresolved": unresolved,
                "assumptions": [], "geometry_source": f"architectural plan DXF {path.name} ({method})"}
    arch = {"run": run, "regions": regions, "other_frames": P["other_frames"], "rooms": rooms, "openings": openings,
            "walls": walls_of, "reference_areas": reference_areas or {}}
    return room_boq, arch, E


def _dxf_of(drawing, out, conversions):
    """a DWG through the DWG adapter (an external converter, run as a separate program) into OUT/converted; a DXF as
    it is. A failed or impossible conversion stops the run with its record (OUT/DWG_CONVERSION.json)."""
    p = Path(drawing)
    if p.suffix.lower() != ".dwg":
        return str(p)
    from tools import dwg_adapter as DA
    rec = DA.convert(p, out / "converted")
    conversions.append(rec)
    if rec["state"] != "CONVERTED":
        out.mkdir(parents=True, exist_ok=True)
        (out / "DWG_CONVERSION.json").write_text(_j({"conversions": conversions}), encoding="utf-8")
        raise SystemExit(f"DWG_CONVERSION_BLOCKED: {p.name}: {rec['remedy']}")
    return rec["dxf"]


def cmd_arch(a):
    facts = json.loads(Path(a.facts).read_text(encoding="utf-8")) if a.facts else None
    roles = _kv(a.layer_roles, "--layer-roles")
    refs = {k: float(v) for k, v in _kv(a.reference_areas, "--reference-areas").items()}
    out = Path(a.out)
    conversions = []
    plan = _dxf_of(a.drawings[0], out, conversions)
    structural = _dxf_of(a.structural, out, conversions) if a.structural else None
    room, arch, E = arch_compute(plan, method=a.method, facts=facts, layer_roles=roles or None,
                                 reference_areas=refs, project_id=a.project)
    if conversions:
        arch["run"]["dwg_conversions"] = conversions
        (out / "DWG_CONVERSION.json").write_text(_j({"conversions": conversions}), encoding="utf-8")
    s_lines, cov, conv = (), None, None
    if structural:
        # the structural drawing through the unchanged route G (its own outputs in OUT/structural), its lines into the
        # same room-by-room workbook (STRUCTURAL sheet; reinforcement stays its own line family, never a ratio)
        from tools import urban_boq_m2 as M2
        R = M2.compute([structural], conventions=a.conventions, profile=a.profile, route="G",
                       completeness=not a.no_completeness)
        M2.write_all(R, out / "structural", as_of=a.as_of, pdf=False, xlsx=not a.no_m9_xlsx)
        s_lines = structural_lines(R)
        cov = (R.get("generic") or {}).get("family_coverage")
        conv = {"set": R["summary"]["conventions"]["set"], "digest": R["summary"]["conventions"]["digest"]}
        arch["run"]["structural"] = {"drawing": Path(structural).name, "route": R["summary"]["route"],
                                     "lines": len(s_lines), "conventions": conv}
    res, rows = write_m9(out, s_lines=s_lines, room=room, family_coverage=cov, project_id=room["project_id"],
                         conventions=conv, xlsx=not a.no_m9_xlsx, arch=arch)
    svgs = []
    if not a.no_svg:
        from tools import arch_overlay as AO
        for reg in arch["regions"]:
            name = f"OVERLAY_{reg['floor']}.svg"
            (out / name).write_text(AO.svg(E, reg, [r for r in arch["rooms"] if r.get("region_id") == reg["region_id"]],
                                           [o for o in arch["openings"] if o["floor"] == reg["floor"]],
                                           walls=next((w for w in arch.get("walls") or () if
                                                       w["region_id"] == reg["region_id"]), None)),
                                    encoding="utf-8")
            svgs.append(name)
    ev = Counter(ln["evidence_state"] for ln in room["lines"])
    print(json.dumps({"method": a.method, "regions": [{"floor": r["floor"], "state": r["stage_state"],
                                                        "rooms": r.get("space_counts"), "lines": r.get("lines"),
                                                        "reference": r.get("reference")} for r in arch["regions"]],
                      "lines": len(room["lines"]), "structural_lines": len(s_lines), "evidence": dict(sorted(ev.items())),
                      "materials": dict(Counter(m["state"] for m in room["materials"])),
                      "unresolved": len(room["unresolved"]), "coverage": CS.summary(rows)["by_run_state"],
                      "outputs": res["files"] + (["URBAN_ROOM_BOQ.xlsx"] if "xlsx" in res else []) + svgs}, indent=1))
    return 0


def _tile_constraints(a):
    c = {"joint_m": a.joint, "min_cut_m": a.min_cut, "min_reusable_m": a.min_reusable, "kerf_m": a.kerf,
         "rotation_allowed": a.rotation, "wet_room": a.wet, "objective": a.objective}
    return {k: v for k, v in c.items() if v is not None}


def cmd_tiles(a):
    specs = [MS.tile(s) for s in (a.sizes or MS.OWNER_TILE_SIZES)]
    for cu in a.custom or []:
        L, W = (float(x) for x in cu.lower().split("x"))
        specs.append(MS.custom_tile(L, W))
    sel = a.selected or specs[0]["spec_id"]
    rows = TL.compare({"room_id": "CLI", "length_m": a.length, "width_m": a.width}, specs, sel, _tile_constraints(a))
    for r in rows:
        r.pop("result", None)
        if not a.verbose:
            r.pop("tried", None)
    print(_j({"room_m": [a.length, a.width], "constraints": _tile_constraints(a), "candidates": rows}), end="")
    return 0


def cmd_membrane(a):
    spec = MS.membrane()
    if a.data_sheet_side_lap is not None or a.data_sheet_end_lap is not None:
        spec = MS.apply_data_sheet(spec, {"side_lap_m": a.data_sheet_side_lap, "end_lap_m": a.data_sheet_end_lap,
                                          "source": a.data_sheet_source})
    dws = []
    for i, d in enumerate(a.door or [], 1):
        p = d.split(":")
        dws.append({"door_id": p[2] if len(p) > 2 else f"D{i}", "width_m": float(p[0]), "depth_m": float(p[1])})
    c = {"upturn_h_m": RS.rule("UP-WP-002")["value"], "doorways": dws, "doorway_detail": a.detail,
         "direction": a.direction, "min_reusable_m": a.min_reusable, "penetrations": a.penetrations}
    r = ML.plan({"room_id": "CLI", "length_m": a.length, "width_m": a.width}, spec, constraints=c)
    print(_j(r), end="")
    return 0


def cmd_rooms_check(a):
    print(_j(RB.check(a.rooms)), end="")
    return 0


def cmd_rules(a):
    if a.check:
        d = RS.check()
        print(_j({"drift": d}), end="")
        return 1 if d else 0
    print(_j(run_rules()), end="")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(prog="urban_boq_m9", description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("run")
    p.add_argument("--drawings", nargs="+", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--conventions")
    p.add_argument("--set", action="append", default=[], metavar="ID=VALUE")
    p.add_argument("--profile")
    p.add_argument("--route", default="auto", choices=["auto", "A", "B", "G", "C"])
    p.add_argument("--no-pdf", action="store_true")
    p.add_argument("--no-xlsx", action="store_true")
    p.add_argument("--as-of", default=datetime.now().strftime("%Y-%m-%d"))
    p.add_argument("--cache")
    p.add_argument("--evidence")
    p.add_argument("--arch", nargs="+")
    p.add_argument("--evidence-review")
    p.add_argument("--no-completeness", action="store_true")
    p.add_argument("--rooms", help="room schedule (URBAN_ROOM_INPUT_V1)")
    p.add_argument("--no-m9-xlsx", action="store_true")
    p.set_defaults(fn=cmd_run)
    p = sub.add_parser("rooms")
    p.add_argument("--rooms", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--no-m9-xlsx", action="store_true")
    p.set_defaults(fn=cmd_rooms)
    p = sub.add_parser("rooms-check")
    p.add_argument("--rooms", required=True)
    p.set_defaults(fn=cmd_rooms_check)
    p = sub.add_parser("tiles")
    p.add_argument("--length", type=float, required=True)
    p.add_argument("--width", type=float, required=True)
    p.add_argument("--joint", type=float, required=True)
    p.add_argument("--min-cut", type=float)
    p.add_argument("--min-reusable", type=float)
    p.add_argument("--kerf", type=float)
    p.add_argument("--rotation", action="store_true", default=None)
    p.add_argument("--wet", action="store_true", default=None)
    p.add_argument("--objective", choices=TL.OBJECTIVES)
    p.add_argument("--sizes", nargs="+")
    p.add_argument("--custom", nargs="+", metavar="LxW")
    p.add_argument("--selected")
    p.add_argument("--verbose", action="store_true")
    p.set_defaults(fn=cmd_tiles)
    p = sub.add_parser("membrane")
    p.add_argument("--length", type=float, required=True)
    p.add_argument("--width", type=float, required=True)
    p.add_argument("--door", nargs="+", metavar="WIDTH:DEPTH[:ID]")
    p.add_argument("--detail", default="NOT_ESTABLISHED", choices=ML.DOORWAY_DETAILS)
    p.add_argument("--direction", default="MIN_MATERIAL", choices=ML.DIRECTIONS)
    p.add_argument("--min-reusable", type=float)
    p.add_argument("--penetrations", type=int, default=0)
    p.add_argument("--data-sheet-side-lap", type=float)
    p.add_argument("--data-sheet-end-lap", type=float)
    p.add_argument("--data-sheet-source")
    p.set_defaults(fn=cmd_membrane)
    p = sub.add_parser("rules")
    p.add_argument("--check", action="store_true")
    p.set_defaults(fn=cmd_rules)
    p = sub.add_parser("arch")
    p.add_argument("--drawings", nargs=1, required=True,
                   help="one architectural plan DXF (a DWG goes through tools/dwg_adapter.py: an external converter)")
    p.add_argument("--out", required=True)
    p.add_argument("--method", required=True, choices=ARCH_METHODS,
                   help="the versioned architectural takeoff method (no default: the route is opt-in until validated)")
    p.add_argument("--facts", help="project facts (URBAN_ARCH_FACTS_V1): heights, finishes, tile constraints, membrane")
    p.add_argument("--layer-roles", nargs="+", metavar="LAYER=ROLE",
                   help="override the detected role of a layer (WALL, COLUMN, WINDOW, DOOR, OTHER); recorded")
    p.add_argument("--reference-areas", nargs="+", metavar="FLOOR=M2",
                   help="independent floor areas to compare the measured plates against (e.g. the area table)")
    p.add_argument("--project")
    p.add_argument("--structural", help="the structural drawing (DXF or DWG): route G, unchanged; its lines join the "
                                        "workbook")
    p.add_argument("--conventions", help="route G conventions profile (with --structural)")
    p.add_argument("--profile", help="route G drawing profile (with --structural)")
    p.add_argument("--no-completeness", action="store_true", help="with --structural: skip the M6 completeness pass")
    p.add_argument("--as-of", default=datetime.now().strftime("%Y-%m-%d"), help="with --structural: report date")
    p.add_argument("--no-m9-xlsx", action="store_true")
    p.add_argument("--no-svg", action="store_true")
    p.set_defaults(fn=cmd_arch)
    a = ap.parse_args(argv)
    return a.fn(a)


if __name__ == "__main__":
    sys.exit(main())
