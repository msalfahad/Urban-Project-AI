# T-346: the freelancer's exterior plaster rows 65 / 68 / 69 (93.150 m2, "no face drawn") read as physical elements (development villa; rules R-T346-1 .. 4 for every villa)

Worker 2 (lane A), claim 2026-10-29 18:43 UTC. Investigation only: research files and tests; no engine module, rule,
knowledge file, candidate line, released line or T-337 FILL row changed; nothing released. ERS applied: s.2.1 (define
the element first), s.2.2 (drawing evidence first; his figures are traced, never taken), s.2.4 (reconciled in m2 to
named causes, residual 0), s.2.7 (no owner question: the drawings settle every row), s.4 (rule + tests), s.7 (lesson).
No coordinate, client name, image or workbook text is committed.

## 1. Question and evidence

T-162 / T-337 left his rows 65 (2 x 1.50 x 6.00 = 18.000), 68 (1.50 x 6.00 = 9.000) and 69 (6.75 x 9.80 = 66.150)
UNRESOLVED: no face of those sizes on the elevations; possible double counts. Evidence read this run:

- His sheet (Drive 'Alsenan chalet project' / the interior-plaster-and-Sigma workbook; the cells are already in
  `tests/alsenan/registers_b1/FREELANCER_RAW_ROWS.json`): rows grouped by elevation (SW 51-55, SE 58-61, NE 63-65,
  NW 68-75, roof 77-84); no merged label cells (checked in the workbook). Row 65 sits in the NE group and is labelled
  as the "vertical" (returns) of the low block; row 68 opens the NW group as a "low-block face"; row 69 is the NW
  "high face". His practice elsewhere: row 64 measures the NE GF face and the 1F face set back behind it as ONE plane
  10.00 x 19.20 from +1.00 (T-159 HAND_RIGHT); row 77 carries the 2F NE + NW faces at 4.70.
- Plan DXF (Drive P7757_DXF_COMPRESSED.zip -> P7757.dxf, T-159 rings rebuilt this run): the GF block stands out
  **1.500 m beyond the 1F on the NE face AND on the sea face** (an L-shaped GF roof band at +5.50, parapet +6.00);
  '1500' is printed twice on the 1F plan across the NE band (passage end and sea end), once across the sea band, and
  once on the GF plan. GF NW-7 (sea face, 7.900) = 1.500 at the NE band's end (nothing above its parapet) + 6.400 under
  1F NW-5 (6.725, +5.50 -> +9.70, CAD-wave parapet 3.0134 m2, 0.325 over open air).
- Passage (T-123, slab sheet registered 30 / 30 columns): the NE end is closed by the 0.200 m boundary wall; the house
  passage face P-2 runs 4.700 m from that wall's inner face; its first 1.300 m lies inside the 1.500 m NE band; the GF
  roof slab +5.50 runs on over the passage (0 .. 1300 mm under the exposed GF roof).
- Sheet 09 (NE view, single sheet PDF): GF +-0.00 / +1.00 / +5.50, parapet '50' to +6.00, 1F to +11.00, 2F +14.40;
  the GF part of that view is drawn as a cut. At its cut the passage reads covered at about +4.30; the cut position is
  not established, so T-123's slab-sheet reading stands (this changes no face area: P-2 is measured to +5.50 either way).

## 2. Each row: element, his implied dimensions, drawing, classification

| His row (cells) | Physical element | Drawing evidence | Drawn m2 (his band) | His - drawn | Classification / owner lines | Verdict proposal |
|---|---|---|---|---|---|---|
| 68 (F 6.00, H 1.50 = 9.000) | GF sea face NW-7, its 1.50 m at the NE band's end, +-0.00 -> +6.00 (0.600 m of W02's width is in it) | plan 1500; NW-7 7.900, levels +1.00 / +5.50 / +6.00 | 9.000 (plinth 1.500, storey 6.750, parapet 0.750) | **0.000** | drawn, already bound once in T-337: GF storey L-b05f70c92405dbcfbe62, PLINTH GF, PARAPET-OUTER GF; no new FILL row | MAPPED |
| 69 (F 9.80, H 6.75 = 66.150) | the sea face as ONE plane from +1.00 (his row 64 practice): GF NW-7 6.40 m under the 1F + 1F NW-5 6.725 m above it, to +10.80 | NW-7, NW-5 (T-305 / T-337); the 2F sea face is his row 77 (4.70 high), so 69 is NOT the 2F face | 63.258 (GF 32.000 + 1F 28.245 + 3.013); plinth 6.400 below his band | **+2.892** = width +1.679 (6.75 vs 6.40 / 6.725), hidden overlap **-3.188** (the 0.50 m where the GF parapet stands 1.50 m in front of the 1F face), height **+4.400** (his top +10.80 vs the CAD wave's mean top +10.148; +10.80 is not printed) | drawn, bound once in T-337: GF storey, PARAPET-OUTER GF, 1F storey L-8bb83e16cc7b104ab88b, PARAPET-OUTER 1F; no new FILL row | RULE_DIFFERENCE (one plane) + height part UNRESOLVED (4.400) |
| 65, first half (9.000) | NW end return of the NE band = the SAME NW-7 1.50 m portion as row 68 | the band is an L: its NW end turns into the sea face | 0 | +9.000 | **double count in his sheet** (no face, no FILL row) | ENGINE_RIGHT (the face once) |
| 65, second half (9.000) | SE end return of the NE band, at the passage: P-2's first 1.300 m (+0.15 -> +5.50, W10 1.00 x 1.50 in it) + 0.200 boundary wall | T-123 passage faces, slab sheet; plan 1500 | 6.955 (plinth 1.105, storey 5.850) | **+2.045** = datum 0.225 (his +-0.00 vs floor +0.15) + boundary wall 0.200 m wide 1.070 (no house face) + 0.750 above +5.50 (roof runs on, no face) | drawn, bound once in T-337 (P-2: GF storey, PLINTH; Q-67 A cond.); the 0.20 m part is the boundary wall, OTHER_TRADE (Q-65 C) | RULE_DIFFERENCE (ENGINE_RIGHT on the geometry) |

## 3. Reconciliation statement (acceptance e)

**93.150 m2 = 79.213 drawn faces matched (63.258 + 9.000 + 6.955) + 9.000 double count + 4.937 named band terms
(+2.892 row 69, 0.000 row 68, +2.045 row 65), residual 0.000000.** Of the named terms only row 69's height part
(4.400 m2, his +10.80 top) is not explained by a physical or rule difference: it stays UNRESOLVED by name (the 1F sea
parapet is a CAD wave without a printed top), never a quantity.

Portions close on the T-337 faces (CLOSURE_T346.csv): NW-7 plinth / storey / parapet 7.900 / 35.550 / 3.950 and NW-5
28.245 / 3.0134 rebuilt to 0.000000; P-2 1.300 of 4.700 m on the same bands and lines.

## 4. What this changes, in units

- **T-314 FILL: no new face row, no change** (acceptance b): every face these rows describe is already bound once.
  The rows are not a scope gap of the drawn facade.
- Against the freelancer: his comparable wall rows 935.365 m2 (net of half openings, T-337) hold a 9.000 m2 double
  count: like for like 926.365 against the drawing's 897.720 .. 938.606 = **-28.645 .. +12.241 m2 (-3.1 % .. +1.3 %)**,
  was -37.645 .. +3.241 (-4.0 % .. +0.3 %). The rule difference on openings (Q-73 A full holes vs his half) stays.
- T-162's "drawn faces in no freelancer row" 210.761 m2 -> **156.406**: NW-7 47.400 is in his rows 68 + 69 and
  6.955 of P-2 in row 65.
- **Finding for the Lead (F-T346-1, not resolved here):** row 69 holds 1F NW-5 (31.258 m2), which T-162 / T-337 had
  placed in his rows 70 + 71 + 74 ("faces above the swimming pool", 4 x 4.95 m at 5.50 / 5.70, 109.890). Those rows
  then match only 1F NW-1 .. NW-4 and two returns (5.903 m, 32.167 m2 drawn): their unexplained part grows from 7.17 m
  of run to 13.90 m. Candidates (pool-court walls, the GF pool glazing face NW-4, a court face) need their own
  investigation row; until then rows 70 / 71 / 74 stay PARTIAL.
- Element register (acceptance c, Lead content): no boundary or site wall is measured by these rows; the only site
  element touched is the **0.200 m boundary wall that closes the GF side passage at its NE end** (T-123), OTHER_TRADE
  (Q-65 C): proposed register row "boundary wall, passage NE closure, 1.200 m x 0.200 m, owner trade OTHER (Q-65 C),
  no house facade face; its thickness is 0.20 m of his row 65's 1.50 m".

## 5. Rules (research functions, proposed for a future rule version; `freelancer_rows.py`)

R-T346-1 a freelancer figure is traced, never a quantity (`fill_row` refuses any source but the drawing).
R-T346-2 his one plane is compared band by band (cuts at every face bottom / top and his own): per band, his width
minus the drawn widths standing in it, in m2, each with its cause; drawn parts outside his band are reported apart.
R-T346-3 a projection band has two ends: (band depth x lower-block height) x 2 is its two end returns; each return is
mapped to the face at that end; a return that is the same face portion as another row of his is a DOUBLE COUNT (his
m2 visible, no drawn m2); a face portion is matched once.
R-T346-4 a site / boundary wall is never a house-facade face (Q-65 C); a part with no drawn face is UNRESOLVED with
drawn None, never 0.

## 6. Tests (acceptance d)

`tests/t346_freelancer_rows/test_t346_rules.py`, villa M (not the development villa; hand calculation in its
docstring): GF block +-0.00 -> +4.50 with an L-shaped 2.00 m band, 1F set back, a side passage closed by a 0.20 m
boundary wall; his rows 9.000 / 57.400 / 18.000 reconcile to drawn 76.020 + double count 9.000 - 0.620 named terms,
residual 0; band terms 0.700 / -3.900 / 0.500 / 0.100 and 0.200 / 0.080 / 0.700 / 1.000 by hand; face order and
millimetres give the same terms. Adverse: a freelancer row as a FILL quantity refused (the naive reading would put
18.000 where the drawing has 7.020); a boundary wall in a house-facade line or ledger refused; one face matched by two
rows refused, a double count without a first claim refused; parts that do not add up to his row refused; UNRESOLVED
never 0; HELD with a point value and a blank DRAWING-CONFIRMED refused; a face with a missing height refused.
`test_t346_alsenan.py`: byte rebuild, statement residual 0, portions close on T-337 to 0.000000, no new FILL row,
row 68 0.000, row 69's height term named and not absorbed, the hidden overlap -3.1875.

## 7. Lessons-register row (ERS s.7, proposed)

2026-10-29 | his rows 65 / 68 / 69 (93.150 m2) labelled "no face drawn" | each row was matched against single
elevation faces of the same size; a one-plane elevation practice and the end returns of a set-back band were not
decomposed | before calling a row "no face", decompose set-backs: a row (band depth x lower height) x 2 is the band's
two end returns, a row (upper width x full height from the floor) is the stacked faces as one plane; map each end to
its face and flag a return that another row already holds as a double count (every villa) | tests/t346_freelancer_rows
| proposed.

Files: `freelancer_rows.py`, `t346_alsenan.py` (--write / --check), `ROWS_T346.csv`, `BANDS_T346.csv`,
`CLOSURE_T346.csv`, `summary.json`; tests `tests/t346_freelancer_rows/`.
