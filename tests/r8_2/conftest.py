"""R8.2 strict expected-failure mechanism (same contract as tests/r8_0/conftest.py).

cad_adapter is FROZEN until the migration commit. Its newly registered defects
are strict KNOWN_DEFECT xfails: a fix can never slip in without this register
changing in the same commit. R8_0_RAW=1 disables the markers.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

REGISTER = Path(__file__).parent / "registers" / "R8_2_CAD_ADAPTER_DEFECTS.json"


def pytest_collection_modifyitems(config, items):
    if os.environ.get("R8_0_RAW") == "1":
        return
    table = {}
    for d in json.loads(REGISTER.read_text())["defects"]:
        for t in d["characterisation_tests"]:
            table[t] = d
    for item in items:
        nid = item.nodeid.replace("\\", "/")
        if "tests/r8_2/" not in nid:
            continue
        d = table.get(nid.split("tests/r8_2/", 1)[1])
        if d is not None:
            item.add_marker(pytest.mark.xfail(strict=True, raises=AssertionError,
                                              reason=f"KNOWN_DEFECT {d['id']}: {d['summary']}"))
