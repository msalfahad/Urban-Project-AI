"""T-314 inputs: URBAN_V3062_INPUTS_V1 for ARCH_TAKEOFF_V3.0.62 (exterior plaster / Sigma face rows, R-T314-1),
built ONLY from the Checker-merged face ledgers (no drawing read here, no figure typed here):

  T-337 BINDING_T337.csv   every T-305 face band once, bound by element and levels to its owner line (merge ce3aaf8f)
  T-337 OPENINGS_T337.csv  every census opening once, on the face band that holds it
  T-337 ITEMS_T337.csv     parapet inner faces / tops (T-324 components) as their own m2 rows; m.l items named MISSING
  T-337 FILL_T314_T337.csv / FILL_ITEMS_T314_T337.csv: the expected figure of every line (asserted by the engine)
  T-348 r2 FILL_T314_T348.csv + FACES_T348.csv (merge 623885fd): NW-2 parapet re-measured DC, 9 new faces for T-314,
                           NW-1 / NW-3 slab edges removed (no physical face); faces for reveals / soffits stay theirs
  T-567 FACES_T567.csv (merge 8aba0d81, R-T567-6): the SW pier returns in front of 1F NW-5 (storey DC, parapet HELD);
                           the face set of record (120 keys): this file's face rows equal it key by key (asserted)

Level parts: the storey band of each floor is [lowest F.F.L., next F.F.L.] as T-337 s.2 binds it (GF +0.30 .. +5.50,
the two-F.F.L. ground floor is one line; 1F +5.50 .. +9.70; 2F +9.70 .. +13.90); a parapet band [roof, parapet top];
the plinth [ground, lowest house F.F.L. +1.00]. The slab edge prints no depth (Q-68 C): blank, no level.

    python3 -I research/agents_t314/t314_inputs.py --write <file>   (or import build(project_id))
"""
from __future__ import annotations

import csv
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
T337 = ROOT / "research" / "agents_t337"
T348 = ROOT / "research" / "agents_t348"
T567 = ROOT / "research" / "agents_t567" / "out"
SCHEMA = "URBAN_V3062_INPUTS_V1"
KIND = {"storey": "STOREY", "parapet": "PARAPET_OUTER", "plinth": "PLINTH", "slab_edge": "SLAB_EDGE"}
EXISTING = {"L-b05f70c92405dbcfbe62": ("GF", [[0.30, 5.50]]),
            "L-8bb83e16cc7b104ab88b": ("1F", [[5.50, 9.70]]),
            "L-d52c4f763b19aedf8b8b": ("2F", [[9.70, 13.90]])}
NEW = {   # T-337 line name -> (element, floor, element_id, parts, why held)
    "NEW FIN.EXT.FINISH PARAPET-OUTER ANNEX +4.30": ("PARAPET_OUTER", "GF", "GF-FACADE:PARAPET_OUTER:ANNEX_ROOF",
                                                     [[4.30, 4.80]], "annex boundary face on AC7 (T-324 C5, Q-65 C): "
                                                     "house parapet or boundary wall 0 .. 0.600 m2"),
    "NEW FIN.EXT.FINISH PARAPET-OUTER GF +5.50": ("PARAPET_OUTER", "GF", "GF-FACADE:PARAPET_OUTER:GF_ROOF",
                                                  [[5.50, 6.00]], None),
    "NEW FIN.EXT.FINISH PARAPET-OUTER 1F +9.70": ("PARAPET_OUTER", "1F", "1F-FACADE:PARAPET_OUTER:1F_ROOF",
                                                  [[9.70, 11.00]], "parapet heights NE-1 / SW-1 / SW-2 not printed and "
                                                  "the NW-2 frame profile (chord 3.2496 vs arc 3.5283 m, T-324 C3)"),
    "NEW FIN.EXT.FINISH PARAPET-OUTER 2F +13.90": ("PARAPET_OUTER", "2F", "2F-FACADE:PARAPET_OUTER:2F_ROOF",
                                                   [[13.90, 14.40]], None),
    "NEW FIN.EXT.FINISH PLINTH GF": ("PLINTH", "GF", "GF-FACADE:PLINTH", [[0.00, 1.00]],
                                     "pool-court plinth bottom level not printed; plinth finish (plaster / Sigma or "
                                     "cladding) not specified (T-317)"),
    "NEW FIN.EXT.FINISH SLAB-EDGE 1F": ("SLAB_EDGE", "1F", "1F-FACADE:SLAB_EDGE", [],
                                        "1F slab edge over open air: 13.079 m run, depth / finish not printed (Q-68 C)"),
    "NEW FIN.EXT.FINISH SLAB-EDGE GF": ("SLAB_EDGE", "GF", "GF-FACADE:SLAB_EDGE", [],
                                        "void ring inner face depth not printed (T-348 r2); pool-court front edge: "
                                        "owner trade open (court sea wall on the plot line, Q-65 C)"),
}
T348_LINE = {("storey", "1F"): "L-8bb83e16cc7b104ab88b", ("parapet", "1F"): "NEW FIN.EXT.FINISH PARAPET-OUTER 1F +9.70",
             ("slab_edge", "1F"): "NEW FIN.EXT.FINISH SLAB-EDGE 1F", ("slab_edge", "GF"): "NEW FIN.EXT.FINISH SLAB-EDGE GF"}
T567_PIER = [  # R-T567-6 (T-567 s.5): 0.536522 m of returns, storey +5.50 -> +9.70 printed; parapet top not printed
    {"key": "1F/NW-5/SW-PIER-RETURNS/storey", "kind": "storey", "bottom": 5.50, "top": 9.70},
    {"key": "1F/NW-5/SW-PIER-RETURNS/parapet", "kind": "parapet", "bottom": 9.70, "top": None}]
ITEM_LINES = {"PARAPET_INNER": ("parapet inner_face_above_upturn", "PARAPET_INNER",
                                "parapet inner face above the membrane upturn: split height not printed (D-39); the "
                                "upturn zone below it is the waterproofing trade's"),
              "PARAPET_TOP": ("parapet top_surface", "PARAPET_TOP", "parapet top width bands (T-324 D bands)")}
ROOF = {"ANNEX": ("GF", "ANNEX_ROOF"), "GF": ("GF", "GF_ROOF"), "1F": ("1F", "1F_ROOF"), "2F": ("2F", "2F_ROOF")}
SOURCES = [
    {"task": "T-305", "file": "research/agents_t305/FACE_LINE_LEDGER_T305.csv", "merge_commit": "9d71ef09"},
    {"task": "T-311", "file": "research/agents_t311/PARAPET_RUN_LEDGER_T311.csv", "merge_commit": "bd7b8c23"},
    {"task": "T-324", "file": "research/agents_t324/T-324_PARAPET_COMPONENTS.md", "merge_commit": "bc5df868"},
    {"task": "T-337", "file": "research/agents_t337/BINDING_T337.csv", "merge_commit": "ce3aaf8f"},
    {"task": "T-337", "file": "research/agents_t337/OPENINGS_T337.csv", "merge_commit": "ce3aaf8f"},
    {"task": "T-337", "file": "research/agents_t337/ITEMS_T337.csv", "merge_commit": "ce3aaf8f"},
    {"task": "T-349", "file": "research/agents_t349/CLOSURE_T349.csv", "merge_commit": "2d22bce1"},
    {"task": "T-348", "file": "research/agents_t348/FILL_T314_T348.csv", "merge_commit": "623885fd"},
    {"task": "T-348", "file": "research/agents_t348/FACES_T348.csv", "merge_commit": "623885fd"},
    {"task": "T-567", "file": "research/agents_t567/out/FACES_T567.csv", "merge_commit": "8aba0d81"},
]
MISSING = [  # m.l items and unregistered faces: named, never a number in this stage (registry family first)
    ("FIN.EXT.CORNERS (all floors)", "lm", "HELD (bounded)", "external arrises: own m.l line; needs an item code with a "
     "registry family (T-337 FILL_ITEMS 710.171878 .. 821.858800 m.l with blank slab-edge arris)"),
    ("FIN.EXT.COPING", "lm", "UNKNOWN", "none printed"),
    ("FIN.EXT.DRIP", "lm", "UNKNOWN", "nothing drawn; owner not answered"),
    ("FIN.EXT.CORNERS accessory (beads)", "lm", "UNKNOWN", "accessory on the same arrises, never a second edge"),
    ("FIN.EXT.FRAME", "m2", "HELD", "frame / band profile not detailed (designer)"),
    ("FIN.EXT.FINISH DIVIDER", "m2", "UNKNOWN", "no top level printed (T-324)"),
    ("FIN.WP.UPTURN-ZONE-FACE (4 roofs)", "m2", "HELD", "waterproofing trade's face below the parapet inner finish; "
     "with the inner face ONE face 94.123 .. 99.558 m2, never summed high + high"),
]


# expected figures of the lines T-348 r2 / T-567 moved: the T-337 FILL figure +/- each named face (merged figures only)
_S = 4.715710 * 2 + 0.715029 + 1.252688 + 2.2533924          # 1F storey: screen front / back, corner arc, returns
_P = 0.221319 + 0.427737                                      # 1F parapet: corner arc and NW-3 return (DC)
DELTA = {
    "L-8bb83e16cc7b104ab88b": {"gross": [round(265.309300 + _S, 6), round(265.309300 + _S + 1.776291, 6)],
                               "net": [round(234.525528 + _S, 6), round(234.525528 + _S + 1.776291, 6)]},
    "NEW FIN.EXT.FINISH PARAPET-OUTER 1F +9.70": {
        "gross": [round(53.550644 - 4.223108 + 3.977236 + _P + 0.0536522, 6),
                  round(59.290836 - 4.585300 + 3.977236 + _P + 0.6974786, 6)]},
    "NEW FIN.EXT.FINISH SLAB-EDGE 1F": {"gross": None, "net": None},
    "NEW FIN.EXT.FINISH SLAB-EDGE GF": {"gross": [round(0.892720 + 0.961540, 6), round(3.347700 + 0.961540, 6)]},
}


def _rows(name, where=T337):
    with open(where / name, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def _f(x):
    return None if x in ("", None) else round(float(x), 6)


def _sha(rel):
    return hashlib.sha256((ROOT / rel).read_bytes()).hexdigest()


def build(project_id=None):
    lines = []
    for lid, (fl, parts) in EXISTING.items():
        lines.append({"key": lid, "line_id": lid, "element": "STOREY", "floor": fl, "parts": parts,
                      "why_held": "W02 (D-53) and D-GF-07 (D-45) hole sizes HELD" if fl == "GF" else None})
    for name, (el, fl, eid, parts, why) in NEW.items():
        lines.append({"key": name, "line_id": None, "element": el, "floor": fl, "element_id": eid, "parts": parts,
                      "why_held": why})
    faces = []
    for r in _rows("BINDING_T337.csv"):
        faces.append({"face_id": r["key"], "line": r["line"], "element": KIND[r["kind"]], "bottom": _f(r["bottom"]),
                      "top": _f(r["top"]), "lo": _f(r["lo"]), "hi": _f(r["hi"]), "status": r["status"],
                      "owner_q07": _f(r["owner_q07"])})
    by = {f["face_id"]: f for f in faces}
    lv = {r["key"]: r for r in _rows("FACES_T348.csv", T348)}
    for r in _rows("FILL_T314_T348.csv", T348):
        if r["consumer"] != "T-314":
            continue                       # reveal / soffit faces: their own families (T-326 / T-327, Q-68 C)
        k = r["key"]
        st = "HELD" if r["status"] == "HELD" else "DRAWING-CONFIRMED"
        lo, hi = (_f(r["m2"]), _f(r["m2"])) if r["m2"] else (_f(r["m2_lo"]), _f(r["m2_hi"]))
        if r["kind"].startswith("REMOVE"):
            del by[k]
        elif r["kind"].startswith("RE-MEASURE"):
            by[k].update(lo=lo, hi=hi, status=st)
        else:
            kind = k.rsplit("/", 1)[1]
            fl = k.split("/")[0]
            by[k] = {"face_id": k, "line": T348_LINE[(kind, fl)], "element": KIND[kind],
                     "bottom": _f(lv[k]["bottom"]), "top": _f(lv[k]["top"]), "lo": lo, "hi": hi, "status": st,
                     "owner_q07": lo if (st != "HELD" and kind != "slab_edge") else None}
    f567 = {r["key"]: r for r in _rows("FACES_T567.csv", T567)}
    for p in T567_PIER:
        r = f567[p["key"]]
        st = "HELD" if r["status"] == "HELD" else "DRAWING-CONFIRMED"
        by[p["key"]] = {"face_id": p["key"], "line": T348_LINE[(p["kind"], "1F")], "element": KIND[p["kind"]],
                        "bottom": p["bottom"], "top": p["top"], "lo": _f(r["lo"]), "hi": _f(r["hi"]), "status": st,
                        "owner_q07": _f(r["lo"]) if st != "HELD" else None}
    faces = list(by.values())
    for it in _rows("ITEMS_T337.csv"):
        for k, (prefix, el, why) in ITEM_LINES.items():
            if not it["item"].startswith(prefix):
                continue
            roof = it["item"].split()[-1]
            fl, tag = ROOF[roof]
            name = it["line"]
            lines.append({"key": name, "line_id": None, "element": el, "floor": fl,
                          "element_id": f"{fl}-FACADE:{el}:{tag}", "parts": [], "why_held": why})
            st = "DRAWING-CONFIRMED" if it["status"] == "DRAWING-CONFIRMED" else "HELD"
            faces.append({"face_id": f"{el}/{roof}", "line": name, "element": el, "bottom": None, "top": None,
                          "lo": _f(it["lo"]), "hi": _f(it["hi"]), "status": st, "owner_q07": None})
    ops = []
    for o in _rows("OPENINGS_T337.csv"):
        if o["status"] == "NOT_AN_OPENING":
            continue
        held = o["status"] == "HELD"
        ops.append({"opening_id": o["opening"], "face_id": o["face_key"], "status": o["status"],
                    "hole_m2": None if held else _f(o["fixed"]), "cap_m2": _f(o["hi"]) if held else None,
                    "sill": _f(o["sill_abs"]), "head": _f(o["head_abs"])})
    expect = {}
    for r in _rows("FILL_T314_T337.csv"):
        g = None if r["gross_lo"] == "" else [_f(r["gross_lo"]), _f(r["gross_hi"])]
        n = None if r["net_lo"] == "" else [_f(r["net_lo"]), _f(r["net_hi"])]
        expect[r["line"]] = {"gross": g, "net": n}
    for r in _rows("FILL_ITEMS_T314_T337.csv"):
        if r["line"].startswith(("NEW FIN.EXT.PARAPET-INNER", "NEW FIN.EXT.PARAPET-TOP")):
            q = [_f(r["qty_lo"]), _f(r["qty_hi"])]
            expect[r["line"]] = {"gross": q, "net": q}
    for k, e in DELTA.items():
        expect[k] = e
    srcs = [dict(s, sha256=_sha(s["file"]), checker_run=f"Verifier Gate A, merge {s['merge_commit']}")
            for s in SOURCES]
    return {"schema": SCHEMA, "project": project_id, "sources": srcs, "lines": lines, "faces": faces,
            "openings": ops, "items": [{"key": k, "unit": u, "status": s, "why": w} for k, u, s, w in MISSING],
            "expect": expect}


if __name__ == "__main__":
    if "--write" in sys.argv:
        Path(sys.argv[sys.argv.index("--write") + 1]).write_text(json.dumps(build(), ensure_ascii=False, indent=1),
                                                                 encoding="utf-8")
