"""T-556 development-villa inputs (no coordinate, client name or drawing content; merged repository ledgers cited).

Lines: the 11 dry FIN.PLASTER room lines of the candidate of record (ARCH_TAKEOFF_V3.0.58 = the V3.0.57 plaster lines,
research/agents_t507/out/LINE_INDEX_V3_0_57.json) that T-552 found at the paint height (ENGINE_WRONG, Checker
2026-11-06 05:58). Faces / roof shares: T-128 r3 (ROOMS_T128_R3.csv; share of each face under a roof from the T-128
trace datum split, trace_lengths.json). Openings: T-292 per-opening ledger (OPENING_DEDUCTIONS_T292.csv, merged), heads
from T-201 / T-144 / T-207, arched holes T-238, W17 crown Q-76 A. Beams: T-110 member register (schedule b x h).
Levels: T-214 (MERGED b29060c2, Verifier independent re-measure 2026-10-23 14:12): dry-floor build-up 0.05 m
DRAWING-CONFIRMED on every floor band of sections A-A / B-B; slab 0.16 (structural general note, owner Q-14 answer).
"""

LINE_INDEX = "research/agents_t507/out/LINE_INDEX_V3_0_57.json"
ROOMS = "research/agents_t128/ROOMS_T128_R3.csv"
OPENINGS = "research/agents_t292/OPENING_DEDUCTIONS_T292.csv"
BEAMS = "research/agents_t110/BEAM_MEMBER_REGISTER.csv"
T552_OUT = "research/agents_t552/out/T552_PLASTER_RECONCILE.json"

# room row -> (candidate line id prefix, storey zone)
LINES = {"GF-01": ("L-b1529955", "GF_ANNEX"), "GF-04": ("L-1ddc23d5", "GF_ANNEX"), "GF-15": ("L-0d93f220", "GF_MAIN"),
         "GF-08": ("L-8cecb1d0", "GF_MAIN"), "1F-01": ("L-af9621f4", "1F"), "1F-04": ("L-971f0bda", "1F"),
         "1F-10": ("L-2ba8077b", "1F"), "1F-11": ("L-31db3c83", "1F"), "1F-13": ("L-9b4a7bab", "1F"),
         "2F-03": ("L-4ce74fc3", "2F"), "2F-01": ("L-ae0cdd79", "2F")}

SLAB = ("0.16", "structural general note 'all slabs 16 cm unless stated' (owner Q-14 answer; T-200 / T-206: suspended "
                "slabs and the annex / 2F roof slabs 0.16)")
FLOOR_BUILDUP = ("0.05", "T-214 drawn layer FFL -> slab top on every floor band of sections A-A / B-B (0.049 .. 0.051), "
                         "DRAWING-CONFIRMED, Verifier re-measured 2026-10-23 14:12 (dry zones)")
ROOF_SCENARIO = ("0.05", "roof DRAWN-SECTION SCENARIO: the same 0.05 layer the cut sections draw on the roof bands "
                         "(A-A +13.90, B-B +4.30; T-214 table); refused by T-214 as a roof datum (constant layer vs the "
                         "printed 1 % falls), roof build-up D-39 / DCR-6 HELD")

# zone -> (interval to the floor or roof above, source, roof element over the roof part)
ZONES = {
    "GF_MAIN": ("4.50", "section A-A storey marks +1.00 / +5.50 (T-128 s.2, T-214)", "TERRACE-550 (+5.50 finished)"),
    "GF_ANNEX": ("4.00", "section B-B marks +0.30 / +4.30 (+4.30 = finished annex roof mark, G2)", "ROOF-430 (+4.30)"),
    "1F": ("4.20", "section A-A marks +5.50 / +9.70 (T-128 s.2, T-214)", "ROOF-970 (+9.70)"),
    "2F": ("4.20", "section A-A marks +9.70 / +13.90 (+13.90 = finished top roof mark)", "ROOF-1390 (+13.90, Q-34)"),
}
# a zone with NO floor above at all (every face under a roof)
NO_FLOOR_ABOVE = {"GF_ANNEX", "2F"}

# T-292 openings whose hole height is established outside the merged_size text (T-207 closure: h 2.20
# DRAWING-CONFIRMED, sill HELD)
HOLE_HEIGHT = {("GF-01", "W11"): "2.20", ("GF-01", "W12"): "2.20"}

# crossing beams (T-128 r3 CROSSING_BEAMS) with the T-110 schedule b x h; ends: 2 in a closed room (OPEN_SIDES 0),
# (0, 2) in an open-sided room; B6 has one CONFLICT span (0.25 schedule / 0.20 drawn) not bound to a room: width range.
BEAM_ENDS = {
    "GF-01": [("CB6", "0.2", "0.75")],
    "GF-08": [("B26", "0.65", "0.85"), ("B27", "0.9", "0.85")],
    "1F-01": [("B6", ("0.2", "0.25"), "0.5")],
    "1F-10": [("B19", "0.4", "0.75"), ("B6", ("0.2", "0.25"), "0.5")],
    "2F-03": [("B2", "0.2", "0.4")],
    "2F-01": [("B15", "0.2", "1.2")],
}
EDGE_BEAMS = {"1F-13": "B25 / CB12 0.75 lie on the zone edges (T-128 r3): not crossing; no wall-face interruption"}
