"""Phase 2A demo tables (synthetic only, reproducible): the door BOQ of the synthetic door plan (PVC, aluminium, main
entrance, provisional, lift excluded) with and without a sourced door height, and the surface ledger of the synthetic
villa. usage: python3 -I research/urban_m9_p2a/demo_p2a.py > DEMO.md"""
import sys
from pathlib import Path
import os
ROOT = Path(os.environ.get("URBAN_ROOT") or Path(__file__).resolve().parents[2])
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests" / "m9_p2a"))
import tempfile                                                      # noqa: E402
import p2a_helpers as H                                              # noqa: E402
from engine.source import arch_measure as AM                         # noqa: E402
from engine.source import door_model as DM                           # noqa: E402


def fmt(v, d=3):
    return "-" if v is None else (f"{v:.{d}f}" if isinstance(v, float) else str(v))


def door_table(model):
    print("| Section | Class | State | Leaves | Width m (source) | Height m (state) | Area m² (state) | Evidence |")
    print("|---|---|---|---|---|---|---|---|")
    for r in DM.schedule_rows(model):
        print(f"| {r['section']} | {r['boq_class']} | {r['state']} | {r['leaf_count']} | "
              f"{fmt(r['structural_opening_width_m'])} ({r['structural_opening_source'].split(' ')[0]}) | "
              f"{fmt(r['height_m'])} ({r['height_state']}) | {fmt(r['area_m2'])} ({r['area_state'].split(':')[0]}) | "
              f"{', '.join(r['evidence_kinds'])} |")
    s = model["summary"]
    print("\n| Released total | Doors | Leaves | Width m | Area m² (sourced heights only) | Heights BLOCKED |")
    print("|---|---|---|---|---|---|")
    for cls, v in s["released"].items():
        print(f"| {cls} | {v['count']} | {v['leaves']} | {fmt(v['width_m'])} | {fmt(v['area_m2_confirmed'])} | "
              f"{v['height_blocked']} |")
    print(f"\nNot released: {s['provisional_not_released']} (provisional / unresolved / candidates), lift doors excluded: "
          f"{s['lift_excluded']}; main entrance: {model['main_entrance']['state']}; conservation: "
          f"{'OK' if model['conservation_ok'] else 'FAILED'}; findings: "
          f"{', '.join(sorted({f['code'] for f in model['findings']}))}")


print("# Phase 2A demo (synthetic only)\n")
print("## 1. Door BOQ: the synthetic door plan, no height source\n")
_S, _M, m0 = H.door_run(H.door_fixture())
door_table(m0)
print("\n## 2. The same plan with a sourced door height (facts opening_heights.DOOR = 2.10 m, authority given)\n")
facts = {"schema": AM.FACTS_SCHEMA, "opening_heights": {"DOOR": {"value_m": 2.1, "authority": "synthetic schedule"}}}
_S, _M, m1 = H.door_run(H.door_fixture(), facts=facts)
door_table(m1)
print("\n## 3. A plan with two entrance candidates (never resolved by assumption)\n")
ops = H.DOOR_OPENINGS + [("DOOR", "x", 0, 200, 1200, 2100, None)]
sw = H.DOOR_SWINGS + (((200, 1200), 900, 90, 180),)
_S, _M, m2 = H.door_run(H.door_fixture(openings=ops, swings=sw))
door_table(m2)
print("\n## 4. Surface ledger of the synthetic villa (ARCH_TAKEOFF_V2.1)\n")
from tools import arch_synth as AS                                   # noqa: E402
from tools import urban_boq_m9 as M9                                 # noqa: E402
p = Path(tempfile.mkdtemp()) / "villa.dxf"
AS.villa(str(p))
room, arch, _E = M9.arch_compute(str(p), method="ARCH_TAKEOFF_V2.1")
L = arch["ledger"]
print(f"Table {L['table']['id']} ({L['table']['status']}, digest `{L['table']['digest'][:16]}`), {len(L['records'])} records\n")
print("| Status | Records |\n|---|---|")
for k, v in L["summary"]["by_status"].items():
    print(f"| {k} | {v} |")
print("\n| Finding | Element kind | Surface | Records |\n|---|---|---|---|")
for f in L["findings"]:
    print(f"| {f['code']} | {f['element_kind']} | {f['surface']} | {f['records']} |")
