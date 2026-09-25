"""Project 23010 as a permanent regression fixture — and the rules it enforces.

Two kinds of test live here. The first re-measures the frozen drawing and holds
the result against the fixture. The second tests the fixture machinery itself:
that a safety property can never be waved through, that a measured value can
move but only with a written reason, and that a fixture cannot quietly stop
pointing at the drawing it claims to pin.
"""

from __future__ import annotations

import json
from decimal import Decimal as D
from pathlib import Path

import pytest

from engine.golden import (BUMP_FIELDS, EXPECTATION_DRIFT, INPUT_CHANGED,
                           INVARIANT_VIOLATION, MISSING, GoldenError,
                           GoldenFixture, forbidden_strings)

GOLDEN = Path("data/golden/23010")

# The golden data is a client drawing and a client's manual measurements, so it
# is gitignored and will not be present on a fresh clone. The tests skip rather
# than fail there: a missing client file is not a regression, and a suite that
# goes red on checkout teaches people to ignore red.
pytestmark = pytest.mark.skipif(
    not (GOLDEN / "fixture.json").exists(),
    reason="golden data for 23010 is not mounted (client drawing, gitignored) — "
           "see runs/golden/23010_MANIFEST.json for what it should contain")

FIXTURE = (GoldenFixture.load(GOLDEN / "fixture.json")
           if (GOLDEN / "fixture.json").exists() else None)


# --- the fixture points at the real, audited inputs --------------------------

def test_the_frozen_drawing_is_in_the_repo_not_a_session_upload():
    """The audited PDF used to live under a session-scoped upload path that
    disappears with the container. A fixture that cannot reach its own input
    proves nothing on a fresh machine."""
    pdf = GOLDEN / "inputs/AR-00_MAR2023.pdf"
    assert pdf.exists() and pdf.stat().st_size > 100_000


def test_every_frozen_input_still_hashes_to_what_was_audited():
    assert FIXTURE.check_inputs() == []


def test_the_fixture_pins_the_run_1_geometry_hash():
    assert FIXTURE.expectations["geometry_sha256"] == (
        "83fc1037cff6154072be02e7f1b6d271cbca6cd394a5002dd43f02621d48a583")


# --- invariants are not negotiable -------------------------------------------

def test_a_safety_property_cannot_be_waved_through_by_a_version_bump():
    rep = FIXTURE.check({**FIXTURE.invariants, **FIXTURE.expectations,
                         "benchmark_leakage_count": 1})
    assert not rep.ok
    assert [f.kind for f in rep.violations] == [INVARIANT_VIOLATION]
    assert "no version bump that permits" in rep.explain()


def test_an_unmeasured_safety_property_is_not_a_pass():
    """Silence is not the same as zero."""
    observed = {k: v for k, v in FIXTURE.invariants.items()
                if k != "accepted_geometry_mutations"}
    rep = FIXTURE.check(observed)
    assert any(f.kind == MISSING and f.name == "accepted_geometry_mutations"
               for f in rep.findings)


def test_a_changed_input_invalidates_every_expectation_below_it(tmp_path):
    f = GoldenFixture.from_dict(
        {"project": "T", "fixture_version": "1.0",
         "inputs": {"drawing.pdf": "0" * 64},
         "invariants": {"leak": 0}}, root=tmp_path)
    (tmp_path / "drawing.pdf").write_bytes(b"a different drawing")
    rep = f.check({"leak": 0})
    assert [x.kind for x in rep.findings] == [INPUT_CHANGED]
    assert rep.violations


# --- expectations may move, but only deliberately ----------------------------

def test_a_measured_value_that_moves_is_a_failure_by_default():
    """Otherwise the fixture is not a guardrail."""
    rep = FIXTURE.check({**FIXTURE.invariants, **FIXTURE.expectations,
                         "engine_full_scope_m2": "399.10"})
    assert not rep.ok and not rep.violations
    assert [f.kind for f in rep.drift] == [EXPECTATION_DRIFT]


def test_the_drift_message_says_what_a_legitimate_bump_needs():
    rep = FIXTURE.check({**FIXTURE.invariants, **FIXTURE.expectations,
                         "space_count": 37})
    text = rep.explain()
    for required in BUMP_FIELDS:
        assert required in text


def test_a_version_bump_without_a_root_cause_is_refused():
    """Editing the expected value and calling it a bump is the failure mode."""
    with pytest.raises(GoldenError, match="missing"):
        GoldenFixture.from_dict({
            "project": "T", "fixture_version": "2.0",
            "invariants": {"leak": 0},
            "drift_log": [{"root_cause": "", "not_project_specific": True,
                           "projects_reviewed": ["23010"], "date": "2026-09-13"}],
        })


def test_a_properly_recorded_bump_is_accepted():
    f = GoldenFixture.from_dict({
        "project": "T", "fixture_version": "2.0",
        "invariants": {"leak": 0},
        "expectations": {"area": "10.00"},
        "drift_log": [{
            "root_cause": "E31 vector planar faces replace the raster boundary on "
                          "irregular rooms; the understatement this fixture pinned "
                          "was an engine limitation, not the drawing.",
            "not_project_specific": True,
            "projects_reviewed": ["23010"],
            "date": "2026-09-13"}],
    })
    assert f.fixture_version == "2.0"


def test_a_fixture_with_no_invariants_is_refused():
    with pytest.raises(GoldenError, match="pins nothing that matters"):
        GoldenFixture.from_dict({"project": "T", "fixture_version": "1.0",
                                 "expectations": {"area": "1.00"}})


# --- the sealed benchmark -----------------------------------------------------

def test_the_site_benchmark_is_recorded_as_having_no_production_role():
    data = json.loads((GOLDEN / "site_benchmark.json").read_text(encoding="utf-8"))
    assert data["production_role"].startswith("NONE")
    assert "395.67" in json.dumps(data)


def test_the_leak_audit_derives_its_forbidden_list_from_the_benchmark_itself():
    """A hand-typed list of forbidden numbers goes stale the first time someone
    adds a benchmark row and forgets."""
    forbidden = forbidden_strings(GOLDEN / "site_benchmark.json")
    for answer in ("395.67", "322.50", "73.17", "102.70", "69.02"):
        assert answer in forbidden


def test_values_that_are_legitimate_production_input_are_not_false_leaks():
    forbidden = forbidden_strings(GOLDEN / "site_benchmark.json")
    for legitimate in ("23010", "2F", "OPEN-01", "STR-01"):
        assert legitimate not in forbidden


def test_the_run_1_input_packages_contain_no_benchmark_value():
    """Re-audited against the derived list rather than the one typed at the time."""
    forbidden = forbidden_strings(GOLDEN / "site_benchmark.json")
    for name in ("a1_user.txt", "a2blind_user.txt"):
        text = (Path("data/runs/run1") / name).read_text(encoding="utf-8")
        assert not [f for f in forbidden if f in text]


# --- known defects are written down, not pinned as correct -------------------

def test_the_three_open_geometry_defects_are_recorded_as_defects():
    known = FIXTURE.ambiguities["known_geometry_defects_at_v1_0"]
    assert set(known) >= {"WSH-01", "OPEN-01", "BED-04"}
    assert "REGION_IDENTITY" in known["WSH-01"]


def test_the_nine_unscored_apartment_spaces_are_named():
    assert len(FIXTURE.ambiguities["apartment_unscored"]) == 9


# --- the real run -------------------------------------------------------------

@pytest.mark.slow
def test_remeasuring_the_frozen_drawing_reproduces_the_geometry_hash():
    """The whole point: the same PDF through the same engine gives the same hash."""
    import hashlib
    from engine.geometry import VectorPdfSource, calibrate
    src = VectorPdfSource(str(GOLDEN / "inputs/AR-00_MAR2023.pdf"),
                          calibrate(887.82, 40000, 554.94, 25000))
    regions = {r.id: {"area_m2": str(r.area_m2), "raw_area_m2": str(r.raw_area_m2),
                      "w_mm": r.width_mm, "h_mm": r.height_mm,
                      "cx": r.centroid_px[0], "cy": r.centroid_px[1],
                      "basis": r.basis}
               for r in src.regions(0, min_m2=0.3)}
    space_map = json.loads((GOLDEN / "inputs/space_map_23010_2f.json")
                           .read_text(encoding="utf-8"))
    rules = {n: json.loads(Path(f"data/trade_rules/{n}.json").read_text(encoding="utf-8"))
             for n in ("23010_ceramic", "23010_plaster")}
    snapshot = {"regions": regions,
                "space_regions": {s["space_id"]: s["region"] for s in space_map["spaces"]},
                "trade_rules": rules,
                "calibration": str(src.calibration.mm_per_pt)}
    blob = json.dumps(snapshot, sort_keys=True, ensure_ascii=False).encode()
    assert hashlib.sha256(blob).hexdigest() == FIXTURE.expectations["geometry_sha256"]


def test_the_engines_own_figures_are_not_treated_as_sealed_answers():
    """Caught by re-auditing: 4.09 is STR-01's engine area, which was always in
    the input package. Sealing it would have made a correct package look leaky."""
    forbidden = forbidden_strings(GOLDEN / "site_benchmark.json")
    assert "4.08" in forbidden          # the manual row IS an answer
    assert "4.09" not in forbidden      # the engine's own output is not
