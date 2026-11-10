# T-669 Concrete close-out: annex SE ground-beam corner square (F-T665-1), lower ends of the 6 roof columns, census of every B10 line HELD in V3.0.63

Worker 1 (lane S), 2026-11-10, run session_01E6cPneT7zKGS879viJoapY, branch `agents/task-T-669`. Research only: no
engine module, candidate line, rule file or method version changed; nothing released; wiring is lane I. ERS s.2 - 5;
UP-CONC-JOINT-001, R-T666-1, R-T658-3 / -4, R-CONC-OWN-1 1.0.0-proposed, D-35, D-39, Q-54 B. Development villa, not an
accuracy claim.

## 0. Sources and run

- Lines: `research/agents_t665/out/LINE_INDEX_V3_0_63.json` (V3.0.63, lines sha 09ec4c1a, T-665 Gate B PASS); family
  census `rules/coverage/BOQ_FAMILY_MASTER_1.64.0.json` (asserted equal family by family); causes from the merged
  ledgers T-647 / T-657 / T-658 / T-659 / T-660 / T-666 / T-667.
- Own read this run (Drive 'Alsenan chalet project', read-only, decoded into `.work/private` only): 'ST7757 dxf.dxf'
  (sha 9f9d1179: GROUND BEAMS PLAN, SECOND FLOOR ROOF SLAB plan) and 'p7757_arch_sheet10.pdf' (SECTION A-A, own render,
  by eye); 'P7757_DXF_COMPRESSED.zip' (inner ab54dd55) searched for roof levels: only +4.30 / +9.70 texts, no section.
  `t669_extract.py <decoded ST dxf>` prints every DXF value used (relative, m); `t669_alsenan.py --write` ->
  `out/T669_LEDGER.json` + `out/T669_HELD_CENSUS.md`; rules `t669_rules.py`.

## 1. (a) F-T665-1: the annex SE corner square (physical element first)

The square is the 0.30 x 0.30 plan prism where the two annex exterior ground-beam runs meet at the SE outer corner,
carried at the run's own depth. Local frame: origin = the outer corner, y along run #1, x along run #2 (m).

| Drawn line | Run | From .. to |
|---|---|---|
| 10B outer | #1 (BAND0012.1 / .2) | x 0, y 0 .. 4.90 |
| 7D1 inner | #1 | x 0.30, y 0 .. 4.60 (crosses the square to the outer line F8) |
| F8 outer | #2 (BAND0015) | y 0, x 0 .. 10.43 |
| 7D4 inner | #2 | y 0.30, x 0.30 .. 10.50 (STOPS on 7D1) |

Nothing else touches the square (S-BOUN 810 / hatch 80F abut the corner from outside, x -1.20 .. 0; S-AXIS 1498 is an
axis); nearest columns 22C (y 1.50 .. 2.00) on run #1 and 20B (x 4.55 .. 4.95) on run #2: **no column owns it**.
Both edges of run #1 are drawn across the square; run #2's inner face stops at run #1's inner face. So the drawing
puts the square in run #1 (R-T669-1 (b)), in its first span (to column 22C), line **L-6bf14711 ground BAND0012.1**.

| Line | Span before | Span after | AT_LEAST m3 before | after |
|---|---|---|---|---|
| L-6bf14711 BAND0012.1 | 1.200 (0.30 .. 1.50) | **1.500** (0 .. 1.50) | 0.0900 | **0.1125** (1.50 x 0.30 x 0.25 D-35 floor) |
| L-3284f440 BAND0012.2, L-402dbe61 BAND0015 | unchanged | | 0.1725 / 0.7275 | unchanged |

Change +0.0225 m3 = 0.09 m2 x 0.25 (the Checker's figure). Residual 0. The line stays LOWER_ONLY (D-35 high open):
both runs carry the same D-35 floor, so the owner choice changes no number, only where it is billed (once).
GB lower-only floor 5.069839 -> **5.092339 m3** (16 lines).

## 2. (b) The 6 UPPER_ONLY roof columns

Physical element: the column section from its base (2F: 9.65 APPROVED datum; annex: 0.25 APPROVED) to the roof slab top
(UP-CONC-JOINT-001). The ceiling (R-T658-4) uses the printed finished mark (13.90 / 4.30). The slab top itself is not
printed (D-39). What the drawings DO fix below it for the 2F:

- arch sheet 10 SECTION A-A: one continuous hatched roof slab across the 2F storey with +13.90 on its top line; the
  arched 2F stair window drawn under it (scaled only as a check: sill ~ +10.85, apex ~ +12.58; not used as a value);
- W26 (2F stair window): printed sill +10.80 and printed chain 170 -> apex **+12.50** (T-194 / RFI-1 closure, merged),
  the highest printed opening top on the 2F storey;
- ST SECOND FLOOR ROOF SLAB plan: one outline 8.175 x 6.80 m holding all 8 2F column outlines; the only thickness
  printed inside it is **T 18** (twice); no level text and no step inside it (the two '+9.70' marks lie outside, lower
  roofs).

R-T669-2: top >= 12.50 + 0.18 = 12.68, so height >= 12.68 - 9.65 = **3.03 m** (ceiling 4.25 m).

| Line | Member | Section | V3.0.63 | After T-669 (HELD, bounded) |
|---|---|---|---|---|
| L-d79d17d1 | C1 2F 20x50 | 0.10 | <= 0.425 | **0.303 .. 0.425** |
| L-26f6b6f2 / L-33a9b772 / L-919a5749 | C2 2F 20x50 | 0.10 | <= 0.425 each | **0.303 .. 0.425** each |
| L-53f223b0 | C9 2F 20x70 | 0.14 | <= 0.595 | **0.4242 .. 0.595** |
| L-fad18af6 | C3 GF 25x50 annex | 0.125 | <= 0.50625 | **<= 0.50625, low open BY NAME** |
| | 5 2F lines | | <= 2.295 | **1.6362 .. 2.295** |

Annex C3: no lower end is printed: the annex prints no opening head or sill (T-201 / T-227), no annex roof slab
thickness and no slab-top level (Q-54 B / D-39); sheet 9 prints +0.30 / +4.30 finished only. R-T669-2 refuses; a
generic storey or build-up value is not used. The 5 2F lines stay HELD (D-39 decides where inside 3.03 .. 4.25 m).
Same reasoning gives a lower end to three more 2F blank lines (2F C2 L-0ede77cf at the tank (D-44 only refuses its
ceiling), 2F C3 L-c10e2945 and 2F C5 L-bc01297b at their least conflicting section); not done here (section conflict
D-66 to settle the least section): named MEASURABLE NOW in the follow-up list, not in the census class (their cause
stays D-39 / D-44 / D-66).

## 3. (c) Census: every B10 line HELD in V3.0.63

144 lines (= the master 1.64.0 candidate census, asserted per family): 82 bounded **42.203169 .. 62.166947 m3**, 62 blank.
Every line once in `out/T669_HELD_CENSUS.md` (member, line id, bound, class, named item, beside). Classes:
DESIGNER ITEM 103, OPEN BOUND 34, MEASURABLE NOW 7.

| Family | Lines | Bounded low .. high m3 | Blank (beside) | Causes |
|---|---|---|---|---|
| B10-01 blinding | 6 | 5: 7.640374 .. 13.466198 | 1 | D-14, D-15, D-33/35, Q-28, Q-31 C; OPEN: lift-raft projection |
| B10-02 footing | 1 | 2.176 .. 2.275 | 0 | Q-31 C conflict record (T-595 third reading WAITING) |
| B10-03 necks | 36 | 32: 8.7724 .. 11.346 | 4 (>= 0.9515) | OPEN 32: founding level not printed (Q-21 C on site); D-43 / D-63 lift 4 |
| B10-04 GB + straps | 31 | 11: 1.20291 .. 5.750071 | 20 (>= 5.069839; T-669 5.092339) | D-34 8, D-33 8, D-35 8 + 3 court, Q-28 1, Q-31 C / D-15 straps; OPEN: neck-cut sliver |
| B10-06 columns | 34 | 18: 9.168 .. 13.602 | 16 (6 <= 2.80125) | D-66 15, D-39 (+Q-54 B / D-44 / D-66) 14; MEASURABLE NOW 5 CN (FR-T647-1..5 NOT_APPLICABLE) |
| B10-07 beams | 26 | 14: 6.023085 .. 8.507278 | 12 | D-04 5, D-27 / D-02 7, D-03, D-26 / D-05 11, D-28; MEASURABLE NOW L-efd3f780 (T-642 split) |
| B10-09 dome | 1 | 0 | 1 | consultant 10-24 G3 (no structural detail) |
| B10-10 lift / pool | 3 | 0 | 3 (pit >= 1.903 flagged) | D-43 x2, consultant 10-23 row 3 (pool steps) |
| B10-11 boundary | 2 | 7.2204 (point carried) | 1 | MEASURABLE NOW band (T-659 5.6392 .. 11.0328, wire in T-668); Q-28 pads |
| B10-12 parapets | 4 | 0 | 4 (floors 8.050943) | Q-65 C + D-39 |

Not in V3.0.63, named: pool blinding (T-667 merged, NEW line, AT_LEAST 0.915529 m3, wiring T-668).

**Plan for the last concrete rows (12-13 Nov):** MEASURABLE NOW = wiring only (lane I): CN x5 to NOT_APPLICABLE
(removes 1.134 .. 3.483 of columns that the schedule prints as absent; 3 bounded 0.378 .. 1.161 + 2 blank), band bound,
T-642 split, + this package's corner square and 5 column lows. Then the residue is designer-bound: 103 lines on
D-33 / 34 / 35 / 39 / 43 / 66 / 04 / 26 / 27, Q-28 / 31 / 65 and two consultant rows, and 34 OPEN on the founding level
(32 necks, site-decided under Q-21 C) and two undimensioned projections. No new owner question: every item is already
registered (ERS s.2.7 not met).

## 4. Owner manual method beside the drawing method; who is right

| Item | Owner / freelancer manual | Drawing-derived | Verdict proposal |
|---|---|---|---|
| annex corner | his footing line lumps pads + straps + band (no GB row) | +0.0225 m3 on BAND0012.1 floor | NOT_COMPARABLE |
| 2F roof columns | manual flat-storey method: printed storey 4.20 x schedule section = 0.42 / 0.588 (not checked against his workbook this run) | 0.303 .. 0.425 / 0.4242 .. 0.595 | the flat-storey figure lies inside the drawn bound: UNRESOLVED (D-39); columns family freelancer 28.5465 stays inside the open range (T-665) |

## 5. Rules, tests, lessons row (proposed)

`t669_rules.py` R-T669-1 (corner square with no column: the run that draws both edges across it owns it; none /
both / partial refused, HELD) and R-T669-2 (roof column lower end from the highest printed opening top + printed slab
thickness under one drawn slab plane; refused by name otherwise). `tests/t669_concrete_closeout` (20): hand villa
V669 corner normal, mirror / rotation / translation, corner inside a column, square partly in a column, no run draws
both edges, both runs draw through, mm / missing; column low normal + 7 refusals (no opening, no thickness, stepped
slab, planted base, low above ceiling, mm, wrong storey); development rebuild from committed files, corner and column
figures, census complete (144 = index, each once, blank stays blank), no absolute coordinate.

Lessons row (ERS s.7): | 2026-11-10 | a corner square with no column was left out of both runs (each measured to the
other's face) and a roof column's lower end was left open although the drawings fix a floor below the slab | the
ownership was read from the measured spans, not the drawn edges; the open slab-top datum was taken to mean no lower
end | a square belongs to the run that draws both edges across it; an unprinted slab top is still bounded below by the
highest printed opening under that slab + its printed thickness (every villa; R-T669-1 / R-T669-2) |
tests/t669_concrete_closeout | PROPOSED |

## 6. For the Checker (re-measure)

1. ST dxf GROUND BEAMS PLAN: 7D1 runs to the outer line F8, 7D4 stops on 7D1; no S-COL.BON at the corner.
2. Sheet 10 A-A: one slab top at +13.90 over the 2F stair window; W26 apex +12.50 on the SE elevation chain.
3. ST SECOND FLOOR ROOF SLAB plan: 'T 18' the only thickness, no level inside the outline; 8 column outlines inside.
4. Census: 144 rows vs the index; spot-check 2 causes against their ledgers.
