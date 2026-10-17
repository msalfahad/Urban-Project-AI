# Completeness matrix (Phase N10)

Every category has one state: SUPPORTED, PARTIAL, EXPERIMENTAL, HELD, CONDITIONAL, EXCLUDED or UNSUPPORTED.

- **Missing is never zero.** A held quantity has no value and a reason.
- **Conditional scenarios are never summed.**
- The "Evidence" column names what a quantity was checked against: hand truth (synthetic), the design spec (synthetic villa), the independent reader (real or synthetic), or none.

**No category carries an accuracy figure** (`ACCURACY_FRAMEWORK.md`).

| Category | Method | State | Evidence | Real-plan outcome | Missing for SUPPORTED |
|---|---|---|---|---|---|
| Room floor areas | V2.8 + curved openings (V2.9) | SUPPORTED | hand; reader faces | curved-window room measured on its face | spaces closed by non-wall lines (D-P8-04) |
| Ceilings | V2.8 | PARTIAL | hand | PROVISIONAL (ceiling type) | ceiling type (O-P8-02) |
| Wall plaster / paint | V2.8 heights + curved widths (V2.9) | SUPPORTED where heights are evidenced | hand; reader takeoff | +57.9478 m² certain (Mode A) | section binding on the real plan (facts used) |
| Wall tile (wet rooms) | V2.8 | SUPPORTED with evidence | hand | as V2.8 | — |
| Skirting | V2.8 + curved (V2.9) | SUPPORTED | hand; reader | range +3.29 m (unknown sill) | sill of the curved window |
| Doors | V2.8 | SUPPORTED | hand | unchanged | D-16 |
| Windows (count, width) | V2.8 + curved (V2.9) | SUPPORTED | hand; reader count | 26 → 27 | — |
| Window reveals | V2.8 + curved strips (V2.9) | PARTIAL | hand | reveal BLOCKED (sill / head) | frame / reveal detail |
| Waterproofing | V2.5 / V2.6 | SUPPORTED | hand (proof library) | unchanged | junction details (D-17) |
| Stairs | earlier stages | PARTIAL | earlier | unchanged | risers / flights from sections |
| **Masonry panel by thickness (m², m³)** | V2.9 (UP-MAS-HEIGHT-001) | **PARTIAL** (was UNSUPPORTED) | hand (43.26 / 8.652; range 35.86) | HELD: no T.O.S. / U/S SLAB on a bound band | section levels; beams over walls (OQ-06) |
| **Block material (MAS.BLOCK)** | V2.9 | **HELD** | hand | RFI naming the family | material per thickness (OQ-07) |
| **Facade run (lm)** | V2.9 (UP-FACADE-001) | **PARTIAL** (was absent) | hand; INDEPENDENT_OUTLINE | 3 floors measured (PROVISIONAL); 1 verified, 1 contradicted 0.16 m, 1 not established | D-N10-01, D-N10-02 |
| **Facade area (m²)** | V2.9 | **HELD** on the real plans; SUPPORTED with evidence (synthetic) | hand (50.60) | HELD: no next F.F.L. on a bound band | section levels (OQ-08) |
| **Exterior finish** | V2.9 | **HELD** | hand | RFI | finish specification (OQ-09) |
| **Facade plinth** | V2.9 | **HELD** | — | RFI | external ground level (OQ-09) |
| **Formwork: slab and beam soffits** | struct_n10 (UP-FW-001) | **EXPERIMENTAL** | design spec; conservation | measured (separate file) | owner approval; BOQ integration |
| **Formwork: beam sides** | struct_n10 | **CONDITIONAL** | design spec | BELOW_SLAB / TOTAL side by side | OQ-11 |
| **Formwork: footing / ground-beam sides** | struct_n10 | **CONDITIONAL** | design spec | FORMED / EARTH_CAST side by side | OQ-10 |
| **Formwork: column sides** | struct_n10 | **EXPERIMENTAL (upper bound)** | design spec | upper bound; held where storey heights are not printed | adjacency (OQ-12) |
| **Formwork: slab edges, necks, stairs, lintels** | struct_n10 | **HELD** | — | held with the reason | OQ-12; neck heights |
| **Excavation volume** | struct_n10 (UP-EXC-001) | **HELD** (footprints measured) | hand (7.92) | held: no levels, no working space | OQ-13 |
| **Backfill** | struct_n10 | **HELD** | — | held | neck heights, ground level |
| Concrete (structural) | route G | PARTIAL (as earlier stages) | earlier; design spec | unchanged | (unchanged) |
| **Rebar mass method** | route G + struct_n10 audit | **SUPPORTED (audited)** | d²/162 vs 7850 kg/m³ (+0.12 %); 0 ratio-as-measured | 0 violations | — |
| Roofs and balconies | — | UNSUPPORTED | — | absent | a roof-plan reader |
| External works | — | UNSUPPORTED | — | absent | site plan |
| MEP | — | EXCLUDED (out of scope) | — | — | — |
| Prices | — | EXCLUDED (out of scope) | — | — | — |
