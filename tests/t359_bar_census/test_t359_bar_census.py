"""T-359 bar-detail census: synthetic villa (not the development villa) + adverse cases + one regression on the
committed development-villa input. No kg, no bar count is ever produced."""
import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("t359", ROOT / "research/agents_t359/t359_bar_census.py")
t359 = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(t359)

P = lambda ref="sheet S-5 detail 3", note="": {"state": "PRINTED", "ref": ref, "note": note}
N = lambda note="": {"state": "NOT_PRINTED", "note": note}
NA = lambda note="": {"state": "NOT_APPLICABLE", "note": note}
FULL = {"layer": P(), "direction": P(), "extent": P(), "end_shape": P()}


def villa(pops, released=(), required=("WALL",)):
    return {"rfi_register": ["RFI-X01", "RFI-X02"], "answered_rules": ["RULE-A"], "elements_required": list(required),
            "released_lines": list(released), "populations": pops}


def pop(pid, label, attrs=None, element="WALL", eid="W-1", comp="vertical bars", **kw):
    return {"pop_id": pid, "element": element, "element_id": eid, "component": comp, "label": label,
            "attrs": dict(FULL if attrs is None else attrs), **kw}


# ---- notation before arithmetic -------------------------------------------------------------------------------
def test_rate_is_a_density_not_a_count():
    p = t359.parse_notation("10%%c12/m")
    assert p["kind"] == t359.RATE and p["n_per_m"] == 10 and p["d"] == 12 and p["count"] is None


def test_adverse_spacing_never_read_as_count():
    p = t359.parse_notation("ø12/20cm")
    assert p["kind"] == t359.SPACING and p["count"] is None and p["s_m"] == pytest.approx(0.20)
    st = t359.notation_states("ø12/20cm")
    assert "not a count" in st["spacing_or_count"]["note"]


def test_explicit_count_and_count_per_spacing():
    assert t359.parse_notation("4%%c20")["count"] == 4
    p = t359.parse_notation("2ø14/20cm")
    assert p["kind"] == t359.COUNT_PER_SPACING and p["count"] is None
    assert t359.notation_states("2ø14/20cm")["spacing_or_count"]["state"] == "NOT_PRINTED"


def test_units_mm_suffix_and_missing_spacing_unit():
    p = t359.parse_notation("%%C12MM/15cm")
    assert p["d"] == 12 and p["s_m"] == pytest.approx(0.15)
    # a spacing printed without a unit (could be cm or mm) is not printed
    assert t359.notation_states("ø12/150")["spacing_or_count"]["state"] == "NOT_PRINTED"
    assert t359.notation_states("ø8/15")["spacing_or_count"]["state"] == "NOT_PRINTED"


def test_label_independent_of_rotation_and_qualifiers():
    # the same label read from a rotated / mirrored view or with a layer qualifier keeps its meaning
    for lab in ("3%%c16 (T&B)", "3ø16", " 3 Ø 16 ", "3%%C16/Top"):
        assert t359.parse_notation(lab)["count"] == 3


# ---- countability ---------------------------------------------------------------------------------------------
def test_normal_population_with_every_attribute_printed_is_countable_now():
    out = t359.run(villa([pop("A", "8ø14/m")]))
    assert out["results"]["A"]["status"] == "COUNTABLE_NOW" and out["kg_computed"] == 0


def test_adverse_bar_mark_without_diameter_is_not_counted():
    with pytest.raises(ValueError):           # blocking diameter asked nowhere and no gap named
        t359.run(villa([pop("A", "12/20cm")]))
    out = t359.run(villa([pop("A", "12/20cm", gap="G-1")]))
    assert out["results"]["A"]["status"] == "GAP" and "diameter" in out["results"]["A"]["blocking"]


def test_diameter_supplied_by_another_print_needs_its_reference():
    a = dict(FULL, diameter={"state": "PRINTED", "ref": "dxf 1A2B", "note": "d 12 mm"})
    out = t359.run(villa([pop("A", "12/20cm", a)]))
    assert out["results"]["A"]["status"] == "COUNTABLE_NOW"
    a_noref = dict(FULL, diameter={"state": "PRINTED", "note": "d 12 mm"})
    with pytest.raises(ValueError):
        t359.run(villa([pop("A", "12/20cm", a_noref)]))


def test_adverse_stair_bar_from_a_typical_detail_is_refused():
    st = pop("S", "6ø14/m", element="STAIR", eid="ST-9", comp="top bars", typical_only=True, gap="G-TYP")
    out = t359.run(villa([st], required=("STAIR",)))
    r = out["results"]["S"]
    assert r["status"] == "GAP" and all(r["attrs"][a]["state"] != "PRINTED" for a in ("mark", "diameter"))


def test_blocking_attribute_named_in_rfi_gives_countable_after():
    a = dict(FULL, extent=N("height not printed"))
    out = t359.run(villa([pop("A", "8ø14/m", a, rfi={"extent": "RFI-X02"})]))
    assert out["results"]["A"]["status"] == "COUNTABLE_AFTER" and out["results"]["A"]["after"] == ["RFI-X02"]


def test_unknown_rfi_and_unanswered_rule_refused():
    a = dict(FULL, extent=N())
    with pytest.raises(ValueError):
        t359.run(villa([pop("A", "8ø14/m", a, rfi={"extent": "RFI-NOPE"})]))
    b = dict(FULL, end_shape={"state": "RULE", "rule": "RULE-UNANSWERED"})
    with pytest.raises(ValueError):
        t359.run(villa([pop("A", "8ø14/m", b)]))
    c = dict(FULL, end_shape={"state": "RULE", "rule": "RULE-A"})
    assert t359.run(villa([pop("A", "8ø14/m", c)]))["results"]["A"]["status"] == "COUNTABLE_NOW"


def test_missing_attribute_reading_and_missing_element_refused():
    with pytest.raises(ValueError):
        t359.run(villa([pop("A", "8ø14/m", {"layer": P(), "direction": P(), "extent": P()})]))
    with pytest.raises(ValueError):
        t359.run(villa([pop("A", "8ø14/m")], required=("WALL", "POOL")))


def test_not_drawn_is_its_own_status_never_zero():
    out = t359.run(villa([pop("A", None, {}, not_drawn=True, rfi={"all": "RFI-X01"})]))
    r = out["results"]["A"]
    assert r["status"] == "NOT_DRAWN" and r["after"] == ["RFI-X01"] and "kg" not in r


# ---- no double count ------------------------------------------------------------------------------------------
def test_double_count_against_released_lines():
    rel = [{"line_id": "BM-9 bottom", "element_id": "RING-1", "component": "bottom bars"}]
    owned = pop("R", "3ø18", element="WALL", eid="RING-1", comp="bottom bars", owned_by="beam BM-9")
    assert t359.run(villa([owned], released=rel))["double_count"] == []
    counted = pop("R", "3ø18", element="WALL", eid="RING-1", comp="bottom bars")
    assert t359.run(villa([counted], released=rel))["double_count"] == [{"pop_id": "R", "released_line": "BM-9 bottom"}]
    alias = pop("Q", "3ø18", eid="RING-2", comp="ring bottom", same_physical_bars_as=[["RING-1", "bottom bars"]])
    assert len(t359.run(villa([alias], released=rel))["double_count"]) == 1


def test_duplicate_population_refused():
    with pytest.raises(ValueError):
        t359.run(villa([pop("A", "8ø14/m"), pop("A", "8ø14/m")]))


# ---- r2: label census (every bar label inside a cited detail is tied to a population) ----------------------------
def detail(*labels):
    return [{"detail": "S-7 TANK SECTION", "labels": [{"ref": r, "text": t} for r, t in labels]}]


def test_label_census_normal_every_label_cited():
    d = villa([pop("A", "8ø14/m", labels=["h1", "h2"])])
    d["details"] = detail(("h1", "8ø14/m"), ("h2", "8ø14/m"), ("h3", "10cm PLAIN CONCRETE"), ("h4", "SECTION A"))
    out = t359.run(d)
    assert out["label_census"]["labels_listed"] == 4 and out["label_census"]["labels_cited"] == 2


def test_adverse_uncited_bar_label_inside_the_detail_refused():
    # an exploded bar-shape label (h2) left out of the census: the census refuses to run
    d = villa([pop("A", "8ø14/m", labels=["h1"])])
    d["details"] = detail(("h1", "8ø14/m"), ("h2", "6%%c12/m"))
    with pytest.raises(ValueError, match="cited by no population"):
        t359.run(d)
    # a schedule pointer is a bar label too
    d["details"] = detail(("h1", "8ø14/m"), ("h2", "AS PER SCH."))
    with pytest.raises(ValueError):
        t359.run(d)


def test_adverse_cited_label_missing_from_its_detail_and_orphan_shape_refused():
    d = villa([pop("A", "8ø14/m", labels=["h1", "h9"])])
    d["details"] = detail(("h1", "8ø14/m"))
    with pytest.raises(ValueError, match="no detail lists"):
        t359.run(d)
    d = villa([pop("A", "8ø14/m", labels=["h1"])])
    d["details"] = detail(("h1", "8ø14/m"))
    d["unlabelled_shapes"] = [{"ref": "h7", "tied_to": "NOPE"}]
    with pytest.raises(ValueError):
        t359.run(d)


def test_conflict_between_two_prints_blocks_and_needs_both_refs():
    two = {"state": "CONFLICT", "refs": ["section 7ø12/m", "shape row 7ø14/m"], "note": "d 12 vs d 14"}
    out = t359.run(villa([pop("A", "7ø12/m", dict(FULL, diameter=two), gap="G-9")]))
    assert out["results"]["A"]["status"] == "GAP" and "diameter" in out["results"]["A"]["blocking"]
    with pytest.raises(ValueError):
        t359.run(villa([pop("A", "7ø12/m", dict(FULL, diameter={"state": "CONFLICT", "refs": ["one"]}), gap="G-9")]))


# ---- r2: candidate binding (an integration fills blank lines, never adds) -----------------------------------------
CAND = [{"element_id": "X:POOL:WALL_V", "line_id": "L-1", "measured_net": None},
        {"element_id": "X:POOL:FLOOR", "line_id": "L-2", "measured_net": None},
        {"element_id": "X:BEAM:B1", "line_id": "L-3", "measured_net": 12.5}]


def test_candidate_binding_normal_and_adverse():
    d = villa([pop("A", "8ø14/m", candidate_lines=["POOL:WALL_V"]), pop("B", "6ø12/m", candidate_lines=["POOL:FLOOR"])])
    d["candidate_scope"] = ["POOL:"]
    b = t359.bind_candidates(d, CAND, "X:")
    assert b["lines_in_scope"] == b["lines_bound"] == 2 and b["line_ids"]["X:POOL:WALL_V"] == "L-1"
    d["populations"][1]["candidate_lines"] = []
    d["populations"][1]["no_line_reason"] = "test"
    with pytest.raises(ValueError, match="bound by no population"):     # a blank line left unbound
        t359.bind_candidates(d, CAND, "X:")
    d = villa([pop("A", "8ø14/m", candidate_lines=["POOL:NOPE"])])
    with pytest.raises(ValueError, match="does not exist"):
        t359.bind_candidates(d, CAND, "X:")
    d = villa([pop("A", "8ø14/m", candidate_lines=["BEAM:B1"])])
    with pytest.raises(ValueError, match="already carries a value"):   # never fill a valued line twice
        t359.bind_candidates(d, CAND, "X:")
    with pytest.raises(ValueError, match="no reason"):
        t359.bind_candidates(villa([pop("A", "8ø14/m")]), CAND, "X:")


# ---- regression on the committed development-villa input -------------------------------------------------------
def _dev():
    data = json.loads((ROOT / "research/agents_t359/ALSENAN_BAR_DETAIL_INPUT.json").read_text(encoding="utf-8"))
    return data, t359.run(data)


def test_development_villa_census_regression():
    data, out = _dev()
    assert out["double_count"] == [] and out["kg_computed"] == 0
    assert sum(out["totals"].values()) == len(data["populations"]) == 79
    assert out["totals"] == {"COUNTABLE_NOW": 0, "COUNTABLE_AFTER": 21, "GAP": 38, "OWNED_ELSEWHERE": 10,
                             "NOT_DRAWN": 10}
    # the dome-A ring is the released beam BM-1F-028: never counted again from the dome detail
    assert all(out["results"][f"DOME-A-RING-{c}"]["status"] == "OWNED_ELSEWHERE" for c in "TBSL")
    # E1, D1, tower dome, tank structure: nothing drawn, never 0
    for pid in ("E1-ALL", "D1-ALL", "DOME-T-ALL", "TANK-STRUCT"):
        assert out["results"][pid]["status"] == "NOT_DRAWN"
    # every pool population waits on the flat-floor population (RFI-B-S11), except the deep-end water-face vertical
    # whose diameter the section (1906 7ø12/m) and the shape row (18A8 7ø14/m) print differently
    pool = [p["pop_id"] for p in data["populations"] if p["element"] == "POOL"]
    assert all(out["results"][p]["status"] == "COUNTABLE_AFTER" for p in pool if p != "POOL-R1-WV-IN")
    r1in = out["results"]["POOL-R1-WV-IN"]
    assert r1in["status"] == "GAP" and r1in["attrs"]["diameter"]["state"] == "CONFLICT" and r1in["gap"] == "G-T359-8"
    # p.16 prints the top bars at a foot on a ground beam as 6ø16/m (not 6ø14/m)
    topg = next(p for p in data["populations"] if p["pop_id"] == "ST-01-T-TOPG")
    assert t359.parse_notation(topg["label"])["d"] == 16


def test_development_villa_r2_outer_vertical_and_shape_row():
    data, out = _dev()
    pops = {p["pop_id"]: p for p in data["populations"]}
    # r2: the shallow-end outer vertical is printed by the shape-row label 1929 (6ø12/m), an L into the floor bottom
    r2o = out["results"]["POOL-R2-WV-OUT"]
    assert r2o["status"] == "COUNTABLE_AFTER" and r2o["after"] == ["RFI-B-S11"]
    assert pops["POOL-R2-WV-OUT"]["labels"] == ["dxf 1929"] and "BOTTOM" in r2o["attrs"]["end_shape"]["note"]
    # the eight shape-row labels the r1 census missed are each tied to a population
    cited = {r: [p["pop_id"] for p in data["populations"] if r in p.get("labels", [])]
             for r in ("dxf 187C", "dxf 18A8", "dxf 1860", "dxf 1869", "dxf 18DB", "dxf 18D7", "dxf 1929", "dxf 18DD")}
    assert all(len(v) == 1 for v in cited.values()), cited
    # every bar label in every cited detail is cited (7 listed texts are notes / titles)
    lc = out["label_census"]
    assert lc["labels_listed"] - lc["labels_cited"] == 7 and lc["unlabelled_shapes"] == 2


def test_development_villa_candidate_binding_fills_never_adds():
    data, _ = _dev()
    cand = json.loads((ROOT / "research/agents_t297/CANDIDATE_V3016_REBAR_LINES.json").read_text(encoding="utf-8"))
    b = t359.bind_candidates(data, cand["lines"], data["candidate_prefix"])
    assert b["lines_in_scope"] == b["lines_bound"] == 88      # 20 pool + 67 stair + 1 tank blank lines
