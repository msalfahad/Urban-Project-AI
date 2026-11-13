"""T-755 R-T755-1: named designer ids, item view, version-step reconciliation (synthetic, not the training villa)."""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t755"))

import t755_rules as R  # noqa: E402

NAMED = ("D-NX1", "D-FACADE-2")
ITEMS = {"D-04": ["1"], "D-44": ["1", "3"], "D-16": ["3"], "D-NX1": ["9"]}


def _ix(lid, code, unit, lo=None, hi=None, cls="HELD", eid=None):
    return {"line_id": lid, "item_code": code, "unit": unit, "held_low": lo, "held_high": hi, "class": cls,
            "element_id": eid or f"E:{lid}"}


def _rec(text=None, notes=None):
    return {"rfi": {"question": text} if text else None, "notes": notes}


def L(n):
    return f"L-{n:020d}"


def test_named_ids_are_read_only_from_the_closed_list():
    k = R.classify_own
    assert k(_rec("band shape not dimensioned (D-NX1)"), NAMED)["bucket"] == "D-NX1"
    assert k(_rec("D-04 and D-NX1"), NAMED)["bucket"] == "D-04+D-NX1"
    # a door mark of the same shape is not an item; an id not in today's list is not read either
    assert k(_rec("junction at D-GF-04"), NAMED)["kind"] == "NAMED_TEXT"
    assert k(_rec("facade D-FACADE-2X"), NAMED)["kind"] == "NAMED_TEXT"      # whole token only
    assert k(_rec("band D-NX1"), ())["kind"] == "NAMED_TEXT"                 # no list -> R-T716-1 unchanged
    # an own D-id still outranks an owner question (rule order of R-T716-1)
    assert k(_rec("Q-34 open; D-NX1"), NAMED)["kind"] == "DESIGNER"


def test_normal_two_lines_on_one_item_one_shared_per_unit():
    ix = [_ix(L(1), "STR.CONC.BEAM", "m3", 1.0, 2.0), _ix(L(2), "STR.CONC.BEAM", "m3", 0.5, None),
          _ix(L(3), "STR.CONC.COLUMN", "m3", 0.25, 0.75), _ix(L(4), "FIN.WP", "m2", 3.0, 4.0),
          _ix(L(5), "STR.FORMWORK", "m2", eid=f"FW:{L(1)}:FACES")]
    recs = {L(1): _rec("depth D-04"), L(2): _rec("D-04 width"), L(3): _rec("size D-44"),
            L(4): _rec("band D-NX1"), L(5): _rec("faces held")}
    c = R.census(ix, recs, NAMED, ITEMS)
    it1 = c["per_item"]["1"]
    # item 1: L1, L2 and the dependent formwork L5 sole; L3 (D-44 in items 1 and 3) shared, never sole
    assert it1["sole_line_ids"] == [L(1), L(2), L(5)] and it1["shared_line_ids"] == [L(3)]
    m3 = {r["unit"]: r for r in it1["sole"] if r["item_code"] == "STR.CONC.BEAM"}["m3"]
    assert (m3["range"], m3["range_low"], m3["range_high"], m3["at_least"], m3["at_least_sum"]) == (1, 1.0, 2.0, 1, 0.5)
    assert c["per_item"]["3"]["sole_lines"] == 0 and c["per_item"]["3"]["shared_lines"] == 1
    assert c["per_item"]["9"]["sole"][0]["unit"] == "m2"                    # units never mixed into m3
    assert c["assignment"][L(5)]["dependent"] and c["assignment"][L(5)]["bucket"] == "D-04"
    assert c["unlisted_d_ids"] == {}


def test_adverse_blank_never_zero_one_sided_never_closed_and_units_apart():
    ix = [_ix(L(1), "STR.CONC.STAIR", "m3"), _ix(L(2), "STR.CONC.STAIR", "m3", 0.4, None),
          _ix(L(3), "STR.REBAR", "kg", 10.0, 12.0), _ix(L(4), "STR.CONC.STAIR", "m3", 1.0, 1.5)]
    recs = {L(n): _rec("D-77 riser") for n in (1, 2, 3, 4)}
    c = R.census(ix, recs, NAMED, ITEMS)
    rows = {(r["item_code"], r["unit"]): r for r in c["per_d_id"]["D-77"]["sole"]}
    st = rows[("STR.CONC.STAIR", "m3")]
    assert st["blank"] == 1 and st["at_least"] == 1 and st["range"] == 1
    assert st["range_low"] == 1.0 and st["range_high"] == 1.5                 # the AT_LEAST 0.4 is not in the range
    assert st["at_least_sum"] == 0.4 and rows[("STR.REBAR", "kg")]["range_high"] == 12.0   # kg apart from m3
    assert c["unlisted_d_ids"] == {"D-77": [L(1), L(2), L(3), L(4)]}          # an unlisted D-id is reported, not dropped
    with pytest.raises(AssertionError):
        R.census(ix + [ix[0]], recs)


def test_version_steps_reconcile_with_zero_residual():
    def ver(rows, recs):
        c = R.census(rows, recs, NAMED, ITEMS)
        return {r["line_id"]: r for r in rows}, c["assignment"]
    v1 = ver([_ix(L(1), "X", "m3"), _ix(L(2), "X", "m3", 1.0, 2.0)], {L(1): _rec("D-04"), L(2): _rec("D-16")})
    # step 2: L1 released, L2 moves to another item, L3 added
    v2 = ver([_ix(L(1), "X", "m3", cls="RELEASED"), _ix(L(2), "X", "m3", 1.0, 2.0), _ix(L(3), "Y", "m2")],
             {L(1): _rec(), L(2): _rec("D-04"), L(3): _rec("D-NX1")})
    # step 3: L3 removed; L2 bound narrows (same bucket: a state change, not a bucket move)
    v3 = ver([_ix(L(1), "X", "m3", cls="RELEASED"), _ix(L(2), "X", "m3", 1.2, 2.0)], {L(1): _rec(), L(2): _rec("D-04")})
    chain = [("a", *v1), ("b", *v2), ("c", *v3)]
    tr = R.transitions(chain)
    assert [s["step"] for s in tr[L(3)]] == ["a->b", "b->c"] and [s["step"] for s in tr[L(2)]] == ["a->b", "b->c"]
    d = R.bucket_delta(v1[1], v3[1], tr)
    assert d["D-04"] == {"first": 1, "last": 1, "in": {"a->b": 1}, "out": {"a->b": 1}, "residual": 0}
    assert d["D-16"]["out"] == {"a->b": 1} and d["D-NX1"] == {"first": 0, "last": 0, "in": {"a->b": 1},
                                                             "out": {"b->c": 1}, "residual": 0}
    assert all(v["residual"] == 0 for v in d.values())


def test_the_runner_never_reads_a_list_id_that_is_a_drawing_mark():
    sys.path.insert(0, str(ROOT / "research" / "agents_t755"))
    import t755_census as C
    named_in_items = {d for ds in C.ITEMS.values() for d in ds if not d[2:].isdigit()}
    assert set(C.NAMED) | set(C.UNREADABLE) == named_in_items
    assert "D-GF-07" in C.UNREADABLE and "D-GF-07" not in C.NAMED
    # a door mark of the D-<floor>-nn shape in a cause text never lands in a DESIGNER bucket
    rec = _rec("D-GF-07: engine door schedule")
    assert R.classify_own(rec, C.NAMED)["kind"] == "NAMED_TEXT"


# ---- R-T755-1 v2: live cause only (Gate A r1 fault F-V755-1) -------------------------------------------------------

def _corrected(rfi_q, notes, old, new, basis=None):
    rec = {"rfi": {"question": rfi_q}, "notes": notes,
           "calculation": {"inputs": {"some_version_key": {"piece": "CAUSE_TEXT", "action": "CAUSE_TEXT",
                                                           "old": old, "new": new}}}}
    if basis is not None:
        rec["bounded_range"] = {"low": 1.0, "high": 2.0, "basis": basis}
    return rec


def test_normal_live_cause_after_a_correction_lands_in_one_bucket():
    rec = _corrected("column size not printed (D-66 (RFI-X20))", "column held",
                     "D-91", "D-66 (RFI-X20)", basis="size D-66")
    c = R.classify_own(rec, NAMED)
    assert (c["kind"], c["bucket"]) == ("DESIGNER", "D-66") and "retired_hits" not in c
    # a line with no correction record is read exactly as R-T716-1
    plain = _rec("D-66 and D-91", "note")
    assert R.classify_own(plain, NAMED)["bucket"] == R.R.classify_own(plain)["bucket"] == "D-66+D-91"


def test_adverse_a_retired_old_id_left_in_history_or_superseded_text_is_ignored():
    notes = ("designer item D-91 (superseded source text) | V3.0.x: cause text 'D-91' -> 'D-66 (RFI-X20)' "
             "(retarget); no figure moves")
    rec = _corrected("column size not printed (D-66 (RFI-X20))", notes, "D-91", "D-66 (RFI-X20)")
    c = R.classify_own(rec, NAMED)
    assert c["bucket"] == "D-66" and c["retired_hits"] == ["D-91"]          # never 'D-66+D-91'
    # dependent formwork follows the host's LIVE bucket, never the retired one
    ix = [_ix(L(1), "STR.CONC.COLUMN", "m3", 0.36, 0.45), _ix(L(2), "STR.FORMWORK", "m2", eid=f"FW:{L(1)}:SIDES")]
    cen = R.census(ix, {L(1): rec, L(2): _rec(None, "sides held")}, NAMED, {"D-66": ["3"], "D-91": ["3", "6"]})
    assert cen["assignment"][L(2)]["bucket"] == "D-66" and cen["assignment"][L(2)]["dependent"]
    assert "6" not in cen["per_item"] and cen["per_item"]["3"]["sole_lines"] == 2
    # a retired id that a LIVE field still prints stays (it was not retired from the live cause)
    keep = _corrected("lift wall D-91 and D-66", notes, "D-91", "D-66 (RFI-X20)")
    assert R.classify_own(keep, NAMED)["bucket"] == "D-66+D-91"
    keep_b = _corrected("held", notes, "D-91", "D-66", basis="D-91 lift raft")
    assert R.classify_own(keep_b, NAMED)["bucket"] == "D-91"                 # live = rfi + basis only
    # notes of a cause-rewritten line are history: an id printed only there never reaches a bucket
    hist = _corrected("held: no face figure", "superseded source D-910 and D-9", "D-91", "D-66")
    c = R.classify_own(hist, NAMED)
    assert c["kind"] == "NAMED_TEXT" and c["retired_hits"] == ["D-09", "D-910"]


def test_adverse_a_restatement_superseded_by_a_later_rewrite_is_history():
    # V3.0.46-like RESTATE named D-63 + RFI-S09 in rfi and notes; a later package rewrote rfi.question to D-43 only
    rec = {"rfi": {"question": "DESIGNER ITEM D-43 (upper end open: supplier pit depth)"},
           "notes": "added HELD BLANK | V3.0.x: held reason restated to name every fact (pit depth (L-1 / D-63); "
                    "build-up (RFI-S09)); quantity unchanged",
           "calculation": {"inputs": {"k46": {"piece": "HELD_REASON", "action": "RESTATE",
                                              "facts": ["pit depth (L-1 / D-63)", "build-up (RFI-S09)"]},
                                      "k73": {"piece": "CONC_SIDE", "action": "AT_LEAST"}}}}
    c = R.classify_own(rec, NAMED)
    assert c["bucket"] == "D-43" and c["retired_hits"] == ["D-63", "RFI-S09"]
    # the same restatement still LIVE in rfi.question (no later rewrite): both ids read
    live = dict(rec, rfi={"question": "every fact this quantity depends on: pit depth (L-1 / D-63); was: (D-43)"})
    assert R.classify_own(live, NAMED)["bucket"] == "D-43+D-63"
