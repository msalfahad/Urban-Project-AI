# AD1: owner authority decisions, recorded before D1.1

**Round:** `AD1` · **Policy:** `AUTHORITY_DECISIONS_V1` · **Recorded:** 2026-10-08 · **Baseline:** `cbcbb36` · **Built by** `build_ad1_authority_decisions.py` (blind, byte-identical rebuild)

S4, S5, S6, S4.1, S6.1 and S5.1 are unchanged. Every frozen manifest was hash-checked before anything was read.
D1.1 is rebuilt on top of this round.

## Where the earlier Q2 answers stand

The Q2 answers were the assistant's own engineering analysis, recorded here as `CLAUDE_ENGINEERING_ANALYSIS`.
- They are **not** answers from the project engineer or consultant.
- No engineer confirmation exists for them.
- They are never promoted to a `PROJECT_ENGINEER_CLAIM` or to project-source authority.
- No confidence percentage from that analysis is carried anywhere.

The only engineer claim on record is `PEC-CLAIM-2026-10-08-01`. It says only that the information sits in the
issued set, and it authorises no assumption.

`02_REJECTED_ANALYSIS_VALUES.csv` names 14 analysis or code values that the decisions refuse. Each is QA only and
is never a quantity basis.

## The nine decisions (`01_AUTHORITY_DECISIONS.json`)

| | Topic | Ruling |
|---|---|---|
| AD-1 | BOXED | existence and the vector-proven inverted U are SOURCE_EXPLICIT; hooks NOT_ESTABLISHED; 3+n PROJECT_PATTERN_ONLY; diameter SOURCE_EXPECTED_NOT_LOCATED; blank FN cell UNRESOLVED; kg blocked |
| AD-2 | 70Ø / 40Ø | starter / development context only; no beam or ground-beam anchorage rule |
| AD-3 | Beam end bends | a drawn bend gives shape; an undimensioned leg gives no length; no 12Ø, beam depth or practice |
| AD-4 | Stirrup hooks | drawn angle / topology is shape only; extension blocked; no 20d; code values QA only |
| AD-5 | GB < 2.5 m | stirrup diameter and rate SOURCE_EXPECTED_NOT_LOCATED; Ø8/15 never inherited |
| AD-6 | WITHOUT CONCENTRATED LOAD | a beam framing in between the supports, or a planted column, is an ENGINEERING_DERIVED_CONCENTRATED_REACTION |
| AD-7 | FOLLOW ARCH | levels give bounds only; no exact depth; no 0.9-1.0 m; 10 cm plain concrete is not RC depth |
| AD-8 | Continuous beams | 0.22 Ln kept where printed; 0.3 Ln2 and 0.15L unresolved; no NTS scale; top / hanger roles separate; 5Ø8/m is rate / count only |
| AD-9 | Side bars | classified as side / skin only where the MIDDLE REINF. field and notes support it; no ceil(h/s) - 1; count and kg blocked |

## What the decisions change in the frozen releases (`03_COMPLIANCE_REGISTER.csv`)

**Known steel retracted: 47.37 kg on S5, carried into S5.1 (AD-6).**
- On GSO-142-7D8-1 and GSO-15D-7C8-1 a ground beam frames into the span between its supports.
- The bars released there were the ones the <2.5 m and <5 m sections agree on. The <5 m section is titled 'without
  concentrated load'.
- On at least one length basis, only the <5 m section applies. For that loaded span there is then no project
  detail, so the bars are not candidate-invariant.
- 6 components are moved to QA_ONLY / BLOCKED_UNQUANTIFIED in `05_S5_AD1_CORRECTIONS.csv`.
- S5.1 known goes from 1550.85 to 1503.49 kg before the D1.1 link errata.

**Authority-state errata, 0 kg (107 rows in `04_AUTHORITY_STATE_ERRATA.csv`):**
- BOXED: hooks NOT_ESTABLISHED (was "no hooks"), 3+n PROJECT_PATTERN_ONLY, blank FN cells UNRESOLVED.
- 14 CB end-support legs: length NOT_ESTABLISHED (was "derivable from the beam depth"), shape only.
- 28 ground-beam spans: load state ENGINEERING_DERIVED_CONCENTRATED_REACTION. Of these, 19 have a
  different candidate-detail set (`06_GB_CONCENTRATED_REACTION_REGISTER.csv`).
- 7 continuous beams: the MIDDLE REINT. token is classified as side / skin reinforcement (count and kg stay
  blocked).

**Already compliant:**
- AD-2: note 9 stays starter-only.
- AD-4: link hooks shape-only; the hook-reliant D1 link path is retracted by D1.1.
- AD-5: GB < 2.5 m stirrups blocked.
- AD-7: no FOLLOW ARCH depth published.
- AD-8: 0.22 Ln kept; 0.3 Ln2 and 0.15L add nothing.
- AD-9: no side-bar count rule.
- The B26 planted-column extra, B3 / B26 base bars, the S5.1 through-support runs and the CB7 counts are untouched.

## Files

| File | Content |
|---|---|
| `01_AUTHORITY_DECISIONS.json` | the nine decisions, the Q2 analysis record, the engineer-claim scan, the policy |
| `02_REJECTED_ANALYSIS_VALUES.csv` | analysis / code values the decisions refuse |
| `03_COMPLIANCE_REGISTER.csv` | every decision checked against every frozen stage |
| `04_AUTHORITY_STATE_ERRATA.csv` | 0 kg facet-state corrections |
| `05_S5_AD1_CORRECTIONS.csv` | CORRECTION_ERRATA for the AD-6 kg |
| `06_GB_CONCENTRATED_REACTION_REGISTER.csv` | every ground-beam span: load state, candidate details before / after |
| `07_AD1_SUMMARY.json` | counts, kg, conservation, flags |
| `08_PROVENANCE.jsonl` | one line per decision, rejected value, erratum and correction |
| `AD1_FREEZE_MANIFEST.json` | hashes of the code, inputs and outputs |
