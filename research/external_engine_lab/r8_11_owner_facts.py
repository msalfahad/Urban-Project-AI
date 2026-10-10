"""R8.11 owner clarification (Hall / Lobby passage) as a SOURCE-BOUND PHYSICAL FACT, and the OPEN_PASSAGE_SITE
record it describes.

    python3 research/external_engine_lab/r8_11_owner_facts.py <work>      # (re)writes data/registry/OWNER_PHYSICAL_FACTS.json

The fact is bound like an owner claim (owner_claims): revision + DXF anchor + region + frame + each source part's
key and fingerprint. A moved part, another revision or another region makes the fact NOT apply. In R8.11 it is used
for three things only, none of which changes a TS01 input, a site or an area:
  1. the owner REVIEW of the H2431 band-end topology closure (physical continuity of the east jamb);
  2. the CLASSIFICATION of the H2430 blocker (physical role resolved; engine representation pending);
  3. the attributes of the owner-declared Hall / Lobby OPEN_PASSAGE_SITE (door, head, side construction).
It is NOT applied as a part-role claim to H2430 (that would close the wall core and compute Q-14): the generic
fragment-aware band rule (E-R8.12-01) is frozen and run blind first; the part-scoped claim is the fallback.
Project semantics live here only.
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).parent))

import r8_8_topology as LAB                                                                   # noqa: E402
from engine.source import owner_claims as OC                                                  # noqa: E402

C = LAB.C
FILE = ROOT / "data/registry/OWNER_PHYSICAL_FACTS.json"
FACT_ID = "QORTUBA-NEW-HALL-LOBBY-OPEN-PASSAGE-OWNER-001"
REAL_WALL_END = "REAL_WALL_END"
REAL_WALL_FACE = "REAL_WALL_FACE"
READINGS = {
    "2430": (REAL_WALL_END, "west jamb end face (block + plaster); the line meets both face end points exactly"),
    "2431": (REAL_WALL_END, "east jamb end face (block + plaster); its 9.2 mm shortfall is a DRAFTING discontinuity, "
                            "not an opening through the wall"),
    "470": (REAL_WALL_FACE, "west jamb wall, lower face (fragment 1 of 2)"),
    "471": (REAL_WALL_FACE, "west jamb wall, lower face (fragment 2 of 2)"),
    "477": (REAL_WALL_FACE, "west jamb wall, upper face"),
    "2296": (REAL_WALL_FACE, "east jamb wall, lower face"),
    "2297": (REAL_WALL_FACE, "east jamb wall, upper face")}
STATEMENT = {
    "passage": "the Hall / Lobby connection is a REAL OPEN PASSAGE: no door, no blockwork across the opening",
    "approx_clear_width_m": 1.00, "approx_width_meaning": "design meaning only - never a calibration target; the "
                                                          "deterministic width is measured from source geometry",
    "clear_height_m": 2.20, "head": "BLOCK / PLASTERED HEAD at 2.20 m clear height",
    "sides": "BLOCK + PLASTER jambs / wall ends on both sides",
    "wall_end_lines": "the geometry around H2430 / H2431, including the wall-end lines, is REAL wall / block "
                      "construction",
    "gap": "the ~9.2 mm H2431 disconnect is not an intended secondary opening",
    "closure": "a derived topology-only closure may bridge the drafting discontinuity if the generic wall-band "
               "evidence establishes it; it carries ZERO material"}


def _parts(inp):
    return {p.identity.source_handle: p for p in inp.parts if not p.identity.instance_handles and p.kind == "SEGMENT"}


def build(inp) -> dict:
    """The fact record, bound to the CURRENT source parts (run once, committed; later runs only verify)."""
    P = _parts(inp)
    rev = inp.revision
    return {
        "SCHEMA": "URBAN_OWNER_PHYSICAL_FACTS_V1",
        "facts": [{
            "fact_id": FACT_ID, "version": 1, "kind": "OPEN_PASSAGE_CONSTRUCTION", "authority": ["PROJECT_OWNER"],
            "received": "R8.11 owner clarification (after the R8.11 package)",
            "scope": {"project": "QORTUBA", "source_revision_id": rev.revision_id,
                      "source_anchor_sha256": rev.anchor_sha256, "region_id": inp.region_id, "frame_id": inp.frame_id,
                      "plan": "PLAN_VARIANT_4_SELECTED"},
            "parts": [{"handle": h, "key": P[h].identity.key, "source_layer": P[h].layer,
                       "fingerprint": OC.part_fingerprint(P[h]), "physical_reading": READINGS[h][0],
                       "note": READINGS[h][1]} for h in READINGS],
            "statement": STATEMENT,
            "used_for_in_r8_11": ["REVIEW of the H2431 topology closure (east-jamb continuity)",
                                  "CLASSIFICATION of the H2430 blocker (physical role resolved, engine representation "
                                  "pending)", "ATTRIBUTES of the Hall / Lobby OPEN_PASSAGE_SITE record"],
            "not_applied_in_r8_11": ["a part-role claim admitting H2430 as boundary (deferred: E-R8.12-01 first, blind; "
                                     "the part-scoped claim is the fallback)"],
            "never": ["a wall or block quantity across the opening", "material on a topology closure",
                      "a width, area or quantity (the width is measured from source)", "a source edit or new entity",
                      "transfer to another revision, region or to the DWG", "a generic rule change"]}]}


def load():
    return json.loads(FILE.read_text())["facts"]


def bind(fact, inp) -> dict:
    """APPLIES only for the same revision + anchor + region + frame and unchanged part fingerprints."""
    rev = inp.revision
    sc = fact["scope"]
    if rev is None or rev.revision_id != sc["source_revision_id"] or rev.anchor_sha256 != sc["source_anchor_sha256"]:
        return {"fact": f"{fact['fact_id']}@v{fact['version']}", "state": OC.SOURCE_SCOPE_MISMATCH, "parts": []}
    if inp.region_id != sc["region_id"] or inp.frame_id != sc["frame_id"]:
        return {"fact": f"{fact['fact_id']}@v{fact['version']}", "state": OC.REGION_SCOPE_MISMATCH, "parts": []}
    by_key = {p.identity.key: p for p in inp.parts}
    per = []
    for q in fact["parts"]:
        p = by_key.get(q["key"])
        st = (OC.PART_NOT_IN_SOURCE if p is None else
              OC.STALE_PART_FINGERPRINT if OC.part_fingerprint(p) != q["fingerprint"] else OC.APPLIES)
        per.append({"handle": q["handle"], "state": st, "physical_reading": q["physical_reading"]})
    ok = all(x["state"] == OC.APPLIES for x in per)
    return {"fact": f"{fact['fact_id']}@v{fact['version']}", "state": OC.APPLIES if ok else per[0]["state"]
            if len({x["state"] for x in per}) == 1 else "PARTIAL_NOT_APPLIED", "parts": per}


def readings(bindings) -> dict:
    """{handle: (reading, fact)} for facts that APPLY in full (a partial binding applies to nothing)."""
    return {x["handle"]: (x["physical_reading"], b["fact"]) for b in bindings if b["state"] == OC.APPLIES
            for x in b["parts"]}


def hall_lobby_passage(inp, res, binding) -> dict:
    """The owner-declared Hall / Lobby OPEN_PASSAGE_SITE, with geometry MEASURED from the source faces (the
    owner's ~1.00 m is design meaning, not a value)."""
    P = _parts(inp)
    u = inp.unit_native_to_mm
    w_a, w_b = P["471"].geometry[2:], P["477"].geometry[2:]              # west jamb end: face end points (= H2430)
    e_a, e_b = P["2296"].geometry[:2], P["2297"].geometry[:2]            # east jamb end: face start points
    width = e_a[0] - w_a[0]
    thick = math.dist(e_a, e_b)
    closure = next((c for c in res["topology_closures"]["closures"]
                    if {OC_h(x) for x in c["source_evidence_ids"][:2]} == {"2296", "2297"}), None)
    from engine.source import topology as T
    sid, _ = T.locate(res["_arr"], res["sites"], ((w_a[0] + e_a[0]) / 2, (w_a[1] + w_b[1]) / 2), 0.0)
    strip = [list(w_a), list(e_a), list(e_b), list(w_b)]
    applies = binding["state"] == OC.APPLIES
    return {
        "passage_id": "OP-OWNER-HALL-LOBBY", "kind": "OPEN_PASSAGE_SITE",
        "record_origin": "OWNER_DECLARED (geometry measured from source)",
        "engine_detection": "NOT_DETECTED: the west jamb (H470 + H471 / H477) is no established wall band under "
                            "WALL_BAND_POLICY_V2 (fragmented face; E-R8.12-01)",
        "owner_fact": binding["fact"], "owner_fact_state": binding["state"],
        "clear_width_mm_measured": round(width * u, 2), "owner_approx_clear_width_m": STATEMENT["approx_clear_width_m"],
        "width_discrepancy_mm": round(width * u - 1000.0 * STATEMENT["approx_clear_width_m"], 1),
        "width_note": "deterministic width = measured face-to-face distance; the owner's ~1.00 m is design meaning. "
                      "The 196 mm difference exceeds any drafting / plaster tolerance and matches the old revision's "
                      "QP-17 1.200 m: recorded for review before any skirting / reveal quantity, not a value change",
        "wall_thickness_mm": round(thick * u, 1),
        "strip_polygon": [[round(v, 4) for v in q] for q in strip],
        "strip_footprint_m2_geometry": round(width * thick * (u ** 2) / 1e6, 4),
        "clear_height_m": STATEMENT["clear_height_m"] if applies else None,
        "door": "NONE" if applies else "NOT_ESTABLISHED",
        "side_construction": "BLOCK + PLASTER" if applies else "NOT_ESTABLISHED",
        "head": STATEMENT["head"] if applies else "NOT_ESTABLISHED_IN_SOURCE",
        "physically_connected": True, "strip_in_site": sid, "trade_allocation": "NOT_ALLOCATED",
        "topology": {"west_end": "OPEN into the H2430 wall core (the core stays in the HALL until the band is "
                                 "established or a claim applies)",
                     "east_end": f"closed by {closure['closure_id'] if closure else None} (zero material)",
                     "across_the_opening": "NOTHING: no closure, no wall, no block crosses the passage"},
        "trade_surfaces_record_only": {
            "floor_strip": {"plan": "strip_polygon", "now": f"inside site {sid} (HALL floor footprint)"},
            "left_reveal_west_jamb": {"plan_segment": [[round(v, 4) for v in w_a], [round(v, 4) for v in w_b]],
                                      "source": "H2430 (DIM layer, owner: real wall end) = H471 / H477 end points",
                                      "height_m": STATEMENT["clear_height_m"], "material": "BLOCK + PLASTER (owner)"},
            "right_reveal_east_jamb": {"plan_segment": [[round(v, 4) for v in e_a], [round(v, 4) for v in e_b]],
                                       "source": "H2296 / H2297 start points (H2431 is 9.2 mm short and is not used)",
                                       "height_m": STATEMENT["clear_height_m"], "material": "BLOCK + PLASTER (owner)",
                                       "same_plan_segment_as": closure["closure_id"] if closure else None,
                                       "two_records_rule": "the closure (material NONE) and this reveal (real "
                                                           "material) share one plan segment: quantity may only "
                                                           "ever come from the reveal record"},
            "top_reveal_soffit": {"plan": "strip_polygon", "level_m": STATEMENT["clear_height_m"],
                                  "material": "BLOCK / PLASTERED HEAD (owner)"},
            "wall_faces_around": {"west": ["H471", "H477", "(H470)"], "east": ["H2296", "H2297"],
                                  "above_head": "wall face between 2.20 m and the wall height on both room sides"}},
        "double_count_guard": [
            "wall plaster / paint: the jamb end faces and the soffit are REVEAL surfaces, never also room wall "
            "perimeter; the room-side wall faces lose the opening (width x 2.20 m), not more",
            "floor finish: the strip is one floor region; it is never also a threshold and never moved into a room "
            "to match a total",
            "ceiling (Q-14): the strip lies inside the HALL footprint, so the owner's Q-14 claim (ceiling = floor "
            "footprint) counts it; its top is a soffit at 2.20 m - the reveal trade must not count it again unless "
            "an allocation rule removes it from the ceiling",
            "opening / reveal quantities: computed once, from the reveal records, never from the topology closure"],
        "material_on_any_closure": "NONE"}


def OC_h(key):
    return key.split("|")[1][1:] if key and "|" in key else key


def main(work):
    import r8_10_qortuba as Q10
    inps, _, _ = Q10.inputs(work)
    FILE.write_text(json.dumps(build(inps["NEW_K2"]), indent=1, ensure_ascii=False) + "\n")
    print(FILE)


if __name__ == "__main__":
    main(sys.argv[1])
