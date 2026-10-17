# S8.7A stair riser, finishing and structural-geometry correction audit

Round S8_7A, baseline `15730e0`, engine `15730e0+code:fc5d044f8894710b`. A dated correction layer over the frozen S8.7
package (`15_S8_7A_CORRECTION_MANIFEST.json`, `references_read: []`). S8.7 is unchanged and its release stands. Nothing new is
released; the owner decides before any production BOQ change.

## Conclusions

1. **The disagreement is not a counting error.** The recount, done again from the DXFs without the S8.7 builder,
   reproduces S8.7's counts. The method:
   - each architectural nosing line and the hidden riser face behind it are one riser;
   - the three landing-edge lines are real risers: flight 1's last riser, the closing riser of the turn, and flight
     2's first riser;
   - the ground-beam plan and the 2F plan are repeated views.

   The drawings themselves disagree:

   | GF -> 1F (4.50 m) | flight 1 + turn + flight 2 | riser |
   |---|---|---|
   | structural GF roof sheet | 12 + 4 + 12 = **28** | 160.714 mm |
   | architectural GF plan | 10 + 4 + 11 = **25** | 180 mm |
   | section A-A (upper flight) | 12 | - |

   | 1F -> 2F (4.20 m) | flight 1 + turn + flight 2 | riser |
   |---|---|---|
   | architectural 1F plan | 12 + 4 + 11 = **27** | 155.556 mm |
   | structural 1F roof sheet | 12 + 1 + 11 = **24** | 175 mm |
   | architectural 2F plan (repeated view) | 12 + 1 + 11 = **24** | 175 mm |
   | section A-A (upper flight) | 12 | - |

   The turn is three radial winder risers plus the closing riser into the landing. The structural 1F roof sheet and
   the 2F plan omit the radial winder lines.
2. **Owner scenario A is a complete drawn arrangement for each storey.** GF -> 1F 28 is the structural GF roof sheet
   (160.714 mm); 1F -> 2F 27 is the architectural 1F plan (155.556 mm). They are proposed for confirmation, not
   selected. Owner scenario B (29 / 26) is not drawn anywhere.

   Against the owner's 150 - 160 mm preference:
   - 28 risers give 160.714 mm, 0.714 mm over the range; 29 (155.172) and 30 fit.
   - For 1F -> 2F, 27 (155.556) and 28 (150.0) fit; 26 gives 161.538 mm.
3. **Physical checks.**
   - The structural sheet's 12th upper-flight riser (y 16112) lies inside the 400 mm head beam B20. The architectural
     plans end both upper flights at y 16412, 100 mm short of the head beam, and section A-A's 12th riser in the
     1F -> 2F upper flight would also fall inside its head beam.
   - With 28 uniform risers the GF -> 1F half-landing is at +3.571. Section A-A gives +3.50.
4. **The round (light-well) stair is consistent.** It has 28 risers on both primary views (12 curved + 11 straight,
   the corner landing, then 5): 160.714 mm, with the corner landing at +4.696 if the risers are uniform.
5. **First and last risers.** Uniform finished risers give a first concrete riser of h + f_b - s, a last of
   h - f_t + s, and every other riser h. The floor build-up is not printed, so `04` evaluates a grid. A worked example
   for GF -> 1F with 28 risers and 30 mm marble:
   - with 50 mm floor build-up, the first concrete riser is 180.714 mm and the last 140.714 mm;
   - with 30 mm (equal to the marble), every concrete riser is 160.714 mm.

   A 200 / 100 pair would need 69.3 mm of floor build-up at the bottom and 90.7 mm at the top. No drawing gives
   those, so the pair is not imposed.
6. **Waist.** It is not established (p.16 'THICK' carries no value). The 'T 16' tags are zone tags lying in the
   winder quarter and on the light-well flight. 160 mm stays a sensitivity.
7. **Bars.** Only 8Ø16/m is explicitly assigned on the project plans. Every other p.16 family is typical only and
   blocked, as are anchorage and laps.
8. **S8.7 release.** 0.516582788 m3 and 59.020862261 kg are reproduced
   exactly from the drawings. No double count was found. Two latent overlaps are recorded for any future flight
   release: A1-F2 over beam B20, and C-F1 over beam CA.

## Scenario concrete not yet released (waist 160 sensitivity; S8.7 plates excluded; never released here)

- A1-ARCH_GF-25: 2.328899 m3
- A1-OWNER_A-28: 2.485061 m3
- A2-FFRS-24: 2.532258 m3
- A2-OWNER_A-27: 2.585191 m3
- C-DRAWN-28: 2.689264 m3

## Files

`01` comparison, `02` line evidence, `03` riser schedule, `04` first / last risers, `05` waist and landings, `06`
concrete, `07` bars, `08` beams and S6 / S7, `09` conflicts, `10` questions, `11` reproduction and corrections, `12`
release summary.
