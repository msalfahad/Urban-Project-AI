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
import re
import sys
from collections import Counter, defaultdict
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
ARCH_METHODS = ("ARCH_TAKEOFF_V1", "ARCH_TAKEOFF_V2", "ARCH_TAKEOFF_V2.1", "ARCH_TAKEOFF_V2.2", "ARCH_TAKEOFF_V2.3",
                "ARCH_TAKEOFF_V2.4", "ARCH_TAKEOFF_V2.5", "ARCH_TAKEOFF_V2.6", "ARCH_TAKEOFF_V2.7", "ARCH_TAKEOFF_V2.7.1",
                "ARCH_TAKEOFF_V2.8", "ARCH_TAKEOFF_V2.9", "ARCH_TAKEOFF_V2.10",
                "ARCH_TAKEOFF_V2.11")
# S6: ARCH_TAKEOFF_V2 = V1 + drawing admission (stop, exit 2, no BOQ on a fatal finding) + unit-relative geometric
# tolerances + plan regions cut only along empty bands + floor-category and finish-surface completeness. V1 is
# unchanged; --strict-admission puts the same admission in front of V1 (its outputs are V1's own).
V2 = "ARCH_TAKEOFF_V2"
# Phase 2A: ARCH_TAKEOFF_V2.1 = V2 + the robust band-path geometry (engine.source.robust_geometry: the reviewed robust
# predicate at three sites, the mean-axis face lines, AT_THRESHOLD / UNDECIDABLE records). Opt-in only: V1 and V2 never
# reach the V2.1 code (their call paths pass no geometry object).
V21 = "ARCH_TAKEOFF_V2.1"
ARCH_POLICY_ID_V21 = "URBAN_BOQ_M9_P2A_ARCH_V2_1"
# Phase 2B-0: ARCH_TAKEOFF_V2.2 = V2.1 + the release-safety corrections (findings F-17 .. F-24 of the Phase 2A
# acceptance review): openings deducted from the room boundary they lie on, one boundary role per edge, door release
# guards, lift-entrance candidates, ledger conservation, window positions. Opt-in only: V1, V2 and V2.1 never reach it
# (their call paths pass no release-safety policy).
V22 = "ARCH_TAKEOFF_V2.2"
ARCH_POLICY_ID_V22 = "URBAN_BOQ_M9_P2B0_ARCH_V2_2"
# Phase 2B-1: ARCH_TAKEOFF_V2.3 = V2.2 + the engineering knowledge registry (knowledge/URBAN_ENGINEERING_KNOWLEDGE_1.0.0.json):
# the owner wet-area scope, marble thresholds and doorway strips, door jamb plaster, doorless-opening jamb skirting,
# exterior waterproofing, the space connectivity model with bound project decisions, the owner door-opening standard
# as AS_DRAWN / OWNER_REQUIRED scenarios, the elevator schedule and the grouped owner questions. Opt-in only: V1 ..
# V2.2 never reach it (their call paths pass no owner-scope policy) and keep the frozen rule set rules/ 1.5.0.
V23 = "ARCH_TAKEOFF_V2.3"
ARCH_POLICY_ID_V23 = "URBAN_BOQ_M9_P2B1_ARCH_V2_3"
# Phase 2B-2: ARCH_TAKEOFF_V2.4 = V2.3 + the knowledge registry 1.1.0 (knowledge/URBAN_ENGINEERING_KNOWLEDGE_1.1.0.json:
# membrane roll, lap and upturn standards, doorway transitions, penetrations, door feasibility), the project rules
# (URBAN_PROJECT_RULES_V1, --project-rules) and the Project Engineering Rules Sheet, the waterproofing system (net /
# installed / procurement, cutting plan per membrane system), the door feasibility engine and the door jamb plaster at
# each door category's height. Opt-in only: V1 .. V2.3 never reach it (V2.3 keeps registry 1.0.0).
V24 = "ARCH_TAKEOFF_V2.4"
ARCH_POLICY_ID_V24 = "URBAN_BOQ_M9_P2B2_ARCH_V2_4"
# Phase 2B-3: ARCH_TAKEOFF_V2.5 = ARCH_TAKEOFF_V2.4 + the corrections proven by the engineering calculation proof library
# (tests/m9_p2b3: independent hand calculations, an independent reference calculator): the shortest band segment, the
# roll-tail band option and exact roll packing, membrane patches of a resolved detail in B and in the rolls, the band
# topology of a resolved doorway detail, the material basis (proven subtotal / provisional final / roll sensitivity to
# open doorway details), the project rules bound to the drawing's sha256, the BOQ traceability chain. Opt-in only:
# no earlier method reaches it (their call paths pass no v25 flag).
V25 = "ARCH_TAKEOFF_V2.5"
ARCH_POLICY_ID_V25 = "URBAN_BOQ_M9_P2B3_ARCH_V2_5"
# Phase 2B-5: ARCH_TAKEOFF_V2.6 = ARCH_TAKEOFF_V2.5 + the waterproofing installation layer (engine.source.wp_install):
# the piece-level cutting plan the engine actually cut (every cut, rip and cross-cut, each piece with its source and
# destination, offcuts as real rectangles in classes), the band joints against corners and floor-seam ends, the doorway
# jamb junctions, multi-layer points, penetration clearances, drains and lay order, and the floor-to-wall junction as
# an open detail with its alternatives. The V2.5 quantities are unchanged. Opt-in only: no earlier method reaches it
# (their call paths pass no v26 flag).
V26 = "ARCH_TAKEOFF_V2.6"
ARCH_POLICY_ID_V26 = "URBAN_BOQ_M9_P2B5_ARCH_V2_6"
# Phase 2B-7: ARCH_TAKEOFF_V2.7 = ARCH_TAKEOFF_V2.6 + the drawing-interpretation corrections proven by independent
# acceptance tests (engine.source.arch_v27, tests/m9_p2b7): the door opening from its own jamb evidence, layer roles
# from geometry with explicit refusal, oriented and four-line columns, arc-aware room boundaries and curved wall
# bands, the separate door-opening record and the wet-room evidence rule of knowledge registry 1.2.0. Opt-in only:
# no earlier method reaches it (their call paths pass no v27 flag).
V27 = "ARCH_TAKEOFF_V2.7"
ARCH_POLICY_ID_V27 = "URBAN_BOQ_M9_P2B7_ARCH_V2_7"
V27_KNOWLEDGE = "1.2.0"           # the registry V2.7 reads (UP-DOOR-OPEN-003, UP-WET-002; tools/kb_build_1_2.py)
# Phase 2B-8: ARCH_TAKEOFF_V2.7.1 = ARCH_TAKEOFF_V2.7 + the acceptance hardening of its review (tests/m9_p2b8): the
# quantities of a review space identical under every plausible classification released, the rest kept as conditional
# scenario quantities (UP-REVIEW-001); every BOQ line reported once as confirmed / conditional / held / excluded
# (UP-QTY-STATUS-001); the door-standard reconciliation (UP-DOOR-OPEN-003 1.3.0); the WC linework profile and the
# basin's own linework by insert path (UP-WET-002 1.3.0); turned columns as jambs and wall interruptions
# (UP-COL-ORIENT-001); doorway-strip lines traced to their entities. Opt-in only: no earlier method reaches it (their
# call paths pass no v271 flag); V2.7 itself is unchanged.
V271 = "ARCH_TAKEOFF_V2.7.1"
ARCH_POLICY_ID_V271 = "URBAN_BOQ_M9_P2B8_ARCH_V2_7_1"
V271_KNOWLEDGE = "1.3.0"          # the registry V2.7.1 reads (UP-REVIEW-001, UP-QTY-STATUS-001, UP-COL-ORIENT-001)
# Phase 2B-9: ARCH_TAKEOFF_V2.8 = ARCH_TAKEOFF_V2.7.1 + heights read from the drawing (engine.source.arch_v28: the
# evidence hierarchy element / room annotation > door-window schedule > section / elevation > floor note > project
# rule > Urban default, every height with its source, value, unit and scope), the opening schedule (width, height,
# sill, head, class; a window's finish deduction clipped to its own band; floor-level glazing not skirted; window
# reveals from the actual glazing depth), the wall geometry per face (centreline, faces, area, short returns and
# curved stubs) and the curved-window corrections (tests/m9_p2b9). Opt-in only: no earlier method reaches it (their
# call paths pass no v28 flag); V2.7.1 itself is unchanged.
V28 = "ARCH_TAKEOFF_V2.8"
ARCH_POLICY_ID_V28 = "URBAN_BOQ_M9_P2B9_ARCH_V2_8"
V28_KNOWLEDGE = "1.4.0"           # the registry V2.8 reads (UP-HGT-001, UP-OPEN-SCHED-001, UP-REVEAL-001, UP-WALL-GEOM-001)
# Phase N10: ARCH_TAKEOFF_V2.9 = ARCH_TAKEOFF_V2.8 + curved wall openings read as openings (engine.source.arch_v29:
# D-P9-01 a glazing layer inferred from concentric glazing in jambed curved wall gaps, D-P9-02 the curved opening
# closed on its own wall faces, never at the glazing line) and the N10 quantity additions (tests/m9_n10). Opt-in only:
# no earlier method reaches it (their call paths pass no v29 flag and no opening of theirs carries "curved").
V29 = "ARCH_TAKEOFF_V2.9"
ARCH_POLICY_ID_V29 = "URBAN_BOQ_M9_N10_ARCH_V2_9"
V29_KNOWLEDGE = "1.5.0"           # the registry V2.9 reads (UP-OPEN-CURVED-001, UP-MAS-HEIGHT-001, UP-FACADE-001)
# T-034: ARCH_TAKEOFF_V2.10 = ARCH_TAKEOFF_V2.9 + the room names typed with engine.source.room_vocab ROOM_VOCAB_V2
# (T-022: compound phrases before bare words, so a swimming bath / pool label is POOL, not BATHROOM wet scope; a
# compound naming no room, e.g. car wash, types nothing and is held). Same registry as V2.9. Opt-in only: every
# earlier method calls arch_rooms.spaces with vocab=None (the V1 lexicon), byte-for-byte as before.
V210 = "ARCH_TAKEOFF_V2.10"
ARCH_POLICY_ID_V210 = "URBAN_BOQ_M9_T034_ARCH_V2_10"
V210_KNOWLEDGE = V29_KNOWLEDGE
V210_VOCAB = "ROOM_VOCAB_V2"
# T-079: ARCH_TAKEOFF_V2.11 = ARCH_TAKEOFF_V2.10 + the verified waterproofing pieces wired (engine.source.arch_v211):
# wet / dry evidence decides the review spaces (T-010), the owner's strip method per wet area and roof (T-076), roofs
# inside the parapet (T-071), one doorway transition per door, the membrane rolls held on owner Q-49 (registry 1.7.0).
# Opt-in only: every earlier method passes no V2.11 flag and keeps its registry; V2.10 itself is unchanged.
V211 = "ARCH_TAKEOFF_V2.11"
ARCH_POLICY_ID_V211 = "URBAN_BOQ_T079_ARCH_V2_11"
V211_KNOWLEDGE = "1.7.0"
V271_FAMILY = (V271, V28, V29, V210, V211)
V27_FAMILY = (V27, V271, V28, V29, V210, V211)
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
                 admission_findings=(), decisions=None, project_rules=None, independent_checks=None):
    """the architectural route on one plan drawing (see _arch_compute). ARCH_TAKEOFF_V2.4 runs inside the knowledge
    registry 1.1.0 (engine.source.knowledge.using) and takes the project rules (URBAN_PROJECT_RULES_V1); every other
    method runs exactly as before (registry 1.0.0 for V2.3, the rule store for V1 .. V2.2)."""
    kw = dict(method=method, facts=facts, layer_roles=layer_roles, reference_areas=reference_areas,
              project_id=project_id, intake=intake, strict=strict, units=units, region_specs=region_specs,
              accept_xrefs=accept_xrefs, extra_documents=extra_documents, admission_findings=admission_findings,
              decisions=decisions)
    if independent_checks is not None and method not in (V25, V26, V27, V271, V28, V29, V210, V211):
        raise SystemExit("--independent-checks (URBAN_INDEPENDENT_CHECKS_V1) needs --method ARCH_TAKEOFF_V2.5, "
                         "ARCH_TAKEOFF_V2.6, ARCH_TAKEOFF_V2.7 or ARCH_TAKEOFF_V2.7.1")
    if method in (V24, V25, V26, V27, V271, V28, V29, V210, V211):
        from engine.source import knowledge as K
        with K.using({V27: V27_KNOWLEDGE, V271: V271_KNOWLEDGE, V28: V28_KNOWLEDGE, V29: V29_KNOWLEDGE,
                      V210: V210_KNOWLEDGE, V211: V211_KNOWLEDGE}.get(method, "1.1.0")):
            ic = {"independent_checks": independent_checks} if method in (V25, V26, V27, V271, V28, V29, V210, V211) else {}
            if method == V211:
                # T-079: ARCH_TAKEOFF_V2.11 reads what each plan region's room builder saw (engine.source.arch_v211)
                from engine.source import arch_v211 as AV
                with AV.capture() as cap:
                    return _arch_v271(drawing, project_rules=project_rules, _v211_cap=cap, **ic, **kw)
            if method in V271_FAMILY:
                return _arch_v271(drawing, project_rules=project_rules, **ic, **kw)
            return _arch_compute(drawing, project_rules=project_rules, **ic, **kw)
    if project_rules is not None:
        raise SystemExit("--project-rules (URBAN_PROJECT_RULES_V1) needs --method ARCH_TAKEOFF_V2.4, "
                         "ARCH_TAKEOFF_V2.5, ARCH_TAKEOFF_V2.6, ARCH_TAKEOFF_V2.7 or ARCH_TAKEOFF_V2.7.1")
    return _arch_compute(drawing, **kw)


def _arch_compute(drawing, *, method, facts=None, layer_roles=None, reference_areas=None, project_id=None, intake=None,
                  strict=False, units=None, region_specs=None, accept_xrefs=(), extra_documents=(),
                  admission_findings=(), decisions=None, project_rules=None, independent_checks=None, _scenario=None,
                  _release=None):
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
    v29 = method in (V29, V210, V211)                               # ARCH_TAKEOFF_V2.8 plus the Phase N10 corrections
    v210 = method in (V210, V211)                             # T-034: V2.9 plus the ROOM_VOCAB_V2 room names
    v28 = method in (V28, V29, V210, V211)                          # ARCH_TAKEOFF_V2.7.1 plus the Phase 2B-9 heights / walls
    v271 = method in V271_FAMILY                              # ARCH_TAKEOFF_V2.7 plus the Phase 2B-8 hardening
    v27 = method in (V27, V271, V28, V29, V210, V211)                          # ARCH_TAKEOFF_V2.6 plus the Phase 2B-7 corrections
    v26 = method in (V26, V27, V271, V28, V29, V210, V211)                     # ARCH_TAKEOFF_V2.5 plus the installation layer
    v25 = method in (V25, V26, V27, V271, V28, V29, V210, V211)                # ARCH_TAKEOFF_V2.4 plus the proven corrections
    v24 = method in (V24, V25, V26, V27, V271, V28, V29, V210, V211)           # V2.3 plus the registry 1.1.0 and the project rules
    v23 = method in (V23, V24, V25, V26, V27, V271, V28, V29, V210, V211)      # V2.3 is V2.2 plus the knowledge registry
    v22 = method in (V22, V23, V24, V25, V26, V27, V271, V28, V29, V210, V211) # V2.2 is V2.1 plus the Phase 2B-0 corrections
    v21 = method in (V21, V22, V23, V24, V25, V26, V27, V271, V28, V29, V210, V211)
    v2 = method in (V2, V21, V22, V23, V24, V25, V26, V27, V271, V28, V29, V210, V211)  # V2.1 is V2 plus the Phase 2A additions
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
    line_region = {}                                  # ARCH_TAKEOFF_V2.7: id(line) -> (line, its plan region)
    floor_areas = []
    v2_unresolved, coverage, column_ev, arc_recs, unread_ev = [], [], [], [], []
    strip_split, strip_split_pieces = [], []                  # ARCH_TAKEOFF_V2.6 (D-V26-07)
    geom_of = {}
    if v21:
        from engine.source import robust_geometry as RG
        geom_of = {r["region_id"]: RG.Geometry(u) for r in regs}
    if v27:
        from engine.source import arch_v27 as V27M          # ARCH_TAKEOFF_V2.7: layer roles from geometry + refusals
    roles_of = {r["region_id"]: (V27M.layer_roles if v27 else AP.layer_roles)(
        ents_of[r["region_id"]], u, override=layer_roles, tol=tol, **({"geom": geom_of[r["region_id"]]} if v21 else {}))
                for r in regs}
    if v29:
        # ARCH_TAKEOFF_V2.9 (D-P9-01): an OTHER layer whose concentric arcs glaze the jambed curved wall gaps is a
        # WINDOW layer (engine.source.arch_v29.curved_glazing_roles); a declared role is never changed
        from engine.source import arch_v29 as V29M
        roles_of = {rid_: (V29M.curved_glazing_roles(ents_of[rid_], L_, u, override=layer_roles)
                           if L_["state"] != "BLOCKED" else L_) for rid_, L_ in roles_of.items()}
    spaces_of = {r["region_id"]: AR.spaces(ents_of[r["region_id"]], roles_of[r["region_id"]]["roles"], u,
                                           region_id=r["region_id"], tol=tol,
                                           **({"geom": geom_of[r["region_id"]]} if v21 else {}),
                                           **({"release_safety": True} if v22 else {}),
                                           **({"door_review": True} if v26 else {}), **({"v27": True} if v27 else {}),
                                           **({"v271": {"scenario": _scenario}} if v271 else {}),
                                           **({"v29": True} if v29 else {}),
                                           **({"vocab": V210_VOCAB} if v210 else {}))
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
    v27_log = []                                              # ARCH_TAKEOFF_V2.7: every correction and refusal
    v271_turned = []                                          # ARCH_TAKEOFF_V2.7.1: turned columns used
    decided, possibly_ext = {}, {}
    v24_floors = []
    door_facts = facts
    if v23:
        from engine.source import door_standards as DSTD
        from engine.source import space_model as SMOD
        door_facts = DSTD.door_model_facts(facts)
    HE, v28_recs = None, {"openings": [], "rooms": [], "walls": [], "stubs": [], "reveals": [], "bindings": {},
                          "lost_labels": []}
    v29_recs = {"curved_openings": [], "curved_rejected": [], "glazing_layers": [], "masonry": [], "facade": []}
    if v28:
        # ARCH_TAKEOFF_V2.8 (UP-HGT-001): the height evidence of the whole drawing - schedules, sections /
        # elevations and project notes on their sheets; each floor's own texts are bound below
        from engine.source import arch_v28 as V28M
        HE = V28M.Evidence(E["texts"], [{"box": f_["box"]} for f_ in P.get("other_frames") or ()] +
                           [{"box": r["box"]} for r in regs], regs, u,
                           {r["floor"]: level[r["region_id"]] for r in regs}, facts)
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
                              **({"geom": geom_of[rid]} if v21 else {}), **({"arc_bands": True, "trace": True} if v27 else {}),
                              **({"column_polys": S.get("column_polys") or ()} if v271 else {}))
        if v28:
            # ARCH_TAKEOFF_V2.8 (UP-WALL-GEOM-001): short returns and curved stubs the 0.30 m band rule drops
            v28_recs["stubs"] += _v28_stubs(S, ents, L["roles"], u, floor)
            # a room named on the plan but closed by no face is a finding, never a silent omission
            open_codes = {c_[0] for c_ in AR.LEXICON if c_[3] in (AR.EXTERIOR, AR.VOID)}
            for x_ in V28M.lost_labels(ents["texts"], S["faces"], AR.room_word, floor, title_of=AP.floor_of_title,
                                       open_codes=open_codes):
                v28_recs["lost_labels"].append(x_)
                if x_["finding"] != "ROOM_LABEL_NOT_IN_A_CLOSED_SPACE":
                    continue
                unresolved.append({"room_id": "-", "floor": floor, "item": f"ROOM {x_['code']}",
                                   "reason": f"ROOM_LABEL_NOT_IN_A_CLOSED_SPACE: '{x_['text']['text']}' lies in no "
                                             "closed space of the plan - the room it names is not measured (an "
                                             "opening the plan reader could not bound, e.g. curved glazing only); "
                                             "review the plan or declare the layer roles"})
        if v271 and S.get("column_polys"):
            # ARCH_TAKEOFF_V2.7.1 (UP-COL-ORIENT-001): the turned columns used as jambs and wall cuts
            v271_turned.append({"correction": "TURNED_COLUMN", "floor": floor, "region_id": rid, "subject": "columns",
                                "decision": "TURNED_COLUMNS_AS_JAMBS_AND_WALL_CUTS",
                                "detail": {"turned": len(S["column_polys"]),
                                           "jamb_openings": _turned_jambs(S, u)}})
        if v27:
            L26 = AP.layer_roles(ents, u, override=layer_roles, tol=tol, **({"geom": RG.Geometry(u)} if v21 else {}))
            v27_log += _v27_region_log(floor, rid, L, S, L26["roles"], set(layer_roles or ()))
            for x in L.get("refusals") or ():
                unresolved.append({"room_id": "-", "floor": floor, "item": f"LAYER {x['layer']}",
                                   "reason": f"{x['code']}: layer {x['layer']}: {x['reason']}"})
        v28_ctx = None
        if v28:
            # ARCH_TAKEOFF_V2.8: the floor's texts bound to its openings / rooms, then every opening's height, sill
            # and head with their sources (UP-OPEN-SCHED-001)
            v28_recs["bindings"][floor] = HE.bind(floor, ents["texts"], [
                {"room_id": AM.room_id(floor, sp_["face_id"]), "polygon": sp_["polygon"]} for sp_ in S["spaces"]],
                S["openings"])
            sched = {o_["opening_id"]: HE.opening(floor, o_, door_fallback=lambda o2: DSTD.door_height(
                DSTD.INTERNAL, facts)) for o_ in S["openings"] if o_["kind"] in ("DOOR", "WINDOW")}
            v28_ctx = {"evidence": HE, "schedule": sched,
                       "height_of": V28M.height_of(sched, (facts or {}).get("opening_heights") or {})}
            v28_recs["openings"] += list(sched.values())
        M = AM.measure(S, floor=floor, project_id=pid, revision_set_sha256=rev, facts=facts,
                       floor_above_level_m=above, floor_level_m=level[rid], documents=docs,
                       **({"release_safety": True} if v22 else {}),
                       **({"owner_scope": True, "door_height": _v28_door_height(v28_ctx, facts) if v28 else
                           (lambda o_: DSTD.door_height(DSTD.INTERNAL, facts))} if v23 else {}),
                       **({"piece_box": True} if v26 else {}), **({"v28": v28_ctx} if v28 else {}))
        if v29:
            # ARCH_TAKEOFF_V2.9: the floor's curved openings, the curved gaps refused and the glazing layers inferred
            for o_ in S["openings"]:
                if o_.get("curved"):
                    v29_recs["curved_openings"].append(_v29_curved_record(o_, floor, M["rooms"]))
            v29_recs["curved_rejected"] += [dict(x_, floor=floor) for x_ in (S.get("v29") or {}).get("rejected") or ()]
            for lay_, ev_ in ((L.get("v29") or {}).get("promoted") or {}).items():
                v29_recs["glazing_layers"].append({"floor": floor, "layer": lay_, **ev_})
            # ARCH_TAKEOFF_V2.9 (UP-MAS-HEIGHT-001): the wall panel by thickness from the evidenced masonry height
            ml_, mu_, mr_ = _v29_masonry(S, floor, v28_ctx["schedule"], HE, E["texts"], facts, u,
                                         {"project_id": pid, "revision_set_sha256": rev, "documents": docs})
            M["lines"] = [ln_ for ln_ in M["lines"] if not (ln_["item_code"] == "MAS.BLOCK" and
                                                          ln_["location"]["floor"] == floor)] + ml_
            M["unresolved"] = [x_ for x_ in M["unresolved"] if not str(x_.get("item", "")).startswith("MAS.BLOCK")] + mu_
            v29_recs["masonry"].append(mr_)
            # ARCH_TAKEOFF_V2.9 (UP-FACADE-001): the floor's exterior outline, its area and finish
            fl_, fu_, fr_ = _v29_facade(S, floor, v28_ctx["schedule"], HE, facts,
                                        {"project_id": pid, "revision_set_sha256": rev, "documents": docs},
                                        reg["order"] == min(r_["order"] for r_ in regs))
            M["lines"] += fl_
            M["unresolved"] += fu_
            v29_recs["facade"].append(fr_)
        if v28:
            v28_recs["rooms"] += [{"floor": floor, "room_id": r_["room_id"], "name_en": r_["name_en"],
                                   "heights": r_.get("heights_v28"), "wet": r_.get("wet_v28"),
                                   "skirting_windows": r_.get("skirting_windows_v28")}
                                  for r_ in M["rooms"] if r_.get("heights_v28")]
        strip_split_pieces += M.get("piece_box") or []                       # ARCH_TAKEOFF_V2.6 (D-V26-07)
        if v271 and _release:
            # ARCH_TAKEOFF_V2.7.1 (UP-REVIEW-001): a review space's quantities identical under every plausible
            # classification, measured by the scenario runs, join its lines (the space keeps its own identity)
            M["lines"] += _released_lines(_release, floor, M["rooms"], {"project_id": pid, "revision_set_sha256": rev,
                                                                        "documents": docs})
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
            if v23:
                # Phase 2B-1 (UP-THR-001): doorway strips of single verified door / passage openings take their
                # owner treatment; every other strip stays in the V2 strip register
                from engine.source import owner_finish_scope as OFS
                t_strips = strips
                if v26:
                    # D-V26-07 (Phase 2B-5 D-C2): a doorway face running on past its openings' jambs
                    # between wall lines is split at the openings' boxes; the face itself is unchanged
                    t_strips, split_recs = AC.split_strips(S, strips, floor)
                    strip_split += split_recs
                    fa["strip_split"] = split_recs
                t_lines, t_unres, rest = OFS.threshold_lines(ctx, t_strips, M["rooms"], floor, line=AM._line,
                                                             **({"wet_review": True} if v27 else {}))
                if v28:
                    # ARCH_TAKEOFF_V2.8 (UP-REVEAL-001): a window strip whose sill is established is the sill surface
                    # (or floor, at floor-level glazing), and the window's reveals are measured from it
                    w_lines, w_unres, rest, w_recs = V28M.window_strip_lines(
                        ctx, rest, M["rooms"], floor, v28_ctx["schedule"], _v28_room_heights, line=AM._line,
                        wet_rooms={r_["room_id"] for r_ in M["rooms"]
                                   if (r_.get("finish_scope") or {}).get("scope") == "WET" or r_.get("kind") == "WET"})
                    t_lines, t_unres = t_lines + w_lines, t_unres + w_unres
                    v28_recs["reveals"] += w_recs
                s_lines, s_unres = AC.strip_lines(ctx, rest, floor)
                s_lines, s_unres = t_lines + s_lines, t_unres + s_unres
            else:
                s_lines, s_unres = AC.strip_lines(ctx, strips, floor)
            r_lines, r_unres = AC.surface_rfis(ctx, M, floor, facts, level[rid], above,
                                               **({"owner_scope": True} if v23 else {}))
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
            dec_here = SMOD.decided_faces(S, floor, decisions) if v23 else {}
            if v23:
                decided.update({(floor, k): v for k, v in dec_here.items()})
                possibly_ext.update(DMOD.possibly_external_faces(S, M["rooms"]))
            door_floors.append((floor, DMOD.floor_model(S, M["rooms"], ents, u, floor, wall_layers=walls_here,
                                                        origin=(reg["box"][0], reg["box"][1]),
                                                        facts=door_facts,
                                                        **({"guards": True} if v22 else {}),
                                                        **({"decided_exterior": dec_here} if dec_here else {}),
                                                        **({"symbol_scope": True} if v27 else {}))))
            tx = {t_["id"]: t_ for t_ in ents["texts"]}
            door_texts[floor] = ents["texts"]
            door_face_texts[floor] = {f_["face_id"]: [tx[i_] for i_ in f_.get("label_text_ids") or () if i_ in tx]
                                      for f_ in S["faces"]}
        if v24:
            v24_floors.append({"floor": floor, "S": S, "M": M, "ents": ents, "roles": L["roles"]})
        for rm in M["rooms"]:
            rm["region_id"] = rid
        rooms += M["rooms"]
        openings += M["openings"]
        lines += M["lines"]
        if v27:
            line_region.update((id(ln), (ln, rid)) for ln in M["lines"])     # the line held: its id stays its own
        mats += X["materials"]
        comps += X["comparisons"]
        unresolved += M["unresolved"] + X["unresolved"]
        regions.append(rec)
    doors = None
    if v21:
        doors, lines, door_unres, door_cov = _v21_doors(door_floors, door_texts, door_face_texts, regs, spaces_of,
                                                         lines, u, _v28_door_facts(door_facts, v28_recs["openings"])
                                                         if v28 else door_facts, pid, rev, docs,
                                                         **({"guards": True} if v22 else {}),
                                                         **({"not_entrance_codes": ("BALCONY", "ROOF")} if v23
                                                            else {}))
        unresolved += door_unres
        coverage += door_cov
    v24_out = None
    if v24:
        # Phase 2B-2: the rules sheet (bound to the drawing's elements), then every rule-dependent quantity
        lines, mats, unresolved, v24_out = _v24_stage(v24_floors, doors, lines, mats, unresolved, facts, decisions,
                                                      project_rules, pid, rev, docs, u,
                                                      **({"v25": True, "independent": independent_checks}
                                                         if v25 else {}), **({"v26": True} if v26 else {}),
                                                      **({"v27": True} if v27 else {}))
    if v27:
        # ARCH_TAKEOFF_V2.7: the door frames read from the door symbol's own insert, the waterproofing boundaries
        # whose near-zero pieces were merged - the corrections that change a quantity outside a plan region's log
        for e in (doors or {}).get("elements") or ():
            if e.get("frame_scope_v27"):
                v27_log.append({"correction": "DOOR_FRAME", "floor": e["floor"], "region_id": "-",
                                "subject": e["element_id"], "decision": "FRAME_FROM_SYMBOL_INSERT",
                                "detail": dict(e["frame_scope_v27"], opening_id=e.get("opening_id"))})
        for x in v24_out.get("v27_slivers") or ():
            v27_log.append({"correction": "SLIVER_MERGE", "floor": x["floor"], "region_id": "-",
                            "subject": x["room_id"], "decision": "MERGED_INTO_NEIGHBOUR", "detail": x["sliver"]})
        # ARCH_TAKEOFF_V2.7: per-line source entities (arch_v27.attach_provenance)
        # one plan region at a time: a line belongs to the region that measured it (opening and wall lines repeat
        # their location in every region of a floor), else to the region of its door's or its own room
        region_of_room = {r_["room_id"]: r_.get("region_id") for r_ in rooms}
        door_rooms = {e["element_id"]: (e.get("from_room"), e.get("to_room"))
                      for e in (doors or {}).get("elements") or ()}
        def _region(ln):
            if line_region.get(id(ln), (None,))[0] is ln:
                return line_region[id(ln)][1]
            for r_ in door_rooms.get(ln.get("physical_element")) or ():
                if r_ in region_of_room:
                    return region_of_room[r_]
            loc_ = ln.get("location") or {}
            m_ = re.fullmatch(r"(.+)-(?:OPENING|STRIP)-(OP-\d+)", str(loc_.get("room_id") or ""))
            if m_:                         # an opening's own line: the region of its door, else the floor's one region
                cand = {region_of_room.get(r_) for e in (doors or {}).get("elements") or ()
                        if e.get("floor") == m_.group(1) and e.get("opening_id") == m_.group(2)
                        for r_ in door_rooms[e["element_id"]] if r_ in region_of_room} or \
                    {r_["region_id"] for r_ in regions if r_["floor"] == m_.group(1)}
                return next(iter(cand)) if len(cand) == 1 else None
            return region_of_room.get(loc_.get("room_id"))
        by_region = defaultdict(list)
        for ln in lines:
            by_region[_region(ln)].append(ln)
        prov = Counter()
        for rid_, S_ in spaces_of.items():
            fl_ = next((r_["floor"] for r_ in regions if r_["region_id"] == rid_), None)
            prov.update(V27M.attach_provenance(
                by_region.pop(rid_, []), [r_ for r_ in rooms if r_.get("region_id") == rid_], S_.get("faces") or [],
                S_.get("openings") or [], {"elements": [e for e in (doors or {}).get("elements") or ()
                                                       if any(region_of_room.get(r_) == rid_
                                                              for r_ in door_rooms[e["element_id"]])]},
                (S_.get("walls") or {}).get("walls") or (), fl_, rid_, **({"v271": True} if v271 else {})))
        prov.update(V27M.attach_provenance([ln for v_ in by_region.values() for ln in v_], [], [], [], {},
                                           **({"v271": True} if v271 else {})))
        v27_log.append({"correction": "PROVENANCE", "floor": "-", "region_id": "-", "subject": "lines",
                        "decision": "SOURCE_ENTITIES_ATTACHED", "detail": dict(prov)})
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
    if v22:
        from engine.source import release_safety as RSF
        run.update(policy=ARCH_POLICY_ID_V22)
        run["policies"]["release_safety"] = RSF.policy_record()
        run["v2_2"] = {"findings_addressed": ["F-17", "F-18", "F-19", "F-20", "F-21", "F-22", "F-24"]}
    if v23:
        from engine.source import knowledge as K
        from engine.source import owner_finish_scope as OFS
        run.update(policy=ARCH_POLICY_ID_V23)
        run["policies"].update(knowledge=K.policy_record(), owner_finish_scope=OFS.policy_record(),
                               door_standards=DSTD.policy_record(), space_model=SMOD.policy_record())
    if v24:
        from engine.source import door_feasibility as DF
        from engine.source import project_rules as PRJ
        from engine.source import waterproofing_system as WS
        from engine.source import wp_geometry as WG
        sh = v24_out["rules_sheet"]
        run.update(policy=ARCH_POLICY_ID_V24)
        run["policies"].update(project_rules=PRJ.policy_record(), waterproofing=WS.policy_record(),
                               wp_geometry=WG.policy_record(), door_feasibility=DF.policy_record())
        run["v2_4"] = {"knowledge": K.policy_record(),
                       "rules_sheet": {"schema": sh["schema"], "rules_sha256": sh["rules_sha256"],
                                       "sheet_sha256": sh["sheet_sha256"], "rows": len(sh["rows"]),
                                       "status_counts": sh["status_counts"],
                                       "project_rules": sh["project"]["rules_input"]},
                       "waterproofing": v24_out["waterproofing"]["project"],
                       "door_feasibility": v24_out["door_feasibility"]["summary"],
                       "approvals": len(v24_out["approvals"])}
        if v25:
            run.update(policy=ARCH_POLICY_ID_V25)
            run["v2_5"] = {"corrections": list(V25_CORRECTIONS), "drawing_binding": v24_out["drawing_binding"],
                           "traceability": v24_out["traceability"]["summary"]}
        if v26:
            from engine.source import wp_install as WI
            run.update(policy=ARCH_POLICY_ID_V27 if v27 else ARCH_POLICY_ID_V26)
            run["policies"]["wp_install"] = WI.policy_record()
            run["v2_6"] = {"corrections": list(V26_CORRECTIONS), "installation": v24_out["wp_install"]["summary"],
                           "door_reconciliation": {
                               "hinge_review_m": AR.HINGE_REVIEW_M, "leaf_review_min_share": AR.LEAF_REVIEW_MIN_SHARE,
                               "swing_note_reach_m": AR.SWING_NOTE_REACH_M,
                               "closure_parallel_deg": AR.CLOSURE_PARALLEL_DEG, "closure_band_m": AR.CLOSURE_BAND_M,
                               "reconciled": sorted(f"{o['floor']}:{o['opening_id']}" for o in openings
                                                    if o.get("door_fit_review")),
                               "noted": sorted(f"{o['floor']}:{o['opening_id']}" for o in openings
                                               if o.get("door_symbol_note"))},
                           "strip_split": {"rule": "D-V26-07", "geom_tol_m": AC.GEOM_TOL_M,
                                           "cover_tol_m": AC.SPLIT_COVER_TOL_M,
                                           "parallel_deg": 1.0,
                                           "split": [f"{r['floor']}:{'+'.join(r['openings'])}"
                                                     for r in strip_split if r["split"]],
                                           "not_split": [{"strip": f"{r['floor']}:{'+'.join(r['openings'])}",
                                                          "reason": r["reason"]}
                                                         for r in strip_split if not r["split"]],
                                           "doorway_pieces": strip_split_pieces}}
    if v27:
        arch_v27 = _v27_outputs(v27_log)
        run["v2_7"] = {"corrections": list(V27_CORRECTIONS), "summary": arch_v27["summary"],
                       "knowledge": V27_KNOWLEDGE}
        run["policies"]["arch_v27"] = V27M.POLICY
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
    if v27:
        arch["v27"] = arch_v27
    if v271:
        arch["v271_turned"] = v271_turned
    if v28:
        arch["v28"] = _v28_record(HE, v28_recs, walls_of, rooms)
    if v29:
        arch["v29"] = _v29_record(v29_recs)
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
        arch["ledger"] = SL.ledger(lines, rooms, openings, unresolved, method=method, doors=doors, walls=walls_of,
                                   **({"conserve": True} if v22 else {}), **({"owner_scope": True} if v23 else {}),
                                   **({"wp_system": True} if v24 else {}))
        run["v2_1"]["ledger"] = {"table": arch["ledger"]["table"], "summary": arch["ledger"]["summary"]}
        run["policies"]["surface_ledger"] = SL.policy_record()
        run["v2_1"]["doors"] = {"summary": doors["summary"], "main_entrance": doors["main_entrance"]["state"],
                                "conservation_ok": doors["conservation_ok"],
                                "findings": dict(Counter(f_["code"] for f_ in doors["findings"]))}
        from engine.source import door_model as DMOD
        run["policies"]["doors"] = DMOD.policy_record()
    if v23:
        _v23_outputs(arch, room_boq, rooms, openings, doors, facts, decisions, decided, possibly_ext, shafts,
                     method, unresolved, drawing=path.name)
    if v24:
        _v24_outputs(arch, v24_out)
    if v2:
        arch["coverage"] = coverage
        if any(c["gate"] != "PASS" for c in coverage):
            raise CompletenessFailed(room_boq, arch, E)
    return room_boq, arch, E


# ---------------------------------------------------------------- ARCH_TAKEOFF_V2.7.1 (Phase 2B-8)
REVIEW_SCENARIOS = (("WET_SCOPE", ("BATHROOM",), "the owner wet scope UP-WET-001, as a W.C. / wash room"),
                    ("DRY_SCOPE", ("CORRIDOR",), "the dry scope, as a lobby / wash area"))
WET_REVIEW_KINDS = ("WET_CLASSIFICATION_REVIEW", "WC_CANDIDATE_REVIEW")
RELEASE_FIELDS = ("measured_net", "bounded_range", "evidence_state")
WALL_FINISH_CODES = ("FIN.PAINT", "FIN.WALL.TILE")


def _arch_v271(drawing, _v211_cap=None, **kw):
    """ARCH_TAKEOFF_V2.7.1: the V2.7 route with the Phase 2B-8 hardening, then (UP-REVIEW-001) when a space is under
    wet-classification review: one run per plausible classification (REVIEW_SCENARIOS, every review space typed by
    the scenario), the quantities identical in every scenario released (one more run, so every derived output holds
    them), the rest kept as conditional scenario quantities. A plan without such a space is one run."""
    if kw.get("intake") is None:
        from tools import urban_intake as UI
        kw = dict(kw, intake=UI.read(str(drawing)))
    room_boq, arch, E = _arch_compute(drawing, **kw)
    targets = _review_targets(arch)
    scen, release, analysis = {}, {}, {}
    v211 = None
    if _v211_cap is not None:
        # T-079 (ARCH_TAKEOFF_V2.11): the wet / dry evidence of every space (WET_ROOM_EVIDENCE_V1) decides the review
        # spaces it classes WET or DRY; the sanitary drawing reading is an optional project input, never guessed
        from engine.source import arch_v211 as AV
        classes = AV.wet_classes(arch["rooms"], _v211_cap, (kw.get("facts") or {}).get("sanitary_by_room"))
        # the main run's capture (a scenario run below replaces the regions' entries; the plan geometry is the same,
        # but the roofs are read from the main run's own record)
        v211 = {"classes": classes, "decided": AV.decide_review(targets, classes), "cap": dict(_v211_cap)}
    if any(x["plausible"] for x in targets):
        for name, codes, why in REVIEW_SCENARIOS:
            try:
                rb, ar_, _ = _arch_compute(drawing, _scenario={"name": name, "codes": list(codes)}, **kw)
                scen[name] = {"lines": rb["lines"], "rooms": ar_["rooms"],
                              "doors": (ar_.get("door_scenarios") or {}).get("rows") or []}
            except CompletenessFailed:
                scen[name] = None                          # a scenario that cannot be measured releases nothing
        release, analysis = _review_release(targets, scen)
        if v211 is not None and v211["decided"]:
            rel_d, v211["decided"] = AV.decided_release(targets, v211["decided"], scen)
            release.update(rel_d)
            for tg in targets:
                if tg["room_id"] in v211["decided"]:
                    tg["plausible"] = []
                    tg["plausible_basis"] = (f"DECIDED {v211['decided'][tg['room_id']]} by WET_ROOM_EVIDENCE_V1 "
                                             f"({v211['classes'][tg['room_id']]['reason']}; ARCH_TAKEOFF_V2.11): the "
                                             "scenario's finish lines are released for the space")
        if release:
            room_boq, arch, E = _arch_compute(drawing, _release=release, **kw)
    elif v211 is not None:
        v211["decided"] = {}
    _v271_outputs(room_boq, arch, targets, scen, analysis)
    if arch.get("v28") is not None:
        _v28_outputs(arch)
    if arch.get("v29") is not None:
        _v29_outputs(arch)
    if v211 is not None:
        _v211_outputs(drawing, room_boq, arch, v211, v211["cap"], kw.get("facts"))
    return room_boq, arch, E


# ---------------------------------------------------------------- ARCH_TAKEOFF_V2.11 (T-079)
def _v211_outputs(drawing, room_boq, arch, v211, cap, facts):
    """ARCH_TAKEOFF_V2.11: the membrane table (wet areas and roofs, MEMBRANE_FOLD_V2), the added lines (door
    transitions, roofs, held rolls, held wet zones), the decided review spaces' line notes, the release report again
    over every line, and the run record."""
    from engine.source import arch_v211 as AV
    path = Path(drawing)
    run = arch["run"]
    ctx = {"project_id": run["project_id"], "revision_set_sha256": run["revision_set_sha256"],
           "documents": [{"file": path.name, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}]}
    classes, decided = v211["classes"], v211["decided"]
    wet, flags = AV.wet_rows(arch, classes)
    held = AV.held_wet(arch, classes)
    roofs = AV.roof_records(cap, {r["region_id"]: r["floor"] for r in arch["regions"]},
                            (facts or {}).get("exterior_spaces"))
    top = AV.top_roofs(arch)                          # T-093: the roof no plan draws (owner Q-34 parked) -> held
    table = AV.membrane_table(wet, roofs, held, top)  # T-093: rolls per area alone (owner Q-49 A)
    existing = {((ln.get("location") or {}).get("room_id"), ln["item_code"]) for ln in room_boq["lines"]}
    names = {(x["floor"], x["room_id"]): {"name_en": x.get("name_en"), "name_ar": x.get("name_ar")} for x in wet}
    added = (AV.door_transition_lines(ctx, wet, lambda x: {"name_en": x.get("name_en"), "name_ar": x.get("name_ar")})
             + AV.roof_lines(ctx, roofs) + AV.top_roof_lines(ctx, top) + AV.rolls_lines(ctx, table, names)
             + AV.held_wet_lines(ctx, held, existing))
    ids = {ln["line_id"] for ln in room_boq["lines"]}
    if any(ln["line_id"] in ids for ln in added) or len({ln["line_id"] for ln in added}) != len(added):
        raise ValueError("ARCH_TAKEOFF_V2.11: an added line repeats an existing line id")
    room_boq["lines"] += added
    if len({ln["line_id"] for ln in room_boq["lines"]}) != len(room_boq["lines"]):
        raise ValueError("ARCH_TAKEOFF_V2.11: a BOQ line id appears twice")
    for ln in room_boq["lines"]:
        rid = (ln.get("location") or {}).get("room_id")
        if rid in decided and "CLASSIFICATION_INVARIANT" in (ln.get("notes") or ""):
            ln["notes"] = (f"DECIDED_BY_EVIDENCE (ARCH_TAKEOFF_V2.11, WET_ROOM_EVIDENCE_V1 {classes[rid]['reason']}; "
                           f"UP-REVIEW-001 closed): the space is measured as its {decided[rid]} scenario")
    sets = arch["release_report"]["categories"]["CONDITIONAL"]["scenario_sets"]
    arch["release_report"] = _release_report(room_boq["lines"], sets, arch.get("owner_questions"))
    arch["v211"] = {"policy": AV.policy_record(), "classes": classes, "decided": decided, "membrane_table": table,
                    "roofs": [{k: v for k, v in r.items() if k != "fold"} for r in roofs], "wet_schedule_flags": flags,
                    "wet_zones_held": held, "top_roofs_held": top, "summary": AV.summary(classes, decided, wet, flags, held, roofs, table,
                                                                  added)}
    run.update(policy=ARCH_POLICY_ID_V211)
    run["v2_11"] = {"knowledge": V211_KNOWLEDGE, "summary": arch["v211"]["summary"],
                    "release_report": arch["release_report"]["conservation"]}
    run["policies"]["arch_v211"] = AV.policy_record()

# ---------------------------------------------------------------- ARCH_TAKEOFF_V2.9 (Phase N10)
V29_CORRECTIONS = (
    "D-V29-01 curved wall openings (UP-OPEN-CURVED-001, D-P9-02): a gap in a curved wall band with a radial jamb line "
    "at both ends is an opening, closed on both wall faces by arcs: the room ends at its own wall face, the strip to "
    "the glazing is a reveal / sill strip (never floor); its width is the arc of the face the room meets",
    "D-V29-02 curved glazing layers (UP-OPEN-CURVED-001, D-P9-01): a layer whose concentric arcs glaze the jambed curved "
    "wall gaps (most of its linework in wall gaps) is a WINDOW layer; a declared role is never changed",
    "D-V29-03 masonry by thickness (UP-MAS-HEIGHT-001, L-P9-05): the wall panel from the floor's T.O.S. to the soffit "
    "(its own section band, or stated facts), never a finish height; area = wall-mass plan area / t x panel + the "
    "wall above / below each opening, volume = area x t; a beam bottom gives a range, no beam evidence holds it; "
    "MAS.BLOCK takes the panel only when the family's material is stated (MASONRY.json)",
    "D-V29-04 facade (UP-FACADE-001): the exterior outline of the floor's wall network (openings closed on their outer "
    "face), its area F.F.L. to the next F.F.L. (or to the parapet top) with each opening on it deducted by its own "
    "band; a second outline is reported, never added; an outline around the building holds the facade; the exterior "
    "finish is held without a stated specification (FACADE.json)",
)


MAS_PANEL_AR = BL.ITEMS["ARCH.WALL_RUN"][1].replace(BL.ITEMS["ARCH.WALL_RUN"][1].split()[0],
                                                     BL.ITEMS["ARCH.SPACE"][1].split()[0])
V29_ITEMS = {"ARCH.WALL_PANEL": ("Wall panel area by thickness (T.O.S. to soffit, openings deducted)", MAS_PANEL_AR,
                                 "MASONRY"),
             "ARCH.WALL_VOLUME": ("Wall volume by thickness (panel area x thickness)",
                                  BL.ITEMS["ARCH.WALL_RUN"][1] + " (m3)", "MASONRY"),
             "ARCH.FACADE_RUN": ("Facade run: exterior wall face length in plan (openings included)",
                                 "\u0637\u0648\u0644 \u0627\u0644\u0648\u0627\u062c\u0647\u0629", "FACADE"),
             "ARCH.FACADE": ("Facade area: exterior wall face, F.F.L. to the next F.F.L., openings deducted",
                             "\u0645\u0633\u0627\u062d\u0629 \u0627\u0644\u0648\u0627\u062c\u0647\u0629", "FACADE"),
             "FIN.EXT.FINISH": ("Exterior wall finish (plaster / paint / cladding as specified)",
                                "\u062a\u0634\u0637\u064a\u0628 \u062e\u0627\u0631\u062c\u064a", "FACADE")}


def _v29_line(ctx, *, item_code, room, element, unit, net, formula, inputs, ev=None, bounded=None, rfi=None,
              notes="", material_state="BY_SPEC", rule_id=ARCH_POLICY_ID_V29):
    """an ARCH_TAKEOFF_V2.9 line (the arch_measure line contract; new item codes carry their own names; rule_id: the
    registry 1.5.0 rule the line applies)."""
    from engine.source import arch_measure as AM
    en, ar, tr = V29_ITEMS.get(item_code, (None, None, None))
    if ev is None:
        ev = "SOURCE_DERIVED" if net is not None else ("BOUNDED_EXPOSURE" if bounded else "BLOCKED_RFI")
    ref = {"rule_id": rule_id, "version": "1", "rule_set": AM.RULE_SET,
           "rule_set_digest": RS.rule_set(AM.RULE_SET)["digest"]}
    return BL.make_line(project_id=ctx["project_id"], revision_set_sha256=ctx["revision_set_sha256"],
                        item_code=item_code, unit=unit, evidence_state=ev,
                        measured_net=net if ev in BL.QUANTITY_STATES else None,
                        element_id=f"{room['room_id']}:{element}", floor=room["floor"], room_id=room["room_id"],
                        room_name_en=room["name_en"], room_name_ar=room["name_ar"], physical_element=element,
                        formula=formula, inputs=inputs, documents=ctx["documents"], geometry_source="CAD_VECTOR",
                        geometry_confidence="EXACT_FACE" if ev in BL.QUANTITY_STATES else "NOT_ESTABLISHED",
                        rule_id=ref["rule_id"], rule_version=ref["version"], rule_set=ref["rule_set"],
                        rule_set_digest=ref["rule_set_digest"], rfi=rfi, notes=notes, bounded_range=bounded,
                        material_state=material_state, item_en=en, item_ar=ar, trade=tr)


def _v29_masonry(S, floor, schedule, HE, texts, facts, u, ctx):
    """ARCH_TAKEOFF_V2.9 (UP-MAS-HEIGHT-001): per thickness family the wall panel area (ARCH.WALL_PANEL, m2) and volume
    (ARCH.WALL_VOLUME, m3) from the evidenced masonry height (engine.source.arch_v29.masonry_takeoff); MAS.BLOCK takes
    the panel area only when the family's material is stated (facts masonry.materials) - otherwise it stays an RFI
    naming exactly what is missing. -> (lines, unresolved, record)"""
    from functools import partial
    from engine.source import arch_v29 as V29M
    line = partial(_v29_line, rule_id="UP-MAS-HEIGHT-001")
    mev = V29M.masonry_evidence(HE.views, texts, floor, facts, u)
    take = V29M.masonry_takeoff(S["walls"], (), S["openings"], schedule, mev, u)   # V2.8 stubs are in the walls
    walls = {"room_id": f"{floor}-WALLS", "floor": floor, "name_en": "Walls", "name_ar": BL.ITEMS["ARCH.WALL_RUN"][1]}
    mats = (((facts or {}).get("masonry") or {}).get("materials") or {})
    lines, unres = [], []
    fams = {w["family"] for w in S["walls"]["walls"]}
    for k in sorted(fams):
        el = f"walls t={k}"
        r = take["families"].get(k)
        mat = mats.get(k)
        if r is None:
            why = mev.get("why") or take.get("state")
            q = f"MASONRY_NOT_MEASURED (walls t={k} m): {why}"
            for code, unit in (("ARCH.WALL_PANEL", "m2"), ("ARCH.WALL_VOLUME", "m3")):
                lines.append(line(ctx, item_code=code, room=walls, element=el, unit=unit, net=None,
                                       formula="wall-mass plan area / t x masonry height - openings",
                                       inputs={"thickness_family_m": k, "masonry_evidence": mev.get("state")},
                                       rfi={"question": q, "unlocks": walls["room_id"]}))
            unres.append({"room_id": walls["room_id"], "floor": floor, "item": f"ARCH.WALL_PANEL {el}", "reason": q})
        else:
            inp = {kk: r[kk] for kk in ("t_m", "walls", "stubs", "band_run_lm", "plan_m2", "run_equivalent_lm",
                                        "junction_in_family_m2", "panel_m", "panel_to_beam_m", "openings_held")}
            inp.update(openings=r["openings"], buildup_m=mev.get("buildup_m"), height_kind=mev.get("kind"),
                       beam=mev.get("beam"), sources=mev.get("sources"))
            f_area = ("wall-mass plan area / t (bands + stubs" + (" + junctions" if r["junction_in_family_m2"] else "")
                      + ") x panel height (T.O.S. to soffit) + the wall above / below each opening (width x (panel - "
                        "its height inside the panel))")
            if r["state"] == "MEASURED":
                pairs = (("ARCH.WALL_PANEL", "m2", r["area_m2"], None), ("ARCH.WALL_VOLUME", "m3", r["volume_m3"], None))
                for code, unit, v, b in pairs:
                    lines.append(line(ctx, item_code=code, room=walls, element=el, unit=unit, net=v,
                                           ev="PROVISIONAL", formula=f_area + (" x t" if unit == "m3" else ""),
                                           inputs=inp, notes="MASONRY_PANEL: the geometry of the wall panel; the "
                                           "wall material is a separate item (MAS.BLOCK)"))
            elif r["state"] == "RANGE":
                for code, unit, lo, hi in (("ARCH.WALL_PANEL", "m2", r["area_low_m2"], r["area_high_m2"]),
                                           ("ARCH.WALL_VOLUME", "m3", r["volume_low_m3"], r["volume_high_m3"])):
                    lines.append(line(ctx, item_code=code, room=walls, element=el, unit=unit, net=None,
                                           formula=f_area, inputs=inp,
                                           bounded={"low": lo, "high": hi, "basis": r["why"]}))
                unres.append({"room_id": walls["room_id"], "floor": floor, "item": f"ARCH.WALL_PANEL {el}",
                              "reason": f"MASONRY_PANEL_RANGE (walls t={k} m): {r['why']}"})
            else:
                q = f"MASONRY_PANEL_HELD (walls t={k} m): {r['why']}; upper bound {r['area_upper_m2']:.2f} m2"
                for code, unit, up in (("ARCH.WALL_PANEL", "m2", r["area_upper_m2"]),
                                       ("ARCH.WALL_VOLUME", "m3", r["volume_upper_m3"])):
                    lines.append(line(ctx, item_code=code, room=walls, element=el, unit=unit, net=None,
                                           formula=f_area, inputs=dict(inp, upper_bound=up),
                                           rfi={"question": q, "unlocks": walls["room_id"]}))
                unres.append({"room_id": walls["room_id"], "floor": floor, "item": f"ARCH.WALL_PANEL {el}",
                              "reason": q})
        # MAS.BLOCK: the material item - the panel area when the family's material is stated
        if r is not None and r["state"] == "MEASURED" and mat and mat.get("authority"):
            lines.append(line(ctx, item_code="MAS.BLOCK", room=walls, element=el, unit="m2", net=r["area_m2"],
                                   ev="PROVISIONAL", formula="ARCH.WALL_PANEL of the family (its material stated)",
                                   inputs={"thickness_family_m": k, "material": mat.get("value"),
                                           "material_authority": mat.get("authority"), "panel_m2": r["area_m2"]},
                                   material_state="PROJECT_OWNER_FACT",
                                   notes=f"MATERIAL {mat.get('value')} ({mat.get('authority')})"))
        else:
            miss = ([] if r is not None and r["state"] == "MEASURED" else ["the wall panel (" + (
                (r or {}).get("why") or mev.get("why") or "masonry height") + ")"]) + \
                ([] if mat and mat.get("authority") else ["the wall material of t=" + k + " m (block type / RC / "
                                                         "partition: legend, specification or a project fact)"])
            q = f"BLOCK_WALL_NOT_ESTABLISHED (walls t={k} m): " + "; ".join(miss)
            lines.append(line(ctx, item_code="MAS.BLOCK", room=walls, element=el, unit="m2", net=None,
                                   formula="ARCH.WALL_PANEL of the family x its stated material",
                                   inputs={"thickness_family_m": k, "panel": (r or {}).get("state"),
                                           "material": (mat or {}).get("value")},
                                   rfi={"question": q, "unlocks": walls["room_id"]}))
            unres.append({"room_id": walls["room_id"], "floor": floor, "item": f"MAS.BLOCK {el}", "reason": q})
    j = take.get("junction")
    if j:
        # the junction pieces between walls of different thicknesses: a volume, never an area of one thickness
        el = "walls junctions (mixed thickness)"
        inp = {"plan_m2": j["plan_m2"], "panel_m": mev.get("panel_m"), "note": j["note"]}
        if j["state"] == "MEASURED":
            lines.append(line(ctx, item_code="ARCH.WALL_VOLUME", room=walls, element=el, unit="m3",
                                   net=j["volume_m3"], ev="PROVISIONAL", formula="junction plan area x panel height",
                                   inputs=inp))
        elif j["state"] == "RANGE":
            lines.append(line(ctx, item_code="ARCH.WALL_VOLUME", room=walls, element=el, unit="m3", net=None,
                                   formula="junction plan area x panel height", inputs=inp,
                                   bounded={"low": j["volume_low_m3"], "high": j["volume_m3"],
                                            "basis": "the beam bottom of the floor's section"}))
        else:
            q = f"MASONRY_PANEL_HELD (junctions): upper bound {j['volume_m3']:.3f} m3; beams over walls not established"
            lines.append(line(ctx, item_code="ARCH.WALL_VOLUME", room=walls, element=el, unit="m3", net=None,
                                   formula="junction plan area x panel height", inputs=dict(inp, upper_bound=j["volume_m3"]),
                                   rfi={"question": q, "unlocks": walls["room_id"]}))
    rec = {"floor": floor, "evidence": mev, "families": take["families"], "junction": j, "state": take.get("state")}
    return lines, unres, rec


def _v29_facade(S, floor, schedule, HE, facts, ctx, lowest):
    """ARCH_TAKEOFF_V2.9 (UP-FACADE-001): the floor's facade run (ARCH.FACADE_RUN, lm: the exterior outline of its wall
    network, openings included), its area from the F.F.L. to the next floor's F.F.L. with each opening on the outline
    deducted (ARCH.FACADE, m2; engine.source.arch_v29.facade_takeoff) and the exterior finish (FIN.EXT.FINISH: the
    facade area when the finish is stated, otherwise an RFI). A second outline is reported, never added; an outline
    around the building holds the facade; the lowest floor's plinth (below its F.F.L.) is an RFI.
    -> (lines, unresolved, record)"""
    from functools import partial
    from engine.source import arch_v29 as V29M
    line = partial(_v29_line, rule_id="UP-FACADE-001")
    fo = (S.get("v29") or {}).get("facade") or {"state": "NO_OUTLINE", "outlines": [], "islands": 0}
    ev = V29M.facade_evidence(HE.views, floor, facts)
    fac = {"room_id": f"{floor}-FACADE", "floor": floor, "name_en": "Facade", "name_ar": V29_ITEMS["ARCH.FACADE"][1]}
    ops = {o["opening_id"]: o for o in S["openings"]}
    fin = (((facts or {}).get("facade") or {}).get("finish") or {})
    rec = {"floor": floor, "state": fo["state"], "outlines": fo["outlines"], "islands": fo["islands"],
           "line_networks": fo.get("line_networks"), "enclosed": fo.get("enclosed"), "height": ev,
           "lowest_floor": lowest}
    lines, unres = [], []
    f_run = "the outer cycle of the plan topology: wall faces + each opening's outer threshold"
    f_area = "facade run x (next F.F.L. - F.F.L.) - each opening on the outline x its own band"

    def held(code, el, unit, q, inputs, formula):
        lines.append(line(ctx, item_code=code, room=fac, element=el, unit=unit, net=None, formula=formula,
                               inputs=inputs, rfi={"question": q, "unlocks": fac["room_id"]}))
        unres.append({"room_id": fac["room_id"], "floor": floor, "item": f"{code} {el}", "reason": q})

    if fo["state"] in ("ENCLOSED_BUILDING", "NO_OUTLINE"):
        q = ("FACADE_NOT_MEASURED (ENCLOSED_BUILDING): the building's wall network stands inside another closed wall "
             "network (a boundary wall on a wall layer?): which outline is the facade is not established"
             if fo["state"] == "ENCLOSED_BUILDING" else "FACADE_NOT_MEASURED (NO_OUTLINE): no exterior outline")
        inp = {"outlines": [{k: o[k] for k in ("perimeter_m", "plate_m2")} for o in fo["outlines"]],
               "enclosed": [{k: o[k] for k in ("perimeter_m", "plate_m2")} for o in fo.get("enclosed") or ()]}
        for code, unit, f_ in (("ARCH.FACADE_RUN", "lm", f_run), ("ARCH.FACADE", "m2", f_area),
                               ("FIN.EXT.FINISH", "m2", "ARCH.FACADE x the stated exterior finish")):
            held(code, "facade", unit, q, inp, f_)
        return lines, unres, rec
    main = fo["outlines"][0]
    several = fo["state"] == "SEVERAL_OUTLINES"
    lines.append(line(ctx, item_code="ARCH.FACADE_RUN", room=fac, element="facade", unit="lm",
                           net=main["perimeter_m"], ev="PROVISIONAL" if several else "SOURCE_DERIVED", formula=f_run,
                           inputs={k: main[k] for k in ("perimeter_m", "plate_m2", "face_lm", "by_role", "openings",
                                                        "door_closures", "other_lm", "twice_lm")},
                           notes="FACADE: the largest of several exterior outlines (the others are RFIs, never "
                                 "added)" if several else "FACADE: the floor's one exterior outline"))
    for i, o in enumerate(fo["outlines"][1:], 2):
        held("ARCH.FACADE_RUN", f"facade outline {i}", "lm",
             f"ANOTHER_EXTERIOR_OUTLINE (facade outline {i}): {o['perimeter_m']:.2f} m around {o['plate_m2']:.2f} m2 - "
             "a separate building, a boundary wall or a drawing element; never added to the facade",
             {k: o[k] for k in ("perimeter_m", "plate_m2", "face_lm", "openings")}, f_run)
    take = V29M.facade_takeoff(main, ev, schedule, ops)
    rec["takeoff"] = take
    inp = {"perimeter_m": main["perimeter_m"], "height": {k: ev.get(k) for k in ("state", "height_m", "ffl_m", "kind",
                                                                                  "basis", "sources")}}
    if take["state"] == "NOT_ESTABLISHED":
        held("ARCH.FACADE", "facade", "m2", f"FACADE_AREA_NOT_MEASURED: {ev.get('why')}; run {main['perimeter_m']:.2f} m",
             inp, f_area)
    elif take["state"] == "MEASURED":
        lines.append(line(ctx, item_code="ARCH.FACADE", room=fac, element="facade", unit="m2",
                               net=take["net_m2"], ev="PROVISIONAL", formula=f_area,
                               inputs=dict(inp, gross_m2=take["gross_m2"], openings=take["openings"]),
                               notes="FACADE: the geometry of the exterior face; the finish is a separate item"))
    else:
        lines.append(line(ctx, item_code="ARCH.FACADE", room=fac, element="facade", unit="m2", net=None,
                               formula=f_area, inputs=dict(inp, gross_m2=take["gross_m2"], openings=take["openings"]),
                               bounded={"low": take["net_low_m2"], "high": take["net_high_m2"],
                                        "basis": "openings on the outline without an established height"}))
        unres.append({"room_id": fac["room_id"], "floor": floor, "item": "ARCH.FACADE facade",
                      "reason": "FACADE_RANGE: openings on the outline without an established height"})
    if take["state"] == "MEASURED" and fin.get("authority"):
        lines.append(line(ctx, item_code="FIN.EXT.FINISH", room=fac, element="facade", unit="m2",
                               net=take["net_m2"], ev="PROVISIONAL", formula="ARCH.FACADE (its finish stated)",
                               inputs={"finish": fin.get("value"), "finish_authority": fin.get("authority"),
                                       "facade_net_m2": take["net_m2"]},
                               material_state="PROJECT_OWNER_FACT", notes=f"FINISH {fin.get('value')} "
                                                                          f"({fin.get('authority')})"))
    else:
        miss = ([] if take["state"] == "MEASURED" else ["the facade area (" + (
            "its height" if take["state"] == "NOT_ESTABLISHED" else "opening heights") + ")"]) + \
            ([] if fin.get("authority") else ["the exterior finish (plaster / paint / cladding system: elevation "
                                              "notes, specification or a project fact)"])
        held("FIN.EXT.FINISH", "facade", "m2", "EXTERIOR_FINISH_NOT_SPECIFIED: " + "; ".join(miss)
             if not fin.get("authority") else "EXTERIOR_FINISH_HELD: " + "; ".join(miss),
             {"facade_net_m2": take.get("net_m2"), "facade_range_m2": [take.get("net_low_m2"), take.get("net_high_m2")]
              if take["state"] == "RANGE" else None, "finish": fin.get("value")},
             "ARCH.FACADE x the stated exterior finish")
    if lowest:
        held("ARCH.FACADE", "facade below F.F.L. (plinth)", "m2",
             "PLINTH_NOT_MEASURED: the facade below the lowest floor's F.F.L. down to the external ground level - the "
             "external ground level is not read from the drawing", {"perimeter_m": main["perimeter_m"]},
             "facade run x (F.F.L. - external ground level)")
    return lines, unres, rec


def _v29_curved_record(o, floor, rooms):
    """one curved opening of a floor: kind, room side, every published basis and the width taken."""
    cv = o["curved"]
    host = [r["room_id"] for r in rooms if o["opening_id"] in (r.get("doors") or []) + (r.get("windows") or []) +
            (r.get("passages") or [])]
    return {"floor": floor, "opening_id": o["opening_id"], "kind": o["kind"], "rooms": host,
            "width_m": round(o["width_m"], 6), "width_basis": cv["width_basis"], "room_side": cv["room_side"],
            "wall_t_m": round(o["wall_t_m"], 6), "r1_m": cv["r1_m"], "r2_m": cv["r2_m"], "sweep_rad": cv["sweep_rad"],
            "bases_m": cv["bases_m"], "glazing": {k: cv["glazing"][k] for k in ("share", "length_m", "radii_m")},
            "jambs": [o["start_jamb"], o["end_jamb"]], "door_symbol": o.get("door_symbol"),
            **({"note": cv["note"]} if cv.get("note") else {})}


def _v29_record(recs):
    from engine.source import arch_v29 as V29M
    return {"policy": V29M.policy_record(), "masonry": recs["masonry"], "facade": recs["facade"],
            "curved_openings": recs["curved_openings"],
            "curved_gaps_rejected": recs["curved_rejected"], "glazing_layers": recs["glazing_layers"],
            "summary": {"curved_openings": dict(Counter(x["kind"] for x in recs["curved_openings"])),
                        "curved_gaps_rejected": dict(Counter(x["reason"] for x in recs["curved_rejected"])),
                        "glazing_layers_inferred": len(recs["glazing_layers"]),
                        "facade": {x["floor"]: x["state"] for x in recs["facade"]}}}


def _v29_outputs(arch):
    """ARCH_TAKEOFF_V2.9: one correction record per curved opening, per glazing layer inferred and per floor's
    masonry panel and facade (continuing the V2.7 numbering), the run policy and the V2.9 summary."""
    log = arch["v27"]["corrections"]
    n = len(log)
    for x in arch["v29"]["curved_openings"]:
        n += 1
        log.append({"id": f"C27-{n:04d}", "correction": "CURVED_OPENING", "floor": x["floor"], "region_id": "-",
                    "subject": x["opening_id"], "decision": f"CURVED_{x['kind']}_CLOSED_ON_ITS_WALL_FACES",
                    "detail": {k: x[k] for k in ("kind", "rooms", "width_m", "width_basis", "room_side", "wall_t_m",
                                                 "r1_m", "r2_m", "sweep_rad", "glazing")}})
    for x in arch["v29"]["glazing_layers"]:
        n += 1
        log.append({"id": f"C27-{n:04d}", "correction": "CURVED_GLAZING_LAYER", "floor": x["floor"], "region_id": "-",
                    "subject": "layer", "decision": "WINDOW_ROLE_FROM_CURVED_GLAZING",
                    "detail": {"share_in_wall_gaps": x["share_in_wall_gaps"], "curved_gaps": x["curved_gaps"]}})
    for x in arch["v29"]["masonry"]:
        n += 1
        fam = {k: r["state"] for k, r in sorted(x["families"].items())}
        log.append({"id": f"C27-{n:04d}", "correction": "MASONRY_PANEL", "floor": x["floor"], "region_id": "-",
                    "subject": f"{x['floor']}-WALLS", "decision": f"MASONRY_PANEL_{x.get('state') or 'NOT_MEASURED'}",
                    "detail": {"evidence": x["evidence"].get("state"), "height_kind": x["evidence"].get("kind"),
                               "beam": x["evidence"].get("beam"), "families": fam,
                               "junction": (x.get("junction") or {}).get("state")}})
    for x in arch["v29"]["facade"]:
        n += 1
        log.append({"id": f"C27-{n:04d}", "correction": "FACADE", "floor": x["floor"], "region_id": "-",
                    "subject": f"{x['floor']}-FACADE", "decision": f"FACADE_{x['state']}",
                    "detail": {"outlines": [o["perimeter_m"] for o in x["outlines"]], "islands": x["islands"],
                               "height": x["height"].get("state"), "takeoff": (x.get("takeoff") or {}).get("state")}})
    arch["v27"]["summary"]["corrections"] = dict(Counter(c["correction"] for c in log))
    run = arch["run"]
    run.update(policy=ARCH_POLICY_ID_V29)
    run["v2_9"] = {"corrections": list(V29_CORRECTIONS), "knowledge": V29_KNOWLEDGE, "summary": arch["v29"]["summary"]}
    run["policies"]["arch_v29"] = arch["v29"]["policy"]
    if run.get("method") in (V210, V211):                      # T-034: ARCH_TAKEOFF_V2.10 (V2.11 builds on it)
        run.update(policy=ARCH_POLICY_ID_V210)
        run["v2_10"] = {"room_vocabulary": V210_VOCAB, "knowledge": V210_KNOWLEDGE,
                        "corrections": ["D-V210-01 room names (T-022, engine.source.room_vocab): compound phrases "
                                        "before bare words; a compound naming no room is held, never typed"]}


# ---------------------------------------------------------------- ARCH_TAKEOFF_V2.8 (Phase 2B-9)
V28_CORRECTIONS = (
    "D-V28-01 heights from the drawing (UP-HGT-001): element / room annotation > door-window schedule > section / "
    "elevation > derived > floor note > project note > project rule (facts) > Urban door default; each height with "
    "its source, value, unit and scope; floor-to-floor never a wall height (HEIGHT_EVIDENCE.json, "
    "MISSING_HEIGHT_EVIDENCE.json)",
    "D-V28-02 the opening schedule (UP-OPEN-SCHED-001): width, schedule width check, height, sill, head and class per "
    "opening; a window's finish deduction is its own band w x (min(head, H) - max(sill, 0)), never its full height "
    "above a lower finish (OPENING_SCHEDULE.json / .csv)",
    "D-V28-03 skirting at windows: floor-level glazing never skirted; a window whose sill is not established is not "
    "skirted with certainty (a range line)",
    "D-V28-04 window reveals and sills (UP-REVEAL-001): the reveal depth measured from the strip to the glazing, jambs "
    "and head as plaster (PROVISIONAL), the internal sill surface released as geometry, a floor-level window's strip "
    "as floor (WINDOW_REVEALS.json)",
    "D-V28-05 wall geometry per face (UP-WALL-GEOM-001): short returns and curved stubs under the 0.30 m band rule "
    "measured as wall, the plan area moved out of the junction pieces (WALL_GEOMETRY.json)")


def _v28_door_height(ctx, facts):
    """the door jamb plaster height under ARCH_TAKEOFF_V2.8: the door's own established height (annotation /
    schedule / section / project rule), else the UP-DOOR-HGT-001 fallback as before."""
    from engine.source import door_standards as DSTD

    def f(o):
        op = ((ctx or {}).get("schedule") or {}).get(o["opening_id"])
        h = (op or {}).get("height") or {}
        if h.get("value_m") is not None and h.get("governing") != "URBAN_DEFAULT":
            return {"value_m": h["value_m"], "state": "SOURCE", "source": h.get("authority"),
                    "precedence": h.get("governing")}
        return DSTD.door_height(DSTD.INTERNAL, facts)
    return f


def _v28_door_facts(door_facts, schedule):
    """the door model's facts under ARCH_TAKEOFF_V2.8: each door's own established height (not the Urban default),
    keyed by floor | opening (door_model._height reads it first)."""
    by_op = {}
    for op in schedule:
        h = op["height"]
        if op["kind"] == "DOOR" and h.get("value_m") is not None and h.get("governing") != "URBAN_DEFAULT":
            by_op[f"{op['floor']}|{op['opening_id']}"] = {"value_m": h["value_m"], "state": "SOURCE",
                                                          "source": f"V2.8 {h.get('governing')}",
                                                          "authority": h.get("authority")}
    return dict(door_facts or {}, opening_heights_by_opening=by_op) if by_op else door_facts


def _v28_room_heights(room):
    """the room's established plaster height under ARCH_TAKEOFF_V2.8 (arch_measure records it), or None."""
    h = ((room or {}).get("heights_v28") or {}).get("PLASTER") or {}
    return h.get("value_m") if h.get("state") == "ESTABLISHED" else None


def _v28_stubs(S, ents, roles, u, floor):
    """ARCH_TAKEOFF_V2.8 (UP-WALL-GEOM-001): the short returns and curved stubs of one floor joined to its walls
    (arch_walls records: the run, the thickness family, the plan strip), the junction pieces reduced by their plan
    area so the wall plan stays conserved. -> the stub records."""
    from engine.source import arch_plan as AP
    from engine.source import arch_v28 as V28M
    from engine.source import arch_walls as AW
    wall_l = sorted(lay for lay, ro in roles.items() if ro == AP.WALL)
    segs, arcs = defaultdict(list), defaultdict(list)
    for s_ in ents["segments"]:
        segs[s_["layer"]].append(s_)
    for a_ in ents.get("arcs") or ():
        arcs[a_["layer"]].append(a_)
    W = S["walls"]
    fams = sorted({w["t_m"] for w in W["walls"]})
    banded = {i for w in W["walls"] for i in w.get("source_ids") or ()}
    found = V28M.straight_stubs(segs, wall_l, W["walls"], u, families=fams) + \
        V28M.curved_stubs(arcs, wall_l, u, banded_ids=banded)
    recs = []
    for k, st in enumerate(found, 1):
        L = st.get("length_m") if st["kind"] == "RETURN_STUB" else st["centreline_m"]
        fam = AW._family(st["t_m"])
        rec = dict(st, stub_id=f"{floor}-STUB-{k:03d}", floor=floor, family=fam, run_lm=round(L, 6))
        rec.pop("mid", None)
        rec["centreline_m"] = [[round(c_ * u, 4) for c_ in p_] for p_ in st["centreline"]]
        rec.pop("centreline", None)
        recs.append(rec)
        W["walls"].append({"wall_id": rec["stub_id"], "layer": st["layer"], "t_m": st["t_m"], "family": fam,
                           "gross_lm": round(L, 6), "net_lm": round(L, 6), "columns_in_wall_lm": 0.0,
                           "strip_m2": st["plan_m2"], "sides": ["-", "-"], "kind": st["kind"],
                           "centreline": [tuple(p_) for p_ in st["centreline"]],
                           "source_ids": list(st["faces"]), "stub": True})
        row = next((r for r in W["by_thickness"] if r["family"] == fam), None)
        if row is None:
            row = {"family": fam, "walls": 0, "net_lm": 0.0, "gross_lm": 0.0, "strip_m2": 0.0, "external_lm": 0.0,
                   "internal_lm": 0.0, "columns_in_wall_lm": 0.0}
            W["by_thickness"].append(row)
            W["by_thickness"].sort(key=lambda r: r["family"])
        row["walls"] += 1
        for kk in ("net_lm", "gross_lm"):
            row[kk] = round(row[kk] + L, 6)
        row["strip_m2"] = round(row["strip_m2"] + st["plan_m2"], 6)
        row["stubs_lm"] = round(row.get("stubs_lm", 0.0) + L, 6)
    if recs:
        c = W["conservation"]
        plan = sum(r["plan_m2"] for r in recs)
        c["band_strips_m2"] = round(c["band_strips_m2"] + plan, 6)
        c["junction_m2"] = round(c["junction_m2"] - plan, 6)
        c["stubs_m2"] = round(plan, 6)
    return recs


def _v28_record(HE, recs, walls_of, rooms):
    """the ARCH_TAKEOFF_V2.8 outputs: the height evidence and what it decided, the missing evidence, the opening
    schedule, the window reveals and the wall geometry per face."""
    from engine.source import arch_v28 as V28M
    missing = []
    for r in recs["rooms"]:
        for tr, h in (r["heights"] or {}).items():
            if tr == "WALL_TILE" and not r.get("wet"):
                continue                                  # a dry room has no wall tile: no height is needed for it
            if (h or {}).get("state") != "ESTABLISHED" or (h or {}).get("governing") in ("PROJECT_RULE",):
                need = {"PLASTER": "the structural soffit level of the floor (a section: U/S SLAB / soffit) or a "
                                   "printed plaster height", "PAINT": "the finished ceiling level (a section / "
                                   "reflected ceiling plan: F.C.L.) or a printed ceiling height",
                        "WALL_TILE": "a printed wall-tile height, or the finished ceiling level (owner full height)"
                        }[tr]
                missing.append({"floor": r["floor"], "room_id": r["room_id"], "room": r["name_en"], "quantity": tr,
                                "state": (h or {}).get("state"), "governing": (h or {}).get("governing"),
                                "used": (h or {}).get("value_m"), "needed": need,
                                "why": (h or {}).get("why")})
    for o in recs["openings"]:
        for q in ("height", "sill"):
            if o["kind"] == "DOOR" and q == "sill":
                continue
            h = o[q]
            if h.get("value_m") is None or h.get("governing") in ("PROJECT_RULE", "URBAN_DEFAULT"):
                missing.append({"floor": o["floor"], "opening_id": o["opening_id"], "kind": o["kind"],
                                "quantity": q.upper(), "state": h.get("state"), "governing": h.get("governing"),
                                "used": h.get("value_m"), "why": h.get("why"),
                                "needed": ("the door / window schedule (mark next to the opening) or an elevation / "
                                           "section of the opening" if q == "height" else
                                           "the window's sill from the schedule, an elevation or a sill note")})
    walls = []
    for w in walls_of:
        for x in w["walls"]:
            walls.append({"floor": w["floor"], "wall_id": x["wall_id"], "kind": x.get("kind"), "t_m": x["t_m"],
                          "family": x["family"], "centreline_lm": x["net_lm"], "gross_lm": x["gross_lm"],
                          "plan_m2": x["strip_m2"], "sides": x.get("sides"), "stub": bool(x.get("stub")),
                          **_v28_curved_faces(x)})
    return {"policy": V28M.policy_record(),
            "evidence": {"schedules": HE.sched["schedules"], "schedule_findings": HE.sched["findings"],
                         "views": HE.views["views"], "view_findings": HE.views["findings"],
                         "project_notes": HE.project, "floors": recs["bindings"]},
            "rooms": recs["rooms"], "openings": recs["openings"], "missing": missing, "reveals": recs["reveals"],
            "walls": walls, "stubs": recs["stubs"], "lost_labels": recs["lost_labels"],
            "conservation": [{"floor": w["floor"], **w["conservation"]} for w in walls_of],
            "summary": {"rooms_with_drawing_heights": sum(
                1 for r in recs["rooms"] if any((h or {}).get("governing") not in (None, "PROJECT_RULE", "DERIVED")
                                                 for h in (r["heights"] or {}).values())),
                "openings": len(recs["openings"]),
                "openings_height_from_drawing": sum(1 for o in recs["openings"] if o["height"].get("governing") in (
                    "ELEMENT_ANNOTATION", "SCHEDULE", "SECTION", "ELEVATION", "FLOOR_NOTE", "PROJECT_NOTE")),
                "windows_sill_established": sum(1 for o in recs["openings"] if o["kind"] == "WINDOW" and
                                                o["sill"].get("value_m") is not None),
                "windows": sum(1 for o in recs["openings"] if o["kind"] == "WINDOW"),
                "stubs": len(recs["stubs"]), "stub_run_lm": round(sum(x["run_lm"] for x in recs["stubs"]), 6),
                "reveals_measured": sum(1 for r in recs["reveals"] if r.get("state") == "MEASURED"),
                "room_labels_not_closed": sum(1 for x in recs["lost_labels"]
                                              if x["finding"] == "ROOM_LABEL_NOT_IN_A_CLOSED_SPACE"),
                "open_area_labels_outside_rooms": sum(1 for x in recs["lost_labels"]
                                                      if x["finding"] == "OPEN_AREA_LABEL_OUTSIDE_ROOMS"),
                "missing_items": len(missing)}}


def _v28_curved_faces(x):
    """a curved wall's three measures kept apart (UP-WALL-GEOM-001): the inner and outer face arcs and the centreline
    (mid-band) arc, with the radii - the face a finish is on is never the mean radius."""
    cv = x.get("curved")
    if not cv:
        return {}
    b = cv.get("bases_lm") or {}
    return {"r_in_m": cv.get("r1_m"), "r_out_m": cv.get("r2_m"), "sweep_rad": cv.get("sweep_rad"),
            "arc_inner_m": b.get("MIN_RADIUS_ARC"), "arc_mid_m": b.get("MID_BAND_ARC"),
            "arc_outer_m": b.get("MAX_RADIUS_ARC"), "run_basis": cv.get("basis")}


OPENING_SCHEDULE_COLUMNS = ("floor", "opening_id", "kind", "class", "mark", "plan_width_m", "schedule_width_m",
                            "height_m", "height_source", "sill_m", "sill_source", "head_m", "area_m2", "area_state",
                            "findings")


def _opening_rows(v28):
    out = []
    for o in v28["openings"]:
        out.append({"floor": o["floor"], "opening_id": o["opening_id"], "kind": o["kind"], "class": o["class"],
                    "mark": (o.get("mark") or {}).get("mark"), "plan_width_m": o["plan_width_m"],
                    "schedule_width_m": (o.get("schedule") or {}).get("width_m"),
                    "height_m": o["height"].get("value_m"), "height_source": o["height"].get("governing"),
                    "sill_m": o["sill"].get("value_m"), "sill_source": o["sill"].get("governing"),
                    "head_m": o["head_m"], "area_m2": o["area_m2"], "area_state": o["area_state"],
                    "findings": "; ".join(f["code"] for f in o.get("findings") or ())})
    return out


def _v28_outputs(arch):
    # D-V28-05: one correction record per stub measured as wall (it continues the V2.7 / V2.7.1 numbering)
    log = arch["v27"]["corrections"]
    n = max([int(x["id"][4:]) for x in log + (arch["v27"].get("refusals") or []) if x.get("id")] or [0])
    for st in arch["v28"]["stubs"]:
        n += 1
        log.append({"id": f"C27-{n:04d}", "correction": "WALL_STUB", "floor": st["floor"], "region_id": "-",
                    "subject": st["stub_id"], "decision": "MEASURED_AS_WALL",
                    "detail": {k: st[k] for k in ("kind", "run_lm", "t_m", "family", "length_m", "inner_m", "outer_m",
                                                  "sweep_rad", "plan_m2", "centreline_m") if k in st}})
    # D-V28-03: one record per room whose window thresholds left the certain skirting
    for r in arch["v28"]["rooms"]:
        a = r.get("skirting_windows") or {}
        moved = {k: a.get(k, 0.0) for k in ("floor_glazing_lm", "to_range_lm", "floor_glazing_range_lm")}
        if not any(v > 1e-9 for v in moved.values()):
            continue
        n += 1
        log.append({"id": f"C27-{n:04d}", "correction": "WINDOW_SKIRTING", "floor": r["floor"], "region_id": "-",
                    "subject": r["room_id"], "decision": "CERTAIN_SKIRTING_ONLY",
                    "detail": dict(moved, windows={k: v["class"] for k, v in (a.get("by_window") or {}).items()},
                                   to_range_by=a.get("to_range_by") or {})})
    arch["v27"]["summary"]["corrections"] = dict(Counter(c["correction"] for c in log))
    run = arch["run"]
    run.update(policy=ARCH_POLICY_ID_V28)
    run["v2_8"] = {"corrections": list(V28_CORRECTIONS), "knowledge": V28_KNOWLEDGE,
                   "summary": arch["v28"]["summary"]}
    run["policies"]["arch_v28"] = arch["v28"]["policy"]


def _turned_jambs(S, u):
    """the openings with a COLUMN_JAMB end at a turned column (within the band-gap column reach + 10 mm)."""
    from engine.source import arch_plan as AP
    reach = 0.07 / u
    out = []
    for o in S.get("openings") or ():
        (ux, uy), (nx, ny) = o["u"], o["n"]
        mid = (o["o0"] + o["o1"]) / 2
        for s_, jamb in ((o["s0"], o.get("start_jamb")), (o["s1"], o.get("end_jamb"))):
            if jamb != "COLUMN_JAMB":
                continue
            pt = (ux * s_ + nx * mid, uy * s_ + ny * mid)
            if any(min(AP._d_point_seg(pt, poly[i - 1], poly[i]) for i in range(len(poly))) <= reach
                   for poly in S.get("column_polys") or ()):
                out.append(o["opening_id"])
    return sorted(set(out))


def _review_targets(arch):
    """the spaces under classification review (no room type) with their geometry and plausible classifications."""
    sm = {s["space_id"]: s for s in ((arch.get("space_model") or {}).get("spaces") or ())}
    by_op = {(o["floor"], o["opening_id"]): o for o in arch.get("openings") or ()}
    out = []
    for r in arch["rooms"]:
        issue = str(r.get("issue") or "")
        kind = next((k for k in WET_REVIEW_KINDS if issue.startswith(k)), None) or \
            ("UNLABELLED_SPACE" if r["class"] == "UNLABELLED" and "UNLABELLED_SPACE" in issue else None)
        if r["class"] != "UNLABELLED" or kind is None:
            continue
        node = sm.get(r["room_id"]) or {}
        sym = r.get("symbols_inside") or {}
        ops = [by_op[(r["floor"], i)] for i in r["doors"] + r["windows"] + r["passages"] if (r["floor"], i) in by_op]
        if kind == "UNLABELLED_SPACE":
            plausible, basis = [], ("NOT_ESTABLISHED: no fixture, water-closet shape or room word says what the "
                                    "space is (a store, a duct, an open court ...): nothing is released")
        elif sym.get("stair_flights") or sym.get("void_symbols"):
            plausible, basis = [], "NOT_ESTABLISHED: a stair or a void is drawn inside: the space may be unfinished"
        elif node.get("interior_status") in ("EXTERIOR", "POSSIBLY_EXTERIOR"):
            plausible, basis = [], (f"NOT_ESTABLISHED: the space may be exterior ({node.get('interior_status')}): "
                                    "its ceiling and finishes depend on it")
        else:
            plausible = [{"scenario": n, "codes": list(c), "why": w} for n, c, w in REVIEW_SCENARIOS]
            basis = ("a sanitary fixture or a water-closet shape is drawn inside an enclosed space reached by "
                     f"{len(r['doors'])} door(s) (space model: {node.get('interior_status') or 'UNKNOWN'}): a W.C. / "
                     "wash room (wet scope) or a lobby / wash area (dry scope); unfinished and exterior readings have "
                     "no evidence")
        out.append({"floor": r["floor"], "room_id": r["room_id"], "face_id": r["face_id"],
                    "region_id": r.get("region_id"), "issue_code": kind, "issue": issue,
                    "plausible": plausible, "plausible_basis": basis,
                    "geometry": {"area_m2": r["area_m2"], "gross_m2": r["gross_m2"],
                                 "obstruction_m2": r["obstruction_m2"], "perimeter_lm": r["perimeter_lm"],
                                 "wall_run_lm": round(r["runs_lm"].get("perimeter", 0.0) -
                                                      (r["runs_lm"].get("zone_line") or 0.0), 6),
                                 "openings": [{"opening_id": o["opening_id"], "kind": o["kind"], "width_m": o["width_m"],
                                               "wall_t_m": o["wall_t_m"]} for o in ops],
                                 "ceiling_plan_m2": round(max(r["area_m2"] - (r.get("void_m2") or 0.0) -
                                                              (r.get("double_height_m2") or 0.0), 0.0), 6),
                                 "double_height_m2": r.get("double_height_m2") or 0.0,
                                 "dims": r.get("dims")}})
    return out


def _key(ln):
    loc = ln.get("location") or {}
    return (loc.get("floor"), loc.get("room_id"), ln["item_code"], ln.get("physical_element"), ln["unit"])


def _rule_of(ln):
    return (ln.get("rule") or {}).get("rule_id")


def _review_release(targets, scen):
    """UP-REVIEW-001: per review space, the lines of its own location in every scenario run; a line is released when
    every scenario has it once with the same quantity, range, state and rule, and its system does not depend on the
    classification (plaster: the wall finish over it the same in every scenario). -> (release {(floor, face_id):
    [scenario line]}, analysis {room_id: {"released", "not_released"}})."""
    release, analysis = {}, {}
    names = [n for n, _c, _w in REVIEW_SCENARIOS]
    for tg in targets:
        if not tg["plausible"]:
            continue
        if any(scen.get(n) is None for n in names):
            analysis[tg["room_id"]] = {"released": [], "not_released": [
                {"item_code": "*", "element": "*", "reason": "SCENARIO_NOT_MEASURABLE"}]}
            continue
        per = {}
        for n in names:
            mine = [ln for ln in scen[n]["lines"] if (ln.get("location") or {}).get("room_id") == tg["room_id"]]
            per[n] = {}
            for ln in mine:
                per[n].setdefault((ln["item_code"], ln.get("physical_element"), ln["unit"]), []).append(ln)
        finishes = {n: sorted({k[0] for k in per[n] if k[0] in WALL_FINISH_CODES}) for n in names}
        keys = sorted(set().union(*[set(per[n]) for n in names]), key=lambda k: (k[0], str(k[1]), k[2]))
        rel, notr = [], []
        for k in keys:
            got = [per[n].get(k) or [] for n in names]
            vals = {n: _scenario_value(g) for n, g in zip(names, got)}
            if any(len(g) != 1 for g in got):
                notr.append({"item_code": k[0], "element": k[1], "reason": "ONLY_IN_SOME_SCENARIOS" if
                             any(not g for g in got) else "REPEATED_IN_A_SCENARIO", "values": vals})
                continue
            ls = [g[0] for g in got]
            if any(ln.get("measured_net") != ls[0].get("measured_net") or
                   ln.get("bounded_range") != ls[0].get("bounded_range") for ln in ls):
                notr.append({"item_code": k[0], "element": k[1], "reason": "QUANTITY_DIFFERS", "values": vals})
            elif any(_rule_of(ln) != _rule_of(ls[0]) for ln in ls):
                notr.append({"item_code": k[0], "element": k[1], "reason": "RULE_DIFFERS", "values": vals})
            elif any(ln["evidence_state"] != ls[0]["evidence_state"] for ln in ls):
                notr.append({"item_code": k[0], "element": k[1], "reason": "STATE_DIFFERS", "values": vals})
            elif k[0] == "FIN.PLASTER" and len({tuple(v) for v in finishes.values()}) > 1:
                notr.append({"item_code": k[0], "element": k[1], "reason": "SYSTEM_DEPENDS_ON_WALL_FINISH",
                             "detail": {n: v for n, v in finishes.items()}, "values": vals})
            elif not k[0].startswith("FIN."):
                # only the space's own finish surfaces are released: a door / opening / count line is measured
                # elsewhere in the main BOQ (it may sit at another room there)
                notr.append({"item_code": k[0], "element": k[1], "reason": "NOT_A_FINISH_OF_THE_SPACE",
                             "values": vals})
            else:
                rel.append(ls[0])
        if rel:
            release[(tg["floor"], tg["face_id"])] = rel
        # the wall face: the plaster measurement (wall run x plaster height - openings) when every scenario measures
        # it once and the same - geometry, whatever finish system the classification puts on it
        pl = [[ln for k, g in per[n].items() if k[0] == "FIN.PLASTER" for ln in g] for n in names]
        wall_face = _wall_face(names, pl)
        analysis[tg["room_id"]] = {"released": [(ln["item_code"], ln.get("physical_element"), ln["unit"])
                                                for ln in rel], "not_released": notr, "wall_face": wall_face}
    return release, analysis


def _scenario_value(lines):
    """a scenario's quantity of one item: the measured net, else its range ({"low", "high"}), else None."""
    if any(x.get("measured_net") is not None for x in lines):
        return round(sum(x.get("measured_net") or 0.0 for x in lines), 6)
    rng = [x.get("bounded_range") for x in lines if x.get("bounded_range")]
    if rng:
        return {"low": round(sum(r.get("low") or 0.0 for r in rng), 6),
                "high": round(sum(r.get("high") or 0.0 for r in rng), 6)}
    return None


def _wall_face(names, pl):
    """the wall face of a review space from each scenario's plaster line (wall run x plaster height - each opening):
    geometry whatever finish system the classification puts on it - never a BOQ line."""
    if not any(pl):
        return {"m2": None, "state": "NOT_MEASURED", "basis": "no scenario measures the wall face (heights)"}
    vals = [_scenario_value(g) if len(g) == 1 else None for g in pl]
    if all(v is None for v in vals):
        return {"m2": None, "state": "NOT_MEASURED",
                "basis": "no scenario measures the wall face (a height is not established: see the held plaster)"}
    ln = pl[0][0] if pl[0] else {}
    height = ((ln.get("calculation") or {}).get("inputs") or {}).get("height_m")
    if all(isinstance(v, (int, float)) for v in vals) and len(set(vals)) == 1:
        return {"m2": vals[0], "state": "CONFIRMED_GEOMETRY", "height_m": height,
                "basis": "the wall face measured (wall run x plaster height - each opening), the same in every "
                         "scenario; the finish system over it depends on the classification - geometry, not a BOQ line"}
    if all(isinstance(v, dict) for v in vals) and all(v == vals[0] for v in vals):
        return {"m2": None, "low_m2": vals[0]["low"], "high_m2": vals[0]["high"], "state": "BOUNDED_GEOMETRY",
                "height_m": height, "basis": (ln.get("bounded_range") or {}).get("basis") or
                "a range, the same in every scenario"}
    return {"m2": None, "state": "NOT_INVARIANT", "by_scenario": dict(zip(names, vals))}


def _released_lines(release, floor, rooms, ctx):
    """the released lines of this floor's review spaces: the scenario line itself (its id is the space's: the same room
    id, element, rule and unit) with the space's own names and the release note."""
    import copy
    out = []
    for r in rooms:
        for ln in release.get((floor, r["face_id"])) or ():
            x = copy.deepcopy(ln)
            x["location"] = dict(x["location"], room_name_en=r["name_en"], room_name_ar=r["name_ar"])
            x["notes"] = "; ".join(y for y in (
                "CLASSIFICATION_INVARIANT (UP-REVIEW-001): identical under every plausible classification of this "
                "review space (" + ", ".join(n for n, _c, _w in REVIEW_SCENARIOS) + "); the space's type stays under "
                "review", ln.get("notes") or "") if y)
            x["source"] = dict(x["source"], documents=list(ctx["documents"]))
            out.append(x)
    return out


def _opening_ids_of(ln):
    loc = ln.get("location") or {}
    text = " ".join(str(x) for x in (loc.get("room_id"), loc.get("element_id"), loc.get("room_name_en"),
                                     ln.get("physical_element")))
    return set(re.findall(r"OP-\d+", text))


def _conditional(tg, scen_lines, main_lines):
    """the scenario's lines that differ from the main BOQ at the review space and its openings: ADDED (only in the
    scenario), REMOVED (only in the main BOQ), CHANGED (another quantity / state)."""
    ops = {o["opening_id"] for o in tg["geometry"]["openings"]}

    def mine(ln):
        loc = ln.get("location") or {}
        if loc.get("room_id") == tg["room_id"] and ln["item_code"] == "ARCH.SPACE":
            return False                    # the space's own area record: a scenario measures the space as a room
        return loc.get("floor") == tg["floor"] and (loc.get("room_id") == tg["room_id"] or _opening_ids_of(ln) & ops)
    a = {}
    for ln in main_lines:
        if mine(ln):
            a.setdefault(_key(ln), []).append(ln)
    b = {}
    for ln in scen_lines:
        if mine(ln):
            b.setdefault(_key(ln), []).append(ln)
    out = []
    for k in sorted(set(a) | set(b), key=lambda k: tuple(str(x) for x in k)):
        la, lb = a.get(k) or [], b.get(k) or []
        qa = [(x.get("measured_net"), x.get("bounded_range"), x["evidence_state"]) for x in la]
        qb = [(x.get("measured_net"), x.get("bounded_range"), x["evidence_state"]) for x in lb]
        if qa == qb:
            continue
        sq = sum(x.get("measured_net") or 0.0 for x in lb) if lb and any(x.get("measured_net") is not None
                                                                          for x in lb) else None
        mq = sum(x.get("measured_net") or 0.0 for x in la) if la and any(x.get("measured_net") is not None
                                                                          for x in la) else None
        rng = next((x.get("bounded_range") for x in lb if x.get("bounded_range")), None)
        out.append({"floor": k[0], "room_id": k[1], "item_code": k[2], "element": k[3], "unit": k[4],
                    "change": "ADDED" if not la else ("REMOVED" if not lb else "CHANGED"),
                    "quantity": None if sq is None else round(sq, 6),
                    "low": (rng or {}).get("low"), "high": (rng or {}).get("high"),
                    "evidence_state": lb[0]["evidence_state"] if lb else None,
                    "rule_id": _rule_of(lb[0]) if lb else None,
                    "main_quantity": None if mq is None else round(mq, 6),
                    "main_evidence_state": la[0]["evidence_state"] if la else None})
    return out


def _quantity_classes(tg, geo, an):
    """the review space's quantities in the five classes of UP-REVIEW-001 (each item in one class only)."""
    g = [{"what": k, "value": geo.get(k)} for k in ("area_m2", "ceiling_plan_m2", "perimeter_lm", "wall_run_lm")]
    wf = geo.get("wall_face") or {}
    if wf.get("m2") is not None:
        g.append({"what": "wall_face_m2", "value": wf["m2"]})
    elif wf.get("state") == "BOUNDED_GEOMETRY":
        g.append({"what": "wall_face_m2", "value": {"low": wf["low_m2"], "high": wf["high_m2"]}, "basis": wf["basis"]})
    cls = {"GEOMETRY_CONFIRMED": g,
           "INDEPENDENT_OF_CLASSIFICATION": [{"item_code": c, "element": e, "unit": u}
                                             for c, e, u in an.get("released") or ()],
           "CONDITIONAL_ON_CLASSIFICATION": [], "REQUIRES_DRAWING_EVIDENCE": [], "NOT_ESTABLISHABLE": []}
    if not tg["plausible"]:
        cls["NOT_ESTABLISHABLE"].append({"item_code": "FIN.*", "reason": tg["plausible_basis"]})
        return cls
    for x in an.get("not_released") or ():
        vals = x.get("values") or {}
        if x["reason"] == "SCENARIO_NOT_MEASURABLE":
            cls["NOT_ESTABLISHABLE"].append({"item_code": x["item_code"], "reason": x["reason"]})
        elif any(v is not None for v in vals.values()):
            cls["CONDITIONAL_ON_CLASSIFICATION"].append({"item_code": x["item_code"], "element": x["element"],
                                                         "reason": x["reason"], "by_scenario": vals})
        else:
            cls["REQUIRES_DRAWING_EVIDENCE"].append({"item_code": x["item_code"], "element": x["element"],
                                                     "reason": "NO_SCENARIO_MEASURES_IT (a detail, a drain or a "
                                                               "height not in the drawing): " + x["reason"]})
    return cls


def _v271_outputs(room_boq, arch, targets, scen, analysis):
    """the review spaces, the door-standard reconciliation, the release report and the V2.7.1 correction records."""
    from engine.source import door_standards as DSTD
    from engine.source import knowledge as K
    lines = room_boq["lines"]
    by_id = {r["room_id"]: r for r in arch["rooms"]}
    spaces = []
    for tg in targets:
        rid = tg["room_id"]
        an = analysis.get(rid) or {"released": [], "not_released": []}
        rel_lines = [ln for ln in lines if (ln.get("location") or {}).get("room_id") == rid and
                     "CLASSIFICATION_INVARIANT" in (ln.get("notes") or "")]
        cond = {}
        doors = {}
        for n, _c, _w in REVIEW_SCENARIOS:
            if not tg["plausible"] or not scen.get(n):
                cond[n] = []
                continue
            cond[n] = _conditional(tg, scen[n]["lines"], lines)
            ops = {o["opening_id"] for o in tg["geometry"]["openings"]}
            doors[n] = [{"opening_id": d.get("opening_id"), "category": d["category"],
                         "owner_minimum_m": (d.get("opening_record") or {}).get("owner_minimum_m")}
                        for d in scen[n]["doors"] if d["floor"] == tg["floor"] and d.get("opening_id") in ops]
        geo = dict(tg["geometry"], wall_face=an.get("wall_face") or
                   {"m2": None, "state": "NOT_MEASURED" if tg["plausible"] else "NOT_ESTABLISHED"})
        spaces.append({**{k: tg[k] for k in ("floor", "room_id", "face_id", "issue_code", "plausible",
                                             "plausible_basis")},
                       "geometry": geo,
                       "quantity_classes": _quantity_classes(tg, geo, an),
                       "name_en": (by_id.get(rid) or {}).get("name_en"),
                       "released": [{"line_id": ln["line_id"], "item_code": ln["item_code"],
                                     "element": ln.get("physical_element"), "unit": ln["unit"],
                                     "quantity": ln.get("measured_net"), "evidence_state": ln["evidence_state"],
                                     "why": "identical under every plausible classification (same quantity, state, "
                                            "rule; a classification-independent system)"} for ln in rel_lines],
                       "not_released": an["not_released"], "conditional": cond, "doors_by_scenario": doors,
                       "never": "the scenarios added together or to the main BOQ"})
    arch["review_spaces"] = {"policy": "URBAN_REVIEW_SPACES_V1", "rule": "UP-REVIEW-001",
                             "scenarios": [{"scenario": n, "codes": list(c), "why": w} for n, c, w in REVIEW_SCENARIOS],
                             "spaces": spaces,
                             "summary": {"spaces": len(spaces),
                                         "with_plausible_scenarios": sum(1 for s in spaces if s["plausible"]),
                                         "released_lines": sum(len(s["released"]) for s in spaces),
                                         "released_by_item": dict(Counter(x["item_code"] for s in spaces
                                                                          for x in s["released"]))}}
    recon = DSTD.reconciliation_v271((arch.get("door_scenarios") or {}).get("rows") or [], arch.get("openings") or [])
    arch["door_reconciliation"] = recon
    sets = []
    for s in spaces:
        if s["plausible"]:
            sets.append({"set_id": f"REVIEW_CLASSIFICATION:{s['floor']}:{s['room_id']}", "kind": "REVIEW_CLASSIFICATION",
                         "subject": s["room_id"], "depends_on": ["the space's classification (UP-WET-002)"],
                         "scenarios": [n for n, _c, _w in REVIEW_SCENARIOS], "mutually_exclusive": True,
                         "by_scenario": {n: _totals(s["conditional"][n]) for n, _c, _w in REVIEW_SCENARIOS}})
    below = [d for d in recon["doors"] if (d["proposed_enlargement"]["STRUCTURAL_OPENING"]["m"] or 0) > 1e-6 or
             (d["proposed_enlargement"]["DOOR_LEAF"].get("high_m_with_unconfirmed_allowance") or 0) > 1e-6]
    if below:
        sets.append({"set_id": "DOOR_OWNER_MINIMUM", "kind": "DOOR_OWNER_MINIMUM", "subject": "doors below the owner "
                     "minimum on a reading", "depends_on": ["D-16"],
                     "scenarios": ["STRUCTURAL_OPENING_READING", "DOOR_LEAF_READING"], "mutually_exclusive": True,
                     "by_scenario": {
                         "STRUCTURAL_OPENING_READING": {
                             "doors": sum(1 for d in below if d["proposed_enlargement"]["STRUCTURAL_OPENING"]["m"]),
                             "enlargement_m": round(sum(d["proposed_enlargement"]["STRUCTURAL_OPENING"]["m"] or 0
                                                        for d in below), 6)},
                         "DOOR_LEAF_READING": {
                             "doors": len(below),
                             "enlargement_m": {"low": round(sum(d["proposed_enlargement"]["DOOR_LEAF"]["low_m"] or 0
                                                                for d in below), 6),
                                               "high_with_unconfirmed_allowance": round(sum(
                                                   d["proposed_enlargement"]["DOOR_LEAF"]
                                                   ["high_m_with_unconfirmed_allowance"] or 0 for d in below), 6)}}},
                     "note": "proposed modifications, not approved: never in the main BOQ"})
    arch["boq_scenarios"]["REVIEW_CLASSIFICATION"] = {"what": "the conditional quantities of each review space per "
                                                              "plausible classification (UP-REVIEW-001)",
                                                      "sets": [x for x in sets if x["kind"] == "REVIEW_CLASSIFICATION"]}
    arch["release_report"] = _release_report(lines, sets, arch.get("owner_questions"))
    log = arch["v27"]["corrections"]
    for s in spaces:
        for x in s["released"]:
            log.append({"correction": "REVIEW_INVARIANT_RELEASE", "floor": s["floor"], "region_id": "-",
                        "subject": s["room_id"], "decision": "RELEASED_INVARIANT_QUANTITY",
                        "detail": {"item_code": x["item_code"], "element": x["element"], "quantity": x["quantity"],
                                   "scenarios": [n for n, _c, _w in REVIEW_SCENARIOS]}})
    for rec in arch.get("v271_turned") or ():
        log.append(rec)
    # the V2.7.1 records continue the run's numbering (after every V2.7 correction and refusal)
    n = max([int(x["id"][4:]) for x in log + (arch["v27"].get("refusals") or []) if x.get("id")] or [0])
    for x in log:
        if not x.get("id"):
            n += 1
            x["id"] = f"C27-{n:04d}"
    arch["v27"]["summary"]["corrections"] = dict(Counter(c["correction"] for c in log))
    run = arch["run"]
    run.update(policy=ARCH_POLICY_ID_V271)
    run["v2_7_1"] = {"corrections": list(V271_CORRECTIONS), "knowledge": V271_KNOWLEDGE,
                     "review_spaces": arch["review_spaces"]["summary"], "door_reconciliation": recon["summary"],
                     "release_report": arch["release_report"]["conservation"],
                     "scenario_runs": sorted(n for n, v in scen.items() if v is not None)}
    run["policies"]["knowledge_1_3_0"] = K.policy_record()


def _totals(entries):
    t = {}
    for c in entries:
        k = f"{c['item_code']} [{c['unit']}]"
        t[k] = round(t.get(k, 0.0) + (c["quantity"] or 0.0) - (c["main_quantity"] or 0.0), 6)
    return {k: v for k, v in sorted(t.items()) if abs(v) > 1e-9}


HELD_CLASS = {"B_MISSING_DRAWING_EVIDENCE": "REQUIRES_DRAWING_EVIDENCE", "C_RULE_CONFLICT": "REQUIRES_OWNER_DECISION",
              "D_MISSING_OWNER_POLICY": "REQUIRES_OWNER_DECISION", "E_ENGINEERING_DEFECT": "ENGINEERING_REVIEW",
              "A_ESTABLISHED": "ENGINEERING_REVIEW"}


def _release_report(lines, sets, questions=None):
    """UP-QTY-STATUS-001: every BOQ line once - CONFIRMED (a quantity), HELD (a range or no quantity, with its reason
    class from the question catalogue), EXCLUDED (not applicable, with its reason) - and the CONDITIONAL scenario sets,
    never in a confirmed total."""
    from engine.source import knowledge as K
    cats = {"CONFIRMED": [], "HELD": [], "EXCLUDED": []}
    for ln in sorted(lines, key=lambda x: (str((x.get("location") or {}).get("floor")),
                                           str((x.get("location") or {}).get("room_id")), x["item_code"],
                                           str(x.get("physical_element")), x["line_id"])):
        loc = ln.get("location") or {}
        base = {"line_id": ln["line_id"], "item_code": ln["item_code"], "floor": loc.get("floor"),
                "room_id": loc.get("room_id"), "element": ln.get("physical_element"), "unit": ln["unit"],
                "evidence_state": ln["evidence_state"],
                "nature": "GEOMETRY_RECORD" if ln["item_code"].startswith("ARCH.") else "BOQ_ITEM"}
        ev = ln["evidence_state"]
        if ev in BL.QUANTITY_STATES and ln.get("measured_net") is not None:
            cats["CONFIRMED"].append(dict(base, quantity=ln["measured_net"]))
        elif ev in ("NOT_APPLICABLE_WITH_EVIDENCE", "EXCLUDED_WITH_REASON"):
            cats["EXCLUDED"].append(dict(base, reason=(ln.get("notes") or (ln.get("calculation") or {})
                                                       .get("formula") or ev)))
        else:
            q = ((ln.get("rfi") or {}).get("question") or (ln.get("bounded_range") or {}).get("basis") or
                 ln.get("notes") or "")
            c = K.classify_question({"item": ln["item_code"], "reason": q})
            rng = ln.get("bounded_range") or {}
            cats["HELD"].append(dict(base, low=rng.get("low"), high=rng.get("high"),
                                     reason_class=HELD_CLASS.get((c or {}).get("category"), "ENGINEERING_REVIEW"),
                                     question_group=(c or {}).get("group"), reason=q[:400]))
    tot = {}
    for x in cats["CONFIRMED"]:
        k = (x["item_code"], x["unit"], x["evidence_state"])
        tot[k] = tot.get(k, 0.0) + x["quantity"]
    ids = [x["line_id"] for c in cats.values() for x in c]
    held_by = Counter(x["reason_class"] for x in cats["HELD"])
    return {"policy": "URBAN_BOQ_RELEASE_REPORT_V1", "rule": "UP-QTY-STATUS-001",
            "categories": {"CONFIRMED": {"lines": cats["CONFIRMED"],
                                         "totals": [{"item_code": c, "unit": u_, "evidence_state": s,
                                                     "quantity": round(q, 6)} for (c, u_, s), q in sorted(tot.items())]},
                           "CONDITIONAL": {"scenario_sets": sets},
                           "HELD": {"lines": cats["HELD"], "by_reason_class": dict(sorted(held_by.items())),
                                    "ranges": {"low": round(sum(x["low"] or 0 for x in cats["HELD"]
                                                                if x["low"] is not None), 6),
                                               "high": round(sum(x["high"] or 0 for x in cats["HELD"]
                                                                 if x["high"] is not None), 6),
                                               "note": "summed over units: a count of exposure, never a quantity"}},
                           "EXCLUDED": {"lines": cats["EXCLUDED"],
                                        "by_item": dict(Counter(x["item_code"] for x in cats["EXCLUDED"]))}},
            "conservation": {"boq_lines": len(lines), "confirmed": len(cats["CONFIRMED"]), "held": len(cats["HELD"]),
                             "excluded": len(cats["EXCLUDED"]), "conditional_sets": len(sets),
                             "every_line_once": sorted(ids) == sorted(ln["line_id"] for ln in lines) and
                             len(set(ids)) == len(ids)},
            "never": ["a conditional quantity added to a confirmed total",
                      "two scenarios of one set added together", "a line in two categories",
                      "an unsupported quantity reported as zero"]}


V271_CORRECTIONS = (
    "D-V271-01 review spaces (UP-REVIEW-001): measured under every plausible classification; the quantities identical "
    "in all of them (same quantity, state and rule, a classification-independent system) released, the rest kept as "
    "conditional scenario quantities (REVIEW_SPACES.json), never added together",
    "D-V271-02 the BOQ release report (UP-QTY-STATUS-001): every line once as CONFIRMED / HELD (with its reason "
    "class) / EXCLUDED, the scenario sets CONDITIONAL (BOQ_RELEASE_REPORT.json / .csv)",
    "D-V271-03 the door-standard reconciliation (UP-DOOR-OPEN-003 1.3.0): as-drawn wall opening, measured jamb span, "
    "leaf, finished clear width, owner minimum, evidenced allowance only, proposed enlargement inside or beyond the "
    "drawn gap, consultant / structural review (DOOR_STANDARD_RECONCILIATION.json / .csv); nothing applied",
    "D-V271-04 water closets drawn as linework (UP-WET-002 1.3.0): the cistern on a wall face, a pan-width bowl, a "
    "round bowl centred on its cistern; every rejected candidate named",
    "D-V271-05 a basin block's own linework matched through the insert path of every entity drawn inside it (L-P7-03)",
    "D-V271-06 turned columns are jambs and wall interruptions (UP-COL-ORIENT-001)",
    "D-V271-07 doorway-strip lines traced to their strip faces and door closures; every untraced line says why")


def _v23_outputs(arch, room_boq, rooms, openings, doors, facts, decisions, decided, possibly_ext, shafts, method,
                 unresolved, drawing=None):
    """Phase 2B-1: the space model, the door scenarios (AS_DRAWN / OWNER_REQUIRED / UNRESOLVED), the elevator
    schedule, the grouped owner questions and the BOQ scenario views. Reads the finished lines; changes none."""
    from engine.source import door_standards as DSTD
    from engine.source import knowledge as K
    from engine.source import space_model as SMOD
    by_face = {fid: d for (_fl, fid), d in decided.items()}
    sm = SMOD.build(rooms, doors["elements"], possibly_external=possibly_ext, decisions_by_face=by_face)
    sm["decisions"] = {"schema": (decisions or {}).get("schema"), "given": len((decisions or {}).get("decisions") or ()),
                       "bound": sorted({d["id"] for d in by_face.values()}),
                       "unbound": [d.get("id") for d in SMOD.unbound(decisions, {d["id"] for d in by_face.values()})]}
    arch["space_model"] = sm
    v27 = method in V27_FAMILY
    arch["door_scenarios"] = DSTD.door_scenarios(doors, facts, openings=openings, rooms=rooms,
                                                 **({"v27": True} if v27 else {}))
    if v27:
        # ARCH_TAKEOFF_V2.7 (UP-DOOR-OPEN-003): which reading the owner minimum refers to is one owner question for
        # the run (OQ-05), never one per door; the readings stay side by side meanwhile
        ordinary = [r for r in arch["door_scenarios"]["rows"] if (r.get("opening_record") or {}).get("owner_question")]
        if ordinary:
            from engine.source import arch_completeness as AC
            unresolved.append(AC.flag({"room_id": "-", "floor": "-", "item": "DOOR.OPENING_RECORD (owner minimum)",
                                       "reason": f"DOOR_MINIMUM_REFERENCE (OQ-05): {len(ordinary)} door(s) - the "
                                                 "owner minimum (1.00 / 0.90 m) may refer to the structural opening, "
                                                 "the door leaf or the clear passage, and the 0.10 m frame allowance "
                                                 "of registry 1.1.0 requires confirmation; every reading is kept side "
                                                 "by side (UP-DOOR-OPEN-003)"}, drawing=drawing))
    arch["elevator_schedule"] = DSTD.elevator_schedule(doors, rooms, shafts)
    enlarged = [r for r in arch["door_scenarios"]["rows"] if r["review_status"] == "MODIFICATION_PROPOSED_NOT_APPROVED"]
    if enlarged:
        # the owner rule (UP-DOOR-OPEN-002) widens the wall opening; its head is not an owner rule (CF-11): one
        # owner question for the run, never one per door, and the widths themselves are never re-asked
        from engine.source import arch_completeness as AC
        unresolved.append(AC.flag({"room_id": "-", "floor": "-", "item": "DOOR.OWNER_REQUIRED (wall-opening head)",
                                   "reason": f"DOOR_OPENING_HEAD_ALLOWANCE (OQ-02): {len(enlarged)} door(s) below the "
                                             "owner opening standard; the enlarged wall opening's head is taken at "
                                             "the door height (ASSUMED) until an allowance is given"},
                                  drawing=drawing))
    arch["owner_questions"] = K.owner_questions(unresolved, method=method)
    rel = Counter()
    for ln in room_boq["lines"]:
        if ln["evidence_state"] in BL.QUANTITY_STATES and ln.get("measured_net") is not None:
            rel[(ln["item_code"], ln["unit"], ln["evidence_state"])] += ln["measured_net"]
    arch["boq_scenarios"] = {
        "policy": "BOQ_SCENARIOS_V1", "rule": "UP-KB-PREC-001", "method": method,
        "AS_DRAWN": {"what": "what the drawing establishes: the BOQ lines of this run by item and state (PROVISIONAL "
                             "is never confirmed)",
                     "by_item": [{"item_code": c, "unit": un, "state": st, "quantity": round(q, 6)}
                                 for (c, un, st), q in sorted(rel.items())]},
        "OWNER_REQUIRED": {"what": ("the owner minimum door openings (UP-DOOR-OPEN-003, registry 1.2.0) on the "
                                    "structural opening - the lower bound of every reading, no allowance added; the "
                                    "leaf and clear-passage readings are in each door's opening record (OQ-05); "
                                    "proposed modifications, not approved") if v27 else
                                   "the owner's approved design standards applied to the same elements (proposed "
                                   "modifications, not approved): doors (UP-DOOR-OPEN-002); no other owner-required "
                                   "modification is defined in knowledge registry 1.0.0",
                           "doors": arch["door_scenarios"]["views"]["OWNER_REQUIRED"],
                           "doors_with_enlargement": sum(1 for r in arch["door_scenarios"]["rows"]
                                                         if r["review_status"] == "MODIFICATION_PROPOSED_NOT_APPROVED"
                                                         and r["view"] == "AS_DRAWN")},
        "UNRESOLVED": {"what": "what cannot yet be quantified reliably",
                       "lines_without_quantity": dict(Counter(ln["item_code"] for ln in room_boq["lines"]
                                                              if ln["evidence_state"] not in BL.QUANTITY_STATES)),
                       "doors": arch["door_scenarios"]["views"]["UNRESOLVED"],
                       "question_groups": arch["owner_questions"]["summary"]["groups"]},
        "never": "the AS_DRAWN and OWNER_REQUIRED views added together"}
    arch["run"]["v2_3"] = {"knowledge": K.policy_record(), "space_model": sm["summary"],
                           "door_scenarios": arch["door_scenarios"]["conservation"],
                           "owner_questions": arch["owner_questions"]["summary"],
                           "elevator_shafts": len(arch["elevator_schedule"]["shafts"]),
                           "decisions": sm["decisions"]}


V25_CORRECTIONS = (
    "D-V25-01 band segment: the shortest whose lanes finish the band (one end lap per lane, not two)",
    "D-V25-02 a band segment that would open a roll is weighed against filling the largest open roll remainder",
    "D-V25-03 rolls: exact packing of the cut pieces (first fit decreasing missed the minimum)",
    "D-V25-04 membrane patches of a resolved corner / penetration detail are in B and in the rolls",
    "D-V25-05 a resolved threshold upturn closes the band loop; jamb returns extend the run",
    "D-V25-06 material basis: proven subtotal, provisional final requirement, roll count with every open doorway "
    "upturned",
    "D-V25-07 project rules bound to the drawing sha256 (a mismatch is refused)",
    "D-V25-08 BOQ traceability chain (owner rule -> drawing evidence -> formula -> independent check -> engine -> "
    "line)")


V26_CORRECTIONS = (
    "D-V26-01 the floor-to-wall junction is an open detail (UNRESOLVED) with its alternatives: separate upstand at "
    "the plan's flange, the widest flange with the same rolls and the first that adds one, continuous fold "
    "(rectangles); the material requirement stays provisional while it is open (F-01, F-09)",
    "D-V26-02 the piece-level cutting plan the engine cut: every cut, rip and cross-cut, each piece with id, size, "
    "source roll and destination; offcuts as real rectangles (the floor beyond a stepped wall included), classed "
    "TRUE_WASTE / REUSABLE_SUBJECT_TO_N7; roll stock apart (F-02, F-07)",
    "D-V26-03 band joints placed on their runs: distance to every corner and floor-seam end, JOINT_AT_CORNER / "
    "JOINT_ON_SEAM_END, the best order of the same pieces; JOINT_OFFSET_UNVERIFIED without a product value (F-03)",
    "D-V26-04 doorway jamb junctions named (BUTT_JOINT_OPEN, two per door), terminations at other breaks (F-04)",
    "D-V26-05 multi-layer points, end-lap stagger, penetration clearances, drains (NOT_SHOWN when not drawn) and the "
    "lay order from the drain (F-05, F-06, F-08)",
    "D-V26-06 door symbol reconciliation (Phase 2B-5 D-C1, arch_rooms.closure_in_passage / match_swings_review): a "
    "door leaf whose leaf-ray closure lies in a passage's gap, or a swing closing no gap whose hinge / leaf fits a "
    "passage within the review limits, makes that passage a DOOR held from every released total with both widths; "
    "a passage near an idle swing carries a note",
    "D-V26-07 doorway strip split at the opening boxes (Phase 2B-5 D-C2, arch_completeness.split_strips): a "
    "door / passage doorway face that runs on past its openings' jambs is split per opening when its threshold "
    "edges are both faces of its openings and every other edge is a wall line; each opening takes its box, the "
    "rest stays a WALL_BAND_REMAINDER strip with no quantity; the doorway waterproofing piece of a door closed by "
    "its leaf is the box between its two closures on the same proof")


V27_CORRECTIONS = (
    "D-V27-01 the door's structural opening from its own jamb lines when every remainder of the wall gap is wall on "
    "both faces (a wall return or a junction mouth); a wider opening is kept with the remainder's nature (open, "
    "column, glazed side panel, wall on one face); a held door that now fits strictly is released "
    "(arch_v27.jamb_reconstruction)",
    "D-V27-02 layer roles from geometry with explicit refusal (arch_v27.layer_roles): a single exploded or inserted "
    "door hinged at a wall-gap jamb is a DOOR, one to three glazing lines in door-free gaps a WINDOW; a layer "
    "carrying door swings is never a WINDOW; a layer drawing a door and glazing is refused",
    "D-V27-03 columns of any orientation, one polyline or four LINEs; a marked square under a 0.20 x 0.20 m column "
    "section is never a column (drains); one or two columns need a wall and must explain their layer, else refused",
    "D-V27-04 arc-aware room polygons (chords of sagitta <= 1 mm, vertices on the arc) and curved wall bands in the "
    "wall run on the centreline (MIN / MID / MAX bases published; D-07)",
    "D-V27-05 wet-room evidence UP-WET-002 (knowledge 1.2.0): a wash basin alone never makes a space wet; a basin "
    "and a second, independent piece of sanitary evidence (a water closet drawn as linework, sanitary-layer linework) "
    "do; one shape alone or an ambiguous space stays REVIEW, never DRY (arch_v27.wet_evidence)",
    "D-V27-06 the door opening record UP-DOOR-OPEN-003: structural opening, leaf, frame, clear passage, owner "
    "minimum, allowance (not established: the 1.1.0 registry's 0.10 m requires confirmation, OQ-05) and the "
    "proposed enlargement kept apart (door_standards.opening_record_v27); no quantity changes",
    "D-V27-07 a door block's frame read from the door symbol's own insert, not from a group or plan block around it "
    "(door_model.symbol_prefix)",
    "D-V27-08 a waterproofing boundary piece of at most 0.1 mm merged into its neighbour on the same edge "
    "(wp_geometry SLIVER_M), never typed as an open edge",
    "D-V27-09 per-line source entities: every room, opening and wall line carries the drawn entities it is measured "
    "from (handle, insert path, part; arch_v27.attach_provenance); no quantity changes")


def _v27_region_log(floor, rid, L, S, roles26, declared):
    """ARCH_TAKEOFF_V2.7: the corrections and refusals of one plan region - each layer whose role differs from the
    V2.6 inference (roles26) with the rule that decided it, jamb spans, turned columns, curved walls, arc polygons."""
    out = []
    for lay in sorted(L["roles"]):
        if lay in declared or L["roles"][lay] == roles26.get(lay):
            continue
        e = (L.get("evidence") or {}).get(lay) or {}
        out.append({"correction": "LAYER_ROLE", "floor": floor, "region_id": rid, "subject": lay,
                    "decision": L["roles"][lay], "before": roles26.get(lay),
                    "rule": e.get("column_rule") or e.get("door_rule") or e.get("window_rule") or
                    ("REFUSED (see refusals)" if any(x["layer"] == lay for x in L.get("refusals") or ()) else None)})
    for x in L.get("refusals") or ():
        out.append({"correction": "REFUSAL", "floor": floor, "region_id": rid, "subject": x["layer"],
                    "decision": "OTHER", **x})
    v = S.get("v27") or {}
    for j in v.get("jamb") or ():
        if j["decision"] in ("NARROWED_TO_JAMB_SPAN", "WIDER_OPENING_KEPT"):
            out.append({"correction": "DOOR_OPENING", "floor": floor, "region_id": rid, "subject": j["opening_id"],
                        "decision": j["decision"], "detail": j})
    if (v.get("columns") or {}).get("turned") or (v.get("columns") or {}).get("added"):
        out.append({"correction": "COLUMN_SHAPES", "floor": floor, "region_id": rid, "subject": "columns",
                    "decision": "TURNED_COLUMNS_IN_BOUNDARY" if v["columns"].get("turned") else
                    "COLUMN_BOXES_ADDED", "detail": v["columns"]})
    for w in (S.get("walls") or {}).get("walls") or ():
        if w.get("curved"):
            out.append({"correction": "CURVED_WALL_BAND", "floor": floor, "region_id": rid, "subject": w["wall_id"],
                        "decision": "IN_WALL_RUN", "detail": {k: w[k] for k in ("t_m", "gross_lm", "net_lm",
                                                                                 "strip_m2", "sides", "curved")}})
    final = {f["face_id"] for f in S.get("faces") or ()}
    for fid, w in sorted((v.get("wet") or {}).items()):
        if fid in final and w.get("decision") != "V2_6_READING":
            out.append({"correction": "WET_EVIDENCE", "floor": floor, "region_id": rid, "subject": fid,
                        "decision": w["decision"], "detail": w})
    arc_faces = [f["face_id"] for f in S.get("faces") or () if f.get("arc_vertices")]
    if arc_faces:
        out.append({"correction": "ARC_POLYGON", "floor": floor, "region_id": rid, "subject": "faces",
                    "decision": "POLYGON_FOLLOWS_ARCS", "detail": {"faces": arc_faces}})
    return out


def _v27_outputs(log):
    for i, x in enumerate(log, 1):
        x["id"] = f"C27-{i:04d}"
    corr = [x for x in log if x["correction"] != "REFUSAL"]
    ref = [{k: v for k, v in x.items() if k not in ("correction", "decision")} for x in log
           if x["correction"] == "REFUSAL"]
    return {"policy": "URBAN_V27_CORRECTIONS_V1", "corrections": corr, "refusals": ref,
            "summary": {"corrections": dict(Counter(x["correction"] for x in corr)),
                        "refusals": dict(Counter(x["code"] for x in ref))},
            "never": "a quantity changed by V2.7 without a record here"}


def _v25_binding(doc, docs):
    """ARCH_TAKEOFF_V2.5 (O-8): a project rules file names the drawing it was written for (drawing_sha256); another
    drawing's file is refused; a file that names none is applied but flagged (PROJECT_RULES_NOT_BOUND)."""
    sha = (docs[0] or {}).get("sha256")
    named = doc.get("drawing_sha256")
    if not doc.get("rules"):
        return {"state": "NO_PROJECT_RULES", "drawing_sha256": sha}
    if named is None:
        return {"state": "PROJECT_RULES_NOT_BOUND", "drawing_sha256": sha,
                "note": "the project rules file names no drawing_sha256: it is applied, but nothing proves it was "
                        "written for this drawing"}
    if named != sha:
        raise SystemExit(f"PROJECT_RULES_DRAWING_MISMATCH: the project rules were written for drawing {named}, this "
                         f"drawing is {sha} - refused (ARCH_TAKEOFF_V2.5, UP-RULES-001)")
    return {"state": "BOUND", "drawing_sha256": sha}


def _v24_stage(floors, doors, lines, mats, unresolved, facts, decisions, project_rules, pid, rev, docs, u, v25=False,
               independent=None, v26=False, v27=False):
    """Phase 2B-2 (ARCH_TAKEOFF_V2.4): the Project Engineering Rules Sheet (project rules bound to the drawing's
    elements), then the quantities that depend on a rule value - the waterproofing system (the wet-room / exterior
    upturn, doorway transitions, terminations, penetrations, layouts, the cutting plan per membrane system), the door
    feasibility and the door jamb plaster by category height. -> (lines, materials, unresolved, outputs)."""
    from engine.source import door_feasibility as DF
    from engine.source import project_rules as PRJ
    from engine.source import waterproofing_system as WS
    doc = PRJ.load(project_rules if project_rules is not None else {"schema": PRJ.SCHEMA, "rules": []})
    binding = _v25_binding(doc, docs) if v25 else None
    rooms_m, ops_m, walls_m = [], [], []
    for f in floors:
        rooms_m += [{"room_id": r["room_id"], "floor": f["floor"], "polygon_m": r["polygon_m"],
                     "hole_polygons_m": r.get("hole_polygons_m") or []} for r in f["M"]["rooms"]]
        ops_m += [{"floor": f["floor"], "opening_id": o["opening_id"],
                   "centre_m": (o.get("position") or {}).get("centre_m")} for o in f["M"]["openings"]]
        for w in (f["S"].get("walls") or {}).get("walls") or ():
            cl = w.get("centreline")
            if cl:
                walls_m.append({"floor": f["floor"], "wall_id": w["wall_id"], "t_m": w["t_m"],
                                "centreline_m": [(cl[0][0] * u, cl[0][1] * u), (cl[1][0] * u, cl[1][1] * u)]})
    bindings = PRJ.bind(doc, rooms=rooms_m, openings=ops_m, walls=walls_m)
    resolver = PRJ.Resolver(doc, bindings=bindings)
    sheet = PRJ.rules_sheet(doc, bindings=bindings, project_id=pid, drawing=docs[0], facts=facts, decisions=decisions)
    ctx = {"project_id": pid, "revision_set_sha256": rev, "documents": docs}
    wp_ids = {ln["location"]["room_id"] for ln in lines if ln["item_code"] == "FIN.WP.FLOOR" and
              ln.get("measured_net") is not None}
    areas = []
    for f in floors:
        mf = dict(f["M"], lines=[ln for ln in lines if ln["location"].get("floor") == f["floor"]])
        areas += WS.areas_from_floor(f["S"], mf, f["ents"], f["roles"], u, wp_room_ids=wp_ids,
                                     **({"v26": True} if v26 else {}), **({"v27": True} if v27 else {}))
    built = [WS.build_area(a, resolver, **({"v25": True} if v25 else {}), **({"v26": True} if v26 else {}))
             for a in areas]
    plans = WS.cutting_plan(built, **({"exact": True} if v25 else {}), **({"cut_ids": True} if v26 else {}))
    sched = WS.schedule(built, plans)
    wl, wu = WS.boq_lines(ctx, built, WS.wp_line)
    ids = {a["room_id"] for a in built}
    lines = [ln for ln in lines if not (ln["item_code"] == "FIN.WP.UPTURN" and ln["location"].get("room_id") in ids)]
    lines += wl
    unresolved = [x for x in unresolved if not (x.get("room_id") in ids and (
        str(x.get("reason") or "").startswith("EXTERIOR_WP_UPTURN_BY_SPECIFICATION") or
        x.get("item") == "FIN.WP (membrane)"))] + wu
    mats = [m for m in mats if not ((m.get("method") or "").startswith("MEMBRANE") and
                                    (m.get("location") or {}).get("room_id") in ids)] + [a["layout"] for a in built]
    contexts = {f["floor"]: DF.floor_context(f["S"], f["ents"], f["roles"], u, f["M"]["rooms"], f["floor"],
                                             walls=f["S"].get("walls")) for f in floors}
    rep = DF.feasibility(doors, contexts, resolver=resolver, facts=facts, **({"v25": True} if v25 else {}))
    lines, ju = DF.jamb_plaster_lines(ctx, lines, doors, resolver, facts, WS.wp_line)
    unresolved += ju
    # one question per conflict (its C- row), per unbound and per unsupported project rule
    raised = [r for r in sheet["rows"] if r["status"] in ("CONFLICT_REVIEW", "ENGINE_LIMITATION") and (
        r["row_id"].startswith("C-") or (r.get("project_rule_id") and not r["notes"].startswith("PROJECT_RULE_CONFLICT")))]
    for r in raised:
        unresolved.append({"room_id": "-", "floor": "-", "item": "PROJECT_RULES", "reason": r["notes"]})
    approvals = [dict(a, subject="DOOR") for a in rep["approvals"]]
    for p_ in plans:
        if p_["roll_count_state"] != "CONFIRMED":
            approvals.append({"subject": "WATERPROOFING", "system_id": p_["system_id"], "who": "consultant / "
                              "waterproofing specialist", "what": "the membrane system and its details before the "
                              "roll count is confirmed: " + "; ".join(p_["why_not_confirmed"])})
    for r in raised:
        if r["status"] == "CONFLICT_REVIEW":
            approvals.append({"subject": "PROJECT_RULES", "row_id": r["row_id"], "who": "project consultant",
                              "what": r["notes"]})
    sheet = dict(sheet, usage=resolver.usage())
    out = {"rules_sheet": sheet, "waterproofing": sched, "door_feasibility": rep, "approvals": approvals,
           "areas": built}
    if v27:
        out["v27_slivers"] = [{"room_id": a["room_id"], "floor": a["floor"], "sliver": a["sliver_v27"]}
                              for a in areas if a.get("sliver_v27")]
    if v25:
        from engine.source import traceability as TR
        sheet["drawing_binding"] = binding
        if binding["state"] == "PROJECT_RULES_NOT_BOUND":
            unresolved.append({"room_id": "-", "floor": "-", "item": "PROJECT_RULES", "reason": binding["note"]})
            approvals.append({"subject": "PROJECT_RULES", "who": "project consultant", "what": "bind the project "
                              "rules to the drawing revision (drawing_sha256)"})
        out["drawing_binding"] = binding
        out["traceability"] = TR.chain(lines, sheet, independent=independent)
    if v26:
        out["wp_install"] = WS.installation_outputs(built)
    return lines, mats, unresolved, out


def _v24_outputs(arch, out):
    """Phase 2B-2: the rules sheet, the waterproofing schedule and cutting plan, the door feasibility, the approvals
    and the engineering summary (the eight questions of the owner program); the BOQ scenario views gain the
    OWNER_STANDARD / PROPOSED_MODIFICATION door views and the waterproofing procurement view."""
    arch["rules_sheet"] = out["rules_sheet"]
    if out.get("traceability") is not None:                     # ARCH_TAKEOFF_V2.5
        arch["traceability"] = out["traceability"]
    if out.get("wp_install") is not None:                       # ARCH_TAKEOFF_V2.6
        arch["wp_install"] = out["wp_install"]
    arch["waterproofing"] = out["waterproofing"]
    arch["door_feasibility"] = out["door_feasibility"]
    arch["approvals"] = {"policy": "APPROVALS_REQUIRED_V1", "items": out["approvals"],
                         "never": "a proposed modification or a withheld quantity released before its approval"}
    df = out["door_feasibility"]
    bs = arch["boq_scenarios"]
    bs["OWNER_STANDARD"] = {"what": "the door standard each door requires (UP-DOOR-OPEN-002, project rules applied)",
                            "doors": df["views"]["OWNER_STANDARD"]}
    bs["PROPOSED_MODIFICATION"] = {"what": "wall-opening enlargements the owner standard needs, with their "
                                           "feasibility class (not approved; never in the as-drawn lines)",
                                   "doors": df["views"]["PROPOSED_MODIFICATION"]}
    wp = out["waterproofing"]
    bs["WATERPROOFING_PROCUREMENT"] = {"what": "C: whole rolls of the cutting plan per membrane system (a procurement "
                                               "view; never a BOQ line, never a total across systems)",
                                       "systems": {s["system_id"]: {"rolls": s["rolls"],
                                                                    "state": s["roll_count_state"],
                                                                    "net_m2": s["net_m2"],
                                                                    "installed_m2": s["installed_m2"]}
                                                   for s in wp["systems"]}}
    bs["never"] = "the AS_DRAWN, OWNER_STANDARD / OWNER_REQUIRED and PROPOSED_MODIFICATION views added together"
    arch["engineering_summary"] = _engineering_summary(arch, out)


def _engineering_summary(arch, out):
    """the eight questions of the owner program, answered from this run's own outputs."""
    sh, df, wp = out["rules_sheet"], out["door_feasibility"], out["waterproofing"]
    lines = arch["boq_scenarios"]["AS_DRAWN"]["by_item"]
    st = Counter()
    for r in arch["ledger"]["records"] if arch.get("ledger") else ():
        st[r["status"]] += 1
    rows = df["rows"]
    below = [r for r in rows if r.get("compliance") == "ENLARGEMENT_REQUIRED"]
    proj = [r for r in sh["rows"] if r.get("project_rule_id") and r["status"] in ("PROJECT_SPECIFIED",
                                                                                   "OWNER_PROJECT_APPROVED",
                                                                                   "DRAWING_CONFIRMED")]
    return {"policy": "ENGINEERING_SUMMARY_V1", "rules_sha256": sh["rules_sha256"],
            "what_the_drawing_shows": {
                "rooms": len(arch["rooms"]), "door_elements": len(rows),
                "doors_released_as_drawn": sum(1 for r in rows if r.get("released_as_drawn")),
                "waterproofed_areas": len(wp["areas"]),
                "boq_lines_by_item_state": len(lines)},
            "what_urban_requires": {
                "status_counts": sh["status_counts"],
                "door_standard": {r["category"]: r["standard"]["required_wall_opening_m"] for r in rows
                                  if r.get("standard") and r["standard"].get("required_wall_opening_m")},
                "waterproofing": {"upturn_h_m": K_value("UP-WP-003", "upturn_h_m"),
                                  "lap_m": K_value("UP-WP-002", "lap_m"),
                                  "roll_m": [K_value("UP-WP-001", "roll_width_m"),
                                             K_value("UP-WP-001", "roll_length_m")]}},
            "where_they_differ": {
                "doors_below_standard": len(below),
                "total_enlargement_m": round(sum(r["enlargement_m"] for r in below), 6),
                "doorway_transitions_unresolved": sum(a["doorway_transitions"]["unresolved"] for a in wp["areas"]),
                "project_rules_applied": [r["project_rule_id"] for r in proj]},
            "can_the_modification_fit": df["summary"],
            "measured_assumed_proposed_unresolved": {
                "ledger_records_by_status": dict(sorted(st.items())),
                "door_views": {k: v for k, v in df["views"].items() if k != "note"},
                "rules_assumed_owner_standard": sh["status_counts"]["OWNER_STANDARD_ASSUMED"]},
            "material_needed": {s["system_id"]: {k: s[k] for k in ("net_m2", "installed_m2", "consumed_m2",
                                                                    "cutting_waste_m2", "rolls",
                                                                    "rolls_if_each_area_alone", "roll_count_state")}
                                | {"withheld_detailing": len(s["withheld_detailing"])} for s in wp["systems"]},
            "governing_project_rules": {"rules_sha256": sh["rules_sha256"], "rows": [
                {"row_id": r["row_id"], "rule_id": r["rule_id"], "applied": r["applied_rule"]["value"],
                 "urban": r["urban_standard"]["value"], "scope": r["scope"], "source": r["source"]} for r in proj]},
            "approvals_needed": {"items": len(out["approvals"]),
                                 "owner_questions": [q["id"] for q in (arch.get("owner_questions") or {})
                                                     .get("owner_questions") or ()]}}


V24_MANIFEST = "OUTPUT_MANIFEST.json"


def _v24_manifest(out, names, arch):
    """the Phase 2B-2 output manifest: the rules sheet and registry every file of this run was computed with, the SHA-256
    of each file (a file without an embedded run record - CSV, BOQ lines, workbook, overlay - is bound here)."""
    import hashlib
    sh, k = arch["rules_sheet"], arch["run"]["v2_4"]["knowledge"]
    return {"policy": {V25: "URBAN_OUTPUT_MANIFEST_V2_5", V26: "URBAN_OUTPUT_MANIFEST_V2_6",
                       V27: "URBAN_OUTPUT_MANIFEST_V2_7", V271: "URBAN_OUTPUT_MANIFEST_V2_7_1",
                       V28: "URBAN_OUTPUT_MANIFEST_V2_8", V29: "URBAN_OUTPUT_MANIFEST_V2_9",
                       V210: "URBAN_OUTPUT_MANIFEST_V2_10", V211: "URBAN_OUTPUT_MANIFEST_V2_11"}.get(
                arch["run"]["method"], "URBAN_OUTPUT_MANIFEST_V2_4"),
            "method": arch["run"]["method"],
            "rules_sheet": {"schema": sh["schema"], "rules_sha256": sh["rules_sha256"],
                            "sheet_sha256": sh["sheet_sha256"], "invalidation": (sh.get("invalidation") or {})
                            .get("state")},
            "knowledge": {"rule_set": k["rule_set"], "digest": k["digest"]},
            "files": [{"name": n, "sha256": hashlib.sha256((Path(out) / n).read_bytes()).hexdigest(),
                       "bytes": (Path(out) / n).stat().st_size,
                       "embeds_rules_sha256": sh["rules_sha256"].encode() in (Path(out) / n).read_bytes()}
                      for n in sorted(set(names))],
            "never": "an output reused after the rules sheet changed (it is moved to SUPERSEDED_n)"}


def K_value(rule_id, key):
    from engine.source import knowledge as K
    return K.rule(rule_id)["logic"][key]


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


def _v21_doors(door_floors, door_texts, door_face_texts, regs, spaces_of, lines, u, facts, pid, rev, docs,
               guards=False, not_entrance_codes=()):
    """ARCH_TAKEOFF_V2.1: the building door model; the ARCH.DOOR opening counts are replaced by the owner door
    classes (released doors only), lift entrances leave the ordinary opening lines; every finding becomes a flag; a
    swing without exactly one element fails the floor's coverage gate (exit 3)."""
    from engine.source import arch_measure as AM
    from engine.source import door_model as DMOD
    from engine.source import rule_store as RS
    measured = [r for r in regs if r["region_id"] in spaces_of and not r.get("warning")]
    entrance = min(measured, key=lambda r: r["order"])["floor"] if measured else None
    if guards:
        model = DMOD.building_model(door_floors, door_texts, door_face_texts, u, entrance_floor=entrance, facts=facts,
                                    guards=True, **({"not_entrance_codes": not_entrance_codes}
                                                    if not_entrance_codes else {}))
    else:
        model = DMOD.building_model(door_floors, door_texts, door_face_texts, u, entrance_floor=entrance, facts=facts)
    lift_ops = {o_["opening_id"] for o_ in model.get("lift_openings") or ()}
    keep = [ln for ln in lines if ln["item_code"] != "ARCH.DOOR" and not
            (ln["item_code"] == "ARCH.PASSAGE" and ln["physical_element"] in lift_ops)]
    if guards:
        # ARCH_TAKEOFF_V2.2 (F-22): a lift-entrance candidate stays in the BOQ as a PROVISIONAL passage (not released,
        # not excluded) until a lift word, a lift schedule or the owner says what it is
        cand = {(c_["floor"], c_["opening_id"]): c_ for c_ in model.get("lift_candidates") or ()}
        for i, ln in enumerate(keep):
            c_ = cand.get((ln["location"].get("floor"), ln["physical_element"])) \
                if ln["item_code"] == "ARCH.PASSAGE" else None
            if c_ is not None:
                keep[i] = BL.validate(dict(ln, evidence_state="PROVISIONAL",
                                           notes=((ln.get("notes") or "") + "; " if ln.get("notes") else "") +
                                           "LIFT_ENTRANCE_CANDIDATE: " + c_["evidence"] + " - not released"))
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
    if arch.get("door_scenarios") is not None:                  # ARCH_TAKEOFF_V2.3
        files["SPACE_MODEL.json"] = _j({"run": run, "space_model": arch["space_model"]})
        files["DOOR_SCENARIOS.json"] = _j({"run": run, "doors": arch["door_scenarios"]})
        files["DOOR_SCENARIOS.csv"] = _csv([_door_row(r) for r in arch["door_scenarios"]["rows"]], DOOR_SCENARIO_COLUMNS)
        files["ELEVATOR_SCHEDULE.json"] = _j({"run": run, "elevators": arch["elevator_schedule"]})
        files["OWNER_QUESTIONS.json"] = _j({"run": run, "questions": arch["owner_questions"]})
        files["BOQ_SCENARIOS.json"] = _j({"run": run, "scenarios": arch["boq_scenarios"]})
    if arch.get("v27") is not None:                            # ARCH_TAKEOFF_V2.7
        files["CORRECTIONS_V2_7.json"] = _j({"run": run, **arch["v27"]})
    if arch.get("release_report") is not None:                 # ARCH_TAKEOFF_V2.7.1
        from engine.source import door_standards as DSTD
        files["REVIEW_SPACES.json"] = _j({"run": run, **arch["review_spaces"]})
        files["BOQ_RELEASE_REPORT.json"] = _j({"run": run, **arch["release_report"]})
        files["BOQ_RELEASE_REPORT.csv"] = _csv(_release_rows(arch["release_report"]), RELEASE_COLUMNS)
        files["DOOR_STANDARD_RECONCILIATION.json"] = _j({"run": run, **arch["door_reconciliation"]})
        files["DOOR_STANDARD_RECONCILIATION.csv"] = _csv(DSTD.reconciliation_csv_rows(arch["door_reconciliation"]),
                                                         DSTD.RECON_COLUMNS)
    if arch.get("v28") is not None:                            # ARCH_TAKEOFF_V2.8
        v8 = arch["v28"]
        files["HEIGHT_EVIDENCE.json"] = _j({"run": run, "policy": v8["policy"], "evidence": v8["evidence"],
                                            "rooms": v8["rooms"], "summary": v8["summary"]})
        files["MISSING_HEIGHT_EVIDENCE.json"] = _j({"run": run, "missing": v8["missing"]})
        files["OPENING_SCHEDULE.json"] = _j({"run": run, "openings": v8["openings"]})
        files["OPENING_SCHEDULE.csv"] = _csv(_opening_rows(v8), OPENING_SCHEDULE_COLUMNS)
        files["WINDOW_REVEALS.json"] = _j({"run": run, "reveals": v8["reveals"]})
        files["WALL_GEOMETRY.json"] = _j({"run": run, "walls": v8["walls"], "stubs": v8["stubs"],
                                          "conservation": v8["conservation"], "unclosed_labels": v8["lost_labels"]})
    if arch.get("v29") is not None:                            # ARCH_TAKEOFF_V2.9
        files["CURVED_OPENINGS.json"] = _j({"run": run, **{k: v for k, v in arch["v29"].items()
                                                           if k not in ("masonry", "facade")}})
        files["MASONRY.json"] = _j({"run": run, "policy": arch["v29"]["policy"], "floors": arch["v29"]["masonry"]})
        files["FACADE.json"] = _j({"run": run, "policy": arch["v29"]["policy"], "floors": arch["v29"]["facade"]})
    if arch.get("traceability") is not None:                    # ARCH_TAKEOFF_V2.5
        from engine.source import traceability as TR
        files["BOQ_TRACEABILITY.json"] = _j({"run": run, "traceability": arch["traceability"]})
        files["BOQ_TRACEABILITY.csv"] = _csv(arch["traceability"]["rows"], TR.CSV_COLUMNS)
    if arch.get("wp_install") is not None:                      # ARCH_TAKEOFF_V2.6
        from engine.source import waterproofing_system as WS
        wi = arch["wp_install"]
        files["MEMBRANE_PIECE_PLAN.json"] = _j({"run": run, "piece_plans": wi["piece_plans"]})
        files["MEMBRANE_PIECE_PLAN.csv"] = _csv(wi["piece_rows"], WS.PIECE_COLUMNS)
        files["WP_INSTALLATION.json"] = _j({"run": run, "installation": wi["installation"], "summary": wi["summary"]})
        files["WP_INSTALLATION.csv"] = _csv(wi["install_rows"], WS.INSTALL_COLUMNS)
    if arch.get("rules_sheet") is not None:                     # ARCH_TAKEOFF_V2.4
        from engine.source import door_feasibility as DF
        from engine.source import project_rules as PRJ
        files["PROJECT_RULES_SHEET.json"] = _j({"run": run, "sheet": arch["rules_sheet"]})
        files["PROJECT_RULES_SHEET.csv"] = _csv(PRJ.csv_rows(arch["rules_sheet"]), PRJ.CSV_COLUMNS)
        wp = arch["waterproofing"]
        files["WATERPROOFING_SCHEDULE.json"] = _j({"run": run, "waterproofing": {k: v for k, v in wp.items()
                                                                                  if k != "systems"}})
        files["WATERPROOFING_SCHEDULE.csv"] = _csv([_wp_row(r) for r in wp["areas"]], WP_COLUMNS)
        files["MEMBRANE_CUTTING_PLAN.json"] = _j({"run": run, "systems": wp["systems"]})
        if arch.get("v211") is not None:                       # T-079: ARCH_TAKEOFF_V2.11 membrane table
            files["MEMBRANE_TABLE_V2_11.json"] = _j({"run": run, "membrane_table": arch["v211"]["membrane_table"],
                                                     "roofs": arch["v211"]["roofs"],
                                                     "wet_zones_held": arch["v211"]["wet_zones_held"],
                                                     "top_roofs_held": arch["v211"]["top_roofs_held"]})
            from engine.source import arch_v211 as AV
            files["MEMBRANE_PURCHASE_V2_11.csv"] = _csv(AV.purchase_rows(arch["v211"]["membrane_table"]),
                                                        AV.PURCHASE_COLUMNS)
        files["DOOR_FEASIBILITY.json"] = _j({"run": run, "doors": arch["door_feasibility"]})
        files["DOOR_FEASIBILITY.csv"] = _csv(DF.csv_rows(arch["door_feasibility"]), DF.CSV_COLUMNS)
        files["APPROVALS_REQUIRED.json"] = _j({"run": run, "approvals": arch["approvals"]})
        files["ENGINEERING_SUMMARY.json"] = _j({"run": run, "summary": arch["engineering_summary"]})
    return files


RELEASE_COLUMNS = ("category", "line_id", "floor", "room_id", "item_code", "element", "unit", "quantity", "low", "high",
                   "evidence_state", "nature", "reason_class", "reason")


def _release_rows(rep):
    rows = []
    for cat in ("CONFIRMED", "HELD", "EXCLUDED"):
        for x in rep["categories"][cat]["lines"]:
            rows.append({"category": cat, **{k: x.get(k) for k in RELEASE_COLUMNS if k != "category"}})
    for s in rep["categories"]["CONDITIONAL"]["scenario_sets"]:
        for sc, tot in s["by_scenario"].items():
            for k, v in (tot.items() if isinstance(tot, dict) else ()):
                rows.append({"category": "CONDITIONAL", "line_id": s["set_id"], "floor": None, "room_id": s["subject"],
                             "item_code": k, "element": sc, "unit": None,
                             "quantity": v if not isinstance(v, dict) else None, "low": None, "high": None,
                             "evidence_state": None, "nature": s["kind"], "reason_class": None,
                             "reason": "depends on " + ", ".join(s["depends_on"])})
    return rows


WP_COLUMNS = ("room_id", "floor", "scope", "system_id", "A_net_horizontal_m2", "eligible_upturn_lm", "upturn_h_m",
              "upturn_h_state", "upturn_m2", "doorway_continuation_m2", "doorway_transitions_unresolved",
              "doorway_transition_range_m2", "terminations_unresolved_lm", "penetrations_state", "penetrations",
              "corners_internal", "corners_external", "corners_state", "laps_m2", "B_installed_m2", "consumed_m2",
              "cutting_waste_m2", "rolls_if_installed_alone", "withheld_items", "state")


def _wp_row(r):
    tr = r["doorway_transitions"]
    rng = tr["range_m2"]
    return {"room_id": r["room_id"], "floor": r["floor"], "scope": r["scope"], "system_id": r["system_id"],
            "A_net_horizontal_m2": r["A_net_horizontal_m2"], "eligible_upturn_lm": r["upturn"]["eligible_lm"],
            "upturn_h_m": r["upturn"]["height_m"], "upturn_h_state": r["upturn"]["height_state"],
            "upturn_m2": r["upturn"]["area_m2"], "doorway_continuation_m2": r["doorway_continuation_m2"],
            "doorway_transitions_unresolved": tr["unresolved"],
            "doorway_transition_range_m2": f"{rng['low']:g} - {rng['high']:g}" if rng else "",
            "terminations_unresolved_lm": r["terminations"]["unresolved_lm"],
            "penetrations_state": r["penetrations"]["state"], "penetrations": r["penetrations"]["count"],
            "corners_internal": r["corners"]["internal"], "corners_external": r["corners"]["external"],
            "corners_state": r["corners"]["state"], "laps_m2": r["laps_m2"], "B_installed_m2": r["B_installed_m2"],
            "consumed_m2": r["consumed_m2"], "cutting_waste_m2": r["cutting_waste_m2"],
            "rolls_if_installed_alone": r["rolls_if_installed_alone"], "withheld_items": len(r["withheld"]),
            "state": r["state"]}


DOOR_SCENARIO_COLUMNS = ("element_id", "floor", "opening_id", "state", "category", "view", "spaces",
                         "cad_wall_opening_m", "width_state", "frame_width_m", "height_m", "height_state",
                         "as_drawn_area_m2", "as_drawn_area_state", "required_nominal_door_m",
                         "owner_required_wall_opening_m", "enlargement_m", "nominal_door_for_opening_m",
                         "owner_required_area_m2", "owner_required_area_state", "review_status", "flags")


def _door_row(r):
    a, o = r["as_drawn"], r["owner_required"]
    return {"element_id": r["element_id"], "floor": r["floor"], "opening_id": r["opening_id"], "state": r["state"],
            "category": r["category"], "view": r["view"], "spaces": " | ".join(str(x) for x in r["spaces"]),
            "cad_wall_opening_m": a["cad_wall_opening_m"], "width_state": a["width_state"],
            "frame_width_m": a["frame_width_m"], "height_m": a["height"].get("value_m"),
            "height_state": a["height"].get("state"), "as_drawn_area_m2": a["wall_opening_area"]["m2"],
            "as_drawn_area_state": a["wall_opening_area"]["state"],
            "required_nominal_door_m": o["required_nominal_door_m"],
            "owner_required_wall_opening_m": o["owner_required_wall_opening_m"], "enlargement_m": o["enlargement_m"],
            "nominal_door_for_opening_m": o["nominal_door_for_opening_m"],
            "owner_required_area_m2": o["wall_opening_area"]["m2"],
            "owner_required_area_state": o["wall_opening_area"]["state"], "review_status": r["review_status"],
            "flags": "; ".join(r["flags"])}


PUBLISHED = ("BOQ_LINES.json", "BOQ_LINES.csv", "MATERIAL_RESULTS.json", "COVERAGE.json", "COVERAGE.csv",
             "RUN_RULES.json", "ARCH_PLAN.json", "ARCH_ROOMS.json", "ARCH_OPENINGS.json", "ARCH_WALLS.json",
             "UNRESOLVED.json", "ARCH_FLOOR_AREAS.json", "URBAN_ROOM_BOQ.xlsx", "FINISH_COVERAGE.json",
             "DRAWING_DISCOVERY.json", "ADMISSION_BLOCKED.json", "COMPLETENESS_FAILED.json",
             "ARCH_GEOMETRY_DECISIONS.json", "DOOR_SCHEDULE.json", "DOOR_SCHEDULE.csv",
             "SURFACE_LEDGER.json", "SURFACE_LEDGER.csv", "DIMENSION_CROSSCHECK.json", "SPACE_MODEL.json",
             "DOOR_SCENARIOS.json", "DOOR_SCENARIOS.csv", "ELEVATOR_SCHEDULE.json", "OWNER_QUESTIONS.json",
             "BOQ_SCENARIOS.json", "PROJECT_RULES_SHEET.json", "PROJECT_RULES_SHEET.csv", "WATERPROOFING_SCHEDULE.json",
             "WATERPROOFING_SCHEDULE.csv", "MEMBRANE_CUTTING_PLAN.json", "DOOR_FEASIBILITY.json", "DOOR_FEASIBILITY.csv",
             "APPROVALS_REQUIRED.json", "ENGINEERING_SUMMARY.json", "OUTPUT_MANIFEST.json",
             "MEMBRANE_PIECE_PLAN.json", "MEMBRANE_PIECE_PLAN.csv", "WP_INSTALLATION.json", "WP_INSTALLATION.csv",
             "CORRECTIONS_V2_7.json", "REVIEW_SPACES.json", "BOQ_RELEASE_REPORT.json", "BOQ_RELEASE_REPORT.csv",
             "DOOR_STANDARD_RECONCILIATION.json", "DOOR_STANDARD_RECONCILIATION.csv", "HEIGHT_EVIDENCE.json",
             "MISSING_HEIGHT_EVIDENCE.json", "OPENING_SCHEDULE.json", "OPENING_SCHEDULE.csv", "WINDOW_REVEALS.json",
             "WALL_GEOMETRY.json")


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
    decisions = None
    if getattr(a, "decisions", None):
        if a.method not in (V23, V24, V25, V26, V27, V271, V28, V29, V210, V211):
            raise SystemExit("--decisions (project decisions, URBAN_PROJECT_DECISIONS_V1) needs --method "
                             "ARCH_TAKEOFF_V2.3, ARCH_TAKEOFF_V2.4, ARCH_TAKEOFF_V2.5, ARCH_TAKEOFF_V2.6, "
                             "ARCH_TAKEOFF_V2.7 or ARCH_TAKEOFF_V2.7.1")
        decisions = json.loads(Path(a.decisions).read_text(encoding="utf-8"))
        if decisions.get("schema") != "URBAN_PROJECT_DECISIONS_V1":
            raise SystemExit("--decisions: schema must be URBAN_PROJECT_DECISIONS_V1")
    project_rules = None
    if getattr(a, "project_rules", None):
        if a.method not in (V24, V25, V26, V27, V271, V28, V29, V210, V211):
            raise SystemExit("--project-rules (URBAN_PROJECT_RULES_V1) needs --method ARCH_TAKEOFF_V2.4, "
                             "ARCH_TAKEOFF_V2.5, ARCH_TAKEOFF_V2.6, ARCH_TAKEOFF_V2.7 or ARCH_TAKEOFF_V2.7.1")
        project_rules = json.loads(Path(a.project_rules).read_text(encoding="utf-8"))
    independent_checks = None
    if getattr(a, "independent_checks", None):
        if a.method not in (V25, V26, V27, V271, V28, V29, V210, V211):
            raise SystemExit("--independent-checks (URBAN_INDEPENDENT_CHECKS_V1) needs --method ARCH_TAKEOFF_V2.5, "
                             "ARCH_TAKEOFF_V2.6, ARCH_TAKEOFF_V2.7 or ARCH_TAKEOFF_V2.7.1")
        independent_checks = json.loads(Path(a.independent_checks).read_text(encoding="utf-8"))
    roles = _kv(a.layer_roles, "--layer-roles")
    refs = {k: float(v) for k, v in _kv(a.reference_areas, "--reference-areas").items()}
    out = Path(a.out)
    conversions = []
    v2 = a.method in (V2, V21, V22, V23, V24, V25, V26, V27, V271, V28, V29, V210, V211)
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
                                     admission_findings=pre, **({"decisions": decisions} if decisions else {}),
                                     **({"project_rules": project_rules} if project_rules is not None else {}),
                                     **({"independent_checks": independent_checks} if independent_checks is not None
                                        else {}))
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
    if arch.get("rules_sheet") is not None:
        # ARCH_TAKEOFF_V2.4 (UP-RULES-001): outputs computed with another rules sheet are moved aside, never reused
        from engine.source import project_rules as PRJ
        prev = out / "PROJECT_RULES_SHEET.json"
        old_sheet = json.loads(prev.read_text(encoding="utf-8"))["sheet"] if prev.exists() else None
        inv = PRJ.invalidation(old_sheet, arch["rules_sheet"])
        if inv["state"] == "RULES_CHANGED":
            inv["moved"] = _supersede(out)
        arch["rules_sheet"]["invalidation"] = inv
        arch["run"]["v2_4"]["rules_sheet"]["invalidation"] = inv["state"]
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
    if arch.get("rules_sheet") is not None:
        # ARCH_TAKEOFF_V2.4 (UP-RULES-001): every output of the run bound to the rules sheet it was computed with
        written = res["files"] + (["URBAN_ROOM_BOQ.xlsx"] if "xlsx" in res else []) + svgs
        (out / V24_MANIFEST).write_text(_j(_v24_manifest(out, written, arch)), encoding="utf-8")
        svgs.append(V24_MANIFEST)
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
    p.add_argument("--project-rules", help="ARCH_TAKEOFF_V2.4: project rules (URBAN_PROJECT_RULES_V1): Level B "
                   "requirements of the project's drawings, details, schedules and specifications that override the "
                   "Urban standards within their scope (engine.source.project_rules)")
    p.add_argument("--independent-checks", help="ARCH_TAKEOFF_V2.5: independently calculated quantities "
                   "(URBAN_INDEPENDENT_CHECKS_V1: {room_id, item_code, value, tolerance, source}) compared with the "
                   "engine's BOQ lines in BOQ_TRACEABILITY (engine.source.traceability)")
    p.add_argument("--decisions", help="ARCH_TAKEOFF_V2.3: project decisions (URBAN_PROJECT_DECISIONS_V1) binding owner "
                                       "decisions to single spaces (kept with the project's private inputs)")
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
