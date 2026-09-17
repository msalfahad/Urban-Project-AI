"""§13, §14. The pantry's applicable walls, from the design set.

The owner confirms the P7757 pantry is an OPEN AMERICAN PANTRY and that
its walls take FULL-WALL tile. Which walls those are is a question about
the installation, and the addendum names where the answer lives:

    water supply and drainage        the sanitary or plumbing set
    the sink position, if any        the sanitary set, or the plan
    the counter or cabinet run       the architectural plan's fittings
    the host walls                   the bands those fittings stand on
    the adjacency to the dining      the labels around it

So this module asks each of those questions and REPORTS THE ANSWER IT
GOT, including "nothing here answers this". It does not invent an L or a
U, and it does not take the perimeter of the open space the pantry sits
in — that perimeter belongs to the dining as much as to the pantry.

A SECOND DESIGN REPRESENTATION IS A REPRESENTATION THIS ENGINE CAN READ.
A sanitary set that exists on paper, or as a scan with no vector and no
text, is a set this module must say it could not read — not one it can
quietly proceed without.
"""

from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass

from engine import functional_zone as fz

MODEL = "PANTRY_HOST_WALLS_FROM_THE_DESIGN_SET_V1"

# How far from a pantry label another label still describes the space it
# opens onto. The functional-zone module's own reach for a fitting run,
# in metres of drawing: nothing new is chosen — SEARCH_MM is the largest
# room dimension this project has measured, so the search is generous
# and the ANSWER is what narrows it, never the radius.
SEARCH_MM = 12000.0

SANITARY_READ = "THE_SANITARY_SET_WAS_READ"
SANITARY_NOT_SUPPLIED = "NO_SANITARY_REPRESENTATION_WAS_SUPPLIED"
SANITARY_UNREADABLE = "THE_SANITARY_SET_SUPPLIED_CANNOT_BE_READ_BY_THIS_ENGINE"
WALLS_ESTABLISHED = "THE_APPLICABLE_PANTRY_WALLS_ARE_ESTABLISHED"
WALLS_NEED_REVIEW = fz.TILE_WALLS_NEED_REVIEW

EV_ADJACENT_OPEN_PLAN = "AN_OPEN_PLAN_LABEL_STANDS_BESIDE_IT"
EV_FITTING_RUN = "A_RUN_OF_FITTINGS_STANDS_NEAR_THE_LABEL"
EV_SANITARY_FIXTURE = "A_SANITARY_FIXTURE_STANDS_IN_THE_PANTRY"
EV_NO_SPACE = "NO_PHYSICAL_SPACE_CARRIES_THIS_PANTRY_LABEL"


def model_hash() -> str:
    parts = [MODEL, SANITARY_READ, SANITARY_NOT_SUPPLIED,
             SANITARY_UNREADABLE, WALLS_ESTABLISHED, WALLS_NEED_REVIEW,
             EV_ADJACENT_OPEN_PLAN, EV_FITTING_RUN, EV_SANITARY_FIXTURE,
             EV_NO_SPACE, str(SEARCH_MM)]
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:24]


@dataclass
class Source:
    """One representation offered for the sanitary evidence."""

    name: str = ""
    kind: str = ""
    status: str = SANITARY_NOT_SUPPLIED
    what_it_is: str = ""
    why_it_could_not_be_read: str = ""

    def record(self) -> dict:
        return {
            "source": self.name,
            "kind": self.kind,
            "status": self.status,
            "what_it_is": self.what_it_is,
            "why_it_could_not_be_read": self.why_it_could_not_be_read,
        }


def _near(labels, x, y, limit=SEARCH_MM) -> list:
    out = []
    for v in labels:
        lx, ly = getattr(v, "x", 0.0), getattr(v, "y", 0.0)
        d = math.hypot(lx - x, ly - y)
        if d <= limit:
            out.append((d, v))
    return sorted(out, key=lambda t: t[0])


def align(rows, labels, *, fittings=None, wall_bands=(), sources=(),
          sanitary_fixtures=(), floor_of=None) -> dict:
    """What the design set says about this pantry's tiled walls."""
    from engine import architectural_ontology as onto

    floor = dict(floor_of or {})
    by_id = {r["space_id"]: r for r in rows}
    bands = {w.wall_id: w for w in (wall_bands or ())}
    fits = dict(fittings or {})
    src = [s.record() if isinstance(s, Source) else dict(s)
           for s in (sources or ())]
    readable = [s for s in src if s.get("status") == SANITARY_READ]

    out = []
    for v in labels:
        raw = (getattr(v, "text", "") or "")
        if not any(term in raw.upper() for term in fz.PANTRY_TERMS):
            continue
        x, y = getattr(v, "x", 0.0), getattr(v, "y", 0.0)
        sid = getattr(v, "space_id", "")
        row = by_id.get(sid)

        neighbours = []
        for d, other in _near(labels, x, y):
            if other is v:
                continue
            concept = onto.classify_term(
                getattr(other, "text", "") or "").concept
            if concept in fz.OPEN_PLAN_CONCEPTS:
                neighbours.append({"label": getattr(other, "text", ""),
                                   "concept": concept,
                                   "distance_mm": round(d, 1),
                                   "physical_space_id": getattr(
                                       other, "space_id", "")})

        runs = []
        for band_id, st in sorted(fits.items()):
            w = bands.get(getattr(st, "wall_id", band_id))
            if w is None:
                continue
            axis = getattr(w, "axis", "")
            fixed = getattr(st, "shared_face_mm", 0.0)
            here = abs((fixed - x) if axis == "V" else (fixed - y))
            if here > SEARCH_MM:
                continue
            spans = [(lo, hi) for lo, hi in getattr(w, "drawn_mm", ())]
            close = [(lo, hi) for lo, hi in spans
                     if min(abs(lo - (y if axis == "V" else x)),
                            abs(hi - (y if axis == "V" else x)))
                     <= SEARCH_MM]
            if not close:
                continue
            runs.append({"fitting_band_id": band_id,
                         "wall_band_id": getattr(st, "wall_id", ""),
                         "axis": axis,
                         "host_face_mm": round(fixed, 1),
                         "front_face_mm": round(
                             getattr(st, "far_face_mm", 0.0), 1),
                         "drawn_mm": [[round(a, 1), round(b, 1)]
                                      for a, b in close],
                         "distance_mm": round(here, 1)})

        fixtures = [f for f in (sanitary_fixtures or ())
                    if math.hypot(f.get("x", 0.0) - x,
                                  f.get("y", 0.0) - y) <= SEARCH_MM]

        ev = []
        if neighbours:
            ev.append(EV_ADJACENT_OPEN_PLAN)
        if runs:
            ev.append(EV_FITTING_RUN)
        if fixtures:
            ev.append(EV_SANITARY_FIXTURE)
        if row is None:
            ev.append(EV_NO_SPACE)

        # THE WALL SET. Established only when the installation's own host
        # walls are known — the fittings inside the pantry's space, or a
        # sanitary fixture's wall. Adjacency alone establishes nothing:
        # it says the pantry is open, not which wall it is tiled on.
        established = bool(row is not None and runs)
        walls = sorted({r["wall_band_id"] for r in runs}) if established \
            else []
        shape = (fz._shape_of(len({(r["axis"], r["host_face_mm"])
                                   for r in runs}))
                 if established else fz.SHAPE_NOT_ESTABLISHED)
        sanitary_status = (SANITARY_READ if readable else
                           (SANITARY_UNREADABLE if src
                            else SANITARY_NOT_SUPPLIED))
        out.append({
            "pantry_label": raw,
            "at_mm": [round(x, 1), round(y, 1)],
            "drawing_region_id": getattr(v, "region_id", ""),
            "floor": floor.get(getattr(v, "region_id", ""), ""),
            "physical_space_id": sid,
            "label_status": getattr(v, "status", ""),
            "adjacent_open_plan_labels": neighbours[:6],
            "fitting_runs_near_the_label": runs,
            "sanitary_fixtures_found": list(fixtures),
            "sanitary_status": sanitary_status,
            "sanitary_sources": src,
            "evidence": ev,
            "applicable_wall_set": walls,
            "wall_tile_shape": shape,
            "status": (WALLS_ESTABLISHED if established
                       else WALLS_NEED_REVIEW),
            "what_would_settle_it": (
                "" if established else
                "the sanitary or plumbing set for this project in a form "
                "this engine reads — a DWG or a vector PDF — or the "
                "owner naming the wall or walls the pantry units are "
                "fitted along"),
            "never_the_perimeter": (
                "the perimeter of the open space this label sits in "
                "belongs to the dining as much as to the pantry, and is "
                "never reported as pantry tile"),
        })
    return {
        "model": MODEL,
        "PANTRY_ALIGNMENT_HASH": model_hash(),
        "rows": out,
        "pantries": len(out),
        "walls_established": sum(1 for r in out
                                 if r["status"] == WALLS_ESTABLISHED),
        "require_owner_review": sum(1 for r in out
                                    if r["status"] == WALLS_NEED_REVIEW),
        "sources": src,
    }
