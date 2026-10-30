"""T-379: tools/label_census_v2.py (T-344) carries its default-guard class, and the class is held to what the tool does.

Normal case: the module declares DEFAULT_GUARD_CLASS = "CHECK_ONLY" (T-212 P1), the live property reads it from the
module (not from a table row), and nothing the census imports, directly or transitively, is an UNWIRED_PRODUCER (a check
module that reached a producer would carry an unguarded quantity path). Adverse cases on the module's own source in a
synthetic tree (no repo file written): the declaration removed is a P1 problem; the census edited to import an unwired
producer is a P2 problem, so the CHECK_ONLY label cannot hide such an edge later."""
from __future__ import annotations

import sys
from collections import deque
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t212"))
sys.path.insert(0, str(ROOT / "research" / "agents_t202"))

import guard_property as GP     # noqa: E402
import guard_sweep as GS        # noqa: E402

CENSUS = "tools/label_census_v2.py"
PRODUCER = "engine/source/masonry_area_v1.py"


@pytest.fixture(scope="module")
def sources():
    return GP.live_sources()


def test_census_declares_check_only_in_its_own_source(sources):
    assert GP.declared(sources[CENSUS]) == GS.CHECK_ONLY
    assert GP.classify(CENSUS, sources[CENSUS], GP.table()) == (GS.CHECK_ONLY, "declared in module")
    assert CENSUS not in GP.table()                         # one place only: never both a table row and a declaration


def test_census_reaches_no_unwired_producer(sources):
    tab = GP.table()
    fwd = GP.edges(sources)
    seen, q = set(), deque([CENSUS])
    while q:
        for t in sorted(fwd.get(q.popleft(), ())):
            if t not in seen:
                seen.add(t)
                q.append(t)
    assert "tools/urban_boq_m9.py" in seen                  # its CLI reads a guarded run
    producers = {p for p in seen if GP.classify(p, sources[p], tab)[0] == GS.UNWIRED_PRODUCER}
    assert producers == set()


def test_adverse_declaration_removed_is_a_p1_problem(sources):
    src = "\n".join(l for l in sources[CENSUS].splitlines() if not l.startswith(GP.DECL))
    assert GP.declared(src) is None
    _, problems = GP.check({CENSUS: src}, [("A", CENSUS)], {})
    assert len(problems) == 1 and problems[0].startswith(CENSUS) and "no default-guard classification" in problems[0]


def test_adverse_census_importing_a_producer_is_a_p2_problem(sources):
    src = sources[CENSUS] + "\nfrom engine.source import masonry_area_v1  # noqa\n"
    tree = {CENSUS: src, PRODUCER: 'DEFAULT_GUARD_CLASS = "UNWIRED_PRODUCER"\n'}
    _, problems = GP.check(tree, [("A", CENSUS), ("A", PRODUCER)], {})
    assert any(p.startswith(f"{CENSUS} (class CHECK_ONLY) reaches the unwired producer {PRODUCER}") for p in problems)
