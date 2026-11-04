# T-508 stair skirting B7-07 / B7-08 + landings: integration package ARCH_TAKEOFF_V3.0.56 (stream F; method every villa)

Worker 1, 2026-11-04. Gate B integration of the merged T-501 stair-side table (5eded7df; Verifier Gate A 2026-11-04
10:56Z, own re-measure by handle MS2-LD 3.700 lm and MS2-L W side sloped 2.737 / zigzag 3.694 lm AGREE; 1F shaft 9.050
lm at +5.50 ENGINE_WRONG confirmed) into the SAME opt-in candidate, on V3.0.55 (T-488, merge e8143e40; first built as V3.0.55 on V3.0.54, renumbered by the
merge-order rule when T-488 merged first). Released default
(V2.9 + route G) untouched; nothing released. No drawing, workbook, client name or coordinate in this folder.

## 1. Physical element (ERS s.2.1)

A skirting is a strip on a finished wall / column face at the level of what stands against it. Along a flight it climbs
with the flight (B7-07 zigzag = goings + rises, UP-STAIR-010; B7-08 sloped = the rake, UP-STAIR-011: the FORM decides the
family, never the side; an open side carries no skirting, B7-09 owns that edge). On a landing it is level and is
room-trade skirting (FIN.SKIRTING, register ruling STAIR vs ROOM SKIRTING). A room line measured at a floor level along a
shaft where no floor of that level stands measures a strip that does not exist (F-T501-2).

## 2. Owner manual method vs drawing-derived method (side by side)

| | owner manual method | drawing-derived method (this package) |
|---|---|---|
| flight, zigzag | goings + rises along the wall side | plan stations by handle + risers standing in the piece x one riser per flight (recomputed, one riser per flight asserted: MS1 0.166667, MS2 0.168, D1 0.175, RS-S 0.160714, E1 0.170) + column returns |
| flight, sloped | plan run x hypot(run, rise) / run | hypot(plan, level change between the piece's end stations) + returns, recomputed from the stations / levels and asserted equal to the table (RS-S / E1: no stations in the table, carried from T-410, flagged not recomputed) |
| landing | level, with the room skirting | sum of the wall pieces drawn on both plans that bracket the landing (plan + returns, recomputed) |
| 1F shaft at +5.50 | (no floor there: not measured) | each stretch retired only by closure: stair pieces at every level cover it exactly (plan union, residual 0) and none stands at +5.50 inside it (level-aware) |

## 3. Rule R-T508-1 (engine/source/arch_v3056.py)

(1) form decides the family, a side ('wall', 'open side') or an average is refused as a form; (2) one strip one owner,
level-aware (stations AND level band); (3) a room stretch retired only by closure, never where a stair piece stands at
the room floor's level; the moved length is never dropped (each covering piece has its own line); (4) every figure
recomputed and asserted against the table; (5) held / unknown / conflict blank, never 0; millimetres refused.

Why TWO lines per flight piece (one per form family), not one line 'B7-07 | B7-08': the census (T-479) maps a line to a
family by item code, and a code owned by two families is a census issue (DOUBLY_OWNED_CODE). So each piece has a
FIN.STAIR.SKIRTING.ZIGZAG line (B7-07) and a FIN.STAIR.SKIRTING.SLOPED line (B7-08), both BLOCKED_RFI blank with their
own figure beside, never_additive_with each other (boq_line.totals sums one), and the check refuses both valued. When
ORR-007 is answered, an input `form` values that form's line of every wall piece with no re-measure and the other becomes
NOT_APPLICABLE (tested on villa K508).

## 4. Before / after (development villa)

| line | element | before (V3.0.55) | after (V3.0.56) | evidence |
|---|---|---|---|---|
| L-ba3599ec 1F living | 1F-R78C367:skirting | 41.435360 lm SOURCE_DERIVED (gross 52.440) | 32.385360 lm (deduction STAIR-SHAFT-NO-FLOOR 9.050 = E 4.150 + W AF0 1.050 + W AF1 2.250 + returns 0.100 + N ADE 1.400 + N ADD 0.100) | T-501 binding, closure recomputed |
| L-079bc766 1F living range | ...boundary role unresolved | 0 .. 2.200 BOUNDED | NOT_APPLICABLE_WITH_EVIDENCE (W13 / W25 faces carried by MS2-LD.W13 / MS2-L.W2 / MS1-L.W2 / MS1-T.W and MS2-LD.W25 / MS1-LD.N) | T-501 binding |
| new landing MS1-LD | STAIR-SKIRT:MS1-LD:landing | none | 1.150 lm MEASURED | Checker-merged table |
| new landing MS2-LD | STAIR-SKIRT:MS2-LD:landing | none | 3.700 lm MEASURED (W 1.050 + NW 1.300 + NE 0.100 + NE2 0.100 + E 1.150) | Checker own 3.700 AGREE |
| new landing RS-LD | STAIR-SKIRT:RS-LD:landing | none | 1.250 lm MEASURED (0.650 + 0.550 + return 0.050) | T-410 carried |
| 3 held landing pieces | MS1-LD.N, MS2-LD.W13, MS2-LD.W25 | none | BLOCKED_RFI blank | sills / heads vs the landing not printed |
| 22 flight / step pieces x 2 forms | STAIR-SKIRT:<piece> | none | 44 BLOCKED_RFI blank lines (13 HELD-FORM, 6 HELD, 1 CONFLICT MS1-U.E3b, 2 UNKNOWN) | form not chosen (ORR-007) |

FIN.SKIRTING released 212.378592 -> 209.428592 lm (-2.950 lm, -1.39 %; = -9.050 + 6.100); held range 2.200 -> 0 (closed,
carried); blocked lines 4 -> 7. FIN.STAIR.SKIRTING.ZIGZAG / .SLOPED: 22 blank lines each, beside HELD-FORM zigzag 23.300481
/ sloped 17.009049 lm (13 pieces, 53 risers). Every other line byte-identical (asserted); totals move only in the three
codes (asserted). Residual between FIN.SKIRTING and B7: 0 (each piece in exactly one line; the retired stretches carried
by named piece lines).

Own chain (this session, Drive copies P7757.dxf ab54dd55 and "ST7757 dxf.dxf" 9f9d1179 in .work/private only): T-167
v304_run -> research/agents_t508/v3056_run.py (one hub call through T-488 v3055_run / T-480 v3054_run, unchanged):
V3_0_53 **36863f6c**, V3_0_54 **c85c4630**, V3_0_55 **a498fc61** (candidates of record reproduced) -> V3_0_56
**4e25c54f**, 4,989 lines = 4,937 byte-identical + 2 changed + 50 added; research/agents_t508/v3056_apply.py on the
hub's V3_0_55 gives the same 4e25c54f (summary_t508.json). Observation F-T508-1 (for the T-488 owner, no action here):
replaying T-488 V3.0.55 OUTSIDE the hub on the V3_0_54 file gave 627d0ed1, not a498fc61: 6 lines (MAS.BLOCK /
ARCH.WALL_PANEL / ARCH.WALL_VOLUME, 2 walls; formula / rfi text only) of the blockwork remainder
lines list their "closable walls carried on their own lines" in a different order (a set iterated without sorting);
quantities identical, hash not reproducible across processes.

## 5. Engine vs freelancer (recorded, never the target)

Freelancer FIN.SKIRTING 282.85 lm (dry-room gross perimeters along the shaft) and 96 stair skirting PIECES. Candidate
FIN.SKIRTING 212.379 -> 209.429 lm: -24.9 % -> -26.0 %. Verdict proposals: 1F shaft stretches at +5.50 ENGINE_WRONG in the
room line (no floor at that level; hand: ABE 4.150 / AC0 4.500 bound the 1F floor zone), corrected here; MS2-LD level
skirting ENGINE_OMISSION corrected (3.700 lm, Checker own); FIN.SKIRTING vs freelancer RULE_DIFFERENCE (doors deducted,
one face one owner along a stair); stair flights RULE_DIFFERENCE on unit (pieces vs lm) and UNRESOLVED on value until
ORR-007; MS1-U top 0.300 lm UNRESOLVED (arch plan vs ST p.4).

## 6. Missing / uncertain

ORR-007 (form; decides 6.291 lm zigzag - sloped); W13 / W25 / GF window 352-354 / hidden opening 33C / 33D sills and
heads; MS2-TR place; MS1-T winders (S-9); MS1-U top CONFLICT (stays 0.300 in the 1F room line remainder); RS-S.S0 /
RS-C.OUT unknown bands; RS-LD / RS-S / E1 from T-410 not re-read this run (no stations in the table: sloped not
recomputed). Lessons row proposed (ERS s.7): "a piece whose family is decided by a still-open owner choice gets one blank
line per alternative family, never_additive_with each other, never one line owned by two families: the census keys a
family by item code".
