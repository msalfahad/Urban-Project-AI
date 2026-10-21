# Ground-slab gap audit: generic faces against the S8.1 face register

**Data:** `06_GROUND_SLAB_GAP_AUDIT.csv`, one row per S8.1 row (sheet-local polygons, with the sheet transform applied) and one row per generic-only face.

**The comparison**
- **M1** carries S9's 21 ground-slab faces: 2 measured zones plus 19 provisional faces at the printed 10 cm, 167.63 m².
- **The generic route** finds 22 PANEL faces on the ground-beam plan, 222.04 m².

## Classes

| class | rows | meaning |
|---|---|---|
| MATCHED_SLAB | 19 | The same face in both. The worst area difference is 0.00073 m²; the sum is −0.0007 m². |
| GENERIC_NO_FACE_REPORTED | 1 | SP-GBP-07 (2.05 m²): no generic face closes. The generic route reported two unenclosed band sides next to it: the loss is visible, not silent. |
| GENERIC_CLASS_BEAM | 1 | SP-GBP-21 (1.14 m²): a 0.95 m slab strip between two ground beams was taken as a 0.95 m-wide ground beam. Ground-beam width modes admit any recurring parallel spacing up to 1.0 m: a generic flaw (technical debt TD-04). |
| GENERIC_COUNTS_EXCLUDED_ZONE | 1 | SP-GBP-12 (8.37 m²): S8.1 excluded it as a stair-flight zone. The generic route counts it as slab, because no stair label lies inside it. |
| GENERIC_ONLY_FACE_WITH_COLUMNS_INSIDE | 1 | A 49.07 m² face with free-standing column marks and a level mark inside it. S8.1 holds no face there. Whether it is ground slab is an engineering question (RFI M2-RFI-03). |
| GENERIC_ONLY_FACE | 1 | A 0.16 m² sliver. |
| BOTH_NOT_SLAB | 1 | SP-GBP-01, outside the building or court: neither route counts it. |

## Reading it

- **Generic measurement is reliable:** where both routes see a face, the areas agree to the square centimetre. Topology over beam faces is the same method S8.1 used.
- **The difference is classification:**
  - the generic route has no stair-zone exclusion without a label;
  - it has no "panel holds free-standing columns" warning;
  - it has a width-mode flaw.

  None of these is hidden: the extra area is in the BOQ as PROVISIONAL with the faces listed.
- **The M1 post-freeze finding PF-M1-02** said the external estimates all sit above M1's ground slab and that "more cells exist between the ground beams". The generic route independently finds one large extra face. It was not tuned to any external area: this audit was run after route G was committed. Whether that face is slab is RFI M2-RFI-03, not a conclusion.

## Recommended engine changes (not made in M2)

1. Flag `SLAB_PANEL_CONTAINS_COLUMNS` (free-standing column outlines or marks inside a panel) as coverage risk.
2. On ground-beam plans, admit only scheduled widths and the drawn widths of bands that carry a ground-beam mark.
3. Treat a stair outline (stair-layer geometry or tread lines) inside a face as an exclusion candidate, reported.
