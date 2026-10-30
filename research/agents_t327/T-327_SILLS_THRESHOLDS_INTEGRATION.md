# T-327: sills and thresholds in the candidate (ARCH_TAKEOFF_V3.0.29), integration package for Gate B

Worker 3 (lane I), 2026-10-30 UTC. Development villa, not an accuracy claim. Opt-in candidate only: the released
default stays ARCH_TAKEOFF_V2.9 + route G; nothing is released. No client name, coordinate or image is committed;
drawings are cited by Drive title only.

integrates: T-325 (MERGED 98f50f0f, Verifier 2026-10-29 04:59 UTC Gate A PASS: the sills / thresholds ledger, every
census opening once), T-340 (MERGED 25c1f52c, Verifier 2026-10-29 16:58 UTC Gate A PASS: the T-327 FILL table bound to
the candidate line ids and the five closure-polygon traces; D-GF-10 kept at 0.800 by the Checker). Inputs:
`research/agents_t327/t327_inputs.py` reads FILL_T327_T340.csv, CLOSURE_TRACE_T340.csv, SILL_THRESHOLD_LEDGER_T325.csv
and STRIP_FLOOR_OVERLAP_T325.csv, each pinned by sha256; nothing is typed; every RETYPE row must equal the T-325 ledger
(m2 = width x depth, m.l = width, 1 pc) or the build stops.

DOWNGRADE-ONLY STEP DGP-T373-LAP (Lead acceptance i): **not applied.** No Checker-issued record exists on the working
head 55da4715 (no verdicts/V3.0.28/DOWNGRADES.json; RUN_LOG 20:22: 'downgrade record DGP-T373-LAP queued'). Per the
row, the sills part is built alone; the 351 STR.REBAR lines and the 22 stair lines are byte-identical to V3.0.28.

## 1. The physical question and the answer (ERS s.2.1, s.3)

The element is ONE strip per doorway at floor level: the drawn clear width (the jamb gap) x the wall thickness
(UP-THR-001), finished in marble where the doorway is wet (URBAN-WET-SERVICE-MARBLE-THRESHOLD v1), in the floor
porcelain continued once where it is dry, and by specification (HELD) at an external entrance; and ONE external sill
surface per raised window (frame to outer face), ONE outside strip per floor-level window. Area, length along the
opening and count are three measures of the one strip.

What V3.0.28 carried: the 26 window strip lines and the W18 sill already filled / added by T-326 (from the same two
ledgers, equal row by row); 10 marble and 7 porcelain doorway strips EQUAL to the ledger; 6 external-entrance
thresholds as point bounds (area kept, material HELD); and **five BLOCKED ARCH.THRESHOLD 'threshold strip CLOSURE' lines
with no figure**, whose own polygons (0.131977 .. 0.218846 m2) are the door symbol's closure polygon, not the strip.

Why the closure polygon is not the threshold (T-340 trace, Checker-merged): the polygon is bounded by the cross walls'
faces, not by the jambs: it runs past the jamb over the wall-end nib and, on three doors, across the cross wall to its
far face. Polygon - (clear width x t) = (nib + cross wall) x t on every door, residual 0.000000 m2 on four and 0.000006
on D-GF-14 (4-dp polygon vertices). D-GF-10: T-340 traced it on the drawn line gap 0.797039; the Checker kept the
D315 symbol's 0.800 (the wall line overruns 2.961 mm into the frame jamb: a drafting overrun, not a narrower opening),
so the excess is restated on 0.800: nib from the frame end 0.0529608 - 0.0029608 = 0.050 + cross wall 0.200 = 0.250 m
x 0.150 = 0.0375 m2 = 0.1575 - 0.120, residual 0.000000.

Rule **R-T327-1** (engine/source/arch_v3029.py, every villa): a threshold = clear width x wall thickness, never the
closure polygon (a polygon offered as the strip, with a traced excess, is refused); wet marble only on a doorway the
wet rule names, never on a dry door or an external entrance; a dry strip is the floor porcelain continued once; an
external entrance is never retyped to a finish line; a strip overlapping a room floor polygon by more than 0.001 m2 is
refused (already in the floor tile line); an untraced closure residual keeps the line BLANK with the residual named; a
floor-level window's outside strip onto a floor is refused unless the floor line is shown to stop at the wall face (never
counted as terrace AND sill); m2 / m.l / pcs carried as three measures (m.l = the width, 1 pc; a relabelled m2 is
refused); one strip one line, one line one opening; HELD blank, never 0.

## 2. BOQ lines (V3.0.28 -> V3.0.29)

| Line | Opening | Before (V3.0.28) | After (V3.0.29) | m2 / m.l / pcs | Evidence (s.5) |
|---|---|---|---|---|---|
| L-cb2fdcac375323371bdf ARCH.THRESHOLD closure | D-GF-02 (wet) | BLOCKED_RFI blank (polygon 0.153542) | NOT_APPLICABLE_WITH_EVIDENCE, successor named | - | retired (superseded: nib 0.0736 + cross wall 0.150) |
| L-791a94968230969c030f FIN.MARBLE.THRESHOLD (ADDED) | D-GF-02 | no line | **0.120 m2** MEASURED | 0.120 / 0.800 / 1 | DRAWING-CONFIRMED; marble OWNER RULE |
| L-95bb76ee6c98edac0179 ARCH.THRESHOLD closure | D-GF-10 (wet) | BLOCKED_RFI blank (0.1575) | retired | - | superseded (nib from the frame end 0.050 + cross wall 0.200) |
| L-1a229f1fead084efb881 FIN.MARBLE.THRESHOLD (ADDED) | D-GF-10 | no line | **0.120 m2** | 0.120 / 0.800 / 1 | DRAWING-CONFIRMED (0.800 = Checker T-340 h) |
| L-8c2040d7c6ecce827316 ARCH.THRESHOLD closure | D-GF-14 (wet) | BLOCKED_RFI blank (0.218846) | retired | - | superseded (east nib + cross wall, west face run, splayed pocket; residual 0.000006) |
| L-3b166c2b5d136302f2dd FIN.MARBLE.THRESHOLD (ADDED) | D-GF-14 | no line | **0.120 m2** | 0.120 / 0.800 / 1 | DRAWING-CONFIRMED |
| L-63c15e31faff037fcdde ARCH.THRESHOLD closure | D-1F-04 (wet) | BLOCKED_RFI blank (0.131977) | retired | - | superseded (nib 0.0798) |
| L-bfdbdaa2d67a5c805f1e FIN.MARBLE.THRESHOLD (ADDED) | D-1F-04 | no line | **0.120 m2** | 0.120 / 0.800 / 1 | DRAWING-CONFIRMED |
| L-a4c323cb1e402c9127d2 ARCH.THRESHOLD closure | D-1F-03 (dry) | BLOCKED_RFI blank (0.185778) | retired | - | superseded (nib 0.0885 + cross wall 0.150) |
| L-fcf3a49c67ae9e730028 FIN.FLOOR.PORCELAIN 'doorway strip' (ADDED) | D-1F-03 | no line | **0.150 m2** | 0.150 / 1.000 / 1 | DRAWING-CONFIRMED; porcelain continued (UP-THR-001) |
| L-56acf34557c315f65bb1 ARCH.THRESHOLD (ADDED, HELD) | gate D-GF-15 | no line | BLANK by name | - | UNKNOWN (width / host wall not established) |

Code totals (A304.code_totals): **FIN.MARBLE.THRESHOLD 1.340 -> 1.820 m2 (+0.480, +35.8 %; 10 -> 14 lines; now every
one of the 14 wet doorways)**; **FIN.FLOOR.PORCELAIN 297.625973 -> 297.775973 m2 (+0.150, +0.05 %)**; ARCH.THRESHOLD
value unchanged (held / bound 1.910 .. 1.910, the six external entrances and three lift sills; blank lines 12 -> 8: 5
retired, 1 added). m.l / pcs beside the m2: marble +3.200 m.l / +4 pcs, porcelain +1.000 m.l / +1 pc. No other item
moves (asserted). Net new physical scope 0.630 m2 (the five strips that had no figure).

Identity: 3,956 -> 3,962 lines; 11 rows: 5 CHANGED (retired), 6 ADDED (5 valued + 1 held); **3,951 byte-identical**
(outside_rows_sha256 ee9fbda9...). Released V2.9: the 5 retired lines exist there BLOCKED (QUANTITY_DIFFERS now: state),
the 6 added NOT_IN_RELEASED. Carried and asserted unchanged (54): 10 marble + 6 porcelain strips EQUAL, A-1F-01 strip
0.150, 6 external-entrance bounds, 26 V3.0.28 window strips and its W18 sill, W17, the two W03 held lines and A-GF-01
blank. Line-by-line diff: V3_0_29_DIFF.csv; per line before / after / m2 / m.l / pcs / material / evidence:
V3_0_29_INTEGRATION_LEDGER.csv (both in the run output, not committed). Against the previous V3.0 (V3.0.28) and the
released V2.9 + route G: as above; no other line differs from either comparison V3.0.28 already reported.

## 3. Owner manual method and drawing-derived method side by side

| | Owner manual method | Drawing-derived (carried) |
|---|---|---|
| Door threshold | UP-THR-001: clear door width x wall thickness per doorway; wet: marble (URBAN-WET-SERVICE-MARBLE-THRESHOLD v1); dry: floor porcelain continued once; external entrance: by specification | width = drawn jamb gap / door symbol frame (T-237, T-340 jamb read, D-GF-10 Checker 0.800); t = T-150; wet / dry from the T-237 room names (T-325) |
| Closure polygon | not a measure | reconciled to the strip by nib + cross wall (T-340 CLOSURE_TRACE), residual <= 0.000006 m2; superseded |
| Window sill | UP-REVEAL-001: its own item; material by specification | frame flush with the room face (room side NONE), outside 0.080 / 0.100 m (T-313 = T-325); V3.0.28 lines carried |

The two methods agree on every retyped strip (the owner's formula on the drawn width and thickness).

## 4. Evidence status, missing and held (WORKFLOW_CONTROLS s.5)

- DRAWING-CONFIRMED: the five retyped strips 0.630 m2 (ledgers Checker-verified; the integrated lines await Gate B).
  The marble / porcelain material of those five: owner rule (UP-THR-001 / URBAN-WET-SERVICE-MARBLE-THRESHOLD v1).
- HELD / UNKNOWN (blank, never 0): gate D-GF-15 threshold (ADDED blank line; width / host wall not established);
  A-GF-01 threshold (line L-868aee12 stays BLANK: the Lead's acceptance ii keeps the arched set A-GF-01 held by name,
  T-377; T-340's 0.150 m2 proposal is a WIDTH_ONLY strip and is NOT applied here, named for the Checker); W17 sills
  (curved, T-302: L-c90d5d6c BLANK); W03 floor strips (V3.0.28 held reveal lines); external window sill material on
  23 sills + W25 / W27 (UNKNOWN, consultant item A13); the six external-entrance threshold materials (HELD, bounds
  kept, unchanged).
- Not in this package: DGP-T373-LAP (no record issued); the GF-14 head-face note (D-T368-1: this package fills no
  FIN.WALL.TILE line and not L-fa408571a8ad; it stays for the wall-tile package).

## 5. Downstream consistency (cross-trade, double count)

- Each opening's strip once: 54 carried strips asserted line by line against the V3.0.28 lines (figure = ledger, blank
  = blank), the 5 retyped and the 1 held strip refused a second carrier (`load_inputs` owner map; `check_strips` on the
  finished lines).
- Room floors: the five closure polygons overlap the room floor polygons by 0.000009 .. 0.000045 m2
  (STRIP_FLOOR_OVERLAP_T325, numeric edge slivers; tolerance 0.001 m2): the strips are in no room floor line, so moving
  them into FIN.FLOOR.PORCELAIN / FIN.MARBLE.THRESHOLD counts them once.
- Waterproofing (T-336 / T-310): D-GF-14 and D-1F-04 membrane pieces equal 0.120 (EQUAL); the D-GF-10 membrane piece
  0.119556 is the side to correct to 0.120 (+0.000444 m2) when T-310 consumes it (Checker T-340 verdict, routed).
- Reveals (T-326): door reveals stay in FIN.PLASTER only; a door's floor face is this strip only (no reveal line books
  it: `check_reveals` re-run on the finished lines).

## 6. Against the freelancer (not proof)

The freelancer's workbooks carry no threshold or sill row (T-325, 885 raw rows): wet-door marble thresholds 14 pcs /
1.820 m2 in the candidate now ALL valued (10 + the 4 retyped) vs 0: **ENGINE_RIGHT by owner rule**, freelancer
omission (-100 % on his side); dry strips 7 pcs / 1.100 m2 (6 + D-1F-03) vs 0: RULE_DIFFERENCE (scope). His 'door steps'
7.70 (m.l in an area column) is the external steps, not this element (T-325: RULE_DIFFERENCE, element).

## 7. Validation

@@VALID@@

## 8. For the Checker (Gate B always-checked lines)

New calculation basis on five lines (always checked): re-derive clear width x wall t for D-GF-02 (INSERT 1EF, jambs
117 / 118, 0.800 x 0.150), D-GF-10 (INSERT 339 D315 0.800 x 0.150, overrun 2.961 mm), D-GF-14 (ARC 334, 2E5 / 2E6,
0.800 x 0.150), D-1F-03 (INSERT C32 D115, AEA / AEB 1.000 x 0.150), D-1F-04 (INSERT C2E D315, C1B-C1D / C1C-C1E 0.800
x 0.150) on Drive 'Alsenan chalet project' / P7757_DXF_COMPRESSED.zip (P7757.dxf); material change (classification):
four to marble, one to porcelain; the retired closure lines carry no figure; the new D-GF-15 held line.

## 9. Lessons-register row (proposed, ERS s.7)

| 2026-10-30 | five wet / dry door thresholds sat two days as BLOCKED closure strips after the ledger and the binding had valued them | the strip line was keyed to the door symbol's closure polygon (bounded by the cross walls) under a 'finish to be confirmed' code, so no package could fill it without retyping it | retire the closure line with its successor named and book the strip once in the finish line the owner rule names at clear width x wall t; supersede a polygon only by a traced nib / cross-wall excess, else HELD with the residual named (every villa) | tests/t327_sill_threshold (normal: villa V327 0.120 marble / 0.180 porcelain / 0.080 + 0.120 sills; adverse: polygon as the strip, marble on a dry door, external retyped, strip inside a floor line, m.l relabelled, terrace and sill twice, held as 0) | PROPOSED |
