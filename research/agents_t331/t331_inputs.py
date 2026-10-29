"""T-331: the URBAN_V3022_INPUTS_V1 of the development villa, from the checker-merged wet-room backing ledger only:

  T-329 MERGED 1c82807b (Verifier 2026-10-29 07:50 UTC, Gate A PASS): BACKING_FACE_LEDGER_T329.csv (115 backing faces
      + 2 open sides, each once), ROOM_BACKING_T329.csv (18 rooms: 12 determinate, 6 HELD), PLASTER_LINE_MAP_T329.csv
      (19 rows: 11 wet-room FILL + the pantry FILL, 6 HELD by name, the superseded pantry room record NOT_APPLICABLE).
      The Checker re-measured GF-12 (7.4140 m x 3.65 - 0.80 x 2.20 = 25.3011 m2 = ledger, 0.0000) and checked the
      evidence chain (UP-FIN-PAINT-001 'substrate', Q-45 B, Q-43).
  T-312 MERGED 8943b5ed: OPENINGS_T312.csv: the m2 of each opening by its part inside the band (the backing ledger
      names the same opening ids on the same faces; R-T329-3).

Every value below is re-read from the merged files and asserted against the pins (an edited or stale ledger stops the
build): 12 FILL lines 340.3038 m2 (307.9616 in the 11 wet-room lines + 32.3422 pantry), 6 HELD lines (blank), band
above the tile owner 0.0000 m2, drawing-derived 0 .. 23.0970 m2 over the 18 rooms (0 .. 16.2125 on the 12). The module
binds each FILL record to its room's own FIN.WALL.TILE line in the run (faces equal, face by face), so a different
candidate refuses the build. No coordinate, no client text here.

    python3 -I research/agents_t331/t331_inputs.py > <scratch>/v3022_inputs.json
"""

from __future__ import annotations

import csv
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
T329 = ROOT / "research/agents_t329"
FACES = T329 / "BACKING_FACE_LEDGER_T329.csv"
ROOMS = T329 / "ROOM_BACKING_T329.csv"
LMAP = T329 / "PLASTER_LINE_MAP_T329.csv"
OPEN = ROOT / "research/agents_t312/OPENINGS_T312.csv"
OA = "ASSUMED - OWNER-APPROVED"
OA_LEDGER = "ASSUMED — OWNER-APPROVED"          # the ledger writes the em dash form
MERGE = "1c82807b24c5392c11501b8bfbc9fb0028830f59"
T312_MERGE = "8943b5ed31dccdacf2838046801d42f1e8573370"
CHECKER = ("Verifier 2026-10-29 07:50 UTC (T-329 Gate A PASS; own GF-12 7.4140 m x 3.65 - 0.80 x 2.20 = 25.3011 m2 = "
           "ledger 0.0000; evidence chain UP-FIN-PAINT-001 substrate / Q-45 B / Q-43 checked; heights stay OA)")
ASSUMPTION = ("backing coat behind the wall tile its own line (UP-FIN-PAINT-001 logic 'substrate', knowledge 1.8.0); "
              "coat 20 mm 1:4 cement-sand (Q-45 B, PROVISIONAL practice value); plaster top = tile top: owner height "
              "Q-43 (GF 3.65, 1F / 2F 3.35) = Q-48 A (tile to the underside of the 0.15 decor ceiling); door head "
              "2.20 where none is printed (Q-55 C): ASSUMED - OWNER-APPROVED (OWNER_QUESTIONS_ANSWERED.md Q-43, Q-45, "
              "Q-48, Q-55; OWNER_RECONCILIATION_2026-10-20 G1)")
BAND_OWNER = "Q-43 plaster top = Q-48 A tile top: no band above the tile"
BAND_OWNER_HELD = ("Q-43 plaster top = Q-48 A tile top: no band above the tile (both tops HELD with the room "
                   "height)")
BAND_REASON = ("Q-52 C MODIFIED: plaster may run above the false ceiling depending on the specification; no "
               "specification or section prints it; the drawing method takes plaster to the slab soffit, the tile to "
               "the underside of the 0.15 decor ceiling, so the band is the decor zone x face length; the beam faces "
               "on the wall line in that band are not split")
PANTRY_TILE_LINE = "L-f5c5a1a9c9ee2b644cb5"   # the V3.0.21 ADD line of GF-07 (T-315 report s.4, MERGED b0041dd2)
PINS = {"FILL": (12, 340.3038), "HELD": 6, "WET_FILL": (11, 307.9616), "PANTRY": 32.3422,
        "BAND_HIGH_ALL": 23.0970, "BAND_HIGH_FILL": 16.2125, "FACES": 115}
KEEP = ("L-6470c6f20f86e542a5ce",)
NOTE_FIXES = ("L-af6fb2d3474c5fbdb80a", "L-71e2e002a3af624097f0")   # Checker cosmetic note 2026-10-29 07:50
DOWNSTREAM = ["coat mortar (m2 x 0.02 m, 1:4) = procurement of the SAME layer (FINISH_MATERIALS_TABLE_V1 WET_WALL), "
              "never a second quantity",
              "tile adhesive: its own line (Q-45 B 20 kg / 5 m2), not in this line",
              "spatter-dash coat on wet walls: a separate item (URBAN-FINISH-EXTRAS-SEPARATE-ITEMS@v1), carrier not "
              "settled",
              "paint on these faces: 0 by rule (UP-FIN-PAINT-001), the room's paint lines carry no figure (asserted)",
              "opening reveals: the reveal ledgers (T-313 / T-326)"]


def _sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _rows(p):
    with p.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def _range(txt):
    """'0 .. 1.3500 (HELD)' -> (0.0, 1.35); a named correction piece '-0.0786 (named correction ..., HELD)' -> (0.0,
    -0.0786): its band part is the decor zone x its negative length (the room's high includes it)"""
    if ".." not in txt:
        return 0.0, float(txt.split()[0])
    a, b = txt.replace("(HELD)", "").split("..")
    return float(a), float(b)


def _source():
    return {"file": str(FACES.relative_to(ROOT)), "sha256": _sha(FACES), "task": "T-329", "merge_commit": MERGE,
            "checker_run": CHECKER,
            "also": {str(p.relative_to(ROOT)): _sha(p) for p in (ROOMS, LMAP, OPEN)},
            "openings_from": f"T-312 OPENINGS_T312.csv (MERGED {T312_MERGE[:8]})"}


def _openings():
    out = {}
    for o in _rows(OPEN):
        if o["state"] != "DETERMINATE":
            continue
        out[(o["face_id"], o["opening_id"])] = float(o["band_m2"])
    return out


def _faces(room, ops):
    fs = []
    for f in _rows(FACES):
        if f["room"] != room or f["tile_scope"] != "TILED":
            continue
        if not f["backing"].startswith("YES"):
            raise SystemExit(f"face {f['face_id']}: a tiled face without backing")
        ids = f["openings"].split()
        opened = [{"id": i, "m2": ops[(f["face_id"], i)]} for i in ids]
        length = float(f["length_m"])
        corr = f["piece"] != "WALL FACE" and length < 0
        rec = {"face_id": f["face_id"], "wall_id": f["face_id"].split("|", 1)[1], "length_m": length,
               "height_m": float(f["tile_top_m"]),
               "height_source": "backing top = tile top (R-T329-2): Q-43 / Q-48 A owner height (G1)",
               "openings": opened, "net_m2": float(f["backing_owner_m2"]), "tile_net_m2": float(f["tile_owner_m2"]),
               "band_owner_m2": float(f["band_owner_m2"]), "band_dwg": list(_range(f["dwg_band_m2"])),
               "plaster_line": f["plaster_line_id"]}
        if abs(float(f["owner_plaster_top_m"]) - float(f["tile_top_m"])) > 1e-9 or abs(float(f["closure_m2"])) > 0:
            raise SystemExit(f"face {f['face_id']}: owner plaster top != tile top or closure != 0")
        if corr:
            rec.update(correction=True, basis=f"{f['piece']} (T-312 named walk correction, T-128 r3 verified outline)")
        fs.append(rec)
    return fs


def build(project_id=None):
    lmap = {r["line_id"]: r for r in _rows(LMAP)}
    rooms = {r["room"]: r for r in _rows(ROOMS)}
    tile_of = {}
    for f in _rows(FACES):
        if f["tile_scope"] == "TILED":
            tile_of.setdefault(f["room"], set()).add(f["tile_line_id"])
    ops = _openings()
    recs = []
    for lid, m in lmap.items():
        if lid in KEEP:
            if not m["proposal"].startswith("NOT_APPLICABLE_WITH_EVIDENCE"):
                raise SystemExit(f"{lid}: the merged map no longer keeps it NOT_APPLICABLE")
            continue
        room = rooms[m["room"]]
        tl = tile_of[m["room"]]
        if len(tl) != 1:
            raise SystemExit(f"{m['room']}: faces on {len(tl)} tile lines")
        tl = tl.pop()
        tl = PANTRY_TILE_LINE if tl == "NO_LINE" else tl
        lo, hi = _range(room["dwg_band_m2"])
        band = {"owner_m2": 0.0, "owner_basis": BAND_OWNER if m["proposal"] == "FILL" else BAND_OWNER_HELD,
                "drawing_low": lo, "drawing_high": hi,
                "status": "HELD", "reason": BAND_REASON}
        base = {"line_id": lid, "tile_line_id": tl, "room": m["room"], "engine_room": m["engine_room"],
                "floor": m["floor"], "task": "T-329", "band": band, "downstream": DOWNSTREAM,
                "drawing_derived_method": {"backing": "HELD (= the tile faces: roof datum DCR-6, sunken panels, "
                                                      "build-up b; T-312 drawing columns)",
                                           "band_above_tile_m2": {"low": lo, "high": hi, "status": "HELD"},
                                           "basis": BAND_REASON}}
        if m["proposal"] == "FILL":
            faces = _faces(m["room"], ops)
            if {f.pop("plaster_line") for f in faces} != {lid}:
                raise SystemExit(f"{lid}: faces bound to another plaster line")
            val = float(m["proposed_m2"])
            if abs(val - float(room["backing_owner_m2"])) > 1e-9 or room["status"] != OA_LEDGER:
                raise SystemExit(f"{lid}: map {val} != room {room['backing_owner_m2']} / {room['status']}")
            recs.append(dict(base, kind="FILL", value=val, evidence_status=OA, assumption=ASSUMPTION, faces=faces,
                             info=f"{len(faces)} faces, closure to tile 0.0000 m2 (T-329)"))
        elif m["proposal"].startswith("HELD"):
            if room["status"] != "HELD" or room["backing_owner_m2"]:
                raise SystemExit(f"{lid}: the room is not HELD in the merged ledger")
            recs.append(dict(base, kind="HELD", evidence_status="HELD", reasons=[room["held_item"]],
                             info=m["basis"]))
        else:
            raise SystemExit(f"{lid}: proposal {m['proposal']!r}")
    fills = [r for r in recs if r["kind"] == "FILL"]
    m2 = round(sum(r["value"] for r in fills), 4)
    wet = [r for r in fills if r["tile_line_id"] != PANTRY_TILE_LINE]
    nfaces = sum(len(r["faces"]) for r in fills) + sum(int(rooms[r["room"]]["backing_faces"])
                                                        for r in recs if r["kind"] == "HELD")
    pins = {"FILL": (len(fills), m2), "HELD": len(recs) - len(fills),
            "WET_FILL": (len(wet), round(sum(r["value"] for r in wet), 4)),
            "PANTRY": round(m2 - sum(r["value"] for r in wet), 4),
            "BAND_HIGH_ALL": round(sum(r["band"]["drawing_high"] for r in recs), 4),
            "BAND_HIGH_FILL": round(sum(r["band"]["drawing_high"] for r in fills), 4), "FACES": nfaces}
    if pins != PINS:
        raise SystemExit(f"the merged ledger is not the pinned one: {pins} != {PINS}")
    sys.path.insert(0, str(ROOT / "research/agents_t193"))
    import t193_inputs as L7   # noqa: E402  (the V3.0.7 guard inputs, unchanged, as V3.0.8 .. V3.0.21)
    g = dict(L7.inputs(project_id)["guard"], new_records=[])
    return {"schema": "URBAN_V3022_INPUTS_V1", "project": project_id, "sources": [_source()], "records": recs,
            "guard": g,
            "keep": [{"line_id": k, "task": "T-329", "why": lmap[k]["basis"]} for k in KEEP],
            "note_fixes": [{"line_id": k, "task": "T-331", "field": "base_ownership_v3021"} for k in NOTE_FIXES],
            "declared": {"FILL": {"lines": len(fills), "m2": m2}, "HELD": {"lines": len(recs) - len(fills)}}}


if __name__ == "__main__":
    json.dump(build(sys.argv[1] if len(sys.argv) > 1 else None), sys.stdout, ensure_ascii=False, indent=1)
