"""R8.7 — CANONICAL_MEASUREMENT_INPUT applied to the QS01 room method (SHADOW).

The QS01 room method (QS01 Method A on pipeline7) is not migrated. It is fed, in this process only, from a
CanonicalMeasurementInput that has passed `canonical_input.validate` against the method's declared contract:

    canonical input --validate(QS01 contract)--> COMPLETE --bridge(strict)--> legacy NormalizedDrawing --> method

Revision isolation
    The pipeline is pointed at a revision-tagged STUB decode (one layer record, the revision's own INSUNITS and
    DIMLFAC), written to a temporary directory. The stub is replaced, in this process, by the bridged canonical
    drawing. No run of one revision ever opens another revision's file.

The bridge has two modes:
    strict   - only for COMPLETE inputs; raises on anything missing (belt and braces after validate);
    lenient  - EVIDENCE ONLY: reproduces the old silent behaviour (missing -> "", (), 0) so the ablations can show
               what the method would have done. Its output is never a quantity.

    python3 research/external_engine_lab/r8_7_canonical.py           (smoke run on the old revision)
"""

from __future__ import annotations

import hashlib
import json
import math
import pickle
import sys
import tempfile
from contextlib import contextmanager
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).parent))

from engine import cad_adapter as CA                                                     # noqa: E402
from engine.source import canonical_build as CB, canonical_input as CI, owner_scope as OS  # noqa: E402
from engine.source import geometry_role as GR, topology_policy as TP                     # noqa: E402
from engine.source.cad import kernel, libredwg_map as L                                  # noqa: E402

import r8_6_canonical_rebuild as R86                                                     # noqa: E402

OLD_DWG = "2ec3a9c8b66eb2e129275b87010f4a8d79d7e5bdcc31c1897c14fd7e5647d355"
NEW_DXF = "df0e1d690285f5455b3b5acebe7e20eaee2d1c8aa3743b633a9fd257c6d6f315"
REV_OLD_ID, REV_NEW_ID = "QORTUBA_REV_OLD", "QORTUBA_REV_NEW"
REGION_ID = "RC:MODEL_SPACE:4267:540:1649"
BOUNDS = (108396.02006539538, 13717.799586433912, 112409.74661105567, 16486.762836288166)
FRAME_ID = "MF:" + REGION_ID
FRAME_INSERT = "156"         # the selected plan's sheet-frame occurrence (same handle in both revisions)
VARIANT_FRAMES = {"PLAN_VARIANT_4_SELECTED": "156", "PLAN_VARIANT_3": "4713", "PLAN_VARIANT_2": "9244",
                  "PLAN_VARIANT_1": "13728"}     # REV_NEW frame occurrences, bottom to top (title labels 1AC/1359/250C/3690)
DECODE = ROOT / "data/runs/cad_convert/QORTUBA_ARCHITECTURAL.json"
CLAIMS = ROOT / "data/registry/OWNER_PROJECT_CLAIMS.json"
OLD_UNIT_CLAIM = "QORTUBA-NATIVE-UNIT-OWNER-001"
NEW_UNIT_CLAIM = "QORTUBA-NEW-REVISION-NATIVE-UNIT-OWNER-001"
Q14_CLAIM = "QORTUBA-Q14-CEILING-FOOTPRINT-OWNER-001"
ETYPE = {"LINE": "19", "ARC": "17", "CIRCLE": "18", "LWPOLYLINE": "77"}
ROUND1 = R86.ROUND1
FINGERPRINT = None                                     # filled from the decode header when the revision is built

# ------------------------------------------------------------------ the QS01 contract (declared; proven below)
QS01 = CI.MethodContract(
    method_id="QS01_METHOD_A_ARRANGEMENT_OF_BOUNDARY_LINES+OWNER_RULES_V1_FLOOR_ROWS",
    version="2",
    input_fields=("revision", "region_id", "frame_id", "unit_native_to_mm", "unit_claim_id"),
    part_fields=("source_revision_id", "source_handle", "instance_path", "block_identity", "source_part_id",
                 "part_index", "layer", "visibility", "curve_kind", "geometry"),
    text_fields=("source_revision_id", "text_identity", "source_handle", "instance_path", "block_identity",
                 "text_value", "world_placement", "visibility"),
    dimension_fields=("source_revision_id", "dimension_identity", "source_handle", "instance_path",
                      "placed_points", "measurement", "user_text", "dimlfac", "dimension_type", "visibility"),
    accepted_part_kinds=("SEGMENT", "ARC", "CIRCLE"),
    # R8.8: the R8.7 bare declaration (no authority) is superseded by an exclusion that needs a role per part
    exclusions=(CI.MethodExclusion(
        kind="ELLIPTICAL_ARC", domain="ROOM_TOPOLOGY (QS01 floor rows)",
        reason="the method's input has no elliptical primitive; an ellipse may be left out only when it is proven not "
               "to bound a room",
        authority=GR.POLICY_ID + " rule GR-02 (door symbol: symbol occurrence + door signature + DOOR layer role)",
        allowed_roles=(GR.OPENING_SYMBOL,)),),
    visibility_relevant=True,
    region_review_blocks=True,
)


def roles_for(inp: CI.CanonicalMeasurementInput):
    """Role authority for the exclusion contract (geometry role admission on the same input)."""
    coords = [abs(c) for p in inp.parts for c in p.geometry[:2]] or [1.0]
    return GR.admit(inp, frame_insert=FRAME_INSERT, eps=TP.eps_noise(max(coords)))["roles"]


# ------------------------------------------------------------------ bridge to the legacy method input
class BridgeError(ValueError):
    pass


def _ints(handles, strict, what):
    if handles is None:
        if strict:
            raise BridgeError(f"{what}: instance path missing")
        return ()
    out = []
    for h in handles:
        if not h or not h.isdigit():
            if strict:
                raise BridgeError(f"{what}: instance handle {h!r} is not a plain handle (MINSERT cell?)")
            continue
        out.append(int(h))
    return tuple(out)


def _names(rec, strict, what):
    if not rec.lineage and rec.identity.instance_handles:
        if strict:
            raise BridgeError(f"{what}: block lineage missing")
        return ()
    names = tuple(s.block_name for s in rec.lineage)
    if any(not n for n in names):
        if strict:
            raise BridgeError(f"{what}: block name missing")
        return tuple(n or "" for n in names)
    return names


def _prov(rec, etype, strict, sub_id=""):
    what = rec.identity.key or repr(rec.identity)
    if strict and (not rec.identity.source_handle or rec.layer is None):
        raise BridgeError(f"{what}: handle or layer missing")
    return CA.Provenance(handle=int(rec.identity.source_handle or 0), entity_type=etype, layer=str(rec.layer or "0"),
                         block_path=_names(rec, strict, what), instance_path=_ints(rec.identity.instance_handles, strict, what),
                         sub_id=sub_id)


def to_legacy(inp: CI.CanonicalMeasurementInput, strict=True):
    """(primitives, texts, dimensions) in the legacy shape. The legacy part id is source-derived: the part kind and
    index within its source entity for multi-part entities; '' for single-part entities."""
    prims, seen = [], set()
    for p in inp.parts:
        if p.kind not in ("SEGMENT", "ARC", "CIRCLE"):
            continue
        idx = p.identity.part_index
        sub = "" if p.entity_type != "LWPOLYLINE" else ("" if idx is None else f"{p.kind[0]}{idx}")
        if strict and p.entity_type == "LWPOLYLINE" and idx is None:
            raise BridgeError(f"{p.identity!r}: part index missing")
        prov = _prov(p, ETYPE.get(p.entity_type, p.entity_type or ""), strict, sub)
        g = p.geometry
        if p.kind == "SEGMENT":
            prim = CA.Primitive(kind="SEGMENT", provenance=prov, x1=g[0], y1=g[1], x2=g[2], y2=g[3])
        elif p.kind == "ARC":
            prim = CA.Primitive(kind="ARC", provenance=prov, cx=g[0], cy=g[1], radius=g[2], start_angle=g[3], end_angle=g[4])
        else:
            prim = CA.Primitive(kind="CIRCLE", provenance=prov, cx=g[0], cy=g[1], radius=g[2])
        if strict and prim.object_id in seen:
            raise BridgeError(f"duplicate legacy object id {prim.object_id}")
        seen.add(prim.object_id)
        prims.append(prim)
    texts = []
    for t in inp.texts:
        if t.x is None or t.y is None or t.value is None:
            if strict:
                raise BridgeError(f"{t.identity.key}: text placement or value missing")
            continue
        texts.append(CA.TextObservation(value=t.value, x=t.x, y=t.y, height=t.height or 0.0,
                                        provenance=_prov(t, t.entity_type or "TEXT", strict)))
    dims = []
    for d in inp.dimensions:
        if d.placed_points is None:
            if strict:
                raise BridgeError(f"{d.identity.key}: dimension placement missing")
            continue
        (x1, y1), (x2, y2) = d.placed_points
        dims.append(CA.DimensionObservation(geometry_mm=math.hypot(x2 - x1, y2 - y1), display_value=d.measurement,
                                            dimlfac=d.dimlfac if d.dimlfac is not None else 1.0,
                                            user_text=d.user_text if d.user_text is not None else "",
                                            x1=x1, y1=y1, x2=x2, y2=y2,
                                            provenance=_prov(d, d.dimension_type or "", strict)))
    return prims, texts, dims


# ------------------------------------------------------------------ isolated run
@contextmanager
def isolated_config(inp: CI.CanonicalMeasurementInput):
    """The run config with ONE source: a revision-tagged stub decode in a temporary directory."""
    from research.qs_wall_treatment_01.pa08.qortuba import blind as B
    cfg = json.loads((B.OUT / "PA08_BLIND_CONFIG.json").read_text("utf-8"))
    orig = B.OUT
    with tempfile.TemporaryDirectory() as d:
        stub = {"HEADER": {"INSUNITS": inp.notes.get("insunits"), "DIMLFAC": inp.notes.get("dimlfac", 1.0)},
                "OBJECTS": [{"object": "LAYER", "name": "0", "handle": [0, 1, 16]}],
                "R8_7_STUB_FOR": {"revision_id": inp.revision.revision_id, "anchor_sha256": inp.revision.anchor_sha256}}
        sp = Path(d) / f"STUB_{inp.revision.revision_id}.json"
        sp.write_text(json.dumps(stub), "utf-8")
        cfg["SOURCES"] = [{"PATH": str(sp), "KIND": "CAD_DECODE_JSON", "FAMILY": "ARCHITECTURAL"}]
        (Path(d) / "PA08_BLIND_CONFIG.json").write_text(json.dumps(cfg), "utf-8")
        B.OUT = Path(d)
        try:
            yield cfg
        finally:
            B.OUT = orig


def run_legacy(inp: CI.CanonicalMeasurementInput, strict=True) -> dict:
    prims, texts, dims = to_legacy(inp, strict)

    def transform(nd):
        return replace(nd, primitives=prims, texts=texts, dimensions=dims, instances=[], block_definitions={}, layers=[])
    with isolated_config(inp):
        res = R86.run_method(transform)
    return res


def rooms_of(res):
    return [{"room_id": f["ROOM_ID"], "room": f["ROOM"], "area_m2": f["METHOD_A_CAD_POLYGON_AREA_M2"],
             "wet_or_dry": f["WET_OR_DRY"],
             "rectangles": [[q["X_MM"][0], q["Y_MM"][0], q["X_MM"][1], q["Y_MM"][1]] for q in f["RECTANGLES"]]}
            for f in res["o"]["floors"]]


def measure(inp, contract=QS01, *, expected_revision_id, selected_region_id=REGION_ID) -> dict:
    """The guarded measurement: no COMPLETE validation -> no quantity; method unit != claimed unit -> no quantity."""
    v = CI.validate(inp, contract, expected_revision_id=expected_revision_id, selected_region_id=selected_region_id,
                    roles=roles_for(inp) if contract.exclusions else None)
    if v["state"] != CI.COMPLETE:
        return {"state": v["state"], "six": None, "rooms": None, "validation": v}
    res = run_legacy(inp, strict=True)
    unit = res["unit"]
    if float(unit.get("UNIT_SCALE_TO_MM") or 0) != float(inp.unit_native_to_mm):
        return {"state": "METHOD_UNIT_DIFFERS_FROM_CLAIMED_UNIT", "six": None, "rooms": None, "validation": v,
                "method_unit": unit, "claimed_native_to_mm": inp.unit_native_to_mm}
    return {"state": CI.COMPLETE, "six": R86.six_values(res), "rooms": rooms_of(res),
            "rooms_digest": R86.digest(R86.rooms_key(res)), "validation": v, "method_unit": unit, "res": res}


def lenient_values(inp) -> dict:
    """EVIDENCE ONLY: what the method silently does with this input when nothing is checked."""
    res = run_legacy(inp, strict=False)
    return {"six": R86.six_values(res), "rooms": rooms_of(res), "rooms_digest": R86.digest(R86.rooms_key(res))}


# ------------------------------------------------------------------ claims
def claims():
    return {c["claim_id"]: OS.from_record(c) for c in json.loads(CLAIMS.read_text())["claims"]}


def old_unit_claim():
    c = next(c for c in json.loads((ROOT / "data/registry/OWNER_UNIT_CLAIMS.json").read_text())["claims"]
             if c["evidence_id"] == OLD_UNIT_CLAIM)
    assert c["source_sha256"] == OLD_DWG
    return c


def unit_for(revision: CI.SourceRevision):
    """(native_to_mm, claim id) for exactly this revision, or (None, reason). Never transferred."""
    if revision.revision_id == REV_OLD_ID and revision.anchor_sha256 == OLD_DWG:
        c = old_unit_claim()
        return float(c["native_to_mm"]), c["evidence_id"]
    r = OS.applies(claims()[NEW_UNIT_CLAIM], project="QORTUBA", revision_id=revision.revision_id,
                   purpose=OS.SHADOW_DIAGNOSTIC)
    if r["state"] != OS.APPLIES:
        return None, r["state"]
    if revision.anchor_sha256 != NEW_DXF:
        return None, "ANCHOR_MISMATCH: the claim is anchored to DXF evidence " + NEW_DXF[:8] + "; re-anchor it first"
    return float(r["value"]["native_to_mm"]), NEW_UNIT_CLAIM


# ------------------------------------------------------------------ revisions and inputs
def rev_old():
    return CI.SourceRevision(REV_OLD_ID, CI.EXACT_SOURCE, OLD_DWG, None, "HISTORICAL_VALIDATED_REVISION")


def rev_new():
    return CI.SourceRevision(REV_NEW_ID, CI.DERIVED_PENDING_SOURCE, NEW_DXF, None,
                             "OWNER_SELECTED_CURRENT_REVISION_PENDING_DWG")


def k1_records(revision, decode=None):
    decode = decode if decode is not None else json.loads(DECODE.read_text())
    doc = L.to_document(decode)
    k = CB.K1(revision.revision_id, decode, doc, kernel.realise(doc))
    return k.parts(), k.texts(), k.dimensions(), decode.get("HEADER", {})


def frame_bounds(parts, frame=FRAME_INSERT):
    """The measurement clip: the extent of the selected plan's own sheet-frame occurrence. The region candidate's
    recorded bounds lie inside the frame's corner marks; clipping to them cuts the frame occurrence (R8.7)."""
    b = CB.occurrence_extent(parts, frame)
    if b is None:
        raise ValueError(f"frame occurrence {frame} not present in this revision")
    return b


def old_input(decode=None, route="K1", region_id=REGION_ID, bounds=None):
    rev = rev_old()
    parts, texts, dims, hdr = k1_records(rev, decode)
    bounds = bounds or frame_bounds(parts)
    mm, claim = unit_for(rev)
    return CB.assemble(rev, region_id, bounds, FRAME_ID, mm, claim, parts, texts, dims,
                       notes={"insunits": hdr.get("INSUNITS"), "dimlfac": float(hdr.get("DIMLFAC") or 1.0), "route": route,
                              "clip_bounds": list(bounds)})


def input_from_pickle(path, revision, region_id=REGION_ID, bounds=None, route="K2", frame=FRAME_INSERT):
    blob = pickle.load(open(path, "rb"))
    hdr = blob["header"]
    bounds = bounds or frame_bounds(blob["parts"], frame)
    mm, claim = unit_for(revision)
    return CB.assemble(revision, region_id, bounds, FRAME_ID, mm, claim, blob["parts"], blob["texts"], blob["dims"],
                       notes={"insunits": hdr.get("$INSUNITS"), "dimlfac": float(hdr.get("$DIMLFAC") or 1.0),
                              "route": route, "findings": blob["findings"], "clip_bounds": list(bounds)}), blob


def build_k2_records(dxf_path, revision_id, out_pickle):
    """K2 route on one DXF -> canonical records, cached (the 214 MB revision takes ~2 min and ~2.6 GB)."""
    from engine.source.cad import kernel_ezdxf as K2R
    doc, findings = K2R.load(dxf_path)
    if doc is None:
        raise ValueError(f"K2 could not load {dxf_path}: {[f.detail for f in findings]}")
    rg = K2R.realise(doc)
    k = CB.K2(revision_id, doc, rg)
    blob = {"parts": k.parts(), "texts": k.texts(), "dims": k.dimensions(),
            "header": {h: doc.header.get(h) for h in ("$INSUNITS", "$DIMLFAC", "$FINGERPRINTGUID", "$VERSIONGUID")},
            "findings": [(f.code, f.obs_id, tuple(f.instance_path), f.detail) for f in rg.findings],
            "hidden": rg.hidden, "dispositions": dict(rg.dispositions), "dxf_sha256": sha(dxf_path)}
    pickle.dump(blob, open(out_pickle, "wb"))
    return blob


def sha(p) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


if __name__ == "__main__":
    if len(sys.argv) == 5 and sys.argv[1] == "build-k2":          # build-k2 <dxf> <revision_id> <out.pkl>
        b = build_k2_records(sys.argv[2], sys.argv[3], sys.argv[4])
        print(len(b["parts"]), len(b["texts"]), len(b["dims"]), b["dxf_sha256"])
        sys.exit(0)
    inp = old_input()
    m = measure(inp, expected_revision_id=REV_OLD_ID)
    print(m["state"], m["six"], len(inp.parts), len(inp.texts), len(inp.dimensions), inp.notes["outside_region"],
          len(inp.region_review), m["validation"]["excluded_by_declaration"])
