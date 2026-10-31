"""T-381 DESIGNER_RFI_ROWS_LANE_A_V1: lane A designer RFI rows bound to merged evidence (R-RFI-BIND-1).

Normal case: a synthetic (non-Alsenan) villa E381 whose two rows cite a temporary ledger written by the test, with a hand
range; adverse cases: uncited row, citation not in the ledger, one fact twice, a fact an owner rule settles, ADD_TO an
unknown RFI, NEW id that exists, HELD as 0, HELD unquantified with no reason, low > high, unit missing, Arabic text, a
client term. Alsenan pins: 7 rows, every citation resolves, the committed outputs are reproduced. Read-only; writes only
to a temporary folder."""

import copy
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t381"))
import t381_rfi_rows as T  # noqa: E402

OUT = ROOT / "research" / "agents_t381"


def _villa(tmp_path):
    led = tmp_path / "research" / "e381" / "LEDGER.md"
    led.parent.mkdir(parents=True)
    led.write_text("E381 arch A-01: drawn on plan only, head NOT_DRAWN.\nbath B-01 tray NOT DIMENSIONED\n",
                   encoding="utf-8")
    base = dict(discipline="architect", own_reading=[], owner_rules_checked=["Q-55 C (doors only)"],
                why_no_rule="drawing fact", stays_held="HELD", held_reason="")
    rows = [
        dict(base, row_id="E1", fact="arch.A-01.head", verdict="ADD_TO", target="RFI-X01", part="(a)",
             question="head of A-01", citations=[("research/e381/LEDGER.md", "head NOT_DRAWN")],
             # hand: deduction bound = width 0.90 x finish height 3.00 = 2.70 m2 per face, two faces
             unlocks=["deduction faces 1 and 2"], unit="m2", low=None, high=0.90 * 3.00),
        dict(base, row_id="E2", fact="bath.B-01.tray", verdict="NEW", target="RFI-X02", part="(a)",
             question="tray size of B-01", citations=[("research/e381/LEDGER.md", "tray NOT DIMENSIONED")],
             unlocks=["tray pcs specification"], unit="pcs", low=None, high=None, held_reason="size not printed"),
    ]
    return rows, frozenset({"RFI-X01"})


def test_normal_villa_by_hand(tmp_path):
    rows, ids = _villa(tmp_path)
    assert T.validate(rows, rfi_ids=ids, root=tmp_path)
    assert rows[0]["high"] == pytest.approx(2.70)
    assert T.governed(rows[0]) == " .. 2.7 m2"
    assert T.governed(rows[1]).startswith("HELD unquantified")


@pytest.mark.parametrize("mutate, msg", [
    (lambda r: r[0].update(citations=[]), "no citation"),
    (lambda r: r[0].update(citations=[("research/e381/LEDGER.md", "head PRINTED 2.10")]), "not in"),
    (lambda r: r[0].update(citations=[("research/e381/MISSING.md", "x")]), "cited file missing"),
    (lambda r: r[1].update(fact="arch.A-01.head"), "same fact"),
    (lambda r: r[0].update(fact="shower.tanking_height"), "owner rule"),
    (lambda r: r[0].update(target="RFI-X99"), "in no RFI file"),
    (lambda r: r[1].update(target="RFI-X01"), "already exists"),
    (lambda r: r[0].update(high=0), "never 0"),
    (lambda r: r[0].update(low=0.0, high=None), "never 0"),
    (lambda r: r[1].update(held_reason=""), "without a reason"),
    (lambda r: r[0].update(low=3.0), "low > high"),
    (lambda r: r[0].update(unit=None), "unit"),
    (lambda r: r[0].update(unit="mm"), "unit"),
    (lambda r: r[0].update(owner_rules_checked=[]), "owner rule search"),
    (lambda r: r[0].update(unlocks=[]), "unlocks nothing"),
    (lambda r: r[0].update(question="head of قوس"), "Arabic"),
    (lambda r: r[0].update(verdict="SEND"), "verdict"),
])
def test_adverse_refused(tmp_path, mutate, msg):
    rows, ids = _villa(tmp_path)
    mutate(rows)
    with pytest.raises(T.RowError, match=msg):
        T.validate(rows, rfi_ids=ids, root=tmp_path)


def test_client_term_refused(tmp_path):
    rows, ids = _villa(tmp_path)
    rows[0]["question"] = "head of A-01 for client Zeta"
    with pytest.raises(T.RowError, match="client term"):
        T.validate(rows, rfi_ids=ids, root=tmp_path, client_terms=("zeta",))


def test_new_part_twice_refused(tmp_path):
    rows, ids = _villa(tmp_path)
    extra = copy.deepcopy(rows[1])
    extra.update(row_id="E3", fact="bath.B-02.tray")
    with pytest.raises(T.RowError, match="twice"):
        T.validate(rows + [extra], rfi_ids=ids, root=tmp_path)


def test_alsenan_rows_resolve_and_pins():
    assert T.validate(T.ROWS)
    assert len(T.ROWS) == 7
    by = {r["row_id"]: r for r in T.ROWS}
    assert by["R04"]["low"] == 8.7414 and by["R04"]["high"] == 8.9965      # T-302 room-side hole
    assert by["R07"]["high"] == pytest.approx(7.30 + 1.256)                 # T-368 r2 edges + arris
    assert {r["target"] for r in T.ROWS if r["verdict"] == "NEW"} == {"RFI-B-A14"}
    assert "RFI-B-A14" not in T.RFI_IDS
    # A-GF-01 / A-1F-01 are named inside A02 (the same fact as D-45's 3 arches), never asked as new questions
    assert by["R05"]["verdict"] == by["R06"]["verdict"] == "ADD_TO"
    assert by["R05"]["target"] == by["R06"]["target"] == "RFI-B-A02"
    # rows with no quantity governed carry a reason, never 0
    for r in T.ROWS:
        assert r["high"] != 0
        if r["high"] is None:
            assert r["held_reason"]


def test_committed_outputs_reproduced():
    assert (OUT / "T381_RFI_ROWS.csv").read_text(encoding="utf-8") == T.to_csv(T.ROWS)
    s = json.loads((OUT / "T381_SUMMARY.json").read_text(encoding="utf-8"))
    assert s == T.summary(T.ROWS)
    assert s["candidate_lines_changed"] == 0 and s["sent"] is False
