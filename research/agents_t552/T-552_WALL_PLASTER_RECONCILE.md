# T-552 B5 wall plaster (internal + external) vs the freelancer, by face class (research, unwired)

Worker 2 (lane A), 2026-11-06, claim 04:41 UTC. Files: `t552_plaster_rules.py` (R-T552-1, any villa), `t552_inputs.py`
(candidate line ids / values, his cells as numbers by sheet row, merged drawing ledgers cited; no coordinate, no client
name), `t552_alsenan.py` -> `out/T552_PLASTER_RECONCILE.json` (`--check` rebuilds byte-identical),
`tests/t552_plaster_reconcile/` (24 tests). No engine module, method, rule / knowledge version, registry or candidate
file changed; no quantity moves. Reads only repository files (inputs sha256-pinned in the builder); the drawing values
are the merged T-128 r3 / T-173 / T-337 ledgers, cited, not re-measured this run.

## 1. Physical element and face classes (ERS s.2.1, s.3)

One finish owner per face: DRY face = spatter + plaster coat (plasterer) + paint; WET face = spatter (plasterer) +
levelling render (tiler) + adhesive / porcelain (owner 2026-11-02; the candidate's wet-room FIN.PLASTER line IS the
render, T-331 / T-454); SHAFT = full exposed height (Q-72); RETURN = door jambs and head (UP-FIN-PLASTER-001); EXTERNAL
= render / Sigma; CEILING = soffits, beam sides and soffits (Q-57). Candidate V3.0.58 (= the V3.0.57 plaster lines,
arch_v3058 (e)): FIN.PLASTER 75 lines, valued **580.5819 m2** = DRY rooms 217.2081 (4 of 11 lines) + RETURN 23.070 (26 of
30) + WET render 340.3038 (12 of 18); SHAFT 3 lines HELD; 13 EXCLUDED route lines. External: no valued line
(FIN.EXT.FINISH 3 + ARCH.FACADE 4 HELD blank; T-314 QUEUED).

His workbook: internal statement rows 4-26, gross **1,209.385** (J27); he deducts HALF of his opening list 116.495 (J45)
-> net **1,151.1375**; wet rooms are not in his plaster: they are his spatter 433.83 (= his wall-tile total, T-317).
External rows 51-92 gross **1,502.84** (J93), half of 65.745 -> net **1,469.9675**.

## 2. Internal: his gross 1,209.385 - engine valued 240.2781 (dry + returns) = +969.1069 m2, by pair, exact

| Pair | his gross | engine valued | gap | HELD | RULE_DIFFERENCE | ENGINE_RIGHT | UNRESOLVED |
|---|---|---|---|---|---|---|---|
| DRY rooms (11 lines + his wet wash row) | 948.505 | 217.2081 | +731.2969 | +587.71805 | +90.15325 | +53.4256 | 0 |
| SHAFT (3 HELD lines) | 244.920 | 0 | +244.920 | +177.07 | - | +13.85 | +54.00 |
| RETURN (30 lines) | 15.960 | 23.070 | -7.110 | (4 lines outside) | - | - | -7.110 |

DRY split: HELD = 7 HELD lines at their engine-basis gross (face x the line's own G1 height: GF-08 194.1362, 1F-13
132.1575, 1F-11 74.19915, GF-01 63.40005, 1F-10 54.27, GF-04 39.375, 2F-01 30.18015; net ranges on the rows). RULE_
DIFFERENCE = openings of the 4 valued lines in his gross (Q-73 full deduction per room side, 42.30195) + heights (his
flat 3.60 / 3.40 / 3.50 vs the lines' G1 3.65 / 3.35 / 3.15, +21.93) + his annex wash row (WET space, render by the
tiler, 7.20 x 3.60 = 25.92). ENGINE_RIGHT = his lengths vs the drawn faces (T-128 two traces): 1F-13 +34.59 (his living
40.25 + wash corridor 9.35 vs 39.45 lm) and 1F-10 +20.74 (his 22.30 vs 16.20: the two 3.05 m passage walls lie in the
1F open zone, counted there), the other rooms -1.75 .. +3.82 each. SHAFT: T-173 drawing gross 177.07 (b 0; 173.82 at b 0.10), his
box -> drawing +20.11 south (open void side) -2.64 north -3.62 west / east; RESIDUAL 54.00 named: his row 24 2.50 x
5.40 (no such face) + his GF 'stair wall' row 11.25 x 3.60 (no face outside the box he already counts). RETURN:
RESIDUAL -7.11 named: the engine values 26 openings by id vs his 14 doors x 0.20 x 5.70 (not listed by id); OP-009
(1.08 .. 1.20) and 3 reveal lines HELD blank stay outside (never 0).

Net view: his net 1,151.1375 - 240.2781 = +910.8594 = the gross gap - his half deduction 58.2475 (his convention, its
own step, never a component). WET (not reconciled here, owned once): 18 render lines, 340.3038 valued + 6 HELD blank,
against his spatter 433.83: T-547 (tile faces) / T-317 / T-349 (spatter).

## 3. ENGINE_WRONG: dry plaster at the paint height after the 2 Nov owner rule (corrected quantity, bounded)

Every dry room line's height basis is the owner G1 room formula (3.65 / 3.35 / 3.15 = interval - 0.60 beam - 0.15
decor - 0.10 floor), i.e. the PAINT height (finished ceiling). The owner rule of 2026-11-02 (Q-72; rulebook 'Plaster and
paint heights') takes plaster to the underside of the structural slab / roof, above false ceilings: H = interval -
slab 0.16 (structural general note) - build-up b (not printed, 0 .. 0.10) = GF 4.24 .. 4.34, annex 3.74 .. 3.84, 1F / 2F
3.94 .. 4.04. Missing per line = face x (H - G1): **+146.4144 .. +171.2304 m2 over the 11 dry lines** (+0.59 .. +0.69
m per face metre); on the 4 released lines +44.567 .. +52.121 (GF-15 56.0131 -> 68.71993 .. 70.87363; 1F-01 51.415 ->
61.858 .. 63.628; 1F-04 52.005 -> 62.271 .. 64.011; 2F-03 57.775 -> 68.926 .. 70.816). Status HELD (BOUNDED) on b; the
rooms under a roof (GF annex, 1F west / east / 500 x 365, 2F) also PROVISIONAL-DATUM (D-39). Crossing beams framing
into a wall above the old G1 line remove their end sections (width x depth below the slab) from the wall: HELD per
beam end (GF-08 B26 / B27, 1F-10 B19 / B6, 1F-01 B6, 2F-03 B2, 2F-01 B15, GF-01 CB6); their sides and soffit are CEILING.
Effect on the comparison: the drawn dry-room gross at the soffit height is 993.6425 .. 1,018.4585 m2 against his
924.205 on the same rooms (+7.5 .. +10.2 %): his flat 3.60 / 3.40 stop below the soffit and outweigh his longer runs.
The shaft (T-173) already uses the full exposed height; returns and wet render are unaffected.

## 4. External: his gross 1,502.84 - engine valued 0 = +1,502.84 m2, exact (T-337 row map)

HELD 1,119.7147 .. 1,125.2857 = drawn faces of his mapped rows 932.7312 .. 938.3022 (measured, not in the candidate:
T-314) + his scope rows HELD by rule 186.9835 (frame bands 28.8675 not measured; boundary wall 107.24 other trade Q-65 C;
drip edge 50.876 unanswered); RULE_DIFFERENCE 164.435 (domes 181.806 owner item 3; pool soffit = the engine's CEILING
line 12.834, owner item 4; row 64 his one plane vs two set-back faces -30.205); ENGINE_RIGHT +125.5403 .. +119.9693
(his lengths / heights vs the drawn faces, T-337 / T-159); RESIDUAL 93.15 named (rows 65, 68, 69: no drawn face,
possible double counts of the 1F set-back ends and the 2F sea face). Net view: 1,469.9675 = gross - half of 65.745.

## 5. Verdict proposals (Checker)

- Internal DRY: no engine error in the measured faces (lengths ENGINE_RIGHT, two traces); heights and half deductions
  RULE_DIFFERENCE; the pair is not comparable as a whole while 7 of 11 lines are HELD (587.72 m2 of the 731.30 gap).
- **ENGINE_WRONG (height basis)**: all 11 dry plaster lines carry the paint height; restate to the slab / roof
  underside, +146.41 .. +171.23 m2 HELD (BOUNDED) on b; a new method version at integration (never an edit in place).
- SHAFT: ENGINE_RIGHT on scope (T-173); 54.00 UNRESOLVED (his two rows with no face). RETURN: UNRESOLVED -7.11 (his
  doors not by id). EXTERNAL: ENGINE_OMISSION in the candidate (T-314), drawn faces 932.73 .. 938.30 beside; 93.15
  UNRESOLVED in his rows.

## 6. Rule, test, lesson, what is missing

R-T552-1 (module docstring): face class first, one owner per face; a plaster height carries its basis and a paint /
finished-ceiling / G1 basis is refused for plaster; exact bridge from his gross, his half rule its own step; HELD lines
at their engine-basis gross, never 0; his scope rows only with an owner rule; one named residual. Tests: villa P552
(14.00 lm x 3.74 m to the slab underside - door 1.98 - window 1.80 - 2 beam ends 0.264 = 48.316 m2; beam band 3.54 m2
CEILING beside; order / mirror invariant; bridge 2.804 exact) + adverse (paint height for plaster, tiled face also a
plaster coat, wet line in a dry pair, HELD as 0, freelancer figure as a component, his scope row with a measurement
cause, tolerance >= 0.01, lm in an m2 pair, missing build-up source, opening height unknown) + development-villa pins.
Lesson proposal (ERS s.7): "the candidate's dry plaster lines kept the owner G1 room height after the owner set plaster
to the slab underside on 2 Nov | plaster and paint were one height in the code path (FIN.PLASTER = FIN.PAINT per room)
and no test pinned the plaster height basis | every plaster height carries its basis and a paint basis is refused |
tests/t552_plaster_reconcile | OPEN until the height restatement is integrated". Missing: the floor build-up b and
the roof datum (D-39), beam widths at wall ends, opening heads of the 7 HELD lines, his door list by id, an
independent re-measure this run (values rest on the merged T-128 r3 / T-173 / T-337 ledgers).
