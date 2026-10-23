"""T-207 Alsenan (development villa): openings closure, census r4 (W02 count, W11 / W12 heights behind shutters, the
three leafless openings' heads and what is built above them, head soffits, the P-GF-05 threshold), from repository
files only.

Usage (Python 3.11, from the repository root):
    python3 -I research/agents_t207/alsenan_t207.py            # writes CLOSURE_T207.csv, DOWNSTREAM_T207.csv, summary.json
    python3 -I research/agents_t207/alsenan_t207.py --check    # rebuilds in memory, compares byte for byte

Inputs (committed, read only): READINGS_T207.csv (this run's readings: relative millimetres or levels, no drawing
coordinate), research/agents_t198/OPENINGS_T198.csv (census r3), research/agents_t201/HEADS_T201.csv and
CONSEQUENCES_T201.csv / NET_BLOCK_T201.csv (T-201, merged 5dade783), research/agents_t175 (hosts + builder through
engine/source/opening_scope_v1.py, merged; read only). The readings were made on Drive "Alsenan chalet project": the
architectural .dwf (DWF 6 plot, read with research/agents_t201/w2d_reader.py), P7757_DXF_COMPRESSED.zip (P7757.dxf),
ST7757 dxf.dxf, and the current-issue scan Alsenan_Architectural_P7757_Pages_11-12 p.12. No drawing, image, coordinate
or client name is committed.
"""
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
import closure_r4 as C                                                 # noqa: E402
import alsenan_t175 as T175                                            # noqa: E402

TOL_BIND = 0.02          # m, as T-201 (plan widths printed to the cm)
TOL_ISSUE = 0.04         # m, as T-201 (400 dpi scan at 1:100)
DC, HELD, UNKNOWN, AOA = C.DC, C.HELD, C.UNKNOWN, C.AOA


def _read(p):
    return list(csv.DictReader(open(p, encoding="utf-8")))


def readings():
    out = {}
    for r in _read(HERE / "READINGS_T207.csv"):
        out[(r["item"], r["quantity"])] = r
    return out


def _nums(s):
    return [float(x) for x in s.split(";")]


def _v(rd, item, q):
    return rd[(item, q)]["value"]


def shuttered_pair(rd, census):
    """W11 / W12: the outline between the shutter leaves on the fence elevation."""
    recs = {}
    drawn = []
    for oid in ("W11", "W12"):
        pw = float(census[oid]["WIDTH_M"])
        jl, jr = float(_v(rd, oid, "jamb_left_x")), float(_v(rd, oid, "jamb_right_x"))
        yb, yt = float(_v(rd, oid, "outline_bottom_y")), float(_v(rd, oid, "outline_top_y"))
        leaves = [tuple(_nums(_v(rd, oid, "leaf_left_x"))), tuple(_nums(_v(rd, oid, "leaf_right_x")))]
        fr = _nums(_v(rd, oid, "frame"))
        rec = C.opening_between_leaves(pw, (jl, jr), (yb, yt), "mm", leaves=leaves, frame=tuple(fr), tol_m=TOL_BIND,
                                       source=rd[(oid, "jamb_left_x")]["source"])
        recs[oid] = rec
        drawn.append((jl, jr, yb, yt))
    sp = float(_v(rd, "W11-W12", "plan_centre_spacing")) / 1000
    pair = C.bind_twins([("W11", 0.0), ("W12", sp)], drawn, "mm", tol_m=TOL_BIND)
    res = [abs(x) / 1000 for x in _nums(_v(rd, "W11-W12", "issue_check_x_residuals"))]
    hh, sill = _nums(_v(rd, "W11-W12", "issue_check_height"))
    res += [abs(hh - (float(_v(rd, "W11", "outline_top_y")) - float(_v(rd, "W11", "outline_bottom_y")))) / 1000,
            abs(sill - float(_v(rd, "W11", "outline_bottom_y"))) / 1000]
    worst = round(max(res), 4)
    issue = f"AGREES (max edge offset {worst:.3f} m over 10 edges)" if worst <= TOL_ISSUE else \
        f"DIFFERS ({worst:.3f} m)"
    out = []
    for oid, rec in recs.items():
        st = rec["status"] if (pair["status"] == "BOUND" and worst <= TOL_ISSUE) else HELD
        h = rec["height_m"] if st == DC else None
        w = float(census[oid]["WIDTH_M"])
        out.append({
            "ID": oid, "ITEM": "window height and area (opening between the shutter leaves)", "UNIT": "m / m2",
            "BEFORE": "HELD (T-201: shutters read as covering the jambs; candidates 2.20 / 2.02)",
            "AFTER_VALUE": f"h {h:.2f}; {w:.2f} x {h:.2f} = {w * h:.3f} m2" if h else "",
            "AFTER_STATUS": st,
            "BASIS": (f"outline between the leaves {rec['width_drawn_m']:.3f} m vs plan {w:.2f} (tol {TOL_BIND}); pair "
                      f"spacing drawn {pair.get('spacing_drawn')} vs plan {pair.get('spacing_plan')} ({pair['status']}: "
                      f"{pair['why']}); leaves {rec['leaves']} m beside the jambs (own item); frame {rec['frame']} m "
                      f"inside (fabrication size, not the opening); current issue {issue}"),
            "STILL_HELD": "absolute sill / head (the fence elevation prints no level: datum not printed); sill above "
                          "the +0.30 dewaneya floor therefore HELD; lintel need HELD on it",
            "FREELANCER": f"{census[oid]['FREELANCER_W']} x {census[oid]['FREELANCER_H']}",
            "VERDICT_PROPOSAL": "ENGINE_RIGHT on the opening basis (his 2.00 is close to the drawn frame 2.017, not the "
                                "2.20 opening)"})
    return out, recs, pair, issue


def w02(rd, census):
    st_cols = [("CN", False)] if _v(rd, "W02", "structural_columns_in_span") == "CN" else []
    rec = C.glazed_run_count(int(_v(rd, "W02", "plan_transverse_lines_in_span")),
                             int(_v(rd, "W02", "arch_column_overlay_in_span")), st_cols,
                             render_count=int(_v(rd, "W02", "render_count")))
    w = float(census["W02"]["WIDTH_M"])
    return [{
        "ID": "W02", "ITEM": "count of the saloon glazing (one opening or two with a pier)", "UNIT": "nr / m2",
        "BEFORE": "HELD 1 .. 2 (T-161 F23 render vs plan; D-53)",
        "AFTER_VALUE": f"drawn count {rec['count']}; area on the drawn count {w:.2f} x 2.20 = {w * 2.20:.3f} m2 "
                       f"(height at the B-B cut, T-201)",
        "AFTER_STATUS": rec["status"],
        "BASIS": ("every project drawing draws ONE opening: plan glazing continuous over 6.232 m with no transverse line "
                  "(DWF + current DXF); no column of the architectural overlay inside the span; the structural column "
                  "plan has one CN 300x300 at 2.950 .. 3.250 m from the south end, and the column schedule strikes CN out "
                  "above the foundation (a neck, no pier); the NW elevation is drawn in section through the saloon "
                  "(W02 not drawn on any elevation); B-B cuts one opening. " + rec["why"]),
        "STILL_HELD": "count (render 2 vs drawings 1) -> windows pcs 29 .. 30 and W02 m2; designer D-53 narrowed: "
                      "'is the pier in the renders built? the structural set has only a neck (CN) at that point'",
        "FREELANCER": f"{census['W02']['FREELANCER_W']} x {census['W02']['FREELANCER_H']} (27.219 m2; his 4.30 is W03's)",
        "VERDICT_PROPOSAL": "count: UNRESOLVED (designer); height ENGINE_RIGHT proposal stands (T-201)"}], rec


def leafless(rd):
    rows = []
    # P-GF-05: head established (T-201); what spans it and what is built above
    head = float(_v(rd, "P-GF-05", "head_level"))
    soffit_lb = float(_v(rd, "P-GF-05", "deepest_drawn_gf_roof_beam_soffit"))
    ln = C.lintel_need(head, soffit_lb, 0.20)
    w = 1.20
    length = round(w + 2 * 0.40, 3)
    rows.append({
        "ID": "P-GF-05", "ITEM": "spanning member at the head (Q-HEAD-UNDER-BEAM, S8.6 OP-GF-012)", "UNIT": "status / m / m3",
        "BEFORE": "BLOCKED_SUPPORT_IDENTITY (head vs B1 soffit not established)",
        "AFTER_VALUE": (f"lintel needed (gap head -> lowest drawn GF-roof member soffit >= {ln['gap_lower_bound_m']:.2f} m); "
                        f"row L2 (101-200 cm) 0.20 x 0.20; length at the printed MIN.40cm bearing {length:.2f} m -> "
                        f"{length * 0.20 * 0.20:.3f} m3 (S8.6 released basis, as LT-OP-1F-021)"),
        "AFTER_STATUS": ln["status"] + " (need); quantity HELD for release (bearing beyond the minimum, T-175)",
        "BASIS": ("head +2.65 (T-201, merged); member over it B1 (S8.6 beam audit, b 0.20, schedule h 0.40); section B-B "
                  "draws the GF-roof slab +5.30 .. +5.50 and its deepest beam soffit at +4.95, so no GF-roof member "
                  "comes within 2.30 m of the head: the head is not the beam soffit"),
        "STILL_HELD": "bearing length beyond MIN.40cm (T-175)", "FREELANCER": "no row (lintels not itemised per opening)",
        "VERDICT_PROPOSAL": "NOT COMPARABLE"})
    face_top = float(_v(rd, "P-GF-05", "face_above_head_drawn_to"))
    s143 = float(_v(rd, "P-GF-05", "member_soffit_t143_basis"))
    lo, hi = round(w * (face_top - head - 0.20), 3), round(w * (s143 - head - 0.20), 3)
    rows.append({
        "ID": "P-GF-05", "ITEM": "masonry above the lintel (in no T-143 run: the open side was split out)", "UNIT": "m2 / m3",
        "BEFORE": "UNKNOWN (T-198: face above the head, owner trade and material)",
        "AFTER_VALUE": f"candidates {lo:.3f} .. {hi:.3f} m2 ({lo * 0.20:.3f} .. {hi * 0.20:.3f} m3 at 0.20)",
        "AFTER_STATUS": HELD,
        "BASIS": (f"1.20 x (top - lintel top +{head + 0.20:.2f}): top = the drawn face edge +{face_top:.2f} (SW elevation) "
                  f".. the B1 soffit +{s143:.2f} on the T-143 calculated basis; block type white by the owner Q-60 "
                  "fallback for an outer wall line (ASSUMED — OWNER-APPROVED) once the quantity is released"),
        "STILL_HELD": "B1 soffit level (structural levels not printed: T-200 / T-206)", "FREELANCER": "no row",
        "VERDICT_PROPOSAL": "NOT COMPARABLE"})
    fa, fb = [x.strip() for x in _v(rd, "P-GF-05", "finishes_either_side").split("|")]
    th = C.threshold_at("PASSAGE", finish_a=fa, finish_b=fb, width_m=w)
    rows.append({
        "ID": "P-GF-05", "ITEM": "threshold line (T-175 42.22 -> 41.02 m.l)", "UNIT": "m.l",
        "BEFORE": "UNKNOWN 1.200 m.l (no door, no level change)",
        "AFTER_VALUE": f"{th['line']} {th['m']:.3f} m.l", "AFTER_STATUS": th["status"],
        "BASIS": th["why"] + "; owner outdoor rule: sides porcelain / ceramic, court interlock",
        "STILL_HELD": "the item at the edge (designer list, not an owner question: 1.20 m.l)", "FREELANCER": "no row",
        "VERDICT_PROPOSAL": "NOT COMPARABLE"})
    # P-GF-01 / P-1F-01: heads drawn nowhere
    for oid, member, row in (("P-GF-01", "B2 (S8.6 OP-GF-020)", "L1"), ("P-1F-01", "none (S8.6 LT-OP-1F-021 released)", "L2")):
        need = C.lintel_need(None, None, 0.20)
        rows.append({
            "ID": oid, "ITEM": "head level and what is built above it", "UNIT": "m / m2",
            "BEFORE": "HELD (drawn on no sheet)", "AFTER_VALUE": "", "AFTER_STATUS": HELD,
            "BASIS": f"{_v(rd, oid, 'head')} {rd[(oid, 'head')]['source']}; member over: {member}; lintel need: {need['why']}",
            "STILL_HELD": ("head (designer D-45 family); " +
                           ("lintel need under B2 (S8.6 Q-HEAD-UNDER-BEAM)" if oid == "P-GF-01" else
                            "masonry above the released lintel 0 .. 4.992 m2 and its faces (T-198)")),
            "FREELANCER": "no row", "VERDICT_PROPOSAL": "NOT COMPARABLE"})
    # head soffits = the reveal's head term
    for oid, depth, incl in (("P-GF-05", 0.20, True), ("P-GF-01", 0.20, False), ("P-1F-01", 0.15, False)):
        w0 = {"P-GF-05": 1.20, "P-GF-01": 0.90, "P-1F-01": 1.30}[oid]
        hr = C.head_reveal(w0, depth)
        rows.append({
            "ID": oid, "ITEM": "head soffit (T-198 listed it as its own m2 line)", "UNIT": "m.l / m2",
            "BEFORE": f"{w0 * depth:.3f} m2 DRAWING-CONFIRMED, owner ledger not named",
            "AFTER_VALUE": f"head term of the reveal: {hr['head_lm']:.2f} m.l x {depth:.2f} = {hr['head_m2']:.3f} m2; "
                           "no separate line",
            "AFTER_STATUS": hr["status"],
            "BASIS": hr["why"] + ("; already inside T-201's P-GF-05 reveal 6.200 m.l (2 x 2.50 + 1.20)" if incl else
                                  "; the reveal's jambs stay HELD with the head level, the head term does not"),
            "STILL_HELD": "" if incl else "jamb terms (head level)", "FREELANCER": "no row",
            "VERDICT_PROPOSAL": "NOT COMPARABLE"})
    return rows


def downstream(heads201, w11_12):
    """Re-run the merged T-175 builder (OPENING_SCOPE_V1) with T-201's established heights and W11 / W12."""
    hosts = _read(RES / "agents_t175/T175_OPENING_HOSTS.csv")
    cols = list(hosts[0].keys())
    est = {h["ID"]: h for h in heads201 if h["STATUS"] == DC}
    for h in hosts:
        e = est.get(h["ID"])
        if e:
            h["HEIGHT_M"] = e["HEIGHT_M"]
            h["HEIGHT_STATUS_T150"] = "PRINTED"
            run_ffl = float(e["FFL_M"]) if e["FFL_M"] else {"GF": 1.00, "1F": 5.50, "2F": 9.70}[h["FLOOR"]]
            h["SILL_ABOVE_FFL_M"] = f"{float(e['SILL_LEVEL_M']) - run_ffl:.3f}"
        if h["ID"] in w11_12 and w11_12[h["ID"]]["status"] == DC:
            h["HEIGHT_M"] = f"{w11_12[h['ID']]['height_m']:.3f}"
            h["HEIGHT_STATUS_T150"] = "PRINTED"          # T-175 maps PRINTED -> DRAWING-CONFIRMED; sill left blank
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "T175_OPENING_HOSTS.csv"
        with open(p, "w", encoding="utf-8", newline="") as f:
            wr = csv.DictWriter(f, fieldnames=cols, lineterminator="\n")
            wr.writeheader()
            wr.writerows(hosts)
        old = T175.HERE
        T175.HERE = Path(td)
        try:
            ops, walls = T175.build()
        finally:
            T175.HERE = old
    before = {r["opening"]: r for r in _read(RES / "agents_t201/CONSEQUENCES_T201.csv")}
    nets_b = {r["row_id"]: r for r in _read(RES / "agents_t201/NET_BLOCK_T201.csv")}
    r3 = T175.r3
    rows = []

    def add(oid, line, unit, b, bs, a, as_, note=""):
        d = round(float(a) - float(b), 3) if (b not in ("", None) and a not in ("", None)) else ""
        rows.append({"opening": oid, "line": line, "unit": unit, "before": b, "before_status": bs, "after": a,
                     "after_status": as_, "delta": d, "note": note})

    byid = {c["id"]: c for c in ops}
    for oid in ("W11", "W12"):
        b, c = before[oid], byid[oid]
        add(oid, "opening m2 (w x h)", "m2", b["opening_m2"], b["opening_status"], r3(c["opening_m2"]),
            c["opening_status"])
        add(oid, "block deduction (Q-73 / T-175)", "m2", b["block_deduction_m2"], b["block_status"],
            r3(c["block_deduction"]["m2"]), c["block_deduction"]["status"],
            "whole opening inside the drawn wall face (outline top 3.05 above the view's ground line, wall face above "
            "it); the host's B9 soffit check needs the sill datum (HELD), the deduction does not")
        fa, fb = c["finish_deduction"]
        add(oid, f"finish deduction face A ({fa['family']})", "m2", b["face_A_m2"], b["finish_status"], r3(fa["m2"]),
            fa["status"])
        add(oid, f"finish deduction face B ({fb['family']})", "m2", b["face_B_m2"], b["finish_status"], r3(fb["m2"]),
            fb["status"])
        add(oid, "reveal (2 jambs + head + sill; UP-REVEAL-001 via OPENING_SCOPE_V1)", "m.l", b["reveal_lm"],
            b["reveal_lm_status"], r3(c["reveal_lm"]["m"]), c["reveal_lm"]["status"],
            "reveal depth HELD (frame position), as T-175")
        add(oid, "lintel need", "status", "", b["lintel_status"], "", HELD,
            "head above the dewaneya FFL not established (no printed level on the fence elevation): the B9 soffit "
            "check is not made; row " + (c["lintel"].get("row") or ""))
    wall = {x["wall"]: x for x in walls}["GF-W18"]
    nb = nets_b["GF-W18"]
    add("GF-W18", "net block m2 of the dewaneya street run (W11 + W12 deducted)", "m2",
        nb["net_m2_on_t143_gross"] or "", nb["s5_status"] + f" (bounds {nb['net_bounds_m2']})", r3(wall["net_m2"]),
        wall["s5_status"], wall.get("s5_why", ""))
    unchanged = []
    for c in ops:
        if c["id"] in ("W11", "W12"):
            continue
        b = before.get(c["id"])
        if b and (b["opening_m2"] != r3(c["opening_m2"]) or b["block_deduction_m2"] != r3(c["block_deduction"]["m2"])
                  or b["reveal_lm"] != r3(c["reveal_lm"]["m"])):
            unchanged.append(c["id"])
    return rows, unchanged


def _csv(rows, cols=None):
    o = io.StringIO()
    cols = cols or list(rows[0].keys())
    w = csv.DictWriter(o, fieldnames=cols, lineterminator="\n")
    w.writeheader()
    for r in rows:
        w.writerow({k: ("" if r.get(k) is None else (f"{r[k]:.3f}" if isinstance(r[k], float) else r[k])) for k in cols})
    return o.getvalue()


def summary(census, heads201, w11_12, w02rec, moved, pair, issue):
    win = [r for r in census.values() if r["KIND"] == "WINDOW"]
    h201 = {h["ID"]: h for h in heads201}
    eng, fl = {}, {}
    for r in win:
        i = r["ID"]
        if r["FREELANCER_W"] and r["FREELANCER_H"]:
            fl[i] = float(r["FREELANCER_W"]) * float(r["FREELANCER_H"])
        if r["HEIGHT_STATUS"] == "PRINTED" and r["HEIGHT_M"]:
            eng[i] = float(r["WIDTH_M"]) * float(r["HEIGHT_M"])
        elif i in h201 and h201[i]["STATUS"] == DC:
            eng[i] = float(h201[i]["AREA_M2"])
        elif i in w11_12 and w11_12[i]["status"] == DC:
            eng[i] = float(r["WIDTH_M"]) * w11_12[i]["height_m"]

    def like(ids):
        ids = [i for i in ids if i in fl and i in eng]
        e, f = sum(eng[i] for i in ids), sum(fl[i] for i in ids)
        return {"n": len(ids), "engine_m2": round(e, 3), "freelancer_m2": round(f, 3), "diff_m2": round(e - f, 3),
                "diff_pct_of_freelancer": round(100 * (e - f) / f, 2) if f else None}

    est = sorted(eng)
    return {
        "task": "T-207", "development_villa": True, "accuracy_claim": "none (development villa)",
        "windows_total_in_census": len(win),
        "windows_height_DRAWING_CONFIRMED_before": 26, "windows_height_DRAWING_CONFIRMED_after": len(est),
        "windows_newly_established": sorted(i for i in w11_12 if w11_12[i]["status"] == DC),
        "windows_still_held": sorted(r["ID"] for r in win if r["ID"] not in eng),
        "like_for_like_W11_W12": like(["W11", "W12"]),
        "like_for_like_after": like(est),
        "freelancer_windows_total_m2": round(sum(fl.values()), 3),
        "W02": {"drawn_count": w02rec["count"], "status": w02rec["status"], "candidates": w02rec.get("candidates"),
                "area_on_drawn_count_m2": round(6.33 * 2.20, 3), "freelancer_m2": round(fl.get("W02", 0.0), 3)},
        "windows_pcs": {"drawn": 29, "with_render_count": 30, "status": HELD, "freelancer": 29},
        "W11_W12_pair_binding": pair["status"], "W11_W12_current_issue": issue,
        "other_T175_openings_changed_by_this_rerun": moved,
        "tolerances_m": {"binding": TOL_BIND, "current_issue_overlay": TOL_ISSUE},
    }


def outputs():
    rd = readings()
    census = {r["ID"]: r for r in _read(RES / "agents_t198/OPENINGS_T198.csv")}
    heads201 = _read(RES / "agents_t201/HEADS_T201.csv")
    sp_rows, w11_12, pair, issue = shuttered_pair(rd, census)
    w02_rows, w02rec = w02(rd, census)
    rows = w02_rows + sp_rows + leafless(rd)
    down, moved = downstream(heads201, w11_12)
    s = summary(census, heads201, w11_12, w02rec, moved, pair, issue)
    return {"CLOSURE_T207.csv": _csv(rows), "DOWNSTREAM_T207.csv": _csv(down),
            "summary.json": json.dumps(s, indent=1, ensure_ascii=False) + "\n"}


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
