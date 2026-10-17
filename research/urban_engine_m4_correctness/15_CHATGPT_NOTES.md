# Notes for ChatGPT: what worked, what is not working, what to do next (M4)

## What worked

**Continuous beams**
- Span matching against the printed span sequence works on 11 of the 12 ST7757 lines:
  - 7 forward, 1 reversed, 1 symmetric;
  - 2 with an ambiguous direction, where the larger reading is the base and the other the range;
  - 1 count conflict, reported and not guessed.
- One unlabelled span took its mark through the sequence.
- The physical bar model gave 24 pieces their bottom, support-top and stirrup bars, 1,835 kg. Mass is conserved per line (IC-06).

**Alignment-only spans**
- Alignment alone no longer carries a section across a support.
- On 40 new synthetic villas, M3 gave 72 unlabelled spans a wrong section; M4 gave none.
- Every span M4 held keeps the truth inside its exposure.

**Architectural evidence**
- The architectural plans register on the structural columns: 28 of 30 on the ground floor.
- They decide the exterior ground beams, and they give 57 lintel openings.

**Independent checks**
- shapely, used as a second method, found three real engine defects, all fixed:
  - dropped CB bars on a two-mark span
  - a member inside a slab hole deducted twice
  - blinding overlaps counted twice
- 33 / 33 checks now pass.

**OCR review**
- The second reading agrees with all 14 accepted OCR records. Nothing was promoted.

## What is not working / not done

**Bars the drawing does not give**
- The CB schedule prints no top-through bars, and four support-top cells are blank. 24 CB pieces stay PARTIAL_MISSING.
- Ground-beam links are missing for 31 bands:
  - EV-0007 was rejected by OCR; it reads Ø8/15cm visually, but a person must confirm.
  - The < 2.5 m class prints no links.

**Exterior ground beams**
- 13 bands carry a wall but sit at the annex / court level (+0.30 / +0.15).
- From that level the exterior detail is not deeper than the class section, so the class section is used and the case is flagged.
- The inside level is the nearest printed level inside, within 8 m. This is a heuristic.

**Lintels and stairs**
- 46 of the 57 openings sit under a beam. Whether a lintel exists depends on the head height against the beam soffit, which the plans do not show.
- Both stair zones hold part of a stair: risers 0.221 and 0.111 m, outside 0.14–0.20. They keep the slab-zone exposure.

**Where M4 is worse**
- The base is more conservative. Held spans leave the base: the beam MAE on clean synthetic drawings rises from 0.22 % to 6.1 %, while the planning envelope still contains the truth on 39 / 40.

**Not compared and not evaluated**
- Arc-bounded slab faces (65 m²) are not compared by the independent check, because the stored ring is a chord polygon.
- The exterior-GB rule and the lintel census have no synthetic held-out set yet. Their tests are hand-made fixtures.

## Recommended next steps (in order)

1. **Person review loop.** Build a fill-in sheet that turns a reviewed OCR record or RFI answer into `MANUALLY_CONFIRMED` (who, when). Then rerun.
   - EV-0007 alone lifts the links of 18 bands.
   - RFI-M4-01 lifts the top bars of 24 CB pieces.
2. **Answer RFI-M4-03.** It covers 10 unlabelled spans: 5.2 m³ if the neighbour's section is confirmed.
3. **Answer RFI-M4-06.** It covers the exterior ground beams at the annex / court levels. Then the 13 conflict cases resolve one way or the other.
4. **Synthetic held-out for architectural rules.** Extend the generator with an architectural plan (walls, openings, levels), so the exterior-GB and lintel rules get scored on unseen drawings.
5. **Section views.** Head heights and the stair waist come from the architectural sections. A section reader would settle lintel need and stairs.
