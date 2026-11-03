# T-419 integration package: GF LIFT TIE BEAM + HOUSE BELOW-GROUND MASONRY into ARCH_TAKEOFF_V3.0.46

Worker 3 (lane I, stream S), 2026-11-03, branch `agents/task-T-419`. **Integration package for Checker Gate B.**
Integrates T-408 (MERGED e3d9a092, Gate A PASS 2026-11-01T05:37Z with own re-measure of the GF tie runs) and T-407
(MERGED 8c0e8349, Gate A PASS 2026-11-01 00:57 with own read of ST p.1 note 2, runs and levels). Base: the candidate
of record ARCH_TAKEOFF_V3.0.45 (`5972888b`, T-478, merge 8ccf69b3; registry 1.41.0 of T-479, merge c3cbeb99).
**NOT RELEASED**; released default V2.9 + route G unchanged; rollback = V3.0.45 / V2.9. Development villa, not an
accuracy claim; rule R-T419-1 is for every villa. Drawings cited by Drive folder and title only.

integrates: T-408, T-407

## 0. Run identity and version

Drive "Alsenan chalet project": P7757.dxf (P7757_DXF_COMPRESSED.zip, `ab54dd55`) and 'ST7757 dxf.dxf' (`9f9d1179`),
decoded by the wrapper into `.work/private`. Own fresh chain this run: `research/agents_t167/v304_run.py`, then
`research/agents_t478/v3045_run.py` (**V3_0_44 `8b2fe2b6` and V3_0_45 `5972888b` reproduced**, 4,861 lines), then
`research/agents_t419/v3046_run.py` through the hub (`--method ARCH_TAKEOFF_V3.0.46`, `--v3046-inputs` from
`t419_inputs.py`): **V3_0_45 `5972888b` reproduced again inside this run; V3_0_46_BOQ_LINES.json `35d70129`**
(4,867 lines = 4,861 + 6; 5 changed (RESTATE), 6 added (ADD_HELD), 4,856 byte-identical to V3.0.45);
V3_0_46_INTEGRATION_LEDGER.csv `610874b7`. The final commit's module re-applied offline to the run's V3_0_45 lines with
the run's inputs file (equal to `t419_inputs.build`) gives `35d70129` again.

```
.work/venv/bin/python -I research/agents_t167/v304_run.py <P7757.dxf> <ST7757.dxf> --out <private>/t167
.work/venv/bin/python -I research/agents_t419/v3046_run.py <P7757.dxf> <ST7757.dxf> --out <private>/t419 --t167 <private>/t167
```

Version: V3.0.46 EXTENDS V3.0.45 (hub branch `if v3046:` inside `if v3045:`); registry 1.42.0 on 1.41.0. The hub's
V3.0.46 name shares the V3.0.45 flag line so every hub line number cited by registry 1.41.0 stays put (its builder
still reproduces the committed file).

## 1. The physical elements (ERS s.2.1)

- **GF lift tie beam**: an RC beam between the four lift columns at +3.00 above the GF F.F.L. in a storey whose F.F.L.
  to F.F.L. exceeds 4.30 m (ST p.8 note 19; GF 4.50 > 4.30; 1F / 2F 4.20: none). One element, four components: concrete,
  two side forms, one soffit form, bars. Supports = the GF storey's own columns (columns own the joints). Section printed
  nowhere (D-43, RFI-B-S14).
- **Block below the house's neighbour-side exterior ground beams**: black block from the foundation top to the beam
  soffit where ST p.1 note 2 prints it (neighbour side only). Owner trade BLOCKWORK BELOW N.G. (ELEMENT_REGISTER
  2026-10-31 20:20); never in the fence masonry (T-403 / T-400), the ground-beam concrete or the lower band.

## 2. Owner manual method and drawing-derived method side by side

| | Owner manual method | Drawing-derived method (merged pieces) |
|---|---|---|
| tie concrete | between column faces x printed section | runs S 1.80 / N 1.80 / W 1.20 / E 0.70 = 5.500 m on three sheets (GF roof slab plan, p.1 column plan, ground-beams plan); band closure 1.100 + 0.500 = 1.600 m2 (0 overlap); invariant under both D-63 column readings; section HELD |
| tie forms | 2 x L x d sides + L x b soffit | the same 5.500 m; d, b HELD |
| tie bars | from the printed bar detail (Q-71) | no bar detail printed: HELD, never a kg / m3 rate |
| MAIN_S block | Q-60 A: run x height to the beam underside | axis 19.271 - columns 3.001 = 16.270 m net; h >= +-0.00 - 0.10 - (-0.80) = 0.70 m; AT_LEAST 11.389 m2 net (gross 13.4897) |
| ANNEX_S block | as above | 10.000 m net; soffit CONFLICT (D-35): no bound |
| E / W house sides | Q-60 A only if block is built | existence UNKNOWN (band drawn, nothing printed): register items, no line |

## 3. Per line: V2.9 / V3.0.45 / V3.0.46 (V3_0_46_INTEGRATION_LEDGER.csv, 11 rows; every other line byte-identical)

| Line | Code / unit | Action | V2.9 | V3.0.45 | V3.0.46 | Evidence status (WFC s.5) | Beside (never the quantity) |
|---|---|---|---|---|---|---|---|
| L-5ae06fda LIFT_TIE_BEAM:GF | STR.CONC.LIFT m3 | ADD_HELD | - | absent (MISSING) | BLOCKED_RFI blank | HELD (section, D-43) | 5.500 m DRAWING-CONFIRMED, 3 sheets |
| L-6ef1ef1f :SIDES | STR.FORMWORK m2 | ADD_HELD, tied to L-5ae06fda | - | absent | blank | HELD (d) | 2 x 5.500 x d |
| L-71262a36 :SOFFIT | STR.FORMWORK m2 | ADD_HELD, tied | - | absent | blank | HELD (b) | 5.500 x b |
| L-c4db92ba :REBAR | STR.REBAR kg | ADD_HELD, tied | - | absent | blank | HELD (bar detail, section) | 5.500 m |
| L-7503af7c HOUSE_BELOW_NG:MAIN_S | MAS.BLOCK m2 | ADD_HELD | - | absent | blank | HELD; lower bound DRAWING-CONFIRMED | AT_LEAST 11.389 m2 net (16.270 x 0.70), gross 13.4897 |
| L-ee857398 HOUSE_BELOW_NG:ANNEX_S | MAS.BLOCK m2 | ADD_HELD | - | absent | blank | HELD (D-35 CONFLICT) | no bound; 10.000 m net run |
| L-684fcad3 pit walls | STR.CONC.LIFT m3 | RESTATE | - | blank, one fact | blank, BOTH facts | HELD | - |
| L-302b401e pit membrane walls | WP.FOUNDATION.LIFT_PIT_MEMBRANE m2 | RESTATE | - | blank, one fact | blank, both | HELD | - |
| L-f0aadf70 pit board walls | WP.FOUNDATION.LIFT_PIT_BOARD m2 | RESTATE | - | blank, one fact | blank, both | HELD | - |
| L-6d72f51d / L-e3eb0057 pit form faces | STR.FORMWORK m2 | RESTATE + tied to L-684fcad3 | - | blank, 'no concrete line' | blank, both facts, tied | HELD | - |

The two facts named on every pit-wall height line (F-T408-1 / -2): pit depth below the GF lift landing F.F.L. (lift
supplier; L-1 / D-63) AND the GF build-up F.F.L. +1.00 -> slab-on-grade top (structural / architect; RFI-S09). The
old reason is kept after 'was:' in the rfi question; quantity fields (state, net, gross, range, code, unit, location)
are asserted unchanged.

Totals (asserted by `check_totals`: no released quantity and no held range moves): MAS.BLOCK m2 26 -> 28 lines,
released 579.1011 unchanged, blocked 7 -> 9; STR.CONC.LIFT m3 1 -> 2 lines (both blocked); STR.FORMWORK m2 612 ->
614, released 1027.977403 unchanged, blocked 368 -> 370; STR.REBAR kg 2066 -> 2067, released 10250.167987 and held
14278.249488 .. 19646.877938 unchanged, blocked 760 -> 761. Released V2.9: no line in this scope.

## 4. Bindings re-checked (BIND_CHECK, nothing moves)

12 lift ring beams STR.CONC.BEAM 1.764 m3 BOUND (PROVISIONAL); shaft cap L-a615e1aa 0.5184 m3 BOUND; raft FF
L-1590b76b 11.385 m3 BOUND; the three GF block lines L-4165954c / L-4423d85b / L-63fa7862 BLOCKED_RFI and still name
the tie beam (paired: they take the displaced face once the section arrives, never a second concrete quantity); the 4
MAIN_S ground-beam lines L-cc6aaa99 / L-e8536bc4 / L-e9a88532 / L-c9bb2eca STR.CONC.GROUND_BEAM SOURCE_DERIVED
(masonry ends at their soffit: 0.000 m3 shared).

## 5. One layer, one owner; verification; held; downstream

- Overlap 0: tie vs columns (band closure 1.600 m2), tie vs ring beams (separate level bands while d < 0.75 -
  build-up, OPEN by name), tie vs pit walls (different bands); house masonry vs fence masonry: band partition house
  44.37 + fence 44.07 + pool 3.50 = 91.94 m asserted (residual 0.000); vs ground-beam concrete and band: different level
  bands (masonry from the foundation top to the beam soffit).
- Codes refused by construction (tests): a tie component on STR.CONC.COLUMN / STR.CONC.BEAM / MAS.BLOCK; a house run on
  EXT.FENCE.* / STR.CONC.GROUND_BEAM / STR.CONC.FOOTING / STR.CONC.BOUNDARY_WALL.
- Every added STR.FORMWORK line carries the V3.0.30 formwork-book record (one face id each, concrete line = the tie
  line) so the V3.0.30 guard (each face once) holds on the whole candidate.
- Checker evidence: T-408 Verifier 2026-11-01T05:37Z (GF runs 1.800 / 1.800 / 1.200 / 0.700 = 5.500 m AGREE; closure
  AGREE); T-407 Verifier 2026-11-01 00:57 (note 2 read on the sheet; runs and levels re-measured).
- HELD (WAITING keys in the run file): tie section (D-43, RFI-B-S14); tie / ring-beam clash bound; lift door head vs
  tie soffit (lintel owner); MAIN_S formation, blinding, thickness, product (Q-65 C); ANNEX_S soffit (D-35, RFI-S09);
  MAIN_E_SEA 6.600 m and ANNEX_W_STREET 6.000 m existence (register items, no line).
- Downstream: T-453 / T-372 (block purchase and mortar) read MAS.BLOCK lines: the two new lines are blank, so no
  purchase or mortar quantity moves until a value exists; the earthworks zones (V3.0.43) do not yet list the masonry
  below N.G. as buried structure (a held blank line, no quantity: the next earthworks round binds it).

## 6. Engine vs freelancer; verdict proposals

Freelancer (merged readings, quantities only): no tie-beam row and no below-N.G. block row. Tie beam: MISSING both
sides before, now a held engine line: UNRESOLVED (section). Neighbour-side masonry existence: ENGINE_RIGHT (p.1 note 2);
quantity UNRESOLVED (HELD, residual = the whole held quantity, formation / D-35). E / W: UNRESOLVED.
Engine valued vs freelancer on these items: 0 vs 0 (both blank); the gain is coverage, not value.

## 7. Regression

See the handoff for the run hashes and suites (L1 t419 43 tests; L2/L3 t478, t479, t459, r8_1, t257, t210, t130;
L4 full suite on the final commit). Rule R-T419-1 (module docstring), tests normal + adverse (villa Q by hand).
Lessons row proposed (ERS s.7): | 2026-11-03 | a printed member with no section and a printed below-ground block run
had no line in the candidate | a held element only appeared in research ledgers | every printed element gets a HELD
BLANK line per component with its drawing-confirmed measure beside and its missing facts named; added formwork lines
carry the formwork-book record | tests/t419_tie_gb_masonry | PROPOSED.
