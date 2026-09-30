"""DECODER_BINARY_PIN registry (R8 A9) — which decoder builds may support FINAL provenance.

A pin is the sha256 of the exact executable (or the package identity of a
library). A route that ran a build NOT registered here may still run in
research, but its anchor says UNREGISTERED_BUILD and it may not support FINAL
provenance. A decode whose producing binary was not hashed when it ran is
NOT_ESTABLISHED: the version string it carries is recorded, never upgraded to
a pin.

Registered entries were hashed in this repository's working environment on
the date shown; nothing here is copied from a vendor listing.
"""

from __future__ import annotations

REGISTERED = "REGISTERED"
UNREGISTERED_BUILD = "UNREGISTERED_BUILD"
NOT_ESTABLISHED = "NOT_ESTABLISHED"

PINS = {
    "LIBREDWG_DWGREAD": [
        {"version": "0.13.3", "sha256": "fe49cf28f5ee5cd84cbb7b9c7ae0475586cedbfcb1a9ca9bc2cab8c72e094c47",
         "hashed": "2026-09-30", "note": "self-built binary found at /tmp/ldwg/programs/dwgread; build flags unrecorded"},
    ],
    "LIBREDWG_DWG2DXF": [
        {"version": "0.13.3", "sha256": "a70027ade23956e86f2f5926faa40c73801ff85a4be88e850673d81972eaebca",
         "hashed": "2026-09-30", "note": "same build tree as dwgread"},
    ],
    "EZDXF": [
        {"version": "1.4.4", "sha256": None, "hashed": "2026-09-30",
         "note": "Python package; identity is the installed distribution version (no single binary)"},
    ],
}


def status(tool: str, sha256: str | None) -> str:
    if not sha256:
        return NOT_ESTABLISHED
    return REGISTERED if any(p["sha256"] == sha256 for p in PINS.get(tool, ())) else UNREGISTERED_BUILD


def package_status(tool: str, version: str | None) -> str:
    """For libraries pinned by distribution version, not by a binary hash."""
    if not version:
        return NOT_ESTABLISHED
    return REGISTERED if any(p["version"] == version and p["sha256"] is None for p in PINS.get(tool, ())) \
        else UNREGISTERED_BUILD
