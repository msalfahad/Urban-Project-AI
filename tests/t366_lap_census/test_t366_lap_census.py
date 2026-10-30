"""T-366 lap-length authority census: synthetic villa K366 (not the development villa) with hand-checked results, the
adverse readings the row names (a 40 d note applied to a group it does not name; a zone guessed; a lap counted in the
net kg) and more, the owner splice formula against the frozen route G form (and the frozen code itself, read only),
and one regression on the committed development-villa input. No kg is ever produced."""
import copy
import importlib.util
import json
import sys
from fractions import Fraction
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


def _load(name, rel):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


t366 = _load("t366", "research/agents_t366/t366_lap_census.py")
E = t366.CensusError

# ---- villa K366: two sheets, one lap note for slab temperature bars, one starter detail, one zone-split note ----------
SOURCES = {
    "K-N4": {"sheet": "K S-1 notes", "handle": "A11", "kind": "NOTE", "category": "LAP_SPLICE",
             "names": ["SLAB_TEMP"], "value_d": {"ANY": 45}, "value_kind": "EXACT", "zones": {"ANY": 45}},
    "K-D2": {"sheet": "K S-3 footing detail", "position": "dimension above the footing top", "kind": "DETAIL",
             "category": "STARTER_BARS", "names": ["STARTER"], "value_d": {"ANY": 50}, "value_kind": "EXACT",
             "zones": {"ANY": 50}, "typical": True},
    "K-N7": {"sheet": "K S-1 notes", "handle": "A17", "kind": "NOTE", "category": "LAP_SPLICE",
             "names": ["COL_MAIN"], "value_d": {"TENSION": 60, "COMPRESSION": 40}, "value_kind": "MINIMUM",
             "zones": {"TENSION": 60, "COMPRESSION": 40}},
}


def pop(pid, group, need="NOT_ESTABLISHED", basis="", auth=(), **kw):
    p = {"id": pid, "family": "K", "group": group, "description": pid, "splice_need": need, "need_basis": basis,
         "authorities": [a if isinstance(a, dict) else {"source": a} for a in auth]}
    p.update(kw)
    return p


def villa(pops=None, stock=None):
    pops = pops if pops is not None else [
        pop("SLAB-TEMP", "SLAB_TEMP", auth=["K-N4"]),
        pop("STARTER", "STARTER", "DRAWN_OVERLAP", auth=["K-D2"]),
        pop("COL", "COL_MAIN", "REQUIRED", "stack 13.2 m > 12 m stock", auth=["K-N7"]),
        pop("BEAM", "BEAM_MAIN", "NOT_REQUIRED", "longest beam bar 6.4 m"),
        pop("GB", "GB_MAIN", "REQUIRED", "ground beam run 15.0 m"),
    ]
    return {"sources": copy.deepcopy(SOURCES), "populations": pops, "required_populations": [p["id"] for p in pops],
            "stock": stock if stock is not None else {"value_m": 12.0, "owner_source": "K owner rule R-1"}}


def rows_by_id(data):
    rows, stock = t366.census(data)
    return {r["id"]: r for r in rows}, stock


# ---- normal case (hand-checked) ----------------------------------------------------------------------------------
def test_villa_k366_normal():
    r, stock = rows_by_id(villa())
    assert r["SLAB-TEMP"]["authority"] == "GENERAL_NOTE" and r["SLAB-TEMP"]["lap_status"] == "PRINTED"
    assert json.loads(r["SLAB-TEMP"]["value_d"]) == {"ANY": 45}
    assert r["STARTER"]["authority"] == "PRINTED_DETAIL" and r["STARTER"]["lap_status"] == "PRINTED_TYPICAL"
    # a zone-split minimum with no printed zone: HELD, both minimums listed, never a range or a pick
    assert r["COL"]["lap_status"] == "HELD_ZONE_NOT_PRINTED" and r["COL"]["zone_printed"] == "no"
    assert json.loads(r["COL"]["value_d"]) == {"COMPRESSION": 40, "TENSION": 60}
    assert r["BEAM"]["authority"] == "NOT_PRINTED" and r["BEAM"]["lap_status"] == "NOT_REQUIRED"
    assert r["GB"]["authority"] == "NOT_PRINTED" and r["GB"]["lap_status"] == "HELD_NO_AUTHORITY"
    assert stock == {"status": "ASSUMED - OWNER-APPROVED", "value_m": 12.0, "source": "K owner rule R-1", "searched": ""}


def test_zone_with_its_own_print_is_accepted():
    pops = [pop("COL", "COL_MAIN", "REQUIRED", "13.2 m", auth=[{"source": "K-N7", "zone": "COMPRESSION",
                                                                  "zone_source": "K S-2 handle B04 'COMPRESSION ZONE'"}])]
    r, _ = rows_by_id(villa(pops))
    assert r["COL"]["lap_status"] == "PRINTED_MINIMUM" and json.loads(r["COL"]["value_d"]) == {"COMPRESSION": 40}


def test_two_authorities_that_disagree_are_a_conflict_not_a_pick():
    src = villa()
    src["sources"]["K-N9"] = {"sheet": "K S-1", "handle": "A19", "kind": "NOTE", "category": "STARTER_BARS",
                              "names": ["STARTER"], "value_d": {"TENSION": 70, "COMPRESSION": 40},
                              "value_kind": "MINIMUM", "zones": {"TENSION": 70, "COMPRESSION": 40}}
    src["populations"][1]["authorities"].append({"source": "K-N9"})
    r, _ = rows_by_id(src)
    assert r["STARTER"]["lap_status"].startswith("CONFLICT_ZONE_NOT_PRINTED")


# ---- adverse cases named by the row -------------------------------------------------------------------------------
def test_a_40d_note_applied_to_a_group_it_does_not_name_is_refused():
    pops = [pop("BEAM", "BEAM_MAIN", "REQUIRED", "beam run 14 m", auth=["K-N4"])]   # temperature-bar note on beam bars
    with pytest.raises(E, match="not group 'BEAM_MAIN'"):
        t366.census(villa(pops))


def test_a_guessed_zone_is_refused():
    pops = [pop("COL", "COL_MAIN", "REQUIRED", "13.2 m", auth=[{"source": "K-N7", "zone": "COMPRESSION"}])]
    with pytest.raises(E, match="guessed zone"):
        t366.census(villa(pops))


def test_a_lap_counted_in_the_net_kg_is_refused():
    with pytest.raises(E, match="inside the net"):
        t366.census(villa([pop("GB", "GB_MAIN", "REQUIRED", "15 m", net_includes_lap=True)]))
    with pytest.raises(E, match="computes no kg"):
        t366.census(villa([pop("GB", "GB_MAIN", "REQUIRED", "15 m", lap_kg=4.2)]))


# ---- further adverse cases ----------------------------------------------------------------------------------------
def test_category_mismatch_refused():
    pops = [pop("STARTER", "STARTER", "DRAWN_OVERLAP", auth=[{"source": "K-D2", "as_category": "LAP_SPLICE"}])]
    with pytest.raises(E, match="category mismatch"):
        t366.census(villa(pops))


def test_unknown_category_and_uncitable_source_refused():
    d = villa()
    d["sources"]["K-N4"]["category"] = "LAP"
    with pytest.raises(E, match="unknown category"):
        t366.census(d)
    d = villa()
    del d["sources"]["K-N4"]["handle"]
    with pytest.raises(E, match="citable"):
        t366.census(d)


def test_every_population_once():
    d = villa()
    d["required_populations"].append("FOOTING")
    with pytest.raises(E, match="missing"):
        t366.census(d)
    d = villa()
    d["populations"].append(copy.deepcopy(d["populations"][0]))
    with pytest.raises(E, match="twice"):
        t366.census(d)


def test_need_without_basis_refused():
    with pytest.raises(E, match="without a basis"):
        t366.census(villa([pop("GB", "GB_MAIN", "REQUIRED", "")]))


def test_stock_never_defaulted():
    assert t366.stock_status({"searched": "all sheets"})["status"] == "HELD"
    assert t366.stock_status({"value_m": 12.0})["status"] == "HELD"            # a value with no source is not a source
    assert t366.stock_status({"printed_handle": "S-1 A30", "value_m": 12.0})["status"] == "PRINTED"


# ---- splice count: owner formula vs the frozen form ----------------------------------------------------------------
@pytest.mark.parametrize("L,S,lap,owner,frozen", [
    ("23.8", "12", "0.48", 2, 1),     # hand: (23.8 - 12) / (12 - 0.48) = 1.024 -> 2; ceil(23.8 / 12) - 1 = 1
    ("35", "12", "0.48", 2, 2),       # hand: 23 / 11.52 = 1.997 -> 2 (3 pieces cover 35.04 m); frozen 2: agrees
    ("23.8", "12", "0.64", 2, 1),
    ("35", "12", "0.64", 3, 2),       # hand: 23 / 11.36 = 2.025 -> 3; frozen 2: short
    ("12.00", "12", "1.2", 0, 0), ("12.01", "12", "1.2", 1, 1), ("22.80", "12", "1.2", 1, 1), ("22.81", "12", "1.2", 2, 1),
])
def test_owner_vs_frozen_counts(L, S, lap, owner, frozen):
    assert t366.owner_laps(L, S, lap) == owner
    assert t366.frozen_form_laps(L, S) == frozen
    assert t366.owner_laps(float(L), int(S), float(lap)) == owner          # read from a float, same exact answer


def test_frozen_safe_window():
    assert t366.frozen_safe_lap_max("35", "12") == Fraction(1, 2)          # frozen right only for laps <= 0.50 m
    assert t366.frozen_safe_lap_max("23.8", "12") == Fraction(1, 5)        # and <= 0.20 m here
    assert t366.frozen_safe_lap_max("11", "12") is None


def test_frozen_form_reproduces_the_frozen_code_read_only():
    sys.path.insert(0, str(ROOT))
    from engine.source.continuous_beams import _with_laps          # frozen module, imported, never edited
    for L, d in ((23.8, 12), (35.0, 12), (23.8, 16), (35.0, 16), (12.0, 16), (24.0, 16)):
        n_code = round((_with_laps(L, d, 40, 12.0) - L) / (40 * d / 1000.0))
        assert n_code == t366.frozen_form_laps(repr(L), "12")


def test_bad_lengths_refused():
    for bad in (True, None, float("nan"), "abc"):
        with pytest.raises(Exception):
            t366.owner_laps(bad, 12, 0.5)
    with pytest.raises(E, match="not shorter"):
        t366.owner_laps(30, 12, 12)


# ---- regression on the committed development-villa input ------------------------------------------------------------
def test_alsenan_committed_input():
    data = json.loads((ROOT / "research/agents_t366/ALSENAN_LAP_AUTHORITY_INPUT.json").read_text(encoding="utf-8"))
    rows, stock = t366.census(data)
    r = {x["id"]: x for x in rows}
    assert len(rows) == 27
    assert sum(x["authority"] != "NOT_PRINTED" for x in rows) == 3
    assert r["SLAB-TEMPERATURE"]["lap_status"] == "PRINTED" and r["SLAB-TEMPERATURE"]["sources"] == "P15N1"
    assert r["NECK-STARTER-SHALLOW"]["lap_status"].startswith("CONFLICT_ZONE_NOT_PRINTED")
    assert r["NECK-STARTER-DEEP"]["lap_status"] == "HELD_ZONE_NOT_PRINTED"
    for pid in ("COL-MAIN", "GB-MAIN", "BW-GB", "CB-BOTTOM", "SLAB-BOTTOM-MAIN"):
        assert r[pid]["lap_status"] == "HELD_NO_AUTHORITY", pid
    assert stock["status"] == "ASSUMED - OWNER-APPROVED" and stock["value_m"] == 12.0
    # the 2,505 candidate lines are all bound (88 pool / stair / tank lines left to T-359)
    b = json.loads((ROOT / "research/agents_t366/LINE_BINDING_T366.json").read_text(encoding="utf-8"))
    assert b["lines"] == 2505 and sum(b["counts"].values()) == 2505
    assert not [k for k in b["counts"] if k.startswith("OUT:UNBOUND")]
    assert b["counts"]["OUT:POOL_STAIR_TANK (T-359 scope, outside the released route)"] == 88
    summ = json.loads((ROOT / "research/agents_t366/T366_SUMMARY.json").read_text(encoding="utf-8"))
    assert summ["kg_computed"] == 0 and summ["candidate_lines_changed"] == 0
