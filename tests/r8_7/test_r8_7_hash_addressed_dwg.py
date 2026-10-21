"""The candidate new-revision DWG enters tests only through the hash-addressed store; missing skips, drift fails."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = json.loads((Path(__file__).parent / "FIXTURE_MANIFEST.json").read_text())


def test_candidate_dwg_bytes_are_the_declared_file():
    want = MANIFEST["inputs"]["QORTUBA_REV_NEW_CANDIDATE_DWG"]
    p = ROOT / MANIFEST["store"] / f"{want['sha256']}{want['suffix']}"
    if not p.exists():
        pytest.skip(f"hash-addressed input not present in this checkout: {p.relative_to(ROOT)}")
    h = hashlib.sha256()
    with open(p, "rb") as f:
        head = f.read(6)
        h.update(head)
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    assert h.hexdigest() == want["sha256"] and p.stat().st_size == want["bytes"], "INPUT DRIFT"
    assert head == b"AC1032"
