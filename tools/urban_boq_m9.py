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
ARCH_POLICY_ID_V2 = "URBAN_BOQ_M9_S6_ARCH_V2"
ARCH_METHODS = ("ARCH_TAKEOFF_V1", "ARCH_TAKEOFF_V2", "ARCH_TAKEOFF_V2.1")
# S6: ARCH_TAKEOFF_V2 = V1 + drawing admission (stop, exit 2, no BOQ on a fatal finding) + unit-relative geometric
# tolerances + plan regions cut only along empty bands + floor-category and finish-surface completeness. V1 is
# unchanged; --strict-admission puts the same admission in front of V1 (its outputs are V1's own).
V2 = "ARCH_TAKEOFF_V2"
# Phase 2A: ARCH_TAKEOFF_V2.1 = V2 + the robust band-path geometry (engine.source.robust_geometry: the reviewed robust
# predicate at three sites, the mean-axis face lines, AT_THRESHOLD / UNDECIDABLE records). Opt-in only: V1 and V2 never
# reach the V2.1 code (their call paths pass no geometry object).
V21 = "ARCH_TAKEOFF_V2.1"
ARCH_POLICY_ID_V21 = "URBAN_BOQ_M9_P2A_ARCH_V2_1"
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
        if arch.get("floor_areas") is not None:
            files["ARCH_FLOOR_AREAS.json"] = _j({"run": arch["run"], "floors": arch["floor_areas"]})
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


class CompletenessFailed(Exception):
    """S6 (V2): measured, but a physical region or a finish surface has no line, exclusion or RFI."""

    def __init__(self, room_boq, arch, E):
        super().__init__("COMPLETENESS_FAILED: " + "; ".join(
            f"{c['floor']}: {len(c['unaccounted'])} unaccounted" for c in arch.get("coverage") or () if c["unaccounted"]))
        self.room_boq, self.arch, self.E = room_boq, arch, E


def arch_compute(drawing, *, method, facts=None, layer_roles=None, reference_areas=None, project_id=None, intake=None,
                 strict=False, units=None, region_specs=None, accept_xrefs=(), extra_documents=(),
                 admission_findings=()):
    """the architectural route on one plan drawing: every stage recorded, nothing silently skipped. `intake` (the
    urban_intake.read result of this same drawing) skips the read for repeated runs / tests.
    S6: method ARCH_TAKEOFF_V2, or strict=True (V1 behind the same admission), run the drawing discovery first and
    raise engine.source.discovery.AdmissionBlocked on a stopping finding (nothing is measured); units / region_specs /
    accept_xrefs are reviewer inputs (recorded). V2 also raises CompletenessFailed when a surface is unaccounted."""
    from engine.source import arch_floor as AF
    from engine.source import arch_measure as AM
    from engine.source import arch_plan as AP
    from engine.source import arch_rooms as AR
    from engine.source import arch_walls as AW
    from tools import arch_intake as AI
    from tools import urban_intake as UI
    if method not in ARCH_METHODS:
        raise SystemExit(f"--method must be one of {ARCH_METHODS} (the architectural route is behind a versioned flag)")
    v21 = method == V21
    v2 = method in (V2, V21)                                  # V2.1 is V2 plus the Phase 2A additions
    admit = v2 or strict
    if not admit and (units or region_specs or accept_xrefs):
        raise SystemExit("--units / --region / --accept-missing-xref are reviewer inputs of the admission: use them "
                         "with --method ARCH_TAKEOFF_V2 or --strict-admission")
    facts = AM.validate_facts(facts)
    path = Path(drawing)
    sha = hashlib.sha256(path.read_bytes()).hexdigest()
    docs = [{"file": path.name, "sha256": sha}]
    rev = revision_set_sha256(docs)
    pid = project_id or (facts or {}).get("project_id") or "new project"
    report = C = None
    dims_read = None
    if admit:
        import ezdxf
        from engine.source import discovery as DS
        from tools import arch_discovery as AD
        report = DS.new_report([], method=method + ("+STRICT_ADMISSION" if strict and not v2 else ""),
                               reviewer_inputs={"units": units, "regions": list(region_specs or ()),
                                                "accepted_missing_xrefs": sorted(accept_xrefs or ())})
        if intake is None:
            intake = UI.read(str(path))
        try:
            doc = ezdxf.readfile(str(path))
        except Exception as ex:                                       # noqa: BLE001 - an unreadable drawing stops
            report["documents"] = [{"file": path.name, "sha256": sha, "format": "DXF", "parse_status": "FAILED"}]
            DS.set_stage(report, "0_intake", [DS.finding(DS.FATAL, "UNREADABLE_DRAWING", str(ex)[:300])])
            DS.gate(report)
            raise DS.AdmissionBlocked(report) from None
        report["documents"] = [AD.documents_record(path, doc, sha)] + list(extra_documents)
        unit_used, C = AD.admit_intake(report, path, intake, doc, units=units, accept_xrefs=accept_xrefs)
        SH = AD.shapes(doc)
        if v21:                                                   # P2-09a: the authored dimensions (read-only)
            from tools import arch_dimensions as ADIM
            dims_read = ADIM.read_doc(doc)
        if strict and not v2:
            st = report["stages"]["4_units"]
            DS.set_stage(report, "4_units", st["findings"] + DS.legacy_tolerance_findings(unit_used),
                         **{k: v for k, v in st.items() if k not in ("state", "findings")})
        if admission_findings:
            st = report["stages"]["0_intake"]
            DS.set_stage(report, "0_intake", st["findings"] + list(admission_findings),
                         **{k: v for k, v in st.items() if k not in ("state", "findings")})
        if DS.stops(report):
            DS.gate(report)
            raise DS.AdmissionBlocked(report)
        if unit_used != intake.get("unit_m"):
            intake = dict(intake, unit_m=unit_used)
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
    fills_merged = None
    if v21 and admit:
        # P2-05: the discovery reads every fill at every depth in world coordinates, with the layer a layer-0 block
        # content inherits from its INSERT (the plan reader misses hatches two or more levels deep or in a later MINSERT
        # cell, SOLID / TRACE, and keeps layer 0); V2.1 gives all of them to the plan as fills too (column evidence; a
        # fill the plan reader also read only repeats it). No segment is added and nothing drawn is moved.
        extra = [{"id": f_["fill_id"], "layer": f_["layer"], "ring": f_["ring"], "rings": [f_["ring"]], "islands": [],
                  "owner": None, "source": f"DISCOVERY_FILL:{f_['kind']}:depth {f_['depth']}"}
                 for f_ in SH["fills"] if len(f_["ring"]) >= 3]
        E = dict(E, hatches=E["hatches"] + extra)
        SH = dict(SH, fills=[dict(f_, unread_by_plan_reader=False, read_in_v2_1=True)
                             if f_.get("unread_by_plan_reader") and len(f_["ring"]) >= 3 else f_ for f_ in SH["fills"]])
        fills_merged = {"fills": len(extra), "by_kind": dict(Counter(x["source"].split(":")[1] for x in extra))}
    u = E["unit_m"]
    split = "EMPTY_BANDS" if v2 else "TITLE_MIDPOINTS"
    tol = "UNIT_RELATIVE" if v2 else "LEGACY"
    if region_specs:
        P = AD.override_regions(region_specs)
    else:
        P = AP.plan_regions(E, split=split, frames_from_lines_fallback=v2)
    if admit:
        AD.admit_regions(report, E, P, C, split=split, overrides=bool(region_specs))
        if DS.stops(report):
            DS.gate(report)
            raise DS.AdmissionBlocked(report)
    regs = P["regions"]
    ents_of = {r["region_id"]: AP.region_entities(E, r["box"]) for r in regs}
    frame_sides = {}
    if v2 and not region_specs:
        # S6: the sheet frame's own sides are never plan geometry (a frame drawn as lines on the wall layer would
        # otherwise close the wall network along the frame); a cut along an empty band has no segment on it
        for r in regs:
            b = r["box"]
            eps = max(1e-3 / u, max(b[2] - b[0], b[3] - b[1]) * 1e-6)
            segs = ents_of[r["region_id"]]["segments"]
            keep = [s_ for s_ in segs if not AP._on_frame_side(s_["a"], s_["b"], b, eps)]
            frame_sides[r["region_id"]] = len(segs) - len(keep)
            ents_of[r["region_id"]] = dict(ents_of[r["region_id"]], segments=keep)
    level = {r["region_id"]: AR.dominant_level(ents_of[r["region_id"]]["texts"]) for r in regs}
    lines, mats, comps, unresolved, rooms, openings, regions, walls_of = [], [], [], [], [], [], [], []
    floor_areas = []
    v2_unresolved, coverage, column_ev, arc_recs, unread_ev = [], [], [], [], []
    geom_of = {}
    if v21:
        from engine.source import robust_geometry as RG
        geom_of = {r["region_id"]: RG.Geometry(u) for r in regs}
    roles_of = {r["region_id"]: AP.layer_roles(ents_of[r["region_id"]], u, override=layer_roles, tol=tol,
                                               **({"geom": geom_of[r["region_id"]]} if v21 else {}))
                for r in regs}
    spaces_of = {r["region_id"]: AR.spaces(ents_of[r["region_id"]], roles_of[r["region_id"]]["roles"], u,
                                           region_id=r["region_id"], tol=tol,
                                           **({"geom": geom_of[r["region_id"]]} if v21 else {}))
                 for r in regs if roles_of[r["region_id"]]["state"] != "BLOCKED"}
    # one stair drawn on two plans: the plans are aligned on their column grid, and a flight lying over a flight of
    # the plan below is counted once (the repeat is exposure until a reviewer says which it is)
    stacked = sorted((r for r in regs if r["region_id"] in spaces_of and not r.get("warning")), key=lambda r: r["order"])
    # a small doorless unlabelled footprint repeated on the other plans (aligned on the column grid) is a shaft (S4)
    shafts = AR.stacked_shafts([(r["floor"], spaces_of[r["region_id"]]["column_boxes"],
                                 spaces_of[r["region_id"]]["faces"], spaces_of[r["region_id"]]["openings_by_id"])
                                for r in stacked], u)
    cross = AR.cross_plan_flights([(r["floor"], spaces_of[r["region_id"]]["column_boxes"],
                                    [fl for f in spaces_of[r["region_id"]]["spaces"]
                                     for fl in (f.get("symbols_inside") or {}).get("stair_flights") or ()],
                                    AR.void_marks(ents_of[r["region_id"]], spaces_of[r["region_id"]]["faces"]))
                                   for r in stacked], u)
    # an outlined void is open to the plan below: the space under it is double height (no ceiling at its level) (S5)
    double_height = AR.voids_above([(r["floor"], spaces_of[r["region_id"]]["column_boxes"],
                                     spaces_of[r["region_id"]]["faces"], spaces_of[r["region_id"]].get("voids"),
                                     ents_of[r["region_id"]]["segments"])
                                    for r in stacked], u)
    col_layers = sorted({lay for v in roles_of.values() for lay, ro in v["roles"].items() if ro == AP.COLUMN})
    door_floors, door_texts, door_face_texts = [], {}, {}
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
        if v2 and not region_specs:
            rec["frame_side_segments_dropped"] = frame_sides.get(rid, 0)
        if L["state"] == "BLOCKED":
            rec["stage_state"] = "BLOCKED_AT_LAYER_ROLES"
            unresolved.append({"room_id": "-", "floor": floor, "item": "plan region " + rid,
                               "reason": L.get("why") or "NO_WALL_LAYER: no layer behaves like walls"})
            regions.append(rec)
            continue
        S = spaces_of[rid]
        S["walls"] = AW.walls(ents, L["roles"], u, S["faces"], S["openings"], columns=S["column_boxes"],
                              **({"geom": geom_of[rid]} if v21 else {}))
        M = AM.measure(S, floor=floor, project_id=pid, revision_set_sha256=rev, facts=facts,
                       floor_above_level_m=above, floor_level_m=level[rid], documents=docs)
        X = AM.materials(M, facts)
        ref = (reference_areas or {}).get(floor)
        rec["repairs"] = {"counts": dict(Counter(x["kind"] + ":" + x["rule"] for x in S.get("repairs") or ())),
                          "items": S.get("repairs") or [], "zones": S.get("zones") or [],
                          "never": "a drawn entity moved, extended, snapped or deleted"}
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
        fa = AF.reconcile(S, M["rooms"], M["lines"], floor=floor)
        keep = {x for a_ in (S.get("zoning") or {}).get("attached") or () for x in a_["cells"]} | \
            {x for s_ in (S.get("zoning") or {}).get("shared") or () for x in s_["cells"]}
        fa.update(region_id=rid, reference=rec.get("reference"), voids=S.get("voids") or [],
                  cell_outlines=[c for c in S.get("cells") or () if c["face_id"] in keep],
                  zoning={k: (S.get("zoning") or {}).get(k) for k in ("attached", "shared", "opening_line_splits")},
                  physical_regions=(S.get("zoning") or {}).get("physical_regions") or [],
                  zones=S.get("zones") or [],
                  double_height=[d for d in double_height if d["onto"] == floor],
                  zone_lines=[ln for f in S["faces"] for ln in (f.get("zone") or {}).get("lines") or ()])
        floor_areas.append(fa)
        in_space = {i for f in S["faces"] for i in f.get("label_text_ids") or ()}
        for v in S.get("voids") or ():
            if v.get("state") == "VOID_EXTENT_UNRESOLVED" and v.get("label_text_id") not in in_space:
                unresolved.append({"room_id": "-", "floor": floor, "item": "VOID",
                                   "reason": "VOID_EXTENT_UNRESOLVED: a VOID word outside every closed space has no "
                                             "outline (X-marked rectangle / void symbol); no floor is deducted"})
        rec["floor_areas"] = {k: fa[k] for k in ("gross_floor_plate_m2", "internal_physical_floor_m2", "external_m2")}
        if admit:
            # S6 entity completeness: the fills read independently of the plan reader against the measured columns,
            # and the door blocks inserted at a non-uniform scale (review flags; V1 strict: the report only)
            from engine.source import arch_completeness as AC
            column_ev.append(AC.column_evidence(S, M, SH["fills"], reg["box"], floor, column_layers=col_layers))
            arc_recs += AC.distorted_arc_blocks(SH["nonuniform_arc_inserts"], reg["box"], floor)
            unread_ev.append(AC.unread_fills(S, M, SH["fills"], reg["box"], floor))
        if v2:
            # S6: every strip reviewed on its own, the surfaces V1 leaves silent get their RFI, then the coverage of
            # this plan in three separate views (physical regions / functional spaces / finish zones)
            from engine.source import arch_completeness as AC
            ctx = {"project_id": pid, "revision_set_sha256": rev, "documents": docs}
            strips = AC.strip_register(S, floor)
            s_lines, s_unres = AC.strip_lines(ctx, strips, floor)
            r_lines, r_unres = AC.surface_rfis(ctx, M, floor, facts, level[rid], above)
            M["lines"] = M["lines"] + s_lines + r_lines
            here = [x for x in unresolved if x.get("floor") == floor]
            cov = AC.coverage(S, M, strips, M["lines"], M["unresolved"] + X["unresolved"] + here + s_unres + r_unres,
                              floor)
            v2_unresolved += [(x, rec) for x in s_unres + r_unres + AC.column_records(column_ev[-1])
                              + [a_ for a_ in arc_recs if a_["floor"] == floor] + unread_ev[-1][1]]
            coverage.append(cov)
            by_cls = Counter()
            for s_ in strips:
                by_cls[s_["class"]] += s_["area_m2"]
            fa.update(strips=strips, coverage={"gate": cov["gate"], "by_category": cov["physical_regions"]["by_category"],
                                               "unaccounted": len(cov["unaccounted"])},
                      doorway_strips_by_class_m2={k: round(v, 6) for k, v in sorted(by_cls.items())},
                      doorway_strips_note="DOORWAY_STRIPS (in internal_physical_floor_m2, as V1) split by class: "
                                          "WINDOW_REVEAL strips have no established floor status (sill not in the "
                                          "plan); every strip is a BLOCKED_RFI line, none is a floor finish quantity")
            rec["coverage_gate"] = cov["gate"]
        if v21:
            # Phase 2A P2-04: every door swing of the floor in exactly one door element, its class and widths
            from engine.source import door_model as DMOD
            walls_here = [lay for lay, ro in L["roles"].items() if ro == AP.WALL]
            door_floors.append((floor, DMOD.floor_model(S, M["rooms"], ents, u, floor, wall_layers=walls_here,
                                                        origin=(reg["box"][0], reg["box"][1]), facts=facts)))
            tx = {t_["id"]: t_ for t_ in ents["texts"]}
            door_texts[floor] = ents["texts"]
            door_face_texts[floor] = {f_["face_id"]: [tx[i_] for i_ in f_.get("label_text_ids") or () if i_ in tx]
                                      for f_ in S["faces"]}
        for rm in M["rooms"]:
            rm["region_id"] = rid
        rooms += M["rooms"]
        openings += M["openings"]
        lines += M["lines"]
        mats += X["materials"]
        comps += X["comparisons"]
        unresolved += M["unresolved"] + X["unresolved"]
        regions.append(rec)
    doors = None
    if v21:
        doors, lines, door_unres, door_cov = _v21_doors(door_floors, door_texts, door_face_texts, regs, spaces_of,
                                                         lines, u, facts, pid, rev, docs)
        unresolved += door_unres
        coverage += door_cov
    by_room = {r["room_id"]: r for r in rooms}
    reg_of = {r["floor"]: r for r in regions}
    unresolved = [AM.flag(u_, drawing=path.name, region=reg_of.get(u_.get("floor")), room=by_room.get(u_.get("room_id")))
                  for u_ in unresolved]
    run = {"policy": ARCH_POLICY_ID, "method": method, "drawing": docs[0], "revision_set_sha256": rev,
           "project_id": pid, "unit_m": u, "insunits": E.get("insunits"), "intake_findings": E.get("intake_findings"),
           "hatch_reader": {"hatches": len(hs), "with_islands": sum(1 for h in hs if h["islands"]),
                            "inside_blocks": sum(1 for h in hs if h["owner"])},
           "arch_reader": A["report"], "cross_plan_stairs": cross, "stacked_shafts": shafts,
           "double_height": double_height,
           "facts": {"schema": (facts or {}).get("schema"), "given": sorted(k for k in (facts or {}) if k != "schema")},
           "layer_roles_override": layer_roles or {}, "policies": {"plan": AP.policy_record(), "rooms": AR.policy_record(),
                                                                    "measure": AM.policy_record(),
                                                                    "walls": AW.policy_record(),
                                                                    "floor_areas": AF.policy_record()}}
    if v2:
        from engine.source import arch_completeness as AC
        unresolved += [AC.flag(x, drawing=path.name, region=r_) for x, r_ in v2_unresolved]
        # the non-stopping admission findings travel with the BOQ as flags (REVIEW / WARNING / later BLOCKED_ITEM)
        for f_ in DS.all_findings(report):
            if f_["level"] != DS.FATAL:
                unresolved.append(AC.flag({"room_id": "-", "floor": "-", "item": f"ADMISSION:{f_['code']}",
                                           "reason": f"{f_['level']}: {f_['message']}"}, drawing=path.name))
        run.update(policy=ARCH_POLICY_ID_V2, s6={
            "tolerance_policy": tol, "region_split": split, "frames_from_lines": bool(P.get("frames_from_lines")),
            "region_overrides": list(region_specs or ()), "unit_m_used": u, "admission": report["gates"] or None,
            "completeness": {c["floor"]: c["gate"] for c in coverage}})
        run["policies"].update(completeness=AC.policy_record(), discovery=DS.policy_record())
    if v21:
        run.update(policy=ARCH_POLICY_ID_V21)
        run["policies"]["robust_geometry"] = RG.policy_record()
        run["v2_1"] = {"geometry": {rid: {k: v for k, v in g.report().items() if k != "records"}
                                    for rid, g in geom_of.items()}, "fills_merged": fills_merged}
    if admit:
        _finish_discovery(report, E, facts, regions, lines, coverage if v2 else None,
                          entity_checks={"column_evidence": column_ev, "door_symbols": arc_recs,
                                         "unread_fills": [u_[0] for u_ in unread_ev], "shape_errors": SH["errors"]})
    room_boq = {"project_id": pid, "lines": lines, "materials": mats, "comparisons": comps, "unresolved": unresolved,
                "assumptions": [], "geometry_source": f"architectural plan DXF {path.name} ({method})"}
    arch = {"run": run, "regions": regions, "other_frames": P["other_frames"], "rooms": rooms, "openings": openings,
            "walls": walls_of, "reference_areas": reference_areas or {}, "floor_areas": floor_areas}
    if admit:
        arch["discovery"] = report
    if v21:
        from engine.source import door_model as DMOD
        arch["geometry"] = {rid: g.report() for rid, g in geom_of.items()}
        arch["doors"] = doors
        arch["door_rows"] = DMOD.schedule_rows(doors)          # the workbook takes rows (it imports no engine.source)
        arch["door_classes"] = list(DMOD.RELEASED_CLASSES)
        arch["lift_openings"] = doors.get("lift_openings") or []
        # P2-08a: the read-only surface ledger over the finished lines (it changes no line and no exit code)
        from engine.source import surface_ledger as SL
        arch["dimensions"] = _v21_dimensions(dims_read, regs, spaces_of, doors, u)
        run["v2_1"]["dimensions"] = {k: arch["dimensions"][k] for k in ("counts", "checks_by_state", "door_evidence")}
        from engine.source import dimension_evidence as DEV
        run["policies"]["dimension_evidence"] = DEV.policy_record()
        arch["ledger"] = SL.ledger(lines, rooms, openings, unresolved, method=method, doors=doors, walls=walls_of)
        run["v2_1"]["ledger"] = {"table": arch["ledger"]["table"], "summary": arch["ledger"]["summary"]}
        run["policies"]["surface_ledger"] = SL.policy_record()
        run["v2_1"]["doors"] = {"summary": doors["summary"], "main_entrance": doors["main_entrance"]["state"],
                                "conservation_ok": doors["conservation_ok"],
                                "findings": dict(Counter(f_["code"] for f_ in doors["findings"]))}
        from engine.source import door_model as DMOD
        run["policies"]["doors"] = DMOD.policy_record()
    if v2:
        arch["coverage"] = coverage
        if any(c["gate"] != "PASS" for c in coverage):
            raise CompletenessFailed(room_boq, arch, E)
    return room_boq, arch, E


def _finish_discovery(report, E, facts, regions, lines, coverage, entity_checks=None):
    """S6: the discovery stages after admission - geometry readiness (the K2 findings and the entity completeness
    checks), the vertical model (heights only from a source or an owner fact), finish zones (the coverage gate) and BOQ
    readiness (lines by state)."""
    from engine.source import discovery as DS
    k2 = E.get("intake_findings") or {}
    ec = entity_checks or {}
    geo = [DS.finding(DS.WARNING, "K2_" + code, f"{n} x {code} (K2 kernel finding)", count=n)
           for code, n in sorted(k2.items())]
    for ce in ec.get("column_evidence") or ():
        if ce["unmeasured"]:
            geo.append(DS.finding(DS.REVIEW, "COLUMN_EVIDENCE_NOT_MEASURED",
                                  f"{ce['floor']}: {len(ce['unmeasured'])} of {ce['member_sized']} filled member-sized "
                                  f"shape(s) are not measured as columns ({ce['measured_columns']} columns measured; "
                                  f"column layers {ce['column_layers'] or 'none found: every layer checked'}): "
                                  "a lost column (nested block, MINSERT, SOLID, rotated / exploded outline, too few to "
                                  "class the layer) or a hatched wall piece / fixture; the rooms named are flagged",
                                  floor=ce["floor"], rooms=sorted({x["room_id"] or "-" for x in ce["unmeasured"]}),
                                  items=ce["unmeasured"][:50]))
    for uf in ec.get("unread_fills") or ():
        if uf["unread_fills"]:
            geo.append(DS.finding(DS.REVIEW, "FILLS_NOT_READ_IN_PLAN",
                                  f"{uf['floor']}: {uf['unread_fills']} fill(s) inside the plan are not read by the plan "
                                  "reader (hatches two or more block levels deep or in a later MINSERT cell, SOLID "
                                  "fills): columns, finish zones or areas they draw are missing; the rooms named are "
                                  "flagged", floor=uf["floor"], rooms=uf["rooms"]))
    for ar in ec.get("door_symbols") or ():
        geo.append(DS.finding(DS.REVIEW, "DOOR_SYMBOLS_DISTORTED", f"{ar['floor']}: {ar['reason']}", floor=ar["floor"]))
    for er in ec.get("shape_errors") or ():
        geo.append(DS.finding(DS.WARNING, "SHAPE_READ_ERROR", f"block {er['block']}: {er['error']}", **er))
    DS.set_stage(report, "6_geometry_readiness", geo,
                 measured_regions=[r["region_id"] for r in regions if r.get("stage_state") == "MEASURED"],
                 blocked_regions=[r["region_id"] for r in regions if r.get("stage_state") != "MEASURED"],
                 column_evidence=[{k: v for k, v in ce.items() if k != "unmeasured"} | {"unmeasured": len(ce["unmeasured"])}
                                  for ce in ec.get("column_evidence") or ()])
    given = sorted(k for k in ("wall_heights", "height_components", "opening_heights", "stairs") if (facts or {}).get(k))
    DS.set_stage(report, "7_vertical_model",
                 [] if given else [DS.finding(DS.BLOCKED_ITEM, "NO_SECTION_SOURCE", "no section, schedule or facts "
                                              "file gives the heights: every height-dependent quantity is BLOCKED; "
                                              "plan level texts are candidates only")],
                 state="PROVISIONAL" if given else None, facts_given=given,
                 level_candidates={r["floor"]: r.get("level_m") for r in regions})
    if coverage is not None:
        un = [dict(x, floor=c["floor"]) for c in coverage for x in c["unaccounted"]]
        DS.set_stage(report, "9_finish_zones",
                     [DS.finding(DS.FATAL, "SURFACE_UNACCOUNTED", f"{len(un)} region part(s) / surface(s) with no line, "
                                 "exclusion or RFI", items=un[:50])] if un else [],
                     gates={c["floor"]: c["gate"] for c in coverage})
    fam = {}
    for ln in lines:
        fam.setdefault(ln["item_code"], Counter())[ln["evidence_state"]] += 1
    DS.set_stage(report, "10_boq_readiness", [], state="PROVISIONAL",
                 families={k: dict(sorted(v.items())) for k, v in sorted(fam.items())},
                 note="MACHINE_ONLY: nothing is reviewed or quotation-ready")
    DS.gate(report)


def _dxf_of(drawing, out, conversions, strict=False):
    """a DWG through the DWG adapter (an external converter, run as a separate program) into OUT/converted; a DXF as
    it is. A failed or impossible conversion stops the run with its record (OUT/DWG_CONVERSION.json)."""
    p = Path(drawing)
    if p.suffix.lower() != ".dwg":
        return str(p)
    from tools import dwg_adapter as DA
    rec = DA.convert(p, out / "converted", strict=strict)
    conversions.append(rec)
    if strict and rec["state"] != "CONVERTED":
        raise _ConversionBlocked(rec)
    if rec["state"] != "CONVERTED":
        out.mkdir(parents=True, exist_ok=True)
        (out / "DWG_CONVERSION.json").write_text(_j({"conversions": conversions}), encoding="utf-8")
        raise SystemExit(f"DWG_CONVERSION_BLOCKED: {p.name}: {rec['remedy']}")
    return rec["dxf"]


class _ConversionBlocked(Exception):
    def __init__(self, rec):
        super().__init__(rec.get("remedy") or "DWG conversion blocked")
        self.rec = rec


def _v21_doors(door_floors, door_texts, door_face_texts, regs, spaces_of, lines, u, facts, pid, rev, docs):
    """ARCH_TAKEOFF_V2.1: the building door model; the ARCH.DOOR opening counts are replaced by the owner door
    classes (released doors only), lift entrances leave the ordinary opening lines; every finding becomes a flag; a
    swing without exactly one element fails the floor's coverage gate (exit 3)."""
    from engine.source import arch_measure as AM
    from engine.source import door_model as DMOD
    from engine.source import rule_store as RS
    measured = [r for r in regs if r["region_id"] in spaces_of and not r.get("warning")]
    entrance = min(measured, key=lambda r: r["order"])["floor"] if measured else None
    model = DMOD.building_model(door_floors, door_texts, door_face_texts, u, entrance_floor=entrance, facts=facts)
    lift_ops = {o_["opening_id"] for o_ in model.get("lift_openings") or ()}
    keep = [ln for ln in lines if ln["item_code"] != "ARCH.DOOR" and not
            (ln["item_code"] == "ARCH.PASSAGE" and ln["physical_element"] in lift_ops)]
    ctx = {"project_id": pid, "revision_set_sha256": rev, "documents": docs}
    new = DMOD.boq_lines(ctx, model, rule_set=AM.RULE_SET, rule_set_digest=RS.rule_set(AM.RULE_SET)["digest"])
    unres = []
    blocked_h = Counter(f_["floor"] for f_ in model["findings"] if f_["code"] == "DOOR_HEIGHT_MISSING")
    for fl, n in sorted(blocked_h.items()):
        unres.append({"room_id": "-", "floor": fl, "item": "DOOR HEIGHTS",
                      "reason": f"MISSING_SOURCE: {n} released door(s) without a height (door schedule / elevation / "
                                "section / facts opening_heights): count and width kept, height and area BLOCKED"})
    for f_ in model["findings"]:
        if f_["code"] != "DOOR_HEIGHT_MISSING":
            unres.append({"room_id": "-", "floor": f_.get("floor") or "-", "item": f"DOORS:{f_['code']}",
                          "reason": f"{f_['level']}: {f_['message']}"})
    cov = [{"floor": c_["floor"], "gate": "FAIL", "kind": "DOOR_CONSERVATION",
            "unaccounted": [{"kind": "DOOR_SWING", "swing": s_} for s_ in c_["without_element"] + c_["in_two_elements"]]}
           for c_ in model["conservation"] if not c_["ok"]]
    return model, keep + new, unres, cov


def _v21_dimensions(dims_read, regs, spaces_of, doors, u):
    """ARCH_TAKEOFF_V2.1: the dimension census and the read-only cross-check of every measured plan; usable dimensions
    across a provisional door's closure are attached to it as DIMENSION evidence (no promotion: owner decision)."""
    from engine.source import dimension_evidence as DEV
    from engine.source import door_model as DMOD
    if dims_read is None:
        return {"counts": None, "checks_by_state": {}, "door_evidence": 0, "regions": [], "findings": [],
                "note": "no drawing document read (dimensions not available)"}
    boxes = [(r["floor"], r["box"]) for r in regs]
    cen = DEV.census(dims_read["dimensions"], dims_read["header_dimlfac"], u, boxes)
    out, findings, ev = [], [], []
    for r in regs:
        if r["region_id"] not in spaces_of:
            continue
        here = [d for d in cen["dimensions"] if d["where"] == r["floor"]]
        els = [e for e in (doors or {}).get("elements") or () if e["floor"] == r["floor"]]
        x = DEV.crosscheck(here, spaces_of[r["region_id"]]["openings"], u, doors=els)
        out.append({"floor": r["floor"], "dimensions": len(here), "usable": sum(1 for d in here if d["usable"]),
                    "checks": x["checks"], "counts": x["counts"], "door_evidence": x["door_evidence"]})
        findings += [dict(f, floor=r["floor"]) for f in x["findings"]]
        ev += x["door_evidence"]
    if doors is not None:
        DMOD.attach_dimensions(doors["elements"], ev, promote=False)
    by_state = {}
    for reg in out:
        for k, v in reg["counts"].items():
            by_state[k] = by_state.get(k, 0) + v
    return {"counts": cen["counts"], "checks_by_state": by_state, "door_evidence": len(ev), "regions": out,
            "findings": findings, "not_read": dims_read["not_read"], "header_dimlfac": dims_read["header_dimlfac"],
            "dimensions": [{k: d.get(k) for k in ("handle", "type", "where", "dimlfac", "dimlfac_source", "usable",
                                                   "why_not", "geometry_mm", "shown_value", "text_overridden",
                                                   "duplicate", "measurement_matches")} for d in cen["dimensions"]]}


def v21_files(arch):
    """the ARCH_TAKEOFF_V2.1 outputs (Phase 2A); none for V1 / V2."""
    if arch.get("geometry") is None:
        return {}
    run = arch["run"]
    files = {"ARCH_GEOMETRY_DECISIONS.json": _j({"run": run, "regions": arch["geometry"]})}
    if arch.get("doors") is not None:
        from engine.source import door_model as DMOD
        files["DOOR_SCHEDULE.json"] = _j({"run": run, "doors": arch["doors"]})
        files["DOOR_SCHEDULE.csv"] = _csv(DMOD.schedule_rows(arch["doors"]), DMOD.SCHEDULE_COLUMNS)
    if arch.get("dimensions") is not None:
        files["DIMENSION_CROSSCHECK.json"] = _j({"run": run, "dimensions": arch["dimensions"]})
    if arch.get("ledger") is not None:
        from engine.source import surface_ledger as SL
        files["SURFACE_LEDGER.json"] = _j({"run": run, "ledger": arch["ledger"]})
        files["SURFACE_LEDGER.csv"] = _csv(arch["ledger"]["records"], SL.CSV_COLUMNS)
    return files


PUBLISHED = ("BOQ_LINES.json", "BOQ_LINES.csv", "MATERIAL_RESULTS.json", "COVERAGE.json", "COVERAGE.csv",
             "RUN_RULES.json", "ARCH_PLAN.json", "ARCH_ROOMS.json", "ARCH_OPENINGS.json", "ARCH_WALLS.json",
             "UNRESOLVED.json", "ARCH_FLOOR_AREAS.json", "URBAN_ROOM_BOQ.xlsx", "FINISH_COVERAGE.json",
             "DRAWING_DISCOVERY.json", "ADMISSION_BLOCKED.json", "COMPLETENESS_FAILED.json",
             "ARCH_GEOMETRY_DECISIONS.json", "DOOR_SCHEDULE.json", "DOOR_SCHEDULE.csv",
             "SURFACE_LEDGER.json", "SURFACE_LEDGER.csv", "DIMENSION_CROSSCHECK.json")


def _supersede(out):
    """S6: before a run that publishes no BOQ, the BOQ files an earlier run left in OUT are moved to
    OUT/SUPERSEDED_<n> (never deleted), so a stale BOQ can never be read as this run's."""
    old = [n for n in PUBLISHED if (out / n).exists()] + sorted(p.name for p in out.glob("OVERLAY_*.svg"))
    if not old:
        return None
    k = 1
    while (out / f"SUPERSEDED_{k}").exists():
        k += 1
    dst = out / f"SUPERSEDED_{k}"
    dst.mkdir(parents=True)
    for n in old:
        (out / n).rename(dst / n)
    return {"moved_to": dst.name, "files": old}


def _blocked(out, report, conversions, *, code, what, extra=None):
    """S6: publish the evidence of a run that stops (no BOQ): the discovery report, the stopping findings with their
    remedies, the conversions; exit code 2 (admission) or 3 (completeness)."""
    from engine.source import discovery as DS
    out.mkdir(parents=True, exist_ok=True)
    moved = _supersede(out)
    if not report.get("gates"):
        DS.gate(report)
    (out / "DRAWING_DISCOVERY.json").write_text(_j(report), encoding="utf-8")
    if conversions:
        (out / "DWG_CONVERSION.json").write_text(_j({"conversions": conversions}), encoding="utf-8")
    st = DS.stops(report) if code == DS.EXIT_ADMISSION_BLOCKED else []
    rec = {"state": what, "exit_code": code, "boq_published": False,
           "stopping_findings": [{k: f[k] for k in ("stage", "level", "code", "message")} for f in st],
           "reviewer_inputs": report.get("reviewer_inputs"), "documents": report.get("documents"),
           "superseded_earlier_outputs": moved, **(extra or {})}
    name = "ADMISSION_BLOCKED.json" if code == DS.EXIT_ADMISSION_BLOCKED else "COMPLETENESS_FAILED.json"
    (out / name).write_text(_j(rec), encoding="utf-8")
    print(json.dumps({"state": what, "exit_code": code, "stopping": [f"{f['stage']}:{f['code']}" for f in st],
                      "outputs": sorted(p.name for p in out.iterdir() if p.is_file())}, indent=1))
    return code


def cmd_arch(a):
    from engine.source import discovery as DS
    facts = json.loads(Path(a.facts).read_text(encoding="utf-8")) if a.facts else None
    roles = _kv(a.layer_roles, "--layer-roles")
    refs = {k: float(v) for k, v in _kv(a.reference_areas, "--reference-areas").items()}
    out = Path(a.out)
    conversions = []
    v2 = a.method in (V2, V21)
    admit = v2 or a.strict_admission
    if not admit and (a.units or a.region or a.accept_missing_xref):
        raise SystemExit("--units / --region / --accept-missing-xref are reviewer inputs of the admission: use them "
                         "with --method ARCH_TAKEOFF_V2 or --strict-admission")
    if a.structural and not a.conventions:
        print("WARNING: --structural without --conventions: route G runs with its default convention set "
              f"({Path(_m2_default()).stem}); the M8 scope pass (SCOPE_FROM_FINDINGS) needs "
              "URBAN_M8_GENERIC_CONVENTIONS_V6, so it is OFF for this run", file=sys.stderr)
    pre = []
    if admit:
        inputs = [("plan", Path(a.drawings[0]))] + ([("structural", Path(a.structural))] if a.structural else [])
        shas = {k: hashlib.sha256(p.read_bytes()).hexdigest() for k, p in inputs}
        if v2 and a.structural and not a.conventions:
            pre.append(DS.finding(DS.FATAL, "STRUCTURAL_CONVENTIONS_REQUIRED",
                                  "ARCH_TAKEOFF_V2 with --structural needs an explicit --conventions profile (the route "
                                  "G defaults differ by entry point and leave the M8 scope pass off)"))
        if a.structural and shas["plan"] == shas["structural"]:
            pre.append(DS.finding(DS.FATAL, "PLAN_AND_STRUCTURAL_ARE_ONE_FILE",
                                  "the architectural plan and the structural drawing are the same file (sha256)",
                                  sha256=shas["plan"]))
        elif a.structural and Path(a.drawings[0]).name.lower() == Path(a.structural).name.lower():
            pre.append(DS.finding(DS.WARNING, "SAME_FILE_NAME", "the plan and the structural drawing have the same "
                                  "file name (different content): their conversions are kept apart by content hash",
                                  name=Path(a.structural).name))
        inputs_rec = [{"role": k, "file": p.name, "sha256": shas[k]} for k, p in inputs]
    try:
        try:
            plan = _dxf_of(a.drawings[0], out, conversions, strict=admit)
            structural = _dxf_of(a.structural, out, conversions, strict=admit) if a.structural else None
        except _ConversionBlocked as ex:
            report = DS.new_report(inputs_rec, method=a.method)
            DS.set_stage(report, "0_intake", pre + [DS.finding(
                DS.FATAL, "DWG_CONVERSION_BLOCKED", ex.rec.get("remedy") or "the DWG was not converted",
                dwg=ex.rec.get("dwg"), dwg_sha256=ex.rec.get("dwg_sha256"), converter=ex.rec.get("converter"))])
            raise DS.AdmissionBlocked(report) from None
        if any(f["level"] == DS.FATAL for f in pre):
            report = DS.new_report(inputs_rec, method=a.method)
            DS.set_stage(report, "0_intake", pre)
            raise DS.AdmissionBlocked(report)
        room, arch, E = arch_compute(plan, method=a.method, facts=facts, layer_roles=roles or None,
                                     reference_areas=refs, project_id=a.project, strict=a.strict_admission,
                                     units=a.units, region_specs=a.region, accept_xrefs=tuple(a.accept_missing_xref or ()),
                                     extra_documents=[d for d in (inputs_rec if admit else ()) if d["role"] != "plan"],
                                     admission_findings=pre)
    except DS.AdmissionBlocked as ex:
        return _blocked(out, ex.report, conversions, code=DS.EXIT_ADMISSION_BLOCKED, what="ADMISSION_BLOCKED")
    except CompletenessFailed as ex:
        diag = out / "diagnostics"
        diag.mkdir(parents=True, exist_ok=True)
        (diag / "FINISH_COVERAGE.json").write_text(_j({"run": ex.arch["run"], "floors": ex.arch["coverage"]}),
                                                   encoding="utf-8")
        (diag / "BOQ_LINES_UNPUBLISHED.json").write_text(BL.dumps(ex.room_boq["lines"]), encoding="utf-8")
        (diag / "UNRESOLVED_UNPUBLISHED.json").write_text(_j({"unresolved": ex.room_boq["unresolved"]}),
                                                          encoding="utf-8")
        return _blocked(out, ex.arch["discovery"], conversions, code=DS.EXIT_COMPLETENESS_FAILED,
                        what="COMPLETENESS_FAILED",
                        extra={"unaccounted": [dict(x, floor=c["floor"]) for c in ex.arch["coverage"]
                                               for x in c["unaccounted"]][:200],
                               "diagnostics": "diagnostics/ (the computed, unpublished lines and the coverage)"})
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
    if admit:
        (out / "DRAWING_DISCOVERY.json").write_text(_j(arch["discovery"]), encoding="utf-8")
        res["files"].append("DRAWING_DISCOVERY.json")
    if v2:
        (out / "FINISH_COVERAGE.json").write_text(_j({"run": arch["run"], "floors": arch["coverage"]}),
                                                  encoding="utf-8")
        res["files"].append("FINISH_COVERAGE.json")
    for name, text in v21_files(arch).items():               # ARCH_TAKEOFF_V2.1 only (empty otherwise)
        (out / name).write_text(text, encoding="utf-8")
        res["files"].append(name)
    svgs = []
    if not a.no_svg:
        from tools import arch_overlay as AO
        for reg in arch["regions"]:
            name = f"OVERLAY_{reg['floor']}.svg"
            (out / name).write_text(AO.svg(E, reg, [r for r in arch["rooms"] if r.get("region_id") == reg["region_id"]],
                                           [o for o in arch["openings"] if o["floor"] == reg["floor"]],
                                           walls=next((w for w in arch.get("walls") or () if
                                                       w["region_id"] == reg["region_id"]), None),
                                           floor_area=next((f for f in arch.get("floor_areas") or () if
                                                            f["region_id"] == reg["region_id"]), None)),
                                    encoding="utf-8")
            svgs.append(name)
    ev = Counter(ln["evidence_state"] for ln in room["lines"])
    print(json.dumps({"method": a.method, "regions": [{"floor": r["floor"], "state": r["stage_state"],
                                                        "rooms": r.get("space_counts"), "lines": r.get("lines"),
                                                        "reference": r.get("reference")} for r in arch["regions"]],
                      "lines": len(room["lines"]), "structural_lines": len(s_lines), "evidence": dict(sorted(ev.items())),
                      "materials": dict(Counter(m["state"] for m in room["materials"])),
                      "unresolved": len(room["unresolved"]), "coverage": CS.summary(rows)["by_run_state"],
                      "outputs": res["files"] + (["URBAN_ROOM_BOQ.xlsx"] if "xlsx" in res else []) + svgs,
                      **({"admission": {k: v for k, v in (arch["discovery"].get("gates") or {}).items() if k != "rule"}}
                         if admit else {})}, indent=1))
    return 0


def _m2_default():
    from tools import urban_boq_m2 as M2
    return M2.GENERIC_CONVENTIONS


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
                   help="the versioned architectural takeoff method (no default: the route is opt-in until validated); "
                        "ARCH_TAKEOFF_V2 (S6) adds the drawing admission, unit-relative tolerances, empty-band plan "
                        "regions and the completeness gates (exit 2: admission blocked, 3: completeness failed)")
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
    # S6: the drawing admission (always on for ARCH_TAKEOFF_V2) and its reviewer inputs (recorded, never defaulted)
    p.add_argument("--strict-admission", action="store_true",
                   help="ARCH_TAKEOFF_V1 behind the S6 drawing admission: a fatal finding stops the run with exit 2 and "
                        "no BOQ; an admitted drawing gives V1's own outputs plus DRAWING_DISCOVERY.json")
    p.add_argument("--units", choices=["mm", "cm", "m", "in"],
                   help="reviewer input: the drawing unit when $INSUNITS is absent / 0 or contradicted (recorded)")
    p.add_argument("--region", nargs="+", metavar="FLOOR=x0,y0,x1,y1",
                   help="reviewer input: a plan region in drawing units (frame-less or paper-space sheets; recorded)")
    p.add_argument("--accept-missing-xref", nargs="+", metavar="XREF_BLOCK",
                   help="reviewer input: measure without these unresolved external references (recorded)")
    p.set_defaults(fn=cmd_arch)
    a = ap.parse_args(argv)
    return a.fn(a)


if __name__ == "__main__":
    sys.exit(main())
