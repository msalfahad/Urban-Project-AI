"""T-348 development villa: the faces above the pool and round the 1F void AT225 that the freelancer's rows 70 / 71 /
74 (109.890 m2, 'faces above the swimming pool') measure, bound once to the T-337 face set or emitted as NEW faces for
T-314 (research only, not a method, not wired).

    python3 -I research/agents_t348/t348_alsenan.py --write | --check

Inputs: the merged T-337 binding (research/agents_t337/BINDING_T337.csv, read for the bound keys and their m2) and the
drawing values below, read by Worker 2 from Drive "Alsenan chalet project" (P7757_DXF_COMPRESSED.zip -> P7757.dxf, the
1F plan, the 2F plan = 1F roof, the NW elevation frame; p7757_arch_sheet04.pdf; Alsenan_Architectural_P7757_Pages_07-08
p.2 = sheet 08). Only lengths, levels, entity handles and a local arch profile (metres from the opening's left leg) are
kept: no coordinate, no client name, no image, no workbook text.
"""
import csv
import io
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import t348_void_faces as R                                                   # noqa: E402

DC, AOA, HELD = "DRAWING-CONFIRMED", "ASSUMED — OWNER-APPROVED", "HELD"

# ------------------------------------------------------------------------------------------------ printed levels (m)
LV = {
    "C_SOFFIT": (5.30, "pool-court soffit +5.30: NW elevation chain on the pool axis '4300' from +1.00 (DXF dim 4300.0)"),
    "F1": (5.50, "1F F.F.L. / GF roof +5.50: chain '200' above +5.30; 1F plan level marks"),
    "F2": (9.70, "1F roof +9.70: 2F plan mark '+9.70'; elevation chains 100 + 870"),
    "TOP": (11.00, "pool-block parapet top +11.00: NW elevation pool-axis chain 3050.5 + 454.3 + 1995.3 from +5.50; "
                   "top line 4.808 m long at +11.00"),
}
# ------------------------------------------------------------------------------------------------ plan / frame values
POOL_BLOCK_W = 4.8077   # 1F sea line under the pool block, 2F plan handle 131B (layer 2); elevation top line 4.808
CHORD = 3.0594          # between the pier ends = the screen opening span: 1F plan CB3 (layer 2, overhead) 3059.4;
                        # elevation chain 201.9 + 2691.5 + 166 = 3059.4; = chord of the NW-2 arc (BCD+BCE+BD0)
ARC_R = 1.935           # NW-2 outer face radius: 1F plan arcs BCD / BCE / BD0 (W17 band); arc 3.5283 = T-305 NW-2
SCREEN_DEPTH = 0.2983   # screen front 0.298 m seaward of the sea line: 1F plan CAA / CB2 298.3 (layer D), 2F plan
                        # 1311 498.3 = 0.20 behind + 0.298 in front, dimension '35' to the coping; elevation chain 298.3
# arch opening of the screen (elevation polyline, layer 1): inner edge (legs at the pier ends, plan CB2 / CAA) and the
# outer line 0.05 m beyond it (its crown = the printed 3050.5); local frame: x from the left leg, y above +5.50
ARCH_INNER = [(0.0, 0.0), (0.0, 1.35), (0.026, 1.7689), (0.165, 2.165), (0.405, 2.5089), (0.73, 2.7747),
              (1.114, 2.9426), (1.53, 3.0), (1.946, 2.9426), (2.33, 2.7747), (2.655, 2.5089), (2.896, 2.165),
              (3.034, 1.7689), (3.06, 1.35), (3.06, 0.0)]
ARCH_OUTER = [(0.0, 0.0), (0.0, 1.3516), (0.027, 1.7788), (0.17, 2.1881), (0.418, 2.5432), (0.754, 2.8178),
              (1.151, 2.9912), (1.58, 3.0505), (2.01, 2.9912), (2.407, 2.8178), (2.742, 2.5432), (2.991, 2.1881),
              (3.134, 1.7788), (3.16, 1.3516), (3.16, 0.0)]
# GF roof opening AT225 (void inside the B7 ring), inner outline on the 1F plan (layer 5): sea-side arc C7A r 1.550
# 2.9218, landward arc BCF r 1.735 2.6750 (0.20 in front of the curved wall), tip arcs 2F1B 0.6185 and 2F1C 0.9233
VOID_LANDWARD = 2.6750
VOID_OTHER = 2.9218 + 0.6185 + 0.9233
RING_H_LO = 0.20        # NW elevation chain '200' (+5.30 -> +5.50)
RING_H_HI = 0.75        # B7 20x75 simple-beam schedule (T-110 BM-GF-049 .. 052 void ring arc pieces)
PL05 = 2.417            # T-121 / T-127 PL-05 '1F roof west / north band' (CAD, faces not listed)

# freelancer rows (PLS statement sheet; cells already in tests/alsenan/registers_b1/FREELANCER_RAW_ROWS.json)
HIS = {"70": (1, 5.70, 4.95), "71": (1, 5.50, 4.95), "74": (2, 5.50, 4.95)}

T337 = ROOT / "research" / "agents_t337" / "BINDING_T337.csv"
INTERIOR_1F11 = ("L-31db3c83552682d92ca3", "L-349db74a70e1eecda2d2")   # 1F-11 plaster / paint, room face r 2.135


def lv(k):
    return LV[k][0]


def f6(v):
    return "" if v is None else "%.6f" % v


def t337_rows():
    with T337.open(encoding="utf-8") as fh:
        return {r["key"]: r for r in csv.DictReader(fh)}


def build():
    B = t337_rows()
    keys = set(B)
    hole_lo = R.poly_area(ARCH_INNER)
    hole_hi = R.poly_area(ARCH_OUTER)
    per_lo = R.path_length(ARCH_INNER)
    per_hi = R.path_length(ARCH_OUTER)
    scr = R.screen_faces(CHORD, lv("F1"), lv("F2"), lv("TOP"), hole_lo, hole_hi, SCREEN_DEPTH, per_lo, per_hi)
    seg = R.segment_area(ARC_R, CHORD)
    arc = R.arc_length(ARC_R, CHORD)

    def b(key):
        r = B[key]
        return float(r["lo"]) if r["lo"] else None, float(r["hi"]) if r["hi"] else None, r

    faces = []

    def add(key, face, band, bottom, top, length, lo, hi, status, bound_to, family, evidence, before=""):
        faces.append(dict(key=key, face=face, band=band, bottom=bottom, top=top, length=length, lo=lo, hi=hi,
                          status=status, bound_to=bound_to, family=family, evidence=evidence, before=before))

    # pier fronts (the screen's solid ends) = T-305 / T-337 NW-1, NW-3: bound, unchanged
    for side in ("NW-1", "NW-3"):
        for part, band in (("STOREY", "storey"), ("PARAPET", "parapet")):
            k = "1F/%s/%s/%s" % (side, part, band)
            lo, hi, r = b(k)
            add(k, "PIER-FRONT " + side, band, float(r["bottom"]), float(r["top"]) if r["top"] else None,
                float(r["length_m"]), lo, hi, r["status"], k, r["line"],
                "pier at the sea line beside the void; front 0.298 m seaward (1F plan CAB / CA7, 2F plan 1315 / 1319); "
                "projected width = T-305 length")
    # the recessed curved wall NW-2 (W17 band), storey band: bound, unchanged (its W17 hole stays T-302 / T-337's)
    k = "1F/NW-2/STOREY/storey"
    lo, hi, r = b(k)
    add(k, "RECESSED CURVED WALL NW-2", "storey", 5.5, 9.7, float(r["length_m"]), lo, hi, r["status"], k, r["line"],
        "outer face r 1.935 (BCD / BCE / BD0), arc %.4f = T-305; behind the screen, under the 1F roof" % arc)
    # screen front, parapet band (+9.70 -> +11.00) = T-337 NW-2 PARAPET re-measured on its real line (the chord at the
    # screen front, 2F plan 1319), not on the arc
    k = "1F/NW-2/PARAPET/parapet"
    lo0, hi0, r = b(k)
    p = [f for f in scr if f["face"] == "SCREEN-FRONT" and f["band"] == "parapet"][0]
    add(k, "SCREEN-FRONT (parapet band)", "parapet", lv("F2"), lv("TOP"), CHORD, p["net_lo"], p["net_hi"], DC, k,
        r["line"], "2F plan: the parapet outer face runs straight at 0.298 m seaward of the sea line across the void "
        "(1319, 4.0594 m incl. the pier steps); top +11.00 printed; the arc carries no face above +9.70 (1F roof over "
        "the recess)", before="%s %s .. %s" % (r["status"], f6(lo0), f6(hi0)))
    # NEW: the screen's storey band, front and back, and its intrados
    for f in scr:
        if f["band"] == "storey":
            add("1F/NW-2/%s/storey" % f["face"], f["face"] + " (storey band)", "storey", f["bottom"], f["top"],
                f["length"], f["net_lo"], f["net_hi"], HELD, None, "NEW FIN.EXT.FINISH 1F (T-314 FILL)",
                "gross %.6f (chord x printed +5.50 -> +9.70) less the arched opening %.6f .. %.6f (inner edge at the pier "
                "ends vs the outer line with the printed crown 3050.5: which drawn line is the hole edge is not printed)"
                % (f["gross"], f["hole_lo"], f["hole_hi"]))
        elif f["band"] == "reveal":
            add("1F/NW-2/SCREEN-INTRADOS/reveal", "SCREEN OPENING INTRADOS", "reveal", lv("F1"), None, None,
                f["net_lo"], f["net_hi"], HELD, None, "REVEAL (exterior; reveals FILL, T-326 / T-327 consumers)",
                "depth 0.2983 x developed legs + head %.6f .. %.6f (no sill: the opening stands on the void)"
                % (per_lo, per_hi))
    # recess soffit (1F roof underside between the arc and the screen back)
    add("1F/NW-2/RECESS-SOFFIT/soffit", "RECESS SOFFIT under the 1F roof", "soffit", None, lv("F2"), None, 0.0, seg,
        HELD, None, "exterior soffit family (Q-68 C: finish HELD), not a facade face",
        "segment r 1.935 / chord 3.0594 = %.6f m2 by geometry; whether T-121 PL-05 (2.417, CAD, faces not listed) "
        "already holds it is not established: new part bounded 0 .. segment" % seg)
    # void ring inner face (GF roof opening AT225): landward arc = T-337 NW-2 'slab edge below'; the rest NEW
    k = "1F/NW-2/SLAB_EDGE_BELOW/slab_edge"
    _, _, r = b(k)
    add(k, "VOID RING inner face, landward arc", "slab_edge", None, lv("F1"), VOID_LANDWARD,
        VOID_LANDWARD * RING_H_LO, VOID_LANDWARD * RING_H_HI, HELD, k, r["line"],
        "the 1F wall stands 0.20 m behind the void edge (ring band r 1.735 .. 1.935): the face is the ring's inner "
        "face, 2.6750 m (BCF), not the 3.5283 m arc; height 0.20 (elevation '200') .. 0.75 (B7 20x75)",
        before="%s blank, length %s" % (r["status"], r["length_m"]))
    add("GF/AT225/RING-INNER/slab_edge", "VOID RING inner face, sea side + tips", "slab_edge", None, lv("F1"),
        VOID_OTHER, VOID_OTHER * RING_H_LO, VOID_OTHER * RING_H_HI, HELD, None,
        "NEW FIN.EXT.FINISH SLAB-EDGE (T-314 FILL)",
        "C7A r 1.550 2.9218 + tips 2F1B 0.6185 / 2F1C 0.9233; open to the pool court below and the sky above")
    # T-337 rows that describe no physical face here
    for side in ("NW-1", "NW-3"):
        k = "1F/%s/SLAB_EDGE_BELOW/slab_edge" % side
        _, _, r = b(k)
        add(k, "NOT_A_FACE (slab edge below %s)" % side, "slab_edge", None, None, float(r["length_m"]), None, None,
            "NOT_A_FACE", k, r["line"], "the pier stands on the GF roof slab, which runs on 1.50 m seaward over the "
            "pool court (1F plan hatch and '150'): no slab edge under it", before="%s blank" % r["status"])
    # GF pool-court front slab edge inside his +5.30 band (one plane): ownership open
    add("GF/POOL-COURT-FRONT/slab_edge", "GF pool-court front slab edge (within his row-70 width)", "slab_edge",
        lv("C_SOFFIT"), lv("F1"), POOL_BLOCK_W, POOL_BLOCK_W * 0.20, POOL_BLOCK_W * 0.20, HELD, None,
        "owner trade open: court sea wall on the plot line (T-127 'boundary' / 'facade' wall; Q-65 C)",
        "+5.30 -> +5.50 printed; 1.50 m in front of the screen; the court front runs 5.40 m, only the pool-block "
        "width lies in his row")
    R.bind([dict(key=f["key"], bound_to=f["bound_to"]) for f in faces], keys)
    return faces, dict(hole=(hole_lo, hole_hi), per=(per_lo, per_hi), seg=seg, arc=arc)


def reconciliation(faces):
    by = {f["key"]: f for f in faces}

    def m(k):
        return by[k]["lo"]
    his = {k: n * h * w for k, (n, h, w) in HIS.items()}
    total = sum(his.values())
    gross_storey = CHORD * (lv("F2") - lv("F1"))
    piers = sum(m("1F/%s/%s/%s" % (s, p, b)) for s in ("NW-1", "NW-3") for p, b in (("STOREY", "storey"),
                                                                                   ("PARAPET", "parapet")))
    par = m("1F/NW-2/PARAPET/parapet")
    edge = by["GF/POOL-COURT-FRONT/slab_edge"]["lo"]
    drawn70 = piers + par + gross_storey + edge
    plane70 = POOL_BLOCK_W * (lv("TOP") - lv("C_SOFFIT"))
    nw2 = m("1F/NW-2/STOREY/storey")
    drawn71 = gross_storey + nw2
    rows = [
        ("70", "pier fronts NW-1 + NW-3, storey + parapet (T-337, bound)", piers, "MAPPED"),
        ("70", "screen front parapet band on the chord (T-337 NW-2 PARAPET, re-measured)", par, "MAPPED"),
        ("70", "screen front storey band, gross (NEW face; his rows deduct openings elsewhere)", gross_storey, "MAPPED"),
        ("70", "GF pool-court front slab edge +5.30 -> +5.50 in his band (HELD: trade)", edge, "MAPPED"),
        ("70", "CAD parapet tops of NW-1 / NW-3 at +10.999 (T-305 4-decimal areas) vs his +11.00", plane70 - drawn70, "BAND TERM"),
        ("70", "his width 4.95 vs the drawn 4.8077 x 5.70", his["70"] - plane70, "BAND TERM"),
        ("71", "screen back storey band, gross (NEW face)", gross_storey, "MAPPED"),
        ("71", "recessed curved wall NW-2 storey band (T-337, bound)", nw2, "MAPPED"),
        ("71", "his band above +9.70: the recess is roofed at +9.70 (no face)", HIS["71"][2] * (lv("TOP") - lv("F2")),
         "BAND TERM"),
        ("71", "two faces stacked in depth (chord 3.0594 x 4.20 + T-337 NW-2 14.8188, arc 3.5283) vs his one width "
               "4.95 x 4.20", HIS["71"][2] * (lv("F2") - lv("F1")) - drawn71, "BAND TERM"),
        ("74", "two more 4.95 x 5.50 faces of the pool block: no exterior face exists (its NE side is in his row 64, "
               "its SW side is the 1F-11 / bath partition)", his["74"], "NO DRAWN EXTERIOR FACE"),
    ]
    parts = [(n, v) for _, n, v, _ in rows]
    res = R.reconcile(total, parts)
    # row-71 check: the two band terms rebuild his row from the drawn faces
    assert abs(his["71"] - (drawn71 + rows[8][2] + rows[9][2])) < 1e-9
    return rows, total, res, his, drawn70, drawn71


def outputs():
    faces, geo = build()
    rows, total, res, his, d70, d71 = reconciliation(faces)
    o = {}
    s = io.StringIO()
    w = csv.writer(s, lineterminator="\n")
    w.writerow(["key", "face", "band", "bottom", "top", "length_m", "m2_lo", "m2_hi", "status", "bound_to_t337",
                "owner_line_family", "before_t337", "evidence"])
    for f in faces:
        w.writerow([f["key"], f["face"], f["band"], f6(f["bottom"]), f6(f["top"]), f6(f["length"]), f6(f["lo"]),
                    f6(f["hi"]), f["status"], f["bound_to"] or "NEW", f["family"], f["before"], f["evidence"]])
    o["FACES_T348.csv"] = s.getvalue()
    s = io.StringIO()
    w = csv.writer(s, lineterminator="\n")
    w.writerow(["key", "kind", "status", "m2", "m2_lo", "m2_hi", "consumer"])
    for f in faces:
        if f["bound_to"] and not f["before"]:
            continue                                   # bound, unchanged: nothing for T-314
        if f["status"] == "NOT_A_FACE":
            w.writerow([f["key"], "REMOVE (no physical face)", "NOT_A_FACE", "", "", "", "T-314"])
            continue
        kind = "RE-MEASURE of a T-337 row" if f["bound_to"] else "NEW face"
        if f["status"] == HELD:
            row = R.fill_row(f["key"], HELD, lo=f["lo"], hi=f["hi"])
        else:
            row = R.fill_row(f["key"], f["status"], m2=f["lo"])
        cons = "T-326 / T-327 (reveals)" if f["band"] == "reveal" else (
            "soffit family (Q-68 C)" if f["band"] == "soffit" else "T-314")
        w.writerow([f["key"], kind, row["status"], row["m2"], row["lo"], row["hi"], cons])
    o["FILL_T314_T348.csv"] = s.getvalue()
    s = io.StringIO()
    w = csv.writer(s, lineterminator="\n")
    w.writerow(["his_row", "part", "m2", "class"])
    for r_, n, v, c in rows:
        w.writerow([r_, n, f6(v), c])
    w.writerow(["70+71+74", "TOTAL his 109.890 = sum of parts; residual", f6(res), "RESIDUAL"])
    o["RECON_T348.csv"] = s.getvalue()
    summ = {
        "task": "T-348", "his_total_m2": round(total, 6), "residual_m2": res,
        "his_rows_m2": {k: round(v, 6) for k, v in his.items()},
        "drawn_in_row70_band_m2": round(d70, 6), "drawn_in_row71_band_m2": round(d71, 6),
        "no_exterior_face_m2": round(his["74"], 6),
        "screen_hole_m2": [round(geo["hole"][0], 6), round(geo["hole"][1], 6)],
        "screen_storey_net_m2": [round(CHORD * 4.2 - geo["hole"][1], 6), round(CHORD * 4.2 - geo["hole"][0], 6)],
        "recess_soffit_segment_m2": round(geo["seg"], 6), "nw2_arc_m": round(geo["arc"], 6),
        "new_faces": sorted(f["key"] for f in faces if f["bound_to"] is None),
        "re_measured_t337": sorted(f["key"] for f in faces if f["bound_to"] and f["before"]),
        "interior_cross_check": {"lines": list(INTERIOR_1F11), "room_face": "r 2.135 (BD2), 1F-11",
                                 "shared_faces": 0, "overlap_m2": 0.0},
        "not_in_rows_70_71_74": ["1F/NW-4 (W18 strip, outside the pool-block width)", "1F/NE-1", "1F/SW-1"],
        "levels": {k: v[0] for k, v in LV.items()},
        "t337_line_effects": {
            "NEW FIN.EXT.FINISH PARAPET-OUTER 1F +9.70": {
                "before": [53.550644, 59.290836],
                "after": [round(53.550644 - 4.223108 + 3.97722, 6), round(59.290836 - 4.5853 + 3.97722, 6)],
                "cause": "NW-2 parapet band on the screen chord 3.0594 (DC), not the arc 3.5283 (HELD 4.223 .. 4.585)"},
            "NEW FIN.EXT.FINISH SLAB-EDGE 1F": {
                "before": "9 faces, all blank", "after": "7 faces: NW-1 / NW-3 removed (NOT_A_FACE); NW-2 = void ring "
                "landward arc 2.675 m, HELD 0.535 .. 2.006 m2"}},
    }
    o["summary.json"] = json.dumps(summ, indent=1, ensure_ascii=False) + "\n"
    return o


def main():
    o = outputs()
    if "--write" in sys.argv:
        for n, t in o.items():
            (HERE / n).write_text(t, encoding="utf-8")
        print("written", ", ".join(o))
    elif "--check" in sys.argv:
        bad = [n for n, t in o.items() if not (HERE / n).exists() or (HERE / n).read_text(encoding="utf-8") != t]
        print("stale:", bad or "none")
        sys.exit(1 if bad else 0)
    else:
        print(o["RECON_T348.csv"])


if __name__ == "__main__":
    main()
