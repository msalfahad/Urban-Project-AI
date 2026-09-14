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
from engine.release_matrix import (CEILING_GEOMETRY, CLOSED_BOUNDARY,
                                   EXTERNAL_SPLIT, FLOOR_AREA, HEIGHT,
                                   OPENING_RULE, OPENINGS,
                                   PHYSICAL_WALL_SPLIT, REGION_IDENTITY, SCOPE,
                                   TRADE_RULE, USES, WALL_THICKNESS,
                                   assess_space)

GOLDEN = Path("data/golden/23010")
DEFAULT_PDF = GOLDEN / "inputs/AR-00_MAR2023.pdf"
DEFAULT_SPACE_MAP = GOLDEN / "inputs/space_map_23010_2f.json"
DEFAULT_OUT = "runs/qa/23010_QA_workbook.xlsx"

# The uses the QA sheets name explicitly, with the engine's own names — not
# friendlier ones. An invented use name is silently dropped by the release
# matrix, which is how the first export came out with no statuses at all.
FLOOR_USES = ("WATERPROOFING_HORIZONTAL", "GROSS_CERAMIC_WALL",
              "NET_CERAMIC_WALL")
WALL_USES = ("GROSS_PERIMETER", "GROSS_WALL_AREA", "BLOCKWORK",
             "EXTERNAL_FINISH")


def _established(space, rec, area) -> dict[str, bool]:
    """What is actually established for one space — nothing assumed true.

    Every value here is False unless something upstream proved it. A dependency
    absent from the dict is also not established: the release matrix blocks on
    a missing key rather than passing one, and `trade_rule` stays False because
    nobody has looked a rule up per space.
    """
    traced = rec is not None and rec.get("status") == "VALIDATED"
    return {
        # The space map maps this space to a region the engine actually found.
        REGION_IDENTITY: rec is not None,
        # The traced boundary closed. An UNRESOLVED trace has not.
        CLOSED_BOUNDARY: traced,
        SCOPE: space.get("scope") == "IN_SCOPE",
        FLOOR_AREA: area is not None,
        # None of the following is established anywhere on this project yet,
        # and each one is written out rather than omitted so the blocker names
        # itself instead of reading as an absent key.
        OPENINGS: False,               # no opening has been validated at all
        OPENING_RULE: False,           # no trade's deduction rule is signed
        PHYSICAL_WALL_SPLIT: False,    # masonry vs doorway closure unknown
        EXTERNAL_SPLIT: (rec is not None
                         and rec.get("classification_status") == "RESOLVED"),
        WALL_THICKNESS: False,         # proven per space, not assumed
        HEIGHT: False,                 # six heights still missing from sections
        CEILING_GEOMETRY: False,       # never independently established
        TRADE_RULE: False,             # not looked up per space in this export
    }


def _release_row(space_id: str, established: dict, uses) -> dict:
    out: dict[str, str] = {}
    worst = ""
    for use in uses:
        if use not in USES:
            raise KeyError(
                f"{use!r} is not a release-matrix use. Known: {sorted(USES)}. "
                "Skipping it silently is how an export came out with no "
                "release statuses at all.")
        st = assess_space(space_id, use, established)
        out[use] = st.status
        if not st.ready and st.applicable and not worst:
            worst = st.primary_blocker
    out["primary_blocker"] = worst or ""
    return out


def bundle(space_map_path: Path = DEFAULT_SPACE_MAP,
           pdf: Path = DEFAULT_PDF, *, measure: bool = True) -> dict:
    """Everything the workbook needs, and not one value it does not."""
    sm = json.loads(Path(space_map_path).read_text(encoding="utf-8"))
    spaces = [dict(s) for s in sm["spaces"]]

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

    for s in spaces:
        # Who named this room. On 23010 a person read every name off the
        # rendered sheet, because the vector PDF carries no text layer. The
        # workbook must say so rather than let a reader assume extraction.
        s["semantic_source"] = ("HUMAN_VERIFIED"
                                if "HUMAN_VERIFIED" in sm.get("label_source", "")
                                else None)
        a = areas.get(s.get("region"))
        s["floor_area_m2"] = None if a is None else float(round(a, 3))
        s["area_source"] = "VECTOR_PDF_RASTER_REGION" if a is not None else None
        s["measurement_basis"] = ("CLEAR_INTERNAL_FINISH_FACE" if a is not None
                                  else None)
        rec = wall_rows.get(s["space_id"])
        s["geometry_status"] = rec.get("status") if rec else None
        s["apartment_id"] = s.get("apartment_id")

    established = {s["space_id"]: _established(
        s, wall_rows.get(s["space_id"]), s["floor_area_m2"]) for s in spaces}

    releases: dict[str, dict] = {}
    for s in spaces:
        sid = s["space_id"]
        row = _release_row(sid, established[sid], FLOOR_USES + WALL_USES)
        releases[sid] = row

    quantities = {
        s["space_id"]: {
            "floor_area_m2": s["floor_area_m2"],
            "floor_area_basis": s["measurement_basis"],
            # Gross traced wall length. NOT a ceramic quantity: it is here
            # because it is what was measured, and its release status beside it
            # says it may not be used as one.
            "ceramic_wall_length_m": None,
            "ceramic_wall_height_m": None,       # six heights still missing
            "height_source": None,
            "height_truth_domain": None,
            "ceramic_wall_area_m2": None,        # never derived here
        } for s in spaces
    }

    wall_records = []
    by_id = {s["space_id"]: s for s in spaces}
    for sid, rec in sorted(wall_rows.items()):
        s = by_id.get(sid, {})

        def num(key):
            v = rec.get(key)
            return None if v is None else float(v)

        wall_records.append({
            "space_id": sid, "room_type": s.get("room_type"),
            "scope": s.get("scope"),
            "gross_room_perimeter_m": num("gross_room_perimeter_m"),
            "gross_wall_perimeter_m": num("gross_wall_perimeter_m"),
            "physical_wall_m": num("physical_wall_m"),
            "open_length_m": num("open_length_m"),
            "opening_count": rec.get("openings"),
            "segment_count": rec.get("segments"),
            "internal_segments": rec.get("internal_segments"),
            "external_segments": rec.get("external_segments"),
            "unclassified_segments": rec.get("unclassified_segments"),
        })

    known_gaps = [{
        "subject": g.get("item", "")[:60], "affected_spaces": 1,
        "affected_uses": 2, "coverage_unlocked": "ceramic wall for this room",
        "owner_action": "review the flagged geometry",
        "item": g.get("item"), "cause": g.get("cause"), "effect": g.get("effect"),
        "status": g.get("status"),
        "resolution": g.get("e25_update") or "Named in the space map known_gaps.",
    } for g in sm.get("known_gaps", ())]

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

    space_exceptions = [{
        "subject": sid, "issue": f"No quantity released ({row['primary_blocker']})",
        "affected_spaces": 1,
        "owner_action": f"establish {row['primary_blocker']}",
        "cause": "The dependency named is not established for this space.",
        "effect": "No figure for this space may be used in a takeoff.",
        "status": "BLOCKED",
        "resolution": f"Establish {row['primary_blocker']}.",
    } for sid, row in sorted(releases.items()) if row.get("primary_blocker")]

    n_spaces = len(spaces)
    graph_exceptions = [{
        "severity": "BLOCKING", "subject": "Vector wall graph (AR-00)",
        "affected_spaces": n_spaces, "affected_uses": len(USES),
        "affected_boq_sections": "all wall and finish sections",
        "coverage_unlocked": "every net quantity on the project",
        "owner_action": "supply the DXF/DWG of AR-00",
        "issue": "The wall graph is in 115 disconnected components; 228 of 342 "
                 "nodes are wall ends meeting nothing.",
        "cause": "Wall faces are drawn as thousands of short segments and most "
                 "runs do not close into cycles.",
        "effect": "Planar face extraction (E31A) cannot derive room polygons "
                  "from this graph, so no net quantity can be built on it.",
        "status": "OPEN — see runs/graph/AR-00_graph_diagnostic.json",
        "resolution": "Connectivity repair before E31A. A DCEL over a "
                      "disconnected graph would produce no faces.",
    }, {
        "severity": "BLOCKING", "subject": "Openings (E34)",
        "affected_spaces": n_spaces,
        "affected_uses": sum(1 for u in USES if u.startswith("NET_")
                             or u in ("SKIRTING", "PAINT", "BLOCKWORK")),
        "affected_boq_sections": "all net wall quantities",
        "coverage_unlocked": "NET ceramic, NET plaster, paint, skirting, "
                             "blockwork",
        "owner_action": "supply the door/window schedule",
        "issue": "No opening has been validated on this drawing.",
        "cause": "No candidate reached two independent evidence families.",
        "effect": "Every wall figure in this workbook is GROSS. There are no "
                  "net quantities at all.",
        "status": "OPEN",
        "resolution": "A door/window schedule, or a DXF/DWG of AR-00.",
    }]

    coverage = []
    for use in sorted(USES):
        ready = blocked = na = 0
        blockers: dict[str, int] = {}
        for s in spaces:
            st = assess_space(s["space_id"], use, established[s["space_id"]])
            if st.ready:
                ready += 1
            elif not st.applicable:
                na += 1
            else:
                blocked += 1
                blockers[st.primary_blocker] = blockers.get(
                    st.primary_blocker, 0) + 1
        commonest = max(blockers, key=blockers.get) if blockers else None
        # The basis IS established for every use — it is in the release matrix.
        # Printing NOT_ESTABLISHED here would claim otherwise.
        basis = ("GROSS" if use.startswith("GROSS_") else
                 "NET" if use.startswith("NET_") else "DIRECT")
        coverage.append({
            "use": use, "basis": basis,
            "applicable": ready + blocked, "ready": ready, "blocked": blocked,
            "not_applicable": na, "commonest_blocker": commonest,
            "quantity_released": ready if ready else 0,
        })

    # One trace per quantity the engine actually established. A trace is not a
    # calculation: it records what was decided and what it was decided from.
    ledger = TraceLedger(project_id=sm["project_id"],
                         revision_id=sm["drawing_revision"])
    floor = sm.get("floor_id", "")
    for rec in wall_records:
        sid = rec["space_id"]
        v = rec.get("gross_room_perimeter_m")
        rel = releases.get(sid, {})
        status = rel.get("GROSS_PERIMETER", "")
        ledger.add(QuantityTrace(
            quantity_id=quantity_id(sm["project_id"], floor, sid, "PERIM",
                                    "GROSS"),
            space_id=sid, use="GROSS_PERIMETER", unit="m",
            value=v if status == "READY" else None,
            drawing_id=sm["drawing_id"], revision_id=sm["drawing_revision"],
            geometry_source="VECTOR_PDF_RASTER_REGION",
            boundary_edge_ids=(f"space:{sid}",),
            calculation_reference="engine.wall_model.run_wall_model",
            validation_status=(
                "VALIDATED" if wall_rows.get(sid, {}).get("status")
                == "VALIDATED" else "DRAFT"),
            release_status=status or "NOT_ASSESSED",
            primary_blocker=rel.get("primary_blocker", "")))

    # No template or assembly has been approved on this project. The library is
    # EMPTY on purpose — an empty Rules sheet says "nobody signed one", which is
    # the truth, and there is no default to fall back to.
    library = TemplateLibrary()

    return {
        "project_id": sm["project_id"],
        "revision_id": sm["drawing_revision"],
        "run_id": f"{sm['project_id']}-{sm['drawing_id']}-"
                  f"{sm['drawing_revision']}".replace(" ", "_"),
        "quantity_traces": [t.record() | {"floor": floor}
                            for t in ledger.traces],
        "room_templates": [t.record() for t in library.rooms],
        "assemblies": [a.record() for a in library.assemblies],
        # One analysed revision. compare(None, ...) returns
        # NO_PRIOR_REVISION_AVAILABLE rather than an empty change list.
        "revision_delta": compare(None, {"revision_id": sm["drawing_revision"]}),
        "title": (f"QA workbook — project {sm['project_id']} "
                  f"{sm['drawing_id']} {sm.get('floor_id', '')}".strip()),
        "spaces": spaces, "quantities": quantities, "releases": releases,
        "wall_records": wall_records, "known_gaps": known_gaps,
        "space_exceptions": space_exceptions,
        "scope_exceptions": scope_exceptions,
        "graph_exceptions": graph_exceptions, "coverage": coverage,
        "provenance": provenance,
        "manual_expected_counts": None,   # nobody has supplied a manual count
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
