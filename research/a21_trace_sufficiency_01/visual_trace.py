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

TRACE_SCHEMA = {
    "IDENTITY": list(P.TRACE_FIELDS),
    "GEOMETRY_ONE_OF": list(P.TRACE_GEOMETRY_FIELDS),
    "TRANSFORM": P.TRACE_TRANSFORM_FIELD,
    "CLAIM_TYPES": list(P.CLAIM_TYPES),
    "TRACE_STATUSES": list(P.TRACE_STATUSES),
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


def validate_trace(t: dict, sheets: dict) -> list:
    """Every reason this trace is not usable. Empty list means usable."""
    bad = []
    for f in REQUIRED_PER_TRACE:
        if not t.get(f):
            bad.append(f"missing {f}")
    ct = t.get("CLAIM_TYPE")
    if ct and ct not in P.CLAIM_TYPES:
        bad.append(f"unknown CLAIM_TYPE {ct}")
    st = t.get("VISUAL_TRACE_STATUS")
    if st and st not in P.TRACE_STATUSES:
        bad.append(f"unknown VISUAL_TRACE_STATUS {st}")
    sid = t.get("SHEET_ID")
    if sid and sid not in sheets:
        bad.append(f"SHEET_ID {sid} is not in the sheet index")
    geom = [g for g in P.TRACE_GEOMETRY_FIELDS if t.get(g)]
    if not geom and st != "TRACE_NOT_ESTABLISHED":
        bad.append("no geometry, and the status is not TRACE_NOT_ESTABLISHED")
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


def mapping_test() -> dict:
    rt = round_trip()
    ink = ink_agreement()
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
                                    for k, v in ink.items()}}


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
