"""T-468: engine/source/status_vocabulary_v1.py, the one status vocabulary, the mapping of every status word in use and
the acceptance record beside MERGED. Synthetic hand fixture 'villa K468' (not the development villa); every expected
state is read off the definitions by hand. Adverse cases: an unlisted word, a legacy 'VERIFIED' word, MERGED / a gate
PASS / INTEGRATED_AND_TESTED read as verification, a missing quantity in a quantity state, a downgrade over a WHOLE
verdict, WHOLE without a completeness record, an acceptance record without the aggregation proof, signed by the author
or by a worker, a malformed time, a reversed line order. The census tests read every committed BOQ_FAMILY_MASTER file
(read-only) and the vocabularies declared in code, so a new status word that nobody mapped fails here."""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "research" / "agents_t471"))
sys.path.insert(0, str(ROOT / "research" / "agents_t469"))

from engine.source import boq_line as BL  # noqa: E402
from engine.source import status_vocabulary_v1 as SV  # noqa: E402
from engine.source import trade_completeness_v1 as TC  # noqa: E402
from tools import boq_export_v1 as EX  # noqa: E402
import t469_trade_scoreboard as T469  # noqa: E402
import t471_completeness as T471  # noqa: E402

PID, REV = "synthetic-k468", "c" * 64


def mk(code, el, ev, net=None, unit="m3", br=None):
    kw = {}
    if ev == "BLOCKED_RFI":
        kw["rfi"] = {"question": "which section?"}
    if ev in ("EXCLUDED_WITH_REASON", "NOT_APPLICABLE_WITH_EVIDENCE"):
        kw["notes"] = "not drawn on any sheet"
    return BL.make_line(project_id=PID, revision_set_sha256=REV, item_code=code, unit=unit, evidence_state=ev,
                        measured_net=net, element_id=el, bounded_range=br, formula="L x W x D", rule_id="R-T468",
                        rule_version="1.0.0", trade="CONCRETE", item_en=code, item_ar=code, **kw)


def villa_k468():
    return [
        mk("STR.CONC.SLAB", "S1", "MEASURED", 12.0),
        mk("STR.CONC.SLAB", "S2", "SOURCE_DERIVED", 3.5),
        mk("STR.CONC.COLUMN", "C1", "PROVISIONAL", 1.8),
        mk("STR.CONC.COLUMN", "C2", "BOUNDED_EXPOSURE", None, br={"low": 0.4, "high": 0.9, "basis": "range"}),
        mk("STR.CONC.COLUMN", "C3", "BLOCKED_RFI"),
        mk("STR.CONC.POOL", "POOL", "EXCLUDED_WITH_REASON"),
        mk("STR.CONC.LIFT", "PIT", "NOT_APPLICABLE_WITH_EVIDENCE"),
    ]


# ---- the canonical words are the ones the code already writes ---------------------------------------------------------

def test_quantity_words_are_the_export_words_and_completeness_the_t471_states():
    assert SV.QUANTITY == EX.QSTATES
    assert (SV.VERIFIED, SV.VERIFIED_ZERO, SV.VERIFIED_COMPONENT) == (EX.VERIFIED, EX.VERIFIED_ZERO,
                                                                     EX.VERIFIED_COMPONENT)
    assert SV.COMPLETENESS == T471.STATES
    assert SV.CHECKER_ROUTINES == EX.CHECKER_ROUTINES
    # the owner's separations are all present, each a distinct word
    for w in ("VERIFIED", "VERIFIED COMPONENT", "VERIFIED ZERO", "HELD", "EXCLUDED", "UNMEASURED"):
        assert w in SV.QUANTITY
    assert SV.UNPRICED in SV.PRICING and SV.UNPRICED not in SV.QUANTITY
    assert set(SV.QUANTITY_MEANING) == set(SV.QUANTITY) and set(SV.PRICING_MEANING) == set(SV.PRICING)


# ---- census: every status word in use maps ----------------------------------------------------------------------------

def _declared_in_code():
    out = set()
    out |= {("boq_line.EVIDENCE", w) for w in BL.EVIDENCE}
    out |= {("boq_line.APPROVAL", w) for w in BL.APPROVAL}
    out |= {(f"legacy.{v}", w) for v, m in BL.LEGACY.items() for w in m}
    out |= {("export.quantity_state", w) for w in EX.QSTATES}
    out |= {("export.owner_status_class", w) for w in (EX.CLS_VERIFIED, EX.CLS_SOURCE, EX.CLS_PROJECT, EX.CLS_OWNER,
                                                       EX.CLS_HELD, EX.CLS_EXCLUDED)}
    out |= {("checker.verdict_scope", w) for w in EX.V2_SCOPES}
    out |= {("checker.downgrade", w) for w in EX.DOWNGRADE_STATES}
    out |= {("trade_completeness.element", w) for w in TC.ELEMENT_STATUSES}
    out |= {("t471.state", w) for w in T471.STATES}
    out |= {("t471.owner_gate", w) for w in T471.GATES}
    out |= {("t469.line_class", w) for w in (T469.RELEASED, T469.HELD, T469.EXCLUDED)}
    return out


def test_every_status_declared_in_code_maps():
    words = _declared_in_code()
    assert len(words) >= 70
    for voc, w in sorted(words):
        m = SV.map_word(voc, w)
        assert m["quantity"] in SV.QUANTITY + (None,), (voc, w)


def test_every_status_used_in_every_committed_family_master_maps():
    files = sorted((ROOT / "rules" / "coverage").glob("BOQ_FAMILY_MASTER_*.json"))
    assert len(files) >= 40
    seen = set()
    for f in files:
        seen |= SV.words_in_master(json.loads(f.read_text(encoding="utf-8")))
    for voc, w in sorted(seen):
        SV.map_word(voc, w)
    # the undeclared one found by this census (1.29.0+): a coverage state outside candidate_states
    assert ("family_master.coverage_in_candidate", "COVERED_BY_B4-01") in seen


def test_board_and_run_words_map_to_no_quantity():
    for w in ("QUEUED", "TODO", "CLAIMED", "READY", "MERGED", "REJECTED", "BLOCKED-DATA", "BLOCKED-OWNER", "PAUSED"):
        assert SV.map_word("board.workflow", w)["quantity"] is None
    for w in ("STARTED", "SUCCESS", "BLOCKED", "FAILED", "INCOMPLETE", "IDLE"):
        assert SV.map_word("run_log.final", w)["quantity"] is None


def test_mapping_table_file_is_current():
    committed = (ROOT / "research" / "agents_t468" / "STATUS_VOCABULARY_V1.md").read_text(encoding="utf-8")
    assert committed == SV.markdown()
    for r in SV.table_rows():
        assert f"| {r['vocabulary']} | {r['axis']} | {r['word']} |" in committed


# ---- adverse: nothing but a Checker record verifies ---------------------------------------------------------------

def test_no_word_outside_a_checker_record_establishes_verified():
    for voc, (_axis, _src, words) in SV.VOCABULARIES.items():
        if voc in SV.CHECKER_VOCABULARIES:
            continue
        for w, (q, _n) in words.items():
            assert q not in SV.VERIFIED_STATES, (voc, w, q)


@pytest.mark.parametrize("voc,word", [("legacy.provisional_estimate", "VERIFIED"),
                                      ("legacy.quantity_release", "INDEPENDENTLY_CHECKED"),
                                      ("legacy.arch_quantity_truth", "VERIFIED_COMPLETE"),
                                      ("legacy.boq_canonical", "RELEASED"),
                                      ("trade_completeness.element", "MEASURED")])
def test_legacy_verified_words_read_measured_unverified(voc, word):
    assert SV.map_word(voc, word)["quantity"] == SV.MEASURED_UNVERIFIED


def test_merge_gate_and_capability_are_not_verification():
    assert SV.map_word("board.workflow", "MERGED")["quantity"] is None
    assert SV.map_word("checker.gate", "GATE B PASS")["quantity"] is None
    assert SV.map_word("family_master.capability", "INTEGRATED_AND_TESTED")["quantity"] is None
    assert SV.map_word("family_master.candidate", "INTEGRATED_IN_CANDIDATE_AND_TESTED")["quantity"] is None
    # the export's owner class 'VERIFIED' covers three states: never read verification from it
    m = SV.map_word("export.owner_status_class", "VERIFIED")
    assert m["quantity"] is None and "AMBIGUOUS" in m["note"]
    # an element VERIFIED is a component, not a line
    assert SV.map_word("trade_completeness.element", "VERIFIED")["quantity"] == SV.VERIFIED_COMPONENT


@pytest.mark.parametrize("voc,word", [("board.workflow", "APPROVED"), ("boq_line.EVIDENCE", "VERIFIED"),
                                      ("family_master.candidate", "COVERED_BY_B4-01"),
                                      ("family_master.coverage_in_candidate", "COVERED_BY_"),
                                      ("family_master.coverage_in_candidate", "COVERED_BY_wall tiles"),
                                      ("no.such.vocabulary", "HELD"), ("boq_line.EVIDENCE", "measured")])
def test_unlisted_word_is_refused_never_defaulted(voc, word):
    with pytest.raises(SV.StatusError):
        SV.map_word(voc, word)


def test_held_states_are_never_zero_or_released():
    for voc, (_a, _s, words) in SV.VOCABULARIES.items():
        for w, (q, note) in words.items():
            if w in ("BLOCKED_RFI", "BOUNDED_EXPOSURE", "UNRESOLVED", "CONFLICT", "POSSIBLY_APPLICABLE", "MISSING"):
                assert q in (SV.HELD, SV.UNMEASURED), (voc, w)


# ---- a line's quantity state (hand fixture villa K468) ----------------------------------------------------------------

def test_line_states_without_checker_records_by_hand():
    got = [SV.quantity_of_line(ln) for ln in villa_k468()]
    assert got == [SV.MEASURED_UNVERIFIED, SV.MEASURED_UNVERIFIED, SV.MEASURED_UNVERIFIED, SV.HELD, SV.HELD,
                   SV.EXCLUDED, SV.EXCLUDED]
    # mirrored order: same state per line
    rev = list(reversed(villa_k468()))
    assert [SV.quantity_of_line(ln) for ln in rev] == list(reversed(got))


def test_line_states_agree_with_the_export_row_states():
    ls = villa_k468()
    out = EX.build(ls, candidate_version="K468", boq_lines_sha256=EX.lines_sha256(ls))
    by = {r["line_id"]: r["quantity_state"] for r in out["rows"] if r["line_id"]}
    for ln in ls:
        assert by[ln["line_id"]] == SV.quantity_of_line(ln), ln["location"]["element_id"]


def test_line_states_with_checker_records():
    s1, _s2, c1, c2, _c3, _pool, pit = villa_k468()
    assert SV.quantity_of_line(s1, whole=True, completeness_passes=True) == SV.VERIFIED
    assert SV.quantity_of_line(s1, whole=True, completeness_passes=False) == SV.MEASURED_UNVERIFIED
    assert SV.quantity_of_line(c1, component=True) == SV.VERIFIED_COMPONENT
    assert SV.quantity_of_line(pit, whole=True, completeness_passes=True) == SV.VERIFIED_ZERO
    assert SV.quantity_of_line(pit) == SV.EXCLUDED
    # a downgrade outranks any verdict; a held line is never promoted by a verdict
    assert SV.quantity_of_line(s1, whole=True, completeness_passes=True, downgraded=True) == SV.HELD
    assert SV.quantity_of_line(c2, whole=True, completeness_passes=True) == SV.HELD
    # a zero with a WHOLE verdict is VERIFIED ZERO, not VERIFIED
    z = copy.deepcopy(s1)
    z["measured_net"] = 0.0
    assert SV.quantity_of_line(z, whole=True, completeness_passes=True) == SV.VERIFIED_ZERO


def test_missing_quantity_in_a_quantity_state_is_held_not_zero():
    ln = copy.deepcopy(villa_k468()[0])
    ln["measured_net"] = None
    assert SV.quantity_of_line(ln) == SV.HELD
    assert SV.quantity_of_line(ln, whole=True, completeness_passes=True) == SV.HELD
    bad = dict(ln, evidence_state="VERIFIED")
    with pytest.raises(SV.StatusError):
        SV.quantity_of_line(bad)


def test_every_line_is_unpriced():
    assert {SV.pricing_of_line(ln) for ln in villa_k468()} == {SV.UNPRICED}


# ---- the acceptance record beside MERGED ----------------------------------------------------------------------------

def acc(**kw):
    rec = {"schema": SV.ACCEPTANCE_SCHEMA, "acceptance_id": "ACC-K468-1", "subject_kind": "TRADE",
           "subject_id": "CONCRETE.SLAB", "task": "T-180", "candidate_version": "K468", "state": SV.VERIFIED,
           "measurement_proof": {"kind": "CHECKER_VERDICT_V2", "ref": "V2-k468slab", "commit": "abc1234"},
           "aggregation_proof": {"kind": "T469_SCOREBOARD", "ref": "research/agents_t469/out/k468.json",
                                 "commit": "abc1234"},
           "checker": {"routine": "Checker", "run_token": "k468"}, "time": "2026-11-04T15:40Z",
           "merge": "def5678", "author": "Worker 1"}
    rec.update(kw)
    return rec


def test_acceptance_with_both_proofs_is_verified():
    assert SV.acceptance_problems(acc()) == []
    assert SV.accepted_state(acc()) == SV.VERIFIED
    line = acc(subject_kind="LINE", subject_id="L-k468-s1")
    assert SV.accepted_state(line) == SV.VERIFIED
    comp = acc(subject_kind="COMPONENT", state=SV.VERIFIED_COMPONENT, aggregation_proof=None)
    assert SV.accepted_state(comp) == SV.VERIFIED_COMPONENT
    zero = acc(subject_kind="LINE", state=SV.VERIFIED_ZERO,
               measurement_proof={"kind": "ABSENCE_FROM_DRAWINGS", "ref": "sheet S-3 note 4", "commit": "abc1234"})
    assert SV.accepted_state(zero) == SV.VERIFIED_ZERO


@pytest.mark.parametrize("change,why", [
    ({"aggregation_proof": None}, "aggregation_proof: required"),
    ({"measurement_proof": None}, "measurement_proof: required"),
    ({"checker": {"routine": "Worker 1"}}, "checker.routine"),
    ({"checker": {"routine": "Checker"}, "author": "checker"}, "cannot accept"),
    ({"time": "4 Nov 2026"}, "time:"),
    ({"state": "MERGED"}, "state:"),
    ({"state": SV.MEASURED_UNVERIFIED}, "state:"),
    ({"task": "merged"}, "task:"),
    ({"measurement_proof": {"kind": "BOARD_MERGED", "ref": "T-180", "commit": "abc1234"}}, "measurement_proof.kind"),
    ({"measurement_proof": {"kind": "ABSENCE_FROM_DRAWINGS", "ref": "S-3", "commit": "abc1234"}}, "re-measure"),
    ({"subject_kind": "COMPONENT", "aggregation_proof": None}, "COMPONENT is VERIFIED COMPONENT"),
    ({"merge": "MERGED"}, "merge:"),
])
def test_acceptance_refused(change, why):
    rec = acc(**change)
    p = SV.acceptance_problems(rec)
    assert any(why in x for x in p), p
    with pytest.raises(SV.StatusError):
        SV.accepted_state(rec)


def test_trade_state_needs_verified_lines_and_an_accepted_aggregation():
    v, z, x = SV.VERIFIED, SV.VERIFIED_ZERO, SV.EXCLUDED
    assert SV.trade_state([v, z, x], acc()) == SV.VERIFIED
    assert SV.trade_state([v, z, x]) == SV.MEASURED_UNVERIFIED            # no acceptance record
    with pytest.raises(SV.StatusError):
        SV.trade_state([v, x], acc(aggregation_proof=None))               # insufficient record: refused, not promoted
    assert SV.trade_state([v, SV.VERIFIED_COMPONENT], acc()) == SV.MEASURED_UNVERIFIED
    assert SV.trade_state([v, SV.HELD], acc()) == SV.HELD
    assert SV.trade_state([v, SV.HELD, SV.UNMEASURED], acc()) == SV.UNMEASURED
    assert SV.trade_state([x, x]) == SV.EXCLUDED
    assert SV.trade_state([]) == SV.UNMEASURED
    assert SV.trade_state([z, x], acc(state=SV.VERIFIED_ZERO)) == SV.VERIFIED_ZERO
    with pytest.raises(SV.StatusError):
        SV.trade_state(["MERGED"])


def test_module_is_check_only():
    assert SV.DEFAULT_GUARD_CLASS == "CHECK_ONLY"
    src = (ROOT / "engine" / "source" / "status_vocabulary_v1.py").read_text(encoding="utf-8")
    assert "open(" not in src and "write_text" not in src
