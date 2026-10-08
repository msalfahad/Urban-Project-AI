# D1.1 stirrup / link core-path authority audit

**Round:** `D1.1` revision 2 · **Policy:** `STIRRUP_AUTHORITY_AUDIT_V1` · **Baseline:** HEAD `59f2083` · **Built by** `build_d1_1_stirrup_audit.py` (blind, byte-identical rebuild)

S4, S5, S6, S4.1, S6.1 and S5.1 are unchanged. Every change below is an explicit CORRECTION_ERRATA record. No
frozen file was edited, and PRE-S7 was not started.

**Order of authority.**
- Revision 1 (`35567e2`) was built before the owner's authority decisions were recorded.
- Revision 2 is built on top of the frozen AD1 record (`research/ad1_authority_decisions/`). AD1's manifest is
  hash-checked together with the six stage manifests before anything is read.
- The earlier Q2 answers are recorded in AD1 as the assistant's own engineering analysis. They are not promoted to
  engineer or source authority, and no confidence value is carried.
- AD1 applies here through four decisions:
  - AD-4: hook shape only, extension blocked;
  - AD-5: no inherited GB < 2.5 m diameter;
  - AD-6: concentrated-reaction applicability;
  - AD-8: 5Ø8/m is rate / count only.

## Conclusion

**The sharp-corner link path is a `MODELLED_POLYGONAL_EQUIVALENT`. It is not a lower bound.** All the link mass
released in D1 is retracted to BLOCKED_UNQUANTIFIED:

| Stage | Link kg released in D1 | Retained | Corrected (moved to modelled / QA) |
|---|---|---|---|
| S6.1 | 1332.26 | 0.00 | -1332.26 |
| S5.1 | 67.26 | 0.00 | -67.26 |

Every other D1 release is kept, because none of them depends on bend geometry:
- S6.1: B3 WITH STAIR and B26 longitudinal bars 372.61 kg, the B26 planted-column extra 12.01 kg, and
  5 new stirrup counts.
- S5.1: through-support portions 25.60 kg.

AD-6 then retracts 47.37 kg of frozen S5 bars carried into S5.1. These are spans GSO-142-7D8-1 and
GSO-15D-7C8-1, where a beam frames in between the supports and one length basis leaves no project detail
(`research/ad1_authority_decisions/05_S5_AD1_CORRECTIONS.csv`).

| | D1 known | After the link errata | After the AD-6 errata (corrected known) |
|---|---|---|---|
| S4.1 | 3629.60 | 3629.60 | 3629.60 |
| S6.1 | 5347.03 | 4014.77 | 4014.77 |
| S5.1 | 1550.85 | 1483.60 | 1436.23 |
| **Combined** | **10527.48** | **9127.96** | **9080.60** |

## The mathematics

Take a closed link whose centreline envelope is W x T, with four 90-degree bends of centreline radius R:

    L_rounded = 2W + 2T - (8 - 2 pi) R = L_sharp - 1.7168 R

Per corner, the sharp path counts 2R and the arc is (pi / 2) R. So L_rounded < L_sharp for every R > 0. Equality
holds only at R = 0, and no bar can be bent to R = 0.

Proving any lower bound would need all three of these:
1. R, or an upper bound on R, from a project source;
2. an envelope that is exact or a minimum;
3. the deficit deducted.

The hooks and the closing overlap could make up the difference, but their lengths are not in the issued set. Using
them is exactly the unsupported premise of D1.

The cover is a second, independent reason:
- p.8 note 22 prints a minimum cover (>= 2.5 cm, >= 7 cm against soil).
- So b - 2c and h - 2c are the largest the link can be, not the smallest.

## Source search (4055 DXF texts / attributes / dimensions, 63 legacy-Arabic notes decoded, the 24 p.8 notes, OCR of pp.9-16, the drawn link geometry)

- **Bend radius / diameter / centreline bend geometry: not located.**
  - The issued p.13 and p.15 link sections draw every corner bent: 4 straight sides plus 16 short chords, i.e. 4
    chords per corner. So the drawing itself shows rounded links.
  - No radius is printed. The DXF has 0 radius or diameter dimensions.
  - P8-N03 says "do not scale the drawings", so the drawn radii cannot be measured.
- **Hook angle / length / extension: not located.** The hook is drawn; the project rule register records
  HOOKS_AND_BENDS = NO_PROJECT_SOURCE.
- **Closure / lap of links: not located.** The only lap rule in the set is for slab temperature bars (p.15: 40 x DIA).
  Note 9 (70D / 40D) applies to starter bars.
- **Link fabrication or bending note: none.**

See `01_SOURCE_SEARCH.md`.

## What stays valid (`05_TOPOLOGY_COUNT_DIAMETER_REGISTER.csv`)

For every stirrup set, A topology, B count and C diameter keep their own states, and only D cut length is blocked:
- **Topology:** 180 sets in total: 168 single closed links, 11 STR2 (4 legs) and 1 STR3
  (6 legs, SB2, still a source conflict).
  - Topology is established on 162 sets.
  - On 18 ground-beam sets it is CANDIDATE_ONLY: the span's loaded case has no project detail (AD-6), so the
    p.13 single link holds only for the unloaded candidates.
- **Hooks:** 151 sets carry a drawn hook shape (SOURCE_EXPLICIT_SHAPE_ONLY). The hook extension is
  BLOCKED_UNQUANTIFIED on all 180 (AD-4).
- **Counts:** 116 sets carry a released count. Each is a rate x run count only; it never gives a cut length
  (AD-8).
- **Diameters:** 149 sets carry a source diameter.

## Files

| File | Content |
|---|---|
| `01_SOURCE_SEARCH.md` | what was searched and what each search returned |
| `02_STIRRUP_PATH_AUDIT.csv` | every D1 released row (S6.1 and S5.1): link paths retracted to modelled, other releases kept, with the reason |
| `03_S6_1A_CORRECTIONS.csv` | S6_1A_STIRRUP_AUTHORITY_CORRECTION errata (88 rows) |
| `04_S5_1A_CORRECTIONS.csv` | S5_1A_STIRRUP_AUTHORITY_CORRECTION errata (6 rows) |
| `05_TOPOLOGY_COUNT_DIAMETER_REGISTER.csv` | per stirrup set: topology, count and diameter kept; cut length and mass blocked |
| `06_CORRECTED_RELEASE_SUMMARY.json` | original, correction and corrected totals; conservation; flags |
| `07_PROVENANCE.jsonl` | one line per audited row and per correction |
| `D1_1_FREEZE_MANIFEST.json` | hashes of the code, inputs and outputs |
| `TEST_RUN.md` | the targeted and full-suite runs (written after the freeze) |

## For the owner

The issued set will not support link mass until it states a bend radius (or a maximum), the hook extension and
closure, and the cover as built rather than as a minimum. If an engineer supplies those facts as a versioned claim,
a later round can release a proven lower bound.

The same minimum-cover reading also affects the cover-reduced footing lengths in frozen S4 (span - 2 x 70 mm). That
is outside this audit's scope and was not changed; it is raised as a question.
