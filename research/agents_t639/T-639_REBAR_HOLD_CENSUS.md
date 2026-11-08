# T-639 B11-01 rebar hold census: 801 HELD-blank + 6 open-high lines to a named cause (R-T639-1)

Worker 1, 2026-11-08 (run session_01E6cPnaMu6r2HpPpicDwtDt), branch `agents/task-T-639`. Research ledger, unwired:
nothing released, no candidate / engine / rule / knowledge version / registry file changed; owner gate 2026-10-25 10:33
(no reinforcement calculation code change) respected. Development villa only; drawings referred to by Drive folder and
title only. Output: `out/REBAR_HOLD_CENSUS_T639.json` (every line: element, bar group, hold text and its source, bound
concrete line and state, class, kind, cause) and `out/REBAR_HOLD_CENSUS_T639.md` (tables).

## 1. Physical element and scope

The reinforcing bars of each structural element, by bar group, net installed mass (kg internally, t at display;
OWNER_RULE_REBAR_2026-10-24 s.1). Laps / stock allowance are never added (s.2 is a proposal; s.4 item 3). Scope: the T-630
trial-BOQ dry run, candidate ARCH_TAKEOFF_V3.0.58 + overlay V15, family B11-01 STR.REBAR: 2,652 lines = 374 RELEASED
(9,375.306 kg) + 900 HELD bounded + 801 HELD blank + 577 EXCLUDED; 6 of the bounded lines have an open high end.

## 2. Method (R-T639-1, t639_rules.py)

Per line, the hold text is read from the latest record that states it (T-449 register for the V3.0.27 slab re-base;
APPLIED Checker downgrade; the line's candidate record via T-297; the wiring-manifest row for overlay lines), never
re-typed. The line's own concrete line is bound by id where a record links them (columns via formwork R4 -> T-332 face,
mark + storey checked; beams via HL:BEAM_LEDGER; footings / necks via the same route id; lift tie beam; overlay rows;
slabs at family level: no STR.CONC.SLAB line is HELD). Class priority: A concrete HELD -> D computable now -> C
owner-gated -> B input not given. Every line must reach a class with a cause (an unknown text raises).

## 3. Result: 807 / 807 classed

| class | lines | what it means | quantity |
|---|---|---|---|
| A concrete HELD | 188 (187 blank + 1 open-high) | bars follow their HELD concrete: 92 columns, 56 necks (route G), 35 beams, lift tie beam, lift-pit walls, DOME-3, east dome ring, 1 footing | none computed |
| B input not given | 603 (598 + 5 open-high) | Q-71 / spacing notation 102, bar ends / legs / bends not dimensioned 251, no bars printed 49, footing cover only a minimum (DG-a97ec2ea66e02194, owner 13:16 / 13:25 holds) 38, candidate sections 34, link rule gap 33, joint links info 30, boxed notation 20, pool designer 19, not drawn 9, held unquantified 6, datum 5, register 2, open-high detail 5 | none computed |
| C owner-gated | 10 | note-9 anchorage / development outside the starter group (owner 2026-10-29 option B, DGP-T373-LAP): 7 beam end anchorages, 3 ground-beam development lengths | none computed |
| D computable now | 6 | column main bars whose hold was a held framing member that does not change D_ctrl (T-119 r2) | 412.444444 kg |

Class D fix rows (R-REBAR-POPULATION-1, n x L x d^2/162, the method of every released sibling: COL-GF-08 8 x 4.50 x
1.580247 = 56.888889 = released 56.889 kg; concrete line of each column RELEASED; length = the 4.50 GF storey interval =
height + D_ctrl reconciled with T-119; no lap):

| fix row | column (p.9 mark) | n x d | L m | kg | t |
|---|---|---|---|---|---|
| FR-T639-1 | COL-GF-01 (C4) | 8 x T16 | 4.50 | 56.888889 | 0.056889 |
| FR-T639-2 | COL-GF-02 (C5) | 10 x T16 | 4.50 | 71.111111 | 0.071111 |
| FR-T639-3 | COL-GF-03 (C4) | 8 x T16 | 4.50 | 56.888889 | 0.056889 |
| FR-T639-4 | COL-GF-05 (C2) | 8 x T16 | 4.50 | 56.888889 | 0.056889 |
| FR-T639-5 | COL-GF-09 (C9) | 14 x T16 | 4.50 | 99.555556 | 0.099556 |
| FR-T639-6 | COL-GF-22 (C5) | 10 x T16 | 4.50 | 71.111111 | 0.071111 |
| total | 58 bars | | 261 m | 412.444444 | 0.412444 |

Effect if wired (lane I): released B11 9,375.306 -> 9,787.750 kg (+4.40 %), HELD blank 801 -> 795. The same D_ctrl-settled
reason on 2F-49 / 52 / 55 / 56 and 1F-36 does NOT free them: their concrete lines are HELD (D-39 roof datum, T-256
section conflict) -> class A.

The 6 open-high lines (lows stay HELD lows, 852.618 kg, never summed): east dome ring 144.290 kg (A: ring concrete HELD;
high open by links, hooks, laps / anchorage, side bars [DETAIL]); west ring 63.897 kg (B: links, hooks, laps [B4 /
DETAIL]); DOME-A / DOME-B shells 290.684 kg each (B: shell anchorage into the ring, hoop laps); lintel bars produced
38.762 kg / flagged 24.301 kg (B: bends, extensions, laps of B1 / T1, S1 links not detailed).

## 4. Findings for the Checker / Lead (nothing changed here)

- F-T639-1: 14 RELEASED column main-bar lines (754.723 kg: 1F-31/32/33/39/41/44/47, 2F-50/51/53/54, GF-14/24/30) sit on
  concrete lines that are HELD in the same candidate (bars released ahead of their concrete; the 2F four rest on the
  D-39 roof datum T-297 R2 already named). Proposal: Checker downgrade review under the class A principle.
- F-T639-2: COL-GF-20 / GF-21 (annex) concrete lines are RELEASED while their bars hold the storey interval on owner
  Q-54 B (DG-1033b87f21613d24 STALE, not applied): one datum, two states.
- Binding gap: 203 B lines + 5 C lines have no recorded concrete binding (131 ground-system spans by ledger id, 38
  stair / pool, 37 beam bands, 2 lintel rows); their class rests on their own hold text, which already holds them; if
  their concrete is HELD they are also A. No quantity depends on it.

## 5. Verdict proposals and lessons

No freelancer comparison here (cause census). Verdict proposal for FR-T639-1..6: ENGINE_RIGHT once wired (drawing p.9
counts x printed storey interval, the released method). Proposed lessons-register row (ERS s.7): "A hold on a
neighbouring member is inherited only by the quantities whose inputs it enters: column main bars over the storey interval
do not depend on a framing member whose depth leaves D_ctrl unchanged; the converse check (bars released while their own
concrete is HELD) is run in the same census." Scope: every villa; provenance T-119 r2 + T-638 + this task.

## 6. Tests

tests/t639 (12 + writer): V639 beam by hand (3 T16 / 2 T12 / T8 @ 0.15, N = 36: 25.600 + 9.600 + 18.488889 kg), units /
mirror, adverse: bars on a HELD concrete element refused, lap without an owner rule refused, missing count / length /
diameter refused (never 0), fractional count, unknown hold text, column D refused when the hold enters the length / the
concrete is HELD / T-119 cause open / interval does not reconcile / no released sibling; development villa: 807 classed
once with a cause, nothing computed outside D, D rows recomputed by hand (COL-GF-09 99.555556, COL-GF-22 71.111111,
total 412.444444), outputs current.
