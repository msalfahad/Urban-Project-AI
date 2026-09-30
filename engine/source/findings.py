"""Source findings — what the source engine could not establish, said out loud.

A separate record type earns its place because three producers already emit
the same shape: the decoder mapping (a field it cannot map), K1 (a frame it
cannot realise, an xref it cannot see into) and, from R8.2, the capability
census. Downstream (qs_core) decides what a finding blocks; the source engine
only states whether the affected observation may support a FINAL quantity.

SOURCE UNCERTAINTY -> VISIBLE FINDING, never -> a silent default.
"""

from __future__ import annotations

from dataclasses import dataclass

# frame
FRAME_UNREADABLE = "FRAME_UNREADABLE"
UNSUPPORTED_FRAME = "UNSUPPORTED_FRAME"
# curves
NON_UNIFORM_SCALE_CURVE = "NON_UNIFORM_SCALE_CURVE"
KERNEL_ORIENTATION_INCONSISTENT = "KERNEL_ORIENTATION_INCONSISTENT"
DEGENERATE_GEOMETRY = "DEGENERATE_GEOMETRY"
# blocks
MISSING_BLOCK_DEFINITION = "MISSING_BLOCK_DEFINITION"
BLOCK_NAME_UNREADABLE = "BLOCK_NAME_UNREADABLE"
NESTING_LIMIT = "NESTING_LIMIT"
# xref (codes frozen by R8.0 fixtures F08; "XREF_UNRESOLVED" in the R8.1 brief == XREF_NOT_RESOLVED)
XREF_NOT_RESOLVED = "XREF_NOT_RESOLVED"
XREF_CONTENT_NOT_IN_SOURCE = "XREF_CONTENT_NOT_IN_SOURCE"
XREF_UNLOADED = "XREF_UNLOADED"
# entities the kernel does not realise
UNHANDLED = "UNHANDLED"
SKIPPED = "SKIPPED"
PROXY = "PROXY"
CUSTOM_CLASS = "CUSTOM_CLASS"
UNSUPPORTED = "UNSUPPORTED"
SOURCE_MAPPING_UNVERIFIED = "SOURCE_MAPPING_UNVERIFIED"
SOURCE_TYPE_CONFLICT = "SOURCE_TYPE_CONFLICT"
# ownership
OWNER_UNRESOLVED = "OWNER_UNRESOLVED"

ENTITY_CATEGORIES = (UNHANDLED, SKIPPED, PROXY, CUSTOM_CLASS, UNSUPPORTED,
                     SOURCE_MAPPING_UNVERIFIED, SOURCE_TYPE_CONFLICT)

# Findings that describe a fact without blocking the observation they name.
NON_BLOCKING = frozenset({NON_UNIFORM_SCALE_CURVE, OWNER_UNRESOLVED})


@dataclass(frozen=True)
class SourceFinding:
    code: str
    obs_id: str | None = None
    instance_path: tuple = ()
    detail: str = ""

    @property
    def blocks_final(self) -> bool:
        return self.code not in NON_BLOCKING

    def as_dict(self) -> dict:
        return {"code": self.code, "obs_id": self.obs_id, "instance_path": list(self.instance_path),
                "blocks_final": self.blocks_final, "detail": self.detail}
