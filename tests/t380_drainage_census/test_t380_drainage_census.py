"""T-380: drainage / water-supply source census (B12-02).

Normal case: a villa that is not Alsenan, counted and measured by hand (a dimensioned run and a vertical run between two
printed levels are lengths; printed chambers, clean-outs and stacks are counts). Adverse: a schematic route measured
as a length, a scaled length, a NOT_PRINTED item written as 0, a legend entry counted as an item, levels in mm, an item
listed twice, a dangling T/B or F/A, a T/B received by a drop without F/A, mirror independence. Then the committed
Alsenan census (no private file).
"""

import importlib.util
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
HERE = os.path.join(ROOT, "research", "agents_t380")


def _load(name):
    spec = importlib.util.spec_from_file_location(name, os.path.join(HERE, name + ".py"))
    mod = importlib.util.module_from_spec(spec)
    if HERE not in sys.path:
        sys.path.insert(0, HERE)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


R = _load("t380_drainage_rules")
A = _load("t380_alsenan")
I = R.Item

# --- villa V (not Alsenan), by hand -------------------------------------------------------------------------------
# GF: two inspection chambers 'IC1', 'IC2' labelled with their sizes; one GCO; drain 'D1' dimensioned 12.40 m on the
#     plan; drain 'D2' drawn only.  Roof +6.20 outlet with a printed outlet level +6.10, RWP to a printed gully at
#     +0.15: vertical 6.10 - 0.15 = 5.95 m.  Stack 'S' 1F T/B -> GF F/A (one stack); RWP 'P' 1F T/B -> GF F/A.
#     Water supply: not on the drainage set (HELD).  Legend lists NRV, drawn nowhere (HELD).
# Hand result: MANHOLE 2, GROUND_CLEAN_OUT 1, SOIL_STACK 1, RAIN_WATER_PIPE 1; D1 = 12.40 m; vertical = 5.95 m;
#              D2 no length; supply HELD; NRV HELD; 2 chains, no finding.


def _villa():
    count = [
        I("IC1", "MANHOLE", "GF", "s1@10,10", R.PRINTED_LABEL),
        I("IC2", "MANHOLE", "GF", "s1@90,10", R.PRINTED_LABEL),
        I("G1", "GROUND_CLEAN_OUT", "GF", "s1@50,40", R.LEGEND_TAG),
        I("S", "SOIL_STACK", "1F-GF", "s1@30,20", R.LEGEND_TAG, diameter="4in", tags=("T/B", "F/A")),
        I("P", "RAIN_WATER_PIPE", "1F-GF", "s1@70,60", R.LEGEND_TAG, diameter="4in", tags=("T/B", "F/A")),
        I("NRV", "NON_RETURN_VALVE", "all", "legend", R.LEGEND_ONLY),
        I("SUP", "SUPPLY_POINT", "all", "searched", R.ABSENT),
    ]
    runs = [
        I("D1", "DRAIN_MAIN", "GF", "s1 IC1-IC2", R.DIMENSION, diameter="6in"),
        I("D2", "SOIL_BRANCH", "GF", "s1 WC-IC1", R.ROUTE_DRAWN),
        I("V1", "RWP_VERTICAL", "1F-GF", "s1 P", R.LEVELS, diameter="4in"),
        I("W", "WATER_SUPPLY", "all", "searched", R.ABSENT),
    ]
    drops = [("S/1F", 1, 30.0, 20.0, ("T/B",)), ("S/GF", 0, 30.0, 20.0, ("F/A",)),
             ("P/1F", 1, 70.0, 60.0, ("T/B",)), ("P/GF", 0, 70.0, 60.0, ("F/A",))]
    return count, runs, drops


def test_villa_counts_by_hand():
    count, runs, _ = _villa()
    c, held = R.counts(count, sheet_not_to_scale=False)
    assert dict(c) == {"MANHOLE": 2, "GROUND_CLEAN_OUT": 1, "SOIL_STACK": 1, "RAIN_WATER_PIPE": 1}
    assert dict(held) == {"NON_RETURN_VALVE": "HELD", "SUPPLY_POINT": "HELD"}


def test_villa_stated_lengths_by_hand():
    _, runs, _ = _villa()
    d1, d2, v1, w = runs
    assert R.length_m(d1, False, stated_length_m=12.40) == pytest.approx(12.40)
    assert R.length_m(v1, False, end_levels=(6.10, 0.15)) == pytest.approx(5.95)
    assert R.status(d2, False) == R.SCHEMATIC_ONLY
    assert R.status(w, False) == R.NOT_PRINTED


def test_villa_stacks_chain():
    _, _, drops = _villa()
    stacks, findings = R.chain_stacks(drops)
    assert sorted(stacks) == [["P/1F", "P/GF"], ["S/1F", "S/GF"]]
    assert findings == []


# --- adverse -------------------------------------------------------------------------------------------------------
def test_schematic_route_never_measured():
    _, runs, _ = _villa()
    with pytest.raises(R.CensusRefused, match="SCHEMATIC_ONLY"):
        R.length_m(runs[1], False, stated_length_m=7.5)
    with pytest.raises(R.CensusRefused, match="not to scale"):
        R.length_m(runs[1], True)


def test_scaled_length_basis_refused():
    with pytest.raises(R.CensusRefused, match="not printed evidence"):
        I("X", "DRAIN_MAIN", "GF", "s1", "SCALED")
    with pytest.raises(R.CensusRefused):
        I("Y", "WATER_TANK", "roof", "s1", "PRACTICE")
    with pytest.raises(R.CensusRefused):
        I("Z", "MANHOLE", "GF", "s1", "FREELANCER")


def test_not_printed_is_held_never_zero():
    count, runs, _ = _villa()
    for it in [count[5], count[6], runs[3]]:
        assert R.quantity(it, False) == "HELD"
        assert R.quantity(it, False) != 0
    with pytest.raises(R.CensusRefused):
        R.length_m(runs[3], False, stated_length_m=0)
    c, held = R.counts(count, False)
    assert "NON_RETURN_VALVE" not in c and held["NON_RETURN_VALVE"] == "HELD"


def test_legend_entry_is_not_an_item():
    it = I("AD", "AREA_DRAIN", "all", "legend", R.LEGEND_ONLY)
    assert R.status(it, True) == R.NOT_PRINTED
    assert R.quantity(it, True) == "HELD"


def test_item_needs_a_printed_basis_to_count():
    it = I("Q", "MANHOLE", "GF", "s1", R.ROUTE_DRAWN)
    with pytest.raises(R.CensusRefused, match="needs a printed"):
        R.status(it, False)


def test_levels_checked():
    _, runs, _ = _villa()
    v1 = runs[2]
    with pytest.raises(R.CensusRefused, match="mm"):
        R.length_m(v1, False, end_levels=(6100.0, 150.0))
    with pytest.raises(R.CensusRefused, match="not above"):
        R.length_m(v1, False, end_levels=(0.15, 6.10))
    with pytest.raises(R.CensusRefused, match="both end levels"):
        R.length_m(v1, False, end_levels=(6.10, None))
    with pytest.raises(R.CensusRefused, match="dimension missing"):
        R.length_m(runs[0], False)


def test_item_listed_twice_refused():
    count, _, _ = _villa()
    with pytest.raises(R.CensusRefused, match="twice"):
        R.counts(count + [count[0]], False)


def test_dangling_tags_refused():
    with pytest.raises(R.CensusRefused, match="T/B with 0"):
        R.chain_stacks([("a", 1, 0.0, 0.0, ("T/B",))])
    with pytest.raises(R.CensusRefused, match="F/A with no matching"):
        R.chain_stacks([("b", 0, 0.0, 0.0, ("F/A",))])
    with pytest.raises(R.CensusRefused, match="no F/A tag"):
        R.chain_stacks([("c", 1, 0.0, 0.0, ("T/B",)), ("d", 0, 0.0, 0.0, ("H/L",))])
    with pytest.raises(R.CensusRefused, match="T/B with 0"):     # offset beyond tolerance
        R.chain_stacks([("e", 1, 0.0, 0.0, ("T/B",)), ("f", 0, 40.0, 0.0, ("F/A",))])


def test_one_sided_link_kept_as_finding():
    stacks, findings = R.chain_stacks([("u", 1, 5.0, 5.0, ()), ("v", 0, 5.0, 5.0, ("F/A",))])
    assert stacks == [["u", "v"]] and len(findings) == 1 and "F/A below" in findings[0]
    stacks, findings = R.chain_stacks([("u", 1, 5.0, 5.0, ("T/B",)), ("v", 0, 5.0, 5.0, (R.UNLABELLED,))])
    assert stacks == [["u", "v"]] and "T/B above" in findings[0]


def test_mirror_and_order_independent():
    _, _, drops = _villa()
    mirrored = [(d[0], d[1], -d[2], d[3], d[4]) for d in reversed(drops)]
    assert sorted(R.chain_stacks(mirrored)[0]) == sorted(R.chain_stacks(drops)[0])


# --- the committed Alsenan census -----------------------------------------------------------------------------------
def test_alsenan_counts_and_held():
    counted, held, stacks, findings, runs = A.run()
    assert dict(counted) == {"MANHOLE": 1, "GROUND_CLEAN_OUT": 2, "CLEAN_OUT": 1, "SOIL_STACK": 4,
                             "RAIN_WATER_PIPE": 5}
    assert set(held) == {"RODDING_EYE", "NON_RETURN_VALVE", "AREA_DRAIN", "SUMP_PUMP", "WATER_TANK",
                         "WATER_HEATER", "SUPPLY_POINT"}
    assert all(v == "HELD" for v in held.values())


def test_alsenan_stacks_match_the_count_items():
    counted, held, stacks, findings, runs = A.run()
    assert len(stacks) == 9
    soil = [s for s in stacks if s[0].startswith("SS-")]
    rwp = [s for s in stacks if s[0].startswith("RWP-")]
    assert len(soil) == counted["SOIL_STACK"] and len(rwp) == counted["RAIN_WATER_PIPE"]
    assert len(findings) == 2


def test_alsenan_no_run_has_a_length():
    for r in A.RUNS:
        st = R.status(r, A.NOT_TO_SCALE)
        assert st in (R.SCHEMATIC_ONLY, R.NOT_PRINTED)
        with pytest.raises(R.CensusRefused):
            R.length_m(r, A.NOT_TO_SCALE, stated_length_m=1.0, end_levels=(9.70, 5.65))
    for v in A.RWP_LEVEL_INDICATORS.values():
        assert v["status"].startswith("HELD")


def test_alsenan_shower_residual_unresolved():
    pops = A.SHOWER_POPULATIONS
    hits = [k for k, v in pops.items() if v == A.FREELANCER_SHOWER]
    assert hits == ["GF + 1F WC rooms (coincidence named by T-370)"]
    assert A.FREELANCER_WET_ROWS["GF"]["bath (حمامات / حمام)"] + A.FREELANCER_WET_ROWS["1F"]["bath (حمام)"] \
        + A.FREELANCER_WET_ROWS["2F"]["bath (حمام)"] == 12
