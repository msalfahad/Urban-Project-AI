"""E83 — when release recall stays at zero, WHICH dependency is holding it.

`RELEASE_ELIGIBLE_SPACE_GEOMETRY_RECALL = 0 / 17` is a true statement and a
useless instruction. Zero because the walls are not established is a
different project from zero because the portals are not validated, and the
two need opposite next rounds.

So the blocks are counted per space and the dominant one is named. Where a
space is blocked by more than one thing, every block is counted — the point
is not to find a single culprit but to see which class of evidence would
unlock the most rooms if it were supplied.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field

DEP_WALL_GEOMETRY = "WALL_GEOMETRY"
DEP_PORTAL_VALIDATION = "PORTAL_VALIDATION"
DEP_IDENTITY = "IDENTITY"
DEP_ENVELOPE = "ENVELOPE"
DEP_OTHER = "OTHER"

DEPENDENCIES = (DEP_WALL_GEOMETRY, DEP_PORTAL_VALIDATION, DEP_IDENTITY,
                DEP_ENVELOPE, DEP_OTHER)

# Which block belongs to which dependency class.
BLOCK_TO_DEPENDENCY = {
    "BOUNDARY_RESTS_ON_UNESTABLISHED_WALL_MATERIAL": DEP_WALL_GEOMETRY,
    "COMPONENT_HOLDS_MORE_THAN_ONE_LABELLED_SPACE": DEP_WALL_GEOMETRY,
    "PARTITION_DEPENDS_ON_A_DIAGNOSTIC_PORTAL": DEP_PORTAL_VALIDATION,
    "MEASUREMENT_BASIS_NOT_VALIDATED": DEP_OTHER,
    "GEOMETRY_ROLE_IS_NOT_AN_OCCUPIABLE_SPACE": DEP_OTHER,
}


@dataclass
class Report:
    rows: list = field(default_factory=list)
    in_scope_spaces: int = 0
    notes: dict = field(default_factory=dict)

    def record(self) -> dict:
        by_dep = Counter()
        spaces_by_dep: dict = {}
        for r in self.rows:
            for dep in set(r["dependencies"]):
                by_dep[dep] += 1
                spaces_by_dep.setdefault(dep, []).extend(r["space_ids"])
        dominant = (by_dep.most_common(1)[0][0] if by_dep else None)
        # A space blocked ONLY by one dependency is the one that dependency
        # would actually unlock. That is the number that should drive the
        # next round, not the raw block count.
        sole: dict = {}
        for r in self.rows:
            deps = set(r["dependencies"])
            if len(deps) == 1:
                sole.setdefault(next(iter(deps)), []).extend(r["space_ids"])
        return {
            "in_scope_spaces": self.in_scope_spaces,
            "blocked_space_geometries": len(self.rows),
            "spaces_blocked_by_dependency": dict(by_dep),
            "DOMINANT_REMAINING_RELEASE_BLOCKER": dominant,
            "spaces_blocked_SOLELY_by": {
                k: sorted(set(v)) for k, v in sorted(sole.items())},
            "what_each_would_unlock": {
                k: len(set(v)) for k, v in sorted(sole.items())},
            "why_sole_blocks_matter_more": (
                "a space blocked by two dependencies is unlocked by "
                "neither on its own. The rooms a single dependency would "
                "actually release are the ones blocked by it ALONE, and "
                "that is the number the next round should be chosen on"),
            "dependencies": list(DEPENDENCIES),
            "rows": self.rows,
            "notes": dict(self.notes),
        }


def assess(recall_record, *, in_scope_spaces: int = 0) -> Report:
    """Classify the blocks the recall report already found."""
    rep = Report(in_scope_spaces=in_scope_spaces)
    for row in recall_record.get("single_label_but_blocked", ()):
        deps = [BLOCK_TO_DEPENDENCY.get(b, DEP_OTHER)
                for b in row.get("blocks", ())]
        rep.rows.append({
            "space_geometry_id": row.get("space_geometry_id"),
            "space_ids": list(row.get("space_ids", ())),
            "blocks": list(row.get("blocks", ())),
            "dependencies": deps,
            "unestablished_boundary_m": row.get(
                "unestablished_boundary_m", 0.0),
            # Carried, not dropped: portal_bottleneck below can only name
            # a portal if the recall row said which one blocked the space.
            "blocking_portal_ids": list(row.get("blocking_portal_ids", ())),
        })
    rep.notes["blocks_seen"] = dict(Counter(
        b for r in rep.rows for b in r["blocks"]))
    return rep


# ------------------------------------------------- the portal bottleneck

def portal_bottleneck(rows, barriers, *, portals=()) -> dict:
    """For each space a portal blocks, what evidence is missing.

    This is preparation, not extraction: no document is read here. The
    output is a list of exactly which portals would need a second,
    independent evidence family, and what kind of source could supply it.
    """
    by_id = {b.portal_id: b for b in barriers}
    portal_by_id = {p.portal_id: p for p in portals}
    out = []
    for r in rows:
        if DEP_PORTAL_VALIDATION not in r["dependencies"]:
            continue
        for pid in r.get("blocking_portal_ids", ()):
            b = by_id.get(pid)
            p = portal_by_id.get(pid)
            if b is None:
                continue
            fams = sorted({
                _family(e) for e in getattr(b, "existence_evidence", ())})
            out.append({
                "space_ids": list(r["space_ids"]),
                "portal_id": pid,
                "host_wall_band_id": b.host_wall_band_id,
                "opening_width_mm": round(b.opening_width_mm, 1),
                "portal_existence_status": b.existence_status,
                "portal_geometry_status": b.geometry_status,
                "evidence_present": list(
                    getattr(b, "existence_evidence", ())),
                "evidence_families_present": fams,
                "source_independence_of_present_evidence": (
                    "SAME_DRAWING — every item above is read off this "
                    "sheet's own geometry"),
                "missing_evidence_needed": [
                    "a DOOR OR WINDOW SCHEDULE row naming an opening at "
                    "this location or on this wall",
                    "a door/window SYMBOL block identified as such rather "
                    "than as anonymous geometry",
                    "a PRINTED DIMENSION for the opening width",
                    "a CAD entity from the originating model, or a site "
                    "observation",
                ],
                "why_this_blocks_release": (
                    "the opening's existence rests on this drawing's "
                    "geometry alone. If the opening is not there the space "
                    "is not there, and a released quantity carries no "
                    "memory of which portal it rested on"),
                "gap_class": getattr(p, "gap_class", "") if p else "",
            })
    return {
        "portals_blocking_release": len({o["portal_id"] for o in out}),
        "spaces_they_block": len({s for o in out for s in o["space_ids"]}),
        "portals": out,
        "this_is_preparation_not_extraction": (
            "no document is read here. The list says which portals would "
            "need a second independent evidence family and what kind of "
            "source could supply it, so the next round can be chosen "
            "rather than guessed"),
    }


def _family(item: str) -> str:
    text = str(item).upper()
    if "SCHEDULE" in text or "DIMENSION" in text or "TABLE" in text:
        return "DOCUMENT"
    if "SYMBOL" in text or "BLOCK" in text or "CAP" in text:
        return "DRAWN_SYMBOL"
    if "RASTER" in text:
        return "RASTER"
    return "GEOMETRY"
