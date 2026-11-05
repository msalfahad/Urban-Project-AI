# T-533: the 0.15 m black-block module (B9-04 panel + perimeter joint mortar, block units) — HELD, sources exhausted

Worker 1, lane S, 2026-11-05. Non-candidate: no candidate line, no released line, no rule / knowledge version file
changes. Files: research/agents_t533/* and tests/t533_block_module/* only.

## 1. Physical element

The 0.15 m black (cement) block as laid in the 15 carried 0.15 m walls of T-520 / T-506 (GF-W19 / W21 / W28 / W29 /
W33, 1F-W12 / W13 / W17 / W18 / W19 / W20 / W21 / W22 / W23 / W24; GF-W22 (D-27) and 2F-W08 (D-39) are held on their
own causes): units of actual face w x h with a 10 mm bed and head joint (owner 2026-10-29), one module cell
(w + j)(h + b). Laid area: contract 178.571 m2, material base 175.871 m2 (2.700 m2 of REQUIRED RC lintel faces out,
T-506), low 175.531 m2 if the HELD D-1F-09 lintel face (0 .. 0.34 m2) is laid concrete.

Two corrections to the row text: 1.975440 is the T-367 PANEL MORTAR in m3 of the 15 walls on the contract area, not
"m2 of joint face"; and the unit is SOLID in the owner's own records (quantity-takeoff-rules s.2: "black cement (solid)
blocks", CONFIRMED user practice), not hollow: full bedding holds (Bayt Al-Omr also advises solid cement block, at
least for the first two courses). A hollow unit would need its shell width (face-shell bedding), which no source gives.

## 2. Evidence (ERS s.2.2 order) — where the 0.15 m module was looked for

| Level | Source | Finding | Verdict |
|---|---|---|---|
| 1 drawings | architectural plans / sections / notes; structural notes p.1 note 2, p.8 notes 18-20 | no block product, size, joint or mix printed (T-091 notes census, T-107, T-143, T-176) | SILENT |
| 2 specification | Kuwait General Specification 1990 §04220 (Drive: Engineering Sources / 01 Kuwait References) | re-read today: read_file_content returns 169,565 characters ending inside 02230; §04220 is listed in the contents only; 11.8 MB, over the connector's download limit | NOT READABLE |
| 3 owner rule | Q-75 answer 2026-11-02; UPC-BLACK-BLOCK-001 1.0.0 | "physical 40 x 19 x 19" = the 20 cm block; 12.5 / m2 only where the installed module is confirmed 40 x 20; rulebook `not_given`: "the 15 cm black block installed module" | 0.20 ONLY |
| 3 owner data | CLARIFICATIONS_SUPPLIER_2026-10-23 row 1 | the 15 / 20 cm dimensions are the open question itself; no answer recorded | OPEN |
| 4 reference | Bayt Al-Omr, KSE 2023 (01 Kuwait References), full text read | black cement blockwork named, solid units advised; no unit size | NO SIZE |
| 6 interpretation | owner's stored takeoff notes, quantity-takeoff-rules s.2.1 | "39 x 19 + 1 cm = 40 x 20 ... for 15 cm and 20 cm" is not labelled CONFIRMED; put to the owner verbatim as Q-75 option A, the answer named the 40 x 19 x 19 block only | NOT A SOURCE |

Not read (outside the named reference folders): a course takeoff "حصر الطابوق" in the owner's Drive root folder
"حساب كميات جلال"; a training takeoff cannot state this villa's supplier block, so it would not be a source either.
The owner's handwritten course notes (Drive title Urban_Project_Original_Yellow_BOQ_Notes_FINAL_15_Photos, OCR text) say "12.5 block
m²" for walls under 0.25 m without naming a block size: a general rule of thumb, level 6.

## 3. Reconstruction (R-T533-1, block_module_v1.py)

Units n = A / ((w + j)(h + b)); panel mortar Vm = A t (1 - kappa), kappa = w h / ((w + j)(h + b)); cement / sand by
UPC-BLACK-MORTAR-001 (Q-78 A: 8 bags + 1.1 m3 loose sand per m3). Independent check: course-by-course lay-out of a
4.00 x 3.00 x 0.15 fixture: 10 x 15 = 150 units, 1.800 - 150 x 0.39 x 0.19 x 0.15 = 0.13275 m3 = 12 x 0.0110625.
The perimeter joint (T-520 R-T520-1) depends on the module twice (kappa and the course height that sets the credited
head joints): it is re-run, not scaled.

## 4. Result

The register built from the rulebook holds 0.20 m only, so all 15 walls are HELD by name: "installed face module of
the 0.15 m black (cement) block: unit length x height and the joint it is laid with (block schedule, project
specification 04220, or the supplier's datasheet / sales record)". No units, mortar, cement or sand value is written
(never 0, never the 0.20 m module). The figures beside, for the three modules already named on the board (none a
source):

| Scenario | units / m2 | units (material base) | panel m3 (material base) | perimeter m3 figure .. high | cement bags | sand m3 |
|---|---|---|---|---|---|---|
| S-A 39 x 19 + 10 mm (40 x 20) | 12.500 | 2,194.14 .. 2,198.39 | 1.941812 .. 1.945573 | 0.079138 .. 0.089890 | 16.20 .. 16.28 | 2.227 .. 2.239 |
| S-B 40 x 20 + 10 mm (41 x 21) | 11.614 | 2,038.69 .. 2,042.64 | 1.865399 .. 1.869012 | 0.079389 .. 0.090176 | 15.59 .. 15.67 | 2.143 .. 2.155 |
| S-C 39 x 24 + 10 mm (40 x 25) | 10.000 | 1,755.31 .. 1,758.71 | 1.685098 .. 1.688362 | 0.079972 .. 0.090839 | 14.15 .. 14.23 | 1.945 .. 1.957 |

S-A reproduces T-520 (perimeter 0.079138 .. 0.089890, panel 1.975442 on the contract area vs 1.975440 pinned: per-wall
rounding) and T-506 (beside 1.945573, low 1.941811). Spread S-A -> S-C: units -439.7 (-20.0 %), panel -0.257 m3
(-13.2 %), perimeter +0.000834 m3 (+1.1 %: a smaller kappa is offset by fewer, taller courses). Cement bags exclude
waste (separate, not sourced). Freelancer: his workbook prices blockwork in m2 only (T-176), no units or mortar:
verdict proposal UNRESOLVED (no comparison possible; the datum is missing on both sides).

## 5. Rule, test, lesson

- R-T533-1 BLOCK_MODULE_BY_THICKNESS_V1 (every villa, every blockwork trade; consistent with UPC-BLACK-BLOCK-001, no
  rule-version change): the module is looked up by (block type, thickness) in a register whose entries carry a
  citation and a source status; a missing thickness returns HELD naming the datum; two disagreeing sources return
  CONFLICT; millimetres, unsourced or ESTIMATED entries are refused.
- tests/t533_block_module: fixture (4.00 x 3.00 by hand, second module by hand, rotated wall) + adverse (0.20 module
  never borrowed, missing area HELD not 0, millimetres refused, unsourced entry refused, two sources conflict, mix
  without source refused); Alsenan pins (reproduce, 15 walls blank HELD, S-A = T-520 / T-506, a sourced 0.15 entry
  stops the HELD builder so the wiring is revisited).
- Proposed lessons-register row: "A module confirmed for one block thickness was carried to another thickness of the
  same family in earlier notes (40 x 20 for 15 and 20 cm) | a product property treated as a family property | the
  installed module is per (type, thickness), sourced, or HELD by name; never by analogy (every villa) |
  tests/t533_block_module adverse 'register holds 0.20 only -> 0.15 HELD' | PROPOSED".

## 6. Owner item (for the Lead's daily package; ERS s.2.7 'material genuinely unspecified' after levels 1-4 are
exhausted; s.6 format; NOT added to OWNER_QUESTIONS.md by this worker)

Issue: the face size (length x height) of the 15 cm black block Urban buys, so the installed module is known.
Evidence: drawings and KSE 2023 silent; the 1990 specification §04220 not readable through the connector; Q-75 answer
gives the 20 cm block only (40 x 19 x 19).
Investigation: units and mortar computed for 3 candidate modules; quantities identical in method, only the module open.
Alternatives: (A) same face as the 20 cm block, 40 x 20 installed (12.5 / m2); (B) 40 x 20 actual face, 41 x 21
installed (11.6 / m2); (C) 40 x 25 installed (10 / m2); or upload §04220 as a PDF under 6 MB.
Impact (15 walls, 175.9 m2): units 2,198 / 2,043 / 1,759; panel mortar 1.946 / 1.869 / 1.688 m3; cement 16.3 / 15.7 /
14.2 bags.
Recommendation: answer from the supplier's sales record (the same kind of evidence as Q-60); A only if that record
shows a 39 x 19 face for the 15 cm block too.
Status: 0.15 m units, panel and perimeter mortar, cement and sand HELD (never 0). Next: everything else continues; the
answer drops in as one register entry (UPC rule version) and the builder re-runs.
