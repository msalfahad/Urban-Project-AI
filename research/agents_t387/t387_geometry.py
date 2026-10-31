"""T-387 geometry export (run once on the private structural DXF, output OUTSIDE the repository): route G's own plan
records (generic_route.detect + items_from on URBAN_M8_GENERIC_CONVENTIONS_V6 + the M4 profile, the same call as
tools/urban_boq_m2.route_generic) as JSON: per plan sheet the beam bands, slab faces and column boxes the candidate's
element ids rest on, and the route G items. Read only: nothing in the engine changes.

    python3 -I research/agents_t387/t387_geometry.py <ST dxf> <out.json>   (out: .work/private/..., never a worktree)
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
CONV = ROOT / "engine/profiles/URBAN_M8_GENERIC_CONVENTIONS_V6.json"
PROFILE = ROOT / "research/urban_engine_m4_correctness/profile_st7757_m4.json"


def _clean(x):
    if isinstance(x, dict):
        return {str(k): _clean(v) for k, v in x.items() if not callable(v)}
    if isinstance(x, (list, tuple)):
        return [_clean(v) for v in x]
    if isinstance(x, (int, float, str, bool)) or x is None:
        return x
    return str(x)


def main(argv=None):
    dxf, out = (argv or sys.argv[1:])[:2]
    if Path(out).resolve().is_relative_to(ROOT):
        raise SystemExit("--out must be outside the repository (private drawing geometry)")
    from tools import urban_intake as UI
    from engine.source import generic_route as GR
    generic = json.loads(CONV.read_text(encoding="utf-8"))
    prof = json.loads(PROFILE.read_text(encoding="utf-8"))
    merged = GR.merge_conventions(generic, prof, {})
    opt = GR.detect_options(merged)
    I = UI.read_dxf(dxf)
    if opt.get("local_origin"):
        I = GR.to_local_origin(I)
    D = GR.detect(I, typical_widths_m=GR.typical_gb_widths(merged), options=opt)
    items, reg, _risk = GR.items_from(D, merged, GR.storey_heights(merged))
    Path(out).write_text(json.dumps({"schema": "T387_ROUTE_G_GEOMETRY_V1", "conventions": CONV.name,
                                     "profile": PROFILE.name, "sheets": _clean(D["sheets"]),
                                     "items": _clean(items)}), encoding="utf-8")
    print("sheets", len(D["sheets"]), "items", len(items))


if __name__ == "__main__":
    main()
