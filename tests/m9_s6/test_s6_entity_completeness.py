"""M9 S6 Phase 1 - entity completeness. The fills of the drawing are read through ezdxf's own block transforms (every
depth, MINSERT cells expanded, layer-0 inheritance) independently of the plan reader; a filled member-sized shape on a
column layer (or on any layer when the drawing has none) that is not a measured column is a REVIEW_REQUIRED flag on
its room, so a lost column is never silent. A door block inserted at a non-uniform scale is flagged the same way.
(The readers themselves are fixed in S6 Phase 2: here the quantities still differ, but loudly.)"""

from __future__ import annotations

import pytest

ezdxf = pytest.importorskip("ezdxf")

from engine.source import arch_completeness as AC      # noqa: E402
from engine.source import discovery as DS              # noqa: E402
from tools import arch_discovery as AD                 # noqa: E402
from tools import urban_boq_m9 as M9                   # noqa: E402

V2 = "ARCH_TAKEOFF_V2"


def _stage6(arch):
    return arch["discovery"]["stages"]["6_geometry_readiness"]


def test_baseline_columns_are_all_accounted(build):
    _, arch, _ = M9.arch_compute(str(build("base")), method=V2)
    st = _stage6(arch)
    gf = next(c for c in st["column_evidence"] if c["floor"] == "GF")
    assert gf["member_sized"] == gf["on_measured_columns"] == gf["measured_columns"] == 3 and gf["unmeasured"] == 0
    assert not [f for f in st["findings"] if f["code"] == "COLUMN_EVIDENCE_NOT_MEASURED"]


@pytest.mark.parametrize("variant", ["nested_2", "nested_3", "col_minsert", "col_layer0", "col_solid", "col_solid_only",
                                     "col_exploded", "col_two_only"])
def test_a_lost_column_is_a_review_flag_on_its_room(build, variant):
    room, arch, _ = M9.arch_compute(str(build(variant)), method=V2)
    f = [x for x in _stage6(arch)["findings"] if x["code"] == "COLUMN_EVIDENCE_NOT_MEASURED"]
    assert f and f[0]["level"] == DS.REVIEW and f[0]["evidence"]["floor"] == "GF"
    recs = [u for u in room["unresolved"] if u["item"] == "COLUMN_EVIDENCE"]
    assert recs and all(u["cause"] == "SOFTWARE" and u["module_function"] == "arch_completeness.column_evidence"
                        for u in recs)
    assert any(u["room_id"] != "-" for u in recs)                                  # named on the room it stands in


@pytest.mark.parametrize("variant", ["nested_2", "col_minsert", "col_solid"])
def test_fills_the_plan_reader_cannot_read_are_flagged(build, variant):
    room, arch, _ = M9.arch_compute(str(build(variant)), method=V2)
    f = [x for x in _stage6(arch)["findings"] if x["code"] == "FILLS_NOT_READ_IN_PLAN"]
    assert f and f[0]["level"] == DS.REVIEW
    assert any(u["item"] == "UNREAD_FILLS" and u["cause"] == "SOFTWARE" for u in room["unresolved"])


def test_baseline_has_no_unread_fill(build):
    _, arch, _ = M9.arch_compute(str(build("base")), method=V2)
    assert not [x for x in _stage6(arch)["findings"] if x["code"] == "FILLS_NOT_READ_IN_PLAN"]


def test_fills_are_read_in_world_coordinates_at_every_depth(build):
    def centres(name):
        sh = AD.shapes(ezdxf.readfile(str(build(name))))
        return sorted((round(sum(p[0] for p in f["ring"][:4]) / 4, 3), round(sum(p[1] for p in f["ring"][:4]) / 4, 3))
                      for f in sh["fills"])
    assert centres("nested_3") == centres("base")
    m = AD.shapes(ezdxf.readfile(str(build("col_minsert"))))
    assert len(m["fills"]) == 3                                                    # every MINSERT cell
    l0 = AD.shapes(ezdxf.readfile(str(build("col_layer0"))))
    assert {f["layer"] for f in l0["fills"]} == {"A-COL"}                          # layer-0 content inherits


def test_fills_on_other_layers_are_counted_not_flagged_when_a_column_layer_exists():
    S = {"unit_m": 0.001, "column_boxes": [(0, 0, 400, 400)], "faces": []}
    sq = lambda x, y: [(x, y), (x + 400, y), (x + 400, y + 400), (x, y + 400)]  # noqa: E731
    fills = [{"kind": "HATCH", "depth": 0, "layer": "COL", "ring": sq(0, 0)},
             {"kind": "HATCH", "depth": 0, "layer": "FIXTURE", "ring": sq(2000, 0)},
             {"kind": "HATCH", "depth": 2, "layer": "COL", "ring": sq(4000, 0)}]
    ev = AC.column_evidence(S, {"rooms": []}, fills, (-1000, -1000, 9000, 9000), "GF", column_layers=["COL"])
    assert (ev["on_measured_columns"], ev["on_other_layers"], len(ev["unmeasured"])) == (1, 1, 1)
    assert ev["unmeasured"][0]["centre"] == (4200.0, 200.0)
    ev0 = AC.column_evidence(S, {"rooms": []}, fills, (-1000, -1000, 9000, 9000), "GF", column_layers=())
    assert len(ev0["unmeasured"]) == 2                                             # no column layer: every fill


def test_distorted_door_blocks_are_flagged(build):
    room, arch, _ = M9.arch_compute(str(build("nonuniform_door")), method=V2)
    f = [x for x in _stage6(arch)["findings"] if x["code"] == "DOOR_SYMBOLS_DISTORTED"]
    assert {x["evidence"]["floor"] for x in f} == {"GF", "1F"}
    assert any(u["item"] == "DOOR_SYMBOLS" for u in room["unresolved"])
