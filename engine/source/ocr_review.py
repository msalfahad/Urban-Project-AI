"""OCR REVIEW (M4) - a second, independent reading of every OCR-derived detail-evidence record, compared value by
value (generic; stdlib + engine.source.detail_evidence). It never promotes a record: whatever the second reading
says, an OCR record stays OCR_UNREVIEWED (or rejected) until a person confirms it (detail_evidence
MANUALLY_CONFIRMED, with who and when). A reading by a model or by a second OCR engine is a check, not a
confirmation.

    review(evidence, readings)  one row per record: the OCR reads and their parses, whether the reads themselves
                                disagreed (and what settled them: vector-glyph consensus or unanimous reads), the
                                independent reading and its parse, the detail / role the record feeds, and an outcome
                                    AGREES             same count, diameter and spacing
                                    DISAGREES          a different value                -> rejected for quantities
                                    AMBIGUOUS_READING  the second reading parses to no single value -> rejected
                                    NOT_READ           no second reading (the record stands as OCR_UNREVIEWED)
                                    REJECTED_STAYS     the OCR rules had rejected the record; a second reading,
                                                       even one that parses, does not restore it (a person must)
                                and a confidence: HIGH only when the OCR reads agreed among themselves, the glyphs were
                                checked and the second reading agrees; MEDIUM when one of the two holds; LOW otherwise
    apply(evidence, rows)       a copy of the evidence in which every DISAGREES / AMBIGUOUS_READING record is
                                OCR_REJECTED_DISAGREE and leaves its detail together with every bar of the same role
                                (two bottom layers read from two records: half a role is not a value); the detail
                                lists it under rejected_records, so the role becomes UNRESOLVED downstream, never zero
    downstream(rows, items)     the quantities each record feeds: reinforcement items whose source names the
                                record's detail, for the record's role -> {record_id: (n_items, base kg)}
"""

from __future__ import annotations

import copy
import re

from engine.source import detail_evidence as DE

POLICY_ID = "OCR_REVIEW_V1"
OUTCOMES = ("AGREES", "DISAGREES", "AMBIGUOUS_READING", "NOT_READ", "REJECTED_STAYS")
REJECTING = ("DISAGREES", "AMBIGUOUS_READING")


def _val(p):
    return None if not p or p.get("state") != "PARSED" else (p.get("count"), p.get("dia_mm"), p.get("spacing_m"))


def review(evidence, readings):
    """readings: {record_id: {text, by, on, basis}} - the independent reading of each record (the reader is named;
    never a person unless a person read it)."""
    where = {}
    for d in evidence.get("details", []):
        for b in d.get("bars", []):
            where.setdefault(b["record_id"], []).append((d["detail_id"], b["role"]))
        for rid in d.get("rejected_records", []):
            where.setdefault(rid, []).append((d["detail_id"], "REJECTED_FROM_DETAIL"))
    rows = []
    for r in evidence.get("records", []):
        if not str(r.get("method", "")).startswith("OCR"):
            continue
        reads = r.get("reads", [])
        vals = {_val(x.get("parsed") or DE.parse_notation(x.get("text"))) for x in reads}
        reads_disagree = len(vals) > 1
        ocr_val = _val(r.get("parsed"))
        rd = readings.get(r["record_id"])
        ip = DE.parse_notation(rd["text"]) if rd else None
        ind = _val(ip)
        if r.get("state") not in DE.USABLE:
            outcome = "REJECTED_STAYS"
        elif rd is None:
            outcome = "NOT_READ"
        elif ind is None:
            outcome = "AMBIGUOUS_READING"
        elif ind == ocr_val:
            outcome = "AGREES"
        else:
            outcome = "DISAGREES"
        checked = r.get("validation") == "VECTOR_GLYPH_CONSENSUS"
        score = (not reads_disagree) + checked
        conf = "LOW"
        if outcome == "AGREES":
            conf = "HIGH" if score == 2 else "MEDIUM" if score == 1 else "LOW"
        rows.append({"record_id": r["record_id"], "page": r.get("page"), "region_pt": r.get("region_pt"),
                     "crop": r.get("crop"), "ocr_state": r.get("state"), "ocr_raw": r.get("raw_text"),
                     "ocr_reads": [x.get("text") for x in reads], "reads_disagree": reads_disagree,
                     "glyph_validation": r.get("validation"),
                     "ocr_value": ocr_val, "independent_text": rd["text"] if rd else None,
                     "independent_value": ind, "independent_by": rd.get("by") if rd else None,
                     "independent_basis": rd.get("basis") if rd else None,
                     "independent_state": ip.get("state") if ip else None,
                     "applies_to": where.get(r["record_id"], []), "outcome": outcome, "confidence": conf,
                     "state_after_review": ("OCR_REJECTED_DISAGREE" if outcome in REJECTING else r.get("state")),
                     "promoted": False})
    return rows


def apply(evidence, rows):
    out = copy.deepcopy(evidence)
    bad = {x["record_id"] for x in rows if x["outcome"] in REJECTING}
    for r in out.get("records", []):
        if r["record_id"] in bad:
            r["state"] = "OCR_REJECTED_DISAGREE"
            r["review"] = POLICY_ID
    for d in out.get("details", []):
        # a role read from several records (two bottom layers) loses all of them: half a role is not a value
        roles = {b["role"] for b in d.get("bars", []) if b["record_id"] in bad}
        if roles:
            drop = [b for b in d["bars"] if b["role"] in roles]
            d["bars"] = [b for b in d["bars"] if b["role"] not in roles]
            d["rejected_records"] = sorted(set(d.get("rejected_records", [])) | {b["record_id"] for b in drop
                                                                                 if b["record_id"] in bad})
            d["roles_rejected_by_review"] = sorted(roles)
    return out


def downstream(rows, items):
    """{record_id: (n_items, base kg)} over the reinforcement items fed by the record's (detail, role)."""
    out = {}
    for x in rows:
        n, kg = 0, 0.0
        for det, role in x["applies_to"]:
            pat = re.compile(rf"typical detail {re.escape(det)}\b")
            for i in items:
                if i.get("trade") != "REINFORCEMENT" or i.get("category") != "PROVISIONAL":
                    continue
                parts = i["item_id"].split(":")
                if len(parts) >= 2 and parts[-2] == role and pat.search(i.get("source") or ""):
                    n += 1
                    kg += i["base"] or 0.0
        out[x["record_id"]] = (n, kg)
    return out


def policy_record():
    return {"policy": POLICY_ID, "outcomes": list(OUTCOMES), "rejecting": list(REJECTING),
            "rule": "a second independent reading checks every OCR record; disagreement or an ambiguous second reading "
                    "rejects the value (its role becomes UNRESOLVED); agreement never promotes a record - only a "
                    "person's confirmation (MANUALLY_CONFIRMED, who and when) does"}
