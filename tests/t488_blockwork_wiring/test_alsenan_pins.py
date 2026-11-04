"""T-488: the development-villa run record (research/agents_t488/summary_t488.json, own chain T-167 -> v3055_run on the
Drive drawings: V3_0_53 36863f6c and V3_0_54 c85c4630 reproduced -> V3_0_55) is internally consistent and agrees with
the pinned inputs (the merged T-482 conditions and T-449 r3 register): 32 lines replaced, 0 added, every other V3.0.54
line byte-identical, totals moved only in the three blockwork items, every roof-storey wall's terms by hand."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "research" / "agents_t488"))

import t488_inputs as T  # noqa: E402

S = json.loads((ROOT / "research/agents_t488/summary_t488.json").read_text(encoding="utf-8"))


def test_chain_and_identity():
    assert S["chain"]["V3_0_53"] == "36863f6c" and S["chain"]["V3_0_54"] == "c85c4630"
    assert S["extends"] == "ARCH_TAKEOFF_V3.0.54"
    i = S["identity"]
    assert (i["replaced"], i["added"]) == (32, 0) and i["base_lines"] == i["v3_0_55_lines"]
    assert i["outside_rows"] == i["outside_rows_identical_to_base"] == i["base_lines"] - 32
    assert sorted(k.split("|")[0] for k in S["totals_moved_by_code"]) == ["ARCH.WALL_PANEL", "ARCH.WALL_VOLUME",
                                                                          "MAS.BLOCK"]
    m = S["totals_moved_by_code"]["MAS.BLOCK|m2"]
    assert m["base"]["released"] == pytest.approx(579.1011) and m["v3_0_55"]["released"] == pytest.approx(467.7925)
    assert m["v3_0_55"]["blocked_lines"] - m["base"]["blocked_lines"] == 6
    w = i["wiring"]
    assert (w["part_held"], w["part_reduced"], w["parents"], w["parapets"]) == (18, 3, 9, 2)
    assert w["roof_walls"] == [f"2F-W0{k}" for k in range(1, 9)] and w["conflicts"] == ["GF-W22"]


def test_released_drop_is_the_held_walls_by_hand():
    m = S["totals_moved_by_code"]["MAS.BLOCK|m2"]
    roof = {w["wall_id"]: w for w in T.build("p")["roof_datum"]["walls"]}
    held = sum(w["carried_m2"] for w in roof.values()) + 12.9311                   # + GF-W22 (CONFLICT, off its part)
    assert round(m["base"]["released"] - m["v3_0_55"]["released"], 6) == pytest.approx(round(held, 6))
    assert round(sum(w["upper_m2"] for w in roof.values()), 6) == pytest.approx(99.8525)       # 53.5225 + 46.330
    assert round(sum(w["length_m"] for w in roof.values()), 6) == pytest.approx(29.495)        # 14.925 + 14.570
    for w in roof.values():
        assert w["carried_m2"] == pytest.approx(w["upper_m2"] - w["length_m"] * 0.05, abs=5e-4)


def test_every_held_part_line_names_its_walls_terms():
    roof = {w["wall_id"]: w for w in T.build("p")["roof_datum"]["walls"]}
    held = [r for r in S["rows"] if r["action"] == "PART_HELD"]
    assert len(held) == 18 and all(r["after"]["value"] is None for r in held)
    for r in held:
        f = 0.2 if "t=0.20" in r["element_id"] else 0.15
        f = f if r["item_code"] == "ARCH.WALL_VOLUME" else 1.0
        for wid, term in zip(r["removed"], r["terms"]):
            u, L = roof[wid]["upper_m2"] * f, roof[wid]["length_m"] * f
            assert term.startswith(f"{wid} HELD ON ROOF DATUM") and "(D-39)" in term
            assert f"{round(u, 6):g}"[:5] in term and f"{round(L, 6):g}" in term


def test_conflict_and_drop_and_parapets():
    red = [r for r in S["rows"] if r["action"] == "PART_REDUCED"]
    assert {(r["item_code"], r["removed"][0]) for r in red} == {(c, "GF-W22") for c in
                                                                ("MAS.BLOCK", "ARCH.WALL_PANEL", "ARCH.WALL_VOLUME")}
    mb = next(r for r in red if r["item_code"] == "MAS.BLOCK")
    assert (mb["before"]["value"], mb["after"]["value"]) == (21.5261, 8.595) and mb["kept"] == ["GF-W19"]
    par = [r for r in S["rows"] if r["action"] == "PARENT_RESTATED" and r["item_code"] == "MAS.BLOCK"
           and r["floor"] == "GF"]
    assert len(par) == 1 and par[0]["drop_upper"][0]["after"] == "10.4121 - 1.7231 d"
    assert sorted(par[0]["retired_increments"]) == ["GF-W22", "GF-W34"]
    pp = {r["parapet"]["run"]: r["parapet"] for r in S["rows"] if r["action"] == "PARAPET_BLOCK_ALT"}
    assert pp["NW-2"]["before_m2"] == [0.0, 3.6107] and pp["NW-2"]["after_m2"] == [0.0, 3.1672]
    assert pp["NE-6x"]["before_m2"] is None and pp["NE-6x"]["after_m2"] == [0.0, 0.25999]
