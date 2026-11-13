"""T-314 r3 (lane I, owner gap #1 of 2026-11-13: exterior render / paint): the inputs of ARCH_TAKEOFF_V3.0.79
(URBAN_V3079_INPUTS_V1), built ONLY from the Checker-merged T-756 face ledger (MERGED e121e0b4, Verifier 2026-11-13T10:00Z,
GATE A PASS), sha256-pinned below, and checked against the candidate of record's line index V3.0.78 (T-738 r2, Gate B
READY on 49d21678; the T-756 mapped ids re-checked on that index: `t756_alsenan.py --recheck` exit 0, none changed).
Nothing here opens a drawing or forms a quantity: every face figure is the merged ledger's; the line figure is the sum of
its faces (asserted equal to the wire table, R-T314-3 (b)).

  RENDER  T756_FACE_PAINT.csv: 126 face rows on 18 FIN.EXT.FINISH lines (3 CHANGE storey lines, 15 ADD; the 1F slab-edge
          line blank: 6 blank faces, valued part beside); T756_WIRE_TABLE.csv: line action, after figure, status.
  PAINT   formed by the method (UP-FIN-PAINT-002: paint = render face by face): one FIN.EXT.PAINT line per render line.
  EDGE    T756_EDGE_DELTAS.csv / WIRE_TABLE: the one CHANGE row (L-d8a40db5, T-754 F-T754-1 -2.60 lm); the 37 KEEP rows
          move nothing (statements).

    python3 -I research/agents_t314/t314_inputs.py [--check]
"""
from __future__ import annotations

import csv
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCHEMA = "URBAN_V3079_INPUTS_V1"
PID = "development-villa-t131"
INDEX = "research/agents_t738/out/LINE_INDEX_V3_0_78.json"
FACES = "research/agents_t756/out/T756_FACE_PAINT.csv"
WIRE = "research/agents_t756/out/T756_WIRE_TABLE.csv"
EDGES = "research/agents_t756/out/T756_EDGE_DELTAS.csv"
COMP = "research/agents_t756/out/T756_COMPONENT_MAP.csv"
PINS = {INDEX: "16b0feeaed5ffb3f", FACES: "0887ecb614083bfa", WIRE: "2754be1d54ad970c", EDGES: "20f384d383650253",
        COMP: "6ca69b29f6807756"}
T756_RUN = "Verifier 2026-11-13T10:00Z GATE A PASS (session_01E6cPnempse2wFh8LTJGZA9; PARTIALLY VERIFIED 2/126 faces)"
SOURCES = [{"task": "T-756", "file": FACES, "merge_commit": "e121e0b4", "checker_run": T756_RUN},
           {"task": "T-756-WIRE", "file": WIRE, "merge_commit": "e121e0b4", "checker_run": T756_RUN},
           {"task": "T-756-EDGE", "file": EDGES, "merge_commit": "e121e0b4", "checker_run": T756_RUN}]
STATUS = {"HELD": "HELD", "DRAWING-CONFIRMED": "DRAWING-CONFIRMED"}
HOST = {"GF": "L-b05f70c92405dbcfbe62", "1F": "L-8bb83e16cc7b104ab88b", "2F": "L-d52c4f763b19aedf8b8b"}
N_FACES, N_RENDER, N_EDGE_CHANGE = 126, 18, 1
# T-756 left the parapet inner / top item code to the Lead at r3 ("stage key"); its reserved line ids are FIN.EXT.FINISH
# ids (re-derived by the method under R-T314-1 1.0.0): they are wired as FIN.EXT.FINISH lines whose element id names the
# part (PARAPET_INNER / PARAPET_TOP); the stage key is kept on the line record. A new item code would need new ids.
STAGE_KEYS = ("FIN.EXT.PARAPET-INNER", "FIN.EXT.PARAPET-TOP")


class InputsError(ValueError):
    pass


def sha(p):
    return hashlib.sha256((ROOT / p).read_bytes()).hexdigest()


def load(p):
    got = sha(p)
    if not got.startswith(PINS[p]):
        raise InputsError(f"{p}: sha256 {got[:16]} is not the pinned {PINS[p]} (stale input)")
    t = (ROOT / p).read_text(encoding="utf-8")
    return json.loads(t) if p.endswith(".json") else list(csv.DictReader(t.splitlines()))


def pair(s):
    s = (s or "").strip()
    if not s:
        return None
    lo, hi = (float(x) for x in s.split(" .. "))
    return [lo, hi]


def status_of(ev):
    if ev.startswith("ASSUMED — OWNER-APPROVED"):
        return "ASSUMED — OWNER-APPROVED", ev
    if ev not in STATUS:
        raise InputsError(f"evidence {ev!r} is not a WORKFLOW_CONTROLS s.5 status")
    return STATUS[ev], None


def inputs():
    idx = {x["line_id"]: x for x in load(INDEX)["lines"]}
    faces, wire, edges = load(FACES), load(WIRE), load(EDGES)
    load(COMP)                                             # pinned: the MISSING / OTHER_TRADE items (statements)
    if len(faces) != N_FACES:
        raise InputsError(f"{len(faces)} face rows, the ledger has {N_FACES}")
    by_line = {}
    for f in faces:
        if f["render"] != f["paint"]:
            raise InputsError(f"{f['face_id']}: paint {f['paint']} is not render {f['render']} (UP-FIN-PAINT-002)")
        by_line.setdefault(f["line_id"], []).append(f)
    render, edge_rows, statements = [], [], []
    for w in wire:
        lid, act = w["line_id"], w["action"]
        if w["item_code"] == "FIN.EXT.FINISH" or w["item_code"].startswith(STAGE_KEYS):
            st, st_text = status_of(w["evidence"])
            fr = by_line.pop(lid, None)
            if not fr:
                raise InputsError(f"{lid}: no face row")
            blank = [f for f in fr if f["state"] == "BLANK"]
            causes = sorted({f["cause"][:160] for f in fr if f["state"] in ("BOUNDED", "BLANK") and f["cause"]})
            held = [f["face_id"] for f in fr if f["state"] in ("BOUNDED", "BLANK")]
            why = (f"T-756 face ledger (re-based by id onto V3.0.77, re-checked on V3.0.78): {len(fr)} face rows of "
                   f"{w['element_id']}, holes once by face (Q-73 A); sources {w['sources']}")
            e = {"line_id": lid, "action": act, "element_id": w["element_id"], "source_tasks": ["T-756", "T-756-WIRE"],
                 "rule": "R-T756-2 / R-T314-1 (face rows; UP-FIN-PAINT-002 paint = render)", "status": st,
                 "status_text": st_text, "why": why,
                 "open": ("held faces " + ", ".join(held[:8]) + ("" if len(held) <= 8 else f" +{len(held) - 8}") +
                          ": " + "; ".join(causes))[:400] if held else
                         f"held until a Checker record releases it ({w['evidence']})",
                 "faces": [{"face_id": f["face_id"], "element": f["element"], "render": pair(f["render"]),
                            "holes": f["holes"], "state": f["state"], "cause": f["cause"][:300]} for f in fr],
                 "expect_after": pair(w["after"]),
                 "stage_key": w["item_code"].split(" ")[0] if w["item_code"] != "FIN.EXT.FINISH" else None}
            if blank:
                vp = pair(w["valued_part"])
                if vp is None:
                    raise InputsError(f"{lid}: blank line without its valued part")
                e["valued_part"] = vp
            if act == "CHANGE":
                x = idx.get(lid)
                if x is None or x["item_code"] != "FIN.EXT.FINISH" or x["class"] != "HELD" or x["held_low"] is not None:
                    raise InputsError(f"{lid}: not a HELD blank FIN.EXT.FINISH line in V3.0.78 (stale)")
                e["expect"] = {"item_code": "FIN.EXT.FINISH", "element_id": x["element_id"], "unit": "m2",
                               "class": "HELD"}
                if x["element_id"] != w["element_id"]:
                    raise InputsError(f"{lid}: element {x['element_id']} is not the ledger's {w['element_id']}")
            elif act == "ADD":
                if lid in idx:
                    raise InputsError(f"{lid}: an ADD id is already a V3.0.78 line")
                e["host_line_id"] = HOST[w["element_id"].split("-")[0]]
            else:
                raise InputsError(f"{lid}: render action {act}")
            render.append(e)
        elif w["item_code"] == "FIN.EXT.PAINT.EDGE":
            x = idx.get(lid)
            if x is None or x["item_code"] != "FIN.EXT.PAINT.EDGE":
                raise InputsError(f"{lid}: not a V3.0.78 edge line (stale)")
            b, a = pair(w["before"]), pair(w["after"])
            got = None if x["held_low"] is None else [x["held_low"], x["held_high"]]
            if got != b:
                raise InputsError(f"{lid}: V3.0.78 {got} is not the ledger's before {b} (stale)")
            if act == "KEEP":
                if a != b:
                    raise InputsError(f"{lid}: a KEEP row moves")
                statements.append({"line_id": lid, "action": "KEEP", "why": "T-756 R-T756-3: no delta"})
                continue
            if act != "CHANGE":
                raise InputsError(f"{lid}: edge action {act}")
            d = next(r for r in edges if r["line_id"] == lid)
            if pair(d["after"]) != a or pair(d["before"]) != b:
                raise InputsError(f"{lid}: edge delta row disagrees with the wire table")
            edge_rows.append({"line_id": lid, "source_tasks": ["T-756-EDGE"],
                              "expect": {"item_code": "FIN.EXT.PAINT.EDGE", "element_id": x["element_id"], "unit": "lm",
                                         "class": "HELD", "low": b[0], "high": b[1]},
                              "low": a[0], "high": a[1], "status": "HELD", "rule": "R-T756-3 / F-T754-1",
                              "why": d["note"][:400]})
        else:
            raise InputsError(f"{lid}: item code {w['item_code']} is not wired by this package")
    if by_line:
        raise InputsError(f"face rows on lines the wire table does not name: {sorted(by_line)}")
    if len(render) != N_RENDER or len(edge_rows) != N_EDGE_CHANGE:
        raise InputsError(f"{len(render)} render / {len(edge_rows)} edge rows (want {N_RENDER} / {N_EDGE_CHANGE})")
    statements += [{"item": r["component"], "state": r["v3077_state"], "why": r["why"][:300]}
                   for r in load(COMP) if r["v3077_state"] in ("MISSING", "PARKED", "OTHER_TRADE")]
    srcs = [dict(s, sha256=sha(s["file"])) for s in SOURCES]
    return {"schema": SCHEMA, "project_id": PID, "sources": srcs, "render": render, "edges": edge_rows,
            "statements": statements}


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    doc = inputs()
    from engine.source import arch_v3079 as A
    d = A.load_inputs(doc, PID)
    lo = sum(e["_sum"][0] for e in d["_render"] if not e["_blank_faces"])
    hi = sum(e["_sum"][1] for e in d["_render"] if not e["_blank_faces"])
    print(json.dumps({"render_lines": len(d["_render"]), "edge_changes": len(d["_edges"]),
                      "statements": len(doc["statements"]), "valued_render_m2": [round(float(lo), 6),
                                                                                 round(float(hi), 6)]}))
    return 0


if __name__ == "__main__":
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    sys.exit(main())
