# PRE-S6 engineering questions

Only questions whose answer changes a quantity. Each names the components it unblocks. No answer is assumed anywhere
in the registers.

## A. Engineering questions

**Q1 - Anchorage / development of beam longitudinal bars at end supports, and bar-end hooks.** The drawing gives a
development rule only for starter bars (note 9: 70Ø tension / 40Ø compression); the slab 0.25L / 0.30L rules are slab
rules. What anchorage applies to beam bottom and top bars at end supports (straight, hooked, length)?
Unblocks DEVELOPMENT_ANCHORAGE and HOOKS on 102 occurrences; turns 156 LOWER_BOUND longitudinal
components into complete bars.

**Q2 - CB top bars and hangers.** The schedule frames draw one top bar per span, from the end support (with a leg) to
near the interior support, with a printed count and diameter. The typical elevation draws instead an end-support bar
('0.3 Ln2') and a separate second-row bar lapping the MID bar, unlabelled. Which governs, what are the extents, and
is the second row a hanger with its own count / diameter? Unblocks 26 CB TOP runs and 13 CB HANGER rows.

**Q3 - Typical-detail labels.** In the 2-span typicals the end top bar is dimensioned '0.3 Ln2' (a 2-span beam has
only Ln and Ln1) and the left end top bar is not dimensioned; the 3-span typical labels its third clear span 'L3'.
Which spans are meant?

**Q4 - 3-span middle bottom bar '0.15L'.** The bar enters span 1 at support 1 and span 3 at support 2; 'L' names the
clear span of span 1 in the typical. Is the extension 0.15 x the clear span it enters? Today the extension is left
out (the run is a lower bound).

**Q5 - Ln for the MID extent.** The typical dimensions 'Ln' axis to axis and 'L' face to face, so the MID bar is
released as 0.22 x (axis-to-axis span) from each face (9 READY runs). Please confirm (in common notation Ln
is the clear span; if so the MID bars would be re-released on the clear span).

**Q6 - Side bars '2Ø12/30cm' (SBT REMARKS) and '2Ø12' + '30cm' (CB MIDDLE REINT.).** Per face or in total; does
'/30cm' mean a vertical spacing (so the count grows with depth) or something else; full length or between supports;
end treatment? Note 21 (AI transcription) asks for side bars in beams deeper than 60 cm. Unblocks 39 side-rebar rows.

**Q7 - Stirrups.** Number of legs (the SBT REMARKS icons STR2 / str3 draw an outer and one / two inner closed links
on B17, B19-B26 and the straps; no legend), hook type and length, first stirrup position, any end-zone densification.
Unblocks all 118 stirrup-mass rows (counts are already released as lower bounds).

**Q8 - Simple-beam longitudinal bars.** The release assumes SBT 'BOTTOM BARS' and 'TOP BARS' run at least support face
to support face, uncurtailed (no curtailment field or detail exists). Please confirm. Basis of 142
READY_LOWER_BOUND simple-beam components.

**Q9 - Special beams.** (a) Curved ring beams (BM-1F_ROOF-B4-BA001-1829, BM-1F_ROOF-B4-BA002-1828, BM-GF_ROOF-B7-BA001-47D:b7>v, BM-GF_ROOF-B7-BA002-46E, BM-GF_ROOF-B7-BA003-470, BM-GF_ROOF-B7-BA004-46F, BM-GF_ROOF-B7-BA005-471): where along the ring do the bars stop (support
positions)? (b) 'WITH STAIR' spans (BM-1F_ROOF-B3-BL023-6B9, BM-GF_ROOF-B3-BL033-6B7): does the p.16 stair-beam detail change the SBT bars? (c) The
span carrying a planted column (BM-GF_ROOF-B26-BL014-4CC): does the p.15 detail add to or replace the SBT bars? (d) The
cantilever CA (BM-GF_ROOF-CA-BL015-69E): bar run to the free end and anchorage into the back span.

## B. Drawing reconciliation (confirm, nothing is assumed)

**R1 - Bindings left as candidates:** TAG:GFRS:445, TAG:GFRS:45D, TAG:GFRS:474, TAG:GFRS:476, TAG:SFRS:78F. 445 / 476 / 78F: an alternative member is excluded only by
text rotation; 45D: B1 on BL016 or the 200 mm band BL021 that shares a face with BL020; 474: CB5 on BL008 (same-mark
continuity with 475) or the parallel band BL017 that shares a face with it.

**R2 - Width conflicts:** FFRS B6, FFRS CB10, GFRS B21, GFRS B29, GFRS CB2 (drawn band width vs schedule B). Which is right?

**R3 - CB span conflicts:** CBO-GFRS-CB4-BL016, CBO-GFRS-CB5-BL008 (span lengths) and CBO-GFRS-CB8-BL024 (2 tagged spans vs 3 schedule spans;
including the adjacent untagged 3.825 m span would match - is it part of CB8?).

**R4 - CB reading direction:** CBO-FFRS-CB13-BL004, CBO-GFRS-CB2-BL038, CBO-GFRS-CB7-BL003 match the schedule in both directions. Which end is span 1?

**R5 - CB3:** its middle span is also tagged 'B3 WITH STAIR' (1827); the MID1 cell is blank while a 3Ø16 callout is
drawn on a longer bar; MID2 is blank.

**R6 - Untagged geometry:** 38 spans / arcs carry no tag (18 were not in the S1 census), including the six 1F dome
ring arcs. Which marks apply?
