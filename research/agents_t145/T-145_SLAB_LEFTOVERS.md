# T-145 Alsenan slab-check leftovers: CB5 span 2, sunken-slab steps, the 13 non-slab faces (NO REPO CODE)

Worker 1 (structural lane S), 2026-10-21. Development villa, not an accuracy claim. Nothing is wired and no released
quantity changes: a checked piece for the V3.0 candidate (lane I, T-146 wires it).

Sources (Drive "Alsenan chalet project", scratchpad copies, never committed): "ST7757 dxf.dxf" (sha256 9f9d1179...38079,
the manifest file) and "ST7757.pdf" (sha256 74da1523...37e3): p.4 / p.5 / p.6 roof-slab plans and their legend (read at
300 dpi), p.8 general notes, p.11 continuous-beam schedules (2 span), p.13 - p.16 details. T-139's own helpers re-run on
the same DXF reproduce its ledger exactly (62 panels, 375.0481 m2, 60.2804 m3). Rules: URBAN-NON-OVERLAPPING-SLAB-BEAM-
MODEL@v1, URBAN-BEAM-TYPE-FROM-SCHEDULE-LENGTH-FROM-PLAN@v1, owner Q-61 C (1)-(6), Q-44 A, UP-QTY-STATUS-001.

Files: `ITEMS.csv` (one row per non-slab face: reading, home line, status, register ref, freelancer, verdict),
`retotal.py` (re-add check against the T-139 ledger), `sunken_edges.py` (what lies beyond every edge of each sunken
panel). Repeat: T-139 `slab_faces.py` + `slab_ledger.py` -> `python -I sunken_edges.py faces.json PANELS.csv`;
`python -I retotal.py ITEMS.csv`.

## 1. Result in engineering terms (concrete, m3; Alsenan development villa)

| Line | Before (engine route G / registers) | After (this hand reading) | Freelancer | Note |
|---|---|---|---|---|
| Suspended slabs | 60.966 released | **60.280** (-0.686, -1.13 %) | 59.817 | hand vs freelancer +0.463 (+0.77 %), as T-139 |
| Beams, CB5 span 2 | in no beam row (its band 0.118 counted as slab) | **0.296 CALCULATED** (0.20 x 0.40 x 3.700) | inside BCB5 0.568 | new beam row |
| Beams, register CALCULATED total (T-110) | 64.764 | **65.060** | 65.970 | -0.910 (-1.4 %), was -1.206 (-1.8 %) |
| Beam-lane holds fed by slab faces | 0.483 m3 of plan area was slab | **HELD** in 8 named beam rows (candidate ranges as in T-110, never 0) | no rows | designer D-04 / D-05 / D-26 |
| Not concrete | 0.085 m3 counted as slab | **none** (stepped drafting line, 4 faces) | no row | 2F face re-read this run |
| Sunken-slab steps | "not measured" | **no free step edge: all 50.885 m of sunken-panel edges are beam faces**; concrete m3 unchanged if drop <= 0.24 m; drop HELD (D-41) | no row | formwork of the exposed beam faces HELD = drop x 50.885 m |

Net effect on released concrete if lane I wires it: slab -0.686, beam +0.296 = **-0.390 m3**; 0.483 m3 of slab-face
volume becomes HELD beam-lane lines (each already in the beam register with its own candidate range).

## 2. (a) CB5 span 2: a beam, measured (0.296 m3)

- Plan (ST p.4, GF roof slab): two CB5 labels, both rotated 90 and parallel to the band x 52.693 - 52.893 (0.200 m):
  y 38.996 on span 1 and **y 42.680 on span 2**. Span 1 = column face 38.348 to column face 40.648 = 2.300 m (beam
  register BM-GF-035, 0.184 m3). **Span 2 = column / B1 face 41.248 to the B20 south face 44.948 = 3.700 m** (B20 is the
  0.40 band 44.948 - 45.348; its west 3.0 m is hatched "Cantilever portion": PDF hatch pitch 17 px = legend 17 px,
  sunken slab 41 px = legend 41 px).
- Schedule (ST p.11, SCHEDULE OF CONTINUES BEAMS (2 SPAN)): **CB5 B 20, H 40**, spans 2.5 / 4.5 m, three supports. The
  short span is the southern one and the long span the northern one, matching the label order; printed spans are design
  spans (centre to centre 2.85 / 4.20, sum 7.05 vs printed 7.0), the concrete length is the plan band
  (URBAN-BEAM-TYPE-FROM-SCHEDULE-LENGTH-FROM-PLAN@v1). Drawn width 0.200 = schedule width: no Q-61 C(1) conflict.
- No section cuts CB5 (section A-A cuts B20 at x 54.2 - 55.0). Bars: span 2 bottom 4 dia 16 (schedule).
- Hand m3: gross 0.20 x 0.40 x 3.700 = **0.2960** (route G gross basis); in the URBAN-NON-OVERLAPPING-SLAB-BEAM-MODEL@v1
  split: slab share 0.740 x 0.16 = 0.1184 + downstand 0.20 x 3.700 x 0.24 = 0.1776. Never both: the 0.1184 now in the
  engine slab face leaves the slab line (T-139 panel GF-098 already stops at the CB5 face x 52.893).
- Freelancer: BCB5 0.20 x 0.40 x 7.10 = 0.568 (both spans, one row). Hand both spans 2.300 + 3.700 = 6.000 m = 0.480
  (-0.088, -15.5 %): **RULE_DIFFERENCE** (he runs through the 0.60 m support column and to the B20 centre; the Urban
  basis takes the plan band between faces, the column joint is in the column line, T-119).
- Proposal for the beam register: new row BM-GF-035.2, CB5 span 2, CALCULATED 0.2960, x 52.793, y 43.098.

## 3. (b) Sunken-slab steps: no free step edge; the drop stays HELD

- Sheets searched for a drop or a step detail: ST p.4 / p.5 / p.6 (hatch legend "Sunken slab." only, no level, no
  section through a sunken panel), p.8 general notes 1 - 24 (note 18: slabs 16 cm; nothing on sunken slabs), p.13 (footings,
  ground beams), p.14 (lift pit, boundary wall, parapets), p.15 (twisted column, slab-on-beam typical detail, temperature
  steel: no step), p.16 (stairs, ribs, beam openings); DXF level texts: levels exist only on the ground-floor slab plan
  (+0.15 / +0.30 / +1.00) and the upper roof (+9.70); none on the GF or 1F roof slab plans. **No drop is printed.**
  Architectural sections were not searched for it: a finish-level difference is not the structural drop.
- Geometry (sunken_edges.py, every edge walked in 10 mm steps): every sunken panel is closed by beam bands and columns
  on its whole perimeter:

| Panel | m2 | Perimeter m | Beyond the edge |
|---|---|---|---|
| GF-015 | 2.5725 | 6.440 | beam / column 6.440 |
| GF-016 | 3.3250 | 7.300 | beam / column 7.300 |
| GF-081 | 4.1176 | 8.841 | beam / column 8.841 |
| GF-128 | 2.0804 | 7.078 | beam / column 7.078 (2.953 of it the B27 band) |
| GF-141 | 7.3009 | 11.626 | beam / column 11.626 (3.642 of it the B27 band) |
| 1F-018 | 5.4000 | 9.600 | beam / column 9.600 |
| **Total** | 24.796 | **50.885** | slab-to-slab step edge **0.000 m** |

- Consequence: on the route G basis (panel between beam faces x t, beam gross B x L x D) the drop adds **no step-edge
  concrete** as long as the sunken slab still frames inside the beam depth, i.e. drop <= D - t = 0.40 - 0.16 = 0.24 m for
  the shallowest framing beams (B1, B2, CB5 at 0.40). That condition cannot be checked without the drop, so the line is
  **HELD-CONDITIONAL, not 0**: "no step concrete if drop <= 0.24 m; otherwise designer detail". Designer item D-41 stands.
- Formwork (lane S): the beam side face exposed under the sunken soffit = drop x 50.885 m2, **HELD** on the same drop.

## 4. (c) The 13 non-slab faces: one home each (ITEMS.csv)

| Engine face | m3 now in slab | Home | Status |
|---|---|---|---|
| b41145 GF | 0.1184 | beam CB5 span 2 | CALCULATED 0.2960 |
| f9b0c2 GF | 0.1372 | beam lane BM-GF-058, strip north of B20 | HELD (D-05 / D-26, Q-61 C(5)) |
| 02047c GF | 0.0784 | BM-GF-061, outer west strip | HELD (D-26) |
| 57ec39 GF | 0.0322 | BM-GF-060, contested void-ring piece | HELD (Q-61 C(3)) |
| 4c7ca8 1F | 0.0992 | BM-1F-035 / -038, SE box + 0.10 strip | HELD (D-05 / D-26) |
| e100a6 1F | 0.0616 | BM-1F-037, rounded box | HELD (D-26) |
| cfe47b 1F | 0.0325 | BM-1F-036, strip outside CB12 | HELD (D-05) |
| 785741 1F | 0.0256 | BM-1F-033, strip north of B23 | HELD (D-05, Q-61 C(5)) |
| d54a5a 1F | 0.0159 | BM-1F-032, unlabelled span | HELD (D-04, Q-61 C(4)) |
| 2597c9 / cf20e8 / ae2689 | 3 x 0.0139 | none: stepped drafting line | NOT CONCRETE |
| 5a1792 2F | 0.0435 | none: same stepped drafting line | NOT CONCRETE (was HELD in T-139) |
| **Sum** | **0.6862** | = engine 60.966 - hand 60.280 | re-add exact (retotal.py) |

Readings made this run:
- **Section A-A** (cut x 54.2 - 55.0 through B20 and the strip north of it) draws the B20 cantilever 40 x 75 with a
  20 x 20 upstand on its north half and nothing outside the 0.40 width; it draws no slab on either side either, so it is
  a beam section, not a full cut: under Q-61 C(5) ("exclude only if the sections conclusively show no concrete beam") the
  strips stay HELD, not excluded.
- **ST p.14 parapet details** ("DETAIL OF PARAPET SECTION", two typical versions: a 30 x 130 parapet on a 60 x 40 beam with
  0.10 m step-outs at its base; a 15 + 15 tapered parapet 105 high on the slab edge, "SEE DETAIL FOR BEAM") are the only
  printed candidates for the roof-edge projection bands. No plan mark points to them and slab note 1 tells the contractor
  to match parapets and projections to the architectural drawings before casting: candidate evidence for D-26, no
  quantity taken from it.
- **The 2F "0.10 strip" west of B15** is not a band: its outer line steps x -20.355 -> -20.380 -> -20.405 -> -20.430 in
  0.025 m steps joined by 0.025 m arcs (y 43.048 - 47.398), the same stepped drafting line as the break slivers beside
  the stair on the GF / 1F / 2F sheets (x 57.018 - 57.093, three 0.025 steps). No tag, no bars, no mark: not concrete.

## 5. Owner manual method and drawing-derived method side by side

| Item | Owner / freelancer manual | Drawing-derived (this piece) | Difference |
|---|---|---|---|
| CB5 | one lump 7.10 m x 0.20 x 0.40 = 0.568 | two plan bands 2.300 + 3.700 m = 0.480 | -0.088 (-15.5 %): length basis (through support vs between faces) |
| Slab edge strips / boxes | not measured (no row) | HELD in the beam lane, plan areas known, depths not printed | not compared |
| Sunken slabs | panel area x 0.16 in the lump slab area | same panels at 0.16; step concrete none if drop <= 0.24 m; drop HELD | none on concrete |

## 6. Who is right (proposals for the verifier)

- CB5 span 2: **HAND_RIGHT** against the engine (beam band measured as slab; beam row missing). Against the freelancer:
  **RULE_DIFFERENCE** (length basis), no % counted against either.
- Slab line 60.966 -> 60.280: **HAND_RIGHT** on all 13 faces (each with a home line or a named HOLD).
- 2F face 5a1792: **NOT CONCRETE** (re-read; T-139 had HELD); checker please confirm on the DXF (one look at the stepped
  outline).
- Sunken steps: **UNRESOLVED (designer D-41)**, conditional statement above; no owner question needed (it is a drawing gap,
  not a rule gap).

## 7. What we learned (every villa)

1. A continuous beam's second label sits on its second span; the schedule's span list gives the order (short / long) to
   bind each label to its band. A band with a label is never slab.
2. Hatch meaning is read by pitch against the legend on the same sheet (cantilever 17 px, sunken 41 px at 300 dpi here):
   B20's west 3.0 m is a cantilever portion, not a sunken slab.
3. A sunken panel bounded by beams on all sides has no step concrete of its own while the drop stays inside the beam
   depth: check the perimeter first, then hold only the condition, not a volume.
4. Stepped 25 mm drafting lines close thin faces at stair cores; they repeat identically on every sheet and are not members.

## 8. Held / not measured (never 0)

- Sunken-slab drop (6 panels, 24.796 m2, 50.885 m of beam faces): HELD, D-41; concrete unaffected if drop <= 0.24 m.
- Beam-side formwork under sunken soffits: HELD (drop x 50.885 m2).
- 8 edge / ring / unlabelled beam-lane pieces: HELD with the T-110 candidate ranges (D-04, D-05, D-26).
- CB5 span 2 rebar: not measured here (column and beam steel by bar population is T-148 / T-009).
