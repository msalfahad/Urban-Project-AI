"""T-514 project inputs: the physical element declared for every screed / threshold / lift-marble / outdoor host line
of the candidate of record (training villa). Project data only; the rules live in t514_screed_bed_producers.py.

Each declaration states what is PHYSICALLY built (ERS s.2.1) and what the documents print, with the source of each
statement. No client name, no coordinate, no drawing content beyond the printed note text quoted for its meaning.
Drawings are named by their Drive folder ("Alsenan chalet project") and title only.

Fields
  kind        physical layer kind (see the module's LAYER_KINDS)
  thickness   printed thickness {"value": number, "unit": "m"|"cm"|"mm", "source": ...} or None (not printed)
  floor_class REGULAR | WET (floor-tile beds only: which band of the owner bed rule)
  finish      the finish laid on the bed and the record that sets it (outdoor floors)
  printed     the printed note(s) read for this layer, with the sheet / file and how they were read
  partner     the m2 line of the same physical layer (screeds: the m3 line must reproduce m2 x thickness)
  record_m3   for a screed with no m2 partner: the merged source record of its m3 (component sum)
"""

DXF_ST = "'ST7757 dxf.dxf' (Drive 'Alsenan chalet project')"
DXF_AR = "'P7757_DXF_COMPRESSED.zip' (Drive 'Alsenan chalet project')"
SCAN = ("T-514 own scan 2026-11-05 of every TEXT / MTEXT / ATTRIB entity in model space and all blocks of "
        f"{DXF_ST} and {DXF_AR} for screed / mortar / cement / sand / 1:n / bed / threshold / marble / porcelain / "
        "interlock / mix and the Arabic terms: the only layer notes are '5cm SECREED.' (x2, ST); no mix, no bed, "
        "no threshold or marble fixing note in either file; the architectural single sheets 03 / 04 carry no text "
        "layer (raster; earlier visual reads T-080 / T-329 / T-335 / T-454 found no mix note)")

SCREED_PRINTED_5CM = {"value": 5, "unit": "cm"}

DECLARATIONS = {
    # ---- screeds (released m3 with a printed thickness) ----
    "L-4ec54f9922da7281573a": {
        "kind": "SCREED_PRODUCT_NOT_STATED", "element": "footing protection screed over the footing membrane",
        "thickness": dict(SCREED_PRINTED_5CM, source="ST sheet p.13 '5 cm screed' (T-219 / T-353, Checker-verified)"),
        "partner": "L-e6280a91646613667b62", "printed": SCAN},
    "L-e4789d76efedbc351bd4": {
        "kind": "SCREED_PRODUCT_NOT_STATED", "element": "lift-pit base screed under the raft, over the membrane",
        "thickness": dict(SCREED_PRINTED_5CM, source="ST sheet p.14 '5cm Screed' (T-322, raft 4.60 x 4.50)"),
        "partner": "L-e11f17bb076058bf172d", "printed": SCAN},
    "L-335ae7ca24030b8e9be4": {
        "kind": "SCREED_PRODUCT_NOT_STATED",
        "element": "pool protection screed between the shell and the membrane: under the base and up both outer walls",
        "thickness": dict(SCREED_PRINTED_5CM, source="ST DXF TEXT handle 1874 '5cm SECREED.' (T-309; T-514 scan)"),
        "partner": None,
        "record_m3": {"value": 1.524503, "source": "T-309 face table (MERGED, Checker-verified) / T-310 r7 line"},
        "printed": SCAN},
    # ---- screeds HELD on the candidate ----
    "L-79bc828150bbfe63ce8e": {
        "kind": "SCREED_PRODUCT_NOT_STATED", "element": "footing protection screed, footing 1B1B",
        "thickness": dict(SCREED_PRINTED_5CM, source="ST sheet p.13 '5 cm screed'"),
        "partner": "L-46cee803214ff2d964fa", "printed": SCAN},
    "L-5f018cfc13aaa9ae2210": {"kind": "ROOF_FALLS_SCREED", "element": "falls screed, terrace +5.50",
                               "thickness": None, "printed": SCAN},
    "L-b016c961ddf9e530e3c1": {"kind": "ROOF_FALLS_SCREED", "element": "falls screed, roof +13.90",
                               "thickness": None, "printed": SCAN},
    "L-bec94500648a90fb2f2a": {"kind": "ROOF_FALLS_SCREED", "element": "falls screed, annex roof +4.30",
                               "thickness": None, "printed": SCAN},
    "L-f4ae7151a6e2b93dd7ad": {"kind": "ROOF_FALLS_SCREED", "element": "falls screed, roof +9.70",
                               "thickness": None, "printed": SCAN},
    # ---- outdoor floors ----
    "L-ab44fbc79bed353bde99": {
        "kind": "FLOOR_TILE_BED", "floor_class": "REGULAR", "thickness": None,
        "element": "cement : sand bed under the porcelain of the north side walk (court side of the house)",
        "finish": {"value": "porcelain / ceramic", "source": "OWNER_RULE_OUTDOOR_FLOORS_2026-10-21, owner additions: "
                   "'sides will always be porcelain or ceramic no interlock', 'considered part of the house'"},
        "printed": SCAN},
    "L-57084fa9d3d0a37212fd": {"kind": "PAVER_SAND_BED", "element": "interlock pavers on a sand bed, west court",
                               "thickness": None, "printed": SCAN},
    "L-1c51d1e7a3b65243382a": {"kind": "OUTDOOR_FINISH_NOT_DECIDED", "element": "pool deck floor",
                               "thickness": None, "printed": SCAN,
                               "finish": {"value": None, "source": "OWNER_RULE_OUTDOOR_FLOORS: pool deck HELD"}},
    "L-dd6e372825ce06d45bdd": {"kind": "OUTDOOR_FINISH_NOT_DECIDED", "element": "covered porch floor",
                               "thickness": None, "printed": SCAN,
                               "finish": {"value": None, "source": "OWNER_RULE_OUTDOOR_FLOORS: porch kind OPEN"}},
}

# marble door thresholds (14 m2 lines) and lift thresholds (3 m2 lines): one stone piece in the doorway strip,
# bedded flush with the adjoining finished floors; no bed thickness or mix printed (T-475 s.'Unsupported': 'the bed
# under the threshold'); the doorway strip is its own line, never inside a room floor (UP-THR-001 'never the strip
# counted in two floors'), so no floor-bed line already carries it.
THRESHOLD_LINES = ("L-07ce1d24164207cd06ca", "L-0ca0f91144403e323c68", "L-1a229f1fead084efb881",
                   "L-3b166c2b5d136302f2dd", "L-709aba3ec07bb0f26319", "L-791a94968230969c030f",
                   "L-8901e416cbce62854fbe", "L-92721c425ab3612bb035", "L-a4909527ff598315be61",
                   "L-bfdbdaa2d67a5c805f1e", "L-c8b5c7f742b22388339e", "L-cbf11d0c1befb0519e98",
                   "L-ccb1182ae9409b432968", "L-f2d296f1fc5184419774")
LIFT_THRESHOLD_LINES = ("L-9840d1da235dd7583427", "L-c32effca1d7eae7f36f8", "L-eba7ac43f3fce9bbd0b5")
# B6-06 lift surround: marble jambs + head on the landing wall face (T-475): a wall cladding, not a floor bed; its
# fixing (adhesive, mortar dabs or mechanical) is printed nowhere.
LIFT_SURROUND_LINES = ("L-b66b8e76425d81ff9f19", "L-d788f643b290e8f92558", "L-fdbd9636828f045aae5a")

for _l in THRESHOLD_LINES:
    DECLARATIONS[_l] = {"kind": "THRESHOLD_STONE_BED", "element": "marble door threshold bed", "thickness": None,
                        "printed": SCAN}
for _l in LIFT_THRESHOLD_LINES:
    DECLARATIONS[_l] = {"kind": "THRESHOLD_STONE_BED", "element": "lift landing marble threshold bed",
                        "thickness": None, "printed": SCAN}
for _l in LIFT_SURROUND_LINES:
    DECLARATIONS[_l] = {"kind": "STONE_CLADDING_FIXING", "element": "lift surround marble fixing on the wall face",
                        "thickness": None, "printed": SCAN}

# a host the documents imply but the candidate has no line for (named, never counted, never 0)
MISSING_HOSTS = [
    {"element": "falls / protection screed of the exposed pool-court slab (B8-06 zone POOLCOURT-550, roof function)",
     "evidence": "owner Q-41: roofs and balconies carry a screed layer; T-507 s.1: build-up (falls screed, insulation, "
                 "protection, B13-01) NOT in the V3.0.58 package (WAITING T507_BUILDUP)",
     "state": "MISSING_HOST_LINE (no candidate line: cement / sand HELD by name when the line exists)"},
]
