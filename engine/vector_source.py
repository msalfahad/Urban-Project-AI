"""E41 — the VECTOR_PATH layer, between the PDF and any wall hypothesis.

We were flattening a drawing into a bag of line segments and throwing away
everything that said where each segment came from. The review asked whether
that destroyed information, and on AR-00 the answer is: it destroyed the wrong
information. Not path continuity — the wall lines turn out to be one item per
path, so nothing was fragmented — but the SOURCE PROPERTIES that tell one
population of marks from another.

WHAT THE SHEET ACTUALLY CONTAINS (measured, not assumed):

    19,257 paths, 76,340 items
    9,059 FILL paths      glyph outlines, hatches  -> 45,378 line items
    10,198 STROKE paths   drawn linework           -> 28,338 line items

    stroke pen weights, axis-aligned items and their total length:
      1.14 pt     458 items      583.5 m     202 over 1 m, only 5 under 100 mm
      0.36 pt  12,572 items      617.5 m   11,005 under 50 mm
      0.30 pt   1,573 items      508.4 m
      0.24 pt     185 items      185.6 m
      0.12 pt     786 items      121.3 m

THE DISCIPLINE THIS MODULE IS UNDER. A 1.14 pt pen is not a wall. It is a
SOURCE PROPERTY of the mark, in exactly the way `source_object_id` is, and it is
kept for the same reason: so that a later stage can use it as evidence. This
module classifies nothing as a wall, excludes no band, and deletes nothing. It
records what the drawing says about each mark and hands the whole population on.

    DO NOT PROMOTE A PROXY INTO PHYSICAL TRUTH.

    heavy pen              is not   "a wall"
    hairline pen           is not   "not a wall"
    a short segment        is not   "noise"
    a fill path            is not   "text"
"""

from __future__ import annotations

import math
from collections import Counter
from dataclasses import dataclass, field

# How the mark was painted. A PDF says this directly; it is not inferred.
STROKE = "STROKE"
FILL = "FILL"

# Direction, in the drawing's own frame. DIAGONAL is kept, never discarded:
# a plan with a rotated wing must not lose it to an orthogonal detector.
AXIS_H = "H"
AXIS_V = "V"
AXIS_DIAGONAL = "DIAGONAL"
AXIS_DEGENERATE = "DEGENERATE"

# Item kinds we do not linearise. Recorded so the count is auditable rather
# than silently missing.
CURVE = "CURVE"
QUAD = "QUAD"

# A segment is axis-aligned when its off-axis extent is below this. Plotted CAD
# output is exact; this catches float noise, not slanted walls.
AXIS_TOL_PT = 0.05

# The sheet's own plotted scale.
MM_PER_PT = 45.0542


class VectorSourceError(RuntimeError):
    """The drawing could not be read without losing something unrecorded."""


@dataclass(frozen=True)
class VectorPath:
    """One path as the PDF drew it, with the properties that identify it."""

    path_id: str
    seqno: int
    path_type: str                 # STROKE or FILL
    stroke_width_pt: float
    colour: tuple
    dashes: str
    item_count: int
    bbox_pt: tuple

    @property
    def is_dashed(self) -> bool:
        """A PDF writes a solid stroke as '[] 0'. Anything else is a pattern."""
        d = (self.dashes or "").strip()
        return bool(d) and d not in ("[] 0", "None")

    def record(self) -> dict:
        return {"path_id": self.path_id, "seqno": self.seqno,
                "path_type": self.path_type,
                "stroke_width_pt": self.stroke_width_pt,
                "dashes": self.dashes, "is_dashed": self.is_dashed,
                "item_count": self.item_count}


@dataclass(frozen=True)
class VectorSegment:
    """One straight mark, and everything the drawing knows about where it came
    from. `axis`, `fixed_mm`, `start_mm` and `end_mm` are the wall engine's
    line form; the rest is provenance it must be able to ask about later."""

    segment_id: str
    path_id: str
    subpath_index: int
    axis: str
    fixed_mm: float
    start_mm: float
    end_mm: float
    path_type: str
    stroke_width_pt: float
    is_dashed: bool
    angle_deg: float = 0.0
    x0_mm: float = 0.0
    y0_mm: float = 0.0
    x1_mm: float = 0.0
    y1_mm: float = 0.0

    @property
    def length_mm(self) -> float:
        return math.hypot(self.x1_mm - self.x0_mm, self.y1_mm - self.y0_mm)

    @property
    def is_axis_aligned(self) -> bool:
        return self.axis in (AXIS_H, AXIS_V)

    def as_line(self) -> tuple[str, float, float, float]:
        """The 4-tuple the topology engine takes. Axis-aligned only."""
        if not self.is_axis_aligned:
            raise VectorSourceError(
                f"{self.segment_id} is {self.axis}; the wall-pair engine is "
                "axis-aligned and must be told so explicitly rather than "
                "silently handed a diagonal it will mis-read")
        return (self.axis, self.fixed_mm, self.start_mm, self.end_mm)

    def record(self) -> dict:
        return {"segment_id": self.segment_id, "path_id": self.path_id,
                "axis": self.axis, "length_mm": round(self.length_mm, 1),
                "path_type": self.path_type,
                "stroke_width_pt": self.stroke_width_pt,
                "is_dashed": self.is_dashed,
                "angle_deg": round(self.angle_deg, 1)}


@dataclass
class VectorDrawing:
    """Everything the PDF page contains, with nothing dropped."""

    paths: list[VectorPath] = field(default_factory=list)
    segments: list[VectorSegment] = field(default_factory=list)
    skipped: dict = field(default_factory=dict)
    page_rotation: int = 0

    def by_path(self) -> dict[str, VectorPath]:
        return {p.path_id: p for p in self.paths}

    def axis_aligned(self) -> list[VectorSegment]:
        return [s for s in self.segments if s.is_axis_aligned]

    def population_bands(self) -> list[dict]:
        """Every population in the drawing, EXCLUDING NONE.

        This is the table a reviewer reads before anyone filters anything. A
        band left out of it is a band quietly declared not-a-wall.
        """
        acc: dict[tuple, dict] = {}
        for s in self.segments:
            key = (s.path_type, round(s.stroke_width_pt, 2), s.axis)
            a = acc.setdefault(key, {
                "path_type": key[0], "stroke_width_pt": key[1], "axis": key[2],
                "segments": 0, "total_length_m": 0.0, "paths": set(),
                "under_50mm": 0, "over_1000mm": 0, "dashed": 0})
            a["segments"] += 1
            a["total_length_m"] += s.length_mm / 1000
            a["paths"].add(s.path_id)
            if s.length_mm < 50:
                a["under_50mm"] += 1
            if s.length_mm >= 1000:
                a["over_1000mm"] += 1
            if s.is_dashed:
                a["dashed"] += 1
        out = []
        for a in acc.values():
            a = dict(a)
            a["paths"] = len(a["paths"])
            a["total_length_m"] = round(a["total_length_m"], 1)
            a["mean_length_mm"] = round(
                a["total_length_m"] * 1000 / a["segments"], 1)
            out.append(a)
        out.sort(key=lambda a: -a["total_length_m"])
        return out

    def angle_bands(self) -> dict[str, int]:
        """Is this drawing orthogonal? Answered, not assumed.

        A plan with a rotated wing shows real length at a non-orthogonal angle.
        One that shows only scattered short marks off-axis has curve
        flattening, not rotated architecture.
        """
        acc: dict[str, list] = {}
        for s in self.segments:
            if s.axis == AXIS_DEGENERATE:
                continue
            a = s.angle_deg
            key = ("0" if s.axis == AXIS_H else "90" if s.axis == AXIS_V
                   else f"{int(round(a / 5) * 5)}")
            acc.setdefault(key, [0, 0.0])
            acc[key][0] += 1
            acc[key][1] += s.length_mm / 1000
        return {k: {"segments": v[0], "total_length_m": round(v[1], 1)}
                for k, v in sorted(acc.items(), key=lambda kv: -kv[1][1])}

    def path_fragmentation(self) -> dict:
        """Did flattening break architectural paths into pieces?

        The review's hypothesis, and on AR-00 it is FALSE for the wall
        population: a heavy-pen path holds exactly one item. Reported as a
        measurement either way, because on another drawing it may be true.
        """
        per_path = Counter(s.path_id for s in self.segments)
        long_paths = {s.path_id for s in self.segments if s.length_mm >= 300}
        short_segs = [s for s in self.segments if s.length_mm < 50]
        return {
            "paths_with_segments": len(per_path),
            "items_per_path": dict(Counter(per_path.values()).most_common(8)),
            "short_segments": len(short_segs),
            "short_in_a_path_that_also_has_a_long_run": sum(
                1 for s in short_segs if s.path_id in long_paths),
            "short_in_a_path_with_no_long_run": sum(
                1 for s in short_segs if s.path_id not in long_paths),
        }


def _angle(dx: float, dy: float) -> float:
    a = math.degrees(math.atan2(abs(dy), abs(dx)))
    return min(a, 180 - a)


def read(path: str, page: int = 0, *, mm_per_pt: float = MM_PER_PT
         ) -> VectorDrawing:
    """Read every mark on the page. Nothing is filtered and nothing is judged.

    Rectangles become their four sides: a wall face drawn as a thin filled
    rectangle is two faces and two ends, and dropping it loses a wall the
    architect drew. Curves are counted, not linearised — a flattened curve is a
    different object from a drawn line and should not enter the same pool
    pretending otherwise.
    """
    import pymupdf

    doc = pymupdf.open(path)
    pg = doc[page]
    out = VectorDrawing(page_rotation=pg.rotation)
    skipped: Counter = Counter()
    n = 0

    for i, d in enumerate(pg.get_drawings()):
        ptype = STROKE if d.get("type") == "s" else FILL
        width = float(d.get("width") or 0.0)
        rect = d.get("rect")
        vp = VectorPath(
            path_id=f"VP-{i:06d}", seqno=int(d.get("seqno", i)),
            path_type=ptype, stroke_width_pt=round(width, 2),
            colour=tuple(d.get("color") or ()), dashes=str(d.get("dashes")),
            item_count=len(d["items"]),
            bbox_pt=(rect.x0, rect.y0, rect.x1, rect.y1) if rect else ())
        out.paths.append(vp)

        def add(sub, x0, y0, x1, y1):
            nonlocal n
            dx, dy = x1 - x0, y1 - y0
            if abs(dx) <= AXIS_TOL_PT and abs(dy) <= AXIS_TOL_PT:
                skipped[AXIS_DEGENERATE] += 1
                axis = AXIS_DEGENERATE
            elif abs(dy) <= AXIS_TOL_PT:
                axis = AXIS_H
            elif abs(dx) <= AXIS_TOL_PT:
                axis = AXIS_V
            else:
                axis = AXIS_DIAGONAL
            if axis == AXIS_DEGENERATE:
                return
            n += 1
            if axis == AXIS_H:
                fixed, a, b = y0 * mm_per_pt, min(x0, x1) * mm_per_pt, max(x0, x1) * mm_per_pt
            elif axis == AXIS_V:
                fixed, a, b = x0 * mm_per_pt, min(y0, y1) * mm_per_pt, max(y0, y1) * mm_per_pt
            else:
                fixed, a, b = 0.0, 0.0, 0.0
            out.segments.append(VectorSegment(
                segment_id=f"VS-{n:06d}", path_id=vp.path_id, subpath_index=sub,
                axis=axis, fixed_mm=fixed, start_mm=a, end_mm=b,
                path_type=ptype, stroke_width_pt=vp.stroke_width_pt,
                is_dashed=vp.is_dashed, angle_deg=_angle(dx, dy),
                x0_mm=x0 * mm_per_pt, y0_mm=y0 * mm_per_pt,
                x1_mm=x1 * mm_per_pt, y1_mm=y1 * mm_per_pt))

        for j, item in enumerate(d["items"]):
            kind = item[0]
            if kind == "l":
                (x0, y0), (x1, y1) = item[1], item[2]
                add(j, x0, y0, x1, y1)
            elif kind == "re":
                r = item[1]
                add(j, r.x0, r.y0, r.x1, r.y0)
                add(j, r.x0, r.y1, r.x1, r.y1)
                add(j, r.x0, r.y0, r.x0, r.y1)
                add(j, r.x1, r.y0, r.x1, r.y1)
            elif kind == "c":
                skipped[CURVE] += 1
            elif kind == "qu":
                skipped[QUAD] += 1
            else:
                skipped[f"UNHANDLED_{kind}"] += 1

    out.skipped = dict(skipped)
    return out
