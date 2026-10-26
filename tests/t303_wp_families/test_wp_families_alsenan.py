"""T-303 on the development villa (committed merged ledgers + T-301's committed waterproofing-line extract; no private
input): the WP.WET_AREA and WP.ROOF inventories and the WP.POOL_TANK presence ruling against the candidate of record
(V3.0.17 = V3.0.18 for every WP line)."""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "research/agents_t303"))

import t303_alsenan as A  # noqa: E402


def lr(fam):
    return {r["line_id"]: r for r in A.family_report(fam)[3]["line_rows"]}


def test_wet_room_presence_agrees_with_the_t209_set_and_the_t249_doors():
    rooms = A.wet_rooms()
    t209 = {r["id"] for r in json.loads(A.T209.read_text(encoding="utf-8"))["rooms"]}
    assert set(rooms) == t209 and len(rooms) == 18
    t249 = A.t249_doors()
    bound = [d for d in A.DOORS if d in t249]
    assert len(bound) == 14 and all(t249[d]["STATE"] == "LOCATED" for d in bound)
    assert len(set(A.DOORS)) == 15                              # + the pantry's own door (not bound to an insert)


def test_wet_area_inventory_and_named_findings():
    els, lines, lk, rep = A.family_report(A.WET)
    assert len(lines) == 119 and rep["counts"] == {"IN_LINE": 113, "NOT_APPLICABLE": 0, "MISSING": 8}
    missing = sorted(r["key"] for r in rep["elements"] if r["status"] == "MISSING")
    assert missing == ["FIN.WP.DOORWAY[m2]/DOOR:D-GF-07-PANTRY/THRESHOLD_FLOOR",
                       "FIN.WP.DOORWAY_TRANSITION[m2]/DOOR:D-1F-06/TRANSITION",
                       "FIN.WP.DOORWAY_TRANSITION[m2]/DOOR:D-GF-07-PANTRY/TRANSITION",
                       "FIN.WP.DOORWAY_TRANSITION[m2]/DOOR:D-GF-11/TRANSITION",
                       "FIN.WP.DOORWAY_TRANSITION[m2]/DOOR:D-GF-12/TRANSITION",
                       "FIN.WP.DOORWAY_TRANSITION_NR[pcs]/DOOR:D-GF-07-PANTRY/TRANSITION",
                       "FIN.WP.PENETRATION[pcs]/GF-07/FLOOR_PENETRATIONS",
                       "FIN.WP.TERMINATION[lm]/GF-07:OPEN_SIDE_DINING/MEMBRANE_EDGE"]
    assert all(r["qty"] is None for r in rep["elements"] if r["status"] == "MISSING")      # blank, never 0
    assert [d["key"] for d in rep["double_carried"]] == ["FIN.WP.DOORWAY_TRANSITION[m2]/DOOR:D-GF-02/TRANSITION",
                                                         "FIN.WP.DOORWAY_TRANSITION[m2]/DOOR:D-GF-10/TRANSITION"]
    assert sorted(x["line_id"] for x in rep["register_only"]) == ["L-0a7238edb9989d99d37a", "L-1ef59757a75524c397d7",
                                                                  "L-8fb80f626889e06f6f97", "L-f78da96a7d31f7b72068"]
    assert rep["unlinked_lines"] == []


def test_wet_area_residuals_by_item_and_line():
    *_x, rep = A.family_report(A.WET)
    fam = {f["item_code"]: f for f in rep["families"]}
    assert (fam["FIN.WP.FLOOR"]["inventory_qty_in_line"], fam["FIN.WP.FLOOR"]["line_qty"]) == (85.6217, 85.62071)
    assert fam["FIN.WP.DOORWAY"]["residual"] == -0.110379
    assert fam["FIN.WP.DOORWAY_TRANSITION_NR"]["residual"] == 0.0
    rows = lr(A.WET)
    assert rows["L-60f100105399a9bdfb08"]["residual"] == 0.1            # 1F east bath upturn: 0.50 m less wall
    assert rows["L-0f04f1a49d795b14d1af"]["residual"] == -0.098846      # GF master bath threshold (closure)
    assert rows["L-f32abcdb3b4db6877c64"]["countability"] == "WHOLE"    # pantry membrane 13.500 = printed box
    cnt = {}
    for r in rows.values():
        cnt[(r["item_code"], r["countability"])] = cnt.get((r["item_code"], r["countability"]), 0) + 1
    assert cnt[("FIN.WP.FLOOR", "WHOLE")] == 17 and cnt[("FIN.WP.FLOOR", "COMPONENT")] == 1
    assert cnt[("FIN.WP.WALL_UPTURN", "WHOLE")] == 12 and cnt[("FIN.WP.WALL_UPTURN", "HELD")] == 1
    assert cnt[("FIN.WP.DOORWAY", "WHOLE")] == 12 and cnt[("FIN.WP.DOORWAY_TRANSITION_NR", "WHOLE")] == 14


def test_roof_inventory():
    els, lines, lk, rep = A.family_report(A.ROOF)
    assert len(lines) == 12 and rep["counts"] == {"IN_LINE": 13, "NOT_APPLICABLE": 0, "MISSING": 3}
    assert sum(1 for r in rep["elements"] if (r["note"] or "").startswith("SCOPE_UNKNOWN")) == 3
    rows = lr(A.ROOF)
    assert rows["L-2f7502be6f501baf49b1"]["countability"] == "WHOLE"    # 1F SE 32.721 m2
    assert rows["L-994b88140f2ea50f1b31"]["countability"] == "WHOLE"    # 1F SE upturn 52.940 lm
    assert rows["L-d4c73babd2a275c28929"]["countability"] == "WHOLE"    # 1F W upturn 35.727 lm
    at379 = rows["L-636fd3ff1784a12e653b"]
    assert at379["countability"] == "COMPONENT" and at379["residual"] == -0.015483 and "missing" in at379["why"]
    assert rows["L-3e8fe55da71851816dd4"]["countability"] == "HELD"     # 2F top roof (Q-34)


def test_pool_tank_presence_ruling():
    els, lines, lk, rep = A.family_report(A.POOL)
    assert lines == []
    st = {r["key"]: r["status"] for r in rep["elements"]}
    assert st == {"WP.POOL_TANK.POOL_MEMBRANE[m2]/POOL-1/BASE_AND_OUTER_WALLS": "MISSING",
                  "WP.POOL_TANK.POOL_PROTECTION_SCREED[m3]/POOL-1/BASE_AND_OUTER_WALLS": "MISSING",
                  "WP.POOL_TANK.TANK_MEMBRANE[m2]/TANK-01/ALL_FACES": "NOT_APPLICABLE"}


def test_t236_schema_reports_gaps_never_complete():
    els, lines, lk, _rep = A.family_report(A.WET)
    assert A.t236(A.WET, els, lines, lk) == {"status": "GAPS", "found": 121, "measured": 81, "held": 32, "missing": 8,
                                             "excluded": 0}
    els, lines, lk, _rep = A.family_report(A.ROOF)
    assert A.t236(A.ROOF, els, lines, lk)["status"] == "GAPS"


def test_committed_outputs_are_the_reproduced_ones(tmp_path):
    A.main(["--out", str(tmp_path)])
    for f in ("WP_WET_ROOF_POOL_INVENTORY_T303.csv", "WP_LINE_COUNTABILITY_T303.csv", "WP_FAMILIES_REPORT_T303.json"):
        assert (tmp_path / f).read_bytes() == (A.HERE / f).read_bytes(), f
    with open(A.HERE / "WP_WET_ROOF_POOL_INVENTORY_T303.csv", encoding="utf-8") as fh:
        assert sum(1 for _ in csv.DictReader(fh)) == 121 + 16 + 3
