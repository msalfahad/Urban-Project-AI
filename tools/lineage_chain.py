"""§5, §6. The real 6C -> 6D -> 6E lineage, from the frozen bundles.

A lineage computed against a registry this round invented would prove
nothing. The predecessors are the bundles that were actually exported
and sent to the owner: their SPACE_REGISTER tables carry a polygon per
candidate, which is all the matching needs.

    seed(6C bundle)            the ids round 6C had, as its stable ids
    assign(6D rows, prev=6C)   what happened between 6C and 6D
    assign(6E rows, prev=6D)   what happened in this round

Round 6C's ids are seeded rather than derived, and marked as seeded:
they are the run enumeration of a round that had no stable identity, and
pretending otherwise would be the very thing §4 refuses.
"""

from __future__ import annotations

import json
from pathlib import Path

from engine import space_lineage as lineage

SEEDED = "SEEDED_FROM_A_FROZEN_BUNDLE"


def _records(path) -> list:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if isinstance(data, dict):
        return list(data.get("records") or data.get("rows") or [])
    return list(data)


def rows_from_bundle(path) -> list:
    """A bundle's register rows, in the shape the matcher wants."""
    from shapely.wkt import loads

    out = []
    for r in _records(path):
        wkt = r.get("polygon_wkt_mm") or ""
        poly = None
        if wkt:
            try:
                poly = loads(wkt)
            except Exception:      # noqa: BLE001
                poly = None
        out.append({
            "space_id": r.get("physical_space_id", ""),
            "region_id": r.get("drawing_region_id", ""),
            "polygon": poly,
            "area_m2": float(r.get("area_m2") or 0.0),
            "normalized_identity": r.get("normalized_identity", ""),
            "candidate_role": r.get("candidate_role", ""),
            "wall_band_ids": (),
        })
    return out


def seed(path, run_id: str) -> dict:
    """The first registry: a round's own ids, taken as its identities."""
    spaces = []
    for row in rows_from_bundle(path):
        g = row["polygon"]
        spaces.append({
            "stable_space_id": row["space_id"],
            "run_candidate_id": row["space_id"],
            "drawing_region_id": row["region_id"],
            "floor": "",
            "area_m2": row["area_m2"],
            "normalized_identity": row["normalized_identity"],
            "candidate_role": row["candidate_role"],
            "wall_band_ids": [],
            "polygon_wkt_mm": (g.wkt if g is not None else ""),
            "identity_source": SEEDED,
        })
    return {"model": lineage.MODEL, "run_id": run_id, "previous_run_id": "",
            "spaces": spaces,
            "note": ("round 6C had no stable identity. These ids are its "
                     "run enumeration, seeded so that the rounds after "
                     "it have something real to be compared against")}


def chain(bundles, regions, *, floor_of=None) -> dict:
    """[(run_id, register json path)] oldest first, then the reports."""
    steps, prev, prev_id = [], None, ""
    for i, (run_id, path) in enumerate(bundles):
        rows = rows_from_bundle(path)
        if i == 0:
            prev = seed(path, run_id)
            prev_id = run_id
            continue
        rep = lineage.assign(rows, regions, previous=prev, run_id=run_id,
                             floor_of=floor_of)
        steps.append({"from": prev_id, "to": run_id,
                      "report": rep, "counts": rep.counts()})
        prev = lineage.registry(rep, rows)
        prev["run_id"] = run_id
        prev["previous_run_id"] = prev_id
        prev_id = run_id
    return {"registry": prev, "previous_run_id": prev_id, "steps": steps}
