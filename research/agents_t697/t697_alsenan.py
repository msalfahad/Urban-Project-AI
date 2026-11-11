"""T-697 builder (development villa): the merged T-405 arris ledger restated on candidate ARCH_TAKEOFF_V3.0.68.

Inputs are committed merged records only (no drawing data is stored here):
  research/agents_t405/EDGE_LEDGER_T405.csv     which edges are arrises (T-405, MERGED cd1aadaf, Gate A PASS)
  research/agents_t672/out/LINE_INDEX_V3_0_68.json  candidate line index (T-672, V3.0.68, lines sha d1de50cb)
  research/agents_t680/out/T680_SHAFT_ROUND2.json   shaft pier-return areas by storey band (T-680 MERGED 707c624e)
  research/agents_t313/WINDOW_DEPTHS_T313.csv     window floor (T-313 r2 MERGED)
  research/alsenan_stairs_s8_7a/05_WAIST_AND_LANDING_GEOMETRY.csv  stair C quarter landing level C-L1 (SOURCE_VERIFIED)
Own drawing read this run (values only, recorded in the report): GF-08 #V60 / #V61 under the HIDDEN outline of stair C's
quarter landing (layer '2', linetype HIDDEN, handles 4AF / 4B6 / 141 on P7757.dxf ab54dd55).

Usage: python3 -I t697_alsenan.py [--write | --check]
"""

import csv
import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
import t697_rules as R  # noqa: E402

OUT = os.path.join(HERE, "out")
SRC = {
    "t405": "research/agents_t405/EDGE_LEDGER_T405.csv",
    "index": "research/agents_t672/out/LINE_INDEX_V3_0_68.json",
    "t680": "research/agents_t680/out/T680_SHAFT_ROUND2.json",
    "t313w": "research/agents_t313/WINDOW_DEPTHS_T313.csv",
    "s87a": "research/alsenan_stairs_s8_7a/05_WAIST_AND_LANDING_GEOMETRY.csv",
}

# Owner G1 finished-ceiling height above the floor finish (Q-43 / Q-48 A; owner heights rule 2026-11-02: paint to the
# finished ceiling). Structural soffit height for plaster (T-556 MERGED: 4.50 / 4.20 storey interval - 0.05 build-up
# - 0.16 slab; 2F under the roof at the drawn-section scenario, D-39).
G1 = {"GF": 3.65, "1F": 3.35, "2F": 3.35}
SOFFIT = {"GF": 4.29, "1F": 3.99, "2F": 3.99}
SOFFIT_STATUS = {"GF": "DRAWING-CONFIRMED (T-556)", "1F": "DRAWING-CONFIRMED (T-556)",
                 "2F": "HELD scenario: roof build-up not printed (D-39)"}
PIER_DEPTH = 0.05      # T-173 ALSENAN_SHAFT_INPUT pier_returns: printed '5', DXF S-COL.BON, GF / 1F / 2F
GF_FFL = 1.00          # GF-08 floor (+1.00, section A-A; T-556 GF interval +1.00 / +5.50)
LANDING_SLAB = 0.16    # 'T 16' zone tag in the stair C zone (GFRS 5B6); the waist itself is OWNER_SCENARIO
BUILDUP = (0.0, 0.10)  # landing build-up b, not printed (DCR-6 / DCR-7), as T-680


def sha8(path):
    with open(os.path.join(ROOT, path), "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()[:8]


def load():
    rows = list(csv.DictReader(open(os.path.join(ROOT, SRC["t405"]), encoding="utf-8")))
    idx = json.load(open(os.path.join(ROOT, SRC["index"]), encoding="utf-8"))
    index = {l["line_id"]: l for l in idx["lines"]}
    t680 = json.load(open(os.path.join(ROOT, SRC["t680"]), encoding="utf-8"))
    wfloor = {r["opening"]: r["floor"] for r in csv.DictReader(open(os.path.join(ROOT, SRC["t313w"]), encoding="utf-8"))}
    land = None
    for r in csv.DictReader(open(os.path.join(ROOT, SRC["s87a"]), encoding="utf-8")):
        if r["ITEM"] == "C-DRAWN-28 C-L1 finished level" and r["STATE"] == "SOURCE_VERIFIED":
            land = float(r["VALUE"])
    if land is None:
        raise R.BeadRuleError("stair C landing level C-L1 not found (HELD)")
    return rows, idx, index, t680, wfloor, land


def by_element(index, code, element_id):
    hits = [l for l in index.values() if l["item_code"] == code and l["element_id"] == element_id]
    if len(hits) != 1:
        raise R.BeadRuleError("expected one %s line for %s, found %d" % (code, element_id, len(hits)))
    return hits[0]["line_id"]


def floor_of(row, wfloor):
    room, eid = row["room"], row["edge_id"]
    for f in ("GF", "1F", "2F"):
        if room.startswith(f) or room.startswith("ST-" + f) or eid.startswith("EXT#" + f) or eid.startswith("D-" + f):
            return f
    op = eid.split("#")[0]
    if op in wfloor:
        return wfloor[op]
    if eid.startswith("LIFT#"):
        return eid.split("#")[1][:2]
    return ""


def build():
    rows, idx, index, t680, wfloor, land = load()
    ext_host = {f: by_element(index, "FIN.EXT.FINISH", f + "-FACADE:facade") for f in ("GF", "1F", "2F")}
    plinth_host = by_element(index, "ARCH.FACADE", "GF-FACADE:facade below F.F.L. (plinth)")
    surround = {f: by_element(index, "FIN.MARBLE.LIFT_SURROUND", "LIFT:ELV-01-%s:surround" % f) for f in ("GF", "1F", "2F")}
    paint_returns = {l["band"]: l["returns_lo_hi"] for l in t680["lines"] if l["finish"] == "paint"}
    plaster_returns = {l["band"]: l["returns_lo_hi"] for l in t680["lines"] if l["finish"] == "plaster"}
    shaft_host = {l["band"]: l["line_id"] for l in t680["lines"] if l["finish"] == "plaster"}
    # stair C quarter landing over GF-08 #V60 / #V61: soffit above the GF-08 floor finish
    ov_hi = land - BUILDUP[0] - LANDING_SLAB - GF_FFL
    ov_lo = land - BUILDUP[1] - LANDING_SLAB - GF_FFL

    out, shaft_done = [], set()
    for r in rows:
        f = floor_of(r, wfloor)
        rec = {"edge_id": r["edge_id"], "scope": r["scope"], "floor": f, "room": r["room"], "class": r["class"],
               "count": r["count"], "status": "", "owner_m": "", "dwg_low": "", "dwg_high": "", "held_low": "",
               "held_high": "", "binding": "", "host_line": "", "host_code": "", "host_class": "", "owner_trade": "",
               "owning_line": "", "t405_owner_m": r["owner_m"], "t405_status": r["owner_status"], "rule": "",
               "cause": "", "source": r["source"][:160]}
        hosts = [h.strip() for h in r["line_id"].split("|")] if r["line_id"].startswith("L-") else []
        if r["line_id"].startswith("FIN.EXT.FINISH"):
            hosts = [ext_host[f]]
        if r["scope"] == "EXTERIOR" and not hosts and f and not r["edge_id"].startswith("D-GF-15"):
            hosts = [ext_host[f]]          # an opening's outer ring lies on its own floor's facade line
        st = r["owner_status"]

        if r["edge_id"].startswith("LIFT#"):                       # R-T697-4: the surround owns the entrance arrises
            rec.update(R.exclusion("B6-06", surround[f]))
            rec["binding"] = "OWNED_BY_B6-06"
            rec.update(rule="R-T697-4", cause="lift entrance: the B6-06 surround owns the arrises (ELEMENT_REGISTER "
                       "LIFT ENTRANCE, Lead 2026-11-01; corner-bead ruling 2026-11-11); T-405 had it HELD "
                       "(LIFT_ENTRANCE_HEAD_NOT_ESTABLISHED)")
            out.append(rec)
            continue

        if r["room"].startswith("ST-") and r["class"] == "EXTERNAL_CORNER":   # R-T697-6 shaft pier arrises, per band
            if f in shaft_done:
                continue
            shaft_done.add(f)
            pair = [x["edge_id"] for x in rows if x["room"] == r["room"] and x["class"] == "EXTERNAL_CORNER"]
            lo_p, hi_p = (float(v) for v in paint_returns[f])
            lo, hi = R.shaft_band_arrises(lo_p, hi_p, PIER_DEPTH)
            pl_lo, pl_hi = (float(v) for v in plaster_returns[f])
            rec.update(edge_id=" + ".join(pair), count=str(len(pair)), binding="BOUND", host_line=shaft_host[f],
                       rule="R-T697-6",
                       source="T-680 MERGED 707c624e returns_lo_hi (paint = exposed, plaster %.3f .. %.3f m2) / depth "
                              "0.05 (T-173 pier_returns u 3.00 / 3.50, column face 0.50)" % (pl_lo, pl_hi))
            if lo == hi:
                rec.update(status="DRAWING-CONFIRMED", owner_m=lo, dwg_low=lo, dwg_high=R.q4(pl_hi / PIER_DEPTH),
                           cause="Q-72 answered (full exposed height); band net of flights / landings (T-680)")
            else:
                rec.update(status="HELD", held_low=lo, held_high=hi,
                           cause="top band under the roof: roof datum D-39 and build-up b 0 .. 0.10 (T-680)")
            out.append(rec)
            continue

        if r["scope"] == "INTERIOR" and r["class"] in ("EXTERNAL_CORNER", "WALL_END") and st.startswith("ASSUMED"):
            if abs(float(r["owner_m"]) - G1[f]) > 1e-9:
                raise R.BeadRuleError("T-405 height is not the owner G1 for %s" % r["edge_id"])
            overhead = (ov_lo, ov_hi) if r["edge_id"] in ("GF-08#V60", "GF-08#V61") else None
            own, lo, hi, rule = R.exposed_vertical(G1[f], SOFFIT[f], overhead)
            rec["rule"] = rule
            if own is None:
                rec.update(status="HELD", held_low=lo, held_high=hi,
                           cause="under the HIDDEN outline of stair C quarter landing C-L1 (finished +%.6f, "
                                 "SOURCE_VERIFIED) minus build-up b 0 .. 0.10 (not printed) minus 0.16 (zone tag T16) "
                                 "minus GF-08 floor +1.00: soffit below G1 3.65" % land)
                if r["edge_id"] == "GF-08#V61":
                    rec["cause"] += "; V61 IS an arris: line 4AF is layer '2' HIDDEN (the landing's east edge "
                    rec["cause"] += "overhead), not a wall face (Checker T-405 open item closed)"
            else:
                rec.update(status=st, owner_m=own, dwg_low=lo, dwg_high=hi,
                           cause="owner G1 (exposed to the finished ceiling, OD-V3B-8 + heights rule); drawing "
                                 "G1 .. soffit %s (ceiling type not printed, O-P8-02)" % SOFFIT_STATUS[f])
        elif st in ("ASSUMED — OWNER-APPROVED", "DRAWING-CONFIRMED"):
            rec.update(status=st, owner_m=float(r["owner_m"]), dwg_low=float(r["dwg_m"] or r["owner_m"]),
                       dwg_high=float(r["dwg_m"] or r["owner_m"]), rule="R-T405 (unchanged)",
                       cause="T-405 value carried; exposed in full (opening heads below every ceiling; exterior faces open)")
        elif st == "NOT A BEAD":
            rec.update(status="NOT A BEAD", rule="R-T405-5/-6, Q-37 A", cause=r["note"][:140])
        else:
            rec.update(status="HELD", cause=(r["held_range"] or r["note"] or "")[:220], rule="R-T697-5")
            if r["edge_id"] == "CEIL#ALL":
                rec["cause"] = ("beam / bulkhead arrises above the finished ceiling: hidden (R-T697-1); a room "
                                "without a decor ceiling would expose them: CEILING_TYPE_PER_ROOM (O-P8-02)")

        if hosts:
            if rec["status"] in ("NOT A BEAD",):
                state, h = ("BOUND", hosts[0]) if len(hosts) == 1 else ("BINDING_OPEN", " | ".join(hosts))
            else:
                state, h = R.bind(hosts, index)
            rec.update(binding=state, host_line=h)
        else:
            rec.update(binding="NO_HOST")
        out.append(rec)

    # held parts of the exterior corners (T-172 / T-405 notes): HELD rows, never 0 and never inside the measured sum
    for eid, fl, host, lo, hi, cause in (
            ("EXT#GF-CONVEX-PLINTH", "GF", plinth_host, 2.10, 2.55, "3 pool-court convex corners below the F.F.L.: "
             "plinth 3 x 0.70 .. 0.85 (T-172), face line HELD"),
            ("EXT#1F-CONVEX-PARAPET-ENDS", "1F", ext_host["1F"], 0.0, 11.90, "1F parapet end parts not printed on the "
             "wavy sides: 0 .. 11.90 (T-172)"),
            ("EXT#GF-MOUTHS-STOP", "GF", ext_host["GF"], 0.0, 1.20, "passage-mouth stop-end parts 0 .. 1.20 (T-172)")):
        out.append({"edge_id": eid, "scope": "EXTERIOR", "floor": fl, "room": "facade", "class": "EXTERNAL_CORNER",
                    "count": "", "status": "HELD", "owner_m": "", "dwg_low": "", "dwg_high": "", "held_low": lo,
                    "held_high": hi, "binding": "BOUND", "host_line": host, "host_code": "", "host_class": "",
                    "owner_trade": "", "owning_line": "", "t405_owner_m": "", "t405_status": "note only",
                    "rule": "R-T697-5", "cause": cause, "source": "T-172 VERIFIED; T-405 ledger note"})

    for rec in out:
        h = rec["host_line"].split(" | ")[0] if rec["host_line"] else ""
        line = index.get(h) if h else None
        if rec.get("owning_line"):
            line = index.get(rec["owning_line"])
        if line:
            rec["host_code"], rec["host_class"] = line["item_code"], line["class"]
    R.check_ledger(out)
    return out, idx


def summarise(rows, idx):
    t405 = list(csv.DictReader(open(os.path.join(ROOT, SRC["t405"]), encoding="utf-8")))
    t405_in = sum(float(r["owner_m"]) for r in t405 if r["scope"] == "INTERIOR" and r["owner_status"] in R.STATUSES[:2])
    t405_ex = sum(float(r["owner_m"]) for r in t405 if r["scope"] == "EXTERIOR" and r["owner_status"] in R.STATUSES[:2])
    s = {"task": "T-697", "family": "B4-09 corner beads (m.l)", "candidate": idx["candidate_version"],
         "index_lines_sha": idx["inputs"]["lines"][:8], "inputs_sha8": {k: sha8(v) for k, v in SRC.items()},
         "rows": len(rows),
         "interior": R.totals([r for r in rows if r["scope"] == "INTERIOR"]),
         "exterior": R.totals([r for r in rows if r["scope"] == "EXTERIOR"]),
         "all": R.totals(rows),
         "t405_measured_m": {"interior": R.q4(t405_in), "exterior": R.q4(t405_ex)},
         "hosts": {}, "binding": {}}
    for r in rows:
        if r["status"] in R.STATUSES[:3] and r["host_line"]:
            k = r["host_line"]
            e = s["hosts"].setdefault(k, {"code": r["host_code"], "class": r["host_class"], "owner_m": 0.0,
                                          "held_rows": 0, "rows": 0})
            e["rows"] += 1
            if r["owner_m"] != "":
                e["owner_m"] = R.q4(e["owner_m"] + float(r["owner_m"]))
            else:
                e["held_rows"] += 1
        s["binding"][r["binding"]] = s["binding"].get(r["binding"], 0) + 1
    s["changes_vs_t405"] = [
        {"edge_id": r["edge_id"], "t405": r["t405_owner_m"] or r["t405_status"], "now": r["owner_m"] if r["owner_m"] != ""
         else ("%s .. %s" % (r["held_low"], r["held_high"]) if r["held_low"] != "" else r["status"]), "rule": r["rule"]}
        for r in rows if r["rule"] in ("R-T697-2", "R-T697-4", "R-T697-6") or r["edge_id"].startswith("EXT#GF-CONVEX-P")
        or r["edge_id"].startswith("EXT#1F-CONVEX-P") or r["edge_id"].startswith("EXT#GF-MOUTHS-S")]
    return s


FIELDS = ["edge_id", "scope", "floor", "room", "class", "count", "status", "owner_m", "dwg_low", "dwg_high", "held_low",
          "held_high", "binding", "host_line", "host_code", "host_class", "owner_trade", "owning_line", "t405_owner_m",
          "t405_status", "rule", "cause", "source"]


def render(rows, s):
    import io
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=FIELDS, lineterminator="\n")
    w.writeheader()
    for r in rows:
        w.writerow({k: r[k] for k in FIELDS})
    return buf.getvalue(), json.dumps(s, indent=1, sort_keys=True, ensure_ascii=False) + "\n"


def main(argv):
    rows, idx = build()
    s = summarise(rows, idx)
    csv_txt, js = render(rows, s)
    paths = {os.path.join(OUT, "T697_BEAD_LEDGER.csv"): csv_txt, os.path.join(OUT, "T697_SUMMARY.json"): js}
    if "--write" in argv:
        os.makedirs(OUT, exist_ok=True)
        for p, t in paths.items():
            open(p, "w", encoding="utf-8").write(t)
    if "--check" in argv:
        for p, t in paths.items():
            if open(p, encoding="utf-8").read() != t:
                print("STALE", p)
                return 1
        print("T-697 outputs reproduce")
    print(json.dumps({k: s[k] for k in ("interior", "exterior", "t405_measured_m", "binding")}, indent=1,
                     ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
