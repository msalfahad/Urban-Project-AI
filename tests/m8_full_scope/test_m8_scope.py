"""M8 full-scope engine (conventions V6): stairs measured from their drawn runs, completeness findings measured or
bounded (engine.source.scope_quantities), the bounded total, and the gates that keep V5 and the frozen packages
unchanged. Unit cases use small hand-built geometry; whole-route cases use tools/synthetic_villa_m8 (the M6 villa with
the design of every scope element). Synthetic drawings share the generator's drafting assumptions: these tests prove
the rules read geometry and printed notes and keep their properties, not real-drawing accuracy."""

from __future__ import annotations

import json
import math
from pathlib import Path

import pytest

from engine.source import concrete_completeness as CC
from engine.source import family_coverage as FC
from engine.source import generic_route as GR
from engine.source import provisional_estimate as PE
from engine.source import scope_quantities as SQ

ROOT = Path(__file__).resolve().parents[2]
V5 = "engine/profiles/URBAN_M7_GENERIC_CONVENTIONS_V5.json"
V6 = "engine/profiles/URBAN_M8_GENERIC_CONVENTIONS_V6.json"


def _conv(path):
    return PE.load_conventions(str(ROOT / path))


# ---------------------------------------------------------------- conventions and gates
def test_v6_is_v5_plus_the_m8_conventions_with_ranges_and_rationale():
    v5 = json.loads((ROOT / V5).read_text(encoding="utf-8"))
    v6 = json.loads((ROOT / V6).read_text(encoding="utf-8"))
    old = {c["id"]: c for c in v5["conventions"]}
    new = {c["id"]: c for c in v6["conventions"]}
    assert all(new[k] == c for k, c in old.items())               # V5 conventions carried unchanged
    m8 = [c for k, c in new.items() if k not in old]
    assert len(m8) >= 30
    for c in m8:
        assert c["rationale"] and c["source"] and c["provenance"] in PE.PROVENANCE
        if c["kind"] == "number":
            assert c["low"] <= c["base"] <= c["high"]
    conv = _conv(V6)
    assert SQ.enabled(conv) and not SQ.enabled(_conv(V5))


def test_v5_detect_options_are_unchanged_by_the_m8_switches():
    o5, o6 = GR.detect_options(_conv(V5)), GR.detect_options(_conv(V6))
    assert "scope_from_findings" not in o5 and "tread_angle_wrap" not in o5
    assert o6["scope_from_findings"] and o6["tread_angle_wrap"]
    assert {k: v for k, v in o6.items() if k in o5} == o5


# ---------------------------------------------------------------- printed dimension notes
def _t(x, y, s):
    return {"x": x, "y": y, "norm": s, "sheet": "SH01"}


def test_notes_beside_an_element_are_read_in_metres_and_the_nearest_wins():
    box = (0.0, 0.0, 2.0, 2.0)
    texts = [_t(0.5, -0.4, "DEPTH 1.65 M, FLOOR 250"), _t(1.0, 2.6, "RISER 165, WAIST 150"),
             _t(1.0, -1.4, "DEPTH 1.20 M"), _t(9.0, 9.0, "DEPTH 1.90 M")]
    n = SQ.notes_in_box(texts, box, 1.0)
    assert n["height"] == [1.65]                           # the nearer depth; the far one is a neighbour's
    assert n["floor"] == [0.25] and n["riser"] == [0.165] and n["waist"] == [0.15]
    assert "rise" not in n


@pytest.mark.parametrize("raw,unit,kind,expect", [(150, None, "waist", 0.15), (1.5, None, "height", 1.5),
                                                  (160, None, "height", 1.6), (25, None, "thickness", 0.25),
                                                  (200, "MM", "wall", 0.2), (165, "CM", "height", 1.65),
                                                  (5, None, "height", None), (2500, None, "waist", None)])
def test_a_printed_number_takes_the_one_plausible_unit(raw, unit, kind, expect):
    assert SQ._dim_value(raw, unit, kind) == expect


# ---------------------------------------------------------------- stairs
def _line(eid, a, b, layer="ST"):
    return {"eid": eid, "type": "LINE", "a": a, "b": b, "layer": layer, "len": math.dist(a, b),
            "pts": [a, b], "box": (min(a[0], b[0]), min(a[1], b[1]), max(a[0], b[0]), max(a[1], b[1]))}


class _Ctx:
    u = 1.0


def test_a_dog_leg_drawing_is_two_flights_and_a_missing_tread_line_is_counted():
    ents = []
    for k in range(11):                                     # left flight, 11 lines at 0.30
        ents.append(_line(f"L{k}", (0.0, 0.3 * k), (1.15, 0.3 * k)))
    for k in range(11):                                     # right flight beside it, one line not drawn
        if k != 3:
            ents.append(_line(f"R{k}", (1.35, 0.3 * k + 0.05), (2.5, 0.3 * k + 0.05)))
    runs = SQ._flights(_Ctx(), ents)
    assert sorted(r["n_lines"] for r in runs) == [11, 11]
    assert all(abs(r["going_m"] - 0.3) < 1e-9 and abs(r["width_m"] - 1.15) < 1e-9 for r in runs)


def test_lines_drawn_the_other_way_are_one_direction_for_the_slab_engine():
    from engine.source import slab_engine as SE
    # a hair above the horizontal reads 0.00000008 degrees, a hair below 179.99999992 (modulo 180)
    segs = [{"id": f"s{k}", "layer": "ST", "a": (0.0, 0.3 * k), "b": (1.2, 0.3 * k + (1e-9 if k % 2 else -1e-9))}
            for k in range(8)]
    assert SE._tread_family_of(segs, 1.0, 4, wrap=True)["n"] == 8
    plain = SE._tread_family_of(segs, 1.0, 4)
    assert plain is None or plain["n"] < 8                  # the frozen binning splits them (kept for V5)


# ---------------------------------------------------------------- box structures and domes
def _rect(prefix, x0, y0, x1, y1, layer="S-POOL", gap=0.0):
    g = gap
    return [_line(f"{prefix}1", (x0 + g, y0), (x1 - g, y0), layer), _line(f"{prefix}2", (x1, y0 + g), (x1, y1 - g), layer),
            _line(f"{prefix}3", (x1 - g, y1), (x0 + g, y1), layer), _line(f"{prefix}4", (x0, y1 - g), (x0, y0 + g), layer)]


def _finding(**kw):
    f = {"FINDING_ID": "CC-test", "KIND": "DRAWN_NOT_MEASURED", "FAMILY": "POOL", "CONFIDENCE": "MEDIUM",
         "SHEET": "SH01", "STOREY": "FOUNDATION", "BOX_M": (0.0, 0.0, 2.0, 4.0), "EVIDENCE": "", "MAGNITUDE": {},
         "VOLUME_LOW_M3": None, "VOLUME_HIGH_M3": None}
    f.update(kw)
    return f


def test_a_double_outline_is_a_ring_and_inner_faces_broken_at_the_corners_give_the_wall():
    conv_t = (0.2, 0.25, 0.3)
    ring = _rect("o", 0, 0, 2, 4) + _rect("i", 0.25, 0.25, 1.75, 3.75)
    w, outer, inner, basis = SQ._wall_geometry(_Ctx(), _finding(), ring, conv_t)
    assert abs(outer - 8.0) < 1e-9 and abs(inner - 5.25) < 1e-9 and abs(w[1] - 2.75) < 1e-9 and "ring" in basis
    broken = _rect("o", 0, 0, 2, 4) + _rect("i", 0.2, 0.2, 1.8, 3.8, gap=0.1)
    w, outer, _, basis = SQ._wall_geometry(_Ctx(), _finding(), broken, conv_t)
    assert abs(w[1] - (12.0 * 0.2 - 4 * 0.04)) < 1e-9 and "inner faces" in basis
    single = _rect("o", 0, 0, 2, 4)
    w, _, _, basis = SQ._wall_geometry(_Ctx(), _finding(), single, conv_t)
    assert w[0] < w[1] < w[2] and "convention" in basis


def test_a_family_is_settled_only_when_layer_and_notes_agree():
    assert SQ._settled(_finding(EVIDENCE="layer S-POOL: 8 entities; notes: POOL; layer suggests POOL"))
    assert not SQ._settled(_finding(EVIDENCE="layer POOL: 8 entities; notes: LIFT; layer suggests POOL",
                                    FAMILY="LIFT"))
    assert not SQ._settled(_finding(CONFIDENCE="LOW"))
    assert not SQ._settled(_finding(EVIDENCE="layer 9: 8 entities; could be LIFT or POOL"))


def test_the_dome_shell_is_a_spherical_cap():
    r, h, t = 1.5, 0.75, 0.12
    lo, base, hi = SQ._combo(lambda hh, tt: math.pi * (r * r + hh * hh) * tt, (h, h, h), (t, t, t))
    assert abs(base - math.pi * (r * r + h * h) * t) < 1e-12 and lo == base == hi


@pytest.mark.parametrize("sizes,expect", [([20.0, 60.0], (0.2, 0.6)), ([200.0, 600.0], (0.2, 0.6)),
                                          ([25, 50], (0.25, 0.5))])
def test_a_schedule_row_section_is_read_in_cm_or_mm(sizes, expect):
    assert SQ._row_section_m(sizes) == pytest.approx(expect)


# ---------------------------------------------------------------- bounds and totals
def test_bounded_total_counts_every_finding_once():
    items = [PE.item(item_id="P-C:A", component_id="A", trade="CONCRETE", family="SLABS", storey="GF",
                     category="PROVISIONAL", low=9.0, base=10.0, high=11.0, formula="x", assumptions=["SLAB_STEP_DROP_M"],
                     support="CONVENTION_ONLY", confidence="LOW", source="t"),
             PE.item(item_id="U-C:B", component_id="B", trade="CONCRETE", family="BEAMS", storey="GF",
                     category="UNRESOLVED", exposure_low=1.0, exposure_high=2.0, blocker="X", support="NO_GEOMETRY",
                     confidence="LOW", source="t")]
    bounds = [{"FINDING_ID": "f1", "SCOPE_STATE": "BOUNDED", "CLASS": "RC", "LOW_M3": -0.5, "HIGH_M3": 3.0},
              {"FINDING_ID": "f2", "SCOPE_STATE": "HELD_BY_ITEMS", "CLASS": "RC", "LOW_M3": 0.0, "HIGH_M3": 0.0,
               "RULE": "HELD_BY_ITEMS"},
              {"FINDING_ID": "f3", "SCOPE_STATE": "MEASURED", "CLASS": "RC", "LOW_M3": 9.0, "HIGH_M3": 11.0,
               "RULE": "MEASURED"},
              {"FINDING_ID": "f4", "SCOPE_STATE": "BOUNDED", "CLASS": "PLAIN", "LOW_M3": 0.0, "HIGH_M3": 4.0,
               "RULE": "SITE_FILL"}]
    for b in bounds:
        b.setdefault("RULE", "R")
    T = SQ.totals(items, bounds)
    assert T["RC"]["bounded_low"] == pytest.approx(9.0 + 1.0 - 0.5)
    assert T["RC"]["bounded_high"] == pytest.approx(11.0 + 2.0 + 3.0)
    assert T["PLAIN"]["bounded_high"] == pytest.approx(4.0) and T["findings_without_range"] == 0


def test_family_coverage_without_bounds_keeps_the_frozen_states():
    D = {"sheets": {}, "model": {"texts": []}}
    a = FC.coverage(D, [], [], {"POOL": {"keywords": ["POOL"], "n_texts": 1, "sheets": ["SH01"]}})
    b = FC.coverage(D, [], [], {"POOL": {"keywords": ["POOL"], "n_texts": 1, "sheets": ["SH01"]}}, bounds=[
        {"FAMILY": "POOL", "SCOPE_STATE": "BOUNDED", "LOW_M3": 0.0, "HIGH_M3": 5.0}])
    pa = next(r for r in a if r["FAMILY"] == "POOL")
    pb = next(r for r in b if r["FAMILY"] == "POOL")
    assert pa["STATE"] == "DETECTED_NOT_QUANTIFIED" and pb["STATE"] == "BOUNDED_NOT_MEASURED"


# ---------------------------------------------------------------- whole route on synthetic villas
ezdxf = pytest.importorskip("ezdxf")


@pytest.fixture(scope="module")
def villa(tmp_path_factory):
    from tools import synthetic_villa_m8 as SM8
    from tools import urban_boq_m2 as CLI
    td = tmp_path_factory.mktemp("m8villa")
    dxf = SM8.generate(td, 21)
    prof = str(td / "villa_m8_21.profile.json")
    R6 = CLI.compute([str(dxf)], profile=prof, route="G", conventions=str(ROOT / V6), completeness=True)
    R5 = CLI.compute([str(dxf)], profile=prof, route="G", conventions=str(ROOT / V5), completeness=True)
    T = json.loads((td / "villa_m8_21.truth.json").read_text(encoding="utf-8"))
    return {"R6": R6, "R5": R5, "T": T, "dxf": dxf, "prof": prof, "dir": td}


def test_every_finding_has_a_range_and_every_scope_item_is_a_valid_provisional_item(villa):
    R6 = villa["R6"]
    sc = R6["generic"]["scope"]
    assert sc["totals"]["findings_without_range"] == 0
    assert {b["FINDING_ID"] for b in sc["bounds"]} >= {f["FINDING_ID"] for f in R6["generic"]["completeness"]["findings"]}
    PE.check(R6["items"], R6["conv"])
    for it in sc["items"]:
        assert it["category"] == "PROVISIONAL" and it["assumptions"] and it["low"] <= it["base"] <= it["high"]
    reg = {r["COMPONENT_ID"]: r for r in R6["generic"]["register"]}
    assert all(reg[it["component_id"]]["REBAR_STATE"] == "MISSING_DATA" for it in sc["items"])
    assert any(b["ITEM"] == "F.000" for b in R6["boq"])


def test_v5_has_no_scope_pass_and_the_core_families_are_identical(villa):
    R5, R6 = villa["R5"], villa["R6"]
    assert "scope" not in R5["generic"] and not any(i["component_id"].startswith("SCOPE:") for i in R5["items"])
    core = ("FOOTINGS", "COLUMNS", "BEAMS", "SLABS", "GROUND_BEAMS", "GROUND_SLAB")

    def q(R):
        return sorted((i["item_id"], i["category"], round(i.get("base") or 0, 9), round(i.get("exposure_high") or 0, 9))
                      for i in R["items"] if i["family"] in core)
    assert q(R5) == q(R6)


def test_each_drawn_scope_element_is_measured_or_bounded_with_its_truth_in_range(villa):
    from tools import m8_evaluate as EV
    R6, T = villa["R6"], villa["T"]
    recs = EV.engine_records(R6)
    sc = R6["generic"]["scope"]
    asg = EV.assign(T["m8"]["elements"], recs)
    for el in T["m8"]["elements"]:
        e = EV.score_element(el, recs, sc["findings"], asg.get(el["id"], []))
        assert e["detected"] and e["outcome"] in ("MEASURED", "BOUNDED"), e
        assert e["in_range"], e
        if e["printed"] and e["outcome"] == "MEASURED":
            assert abs(e["base_error_rel"]) <= 0.02, e


def test_scope_items_keep_their_volumes_when_the_drawing_is_moved_rotated_or_re_unit(villa):
    from tools import m7_metamorphic as MM
    r = MM.run(villa["dxf"], profile=villa["prof"], conventions=str(ROOT / V6), work=str(villa["dir"]),
               ops=("translate", "rot90", "rot180", "reorder", "dup_text", "explode", "units_m"), completeness=True)
    bad = {op: (v.get("error") or v["differences"][:3]) for op, v in r["ops"].items() if op in r["failed"]}
    assert not bad, bad


def test_a_furniture_layer_changes_no_measured_item(villa):
    """the unrelated furniture layer may widen the bounded range (its column-sized rectangles are reported 'confirm
    it is a column'), but it never becomes a measured pool, pit, tank, dome or stair."""
    from tools import m7_metamorphic as MM
    r = MM.run(villa["dxf"], profile=villa["prof"], conventions=str(ROOT / V6), work=str(villa["dir"]),
               ops=("noise_layer",), completeness=True)
    diffs = r["ops"]["noise_layer"].get("differences") or []
    assert r["ops"]["noise_layer"]["ok"]
    assert all(d["key"].startswith("SCOPE|BOUNDED") for d in diffs), diffs


def test_a_winder_on_the_topmost_plan_is_left_to_the_scope_pass(tmp_path):
    """dome ribs fanning about one point on the top roof plan are not a stair (seed 9 draws a ribbed dome there)."""
    from tools import synthetic_villa_m8 as SM8
    from tools import urban_boq_m2 as CLI
    dxf = SM8.generate(tmp_path, 9)
    R = CLI.compute([str(dxf)], profile=str(tmp_path / "villa_m8_9.profile.json"), route="G",
                    conventions=str(ROOT / V6), completeness=True)
    assert not any(i["family"] == "STAIRS" and i["storey"] == "1F" for i in R["items"])
    assert any(r["KIND"] == "STAIR_WINDER_ON_TOP_PLAN" for r in R["generic"]["risk"])
    T = json.loads((tmp_path / "villa_m8_9.truth.json").read_text(encoding="utf-8"))
    stair = next(e for e in T["m8"]["elements"] if e["kind"] == "STAIR")
    assert any(i["family"] == "STAIRS" and i["storey"] == "GF" for i in R["items"]), stair
