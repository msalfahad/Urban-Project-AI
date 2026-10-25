"""T-295 Alsenan ceiling face-to-line ledger from committed inputs only (T-283 export, T-281 ledger, the extracted
V3.0.15 ceiling lines). Rebuilds without writing and pins the results (development villa; not an accuracy claim)."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "research" / "agents_t295"
sys.path.insert(0, str(HERE))
import t295_alsenan as A  # noqa: E402
import ceiling_line_ledger as R  # noqa: E402

B = A.build()
F = A.outputs(B)
S = json.loads(F["summary.json"])
ROWS = B["rows"]


def row(fid):
    return next(r for r in ROWS if r["face_id"] == fid)


def test_committed_outputs_reproduce_byte_for_byte():
    for name, text in F.items():
        assert (HERE / name).read_text(encoding="utf-8") == text, name


def test_candidate_is_the_v3015_gate_b_file_and_every_ceiling_line_once():
    c = B["candidate"]
    assert c["candidate"] == "ARCH_TAKEOFF_V3.0.15"
    assert c["candidate_lines_csv_sha256"].startswith("a4dc01dd")
    ids = [l["line_id"] for l in B["lines"]]
    assert len(ids) == len(set(ids)) == 36
    keyed = {x for c in B["compare"] for x in c["lines"]}
    un = {l["line_id"] for l in B["unmatched_lines"]}
    assert keyed | un == set(ids) and not keyed & un
    # the five unmatched lines are the exterior soffits over outside air (T-121 / T-127), listed with that reason
    assert sorted(l["element_id"] for l in B["unmatched_lines"]) == [
        "SOFFIT:1F:PL-04", "SOFFIT:1F:PL-05", "SOFFIT:GF:PL-01", "SOFFIT:GF:PL-02", "SOFFIT:GF:PL-03"]
    assert sum(l["measured_net"] for l in B["unmatched_lines"]) == pytest.approx(44.446, abs=1e-6)
    assert all("exterior soffit" in v["reason"] for v in S["unmatched_lines"].values())
    assert all("POSSIBLE OVERLAP" in v["reason"] for v in S["unmatched_lines"].values()
               if v["element_id"].startswith("SOFFIT:GF"))


def test_every_face_once_one_owner_and_closures_zero():
    fids = [r["face_id"] for r in ROWS]
    assert len(fids) == len(set(fids))
    R.one_owner(B["faces"])
    assert all(abs(v) <= R.TOL for v in B["closure"].values())
    assert set(B["closure"]) == set(B["pieces"]) and len(B["pieces"]) == 39
    for k, v in S["source_closure"].items():
        assert abs(v["residual"]) <= R.TOL, k
    assert S["max_abs_line_remainder_m2"] <= 0.001          # GF-RC99C2A chord 0.0009 of the split face


def test_status_totals_carry_the_merged_ledgers():
    t = S["by_owner_status"]
    assert t["DECOR / DRAWING-CONFIRMED"]["carried_m2"] == pytest.approx(361.2287 + 0.777392, abs=1e-4)
    assert t["BULKHEAD / ASSUMED — OWNER-APPROVED"]["carried_m2"] == pytest.approx(27.9345, abs=1e-4)
    assert t["DOME / HELD"]["carried_m2"] is None and t["DOME / HELD"]["plan_m2"] == pytest.approx(30.718, abs=2e-4)
    for k, v in t.items():
        if "/ HELD" in k or "/ UNKNOWN" in k:
            assert v["carried_m2"] is None, k


def test_checker_one_owner_rulings_applied():
    # 0.777392 north of riser 315: decor (T-281 RIGHT), in the GF-RC99C2A line
    assert row("GF-RC99C2A/open|slab-n315")["owner"] == R.DECOR
    assert row("GF-RC99C2A/open|slab-n315")["line_id"] == "L-eb3be58fc760b39f0e38"
    # the flight under the bands: one plan area, carried ONCE in the stair-soffit HELD rows; T-281's member rows are an
    # alternative listed outside every total
    b = row("GF-RC99C2A/open|beyond")
    assert b["owner"] == R.STAIR_SOFFIT and b["status"] == R.HELD and b["carried"] is None
    assert any(a["qty"] == 1.760625 for a in B["alternatives"])
    # the 1F 0.1725 is the B23 underside over the stair foot: ceiling trade, HELD, not a stair soffit
    f = row("1F-R78C367|b23-foot")
    assert f["owner"] == R.HELD_CEILING and f["status"] == R.HELD and f["plan_m2"] == pytest.approx(0.1725)
    assert row("GF-RC99C2A/open|lw-strip")["owner"] == R.VOID


def test_stair_soffits_held_blank_where_held_ranges_never_summed():
    for r in ROWS:
        if r["owner"] == R.STAIR_SOFFIT and r["status"] != R.DC:
            assert r["carried"] is None and r["held_item"]
    ms1l = row("ST01-MS1-L")
    assert ms1l["range"][0] < ms1l["range"][1] and ms1l["carried"] is None
    assert row("ST01-MS1-LD")["carried"] == pytest.approx(1.44)        # O = D, measured
    assert row("ST01-MS1-U")["carried"] is None                        # O 4.255527 vs D 4.248365: both shown
    with pytest.raises(R.LedgerError, match="^HELD_AS_ZERO"):
        R.total([r for r in ROWS if r["owner"] == R.STAIR_SOFFIT], R.HELD)


def test_line_states_and_bindings_carried():
    lines = {l["line_id"]: l for l in B["lines"]}
    # the GF stair room's only ceiling line is BLOCKED: its 'before' is BLANK, the ST-01 MS1 soffit pieces bind to it
    gfs = "L-2175a965bb7c48a50e6c"
    assert lines[gfs]["evidence_state"] == "BLOCKED_RFI" and lines[gfs]["measured_net"] is None
    assert row("ST01-MS1-U")["line_id"] == gfs and row("GF-R31F8AE|top")["line_id"] == gfs
    # the 1F living's two lines (floor face less its void + the double-height ceiling over it): a LINE GROUP
    g = row("1F-R78C367|decor")
    assert g["line_group"] and g["binding"].startswith("LINE GROUP")
    # VOID and DOME faces in no line
    for r in ROWS:
        if r["owner"] in (R.VOID, R.DOME):
            assert r.get("line_id") is None and r.get("line_group") is None


def test_no_line_faces_named_with_the_line_that_books_them():
    nl = S["no_line_faces"]
    assert nl["1F-RFFE7AF|decor"] is None             # dressing 2.970 m2: the candidate has no ceiling line for it
    assert nl["GF-RC99C2A/open|st02-soffit"] == "L-eb3be58fc760b39f0e38"
    for k in ("ST01-MS2-L", "ST01-MS2-U"):
        assert " + " in nl[k]                          # booked today in the 1F living line group


def test_villa_reconciliation_named_parts_close():
    v = S["villa_reconciliation_m2"]
    assert v["engine_FIN_CEILING_with_quantity"] == pytest.approx(403.162928, abs=1e-6)   # released FIN.CEILING
    assert v["identity_residual"] == pytest.approx(0.0, abs=1e-6)
    assert v["decor_total"] == pytest.approx(362.006092, abs=1e-6)
    assert v["decor_in_BLOCKED_lines (engine BLANK)"] == pytest.approx(5.6258)
    assert v["decor_in_no_candidate_line"] == pytest.approx(2.970)
    assert v["engine_minus_decor_total"] == pytest.approx(41.156836, abs=1e-6)


def test_no_coordinates_or_names_committed():
    txt = "".join(F.values()) + (HERE / "CANDIDATE_V3015_CEILING_LINES.json").read_text(encoding="utf-8")
    assert not re.search(r"\b\d{5,}\.\d+\b", txt)      # no drawing coordinates
    assert "room_name" not in txt
