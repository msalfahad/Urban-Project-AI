# T-066: development project 2, why the DWG -> DXF conversion lost 57 %, and the acceptance check

Worker 1, 2026-10-19. Read-only. Development project 2 is a separate project (owner Q-15 = A): nothing here is mixed
with Alsenan quantities, rules or benchmark data. Source: Drive, development project 2 folder, the `-STR.dwg`
(2,437,120 bytes, sha256 `2635cc50...d00d60b`, AC1021 = AutoCAD 2007 format, same file T-033 audited). The owner's new
DXF is **not yet on Drive** (folder listed 11:27 UTC: 9 files, no DXF), so the check below was run on the converter
outputs only. Every number comes from a command output of this run; counts, type and layer names only (machine-readable
in `T066_COUNTS.json`). Decoders were built outside the clone from release tarballs (0.13.3 tarball sha256
`83f1f6e7...1e8816e` = the pinned source; the binary hash of a local build differs from the registered one, builds are
not byte-reproducible across machines).

## 1. Result in one paragraph

The 27,504 lost entities have **two causes, both in the pinned LibreDWG 0.13.3, none in the drawing**:
**(1) a parser defect**: `src/bits.c:1378-1379` (`bit_read_H`) masks every handle to 16 bits for any DWG older than
R2018 (`handle->value &= 0xFFFF; // cap at 32bit`; the comment says 32 bit, the mask is 16). This DWG has handles up to
0x237FC2 (2,326,466) and 58,125 of its 58,343 objects have 3-byte handles, so 12,567 handle values collide (27,657
objects share them). The DXF writer then cannot resolve the model-space block, writes no ENTITIES and no OBJECTS
section and no EOF, and writes block contents into the wrong blocks. **(2) a DXF writer defect**: every INSERT of an
anonymous dynamic block is written with the bare name `*U` instead of the numbered block name, so 322 references
(190 in model space: 85 room tags, 54 doors, 50 windows, 1 hatch group) point to no block. The drawing itself is
complete: with the one-line mask fix (diagnostic build, never for quantities) the DXF holds **48,574 of 48,576
entities, exact per type and per space**, the 2 missing are Express Tools RTEXT fields in the paper title block, and
model-space LINE length per layer and the vertex extents equal the DWG's. No proxy entities, no OLE objects, no
MLEADER, no images, no XREFs are involved. LibreDWG 0.13.4 removes the mask (its JSON decode is clean) but its
`dwg2dxf` crashes on this file (`double free or corruption (out)`, exit 134). **No open-source route available here
passes the acceptance check**; the owner's AutoCAD export (Q-15 A) is still needed and must pass section 5.

## 2. Per entity type and per space (DWG decode vs DXF)

Reference = `dwgread -O JSON`: its entity counts and entity modes (0 = owned by a block, 1 = active paper layout,
2 = model space) are read from each object's own bits, so they are exact even when handles collide. T-033 split model
space vs blocks through owner handles, which collide; the split below replaces it (for example A-PL-WALL in model
space is 5,026 entities, not about 3,389).

| Type | DWG model | DWG paper | DWG in blocks | DWG total | pinned DXF (BLOCKS only) | lost (pinned) | patched DXF ENTITIES + BLOCKS |
|---|---:|---:|---:|---:|---:|---:|---:|
| LINE | 8,882 | 28 | 8,087 | 16,997 | 4,371 | 12,626 | 8,910 + 8,087 = 16,997 |
| TEXT | 1,827 | 50 | 4,306 | 6,183 | 2,458 | 3,725 | 1,877 + 4,306 = 6,183 |
| POINT | 0 | 0 | 5,802 | 5,802 | 3,806 | 1,996 | 5,802 |
| INSERT | 670 | 4 | 3,627 | 4,301 | 2,248 | 2,053 | 674 + 3,627 = 4,301 |
| LWPOLYLINE | 1,329 | 38 | 1,503 | 2,870 | 1,359 | 1,511 | 2,870 |
| BLOCK / ENDBLK | 1 / 1 | 1 / 1 | 1,962 / 1,962 | 1,964 / 1,964 | 1,386 / 1,242 | 578 / 722 | 1,964 / 1,964 |
| HATCH | 599 | 0 | 1,264 | 1,863 | 1,299 | 564 | 1,863 |
| MTEXT | 2 | 0 | 1,764 | 1,766 | 1,083 | 683 | 1,766 |
| DIMENSION (linear 1,740, aligned 22, diameter 2) | 1,589 | 0 | 175 | 1,764 | 206 | 1,558 | 1,764 |
| CIRCLE | 420 | 0 | 1,211 | 1,631 | 1,263 | 368 | 1,631 |
| ARC | 234 | 0 | 113 | 347 | 64 | 283 | 347 |
| LEADER | 195 | 0 | 125 | 320 | 130 | 190 | 320 |
| ELLIPSE | 66 | 0 | 248 | 314 | 111 | 203 | 314 |
| ATTRIB / ATTDEF | 0 / 0 | 0 / 0 | 146 / 18 | 146 / 18 | 7 / 17 | 139 / 1 | 146 / 18 |
| POLYLINE / VERTEX / SEQEND | 36 / 0 / 0 | 0 | 1 / 98 / 106 | 37 / 98 / 106 | 0 / 0 / 1 | all but 1 | 37 / 98 / 106 |
| MLINE | 31 | 0 | 0 | 31 | 0 | 31 | 31 |
| SOLID / REGION | 2 / 0 | 0 | 29 / 16 | 31 / 16 | 13 / 8 | 18 / 8 | 31 / 16 |
| VIEWPORT | 1 | 3 | 1 | 5 | 0 | 5 | 5 |
| RTEXT (Express Tools, no DXF form in the writer) | 0 | 2 | 0 | 2 | 0 | 2 | 0 (HELD, paper title block) |
| **Total** | **15,885** | **127** | **32,564** | **48,576** | **21,072** | **27,504 (57 %)** | **48,574** |

Where the pinned DXF holds MORE of a type in BLOCKS than the DWG has in blocks (HATCH 1,299 vs 1,264, CIRCLE 1,263 vs
1,211, DIMENSION 206 vs 175), model-space entities were written into block definitions: the pinned DXF is not only
incomplete, it is contaminated (entities under the wrong owner).

Spaces: Model; two paper layouts (FRAME: 121 entities, the title frame; ROLL: 1 viewport). Nested blocks: 1,964
definitions = 1,764 `*D` (one per dimension, all present in the patched DXF), 117 `*U` (dynamic block
representations), 1 `*X`, 79 named, model and 2 paper blocks; maximum insert depth 2; no MINSERT.

## 3. Each loss type explained (task list)

| Item asked | Finding (command output) |
|---|---|
| Model space | Pinned: all 15,885 model-space and 127 paper entities lost, because the DXF has no ENTITIES section (`dwg2dxf` logs 206 x `dwg_handle_name: Could not resolve CONTROL object POINT for table BLOCK`, 637 x `BLOCK_HEADER *D first_owned_entity missing`, 39 x `*U first_owned_entity missing`, 2,728 of 3,066 `Object handle not found` warnings name a value 0xFFFFFFFF... = relative references computed from a truncated own handle wrap below zero). File ends after BLOCKS ENDSEC, no EOF. Patched: ENTITIES 16,351 records = 15,883 model + 123 active-paper + their 145 ATTRIB, 104 SEQEND, 96 VERTEX; exact. |
| Paper-space layouts | FRAME (title frame, 121) and ROLL (1 viewport): lost with ENTITIES in the pinned DXF; complete in the patched DXF except 2 RTEXT. |
| Nested blocks | Pinned: 1,386 BLOCK records written, but block bodies resolved through colliding handles (578 definitions empty or missing, contaminated contents). Patched: 1,964 / 1,964 definitions; 322 INSERTs name the bare `*U` (cause 2). |
| ACAD_PROXY_ENTITY / proxy objects | 0 (no object of type 498 / 499). |
| RTEXT | 2 `UNKNOWN_ENT` of class RTEXT, both in the active paper layout (title block fields); the writer has no DXF form for them. Not a finishes item; reported HELD by the check. |
| Dimensions | 1,764 in the DWG; pinned DXF 206 (all in blocks); patched 1,764, every one with its `*D` geometry block. |
| Hatches | 1,863 in the DWG, 1,863 in the patched DXF. |
| MLEADER / MTEXT | MLEADER (MULTILEADER) 0 (only 1 MLEADERSTYLE). MTEXT 1,766, all kept in the patched DXF. |
| OLE | 0 OLE2FRAME. 1 IMAGEDEF with 0 IMAGE entities (an unused raster definition, nothing placed). |
| XREFs | 0 block headers flagged xref or overlay; file dependency list empty. Nothing referenced and unbound. |
| 12,567 handle collisions | Cause localised: parser, `bits.c:1378-1379`; the registered defect `PINNED_LIBREDWG_DWGREAD_JSON_HANDLE_REPRESENTATION_DEFECT` (engine/source/decoder_pins.py, "NOT_LOCALISED") is a parse-time mask, so JSON and DXF writers both see truncated handles. The pinned JSON prints `HANDSEED [0,3,32706]`; the patched decode prints 2,326,466 = 0x237FC2 = the DXF `$HANDSEED`. Upstream removed the mask in 0.13.4 (its `bit_read_H` has no mask; 0.14 also not). Also contradicted here: the libredwg_map.py comment "(byte size, value) stays unique in every real decode": 12,533 (size, value) pairs collide in this decode, so absolute 3-byte references are not exact on such files. |
| Other warnings left in the patched run | 418 `Object handle not found` (none with a wrapped 0xFFFF... value; references to objects absent from the DWG's object map; ezdxf audit fixes 1,402 invalid dictionary owner keys, no entity), 206 DIMASSOC objects decoded as unknown (associativity only, no geometry). |

## 4. Which losses matter for finishes (walls, doors, windows, room labels, dimensions)

| Finishes input (model space) | DWG | pinned DXF | patched DXF | still lost in patched |
|---|---:|---:|---:|---|
| A-PL-WALL entities | 5,026 | 0 | 5,026 | 0 |
| Doors: ARDOOR inserts (named block D1) | 262 | 0 | 262 | 0 |
| Doors: A-PL-DOOR inserts of dynamic blocks | 54 | 0 | 54 written, 54 unresolved (`*U`) | **54 doors** |
| A-PL-WINDOW entities (of which dynamic-block inserts) | 834 (50) | 0 | 834, 50 unresolved | **50 windows** |
| Room tags: A-PL-TEXT dynamic-block inserts | 85 | 0 | 85 unresolved | **85 room tags** |
| A-PL-DIM-INT dimensions / all model dimensions | 1,401 / 1,589 | 0 | 1,401 / 1,589 | 0 |
| A-PL-STAIRS, P-FIXT (sanitary fixtures) | 899, 363 | 0 | 899, 363 | 0 |

The engine's K2 kernel reports the 190 unresolved inserts as `MISSING_BLOCK_DEFINITION` (not silent); ezdxf's audit
deletes them (322 `UNDEFINED_BLOCK` fixes). Either way 54 doors, 50 windows and 85 room tags would be missing from a
takeoff on the patched DXF, so it is refused (check C8) even before the decoder pin question.

**A second finding for every villa (latent on Alsenan):** the 85 room tags are dynamic visibility blocks. In the clean
decode each shows 2 texts and hides about 233 (19,840 hidden texts in all, flagged `invisible`); the 54 dynamic doors
show 3 entities and hide 1,308 in all. `tools/urban_intake.read_dxf` reads texts through
`ezdxf.disassemble.recursive_decompose` and `engine/source/cad/shx_arabic.py:_walk` through `virtual_entities()`;
neither checks the `invisible` flag (reproduced on a synthetic block: a hidden "KITCHEN" text is returned with a visible
"BEDROOM"). The K2 geometry kernel does check it (kernel_ezdxf.py:150, HIDDEN). On a correct export of this file the
text path would read 19,840 hidden room names as labels. Alsenan's AutoCAD export (P7757, AC1032) has 0 hidden texts
among its 665 model-space texts, 0 `*U` blocks and 0 unresolved block references, so no Alsenan quantity is affected
today; the defect is general (any drawing with dynamic room tags or door blocks).

Readable labels: on the clean decode the Arabic texts of this file are in `XARB.SHX` (312 texts; T-033's `bas-f-n.shx`
attribution came through colliding style handles). The merged SHX decoder (T-047) decodes 296 and holds 16 partial;
254 model-space texts match the room vocabulary (245 decoded Arabic on layer TEXT70; decoded words: bathroom 53, bedroom 42, dressing 30,
void 24, living 15, stair 15, garden 12, roof 12, dining 9, kitchen 9, ...). Storey titles recognised by the storey
vocabulary: 4 (basement, ground, first, roof); 6 plan-like titles held as unrecognised; **no second-floor title**,
which is the floor of the PDF's sheet 1, so the apartment still cannot be bound to a storey from this file.

## 5. Conversion acceptance check (every future DXF must pass; `dxf_acceptance_check.py`)

Inputs: the DWG as delivered, its `dwgread -O JSON` decode (reference), the candidate DXF. Read-only; prints counts.
1. **C1 reference clean**: the decode has 0 colliding handle values. If not (the pinned 0.13.3 on a pre-R2018 DWG
   with handles above 0xFFFF), steps 9-10 are not checkable and the DXF is refused until a clean reference exists.
2. **C2 structure**: HEADER, CLASSES, TABLES, BLOCKS, ENTITIES, OBJECTS sections and EOF present; ezdxf opens the
   file without recover mode.
3. **C3 handles**: no record handle written twice (SORTENTSTABLE sort handles excluded); every handle <= `$HANDSEED`.
4. **C4 units**: `$INSUNITS` equal to the DWG's (4 = mm here).
5. **C5 model space**: top-level entity count per type equal to the DWG's entity-mode-2 count.
6. **C6 all entities**: count per type over ENTITIES + BLOCKS equal to the DWG's; only a listed type with no DXF form
   (RTEXT) may differ, only in paper space, and it is reported HELD with its count.
7. **C7 block definitions**: BLOCK records = BLOCK_HEADER objects (1,964 here).
8. **C8 references**: 0 INSERT or DIMENSION naming an undefined block.
9. **C9 layers**: model-space count per layer equal.
10. **C10 geometry checksum**: model-space LINE length per layer equal (relative 1e-9) and LINE / LWPOLYLINE vertex
    extents equal (1e-6 drawing units).
11. **C11 text and dimensions**: model-space TEXT + MTEXT and DIMENSION counts equal.
12. Verdict ACCEPTED only when every step passes; otherwise REFUSED with the failing steps, and no method runs on it.

Self-test (`--selftest`, synthetic two-storey plan in mm, not a client drawing): identical file ACCEPTED; no ENTITIES
section, bare `*U` insert name, one wall LINE removed, units changed to metres and one duplicated handle each REFUSED
with exactly the expected steps: 6 / 6 cases as expected.

Results on development project 2 (DWG sha `2635cc50...`):

| Candidate | Verdict | Failing steps |
|---|---|---|
| pinned 0.13.3 `dwg2dxf` | REFUSED | C1 (12,567 collisions), C2 (no ENTITIES / OBJECTS, no EOF), C6 (27,504 entities short) |
| diagnostic 0.13.3, mask fixed (default R2007 out) | REFUSED | C8 only (322 unresolved `*U` references); C1-C7, C9-C11 pass |
| diagnostic, `--as r2018` | REFUSED | C8 only (322) |
| diagnostic, `--as r2000` | REFUSED | C2 (`Expected DXF entity ENDBLK or SEQEND`), C6 |
| release 0.13.4 `dwg2dxf` | REFUSED | writer aborts after 24,576 bytes (C2, C6); its JSON decode is clean (C1 passes) |
| owner's new DXF | not on Drive yet | to be run with the 0.13.4 or patched clean decode as reference |

## 6. Handoff in engine terms

- Development project 2 finishes (tiles, plaster, paint, floor area, wet / dry, doors, windows): engine vs freelancer
  **not measured** for every line; no method was run, because no DXF passes the check. Nothing is shown as 0.
- What a passing DXF of this file could give: walls (5,026 entities), 316 door inserts, 834 window entities, 1,589
  dimensions, 363 sanitary fixtures and 254 readable room labels in model space; but it is a structural set with an
  architectural background of several storeys and no second-floor title, so binding the apartment's rooms to its
  storey stays HELD until the architectural plans file named on the PDF plot stamp (Q-15 A) arrives.
- Verdict proposals: none (no quantity compared).

## 7. Proposed tasks (for the lead)

1. Text intake honours the `invisible` flag (every villa): new versions of the text read path of
   `tools/urban_intake.read_dxf` and of `shx_arabic.records_from_doc` that record a hidden text as HIDDEN (count, path)
   and never as a label; fixture: synthetic dynamic room-tag and door blocks with visibility states, mirrored and
   rotated; Alsenan must not change (0 hidden texts).
2. Decoder pin: record the localisation (bits.c:1378-1379) in a new decoder_pins record; add the C1 collision test to
   every DWG intake so a decode with colliding handles is refused, not mapped; the libredwg_map "(size, value) unique"
   assumption is false on this file (12,533 pairs). Re-pinning to 0.13.4 needs its writer crash fixed or the JSON-only
   route; lead / owner decision.
3. When the owner's DXF arrives: run `dxf_acceptance_check.py` with the 0.13.4 JSON decode as reference, then the
   urban-cad-audit, before any V2.9 run.
