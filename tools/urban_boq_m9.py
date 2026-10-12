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

`run` calls urban_boq_m2's compute and writer exactly as `urban_boq_m2 run` does (tools/urban_boq_m2.py is frozen and
not edited), so every file it writes in OUT is the route G output unchanged; the M9 outputs go to OUT/m9/:

    BOQ_LINES.json / .csv     canonical lines (URBAN_CANONICAL_BOQ_LINE_V1): the route G items adapted (numbers and
                              states never raised) + the room lines of --rooms
    MATERIAL_RESULTS.json     tile / membrane material results per room (waste, offcuts, packs: views of a line)
    COVERAGE.json / .csv      the 99 BOQ families with this run's terminal state
    RUN_RULES.json            rule-set version and digest, superseded rules, conventions set and digest, specs used
    URBAN_ROOM_BOQ.xlsx       the room-by-room workbook (formulas; recalculate before reading cached values)
    ROOMS_DIAGNOSTIC.json     with --rooms: the room schedule check (no BOQ line)

No prices. MACHINE_ONLY: nothing here is reviewed, approved or quotation-ready.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import sys
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


def write_m9(out, *, s_lines=(), room=None, family_coverage=None, project_id, conventions=None, xlsx=True, rooms_check=None):
    from engine import boq_room_workbook as WB
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    lines = list(s_lines) + (room["lines"] if room else [])
    mats = room["materials"] if room else []
    rows = CS.census(lines, family_coverage=family_coverage, structural_run=bool(s_lines) or family_coverage is not None,
                     rooms_run=room is not None, material_results=mats)
    specs = [(m.get("material_spec") or {}).get("spec_id") for m in mats if (m.get("material_spec") or {}).get("spec_id")]
    rr = run_rules(conventions=conventions, specs=specs)
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
    for name, text in files.items():
        (out / name).write_text(text, encoding="utf-8")
    res = {"files": sorted(files)}
    if xlsx:
        res["xlsx"] = WB.write(out / "URBAN_ROOM_BOQ.xlsx", room_boq=room, structural_lines=list(s_lines), census_rows=rows,
                               meta={"project_id": project_id, "rule_set": rr["rule_set"],
                                     "rule_set_digest": rr["rule_set_digest"]}, created=CREATED)
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
    a = ap.parse_args(argv)
    return a.fn(a)


if __name__ == "__main__":
    sys.exit(main())
