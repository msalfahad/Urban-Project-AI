"""Private project inputs: SKIPPED, not FAILED, in a public checkout (owner directive 2026-11-02, D1, task T-462).

A test file that reads private project data declares the private roots it reads in a module-level
``PRIVATE_INPUTS = (...)``. When one of its tests fails in setup or call with a ``FileNotFoundError`` for a file under a
declared root that is still absent, the report becomes SKIPPED ``private data not available: <file>``. Everything else
is untouched: other exceptions, missing files outside the declared roots, and private files that are present but fail.
``URBAN_PRIVATE_INPUTS=require`` (the machine with the private data) keeps those failures as failures. Rules and helper:
tests/_private_inputs.py.
"""

from __future__ import annotations

import pytest

from tests import _private_inputs as PI

_SKIPS = pytest.StashKey[list]()


def pytest_collection_modifyitems(session, config, items):
    """A wrong declaration fails the run at collection: a public path can never be declared skippable."""
    seen = set()
    for item in items:
        mod = getattr(item, "module", None)
        if mod is None or id(mod) in seen:
            continue
        seen.add(id(mod))
        try:
            PI.declared_roots(mod)
        except ValueError as e:
            raise pytest.UsageError(f"{mod.__name__}: PRIVATE_INPUTS: {e}") from None


@pytest.hookimpl(wrapper=True)
def pytest_runtest_makereport(item, call):
    rep = yield
    if rep.when not in ("setup", "call") or not rep.failed or call.excinfo is None or hasattr(rep, "wasxfail"):
        return rep
    roots = PI.declared_roots(getattr(item, "module", None))
    name = PI.absent_private_file(call.excinfo.value, roots)
    if name is None:
        return rep
    if PI.strict():
        rep.sections.append(("private inputs", PI.REQUIRE_PREFIX + name))
        return rep
    path, line = item.reportinfo()[:2]
    rep.outcome = "skipped"
    rep.longrepr = (str(path), (line or 0) + 1, "Skipped: " + PI.SKIP_PREFIX + name)
    item.config.stash.setdefault(_SKIPS, []).append(name)
    return rep


def pytest_terminal_summary(terminalreporter, exitstatus, config):
    skips = config.stash.get(_SKIPS, [])
    if skips:
        terminalreporter.write_line(
            f"PRIVATE INPUTS: {len(skips)} test phase(s) skipped, {len(set(skips))} private file(s) not available "
            f"(set {PI.STRICT_ENV}=require where the private data is present)")
