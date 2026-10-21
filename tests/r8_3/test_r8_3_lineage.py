"""R8.3 §5-§7 — block-lineage reconciliation under ONE identity contract.

R8.2 compared INSERT -> block record with `insert_blocks_b.get(ins)`: a truncated D1 INSERT
was silently skipped, and a truncated D1 block record was reported as a false conflict.
"""

from __future__ import annotations

import pytest

from engine.source import reconcile as R
from engine.source.realised import Lineage, RealisedGeometry, RealisedSegment

T = 10388                      # a 16-bit value
FULL = str(0x10000 + T)        # the 3-byte handle whose low bits it is
TRUNC = f"{T}+3B"              # how D1 prints it


def lin(a, b):
    r = R.reconcile(RealisedGeometry(), RealisedGeometry(), insert_blocks_a=a, insert_blocks_b=b)
    return r, [x for x in r["items"] if x["field_class"] == "BLOCK_LINEAGE"]


def outcomes(rows):
    return sorted(x["outcome"] for x in rows)


def test_1_exact_insert_and_exact_record():
    r, rows = lin({"7": "3"}, {"7": "3"})
    assert outcomes(rows) == ["PASS"] and rows[0]["basis"] == "SOURCE_HANDLE" and r["verdict"] == R.PASS


def test_2_truncated_d1_insert_matches_full_d2_insert():
    r, rows = lin({TRUNC: "3"}, {FULL: "3"})
    assert outcomes(rows) == ["PASS"] and rows[0]["basis"] == "TRUNCATED_HANDLE_LOW_BITS"
    assert r["lineage_bases"] == {"TRUNCATED_HANDLE_LOW_BITS": 1}


def test_3_exact_insert_with_truncated_d1_block_record():
    r, rows = lin({"7": TRUNC}, {"7": FULL})
    assert outcomes(rows) == ["PASS"] and rows[0]["basis"] == "TRUNCATED_HANDLE_LOW_BITS" and r["verdict"] == R.PASS


def test_4_truncated_insert_and_truncated_record():
    r, rows = lin({TRUNC: f"{T + 1}+3B"}, {FULL: str(0x10000 + T + 1)})
    assert outcomes(rows) == ["PASS"] and r["verdict"] == R.PASS


def test_5_ambiguous_low_bit_insert_match():
    """Two full handles share the low bits (0x1xxxx and 0x2xxxx): never guessed."""
    r, rows = lin({TRUNC: "3"}, {FULL: "3", str(0x20000 + T): "3"})
    assert "AMBIGUOUS_INSERT_LINEAGE" in outcomes(rows) and r["verdict"] == R.BLOCK


def test_6_ambiguous_low_bit_block_record_match():
    r, rows = lin({"7": TRUNC, "8": "4"}, {"7": FULL, "8": str(0x20000 + T)})
    assert outcomes(rows)[0] == "AMBIGUOUS_BLOCK_RECORD_LINEAGE" and r["verdict"] == R.BLOCK


def test_7_missing_k2_insert_lineage_is_reported_not_skipped():
    r, rows = lin({"7": "3", "9": "3"}, {"7": "3"})
    assert outcomes(rows) == ["PASS", "UNMATCHED_INSERT_LINEAGE"] and r["verdict"] == R.BLOCK
    r, rows = lin({"7": "3"}, {"7": "3", "11": "3"})                   # and the other side too
    assert "UNMATCHED_INSERT_LINEAGE" in outcomes(rows) and r["verdict"] == R.BLOCK


def test_8_same_block_name_different_record_handles_is_a_conflict():
    r, rows = lin({"7": {"record": "3", "name": "DOOR 90"}}, {"7": {"record": "4", "name": "DOOR 90"}})
    assert outcomes(rows) == ["BLOCK_LINEAGE_CONFLICT"] and r["verdict"] == R.BLOCK


def test_9_different_names_same_record_identity_passes():
    r, rows = lin({"7": {"record": "3", "name": "*U12"}}, {"7": {"record": "3", "name": "*U3"}})
    assert outcomes(rows) == ["PASS"] and r["verdict"] == R.PASS


def _seg(h, path):
    return RealisedSegment((0, 0), (1, 0), Lineage(f"X:{h}", str(h), path, "0", "LINE"))


def test_10_nested_instance_path_with_truncated_handles():
    a, b = RealisedGeometry(), RealisedGeometry()
    a.segments.append(_seg("5", (TRUNC, f"{T + 7}+3B")))
    b.segments.append(_seg("5", (FULL, str(0x10000 + T + 7))))
    r = R.reconcile(a, b, insert_blocks_a={TRUNC: "3", f"{T + 7}+3B": "4"},
                    insert_blocks_b={FULL: "3", str(0x10000 + T + 7): "4"})
    assert r["verdict"] == R.PASS
    assert r["correlation_bases"] == {"TRUNCATED_HANDLE_LOW_BITS": 1}
    assert r["lineage_outcomes"] == {"PASS": 2}


def test_lineage_needs_both_sides():
    with pytest.raises(ValueError):
        R.reconcile(RealisedGeometry(), RealisedGeometry(), insert_blocks_a={"7": "3"})


def test_every_insert_yields_exactly_one_lineage_row():
    a = {"1": "3", TRUNC: "3", "9": "5"}
    b = {"1": "3", FULL: "3", "12": "5"}
    _, rows = lin(a, b)
    assert len(rows) == 4                      # 2 PASS + A-only 9 + B-only 12


def test_names_never_enter_identity():
    """A name identical on both sides cannot rescue different records (§7)."""
    assert R.handle_basis("DOOR", "DOOR") == "SOURCE_HANDLE"       # the function compares handles only;
    _, rows = lin({"7": {"record": "3", "name": "X"}}, {"7": {"record": "3", "name": "Y"}})
    assert rows[0]["name_a"] == "X" and rows[0]["name_b"] == "Y" and rows[0]["outcome"] == "PASS"


# ---------------------------------------------------------------- mutation (§6)

def test_mutation_disabling_truncated_lineage_correlation_is_caught(monkeypatch):
    """With low-bit correlation disabled, the truncated-INSERT case can no longer pass: the
    lineage tests above would fail. This guards the fix from silent regression."""
    monkeypatch.setattr(R, "_low_bits_match", lambda x, y: False)
    r, rows = lin({TRUNC: "3"}, {FULL: "3"})
    assert r["verdict"] == R.BLOCK and "UNMATCHED_INSERT_LINEAGE" in outcomes(rows)
    r, rows = lin({"7": TRUNC}, {"7": FULL})
    assert outcomes(rows) == ["BLOCK_LINEAGE_CONFLICT"]


def test_mutation_raw_string_lookup_is_what_r8_2_did(monkeypatch):
    """Re-create the R8.2 behaviour and show it silently skipped the truncated INSERT."""
    def r82(a, b):
        rows = []
        for ins, blk in a.items():
            other = b.get(ins)
            if other is not None and other != blk:
                rows.append("CONFLICT")
        return rows
    assert r82({TRUNC: "3"}, {FULL: "3"}) == []            # skipped: nothing compared, nothing reported
    assert r82({"7": TRUNC}, {"7": FULL}) == ["CONFLICT"]   # false conflict
    assert outcomes(lin({TRUNC: "3"}, {FULL: "3"})[1]) == ["PASS"]
    assert outcomes(lin({"7": TRUNC}, {"7": FULL})[1]) == ["PASS"]
