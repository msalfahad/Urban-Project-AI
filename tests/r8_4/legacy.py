"""Canonical hashes of historical R8.0 contracts (R8.4 §31). A superseded contract is never
edited: its row / test source is hashed here and the hash is frozen in
tests/r8_0/registers/R8_CONTRACT_SUPERSESSION.json, so any silent rewrite fails the suite."""

from __future__ import annotations

import hashlib
import inspect
import json

ENV_PLACEHOLDER = "<ENV:URBAN_R8_REAL_SOURCE>"


def _canon(v):
    if isinstance(v, dict):
        return {k: (ENV_PLACEHOLDER if k == "real_source" else _canon(x)) for k, x in v.items()}
    if isinstance(v, (list, tuple)):
        return [_canon(x) for x in v]
    return v


def contract_row(cid):
    from tests.r8_0.test_r8_0_pending_contracts import CONTRACTS
    return next(r for r in CONTRACTS if r[0] == cid)


def row_hash(cid) -> str:
    cid_, target, inputs, expect = contract_row(cid)
    blob = json.dumps(_canon([cid_, target, inputs, expect]), sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(blob.encode()).hexdigest()


def source_hash(func) -> str:
    return hashlib.sha256(inspect.getsource(func).encode()).hexdigest()


def f19_hash() -> str:
    from tests.r8_0 import test_r8_0_source_capability as T
    from tests.r8_0.scenes import SKIP_CASES
    scene = next(s for s in SKIP_CASES if s[0] == "F19")
    blob = source_hash(T.test_custom_entity_on_wall_layer_blocks_region_contract) + json.dumps(
        _canon(list(scene)), sort_keys=True, default=str)
    return hashlib.sha256(blob.encode()).hexdigest()
