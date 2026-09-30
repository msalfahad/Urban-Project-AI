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
REPRODUCED_BY_REGISTERED_BUILD = "REPRODUCED_BY_REGISTERED_BUILD"

PINS = {
    "LIBREDWG_DWGREAD": [
        {"version": "0.13.3", "sha256": "fe49cf28f5ee5cd84cbb7b9c7ae0475586cedbfcb1a9ca9bc2cab8c72e094c47",
         "hashed": "2026-09-30", "note": "self-built binary at /tmp/ldwg/programs/dwgread",
         "build_provenance": {"status": "BUILD_CONFIGURATION_NOT_FULLY_RECORDED",
                              "configure": "./configure --disable-bindings --disable-shared --enable-static "
                                           "--disable-dependency-tracking",
                              "CC": "gcc", "CFLAGS": "-g -O2", "host": "x86_64-pc-linux-gnu",
                              "source": "/tmp/ldwg/config.log (sha256 a9fd454c...); compiler version, libc and "
                                        "source tarball hash not recorded"}},
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


# A historical decode made before its binary was hashed is NOT_ESTABLISHED. It becomes
# REPRODUCED_BY_REGISTERED_BUILD only when a pinned re-decode of the same DWG bytes by a
# REGISTERED build reproduces it: byte-identical, or identical after a documented
# normalisation. Recorded by research/external_engine_lab/r8_3_pinned_redecode.py (R8.3).
# Keyed by hashes only: production code names no project.
REPRODUCTIONS = {
    "c742657fab496d554c1f04480ce9dcf3d7b331033e625f0cc14e6f50de7ab49b": {
        "dwg_sha256": "7f61f3acdd62d62dc745f8b522f8136cb41c575df36ec6d9f27c2fe48fea41e3",
        "tool": "LIBREDWG_DWGREAD", "binary_sha256": "fe49cf28f5ee5cd84cbb7b9c7ae0475586cedbfcb1a9ca9bc2cab8c72e094c47",
        "match": "BYTE_IDENTICAL", "reproduced": "2026-09-30"},
    "7dbafb3ddd59076664f05c2f3c539d3133b295002c90e3f6f26ffd01737d5e36": {
        "dwg_sha256": "2ec3a9c8b66eb2e129275b87010f4a8d79d7e5bdcc31c1897c14fd7e5647d355",
        "tool": "LIBREDWG_DWGREAD", "binary_sha256": "fe49cf28f5ee5cd84cbb7b9c7ae0475586cedbfcb1a9ca9bc2cab8c72e094c47",
        "match": "BYTE_IDENTICAL", "reproduced": "2026-09-30"},
    "4196c03d6feae645c82c47f36bfdeaa3ccbff86af6676c1289dcec9e01358851": {
        "dwg_sha256": "299c61b1df7660384e027d44c0a29d8b64c92995843c0517cea05d485974660c",
        "tool": "LIBREDWG_DWGREAD", "binary_sha256": "fe49cf28f5ee5cd84cbb7b9c7ae0475586cedbfcb1a9ca9bc2cab8c72e094c47",
        "match": "IDENTICAL_AFTER_UTF8_REPLACEMENT",
        "normalisation": "40 invalid UTF-8 bytes (legacy Arabic font text) replaced by U+FFFD; no other byte differs",
        "reproduced": "2026-09-30"},
}

# Representation defects attributed to a REGISTERED build (only after a pinned reproduction).
KNOWN_REPRESENTATION_DEFECTS = {
    "PINNED_LIBREDWG_DWGREAD_JSON_HANDLE_REPRESENTATION_DEFECT": {
        "tool": "LIBREDWG_DWGREAD", "version": "0.13.3",
        "binary_sha256": "fe49cf28f5ee5cd84cbb7b9c7ae0475586cedbfcb1a9ca9bc2cab8c72e094c47",
        "operation": "dwgread -O JSON",
        "behaviour": "an object's own 3-byte handle is printed [code, 3, low 16 bits]; values collide",
        "reproduced_on_decode_sha256": ["4196c03d6feae645c82c47f36bfdeaa3ccbff86af6676c1289dcec9e01358851",
                                        "c742657fab496d554c1f04480ce9dcf3d7b331033e625f0cc14e6f50de7ab49b"],
        "reproduction_count": 2,
        "detail": "research/external_engine_lab/r8_3_pinned_redecode.py -> data/runs/pinned_redecode/"
                  "PINNED_REDECODE_RESULTS.json (per-source command, output hash, collisions, affected references)",
        "layer": "NOT_LOCALISED (DWG parser, internal representation or JSON writer); dwg2dxf output of that source ends "
                 "before any 3-byte handle, so the DXF route cannot localise it",
        "previous_name": "OBSERVED_HANDLE_TRUNCATION_IN_EXISTING_LIBREDWG_JSON",
        "mitigation": "identity = (byte size, value); relative references to colliding values not trusted",
    },
}


def decode_status(decode_sha256: str | None, binary_sha256: str | None = None, tool: str = "LIBREDWG_DWGREAD") -> str:
    """Pin status of a DECODE artifact: the producing binary's status when it was hashed at
    decode time, else whether a registered build has reproduced these exact bytes."""
    if binary_sha256:
        return status(tool, binary_sha256)
    rec = REPRODUCTIONS.get(decode_sha256 or "")
    if rec and status(rec["tool"], rec["binary_sha256"]) == REGISTERED:
        return REPRODUCED_BY_REGISTERED_BUILD
    return NOT_ESTABLISHED
