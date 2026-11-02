# T-476 Handrails along the slope, flight by flight (development villa; method every villa)

Worker 1, 2026-11-02. Research files `research/agents_t476/*` and `tests/t476_handrail_runs/` only; no engine, rule,
knowledge, method, registry or candidate file touched; no candidate quantity changed (section 5 is the stream F
proposal). ERS applied (s.2.1 physical element first, s.2.2 evidence, s.2.4 reconciliation, s.4 rule + test, s.7
lesson). Rules: UP-STAIR-012 v2.0.0 (installed 3D path), UP-STAIR-013 (wall handrail only where shown), owner stair
rules 2026-10-21 / 2026-10-24 (S-9 (4) release per item on its own evidence; HELD stays blank), R-T393-1 .. 3.
No image, client name or title-strip text is copied here.

## 0. What was read (own run, Python 3.11.18, engine 0f0ac54c)

| Source | Used for |
|---|---|
| Drive "Alsenan chalet project" P7757_DXF_COMPRESSED.zip (architectural DXF), by handle | ST-02 riser lines + band arcs (own re-measure), ST-01 shaft bands on GF / 1F / 2F, wall-side scan, D-23, 138A / 1358 continuity |
| same DXF through the released plan reader (`tools/urban_boq_m9.py arch ... --method ARCH_TAKEOFF_V2.9`) | the 14 per-flight FIN.RAILING lines (F-T199-1) with their flight geometry, sides and treads |
| p7757_arch_sheet04.pdf (1F plan), p7757_arch_sheet03.pdf (GF plan), rendered and read by eye | ST-02 against the outer wall, outer-band corner, void and gallery; ST-01 shaft at GF |
| research/agents_t184 (riser counts, MERGED), agents_t164 / agents_t393 (run census, MERGED) | goings / risers per flight; runs RL-01 .. RL-12 |

T-164 and T-393 reproduced first from the private DXF: every run figure identical.

## 1. Flight census (FLIGHT_CENSUS_T476.csv): every flight side, its kind and family

Pitch line of a flight = first nosing to last nosing: plan = goings x going (or the drawn band between the first and
last riser line on a curved flight, one sloped piece per going), rise = goings x riser, installed = hypot.

| Stair / flight | goings x going (plan m) | rise m | open side (rail drawn) | installed lm | wall side |
|---|---|---|---|---|---|
| ST-01 MS1-L | 9 x 0.300 (2.700) | 9 x 0.16667 = 1.500 | well band, A-A rail | 3.089 | shaft wall: NOT_APPLICABLE |
| ST-01 MS1-U | 11 x 0.300 (3.300) | 1.833 | well band | 3.775 | NOT_APPLICABLE |
| ST-01 MS2-L | 11 x 0.300 (3.300) | 11 x 0.168 = 1.848 | well band | 3.782 | NOT_APPLICABLE |
| ST-01 MS2-U | 11 x 0.300 (3.300) | 1.848 | well band | 3.782 | NOT_APPLICABLE |
| ST-01 turns / guard | T-1F-S 0.200 level; G-2F 1.325 level (one band with 1358) | 0 | | 1.525 | |
| ST-01 T-MS1-N (5 winders) | plan 0.200 | 0.833 | well band, profile not drawn | HELD (blank) | corner: NOT_APPLICABLE |
| ST-01 T-MS2-LD | plan 0.200 | 0.168 | closing riser place not drawn | HELD (blank) | |
| ST-01b D1 | 3 x 0.300 (0.900) | 3 x 0.175 = 0.525 | A-A one rail | 1.042 | lift-shaft wall: NOT_APPLICABLE |
| ST-02 RS-C (curved) | 12 goings on band r 1.5555 (2.587) | 12 x 0.160714 = 1.929 | inner band B9C / BA2 | 3.228 (per going) | outer band BA0 / BA1: UNKNOWN (RL-09) |
| ST-02 RS-S | 10 x 0.300 (3.000) | 1.607 | void band B76 | 3.403 | outer wall: NOT_APPLICABLE |
| ST-02 RS-A | 4 x 0.300 (1.200) | 0.643 | west band B75 | 1.361 | east: D-23 floor-edge band at +5.50, horizontal 2.400 (B13-08, RL-06) |
| ST-02 level pieces | volute 0.811, corner 0.050, void edge 1.625, gallery 5.845 | 0 | one band with the flights | 8.331 | |
| ST-03 E1 (outside) | 4 x 0.300 (1.200) per side | 0.680 (0.85 floor to floor) | no rail drawn | HELD x 2 sides (RL-11) | |

Census totals: B7-09 DRAWING-CONFIRMED **33.319 lm** (14 pieces), HELD 4 (T-MS1-N, T-MS2-LD, E1 x 2), UNKNOWN 2 (RL-09,
F-T476-1); B13-08 in this census 2.400 (RL-06); B7-10 none. ST-02 re-measured independently of the T-164 code
(own angles of the 12 curved riser lines): RS-C 3.2283 + RS-S 3.4034 + RS-A 1.3613 + level 8.3307 = **16.3237** vs
T-164 16.324 (0.0003 lm, rounding) -> RL-05 confirmed by a second path. RS-C + RS-S as T-164's one 22-going piece 6.6316
= 3.2283 + 3.4034 (identical).

## 2. The 14 per-flight reader lines (F-T199-1), each bound to one physical flight (READER_BINDING_T476.csv)

| Physical flight | primary reading | other readings of the same flight |
|---|---|---|
| ST-02 RS-C | GF F1 L-7248a8eb | 1F F1 L-6a0af8d2 (seen through the void, reader's own flag) |
| ST-02 RS-S | GF F2 L-da416ad0 (6 of 10 goings) | GF F3 L-4e2dd6e9 (the other 3 goings, SPLIT_PART); 1F F4 L-f2b90e48 (through the void) |
| ST-02 RS-A | 1F F6 L-6c636d1c | GF F4 L-6c67a511 (3 of 4 goings, overhead layer 2) |
| ST-01 MS1-L | GF F1 L-5a12ecf5 (7 of 9 goings: 2.10 vs 2.70 m) | |
| ST-01b D1 | GF F2 L-820a4035 | |
| ST-01 MS1-U | 1F F3 L-ffe82ff4 | |
| ST-01 MS2-L | 1F F2 L-ff7765e4 | 2F F1 L-01db55b3 (through the 2F opening; the reader did NOT flag it) |
| ST-01 MS1-T winders | 1F F5 L-1b41f6db (inner r 0.099 = the well) | |
| ST-01 MS2-U | 2F F2 L-67f25abf | |

14 lines -> 9 physical flights, 9 primary readings (one each), 5 repeat readings. The reader's OPEN / WALL kinds agree
with the census for every line (multiset check; the reader's side_a / side_b carry no orientation). Every flight's sides
already have a home in a run segment, so all 14 lines are **RETIRE** (no figure ever). Why a figure on them would be
wrong, by line: 5 repeats would double the guard; 2 partial readings would undercount MS1-L (-0.6 m plan) and RS-S; RS-A
'both sides OPEN' would bill the D-23 floor-edge guard as a second sloped rail (hypot(1.2, 0.643) = 1.361 instead of the
horizontal 2.400 already in B13-08); RS-C 'outer OPEN' would bill the UNKNOWN RL-09 band.

## 3. What stays HELD / UNKNOWN (blank) and the exact missing fact

- **RL-09 RS-C outer band** (plan 4.035 / 4.455 on the two edges, centreline 4.245; rise 1.929): the 1F plan (sheet04)
  shows the curved flight inside a rectangular corner of the outer walls; the region between the outer band and the two
  walls is blank (no hatch, no level). A 50 mm layer-5 band = the railing graphic of every other run, but if the corner is
  filled / closed the band is a string. The band ends differ between plans: 259.1 deg on 1F (BA1) vs 270.4 deg on the GF
  copy (23E). UNKNOWN, designer RFI.
- **T-MS1-N, T-MS2-LD** (T-393, unchanged): rail profile over the winders / closing riser not drawn.
- **RL-11 E1 entrance stair**, both sides: 0.85 m rise, no guard drawn (render shows one): designer item.
- **F-T476-1 (new)**: GF east-lane well band 47F / 4A4 (solid, layer 5) is 2.750 / 2.800 m long, D1's pitch line covers
  0.900 m of it; 1.875 m (centreline plan) beyond D1 along the well is in no run. Whether D1's rail continues along the
  east lane at +1.00 or the band is a drafting edge is not printed. UNKNOWN, no figure, no line (same class as T-393
  GF-EXT); RFI below.
- B13-08: RL-04 (balcony edge) and RL-10 (fence railing) HELD as before.

## 4. Engine vs freelancer (reference only, never the target)

Freelancer 'internal railing' 18.95 lm, a typed constant with no rows (T-393). Engine candidate V3.0.42 B7-09 valued
17.366 lm (RL-05 16.324 + RL-08 1.042) = -1.584 lm (-8.4 %); proposed 33.319 lm = +14.369 lm (+75.8 %). Causes, named:
+15.953 ST-01 balustrade (RL-07, T-393 segments, drawn on every flight in section A-A) = **ENGINE_RIGHT on scope**
(freelancer omission of one staircase, as T-393); the remaining -1.584 is T-393's decomposition (RL-08 D1 1.042
ENGINE_RIGHT on scope, -0.226 UNRESOLVED). His figure is not adopted under any decomposition.

## 5. Stream F proposal (lane I package after the Checker; no change in this task)

| Family / code | V3.0.42 | proposed | lines |
|---|---|---|---|
| B7-09 FIN.RAILING | 19 lines: 2 valued 17.366 lm + 17 held blank | **33.319 lm** valued: RL-05 16.324, RL-07 split 15.953 (T-393), RL-08 1.042 | 5 HELD / UNKNOWN blank: T-MS1-N, T-MS2-LD, RL-09, RL-11 (+ F-T476-1 reported, no line); 14 per-flight lines retired (READER_BINDING_T476.csv) |
| B13-08 MET.RAILING.GUARD | 6 lines: 21.550 lm + 2 held | 21.550 unchanged | RL-04, RL-10 HELD |
| B7-10 FIN.HANDRAIL | 1 line EXCLUDED_ONLY | NOT_APPLICABLE confirmed | scan: no layer-5 band along any wall side of the 9 flights on GF / 1F / 2F |

Posts / glass (B7-11): posts drawn only on roof railings RL-01 / RL-02 (T-199), none on any stair; stays BLOCKED_BY_SOURCE.
The retirement of the 14 per-flight lines needs the element-register owner line (F-T199-1); this table supplies the
binding, the integration package applies it (registered item codes only: FIN.RAILING, MET.RAILING.GUARD).

## 6. Rules, tests, lesson

- **R-T476-1** (research, any villa): a rail on the slope is hypot(plan, rise) per flight (nosing to nosing, per going on
  a curved flight); the plan length of an inclined run is refused as its installed length; a guard drawn at the floor
  level beside a flight is horizontal.
- **R-T476-2**: each per-flight reader line binds to exactly one physical flight (PRIMARY, PARTIAL_PRIMARY, SPLIT_PART,
  SEEN_THROUGH_VOID, SEEN_THROUGH_OPENING); two primaries refused; unbound refused; a reader line beside the runs never
  carries a figure; reader / census side kinds compared and differences named.
- **R-T476-3**: a horizontal guard drawn as one band continuous with a stair balustrade stays in that run (B7-09: RL-05
  gallery, RL-07 G-2F, checked 138A starts at 1358's end); a separately drawn floor-edge band is B13-08 (RL-06 D-23).
- Tests `tests/t476_handrail_runs` (9): synthetic Villa E, hand 6.633030 lm B7-09 + 0.900 B13-08; adverse: plan length
  billed as slope, inclined without rise, mm as m, guard on a walled side, held with 0, figure on a per-flight line, two
  primaries, unbound line, side difference named, mirrored sides; committed outputs close (33.319, 14 retired).
- Lessons-register row proposed:

| 2026-11-02 | 14 per-flight railing lines sat beside the run lines for 4 days with no owner, while 5 of them were repeat readings of a flight seen through a void / opening and 2 were partial readings | the plan reader writes one line per drawn flight per floor; the run census counts physical guards | bind every reader line to one physical flight with its reading before any figure is placed (one home per flight side); a floor-edge guard beside a flight is horizontal, not a second sloped rail | tests/t476_handrail_runs | T-476 |

## 7. Designer RFI proposals (rfi/B rows; nothing sent)

1. ST-02: the outer edge of the curved flight (band r 2.73 / 2.78): balustrade, or a string against a filled corner? If a
   balustrade, its end (1F plan 259 deg vs GF plan 270 deg).
2. ST-01b: the GF east-lane well band beyond D1 (2.75 m drawn, D1 0.90 m): does D1's rail continue at +1.00 along the well?
3. (open already) ST-03 E1 guards; T-393 RFIs 1-4 unchanged.

## 8. Self-gate and what is missing

Self-gate: no engine / rule / candidate file; research + tests only; non-Alsenan hand fixture with adverse cases;
reproducible with `python3 -I research/agents_t476/t476_alsenan.py <P7757.dxf> <V2.9 BOQ_LINES.json> --write`; no new item
code; no client data in tracked files. Missing: rail heights and materials (not printed); the RFI facts above; the
freelancer's breakdown (his row is a constant).
