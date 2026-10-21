"""ALSENAN CONTROL-PLANE AUDIT R1 - live evidence extractor (diagnosis only; changes nothing).

Rebuilds (or loads) the frozen Alsenan V3b context and writes the facts the frozen registers do not carry:

    semantic      TS01 (room_topology_v3) semantic-zone state of every V3 room site
    wet_labels    every wet / service room text on the plans and the physical site it falls in (or NO_SITE)
    wall_ledger   wall-band centreline per floor (ESTABLISHED / AMBIGUOUS by width) + admitted boundary length not in
                  any band, by geometry role
    columns       column occurrence state (concrete) beside the bar sets V3 emits for it (rebar)
    ground        ground-slab zones as bound by V3 / V3b
    openings      V3 opening rows (width / height state / status)

    python3 research/alsenan_control_plane_01/extract_live.py <ctx.pkl | work_dir> [out.json]

A ctx.pkl is the pickled return value of alsenan_v3b.build(work_dir); with a directory the build is run here.
"""

from __future__ import annotations

import json
import math
import pickle
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "external_engine_lab"))
sys.path.insert(0, str(ROOT))

WET_RE = re.compile(r"BATH|W\.?C\b|WASH|TOILET|SHOWER|LAUNDRY|KITCHEN|PANTRY|حمام|مرحاض|مغسل|غسيل|مطبخ|تحضير", re.I)


def _r(v, n=3):
    return None if v is None else round(v, n)


def _seglen(it):
    g = it.geometry
    if it.kind == "SEGMENT":
        return math.hypot(g[2] - g[0], g[3] - g[1])
    if it.kind == "ARC":
        return g[2] * ((g[4] - g[3]) % (2 * math.pi))
    return 0.0


def load(src):
    p = Path(src)
    if p.is_file():
        return pickle.load(open(p, "rb"))
    import alsenan_v3b as V3B
    return V3B.build(p, "control-plane-diagnosis")


def extract(ctx) -> dict:
    from engine.source import legacy_text as LT
    from engine.source import topology as T
    fonts = ctx["v3_topology"]["fonts_legacy"]
    rooms = ctx["v3"]["rooms"]["rows"]
    by_site = {r["site"]: r["id"] for r in rooms}
    out = {"SCHEMA": "URBAN_ALSENAN_CONTROL_PLANE_LIVE_EXTRACT_V1", "semantic": [], "wet_labels": [],
           "wall_ledger": {}, "columns": [], "ground": None, "openings": []}

    def decode(t_value, handle):
        fam = LT.font_family(fonts.get(handle, ""))
        return LT.decode(t_value, fam)["text"] if fam else t_value

    for fl in ("GF", "1F", "2F"):
        raw = ctx["a2_raw"][fl]
        res, inp = raw["res"], raw["inp"]
        u = (inp.unit_native_to_mm or 1.0) / 1000.0
        sem = res["semantic"]
        for r in rooms:
            if r["floor"] != fl:
                continue
            st = sem["sites"].get(r["site"], {})
            zs = [z for z in sem["zones"] if z["physical_site_id"] == r["site"]]
            out["semantic"].append({"room": r["id"], "site": r["site"], "ts01_semantic_state": st.get("state"),
                                    "zones": [{"label_values": z["label_values"], "state": z["state"],
                                               "authority": z["authority"]} for z in zs]})
        roles = raw.get("text_roles_v3") or {}
        for t in inp.texts:
            if not t.value or t.x is None:
                continue
            v = decode(t.value, t.identity.source_handle)
            if not WET_RE.search(v):
                continue
            sid, _ = T.locate(res["_arr"], res["sites"], (t.x, t.y), 1.0)
            ro = roles.get(t.identity.key)
            out["wet_labels"].append({"floor": fl, "text": v.strip(), "key": t.identity.key,
                                      "xy": [_r(t.x, 1), _r(t.y, 1)], "site": sid,
                                      "room": by_site.get(sid) if sid else None,
                                      "located": "IN_ROOM_ROW" if sid in by_site else ("IN_NON_ROOM_SITE" if sid
                                                                                      else "NO_SITE"),
                                      "text_role": ro.role if ro else None, "rule": ro.rule_id if ro else None})
        bands = res["wall_bands"]["bands"]
        est, amb, faces = defaultdict(float), defaultdict(float), set()
        for b in bands:
            L = (b["interval"][1] - b["interval"][0]) * u
            w = int(round(b["width"] * (inp.unit_native_to_mm or 1.0) / 10.0) * 10)
            (est if b["state"] == "WALL_BAND_ESTABLISHED" else amb)[w] += L
            faces.update([b["face_a"], b["face_b"]])
        role_len, unpaired = defaultdict(float), defaultdict(float)
        for it in res["_items"]:
            role_len[it.role] += _seglen(it) * u
            if it.source_id not in faces:
                unpaired[it.role] += _seglen(it) * u
        out["wall_ledger"][fl] = {
            "established_centreline_m_by_width_mm": {str(k): _r(v) for k, v in sorted(est.items())},
            "ambiguous_centreline_m_by_width_mm": {str(k): _r(v) for k, v in sorted(amb.items())},
            "band_counts": dict(Counter(b["state"] for b in bands)),
            "admitted_boundary_m_by_role": {k: _r(v) for k, v in sorted(role_len.items())},
            "admitted_not_in_any_band_m_by_role": {k: _r(v) for k, v in sorted(unpaired.items())},
            "unsupported_runs": len(res["wall_bands"]["unsupported_runs"])}
    bw = defaultdict(float)
    for x in ctx["v3"]["blockwork"]["rows"]:
        bw[f"{x['floor']}|{x.get('thickness_mm')}|{x['status']}"] += x.get("length_m") or 0.0
    for fl in out["wall_ledger"]:
        out["wall_ledger"][fl]["blockwork_rows_m"] = {k.split("|", 1)[1]: _r(v) for k, v in sorted(bw.items())
                                                       if k.startswith(fl + "|")}
    states = {(r["floor"], r["tag_key"].split("|")[1]): r for r in ctx["b2a"]["columns"]["rows"]}
    kg = defaultdict(float)
    for b in ctx["v3"]["rebar"]["columns"]:
        fl, _typ, tag = b["ref"].split()[:3]
        kg[(fl, tag)] += b.get("net_design_weight_kg") or b.get("straight_weight_kg") or 0.0
    for key, r in sorted(states.items()):
        out["columns"].append({"floor": key[0], "tag": key[1], "type": r["type"], "state": r["state"],
                               "B_cm": r.get("B_cm"), "concrete_m3": r.get("volume_m3"),
                               "rebar_net_kg": _r(kg.get(key, 0.0))})
    gz = ctx["v3b"]["struct"]["ground_zones"]
    out["ground"] = {"zones": gz["zones"], "footprints": gz["footprints"],
                     "v3a_zones": [{k: v for k, v in z.items() if not k.startswith("_")}
                                   for z in ctx["v3"]["ground"]["zones"]]}
    for o in ctx["v3"]["openings"]["rows"]:
        out["openings"].append({k: o.get(k) for k in ("floor", "id", "kind", "width_m", "wall_t_m", "height_m",
                                                      "height_state", "status", "rule")})
    out["beam_occurrences"] = []
    for fl in ("GF", "1F", "2F"):
        for o in ctx["b2a"]["sheets"][fl]["occurrences"]:
            out["beam_occurrences"].append({
                "floor": fl, "type": o["type"], "tag": o["tags"][0].split("|")[1] if o.get("tags") else None,
                "state": o["state"], "B_cm": o.get("B_cm"), "D_cm": o.get("D_cm"),
                "support_centreline_m": _r((o.get("lengths") or {}).get("SUPPORT_CENTRELINE_LENGTH")),
                "clear_m": _r((o.get("lengths") or {}).get("CLEAR_FACE_TO_FACE_LENGTH"))})
    out["footings"] = [{"type": f["type"], "mark": f["mark_key"].split("|")[1], "status": f.get("status"),
                        "L_m": (f.get("dims") or {}).get("L", {}).get("m"),
                        "W_m": (f.get("dims") or {}).get("W", {}).get("m"),
                        "H_m": (f.get("dims") or {}).get("H", {}).get("m"), "qty_m3": f.get("qty")}
                       for f in ctx["a3"]["footings"]["rows"]]
    out["straps"] = [{"type": s["type"], "mark": s["mark_key"].split("|")[1], "state": s.get("state"),
                      "B_cm": s.get("B_cm"), "D_cm": s.get("D_cm"), "length_m": _r(s.get("length_m")),
                      "status": s.get("status")} for s in ctx["a3"]["straps"]["rows"]]
    return out


def main(src, dest=None):
    ex = extract(load(src))
    dest = Path(dest) if dest else Path(__file__).parent / "evidence" / "LIVE_EXTRACT.json"
    dest.write_text(json.dumps(ex, indent=1, ensure_ascii=False, default=str) + "\n")
    print(dest, {k: (len(v) if isinstance(v, list) else "ok") for k, v in ex.items() if k != "SCHEMA"})


if __name__ == "__main__":
    main(*sys.argv[1:3])
