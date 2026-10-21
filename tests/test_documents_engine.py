"""E22 — Document Numbers tests."""

from datetime import date

import pytest

from engine.documents import (
    Milestone, PriceLine, amount_in_words_ar, format_kwd, grand_total, ordinal_ar,
    payment_schedule, reference_number, summarise_by_package, validity_expiry,
)


# ---- ordinals / formatting ----------------------------------------------------
def test_ordinals_run_in_document_order():
    assert [ordinal_ar(i) for i in (1, 2, 3, 10)] == ["أولاً", "ثانياً", "ثالثاً", "عاشراً"]


def test_ordinal_out_of_range():
    with pytest.raises(ValueError):
        ordinal_ar(0)
    with pytest.raises(ValueError):
        ordinal_ar(99)


def test_format_kwd_has_fils_and_grouping():
    assert format_kwd(93500) == "93,500.000 د.ك"
    assert format_kwd(12.5) == "12.500 د.ك"


def test_reference_number_shape():
    assert reference_number(date(2026, 9, 12), 1) == "UP/2026-9-001-R01"
    assert reference_number(date(2025, 8, 21), 415, revision=2, prefix="AWJ") == "AWJ/2025-8-415-R02"


def test_reference_number_rejects_zero():
    with pytest.raises(ValueError):
        reference_number(date(2026, 1, 1), 0)


def test_validity_expiry():
    assert validity_expiry(date(2026, 9, 12), 14) == date(2026, 9, 26)
    with pytest.raises(ValueError):
        validity_expiry(date(2026, 9, 12), 0)


# ---- price table --------------------------------------------------------------
def test_summarise_by_package_groups_and_keeps_order():
    lines = summarise_by_package([
        ("أعمال الهيكل الأسود", 50000.0),
        ("أعمال الصحي", 16900.0),
        ("أعمال الهيكل الأسود", 43500.0),
    ])
    assert [l.package for l in lines] == ["أعمال الهيكل الأسود", "أعمال الصحي"]
    assert lines[0].amount_kwd == 93500.0


def test_summarise_rejects_nameless_or_negative():
    with pytest.raises(ValueError, match="package name"):
        summarise_by_package([("  ", 1.0)])
    with pytest.raises(ValueError, match="negative"):
        summarise_by_package([("x", -1.0)])


def test_grand_total_exact():
    assert grand_total([PriceLine("a", 93500.0), PriceLine("b", 16900.0)]) == 110400.0
    assert grand_total([PriceLine("a", 0.1), PriceLine("b", 0.2)]) == 0.3


def test_grand_total_needs_lines():
    with pytest.raises(ValueError):
        grand_total([])


# ---- payment schedule ---------------------------------------------------------
def test_payment_schedule_sums_exactly():
    rows = payment_schedule(1000.0, [Milestone("أ", 33.333), Milestone("ب", 33.333), Milestone("ج", 33.334)])
    assert round(sum(r["amount_kwd"] for r in rows), 3) == 1000.0
    assert [r["trigger"] for r in rows] == ["أ", "ب", "ج"]


def test_payment_schedule_must_total_100():
    with pytest.raises(ValueError, match="sum to 100"):
        payment_schedule(1000.0, [Milestone("a", 50), Milestone("b", 40)])


def test_payment_schedule_rejects_bad_milestones():
    with pytest.raises(ValueError, match="trigger"):
        payment_schedule(100.0, [Milestone(" ", 100)])
    with pytest.raises(ValueError, match="positive"):
        payment_schedule(100.0, [Milestone("a", 0), Milestone("b", 100)])
    with pytest.raises(ValueError):
        payment_schedule(100.0, [])


# ---- amount in words ----------------------------------------------------------
@pytest.mark.parametrize("amount, words", [
    (0, "فقط صفر دينار كويتي لا غير"),
    (1, "فقط دينار كويتي واحد لا غير"),
    (2, "فقط ديناران كويتيان لا غير"),
    (3, "فقط ثلاثة دنانير كويتية لا غير"),
    (11, "فقط أحد عشر ديناراً كويتياً لا غير"),
    (21, "فقط واحد وعشرون ديناراً كويتياً لا غير"),
    (100, "فقط مائة دينار كويتي لا غير"),
    (105, "فقط مائة وخمسة دنانير كويتية لا غير"),
    (1000, "فقط ألف دينار كويتي لا غير"),
    (2000, "فقط ألفان دينار كويتي لا غير"),
    (3000, "فقط ثلاثة آلاف دينار كويتي لا غير"),
    (21000, "فقط واحد وعشرون ألفاً دينار كويتي لا غير"),
    (93500, "فقط ثلاثة وتسعون ألفاً وخمسمائة دينار كويتي لا غير"),
    (110400, "فقط مائة وعشرة آلاف وأربعمائة دينار كويتي لا غير"),
    (121626, "فقط مائة وواحد وعشرون ألفاً وستمائة وستة وعشرون ديناراً كويتياً لا غير"),
    (2500000, "فقط مليونان وخمسمائة ألف دينار كويتي لا غير"),
    (12.75, "فقط اثنا عشر ديناراً كويتياً وسبعمائة وخمسون فلساً لا غير"),
    (2.002, "فقط ديناران كويتيان وفلسان لا غير"),
])
def test_amount_in_words(amount, words):
    assert amount_in_words_ar(amount) == words


def test_amount_in_words_rejects_negative_and_huge():
    with pytest.raises(ValueError):
        amount_in_words_ar(-1)
    with pytest.raises(ValueError):
        amount_in_words_ar(1_000_000_000)
