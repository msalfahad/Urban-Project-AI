"""Deterministic unit / scale EVIDENCE from a D1 (LibreDWG JSON) decode — R8.3 §16.

This module EMITS EVIDENCE. It never chooses a unit: engine/source/frame.py (the resolver)
calculates UNIT_CONTEXT status from what is emitted here.

Emitted per coordinate space (model space):

  DECLARATION   $INSUNITS read from the header (frame.declaration_evidence). Never physical truth.
  CANDIDATE     one DIMENSION family per effective display/geometry ratio. LibreDWG's stored
                act_measurement already includes DIMLFAC, so act_measurement / defpoint distance is
                the effective display factor r. A display value is a number in SOME display unit
                the drawing does not state; each standard display unit u gives one native
                interpretation  native_to_mm = r * mm(u).  The family therefore constrains the unit
                to a SET, and rests on ASSUMPTION:DISPLAY_IN_STANDARD_UNIT — it is candidate-only.
                It can contradict (a declaration outside every family's set) or narrow; set
                membership is never support (R8.3 review §3-§4).
  SCALE NOTES   literal "1:100" / "1/100" texts, recorded as observations (a plot/sheet scale is
                not a model-space local scale). Several distinct ratios in one unsegmented space
                raise REGION_MIXED_SCALE_NOTES.
  CHECKED DIMENSIONS  every family's dimensions with stored measurement vs own geometry, as a
                residual census (unit-free).

No project value is read or targeted; the display-unit list is the standard CAD unit list.
"""

from __future__ import annotations

import math
import re
from collections import defaultdict

from .. import frame as FR
from ..findings import SourceFinding
from .. import findings as F

STANDARD_DISPLAY_UNITS = (("mm", 1.0), ("cm", 10.0), ("m", 1000.0), ("in", 25.4), ("ft", 304.8))
DIM_TYPES = (20, 21, 22)                  # ordinate, linear (rotated), aligned
SCALE_NOTE = re.compile(r"(?<![\d.])1\s*[:/]\s*(\d{1,5})(?![\d.])")


def _h(ref):
    return f"{ref[1]}:{ref[-1]}" if isinstance(ref, list) and ref else None


def _dim_length(o):
    a, b = o.get("xline1_pt"), o.get("xline2_pt")
    if not a or not b:
        return None
    if o.get("type") == 21 or o.get("_subclass") == "AcDbRotatedDimension":
        r = float(o.get("dim_rotation", 0.0) or 0.0)
        return abs((b[0] - a[0]) * math.cos(r) + (b[1] - a[1]) * math.sin(r))
    return math.hypot(b[0] - a[0], b[1] - a[1])


def dimension_families(decode) -> list:
    """Group dimensions by effective display factor r = act_measurement / geometry (6 s.f.)."""
    objs = decode.get("OBJECTS", [])
    styles = {tuple(o["handle"][1:]): (o.get("name"), o.get("DIMLFAC"))
              for o in objs if o.get("object") == "DIMSTYLE" and isinstance(o.get("handle"), list)}
    fam = defaultdict(list)
    for o in objs:
        if o.get("type") not in DIM_TYPES or "act_measurement" not in o:
            continue
        L = _dim_length(o)
        if not L or L < 1e-12:
            continue
        r = float(f"{o['act_measurement'] / L:.6g}")
        ds = o.get("dimstyle")
        name, lfac = styles.get((ds[1], ds[3]) if isinstance(ds, list) and len(ds) >= 4 else None, (None, None))
        fam[r].append({"handle": _h(o.get("handle")), "type_code": o.get("type"), "entmode": o.get("entmode"),
                       "literal_act_measurement": o["act_measurement"], "geometry_native": L,
                       "dimstyle": name, "dimstyle_DIMLFAC": lfac, "user_text": o.get("user_text") or ""})
    out = []
    for r, members in sorted(fam.items()):
        out.append({"ratio": r, "count": len(members),
                    "styles": sorted({(m["dimstyle"], m["dimstyle_DIMLFAC"]) for m in members}, key=str),
                    "interpretations": [{"display_unit": u, "native_to_mm": r * mm} for u, mm in STANDARD_DISPLAY_UNITS],
                    "members": members})
    return out


def scale_notes(decode) -> list:
    notes = []
    for o in decode.get("OBJECTS", []):
        if o.get("type") not in (1, 44):
            continue
        t = o.get("text_value") if o.get("type") == 1 else o.get("text")
        if not isinstance(t, str):
            continue
        for m in SCALE_NOTE.finditer(t):
            notes.append({"handle": _h(o.get("handle")), "literal": t.strip()[:80], "denominator": int(m.group(1)),
                          "entmode": o.get("entmode")})
    return notes


def extract(decode, source_sha256: str, space_id: str = "MODEL_SPACE", parser: str = "LIBREDWG") -> dict:
    """{evidence: [UnitEvidence], rows: [...], findings: [...], families, scale_notes}."""
    hdr = decode.get("HEADER", {})
    rows, evidence, findings = [], [], []
    decl, f = FR.declaration_evidence(hdr.get("INSUNITS"), space_id, source_sha256, parser)
    if f:
        findings.append(f)
    for e in decl:
        evidence.append(e)
        rows.append({"evidence_id": e.evidence_id, "role": "DECLARATION", "kind": e.kind, "source_handle": "HEADER",
                     "literal": hdr.get("INSUNITS"), "parsed": e.unit, "native_to_mm": e.derived_value,
                     "lineage": list(e.lineage), "scope": space_id})
    fams = dimension_families(decode)
    for fam in fams:
        eid = f"{space_id}:DIMFAMILY:r={fam['ratio']:g}"
        lineage = tuple(sorted({f"AUTHORED:{source_sha256}:DIMSTYLE:{s[0]}" for s in fam["styles"]})) + (
            FR.family_lineage(FR.DIMENSION_STYLE, source_sha256), f"PARSER:{parser}",
            "ASSUMPTION:DISPLAY_IN_STANDARD_UNIT")
        vals = tuple(i["native_to_mm"] for i in fam["interpretations"])
        e = FR.UnitEvidence(eid, FR.NATIVE_UNIT, FR.DIMENSION_STYLE, space_id, lineage, None,
                            observed_value={"ratio": fam["ratio"], "count": fam["count"]},
                            source_ref=",".join(m["handle"] for m in fam["members"][:20]),
                            source_sha256=source_sha256, producer=FR.ENGINE, review_status=FR.CANDIDATE,
                            notes="display / geometry ratio; display unit not authored", derived_set=vals)
        evidence.append(e)
        rows.append({"evidence_id": eid, "role": "CANDIDATE", "kind": e.kind,
                     "source_handles": [m["handle"] for m in fam["members"]], "count": fam["count"],
                     "literal": [m["literal_act_measurement"] for m in fam["members"][:5]],
                     "geometry_native": [m["geometry_native"] for m in fam["members"][:5]],
                     "parsed_ratio": fam["ratio"], "dimstyle_relationship": fam["styles"],
                     "possible_interpretations": fam["interpretations"], "lineage": list(lineage), "scope": space_id})
    notes = scale_notes(decode)
    denoms = sorted({n["denominator"] for n in notes})
    if len(denoms) > 1:
        findings.append(SourceFinding(F.REGION_MIXED_SCALE_NOTES, None, (),
                                      f"{space_id}: scale notes 1:" + ", 1:".join(map(str, denoms)) + " in one unsegmented space",
                                      scope=space_id))
    if len(fams) > 1:
        findings.append(SourceFinding(F.REGION_MIXED_SCALE_NOTES, None, (),
                                      f"{space_id}: {len(fams)} dimension families with different display factors "
                                      "(" + ", ".join(format(x["ratio"], "g") for x in fams) + ") in one unsegmented space",
                                      scope=space_id))
    return {"evidence": evidence, "rows": rows, "findings": findings, "families": fams, "scale_notes": notes}
