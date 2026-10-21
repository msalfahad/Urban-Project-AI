"""M7 quantity release policy (engine.source.quantity_release) and generic BOQ reconciliation (engine.source.
boq_reconcile) on hand-built items: the evidence ladder, decisions bound to the source revision and the item, the
rejected-OCR ledger, totals with their denominators, and the reconciliation states."""

from __future__ import annotations

import pytest

from engine.source import boq_reconcile as BR
from engine.source import quantity_release as QR

SRC = {"plan.dxf": "a" * 64}


def _item(iid="P-C:SLABS:1F:SITE-1", **kw):
    it = {"item_id": iid, "component_id": iid[4:], "trade": "CONCRETE", "family": "SLABS", "storey": "1F",
          "category": "PROVISIONAL", "unit": "m3", "low": 3.0, "base": 3.0, "high": 3.0, "dimensions": {"area_m2": 15},
          "assumptions": ["SLAB_SHEET_UNIFORM_THICKNESS"], "support": "CONVENTION_ONLY",
          "source": "plan.dxf SH02 face SITE-1", "blocker": "NOT_REVIEWED"}
    it.update(kw)
    return it


def test_the_ladder_and_the_release_states():
    assert QR.assess(_item(), sources=SRC)["STATE"] == "PROVISIONAL"
    src_ok = _item(support="SOURCE_COMPLETE_UNREVIEWED", assumptions=["FROZEN:PRINTED_THICKNESS"])
    assert QR.assess(src_ok, sources=SRC)["STATE"] == "SOURCE_SUPPORTED"
    assert QR.assess(src_ok, sources=SRC, check={"result": "PASS"})["STATE"] == "INDEPENDENTLY_CHECKED"
    r = QR.assess(src_ok, sources=SRC, check={"result": "DIFFERS"})
    assert r["STATE"] == "UNRESOLVED" and "INDEPENDENT_CHECK_DIFFERS" in r["REASONS"]
    u = _item("U-C:SLABS:1F:SITE-2", category="UNRESOLVED", base=None, low=None, high=None, support="NO_GEOMETRY",
              exposure_low=0.0, exposure_high=2.0, blocker="SLAB_OPENING_EXTENT_UNKNOWN")
    assert QR.assess(u, sources=SRC)["STATE"] == "UNRESOLVED"
    assert QR.assess(_item(source=""), sources=SRC)["MACHINE_RUNG"] is None


def test_an_approval_holds_only_for_the_revision_and_the_item_it_was_made_on():
    it = _item()
    d = QR.decision(it, "APPROVE", "eng-1", "ENGINEER", "2026-10-01", SRC)
    assert QR.assess(it, sources=SRC, decisions=[d])["STATE"] == "ENGINEER_APPROVED"
    r = QR.assess(it, sources={"plan.dxf": "b" * 64}, decisions=[d])               # a new drawing revision
    assert r["STATE"] == "PROVISIONAL" and "SOURCE_REVISION_CHANGED" in r["INVALIDATED_DECISIONS"]
    r = QR.assess(dict(it, base=3.2, high=3.2), sources=SRC, decisions=[d])       # the quantity changed
    assert r["STATE"] == "PROVISIONAL" and "ITEM_CHANGED" in r["INVALIDATED_DECISIONS"]
    est = QR.decision(it, "APPROVE", "est-1", "ESTIMATOR", "2026-10-01", SRC)
    assert "ROLE_NOT_ALLOWED" in QR.assess(it, sources=SRC, decisions=[est])["INVALIDATED_DECISIONS"]
    anon = dict(d, reviewer="")
    assert "NO_REVIEWER" in QR.assess(it, sources=SRC, decisions=[anon])["INVALIDATED_DECISIONS"]


def test_an_unresolved_item_cannot_be_approved_into_a_total():
    u = _item("U-C:BEAMS:1F:B3", family="BEAMS", category="UNRESOLVED", base=None, low=None, high=None,
              support="NO_GEOMETRY", exposure_low=0.3, exposure_high=0.5, blocker="UNLABELLED_SPAN_ACROSS_SUPPORT")
    d = QR.decision(u, "APPROVE", "eng-1", "ENGINEER", "2026-10-01", SRC)
    reg = QR.register([u], sources=SRC, decisions=[d])
    assert reg["rows"][0]["STATE"] == "UNRESOLVED"
    t = reg["totals"]["CONCRETE"]
    assert t["released"]["n"] == 0 and t["unresolved"] == {"n": 1, "exposure_low": 0.3, "exposure_high": 0.5,
                                                            "n_without_exposure": 0}


def test_a_rejected_ocr_reading_never_comes_back_by_itself():
    led = QR.OcrLedger([{"kind": "REJECT", "record_id": "OCR-7", "value": "4 T16", "rejection_id": "R1",
                         "reviewer": "eng-1"}])
    kept, dropped = led.screen([{"record_id": "OCR-7", "value": "4  t16"}, {"record_id": "OCR-8", "value": "2T12"}])
    assert [r["record_id"] for r in kept] == ["OCR-8"] and [r["record_id"] for r in dropped] == ["OCR-7"]
    it = _item("P-S:BEAMS:1F:B1:BOT:D16", trade="REINFORCEMENT", family="BEAMS", unit="kg")
    d = QR.decision(it, "APPROVE", "eng-1", "ENGINEER", "2026-10-01", SRC)
    r = QR.assess(it, sources=SRC, decisions=[d], ocr_dependencies=[{"record_id": "OCR-7", "value": "4 T16"}],
                  ocr_ledger=led)
    assert r["STATE"] == "UNRESOLVED" and r["REASONS"] == "DEPENDS_ON_REJECTED_OCR"
    with pytest.raises(QR.ReleaseError):                       # a re-admission must name the rejection it lifts
        led.add({"kind": "READMIT", "record_id": "OCR-7", "value": "4 T16", "reviewer": "eng-2"})
    led.add({"kind": "READMIT", "record_id": "OCR-7", "value": "4 T16", "reviewer": "eng-2", "rejection_id": "R1"})
    assert not led.is_rejected("OCR-7", "4 T16")


def test_totals_keep_their_denominators():
    items = [_item(f"P-C:SLABS:1F:SITE-{k}", base=1.0 + k, low=1.0 + k, high=1.0 + k) for k in range(3)]
    d = QR.decision(items[0], "APPROVE", "eng-1", "ENGINEER", "2026-10-01", SRC)
    t = QR.register(items, sources=SRC, decisions=[d])["totals"]["CONCRETE"]
    assert t["released"] == {"n": 1, "base": 1.0, "low": 1.0, "high": 1.0}
    assert t["provisional"]["n"] == 2 and t["provisional"]["base"] == 5.0 and t["items"] == 3
    assert sum(t["by_state"].values()) == 3
    assert "percent" not in str(t).lower()


def test_reconciliation_states():
    items = [_item(base=10.0, low=10.0, high=10.0),
             _item("U-C:SLABS:1F:SITE-9", category="UNRESOLVED", base=None, low=None, high=None, exposure_low=0.0,
                   exposure_high=2.0),
             _item("P-C:BEAMS:1F:B1", family="BEAMS", base=5.0, low=5.0, high=5.0),
             _item("P-C:COLUMNS:GF:C1", family="COLUMNS", storey="GF", base=4.0, low=4.0, high=4.0)]
    ref = BR.read_reference("FAMILY,STOREY,QUANTITY,UNIT,ITEM_REF\nSuspended slab,1F,11.5,m3,A1\n"
                            "beams,first floor,9.0,m3,A2\ncolumn,GF,4.02,m3,A3\nfooting,FDN,6.0,m3,A4\n"
                            "parapet,1F,1.0,m3,A5\n")
    res = BR.reconcile(items, ref, rate=26.5)
    st = {(r["FAMILY"], r["STOREY"]): r["STATE"] for r in res["rows"]}
    assert st[("SLABS", "1F")] == "EXPLAINED_BY_UNRESOLVED"
    assert st[("BEAMS", "1F")] == "ENGINE_SHORT"
    assert st[("COLUMNS", "GF")] == "MATCH"
    assert st[("FOOTINGS", "FOUNDATION")] == "REFERENCE_ONLY"
    assert [u["family_text"] for u in res["unmapped"]] == ["parapet"]        # never guessed
    beams = next(r for r in res["rows"] if r["FAMILY"] == "BEAMS")
    assert beams["DIFF_VALUE_AT_RATE"] == round(4.0 * 26.5, 3)
