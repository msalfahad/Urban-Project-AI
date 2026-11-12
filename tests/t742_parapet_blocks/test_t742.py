"""T-742: B9-05 parapet block walls (research/agents_t742, R-T742-1..3). Synthetic roof "P742" by hand (not the training
villa), adverse cases, then the development villa from merged repository files only (no private input needed)."""
from __future__ import annotations

import json
import subprocess
import sys
from decimal import Decimal
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t742"))
import t742_rules as R  # noqa: E402

# ---- roof "P742" (hand) ---------------------------------------------------------------------------------------------
# A U-shaped parapet on a 6.00 x 4.00 roof edge, t 0.20; the fourth side abuts a higher wall (square ends there).
#   R1 6.00 side: outer 6.00, inner 5.60 (two convex corners)  -> centreline 5.80
#   R2 4.00 side: outer 4.00, inner 3.80 (one convex corner)   -> centreline 3.90
#   R3 4.00 side: as R2                                        -> centreline 3.90, height NOT printed: HELD 0.90..1.10
# Corner counted once: centrelines 13.60; outer faces 14.00; corner term (0.40 + 0.20 + 0.20) / 2 = 0.40 = 14.00 - 13.60.
# Keyed detail: BLOCK from the slab finish (no upstand), printed cap 0.10, heights above finish 1.00 (R1, R2).
#   block height 1.00 - 0.10 = 0.90: R1 5.80 x 0.90 = 5.22; R2 3.90 x 0.90 = 3.51; R3 3.90 x (0.80 .. 1.00) = 3.12 .. 3.90
#   line HELD 11.85 .. 12.63 m2; m3 x 0.20 = 2.37 .. 2.526; black block 12.5 / m2 -> 148.125 .. 157.875 (waste apart).
ITEM = "P742 A-501: R3 parapet height not printed (designer item 7)"


def run(rid, L, h, **kw):
    r = {"id": rid, "centreline_m": L, "h_above_finish_m": h, "t_m": "0.20", "material": "BLOCK",
         "upstand_above_slab_top_m": None, "cap_m": "0.10", "openings_m2": [], "designer_item": None,
         "block_type": "BLACK"}
    r.update(kw)
    return r


def runs():
    return [run("R1", "5.80", "1.00"), run("R2", "3.90", "1.00"),
            run("R3", "3.90", ("0.90", "1.10"), designer_item=ITEM)]


def test_normal_measured_runs_by_hand():
    a = R.block_body(run("R1", "5.80", "1.00"))
    assert a["status"] == "MEASURED" and a["net_m2"] == (Decimal("5.220000"),) * 2
    assert a["m3"] == (Decimal("1.044000"),) * 2 and a["block_height_m"] == (Decimal("0.900000"),) * 2
    assert a["procurement_blocks"]["count"] == (Decimal("65.250000"),) * 2


def test_family_line_three_runs_one_held():
    f = R.family_line("P742-ROOF", runs())
    assert f["status"] == "HELD"
    assert f["net_m2"] == (Decimal("11.850000"), Decimal("12.630000"))
    assert f["m3"] == (Decimal("2.370000"), Decimal("2.526000"))
    r3 = f["runs"][2]
    assert r3["status"] == "HELD" and r3["net_m2"] == (Decimal("3.120000"), Decimal("3.900000"))
    assert r3["procurement_blocks"]["status"] == "HELD"
    assert sum(r["procurement_blocks"]["count"][1] for r in f["runs"]) == Decimal("157.875000")


def test_corner_counted_once_lengths_close():
    rr = [{"outer_m": "6.00", "inner_m": "5.60"}, {"outer_m": "4.00", "inner_m": "3.80"},
          {"outer_m": "4.00", "inner_m": "3.80"}]
    c = R.reconcile_lengths(rr, "14.00")
    assert c["centreline_sum_m"] == Decimal("13.600000") and c["corner_term_m"] == Decimal("0.400000")
    assert c["closes"] is True
    # mirror / reversed run order does not move it
    assert R.reconcile_lengths(list(reversed(rr)), "14.00") == c
    # a face trade that counted the corner square twice (outer + 0.20) does not close
    assert R.reconcile_lengths(rr, "14.20")["closes"] is False


def test_upstand_datum_and_opening():
    # P1-type: RC upstand 0.30 above the slab top, b_edge 0.10 printed -> masonry starts 0.20 above finish
    a = R.block_body(run("R1", "5.80", "1.00", upstand_above_slab_top_m="0.30", b_edge_m="0.10"))
    assert a["block_height_m"] == (Decimal("0.700000"),) * 2 and a["net_m2"] == (Decimal("4.060000"),) * 2
    # a full opening (Q-73) of 0.60 m2 in R1
    b = R.block_body(run("R1", "5.80", "1.00", openings_m2=["0.60"]))
    assert b["net_m2"] == (Decimal("4.620000"),) * 2


def test_rc_run_never_in_b9_and_unkeyed_keeps_rc_reading():
    a = R.block_body(run("R1", "5.80", "1.00", material="RC"))
    assert a["status"] == "NOT_APPLICABLE" and a["net_m2"] is None
    u = R.block_body(run("R1", "5.80", "1.00", material="UNKEYED", designer_item=ITEM))
    assert u["status"] == "HELD" and u["net_m2"] == (Decimal("0.000000"), Decimal("5.220000"))
    # all runs RC -> the family line is NOT_APPLICABLE, never a measured 0
    f = R.family_line("X", [run("R1", "5.80", "1.00", material="RC")])
    assert f["status"] == "NOT_APPLICABLE" and f["net_m2"] is None


@pytest.mark.parametrize("bad", [
    {"h_above_finish_m": None},                       # missing height: never defaulted
    {"h_above_finish_m": 1.0},                        # float refused
    {"h_above_finish_m": "1000"},                     # millimetres refused
    {"material": "BRICK?"},                           # unknown material
    {"h_above_finish_m": ("0.90", "1.10")},           # HELD without a named designer item
    {"h_above_finish_m": "0.05"},                     # no masonry under the cap
    {"centreline_m": ("4.0", "3.0")},                 # inverted interval
    {"upstand_above_slab_top_m": "0.30"},             # an upstand needs its b_edge (none given)
])
def test_adverse_refused(bad):
    with pytest.raises(R.RuleError):
        R.block_body(run("R1", "5.80", "1.00", **bad))


def test_duplicate_run_and_census_status():
    with pytest.raises(R.RuleError):
        R.family_line("X", [run("R1", "5.80", "1.00"), run("R1", "5.80", "1.00")])
    assert R.census_status("6.00", "6.00", "5.60", "5.60") == "DRAWN"
    assert R.census_status("6.00", "5.00", "5.60", "5.60") == "PARTLY_DRAWN"
    assert R.census_status("6.00", "0", "0", "5.60") == "NOT_ON_ROOF_PLAN"
    assert R.procurement(None, (Decimal(1), Decimal(1)), False)["status"] == "HELD"


# ---- the development villa (merged files only) ----------------------------------------------------------------------
OUT = ROOT / "research" / "agents_t742" / "out" / "T742_PARAPET_BLOCKS.json"


def test_alsenan_rebuild_byte_equal():
    p = subprocess.run([sys.executable, "-I", str(ROOT / "research/agents_t742/t742_alsenan.py"), "--check"],
                       capture_output=True, text=True)
    assert p.returncode == 0, p.stdout + p.stderr


def test_alsenan_figures():
    d = json.loads(OUT.read_text(encoding="utf-8"))
    L = d["family_lines"]
    assert set(L) == {"ANNEX", "GF", "1F", "2F"} and all(v["status"] == "HELD" for v in L.values())
    assert d["total_net_m2"] == "0.000000 .. 101.464223"          # = T-550 engine face above finish 101.4642
    assert len(d["runs"]) == 25 and len({(r["chain"], r["run"]) for r in d["runs"]}) == 25
    rc = d["length_reconciliation"]
    for ch in ("ANNEX", "GF", "2F"):
        assert rc[ch]["closes"] is True
    assert rc["2F"]["corner_term_m"] == "0.750000"
    assert rc["1F"]["nw_group"]["difference_m"] == rc["1F"]["nw_group"]["v3023_minus_t311_m"] == "-0.443500"
    assert d["freelancer"]["his_total_m2"] == "172.930000"


def test_census_holds_no_coordinate():
    c = json.loads((ROOT / "research/agents_t742/in/T742_CENSUS.json").read_text(encoding="utf-8"))
    txt = json.dumps(c)
    assert '"a"' not in txt and '"b"' not in txt and '"c"' not in txt
    for r in c["runs"]:
        for h in r["outer_handles"] + r["inner_handles"]:
            assert set(h) == {"handle", "layer", "overlap_m"}
