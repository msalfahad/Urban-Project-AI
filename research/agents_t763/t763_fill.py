"""T-763 F-04 PLASTER HEIGHT 4.34 / 4.04 + plaster, paint and corner-bead figures (DELIVERY MODE fix-row set; worker 2,
2026-11-13).

Reads the candidate line index ARCH_TAKEOFF_V3.0.81 (T-770 r1, agents/task-T-770 @ 20f6d37d = V3.0.78 + MAIN_FILL_ALL
wired) and writes out/FIX_ROWS.json + out/FIX_ROWS.md: one row per FIN.PLASTER, FIN.PAINT and FIN.PLASTER.BEAD line
that is still HELD (blank or ranged) after MAIN_FILL, plus the four RELEASED wet-room 'band above ceiling' lines that
still carry the superseded height (set HEIGHT_RESTATE, separable). FIN.WALL.TILE (MAIN_FILL_4 TILE_300) and the
floor beds (MAIN_FILL_1) are already filled: overlap with MAIN_FILL_ALL is asserted 0.

Height rule (owner 2026-11-13, DELIVERY_MODE s.3; rule record RULE_T763_PLASTER_HEIGHT.json, supersedes R-T556-1's
roof-scenario height): plaster height H = storey - slab 0.16 = 4.34 GF, 4.04 1F / 2F, 3.84 GF annex (+0.30 .. +4.30);
false ceiling = H - 0.90 (company default); wet-room tiles 3.00 m (owner 2026-11-13).
  wet room 'plaster' line   = render behind the tiles up to the false ceiling = run x Hc - doorway 2.20
                              (Hc = H - 0.90; in the annex Hc = 3.00 because H - 0.90 = 2.94 is below the owner's 3.00
                              tile top and a ceiling cannot sit below the tiling)
  wet room 'band' line      = run x (H - Hc)  (wall face above the false ceiling to the soffit; no opening reaches it)
  so render + band          = run x H - doorway, whatever the ceiling split.
Every other figure: the merged ledgers named in its basis. No drawing was opened in this run; no client data here.

  python3 -I research/agents_t763/t763_fill.py <LINE_INDEX_V3_0_81.json> [--check]
"""
from __future__ import annotations

import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out", "FIX_ROWS.json")
OUT_MD = os.path.join(HERE, "out", "FIX_ROWS.md")
T728 = os.path.join(HERE, "..", "agents_t728", "out", "T728_BEAD_RESTATEMENT.json")
INDEX_SHA16 = "9cbc24d921f82323"     # sha256[:16] of LINE_INDEX_V3_0_81.json at agents/task-T-770 20f6d37d
FAMILIES = ("FIN.PLASTER", "FIN.PAINT", "FIN.PLASTER.BEAD")
LABELS = ("MEASURED", "DRAWING-READ", "DEFAULT", "ESTIMATE", "SAFETY")

SLAB = 0.16
H = {"GF": 4.50 - SLAB, "1F": 4.20 - SLAB, "2F": 4.20 - SLAB, "ANNEX": 4.00 - SLAB}   # 4.34 / 4.04 / 4.04 / 3.84
CEIL_DROP = 0.90            # false ceiling = clear height - 0.90 (company default, owner 2026-11-13)
TILE_H = 3.00               # wet-room wall tiles 3.00 m from F.F.L. (owner 2026-11-13)
DOOR = 1.00 * 2.20          # doorway 1.00 x 2.20 (head default 2.20; same deduction as MAIN_FILL_4)
HEAD = 2.20                 # head default where none is printed
REVEAL_T = 0.15             # through-reveal depth: the 4 released THROUGH reveals of this candidate = perimeter x 0.15

r4 = lambda x: round(x + 0.0, 4)


def ceiling(zone: str) -> float:
    """false-ceiling height of a wet room: H - 0.90, never below the 3.00 m tile top (annex 3.84 - 0.90 = 2.94 -> 3.00)"""
    return max(H[zone] - CEIL_DROP, TILE_H)


def wet_render(run: float, zone: str, doors: int = 1) -> float:
    """render behind the tiles up to the false ceiling (the wet room's FIN.PLASTER 'plaster' line)"""
    if run is None or run <= 0:
        raise ValueError("wall run missing: a wet-room render line is never valued without its run")
    return run * ceiling(zone) - doors * DOOR


def wet_band(run: float, zone: str) -> float:
    """wall face above the false ceiling up to the soffit (FIN.PLASTER 'plaster band above ceiling')"""
    if run is None or run <= 0:
        raise ValueError("wall run missing: a band line is never valued without its run")
    return run * (H[zone] - ceiling(zone))


# Wall runs (lm) of the wet rooms: the ledger runs MAIN_FILL_4 used for the same rooms' tile lines (CANDIDATE_V3021_T335
# wall_run_lm), zone from the T-676 hold class (Q-54 B = annex under the +4.30 roof).
WET = {  # room: (zone, run_lm)
    "GF-R8496F0": ("ANNEX", 7.2), "GF-RA3AD49": ("ANNEX", 14.5), "GF-RB62B55": ("ANNEX", 7.5), "GF-RFAD3C4": ("ANNEX", 5.6),
    "GF-RD36087": ("GF", 4.9), "GF-RDF7D28": ("GF", 6.2), "GF-RD6F891": ("GF", 7.624665), "GF-RDBD4F9": ("GF", 8.243202),
    "GF-RB28769": ("GF", 6.809808), "GF-RF38DAF": ("GF", 7.414038),
    "1F-R8BDA49": ("1F", 9.0), "1F-RED23B8": ("1F", 7.6), "1F-R48AA46": ("1F", 9.0), "1F-R48CDA5": ("1F", 8.7),
    "1F-R26FA0D": ("1F", 16.94), "1F-R52AC05": ("1F", 6.54), "2F-RE83BED": ("2F", 9.7),
}
PANTRY = "GF-RC06FED"       # GF-07 pantry, tiled to the decor ceiling: released tile 32.3422 m2 at Hc 3.44 -> run 9.4018
PANTRY_TILE = 32.3422

# Bead hosts: element room key -> T-728 room; blank arrises valued by default (edge id: (lm, label, basis)).
BEAD_BLANK = {
    "A-GF-01#GF-01": (1.223795 + 2 * HEAD, "DEFAULT", "arch A-GF-01: head on the drawn arc 1.2238 (T-238 ARC, drawing) + 2 jambs x 2.20 head default"),
    "A-1F-01#1F-10": (1.00 + 2 * HEAD, "DEFAULT", "arch A-1F-01: width 1.00 (MAIN_FILL_2 basis) + 2 jambs x 2.20 head default"),
    "OPEN#ST-GF-OP020": (0.90 + 2 * HEAD, "DEFAULT", "doorless 0.90 opening OP-020: 0.90 head + 2 jambs x 2.20 head default"),
    "OPEN#GF-08-OP003": (2 * 3.65, "ESTIMATE", "open side OP-003 between columns: 2 column-jamb arrises x 3.65 (the room's measured arris height)"),
    "W03#IN": (6.6577 + 2 * (5.30 - 1.00), "DRAWING-READ", "curved W03 room side = the outside edge T-760 (merged): developed head 6.6577 + 2 jambs +1.00 .. +5.30"),
    "W17#IN": (3.29 + 2 * 3.00, "DRAWING-READ", "W17 room side: 3.29 x 3.00 (owner Q-76 A): head 3.29 + 2 jambs 3.00"),
}


def line_row(l, after, label, basis, set_name):
    return {"set": set_name, "line_id": l["line_id"], "item_code": l["item_code"], "unit": l["unit"],
            "element_id": l["element_id"],
            "before": {"class": l["class"], "net": l["measured_net"], "low": l["held_low"], "high": l["held_high"]},
            "after": {"class": "RELEASED", "net": r4(after)}, "label": label, "basis": basis}


def mid(l):
    return (l["held_low"] + l["held_high"]) / 2


def bead_hosts(t728_path):
    t = json.load(open(t728_path))
    hosts = {}
    for r in t["rows"]:
        hosts.setdefault(r["room"], []).append(r)
    return hosts


def bead_value(arrises):
    tot, parts, labels = 0.0, [], set()
    for a in arrises:
        if a["bead_state"] == "HELD_BLANK":
            if a["edge_id"] not in BEAD_BLANK:
                raise ValueError(f"blank arris {a['edge_id']} has no default: never 0")
            v, lab, b = BEAD_BLANK[a["edge_id"]]
            labels.add(lab); parts.append(f"{a['edge_id']} {v:.4f} ({b})")
        else:
            v = (a["low"] + a["high"]) / 2
            labels.add("MEASURED" if a["low"] == a["high"] else "ESTIMATE")
            parts.append(f"{a['edge_id']} {v:.4f}")
        tot += v
    label = "ESTIMATE" if "ESTIMATE" in labels else ("DEFAULT" if "DEFAULT" in labels else
                                                     ("DRAWING-READ" if "DRAWING-READ" in labels else "MEASURED"))
    return tot, label, "; ".join(parts)


def build(index_path, t728_path=T728):
    raw = open(index_path, "rb").read()
    sha = hashlib.sha256(raw).hexdigest()[:16]
    if sha != INDEX_SHA16:
        raise SystemExit(f"index sha {sha} != pinned {INDEX_SHA16}: rebuild on the newer index deliberately")
    idx = json.loads(raw)
    L = [l for l in idx["lines"] if l["class"] != "EXCLUDED"]
    by_eid = {l["element_id"]: l for l in L}
    rows = []

    # 1. wet rooms: render (plaster) and band lines
    for room, (zone, run) in WET.items():
        p = by_eid.get(f"{room}:plaster"); b = by_eid.get(f"{room}:plaster band above ceiling")
        Hc = ceiling(zone)
        if p and p["class"] == "HELD":
            rows.append(line_row(p, wet_render(run, zone), "DEFAULT",
                                 f"{room}: render behind tiles to the false ceiling: run {run} lm x Hc {Hc:.2f} - doorway 1.00 x 2.20 "
                                 f"(H {H[zone]:.2f} = storey - slab 0.16; Hc = max(H - 0.90, tile 3.00))", "PLASTER_WET"))
        if b and (b["class"] == "HELD" or b["measured_net"] is not None and room in ("GF-RB28769", "GF-RF38DAF", "1F-R26FA0D", "1F-R52AC05")):
            set_name = "PLASTER_BAND" if b["class"] == "HELD" else "HEIGHT_RESTATE"
            rows.append(line_row(b, wet_band(run, zone), "DEFAULT",
                                 f"{room}: band above the false ceiling: run {run} lm x (H {H[zone]:.2f} - Hc {Hc:.2f}) = x {H[zone] - Hc:.2f}"
                                 + ("; was run x 0.64 at the superseded height (R-T556-1 scenario)" if set_name == "HEIGHT_RESTATE" else ""),
                                 set_name))
    pb = by_eid[f"{PANTRY}:plaster band above ceiling"]
    run_p = PANTRY_TILE / (H["GF"] - CEIL_DROP)
    rows.append(line_row(pb, run_p * CEIL_DROP, "ESTIMATE",
                         f"GF-07 pantry: run = released tile {PANTRY_TILE} m2 / Hc 3.44 = {run_p:.4f} lm (openings ignored) x (4.34 - 3.44)",
                         "PLASTER_BAND"))

    # 2. stair-shaft and band-share lines: bounded by the shaft build-up / held contacts (T-173): midpoint
    for eid, code in (("HL:WALL_FINISH:ST_GF:PLASTER", "FIN.PLASTER"), ("HL:WALL_FINISH:ST_1F:PLASTER", "FIN.PLASTER"),
                      ("HL:WALL_FINISH:ST_2F:PLASTER", "FIN.PLASTER"), ("HL:WALL_FINISH:ST_GF:PAINT", "FIN.PAINT"),
                      ("HL:WALL_FINISH:ST_1F:PAINT", "FIN.PAINT"), ("HL:WALL_FINISH:ST_2F:PAINT", "FIN.PAINT")):
        l = by_eid[eid]
        rows.append(line_row(l, mid(l), "ESTIMATE",
                             f"stair shaft full exposed height (Q-72), T-173 bound {l['held_low']} .. {l['held_high']}: midpoint "
                             "(floor build-up 0 .. 0.10, held window / passage heads; paint = plaster, no false ceiling in the shaft)",
                             "SHAFT"))
    for l in L:
        if l["class"] == "HELD" and str(l["element_id"]).startswith(("PLASTER-BAND@", "PAINT-BAND@")):
            rows.append(line_row(l, mid(l), "ESTIMATE",
                                 f"band share bound {l['held_low']} .. {l['held_high']} (width {l['held_high'] - l['held_low']:.3f} m2, "
                                 "below 1 % of the family): midpoint", "BAND_SHARE"))

    # 3. through-reveal plaster returns (blank): (2 jambs + head) x 0.15
    for eid, w, head_len, why in (("GF-REVEAL-A-GF-01:THROUGH:JAMBS_HEAD:HELD", 1.00, 1.223795, "arch: drawn arc 1.2238 as head"),
                                  ("1F-REVEAL-A-1F-01:THROUGH:JAMBS_HEAD:HELD", 1.00, 1.00, "arch drawn on no view: straight 1.00 head"),
                                  ("GF-REVEAL-D-GF-15:THROUGH:JAMBS_HEAD:HELD", 1.00, 1.00, "door width 1.00 (T-602 drawn)")):
        l = by_eid[eid]
        perim = 2 * HEAD + head_len
        rows.append(line_row(l, perim * REVEAL_T, "DEFAULT",
                             f"{eid.split(':')[0]}: (2 x 2.20 head default + {head_len:.4f}) = {perim:.4f} lm x depth 0.15 "
                             f"(as the released THROUGH reveals); {why}", "REVEAL"))

    # 4. corner beads: one line per host, its own arrises (T-728 restatement, merged), blank arrises by default
    hosts = bead_hosts(t728_path)
    for l in L:
        if l["item_code"] == "FIN.PLASTER.BEAD" and l["class"] == "HELD":
            key = l["element_id"].split("HL:WALL_FINISH:")[1].replace("#BEAD", "").replace("_", "-")
            arr = hosts.get(key)
            if not arr:
                raise ValueError(f"no T-728 arrises for {l['element_id']}")
            v, lab, basis = bead_value(arr)
            if l["held_low"] is not None and abs(sum((a['low'] or 0) for a in arr if a['bead_state'] != 'HELD_BLANK') - l["held_low"]) > 0.01:
                raise ValueError(f"{l['element_id']}: T-728 arris sum differs from the line's low bound (stale ledger)")
            rows.append(line_row(l, v, lab, f"{key}: {len(arr)} arris rows: {basis}", "BEAD"))

    # every held line of the families is covered, nothing twice
    ids = [r["line_id"] for r in rows]
    assert len(ids) == len(set(ids)), "a line written twice"
    held_left = [l["line_id"] for l in L if l["item_code"] in FAMILIES and l["class"] == "HELD" and l["line_id"] not in ids]
    assert not held_left, f"held lines left without a figure: {held_left}"
    assert all(r["label"] in LABELS and r["basis"] and r["after"]["net"] > 0 for r in rows)
    return sha, idx.get("candidate_version"), rows, L


def summary(rows, L):
    s = {}
    for fam in FAMILIES:
        fam_lines = [l for l in L if l["item_code"] == fam]
        frows = [r for r in rows if r["item_code"] == fam]
        held = [l for l in fam_lines if l["class"] == "HELD"]
        rel_before = sum(l["measured_net"] or 0 for l in fam_lines if l["class"] == "RELEASED")
        moved = {r["line_id"]: r for r in frows}
        rel_after = sum((moved[l["line_id"]]["after"]["net"] if l["line_id"] in moved else (l["measured_net"] or 0))
                        for l in fam_lines if l["class"] in ("RELEASED", "HELD"))
        labels = {}
        for r in frows:
            labels[r["label"]] = labels.get(r["label"], 0) + 1
        s[fam] = {"lines": len(fam_lines), "held_before": len(held),
                  "blank_before": sum(1 for l in held if l["held_low"] is None),
                  "held_low_before": round(sum(l["held_low"] or 0 for l in held), 1),
                  "held_high_before": round(sum(l["held_high"] or 0 for l in held), 1),
                  "released_before": round(rel_before, 1), "held_after": 0, "released_after": round(rel_after, 1),
                  "rows": len(frows), "labels": labels}
    return s


def write(index_path):
    sha, ver, rows, L = build(index_path)
    out = {"schema": "T763_FIX_ROWS_V1", "candidate_version": ver, "index_sha16": sha,
           "base": "agents/task-T-770 20f6d37d (V3.0.81 = V3.0.78 + MAIN_FILL_ALL)",
           "overlap_with_MAIN_FILL_ALL": 0, "summary": summary(rows, L), "rows": rows}
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    text = json.dumps(out, indent=1, sort_keys=True) + "\n"
    md = ["# T-763 fix rows (DEFAULT / ESTIMATE / DRAWING-READ / MEASURED; never verified until the Checker re-measures)", "",
          "| family | lines | held before (blank) | held range before | released before | released after |", "|---|---|---|---|---|---|"]
    for k, v in out["summary"].items():
        md.append(f"| {k} | {v['lines']} | {v['held_before']} ({v['blank_before']}) | {v['held_low_before']} .. {v['held_high_before']} | "
                  f"{v['released_before']} | {v['released_after']} |")
    md += ["", "| set | line | element | before | after | label | basis |", "|---|---|---|---|---|---|---|"]
    for r in rows:
        b = r["before"]
        bb = f"{b['class']} {b['net'] if b['net'] is not None else ''}{'' if b['low'] is None else str(b['low']) + '..' + str(b['high'])}"
        md.append(f"| {r['set']} | {r['line_id'][:10]} | {r['element_id']} | {bb} | {r['after']['net']} | {r['label']} | {r['basis']} |")
    return text, "\n".join(md) + "\n", out


def main(argv):
    if len(argv) < 2:
        raise SystemExit(__doc__)
    text, md, out = write(argv[1])
    if "--check" in argv:
        if open(OUT).read() != text or open(OUT_MD).read() != md:
            raise SystemExit("FIX_ROWS is stale: rerun without --check")
        print(f"check OK {len(out['rows'])} rows")
        return
    open(OUT, "w").write(text); open(OUT_MD, "w").write(md)
    print(json.dumps(out["summary"], indent=1))


if __name__ == "__main__":
    main(sys.argv)
