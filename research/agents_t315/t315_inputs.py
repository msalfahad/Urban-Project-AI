"""T-315: the URBAN_V3021_INPUTS_V1 of the development villa, from the checker-merged wall-tile face ledger only:

  T-312 MERGED 8943b5ed (Verifier 2026-10-28 21:20 UTC, Gate A PASS): FACE_LEDGER_T312.csv (115 wet-room face pieces +
      2 open edges, each once; 18 rooms close 0.0000 m), OPENINGS_T312.csv (35 openings once per room side, each by its
      part inside the tile band), LINE_SUMMARY_T312.csv (each of the 17 candidate FIN.WALL.TILE lines once + the
      pantry NO_LINE row). The Checker re-measured 1F-12 (26.305 m2, = ledger 26.3051) and the pantry (own 32.375 vs
      32.3422, +0.10 %, scope by host walls agrees) on length / openings; the heights stay ASSUMED - OWNER-APPROVED.

Every value below is re-read from the merged files and asserted against the pins (an edited or stale ledger stops
the build): 11 FILL lines 307.9616 m2, 6 HELD lines (blank), 1 ADD line (pantry) 32.3422 m2. The module asserts each
FILL / HELD line against the candidate line (a blank FIN.WALL.TILE line of its engine room), so a different candidate
refuses the build. No coordinate, no client text here.

    python3 -I research/agents_t315/t315_inputs.py > <scratch>/v3021_inputs.json
"""

from __future__ import annotations

import csv
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
T312 = ROOT / "research/agents_t312"
FACES = T312 / "FACE_LEDGER_T312.csv"
OPEN = T312 / "OPENINGS_T312.csv"
LINES = T312 / "LINE_SUMMARY_T312.csv"
CLOSE = T312 / "ROOM_CLOSURE_T312.csv"
OA = "ASSUMED - OWNER-APPROVED"
OA_LEDGER = "ASSUMED — OWNER-APPROVED"          # the ledger writes the em dash form
MERGE = "8943b5ed31dccdacf2838046801d42f1e8573370"
CHECKER = ("Verifier 2026-10-28 21:20 UTC (Gate A PASS; own 1F-12 26.305 m2 = ledger 26.3051; own pantry 32.375 vs "
           "32.3422, +0.10 %, host-wall scope agrees; heights stay OA)")
ASSUMPTION = ("owner wall height G1 (Q-43 / Q-48 A: tile top = underside of the 0.15 decor ceiling, GF 3.65, 1F / 2F "
              "3.35) and door head 2.20 where none is printed (Q-55 C): ASSUMED - OWNER-APPROVED "
              "(OWNER_QUESTIONS_ANSWERED.md Q-48, Q-55; OWNER_RECONCILIATION_2026-10-20 G1)")
PANTRY_SCOPE = ("UP-PANTRY-001 .. 004: open pantry, every drawn wall hosts a counter run (west 3.066, south 1.400, north "
                "0.500 + column 0.900 m; T-312 / Checker 21:20), each tiled as a whole wall; the open edge 4.49 m tiles "
                "nothing")
PINS = {"FILL": (11, 307.9616), "HELD": (6, None), "ADD": (1, 32.3422)}
DOWNSTREAM = ["wall-tile backing plaster / render behind the tile: its own line (UP-FIN-PAINT-001 substrate), not "
              "carried by a merged ledger: HELD by name",
              "tile adhesive / grout and procurement (cartons, waste): HELD, no product / waste rule applied here",
              "no skirting on a full-height tiled wet face (URBAN-NO-SKIRTING-FULL-TILE-WET@v1)",
              "no paint on these faces (UP-FIN-PAINT-001): the room's paint lines carry no figure (asserted)"]


def _sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _f(x):
    try:
        return float(x)
    except ValueError:            # 'HELD' / blank: no figure
        return None


def _rows(p):
    with p.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def _source():
    return {"file": str(FACES.relative_to(ROOT)), "sha256": _sha(FACES), "task": "T-312", "merge_commit": MERGE,
            "checker_run": CHECKER,
            "also": {str(p.relative_to(ROOT)): _sha(p) for p in (OPEN, LINES, CLOSE)}}


def _openings():
    out = {}
    for o in _rows(OPEN):
        if o["state"] != "DETERMINATE":     # an opening of a HELD room: its band part waits with the room height
            out.setdefault(o["face_id"], []).append({"id": o["opening_id"], "m2": None, "state": o["state"]})
            continue
        if abs(float(o["band_m2"]) - float(o["t292_owner_ded_m2"])) > 1e-6:
            raise SystemExit(f"opening {o['opening_id']}: band {o['band_m2']} != T-292 {o['t292_owner_ded_m2']}")
        out.setdefault(o["face_id"], []).append({"id": o["opening_id"], "m2": float(o["band_m2"]),
                                                 "basis": f"{o['kind']} {o['merged_size']} ({o['merged_source']})"})
    return out


def _faces(room, ops, used):
    fs = []
    dwg = {}
    for f in _rows(FACES):
        if f["room"] != room or f["scope"] != "TILED":
            continue
        got = ops.get(f["face_id"], [])
        rest = f["openings"]
        for o in got:              # every ledger opening of the face named on the face row, nothing else
            if o["id"] not in rest:
                raise SystemExit(f"face {f['face_id']}: opening {o['id']} not on the face row {f['openings']!r}")
            rest = rest.replace(o["id"], "", 1)
        if rest.strip():
            raise SystemExit(f"face {f['face_id']}: {rest.strip()!r} on the face row is not in the opening ledger")
        used.update((f["face_id"], o["id"]) for o in got)
        fs.append({"face_id": f["face_id"], "wall_id": f["wall_id"], "length_m": float(f["length_m"]),
                   "height_m": _f(f["owner_h_m"]),
                   "height_source": f["owner_h_source"], "openings": got,
                   "net_m2": _f(f["owner_net_m2"]),
                   "owner_status": f["owner_status"]})
        if fs[-1]["length_m"] is not None and fs[-1]["length_m"] < 0:
            fs[-1].update(correction=True, basis=f["length_source"][:300])
        dwg.setdefault((f["dwg_status"], f["dwg_held_item"][:200]), 0)
        dwg[(f["dwg_status"], f["dwg_held_item"][:200])] += 1
    ddm = [{"status": k[0], "held_item": k[1], "faces": n} for k, n in sorted(dwg.items())]
    return fs, ddm


def build(project_id=None):
    if project_id is None:
        sys.path.insert(0, str(ROOT / "research/agents_t131"))
        import alsenan_v30_run as T131  # noqa: E402
        project_id = T131.PID
    ops = _openings()
    closure = {c["room"]: c for c in _rows(CLOSE)}
    used = set()
    recs = []
    for s in _rows(LINES):
        room = s["rooms"]
        fs, ddm = _faces(room, ops, used)
        if len(fs) != int(s["faces"]):
            raise SystemExit(f"{room}: {len(fs)} tiled faces != the line summary's {s['faces']}")
        cl = closure.get(room)
        if cl is None or cl["line_id"] != s["line_id"]:
            raise SystemExit(f"{room}: no room closure row for line {s['line_id']}")
        if abs(float(cl["residual_m"])) > 1e-9:
            raise SystemExit(f"{room}: closure residual {cl['residual_m']} m")
        base = {"room": room, "engine_room": s["engine_room"].split(" ")[0], "floor": s["floor"], "task": "T-312",
                "drawing_derived_method": ddm, "downstream": DOWNSTREAM}
        if s["ledger_status"] == "HELD":
            if any(f["net_m2"] is not None and f["owner_status"] == OA_LEDGER for f in fs):
                raise SystemExit(f"{room}: a HELD line with an owner-approved face figure")
            info = None
            vals = [f for f in fs if f["owner_status"] != OA_LEDGER]
            recs.append(dict(base, kind="HELD", line_id=s["line_id"], evidence_status="HELD",
                             reasons=[s["held_item"]], info=info,
                             faces_held=len(vals)))
            continue
        if s["ledger_status"] != OA_LEDGER:
            raise SystemExit(f"{room}: ledger status {s['ledger_status']!r}")
        for f in fs:
            if any(o.get("state") for o in f["openings"]):
                raise SystemExit(f"face {f['face_id']}: an opening that is not DETERMINATE in a valued line")
            if f["owner_status"] != OA_LEDGER or f["net_m2"] is None or f["height_m"] is None:
                raise SystemExit(f"face {f['face_id']}: not an owner-approved figure")
            f.pop("owner_status")
        val = round(sum(f["net_m2"] for f in fs), 4)
        if abs(val - float(s["ledger_owner_m2"])) > 1e-4:
            raise SystemExit(f"{room}: faces {val} != the line summary {s['ledger_owner_m2']}")
        rec = dict(base, value=float(s["ledger_owner_m2"]), evidence_status=OA, assumption=ASSUMPTION, faces=fs,
                   contour={"contour_m": float(cl["contour_m"]), "open_m": float(cl["open_m"]),
                            "not_tiled_m": float(cl["not_tiled_m"]),
                            "source": "T-312 ROOM_CLOSURE_T312.csv (T-074 / T-128 r3 walked contour)"})
        if s["line_id"] == "NO_LINE":
            rec.update(kind="ADD", scope=PANTRY_SCOPE)
            rec["assumption"] = ASSUMPTION + "; scope " + PANTRY_SCOPE
        else:
            rec.update(kind="FILL", line_id=s["line_id"])
        if room == "1F-12":
            rec["note"] = ("per-face split 2.125 / 2.250 / 2.145 / 2.100 / 0.080 (T-250 walk) vs the Checker's "
                           "rectangle 2.100 / 2.250: the room total 8.700 m agrees 0.000, and one height carries "
                           "every face, so the line figure does not depend on the split")
        recs.append(rec)
    for r in recs:
        r.pop("faces_held", None)
    allops = {(fid, o["id"]) for fid, lst in ops.items() for o in lst}
    if allops - used:
        raise SystemExit(f"openings on no tiled face: {sorted(allops - used)}")
    dec = {}
    for k, (n, m2) in PINS.items():
        got = [r for r in recs if r["kind"] == k]
        tot = round(sum(r.get("value") or 0 for r in got), 4)
        if len(got) != n or (m2 is not None and abs(tot - m2) > 1e-4):
            raise SystemExit(f"{k}: {len(got)} lines {tot} m2 != the pins {n} / {m2}")
        dec[k] = {"lines": n, "m2": m2 if m2 is not None else 0.0}
    sys.path.insert(0, str(ROOT / "research/agents_t193"))
    import t193_inputs as L7   # noqa: E402  (the V3.0.7 guard inputs, unchanged, as V3.0.8 .. V3.0.15)
    g = dict(L7.inputs(project_id)["guard"], new_records=[])
    return {"schema": "URBAN_V3021_INPUTS_V1", "project": project_id, "sources": [_source()], "records": recs,
            "declared": dec, "guard": g}


if __name__ == "__main__":
    print(json.dumps(build(), ensure_ascii=False, indent=1))
