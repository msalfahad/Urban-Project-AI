"""TOPOLOGY RESULT DIGEST (RC1 final) - one sha256 over the certified topology OUTPUT of a run.

TOPOLOGY_RUN_INPUT_DIGEST (run_manifest) identifies everything that can CHANGE the topology; this digest identifies
what the topology IS. It covers, for one run result:
  sites           site_id, kind, status, physical_status, area, gross outer area, perimeter, holes, sorted outer /
                  hole boundary source ids, interior stub ids, label occurrences
  wall_bands      band_id, state, face_a, face_b, width, interval
  topology closures and opening closures: source id, kind, role, geometry, derived_from
  openings        occurrence, state, width, closure ids, closure-B rule
  passages        passage_id, kind, band_id, band_end, width, wall thickness, area, strip site, head condition
Numbers are quantised with digests.quantise (1e-6 native units); every list is sorted; keys are sorted. It never
covers arrangement face / cycle indices, timestamps, paths, object ids or evidence prose.

Project-agnostic; stdlib only.
"""

from __future__ import annotations

import hashlib
import json
from decimal import Decimal

from engine.source.digests import quantise

POLICY_ID = "TOPOLOGY_RESULT_DIGEST_V1"
Q = Decimal("0.000001")


def _n(v):
    if isinstance(v, bool) or v is None or isinstance(v, (str, int)):
        return v
    if isinstance(v, float):
        return quantise(v, Q)
    if isinstance(v, (list, tuple)):
        return [_n(x) for x in v]
    if isinstance(v, dict):
        return {k: _n(x) for k, x in sorted(v.items())}
    return repr(v)


def _item(b):
    return {"source_id": b.source_id, "kind": b.kind, "role": b.role, "geometry": _n(list(b.geometry)),
            "derived_from": sorted(b.derived_from or ())}


def content(res: dict) -> dict:
    sites = [{"site_id": s["site_id"], "kind": s["kind"], "status": s["status"],
              "physical_status": s.get("physical_status"), "area": _n(s["area"]),
              "gross_outer_area": _n(s.get("gross_outer_area")), "perimeter": _n(s.get("perimeter")),
              "holes": s.get("holes"), "outer": sorted(s.get("outer_boundary_source_ids") or ()),
              "hole_ids": sorted(s.get("hole_boundary_source_ids") or ()),
              "stubs": sorted(s.get("interior_stub_source_ids") or ()), "labels": sorted(s.get("labels") or ())}
             for s in res["sites"]]
    bands = [{"band_id": b["band_id"], "state": b["state"], "face_a": b["face_a"], "face_b": b["face_b"],
              "width": _n(b["width"]), "interval": _n(list(b["interval"]))} for b in res["wall_bands"]["bands"]]
    tcl = res.get("topology_closures")
    tcl = tcl.get("closures", []) if isinstance(tcl, dict) else (tcl or [])
    tclosures = [_n(c) if isinstance(c, dict) else _item(c) for c in tcl]
    closures = [_item(c) for c in res.get("closures") or ()]
    openings = [{"occurrence": k, "state": o.get("state"), "width": _n(o.get("width")),
                 "closure_a": o.get("closure_a"), "closure_b": o.get("closure_b"),
                 "closure_b_rule": o.get("closure_b_rule")} for k, o in sorted((res.get("openings") or {}).items())]
    passages = [{k: _n(p.get(k)) for k in ("passage_id", "kind", "band_id", "band_end", "width", "wall_thickness",
                                            "area_native", "strip_in_site", "head_condition")}
                for p in res.get("passages") or ()]
    key = lambda x: json.dumps(x, sort_keys=True)          # noqa: E731
    return {"policy": POLICY_ID, "sites": sorted(sites, key=key), "wall_bands": sorted(bands, key=key),
            "topology_closures": sorted(tclosures, key=key), "closures": sorted(closures, key=key),
            "openings": openings, "passages": sorted(passages, key=key)}


def digest(res: dict) -> dict:
    c = content(res)
    blob = json.dumps(c, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()
    return {"policy": POLICY_ID, "sha256": hashlib.sha256(blob).hexdigest(),
            "counts": {k: len(v) for k, v in c.items() if isinstance(v, list)}, "bytes": len(blob),
            "covers": ["sites", "wall_bands", "topology_closures", "closures", "openings", "passages"],
            "excludes": ["arrangement face / cycle indices", "timestamps", "paths", "object ids", "evidence prose"]}
