"""Deterministic model-space REGION CANDIDATES (R8.4 §19-§20).

A candidate is NOT a designation. This module proposes where the separate drawings of one
model space are (spatial clusters of realised geometry) and what each might be (plan / detail /
section / elevation / unknown) from the labels and scale notes inside it. It never grants
measurement authority:

    candidate role PLAN          -> region kind MODEL_SPACE_PLAN (full-size convention is a
                                    DECLARATION: UNCONFIRMED, preview at most, until a
                                    ReferenceRegionDesignation is ACCEPTED)
    candidate role DETAIL        -> MODEL_SPACE_DETAIL  (U-2: BLOCKED without region evidence)
    SECTION / ELEVATION / UNKNOWN -> MODEL_SPACE_UNKNOWN (never inherits plan full-size authority)

Project-specific windows (a known plan rectangle) belong in project adapters, which may submit
them as PROJECT_ADAPTER_CLAIM designations for review; nothing project-specific lives here.

CLUSTERING. Realised geometry is sampled onto a square occupancy grid whose cell is a fixed
fraction of the robust (1st-99th percentile) extent — unit-free, the same rule for every source
— and 8-connected occupied cells form one candidate. The cell fraction is a candidate-generation
parameter only: a different value changes which candidates are proposed, never a status.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass, field

from . import frame as FR
from . import observations as O

PLAN, DETAIL, SECTION, ELEVATION, UNKNOWN = "PLAN", "DETAIL", "SECTION", "ELEVATION", "UNKNOWN"
ROLES = (PLAN, DETAIL, SECTION, ELEVATION, UNKNOWN)
# generic drawing-type vocabulary (English / Arabic), not project text
ROLE_WORDS = {
    PLAN: re.compile(r"(?i)\b(floor\s+plan|plan|layout)\b|مسقط|مخطط"),
    DETAIL: re.compile(r"(?i)\b(detail|det\.)\b|تفصيل|تفاصيل"),
    SECTION: re.compile(r"(?i)\b(section|sec\.)\b|قطاع|مقطع"),
    ELEVATION: re.compile(r"(?i)\b(elevation|elev\.?)\b|واجهة"),
}
SCALE_NOTE = re.compile(r"(?<![\d.])1\s*[:/]\s*(\d{1,5})(?![\d.])")
KIND_FOR_ROLE = {PLAN: FR.MODEL_SPACE_PLAN, DETAIL: FR.MODEL_SPACE_DETAIL, SECTION: FR.MODEL_SPACE_UNKNOWN,
                 ELEVATION: FR.MODEL_SPACE_UNKNOWN, UNKNOWN: FR.MODEL_SPACE_UNKNOWN}
CELL_FRACTION = 1.0 / 150.0
MIN_CELLS = 4


@dataclass(frozen=True)
class RegionCandidate:
    candidate_id: str
    coordinate_space_id: str
    bounds: tuple                       # native (xmin, ymin, xmax, ymax)
    role_candidate: str
    role_evidence: tuple = ()           # ((role, handle, literal), ...)
    scale_notes: tuple = ()             # ((denominator, handle, literal), ...)
    sample_count: int = 0
    review_status: str = FR.CANDIDATE
    producer: str = FR.ENGINE
    notes: str = ""

    @property
    def region_kind(self) -> str:
        return KIND_FOR_ROLE[self.role_candidate]

    def as_dict(self):
        d = dict(self.__dict__)
        d["region_kind_without_designation"] = self.region_kind
        d["role_evidence"] = [list(x) for x in self.role_evidence]
        d["scale_notes"] = [list(x) for x in self.scale_notes]
        return d


def _polylines(realised):
    for s in realised.segments:
        yield (s.a, s.b)
    for a in realised.arcs:
        yield (a.start, a.mid, a.end)
    for c in realised.circles:
        r = c.radius
        yield tuple((c.center[0] + r * math.cos(t * math.pi / 4), c.center[1] + r * math.sin(t * math.pi / 4))
                    for t in range(9))
    for e in realised.elliptical_arcs:
        yield (e.start, e.mid, e.end)


def _points(realised):
    for pl in _polylines(realised):
        yield from pl


def _sampled(realised, step):
    """Points along every primitive at most `step` apart (so a long wall line stays one cluster)."""
    for pl in _polylines(realised):
        for p, q in zip(pl, pl[1:]):
            n = min(max(1, math.ceil(math.hypot(q[0] - p[0], q[1] - p[1]) / step)), 4000)
            for i in range(n + 1):
                t = i / n
                yield (p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t)


def _pct(sorted_vals, q):
    if not sorted_vals:
        return 0.0
    i = min(len(sorted_vals) - 1, max(0, int(round(q * (len(sorted_vals) - 1)))))
    return sorted_vals[i]


def _texts(document):
    for o in document.entities:
        if o.kind in (O.TEXT, O.MTEXT) and isinstance(o.geometry, O.TextGeom) and o.geometry.value:
            yield o.source_handle, o.geometry.insertion, o.geometry.value


def candidates(document: O.SourceDocument, realised, space_id: str = "MODEL_SPACE",
               cell_fraction: float = CELL_FRACTION) -> dict:
    """{candidates: [RegionCandidate], parameters: {...}}. Deterministic: same input -> same ids."""
    pts = [p for p in _points(realised) if all(math.isfinite(v) for v in p[:2])]
    if not pts:
        return {"candidates": [], "parameters": {"cell": None, "cell_fraction": cell_fraction}}
    xs, ys = sorted(p[0] for p in pts), sorted(p[1] for p in pts)
    span = max(_pct(xs, 0.99) - _pct(xs, 0.01), _pct(ys, 0.99) - _pct(ys, 0.01), 1e-9)
    cell = span * cell_fraction
    occ = {}
    for p in _sampled(realised, cell * 0.5):
        if not all(math.isfinite(v) for v in p):
            continue
        k = (math.floor(p[0] / cell), math.floor(p[1] / cell))
        occ[k] = occ.get(k, 0) + 1
    parent = {k: k for k in occ}

    def find(k):
        while parent[k] != k:
            parent[k] = parent[parent[k]]
            k = parent[k]
        return k

    for (i, j) in occ:
        for di in (-1, 0, 1):
            for dj in (-1, 0, 1):
                n = (i + di, j + dj)
                if n in occ:
                    a, b = find((i, j)), find(n)
                    if a != b:
                        parent[max(a, b)] = min(a, b)
    comps = {}
    for k in occ:
        comps.setdefault(find(k), []).append(k)
    texts = list(_texts(document))
    out = []
    for cells in sorted(comps.values(), key=lambda c: (min(c), len(c))):
        if len(cells) < MIN_CELLS:
            continue
        xmin = min(c[0] for c in cells) * cell
        ymin = min(c[1] for c in cells) * cell
        xmax = (max(c[0] for c in cells) + 1) * cell
        ymax = (max(c[1] for c in cells) + 1) * cell
        cellset = set(cells)
        inside = [t for t in texts if (math.floor(t[1][0] / cell), math.floor(t[1][1] / cell)) in cellset
                  or (xmin <= t[1][0] <= xmax and ymin <= t[1][1] <= ymax)]
        role_ev, notes = [], []
        for h, _, v in inside:
            for role, rx in ROLE_WORDS.items():
                if rx.search(v):
                    role_ev.append((role, h, v.strip()[:60]))
            for m in SCALE_NOTE.finditer(v):
                notes.append((int(m.group(1)), h, v.strip()[:60]))
        roles = sorted({r for r, _, _ in role_ev})
        role = roles[0] if len(roles) == 1 else UNKNOWN
        why = ("no role label inside" if not roles else
               f"one role class labelled ({roles[0]})" if len(roles) == 1 else
               "several role classes labelled (" + ", ".join(roles) + "): not resolved")
        if len({n[0] for n in notes}) > 1:
            why += "; several scale notes"
        cid = f"RC:{space_id}:{round(xmin / cell)}:{round(ymin / cell)}:{len(cells)}"
        out.append(RegionCandidate(cid, space_id, (xmin, ymin, xmax, ymax), role, tuple(role_ev), tuple(notes),
                                   sum(occ[c] for c in cells), notes=why))
    return {"candidates": out, "parameters": {"cell": cell, "cell_fraction": cell_fraction, "robust_span": span,
                                              "min_cells": MIN_CELLS}}


def region_for(unit: FR.UnitContext, cand: RegionCandidate, designation: FR.ReferenceRegionDesignation | None = None,
               evidence=(), policy=None) -> FR.RegionMeasurementTransform:
    """The region transform a candidate supports. Only a PLAN candidate may carry a designation;
    without one it keeps the plan convention as a declaration (UNCONFIRMED at most)."""
    kind = cand.region_kind
    if designation is not None and kind != FR.MODEL_SPACE_PLAN:
        kind = FR.MODEL_SPACE_PLAN if designation.basis in (FR.HUMAN_DESIGNATION, FR.PROJECT_ADAPTER_CLAIM) else kind
    return FR.region_transform(unit, cand.candidate_id, kind, evidence, bounds=cand.bounds, policy=policy,
                               reference=designation is not None and kind == FR.MODEL_SPACE_PLAN,
                               designation=designation if kind == FR.MODEL_SPACE_PLAN else None)
