"""T-108: the development villa's block walls through MASONRY_AREA_V1 (engine/source/masonry_area_v1.py, not wired).

Repository inputs only (no drawing is read here; the drawing work is in the merged ledgers it cites):
  research/agents_t143/T143_BLOCK_BY_WALL_RUN.csv   wall runs: Q-69 B physical length, architectural run, thickness,
                                                    block type + source, and the member above each sampled piece
                                                    (mark, schedule depth, register status) from the structural
                                                    roof-slab plans laid on the architectural plans (T-143, T-110)
  research/agents_t143/T143_TOTALS_VS_FREELANCER.csv  the freelancer's block rows by floor / section (gross, deduction)
  research/agents_t175/T175_OPENING_HOSTS.csv       opening -> host run (T-175, census r3 of T-198 applies: no block
                                                    m2 change, DOWNSTREAM_T198.csv C1-C5)
  research/agents_t175/T175_NET_BLOCK_BY_WALL.csv   T-175's nets, compared row by row
The module re-derives every height from the storey height and the member depth (Q-60 A) instead of taking the T-143
height, so this run is an independent recomputation of T-143's arithmetic, not of its drawing reading.
Usage: python3 -I research/agents_t108/alsenan_t108.py [--check]"""
from __future__ import annotations

import argparse
import csv
import io
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "research/agents_t175"))
from engine.source import masonry_area_v1 as M          # noqa: E402
import alsenan_t175 as T175                             # noqa: E402

DC, AOA, HELD = M.DC, M.AOA, M.HELD
FLOORS = ("GF", "1F", "2F")
# storey heights, slab top to slab top (T-143 method step 4; T-112 section reading on sheet 10, FFL marks):
STOREYS = {"GF": {"floor_to_floor_m": 4.50, "status": DC, "source": "+1.00 -> +5.50 (sheet 10 / elevations)"},
           "GF annex": {"floor_to_floor_m": 4.00, "status": HELD,
                        "source": "marks +0.30 -> +4.30; annex datum HELD (owner Q-54 B): heights PROVISIONAL"},
           "1F": {"floor_to_floor_m": 4.20, "status": DC, "source": "+5.50 -> +9.70"},
           "2F": {"floor_to_floor_m": 4.20, "status": DC, "source": "+9.70 -> +13.90"}}
TYPE_STATUS = {"ASSUMED": AOA, "PROVISIONAL": HELD, "HELD": HELD}
# The three free-end doorways inside a run are not on the wall band, so T-143 sampled no member over them (coverage
# < 0.8). Own read, T-108 (ST7757 dxf.dxf on the roof-slab plans, translation from the column outlines: GF 30 / 30
# columns at (202.33, 841.64) m, 1F 20 / 20 at (208.46, 841.64) m, residual <= 0.004 m; probe script in the scratchpad):
COVERAGE_READ = {
    "GF-W27": "over D-GF-02 (0.874 m gap): no beam edge parallel within 0.70 m, one crossing line at the node (0.053 m), "
              "slab rebar text only, no T tag: slab 0.16 (ST p.8 note 18), same member as the sampled piece",
    "GF-W29": "over D-GF-10 (0.85 m gap): no beam edge parallel within 0.70 m, one crossing line at the node (0.003 m), "
              "slab rebar text only, no T tag: slab 0.16, same member as the sampled piece",
    "1F-W12": "over D-1F-03 (1.089 m gap): the B4 band (layer 1 edges at -0.124 / +0.076 m, 0.20 wide) continues over "
              "0.988 m of the gap; crossing line at the node 0.101 m: B4 20 x 50, same member as the sampled piece",
    "1F-W25": "NOT read: concave bay stubs (0.537 m physical, 0.168 m sampled under CB12); for the Checker"}
TIE_BEAM_ROWS = ("GF-W08", "GF-W09", "GF-W13", "GF-W14")   # ST p.8 note 19: lift tie beam at 3.00 m, size not printed


def parse_pieces(s):
    """T-143 'members_above' -> [{length_m, member}], and whether the run is on the annex datum."""
    if not s or s.strip() == "not bound":
        return [], False
    pieces, annex = [], "(annex:" in s
    for part in re.split(r"; (?=[^;]*? BM-\S+ b |slab |DOME_OPENING|BEAM_OR_COLUMN)", s):
        m = re.search(r": (\d+\.\d+) m(?: -> h|$)", part)
        if not m:
            continue
        ln = float(m.group(1))
        if part.startswith("slab "):
            t = float(re.match(r"slab \S+ t (\d+\.\d+)", part).group(1))
            mem = {"kind": "SLAB", "mark": part.split()[1], "depth_m": t, "status": DC}
        elif part.startswith(("DOME_OPENING", "BEAM_OR_COLUMN")):
            mem = {"kind": "NONE", "status": HELD, "mark": part.split()[0]}
        else:
            st = re.search(r"\[(\w+)\]", part).group(1)
            mark = part.split(" BM-")[0]
            if st == "CALCULATED":
                d = float(re.search(r" h (\d+(?:\.\d+)?) \[", part).group(1))
                mem = {"kind": "BEAM", "mark": mark, "depth_m": d, "status": DC}
            else:
                mem = {"kind": "BEAM", "mark": mark, "depth_m": None, "status": HELD,
                       "why": f"register {st} (T-110: {part.split('[')[1].split(']: ', 1)[-1][:90]})"}
        pieces.append({"length_m": ln, "member": mem, "t143_h": (re.search(r"-> h (\d+\.\d+)$", part) or [None, None])[1]})
    return pieces, annex


def openings_by_row():
    hosts = list(csv.DictReader(open(ROOT / "research/agents_t175/T175_OPENING_HOSTS.csv", encoding="utf-8")))
    lrows, bearing = T175.lintel_rows()
    by_row = {}
    for h in hosts:
        if h["ID"] in ("W02", "W03", "W17", "U-01", "D-GF-15", "P-GF-02", "P-GF-03", "P-GF-04", "P-GF-05"):
            continue                                    # glazed lines / no building wall: no masonry (T-175 s.2)
        if h["IN_GROSS"] != "YES" or not h["HOST_ROW"]:
            continue
        kind = T175.kind_of(h)
        w = float(h["WIDTH_M"]) if h["WIDTH_M"] else None
        ws = DC if (w is not None and not h["WIDTH_LO_M"] and not h["HOLD_CAUSE"]) else HELD
        hv = float(h["HEIGHT_M"]) if h["HEIGHT_M"] else None
        hs = {"PRINTED": DC, "ASSUMED": AOA}.get(h["HEIGHT_STATUS_T150"], HELD) if hv is not None else HELD
        op = {"id": h["ID"], "kind": kind, "width_m": w, "width_status": ws, "height_m": hv, "height_status": hs,
              "sill_m": float(h["SILL_ABOVE_FFL_M"]) if h["SILL_ABOVE_FFL_M"] else 0.0, "in_gross": True,
              "frame": kind in ("DOOR", "WINDOW", "SHAFT", "GATE"),
              "faces": (T175.face(h["SIDE_A"]), T175.face(h["SIDE_B"])),
              "wet_side": any(T175.face(s) == "WALL_TILE" for s in (h["SIDE_A"], h["SIDE_B"])),
              "lintel": T175.lintel_for(w, lrows, bearing)}
        by_row.setdefault(h["HOST_ROW"], []).append(op)
    return by_row


def build():
    rows = list(csv.DictReader(open(ROOT / "research/agents_t143/T143_BLOCK_BY_WALL_RUN.csv", encoding="utf-8")))
    t175 = {r["row_id"]: r for r in csv.DictReader(open(ROOT / "research/agents_t175/T175_NET_BLOCK_BY_WALL.csv",
                                                        encoding="utf-8"))}
    ops = openings_by_row()
    out, hchecks = [], []
    for r in rows:
        pieces, annex = parse_pieces(r["members_above"])
        storey = STOREYS["GF annex" if annex else r["floor"]]
        bt = r["block_type"] if r["block_type"] in ("WHITE", "BLACK") else None
        held_row = r["status"] == "HELD" and not pieces or bt is None
        wall = {"id": r["row_id"], "floor": r["floor"], "group": r["group"], "t_m": float(r["t_m"]),
                "block_type": bt, "type_status": TYPE_STATUS.get(r["type_status"], HELD) if bt else HELD,
                "physical_length_m": float(r["L2a_q69_physical_m"]),
                "length_status": HELD if held_row else DC,
                "arch_length_m": float(r["L1_arch_run_m"]),
                "pieces": [] if bt is None else [{"length_m": p["length_m"], "member": p["member"]} for p in pieces]}
        # a row whose thickness / material is HELD in T-103 (GF-H01 0.40 band, GF-H02) gets no gross at all
        x = M.wall_ledger(wall, storey, ops.get(r["row_id"], []), printed_lintel_schedule=True)
        if r["row_id"] in TIE_BEAM_ROWS:                # T-143: gross PROVISIONAL, the tie-beam strip not deducted
            x["net_status"], x["net_m2"], x["net_m3"] = HELD, None, None
            x["gross_status"] = HELD
            x["hold_note"] = "ST p.8 note 19 lift tie beam (size not printed): its strip is not deducted"
        for p_in, p_out in zip(pieces, x["gross"]["pieces"]):
            if p_in["t143_h"] is not None and p_out["height_m"] is not None:
                hchecks.append((r["row_id"], float(p_in["t143_h"]), p_out["height_m"]))
        x["t143_gross"] = float(r["gross_m2_q69_physical"]) if r["gross_m2_q69_physical"] not in ("", "HELD") else None
        t5 = t175.get(r["row_id"], {})
        x["t175_net"] = float(t5["net_m2_on_t143_gross"]) if t5.get("net_m2_on_t143_gross") else None
        x["t175_status"] = t5.get("s5_status")
        x["storey_source"] = storey["source"]
        out.append(x)
    return out, hchecks


def r3(v):
    return "" if v is None else f"{v:.3f}"


def by_wall_csv(L):
    o = io.StringIO()
    w = csv.writer(o, lineterminator="\n")
    w.writerow(["row_id", "floor", "group", "t_m", "block_type", "type_status", "physical_length_m", "held_length_m",
                "height_weighted_m", "coverage", "gross_m2", "gross_status", "t143_gross_m2", "d_gross_m2",
                "deducted_m2", "held_openings", "net_m2", "net_status", "net_candidate_m2 (HELD: not a quantity)",
                "net_bounds_m2", "t175_net_m2", "t175_status", "d_net_vs_t175_m2", "net_m3",
                "white_units_62.5x25", "white_units_60x20", "units_status", "atab", "flags", "hold_reason"])
    for x in L:
        g = x["gross"]
        u = x["units"]
        u1 = u.get("62.5x25", {}).get("units")
        u2 = u.get("60x20", {}).get("units")
        ust = next(iter(u.values()))["status"]
        b = x["net_bounds_m2"]
        dg = (x["gross_m2"] - x["t143_gross"]) if (x["gross_m2"] is not None and x["t143_gross"] is not None) else None
        dn = (x["net_candidate_m2"] - x["t175_net"]) if (x["net_candidate_m2"] is not None and x["t175_net"] is not None) else None
        at = sorted({a["status"] for a in x["atab"]})
        why = x.get("hold_note") or g.get("why") or ""
        if x["held_openings"]:
            why = (why + "; " if why else "") + "held opening(s): " + ";".join(x["held_openings"])
        w.writerow([x["wall"], x["floor"], x["group"], x["t_m"], x["block_type"] or "-", x["type_status"],
                    r3(g["physical_length_m"]), r3(g.get("held_length_m")), r3(g.get("height_weighted_m")),
                    r3(g.get("coverage")), r3(x["gross_m2"]), x["gross_status"], r3(x["t143_gross"]), r3(dg),
                    r3(x["deducted_m2"]), ";".join(x["held_openings"]), r3(x["net_m2"]), x["net_status"],
                    r3(x["net_candidate_m2"]), f"{r3(b[0])} .. {r3(b[1])}" if b else "", r3(x["t175_net"]),
                    x["t175_status"] or "", r3(dn), r3(x["net_m3"]), r3(u1), r3(u2), ust,
                    ";".join(at) if at else "", ";".join(g.get("flags") or []), why[:220]])
    return o.getvalue()


def totals_csv(L):
    o = io.StringIO()
    w = csv.writer(o, lineterminator="\n")
    w.writerow(["floor", "block_type", "t_m", "walls", "gross_known_m2", "held_length_m", "net_DC_m2", "net_AOA_m2",
                "net_m3_DC_plus_AOA", "walls_net_held", "net_candidate_on_held_m2 (not a quantity)",
                "white_units_62.5x25", "white_units_60x20"])
    agg = M.totals(L)
    for k in sorted(agg, key=lambda k: (FLOORS.index(k[0]), str(k[1]), k[2])):
        a = agg[k]
        nb = a["net_by_status"]
        wu = a["white_units"]
        w.writerow([k[0], k[1] or "-", f"{k[2]:.2f}", a["walls"], r3(a["gross_known_m2"]), r3(a["held_length_m"]),
                    r3(nb.get(DC, {}).get("m2", 0.0)), r3(nb.get(AOA, {}).get("m2", 0.0)),
                    r3(sum(v["m3"] for v in nb.values())), a["walls_net_held"], r3(a["net_candidate_on_held_m2"]),
                    r3(sum(wu.get("62.5x25", {}).values())) if wu else "", r3(sum(wu.get("60x20", {}).values())) if wu else ""])
    return o.getvalue()


def vs_freelancer_csv(L):
    fl = {(r["floor"], r["freelancer_section"]): r for r in
          csv.DictReader(open(ROOT / "research/agents_t143/T143_TOTALS_VS_FREELANCER.csv", encoding="utf-8"))}
    o = io.StringIO()
    w = csv.writer(o, lineterminator="\n")
    w.writerow(["floor", "section", "walls", "engine_gross_known_m2", "engine_held_length_m", "fl_gross_m2",
                "d_gross_m2", "d_gross_pct", "engine_net_established_m2 (DC+AOA, walls with a net)",
                "same_walls_gross_m2", "engine_walls_net_held", "fl_deduction_m2", "fl_net_m2", "like_for_like"])
    for (f, sec), r in sorted(fl.items(), key=lambda kv: (FLOORS.index(kv[0][0]), kv[0][1])):
        grp = "EXTERNAL" if sec == "EXTERNAL" else "INTERNAL"
        t = None if sec == "EXTERNAL" else float(sec.split()[-1])
        W = [x for x in L if x["floor"] == f and x["group"] == grp and (t is None or abs(x["t_m"] - t) < 1e-6)]
        gk = sum(x["gross_m2"] or 0 for x in W)
        hl = sum(x["gross"].get("held_length_m") or 0 for x in W)
        net = [x for x in W if x["net_m2"] is not None]
        fg = float(r["freelancer_gross_m2"])
        lfl = "NO: held length > 0 (held is missing, not 0)" if hl > 1e-6 else "gross yes; net only on walls with a net"
        w.writerow([f, sec, len(W), r3(gk), r3(hl), r3(fg), r3(gk - fg), f"{(gk - fg) / fg * 100:+.1f} %",
                    r3(sum(x["net_m2"] for x in net)), r3(sum(x["gross_m2"] for x in net)),
                    len(W) - len(net), r["freelancer_deduction_m2"], r["freelancer_net_m2"], lfl])
    return o.getvalue()


def summary(L, hchecks):
    s = {"method": M.METHOD, "rules": list(M.RULES), "inputs": ["T143_BLOCK_BY_WALL_RUN.csv",
         "T175_OPENING_HOSTS.csv", "T175_NET_BLOCK_BY_WALL.csv", "T143_TOTALS_VS_FREELANCER.csv"],
         "printed_lintel_schedule": "ST7757.pdf p.13 LINTEL SCHEDULE (S8.6): atab NOT APPLICABLE on every opening",
         "height_recomputation": {"pieces": len(hchecks),
                                  "max_abs_diff_vs_t143_m": round(max(abs(a - b) for _, a, b in hchecks), 6)}}
    dg = [abs(x["gross_m2"] - x["t143_gross"]) for x in L if x["gross_m2"] is not None and x["t143_gross"] is not None]
    dn = [abs(x["net_candidate_m2"] - x["t175_net"]) for x in L
          if x["net_candidate_m2"] is not None and x["t175_net"] is not None]
    s["gross_vs_t143"] = {"rows": len(dg), "max_abs_diff_m2": round(max(dg), 3), "sum_abs_diff_m2": round(sum(dg), 3)}
    s["net_vs_t175"] = {"rows": len(dn), "max_abs_diff_m2": round(max(dn), 3), "sum_abs_diff_m2": round(sum(dn), 3)}
    s["status_mismatch_vs_t175"] = sorted(x["wall"] for x in L if x["t175_status"] and
                                          ((x["net_m2"] is None) != (x["t175_status"] == HELD or x["t175_net"] is None)))
    s["low_height_coverage_resolved_by_own_read"] = COVERAGE_READ
    s["low_height_coverage"] = sorted(x["wall"] for x in L if "LOW_HEIGHT_COVERAGE" in (x["gross"].get("flags") or []))
    for fl in FLOORS + ("ALL",):
        W = [x for x in L if fl == "ALL" or x["floor"] == fl]
        net = [x for x in W if x["net_m2"] is not None]
        by = {}
        for x in net:
            e = by.setdefault(x["net_status"], {"walls": 0, "m2": 0.0, "m3": 0.0})
            e["walls"] += 1
            e["m2"] += x["net_m2"]
            e["m3"] += x["net_m3"]
        wu = {}
        for x in net:
            for f, u in x["units"].items():
                if u.get("units") is not None:
                    wu[f] = wu.get(f, 0.0) + u["units"]
        gbs = {}
        for x in W:
            if x["gross_m2"] is not None:
                gbs[x["gross_status"]] = gbs.get(x["gross_status"], 0.0) + x["gross_m2"]
        s[fl] = {"walls": len(W), "gross_known_m2": round(sum(x["gross_m2"] or 0 for x in W), 3),
                 "gross_known_by_status_m2 (HELD = known pieces of held / provisional walls)":
                     {k: round(v, 3) for k, v in sorted(gbs.items())},
                 "gross_m3_known": round(sum(x["gross_m3"] or 0 for x in W), 3),
                 "held_length_m": round(sum(x["gross"].get("held_length_m") or 0 for x in W), 3),
                 "walls_with_net": len(net),
                 "net_by_status": {k: {"walls": v["walls"], "m2": round(v["m2"], 3), "m3": round(v["m3"], 3)}
                                   for k, v in sorted(by.items())},
                 "walls_net_held": len(W) - len(net),
                 "net_candidate_on_held_walls_m2 (not a quantity)": round(
                     sum(x["net_candidate_m2"] or 0 for x in W if x["net_m2"] is None), 3),
                 "white_units_installed_on_established_net": {k: round(v, 1) for k, v in sorted(wu.items())},
                 "white_net_held_walls": sum(1 for x in W if x["block_type"] == "WHITE" and x["net_m2"] is None)}
    s["held_scope_outside_the_rows"] = [
        "P-1F-01 masonry above the S8.6 lintel (black 0.15), in no run: 0 .. 4.992 m2 bounds, HELD on the head (T-198 C2)",
        "pool-court east-wall piers 0.632 + 0.247 m and the north pier (T-154 / T-175): built, in no T-143 row, height not read: HELD",
        "masonry above / below the glazing of W02 (GF-W11), W03 (GF-W37), W17 (1F-W25): Q-69 B item (4), HELD on heads (T-144; T-201 READY)",
        "roof parapets 104.25 lm (+4.30 m thickness held) and street fence 8.20 lm: material HELD (owner Q-65 C), heights from ST p.14 details not measured here",
        "T-stem overlap of centreline runs 2.70 m3 (T-143, measured part, gross basis): to deduct for a physical volume; not split per row, not re-derived here"]
    return s


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args(argv)
    L, hc = build()
    files = {"T108_BY_WALL.csv": by_wall_csv(L), "T108_TOTALS_BY_FLOOR_TYPE_T.csv": totals_csv(L),
             "T108_VS_FREELANCER_BY_SECTION.csv": vs_freelancer_csv(L),
             "summary.json": json.dumps(summary(L, hc), indent=1, ensure_ascii=False) + "\n"}
    if a.check:
        bad = [n for n, t in files.items() if (HERE / n).read_text(encoding="utf-8") != t]
        print("CHECK", "PASS" if not bad else f"FAIL {bad}")
        return 0 if not bad else 1
    for n, t in files.items():
        (HERE / n).write_text(t, encoding="utf-8")
    print(files["summary.json"][:4000])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
