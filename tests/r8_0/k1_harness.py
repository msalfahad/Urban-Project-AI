"""Test-side adapter behind the K1_REALISE target (bound in targets.py, R8.1).

    builder decode --(PRODUCTION D1 mapper, verified fields only)--> SourceDocument
                   --(TEST-SCHEMA extensions, below)-------------->  SourceDocument
                   --(PRODUCTION K1)-------------------------------> contract dict

Every R8.0 acceptance scene therefore goes through the real D1 mapping and
the real kernel. The only thing this adapter adds is what production
deliberately refuses to guess, using the TEST BUILDER's own schema (which the
test authored, so there is nothing to verify):

  * MINSERT grid fields (num_cols / num_rows / col_spacing / row_spacing) —
    production maps MINSERT to SOURCE_MAPPING_UNVERIFIED;
  * xref flag semantics (is_xref_resolved / loaded_bit) — production records
    them as SOURCE_MAPPING_UNVERIFIED and fails closed to XREF_NOT_RESOLVED.

Contract sections K1 does not provide raise TargetNotImplemented when read
(e.g. 'flattened': a chord tolerance in mm needs a MEASUREMENT_FRAME, R8.3).
"""

from __future__ import annotations

from dataclasses import replace

from .targets import TargetNotImplemented

PENDING_SECTIONS = {
    "flattened": "flattening needs a chord tolerance in mm, i.e. an established MEASUREMENT_FRAME (R8.3); "
                 "K1 realises the exact elliptical arc instead",
}


class ContractResult(dict):
    def __missing__(self, key):
        if key in PENDING_SECTIONS:
            raise TargetNotImplemented(f"K1 contract section {key!r}: {PENDING_SECTIONS[key]}")
        raise KeyError(key)


def _imports():
    try:
        from engine.source import observations as O
        from engine.source.cad import kernel, libredwg_map
    except ModuleNotFoundError as err:
        raise TargetNotImplemented(f"K1_REALISE: {err.name} not implemented") from None
    return O, kernel, libredwg_map


def apply_test_schema_extensions(decode, doc):
    O, _, lm = _imports()
    rows = {str(lm._abs(o.get("handle"))): o for o in decode.get("OBJECTS", [])}

    def fix(obs):
        row = rows.get(obs.source_handle, {})
        if obs.kind == O.UNSUPPORTED_KIND and row.get("type") == 8:
            sc = row.get("scale") or [1.0, 1.0, 1.0]
            geom = O.InsertGeom(lm.block_key(row["block_header"]), tuple(row["ins_pt"][:2]), (sc[0], sc[1]),
                                float(row.get("rotation", 0.0)),
                                O.GridSpec(int(row["num_cols"]), int(row["num_rows"]),
                                           float(row["col_spacing"]), float(row["row_spacing"])))
            return replace(obs, kind=O.INSERT, geometry=geom, extrusion=row.get("extrusion", O.DEFAULT_EXTRUSION))
        return obs

    blocks = {}
    for key, blk in doc.blocks.items():
        hdr = rows.get(key[1:], {})
        xref = blk.xref
        if xref is not None:
            xref = replace(xref, resolved=bool(hdr.get("is_xref_resolved")), unloaded=bool(hdr.get("loaded_bit")),
                           mapping_status="TEST_SCHEMA")
        blocks[key] = replace(blk, entities=tuple(fix(e) for e in blk.entities), xref=xref)
    return replace(doc, entities=tuple(fix(e) for e in doc.entities), blocks=blocks)


def realise_decode(decode):
    _, kernel, lm = _imports()
    doc = apply_test_schema_extensions(decode, lm.to_document(decode))
    return ContractResult(kernel.realise(doc).as_contract_dict())
