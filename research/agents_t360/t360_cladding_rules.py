"""T-360 rules: facade cladding / stone (BOQ family B4-11), research only (PROPOSED; scope every villa; provenance T-360).

A facade cladding is a layer (stone, tile, GRC, composite panel ...) that replaces or covers the plaster / Sigma / paint
system on an exterior face, between a bottom and a top level, with its own returns at reveals. It is a quantity only when
a printed source names it.

R-T360-1  SOURCE. The material of a cladding face comes only from a printed legend, a hatch that a legend or note on the
          same set names, a text note, a specification line or an owner rule. A render, a photo, a hatch without a
          legend, a 'typical' material or a default is refused as a source of material (design intent / drafting only).
R-T360-2  GRAPHIC FORM WITHOUT MATERIAL. Drawn unit outlines (voussoirs, quoins, coursed blocks) without a legend mark
          an ELEMENT (its geometry may be measured) but not its material: the element is HELD by name, never a stone
          line and never 0. Section-cut hatches (cut concrete / slab bands) and ground hatches are not finishes.
R-T360-3  CURVED-FACE SHADING. A field of parallel lines whose spacing changes monotonically and symmetrically toward a
          silhouette (equal angular steps of a cylinder, spacing ~ cos) is the projection of a curved face, not a
          material hatch.
R-T360-4  ONE FACE ONE FINISH. A face (or a part of a face between two levels) carries one finish line: if a cladding
          is established on it, the plaster / Sigma / paint / spatter-dash on the same part is named as REPLACED (not
          applied here: integration decides); a part quantified in both is refused.
R-T360-5  OPENINGS once, by id, inside the cladding band only; HELD = None (blank) or a (lo, hi) range, never 0.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

DC = "DRAWING-CONFIRMED"
HELD = "HELD"
UNKNOWN = "UNKNOWN"
OA = "ASSUMED — OWNER-APPROVED"

MATERIAL_SOURCES = ("PRINTED_LEGEND", "LEGEND_NAMED_HATCH", "TEXT_NOTE", "SPECIFICATION", "OWNER_RULE")
REFUSED_SOURCES = ("RENDER", "PHOTO", "UNNAMED_HATCH", "TYPICAL", "DEFAULT", "FREELANCER")
NOT_FINISH_HATCH_KINDS = ("SECTION_CUT", "GROUND")


class RefusedSource(ValueError):
    pass


class DoubleCount(ValueError):
    pass


@dataclass(frozen=True)
class Mark:
    """What a sheet shows on a face: kind in MATERIAL_SOURCES / REFUSED_SOURCES / 'GRAPHIC_FORM' / hatch kinds."""
    kind: str
    material: str | None = None
    ref: str = ""


@dataclass(frozen=True)
class Opening:
    oid: str
    width: float
    sill: float
    head: float | None  # None = head not established (HELD)


@dataclass
class Face:
    key: str
    length: float
    bottom: float
    top: float
    openings: tuple = ()
    marks: tuple = ()
    plaster_line: str | None = None  # the exterior plaster / Sigma line that carries the face today
    extra: dict = field(default_factory=dict)


def material_of(marks):
    """R-T360-1 / -2: (state, material, source refs). Refused sources raise; form-only marks HOLD by name."""
    named = []
    form = []
    for m in marks:
        if m.kind in REFUSED_SOURCES:
            raise RefusedSource(f"{m.kind} is not a source of a cladding material ({m.ref})")
        if m.kind in MATERIAL_SOURCES:
            if not m.material:
                raise RefusedSource(f"{m.kind} without a named material ({m.ref})")
            named.append(m)
        elif m.kind == "GRAPHIC_FORM":
            form.append(m)
        elif m.kind in NOT_FINISH_HATCH_KINDS:
            continue
        else:
            raise ValueError(f"unknown mark kind {m.kind}")
    mats = sorted({m.material for m in named})
    if len(mats) > 1:
        return "CONFLICT", None, tuple(m.ref for m in named)
    if mats:
        return "MARKED_MATERIAL", mats[0], tuple(m.ref for m in named)
    if form:
        return "MARKED_FORM_MATERIAL_HELD", None, tuple(m.ref for m in form)
    return "NOT_MARKED", None, ()


def band_overlap(op: Opening, bottom: float, top: float):
    """Height of an opening inside [bottom, top]; None when the head is not established."""
    if op.head is None:
        return None
    return max(0.0, min(op.head, top) - max(op.sill, bottom))


def cladding_net(face: Face, bottom: float, top: float):
    """R-T360-5: (gross, deduction, net) m2 of a cladding band on one face; openings once by id; HELD -> net None."""
    if not (face.bottom - 1e-9 <= bottom < top <= face.top + 1e-9):
        raise ValueError(f"{face.key}: band {bottom} .. {top} leaves the face {face.bottom} .. {face.top}")
    seen = set()
    gross = round(face.length * (top - bottom), 6)
    ded = 0.0
    held = False
    for op in face.openings:
        if op.oid in seen:
            raise DoubleCount(f"opening {op.oid} deducted twice on {face.key}")
        seen.add(op.oid)
        h = band_overlap(op, bottom, top)
        if h is None:
            held = True
            continue
        ded += op.width * h
    ded = round(ded, 6)
    return gross, ded, (None if held else round(gross - ded, 6))


def face_state(face: Face):
    """One B4-11 row for a face: state, material, refs, cladding m2 (None unless a material AND a band are printed),
    and the finish line the cladding would replace (named, not applied)."""
    state, mat, refs = material_of(face.marks)
    row = dict(key=face.key, state=state, material=mat, refs=";".join(refs), cladding_m2=None,
               replaces=None, status=None)
    if state == "NOT_MARKED":
        row["status"] = "NOT IN DRAWN SCOPE"
    elif state == "MARKED_MATERIAL":
        band = face.extra.get("band")
        if band is None:
            row["status"] = HELD  # material named, extent not printed
        else:
            g, d, n = cladding_net(face, *band)
            row["cladding_m2"] = n
            row["status"] = DC if n is not None else HELD
        row["replaces"] = face.plaster_line
    else:  # form only or conflict
        row["status"] = HELD
        row["replaces"] = face.plaster_line
    return row


def check_no_double_count(rows, plaster_parts):
    """R-T360-4: a (face key, bottom, top) part quantified in a cladding row AND in a plaster / Sigma part is refused.
    plaster_parts: {(key, bottom, top): m2 or None}; rows carry 'key', 'band' and 'cladding_m2'."""
    hits = []
    for r in rows:
        if r.get("cladding_m2") is None or r.get("band") is None:
            continue
        b0, b1 = r["band"]
        for (k, p0, p1), m2 in plaster_parts.items():
            if k == r["key"] and m2 is not None and min(b1, p1) - max(b0, p0) > 1e-9:
                hits.append((k, b0, b1, p0, p1))
    if hits:
        raise DoubleCount(f"face part in a cladding line and a plaster / Sigma line: {hits}")
    return 0.0


def is_curved_face_shading(xs, tol=0.15):
    """R-T360-3: positions of parallel lines across a field. True when the spacing grows (or shrinks) monotonically
    toward one side and the positions fit a cosine of equal angular steps (a cylinder seen from the side);
    a uniform or irregular spacing returns False."""
    xs = sorted(xs)
    if len(xs) < 4:
        return False
    gaps = [b - a for a, b in zip(xs, xs[1:])]
    inc = all(g2 > g1 for g1, g2 in zip(gaps, gaps[1:]))
    dec = all(g2 < g1 for g1, g2 in zip(gaps, gaps[1:]))
    if not (inc or dec):
        return False
    if max(gaps) / min(gaps) < 1.3:
        return False
    # Fit x_i = c + r*sin(theta0 + i*dt) by scanning dt; accept a close fit.
    n = len(xs)
    best = math.inf
    for k in range(1, 400):
        dt = k * (math.pi / 2) / (400 * max(1, n - 1)) * 2
        for j in range(0, 60):
            t0 = -math.pi / 2 + j * (math.pi / 60)
            s = [math.sin(t0 + i * dt) for i in range(n)]
            ms, mx = sum(s) / n, sum(xs) / n
            den = sum((v - ms) ** 2 for v in s)
            if den < 1e-12:
                continue
            r = sum((v - ms) * (x - mx) for v, x in zip(s, xs)) / den
            c = mx - r * ms
            res = max(abs(c + r * v - x) for v, x in zip(s, xs))
            best = min(best, res / (xs[-1] - xs[0]))
    return best < tol / 10


def hatch_kind(pattern: str, role: str):
    """R-T360-2: a hatch's role in an elevation: 'SECTION_CUT' (a cut element band), 'GROUND' (earth below the
    ground line) or 'UNNAMED_HATCH' (on a face, no legend). Only a legend or note can turn a hatch into a material."""
    if role in ("section_cut", "cut"):
        return "SECTION_CUT"
    if role == "ground":
        return "GROUND"
    return "UNNAMED_HATCH"
