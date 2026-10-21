"""PART B - the visual trace schema, its transform, and its proof.

A trace is a claim with a place. The place is given in the coordinates of
the PROCESSED sheet the reader actually saw, and it must survive every
step that produced that sheet - rotation, trim, downscale - so it can be
projected back onto the original PDF page.

The transform is not asserted. round_trip() checks the algebra and
ink_agreement() checks the PIXELS: it takes patches from the processed
image, maps their centres back to the original page, and compares what is
actually printed there. Algebra that inverts cleanly but lands on the
wrong part of the drawing would pass the first test and fail the second.

    python3 -m research.a21_trace_sufficiency_01.visual_trace
"""

from __future__ import annotations

import hashlib
import json
import random
from pathlib import Path

from PIL import Image

from research.a21_trace_sufficiency_01 import protocol as P
from research.a21_trace_sufficiency_01 import source_sufficiency as S

OUT = Path("data/experiments/A21_TRACE_SUFFICIENCY_01")

# ==================================================================
# the schema
# ==================================================================

# Schema normalisation (TRACE_ARCHITECTURE_HARDENING). Two claim types
# are added to the protocol's list; raw outputs that expressed a vertical
# relation as UNRESOLVED_FEATURE + RELATION stay valid and are VIEWED as
# VERTICAL_RELATION by the register without any raw byte changing.
ADDED_CLAIM_TYPES = ("VERTICAL_RELATION", "CROSS_SHEET_RELATION")
CLAIM_TYPES = tuple(P.CLAIM_TYPES) + ADDED_CLAIM_TYPES

# Three statuses that are NEVER collapsed into one another:
#   TRACE_RECORD_STATUS       is the record well-formed?
#   TRACE_LOCATABILITY_STATUS does it carry geometry that can be drawn
#                             and projected?
#   the five semantic statuses (GEOMETRY / IDENTITY / DIMENSION /
#                             TREATMENT / PARAMETER)
# A VALID record that is NOT locatable is a legitimate, useful trace - it
# is how a reader says "there is something here I cannot place".
TRACE_RECORD_STATUSES = ("VALID", "INVALID")
TRACE_LOCATABILITY_STATUSES = ("LOCATABLE", "NOT_ESTABLISHED")

# Cross-sheet relations. Two sheets whose projected graphics differ are
# NOT thereby contradictory - an elevation projection can hide an
# internal void. Promotion to an established contradiction needs all
# five conditions; anything less is POTENTIAL.
CROSS_SHEET_RELATION_STATUSES = (
    "SAME_PHYSICAL_LOCATION_ESTABLISHED",
    "SAME_PHYSICAL_LOCATION_PROVISIONAL",
    "DIFFERENT_PHYSICAL_LOCATION",
    "NOT_ESTABLISHED",
)
CONTRADICTION_STATUSES = ("ESTABLISHED_CROSS_SHEET_CONTRADICTION",
                          "POTENTIAL_CROSS_SHEET_CONTRADICTION")
CONTRADICTION_PROMOTION_REQUIRES = (
    "both claims are traced",
    "both sheet identities are established",
    "the physical relationship / location is established",
    "the drawings are expected to describe the same condition",
    "the represented conditions are incompatible",
)


def classify_contradiction(claim_a: dict, claim_b: dict,
                           relation_status: str,
                           same_condition_expected: bool,
                           incompatible: bool) -> str:
    """POTENTIAL unless every promotion condition holds."""
    traced = all(locatability_status(c) == "LOCATABLE"
                 for c in (claim_a, claim_b))
    sheets = all(c.get("SHEET_ID") for c in (claim_a, claim_b))
    located = relation_status == "SAME_PHYSICAL_LOCATION_ESTABLISHED"
    if traced and sheets and located and same_condition_expected and incompatible:
        return "ESTABLISHED_CROSS_SHEET_CONTRADICTION"
    return "POTENTIAL_CROSS_SHEET_CONTRADICTION"


# The three mapping tests, named precisely, with what each does NOT prove.
MAPPING_TESTS = {
    "COORDINATE_ROUNDTRIP_PASS": (
        "processed -> original -> processed inverts at ~0.0 px on every "
        "sheet"),
    "SOURCE_INK_CORRESPONDENCE_PASS": (
        "random ink points on the processed sheet land on the same ink on "
        "the original page, compared at equal PHYSICAL area"),
    "TRACE_COORDINATE_MAPPING_PASS": (
        "the coordinates readers actually produced land on the same ink "
        "on the original page, for every locatable accepted trace"),
}
MAPPING_TESTS_DO_NOT_PROVE = (
    "SEMANTIC_ACCURACY", "GEOMETRY_CORRECTNESS", "MEASUREMENT_CORRECTNESS",
)
WHY_THAT_MATTERS = (
    "a trace can map perfectly to ink and still identify the wrong "
    "architectural object. 'Trace accuracy' is never used to mean both")

TRACE_SCHEMA = {
    "IDENTITY": list(P.TRACE_FIELDS),
    "GEOMETRY_ONE_OF": list(P.TRACE_GEOMETRY_FIELDS),
    "TRANSFORM": P.TRACE_TRANSFORM_FIELD,
    "CLAIM_TYPES": list(CLAIM_TYPES),
    "CLAIM_TYPES_ADDED_AT_HARDENING": list(ADDED_CLAIM_TYPES),
    "TRACE_STATUSES": list(P.TRACE_STATUSES),
    "TRACE_RECORD_STATUSES": list(TRACE_RECORD_STATUSES),
    "TRACE_LOCATABILITY_STATUSES": list(TRACE_LOCATABILITY_STATUSES),
    "CROSS_SHEET_RELATION_STATUSES": list(CROSS_SHEET_RELATION_STATUSES),
    "CONTRADICTION_STATUSES": list(CONTRADICTION_STATUSES),
    "CONTRADICTION_PROMOTION_REQUIRES": list(CONTRADICTION_PROMOTION_REQUIRES),
    "MAPPING_TESTS": MAPPING_TESTS,
    "MAPPING_TESTS_DO_NOT_PROVE": list(MAPPING_TESTS_DO_NOT_PROVE),
    "PRINTED_DIMENSION_FIELDS": list(P.PRINTED_DIMENSION_FIELDS),
    "LINKAGE": {
        "SUPPORTED_BY": (
            "a geometry trace names the PRINTED_DIMENSION trace that "
            "establishes its value. The dimension text and the thing it "
            "measures are two separate pieces of evidence"),
    },
    "TWO_STATUSES_NEVER_COLLAPSED": {
        "VISUAL_TRACE_STATUS": list(P.TRACE_STATUSES),
        "MEASUREMENT_STATUS": [
            "SOURCE_ESTABLISHED", "NOT_ESTABLISHED",
            "OWNER_PARAMETRIC", "PROVISIONAL_DEFAULT"],
        "WHY": P.VISUAL_TRACE_STATUS_IS_NOT_MEASUREMENT_STATUS,
    },
    "NO_NUMERIC_CONFIDENCE_SCORE_YET": P.NO_NUMERIC_CONFIDENCE_SCORE_YET,
}

REQUIRED_PER_TRACE = ("TRACE_ID", "CASE_ID", "CLAIM_TYPE", "SHEET_ID",
                      "VISUAL_TRACE_STATUS")

DIMENSION_CLAIM_TYPES = ("PRINTED_DIMENSION", "HEIGHT_DIMENSION")

# A dimension's geometry is not a generic PIXEL_* box - it is the text
# box plus the dimension line plus the two extension lines, which is
# exactly what PRINTED_DIMENSION_FIELDS specifies and what makes the
# dimension auditable at all. The first validator only accepted the
# generic fields and rejected 43 perfectly well-formed dimension traces.
DIMENSION_GEOMETRY_FIELDS = ("TEXT_BBOX", "DIMENSION_LINE_TRACE",
                             "EXTENSION_LINE_A", "EXTENSION_LINE_B")


def geometry_fields_for(claim_type: str) -> tuple:
    if claim_type in DIMENSION_CLAIM_TYPES:
        return tuple(P.TRACE_GEOMETRY_FIELDS) + DIMENSION_GEOMETRY_FIELDS
    return tuple(P.TRACE_GEOMETRY_FIELDS)


def locatability_status(t: dict) -> str:
    """Does the trace carry any geometry that can be drawn and projected?"""
    return ("LOCATABLE"
            if any(t.get(g) for g in geometry_fields_for(t.get("CLAIM_TYPE", "")))
            else "NOT_ESTABLISHED")


def record_status(t: dict, sheets: dict) -> tuple:
    """(VALID | INVALID, reasons). Well-formedness only - never semantics,
    and never locatability: a well-formed trace with no geometry is VALID
    and NOT_ESTABLISHED, which is a different thing from INVALID."""
    reasons = [r for r in validate_trace(t, sheets)
               if not r.startswith("no geometry")]
    return ("INVALID" if reasons else "VALID"), reasons


def effective_claim_type(t: dict) -> str:
    """The register's VIEW of a claim type. An UNRESOLVED_FEATURE that
    carries a RELATION is a vertical relation expressed before the type
    existed; it is viewed as one without the raw record changing."""
    ct = t.get("CLAIM_TYPE")
    if ct == "UNRESOLVED_FEATURE" and t.get("RELATION"):
        return "VERTICAL_RELATION"
    return ct


def validate_trace(t: dict, sheets: dict) -> list:
    """Every reason this trace is not usable. Empty list means usable."""
    bad = []
    for f in REQUIRED_PER_TRACE:
        if not t.get(f):
            bad.append(f"missing {f}")
    ct = t.get("CLAIM_TYPE")
    if ct and ct not in CLAIM_TYPES:
        bad.append(f"unknown CLAIM_TYPE {ct}")
    st = t.get("VISUAL_TRACE_STATUS")
    if st and st not in P.TRACE_STATUSES:
        bad.append(f"unknown VISUAL_TRACE_STATUS {st}")
    sid = t.get("SHEET_ID")
    if sid and sid not in sheets:
        bad.append(f"SHEET_ID {sid} is not in the sheet index")
    geom = [g for g in geometry_fields_for(ct) if t.get(g)]
    if not geom and st != "TRACE_NOT_ESTABLISHED":
        bad.append("no geometry, and the status is not TRACE_NOT_ESTABLISHED")
    # A running dimension CHAIN ("125 / 120 / 77 / 77 / 52") is a real
    # drawing construct and has no single VALUE_M. Only an ESTABLISHED
    # dimension must carry one; an ambiguous or unresolved dimension is
    # allowed to say so.
    if (ct in DIMENSION_CLAIM_TYPES and t.get("VALUE_M") is None
            and not t.get("VALUES_M")
            and st == "TRACE_ESTABLISHED"):
        bad.append("an ESTABLISHED dimension trace with no VALUE_M")
    if t.get("SUPPORTED_BY") and not isinstance(t["SUPPORTED_BY"], (str, list)):
        bad.append("SUPPORTED_BY must be a trace id or a list of them")
    return bad


# ==================================================================
# the transform
# ==================================================================

class SheetTransform:
    """Processed sheet pixels <-> original PDF page pixels, both ways."""

    def __init__(self, rec: dict):
        t = rec["ORIGINAL_PAGE_COORDINATE_TRANSFORM"]
        self.W = t["W_orig"]
        self.H = t["H_orig"]
        self.tx = t["trim_x0"]
        self.ty = t["trim_y0"]
        self.k = t["scale"]
        self.page = rec["ORIGINAL_PDF_PAGE"]
        self.sheet = rec["SHEET_ID"]

    def to_original(self, x, y):
        """processed px -> original page px."""
        xr = x / self.k + self.tx
        yr = y / self.k + self.ty
        return ((self.W - 1) - yr, xr)

    def to_processed(self, x, y):
        """original page px -> processed px."""
        xr = y
        yr = (self.W - 1) - x
        return ((xr - self.tx) * self.k, (yr - self.ty) * self.k)


def round_trip(n: int = 4000, seed: int = 7) -> dict:
    """Does the algebra invert, on every sheet, at sub-pixel error?"""
    idx = json.loads((OUT / "SHEET_INDEX.json").read_text("utf-8"))["SHEETS"]
    rng = random.Random(seed)
    out = {}
    for sid, rec in idx.items():
        tr = SheetTransform(rec)
        w, h = rec["FINAL_SIZE_PX"]
        worst = 0.0
        for _ in range(n):
            x, y = rng.uniform(0, w - 1), rng.uniform(0, h - 1)
            ox, oy = tr.to_original(x, y)
            bx, by = tr.to_processed(ox, oy)
            worst = max(worst, abs(bx - x), abs(by - y))
        out[sid] = {"points": n, "WORST_ABS_ERROR_PX": round(worst, 9),
                    "INVERTS": worst < 1e-6}
    return out


def ink_agreement(patch: int = 24, samples: int = 120, seed: int = 11) -> dict:
    """The test that matters: does a processed point land on the SAME INK
    in the original page? Algebra can invert perfectly and still point at
    the wrong part of the drawing."""
    import numpy as np
    idx = json.loads((OUT / "SHEET_INDEX.json").read_text("utf-8"))["SHEETS"]
    rng = random.Random(seed)
    out = {}
    for sid, rec in idx.items():
        tr = SheetTransform(rec)
        proc = np.asarray(Image.open(S.INDEX_BOX / rec["PREPARED_FILE"])
                          .convert("L"), dtype=float)
        orig = np.asarray(Image.open(S.PAGES / rec["ORIGINAL_PAGE_ID"])
                          .convert("L"), dtype=float)
        ph, pw = proc.shape
        # sample where there IS ink - blank paper would agree trivially
        ys, xs = np.where(proc < 150)
        if len(xs) == 0:
            continue
        picks = [rng.randrange(len(xs)) for _ in range(samples)]
        agree, checked = 0, 0
        deltas = []
        for i in picks:
            x, y = float(xs[i]), float(ys[i])
            ox, oy = tr.to_original(x, y)
            r = patch // 2
            if not (r < x < pw - r and r < y < ph - r):
                continue
            if not (r < ox < orig.shape[1] - r and r < oy < orig.shape[0] - r):
                continue
            pp = proc[int(y) - r:int(y) + r, int(x) - r:int(x) + r]
            # A patch of `patch` px on the PROCESSED sheet covers
            # patch/scale px on the original - about 80 px at scale 0.3.
            # Comparing two equally sized boxes would compare different
            # pieces of building, so the original box is taken at the
            # matching PHYSICAL size and then reduced to match.
            R = max(r, int(round(r / tr.k)))
            if not (R < ox < orig.shape[1] - R and R < oy < orig.shape[0] - R):
                continue
            ob = orig[int(oy) - R:int(oy) + R, int(ox) - R:int(ox) + R]
            # the original is rotated relative to the processed sheet:
            # undo the 90 CCW so the two patches are comparable
            ob = np.rot90(ob, k=-1)
            oo = np.asarray(Image.fromarray(ob.astype("uint8"))
                            .resize((2 * r, 2 * r), Image.LANCZOS),
                            dtype=float)
            checked += 1
            d = abs(pp.mean() - oo.mean())
            deltas.append(d)
            if d < 25.0:
                agree += 1
        out[sid] = {
            "SAMPLED_INK_POINTS": checked,
            "PATCH_PX": patch,
            "MEAN_ABS_INTENSITY_DELTA": round(float(np.mean(deltas)), 3),
            "AGREEING_WITHIN_25_LEVELS": agree,
            "AGREEMENT_RATE": round(agree / checked, 4) if checked else None,
        }
    return out


def trace_mapping_check(patch: int = 24) -> dict:
    """Criterion C on the REAL traces, not on random points.

    Every accepted trace has a representative point taken from its own
    stored geometry, projected to the original page, and the ink around
    it compared. Random points prove the transform; these prove that the
    coordinates a reader actually produced land where they claim to.
    """
    import numpy as np
    reg_path = OUT / "TRACE_REGISTER.json"
    if not reg_path.exists():
        return {"REGISTER_PRESENT": False}
    reg = json.loads(reg_path.read_text("utf-8"))
    idx = json.loads((OUT / "SHEET_INDEX.json").read_text("utf-8"))["SHEETS"]
    cache = {}

    def sheets(sid):
        if sid not in cache:
            rec = idx[sid]
            cache[sid] = (
                np.asarray(Image.open(S.INDEX_BOX / rec["PREPARED_FILE"])
                           .convert("L"), dtype=float),
                np.asarray(Image.open(S.PAGES / rec["ORIGINAL_PAGE_ID"])
                           .convert("L"), dtype=float),
                SheetTransform(rec))
        return cache[sid]

    def rep_point(t):
        for f in geometry_fields_for(t["CLAIM_TYPE"]):
            g = t.get(f)
            if not g:
                continue
            if f.endswith("_BBOX"):
                return ((g[0] + g[2]) / 2.0, (g[1] + g[3]) / 2.0)
            if f.endswith("_POINT"):
                return (g[0], g[1])
            mid = g[len(g) // 2]
            return (mid[0], mid[1])
        return None

    checked, agree, deltas, off = 0, 0, [], []
    for t in reg["TRACES"]:
        pt = rep_point(t)
        if pt is None:
            continue
        proc, orig, tr = sheets(t["SHEET_ID"])
        x, y = pt
        ox, oy = tr.to_original(x, y)
        r = patch // 2
        R = max(r, int(round(r / tr.k)))
        if not (r < x < proc.shape[1] - r and r < y < proc.shape[0] - r):
            off.append({"TRACE_ID": t["TRACE_ID"],
                        "WHY": "representative point falls outside the "
                               "processed sheet"})
            continue
        if not (R < ox < orig.shape[1] - R and R < oy < orig.shape[0] - R):
            off.append({"TRACE_ID": t["TRACE_ID"],
                        "WHY": "projected point falls outside the page"})
            continue
        pp = proc[int(y) - r:int(y) + r, int(x) - r:int(x) + r]
        ob = np.rot90(orig[int(oy) - R:int(oy) + R,
                           int(ox) - R:int(ox) + R], k=-1)
        oo = np.asarray(Image.fromarray(ob.astype("uint8"))
                        .resize((2 * r, 2 * r), Image.LANCZOS), dtype=float)
        d = abs(pp.mean() - oo.mean())
        deltas.append(d)
        checked += 1
        if d < 25.0:
            agree += 1
    return {
        "REGISTER_PRESENT": True,
        "TRACES_CHECKED": checked,
        "AGREEING_WITHIN_25_LEVELS": agree,
        "AGREEMENT_RATE": round(agree / checked, 4) if checked else None,
        "MEAN_ABS_INTENSITY_DELTA": (round(float(sum(deltas) / len(deltas)), 3)
                                     if deltas else None),
        "POINTS_OFF_SHEET": off,
    }


def mapping_test() -> dict:
    rt = round_trip()
    ink = ink_agreement()
    real = trace_mapping_check()
    body = {
        "PHASE_ID": P.PHASE_ID,
        "ARTIFACT": "ORIGINAL_SOURCE_MAPPING_TEST",
        "WHAT_IT_PROVES": (
            "a coordinate recorded on the processed sheet a reader saw can "
            "be projected back onto the original PDF page, through "
            "rotation, content trim and downscale"),
        "WHY_TWO_TESTS": (
            "round_trip checks the algebra inverts. ink_agreement checks "
            "the pixels: a transform can invert perfectly and still land "
            "on the wrong part of the drawing, and only the second test "
            "would catch that"),
        "ROUND_TRIP": rt,
        "ALL_SHEETS_INVERT": all(v["INVERTS"] for v in rt.values()),
        "INK_AGREEMENT": ink,
        "REAL_TRACE_MAPPING": real,
        "WHY_A_THIRD_TEST": (
            "random points prove the transform. The third test projects "
            "the coordinates READERS ACTUALLY PRODUCED and checks the ink "
            "there, which is what criterion C is really asking"),
        "SHEETS_TESTED": len(rt),
        "THE_TRANSFORM_IS_STORED_PER_SHEET_NOT_GLOBALLY": (
            "each sheet carries its own W_orig, trim origin and scale, so "
            "a trace stays valid even if another sheet is re-prepared"),
    }
    p = OUT / "ORIGINAL_SOURCE_MAPPING_TEST.json"
    p.write_text(json.dumps(body, indent=2, ensure_ascii=False) + "\n",
                 encoding="utf-8")
    return {"SHA256": hashlib.sha256(p.read_bytes()).hexdigest(),
            "ALL_SHEETS_INVERT": body["ALL_SHEETS_INVERT"],
            "WORST_ROUND_TRIP_PX": max(v["WORST_ABS_ERROR_PX"]
                                       for v in rt.values()),
            "INK_AGREEMENT_RATES": {k: v["AGREEMENT_RATE"]
                                    for k, v in ink.items()},
            "REAL_TRACE_MAPPING": real}


def write_schema() -> str:
    p = OUT / "VISUAL_TRACE_SCHEMA.json"
    p.write_text(json.dumps({
        "PHASE_ID": P.PHASE_ID,
        "ARTIFACT": "VISUAL_TRACE_SCHEMA",
        "SCHEMA": TRACE_SCHEMA,
        "REQUIRED_PER_TRACE": list(REQUIRED_PER_TRACE),
        "DIMENSION_AND_OBJECT_ARE_SEPARATE_EVIDENCE":
            P.DIMENSION_AND_OBJECT_ARE_SEPARATE_EVIDENCE,
        "THE_TRACE_MUST_SURVIVE": list(P.THE_TRACE_MUST_SURVIVE),
        "OVERLAY_RULES": list(P.OVERLAY_RULES),
    }, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return hashlib.sha256(p.read_bytes()).hexdigest()


if __name__ == "__main__":
    print(json.dumps({"VISUAL_TRACE_SCHEMA_SHA256": write_schema(),
                      "MAPPING_TEST": mapping_test()}, indent=2))
