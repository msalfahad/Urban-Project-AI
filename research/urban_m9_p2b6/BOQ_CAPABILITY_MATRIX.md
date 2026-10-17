# BOQ capability matrix (Phase 2B-6, Part 13)

This covers the whole villa BOQ, not only finishes and waterproofing.

**Evidence states.**

| state | meaning |
|---|---|
| VERIFIED | against independent truth |
| WORKS | behaves as designed, limits stated |
| PARTIAL | some families only |
| ABSENT | no measured item |

**Line states on the reference plan.** "Reference-plan lines" counts V2.6 Mode A line states on the private plan
(511 lines in total, aggregates only). The labels used in the matrix:

| label in the matrix | engine evidence state |
|---|---|
| measured | SOURCE_DERIVED |
| provisional | PROVISIONAL |
| bounded | BOUNDED_EXPOSURE |
| blocked | BLOCKED_RFI |

**Structural evidence.** Structural rows rest on route G / V6 and the S-stage packages (`research/urban_engine_m8_full_scope/`).

## Matrix

| capability | current implementation | accuracy evidence | coverage | major limitations | dependencies | engineering risk | recommended next action |
|---|---|---|---|---|---|---|---|
| **Architectural geometry** (intake, regions, walls, topology) | K2 intake (ezdxf): blocks, OCS, MINSERT, bulges, text, DIMENSION; band census; arrangement topology; robust geometry (V2.1) | benchmark exact on straight walls; translate / rot90 / mirror / metres / reorder / rename invariant tonight | DXF; DWG through a converter; XREF refused | curved wall bands missing (D-D2b); a turned sheet frame is refused; whole plan in a block holds the doors (D-P6-05) | ezdxf | low | curved bands (Exp. B2) in the next method |
| **Room understanding** (spaces, labels, wet / dry, attachments) | lexicon (Arabic, SHX), room tags, fixtures, zones, stacked shafts, voids | Stage C: floor, ceiling and perimeter exact in 5 / 5 real rooms | 38 rooms on the reference plan | layer roles from counts (D-D1, D-P6-02 / 03 / 04 / 08); basin-only space typed wet (D-P6-07); a doorless cell takes wet scope silently (D-C3) | - | **high**: role errors are silent without the run audit | the run audit on every run now; geometry signatures (Exp. C) + the basin rule (Exp. G) in the next method |
| **Openings** (doors, windows, passages, door classes) | band gaps, swings, leaf closures, door model (PVC / aluminium / main / lift excluded), feasibility (owner nominal + 0.10 m), held doors | Stage C windows exact; doors exact except the held one (D-P6-01) | doors 16 measured; windows 26 counted, their reveals 26 blocked | held door takes its wall gap (D-P6-01); leaf-closed thresholds withheld (D-C2); window reveals blocked (no sill / head evidence); aluminium windows only counted (no area / glazing items) | - | medium | the jamb-span rule (Exp. A); window area and glazing items from width x height when heights are read |
| **Finishes** (floor, wall porcelain, plaster, paint, skirting, ceilings, thresholds) | owner finish scope (knowledge 1.1.0), surface ledger, deductions, attached areas | Stage C: 66 checks, 8 failing (both causes found and fixed in experiments: 0 failing); curved boundaries exact | floors 49 measured / provisional; plaster 36 of 52; paint 6 of 30; skirting 28 of 49; wall tile 10 of 17 | every wall-area line rests on heights (synthetic, D-C5); paint largely blocked (scope / heights); no decorative-ceiling or hidden-skirting items | project heights | medium | read heights from sections / schedules (Part 4); then paint and decorative ceilings |
| **Waterproofing** (floor, upturn, doorway, transition, terminations, penetrations, membrane layout, construction layer) | V2.4 - V2.6: net / installed / procurement, piece plan, junction alternatives | 297 / 297 independent checks on 10 worked examples; Stage C | floor / upturn / doorway measured in 17 areas; penetrations 17 blocked; terminations bounded | procurement PROVISIONAL (junction detail D-01); layouts on the chord for arc rooms (D-D2a); a basin lobby takes wet scope (D-P6-07); zero-length termination sliver (D-P6-06) | - | low | **stop optimising** until the owner's junction detail (D-01); fix D-P6-07 with the room types |
| **Stairs** (architectural treads, risers, landings, railings; structural flights) | tread-family detection, riser schedules, landings; structural stairs (route G V6, S8.7 series) | S8.7A-C stair stages (owner-reviewed riser counts); M8: one stair within 0.73 % where printed | treads 11 provisional, 3 bounded; risers 14 blocked; flights 14 blocked; railings 14 blocked | risers and flights need heights; curved / winder flights partly; railing lengths not measured | heights | medium | heights from sections unblock risers / flights; railing length from the stair edges |
| **Roofs and balconies** | exterior spaces get waterproofing under the default scope (UP-WP-ROOF-001); domes (structural) | M8 domes measured where drawn | 1 exterior space on the plan | no roof-finish items (tiles, screed, insulation), no parapet finishes, no roof drainage | roof plan reading | medium | roof finish items from the roof plan region (the exterior faces already exist) |
| **External works** (interlock paving, boundary walls, landscaping) | boundary walls (structural, M8); garden / yard words in the lexicon | M8 boundary walls measured where drawn | - | **no interlock paving or external finish items**; the site plan is not a region | site plan region | medium | site-plan region + paving areas (same topology) |
| **Structural concrete** (excavation, blinding, footings, necks, ground beams, slabs, columns, beams, stairs, lintels, domes, pool, tank, lift, walls, parapets) | route G V6 + the S-stage packages: measured or bounded families, conventions with low / base / high, ownership / conservation | M8: printed dimensions within 0.73 % (max); held-out villas 80 / 80 run with no unranged finding; total RC within 6 % of a freelance QS (agreement, not accuracy) | 14 families measured or bounded | not engineer-released; no blind second project; **no excavation item** (blinding only) | structural drawings and schedules | medium | excavation and backfill from footing geometry + levels; an independent volume check (Manifold, test tree) |
| **Formwork** | **ABSENT**: trades listed, no measured item | - | - | - | member geometry (exists) | low to build, medium to verify | contact areas from the existing member geometry (sides, soffits, junction deductions), verified by solid booleans in the test tree |
| **Reinforcement** | schedule- and notation-based modules (footings, columns, ground system, beams, slabs, stairs, lintels, special columns), completeness registers, sanity variance | S3 - S9 stage reports (owner-reviewed bar lists); the 89-component completeness register | from schedules and bar notes, never kg / m3 ratios | rebar for some M8 families not measured (W8-09); depends on schedules being present | schedules | medium | the missing families; bar-by-bar provenance in the BOQ export |
| **Drawing revision control** | revision-set hash per line, drawing SHA-256, project manifest (M7.F), review-decision invalidation, freeze verifier | freeze verifier 0 differing; byte identity 968 + 272 files | every run | no revision **label** (only the content hash); no drawing-to-drawing change report | - | low | a revision delta report (lines added / changed / removed between two runs) |
| **BOQ exports** | BOQ_LINES (CSV / JSON), the room workbook (xlsx), scenarios, ledgers; the M1 contractor workbook / PDF (structural) | schema tests | architectural + structural (separate routes) | no single combined villa BOQ export across routes; no IFC cost schedule | openpyxl | low | a combined export (architectural + structural) with line provenance; IFC later if wanted |
| **QA and provenance** | per-line rule / formula / inputs / evidence state; run rules; rules sheet; the run audit (tonight); as-found defect tests | Experiment E: door symbols resolve to DXF handles | every line | faces and walls do not list their source entities (Exp. E) | - | low | `source_entities` per line (topology ids already carry them) |

## Prioritisation (Part 13)

Score = expected improvement in real-world BOQ correctness x frequency x importance to the full BOQ, against
implementation risk and cost.

- Improvement and importance: 1 - 3.
- Frequency: how often a villa drawing hits the case, 1 - 3.
- Risk / cost: 1 (low) - 3 (high).

| work | improvement | frequency | importance | risk / cost | score | rank |
|---|---|---|---|---|---|---|
| layer-role understanding: geometry signatures + run audit (D-D1, D-P6-02 / 04 / 08) | 3 | 3 (partial sheets, exploded symbols, turned wings) | 3 (rooms → every finish) | 1 | **27** | 1 |
| heights from sections / schedules (D-C5) | 3 | 3 (every villa) | 3 (every wall line, stairs) | 2 | **13.5** | 2 |
| the held door's width (D-P6-01) + leaf-closed thresholds (D-C2) | 2 | 2 | 2 | 1 | 8 | 4 |
| room types: the basin rule (D-P6-07) + doorless cells (D-C3) | 2 | 2 | 2 | 1 | 8 | 4 |
| formwork from member geometry | 3 | 3 | 3 | 3 | 9 | 3 |
| excavation / backfill | 2 | 3 | 2 | 2 | 6 | 6 |
| windows (area, glazing, reveals) | 2 | 3 | 2 | 2 | 6 | 6 |
| roof, balcony and external-works finishes, interlock paving | 2 | 3 | 2 | 2 | 6 | 6 |
| curved walls (D-D2a / b) | 1 | 1 (4 of 38 rooms; +0.88 % run) | 1 | 1 | 1 | 10 |
| waterproofing procurement | 1 | 3 | 1 | 1 (blocked on D-01) | 3 | 9 |

The ranks feed `PRIORITIZED_ROADMAP.md`. Waterproofing and the single doorway rank low. They are understood, and
their remaining exposure is small next to the role, height and scope gaps.
