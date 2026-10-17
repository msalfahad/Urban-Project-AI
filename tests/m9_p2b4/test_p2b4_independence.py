"""Phase 2B-4 constructability audit: the calculation is independent of the engine. The construction calculator is
stdlib only and imports nothing from the project (neither the engine nor the Phase 2B-3 reference calculator); the
case file imports nothing at all and holds its expected values as typed literals; only construct_engine.py reaches the
engine, and it holds no expected value."""

from __future__ import annotations

import ast
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import construct_cases as CC                                  # noqa: E402


def _imports(path):
    out = set()
    for n in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(n, ast.Import):
            out |= {a.name for a in n.names}
        elif isinstance(n, ast.ImportFrom):
            out.add(n.module or "")
    return out


def test_the_calculator_is_stdlib_only_and_the_cases_import_nothing():
    assert _imports(HERE / "construct_reference.py") <= {"__future__", "itertools", "collections"}
    assert _imports(HERE / "construct_cases.py") == set()


def _literal(node):
    if isinstance(node, ast.Constant):
        return True
    if isinstance(node, (ast.List, ast.Tuple)):
        return all(_literal(e) for e in node.elts)
    if isinstance(node, ast.Dict):
        return all(isinstance(k, ast.Constant) for k in node.keys) and all(_literal(v) for v in node.values)
    return False


def test_every_expected_value_is_a_typed_literal():
    tree = ast.parse((HERE / "construct_cases.py").read_text(encoding="utf-8"))
    n = 0
    for d in [x for x in ast.walk(tree) if isinstance(x, ast.Dict)]:
        for k, v in zip(d.keys, d.values):
            if isinstance(k, ast.Constant) and k.value == "expected":
                assert _literal(v), ast.unparse(v)[:120]
                n += 1
    assert n == len(CC.PLANS)
    for a in [x for x in ast.walk(tree) if isinstance(x, ast.Assign)]:
        if any(isinstance(t, ast.Name) and t.id == "SWEEP_HAND" for t in a.targets):
            assert _literal(a.value)


def test_every_plan_carries_its_derivation_junction_and_reading():
    for p in CC.PLANS:
        for k in ("id", "room", "junction", "reading", "title", "plan", "hand", "expected"):
            assert p.get(k), (p.get("id"), k)
        assert p["room"] in CC.ROOMS


def test_the_audited_rooms_are_the_phase_2b3_rooms():
    """the audit reads the same geometry the V2.5 engine was run on (the Phase 2B-3 cases, in millimetres)."""
    import construct_engine as CE
    for rid, room in CC.ROOMS.items():
        sc = CE.scenario(rid)
        assert [tuple(int(round(c * 1000)) for c in p) for p in sc["ring"]] == [tuple(p) for p in room["poly"]]
        assert sorted((d["id"], d["edge"], int(round(d["t0"] * 1000)), int(round(d["t1"] * 1000)),
                       int(round(d["depth_m"] * 1000))) for d in sc["doors"]) == \
            sorted((d["id"], d["edge"], d["t0"], d["t1"], d["depth"]) for d in room["doors"])
