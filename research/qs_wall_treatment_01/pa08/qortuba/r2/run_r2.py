"""PA08-QORTUBA-R2 runner: separate real floor-finish space from artifact cells, then measure only what survives.

R1 is immutable and is cited, never rewritten.  Nothing here reads, requests or infers the owner's withheld flooring,
skirting or profile quantities, and no rule is tuned towards any expected total.
"""

from __future__ import annotations

import hashlib
import json
import math
import subprocess
from collections import Counter, defaultdict
from pathlib import Path

from engine.ingest import ENGINE_VERSION, material_bands as MB, pipeline7 as P7
from research.qs_wall_treatment_01 import protocol as PR
from research.qs_wall_treatment_01.pa08.qortuba import blind as B, common as C
from research.qs_wall_treatment_01.pa08.qortuba.r1 import measure as ME
from research.qs_wall_treatment_01.pa08.qortuba.r2 import cells as CELLS

OUT = Path(PR.OUT_DIR) / "pa08_qortuba_r2"
R1_OUT = Path(PR.OUT_DIR) / "pa08_qortuba_r1"
BLIND_OUT = B.OUT
STOREY = "SECOND_FLOOR (title block 'SECOND FLOOR PLAN'; engine storey status HUMAN_REVIEW:CONFLICTING_FLOOR_WORDS)"
WET_CLASSES = ("BATHROOM", "WC", "KITCHEN", "LAUNDRY", "WASHROOM")
DIM_MATCH_MM = 30.0                      # an authored dimension confirms a clear span when it agrees within this
ENGINE_FILES = sorted(str(x) for x in Path("engine/ingest").glob("*.py")) + ["engine/cad_adapter.py"]


def write(name, obj):
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f"{name}.json").write_text(json.dumps(obj, indent=1, ensure_ascii=False, default=str), "utf-8")
    return name


def _sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


# ---------------------------------------------------------------------------- §5 boundary certainty
BOUNDARY_CERTAINTY = ("ESTABLISHED_MATERIAL_WALL", "ESTABLISHED_OPENING", "ESTABLISHED_OPEN_EDGE",
                      "PROVISIONAL_MATERIAL_WALL", "UNRESOLVED")


def boundary_certainty(result, vid, face_id):
    """Every boundary stretch of one face, with how certain it is, and the room-level verdict.

    A floor region is bounded by LINES.  An opening's line position comes from the host band's own face coverage - the two jambs -
    and is established whenever that band is; whether the opening is a confirmed door or only a probable one changes the SKIRTING
    deduction, not where the floor stops.  Those two facts are therefore recorded separately: CERTAINTY is about the line, and
    OPENING_TYPE_STATUS about the opening.  A chord from a band the engine never established is a different matter: that line may
    not exist at all, so it is UNRESOLVED and it blocks the region.
    """
    sites = {s["SITE_ID"]: s for s in result.sites7[vid]}
    bands = {b["BAND_ID"]: b for b in result.bands7[vid]}
    faces = {f["FACE_ID"]: f for f in result.faces[vid]}
    rows, by = [], Counter()
    provisional_types = []
    for r_ in result.brows[vid]:
        if r_["SPACE_FACE_ID"] != face_id:
            continue
        b = bands.get(r_["BAND_ID"])
        site = sites.get(r_["SITE_ID"]) if r_.get("SITE_ID") else None
        kind = r_["SEAL_KIND"]
        type_status = None
        if kind in ("FACE", "COLUMN_FACE"):
            cert = "ESTABLISHED_MATERIAL_WALL" if (b and b["STATUS"] == "ACCEPTED") else "PROVISIONAL_MATERIAL_WALL"
            why = f"material face of band {r_['BAND_ID']} ({round(b['THK']) if b else '?'} mm, {b['STATUS'] if b else '?'})"
        elif kind == "OPENING_CHORD":
            if site and site["CLASS"] == "CONFIRMED_OPEN_PASSAGE":
                cert, why = "ESTABLISHED_OPEN_EDGE", "confirmed open passage: interior space on both sides"
            elif b and b["STATUS"] == "ACCEPTED":
                cert = "ESTABLISHED_OPENING"
                type_status = site["STATUS"] if site else "UNKNOWN"
                why = (f"the opening's line position is the pair of jambs on established band {r_['BAND_ID']}, so the floor boundary is established here; "
                       f"the opening TYPE is {site['CLASS'] if site else '?'} / {type_status}, which affects the skirting deduction, not the floor extent")
                if site and site["STATUS"] != "ESTABLISHED":
                    provisional_types.append({"SITE_ID": site["SITE_ID"], "CLASS": site["CLASS"], "STATUS": site["STATUS"], "SPAN_MM": site["SPAN_MM"]})
            else:
                cert, why = "UNRESOLVED", "an opening chord on a band that was never established: the line itself is not established"
        elif kind == "JUNCTION_CHORD":
            cert, why = "ESTABLISHED_MATERIAL_WALL", "junction chord: another established wall occupies this stretch"
        else:
            cert, why = "UNRESOLVED", f"{kind}: the source does not establish this stretch"
        rows.append({"BAND_ID": r_["BAND_ID"], "SITE_ID": r_.get("SITE_ID"), "SEAL_KIND": kind, "SIDE": r_["SIDE"],
                     "LENGTH_MM": r_["LENGTH_MM"], "CERTAINTY": cert, "OPENING_TYPE_STATUS": type_status, "WHY": why})
        by[cert] += r_["LENGTH_MM"]
    # the raster is the complete perimeter: a chord from a band that hosts no boundary row still bounds this face, and only the
    # raster sees it.  Its barrier-cell count is a faithful proportional measure of how much of the perimeter is unresolved.
    f = faces[face_id]
    rel = dict(f["BOUNDARY_RELATIONS"])
    cells_total = sum(rel.values())
    cells_unres = rel.get("UNRESOLVED_CHORD", 0) + rel.get("THICKNESS_CHORD", 0) + rel.get("GLAZING_SEPARATOR", 0)
    est = sum(v for k, v in by.items() if k.startswith("ESTABLISHED"))
    tot = sum(by.values())
    blocking = [k for k in ("UNRESOLVED", "PROVISIONAL_MATERIAL_WALL") if by.get(k)]
    verdict = ("SOURCE_ESTABLISHED" if tot > 0 and not blocking and cells_unres == 0 else
               "PROVISIONAL" if tot > 0 else "NOT_ESTABLISHED")
    return rows, {"BY_CERTAINTY_MM": {k: round(v, 1) for k, v in by.items()},
                  "ESTABLISHED_SHARE_BY_LENGTH": round(est / tot, 3) if tot else 0.0,
                  "PERIMETER_CELLS": cells_total, "UNRESOLVED_PERIMETER_CELLS": cells_unres,
                  "UNRESOLVED_PERIMETER_SHARE": round(cells_unres / cells_total, 3) if cells_total else 0.0,
                  "OPENINGS_WITH_A_PROVISIONAL_TYPE": provisional_types,
                  "BLOCKING": blocking + (["UNRESOLVED_CHORDS_IN_THE_RASTER_PERIMETER"] if cells_unres else []),
                  "VERDICT": verdict,
                  "RULE": "a room is SOURCE_ESTABLISHED only when every stretch of its floor boundary is an established line and no unresolved chord touches its perimeter.  An opening whose TYPE is provisional does not block the floor area; it is carried into the skirting line as a provisional deduction.  A plausible shape is never a reason."}


# ---------------------------------------------------------------------------- §6 thickness evidence
def thickness_evidence(result, vid):
    dims = [d for d in result.registers["DIMENSION_CHAIN_REGISTER"]["ROWS"] if d.get("DIMENSION_LINE")]
    bands = [b for b in result.bands7[vid] if b["KIND"] == "S"]
    thk_counts = Counter(round(b["THK"] / 10) * 10 for b in bands if b["STATUS"] == "ACCEPTED")
    rows = []
    for b in bands:
        if b["STATUS"] != "ACCEPTED":
            continue
        half = b["THK"] / 2
        dimensioned = []
        for d in dims:
            if abs(d["MEASURED_VALUE_MM"] - b["THK"]) > DIM_MATCH_MM:
                continue
            ok = 0
            for ox, oy in d["DIMENSION_LINE"]["ORIGINS_MM"]:
                t, off = MB.band_param(b, ox, oy)
                if abs(abs(off) - half) <= DIM_MATCH_MM and b["EXTENT"][0] - 200 <= t <= b["EXTENT"][1] + 200:
                    ok += 1
            if ok >= 2:
                dimensioned.append({"DIMENSION_ID": d["DIMENSION_ID"], "DISPLAY_TEXT": d["DISPLAY_TEXT"], "MEASURED_VALUE_MM": d["MEASURED_VALUE_MM"]})
        t = round(b["THK"] / 10) * 10
        if dimensioned:
            cls = "EXPLICITLY_DIMENSIONED_WALL"
            why = f"an authored dimension of {dimensioned[0]['MEASURED_VALUE_MM']} mm has both extension origins on this band's two faces"
        elif thk_counts.get(t, 0) >= 3 and t == 150:
            cls, why = "REPEATED_GEOMETRIC_150_PATTERN", f"{thk_counts[t]} accepted bands in this drawing share a {t} mm thickness; no dimension lands on this one"
        elif thk_counts.get(t, 0) >= 3 and t == 200:
            cls, why = "REPEATED_GEOMETRIC_200_PATTERN", f"{thk_counts[t]} accepted bands in this drawing share a {t} mm thickness; no dimension lands on this one"
        else:
            cls, why = "OTHER_THICKNESS", f"thickness {t} mm, {thk_counts.get(t, 0)} band(s) of this thickness in the drawing, no dimension on this one"
        ev = b["EVIDENCE"]
        rows.append({"BAND_ID": b["BAND_ID"], "KEY": b["KEY"], "THICKNESS_MM": round(b["THK"], 1), "LENGTH_MM": round(b["LENGTH"], 1),
                     "THICKNESS_EVIDENCE_CLASS": cls, "WHY": why, "AUTHORED_DIMENSIONS": dimensioned,
                     "PAIRING_CONSISTENT": round(b["THK_SPREAD"], 1) <= MB.THK_MERGE_MM,
                     "CONTINUITY": ev.get("CONTINUITY"), "JUNCTIONS": len(ev.get("INTERSECTION", {}).get("JOINS", [])),
                     "IS_BLOCK_SYMBOL": b["BLOCK"], "FILL": ev.get("MATERIAL_FILL", {}).get("FILL"),
                     "STRENGTHENS_CANDIDATE": bool(dimensioned) and round(b["THK_SPREAD"], 1) <= MB.THK_MERGE_MM and not b["BLOCK"] and len(ev.get("INTERSECTION", {}).get("JOINS", [])) > 0})
    return {"ARTIFACT": "PA08_QORTUBA_R2_THICKNESS_EVIDENCE_REGISTER", "ROWS": rows, "COUNT": len(rows),
            "BY_CLASS": dict(Counter(x["THICKNESS_EVIDENCE_CLASS"] for x in rows)),
            "ACCEPTED_THICKNESS_HISTOGRAM_MM": dict(thk_counts),
            "RULE": "a repeated thickness convention may strengthen a candidate only when the pairing is geometrically consistent, continuity holds, the pair is not a block symbol and it joins the structure.  A repeated 150 or 200 mm gap is never a wall on its own."}


# ---------------------------------------------------------------------------- §12 dimension / area reconciliation
def dimension_reconciliation(result, vid, region_rows):
    dims = [d for d in result.registers["DIMENSION_CHAIN_REGISTER"]["ROWS"] if d.get("DIMENSION_LINE")]
    rows = []
    for reg in region_rows:
        fml = reg.get("FORMULA") or {}
        xs, ys = fml.get("CUT_LINES_X_MM") or [], fml.get("CUT_LINES_Y_MM") or []
        spans = {"X": (max(xs) - min(xs)) if len(xs) >= 2 else None, "Y": (max(ys) - min(ys)) if len(ys) >= 2 else None}
        hits = {"X": [], "Y": []}
        for d in dims:
            v = d["MEASURED_VALUE_MM"]
            og = d["DIMENSION_LINE"]["ORIGINS_MM"]
            for ax, arr, other in (("X", xs, ys), ("Y", ys, xs)):
                if spans[ax] is None or abs(v - spans[ax]) > DIM_MATCH_MM:
                    continue
                i = 0 if ax == "X" else 1
                j = 1 - i
                inside = all(min(other) - 1500 <= o[j] <= max(other) + 1500 for o in og) if other else False
                near = all(any(abs(o[i] - c) <= DIM_MATCH_MM for c in arr) for o in og)
                if inside and near:
                    hits[ax].append({"DIMENSION_ID": d["DIMENSION_ID"], "DISPLAY_TEXT": d["DISPLAY_TEXT"], "MEASURED_VALUE_MM": v})
        recon = None
        if hits["X"] and hits["Y"] and len(fml.get("RECTANGLES") or []) == 1:
            recon = round(hits["X"][0]["MEASURED_VALUE_MM"] * hits["Y"][0]["MEASURED_VALUE_MM"] / 1e6, 4)
        area = (reg.get("AREA_M2") or {}).get("VALUE")
        if recon is None or area is None:
            verdict, why = "NOT_COMPARABLE", ("no authored dimension spans this region in both axes" if recon is None else "the region has no measured area")
            diff = None
        else:
            diff = round(area - recon, 4)
            if abs(diff) <= 0.02 * max(recon, 1e-9):
                verdict, why = "AGREE", "the clear-span reconstruction from authored dimensions matches the boundary-line area within 2 per cent"
            elif abs(diff) <= 0.10 * max(recon, 1e-9):
                verdict, why = "BASIS_DIFFERENCE", "the two differ by less than a tenth: a face-line versus centre-line or finish-face basis difference, not a conflict"
            else:
                verdict, why = "CONFLICT", "the authored dimensions and the drawn boundary lines do not describe the same region"
        rows.append({"ZONE_ID": reg["ZONE_ID"], "ROOM": reg["ROOM"], "POLYGON_AREA_M2": area, "DIMENSION_RECONSTRUCTED_AREA_M2": recon,
                     "DIFFERENCE_M2": diff, "SPANS_MM": {k: round(v, 1) if v else None for k, v in spans.items()},
                     "DIMENSIONS_USED": {k: v[:2] for k, v in hits.items()}, "VERDICT": verdict, "WHY": why})
    return {"ARTIFACT": "PA08_QORTUBA_R2_DIMENSION_AREA_RECONCILIATION", "ROWS": rows, "COUNT": len(rows),
            "BY_VERDICT": dict(Counter(x["VERDICT"] for x in rows)),
            "RULE": "an independent check of drawn geometry against the drawing's own authored dimensions.  It is never compared against any withheld commercial quantity."}


# ---------------------------------------------------------------------------- §7 the bath / dress boundary, from source evidence only
def bath_dress_finding(result, vid, cell_rows, adjacency):
    """The one semantic disagreement R1 left open, decided on DWG geometry, not on the reader's claim."""
    faces = {f["FACE_ID"]: f for f in result.faces[vid]}
    baths = sorted([c for c in cell_rows if any("BATH" in (n or "").upper() for n in c["ROOM_NAMES"])],
                   key=lambda c: -faces[c["FACE_ID"]]["CENTROID_MM"][1])
    dress = next((c for c in cell_rows if any("DRESS" in (n or "").upper() for n in c["ROOM_NAMES"])), None)
    if not baths or dress is None:
        return {"CLASSIFICATION": "UNRESOLVED", "WHY": "the engine holds no labelled BATH or no labelled DRESS cell to test"}
    bath = baths[0]
    rel = next((a for a in adjacency if {a["ROOM_A"], a["ROOM_B"]} == {bath["CELL_ID"], dress["CELL_ID"]}), None)
    sites = {s["SITE_ID"]: s for s in result.sites7[vid]}
    site = None
    if rel:
        for s in rel["SITES"]:
            if s["SITE_ID"] in sites:
                site = sites[s["SITE_ID"]]
                break
    view = next(v for v in result.views if v["VIEW_ID"] == vid)
    ev = {}
    if site:
        host = next((b for b in result.bands7[vid] if b["BAND_ID"] == site["HOST_BAND_ID"]), None)
        x, y = MB.band_point(host, (site["AXIAL_START"] + site["AXIAL_END"]) / 2) if host else (None, None)
        near = [p for p in view["PRIMITIVES"] if p.kind == "SEGMENT" and x and abs((p.x1 + p.x2) / 2 - x) < 900 and abs((p.y1 + p.y2) / 2 - y) < 900]
        ev = {"HOST_BAND": {"BAND_ID": site["HOST_BAND_ID"], "THICKNESS_MM": round(host["THK"], 1) if host else None,
                            "STATUS": host["STATUS"] if host else None, "EXTENT_MM": [round(v, 1) for v in host["EXTENT"]] if host else None},
              "GAP_AT_MM": [round(x), round(y)] if x else None, "SPAN_MM": site["SPAN_MM"], "IS_END_GAP": bool(site.get("END_GAP")),
              "JAMB_A": site["JAMB_A"], "JAMB_B": site["JAMB_B"],
              "LEAF_EVIDENCE": [l["OBJECT_ID"] for l in site["LEAF_EVIDENCE"]], "SWING_EVIDENCE": [l["OBJECT_ID"] for l in site["SWING_EVIDENCE"]],
              "FRAME_EVIDENCE": [l["OBJECT_ID"] for l in site["FRAME_EVIDENCE"]],
              "DOOR_BLOCK_PIECES_IN_THE_GAP": sorted({p.object_id for p in near if p.provenance.layer == "DOOR"})[:10],
              "WALL_RETURNS_ACROSS_THE_THICKNESS": sorted({p.object_id for p in near if p.provenance.layer == "WALL" and 0.6 * (host["THK"] if host else 150) <= p.length_mm <= 1.4 * (host["THK"] if host else 150)})[:6],
              "ENGINE_SITE_CLASS": site["CLASS"], "ENGINE_SITE_STATUS": site["STATUS"]}
        if site["LEAF_EVIDENCE"] and (site["JAMB_A"] or site["JAMB_B"]):
            cls = "DOOR"
            why = ("the partition band stops short of the wall it runs into; the gap carries a door leaf and frame pieces from a door block, "
                   "with a wall return across the thickness at the jamb.  Leaf plus jamb is a door, with or without a swing arc, which this drawing never draws")
        elif site["JAMB_A"] and site["JAMB_B"]:
            cls, why = "OPEN_PASSAGE", "jamb returns at both ends with no leaf, swing or frame drawn in the gap"
        else:
            cls, why = "UNRESOLVED", "a gap exists but the evidence in it does not establish its type"
    elif rel and rel["RELATION"] == "SEPARATED_BY_MATERIAL_WALL":
        cls, why = "CONTINUOUS_WALL", "the two rooms share only material wall face; no gap exists in the partition between them"
    else:
        cls, why = "UNRESOLVED", "the two rooms are not adjacent in the raster and no site joins them"
    return {"ROOM_A": {"CELL_ID": bath["CELL_ID"], "ROOM_NAMES": bath["ROOM_NAMES"], "CENTROID_MM": faces[bath["FACE_ID"]]["CENTROID_MM"]},
            "ROOM_B": {"CELL_ID": dress["CELL_ID"], "ROOM_NAMES": dress["ROOM_NAMES"], "CENTROID_MM": faces[dress["FACE_ID"]]["CENTROID_MM"]},
            "ENGINE_RELATION": rel["RELATION"] if rel else None, "VIA": rel.get("VIA") if rel else None,
            "SOURCE_EVIDENCE": ev, "CLASSIFICATION": cls, "WHY": why,
            "R1_DISAGREEMENT": "R1 reported SEPARATED_BY_MATERIAL_WALL because it compared only the two rooms' direct raster adjacency; a doorway is a cell of its own, so two rooms joined by a door touch it, not each other",
            "SEMANTIC_READER_ROLE": "the reader raised the question; it did not decide it.  The classification above rests on the DWG entities named in SOURCE_EVIDENCE"}


# ---------------------------------------------------------------------------- §14 regression
SYNTH = ["tests/test_pa07r3_partitions.py", "tests/test_pa07r2_guards.py", "tests/test_pa07r1_guards.py", "tests/test_pa07_bands.py",
         "tests/test_pa07_topology.py", "tests/test_pa07_spaces.py", "tests/test_pa06_topology.py", "tests/test_pa06_pipeline.py",
         "tests/test_pa05_ingest.py", "tests/test_pa08_harness.py", "tests/test_pa08_qortuba.py", "tests/test_pa08_qortuba_r2.py"]


def regression(cell_rows, region_rows):
    res = subprocess.run(["python", "-m", "pytest", "-q", "-p", "no:cacheprovider", *[s for s in SYNTH if Path(s).exists()]], capture_output=True, text=True)
    lines = [l for l in res.stdout.strip().splitlines() if l.strip()]
    syn = {"SUITES": [s for s in SYNTH if Path(s).exists()], "EXIT_CODE": res.returncode, "SUMMARY_LINE": lines[-1] if lines else "",
           "STATUS": "PASS" if res.returncode == 0 else "FAIL"}
    base = Path(PR.OUT_DIR)
    def qa(tag):
        p = base / tag / "PA07_QA_REPORT.json"
        return json.loads(p.read_text("utf-8")) if p.exists() else None
    r2q, r3q = qa("pa07r2"), qa("pa07r3")
    p7757 = None
    if r2q and r3q:
        p7757 = {"NOTE": "PA07R2 (frozen engine) against the engine of this phase, same sources and runner; R2 changed no engine rule, so this delta is the one R1 already recorded",
                 "BANDS_ACCEPTED": [r2q["BANDS"]["ACCEPTED"], r3q["BANDS"]["ACCEPTED"]],
                 "ACCEPTED_DEVELOPED_M": [r2q["BANDS"]["ACCEPTED_DEVELOPED_M"], r3q["BANDS"]["ACCEPTED_DEVELOPED_M"]],
                 "SITES_BY_CLASS": [r2q["SITES"], r3q["SITES"]],
                 "SPACES_ON_PLAN_VIEWS": [r2q["SPACES_ON_PLAN_VIEWS"], r3q["SPACES_ON_PLAN_VIEWS"]],
                 "SPACES_BY_GEOMETRY_STATUS": [r2q["SPACES_BY_GEOMETRY_STATUS"], r3q["SPACES_BY_GEOMETRY_STATUS"]],
                 "NEW_FALSE_SPACES": "not measurable on P7757 without a truth set; the R2 cell classifier is applied to Qortuba only and changes no engine output",
                 "NEW_FALSE_WALLS": "none: R2 added no band rule; the accepted band set is identical to R1",
                 "NEW_ROOM_MERGES": "none: R2 added no seal; the raster is identical to R1",
                 "NEW_QUANTITY_RELEASE_FROM_UNRESOLVED_TOPOLOGY": "none: R2 only narrows what may become a floor region"}
    r1 = None
    p = R1_OUT / "PA08_QORTUBA_R1_FLOOR_REGION_REGISTER.json"
    if p.exists():
        d = json.loads(p.read_text("utf-8"))
        est_r2 = [x for x in region_rows if x["QUANTITY_STATUS"] == "SOURCE_ESTABLISHED"]
        r1 = {"R1_INTERNAL_FLOOR_REGIONS": len(d["INTERNAL_FLOOR_REGIONS"]), "R2_FLOOR_FINISH_REGIONS": len(region_rows),
              "R1_ESTABLISHED": len(d["ESTABLISHED_ROOMS"]), "R2_ESTABLISHED": len(est_r2),
              "R1_ESTABLISHED_AREA_M2": d["ESTABLISHED_INTERNAL_AREA_M2"],
              "R2_ESTABLISHED_AREA_M2": round(sum(x["AREA_M2"]["VALUE"] for x in est_r2 if x["AREA_M2"]["VALUE"]), 4),
              "CELLS_REMOVED_FROM_FLOOR_SCOPE": sum(1 for c in cell_rows if not c["MAY_BECOME_FLOOR_REGION"]),
              "NOTE": "R1 called every eligible cell an internal floor region, including wall-strip interiors and stair pockets; R2 admits only classified free space"}
    return {"ARTIFACT": "PA08_QORTUBA_R2_REGRESSION", "SYNTHETIC": syn, "P7757": p7757, "R1_COMPARISON": r1,
            "RULE": "§14: safer refusal is acceptable; a new quantity released from unresolved topology is not"}


def run():
    OUT.mkdir(parents=True, exist_ok=True)
    cfg = json.loads((BLIND_OUT / "PA08_BLIND_CONFIG.json").read_text("utf-8"))
    r = P7.run(cfg)
    vid = next(v for v in r.grids7 if r.grids7[v])
    view = next(v for v in r.views if v["VIEW_ID"] == vid)
    faces = {f["FACE_ID"]: f for f in r.faces[vid]}
    grid, seals, bands = r.grids7[vid], r.seals[vid], r.bands7[vid]
    written = []

    # ------------------------------------------------------------ §2 / §3 / §4 cell forensics and free-space eligibility
    cell_rows, thin_meta = CELLS.build(r, vid)
    adjacency = CELLS.room_adjacency(r, vid, cell_rows)
    nb = defaultdict(list)
    for a in adjacency:
        nb[a["ROOM_A"]].append({"CELL_ID": a["ROOM_B"], "RELATION": a["RELATION"], "VIA": a["VIA"]})
        nb[a["ROOM_B"]].append({"CELL_ID": a["ROOM_A"], "RELATION": a["RELATION"], "VIA": a["VIA"]})
    for c in cell_rows:
        c["ADJACENT_CELLS"] = nb.get(c["CELL_ID"], [])
    micro = [c for c in cell_rows if c["AREA_M2"] < 1.0]
    write("QORTUBA_CELL_FORENSICS_REGISTER", {
        "ARTIFACT": "QORTUBA_CELL_FORENSICS_REGISTER", "PHASE": "PA08_QORTUBA_R2 §2-§4", "STOREY": STOREY,
        "ROWS": cell_rows, "COUNT": len(cell_rows), "BY_CLASS": dict(Counter(c["SPACE_ELIGIBILITY"] for c in cell_rows)),
        "FREE_SPACE_CLASSES": CELLS.FREE_SPACE_CLASSES, "FLOOR_ELIGIBLE_CLASSES": CELLS.FLOOR_ELIGIBLE_CLASSES,
        "SOURCE_DERIVED_THRESHOLD": thin_meta,
        "MICRO_CELLS_UNDER_1_M2": {"COUNT": len(micro), "BY_CLASS": dict(Counter(c["SPACE_ELIGIBILITY"] for c in micro)),
                                   "ROWS": [{"CELL_ID": c["CELL_ID"], "AREA_M2": c["AREA_M2"], "CLEAR_WIDTH_MM": c["CLEAR_WIDTH_MM"],
                                             "SPACE_ELIGIBILITY": c["SPACE_ELIGIBILITY"], "REASON": c["REASON"]} for c in micro]},
        "RULE": "no cell is classified by its area.  Every rejection names the physical element whose interior the cell is, or the drawing's own thinnest material band; a cell that nothing explains is HUMAN_REVIEW and is neither deleted nor promoted",
        "ROOM_ADJACENCY": adjacency})
    written.append("QORTUBA_CELL_FORENSICS_REGISTER")

    # ------------------------------------------------------------ physical spaces (every cell, with its class)
    sp_by_id = {s["SPACE_ID"]: s for s in r.spaces[vid]}
    phys = []
    for c in cell_rows:
        sp = sp_by_id[c["CELL_ID"]]
        phys.append({"PHYSICAL_SPACE_ID": c["CELL_ID"], "FACE_ID": c["FACE_ID"], "STOREY": STOREY,
                     "SPACE_ELIGIBILITY": c["SPACE_ELIGIBILITY"], "ROOM_NAMES": c["ROOM_NAMES"], "SEMANTIC_ANCHORS": c["SEMANTIC_ANCHORS"],
                     "RASTER_AREA_M2_TOPOLOGY_ONLY": c["AREA_M2"], "CLEAR_WIDTH_MM": c["CLEAR_WIDTH_MM"], "BBOX_MM": c["BBOX_MM"],
                     "ENGINE_GEOMETRY_STATUS": sp["GEOMETRY_STATUS"], "IDENTITY_STATUS": sp["IDENTITY_STATUS"],
                     "IS_TRUE_FREE_SPACE": c["IS_TRUE_FREE_SPACE"], "ADJACENT_CELLS": c["ADJACENT_CELLS"]})
    write("PA08_QORTUBA_R2_PHYSICAL_SPACE_REGISTER", {"ARTIFACT": "PA08_QORTUBA_R2_PHYSICAL_SPACE_REGISTER", "ROWS": phys, "COUNT": len(phys),
                                                      "BY_CLASS": dict(Counter(x["SPACE_ELIGIBILITY"] for x in phys)),
                                                      "TRUE_FREE_SPACES": sum(1 for x in phys if x["IS_TRUE_FREE_SPACE"])})
    written.append("PA08_QORTUBA_R2_PHYSICAL_SPACE_REGISTER")

    # ------------------------------------------------------------ §5 boundary certainty (every free-space cell)
    cert_rows, cert_of = [], {}
    for c in cell_rows:
        if not (c["MAY_BECOME_FLOOR_REGION"] or c["SPACE_ELIGIBILITY"] in ("OPEN_ROOF_OR_TERRACE", "STAIR_OR_LANDING_SPACE")):
            continue
        rows, summary = boundary_certainty(r, vid, c["FACE_ID"])
        cert_of[c["CELL_ID"]] = summary
        cert_rows.append({"PHYSICAL_SPACE_ID": c["CELL_ID"], "ROOM": " / ".join(c["ROOM_NAMES"]) or "UNLABELLED",
                          "SPACE_ELIGIBILITY": c["SPACE_ELIGIBILITY"], "BOUNDARY": rows, **summary})
    write("PA08_QORTUBA_R2_BOUNDARY_CERTAINTY_REGISTER", {"ARTIFACT": "PA08_QORTUBA_R2_BOUNDARY_CERTAINTY_REGISTER", "ROWS": cert_rows,
                                                          "COUNT": len(cert_rows), "CLASSES": BOUNDARY_CERTAINTY,
                                                          "BY_VERDICT": dict(Counter(x["VERDICT"] for x in cert_rows))})
    written.append("PA08_QORTUBA_R2_BOUNDARY_CERTAINTY_REGISTER")

    # ------------------------------------------------------------ §8 floor-finish regions
    region_rows = []
    for c in cell_rows:
        if not c["MAY_BECOME_FLOOR_REGION"]:
            continue
        f = faces[c["FACE_ID"]]
        area, formula = ME.face_polygon_area(f, grid, seals)
        summary = cert_of.get(c["CELL_ID"], {})
        verdict = summary.get("VERDICT", "NOT_ESTABLISHED")
        room = " / ".join(c["ROOM_NAMES"]) or "UNLABELLED"
        if area is None:
            av = {"VALUE": None, "STATE": "NOT_ESTABLISHED", "WHY": formula.get("WHY")}
        elif verdict == "SOURCE_ESTABLISHED":
            av = {"VALUE": round(area, 4), "STATE": "SOURCE_ESTABLISHED", "WHY": "every stretch of this region's floor boundary is an established material wall or an established opening, and the arrangement of those lines reproduces the face"}
        else:
            av = {"VALUE": round(area, 4), "STATE": "PROVISIONAL", "WHY": f"boundary certainty {verdict}: {summary.get('BY_CERTAINTY_MM')}; the area follows the drawn lines but the region's extent is not established"}
        wet = any(x in WET_CLASSES for x in c["SEMANTIC_CLASSES"]) or c["SPACE_ELIGIBILITY"] == "SERVICE_FREE_SPACE"
        opens = [d for d in c["DOOR_RELATIONS"]]
        region_rows.append({
            "ZONE_ID": "FZ-" + c["CELL_ID"].split("-")[1], "PHYSICAL_SPACE_ID": c["CELL_ID"], "ROOM": room,
            "SEMANTIC_IDENTITY": {"ROOM_NAMES": c["ROOM_NAMES"], "CLASSES": c["SEMANTIC_CLASSES"],
                                  "STATUS": "SOURCE_TEXT_ESTABLISHED" if c["ROOM_NAMES"] else "UNLABELLED"},
            "FUNCTIONAL_ZONE": ("WET_ROOM" if wet else "DRY_ROOM"),
            "FLOOR_FINISH_TRADE_ZONE": {"ZONE_PER_PHYSICAL_SPACE": True,
                                        "WHY": "one trade zone per physical space: two spaces joined by a door or an open edge are not assumed to carry one finish, and no finish schedule exists for this project"},
            "AREA_M2": av, "BOUNDARY_IDS": c["BOUNDARY_IDS"], "OPENING_IDS": [d["SITE_ID"] for d in opens],
            "OPEN_EDGES": [d["SITE_ID"] for d in opens if d["CLASS"] in ("CONFIRMED_OPEN_PASSAGE",)],
            "FINISH_TYPE_STATUS": {"VALUE": None, "STATE": "SOURCE_REQUIRED", "WHY": "no finishes schedule, legend or owner instruction exists for this project; the region is geometry, the finish is not established"},
            "QUANTITY_STATUS": av["STATE"], "BOUNDARY_CERTAINTY": summary, "FORMULA": formula,
            "RASTER_AREA_M2_TOPOLOGY_ONLY": c["AREA_M2"]})
    est = [x for x in region_rows if x["QUANTITY_STATUS"] == "SOURCE_ESTABLISHED"]
    write("PA08_QORTUBA_R2_FLOOR_FINISH_REGION_REGISTER", {
        "ARTIFACT": "PA08_QORTUBA_R2_FLOOR_FINISH_REGION_REGISTER", "ROWS": region_rows, "COUNT": len(region_rows),
        "BY_STATUS": dict(Counter(x["QUANTITY_STATUS"] for x in region_rows)),
        "ESTABLISHED_AREA_M2": round(sum(x["AREA_M2"]["VALUE"] for x in est if x["AREA_M2"]["VALUE"]), 4),
        "PROVISIONAL_AREA_M2": round(sum(x["AREA_M2"]["VALUE"] for x in region_rows if x["QUANTITY_STATUS"] == "PROVISIONAL" and x["AREA_M2"]["VALUE"]), 4),
        "LAYERS_KEPT_SEPARATE": ["PHYSICAL_SPACE", "FUNCTIONAL_ZONE", "FLOOR_FINISH_TRADE_ZONE"],
        "AREA_METHOD": "ARRANGEMENT_OF_BOUNDARY_LINES (pa08/qortuba/r1/measure.py), unchanged from R1 and cross-checked against the rasterised face",
        "RULE": "only a cell classified as physical free space may appear here; a wall-strip interior, a frame pocket, a stair component or an outline interior can never enter floor area"})
    written.append("PA08_QORTUBA_R2_FLOOR_FINISH_REGION_REGISTER")

    # ------------------------------------------------------------ §9 skirting and profile paths
    skirt, prof, wall_rows = [], [], []
    sites_by = {s["SITE_ID"]: s for s in r.sites7[vid]}
    for reg in region_rows:
        c = next(x for x in cell_rows if x["CELL_ID"] == reg["PHYSICAL_SPACE_ID"])
        p = ME.path_rows(r.brows[vid], c["FACE_ID"])
        host, opening, junction, unres = ME.total(p["PHYSICAL_HOST_WALL"]), ME.total(p["OPENING"]), ME.total(p["JUNCTION"]), ME.total(p["UNRESOLVED"])
        state = reg["QUANTITY_STATUS"]
        wet = reg["FUNCTIONAL_ZONE"] == "WET_ROOM"
        door_ded = [{"SITE_ID": x["SITE_ID"], "CLASS": sites_by[x["SITE_ID"]]["CLASS"], "SPAN_MM": sites_by[x["SITE_ID"]]["SPAN_MM"]}
                    for x in p["OPENING"] if x.get("SITE_ID") and x["SITE_ID"] in sites_by]
        open_edges = [d for d in door_ded if d["CLASS"] == "CONFIRMED_OPEN_PASSAGE"]
        wall_rows.append({"ROOM": reg["ROOM"], "ZONE_ID": reg["ZONE_ID"], "PHYSICAL_SPACE_ID": reg["PHYSICAL_SPACE_ID"],
                          "PHYSICAL_WALL_PATH_LM": {"VALUE": round(host / 1000, 3), "STATE": state, "WHY": "developed length of the material wall and column faces bounding this region, cut at junctions so no stretch is owned twice"},
                          "SKIRTING_ELIGIBLE_LM": {"VALUE": round(host / 1000, 3), "STATE": state,
                                                   "WHY": "the same wall-face path: a skirting needs a wall face to stand on.  Door and open-edge chords carry no wall face and are therefore not in the path, which is geometry, not a commercial deduction"},
                          "PROFILE_GEOMETRIC_PATH_LM": {"VALUE": round((host + opening + junction) / 1000, 3), "STATE": state,
                                                        "WHY": "the closed ceiling-level perimeter: wall faces plus the opening and junction chords a profile runs across"},
                          "UNRESOLVED_EDGE_LM": {"VALUE": round(unres / 1000, 3), "STATE": "NOT_ESTABLISHED", "WHY": "boundary the source does not establish; it belongs to no trade line"},
                          "DOOR_DEDUCTIONS": door_ded, "OPEN_EDGES": open_edges,
                          "WET_ROOM_NON_SKIRTING_EDGES": {"VALUE": None, "STATE": "SOURCE_REQUIRED",
                                                          "WHY": "a wet room may be tiled to a height instead of skirted; no finishes schedule or owner instruction exists for this project, so which of its edges take no skirting is not established"} if wet else None,
                          "SEPARATE_TRADE_LINES": "SKIRTING and PROFILE are separate trade lines and are never added together, even where their geometry coincides"})
        skirt.append({"ROOM": reg["ROOM"], "ZONE_ID": reg["ZONE_ID"], "STATE": state, "TOTAL_LM": round(host / 1000, 3),
                      "PATH": [{"BAND_ID": x["BAND_ID"], "SIDE": x["SIDE"], "LENGTH_MM": x["LENGTH_MM"], "SEAL_KIND": x["SEAL_KIND"]} for x in p["PHYSICAL_HOST_WALL"]],
                      "DOOR_DEDUCTIONS": door_ded, "OPEN_EDGES": open_edges,
                      "UNRESOLVED_EDGES_LM": round(unres / 1000, 3),
                      "COMMERCIAL_RULES": {"STATE": "SOURCE_REQUIRED", "WHY": "no owner measurement rule for this project was supplied and none was assumed"}})
        prof.append({"ROOM": reg["ROOM"], "ZONE_ID": reg["ZONE_ID"], "STATE": state, "TOTAL_LM": round((host + opening + junction) / 1000, 3),
                     "PATH": [{"BAND_ID": x["BAND_ID"], "SIDE": x["SIDE"], "LENGTH_MM": x["LENGTH_MM"], "SEAL_KIND": x["SEAL_KIND"]} for x in p["PHYSICAL_HOST_WALL"] + p["OPENING"] + p["JUNCTION"]],
                     "PROFILE_TYPE_AND_SIZE": {"VALUE": None, "STATE": "SOURCE_REQUIRED", "WHY": "no reflected ceiling plan or profile detail for this project"}})
    write("PA08_QORTUBA_R2_SKIRTING_PATH_REGISTER", {"ARTIFACT": "PA08_QORTUBA_R2_SKIRTING_PATH_REGISTER", "ROWS": skirt, "COUNT": len(skirt),
                                                     "TOTAL_ESTABLISHED_LM": round(sum(x["TOTAL_LM"] for x in skirt if x["STATE"] == "SOURCE_ESTABLISHED"), 3)})
    write("PA08_QORTUBA_R2_PROFILE_PATH_REGISTER", {"ARTIFACT": "PA08_QORTUBA_R2_PROFILE_PATH_REGISTER", "ROWS": prof, "COUNT": len(prof),
                                                    "TOTAL_ESTABLISHED_LM": round(sum(x["TOTAL_LM"] for x in prof if x["STATE"] == "SOURCE_ESTABLISHED"), 3)})
    write("PA08_QORTUBA_R2_WALL_LENGTH_REGISTER", {"ARTIFACT": "PA08_QORTUBA_R2_WALL_LENGTH_REGISTER", "ROWS": wall_rows, "COUNT": len(wall_rows)})
    written += ["PA08_QORTUBA_R2_SKIRTING_PATH_REGISTER", "PA08_QORTUBA_R2_PROFILE_PATH_REGISTER", "PA08_QORTUBA_R2_WALL_LENGTH_REGISTER"]

    # ------------------------------------------------------------ §10 ceiling geometry
    label, meta = grid["label"], grid["cell"]
    ceil = []
    for reg in region_rows:
        c = next(x for x in cell_rows if x["CELL_ID"] == reg["PHYSICAL_SPACE_ID"])
        stair_adj = [a for a in c["ADJACENT_CELLS"] if any(z["CELL_ID"] == a["CELL_ID"] and z["SPACE_ELIGIBILITY"] == "STAIR_OR_LANDING_SPACE" for z in cell_rows)]
        opens_to_stair = [a for a in stair_adj if a["RELATION"] in ("SEPARATED_BY_OPENING", "SEPARATED_BY_UNRESOLVED_BOUNDARY")]
        conditions = {"STAIR_OPENING_INSIDE_THE_REGION": bool(c["IS_STAIR_COMPONENT"]),
                      "SHAFT_OR_VOID_INSIDE_THE_REGION": bool(c["IS_FURNITURE_OR_CASEWORK_INTERIOR"]),
                      "OPEN_TO_ABOVE_EVIDENCE": False,
                      "OPENS_ONTO_A_STAIR_CELL": bool(opens_to_stair)}
        if any(conditions.values()):
            state, area, why = "NOT_ESTABLISHED", None, f"a ceiling-plan condition is present: {[k for k, v in conditions.items() if v]}; the ceiling plan is not derived from the floor region"
        elif reg["AREA_M2"]["VALUE"] is None:
            state, area, why = "NOT_ESTABLISHED", None, "the floor region itself has no measured area"
        else:
            state, area = reg["QUANTITY_STATUS"], reg["AREA_M2"]["VALUE"]
            why = ("no stair opening, no shaft, no void and no open-to-above line is drawn inside this region, so its ceiling plan geometry "
                   "is derived from the floor region.  This is a geometric derivation only: the ceiling FINISH is not inferred")
        ceil.append({"ROOM": reg["ROOM"], "ZONE_ID": reg["ZONE_ID"], "CEILING_PLAN_AREA_M2": {"VALUE": area, "STATE": state, "WHY": why},
                     "DERIVATION": "CEILING_PLAN = CLEANED_PHYSICAL_FLOOR_REGION" if area is not None else "NOT_DERIVED",
                     "CONDITIONS_TESTED": conditions,
                     "CEILING_FINISH_TYPE": {"VALUE": None, "STATE": "SOURCE_REQUIRED", "WHY": "no reflected ceiling plan or finishes schedule for this project; the finish is never inferred from the geometry"},
                     "CEILING_HEIGHT": {"VALUE": None, "STATE": "SOURCE_REQUIRED", "WHY": "no section or level for this storey"}})
    write("PA08_QORTUBA_R2_CEILING_REGION_REGISTER", {"ARTIFACT": "PA08_QORTUBA_R2_CEILING_REGION_REGISTER", "ROWS": ceil, "COUNT": len(ceil),
                                                      "BY_STATE": dict(Counter(x["CEILING_PLAN_AREA_M2"]["STATE"] for x in ceil)),
                                                      "RULE": "case by case: the ceiling plan follows the cleaned floor region only when the four conditions are all absent, and the finish is never inferred"})
    written.append("PA08_QORTUBA_R2_CEILING_REGION_REGISTER")

    # ------------------------------------------------------------ §11 block / plaster / paint, and the wet rooms
    acc = [b for b in bands if b["STATUS"] == "ACCEPTED"]
    by_thk = defaultdict(float)
    for b in acc:
        by_thk[round(b["THK"] / 10) * 10] += b["LENGTH"] / 1000
    blk = [{"BAND_ID": b["BAND_ID"], "THICKNESS_MM": round(b["THK"], 1), "DEVELOPED_LENGTH_M": round(b["LENGTH"] / 1000, 3),
            "BAND_TYPE": b["BAND_TYPE"], "LAYERS": sorted({f_.provenance.layer for f_ in b["FACES"].values()}),
            "AREA_M2": {"VALUE": None, "STATE": "NOT_ESTABLISHED", "WHY": "a blockwork area needs a wall height; this project has no section, elevation or owner height and none was invented"}} for b in acc]
    write("PA08_QORTUBA_R2_BLOCK_INPUT_REGISTER", {"ARTIFACT": "PA08_QORTUBA_R2_BLOCK_INPUT_REGISTER", "ROWS": blk, "COUNT": len(blk),
                                                   "BLOCK_WALL_LENGTH_M_BY_THICKNESS": {str(k): round(v, 3) for k, v in sorted(by_thk.items())},
                                                   "TOTAL_LENGTH_M": round(sum(by_thk.values()), 3), "AREA_STATE": "NOT_ESTABLISHED"})
    plaster, paint, wet_rows = [], [], []
    for reg, wl in zip(region_rows, wall_rows):
        host = wl["PHYSICAL_WALL_PATH_LM"]["VALUE"]
        state = reg["QUANTITY_STATUS"]
        plaster.append({"ROOM": reg["ROOM"], "ZONE_ID": reg["ZONE_ID"], "PLASTERABLE_FACE_LENGTH_M": {"VALUE": host, "STATE": state, "WHY": "the room-side wall-face path of this region"},
                        "AREA_M2": {"VALUE": None, "STATE": "NOT_ESTABLISHED", "WHY": "a plaster area needs a plaster height; none exists for this project"}})
        paint.append({"ROOM": reg["ROOM"], "ZONE_ID": reg["ZONE_ID"], "PAINT_ELIGIBLE_FACE_LENGTH_M": {"VALUE": host, "STATE": state, "WHY": "the same wall-face path; paint follows the plastered face"},
                      "AREA_M2": {"VALUE": None, "STATE": "NOT_ESTABLISHED", "WHY": "a paint area needs a height and the treated-face decision; neither exists for this project"},
                      "PAINT_SYSTEM": {"VALUE": None, "STATE": "SOURCE_REQUIRED", "WHY": "no finishes schedule for this project"}})
        if reg["FUNCTIONAL_ZONE"] == "WET_ROOM":
            wet_rows.append({"ROOM": reg["ROOM"], "ZONE_ID": reg["ZONE_ID"], "PHYSICAL_SPACE_ID": reg["PHYSICAL_SPACE_ID"],
                             "WET_CLASS_SOURCE": "room name only: no sanitary fixture, tiling note or wet-area hatch is drawn in this project",
                             "FLOOR_AREA_M2": reg["AREA_M2"], "WET_ROOM_HOST_WALL_LM": {"VALUE": host, "STATE": state, "WHY": "the wall-face path that a wet-wall treatment would run along"},
                             "WALL_TILE_HEIGHT": {"VALUE": None, "STATE": "SOURCE_REQUIRED", "WHY": "no height parameter for this project; P7757 heights are not Qortuba rules"},
                             "WET_TREATMENT": {"VALUE": None, "STATE": "SOURCE_REQUIRED", "WHY": "a wet-room treatment cannot be established from a room name alone"}})
    write("PA08_QORTUBA_R2_PLASTER_INPUT_REGISTER", {"ARTIFACT": "PA08_QORTUBA_R2_PLASTER_INPUT_REGISTER", "ROWS": plaster, "COUNT": len(plaster), "AREA_STATE": "NOT_ESTABLISHED"})
    write("PA08_QORTUBA_R2_PAINT_INPUT_REGISTER", {"ARTIFACT": "PA08_QORTUBA_R2_PAINT_INPUT_REGISTER", "ROWS": paint, "COUNT": len(paint), "AREA_STATE": "NOT_ESTABLISHED"})
    write("PA08_QORTUBA_R2_WET_ROOM_REGISTER", {"ARTIFACT": "PA08_QORTUBA_R2_WET_ROOM_REGISTER", "ROWS": wet_rows, "COUNT": len(wet_rows),
                                                "RULE": "a wet room here is a room NAME, not an established wet condition; no fixture is drawn in this project"})
    written += ["PA08_QORTUBA_R2_BLOCK_INPUT_REGISTER", "PA08_QORTUBA_R2_PLASTER_INPUT_REGISTER", "PA08_QORTUBA_R2_PAINT_INPUT_REGISTER", "PA08_QORTUBA_R2_WET_ROOM_REGISTER"]

    # ------------------------------------------------------------ §6 thickness evidence, §12 dimension reconciliation, §7 bath / dress
    write("PA08_QORTUBA_R2_THICKNESS_EVIDENCE_REGISTER", thickness_evidence(r, vid)); written.append("PA08_QORTUBA_R2_THICKNESS_EVIDENCE_REGISTER")
    dimrec = dimension_reconciliation(r, vid, region_rows)
    write("PA08_QORTUBA_R2_DIMENSION_AREA_RECONCILIATION", dimrec); written.append("PA08_QORTUBA_R2_DIMENSION_AREA_RECONCILIATION")
    bd = bath_dress_finding(r, vid, cell_rows, adjacency)

    # ------------------------------------------------------------ §7 opening register
    op = []
    for s in r.sites7[vid]:
        h = next((b for b in bands if b["BAND_ID"] == s["HOST_BAND_ID"]), None)
        op.append({"SITE_ID": s["SITE_ID"], "HOST_BAND_ID": s["HOST_BAND_ID"], "HOST_WALL_THICKNESS_MM": round(h["THK"], 1) if h else None,
                   "HOST_WALL_STATUS": h["STATUS"] if h else None, "CLASS": s["CLASS"], "STATUS": s["STATUS"], "SPAN_MM": s["SPAN_MM"],
                   "IS_END_GAP": bool(s.get("END_GAP")), "JAMB_A": s["JAMB_A"], "JAMB_B": s["JAMB_B"],
                   "LEAF_EVIDENCE": [x["OBJECT_ID"] for x in s["LEAF_EVIDENCE"]], "SWING_EVIDENCE": [x["OBJECT_ID"] for x in s["SWING_EVIDENCE"]],
                   "FRAME_EVIDENCE": [x["OBJECT_ID"] for x in s["FRAME_EVIDENCE"]], "REASON": s["REASON"],
                   "OPENING_HEIGHT": {"VALUE": None, "STATE": "SOURCE_REQUIRED", "WHY": "no elevation, section or door schedule for this project"}})
    write("PA08_QORTUBA_R2_OPENING_REGISTER", {"ARTIFACT": "PA08_QORTUBA_R2_OPENING_REGISTER", "ROWS": op, "COUNT": len(op),
                                               "BY_CLASS": dict(Counter(x["CLASS"] for x in op)), "BY_STATUS": dict(Counter(x["STATUS"] for x in op)),
                                               "BATH_DRESS_FINDING": bd,
                                               "ROOM_TO_ROOM_RELATIONS": [a for a in adjacency if a["SITES"] or a["RELATION"] != "SEPARATED_BY_MATERIAL_WALL"]})
    written.append("PA08_QORTUBA_R2_OPENING_REGISTER")
    return r, vid, cell_rows, region_rows, wall_rows, adjacency, bd, dimrec, cert_rows, written, phys, ceil, wet_rows, by_thk


def finish():
    (r, vid, cell_rows, region_rows, wall_rows, adjacency, bd, dimrec, cert_rows, written, phys, ceil, wet_rows, by_thk) = run()
    faces = {f["FACE_ID"]: f for f in r.faces[vid]}

    # ------------------------------------------------------------ §13 semantic reconciliation, through the room graph
    reader = json.loads((Path("research/qs_wall_treatment_01/pa08/qortuba/r1/SEMANTIC_READER_OUTPUT.json")).read_text("utf-8"))
    by_cell = {c["CELL_ID"]: c for c in cell_rows}
    named = [c for c in cell_rows if c["ROOM_NAMES"]]
    def match(label):
        base = label.split("(")[0].strip().upper()
        cands = [c for c in named if any(base == (n or "").strip().upper() for n in c["ROOM_NAMES"])]
        return sorted(cands, key=lambda c: -faces[c["FACE_ID"]]["CENTROID_MM"][1])
    groups = defaultdict(list)
    for rr in reader["ROOMS"]:
        groups[rr["LABEL"].split("(")[0].strip().upper()].append(rr)
    mapping = {}
    for base, rrs in groups.items():
        cands = match(base)
        for k, rr in enumerate(sorted(rrs, key=lambda z: z["Y"])):
            if k < len(cands):
                mapping[rr["LABEL"]] = cands[k]["CELL_ID"]
    rel_of = {}
    for a in adjacency:
        rel_of[tuple(sorted((a["ROOM_A"], a["ROOM_B"])))] = a
    rec_rows, agree, disagree, ncomp = [], 0, 0, 0
    for a in reader["ADJACENCIES"]:
        ca, cb = mapping.get(a["ROOM_A"]), mapping.get(a["ROOM_B"])
        if ca is None or cb is None or ca == cb:
            rec_rows.append({"READER": a, "ENGINE": {"RELATION": "ROOM_NOT_MATCHED"}, "VERDICT": "NOT_COMPARABLE"}); ncomp += 1; continue
        rel = rel_of.get(tuple(sorted((ca, cb))))
        eng = {"RELATION": rel["RELATION"], "VIA": rel["VIA"], "SITES": rel["SITES"], "KINDS": rel["KINDS"]} if rel else {"RELATION": "NOT_ADJACENT"}
        want = a["RELATION"]
        got = eng["RELATION"]
        if want == "SEPARATED_WALL_WITH_DOOR":
            v = "AGREE" if got == "SEPARATED_BY_DOOR" else ("PARTIAL_ENGINE_PROVISIONAL" if got in ("SEPARATED_BY_OPENING", "SEPARATED_BY_UNRESOLVED_SITE", "SEPARATED_BY_UNRESOLVED_BOUNDARY") else "DISAGREE_ENGINE_SEES_NO_OPENING")
        elif want == "SEPARATED_WALL_WITH_DOORLESS_OPENING":
            v = "AGREE" if got in ("SEPARATED_BY_OPENING", "SEPARATED_BY_DOOR", "SEPARATED_BY_UNRESOLVED_SITE") else "DISAGREE_ENGINE_SEES_NO_OPENING"
        elif want == "SEPARATED_WALL_NO_OPENING":
            v = "AGREE" if got in ("SEPARATED_BY_MATERIAL_WALL", "NOT_ADJACENT") else ("PARTIAL_ENGINE_PROVISIONAL" if got.endswith("UNRESOLVED_BOUNDARY") else "DISAGREE_ENGINE_SEES_AN_OPENING")
        elif want == "INTENTIONALLY_OPEN":
            v = "AGREE" if got in ("SEPARATED_BY_OPENING",) else "DISAGREE_ENGINE_SEPARATED"
        else:
            v = "NOT_COMPARABLE"
        rec_rows.append({"READER": a, "ENGINE": eng, "VERDICT": v})
        agree += v == "AGREE"; disagree += v.startswith("DISAGREE"); ncomp += v == "NOT_COMPARABLE"
    rec = {"ARTIFACT": "PA08_QORTUBA_R2_SEMANTIC_RECONCILIATION", "READER_SOURCE": "reused from PA08_QORTUBA_R1, cleanly isolated: the reader saw the PDF render only and no engine output",
           "READER_STATUS": reader["STATUS"], "READER_POWERS": "it may challenge identity, open-versus-separated and an obvious opening; it may not move a coordinate, close a polygon, supply an area or promote a quantity state",
           "ROOM_MATCHING": mapping, "ROWS": rec_rows, "COUNT": len(rec_rows), "AGREE": agree, "DISAGREE": disagree,
           "BY_VERDICT": dict(Counter(x["VERDICT"] for x in rec_rows)),
           "R1_TO_R2_CHANGE": "R2 reads the relation through the doorway cell, so a door no longer reads as a solid wall; the bath / dress disagreement is resolved in PA08_QORTUBA_R2_OPENING_REGISTER.BATH_DRESS_FINDING"}
    write("PA08_QORTUBA_R2_SEMANTIC_RECONCILIATION", rec); written.append("PA08_QORTUBA_R2_SEMANTIC_RECONCILIATION")

    # ------------------------------------------------------------ §14 regression
    regr = regression(cell_rows, region_rows)
    write("PA08_QORTUBA_R2_REGRESSION", regr); written.append("PA08_QORTUBA_R2_REGRESSION")

    # ------------------------------------------------------------ coverage and defects
    est = [x for x in region_rows if x["QUANTITY_STATUS"] == "SOURCE_ESTABLISHED"]
    prov = [x for x in region_rows if x["QUANTITY_STATUS"] == "PROVISIONAL"]
    cov = {"ARTIFACT": "PA08_QORTUBA_R2_COVERAGE", "STOREY": STOREY,
           "CELLS_TOTAL": len(cell_rows), "CELLS_BY_CLASS": dict(Counter(c["SPACE_ELIGIBILITY"] for c in cell_rows)),
           "CELLS_REMOVED_FROM_FLOOR_SCOPE": sum(1 for c in cell_rows if not c["MAY_BECOME_FLOOR_REGION"]),
           "MICRO_CELLS_UNDER_1_M2": sum(1 for c in cell_rows if c["AREA_M2"] < 1.0),
           "MICRO_CELLS_STILL_IN_FLOOR_SCOPE": sum(1 for c in cell_rows if c["AREA_M2"] < 1.0 and c["MAY_BECOME_FLOOR_REGION"]),
           "FLOOR_FINISH_REGIONS": len(region_rows), "ESTABLISHED": len(est), "PROVISIONAL": len(prov),
           "ESTABLISHED_AREA_M2": round(sum(x["AREA_M2"]["VALUE"] for x in est if x["AREA_M2"]["VALUE"]), 3),
           "PROVISIONAL_AREA_M2": round(sum(x["AREA_M2"]["VALUE"] for x in prov if x["AREA_M2"]["VALUE"]), 3),
           "HUMAN_REVIEW_CELLS": sum(1 for c in cell_rows if c["STATUS"] == "HUMAN_REVIEW"),
           "BLOCK_WALL_LENGTH_M_BY_THICKNESS": {str(k): round(v, 3) for k, v in sorted(by_thk.items())},
           "DIMENSION_RECONCILIATION": dimrec["BY_VERDICT"], "SEMANTIC": rec["BY_VERDICT"],
           "VERTICAL_QUANTITIES": "NONE: no height exists for this project, so every area needing a height is NOT_ESTABLISHED",
           "WITHHELD_OWNER_DATA": "NOT_REQUESTED_NOT_OPENED_NOT_INFERRED"}
    write("PA08_QORTUBA_R2_COVERAGE", cov); written.append("PA08_QORTUBA_R2_COVERAGE")

    defects = []
    hr = [c for c in cell_rows if c["STATUS"] == "HUMAN_REVIEW"]
    if hr:
        defects.append({"DEFECT_ID": "QR2-01", "SEVERITY": "MEDIUM_YIELD_LOSS_SAFE",
                        "SOURCE_CONDITION": "unlabelled regions of the plan (the stair hall, the lift lobby, the bedroom vestibule) that no element explains and no room name identifies",
                        "ENGINE_BEHAVIOUR": f"{len(hr)} cells are HUMAN_REVIEW, including {sorted((round(c['AREA_M2'], 1) for c in hr), reverse=True)[:4]} m2",
                        "EXPECTED_SAFE_BEHAVIOUR": "neither deleted nor promoted; they carry no floor quantity and are listed for a human",
                        "SILENT_WRONG": False, "SAFE_REFUSAL": True, "AFFECTED_TRADES": ["FLOOR_FINISH", "SKIRTING", "PROFILE"]})
    nonest = [x for x in region_rows if x["QUANTITY_STATUS"] != "SOURCE_ESTABLISHED"]
    if nonest:
        defects.append({"DEFECT_ID": "QR2-02", "SEVERITY": "HIGH_YIELD_LOSS_SAFE",
                        "SOURCE_CONDITION": "partitions whose thickness the drawing never dimensions, and openings whose type the drawing does not establish",
                        "ENGINE_BEHAVIOUR": f"{len(nonest)} of {len(region_rows)} floor-finish regions stay PROVISIONAL: {[x['ROOM'] for x in nonest]}",
                        "EXPECTED_SAFE_BEHAVIOUR": "provisional is the correct state; the loss is yield, not accuracy",
                        "SILENT_WRONG": False, "SAFE_REFUSAL": True, "AFFECTED_TRADES": ["FLOOR_FINISH", "SKIRTING", "PROFILE", "PLASTER", "PAINT"]})
    if bd["CLASSIFICATION"] != "CONTINUOUS_WALL":
        defects.append({"DEFECT_ID": "QR2-03", "SEVERITY": "MEDIUM_FIXED_IN_R2",
                        "SOURCE_CONDITION": "a doorway is a cell of its own, so two rooms joined by a door are not raster-adjacent to each other",
                        "ENGINE_BEHAVIOUR": "R1 read that as a solid wall and recorded a false semantic disagreement; R2 reads room relations through the doorway cell",
                        "EXPECTED_SAFE_BEHAVIOUR": f"the bath / dress boundary is {bd['CLASSIFICATION']} on DWG evidence",
                        "SILENT_WRONG": False, "SAFE_REFUSAL": True, "AFFECTED_TRADES": ["NONE_DIRECTLY"]})
    defects.append({"DEFECT_ID": "QR2-04", "SEVERITY": "MEDIUM_CORRECTED_IN_R2",
                    "SOURCE_CONDITION": "a free cell inside a wall strip, a door frame or a stair tread run looks exactly like a small room to a raster",
                    "ENGINE_BEHAVIOUR": f"R1 offered all 53 cells as internal floor regions, including a 0.417 m2 stair pocket that was SOURCE_ESTABLISHED; R2 removes {cov['CELLS_REMOVED_FROM_FLOOR_SCOPE']} cells from floor scope by naming the element whose interior each one is",
                    "EXPECTED_SAFE_BEHAVIOUR": "an element's interior never enters floor area", "SILENT_WRONG": True, "SAFE_REFUSAL": False,
                    "AFFECTED_TRADES": ["FLOOR_FINISH", "SKIRTING", "PROFILE"], "STATUS_NOW": "CORRECTED_IN_R2"})
    dr = {"ARTIFACT": "PA08_QORTUBA_R2_DEFECT_REGISTER", "ROWS": defects, "COUNT": len(defects),
          "SILENT_WRONG_STILL_OPEN": sum(1 for d in defects if d.get("SILENT_WRONG") and d.get("STATUS_NOW") != "CORRECTED_IN_R2")}
    write("PA08_QORTUBA_R2_DEFECT_REGISTER", dr); written.append("PA08_QORTUBA_R2_DEFECT_REGISTER")

    # ------------------------------------------------------------ §15 readiness
    principal = [x for x in region_rows if x["SEMANTIC_IDENTITY"]["ROOM_NAMES"]]
    conds = [
        {"N": 1, "CONDITION": "all principal internal floor-finish regions are individually represented",
         "PASS": len(principal) >= 9 and all(x["AREA_M2"]["VALUE"] is not None for x in principal),
         "EVIDENCE": f"{len(principal)} named internal regions, each its own cell: {[x['ROOM'] for x in principal]}"},
        {"N": 2, "CONDITION": "their boundaries are established enough to calculate floor area without a merged or provisional macro-cell",
         "PASS": len(est) == len(principal),
         "EVIDENCE": f"{len(est)} of {len(principal)} named regions are SOURCE_ESTABLISHED; the rest are PROVISIONAL: {[x['ROOM'] for x in principal if x['QUANTITY_STATUS'] != 'SOURCE_ESTABLISHED']}"},
        {"N": 3, "CONDITION": "skirting-eligible wall paths are independently measurable",
         "PASS": all(w["SKIRTING_ELIGIBLE_LM"]["STATE"] == "SOURCE_ESTABLISHED" for w in wall_rows if w["ROOM"] != "UNLABELLED") and bool(wall_rows),
         "EVIDENCE": f"{sum(1 for w in wall_rows if w['SKIRTING_ELIGIBLE_LM']['STATE'] == 'SOURCE_ESTABLISHED')} of {len(wall_rows)} regions have an established skirting path"},
        {"N": 4, "CONDITION": "profile geometric paths are independently measurable",
         "PASS": all(w["PROFILE_GEOMETRIC_PATH_LM"]["STATE"] == "SOURCE_ESTABLISHED" for w in wall_rows if w["ROOM"] != "UNLABELLED") and bool(wall_rows),
         "EVIDENCE": f"{sum(1 for w in wall_rows if w['PROFILE_GEOMETRIC_PATH_LM']['STATE'] == 'SOURCE_ESTABLISHED')} of {len(wall_rows)} regions have an established profile path"},
        {"N": 5, "CONDITION": "artifact micro-cells do not materially contaminate floor, skirting or profile quantities",
         "PASS": cov["MICRO_CELLS_STILL_IN_FLOOR_SCOPE"] == 0,
         "EVIDENCE": f"{cov['MICRO_CELLS_STILL_IN_FLOOR_SCOPE']} cells under 1 m2 remain in floor scope out of {cov['MICRO_CELLS_UNDER_1_M2']}"},
        {"N": 6, "CONDITION": "no withheld commercial quantity has been accessed",
         "PASS": True, "EVIDENCE": "no register, module or run in this phase reads, requests or infers the owner's flooring, skirting or profile quantities"},
        {"N": 7, "CONDITION": "results are frozen before comparison", "PASS": True, "EVIDENCE": "FREEZE_PA08_QORTUBA_R2 is written by this run, before any comparison"},
    ]
    ready = all(c["PASS"] for c in conds)
    decision = {"ARTIFACT": "PA08_QORTUBA_R2_READY_FOR_EXTERNAL_COMPARISON", "READY_FOR_WITHHELD_FLOORING_COMPARISON": "YES" if ready else "NO",
                "CONDITIONS": conds, "FAILED": [c["N"] for c in conds if not c["PASS"]],
                "SCOPE_NOTE": "the question is whether the withheld flooring package can be compared meaningfully, not whether every decorative, stair or roof cell is resolved"}
    write("PA08_QORTUBA_R2_READY_FOR_EXTERNAL_COMPARISON", decision); written.append("PA08_QORTUBA_R2_READY_FOR_EXTERNAL_COMPARISON")

    # ------------------------------------------------------------ §17 freeze
    head = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip()
    dirty = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True).stdout.strip().splitlines()
    r1fr = json.loads((R1_OUT / "FREEZE_PA08_QORTUBA_R1.json").read_text("utf-8"))
    r1_ok = all((R1_OUT / f"{n}.json").exists() and _sha(R1_OUT / f"{n}.json") == h for n, h in r1fr["CONTENTS"].items())
    blind = json.loads((BLIND_OUT / "FREEZE_PA08_QORTUBA_BLIND_01.json").read_text("utf-8"))
    blind_ok = all((BLIND_OUT / n).exists() and _sha(BLIND_OUT / n) == h for n, h in blind.get("FILES", {}).items())
    contents = {n: _sha(OUT / f"{n}.json") for n in sorted(set(written)) if (OUT / f"{n}.json").exists()}
    fr = {"ARTIFACT": "FREEZE_PA08_QORTUBA_R2", "PROJECT_ALIAS": "QORTUBA",
          "PRIOR_FREEZES_NOT_REWRITTEN": [
              {"FREEZE": "PA08_QORTUBA_BLIND_01", "DIGEST": blind.get("FREEZE_DIGEST_SHA256"), "FILE_COUNT": len(blind.get("FILES", {})), "VERIFIED_ON_DISK": blind_ok},
              {"FREEZE": "PA08_QORTUBA_R1", "DIGEST": r1fr.get("DIGEST"), "FILE_COUNT": len(r1fr.get("CONTENTS", {})), "VERIFIED_ON_DISK": r1_ok}],
          "GIT_HEAD_AT_FREEZE": head,
          "WORKING_TREE_AT_FREEZE": {"CLEAN": not dirty, "UNCOMMITTED_PATHS": [l[3:] for l in dirty][:20],
                                     "MEANING": "CLEAN means GIT_HEAD_AT_FREEZE contains exactly the code that produced these registers"},
          "ENGINE_VERSION": ENGINE_VERSION, "ENGINE_FILE_HASHES": {f: _sha(f) for f in ENGINE_FILES if Path(f).exists()},
          "ENGINE_RULES_CHANGED_IN_R2": "none: R2 adds a measurement-layer classifier and changes no engine rule; the accepted bands, seals and raster are identical to R1",
          "SOURCE_HASHES": blind["SOURCE_HASHES"], "DECODER": blind["DECODER"],
          "CONTENTS": contents, "COUNT": len(contents),
          "READY_FOR_WITHHELD_FLOORING_COMPARISON": decision["READY_FOR_WITHHELD_FLOORING_COMPARISON"],
          "WITHHELD_OWNER_DATA": "NOT_REQUESTED_NOT_OPENED_NOT_INFERRED"}
    fr["DIGEST"] = hashlib.sha256(json.dumps({k: v for k, v in fr.items() if k != "DIGEST"}, sort_keys=True, default=str).encode()).hexdigest()
    write("FREEZE_PA08_QORTUBA_R2", fr)
    return {"WRITTEN": written, "FREEZE": fr["DIGEST"], "COVERAGE": cov, "REGRESSION": regr, "READY": decision, "BATH_DRESS": bd,
            "REGIONS": region_rows, "CELLS": cell_rows, "DEFECTS": dr, "DIMREC": dimrec, "PRIOR_VERIFIED": {"BLIND": blind_ok, "R1": r1_ok}}


if __name__ == "__main__":
    o = finish()
    print("FREEZE", o["FREEZE"][:16], "| registers", len(o["WRITTEN"]), "| prior freezes verified", o["PRIOR_VERIFIED"])
    print("cells", o["COVERAGE"]["CELLS_BY_CLASS"])
    print("regions", o["COVERAGE"]["FLOOR_FINISH_REGIONS"], "established", o["COVERAGE"]["ESTABLISHED"], o["COVERAGE"]["ESTABLISHED_AREA_M2"], "m2 | provisional", o["COVERAGE"]["PROVISIONAL"], o["COVERAGE"]["PROVISIONAL_AREA_M2"], "m2")
    print("bath/dress:", o["BATH_DRESS"]["CLASSIFICATION"], "|", o["BATH_DRESS"]["WHY"][:110])
    print("dimension reconciliation", o["DIMREC"]["BY_VERDICT"])
    print("READY:", o["READY"]["READY_FOR_WITHHELD_FLOORING_COMPARISON"], "failed conditions", o["READY"]["FAILED"])
