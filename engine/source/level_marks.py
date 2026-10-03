"""LEVEL MARK UNIT EVIDENCE (V1) - authored level annotations of ONE elevation / section view as unit evidence.

A level annotation states a height in metres ('+5.50', '%%p0.00'). In one view drawn full size, two marks of different
value lie (value_b - value_a) metres apart vertically, so their native distance gives millimetres per native unit:
    native_to_mm = (value_b - value_a) * 1000 / (y_b - y_a)
The marks must be the same annotation family (same layer, same text height) so the text-to-level-line offset cancels.

view_evidence() returns one frame.UnitEvidence of kind SECTION_ELEVATION_DIMENSION (failure-domain family
DOCUMENT_SOURCE of that drawing) when every pair agrees; pairs that disagree are ALL returned as separate items of
the SAME lineage, so the frozen frame rule reads them as ONE_LINEAGE_DISAGREES_WITH_ITSELF (a conflict, never an
average). A view with fewer than two distinct values yields nothing. The resolver decides the status (frame.py).

Project-agnostic; stdlib only.
"""

from __future__ import annotations

import re

from . import frame as FR

POLICY_ID = "LEVEL_MARK_UNIT_EVIDENCE_V1"
_LEVEL = re.compile(r"^\s*(%%p|%%P|±|\+|-)\s*(\d+(?:\.\d+)?)\s*$|^\s*()(\d+\.\d{2})\s*$")


def parse_level(text):
    """metres or None. '%%p0.00' / '+1.00' / '-0.50' / '5.50' (a bare number needs exactly two decimals: '3700' or
    '1:100' is never a level)."""
    if text is None:
        return None
    m = _LEVEL.match(text)
    if not m:
        return None
    sign, val = (m.group(1), m.group(2)) if m.group(2) is not None else (m.group(3), m.group(4))
    v = float(val)
    return -v if sign == "-" else v


def view_evidence(marks, *, view_id: str, source_sha256: str, space_id: str = "MODEL_SPACE") -> dict:
    """marks [{"key", "text", "y", "layer", "height"}] of one view."""
    parsed = [dict(m, value_m=parse_level(m["text"])) for m in marks]
    rejected = [m["key"] for m in parsed if m["value_m"] is None]
    ok = [m for m in parsed if m["value_m"] is not None]
    fams = {(m["layer"], m["height"]) for m in ok}
    out = {"policy": POLICY_ID, "view": view_id, "marks": len(ok), "rejected": rejected, "families": sorted(map(str, fams)),
           "pairs": [], "evidence": []}
    if len(fams) != 1:
        out["state"] = "MIXED_ANNOTATION_FAMILIES" if fams else "NO_MARKS"
        return out
    by = {}
    for m in ok:
        by.setdefault(m["value_m"], []).append(m)
    for v, ms in by.items():
        if max(x["y"] for x in ms) - min(x["y"] for x in ms) > 1e-6 * max(1.0, abs(ms[0]["y"])):
            out["state"] = "SAME_VALUE_AT_DIFFERENT_HEIGHTS"
            out["conflict_value"] = v
            return out
    vals = sorted(by)
    if len(vals) < 2:
        out["state"] = "FEWER_THAN_TWO_VALUES"
        return out
    lineage = (FR.family_lineage(FR.SECTION_ELEVATION_DIMENSION, source_sha256), f"AUTHORED:LEVEL_MARKS:{view_id}")
    derived = []
    for i in range(len(vals)):
        for j in range(i + 1, len(vals)):
            a, b = by[vals[i]][0], by[vals[j]][0]
            dy = b["y"] - a["y"]
            d = (vals[j] - vals[i]) * 1000.0 / dy if dy else None
            out["pairs"].append({"a": [a["key"], vals[i]], "b": [b["key"], vals[j]], "dy_native": dy,
                                 "native_to_mm": d})
            if d is not None:
                derived.append(d)
    if not derived or any(x <= 0 for x in derived):
        out["state"] = "INVERTED_OR_FLAT_MARKS"
        return out
    distinct = []
    for d in derived:
        if not any(abs(d - e) / e <= FR.AGREEMENT_REL for e in distinct):
            distinct.append(d)
    for k, d in enumerate(distinct):
        out["evidence"].append(FR.UnitEvidence(f"LEVEL_MARKS:{view_id}:{k}", FR.NATIVE_UNIT, FR.SECTION_ELEVATION_DIMENSION,
                                               space_id, lineage, derived_value=d, observed_value=len(derived),
                                               source_ref=view_id, source_sha256=source_sha256, unit="m"))
    out["state"] = "AGREE" if len(distinct) == 1 else "PAIRS_DISAGREE"
    return out


def policy_record() -> dict:
    return {"policy_id": POLICY_ID, "kind": FR.SECTION_ELEVATION_DIMENSION, "agreement_rel": FR.AGREEMENT_REL,
            "requires": "one view, one annotation family (layer + text height), >= 2 distinct values",
            "never": ["an average of disagreeing pairs", "a plan level tag (no vertical axis)", "a status set here"]}


# ======================================================================== A2: cross-document plot sides
_PLOT_VALUE = re.compile(r"^\s*(\d{1,3}\.\d{2})\s*$")


def plot_side_values(texts) -> list:
    """Printed site-side values: a bare number with exactly two decimals (the metre-to-centimetre convention of
    site / plot dimensions). [(value_m, text key)] - sorted, duplicates kept (each is one printed occurrence)."""
    out = []
    for key, value in texts:
        m = _PLOT_VALUE.match(value or "")
        if m:
            out.append((float(m.group(1)), key))
    return sorted(out)


def cross_document_plot_evidence(printed, rectangles, *, printed_sha256: str, drawing_sha256: str,
                                 evidence_id: str, space_id: str = "MODEL_SPACE") -> dict:
    """OTHER_SOURCE_DOCUMENT unit evidence: a closed rectangle drawn in THIS drawing whose two side lengths are
    printed (as metre values) in ANOTHER document, with ONE ratio for both sides (agreement <= frame.AGREEMENT_REL).
    printed     [(value_m, key)] from the other document (plot_side_values)
    rectangles  [{"width", "height", "edge_keys"}] native, from this drawing
    The metre reading of a two-decimal site value is a stated CONVENTION (recorded); the two printed values must be
    DISTINCT (a square rectangle gives no evidence); a rectangle matching only one printed value gives none; matches
    at different ratios are a contradiction (RATIOS_DISAGREE), never averaged. The family lineage is the OTHER
    document's (EXTERNAL_DOCUMENT), so it is independent of this drawing's own annotation."""
    vals = sorted({v for v, _ in printed if v > 0})
    hits = []
    for r in rectangles:
        w, h = sorted((r["width"], r["height"]))
        if w <= 0 or w == h:
            continue                                   # a square cannot tell which printed side is which
        for i, a in enumerate(vals):
            for b in vals[i + 1:]:                     # two DISTINCT printed sides, short with short
                k1, k2 = a * 1000.0 / w, b * 1000.0 / h
                if abs(k1 - k2) <= FR.AGREEMENT_REL * max(k1, k2):
                    hits.append({"rect": r.get("edge_keys", [])[:8], "sides_native": [w, h], "printed_m": [a, b],
                                 "mm_per_native": (k1 + k2) / 2.0})
    ratios = sorted({round(h_["mm_per_native"], 9) for h_ in hits})
    state = "NO_MATCH" if not hits else ("AGREE" if all(abs(r - ratios[0]) <= FR.AGREEMENT_REL * ratios[0]
                                                        for r in ratios) else "RATIOS_DISAGREE")
    ev = []
    if state == "AGREE":
        ev.append(FR.UnitEvidence(evidence_id, FR.NATIVE_UNIT, FR.OTHER_SOURCE_DOCUMENT, space_id,
                                  (FR.family_lineage(FR.OTHER_SOURCE_DOCUMENT, printed_sha256),
                                   "AUTHORED:PRINTED_PLOT_SIDES", "DRAWN:" + str(drawing_sha256)),
                                  derived_value=ratios[0], observed_value=len(hits), source_ref="PLOT_SIDES",
                                  source_sha256=printed_sha256, unit="m",
                                  notes="convention: a two-decimal site / plot side value is metres"))
    return {"state": state, "matches": hits, "ratios": ratios, "evidence": ev,
            "convention": "two-decimal site value = metres (recorded, not hidden)"}
