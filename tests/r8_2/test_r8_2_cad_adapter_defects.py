"""R8.2 — new cad_adapter defects, frozen as strict KNOWN_DEFECT (§4, §23).

Each defect has a CHARACTERISATION test on the current cad_adapter (strict
xfail: it fails today, and a silent fix fails the run) and a REPLACEMENT test
showing K1 (D1) and, where the DXF route applies, K2 get it right.
cad_adapter itself is not modified.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from engine import cad_adapter as CA
from engine.source import findings as F
from engine.source.cad import kernel, kernel_ezdxf as K2, libredwg_map as L
from tests.r8_0 import libredwg_builder as B, scenes as S

from .pairing import pair

ROOT = Path(__file__).resolve().parents[2]
REG = json.loads((Path(__file__).parent / "registers" / "R8_2_CAD_ADAPTER_DEFECTS.json").read_text())


def k1(dec):
    return kernel.realise(L.to_document(dec)).as_contract_dict()


# A ---------------------------------------------------------------- invisible geometry
def _invisible_decode():
    dec = B.build({"entities": [{"kind": "LINE", "a": (0, 0), "b": (10, 0)}, {"kind": "LINE", "a": (0, 5), "b": (10, 5)}]})
    for o in dec["OBJECTS"]:
        if o.get("entity") == "LINE" and o["start"][1] == 5.0:
            o["invisible"] = 1
    return dec


def test_A_cad_adapter_does_not_realise_invisible_geometry():
    n = CA.normalize(_invisible_decode())
    assert all(not p.provenance.invisible for p in n.primitives), "invisible entity emitted as a primitive"


def test_A_k1_hides_invisible_geometry():
    got = k1(_invisible_decode())
    assert got["segments"] == [((0.0, 0.0), (10.0, 0.0))] and len(got["hidden"]) == 1


def test_A_k2_hides_invisible_geometry():
    scene = {"entities": [{"kind": "LINE", "a": (0, 0), "b": (10, 0)}]}
    doc, _ = pair(scene)
    for e in doc.modelspace():
        e.dxf.invisible = 1
    got = K2.realise(doc).as_contract_dict()
    assert got["segments"] == [] and len(got["hidden"]) == 1


# B ---------------------------------------------------------------- nameless block header
def _nameless_decode():
    dec = B.build({"blocks": {"CURVES": S.CURVES_BLOCK}, "entities": [S._insert("CURVES", at=(10000.0, 0.0))]})
    for o in dec["OBJECTS"]:
        if o.get("type") == 49 and o.get("name") == "CURVES":
            o["name"], o["object"] = "", ""
    return dec


def test_B_cad_adapter_places_nameless_block_content_through_its_insert():
    n = CA.normalize(_nameless_decode())
    arcs = [p for p in n.primitives if p.kind == "ARC" and p.provenance.entity_type == "17"]
    assert arcs and all(abs(p.cx - 11000.0) < 1e-6 for p in arcs), "block-local coordinates emitted at top level"


def test_B_k1_places_nameless_block_through_its_insert():
    got = k1(_nameless_decode())
    assert [f["code"] for f in got["findings"]] == [F.BLOCK_NAME_UNREADABLE]
    assert got["arcs"][0]["CENTER"] == (11000.0, 0.0)


# C ---------------------------------------------------------------- OLE2FRAME labelled type 2
def _ole_type2_decode():
    dec = B.build({"entities": [{"kind": "LINE", "a": (0, 0), "b": (1, 0)}]})
    line = next(o for o in dec["OBJECTS"] if o.get("entity") == "LINE")
    dec["OBJECTS"].append({"entity": "OLE2FRAME", "type": 2, "handle": [0, 1, 999], "ownerhandle": line["ownerhandle"],
                           "layer": line["layer"]})
    return dec


def test_C_cad_adapter_counts_a_type2_ole2frame():
    n = CA.normalize(_ole_type2_decode())
    counted = sum(n.unhandled.values()) + sum(n.notes.get("entities_dropped_by_kind", {}).values())
    assert counted >= 1, "OLE2FRAME with type code 2 vanished without a count"


def test_C_k1_reports_type2_ole2frame_as_skipped():
    got = k1(_ole_type2_decode())
    assert F.SKIPPED in [f["code"] for f in got["findings"]]


# D ---------------------------------------------------------------- unresolved owner guessed into model space
def _unowned_decode():
    dec = B.build({"entities": [{"kind": "LINE", "a": (0, 0), "b": (1, 0)}]})
    for o in dec["OBJECTS"]:
        if o.get("entity") == "LINE":
            o["ownerhandle"] = [4, 1, 12345, 12345]
    return dec


def test_D_cad_adapter_does_not_place_an_unowned_entity_in_model_space():
    n = CA.normalize(_unowned_decode())
    assert n.primitives == [], "entity with an unresolvable owner realised as model-space geometry"


def test_D_k1_quarantines_an_unowned_entity():
    got = k1(_unowned_decode())
    assert got["segments"] == [] and got["dispositions"] == {"UNPLACED": 1}


# E ---------------------------------------------------------------- truncated handle identity collision
def _collision_decode():
    dec = B.build({"entities": [{"kind": "LINE", "a": (0, 0), "b": (1, 0)}, {"kind": "LINE", "a": (0, 5), "b": (1, 5)}]})
    ls = [o for o in dec["OBJECTS"] if o.get("entity") == "LINE"]
    ls[1]["handle"] = [0, 3, ls[0]["handle"][-1]]            # a 3-byte handle printed with 16 bits
    return dec


def test_E_cad_adapter_keeps_distinct_identity_for_colliding_handle_values():
    n = CA.normalize(_collision_decode())
    ids = [p.object_id for p in n.primitives]
    assert len(set(ids)) == len(ids), "two different entities share one object_id"


def test_E_k1_keeps_distinct_identity_for_colliding_handle_values():
    doc = L.to_document(_collision_decode())
    ids = [o.obs_id for o in doc.entities]
    assert len(set(ids)) == 2 and any(i.endswith("+3B") for i in ids)
    assert F.HANDLE_VALUE_TRUNCATED in [f.code for f in doc.findings]


# register integrity --------------------------------------------------------
def test_register_names_every_characterisation_test_that_exists():
    here = {n for n in globals() if n.startswith("test_")}
    for d in REG["defects"]:
        for t in d["characterisation_tests"]:
            assert t.split("::")[1] in here, t


def test_cad_adapter_is_unchanged():
    assert hashlib.sha256((ROOT / "engine" / "cad_adapter.py").read_bytes()).hexdigest() == REG["cad_adapter_sha256"]
