# T-245: one project identity and one revision set in the candidate; the real candidate exports (integration package)

Lane I, worker 3, 2026-10-25. INTERNAL REVIEW CANDIDATE. Opt-in ARCH_TAKEOFF_V3.0.16 = V3.0.15 + one identity step;
released default unchanged (ARCH_TAKEOFF_V2.9 + route G); nothing released, nothing promoted, no quantity moved.
Integrates: T-235 (export, MERGED d7d232b9), T-270 (V3.0.15, MERGED 04d34378).

## 1. Cause of the run-to-run BOQ_LINES.json difference (owner 04:38: cause first, named)

Physical question: what identifies the drawing a line rests on? Its content (sha256), not the name of the local copy.

Up to V3.0.15 every structural-route line carries `source.documents[] = {"file": <local copy's file name>, "sha256"}`.
The file name is not a csv column, so BOQ_LINES.csv stays byte-stable while the json changes with whatever name the
agent gave its decoded copy (`agent_env.sh decode` refuses a name with a space, so copies were named differently).
Proof, on this run's V3.0.14 / V3.0.15 lines (own run, section 3), renaming only the structural copy in
source.documents[].file reproduces every hash the Checker and workers recorded, exactly:

| local name of the structural copy | V3.0.14 json | V3.0.15 json | seen in |
|---|---|---|---|
| `ST7757 dxf.dxf` (Drive title) | 8f9287d0 | ec733948 | this run |
| `ST7757_dxf.dxf` | 48d7d54b | e54cae74 | Verifier 01:43, T-270 r2 |
| `ST7757.dxf` | 98a68b72 | 53450a1f | T-240, Verifier 04:15 |

Not the cause (checked): line order, float formatting, set order, timestamps or paths (two independent T-167 chains in
this run, two local names, are identical line by line once the file name is removed: V3.0, V3.0.3, V3.0.4, 1,696 /
3,132 / 3,132 lines, 0 other differences; no path, time or run id in any line; every embedded ledger sha256 equals
the file on the head, 17 ledgers).

Fix (at the cause, not by suppression): V3.0.16 writes the declared document TITLE of the revision set for each sha256
(`source.documents[].file`), and keeps the local names as run metadata in `V3_0_16_RUN.json`
(`run_metadata.local_file_names_replaced_by_declared_titles`). The three V3.0.15 jsons above all give the SAME
V3.0.16 json `3181cf12`. The export binds verdicts to the sha256 of the canonical line content
(`lines_sha256`, boq_line.dumps), never the raw file bytes; a genuine quantity / status / drawing change still changes
it (tests).

## 2. One identity, one revision set (owner 23:49 (a), 23:57 (4))

Before: 3,120 lines `ST7757 villa (structural set)` / set `297e913d` (structural file alone) and 579 lines
`development-villa-t131` / set `db7b3eb8` (plan file alone) -> export REFUSED (probe 10).

V3.0.16 inputs (URBAN_V3016_INPUTS_V1, research/agents_t245/t245_inputs.py), every value from source evidence:
- project id `development-villa-t131` (the id every V3.0.x project input of this villa is already bound to); evidence:
  the owner's one-folder-per-project Drive folder holds both files; both titles carry the same drawing number.
- documents: ARCHITECTURAL `P7757.dxf (P7757_DXF_COMPRESSED.zip)` sha256 ab54dd55..., revision UNCONFIRMED (no
  revision mark or issue date in the DXF model-space text: own search for REV / DATE / ISSUE, none; PDF title blocks
  not read); STRUCTURAL `ST7757 dxf.dxf` sha256 9f9d1179..., revision UNCONFIRMED (D-61 issue-date conflict).
  No invented revision, no "approved set": a file sha256 proves the file used, not its approval.
- routes: each route identity named with the files it was computed from; their sets recomputed and checked.

After: every line `{project_id, revision_set_sha256 5e369075..., route {...}}`; line ids, order and every other field
byte-identical to V3.0.15 (asserted on every run: body sha256 17d2875d...); totals moved by code: none.
Refused: a line of another project or of a changed drawing (no declared route), two revisions of one sheet, a document
no route uses, a route naming an undeclared file, a line on an undeclared file, UNCONFIRMED without its reason,
"new project", and in the export lines of two ids (probe 10 unchanged) or an identity record of another set.

## 3. Run on the development villa (own, Python 3.11.17, Drive copies)

Inputs: Drive 'Urban BOQ private data' / project folder: P7757.dxf from P7757_DXF_COMPRESSED.zip (ab54dd55),
'ST7757 dxf.dxf' (9f9d1179). T-167 chain: V3.0.4 csv d86de34a (= T-270). Runner
`research/agents_t245/v3016_run.py <plan> <structural> --out <dir> --t167 <t167 dir>`:
V3.0.14 csv ad893df9, V3.0.15 csv a4dc01dd (= T-270 r2, 3,699 lines), V3.0.16 json 3181cf12, csv a4dc01dd (no csv
column changes), identity json 6f1676c2, diff csv 5fa25da3; diff vs V3.0.15: IDENTITY_ONLY 3,699; vs V2.9:
SAME_QUANTITY 758, QUANTITY_DIFFERS 832, NOT_IN_RELEASED 2,109 (as V3.0.15). A second, separate V3.0.16 run (new
process) gives byte-identical V3_0_16_BOQ_LINES.json / .csv / IDENTITY / DIFF and an identical export (all four
files); renaming the structural copy (the three names of section 1) leaves V3.0.16 at 3181cf12.

Export (one command):

    python3 -I tools/boq_export_v1.py --lines <dir>/v3016/V3_0_16_BOQ_LINES.json \
        --candidate-version ARCH_TAKEOFF_V3.0.16 --identity <dir>/v3016/V3_0_16_IDENTITY.json --out <out>

-> BOQ.csv 7d56e5ed, BOQ.xlsx ae460744, BOQ_TRADE_SUMMARY.csv 20b5261f, semantic be907110; 3,699 rows: VERIFIED 0
(no promotion: no V2 record exists yet), MEASURED UNVERIFIED 1,047, HELD 1,878 (blank), EXCLUDED 774, UNMEASURED 0;
manifest `project_identity` + XLSX Manifest sheet state both revisions UNCONFIRMED with why, the INTERNAL REVIEW
CANDIDATE label and the binding rule.

## 4. Downgrade-only records (T-245 (f), (f2))

`boq_export_v1.py downgrade-add` (Checker routines only) and `--downgrades` (URBAN_CHECKER_DOWNGRADE_V1_SET). A record
binds project, revision set, line ids, unit and the candidate quantity it downgrades; it carries no quantity of its own
(a record with checker_qty is INVALID). VALID + unresolved -> each line HELD ("HELD: ..." / "CONFLICT: ..." with the
basis label, default UNSUPPORTED BASIS), a VERIFIED / COMPONENT verdict on it shown OVERRIDDEN; the candidate number
only in BOQ_AUDIT_UNSUPPORTED_BASIS.csv / sheet "Audit (unsupported basis)"; candidate lines unchanged; an unlisted
line untouched; another project / missing line / changed quantity / resolved -> not applied, listed. No records are
written by this package (a worker never grades). For the Checker, lines found in the V3.0.16 candidate: 2F columns
STR.CONC.COLUMN floor 2F, 8 lines, 3.528 m3; ST-03 = L-061e18cf35a4b6b33d68 (GROUND flights, PROVISIONAL 0.948267 m3);
the 24 exterior ground beams (11.93 m3 of the 58 GROUND lines, 27.3649 m3) and the 7 annex columns (3.7125 m3) by the
element lists of the T-254 row (not re-derived here).

## 5. Not done / limits

- Part (d) metric tons as the DEFAULT export unit: NOT in this package (droppable by the owner's terms): making it the
  default changes the byte output of every existing export and the t235 / t273 expectations; the opt-in
  `--contract-units` view (T-273) works on the real candidate. Separate row proposed.
- The architectural revision is UNCONFIRMED because the DXF prints none as model-space text; the PDF title blocks
  (sheet parts on Drive) were not read for a revision.
- Line ids of structural-route lines still derive from the route id (kept on purpose: no churn).

## 6. Rule, tests, lessons

Rule (general, any villa): a BOQ is ONE project identity over ONE revision set of every drawing file it rests on,
each with its own revision (PRINTED or UNCONFIRMED with why); a drawing is identified by its content sha256, never by
the local copy's name; verdicts bind the canonical line content.
Tests `tests/t245_project_identity` (villa N245 / N245D by hand; normal: one identity, line ids / quantities / held
unchanged, two local names -> identical json, export with identity, a verdict made on run 1 binds on run 2; adverse:
another project, changed drawing, two revisions of one sheet, unused / undeclared documents, missing reason, new
project, export of two routes refused (probe 10), identity record of another set, one quantity change -> STALE;
downgrades: held not measured, unlisted untouched, verified component overridden, invalid / other project / stale /
missing / resolved not applied, the four owner-named quantities HELD with their numbers only in the audit file) +
BOQ_FAMILY_MASTER 1.11.0 tests.
Lessons row (proposed, ERS s.7): 2026-10-25 | the candidate json changed run to run while the csv was stable |
the local copy's file name was written into every line's source documents | identify a drawing by sha256 and its
declared title; keep local names as run metadata; bind verdicts to canonical content | tests/t245_project_identity |
PROPOSED.

## 7. Rework r2 (worker 3, 2026-10-25)

Checker finding F-T245-01 (Gate B 07:58, minor): on the real candidate the (STR.CONC.COLUMN, 2F) group is 14 line
ids for 3.528 m3, some NOT_APPLICABLE; a downgrade over all 14 moved one EXCLUDED row to HELD (EXCLUDED 774 -> 773).
Physical reading: an EXCLUDED row (excluded with reason / not applicable with evidence) is not a quantity of the BOQ;
holding it would list a not-applicable element as an open quantity. Fix (`tools/boq_export_v1.py`, `apply_downgrades`):
listed EXCLUDED rows are left exactly as they are (state, reason, no audit row); the record's status names them
("APPLIED (HELD, n line(s); m EXCLUDED row(s) left EXCLUDED)"). The binding check (unit, engine quantity over all
listed ids) is unchanged; an EXCLUDED line carries no quantity, so a record over the whole group still binds.
Test `test_an_excluded_row_named_by_a_downgrade_stays_excluded` (synthetic 2F group 0.360 + 0.720 m3 + one
NOT_APPLICABLE row): the measured rows go HELD, the excluded row is byte-identical, the EXCLUDED count unchanged.
No quantity moved; no candidate line changed. Base 86fdc315 merged; the maps regenerated by the tool as the last commit.
