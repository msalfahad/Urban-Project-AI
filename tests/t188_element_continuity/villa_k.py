"""Synthetic villa K (NOT the development villa): 3 storeys over a foundation, a roof; other names, other layout.

Storeys FDN, GF, 1F, 2F, ROOF. Sheets: A-101 / A-102 / A-103 ground / first / second floor plans, A-201 elevations,
A-301 section 1-1; S-001 foundation plan, S-101 / S-102 / S-103 GF / 1F / 2F roof slabs, S-201 typical details,
S-202 dome detail D2, S-203 pool detail. Plan places in metres in one frame.

Elements and the findings a QS reading the set by hand gets (the expected rows of the tests):

  K-SA  dog-leg stair, GF +0.00 -> 1F +3.60 -> 2F +7.20 (occupies GF, 1F), drawn on A-101 / A-102 and S-101 / S-102
        at (4.0, 6.0); A-103 shows the flights seen through the opening; S-103 slab closes over it (ends evidenced).
        Lines: GF and 1F stair concrete. Detail: TYPICAL (S-201)                -> TYPICAL_DETAIL_ONLY only
  K-SB  straight stair GF -> 1F -> 2F (occupies GF, 1F), drawn on both storeys at (12.0, 3.0), stair concrete line
        on GF only (the 1F flight folded into GF, the D-T184-1 pattern)           -> STOREY_WITHOUT_LINE 1F
  K-SC  spiral service stair GF -> 2F by section 1-1 (occupies GF, 1F), drawn on A-101 only
                                                                                  -> STOREY_NOT_DRAWN 1F,
                                                                                     STOREY_WITHOUT_LINE 1F
  K-LF  lift FDN -> 2F (occupies FDN, GF, 1F, 2F), drawn on every storey, no pit drawn or noted, lift-core
        concrete line on GF                                                       -> MISSING_COMPONENT PIT
  K-DT  tower dome on the roof: elevation A-201 only; S sheets searched; no detail -> NO_STRUCTURAL_COUNTERPART,
                                                                                     NO_STRUCTURAL_DETAIL, NO_BOQ_LINE
  K-DR  terrace dome on the 2F roof: S-103 + detail S-202; its line plus a 'stair' line the route read from its ribs
                                                                                  -> KIND_MISMATCH (the stair line)
  K-PL  pool, base and walls drawn (S-203); reference row 'pump room' on no drawing -> NOT_DRAWN (reference row)
  K-VD  double-height void over the hall (occupies 1F): A-102 'VOID' and the S-101 slab opening; ends at 1F by
        S-102                                                                     -> none
  K-C4  column C4, FDN -> 2F, concrete lines FDN, GF, 1F (none on 2F)             -> STOREY_WITHOUT_LINE 2F
  K-WT  water tank on the roof, drawn on A-201, structure NOT searched yet        -> NOT_SEARCHED (UNKNOWN), and its
                                                                                     detail not recorded -> NOT_SEARCHED;
                                                                                     no line -> NO_BOQ_LINE
  line  L-99 a stair line bound to no element                                     -> UNBOUND_LINE
"""

STOREYS = ["FDN", "GF", "1F", "2F", "ROOF"]


def pr(storey, disc, ref, xy=None, what="DRAWN"):
    d = {"storey": storey, "discipline": disc, "ref": ref, "what": what}
    if xy is not None:
        d["xy"] = list(xy)
    return d


def project():
    return {
        "storeys": list(STOREYS), "place_tol_m": 0.50,
        "elements": [
            {"id": "K-SA", "kind": "STAIR", "place": "core west", "occupies": ["GF", "1F"],
             "occupies_ref": "A-301 levels +0.00 / +3.60 / +7.20",
             "presence": [pr("GF", "ARCH", "A-101", (4.0, 6.0)), pr("GF", "STRUCT", "S-101", (4.0, 6.0)),
                          pr("1F", "ARCH", "A-102", (4.0, 6.0)), pr("1F", "STRUCT", "S-102", (4.0, 6.0)),
                          pr("2F", "ARCH", "A-103 flights seen through the opening", (4.0, 6.0), "SEEN_BELOW")],
             "searched": {"ARCH": "A-101..A-103", "STRUCT": "S-101..S-103"},
             "detail": {"state": "TYPICAL", "ref": "S-201 typical stair section"},
             "ends": {"ref": "A-103 no flight leaves +7.20; S-103 slab panel over the shaft"}},
            {"id": "K-SB", "kind": "STAIR", "place": "east wing", "occupies": ["GF", "1F"],
             "occupies_ref": "A-301 levels",
             "presence": [pr("GF", "ARCH", "A-101", (12.0, 3.0)), pr("GF", "STRUCT", "S-101", (12.0, 3.0)),
                          pr("1F", "ARCH", "A-102", (12.0, 3.0)), pr("1F", "STRUCT", "S-102", (12.0, 3.0))],
             "searched": {"ARCH": "A-101..A-103", "STRUCT": "S-101..S-103"},
             "detail": {"state": "PROJECT", "ref": "S-201 stair SB section"},
             "ends": {"ref": "A-103 / S-103"}},
            {"id": "K-SC", "kind": "STAIR", "place": "service yard", "occupies": ["GF", "1F"],
             "occupies_ref": "A-301 section 1-1 +0.00 -> +7.20",
             "presence": [pr("GF", "ARCH", "A-101", (18.0, 9.0)), pr("GF", "STRUCT", "S-101", (18.0, 9.0))],
             "searched": {"ARCH": "A-101..A-103", "STRUCT": "S-101..S-103"},
             "detail": {"state": "PROJECT", "ref": "S-201 spiral"}, "ends": {"ref": "A-103 arrival at +7.20"}},
            {"id": "K-LF", "kind": "LIFT", "place": "core east", "occupies": ["FDN", "GF", "1F", "2F"],
             "occupies_ref": "A-301 lift shaft",
             "presence": [pr("FDN", "STRUCT", "S-001 lift footing"), pr("GF", "ARCH", "A-101"),
                          pr("GF", "STRUCT", "S-101"), pr("1F", "ARCH", "A-102"), pr("1F", "STRUCT", "S-102"),
                          pr("2F", "ARCH", "A-103"), pr("2F", "STRUCT", "S-103")],
             "searched": {"ARCH": "A-101..A-103", "STRUCT": "S-001..S-203"}, "components": [],
             "ends": {"ref": "S-103 machine-room-less: slab over the shaft"}},
            {"id": "K-DT", "kind": "DOME", "place": "tower", "presence": [pr("ROOF", "ARCH", "A-201 elevation")],
             "searched": {"ARCH": "A-201", "STRUCT": "S-001..S-203"},
             "detail": {"state": "NONE", "ref": "S-201..S-203 searched"}},
            {"id": "K-DR", "kind": "DOME", "place": "terrace",
             "presence": [pr("2F", "STRUCT", "S-103"), pr("2F", "ARCH", "A-103")],
             "searched": {"ARCH": "A-103", "STRUCT": "S-103"}, "detail": {"state": "PROJECT", "ref": "S-202"}},
            {"id": "K-PL", "kind": "POOL", "place": "garden",
             "presence": [pr("GF", "ARCH", "A-101"), pr("GF", "STRUCT", "S-203")],
             "searched": {"ARCH": "A-101", "STRUCT": "S-203"}, "detail": {"state": "PROJECT", "ref": "S-203"},
             "components": [{"name": "BASE", "state": "DRAWN", "ref": "S-203"},
                            {"name": "WALLS", "state": "DRAWN", "ref": "S-203"}]},
            {"id": "K-VD", "kind": "VOID", "place": "hall", "occupies": ["1F"], "occupies_ref": "A-301 double height",
             "presence": [pr("1F", "ARCH", "A-102 VOID"), pr("1F", "STRUCT", "S-101 slab opening")],
             "searched": {"ARCH": "A-102", "STRUCT": "S-101"}, "ends": {"ref": "S-102 slab closes over the hall"}},
            {"id": "K-C4", "kind": "COLUMN", "place": "grid B/2", "occupies": ["FDN", "GF", "1F", "2F"],
             "occupies_ref": "S-001 column schedule C4 FDN -> roof",
             "presence": [pr("FDN", "STRUCT", "S-001"), pr("GF", "STRUCT", "S-101"), pr("1F", "STRUCT", "S-102"),
                          pr("2F", "STRUCT", "S-103")],
             "searched": {"STRUCT": "S-001..S-103"}, "ends": {"ref": "S-103 column stops under the roof slab"}},
            {"id": "K-WT", "kind": "TANK", "place": "roof", "presence": [pr("ROOF", "ARCH", "A-201")],
             "searched": {"ARCH": "A-201"}},
        ],
        "lines": [
            {"line_id": "L-01", "item": "STAIR CONCRETE", "kind": "STAIR", "storey": "GF", "trade": "STRUCTURE",
             "state": "MEASURED", "element": "K-SA"},
            {"line_id": "L-02", "item": "STAIR CONCRETE", "kind": "STAIR", "storey": "1F", "trade": "STRUCTURE",
             "state": "MEASURED", "element": "K-SA"},
            {"line_id": "L-03", "item": "STAIR MARBLE", "kind": "STAIR", "storey": "GF", "trade": "FINISHES",
             "state": "MEASURED", "element": "K-SA"},
            {"line_id": "L-10", "item": "STAIR CONCRETE", "kind": "STAIR", "storey": "GF", "trade": "STRUCTURE",
             "state": "MEASURED", "element": "K-SB"},
            {"line_id": "L-20", "item": "STAIR CONCRETE", "kind": "STAIR", "storey": "GF", "trade": "STRUCTURE",
             "state": "MEASURED", "element": "K-SC"},
            {"line_id": "L-30", "item": "LIFT CORE CONCRETE", "kind": "LIFT", "storey": "GF", "trade": "STRUCTURE",
             "state": "MEASURED", "element": "K-LF"},
            {"line_id": "L-40", "item": "DOME SHELL", "kind": "DOME", "storey": "2F", "trade": "STRUCTURE",
             "state": "MEASURED", "element": "K-DR"},
            {"line_id": "L-41", "item": "STAIR CONCRETE", "kind": "STAIR", "storey": "1F", "trade": "STRUCTURE",
             "state": "PROVISIONAL", "element": "K-DR", "ref": "route face: 18 lines from one point, r 2.20 m"},
            {"line_id": "L-50", "item": "POOL BASE", "kind": "POOL", "storey": "GF", "trade": "STRUCTURE",
             "state": "MEASURED", "element": "K-PL"},
            {"line_id": "L-60", "item": "COLUMN NECK", "kind": "COLUMN", "storey": "FDN", "trade": "STRUCTURE",
             "state": "MEASURED", "element": "K-C4"},
            {"line_id": "L-61", "item": "COLUMN", "kind": "COLUMN", "storey": "GF", "trade": "STRUCTURE",
             "state": "MEASURED", "element": "K-C4"},
            {"line_id": "L-62", "item": "COLUMN", "kind": "COLUMN", "storey": "1F", "trade": "STRUCTURE",
             "state": "MEASURED", "element": "K-C4"},
            {"line_id": "L-99", "item": "STAIR CONCRETE", "kind": "STAIR", "storey": "GF", "trade": "STRUCTURE",
             "state": "MEASURED", "element": None},
        ],
        "reference_rows": [
            {"row_id": "REF:7", "kind": "POOL", "element": "K-PL", "component": "base"},
            {"row_id": "REF:8", "kind": "POOL", "element": None, "component": "pump room", "ref": "reference BOQ"},
        ],
    }


EXPECTED = sorted([
    ("NO_BOQ_LINE", "K-DT", None), ("NO_STRUCTURAL_COUNTERPART", "K-DT", None), ("NO_STRUCTURAL_DETAIL", "K-DT", None),
    ("KIND_MISMATCH", "K-DR", "1F"), ("MISSING_COMPONENT", "K-LF", None), ("NOT_DRAWN", None, None),
    ("TYPICAL_DETAIL_ONLY", "K-SA", None), ("STOREY_WITHOUT_LINE", "K-SB", "1F"), ("STOREY_NOT_DRAWN", "K-SC", "1F"),
    ("STOREY_WITHOUT_LINE", "K-SC", "1F"), ("STOREY_WITHOUT_LINE", "K-C4", "2F"), ("NOT_SEARCHED", "K-WT", None),
    ("NOT_SEARCHED", "K-WT", None), ("NO_BOQ_LINE", "K-WT", None), ("UNBOUND_LINE", None, None),
], key=lambda t: (t[0], t[1] or "", t[2] or ""))
