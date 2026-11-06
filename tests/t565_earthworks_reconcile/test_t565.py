"""T-565: B1 earthworks reconciled against a freelancer by component (research/agents_t565, R-T565-1 .. 4).
Hand villa "E565" (not the training villa) with normal and adverse cases; then the committed development-villa tables,
checked from merged repository files (the re-read of the private concrete workbook runs only when it is present)."""
from __future__ import annotations

import json
import sys
from decimal import Decimal
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t565"))
import t565_rules as R  # noqa: E402

OUT = ROOT / "research" / "agents_t565" / "out" / "T565_EARTHWORKS_RECONCILE.json"
PRIVATE_WB = ROOT.parent / "private" / "concrete_rebar.xlsx"
D = Decimal


# ---- villa "E565" (hand) ----------------------------------------------------------------------------------------
# Pad 2.00 x 2.00 x 0.60 on a blinding 2.00 x 2.00 x 0.10; NGL 1.20 above the pad base; no working space printed.
#   excavation  2.00 x 2.00 x (1.20 + 0.10) = 5.200 m3 in situ
#   pad 2.400, blinding 0.400, neck 0.30 x 0.30 from the pad top (0.60) to NGL (1.20) = 0.054  -> displacement 2.854
#   backfill    5.200 - 2.400 - 0.400 - 0.054 = 2.346 m3 compacted (geometric)
def test_hand_pad_villa():
    v = R.pad_villa(2.00, 2.00, 0.60, 0.10, 1.20, neck_b=0.30, neck_d=0.30)
    assert v["excavation_in_situ"] == D("5.200000")
    assert v["parts"] == {"PAD": D("2.400000"), "BLINDING": D("0.400000"), "NECK": D("0.054000")}
    assert v["backfill_compacted"] == D("2.346000")
    assert v["displacement_solid"] == D("2.854000")
    assert v["excavation_in_situ"] - v["backfill_compacted"] == v["displacement_solid"]


def test_hand_pad_mirror_and_rotation_invariant():
    a = R.pad_villa(2.50, 1.60, 0.50, 0.10, 1.40, neck_b=0.30, neck_d=0.50)
    b = R.pad_villa(1.60, 2.50, 0.50, 0.10, 1.40, neck_b=0.50, neck_d=0.30)     # rotated 90 degrees / mirrored
    assert a["excavation_in_situ"] == b["excavation_in_situ"] == D("6.000000")
    assert a["backfill_compacted"] == b["backfill_compacted"] == D("3.465000")   # 6.0 - 2.0 - 0.4 - 0.135 (neck 0.15 m2 x 0.90)


def test_working_space_only_when_printed():
    neat = R.pad_villa(2.00, 2.00, 0.60, 0.10, 1.20)
    ws = R.pad_villa(2.00, 2.00, 0.60, 0.10, 1.20, working_space=0.30)
    assert neat["excavation_in_situ"] == D("5.200000")
    assert ws["excavation_in_situ"] == D("8.788000")                             # 2.60 x 2.60 x 1.30
    assert ws["backfill_compacted"] - neat["backfill_compacted"] == D("3.588000")


def test_units_mm_refused():
    with pytest.raises(ValueError, match="millimetres"):
        R.pad_villa(2000, 2000, 600, 100, 1200)


def test_bulked_against_in_place_refused():
    with pytest.raises(ValueError, match="basis mismatch"):
        R.compare(R.valued("6.24", "LOOSE"), R.valued("5.20", "IN_SITU"))
    with pytest.raises(ValueError, match="mixed bases"):
        R.total([R.valued("5.20", "IN_SITU"), R.valued("2.346", "COMPACTED")])
    with pytest.raises(ValueError, match="unit"):
        R.valued("5.2", "IN_SITU", "m2")


def test_buried_volume_deducted_twice_refused():
    with pytest.raises(ValueError, match="deducted twice"):
        R.backfill("5.20", [("PAD", "2.40"), ("BLINDING", "0.40"), ("PAD", "2.40")])
    els = {"PAD": D("2.40"), "BLINDING": D("0.40")}
    with pytest.raises(ValueError, match="deducted twice"):
        R.ownership(els, [("PAD", "Z1", "2.40"), ("PAD", "Z1", "2.40"), ("BLINDING", "Z1", "0.40")])
    with pytest.raises(ValueError, match="owned more or less than once"):       # same pad in two zones in full
        R.ownership(els, [("PAD", "Z1", "2.40"), ("PAD", "Z2", "2.40"), ("BLINDING", "Z1", "0.40")])
    with pytest.raises(ValueError, match="owned by no zone"):
        R.ownership(els, [("PAD", "Z1", "2.40")])
    with pytest.raises(ValueError, match="no line"):
        R.ownership(els, [("PAD", "Z1", "2.40"), ("BLINDING", "Z1", "0.40"), ("BEAM", "Z1", "0.1")])
    ok = R.ownership(els, [("PAD", "Z1", "2.00"), ("PAD", "Z2", "0.40"), ("BLINDING", "Z1", "0.40")])
    assert ok["per_zone"] == {"Z1": D("2.400000"), "Z2": D("0.400000")}


def test_no_row_is_never_zero():
    his = R.no_row("IN_SITU", "no row in 10 rows")
    c = R.compare(R.valued("5.20", "IN_SITU"), his)
    assert c == {"class": "NOT_COMPARABLE", "difference": None, "pct": None}
    with pytest.raises(ValueError, match="never summed"):
        R.total([R.valued("5.20", "IN_SITU"), his])
    with pytest.raises(ValueError, match="evidence"):
        R.no_row("IN_SITU", "")
    with pytest.raises(ValueError, match="never 0"):
        R.d6(None)
    st = R.not_in_scope("AREA", "31 sheets searched")
    assert R.compare(st, R.no_row("AREA", "searched"))["class"] == "AGREE_ABSENT"


def test_held_kept_apart_and_absent_parts_none():
    t = R.total([R.valued("5.2", "IN_SITU"), R.held_range("1.0", "1.5", "IN_SITU"),
                 R.held_blank("IN_SITU", "formation not printed")])
    assert (t["valued"], t["held_low"], t["held_high"], t["held_blank"]) == (D("5.2"), D("1.0"), D("1.5"), 1)
    blank = R.total([R.held_blank("IN_SITU", "densities")])
    assert blank["valued"] is None and blank["held_low"] is None and blank["held_high"] is None
    with pytest.raises(ValueError, match="names what holds it"):
        R.held_blank("IN_SITU", "")
    with pytest.raises(ValueError, match="bad held range"):
        R.held_range("2", "1", "IN_SITU")


def test_compared_difference_and_table_closure():
    c = R.compare(R.valued("5.20", "IN_SITU"), R.valued("4.00", "IN_SITU"))
    assert c["difference"] == D("1.200000") and c["pct"] == D("30.000000")
    rows = [{"v": "1.2"}, {"v": "0.3"}, {"v": "-0.5"}]
    assert R.table_closes(rows, "v", "1.0") == D("1.000000")
    with pytest.raises(AssertionError, match="does not close"):
        R.table_closes(rows, "v", "1.1")


def test_disposal_needs_a_sourced_density_ratio():
    assert R.disposal_in_situ("5.20", "2.346") is None
    assert R.disposal_in_situ("5.20", "2.346", k="1.10") is None                  # a factor with no source
    assert R.disposal_in_situ("5.20", "2.346", k="1.10", k_source="lab MDD / field") == D("2.619400")


def test_layers():
    assert R.layers("1.57", "0.15") == 11
    assert R.layers("1.50", "0.15") == 10
    assert R.layers("1.47", "0.15") == 10
    with pytest.raises(ValueError):
        R.layers("1.5", "0")


# ---- development villa (committed files only) -------------------------------------------------------------------
@pytest.fixture(scope="module")
def doc():
    import t565_alsenan as A
    return A, A.build()


def test_dev_rebuild_equals_committed(doc):
    A, d = doc
    assert A.dump(d) == OUT.read_text(encoding="utf-8")


def test_dev_family_totals(doc):
    _, d = doc
    ft = d["family_totals"]
    ex, bf, dp = ft["STR.EARTH.EXCAVATION"], ft["STR.EARTH.BACKFILL"], ft["STR.EARTH.DISPOSAL"]
    assert (ex["lines"], ex["valued"], ex["held_low"], ex["held_high"], ex["held_blank_lines"]) == \
        (12, D("225.941333"), D("8.333769"), D("9.568217"), 8)
    assert ex["valued"] == D("208.164757") + D("17.776576")
    assert (bf["lines"], bf["valued"], bf["held_low"], bf["held_high"], bf["held_blank_lines"]) == \
        (7, None, D("119.963335"), D("128.643547"), 6)
    assert (dp["lines"], dp["valued"], dp["held_low"], dp["held_blank_lines"]) == (1, None, None, 1)


def test_dev_backfill_closure(doc):
    _, d = doc
    c = d["pits_backfill_closure"]
    assert c["backfill_low"] == D("208.164757") - D("71.925255") - D("16.276167") == c["line_low"]
    assert c["backfill_high"] == D("208.164757") - D("71.925255") - D("7.595955") == c["line_high"]
    p = d["pits_verified_displacement_parts"]
    assert p == {"blinding": D("12.464956"), "underlay": D("7.542559"), "footings": D("51.917740")}


def test_dev_footings_owned_once(doc):
    _, d = doc
    f = d["ownership"]["footings"]
    assert f["valued_m3"] == D("64.304000") and f["pits_joined"] == 24 and f["valued_lines"] == 25
    z = f["per_zone"]
    assert z["Z1-PITS-24"] == f["t350r2_footings_m3"] == D("51.917740")
    assert z["Z1-POOL-INTERFACE (held, F-T350R2-2)"] == D("1.001260")      # F8 1.615967 x 0.5 + F4 0.48319 x 0.4
    assert z["Z1-PIT-FF (held blank)"] == D("11.385000")
    assert sum(z.values()) == f["valued_m3"]
    # the T-320 ledger bills the FN / F9 notch 0.042 in FN; the candidate FN line is net of it (F9 owns it)
    assert f["t320_ledger_pits_m3"] - (z["Z1-PITS-24"] + z["Z1-POOL-INTERFACE (held, F-T350R2-2)"]) == D("0.042")
    assert len(f["handle_differs"]) == 2                                   # joined by mark + position, not handle


def test_dev_blinding_split(doc):
    _, d = doc
    b = d["ownership"]["blinding"]
    assert b["line_m3"] == D("12.734438")
    assert b["per_zone"]["Z1-PITS-24"] == D("12.464956")
    assert b["per_zone"]["Z1-POOL-INTERFACE (held, under-pool band)"] == D("0.269482")
    assert D("0") < b["overlap_inside_envelope_m2"] < D("0.001")           # F8 / FN neat plans overlap once


def test_dev_straps_and_necks(doc):
    _, d = doc
    s = d["ownership"]["straps"]
    assert s["per_zone"]["Z1-PITS-24"] == D("0.179618")
    assert sum(s["per_zone"].values()) == D("1.5925") + D("1.1464") + D("0.6516")
    n = d["ownership"]["necks"]
    assert n["concrete_lines"] == 36 and n["all_concrete_lines_held"]
    assert n["necks_per_zone"] == {"Z1-PITS-24": 30, "Z1-PIT-FF": 4, "Z1-PIT-F10F": 2}
    assert n["pits_calculated_29_m3_S01"] == D("5.154000")


def test_dev_benchmark_has_no_earthworks_row(doc):
    _, d = doc
    fb = d["benchmark_search"]["freelancer"]
    assert fb["rows"] == 885 and sum(fb["per_file"].values()) == 885 and fb["hits"] == {}
    assert set(fb["per_file"]) == {"FIN", "BLK", "PNT", "RC", "ALU", "PLS"}
    w = d["benchmark_search"]["web_app"]
    assert {h["class"] for h in w["hits_read"]} == {"MATERIAL_LOAD_NOT_EARTHWORKS"}
    for c in d["components"]:
        assert c["his"] == "NO_ROW" and c["difference"] is None and c["pct"] is None
        assert c["class"] in ("NOT_COMPARABLE", "AGREE_ABSENT")
    st = [c for c in d["components"] if c["component"].startswith("B1-05")]
    assert len(st) == 1 and st[0]["engine"]["state"] == "NOT_IN_SCOPE" and st[0]["class"] == "AGREE_ABSENT"


def test_dev_committed_file_has_no_benchmark_text():
    s = OUT.read_text(encoding="utf-8")
    for w in ("شركه", "المحترم", "ملك", "description"):
        assert w not in s


@pytest.mark.skipif(not PRIVATE_WB.exists(), reason="private data not available: concrete_rebar.xlsx")
def test_private_workbook_has_no_earthworks_row():
    import t565_alsenan as A
    pc = A.private_check(PRIVATE_WB)
    assert pc["census_complete"] and pc["keyword_hits"] == 0 and len(pc["sheets"]) == 8
