# T-349: spatter dash (B4-05) bound face by face to the V3.0.24 plaster / backing lines and the T-337 exterior faces (development villa; every villa by R-T349-1 .. 7)

Worker 3 (lane A row; lane I had no claimable row), claim 2026-10-30 03:05 UTC, run session_01E6cPnddo9Y76FhPcLAdwyx.
Integration dependency of a later lane I row (MISSING category B4-05). Research only: no engine module, rule,
knowledge or registry file, candidate line, released line or V2.9 cell changed; released default stays V2.9 + route G;
nothing released. Joint mesh (B9-03) is NOT touched (OWNER PACKAGE item 2 / Q-77). No drawing was read in this run: every
input is a merged ledger of this repository; no coordinate, client name or drawing content is committed. ERS applied:
s.2.1 (physical element first), s.2.2 (owner method record beside the drawing-derived faces), s.2.4 (closure in m2,
every residual named), s.2.7 (no owner question: the scope is answered, every open item is an existing designer /
specification hold), s.3 (one face one carrier; layer order), s.4 (rules + normal and adverse tests), s.7 (lesson row).

## 1. Engineering question and answer

**On which substrate is spatter dash applied, and under which candidate line does each face's spatter sit?**
Answered rule first (row instruction): OWNER_QUESTIONS_ANSWERED.md, OWNER_QUESTIONS.md and OWNER_SESSION_CHANGES.md
hold no newer spatter / bond-coat answer (grep 'spatter|dash|rough|bond coat|طرطش': only the T-317 / Q-77 mesh text).
The governing record stays **OD-V3B-4 .. 7 (owner, 2026-10-04, research/external_engine_lab/
alsenan_v3b_owner_decisions.json)**: tiled faces SPATTER DASH -> TILE PREPARATION -> TILE ("items TILE_PREP /
SPATTER_DASH m2 and WALL_TILE_NET m2 kept separate"); dry internal SPATTER -> ROUGH -> SMOOTH -> PAINT; external Sigma
SPATTER -> ROUGH -> SMOOTH -> SIGMA; stone SPATTER -> CLADDING. So spatter is on **every finished wall face, block and
concrete alike**; the substrate is information beside the face, never the scope (T-317 R-T317-2, kept).
Physical layer order decides the carrier: spatter is thrown on the substrate and is covered by the next coat, so its
row is bound to **the line of the coat directly above it**: dry face -> the FIN.PLASTER line; tiled face -> the
tile-preparation coat, which V3.0.22 (T-331, Gate B) carries as the room's FIN.PLASTER backing line (20 mm 1:4, =
OD-V3B-4 TILE_PREP), the tile line named only as `via`; exterior face -> its T-337 face key (owner line beside).

## 2. Candidate identity (V3.0.24) without a re-run

V3.0.24 (T-338, MERGED dd4c9f8f, json `19394733`) = V3.0.22 (json `7199c8b6`) + V3.0.23 STR.CONC.PARAPET lines (every
V3.0.22 line asserted byte-identical, T-319) + V3.0.24 text / state fixes ("no quantity, no state word, no range and no
line id changes"). The builder asserts: the T-347 V3.0.24 census has FIN.PLASTER 67, FIN.WALL.TILE 18, FIN.EXT.FINISH 3
(= the V3.0.22 extract of T-340), no spatter / B4-05 line exists, and each of the 7 FIN.PLASTER rows of
V3_0_24_LINE_STATE_FIXES.csv keeps measured_net, range and evidence state equal to the V3.0.22 line (FORMULA_END text
only). So the binding uses the V3.0.22 line figures as V3.0.24's.

## 3. The binding (SPATTER_BINDING_T349.csv, 271 rows, double count 0 m2)

| Family | Rows | Carrier | Determinate m2 | HELD m2 | Blank / UNKNOWN |
|---|---|---|---|---|---|
| Dry plaster lines (incl. 22 door-through-wall reveal lines) | 36 | 36 FIN.PLASTER lines | 234.9481 (24, OA) | 489.4810 .. 545.4606 (9 lines) | 3 HELD blank: GF_01 / GF_04 (annex G2), ST-2F (T-173) |
| Wet / pantry faces (T-329 faces = T-331 backing lines) | 115 (105 faces + 10 walk-class residual terms) | 18 FIN.PLASTER backing lines, tile line as via | 340.3038 (73 rows on 12 lines, OA: faces 342.0474 + residual terms -1.7436) = 307.9616 wet + 32.3422 pantry | - | 42 rows on 6 lines HELD blank (annex GF-02/03/05/06 G2 / Q-54 B; GF-10/11 level T-088) |
| Exterior faces (T-337 keys) | 109 | 3 storey lines + 4 parapet-outer + plinth + slab-edge (T-337) | DC 708.8146 (83) + OA 159.1450 (6: door heads 2.20 Q-55 C) | 29.7603 .. 70.6467 (11 faces) | 9 slab-edge faces HELD blank (depth Q-68 C) |
| Exterior items (T-337) | 11 | parapet inner x4, parapet top x4, frame x2, divider | 5.4150 (2F top, DC) | 88.8329 .. 121.1151 (7 items) | 3 UNKNOWN (frames, divider: profile / level not printed) |
| **Interior** | 151 | 54 lines | **575.2519 = the live FIN.PLASTER family of V3.0.24** | **489.4810 .. 545.4606** | 45 rows blank |

**Exterior at line level** (one figure per owner line, the granularity T-317 used; FILL_T349.csv): determinate
**386.5305 m2** (1F storey 234.5255 DC, 2F storey 117.3050 OA part, parapet outer GF 14.3850 / 2F 14.9000 DC, parapet top
2F 5.4150 DC), HELD **605.4373 .. 678.6059 m2** (GF storey 376.6941 .. 410.1791 held by W02 0 .. 28.485 and D-GF-07
0 .. 5.000; parapet outer annex / 1F; plinth; parapet inner x4; parapet tops x3), 1 line blank, 2 UNKNOWN. Face level
shows the GF storey line's 28 determinate faces beside its 2 held ones (the line itself stays HELD, never a point).
Not bound (named): 13 NOT_APPLICABLE plaster lines (taken off, NOT_APPLICABLE_T349.csv); the 4 membrane upturn-zone
faces (T-324: "never plaster": the waterproofing's edge protection, no spatter); exposed soffits (stair soffit 10.725,
pool-court soffit 12.834 m2: OD-V3B-4 .. 7 are wall rules, HELD by name as in T-317); boundary fence faces (other trade).
**Pending carriers** (PENDING_T349.csv): the T-326 reveal rows of the merged T-340 FILL table have no V3.0.24 line yet:
5 door reveals 3.930 m2 OA, 27 window outside reveals 9.667 m2 DC (W02 jambs HELD beside), 7 held blank; their spatter
row follows the carrier when lane I lands T-326 (FILL rows marked "after T-326"); D-GF-07 stays at its line's 1.28 ..
1.40 until T-326 narrows it to 1.400.

Hand checks (own, from the merged ledger figures): GF-13 backing faces 6.81 x 3.65 = 24.8565 - D-GF-12 1.760 - W06
0.480 = 22.6165 (8 rows sum 22.6165 = line L-302f7235); 1F NE-2 face 80.934 - W19 0.480 - W20 0.480 - W24 2.325 = 77.649
(row 77.649); 2F storey 125.160 - 7.855 = 117.305 (4 rows); pantry 38.29215 - 2.20 - 2.25 - 1.50 = 32.34215 (6 rows +
residual 0.0037 = line 32.3422). Every interior line closes on its candidate figure and every exterior line on the
T-337 FILL net (R-T349-5, asserted in the build).

## 4. Faces changed since T-317, before -> after, with cause (CLOSURE_T349.csv)

| T-317 host | T-317 (m2) | T-349 (m2) | Delta | Cause |
|---|---|---|---|---|
| 35 dry plaster lines | 234.9481 + 489.4811 .. 545.4607 | 234.9481 + 489.4810 .. 545.4606 | 0 / -0.0001 | L-31db3c83 1F-11: T-317 took the 6-dp T-244 constants 61.46265 / 61.71775, the line prints 61.4626 / 61.7177 (rounding) |
| pantry L-721a0f14 | HELD blank | 32.3422 OA | +32.3422 | T-331 filled the pantry room-face line with the backing under the pantry tile (T-312 NO LINE) |
| 17 wall-tile lines | 307.9616 + 6 blank | the same m2 on the 17 backing lines | 0 | re-bound tile -> backing (layer directly above the spatter); faces = tile faces, closure 0 (T-329) |
| 1F storey | 234.5255 DC | 234.5255 DC | 0 | unchanged |
| 2F storey | 132.2050 OA | 117.3050 OA | -14.9000 | band +13.90 -> +14.40 is the 2F parapet's outer face (T-337 rule 1, T-311) |
| GF storey | 387.2852 .. 420.7702 | 376.6941 .. 410.1791 | -14.6710 + 4.0800 | annex band +4.30 -> +4.80 moved to PARAPET-OUTER ANNEX; the 1F SE-1 face on the annex roof (T-317 NO_LINE 4.0800) lies in the GF storey by levels |
| lower-roof face | 4.0800 DC | 0 (in GF storey) | -4.0800 | moved, not lost |
| parapet outer | 68.2978 .. 73.6758 | 97.5067 .. 103.8469 (of which 29.2850 DC) | +14.6710 +14.9000, -0.3622 lo / +0.6000 hi | the two bands above; T-324 C3 (1F NW-2 chord vs arc), C5 (annex B34 face 0 .. 0.600) |
| plinth | 71.6886 .. 72.7498 | 71.6886 .. 72.7498 | 0 | unchanged (finish not printed; spatter under Sigma or cladding alike) |
| **not in T-317** parapet inner above the upturn | - | 67.4114 .. 99.5575 HELD | + | finished plaster face (owner trade PLASTER_PARAPET_INNER): **T-317 omission (F-T349-1)** |
| **not in T-317** parapet tops | - | 5.4150 DC + 21.4215 .. 21.5575 HELD | + | plain top (section A-A), a finished exterior face: **T-317 omission (F-T349-1)** |
| **not in T-317** slab edge over open air | - | blank HELD (9 faces) | + blank | finished face, depth not printed (Q-68 C) |

**Totals against T-317 (line level, m2):** determinate 913.7202 -> **961.7824** (+48.0622 = pantry +32.3422; exterior
-14.900 - 4.080 + 14.385 + 14.900 + 5.415 = +15.720); HELD 1,016.7526 .. 1,112.6565 -> **1,094.9183 .. 1,224.0665**
(lo +78.1657 = interior -0.0001 + GF storey -10.5910 + parapet-outer held part -0.0762 (annex in +14.6710, GF out to DC
-14.3850, C3 -0.3622) + parapet inner +67.4114 + parapet tops held +21.4215); blank hosts 10 -> 12 lines (pantry left
the blank set; slab edge, frames, divider joined). Residual after the named causes: 0.0000. Every move is a re-binding
or a scope the merged ledgers settled after T-317; no physical face changed size.

## 5. Substrate (concrete vs block) per face (SUBSTRATE_T349.csv, 218 interior face rows)

The T-317 split is per register wall SIDE (T-274 run pieces cut at column outlines, beam bands and slab faces; owner
band). A room face of T-250 / T-329 is usually a PART of a side (its length differs from the side's), and no committed
crosswalk places a face's interval on the run stations, so the side's concrete share is **never pro-rated to a face**
(R-T349-6). Result: ESTABLISHED 2 faces (1F-09|1F-W19 6.03 and GF-12|GF-W22 10.5385 m2 band, both all block, no column
in the run); HELD 216: 62 partial faces (the side's split shown beside: face m2, concrete m2, block m2 and the concrete
sources COLUMN / MEMBER_BAND member ids), 82 on sides T-317 holds (band or block top not established), 72 not register
wall sides (column faces, off-wall pieces, residual terms, walls without a census run). Exterior: T-337 face keys are
drawn outline sides and register walls are census runs, no crosswalk: HELD per face; the T-317 side totals stay beside
(GF 29.1524 concrete of 96.3000 = 30.3 %, 1F 38.7532 of 134.4484 = 28.8 %, 2F all held). Physically certain classes
named: slab-edge faces are concrete; parapet faces RC or block above the upstand (material HELD, T-319). The split does
not move any spatter quantity (spatter covers both substrates); it feeds a later bond-coat-by-substrate rate question
only if the owner's rates distinguish them (none does today).

## 6. FILL table for the lane I row (FILL_T349.csv)

One proposed **NEW B4-05 SPATTER DASH** line per carrier: 54 interior (36 dry + 18 backing), 19 exterior (3 storey,
4 parapet outer, plinth, slab edge, 4 parapet inner, 4 parapet top, frame, divider), 34 PENDING after T-326 (32 valued
13.597, 7 blank; 5 PENDING rows are FIN.PLASTER door reveals and 27 window outside reveals, plus held arch / window-in
/ gate rows). Each row: host line, unit m2, rows, rows blank, quantity OR lo / hi OR blank, status, source. HELD rows
carry no quantity (test); a bounded row carries its range only; UNKNOWN carries nothing. Lane I wires these as
`<host>#SPATTER` lines whose figure is DERIVED from the host line in the same run (so a later host change moves its
spatter line with it, never a frozen copy), with the evidence status of the host.

## 7. Engine vs freelancer (unchanged from T-317, restated on the new carriers)

His workbook 'المساح الداخلى والسجما' prices spatter 433.83 m2 'wet rooms and kitchens' (= his wall-tile total) + 70.7125
m2 under skirting (282.85 m x 0.25 typed) = 504.5425 m2, interior only. Like for like on the 11 wet rooms: **307.9616 vs
295.44 = +12.5216 m2 (+4.24 %)** = height +43.1933 (owner G1 3.65 / 3.35 vs his 3.00) - doors 23.10 - windows 4.92 -
length 2.652, residual 0.0002 (T-329 reconciliation). Verdict proposals: wet rooms **RULE_DIFFERENCE** (height basis);
under-skirting band **RULE_DIFFERENCE, not additive** (inside the dry population under OD-V3B-5; his 0.25 m printed
nowhere); dry interior and exterior **RULE_DIFFERENCE** (he includes spatter in his plaster / Sigma rates; OD-V3-4 makes
it a separate item). No villa total is compared (different scope).

## 8. Findings for the Checker / Lead

- **F-T349-1 (scope omission in T-317, HELD + DC):** the parapet inner faces above the upturn (67.4114 .. 99.5575 HELD)
  and the parapet tops (5.4150 DC + 21.4215 .. 21.5575 HELD) are finished exterior faces under OD-V3B-6 / 7 that T-317
  did not host; added here. The 4 upturn-zone faces are excluded (waterproofing protection, T-324 "never plaster").
- **F-T349-2 (rounding):** T-317 used the 6-dp T-244 constants on L-31db3c83 (0.00005 m2 per bound); the binding follows
  the line's printed 4 dp.
- **F-T349-3 (pre-existing, ledger form):** the T-312 / T-329 wet-face ledgers carry a signed WALK-CLASS RESIDUAL row per
  room (GF-16: -0.524 m, -1.9126 m2), a contour closure term, not a face. The spatter rows keep it (family
  INT_WET_RESIDUAL, the only row allowed negative) so each line closes; no quantity changed. Named for the Lead: a future
  face-station crosswalk should resolve it into real faces.
- **F-T349-4 (gap, information only):** per-face substrate split HELD on 216 of 218 interior faces for want of a face ->
  run-station crosswalk (T-250 face intervals on T-274 stations); proposal: one research row (lane A) if a substrate-rated
  item ever needs it.
- OD-V3B-4 "no general plaster on a tiled face" and the T-331 backing coat do not conflict: the backing is OD-V3B-4's
  TILE PREPARATION layer (its own line), the spatter lies under it.

## 9. Rules, code, tests

- R-T349-1 .. 7 (research/agents_t349/t349_spatter_binding.py docstring; project-independent research rules, not a rule-file
  version; provenance OD-V3B-4 .. 7, OD-V3-4, T-317 R-T317-2 / 3, T-331, T-337, T-340, WORKFLOW_CONTROLS s.5).
- Builder research/agents_t349/t349_alsenan.py (`--write`, `--check` reproduces every output byte for byte).
- tests/t349_spatter_binding/test_t349_spatter_binding.py: NON-Alsenan hand fixture K349 (dry room 40.02, bath backing
  faces 20.64, exterior 18.60 DC + 8.20 .. 10.20 HELD; villa 79.26 determinate, range never added) and adverse: one face
  under two lines refused; a tiled face on its tile line while a backing carries it refused; spatter under tile refused
  where the rule excludes tile; HELD as 0, HELD with a figure, UNKNOWN with a number, HELD without reason refused; no
  answered record holds the item; host drift and a held row under a determinate host refused; negative area only for a
  residual term; mm read as m refused; mirror order and mm input identical; substrate split never pro-rated.
  test_t349_alsenan_pins.py: committed outputs reproduce; one face once; interior determinate = live FIN.PLASTER
  575.2519; hand checks GF-13 / NE-2 / W02 range; FILL held blank never 0 and PENDING 13.597; closure moves only the
  pantry (+32.3422) and the 4-dp rounding; an edited backing face stops the build.

## 10. For the Checker (re-measure)

1. OD-V3B-4 .. 7 wording (json above); no later answer narrows spatter (grep over OWNER_QUESTIONS*, OWNER_SESSION_CHANGES).
2. V3.0.24 = V3.0.22 on the 67 FIN.PLASTER / 18 FIN.WALL.TILE lines (T-338 fix rows text-only; T-347 census).
3. Two hand rows: GF-13 backing 22.6165 (T-329 faces by id), 1F NE-2 77.649 (T-337 face + OPENINGS by id).
4. F-T349-1 parapet inner / top as finished faces (T-337 ITEMS_T337.csv by item name).
5. The closure residual 0 on CLOSURE_T349.csv (exterior moves = T-337 s.2 table).

Lessons-register proposal (ERS s.7): *Problem*: a preparation coat ledger hosted wet faces on the tile line and missed
two finished exterior faces (parapet inner, parapet top). *Root cause*: the carrier was chosen by trade, not by the layer
that physically covers the coat, and the host list was taken from the face lines that existed then. *Rule*: a
preparation coat is bound face by face to the line of the coat directly above it (tile prep before tile), one face one
carrier, and its scope is re-derived from the current face binding of every finished face, not from an earlier host
list (every villa). *Test*: tests/t349_spatter_binding. *Status*: PROPOSED.
