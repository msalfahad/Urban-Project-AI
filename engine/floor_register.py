"""Assemble one drawing's floor register from a finished measurement.

Nothing here measures anything. It is the order the round-6C objects go
together in, kept in ONE place so the synthetic drawings and the real one
are assembled identically:

    what does each region show          drawing_role.classify
    which bands are fittings            space_register.linings
    one row per measured candidate      here
    the unique register, per floor      space_register.build
    every authored label to one space   space_register.reconcile_labels
    and then, and only then, the drawing-role refusal

The refusal is last on purpose: a region that may not release rooms is
told so after its geometry has been measured and registered, never
before, so the register still records what is drawn there.
"""

from __future__ import annotations

from engine import drawing_role as drole
from engine import semantic_seed as seeds_mod
from engine import space_register as sreg

RELEASE_ELIGIBLE = "RELEASE_ELIGIBLE_GEOMETRY"
WITHHELD_ROLE = "WITHHELD_DRAWING_ROLE"


def _labels(r) -> str:
    return " | ".join(str(t) for z in r.zones for t in z.label_observations)


def rows(rep, roles=None) -> list:
    """One dict per measured space: geometry, identity and its faces.

    `face_contacts` carries (band, the line that face sits on) for every
    boundary face. WHICH face of a band bounds a space is the whole
    question when that band is a fitting standing on a wall.
    """
    from shapely.wkt import loads

    srole = ({v.space_id: v.role for v in rep.space_roles.verdicts}
             if rep.space_roles else {})
    out = []
    for r in rep.rows:
        c = r.clear
        poly = None
        if c is not None and c.polygon_wkt:
            try:
                poly = loads(c.polygon_wkt)
            except Exception:      # noqa: BLE001
                poly = None
        rel = r._release()
        faces = c.boundary_faces if c is not None else ()
        out.append({
            "space_id": r.space_id,
            "region_id": r.region_id,
            "polygon": poly,
            "area_m2": (c.area_m2 if c is not None else 0.0),
            "principal_dims_mm": (list(c.principal_dims_mm)
                                  if c is not None else []),
            "basis": (c.basis if c is not None else ""),
            "label_raw": _labels(r),
            "normalized_identity": (
                getattr(r.identity, "normalized_identity", "")
                if r.identity else ""),
            "identity_authority": r.identity_status,
            "geometry_authority": r.geometry_status,
            "release_status": rel["status"],
            "blockers": ([rel["blocker"]] if rel.get("blocker") else []),
            "space_role": srole.get(r.space_id, ""),
            "wall_band_ids": sorted({f.wall_band_id for f in faces
                                     if f.wall_band_id}),
            "face_contacts": sorted({(f.wall_band_id, round(f.fixed_mm, 3))
                                     for f in faces if f.wall_band_id}),
            "cad_provenance": sorted({p for f in faces
                                      for p in f.cad_provenance})[:8],
        })
    return out


def assemble(nd, rep, *, supervised=None) -> dict:
    """roles, linings, rows, register and labels, in that order."""
    regions = rep.regions.regions

    spaces_by, openings_by, bands_by, sites_by, stamps_by = {}, {}, {}, {}, {}
    for r in rep.rows:
        spaces_by.setdefault(r.region_id, []).append(r.space_id)
    for wr in rep.walls:
        bands_by[wr.region_id] = list(wr.walls)
    if rep.openings is not None:
        for o in rep.openings.openings:
            openings_by.setdefault(
                getattr(o, "region_id", ""), []).append(o.opening_id)
    if rep.space_roles is not None:
        for rid, m in rep.space_roles.envelopes.items():
            sites_by[rid] = m.site is not None
    sem = seeds_mod.classify(nd.texts)
    for o in sem.seeds():
        for reg in regions:
            if reg.contains(o.x, o.y):
                stamps_by.setdefault(reg.region_id, []).append(o)
                break

    roles = drole.classify(
        regions, texts=nd.texts, spaces_by_region=spaces_by,
        openings_by_region=openings_by, bands_by_region=bands_by,
        sites_by_region=sites_by, stamps_by_region=stamps_by,
        supervised=dict(supervised or {}))
    floor_of = {r.region_id: r.floor_level for r in roles.roles}

    table = rows(rep, roles)
    srole = ({v.space_id: v.role for v in rep.space_roles.verdicts}
             if rep.space_roles else {})
    lining = sreg.linings({wr.region_id: wr.walls for wr in rep.walls})
    # §3. The drawing-role gate is part of the ONE release state, not a
    # second pass that rewrites a status somebody else set.
    may_release_in = {r.region_id for r in roles.roles if r.may_release_rooms}
    register = sreg.build(table, regions, roles=roles, floor_of=floor_of,
                          space_role_of=srole, lining_bands=lining,
                          may_release_in=may_release_in)
    register = sreg.reconcile_labels(register, sem.seeds(), table,
                                     floor_of=floor_of)
    refused = sum(1 for e in register.entries
                  if sreg.W_DRAWING_ROLE in e.withheld_because)

    return {"roles": roles, "floor_of": floor_of, "rows": table,
            "linings": lining, "register": register,
            "release_refused_for_drawing_role": refused}
