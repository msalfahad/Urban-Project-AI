"""Blocked is not a footnote on a number; it is the absence of a number.

R4 marked all sixty-one wall rows blocked and published a 150 mm and a 200 mm figure anyway, beside the frozen
ones, as a comparison.  Nothing in the engine objected, because nothing had been asked to.
"""

from __future__ import annotations

from engine.qs_core import invariants, quantities as QY

BLOCKED = "BLOCKED_PENDING_ANSWERS"


def rows():
    return [
        {"COMPONENT_REF": "L1", "THICKNESS_M": 0.20, "NET_AREA_M2": 10.0, "STATUS": QY.FINAL},
        {"COMPONENT_REF": "L2", "THICKNESS_M": 0.20, "NET_AREA_M2": None, "STATUS": BLOCKED,
         "DIAGNOSTIC_ONLY_NET_AREA_M2": 4.0, "BLOCKED_NOTE": "a host is unproved",
         "BLOCKED_BY": [{"KIND": "HOST_WALL_UNRESOLVED", "WHY": "a host is unproved"}]},
        {"COMPONENT_REF": "L3", "THICKNESS_M": 0.15, "NET_AREA_M2": 7.0, "STATUS": QY.FINAL},
    ]


def publish(rs, blocked_groups=None):
    return QY.publish(rs, lambda r: r["THICKNESS_M"], "NET_AREA_M2", "m2", "masonry by thickness",
                      blocked_groups=blocked_groups)


def test_a_subtotal_with_one_blocked_contributor_is_null_not_provisional():
    pub = publish(rows())
    assert pub["SUBTOTALS"]["0.2"]["FINAL_QUANTITY"] is None
    assert pub["SUBTOTALS"]["0.2"]["STATUS"] == QY.STATUS_BLOCKED
    assert pub["SUBTOTALS"]["0.15"]["FINAL_QUANTITY"] == 7.0


def test_the_project_total_is_null_while_any_subtotal_is_null():
    assert publish(rows())["PUBLISHED_TOTAL"] is None
    clean = [r for r in rows() if r["STATUS"] == QY.FINAL]
    assert publish(clean)["PUBLISHED_TOTAL"] == 17.0


def test_a_diagnostic_value_is_named_so_it_cannot_be_summed_by_accident():
    pub = publish(rows())
    sub = pub["SUBTOTALS"]["0.2"]
    assert sub[QY.diagnostic_name("SUM_OF_EVERY_ROW")] == 14.0
    assert all(k.startswith(QY.DIAGNOSTIC_PREFIX) or k != "FINAL_QUANTITY" or sub[k] is None
               for k in sub if "SUM" in k)
    assert rows()[1]["NET_AREA_M2"] is None


def test_the_reader_is_told_what_each_null_is_waiting_on():
    sub = publish(rows())["SUBTOTALS"]["0.2"]
    assert sub["WAITING_ON"][0]["REF"] == "L2"
    assert "a host is unproved" in sub["WAITING_ON"][0]["WHY"]
    assert sub["WHY_NULL"]


def test_a_subtotal_can_be_blocked_by_something_that_is_not_in_its_rows():
    """A band whose identity is unresolved might belong to this thickness and is not a row of it yet."""
    clean = [r for r in rows() if r["STATUS"] == QY.FINAL]
    pub = publish(clean, blocked_groups={0.15: {"KIND": "WALL_IDENTITY_UNRESOLVED",
                                                "WHY": "a band of this thickness is not established"}})
    assert pub["SUBTOTALS"]["0.15"]["FINAL_QUANTITY"] is None
    assert pub["SUBTOTALS"]["0.2"]["FINAL_QUANTITY"] == 10.0


def test_the_invariant_passes_on_an_honest_publication():
    rs = rows()
    assert invariants.blocked_never_enters_a_published_total(publish(rs), rs, "NET_AREA_M2")["PASS"]


def test_the_mutation_that_sums_everything_is_caught():
    """The R4 behaviour, re-implemented: sum the rows and publish the answer."""
    rs = rows()

    def sum_everything(rows_, group_of, field, unit, what, blocked_groups=None, reasons_of=None):
        subs = {}
        for r in rows_:
            g = str(group_of(r))
            value = r.get(field)
            if value is None:
                value = r.get(QY.diagnostic_name(field)) or 0.0
            s = subs.setdefault(g, {"GROUP": g, "FINAL_QUANTITY": 0.0, "ROWS_FINAL": 0, "ROWS_BLOCKED": 0,
                                    "FINAL_ROW_REFS": [], "BLOCKED_ROW_REFS": [], "WAITING_ON": [],
                                    "STATUS": QY.STATUS_FINAL, "WHY_NULL": None})
            s["FINAL_QUANTITY"] += value
            key = "ROWS_FINAL" if r.get("STATUS") == QY.FINAL else "ROWS_BLOCKED"
            s[key] += 1
        return {"SUBTOTALS": subs,
                "PUBLISHED_TOTAL": round(sum(s["FINAL_QUANTITY"] for s in subs.values()), 6),
                "BLOCKED_SUBTOTAL_COUNT": 0, "PUBLISHED_SUBTOTAL_COUNT": len(subs),
                "WHAT": "masonry", "UNIT": "m2"}

    mutant = sum_everything(rs, lambda r: r["THICKNESS_M"], "NET_AREA_M2", "m2", "masonry")
    assert mutant["SUBTOTALS"]["0.2"]["FINAL_QUANTITY"] == 14.0, "the mutation does publish a figure"
    check = invariants.blocked_never_enters_a_published_total(mutant, rs, "NET_AREA_M2")
    assert not check["PASS"]
    assert any(o.get("SUBTOTAL") == "0.2" for o in check["RESULT"]["OFFENDERS"])


def test_the_invariant_also_catches_a_blocked_row_carrying_a_publishable_value():
    rs = rows()
    rs[1]["NET_AREA_M2"] = 4.0            # the value put back under the summable name
    check = invariants.blocked_never_enters_a_published_total(publish(rs), rs, "NET_AREA_M2")
    assert not check["PASS"]
    assert any(o.get("ROW") == "L2" for o in check["RESULT"]["OFFENDERS"])


def test_no_rows_at_all_publishes_nothing_rather_than_zero():
    """An extraction that produced no wall is not a building with no wall in it."""
    pub = QY.publish([], lambda r: r["THICKNESS_M"], "NET_AREA_M2", "m2", "masonry")
    assert pub["SUBTOTALS"] == {} and pub["PUBLISHED_TOTAL"] is None and pub["NOTHING_TO_PUBLISH"]
