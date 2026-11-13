"""T-744: a room-tag block is text, not a fixture (WET_ROOM_EVIDENCE_V2, engine.source.wet_room_evidence
plan_evidence_v2 / classify_v2). Hand truth from the owner rules and the drawn content, not from engine output (see
plan_t744.py): Q-13 B (the label decides; a name alone is not a fixture; uncertain recognition creates no quantity),
Q-06 (a) (a basin-only space is wet ONLY when a basin is drawn), L-T743-1 (type a fixture from its block content).
V1 (plan_evidence / classify) is kept unchanged: the candidate chain reads it."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import ezdxf
import pytest

from engine.source import wet_room_evidence as W

from . import plan_t744 as N

ROOT = Path(__file__).resolve().parents[2]
F010 = importlib.util.spec_from_file_location("t010_plan_fixtures",
                                              ROOT / "tests/t010_wet_room_evidence/plan_fixtures.py")
P010 = importlib.util.module_from_spec(F010)
F010.loader.exec_module(P010)
S744 = importlib.util.spec_from_file_location("t744_alsenan", ROOT / "research/agents_t744/t744_alsenan.py")
R744 = importlib.util.module_from_spec(S744)
S744.loader.exec_module(R744)

WC_AT, TAG_AT, BASIN_AT = (1300, 2000), (1300, 1100), (2000, 1700)
MIRRORS = [False, True]


def _read(tmp_path, **kw):
    p = tmp_path / "n744.dxf"
    pl, pr = N.villa(p, **kw)
    ents = P010.read_plan(p)
    bt = R744.block_types(ezdxf.readfile(str(p)))
    return ents, bt, pl, pr


def _both(ents, bt, poly):
    v1 = W.plan_evidence(poly, ents, N.ROLES, ents["unit_m"])
    v2 = W.plan_evidence_v2(poly, ents, N.ROLES, ents["unit_m"], block_types=bt)
    return v1, v2


# ------------------------------------------------------------------------------------------------ content table
def test_block_content_table():
    assert W.block_content(["TEXT"]) == W.CONTENT_TAG
    assert W.block_content(["TEXT", "MTEXT", "ATTDEF"]) == W.CONTENT_TAG
    assert W.block_content(["text", "LINE"]) == W.CONTENT_GEOMETRY
    assert W.block_content(["CIRCLE"]) == W.CONTENT_GEOMETRY
    assert W.block_content([]) == W.CONTENT_EMPTY
    assert W.block_content(None) == W.CONTENT_NOT_READ


def test_fixture_reading_verdicts():
    bt = {"WC": ["TEXT", "TEXT"], "WC2": ["LINE", "CIRCLE"], "WC-E": [], "BED": ["TEXT"]}
    assert W.fixture_reading({"name": "WC", "box": (0, 0, 1, 1)}, bt)["verdict"] == W.TAG   # the map wins
    assert W.fixture_reading({"name": "WC2", "box": None}, bt)["verdict"] == W.FIXTURE
    assert W.fixture_reading({"name": "WC-E", "box": None}, bt)["verdict"] == W.NOT_EVIDENCE
    assert W.fixture_reading({"name": "WC9", "box": None}, bt)["verdict"] == W.UNCONFIRMED
    assert W.fixture_reading({"name": "WC9", "box": (0, 0, 1, 1)}, None)["verdict"] == W.FIXTURE
    assert W.fixture_reading({"name": "BED", "box": None}, bt)["verdict"] == W.TAG
    assert W.fixture_reading({"name": "CHAIR", "box": (0, 0, 1, 1)}, bt)["verdict"] == W.NOT_EVIDENCE


def test_block_types_flattens_nesting(tmp_path):
    _ents, bt, _pl, _pr = _read(tmp_path)
    assert bt["TAG-WC"] == ["TEXT"] and bt["WC-EMPTY"] == []
    assert sorted(bt["WC-WRAP"]) == sorted(bt["WC-PAN"]) == ["CIRCLE", "LWPOLYLINE"]


# ------------------------------------------------------------------------------------------------ NORMAL
@pytest.mark.parametrize("mirror", MIRRORS)
def test_normal_drawn_wc_in_a_labelled_bathroom_same_in_v1_and_v2(tmp_path, mirror):
    """a drawn WC (WC-PAN) in each of the two mirrored bathrooms: 1 WC each, WET by the label, no check."""
    ents, bt, pl, pr = _read(tmp_path, left=[("WC-PAN", WC_AT)], right=[("WC-PAN", WC_AT)],
                             label_left="BATHROOM", label_right="BATHROOM", mirror_drawing=mirror)
    for poly in (pl, pr):
        v1, v2 = _both(ents, bt, poly)
        assert [x["kind"] for x in v2["fixtures"]] == [W.WC] == [x["kind"] for x in v1["fixtures"]]
        c1, c2 = W.classify(v1), W.classify_v2(v2)
        assert (c2["class"], c2["reason"], c2["basis"]) == (c1["class"], c1["reason"], c1["basis"])
        assert c2["class"] == W.WET and c2["reason"] == "LABEL_WET" and not c2["coordination_checks"]
        assert c2["method"] == W.METHOD_ID_V2


@pytest.mark.parametrize("mirror", MIRRORS)
def test_normal_nested_wrapper_is_one_wc(tmp_path, mirror):
    """WC-WRAP holds WC-PAN: one physical WC, counted once (with the block table and without it)."""
    ents, bt, pl, _pr = _read(tmp_path, left=[("WC-WRAP", WC_AT)], label_left="BATHROOM", mirror_drawing=mirror)
    v1 = W.plan_evidence(pl, ents, N.ROLES, ents["unit_m"])
    assert len(v1["fixtures"]) == 2                              # V1: wrapper + symbol, both by name
    for table in (bt, None):
        v2 = W.plan_evidence_v2(pl, ents, N.ROLES, ents["unit_m"], block_types=table)
        assert [x["kind"] for x in v2["fixtures"]] == [W.WC]


# ------------------------------------------------------------------------------------------------ ADVERSE
@pytest.mark.parametrize("mirror", MIRRORS)
def test_adverse_tag_named_wc_is_not_a_wc(tmp_path, mirror):
    """a bathroom with only its tag block TAG-WC (text '03') and no WC symbol, mirrored pair: V1 reads 1 WC (the
    T-743 defect); V2 reads 0, keeps WET by the label (Q-13: class kept) and raises the coordination check V1 hid."""
    ents, bt, pl, pr = _read(tmp_path, left=[("TAG-WC", TAG_AT)], right=[("TAG-WC", TAG_AT)],
                             label_left="BATHROOM", label_right="BATHROOM", mirror_drawing=mirror)
    for poly in (pl, pr):
        v1, v2 = _both(ents, bt, poly)
        assert [x["kind"] for x in v1["fixtures"]] == [W.WC]
        assert v2["fixtures"] == [] and v2["fixtures_unconfirmed"] == []
        assert [r["verdict"] for r in v2["fixture_readings"]] == [W.TAG]
        c1, c2 = W.classify(v1), W.classify_v2(v2)
        assert c1["class"] == c2["class"] == W.WET and c2["reason"] == "LABEL_WET"
        assert not c1["coordination_checks"]
        assert any("shows no a WC, shower, bath, basin or drain" in x or "plan shows no" in x
                   for x in c2["coordination_checks"])


@pytest.mark.parametrize("mirror", MIRRORS)
def test_adverse_unlabelled_space_with_a_wash_tag_is_not_wet(tmp_path, mirror):
    """an unlabelled space holding only TAG-WASH (text '04'): no basin is drawn, so Q-06 (a) does not apply. V1 makes
    it WET (BASIN_ONLY_HAND_WASH: a phantom wet scope); V2 holds it, never wet and never dry."""
    ents, bt, pl, _pr = _read(tmp_path, left=[("TAG-WASH", TAG_AT)], mirror_drawing=mirror)
    v1, v2 = _both(ents, bt, pl)
    c1 = W.classify(v1)
    assert c1["class"] == W.WET and c1["reason"] == "BASIN_ONLY_HAND_WASH"          # the V1 defect, pinned
    c2 = W.classify_v2(v2)
    assert c2["class"] == W.HELD and c2["reason"] == "NO_LABEL_NO_EVIDENCE"
    assert W.assess(v2)["quantities"] is None


@pytest.mark.parametrize("mirror", MIRRORS)
def test_adverse_unlabelled_space_with_a_wc_tag_is_not_typed_by_fixture(tmp_path, mirror):
    """an unlabelled space with only TAG-WC: V1 types it WET by a 'fixture' (FIXTURES_TOILET); V2 never does."""
    ents, bt, pl, _pr = _read(tmp_path, left=[("TAG-WC", TAG_AT)], mirror_drawing=mirror)
    v1, v2 = _both(ents, bt, pl)
    assert W.classify(v1)["reason"] == "FIXTURES_TOILET"
    c2 = W.classify_v2(v2)
    assert c2["reason"] != "FIXTURES_TOILET" and v2["fixtures"] == []


@pytest.mark.parametrize("mirror", MIRRORS)
def test_adverse_wc_symbol_in_a_room_labelled_store(tmp_path, mirror):
    """a drawn WC in a room labelled STORE: DRY by the label (Q-13), the WC a coordination check, in V1 and V2."""
    ents, bt, pl, _pr = _read(tmp_path, left=[("WC-PAN", WC_AT)], label_left="STORE", mirror_drawing=mirror)
    v1, v2 = _both(ents, bt, pl)
    for c in (W.classify(v1), W.classify_v2(v2)):
        assert c["class"] == W.DRY and c["reason"] == "LABEL_DRY"
        assert any("WC" in x for x in c["coordination_checks"])


def test_adverse_empty_block_named_wc_is_nothing(tmp_path):
    ents, bt, pl, _pr = _read(tmp_path, left=[("WC-EMPTY", WC_AT)])
    v1, v2 = _both(ents, bt, pl)
    assert W.classify(v1)["class"] == W.WET                                         # V1: by name
    assert v2["fixtures"] == [] and W.classify_v2(v2)["reason"] == "NO_LABEL_NO_EVIDENCE"


def test_adverse_content_not_read_is_held_not_typed():
    """no block table and no geometry extents (a producer that gives no box): the WC name is a candidate only."""
    poly = [(0, 0), (10, 0), (10, 10), (0, 10)]
    ents = {"unit_m": 0.001, "texts": [], "segments": [], "arcs": [], "circles": [],
            "inserts": [{"id": "I:A1:0", "name": "WC", "layer": "X", "x": 5, "y": 5, "box": None, "path": []}]}
    v2 = W.plan_evidence_v2(poly, ents, {}, 0.001)
    assert v2["fixtures"] == [] and [x["kind"] for x in v2["fixtures_unconfirmed"]] == [W.WC]
    c = W.classify_v2(v2)
    assert c["class"] == W.HELD and c["reason"] == "WET_DRY_NOT_ESTABLISHED" and "'WC'" not in c["basis"]
    assert "WC" in c["basis"]
    assert W.classify(W.plan_evidence(poly, ents, {}, 0.001))["reason"] == "FIXTURES_TOILET"   # V1 by name


def test_v1_functions_unchanged_by_the_v2_additions():
    """the module's V1 surface the chain reads is still there and still names its method WET_ROOM_EVIDENCE_V1."""
    assert W.METHOD_ID == "WET_ROOM_EVIDENCE_V1" and W.policy_record()["id"] == "WET_ROOM_EVIDENCE_V1"
    assert W._fixture_kind("WC") == W.WC and W._fixture_kind("WASH") == W.BASIN


def test_alsenan_committed_census_shape():
    """the committed Alsenan census (research/agents_t744/out): 9 text-only fixture-named tags (7 WC + 2 WASH), 5 drawn
    basins, no space's class / reason / basis changed, no candidate line named."""
    import json
    d = json.loads((ROOT / "research/agents_t744/out/T744_ALSENAN_CENSUS.json").read_text(encoding="utf-8"))
    tags = [x for x in d["fixture_named_inserts"] if x["verdict"] == "TAG"]
    assert sorted({x["block"] for x in tags}) == ["WASH", "WC"] and len(tags) == 9
    assert sum(1 for x in tags if x["block"] == "WC") == 7
    assert all(x["content_types"] == {"TEXT": 2} for x in tags)
    assert d["inventory_verdicts"] == {"TAG": 9, "FIXTURE": 5}
    assert d["v1_reproduces_chain_classes"] is True
    assert d["spaces_whose_class_reason_basis_changed"] == []
    assert d["line_index"]["lines_naming_a_changed_space"] == []
