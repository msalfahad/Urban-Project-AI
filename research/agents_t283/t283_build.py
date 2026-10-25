"""T-283 build (research only, stdlib): the R3 ceiling ledger, its lane-I export, the dome records and the before / after.

Inputs (committed, no coordinates): research/agents_t271/ALSENAN_T271_INPUT.json + CEILINGS_T271.csv + RECONCILE_T271.csv
(T-271 r2b, MERGED 789ebbb4) and ALSENAN_T283_DELTAS.json (t283_extract.py on the drawings). Outputs in this folder:
CEILINGS_T283.csv, BEFORE_AFTER_T283.csv, DOMES_T283.csv, CEILING_LEDGER_R3_EXPORT.json, summary.json.
`--check` rebuilds in memory and fails if any committed output differs."""
import csv
import hashlib
import io
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import ceilings_r3 as C3  # noqa: E402

T271 = HERE.parent / "agents_t271"
OWNER_H = 0.15                      # D - 0.60 for every owner-method beam here (all owner beams are D 0.75 or 0.85)
DOMES = {"west": {"open_m2": 15.359, "rooms": {}}, "east": {"open_m2": 15.359, "rooms": {}}}
DOME_OF = {"1F-073": "west", "1F-076": "east", "1F-077": "east"}
FIELDS = ["FACE", "FLOOR", "ROOM", "CLASS", "SURFACE", "QTY", "UNIT", "STATUS", "BASIS"]


def _csv(rows, fields):
    b = io.StringIO()
    w = csv.DictWriter(b, fieldnames=fields, lineterminator="\n")
    w.writeheader()
    for r in rows:
        w.writerow(r)
    return b.getvalue()


def deltas_for(face, d, warn):
    """The R3 deltas of one piece, with the committed T-271 free edge as the 'before'. A beam whose re-run free edge
    differs from the committed one is used only when it carries no quantity in R2 or R3 (CALCULATED, D <= 0.60) -
    listed as a reproduction note; otherwise the build stops."""
    r2b = {b["slab_face"]: b for b in face["beams"]}
    out = {"stair_beyond": [tuple(x) for x in d["stair_beyond"]], "beams": {}}
    for sf, b in d["beams"].items():
        c = r2b.get(sf)
        if c is None:
            raise SystemExit(f"{face['face']}: beam piece {sf} is not in the T-271 record")
        dep = b["depth"]
        carries = not (b["status"] == "CALCULATED" and dep is not None and dep <= C3.OWNER_ALLOW)
        if abs(c["free_edge_m"] - b["free_edge_m"]) > 0.002:
            if carries:
                raise SystemExit(f"{face['face']} {sf}: re-run free edge {b['free_edge_m']} vs T-271 "
                                 f"{c['free_edge_m']} on a beam that carries a quantity")
            warn.append(f"{face['face']} {sf} ({b['mark']}, D {dep}): re-run free edge {b['free_edge_m']} m vs T-271 "
                        f"{c['free_edge_m']} m; no owner face and no held edge either way (D <= 0.60), not used")
            continue
        if not carries:
            continue
        if c["cls"] == "BEAM_OR_COLUMN" and b["member"] is None and c["piece_m2"] < CRJ:
            continue                                                     # junction piece (listed in R2, no edge)
        out["beams"][sf] = {"mark": b["mark"], "status": b["status"], "depth": dep, "free_edge_m": c["free_edge_m"],
                            "borders": b["borders"]}
    return out


CRJ = C3.CR.JUNCTION_MAX


def build():
    T = json.load(open(T271 / "ALSENAN_T271_INPUT.json"))
    D = {p["face"]: p for p in json.load(open(HERE / "ALSENAN_T283_DELTAS.json"))["pieces"]}
    R2 = {}
    for r in csv.DictReader(open(T271 / "CEILINGS_T271.csv")):
        R2.setdefault(r["FACE"], []).append(r)
    REC = {r["FACE"]: r for r in csv.DictReader(open(T271 / "RECONCILE_T271.csv"))}
    warn, recs, rows, ba = [], [], [], []
    for f in T["faces"]:
        dl = deltas_for(f, D[f["face"]], warn)
        rec = C3.face_r3(f, R2[f["face"]], dl)
        rr = REC[f["face"]]
        rec["floor_piece_status"] = rr["FLOOR_PIECE_STATUS"] or "DRAWING-CONFIRMED (floor piece not yet Checker-verified)"
        rec["engine_fin_ceiling_m2"] = float(rr["ENGINE_FIN_CEILING_M2"]) if rr["ENGINE_FIN_CEILING_M2"] else None
        rec["engine_lines"] = rr["ENGINE_LINES"]
        for o in f["openings"]:
            dm = DOME_OF.get(o["slab_face"])
            if dm and o.get("open_m2", 0) > 0.0005:
                DOMES[dm]["rooms"][f["face"]] = round(DOMES[dm]["rooms"].get(f["face"], 0.0) + o["open_m2"], 6)
        recs.append(rec)
        for s in rec["surfaces"]:
            rows.append({"FACE": rec["face_id"], "FLOOR": rec["floor"], "ROOM": rec["room"], "CLASS": rec["class"],
                         "SURFACE": s["surface"], "QTY": "" if s["qty"] is None else f"{s['qty']:.4f}",
                         "UNIT": s["unit"], "STATUS": s["status"], "BASIS": s["basis"]})
        h2 = rr["HORIZONTAL_M2"]
        own2 = sum(float(r["QTY"]) for r in R2[f["face"]]
                   if r["SURFACE"].startswith("bulkhead vertical faces, owner method, total"))
        ba.append({"FACE": rec["face_id"], "FLOOR": rec["floor"], "CLASS": rec["class"],
                   "ENGINE_FIN_CEILING_M2": rr["ENGINE_FIN_CEILING_M2"], "R2_HORIZONTAL_M2": h2,
                   "R3_HORIZONTAL_M2": "" if rec.get("horizontal_m2") is None else f"{rec['horizontal_m2']:.4f}",
                   "R2_OWNER_BULKHEAD_M2": f"{own2:.4f}" if own2 else "",
                   "R3_OWNER_BULKHEAD_M2": f"{rec['owner_bulkhead_m2']:.4f}" if rec.get("owner_bulkhead_m2") else "",
                   "CHANGES": "; ".join(rec.get("changes_vs_r2", []))})
    # totals by floor and class
    tot = {"horizontal_m2": {}, "owner_bulkhead_m2": {}, "paint_owner_m2": {}}
    held = {}
    for r in recs:
        for k in tot:
            if r.get(k) is not None:
                tot[k][r["floor"]] = round(tot[k].get(r["floor"], 0.0) + r[k], 4)
        for s in r["surfaces"]:
            if s["status"] in ("HELD", "UNKNOWN") and s["qty"] is not None:
                key = (s["surface"].split(" (")[0].split(":")[0], s["unit"])
                held[key] = round(held.get(key, 0.0) + s["qty"], 4)
    tot["horizontal_by_class_m2"] = {}
    for r in recs:
        if r.get("horizontal_m2") is not None:
            c = tot["horizontal_by_class_m2"]
            c[r["class"]] = round(c.get(r["class"], 0.0) + r["horizontal_m2"], 4)
    for k in ("horizontal_m2", "owner_bulkhead_m2", "paint_owner_m2"):
        tot[k]["villa"] = round(sum(v for f, v in tot[k].items()), 4)
    domes = []
    for name, dm in DOMES.items():
        inrooms = round(sum(dm["rooms"].values()), 4)
        domes.append({"DOME": name, "OPEN_DISC_M2": f"{dm['open_m2']:.3f}",
                      "OVER_FLOOR_PIECES_M2": f"{inrooms:.4f}",
                      "OVER_WALLS_OR_OUTSIDE_M2": f"{dm['open_m2'] - inrooms:.4f}",
                      "ROOMS": "; ".join(f"{k} {v:.4f}" for k, v in sorted(dm["rooms"].items())),
                      "STATUS": "HELD (designer DCR-4: what closes the opening; Q-44 A)",
                      "S0_SHELL_INTRADOS_M2": "24.150 (T-185 S0, CALCULATED, dome finish line, scenario report only)",
                      "IN_FIN_CEILING": "no (plan area HELD apart; the shell soffit is not a decor ceiling)"})
    csv_text = _csv(rows, FIELDS)
    sha = hashlib.sha256(csv_text.encode()).hexdigest()
    export = {"schema": "URBAN_CEILING_LEDGER_R3_EXPORT_V1", "rules": ["R-CEIL-R2-1", "R-CEIL-R2-2", "R-CEIL-R2-3",
                                                                        "R-CEIL-R3-1", "R-CEIL-R3-2"],
              "integrates": {"T-271 r2b": "789ebbb4"}, "ledger_csv_sha256": sha,
              "status_note": "research ledger; NOT RELEASED; values only: item-code mapping, scope accounting and "
                             "Gate B stay with lane I (T-284)",
              "units": {"horizontal / bulkhead / paint": "m2", "edges, coves": "m"},
              "stair_zones": C3.STAIR_REF, "records": []}
    for r in recs:
        export["records"].append({
            "face_id": r["face_id"], "floor": r["floor"], "room": r["room"], "class": r["class"],
            "floor_piece_m2": r["floor_piece_m2"], "floor_piece_status": r["floor_piece_status"],
            "supersedes_engine": {"item_code": "FIN.CEILING", "room_id": r["face_id"].split("/")[0],
                                  "engine_m2": r["engine_fin_ceiling_m2"], "engine_lines": r["engine_lines"]},
            "horizontal_decor_m2": r.get("horizontal_m2"),
            "horizontal_status": "DRAWING-CONFIRMED" if r.get("horizontal_m2") is not None else "HELD",
            "owner_bulkhead_m2": r.get("owner_bulkhead_m2"), "paint_owner_m2": r.get("paint_owner_m2"),
            "surfaces": r["surfaces"], "held": sorted(set(r["held"])), "stair_ref": r.get("stair_ref")})
    export["domes"] = domes
    summ = {"pieces": len(recs), "totals": tot,
            "held_by_surface": {f"{k[0]} [{k[1]}]": v for k, v in sorted(held.items())},
            "r2_horizontal_m2": 363.1732, "r2_owner_bulkhead_m2": 29.2367, "released_fin_ceiling_m2": 403.1628,
            "freelancer_decor_m2": 409.58, "reproduction_notes": warn, "ledger_csv_sha256": sha}
    h = tot["horizontal_m2"]["villa"]
    summ["r3_vs_r2_m2"] = round(h - 363.1732, 4)
    summ["r3_vs_released_m2"] = round(h - 403.1628, 4)
    summ["r3_vs_released_pct"] = round(100 * (h - 403.1628) / 403.1628, 2)
    summ["r3_vs_freelancer_m2"] = round(h - 409.58, 4)
    summ["r3_vs_freelancer_pct"] = round(100 * (h - 409.58) / 409.58, 2)
    return {"CEILINGS_T283.csv": csv_text,
            "BEFORE_AFTER_T283.csv": _csv(ba, list(ba[0].keys())),
            "DOMES_T283.csv": _csv(domes, list(domes[0].keys())),
            "CEILING_LEDGER_R3_EXPORT.json": json.dumps(export, indent=1, sort_keys=True) + "\n",
            "summary.json": json.dumps(summ, indent=1, sort_keys=True) + "\n"}


def main(argv=None):
    a = argv if argv is not None else sys.argv[1:]
    out = build()
    if "--check" in a:
        bad = [n for n, t in out.items() if not (HERE / n).exists() or (HERE / n).read_text() != t]
        if bad:
            raise SystemExit(f"stale outputs: {bad}")
        print("T-283 outputs reproduce")
        return
    for n, t in out.items():
        (HERE / n).write_text(t)
    print(out["summary.json"])


if __name__ == "__main__":
    main()
