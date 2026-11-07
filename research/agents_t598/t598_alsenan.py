"""T-598 development-villa reading: the 20 HELD nosing edges of the T-412 census, closed by name (Alsenan is one sample;
the method is edge_classes.py).

Build (needs PRIVATE inputs decoded into .work/private only: Drive "Alsenan chalet project" P7757_DXF_COMPRESSED.zip
(architectural DXF) and "ST7757 dxf.dxf" (structural DXF)):
    python3 -I research/agents_t598/t598_alsenan.py --dxf <P7757.dxf> --st <ST7757.dxf> --write
reads every entity BY HANDLE with a plain group-code reader (no CAD library needed), asserts layer / length / pairing,
converts to run positions (metres from the stair's north wall face), lengths, radii and sweeps (no drawing coordinates)
and writes ALSENAN_EDGES_T598.json. Check (no private input):
    python3 -I research/agents_t598/t598_alsenan.py --check
recomputes every class, the lm per class and the reconciliation against the freelancer from the committed JSON and
prints REPRODUCED. Compare (private input; used by the test):
    python3 -I research/agents_t598/t598_alsenan.py --dxf <P7757.dxf> --st <ST7757.dxf> --compare
re-reads the drawings and prints SAME AS COMMITTED when the reading equals the committed JSON.
No drawing text, client name, image or workbook row text is written; freelancer figures are quantities only (T-578).
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import edge_classes as E  # noqa: E402

OUT = HERE / "ALSENAN_EDGES_T598.json"
MM = 0.001

# T-412 (MERGED f9c80501) + T-434 (MERGED a6b325b3) state this task starts from.
T412_CONFIRMED_LM = 87.350           # 69 edges
T434_N05_LM = 1.150                  # MS1-T landing nosing 2C6, DRAWING-CONFIRMED by T-434
T412_BY_STAIR = {"ST-01": 55.100, "ST-02": 18.250, "ST-03": 14.000}   # confirmed lm per stair (T-412 s.2)
T412_EDGES_BY_STAIR = {"ST-01": 48, "ST-02": 16, "ST-03": 5}
T412_NOTCHES = {"ST-01": 0.100, "ST-02": 0.150, "ST-03": 0.0}          # columns proud of the edge (T-412 / T-410)
# Freelancer (T-578 s.2, quantities only): pieces x width per stair.
HIS = {"ST-01": (63, 1.20), "ST-02": (28, 1.20), "ST-03": (5, 2.80)}
DRAWN_RISERS = {"ST-01": 56, "ST-02": 28, "ST-03": 5}                 # Q-46 A section + D1 4; Q-50 A cond; plan


# ---------------------------------------------------------------- plain DXF reader (group codes, by handle)
def read_handles(path: str, wanted: set[str]) -> dict:
    lines = Path(path).read_text(encoding="utf-8", errors="replace").splitlines()
    out, cur = {}, None
    for i in range(0, len(lines) - 1, 2):
        code, val = lines[i].strip(), lines[i + 1].strip()
        if code == "0":
            if cur and cur.get("5", [None])[0] in wanted:
                out[cur["5"][0]] = cur
            cur = {"type": val}
        elif cur is not None:
            cur.setdefault(code, []).append(val)
    if cur and cur.get("5", [None])[0] in wanted:
        out[cur["5"][0]] = cur
    missing = wanted - set(out)
    assert not missing, f"handles not found: {sorted(missing)}"
    return out


def line(H, h, layer=None):
    e = H[h]
    assert e["type"] == "LINE", (h, e["type"])
    if layer is not None:
        assert e["8"][0] == layer, (h, e["8"][0], layer)
    return (float(e["10"][0]), float(e["20"][0])), (float(e["11"][0]), float(e["21"][0]))


def arc(H, h, layer=None):
    e = H[h]
    assert e["type"] == "ARC", (h, e["type"])
    if layer is not None:
        assert e["8"][0] == layer, (h, e["8"][0], layer)
    return (float(e["10"][0]), float(e["20"][0])), float(e["40"][0]), float(e["50"][0]), float(e["51"][0])


def length(p):
    (a, b), (c, d) = p
    return math.hypot(c - a, d - b)


def r6(x):
    return round(x, 6)


# ---------------------------------------------------------------- handle lists
MS1U_FRONTS = ["A92", "A95", "AA5", "AA6", "AA7", "AA8", "AA9", "AAA", "AAB", "AAC", "ABE"]   # arch 1F, layer 5
MS2U_FRONTS = ["135B", "135E", "136D", "136E", "136F", "1370", "1371", "1372", "1373", "1374", "1386"]  # arch 2F
ST4_EAST = ["25B", "25C", "261", "263", "262", "260", "267", "266", "265", "264", "270", "459"]  # ST p.4 riser faces
ST5_EAST = ["62F", "630", "635", "637", "636", "634", "63B", "63A", "639", "638", "644"]         # ST p.5 riser faces
RSC_FRONTS = ["256", "254", "252", "250", "24E", "24C", "24A", "248", "246", "244", "242", "240"]  # walking order
RSC_FACES = ["257", "255", "253", "251", "24F", "24D", "24B", "249", "247", "245", "243", "241"]
ST_RSC = ["2EA", "2E9", "2E8", "2E7", "2E6", "2E5", "2E4", "2E3", "2E2", "2E1", "2E0", "2DF"]
ARCH = set(MS1U_FRONTS + MS2U_FRONTS + RSC_FRONTS + RSC_FACES + [
    "A8F", "B16", "1358", "129A", "12B4", "12B5", "2F1F", "2F20", "239", "23D", "23E", "23F", "258", "259", "25A", "25B"])
STRUCT = set(ST4_EAST + ST5_EAST + ST_RSC + ["2F3", "25A", "5E2", "62E", "2EB", "2EC"])


def read_cad(arch_path: str, st_path: str) -> dict:
    A = read_handles(arch_path, ARCH)
    S = read_handles(st_path, STRUCT)
    d = {}

    # ---- MS1-U (arch 1F plan): 11 fronts at 0.300; north wall face = the y the turn line BE4 ends on (-791993.54)
    fr = [line(A, h, "5") for h in MS1U_FRONTS]
    north = max(max(p[0][1], p[1][1]) for p in [line(A, "B16", "1")])
    s = [r6((north - p[0][1]) * MM) for p in fr]
    assert all(abs(length(p) - 1150) < 0.01 for p in fr)
    assert all(abs((s[i + 1] - s[i]) - 0.300) < 1e-6 for i in range(10))
    lane_w = line(A, "A8F", "5")
    wall = line(A, "B16", "1")
    d["MS1U"] = {
        "fronts": MS1U_FRONTS, "front_len_m": r6(length(fr[0]) * MM), "s_first": s[0], "s_last": s[-1],
        "going_m": 0.300, "governing_floor_front_s": r6(s[-1] + 0.300),
        "lane_bound_west": {"h": "A8F", "s": sorted([r6((north - lane_w[0][1]) * MM), r6((north - lane_w[1][1]) * MM)])},
        "lane_bound_east": {"h": "B16", "s": sorted([r6((north - wall[0][1]) * MM), r6((north - wall[1][1]) * MM)])},
        "floor_front_line_on_arch_plan": False,
    }
    # ---- ST p.4 east lane: 12 riser faces, the 12th (459) at the floor; north ref = the end of the turn face 2F3
    st4 = [line(S, h, "2") for h in ST4_EAST]
    n4 = max(line(S, "2F3", "2")[0][1], line(S, "2F3", "2")[1][1])
    s4 = [r6((n4 - p[0][1]) * MM) for p in st4]
    assert all(abs(length(p) - 1150) < 0.01 for p in st4)
    op4 = line(S, "25A", "S-OPENING")
    d["ST4"] = {"faces": ST4_EAST, "count": len(st4), "s_faces": s4, "s_459": s4[-1],
                "opening_south_s": r6((n4 - min(op4[0][1], op4[1][1])) * MM)}
    # ---- MS2-U (arch 2F): 11 fronts, no 12th line; MS2-TR pair 12B4 / 12B5; the diagonal pair 2F1F / 2F20
    fr2 = [line(A, h, "5") for h in MS2U_FRONTS]
    north2 = max(line(A, "12B4", "5")[0][1], line(A, "12B4", "5")[1][1])
    s2 = [r6((north2 - p[0][1]) * MM) for p in fr2]
    assert all(abs(length(p) - 1150) < 0.01 for p in fr2)
    assert all(abs((s2[i + 1] - s2[i]) - 0.300) < 1e-6 for i in range(10))
    lw2 = line(A, "1358", "5")
    w2 = line(A, "129A", "1")
    tr, tf = line(A, "12B4", "5"), line(A, "12B5", "2")
    dg, df = line(A, "2F1F", "5"), line(A, "2F20", "2")
    # perpendicular offset of the face from the diagonal front
    (ax, ay), (bx, by) = dg
    nx, ny = (by - ay), -(bx - ax)
    nl = math.hypot(nx, ny)
    off = abs(((df[0][0] - ax) * nx + (df[0][1] - ay) * ny) / nl)
    d["MS2U"] = {
        "fronts": MS2U_FRONTS, "front_len_m": r6(length(fr2[0]) * MM), "s_first": s2[0], "s_last": s2[-1],
        "governing_floor_front_s": r6(s2[-1] + 0.300),
        "lane_bound_west": {"h": "1358", "s": sorted([r6((north2 - lw2[0][1]) * MM), r6((north2 - lw2[1][1]) * MM)])},
        "lane_bound_east": {"h": "129A", "s": sorted([r6((north2 - w2[0][1]) * MM), r6((north2 - w2[1][1]) * MM)])},
        "floor_front_line_on_arch_plan": False,
    }
    d["MS2TR"] = {
        "front": "12B4", "face": "12B5", "front_len_m": r6(length(tr) * MM), "face_offset_m": r6(abs(tf[0][0] - tr[0][0]) * MM),
        "front_s_span": sorted([r6((north2 - tr[0][1]) * MM), r6((north2 - tr[1][1]) * MM)]),
        "front_to_east_lane_edge_m": r6(abs(lw2[0][0] - tr[0][0]) * MM),
        "diagonal": {"front": "2F1F", "face": "2F20", "len_m": r6(length(dg) * MM), "face_offset_m": r6(off * MM),
                     "on_structural_plan": False},
    }
    # ---- ST p.5: 11 east riser faces, the closing-riser face 5E2, the slab opening end
    st5 = [line(S, h, "2") for h in ST5_EAST]
    e2 = line(S, "5E2", "2")
    n5 = max(e2[0][1], e2[1][1])
    s5 = [r6((n5 - p[0][1]) * MM) for p in st5]
    op5 = line(S, "62E", "S-OPENING")
    lane5_west = min(st5[0][0][0], st5[0][1][0])
    d["ST5"] = {"faces": ST5_EAST, "count": len(st5), "s_faces": s5,
                "opening_south_s": r6((n5 - min(op5[0][1], op5[1][1])) * MM),
                "tr_face": "5E2", "tr_face_len_m": r6(length(e2) * MM),
                "tr_face_to_east_lane_edge_m": r6((lane5_west - e2[0][0]) * MM)}
    # ---- RS-C (arch GF plan): 12 radial fronts, bands, curtail arcs; ST p.4 radial faces and curtail faces
    c239 = arc(A, "239", "5")
    cen = c239[0]

    def rad(p):
        return [r6(math.hypot(p[0][0] - cen[0], p[0][1] - cen[1]) * MM), r6(math.hypot(p[1][0] - cen[0], p[1][1] - cen[1]) * MM)]

    fronts = {h: line(A, h, "5") for h in RSC_FRONTS}
    d["RSC"] = {
        "fronts": {h: {"len_m": r6(length(p) * MM), "r": sorted(rad(p))} for h, p in fronts.items()},
        "inner_r": r6(c239[1] * MM), "inner_band_r": r6(arc(A, "23F", "5")[1] * MM),
        "outer_r": r6(arc(A, "23D", "5")[1] * MM), "outer_band_r": r6(arc(A, "23E", "5")[1] * MM),
        "outer_band_starts_on_256": abs(arc(A, "23D", "5")[2] - math.degrees(math.atan2(
            fronts["256"][0][1] - cen[1], fronts["256"][0][0] - cen[0])) % 360) < 0.01,
    }
    cur = {}
    for front, face, nose_of in (("258", "259", "256"), ("25A", "25B", "254")):
        c, r, a0, a1 = arc(A, front, "5")
        cf, rf, b0, b1 = arc(A, face, "2")
        end_pt = (c[0] + r * math.cos(math.radians(a1)), c[1] + r * math.sin(math.radians(a1)))
        st_pt = (c[0] + r * math.cos(math.radians(a0)), c[1] + r * math.sin(math.radians(a0)))
        inner_end = min(fronts[nose_of], key=lambda q: math.hypot(q[0] - cen[0], q[1] - cen[1]))
        f251 = line(A, "251", "2")
        f251_in = min(f251, key=lambda q: math.hypot(q[0] - cen[0], q[1] - cen[1]))
        cur[front] = {"continues": nose_of, "face": face, "r_m": r6(r * MM), "sweep_deg": r6((a1 - a0) % 360),
                      "len_m": r6(E.arc_length(r * MM, a0, a1)), "chord_m": r6(E.chord(r * MM, a0, a1)),
                      "joins_front_inner_end_mm": r6(math.dist(end_pt, inner_end)),
                      "returns_to_inner_edge_at_251_mm": r6(math.dist(st_pt, f251_in)),
                      "min_r_m": r6((math.dist(c, cen) - r) * MM),
                      "face_r_m": r6(rf * MM), "face_sweep_deg": r6((b1 - b0) % 360)}
    st_cur = {}
    for h in ("2EB", "2EC"):
        c, r, a0, a1 = arc(S, h, "2")
        st_cur[h] = {"r_m": r6(r * MM), "sweep_deg": r6((a1 - a0) % 360)}
    d["RSC"]["curtail"] = cur
    d["RSC"]["st_curtail_faces"] = st_cur
    d["RSC"]["st_radials"] = {"count": len(ST_RSC), "len_m": sorted({r6(length(line(S, h, "2")) * MM) for h in ST_RSC})}
    return d


# ---------------------------------------------------------------- classification (from the reading only)
def checks(d: dict) -> dict:
    """Cross-drawing agreements every class below rests on (each recomputed from the reading)."""
    ms1, ms2, s4, s5, tr, rs = d["MS1U"], d["MS2U"], d["ST4"], d["ST5"], d["MS2TR"], d["RSC"]
    face = 0.050
    return {
        # ST p.4 draws the 12th (floor) riser face exactly where 11 drawn fronts + the section's 12th riser put it
        "ms1u_floor_face_on_st4": s4["count"] == 12 and abs(s4["s_459"] - (ms1["governing_floor_front_s"] + face)) < 1e-6,
        # head clash (position only): governing top riser face minus the slab opening end on each slab plan
        "ms1u_clash_m": r6(s4["s_459"] - s4["opening_south_s"]),
        "ms2u_clash_m": r6(ms2["governing_floor_front_s"] + face - s5["opening_south_s"]),
        "ms2u_floor_on_any_plan": ms2["floor_front_line_on_arch_plan"] or s5["count"] == 12,
        # the closing-riser face: arch 12B5 and ST p.5 5E2 at the same offset from the east lane edge, same length
        "ms2tr_face_agrees": abs((tr["front_to_east_lane_edge_m"] - tr["face_offset_m"]) - s5["tr_face_to_east_lane_edge_m"]) < 1e-6
        and abs(tr["front_len_m"] - s5["tr_face_len_m"]) < 1e-6,
        "rsc_lane_m": r6(rs["outer_r"] - rs["inner_r"]),
        "rsc_st_radials_12": rs["st_radials"]["count"] == 12,
        "rsc_curtail_faces_match_st": all(
            abs(rs["curtail"][a]["face_r_m"] - rs["st_curtail_faces"][b]["r_m"]) < 1e-6
            and abs(rs["curtail"][a]["face_sweep_deg"] - rs["st_curtail_faces"][b]["sweep_deg"]) < 1e-4
            for a, b in (("258", "2EB"), ("25A", "2EC"))),
        "rsc_curtail_joins_fronts": all(rs["curtail"][a]["joins_front_inner_end_mm"] < 1.0 for a in ("258", "25A")),
    }


def compute(d: dict) -> dict:
    ck = checks(d)
    edges = []
    # MS1-T N01..N04: count governed (section A-A, 5 turn risers, T-434), subdivision not drawn -> DESIGNER_ITEM.
    lane = 1.150
    longest = r6(math.hypot(1.150, 1.300))   # the turn region 1.150 x 1.300 between riser faces 486 and 49D (T-434)
    for i in range(1, 5):
        edges.append(E.classify({"id": f"ST01-MS1T-N0{i}", "count_source": "SECTION_OWNER_RULE",
                                 "length_basis": "NOT_DRAWN",
                                 "region": {"n_fronts": 1, "lane_m": lane, "longest_m": longest}}) | {
            "stair": "ST-01", "sheet": "arch GF plan + ST p.4 (3 radial fronts = 4-riser fan) vs section A-A (5 risers)",
            "cause": "WINDER_SUBDIVISION_NOT_DRAWN (R-T434-2, S-9, A8)"})
    # Floor edges: count governed (section A-A 12 risers), length = the lane, invariant over the open position.
    for key, eid, sheet, second, clash, beam in (
            ("MS1U", "ST01-MS1U-FLOOR", "arch 1F plan lane A8F / B16; ST p.4 riser face 459",
             ck["ms1u_floor_face_on_st4"], ck["ms1u_clash_m"], "B20"),
            ("MS2U", "ST01-MS2U-FLOOR", "arch 2F plan lane 1358 / 129A; not drawn on ST p.5",
             ck["ms2u_floor_on_any_plan"], ck["ms2u_clash_m"], "B23")):
        m = d[key]
        # the open position range: the governing position .. the slab opening end (the clash), both inside the lane
        pos = [m["governing_floor_front_s"], r6(m["governing_floor_front_s"] - clash)]
        rng = (min(pos), max(pos))
        c = E.classify({"id": eid, "count_source": "SECTION_OWNER_RULE", "length_basis": "LANE_INVARIANT",
                        "lane_bounds": [tuple(m["lane_bound_west"]["s"]), tuple(m["lane_bound_east"]["s"])],
                        "position_range": rng, "length_m": m["front_len_m"],
                        "position_conflict": f"head clash: the governing 12th riser face lies {clash:.3f} inside the "
                                             f"slab opening end ({beam}, Q-46 RFI): position only"})
        edges.append(c | {"stair": "ST-01", "sheet": sheet, "second_drawing_draws_it": second,
                          "position_range_s": list(rng), "cause": "FLOOR_EDGE (R-T412-1 one riser one nosing)"})
    # MS2-TR: one closing riser (section A-A); 12B4 drawn on arch 2F, its face 12B5 = ST p.5 5E2 (same offset from the
    # east lane edge); the diagonal 2F1F is on one drawing only and the governing count admits one riser.
    t = d["MS2TR"]
    if not ck["ms2tr_face_agrees"]:   # no second drawing places 12B4: the two drawn fronts are two readings
        edges.append(E.classify({"id": "ST01-MS2TR", "count_source": "SECTION_OWNER_RULE",
                                 "length_basis": "TWO_READINGS", "readings_m": [t["front_len_m"], t["diagonal"]["len_m"]]})
                     | {"stair": "ST-01", "sheet": "arch 2F plan 12B4 vs 2F1F", "cause": "CLOSING_RISER"})
    else:
        edges.append(E.classify({"id": "ST01-MS2TR", "count_source": "SECTION_OWNER_RULE", "length_basis": "DRAWN_EDGE",
                             "length_m": t["front_len_m"],
                             "position_conflict": "arch 2F also draws a diagonal front + face pair 2F1F / 2F20 "
                                                  f"({t['diagonal']['len_m']:.6f}) across the east half; not on ST p.5; "
                                                  "the section admits one riser: designer item Q-ST-11, never added"})
                 | {"stair": "ST-01", "sheet": "arch 2F plan 12B4 / 12B5 + ST p.5 5E2",
                    "beside_if_diagonal_were_the_riser_m": t["diagonal"]["len_m"], "cause": "CLOSING_RISER"})
    # RS-C: 12 radial fronts drawn on arch GF + ST p.4 radial faces (count: Q-50 A cond, reconstructed, no section).
    rs = d["RSC"]
    if not ck["rsc_st_radials_12"]:
        raise E.RuleError("RS-C: the structural plan does not carry 12 radial faces: count not reconstructed")
    curtail_ok = ck["rsc_curtail_faces_match_st"] and ck["rsc_curtail_joins_fronts"]
    if not curtail_ok:
        raise E.RuleError("RS-C curtail: front / face pair not confirmed on the second drawing: review, never 0")
    for h in RSC_FRONTS:
        f = rs["fronts"][h]
        in_lane = ck["rsc_lane_m"]
        L = in_lane + (rs["curtail"]["258"]["len_m"] if h == "256" else 0) + (rs["curtail"]["25A"]["len_m"] if h == "254" else 0)
        c = E.classify({"id": f"ST02-RSC-{h}", "count_source": "PLAN_RECONSTRUCTION_OWNER_APPROVED",
                        "length_basis": "DRAWN_EDGE", "length_m": r6(L)})
        c |= {"stair": "ST-02", "sheet": "arch GF plan radial front + ST p.4 radial face (2DF .. 2EA)",
              "in_lane_m": in_lane, "curtail_m": r6(L - in_lane), "drawn_len_m": f["len_m"],
              "cause": "CURVED_FLIGHT (Q-50 A cond)"}
        edges.append(c)
    band = r6(rs["outer_band_r"] - rs["outer_r"])
    edges.append(E.classify({"id": "ST02-RSC-256-BAND", "count_source": "PLAN_RECONSTRUCTION_OWNER_APPROVED",
                             "length_basis": "NOT_DRAWN",
                             "region": {"n_fronts": 1, "lane_m": band, "longest_m": band}}) | {
        "stair": "ST-02", "sheet": "arch GF plan 256 over the outer band 23D / 23E", "bound": (0.0, band),
        "cause": "BAND_KIND_NOT_PRINTED (RL-09): stringer cap / upstand / tread"})

    value = [e for e in edges if e["cls"] == "VALUE"]
    held = [e for e in edges if e["cls"] != "VALUE"]
    named = [e for e in edges if e["id"] != "ST02-RSC-256-BAND"]
    by_status = {}
    for e in value:
        by_status[e["status"]] = r6(by_status.get(e["status"], 0) + e["lm"])
    ours = {st: r6(T412_BY_STAIR[st] + (T434_N05_LM if st == "ST-01" else 0)
                   + sum(e["lm"] for e in value if e["stair"] == st)) for st in T412_BY_STAIR}
    n_valued = {st: T412_EDGES_BY_STAIR[st] + (1 if st == "ST-01" else 0)
                + sum(1 for e in value if e["stair"] == st) for st in T412_BY_STAIR}
    n_held = {st: sum(1 for e in held if e["stair"] == st and e["id"] != "ST02-RSC-256-BAND") for st in T412_BY_STAIR}
    recon = {}
    for st, (cnt, w) in HIS.items():
        his = r6(cnt * w)
        causes = []
        extra = cnt - DRAWN_RISERS[st]
        if extra:
            causes.append(("COUNT his pieces beyond the drawn risers (UNRESOLVED, T-434)", r6(extra * w)))
        if n_held[st]:
            causes.append(("HELD his share opposite our held edges", r6(n_held[st] * w)))
        width_edges = n_valued[st]
        edge_w = 1.150 if st != "ST-03" else 2.800
        if abs(w - edge_w) > 1e-9:
            causes.append(("WIDTH his width vs the drawn front edge (ENGINE_RIGHT)", r6(width_edges * (w - edge_w))))
        if T412_NOTCHES[st]:
            causes.append(("NOTCH columns proud of the edge (ENGINE_RIGHT)", T412_NOTCHES[st]))
        curt = sum(e.get("curtail_m", 0) for e in value if e["stair"] == st)
        if curt:
            causes.append(("CURTAIL developed arc he does not carry (ENGINE_RIGHT on the drawn front + face pair)",
                           -r6(curt)))
        resid = E.residual({"rows": [(cnt, w)]}, causes, ours[st])
        recon[st] = {"his_lm": his, "his_pieces": cnt, "ours_lm": ours[st], "ours_edges_valued": n_valued[st],
                     "ours_edges_held": n_held[st], "his_minus_ours": r6(his - ours[st]),
                     "causes": [{"cause": c, "lm": v} for c, v in causes], "unexplained": r6(resid)}
    total_ours = r6(sum(ours.values()))
    return {
        "checks": ck,
        "edges": edges,
        "named_held_edges_closed": len(named),
        "value_lm_by_status": by_status,
        "value_lm": r6(sum(e["lm"] for e in value)),
        "designer_or_conflict": [{"id": e["id"], "cls": e["cls"], "bound": e["bound"]} for e in held],
        "held_bound_lm": [r6(sum(e["bound"][0] for e in held)), r6(sum(e["bound"][1] for e in held))],
        "nosing_after": {"valued_lm": total_ours, "edges_valued": sum(n_valued.values()),
                         "edges_held": sum(n_held.values())},
        "reconciliation": recon,
        "his_total": r6(sum(c * w for c, w in HIS.values())),
        "his_minus_ours_total": r6(sum(c * w for c, w in HIS.values()) - total_ours),
    }


def main(argv):
    if "--check" in argv:
        data = json.loads(OUT.read_text())
        res = compute(data["reading"])
        ok = json.dumps(res, sort_keys=True) == json.dumps(data["result"], sort_keys=True)
        print("REPRODUCED" if ok else "DIFFERS")
        return 0 if ok else 1
    dxf = argv[argv.index("--dxf") + 1]
    st = argv[argv.index("--st") + 1]
    reading = read_cad(dxf, st)
    if "--compare" in argv:
        data = json.loads(OUT.read_text())
        ok = json.dumps(reading, sort_keys=True) == json.dumps(data["reading"], sort_keys=True)
        print("SAME AS COMMITTED" if ok else "DIFFERS FROM COMMITTED")
        return 0 if ok else 1
    res = compute(reading)
    blob = {"task": "T-598", "sources": ["Drive 'Alsenan chalet project' P7757_DXF_COMPRESSED.zip (architectural DXF)",
                                         "Drive 'Alsenan chalet project' ST7757 dxf.dxf (structural DXF)"],
            "reading": reading, "result": res}
    if "--write" in argv:
        OUT.write_text(json.dumps(blob, indent=1, sort_keys=True) + "\n")
    print(json.dumps(res, indent=1, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
