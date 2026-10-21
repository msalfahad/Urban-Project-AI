"""T-071 Alsenan run (read only): EXTERIOR_SPACES_V1 on every exterior label the ROOM_LABEL_GUARD_V1 holds.

Runs ARCH_TAKEOFF_V2.9 once, keeps per plan region what arch_rooms.spaces sees (entities, layer roles, the items of its
first boundary arrangement, its openings), guards the room labels against the run's faces, and traces each held
exterior label with engine/source/exterior_spaces.py. Output: areas, lengths, counts and entity handles only (no
coordinates, no drawing text other than the room-vocabulary code).

    python research/agents_t071/run_alsenan.py <P7757.dxf> <out.json> [--facts facts.json]
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.source import arch_rooms as AR  # noqa: E402
from engine.source import exterior_spaces as XS  # noqa: E402
from engine.source import room_label_guard as G  # noqa: E402
from engine.source import topology as TP  # noqa: E402


def capture(drawing, method="ARCH_TAKEOFF_V2.9", layer_roles=None):
    from tools import urban_boq_m9 as M
    cap, cur = {}, [None]
    o_spaces, o_build = AR.spaces, TP.build

    def spaces(ents, roles, unit_m, **kw):
        cur[0] = kw.get("region_id")
        cap[cur[0]] = {"builds": []}
        r = o_spaces(ents, roles, unit_m, **kw)
        cap[cur[0]].update(ents=ents, roles=roles, unit_m=unit_m, res=r)
        cur[0] = None
        return r

    def build(items, eps):
        if cur[0] is not None:
            cap[cur[0]]["builds"].append(list(items))
        return o_build(items, eps)
    AR.spaces, TP.build = spaces, build
    try:
        res = M.arch_compute(str(drawing), method=method, layer_roles=layer_roles)
    finally:
        AR.spaces, TP.build = o_spaces, o_build
    return res, cap


def run(drawing, facts=None, layer_roles=None, captured=None):
    res, cap = captured or capture(drawing, layer_roles=layer_roles)
    out = []
    for rid, c in sorted(cap.items()):
        if "ents" not in c or not c["builds"]:
            continue
        faces = _faces(c["res"])
        texts = c["ents"].get("texts") or []
        g = G.guard(faces, texts, frame=rid, unit_m=c["unit_m"])
        held_ids = {r["text_id"] for r in g["held"]}
        labels = [t for t in texts if t["id"] in held_ids]
        building, layers, openings, _t = XS.inputs_from_spaces(c["ents"], c["roles"], c["builds"][0], c["res"])
        tr = XS.trace(labels, building, layers, c["unit_m"], openings=openings, facts=facts, frame=rid, texts=texts)
        roles_chk = XS.layer_role_check(c["roles"], {l: XS.items_of_layer(c["ents"], l) for l in c["roles"]},
                                        texts, c["unit_m"])
        XS.apply_role_check(tr, roles_chk)
        out.append({"region": rid, "guard_summary": g["summary"], "trace_summary": tr["summary"],
                    "records": XS.report_rows(tr), "layer_role_check": roles_chk})
    return out


def _faces(spaces_result):
    """the run's room faces (polygons) for the guard, from arch_rooms.spaces' result."""
    out = []
    for f in spaces_result.get("faces") or ():
        if f.get("polygon"):
            out.append({"face_id": f.get("face_id"), "polygon": f["polygon"], "hole_polygons": f.get("hole_polygons") or ()})
    return out


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("drawing")
    ap.add_argument("out")
    ap.add_argument("--facts")
    a = ap.parse_args(argv)
    facts = json.loads(Path(a.facts).read_text()) if a.facts else None
    rep = run(a.drawing, facts)
    Path(a.out).write_text(json.dumps(rep, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    for reg in rep:
        for r in reg["records"]:
            print(reg["region"], r["text_id"], r["code"], r["status"], r["reason"], r.get("layer"), r["membrane_m2"],
                  r["upturn_lm"], r.get("held_part_m2"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
