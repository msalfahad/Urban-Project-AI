# T-144: Alsenan openings for finishes: sill, head and crown of every opening, read on the elevations and sections, and the plaster / paint / wall-tile nets by both methods

Worker 2, 2026-10-21 09:41 - 10:30 UTC. Lane A. NO REPO CODE: research files only (this folder); no engine module, rule,
knowledge version, key map, test or released quantity changed. Development villa (Alsenan), not an accuracy claim. No
client name, image, coordinate or personal data is committed; sheets are cited by Drive title and page.

Files: `OPENINGS_T144.csv` (79 rows: one per opening on each room face, with sheet + reading + status),
`ROOMS_T144.csv` (31 rooms / shaft storeys, both methods, nets with bounds), `calc.py` (standard library; rerun:
`python3 -I calc.py T128_ROOMS_INPUT.csv OPENINGS_T144.csv ROOMS_T144.csv summary.json`), `summary.json` (per floor and
kind), `T128_ROOMS_INPUT.csv` (worker 3's T-128 room table 69c1a0a, copied unchanged as the input: face lengths, heights,
gross).

Rules: UP-OPEN-SCHED-001 (wall_finish_deduction = face length x (min(head, H) - max(sill, 0)), OWNER_APPROVED), owner
Q-32 A (an arched opening counts to its crown, enclosing rectangle), Q-38 A (curved pool glazing width = printed 6.57),
Q-39 C, Q-55 C (door head 2.20 m ASSUMED only when the drawings are silent; main entrance 2.50 printed), Q-17 (status
words; INFERRED is kept apart and never released), G1 / G2 (both methods kept), Q-43, Q-48 A, Q-52 C mod, UP-DOOR-HGT-001
(order: schedule, section, elevation, dimension, fallback), UP-QTY-STATUS-001 (held = bounds, never 0). Printed note N09
(sanitary NOTES box, T-091 F2: "work with stated dimensions, not to scale"): nothing in this package is scaled off a
drawing; every released level is a printed chain value, checked against the DXF dimension entities (their measured
values) where the DXF has the view.

## 1. What was read (independent of T-083 / T-078; Drive "Alsenan chalet project", read this run)

| Sheet | View | How | What it prints for openings |
|---|---|---|---|
| Alsenan_Architectural_P7757_Pages_05-06, p.6 | SOUTH EAST ELEVATION 1:100 | 400 dpi scan, whole page + chain crops | two height chains: 185 / 200 / 250 / 230 / 200 / 170 / ... (stair stack) and 85 / 250 / 55 / **65** / 220 / 160 / 139 / 104 / 193 / 155 |
| Alsenan_Architectural_P7757_Pages_07-08, p.7 | SOUTH WEST ELEVATION | whole page + window zone crop | storey chains 100 / 870 / 420 / 50, 550 / 50, 130 and ±0.00 / +0.15 only: 14 windows drawn, **no** sill / head / height |
| Alsenan_Architectural_P7757_Pages_07-08, p.8 | NORTH WEST ELEVATION | whole page + 1F crop | chains 300 + 10 (W15), 115 / 70 / 430 / 20 / 305 / 45 (pool glazing, W17), 84 / 216 / 230 (W18); widths 155 / 29 / 155 |
| p7757_arch_sheet09 | NORTH EAST ELEVATION | whole page | levels ±0.00 / +0.15 / +0.30 / +1.00 / +4.30 / +5.50, widths 480 / 400 / 450 and the storey chain: no opening height |
| p7757_arch_sheet10 | SECTION A-A | whole page | levels and storey chains only; doors / windows drawn without dimension |
| Alsenan_Architectural_P7757_Pages_11-12, p.11 | SECTION B-B | whole page | levels and storey chains only; the GF arch and 8 doors drawn without dimension |
| P7757_DXF_COMPRESSED.zip / P7757.dxf | the two elevation frames it holds (NW, SE): 388 DIMENSION entities read with their measured values; window jamb / arch geometry on layers W and 1 | ezdxf 1.4.4 (project venv), scratchpad only | every NW / SE window drawn in the DXF is now bound to a printed chain (section 2) |

Result of the census: the set prints sill / head (or crown) for **9 openings** (8 windows + the main entrance door);
the other 20 windows, 27 doors and 3 interior arches print nothing on any sheet. Against the T-083 table this run
**corrects two readings, adds one sill, closes one drawing conflict and confirms one width answer**:

| Opening | Before (T-083 / T-128) | Now (this run) | Evidence |
|---|---|---|---|
| W14 1F west master bed | sill +6.70, head +8.30 (1.20 / 2.80 above the 1F floor) | **sill +6.90, head +8.50 (1.40 / 3.00)**, height 1.60 unchanged | SE chain part 4 is "65", not "45": 0.15 + 0.85 + 2.50 + 0.55 + 0.65 + 2.20 + 1.60 + 1.39 + 1.04 + 1.93 + 1.55 = 14.41 = the printed 14.40 top (with 45 it closes at 14.21); DXF dimensions 2201.4 and 1598.6 end at +6.90 / +8.50 |
| W17 1F east master, curved | sill 0.20, crown 3.70 above the floor | **sill 0.00, crown 3.50** | NW chain 115 / 70 / 430 / 20 / 305 / 45: the 430 is the pool glazing +1.00 -> +5.30, the 20 is the slab band +5.30 -> +5.50 (1F floor), so the 305 + 45 start ON the 1F floor; DXF 3050.5 + 454.3 start at y(+5.50) |
| W15 1F living, sea side | height 3.10, "sill not printed" | **sill 0.00, crown 3.10** | NW chain "300" starts on the +5.50 floor line; DXF 3000 starts at y(+5.50) and the W15 jamb feet are at +5.50 |
| W26 2F stair, arched | HELD DRAWING_CONFLICT (RFI-1: DXF crown 0.50 above the PDF crown) | **MEASURED: sill +10.80, crown +12.50 (1.10 / 2.80 above the 2F floor), 1.20 x 1.70 = 2.04 m2** | SE chain 200 ends at +10.80, 170 at +12.50; DXF SE: opening jambs 1.20 apart (layer 1) with the opening arch apex at +12.50 exactly; the arcs at +12.55, +12.95 and +13.00 are the surround mouldings (the PDF draws the same thick band), which T-078 took for the crown. No conflict between the two drawings: RFI-1 can close (checker: confirm) |
| W03 GF curved pool glazing | height printed, width HELD (Q-38 answer "missing") | width answered: Q-38 A, printed 6.57 (OWNER_QUESTIONS index, owner main chat 2026-10-19 20:50) | 6.57 x 4.30 = 28.251 m2 aluminium (not this task's line; noted for the openings line) |
| W16 1F living twin | HELD, candidate 3.10 | still HELD; **INFERRED** 0.00 / 3.10 | width 155 printed; no chain through it; DXF jamb feet, springing and frame lines at the same 9 levels as W15. Q-17 INFERRED: candidate only (RFI-3 stands) |

Confirmed unchanged: W01 +2.00 / +4.00 (SE 185 / 200; DXF 1850 / 2000), W13 +6.50 / +8.80 (SE 250 / 230; DXF 2500 /
2300), W18 +6.34 / +8.50 (NW 84 / 216; DXF 839.3 / 2160.7), D01 main entrance +1.00 / +3.50 (SE 85 / 250; DXF 850 / 2500),
W03 +1.00 / +5.30 (NW 430; DXF 4300). The DXF holds no SW / NE elevation and no section, so the 20 windows on those faces
can be read only on the PDF scans, which print no opening dimension.

## 2. Every opening on a finished wall face (79 rows, `OPENINGS_T144.csv`)

| Status | Rows | Face width | What it means for the nets |
|---|---|---|---|
| PRINTED (incl. 2 corrected, 1 RFI closed) | 9 | 17.38 m | measured band, released by UP-OPEN-SCHED-001 |
| ASSUMED door head 2.20 m (Q-55 C) | 45 | 39.38 m | PROVISIONAL band (door heads only); measured widths kept |
| INFERRED (W16) | 1 | 1.55 m | candidate, not released |
| HELD: no head printed (20 window faces) or arch head not printed (3 arches) | 24 | 28.91 m | net HELD with bounds: lower = band from the floor to the wall height, upper = no deduction |

## 3. Nets per room and per floor, both methods (m2; `ROOMS_T144.csv`, `summary.json`)

Owner method = G1 heights (GF 3.65, annex 3.15 PROVISIONAL, 1F / 2F 3.35); drawing-derived = T-128 section 2 heights
(GF 4.09 .. 4.19, annex 3.59 .. 3.69, 1F / 2F 3.79 .. 3.89; plaster upper bound to the soffit +0.15; shaft by storey
interval). Every net re-adds to T-128's gross (calc.py asserts the owner gross to 0.01 m2; every owner net that this run
does not touch equals T-128's to 0.01 m2).

Changed or new against T-128:

| Room | Owner method net | Was (T-128) | Drawing-derived net (paint / tile height) | Why |
|---|---|---|---|---|
| 1F east master bed (curved W17) | **59.08 PROVISIONAL** | 59.75 | **68.30 .. 70.50 PROVISIONAL** (new) | W17 sill 0.00: the band under the owner line grows from 3.15 to 3.35 m on 3.32 m of face (-0.66 m2). The owner-line conflict is now +0.15 m (crown 3.50 vs 3.35), not +0.35 m |
| 1F living + corridor + landing (open zone) | **HELD 111.21 .. 116.41, INFERRED 111.60** | HELD 110.83 .. 121.21 | **HELD 127.52 .. 137.26, INFERRED 128.59 .. 132.45** (new) | W15 released (1.55 x 3.10 = 4.81 m2); only the twin W16 holds it, so the range shrinks from 10.38 to 5.20 m2 (owner) |
| Stair shaft GF part | HELD (no owner rule, Q-72 open) | HELD | **49.13 PROVISIONAL** (new) | W01 printed 1.20 x 2.00; north door 2.20 ASSUMED |
| Stair shaft 1F part | HELD (Q-72) | HELD | **HELD 47.05 .. 51.25** (new) | W13 printed 1.20 x 2.30; the 1.00 m north window prints nothing |
| Stair shaft 2F part | HELD (Q-72) | HELD | **HELD 48.16 .. 53.37** (new) | W26 now measured 1.20 x 1.70; W27 prints nothing |
| every other room | = T-128 | | drawing-derived nets added (new), same openings | |

Per floor (dry = plaster + paint face; wet = wall tile to the decor ceiling; "known" = rooms whose every opening is
printed or an ASSUMED door; "held" = rooms with an unprinted opening, as a range):

| Floor | Owner known | Owner held (rooms) | Drawing-derived known | Drawing-derived held (rooms) | Freelancer gross, same rooms |
|---|---|---|---|---|---|
| GF dry | 56.95 (1) | 256.90 .. 300.72 (3) | 64.26 .. 65.93 | 291.36 .. 349.90 | 388.08 |
| GF wet | 89.53 (4) | 128.06 .. 149.44 (5) + 2 rooms level HELD | 102.17 .. 105.05 | 145.84 .. 174.59 | (spatter area, one total) |
| 1F dry | 110.42 (2) | 209.25 .. 222.99 (3, one INFERRED) | 127.42 .. 131.38 | 239.22 .. 261.98 | 441.27 |
| 1F wet | 26.30 (1) | 143.51 .. 153.56 (5) | 30.13 .. 31.00 | 163.78 .. 180.05 | (spatter area) |
| 2F dry | 40.42 (1) | 55.55 .. 59.57 (1) | 46.28 .. 47.61 | 63.34 .. 69.78 | 94.86 |
| 2F wet | - | 28.72 .. 30.73 (1) | - | 32.73 .. 35.97 | (spatter area) |
| Stair shaft | HELD (Q-72) | HELD (Q-72) | 49.13 | 95.21 .. 104.62 | 204.42 (+ GF stair wall 40.50) |

Whole house, dry walls incl. the shaft (plaster = paint face under the owner method):

- Owner method: known 207.79 + held 521.70 .. 583.28 = **729.49 .. 791.07 m2**, shaft HELD (Q-72).
- Drawing-derived (paint height): known 287.09 .. 294.05 + held 689.13 .. 786.28 = **976.22 .. 1 080.33 m2**
  (plaster to the soffit is higher still: ROOMS_T144.csv column DWG_PLASTER_NET_HI).
- Freelancer: plaster net 1 151.14 m2 (gross 1 209.39 less HALF of 116.50 m2 of openings), paint net 1 191.13 m2
  (gross 1 249.38 incl. 39.99 of stair soffit strips, same half deduction). Drawing-derived vs his plaster net:
  **-174.9 .. -70.8 m2 (-15.2 .. -6.2 %)**; vs his paint net -214.9 .. -110.8 m2 (-18.0 .. -9.3 %). Not a finished
  comparison: 104.1 m2 of the range is the 24 unprinted opening faces (lower bound = full height), and the rest is
  his larger gross (T-128: his 1 209.39 vs 1 150.62 .. 1 177.59 drawing-derived, from his flat heights and longer 1F /
  shaft runs) and the full-band per-face deduction here vs his half deduction per opening (RULE_DIFFERENCE, T-128).
- Owner method vs the freelancer on the same rooms stays a gross comparison (T-128 section 3): his deduction is one
  house-wide list, not split per room or floor, so no per-floor net of his exists to compare with.
- Wet-wall tile: owner known 115.83 + held 300.29 .. 333.73 (2 rooms level HELD); drawing-derived known 132.30 ..
  136.05 + held 342.35 .. 390.61; the freelancer's wet-wall figure is one spatter-dash total of 433.83 m2 at 3.00 m
  flat (not comparable room by room, T-128).

Deductions themselves (dry + shaft faces, drawing-derived, at the lower wall height): printed 48.74 m2 (41.89 with
T-128's readings: W15 4.81 and W26 2.04 added, W17 unchanged in this method), ASSUMED doors 48.14 m2, held faces 18.51 m
of width. The freelancer's full opening list is 116.50 m2 per opening (not per face), deducted at half.

## 4. Opening heights vs the freelancer (his two workbooks disagree with each other)

| Opening | Printed (this census) | Freelancer plaster / paint sheets (deduction rows) | Freelancer aluminium sheet | Verdict proposal |
|---|---|---|---|---|
| W01 GF stair 1.20 | 2.00 | 1.20 x 2.00 | 1.20 x 2.00 | AGREE |
| W13 1F stair 1.20 | 2.30 | 1.20 x 2.30 | 1.20 x 2.00 | AGREE (finishes); ENGINE_RIGHT on aluminium |
| W26 2F stair 1.20, arched | 1.70 to the crown | 1.20 x 1.70 | 1.20 x 2.00 | AGREE (finishes); ENGINE_RIGHT on aluminium; supports closing RFI-1 |
| W14 1F 2.45 | 1.60 (sill 1.40) | 2.45 x 1.50 | 2.45 x 2.00 | ENGINE_RIGHT (1.60 printed) |
| W15 / W16 1F twins 1.55 | 3.10 to the crown / W16 INFERRED | 2 x 1.55 x 2.70 | 2 x 1.55 x 3.00 | ENGINE_RIGHT for W15 (3.10 printed); W16 UNRESOLVED (RFI-3) |
| W18 1F bath 0.50 | 2.16 (sill 0.84) | 0.50 x 1.50 | 0.60 x 0.80 | ENGINE_RIGHT |
| D01 main entrance 2.00 | 2.50 | 2.00 x 2.30 | not listed | ENGINE_RIGHT (2.50 printed) |
| interior doors | none printed (2.20 ASSUMED, Q-55 C) | 26 x 1.00 x 2.10 | 4 x 1.00 x 2.40 (outdoor) | UNRESOLVED (no sheet prints a door height) |

## 5. What stays HELD, and why

- 20 windows print no sill / head on any sheet: W02 (saloon glazing 6.33), W04, W05-07 (GF baths, 0.60), W08, W09, W10,
  W11, W12 (GF), W19-W23 (1F baths / laundry, 0.60), W24, W25 (1F), W27, W28, W29 (2F), the GF "other glazing" 0.93 and
  the 1F stair north window 1.00. SW (p.7) and NE (sheet 9) draw most of them with no dimension; the DXF has no SW / NE view.
  Scaling is not used (N09). Route: designer window schedule (designer list), or the controlled project data file (Q-17).
- 3 interior arches (GF dewaneya <-> wash, both faces; 1F 380 x 430 bed room to the dressing passage): B-B draws the GF arch
  with no dimension; no plan prints a head. HELD (designer list).
- W16: INFERRED twin (RFI-3).
- 27 door heads: Q-55 C fallback 2.20 m ASSUMED (PROVISIONAL), the main entrance printed 2.50.
- Room heights: as T-128 (annex G2 datum, roof datum DCR-6, build-up DCR-7, two GF wet rooms with no level, stair shaft
  owner method Q-72): this package does not change them.

## 6. Designer list (for DESIGNER_CLARIFICATIONS.md; the Lead files them)

- Window schedule with sill and head per window mark for the 20 unprinted windows (and the 1F stair north window).
- Head / crown of the three interior arches.
- RFI-3 (stands): confirm W16 = W15 (sill at the 1F floor, crown +8.60).
- RFI-1: proposed CLOSED (no conflict: the DXF opening arch apex is +12.50 = the printed chain; +13.00 is the moulding).

## 7. Learned

- A chain must close on its printed total before any one part is trusted: the SE "65" read as "45" moved W14's sill by
  0.20 m in two earlier tables; the overall 14.40 top caught it.
- A small dimension between two openings in one chain (the "20" between the pool glazing head and W17) belongs to the
  slab band, not to the upper window: the chain must be bound to the floor level marks before the sill is read.
- In this DXF the arched openings are drawn with their mouldings as concentric arcs; the opening crown is the arc that
  meets the jamb lines of the opening (layer 1), not the outermost arc.
- The freelancer reads the printed stair-window heights in his finishes sheets but uses 2.00 m in his aluminium sheet:
  the two trades of the same BOQ disagree with each other.

## 8. Checker re-read (3 openings proposed)

1. W14: SE p.6 chain 85 / 250 / 55 / **65** / 220 / 160 ... closes on 14.40; DXF SE dimensions 2201.4 / 1598.6.
2. W17: NW p.8 chain 430 / 20 / 305 / 45: the 305 starts at +5.50 (DXF 3050.5 from y(+5.50)).
3. W26: SE p.6 chain 200 / 170 (sill +10.80, crown +12.50); DXF SE layer-1 opening arch apex +12.50, mouldings at
   +12.55 / +12.95 / +13.00.
