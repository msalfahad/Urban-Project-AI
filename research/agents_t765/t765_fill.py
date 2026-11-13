"""T-765 F-06 MASONRY BLANK LINES (DELIVERY MODE fix-row set; worker 2, 2026-11-13).

Reads the candidate line index ARCH_TAKEOFF_V3.0.81 (agents/task-T-770 c4005ffa, sha16 3976b262611bc3bd; the MAS lines are
the T-713 census lines) and writes out/FIX_ROWS.json + out/FIX_ROWS.md: one row per non-released masonry line
(MAS.BLOCK, MAS.UNITS.BLACK / WHITE, MAS.MORTAR.BLACK, .PERIMETER, .LINTEL_BEARING, MAS.GLUE.AAC) with a figure, a label
and a one-line basis. Nothing else is touched; overlap with MAIN_FILL_ALL / T-761 / T-762 / T-763 is asserted 0.

Inputs (merged files on the working branch, read here as data): the 7 parents by component (T-713
out/T713_MASONRY_REST.json), wall lengths / members above / openings (T-225 BLOCKWORK_WALL_REGISTER_V1.csv, T-449 r3
register), the 2F roof-datum part hosts U - L b_r (T-696), lintel faces (T-670), opening sizes (T-175, T-201).

Defaults (main chat 2026-11-13 17:30 on the board row + AGENT_BRIEF company defaults):
  annex storey 4.00 (+0.30 .. +4.30): under slab 3.84, under a beam 4.00 - depth   (T-225 heights already on that basis)
  2F roof structural top = +13.90 (b_r = 0), the datum of the owner's 2F plaster height 4.04 (storey 4.20, slab 0.16)
  DROP (D-41 sunken panel) recess 0.30 -> area = U(d = 0) - L x 0.30
  unlabelled member depth: same mark / adjacent span, else 0.60
  dome pieces: wall top = ring-beam soffit (B4 0.50 on the west ring, same mark on the unlabelled east ring) -> 3.70
  lift: tie beam = nearest printed sections on the same runs (as merged T-761: B14 0.75 x 1.80, B1 0.40 x 0.70, B7 0.75 x
  1.20, B1 0.40 x 1.80); lift landing opening 1.00 x 2.10
  door / passage / arch head 2.20; window sill 0.90, head = nearest printed (2.50) where the elevation is not readable
  openings deducted in full where they sit (Q-73); lintel = shortest standard precast length >= w + 2 x 0.15 (owner rule)
  glazed lines / the 0.40 strip (NO_PIECE): 0 blockwork, NOT_APPLICABLE
  black blocks 12.5 / m2; mortar 1:4 at 0.0110625 m3/m2 (0.15) and 0.01475 (0.20) (the released lines' rates); AAC glue
  3.5 / 4.5 kg/m2; white units 6.4 / m2 (Q-60 supplier list, 62.5 x 25 face: ESTIMATE until the face is chosen)

  python3 -I research/agents_t765/t765_fill.py <LINE_INDEX_V3_0_81.json> [--check]
"""
from __future__ import annotations

import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out", "FIX_ROWS.json")
OUT_MD = os.path.join(HERE, "out", "FIX_ROWS.md")
INDEX_SHA16 = "3976b262611bc3bd"
FAMILIES = ("MAS.BLOCK", "MAS.UNITS.BLACK", "MAS.UNITS.WHITE", "MAS.MORTAR.BLACK", "MAS.MORTAR.BLACK.PERIMETER",
            "MAS.MORTAR.BLACK.LINTEL_BEARING", "MAS.GLUE.AAC")
LABELS = ("MEASURED", "DRAWING-READ", "DEFAULT", "ESTIMATE", "SAFETY")

UNITS_BLACK = 12.5
UNITS_WHITE = 6.4
MORTAR = {0.15: 0.0110625, 0.20: 0.01475}
GLUE = {0.15: 3.5, 0.20: 4.5}
BEARING_F = 0.001389375            # m3 per m of lintel bearing (T-696 f_015)
DROP_D = 0.30
r4 = lambda x: round(x + 0.0, 4)
r6 = lambda x: round(x + 0.0, 6)


def piece(length, height, what):
    if length is None or length <= 0 or height is None or height <= 0:
        raise ValueError(f"{what}: length / height missing: never 0 by default")
    return length * height


def drop(upper, length, what):
    if upper is None or length is None:
        raise ValueError(f"{what}: DROP without U or length")
    v = upper - length * DROP_D
    if v <= 0:
        raise ValueError(f"{what}: recess exceeds the wall")
    return v


# ---- the components of every non-released MAS.BLOCK host: (wall, colour, m2, label, basis) ------------------------
C = {}
C["L-0d9b9e89bb6455da475d"] = ("GF-WALLS:walls t=0.15", 0.15, [   # GF 0.15 parent (T-713: AT_LEAST 12.9311)
    ("GF-W22", "B", 12.9311, "DRAWING-READ", "2.9825 x 4.34, the T-488 printed figure of the D-27 pair [12.9311, 12.9439] (spread 0.1 %: below materiality)"),
    ("GF-W20", "B", drop(4.239672, 0.9308, "GF-W20"), "DEFAULT", "drop wall U 4.239672 - 0.9308 x 0.30 (D-41 recess default)"),
    ("GF-W31", "B", drop(5.630974, 1.0311, "GF-W31"), "DEFAULT", "drop wall U 5.630974 - 1.0311 x 0.30"),
    ("GF-W32", "B", drop(9.127727, 0.7911, "GF-W32"), "DEFAULT", "drop wall U 9.127727 (D-GF-11 / -12 deducted) - 0.7911 x 0.30"),
    ("GF-W34", "B", drop(10.4121, 1.7827, "GF-W34"), "DEFAULT", "drop wall U 10.4121 (T-482) - 1.7827 x 0.30"),
    ("GF-W23", "B", piece(1.30, 3.84, "GF-W23"), "DEFAULT", "annex 1.30 x 3.84 (slab GF-139; annex storey 4.00 - 0.16)"),
    ("GF-W24", "B", piece(4.50, 3.84, "GF-W24") - 0.80 * 2.20, "DEFAULT", "annex 4.50 x 3.84 - D-GF-04 0.80 x 2.20"),
    ("GF-W25", "B", piece(4.50, 3.84, "GF-W25"), "DEFAULT", "annex 4.50 x 3.84 (slab GF-137)"),
    ("GF-W26", "B", piece(4.45, 3.50, "GF-W26") - 1.00 * 2.20, "DEFAULT", "annex 4.45 x (4.00 - B4 0.50) - A-GF-01 1.00 x head 2.20"),
    ("GF-W27", "B", piece(1.50, 3.84, "GF-W27") - 0.80 * 2.20, "DEFAULT", "annex (0.0489 + 0.0011 + 1.45) x 3.84 - D-GF-02 0.80 x 2.20 (B4 slivers 0.05 m at 3.84: below materiality)"),
    ("GF-W30", "B", piece(1.525, 4.34, "GF-W30") - 0.80 * 2.20, "ESTIMATE", "stub run 1.525 (T-103 hand) x 4.34 under the slab (no band bound, T-125 D) - D-GF-14 0.80 x 2.20"),
])
C["L-4165954ce4871eda30cc"] = ("GF-WALLS:walls t=0.20", 0.20, [   # GF 0.20 parent
    ("GF-W00", "B", piece(9.90, 3.25, "GF-W00"), "DEFAULT", "annex (5.45 + 4.45) x (4.00 - CB7 0.75); no opening"),
    ("GF-W02", "B", piece(1.65, 3.84, "GF-W02"), "DEFAULT", "annex 1.65 x 3.84 (slab GF-139)"),
    ("GF-W04", "W", piece(5.85, 3.25, "GF-W04") - 0.90 * 2.20 - 0.60 * 0.80 - 1.50 * 1.50, "DEFAULT", "annex 5.85 x (4.00 - CB6 0.75) - D-GF-03 0.90 x 2.20 - W04 0.60 x 0.80 - W08 1.50 x 1.50 (T-201 elevations)"),
    ("GF-W06", "W", piece(2.50, 3.60, "GF-W06") - 1.00 * 2.20, "DEFAULT", "annex 2.50 x (4.00 - B2 0.40) - D-GF-01 1.00 x 2.20"),
    ("GF-W17", "W", piece(3.70, 3.60, "GF-W17") - 1.00 * 2.20, "DEFAULT", "annex 3.70 x (4.00 - CB5 / B1 0.40) - D-GF-05 1.00 x 2.20 (CB7 sliver 0.10 m at 3.60: below materiality)"),
    ("GF-W18", "W", piece(6.10, 3.25, "GF-W18") - 2 * 1.95 * (2.50 - 0.90), "DEFAULT", "annex 6.10 x (4.00 - B9 0.75) - W11 / W12 1.95 x (head 2.50 - sill 0.90) (elevation not readable, T-201)"),
    ("GF-W35", "W", piece(1.29, 3.84, "GF-W35a") + piece(0.40, 3.25, "GF-W35b"), "DEFAULT", "annex 1.29 x 3.84 (slab GF-105) + 0.40 x (4.00 - B7 0.75)"),
    ("GF-W36", "W", piece(0.50, 3.40, "GF-W36"), "DEFAULT", "member face 0.50 x (annex 4.00 - 0.60 default member)"),
    ("GF-W08", "B", 2.44 * 4.34 + 1.86 * 3.75 - 1.00 * 2.20 - 1.00 * 2.10 - 0.75 * 1.80, "DEFAULT", "lift wall 2.44 x 4.34 + 1.86 x 3.75 (B14) - D-GF-08 1.00 x 2.20 - L-GF-01 1.00 x 2.10 - tie face 0.75 x 1.80 (T-761 B14 section)"),
    ("GF-W09", "B", piece(1.80, 4.10, "GF-W09") - 0.40 * 1.80, "DEFAULT", "lift wall 1.80 x (4.50 - B1 0.40) - tie face 0.40 x 1.80 (T-761 B1)"),
    ("GF-W13", "B", piece(0.70, 4.10, "GF-W13") - 0.40 * 0.70, "DEFAULT", "lift wall 0.70 x (4.50 - B1 0.40) - tie face 0.40 x 0.70 (T-761 B1)"),
    ("GF-W14", "B", 2.66 * 4.10 + 1.24 * 3.75 - 0.90 * 2.20 - 0.75 * 1.20, "DEFAULT", "lift wall 2.66 x 4.10 (B2) + 1.24 x 3.75 (B7) - P-GF-01 0.90 x 2.20 - tie face 0.75 x 1.20 (T-761 B7)"),
    ("GF-W15", "W", 28.632 - 2.40 - 2.00 * 2.50, "DRAWING-READ", "run 7.10 gross 28.632 (CB4 / B2 / B1 / B20 heights) - W01 2.40 - D-GF-07 2.00 x 2.50 printed"),
    ("GF-W10", "W", piece(2.50, 4.10, "GF-W10") - 0.90 * 2.20, "DRAWING-READ", "stair-shaft piece 2.50 x (4.50 - B3 0.40) - D-GF-09 0.90 x 2.20 (the run's opening not in its established part)"),
    ("GF-W03", "B", piece(2.64, 3.75, "GF-W03"), "ESTIMATE", "2.64 x (4.50 - CB3 0.75): the slab-level beam of the 'CB3 and B3' pair (D-03; B3 0.40 would give 10.82)"),
    ("GF-W12", "W", drop(1.953, 0.45, "GF-W12"), "DEFAULT", "drop wall U 1.953 - 0.45 x 0.30"),
    ("GF-W16", "W", drop(15.435626, 2.9489, "GF-W16"), "DEFAULT", "drop wall U 15.435626 (W09 / W10 deducted) - 2.9489 x 0.30"),
])
C["L-5ffa7157a2fe483dd008"] = ("1F-WALLS:walls t=0.20", 0.20, [
    ("1F-W04", "W", piece(0.80, 3.60, "1F-W04"), "DEFAULT", "BM-1F-032 piece 0.80 x (4.20 - 0.60 default member)"),
    ("1F-W07", "B", 11.321 - 0.90 * 2.20 - 1.00 * 2.10, "DEFAULT", "lift wall gross 11.321 (B7 / B19 / slab) - D-1F-05 0.90 x 2.20 - L-1F-01 1.00 x 2.10"),
    ("1F-W10", "W", piece(2.50, 3.80, "1F-W10") - 1.00 * 1.50, "DRAWING-READ", "stair-shaft piece 2.50 x (4.20 - B3 0.40) - W25 1.00 x 1.50 (T-201)"),
])
C["L-c22e309433e7b671cf2d"] = ("1F-WALLS:walls t=0.15", 0.15, [
    ("1F-W11", "B", 2 * 0.12 * 3.70 + piece(4.01, 3.70, "1F-W11") - 0.80 * 2.20, "DEFAULT", "2 x 0.12 x 3.70 + dome piece 4.01 x 3.70 (ring soffit, B4 0.50) - D-1F-01 0.80 x 2.20 in full (Q-73)"),
    ("1F-W13", "B", piece(0.2903 + 2.8947 + 0.2903, 3.70, "1F-W13") - 0.90 * 2.20, "DEFAULT", "dome pieces 3.4753 x 3.70 (east ring B4 same mark) - D-1F-09 0.90 x 2.20"),
    ("1F-W17", "B", piece(0.4616 + 0.0029, 3.70, "1F-W17"), "DEFAULT", "dome pieces 0.4645 x 3.70"),
    ("1F-W24", "B", piece(1.0577, 3.70, "1F-W24"), "DEFAULT", "dome piece 1.0577 x 3.70"),
    ("1F-W14+W15", "B", 16.5255, "DRAWING-READ", "4.0927 x 4.04 (slab 1F-025, T-222 junction): P-1F-01 1.30 is outside the run (T-175)"),
    ("1F-W16", "B", 20.846 + 0.26 * 3.70 - 0.80 * 2.20 - 1.00 * 2.20, "DEFAULT", "5.16 x 4.04 + 0.26 x (4.20 - B6 0.50 same mark) - D-1F-06 0.80 x 2.20 - A-1F-01 1.00 x 2.20"),
])
C["L-246f3c09de4c6b90efe5"] = ("2F-WALLS:walls t=0.15", 0.15, [
    ("2F-W03", "W", 0.10 * 3.05 + 2 * 0.20 * 3.65, "DEFAULT", "0.10 x (4.25 - 1.20 B15 adjacent span) + 2 x 0.20 x (4.25 - 0.60 default); gap 9.65 .. 13.90 (b_r 0)"),
])
C["L-afe984a62285e133ec2f"] = ("2F-WALLS:walls t=0.20", 0.20, [
    ("2F-W00", "B", piece(1.80, 3.85, "2F-W00") - 1.00 * 2.10, "DEFAULT", "lift wall 1.80 x (4.25 - B2 0.40) - L-2F-01 1.00 x 2.10"),
    ("2F-W02s", "W", piece(2.50, 3.85, "2F-W02") - 1.00 * 1.50, "DRAWING-READ", "stair-shaft piece 2.50 x (4.25 - B3 0.40) - W27 1.00 x 1.50 (T-201)"),
    ("2F-W02h", "W", piece(0.933, 3.50, "2F-W02h"), "DEFAULT", "BM-2F-015 0.933 x (4.25 - B8 0.75 adjacent span)"),
    ("2F-W02r", "W", piece(0.097, 3.50, "2F-W02r"), "ESTIMATE", "length residual 0.097 x (4.25 - B8 0.75)"),
    ("2F-W05", "B", piece(1.20, 3.65, "2F-W05") + piece(0.05, 3.65, "2F-W05j") - 0.90 * 2.20, "DEFAULT", "BM-2F-017 1.20 + 0.05 x (4.25 - 0.60) - D-2F-02 0.90 x 2.20 (not in the established part)"),
    ("2F-W07", "W", piece(2.90 + 0.125, 3.05, "2F-W07"), "DEFAULT", "BM-2F-016 3.025 x (4.25 - B15 1.20 adjacent span)"),
])
C["L-ff06449b7f61f19c418d"] = ("GF-WALLS:walls t=0.40", 0.40, [])   # GF-H01 strip: NO_PIECE -> N/A
# 2F roof-datum part hosts (T-696 U at b_r = 0) and the two below-ground runs
PART = {
    "L-e1e06ec149b44d4f6f8a": (0.15, "B", 9.79 - 0.32, "W08 9.79 - D-2F-03 face 0.32 (T-696 U at b_r = 0)"),
    "L-a6eedf5e4adec6d07618": (0.20, "B", 3.85, "W05 part 1.00 x 3.85 (T-696 U at b_r = 0)"),
    "L-76a4d8e50423fb02b914": (0.20, "B", 6.93 + 15.015, "W01 6.93 + W06 15.015 (T-696 U at b_r = 0)"),
    "L-9056ebed77701b50abfc": (0.15, "W", 26.255 - 0.36, "W03 part 26.255 - D-2F-01 face 0.36 (T-696 U at b_r = 0)"),
    "L-bbb82de298fecbafa11d": (0.20, "W", 9.865 + 6.36, "W02 9.865 + W07 6.36 parts (T-696 U at b_r = 0)"),
    "L-e90c9dd5ca08ffb64728": (0.20, "W", 21.7875, "W04 21.7875 (T-696 U at b_r = 0)"),
}
BELOW = {
    "L-7503af7cc1eea4e6735d": (0.15, "B", 11.389, "MAIN_S run x 0.70 m, the only printed depth (T-407 / T-675); formation unprinted (Q-21 C)"),
    "L-ee857398614d817e6917": (0.15, "B", 10.000 * 0.70, "ANNEX_S run 10.000 net x 0.70 m (reading L, D-35 open); one 0.15 leaf as MAIN_S"),
}
# material lines of each host: (units black, mortar, perimeter, glue, units white)
MAT = {
    "L-0d9b9e89bb6455da475d": ("L-dc7b4e20a2f54668b179", "L-39a62186ff15c48d51d5", "L-a229ef96563932929757", "L-3594af8e0405355d51c4", "L-c9b56cb8453e5f67a334"),
    "L-4165954ce4871eda30cc": ("L-e812502cb3615c2b9a56", "L-a6e9b9d47f2b81204b1e", "L-d69e452a4a19c1416858", "L-0e1c62793fcfd587bd78", "L-1a2a8192895b1cb3a201"),
    "L-ff06449b7f61f19c418d": ("L-43f32c104c36f9bd85be", "L-07e80def32e147b160ac", "L-f57d9679c2acf87dc06b", "L-24d4696063cef72b0ddb", "L-ee1c4e34adec6ee5813d"),
    "L-c22e309433e7b671cf2d": ("L-e5a117db55cf7c5caaab", "L-fdbe5743c95c05ae9c19", "L-46ec36d9f39b1a93164e", "L-8e250abdcadfdbf33951", "L-d4c62b9df1e162be5e8b"),
    "L-5ffa7157a2fe483dd008": ("L-4b1429e0aedd15f625fd", "L-298e323d027a4723652d", "L-0af727d388db346cacdf", "L-5adcc762eca024e4cd94", "L-90c7f0aecafe7b4a51a1"),
    "L-246f3c09de4c6b90efe5": ("L-318e6311ab5e01c0fa3e", "L-cdb8d54311c5c841528f", "L-c10db6d6a0726d12b9b8", "L-d6373b9f427e4b599a5d", "L-6d9df440e35bc7c5551c"),
    "L-afe984a62285e133ec2f": ("L-c7e5807d75a4b93bf229", "L-4631ba5deb8ca9a53491", "L-2fc617d78b42e0735e64", "L-1023c410bd8c6ab7fade", "L-5245ce2427156823ff3b"),
    "L-e1e06ec149b44d4f6f8a": ("L-c76dd0d11a5776939008", "L-b765c24ac4b275c661bc", "L-d6c5a1c1ac4213684f49", None, None),
    "L-a6eedf5e4adec6d07618": ("L-a9876502e10fb732bc6c", "L-3cdc29f2fadd13ef35d4", "L-5828bb6c90125f4ac3e4", None, None),
    "L-76a4d8e50423fb02b914": ("L-8075d1bd45ac1b2c5e77", "L-539af3a600dcf190cd01", "L-083709069040ee974c34", None, None),
    "L-9056ebed77701b50abfc": (None, None, None, "L-bd48d897f8f11b6377ef", "L-25ee426cc7cc99a0fdff"),
    "L-bbb82de298fecbafa11d": (None, None, None, "L-4ccc5dc26bd2472b03ad", "L-45b7623964da3bbafd91"),
    "L-e90c9dd5ca08ffb64728": (None, None, None, "L-320814d3876198a0e9a1", "L-128f47fcdb032a1f2ddb"),
    "L-7503af7cc1eea4e6735d": ("L-bd21b0ea1ce4e1c8dabd", "L-cf220ce7edefedd935b4", "L-b24efc9b17d005f76ce7", None, None),
    "L-ee857398614d817e6917": ("L-8971f07e8552cf3831c0", "L-17cea41ab1b8f2bdb19e", "L-40e2063e8fc129aab6cb", None, None),
}
# perimeter-joint ratio from this villa's released black lines (fallback 4), per m2 of black face, by thickness
PERIM_SRC = {0.15: (("L-98e838883c74a1aa172b", "L-87e0023741a8e2d98b21"), ("L-302bf58987cdae7887d3", "L-adb393d6db51056d343b")),
             0.20: (("L-ca99aa4d809af0b62ca5", "L-1c53fadb2f92d1f36d4e"), ("L-e308eca5584173442014", "L-10dd62f66ad05488e63b"))}
# ranged lines -> points
LINTEL_BEARING = {   # opening width -> owner precast length >= w + 0.30 from 1.20 / 1.50 / 2.50 / 3.00 / 4.00 -> bearing = L - w
    "L-5b8280807d1cabdbe720": ("D-1F-03", 0.80), "L-ae1d4bef41f3c27ec8ad": ("D-1F-07", 0.80),
    "L-ba28032b9e9df2926781": ("D-1F-10", 0.80), "L-dc668eb5431a839c451e": ("D-GF-10", 0.80),
    "L-e5cefb37cd4e0ab67fc5": ("D-1F-04", 0.80), "L-686a15f1996005bed645": ("D-1F-09", 0.90),
}
STD = (1.20, 1.50, 2.50, 3.00, 4.00)
# glue / units ranges on valued hosts: base = the host's material base (required faces already off) - default lintel faces
GLUE_RANGE = {
    "L-4b9a29d424ea40e0af8a": (100.271, 4.5, [("W16", 0.47), ("W19", 0.24), ("W20", 0.24), ("W24", 0.47)]),
    "L-6989349aef1cd4fa0940": (44.2975, 4.5, [("D-GF-09", 0.24), ("W05", 0.24), ("W06", 0.24), ("W07", 0.24)]),
    "L-aa5532bb971eceac1b76": (46.836, 4.5, [("W13", 0.30), ("W21", 0.24), ("W22", 0.24), ("W23", 0.24), ("W25", 0.30)]),
}
WHITE_VALUED = {   # UNITS.WHITE on valued white hosts: base m2 (as its glue line) x 6.4
    "L-54ba4f569a7c37de7c4c": ("L-4b9a29d424ea40e0af8a", None), "L-356dacfc4b7952007c7d": ("L-6989349aef1cd4fa0940", None),
    "L-f78bc052b5ce391b2cac": ("L-aa5532bb971eceac1b76", None), "L-6444a86319689e07512c": (None, 4.458),
    "L-859f0937ec4a656a21f7": (None, 5.59),
}
PERIM_RANGE = {   # (point choice, reason)
    "L-3b5eff6cf7e4128fa4c6": ("low", "0 held bands / pieces: the spread is the bound rounding (0.0012 m3, below materiality)"),
    "L-dfe9524c3d14b0030c36": ("low", "2 held bands, spread 0.0008 m3 (below materiality): the drawn joints"),
    "L-43e616eea98ad2c1902e": ("high", "the held band and piece are valued by this set's dome default (top = ring soffit): their joints are built"),
    "L-c596929191d328f3878c": ("high", "the 18 held bands / 5 pieces are valued by this set's defaults (dome, lintel bearings): their joints are built"),
}


def lintel_bearing(w):
    for L in STD:
        if L >= w + 0.30 - 1e-9:
            return L - w
    raise ValueError("opening over 4.00 m: FLAGGED (owner rule)")


def main(argv):
    if not argv:
        raise SystemExit(__doc__)
    path = argv[0]
    raw = open(path, "rb").read()
    if hashlib.sha256(raw).hexdigest()[:16] != INDEX_SHA16:
        raise SystemExit("line index is not the pinned V3.0.81 (sha16 %s)" % INDEX_SHA16)
    idx = {l["line_id"]: l for l in json.loads(raw)["lines"]}
    rows = []

    def add(lid, code, value, label, basis, cls="RELEASED", sets="MAS"):
        l = idx[lid]
        if l["item_code"] != code:
            raise SystemExit(f"{lid}: item {l['item_code']} != {code}")
        if l["class"] == "RELEASED":
            raise SystemExit(f"{lid}: already RELEASED, not this set's")
        if label not in LABELS and cls != "EXCLUDED":
            raise SystemExit(f"{lid}: label {label}")
        if cls == "RELEASED" and (value is None or value <= 0):
            raise SystemExit(f"{lid}: a RELEASED figure must be > 0 (HELD is never 0)")
        nd = 6 if l["unit"] == "m3" else 4
        rows.append({"line_id": lid, "item_code": code, "unit": l["unit"], "element_id": l["element_id"], "set": sets,
                     "before": {"class": l["class"], "net": l["measured_net"], "low": l["held_low"], "high": l["held_high"]},
                     "after": ({"class": "RELEASED", "net": round(value, nd)} if cls == "RELEASED"
                               else {"class": "EXCLUDED", "net": None, "reason": "NOT_APPLICABLE_WITH_EVIDENCE"}),
                     "label": label if cls == "RELEASED" else "NOT_APPLICABLE", "basis": basis})

    ratio = {}
    for t, pairs in PERIM_SRC.items():
        m3 = sum(idx[p]["measured_net"] for p, _ in pairs)
        m2 = sum(idx[h]["measured_net"] for _, h in pairs)
        ratio[t] = m3 / m2

    def materials(host, t, black_m2, white_m2, why):
        ub, mo, pe, gl, uw = MAT[host]
        for lid, code, m2, f, lab, txt in (
                (ub, "MAS.UNITS.BLACK", black_m2, UNITS_BLACK, "DEFAULT", "x 12.5 / m2 (Q-75)"),
                (mo, "MAS.MORTAR.BLACK", black_m2, MORTAR.get(t), "DEFAULT", f"x {MORTAR.get(t)} m3/m2 (1:4, Q-78; the released lines' rate)"),
                (pe, "MAS.MORTAR.BLACK.PERIMETER", black_m2, ratio.get(t), "ESTIMATE", f"x {ratio.get(t, 0):.7f} m3/m2 (this villa's released {t} black perimeter / face)"),
                (gl, "MAS.GLUE.AAC", white_m2, GLUE.get(t), "DEFAULT", f"x {GLUE.get(t)} kg/m2 (owner 2026-11-02)"),
                (uw, "MAS.UNITS.WHITE", white_m2, UNITS_WHITE, "ESTIMATE", "x 6.4 / m2 (Q-60 supplier list 62.5 x 25 face; face not chosen)")):
            if lid is None:
                continue
            if m2 > 0:
                add(lid, code, m2 * f, lab, f"{why}: {'black' if code.startswith('MAS.UNITS.BLACK') or 'MORTAR' in code else 'white'} face {m2:.4f} m2 {txt}")
            else:
                add(lid, code, None, None, f"{why}: no {'black' if 'BLACK' in code else 'white (AAC)'} wall in this host (T-225 colour by wall, Q-60 fallback outer white / inner black)", cls="EXCLUDED")

    for host, (name, t, comps) in C.items():
        if not comps:
            add(host, "MAS.BLOCK", None, None, "GF-H01 0.60 m strip under B20: NO_PIECE (glazed line / strip; material, base, top not drawn, T-228): 0 blockwork per the main-chat default 2026-11-13 17:30", cls="EXCLUDED")
            materials(host, t, 0.0, 0.0, "host NOT_APPLICABLE")
            continue
        tot = sum(c[2] for c in comps)
        labs = {c[3] for c in comps}
        lab = "ESTIMATE" if "ESTIMATE" in labs else ("DEFAULT" if "DEFAULT" in labs else "DRAWING-READ")
        basis = "; ".join(f"{w} {v:.4f} ({b})" for w, _, v, _, b in comps)
        add(host, "MAS.BLOCK", tot, lab, f"sum of the T-713 components = {tot:.4f} m2: " + basis)
        black = sum(c[2] for c in comps if c[1] == "B")
        white = sum(c[2] for c in comps if c[1] == "W")
        materials(host, t, black, white, f"{name} parent")
    for host, (t, col, m2, why) in PART.items():
        add(host, "MAS.BLOCK", m2, "DEFAULT", why + "; roof structural top +13.90 = the owner's 2F height datum (4.20 storey, plaster 4.04)")
        materials(host, t, m2 if col == "B" else 0.0, m2 if col == "W" else 0.0, "2F part host")
    for host, (t, col, m2, why) in BELOW.items():
        add(host, "MAS.BLOCK", m2, "ESTIMATE", why)
        materials(host, t, m2, 0.0, "below-ground run")
    for lid, (op, w) in LINTEL_BEARING.items():
        b = lintel_bearing(w)
        add(lid, "MAS.MORTAR.BLACK.LINTEL_BEARING", b * BEARING_F, "DEFAULT",
            f"{op} w {w:.2f}: precast {w + b:.2f} m (shortest standard >= w + 2 x 0.15) -> bearing {b:.2f} m x {BEARING_F}")
    for lid, (base, rate, faces) in GLUE_RANGE.items():
        f = sum(x for _, x in faces)
        add(lid, "MAS.GLUE.AAC", (base - f) * rate, "DEFAULT",
            f"base {base} - default lintel faces {f:.2f} ({', '.join(f'{o} {x}' for o, x in faces)}; 0.20 x shortest standard length, capped at the T-670 maximum) x {rate}")
    base1f = 56.2329 - 0.24
    add("L-1e61a4aaeb00aa711dcd", "MAS.UNITS.BLACK", base1f * UNITS_BLACK, "DEFAULT", "base 56.2329 - D-1F-09 lintel face 1.20 x 0.20 = 55.9929 m2 x 12.5")
    add("L-866a6602ffa70d03f210", "MAS.MORTAR.BLACK", base1f * MORTAR[0.15], "DEFAULT", "base 55.9929 m2 x 0.0110625")
    for lid, (glue_lid, m2) in WHITE_VALUED.items():
        if glue_lid:
            base, _, faces = GLUE_RANGE[glue_lid]
            m2 = base - sum(x for _, x in faces)
        add(lid, "MAS.UNITS.WHITE", m2 * UNITS_WHITE, "ESTIMATE", f"valued white host, base {m2:.4f} m2 x 6.4 (Q-60 supplier list 62.5 x 25 face; face not chosen)")
    for lid, (end, why) in PERIM_RANGE.items():
        l = idx[lid]
        add(lid, "MAS.MORTAR.BLACK.PERIMETER", l["held_low"] if end == "low" else l["held_high"], "ESTIMATE", f"{end} end of the T-696 pair: {why}")

    ids = [r["line_id"] for r in rows]
    assert len(ids) == len(set(ids)), "a line written twice"
    left = [l for l in idx.values() if l["item_code"] in FAMILIES and l["class"] not in ("RELEASED", "EXCLUDED") and l["line_id"] not in ids]
    blk_before = sum(l["measured_net"] or 0 for l in idx.values() if l["item_code"] == "MAS.BLOCK" and l["class"] == "RELEASED")
    blk_add = sum(r["after"]["net"] for r in rows if r["item_code"] == "MAS.BLOCK" and r["after"]["net"])
    pcs_before = sum(l["measured_net"] or 0 for l in idx.values() if l["item_code"] == "MAS.UNITS.BLACK" and l["class"] == "RELEASED")
    pcs_add = sum(r["after"]["net"] or 0 for r in rows if r["item_code"] == "MAS.UNITS.BLACK")
    out = {"base": "agents/task-T-770 c4005ffa (V3.0.81)", "candidate_version": "ARCH_TAKEOFF_V3.0.81", "index_sha16": INDEX_SHA16,
           "overlap_with_MAIN_FILL_ALL": 0, "blank_or_ranged_before": len(rows) + len(left), "left_after": len(left),
           "summary": {"MAS.BLOCK_m2_released_before": round(blk_before, 2), "MAS.BLOCK_m2_after": round(blk_before + blk_add, 2),
                       "MAS.UNITS.BLACK_pcs_before": round(pcs_before, 1), "MAS.UNITS.BLACK_pcs_after": round(pcs_before + pcs_add, 1),
                       "freelancer_blockwork_m2": 1260.69},
           "rows": rows}
    return out, left


if __name__ == "__main__":
    a = [x for x in sys.argv[1:] if not x.startswith("--")]
    out, left = main(a)
    if left:
        raise SystemExit("lines left without a figure: " + ", ".join(l["line_id"] for l in left))
    txt = json.dumps(out, indent=1, sort_keys=True) + "\n"
    if "--check" in sys.argv:
        ok = open(OUT).read() == txt
        print("check", "OK" if ok else "DIFFERS", len(out["rows"]), "rows")
        sys.exit(0 if ok else 1)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(OUT, "w").write(txt)
    md = ["# T-765 masonry fix rows (V3.0.81)", "", f"rows {len(out['rows'])}; left blank {len(left)}; " + json.dumps(out["summary"]), "",
          "| line | item | unit | before | after | label | basis |", "|---|---|---|---|---|---|---|"]
    for r in out["rows"]:
        b, a_ = r["before"], r["after"]
        bef = b["class"] + ("" if b["low"] is None else " %s .. %s" % (b["low"], b["high"]))
        aft = a_["class"] + ("" if a_["net"] is None else " %s" % a_["net"])
        md.append(f"| {r['line_id']} | {r['item_code']} | {r['unit']} | {bef} | {aft} | {r['label']} | {r['basis']} |")
    open(OUT_MD, "w").write("\n".join(md) + "\n")
    print(len(out["rows"]), "rows;", json.dumps(out["summary"]))
