"""T-777 STR.CONC.BEAM candidate vs freelancer by named cause (BEAM_COMPARE_V1, proposed).

Normal: a synthetic villa (not Alsenan) splits a per-mark difference exactly into width / depth / length; the Alsenan
candidate (V3.0.81 + T-761 / T-757 fix rows) vs his sheet closes to named causes with a residual below 1 %.
Adverse: a missing dimension, a HELD line with no figure, an unlabelled piece paired with a neighbour mark of his, and an
equal total hiding offsetting causes are all refused or exposed. Reads committed inputs only; writes nothing."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t777"))
import beam_vs_freelancer as B  # noqa: E402


# ------------------------------------------------------------------ normal (synthetic villa)
def test_split_effects_sum_exactly_any_units():
    db, dd, dl = B.split_effects(0.20, 0.50, 4.00, 0.25, 0.60, 4.40)
    assert db + dd + dl == pytest.approx(0.25 * 0.60 * 4.40 - 0.20 * 0.50 * 4.00, abs=1e-12)
    mm = B.split_effects(200, 500, 4000, 250, 600, 4400)
    assert sum(mm) / 1e9 == pytest.approx(db + dd + dl, abs=1e-12)


def test_equal_totals_with_offsetting_causes_are_exposed():
    # his beam runs through a 0.30 column (3.30 m) but omits a second labelled beam; mine stops at faces (3.00 m)
    db, dd, dl = B.split_effects(0.20, 0.50, 3.00, 0.20, 0.50, 3.30)   # his - mine on the shared mark
    shared = -(db + dd + dl)                                            # mine - his
    omitted = 0.20 * 0.50 * 0.30                                        # the labelled beam he leaves out
    assert shared + omitted == pytest.approx(0.0, abs=1e-12)            # totals agree ...
    assert dl == pytest.approx(0.03) and omitted == pytest.approx(0.03)  # ... by two named, opposite causes


def test_marks_and_continuation_rows():
    assert B.norm_mark("BCB8") == "CB8" and B.norm_mark("GCB11") == "CB11"
    assert B.norm_mark("B23 upstand") == "B23 upstand" and B.norm_mark("B23") == "B23"
    s, by = B.his_rows_resum([dict(storey="GF", mark="B4", m3=0.375), dict(storey="GF", mark=None, m3=0.3)])
    assert s == pytest.approx(0.675) and len(by[("GF", "B4")]) == 2


def test_conflict_run_takes_the_drawn_width():
    r = dict(b_drawn_m="", depth_m="0.75", length_m="7.4802", reason="schedule width 0.45 vs drawn 0.4: same kind")
    assert B.run_dims(r, 2.262872) == (0.4, 0.75, 7.4802)
    ring = dict(b_drawn_m="0.2", depth_m="0.5", length_m="", reason="")
    assert B.run_dims(ring, 0.7553)[2] == pytest.approx(7.553)


# ------------------------------------------------------------------ adverse
def test_missing_or_negative_dimension_refused():
    for bad in ((None, 0.5, 4, 0.2, 0.5, 4), (0.2, 0.5, -4, 0.2, 0.5, 4)):
        with pytest.raises(ValueError):
            B.split_effects(*bad)


def test_unlabelled_piece_never_paired_with_his_neighbour_mark():
    c = B.classify({("GF", "(unlabelled / held piece)"): 1, ("GF", "B24"): 1}, {("GF", "B24"): 1})
    assert c[("GF", "(unlabelled / held piece)")] == "ENGINE_ONLY"


def test_held_line_without_a_figure_refused():
    L = dict(lines=[dict(item_code=B.ITEM, class_="x")])
    L["lines"][0] = {"item_code": B.ITEM, "class": "HELD", "line_id": "X-1", "element_id": "HL:BEAM_LEDGER:GF:BM-GF-999",
                     "measured_net": None, "held_low": 0.1, "held_high": 0.2}
    with pytest.raises(ValueError):
        B.engine_lines(L, {}, [])


# ------------------------------------------------------------------ Alsenan pinned (development villa; no accuracy claim)
D = B.build()


def test_alsenan_totals_and_residual():
    assert D["engine_m3"] == pytest.approx(79.2437, abs=1e-4)
    assert D["freelancer_total_cell"] == pytest.approx(65.965875, abs=1e-6)
    assert D["freelancer_rows_sum"] == pytest.approx(66.093875, abs=1e-6)
    assert D["diff_m3"] == pytest.approx(13.2778, abs=1e-4)
    assert abs(D["residual_m3"]) < B.MATERIALITY * D["freelancer_total_cell"]
    assert abs(D["residual_m3"]) < 0.001


def test_alsenan_named_causes():
    c = D["causes"]
    assert c["C1_MARKS_DRAWN_NOT_IN_HIS_SHEET"] == pytest.approx(10.1225, abs=1e-4)
    assert c["C2c2_LENGTH_HIS_LONGER"] == pytest.approx(-8.3228, abs=1e-4)
    assert c["C4_UNLABELLED_PIECES_DEFAULT_DEPTH"] == pytest.approx(6.8589, abs=1e-4)
    assert c["C3_HIS_SHEET_ARITHMETIC"] == pytest.approx(0.128, abs=1e-6)
    assert abs(c["C2b_DEPTH"]) < 0.001
    assert D["verdicts"]["C2c2_LENGTH_HIS_LONGER"] == "RULE_DIFFERENCE"
    assert D["verdicts"]["C4_UNLABELLED_PIECES_DEFAULT_DEPTH"] == "UNRESOLVED"


def test_every_candidate_line_once_with_a_figure():
    ids = [x["line_id"] for x in D["lines"]]
    assert len(ids) == len(set(ids)) == 140
    assert all(x["m3"] is not None for x in D["lines"])


def test_committed_outputs_match_a_rebuild():
    import json
    js = json.dumps(D, indent=1, ensure_ascii=False, sort_keys=True) + "\n"
    assert (B.OUT / "BEAM_CAUSES.json").read_text(encoding="utf-8") == js
