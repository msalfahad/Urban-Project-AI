"""T-638: formwork hold census (R-T638-1). Synthetic villa "V638" (not the training villa) by hand with adverse cases
(face against blinding, formwork from a HELD volume, missing dimension, mm read as m, mirror / order of framing
members); then the development villa: the 370 HELD-blank B10-13 STR.FORMWORK lines of the T-630 dry run classed, with
fix rows (repository files only)."""
from __future__ import annotations

import os
import sys
from decimal import Decimal
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t638"))
import t638_rules as R  # noqa: E402
import t638_alsenan as A  # noqa: E402

D = Decimal

# ---- villa "V638" (hand) --------------------------------------------------------------------------------------------
# Beam B1 0.20 x 0.50 (overall depth) between two columns, clear span 4.00 face to face, under a 0.15 slab on both
# sides:  soffit 0.20 x 4.00 = 0.800; sides 2 x 4.00 x (0.50 - 0.15) = 2.800; total 3.600 m2.
# Column C1 0.30 x 0.30, storey 3.20 slab top to slab top, B1 frames into one face:
#   shaft 1.20 x (3.20 - 0.50) = 3.240; joint 1.20 x (0.50 - 0.15) - 0.20 x 0.35 = 0.420 - 0.070 = 0.350;
#   total 3.590 = 1.20 x (3.20 - 0.15) - 0.070 (check).
# Column C2 0.30 x 0.30 with B1 (0.20 x 0.50) and B2 (0.20 x 0.40) framing in:
#   D_ctrl 0.50: shaft 3.240; joint 0.420 - 0.070 - 0.20 x 0.25 = 0.300; total 3.540.


def test_v638_beam_by_hand():
    r = R.beam_forms("0.20", "0.50", "0.15", "4.00")
    assert (r["soffit"], r["sides"], r["total"]) == (D("0.8"), D("2.8"), D("3.6"))


def test_v638_beam_side_on_masonry_has_no_form():
    r = R.beam_forms("0.20", "0.50", "0.15", "4.00", side_contacts=("FORM", "MASONRY"))
    assert (r["sides"], r["total"]) == (D("1.4"), D("2.2"))


def test_v638_column_by_hand():
    r = R.column_forms("0.30", "0.30", "3.20", "0.15", [("0.20", "0.50")])
    assert (r["shaft"], r["joint"], r["total"], r["d_ctrl"]) == (D("3.24"), D("0.35"), D("3.59"), D("0.5"))
    assert r["total"] == R.q(D("1.20") * (D("3.20") - D("0.15")) - D("0.070"))


def test_v638_two_framing_members_order_and_mirror_invariant():
    a = R.column_forms("0.30", "0.30", "3.20", "0.15", [("0.20", "0.50"), ("0.20", "0.40")])
    b = R.column_forms("0.30", "0.30", "3.20", "0.15", [("0.20", "0.40"), ("0.20", "0.50")])
    assert a == b and a["joint"] == D("0.3") and a["total"] == D("3.54")
    rot = R.column_forms("0.40", "0.20", "3.20", "0.15", [("0.20", "0.50")])     # a x c swapped (rotation 90 deg)
    assert rot == R.column_forms("0.20", "0.40", "3.20", "0.15", [("0.20", "0.50")])
    assert rot["total"] == D("3.59")                     # 1.20 x 3.05 - 0.070: same perimeter as 0.30 x 0.30


def test_adverse_face_against_blinding_refused():
    with pytest.raises(R.RuleError, match="BLINDING"):
        R.beam_forms("0.20", "0.50", "0.15", "4.00", soffit_contact="BLINDING")
    with pytest.raises(R.RuleError, match="unknown"):
        R.beam_forms("0.20", "0.50", "0.15", "4.00", side_contacts=("FORM", "??"))


def test_adverse_formwork_from_held_volume_refused():
    with pytest.raises(R.RuleError, match="HELD volume"):
        R.beam_forms("0.20", "0.50", "0.15", "4.00", concrete_state="HELD")
    with pytest.raises(R.RuleError, match="HELD volume"):
        R.column_forms("0.30", "0.30", "3.20", "0.15", [], concrete_state="BLOCKED_RFI")


def test_adverse_missing_units_geometry():
    with pytest.raises(R.RuleError, match="never 0"):
        R.beam_forms("0.20", None, "0.15", "4.00")
    with pytest.raises(R.RuleError, match="mm"):
        R.beam_forms("200", "0.50", "0.15", "4.00")
    with pytest.raises(R.RuleError, match="a band"):
        R.beam_forms("0.20", "0.15", "0.15", "4.00")
    with pytest.raises(R.RuleError, match="interval"):
        R.column_forms("0.30", "0.30", "0.50", "0.15", [("0.20", "0.50")])


BLANK = dict(R.BLANK)


def entry(**kw):
    e = {"line_id": "L-x", "class": "A_FIX", "concrete_class": "RELEASED", "cause": "c",
         "faces": [{"face_id": "f", "cause": "c"}],
         "fix": {"kind": "RELEASE", "before": dict(BLANK), "open_faces": [], "companion": None,
                 "after": {"class": "RELEASED", "measured_net": "1.2"}}}
    e.update(kw)
    return e


def test_census_adverse():
    R.check_entry(entry())
    with pytest.raises(R.RuleError, match="HELD volume"):
        R.check_entry(entry(concrete_class="HELD"))
    with pytest.raises(R.RuleError, match="as 0"):
        R.check_entry(entry(fix={"kind": "RELEASE", "before": dict(BLANK), "open_faces": [], "companion": None,
                                 "after": {"class": "RELEASED", "measured_net": "0"}}))
    with pytest.raises(R.RuleError, match="companion"):
        R.check_entry(entry(fix={"kind": "RELEASE", "before": dict(BLANK), "open_faces": ["j"], "companion": None,
                                 "after": {"class": "RELEASED", "measured_net": "1"}}))
    with pytest.raises(R.RuleError, match="companion must be HELD"):
        R.check_entry(entry(fix={"kind": "RELEASE", "before": dict(BLANK), "open_faces": ["j"],
                                 "companion": {"class": "HELD", "measured_net": "0"},
                                 "after": {"class": "RELEASED", "measured_net": "1"}}))
    with pytest.raises(R.RuleError, match="named cause"):
        R.check_entry(entry(cause=" "))
    with pytest.raises(R.RuleError, match="no fix row"):
        R.check_entry(entry(**{"class": "B_HELD"}))
    with pytest.raises(R.RuleError, match="needs a fix row"):
        R.check_entry(entry(fix=None))
    with pytest.raises(R.RuleError, match="face f"):
        R.check_entry(entry(**{"class": "C_HELD", "fix": None, "faces": [{"face_id": "f", "cause": ""}]}))


# ---- development villa ----------------------------------------------------------------------------------------------

@pytest.mark.skipif(os.environ.get("URBAN_T638_WRITE") != "1", reason="writer only on request")
def test_write_outputs():
    A.write_outputs()


def test_build_reproduces_committed_output():
    b = A.build()
    assert A.dumps(b) == A.OUT_JSON.read_text(encoding="utf-8")
    assert A.render_md(b) == A.OUT_MD.read_text(encoding="utf-8")


def test_alsenan_census():
    b = A.build()
    c = b["counts"]
    assert c["lines"] == 370
    assert c["by_class"] == {"A_FIX": 54, "B_HELD": 203, "C_HELD": 113}
    assert (c["fix_rows"], c["companions"], c["released_m2"]) == (54, 4, "33.127058")
    ids = [e["line_id"] for e in b["lines"]]
    assert len(set(ids)) == 370
    by = b["fix_rows_by_element"]
    assert by["COLUMN shaft"] == {"fix_rows": 4, "released_m2": "27.002", "companions": 4}
    assert sum(D(v["released_m2"]) for k, v in by.items() if "split" in k) == D("6.125058")
    for e in b["lines"]:
        if e["class"] == "A_FIX":
            assert e["concrete_class"] == "RELEASED" and D(e["fix"]["after"]["measured_net"]) > 0
        else:
            assert "fix" not in e or not e["fix"]
        if e["element_id"].split(":")[2:3] == ["OQ10"]:
            assert e["class"] in ("B_HELD", "C_HELD")    # OQ-10 never freed: EARTH_CAST reads 0


def test_alsenan_column_shafts_by_hand():
    b = A.build()
    fr = {c["column"]: c for e in b["lines"] if e["class"] == "A_FIX" for c in e.get("checks", [])}
    assert set(fr) == {"COL-GF-01", "COL-GF-02", "COL-GF-03", "COL-GF-09"}
    assert fr["COL-GF-09"]["hand_m2"] == "9.375" and fr["COL-GF-09"]["residual_m2"] == "0"
    assert fr["COL-GF-01"]["residual_m2"] == "0.001"           # drawn-outline perimeter vs printed section, named
    held = [e for e in b["lines"] if any(c["column"] in ("COL-GF-05", "COL-GF-22") for c in e.get("checks", []))]
    assert len(held) == 2 and all(e["class"] == "B_HELD" for e in held)   # stair beside: not freed


def test_strip_d_held_never_zero():
    s = A.build()["strip_D"]
    assert s["class"] == "C_HELD" and [r["plan_m2"] for r in s["storeys"]] == ["0.865", "0.865"]
    for r in s["storeys"]:
        assert r["status"] == "HELD" and r["beside_if_slab_t_0_16"]["concrete_m3"] == "0.1384"
