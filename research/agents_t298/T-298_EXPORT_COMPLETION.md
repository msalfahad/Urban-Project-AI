# T-298: export completion: reinforcement in metric tons by default + the slab completeness join by panel id

Owner 2026-10-25 11:51 (0) ("complete the real export first ... correct tonne reporting"); Verifier 11:28 F-REC-01.
Worker 2, 2026-10-25. Drive "Alsenan chalet project": P7757.dxf (from P7757_DXF_COMPRESSED.zip, sha ab54dd55) and
"ST7757 dxf.dxf" (sha 9f9d1179). No drawing content, coordinate or name is written here.

## 1. Physical / contractual element

- Reinforcement: the contractual BOQ unit is the metric ton (owner 2026-10-24 14:23). The engine measures in kg and every
  V2 verdict binds to the canonical line content in kg. The unit is a REPORTING conversion (t = kg / 1000), applied once,
  at the export boundary; it changes no quantity, no line, no verdict.
- Slab: the element of CONC.SLAB is a slab panel between beam faces (T-234 C1 convention, 62 panels, Checker-verified
  60.2804 m3). A candidate face that the drawing classes as beam / not concrete is not a slab element: V3.0.12 retired
  13 such faces (NOT_APPLICABLE_WITH_EVIDENCE, home named, source document cited).

## 2. What changed

| File | Change |
|---|---|
| tools/boq_export_v1.py | CLI default = the CONTRACTUAL export (schema URBAN_BOQ_EXPORT_V2, manifest URBAN_BOQ_EXPORT_MANIFEST_V3): BOQ.csv / sheet BOQ / BOQ_TRADE_SUMMARY.csv / sheet Trade summary carry kg rows in t (contract_view, kg / 1000 once, 6 dp, totals from the unrounded kg sums); columns unit / engine_unit / conversion + audit columns engine_<quantity column> (kg beside t); BOQ_ENGINE_UNITS.csv and BOQ_TRADE_SUMMARY_ENGINE_UNITS.csv = the V1 files byte for byte; BOQ_CONTRACT_TOTALS.csv. `--engine-units` = opt-out (V1 bytes); `--contract-units` keeps the T-273 layout; export() keeps its V1 library default. New refusals: a row converted twice; a t row of an item registered in kg (pre-converted or relabelled); contractual + contract_units in one export. Unchanged: mixed kg / t refused, verdict binding, semantic_sha256 (engine-unit rows). |
| tools/boq_export_v1.py | Completeness scope (F-REC-01): `scope_split()`: an element whose every line of the group is NOT_APPLICABLE_WITH_EVIDENCE WITH evidence (notes AND a source document) leaves the element scope count (listed as not_applicable_out_of_scope); an NA line without a document is the blocker `NOT_APPLICABLE WITHOUT EVIDENCE n`; the T-236 inventory count leaves out an inventory element that only such lines carry. The V2 verdict scope (bind_verdict) is unchanged: it still names every line id. |
| research/agents_t236/slab_panel_join.py | NEW rule R-T298-SLAB-JOIN-1: slab lines join the T-234 panels BY PANEL ID (nearest volume within 0.0002 m3 per storey; EXACT / INTERCHANGEABLE / AMBIGUOUS; unmatched lines -> REGISTER_ONLY; panels with no line -> MISSING). |
| research/agents_t236/alsenan_t236.py | `--slab-join panel` (default) / `count` (the merged T-236 join, reproduces the V2.9 / V3.0.8 summaries); retired NA slab faces get their own EXCLUDED key; held slab lines are not joined by volume. Writes SLAB_PANEL_JOIN.json. |
| research/agents_t298/SLAB_PANEL_JOIN_V3016.csv | the 62 panel -> line pairs on V3.0.16 (panel / line ids, volumes only). |
| tests/t298_export_completion/* | 23 tests: contractual default (10), slab join + scope (10, synthetic villa VG-298), committed V3.0.16 join ledger (3). |

Why the count join failed on V3.0.12+: it gave the k-th slab line of a storey the key SLAB#k, retired lines included, so
13 retired faces took panel slots (12 surplus keys REGISTER_ONLY, the panels they took EXCLUDED: found 50) and the
13 NA elements stayed in the export's element scope (75 vs inventory 62). A count join also lets one missing panel and
one extra face on the same storey cancel; the panel join reports both (test_a_panel_missing_and_an_extra_face...).

## 3. Real re-run (V3.0.16, own run this session on code 08f23dd9 = working head 294da634 + T-298)

Candidate reproduced: V3_0_16_BOQ_LINES.json canonical lines_sha256 3181cf12, csv a4dc01dd, IDENTITY 6f1676c2 (= the
Verifier 11:28 values); 3,699 lines; Checker records docs/agents/verdicts/V3.0.16/ (8 V2 + 7 downgrades).

Regression first: with the T-236 count join and `--engine-units`, the T-298 tool writes BOQ.csv 8487084d = the Verifier
11:28 export byte for byte (the old tool on 294da634 also gives BOQ_TRADE_SUMMARY fa656260; the T-298 summary differs
only in completeness texts: the NA-with-evidence elements leave each group's scope count, no group changes status).

Slab panel join on V3.0.16: 62 / 62 panels, 52 EXACT + 10 INTERCHANGEABLE (5 pairs on 1F: two dome-corner pairs
1F-073/c0|c1 and 1F-076/c0|1F-091, 1F-076/c1|1F-092, 1F-060|1F-090, 1F-086|1F-088, each pair two lines of identical
volume), 0 unmatched lines, 0 missing panels, max |line - panel| 0.000093 m3 (1F-076/c0, a curved corner), per storey
line - ledger GF +0.000004, 1F -0.000242 (T-234's own 4-dp area rounding), 2F 0.000000 m3. T-236 CONCRETE.SLAB:
GAPS (found 50, REGISTER_ONLY 12) -> COMPLETE_AGAINST_INVENTORY (found 62, missing / duplicated / held / register-only 0).

Contractual export (default) with the Verifier's records and the panel-join report:

| | Verifier 11:28 (kg, count join) | T-298 |
|---|---|---|
| CONC.SLAB m3 | COUNTED WHOLE, completeness FAIL (REGISTER_ONLY 12; 62 != 75) | **VERIFIED whole line**: 62 rows VERIFIED, 13 retired faces VERIFIED ZERO (the verdict names them), completeness PASS (inventory 62 = element scope 62) |
| whole lines verified in the export | 0 | **1** (CONCRETE 1 / 13 lines) |
| row counts | VERIFIED 0 / ZERO 0 / COMPONENT 5 / MEASURED 999 / HELD 1,921 / UNMEASURED 54 / EXCLUDED 774 | VERIFIED 62 / ZERO 13 / COMPONENT 5 / MEASURED 937 / HELD 1,921 / UNMEASURED 54 / EXCLUDED 761 (total 3,753 both) |
| STR.REBAR | kg: 2,505 rows | **t**: 2,505 rows converted once; measured unverified 10.250168 t (10,250.167987 kg); held range 15.250786 .. 21.621545 t; 1,524 held rows blank; line NOT VERIFIED |
| WP.FOUNDATION.LIFT_PIT_SCREED WHOLE records | COUNTED WHOLE, completeness FAIL | unchanged (F-REC-02: no waterproofing inventory, T-301) |

Cell check (script in this run): engine-unit rows vs 11:28: only the 75 STR.CONC.SLAB rows moved (62 MEASURED
UNVERIFIED -> VERIFIED, 13 EXCLUDED -> VERIFIED ZERO), no quantity cell moved; contractual BOQ.csv vs its engine-unit
file: every non-kg row identical in every V1 column; every kg row differs only in unit and quantity columns, each t
value = kg / 1000 within 5e-7 and its engine_<column> = the kg cell. The verified subtotal 60.280155 m3 is the sum of
the 6-dp rows; the engine's unrounded line sum is 60.280158 (Checker 60.2804, -0.0004 %): a 0.000003 m3 rounding residual.

No candidate line, quantity, state, line id or V2.9 cell moves (the export is read-only; the candidate is reproduced
byte for byte).

## 4. Statuses, verdicts, what is missing

- CONC.SLAB: VERIFIED (Verifier Gate B 2026-10-24 09:38, V2 record V2-30fd673898470518); now countable as a whole line
  once the Checker re-runs the join (Gate A of this task).
- STR.REBAR in t: a unit change only; every rebar quantity keeps its own status (route G 16.39 t remains a PROVISIONAL
  SUBTOTAL, owner 10:33 (2)).
- Verdict proposal: RULE_DIFFERENCE is not involved; ENGINE_RIGHT on the slab join (the 62 candidate slab lines are the
  62 T-234 panels, per-panel |diff| <= 0.000093 m3).
- Not done: F-REC-02 (waterproofing inventory: T-301). The audit file BOQ_AUDIT_UNSUPPORTED_BASIS.csv stays in engine
  units (it carries a unit column; no kg row is in it today). Held-reason texts that quote a discrepancy keep the
  engine unit they name.
- Residual risk: the panel join matches by volume, so two panels of equal volume carried by two equal lines are
  INTERCHANGEABLE (which is which is not established; no count or sum depends on it).

## 5. Lessons-register row (proposed, ERS s.7)

| 2026-10-25 | a verified whole line could not count because the completeness join used a count per storey | a count join
assigns keys by order and absorbs retired lines; it cannot say which element is missing | a completeness join binds
each line to an inventory element by id (or by an exact, tolerance-bounded attribute with ties named), retired NA lines
with evidence take their own excluded key, and the join is re-run on every candidate grain (PROJECT-INDEPENDENT;
provenance T-236 / T-298) | tests/t298_export_completion | CLOSED by T-298 once verified |
