# S8.7B staircase owner scenario and engineering reconciliation

Round S8_7B, baseline `303df68`, engine `303df68+code:f766bafc50a50887`. A research scenario layer over the frozen S8.7
package and the S8.7A correction layer; both are unchanged and verified. **Release delta: 0 m3 concrete and 0 kg
reinforcement.** S8.7's frozen release (0.516582788 m3,
59.020862261 kg) is untouched. A zero delta means nothing more is released here, not that
the stairs contain no concrete or steel. Passing tests prove the arithmetic and the reading, not engineering approval.

## The owner's provisional scenario

| Parameter | Owner scenario | Status |
|---|---|---|
| Main stair, GF -> 1F | 28 risers | PROVISIONAL_OWNER_SCENARIO |
| Main stair, 1F -> 2F | 27 risers | PROVISIONAL_OWNER_SCENARIO |
| Structural stair waist | UNKNOWN | REQUIRES_ENGINEER_CONFIRMATION |
| Marble / stair finish | 30 mm (bedding not stated, never assumed inside it) | PROVISIONAL_OWNER_SCENARIO |

The round (light-well) stair is evaluated on its own drawn 28-riser arrangement; the owner's decisions are not read
as an approval of it.

## Findings

1. **GF -> 1F, 28 risers: PROVISIONAL_SCENARIO_WITH_CONFLICT.**
   - The finished riser is 4500 / 28 = 160.714285714 mm, 0.714 mm above the preferred 160 mm maximum. This is a
     tolerance decision for the owner, not an automatic approval.
   - **Landing.** The half-landing is printed at +3.50: section A-A dimensions it '320' above the +0.30 lobby
     floor, and its level line measures +3.505.
     - With 28 equal risers that level falls between riser 15 (+3.411) and riser 16 (+3.571).
     - The only drawn 28-riser allocation (the structural GF roof sheet: 12 + 4 + 12) lands at
       +3.571, 71.4 mm above the
       printed level.
     - Keeping +3.50 with that allocation would need unequal risers of 156.25 and 166.667 mm.
     - With equal risers only 27 or 36
       risers reach +3.50 (166.667 / 125 mm); none lies in the 150 - 160 mm band.
   - **B20.** On the structural sheet the 12th upper riser (y 16111.9) is
     200 mm inside head beam B20, so the top tread sits over the beam at
     the 1F floor. The overlap zone is 0.054 - 0.067 m3 (150 - 200 mm waist)
     and is reported apart. Nothing is resolved here: no flight is shortened and no beam is moved. The
     architectural plan's 11-riser upper flight stops 100 mm clear of B20.
   - **Foot.** The structural sheet starts the lower flight 600 mm (two goings) south of the architectural and
     ground-beam plans, and no ground beam is drawn under either foot.
   - **Section A-A (measured this round).** The section draws a third arrangement: 15 +
     12 = 27 equal risers of 166.667 mm, which reaches +3.50
     exactly.
2. **1F -> 2F, 27 risers: PROVISIONAL_SCENARIO_WITH_CONFLICT.**
   - The finished riser is 155.555555556 mm, inside the preference.
   - **Winders.** 27 needs the architectural 1F plan's four-riser winder turn (3 radial + closing). The structural
     1F roof sheet and the 2F plan draw that quarter flat (24 risers of 175 mm).
   - **B23.** The 11-riser upper flight stops 100 mm clear of head beam
     B23, with the S8.7 arrival strip A2-T1 between them. This is compatible.
   - **Landing.** No level is printed. 27 risers put it at +7.989; section A-A scales to
     +7.687 and draws 13 + 12 = 25 risers of 168 mm. Its
     12-riser upper flight would end inside B23.
   - **Foot.** The foot bears on B20 at the 1F floor. This is a support interface; its zone is reported apart.
3. **Round (light-well) stair, 28 risers: independently drawn, not owner-approved.**
   - The GF roof sheet and the architectural 1F plan agree: 12 curved + 11 straight, then a corner landing, then 5
     (160.714 mm). The architectural GF plan's second view draws one riser fewer.
   - No section cuts this stair. Its foot level is not printed inside the light well; its corner landing is not
     printed (+4.696 with equal risers); its 1F arrival '+5.50' is printed.
   - Beam CA crosses the straight part at an unstated level; its zone is deducted from NET.
4. **Landing levels.**
   - Established: GF -> 1F +3.50 (printed).
   - Inferred, not printed: 1F -> 2F (+7.989 under 27; section scale +7.69) and the round-stair corner landing
     (+4.696).
   - The +0.30 lobby under the GF -> 1F landing is printed on the GF plan and on the section.
5. **What the 30 mm finish changes.**
   - No finished level or finished riser moves. Every concrete tread lies the full tread build-up (marble + bedding)
     below its finished tread.
   - The first concrete riser is h + f_b - s and the last h - f_t + s (f = floor build-up, s = stair build-up);
     every other riser is h. Finished risers stay equal while the first and last concrete risers differ.
   - With s = 30 and f = 50 (illustrative) they are 180.714 /
     140.714 mm. With bedding 20 (s = 50) and f = 80 they are
     190.714 / 130.714 mm. With f = s every
     concrete riser equals h.
   - A 200 / 100 pair would need 69.29 / 90.71
     mm floor build-ups (s = 30). Nothing prints them, so the pair is not used.
   - Two drawn offsets exist but are indications only: section A-A draws a finish line about
     51 mm above the structural treads, and p.16's typical detail shows 50 mm
     head and foot offsets.
6. **Concrete sensitivity by waist** (research only, never released; m3, GROSS / NET; NET excludes the beam overlap
   zones and column cut-outs; the S8.7 plates are excluded):

   | Stair | 150 | 160 | 175 | 200 |
   |---|---|---|---|---|
   | main stair GF -> 1F (OWNER-28) | 2.364 / 2.305 | 2.472 / 2.409 | 2.632 / 2.565 | 2.9 / 2.825 |
   | main stair 1F -> 2F (OWNER-27) | 2.456 / 2.398 | 2.572 / 2.513 | 2.748 / 2.684 | 3.04 / 2.97 |
   | round (light-well) stair GF -> 1F (drawn 28) | 2.439 / 2.342 | 2.553 / 2.453 | 2.726 / 2.618 | 3.013 / 2.895 |
   | steps on grade | 1.147 / 1.121 | 1.198 / 1.17 | 1.275 / 1.245 | 1.403 / 1.368 |
   | ALL | 8.406 / 8.166 | 8.796 / 8.544 | 9.381 / 9.112 | 10.355 / 10.059 |

   Flights use an exact section integral between plumb cuts. Winders and the curved flight are plane-equivalent
   approximations; `08` gives a flat-soffit upper bound for the winders and solid-step readings for the steps on
   grade.
7. **Reinforcement.**
   - Only 8Ø16/m is project-specific: nine plan callouts, read again and equal to S8.7's bindings.
   - S8.7's 59.020862261 kg over the three plates and S7's 75 stair-side top extensions
     (71.895327413 kg) are preserved and not counted again.
   - Blocked: 6Ø14/m, 6Ø12/m, Ø12/20cm, Ø8/15, 1Ø12, 6Ø16/m, 2Ø12 / 4Ø16 (20 x 40), 3Ø14 / 4Ø16 / 2Ø14/30 / Ø8/15, anchorage / development / laps / bends.
   - The 8Ø16/m main-bar sensitivity along the straight flights (290.515 kg)
     is never released.
   - The p.16 cranked stair beam is not assumed to exist anywhere. The 'With Stair' beams stay with S6.
8. **Engineer decisions needed** (`10`, Q-ST7B-01..14):
   - which of +3.50 / 28 risers governs on GF -> 1F;
   - B20 under the GF -> 1F top tread;
   - the GF -> 1F foot and its support;
   - the 0.714 mm tolerance;
   - the 1F -> 2F winders and landing level;
   - the waist and landing thickness;
   - marble bedding and floor build-ups;
   - the typical bars, anchorage and laps;
   - the 'With Stair' beams;
   - the round stair's levels, width, soffit and beam CA;
   - the winder soffit form;
   - the steps on grade.

## Files

- `01` owner scenario and assumption register
- `02` riser calculation table
- `03` riser-by-riser setting-out schedule (exact levels and 1 mm site levels)
- `04` landing and elevation reconciliation
- `05` structural / architectural conflict matrix
- `06` beam interference audit
- `07` first / last risers and finish build-ups
- `08` waist-thickness concrete sensitivity
- `09` reinforcement and ownership audit
- `10` engineer RFI register
- `11` conservation and no-double-count checks
- `12` plan riser line evidence
- `13` section A-A, plan level texts and the p.16 visual record
- `14` release summary
- `15` provenance
- `16` freeze manifest
