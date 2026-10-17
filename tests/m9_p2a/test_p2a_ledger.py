"""Phase 2A P2-08a: the read-only surface ledger (ELIGIBILITY_V0 PROPOSAL) - totality, the nine statuses, read-only,
injected omission, reveals never a confirmed omission, the kitchen never reclassified, every missing record a
finding (round 2 AT-Q3-01 .. 06; owner requirement 3)."""

from __future__ import annotations

import copy
import sys
from collections import Counter
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from engine.source import door_model as DM                     # noqa: E402
from engine.source import surface_ledger as SL                 # noqa: E402

import p2a_helpers as H                                         # noqa: E402


@pytest.fixture(scope="module")
def villa(tmp_path_factory):
    from tools import arch_synth as AS
    from tools import urban_boq_m9 as M9
    p = tmp_path_factory.mktemp("v") / "villa.dxf"
    AS.villa(str(p))
    room, arch, _E = M9.arch_compute(str(p), method="ARCH_TAKEOFF_V2.1")
    return room, arch


def _run(room, arch, lines=None):
    return SL.ledger(room["lines"] if lines is None else lines, arch["rooms"], arch["openings"], room["unresolved"],
                     method="ARCH_TAKEOFF_V2.1", doors=arch["doors"], walls=arch["walls"])


def test_every_record_has_one_of_the_nine_statuses_and_one_record_per_element_and_row(villa):
    room, arch = villa
    L = arch["ledger"]
    assert {r["status"] for r in L["records"]} <= set(SL.STATUSES)
    per = Counter(r["element"] for r in L["records"] if r["element_kind"].startswith("SPACE:"))
    for rm in arch["rooms"]:
        if rm["class"] not in ("ROOM", "MIXED", "MERGED", "UNLABELLED"):
            continue
        kind = SL.KIND_OF.get(rm.get("kind"), "UNKNOWN")
        rows = SL.ELIGIBILITY_V0[kind]
        assert per[f"{rm['room_id']} ({rm.get('name_en') or rm['class']})"] == (1 if isinstance(rows, str) else len(rows))


def test_the_ledger_is_read_only(villa):
    room, arch = villa
    before = copy.deepcopy(room["lines"])
    _run(room, arch)
    assert room["lines"] == before
    assert _run(room, arch)["records"] == arch["ledger"]["records"]


def test_reveals_and_head_soffits_are_never_a_confirmed_omission(villa):
    _room, arch = villa
    rv = [r for r in arch["ledger"]["records"] if r["surface"] in ("REVEAL_JAMBS", "HEAD_SOFFIT")]
    assert rv and all(r["status"] == "UNRESOLVED_ELIGIBILITY" for r in rv)
    assert all(any(c.startswith("NO_EMITTER") for c in r["conditions"]) for r in rv)


def test_the_kitchen_stays_service_and_its_wet_eligibility_is_an_open_question(villa):
    _room, arch = villa
    k = [r for r in arch["ledger"]["records"] if r["element_kind"] == "SPACE:SERVICE"]
    assert k and not [r for r in k if r["trade"] in ("WALL_TILE", "WET_FLOOR_TILE", "WATERPROOFING_UPTURN")]
    wp = [r for r in k if r["trade"] == "WATERPROOFING_FLOOR"]
    assert wp and all(r["status"] == "UNRESOLVED_ELIGIBILITY" for r in wp)


def test_an_injected_omission_becomes_exactly_one_confirmed_missing_with_a_finding(villa):
    """AT-Q3-04: delete one room's skirting line: exactly one more CONFIRMED_MISSING at that (element, surface)."""
    room, arch = villa
    base = arch["ledger"]["summary"]["by_status"]["CONFIRMED_MISSING"]
    sk = next(ln for ln in room["lines"] if ln["item_code"] == "FIN.SKIRTING" and ln["evidence_state"] == "SOURCE_DERIVED")
    L = _run(room, arch, [ln for ln in room["lines"] if ln["line_id"] != sk["line_id"]])
    assert L["summary"]["by_status"]["CONFIRMED_MISSING"] == base + 1
    (miss,) = [r for r in L["records"] if r["status"] == "CONFIRMED_MISSING"]
    assert miss["surface"] == "SKIRTING" and miss["element"].startswith(sk["location"]["room_id"])
    assert any(f["code"] == "LEDGER_CONFIRMED_MISSING" and f["records"] == 1 for f in L["findings"])


def test_every_record_without_a_line_is_a_finding_and_no_total_adds_them(villa):
    _room, arch = villa
    L = arch["ledger"]
    gap = [r for r in L["records"] if r["status"] in ("NO_EMITTER", "CONFIRMED_MISSING", "UNRESOLVED_ELIGIBILITY")]
    assert sum(f["records"] for f in L["findings"]) == len(gap)
    assert L["summary"]["confirmed_missing"] == L["summary"]["by_status"]["CONFIRMED_MISSING"]
    assert set(L["summary"]["never_added_to_missing"]) >= {"NO_EMITTER", "UNRESOLVED_ELIGIBILITY",
                                                           "BLOCKED_MISSING_SOURCE", "BLOCKED_OWNER_DECISION"}


def test_the_eligibility_table_is_versioned_and_a_proposal(villa):
    _room, arch = villa
    t = arch["ledger"]["table"]
    assert t == {"id": "ELIGIBILITY_V0", "status": "PROPOSAL", "digest": SL.table_digest()}
    assert arch["run"]["v2_1"]["ledger"]["table"]["digest"] == SL.table_digest()
    assert not SL._approved("PROPOSAL") and not SL._approved("OWNER_DECISION_OPEN: Q-S6-1")
    assert SL._approved("UP-CER-003") and SL._approved(SL.DOOR_RULE)


def test_door_elements_in_the_ledger_follow_the_door_model():
    S, M, model = H.door_run(H.door_fixture())
    lines = M["lines"] + DM.boq_lines({"project_id": "P", "revision_set_sha256": "0" * 64, "documents": []}, model)
    lines = [ln for ln in lines if ln["item_code"] != "ARCH.DOOR"]
    L = SL.ledger(lines, M["rooms"], M["openings"], M["unresolved"], method="ARCH_TAKEOFF_V2.1", doors=model)
    op = {r["element"]: r for r in L["records"] if r["surface"] == "OPENING" and r["element_kind"].startswith("OPENING")}
    by_class = Counter()
    for el in model["elements"]:
        if not el.get("opening_id"):
            continue
        r = next(v for k, v in op.items() if k.startswith(f"GF:{el['opening_id']} "))
        by_class[(el["boq_class"], r["status"])] += 1
    assert by_class[(DM.LIFT, "EXCLUDED")] == 1
    assert by_class[(DM.MAIN, "MEASURED")] == 1 and by_class[(DM.PVC, "MEASURED")] == 4
    un = [r for r in L["records"] if r["element_kind"] == "DOOR_ELEMENT" and r["surface"] == "OPENING"]
    assert len(un) == 1 and un[0]["status"] == "BLOCKED_MISSING_SOURCE"
