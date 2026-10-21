# M4 — source-evidence audit, continuous beams and structural completeness

Planning estimate. Not engineering-approved. Nothing is VERIFIED, no OCR record is promoted, and the gate stays
INCOMPLETE.

- **Engine:** frozen at `35c0587` (the M4 conventions are `engine/profiles/URBAN_M4_GENERIC_CONVENTIONS_V3.json`).
- **Package:** built by `build_m4_package.py`.
- **Commands:** `14_COMMANDS.md`.

| File | What it holds |
|---|---|
| `01_EXECUTIVE_REPORT.md` | What changed, why, the new totals, the ten questions answered |
| `02_BEFORE_AFTER_QUANTITIES.csv` | M3 vs M4 by trade and family: low / base / high, unresolved, exposure |
| `03_RECONCILIATION_M3_TO_M4.csv`, `03_RECONCILIATION_SUMMARY.csv` | Every component whose value changed, tagged by the M4 rule that changed it |
| `03A_CB_SPAN_AUDIT.csv` | Every continuous-beam piece (span, reading, M3 vs M4) and every alignment-only span |
| `03B_EXTERIOR_GB_AUDIT.csv` | Every perimeter ground beam: architectural class, wall cover, inside level, case, M3 vs M4 |
| `03C_SLAB_THICKNESS_AUDIT.csv` | Every slab panel: thickness evidence class, member overlap, M3 vs M4 |
| `03D_BLINDING_AUDIT.csv` | Footing and beam blinding, the areas counted once, the conventions and their sources |
| `04_OCR_REVIEW_SHEET.csv` | The 15 OCR records: reads, glyph validation, second reading, outcome, applicability, downstream kg. The sheet with crops beside the values is generated but not committed (client drawing content). |
| `05_CB_LINES.csv`, `05_CB_PHYSICAL_BARS.csv` | The continuous-beam model: span matching and the physical bar groups |
| `06_MISSING_REINFORCEMENT_REGISTER.csv`, `06_MISSING_REINFORCEMENT_SUMMARY.csv` | Every component without a full bar quantity: roles, the detail needed, provisional kg of the other roles, M3 state |
| `07_UNRESOLVED_CONCRETE_EXCEPTIONS.csv`, `07_LINTEL_OPENINGS.csv` | The 86 unresolved concrete items, numbered and located (overlays in `st7757_route_g/overlays_m4/`), and the 57 openings |
| `08_CONFLICTS.csv`, `08_OCR_DERIVED_ITEMS.csv` | Source conflicts; quantities built on OCR-read details |
| `09_BENCHMARK_POSITIONS.csv` | External estimates as positions only (BELOW / INSIDE / ABOVE), computed after the engine freeze |
| `10_INDEPENDENT_VALIDATION.csv` | 33 independent checks (shapely second method, arithmetic, conservation); shared code disclosed per check |
| `11_HELDOUT_EVALUATION.json`, `11_HELDOUT_EVALUATION.md` | 40 new synthetic villas × 2 variants: M3 vs M4 |
| `12_RFIS.csv` | The questions a person must answer, with their scope |
| `13_TEST_RECORD.md` | M4 tests and the full suite on this commit |
| `14_COMMANDS.md`, `15_CHATGPT_NOTES.md` | How to reproduce; notes for the next session |
| `st7757_route_g/` | The CLI registers of the M4 run (CSV / JSON / SVG / HTML; the Excel and PDFs are generated only) |
| `profile_st7757_m4.json`, `evidence/OCR_INDEPENDENT_READINGS.json` | The project's printed values; the second reading of the OCR records |
