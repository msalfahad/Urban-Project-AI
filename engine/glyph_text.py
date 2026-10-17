"""E88 — find the text on a drawing that has no text objects.

AR-00 contains ZERO PDF text objects. Every room name, every printed
dimension and every door tag on it is a set of vector outlines: the letters
were exploded to curves by the plotter. A naive extractor reports "this
drawing has no text", and a drawing whose room names are vector outlines is
not a drawing without room names.

So the text is found GEOMETRICALLY. This module clusters the small strokes
into glyph-sized marks, then groups those into text runs, and reports where
each run is and how big it is. It does NOT claim to know what any run says:
`raw_text` is empty here, and filling it is the reader's job (a vision pass,
a human, or a future CAD source).

That split is deliberate. The localiser is deterministic and reproducible
with no model and no network; only the transcription needs either. If the
reader is unavailable, the pipeline still knows where the labels are and
says so, instead of pretending the sheet is blank.
"""

from __future__ import annotations

import hashlib
from collections import Counter
from dataclasses import dataclass, field

# A glyph on a 1:100 architectural sheet is 2-3 mm of PAPER, which at this
# project's 45.05 mm/pt drawing scale is a few points. Anything much bigger
# is a wall, a hatch or a leader line, not a letter.
MAX_GLYPH_PT = 12.0
# Both dimensions must exceed this. It is the discriminator that matters: a
# wall, a dimension line and a leader are axis-aligned marks with ZERO
# thickness, while a letter is a closed outline with real width AND height.
# Without it, every wall segment near a label came back as a glyph.
MIN_GLYPH_PT = 0.3
# Marks this far apart (in points) belong to different runs. A CLUSTERING
# parameter, not a physical constant: it decides how aggressively separate
# strings are joined, and `sensitivity()` below records how the run count
# moves with it so the choice can be argued with rather than trusted. At 6 pt
# a label, its two dimensions and the wall between them merged into one run,
# which destroys the per-string anchor; at 2 pt they stay separate.
RUN_GAP_PT = 2.0
# A run needs this many marks to be text rather than a stray tick.
MIN_MARKS_PER_RUN = 2

# A glyph on this sheet is a BLACK FILLED path. Measured, not assumed:
# the letters come back as fill=(0,0,0) type 'f', the dimension arrowheads
# as fill=(0.541,0,0), and the dimension and extension lines as grey
# strokes. Without this test a cluster of red arrowheads scored as a
# LABEL_LIKE run and was sent to the reader, which correctly answered "no
# text" — after paying for the crop.
MAX_INK_CHANNEL = 0.25

ORIENT_H = "HORIZONTAL"
ORIENT_V = "VERTICAL"

# What a run might be, from its SHAPE alone. A guess about form, never
# about content: a wide short run beside a wall looks like a dimension and
# could equally be a note.
FORM_DIMENSION_LIKE = "DIMENSION_LIKE_RUN"
FORM_LABEL_LIKE = "LABEL_LIKE_RUN"
FORM_TAG_LIKE = "TAG_LIKE_RUN"
FORM_BLOCK_LIKE = "TEXT_BLOCK_LIKE_RUN"


@dataclass(frozen=True)
class TextRun:
    """A cluster of glyph-sized marks: text, somewhere, of some size."""

    run_id: str
    bbox_pt: tuple
    bbox_mm: tuple
    centre_mm: tuple
    marks: int
    glyph_height_pt: float
    orientation: str
    form_guess: str
    curved_marks: int = 0
    page: int = 0

    @property
    def width_pt(self) -> float:
        return self.bbox_pt[2] - self.bbox_pt[0]

    @property
    def height_pt(self) -> float:
        return self.bbox_pt[3] - self.bbox_pt[1]

    def crop_pt(self, pad: float = 3.0) -> tuple:
        """The page rectangle to render when something wants to READ this."""
        x0, y0, x1, y1 = self.bbox_pt
        return (x0 - pad, y0 - pad, x1 + pad, y1 + pad)

    def record(self) -> dict:
        return {
            "run_id": self.run_id,
            "page": self.page,
            "bbox_pt": [round(v, 2) for v in self.bbox_pt],
            "bbox_mm": [round(v, 1) for v in self.bbox_mm],
            "anchor_mm": [round(v, 1) for v in self.centre_mm],
            "marks": self.marks,
            "curved_marks": self.curved_marks,
            "glyph_height_pt": round(self.glyph_height_pt, 2),
            "orientation": self.orientation,
            "form_guess": self.form_guess,
            "raw_text": "",
            "text_status": "LOCATED_NOT_READ",
            "why_no_text": (
                "this sheet has no PDF text objects: the run is a cluster of "
                "vector outlines. Where it is and how big it is are "
                "measured; what it SAYS needs a reader"),
        }


@dataclass
class Report:
    runs: list = field(default_factory=list)
    notes: dict = field(default_factory=dict)

    @property
    def output_hash(self) -> str:
        payload = "|".join(
            f"{r.run_id}:{r.marks}:{r.bbox_pt[0]:.1f},{r.bbox_pt[1]:.1f}"
            for r in self.runs)
        return hashlib.sha256(payload.encode()).hexdigest()[:24]

    def record(self, *, limit: int = 400) -> dict:
        return {
            "GLYPH_LOCALISER_OUTPUT_HASH": self.output_hash,
            "text_runs": len(self.runs),
            "by_form_guess": dict(Counter(r.form_guess for r in self.runs)),
            "by_orientation": dict(Counter(r.orientation for r in self.runs)),
            "runs": [r.record() for r in self.runs[:limit]],
            "pdf_text_objects": self.notes.get("pdf_text_objects", 0),
            "text_representation": (
                "VECTOR_GLYPH_OUTLINE" if not self.notes.get(
                    "pdf_text_objects") else "PDF_TEXT_OBJECT"),
            "what_this_establishes": (
                "WHERE text is and HOW BIG it is. Not what it says, and "
                "certainly not what it means: a run's form_guess is read "
                "off its shape, so a DIMENSION_LIKE_RUN is a wide short "
                "cluster and might be a note"),
            "what_this_may_not_do": (
                "supply a room identity, a dimension value or a released "
                "millimetre. A located run is a place to look"),
            "notes": dict(self.notes),
        }


def locate(path: str, page: int = 0, *, mm_per_pt: float = 45.0542,
           max_glyph_pt: float = MAX_GLYPH_PT,
           run_gap_pt: float = RUN_GAP_PT) -> Report:
    """Cluster a page's small vector marks into text runs."""
    import pymupdf

    doc = pymupdf.open(path)
    pg = doc[page]

    # If the page DOES have text objects, say so — this module is the
    # fallback for the case where it does not, and quietly running the
    # geometric path on a sheet with real text would be worse than useless.
    raw = pg.get_text("rawdict")
    text_objects = sum(1 for b in raw.get("blocks", ())
                       if b.get("type") == 0)

    boxes = []
    for d in pg.get_drawings():
        rect = d.get("rect")
        if rect is None:
            continue
        w, h = float(rect.x1 - rect.x0), float(rect.y1 - rect.y0)
        big, small = max(w, h), min(w, h)
        if big > max_glyph_pt or small < MIN_GLYPH_PT:
            continue
        if not _is_glyph_ink(d):
            continue
        curved = any(it[0] == "c" for it in d.get("items", ()))
        boxes.append((float(rect.x0), float(rect.y0),
                      float(rect.x1), float(rect.y1), curved))

    clusters = _cluster(boxes, run_gap_pt)

    runs, n = [], 0
    for cl in clusters:
        if len(cl) < MIN_MARKS_PER_RUN:
            continue
        n += 1
        x0 = min(b[0] for b in cl)
        y0 = min(b[1] for b in cl)
        x1 = max(b[2] for b in cl)
        y1 = max(b[3] for b in cl)
        glyph_h = sorted(b[3] - b[1] for b in cl)[len(cl) // 2]
        curved = sum(1 for b in cl if len(b) > 4 and b[4])
        w, h = x1 - x0, y1 - y0
        runs.append(TextRun(
            run_id=f"TR-{n:04d}", page=page,
            bbox_pt=(x0, y0, x1, y1),
            bbox_mm=(x0 * mm_per_pt, y0 * mm_per_pt,
                     x1 * mm_per_pt, y1 * mm_per_pt),
            centre_mm=((x0 + x1) / 2 * mm_per_pt,
                       (y0 + y1) / 2 * mm_per_pt),
            marks=len(cl), curved_marks=curved,
            glyph_height_pt=glyph_h,
            orientation=ORIENT_H if w >= h else ORIENT_V,
            form_guess=_form(w, h, glyph_h, len(cl))))

    return Report(runs=runs, notes={
        "pdf_text_objects": text_objects,
        "glyph_candidate_marks": len(boxes),
        "glyph_test": (
            "a BLACK FILLED path no larger than "
            f"{max_glyph_pt} pt in either direction, with both dimensions "
            f"above {MIN_GLYPH_PT} pt. Measured on this sheet: letters are "
            "fill=(0,0,0), dimension arrowheads are fill=(0.54,0,0) and "
            "dimension lines are grey strokes"),
        "clusters_before_min_marks": len(clusters),
        "max_glyph_pt": max_glyph_pt,
        "run_gap_pt": run_gap_pt,
        "mm_per_pt": mm_per_pt,
        "why_geometric": (
            "this page carries "
            f"{text_objects} PDF text objects. With none, every label is a "
            "vector outline and the only way to find text is its geometry"),
    })


def _is_glyph_ink(d) -> bool:
    """Is this mark black filled ink — a letter rather than a symbol?"""
    if d.get("type") != "f":
        return False
    fill = d.get("fill")
    if not fill:
        return False
    return all(float(c) <= MAX_INK_CHANNEL for c in fill)


def sensitivity(path: str, page: int = 0, *,
                gaps=(1.5, 2.0, 2.5, 3.0, 4.0, 6.0)) -> dict:
    """How the run count moves with the clustering gap.

    A tolerance nobody measured cannot be wrong (invariant 23). This does
    not pick the gap — it records what the choice costs, so a reader can
    see that 2 pt is a decision and what the alternatives produce.
    """
    rows = []
    for g in gaps:
        rep = locate(path, page, run_gap_pt=g)
        rows.append({
            "run_gap_pt": g,
            "runs": len(rep.runs),
            "largest_run_marks": max((r.marks for r in rep.runs),
                                     default=0),
        })
    return {
        "in_use_pt": RUN_GAP_PT,
        "rows": rows,
        "why_it_matters": (
            "too large and a room label, its dimensions and the wall "
            "between them become one run, which destroys the per-string "
            "anchor. Too small and one word breaks into letters"),
        "this_is_not": (
            "a physical constant of the drawing. It is a clustering choice "
            "for THIS sheet's glyph spacing"),
    }


def render_crop(path: str, run: TextRun, *, dpi: int = 900,
                pad_pt: float = 8.0) -> bytes:
    """Render one run as a PNG, for something that can actually READ it.

    The pad is generous on purpose: a run is one string, but an
    architectural label is often a stacked pair (Arabic over English) and a
    tight crop cut "BED ROOM" down to "BED I". Padding gives the reader the
    whole string; the run's ANCHOR is unchanged, so the observation still
    points at the text's own centre rather than at the padded box.

    The rotation matters and cost this a wrong turn: `get_drawings()` returns
    UNROTATED mediabox coordinates, while `get_pixmap(clip=...)` expects the
    page's rotated coordinates. On this 270-degree sheet the two differ, and
    clipping with the raw drawing rect renders blank paper. The page's own
    rotation matrix is the conversion.
    """
    import pymupdf

    doc = pymupdf.open(path)
    pg = doc[run.page]
    rect = pymupdf.Rect(*run.crop_pt(pad_pt)) * pg.rotation_matrix
    return pg.get_pixmap(clip=rect, dpi=dpi).tobytes("png")


def _form(w: float, h: float, glyph_h: float, marks: int) -> str:
    """What shape this run is. A guess about form, not about meaning."""
    long_side = max(w, h)
    short_side = max(min(w, h), 0.01)
    ratio = long_side / short_side
    if ratio >= 6.0 and marks >= 3:
        return FORM_DIMENSION_LIKE
    if short_side > glyph_h * 2.2:
        return FORM_BLOCK_LIKE
    if marks <= 4:
        return FORM_TAG_LIKE
    return FORM_LABEL_LIKE


def _cluster(boxes, gap: float) -> list:
    """Group marks whose boxes come within `gap` points of each other.

    Bucketed by cell so this stays linear rather than quadratic — a sheet
    has tens of thousands of glyph marks.
    """
    if not boxes:
        return []
    cell = max(gap, 0.5)
    grid: dict = {}
    for i, b in enumerate(boxes):
        for cy in range(int(b[1] // cell), int(b[3] // cell) + 1):
            for cx in range(int(b[0] // cell), int(b[2] // cell) + 1):
                grid.setdefault((cy, cx), []).append(i)

    seen, out = set(), []
    for i in range(len(boxes)):
        if i in seen:
            continue
        stack, group = [i], []
        seen.add(i)
        while stack:
            j = stack.pop()
            group.append(j)
            bj = boxes[j]
            for cy in range(int((bj[1] - gap) // cell),
                            int((bj[3] + gap) // cell) + 1):
                for cx in range(int((bj[0] - gap) // cell),
                                int((bj[2] + gap) // cell) + 1):
                    for k in grid.get((cy, cx), ()):
                        if k in seen:
                            continue
                        bk = boxes[k]
                        if (bk[0] - gap <= bj[2] and bk[2] + gap >= bj[0]
                                and bk[1] - gap <= bj[3]
                                and bk[3] + gap >= bj[1]):
                            seen.add(k)
                            stack.append(k)
        out.append([boxes[j] for j in group])
    return out
