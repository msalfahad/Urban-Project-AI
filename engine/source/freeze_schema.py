"""FREEZE SCHEMA (RC1 final) - every identity field of a freeze record is a real identity or says why not.

A schema declares each field with one class:
  SHA256        64 lower-case hex characters
  SHA256_MAP    a non-empty mapping whose every value is SHA256 (or, recursively, a SHA256_MAP)
  GIT_COMMIT    7..40 lower-case hex characters
  GIT_COMMIT_MAP
  BOOLEAN       an intentional true / false
  TEXT          a non-empty string
  LIST          a list
  OPTIONAL      may hold anything, but the schema states WHY it is optional
validate() rejects a missing required field, false / true / null / '' / 'UNKNOWN' where an identity is required, a
value of the wrong form, and a field the schema does not declare (an undeclared field is an unaudited field).

Project-agnostic; stdlib only.
"""

from __future__ import annotations

import re

POLICY_ID = "FREEZE_SCHEMA_V1"
CLASSES = ("SHA256", "SHA256_MAP", "GIT_COMMIT", "GIT_COMMIT_MAP", "BOOLEAN", "TEXT", "LIST", "OPTIONAL")
_SHA = re.compile(r"^[0-9a-f]{64}$")
_GIT = re.compile(r"^[0-9a-f]{7,40}$")


def _is_sha(v):
    return isinstance(v, str) and bool(_SHA.match(v))


def _sha_map(v):
    return isinstance(v, dict) and bool(v) and all(_is_sha(x) or _sha_map(x) for x in v.values())


def check(cls, v):
    if cls == "OPTIONAL":
        return True
    if cls == "BOOLEAN":
        return isinstance(v, bool)
    if isinstance(v, bool) or v is None or (isinstance(v, str) and v.strip().upper() in ("", "UNKNOWN", "SAME",
                                                                                         "CHANGED", "N/A")):
        return False
    if cls == "SHA256":
        return _is_sha(v)
    if cls == "SHA256_MAP":
        return _sha_map(v)
    if cls == "GIT_COMMIT":
        return isinstance(v, str) and bool(_GIT.match(v))
    if cls == "GIT_COMMIT_MAP":
        return isinstance(v, dict) and bool(v) and all(isinstance(c, str) and bool(_GIT.match(c)) for c in v.values())
    if cls == "TEXT":
        return isinstance(v, str)
    return isinstance(v, list)


def validate(record: dict, schema: dict) -> dict:
    """schema: {field: {"class": CLASS, "why": text (required for OPTIONAL / BOOLEAN)}}."""
    errors = []
    for f, spec in schema.items():
        if spec["class"] not in CLASSES:
            errors.append({"field": f, "error": "UNKNOWN_CLASS"})
            continue
        if spec["class"] in ("OPTIONAL", "BOOLEAN") and not spec.get("why"):
            errors.append({"field": f, "error": "NO_REASON_FOR_OPTIONAL_OR_BOOLEAN"})
        if f not in record:
            if spec["class"] != "OPTIONAL":
                errors.append({"field": f, "error": "MISSING"})
            continue
        if not check(spec["class"], record[f]):
            errors.append({"field": f, "error": "INVALID_" + spec["class"], "value": repr(record[f])[:80]})
    for f in sorted(set(record) - set(schema)):
        errors.append({"field": f, "error": "UNDECLARED_FIELD"})
    return {"policy": POLICY_ID, "state": "PASS" if not errors else "FAIL", "errors": errors,
            "fields": len(schema), "classes": {f: s["class"] for f, s in schema.items()}}
