# T-295: ceiling face-to-line ledger, every face of the merged ceiling ledgers against the candidate's ceiling line ids (development villa; every villa by R-T295-1)

Worker 3 (lane I), claim 2026-10-25 13:03 UTC. Integration dependency of T-284. Research only: no engine module, rule
or knowledge file, candidate line or released line changed; released default stays V2.9 + route G; nothing released.
ERS read: s.2.1 (physical element first), s.2.4 (reconcile to named causes), s.3 (one element, several geometries;
build before deduct), s.4 (rule + test, normal and adverse), s.7 (lesson row). Pattern: T-291 (R-T291-1).

## 1. Run and identity

Own run, Python 3.11.17, Drive 'Alsenan chalet project' / P7757_DXF_COMPRESSED.zip (P7757.dxf `ab54dd55`) and
'ST7757 dxf.dxf' (`9f9d1179`): research/agents_t167/v304_run.py, then research/agents_t270/v3015_run.py:
**V3_0_15_BOQ_LINES.csv `@@CSV@@`** (@@LINES@@ lines; the T-245 V3.0.16 lines are byte-identical to it, T-290 row).
Extract: `python3 -I research/agents_t295/t295_alsenan.py --extract <run>/v3015` -> CANDIDATE_V3015_CEILING_LINES.json
(@@CEIL@@ FIN.CEILING lines + the stair / dome lines read to prove there is no soffit or dome-finish line: id, item, room /
element id, unit, state, quantity, gross, deductions, RFI text; no coordinate, no name). Ledger: `--write`; `--check`
rebuilds byte-identical. Inputs (committed, merged): T-283 CEILING_LEDGER_R3_EXPORT.json (39 pieces), T-281
LEDGER_T281.csv + summary.json (stair soffit rows and zone reconciliations), T-271 RECONCILE_T271.csv (chord residuals),
and the Checker's one-owner rulings of the T-281 / T-283 batch (Verifier 05:32 / 05:34).

## 2. Physical element and what the candidate measures

Under every slab, per floor piece, exactly one owner surface: the horizontal decor ceiling; a bulkhead vertical face
(owner method, Q-48 A + Q-43); the underside of a flight or landing (stair soffit, a stair finish); no ceiling (outlined
slab opening, shaft, stair well); an open dome position (DCR-4); a held part. The formwork soffit is a form, not a
finish area, and owns no face. The candidate measures the ceiling as **one FIN.CEILING line per room = the room's plan
area** (less a void it deducts), PROVISIONAL; it has no bulkhead, stair-soffit, dome or edge line. Read from the lines:

- the GF stair room (GF-R31F8AE) and the 2F stair hall (2F-R4D1B62) have ONE line each, 'stair-well ceiling / soffit
  (section)', **BLOCKED_RFI with no quantity**: their 'before' is BLANK, never 0;
- the 1F living (1F-R78C367) has TWO lines: floor face less its own void 59.978 + the double-height ceiling over the void
  16.005 (= its piece 75.983); the per-line split of its faces is not established: they bind to the LINE GROUP;
- the GF open + pantry (GF-RC99C2A) is one line 110.9227 = 126.9277 less the void it deducts 16.005;
- five FIN.CEILING lines are EXTERIOR soffits over outside air (SOFFIT:GF:PL-01 / -02 / -03, SOFFIT:1F:PL-04 / -05,
  SOURCE_DERIVED, T-121 / T-127): no interior face lies in them (listed UNMATCHED with that reason);
- the 1F dressing (1F-RFFE7AF, decor 2.970 m2 DRAWING-CONFIRMED) has NO candidate ceiling line: a missing scope;
- the stair (FIN.STAIR.FLIGHT, lm, BLOCKED) and dome (STR.CONC.DOME, m3) lines are not finish areas: no soffit or dome
  finish line exists, so every stair-soffit face outside the GF stair room and every dome face binds to NO line.

@@BODY@@
