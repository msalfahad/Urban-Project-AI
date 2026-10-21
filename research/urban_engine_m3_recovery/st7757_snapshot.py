"""One engine's view of the ST7757 structural set, as plain JSON (counts, family totals, item list): run once with
the M2 engine (its commit checked out in a separate worktree) and once with the current engine, each in its own
process, so the before / after tables come from live runs and never from edited numbers.

    python3 -I research/urban_engine_m3_recovery/st7757_snapshot.py --engine-root ROOT --profile P.json \
            --out OUT.json [--evidence DETAIL_EVIDENCE.json]

Nothing here writes into a package folder; owner text never leaves the engine (counts and ids only).
"""

from __future__ import annotations

import inspect
import json
import sys
import time
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
DXF = REPO / "data/inputs/by_sha256/9f9d1179a5d2a6635f9b412915a72184b7db1ff7729f4ab39a72dc3391738079.dxf"


def snapshot(root, profile, evidence=None):
    sys.path.insert(0, str(root))
    from engine.source import generic_route as GR
    from engine.source import provisional_estimate as PE
    from tools import urban_intake as UI
    gen = root / "engine/profiles/URBAN_M3_GENERIC_CONVENTIONS_V2.json"
    gen = gen if gen.exists() else root / "engine/profiles/URBAN_M2_GENERIC_CONVENTIONS_V1.json"
    t0 = time.perf_counter()
    I = UI.read(DXF)                         # the private drawing of this checkout (git-ignored, never in a worktree)
    t1 = time.perf_counter()
    conv = GR.merge_conventions(json.loads(gen.read_text()), json.loads(Path(profile).read_text()))
    kw = {}
    if "typical_widths_m" in inspect.signature(GR.detect).parameters:
        kw["typical_widths_m"] = GR.typical_gb_widths(conv)
    D = GR.detect(I, **kw)
    t2 = time.perf_counter()
    ikw = {"evidence": json.loads(Path(evidence).read_text())} if evidence and \
        "evidence" in inspect.signature(GR.items_from).parameters else {}
    items, reg, risk = GR.items_from(D, conv, GR.storey_heights(conv), **ikw)
    PE.check(items, conv)
    t3 = time.perf_counter()
    det = {}
    for sid, rec in sorted(D["sheets"].items()):
        r = {"role": rec["sheet"]["role"], "storey": rec["sheet"]["storey"]}
        if rec.get("footings"):
            r["footings"] = dict(Counter(f["state"] for f in rec["footings"]))
        if rec.get("columns"):
            r["column_occurrences"] = dict(Counter(c.get("state", "?") for c in rec["columns"]))
        if "beams" in rec:
            r["bands"] = dict(Counter(b["state"] for b in rec["beams"]))
            r["marks"] = dict(Counter(m["state"] for m in rec.get("marks", [])))
            r["band_widths_m"] = dict(Counter(str(round(b["width_m"], 2)) for b in rec["beams"]))
        if rec.get("slab"):
            r["faces"] = dict(Counter(f["class"] for f in rec["slab"]["faces"]))
            r["face_area_m2"] = {k: round(v, 3) for k, v in Counter(
                {c: sum(f["area_m2"] for f in rec["slab"]["faces"] if f["class"] == c)
                 for c in {f["class"] for f in rec["slab"]["faces"]}}).items()}
            if rec["slab"].get("regions_m2"):
                r["regions_m2"] = {k: round(v, 3) for k, v in rec["slab"]["regions_m2"].items() if v}
        if rec.get("straps"):
            r["straps"] = dict(Counter(b["state"] for b in rec["straps"].get("bands", [])))
        det[sid] = r
    fam = {}
    for row in PE.rollup(items, ("trade", "family")):
        fam[f"{row['trade']}|{row['family']}"] = {k: round(row[k], 4) if isinstance(row[k], float) else row[k]
                                                 for k in ("PROVISIONAL_LOW", "PROVISIONAL_BASE", "PROVISIONAL_HIGH",
                                                           "N_PROVISIONAL", "N_UNRESOLVED", "UNRESOLVED_EXPOSURE_LOW",
                                                           "UNRESOLVED_EXPOSURE_HIGH")}
    return {"engine_root": root.name, "conventions": gen.name, "profile": Path(profile).name,
            "evidence": Path(evidence).name if ikw else None,
            "seconds": {"intake": round(t1 - t0, 3), "detect": round(t2 - t1, 3), "items": round(t3 - t2, 3)},
            "families": fam, "detection": det, "risk": dict(sorted(Counter(r["KIND"] for r in risk).items())),
            "rebar_states": dict(sorted(Counter(r["REBAR_STATE"] for r in reg).items())),
            "items": [{k: i[k] for k in ("item_id", "component_id", "trade", "family", "storey", "category", "low",
                                         "base", "high", "blocker", "exposure_low", "exposure_high", "dia_mm")}
                      for i in items]}


def main(argv):
    a = dict(zip(argv[::2], argv[1::2]))
    root = Path(a["--engine-root"]).resolve()
    res = snapshot(root, a["--profile"], a.get("--evidence"))
    Path(a["--out"]).write_text(json.dumps(res, indent=1, default=str))
    print(json.dumps({k: res[k] for k in ("engine_root", "conventions", "seconds", "rebar_states")}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
