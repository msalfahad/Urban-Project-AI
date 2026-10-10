"""VISUAL_SOURCE_CLAIM_V1 - structured claims read from rendered drawing evidence (PDF pages whose text is vector
glyphs or raster, so no machine text exists), with a review state that decides how much authority a claim carries.

    AI reads.  Deterministic code calculates.

A claim records the drawing (sha256), page, crop box, the hash of the rendered crop, the raw transcription and its
normalised interpretation. Its source state is *derived* from its corroborations, never asserted:

    MACHINE_READ             the value itself came from deterministic text / geometry (no AI reading involved)
    AI_VISUAL_TRANSCRIPTION  read by an AI from the rendered crop; nothing independent agrees yet
    CROSS_VERIFIED_SOURCE    the AI reading is agreed by >= 2 distinct non-AI channels, at least one deterministic
                             (OCR text, PDF vector geometry, DXF geometry / text), and every facet the claim asserts
                             (count, diameter, spacing, dimension ...) is covered by at least one agreeing channel
    HUMAN_VERIFIED_SOURCE    a named human verification record is attached
    SOURCE_CONFLICT          any corroboration disagrees
    BLOCKED_UNREAD           the region could not be read

Authority: MACHINE_READ / CROSS_VERIFIED / HUMAN_VERIFIED may feed VERIFIED quantities; AI_VISUAL_TRANSCRIPTION may
feed PROVISIONAL quantities only; SOURCE_CONFLICT and BLOCKED_UNREAD feed nothing.

Reading a source is not applying it: `applicability` is a separate field (APPLICABLE / NOT_APPLICABLE /
APPLICABILITY_BLOCKED / NOT_ASSESSED) and only an APPLICABLE claim with quantity authority may drive a quantity.
Stdlib only; project-agnostic.
"""

from __future__ import annotations

import hashlib
import re

POLICY_ID = "VISUAL_SOURCE_CLAIM_V1"
MACHINE_READ = "MACHINE_READ"
AI_VISUAL = "AI_VISUAL_TRANSCRIPTION"
CROSS_VERIFIED = "CROSS_VERIFIED_SOURCE"
HUMAN_VERIFIED = "HUMAN_VERIFIED_SOURCE"
SOURCE_CONFLICT = "SOURCE_CONFLICT"
BLOCKED_UNREAD = "BLOCKED_UNREAD"
SOURCE_STATES = (MACHINE_READ, AI_VISUAL, CROSS_VERIFIED, HUMAN_VERIFIED, SOURCE_CONFLICT, BLOCKED_UNREAD)

DETERMINISTIC_KINDS = ("OCR_TEXT", "PDF_VECTOR_GEOMETRY", "DXF_GEOMETRY", "DXF_TEXT")
INDEPENDENT_KINDS = ("INDEPENDENT_REVIEW", "INDEPENDENT_DOCUMENT")
CORROBORATION_KINDS = DETERMINISTIC_KINDS + INDEPENDENT_KINDS
APPLICABILITY = ("APPLICABLE", "NOT_APPLICABLE", "APPLICABILITY_BLOCKED", "NOT_ASSESSED")
REVIEW_STATES = ("UNREVIEWED", "QS_REVIEW_PENDING", "REVIEWED")
VERIFIED_AUTHORITY, PROVISIONAL_AUTHORITY, NO_AUTHORITY = "VERIFIED", "PROVISIONAL", "NONE"
REQUIRED = ("claim_id", "drawing_sha256", "drawing", "page", "crop_bbox", "crop_hash", "raw_visual_transcription",
            "normalised_interpretation", "discipline", "element_type", "value", "unit", "consumer")


def crop_hash(samples: bytes) -> str:
    """sha256 of the rendered crop's raw pixel samples (the image a QS opens to check the claim)."""
    return hashlib.sha256(samples).hexdigest()


def corroboration(kind, ref, agrees, facets, detail=None) -> dict:
    if kind not in CORROBORATION_KINDS:
        raise ValueError(f"unknown corroboration kind {kind}")
    return {"kind": kind, "ref": ref, "agrees": bool(agrees), "facets": sorted(set(facets)), "detail": detail}


def claim(*, claim_id, drawing_sha256, drawing, page, crop_bbox, crop_hash, raw_visual_transcription,
          normalised_interpretation, discipline, element_type, value, unit, consumer, bar_role=None, facets=(),
          corroborations=(), origin=AI_VISUAL, human_verification=None, applicability="NOT_ASSESSED",
          applicability_why=None, review_state="QS_REVIEW_PENDING", notes=None) -> dict:
    if origin not in (AI_VISUAL, MACHINE_READ, BLOCKED_UNREAD):
        raise ValueError("origin must be AI_VISUAL_TRANSCRIPTION, MACHINE_READ or BLOCKED_UNREAD")
    if applicability not in APPLICABILITY:
        raise ValueError(f"unknown applicability {applicability}")
    c = {"policy_id": POLICY_ID, "claim_id": claim_id, "drawing_sha256": drawing_sha256, "drawing": drawing,
         "page": page, "crop_bbox": list(crop_bbox) if crop_bbox is not None else None, "crop_hash": crop_hash,
         "raw_visual_transcription": raw_visual_transcription, "normalised_interpretation": normalised_interpretation,
         "discipline": discipline, "element_type": element_type, "bar_role": bar_role, "value": value, "unit": unit,
         "facets": sorted(set(facets)), "corroborations": list(corroborations), "origin": origin,
         "human_verification": human_verification, "applicability": applicability,
         "applicability_why": applicability_why, "review_state": review_state, "consumer": consumer, "notes": notes}
    c["source_state"], c["state_why"] = resolve_state(c)
    c["quantity_authority"] = authority(c)
    return c


def resolve_state(c) -> tuple:
    """Derive the source state from origin + corroborations (the only way a claim gains authority)."""
    if c["origin"] == BLOCKED_UNREAD:
        return BLOCKED_UNREAD, "region not readable"
    cs = c.get("corroborations") or []
    bad = [x for x in cs if not x["agrees"]]
    if bad:
        return SOURCE_CONFLICT, "disagreeing corroboration: " + "; ".join(f"{x['kind']} {x['ref']}" for x in bad)
    hv = c.get("human_verification")
    if hv:
        if not (hv.get("verified_by") and hv.get("date") and hv.get("statement")):
            raise ValueError("a human verification needs verified_by, date and statement")
        return HUMAN_VERIFIED, f"human verification by {hv['verified_by']} on {hv['date']}"
    if c["origin"] == MACHINE_READ:
        return MACHINE_READ, "value read by deterministic code"
    fac = set(c.get("facets") or ())
    kinds = {x["kind"] for x in cs if not fac or set(x["facets"]) & fac}      # a channel counts only for what it checks
    det = kinds & set(DETERMINISTIC_KINDS)
    covered = set()
    for x in cs:
        covered |= set(x["facets"])
    missing = sorted(set(c.get("facets") or ()) - covered)
    if len(kinds) >= 2 and det and not missing:
        return CROSS_VERIFIED, ("AI reading agreed by " + ", ".join(sorted(kinds)) +
                                "; every facet covered (" + ", ".join(c.get("facets") or ()) + ")")
    why = []
    if len(kinds) < 2:
        why.append(f"{len(kinds)} non-AI channel(s) (needs 2)")
    if not det:
        why.append("no deterministic channel")
    if missing:
        why.append("facets not corroborated: " + ", ".join(missing))
    return AI_VISUAL, "AI transcription only - " + "; ".join(why)


def authority(c) -> str:
    st = c["source_state"]
    if st in (MACHINE_READ, CROSS_VERIFIED, HUMAN_VERIFIED):
        return VERIFIED_AUTHORITY
    if st == AI_VISUAL:
        return PROVISIONAL_AUTHORITY
    return NO_AUTHORITY


def quantity_authority(c) -> str:
    """What the claim may drive: VERIFIED / PROVISIONAL / NONE. Applicability gates it: a source that is read but not
    established as applicable drives nothing."""
    if c["applicability"] != "APPLICABLE":
        return NO_AUTHORITY
    return authority(c)


def validate(c) -> list:
    """Hard checks: provenance fields present, a crop hash (64 hex) and a crop box, and a state that is the one the
    corroborations derive (a hand-edited state is rejected)."""
    v = []
    for k in REQUIRED:
        if c.get(k) in (None, "", []):
            v.append(("MISSING_FIELD", c.get("claim_id"), k))
    h = c.get("crop_hash") or ""
    if not re.fullmatch(r"[0-9a-f]{64}", h):
        v.append(("BAD_CROP_HASH", c.get("claim_id")))
    if not c.get("crop_bbox") or len(c["crop_bbox"]) != 4:
        v.append(("BAD_CROP_BBOX", c.get("claim_id")))
    try:
        st, _ = resolve_state(c)
    except ValueError as e:
        v.append(("BAD_HUMAN_VERIFICATION", c.get("claim_id"), str(e)))
        return v
    if st != c.get("source_state"):
        v.append(("STATE_NOT_DERIVED", c.get("claim_id"), c.get("source_state"), st))
    if authority({"source_state": st}) != c.get("quantity_authority"):      # from the derived state, not the stored one
        v.append(("AUTHORITY_NOT_DERIVED", c.get("claim_id")))
    return v


# ---------------------------------------------------------------------------------------------------- OCR matching
_DIA_GLYPHS = "Øø∅ΦφOo0698%#"


def ocr_pattern(token: str) -> re.Pattern:
    """A tolerant pattern for an engineering token as OCR renders stroked CAD text: the diameter glyph (Ø) may come back
    as 0 / 6 / 9 / 8 / O / %, and spaces may appear or vanish; every other digit must match exactly."""
    out = []
    for ch in token:
        if ch in "Øø∅Φφ":
            out.append(rf"\s?[{re.escape(_DIA_GLYPHS)}]?\s?")
        elif ch == " ":
            out.append(r"\s*")
        else:
            out.append(re.escape(ch))
    return re.compile(r"\s*".join(["".join(out)]), re.I)


def ocr_count(token: str, ocr_text: str) -> int:
    """How many times the token occurs in the OCR text (non-overlapping, digit-bounded so 3Ø16 does not match 13Ø16)."""
    p = ocr_pattern(token)
    n = 0
    for m in p.finditer(ocr_text or ""):
        a, b = m.start(), m.end()
        if a > 0 and ocr_text[a - 1].isdigit():
            continue
        if b < len(ocr_text) and ocr_text[b].isdigit():
            continue
        n += 1
    return n


def ocr_corroboration(ref, expected_tokens: dict, ocr_text: str, facets, engine="tesseract") -> dict:
    """OCR agrees when every expected token occurs at least the expected number of times in the crop's OCR text."""
    found = {t: ocr_count(t, ocr_text) for t in expected_tokens}
    ok = all(found[t] >= n for t, n in expected_tokens.items())
    return corroboration("OCR_TEXT", ref, ok, facets,
                         detail={"engine": engine, "expected": dict(expected_tokens), "found": found})
