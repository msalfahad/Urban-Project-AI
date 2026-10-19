# T-004a: room label census on Alsenan under ARCH_TAKEOFF_V2.9 (read-only)

Worker 2, 2026-10-19. Diagnostic only: no engine, rule or quantity change. Development villa: not an accuracy claim.
Counts and label classes only (vocabulary codes); no coordinates, no client data.

## Tool

`tools/label_census.py` (new, general: no layer, room or project name in code). For every text inside a plan region
that the V2.9 room vocabulary (`arch_rooms.room_word`) codes as a room, it looks the label up in the run's own outputs
(rooms' polygons, the ARCH_COMPLETENESS_V1 coverage ledger, the unresolved records) and gives one status:
MEASURED (face accounted LINE), HELD (RFI, or the text id named in an unresolved record), UNSUPPORTED (EXCLUDED),
SILENT_OMISSION (in no room, code not on its room, or no ledger record). Undecodable SHX texts are counted
UNREAD_SHX, never guessed. Tests: `tests/t004a_label_census/` (hand synthetic plan, mm / m / rotated 37 deg /
mirrored, planted outside label found; pure census cases for every status, holes, nesting, multi-entry faces,
other-floor rooms, empty input).

## Input and run

Drive "Alsenan chalet project" / "P7757_DXF_COMPRESSED.zip" -> P7757.dxf, sha256 ab54dd55...31cc4 (= SOURCE_MANIFEST),
read outside the clone. `python3 -I tools/label_census.py P7757.dxf --out <scratch>/census.json` on the working
branch fd0d5dd, Python 3.11.17, ARCH_TAKEOFF_V2.9 (about 55 s). Plan frames: SH05 GF, SH04 1F, SH03 2F (T-038).

## Result

41 room labels in the three plan frames, plus 47 UNREAD_SHX texts (font x-arab1b: GF 20, 1F 19, 2F 8).

| Floor | MEASURED | HELD | UNSUPPORTED | SILENT_OMISSION | UNREAD_SHX |
|---|---|---|---|---|---|
| GF | 15 | 1 | 0 | 6 | 20 |
| 1F | 11 | 0 | 1 | 3 | 19 |
| 2F | 2 | 0 | 0 | 2 | 8 |
| total | 28 | 1 | 1 | 11 | 47 |

HELD: the GF GARDEN label inside an EXTERNAL face (RFI). UNSUPPORTED: one 1F VOID label inside the void part of a
room face (excluded, open to below: correct).

## Silent omissions (11, all cause NO_ROOM: the label lies in no room face; no line, RFI or unresolved record names it)

| # | Sheet | Label class (vocabulary code) | Count | Note |
|---|---|---|---|---|
| 1 | SH05 GF | GARDEN (English COURT x2, Arabic courtyard word x2) | 4 | open yards outside the wall network: paving / landscape scope never reported |
| 2 | SH05 GF | POOL (English) | 1 | pool space in no face; the pool's floor and finishes are not reported by the architectural route |
| 3 | SH05 GF | BATHROOM (the Arabic word for swimming pool) | 1 | same pool; V1 vocabulary reads the Arabic "swimming pool" as BATHROOM (T-034's V2.10 types it POOL) |
| 4 | SH04 1F, SH03 2F | ROOF | 4 (2 + 2) | roof areas of the floor below, drawn outside the upper floor's walls: roof waterproofing / insulation / tiles have no record on these plans |
| 5 | SH04 1F | VOID | 1 | a second void label outside every room face |

## Proposed fix tasks (for the lead)

1. **Labels in no room are reported** (general, every villa): a new method piece that turns every vocabulary label
   lying in no room face of its floor into one HELD record (reason LABEL_WITHOUT_SPACE, with sheet, label class and
   floor), never a silent drop; fixture: hand plan with a labelled yard and roof outside the walls. Rule UP-QTY-STATUS-001.
2. **Roof areas from upper-floor plans** (ROOF labels outside the upper floor's walls): decide where roof finishes are
   measured (the floor below's slab outline minus the upper floor's footprint, or the roof plan); likely an owner
   question on the source of truth before code.
3. **External yards** (COURT / courtyard / GARDEN outside the walls): reported as external spaces (plot minus the
   building footprint) for paving and landscape, HELD until the plot outline is read.
4. **Pool label** joins T-057 (pool check list) and T-034 (pool vocabulary): the pool space must be named once in the
   architectural output.
5. **47 Arabic texts in x-arab1b** stay unread: x-arab fonts are UNMAPPED (no public glyph table); T-047 covers
   keyboard-mapped SHX only, so these labels need their own decoding task or the owner's typed list.

## Verdict proposals

No freelancer quantity is compared here. The 11 omissions are ENGINE gaps found from the drawing (labels present,
outputs silent): proposed status UNRESOLVED until fix task 1 lands (then HELD by construction).
