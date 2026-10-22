"""T-160: ring beam round a circular slab opening inside a bay framed by straight beams (NO REPO CODE: research tool).

Model (owner Q-44 A; URBAN-NON-OVERLAPPING-SLAB-BEAM-MODEL@v1; Q-61 C(3); UP-QTY-STATUS-001):
  - the bay is the rectangle between the inner faces of its four framing members (distances d_k from the ring centre);
  - the ring is the annulus r_i .. r_o. The part of it beyond a face d_k lies in that framing member (counted there,
    gross B x L x D), or, past the member's far face, in the next panel. Only the part INSIDE the bay is the ring's own:
        A_ring = A(annulus in bay) = [pi r_o^2 - sum_k seg(r_o, d_k)] - [pi r_i^2 - sum_k seg(r_i, d_k)]
    with seg(r, d) = r^2 acos(d / r) - d sqrt(r^2 - d^2) (circular segment beyond a chord at distance d; 0 if d >= r).
    Valid while no two segments overlap: d_j^2 + d_k^2 >= r_o^2 for every pair of adjacent faces (checked).
  - each overlap is removed once: annulus = A_ring + sum_k [in member k] + sum_k [beyond member k] (re-add check);
  - ring m3, gross basis (the beam register and T-139's slab ledger, whose dome corners stop at r_o): A_ring x D;
    the same concrete under the non-overlapping split: slab share A_ring x t + downstand A_ring x (D - t), never both;
  - a ring without an established depth is HELD: m3 None, never 0.

Two independent computations: the closed-form segment formula above and a shapely polygon intersection (circles as
polygons of 2^14 sides, area error < 1e-7 relative); they must agree to 1e-6 m2.

Usage:
  python -I dome_ring.py DOMES_INPUT.json [--csv OUT.csv]   one row per dome (and per side)
  python -I dome_ring.py --check                            synthetic NON-Alsenan fixture with hand values
"""
import csv
import json
import math
import sys

from shapely import affinity
from shapely.geometry import Point, Polygon, box

QUAD = 4096  # quad_segs per quarter circle -> 16384 sides
SIDES = ("W", "E", "S", "N")


def seg(r, d):
    """area of the disc of radius r beyond a straight line at distance d from its centre (d >= 0)."""
    if d >= r:
        return 0.0
    return r * r * math.acos(d / r) - d * math.sqrt(r * r - d * d)


def disc_in_bay(r, faces):
    return math.pi * r * r - sum(seg(r, faces[k]) for k in SIDES)


def _adjacent_ok(r, faces):
    for a in ("W", "E"):
        for b in ("S", "N"):
            if faces[a] ** 2 + faces[b] ** 2 < r * r:
                return False
    return True


def _bay_poly(faces, rot_deg=0.0):
    p = box(-faces["W"], -faces["S"], faces["E"], faces["N"])
    return affinity.rotate(p, rot_deg, origin=(0, 0)) if rot_deg else p


def _disc(r):
    return Point(0, 0).buffer(r, quad_segs=QUAD)


def ring(rec, unit=1.0, t=None, rot_deg=0.0):
    """rec: {r_inner_m, r_outer_m, faces{W,E,S,N: {d_m, far_d_m}}, columns_rel_m, ring_depth_m (None = HELD)}.
    unit: metres per input unit (0.001 for mm). rot_deg: the bay is rotated by this angle (shapely check only;
    the closed form is rotation invariant). Returns a dict of areas (m2) and m3."""
    ri, ro = rec["r_inner_m"] * unit, rec["r_outer_m"] * unit
    if not (0 < ri < ro):
        raise ValueError("ring radii must satisfy 0 < r_inner < r_outer")
    faces = {k: rec["faces"][k]["d_m"] * unit for k in SIDES}
    far = {k: (rec["faces"][k].get("far_d_m") * unit if rec["faces"][k].get("far_d_m") is not None else None)
           for k in SIDES}
    if not _adjacent_ok(ro, faces):
        raise ValueError("two face segments of the outer circle overlap (corner inside the ring): closed form invalid")
    annulus = math.pi * (ro * ro - ri * ri)
    a_ring = disc_in_bay(ro, faces) - disc_in_bay(ri, faces)
    opening = disc_in_bay(ri, faces)
    bay = (faces["W"] + faces["E"]) * (faces["S"] + faces["N"])
    corners = bay - disc_in_bay(ro, faces)
    sides = {}
    for k in SIDES:
        tot = seg(ro, faces[k]) - seg(ri, faces[k])
        beyond = 0.0 if far[k] is None else seg(ro, far[k]) - seg(ri, far[k])
        sides[k] = {"in_member_m2": tot - beyond, "beyond_member_m2": beyond,
                    "opening_in_member_m2": seg(ri, faces[k]) - (0.0 if far[k] is None else seg(ri, far[k]))}
    readd = a_ring + sum(s["in_member_m2"] + s["beyond_member_m2"] for s in sides.values())
    # independent shapely computation
    bp = _bay_poly(faces, rot_deg)
    ann = _disc(ro).difference(_disc(ri))
    a_ring_sh = ann.intersection(bp).area
    open_sh = _disc(ri).intersection(bp).area
    corners_sh = bp.difference(_disc(ro)).area
    cols = []
    for c in rec.get("columns_rel_m") or []:
        cp = box(*(v * unit for v in c))
        if rot_deg:
            cp = affinity.rotate(cp, rot_deg, origin=(0, 0))
        cols.append({"column_rel_m": c, "ring_in_column_m2": ann.intersection(cp).area,
                     "ring_in_column_inside_bay_m2": ann.intersection(cp).intersection(bp).area,
                     "opening_in_column_m2": _disc(ri).intersection(cp).area})
    diff = max(abs(a_ring - a_ring_sh), abs(opening - open_sh), abs(corners - corners_sh), abs(readd - annulus))
    out = {"annulus_full_m2": annulus, "ring_in_bay_m2": a_ring, "ring_in_bay_shapely_m2": a_ring_sh,
           "ring_outside_bay_m2": annulus - a_ring, "opening_in_bay_m2": opening, "bay_m2": bay,
           "slab_corners_m2": corners, "sides": sides, "columns": cols, "readd_m2": readd, "max_method_diff_m2": diff}
    D = rec.get("ring_depth_m")
    D = None if D is None else D * unit
    if D is None:
        out.update(status="HELD", ring_m3=None, slab_share_m3=None, downstand_m3=None)
        cd = rec.get("candidate_depth_m")
        out["candidate_m3"] = None if cd is None else a_ring * cd * unit
    else:
        out.update(status="CALCULATED", ring_m3=a_ring * D)
        if t is not None:
            out.update(slab_share_m3=a_ring * t, downstand_m3=a_ring * (D - t))
        out["full_annulus_m3"] = annulus * D
        out["double_count_avoided_m3"] = (annulus - a_ring) * D
    return out


# ---------------------------------------------------------------- synthetic NON-Alsenan fixture (hand values)
# Hand values worked with the segment formula (r^2 acos(d/r) - d sqrt(r^2 - d^2)) on a calculator, 6 decimals:
#  F1 square bay 4.00 x 4.00 (faces 2.00 all round), ring r 1.90 / 2.10 (crosses all four straight beams):
#     annulus = pi (2.10^2 - 1.90^2) = pi x 0.80                                   = 2.513274
#     seg(2.10, 2.00) = 4.41 x acos(0.952381) - 2.00 x sqrt(0.41)
#                     = 4.41 x 0.309845 - 2.00 x 0.640312 = 1.366415 - 1.280625    = 0.085790  (x 4 = 0.343160)
#     inner circle 1.90 < 2.00: no segment; ring in bay = 2.513274 - 0.343160       = 2.170114
#     beams 0.25 wide: far face 2.25 > 2.10, nothing beyond. D 0.60, t 0.15:
#     ring 2.170114 x 0.60 = 1.302068 m3 (gross) = slab share x 0.15 = 0.325517 + downstand x 0.45 = 0.976551;
#     the full annulus (1.507964 m3) would double count (2.513274 - 2.170114) x 0.60 = 0.205896 m3.
#  F2 asymmetric bay (mirror pair): faces W 1.80, E / S / N 2.00; beams 0.20 (far faces W 2.00, E / S / N 2.20):
#     seg(2.10, 1.80) = 4.41 x acos(0.857143) - 1.80 x sqrt(1.17) = 4.41 x 0.541100 - 1.80 x 1.081665
#                     = 2.386249 - 1.946997 = 0.439251
#     seg(1.90, 1.80) = 3.61 x acos(0.947368) - 1.80 x sqrt(0.37) = 3.61 x 0.325883 - 1.80 x 0.608276
#                     = 1.176438 - 1.094897 = 0.081540
#     W side: annulus beyond the face 0.439251 - 0.081540 = 0.357711; beyond the W beam's far face (2.00):
#             seg(2.10, 2.00) - 0 = 0.085790 -> in the W beam 0.271921, past it (next panel) 0.085790
#     ring in bay = 2.513274 - 3 x 0.085790 - 0.357711 = 1.898193 (the mirror, W <-> E, gives the same)
#  F3 = F1 in millimetres (unit 0.001): same m2 and m3.  F4 = F1 rotated 30 deg: same m2.
#  F5 = F1 with no ring depth: HELD, m3 None (never 0).  F6 a bay whose corner lies inside the ring: refused.
HAND = {"F1_ring": 2.170114, "F1_m3": 1.302068, "F1_slab": 0.325517, "F1_down": 0.976551, "F1_dc": 0.205896,
        "F2_ring": 1.898193, "F2_W_in": 0.271921, "F2_W_beyond": 0.085790}


def _fx(faces, far, D=0.60):
    return {"r_inner_m": 1.90, "r_outer_m": 2.10,
            "faces": {k: {"d_m": faces[k], "far_d_m": far[k]} for k in SIDES}, "ring_depth_m": D, "columns_rel_m": []}


def check():
    ok = True

    def eq(name, got, want, tol=1.5e-6):
        nonlocal ok
        good = got is not None and abs(got - want) <= tol
        ok &= good
        print(f"{'PASS' if good else 'FAIL'} {name}: {got if got is None else round(got, 6)} vs hand {want}")

    f1 = ring(_fx({k: 2.0 for k in SIDES}, {k: 2.25 for k in SIDES}), t=0.15)
    eq("F1 ring in bay m2", f1["ring_in_bay_m2"], HAND["F1_ring"])
    eq("F1 shapely = closed form", f1["max_method_diff_m2"], 0.0, 1e-6)
    eq("F1 ring m3 (gross)", f1["ring_m3"], HAND["F1_m3"])
    eq("F1 slab share m3", f1["slab_share_m3"], HAND["F1_slab"])
    eq("F1 downstand m3", f1["downstand_m3"], HAND["F1_down"])
    eq("F1 split re-adds to gross", f1["slab_share_m3"] + f1["downstand_m3"], f1["ring_m3"], 1e-9)
    eq("F1 full annulus would double count m3", f1["double_count_avoided_m3"], HAND["F1_dc"])
    eq("F1 re-add annulus", f1["readd_m2"], f1["annulus_full_m2"], 1e-9)
    f2 = ring(_fx({"W": 1.8, "E": 2.0, "S": 2.0, "N": 2.0}, {"W": 2.0, "E": 2.2, "S": 2.2, "N": 2.2}))
    eq("F2 ring in bay m2", f2["ring_in_bay_m2"], HAND["F2_ring"])
    eq("F2 W in member m2", f2["sides"]["W"]["in_member_m2"], HAND["F2_W_in"])
    eq("F2 W beyond the member (next panel) m2", f2["sides"]["W"]["beyond_member_m2"], HAND["F2_W_beyond"])
    eq("F2 shapely = closed form", f2["max_method_diff_m2"], 0.0, 1e-6)
    f2m = ring(_fx({"W": 2.0, "E": 1.8, "S": 2.0, "N": 2.0}, {"W": 2.2, "E": 2.0, "S": 2.2, "N": 2.2}))
    eq("F2 mirror: same ring m2", f2m["ring_in_bay_m2"], HAND["F2_ring"])
    eq("F2 mirror: E side carries what W carried", f2m["sides"]["E"]["in_member_m2"], HAND["F2_W_in"])
    mm = {"r_inner_m": 1900.0, "r_outer_m": 2100.0, "ring_depth_m": 600.0, "columns_rel_m": [],
          "faces": {k: {"d_m": 2000.0, "far_d_m": 2250.0} for k in SIDES}}
    f3 = ring(mm, unit=0.001)
    eq("F3 mm input: ring m2", f3["ring_in_bay_m2"], HAND["F1_ring"])
    eq("F3 mm input: ring m3", f3["ring_m3"], HAND["F1_m3"])
    f4 = ring(_fx({k: 2.0 for k in SIDES}, {k: 2.25 for k in SIDES}), rot_deg=30.0)
    eq("F4 rotated 30 deg: shapely ring m2", f4["ring_in_bay_shapely_m2"], HAND["F1_ring"])
    f5 = ring(_fx({k: 2.0 for k in SIDES}, {k: 2.25 for k in SIDES}, D=None))
    good = f5["status"] == "HELD" and f5["ring_m3"] is None
    ok &= good
    print(f"{'PASS' if good else 'FAIL'} F5 missing ring depth stays HELD, m3 None (never 0): {f5['status']} {f5['ring_m3']}")
    try:
        ring(_fx({k: 1.4 for k in SIDES}, {k: 1.6 for k in SIDES}))
        good = False
    except ValueError:
        good = True
    ok &= good
    print(f"{'PASS' if good else 'FAIL'} F6 corner inside the ring is refused (closed form not valid), never guessed")
    try:
        ring({"r_inner_m": 2.1, "r_outer_m": 1.9, "faces": {k: {"d_m": 2.0, "far_d_m": 2.2} for k in SIDES}})
        good = False
    except ValueError:
        good = True
    ok &= good
    print(f"{'PASS' if good else 'FAIL'} F7 inner radius >= outer radius refused")
    print("CHECK", "PASS" if ok else "FAIL")
    return ok


def run(path, out_csv=None):
    d = json.load(open(path))
    rows = []
    for rec in d["domes"]:
        r = ring(rec, unit=d.get("unit_m", 1.0), t=d.get("slab_t_m"))
        base = {"dome": rec["id"], "status": r["status"], "annulus_full_m2": round(r["annulus_full_m2"], 4),
                "ring_in_bay_m2": round(r["ring_in_bay_m2"], 4), "ring_outside_bay_m2": round(r["ring_outside_bay_m2"], 4),
                "opening_in_bay_m2": round(r["opening_in_bay_m2"], 4), "slab_corners_m2": round(r["slab_corners_m2"], 4),
                "bay_m2": round(r["bay_m2"], 4), "readd_m2": round(r["readd_m2"], 4),
                "method_diff_m2": f"{r['max_method_diff_m2']:.1e}",
                "ring_depth_m": rec.get("ring_depth_m"), "ring_m3": None if r["ring_m3"] is None else round(r["ring_m3"], 4),
                "slab_share_m3": None if r.get("slab_share_m3") is None else round(r["slab_share_m3"], 4),
                "downstand_m3": None if r.get("downstand_m3") is None else round(r["downstand_m3"], 4),
                "candidate_m3": None if r.get("candidate_m3") is None else round(r["candidate_m3"], 4),
                "full_annulus_m3": None if r.get("full_annulus_m3") is None else round(r["full_annulus_m3"], 4),
                "double_count_avoided_m3": None if r.get("double_count_avoided_m3") is None else
                round(r["double_count_avoided_m3"], 4)}
        print(json.dumps(base))
        rows.append(dict(base, part="DOME"))
        for k in SIDES:
            s, f = r["sides"][k], rec["faces"][k]
            row = {"dome": rec["id"], "part": f"SIDE {k}", "member": f["member"], "register": f["register"],
                   "d_m": f["d_m"], "far_d_m": f["far_d_m"], "ring_in_member_m2": round(s["in_member_m2"], 4),
                   "ring_beyond_member_m2": round(s["beyond_member_m2"], 4),
                   "beyond_is": (rec.get("beyond") or {}).get(k, ""),
                   "opening_in_member_m2": round(s["opening_in_member_m2"], 4)}
            print("  ", json.dumps(row))
            rows.append(row)
        for c in r["columns"]:
            row = {"dome": rec["id"], "part": "COLUMN", "column_rel_m": c["column_rel_m"],
                   "ring_in_column_m2": round(c["ring_in_column_m2"], 4),
                   "ring_in_column_inside_bay_m2": round(c["ring_in_column_inside_bay_m2"], 4),
                   "opening_in_column_m2": round(c["opening_in_column_m2"], 4)}
            print("  ", json.dumps(row))
            rows.append(row)
    if out_csv:
        keys = []
        for row in rows:
            keys += [k for k in row if k not in keys]
        with open(out_csv, "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=keys)
            w.writeheader()
            w.writerows(rows)
    return rows


if __name__ == "__main__":
    a = sys.argv[1:]
    if a and a[0] == "--check":
        sys.exit(0 if check() else 1)
    run(a[0], a[a.index("--csv") + 1] if "--csv" in a else None)
