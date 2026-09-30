"""Per-entity SOURCE CAPABILITY CENSUS (R8.2) — one row per thing the source engine
could not fully establish, with where it is and what it affects.

Route-neutral: takes a SourceDocument (any route) and its K1/K2 realisation.
Rows come from the kernel's findings (instance-aware: the same block entity
placed twice gives two rows with two instance paths) plus document-level
checks that need no placement (undecodable text).

Row fields: code, handle, obs_id, type_code, source_type, layer, instance_path,
reason, blocks_final (compatibility view), impacts, and per-code facts
(xref attachment, dynamic-block visibility / identity flags, text identity flag).
"""

from __future__ import annotations

from .. import findings as F
from .. import observations as O
from . import kernel as K1

DYNAMIC_CODES = (F.DYNAMIC_BLOCK_UNRESOLVED, F.DYNAMIC_BLOCK_IDENTITY_UNVERIFIED, F.ANONYMOUS_BLOCK_NO_IDENTITY)
XREF_CODES = (F.XREF_NOT_RESOLVED, F.XREF_CONTENT_NOT_IN_SOURCE, F.XREF_UNLOADED)


def _type_code(source_type):
    parts = (source_type or "").split(":")
    try:
        return int(parts[1])
    except (IndexError, ValueError):
        return None


def undecodable(text: str) -> bool:
    """Bytes the decoder could not map to characters survive as lone surrogates
    (surrogateescape) or U+FFFD; such text can never be an identity source."""
    return any(0xDC80 <= ord(ch) <= 0xDCFF or ch == "�" for ch in text or "")


def _all_observations(doc):
    for o in doc.entities:
        yield o
    for b in doc.blocks.values():
        for o in b.entities:
            yield o
    for u in doc.unplaced:
        yield u.observation
    for _, o in doc.other_layouts:
        yield o


def capability_register(document, realised=None) -> list:
    rg = realised if realised is not None else K1.realise(document)
    obs = {o.obs_id: o for o in _all_observations(document)}
    rows = []
    for f in rg.findings:
        o = obs.get(f.obs_id)
        row = {"code": f.code, "obs_id": f.obs_id, "handle": o.source_handle if o else None,
               "type_code": _type_code(o.source_type) if o else None, "source_type": o.source_type if o else None,
               "layer": o.layer if o else None, "instance_path": list(f.instance_path), "reason": f.detail,
               "blocks_final": f.blocks_final, "impacts": [{"domain": d, "severity": s} for d, s in f.impacts]}
        if f.code in XREF_CODES and o is not None and o.kind == O.INSERT:
            blk = document.blocks.get(o.geometry.block_key)
            row["attachment"] = blk.xref.attachment if blk and blk.xref else None
            row["xref_path"] = blk.xref.path if blk and blk.xref else None
        if f.code in DYNAMIC_CODES:
            row["visibility_resolved"] = False
            row["identity_claim_allowed"] = False
            row["geometry_evaluated"] = True
        rows.append(row)
    for o in obs.values():
        texts = []
        if o.kind in (O.TEXT, O.MTEXT) and isinstance(o.geometry, O.TextGeom):
            texts.append(o.geometry.value)
        if o.kind == O.INSERT:
            texts.extend(a.value for a in o.geometry.attributes)
        if any(undecodable(t) for t in texts):
            rows.append({"code": F.TEXT_UNDECODABLE, "obs_id": o.obs_id, "handle": o.source_handle,
                         "type_code": _type_code(o.source_type), "source_type": o.source_type, "layer": o.layer,
                         "instance_path": [], "reason": "text contains bytes the decoder could not map to characters",
                         "blocks_final": True, "identity_source_allowed": False,
                         "impacts": [{"domain": d, "severity": s} for d, s in F.IMPACTS[F.TEXT_UNDECODABLE]]})
    return rows
