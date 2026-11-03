"""T-455 ledger on the pinned candidate V3.0.45 line index: no tile size is printed for the training villa, so every
adhesive figure is HELD with the owner-rule bound beside it; V3's size-blind figure is kept as the 'before'."""

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "research" / "agents_t455"))

import t455_tile_purchase as L  # noqa: E402


def test_ledger_on_the_candidate_holds_every_bag_with_its_bound():
    led = L.build()
    c = led["by_item_code"]
    assert c["FIN.FLOOR.PORCELAIN"]["area_m2"] == pytest.approx(305.020973)
    assert c["FIN.WALL.TILE"]["released"] == 12 and c["FIN.WALL.TILE"]["held"] == 6
    assert c["FIN.WALL.TILE"]["v3_flat_bags"] == pytest.approx(340.3038 / 5)
    assert c["FIN.WALL.TILE"]["bound_high"] == pytest.approx(340.3038 / 3)
    g = led["purchase"]["adhesive"]["PROJECT"]
    assert g["status"] == "HELD" and g["bags_to_buy"] is None and g["bags_known"] == 0.0
    assert g["bound_bags_to_buy"] is None            # 7 held lines have no area: no bound is claimed
    assert len(led["excluded_lines"]) == 13
    assert all(r["tile_product"] is None for r in led["rows"])


def test_ledger_refuses_an_unpinned_or_wrong_unit_input(tmp_path):
    d = json.loads(L.LINE_INDEX.read_text(encoding="utf-8"))
    for ln in d["lines"]:
        if ln["item_code"] == "FIN.FLOOR.WET_TILE":
            ln["unit"] = "m3"
            break
    p = tmp_path / "idx.json"
    p.write_text(json.dumps(d), encoding="utf-8")
    with pytest.raises(L.LedgerError, match="not m2"):
        L.build(p)


def test_committed_ledger_matches_a_rebuild(tmp_path):
    L.write(tmp_path)
    for name in ("TILE_PURCHASE_T455.json", "TILE_PURCHASE_T455.csv"):
        assert (tmp_path / name).read_bytes() == (L.HERE / "out" / name).read_bytes()
