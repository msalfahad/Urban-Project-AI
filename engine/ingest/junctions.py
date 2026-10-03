"""Column / beam junction register (PA07E).

For every structural object the register keeps five separate facts, never collapsed into one:

    OBJECT_EXISTS         the closed loop / structural read exists (band evidence or structural sheet)
    OBJECT_GEOMETRY       sides, centre, orientation
    EXPOSED_TO_SPACE      which of its faces border a planar face that is a space (from the boundary face register)
    HOSTS_WALL            wall bands whose end lies inside the column footprint (the wall terminates on the column)
    TERMINATES_WALL       the same relation seen from the wall: its face is shortened by the footprint (JUNCTION_CUT rows)
    CLEAR_FACE_OWNERSHIP  each exposed face stretch is owned by the column, never counted again as wall face
    TRADE_ELIGIBILITY     decided separately from the four above: exposed faces may carry a linear column-bonding run;
                          embedded faces carry nothing; a beam edge is never wall material and carries nothing here

An embedded column (all four faces inside wall bands) contributes no exposed face; a free-standing column contributes
only its exposed faces; a wall terminating on a column keeps the shortened face (the footprint stretch is a JUNCTION_CUT).
"""

from __future__ import annotations

import math
from collections import defaultdict

from engine.ingest import material_bands as MB


def build(view_id, bands, boundary_rows, prims, roles, structural_objects=()):
    accepted = [b for b in bands if b["STATUS"] == "ACCEPTED"]
    cols = [b for b in accepted if b.get("BAND_TYPE") == "COLUMN_BAND"]
    walls = [b for b in accepted if b.get("BAND_TYPE") != "COLUMN_BAND"]
    by_band = defaultdict(list)
    for r in boundary_rows:
        by_band[r["BAND_ID"]].append(r)
    rows = []
    for c in cols:
        cx, cy = MB.band_point(c, (c["EXTENT"][0] + c["EXTENT"][1]) / 2)
        hosts = []
        for w in walls:
            for k, (x, y) in enumerate(MB._ends(w)):
                if MB.in_strip(c, x, y, tol=MB.JUNCTION_TOL):
                    hosts.append({"BAND_ID": w["BAND_ID"], "END": "START" if k == 0 else "END"})
        exposed = [r for r in by_band.get(c["BAND_ID"], []) if r["SEAL_KIND"] == "COLUMN_FACE" and r["SPACE_ELIGIBILITY"] == "ELIGIBLE"]
        embedded = [r for r in by_band.get(c["BAND_ID"], []) if r["SEAL_KIND"] == "JUNCTION_CUT"]
        other = [r for r in by_band.get(c["BAND_ID"], []) if r["SEAL_KIND"] == "COLUMN_FACE" and r["SPACE_ELIGIBILITY"] != "ELIGIBLE"]
        # short sides: exposed when no wall band occupies them
        short_sides = []
        for t, tag in ((c["EXTENT"][0], "START"), (c["EXTENT"][1], "END")):
            x, y = MB.band_point(c, t + (-1 if tag == "START" else 1) * 60.0)
            occupied = any(MB.in_strip(w, x, y, tol=0.0) for w in walls)
            short_sides.append({"SIDE": tag, "LENGTH_MM": round(c["THK"], 1), "STATE": "EMBEDDED_IN_WALL_BAND" if occupied else "FREE_OR_UNATTRIBUTED"})
        exposed_mm = round(sum(r["LENGTH_MM"] for r in exposed), 1)
        rows.append({"COLUMN_ID": c["BAND_ID"].replace("MB-", "CO-"), "BAND_ID": c["BAND_ID"], "VIEW_ID": view_id,
                     "OBJECT_EXISTS": {"STATUS": "ESTABLISHED", "EVIDENCE": "closed four-sided loop of material lines within column size (material band engine)"},
                     "OBJECT_GEOMETRY": {"CENTRE_MM": [round(cx, 1), round(cy, 1)], "SIDES_MM": [round(c["LENGTH"], 1), round(c["THK"], 1)], "ORIENTATION_DEG": round(math.degrees(c["ANGLE"]), 2)},
                     "EXPOSED_TO_SPACE": {"FACE_STRETCHES": [{"SPACE_FACE_ID": r["SPACE_FACE_ID"], "SIDE": r["SIDE"], "LENGTH_MM": r["LENGTH_MM"]} for r in exposed], "EXPOSED_MM_STRUCTURE_ONLY": exposed_mm,
                                          "SHORT_SIDES": short_sides, "STATUS": "EXPOSED" if exposed else ("EMBEDDED" if embedded or all(s["STATE"] == "EMBEDDED_IN_WALL_BAND" for s in short_sides) else "NOT_BESIDE_A_SPACE")},
                     "HOSTS_WALL": hosts, "TERMINATES_WALL": [{"BAND_ID": w["BAND_ID"]} for w in walls if any(r["SEAL_KIND"] == "JUNCTION_CUT" for r in by_band.get(w["BAND_ID"], []) if _cut_by(c, w, r))],
                     "CLEAR_FACE_OWNERSHIP": {"OWNER": "COLUMN", "RULE": "an exposed column face stretch is a COLUMN_FACE row; the wall face over the footprint is a JUNCTION_CUT row, never counted as wall"},
                     "TRADE_ELIGIBILITY": {"COLUMN_BONDING": "CANDIDATE_LINEAR_RUN" if exposed else "NONE", "WALL_PLASTER": "NONE", "NOTE": "eligibility is a separate decision from existence and exposure; the bridge still needs height, identity and rule status"},
                     "NON_SPACE_FACES": [{"SIDE": r["SIDE"], "LENGTH_MM": r["LENGTH_MM"], "ELIGIBILITY": r["SPACE_ELIGIBILITY"]} for r in other]})
    beams = [p for p in prims if roles.get(p.object_id, {}).get("ROLE") == "BEAM_EDGE"]
    beam_row = {"OBJECT": "BEAM_EDGES", "COUNT": len(beams), "OBJECT_EXISTS": {"STATUS": "PROVISIONAL", "EVIDENCE": "hidden / dashed linetype pairs (PA06 role)"},
                "TRADE_ELIGIBILITY": {"WALL_PLASTER": "NONE", "COLUMN_BONDING": "NONE", "NOTE": "a beam edge is never wall material and never a space boundary"},
                "USED_AS_MATERIAL_FACE": False}
    ext = []
    for o in structural_objects:
        ext.append({"OBJECT": o.get("TYPE"), "SOURCE": "PA06_STRUCTURAL_OBJECT_REGISTER", "OBJECT_EXISTS": {"STATUS": "REPORTED_BY_PA06", "EVIDENCE": o.get("EVIDENCE")}, "MATCHED_COLUMN_BAND": _match(o, cols)})
    return rows, beam_row, ext


def _cut_by(c, w, r):
    """Does the JUNCTION_CUT row r on wall w lie inside column c's footprint?"""
    t = (r["AXIAL_START"] + r["AXIAL_END"]) / 2
    x, y = MB.band_point(w, t, (-1 if r["SIDE"] == "A" else 1) * (w["THK"] / 2 + 1.0))
    return MB.in_strip(c, x, y, tol=0.0)


def _match(o, cols):
    cen = o.get("CENTRE_MM") or o.get("CENTER_MM")
    if not cen:
        return None
    for c in cols:
        if MB.in_strip(c, cen[0], cen[1], tol=0.0):
            return c["BAND_ID"]
    return None


def summarise(rows, beam_row):
    out = {"COLUMNS": len(rows), "EXPOSED": 0, "EMBEDDED": 0, "NOT_BESIDE_A_SPACE": 0, "HOSTING_WALLS": 0, "EXPOSED_M_STRUCTURE_ONLY": 0.0, "BEAM_EDGES": beam_row["COUNT"], "BEAM_USED_AS_WALL": False}
    for r in rows:
        out[r["EXPOSED_TO_SPACE"]["STATUS"]] += 1
        out["HOSTING_WALLS"] += 1 if r["HOSTS_WALL"] else 0
        out["EXPOSED_M_STRUCTURE_ONLY"] = round(out["EXPOSED_M_STRUCTURE_ONLY"] + r["EXPOSED_TO_SPACE"]["EXPOSED_MM_STRUCTURE_ONLY"] / 1000, 3)
    return out
