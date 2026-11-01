# T-438 ST-02 straight part (RS-S, RS-LD, RS-A): one stair drawn three times, or two stairs? (research only)

Worker 1 (lane S), 2026-11-01, branch `agents/task-T-438`. Development villa (Alsenan is one sample; the method
`t438_rules.py` is for every villa). No engine module, candidate line, released cell, rule or knowledge version is
changed; nothing is released. ERS s.2.1 - 2.4, s.2.7, s.3, s.4, s.7; Q-46 A, Q-50 A cond, OWNER_RULE_STAIRS_2026-10-24
s.1 / s.4 (S-8, S-9), T-425 R-T425-2 and engine cause (b), T-432 s.3a (the finding this task tests).

## 0. Sources (own read this run, by handle; private copies in `.work/private` only)

| Source | Read |
|---|---|
| Drive 'Alsenan chalet project' / P7757_DXF_COMPRESSED.zip (architectural DXF), the two ST-02 frames, each registered on its own S-OPENING-radius arcs (r 1.530511 / 2.780511): GF frame arcs 23E / 23F, 1F frame arcs BA1 / BA2 | every line of RS-S / RS-LD / RS-A by handle with layer asserted; layer 2 = linetype HIDDEN, layer 5 = CONTINUOUS (asserted); a sweep of every LINE / LWPOLYLINE segment (block contents exploded) in the RS-LD / RS-A zone; 1F dimensions 1265 ('125') and 1257 ('240'), level D16 '+5.50' |
| Drive 'Alsenan chalet project' / ST7757 dxf.dxf, ST p.4 (arcs 2DE / 2DD) | RS-S faces 2BA .. 2C4, RS-A faces 2C8 .. 315, wall 283, east edge 289, void edges 2CF / 2D0, column 374 |
| Drive 'Alsenan chalet project' / p7757_arch_sheet03.pdf and p7757_arch_sheet04.pdf (scans), looked at, not measured | the printed sheets draw what the DXF frames draw: GF dashed single lines beyond the cut symbol, four dashed lines in the RS-A zone; 1F pairs, '120', '125', '240', arrow up RS-A to '+5.50' |

`python3 -I research/agents_t438/t438_alsenan.py --arch <P7757.dxf> --st <ST7757 dxf.dxf> --write` builds
`ALSENAN_T438.json` (counts, goings, runs, areas, m3 and handles only; no position, no coordinate); `--check` re-derives
every check and figure from it without private input and prints REPRODUCED.

## 1. Physical element (ERS s.2.1)

ST-02 rises from GF FFL +1.00 to 1F FFL +5.50 (4.50 m): RS-C curved (12 risers, T-415), RS-S straight along the wall
283, RS-LD corner landing, RS-A straight along 289 arriving on the 1F floor. The straight part is the same physical
flight on every sheet; what differs between sheets is how it is DRAWN:

- 1F plan: its cut lies above the whole stair, so every edge is drawn as a PAIR: the nosing (layer 5, continuous,
  visible) and, 0.050 uphill, the riser face under it (layer 2, hidden). Projection 0.050 on all 16 straight pairs.
- ST p.4: riser FACES only (one line per riser); every one coincides with the 1F face line to 0.1 mm.
- GF plan: its cut symbol (block 147) lies on RS-S between edges 7 and 8. Below the cut: pairs, as on 1F. Beyond the
  cut (RS-S edges 8 .. 11, RS-LD, RS-A) the part is OVERHEAD: one dashed line per edge, on layer 2, and only the
  edges; the void-side edge line of the flight is not drawn beyond the cut either (visible edge 22E stops at the cut
  symbol; on 1F the same line B76 runs on to the landing and continues as B59).

## 2. Line families (R-T438-1) and the RS-S reading: NO CONFLICT

| Reading | Edges | Goings (one family) | Run first -> last face | Verdict |
|---|---|---|---|---|
| ARCH 1F (visible) B43 .. B4D / B4E .. B58 | 11 pairs | 10 x 0.300 | 3.000 | GOVERNING (s.4) |
| ST p.4 2BA .. 2C4 | 11 faces | 10 x 0.300 | 3.000 | AGREES edge by edge (0.1 mm) |
| ARCH GF 22F .. 13C / 234 .. 142 + overhead 13B / 13F / 140 / 141 | 7 pairs + 4 singles | 10 x 0.300 (nosings 34.5-step positions) | 3.000 | AGREES: the 4 singles coincide with the governing NOSINGS (not the faces) |
| T-432 worker reading of the GF frame (all layer-2 lines in order) | 11 | 6 x 0.300, **0.250**, 3 x 0.300 | **2.950** | a FAMILY MIX: faces 234 .. 142 below the cut and overhead nosings 13B .. 141 beyond it share layer 2; 142 (face of edge 7) -> 13B (nosing of edge 8) = 0.300 - 0.050 = 0.250 |

The '2.950 run with one 0.250 tread' is reproduced exactly (JSON `worker_mixed_*`) and explained: it is not drawn
geometry. RS-S is 11 risers, 10 goings of 0.300, 3.000 m on all three drawings. Nothing to hold.

## 3. RS-LD + RS-A reading (one table per reading)

Storey rise 4.50 m. Checks are reported, never used to choose (R-T438-4).

| Reading | Risers RS-C + RS-S + RS-A | Riser (check 0.150 - 0.170) | Going (0.280 - 0.300) | RS-A run (faces) | Landing (structural lane, faces) | Wall 283 -> arrival edge vs printed '240' | Landing level (1.00 + 23 R; none printed) | Drawing + handles | Verdict |
|---|---|---|---|---|---|---|---|---|---|
| ARCH 1F + ST p.4 | 12 + 11 + 5 = **28** | 0.160714 PASS | 0.300 PASS | 4 x 0.300 = 1.200 | 1.150 x 1.200 (1.3525 m2 net of column 374) | 2.400 PASS | +4.6964 | 1F nosings B59 B5A B5B B5C D22 / faces B6E B6F B70 B71 D24; ST 2C8 2C9 2CA 2CB 315 | **GOVERNING** (s.4) |
| ARCH GF (overhead) | 12 + 11 + 4 = 27 | 0.166667 PASS | 0.300 PASS | 3 x 0.300 = 0.900 | 1.150 x 1.500 (1.7125 m2) | 2.400 PASS | +4.8333 | overhead singles 144 145 146 4B5 = the governing nosings B5A .. D22 (0.1 mm); NO line on the first edge (B59 / B6E position): swept, 0 segments, incl. blocks | **PARTIAL PROJECTION** (one edge not drawn), not a count |

(The T-432 '1.250 x 1.450' landing is the same 1.150 x 1.500 read on the nosing lines from the last RS-S nosing.)

Both readings pass every check: the riser range, the going, the printed 2.400 and the lane. A test that fits the
storey rise or a range cannot decide here, and none is used.

## 4. Governing drawing and its reason (ERS s.2.2; never best fit)

**RS-S, RS-LD and RS-A govern from the ARCHITECTURAL 1F PLAN, which ST p.4 confirms edge by edge: 11 + 5 risers,
landing 1.150 x 1.200, ST-02 = 28 risers (riser 0.160714).** Reasons, in order:

1. No section cuts ST-02, so Q-46 A (section counts) does not apply; the owner's Q-50 A cond names the stair
   'reconstructed from the architectural + structural plans', which must agree. The plan that draws the straight part
   as measured geometry is the one whose cut lies above it: the 1F plan (T-425 engine cause (b), Checker-verified
   MERGED 6f159091: 'the governing reading is the plan whose cut the flight lies below'; it already classed the GF
   readings of RS-S / RS-A as PARTIAL, 9 / 10 and 3 / 4 treads). The 1F plan and ST p.4 agree on every edge.
2. The GF frame's RS-A lines are an overhead projection, and every one of them lies on a governing edge (R-T438-3):
   the GF frame does not draw a DIFFERENT layout (no line where the governing view has none); it lacks one line,
   the first RS-A edge, which lies on the same straight line (y of the RS-S void edge) as the flight's void-side edge
   that the GF frame also stops drawing at the cut symbol. A 27-riser stair would need a drawn landing edge or a
   re-spaced flight somewhere; no sheet draws either.
3. The checks pass for both readings and are not used to choose (owner S-4 (8): drawn dimensions govern; S-8: a drawn
   stair is preserved).

What stays as it was: the count 28 rests on Q-50 A cond (ASSUMED — OWNER-APPROVED, 'reconstructed, no section'),
exactly as in T-258 / T-415 / T-432; this task removes the second-drawing doubt (T-432 s.3a), it does not upgrade the
label.

## 5. Quantity effect of each reading (stated beside; the governing column is the current engine figure)

Concrete on the structural lane, merged engine construction (flight: plan x (t sec(alpha) + R / 2), landing: plate
x t, t = 0.16 'T 16'):

| Line | 28 (governing) | 27 (GF overhead, NOT a quantity) | 27 - 28 |
|---|---|---|---|
| ST02-RS-S (3.600 m2) | **0.942732** m3 | 0.958920 | +0.016188 (riser only) |
| ST02-RS-LD | **0.216400** (1.3525 m2) | 0.274000 (1.7125 m2) | +0.057600 |
| ST02-RS-A | **0.377093** (1.440 m2) | 0.287676 (1.080 m2) | -0.089417 |
| straight part | **1.536225** | 1.520596 | -0.015629 (-1.02 %) |
| ST02-RS-C steps (AT_LEAST, waist HELD) | 0.357034 | 0.370258 | +0.013224 |

Engine minus the governing reading: 0.000000 m3 on all three lines (the merged T-258 ledger already rests on 28).

B7 finishes (architectural tread line 1.150; T-412 / T-425 figures):

| Item | 28 (governing) | 27 (beside) |
|---|---|---|
| RS-A treads / tread marble | 4 / **1.380 m2** | 3 / 1.035 m2 (+0.345 m2 to the landing marble) |
| RS-A step lm (B7-06) | **4.600** | 3.450 |
| RS-A risers (B7-03 pieces) | **5** | 4 |
| RS-A nosing (B7-05) | **5.750 lm** | 4.600 lm |
| RS-S treads / marble / nosing | 10 / 3.450 m2 / 12.500 lm | the same |
| ST-02 risers | **28** | 27 |

So: no candidate value moves on this task. The T-425 correction of the GF-valued RS-A tread line (L-1dac5d9b574d7608d80d
1.035 -> 1.380 m2, 3 -> 4 treads) and of RS-S (3.105 -> 3.450) is CONFIRMED by the governing reading; its 1.035 is the
overhead count, the exact 27-reading figure above.

Freelancer (quantities only): his ST-02 row 1.2 x 16.4 x 0.28 = 5.5104 m3, 28 pieces x 1.20 on his steps; neither moves
on this task (T-432: 16.4 untraced either way; on the 27 reading his 28 pieces would be +1, on the governing reading
they AGREE: 28).

## 6. Verdicts, cross-trade ruling, designer list

- WHO IS RIGHT, ST-02 straight-part count: **ENGINE_RIGHT 28** (engine and freelancer agree on 28; the T-432 GF-frame
  '27' is a PARTIAL PROJECTION + a family mix, not a drawing conflict).
- Cross-trade ruling proposal (register): owner trade STAIRS CONCRETE for the waist and steps of RS-S / RS-LD / RS-A
  (lane S: count and positions from ST p.4 = 1F); owner trade STAIRS FINISHES for treads / risers / nosing (lane A: the
  1F reading per R-T425-2). One governing geometry feeds both (OWNER_RULE_STAIRS s.1 'from ONE verified stair
  geometry').
- Designer list (drawing-correction NOTE, not an RFI that holds anything; not an owner question, ERS s.2.7 not met:
  the drawings settle the quantity):
  - Issue: the GF plan's overhead RS-A shows 4 edges where the 1F plan and ST p.4 show 5.
  - Evidence: GF 144 / 145 / 146 / 4B5 coincide with 1F nosings B5A / B5B / B5C / D22; 1F B59 / B6E and ST 2C8 have
    no counterpart on GF (swept); GF also omits the flight's void-side edge beyond the cut.
  - Investigation: line families, view (cut position), registration of all three drawings by the arc centres; checks
    pass both readings.
  - Alternatives: (a) add the first RS-A edge to the GF overhead; (b) the designer intends a 1.500 deep landing and
    27 risers, then the 1F plan and ST p.4 must change.
  - Quantity impact: as section 5 (straight part -0.015629 m3; RS-A 1 tread, 1 riser, 1.150 lm nosing).
  - Recommendation: (a), by section 4 reasons 1 - 2.
  - Status: nothing HELD by it; T-432's 'DRAWING CONFLICT' entry for the Lead's register can close as 'no conflict:
    partial overhead projection (T-438)'.

## 7. Rules, tests, lesson

- **R-T438-1 .. R-T438-5** (research, every villa), in `t438_rules.py`: line families before goings; the governing
  view is the plan whose cut lies above the flight, agreeing with the structural plan; overhead lines are a check
  (subset -> PARTIAL, a line elsewhere -> CONFLICT, HELD); checks never select; effects beside.
- Tests `tests/t438_st02_straight` (non-Alsenan Villa K438 hand fixture, rise 2.32, going 0.280, projection 0.040):
  normal: three readings of flight S agree once families are kept; the mixed reading reproduces the 0.240 'short tread'
  and the 2.48 run; flight A overhead = PARTIAL missing the first edge; quantities by hand. ADVERSE: 'riser count taken
  from the plan that fits the storey rise best without a governing reason' (governing 16 at 0.145 FAIL is kept, the
  overhead 15 at 0.154667 PASS is not taken; `choose_by_fit` refused; without a visible reading -> HELD, never the
  overhead count); an overhead line where the governing view has none -> CONFLICT, HELD; visible vs structural
  disagree -> HELD; no structural reading -> HELD; mm as m, projection in mm, no direction, edge twice, unknown view /
  family, empty, reading twice, float count, missing rise, waist missing (never 0) refused; mirror / reversed order
  invariant. Alsenan pins: REPRODUCED, the classes, 2.950 / 0.250 reproduced, both check rows, every m3 by hand,
  engine minus governing 0, no position in the summary.
- Lessons-register row proposed:

| Date | Problem | Root cause | General rule (scope) | Regression test | Status |
|---|---|---|---|---|---|
| 2026-11-01 | ST-02's straight part was recorded as a drawing conflict (GF frame 27 risers, a 0.250 tread, 1.250 x 1.450 landing vs 28 elsewhere) and queued for a designer decision (T-432 s.3a) | lines of one CAD layer were read in order although the layer carries riser faces below the cut and overhead nosings beyond it; an overhead projection was read as a count | measure goings only within one line family (nosing or face); a flight's count governs from the plan whose cut lies above it, agreeing with the structural plan; a lower plan's overhead lines are a check: a coincident subset is a partial projection (note for the designer), a line where the governing view has none is a conflict (HELD) (any villa, any multi-plan stair) | tests/t438_st02_straight | PROPOSED |

## 8. Lane I proposal

Nothing to wire: no candidate value moves. Restate in the candidate notes of ST02-RS-S / ST02-RS-LD / ST02-RS-A:
'straight part 11 + 5 risers, landing 1.150 x 1.200: 1F plan + ST p.4 (T-438); the GF frame is a partial overhead
projection (first RS-A edge not drawn)'. For T-424 / T-429 (B7): the RS-A tread set binds to 4 treads / 5 risers /
5.750 lm (the governing reading), the T-425 line-table correction stands.

## 9. Not done / uncertain

- The count stays ASSUMED — OWNER-APPROVED (Q-50 A cond): no section exists; the arrival floor edge is the 28th riser
  on every drawing that shows it (1F D22 / D24, ST 315, GF 4B5).
- The landing level is printed on no sheet (s8_7: 'the corner landing level is not printed'); +4.6964 is arithmetic.
- ST p.4 and the 1F frame coincide to 0.1 mm, which suggests one drafted layout shared by both sheets: their agreement
  is the owner's Q-50 condition, not two independent surveys.
- The scans (sheets 03 / 04) were looked at to confirm they draw what the DXF draws; nothing was scaled from them.

self-gate: a (research + tests only; no engine / rule / candidate file) c (Villa K438 hand fixture, normal + the named
adverse case) d (`--check` REPRODUCED without private input) f (no value wired, nothing released) h (counts, goings,
lengths, areas, m3 and handles only; no coordinate, no drawing text, no client data) PASS.
