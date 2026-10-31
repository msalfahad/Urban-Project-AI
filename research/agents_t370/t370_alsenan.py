"""T-370 Alsenan register: the two sources as read in this run (worker 3, 2026-10-30), no private file needed to run.

ARCH = Drive 'Alsenan chalet project' / P7757_DXF_COMPRESSED.zip (P7757.dxf), modelspace; refs are DXF handles.
  Room anchors are the architectural room-tag INSERT handles (block WC 'W.C', bath 'BATH', WASH 'Wash', kit, PAN,
  laun) or, for the one untagged space, the basin handle inside it. The architectural plans DRAW only 5 fixtures:
  the WASH2 basin block (layer 1). WCs, showers and the 5 'BATH' rooms carry a room tag and floor-tile hatch, no
  fixture outline; the three circles A79 / A81 / A84 (layer 5) are 'mechanical ventilation' marks (each with a
  mecvent leader block A7A / A82 / A85, text 'ji,dm wkhudm' = x-arab keyboard for 'تهوية صناعية'), NOT drains.
SAN = Drive 'Alsenan chalet project' / sanitary-7757.pdf, 3 pages (p1 GROUND FLOOR DRAINAGE PLAN, p2 FIRST FLOOR,
  p3 2nd FLOOR), all vector, no text layer; read visually at 600 dpi. refs are 'p<page>@<x>,<y>' in PDF points of the
  page as displayed (rotation applied; 600 dpi pixel / 600 * 72). Fixtures the sanitary sheet adds are BLUE; the
  architectural underlay is BLACK; FD = floor drain (legend), RWD = rain water drain (legend, roof outlet).
"""

from __future__ import annotations

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import t370_fixture_rules as R  # noqa: E402

S, L, B = R.BASIS_SYMBOL, R.BASIS_LEGEND, R.BASIS_LABEL


def _p(page, px, py):
    """600 dpi pixel of the displayed page -> PDF point reference."""
    return f"p{page}@{px * 72 / 600:.1f},{py * 72 / 600:.1f}"


# Room anchors (architectural tag handles). Untagged: the basin annex of the GF core W.C (anchored on its basin).
GF_WC_CORE_A = "GF/WC tag 2DA"
GF_ANNEX_A = "GF/annex of WC 2DA (untagged; basin 33B)"
GF_WC_CORE_B1 = "GF/WC tag 322 (upper of the two W.C split by the diagonal wall)"
GF_WC_CORE_B2 = "GF/WC tag 323 (lower of the two)"
GF_BATH = "GF/BATH text 2ED (by the master bedroom)"
GF_WASH_CORE = "GF/Wash tag 2C5 (core lobby)"
GF_WASH_WEST = "GF/Wash tag 1F0 (by the dewaneya)"
GF_WC_WEST = "GF/WC tag 1F7"
GF_WC_KIT = "GF/WC tag 1C8 (by the kitchen)"
GF_KITCHEN = "GF/KITCHEN tag 276"
GF_PANTRY = "GF/PANTRY tag 178"
FF_LAUNDRY = "1F/LAUNDRY tag BDD"
FF_WC = "1F/WC tag C19"
FF_BATH_TOP = "1F/BATH tag C01"
FF_BATH_RIGHT = "1F/BATH tag C11"
FF_BATH_BL = "1F/BATH tag C2F (bottom, left)"
FF_BATH_BR = "1F/BATH tag C2C (bottom, right)"
SF_WC = "2F/WC tag 12B6"
FF_ROOF_ANNEX = "1F/annex roof +4.30"
FF_ROOF_TERRACE = "1F/terrace roof +5.50"
SF_ROOF = "2F/roof +9.70"

ARCH_ITEMS = [
    R.Item(R.ARCH, "33B", "GF", GF_ANNEX_A, R.BASIN, S, "WASH2 block, layer 1"),
    R.Item(R.ARCH, "2C0", "GF", GF_WASH_CORE, R.BASIN, S, "WASH2 block, layer 1"),
    R.Item(R.ARCH, "2C1", "GF", GF_WASH_CORE, R.BASIN, S, "WASH2 block, layer 1, rotated 133 deg"),
    R.Item(R.ARCH, "1CF", "GF", GF_WASH_WEST, R.BASIN, S, "WASH2 block, layer 1"),
    R.Item(R.ARCH, "1EE", "GF", GF_WASH_WEST, R.BASIN, S, "WASH2 block, layer 1"),
]

SAN_ITEMS = [
    # ---- p1 GROUND FLOOR DRAINAGE PLAN -------------------------------------------------------------------------
    R.Item(R.SAN, _p(1, 5110, 2310), "GF", GF_WC_CORE_A, R.WC, S, "blue WC"),
    R.Item(R.SAN, _p(1, 5140, 2495), "GF", GF_WC_CORE_A, R.BASIN, S, "blue rectangular basin by the door"),
    R.Item(R.SAN, _p(1, 5135, 2400), "GF", GF_WC_CORE_A, R.FLOOR_DRAIN, L, "FD 4in"),
    R.Item(R.SAN, _p(1, 5130, 2760), "GF", GF_ANNEX_A, R.BASIN, S,
           "black underlay basin with a red waste pipe drawn to it"),
    R.Item(R.SAN, _p(1, 5137, 2675), "GF", GF_ANNEX_A, R.FLOOR_DRAIN, L, "FD 3in"),
    R.Item(R.SAN, _p(1, 5648, 2310), "GF", GF_WC_CORE_B1, R.WC, S, "blue WC"),
    R.Item(R.SAN, _p(1, 5420, 2325), "GF", GF_WC_CORE_B1, R.BASIN, S, "blue basin on the diagonal wall, upper face"),
    R.Item(R.SAN, _p(1, 5530, 2302), "GF", GF_WC_CORE_B1, R.FLOOR_DRAIN, L,
           "FD 4in; both diagonal-wall basins pipe to it"),
    R.Item(R.SAN, _p(1, 5300, 2680), "GF", GF_WC_CORE_B2, R.WC, S, "blue WC"),
    R.Item(R.SAN, _p(1, 5330, 2450), "GF", GF_WC_CORE_B2, R.BASIN, S, "blue basin on the diagonal wall, lower face"),
    R.Item(R.SAN, _p(1, 5266, 2790), "GF", GF_WC_CORE_B2, R.FLOOR_DRAIN, L, "FD 4in"),
    R.Item(R.SAN, _p(1, 5890, 2305), "GF", GF_BATH, R.SHOWER_TRAY, S, "blue tray outline with a corner waste"),
    R.Item(R.SAN, _p(1, 6155, 2300), "GF", GF_BATH, R.WC, S, "blue WC"),
    R.Item(R.SAN, _p(1, 5975, 2535), "GF", GF_BATH, R.BASIN, S, "blue basin on the angled wall"),
    R.Item(R.SAN, _p(1, 6065, 2325), "GF", GF_BATH, R.FLOOR_DRAIN, L, "FD 4in"),
    R.Item(R.SAN, _p(1, 5850, 2730), "GF", GF_WASH_CORE, R.BASIN, S, "black underlay basin, red waste to FD"),
    R.Item(R.SAN, _p(1, 5720, 2970), "GF", GF_WASH_CORE, R.BASIN, S, "black underlay basin, red waste to FD"),
    R.Item(R.SAN, _p(1, 5746, 2790), "GF", GF_WASH_CORE, R.FLOOR_DRAIN, L, "FD 3in"),
    R.Item(R.SAN, _p(1, 2200, 4190), "GF", GF_WASH_WEST, R.BASIN, S, "black underlay basin, red waste to FD"),
    R.Item(R.SAN, _p(1, 2200, 4460), "GF", GF_WASH_WEST, R.BASIN, S, "black underlay basin, red waste to FD"),
    R.Item(R.SAN, _p(1, 2234, 4320), "GF", GF_WASH_WEST, R.FLOOR_DRAIN, L, "FD 3in"),
    R.Item(R.SAN, _p(1, 2090, 4980), "GF", GF_WC_WEST, R.WC, S, "blue WC"),
    R.Item(R.SAN, _p(1, 2210, 4720), "GF", GF_WC_WEST, R.BASIN, S, "blue basin"),
    R.Item(R.SAN, _p(1, 2204, 5016), "GF", GF_WC_WEST, R.FLOOR_DRAIN, L, "FD 4in"),
    R.Item(R.SAN, _p(1, 2960, 4864), "GF", GF_WC_KIT, R.WC, S, "blue WC"),
    R.Item(R.SAN, _p(1, 2800, 5030), "GF", GF_WC_KIT, R.BASIN, S, "blue rectangular basin"),
    R.Item(R.SAN, _p(1, 2976, 5040), "GF", GF_WC_KIT, R.FLOOR_DRAIN, L, "FD 4in"),
    R.Item(R.SAN, _p(1, 3000, 5000), "GF", GF_WC_KIT, R.UNKNOWN, S,
           "yellow valve symbol on the soil line by the FD (the symbol the 1F / 2F sheets draw as the shower valve "
           "inside a screened zone); here no screen, no tray, not in the legend: type not printed"),
    R.Item(R.SAN, _p(1, 2856, 4380), "GF", GF_KITCHEN, R.FLOOR_DRAIN, L, "FD 4in; no sink drawn on either sheet"),
    R.Item(R.SAN, _p(1, 3910, 4294), "GF", GF_PANTRY, R.FLOOR_DRAIN, L, "FD 3in; no sink drawn on either sheet"),
    # ---- p2 FIRST FLOOR DRAINAGE PLAN --------------------------------------------------------------------------
    R.Item(R.SAN, _p(2, 5140, 2268), "1F", FF_LAUNDRY, R.FLOOR_DRAIN, L, "FD 4in; no washer / sink drawn"),
    R.Item(R.SAN, _p(2, 5500, 2290), "1F", FF_WC, R.WC, S, "blue WC"),
    R.Item(R.SAN, _p(2, 5380, 2500), "1F", FF_WC, R.BASIN, S, "blue basin"),
    R.Item(R.SAN, _p(2, 5372, 2337), "1F", FF_WC, R.FLOOR_DRAIN, L, "FD 4in"),
    R.Item(R.SAN, _p(2, 5760, 2310), "1F", FF_BATH_TOP, R.SHOWER_TRAY, S, "blue tray outline with a corner waste"),
    R.Item(R.SAN, _p(2, 6010, 2295), "1F", FF_BATH_TOP, R.WC, S, "blue WC"),
    R.Item(R.SAN, _p(2, 5730, 2505), "1F", FF_BATH_TOP, R.BASIN, S, "blue basin"),
    R.Item(R.SAN, _p(2, 5908, 2295), "1F", FF_BATH_TOP, R.FLOOR_DRAIN, L, "FD 4in"),
    R.Item(R.SAN, _p(2, 7370, 3500), "1F", FF_BATH_RIGHT, R.SHOWER_TRAY, S, "blue tray outline with a corner waste"),
    R.Item(R.SAN, _p(2, 7090, 3495), "1F", FF_BATH_RIGHT, R.WC, S, "blue WC"),
    R.Item(R.SAN, _p(2, 7293, 3190), "1F", FF_BATH_RIGHT, R.BASIN, S, "blue basin"),
    R.Item(R.SAN, _p(2, 7200, 3508), "1F", FF_BATH_RIGHT, R.FLOOR_DRAIN, L, "FD 4in"),
    R.Item(R.SAN, _p(2, 3560, 4660), "1F", FF_BATH_BL, R.SHOWER_WALKIN, S,
           "full-width zone closed by a blue screen line with a hinged-leaf symbol, yellow shower valve on the wall"),
    R.Item(R.SAN, _p(2, 3420, 4450), "1F", FF_BATH_BL, R.WC, S, "blue WC"),
    R.Item(R.SAN, _p(2, 3390, 4305), "1F", FF_BATH_BL, R.BASIN, S, "blue basin"),
    R.Item(R.SAN, _p(2, 3388, 4538), "1F", FF_BATH_BL, R.FLOOR_DRAIN, L,
           "FD 4in, outside the screened zone (no drain drawn inside it)"),
    R.Item(R.SAN, _p(2, 4040, 4290), "1F", FF_BATH_BR, R.SHOWER_WALKIN, S,
           "full-width zone closed by a blue screen line with a hinged-leaf symbol, yellow shower valve on the wall"),
    R.Item(R.SAN, _p(2, 3900, 4495), "1F", FF_BATH_BR, R.WC, S, "blue WC"),
    R.Item(R.SAN, _p(2, 3880, 4655), "1F", FF_BATH_BR, R.BASIN, S, "blue basin"),
    R.Item(R.SAN, _p(2, 3862, 4248), "1F", FF_BATH_BR, R.FLOOR_DRAIN, L, "FD 3in, inside the screened zone"),
    R.Item(R.SAN, _p(2, 3862, 4553), "1F", FF_BATH_BR, R.FLOOR_DRAIN, L, "FD 4in, by the WC"),
    R.Item(R.SAN, _p(2, 1056, 5046), "1F", FF_ROOF_ANNEX, R.ROOF_DRAIN, L, "RWD, RWP 4in T/B, slope 1 % to it"),
    R.Item(R.SAN, _p(2, 7754, 4970), "1F", FF_ROOF_TERRACE, R.ROOF_DRAIN, L, "RWD, slope 1 % to it"),
    # ---- p3 2nd FLOOR DRAINAGE PLAN ----------------------------------------------------------------------------
    R.Item(R.SAN, _p(3, 5100, 2320), "2F", SF_WC, R.SHOWER_WALKIN, S,
           "zone closed by a blue screen line with a hinged-leaf symbol, yellow shower valve on the wall"),
    R.Item(R.SAN, _p(3, 4975, 2540), "2F", SF_WC, R.WC, S, "blue WC"),
    R.Item(R.SAN, _p(3, 4950, 2750), "2F", SF_WC, R.BASIN, S, "blue basin"),
    R.Item(R.SAN, _p(3, 4928, 2630), "2F", SF_WC, R.FLOOR_DRAIN, L, "FD 4in, outside the screened zone"),
    R.Item(R.SAN, _p(3, 7230, 2254), "2F", SF_ROOF, R.ROOF_DRAIN, L, "RWD, RWP 4in T/B"),
    R.Item(R.SAN, _p(3, 3410, 4715), "2F", SF_ROOF, R.ROOF_DRAIN, L, "RWD, RWP 4in T/B"),
    R.Item(R.SAN, _p(3, 7425, 4700), "2F", SF_ROOF, R.ROOF_DRAIN, L, "RWD, RWP 4in T/B"),
]

# The five architectural basins are the black underlay basins the sanitary sheet drains (same room, same position).
LINKS = [
    ("33B", _p(1, 5130, 2760)),
    ("2C0", _p(1, 5850, 2730)),
    ("2C1", _p(1, 5720, 2970)),
    ("1CF", _p(1, 2200, 4190)),
    ("1EE", _p(1, 2200, 4460)),
]

# Wet / dry class of each space as the drawings and the answered owner rules give it: a W.C / BATH tag is a wet
# room; a basin-only hand-wash space is wet (Q-06 = a); a kitchen is waterproofed (Q-30 = A). Pantry and laundry
# are not classed here (the pantry zone is HELD in the candidate, T-010): they appear only in the drain-only list.
ROOM_CLASS = {(r.split("/")[0], r): "WET" for r in (
    GF_WC_CORE_A, GF_ANNEX_A, GF_WC_CORE_B1, GF_WC_CORE_B2, GF_BATH, GF_WASH_CORE, GF_WASH_WEST, GF_WC_WEST,
    GF_WC_KIT, GF_KITCHEN, FF_WC, FF_BATH_TOP, FF_BATH_RIGHT, FF_BATH_BL, FF_BATH_BR, SF_WC)}

# Benchmark side (T-389 relabel, R-T386-1). These four rows are Urban Projects' own cost record (benchmark manifest
# key WEB, kind WEB_APP_COMMERCIAL_REPORT -> source class URBAN_COST_RECORD; register
# tests/alsenan/registers_b1/WEB_APP_ROWS.json): payable labour / material entries, not a measured BOQ. None has a
# source cell in any of the six freelancer workbooks (source_freelancer_items == []), and FREELANCER_RAW_ROWS.json
# holds no fixture or drain row: B12-01 has NO freelancer item, so the freelancer comparison is NOT COMPARABLE.
# Quantities only (no rate, no total). The counted rows are payable labour counts whose basis (which physical items
# the count covers) the record does not print: compared as UNRESOLVED scope, never as a residual of the drawn count.
COST_RECORD_SOURCE = {"source_class": "URBAN_COST_RECORD", "manifest_key": "WEB",
                      "register": "tests/alsenan/registers_b1/WEB_APP_ROWS.json"}
COST_RECORD = {
    "WEB-055": {"what": "sanitary materials", "kind": "LUMP_SUM", "qty": 1, "unit": "item",
                "comparison": "NOT_COMPARABLE (lump sum, no count)"},
    "WEB-060": {"what": "sanitary labour", "kind": "LUMP_SUM", "qty": 1, "unit": "item",
                "comparison": "NOT_COMPARABLE (lump sum, no count)"},
    "WEB-019": {"what": "floor drains installation (tiling labour)", "kind": "NO_FREELANCER_ITEM", "qty": 24,
                "unit": "qty", "comparison": "UNRESOLVED_SCOPE (payable count; covered population not printed)"},
    "WEB-018": {"what": "showers (tiling labour)", "kind": "NO_FREELANCER_ITEM", "qty": 11, "unit": "qty",
                "comparison": "UNRESOLVED_SCOPE (payable count; unit and covered population not printed)"},
}
B12_01_FREELANCER = "NOT_COMPARABLE: no freelancer item (0 fixture / drain rows in the six freelancer workbooks)"


def run():
    entries = R.reconcile(ARCH_ITEMS, SAN_ITEMS, LINKS)
    return entries, R.totals(entries), R.counts(entries)


if __name__ == "__main__":
    import json
    entries, tot, per_floor = run()
    print(json.dumps(tot, indent=1))
    print(json.dumps({k: v for k, v in per_floor.items()}, indent=1))
    print(R.wet_room_check(entries, ROOM_CLASS))
