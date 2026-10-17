"""Phase 2B-3 proof library: the expected answers are independent of the engine. The reference calculator imports
nothing from engine/ or tools/; the case files import nothing at all from the project and hold their expected values
as literals typed from the hand calculations (never computed, never read back from the engine); every approved rule
the library proves has a positive example, and a boundary and a conflict / exception example where the rule admits
one (the rest are listed with the reason)."""

from __future__ import annotations

import ast
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import proof_cases as C                                       # noqa: E402
import proof_cases_doors as D                                 # noqa: E402
import proof_cases_rules as RC                                # noqa: E402

INDEPENDENT = ("proof_reference.py", "proof_check.py", "proof_cases.py", "proof_cases_doors.py",
               "proof_cases_rules.py")
STDLIB_ONLY = ("proof_reference.py",)
CASE_FILES = ("proof_cases.py", "proof_cases_doors.py", "proof_cases_rules.py")
# a rule with no boundary or no conflict / exception example, and why none applies
NOT_APPLICABLE = {
    ("UP-WP-001", "BOUNDARY"): "the roll size is a constant; its boundary is the strip / splice count (UP-WP-002)",
    ("UP-WP-001", "CONFLICT"): "a roll conflict blocks the layout exactly as the upturn conflict of RS-03",
    ("UP-WP-MAT-001", "BOUNDARY"): "the three quantities are definitions, not a threshold",
    ("UP-WP-004", "BOUNDARY"): "a count is not shown (WP-A: never 0) or counted (WP-C: 1): the two sides are the "
                               "positive cases",
    ("UP-WP-DOOR-001", "BOUNDARY"): "a doorway exists (WP-B) or not (WP-A): no threshold between them",
    ("UP-WP-ROOF-001", "BOUNDARY"): "the exterior scope is a classification (WP-F / WP-G), not a threshold",
    ("UP-WP-ROOF-001", "CONFLICT"): "an exterior system conflict follows UP-RULES-001 exactly as RS-03",
    ("UP-DOOR-OPEN-002", "BOUNDARY"): "DR-01 is the boundary itself: the opening exactly at the standard",
    ("UP-DOOR-HGT-001", "BOUNDARY"): "heights are values by category, no threshold",
    ("UP-DOOR-HGT-001", "CONFLICT"): "a height conflict is held by the door model (Phase 2B-0 guards), not by this rule",
}


def _imports(path):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    out = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            out |= {a.name for a in n.names}
        elif isinstance(n, ast.ImportFrom):
            out.add(n.module or "")
    return out


def test_the_reference_and_the_cases_never_import_the_engine():
    for name in INDEPENDENT:
        mods = _imports(HERE / name)
        assert not any(m.startswith(("engine", "tools", "proof_engine", "p2b2_fixtures")) for m in mods), (name, mods)
    for name in STDLIB_ONLY:
        mods = _imports(HERE / name)
        assert mods <= {"__future__", "itertools", "math"}, (name, mods)


def _literal(node):
    if isinstance(node, ast.Constant):
        return True
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub) and isinstance(node.operand, ast.Constant):
        return True
    if isinstance(node, (ast.List, ast.Tuple)):
        return all(_literal(e) for e in node.elts)
    if isinstance(node, ast.Dict):
        return all(_literal(v) for v in node.values) and all(isinstance(k, ast.Constant) for k in node.keys)
    return False


def test_every_expected_value_is_a_typed_literal():
    """the 'expected' block of every case is a literal dictionary: no call, no name, no arithmetic."""
    n = 0
    for name in CASE_FILES:
        tree = ast.parse((HERE / name).read_text(encoding="utf-8"))
        for d in [x for x in ast.walk(tree) if isinstance(x, ast.Dict)]:
            for k, v in zip(d.keys, d.values):
                if isinstance(k, ast.Constant) and k.value == "expected":
                    assert _literal(v), (name, ast.unparse(v)[:120])
                    n += 1
    assert n == len(C.WP_CASES) + len(D.DOOR_CASES) + len(RC.RULES_CASES)


def test_every_case_carries_the_ten_parts_of_a_proof():
    """(1) scenario, (2) rules, (3) overrides, (4) hand calculation, (5) expected, (9) coordinates, (10) exclusions;
    (6) - (8) come from proof_engine.compare at run time."""
    for c in C.WP_CASES:
        if c["id"] == "WP-H":
            assert c["members"] and c["hand"] and c["expected"] and c["exclusions"]
            continue
        for k in ("scenario", "proves", "overrides", "hand", "expected", "coordinates", "exclusions", "assumptions"):
            assert k in c, (c["id"], k)
        assert len(c["hand"]) >= 3
    for c in D.DOOR_CASES:
        for k in ("plan", "proves", "hand", "expected", "exclusions"):
            assert k in c, (c["id"], k)
    for c in RC.RULES_CASES:
        for k in ("rules", "proves", "hand", "expected"):
            assert k in c, (c["id"], k)


def test_every_proven_rule_has_positive_boundary_and_conflict_examples():
    kinds = {}
    for c in C.WP_CASES + D.DOOR_CASES + RC.RULES_CASES:
        for r in c.get("proves") or ():
            kinds.setdefault(r, set()).add("CONFLICT" if c["kind"] in ("CONFLICT", "EXCEPTION") else c["kind"])
    approved = ("UP-WP-001", "UP-WP-002", "UP-WP-003", "UP-WP-004", "UP-WP-DOOR-001", "UP-WP-MAT-001",
                "UP-WP-LAY-001", "UP-WP-ROOF-001", "UP-DOOR-OPEN-002", "UP-DOOR-FEAS-001", "UP-DOOR-HGT-001",
                "UP-RULES-001")
    for r in approved:
        assert "POSITIVE" in kinds.get(r, ()), r
        for k in ("BOUNDARY", "CONFLICT"):
            assert k in kinds.get(r, ()) or (r, k) in NOT_APPLICABLE, (r, k, kinds.get(r))
