# MINSERT reflection oracle (R8.1 §12)

**Status: `MINSERT_REFLECTION_ORACLE_CONFLICT`.** Analysis favours the Urban hand truth. A native AutoCAD check is recommended once, but it does not block R8.1.

Files:
- `minsert_reflection_oracle.py` is the generator. It is a research-lab script that uses ezdxf 1.4.4.
- `MINSERT_REFLECTION_ORACLE.dxf` is the scene. Open it in AutoCAD.
- `MINSERT_REFLECTION_ORACLE.json` holds the expected points, the ezdxf points, the mechanism and the instructions.

## Case A: F06_MINSERT_MIRRORED_PARENT

| | cell (c,r) origin |
|---|---|
| Urban hand truth (R8.0, frozen) | (−1000c, **+500r**) |
| K1 (R8.1) | (−1000c, **+500r**) |
| ezdxf 1.4.4 | (−1000c, **−500r**) |

The scene is `INSERT HOLDER scale(−1,1)`, which contains `MINSERT CELL` as a 3×2 grid with column spacing 1000 and row spacing 500.

**Re-check of the hand derivation.** A block reference places its definition through one affine matrix, and nothing inside the definition is re-encoded. In HOLDER's frame the MINSERT's cells sit at (1000c, 500r), with spacing rotated by the MINSERT's own rotation (0) and never scaled. The parent matrix diag(−1, 1) maps them to (−1000c, 500r). This is the same composition K1 performs: `parent @ OCS @ T(ins + R·offset) @ R @ S @ T(−base)`.

**The ezdxf mechanism, read in its source.** `Insert.virtual_entities()` hands the nested MINSERT to `Insert.transform(m)`. There, `InsertCoordinateSystem` absorbs the X reflection as rotation 180° plus yscale −1, but `row_spacing` and `column_spacing` are never touched. `multi_insert()` then rotates the unchanged offsets (1000c, 500r) by 180°, which gives (−1000c, −500r). Only the columns agree with the truth, and that is by accident. A flat INSERT encoding can represent the reflected grid only with an extrusion flip or with negated spacing, and ezdxf does neither.

**Autodesk semantics.** Per the DXF reference, the MINSERT grid is laid out in the insert's rotated frame in parent units, and the spacing is not scaled. Nested block content is displayed by matrix composition. Nothing in the reference makes a parent reflection re-encode a child's spacing.

## Case B: top-level MINSERT with scale (−1, 1)

Both engines give (1000c, −3000 + 500r), with every cell's line drawn toward −x. This case tests the stored-field rule itself ("spacing is rotated, never scaled"). All three agree, so there is no conflict.

## Recommendation

- Keep the hand truth, and keep ezdxf's result registered as `LIBRARY_KNOWN_FAILURE`.
- Do **not** tune K1 toward either engine.
- Run the native check once (steps are in the JSON), and record the result as a `NATIVE_AUTOCAD_OBSERVATION` for R8.2.
- The optional MIRROR/LIST step also tells us how AutoCAD re-encodes a mirrored top-level MINSERT, meaning whether it negates the column spacing. We need that before R8.2 maps real MINSERT fields. No MINSERT exists in either real decode, so the D1 route keeps MINSERT as `SOURCE_MAPPING_UNVERIFIED` until then.
