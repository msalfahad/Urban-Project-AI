"""M4 OCR review: a second independent reading checks every OCR record; disagreement or an ambiguous second reading
rejects the value (its role becomes UNRESOLVED, never zero, never half a role); agreement never promotes a record.
Synthetic evidence in the detail_evidence schema, plus the committed readings of the ST7757 p.13 records."""

from __future__ import annotations

import json
from pathlib import Path

from engine.source import detail_evidence as DE             # noqa: E402
from engine.source import ocr_review as OR                  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]


def _rec(rid, text, reads=None, validation="VECTOR_GLYPH_CONSENSUS", state="OCR_UNREVIEWED"):
    reads = reads or [text, text]
    return {"record_id": rid, "page": 3, "region_pt": [0, 0, 10, 5], "method": "OCR_TESSERACT", "raw_text": text,
            "reads": [{"text": t, "parsed": DE.parse_notation(t)} for t in reads], "parsed": DE.parse_notation(text),
            "state": state, "validation": validation}


def _ev():
    recs = [_rec("R1", "3Ø16"), _rec("R2", "Ø8/15cm", validation="UNANIMOUS_READS_GLYPHS_UNCHECKED"),
            _rec("R3", "3Ø16", reads=["5016", "3916"]), _rec("R4", "3Ø16"),
            _rec("R5", "98/150m", state="OCR_REJECTED_UNPARSED", validation=None), _rec("R6", "3Ø14")]
    det = {"detail_id": "DET-A", "caption_id": "C1", "caption": DE.caption_of("Ground Beams. More than 5m length"),
           "state": "ASSEMBLED", "page": 3, "rejected_records": ["R5"],
           "bars": [{"role": "TOP", "count": 3, "dia_mm": 16, "spacing_m": None, "record_id": "R1"},
                    {"role": "LINKS", "count": None, "dia_mm": 8, "spacing_m": 0.15, "record_id": "R2"},
                    {"role": "BOTTOM", "count": 3, "dia_mm": 16, "spacing_m": None, "record_id": "R3"},
                    {"role": "BOTTOM", "count": 3, "dia_mm": 16, "spacing_m": None, "record_id": "R4"}]}
    det2 = {"detail_id": "DET-B", "caption_id": "C2", "caption": DE.caption_of("Ground Beams. Less than 5m length"),
            "state": "ASSEMBLED", "page": 3, "rejected_records": [],
            "bars": [{"role": "TOP", "count": 3, "dia_mm": 14, "spacing_m": None, "record_id": "R6"}]}
    return {"schema": DE.SCHEMA, "records": recs, "details": [det, det2]}


def _rd(**kv):
    return {k: {"text": v, "by": "SECOND_READER", "on": "2026-10-11", "basis": "crop"} for k, v in kv.items()}


def test_outcomes_and_confidence():
    rows = {r["record_id"]: r for r in OR.review(_ev(), _rd(R1="3Ø16", R2="Ø8/15cm", R3="3Ø16", R4="3Ø18",
                                                           R5="Ø8/15cm", R6="3?14"))}
    assert rows["R1"]["outcome"] == "AGREES" and rows["R1"]["confidence"] == "HIGH"
    assert rows["R2"]["confidence"] == "MEDIUM"              # glyphs unchecked
    assert rows["R3"]["reads_disagree"] and rows["R3"]["confidence"] == "MEDIUM"   # settled by glyphs only
    assert rows["R4"]["outcome"] == "DISAGREES" and rows["R4"]["state_after_review"] == "OCR_REJECTED_DISAGREE"
    assert rows["R5"]["outcome"] == "REJECTED_STAYS" and rows["R5"]["state_after_review"] == "OCR_REJECTED_UNPARSED"
    assert rows["R6"]["outcome"] == "AMBIGUOUS_READING"
    assert not any(r["promoted"] for r in rows.values())
    assert all(r["state_after_review"] != "MANUALLY_CONFIRMED" for r in rows.values())
    assert rows["R1"]["applies_to"] == [("DET-A", "TOP")] and rows["R5"]["applies_to"] == [("DET-A",
                                                                                          "REJECTED_FROM_DETAIL")]
    nr = {r["record_id"]: r for r in OR.review(_ev(), {})}
    assert {r["outcome"] for k, r in nr.items() if k != "R5"} == {"NOT_READ"}


def test_apply_drops_the_whole_role_and_never_promotes():
    ev = _ev()
    rows = OR.review(ev, _rd(R1="3Ø16", R2="Ø8/15cm", R3="3Ø16", R4="3Ø18", R6="3?14"))
    out = OR.apply(ev, rows)
    assert ev["records"][3]["state"] == "OCR_UNREVIEWED"          # the input is not modified
    st = {r["record_id"]: r["state"] for r in out["records"]}
    assert st == {"R1": "OCR_UNREVIEWED", "R2": "OCR_UNREVIEWED", "R3": "OCR_UNREVIEWED",
                  "R4": "OCR_REJECTED_DISAGREE", "R5": "OCR_REJECTED_UNPARSED", "R6": "OCR_REJECTED_DISAGREE"}
    a = next(d for d in out["details"] if d["detail_id"] == "DET-A")
    assert {b["role"] for b in a["bars"]} == {"TOP", "LINKS"}      # both bottom layers leave: no half role
    assert a["rejected_records"] == ["R4", "R5"] and a["roles_rejected_by_review"] == ["BOTTOM"]
    assert DE.validate(out) == []
    # downstream: the detail is still usable, the bottom role is not
    gd = {d["detail_id"]: d for d in DE.ground_beam_details(out)}
    assert "BOTTOM" not in gd["DET-A"]["bars"] and gd["DET-A"]["rejected_records"]
    assert "DET-B" not in gd                                      # its only record was rejected


def test_downstream_quantities_by_detail_and_role():
    rows = OR.review(_ev(), _rd(R1="3Ø16"))
    items = [{"trade": "REINFORCEMENT", "category": "PROVISIONAL", "item_id": "P-S:GB:X:TOP:D16", "base": 10.0,
              "source": "x; typical detail DET-A p.3 records R1,R2"},
             {"trade": "REINFORCEMENT", "category": "PROVISIONAL", "item_id": "P-S:GB:X:BOTTOM:D16", "base": 20.0,
              "source": "x; typical detail DET-A p.3 records R1,R2"},
             {"trade": "REINFORCEMENT", "category": "PROVISIONAL", "item_id": "P-S:GB:Y:TOP:D14", "base": 5.0,
              "source": "x; typical detail DET-AB p.3"}]
    d = OR.downstream(rows, items)
    assert d["R1"] == (1, 10.0) and d["R3"] == (1, 20.0) and d["R4"] == (1, 20.0) and d["R6"] == (0, 0.0)


def test_st7757_readings_check_but_never_confirm():
    ev = json.loads((ROOT / "research/urban_engine_m3_recovery/evidence/DETAIL_EVIDENCE.json").read_text())
    doc = json.loads((ROOT / "research/urban_engine_m4_correctness/evidence/OCR_INDEPENDENT_READINGS.json")
                     .read_text())
    assert doc["reader"] != "PERSON" and "not a person" in doc["status"]
    rows = OR.review(ev, doc["readings"])
    out = {r["record_id"]: r["outcome"] for r in rows}
    assert len(rows) == 15 and sum(v == "AGREES" for v in out.values()) == 14
    assert out["EV-0007"] == "REJECTED_STAYS"                      # read as a value, still rejected: a person decides
    assert OR.apply(ev, rows) == ev                                # nothing changes, nothing is promoted
