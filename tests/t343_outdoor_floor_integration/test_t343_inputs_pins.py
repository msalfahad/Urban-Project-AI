"""T-343: the V3.0.25 project inputs come ONLY from the merged T-342 / T-157 / T-183 ledgers, pinned by sha256 (areas,
statuses, Drive titles and DXF handles only, no private data). Normal: 7 pieces + the pool finish, plan pieces
166.878936 m2 (deck 7.105836 = 17.3414 - the exact outer D 10.235564), risers 1.96, held finish 17.784336, pool
bound 21.308727 m2, the inputs load and re-add to the face within 0.0008 m2; adverse: an edited ledger stops the
build."""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "research" / "agents_t343"))

import t343_inputs as L  # noqa: E402
from engine.source import arch_v3025 as A  # noqa: E402


def test_inputs_from_the_merged_ledgers():
    d = L.build("p")
    assert [(p["piece"], p["item_code"], p["area_m2"], p["material_status"]) for p in d["pieces"]] == [
        ("WEST-OPEN", "EXT.PAVING.INTERLOCK", 119.5416, A.OA), ("PORCH", "EXT.FLOOR.OUTDOOR", 10.6785, "HELD"),
        ("E1-TREADS", "FIN.MARBLE.TREAD", 3.3594, A.OA), ("E1-RISERS", "FIN.MARBLE.RISER", 1.96, A.OA),
        ("E1-LANDING", "FIN.MARBLE.LANDING", 5.1794, A.OA), ("NORTH-WALK", "EXT.FLOOR.PORCELAIN", 21.0142, A.OA),
        ("POOL-DECK", "EXT.FLOOR.OUTDOOR", 7.105836, "HELD")]
    assert d["declared"] == {"lines": 8, "plan_m2": 166.878936, "vertical_m2": 1.96, "held_material_m2": 17.784336,
                             "pool_bound_m2": 21.308727}
    assert [s["merge_commit"][:8] for s in d["sources"]] == ["4dd9cff8", "554c1c46", "63802945"]
    assert A.load_inputs(d, "p") is d
    clo = A.closure(d)
    assert clo["holes"][0]["exact_m2"] == 10.235564 and clo["holes"][0]["tessellation_residual_m2"] == -0.003564
    assert abs(clo["difference_m2"]) < 0.001 and clo["vs_reference_m2"] == round(166.878936 - 166.883, 6)
    pf = d["pool_finish"]
    assert (pf["rim_height_m"], pf["structural_height_m"], pf["rim_basis"]) == (1.15, 1.20, "FINISHED_FLOOR_TO_RIM")
    assert "2E5E" in pf["rim_height_source"]


@pytest.mark.parametrize("which", ["T342", "T157", "T183"])
def test_adverse_an_edited_ledger_stops_the_build(tmp_path, monkeypatch, which):
    src = getattr(L, which)
    p = tmp_path / src.name
    shutil.copy(src, p)
    p.write_text(p.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    pins = {(p if k == src else k): v for k, v in L.PINS.items()}
    monkeypatch.setattr(L, which, p)
    monkeypatch.setattr(L, "PINS", pins)
    with pytest.raises(SystemExit, match="edited ledger"):
        L.build("p")
