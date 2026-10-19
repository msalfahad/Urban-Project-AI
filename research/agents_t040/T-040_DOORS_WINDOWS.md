# T-040 (with T-053): doors and windows, development villa (Alsenan): m2 code gap, printed heights, opening census

Worker 1, 2026-10-19 15:30-16:30 UTC. Read-only: no engine, rule, test, key map or quantity changed. Development villa,
not an accuracy claim. Counts, widths, heights and sheet references only: no coordinates of client data, no images, no
client names. Rules: UP-OPEN-SCHED-001, UP-DOOR-AREA-001, UP-DOOR-HGT-001, UP-DOOR-CLS-002, UP-QTY-STATUS-001,
UP-KB-PREC-001; owner answers Q-04 (door minimum), Q-14 (heights from the drawing).

## Inputs (session scratchpad, never committed)

| Input (Drive "Alsenan chalet project") | Used for | Note |
|---|---|---|
| P7757_DXF_COMPRESSED.zip / P7757.dxf | engine run, door blocks, plan texts, SE and NW elevation dimensions | sha256 ab54dd55...31cc4 = SOURCE_MANIFEST |
| ST7757 dxf.dxf | engine run (route G, unchanged) | sha256 9f9d1179...38079 = SOURCE_MANIFEST |
| freelancer aluminium workbook (title "الالومنيوم.xlsx") | per-opening freelancer rows (sheet "الكميات"), cover totals (sheet "الغلاف") | |
| p7757_arch_sheet03 / sheet04 / sheet09 / sheet10, Pages_07-08 | GF / 1F plans, NE elevation, section A-A, SW elevation: visual check for printed heights and marks | new single-sheet uploads read fine (3.1-3.4 MB) |

Engine run: working branch 97c4bfc, Python 3.11 venv from requirements.txt, the T-001b command
(`tools/urban_boq_m9.py arch ... --method ARCH_TAKEOFF_V2.9 --structural ... --conventions ..._V6.json`): exit 0,
1455 lines (same count as the scoreboard run). Reproduce the census with
`python3 -I research/agents_t040/opening_census.py P7757.dxf RUN` (read-only).

## Part 1: does ARCH_TAKEOFF_V2.9 emit door / window areas? No: the code gap

The freelancer prices aluminium in m2 (cover sheet: doors 12.0 m2, windows 116.9 m2, total 128.9 m2). V2.9 emits only
counts:

| Engine line (item code) | Unit | Alsenan lines | Area carried | Where |
|---|---|---|---|---|
| ARCH.WINDOW | pcs | 27 (GF 11, 1F 12, 2F 4), all SOURCE_DERIVED count 1 | `calculation.inputs.area_m2` = null on all 27: height NOT_ESTABLISHED (NO_EVIDENCE), sill NOT_ESTABLISHED, class WINDOW_SILL_NOT_ESTABLISHED | engine/source/arch_measure.py:736-760 (V2.8 schedule branch), item at engine/source/boq_line.py:96 |
| DOOR.EXTERNAL.ALUMINIUM | pcs | 2 released (GF 0.90 m, 2F 1.00 m) | `inputs.area_m2` 1.98 + 2.20 = 4.18 m2 with area_state ASSUMED (owner reference height 2.20 m, UP-DOOR-HGT-001: never a confirmed area); summary `area_m2_confirmed` = null | engine/source/door_model.py:768-795 (`boq_lines`), item at engine/source/boq_line.py:109 |
| DOOR.INTERNAL.PVC | pcs | 15 released | ASSUMED areas only | same |
| ARCH.WINDOW_REVEAL | m2 | 27, BLOCKED_RFI | the reveal strip, not the window (V1 key map note stands) | engine/source/arch_v28.py:766-791 |

So a key map V2 has no m2 line to key: `tests/alsenan/T001B_KEY_MAP_V2.json` was NOT written (it would only re-key pcs
lines, which the scorer refuses as a unit mismatch, or convert pcs inputs into m2, which the V1 rule forbids). The rows
stay "unit refused" until the method emits m2 lines. Exact gap for the next method version (new method version, frozen
V2.9 untouched):

- G1 (BOQ items): no m2 item code for an opening. Needed: a window area line and a door area line per opening, unit m2,
  `measured_net = width x height` only when both are established (UP-OPEN-SCHED-001: else the width released, the area
  HELD with the reason); doors in two never-added views AS_DRAWN / OWNER_STANDARD (UP-DOOR-AREA-001); an ASSUMED height
  gives a CONDITIONAL / PROVISIONAL scenario quantity, never a confirmed one (UP-DOOR-HGT-001 "never a confirmed area
  from an assumed height"). Key map V2 then keys these codes; tools/alsenan_keymap.py needs no change.
- G2 (window material class): windows carry `material: BY_SCHEDULE` (engine/source/arch_measure.py:706); no Urban rule
  classes a window as aluminium (UP-DOOR-CLS-002 covers doors only). The freelancer's aluminium sheet holds every
  window. A WINDOWS.ALUMINIUM line needs an owner rule: asked as Q-33.
- G3 (heights printed on elevations are not read): engine/source/arch_v28.py:290 `read_views` binds only level texts of
  sections / elevations (defect L-P9-02). On this villa the window heights that ARE printed are vertical DIMENSION
  chains on the SE and NW elevations (table below), so all 27 windows are held for want of a reader, 7 of them with a
  printed height. Needed: bind each elevation opening to its plan opening (facade match + position along the facade +
  plan width = elevation width within the UP-OPEN-SCHED-001 0.03 m), then read its vertical chain (sill, head).
- G4 (curved glazing without jambs is not an opening): the GF pool glazing (arc printed "657" on the GF plan) is in no
  opening, no room window list and no held record: a SILENT_OMISSION (known defect family D-P9-01/02;
  CURVED_OPENINGS.json keeps only COP-001 on 1F and rejects two other curved gaps).
- G5 (door heights): door height order is schedule / section / elevation / facts / owner reference
  (engine/source/door_standards.py:259 `door_height`), but no reader feeds an elevation-printed door height (the 2.50 m
  printed door on the SE elevation stays at the 2.20 m owner reference).
- G6 (arched heads): no Urban rule says how an arched-head window or glazed door is measured (rectangle to the apex,
  rectangle to the springing, or the true shape). Four Alsenan openings depend on it: asked as Q-32.

## Part 2: tag census (T-053) and opening census

Door / window marks: **0 tag texts in all three plan frames** (top-level TEXT / MTEXT in GF 30, 1F 20, 2F 17 are room
labels, level marks and title-block texts; room-label blocks hold only room names). The 12-sheet set has no door or
window schedule sheet (T-063 sheet list; section A-A, sheet 10, read this run: levels only). So the UP-OPEN-SCHED-001
schedule route has nothing to read on this villa; UNREAD_SHX tags: 0 (no tag exists to decode).

### Doors: 27 door symbol blocks vs 28 engine door elements

Door symbols are block inserts (one or two swing arcs, no text); `opening_census.py` binds each to the nearest engine
door element of its floor:

| Floor | Door blocks | Engine elements | Released (pcs) | Held (PROVISIONAL_NOT_RELEASED) |
|---|---|---|---|---|
| GF | 14 | 15 | 6 (1 ALU 0.90, 5 PVC) | 9: 2 main-entrance candidates (1.00, 2.00), 1 class review 1.00, 1 class unresolved 1.00, 1 ALU 0.90 (width review: opening 0.90 vs frame 1.00), 3 PVC 0.80 provisional, 1 swing with no width |
| 1F | 10 | 10 | 8 PVC | 2 PVC provisional (0.80, 1.00) |
| 2F | 3 | 3 | 3 (1 ALU 1.00, 2 PVC) | 0 |
| All | **27** | **28** | **17** | **11** |

Status per symbol (UP-QTY-STATUS-001): 27 of 27 blocks answered (17 MEASURED as counts, 10 HELD), **0 silent
omissions**. One engine element (GF, 0.80 m, provisional PVC) has no block nearby: a swing drawn as loose geometry or a
double reading of one door; it is held, not released, so no released total is affected (verifier: check).

External (aluminium) doors, engine vs freelancer:

| Opening | Engine | Freelancer row | Width verdict proposal |
|---|---|---|---|
| 2F roof door | released ALU, 1.00 m, height 2.20 ASSUMED, area 2.20 m2 ASSUMED | roof "باب" 1 x 1.00 x 2.40 = 2.40 | width agrees; height not printed for this door -> UNRESOLVED (2.20 owner reference vs freelancer 2.40, neither printed) |
| GF door, driver side | released ALU, 0.90 m jamb to jamb (block leaf 0.79 m) | one of "باب خارجي" 4 x 1.00 x 2.40 | RULE_DIFFERENCE: freelancer 1.00 = the OWNER_STANDARD view (owner Q-04: ordinary minimum opening 1.00 m), engine 0.90 = AS_DRAWN; UP-DOOR-AREA-001 keeps both views, never added |
| GF 2 main-entrance candidates (1.00 single, 2.00 double), 1 class review 1.00, 1 class unresolved 1.00, 1 ALU width review 0.90 | HELD (no released total) | the other 3 of the 4 GF doors | UNRESOLVED: which GF doors are external and which is the main entrance is not fixed by the plan (engine findings MAIN_ENTRANCE_UNRESOLVED, DOOR_CLASS_REVIEW); freelancer counts 4 at 1.00 |

Door m2, engine vs freelancer: engine 0 m2 released (4.18 m2 exists only as an ASSUMED input on 2 count lines; 2.76 m2
more ASSUMED on the held ALU / class-review candidates) vs freelancer 12.0 m2: not comparable until G1. One door
height IS printed: SE elevation, the GF door under the arched porch, "250" from +1.00 to +3.50 (DXF dimension 2500,
dimension chain 850 / 2500 / 550 above the +0.15 path); its plan door is not bound by this run (two main-entrance
candidates), so it stays UNRESOLVED for the binding, not for the value.

### Windows: 27 engine windows vs 29 freelancer windows, and which heights the drawing prints

Printed heights exist only as dimension chains on the two elevations in the DXF (SE and NW; same views on the PDF);
the SW elevation (Pages_07-08 p.1), NE elevation (sheet09) and sections A-A (sheet10) / B-B print levels only, no
opening heights. Engine widths are the plan jamb-to-jamb widths.

| Floor | Opening (engine id, room) | Engine width m | Printed (view: width / height) | Hand area m2 | Freelancer row | Freelancer m2 | Status / proposal |
|---|---|---|---|---|---|---|---|
| GF | OP-022 stair | 1.20 | SE: "120" / "200" (+2.00 to +4.00) | **2.400** = 1.20 x 2.00 | شباك 1.20 x 2.00 | 2.400 | releasable when G1+G3 exist; difference 0.000 (0.0 %) |
| 1F | OP-021 stair | 1.20 | SE: "120" / "230" (+6.50 to +8.80) | **2.760** = 1.20 x 2.30 | 1.20 x 2.00 | 2.400 | ENGINE_RIGHT proposal on the height (printed 2.30); freelancer -0.360 m2 (-13.0 % of hand) |
| 1F | OP-022 master bedroom | 2.4498 | SE: "245" / "160" (+6.90 to +8.50; DXF 1598.6) | **3.920** = 2.45 x 1.60 | 2.45 x 2.00 | 4.900 | ENGINE_RIGHT proposal on the height (printed 1.60); freelancer +0.980 m2 (+25.0 % of hand) |
| 2F | OP-008 stair | 1.20 | SE: "120" / "170" + arched head "88" | HELD | 1.20 x 2.00 | 2.400 | arched head: no rule (Q-32) |
| 1F | OP-016, OP-017 living (sea side) | 1.5523 each | NW: "155" / "300" full height from +5.50 floor, arched fanlight | HELD | 2 x 1.55 x 3.00 (شباك المسبح) | 9.300 | arched head: no rule (Q-32); widths agree (1.5523 vs 1.55) |
| 1F | COP-001 curved, master bedroom over the pool | 3.2895 (MAX_RADIUS_ARC; chord 2.6917, mid-band arc 3.1331) | NW: chord "269" / "305" to the springing + arch "45" | HELD | 3.15 x 3.00 | 9.450 | arched head (Q-32) and curved width basis; freelancer 3.15 ~ engine mid-band arc 3.133 |
| GF | OP-019 saloon, sea side | 6.3316 | plan "633"; NW: one GF pool glazing "430" (+1.00 to +5.30) | HELD | 6.33 x 4.30 | 27.219 | the "430" is drawn on the NW view; whether it is this glazing or the curved one (next row) is not bound by this run: UNRESOLVED binding |
| GF | curved pool glazing, master bedroom | **none** | plan arc "657" | - | 6.57 x 4.30 | 28.251 | **SILENT_OMISSION** in the engine (G4); FREELANCER_RIGHT on existence |
| GF | OP-004, 014, 015, 016 (driver, 3 baths) | 0.60 x 4 | none printed | HELD | 4 x 0.60 x 0.80 | 1.920 | height not printed (freelancer 0.80 unprinted) |
| GF | OP-006 kitchen, OP-024, OP-023, OP-028, OP-029 | 1.50, 1.50, 1.00, 1.9549, 1.9549 | none printed (SW elevation: drawn, no dimension) | HELD | 1.50, 1.50, 1.00, 2 x 1.95 at 2.00 | 15.800 | widths agree within 0.005; heights not printed |
| 1F | OP-001, 002, 013, 014, 015 (baths, laundry) | 0.60 x 5 | none printed (NE elevation: drawn, no dimension) | HELD | 6 x 0.60 x 0.80 | 2.880 | freelancer 6, engine 5: the sixth 0.60 window was not located in the plan by this run (not measured) |
| 1F | OP-003 master bedroom, OP-012 living | 1.5523, 1.00 | none printed | HELD | 1.55 x 2.00, 1.00 x 2.00 | 5.100 | heights not printed |
| 2F | OP-003 stair, OP-004 bath, OP-005 maid | 1.00, 0.60, 1.20 | none printed | HELD | 1.00 x 2.00, 0.60 x 0.80, 1.20 x 2.00 | 4.880 | heights not printed |

Window census status (UP-QTY-STATUS-001), 30 drawn windows (27 engine + the GF curved glazing + the unlocated 1F
sixth bath window as a freelancer claim): 27 HELD (count released, area held), **1 SILENT_OMISSION** (GF curved pool
glazing, 6.57 m printed arc), 1 not located (1F sixth bath window: freelancer only, not measured), 0 MEASURED in m2.
Widths, engine vs freelancer: GF 17.84 vs 24.40 m (-6.56 m = the missing 6.57 curved glazing), 1F 15.60 vs 16.05 m
(-0.60 m one bath window, +0.14 m curved basis), 2F 4.00 vs 4.00 m.

Window m2, engine vs freelancer: engine 0 m2 released (27 held) vs freelancer 116.9 m2: not comparable. By hand from
printed values and existing rules only, 3 windows are releasable: 9.08 m2 (2.40 + 2.76 + 3.92) against the
freelancer's 9.70 m2 for the same three (-0.62 m2, -6.4 %); that is 7.8 % of the freelancer's window m2. 4 more
(about 21.15 m2 of the freelancer's rows) wait on the arched-head rule (Q-32) and 2 pool glazings (55.47 m2 of his rows,
47 % of the window total) on the curved-glazing reader (G4) and the "430" binding; the other 19 have no printed height
on any sheet and stay HELD (owner Q-14: heights from the drawing, never a usual size).

## Hand check (accept: 3 windows, 2 doors)

1. GF stair window OP-022: plan opening 1.20 m (engine 1.2000); SE elevation width "120", vertical chain 1850 / 2000
   (+0.15 path to +2.00 sill, +2.00 to +4.00 head): 1.20 x 2.00 = 2.400 m2. Freelancer 1.20 x 2.00 = 2.400 m2.
2. 1F master-bedroom window OP-022: plan 2.4498 m; SE elevation "245" wide, chain 2201.4 / 1598.6 (sill +6.90, head
   +8.50), printed text "160": 2.45 x 1.60 = 3.920 m2. Freelancer 2.45 x 2.00 = 4.900 m2: he used 2.00 where 1.60 is
   printed.
3. 1F stair window OP-021: SE chain 2500 / 2300 / 2000 on the stair tower (+4.00, +6.50, +8.80, +10.80); window "230"
   from +6.50 to +8.80: 1.20 x 2.30 = 2.760 m2. Freelancer 1.20 x 2.00 = 2.400 m2.
4. 2F roof door (released ALU): plan jamb to jamb 1.00 m, block leaf 0.89 m (+ frame); no elevation or section prints
   its height: height NOT printed -> engine 2.20 owner reference (ASSUMED, not a confirmed area), freelancer 2.40;
   neither is printed: UNRESOLVED.
5. GF driver-side door (released ALU): plan jamb to jamb 0.90 m (engine 0.90), block leaf 0.79 m; height not printed:
   width AS_DRAWN 0.90 vs freelancer 1.00 = owner minimum (Q-04): RULE_DIFFERENCE (two views of UP-DOOR-AREA-001).

A window with no printed height stays HELD (19 here), never 0 and never a usual size.

## What was learned

- This villa's architectural set has no door / window marks and no schedule: heights come only from dimension chains
  on two elevations. The schedule reader (V2.8) therefore can never release an area here; an elevation-chain reader
  (G3) is the general fix and would release 3 rectangular windows today.
- The freelancer applies uniform heights (2.00 windows, 0.80 bath windows, 2.40 doors) where the drawing prints
  1.60 and 2.30 on two of the three checked windows: on printed openings the engine's hand result is 0.62 m2 lower.
- The largest aluminium items (two GF pool glazings 6.57 / 6.33 x 4.30 = 55.47 m2, 43 % of the freelancer's 128.9 m2)
  depend on curved glazing without jambs (missed) and on binding the one printed 4.30 height.

Gate 1 (no lost openings): doors 0 silent omissions of 27 symbols; windows 1 silent omission (GF curved pool glazing).
Gate 2 (schedules / architectural ledger): door and window m2 not emitted (G1-G6).
