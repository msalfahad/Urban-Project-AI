"""T-308 step 1: the merged formwork r3 drawing-face walk re-run with ONE binding corrected: T-139 face GF-095 (the
drawn curved B7 corner of the GF roof slab, ST p.4) bound to its register member BM-GF-049 (route G band BAND0049).

    python3 -I research/agents_t308/t308_walk_delta.py <faces.json> <bands.json> [--write]

faces.json = `python3 -I research/agents_t139/slab_faces.py <ST7757 dxf.dxf> faces.json` (the T-139 faces formwork r3
walks); bands.json = `python3 -I research/agents_t110/scripts/bands.py research/urban_engine_m4_correctness/st7757_route_g
bands.json` (route G band polygons, fit 0.6 mm). Both are re-made from the private Drive copy 'ST7757 dxf.dxf'
(sha 9f9d1179) and the committed route G overlay; nothing private is written: the output holds face ids, member ids,
categories and m2 / m only (no coordinate, no drawing text).

Why (F-T293-P2-02, T-293 part 2 MERGED a1e0c43a): the candidate line P-C:BEAMS:GF:BAND0049 (B7 20 x 75, 0.282743 m3)
carried element-method faces but no drawing face. Read on the drawing (this run, by handle): BAND0049 is NOT a void-ring
piece (the T-110 register and the r3 hard-code 'B7 ring band' name it so; T-252 found it outside the ring): it is a
quarter-circle corner beam between the B2 run and the beam strip x-face 2B2 / 2B3, drawn by two concentric arcs 29F
(R 1.300) and 2A0 (R 1.100), 90 degrees, closed by line 314 (column COL-GF-15 side) and line 484 (the strip side), mark
block 47D 'b7' beside its outer arc. Its plan is exactly T-139 face GF-095 (0.376924 m2 as polygonised; exact annulus
quarter pi / 4 (1.300^2 - 1.100^2) = 0.376991 m2), which the r3 walk left UNMATCHED because (a) the tag lies 0.135 m
outside the face, (b) B7 has several members so the mark is not unique, (c) a curved member has no H / V axis rectangle
for the nearest-band search. Route G's own band BAND0049 covers 99.49 % of GF-095 and no other band touches it.

Rule R-T308-3 (research scope, any villa): a band face that the walk leaves UNMATCHED is bound to the register member
whose route G band covers at least 95 % of the face, when no other band covers any of it and the member's mark is
printed beside the face; the walk is then re-run with that one binding, nothing else re-cut; every changed record is
listed (before -> after) and every other record must be byte-identical to the merged walk.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
RES = HERE.parent
sys.path.insert(0, str(RES / "agents_t293"))
import t293p2_walk as W  # noqa: E402  (merged part-2 walk driver, read only)
sys.path.insert(0, str(HERE))
import t308_rules as R8  # noqa: E402

T = W.T
FACE, MEMBER, BAND = "GF-095", "BM-GF-049", "BAND0049@GF"
OUT = HERE / "T308_WALK_DELTA_BAND0049.json"
COVER_MIN = 0.95


def _key(r):
    return (r["floor"], r["face"], r["category"], r.get("run") or "", r.get("owner") or "")


def run(faces_json, bands_json, bind):
    orig = T.rd

    def rd(p):
        rows = orig(p)
        if bind and p.endswith("agents_t139/PANELS.csv"):
            hit = [r for r in rows if r["id"] == FACE]
            if len(hit) != 1 or hit[0]["cls"] != "BEAM_OR_COLUMN":
                raise SystemExit(f"{FACE}: expected one BEAM_OR_COLUMN panel row")
            hit[0]["evidence"] = hit[0]["evidence"] + f" ({MEMBER}, T-308 R-T308-3)"
        return rows

    T.rd = rd
    try:
        recs, _lines = W.records(faces_json)
    finally:
        T.rd = orig
    for r in recs:
        r["m2"] = round(r["m2"], 9)
    return recs


def coverage(faces_json, bands_json):
    from shapely.geometry import Polygon
    from shapely.wkt import loads
    face = next(f for f in json.loads(Path(faces_json).read_text())["GF"] if f["id"] == FACE)
    g = loads(face["wkt"])
    bands = json.loads(Path(bands_json).read_text())
    own = Polygon(bands[BAND]["pts"]).intersection(g).area / g.area
    other = {k: round(Polygon(v["pts"]).intersection(g).area, 9) for k, v in bands.items()
             if k.endswith("@GF") and k != BAND and Polygon(v["pts"]).intersection(g).area > 1e-9}
    return round(g.area, 9), round(own, 6), other


def main(argv):
    write = "--write" in argv
    argv = [a for a in argv if a != "--write"]
    faces_json, bands_json = argv[:2]
    area, own, other = coverage(faces_json, bands_json)
    if R8.band_binding(area, dict(other, **{BAND: own * area}), COVER_MIN) != BAND:
        raise SystemExit(f"R-T308-3 not met: {BAND} covers {own:.4f} of {FACE}, other bands {other}")
    W.install_split(bands_json)
    merged = json.loads((RES / "agents_t293" / "T293P2_WALK_RECORDS.json").read_text())["records"]
    before = run(faces_json, bands_json, bind=False)
    m0 = {_key(r): r["m2"] for r in merged}
    m1 = {_key(r): r["m2"] for r in before}
    if m0 != m1:
        raise SystemExit("the unbound re-run does not reproduce the merged T293P2_WALK_RECORDS.json")
    after = run(faces_json, bands_json, bind=True)
    m2 = {_key(r): r for r in after}
    changed = []
    for k in sorted(set(m1) | set(m2)):
        a, b = m1.get(k), (m2[k]["m2"] if k in m2 else None)
        if a != b:
            rec = m2.get(k) or next(r for r in before if _key(r) == k)
            changed.append({"floor": k[0], "face": k[1], "category": k[2], "owner": k[4] or None,
                            "owner_kind": rec["owner_kind"], "owner_status": rec["owner_status"],
                            "pieces": rec["pieces"], "before_m2": a, "after_m2": b})
    faces_touched = {c["face"] for c in changed}
    if not faces_touched <= {FACE, "GF-093"}:
        raise SystemExit(f"the binding moved records outside {FACE} and its column neighbour: {faces_touched}")
    doc = {"schema": "T308_WALK_DELTA_V1",
           "source": "formwork r3 walk (T-163 MERGED 659f889f) via t293p2_walk (T-293 part 2 MERGED a1e0c43a) on the "
                     "T-139 faces of 'ST7757 dxf.dxf' (sha 9f9d1179); one binding changed: GF-095 -> BM-GF-049",
           "rule": "R-T308-3",
           "face": FACE, "member": MEMBER, "band": BAND, "face_plan_m2": area, "band_cover_of_face": own,
           "other_bands_on_face": other, "unchanged_records": len(m1) - sum(1 for c in changed if c["before_m2"] is not None),
           "merged_records": len(m0), "changed": changed}
    print(json.dumps({k: v for k, v in doc.items() if k != "changed"}, indent=1))
    for c in changed:
        print(c)
    if write:
        OUT.write_text(json.dumps(doc, indent=1, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main(sys.argv[1:])
