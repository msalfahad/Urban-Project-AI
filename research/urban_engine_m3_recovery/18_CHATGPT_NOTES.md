# Notes for ChatGPT: what worked, what is not working, what to do next

**Context**
- M3 ("real-drawing recovery and BOQ completeness") on branch `claude/access-permissions-setup-ii24ws`.
- Planning estimate only, no prices; the gate stays INCOMPLETE.
- Figures come from `01_FINAL_REPORT.md` and the CSVs it cites.

## What worked

1. **Footings are now complete on ST7757.**
   - Every footing label is quantified once: 25 confirmed, 0 without an outline (M2: 22 and 4).
   - Footing concrete went from 50.04 to 66.26 m³ and equals the frozen M1 replay.
   - The recovered pieces: FF and FN (type marks without a number), one outline from its layer template, and one two-label footing (quantified once).
2. **Necks and storey presence.**
   - 28 necks are measured from printed levels (10.86 m³, 1 429 kg).
   - 13 column occurrences on storeys where the roof plan shows none are no longer counted (−5.88 m³).
3. **Ground beams have steel.** M2 had 0 kg.
   - The typical bars come from the p.13 PDF details. The page's text is vector glyphs, so it went through a local OCR adapter with a vector-glyph check.
   - 4 918 kg is PROVISIONAL / LOW / OCR-derived and unreviewed.
   - The roles the details do not show are UNRESOLVED and counted as PARTIAL_MISSING, never 0 kg.
4. **The OCR adapter refuses to guess.**
   - Four reads per token plus a page-wide glyph-shape vote settled the 3 / 5 confusion (`5016` vs `3Ø16`).
   - The one read it could not settle (EV-0007) is rejected and kept.
   - Every record has page, region, raw text, confidence and a crop; owner text is redacted before recording.
   - A manual-transcription schema is the fallback.
5. **Beam recovery.**
   - CB11 (2.85 m³), dropped whole by M2 because of a 10 mm intervening stub, is recovered.
   - So are B27, B1 and CB5 and CB8's third span.
   - TAG_UNBOUND 7 → 1; unbound bands 15 → 13.
6. **Slabs.**
   - Every face has a region class.
   - The two stair zones (from tread lines) and a 49 m² ground-slab cell with a free-standing column are held out as UNRESOLVED instead of being counted as slab.
7. **Completeness is visible.**
   - Every concrete component has one reinforcement state.
   - 110 components with missing steel are counted by family and storey in BOQ section D, the workbook and the PDF.
   - Every family outside the core six has a coverage state and names the input it needs. NO_EVIDENCE_FOUND reads "confirm absent".
8. **Generalisation holds on unseen drawings.**
   - On 40 new synthetic villas (seeds 501–540), M3 equals M2 on the clean and drafting-noise sets: beam recall 0.9975, MAE 0.40 %.
   - On the M3-defect set (157 stubs, 40 label-only footings), M2 drops to recall 0.896, beam MAE 11.8 % and footings 8.0 %. M3 holds 0.9975, 0.43 % and 0.
9. **Runtime and determinism.**
   - One CLI command, about 4.1 s compute cold and 2.9 s warm (intake cache).
   - Each convention change re-prices from the detected model.
   - The before/after tables come from live runs of both engines in separate processes.

## What is not working (or not proven)

1. **No independent truth on a real villa.**
   - The only real-drawing comparisons are the M2 run and our own frozen M1 replay. The M3 rules were written from ST7757's failures, so ST7757 is not a test set.
   - Accuracy on a real unseen villa is unknown; the 95 % target is not demonstrated.
2. **The beam total is above the frozen replay** (+6.18 m³):
   - mostly spans given to the collinear mark across a support (an inheritance convention, 11 items, 5.98 m³);
   - plus length and width readings on 6 marks.
   - Whether inheritance is right is an engineering question, not something the drawing proves.
3. **The ground-beam total depends on an assumption.**
   - The exterior detail is applied to every band with an outside side: +9.90 m³ against the typical class section. The frozen replay used fewer exterior candidates.
4. **Blinding** (26.41 m³) rests on one OCR-read note ("10cm Plain con."), not yet reviewed.
5. **Steel gaps are counted, not filled.**
   - 82 components are MISSING_DATA, chiefly:
     - continuous-beam bars whose span order is not mapped (25);
     - slab panels with no bar tag (25);
     - beam bands without a section (14).
   - 28 ground beams are PARTIAL_MISSING (links).
6. **Still unresolved on concrete:** 30 items, exposure 13.5–21.9 m³ (13 unbound bands, 8 necks, 5 CN columns, 2 stair zones, 1 multiple-mark band, 1 free-column cell).
7. **Six families are detected but not quantified** (lintels, pool, stairs, domes, water tank, parapets). Two have no evidence (lift, walls). The frozen replay quantifies most of them from its stage registers; the generic route does not.
8. **The synthetic generator draws one drafting convention.** Real sets may fail in ways it never draws.

## What I recommend next

1. **Get independent ground truth for one or two real villas.** A QS takeoff we did not tune against, frozen before comparison, is the only way to measure real accuracy.
2. **Have a person review the 14 OCR records and the blinding note** (about 30 minutes with the crops).
   - Each confirmed record removes the OCR blocker.
   - Send the 13 RFIs in `19_RFIS.csv`. The highest value are RFI-05 (exterior ground beams), RFI-07 (short-class links), RFI-12 (span order) and RFI-01 (the 49 m² cell).
3. **Map the span order of continuous beams** (the schedule's span 1..n against the drawn line order). It would fill 25 MISSING_DATA beam components generically.
4. **Add stair quantities from the stair section.** The zones are already found and excluded from the slabs.
   - Then add lintels from the architectural opening widths; the S8.6 census already exists.
5. **Extend the synthetic generator:**
   - with the new real-drawing failure patterns as they appear (each new real bug becomes a generator defect and a held-out score);
   - with a second drafting convention (layer names, label placement), so generalisation is tested beyond one style.
6. **Keep the firewall.** Freeze before any external comparison, and give external estimates as positions only. Never tune to them.
