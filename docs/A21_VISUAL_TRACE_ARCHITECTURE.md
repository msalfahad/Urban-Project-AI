# A21 Visual Trace and Source Sufficiency Architecture

Status: hardening after `A21_VISUAL_TRACE_AND_SOURCE_SUFFICIENCY_01`.
Code: `research/a21_trace_sufficiency_01/`. Tests: `tests/test_a21_trace_invariants.py`.

**Agents extract and explain. Code calculates. Humans approve. Database remembers.**

## 1. The problem this layer solves

Two frozen presentation experiments established that better pixels do not
create missing construction information. What remained was:

- **source sufficiency** — a case can legitimately need a sheet its packet
  omitted (DEV-02, DEV-03), and the resulting UNKNOWN is indistinguishable
  from a real one;
- **evidence traceability** — a correct number attached to the wrong wall is
  worthless, and no reader output could be pointed at on the drawing;
- **missing QS inputs** — the drawing establishes geometry, not every input a
  quantity needs.

## 2. Source sufficiency: two paths, conservative union, two records

```
SHEET_INDEX (all sheets, upright, hashed, per-sheet inverse transform)
        │
        ├── PATH A  DOCUMENT_GRAPH   deterministic: floor identity, facade
        │                             direction, roof relationship, vertical
        │                             condition, schedule existence
        └── PATH B  VISUAL_PREREAD   sealed reader: sheet titles, markers,
                                      cross references. Measures nothing.
                          │
                          ▼
              CASE_SOURCE_REQUIREMENTS   union of justified REQUIRED sheets,
                                          never a vote; disagreement preserved
                          │
          ┌───────────────┴────────────────┐
          ▼                                ▼
CONTROLLER_SOURCE_REQUIREMENTS    A21_READER_SOURCE_MANIFEST
  every reason, every pre-read      sheet id, file, page id, hashes,
  interpretation, every             document type, image size,
  disagreement. NEVER mounted.      available / missing. Nothing else.
```

Why two records: the first packet built in this phase told the reader which
sheet drew the curved stair and which dimensions to look for. That is the
answer wearing a source's clothes. A shingle screen over every reader-visible
file now fails the build if any pre-read sentence survives (`reader_manifest.py`).

Missing sources are reported to the reader as **document types**
(`STAIR_SECTION_DETAIL`), never descriptions ("the curved main stair detail"),
for the same reason. `SOURCE_SET_INCOMPLETE` is recorded before any reader
runs and means one thing only: the missing information cannot be silently
replaced. It does not make visible geometry unknown.

What the document path cannot do, and says so: resolve which section cuts
which room. The CAD decode carries no sheet titles and no section markers, and
long-line candidates are indistinguishable from plot boundaries. So when a
height is needed both sections are raised. Omission is the asymmetric risk.

## 3. Traces

A trace is a claim with a place. Every trace carries identity
(`TRACE_ID, CASE_ID, SHEET_ID, SOURCE_FILE_HASH, SOURCE_PRESENTATION_HASH,
SOURCE_COORDINATE_SYSTEM, ORIGINAL_PDF_PAGE`), geometry in processed-sheet
pixels, and the sheet's stored inverse transform. The register projects every
geometry back to the original PDF page.

**A printed dimension is separate evidence from what it measures.** A
`PRINTED_DIMENSION` carries `TEXT_BBOX`, `DIMENSION_LINE_TRACE`,
`EXTENSION_LINE_A/B`; the geometry it supports names it in `SUPPORTED_BY`.
The extension lines are the point — they show which faces the dimension runs
between, and in CASE-4 three dimensions passing near the stair turned out to
terminate on room walls, not stair faces.

### 3.1 Three statuses, never collapsed

| status | values | meaning |
|---|---|---|
| `TRACE_RECORD_STATUS` | VALID / INVALID | is the record well-formed |
| `TRACE_LOCATABILITY_STATUS` | LOCATABLE / NOT_ESTABLISHED | does it carry drawable geometry |
| five semantic statuses | ESTABLISHED / NOT_ESTABLISHED / AMBIGUOUS / NOT_APPLICABLE | GEOMETRY, IDENTITY, DIMENSION, TREATMENT, PARAMETER |

A VALID, NOT_ESTABLISHED trace is a legitimate result: "there is something
here I cannot place". The register reports `VALID_TRACE_RECORDS`,
`LOCATABLE_TRACES`, `NON_LOCATABLE_VALID_TRACES`, `INVALID_TRACE_RECORDS`
separately. One established semantic field never establishes another.

### 3.2 Cross-sheet relations

Two sheets whose projected graphics differ are not thereby contradictory. An
`ESTABLISHED_CROSS_SHEET_CONTRADICTION` needs: both claims traced, both sheet
identities established, `SAME_PHYSICAL_LOCATION_ESTABLISHED`, the drawings
expected to describe the same condition, and the conditions incompatible.
Anything less is `POTENTIAL_CROSS_SHEET_CONTRADICTION`. A plan labelled VOID
against a continuous slab line on an elevation is POTENTIAL: an elevation
projection can hide an internal void.

### 3.3 What the mapping tests prove, and do not

| test | proves |
|---|---|
| `COORDINATE_ROUNDTRIP_PASS` | the transform inverts at ~0.0 px |
| `SOURCE_INK_CORRESPONDENCE_PASS` | random processed ink lands on the same original ink, at equal physical area |
| `TRACE_COORDINATE_MAPPING_PASS` | the coordinates readers actually produced land on the same ink |

None of them proves `SEMANTIC_ACCURACY`, `GEOMETRY_CORRECTNESS` or
`MEASUREMENT_CORRECTNESS`. A trace can map perfectly to ink and still identify
the wrong architectural object. "Trace accuracy" is never used to mean both.

## 4. Overlays

Drawn from stored coordinates only. A trace with no geometry is listed as
undrawable, never invented onto the sheet. Line style plus a short id carries
the meaning; colour is redundant. Dimension traces draw all four geometries,
extension lines thinner. The renderer is deliberately dense and is frozen for
the experiment; `FOLLOW_ON_DESIGN_ITEM = TRACE_REVIEW_UI`.

## 5. Parameters and the three quantity states

A parameter is UNKNOWN because **no currently accepted project source or
owner project input establishes it** — a property of the project's evidence,
not of any experiment. Reader history is validation evidence only.

A quantity inherits the **weakest** provenance among its inputs:

| state | when |
|---|---|
| `SOURCE_ESTABLISHED_QUANTITY` | every input from a permitted project source |
| `OWNER_PARAMETRIC_QUANTITY` | geometry from source, a QS input from the owner |
| `PROVISIONAL_DEFAULT_QUANTITY` | any input is a temporary default |
| `NOT_ESTABLISHED` | any input unknown |

The constructor makes the dangerous states unrepresentable: a `DRAWING`
parameter cannot be owner-confirmed, a default cannot be unmarked. An owner
value is stored `OWNER_PROJECT_INPUT / PROJECT_INPUT / ESTABLISHED_FOR_PROJECT`
and never relabelled drawing-derived. Changing a parameter recalculates
dependent arithmetic; the trace-derived geometry hash does not move and no
reader reruns (`recalculation_test.py`, synthetic values only).

## 6. Generic guards

- `source_access_guard.py` — every reading's cited and mentioned sheets
  checked against its manifest; verdict stamped into the register.
- `reader_manifest.py` — shingle screen: no pre-read sentence in any
  reader-visible file; question text exempt.
- `phase_registry.py` / `PARTIAL_STATE_FREEZE` — raw outputs frozen by hash
  before any validator change; a validator defect is fixed generically and the
  FINAL validator runs over every frozen raw output. Raw outputs are never edited.

## 7. Recorded limitations

- `SUBSET_SELECTION_PROTOCOL_STATUS = E1_4_INFLUENCED_MEMBERSHIP_UNCHANGED`.
  Three subset clauses consulted E1.4 boundary classifications; no quantity,
  no prior A21 result; declared-category re-derivation gives the same four
  cases. The selection is not described as blind. E1.4 is sealed from
  everything downstream.
- The pre-read stage is itself a reader. Its output decides access, never
  interpretation, and its interpretations live only in the controller record.
