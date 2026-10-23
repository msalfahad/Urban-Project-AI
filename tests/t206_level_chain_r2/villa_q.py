"""Hand fixture "villa T206-Q" (NOT the development villa) for level-chain run 2: sunken wet panels (one with a
printed T.O.S., one shown only by a hatch), a printed T.O.S. that contradicts the printed floor build-up, two sheets
printing different T.O.S. for one slab, and per-footing chains (one with a printed formation, one without, one whose
printed formation breaks the 'not less than' note). Metres; `in_mm` builds the millimetre copy.

Printed (invented sheet names A-xx architectural, S-xx structural; one zero, ARCH):
  1F    FFL +3.80 (A-04 section 2-2); T.O.S +3.70 (S-11 section 'T.O.S +3.70'); floor build-up 0.10 (A-12 floor
        detail 'screed 60 + tile 40'); slab 0.20 (S-10 note); beams 0.60 (S-12 schedule).
  1F-WA sunken wet panel (S-10 'sunken slab' hatch + S-11 cut 'T.O.S +3.45'); FFL +3.80 (no own level mark: the storey
        FFL); slab 0.20 (S-10 note).
  1F-WB sunken wet panel shown ONLY by the S-10 hatch: no T.O.S., no drop printed; FFL +3.80; slab 0.20.
  2F    FFL +7.20 (A-04); T.O.S +7.10 (S-13 section); floor build-up 0.15 (A-12 detail 'screed 110 + tile 40'): the two
        printed datums give 0.10, the printed layer 0.15 -> they cannot all be right; slab 0.20.
  2F-K  one slab panel with T.O.S +7.10 on S-13 and +7.05 on S-14.
  FTG-A footing depth 0.60 (S-02 schedule); under it 0.05 screed + 0.02 membrane (S-03 detail chain 5 / 2) and 0.10
        blinding; formation printed 'F.L. -1.80' (S-01 section F-1); ground-beam top +0.30 (S-03 'T.O.B +0.30'); GF FFL
        +0.45 (A-04); existing ground +-0.00 (A-01); note 'excavation not less than 1.50 below existing ground' (S-01
        note 3 -> FORMATION AT_MOST -1.50, a limit).
  FTG-B as FTG-A (depth 0.50) but NO formation printed.
  FTG-C as FTG-A (depth 0.40) with formation printed 'F.L. -1.40' (shallower than the note allows).

Hand truth (worked here, never taken from the module):
  1F    FFL -> T.O.S 3.80 - 3.70 = 0.10 = printed 0.10: agree (DRAWING-CONFIRMED); soffit 3.70 - 0.20 = 3.50; beam
        bottom 3.70 - 0.60 = 3.10.
  1F-WA wet build-up 3.80 - 3.45 = 0.35 (= 0.10 finish + 0.25 sunken drop below the 1F T.O.S 3.70); soffit 3.45 - 0.20 =
        3.25. A ceiling under it taken at the 1F soffit 3.50 is off by 3.50 - 3.25 = +0.25 m (WRONG_REFERENCE).
  1F-WB slab top, soffit and wet build-up HELD (value None, never 0, never the 1F 3.70).
  2F    LINK_MISMATCH: datums 0.10 vs layer 0.15 -> CONFLICT; the soffit derived from that T.O.S (6.90) is CONFLICT too.
  2F-K  CONFLICT (+7.05 vs +7.10), never the average 7.075.
  FTG-A blinding top -1.80 + 0.10 = -1.70; footing bottom -1.70 + 0.07 = -1.63; footing top -1.63 + 0.60 = -1.03;
        neck run 0.30 - (-1.03) = 1.33; excavation 0.00 - (-1.80) = 1.80; limit -1.80 <= -1.50 SATISFIED. A neck top
        taken at the FFL +0.45 instead of the T.O.B +0.30: FINISHED_AS_STRUCTURAL (+0.15 m).
  FTG-B every level below the ground-beam top HELD, limit OPEN; relation to the formation 0.10 / 0.17 / 0.67 m.
  FTG-C limit VIOLATED (-1.40 > -1.50): the printed formation stands, the violation is reported, nothing adjusted."""
from __future__ import annotations

import copy

DC = "DRAWING-CONFIRMED"
WET = [["FFL", "SLAB_TOP", "WET_FLOOR_BUILD_UP"], ["SLAB_TOP", "SLAB_SOFFIT", "SLAB_THICKNESS"]]
FTG = [["GB_TOP", "FOOTING_TOP", "NECK_RUN"], ["FOOTING_TOP", "FOOTING_BOTTOM", "FOOTING_DEPTH"],
       ["FOOTING_BOTTOM", "BLINDING_TOP", "UNDERLAY"], ["BLINDING_TOP", "FORMATION", "BLINDING_THICKNESS"],
       ["EXISTING_GROUND", "FORMATION", "EXCAVATION_DEPTH"]]


def _d(chain, kind, value, ref, status=DC, **kw):
    return dict({"chain_id": chain, "kind": kind, "value": value, "status": status, "ref": ref}, **kw)


def _l(chain, layer, t, ref, status=DC):
    return {"chain_id": chain, "layer": layer, "thickness": t, "status": status, "ref": ref}


def project():
    datums = [
        _d("1F", "FFL", 3.80, "A-04 2-2"), _d("1F", "SLAB_TOP", 3.70, "S-11 T.O.S"),
        _d("1F-WA", "FFL", 3.80, "A-04 storey FFL"), _d("1F-WA", "SLAB_TOP", 3.45, "S-11 cut T.O.S sunken"),
        _d("1F-WB", "FFL", 3.80, "A-04 storey FFL"),
        _d("1F-WB", "SLAB_TOP", None, "S-10 hatch 'sunken slab' only", status="HELD"),
        _d("2F", "FFL", 7.20, "A-04"), _d("2F", "SLAB_TOP", 7.10, "S-13 T.O.S"),
        _d("2F-K", "SLAB_TOP", 7.10, "S-13 T.O.S"), _d("2F-K", "SLAB_TOP", 7.05, "S-14 T.O.S"),
    ]
    layers = [
        _l("1F", "FLOOR_BUILD_UP", 0.10, "A-12"), _l("1F", "SLAB_THICKNESS", 0.20, "S-10"),
        _l("1F", "BEAM_DEPTH", 0.60, "S-12"),
        _l("1F-WA", "SLAB_THICKNESS", 0.20, "S-10"), _l("1F-WB", "SLAB_THICKNESS", 0.20, "S-10"),
        _l("2F", "FLOOR_BUILD_UP", 0.15, "A-12"), _l("2F", "SLAB_THICKNESS", 0.20, "S-10"),
        _l("2F-K", "SLAB_THICKNESS", 0.20, "S-10"),
    ]
    chains = [{"chain_id": "1F", "family": "FLOOR"}, {"chain_id": "2F", "family": "FLOOR"},
              {"chain_id": "2F-K", "family": "FLOOR"},
              {"chain_id": "1F-WA", "family": "FLOOR_SUNKEN_WET", "links": WET},
              {"chain_id": "1F-WB", "family": "FLOOR_SUNKEN_WET", "links": WET}]
    for cid, h, fl in (("FTG-A", 0.60, -1.80), ("FTG-B", 0.50, None), ("FTG-C", 0.40, -1.40)):
        chains.append({"chain_id": cid, "family": "FOUNDATION_FOOTING", "links": FTG})
        datums += [_d(cid, "EXISTING_GROUND", 0.0, "A-01"), _d(cid, "GB_TOP", 0.30, "S-03 T.O.B"),
                   _d(cid, "FFL", 0.45, "A-04"),
                   _d(cid, "FORMATION", -1.50, "S-01 note 3", bound="AT_MOST"),
                   _d(cid, "FORMATION", fl, "S-01 F-1" if fl is not None else "not printed",
                      status=DC if fl is not None else "HELD")]
        layers += [_l(cid, "FOOTING_DEPTH", h, "S-02"), _l(cid, "UNDERLAY", 0.07, "S-03 5 + 2"),
                   _l(cid, "BLINDING_THICKNESS", 0.10, "S-03")]
    uses = [
        {"use_id": "CEIL-UNDER-WA", "quantity": "GF ceiling height under the 1F-WA wet room", "chain_id": "1F-WA",
         "needs": "SLAB_SOFFIT", "used": {"chain_id": "1F", "kind": "SLAB_SOFFIT"}, "ref": "takeoff T-x"},
        {"use_id": "WB-TOP", "quantity": "1F-WB slab top", "chain_id": "1F-WB", "needs": "SLAB_TOP",
         "used": {"chain_id": "1F", "kind": "SLAB_TOP"}, "ref": "takeoff T-y"},
        {"use_id": "NECK-A-FFL", "quantity": "neck A top", "chain_id": "FTG-A", "needs": "GB_TOP",
         "used": {"value": 0.45}, "ref": "takeoff T-z"},
        {"use_id": "NECK-A-OK", "quantity": "neck A top", "chain_id": "FTG-A", "needs": "GB_TOP",
         "used": {"kind": "GB_TOP"}, "ref": "takeoff T-z r2"},
    ]
    return {"base_system": "ARCH", "units": "m", "chains": chains, "datums": datums, "layers": layers, "uses": uses}


def in_mm(p):
    q = copy.deepcopy(p)
    q["units"] = "mm"
    for d in q["datums"]:
        if d["value"] is not None:
            d["value"] = round(d["value"] * 1000)
    for ly in q["layers"]:
        ly["thickness"] = round(ly["thickness"] * 1000)
    for u in q["uses"]:
        if "value" in u.get("used", {}):
            u["used"]["value"] = round(u["used"]["value"] * 1000)
    return q
