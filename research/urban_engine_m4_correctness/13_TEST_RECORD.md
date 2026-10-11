# Test record (M4)

## M4 tests (`tests/m4_correctness/`)

| File | Tests | What they prove |
|---|---|---|
| `test_m4_continuous_beams.py` | 6 | Printed spans and roles; a span takes a mark only through the printed sequence (forward, hand-derived 1.008 m3); a simple beam's unlabelled span is never inherited (exposure 0.46 m3); count conflict and reversed reading; physical bar lengths by hand (bottom 4.79 m, support top 2.45 m); mass conserved, including a mapped span with two marks whose bars are held as exposure |
| `test_m4_exterior_gb.py` | 6 | Architectural registration (shift recovered), wall classes (exterior / interior / perimeter without wall), inside level; exterior depth only where a wall is evidenced; level conflict keeps the class section; without the architectural plan a perimeter band is a candidate only; wall cover; registration refuses a tie |
| `test_m4_stairs_lintels.py` | 7 | Straight flight vs hand section; riser rule; partial zone; winder; lines that do not fan; lintel row by width, bearings on masonry jambs only, boundary gap and above-schedule never measured; beam over the opening; census cuts a gap at a column |
| `test_m4_slab_blinding.py` | 7 | Member overlap deducted, project default first, ground slab excluded; a member inside a face hole and crossing members deducted once; exact union where four outlines meet; blinding union against shapely |
| `test_m4_ocr_review.py` | 4 | Outcomes and confidence; a disagreeing or ambiguous reading rejects the whole role; never promoted; downstream quantities; the ST7757 readings check but never confirm |
| `test_m4_reports.py` | 3 | Missing-reinforcement register (roles, detail needed, never kg by ratio); numbered, located exceptions; CB registers and visual QA |
| `test_m4_heldout_generator.py` | 3 | The m4 variant changes only its own drawings; the M4 engine never assigns a wrong section and its exposure covers the truth |
| `test_m4_package.py` | 11 | Deliverables; hygiene, path and benchmark firewall; nothing tracked that embeds drawing content; registers agree; nothing VERIFIED or promoted; independent checks pass; positions only; held-out precision; RFIs; live reproduction of the registers from the private drawings |

## Full suite

Recorded after the run, below.
