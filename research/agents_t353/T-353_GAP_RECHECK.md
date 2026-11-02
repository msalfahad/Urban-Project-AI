# T-353 gap re-check: B8-08 foundation waterproofing is already in the candidate (no new version built)

Worker 3 (lane I), 2026-11-02, run session_01E6cPndqoiEGW113sqaZgpw. Research + test only; no engine, tools, rules
or registry file changed; nothing released; released default unchanged.

## Finding

The row's evidence ("B8-08 NOT_IMPLEMENTED in BOQ_FAMILY_MASTER 1.19.0, not in the candidate") is stale. The family
was integrated by T-270 as ARCH_TAKEOFF_V3.0.15 (`engine/source/arch_v3015.py`, r2 Gate B PASS 04d34378; ELEMENT_REGISTER
row 'Footing undersides and sides, lift pit': VERIFIED 7 lines in V3.0.15) and is carried unchanged to V3.0.42.
Master 1.26.0 (T-328) already raised B8-08 to IMPLEMENTED_NOT_INTEGRATED (the 1.25.0 scan missed the `WP.` prefix,
F-T199-5). Building a V3.0.43/44 family now would count every piece twice (+360.0282 m2, +6.5275 m3).

## Reconciliation (R-T353-1, `t353_reconcile.py`)

T-270 records (19 lines, from the merged T-219 / T-276 ledgers) vs the T-471 V3.0.42 completeness row B8-08:

| unit | lines | released | held blank | candidate V3.0.42 | difference |
|---|---|---|---|---|---|
| m2 | 15 | 360.0282 (membrane 109.85 + screed 109.85 + pit membrane 47.43 + board 26.73 + pit screed 20.70 + buried liquid 45.4682) | 9 | 15 / 360.0282 / 9 | 0.000000 |
| m3 | 3 | 6.5275 (screed 5.4925 + pit screed 1.035) | 1 | 3 / 6.5275 / 1 | 0.000000 |
| item | 1 | - | 1 (procurement) | 1 / - / 1 | 0 |

No blinding line in the family (the 10 cm blinding stays STR.CONC.BLINDING; T-478 integrates its valued pit line).
Held stays held: 1B1B F10/F (Q-31: hold, designer), footing sides (formation selects the detail, Q-21 C), pit walls
(pit depth, D-43), buried tops / necks / boundary / held GB faces, procurement (product not printed).

## Open items for the Lead / Checker (not changed here)

1. Coverage registry metadata stale in master 1.37.0 B8-08: `in_v3_0_candidate: "no"`, `candidate.state:
   NOT_IN_CANDIDATE` (as_of T-193), opt_in_readers 'V3.0.15 .. V3.0.31'. Correct in the next master version after
   T-350's 1.38.0 merges (a new version file; never edit 1.37.0 / 1.38.0).
2. Verified under-reported in the aggregation: the T-270 line records name the Verifier 10:40 own re-measure of ALL
   components for 7 lines, but the binding V2 verdict set (T-469 / T-471) holds WHOLE verdicts only for the 2 pit
   screed lines (20.70 m2, 1.035 m3). Gap: 293.86 m2 (109.85 + 109.85 + 47.43 + 26.73) and 5.4925 m3 counted
   MEASURED, not VERIFIED. Whether those lines meet the V2 aggregation-proof bar is the Checker's call.

## Rule and lesson (proposed, ERS s.7)

R-T353-1 (every villa): before integrating a 'missing' family, reconcile its merged pieces with the candidate's
completeness row; equal -> already carried, no new version; else name the difference, never net it.
Lessons row: 2026-11-02 | a row asked to integrate a family the candidate had carried for 27 versions | the row cited
an old master and the master's candidate sub-record was never refreshed | re-check the gap on the current candidate's
completeness row before building | tests/t353_foundation_wp_carried (normal: Q-353 hand; adverse: second
integration +34.040 m2 named, held as 0 refused, held range, mm scale, no shared code) | PROPOSED.
