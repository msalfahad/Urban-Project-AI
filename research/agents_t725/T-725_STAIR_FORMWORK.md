# T-725 Stair formwork: the 20 HELD STR.FORMWORK.STAIR lines of V3.0.72 restated (research, unwired)

Worker 1, lane S, 2026-11-12, branch `agents/task-T-725`. Files: `t725_rules.py` (R-T725-1..3, every villa),
`t725_alsenan.py` (builder; committed inputs sha256-pinned in `PINS.json`; drawing facts as constants), `out/T725_LEDGER.json`
(one row per line, every face per reading), `out/T725_CENSUS.md`, `tests/t725_stair_formwork` (17 tests). No engine,
candidate, rule / knowledge version, registry or frozen file changed; nothing wired, released or VERIFIED.
Own drawing read: Drive "Alsenan chalet project" / "ST7757 dxf.dxf" (sha256 9f9d1179, = manifest), decoded by the wrapper
into `.work/private` only; `t352_extract.py` re-run (every T-352 length reproduced) plus E1 / 5E2 / winder handles.

## 1. Physical element and methods (ERS s.2.1 / 2.2)

Stair formwork = riser boards, waist / landing soffits, side forms (stringer profile) and landing edges, wherever the cast
face is not against earth, a slab it bears on, masonry or an earlier pour (R-CONC-OWN-1, R-STAIR-FW-SIDE-1). The stair
concrete and its formwork are lane S; finish faces of the same surfaces (T-715 / T-718 soffit plaster, marble risers) are
lane A, never the same item twice. No owner rule measures formwork: the T-281 soffit methods are shown side by side
(O = plan x sec from the first riser line; D = O less the slab-borne foot), and the side profile likewise (O = owner
concrete region; D = clipped at the slab top at a foot on a slab). The line low takes the least coherent reading and
method; nothing is chosen for size.

## 2. Census 20 / 20 by id (V3.0.72; T-474 face map)

| Class after | Lines | m2 (beside, never summed into the released total) |
|---|---|---|
| BOUNDED | 2 | L-9c3643da MS1-L well side **0.679193 .. 0.854426**; L-77ecb282 E1 risers **1.904000 .. 2.380000** |
| AT_LEAST | 2 | L-ffd491ad MS1-L risers + soffit + winder turn **>= 7.678894**; L-739ee9fe MS2-TR turn riser **>= 0.193200** |
| BLANK, cap beside | 12 | sequence (wall / 'B3 (With Stair)' / column / junction) 6 lines, caps 1.215293 / 0.871015 / 0.834477 / 0.979355 / 0.776000 / 0.873917; column D-16 2 (0.045379 / 0.028654); unmarked layer-5 pairs F-T281-03 4 (0.136135 / 0.306303 / 0.087731 / 0.118750) |
| BLANK, no figure | 4 | RS-C curved (RFI-S27, D-08, Q-50 curved HELD); E1 ends, D1 sides, D1 soffit (RFI-S26) |

Lows beside: 10.455287 m2 over 4 lines (stair formwork released family 32.822036 + 4.105400 = 36.927436 m2 unchanged).
Freelancer: no formwork row in any workbook (FREELANCER_NO_ROW): NOT_COMPARABLE, no %.

## 3. Per line (readings A = section 27 risers, B = structural plan 28; 1F = 25)

- **L-ffd491ad** (R4-316..319, MS1-L + MS1-T). Risers A 10 x 1.20 x 0.166667 = 2.000000, B 12 x 1.20 x 0.160714 =
  2.314286. Waist soffit (T-281 plans 2.7 / 3.3 x 1.20 - col 36B 0.025): A O 3.677828 / D 3.225561, B O 4.464083 / D
  4.002826. Turn soffit warped, not drawn: floor = drawn region 1.300 x 1.150 = 1.495 (F-T352-1; T-332's 1.440 low
  understated), no high. Winder risers: A 5 fronts not drawn, each >= 1.150 (R-T718-2) x 0.166667 = 0.958333; B the
  drawn 2F6 / 2F4 / 2F5 / 2F3 = 5.2937 m x 0.160714 = 0.850771. Turn sides on walls: open. Readings AD 7.678895, AO
  8.131161, BD 8.662885, BO 9.124142 -> **AT_LEAST 7.678894** (T-332 held_from 5.706 = 2.000 + a stale 3.706 superseded).
- **L-9c3643da** (T352-01, MS1-L east side on the well, formed on every reading): A O 0.709344, A D 0.679193, B O
  0.854426, B D 0.823675 -> **0.679193 .. 0.854426** (T-352 printed 0.709344 .. 0.869164: high at an incoherent B, low
  without the foot clip).
- **L-77ecb282** (R4-329, E1 risers): own read p.3 18A / 189 / 188 / 17A / 179 each 2.800, spaced 0.300; 179 lies 0.050
  past the band face 178 (ground-beam band 178 / 7DB 0.300). Levels +0.15 / +1.00, 5 risers -> 0.170. Risers 1-4
  4 x 2.800 x 0.170 = 1.904000 stand (riser faces do not contain the held waist); riser 5 (0.476) is the stair's or the
  ground beam's side (GB top level not printed, T-242 / T-253): formed once, owner open -> **1.904000 .. 2.380000**.
- **L-739ee9fe** (R4-325, MS2-TR): the face between the lower plate top +7.516 and the upper +7.684 along 5E2 (own read
  1.150) is exposed whatever the junction is: 1.150 x 4.20 / 25 = 0.193200; it is in neither 12-riser row and in no
  T-352 edge row. Junction soffit step / well end open (C-ST-3, RFI-S25) -> **AT_LEAST 0.193200**.
- Sequence lines L-39d830b1, L-4c0e72c4, L-57fc1652, L-7db84872, L-f93c7248, L-d9790e45: wall / member / junction
  contacts 0 .. face (T-352; ST p.8 notes print no stair sequence). A member-member interface is formed at most once:
  each landing edge on a 'B3 (With Stair)' band shares its cap with that band's own 'next to STAIR' face (R4-261 /
  R4-285 rows), never both. L-d9790e45 cap restated on coherent B: 0.873917 (was 0.888856).
- L-1b5c40de / L-24da5c2a: lane strips of columns 380 (a 0.200 .. 0.225) / 691 (0.100 .. 0.125), CONFLICT D-16: which
  side the schedule section loses is not printed -> column (0) or soffit; caps 0.045379 / 0.028654.
- Four untied hidden-pair strips: a wall below (space under ST-02, RFI-A07) gives 0; a downstand or nothing gives a
  formed underside: caps only.
- L-997777b3 RS-C: Q-50 A cond holds curved parts, rise / helicoid / thickness not printed (RFI-S27): blank;
  information only 13.798024 lm of drawn riser faces per m of rise.
- D-56 lines: L-77ecb282 and L-caa721ed (and concrete L-061e18cf, not this task) now cite RFI-S26 / designer item 7.

## 4. Hand figure from the DXF (Checker pick: MS1-L well side, reading A)

Lane 284 -> 256 1.200; 45A -> 25E 3.300; A from 0.600 later: 10 lines, 9 goings, L = 2.700; r = 4.50 / 27 = 0.166667;
sec = 1.143959, ts = 0.16 x sec = 0.183033. O: 9 x 1/2 x 0.300 x 0.166667 = 0.225000 + 0.16 x 2.700 x 1.143959 =
0.494190 -> 0.719190; head strip (last 0.050 beside the well end): (9r + ts) x 0.05 - (r/g)(2.70^2 - 2.65^2)/2 =
0.084152 - 0.074306 = 0.009846; O side 0.709344. D: less the foot below the GF floor top 1/2 x ts^2 x g / r = 0.030151
-> 0.679193. Second check E1: 4 x 2.800 x 0.170 = 1.904 (handles above).

## 5. Findings

- **F-T725-1** (R-T725-1): T-258 / T-281 / T-352 carried MS1-L reading B (12 + 4 + 12 = 28 structural risers) at the
  section's 4.50 / 27, which is not a buildable stair (28 risers x 4.50 / 27 = 4.667 m, 0.167 m above the storey). Coherent
  B (4.50 / 28) moves highs only: concrete hi 1.054813 -> 1.037005 m3 (T-711's B sum 1.400927 -> 1.383119, its MS1-L
  part used /27, the winder part /28), soffit O hi 4.501478 -> 4.464083, D hi 4.049212 -> 4.002826, side hi 0.869164 ->
  0.854426 m2. No floor moves, no released line moves.
- **F-T725-2**: the Lead ruling moves the D-56 lines to D-67 / D-68; D-67 is the GF winder turn and D-68 is WITHDRAWN.
  The live item holding E1 is RFI-S26 (item 7); used here.
- **F-T725-3**: T-718 bounded the RS-C marble risers at 4.50 / 28 on the curved part, which Q-50 A cond holds and T-711
  keeps blank; the formwork line stays blank. For the Checker / lane A, not changed here.

## 6. Rules, tests, lesson

R-T725-1 one reading = one count with its own rise; R-T725-2 formed stair faces from drawn geometry (risers, winder
floor, soffit O / D, warped-soffit floor = drawn region, side profile O / D, CAP_ONLY contacts, an interface formed once);
R-T725-3 line class by the least coherent reading, never 0, removed items refused. Tests (villa V725, not Alsenan): side
profile O 0.505475 / D 0.479879, soffit O 2.509040 / D 2.133625, risers, winder floor 0.55, warped floor 1.375, mirror /
37 deg rotation; adverse: mixed reading refused, mm refused, generated winder / undrawn region refused, missing waist
never 0, winder flight blank, removed item refused, CAP_ONLY with a floor refused; development villa reproduced and
pinned (20 / 20, none 0, no range from 0).

Lessons row (ERS s.7, proposed): 2026-11-12 | MS1-L reading B overstated at its high end in four merged pieces | the
structural riser count was combined with the section's rise | a reading carries its own count AND its own rise
(R-T725-1, PROJECT-INDEPENDENT) | tests/t725_stair_formwork test_adverse_count_from_one_source_rise_from_another_refused
| PROPOSED.
