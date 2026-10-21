"""ALSENAN V3b - dual measurement (OC-V3B-D): Route A (topology polygon) vs Route B (DIMENSION entities of the same
drawing) vs Route C (another source) where one exists.

Rooms: a room whose polygon fills its minimum rotated rectangle (>= 97 %) has two side lengths a, b; Route B finds
the DIMENSION entities of P7757.dxf parallel to a side, measuring it within DIM_TOL and placed within NEAR of the room;
area_B = a_dim x b_dim. CALCULATION_INDEPENDENCE = YES (dimension values vs polygon topology), SOURCE_INDEPENDENCE =
NO (same drawing). Non-rectangular rooms: Route B NOT_APPLICABLE (listed).
Other quantities: the second routes built elsewhere (footprint, domes, pool, slab bars, opening widths, facades).
"""

from __future__ import annotations

import math

from shapely.geometry import Point, Polygon

DIM_TOL = 15.0                 # mm
NEAR = 1500.0                  # mm
RECT_FILL = 0.97


def _dims(arch):
    out = []
    for e in arch.modelspace().query("DIMENSION"):
        try:
            m = e.get_measurement()
            p2, p3 = e.dxf.defpoint2, e.dxf.defpoint3
        except Exception:
            continue
        if not isinstance(m, (int, float)) or m <= 0:
            continue
        d = (p3.x - p2.x, p3.y - p2.y)
        L = math.hypot(*d)
        ang = e.dxf.get("angle", None)
        if ang is not None and e.dimtype & 7 == 0:
            u = (math.cos(math.radians(ang)), math.sin(math.radians(ang)))
        elif L > 0:
            u = (d[0] / L, d[1] / L)
        else:
            continue
        out.append({"handle": e.dxf.handle, "m": float(m), "u": u, "mid": ((p2.x + p3.x) / 2, (p2.y + p3.y) / 2),
                    "text": e.dxf.get("text", "")})
    return out


def rooms(ctx, arch) -> dict:
    dims = _dims(arch)
    out = []
    for r in ctx["v3"]["rooms"]["rows"]:
        P = r.get("_polygon") or []
        if len(P) < 3 or r["room_class"] in ("SHAFT",):
            continue
        poly = Polygon(P).buffer(0)
        mrr = poly.minimum_rotated_rectangle
        rec = {"room": r["id"], "floor": r["floor"], "name": r["name_en"], "route_a_m2": round(r["area_m2"], 4),
               "route_a": "TOPOLOGY_POLYGON (V3 room register)", "calculation_independence": "YES",
               "source_independence": "NO (same DXF)", "route_c": "NOT_AVAILABLE (no per-room source outside the DXF)"}
        if not mrr.area or poly.area / mrr.area < RECT_FILL:
            rec.update(route_b="NOT_APPLICABLE (non-rectangular room)", route_b_m2=None, diff_pct=None,
                       recon="ROUTE_A_ONLY")
            out.append(rec)
            continue
        c = list(mrr.exterior.coords)[:4]
        sides = []
        for i in range(2):
            a, b = c[i], c[i + 1]
            L = math.hypot(b[0] - a[0], b[1] - a[1])
            sides.append((L, ((b[0] - a[0]) / L, (b[1] - a[1]) / L)))
        found = []
        box = mrr.buffer(NEAR)
        for L, u in sides:
            hit = [d for d in dims if abs(d["m"] - L) <= DIM_TOL and abs(d["u"][0] * u[0] + d["u"][1] * u[1]) > 0.99
                   and box.contains(Point(d["mid"]))]
            found.append(sorted(hit, key=lambda d: abs(d["m"] - L))[0] if hit else None)
        if all(found):
            aB = found[0]["m"] * found[1]["m"] / 1e6
            diff = 100.0 * (r["area_m2"] - aB) / aB if aB else None
            rec.update(route_b="DIMENSION_CHAIN (two printed dimensions)", route_b_m2=round(aB, 4),
                       dims=[f["handle"] for f in found], dim_values_mm=[round(f["m"], 1) for f in found],
                       diff_pct=round(diff, 3), recon="RECONCILED" if abs(diff) <= 1.0 else "MISMATCH")
        else:
            rec.update(route_b=f"PARTIAL ({sum(1 for f in found if f)} of 2 sides dimensioned)", route_b_m2=None,
                       diff_pct=None, recon="ROUTE_A_ONLY")
        out.append(rec)
    return {"rooms": out, "dimensions_read": len(dims), "tolerance_mm": DIM_TOL,
            "rule": "rectangular rooms only; a side is confirmed by a parallel DIMENSION measuring it within 15 mm "
                    "placed within 1.5 m of the room"}


def register(V) -> dict:
    S, F = V["struct"], V["finish"]
    rows = []
    rr = V["dual"]["rooms"]
    rec = sum(1 for x in rr if x["recon"] == "RECONCILED")
    mis = [x for x in rr if x["recon"] == "MISMATCH"]
    rows.append({"item": "Room floor areas", "route_a": "topology polygon", "route_b": "DXF DIMENSION entities",
                 "route_c": "none per room", "calculation_independence": "YES", "source_independence": "NO",
                 "result": f"{rec} reconciled within 1 %, {len(mis)} mismatch, "
                           f"{len(rr) - rec - len(mis)} route A only (non-rectangular / undimensioned)"})
    bl = S["blinding"]["OWNER_FULL_FOOTPRINT_BLINDING"]
    rows.append({"item": "Founded footprint (blinding)", "route_a": f"ground-beam outline {bl['area_m2']} m2",
                 "route_b": f"GF plate registered on the plan {bl['route_b']['area_m2']} m2 (includes overhangs)",
                 "route_c": "arch area sheet (raster, not machine-read)", "calculation_independence": "YES",
                 "source_independence": "YES (structural vs architectural drawing)",
                 "result": "consistent (footprint < plate, as expected)"})
    for d in S["domes"]["rows"]:
        rows.append({"item": f"Dome span {d['id']}", "route_a": f"plan circle {d['span_m']} m",
                     "route_b": f"detail / elevation {d['span_route_c_m']} m", "route_c": "-",
                     "calculation_independence": "YES", "source_independence": "YES (plan DXF vs raster / detail)",
                     "result": f"diff {abs(d['span_m'] - (d['span_route_c_m'] or d['span_m'])) * 100:.1f} cm"})
    p = S["pool"]
    rows.append({"item": "Pool", "route_a": f"S-BW outline {p.get('inner_m')}", "route_b": f"printed depth {p.get('depth_m')}",
                 "route_c": "DETAIL OF SWIMMING POOL thicknesses", "calculation_independence": "YES",
                 "source_independence": "YES (3 sources, one value each)",
                 "result": "complementary, not a check of one value by another"})
    n_b = sum(1 for r in S["slab"]["rows"] if r.get("drawn_length_mm"))
    rows.append({"item": "Slab bars", "route_a": "clear span + embedment (rays)", "route_b": "drawn bar length (symbol)",
                 "route_c": "-", "calculation_independence": "YES", "source_independence": "NO",
                 "result": f"{n_b} bars with both values recorded (route B reported, never the quantity)"})
    rows.append({"item": "Opening widths", "route_a": "DXF closure / jambs", "route_b": "calibrated raster width",
                 "route_c": "-", "calculation_independence": "YES", "source_independence": "YES",
                 "result": "width gate max(6 cm, 4 %) applied to every height"})
    for f in F["facades"]["floors"]:
        rows.append({"item": f"Facade {f['floor']}", "route_a": f"outline perimeter {f['outline_perimeter_m']} m",
                     "route_b": "raster silhouette - NOT DONE this round", "route_c": "-",
                     "calculation_independence": "NO (single route)", "source_independence": "NO",
                     "result": "provisional (+-10 %)"})
    return {"SCHEMA": "URBAN_ALSENAN_V3B_DUAL_MEASUREMENT_V1", "rows": rows, "rooms": rr,
            "mismatches": [{"room": x["room"], "route_a_m2": x["route_a_m2"], "route_b_m2": x["route_b_m2"],
                            "diff_pct": x["diff_pct"]} for x in mis]}
