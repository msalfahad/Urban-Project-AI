# T-099: rooms that vanish - room census guard (ROOM_CENSUS_GUARD_V1)

Worker 2, 2026-10-20. Gate 1 (no silent omissions: every labelled room appears as measured, held or unsupported).
Development villa (Alsenan) only; NOT an accuracy claim. New method piece `engine/source/room_census_guard.py`, read by
no released method: no released quantity changed.

## The two ways a room dropped out, and what the guard does

1. **Labelled faces under 1 m2.** `arch_rooms.MIN_SPACE_M2 = 1.0` makes a face under 1 m2 a SLIVER. Found while
   building the fixture: a face under about 0.81 m2 never even reaches SLIVER, because the thin test
   (2A/P < 0.45 m) comes first and 2A/P of a square is half its side. So a labelled 1.00 x 0.80 = 0.80 m2 W.C. arrives
   as a WALL / DOORWAY face. Both kinds were invisible to the V2.8 lost-label finding, because the label IS inside a
   face. Now: HELD `SUB_THRESHOLD_LABELLED` (under 1 m2, any class) or `THIN_FACE_LABELLED` (a thin face of 1 m2 or
   more, e.g. a 0.40 x 3.85 duct). Each keeps its label words, code, wet / dry kind, m2 and the faces it touches.
2. **Unlabelled rooms.** The guard re-reads every space that has no label text with WET_ROOM_EVIDENCE_V1 (T-010,
   owner Q-13 B, Q-06 a). It gives one of:
   - `TYPED_BY_EVIDENCE`: a toilet / shower / bath block, WC lines on a sanitary layer or next to a drain mark, a
     basin-only hand-wash space, or a label that ROOM_VOCAB_V2 reads and the room builder's V1 words missed.
   - HELD `UNLABELLED_ROOM`: no evidence, loose WC lines on a furniture layer, or an appliance alone.
   - `NO_ROOM_FINISH`: stair flights, a void symbol or a stacked shaft footprint.

   A face the room builder typed only from a cooker block (V2.11: KITCHEN) is HELD and marked `differs_from_engine`.
3. Every face gets one record (`every_face_once`). A held space carries its measured m2, never 0. An unlabelled
   non-space face under 1 m2 that holds sanitary evidence is HELD `SUB_THRESHOLD_FIXTURE`. One that holds a text the
   reader could not decode (an Arabic label in an unmapped SHX font) is HELD `UNDECODED_TEXT_INSIDE`.

## Alsenan census (ARCH_TAKEOFF_V2.11 faces, Drive "Alsenan chalet project", P7757_DXF_COMPRESSED.zip)

| Floor | Faces | Labelled rooms | Held unlabelled | Typed by evidence | Shaft (no finish) | Labelled face < 1 m2 or thin | Sliver |
|---|---|---|---|---|---|---|---|
| GF | 349 | 15 (231.63 m2) | 2: 3.60 + 1.56 = 5.16 m2 | 3: 1.485 + 3.1325 + 4.7307 = 9.348 m2 | 1 (3.24 m2) | 0 | 0 |
| 1F | 294 | 11 (179.75 m2) | 1: 2.97 m2 | 0 | 1 (3.24 m2) | 0 | 0 |
| 2F | 98 | 3 (43.50 m2) | 0 | 0 | 1 (3.24 m2) | 0 | 0 |

- **Labelled faces under 1 m2 or thin: 0 on all three floors.** No Alsenan room is lost to the threshold. The
  freelancer's floor rows agree: his smallest wet row is 1.70 m2 and his smallest dry row 7.70 m2. Of the 43 room-label
  texts, 31 are in labelled faces and 1 ('Wash') in a face that the room builder's V1 words missed. The other 11 lie in
  no face: pool / court (6), roof / void (5). These are open areas, already the V2.8 OPEN_AREA findings.
- **Held unlabelled rooms: 3 faces, 8.13 m2.** They are the same three faces, with the same m2, as the held rows of the
  verified tiling table (T-086 DF-GF-RF002DC 3.60, DF-GF-R7B7A5D 1.56, DF-1F-RFFE7AF 2.97), so the two independent
  routes agree to 0.00 m2. What the plan shows round them:
  - GF 1.20 x 3.00 = 3.60 m2: a strip with three openings, beside the kitchen; no text inside but a dimension.
  - GF 1.20 x 1.30 = 1.56 m2: four openings, level mark +0.15, by the +0.30 lobby.
  - 1F 1.65 x 1.80 = 2.97 m2: two openings, beside a master bedroom.

  None has a label, a fixture or a drain. Under Q-13 B they stay HELD: no wet and no dry finish, never a dry default.
  Whether the freelancer's dry rows include them (entrance 10.46, corridor 7.70 m2) is not established. They are not
  paired here.
- **Typed by evidence: 9.35 m2.** That is 1.485 (basin, no label), 3.1325 (two basins; its label is an undecoded SHX
  text) and 4.7307 ('Wash'), the three hand-wash spaces of owner Q-06 ("9.35 m2 in all"). They match the verified wet
  hand table (T-074 / T-086 WF-GF-11 1.485, WF-GF-02 3.1325, WF-GF-14 4.7321; -0.0014 m2). The freelancer's wash rows
  in the tiles sheet are 4.73 + 1.70 + 3.15 = 9.58 m2. The 1.70 row is unnamed under the diwaniya wash. Not paired
  room by room.
- **Undecoded texts:** 47 texts on the three plans are in an unmapped SHX font. They are the Arabic twins of the
  English labels: 'MOSLy' = مغسلة, 'HMam' = حمام. None lies in a sliver or thin face. One lies in an unlabelled space:
  the 3.1325 m2 basin space, whose Arabic label is unreadable, so only its basins type it. 17 lie in no face; most are
  sheet notes on layer 1.

## What this does not do

It changes no face, room or released quantity, and it is not wired. A later ARCH_TAKEOFF version would release the
TYPED_BY_EVIDENCE spaces and carry the HELD records into the BOQ's held list. It does not decode SHX fonts.

Run: `python3 -I research/agents_t099/alsenan_census_run.py <P7757.dxf> --out <scratch>/t099.json`. The output stays
outside the repository.
