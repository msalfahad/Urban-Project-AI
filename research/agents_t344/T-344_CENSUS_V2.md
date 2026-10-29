# T-344: label census V2 (compound vocabulary + merged label binding)

Worker 2 (lane A), 2026-10-29 16:43-17:40 UTC. Gate 1 (M2, silent omissions). Tooling only: no engine module, rule,
knowledge file, candidate line or released line changes; `tools/label_census.py` (URBAN_LABEL_CENSUS_V1, V2.9) is
untouched and is called by the new tool. No client name, coordinate or label text is committed.

## What the new tool does (`tools/label_census_v2.py`, URBAN_LABEL_CENSUS_V2)

1. Types every text with ROOM_VOCAB_V2 (`engine/source/room_vocab.py`: compound phrase before the bare word). A label
   V1 types and V2 holds (a compound naming no room type, e.g. the Arabic "car wash") stays in the census as HELD
   (VOCAB_V2_HELD_COMPOUND), never dropped. V1 code and RETYPED are recorded per label.
2. Applies a merged label-binding ledger (R-T342-BIND-1; for Alsenan research/agents_t342 LABEL_BINDING_T342.csv +
   SCOPES_T342.csv on CANDIDATE_V3022_T342.json). A label the V1 logic leaves SILENT_OMISSION becomes
   ACCOUNTED_BY_BINDING (binding BOUND / PARTIAL / MISSING / NOT_APPLICABLE, duplicates counted once, open scopes listed
   with quantity or bound) only when the row passes every check: same floor and V2 code; face with scopes; row binding
   = the binding its scopes give; BOUND scope has lines, NOT_APPLICABLE has evidence, MISSING has unit and a non-zero
   quantity or bound; row lines = its BOUND scopes' lines (else REFUSED_NAME_ONLY); every line exists in the candidate
   (REFUSED_UNKNOWN_LINE), has its own source entities (else REFUSED_NAME_ONLY), is not a 0 line; a duplicate points to
   a first label of the same face and code that the census itself accepts. Anything else stays SILENT_OMISSION with
   the refusal printed. A label with no row stays SILENT_OMISSION.

## Alsenan result (acceptance a), own run on Drive "Alsenan chalet project" / P7757_DXF_COMPRESSED.zip

P7757.dxf sha256 ab54dd55.. (matches T-342), ARCH_TAKEOFF_V2.9 room set, one architectural run:

| | V1 tool (unchanged) | V2 tool |
|---|---|---|
| labels | 41 | 41 (same text ids; no label added or dropped by V2) |
| MEASURED / HELD / UNSUPPORTED | 28 / 1 / 1 | 28 / 1 / 1 |
| SILENT_OMISSION | 11 (all NO_ROOM) | **0** |
| ACCOUNTED_BY_BINDING | - | **11**: BOUND 3 (roofs AT216, AT220, AT379), PARTIAL 1 (AT19 pool), MISSING 1 (AT21 court), NOT_APPLICABLE 1 (AT225 1F opening), 5 duplicates counted once (AT20, AT22, AT39, AT40, AT385) |
| UNREAD_SHX | 47 | 47 |

- The V1 output of the same run is byte-identical to the V1 tool run alone (sha256 cba0762b0cde2eca..), and its labels
  equal the committed T-342 census row for row.
- Only one label changes type: AT19, V1 BATHROOM (first word of the Arabic compound "swimming pool") -> V2 POOL. With
  the V1 code the ledger's POOL row is refused (REFUSED_CODE), so the census could not account for it by name.
- Open scopes the census now prints instead of "silent" (from the merged ledger, not re-measured here): pool membrane
  29.582 m2, screed 1.525 m3, water-face finish blank (bound 21.309 m2); court 7 pieces 168.843 m2 (interlock 119.542,
  porch 10.679, E1 treads 3.359, risers 1.960, landing 5.179, side walk 21.014, pool deck 7.109). These are BOQ
  integration gaps (T-310 FILL, new outdoor-floor lane I row T-343), not silent omissions.
- Committed: research/agents_t344/CENSUS_V2_ALSENAN.json (ids, codes, statuses, bindings; no label text).

## Tests

tests/t344_label_census_v2: hand villa (not Alsenan; mm, metres, mirrored) with hand quantities (pool walls 3.584 m3,
base 2.640 m3, membrane 22.40 m2, court paving 49.44 m2); normal case; adverse: bare-word bathroom inside a pool
compound (refused, and its duplicate), name-only line (two forms), unknown line id, no candidate, MISSING as 0 /
unquantified, 0 line, NOT_APPLICABLE without evidence, row binding overstating its scopes, duplicate of another face,
wrong floor, MISSING_NO_FACE, a genuinely unbound label (stays SILENT_OMISSION); V1 output unchanged and inputs not
mutated; CSV ledger round trip; one DXF run (pool compound outside every room). test_alsenan.py: offline rebind of the
committed T-342 census equals the live run label by label.

## Lessons register row (proposal)

"A census line is accounted for only by a binding it can check (same floor and compound-read code, lines that exist
and carry their own source entities, missing scopes with a non-zero quantity or bound); a vocabulary change never
removes a label from the census" (scope: every villa; provenance T-344, builds on T-342).

## Uncertain / not done

- The ledger is research data (T-342); the tool checks its consistency and the candidate extract, it does not re-derive
  face geometry (that is R-T342-BIND-1's own step; the Checker verified it in T-342).
- `rebind()` on a saved V1 census cannot see texts only V2 would type (reported NOT_READ); the drawing run can.
