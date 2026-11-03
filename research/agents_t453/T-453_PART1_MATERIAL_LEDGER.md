# T-453 part 1: B1 blockwork material ledger beside candidate V3.0.45 (not in it)

Worker 2, 2026-11-03. Research reader only: `t453_material_ledger.py` + `out/` + `tests/t453_material_ledger/`. No
candidate module, engine, rule, knowledge or registry file changed; no candidate or released (V2.9 + route G) line
moves. Inputs are committed and sha256-pinned (candidate line index V3.0.45 5972888b, merged fill T-333 via
t279_inputs, T-449 r3 register pieces, opening census T-198 r3, printed lintel schedule transcription S8.6, T-367
joint mortar). Rebuild: `python3 -I research/agents_t453/t453_material_ledger.py` (byte-identical; tested).

## Physical elements and rules
- Black block units (count), AAC thin-bed glue (kg / 25 kg bags), black-block joint mortar (m3 -> cement / sand),
  lintels (one per opening under built masonry). Net area, theoretical material and procurement are kept apart.
- R-T453-1 black 0.20 m: 12.5 / m2 (UPC-BLACK-BLOCK-001, OWNER CONFIRMED 40 x 20). Black 0.15 m: HELD (face not
  stated). White AAC count: HELD (two supplier faces, none selected; both shown beside). Breakage: HELD (no source).
- R-T453-2 glue 3.5 / 4.5 kg/m2 (UPC-AAC-GLUE-001); bags once per purchasing group; the PROJECT group is HELD while 7
  held parent lines remain.
- R-T453-3 mortar: installed m3 from T-367 (10 mm joint, owner-provisional) x Q-78 1:4 (8 bags, 1.1 m3 sand per m3).
  0.20 m only; 0.15 m HELD (T-367 figure beside); procurement mortar HELD.
- R-T453-4 lintels: the structural set prints a LINTEL SCHEDULE (cast-in-situ RC, B = wall width, D by width band
  L1-L5, MIN 40 cm bearing). Level 1 project document governs the company precast rule (level 3): RC is carried; the
  owner's white precast atab (Q-60, UPC-LINTEL-001 with the printed 0.40 m bearing) is beside for white walls only
  (finding F-T453-1, no owner question: the resolution order settles it). A lintel is REQUIRED only where every drawn
  piece of the host wall leaves D + 0.06 m (owner tile-bed maximum, Q-45) above the head; less than D under every
  piece = the beam serves / conflicts -> FLAGGED; between -> FLAGGED; unknown head, held wall or opening in a held
  piece -> HELD.

## r2 (Checker F-C-T453-1, REJECTED r1 @ cafdbb24): R-T453-5 lintel faces leave the material base
- Physical element: the candidate MAS.BLOCK net is the fill net = drawn pieces (length x clear height) minus openings
  w x h. An RC lintel (project LINTEL SCHEDULE) is cast inside that panel over (w + 2 x 0.40) x D: that face is
  concrete in the lintel ledger, not glued / laid masonry (owner Q-73: only masonry that physically exists, no double
  count). r1 counted it twice.
- Rule: material base = contract net - every REQUIRED lintel face (one named row per lintel, `lintel_deductions`);
  the MAS.BLOCK contract area (`net_m2`) is untouched. A HELD / FLAGGED lintel ('at most 1') on a released host line is
  a named range 0 .. its face (`lintel_held_faces`): the material becomes RANGE-NET (never VERIFIED-NET); a face that
  cannot be bounded (no width / band) holds the material. Lintels on HELD walls deduct nothing (material already HELD;
  listed in `faces_on_held_hosts`). Black mortar = T-367 m3/m2 (uniform 40 x 20 joint) x base.
- Effect on the training villa (before r1 -> after r2): REQUIRED faces 5.445 m2 on 6 lines (white 2.425, black 0.15
  3.020 whose material stays HELD for its module), HELD / FLAGGED faces 0 .. 6.40 m2 on 6 lines. AAC glue VERIFIED-NET 575.595 kg -> 116.703 kg
  (25.934 m2; L-2fdc moved to RANGE: 444.4695 .. 451.2195 kg = the Checker's figure); PROVISIONAL-NET 597.478 ->
  112.8725 kg; RANGE-NET 907.2045 .. 932.9445 kg (4 lines). Upper sum 1,162.520 kg = r1 1,173.073 - 10.5525 kg
  (white faces 1.705 x 4.5 + 0.36 x 3.5 + 0.36 x 4.5). Black 0.20 VERIFIED-NET 1,346.55 nr unchanged (no lintel in those
  panels); 2F 3.80 m2 line (D-2F-02 in a held piece, 0 .. 0.34 m2) -> RANGE 43.25 .. 47.50 nr; black mortar
  PROVISIONAL-NET 1.644979 -> 1.588929 m3 (12.71 bags, 1.748 m3 sand) + RANGE 0.051 .. 0.056 m3.
- O-1 (Checker observation): the FFL-to-structural-top build-up is carried as `floor_buildup_m` 0.06, status STAND-IN,
  with its source (Q-45 bed maximum; tile and screed not included); each lintel row prints `spare_margin_m` (W15 0.09,
  W14 0.09) so a larger build-up is tested, not absorbed.
- Tests: 19 pass (r1 14, two r1 hand values corrected to the physical base, 4 new: normal VERIFIED wall + RC lintel,
  adverse HELD lintel range, unbounded face HELD, held-host / faces > net refused).

## Result r1 (SUPERSEDED for block / glue / mortar by r2 above; lintel rows unchanged)
| item | VERIFIED-NET | PROVISIONAL-NET | HELD |
|---|---|---|---|
| black 0.20 blocks (theoretical nr) | 107.724 m2 -> 1,346.55 | 3.800 m2 -> 47.50 | all 0.15 m black (7 lines, 201.142 m2), 7 held parents; procurement |
| AAC glue | 127.910 m2 -> 575.595 kg (23.02 bags net) | 138.525 m2 -> 597.478 kg (23.90 bags net) | project bag count (7 held parents) |
| black mortar 0.20 m | - (joint is provisional) | 111.524 m2 -> 1.644979 m3 -> 13.16 bags cement, 1.809 m3 sand | 0.15 m lines (7); procurement |
| lintels (RC per schedule) | - | 16 REQUIRED: 1.016 m3 concrete, 14.845 m2 formwork | 42 HELD, 2 FLAGGED (W13, W26), rebar kg (cover / bends not printed) |

Hand checks (Checker reproduces): GF-W01 line 62.164 m2 x 12.5 = 777.05 blocks; 1F VERIFIED_WHITE 101.976 x 4.5 =
458.892 kg; GF 0.20 black mortar 62.164 x 0.01475 = 0.916919 m3 -> 7.3354 bags, 1.0086 m3 sand; D-GF-06 (1.00 m in
a 0.20 white wall): L1 0.20 x 0.20 x (1.00 + 0.80) = 0.072 m3, formwork 2 x 0.20 x 1.80 + 0.20 x 1.00 = 0.92 m2,
precast beside 1.80 m -> 2.50 m piece; W14 (2.45 m): L3 0.20 x 0.30 x 3.25 = 0.195 m3.

## Reconciliation
- 19 released split lines = the sum of their fill walls (residual 0.0000 m2 each); no released wall outside a line.
- 60 openings in masonry walls; 8 census openings in no masonry wall (glazing lines W02 / W03, arc W17, SX-01 / SX-03,
  U-01, gate D-GF-15) and P-GF-05, whose above-lintel panel is in the fill (support HELD).

## Open / not done
- Bearing availability at both jambs and jambs on RC columns are not measured (named per lintel; S8.6's older census
  saw bearing deficits on 13 of 64 openings). Head levels of most windows HELD in the census.
- Mesh strip m and ties pcs (Q-77) are T-363's B9-03 items: not in part 1. Freelancer material lines not compared.
- Part 2 (integration) goes through a stream after this part is verified.

Lessons row (proposed): a material is labelled from its weakest input (area status AND rate status), never from the
area alone; a lintel exists only where masonry is built above the head, decided against the drawn soffit, and the
project's printed lintel schedule outranks a company stock rule (provenance T-453).
