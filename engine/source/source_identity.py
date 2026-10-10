"""SOURCE IDENTITY - is a re-supplied file the same source as one registered earlier (generic).

A file whose SHA-256 differs from a registered one may still carry the same drawing. For a classic-xref PDF whose only
change is extra entries in its document-information dictionary (a title or subject added when it was re-saved or
split), removing exactly those entries and shifting the cross-reference offsets back must reproduce the registered
bytes. If it does, the two files are the same source apart from wrapper metadata; if it does not, they are different
sources until shown otherwise.

    strip_info_entries(pdf_bytes, keys)        the bytes with those /Info entries removed and offsets restored
    relation(new_bytes, registered_sha, keys)  IDENTICAL | WRAPPER_METADATA_ONLY | DIFFERENT, with the evidence

Stdlib only. Bytes are handled as data: nothing in the file is executed or interpreted beyond the PDF syntax used.
"""

from __future__ import annotations

import hashlib
import re

IDENTICAL = "IDENTICAL"
WRAPPER_METADATA_ONLY = "WRAPPER_METADATA_ONLY"
DIFFERENT = "DIFFERENT"


class SourceIdentityError(ValueError):
    pass


def sha256(b):
    return hashlib.sha256(b).hexdigest()


def _info_span(b):
    tr = b[b.rfind(b"trailer"):]
    m = re.search(rb"/Info\s+(\d+)\s+(\d+)\s+R", tr)
    if not m:
        raise SourceIdentityError("no /Info reference in the trailer")
    om = re.search(rb"(?:^|\n)" + m.group(1) + rb"\s+" + m.group(2) + rb"\s+obj\s*(.*?)endobj", b, re.S)
    if not om:
        raise SourceIdentityError("the /Info object is not a plain indirect object")
    return om.start(1), om.end(1)


def strip_info_entries(b, keys):
    """Remove /Key (literal string) entries, each on its own line, from the /Info dictionary; shift every
    cross-reference offset after it and startxref by the bytes removed. Needs a classic xref table."""
    start, end = _info_span(b)
    info = b[start:end]
    pat = b"|".join(re.escape(k.encode()) for k in keys)
    stripped = re.sub(rb"(?:" + pat + rb")\s*\((?:\\.|[^\\)])*\)\n", b"", info, flags=re.S)
    delta = len(info) - len(stripped)
    nb = b[:start] + stripped + b[end:]
    xi = nb.rfind(b"\nxref")
    if xi < 0:
        raise SourceIdentityError("no classic xref table (cross-reference streams are not handled)")
    head, xref = nb[:xi], nb[xi:]

    def fix(mm):
        off = int(mm.group(1))
        return (b"%010d" % (off - delta if off > start else off)) + mm.group(2)
    xref = re.sub(rb"(\d{10})( \d{5} n)", fix, xref)
    sx = re.search(rb"startxref\s+(\d+)", xref)
    if not sx:
        raise SourceIdentityError("no startxref")
    xref = xref[:sx.start(1)] + str(int(sx.group(1)) - delta).encode() + xref[sx.end(1):]
    return head + xref, delta


def relation(new_bytes, registered_sha, keys=("/Title", "/Subject")):
    new_sha = sha256(new_bytes)
    if new_sha == registered_sha:
        return {"relation": IDENTICAL, "new_sha256": new_sha, "removed_bytes": 0, "reconstructed_sha256": new_sha}
    try:
        rec, delta = strip_info_entries(new_bytes, keys)
    except SourceIdentityError as e:
        return {"relation": DIFFERENT, "new_sha256": new_sha, "removed_bytes": None, "reconstructed_sha256": None,
                "why": str(e)}
    rs = sha256(rec)
    return {"relation": WRAPPER_METADATA_ONLY if rs == registered_sha and delta > 0 else DIFFERENT,
            "new_sha256": new_sha, "removed_bytes": delta, "reconstructed_sha256": rs}
