# PRE-S5 engineering questions (only those that change S5)

The project sources were exhausted first:
- ST7757.dxf: the SBT rows, TEXT / MTEXT in model space and blocks, layer-1 / 2 geometry;
- the p.8 and pp.13–16 claim register;
- the R4 project rule register.

Each question below is open because no project source answers it.

| # | Question | Members affected | What S5 can do until it is answered | Source searched |
|---|---|---|---|---|
| S5-Q1 | **Exterior ground-beam depth.** p.13 says "depth FOLLOW ARCH. (Ground Floor slab level to below Outer Normal ground level)". What is the depth, or the outer natural-ground level? | 20 PROJECT_GENERAL_DETAIL spans, plus every candidate span that includes the exterior section | Longitudinal bars (3Ø16 + 3Ø16 + 3Ø16): lower bound. Side bars (2Ø12 per 30 cm of depth) and the stirrup core path stay blocked. | p.13 claim P13-GB-EXTERIOR; S1 level register (no outer NGL printed) |
| S5-Q2 | **Which ground beams carry exterior walls?** The two geometric exterior tests disagree on 19 spans. Q-R4-6 is source-resolvable by an architectural overlay; that is wall work, out of scope here. | 23 CANDIDATE_DETAIL spans; for 13 of them exterior versus interior changes the bars (3Ø16 versus 3Ø14) | 13 spans blocked; 10 candidate-invariant spans are released as lower bounds | V3 zone outline, R4 footprint outline |
| S5-Q3 | **Length basis of the p.13 titles.** Is "length" the clear span between supports or the centreline span? | 7 spans change section with the basis (all below 3.1 m: LT2.5 versus LT5) | Bars are identical in both sections (3Ø14), so longitudinal bars are released. Section depth and stirrup stay blocked for these spans. | p.13 titles (literal) |
| S5-Q4 | **Below 2.5 m both "Less than 2.5m" and "Less than 5m" hold literally.** Is the 2.5 m section the intended one? It draws a stirrup with no size or spacing callout. | 15 spans with nested conditions | Bars are identical; the stirrup is blocked (no callout in one candidate) | P13-GB-LT2_5M-BARS / -SECTION (the section size is an AI transcription only) |
| S5-Q5 | **"Without concentrated load".** Does any ground beam carry a concentrated load? The interior sections are titled for beams without one, and no alternative section is drawn. | All 59 (condition preserved, not assessed) | Proceed with the literal title; flag only | p.13 titles |
| S5-Q6 | **Stirrup geometry.** Ground beams: a closed link is drawn in each p.13 section, but its legs, hook angle and extension are not stated. Straps: SBT gives Ø and per-metre count only; link topology (13Ø18 top in a 700 mm strap implies several legs) and hooks are not stated. | All stirrups | Count lower bound only; core path provisional (12 GB spans) or blocked; hooks blocked | p.13 sections; SBT block (ATTDEFs and Ø glyphs, no sketch); HOOKS_AND_BENDS = NO_PROJECT_SOURCE |
| S5-Q7 | **Development / anchorage.** Development of ground-beam bars into columns and supporting beams, and of strap bars into the footings. The 70Ø / 40Ø note (p.8 n.9) applies to starter bars only. | All longitudinal bars | Straight source-supported run only (lower bound); development components blocked | P8-N09 claim, R4 rule DEVELOPMENT_STARTER_70D_40D |
| S5-Q8 | **SB2 governing schedule row:** 80×50 (10Ø18 / 10Ø18) or 100×50 (20Ø18 / 10Ø16)? The drawn width is 987 mm. | SB2 | Blocked (SOURCE_CONFLICT; never released) | SBT inserts 1FBB, 2ABA |
| S5-Q9 | **Free ends.** 7 span ends (6 spans) end on no column or beam. What supports them? | 6 spans | Lower bound to the drawn end; flagged | GBP layer-1 geometry |
| (open) | F / F10 identity of outline 1B1B (S4) | SB1 start support | SB1's clear length is measured to the drawn face. Both candidate footings are smaller than the drawn outline, so it is a lower bound. | carried from S4 |
