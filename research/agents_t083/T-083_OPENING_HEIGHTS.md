# T-083: every printed opening height on the Alsenan architectural PDF (hand table, NO REPO CODE)

Worker 1, 2026-10-19 23:24 - 2026-10-20 UTC. Reading only: no engine, rule, test, key map or quantity changed. Development
villa (Alsenan), not an accuracy claim. No image, coordinate, client name or personal data is committed; sheets are cited
by their Drive title, page and view. Rules: owner Q-32 = A (arched: enclosing rectangle to the top of the arch), Q-33 = A
(windows aluminium by default), Q-39 = C (window curved on plan: outer arc), Q-14 / no-assumptions (a height is printed or
HELD, never a typical value, never the freelancer's 2.00 m, never 0), UP-OPEN-SCHED-001, UP-DOOR-AREA-001,
UP-DOOR-HGT-001, UP-QTY-STATUS-001, L-P9-02, drawing-first directive (MISSION.md: a conflict between two drawings is
recorded, not settled).

The table itself is `OPENINGS.csv` (57 rows: 29 windows W01-W29, 28 door elements D01-D28; none silent, none 0).

## Inputs (session scratchpad, never committed)

| Drive "Alsenan chalet project" | Page / view | Read |
|---|---|---|
| Alsenan_Architectural_P7757_Pages_05-06 | p.5 2F plan; p.6 SOUTH EAST ELEVATION 1:100 | full resolution (4672 x 6624 px scan, 157 px per metre) |
| Alsenan_Architectural_P7757_Pages_07-08 | p.7 SOUTH WEST ELEVATION; p.8 NORTH WEST ELEVATION (cut through the court and the pool) | full resolution |
| Alsenan_Architectural_P7757_Pages_11-12 | p.11 SECTION B-B | full resolution |
| p7757_arch_sheet09 / sheet10 | NORTH EAST ELEVATION; SECTION A-A | overview + T-082's full-resolution reading |
| p7757_arch_sheet03 / sheet04 | GF / 1F plans: plan widths and binding | full resolution |
| freelancer aluminium workbook ("الالومنيوم.xlsx", sheet "الكميات") | per-opening rows | rows reconcile to his 116.9 m2 windows + 12.0 m2 doors |

Plan widths and engine ids come from research/agents_t040, t077 and t078 (the engine run itself is outside this run's
execution authorization; door elements are therefore listed by T-040's engine classes, not by element id).

## What the engine gets against the freelancer (aluminium, Alsenan, by hand from printed values)

| Line | Measured by hand | Freelancer, same openings | Difference | Was (T-078) |
|---|---|---|---|---|
| Windows m2, measured | **6 of 29, 26.485 m2** | 24.280 m2 | **+2.205 m2 (+9.1 %)** | 4 of 29, 13.892 vs 14.350 m2 (-3.2 %) |
| Windows m2, held with a printed candidate | 3 (2F stair 2.040, GF curved pool glazing 28.251, 1F living twin 4.812) | 35.301 m2 | not released | - |
| Windows m2, held, nothing printed | 20 | 57.319 m2 | not comparable | 23 |
| Doors m2, measured | **1 height printed: GF main entrance 2.00 x 2.50 = 5.000 m2** (AS_DRAWN; class held) | freelancer has no 2.00 door (4 x 1.00 x 2.40 GF + 1.00 x 2.40 roof = 12.0 m2) | not comparable | 0 |

Measured share: 26.485 m2 of the freelancer's 116.9 m2 windows is now drawing-sourced (22.7 %, was 11.9 %); 28.251 m2 more
waits only on the width rule of the curved glass wall.

### The six measured windows

| Row | Window | Width | Printed height (sheet, view, chain) | Hand m2 | Freelancer | Diff | Verdict proposal |
|---|---|---|---|---|---|---|---|
| W01 | GF stair hall | 1.20 (plan, SE "120") | 2.00: SE p.6, 185 / **200** (+2.00 to +4.00) | 2.400 | 1.20 x 2.00 = 2.400 | 0.000 (0.0 %) | AGREE |
| W13 | 1F stair hall | 1.20 | 2.30: SE p.6, 250 / **230** / 200 (+6.50 to +8.80) | 2.760 | 1.20 x 2.00 = 2.400 | +0.360 (+15.0 %) | ENGINE_RIGHT (2.30 printed) |
| W14 | 1F master bedroom, street end | 2.4498 (plan, SE "245") | 1.60: SE p.6, 220 / **160** / 139 | 3.920 | 2.45 x 2.00 = 4.900 | -0.980 (-20.0 %) | ENGINE_RIGHT (1.60 printed) |
| W15 | 1F living, sea side (left) | 1.5523 (plan and NW "155") | 3.10: NW p.8, **300** to the inner arch + **10** to the outer crown (Q-32 A) | 4.812 | 1.55 x 3.00 = 4.650 | +0.162 (+3.5 %) | ENGINE_RIGHT |
| W17 | 1F master bedroom over the pool, curved | 3.2895 outer arc (Q-39 C; NW chord "269") | 3.50: NW p.8, 20 / **305** / **45** (Q-32 A, the owner's own example) | 11.513 | 3.15 x 3.00 = 9.450 | +2.063 (+21.8 %) | RULE_DIFFERENCE (owner Q-39 C) |
| W18 | 1F sea-side bath (the window T-077 recovered) | 0.50 (plan "50", NW "50") | **2.16**: NW p.8, 84 / **216** / 230 (sill +6.34, head +8.50) | **1.080** | 0.60 x 0.80 = 0.480 | +0.600 (+125 %) | ENGINE_RIGHT (both width and height printed) |

New this run: W18. T-040 and T-077 recorded "height not printed" for this window; the NW elevation draws it as a framed
0.50 m slot with its own chain. Binding by hand: the NW horizontal chain 99 / 31 + 60 / 50 / 43 (frames "10" printed beside
each window) equals the 1F plan sea-wall chain 109 / 101 (filled column) / 50 / 58 (sheet 4): the slot is the bath window.
The freelancer's 0.60 x 0.80 is neither the printed width nor the printed height.

### Held with a printed candidate (not released)

- **W03 GF curved pool glazing**: height **4.30 PRINTED** (NW p.8: 115 pool / 70 / **430** / 20 slab on the pool axis,
  +1.00 to +5.30; the drawn glazing spans 4.95 m on the view = the chord between its jambs, so the 4.30 belongs to this
  glazing, not to the saloon's). This closes T-040's "430 binding" question. Width stays HELD: OWNER_QUESTIONS.md Q-38 has
  no answer of its own on record (the "Answer:" line under Q-38 is the Q-47 stair answer); Q-39's note reads "Q-38 stays
  the printed width". Lead: confirm Q-38 from the owner's main chat. Candidate on the printed arc: 6.57 x 4.30 = 28.251 m2
  = the freelancer's row exactly.
- **W26 2F stair window, arched**: the PDF SE (p.6) chain from the sill (+10.80) is 170 / 5 / 88 / 97 to +14.40, and on
  the PDF the 170 witness ends at the drawn crown of the window arch (measured on the scan: 272 px = 1.73 m above the
  sill). The DXF SE view (T-078) draws the crown 0.50 m above the end of the same 170. Same printed number, different
  drawn window: a conflict between two drawings (**RFI-1**), so HELD; candidate from the PDF 1.20 x 1.70 = 2.040 m2
  (freelancer 2.400).
- **W16 1F living, sea side (right)**: width "155" printed on NW, drawn identical to W15, but the height chain runs through
  W15 only. HELD (candidate 4.812 m2; **RFI-3**: confirm the twin is 3.10).

### Held, nothing printed (20 windows, 27 door elements)

SW (p.7), NE (sheet 9), sections A-A (sheet 10) and B-B (p.11) print storey chains and levels only: GF 0.15 / 1.00 /
4.50, 1F 4.20, 2F 4.20, parapets 0.50 / 1.10 / 1.30, annex 4.00. No sill, head or opening height is printed on them.
GF saloon glazing 6.33 (W02): B-B cuts it with no dimension and the NW view shows the saloon in section, so the
freelancer's 4.30 there has no drawing source (UNRESOLVED, not FREELANCER_RIGHT: the drawing prints nothing either way).
Every interior door drawn on B-B (4 on 1F, 3 on GF, 1 roof door), A-A and NE carries no dimension.

### Doors

One door height is printed on the whole set: SE p.6, chain 85 / **250** / 55 / 45 from the +0.15 court: the door foot is
at +1.00 (top of the five-riser entrance flight) and its head at +3.50. Binding by hand on the GF plan (sheet 3): the only
door at the top of the 2.80 m wide entrance steps on the street end is the double door printed "200" in the 370 chain into
the dining / entrance hall; the SE view hides part of its leaf behind the porch arch. So D01 = 2.00 x 2.50 = 5.000 m2
AS_DRAWN; its class stays held as the engine says (MAIN_ENTRANCE_UNRESOLVED). The freelancer lists no 2.00 door: his
aluminium doors are 4 x 1.00 x 2.40 (GF) + 1.00 x 2.40 (roof) = 12.0 m2, all at 2.40, a height printed nowhere.

## RFI list (elevation, plan or two drawings disagree)

1. RFI-1 2F stair window: PDF SE draws the arch crown at the end of the "170"; the DXF SE draws it 0.50 m higher.
2. RFI-2 GF curved pool glazing: width basis (printed inner-face arc 6.57 vs glass lines 6.66-6.79 vs chord 4.95); Q-38
   answer missing from the record.
3. RFI-3 1F living twin window: no height chain through it.
4. RFI-4 (plan vs freelancer, for the verifier): the GF plan notes "تهوية صناعية" (mechanical ventilation) at the street-end
   WCs; the freelancer counts 4 GF bath windows. Which engine 0.60 windows sit in those WCs was not traced (needs the
   engine run).

## Learned

- A narrow window can be dimensioned on an elevation even when the plan census says "not printed": every elevation slot
  must be bound to the plan chain before a window is declared NO_PRINTED_HEIGHT.
- On this set the PDF and the DXF agree on the printed numbers but not always on the drawn geometry (2F stair arch): a
  witness end must be checked on the drawing that carries it.
- The freelancer's uniform heights (2.00 windows, 0.80 bath windows, 2.40 doors) disagree with every printed height but
  one (GF stair 2.00).

## Missing

Door element ids (engine run outside this run's authorization); 20 window heights and 27 door heights are printed on no
sheet: only the designer can give them (route: the controlled project data file of owner Q-17 = A, T-064).
