"""Hand fixture "villa T200-R" (NOT the development villa): two storeys, a roof, a sunken wet slab, a basin, two
footings (one with a printed founding level, one without). Metres; a millimetre copy is built by `in_mm`.

Printed (invented sheet names A-xx architectural, S-xx structural; one zero, ARCH):
  GF   FFL +0.60 (A-05 section 1-1); structural slab top +0.50 (S-02 'T.O.S +0.50'); ground-beam top = slab top
       (S-03 detail: layer 0.00); ground beam 0.60 deep (S-03); footing A underside printed 'F.L. -1.20' (S-01), depth
       0.60; footing B depth 0.50, founding level NOT printed; under every footing 0.05 screed (UNDERLAY) and 0.10
       blinding (S-03); existing ground +-0.00 (A-01); note 'excavation not less than 1.30 below existing ground' (S-01
       note 4: FORMATION AT_MOST -1.30, a limit, not a value); finish schedule 'screed 70 + tile 30' = 0.10 (A-09).
  1F   FFL +4.10 (A-05); T.O.S +4.00 (S-04); slab 0.20 (S-04 note); beams 0.60 deep (S-06 schedule).
  1F-WET (sunken bathroom) FFL +4.08 (A-03 plan mark); T.O.S +3.70 (S-04 'sunken slab'); slab 0.20.
  RF   finished roof +7.70 (A-05); parapet top +8.70 (A-05 chain 1000); roof build-up NOT printed; roof slab 0.20,
       beams 0.60 (S-05).
  BASIN rim (structure) +0.45, finished floor -0.95, structure line -1.03 (A-07 cut); finished depth 1.40 printed;
       base 0.35 (S-07 detail); no screed under the base (S-07: blinding directly, UNDERLAY 0.00); blinding 0.10;
       existing ground +-0.00.

Hand truth (worked here, never taken from the module):
  GF-A  FFL->SLAB_TOP 0.60 - 0.50 = 0.10 (= schedule 0.10: agree); GB_TOP 0.50 - 0 = +0.50; GB_BOTTOM 0.50 - 0.60 =
        -0.10; FOOTING_TOP -1.20 + 0.60 = -0.60; NECK_RUN 0.50 - (-0.60) = 1.10; BLINDING_TOP -1.20 - 0.05 = -1.25;
        FORMATION -1.25 - 0.10 = -1.35; EXCAVATION_DEPTH 0.00 - (-1.35) = 1.35; limit -1.35 <= -1.30 SATISFIED.
  GF-B  FFL / SLAB_TOP / GB as GF-A; FOOTING_TOP, FOOTING_BOTTOM, BLINDING_TOP, FORMATION: HELD (no founding
        level); NECK_RUN, FOOTING_DEPTH (both ends unknown), UNDERLAY, BLINDING_THICKNESS, EXCAVATION_DEPTH: HELD.
  1F    build-up 4.10 - 4.00 = 0.10; soffit 4.00 - 0.20 = 3.80; beam bottom 4.00 - 0.60 = 3.40.
  1F-WET build-up 4.08 - 3.70 = 0.38 (sunken fill + finish); soffit 3.50; beam link HELD (no beam printed there).
  RF    slab top HELD (build-up not printed), soffit / beam bottom HELD; parapet height 8.70 - 7.70 = 1.00.
  BASIN finished depth 0.45 - (-0.95) = 1.40 (= printed); build-up -0.95 - (-1.03) = 0.08; RC wall 0.45 - (-1.03) =
        1.48; base underside -1.03 - 0.35 = -1.38; blinding top -1.38; formation -1.48; excavation 1.48.
Uses: basin wall height from the finished floor -> FINISHED_AS_STRUCTURAL (+0.08 m); sill W5 measured from the ground
line -> WRONG_REFERENCE (-0.60 m); neck A top value 0.60 (= FFL) -> FINISHED_AS_STRUCTURAL; 0.45 -> VALUE_NOT_FROM_
DRAWINGS; 0.50 -> OK; neck B footing top -> NEEDS_HELD; wet fill from the 1F slab top -> WRONG_REFERENCE (+0.30 m);
roof storey height from the finished roof -> FINISHED_AS_STRUCTURAL with the needed datum HELD."""
from __future__ import annotations

import copy

DC = "DRAWING-CONFIRMED"


def _d(chain, kind, value, ref, status=DC, **kw):
    return dict({"chain_id": chain, "kind": kind, "value": value, "ref": ref, "status": status}, **kw)


def _l(chain, layer, t, ref, status=DC, **kw):
    return dict({"chain_id": chain, "layer": layer, "thickness": t, "ref": ref, "status": status}, **kw)


def project():
    datums, layers = [], []
    for c in ("GF-A", "GF-B"):
        datums += [_d(c, "FFL", 0.60, "A-05 section 1-1"), _d(c, "SLAB_TOP", 0.50, "S-02 T.O.S +0.50"),
                   _d(c, "EXISTING_GROUND", 0.00, "A-01 +-0.00")]
        layers += [_l(c, "FLOOR_BUILD_UP", 0.10, "A-09 finish schedule screed 70 + tile 30"),
                   _l(c, "GB_TOP_BELOW_SLAB_TOP", 0.00, "S-03 detail GB top = slab top"),
                   _l(c, "GB_DEPTH", 0.60, "S-03"), _l(c, "UNDERLAY", 0.05, "S-03 5 cm screed"),
                   _l(c, "BLINDING_THICKNESS", 0.10, "S-03 10 cm blinding")]
    datums += [_d("GF-A", "FOOTING_BOTTOM", -1.20, "S-01 F.L. -1.20"),
               _d("GF-A", "FORMATION", -1.30, "S-01 note 4", bound="AT_MOST"),
               _d("GF-B", "FOOTING_BOTTOM", None, "S-01 (no founding level printed for B)", status="HELD")]
    layers += [_l("GF-A", "FOOTING_DEPTH", 0.60, "S-01 schedule A"), _l("GF-B", "FOOTING_DEPTH", 0.50, "S-01 schedule B")]
    datums += [_d("1F", "FFL", 4.10, "A-05 section 1-1"), _d("1F", "SLAB_TOP", 4.00, "S-04 T.O.S +4.00"),
               _d("1F-WET", "FFL", 4.08, "A-03 plan mark"), _d("1F-WET", "SLAB_TOP", 3.70, "S-04 sunken slab"),
               _d("RF", "FINISHED_ROOF", 7.70, "A-05"), _d("RF", "PARAPET_TOP", 8.70, "A-05 chain 1000"),
               _d("BASIN", "POOL_RIM", 0.45, "A-07 cut"), _d("BASIN", "POOL_FINISHED_FLOOR", -0.95, "A-07 cut"),
               _d("BASIN", "POOL_BASE_TOP", -1.03, "A-07 structure line"),
               _d("BASIN", "EXISTING_GROUND", 0.00, "A-01")]
    layers += [_l("1F", "SLAB_THICKNESS", 0.20, "S-04 note"), _l("1F", "BEAM_DEPTH", 0.60, "S-06"),
               _l("1F-WET", "SLAB_THICKNESS", 0.20, "S-04 note"),
               _l("RF", "SLAB_THICKNESS", 0.20, "S-05"), _l("RF", "BEAM_DEPTH", 0.60, "S-05"),
               _l("RF", "ROOF_BUILD_UP", 0.10, "owner manual finish allowance", method="OWNER_MANUAL",
                  status="ASSUMED — OWNER-APPROVED"),
               _l("BASIN", "FINISHED_DEPTH", 1.40, "A-07 1400"), _l("BASIN", "BASE_THICKNESS", 0.35, "S-07"),
               _l("BASIN", "UNDERLAY", 0.00, "S-07 blinding directly under the base"),
               _l("BASIN", "BLINDING_THICKNESS", 0.10, "S-07")]
    uses = [
        {"use_id": "U-BASIN-WALL", "quantity": "basin RC wall height", "chain_id": "BASIN", "needs": "POOL_BASE_TOP",
         "used": {"kind": "POOL_FINISHED_FLOOR"}, "ref": "ledger B-1"},
        {"use_id": "U-SILL-W5", "quantity": "W5 sill above floor", "chain_id": "GF-A", "needs": "FFL",
         "measured_from": {"chain_id": "GF-A", "kind": "EXISTING_GROUND"},
         "must_be_from": {"chain_id": "GF-A", "kind": "FFL"}, "ref": "census row W5"},
        {"use_id": "U-NECK-A-FFL", "quantity": "neck A top", "chain_id": "GF-A", "needs": "GB_TOP",
         "used": {"value": 0.60}, "ref": "profile NECK_TOP"},
        {"use_id": "U-NECK-A-CONV", "quantity": "neck A top", "chain_id": "GF-A", "needs": "GB_TOP",
         "used": {"value": 0.45}, "ref": "profile NECK_TOP"},
        {"use_id": "U-NECK-A-OK", "quantity": "neck A top", "chain_id": "GF-A", "needs": "GB_TOP",
         "used": {"value": 0.50}, "ref": "profile NECK_TOP"},
        {"use_id": "U-NECK-B", "quantity": "neck B run", "chain_id": "GF-B", "needs": "FOOTING_TOP",
         "used": {"kind": "FOOTING_TOP"}, "ref": "ledger N-B"},
        {"use_id": "U-WET-FILL", "quantity": "wet-room fill depth", "chain_id": "1F-WET", "needs": "SLAB_TOP",
         "used": {"chain_id": "1F", "kind": "SLAB_TOP"}, "ref": "ledger W-3"},
        {"use_id": "U-ROOF-COL", "quantity": "2F column height to the roof structure", "chain_id": "RF",
         "needs": "SLAB_TOP", "used": {"kind": "FINISHED_ROOF"}, "margin": {"up": 0.0, "down": 0.12},
         "ref": "ledger C-9"},
    ]
    return {"base_system": "ARCH", "units": "m",
            "chains": [{"chain_id": "GF-A", "family": "FOUNDATION"}, {"chain_id": "GF-B", "family": "FOUNDATION"},
                       {"chain_id": "1F", "family": "FLOOR"}, {"chain_id": "1F-WET", "family": "FLOOR"},
                       {"chain_id": "RF", "family": "ROOF"}, {"chain_id": "BASIN", "family": "POOL"}],
            "datums": datums, "layers": layers, "uses": uses}


def in_mm(p):
    q = copy.deepcopy(p)
    q["units"] = "mm"
    for d in q["datums"]:
        if d["value"] is not None:
            d["value"] = round(d["value"] * 1000, 6)
    for ly in q["layers"]:
        ly["thickness"] = round(ly["thickness"] * 1000, 6)
    for u in q["uses"]:
        if "value" in u.get("used", {}):
            u["used"]["value"] = round(u["used"]["value"] * 1000, 6)
        if "margin" in u:
            u["margin"] = {k: v * 1000 for k, v in u["margin"].items()}
    return q
