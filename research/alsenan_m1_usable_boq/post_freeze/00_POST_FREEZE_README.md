# M1 post-freeze: the planning estimate against the external estimates

Written after the M1 freeze (`bc28327`). M1 is verified before and after, and nothing here feeds back.

- **No external figure is written.** Several are benchmark-firewall figures. Each comparison gives the external estimate's position against M1's planning range, the difference as a whole percentage of M1's base (except for totals, whose scopes differ), and one discrepancy class with the side it applies to.
- **No external estimate is a measured truth.** No accuracy figure is claimed.

| Class | Concrete comparisons | Steel comparisons |
|---|---:|---:|
| AGREES_WITHIN_M1_RANGE | 8 | 0 |
| SCOPE | 9 | 0 |
| MEASUREMENT_CONVENTION | 15 | 2 |
| MISSING_COMPONENT | 16 | 5 |
| GEOMETRY_EXTRACTION_ERROR | 2 | 0 |
| UNSUPPORTED_ASSUMPTION | 7 | 0 |
| DOUBLE_COUNTING | 2 | 0 |
| UNRESOLVED | 21 | 2 |

## Findings

| ID | Topic | Finding | Action |
|---|---|---|---|
| PF-M1-01 | totals | Every external RC total sits INSIDE M1's planning range; old V3b sits BELOW. The totals combine different scopes, so this is not an accuracy figure. | none (not a benchmark) |
| PF-M1-02 | ground slab | All three external estimates sit ABOVE M1's ground slab. M1 carries S9's 21 faces; R9.1's best route finds more cells between the ground beams. This is the largest real M1 gap the comparison exposes. | M1.1: add the R9.1 cells as PROVISIONAL faces (printed T = 10 cm) after review; do not tune to the external areas |
| PF-M1-03 | missing reinforcement items | 89 beam / ground-beam / lift concrete components that M1 carries have no bar row of any lane in S9 03 (matched by id or beam-line prefix). M1's 33 unresolved reinforcement items therefore understate what has no bar model. | M1.1: one UNRESOLVED reinforcement item per such component, so the exception report is complete |
| PF-M1-04 | necks | M1's neck volumes are above every external estimate: M1 derives about 2 m of neck from the printed 1.50 m minimum founding depth and +1.00 top; the others assume 1.5 m or do not say. | keep the printed-rule base; RFI-A03 (founding level) decides |
| PF-M1-05 | ground beams and straps | christiannp and U-C4N measure straps into the footings (a double count against the footing); the freelancer applies 30 x 60 everywhere. M1's ground beams sit near the oracles once straps are measured clear. | none to M1; RFI-A05 / exterior depth still open |
| PF-M1-06 | steel | The freelancer is above M1 in most steel groups. Where M1 has a bar model the difference is laps / wastage and section assumptions; elsewhere it is M1's unresolved bars (no bar model, no ratio used). | M1 keeps unresolved bars out of the total; a ratio is never used to fill them |
| PF-M1-07 | agreement count | 8 of 80 engine-group comparisons agree within M1's range on the same components. DOMES and the lift walls match numerically but count different components. | none |

Files: `01_CONCRETE_RECONCILIATION.csv` (family groups, four engines), `02_REINFORCEMENT_RECONCILIATION.csv`, `03_R9_1_ITEM_POSITIONS.csv`, `04_MISSING_REINFORCEMENT_CANDIDATES.csv`, `06_POST_FREEZE_SUMMARY.json`.
