"""S6 Phase 1: the ARCH_TAKEOFF_V1 quantity snapshot of the synthetic villa (tools.arch_synth.villa) - every line,
room, opening, region and floor category, rounded to 1e-6 (the byte form differs between Python versions; the values
agree within 1e-9). tests/m9_s6/data/V1_SYNTHETIC_VILLA_SNAPSHOT.json was written by this script from the HEAD before
S6 Phase 1 (6b7a2e4), so tests/m9_s6/test_s6_frozen.py proves that V1 is unchanged.

usage: python3 -I research/urban_m9_s6/phase1/v1_snapshot.py REPO OUT_JSON
"""
import json
import sys
from pathlib import Path


def r6(x):
    return None if x is None else round(float(x), 6)


def snapshot(room, arch):
    return {
        "lines": sorted([ln["line_id"], ln["item_code"], ln["location"]["floor"], ln["location"]["room_id"],
                         ln["physical_element"], ln["unit"], r6(ln.get("measured_net")), ln["evidence_state"]]
                        for ln in room["lines"]),
        "unresolved": sorted([u.get("room_id") or "-", u.get("floor") or "-", u.get("item") or "-"]
                             for u in room["unresolved"]),
        "rooms": sorted([r["floor"], r["room_id"], r["class"], "+".join(r.get("codes") or []), r6(r.get("area_m2")),
                         r6(r.get("gross_m2"))] for r in arch["rooms"]),
        "openings": sorted([o["floor"], o["opening_id"], o["kind"], r6(o.get("width_m"))] for o in arch["openings"]),
        "regions": sorted([r["floor"], r["stage_state"], r.get("columns"), r6((r.get("plate") or {}).get("largest_m2"))]
                          for r in arch["regions"]),
        "floor_categories": sorted([f["floor"], sorted([k, r6(v)] for k, v in (f.get("categories_m2") or {}).items())]
                                   for f in arch["floor_areas"]),
    }


def main():
    repo, out = Path(sys.argv[1]).resolve(), Path(sys.argv[2])
    sys.path.insert(0, str(repo))
    import tempfile
    from tools import arch_synth as AS
    from tools import urban_boq_m9 as M9
    with tempfile.TemporaryDirectory() as td:
        dxf = Path(td) / "villa.dxf"
        AS.villa(str(dxf))
        room, arch, _E = M9.arch_compute(str(dxf), method="ARCH_TAKEOFF_V1")
    snap = snapshot(room, arch)
    snap["generated_from"] = {"method": "ARCH_TAKEOFF_V1", "fixture": "tools.arch_synth.villa()",
                              "rounding": "1e-6", "by": "research/urban_m9_s6/phase1/v1_snapshot.py"}
    out.write_text(json.dumps(snap, indent=0, ensure_ascii=True, sort_keys=True) + "\n", encoding="utf-8")
    print(out, len(snap["lines"]), "lines")


if __name__ == "__main__":
    main()
