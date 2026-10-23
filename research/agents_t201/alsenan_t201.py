"""T-201 Alsenan (development villa): heads and sills of the openings the drawings leave undimensioned, from drawn
geometry, and the downstream deltas, from repository files only.

Usage (Python 3.11, from the repository root):
    python3 -I research/agents_t201/alsenan_t201.py            # writes HEADS_T201.csv, CONSEQUENCES_T201.csv,
                                                               #        NET_BLOCK_T201.csv, DOWNSTREAM_T201.csv, summary.json
    python3 -I research/agents_t201/alsenan_t201.py --check    # rebuilds in memory, compares byte for byte

Inputs (committed, read only): READINGS_T201.csv (this run's readings: drawn edges as millimetres above the view's own
+-0.00 dimension-chain tick, drawn x relative to the first drawn edge of the row, per-edge overlay residuals against the
current issue; no drawing coordinate), research/agents_t198/OPENINGS_T198.csv (census r3), research/agents_t175 (hosts,
consequence / net-block builder through engine/source/opening_scope_v1.py, merged), research/agents_t143 (block runs).
The readings were made on Drive "Alsenan chalet project": the architectural .dwf (DWF 6 model-space plot, 2026-04-26,
read with w2d_reader.py), P7757_DXF_COMPRESSED.zip (P7757.dxf) and the 400 dpi scans p7757_arch_sheet09, p7757_arch_sheet10,
Alsenan_Architectural_P7757_Pages_07-08 p.7 and Pages_11-12 p.11 / p.12. No drawing, image, coordinate or client name
is committed."""
from __future__ import annotations

import csv
import io
import json
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
RES = HERE.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(RES / "agents_t175"))
import heads_from_geometry as G                                        # noqa: E402
import alsenan_t175 as T175                                             # noqa: E402

TOL_BIND = 0.02          # m: spacing and width agreement for a binding (plan widths are printed to the cm)
TOL_ISSUE = 0.04         # m: overlay agreement with the current-issue scan (400 dpi at 1:100: 1 px = 6.35 mm; the
                         #    scan's local distortion reached 32 mm on correct lines; a smaller change is undetectable)
DC, HELD = G.DC_GEOM, G.HELD


def _read(p):
    return list(csv.DictReader(open(p, encoding="utf-8")))


def _f(v):
    return float(v) if v not in ("", None) else None


def heads():
    rd = _read(HERE / "READINGS_T201.csv")
    census = {r["ID"]: r for r in _read(RES / "agents_t198/OPENINGS_T198.csv")}
    dat = G.datum(0.0, 0.0, "mm", "the view's own +-0.00 dimension-chain tick (chain 100 / 870 / 420 / 50 cm)")
    groups = {}
    for r in rd:
        groups.setdefault((r["view"], r["storey"]), []).append(r)
    binding = {}
    for (view, st), rows in groups.items():
        plan = [(r["opening_id"], float(r["plan_pos_m"]), float(r["plan_width_m"])) for r in rows
                if r["plan_pos_m"] and r["drawn_x0_mm"]]
        drawn = [(r["opening_id"], float(r["drawn_x0_mm"]), float(r["drawn_x1_mm"])) for r in rows
                 if r["plan_pos_m"] and r["drawn_x0_mm"]]
        if len(plan) >= 2:
            b = G.bind(plan, drawn, tol_m=TOL_BIND, units="mm")
            for pid in [p[0] for p in plan]:
                ok = b["bound"].get(pid) == pid and b["width_check"].get(pid, (0, 0, False))[2]
                binding[pid] = ("BOUND" if ok else "NOT BOUND", b)
    out = []
    for r in rd:
        oid = r["opening_id"]
        c = census[oid]
        w = float(c["WIDTH_M"]) if c["WIDTH_M"] else None
        cand = [x.strip() for x in r["note"].split(";")] if r["view"] == "FENCE" else None
        if r["drawn_sill_mm"] == "":
            rec = G.head_record(oid, w, None, None, dat, candidates=cand)
            bstat = "NOT DRAWN" if r["view"] == "NONE" else "EDGES NOT THE OPENING'S"
        else:
            issue = None if r["issue_edges_mm"] == "CURRENT" else [float(x) / 1000 for x in r["issue_edges_mm"].split(";")]
            bstat, width_ok = {"B-B": "SECTION CUT (the plan's B-B cut line crosses the opening's plan symbol)",
                               "NW": "SAME OUTLINE AS ITS PRINTED TWIN W15 (lines translate to 1 mm)"}.get(r["view"], "UNBOUND"), True
            if oid in binding:
                bstat = binding[oid][0]
                width_ok = bstat == "BOUND"
            rec = G.head_record(oid, w, float(r["drawn_sill_mm"]), float(r["drawn_head_mm"]), dat,
                                ffl_m=_f(r["ffl_m"]), width_ok=width_ok, current_issue=issue, tol_m=TOL_ISSUE,
                                cut_only=r["view"] == "B-B",
                                count_held=c["HOLD_CAUSE"] if oid == "W02" else None)
            if issue is None:
                rec["issue_check"] = "CURRENT ISSUE (P7757.dxf)"
        a = G.area(rec, w)
        fw, fh = _f(c["FREELANCER_W"]), _f(c["FREELANCER_H"])
        out.append({
            "ID": oid, "KIND": c["KIND"], "FLOOR": c["FLOOR"], "WIDTH_M": c["WIDTH_M"], "VIEW": r["view"],
            "BINDING": bstat, "SILL_LEVEL_M": rec.get("sill_level_m"), "HEAD_LEVEL_M": rec.get("head_level_m"),
            "HEIGHT_M": rec.get("height_m"), "FFL_M": r["ffl_m"], "FFL_SOURCE": r["ffl_source"],
            "SILL_ABOVE_FFL_M": rec.get("sill_above_ffl_m"), "HEAD_ABOVE_FFL_M": rec.get("head_above_ffl_m"),
            "AREA_M2": a, "STATUS": rec["status"], "BASIS": "drawn geometry (no printed dimension); N09 'dimensions not "
            "to scale' stands: a printed value, when issued, governs" if rec.get("height_m") else "",
            "ISSUE_CHECK": rec.get("issue_check", ""), "WHY": rec.get("why", ""),
            "FREELANCER_W_X_H": f"{fw:.2f} x {fh:.2f}" if fw and fh else "",
            "FREELANCER_M2": round(fw * fh, 4) if fw and fh else None,
            "SOURCE": r["source"], "NOTE": r["note"],
        })
    return out, census


def consequences(hd):
    """Re-run the merged T-175 builder (OPENING_SCOPE_V1) with the established heights put into its host list."""
    est = {h["ID"]: h for h in hd if h["HEIGHT_M"] is not None}
    hosts = _read(RES / "agents_t175/T175_OPENING_HOSTS.csv")
    cols = list(hosts[0].keys())
    for h in hosts:
        e = est.get(h["ID"])
        if not e:
            continue
        h["HEIGHT_M"] = f"{e['HEIGHT_M']:.3f}"
        h["HEIGHT_STATUS_T150"] = "PRINTED" if e["STATUS"] == DC else "HELD"   # T-175 maps PRINTED -> DRAWING-CONFIRMED
        # sill above the HOST RUN's datum (the run's storey FFL in T-143); for W05 the W.C.'s own floor stays HELD
        run_ffl = {"GF": 1.00, "1F": 5.50, "2F": 9.70}[h["FLOOR"]]
        if e["FFL_M"]:
            run_ffl = float(e["FFL_M"])
        h["SILL_ABOVE_FFL_M"] = f"{e['SILL_LEVEL_M'] - run_ffl:.3f}"
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "T175_OPENING_HOSTS.csv"
        with open(p, "w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=cols, lineterminator="\n")
            w.writeheader()
            w.writerows(hosts)
        old = T175.HERE
        T175.HERE = Path(td)
        try:
            ops, walls = T175.build()
        finally:
            T175.HERE = old
    a, b = T175.tables(ops, walls)
    return ops, walls, a, b


def downstream(hd, ops_new):
    before = {r["opening"]: r for r in _read(RES / "agents_t175/T175_OPENING_CONSEQUENCES.csv")}
    nets_b = {r["row_id"]: r for r in _read(RES / "agents_t175/T175_NET_BLOCK_BY_WALL.csv")}
    after = {c["id"]: c for c in ops_new}
    ids = [h["ID"] for h in hd]
    t143 = {r["row_id"]: r for r in _read(RES / "agents_t143/T143_BLOCK_BY_WALL_RUN.csv")}
    rows = []

    def add(oid, line, unit, b, bs, a, as_, note=""):
        rows.append({"opening": oid, "line": line, "unit": unit, "before": b, "before_status": bs, "after": a,
                     "after_status": as_, "delta": (round(float(a) - float(b), 3) if b not in ("", None) and
                                                    a not in ("", None) else ""), "note": note})

    for oid in ids:
        if oid not in before or oid not in after:
            continue
        b, c = before[oid], after[oid]
        r3 = T175.r3
        add(oid, "opening m2 (w x h)", "m2", b["opening_m2"], b["opening_status"], r3(c["opening_m2"]),
            c["opening_status"])
        add(oid, "block deduction (Q-73 / T-175)", "m2", b["block_deduction_m2"], b["block_status"],
            r3(c["block_deduction"]["m2"]), c["block_deduction"]["status"], c["block_deduction"].get("why", ""))
        fa, fb = c["finish_deduction"]
        add(oid, f"finish deduction face A ({fa['family']})", "m2", b["face_A_m2"], b["finish_status"], r3(fa["m2"]),
            fa["status"])
        add(oid, f"finish deduction face B ({fb['family']})", "m2", b["face_B_m2"], b["finish_status"], r3(fb["m2"]),
            fb["status"])
        add(oid, "reveal (2 jambs + head + sill for a window; UP-REVEAL-001 via OPENING_SCOPE_V1)", "m.l",
            b["reveal_lm"], b["reveal_lm_status"], r3(c["reveal_lm"]["m"]), c["reveal_lm"]["status"])
        lt = c["lintel"]
        add(oid, "lintel need (head vs member soffit of the host run)", "status", "", b["lintel_status"], "",
            lt["status"], lt.get("why", "") + (f"; row {lt.get('row')}" if lt.get("row") else ""))
        run = t143.get(c["_host"]["HOST_ROW"])
        clear = T175.clear_min(run["members_above"]) if run else None
        if c["height_m"] is not None and c["height_status"] == DC:
            head = (c["sill_m"] or 0.0) + c["height_m"]
            if clear is None:
                add(oid, "masonry above the head, LOWER BOUND (lowest member soffit along the host run - head)", "m", "", "HELD", "",
                    "HELD", "member soffit of the host run not established (T-143)")
            else:
                room = round(clear - head, 3)
                add(oid, "masonry above the head, LOWER BOUND (lowest member soffit along the host run - head)", "m", "", "HELD",
                    f"{room:.3f}", DC if room >= -0.005 else HELD,
                    "head reaches the member: the member is the lintel" if abs(room) <= 0.005 else
                    ("head ABOVE the lowest soffit of the run: the soffit is not over this opening or a level is "
                     "wrong: HELD" if room < -0.005 else "lintel needed (S8.6 schedule row binds by width)"))
                if room > 0.005 and c["width_m"]:
                    add(oid, "face above the head per side, LOWER BOUND (width x masonry above), inside the room / facade faces",
                        "m2", "", "HELD", f"{c['width_m'] * room:.3f}", DC, "already inside the T-128 / T-162 gross "
                        "faces; listed for the Checker, not an additional quantity")
    return rows, nets_b


def _csv(rows, cols=None):
    o = io.StringIO()
    cols = cols or list(rows[0].keys())
    w = csv.DictWriter(o, fieldnames=cols, lineterminator="\n")
    w.writeheader()
    for r in rows:
        w.writerow({k: ("" if r.get(k) is None else (f"{r[k]:.3f}" if isinstance(r[k], float) else r[k])) for k in cols})
    return o.getvalue()


def summary(hd, census, walls_new, nets_b, down):
    win = [r for r in census.values() if r["KIND"] == "WINDOW"]
    new = {h["ID"]: h for h in hd}
    dc_before = [r for r in win if r["HEIGHT_STATUS"] == "PRINTED" and r["HEIGHT_M"]]
    dc_after_ids = {r["ID"] for r in dc_before} | {i for i, h in new.items() if h["KIND"] == "WINDOW" and h["STATUS"] == DC}

    def eng(i):
        if i in new and new[i]["AREA_M2"] is not None:
            return new[i]["AREA_M2"]
        r = census[i]
        return float(r["WIDTH_M"]) * float(r["HEIGHT_M"])

    def fl(i):
        r = census[i]
        return float(r["FREELANCER_W"]) * float(r["FREELANCER_H"]) if r["FREELANCER_W"] and r["FREELANCER_H"] else None

    def like(ids):
        ids = [i for i in ids if fl(i) is not None]
        e, f = sum(eng(i) for i in ids), sum(fl(i) for i in ids)
        return {"n": len(ids), "engine_m2": round(e, 3), "freelancer_m2": round(f, 3),
                "diff_m2": round(e - f, 3), "diff_pct_of_freelancer": round(100 * (e - f) / f, 2) if f else None}

    newly = sorted(i for i in dc_after_ids if i not in {r["ID"] for r in dc_before})
    wb = {r["row_id"]: r for r in nets_b.values()}
    wall_moves = []
    for x in walls_new:
        b = wb.get(x["wall"])
        if not b:
            continue
        nb = b["net_m2_on_t143_gross"]
        na = T175.r3(x["net_m2"])
        db, da = b["deducted_established_m2"], T175.r3(x["deducted_m2"])
        if nb != na or db != da:
            bb = x.get("net_bounds_m2")
            wall_moves.append({"wall": x["wall"], "gross_m2": T175.r3(x["gross_m2"]), "deducted_before_m2": db,
                               "deducted_after_m2": da, "net_before_m2": nb or b["net_bounds_m2"], "net_after_m2": na or
                               (f"{T175.r3(bb[0])} .. {T175.r3(bb[1])}" if bb else ""), "held_after": ";".join(x["held_openings"]),
                               "s5_after": x["s5_status"]})
    rev = {}
    for d in down:
        if d["line"].startswith("reveal") and d["after_status"] == DC and d["before_status"] != DC:
            rev[d["opening"]] = float(d["after"])
    return {
        "task": "T-201", "development_villa": True, "accuracy_claim": "none (development villa)",
        "windows_total_in_census": len(win),
        "windows_height_DRAWING_CONFIRMED_before": len(dc_before),
        "windows_height_DRAWING_CONFIRMED_after": len(dc_after_ids),
        "windows_newly_established": newly,
        "windows_still_held": sorted(i for i in (r["ID"] for r in win) if i not in dc_after_ids),
        "like_for_like_before (same openings, engine vs freelancer)": like([r["ID"] for r in dc_before]),
        "like_for_like_newly_established": like(newly),
        "like_for_like_after": like(sorted(dc_after_ids)),
        "other_openings": {h["ID"]: {"status": h["STATUS"], "height_m": h["HEIGHT_M"], "area_m2": h["AREA_M2"],
                                     "why": h["WHY"]} for h in hd if h["KIND"] != "WINDOW"},
        "W02": {k: new["W02"][k] for k in ("SILL_LEVEL_M", "HEAD_LEVEL_M", "HEIGHT_M", "STATUS", "WHY")},
        "block_runs_moved": wall_moves,
        "reveal_m_l_newly_DRAWING_CONFIRMED": {"n": len(rev), "m": round(sum(rev.values()), 3)},
        "tolerances_m": {"binding": TOL_BIND, "current_issue_overlay": TOL_ISSUE},
    }


def outputs():
    hd, census = heads()
    ops, walls, cons_csv, net_csv = consequences(hd)
    down, nets_b = downstream(hd, ops)
    s = summary(hd, census, walls, nets_b, down)
    return {"HEADS_T201.csv": _csv(hd), "CONSEQUENCES_T201.csv": cons_csv, "NET_BLOCK_T201.csv": net_csv,
            "DOWNSTREAM_T201.csv": _csv(down), "summary.json": json.dumps(s, indent=1, ensure_ascii=False) + "\n"}


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    out = outputs()
    if "--check" in argv:
        bad = [n for n, t in out.items() if (HERE / n).read_text(encoding="utf-8") != t]
        print("check:", "OK" if not bad else f"DIFFERS {bad}")
        return 1 if bad else 0
    for n, t in out.items():
        (HERE / n).write_text(t, encoding="utf-8")
    print("written:", ", ".join(out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
