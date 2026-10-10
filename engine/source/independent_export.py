"""INDEPENDENT EXPORT ADMISSION (R8.5 follow-up) — may this DXF serve as the independent parser route?

Two separate questions, never merged:

  1. ADMISSION — is the file what an independent route must be? Decided from the file itself and its
     declared provenance:
       * the writer recorded in the file ($LASTSAVEDBY, the 999 comment) is not a library that cannot read
         DWG (ezdxf) and is not the D1 parser family (LibreDWG): either makes it a conversion of unknown or
         correlated lineage -> DIAGNOSTIC_NONQUALIFYING_CONVERSION;
       * the declared tool is AutoCAD or the ODA File Converter (parser-independent of LibreDWG);
       * it was exported from the exact source DWG (sha256), with NO editing, exploding, purging, auditing,
         rescaling or cleaning;
       * the requested format's version is the file's $ACADVER (AutoCAD 2018 DXF -> AC1032).
     Admitted -> ADMITTED_FOR_VERIFICATION. Admission qualifies nothing.

  2. VERIFICATION — measured from the resulting file, never assumed (an ODA export is parser-independent
     but is NOT assumed to preserve every source handle):
       HANDLE_IDENTITY   every compared D1 handle exists in the DXF with the same entity type and layer
       ENTITY_CENSUS     per (owner space, type, layer) counts equal
       BLOCK_LINEAGE     named block definitions and their entity counts equal
       CUSTOM_CLASSES    every custom class the source uses is present in the export
       GEOMETRY          the K1-vs-K2 reconciliation itself (engine/source/reconcile.py), run afterwards
     A domain is VERIFIED only with zero inconsistencies among what was compared (no percentage). Only the
     signature dimensions a VERIFIED domain supports may later enter a qualification: without handle
     identity, no handle-keyed comparison is possible and the handle / reference signatures stay unqualified.
"""

from __future__ import annotations

from collections import Counter

ADMITTED_FOR_VERIFICATION = "ADMITTED_FOR_VERIFICATION"
DIAGNOSTIC_NONQUALIFYING_CONVERSION = "DIAGNOSTIC_NONQUALIFYING_CONVERSION"
REJECTED = "REJECTED"

INDEPENDENT_TOOLS = ("AUTOCAD", "ODA_FILE_CONVERTER")
NON_READER_WRITERS = ("ezdxf",)                 # libraries that cannot read DWG: something else decoded it
CORRELATED_WRITERS = ("libredwg",)              # the D1 parser family
FORBIDDEN_OPERATIONS = ("EDIT", "EXPLODE", "PURGE", "AUDIT", "RESCALE", "CLEAN", "RECOVER", "BIND", "OVERKILL")
ACADVER = {"AUTOCAD_2000_DXF": "AC1015", "AUTOCAD_2004_DXF": "AC1018", "AUTOCAD_2007_DXF": "AC1021",
           "AUTOCAD_2010_DXF": "AC1024", "AUTOCAD_2013_DXF": "AC1027", "AUTOCAD_2018_DXF": "AC1032"}
DOMAINS = ("HANDLE_IDENTITY", "ENTITY_CENSUS", "BLOCK_LINEAGE", "CUSTOM_CLASSES", "GEOMETRY")
VERIFIED, NOT_VERIFIED, NOT_RUN = "VERIFIED", "NOT_VERIFIED", "NOT_RUN"


def admission(file_sha256: str, header: dict, writer_comment: str | None, declared: dict, source_sha256: str) -> dict:
    """{status, reasons, writer, parser_independence}. `declared`: tool, tool_version, requested_format,
    exported_from_sha256, operations (list), exported_by."""
    reasons, status = [], ADMITTED_FOR_VERIFICATION
    writer = " / ".join(x for x in (str(header.get("$LASTSAVEDBY") or ""), str(writer_comment or "")) if x)
    wl = writer.lower()
    if any(w in wl for w in NON_READER_WRITERS):
        status = DIAGNOSTIC_NONQUALIFYING_CONVERSION
        reasons.append(f"written by {writer!r}: a library that cannot read DWG; the DWG decoder upstream is not in the file")
    if any(w in wl for w in CORRELATED_WRITERS):
        status = DIAGNOSTIC_NONQUALIFYING_CONVERSION
        reasons.append(f"written by {writer!r}: the D1 parser family (correlated, not independent)")
    tool = (declared.get("tool") or "").upper()
    if tool not in INDEPENDENT_TOOLS:
        status = DIAGNOSTIC_NONQUALIFYING_CONVERSION if status == ADMITTED_FOR_VERIFICATION else status
        reasons.append(f"declared tool {declared.get('tool')!r} is not AutoCAD or the ODA File Converter")
    if declared.get("exported_from_sha256") != source_sha256:
        status = REJECTED
        reasons.append("not declared as exported from the exact source DWG")
    if declared.get("operations") is None:
        status = DIAGNOSTIC_NONQUALIFYING_CONVERSION if status == ADMITTED_FOR_VERIFICATION else status
        reasons.append("export operations not documented: cannot show that nothing was edited, exploded, purged, "
                       "audited, rescaled or cleaned")
    ops = [o.upper() for o in declared.get("operations") or ()]
    bad = [o for o in ops if o in FORBIDDEN_OPERATIONS]
    if bad:
        status = REJECTED
        reasons.append(f"operations applied before / during export: {bad}")
    req = declared.get("requested_format")
    if req in ACADVER and header.get("$ACADVER") != ACADVER[req]:
        status = REJECTED
        reasons.append(f"requested {req} requires $ACADVER {ACADVER[req]}, file has {header.get('$ACADVER')!r}")
    if req and req not in ACADVER:
        reasons.append(f"requested format {req!r} has no recorded $ACADVER requirement")
    return {"file_sha256": file_sha256, "status": status, "reasons": reasons, "writer_in_file": writer,
            "declared": dict(declared),
            "parser_independence": "INDEPENDENT_PARSER" if status == ADMITTED_FOR_VERIFICATION else "NOT_ESTABLISHED",
            "qualifies_anything": False}


def _verdict(inconsistent: int, compared: int) -> str:
    return NOT_RUN if compared == 0 else (VERIFIED if inconsistent == 0 else NOT_VERIFIED)


def verify(d1_entities, dxf_entities, d1_blocks: dict, dxf_blocks: dict, d1_custom_classes, dxf_custom_classes) -> dict:
    """Measured verification of an export. Entities: iterables of dicts {handle, type, layer, space};
    blocks: {name: entity count}; custom classes: iterables of class dxfnames."""
    by_handle = {}
    for e in dxf_entities:
        by_handle.setdefault(str(e["handle"]).upper(), e)
    dxf_list = list(by_handle.values())
    mism = []
    compared = 0
    for e in d1_entities:
        compared += 1
        x = by_handle.get(str(e["handle"]).upper())
        if x is None or x["type"] != e["type"] or x["layer"] != e["layer"]:
            mism.append({"handle": e["handle"], "d1": [e["type"], e["layer"]],
                         "dxf": [x["type"], x["layer"]] if x else None})
    c1 = Counter((e["space"], e["type"], e["layer"]) for e in d1_entities)
    c2 = Counter((e["space"], e["type"], e["layer"]) for e in dxf_list)
    census = sorted({k for k in c1 | c2 if c1[k] != c2[k]})
    blocks = sorted(n for n in set(d1_blocks) | set(dxf_blocks) if n and d1_blocks.get(n) != dxf_blocks.get(n))
    missing_classes = sorted(set(d1_custom_classes) - set(dxf_custom_classes))
    out = {
        "HANDLE_IDENTITY": {"verdict": _verdict(len(mism), compared), "compared": compared, "inconsistent": len(mism),
                            "examples": mism[:10]},
        "ENTITY_CENSUS": {"verdict": _verdict(len(census), len(c1 | c2)), "differing_keys": len(census),
                          "examples": [[list(k), c1[k], c2[k]] for k in census[:10]]},
        "BLOCK_LINEAGE": {"verdict": _verdict(len(blocks), len(set(d1_blocks) | set(dxf_blocks))),
                          "differing_blocks": len(blocks), "examples": blocks[:10]},
        "CUSTOM_CLASSES": {"verdict": _verdict(len(missing_classes), len(set(d1_custom_classes))),
                           "missing": missing_classes},
        "GEOMETRY": {"verdict": NOT_RUN, "note": "K1-vs-K2 reconciliation runs only after admission"},
    }
    out["handle_keyed_comparison_possible"] = out["HANDLE_IDENTITY"]["verdict"] == VERIFIED
    return out


# ====================================================================== V2 (R8.6A): writer, decoder, revision, scoped states
# The three facts a DXF carries are kept apart and never inferred from one another:
#   DXF_WRITER                  what wrote the DXF bytes (measured from the file's own fingerprint)
#   DWG_DECODER                 what read the DWG (provable only from a conversion record with evidence)
#   SOURCE_METADATA_LASTSAVEDBY the $LASTSAVEDBY string the DWG already carried (a user name, not a tool)
PROVENANCE_UNVERIFIED = "PROVENANCE_UNVERIFIED"          # no known non-qualifying writer, but the decoder is unproven
DECODER_STATES = ("AUTOCAD_PROVEN", "ODA_FILE_CONVERTER_PROVEN", "OTHER_INDEPENDENT_DWG_PARSER_PROVEN",
                  "LIBREDWG_LINEAGE_PROVEN", "SHARED_OR_DEPENDENT_LINEAGE", "CONVERTER_UNKNOWN")
INDEPENDENT_DECODER_STATES = DECODER_STATES[:3]
WRITER_EZDXF, WRITER_LIBREDWG = "EZDXF_WRITER", "LIBREDWG_WRITER"
WRITER_AUTOCAD_ODA_FORMAT = "AUTOCAD_OR_ODA_FAMILY_FORMAT"     # formatting family only: never names the decoder
WRITER_UNKNOWN = "WRITER_UNKNOWN"
SAME_REVISION = "SAME_REVISION"
SAME_LINEAGE_DIFFERENT_REVISION = "SAME_LINEAGE_DIFFERENT_REVISION"
UNRELATED_SOURCE = "UNRELATED_SOURCE"
REVISION_NOT_ESTABLISHED = "REVISION_NOT_ESTABLISHED"
PROVENANCE_NOT_INDEPENDENT = "PROVENANCE_NOT_INDEPENDENT"


def writer_fingerprint(header: dict, comments=(), sections=(), maintver_group_code=None) -> dict:
    """What the DXF's own bytes say about its writer. Rules are observations of known writers, not guesses:
    ezdxf stamps $LASTSAVEDBY 'ezdxf'; LibreDWG writes a '999 LibreDWG <version>' comment and copies the DWG's
    maintenance version with group code 70; AutoCAD and ODA-based writers emit an ACDSDATA section and, for
    AC1032, $ACADMAINTVER with group code 90. The last class names a FORMAT FAMILY: it cannot tell AutoCAD from
    an ODA-based tool, and it says nothing about which library decoded the DWG."""
    text = " ".join(str(c) for c in comments).lower()
    saved = str(header.get("$LASTSAVEDBY") or "")
    evidence = []
    if "ezdxf" in saved.lower() or "ezdxf" in text:
        cls = WRITER_EZDXF
        evidence.append("$LASTSAVEDBY / comment names ezdxf")
    elif "libredwg" in text:
        cls = WRITER_LIBREDWG
        evidence.append("999 comment names LibreDWG")
    elif "ACDSDATA" in sections and maintver_group_code == 90:
        cls = WRITER_AUTOCAD_ODA_FORMAT
        evidence += ["ACDSDATA section present", "$ACADMAINTVER written with group code 90"]
    else:
        cls = WRITER_UNKNOWN
    return {"class": cls, "evidence": evidence, "source_metadata_lastsavedby": saved or None,
            "note": "the writer class never establishes the DWG decoder"}


def decoder_provenance(writer: dict, conversion_record: dict | None = None) -> dict:
    """DWG_DECODER state. Only a conversion record with hashed evidence (log, tool output) can PROVE a decoder;
    a writer fingerprint alone can only prove LibreDWG lineage (its own stamp) or leave the decoder UNKNOWN."""
    rec = conversion_record or {}
    tool, ev = (rec.get("tool") or "").upper(), rec.get("evidence_sha256")
    if writer["class"] == WRITER_LIBREDWG:
        state = "LIBREDWG_LINEAGE_PROVEN"
    elif tool == "AUTOCAD" and ev:
        state = "AUTOCAD_PROVEN"
    elif tool == "ODA_FILE_CONVERTER" and ev:
        state = "ODA_FILE_CONVERTER_PROVEN"
    elif tool and ev and rec.get("independent_of_libredwg") is True:
        state = "OTHER_INDEPENDENT_DWG_PARSER_PROVEN"
    elif rec.get("shares_libredwg") is True:
        state = "SHARED_OR_DEPENDENT_LINEAGE"
    else:
        state = "CONVERTER_UNKNOWN"
    return {"state": state, "independent": state in INDEPENDENT_DECODER_STATES,
            "basis": ("conversion record with hashed evidence" if ev else
                      "writer stamp" if state == "LIBREDWG_LINEAGE_PROVEN" else "no conversion record")}


def revision_identity(source_header: dict, dxf_header: dict, source_entities_missing: int,
                      entities_added_in_scope: int) -> dict:
    """Is the DXF an export of THIS DWG revision? Drawing lineage (FINGERPRINTGUID) is necessary, not
    sufficient: the source's own entities must all be present, and no entity may be added inside the scope.
    VERSIONGUID equality is recorded as supporting evidence only (some writers renew it on save)."""
    fs, fd = source_header.get("FINGERPRINTGUID"), dxf_header.get("$FINGERPRINTGUID")
    vs, vd = source_header.get("VERSIONGUID"), dxf_header.get("$VERSIONGUID")
    if not fs or not fd:
        state = REVISION_NOT_ESTABLISHED
    elif fs != fd:
        state = UNRELATED_SOURCE
    elif source_entities_missing == 0 and entities_added_in_scope == 0:
        state = SAME_REVISION
    else:
        state = SAME_LINEAGE_DIFFERENT_REVISION
    return {"state": state, "fingerprintguid_equal": bool(fs) and fs == fd, "versionguid_equal": bool(vs) and vs == vd,
            "source_entities_missing": source_entities_missing, "entities_added_in_scope": entities_added_in_scope}


def admission_v2(file_sha256: str, header: dict, writer: dict, decoder: dict, revision: dict,
                 declared: dict, source_sha256: str) -> dict:
    """V2 admission. Order of checks: revision (is it the exact source at all), writer, decoder, operations,
    version. Admission still qualifies nothing."""
    reasons, status = [], ADMITTED_FOR_VERIFICATION
    if revision["state"] != SAME_REVISION:
        status = REJECTED
        reasons.append(f"SOURCE_REVISION_MISMATCH: {revision['state']} (missing source entities "
                       f"{revision['source_entities_missing']}, added in scope {revision['entities_added_in_scope']})")
    if writer["class"] in (WRITER_EZDXF, WRITER_LIBREDWG):
        status = DIAGNOSTIC_NONQUALIFYING_CONVERSION if status != REJECTED else status
        reasons.append(f"writer {writer['class']}: not an independent route")
    if not decoder["independent"]:
        if status == ADMITTED_FOR_VERIFICATION:
            status = PROVENANCE_UNVERIFIED
        reasons.append(f"DWG decoder {decoder['state']}: parser independence not established")
    ops = declared.get("operations")
    if ops is None:
        reasons.append("export operations not documented")
        if status == ADMITTED_FOR_VERIFICATION:
            status = PROVENANCE_UNVERIFIED
    elif any(o.upper() in FORBIDDEN_OPERATIONS for o in ops):
        status = REJECTED
        reasons.append(f"forbidden operations {ops}")
    req = declared.get("requested_format")
    if req in ACADVER and header.get("$ACADVER") != ACADVER[req]:
        status = REJECTED
        reasons.append(f"requested {req} requires $ACADVER {ACADVER[req]}, file has {header.get('$ACADVER')!r}")
    return {"file_sha256": file_sha256, "source_sha256": source_sha256, "status": status, "reasons": reasons,
            "DXF_WRITER": writer["class"], "DWG_DECODER": decoder["state"],
            "SOURCE_METADATA_LASTSAVEDBY": writer.get("source_metadata_lastsavedby"),
            "revision": revision["state"],
            "parser_independence": "INDEPENDENT_PARSER" if status == ADMITTED_FOR_VERIFICATION else "NOT_ESTABLISHED",
            "qualifies_anything": False}


def scoped_signature_states(diagnostic_states: dict, admission: dict) -> dict:
    """{signature: state}. A diagnostic reconciliation of a route that is not admitted never yields a
    qualification state: every signature reads PROVENANCE_NOT_INDEPENDENT, the diagnostic outcome kept beside it."""
    if admission["status"] == ADMITTED_FOR_VERIFICATION:
        return {s: {"state": st, "diagnostic": st} for s, st in diagnostic_states.items()}
    return {s: {"state": PROVENANCE_NOT_INDEPENDENT, "diagnostic": st} for s, st in diagnostic_states.items()}
