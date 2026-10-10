"""R8.7 on the declared fixture (the OLD revision's pinned decode): the QS01 room method through the canonical
contract reproduces the R8.6 six rows; the R8.6 silent HALL case can no longer publish; identity is stable across
repeated decodes and specific to the revision; mixed revisions and a cut frame fail closed."""

from __future__ import annotations

import hashlib
import json
import sys
from dataclasses import replace
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = json.loads((Path(__file__).parent / "FIXTURE_MANIFEST.json").read_text())
SIX = {"Q-03": 17.8625, "Q-03P": 11.685, "Q-11": 17.8625, "Q-12": 11.685, "Q-13": 108.9625, "Q-14": 138.51}


@pytest.fixture(scope="module")
def R7():
    for path, want in MANIFEST["fixtures"].items():
        if not (ROOT / path).exists():
            pytest.skip(f"declared fixture not present in this checkout: {path}")
        assert hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == want, f"FIXTURE DRIFT: {path}"
    sys.path.insert(0, str(ROOT / "research/external_engine_lab"))
    import r8_7_canonical as m
    return m


@pytest.fixture(scope="module")
def base(R7):
    return R7.old_input()


def test_old_revision_through_the_contract_reproduces_the_six_rows(R7, base):
    m = R7.measure(base, expected_revision_id=R7.REV_OLD_ID)
    assert m["state"] == "COMPLETE" and m["six"] == SIX
    assert m["validation"]["excluded_by_declaration"] == {"ELLIPTICAL_ARC": 8}
    assert float(m["method_unit"]["UNIT_SCALE_TO_MM"]) == base.unit_native_to_mm == 10.0


def test_the_r86_silent_hall_case_publishes_nothing(R7, base):
    """Permanent regression: same segments, block identity and part identity lost. The unguarded method silently
    turns HALL 36.37 into 25.0925 m2; through the contract there is no quantity at all."""
    def lossy(p):
        if p.identity.instance_handles:
            p = replace(p, lineage=())
        if p.entity_type == "LWPOLYLINE":
            p = replace(p, identity=replace(p.identity, part_index=None))
        return p
    bad = replace(base, parts=tuple(lossy(p) for p in base.parts))
    assert [p.geometry for p in bad.parts] == [p.geometry for p in base.parts]          # identical geometry
    silent = R7.lenient_values(bad)
    assert ["HALL / whgm", 25.0925] in [[r["room"], r["area_m2"]] for r in silent["rooms"]]
    m = R7.measure(bad, expected_revision_id=R7.REV_OLD_ID)
    assert m["state"] == "METHOD_INPUT_INCOMPLETE" and m["six"] is None and m["rooms"] is None
    assert {"parts.block_identity", "parts.source_part_id"} <= set(m["validation"]["missing_fields"])


def test_source_identity_is_stable_across_repeated_decodes_and_revision_specific(R7):
    a = R7.k1_records(R7.rev_old())[0]
    b = R7.k1_records(R7.rev_old())[0]
    ka, kb = [p.identity.key for p in a], [p.identity.key for p in b]
    assert ka == kb and None not in ka and len(set(ka)) == len(ka)
    other = R7.CI.SourceRevision("ANOTHER_REVISION", R7.CI.EXACT_SOURCE, "e" * 64)
    kc = {p.identity.key for p in R7.k1_records(other)[0]}
    assert kc.isdisjoint(ka)


def test_mixed_revision_input_is_blocked(R7, base):
    mixed = replace(base, revision=R7.rev_new())                          # old records under the new anchor
    m = R7.measure(mixed, expected_revision_id=R7.REV_NEW_ID)
    assert m["state"] == "SOURCE_REVISION_MISMATCH" and m["six"] is None


def test_wrong_plan_variant_is_blocked(R7, base):
    m = R7.measure(replace(base, region_id="RC:PLAN_VARIANT_3"), expected_revision_id=R7.REV_OLD_ID)
    assert m["state"] == "REGION_NOT_SELECTED" and m["six"] is None


def test_a_cut_frame_occurrence_is_review_required_not_a_room(R7):
    cut = R7.old_input(bounds=R7.BOUNDS)                                  # the candidate bounds cut the frame block
    m = R7.measure(cut, expected_revision_id=R7.REV_OLD_ID)
    assert m["state"] == "METHOD_INPUT_INCOMPLETE" and m["validation"]["region_review_required"] > 0
