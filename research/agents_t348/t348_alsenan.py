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
CHORD = 3.059412        # r2 (DXF, not rounded): between the pier ends = the screen opening span: 1F plan CB3 (layer 2,
                        # overhead) 3059.411708; elevation inner legs 2784 / 2565 3059.4; = chord of the NW-2 arc
ARC_R = 1.935           # NW-2 outer face radius: 1F plan arcs BCD / BCE / BD0 (W17 band); arc 3.5283 = T-305 NW-2
SCREEN_DEPTH = 0.298259  # r2 (DXF): screen / pier front 298.259164 seaward of the sea line: 1F plan CAA / CB2 / CA2 (layer
                        # D); 2F plan 1311 498.259 = 0.298 in front + 0.20 behind (to the parapet inner face 12A7)
# Arch polylines of the screen, NW elevation frame, layer 1, vertices taken from the DXF handles (r2, D-T348-2), local
# frame: x in m from the inner left leg (handle 2784), y in m above +5.50 (the legs' base). Legs + head, base open.
ARCH_INNER_H = "2784 2738 2739 273A 27CC 273B 273C 273D 273E 27CD 273F 2740 2741 2565"
ARCH_INNER = [(0.0, 0.0), (0.0, 1.35), (0.025823, 1.768846), (0.164176, 2.165024), (0.404706, 2.50889),
              (0.729416, 2.774714), (1.114008, 2.942605), (1.529706, 3.0), (1.945404, 2.942605),
              (2.329996, 2.774714), (2.654706, 2.50889), (2.895236, 2.165024), (3.033589, 1.768846),
              (3.059412, 1.35), (3.059412, 0.0)]
ARCH_OUTER_H = "2723 271E 2722 2727 271A 271C 271F 2726 2721 271B 2724 2725 271D 2720"
ARCH_OUTER = [(-0.05, 0.0), (-0.05, 1.35154), (-0.023658, 1.778813), (0.119247, 2.188026), (0.367691, 2.543206),
              (0.703085, 2.817776), (1.100331, 2.991191), (1.529706, 3.050474), (1.959081, 2.991191),
              (2.356327, 2.817776), (2.69172, 2.543206), (2.940165, 2.188026), (3.083069, 1.778813),
              (3.109412, 1.35154), (3.109412, 0.0)]
# r2: two more arches of the same moulding (3.9594 / 4.0594 wide, centred 0.35 m towards NW-1), DXF handles
MOULD2_H = "2719 270F 2717 2711 2718 270E 270C 2710 2714 2712 2716 270D 2715 2713"
MOULD2 = [(-0.1, 0.0), (-0.1, 1.363859), (-0.069501, 1.85855), (0.10982, 2.372043), (0.421575, 2.817734),
          (0.842437, 3.162272), (1.340914, 3.379878), (1.879706, 3.454269), (2.418498, 3.379878),
          (2.916975, 3.162272), (3.337836, 2.817734), (3.649592, 2.372043), (3.828913, 1.85855),
          (3.859412, 1.363859), (3.859412, 0.0)]
MOULD3_H = "272B 2733 272E 272C 272F 2730 2731 2729 2735 272A 2736 2734 2732 272D"
MOULD3 = [(-0.15, 0.0), (-0.15, 1.365398), (-0.118982, 1.868518), (0.064892, 2.395046), (0.384561, 2.85205),
          (0.816106, 3.205334), (1.327236, 3.428464), (1.879706, 3.504743), (2.432175, 3.428464),
          (2.943306, 3.205334), (3.374851, 2.85205), (3.69452, 2.395046), (3.878393, 1.868518),
          (3.909412, 1.365398), (3.909412, 0.0)]
# The plan cut settles which arch line is the opening edge (R-T348-6): 1F plan, NW-3 side from the opening: CB0 0.05 at
# the front plane (a lip), CB1 step 0.05 back, CAF 0.05 recess, CAE step 0.10 forward, CAC 0.05 projecting band, CAD
# step 0.05 back, CAB 0.428 front; NW-1 side: CA8 0.05 lip, CA9 0.05 back, CA7 0.75 recess, CA6 0.10 forward, B64 0.05
# band, CA5 0.05 back, B63 0.022 front. The elevation chain prints the same zones (50 / 750 / 72 on NW-1, 150 on NW-3).
# So the solid stops at the pier end lines CB2 / CAA (inner arch); the outer arch line is the lip-to-recess step.
MOULD_STEPS = (("lip -> recess (outer arch line)", 0.05, "OUTER"), ("recess -> projecting band", 0.10, "MOULD2"),
               ("projecting band -> front plane", 0.05, "MOULD3"))
# r2, D-T348-1: pier outlines (plan, layer D) beyond their sea-line ring keys
NW1_FRONT = 0.872035     # 1F plan: CAA leg (y of the opening edge) to the CA4 tangent point (CA8 + CA7 + B64 + B63 zones)
NW1_ARC = 0.468504       # 1F plan CA4 (and 2F plan 1313): quarter arc r 0.298259, centre on the sea line
NW1_KEY = 1.170294       # 1F plan B62 (layer 1, sea line) = T-159 / T-337 NW-1 1.1703: the projected width
NW3_FRONT = 0.578        # CB0 + CAF + CAC + CAB zones = B61 0.577992 = T-337 NW-3 0.578 (the front is straight)
NW3_RETURN_1F = 0.298259  # 1F plan CA2 (pier SW end, front to the sea line; the W18 strip window 0.08 behind it)
NW3_RETURN_2F = 0.498259  # 2F plan 1311: front to the parapet inner face 12A7 (0.20 behind the sea line)
STRIP_TOP = (10.80, "W18 strip parapet top +10.80: NW elevation chain 839.3 + 2160.7 + 2300 from +5.50 (dims 2EEC / "
                    "2EFA / 2F08), top line 270B; its outer face on the sea line (2F plan 12A6)")
# not measured here (outside rows 70 / 71 / 74): the element SW of the W18 strip, 1F plan layer D
SW_FIN = dict(handles="CA1 CA3 C9E CA0 C9D C9F", developed=0.305222 + 0.157080 + 0.600 + 0.479442 + 0.994289 + 0.157080,
              ring_segment=("B60", 2.099512))
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
    # r2: the opening edge is the inner arch (R-T348-6, plan pier ends CB2 / CAA); the outer arch is a moulding step
    hole_lo = hole_hi = R.poly_area(ARCH_INNER)
    hole_outer = R.poly_area(ARCH_OUTER)
    per_lo = per_hi = R.path_length(ARCH_INNER)
    paths = {"OUTER": R.path_length(ARCH_OUTER), "MOULD2": R.path_length(MOULD2), "MOULD3": R.path_length(MOULD3)}
    steps = R.step_faces([(n, d, paths[k]) for n, d, k in MOULD_STEPS])
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
    # NEW: the screen's storey band, front and back, and its intrados (r2: DRAWING-CONFIRMED, R-T348-6)
    for f in scr:
        if f["band"] == "storey":
            add("1F/NW-2/%s/storey" % f["face"], f["face"] + " (storey band)", "storey", f["bottom"], f["top"],
                f["length"], f["net_lo"], f["net_hi"], DC, None, "NEW FIN.EXT.FINISH 1F (T-314 FILL)",
                "gross %.6f (chord CB3 x printed +5.50 -> +9.70) less the arched opening %.6f (inner arch, handles %s; "
                "the plan pier ends CB2 / CAA are its legs; the outer arch %.6f is the lip-to-recess step of the "
                "moulding, 1F plan CB0 / CB1 and CA8 / CA9: not the hole edge)"
                % (f["gross"], f["hole_lo"], ARCH_INNER_H, hole_outer))
        elif f["band"] == "reveal":
            add("1F/NW-2/SCREEN-INTRADOS/reveal", "SCREEN OPENING INTRADOS", "reveal", lv("F1"), None, None,
                f["net_lo"], f["net_hi"], DC, None, "REVEAL (exterior; reveals FILL, T-326 / T-327 consumers)",
                "depth %.6f (CAA / CB2) x developed legs + head %.6f of the inner arch (no sill: the opening stands on "
                "the void)" % (SCREEN_DEPTH, per_lo))
    # NEW (r2): the moulding's plane steps round the opening on the screen front (R-T348-6)
    st_m2 = sum(v for _, v in steps)
    add("1F/NW-2/SCREEN-MOULDING-STEPS/storey", "SCREEN-FRONT MOULDING STEP FACES (narrow returns)", "storey",
        lv("F1"), None, None, 0.0, st_m2, HELD, None, "NEW FIN.EXT.FINISH 1F (T-314 FILL), narrow returns",
        "three arched step faces on the screen front: %s; developed paths outer %.6f (%s), %.6f (%s), %.6f (%s) m; "
        "geometry drawn (plan steps + elevation arches, crowns +8.550 / +8.954 / +9.005, all below +9.70); HELD: no Urban "
        "rule says whether 0.05 / 0.10 m returns are measured as m2 in the face, as narrow-width m.l, or not at all "
        "(bound 0 .. %.6f m2)" % ("; ".join("%s %.2f x path = %.6f m2" % (n, d, v) for (n, d, _), (_, v)
                                             in zip(MOULD_STEPS, steps)),
                                  paths["OUTER"], ARCH_OUTER_H, paths["MOULD2"], MOULD2_H, paths["MOULD3"], MOULD3_H,
                                  st_m2))
    # NEW (r2, D-T348-1): pier NW-1 rounded NE corner, the part beyond its projected ring key
    inc = NW1_FRONT + NW1_ARC - NW1_KEY
    for band, bot, top_ in (("storey", lv("F1"), lv("F2")), ("parapet", lv("F2"), lv("TOP"))):
        add("1F/NW-1/CORNER-ARC/%s" % band, "PIER NW-1 corner arc beyond the ring key (%s band)" % band, band, bot, top_,
            inc, inc * (top_ - bot), inc * (top_ - bot), DC, None,
            "L-8bb83e16cc7b104ab88b (1F storey)" if band == "storey" else "NEW FIN.EXT.FINISH PARAPET-OUTER 1F +9.70",
            "developed front %.6f (1F plan CAA leg to the CA4 tangent) + quarter arc %.6f (CA4 r 0.298259; 2F plan 1313 "
            "the same) = %.6f m vs the ring key B62 %.6f (projected) -> +%.6f m; levels printed %s"
            % (NW1_FRONT, NW1_ARC, NW1_FRONT + NW1_ARC, NW1_KEY, inc,
               "+5.50 / +9.70" if band == "storey" else "+9.70 / +11.00 (pool-axis chain)"))
    # NEW (r2, D-T348-1): pier NW-3 SW end return (faces the W18 strip; open air)
    add("1F/NW-3/SW-RETURN/storey", "PIER NW-3 SW end return (storey band)", "storey", lv("F1"), lv("F2"),
        NW3_RETURN_1F, NW3_RETURN_1F * (lv("F2") - lv("F1")), NW3_RETURN_1F * (lv("F2") - lv("F1")), DC, None,
        "L-8bb83e16cc7b104ab88b (1F storey)",
        "1F plan CA2 %.6f (front to the sea line); the strip window lies 0.08 behind the sea line (C3B / C33 .. C3E), "
        "that 0.08 jog is T-337 SW-1, not this face; in no ring key" % NW3_RETURN_1F)
    par_ret = R.end_return_area(NW3_RETURN_1F, NW3_RETURN_2F, lv("F2"), STRIP_TOP[0], lv("TOP"))
    add("1F/NW-3/SW-RETURN/parapet", "PIER NW-3 SW end return (parapet band)", "parapet", lv("F2"), lv("TOP"),
        NW3_RETURN_2F, par_ret, par_ret, DC, None, "NEW FIN.EXT.FINISH PARAPET-OUTER 1F +9.70",
        "R-T348-6: %.6f (front to the strip parapet's outer face 12A6 on the sea line) x (+10.80 - +9.70) + %.6f (2F "
        "plan 1311, to the inner face 12A7) x (+11.00 - +10.80); %s" % (NW3_RETURN_1F, NW3_RETURN_2F, STRIP_TOP[1]))
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
    # R-T348-5: each pier's own outline closes on its claims (the opening end = the intrados leg)
    by = {f["key"]: f for f in faces}
    closure = {
        "NW-1": R.outline_closure(
            [("front + corner arc (CAA leg .. CA4 .. sea line)", NW1_FRONT + NW1_ARC, "OPEN_AIR"),
             ("opening end CAA", SCREEN_DEPTH, "OPEN_AIR"), ("back on the wall line B62", NW1_KEY, "ABUTS")],
            [("front + corner arc (CAA leg .. CA4 .. sea line)", float(B["1F/NW-1/STOREY/storey"]["length_m"])
              + by["1F/NW-1/CORNER-ARC/storey"]["length"]), ("opening end CAA", SCREEN_DEPTH)],
            tol=1e-5),                                 # the ledger keeps 1.1703 (4 decimals) for B62 1.170294
        "NW-3": R.outline_closure(
            [("front CB0 .. CAB", NW3_FRONT, "OPEN_AIR"), ("opening end CB2", SCREEN_DEPTH, "OPEN_AIR"),
             ("SW end return CA2", NW3_RETURN_1F, "OPEN_AIR"), ("back on the wall line B61", 0.577992, "ABUTS")],
            [("front CB0 .. CAB", float(B["1F/NW-3/STOREY/storey"]["length_m"])), ("opening end CB2", SCREEN_DEPTH),
             ("SW end return CA2", by["1F/NW-3/SW-RETURN/storey"]["length"])]),
    }
    return faces, dict(hole=(hole_lo, hole_hi), hole_outer=hole_outer, per=(per_lo, per_hi), seg=seg, arc=arc,
                       steps=steps, paths=paths, closure=closure)


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
    ret_s = m("1F/NW-3/SW-RETURN/storey")
    ret_p = m("1F/NW-3/SW-RETURN/parapet")
    rows = [
        ("70", "pier fronts NW-1 + NW-3, storey + parapet (T-337, bound)", piers, "MAPPED"),
        ("70", "screen front parapet band on the chord (T-337 NW-2 PARAPET, re-measured)", par, "MAPPED"),
        ("70", "screen front storey band, gross (NEW face; his rows deduct openings elsewhere)", gross_storey, "MAPPED"),
        ("70", "GF pool-court front slab edge +5.30 -> +5.50 in his band (HELD: trade)", edge, "MAPPED"),
        ("70", "CAD parapet tops of NW-1 / NW-3 at +10.999 (T-305 4-decimal areas) vs his +11.00 (+0.001150), less the "
               "DXF chord 3.059412 vs the 3.0594 inside 4.8077 x 5.50 (-0.000066)", plane70 - drawn70, "BAND TERM"),
        ("70", "his width 4.95 vs the drawn 4.8077 x 5.70", his["70"] - plane70, "BAND TERM"),
        ("71", "screen back storey band, gross (NEW face)", gross_storey, "MAPPED"),
        ("71", "recessed curved wall NW-2 storey band (T-337, bound)", nw2, "MAPPED"),
        ("71", "his band above +9.70: the recess is roofed at +9.70 (no face)", HIS["71"][2] * (lv("TOP") - lv("F2")),
         "BAND TERM"),
        ("71", "two faces stacked in depth (chord 3.059412 x 4.20 + T-337 NW-2 14.8188, arc 3.5283) vs his one width "
               "4.95 x 4.20", HIS["71"][2] * (lv("F2") - lv("F1")) - drawn71, "BAND TERM"),
        ("74", "SW side: pier NW-3 SW end return, storey band (1F plan CA2; NEW, r2)", ret_s, "MAPPED"),
        ("74", "SW side: pier NW-3 SW end return, parapet band (2F plan 1311 beside the +10.80 strip; NEW, r2)", ret_p,
         "MAPPED"),
        ("74", "the rest of two 4.95 x 5.50 side faces of the pool block: no exterior face exists (its NE side runs on "
               "as NE-2 in his row 64; its SW side is the 1F-11 / bath partition behind the W18 strip)",
         his["74"] - ret_s - ret_p, "NO DRAWN EXTERIOR FACE"),
    ]
    parts = [(n, v) for _, n, v, _ in rows]
    res = R.reconcile(total, parts)
    # row-71 check: the two band terms rebuild his row from the drawn faces
    assert abs(his["71"] - (drawn71 + rows[8][2] + rows[9][2])) < 1e-9
    return rows, total, res, his, drawn70, drawn71, ret_s + ret_p


def outputs():
    faces, geo = build()
    rows, total, res, his, d70, d71, d74 = reconciliation(faces)
    by = {f["key"]: f for f in faces}
    T = t337_rows()
    arc_s, arc_p = by["1F/NW-1/CORNER-ARC/storey"]["lo"], by["1F/NW-1/CORNER-ARC/parapet"]["lo"]
    ret_s, ret_p = by["1F/NW-3/SW-RETURN/storey"]["lo"], by["1F/NW-3/SW-RETURN/parapet"]["lo"]
    par_new = by["1F/NW-2/PARAPET/parapet"]["lo"]
    par_old = (float(T["1F/NW-2/PARAPET/parapet"]["lo"]), float(T["1F/NW-2/PARAPET/parapet"]["hi"]))
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
        "drawn_in_row74_m2": round(d74, 6), "no_exterior_face_m2": round(his["74"] - d74, 6),
        "screen_hole_m2": round(geo["hole"][0], 6), "screen_outer_arch_m2_not_the_hole": round(geo["hole_outer"], 6),
        "screen_storey_net_m2_each_face": round(CHORD * 4.2 - geo["hole"][0], 6),
        "screen_intrados_m2": round(SCREEN_DEPTH * geo["per"][0], 6),
        "moulding_step_faces_m2": {n: round(v, 6) for n, v in geo["steps"]},
        "moulding_paths_m": {k: round(v, 6) for k, v in geo["paths"].items()},
        "pier_outline_closure_m": {k: round(v, 6) for k, v in geo["closure"].items()},
        "recess_soffit_segment_m2": round(geo["seg"], 6), "nw2_arc_m": round(geo["arc"], 6),
        "new_faces": sorted(f["key"] for f in faces if f["bound_to"] is None),
        "re_measured_t337": sorted(f["key"] for f in faces if f["bound_to"] and f["before"]),
        "interior_cross_check": {"lines": list(INTERIOR_1F11), "room_face": "r 2.135 (BD2), 1F-11",
                                 "shared_faces": 0, "overlap_m2": 0.0},
        "not_in_rows_70_71_74": ["1F/NW-4 (W18 strip, outside the pool-block width)", "1F/NE-1", "1F/SW-1",
                                 "1F/NW-1/CORNER-ARC (his row 70 is the projected plane): %.6f m2" % (arc_s + arc_p)],
        "levels": {k: v[0] for k, v in LV.items()},
        "t337_line_effects": {
            "NEW FIN.EXT.FINISH PARAPET-OUTER 1F +9.70": {
                "before": [53.550644, 59.290836],
                "after": [round(53.550644 - par_old[0] + par_new + arc_p + ret_p, 6),
                          round(59.290836 - par_old[1] + par_new + arc_p + ret_p, 6)],
                "cause": "NW-2 parapet band on the screen chord %.6f (DC %.6f), not the arc 3.5283 (HELD %.6f .. %.6f); "
                         "r2: + NW-1 corner arc %.6f + NW-3 SW end return %.6f" % (CHORD, par_new, par_old[0], par_old[1],
                                                                                arc_p, ret_p)},
            "L-8bb83e16cc7b104ab88b (1F exterior storey)": {
                "added_m2": round(arc_s + ret_s, 6),
                "cause": "r2: NW-1 corner arc %.6f + NW-3 SW end return %.6f (faces in no ring key)" % (arc_s, ret_s)},
            "NEW FIN.EXT.FINISH SLAB-EDGE 1F": {
                "before": "9 faces, all blank", "after": "7 faces: NW-1 / NW-3 removed (NOT_A_FACE); NW-2 = void ring "
                "landward arc 2.675 m, HELD 0.535 .. 2.006 m2"}},
        "finding_for_the_lead": {
            "element": "1F, the element SW of the W18 strip (layer D, up to 0.405 m seaward of the sea line), handles %s"
                       % SW_FIN["handles"],
            "developed_outline_m": round(SW_FIN["developed"], 6), "ring_segment": SW_FIN["ring_segment"][0],
            "ring_segment_m": SW_FIN["ring_segment"][1],
            "difference_m": round(SW_FIN["developed"] - SW_FIN["ring_segment"][1], 6),
            "status": "NOT MEASURED here (outside rows 70 / 71 / 74): same R-T348-5 pattern; check which ring key holds "
                      "B60 and whether it carries the projected width"},
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
