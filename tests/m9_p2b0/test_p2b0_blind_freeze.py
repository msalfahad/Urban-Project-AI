"""Phase 2B-0 P1, blind readiness: the scorer, the dry run, the protocol and the facts template are frozen (sha256 in
research/urban_m9_p2b0/BLIND_READINESS_RECORD.json); the facts template holds no number and is refused until filled."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

import pytest

from engine.source import arch_measure as AM

ROOT = Path(__file__).resolve().parents[2]
REC = json.loads((ROOT / "research/urban_m9_p2b0/BLIND_READINESS_RECORD.json").read_text(encoding="utf-8"))
TEMPLATE = ROOT / "research/urban_m9_p2b0/FACTS_TEMPLATE_HEIGHTS.json"


def test_the_frozen_evaluation_files_are_unchanged():
    for p, h in REC["frozen_evaluation_sha256"].items():
        assert hashlib.sha256((ROOT / p).read_bytes()).hexdigest() == h, \
            f"{p} changed after the blind-readiness freeze: record a protocol amendment and re-freeze"


def test_the_facts_template_holds_no_value_and_is_refused_until_filled():
    t = json.loads(TEMPLATE.read_text(encoding="utf-8"))
    vals = [v["value_m"] for g in ("wall_heights", "opening_heights") for blk in
            ([t[g]] if g == "opening_heights" else t[g].values()) for v in blk.values()]
    assert vals and all(v is None for v in vals)
    with pytest.raises(AM.FactsError):
        AM.validate_facts(t)
    filled = copy.deepcopy(t)
    for blk in list(filled["wall_heights"].values()) + [filled["opening_heights"]]:
        for v in blk.values():
            v["value_m"], v["authority"] = 2.5, "SOURCE: test"
    assert AM.validate_facts(filled) is filled
