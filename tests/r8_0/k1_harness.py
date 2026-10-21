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
    rows = {str(lm.handle_id(o.get("handle"))): o for o in decode.get("OBJECTS", [])}

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


def capability_register_decode(decode):
    """CAPABILITY_REGISTER target (R8.2): builder decode -> production D1 -> test-schema
    extensions -> production census (engine.source.cad.census)."""
    _, kernel, lm = _imports()
    try:
        from engine.source.cad import census
    except ModuleNotFoundError as err:
        raise TargetNotImplemented(f"CAPABILITY_REGISTER: {err.name} not implemented") from None
    doc = apply_test_schema_extensions(decode, lm.to_document(decode))
    return census.capability_register(doc)


def _modified(route):
    import copy
    dec = copy.deepcopy(route["decode"])
    for old, new in (route.get("rename") or {}).items():
        for o in dec["OBJECTS"]:
            if (o.get("object") == "BLOCK_HEADER" or o.get("type") == 49) and o.get("name") == old:
                o["name"] = new
    kind = route.get("drop_first_of")
    if kind:
        i = next(i for i, o in enumerate(dec["OBJECTS"]) if o.get("entity") == kind)
        dec["OBJECTS"].pop(i)
    return dec


def reconcile_routes(route_a, route_b):
    """RECONCILE target (R8.2): two decodes of the same synthetic source, each through the
    production D1 mapper and K1, compared by the production reconciliation (SYNTHETIC tolerance).
    The route modifiers (rename / drop_first_of) are the R8.0 fixture's own mutations."""
    _, kernel, lm = _imports()
    try:
        from engine.source import reconcile as R
    except ModuleNotFoundError as err:
        raise TargetNotImplemented(f"RECONCILE: {err.name} not implemented") from None
    docs = []
    for route in (route_a, route_b):
        dec = _modified(route)
        docs.append(apply_test_schema_extensions(dec, lm.to_document(dec)))
    ra, rb = (kernel.realise(d) for d in docs)
    return R.reconcile(ra, rb, R.SYNTHETIC, insert_blocks_a=lm.insert_blocks(docs[0]),
                       insert_blocks_b=lm.insert_blocks(docs[1]), name_a="D1/K1", name_b="D1'/K1")
