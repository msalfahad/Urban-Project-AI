# T-058: strip guard on the foundation-level perimeter band (read-only run)

Worker 3, 2026-10-19. Development reference, not an accuracy claim. Not wired into any released method.

Input: Drive "Alsenan chalet project" / "ST7757 dxf.dxf" (sha256 9f9d1179..., = SOURCE_MANIFEST.json), band polylines
1658 (outer) and 1659 (inner) on the band layer; members = closed outlines on the footing (8) and column (36) layers
inside the band's box; units mm (`--unit-m 0.001`); frozen state given for span 1658:2 (EXPLAINED_BY_MEMBER, T-050,
confirmed by the verifier with edge_trace.py). Command:

    python3 -I research/agents_t058/run_on_dxf.py <dxf> --band 1658 1659 --members <footing layer>=FOOTING
        <column layer>=COLUMN --unit-m 0.001 --depth 0.60 --explained 1658:2

| Quantity | Value |
|---|---|
| ring centre line (closed, 4 strips joined at corners) | **91.94 m** (= T-037 / T-050 hand value 2 x 31.17 + 2 x 14.80) |
| ring plan area | 18.388 m2 (91.94 x 0.20) |
| MEASURED (centre line outside every member) | 78.54 m, 15.708 m2, 9.425 m3 at the B.W 0.60 section |
| HELD STRIP_UNDER_MEMBER (centre line inside a footing or column cast against the plot line) | 13.40 m, 2.680 m2 (1.608 m3 at 0.60), 12 records with member handles |
| HELD STRIP_FACE_UNPAIRED | 0 |
| frozen view: kept paired overlap | **60.17 m** (= the engine's released line, so the frozen result is reproduced) |
| frozen view: silent omission | span 1658:2 (31.37 m, removed as EXPLAINED_BY_MEMBER) and its partner 1659:2 (30.97 m, left unpaired) |
| frozen view: corner basis loss | 0.60 m (3 kept sides x 0.20 m) |

Neighbour-side plot line 1658:2: frozen 5-point share 0.8 (removed) but covered length share 0.286 (8.96 m of 31.37 m
within 0.03 m of a member edge or inside a column): the frozen 5-point rule, not the members' length, removed it.

Verdict proposal (footing edge strip, CONC.FOOTING line): engine (this guard) 91.94 m = 11.033 m3 at 0.20 x 0.60, of
which 9.425 m3 MEASURED and 1.608 m3 HELD under members (may already be in the footing / column volume: the reviewer
decides, never added silently); frozen engine 60.17 m (7.220 m3): ENGINE_RIGHT for the guard against the frozen line
by the hand trace (T-050); freelancer 71.7 m (8.604 m3) not identifiable as a set of drawn sides: UNRESOLVED. Whether
the band belongs in the footing line stays owner Q-12 (c).
