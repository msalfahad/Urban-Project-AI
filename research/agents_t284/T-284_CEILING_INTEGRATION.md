# T-284: the ceiling line family into the SAME candidate (ARCH_TAKEOFF_V3.0.32; integration package, Gate B)

Worker 3 (lane I), claim 2026-10-31 13:05 UTC. Development villa, not an accuracy claim; NOTHING RELEASED; the released
default stays ARCH_TAKEOFF_V2.9 + route G (rollback: run V2.9). Drawings named by Drive folder and title only.
ERS read: s.2.1 (element first), s.2.3 (owner method and drawing method side by side), s.3 (build before deduct), s.4
(statuses), s.7 (lessons row below). integrates: T-283 (ceilings r3), T-335 (line binding / FILL), T-281 (stair
soffits, beside only).

## 1. Physical element and what each line now carries

Under each slab face: the horizontal gypsum decor ceiling 0.15 below the slab (Q-48 A), bulkhead vertical faces on free
beam edges with decor on the open side (owner method Q-48 A + Q-43, R-CEIL-R3-2), the paint system on the gypsum (Q-57 A
modified: "measure separately ... actual paintable surfaces"), and APART from them the stair soffit (a stair finish,
T-281), the open dome position (its intrados is the dome finish, designer DCR-4) and the no-ceiling parts (void, shaft,
light well). One surface, one line, one layer per line (R-T335-1).

| Line family | Code | State in V3.0.32 | Evidence status | Lines |
|---|---|---|---|---|
| decor ceiling per room | FIN.CEILING (existing lines restated) | PROVISIONAL (board type not in a plan, O-P8-02 / Q-52 C), material BY_SPEC | DRAWING-CONFIRMED (T-283 r3, Checker Gate A 2026-10-25 05:32; T-335 binding Gate A 2026-10-29 11:41) | 27 restated + 3 added (1F living group, 2F stair-hall part, 1F dressing) |
| line group parents / held stair-well lines | FIN.CEILING | BLOCKED_RFI, BLANK | HELD by name | 4 (1F living x 2, GF and 2F stair wells) |
| bulkhead vertical faces | FIN.CEILING.BULKHEAD (new) | PROVISIONAL | ASSUMED — OWNER-APPROVED (Q-48 A + Q-43) | 13 |
| ceiling paint | FIN.PAINT.CEILING (new) | PROVISIONAL | ASSUMED — OWNER-APPROVED (Q-57 A mod (6)) | 30 |
| stair soffit per stair | FIN.STAIR.SOFFIT (new) | BLOCKED_RFI, BLANK | HELD (T-281 not verified whole; method O vs D) | 2 |
| dome intrados per dome | FIN.DOME.SOFFIT (new) | BLOCKED_RFI, BLANK | HELD (designer DCR-4, Q-44 A) | 2 |
| exterior soffits (5) | FIN.CEILING | unchanged (byte-identical) | as V3.0.31 | 0 |

Owner manual method and drawing-derived method side by side: owner = room ceiling at 0.15 below the slab between the
finish faces, less what is not decor; bulkhead = free beam edge x 0.15 (decor on the open side); paint = decor +
bulkhead faces. Drawing = per slab face on the roof-slab plans (T-139 faces, T-271 r2b, T-283 r3), stair footprints
distributed over every face they cross (R-CEIL-R3-1), dome discs from the drawn circles, beam edges run by run
(R-CEIL-R3-2), bound to the line ids by T-335 (R-T335-1). For the decor area the two agree (the ledger IS the owner
geometry measured from the drawing); the bulkhead drawing-derived candidate (ceiling 0.15 under the soffit, D-40) stays
HELD in each line's record, never a total.

## 2. Result in engineering terms (development villa, own run)

| Quantity (m2) | V2.9 released | V3.0.31 | **V3.0.32** | Freelancer (workbook, quantity only) |
|---|---|---|---|---|
| Interior decor ceiling (FIN.CEILING, valued) | 403.163 (29 lines) | 403.163 | **362.006177** (30 valued lines) | 409.58 |
| change | | | -41.157 (-10.21 %) | -47.574 (-11.62 %): not a verdict on a total while domes, stair zones and class pieces stay HELD |
| Exterior soffits | 44.446 | 44.446 | 44.446 (unchanged) | |
| Bulkhead faces | none | none | **27.9345** (13 rooms) | none |
| Ceiling paint | none | none | **389.940677** (30 rooms) | 452.33 (with 42.75 cove strips, no detail drawn) |
| Stair soffit / dome intrados | none | none | BLANK x 2 / BLANK x 2 | |

Decor 362.006177 = T-335 362.006092 + 0.000085: 10 lines (of 21 where the ledger confirms the line) whose ledger figure equals the line's own floor piece to the
ledger's 4-decimal print keep their unrounded figure (rule in t284_inputs.py, LEDGER_HALF_UNIT; never a rounding move).
Every m2 of the -41.157 is named in T-295 s.4 / T-335 s.3: domes 29.070 HELD, stair pieces 21.201 HELD, no ceiling
15.316, B23 underside 0.173 HELD, less the 16.005 void the GF line deducts; plus the 2.970 dressing omission added.

Per changed line (V3.0.31 -> V3.0.32; the rest in V3_0_32_DIFF.csv): GF-RC99C2A 110.922696 -> 101.137092 (stair under
bands 1.7719, light-well / pocket no-ceiling, + the Checker's 0.777392 slab north of riser 315); 1F-RB72F22 19.050 ->
7.4692 (west dome 11.5808 HELD); 1F-R3CFCFD 19.016545 -> 18.6747 (east dome 0.3418); 1F-R8BDA49 5.0225 -> 3.5998 and
1F-R48AA46 5.0225 -> 3.7815 (west dome 1.4227 / 1.2410); 1F-R48CDA5 4.725 -> 4.2778 (east dome 0.4472); 1F living
59.978 + 16.005 -> both BLANK parents + group line 51.0496 (stair zone 10.725 + 0.1725 B23 foot, east dome 14.0359;
the normal / double-height split is not drawn: carried once, never pro rata); 2F stair hall BLOCKED -> BLANK parent +
part 5.6258 (stair box top 12.974 HELD, Q-72); 1F dressing NEW 2.970 (missing scope, T-295 finding c).

## 3. Rule, tests, registry

- **R-T284-1** (engine/source/arch_v3032.py, every villa): a room's decor in ONE FIN.CEILING figure (a group carries it
  once, parents BLANK naming the group line); bulkhead faces and paint never inside the ceiling area line; paint of a
  room = its decor + bulkhead lines; stair soffit / dome intrados never in a ceiling line and BLANK; HELD never 0;
  bound lines must stand as bound (stale binding stops); inside a restated line only quantity / state / basis / rfi /
  calculation / notes change (a blank parent drops its numeric gross: V3.0.24 NA_GROSS guard caught it on the first
  fixture run); every other line byte-identical; every family guard V3.0.10 .. V3.0.31 re-run on the V3.0.32 lines.
- tests/t284_ceiling_integration (42): villa V284 by hand (hall 48.000 - stair 3.600 = 44.400, bulkhead 6.00 x 0.15 =
  0.900, paint 45.300; living group 24.000 - dome 3.000 = 21.000 over two lines; stair-hall part 4.500; dressing 3.000;
  totals FIN.CEILING 77.900, bulkhead 0.900, paint 73.800); adverse: decor 0, held item 0, paint != decor + bulkhead,
  decor without paint, bulkhead without owner rule, group without cause, one line in two rows, one room in two rows,
  stale binding, dome closure, stair range reversed, applied twice, valued stair soffit, paint drift, ceiling on a
  stair element, wrong unit, missing decor; BOQ_FAMILY_MASTER 1.27.0 (builder, counts, pending V3.0.32, file checks,
  ownership census at full strength, adverse: paint code dropped, B5-04 back to NOT_IMPLEMENTED, unowned soffit code).
- Registry 1.27.0 (research/agents_t284/build_master_1_27_0.py): B5-04 owns FIN.CEILING.BULKHEAD (BLOCKED_BY_SOURCE ->
  IMPLEMENTED_NOT_INTEGRATED); B4-06 adds FIN.PAINT.CEILING beside FIN.PAINT (capability unchanged); NEW B7-15 'Stair
  soffit finish' and B5-06 'Dome intrados finish' (BLOCKED_BY_SOURCE: blank lines only); 102 families; V3.0.32 PENDING.
  The 1.26.0 test takes the newer-registry set-aside the 1.25.0 test took for T-328 (precedent, O-T328-2).

## 4. Who is right (proposals, carried from T-283 / T-335; no new verdict)

Decor vs released engine: ENGINE_WRONG on domes / stair pieces / no-ceiling strips, ENGINE_MISSING on the 1F dressing
2.970; vs freelancer: rooms with no stair, dome or void agree within 1.6 % (finish face vs structural face); totals
UNRESOLVED while 29.070 domes, 21.201 stair pieces, 19.146 class and 12.974 stair-box m2 stay HELD. Ceiling paint:
RULE_DIFFERENCE (freelancer adds 42.75 m2 of cove strips with no detail drawn; owner Q-57 A mod: geometry or an approved
detail first).

## 5. For the Checker (Gate B re-measure; Drive 'Alsenan chalet project')

1. GF-RC99C2A decor 101.137092 = pantry 8.955 + open 91.4047 + 0.777392 (T-335 check 2); bulkhead 11.9189 = 1.7242 +
   10.1947 (B22 1.3274 after R-CEIL-R3-2).
2. 1F-RB72F22 7.4692 = 19.050 - west dome over the room 11.5808 ('ST7757 dxf.dxf', 1F-roof slab plan, dome circle
   r 2.21109); 1F-R0E919A 16.340 (open second-room acceptance item from the T-283 verdict).
3. 1F living group 51.0496 (both parents blank and naming L-43bf1f86); 2F stair-hall part 5.6258 = 18.600 - 12.974.
4. 1F dressing 2.970 = 1.650 x 1.800 (P7757.dxf).
5. The four blank-line families: no figure, no 0; FIN.PAINT wall lines untouched (no ceiling element).

## 6. Lessons row (ERS s.7, proposed)

2026-10-31 | a ceiling integration could carry the 1F living decor on one of two lines (normal / double height) and a
blank parent could keep its numeric gross (T-284) | the line binding gave one figure for two lines whose split is not
drawn; the line-state guard flags a BLOCKED line with a gross | a figure spanning several lines is carried once on its
own group line with the parents blank and naming it (never split pro rata); a blank line drops its gross (any villa,
any trade) | tests/t284_ceiling_integration | PROPOSED.

## 7. Still HELD / not done

Stair soffits ST-01 / ST-02 (blank lines; T-281 figures beside), dome intrados x 2 (DCR-4), 2F stair box top 12.974
(Q-72), GF stair-well top 1.750, class pieces 19.146 (P-2), shafts 3.240 x 3, wet-room board type, coves 288.640 m,
opening edges 49.134 m, bulkhead edges on CONFLICT / HELD beams 45.573 m, the drawing-derived bulkhead candidate (D-40),
the hidden wall band above the decor 0 .. 53.851 m2 (Q-52 C), concrete ceiling plaster NOT SPECIFIED. Exterior soffit vs
GF P-2 class bands (ELEMENT_REGISTER, T-295 (e)): unchanged, both HELD where held, nothing double counted.
