"""T-105 evidence for the rebar-firewall declaration of engine/source/concrete_ledger_v3.py (synthetic villas only,
tests/t097 fixture, never a client drawing): CONCRETE_LEDGER_V3 must emit no reinforcement item and must leave every
route-G reinforcement item byte-identical. Run: .venv/bin/python -I research/agents_t105/check_ledger_v3_steel_passthrough.py
"""
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engine.source import concrete_ledger_v3 as V3          # noqa: E402
from tests.t097_concrete_ledger_v3 import fixture as FX     # noqa: E402
from tools import urban_boq_m2 as M2                        # noqa: E402

CONV = str(ROOT / "engine/profiles/URBAN_M8_GENERIC_CONVENTIONS_V6.json")


def main():
    ok = True
    with tempfile.TemporaryDirectory() as td:
        for seed, mirror in ((3, False), (7, False), (3, True)):
            d = Path(td) / f"s{seed}{int(mirror)}"
            d.mkdir()
            src = d / "villa.dxf"
            D, T = FX.write(seed, str(src))
            path = src
            if mirror:
                path = d / "m.dxf"
                FX.mirror_dxf(str(src), str(path))
            R = M2.compute([str(path)], conventions=CONV, route="G", completeness=True)
            rule = {"family": "BEAM", "mark": T["rings"][1]["mark"], "storey": "GF", "basis": "test: owner rule"}
            v3 = V3.measure(R, ring_rule=rule)
            items = V3.apply(R, v3)
            emitted = list(v3["beam_items"]) + list(v3.get("neck_items") or []) + \
                list((v3.get("v2") or {}).get("items") or [])
            steel_emitted = [i["item_id"] for i in emitted if i["trade"] != "CONCRETE"]
            route_steel = {i["item_id"]: i for i in R["items"] if i["trade"] == "REINFORCEMENT"}
            out_steel = {i["item_id"]: i for i in items if i["trade"] == "REINFORCEMENT"}
            superseded_steel = [k for k in v3["supersedes"] if k in route_steel]
            same = out_steel == route_steel
            print(f"seed {seed} mirror {mirror}: route reinforcement items {len(route_steel)}, after V3 "
                  f"{len(out_steel)}, byte-identical {same}; V3-emitted non-concrete items {len(steel_emitted)}; "
                  f"superseded reinforcement items {len(superseded_steel)}")
            ok &= same and not steel_emitted and not superseded_steel
    print("PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
