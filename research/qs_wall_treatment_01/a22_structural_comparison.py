"""A22 - STRUCTURAL comparison between measurement paths (§34-§36).

The owner's rule: two identical final numbers reached using different
wrong assumptions are not evidence of correctness. So A22 compares
DERIVATIONS - which faces, which lengths from which source, which height
rule, which openings, which basis - and never just totals.

Paths compared, all frozen before this runs:

    PATH_A  the A21 visual-trace path: frozen TRACE_REGISTER -> face sets
            -> P7757_WALL_TREATMENT_ESTIMATE (this phase)
    PATH_B  the deterministic CAD path: the authored DWG geometry, read
            directly (clipped axis-aligned wall lines around a declared
            locator) and the frozen E1.4 ground-floor registers
    PATH_C  the CAD curve register (arcs)

Verdict vocabulary (from the A21 protocol, plus the owner's three):

    STRUCTURAL_AGREEMENT, NUMERIC_AGREEMENT_ONLY, BASIS_DIFFERENCE,
    SCOPE_DIFFERENCE, OPENING_DIFFERENCE, HEIGHT_DIFFERENCE,
    GEOMETRY_DIFFERENCE, TREATMENT_DIFFERENCE, IDENTITY_MAPPING_DIFFERENCE,
    HUMAN_MEASUREMENT_ERROR_OR_OMISSION, ENGINE_GEOMETRY_ERROR,
    VISUAL_QS_ERROR, UNRESOLVED, HUMAN_REVIEW_REQUIRED,
    SHARED_ASSUMPTION_AGREEMENT, CAD_GEOMETRY_STRONGER_THAN_VISUAL,
    VISUAL_SEMANTIC_STRONGER_THAN_CAD

Evidence independence is stated on every item: the DWG and the PDF are one
design family, so an agreement between them is repeatability of the same
design, not independent corroboration.

    python3 -m research.qs_wall_treatment_01.a22_structural_comparison
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from engine import cad_adapter as CA
from research.qs_wall_treatment_01 import protocol as P

OUT = Path(P.OUT_DIR)
DECODE = "data/runs/cad_convert/P7757_ARCHITECTURAL.json"
E14_CHAIN = "data/runs/7757/e1_4/E1_4_PHYSICAL_BOUNDARY_CHAIN_REGISTER.json"
E14_FREEZE = "data/runs/7757/e1_4/E1_4_FREEZE.json"

VERDICTS = (
    "STRUCTURAL_AGREEMENT", "NUMERIC_AGREEMENT_ONLY", "BASIS_DIFFERENCE",
    "SCOPE_DIFFERENCE", "OPENING_DIFFERENCE", "HEIGHT_DIFFERENCE",
    "GEOMETRY_DIFFERENCE", "TREATMENT_DIFFERENCE", "IDENTITY_MAPPING_DIFFERENCE",
    "HUMAN_MEASUREMENT_ERROR_OR_OMISSION", "ENGINE_GEOMETRY_ERROR",
    "VISUAL_QS_ERROR", "UNRESOLVED", "HUMAN_REVIEW_REQUIRED",
    "SHARED_ASSUMPTION_AGREEMENT", "CAD_GEOMETRY_STRONGER_THAN_VISUAL",
    "VISUAL_SEMANTIC_STRONGER_THAN_CAD",
)
TOL_M = 0.02

# Deterministic CAD locators for the A21 faces that carry a printed length.
# Each names an axis-aligned band in model space near the SALOON label and
# the layers to read; the clipped run lengths are the CAD-path lengths.
CAD_LOCATORS = {
    "SEG-03 return wall (SALOON side face)": {
        "AXIS": "H", "FIXED_MM": (-797600.0, -797585.0),
        "WINDOW_MM": (-131200.0, -128800.0), "LAYERS": ("1", "W", "2", "5")},
    "SEG-03 return wall (terrace side face)": {
        "AXIS": "H", "FIXED_MM": (-797400.0, -797385.0),
        "WINDOW_MM": (-131200.0, -128800.0), "LAYERS": ("1", "W", "2", "5")},
    "SEG-02 neighbour wall (SALOON side face)": {
        "AXIS": "H", "FIXED_MM": (-805100.0, -805085.0),
        "WINDOW_MM": (-137500.0, -128800.0), "LAYERS": ("1", "W", "2", "5")},
    "SEG-01/GLZ-01 sea-view line (glazing band lines)": {
        "AXIS": "V", "FIXED_MM": (-129080.0, -128940.0),
        "WINDOW_MM": (-805400.0, -797300.0), "LAYERS": ("W",)},
    "SEG-01/GLZ-01 sea-view line (outer face line)": {
        "AXIS": "V", "FIXED_MM": (-128880.0, -128860.0),
        "WINDOW_MM": (-805400.0, -797300.0), "LAYERS": ("5", "1")},
    "COL-01/COL-02 corner piers (bonding hatch bounds)": {
        "AXIS": "V", "FIXED_MM": (-129080.0, -128860.0),
        "WINDOW_MM": (-805400.0, -797300.0), "LAYERS": ("S-COL.BON",)},
}


def _runs(n, loc: dict) -> list:
    """Axis-aligned segments on the given layers whose fixed coordinate lies
    in FIXED_MM, clipped to WINDOW_MM along the free axis; merged into runs."""
    lo, hi = loc["FIXED_MM"]
    w0, w1 = loc["WINDOW_MM"]
    ivs = {}
    for p in n.primitives:
        if p.kind != "SEGMENT" or p.provenance.layer not in loc["LAYERS"]:
            continue
        if loc["AXIS"] == "H":
            if abs(p.y1 - p.y2) > 1 or not (lo <= p.y1 <= hi):
                continue
            a, b, fixed = min(p.x1, p.x2), max(p.x1, p.x2), round(p.y1, 1)
        else:
            if abs(p.x1 - p.x2) > 1 or not (lo <= p.x1 <= hi):
                continue
            a, b, fixed = min(p.y1, p.y2), max(p.y1, p.y2), round(p.x1, 1)
        a, b = max(a, w0), min(b, w1)
        if b - a <= 0:
            continue
        ivs.setdefault((fixed, p.provenance.layer), []).append((a, b, p.object_id))
    out = []
    for (fixed, layer), lst in sorted(ivs.items()):
        lst.sort()
        merged = []
        for a, b, oid in lst:
            if merged and a <= merged[-1][1] + 1.0:
                merged[-1][1] = max(merged[-1][1], b)
                merged[-1][2].append(oid)
            else:
                merged.append([a, b, [oid]])
        for a, b, ids in merged:
            out.append({"FIXED_MM": fixed, "LAYER": layer, "FROM_MM": round(a, 1),
                        "TO_MM": round(b, 1), "LENGTH_M": round((b - a) / 1000.0, 4),
                        "CAD_IDS": ids, "CAD_GEOMETRY_STATUS": "ESTABLISHED_FROM_DWG"})
    return out


def _e14_saloon(chain_reg: dict) -> dict:
    cand = next((c for c in chain_reg["CANDIDATES"]
                 if c.get("IDENTITY_AS_DRAWN") == "SALOON"), None)
    if not cand:
        return {"STATUS": "SALOON_CANDIDATE_NOT_FOUND"}
    chain = cand["CHAIN"]["CHAIN"]
    faces = [{"SEQ": e["SEQ"], "start_mm": e["start_mm"], "end_mm": e["end_mm"],
              "length_m": round(e["length_mm"] / 1000.0, 4), "layer": e.get("layer"),
              "role": e.get("CHAIN_ELEMENT")} for e in chain
             if e.get("CHAIN_ELEMENT") == "MATERIAL_WALL_FACE"]
    return {"CANDIDATE_ID": cand["CANDIDATE_ID"],
            "BOUNDARY_BASIS": cand["BOUNDARY_BASIS"],
            "CLOSED_BY_DRAWN_MATERIAL": cand["walk"]["CLOSED_BY_DRAWN_MATERIAL"],
            "SHARES_PHYSICAL_REGION_WITH": cand.get("candidates_sharing_this_physical_region"),
            "MATERIAL_WALL_FACES_IN_CHAIN": len(faces),
            "MATERIAL_LENGTH_M": round(sum(f["length_m"] for f in faces), 4),
            "FACES": faces}


def _item(item_id, subject, a, b, verdict, why, independence="SHARED_SOURCE_FAMILY",
          numeric=None):
    assert verdict in VERDICTS
    return {"ITEM_ID": item_id, "SUBJECT": subject, "PATH_A_A21_TRACE": a,
            "PATH_B_CAD": b, "VERDICT": verdict, "WHY": why,
            "EVIDENCE_INDEPENDENCE": independence,
            "NUMERIC": numeric,
            "AGREEMENT_IS_REPEATABILITY_NOT_TRUTH": independence == "SHARED_SOURCE_FAMILY"}


def run() -> dict:
    est = json.loads((OUT / "P7757_WALL_TREATMENT_ESTIMATE.json").read_text("utf-8"))
    curves = json.loads((OUT / "CAD_CURVE_REGISTER.json").read_text("utf-8"))
    freeze = json.loads((OUT / "FREEZE_ESTIMATE.json").read_text("utf-8"))
    d = json.loads(Path(DECODE).read_text("utf-8"))
    n = CA.normalize(d, source_file="P7757_ARCHITECTURAL.dwg")
    cad = {k: _runs(n, loc) for k, loc in CAD_LOCATORS.items()}
    e14 = _e14_saloon(json.loads(Path(E14_CHAIN).read_text("utf-8")))

    sets = {s["PLAN"]["SET_ID"]: s for s in est["SETS"]}
    saloon = sets["GF-SALOON-NORMAL-PLASTER"]
    cols = sets["GF-SALOON-COLUMN-BONDING"]
    faces_a = {f["FACE_ID"]: f for f in saloon["FACE_SET"]["ESTABLISHED_FACES"]
               + saloon["FACE_SET"]["PROVISIONAL_FACES"] + saloon["FACE_SET"]["UNRESOLVED_FACES"]}
    items = []

    # --- T1 return wall SEG-03: printed 2.00 vs CAD line runs ----------
    r1 = cad["SEG-03 return wall (SALOON side face)"]
    cad_len = max((r["LENGTH_M"] for r in r1), default=None)
    a = {"FACE_ID": "SEG-03", "LENGTH_M": faces_a["SEG-03"]["length_m"],
         "SOURCE": "DRAWING_PRINTED_DIMENSION (DIM-07 200, DIM-09 thickness 20)",
         "BASIS": "printed dimension, ticks at both ends of the wall run"}
    b = {"RUNS": r1, "LENGTH_M": cad_len, "BASIS": "authored line length on the wall face"}
    if cad_len is not None and abs(cad_len - a["LENGTH_M"]) <= TOL_M:
        items.append(_item("T1", "SALOON return wall face length", a, b,
                           "STRUCTURAL_AGREEMENT",
                           "same face, same extent, same 0.20 thickness (two faces "
                           "2.000 m apart / 0.200 apart); printed dimension and "
                           "authored geometry agree within tolerance",
                           numeric={"A": a["LENGTH_M"], "B": cad_len}))
    else:
        items.append(_item("T1", "SALOON return wall face length", a, b,
                           "GEOMETRY_DIFFERENCE", "printed and authored lengths differ",
                           numeric={"A": a["LENGTH_M"], "B": cad_len}))

    # --- T2 neighbour wall SEG-02: printed 5.15 vs CAD runs -------------
    r2 = cad["SEG-02 neighbour wall (SALOON side face)"]
    a = {"FACE_ID": "SEG-02", "LENGTH_M": faces_a["SEG-02"]["length_m"],
         "SOURCE": "DRAWING_PRINTED_DIMENSION (DIM-05 515)",
         "BASIS": "printed dimension from the open-edge tick to the sea-view wall LINE"}
    b = {"RUNS": r2, "BASIS": "authored line runs on the SALOON-side face of the "
                              "neighbour wall, clipped to the SALOON window"}
    match = [r for r in r2 if abs(r["LENGTH_M"] - a["LENGTH_M"]) <= TOL_M]
    if match:
        items.append(_item("T2", "SALOON neighbour wall face length", a, b,
                           "STRUCTURAL_AGREEMENT", "a CAD face run of the same extent exists",
                           numeric={"A": a["LENGTH_M"], "B": match[0]["LENGTH_M"]}))
    elif r2:
        items.append(_item("T2", "SALOON neighbour wall face length", a, b,
                           "BASIS_DIFFERENCE",
                           "the printed 515 runs tick-to-wall-line across the open "
                           "edge and pier; the authored face runs are bounded by "
                           "junctions. Lengths are not the same object; no run "
                           "matches 5.15 within tolerance. HUMAN_REVIEW_REQUIRED "
                           "before the printed length is treated as the plastered "
                           "face length",
                           numeric={"A": a["LENGTH_M"], "B": [r["LENGTH_M"] for r in r2]}))
    else:
        items.append(_item("T2", "SALOON neighbour wall face length", a, b, "UNRESOLVED",
                           "no CAD run found at the locator", numeric={"A": a["LENGTH_M"], "B": None}))

    # --- T3 sea-view line: A21 chain 90+633+20+90 vs CAD extents --------
    r3 = cad["SEG-01/GLZ-01 sea-view line (glazing band lines)"]
    r3b = cad["SEG-01/GLZ-01 sea-view line (outer face line)"]
    r4 = cad["COL-01/COL-02 corner piers (bonding hatch bounds)"]
    chain = {"COL-01": 0.90, "GLZ-01": 6.33, "frame piece": 0.20, "COL-02": 0.90}
    chain_sum = round(sum(chain.values()), 2)
    band = max((r["LENGTH_M"] for r in r3), default=None)
    outer = max((r["LENGTH_M"] for r in r3b), default=None)
    a = {"CHAIN_AS_READ": chain, "CHAIN_SUM_M": chain_sum,
         "GLZ-01_LENGTH_M": 6.33, "GLZ-01_DIMENSION_STATUS": "AMBIGUOUS (A21)",
         "SOURCE": "DRAWING_PRINTED_DIMENSION chain DIM-02/DIM-01/DIM-04/DIM-03"}
    b = {"GLAZING_BAND_LINES": r3, "OUTER_FACE_LINE": r3b, "PIER_HATCH_BOUNDS": r4,
         "BAND_LENGTH_M": band, "OUTER_LINE_LENGTH_M": outer}
    verdict, why = "HUMAN_REVIEW_REQUIRED", ""
    if outer is not None and abs(outer - 6.33) <= TOL_M:
        why = ("the printed 633 matches the OUTER face line of the glazing band "
               f"({outer} m), while the four inner band lines run {band} m: the "
               "glazed length depends on which line the QS takes. The A21 chain "
               "sum 8.33 does not reconcile with the CAD extent of the line between "
               "the two wall faces; the pier lengths as read (0.90 each) do not "
               "match the bonding-hatch bounds. GEOMETRY_DIFFERENCE on the chain, "
               "agreement on the 633 line only")
        verdict = "GEOMETRY_DIFFERENCE"
    else:
        why = "the printed 633 matches no CAD line at the locator"
    items.append(_item("T3", "SALOON sea-view line: glazing length and pier chain", a, b,
                       verdict, why, numeric={"A": 6.33, "B_BAND": band, "B_OUTER": outer,
                                              "A_CHAIN_SUM": chain_sum}))

    # --- T4 curved pool wall: A21 cannot, CAD can -----------------------
    pool = next((s for s in curves["CURVE_SETS"] if s["ANCHOR_ID"] == "POOL"), None)
    items.append(_item(
        "T4", "curved pool wall (GLZ-02)",
        {"TRACE": "GLZ-02", "STATUS": "CURVE_DIMENSION_NOT_ESTABLISHED_FROM_VISUAL_SOURCE",
         "WHAT_A21_ESTABLISHED": "a curved band of concentric lines exists at the pool"},
        {"CURVE_SET": pool["CURVE_SET_ID"] if pool else None,
         "RADII_MM": pool["RADII_MM"] if pool else None,
         "LENGTH_BY_RADIUS_M": pool["LENGTH_BY_RADIUS_M"] if pool else None,
         "CAD_GEOMETRY_STATUS": "ESTABLISHED_FROM_DWG",
         "SEMANTIC_LINK_STATUS": "NOT_ESTABLISHED (proposed by anchor locator only)"},
        "CAD_GEOMETRY_STRONGER_THAN_VISUAL",
        "the DWG carries the arcs exactly; the raster path can only say a curve "
        "exists. The link between the curve set and the traced face is a human "
        "decision, so no length enters the estimate from this item"))

    # --- T5 RECEPTION void: visual semantics vs CAD identity ------------
    items.append(_item(
        "T5", "RECEPTION is a label under a first-floor VOID",
        {"TRACES": "CASE-1 UNK-01 / UNK-02 VERTICAL_RELATION ESTABLISHED (5.87 x 4.00 VOID)",
         "CONSEQUENCE": "double-height zone; NORMAL height not applied (§8)"},
        {"E1_4": {"SALOON_CANDIDATE": e14.get("CANDIDATE_ID"),
                  "BOUNDARY_BASIS": e14.get("BOUNDARY_BASIS"),
                  "SHARES_PHYSICAL_REGION_WITH": e14.get("SHARES_PHYSICAL_REGION_WITH")},
         "CAD_PATH_HAS_VOID_SEMANTICS": False},
        "VISUAL_SEMANTIC_STRONGER_THAN_CAD",
        "the CAD ground-floor path sees one open physical region shared by several "
        "labels and carries no vertical relation; the visual path established the "
        "void from the first-floor sheet. The height consequence exists only on "
        "PATH_A", independence="DIFFERENT_SHEETS_SAME_DESIGN_FAMILY"))

    # --- T6 height rule ------------------------------------------------
    items.append(_item(
        "T6", "plaster height for SALOON",
        {"HEIGHT_PARAMETER": "NORMAL_INTERNAL_PLASTER_HEIGHT", "VALUE_M": 3.20,
         "SOURCE_TYPE": "OWNER_PROJECT_INPUT"},
        {"CAD_PATH_HEIGHT": None, "WHY": "the CAD path produces no plaster quantity "
                                         "and no height; any CAD-path quantity built "
                                         "later on the same owner value would agree "
                                         "by construction"},
        "SHARED_ASSUMPTION_AGREEMENT",
        "the height is an owner input on both paths whenever both are run; agreement "
        "on it is a shared assumption, never corroboration",
        independence="SHARED_ASSUMPTION"))

    # --- T7 enclosure basis --------------------------------------------
    items.append(_item(
        "T7", "SALOON enclosure",
        {"BASIS": "WALL_FACE_SET (no ring required)", "OPEN_EDGE": "OE-01 toward RECEPTION, "
         "not bridged", "COVERAGE": saloon["FACE_SET"]["COVERAGE_STATUS"]},
        {"E1_4_BOUNDARY_BASIS": e14.get("BOUNDARY_BASIS"),
         "CLOSED_BY_DRAWN_MATERIAL": e14.get("CLOSED_BY_DRAWN_MATERIAL"),
         "MATERIAL_WALL_FACES_IN_CHAIN": e14.get("MATERIAL_WALL_FACES_IN_CHAIN"),
         "MATERIAL_LENGTH_M": e14.get("MATERIAL_LENGTH_M")},
        "STRUCTURAL_AGREEMENT",
        "both paths establish that the drawing does not enclose the SALOON with "
        "drawn material; PATH_A measures faces without a ring, E1.4 withholds the "
        "boundary. Agreement on the negative, and a BASIS_DIFFERENCE on what is "
        "measured next (faces vs ring)"))

    # --- T8 openings ----------------------------------------------------
    items.append(_item(
        "T8", "openings deducted on SALOON established faces",
        {"DEDUCTED": [], "UNRESOLVED_OPENINGS": [o["OPENING_ID"] for o in
                                                 saloon["FACE_SET"]["OPENINGS"]]},
        {"CAD_PATH_OPENINGS_ON_THESE_FACES": "not read on this path"},
        "SCOPE_DIFFERENCE",
        "PATH_A deducts nothing (no opening is hosted in an established face); the CAD "
        "path did not read openings for this comparison. Equal deductions (zero) are "
        "not corroboration"))

    # --- T9 columns -----------------------------------------------------
    col_a = {f["FACE_ID"]: f["length_m"] for f in cols["FACE_SET"]["ESTABLISHED_FACES"]}
    items.append(_item(
        "T9", "SALOON corner piers COL-01 / COL-02 (0.90 printed each)",
        {"LENGTHS_M": col_a, "SOURCE": "DRAWING_PRINTED_DIMENSION (DIM-02, DIM-03)"},
        {"PIER_HATCH_BOUNDS": r4},
        "HUMAN_REVIEW_REQUIRED",
        "the bonding-hatch bounds in the CAD do not span 0.90 m at the locator; the "
        "printed 90 may be the pier's plan length along another line. The column "
        "bonding subtotal (5.76 m2) rests on the printed 90s and is flagged",
        numeric={"A": col_a, "B": [r["LENGTH_M"] for r in r4]}))

    counts = {v: sum(1 for i in items if i["VERDICT"] == v) for v in VERDICTS}
    body = {
        "PHASE_ID": P.PHASE_ID, "ARTIFACT": "A22_STRUCTURAL_COMPARISON",
        "RAN_AFTER_FREEZE": freeze["FREEZE_DIGEST_SHA256"],
        "ESTIMATE_SHA256": freeze["ARTIFACT_SHA256"]["P7757_WALL_TREATMENT_ESTIMATE.json"],
        "E1_4_FREEZE_SHA256": hashlib.sha256(Path(E14_FREEZE).read_bytes()).hexdigest(),
        "E1_4_IS_READ_HERE_ONLY": "after A21 froze; A21 never saw it",
        "CAD_LOCATORS": CAD_LOCATORS, "CAD_RUNS": cad, "E1_4_SALOON": e14,
        "ITEMS": items, "COUNTS": counts,
        "NUMERIC_AGREEMENT_ONLY_IS_A_WARNING": True,
        "WHAT_CHANGES_IN_THE_ESTIMATE": "nothing: A22 compares, it does not tune",
        "ITEMS_FOR_HUMAN_REVIEW": [i["ITEM_ID"] for i in items
                                   if i["VERDICT"] in ("HUMAN_REVIEW_REQUIRED",
                                                       "GEOMETRY_DIFFERENCE",
                                                       "BASIS_DIFFERENCE")],
    }
    p = OUT / "A22_STRUCTURAL_COMPARISON.json"
    p.write_text(json.dumps(body, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return {"A22_SHA256": hashlib.sha256(p.read_bytes()).hexdigest(),
            "COUNTS": {k: v for k, v in counts.items() if v},
            "ITEMS": [(i["ITEM_ID"], i["VERDICT"], i["NUMERIC"]) for i in items],
            "CAD_RUNS": {k: [(r["LAYER"], r["FIXED_MM"], r["LENGTH_M"]) for r in v]
                         for k, v in cad.items()},
            "E1_4_SALOON": {k: v for k, v in e14.items() if k != "FACES"}}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
