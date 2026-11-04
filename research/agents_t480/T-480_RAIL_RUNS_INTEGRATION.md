# T-480 B7-09 stair guardrail runs: integration package ARCH_TAKEOFF_V3.0.54 (stream F; method every villa)

Worker 1, 2026-11-04. Gate B integration of the merged T-476 per-flight census (88e70ffe; Verifier Gate A 2026-11-02
18:40, own re-measure ST-01 MS2-L 3.782209 lm AGREE 0.000 %) into the SAME opt-in candidate. Released default
(V2.9 + route G) untouched; nothing released. No drawing, workbook, client name or coordinate in this folder.

## 1. Physical element (ERS s.2.1)

B7-09 = the guard rail on the OPEN side of a stair flight, installed along the pitch line from first to last nosing
(inclined piece: sqrt(plan^2 + rise^2)), continuing as level pieces where the same band runs along a landing, well end
or floor edge. A wall side with no rail drawn has no B7-09 (UP-STAIR-013: a wall handrail only where shown; B7-10 stays
NOT_APPLICABLE). Posts / glass / infill are not measured here (not printed).

## 2. Owner manual method vs drawing-derived method (side by side)

| | owner manual method | drawing-derived method (this package) |
|---|---|---|
| inclined flight | per flight, open side: sqrt(going run^2 + rise^2) | goings x going (plan) and risers x riser (rise) of the T-184 reconstruction, hypot recomputed by the engine and asserted equal to the census (1e-6) |
| level pieces | landing / floor-edge runs with the same rail | the drawn band length (T-164 / T-393 handles) |
| curved flight | per going | one sloped piece per going (T-476); the engine bounds the per-going sum between the straight pitch line and plan + rise (cannot recompute it from totals), and accepts it only to CONFIRM an already valued run |
| turn over winders | not stated | HELD blank by name: rail profile not drawn |

## 3. Rule R-T480-1 (engine/source/arch_v3054.py)

(1) inclined rail billed along its pitch line, recomputed; plan length for an inclined piece, a rise on a horizontal
piece, a valued turn, mm / cm and a held piece with a length (or 0) are refused; (2) one physical run, one valued line:
the V3.0.30 run lines keep their record (its family guard `check_formwork_metalwork` forbids a figure on a per-flight
line beside a valued run line: the same guard twice), so the flight-by-flight breakdown sits on the run line as pieces;
(3) every plan-reader per-flight line is retired NOT_APPLICABLE_WITH_EVIDENCE against run line(s) that exist; (4) held /
unknown stays blank, never 0; (5) open side only.

Why not one LINE per flight: the task row says "one line per flight"; the candidate's own V3.0.30 guard (every railing
run once; no per-flight figure beside a run) makes a per-flight valued line a double count by construction. The flight
pieces are printed on the run line (formula + record), each with plan, rise and length, so the per-flight before /
after is fully traceable; the held pieces DO get their own blank lines.

## 4. Before / after (development villa)

| line | element | before (V3.0.53) | after (V3.0.54) | evidence |
|---|---|---|---|---|
| RL-07 run (ST-01) | RAIL:RL-07 | BLOCKED_RFI blank | 15.953174 lm PROVISIONAL = MS1-L 3.088690 + MS1-U 3.775066 + MS2-L 3.782209 (Checker own) + MS2-U 3.782209 + T-1F-S 0.200 + G-2F 1.325 | DRAWING-CONFIRMED pieces |
| T-MS1-N (ST-01, 5 winders) | RAIL:RL-07:ST-01:T-MS1-N | none | BLOCKED_RFI blank (new) | HELD: profile over the 0.10 m well not drawn |
| T-MS2-LD (ST-01 half landing) | RAIL:RL-07:ST-01:T-MS2-LD | none | BLOCKED_RFI blank (new) | HELD: closing riser position not drawn |
| F-T476-1 GF band beyond D1 | RAIL:ST-01b:GF east-lane band beyond D1 | none | BLOCKED_RFI blank (new) | UNKNOWN: rail or drafting edge |
| RL-05 run (ST-02) | RAIL:RL-05 | 16.324 lm | unchanged | census 16.323713 AGREE (-0.000287) |
| RL-08 run (ST-01b D1) | RAIL:RL-08 | 1.042 lm | unchanged | census 1.041933 AGREE |
| RL-06 guard (B13-08) | RAIL:RL-06 | 2.400 lm | unchanged | census 2.400 AGREE |
| RL-09 (RS-C outer band) | RAIL:RL-09 | blank | unchanged | UNKNOWN |
| RL-11 (outside steps E1 x 2) | RAIL:RL-11 | blank | unchanged | HELD: no rail drawn (designer item) |
| 14 reader lines (GF 6, 1F 6, 2F 2) | `<room>:flight n` | BLOCKED_RFI blank | NOT_APPLICABLE_WITH_EVIDENCE, naming the physical flight and its run line(s) | T-476 binding, 9 physical flights |

B7-09 FIN.RAILING: 17.366 -> 33.319174 lm (+15.953174, +91.9 %); B13-08 21.550 unchanged; B7-10 NOT_APPLICABLE kept.
Every other line byte-identical (asserted); totals move only in FIN.RAILING (asserted). Chain figures and identity are
in summary_t480.json (own run on the Drive copies).

## 5. Engine vs freelancer (recorded, never the target)

Freelancer B7-09 18.95 lm. Before: 17.366 (-8.4 %); after: 33.319 (+75.8 %). WHO IS RIGHT (proposal):
UNRESOLVED as a whole (1 of 14 census pieces Checker-measured); MS2-L ENGINE_RIGHT by the Checker's own calculation; the
ST-01 run (a second stair with four flights, open well side, section A-A rail) is absent from 18.95 if his figure is
ST-02 + D1 only (16.324 + 1.042 = 17.366 is within 8 % of it): proposed ENGINE_RIGHT on scope for RL-07, to be ruled by
the Checker from the drawings, not from the total.

## 6. Missing / uncertain

The two ST-01 turn pieces and RL-09 / RL-11 / F-T476-1 stay blank; posts, glass and fixings not measured; RL-07 is
PROVISIONAL (5 of its 6 confirmed pieces not own-measured by the Checker). Lessons row proposed (ERS s.7): "a run with a
V3.0.30 record is the only valued carrier of its rail; reader per-flight lines are readings, retired against it, never
valued beside it".
