"""T-458 (owner directive 2026-11-02 C3): the wet-room upturn is 0.20 m with NO door deduction (UP-WP-002 2.0.0,
owner Q-03 / Q-35 C); the legacy 0.15 m / door-deduction sites are superseded and unreachable from the candidate.

Hand-calculated fixture (not the training villa): a 3.00 x 2.00 m bathroom, one 0.80 m door in a 0.20 m wall.
  floor 3.00 x 2.00 = 6.000 m2; boundary incl. the door crossing 2 x (3.00 + 2.00) = 10.000 m;
  upturn 10.000 x 0.20 = 2.000 m2 (NOT (10.000 - 0.80) x 0.15 = 1.380 m2, the legacy V1 answer);
  doorway transition 0.80 x 0.20 = 0.160 m2, its own line.
"""

from __future__ import annotations

import ast
import math
import re
from pathlib import Path

import pytest

from engine.source import rule_store as RS
from engine.source import waterproofing_policy_v2 as WP2

ROOT = Path(__file__).resolve().parents[2]
LEGACY = {"engine.source.waterproofing_policy", "engine.source.room_slice", "engine.finishes_rules",
          "engine.source.arch_quantity_truth"}


def _perimeter(poly):
    return sum(math.dist(poly[i], poly[(i + 1) % len(poly)]) for i in range(len(poly)))


def _item(r, name):
    return [i for i in r["items"] if i["item"] == name]


def test_normal_room_with_a_door():
    r = WP2.wet(floor_m2=6.0, boundary_lm=10.0, doors=[{"id": "D1", "width_m": 0.80, "wall_t_m": 0.20}], room="B1")
    up = _item(r, "FIN.WP.UPTURN")[0]
    assert up["upturn_m"] == pytest.approx(0.20)
    assert up["m2"] == pytest.approx(2.000)
    assert up["door_crossings_deducted"] is False
    assert _item(r, "FIN.WP.FLOOR")[0]["m2"] == pytest.approx(6.000)
    assert _item(r, "FIN.WP.DOORWAY")[0]["m2"] == pytest.approx(0.160)
    assert r["state"] == "MEASURED" and r["held_items"] == []


def test_adverse_legacy_door_deduction_and_015_not_reproduced():
    one = WP2.wet(floor_m2=6.0, boundary_lm=10.0, doors=[{"id": "D1", "width_m": 0.80, "wall_t_m": 0.20}], room="a")
    two = WP2.wet(floor_m2=6.0, boundary_lm=10.0, doors=[{"id": "D1", "width_m": 0.80, "wall_t_m": 0.20},
                                                         {"id": "D2", "width_m": 0.90, "wall_t_m": 0.20}], room="b")
    u1, u2 = _item(one, "FIN.WP.UPTURN")[0]["m2"], _item(two, "FIN.WP.UPTURN")[0]["m2"]
    assert u1 == u2 == pytest.approx(2.000)              # doors never reduce the upturn
    assert u1 != pytest.approx((10.0 - 0.80) * 0.15)     # the legacy V1 answer 1.380
    assert len(_item(two, "FIN.WP.DOORWAY")) == 2


def test_units_mirror_rotation():
    mm = [(0, 0), (3000, 0), (3000, 2000), (0, 2000)]
    u = 0.001                                            # metres per drawing unit
    m = [(x * u, y * u) for x, y in mm]
    mirrored = [(-x, y) for x, y in m]
    c, s = math.cos(0.7), math.sin(0.7)
    rotated = [(x * c - y * s, x * s + y * c) for x, y in m]
    vals = {round(_item(WP2.wet(floor_m2=6.0, boundary_lm=_perimeter(p), room="r"), "FIN.WP.UPTURN")[0]["m2"], 9)
            for p in (m, mirrored, rotated)}
    assert vals == {2.0}
    # a caller that forgets the unit gets 2000 m2, never silently 2 m2: the input is metres by contract
    assert _item(WP2.wet(floor_m2=6.0, boundary_lm=_perimeter(mm), room="r"), "FIN.WP.UPTURN")[0]["m2"] == \
        pytest.approx(2000.0)


def test_missing_inputs_are_held_never_zero():
    r = WP2.wet(floor_m2=None, boundary_lm=None, doors=[{"id": "D1", "width_m": 0.80, "wall_t_m": None}], room="x")
    for name in ("FIN.WP.FLOOR", "FIN.WP.UPTURN", "FIN.WP.DOORWAY"):
        it = _item(r, name)[0]
        assert it["state"] == "HELD" and it["m2"] is None
    assert r["state"] == "HELD"
    partial = WP2.wet(floor_m2=6.0, boundary_lm=10.0, doors=[{"id": "D1", "width_m": None, "wall_t_m": 0.2}],
                      room="y")
    assert _item(partial, "FIN.WP.UPTURN")[0]["m2"] == pytest.approx(2.000)
    assert partial["held_items"] == ["FIN.WP.DOORWAY"]
    assert WP2.procurement(None, system="X", lap_factor=1.1)["procurement_m2"] is None


def test_rule_store_supersession():
    assert RS.rule("UP-WP-002", RS.LATEST_APPROVED)["value"] == pytest.approx(0.20)
    assert RS.rule("UP-WP-002", "1.4.0")["value"] == pytest.approx(0.15)     # the superseded base record, history


def test_policy_id_distinct_and_clash_recorded():
    ids = {}
    for p in sorted((ROOT / "engine").rglob("*.py")):
        for m in re.finditer(r'^POLICY_ID\s*=\s*"([^"]+)"', p.read_text(encoding="utf-8"), re.M):
            ids.setdefault(m.group(1), []).append(p.relative_to(ROOT).as_posix())
    assert ids[WP2.POLICY_ID] == ["engine/source/waterproofing_policy_v2.py"]
    # the V1 clash (opposite doorway rules) is exactly the recorded pair; a third claimant fails here
    assert sorted(ids["WATERPROOFING_POLICY_V1"]) == ["engine/source/waterproofing.py",
                                                      "engine/source/waterproofing_policy.py"]
    clash = [s for s in WP2.SUPERSEDED if s["id_clash_with"]]
    assert [s["id_clash_with"] for s in clash] == ["engine/source/waterproofing.py"]


def _closure(start):
    seen, todo = set(), [start]
    while todo:
        mod = todo.pop()
        if mod in seen:
            continue
        rel = mod.replace(".", "/")
        path = next((q for q in (ROOT / f"{rel}.py", ROOT / rel / "__init__.py") if q.exists()), None)
        if path is None:
            continue
        seen.add(mod)
        pkg = mod if path.name == "__init__.py" else mod.rsplit(".", 1)[0]
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, ast.Import):
                todo += [a.name for a in node.names if a.name.startswith("engine")]
            elif isinstance(node, ast.ImportFrom):
                base = node.module or ""
                if node.level:
                    parts = pkg.split(".")
                    parts = parts[:len(parts) - node.level + 1]
                    base = ".".join(parts + ([node.module] if node.module else []))
                if base.startswith("engine"):
                    todo.append(base)
                    todo += [f"{base}.{a.name}" for a in node.names]
    return seen


def test_candidate_closure_never_imports_a_legacy_upturn_module():
    """adverse guard: the candidate ARCH_TAKEOFF_V3.0.40 module (every import, also inside functions) must not reach a
    module that still applies 0.15 m or the upturn door deduction."""
    c = _closure("engine.source.arch_v3040")
    assert "engine.source.arch_v3040" in c and len(c) > 20
    assert not (c & LEGACY), sorted(c & LEGACY)
