"""R8.0 expected-failure mechanism.

Known failures are DATA, frozen in registers/R8_0_EXPECTED_FAILURES.json,
never ad-hoc decorators. Each entry is applied as a STRICT xfail on the
exception its class allows:

    KNOWN_DEFECT            AssertionError           current engine is wrong
    TARGET_NOT_IMPLEMENTED  TargetNotImplemented     the R8 module is not written yet
    LIBRARY_KNOWN_FAILURE   AssertionError           an oracle library is wrong here
    BOUNDARY_DEBT           AssertionError           pre-existing, frozen, to retire
    CONTRACT_DISPUTED       AssertionError           (R8.3) the implemented design disagrees with a
                                                     frozen R8.0 expectation; the expectation is kept
                                                     UNCHANGED and the dispute awaits review

Strict means an entry that unexpectedly passes FAILS the run, so a fix can
never slip in without the register being updated in the same change.

Set R8_0_RAW=1 to switch the markers off and see every failure raw.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from .targets import TargetNotImplemented

HERE = Path(__file__).parent
REGISTER = HERE / "registers" / "R8_0_EXPECTED_FAILURES.json"
RAISES = {"KNOWN_DEFECT": AssertionError, "TARGET_NOT_IMPLEMENTED": TargetNotImplemented,
          "LIBRARY_KNOWN_FAILURE": AssertionError, "BOUNDARY_DEBT": AssertionError,
          "CONTRACT_DISPUTED": AssertionError}


def load_expected():
    return json.loads(REGISTER.read_text())["expected_failures"]


def pytest_collection_modifyitems(config, items):
    if os.environ.get("R8_0_RAW") == "1":
        return
    table = {e["test"]: e for e in load_expected()}
    for item in items:
        if "tests/r8_0/" not in item.nodeid.replace("\\", "/"):
            continue
        key = item.nodeid.replace("\\", "/").split("tests/r8_0/", 1)[1]
        e = table.get(key)
        if e is None:
            continue
        item.add_marker(pytest.mark.xfail(strict=True, raises=RAISES[e["class"]],
                                          reason=f"{e['class']}: {e.get('defect') or e.get('target') or ''} — {e['reason']}"))
