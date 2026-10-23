"""T-176 runner for the development villa (Alsenan): procurement after the NET installed blockwork m2.

Input (merged, Checker-verified): research/agents_t108/T108_BY_WALL.csv (MASONRY_AREA_V1 r2, T-108 r2 MERGED 01eeafd0)
and research/agents_t175/T175_OPENING_HOSTS.csv (opening sizes, only for the course-grid evidence), research/agents_t117/
D12_CONFLICT_RUNS.csv (D-12 flags). Nothing is re-derived:
the net m2 and its status are read as merged.

Outputs: BLOCK_PROCUREMENT_BY_WALL.csv (one row per wall run), BLOCK_PROCUREMENT_BY_TYPE.csv (type x thickness x
status), WASTE_SENSITIVITY.csv (procurement at named parameter values, NOT a released quantity), summary.json.
`--check` rebuilds in memory and compares with the committed files (exit 0 / 1)."""
from __future__ import annotations

import csv
import io
import json
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
RES = HERE.parent
sys.path.insert(0, str(HERE))
import block_procurement_v1 as B                                          # noqa: E402

PRODUCT_OF = {"BLACK": ("BLACK_40x20",), "WHITE": ("WHITE_62.5x25", "WHITE_60x20")}
SENSITIVITY = (  # named parameter values for the sensitivity table: NOT approved fallbacks, NOT released
    ("cutting 0.03 + breakage 0.00", 0.03, 0.00, "illustrative low end of the owner skill range 3-8 % (DEFAULT/CONFIRM)"),
    ("cutting 0.05 + breakage 0.00", 0.05, 0.00, "owner skill quantity-takeoff-rules 2.1 DEFAULT/CONFIRM (not approved)"),
    ("cutting 0.08 + breakage 0.00", 0.08, 0.00, "illustrative high end of the owner skill range 3-8 % (DEFAULT/CONFIRM)"),
)


def f(x):
    return float(x) if x not in ("", None) else None


def r3(v):
    return "" if v is None else f"{v:.3f}"


def r4(v):
    return "" if v is None else f"{v:.4f}"


def load():
    walls = list(csv.DictReader(open(RES / "agents_t108" / "T108_BY_WALL.csv", encoding="utf-8")))
    hosts = defaultdict(list)
    for o in csv.DictReader(open(RES / "agents_t175" / "T175_OPENING_HOSTS.csv", encoding="utf-8")):
        hosts[o["HOST_ROW"]].append(o)
    d12 = {}
    for c in csv.DictReader(open(RES / "agents_t117" / "D12_CONFLICT_RUNS.csv", encoding="utf-8")):
        for hr in (x.strip() for x in c["hand_rows"].split("+")):
            d12[hr] = f"D-12 CONFLICT: drawn {c['t_drawn_m']} vs column width {c['t_by_note_s2_m']} (ST p.8 note 20); never chosen"
    return walls, hosts, d12


def grid_openings(wall, hosts):
    """Openings for the course-grid evidence: only when their w x h reproduces the merged deduction (else n/a)."""
    ded = f(wall["deducted_m2"]) or 0.0
    if ded < 1e-6:
        return []
    ops = []
    for o in hosts.get(wall["row_id"], []):
        w, h = f(o["WIDTH_M"]), f(o["HEIGHT_M"])
        if w is None or h is None:
            return None
        ops.append((w, h))
    return ops if abs(sum(w * h for w, h in ops) - ded) < 0.005 else None


def build(p=None):
    p = p or B.params()
    walls, hosts, d12 = load()
    rows, agg = [], defaultdict(lambda: defaultdict(float))
    census = defaultdict(float)
    for w in walls:
        bt, t = w["block_type"], f(w["t_m"])
        census[f"{t:.2f}"] += f(w["gross_m2"]) or 0.0
        net, nst = f(w["net_m2"]), w["net_status"]
        L, H = f(w["physical_length_m"]), f(w["height_weighted_m"])
        prods = PRODUCT_OF.get(bt, (None,))
        for prod in prods:
            row = {"row_id": w["row_id"], "floor": w["floor"], "block_type": bt, "t_m": f"{t:.2f}", "product": prod or "",
                   "gross_m2 (MASONRY_AREA_V1 r2)": w["gross_m2"], "net_m2 (MASONRY_AREA_V1 r2)": w["net_m2"],
                   "net_status": nst, "d12_flag": d12.get(w["row_id"], "")}
            if prod is None:
                row.update(units_status=B.HELD, why="block type not established (Q-65 C / no note) or thickness not a product")
                rows.append(row)
                agg[(bt, f"{t:.2f}", "-", B.HELD, nst)]["walls"] += 1
                continue
            inst = B.installed_units(net, prod, t, nst)
            proc = B.procurement_units(inst, p)
            mo = B.mortar(net, nst, prod, t, p)
            ops = grid_openings(w, hosts) if inst["units"] is not None and L and H else None
            grid = B.grid_units(L, H, prod, ops) if ops is not None else None
            tol = B.edge_tolerance_m3(L, H, prod, t) if (mo["wet_m3"] is not None) else None
            row.update({
                "units_per_m2": r4(inst.get("per_m2")), "installed_units": r3(inst["units"]),
                "installed_status": inst["status"], "joint_basis": inst.get("joint", ""),
                "procurement_units": "" if proc["units"] is None else str(proc["units"]),
                "procurement_status": proc["status"], "procurement_why": proc.get("why", ""),
                "grid_units (evidence, no reuse)": "" if grid is None else str(grid),
                "grid_implied_cutting": "" if grid is None else f"{grid / inst['units'] - 1:.4f}",
                "mortar_wet_m3": r4(mo["wet_m3"]), "mortar_status": mo["wet_status"],
                "mortar_edge_tolerance_m3 (not added)": r4(tol),
                "cement_bags": r3(mo["cement_bags"]), "sand_m3": r4(mo["sand_m3"]),
                "cement_sand_status": mo["cement_sand_status"], "why": "; ".join(mo["why"]) or inst.get("why", ""),
            })
            rows.append(row)
            st = inst["status"]
            a = agg[(bt, f"{t:.2f}", prod, st, nst)]
            a["walls"] += 1
            if net is not None and st not in (B.HELD, B.UNKNOWN):
                a["net_m2"] += net
                a["installed_units"] += inst["units"]
                a["mortar_wet_m3"] += mo["wet_m3"] or 0.0
                a["edge_tol_m3"] += tol or 0.0
                if grid is not None:
                    a["grid_units"] += grid
                    a["grid_base_units"] += inst["units"]
            else:
                a["gross_m2_on_held_walls"] += f(w["gross_m2"]) or 0.0
    return rows, agg, census, p


def sensitivity(agg):
    out = []
    for name, cw, br, src in SENSITIVITY:
        p = B.params(cutting_waste=(cw, src), breakage=(br, src))
        for (bt, t, prod, st, nst), a in sorted(agg.items()):
            if prod == "-" or st in (B.HELD, B.UNKNOWN) or not a["installed_units"]:
                continue
            pr = B.procurement_units({"units": a["installed_units"], "status": st}, p)
            pal = B.pallets(pr["units"], prod, float(t)) if bt == "WHITE" else {"pallets": None}
            out.append({"parameter_set": name, "parameter_source": src, "block_type": bt, "t_m": t, "product": prod,
                        "net_status": nst, "status": st, "installed_units": r3(a["installed_units"]),
                        "ordered_units (NOT RELEASED)": str(pr["units"]),
                        "white_pallets (NOT RELEASED)": "" if pal["pallets"] is None else str(pal["pallets"])})
    return out


def summarize(rows, agg, census, p):
    by_type = []
    for (bt, t, prod, st, nst), a in sorted(agg.items()):
        by_type.append({"block_type": bt, "t_m": t, "product": prod, "net_status": nst, "units_status": st, "walls": int(a["walls"]),
                        "net_m2": r3(a["net_m2"]), "installed_units": r3(a["installed_units"]),
                        "procurement_units": "HELD (cutting / breakage not established)",
                        "mortar_wet_m3": r4(a["mortar_wet_m3"]) if bt == "BLACK" else ("HELD (thin-bed adhesive)" if bt == "WHITE" else "HELD (type)"),
                        "mortar_edge_tolerance_m3": r4(a["edge_tol_m3"]) if bt == "BLACK" else "",
                        "cement / sand": "HELD (mix not established)" if bt == "BLACK" else ("n/a (adhesive)" if bt == "WHITE" else "HELD (type)"),
                        "grid_implied_cutting (evidence)": (f"{a['grid_units'] / a['grid_base_units'] - 1:.4f}"
                                                            if a["grid_base_units"] else ""),
                        "gross_m2 of walls whose net is HELD": r3(a["gross_m2_on_held_walls"])})
    black = {k: v for k, v in agg.items() if k[0] == "BLACK"}
    tot = lambda key, sts: round(sum(v[key] for k, v in black.items() if k[3] in sts), 3)   # noqa: E731
    est_k = lambda k: k[3] not in (B.HELD, B.UNKNOWN)                                      # noqa: E731
    est = (B.DC, B.AOA)
    summ = {
        "method": B.METHOD, "input": "MASONRY_AREA_V1 r2 (T-108 r2 MERGED 01eeafd0): T108_BY_WALL.csv",
        "params": {k: v for k, v in p.items()},
        "black": {"net_established_m2": tot("net_m2", est), "installed_units": tot("installed_units", est),
                  "mortar_wet_m3": round(sum(v["mortar_wet_m3"] for k, v in black.items() if k[3] in est), 4),
                  "mortar_edge_tolerance_m3": round(sum(v["edge_tol_m3"] for k, v in black.items() if k[3] in est), 4),
                  "gross_m2 of walls whose net is HELD": tot("gross_m2_on_held_walls", (B.HELD, B.UNKNOWN)),
                  "by_t (net status of the area; units / mortar status ASSUMED — OWNER-APPROVED via Q-75)": {
                      t: {nst: {"net_m2": round(v["net_m2"], 3), "installed_units": round(v["installed_units"], 3),
                                "mortar_wet_m3": round(v["mortar_wet_m3"], 4)}
                          for k, v in black.items() for (bt, tt, pr, st, nst) in [k] if tt == t and est_k(k)}
                      for t in ("0.15", "0.20")}},
        "thickness_census_gross_m2 (MASONRY_AREA_V1 rows)": {k: round(v, 3) for k, v in sorted(census.items())},
        "rows": len(rows),
    }
    return by_type, summ


def write_csv(rows, cols=None):
    cols = cols or list(dict.fromkeys(k for r in rows for k in r))
    s = io.StringIO()
    w = csv.DictWriter(s, fieldnames=cols, lineterminator="\n", extrasaction="ignore")
    w.writeheader()
    for r in rows:
        w.writerow({c: r.get(c, "") for c in cols})
    return s.getvalue()


def outputs():
    rows, agg, census, p = build()
    by_type, summ = summarize(rows, agg, census, p)
    return {"BLOCK_PROCUREMENT_BY_WALL.csv": write_csv(rows), "BLOCK_PROCUREMENT_BY_TYPE.csv": write_csv(by_type),
            "WASTE_SENSITIVITY.csv": write_csv(sensitivity(agg)),
            "summary.json": json.dumps(summ, indent=1, ensure_ascii=False) + "\n"}


def main(argv):
    out = outputs()
    if "--check" in argv:
        bad = [n for n, t in out.items() if (HERE / n).read_text(encoding="utf-8") != t]
        print("check:", "OK" if not bad else f"DIFFERS {bad}")
        return 1 if bad else 0
    for n, t in out.items():
        (HERE / n).write_text(t, encoding="utf-8")
    print(json.dumps(json.loads(out["summary.json"])["black"], indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
