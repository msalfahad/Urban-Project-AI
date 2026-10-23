"""T-218: the development villa's ledger reproduces from committed files; the ground-floor kitchen is WET in every
line but its floor item; the 1F bed-room residual closes to named parts; the doorway strips are one line each or
named as duplicates."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "research" / "agents_t218"
sys.path.insert(0, str(HERE))

import alsenan_t218 as A                                               # noqa: E402


def test_committed_files_reproduce():
    assert A.main(["--check"]) == 0


def _s():
    return json.loads((HERE / "summary.json").read_text(encoding="utf-8"))


def test_kitchen_is_wet_but_floored_dry_in_both_states():
    k = _s()["kitchen"]
    for key in ("findings_released", "findings_candidate_base"):
        assert [f["finding"] for f in k[key]] == ["WET_ROOM_FLOORED_DRY"]
    assert k["lexicon_kind"] == "SERVICE" and k["owner_scope"] == "WET"
    # hand from the printed sizes = the engine face and boundary; upturn walls only
    assert k["floor_hand_m2"] == 9.63 and k["floor_engine_m2"] == 9.63
    assert k["boundary_hand_lm"] == 14.5 and k["boundary_engine_lm"] == 14.5
    assert k["upturn_lm_hand"] == 13.5 and k["upturn_m2_hand"] == 2.7 == k["upturn_m2_engine"]
    w = k["wet_floor_key"]
    assert w["before_m2"] == 62.4907 and w["after_m2"] == 72.1207 and w["diff_after_m2"] == 0.1107
    assert w["floor_key_total_change_m2"] == 0.0 and w["dry_porcelain_change_m2"] == -9.63


def test_bedroom_residual_closes_to_named_parts():
    b = _s()["bedrooms"]
    assert b["old_pairing"]["diff_m2"] == -1.3785
    d = b["decomposition"]
    assert d["closed"] and abs(d["residual_m2"]) < 0.0005
    kinds = {p["id"]: (p["m2"], p["kind"]) for p in d["parts"]}
    assert kinds["curved room vs his 17.29"] == (1.7265, "UNRESOLVED")
    assert kinds["dressing 1F-RFFE7AF HELD outside the key (type), in his bed-room-2 row"] == (-2.97, "STATUS")


def test_strips_one_line_each_or_named():
    s = _s()["strips"]
    assert s["by_floor"]["1F"]["to_held_m2"] == 0.35 and s["by_floor"]["1F"]["stay_porcelain_m2"] == 0.42
    assert s["by_floor"]["2F"]["to_held_m2"] == 0.35 and s["by_floor"]["2F"]["stay_porcelain_m2"] == 0.18
    assert sorted(d["opening_id"] for d in s["duplicates"]) == ["1F:OP-004", "1F:OP-005"]


def test_floor_key_like_for_like_closes():
    f = _s()["floor_key"]
    assert f["t208"]["like_for_like_m2"] == 0.0443
    assert f["after"]["engine_total_m2"] == 384.9339 and f["after"]["like_for_like_m2"] == 2.4643
    assert f["decomposition"]["closed"]


def test_input_carries_no_coordinates():
    raw = (HERE / "ALSENAN_T218_INPUT.json").read_text(encoding="utf-8")
    assert "polygon" not in raw and "point" not in raw and "centre_m" not in raw
