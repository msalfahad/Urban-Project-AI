# T-701 plaster / paint reference reconciliation on ARCH_TAKEOFF_V3.0.69 (lane A, research, unwired)

Worker 2, 2026-11-11. Candidate of record V3.0.69 (T-687 Gate B PASS, line index e908a5f1). A REFERENCE COMPARISON:
freelancer agreement is never proof and nothing here is a verification. No engine module, method, rule / knowledge
version, registry or candidate file changed; no line moves. Files: `t701_rules.py` (R-T701-1 .. -3, every villa),
`t701_alsenan.py` (builder, inputs sha256-pinned, `--check`), `out/T701_RECONCILE.{json,md}` (all tables),
`tests/t701_plaster_paint_reconcile/` (26 tests). Inputs are repository files only: the V3.0.69 line index, T-556 per
room gross / deductions, his workbooks as parsed cells (FREELANCER_RAW_ROWS, by sheet row), and the merged T-128 r3 /
T-173 / T-680 / T-686 terms (cited). No drawing re-read this run; no client data or workbook text stored.

## 1. Physical elements and face classes (ERS s.2.1)

One finish owner per face. DRY wall: plaster coat to the structural slab / roof underside (Q-72) + paint to the
finished ceiling (owner G1, Q-48 A). WET wall: spatter (plasterer) + levelling render to the tile top (tiler; the
engine's room FIN.PLASTER line IS this render) + the band above the ceiling to the soffit (T-690, plaster). SHAFT: full
exposed height (Q-72). RETURN: door / opening jambs and head. Stair flight soffits: CEILING (Q-57). Census of V3.0.69
(every non-excluded line once, asserted to the board totals):

| class | FIN.PLASTER (m2) | FIN.PAINT (m2) |
|---|---|---|
| DRY rooms (11 HL lines) | HELD 840.646 .. 895.896 | 217.208 released (4) + HELD 459.991 .. 526.511 (7) |
| SHAFT (3) | HELD 143.604 .. 157.770 | HELD 141.654 .. 155.820 |
| RETURN (30) | 24.150 released (27) + 3 blank (A-GF-01, A-1F-01, D-GF-15) | no line (omission) |
| WET render (18) | 340.304 released (12) + HELD 93.015 .. 148.134 (6) | 17 'above wall tile' + GF-07 EXCLUDED |
| WET band above ceiling (18) | 24.131 released (4) + HELD 54.701 .. 98.894 (14) | - |
| EXCLUDED (superseded route) | 13 | 14 |
| **total** | **388.584 + 1,131.966 .. 1,300.694 = 1,520.550 .. 1,689.279** | **217.208 + 601.645 .. 682.331 = 818.853 .. 899.539** |

His statements: plaster rows 4-26 gross 1,209.385, paint rows 4-27 gross 1,249.375 (= his plaster rows 1:1 + his
rows 18-19 stair soffits 39.99); he deducts HALF his opening list once on each statement (58.2475), net 1,151.1375 /
1,191.1275. His wet walls are not in his plaster: they are his spatter row 433.83 (= his wall-tile total, T-317).

## 2. PLASTER: engine 1,520.550 .. 1,689.279 vs his net 1,151.138 (+32.09 .. +46.75 %), exact bridge

his gross - engine = -311.165 (engine low) .. -479.894 (engine high); + his half step 58.2475 = his net - engine.

| cause (m2, his - engine) | at engine low | at engine high | verdict |
|---|---|---|---|
| (2) KEY SCOPE: wet render 17 + bands 18 in the engine key, his wet faces are his spatter row | -498.448 | -589.822 | RULE_DIFFERENCE (key scope) |
| (1) DRY height: his flat 3.60 / 3.40 / 3.50 vs the soffit 4.29 / 3.99 / 3.79 | -137.635 | -137.635 | RULE_DIFFERENCE (engine on Q-72) |
| (3) DRY openings in full per room (Q-73) at the engine minimum | +110.154 | +110.154 | RULE_DIFFERENCE |
| (3) DRY held deductions (W02 / lift door / arch heads, beam ends) | +55.251 | 0 | HELD |
| DRY lengths: his runs vs the drawn faces (1F-13 +35.33, 1F-10 +20.74, others -1.75 .. +3.82) | +55.789 | +55.789 | ENGINE_RIGHT (T-128 two traces) |
| GF-02 wash (his row 9, a wet room in his dry list): length -1.62, height +7.96 .. +2.52, door 1.76, arch 0 .. 2.494 | +10.597 | +2.660 | RULE_DIFF / HELD |
| SHAFT: his two rows with no drawn face (2.50 x 5.40; 11.25 x 3.60) | +54.000 | +54.000 | UNRESOLVED |
| SHAFT: his box vs the drawn faces (south open void side) / pier returns he omits | +12.637 | +12.627 | ENGINE_RIGHT |
| SHAFT: build-up b + drawn deductions and held items (remainder of the T-173 / T-680 gross) | +34.679 | +20.523 | HELD |
| RETURNS: his 14 doors x 0.20 x 5.70 vs 27 valued returns by id | -8.190 | -8.190 | UNRESOLVED |

So the +32.09 % is the key, not the faces: like for like (dry rooms + shaft, same layer) the engine is
**984.250 .. 1,053.666 vs his 1,169.125 gross (-15.81 .. -9.88 %)**, BELOW him, because his gross carries no
per-room deductions (110 .. 165 m2) and 54 m2 of rows with no face, which outweigh the engine's higher plaster
height (+137.6 m2). Beside, not summed: engine wet render faces 433.319 .. 488.437 vs his spatter 433.83 (different
coat on the same faces; reference only). Per floor (dry): GF his 388.08 vs 349.37 .. 386.74; 1F 441.265 vs 394.14 ..
407.61; 2F 94.86 vs 97.13 .. 101.54.

## 3. PAINT: engine 818.853 .. 899.539 vs his net 1,191.128 (-31.25 .. -24.48 %), exact bridge

his gross - engine = +430.522 .. +349.836.

| cause (m2) | at engine low | at engine high | verdict |
|---|---|---|---|
| (3) DRY openings in full per room (Q-73) at the engine minimum | +106.771 | +106.771 | RULE_DIFFERENCE |
| (3) DRY held deductions | +41.854 | 0 | HELD |
| (1) DRY height: his flat height vs G1 3.65 / 3.35 / 3.15; annex H 2.494 .. 3.25 (Q-54 B) | +42.591 | +17.925 | RULE_DIFFERENCE |
| DRY lengths | +55.789 | +55.789 | ENGINE_RIGHT |
| (2) GF-02 wash row 9: full-height porcelain, no paint face | +24.300 | +24.300 | RULE_DIFFERENCE |
| (5) his stair flight soffits (rows 18-19) in his wall paint: CEILING class | +39.990 | +39.990 | RULE_DIFFERENCE |
| (6) RETURNS: the engine has no paint return line; physically 19.17 .. 20.25 m2 painted | +15.960 | +15.960 | ENGINE_OMISSION (T-561; T-569 row not wired) |
| SHAFT: no-face rows 54.00 UNRESOLVED; box / returns +12.65 ENGINE_RIGHT; paint top +1.93 RULE_DIFF; b + deductions +34.68 .. +20.53 HELD | +103.266 | +89.100 | mixed |

Like for like (dry + shaft): engine 818.853 .. 899.539 vs his 1,169.125 (-29.96 .. -23.06 %): per-room deductions
(106.8 .. 148.6), his 54 m2 no-face shaft rows, his length surplus (55.8, ENGINE_RIGHT) and his heights (17.9 ..
42.6) are the whole of it. (4) External faces in the internal lines: none (shaft lines exclude the outside faces,
T-314); OP-009 is a through-wall reveal of an external door (1.08 m2, RETURN): which side is facade render is not
established, named only.

## 4. ENGINE_WRONG found: the two annex dry plaster lines carry a point inside a bounded datum (R-T701-2)

GF-01 (L-b1529955) and GF-04 (L-1ddc23d5) plaster are priced at one scenario S = 3.79 (T-556 drawn section: +4.30 -
0.05 - 0.16 - 0.30; reproduced exactly: 76.28133 - 10.791 - 0 .. 3.79 arch - 0.236; 47.375 - 4.22). The annex slab
top is bounded by a Checker-merged record, s = 3.544 .. 4.30 (R-T678-2), so S = s - 0.46 = 3.084 .. 3.84 (T-686, Q-54
B: no point). Their own paint lines and the four annex wet lines already carry that bound (T-686, wired in V3.0.69);
the plaster lines do not (the T-676 finding F-T676-2, now quantified):

| line | V3.0.69 | corrected HELD bound | change low / high |
|---|---|---|---|
| GF-01 plaster | 61.46433 .. 65.25433 | 20.127 x 3.084 - 10.791 - 1.0 x 3.084 - 0.236 = **47.960668** .. 20.127 x 3.84 - 10.791 - 0.236 = **66.26068** | -13.503662 / +1.00635 |
| GF-04 plaster | 43.155 | 12.5 x 3.084 - 4.22 = **34.33** .. 12.5 x 3.84 - 4.22 = **43.78** | -8.825 / +0.625 |

Status HELD (BOUNDED, Q-54 B datum; W11 / W12 hole areas taken below S as T-686 states: if a hole reached above S at
the low datum its deduction would shrink, so the low end stays a valid lower bound). Code effect if wired (lane I):
FIN.PLASTER HELD 1,131.966 .. 1,300.694 -> **1,109.637 .. 1,302.326**; vs his net +30.15 .. +46.89 %. The
main-house roof rooms stay at their D-39 scenario: no merged record bounds that roof build-up (designer item, not an
owner question, ERS 2.7 not met).

## 5. Verdict proposals (Checker)

- PLASTER.INTERNAL key: RULE_DIFFERENCE of scope (-498.45 .. -589.82): the scoreboard key adds the wet render + bands
  (35 lines) to a reference that holds only dry faces. Proposal for the Lead (keymap, not this task's file): key the
  dry + shaft + return classes against his plaster rows and the wet render beside his spatter row.
- DRY heights: plaster ENGINE_RIGHT on Q-72 (his height RULE_DIFFERENCE); paint ENGINE_RIGHT on Q-48 A. Lengths
  ENGINE_RIGHT (T-128). Per-room deductions RULE_DIFFERENCE (Q-73 full vs his half once).
- SHAFT: ENGINE_RIGHT on scope; 54.00 UNRESOLVED (his rows by id needed). RETURNS: plaster -8.19 UNRESOLVED (his door
  list by id); paint ENGINE_OMISSION (HELD, 19.17 .. 20.25 painted, frame depth not printed). Soffits and wash:
  RULE_DIFFERENCE (class).
- GF-01 / GF-04 plaster: ENGINE_WRONG (bound too narrow), corrected bound above.

## 6. Rule, test, lesson

R-T701-1 room bridge LENGTH + HEIGHT + DEDUCTIONS = his gross - engine net per end (exact; blank lines listed,
never 0; his half step on the whole statement only); R-T701-2 a held line covers its datum's merged bound at both
ends, a point inside it is NARROW; R-T701-3 one finish per face (render, no paint, under full-height porcelain).
Tests: villa V701 by hand (4 x 3 room, soffit 3.00 / ceiling 2.80, door 1.98: plaster 40.02, paint 37.22, bridge
-0.82 / +1.98; tiled wet room render 23.44 + band 1.80, no paint; datum bound 24.90 .. 33.90) + adverse (mm / cm
heights, paint on tile, ceiling above soffit, net above gross, blank / 0 as a value, low > high, float, a pair that
does not close, an unknown cause, datum low > high, deductions over the face) + development villa pins.
Lesson row (ERS s.7, proposed): 2026-11-11 | the plaster key showed +32 % while like for like the engine is 10 .. 16 %
below the reference | the key mixed the wet render and the band above the ceiling with a reference that prices only
dry faces | compare a finish key by face class and layer; a line that hangs on a datum bounded by a merged record
carries that bound, never one scenario (every villa) | tests/t701 | PROPOSED.

## 7. For the Checker (re-measure two rooms)

1. GF-04 annex driver room plaster: 12.5 lm x S, S = 3.084 .. 3.84 (R-T678-2 / T-686), openings W04 0.48 + D-GF-03
   1.98 + D-GF-04 1.76 = 4.22 -> 34.33 .. 43.78 (line 43.155 at S 3.79).
2. 1F-04 dry room: his 17.30 x 3.40 = 58.82. Plaster 63.141 = 17.4 x 3.99 - 6.285: LENGTH -0.34, HEIGHT -10.266,
   DEDUCTIONS 6.285 -> -4.321. Paint 52.005 = 17.4 x 3.35 - 6.285: LENGTH -0.34, HEIGHT +0.87, DEDUCTIONS 6.285 ->
   +6.815.

Missing: his door list and his two shaft rows by id; roof build-up D-39; frame depth of painted returns; an own
drawing re-measure this run (values rest on merged, Checker-passed ledgers; 4 of 11 dry rooms independently
re-measured earlier by T-634 / the Checker).
