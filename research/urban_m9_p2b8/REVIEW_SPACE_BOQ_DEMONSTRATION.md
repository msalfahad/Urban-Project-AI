# REVIEW-space BOQ coverage: demonstration

**Method:** ARCH_TAKEOFF_V2.7.1, rules UP-REVIEW-001 and UP-QTY-STATUS-001 (registry 1.3.0).

**Outputs**
- `REVIEW_SPACES.json`: per space, the plausible readings, the geometry, the five quantity classes, the released lines and the conditional quantities per scenario;
- `BOQ_RELEASE_REPORT.json` / `.csv`;
- the scenario sets in `BOQ_SCENARIOS.json`.

## 1. The rule

1. **Which spaces get scenarios.** A space under wet-classification review has a **plausible set** of readings when all three hold:
   - a sanitary fixture or a WC shape is drawn inside it;
   - it is enclosed and interior;
   - no stair or void is drawn inside.

   The readings are **WET_SCOPE** (a W.C. / wash room, owner wet scope UP-WET-001) and **DRY_SCOPE** (a lobby / wash area). A space without that evidence (a plain unlabelled space) has no plausible set: NOT_ESTABLISHABLE.
2. **One run per reading.** In each run the space is typed by the scenario, and nothing else changes.
3. **Released into the main BOQ** is only a finish line of the space that is identical in every scenario: same quantity or range, same evidence state, same rule. Its system must also not depend on the type. **Plaster is never released while the wall finish over it differs**: behind wall porcelain it is a different system (UP-FIN-PAINT-001). A released line is labelled CLASSIFICATION_INVARIANT; the space's type stays under review.
4. **The wall face** is the plaster measurement: wall run × plaster height − each opening. It is reported as **geometry**, not as a BOQ line:
   - CONFIRMED_GEOMETRY: the same value in every scenario;
   - BOUNDED_GEOMETRY: the same range in every scenario;
   - NOT_MEASURED: no height is established;
   - NOT_INVARIANT: the scenarios disagree.
5. **The rest are CONDITIONAL quantities**, one mutually exclusive set per space. They never enter the main BOQ, and the scenarios are never added together.
6. **Five classes.** Every quantity of the space sits in exactly one:

   | Class | Meaning |
   |---|---|
   | GEOMETRY_CONFIRMED | measured with confidence, whatever the type |
   | INDEPENDENT_OF_CLASSIFICATION | identical in every reading; released |
   | CONDITIONAL_ON_CLASSIFICATION | depends on the reading |
   | REQUIRES_DRAWING_EVIDENCE | no scenario measures it |
   | NOT_ESTABLISHABLE | no evidence-based set of readings |

## 2. Hand derivation on a synthetic plan

The plan is `p2b8_fixtures.wc_plan("BASIN")`:
- **The lobby:** 3.40 × 3.00 m, unlabelled, holding a wash basin.
- **Its doors:** a 0.80 m door from a W.C. and a 1.00 m external door, both 2.10 m high.
- **Stated test heights:** plaster 3.00 m, wall tile 2.40 m.

| Quantity | Hand value | Class | Engine (V2.7.1) |
|---|---|---|---|
| floor area / ceiling plan | 3.40 × 3.00 = 10.20 m² | geometry | 10.20 |
| perimeter / wall run | 2 × (3.40 + 3.00) = 12.80 m | geometry | 12.80 |
| **wall face** | 12.80 × 3.00 − (0.80 + 1.00) × 2.10 = 34.62 m² | geometry (CONFIRMED) | 34.62 |
| **ceiling** | 10.20 m² | INDEPENDENT_OF_CLASSIFICATION: **released** | 10.20, labelled CLASSIFICATION_INVARIANT |
| plaster | 34.62 m² in both readings | CONDITIONAL (SYSTEM_DEPENDS_ON_WALL_FINISH) | 34.62 / 34.62, not released |
| WET: floor wet tile | 10.20 m² | CONDITIONAL | 10.20 |
| WET: wall tile | 12.80 × 2.40 − 1.80 × 2.10 = 26.94 m² | CONDITIONAL | 26.94 |
| WET: waterproofing floor / upturn | 10.20 m² / (12.80 − 1.80) × 0.20 = 2.20 m² | CONDITIONAL | 10.20 / 2.20 |
| WET: doorway waterproofing | 1.00 × 0.20 + 0.80 × 0.20 = 0.36 m² (two lines) | CONDITIONAL | 0.20 + 0.16 |
| DRY: floor porcelain / paint | 10.20 m² / 34.62 m² | CONDITIONAL | 10.20 / 34.62 |
| skirting | 12.80 − 1.80 = 11.00 m in both, under different rules | CONDITIONAL (RULE_DIFFERS) | 11.00 / 11.00 |
| paint above tile, penetrations, transitions | no scenario measures them | REQUIRES_DRAWING_EVIDENCE | held, with the reason |

**Without heights (Mode U):**
- the ceiling is still released (10.20 m²);
- the wall face is NOT_MEASURED;
- plaster moves to REQUIRES_DRAWING_EVIDENCE.

**A plain unlabelled lobby** (no fixture) gets geometry only. Its finishes are NOT_ESTABLISHABLE, and nothing is released.

Tests: `tests/m9_p2b8/test_p2b8_review_release.py`, 18 tests. They also check invariance under rot30 / mirror / metres, determinism, and that every line is reported once.

## 3. The reference plan: the three hand-wash spaces (private run, aggregates)

| | V2.7 | V2.7.1 Mode A | V2.7.1 Mode U |
|---|---|---|---|
| REVIEW spaces | 6 (3 hand-wash, 3 with no fixture evidence) | same 6, same classification | same |
| hand-wash spaces: area / ceiling plan / perimeter | 9.348195 m² / 9.348195 m² / 21.598855 m | same | same |
| **ceilings released** | none | **3 lines, 9.348195 m²** | 3 lines, 9.348195 m² (no height needed) |
| **wall faces (geometry, not BOQ lines)** | not reported | 1 CONFIRMED (21.369607 m²); 2 BOUNDED (16.2 – 18.6 and 9.608882 – 12.0 m²: a door closed only by its leaf has no established deduction); all three 47.178489 – 51.969607 m² | 3 NOT_MEASURED (no heights) |
| quantity classes (3 spaces) | — | 3 independent, 31 conditional, 6 require drawing evidence (paint above tile, waterproofing penetrations) | 3 independent, 22 conditional, 15 require drawing evidence |
| the 3 spaces with no fixture evidence (8.13 m²) | withheld | NOT_ESTABLISHABLE: geometry only, nothing released | same |
| main BOQ lines | 484 | 487 (+3 ceilings; no other difference) | 476 |
| release report | — | 296 confirmed (196 source-derived, 100 provisional), 191 held, 0 excluded, 4 conditional sets; every line once | 252 confirmed, 196 held, 28 excluded, 4 conditional sets; every line once |

**Conditional quantities of the three spaces, Mode A, per reading.**
- They are **never summed across readings**, and none is in the main BOQ.
- A bounded plaster / tile range is shown as a range, not in these totals.

| Item | WET_SCOPE | DRY_SCOPE |
|---|---|---|
| floor wet tile | 9.348195 m² | — |
| floor porcelain | 0.33 m² (doorway strips) | 9.678195 m² (incl. 0.33 m² of strips) |
| wall tile | 16.423686 m² (one space; two bounded) | — |
| plaster | 21.369607 m² (one space; two bounded) | 21.369607 m² (one space; two bounded) |
| paint | — (above tile: held) | 21.369607 m² (one space; two bounded) |
| skirting | 15.246163 m | 15.546163 m |
| waterproofing floor / upturn / doorway | 9.348195 m² / 3.049232 m² / 0.24 m² | — |

**Verification.**
- The released ceilings were checked against the independent reader (`tools/arch_change_verify.py`, V2.7 → V2.7.1). Two of three are VERIFIED by the independent face. The third is EXPLAINED_UNVERIFIED: one side of that space is a 1.256 m line of a non-wall layer, so the wall lines alone do not enclose it (D-P8-04).
- The wet-evidence decision of each space (basin inserts, no WC) is re-read by the independent fixture census.

**Still open: D-17** (the owner's type for each space). Once it is answered, each space's conditional set becomes its BOQ lines.
