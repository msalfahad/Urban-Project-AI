# T-681 tiles and adhesive HELD census and MEASURABLE NOW stretches (lane A, research, unwired)

Worker 2, 2026-11-10. Candidate ARCH_TAKEOFF_V3.0.65 (T-671 line index, file sha256 e1887c34..., lines 38af7909; the
tile-scope lines are byte-identical V3.0.61 .. V3.0.65). Nothing wired or released; V2.9 + route G unchanged; no rule /
knowledge version file touched. Rules R-T681-1 (census), R-T681-2 (skirting at an opening by its foot level), R-T681-3
(adhesive / bed materials) in `t681_rules.py`; builder `t681_alsenan.py` (`--check`); outputs
`out/T681_TILES_CENSUS.{json,md}`; tests `tests/t681_tiles_census`.

## Physical elements and scope

Floor tile (porcelain, wet-room tile, outdoor), wall tile, skirting (room and stair forms), the 1:4 cement-sand tile bed
and the 20 kg tile adhesive. Filter: class HELD and item code in FIN.FLOOR.PORCELAIN / WET_TILE / FINISH_HELD,
EXT.FLOOR.PORCELAIN / OUTDOOR, FIN.WALL.TILE, FIN.SKIRTING, FIN.STAIR.SKIRTING.SLOPED / ZIGZAG, FIN.FLOOR.BED.DRY / WET.
Out of scope (named, not counted): marble (FIN.MARBLE.*), roof / WP screeds; the wet-wall spatter dash and levelling
render are plaster-scope coats (T-676 / T-364). The candidate has NO adhesive line (materials only in the unwired
T-455 table).

## Census: 104 HELD lines = the candidate filter (none missing, none twice)

| Class | Lines | What holds them |
|---|---|---|
| OWNER_OPEN | 46 | stair skirting forms ORR-007 (20 sloped + 20 zigzag), annex wall tile Q-54 B (4), outdoor porch / pool deck OD-1 (2) |
| OPEN_BOUND | 44 | tile bed m3 = released bed area x owner band Q-45 (dry 3-4 cm: 23; wet 4-6 cm: 21) |
| DESIGNER_ITEM | 7 | stair-core wet-room floor level not drawn (2 wall tile), GF stair-centre floor material, stair-hall skirting scope Q-S6-4 / RFI a / RFI c, MS1-LD.N door 3FF floor and head |
| MEASURABLE_NOW | 6 | below |
| WIRING_GAP | 1 | OP-020 jamb skirting: EXCLUDED NOT_APPLICABLE in merged FR-T601-2 (manifest V20), still HELD in the candidate |

Totals (HELD, blank never 0): bed dry 9.045554 .. 12.060739 m3 (23), bed wet 3.423023 .. 5.134535 m3 (21), outdoor
17.227412 m2 (2, option bound), FINISH_HELD 0 .. 0.23 m2; blank: wall tile 6, skirting 7, stair skirting 22 + 22.
Cross-check: each bed m3 bound = its released m2 x band (301.518472 x 0.03 .. 0.04; 85.575578 x 0.04 .. 0.06): AGREE.

## Materials beside the m2 (R-T681-3)

Adhesive (owner 2026-11-02 / Q-45): no tile size is printed (T-455: 0 size notes in 276 DXF texts) -> HELD with the
owner-rule bound on released area: porcelain 305.020973 m2 61.004 .. 101.674 bags, wet tile 75.945577 15.189 ..
25.315, wall tile 340.3038 (+6 blank faces) 68.061 .. 113.435, outdoor porcelain 21.0142 4.203 .. 7.005; one
purchasing group 148.457 .. 247.428 -> 149 .. 248 bags (same as T-455, area unchanged). FINISH_HELD, OD-1 floors and
skirting: HELD (material / product / per-lm rule missing). Bed 1:4 (Q-45 B / Q-78 figures 8 bags + 1.1 m3 per m3,
PROVISIONAL): dry 72.364 .. 96.486 bags, 9.950 .. 13.267 m3 sand; wet 27.384 .. 41.076 bags, 3.765 .. 5.648 m3; waste
separate. Wet walls follow the owner rule 2026-11-02 (spatter + levelling render + adhesive + porcelain; no second bed).

## MEASURABLE NOW: own measure this run (P7757.dxf sha ab54dd55, private copy)

Own plan read, shaft-local stations: 1F W face solid 0 .. 1.050, window 1.050 .. 2.250 (W13, 1.200), N face solid
0 .. 1.400, window 1.400 .. 2.400 (W25, 1.000); landing south edge W 1.200; 12 riser faces 4.500 .. 1.200 at 0.300.
GF W face window 1.050 .. 2.250 (stacked, W01), 10 risers 3.900 .. 1.200. Own SE elevation chain from the '+0.15' mark:
1850 / 2000 / 2500 / 2300 -> W01 +2.00 .. +4.00, W13 +6.50 .. +8.80 (AGREE T-083 printed chain). Inherited (merged):
W25 +5.50 / +7.00 (T-201 vector; raster +7.36 adverse), MS1-L +1.00 -> +2.667, MS2-L +5.50 -> +7.516, MS2-LD +7.516 /
+7.684 (T-493 / T-501).

| Line | Stretch | Levels vs opening | Result |
|---|---|---|---|
| L-760bfa8d | MS2-LD.W25, N 1.400 .. 2.400 | landing +7.684 >= head +7.00 (raster +7.36) | **1.000 lm** FULL (was blank) |
| L-33f2018c | MS2-LD.W13, W 1.050 .. 1.200 | landing +7.516 inside +6.50 .. +8.80 | NOT_APPLICABLE (opening) |
| L-4ff56def / L-f45c2e6d | MS2-L.W2 sloped / zigzag | treads +6.844 .. +7.516 inside W13 | NOT_APPLICABLE both forms |
| L-18efa069 / L-76748b7b | MS1-L.W2 sloped / zigzag | treads +2.000 .. +2.667 inside W01 +2.00 .. +4.00 | NOT_APPLICABLE both forms (tread = sill, boundary) |

The stale cause 'sills / heads not printed' is wrong for W13 / W01 (printed chain) and W25 (drawn vector). Effect:
FIN.SKIRTING blank 7 -> 5 + 1.000 lm measured; stair skirting blank 22 + 22 -> 20 + 20 (overlay V20 highs 1.233936 /
1.230432 lm sloped removed: no wall). Freelancer: no stair / landing skirting row (NOT_COMPARABLE); verdict proposal
ENGINE_RIGHT on existence from the drawing.

## Findings for the Lead

- F-T681-1: WIRING_GAP L-6ff876ae (FR-T601-2 EXCLUDED in the overlay, HELD in the candidate).
- F-T681-2: the MS1-L / MS2-L flights and the MS2-LD landing run in front of W01 / W13 glazing (treads above the sill):
  a coordination item for the designer list (stair edge against glass, guarding); skirting is 0 either way unless a
  window moves.
- F-T681-3: trial R4 cause for L-77a18 bed (3.272 .. 4.363) is stale vs the candidate (3.284 .. 4.379, = 109.478417 m2
  x band); the overlay restates the base.
- MS1-LD.N stays HELD: door 3FF's floor and head are not printed (Q-55 C would put a head at FFL + 2.20, but which
  floor the door serves is not drawn).

Lessons-register row (proposed, ERS s.7): 2026-11-10 | landing / flight skirting stayed blank as 'sills / heads not
printed' though the elevation chain printed them | skirting sits at the floor-wall junction: an opening whose sill is at
or below the walking level and head above it removes the junction whatever the skirting height | decide a stretch beside
an opening by its foot levels against the printed sill / head; HELD only when it straddles or the band height matters
(every villa) | tests/t681 (normal: inside / above head / below sill with height; adverse: missing level, mm, head below
sill, straddle, no drawn wall above head, size not printed, unknown size) | PROPOSED.
