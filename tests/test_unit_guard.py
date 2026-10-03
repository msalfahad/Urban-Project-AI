"""Tests for E1 — Unit Guard.

The headline test reconstructs the real defect the Phase 0 audit found: a total
of 295.44 that mixed square metres, linear metres and a count. The guard's job
is to make that impossible at the point of entry.
"""

from engine.units import Quantity, Unit
from engine.unit_guard import TakeoffRecord, check, check_batch


def _length(v: float) -> Quantity:
    return Quantity(v, Unit.LENGTH)


def test_valid_area_record_passes():
    # A wall face: 1 instance, 6.0 m long x 3.0 m high = 18.0 m2.
    rec = TakeoffRecord(
        description="Plaster to wall W1",
        count=1,
        dimensions=[_length(6.0), _length(3.0)],
        claimed_unit=Unit.AREA,
    )
    result = check(rec)
    assert result.ok
    assert result.derived_unit is Unit.AREA
    assert result.computed.value == 18.0


def test_valid_count_of_lengths_passes():
    # 5 identical beams, each 4.0 m — a length total, not an area.
    rec = TakeoffRecord(
        description="Skirting run",
        count=5,
        dimensions=[_length(4.0)],
        claimed_unit=Unit.LENGTH,
    )
    result = check(rec)
    assert result.ok
    assert result.computed == Quantity(20.0, Unit.LENGTH)


def test_unit_mismatch_is_caught():
    # Multiplying a count by a single length yields a LENGTH, but the record
    # claims AREA. This is the shape of the audited error.
    rec = TakeoffRecord(
        description="Mislabelled line",
        count=3,
        dimensions=[_length(4.0)],
        claimed_unit=Unit.AREA,
    )
    result = check(rec)
    assert not result.ok
    assert result.derived_unit is Unit.LENGTH
    assert any("unit mismatch" in e for e in result.errors)


def test_dimension_must_be_a_length_not_an_area():
    rec = TakeoffRecord(
        description="Bad dimension",
        count=1,
        dimensions=[Quantity(18.0, Unit.AREA), _length(2.0)],
        claimed_unit=Unit.VOLUME,
    )
    result = check(rec)
    assert not result.ok
    assert any("must be lengths" in e for e in result.errors)


def test_negative_count_is_refused():
    rec = TakeoffRecord(
        description="Negative",
        count=-2,
        dimensions=[_length(3.0)],
        claimed_unit=Unit.LENGTH,
    )
    result = check(rec)
    assert not result.ok


def test_the_295_44_defect_cannot_be_formed():
    """A single line cannot legally sum areas, lengths and a count.

    Adding across unlike units raises inside the units core, so a record that
    tries to reach a mixed total never produces one — it fails the guard.
    """
    pieces = [
        Quantity(180.0, Unit.AREA),
        Quantity(100.0, Unit.LENGTH),
        Quantity(15.44, Unit.COUNT),
    ]
    total = Quantity(0.0, Unit.AREA)
    raised = False
    try:
        for p in pieces:
            total = total + p
    except Exception:
        raised = True
    assert raised, "mixing m2 + m + count into one total must be impossible"


def test_batch_reports_each_line():
    recs = [
        TakeoffRecord("good", 1, [_length(2.0), _length(2.0)], Unit.AREA),
        TakeoffRecord("bad", 1, [_length(2.0)], Unit.AREA),
    ]
    results = check_batch(recs)
    assert results[0].ok
    assert not results[1].ok
