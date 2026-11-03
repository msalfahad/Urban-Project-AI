# T-350 r4: calculated earthworks quantities wired into the candidate (ARCH_TAKEOFF_V3.0.48), integration package for Gate B

Lane I wiring of Checker-merged lane S quantities. No quantity is invented, changed or approved here: every figure is
read from a sha-pinned merged file (research/agents_t350r4/t350r4_inputs.py).

| source | task | merge | Checker |
|---|---|---|---|
| research/agents_t350r2/FILL_T350R2.csv | T-350 r2 | 42a99508 | Verifier 2026-11-03 06:05 UTC, Gate A PASS (own zone plan 124.649020 m2, excavation 208.163863 m3 AGREE) |
| research/agents_t484/summary_t484.json | T-484 | 12395ea4 | Verifier 2026-11-03 09:56 UTC, Gate A PASS (necks, strap ends VERIFIED; backfill PARTIALLY VERIFIED 6 / 8) |

## 1. Physical elements and level basis

- Excavation of a zone: the neat plan of the pits / trench / pool envelope inside the plot line, from the existing
  ground (+-0.00, T-357 DERIVED) down to the formation. Level basis S01 ESTIMATED (owner-accepted RFI re-review
  2026-11-02): footing underside at the printed 1.50 m minimum, underlay 0.07 + blinding 0.10 under it -> -1.67.
- Backfill of a zone: its excavation minus every buried element below the existing ground at its actual position, once.
- Disposal: excavation minus re-used fill, by dry mass (owner 2026-11-02 18:00 (3)): every density HELD -> line HELD.

## 2. Owner manual method and drawing-derived method, side by side

| line | owner manual method | drawing-derived (merged) | V3.0.47 | V3.0.48 | evidence status (WC s.5) |
|---|---|---|---|---|---|
| B1-02 pits 24 | plan x depth EG -> formation | union of 24 outlines by handle in plot, minus pool envelope = 124.649555 m2 x 1.67 | HELD BLANK (at least 188.017207 beside) | **208.164757 m3** PROVISIONAL | ESTIMATED (S01); +-0.10 m 195.699801 / 220.629712 beside; printed-minimum bound 186.974333 (F-T350R2-1) |
| B1-02 pool | envelope x printed -1.50 | envelope in plot 11.851051 m2 x 1.50 | HELD BLANK (at least 17.776576) | **17.776576 m3** SOURCE_DERIVED | DRAWING-CONFIRMED |
| B1-02 ext main GB trench | strip L x B x blinding depth outside the pits | r2 route-G 1.391722 .. 1.418002; T-484 own strip 1.432834 incl. 0.229565 beyond plot | HELD BLANK | **1.203269 .. 1.432834 m3** BOUNDED | HELD (envelope, plot clip S06 / D-14) |
| B1-02 F10F outline | plan x depth per reading | F10 alone 7.2645 .. 7.515; F10 + F union 7.2645 .. 8.0995 (T-484, replaces r2 sum 8.7675 .. 9.352); drawn outline 8.39175 | HELD BLANK | **7.2645 .. 8.39175 m3** BOUNDED | ESTIMATED (S02 scenarios) |
| B1-03 pits 24 | excavation - buried structure | 208.164757 - verified 71.925255 - re-measured 7.595955 .. 16.276167 | HELD BLANK | **119.963335 .. 128.643547 m3** BOUNDED | PARTIALLY VERIFIED 6 / 8; 11 layers at 0.15 m (OWNER-PROVISIONAL) beside |
| B1-03 F10F | (gap) | r2 PROPOSED_NEW_LINE_HELD | no line | **added HELD BLANK** | HELD |
| B1-03 FF lift pit | (gap) | lift pit depth not printed | no line | **added HELD BLANK** | HELD |

Unchanged HELD BLANK (S01 does not settle their open dimension): B1-02 FF lift pit, interior ZERO / D-33, annex,
court, straps, boundary, lower GB row (S01 2.45 m -> not required, +0.10 m -> required: flips); B1-03 pool, ext GB
trench, other trenches, Z2; B1-04 disposal.

## 3. Reconciliation (named, not picked)

- Ext GB trench: the two merged readings differ by a plot-line clip, not by a measurement error. r2 read route-G run
  lengths (dL range) with no clip; T-484 closed the cut on its own strip polygon (27.919513 m2) to one value, of which
  2.295645 m2 x 0.10 = 0.229565 m3 lies beyond the plot line. The pits zone holds its beyond-plot strip; the trench
  line therefore carries in-plot (1.203269) .. with beyond-plot (1.432834); r2 lies inside. Neither was re-measured by
  the Checker: the Gate B hand check decides; no figure was chosen because it is larger.
- F10F: r2 summed the F10 and F plans (8.7675 .. 9.352); T-484 F-T484-4 (ENDORSED) unites them (one excavation, one
  plan): the range high end becomes the drawn outline 8.39175.
- Backfill closure (asserted by the module at both ends): 208.164757 - 71.925255 - 16.276167 = 119.963335;
  208.164757 - 71.925255 - 7.595955 = 128.643547. Width 8.680212 = D-33 / D-35 sections 8.650212 + C8 0.030 (named).

## 4. What stays HELD (never 0)

working space (OQ-13), beyond-plot parts (S06 / D-14), F8 / F4 / FN pit chains under the pool formation 0.458211 m3
(F-T350R2-2 CONFLICT), D-33 / D-35 beam sections, C8 mark conflict, lift pit FF depth, the trench zones S01 does not
settle, disposal densities.

## 5. Registry

BOQ_FAMILY_MASTER 1.45.0 = 1.44.0 + pending V3.0.48 (package id T-350b: T-350 is the merged V3.0.43 package) + B1-02 /
B1-03 / B1-04 text + rule r4 (F-C-T485-1): the 7 families that own no item code (B2-01, B2-03, B2-04, B2-05, B4-04,
B7-14, B11-03) say 'N/A', never 'yes' (tools/family_master_candidate.py r4, from 1.45.0 on; earlier versions unchanged).
Known, pre-existing: tests/t485 'merged package never stays pending' fails on the working branch e8ee22f0 itself (T-443
merged but pending in 1.44.0): its promotion needs the V3.0.47 census (a T-485-style promotion), not done here.

## 6. Who is right

No freelancer earthworks line and no released line: no comparison (UNRESOLVED for the held zones).

## 7. Lessons row (proposed)

2026-11-03 | two merged readings of one cut differed only by the plot-line clip | carry the envelope of the merged
readings with the clip named, and state the closure arithmetic in the module (excavation - displacement at both ends) |
T-350 r4.

## 8. Development-villa run (stage 2, 2026-11-03 22:19 UTC)

`research/agents_t350r4/v3048_run.py` on the Drive copies (architectural DXF from P7757_DXF_COMPRESSED.zip; structural
'ST7757 dxf.dxf' sha 9f9d1179), T-167 base run fresh on the same drawings: V3_0_47_BOQ_LINES.json = **e86a53a8** (the
candidate of record, asserted) -> V3_0_48_BOQ_LINES.json **33a81c53**; 4,874 -> 4,876 lines; 5 CHANGED, 2 ADDED,
4,869 byte-identical (outside rows sha 669b0a0b). Totals moved only in STR.EARTH.EXCAVATION (valued 0 -> 225.941333 =
208.164757 + 17.776576; held 8.467769 .. 9.824584 = trench + F10F; blocked 12 -> 8) and STR.EARTH.BACKFILL (held
119.963335 .. 128.643547; blocked 5 -> 6, lines 5 -> 7); disposal unchanged. Against released V2.9: every earthworks
line NOT_IN_RELEASED (no released line moves). Summary: summary_t350r4.json (ids, codes, states, quantities only).
