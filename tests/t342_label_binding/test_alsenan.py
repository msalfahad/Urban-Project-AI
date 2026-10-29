"""T-342 Alsenan binding: rebuild from the committed extracts is byte-identical, and the engineering result holds."""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t342"))
import t342_alsenan as A  # noqa: E402


@pytest.fixture(scope="module")
def built():
    return A.render(), json.loads(A.OUT["summary"].read_text(encoding="utf-8"))


def test_rebuild_is_byte_identical(built):
    out, _ = built
    for k, p in A.OUT.items():
        assert p.read_text(encoding="utf-8") == out[k], k


def test_census_reproduced_before_binding(built):
    _, s = built
    c = s["census"]
    assert (c["labels"], c["MEASURED"], c["HELD"], c["UNSUPPORTED"], c["SILENT_OMISSION"], c["unread_shx"]) == \
        (41, 28, 1, 1, 11, 47)


def test_every_target_label_has_a_binding_and_none_is_silent(built):
    _, s = built
    rows = s["rows"]
    assert set(A.TARGET) <= set(rows)
    assert all(rows[t]["binding"] in ("BOUND", "PARTIAL", "MISSING", "NOT_APPLICABLE", "DUPLICATE_OF") for t in rows)


def test_at19_is_the_pool_not_a_bathroom(built):
    _, s = built
    r = s["rows"]["AT19"]
    assert r["retype"].startswith("RETYPED BATHROOM -> POOL") and r["face"] == "GF-POOL-WATER"
    assert r["binding"] == "PARTIAL" and len(r["lines"]) >= 2          # shell walls + base bound, WP / finish missing
    assert s["rows"]["AT20"]["duplicate_of"] == "AT19"


def test_pool_water_d_matches_the_candidate_shell():
    assert A.WATER_M2 == pytest.approx(math.pi * 1.55 ** 2 / 2 + 3.10 * 1.55)
    assert abs(A.WATER_M2 - 8.578838) < 1e-6                              # the candidate pool line's inner area
    assert A.OUTER_CUT_LM == pytest.approx(12.097787, abs=1e-6)


def test_roof_duplicate_and_void_and_deck():
    sc = {(r["face_id"], r["scope"]): r for r in A.build()[2]["scopes"]}
    assert sc[("2F-ROOF-1", "roof membrane")]["status"] == "BOUND"
    assert sc[("1F-VOID-POOLCOURT", "floor / finishes of the opening")]["status"] == "NOT_APPLICABLE"
    deck = sc[("GF-COURT", "pool deck")]
    assert deck["status"] == "MISSING" and deck["quantity"] == pytest.approx(17.3414 - 10.232, abs=1e-4)
    # a held scope is never 0; the pool finish stays blank with its drawn bound
    fin = sc[("GF-POOL-WATER", "pool water-face finish (floor + walls to the rim)")]
    assert fin["quantity"] is None and fin["bound"][0] > 20
