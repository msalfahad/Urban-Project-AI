# T-230 Strap and tie-beam (ground-beam) ends into footings, necks and walls: every intersection volume once

Worker 1, 2026-10-23 (lane S, gate 2; Alsenan + every villa). Research only, unwired: `end_ownership.py`
(END_OWNERSHIP_V1, stdlib, `DEFAULT_GUARD_CLASS = "UNWIRED_PRODUCER"`), `t230_extract.py` (DXF -> values-only
`ALSENAN_END_INPUT.json`), `t230_alsenan_check.py` (-> `LEDGER_T230.csv`, `summary.json`), tests
`tests/t230_end_ownership/` (Villa T hand fixture + Alsenan ledger). No released or candidate quantity, rule file,
frozen method or engine module changed; T-174's module and GROUND_SYSTEM_SPANS_V2 are read only.

Sources (Drive "Alsenan chalet project"): ST7757 dxf.dxf (sha 9f9d1179; GROUND BEAMS PLAN layer 1 bands, S-COL.BON,
S-BW ring 7C2 / 7BE; FOUNDATION PLAN S-FOOTINGS, S-COL.BON), ST7757.pdf p.8 (notes), p.9 (footing schedule), p.10 (SB1-3
rows), p.13 (typical isolated footing, ground-beam sections), p.14 (lift detail), all read this run. Merged records
reused with citation (never as proof of a quantity): T-174 (strap plan areas in the footings, Checker 14:52), T-141
(spans, p.13 depth classes), T-138 (exterior-wall beams), T-205 (neck = footing top -> GB top, beams net of the neck),
T-206 / T-214 (level chain: footing soffit = formation + 0.17; formation AT_MOST -1.50; GF slab top +0.95, annex +0.25),
T-217 (neck section readings), T-204 (lift ring, ground beams stop on its outer face), R-CONC-OWN-1 (T-189).

## 1. The physical elements and the question

At the foundation of a Kuwait villa three element families meet the footings: **straps** (SB, cast between two footings
at footing level, Q-74 axis length), **necks** (the column from the footing top to the ground-beam top, billed through at
full section) and **ground beams / tie beams** (at GF slab level, between necks; p.13). For every end: which solids
really intersect in 3-D, how much, and who owns it (R-CONC-OWN-1: the element billed through owns; the other is net; a
plan overlap is no intersection unless the solids overlap in 3-D, Q-62).

Searched for a strap level or section: ST PDF p.8 notes (24 items, none on straps), p.10 (SB rows: B, D, bars only),
p.13 / p.14 (footings, ground beams, lift, boundary wall: no strap), DXF texts (only 'S.B3' and the SB schedule
attributes) and blocks (SB1 / sb2 blocks hold only the label). **The strap level against the footings is printed
nowhere** (confirms T-174).

## 2. Strap ends (owner manual method beside the drawing-derived solid)

Owner / Urban method (Q-74): strap = B x D x axis between the footing faces; "concrete inside a footing counted once"
(3.3905 m3, T-174, unchanged). Drawing-derived: the strap is one straight member of one printed section, so its soffit
is ONE level e (above the soffit of the footings it joins: footing soffit = formation + 0.17 for every type, T-206).
Inside a footing outline: footing owns A_net x overlap(e); strap owns A_net x (D - overlap); the neck owns the strap
above the footing top inside its footprint (the neck is billed from the footing top up).

| End | D / H | A_net / A_col (m2, T-174) | footing owns (e = 0) | strap excess (e = 0) | neck (e = 0) | status |
|---|---|---|---|---|---|---|
| SB1 / F8 | 0.50 / 0.50 | 1.155 / 0 | 0.5775 | 0 | 0 | DRAWING-CONFIRMED at e = 0 |
| SB1 / F10 + F | 0.50 / ? | 0.770 / 0.035 | - | - | - | HELD (Q-31 C: which footing, H) |
| SB2 / F11 | 0.50 / 0.50 | 1.2228 / 0 | 0.6114 | 0 | 0 | DRAWING-CONFIRMED at e = 0 |
| SB2 / F6 | 0.50 / 0.50 | 1.4764 / 0.21 | 0.7382 | 0 | 0 | DRAWING-CONFIRMED at e = 0 |
| SB3 / F15 | 0.40 / 0.40 | 0.3755 / 0.0242 | 0.1502 | 0 | 0 | DRAWING-CONFIRMED at e = 0 |
| SB3 / F3 | 0.40 / 0.30 | 0.2953 / 0.0463 | 0.0886 | **0.0295** | **0.0046** | HELD (level), see below |

**Finding 1 (the T-174 range is not one level).** T-174 held SB3 / F3 at 0.0295 .. 0.1181 m3 while keeping the F15 end at
0. Its high end (strap entirely above F3, e >= 0.30) puts the same straight strap 0.30 m above the F15 soffit, so the
F15 end then carries 0.3755 x 0.30 = 0.1127 m3 of excess too. Over every level at which the strap is cast monolithic
with both footings (-0.40 < e < 0.30): SB3 excess **0.0295 (e = 0, the unique minimum) .. 0.2683 m3** (0.2308 with the
soffit not below the footings). The e = 0 state is the one where every other strap end (SB1 / F8, SB2 / F11, SB2 / F6,
SB3 / F15, all D = H) has zero excess: the designer sized each strap's depth to the footings it joins (D = H at 5 of 5
known ends), which is drawing evidence for "soffit flush with the footing soffits", but not a printed level. So:
- the T-174 zeros at the D = H ends are conditional on e = 0 (exposure 0.1155 / 0.2699 / 0.0671 m3 per 0.10 m of e for
  SB1 / SB2 / SB3, all ends);
- SB3 / F3 stays HELD: 0.0295 m3 strap excess + 0.0046 m3 to the neck at e = 0, range up to 0.2683 m3 (never 0);
- the remaining physical question is ONE level per strap (soffit flush with the footing soffits or not), and for SB3
  also whether F3 and F15 share one formation (T-206: formation HELD, Q-21 C). Designer item: narrow D-15 ("blinding
  under straps"), which already asks what the strap sits on, rather than a new item.

Strap vs ground beam: 11 plan overlaps (1.680 m2) under SB1 / SB2 / SB3, no 3-D contact: strap top at most -0.83 (SB1,
SB2) / -0.93 (SB3) at e = 0, at most -0.33 / -0.63 at the monolithic bound; ground-beam soffits at least +0.35 in the
main house (top +0.95, D <= 0.60; SB1 / SB2 lie under +1.00 level marks) and -0.35 in the annex (top +0.25; SB3 lies
under the +0.30 marks): gap >= 0.28 m. Strap bars (D-36), links (D-37), SB2 row (D-38) unchanged.

## 3. Ground-beam ends at necks (34 junctions, 72 ends)

Basis checked: GROUND_SYSTEM_SPANS_V2 face to face, faces read from the column outline DRAWN ON THE GROUND-BEAM PLAN;
neck = the PRINTED section (T-205 / T-217). Per junction: DOUBLE = neck plan inside a billed span; GAP = beam strip drawn
beside / around the neck that no span bills (union over the ends, counted once).

| Junction | Ends | What the drawings print | DOUBLE / GAP plan (m2) | m3 | Owner | Status |
|---|---|---|---|---|---|---|
| 26 junctions | 52 ends | outline = printed section, column covers the band | 0 / 0 | 0 | - | DRAWING-CONFIRMED |
| C at F (GBP 204), C at F (207), C3 at F15 (20B), C at F (214) | 136+7D5#1, 7D4+F8#1, 7D4+F8#2, 137+138#1 | GB plan draws 0.30 x 0.40; printed 0.30 x 0.50 (CAP text + dims) drawn on the foundation plan at the same place (3 of 4 edges coincide): the 0.10 m lies in the span | DOUBLE 0.030 each, 0.120 | **0.096 .. 0.114** (exterior beams, depth 0.80 .. 0.95 "FOLLOW ARCH.", D-35) | NECK; beam -0.10 m at each end | plan DRAWING-CONFIRMED, m3 HELD on D-35 |
| C3 (211) | 13D+7D2, 13E+7D6 x2 | both bands drawn through the corner beside the 0.30 x 0.50 neck (0.10 x 0.30) | GAP 0.030 | 0.009 .. 0.0285 | GROUND BEAM keeps it | plan DRAWING-CONFIRMED |
| C8 (24D) | 184+7CF#1 / #2, 7DC+7DD | 0.30 x 0.80 drawn + text vs schedule 0.30 x 0.90 (T-217 CONFLICT) | DOUBLE 0 .. 0.030 | 0 .. 0.012 | NECK | CONFLICT (range, never its larger end) |
| lift C2 (1F2) | 15C+7CC | 0.20 x 0.50 vs schedule 0.30 x 0.50 (CONFLICT) | DOUBLE 0 .. 0.030 | 0 .. 0.012 | NECK | CONFLICT |
| lift C2 (1EF), oblique band | 17E+17F | as above; band leaves the column corner obliquely | DOUBLE 0 .. 0.005, GAP 0.0047 .. 0.0104 | 0 .. 0.002 / 0.0014 .. 0.0042 | NECK / GB | CONFLICT |
| lift C1 (1F5), C4 (1E8) | 15E+15F, 1811+1812 | section differs across the band width only | 0 / 0 in every reading | 0 | - | DRAWING-CONFIRMED (0) |

**Finding 2.** On four exterior-wall beam ends the span is measured to a drafting outline (0.30 x 0.40 on the ground-beam
plan) while the neck is 0.30 x 0.50 (printed, T-217 DRAFTING_NOTE): the beam is billed 0.10 m into the neck at each, 0.12
m2 of plan, 0.096 .. 0.114 m3 counted twice (neck + beam). The same applies to the frozen route G beam lines, whose basis
also deducts the drawn ground-beam-plan outline (generic_route 'column footprint split out'); not quantified here.

## 4. Ground-beam ends at the lift (footing outline is not a support)

Three ground beams are drawn to the outer face of the RC pit ring (S-BW 7C2, T-204: "edges stop on the ring's outer
face"). GROUND_SYSTEM_SPANS_V2 (and S5 and the T-138 hand ledger, which follow it) ended two of them at the lift footing
FF outline (FOOTING_FACE, 1B2B) and held the third: but the beam (soffit >= -0.35) and the footing (top <= -0.63) never
touch, so a footing outline cannot terminate a ground beam.

| Span | V2 end / length | Drawn support | Length to the ring face | p.13 class | m3 (0.30 wide) | V2 m3 | change |
|---|---|---|---|---|---|---|---|
| 15D+7C8#1 | FF outline, 1.8999 m (CANDIDATES < 2.5 / < 5) | ring 7C2 outer face | **2.900** | < 5 m: 0.40 | **0.3480** | 0.1710 .. 0.2280 | +0.120 .. +0.177 |
| 17C+7E3#1 | FF outline, 1.9278 m | ring 7C2 | **3.228** | < 5 m: 0.40 | **0.3873** | 0.1735 .. 0.2313 | +0.156 .. +0.214 |
| 177+7CD#1 | HELD (GAP_TO_COLUMN 1EC; 4.97 / 5.02 / 3.52 candidates) | ring 7C2 (band end = ring face to 0.2 mm; C9 1EC is 50 mm beside the band, not in its path) | **5.020** | > 5 m: 0.60 | **0.9036** | HELD | resolves the T-141 hold (5.02, > 5 m) |

Bars and formwork of these spans move with them (top / bottom runs +1.000 / +1.300 m, sides 2 x dL x D); not
quantified here (lane I with the T-138 ledger). The pit wall is its own line (T-204, height HELD); the ring owns its
wall section, the beam stops on its face: no overlap.

Ground beams over footings in plan: 80 overlaps on 51 spans, 19.925 m2 of plan; 3-D intersection 0 (gap >= 0.28 m, see
s.2 levels). Nothing is deducted for them (Q-62), and none of them is a beam end.

## 5. Engine vs freelancer, verdict proposals

- Straps: concrete 3.3905 vs freelancer 3.3925 m3 (-0.06 %) unchanged (owner method = drawing-derived at e = 0); SB3 / F3
  excess HELD 0.0295 .. 0.2683 m3 (T-174 range 0.0295 .. 0.1181 superseded: one level for one strap). UNRESOLVED
  (designer: strap soffit level, D-15 narrowed).
- Ground beams: the freelancer prices every beam 0.30 x 0.60 x 253 m inside "ground beams + ground floor" with the slab
  (T-138): no per-end comparison is possible. ENGINE (V2 face basis) WRONG at the 3 lift ends (+0.276 .. +0.391 m3 of
  beam missing on the face-to-face basis, plus the held 0.9036) and at the 4 drafting-note ends (-0.096 .. -0.114 m3
  double); RULE_DIFFERENCE none.
- Necks: unchanged (T-205); they own every DOUBLE above.

## 6. Rule (proposed, R-END-OWN-1; any villa; provenance T-230 on R-CONC-OWN-1, Q-62, Q-74, T-174, T-205)

A strap end inside a footing is footing concrete up to the footing's own depth; the strap keeps what lies outside that
depth, except inside the neck footprint above the footing top (neck). A strap is one member at ONE soffit level:
every end is evaluated at that same level, so a range is never assembled from two levels; equal D and H is evidence for
a flush soffit, never a printed level. A ground beam is billed net of the PRINTED neck section (a drafting outline on
the beam plan is not a face); a beam strip drawn beside a narrower neck is beam concrete; a footing outline never
terminates a ground beam (no 3-D contact): the support is the element drawn at the band end (neck, wall, beam), else
HELD.

## 7. Lessons-register row (proposed, ERS s.7)

| 2026-10-23 | Ground beams ended at the lift footing outline (1.90 / 1.93 m) though drawn to the pit ring 1.00 / 1.30 m further, and four beam ends measured to a 0.40 drafting outline into a printed 0.50 neck; the SB3 / F3 range assembled from two strap levels | Plan outlines were used as faces without the vertical check (a footing 0.28 m+ below the beam) and without the printed section; the two strap ends were bounded independently | A face is a face only if the solids touch in 3-D and the section is the printed one; one member has one level, every end at that level (every villa; straps, ground beams, tie beams) | tests/t230_end_ownership (Villa T: angled strap into a shallower footing, neck in the strap end, one-level range, drafting outline double, oblique gap; adverse: both-owner double, centre / projection length, two-level range, footing as support, missing H -> HELD) | proposed (T-230 READY) |

## 8. What remains

- Designer: strap soffit level (narrow D-15); D-35 exterior beam bottom (the m3 of Finding 2); T-217 C8 / lift CONFLICTs.
- Lane I: apply the lift-ring lengths and the net-of-printed-neck ends to the V3.0 ground-beam lines with bars and
  formwork; keep SB3 / F3 as its own HELD line with the new range.
- Annex / main ground-beam tops for the interior beams are taken as the slab tops (T-205 relation, T-214 values); only
  the separation proofs use them, with >= 0.28 m margin.
