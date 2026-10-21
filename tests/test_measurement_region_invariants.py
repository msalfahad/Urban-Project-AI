"""Invariants §120 and §121 — the physical/measurement separation.

Two of these run today against the frozen experiment. The other two are
the mandatory CI requirements for the future QS_MEASUREMENT_REGION_BUILDER:
they skip while no builder exists and bite the moment one does, so the
rule cannot be quietly lost between now and then.

Nothing here reruns, retunes or rewrites the frozen experiment. It reads it.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

EXP = Path("data/experiments/QS_MEASUREMENT_REGION_EXPERIMENT_01")

# Recorded when the experiment was frozen. A change here means a frozen
# artifact moved, which is itself the failure.
FREEZE_SHA256 = "c9d13a2c350b0d5ee8d050363afc6813880999ccc4773dbd5addf5846426f252"
PROTOCOL_SHA256 = "71eb8ec7cfe9c64c5c4ae1e9862d48b197b163f67f51d415798f0d5b8133ee8d"

SYNTHETIC_ROLES = {"SYNTHETIC_MEASUREMENT_BOUNDARY", "OPEN_PHYSICAL_EDGE",
                   "UNRESOLVED_EDGE"}
MATERIAL_FLAGS = ("MATERIAL_LENGTH_CONTRIBUTION",
                  "PLASTER_LENGTH_CONTRIBUTION",
                  "WALL_CERAMIC_LENGTH_CONTRIBUTION")

frozen = pytest.mark.skipif(
    not EXP.exists(),
    reason="the frozen experiment is not present in this checkout")


def _load(name):
    return json.loads((EXP / name).read_text("utf-8"))


@frozen
def test_the_frozen_experiment_still_hashes_as_recorded():
    """§9 of the accepting directive: preserve the hashes exactly."""
    freeze = _load("FREEZE.json")
    assert freeze["PROTOCOL_HASH"] == PROTOCOL_SHA256
    assert freeze["FREEZE_SHA256"] == FREEZE_SHA256

    files = {}
    for p in sorted(EXP.rglob("*")):
        if p.is_file() and p.name != "FREEZE.json":
            files[str(p.relative_to(EXP))] = hashlib.sha256(
                p.read_bytes()).hexdigest()
    recomputed = hashlib.sha256(json.dumps(
        {k: files[k] for k in sorted(files)}, sort_keys=True).encode()
    ).hexdigest()
    assert recomputed == FREEZE_SHA256, (
        "a frozen artifact changed: the experiment is accepted as a result "
        "and may not be rerun, retuned or edited")


@frozen
def test_no_synthetic_or_open_edge_contributes_material_length():
    """§121 ZERO MATERIAL CONTRIBUTION, over the frozen edges.

    Polygon perimeter may never silently become wall length.
    """
    edges = _load("EDGE_CONTRIBUTION_REGISTER.json")["EDGES"]
    assert edges, "the edge register is empty"
    offenders = [
        (e["CANDIDATE_ID"], e["SEQ"], f)
        for e in edges if e["TOPOLOGICAL_ROLE"] in SYNTHETIC_ROLES
        for f in MATERIAL_FLAGS if e["TRADE_CONTRIBUTION_ROLE"][f]]
    assert not offenders, f"synthetic edges carrying material: {offenders[:5]}"

    # and E1.4's own independently computed figure must agree at zero
    disagree = [(e["CANDIDATE_ID"], e["SEQ"],
                 e["E1_4_wall_length_contribution_mm"])
                for e in edges
                if e["TOPOLOGICAL_ROLE"] == "SYNTHETIC_MEASUREMENT_BOUNDARY"
                and (e["E1_4_wall_length_contribution_mm"] or 0) != 0]
    assert not disagree, f"E1.4 disagrees at a synthetic edge: {disagree[:5]}"


@frozen
def test_physical_and_measurement_closure_are_never_the_same_number():
    """§120. A region closed through a zero-material portal is not
    enclosed by drawn material, and the two counts are never summed."""
    met = _load("METRIC_SEPARATION.json")
    assert met["PHYSICAL_REGIONS_ENCLOSED_BY_DRAWN_MATERIAL"] == 0
    assert met["MEASUREMENT_REGIONS_CLOSED"] == 3
    assert "CLOSED_ROOMS" not in met, (
        "there is no combined closed-rooms metric, by design")

    for row in met["PER_CANDIDATE"]:
        if row["PHYSICAL_REGION_STATUS"] == "CLOSED_BY_DRAWN_MATERIAL":
            assert row["confirmed_openings_encountered"] == 0, (
                "a region reported as enclosed by drawn material used an "
                f"opening to close: {row['CANDIDATE_ID']}")


@frozen
def test_the_fifteen_unresolved_gaps_were_not_promoted():
    """§5 of the accepting directive. Closure success is not evidence."""
    sites = _load("OPENING_SITE_REGISTER.json")
    assert sites["BY_SITE_TYPE"].get("UNRESOLVED_GAP") == 15
    for s in sites["SITES"]:
        if s["SITE_TYPE"] == "UNRESOLVED_GAP":
            assert not s["ELIGIBLE_FOR_A_MEASUREMENT_CLOSURE"], (
                f"an unresolved gap became eligible: {s['SITE_ID']}")
    closures = _load("MEASUREMENT_CLOSURE_REGISTER.json")["CLOSURES"]
    bridged = {c["source_opening_id"] for c in closures}
    unresolved = {s["SITE_ID"] for s in sites["SITES"]
                  if s["SITE_TYPE"] == "UNRESOLVED_GAP"}
    assert not (bridged & unresolved), "an unresolved gap was bridged"


# ------------------------------------------------------------------
# Mandatory CI requirements for the future builder. These skip while no
# builder exists, and bite the moment one does.
# ------------------------------------------------------------------
def _builder():
    try:
        from engine import qs_measurement_region_builder as b
        return b
    except ImportError:
        return None


needs_builder = pytest.mark.skipif(
    _builder() is None,
    reason="QS_MEASUREMENT_REGION_BUILDER does not exist yet; §121 applies "
           "the moment it does")


@needs_builder
def test_builder_proves_reversibility_by_hash():
    """§121 REVERSIBILITY. Proved, never stored.

    The builder must expose a check that hashes the physical claims,
    constructs every closure, removes them all, and compares.
    """
    b = _builder()
    assert hasattr(b, "reversibility_check"), (
        "the builder must expose reversibility_check() — REVERSIBLE is "
        "proved, never stored")
    got = b.reversibility_check()
    assert got["HASH_A_EQUALS_HASH_C"] is True, got
    assert not got.get("CLOSURES_THAT_LEAKED_INTO_LAYER_A")


@needs_builder
def test_builder_never_bridges_an_unresolved_site():
    """§121. An UNRESOLVED_GAP may never receive a measurement closure."""
    b = _builder()
    assert hasattr(b, "closures_for"), "the builder must expose closures_for()"
    for c in b.closures_for(trade="PLASTER"):
        assert c["physical_material_present"] is False
        assert c["physical_wall"] is False
        assert c["changes_connectivity"] is False
        assert c["quantity_length_contribution"] == 0
        assert c["source_opening_id"], "a closure must name its opening"
