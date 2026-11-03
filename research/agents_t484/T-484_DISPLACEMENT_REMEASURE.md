# T-484: pits backfill, the four unverified displacement components re-measured from the drawing

Worker 1 (lane S), 2026-11-03, run session_01E6cPnd7V1pcXGj9e62Tj9K. Development villa, not an accuracy claim. Research
only: no engine module, method version, rule / knowledge file, candidate line or released quantity changed. ERS s.2-4,
s.7 applied; level basis S01 ESTIMATED (owner-accepted): footing underside -1.50, underlay 0.07 + blinding 0.10 under
it, EG +-0.00 (T-357 DERIVED). Owner earthworks notes 2026-11-02 17:20 / 17:45 / 18:00 govern; Q-71 not involved.

Files: `displacement_remeasure_v1.py` (DISPLACEMENT_REMEASURE_V1, every villa: neck to EG, strap end in the pit margin,
ground-beam solids with columns to the necks / each plan point once / high end stopped on the solid below, scenario
union; HELD never 0), `t484_alsenan.py` (own read of 'ST7757 dxf.dxf', sha 9f9d1179, by layer and handle) ->
`summary_t484.json`, `NECKS_T484.csv`, `BEAM_PIECES_T484.csv` (handles and values only). Tests
`tests/t484_displacement/` (villa R484 by hand, normal + adverse, 4 frames: plain / mirror / rotate 30 / rotate 90 +
shift; development-villa records).

## 1. Physical elements (ERS s.2.1)

Pits backfill = pit excavation (zone plan in the plot, outside the pool envelope, EG -> formation -1.67) minus every
solid below EG inside that plan, ONCE at its own position. The four components re-measured here:
- **Neck**: column below the GF, its schedule FOUNDATION section, from its footing TOP (-1.50 + H) to EG (the part
  above EG is zone Z2). The column owns its footprint (R-CONC-OWN-1), so no beam solid may be counted there.
- **Strap end**: the strap solid between the footing face and the pit edge (0.10 projection margin), printed section.
  Soffit level D-15 not printed: the strap lies below EG on every reading, so the plan x section stands.
- **Ground-beam solid over the pits**: blinding strip (beam + 0.10 each side) and beam below EG, by category; depth
  printed (MAIN_EXT bottom on N.G.: blinding only, exact; MAIN_INT_D wholly above EG: 0) or a designer item
  (D-33 / D-35: a range from the shallowest reading to the deepest physically possible: down to the footing + underlay
  top over a footprint, to the pit blinding top over the margin).
- **Scenario footing (F10 + F)**: one excavation over the union of the footings of the scenario.

## 2. Results, both methods side by side (m3)

| Component | T-350 r2 (worker 3) | T-484 own DXF re-measure | Status / cause of the difference |
|---|---|---|---|
| 29 necks | 5.153642 | **5.154000** (sum of schedule sections 4.86 m2, plan x (1.50 - H)) | AGREE +0.000358 (0.007 %): T-350 r2 placed CN on F4 at its LABEL point (0.0003 m2 inside the pool envelope); the drawn outline 17C8 is 0.40 m clear: F-T484-1 |
| C8 on F14 | 0.24 .. 0.27 | **0.24 .. 0.27** | stays a RANGE: drawing CONFLICT. Foundation-plan mark C8 (schedule 0.30 x 0.90) vs plan text 30X80, drawn 0.80 AND the ground-beam plan labels this column C7 (0.30 x 0.80) (new evidence, F-T484-2); designer item, never the larger figure |
| strap ends (5 ends in the 24 pits) | 0.179630 | **0.179618** (SB1 0.035; SB2 0.050933 + 0.050961; SB3 0.021393 + 0.021331) | AGREE -0.000012 (0.007 %): exact margin geometry vs the slope factor. Sections from the schedule rows on the sheet (SB1 70 x 50; SB2 100 x 50, the 80 x 50 insert lies off the sheet, RFI-099; SB3 50 x 40); drawn widths 0.700 / 0.9877 / 0.5011, axes 4.550 / 2.2926 / 3.2577 m (Checker 2.2927 / 3.2580) |
| ground-beam solids over the pits | 2.043877 .. 15.082310 | **2.022337 .. 10.672549** | range NARROWED 4.43 m3 (below); stays a range: D-33 / D-35 sections are designer items (not a drawing conflict, a missing section) |
| ext main GB trench outside the pits | 1.391722 .. 1.418002 | **1.432834** (own strip 27.919513 m2 vs T-253 L x 0.50 = 27.9956, -0.27 %); in the pits 1.359118 | CLOSES to one value (the route-G dL range was a piece-through-a-column effect); of it 0.229565 beyond the plot line (S06 clip, HELD like the pits' beyond-plot strips) |
| F10 + F zone excavation | 7.2645 .. 9.352 | **7.2645 .. 8.39175** | F-T484-3: T-478 / T-350 r2 SUMMED the F10 and F grown plans although inside the 3.25 frame the two footings overlap 0.36 .. 0.72 m2: one excavation = the union, 4.35 .. 4.85 m2 (not 5.25 .. 5.60), never above the drawn outline 5.025 m2. Stays scenarios (S02), never mixed |

Ground-beam solids, by category (low partition: blinding-only beams own their strip; high partition: the deeper
category owns a crossing): ANNEX_EXT_D35 0.425217 .. 3.420315; MAIN_INT_D33 0 .. 4.963137; ANNEX_INT_D33 0.102 ..
0.808298; MAIN_EXT 1.359118 (exact; 1.344797 of it outside the D-33 / D-35 crossings); MAIN_INT_D 0 (above EG);
upper boundary G.B 0.340006 m2 x 0.40 = 0.136002 (T-350 r2 0.136008, AGREE).

Reconciliation T-350 r2 -> T-484 (high end; without the upper G.B): 14.946302 (route-G pieces) -> **13.882944** own
pieces (the band cut at every column standing in it: route-G pieces running through a column, dL > 0, on 7D4+F8 /
137+138 / 136+7D5 / 7DC+7DD / 7E7+7E8 / 7E0+FD carried the column square 0.09 .. 0.233 m2 each; crossings once; the
arc 157+158 over its common span) -> **13.765068** zone plan as the excavation (the beyond-plot parts of 7D0+FC /
7E0+FD / 7D4+F8 / 136+7D5 strips, 1.18 m2, were displacement for an excavation that excludes them: F-T484-4) ->
13.758780 column footprints -> **10.536546** the high end stopped on the footing + underlay top (a beam cannot pass
through a solid already deducted: overlap counted once; -3.222 m3, F-T484-5). Low end 1.907869 -> 1.886334.

## 3. Pits backfill

Excavation 208.164757 (S01, Checker AGREE) - verified displacement 71.925255 (blinding, underlay, footings) - the
re-measured four 7.595955 .. 16.276167 = **119.963335 .. 128.643547 m3** (T-350 r2: 115.553920 .. 128.622353; width
13.068 -> 8.680 m3). Named residual range: D-33 / D-35 beam sections 8.650 m3 (designer items, RFI), C8 mark conflict
0.030 m3 (drawing conflict). Disposal stays HELD (dry-mass inputs, Z2). Status: ESTIMATED (S01) on the excavation;
the displacement components DRAWING-CONFIRMED geometry, ranges where the drawing does not print the section.

## 4. Findings (for the Checker)

- **F-T484-1** neck CN on F4: label point used as the section centre; the drawn outline 17C8 is 0.40 m clear of the
  pool envelope: +0.000358 m3 (necks 5.154000). Rule: a solid's position is its drawn outline, never its label.
- **F-T484-2** C8 on F14: three sources read 0.80 (plan text 30X80, drawn 0.80, ground-beam plan label C7) against
  the foundation-plan mark C8 (0.90): still a CONFLICT of marks (range 0.24 .. 0.27 stays); add the GB-plan label to
  the engineer RFI. Also: C4 on F4 (108D) drawn 0.25 x 0.50 and C on F 166A drawn 0.30 x 0.40 vs schedule / printed
  30X50 (the printed text agrees with the schedule: schedule governs, drawn-outline basis would be -0.0635 m3).
- **F-T484-3** F10 + F scenario: union not sum (above).
- **F-T484-4** beam solids over pit plans BEYOND the plot line were deducted from an excavation that does not include
  them (zone plan in the plot only): displacement and excavation must use one plan.
- **F-T484-5** the D-33 / D-35 high end let a beam pass through the footing and its underlay over the footprint.
- **F-T484-6** route-G pieces that run through a column (dL > 0) carry the column square in their plan; the neck
  already owns it (MAIN_EXT low end handled it by dL x 0.50; the high ends did not).

## 5. Engine vs freelancer; who is right

Earthworks are absent from the freelancer's BOQ and from the released V2.9 + route G: no comparison. Verdict proposal:
UNRESOLVED for the D-33 / D-35 sections and the C8 mark (designer items); the necks, straps, upper G.B and main
exterior strips: drawing-confirmed geometry, re-measured twice (T-350 r2, T-484) AGREE within 0.01 %.

## 6. Rule, regression, lessons (ERS s.7)

R-T484-1 (every villa, PROPOSED): a displaced solid is measured once, at its drawn outline, inside the SAME plan as
the excavation it is deducted from; a column / neck owns its footprint through every beam; a crossing belongs to the
deeper element; an upper bound may not pass through a solid already deducted; a scenario of several footings digs
their union. Regression: villa R484 (normal; adverse: crossing once, straddling piece, column inside a piece, the
footing stop, drawn width vs printed section, missing level / section / rule = HELD, union vs sum, 4 frames).
Lessons row proposed: 2026-11-03 | earthwork displacement deducted for areas the excavation plan excludes, and upper
bounds passing through deducted solids | build displacement on the excavation's own plan and stop every bound on the
solid below | F-T484-4 / -5.
