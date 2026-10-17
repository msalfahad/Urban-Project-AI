# S9A: structural completeness, cantilever bands and visual QA

Baseline HEAD `5f317d2`. Date 2026-10-10. State: `DATED_CORRECTION_LAYER` (`18_S9A_CORRECTION_MANIFEST.json`).

S9A is a correction layer over S9 (`research/alsenan_structural_s9`, frozen, unchanged). It re-checks S9, finds the eight hatched bands, compares the two beam-depth readings and audits the ground-beam and column conflicts. S9 and the 29 stage freezes verify unchanged before and after the build.

**Nothing is released.** The released baseline stays **158.070 m3 concrete** and **18,845.961 kg reinforcement**: a partial structural BOQ, not a complete building estimate. S9A changes owners and lanes only, each with a reason (`10`). The production BOQ is not touched, and the project gate stays INCOMPLETE.

## Conclusions

1. **S9's totals hold.** Every released family was recomputed from the stages' own row registers: 21 of 21 agree to rounding (largest difference below one millionth). The 0.001 kg difference is only the S9 README table, whose 3-dp family values add up to 0.001 kg more than the unrounded total.
2. **The inventory is consistent.** 560 records, one lane each, mutually exclusive. There are 110 deltas summing to the published release, and S9-C01 holds 1,217.128 kg in 288 parts. The 98.994 m3 conditional point sits on no released row.
3. **The eight bands are cantilever portions, not new structure.** There are 8 regions with 4.947 m2 in plan. All match the legend's cantilever-portion hatch on the plotted PDF.
   - 7 were S9 untagged beam spans. They are re-owned as cantilever portions and remain blocked, because no thickness is printed.
   - One is the hatch of the tagged beam CA, which keeps it.
   - No band overlaps a panel or a column, so there is no double count.
4. **Beam concrete depends on one answer.** 103 beams have a full section and clear length. They total 56.767 m3 if H is the overall depth, or 70.932 m3 if H is below the slab: 14.165 m3 (24.95 %) apart. Neither reading is chosen.
   - Panels stop at beam faces (243 of 243 edges), so the slab strip over a beam is counted once under either reading.
   - Corner squares where two beams meet without a column are counted nowhere: an undercount of at most 0.454 m3.
5. **Interpretation is separated from missing information.**
   - Columns: 19 of the 28 section mismatches match another schedule row or type (interpretation). 9 match nothing (conflict). The four lift-pit columns stay a conflict: drawn 200 / 250 mm against a scheduled 300 mm.
   - Ground beams: 18 spans are interpretation questions (title overlap, c/c or clear length, exterior or interior). 30 lack source information (the exterior depth is 'FOLLOW ARCH.').
   - Column ties: no bend radius, hook or closure is printed anywhere (missing source information).

## What the engineer can unlock

These are conditional quantities each answer would make releasable, never a promise of release (`14`).

| Rank | RFI | Question | Concrete m3 | Reinforcement kg |
|---|---|---|---|---|
| 1 | RFI-A01 | Is the beam schedule depth H the overall depth including the slab, or the depth below the slab? | 56.767 - 70.932 | 0.000 |
| 2 | RFI-A05 | p.13 ground-beam sections: are the titles '< 2.5 m' / '< 5 m' exclusive bands, which length selects the class (centre-to-centre or clear), and what are the exterior 'FOLLOW ARCH.' depths? | 2.058 - 18.356 | 0.000 |
| 3 | RFI-A03 | Founding level of the footings (only 'excavation >= 1.50 m below plot level' is printed) | 14.162 | - |
| 4 | RFI-A04 | For the 28 column occurrences whose drawn section differs from the schedule (22 in GF - 2F, 6 foundation necks including the 4 lift columns drawn 200 / 250 vs 300 at the pit), which governs? | 10.650 - 13.480 | 0.000 |
| 5 | RFI-A06 | Scope of the 'T=10cm, 5Ø10/m E.W.' ground-slab note beyond the two source-zoned cells, and its cover | 12.978 | 0.000 |
| 6 (steel 2) | RFI-A07 | Lintel bearings, column connections and head functions for the lintels S8.6A blocked | 4.611 | 522.091 |
| 7 | RFI-A08 | Thickness (and section) of the 8 cantilever portions hatched on the slab sheets (legend 'Cantilever portion'), and their bars | 0.736 | 0.000 |
| 8 | RFI-A10 | Which beam owns the corner square where two beams meet without a column? | 0.000 - 0.454 | 0.000 |
| - (steel 1) | RFI-A02 | Column ties and beam links: bend radius, hook length and closure (none is printed; S9-C01 and D1.1 hold the tie and link paths conditional) | 0.000 | 2,616.648 |
| - | RFI-A09 | Section of the 25 untagged beam spans that are not cantilever portions (no tag binds them, no schedule row) | - | 0.000 |

**The single largest unlock is RFI-A01, the beam depth convention.** One answer makes 56.767 - 70.932 m3 of beam concrete releasable. The largest steel unlock is RFI-A02, the tie and link bend radius and hooks: 2,616.648 kg.

## Files

| File | What it holds |
|---|---|
| `01_S9_TOTALS_VERIFICATION.csv` | Each released family: published, row sum, independent recompute |
| `02_S9_INVENTORY_VERIFICATION.csv` | V01 - V07: inventory, lanes, deltas, S9-C01, conditional leakage |
| `03_BAND_CORRECTION_REGISTER.csv` | The 8 bands: handle, sheet, polygon, size, legend match, overlaps, owner, states |
| `04_BAND_EVIDENCE.json` | Hatch population, PDF legend spacings, per-band evidence |
| `05_BEAM_CONVENTION_COMPARISON.csv` | 150 beams: B / H / L sources, t, volumes under each reading |
| `06_BEAM_CONVENTION_TOTALS.csv` | Totals by storey and set |
| `07_BEAM_SLAB_COLUMN_OVERLAP_AUDIT.csv` | BO-01 - BO-05 |
| `08_GROUND_BEAM_AUDIT.csv` | 62 ground and strap beams: c/c vs clear class, title overlap, exterior depth |
| `09_COLUMN_AUDIT.csv` | The 28 section mismatches, interpretation vs conflict; lift columns |
| `10_S9A_DELTA_REGISTER.csv` | 15 owner / lane changes, all 0 m3 / 0 kg |
| `11_CONCRETE_AND_STEEL_RECONCILIATION.csv` | Released (unchanged) and conditional ranges by family |
| `12_STRUCTURAL_COMPLETENESS_REPORT.md` | The updated completeness report |
| `13_ENGINEER_RFI_REGISTER.csv` / `14_UNLOCK_RANKING.csv` | 10 RFIs with problem type and unlock values |
| `15_CONSERVATION_CHECKS.csv` | C01 - C17 |
| `16_S9A_SUMMARY.json`, `17_PROVENANCE.jsonl`, `18_S9A_CORRECTION_MANIFEST.json` | Summary, provenance, manifest |
| `visual/S9A_VISUAL_QA.html` | The visual QA package (10 items) as one page; print to PDF with `make_pdf_s9a.py` |
| `visual/*.svg` | Each figure on its own, labelled SOURCE-DERIVED, SCHEMATIC or CONDITIONAL |

Rebuild: `python3 -I research/alsenan_structural_s9a/build_s9a.py` (byte-identical). The PDF (`visual/S9A_VISUAL_QA.pdf`) is printed from the HTML and git-ignored, like the other review PDFs.

## Notes for the reviewer

**What worked**

- The independent recompute matches S9 to rounding in every family.
- The bands were found and classified from the drawing alone:
  - DXF hatch pattern and scale;
  - the plotted spacing read from the PDF vector paths;
  - the legend boxes on the same pages.
- Every slab-panel edge S1 marks as beam-supported lies on a drawn beam or column face. This is what makes the two beam readings safe from slab double counting.

**What did not work, or stays open**

- No source states the beam depth convention, the band thickness, the founding level, the tie hooks or the exterior ground-beam depth. These stay blocked or conditional.
- Ground-beam spans could not be placed on the plan span by span: the registers hold edge lines, not span ends.
- Untagged beam spans have no tag, so they have no marker on the maps.

**Recommended next step**

- Send RFI-A01, A02, A03 and A04 to the engineer first. Together they cover most of the unreleased concrete and steel.
- Release nothing until the answers come back. Then apply them as a separately approved release on top of S9 / S9A.
- Do not start S10 until that review.

