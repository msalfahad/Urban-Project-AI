# T-328 Roof build-up (B13-01) into the candidate: ARCH_TAKEOFF_V3.0.31 (integration package, Gate B)

Worker 3 (lane I), 2026-10-31, run session_01E6cPnc1vcUJogfo64xkX62. Development villa, not an accuracy claim. ERS read;
s.2 steps 1-4, s.3 (physical vs contract quantity, one physical layer one line), s.4 statuses, s.7 applied. Integrates
T-321 (layer ledger, MERGED 59c82a05) and T-339 (line binding, MERGED 04f371ba): `integrates: T-321, T-339`. Released
default unchanged (ARCH_TAKEOFF_V2.9 + route G); V3.0.31 is opt-in, NOT RELEASED. Drawings cited by Drive title and
entity handle only ('Alsenan chalet project' / P7757_DXF_COMPRESSED.zip -> P7757.dxf; 'ST7757 dxf.dxf').

## 1. Result in engineering terms

The candidate had NO roof build-up family (registry B13-01 NOT_IN_CANDIDATE). V3.0.31 adds it as 16 lines = 4 roofs x
4 layers, each layer one owner trade; the membrane and its 0.20 m upturn stay the existing waterproofing lines.

| Roof (element) | SCREED TO FALLS (m3) | INSULATION (m2) | PROTECTION (m2) | FINISH (m2) |
|---|---|---|---|---|
| ROOF-430 annex +4.30 (1F-ROOF-AT220) | HELD blank; basis 54.920332 .. 55.560332 m2 (D band B3C) | UNKNOWN blank | UNKNOWN blank | **54.9203 MEASURED** (hatch D1F + B2A) |
| TERRACE-550 +5.50 (1F-ROOF-AT216) | HELD blank; basis 31.643 .. 32.721 m2 (D band 1.078, F-T339-1) | UNKNOWN blank | UNKNOWN blank | **31.643 MEASURED** (hatch AE0 + D1A + 1252) |
| ROOF-970 +9.70 (2F-ROOF-AT379) | HELD blank; basis 115.65646 .. 115.81396 m2 net of 2 domes (D band 12E2) | UNKNOWN blank | UNKNOWN blank | **115.65646 MEASURED** (hatch 2F21, domes excluded) |
| ROOF-1390 +13.90 (2F-ROOF-TOP) | HELD (Q-34) | HELD (Q-34) | HELD (Q-34) | HELD (Q-34); 49.665 drawing-derived beside |

- **FIN.ROOF.FINISH 202.21976 m2 valued** (54.9203 + 31.643 + 115.65646, DRAWING-CONFIRMED area, material BY_SPEC: no
  tile / paving type printed); 1 line blank (top roof).
- **FIN.ROOF.SCREED: 4 blank m3 lines** (t0 unprinted, designer D-39). Beside each: the T-321 falls model (above the t0
  plane ROOF-430 3.4008 .. 4.2079, TERRACE-550 2.7176 .. 2.9102, ROOF-970 8.089 .. 10.3515 m3; never a bound, never 0).
- **FIN.ROOF.INSULATION / .PROTECTION: 8 blank lines** (printed nowhere, no owner rule: UNKNOWN; the pool's
  '5cm INSULATION MEMBRANE' not extended to a roof).
- Before / after: V3.0.30 4,623 lines -> V3.0.31 4,639 lines; **4,623 byte-identical (diff SAME 4,623, ADDED 16)**;
  totals moved only in the four FIN.ROOF.* codes. Against released V2.9 + route G: the 16 lines are NOT_IN_RELEASED
  (V2.9 has no roof build-up). Files: V3_0_31_BOQ_LINES.json sha 0de8e998.., .csv 096f5b56.. (own run; the V3.0.30 it
  extends reproduces the merged candidate exactly: V3_0_30_BOQ_LINES.json f90e8a66.., .csv c8fd70f2..).
- **Freelancer:** his workbook gives ONE roof line, 285.00 m2 (source class: freelancer workbook; figure via T-071 /
  T-303, the Verifier re-multiplied it; cells NOT read here: 23.6 MB, over the connector limit). Which layer it prices
  is not known, so no finish / screed / insulation residual is claimed: NOT COMPARABLE per layer. Against the candidate's
  membrane basis (204.112 m2) T-321 decomposed it as scope (+30.718 dome footprints, +49.665 top roof Q-34 =
  284.478, residual +0.522 m2, +0.18 %): RULE_DIFFERENCE + HELD scope, a decomposition, not a proof (unchanged).

## 2. Owner manual method and drawing-derived method, side by side

| Layer | Owner manual method / rule | Drawing-derived method | Evidence status |
|---|---|---|---|
| Screed to falls | Q-41 'if it is roof or balconies it is screed', its own line (volume); Q-45 sets its mix only (Lead ruling ELEMENT_REGISTER 2026-10-29: one physical falls layer, one SCREED volume); thickness not given (D-39) | plan inside the wall / parapet INNER faces by handle (T-321, bound T-339); falls model t0 + 1 % rise beside | scope ASSUMED — OWNER-APPROVED (Q-41); area DRAWING-CONFIRMED; volume HELD |
| Insulation | none on record (OWNER_QUESTIONS_ANSWERED searched by T-321: 'insulation', 'roof') | not printed on any sheet (T-321 search of both DXFs, sanitary sheets, section A-A) | UNKNOWN |
| Protection | none (Q-41 gives ONE screed line; a separate protection layer is neither printed nor ruled) | not printed | UNKNOWN |
| Finish | no owner rule for a roof finish material; Q-42 gives roof tile joints 2 mm only | designer finish hatch (layer 3) to its physical edges; annotation islands / symbol frames / door swing are not edges | area DRAWING-CONFIRMED (Gate A T-339: TERRACE-550 hatches re-measured 31.643290); material HELD |
| Membrane + upturn (not this package) | UP-WP-ROOF-001 / Q-24 | existing FIN.WP.ROOF / FIN.WP.ROOF_UPTURN lines | ASSUMED — OWNER-APPROVED, unchanged, bound by id |

## 3. Method (R-T328-1, every villa) and what the engine refuses

engine/source/arch_v3031.py: one line per (roof, layer); every roof carries all four layers (an unknown layer is a blank
row, never a silent omission); ONE screed m3 line per roof (a second falls / tile-bed volume refused: Q-41 and Q-45
describe one layer); a valued screed is a wedge (area x t0 + the rise, both printed): a constant-thickness volume on a
roof with a printed fall is refused; no thickness without its print; no layer area above the roof outline (face plan
inside the parapet inner faces); a layer edge at the parapet OUTER face refused; a layer up a parapet only with a printed
upturn; a basis range only with its named cause; HELD / UNKNOWN BLANK, a held figure refused (0 included); a valued layer
on a held roof refused; the bound membrane / upturn lines and the 4 STR.CONC.PARAPET lines must stand in the candidate as
bound (stale binding stops); a roof layer on a parapet element id refused; applied once; every V3.0.30 line
byte-identical and every family guard of V3.0.10 .. V3.0.30 re-run on the V3.0.31 lines. A held text never concludes on
a figure (the V3.0.24 line-state rule found 'a x b = c m2' beside on the top-roof rows: written '->' since).

Cross-trade (acceptance (b) / (i)): the parapet RC (STR.CONC.PARAPET, STRUCTURE) and its faces (FACADE outer, ROOFING /
WP inner) are other lines; the roof layers stop at the parapet inner face (T-339 closure: shared with parapet rows 0.000
m2); the roof edges shared with the parapet are carried once, by the parapet's own lines (layer upturns: only the
membrane's 0.20 m, an existing lm line). Pinned parapet binding: research/agents_t328/PARAPET_LINES_V3030.json (4 ids,
state, figure only).

## 4. Registry: BOQ_FAMILY_MASTER 1.26.0 (acceptance (g) / (h))

research/agents_t328/build_master_1_26_0.py -> rules/coverage/BOQ_FAMILY_MASTER_1.26.0.json (1.25.0 never edited; FMC
check clean; builder --check equal). PROPOSED, the Checker confirms with the merge; no candidate state changes.

- B13-01 owns FIN.ROOF.SCREED / .INSULATION / .PROTECTION / .FINISH; NOT_IMPLEMENTED -> IMPLEMENTED_NOT_INTEGRATED.
- (g) ownership census over every UPPER.UPPER literal of every engine/source/arch_v30*.py: the 1.25.0 scan (STR / FIN /
  ARCH / MAS / DOOR / MET) missed 15 literals of merged packages: EXT.PAVING.INTERLOCK / EXT.FLOOR.PORCELAIN /
  EXT.FLOOR.OUTDOOR -> B13-02 (outdoor hard floors; NOT_IMPLEMENTED -> IMPLEMENTED_NOT_INTEGRATED); WP.FOUNDATION.* (8)
  -> B8-08 (below-grade waterproofing; same move); EXT.POOL.WATER_FACE apart with its reason (no pool-finish family:
  FINDING F-T328-2 for the register owner); FLOOR.INTERNAL / FLOOR.OUTDOOR (floor-scope keys) and
  WATERPROOFING.FOUNDATION (subtrade label) apart: not item codes. The 1.26.0 guard scans STR / FIN / ARCH / MAS / DOOR /
  MET / EXT / WP / FLOOR / WATERPROOFING; adverse: an XYZ.* literal in a V3.0.x module, an EXT.* / WP.* code no family
  owns, B13-01 back to NOT_IMPLEMENTED, the guard code dropped from its family: each refused.
- (h) Lead ruling F-T199-4: NEW family B13-08 'Guard railings outside stairs' (lm, metalwork) owns MET.RAILING.GUARD
  (21.550 lm, no quantity moved), removed from item_codes_without_family; the stair guardrail B7-09 keeps FIN.RAILING.
  The registry carries 100 families (the 99 in their order + B13-08); the 1.26.0 test asserts 100.
- **Test adaptation (for the Checker's judgement, gate on tests):** tests/t199_formwork_metalwork/test_family_master_1_25_0.py
  asserted "1.25.0 is the governing registry" and ran its full-strength guards on the LIVE code, so any later package
  that writes a new code fails it by construction. It now judges 1.25.0 on the code of its own head: a module that a
  NEWER registry declares (and that 1.25.0 does not) is set aside there and judged at full strength by the newer
  registry's test (tests/t328_roof_buildup/test_family_master_1_26_0.py); the governing assertion accepts a newer
  registry only if it carries every 1.25.0 pending entry unchanged. Every 1.25.0 assertion on its own head still runs
  (the same adverse cases, same expected sets). No assertion removed. One function renamed in my module
  (check_roof_layers, not ..._buildup) so it does not carry B13-01's 1.25.0 name term 'roof_build'.

## 5. Validation

- tests/t328_roof_buildup: 36 pass (17 + 19) (V328 non-Alsenan villa by hand: finish 47.140 + 20.000 = 67.140 m2, insulation
  20.000 m2 printed, screed wedge 20.000 x 0.05 + 20.000 x 0.040 / 2 = 1.400 m3, 8 blank lines; adverse: second falls
  layer for Q-45, constant layer on a sloped roof, held as 0, default thickness, outer-face edge, above the outline,
  range without cause, up a parapet without upturn, wrong unit, missing layer, wrong owner trade, valued layer on a held
  roof, unknown source, stale membrane / parapet binding, applied twice, finished-line guard (figure on a blank line,
  duplicate roof x layer, layer on a parapet element), foreign change, runner registration, blank text without '=').
- Registry folders (every tests folder that reads a BOQ_FAMILY_MASTER file, 30 folders): pass except the codemap map
  check before regeneration (regenerated by the tool, stale none).
- Alsenan: research/agents_t328/v3031_direct.py on the reproduced V3.0.30 (byte-identical to the merged candidate),
  and research/agents_t328/v3031_run.py through tools/urban_boq_m9.py arch --method ARCH_TAKEOFF_V3.0.31 (section 7).
- Freeze 0 differing; codemap check stale none; FULL SUITE: section 7.

## 6. For the Checker (Gate B: every added line is new scope, so all 16 are hand-checked)

1. Finish areas by own read of P7757.dxf: ROOF-430 hatches D1F + B2A = 54.920; TERRACE-550 AE0 + D1A + 1252 = 31.643
   (T-339 own 31.643290); ROOF-970 hatch 2F21 five paths 114.985 + door swing 0.622 + dome cusps 0.045 + flattening 0.004
   = 115.656. Lines L-702487d5998861c463c1, L-a6ce29981d037284ec84, L-e005eb9041acb08d8b87.
2. Screed basis ranges and their causes (D bands B3C, C8A .. CA3, 12E2) on L-bec94500648a90fb2f2a,
   L-5f018cfc13aaa9ae2210, L-f4ae7151a6e2b93dd7ad; ROOF-1390 L-b016c961ddf9e530e3c1 blank (Q-34).
3. The 8 insulation / protection lines blank with their reason; no figure anywhere.
4. Byte-identity: diff SAME 4,623; the four STR.CONC.PARAPET and eight FIN.WP.ROOF / ROOF_UPTURN lines unchanged.
5. Registry 1.26.0: the three moved families, B13-08, the four apart entries (confirm or correct the family choices:
   EXT.* outdoor floors in B13-02, WP.FOUNDATION.* in B8-08), and the 1.25.0 test adaptation of section 4.

## 7. Run record

- Drawings decoded into the private folder only (Drive 'Alsenan chalet project': P7757_DXF_COMPRESSED.zip, ST7757 dxf.dxf).
- research/agents_t167/v304_run.py -> research/agents_t199/v3030_run.py: V3_0_30_BOQ_LINES.json f90e8a66fd05.. / .csv
  c8fd70f225a1.. = the merged candidate of record V3.0.30 (T-199 r3) byte for byte.
- research/agents_t328/v3031_direct.py on it and research/agents_t328/v3031_run.py through tools/urban_boq_m9.py arch
  --method ARCH_TAKEOFF_V3.0.31: the same V3_0_31_BOQ_LINES.json 0de8e99864a2.. / .csv 096f5b56fc5a.. (identity: added
  16, outside rows identical to V3.0.30 4,623; diff vs V3.0.30 ADDED 16 / SAME 4,623; vs released V2.9 the 16 added
  NOT_IN_RELEASED).
- L4 full suite to the end (tests/ 376 folders + 213 top-level files + agents/, two parallel parts) on 1277adfa against
  research/agents_t202/known_failures.json: KNOWN 395, ABSENT 1, NEW 3, each traced: (1) tests/codemap map check: this
  report file was created during the run (research/agents_t328 file count 5 -> 6); maps rebuilt by the tool on the
  hand-in commit, stale none, the folder passes; (2) tests/ad1_authority_decisions test_rebuild_is_byte_identical: the
  folder re-run alone passes (the parallel-part sandbox interference T-199 r3 recorded); (3) below. Part B (second half of the folders +
  agents/): 1 failure, tests/t374_straight_bbs::test_snapshot_equals_the_board_verdict_files_when_the_board_is_present,
  which fails identically on the working head ca1d4278 (.work/engine): the T-374 downgrade snapshot predates the
  Checker's DG-df07eb3d6ccec0e9 record on the board (FINDING F-T328-3 for the Lead / Checker: refresh the T-374 snapshot;
  not this package's file).

## 8. Lessons row (proposed, ERS s.7)

| Date | Problem | Root cause | General rule (scope) | Regression test | Status |
|---|---|---|---|---|---|
| 2026-10-31 | 15 item-code literals of merged V3.0.x packages (EXT.*, WP.FOUNDATION.*) were owned by no registry family, and two families that measure them stood NOT_IMPLEMENTED | each registry version's guard scanned a fixed prefix list; a package with a new prefix was not seen | the ownership guard derives its prefix set from every V3.0.x module and requires every UPPER.UPPER literal there to be owned or listed apart with a reason (every villa, every package) | tests/t328_roof_buildup/test_family_master_1_26_0.py (normal census; adverse XYZ.* / EXT.* / WP.* unowned) | proposed |
| 2026-10-31 | a held line's text with 'a x b = c m2' beside reads as a line concluding on a figure | a beside figure written with '=' in a BLANK line's formula | a blank line's text writes a beside figure with '->', never '=' (every package) | test_a_blank_line_never_concludes_on_a_figure | proposed |
