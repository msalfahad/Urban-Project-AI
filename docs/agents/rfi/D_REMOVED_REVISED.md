# D. Removed and revised RFI rows, with evidence (internal; owner 2026-10-29 22:05)

Lead 2026-10-30 00:15-00:25 UTC. Source package: CLARIFICATIONS_CONSULTANT_2026-10-24.md (30 rows S1-S18, A1-A12 at the
Lead's 10-25 check, then S19-S23 and A13 added, plus the missing rows G1-G4). Evidence = merged, Checker-verified tasks
on the engine branch (head b12e10de at this revalidation) and the Checker's CLOSABLE LINES table (SCOREBOARD.md).

## 1. G1-G4: are they fully drafted and source-verified?

| Row | Outcome | Evidence |
|---|---|---|
| G1 CB5 column / neck boundary (C5 35F, C3 365) | REMOVED: settled from the drawings, no question | T-287 MERGED 542b64c7 (Checker Gate A PASS 2026-10-25 07:58): ST p.3 bay levels +0.30 / +0.15 settle both column bases at +0.25 (DRAWING-DERIVED); the neck depth stays only on RFI-S01 (founding level). P-7 loses G1 and is now complete |
| G2 stair turn and waists | REVISED and drafted: narrowed to MS1-T, MS2-TR, D1, E1, RS-C (RFI-S24 .. S27) | T-287 sheet search (G2-a, G2-c, G2-w; Checker PASS): "T 16" is printed on every ST-01 flight, half landing and the turn and on RS-S / RS-LD / RS-A, so the "unprinted waist per flight" part is removed for those; only D1, E1 and RS-C print no thickness |
| G3 tower dome, rings, drums | DRAFTED (RFI-S28, RFI-A05) | T-287 (G3-a, G3-b; Checker PASS): ST p.6 flat B2 panel with no opening / ring; ST p.7 one generic dome detail; drum material not printed |
| G4 GF pantry doorway zone 1.100 m2 | REMOVED: settled from the drawings, no question | T-286 MERGED e861e390 (Checker Gate A PASS 2026-10-25 09:51): the "doorway strip" was an engine defect (a band edge extended 3.8 m past its drawn end); floor area +1.100 m2 DRAWING-CONFIRMED (ENGINE_WRONG_CLASS) |

Source-verification of the citations in A: the Checker's light run re-checks every A question's sheet / detail / handle
(owner 2026-10-29 22:05 (3)). Citations marked "(sheet no. to confirm)" name the drawing by content only.

## 2. Rows removed or moved out of the consultant package

| Row | Change | Evidence / reason |
|---|---|---|
| A7 part D-21 (2F maid-room dome) | MERGED into RFI-S28 (sent once) | T-287 s.5 note: G3 contains D-21 with its structural questions |
| S14 part: lift-pit depth | MOVED to the LIFT SUPPLIER list (CLARIFICATIONS_SUPPLIER) | ST p.14 prints "As Per Lift Manufactures recommendations" (T-204 MERGED 4fbf7627); owner 22:05: lift-supplier matters go to the supplier. The tie-beam section stays with the structural designer (B) |
| Plaster / paint: lift landing door heads L-GF-01 / L-1F-01 / L-2F-01 | MOVED to the LIFT SUPPLIER list | CLOSABLE row 3 names them "BLOCKED BY SUPPLIER" |
| S18 D-61 structural issue date | RECLASSIFIED: document-control clarification (B, its own section), not a design question | owner 22:05; T-195 MERGED 06c2b045 |
| W03 room-side line, W06 wedge | NOT ADDED (never a designer item) | settled by T-250 MERGED 47390c9b; T-286 confirmed (stale scoreboard citation) |
| Pool deck SX-02 recess 0.561 m2 (T-343) | NOT ADDED | the drawings settle it (Checker 2026-10-29 23:05: band face ARC 201 = printed 657 line; recess is the glazing reveal strip) |
| Stair-side / blockwork construction sequence (T-352, 16 sides HELD) | NOT ADDED | construction sequence is the contractor's, not a design question; it stays an internal HELD item |
| Excavation working space, side slope, bulking (T-347) | NOT ADDED | measurement / method conventions are internal (owner 22:05: keep our conventions out); they go to the owner rule library only if ERS s.2.7 is met. The founding level (RFI-S01) is the only designer part |
| Any question whose options state how Urban measures | WORDING REMOVED | the "Options the drawings allow" now list only drawing-based alternatives |
| D-65 (five upper columns) | STAYS OUT | drawing-confirmed absence (Checker); re-opened only if the designer says they exist |
| D-13, D-23, D-29, D-30, D-32, D-56, D-60 | STAY OUT | as in the package s.D (resolved from the drawings, owner decisions, or no quantity effect) |

## 3. Rows revised (kept, with changed content)

| Row | Revision | Evidence |
|---|---|---|
| S2 (Q-28) | SPLIT into RFI-S03 (band section / level) and RFI-S04 (boundary-wall column / pad positions) so each is answerable alone; T-347 adds the boundary lower-band range 5.639 .. 11.033 m3 | T-347 READY F-T347-3 (Checker verdict pending; quoted as a range only) |
| S3 / S15 | S15 split into RFI-S06 (plot-line blinding) and RFI-S07 (straps); the SB3 / F3 strap soffit is its own RFI-S05 | T-230 / T-233; T-347 F-T347-1 (SB3 range 0.0295 .. 0.2683 m3 is the right ledger range) and F-T347-2 (strap blinding 0 .. 0.913) |
| S5 (D-02, D-27) | quantity restated to the T-277 census: 7 runs drawn 5.4421 vs scheduled 5.7665 m3, soffit 8.7140 vs 9.0072 m2; split RFI-S12 (CB10, incl. which band is CB10) and RFI-S13 (the other spans) | T-277 MERGED 9446dfcb |
| S6 | split into RFI-S14 (CB3 / B3), S15 (unlabelled spans), S16 (strips), S17 (east ring) | T-110 MERGED 575df66, T-252 |
| S4 | split into RFI-S19 (C8), S20 (13 columns, by handle), S21 (lift necks) | T-217 MERGED 65fef8fa, T-256 MERGED 74c966b1 |
| S8 | split into RFI-S09 (exterior depth, incl. the annex), S10 (loaded spans), S11 (title basis, < 2.5 m link, 5.00 m span) | T-138, T-242 |
| S23 (FF blinding projection) | ADDED to P-4 as RFI-S08 | T-322 verdict (Checker 2026-10-29 01:55): CONC.BLINDING downgraded, FF HELD >= 2.070 m3 |
| A5 / D-39 / D-06 / D-17 | the structural-level part is RFI-S23 (one question for every roof); the build-up part stays in B | T-112, T-128; T-339 MERGED (roof layers: insulation / protection material UNKNOWN, D-39) |
| A3 (D-53) | W02 is RFI-A01; the main door and SX-01 stay in B | Q-76 answered A (W17 9.870 m2): D-53 W02 is the only remaining windows blocker (CLOSABLE row 6) |
| A6 (D-08, C-ST-4) | split into RFI-A03 (round stair section) and RFI-A04 (MS1-L) | T-111, T-184, T-189, T-192, T-258 |
| A9 (D-48, D-55) | the garden band is RFI-A06; the side passage and D-55 level changes stay in B | T-153, T-157 |
| A12 (D-10) | the dressing-room floor finish is RFI-A08 (it closes the floor-area line); the general schedules request stays in B | CLOSABLE row 2 |
| NEW under-stair F1 / F2 | RFI-A07 (designer item proposed in the T-240 verdict, never filed until now) | T-240 MERGED d07af773 verdict: "ST-02 GF under-stair F1 / F2: floor-finished, closed or solid? 6.1244 m2 HELD" |
| NEW sharmat restraint | queued for B (structural), as a question about whether a restraint is required and its specification, never as our design | owner 2026-10-29 (T-355 answers point 3) |
| S19 - S22 ("SEARCH: Lead to confirm") | search CONFIRMED, kept for B | the Checker's own reads: p.8 note 21 (2026-10-25 12:06: width-indexed wording now in S19), p.10 / p.11 / p.12 schedules and CB11 trace (T-299 / T-300 verdicts: hooks, bar ends and inner links not printed) |

## 4. The nine priority groups: still valid?

All nine stay valid; their content changed as follows. P-1 windows (RFI-A01): YES. P-2 pool (RFI-A02): YES. P-3 footing
(S02, S03, S04, S05): YES. P-4 blinding (S01, S02, S03, S04, S06, S07, S08): YES, closes only with P-3's S03 / S04.
P-5 ground beams (S03, S04, S09, S10, S11): YES. P-6 beams (S12 .. S18): YES. P-7 columns (S01, S19 .. S23): NOW
COMPLETE (G1 settled). P-8 stairs / domes (S24 .. S28, A03 .. A05): NOW COMPLETE (G2 / G3 drafted). P-9 floor area (A06 ..
A08): NOW COMPLETE (G4 settled; A07 added). Details: C_UNLOCK_MATRIX.md.

No owner decision was reopened; no structural quantity, verification status or released (V2.9) cell was changed for this
package.
