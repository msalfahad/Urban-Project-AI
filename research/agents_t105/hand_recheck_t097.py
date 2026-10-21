"""T-105 depth check of CONCRETE_LEDGER_V3 on the T-097 synthetic villas (tools/synthetic_villa, NOT a client drawing).
Hand truth from the design grid printed by tests/t097_concrete_ledger_v3/fixture.plan (column centres and sizes, beam
B x H from the schedule rows), worked before the run:

1 beam split by a planted column
  seed 3 (mm): B1 0.20 x 0.50 on the span between columns x 8.75 (0.30 wide) and x 13.50 (0.20 wide):
     clear 13.50 - 0.10 - (8.75 + 0.15) = 4.50 m -> one span 4.50 x 0.20 x 0.50 = 0.450 m3
  seed 7 (m):  B5 0.25 x 0.50 between x 7.60 (0.50 wide) and x 12.95 (0.30 wide):
     clear 12.95 - 0.15 - (7.60 + 0.25) = 4.95 m -> 4.95 x 0.25 x 0.50 = 0.61875 m3
2 ring (arc band) with its printed mark: ri 1.00, ro 1.00 + B 0.20, H 0.50, isolated:
     pi (1.20^2 - 1.00^2) = pi x 0.44 = 1.382301 m2 x 0.50 = 0.691150 m3 (both seeds; polygon tolerance 1e-4 m2)
3 printed upstand 0.10 x 0.15 (SECTION A-A) on the cut span
  seed 3: B3 between x 0.00 (0.30) and x 4.60 (0.20): clear 4.60 - 0.10 - 0.15 = 4.35 m -> 0.10 x 0.15 x 4.35 = 0.06525
  seed 7: B1 between x 0.00 (0.30) and x 4.25 (0.25): clear 4.25 - 0.125 - 0.15 = 3.975 m -> 0.059625 m3
Mirrored seed 3 must give the same numbers.
"""
import math
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from engine.source import concrete_ledger_v3 as V3          # noqa: E402
from tests.t097_concrete_ledger_v3 import fixture as FX     # noqa: E402
from tools import urban_boq_m2 as M2                        # noqa: E402

CONV = str(ROOT / "engine/profiles/URBAN_M8_GENERIC_CONVENTIONS_V6.json")
HAND = {3: {"planted": 0.450, "ring": math.pi * 0.44 * 0.50, "upstand": 0.06525},
        7: {"planted": 0.61875, "ring": math.pi * 0.44 * 0.50, "upstand": 0.059625}}


def main():
    ok = True
    with tempfile.TemporaryDirectory() as td:
        for seed, mirror in ((3, False), (7, False), (3, True)):
            d = Path(td) / f"s{seed}{int(mirror)}"
            d.mkdir()
            src = d / "v.dxf"
            D, T = FX.write(seed, str(src))
            path = src
            if mirror:
                path = d / "m.dxf"
                FX.mirror_dxf(str(src), str(path))
            R = M2.compute([str(path)], conventions=CONV, route="G", completeness=True)
            v3 = V3.measure(R)                                   # no owner ring rule: the printed ring only
            p = T["planted"]
            span = [i for i in v3["beam_items"] if i["category"] != "UNRESOLVED" and i["base"] is not None
                    and abs(i["base"] - p["v3_m3"]) < 0.02 and "RING" not in i["component_id"]
                    and "UPSTAND" not in i["component_id"]]
            rings = [i for i in v3["beam_items"] if ":RING" in i["component_id"]]
            held_rings = [r for r in v3["rings"] if r["state"] not in ("PRINTED_MARK", "OWNER_RULE")]
            ups = [u for u in v3["upstands"] if u.get("state") == "MEASURED"]
            h = HAND[seed]
            got = {"planted": span[0]["base"] if len(span) == 1 else None,
                   "ring": rings[0]["base"] if len(rings) == 1 else None,
                   "upstand": ups[0]["volume_m3"] if len(ups) == 1 else None}
            tol = {"planted": 1e-6, "ring": 1e-4 * 0.5 + 1e-9, "upstand": 1e-6}
            print(f"seed {seed} mirror {mirror}")
            for k in ("planted", "ring", "upstand"):
                good = got[k] is not None and abs(got[k] - h[k]) <= tol[k]
                ok &= good
                print(f"  {k}: engine {got[k]} hand {round(h[k], 6)} {'OK' if good else 'DIFF'}")
            print(f"  unmarked ring without owner rule: {len(held_rings)} held, quantity line none "
                  f"(annulus {[round(r['annulus_m2'], 6) for r in held_rings]} m2 listed)")
            ok &= len(held_rings) == 1
    print("PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
