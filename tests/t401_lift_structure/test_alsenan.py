"""T-401 on the development villa: LIFT_STRUCTURE_V1 on the own reads (research/agents_t401/t401_alsenan.py SPEC) and the
committed outputs of the run against the candidate of record ARCH_TAKEOFF_V3.0.32 (V3_0_32_BOQ_LINES.json 0c8bfbe6, own
reproduction). Private inputs are not needed: the committed CSV / JSON are pinned."""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
D = ROOT / "research" / "agents_t401"
sys.path.insert(0, str(D))
import lift_structure_v1 as X  # noqa: E402
import t401_alsenan as A  # noqa: E402

S = json.loads((D / "summary_t401.json").read_text(encoding="utf-8"))


def rows(name):
    with (D / name).open(encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def spec(**kw):
    st = [{"name": s["name"], "ffl": s["ffl"], "next_ffl": s["next_ffl"], "shaft": s["shaft"],
           "ring_beams": [{"mark": m, "length": 1.0, "depth": 0.4} for m, _ in s["bands"]]} for s in A.STOREYS]
    d = dict(A.SPEC, storeys=st, bind={})
    d.update(kw)
    return d


def test_ring_from_the_drawn_ring_and_columns():
    led = X.build(spec())
    g = led["ring"]
    assert g["gross_m2"] == pytest.approx(1.60) and g["net_m2"] == pytest.approx(1.10)    # 2.20^2 - 1.80^2 - 0.50
    assert g["runs_m"] == pytest.approx({"S": 1.80, "N": 1.80, "W": 1.20, "E": 0.70})       # = T-204 open runs
    assert S["ring"]["net_m2"] == pytest.approx(1.10) and S["ring"]["run_total_m"] == pytest.approx(5.50)


def test_pit_wall_held_by_two_facts_never_zero():
    c = {r["component_id"]: r for r in rows("COMPONENTS_T401.csv")}
    w = c["PIT_WALL"]
    assert w["status"] == X.MISSING and w["value"] == "" and w["candidate_line"] == "MISSING"
    assert "pit depth" in w["missing"]
    # a supplier depth below the F.F.L. alone does not fix the wall: the GF build-up is unprinted (T-206)
    led = X.build(spec(pit_depth={"value": 1.40, "basis": X.SUPPLIER, "datum": X.WALL_TOP_FFL}))
    w2 = {x["id"]: x for x in led["components"]}["PIT_WALL"]
    assert w2["value"] is None and w2["missing"][0] == "floor build-up F.F.L. -> slab-on-grade top"


def test_freelancer_neck_height_as_pit_depth_refused():
    with pytest.raises(X.Refused) as e:
        X.build(spec(pit_depth={"value": 1.50, "basis": "FREELANCER", "datum": X.WALL_TOP_SLAB}))
    assert e.value.code == "DEPTH_DEFAULTED"


def test_tie_beam_missing_with_drawn_length():
    c = {r["component_id"]: r for r in rows("COMPONENTS_T401.csv")}
    t = c["TIE_BEAM:GF"]
    assert t["status"] == X.MISSING and t["value"] == "" and "5.500 m" in t["note"]
    assert "TIE_BEAM:1F" not in c and "TIE_BEAM:2F" not in c        # 4.20 m storeys <= 4.30 (note 19)


def test_ring_beams_bound_and_equal_to_hand():
    assert S["ring_beams_line_m3"] == pytest.approx({"GF": 0.650, "1F": 0.650, "2F": 0.464})
    assert S["ring_beams_hand_m3"] == pytest.approx(S["ring_beams_line_m3"])
    c = [r for r in rows("COMPONENTS_T401.csv") if r["component_id"].startswith("RING_BEAM:")]
    assert len(c) == 12 and all(r["candidate_line"].startswith("L-") for r in c)
    assert len({r["candidate_line"] for r in c}) == 12


def test_raft_shaft_cap_and_openings():
    c = {r["component_id"]: r for r in rows("COMPONENTS_T401.csv")}
    assert float(c["RAFT"]["line_value"]) == pytest.approx(11.385) and float(c["RAFT"]["value"]) == pytest.approx(11.385)
    assert float(c["SHAFT_SLAB:2F"]["line_value"]) == pytest.approx(3.24 * 0.16)          # roof panel over the shaft
    assert c["SHAFT_SLAB:GF"]["owner_trade"] == "NONE" and c["SHAFT_SLAB:1F"]["owner_trade"] == "NONE"
    assert S["lift_lines_in_candidate"] == []                                             # no pit-wall line in V3.0.32


def test_overlap_census_zero_double_and_ground_partition():
    o = rows("OVERLAP_T401.csv")
    assert [r for r in o if r["kind"] == "DOUBLE"] == []
    f = rows("FACES_T401.csv")
    for lv in ("GF", "1F", "2F"):                           # ring band 1.60 = beams + columns on every suspended floor
        band = sum(float(r["on_ring_band_m2"]) for r in f if r["level"] == lv)
        assert band == pytest.approx(1.60, abs=2e-3)
    g = S["ground"]
    assert g["ring_net_from_pieces_m2"] == pytest.approx(1.10)                            # T-391 own pieces
    assert g["ring_pieces_in_cell_m2"] == pytest.approx(0.96) and g["shaft_face_m2"] == pytest.approx(3.24)
    cell = next(r for r in f if r["face"] == "SITE-c1089bdb4cfcdc4a")
    gap = next(r for r in f if r["face"] == "SITE-47d689fe2121d8c6")
    assert float(cell["on_shaft_m2"]) + float(gap["on_shaft_m2"]) == pytest.approx(3.24, abs=1e-3)
    assert gap["lines"] == "NO_LINE" and cell["lines"] == "L-41cfb82ed733f4d6e3a5"


def test_held_cell_valued_over_the_ring_would_be_refused():
    # the V3.0.32 held cell covers the shaft and 0.88 m2 of the ring band: valued, it is refused both ways
    claims = [{"line": "L-41cfb82e", "family": "SLAB", "level": "GROUND", "rect": [-1.0, -1.0, 1.0, 2.2]},
              {"line": "LIFT_PIT:WALLS", "family": "PIT_WALL", "valued": False, "rect": [0.2, 0.0, 2.0, 0.2]}]
    with pytest.raises(X.Refused) as e:
        X.claims_check(A.SPEC["ring_outer"], A.SPEC["shaft"], A.SPEC["columns"], claims)
    assert e.value.code == "SHAFT_VOID_AS_SLAB"


def test_freelancer_row_closes_on_two_named_causes():
    r = S["freelancer_reconciliation"]
    assert r["freelancer_m3"] == pytest.approx(2.40) and r["plan_difference_m2"] == pytest.approx(0.0)
    assert r["columns_in_his_ring_m3"] == pytest.approx(-0.75) and r["net_ring_at_his_height_m3"] == pytest.approx(-1.65)
    assert r["closure_m3"] == pytest.approx(0.0, abs=1e-9)
    assert S["freelancer_lift_rows"] == [{"numbers": [8, 0.2, 1.5, pytest.approx(2.4), 1, pytest.approx(2.4)],
                                          "row": 11, "sheet_index": 3}]


def test_columns_bound_every_storey():
    c = rows("COLUMNS_T401.csv")
    conc = [r for r in c if r["item_code"].startswith("STR.CONC")]
    assert sorted({r["mark"] for r in conc if r["sheet"] == "SH10"}) == ["C1", "C2", "C9"]
    assert len([r for r in conc if r["sheet"] == "SH10"]) == 4                              # 4 necks, all HELD
    assert all(r["value_m3"] == "" for r in conc if r["sheet"] == "SH10")
    gf = sorted(float(r["value_m3"]) for r in conc if r["sheet"] == "SH12" and r["value_m3"]
                and float(r["value_m3"]) in (0.45, 1.125))
    assert gf == pytest.approx([0.45, 0.45, 0.45, 1.125])                                   # GF 4.50 x section


def test_dependent_lines_listed():
    d = {x["element"]: x for x in S["dependent_lift_lines"]}
    assert d["WPF:LIFT_PIT_MEMBRANE_FIXED"]["value"] == pytest.approx(47.43)
    assert d["WPF:LIFT_PIT_MEMBRANE_WALLS"]["value"] is None
    assert d["FW:FACE:T332-LIFT-PIT-INNER"]["value"] is None and d["FW:FACE:T332-LIFT-PIT-OUTER"]["value"] is None
