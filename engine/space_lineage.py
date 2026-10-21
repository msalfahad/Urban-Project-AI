"""A run candidate is not a physical identity.

Between the frozen round-6C export and round 6D, 68 `physical_space_id`
values appear in both — and 17 of them change area by more than 5%, 15 by
more than 20%. Areas SWAPPED between ids: 26.58 m2 moved from
PS-DR-004-014 to PS-DR-004-004, and 13.8255 m2 from -015 to -017. The
ids were the order the flood happened to enumerate the faces in, and
nothing else.

An id like that cannot carry a revision comparison, a BOQ revision, an
approval, a change order or an audit history. So there are two ids:

    RUN_CANDIDATE_ID          this run's enumeration. It may change on
                              every execution and that is allowed
    STABLE_PHYSICAL_SPACE_ID  the identity of a space of the building. It
                              survives ordinary geometry refinement

A stable id is carried forward by EVIDENCE, never by area:

    the drawing region and the floor it belongs to
    how much of it the same polygon still covers, both ways round
    where its centroid sits relative to its own region
    which wall bands bound it
    what it is called

and where the evidence does not settle it, the answer is
UNRESOLVED_LINEAGE rather than a guess that looks tidy.

WHAT A SPLIT AND A MERGE DO

A split gives NEITHER child the parent's id — whichever child the flood
enumerates first is not the parent, and pretending otherwise is how a
revision comparison silently follows the wrong room. Both children are
new identities with the parent recorded as their predecessor. A merge is
the same in reverse: one new identity, every predecessor kept.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path

MODEL = "RUN_CANDIDATE_IS_NOT_A_PHYSICAL_IDENTITY_V1"

# --- §6 what happened to a space between two runs ------------------------
UNCHANGED = "UNCHANGED"
RESHAPED = "RESHAPED"
SPLIT = "SPLIT"
MERGED = "MERGED"
NEW = "NEW"
REMOVED = "REMOVED"
IDENTITY_CHANGED = "IDENTITY_CHANGED"
ROLE_CHANGED = "ROLE_CHANGED"
UNRESOLVED_LINEAGE = "UNRESOLVED_LINEAGE"

LINEAGE = (UNCHANGED, RESHAPED, SPLIT, MERGED, NEW, REMOVED,
           IDENTITY_CHANGED, ROLE_CHANGED, UNRESOLVED_LINEAGE)

# The same polygon, to within what the drawing itself would not
# distinguish. A share of the union, never an area.
SAME_SHAPE = 0.98
# Enough of both to be the same space refined, rather than two spaces
# that happen to touch.
SAME_SPACE = 0.5
# A child of a split lies almost entirely inside its parent.
INSIDE_ITS_PARENT = 0.8
# Together, the children of a split account for most of the parent.
COVERS_ITS_PARENT = 0.6

# A centroid cell, for the fingerprint of a space nobody has seen before.
# The enclosure's own junction reach, times a hundred: a quarter of a
# metre, which no room of this project is smaller than.
CENTROID_CELL_MM = 250.0


def frozen_parameters() -> dict:
    return {
        "MODEL": MODEL,
        "LINEAGE": list(LINEAGE),
        "SAME_SHAPE": SAME_SHAPE,
        "SAME_SPACE": SAME_SPACE,
        "INSIDE_ITS_PARENT": INSIDE_ITS_PARENT,
        "COVERS_ITS_PARENT": COVERS_ITS_PARENT,
        "CENTROID_CELL_MM": CENTROID_CELL_MM,
        "why": {
            "never_by_area": (
                "two rooms of 12.60 m2 on one floor are two rooms. Area "
                "is the one piece of evidence that cannot tell them "
                "apart, and it is the one the old ids effectively used"),
            "a_split_keeps_no_id": (
                "whichever child is enumerated first is not the parent. "
                "Both are new identities and the parent is their "
                "predecessor"),
            "a_merge_keeps_every_predecessor": (
                "a merged space is one identity with several histories, "
                "and losing any of them loses a revision"),
            "unresolved_is_an_answer": (
                "where two candidates match a predecessor equally well, "
                "the lineage is UNRESOLVED and no id is carried"),
        },
    }


def model_hash() -> str:
    parts = ([MODEL] + list(LINEAGE)
             + [str(v) for v in (SAME_SHAPE, SAME_SPACE, INSIDE_ITS_PARENT,
                                 COVERS_ITS_PARENT, CENTROID_CELL_MM)])
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:24]


# ---------------------------------------------------------------- objects

@dataclass
class Link:
    """What happened to one space between the previous run and this one."""

    run_candidate_id: str = ""
    stable_space_id: str = ""
    region_id: str = ""
    floor_level: str = ""
    lineage: str = NEW
    predecessor_ids: tuple = ()
    successor_ids: tuple = ()
    overlap_ratio: float = 0.0
    boundary_lineage: tuple = ()
    area_m2: float = 0.0
    previous_area_m2: float | None = None
    identity: str = ""
    previous_identity: str = ""
    role: str = ""
    previous_role: str = ""
    confidence: str = ""
    reason: str = ""

    def record(self) -> dict:
        return {
            "run_candidate_id": self.run_candidate_id,
            "stable_space_id": self.stable_space_id,
            "drawing_region_id": self.region_id,
            "floor": self.floor_level,
            "lineage": self.lineage,
            "predecessor_ids": list(self.predecessor_ids),
            "successor_ids": list(self.successor_ids),
            "overlap_ratio": round(self.overlap_ratio, 4),
            "boundary_lineage": list(self.boundary_lineage),
            "area_m2": round(self.area_m2, 4),
            "previous_area_m2": (None if self.previous_area_m2 is None
                                 else round(self.previous_area_m2, 4)),
            "normalized_identity": self.identity,
            "previous_identity": self.previous_identity,
            "candidate_role": self.role,
            "previous_candidate_role": self.previous_role,
            "confidence": self.confidence,
            "reason": self.reason,
        }


@dataclass
class LineageReport:
    run_id: str = ""
    previous_run_id: str = ""
    links: list = field(default_factory=list)
    removed: list = field(default_factory=list)
    notes: dict = field(default_factory=dict)

    def counts(self) -> dict:
        from collections import Counter

        out = dict(Counter(x.lineage for x in self.links).most_common())
        out[REMOVED] = len(self.removed)
        out["links"] = len(self.links)
        out["stable_ids_carried_forward"] = sum(
            1 for x in self.links if x.predecessor_ids
            and x.lineage in (UNCHANGED, RESHAPED, IDENTITY_CHANGED,
                              ROLE_CHANGED))
        return out

    def record(self) -> dict:
        return {
            "model": MODEL,
            "SPACE_LINEAGE_HASH": model_hash(),
            "run_id": self.run_id,
            "previous_run_id": self.previous_run_id,
            "counts": self.counts(),
            "frozen_parameters": frozen_parameters(),
            "links": [x.record() for x in self.links],
            "removed": [dict(x) for x in self.removed],
            "notes": dict(self.notes),
        }


# ------------------------------------------------------------ the matching

def _key(region_id: str, poly, origin) -> str:
    """A fingerprint for a space nobody has seen before.

    The centroid RELATIVE to its own drawing region, in cells: a plan
    redrawn at another place on the sheet keeps its identities, and two
    rooms of the same area in different places never collide.
    """
    ox, oy = origin
    cx, cy = poly.centroid.x - ox, poly.centroid.y - oy
    raw = f"{region_id}|{round(cx / CENTROID_CELL_MM)}|" \
          f"{round(cy / CENTROID_CELL_MM)}"
    return "SP-" + hashlib.sha256(raw.encode("utf-8")).hexdigest()[:12]


def _shares(a, b) -> tuple:
    """(in a, in b, over the union). Three numbers, no thresholds yet."""
    try:
        inter = a.intersection(b).area
    except Exception:      # noqa: BLE001
        return (0.0, 0.0, 0.0)
    if inter <= 0:
        return (0.0, 0.0, 0.0)
    union = a.area + b.area - inter
    return (inter / a.area if a.area else 0.0,
            inter / b.area if b.area else 0.0,
            inter / union if union else 0.0)


def assign(rows, regions, *, previous=None, run_id: str = "",
           floor_of=None) -> LineageReport:
    """Give every candidate of this run a stable identity and a history.

    `rows` are the register's rows (a polygon, a region, an identity and
    a role each). `previous` is the registry of the last run — the list
    of records this function returned then.
    """
    rep = LineageReport(run_id=run_id)
    floor = dict(floor_of or {})
    origin = {r.region_id: (r.x0, r.y0) for r in regions}
    prev = list((previous or {}).get("spaces", []))
    rep.previous_run_id = (previous or {}).get("run_id", "")

    from shapely.wkt import loads

    prev_poly = {}
    for p in prev:
        wkt = p.get("polygon_wkt_mm") or ""
        if not wkt:
            continue
        try:
            prev_poly[p["stable_space_id"]] = loads(wkt)
        except Exception:      # noqa: BLE001
            continue
    prev_by_id = {p["stable_space_id"]: p for p in prev}

    # ---- every overlap worth considering, both ways round -------------
    pairs = []
    for row in rows:
        poly = row.get("polygon")
        if poly is None:
            continue
        for sid, g in prev_poly.items():
            if prev_by_id[sid].get("drawing_region_id") != row["region_id"]:
                continue
            in_new, in_old, iou = _shares(poly, g)
            if iou <= 0.0:
                continue
            pairs.append({"row": row, "prev": sid, "in_new": in_new,
                          "in_old": in_old, "iou": iou})

    by_row: dict = {}
    by_prev: dict = {}
    for pr in pairs:
        by_row.setdefault(pr["row"]["space_id"], []).append(pr)
        by_prev.setdefault(pr["prev"], []).append(pr)

    used_prev: set = set()
    for row in rows:
        poly = row.get("polygon")
        mine = sorted(by_row.get(row["space_id"], ()),
                      key=lambda p: -p["iou"])
        link = Link(
            run_candidate_id=row["space_id"], region_id=row["region_id"],
            floor_level=floor.get(row["region_id"], ""),
            area_m2=row.get("area_m2", 0.0) or 0.0,
            identity=row.get("normalized_identity", ""),
            role=row.get("candidate_role", ""),
            boundary_lineage=tuple(sorted(row.get("wall_band_ids", ()))[:8]))

        if poly is None or not mine:
            link.stable_space_id = (
                _key(row["region_id"], poly, origin.get(row["region_id"],
                                                        (0.0, 0.0)))
                if poly is not None else f"SP-RUN-{row['space_id']}")
            link.lineage = NEW
            link.confidence = "NO_PREDECESSOR_OVERLAPS_IT"
            link.reason = ("nothing in the previous run covers this "
                           "polygon at all")
            rep.links.append(link)
            continue

        best = mine[0]
        prev_id = best["prev"]
        # several of THIS run's candidates inside one previous space
        children = [p for p in by_prev.get(prev_id, ())
                    if p["in_new"] >= INSIDE_ITS_PARENT]
        covered = sum(p["in_old"] for p in children)
        # several PREVIOUS spaces inside this one candidate
        parents = [p for p in mine if p["in_old"] >= INSIDE_ITS_PARENT]

        link.overlap_ratio = best["iou"]
        link.previous_area_m2 = prev_by_id[prev_id].get("area_m2")
        link.previous_identity = prev_by_id[prev_id].get(
            "normalized_identity", "")
        link.previous_role = prev_by_id[prev_id].get("candidate_role", "")

        if best["iou"] >= SAME_SHAPE:
            # THE SAME POLYGON IS THE SAME SPACE. Asked first, because a
            # plate that still contains its own rooms overlaps every one
            # of them, and a register that carries a parent and its
            # children would otherwise read as a merge every time.
            link.stable_space_id = prev_id
            link.lineage = UNCHANGED
            link.predecessor_ids = (prev_id,)
            link.confidence = "THE_SAME_POLYGON"
            link.reason = f"it covers {round(best['iou'] * 100, 1)}% of " \
                          "the union with its predecessor"
        elif len(parents) >= 2:
            link.stable_space_id = _key(
                row["region_id"], poly, origin.get(row["region_id"],
                                                   (0.0, 0.0)))
            link.lineage = MERGED
            link.predecessor_ids = tuple(sorted(p["prev"] for p in parents))
            link.confidence = "EVERY_PREDECESSOR_IS_KEPT"
            link.reason = (f"{len(parents)} spaces of the previous run lie "
                           "inside this one. A merged space is a new "
                           "identity with all of their histories")
        elif len(children) >= 2 and covered >= COVERS_ITS_PARENT:
            link.stable_space_id = _key(
                row["region_id"], poly, origin.get(row["region_id"],
                                                   (0.0, 0.0)))
            link.lineage = SPLIT
            link.predecessor_ids = (prev_id,)
            link.confidence = "NEITHER_CHILD_INHERITS_THE_PARENT"
            link.reason = (f"{len(children)} candidates of this run lie "
                           f"inside {prev_id}. Whichever was enumerated "
                           "first is not the parent")
        elif best["iou"] >= SAME_SPACE and len(
                [p for p in mine if p["iou"] >= SAME_SPACE]) == 1 and len(
                [p for p in by_prev.get(prev_id, ())
                 if p["iou"] >= SAME_SPACE]) == 1:
            link.stable_space_id = prev_id
            link.lineage = RESHAPED
            link.predecessor_ids = (prev_id,)
            link.confidence = "ONE_TO_ONE_ON_OVERLAP"
            link.reason = f"it covers {round(best['iou'] * 100, 1)}% of " \
                          "the union with its predecessor, and nothing " \
                          "else matches either of them"
        else:
            link.stable_space_id = _key(
                row["region_id"], poly, origin.get(row["region_id"],
                                                   (0.0, 0.0)))
            link.lineage = UNRESOLVED_LINEAGE
            link.predecessor_ids = tuple(sorted(
                p["prev"] for p in mine[:3]))
            link.confidence = "SEVERAL_CANDIDATES_MATCH_EQUALLY_POORLY"
            link.reason = (f"the best overlap is "
                           f"{round(best['iou'] * 100, 1)}% and "
                           f"{len(mine)} previous space(s) overlap it. No "
                           "id is carried on that")

        if link.lineage in (UNCHANGED, RESHAPED):
            if link.identity and link.previous_identity and \
                    link.identity != link.previous_identity:
                link.lineage = IDENTITY_CHANGED
            elif link.role and link.previous_role and \
                    link.role != link.previous_role:
                link.lineage = ROLE_CHANGED
        for p in mine:
            if p["iou"] >= SAME_SPACE or p["in_old"] >= INSIDE_ITS_PARENT:
                used_prev.add(p["prev"])
        used_prev.add(prev_id)
        rep.links.append(link)

    # ---- successors, and what is gone ---------------------------------
    succ: dict = {}
    for link in rep.links:
        for pid in link.predecessor_ids:
            succ.setdefault(pid, []).append(link.stable_space_id)
    for link in rep.links:
        if link.lineage == SPLIT:
            link.successor_ids = tuple(sorted(
                succ.get(link.predecessor_ids[0], ())))
    for p in prev:
        sid = p["stable_space_id"]
        if sid in used_prev:
            continue
        rep.removed.append({
            "stable_space_id": sid,
            "drawing_region_id": p.get("drawing_region_id", ""),
            "area_m2": p.get("area_m2"),
            "normalized_identity": p.get("normalized_identity", ""),
            "lineage": REMOVED,
            "reason": "no candidate of this run overlaps it",
        })

    rep.notes["two_ids"] = (
        "a run candidate id may change on every execution. A stable "
        "physical-space id may not, and it is carried only on evidence")
    rep.notes["never_by_area"] = (
        "area is the one piece of evidence that cannot tell two rooms "
        "apart, and nothing here matches on it")
    return rep


# --------------------------------------------------------------- the store

def registry(rep: LineageReport, rows) -> dict:
    """What the next run needs to know about this one."""
    poly = {r["space_id"]: r.get("polygon") for r in rows}
    row_of = {r["space_id"]: r for r in rows}
    out = []
    for link in rep.links:
        g = poly.get(link.run_candidate_id)
        row = row_of.get(link.run_candidate_id, {})
        out.append({
            "stable_space_id": link.stable_space_id,
            "run_candidate_id": link.run_candidate_id,
            "drawing_region_id": link.region_id,
            "floor": link.floor_level,
            "area_m2": link.area_m2,
            "normalized_identity": link.identity,
            "candidate_role": row.get("candidate_role", link.role),
            "wall_band_ids": sorted(row.get("wall_band_ids", ())),
            "polygon_wkt_mm": (g.wkt if g is not None else ""),
        })
    return {"model": MODEL, "run_id": rep.run_id,
            "previous_run_id": rep.previous_run_id, "spaces": out}


def load(path: str) -> dict:
    p = Path(path)
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:      # noqa: BLE001
        return {}


def save(path: str, data: dict) -> str:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, indent=2, ensure_ascii=False,
                            default=str) + "\n", encoding="utf-8")
    return str(p)
