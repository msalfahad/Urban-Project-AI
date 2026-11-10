# T-675: masonry round 2 on ARCH_TAKEOFF_V3.0.63 (F-T670-1, F-T372-2, F-T372-1) (lane A, research piece)

Worker 2, 2026-11-10. Research only, nothing wired: `research/agents_t675/*`, `tests/t675_masonry_round2/*`. No engine,
rule, rulebook, knowledge, registry or candidate file changed. No drawing, workbook, client name or coordinate here.
Read this run (Drive 'Alsenan chalet project', read-only, private copies in `.work/private` only): ST7757.pdf (74da1523)
p.1; P7757_DXF_COMPRESSED.zip -> P7757.dxf (ab54dd55), census by `research/agents_t125/alsenan_v2_dump.py`;
ST7757 dxf.dxf (9f9d1179) text search. Script: `bash scripts/agent_env.sh run --tree task-T-675
research/agents_t675/t675_masonry_round2.py [<t125 pickle>]`; inputs pinned by sha256 (merged T-665 index, T-670,
T-372, T-520, T-527, T-654 trial r4, T-407).

## (a) F-T670-1: MAIN_S / ANNEX_S block type (physical element first, ERS s.2.1)

Physical element: the block built under the neighbour-side exterior ground beams of the house, from the foundation top
to the beam soffit (T-407 runs MAIN_S 16.270 m, ANNEX_S 10.000 m net of columns).

| Source | What it prints for these runs |
|---|---|
| ST7757.pdf p.1 note 2 (own read, 2026-11-10) | the neighbour-side exterior ground beams are cast over and under **black block** (طابوق أسود) built from the foundation level |
| owner 2026-10-20 10:45 (Q-60 record) | the plan / engineering-office note decides black or white and overrides the Urban fallback |
| P7757 architectural DXF (own survey) | no wall hatch, no block legend, no block-type text on any layer (hatches: S-COL.BON SOLID and floor patterns only); nothing below N.G. (T-407: section B-B silent) |
| ST7757 dxf.dxf | the notes are not DXF text (only 'NOTE-' titles): the PDF governs |

Decision: BLACK on both hosts (DRAWING-CONFIRMED by the note; no contrary source). The four AAC lines on them describe no
material: **R-T675-1** -> NOT_APPLICABLE_WITH_EVIDENCE, retire in the wiring row with this evidence in the same diff.

| line | code | before | after |
|---|---|---|---|
| L-a951fbf0 / L-6b0bb35b | MAS.GLUE.AAC (MAIN_S / ANNEX_S) | HELD blank | NOT_APPLICABLE_WITH_EVIDENCE (proposal) |
| L-09c52c7b / L-2ae0aac4 | MAS.UNITS.WHITE (MAIN_S / ANNEX_S) | HELD blank | NOT_APPLICABLE_WITH_EVIDENCE (proposal) |
| L-bd21b0ea | MAS.UNITS.BLACK MAIN_S | HELD blank | HELD blank; beside, CONDITIONAL: AT_LEAST 11.389 x 12.5 = **142.3625 pcs** (one 0.15 / 0.20 m leaf on the 40 x 20 module) |
| L-cf220ce7 | MAS.MORTAR.BLACK MAIN_S | HELD blank | HELD blank; beside, CONDITIONAL: AT_LEAST 11.389 x 0.0110625 = **0.125991 m3** (0.15 leaf; 0.167988 if 0.20) |
| L-8971f07e / L-17cea41a | ANNEX_S black pair | HELD blank | HELD blank, no bound (D-35 / RFI-S09; reading L 87.5 pcs shown, not adopted) |

Why the black lines stay HELD: host height has no upper bound (formation not printed, Q-21 C), thickness / leaf build not
printed (0.20 band vs 0.30 beam, T-407 s.7 item 4), product Q-65 C. Counts on V3.0.63: GLUE.AAC HELD 15 -> 13 (3 bounded,
10 blank) + 2 N/A; UNITS.WHITE 17 -> 15 blank + 2 N/A; black codes unchanged in count (T-670 restatement beside, unwired).

## (b) F-T372-2: the perimeter components V20 does not carry

f = kappa b j = 0.92625 x 0.15 x 0.010 = 0.001389375 m3/m (R-T520-1: the module already holds 7.375 % mortar, so the
task's 'bearing x t x 10 mm' overstates by 1 / kappa; kept as T-372).

**Lintel bearing bed (R-T675-2).** T-516 / T-527 'available' runs through the walls met to the far face, so beyond an
END_OF_MASONRY or OPENING stopper no block exists on the lintel line: the deficit end's high is the drawn available
length (T-372 used 0.40 there), at 6 dp (F-C-T372-1).

| lintel | was m3 | after m3 | bearing m (low .. high) |
|---|---|---|---|
| D-1F-02 / D-1F-08 / D-GF-13 | 0.001111 each | unchanged (EXACT) | 0.80 |
| D-1F-03 | 0.000556 .. 0.001111 | 0.000556 .. **0.000887** | 0.40 .. 0.638520 (START 0.238520 END_OF_MASONRY) |
| D-1F-04 | 0.000556 .. 0.000666 | 0.000556 .. 0.000667 | 0.40 .. 0.479800 (COLUMN, 6 dp) |
| D-1F-07 / D-1F-10 | 0.000556 .. 0.001111 | 0.000556 .. **0.000916** | 0.40 .. 0.659300 |
| D-GF-10 | 0.000556 .. 0.001111 | 0.000556 .. **0.000907** | 0.40 .. 0.653000 |
| 8 lintels | 0.006113 .. 0.008443 | **0.006113 .. 0.007628** (-0.000815 high, -9.7 %) | 4.40 .. 5.48992 m |
| D-1F-09 | HELD, no bound | **HELD 0 .. 0.001111** (2 x 0.40 printed bearing; lintel itself HELD_RANGE, in the dome piece) | |

**23 held junction bands (R-T675-3).** Rebuilt from T-520 JUNCTIONS end classes: increment = (c - 1) dz, C = 1,
O / U = 0..1, F = 0 (reproduces all 23 T-520 bounds). 2 bands (1F-W13 'D-1F-08 | east ring west crossing', 1F-W17 'east
ring sliver | D-1F-10', both 0 .. 2.20 m, ends F + U) have high 0 under every reading: **NOT_APPLICABLE_WITH_EVIDENCE**,
not held. 21 stay HELD bounded, sum 0 .. **0.017896 m3** unchanged, each with a cause: 10 FLAGGED_DEFICIT lintel ends
(D-GF-10, D-1F-03 / 04 / 07 / 10: the built bearing decides whether block meets the lintel end; one of them, 1F-W17
UU, also a dome piece), 11 dome-opening pieces only (top / ring not drawn, T-227 / T-261).

**Held pieces (top not drawn).** At most one soffit joint per metre: 6 pieces 0 .. **0.006943 m3** (1F-W13 3.4753 m,
1F-W17 0.4645 m, 1F-W24 1.0577 m). With it the OPEN companions get a drawn upper bound.

**Why V20 omits them (cause, not an error of the overlay rule).** (1) The lintel bed was first quantified by T-372
(merged 2026-11-10 10:50), after V20 (T-654, 2026-11-09 17:13). (2) T-520's per-wall high excludes HELD bands, and
T-615 labels the lintel-deficit bands 'closed as RANGE in T-520' although its high equals its low (GF-W29, 1F-W12):
the label is false; V15 FR-T615-3 opens a companion only where `held_pieces` is non-empty, so GF-W29's 2 bands fall out
of the GF 0.15 OWNER_APPROVED companion (0 .. 0.000278 instead of 0 .. 0.000834). (3) GF-W22's 0.004140 .. 0.004144 m3
sits outside its host's 8.595 m2 (parent area CONFLICT 12.9311 .. 12.9439 m2, D-27), so the R-T629-1 (c)(3) area
re-add keeps it out: it stays beside by name.

Proposed companions for the wiring row (line at the low end unchanged):

| mortar line (host) | V20 companion | proposed (bounded) | envelope m3 |
|---|---|---|---|
| L-866a6602 1F 0.15 OWNER_APPROVED | 0 .. OPEN | 0 .. 0.021449 | 0.028344 .. 0.049793 |
| L-a8f0d0e9 1F 0.15 DRAWING_CONFIRMED | 0 .. OPEN | 0 .. 0.012697 | 0.014744 .. 0.027441 |
| L-8f163174 GF 0.15 OWNER_APPROVED | 0 .. 0.000278 | 0 .. 0.000834 | 0.010361 .. 0.011195 |
| 5 other lines | unchanged | unchanged | |
| all 8 | | | **0.176727 .. 0.212874** (T-372 high 0.188035 + bands 0.017896 + pieces 0.006943) |

Beside, never summed into the panel: lintel bed 0.006113 .. 0.007628 + D-1F-09 0 .. 0.001111; GF-W22 0.004140 .. 0.004144.

## (c) F-T372-1: the two 0.20 m perimeter lines with evidence UNKNOWN

Cause: the T-580 op `PERIMETER_MORTAR` (t580_alsenan.py step 6) has no `evidence` key, so e2e_dry_run prints UNKNOWN.
Own read (P7757.dxf census): GF-W01 (WB-FL0001-FL0002, 11 face sources), 1F-W02 / W03 / W09 (2 / 3 / 2) all on the wall
layer '1' at -100.0 / +100.0 mm from the axis = **0.200 m DRAWING-CONFIRMED**; no wall hatch exists in the DXF, so no
hatch evidence either way. Colour BLACK (ST p.1 note 2 neighbour side; host ids VERIFIED_BLACK). Proposed stamp for
NEW:...PERIMETER:L-1c53fadb (0.058854) and :L-10dd62f6 (0.039291): **ASSUMED - OWNER-APPROVED** (weakest of area
VERIFIED, thickness DRAWING-CONFIRMED, module OWNER CONFIRMED Q-75, 10 mm joint ASSUMED - OWNER-APPROVED 2026-10-29),
PROVISIONAL, never VERIFIED.

## Verdicts, findings, lesson

Freelancer: no block-below-N.G., mortar or glue row: RULE_DIFFERENCE, no %. Proposals: (a) ENGINE_RIGHT on the colour
(note 2 printed); (b) bed ENGINE_RIGHT as bounded, UNRESOLVED as a point (deficit bearings, designer); (c) label only.
F-T675-1 (for T-615's owner / the wiring row): T-615 `residual_held` says 'closed as RANGE' for 4 walls whose lintel
bands are in no high. F-T675-2: producer BY_COLOUR[None] opens 4 codes on any colour-less host; the wiring should apply
R-T675-1 before staging. Lesson row (ERS s.7, proposed): "a material line is opened only for the material the host's own
evidence prints, and a bound at a stopper never runs past the drawn end of the masonry (every villa; T-675)".
