"""T-324 builder: the parapet composite component ledger of the development villa (Alsenan), every component once.

Inputs (all in the repository, merged or cited): research/agents_t311 (PARAPET_RUN_LEDGER_T311.csv,
COMPONENT_OWNER_T311.csv: merged bd7b8c23), research/agents_t305/ITEMS_T305.csv (merged 9d71ef09),
research/agents_t172/VERTICAL_CORNERS_T172.csv (merged), MEASURED_T324.json (entity lengths read in this run from
Drive 'Alsenan chalet project' / P7757_DXF_COMPRESSED.zip, P7757.dxf sha256 ab54dd55: handles and lengths only).

  python3 -I research/agents_t324/t324_alsenan.py --measure <P7757.dxf>   # re-read the handles -> MEASURED_T324.json
  python3 -I research/agents_t324/t324_alsenan.py --write | --check
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from parapet_components import Book, Row, inner_face_split, top_surface, UPTURN_H  # noqa: E402

HANDLES = {  # handle -> what it is (P7757.dxf, model space; mm)
    "B34": "annex roof: boundary parapet inner face (layer 5), full run to the divider",
    "CEC": "annex roof: divider west face (layer 5), runs to the outer boundary line",
    "CED": "annex roof: divider east face (layer 5)",
    "AC7": "boundary / parapet outer line (layer 5), neighbour side",
    "B3A": "house SW wall face (layer 1) on the annex roof",
    "B3C": "D band edge (layer D) on the annex roof",
    "B35": "annex roof: north parapet inner face (layer 5), stops on the D band",
    "12A7": "1F roof +9.70: sea-side parapet inner face (layer 5), straight",
    "12A5": "1F roof +9.70: sea-side 0.20 wall line (layer 2) south part",
    "131C": "1F roof +9.70: sea-side 0.20 wall line (layer 2) middle part",
    "131B": "1F roof +9.70: sea-side 0.20 wall line (layer 2) north part",
    "12B9": "1F roof +9.70: SW-2 parapet inner face (layer 5), stops on the D band",
    "12E2": "1F roof +9.70: D band edge (layer D)",
    "B25": "GF terrace +5.50: NE-4 parapet inner face (layer 5), from the divider east face",
    "B33": "GF terrace +5.50: NW-7 parapet inner line (layer 5)",
    "BDB": "GF terrace +5.50: SW-9 parapet inner face (layer 5), stops on a D-band curve",
    "C9E": "GF terrace +5.50: D band (layer D)",
}
DXF_SHA8 = "ab54dd55"
# The sea-side parapet plan outline on the +9.70 roof (layer 5, handles 1308 / 130F / 130E / 1312 / 1310 / 1311 / 12A6 /
# 1315 / 1316 / 1317 / 1318 / 130D / 1314 / 130C / 1313), as x (m, outward from 12A7) over y (m, along 12A7).
SEA_PROFILE = [  # (y0, y1, kind, a, b, c): flat x=a, or quarter arc centre (a, b) radius c (outer half)
    (0.0, 5.4871, "flat", 0.3, None, None),
    (5.4871, 5.7923, "arc", 0.3, 5.7923, 0.3052),
    (5.7923, 6.3923, "flat", 0.6052, None, None),
    (6.3923, 6.4923, "arc", 0.5052, 6.3923, 0.1),
    (6.4923, 6.9923, "flat", 0.2, None, None),
    (6.9923, 7.4203, "flat", 0.4983, None, None),
    (7.4203, 7.4703, "flat", 0.4983, None, None),
    (7.4703, 11.4297, "flat", 0.5483, None, None),
    (11.4297, 11.5017, "flat", 0.4983, None, None),
    (11.5017, 11.6, "arc", 0.2, 11.5017, 0.2983),
]

F = lambda v: f"{v:.6f}" if v is not None else ""  # noqa: E731


def _rows(path):
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def measure(dxf_path):
    import ezdxf
    sha = hashlib.sha256(open(dxf_path, "rb").read()).hexdigest()[:8]
    if sha != DXF_SHA8:
        raise SystemExit(f"P7757.dxf sha {sha} != {DXF_SHA8}")
    doc = ezdxf.readfile(dxf_path)
    out = {"source": "Drive 'Alsenan chalet project' / P7757_DXF_COMPRESSED.zip -> P7757.dxf", "sha256_8": sha,
           "units": "m (drawing mm / 1000)", "handles": {}}
    for h, what in HANDLES.items():
        e = doc.entitydb.get(h)
        a, b = e.dxf.start, e.dxf.end
        out["handles"][h] = {"layer": e.dxf.layer, "length_m": round((a - b).magnitude / 1000.0, 6), "what": what}
    # relations needed by the ledger (differences only, no coordinates)
    g = lambda h, k: getattr(doc.entitydb.get(h).dxf, k)  # noqa: E731
    out["relations"] = {
        "B34_east_end_on_CEC_m": round(abs(g("B34", "start").x - g("CEC", "start").x) / 1000.0, 6),
        "B3A_to_CEC_m": round(abs(g("CEC", "start").x - g("B3A", "start").x) / 1000.0, 6),
        "divider_thickness_CEC_CED_m": round(abs(g("CED", "start").x - g("CEC", "start").x) / 1000.0, 6),
        "AC7_offset_from_B34_m": round(abs(g("AC7", "start").y - g("B34", "start").y) / 1000.0, 6),
        "CEC_reaches_AC7": abs(min(g("CEC", "start").y, g("CEC", "end").y) - g("AC7", "start").y) < 1.0,
        "B35_west_of_D_band_gap_m": round(abs(g("B3A", "start").x - g("B3C", "start").x) / 1000.0, 6),
        "B35_ends_on_D_band": abs(max(g("B35", "start").x, g("B35", "end").x) - g("B3C", "start").x) < 1.0,
        "12B9_ends_on_D_band": abs(max(g("12B9", "start").x, g("12B9", "end").x) - g("12E2", "start").x) < 1.0,
        "B25_ends_on_CED": abs(min(g("B25", "start").x, g("B25", "end").x) - g("CED", "start").x) < 1.0,
        "BDB_ends_on_C9E": abs(min(g("BDB", "start").x, g("BDB", "end").x) - g("C9E", "start").x) < 1.0,
        "divider_length_CED_m": round(abs(g("CED", "start").y - g("CED", "end").y) / 1000.0, 6),
        "sea_wall_line_offset_from_12A7_m": round(abs(g("12A5", "start").x - g("12A7", "start").x) / 1000.0, 6),
    }
    path = os.path.join(HERE, "MEASURED_T324.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1, sort_keys=True)
        fh.write("\n")
    print(json.dumps(out["relations"], indent=1))


def sea_plan_area(y1=11.6, n=116000):
    import math
    tot = 0.0
    h = y1 / n
    for i in range(n):
        y = (i + 0.5) * h
        for y0, ya, kind, a, b, c in SEA_PROFILE:
            if y0 <= y < ya:
                x = a if kind == "flat" else a + math.sqrt(max(0.0, c * c - (y - b) ** 2))
                break
        tot += x * h
    return tot


def build():
    M = json.load(open(os.path.join(HERE, "MEASURED_T324.json"), encoding="utf-8"))
    H = {k: v["length_m"] for k, v in M["handles"].items()}
    R = M["relations"]
    runs = _rows(os.path.join(RES, "agents_t311", "PARAPET_RUN_LEDGER_T311.csv"))
    owner = {r["component"]: r for r in _rows(os.path.join(RES, "agents_t311", "COMPONENT_OWNER_T311.csv"))}
    by = {(r["chain"], r["side"]): r for r in runs}
    corrections = []

    def corr(cid, chain, side, comp, unit, d_lo, d_hi, evidence, status):
        corrections.append({"id": cid, "chain": chain, "side": side, "component": comp, "unit": unit,
                            "delta_lo": d_lo, "delta_hi": d_hi, "evidence": evidence, "status": status})

    # --- per-run geometry, corrected where this run re-measured the drawn line --------------------------------------
    geo = {}
    for r in runs:
        k = (r["chain"], r["side"])
        h_lo = float(r["h_above_finish_m"] or r["h_held_lo"])
        h_hi = float(r["h_above_finish_m"] or r["h_held_hi"])
        geo[k] = {"inner_lo": float(r["inner_top_arris_m"]), "inner_hi": float(r["inner_top_arris_m"]),
                  "outer_lo": float(r["outer_top_arris_m"]), "outer_hi": float(r["outer_top_arris_m"]),
                  "cl_lo": float(r["centreline_m"]), "cl_hi": float(r["centreline_m"]), "t": float(r["t_m"]),
                  "h_lo": h_lo, "h_hi": h_hi, "outer_face_lo": float(r["outer_face_m2_lo"]),
                  "outer_face_hi": float(r["outer_face_m2_hi"]), "note": [], "kind": r["kind"],
                  "geometry_status": r["geometry_status"]}
    # C1 annex SW-3 inner face stops on the D band (B35 -> B3C), the wall face is 0.20 further (B3A)
    g = geo[("ANNEX", "SW-3")]
    assert R["B35_ends_on_D_band"]
    g["inner_lo"] = round(g["inner_hi"] - R["B35_west_of_D_band_gap_m"], 6)
    g["cl_lo"] = round(g["cl_hi"] - R["B35_west_of_D_band_gap_m"], 6)
    g["note"].append("inner face drawn to the D band (B35 on B3C), wall face 0.20 further (B3A): D-BAND range")
    corr("C1", "ANNEX", "SW-3", "inner run / inner face / top", "m", -R["B35_west_of_D_band_gap_m"], 0.0,
         "B35 ends on D band B3C; B3A 0.200 m further (P7757.dxf)", "HELD (D band: what it is is not printed)")
    # C2 1F SW-2 likewise (12B9 -> 12E2)
    g = geo[("1F", "SW-2")]
    assert R["12B9_ends_on_D_band"]
    d = round(g["inner_hi"] - H["12B9"], 6)
    g["inner_lo"] = H["12B9"]
    g["cl_lo"] = round(g["cl_hi"] - d, 6)
    g["note"].append("inner face drawn to the D band (12B9 on 12E2): D-BAND range")
    corr("C2", "1F", "SW-2", "inner run / inner face / top", "m", -d, 0.0, "12B9 4.125 m ends on D band 12E2",
         "HELD (D band)")
    # C3 1F sea side: the inner face is the straight line 12A7; T-311 carried the 1F outline's bay arc (NW-2)
    sea = [("1F", s) for s in ("NW-1", "NW-2", "NW-3", "NW-4", "NW-5")]
    others = sum(geo[k]["inner_hi"] for k in sea if k[1] != "NW-2")
    chord = round(H["12A7"] - others, 6)
    g = geo[("1F", "NW-2")]
    d = round(chord - g["inner_hi"], 6)
    g["inner_lo"] = g["inner_hi"] = chord
    g["cl_lo"] = g["cl_hi"] = round(g["cl_hi"] + d, 6)
    g["outer_lo"] = chord
    g["note"].append("roof plan +9.70 draws the sea-side parapet straight (12A7 11.600; 0.20 wall line 12A5 / 131C / "
                     "131B straight): arc replaced by its chord; outer edge at parapet level = frame profile (HELD)")
    corr("C3", "1F", "NW-2", "inner run / inner face / top / inner arris", "m", d, d,
         f"12A7 = {H['12A7']:.3f} m straight = NW-1 + chord + NW-3 + NW-4 + NW-5 (chord {chord:.4f})",
         "DRAWING-CONFIRMED")
    # C4 GF NE-4: the terrace inner face B25 runs to the divider's east face CED; T-311 ran it across the divider
    g = geo[("GF", "NE-4")]
    assert R["B25_ends_on_CED"]
    d = round(H["B25"] - g["inner_hi"], 6)
    g["inner_lo"] = g["inner_hi"] = H["B25"]
    g["note"].append("inner face B25 18.970 m ends on the divider east face CED (0.20 divider CEC / CED)")
    corr("C4", "GF", "NE-4", "inner run / inner face / inner arris / upturn", "m", d, d,
         f"B25 {H['B25']:.3f} m from CED (divider 0.200) to B33", "DRAWING-CONFIRMED")
    # C6 GF SW-9: the inner face BDB stops on a D-band curve C9E; T-311 ran it to the 1F wall face
    g = geo[("GF", "SW-9")]
    assert R["BDB_ends_on_C9E"]
    d = round(H["BDB"] - g["inner_hi"], 6)
    g["inner_lo"] = H["BDB"]
    g["cl_lo"] = round(g["cl_hi"] + d, 6)
    g["note"].append("inner face BDB 0.895 m ends on the D-band curve C9E, the 1F wall face 0.405 m further: D-BAND")
    corr("C6", "GF", "SW-9", "inner run / inner face / top / inner arris / upturn", "m", d, 0.0,
         "BDB ends on D band C9E; T-311 to the 1F wall face", "HELD (D band)")
    # C5 annex B34 extension (F-T321-02): the boundary parapet continues from the house wall line to the divider
    assert R["CEC_reaches_AC7"]
    ext_inner = round(R["B3A_to_CEC_m"], 6)                       # 1.400
    t = R["AC7_offset_from_B34_m"]                                # 0.200
    ne6 = geo[("ANNEX", "NE-6")]
    ext_outer = round(H["B34"] + t - ne6["outer_hi"], 6)          # outer from T-311's NE-6 end to the divider
    ext_top = round((H["B34"] + (H["B34"] + t)) / 2 * t - ne6["cl_hi"] * t, 6)
    geo[("ANNEX", "NE-6x")] = {"inner_lo": ext_inner, "inner_hi": ext_inner, "outer_lo": ext_outer,
                               "outer_hi": ext_outer, "cl_lo": round(ext_top / t, 6), "cl_hi": round(ext_top / t, 6),
                               "t": t, "h_lo": 0.5, "h_hi": 0.5, "outer_face_lo": None, "outer_face_hi": None,
                               "note": ["F-T321-02 confirmed: B34 runs 11.800 m to the divider CEC; T-311 NE-6 stops "
                                        "at the house wall line B3A (10.400)"], "kind": "STRAIGHT",
                               "geometry_status": "DRAWING-CONFIRMED"}
    corr("C5", "ANNEX", "NE-6x", "new run: inner / top / outer / arrises", "m", ext_inner, ext_inner,
         f"B34 {H['B34']:.3f} - B3A->CEC; divider CEC/CED {R['divider_thickness_CEC_CED_m']:.3f} reaches AC7",
         "DRAWING-CONFIRMED (outer face owner HELD: on the boundary line AC7)")

    # --- book every component once ---------------------------------------------------------------------------------
    B = Book()
    wp_line = {"ANNEX": "L-d4c73babd2a275c28929", "GF": "L-994b88140f2ea50f1b31", "1F": "L-5ce5ba49792e8f9d1f6f",
               "2F": "L-aac1f35e08f85b643692"}
    ext_line = {"ANNEX": "L-b05f70c92405dbcfbe62", "2F": "L-d52c4f763b19aedf8b8b"}
    for (chain, side), g in sorted(geo.items(), key=lambda kv: (["ANNEX", "GF", "1F", "2F"].index(kv[0][0]), kv[0][1])):
        base = f"{chain}/{side}"
        held_geo = g["geometry_status"].startswith("HELD") or g["inner_lo"] != g["inner_hi"] or g["h_lo"] != g["h_hi"]
        # outer face (owner FIN.EXT.FINISH, T-314); booked once here only as the reference to T-305's band
        if side == "NE-6x":
            B.add(Row(f"{base}/OUTER_FACE", "OUTER_FACE", "m2", round(g["outer_lo"] * 0.5, 6),
                      round(g["outer_hi"] * 0.5, 6), "HELD", "NO_LINE", "FIN.EXT.FINISH or BOUNDARY (Q-65 C)",
                      "NO LINE", "outer run x 0.50 on the neighbour boundary line AC7: not in T-159 / T-305 (NE-6 "
                      "ends at 10.600); T-172 reads AC7 as the boundary wall's outer line: owner HELD",
                      f"{base}/outer_face"))
        else:
            st = "HELD" if g["outer_face_lo"] != g["outer_face_hi"] else "DRAWING-CONFIRMED"
            line = ext_line.get(chain, "NO LINE")
            B.add(Row(f"{base}/OUTER_FACE", "OUTER_FACE", "m2", g["outer_face_lo"], g["outer_face_hi"], st,
                      "IN_LINE" if line != "NO LINE" else "NO_LINE", "FIN.EXT.FINISH", line,
                      "T-305 / T-311 band (unchanged here; T-314 integrates)", f"{base}/outer_face"))
        if g["inner_hi"] > 0:
            lo = inner_face_split(g["inner_lo"], g["h_lo"])
            hi = inner_face_split(g["inner_hi"], g["h_hi"])
            tot_lo, tot_hi = round(lo["total"], 6), round(hi["total"], 6)
            st_face = "HELD" if held_geo else "DRAWING-CONFIRMED"
            B.add(Row(f"{base}/INNER_FACE_ABOVE_UPTURN", "INNER_FACE_ABOVE_UPTURN", "m2", round(lo["above_lo"], 6),
                      round(hi["above_hi"], 6), "HELD", "NO_LINE", "PLASTER_PARAPET_INNER", "NO LINE",
                      f"face total {tot_lo:.6f} .. {tot_hi:.6f} ({st_face}); split at the upturn top HELD: build-up above "
                      "the membrane not printed (R-T324-1)", f"{base}/inner_face_upper"))
            B.add(Row(f"{base}/INNER_FACE_UPTURN_ZONE", "INNER_FACE_UPTURN_ZONE", "m2", round(lo["zone_lo"], 6),
                      round(hi["zone_hi"], 6), "HELD", "NO_LINE", "WATERPROOFING (upturn termination / protection)",
                      "NO LINE", f"0 .. inner run x min({UPTURN_H}, h): the exposed part of the 0.20 m upturn; its "
                      "finish over the membrane is the WP edge detail (UNKNOWN system)", f"{base}/inner_face_lower"))
        top_lo, _ = top_surface(g["cl_lo"], g["t"])
        top_hi, _ = top_surface(g["cl_hi"], g["t"])
        st_top = "DRAWING-CONFIRMED" if abs(top_hi - top_lo) < 1e-9 else "HELD"
        B.add(Row(f"{base}/TOP_SURFACE", "TOP_SURFACE", "m2", round(top_lo, 6), round(top_hi, 6), st_top, "NO_LINE",
                  "FIN.EXT.FINISH (plain top, section A-A; a printed coping would replace it)", "NO LINE",
                  f"centreline x drawn t {g['t']:.3f} (R-T324-2)", f"{base}/top"))
        outer_st = "HELD" if (side in ("NE-6x",) or g["outer_lo"] != g["outer_hi"]) else "DRAWING-CONFIRMED"
        B.add(Row(f"{base}/OUTER_TOP_ARRIS", "OUTER_TOP_ARRIS", "m.l", g["outer_lo"], g["outer_hi"], outer_st,
                  "NO_LINE", "CORNERS (own m.l line)", "NO LINE", "outer run", f"{base}/outer_top_edge"))
        if g["inner_hi"] > 0:
            B.add(Row(f"{base}/INNER_TOP_ARRIS", "INNER_TOP_ARRIS", "m.l", g["inner_lo"], g["inner_hi"],
                      "HELD" if g["inner_lo"] != g["inner_hi"] else "DRAWING-CONFIRMED", "NO_LINE",
                      "CORNERS (own m.l line)", "NO LINE", "drawn inner face line", f"{base}/inner_top_edge"))
            B.add(Row(f"{base}/UPTURN_ML", "UPTURN_ML", "m.l", g["inner_lo"], g["inner_hi"],
                      "HELD" if (chain == "2F" or g["inner_lo"] != g["inner_hi"]) else "DRAWING-CONFIRMED", "IN_LINE",
                      "WATERPROOFING (roof upturn)", wp_line[chain], "inner base: upturn length = the inner base "
                      "junction (a termination, never an arris); m.l x 0.20 in the WP line", f"{base}/inner_base"))
    # chain-level items (each once)
    for chain in ("ANNEX", "GF", "1F", "2F"):
        B.add(Row(f"{chain}/ALL/COPING", "COPING", "m.l", None, None, "UNKNOWN", "NO_LINE", "COPING (if printed)",
                  "NO LINE", "no coping printed: section A-A plain top; ST p.14 P1 cap 'as per arc.' and P2 0.30 x 0.10 "
                  "cap not keyed to any run (Q-65 C designer)"))
        B.add(Row(f"{chain}/ALL/DRIP", "DRIP", "m.l", None, None, "UNKNOWN", "NO_LINE", "FIN.EXT.FINISH (drip / "
                  "throat)", "NO LINE", "nothing drawn (section A-A); owner not answered (Sigma notes item 3)"))
        B.add(Row(f"{chain}/ALL/CORNER_BEAD", "CORNER_BEAD", "m.l", None, None, "UNKNOWN", "NO_LINE",
                  "CORNERS (accessory on the arris)", "NO LINE", "an accessory ON the top arrises booked above: same "
                  "physical edges, never a second length; whether specified: UNKNOWN (no specification on Drive)"))
    dv = R["divider_length_CED_m"]
    B.add(Row("ANNEX|GF/DIVIDER/FACES", "DIVIDER_FACES", "m2", None, None, "UNKNOWN", "NO_LINE",
              "PLASTER_PARAPET_INNER (both roofs)", "NO LINE", f"0.20 divider CEC / CED between the annex roof +4.30 "
              f"and the GF terrace +5.50: two faces of {dv:.3f} m and a top {dv:.3f} x 0.200 m in plan; its top level is "
              "printed nowhere: no area (in no T-311 run)", "divider"))
    B.add(Row("ANNEX|GF/DIVIDER/UPTURN_ML", "UPTURN_ML", "m.l", round(2 * dv, 6), round(2 * dv, 6),
              "DRAWING-CONFIRMED", "IN_LINE", "WATERPROOFING (roof upturn)",
              "L-d4c73babd2a275c28929 + L-994b88140f2ea50f1b31", "1.300 m on each roof (T-321 counts the divider in "
              "both roofs' vertical faces)", "divider_base"))
    B.add(Row("GF/NE-4|passage mouth/STOP_END", "STOP_END", "m.l", 0.0, 1.2, "HELD", "NO_LINE", "CORNERS",
              "NO LINE", "free end or return at the NE passage mouth not drawn (T-172): 0 .. 2 x 0.50 + 0.20",
              "GF/stop_end"))
    # vertical external corners at parapet height: owned by the vertical-corner line, listed for the no-double check
    vc = _rows(os.path.join(RES, "agents_t172", "VERTICAL_CORNERS_T172.csv"))
    roof_of_top = {4.8: 4.3, 6.0: 5.5, 14.4: 13.9}
    p_dc = 0.0
    p_held = 0.0
    for r in vc:
        if not r["type"].startswith("CONVEX"):
            continue
        top = float(r["top"])
        if top in roof_of_top:
            p_dc += top - roof_of_top[top]
        p_held += float(r["held_extra_ml"] or 0)
    B.add(Row("ALL/ALL/VERTICAL_ARRIS_AT_PARAPET_HEIGHT", "VERTICAL_ARRIS_PARAPET_PART", "m.l", round(p_dc, 6),
              round(p_dc + p_held, 6), "HELD", "OTHER_LINE", "CORNERS (vertical external corners, T-172 124.700)",
              "OTHER_LINE: facade vertical arrises (inside 124.700 DC + 0 .. 11.900 HELD)", "the parapet-height part "
              "of facade corners that run from the ground: never booked again as a parapet item", "vertical_corners"))
    return B, corrections, geo, owner


def summarise(B):
    comps = ["OUTER_FACE", "INNER_FACE_ABOVE_UPTURN", "INNER_FACE_UPTURN_ZONE", "TOP_SURFACE", "OUTER_TOP_ARRIS",
             "INNER_TOP_ARRIS", "UPTURN_ML", "STOP_END", "VERTICAL_ARRIS_PARAPET_PART"]
    out = []
    for c in comps:
        for chain in ("ANNEX", "GF", "1F", "2F", "ANNEX|GF", "ALL"):
            rows = [r for r in B.rows if r.component == c and r.key.split("/")[0] == chain]
            if not rows:
                continue
            lo = sum(r.qty_lo or 0 for r in rows)
            hi = sum((r.qty_hi if r.qty_hi is not None else r.qty_lo) or 0 for r in rows)
            st = "DRAWING-CONFIRMED" if all(r.status == "DRAWING-CONFIRMED" for r in rows) else "HELD"
            out.append({"component": c, "chain": chain, "unit": rows[0].unit, "runs": len(rows), "lo": lo, "hi": hi,
                        "status": st, "state": rows[0].state, "line": ";".join(sorted({r.line for r in rows}))})
    return out


def face_totals(B, geo):
    """Inner face totals (fixed by geometry, split HELD) per chain, for the reconciliation."""
    t = {}
    for (chain, side), g in geo.items():
        a = t.setdefault(chain, [0.0, 0.0])
        a[0] += g["inner_lo"] * g["h_lo"]
        a[1] += g["inner_hi"] * g["h_hi"]
    return t


def reconcile(B, geo):
    ft = face_totals(B, geo)
    tops = {c: B.total("TOP_SURFACE", "m2") for c in ("x",)}
    rows = []
    inner_lo = sum(v[0] for v in ft.values())
    inner_hi = sum(v[1] for v in ft.values())
    top_lo, top_hi = B.total("TOP_SURFACE", "m2")
    rows.append(("T-305 parapet items m2: inner faces", 94.431, 99.534, inner_lo, inner_hi,
                 "C1 annex SW-3 D band -0.100 .. 0; C2 1F SW-2 D band (x HELD h); C3 sea-side chord -0.577; C4 GF NE-4 to the "
                 "divider -0.100; C5 B34 extension +0.700; C6 GF SW-9 D band -0.203 .. 0"))
    rows.append(("T-305 parapet items m2: tops", 26.801, 26.801, top_lo, top_hi,
                 "C1 -0.040 .. 0; C2 -0.015 .. 0; C3 -0.089; C5 +0.260; C6 -0.081 .. 0; divider top UNKNOWN (no level)"))
    rows.append(("T-305 parapet items m2: inner + top", 121.232, 126.335, inner_lo + top_lo, inner_hi + top_hi,
                 "sum of the two rows above"))
    oa_lo, oa_hi = B.total("OUTER_TOP_ARRIS", "m.l")
    ia_lo, ia_hi = B.total("INNER_TOP_ARRIS", "m.l")
    rows.append(("T-305 corners m.l: parapet outer top arrises", 138.481, 138.481, oa_lo, oa_hi,
                 "C3 sea-side outer edge HELD on the frame profile (chord .. arc); C5 +1.200 HELD (boundary)"))
    rows.append(("T-305 corners m.l: parapet inner top arrises", 133.482, 133.482, ia_lo, ia_hi,
                 "C1 -0.200 .. 0; C2 -0.075 .. 0; C3 -0.4435; C4 -0.200; C5 +1.400; C6 -0.405 .. 0"))
    vp = [r for r in B.rows if r.component == "VERTICAL_ARRIS_PARAPET_PART"][0]
    rows.append(("T-305 corners m.l: vertical convex arrises (not parapet items)", 124.700, 124.700, 124.700,
                 124.700, f"OTHER_LINE: their parapet-height part {vp.qty_lo:.3f} DC (+ 0 .. 11.900 HELD 1F ends) "
                 "stays in this line"))
    rows.append(("T-305 corners m.l: passage-mouth wall ends (not parapet)", 43.100, 43.100, 43.100, 43.100,
                 "not a parapet item; GF stop-end HELD 0 .. 1.20 kept apart"))
    rows.append(("T-305 corners m.l: opening arrises (not parapet)", 137.110, 137.110, 137.110, 137.110,
                 "not a parapet item"))
    rows.append(("T-305 corners m.l: total DRAWING-CONFIRMED", 576.872, 576.872,
                 oa_lo + ia_lo + 124.7 + 43.1 + 137.11, oa_hi + ia_hi + 124.7 + 43.1 + 137.11,
                 "parapet arrises (corrected) + the three non-parapet groups unchanged"))
    return rows


FREELANCER = [  # his sheet 1 cells (re-read this run; T-162 r2 / T-172 merged readings agree): row, L (H), F, I, A, B
    ("79", "ANNEX", 28.40, 0.70, 19.880, 28.40, 56.80),
    ("83+84", "GF+2F", 63.40, 0.70, 44.380, 63.40, 126.85),
    ("78", "1F", 48.47, 1.70, 82.399, 48.47, 96.94),
]


def freelancer(B, geo):
    ft = face_totals(B, geo)
    out = []
    for row, chains, L, girth, m2, a, b in FREELANCER:
        cs = chains.split("+")
        il = sum(ft[c][0] for c in cs)
        ih = sum(ft[c][1] for c in cs)
        tl = sum(r.qty_lo for r in B.rows if r.component == "TOP_SURFACE" and r.key.split("/")[0] in cs)
        th = sum(r.qty_hi for r in B.rows if r.component == "TOP_SURFACE" and r.key.split("/")[0] in cs)
        al = sum(r.qty_lo for r in B.rows if r.component in ("OUTER_TOP_ARRIS", "INNER_TOP_ARRIS")
                 and r.key.split("/")[0] in cs)
        ah = sum(r.qty_hi for r in B.rows if r.component in ("OUTER_TOP_ARRIS", "INNER_TOP_ARRIS")
                 and r.key.split("/")[0] in cs)
        out.append({"his_row": row, "chains": chains, "his_L_m": L, "his_girth_m": girth, "his_m2": m2,
                    "drawing_inner_plus_top_lo": il + tl, "drawing_inner_plus_top_hi": ih + th,
                    "diff_m2_lo": m2 - (ih + th), "diff_m2_hi": m2 - (il + tl),
                    "his_ml_A_plus_B": a + b, "drawing_top_arrises_lo": al, "drawing_top_arrises_hi": ah})
    return out


def render(B, corrections, geo):
    files = {}
    s = io.StringIO()
    w = csv.writer(s, lineterminator="\n")
    w.writerow(["component_id", "component", "unit", "qty_lo", "qty_hi", "status", "state", "owner_trade", "line",
                "physical_item", "basis"])
    for r in B.rows:
        w.writerow([r.key, r.component, r.unit, F(r.qty_lo), F(r.qty_hi), r.status, r.state, r.owner, r.line, r.edge,
                    r.basis])
    files["COMPONENT_LEDGER_T324.csv"] = s.getvalue()
    s = io.StringIO()
    w = csv.writer(s, lineterminator="\n")
    w.writerow(["component", "chain", "unit", "rows", "qty_lo", "qty_hi", "status", "state", "line"])
    for r in summarise(B):
        w.writerow([r["component"], r["chain"], r["unit"], r["runs"], F(r["lo"]), F(r["hi"]), r["status"], r["state"],
                    r["line"]])
    files["COMPONENT_SUMMARY_T324.csv"] = s.getvalue()
    s = io.StringIO()
    w = csv.writer(s, lineterminator="\n")
    w.writerow(["id", "chain", "run", "component", "unit", "delta_lo", "delta_hi", "evidence", "status"])
    for c in corrections:
        w.writerow([c["id"], c["chain"], c["side"], c["component"], c["unit"], F(c["delta_lo"]), F(c["delta_hi"]),
                    c["evidence"], c["status"]])
    files["CORRECTIONS_T324.csv"] = s.getvalue()
    s = io.StringIO()
    w = csv.writer(s, lineterminator="\n")
    w.writerow(["reference", "reference_lo", "reference_hi", "this_ledger_lo", "this_ledger_hi", "delta_lo",
                "delta_hi", "named_causes"])
    for name, rlo, rhi, lo, hi, cause in reconcile(B, geo):
        w.writerow([name, F(rlo), F(rhi), F(lo), F(hi), F(lo - rlo), F(hi - rhi), cause])
    files["RECONCILIATION_T324.csv"] = s.getvalue()
    s = io.StringIO()
    w = csv.writer(s, lineterminator="\n")
    fr = freelancer(B, geo)
    w.writerow(list(fr[0].keys()))
    for r in fr:
        w.writerow([F(v) if isinstance(v, float) else v for v in r.values()])
    files["FREELANCER_T324.csv"] = s.getvalue()
    summ = {"rows": len(B.rows), "sea_side_plan_area_m2_0_11600": round(sea_plan_area(), 4),
            "sea_side_0p20_wall_m2_0_11600": round(0.2 * 11.6, 4),
            "components": {f"{r['component']}|{r['chain']}": [round(r["lo"], 6), round(r["hi"], 6), r["status"]]
                           for r in summarise(B)}}
    files["summary.json"] = json.dumps(summ, indent=1, sort_keys=True) + "\n"
    return files


def main(argv):
    if len(argv) >= 2 and argv[0] == "--measure":
        measure(argv[1])
        return 0
    B, corrections, geo, _ = build()
    files = render(B, corrections, geo)
    if argv and argv[0] == "--write":
        for n, txt in files.items():
            with open(os.path.join(HERE, n), "w", encoding="utf-8") as fh:
                fh.write(txt)
        print(f"wrote {len(files)} files, {len(B.rows)} components")
        return 0
    if argv and argv[0] == "--check":
        bad = [n for n, txt in files.items() if open(os.path.join(HERE, n), encoding="utf-8").read() != txt]
        print("check:", "OK" if not bad else f"DIFFER {bad}")
        return 1 if bad else 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
