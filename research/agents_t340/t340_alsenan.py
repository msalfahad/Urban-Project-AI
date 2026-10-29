"""T-340 Alsenan (development villa): the Checker-verified T-313 r2 reveal ledger and T-325 sills / thresholds ledger
(with the T-336 threshold corrections) bound to the CANDIDATE OF RECORD ARCH_TAKEOFF_V3.0.22 line ids, one owner per
physical component, with the wet-room cross-check against the V3.0.22 backing plaster (T-331) and the wall-tile faces
(T-312 / T-315 r2), the finish-vs-waterproofing threshold layer check, the trace of the five closure-strip residuals
T-325 left open, and the FILL tables lane I consumes unchanged (T-326 reveals, T-327 sills / thresholds). Research
only: no engine module, candidate line or released line changes.

    python3 -I research/agents_t340/t340_alsenan.py --extract <v3022 run dir>   # writes CANDIDATE_V3022_T340.json
    python3 -I research/agents_t340/t340_alsenan.py --write                     # writes the binding files
    python3 -I research/agents_t340/t340_alsenan.py --check                     # rebuilds in memory, compares bytes

Inputs (committed, merged): research/agents_t313 (REVEAL_LEDGER, DOOR_PLASTER_RECONCILIATION), research/agents_t325
(SILL_THRESHOLD_LEDGER, LINES), research/agents_t336/FILL_T310_T336.csv (WP doorway pieces), research/agents_t312
(OPENINGS, FACE_LEDGER), research/agents_t329/BACKING_FACE_LEDGER_T329.csv, and CANDIDATE_V3022_T340.json (extracted here
from an own V3.0.20 / V3.0.21 / V3.0.22 run: ids, item codes, element ids, units, states, quantities and a digest of each
line per version; no coordinates, no names). Drawing readings added here are cited by DXF entity handle on Drive
'Alsenan chalet project' / P7757_DXF_COMPRESSED.zip (P7757.dxf sha256 ab54dd55..), lengths only.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
RES = ROOT / "research"
sys.path.insert(0, str(HERE))
import t340_binding as B  # noqa: E402

CAND = HERE / "CANDIDATE_V3022_T340.json"
OUT = {"owners": HERE / "OWNERS_T340.csv", "t326": HERE / "FILL_T326_T340.csv", "t327": HERE / "FILL_T327_T340.csv",
       "wet": HERE / "WET_CROSS_CHECK_T340.csv", "faces": HERE / "FACE_CLOSURE_T340.csv",
       "layers": HERE / "THRESHOLD_LAYERS_T340.csv", "trace": HERE / "CLOSURE_TRACE_T340.csv",
       "rebind": HERE / "LINE_REBIND_T340.csv", "summary": HERE / "summary.json"}
DXF = "Drive 'Alsenan chalet project' / P7757_DXF_COMPRESSED.zip, P7757.dxf"
FAMILIES = ("FIN.PLASTER", "ARCH.WINDOW_REVEAL", "ARCH.THRESHOLD", "FIN.MARBLE.THRESHOLD", "FIN.FLOOR.PORCELAIN",
            "FIN.WALL.TILE", "FIN.WP.DOORWAY")
SOURCES = {"T-313": "T-313 r2 MERGED 5f2bf0d5 (Verifier 2026-10-29 01:29, own re-measure)",
           "T-325": "T-325 MERGED (Verifier 2026-10-29 04:59)",
           "T-336": "T-336 MERGED c4246877 (Verifier 2026-10-29 11:58)",
           "T-329": "T-329 MERGED 1c82807b / T-331 MERGED 15ac21f7 (Gate B, V3.0.22)",
           "T-312": "T-312 MERGED 8943b5ed"}

# --- the 5 BLOCKED closure strips (T-325 s.3): own read at the jambs (wall-face line ends; lengths in m, no coordinates)
# jamb gap = clear width; face pair = depth; the closure polygon runs on past a jamb over the wall-end nib and, on three
# doors, across the cross wall to its far face. strip_m2 = the line's own polygon (LINES_T325.csv).
TRACE = [
    {"door": "D-GF-02", "symbol": "INSERT 1EF (D315)", "faces": "117 / 118 and 115 / 116", "width_m": 0.800,
     "depth_m": 0.150, "nib": "118 / 116 to wall face 129: 0.0736149", "cross_wall": "129 / 127: 0.150",
     "extension_m": 0.2236149, "strip_m2": 0.153542},
    {"door": "D-GF-10", "symbol": "INSERT 339 (D315)", "faces": "2B1 / 2B2 and 2AF / 2B0", "width_m": 0.7970392,
     "depth_m": 0.150, "nib": "2B1 / 2AF to wall face 215: 0.0529608", "cross_wall": "215 / 21B: 0.200",
     "extension_m": 0.2529608, "strip_m2": 0.1575},
    {"door": "D-GF-14", "symbol": "ARC 334 (loose leaf, r 0.690)", "faces": "2E5 / 2E6 and 2E7 / 2E8", "width_m": 0.800,
     "depth_m": 0.150, "nib": "east: 2E6 / 2E8 to wall face 2DD 0.0391811; west: face 2E5 runs 0.278661 to the "
     "splayed wall 325, then the polygon fills the splayed-wall junction (ends of 325 / 318 and 2E7)",
     "cross_wall": "2DD / 2DE: 0.150", "extension_m": None, "strip_m2": 0.218846,
     "parts_m2": {"east nib + cross wall 0.1891811 x 0.150": 0.0283772, "west face run 2E5 0.278661 x 0.150": 0.0417992,
                  "splayed-wall junction pocket (the line's own polygon, 4-dp vertices)": 0.0286632}},
    {"door": "D-1F-03", "symbol": "INSERT C32 (D115)", "faces": "AEA / AEB and AE8 / AE9", "width_m": 1.000,
     "depth_m": 0.150, "nib": "AEA / AE8 to wall face C21: 0.0885198", "cross_wall": "C21 / C1F: 0.150",
     "extension_m": 0.2385198, "strip_m2": 0.185778},
    {"door": "D-1F-04", "symbol": "INSERT C2E (D315)", "faces": "C1B / C1D (south jamb), C1C / C1E (north jamb)",
     "width_m": 0.800, "depth_m": 0.150, "nib": "C1B / C1D to wall faces AE6 / C25: 0.0798447", "cross_wall": "none",
     "extension_m": 0.0798447, "strip_m2": 0.131977},
]
RETYPE = {"D-GF-02": "FIN.MARBLE.THRESHOLD", "D-GF-10": "FIN.MARBLE.THRESHOLD", "D-GF-14": "FIN.MARBLE.THRESHOLD",
          "D-1F-04": "FIN.MARBLE.THRESHOLD", "D-1F-03": "FIN.FLOOR.PORCELAIN"}
WP_ALIAS = {"D-GF-07-PANTRY": "D-GF-06"}       # T-336 names the pantry door by room; census D-GF-06 = INSERT 33E D120


def _sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def _csvr(p):
    with open(p, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _f(v, nd=6):
    return "" if v is None else f"{v:.{nd}f}"


# ------------------------------------------------------------------------------------------------ extraction
def _digest(ln):
    return hashlib.sha256(json.dumps(ln, sort_keys=True, ensure_ascii=False).encode()).hexdigest()[:16]


def _rng(ln):
    br = ln.get("bounded_range")
    if isinstance(br, dict):
        return br.get("low"), br.get("high")
    if isinstance(br, (list, tuple)):
        return tuple(br[:2])
    return None, None


def extract(run_dir):
    """the lines of the seven families in V3.0.20 / V3.0.21 / V3.0.22 of one run: V3.0.22 fields + a digest per version."""
    run = Path(run_dir)
    vers = {}
    shas = {}
    for v in ("V3_0_20", "V3_0_21", "V3_0_22"):
        p = run / f"{v}_BOQ_LINES.json"
        shas[v] = _sha(p)[:8]
        raw = json.loads(p.read_text(encoding="utf-8"))
        vers[v] = {ln["line_id"]: ln for ln in (raw["lines"] if isinstance(raw, dict) else raw)}
    out = []
    for lid, ln in vers["V3_0_22"].items():
        if ln.get("item_code") not in FAMILIES:
            continue
        loc = ln.get("location") or {}
        lo, hi = _rng(ln)
        out.append({"line_id": lid, "item_code": ln["item_code"], "unit": ln.get("unit"),
                    "evidence_state": ln.get("evidence_state"), "measured_net": ln.get("measured_net"),
                    "low": lo, "high": hi, "floor": loc.get("floor"), "element_id": loc.get("element_id"),
                    "physical_element": ln.get("physical_element"),
                    "digest": {v: (_digest(vers[v][lid]) if lid in vers[v] else None) for v in vers}})
    out.sort(key=lambda x: (x["item_code"], x["line_id"]))
    gone = sorted(lid for v in ("V3_0_20", "V3_0_21") for lid, ln in vers[v].items()
                  if ln.get("item_code") in FAMILIES and lid not in vers["V3_0_22"])
    return {"source": "own run research/agents_t167/v304_run.py -> research/agents_t331/v3022_run.py",
            "lines_json_sha8": shas, "lines_total": {v: len(x) for v, x in vers.items()}, "families": list(FAMILIES),
            "gone_since_v3020": gone, "lines": out}


# ------------------------------------------------------------------------------------------------ build
def build():
    cand = json.loads(CAND.read_text(encoding="utf-8"))
    lines = {x["line_id"]: x for x in cand["lines"]}
    rev = _csvr(RES / "agents_t313" / "REVEAL_LEDGER_T313.csv")
    sil = _csvr(RES / "agents_t325" / "SILL_THRESHOLD_LEDGER_T325.csv")
    dpr = _csvr(RES / "agents_t313" / "DOOR_PLASTER_RECONCILIATION_T313.csv")
    l325 = {x["line_id"]: x for x in _csvr(RES / "agents_t325" / "LINES_T325.csv")}
    wpf = _csvr(RES / "agents_t336" / "FILL_T310_T336.csv")
    o312 = _csvr(RES / "agents_t312" / "OPENINGS_T312.csv")
    f312 = _csvr(RES / "agents_t312" / "FACE_LEDGER_T312.csv")
    b329 = _csvr(RES / "agents_t329" / "BACKING_FACE_LEDGER_T329.csv")

    comps = B.merge_ledgers(B.reveal_components(rev), B.sill_components(sil))
    door_plaster = {x["opening"]: x["line_id"] for x in dpr}
    narrow = {}
    for x in dpr:
        if x["opening"] == "D-GF-07":    # the drawing PRINTS 2.50 m (T-201 / T-237): the line's low end is excluded
            narrow[x["line_id"]] = (1.4, "NARROW to the printed height 2.50 m (DRAWING-CONFIRMED): bound 1.28 .. 1.40 "
                                         "-> 1.400 (T-313 r2 s.5, Checker own-confirmed)")
    retype = {}
    for k, c in comps.items():
        if c.comp == "THRESHOLD" and c.opening in RETYPE:
            retype[c.ledger_line] = (RETYPE[c.opening], f"RETYPE the BLOCKED closure strip to {RETYPE[c.opening]} "
                                     "(UP-THR-001; wet doorway marble by URBAN-WET-SERVICE-MARBLE-THRESHOLD v1, dry "
                                     "porcelain continued) and FILL clear width x wall t, never the closure polygon")
    new_rows = {}
    for k, c in comps.items():
        if c.ledger_line:
            continue
        if c.status == "NOT_APPLICABLE_WITH_EVIDENCE":
            continue
        if c.comp.startswith("REVEAL_THROUGH"):
            fam = "FIN.PLASTER|door jambs and head" if c.kind == "DOOR" else (
                "FIN.PLASTER|gate jambs and head" if c.kind == "GATE" else "REVEAL.ARCH|arch jambs and head")
            new_rows[k] = f"{fam}|{c.opening}"
        elif c.comp.startswith("REVEAL_OUT") or c.comp.startswith("REVEAL_IN"):
            side = "OUT" if c.comp.startswith("REVEAL_OUT") else "IN"
            new_rows[k] = f"REVEAL.WINDOW_{side}|window jambs and head|{c.opening}"
        elif c.comp in ("SILL_OUT", "SILL_IN", "THRESHOLD_OUT", "THRESHOLD_IN"):
            new_rows[k] = f"ARCH.WINDOW_REVEAL|window sill / floor-level strip|{c.opening}"
        elif c.comp == "THRESHOLD":
            new_rows[k] = f"ARCH.THRESHOLD|threshold strip|{c.opening}"
    owners, carriers = B.assign_owners(comps, lines, door_plaster, narrow, retype, new_rows)

    # superseded closure polygons (T-325 s.3, T-336 s.3): never the fill
    fills = {(r.opening, "THRESHOLD"): r.m2 for r in owners if r.comp == "THRESHOLD" and r.m2 is not None}
    B.check_superseded(fills, {(t["door"], "THRESHOLD"): t["strip_m2"] for t in TRACE})

    # ---- closure trace: width x depth + extension x depth = the polygon, residual named
    trace = []
    for t in TRACE:
        clear = round(t["width_m"] * t["depth_m"], 6)
        led = comps[(t["door"], "THRESHOLD")].m2
        if t["extension_m"] is None:
            ext = round(sum(t["parts_m2"].values()), 6)
            res = round(t["strip_m2"] - clear - ext, 6)
            cause = ("TRACED: the polygon runs past both jambs: " + "; ".join(f"{k} = {v:.7f}" for k, v in
                     t["parts_m2"].items()) + f" -> {ext:.6f} m2; residual {res:.6f} m2 = vertex rounding of the 4-dp "
                     "polygon; the threshold stays the jamb read 0.120 (T-336)")
        else:
            ext = round(t["extension_m"] * t["depth_m"], 6)
            res = round(t["strip_m2"] - clear - ext, 6)
            cause = (f"TRACED: the closure polygon runs {t['extension_m']:.7f} m past the jamb (wall-end nib"
                     f"{' + cross wall' if t['cross_wall'] != 'none' else ''}): {ext:.6f} m2; residual {res:.6f} m2")
        trace.append({"door": t["door"], "symbol": t["symbol"], "jamb_faces": t["faces"], "drawn_width_m": t["width_m"],
                      "depth_m": t["depth_m"], "clear_m2": clear, "ledger_m2": led,
                      "ledger_minus_drawn_m2": round(led - clear, 6), "closure_polygon_m2": t["strip_m2"],
                      "nib": t["nib"], "cross_wall": t["cross_wall"],
                      "polygon_minus_clear_m2": round(t["strip_m2"] - clear, 6), "residual_m2": res, "cause": cause,
                      "source": f"{DXF}; strip polygon: LINES_T325.csv"})

    # a drawn jamb gap that differs from the ledger width: the ledger figure is carried (Checker-passed), the own read is
    # a correction PROPOSAL beside it on the carrier (threshold and head soffit), for the Checker's Gate A
    for t in trace:
        if abs(t["ledger_minus_drawn_m2"]) > B.TOL:
            for c in carriers:
                if c["opening"] == t["door"] and ("THRESHOLD" in c["components"] or "REVEAL_THROUGH_HEAD" in c["components"]):
                    c["note"] += (f"; CORRECTION PROPOSED (own jamb read {t['jamb_faces']}: clear width "
                                  f"{t['drawn_width_m']:.7f} m, not the T-237 0.800 matched within 0.06): "
                                  f"{'threshold' if 'THRESHOLD' in c['components'] else 'head soffit'} "
                                  f"{t['drawn_width_m'] * t['depth_m']:.6f} m2 (-{t['ledger_minus_drawn_m2']:.6f}); "
                                  "the ledger figure is carried until the Checker confirms")

    # ---- finish threshold vs waterproofing doorway piece (same strip, two layers)
    fin = {c.opening: c.m2 for c in comps.values() if c.comp == "THRESHOLD" and c.m2 is not None}
    wp, wp_super = {}, {}
    for x in wpf:
        if x["kind"] != "THRESHOLD" or x["family"] != "WP.WET_AREA":
            continue
        door = x["piece"].split("DOOR:")[1].split("/")[0]
        wp[door] = float(x["after"])
        if x["action"] == "CORRECT":
            wp_super[(B_alias(door), "WP")] = float(x["before"])
    B.check_superseded({(B_alias(d), "WP"): v for d, v in wp.items()}, wp_super)
    layers = B.layer_check(fin, wp, WP_ALIAS)
    wet_doors = {c.opening for c in comps.values() if c.comp == "THRESHOLD" and "MARBLE" in (c.material or "")}
    for r in layers:
        d = r["door"]
        r["finish_material"] = comps[(d, "THRESHOLD")].material[:40] if (d, "THRESHOLD") in comps else ""
        if r["result"].startswith("DIFFERS"):
            tr = next((t for t in trace if t["door"] == d), None)
            r["cause"] = ("the WP piece is the drawn jamb gap (wall-face ends) x depth; the finish ledger used the T-237 "
                          "width 0.800 (matched within 0.06): "
                          + (f"drawn width {tr['drawn_width_m']} m" if tr else "not traced here"))
        elif r["result"].startswith("FINISH ONLY"):
            r["cause"] = ("wet marble doorway with no membrane piece" if d in wet_doors else
                          "dry / external doorway: the membrane rule does not reach it")
        elif r["door"] == "D-GF-06":
            r["cause"] = ("one strip, two layers: T-336's 'D-GF-07-PANTRY' is census D-GF-06 (INSERT 33E D120 into the "
                          "pantry GF-07); finish material HELD (external-entrance class, T-240), membrane Q-37 A")
        else:
            r["cause"] = "one strip, two layers, equal"

    # ---- wet rooms: every backed / tiled face closes; every opening in such a face named with its components' owners
    backing_lines = {x["plaster_line_id"] for x in b329 if x["plaster_line_id"]}
    tile_lines = {x["tile_line_id"] for x in b329 if x["tile_line_id"]} | {x["line_id"] for x in f312 if x["line_id"]}
    parts = {(x["face_id"], x["opening_id"]): B.num(x["band_m2"]) for x in o312}
    faces, held_faces = [], []
    for x in b329:
        if x["tile_scope"] != "TILED":
            continue
        ops = x["openings"].split()
        if not x["backing_owner_m2"]:
            held_faces.append({"face_id": x["face_id"], "room": x["room"], "openings": ops})
            continue
        faces.append({"face_id": x["face_id"], "length_m": float(x["length_m"]), "top_m": float(x["tile_top_m"]),
                      "net_m2": float(x["backing_owner_m2"]), "openings": ops})
    tile_faces = [{"face_id": x["face_id"], "length_m": float(x["length_m"]), "top_m": float(x["owner_h_m"]),
                   "net_m2": float(x["owner_net_m2"]), "openings": x["openings"].split()}
                  for x in f312 if x["scope"] == "TILED" and x["owner_net_m2"]]
    clo_b = B.face_closure(faces, parts)
    clo_t = B.face_closure(tile_faces, parts)
    wet_open = [{"room": f["face_id"].split("|")[0], "opening": o, "face_id": f["face_id"],
                 "band_m2": parts[(f["face_id"], o)]} for f in faces for o in f["openings"]]
    wet = B.wet_cross_check(wet_open, owners, backing_lines, tile_lines, clo_b + clo_t)
    held_wet = []
    by_open = {}
    for r in owners:
        by_open.setdefault(r.opening, []).append(r)
    for f in held_faces:
        for o in f["openings"]:
            for r in sorted(by_open.get(o, []), key=lambda z: z.comp):
                if r.owner in backing_lines or r.owner in tile_lines:
                    raise B.BindingError(f"{o}: owned by a backing / tile line")
                held_wet.append({"room": f["room"], "face_id": f["face_id"], "opening": o, "band_part_m2": None,
                                 "component": r.comp, "component_m2": r.m2, "owner": r.owner or "(none)",
                                 "owner_item": r.owner_item, "status": r.status,
                                 "overlap_m2": 0.0 if r.m2 is not None else None,
                                 "why": "the face itself is HELD (backing / tile blank, T-331); the opening's "
                                        "components keep their own owner, no figure in the held face"})
    # the backing faces ARE the V3.0.22 filled lines: per plaster line, the sum of its faces = the line's figure
    per_line = {}
    for x in b329:
        if x["tile_scope"] == "TILED" and x["plaster_line_id"]:
            per_line.setdefault(x["plaster_line_id"], []).append(B.num(x["backing_owner_m2"]))
    backing_vs_line = []
    for lid, vals in sorted(per_line.items()):
        ln = lines[lid]
        q = B.num(ln["measured_net"])
        tot = None if any(v is None for v in vals) else round(sum(vals), 4)
        if (q is None) != (tot is None) or (q is not None and abs(q - tot) > 0.00051):
            raise B.BindingError(f"{lid}: backing faces {tot} vs V3.0.22 line {q}")
        backing_vs_line.append({"line_id": lid, "faces": len(vals), "faces_m2": tot, "v3022_m2": q,
                                "state_v3022": ln["evidence_state"]})
    face_rows = ([dict(r, layer="BACKING (FIN.PLASTER V3.0.22)") for r in clo_b] +
                 [dict(r, layer="WALL TILE (FIN.WALL.TILE, T-312 owner method)") for r in clo_t])

    # ---- line rebind: every carrier line V3.0.20 (the ledgers' grain) = V3.0.21 = V3.0.22
    rebind = []
    wp_lines = {x["row"] for x in wpf if x["kind"] == "THRESHOLD" and x["row"].startswith("L-")}
    for cid in sorted({r.owner for r in owners if r.owner and not r.owner.startswith("NEW:")} | wp_lines):
        ln = lines.get(cid)
        if ln is None:
            raise B.BindingError(f"{cid}: not a line of V3.0.22")
        d = ln["digest"]
        rebind.append({"line_id": cid, "item_code": ln["item_code"], "state_v3022": ln["evidence_state"],
                       "measured_net": ln["measured_net"], "low": ln["low"], "high": ln["high"],
                       "digest_v3020": d["V3_0_20"], "digest_v3021": d["V3_0_21"], "digest_v3022": d["V3_0_22"],
                       "result": "SAME" if d["V3_0_20"] == d["V3_0_21"] == d["V3_0_22"] else "CHANGED"})
    return {"cand": cand, "comps": comps, "owners": owners, "carriers": carriers, "trace": trace, "layers": layers,
            "wet": wet + held_wet, "faces": face_rows, "backing_vs_line": backing_vs_line, "rebind": rebind, "l325": l325}


def B_alias(d):
    return WP_ALIAS.get(d, d)


def _write_csv(rows, cols):
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=cols, lineterminator="\n", extrasaction="ignore")
    w.writeheader()
    for r in rows:
        w.writerow({k: (_f(v) if isinstance(v, float) else ("" if v is None else v)) for k, v in r.items()})
    return buf.getvalue()


def outputs():
    b = build()
    owners = [dict(vars(r)) for r in b["owners"]]
    for r in owners:
        c = b["comps"][(r["opening"], r["comp"])]
        r["sources"] = " + ".join(SOURCES[s] for s in c.sources)
    cols_o = ["opening", "comp", "owner", "owner_item", "action", "m2", "ml", "pcs", "status", "material", "fill_table",
              "note", "sources"]
    car = b["carriers"]
    cols_c = ["carrier", "opening", "item", "action", "m2", "ml", "pcs", "components", "held", "status", "material",
              "note"]
    files = {
        "owners": _write_csv(owners, cols_o),
        "t326": _write_csv([c for c in car if c["fill_table"] == "T-326"], cols_c),
        "t327": _write_csv([c for c in car if c["fill_table"] == "T-327"], cols_c),
        "wet": _write_csv(b["wet"], ["room", "face_id", "opening", "band_part_m2", "component", "component_m2", "owner",
                                     "owner_item", "status", "overlap_m2", "why"]),
        "faces": _write_csv(b["faces"], ["layer", "face_id", "gross_m2", "deductions_m2", "net_m2", "residual_m2"]),
        "layers": _write_csv(b["layers"], ["door", "finish_m2", "wp_m2", "difference_m2", "result", "finish_material",
                                           "cause"]),
        "trace": _write_csv(b["trace"], ["door", "symbol", "jamb_faces", "drawn_width_m", "depth_m", "clear_m2",
                                         "ledger_m2", "ledger_minus_drawn_m2", "closure_polygon_m2",
                                         "polygon_minus_clear_m2", "residual_m2", "nib", "cross_wall", "cause", "source"]),
        "rebind": _write_csv(b["rebind"], ["line_id", "item_code", "state_v3022", "measured_net", "low", "high",
                                           "digest_v3020", "digest_v3021", "digest_v3022", "result"]),
    }
    files["summary"] = json.dumps(summary(b), indent=1, sort_keys=True, ensure_ascii=False) + "\n"
    return files


def _sum(rows, pred, key="m2"):
    return round(sum(r[key] for r in rows if pred(r) and r[key] is not None), 6)


def summary(b):
    car = b["carriers"]
    by_act = {}
    for c in car:
        by_act.setdefault(f"{c['fill_table']}:{c['action']}", []).append(c)
    acts = {k: {"carriers": len(v), "m2": round(sum(c["m2"] or 0 for c in v), 6)} for k, v in sorted(by_act.items())}
    t326 = [c for c in car if c["fill_table"] == "T-326"]
    t327 = [c for c in car if c["fill_table"] == "T-327"]
    return {
        "candidate": {"lines_json_sha8": b["cand"]["lines_json_sha8"], "lines_total": b["cand"]["lines_total"]},
        "components": len(b["owners"]), "openings": len({r.opening for r in b["owners"]}),
        "carriers": len(car), "actions": acts,
        "t326_reveals": {
            "in_line_kept_m2": _sum(t326, lambda c: c["action"] in ("KEEP", "NARROW")),
            "narrowed": [c["carrier"] for c in t326 if c["action"] == "NARROW"],
            "new_rows_m2": _sum(t326, lambda c: c["action"] == "ADD_ROW"),
            "new_door_rows_m2": _sum(t326, lambda c: c["action"] == "ADD_ROW" and c["item"] == "FIN.PLASTER"),
            "new_window_out_rows_m2": _sum(t326, lambda c: c["action"] == "ADD_ROW" and
                                           c["item"] == "REVEAL.WINDOW_OUT"),
            "held_rows": [c["carrier"] for c in t326 if c["action"] in ("ADD_HELD_ROW", "HOLD")],
            "held_beside": [c["carrier"] for c in t326 if c["held"] and c["action"] not in ("ADD_HELD_ROW", "HOLD")]},
        "t327_sills_thresholds": {
            "kept_m2": _sum(t327, lambda c: c["action"] == "KEEP"),
            "filled_m2": _sum(t327, lambda c: c["action"] == "FILL"),
            "retyped_filled_m2": _sum(t327, lambda c: c["action"] == "RETYPE_FILL"),
            "new_rows_m2": _sum(t327, lambda c: c["action"] == "ADD_ROW"),
            "held": [c["carrier"] for c in t327 if c["action"] in ("ADD_HELD_ROW", "HOLD")]},
        "wet_cross_check": {"rows": len(b["wet"]), "overlap_m2": round(sum(r["overlap_m2"] or 0 for r in b["wet"]), 6),
                            "faces_closed": len(b["faces"]),
                            "max_abs_face_residual_m2": max(abs(r["residual_m2"]) for r in b["faces"]),
                            "backing_lines": {"filled_equal": sum(r["v3022_m2"] is not None for r in b["backing_vs_line"]),
                                              "held_blank": sum(r["v3022_m2"] is None for r in b["backing_vs_line"]),
                                              "filled_m2": round(sum(r["v3022_m2"] or 0 for r in b["backing_vs_line"]),
                                                                 4)}},
        "threshold_layers": {r["door"]: r["result"] for r in b["layers"]},
        "closure_trace": {t["door"]: t["cause"][:60] for t in b["trace"]},
        "rebind": {"lines": len(b["rebind"]), "same": sum(r["result"] == "SAME" for r in b["rebind"]),
                   "changed": [r["line_id"] for r in b["rebind"] if r["result"] != "SAME"]},
    }


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--extract", help="a V3.0.22 run directory (writes CANDIDATE_V3022_T340.json)")
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args(argv)
    if a.extract:
        CAND.write_text(json.dumps(extract(a.extract), indent=1, sort_keys=True) + "\n", encoding="utf-8")
        print("extract", CAND.name, _sha(CAND)[:8])
    if a.write or a.check:
        files = outputs()
        bad = []
        for k, txt in files.items():
            if a.write:
                OUT[k].write_text(txt, encoding="utf-8")
            elif OUT[k].read_text(encoding="utf-8") != txt:
                bad.append(OUT[k].name)
        print("check", "OK" if not bad else f"DIFFERS {bad}")
        return 1 if bad else 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
