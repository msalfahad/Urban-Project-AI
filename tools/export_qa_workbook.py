"""Assemble the QA bundle from the engines, then hand it to the export layer.

This is where the arrow turns around and stops. Everything upstream of this
file computes; everything downstream of it only formats. The split is the
control: `engine.qa_workbook` is given data and has no engine imports at all,
so no reported figure can re-enter a calculation even by accident.

    python3 -m tools.export_qa_workbook [--out PATH] [--space-map PATH]

The workbook is gitignored (*.xlsx) and deliberately so: it is a snapshot of a
client's drawing, and the repository holds the code that makes it, not the
output.
"""

from __future__ import annotations

import argparse
import json
from decimal import Decimal
from pathlib import Path

from engine.qa_workbook import build_workbook
from engine.qa_writer import write
from engine.quantity_trace import QuantityTrace, TraceLedger, quantity_id
from engine.revision_entities import compare
from engine.templates import TemplateLibrary
from engine.findings import from_graph_diagnostic
from engine.space_model import (AI_INFERRED, HUMAN_VERIFIED,
                                IDENTITY_WRONG_REGION, NOT_RECOVERED,
                                PHYSICAL_TOPOLOGY_VALIDATED,
                                RASTER_REGION_AVAILABLE,
                                REGION_IDENTITY_VALIDATED, TOPOLOGY_MERGED,
                                TOPOLOGY_SPLIT, WALL_GEOMETRY_AVAILABLE,
                                FunctionalZone, PhysicalSpace,
                                SemanticObservation, SpaceModel)
from engine.takeoff_status import assess as assess_status
from engine.quantity_trace import (CANDIDATE, OBSERVATION, RELEASABLE_QUANTITY)
from engine.release_matrix import (CEILING_GEOMETRY, CLOSED_BOUNDARY,
                                   EXTERNAL_SPLIT, FLOOR_AREA, HEIGHT,
                                   OPENING_RULE, OPENINGS,
                                   PHYSICAL_TOPOLOGY,
                                   PHYSICAL_WALL_SPLIT, REGION_IDENTITY, SCOPE,
                                   TRADE_RULE, USES, WALL_THICKNESS,
                                   assess_space)

GOLDEN = Path("data/golden/23010")
DEFAULT_PDF = GOLDEN / "inputs/AR-00_MAR2023.pdf"
DEFAULT_SPACE_MAP = GOLDEN / "inputs/space_map_23010_2f.json"
# Topology facts live OUTSIDE the frozen space map. The space map is an audited
# input pinned by sha256 and Run 1 was scored against that hash — editing it
# retroactively would break the acceptance run's reproducibility, and the
# golden fixture test caught exactly that attempt. The overlay makes prose the
# space map already carries machine-readable; it adds no new judgement.
DEFAULT_TOPOLOGY_OVERLAY = GOLDEN / "topology_overlay.json"
DEFAULT_OUT = "runs/qa/23010_QA_workbook.xlsx"

# The uses the QA sheets name explicitly, with the engine's own names — not
# friendlier ones. An invented use name is silently dropped by the release
# matrix, which is how the first export came out with no statuses at all.
FLOOR_USES = ("WATERPROOFING_HORIZONTAL", "GROSS_CERAMIC_WALL",
              "NET_CERAMIC_WALL")
WALL_USES = ("GROSS_PERIMETER", "GROSS_WALL_AREA", "BLOCKWORK",
             "EXTERNAL_FINISH")


def _established(space, rec, area, use: str = "") -> dict[str, bool]:
    """What is actually established for one space — nothing assumed true.

    REGION_IDENTITY and PHYSICAL_TOPOLOGY are read from the space map's own
    structured fields. They are separate questions: WSH-01's region is the
    shaft beside the washroom (identity fails), while BED-04's region is a real
    bedroom with an unseparated bathroom inside it (identity holds, topology
    fails). The previous export released a READY quantity for both.
    """
    traced = rec is not None and rec.get("status") == "VALIDATED"
    return {
        REGION_IDENTITY: (rec is not None
                          and space.get("region_identity") == "VALIDATED"),
        PHYSICAL_TOPOLOGY: space.get("physical_topology") == "VALIDATED",
        CLOSED_BOUNDARY: traced,
        SCOPE: space.get("scope") == "IN_SCOPE",
        FLOOR_AREA: area is not None,
        OPENINGS: False,               # no opening has been validated at all
        OPENING_RULE: False,           # no trade's deduction rule is signed
        PHYSICAL_WALL_SPLIT: False,    # masonry vs doorway closure unknown
        EXTERNAL_SPLIT: (rec is not None
                         and rec.get("classification_status") == "RESOLVED"),
        WALL_THICKNESS: False,
        HEIGHT: False,                 # six heights still missing from sections
        CEILING_GEOMETRY: False,
        TRADE_RULE: _trade_rule_covers(space, use),
    }


# Which trade each use belongs to. A use whose trade has no signed rule set
# cannot have TRADE_RULE established, however many OTHER trades are signed.
USE_TRADE = {
    "GROSS_CERAMIC_WALL": "ceramic", "NET_CERAMIC_WALL": "ceramic",
    "GROSS_PLASTER": "plaster", "NET_PLASTER": "plaster",
    "PAINT": "paint", "SKIRTING": "skirting", "CEILING": "ceiling",
    "EXTERNAL_FINISH": "external_finish",
    "WATERPROOFING_HORIZONTAL": "waterproofing",
    "WATERPROOFING_VERTICAL": "waterproofing",
}


def _trade_rule_covers(space, use: str) -> bool:
    """Does THIS TRADE's signed E27 project rule cover this room type?

    Two mirror-image errors are both guarded here.

    The first export hard-coded False for every space, which UNDERSTATED what
    exists: 23010 has two approved owner rule sets covering fifteen room types
    each, and a signed rule the workbook ignores is a real rule thrown away.

    The fix then OVER-released: asking "does any rule cover this room type"
    made waterproofing releasable on the strength of the ceramic rule. A
    ceramic rule saying a bedroom has a ceramic floor says nothing whatever
    about waterproofing, and thirteen spaces briefly read READY because of it.

    The question is per trade AND per room type, and a trade with no signed
    rule set is simply not established. NULL RULE SET MUST NEVER MEAN DEFAULT
    RULE.
    """
    trade = USE_TRADE.get(use)
    if trade is None:
        return False
    rt = (space.get("room_type") or "").strip().upper()
    if not rt:
        return False
    for rs in _rule_sets().values():
        if rs.trade.strip().lower() != trade:
            continue
        try:
            rs.rule_for(rt)
            return True
        except Exception:
            return False
    return False


_RULE_CACHE: dict = {}


def _rule_sets() -> dict:
    """The approved E27 project rules, loaded once.

    AUTHORITY ORDER, and the template layer did not change it:

        1  APPROVED PROJECT TRADE RULE   (E27, data/trade_rules/*.json)
        2  approved room/trade template  (E45, reusable structure)
        3  nothing

    A template is reusable structure a project rule may reference. It never
    replaces a project-specific approved rule, and an empty template library
    does not erase one. NULL TEMPLATE must never mean NULL PROJECT RULE.
    """
    if _RULE_CACHE:
        return _RULE_CACHE
    from engine.trade_rules import TradeRuleSet
    for path in sorted(Path("data/trade_rules").glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            _RULE_CACHE[path.stem] = TradeRuleSet.from_dict(data)
        except Exception:
            continue
    return _RULE_CACHE


def _release_row(space_id: str, established: dict, uses, *,
                 scope: str = "IN_SCOPE") -> dict:
    """One space's status for each use, with the blocker belonging to that use.

    TWO BUGS THE WORKBOOK EXPOSED, both fixed here:

      1  A single `primary_blocker` was computed across all uses and stamped on
         every row, so rows read READY beside a blocker. The blocker now
         belongs to the use it blocks.
      2  OUT_OF_SCOPE spaces were counted as BLOCKED. They are N/A: Urban
         Projects is not measuring them, so there is no work queued and nothing
         to unblock. AMBIGUOUS stays BLOCKED_SCOPE — that one IS work, and the
         work is an owner decision.
    """
    out: dict[str, str] = {}
    blockers: dict[str, str] = {}
    for use in uses:
        if use not in USES:
            raise KeyError(
                f"{use!r} is not a release-matrix use. Known: {sorted(USES)}. "
                "Skipping it silently is how an export came out with no "
                "release statuses at all.")
        st = assess_space(
            space_id, use, established(use) if callable(established)
            else established,
            applicable=(scope != "OUT_OF_SCOPE"),
            not_applicable_reason=(
                "" if scope != "OUT_OF_SCOPE"
                else "OUT_OF_SCOPE: excluded from this contract by owner "
                     "instruction, so nothing is measured or released"))
        out[use] = st.status
        blockers[use] = "" if st.ready else st.primary_blocker
    out["blockers"] = blockers
    # Kept for the sheets that show one blocker per SPACE. It is the blocker of
    # the space's best use, and it is empty when that use is ready.
    first = next((u for u in uses if out.get(u) == "READY"), None)
    out["primary_blocker"] = "" if first else next(
        (b for b in blockers.values() if b), "")
    return out


# THE SINGLE SOURCE OF TRUTH for a workbook. One file, written by one
# pipeline run, carrying the manifest the exporter must check. Reading several
# per-stage files off disk is what let a V2 extraction sit beside V1
# exceptions.
CURRENT_RUN = Path("runs/current/23010.json")
E31A_REPORT = Path("runs/graph/AR-00_e31a.json")
WALL_V2_REPORT = Path("runs/graph/AR-00_wall_v2.json")


_RUN_CACHE: dict = {}


def _run() -> dict:
    """The current pipeline run. Read once, and it carries its own manifest."""
    if _RUN_CACHE:
        return _RUN_CACHE
    if CURRENT_RUN.exists():
        try:
            _RUN_CACHE.update(json.loads(CURRENT_RUN.read_text()))
        except Exception:
            pass
    return _RUN_CACHE


def _wall_v2() -> dict:
    """Wall extraction, from the current run only."""
    return _run()


def _e31a() -> dict:
    """The diagnostic face run, if one exists. Read-only and optional."""
    if not E31A_REPORT.exists():
        return {}
    try:
        return json.loads(E31A_REPORT.read_text())
    except Exception:
        return {}


def _faces() -> list:
    """Faces from the CURRENT run. An older E31A file is not consulted."""
    return _run().get("largest_faces", [])


def _face_correspondence() -> list:
    return _run().get("correspondence", [])


def _space_model(spaces, wall_rows, areas) -> SpaceModel:
    """The three layers, built from the space map's own structured fields."""
    model = SpaceModel()
    for i, sp in enumerate(spaces, 1):
        sid = sp["space_id"]
        rec = wall_rows.get(sid)
        area = sp.get("floor_area_m2")

        layers = set()
        if area is not None:
            layers.add(RASTER_REGION_AVAILABLE)
        if rec is not None and rec.get("status") == "VALIDATED":
            layers.add(WALL_GEOMETRY_AVAILABLE)
        if sp.get("region_identity") == "VALIDATED" and rec is not None:
            layers.add(REGION_IDENTITY_VALIDATED)
        if sp.get("physical_topology") == "VALIDATED":
            layers.add(PHYSICAL_TOPOLOGY_VALIDATED)

        reason = ""
        if sp.get("region_identity") != "VALIDATED":
            reason = IDENTITY_WRONG_REGION
        elif sp.get("physical_topology") == "MERGED":
            reason = TOPOLOGY_MERGED
        elif sp.get("physical_topology") == "SPLIT":
            reason = TOPOLOGY_SPLIT
        elif sp.get("physical_topology") != "VALIDATED":
            reason = "UNRESOLVED"
        elif rec is None:
            reason = NOT_RECOVERED

        model.spaces.append(PhysicalSpace(
            space_id=sid, region_id=sp.get("region"), scope=sp.get("scope", ""),
            layers=frozenset(layers), unresolved_reason=reason,
            room_type=sp.get("room_type", ""), area_m2=area))

        # The LABEL is a separate record from the polygon. That separation is
        # the whole point: WSH-01's label is real and its polygon is the shaft.
        model.observations.append(SemanticObservation(
            observation_id=f"SO-{i:03d}", room_type=sp.get("room_type", ""),
            name_en=sp.get("name_en", ""), name_ar=sp.get("name_ar", ""),
            source=sp.get("semantic_source") or AI_INFERRED,
            seen_at_region=sp.get("region")))

        for z in sp.get("functional_zones", ()):
            model.zones.append(FunctionalZone(
                zone_id=z["zone_id"], physical_space_id=sid,
                function=z["function"], basis=z.get("basis", "")))
    return model


def bundle(space_map_path: Path = DEFAULT_SPACE_MAP,
           pdf: Path = DEFAULT_PDF, *, measure: bool = True,
           diagnostic_path: Path = Path(
               "runs/graph/AR-00_graph_diagnostic.json")) -> dict:
    """Everything the workbook needs, and not one value it does not."""
    sm = json.loads(Path(space_map_path).read_text(encoding="utf-8"))
    spaces = [dict(s) for s in sm["spaces"]]

    # Merge the overlay. An absent overlay does NOT mean "everything is
    # validated": a space with no entry gets UNRESOLVED, so a missing file
    # fails closed rather than releasing every quantity on the sheet.
    overlay = {}
    if Path(DEFAULT_TOPOLOGY_OVERLAY).exists():
        overlay = json.loads(
            Path(DEFAULT_TOPOLOGY_OVERLAY).read_text(encoding="utf-8")
        ).get("spaces", {})
    for sp in spaces:
        o = overlay.get(sp["space_id"])
        if o is None:
            sp["region_identity"] = "UNRESOLVED"
            sp["region_identity_reason"] = (
                "no topology overlay entry for this space; absence is not "
                "validation")
            sp["physical_topology"] = "UNRESOLVED"
            sp["physical_topology_reason"] = sp["region_identity_reason"]
        else:
            sp.update(o)

    areas: dict[int, Decimal] = {}
    wall_rows: dict[str, dict] = {}
    provenance = {
        "space_map": str(space_map_path),
        "drawing": f"{sm['drawing_id']} rev {sm['drawing_revision']}",
        "geometry_source": sm.get("geometry_source", ""),
        "label_source": sm.get("label_source", ""),
        "measured": "yes" if measure else "no — register and counts only",
    }

    if measure:
        from engine.geometry import VectorPdfSource, calibrate
        from engine.wall_model import run_wall_model

        src = VectorPdfSource(str(pdf), calibrate(887.82, 40000, 554.94, 25000))
        areas = {r.id: r.area_m2 for r in src.regions(0, min_m2=0.3)}
        seg = src.segmentation(0, drawing_id=sm["drawing_id"],
                               revision=sm["drawing_revision"])
        res = run_wall_model(seg, {s["space_id"]: s["region"] for s in spaces})
        wall_rows = {r.space_id: r.row() for r in res.records}
        provenance["segmentation"] = json.dumps(seg.provenance(), sort_keys=True)

    for sp in spaces:
        sp["semantic_source"] = (HUMAN_VERIFIED
                                 if "HUMAN_VERIFIED" in sm.get("label_source", "")
                                 else None)
        a = areas.get(sp.get("region"))
        sp["floor_area_m2"] = None if a is None else float(round(a, 3))
        sp["area_source"] = "VECTOR_PDF_RASTER_REGION" if a is not None else None
        sp["measurement_basis"] = ("CLEAR_INTERNAL_FINISH_FACE" if a is not None
                                   else None)
        rec = wall_rows.get(sp["space_id"])
        sp["geometry_status"] = rec.get("status") if rec else None

    model = _space_model(spaces, wall_rows, areas)
    by_space = {s.space_id: s for s in model.spaces}
    for sp in spaces:
        ps = by_space[sp["space_id"]]
        sp["physical_space_validated"] = ps.validated
        sp["unresolved_reason"] = ps.unresolved_reason

    # Establishment is per (space, USE), because TRADE_RULE is a question about
    # a trade and asking it without naming one is how waterproofing came to be
    # released on the strength of the ceramic rule.
    def established_for(sid):
        sp = next(x for x in spaces if x["space_id"] == sid)
        return lambda use: _established(
            sp, wall_rows.get(sid), sp["floor_area_m2"], use)

    established = {s["space_id"]: established_for(s["space_id"])
                   for s in spaces}

    releases = {s["space_id"]: _release_row(
        s["space_id"], established[s["space_id"]], FLOOR_USES + WALL_USES,
        scope=s.get("scope", "")) for s in spaces}

    # --- quantity traces, with a ROLE ------------------------------------
    ledger = TraceLedger(project_id=sm["project_id"],
                         revision_id=sm["drawing_revision"])
    floor = sm.get("floor_id", "")
    for sid, rec in sorted(wall_rows.items()):
        sp = next(x for x in spaces if x["space_id"] == sid)
        ps = by_space[sid]
        rel = releases.get(sid, {})
        status = rel.get("GROSS_PERIMETER", "")
        blocker = rel.get("blockers", {}).get("GROSS_PERIMETER", "")
        v = rec.get("gross_room_perimeter_m")
        v = None if v is None else float(v)

        # THE DISTINCTION THE WORKBOOK WAS MISSING. WSH-01's 4.19 m is a real
        # measurement of raster region 361 and is NOT a washroom perimeter.
        # Deleting it loses useful geometry; releasing it puts a shaft into a
        # bathroom's takeoff. It is an OBSERVATION and it keeps its value.
        if ps.validated and status == "READY":
            role, obs_of = RELEASABLE_QUANTITY, ""
        elif ps.validated:
            role, obs_of = CANDIDATE, ""
        else:
            role = OBSERVATION
            obs_of = (f"the traced boundary of raster region {ps.region_id}, "
                      f"which is not a validated {sp.get('room_type', 'space')} "
                      f"({ps.unresolved_reason})")
        ledger.add(QuantityTrace(
            quantity_id=quantity_id(sm["project_id"], floor, sid, "PERIM",
                                    "GROSS"),
            space_id=sid, use="GROSS_PERIMETER", unit="m", value=v,
            quantity_role=role, observation_of=obs_of,
            drawing_id=sm["drawing_id"], revision_id=sm["drawing_revision"],
            geometry_source="VECTOR_PDF_RASTER_REGION",
            boundary_edge_ids=(f"space:{sid}",),
            calculation_reference="engine.wall_model.run_wall_model",
            validation_status=("VALIDATED" if ps.validated else "DRAFT"),
            release_status=status or "NOT_ASSESSED",
            primary_blocker=blocker))

    # --- findings, generated from the CURRENT diagnostic ------------------
    diagnostic, findings = {}, []
    run_id = (f"{sm['project_id']}-{sm['drawing_id']}-"
              f"{sm['drawing_revision']}".replace(" ", "_"))
    cur = _run()
    if cur:
        # Findings are generated from the CURRENT run's numbers. Reading an
        # older diagnostic file is exactly how 115 components and 228 termini
        # survived into a V2 workbook.
        diagnostic = {
            "connectivity": {
                "components": cur["connectivity"]["components"],
                "termini": cur["connectivity"]["termini"],
                "terminus_histogram": cur["connectivity"][
                    "terminus_histogram"],
                "cause_histogram": {},
                "major_components": cur["connectivity"][
                    "components_with_cycles"],
                "share_of_length_in_major_components_pct": None,
            },
            "noded_graph": cur["graph"],
            "source": {"path_fragmentation": {
                "short_segments": None,
                "short_in_a_path_that_also_has_a_long_run": None}},
            "end_caps": {"found": None},
            "stitching": {},
            "e31a_gate": {"ready_for_e31a": False,
                          "verdict": "NOT READY",
                          "failed": ["POSITIVE_CONTROLS"],
                          "not_measured": []},
        }
        run_id = cur["manifest"]["stages"]["wall_graph"]["run_id"]
        findings = from_graph_diagnostic(
            diagnostic, run_id=run_id, reference=str(CURRENT_RUN),
            space_count=len(spaces), use_count=len(USES))
    elif (dp := Path(diagnostic_path)).exists():
        diagnostic = json.loads(dp.read_text())
        findings = from_graph_diagnostic(
            diagnostic, run_id=run_id, reference=str(dp),
            space_count=len(spaces), use_count=len(USES))

    # §16 — the space map's known_gaps carry PRIOR causal prose. One of them
    # still said the wash room's south edge is a dashed threshold, and this
    # project has since measured ZERO dashed strokes on the sheet and found the
    # nearby marks to be shaft hatch. It is kept for history and labelled, and
    # the CURRENT supported fact is stated separately.
    superseded = {
        "WSH-01": ("no dashed stroke exists anywhere on this sheet (every "
                   "stroke path is solid) and the repeated short marks beside "
                   "WSH-01 are the shaft symbol's hatch fill, 8 mm marks with "
                   "8 mm gaps. Geometric dashed-run recovery found no "
                   "threshold here."),
    }
    known_gaps = [{
        "subject": g.get("item", "")[:60], "affected_spaces": 1,
        "affected_uses": 2, "coverage_unlocked": "ceramic wall for this room",
        "owner_action": "review the flagged geometry",
        "item": g.get("item"), "cause": g.get("cause"), "effect": g.get("effect"),
        "status": g.get("status"),
        "resolution": g.get("e25_update") or "Named in the space map known_gaps.",
        "provenance_class": ("LEGACY_HYPOTHESIS"
                             if "dashed" in (g.get("cause") or "").lower()
                             else "GOLDEN_KNOWN_DEFECT"),
        "superseded_because": next(
            (v for k, v in superseded.items() if k in (g.get("item") or "")),
            "" if "dashed" not in (g.get("cause") or "").lower()
            else superseded["WSH-01"]),
    } for g in sm.get("known_gaps", ())]

    # The CURRENT supported facts about the two hard spaces, stated without
    # any cause that this round's measurements did not support.
    current_hard_cases = [{
        "subject": "WSH-01", "severity": "UNDERSTATES_A_QUANTITY",
        "area": "GEOMETRY", "provenance_class": "CURRENT_DIAGNOSTIC",
        "issue": "The physical washroom geometry is unresolved.",
        "cause": ("No validated boundary currently separates the wash floor "
                  "from OPEN-01. The region carrying the label is the hatched "
                  "shaft beside it. Dashed-run recovery ran on this sheet and "
                  "found no supporting threshold — that hypothesis is retired, "
                  "not pending."),
        "effect": ("No washroom polygon exists, so no washroom quantity "
                   "exists. The 4.19 m perimeter is an OBSERVATION of the "
                   "shaft region."),
        "engineering_next_action": (
            "General topology recovery only. The printed 1500 x 2400 is used "
            "to validate a candidate, never to generate one."),
        "affected_spaces": 1, "affected_uses": 13,
        "status": "WASHROOM_GEOMETRY_UNRESOLVED",
    }, {
        "subject": "BED-04", "severity": "UNDERSTATES_A_QUANTITY",
        "area": "GEOMETRY", "provenance_class": "CURRENT_DIAGNOSTIC",
        "issue": "The bedroom's bathroom has not separated from the bedroom.",
        "cause": ("Local topology analysis this run: 0 of 4 sides of the "
                  "merged region have a wall run covering them. North covers "
                  "1798 mm of 6218; south has no wall pair within 2 m; east "
                  "and west end at unresolved termini."),
        "effect": "The merged perimeter is an OBSERVATION, not a bedroom.",
        "engineering_next_action": (
            "Recover the missing wall pairs. The printed 1600 x 3000 is used "
            "only to validate a candidate face after generation."),
        "affected_spaces": 1, "affected_uses": 13, "status": "BLOCKED",
    }]

    scope_exceptions = [{
        "subject": s["space_id"], "issue": "Scope not decided",
        "affected_spaces": 1, "affected_uses": len(USES),
        "coverage_unlocked": "every use for this space",
        "owner_action": "decide whether this space is in the contract",
        "cause": "The owner's markup does not settle this space.",
        "effect": "Every quantity for it is withheld: SCOPE gates all uses.",
        "status": "AWAITING OWNER DECISION",
        "resolution": "A written scope decision for this space.",
    } for s in spaces if s.get("scope") == "AMBIGUOUS"]

    topology_exceptions = [{
        "subject": s["space_id"],
        "issue": f"Physical space not validated ({s['unresolved_reason']})",
        "affected_spaces": 1, "affected_uses": len(USES),
        "cause": (s.get("region_identity_reason")
                  or s.get("physical_topology_reason") or ""),
        "effect": ("Every quantity for this space is an OBSERVATION of a "
                   "raster region, not a quantity attributed to the room."),
        "status": "BLOCKED", "coverage_unlocked": "every use for this space",
        "owner_action": "",
        "resolution": "Recover the physical space geometry.",
    } for s in spaces if not s["physical_space_validated"]]

    # --- coverage, with OUT_OF_SCOPE as N/A -------------------------------
    coverage = []
    for use in sorted(USES):
        ready = blocked = na = 0
        blockers: dict[str, int] = {}
        for sp in spaces:
            st = assess_space(
                sp["space_id"], use, established[sp["space_id"]](use),
                applicable=(sp.get("scope") != "OUT_OF_SCOPE"),
                not_applicable_reason=(
                    "" if sp.get("scope") != "OUT_OF_SCOPE"
                    else "OUT_OF_SCOPE: excluded from this contract"))
            if st.ready:
                ready += 1
            elif not st.applicable:
                na += 1
            else:
                blocked += 1
                blockers[st.primary_blocker] = blockers.get(
                    st.primary_blocker, 0) + 1
        coverage.append({
            "use": use,
            "basis": ("GROSS" if use.startswith("GROSS_")
                      else "NET" if use.startswith("NET_") else "DIRECT"),
            "applicable": ready + blocked, "ready": ready, "blocked": blocked,
            "not_applicable": na,
            "commonest_blocker": (max(blockers, key=blockers.get)
                                  if blockers else None),
            "quantity_released": ready,
        })

    # --- the two top-level statuses ---------------------------------------
    status = assess_status(
        uses_total=len(USES),
        uses_with_ready_spaces=sum(1 for c in coverage if c["ready"]),
        net_uses_ready=sum(1 for c in coverage
                           if c["ready"] and c["use"].startswith("NET_")),
        validated_physical_spaces=sum(
            1 for s in model.spaces if s.validated and s.scope == "IN_SCOPE"),
        total_in_scope_spaces=sum(1 for s in spaces
                                  if s.get("scope") == "IN_SCOPE"),
        openings_validated=0,
        signed_trade_rules=len(_rule_sets()),
        unresolved_topology_spaces=sum(
            1 for s in model.spaces if not s.validated),
        graph_gate_passed=bool(
            diagnostic.get("e31a_gate", {}).get("ready_for_e31a")))

    # §18 — these are E27 APPROVED PROJECT TRADE RULES. They are not room
    # templates and must not be filed as such.
    project_rules = [{
        "template_id": name, "version": rs.version,
        "room_type": rs.trade.upper(),
        "approval_status": "APPROVED", "approved_by": "Urban Projects (owner)",
        "approved_on": rs.effective_from, "source": rs.source,
    } for name, rs in sorted(_rule_sets().items())]

    return {
        "project_id": sm["project_id"],
        "revision_id": sm["drawing_revision"],
        "run_id": run_id,
        "diagnostic_run_id": run_id,
        "title": (f"QA workbook — project {sm['project_id']} "
                  f"{sm['drawing_id']} {sm.get('floor_id', '')}".strip()),
        "spaces": spaces,
        "space_model": model,
        "room_counts": model.room_counts(),
        "geometry_layers": model.geometry_summary(),
        "zones": [z.record() for z in model.zones],
        "quantities": {s["space_id"]: {
            "floor_area_m2": s["floor_area_m2"],
            "floor_area_basis": s["measurement_basis"],
            "ceramic_wall_length_m": None, "ceramic_wall_height_m": None,
            "height_source": None, "height_truth_domain": None,
            "ceramic_wall_area_m2": None,
        } for s in spaces},
        "releases": releases,
        "wall_records": [{
            "space_id": sid, "room_type": next(
                (x.get("room_type") for x in spaces if x["space_id"] == sid),
                None),
            "scope": next((x.get("scope") for x in spaces
                           if x["space_id"] == sid), None),
            "gross_room_perimeter_m": float(rec["gross_room_perimeter_m"]),
            "gross_wall_perimeter_m": float(rec["gross_wall_perimeter_m"]),
            "physical_wall_m": float(rec["physical_wall_m"]),
            "open_length_m": float(rec["open_length_m"]),
            "opening_count": rec.get("openings"),
            "segment_count": rec.get("segments"),
            "internal_segments": rec.get("internal_segments"),
            "external_segments": rec.get("external_segments"),
            "unclassified_segments": rec.get("unclassified_segments"),
        } for sid, rec in sorted(wall_rows.items())],
        "quantity_traces": [t.record() | {"floor": floor}
                            for t in ledger.traces],
        "findings": [f.record() for f in findings],
        "known_gaps": known_gaps + current_hard_cases,
        "scope_exceptions": scope_exceptions,
        "space_exceptions": topology_exceptions,
        "coverage": coverage,
        "top_level_status": status.record(),
        "project_trade_rules": project_rules,
        "room_templates": [],      # none approved: a template is not a rule
        "assemblies": [],
        "faces": _faces(),
        "face_correspondence": _face_correspondence(),
        "manifest": _run().get("manifest"),
        "wall_bands": _run().get("band_sample", []),
        "wall_rejections": _run().get("rejection_sample", []),
        "wall_sides": [
            {"space_id": sid, "side": side,
             "status": ("PHYSICAL_WALL_PRESENT" if v["coverage_pct"] >= 95
                        else "GAP"),
             "likely_cause": (f"{v['coverage_pct']}% covered"
                              + (f", gaps {v['gaps_mm']} mm" if v["gaps_mm"]
                                 else ""))}
            for sid, sides in _run().get("gap_map", {}).items()
            for side, v in sides.items()],
        "revision_delta": compare(
            None, {"revision_id": sm["drawing_revision"]}),
        "provenance": provenance,
        "manual_expected_counts": None,
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default=DEFAULT_OUT)
    ap.add_argument("--space-map", default=str(DEFAULT_SPACE_MAP))
    ap.add_argument("--pdf", default=str(DEFAULT_PDF))
    ap.add_argument("--no-measure", action="store_true",
                    help="register and counts only; skips the slow geometry run")
    a = ap.parse_args()

    wb = build_workbook(bundle(Path(a.space_map), Path(a.pdf),
                               measure=not a.no_measure))
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    write(wb, a.out)
    print(f"wrote {a.out}")
    for s in wb.sheets:
        print(f"  {s.name:26} {len(s.rows):4d} rows")


if __name__ == "__main__":
    main()
