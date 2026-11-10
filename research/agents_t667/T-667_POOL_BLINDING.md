# T-667 Pool blinding (MISSING B10 item) and pool steps (HELD)

Worker 2, 2026-11-10, branch `agents/task-T-667`. Research only (no hub, no master, no engine module; wiring is a lane I
row). Development villa, not an accuracy claim; the method R-T667-1 .. 5 is for every villa. ERS s.2 - 5 applied; owner
Q-26 A (flat floor); T-183, T-445 / T-478, T-597, T-659 read, not re-derived.

## 0. Sources (own reads this run; Drive 'Alsenan chalet project', decoded into `.work/private` only)

- ST7757.pdf p.7 DETAIL OF SWIMMING POOL (N.I.S.): walls 20, base 40, plan and depths 'AS PER ARCH'; from the base
  down '5cm SECREED. / 5cm INSULATION MEMBRANE. / 10cm PLAIN CONCRETE.'; screed and membrane drawn under the base AND up
  both outer wall faces, standing on the plain concrete; the plain concrete drawn past the outer membrane at both ends,
  **no projection dimension**. The detail draws a sloped floor with a shallow bench; owner Q-26 A set the slope aside
  (flat floor at 1.15 m). No step, ladder recess or bench dimension.
- ST7757 dxf.dxf (sha 9f9d1179), `t667_extract.py`: outer outline S-BW 7C6 (back 3.50 straight, sides 1.75, bulge -1
  half circle r 1.75) = 10.935563 m2 / 12.497787 m sampled on the true circle (ezdxf's Bezier path overstates the arc by
  ~0.03 %: 10.93679); water outline 8.578838 m2. Ground-beams frame and foundation frame share the plot line (both 31.37
  wide, same lower edge): shift = difference of the left edges, **proven by 35 of 35 columns of the ground-beams frame
  falling inside a footing outline**. The pool back lies ON the plot line (gap 0.000).
- P7757.dxf: text search 'pool / swim / step / ladder' (EN + AR): only the label block; nothing on steps.

## 1. The physical element and the two methods

Blinding = plain concrete 0.10 on the formation under the pool base. The wrap layers (5 + 5 cm) under the base turn up
the outer wall faces and stand on the blinding, so the blinding covers at least the base footprint grown by 0.10.

| | Owner manual method | Drawing-derived method |
|---|---|---|
| plan | (L + 2p)(W + 2p) x t with p = what the detail prints | outline 7C6 grown by the printed wrap 0.10 (mitred at the two back corners, true offset on the arc), clipped at the plot line |
| p | not printed -> the drawn minimum (wrap) | same; projection beyond the wrap OPEN (C4) |
| floor | Q-26 A flat: plan area | same (a sloped floor would take true section lengths, R-T667-2) |

Hand calculation: core 3.50 x 1.75 + pi 1.75^2 / 2 = **10.935564 m2**; grown 0.10 = 10.935564 + 12.497787 x 0.10 + 2 x 0.01 +
pi/2 x 0.01 = 12.221050; beyond the plot line (3.50 + 0.20) x 0.10 = 0.370; **in plot 11.851050 m2** (= T-597 pool
excavation envelope 11.851050, Checker re-measured; = own DXF 11.85105).

## 2. Line by line (m3)

| Line | Before (V3.0.61) | After | Status | Basis / item |
|---|---|---|---|---|
| NEW STR.CONC.BLINDING POOL-1 | MISSING | **>= 0.915529** | HELD LOWER_ONLY | plan-distinct: 11.851050 - 2.695761 (VERIFIED pit layer, one layer in plan) = 9.155289 m2 x 0.10 |
| beside: own layer in plot | - | 1.185105 | DRAWING-CONFIRMED plan, AT_LEAST | footings deeper than the pool: both layers cast |
| beside: beyond plot line | - | 0.037 (mitred; 0.0365708 round) | existence open (D-14 item) | back wall = boundary wall face on the plot line |
| L-b62a7065 pool steps | HELD blank | HELD blank | HELD | none drawn or dimensioned (R-T667-5); consultant C5 |

Items keeping the pool blinding from a value: (1) projection beyond the wrap drawn, not dimensioned (C4); (2) founding
levels of F8 / F4 / FN vs the pool formation -1.50 not printed (C6): one layer or two. Both are on the designer lists;
no owner question (ERS s.2.7 not met). T-183 B '>= 1.222' is superseded: it did not clip the plot line.

## 3. One element once: the blinding lines of V3.0.61

| Line | Touch |
|---|---|
| L-98eb2d58 pits (VERIFIED 12.734438) | **SHARES PLAN, NOT CHANGED**: its grown layer covers 2.695761 m2 of the pool plan (F8 1.931845, F4 0.735358, FN 180C 0.028558; = T-597's pits share given to the pool envelope, exact); netted at the pool low end |
| L-16b95607 FF raft | not touched (not within 1 m) |
| L-10032bf9 beyond plot (footings) | not touched; the pool's own 0.037 beyond is beside the pool line under the same item |
| L-080c97f5 F10 + F | not touched |
| L-35382b18 straps | not touched (no strap line within 1 m on the foundation plan) |
| L-7a5214a3 ground beams | not touched: nearest GB line 0.4998 m; 0.30 m clear after both 0.10 growths (a touch needs an undimensioned pool projection > 0.2998 m) |
| L-d0313e5d boundary-wall base | not touched: the band 7FE stops at the pool corners; no pad under the pool |

## 4. Findings

- **F-T667-1 (interface, no quantity moved): the pool sits over TWO footings, not one.** Besides F8 (outline over the
  pool outline 1.296549 m2, T-183 interface 1), **F4 (outline 1666) overlaps the pool outline by 0.282424 m2**; footing
  outlines F8 + F4 clash with the pool base footprint by 1.578973 m2. The designer item C6 (founding levels) now names
  F4 as well; the pool excavation (T-350 / T-597) already gives the pool envelope priority over the pits.
- **F-T667-2 (for T-666 stretch ownership):** on the ground-beams plan the boundary band 7FE does not run along the pool
  back (0.001 m of 3.50): the pool's back wall replaces it. The B10-11 band high end uses the gross centreline 91.94 m
  (whole plot perimeter), which includes these 3.50 m: 0.20 x 0.60 x 3.50 = 0.420 m3 of band concrete where the pool
  wall and base already stand (0.280 m3 at 20 x 40, if the low end's 70.49 m also includes them: not established here).
  Not changed here (T-659 / T-666 line).

## 5. Engine vs freelancer

| Element | Engine | Freelancer | Verdict proposal |
|---|---|---|---|
| pool blinding | HELD >= 0.915529 (own layer 1.185105) | no row; one plate 47.055 m3 = plot x 0.10 (T-478) | NOT_LIKE_FOR_LIKE (inside his plate); ENGINE_RIGHT on scope (the drawing prints it) |
| pool steps | HELD blank | 0.228 m3 (0.30 x 2.00 x 0.38, sizes his own) | RULE_DIFFERENCE: an undrawn element added; never a bound |

## 6. Rules, tests, lessons row

R-T667-1 .. 5 in `t667_rules.py`. `tests/t667_pool_blinding` (28): hand villa V667 rectangle 6.00 x 4.00 -> 26.04 m2 /
2.604 m3; printed projection 0.15 -> 2.925; sloped 2.00 + 2.40 (drop 0.70, true 2.50) + 1.60 -> 2.644; D r 2.00 b 1.20 on
the plot line -> 11.967212 m2 in, 0.42 beyond; rotation / mirror vs a polygon offset; adverse: drop not printed / AS
PER ARCH / section not closing -> HELD, overlap counted once (2.484 vs 2.604) and refused without its line or above
the plan, edge 'arc' on the plot line, mm / cm / slip / 0 / blank / typical / freelancer refused, no wrap, steps only
when drawn; Alsenan rebuild = committed, key figures, an edited input stops the build.

Lessons row (ERS s.7, PROPOSED): | 2026-11-10 | pool blinding missing from the candidate; T-183 stated it '>= 1.222'
unclipped and named one footing under the pool | the pool's layers were read from its own detail only; the plot line
and the foundation plan's outlines were not overlaid | a pool / tank blinding is the base footprint grown by the
printed wrap, clipped at the plot line, overlaid on every counted blinding layer (plan-distinct low, own layer beside)
(every villa; R-T667-1, -3, -4) | tests/t667_pool_blinding test_overlap_counted_once, test_edge_on_plot_line | PROPOSED |

## 7. For the Checker

Re-measure: the pool outline (ST DXF S-BW outer: back 3.50, sides 1.75, half circle r 1.75) and its 0.10 growth in the
plot (11.851050 m2); p.7 wrap 5 + 5 cm and '10cm PLAIN CONCRETE', projection undimensioned; the pit-layer share
2.695761 m2 (T-597 has the same figure by integral); F4 1666 over the pool outline (0.282424 m2).
