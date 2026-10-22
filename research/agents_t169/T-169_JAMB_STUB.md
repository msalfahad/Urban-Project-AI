# T-169: jamb stub at a free-end doorway (MASONRY_CENTRELINE_V2, defect D-T125-1)

Status: fix in an opt-in module that no method imports; no released quantity changes (V2.9 + route G and the V3.0.x
candidate are identical by construction). Rules: UP-WALL-GEOM-001, L-P9-04 (stubs under 0.05 m are drafting artefacts),
owner Q-69 B (2) physical blockwork length at the plan cut.

## The defect

V2 carries a free wall end across a doorway to the near face of the wall across (T-125 fix 2) and books the whole
face-to-face gap as the doorway. Where the drawing draws a short jamb nib on that face (both faces of the partition
continued on the wall layer, no closing line, no wall record of its own), the nib went into the doorway: the
architectural run was right, the physical length (2) lost the nib. Checker re-measure (T-125 merge, 02:40): GF-W29
physical 0.500 vs 0.553 m, doorway 0.850 vs drawn gap 0.797 m.

## The fix (engine/source/masonry_centreline_v2.py, `_jamb_stub` and the doorway block of `measure`)

Seen from the free end, the wall-layer face lines on the partition's two face offsets (+-t/2, 2 cm tolerance) are
merged; the part drawn unbroken from the near face of the wall across back towards the free end is the jamb stub.

| Case | Status | Doorway | Physical |
|---|---|---|---|
| both faces drawn, stub >= 0.05 m (L-P9-04) | WALL | gap - stub | keeps the stub |
| both faces drawn, stub < 0.05 m | BELOW_L-P9-04_LISTED | gap (artefact by L-P9-04) | unchanged, stub listed |
| one face only | ONE_FACE_LISTED | gap (a frame / lining line is not a wall) | unchanged, listed |
| a collinear wall record on the face (arch_v28 RETURN_STUB) | WALL, basis WALL_RECORD | gap - record | the free end stops at the record; V1 measures the record once |
| face lines not touching the face (floating) | none | gap | unchanged |

The door evidence (record width or swing leaf, + 0.25 m frames) is now fitted to the doorway between the jambs. Every
stub is listed in `jamb_stubs[]` and on its doorway (`jamb_stub`, `face_to_face_m`); the architectural run (1) never
moves. A run with no stub is byte-identical to before.

## Alsenan (ARCH_TAKEOFF_V2.12 wall stage, Drive P7757_DXF_COMPRESSED.zip): before c8a524f / after

68 of 72 runs byte-identical (T169_BEFORE_AFTER_BY_RUN.csv); the four free-end doorways of the villa all stand on a
drawn jamb nib, and only they move. Identities (PASS_WITH_LISTED_PIECES +0.116202 m2 GF, PASS 1F / 2F) and glazed
lines unchanged.

| Run (hand row) | Arch run (1) | Doorway before -> after | Jamb stub | Physical (2) before -> after | Hand check (T-103 / T-143 rows) |
|---|---|---|---|---|---|
| GF WB-FL0010-FL0011 (GF-W27) | 1.500 | 0.874 -> 0.800 | 0.0736 | 0.626 -> 0.700 | hand door 0.80 = after; hand run 1.65 runs the T stem to the through-wall centreline (+0.15, ENGINE_RIGHT in T-125): 1.65 - 0.15 - 0.80 = 0.700, 0.0 % |
| GF WB-FL0038-FL0039 (GF-W29) | 1.350 | 0.850 -> 0.797 | 0.053 | 0.500 -> 0.553 | checker re-measure 0.553 / gap 0.797: 0.0 %; hand row 1.224 / 0.424 has the wrong run (checker) |
| 1F WB-FL0011-FL0012 (1F-W12) | 3.725 | 1.0885 -> 1.000 | 0.0885 | 2.6365 -> 2.725 | hand door 1.00 = after; hand 3.80 - 1.00 = 2.80, the 0.075 is the T stem to centreline (half the 0.15 wall) |
| 1F WB-FL0074-FL0075 (1F-W23) | 6.400 | 0.8798 -> 0.800 | 0.0798 | 4.520 -> 4.600 | hand openings 1.80 = 0.80 + 1.00 = after; hand 6.50 - 1.80 = 4.70, the 0.100 is the T stem to centreline (half the 0.20 wall) |

Families: GF 0.15 physical 31.6649 -> 31.7915 m (+0.1266 = 0.0736 + 0.053), 1F 0.15 46.4674 -> 46.6357 m (+0.1683 =
0.0885 + 0.0798); every other family and every architectural run unchanged. The doorways after the fix are 0.800 /
0.797 / 1.000 / 0.800 m: the leaf (0.69 / 0.69 / 0.89 / 0.69) plus its frames, the widths the hand rows used.
Raw linework read for GF-W29 and 1F-W12 (wall-layer faces at +-0.075 from the partition centreline, 0.053 / 0.0885 m
long, standing on the face of the wall across, whose own face line is broken between them; no closing line).

## Who is right

GF-W29, GF-W27, 1F-W12, 1F-W23 physical length: ENGINE_RIGHT after the fix (the nib is drawn on the wall layer on both
faces; the doorway is the gap between the jambs, matching the door + frames). The 0.075 .. 0.150 m left against the
hand rows is the T-stem convention already settled in T-125 (ENGINE_RIGHT).

## Missing / for the team

- T-143's ledger column `openings_other_m` for GF-W27 / GF-W29 / 1F-W12 / 1F-W23 copies the pre-fix V2 doorways
  (0.874 / 0.85 / 1.089 / 1.88); its hand solid lengths (L2b) used the 0.80 / 1.00 doors and are not affected. Not
  edited here (merged research of another task); the Lead decides whether a note is needed.
- Heights, m2 / m3 stay HELD (owner Q-60 A, T-108). No freelancer row is at run level: no engine-vs-freelancer change.
- The L-P9-04 0.05 m convention is reused (no new constant value); a stub of 0.05 .. 0.10 m is wall, as the checker
  read GF-W29.
