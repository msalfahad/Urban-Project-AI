"""T-614 development-villa census (research, unwired): every beam band x column on the GF / 1F / 2F roof-slab plans,
the uncovered band piece beside each column measured under R-T614-1 (t614_rules.py), against the candidate of record's
STR.CONC.BEAM lines; every beam end classified (column / beam / open).

    .work/venv/bin/python -I research/agents_t614/t614_alsenan.py <structural.dxf> [--write | --check] [--top]

Inputs (read only): Drive 'Alsenan chalet project' / 'ST7757 dxf.dxf' (sha256 9f9d1179..; decoded to .work/private
only), read by route G exactly as ARCH_TAKEOFF_V3.0.x does; the member / line plan model of T-610
(research/agents_t610/t610_alsenan.py: drawn band hulls, support columns net of carried (S-COL.HAT ANSI35) columns,
billed plans per candidate line incl. the T-229 ledger runs) is reused unchanged, so a piece is never counted in a
way R-T610-1 would count again. Tracked output (out/): band ids, marks, line ids, areas, depths, volumes and verdicts
only; no coordinate, no drawing content.
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(HERE))
sys.path.insert(1, str(ROOT / "research" / "agents_t610"))

import t614_rules as R  # noqa: E402
import t610_alsenan as T610  # noqa: E402  (read only)
import t610_rules as R610  # noqa: E402  (read only)

OUT = HERE / "out"
JSON_OUT = OUT / "T614_BEAM_END_CENSUS.json"
MD_OUT = OUT / "T614_BEAM_END_CENSUS.md"
DXF_SHA = T610.DXF_SHA
SHEETS = T610.SHEETS                       # GF roof slab SH06, 1F roof slab SH04, 2F (top roof) slab SH02
VALUE_MATCH_M3 = 0.001                     # an unmapped ledger run 'explains' a piece when value = piece x depth +- this
CHECKER_CB11 = {"storey": "1F", "mark": "CB11", "piece_m2": 0.025, "m3": 0.018750}


def r6(x):
    return None if x is None else round(float(x), 6)


def parent_hulls(G, sid):
    """Drawn hull per route G parent band in metres (column parts included), its unit axis and its pieces."""
    from shapely.geometry import Polygon
    from shapely.affinity import affine_transform
    rec = G["D"]["sheets"][sid]
    u_m = G["D"]["unit_m"]
    ox, oy = rec["sheet"]["origin"]
    to_m = [u_m, 0, 0, u_m, -ox * u_m, -oy * u_m]
    segs = {s["id"]: s for s in G["intake"]["segments"]}
    bands = {b["band_id"]: b for b in rec["bands"]}
    beams = {b["band_id"] for b in rec["beams"]}
    parents = defaultdict(list)
    for bid, b in bands.items():
        if bid in beams:
            parents[b.get("parent") or bid].append(bid)
    out = {}
    for par, kids in sorted(parents.items()):
        b0 = bands[kids[0]]
        if b0["kind"] == "STRAIGHT":
            hull = T610._face_quad(b0, segs)
        else:
            hull = Polygon(b0["polygon"]).buffer(0)
        faces = []
        if b0["kind"] == "STRAIGHT":
            uu = R.unit(b0["u"])
            nn = (-uu[1], uu[0])
            for side in ("faces_a", "faces_b"):
                pts = [[((segs[h][k][0] - ox) * u_m, (segs[h][k][1] - oy) * u_m) for k in ("a", "b")]
                       for h in b0[side]]
                off = sum(p[0] * nn[0] + p[1] * nn[1] for s_ in pts for p in s_) / (2 * len(pts))
                iv = sorted(tuple(sorted(p[0] * uu[0] + p[1] * uu[1] for p in s_)) for s_ in pts)
                faces.append({"off_m": off, "intervals": iv})
        out[par] = {"faces": faces, "hull": R.snap(affine_transform(hull, to_m)), "u": R.unit(b0["u"]) if b0["kind"] == "STRAIGHT" else None, "kind": b0["kind"],
                    "kids": sorted(kids, key=lambda k: (bands[k].get("t0", 0.0), k))}
    return out


def unmapped_runs(lines, ledger, st):
    """Candidate HL ledger lines of this storey whose pieces are not route G bands (no plan in the T-610 model)."""
    out = []
    for ln in lines:
        eid = ln["element_id"]
        if not eid.startswith("HL:BEAM_LEDGER:") or eid.split(":")[2] != st:
            continue
        row = ledger[eid.split(":", 3)[3]]
        pcs = [p for p in row["pieces"].split("|") if p.startswith(st + ":")]
        if not pcs:
            out.append({"line_id": ln["line_id"], "run": row["run"], "mark": row["mark"], "class": ln["class"],
                        "value_m3": ln["measured_net"], "depth_m": float(row["depth_m"]) if row["depth_m"] else None,
                        "pieces_text": row["pieces"]})
    return out


def adds_lines(adds):
    return {a["line_id"] for a in adds}


def storey_census(G, sid, st, lines, ledger):
    members, cols, n_carried = T610.storey_members(G, sid, st)
    recs, piece_line = T610.line_members(lines, ledger, members, st)
    live = {lid: r for lid, r in recs.items() if r.get("drawn") is not None}
    hulls = parent_hulls(G, sid)
    col_list = sorted(getattr(cols, "geoms", [cols]), key=lambda c: (round(c.centroid.x, 3), round(c.centroid.y, 3)))
    col_list = [c for c in col_list if c.area > R.EPS_M2]
    billed = {lid: r["billed"] for lid, r in live.items() if r["billed"] is not None}
    held = [r["drawn"] for r in live.values() if r["billed"] is None]
    unmapped = unmapped_runs(lines, ledger, st)
    pairs, ends, claimed_held = [], [], []
    col_acc = defaultdict(lambda: {"X": [], "bands": [], "extra_bill": {}, "model_only": {}})
    beside_adds = defaultdict(list)
    for lid, r in recs.items():
        if r["kind"] != "LEDGER":
            continue
        row = ledger[r["element_id"].split(":", 3)[3]]
        for term in (row["adds"] or "").split(";"):
            m = re.search(r"SUPPORT_CUT_BESIDE \(to [A-Z0-9]+:([A-Z0-9.]+)\) \+([0-9.]+)", term)
            if m:
                beside_adds[lid].append({"to": m.group(1), "value_m3": float(m.group(2))})
    for par, h in hulls.items():
        H, u, kids = h["hull"], h["u"], h["kids"]
        own_lines = sorted({piece_line[k] for k in kids if k in piece_line})
        others = [r["drawn"] for lid, r in live.items() if lid not in own_lines]
        marks = sorted({members[k]["mark"] or "?" for k in kids})
        near = [(i, c) for i, c in enumerate(col_list) if c.distance(H) <= R.NEAR_M]
        if u is None:
            # an ARC band (ring beam): no straight axis; list every column it reaches for review, measure nothing
            for i, c in near:
                pairs.append({"storey": st, "sheet": sid, "parent": par, "marks": marks, "column": f"C{i}",
                              "position": "ARC", "overlap_with_band_m2": r6(R.inter(H, c).area), "piece_m2": 0.0,
                              "verdict": "ARC_REVIEW", "line_id": None, "line_mark": None})
            ends.append({"storey": st, "parent": par, "marks": marks, "end": "ARC", "closed_by": "ARC_RING",
                         "by": [f"C{i}" for i, _ in near]})
            continue
        end_cols = {"END_LO": [], "END_HI": []}
        nvec = (-u[1], u[0])
        nlo, nhi = R.span(H, nvec)
        b0, b1 = R.span(H, u)
        for i, c in near:
            pos = R.position(H, u, c)
            rest = [x for j, x in enumerate(col_list) if j != i]
            P, E = R.piece(H, u, c, rest)
            cover, width, off = R.column_cover(H, u, c)
            if cover <= 1e-3:
                # the column stands beside the band (touching or within NEAR_M), not in it: no beam-column piece
                pos = "BESIDE_BAND"
                E = R.Polygon()
            c0, c1 = R.span(c, u)
            # the beam that owns the piece: the piece of this parent nearest the column (its line and depth)
            kid = min(kids, key=lambda k: members[k]["drawn"].distance(c) if not members[k]["drawn"].is_empty else 9)
            lid = piece_line.get(kid)
            ln = live.get(lid)
            depth = None
            if ln is not None and ln["class"] == "RELEASED":
                depth = ln.get("depth_m")
            # T-229 SUPPORT_CUT_BESIDE: a ledger run that adds the strip beside the support at the cut to the next
            # piece bills the WHOLE strip at that column (beam_support.classify_gap: beside = gap - support)
            bill = dict(billed)
            adds = []
            near_kids = [k for k in kids if members[k]["rect"].distance(c) <= R.END_TOL_M]
            for k in near_kids:
                lk = piece_line.get(k)
                for a in beside_adds.get(lk, []):
                    if a["to"] in near_kids and a["to"] != k and lk in bill:
                        bill[lk] = R.union([bill[lk], R.minus(E, R.union(others))])
                        adds.append({"line_id": lk, "to": a["to"], "value_m3": a["value_m3"]})
                        # the neighbouring run's ledger value is its rectangle (L x b x D): the half strip the
                        # T-610 plan model gives it past the cut is model only (GF CB1 L-9270: residual -0.028125
                        # = 0.0375 x 0.75 exactly), so the strip is the adding run's alone
                        for k2 in near_kids:
                            l2 = piece_line.get(k2)
                            if l2 != lk and l2 in bill and live[l2]["kind"] == "LEDGER":
                                bill[l2] = R.minus(bill[l2], E)
            acc = R.account_piece(E, depth, bill, held, others)
            # R-T614-1 (f): the strip the column leaves beside it over its whole span (end gap included) must be
            # inside the drawn band for the piece to be MEASURED; the rest (face broken / band not drawn there) HELD
            # the collinear continuation of this band on the column's far side (same axis and face offsets)
            bridge = sorted(q for q, hq in hulls.items() if q != par and hq["u"] is not None
                            and abs(abs(hq["u"][0] * u[0] + hq["u"][1] * u[1]) - 1.0) < 1e-6
                            and abs(R.span(hq["hull"], nvec)[0] - nlo) <= 0.01
                            and abs(R.span(hq["hull"], nvec)[1] - nhi) <= 0.01
                            and hq["hull"].distance(c) <= R.NEAR_M)
            cols_all = R.union([c] + rest)
            full_diag = R.minus(R.beside_strip(u, nlo, nhi, c, (b0, b1), pos), cols_all)
            full = R.minus(R.beside_strip(u, nlo, nhi, c, (b0, b1), pos, clip=True, bridge=bool(bridge)), cols_all)
            oth_d = R.union(others)
            oth_b = R.union([bill[k] for k in bill if k not in own_lines])
            in_oth = R.inter(R.minus(full, E), oth_d)
            gap_face = R.face_gaps(R.minus(E, oth_d), u, nlo, nhi, h["faces"], c)
            rem = R.minus(R.minus(R.minus(full, E), oth_d), R.union(list(bill.values()) + held + claimed_held))
            claimed_held.append(rem)
            if 1e-3 < cover < width - 1e-3:
                col_acc[i]["X"].append(R.union([full, E]))
                col_acc[i]["bands"].append((par, marks, lid, depth, cover, width))
                for k, g in bill.items():
                    if g is not None and k in adds_lines(adds):
                        col_acc[i]["extra_bill"].setdefault(k, []).append(R.minus(E, R.union(others)))
                for k2 in near_kids:
                    l2 = piece_line.get(k2)
                    if adds and l2 in billed and l2 not in adds_lines(adds) and live[l2]["kind"] == "LEDGER":
                        col_acc[i]["model_only"].setdefault(l2, []).append(E)
            rem_a = rem.area if rem.area > R.EPS_M2 else 0.0
            if pos in end_cols:
                end_cols[pos].append(f"C{i}")
            row = {"storey": st, "sheet": sid, "parent": par, "marks": marks, "column": f"C{i}",
                   "column_area_m2": r6(c.area), "column_span_m": r6(c1 - c0), "position": pos,
                   "cover_across_m": r6(cover), "band_width_m": r6(width), "column_off_axis_m": r6(off),
                   "overlap_with_band_m2": r6(R.inter(H, c).area), "piece_kid": kid, "line_id": lid,
                   "line_class": ln["class"] if ln else None, "line_kind": ln["kind"] if ln else None,
                   "line_mark": (ln or {}).get("mark"),
                   "line_model_state": (ln or {}).get("ledger_model_state"),
                   "line_model_residual_m3": r6((ln or {}).get("ledger_residual_m3")),
                   **{k: (r6(v) if isinstance(v, float) else v) for k, v in acc.items() if k != "billed_by"},
                   "billed_by": {k: r6(v) for k, v in sorted(acc["billed_by"].items())},
                   "support_cut_beside_adds": [dict(a, strip_x_depth_m3=r6(acc["owned_m2"] * depth) if depth else None,
                                                    residual_m3=r6(a["value_m3"] - acc["owned_m2"] * depth)
                                                    if depth else None) for a in adds],
                   "collinear_continuation": bridge,
                   "beside_full_span_m2": r6(full_diag.area),
                   "beside_full_span_in_other_band_m2": r6(R.inter(R.minus(full_diag, E), oth_d).area),
                   "beside_full_span_in_other_band_billed_m2": r6(R.inter(R.inter(R.minus(full_diag, E), oth_d),
                                                                          oth_b).area),
                   "beside_strip_m2": r6(full.area), "beside_in_other_band_m2": r6(in_oth.area),
                   "beside_in_other_band_billed_m2": r6(R.inter(in_oth, oth_b).area),
                   "face_gap_m": r6(gap_face), "undrawn_strip_m2": r6(rem_a),
                   "undrawn_strip_bound_m3": r6(rem_a * depth) if (rem_a and depth) else None}
            # an unowned piece of a band whose mark has a ledger run with no route G plan: the run may bill it
            if acc.get("unowned_m2", 0) > R.EPS_M2:
                cand = [x for x in unmapped if x["mark"] in marks and x["depth_m"] and x["value_m3"] is not None]
                row["unmapped_runs_same_mark"] = [x["line_id"] for x in cand]
            pairs.append(row)
        # every drawn end of this parent: closed by a column, by another beam's band, or open (wall / slab edge)
        for side, t in (("END_LO", b0), ("END_HI", b1)):
            if end_cols[side]:
                kind, by = "COLUMN", end_cols[side]
            else:
                tip = R.inter(H, R.strip(u, t - R.END_TOL_M, t + R.END_TOL_M))
                beams = sorted({live[lid].get("mark") or lid for lid in live if lid not in own_lines
                                and live[lid]["drawn"].distance(tip) <= R.END_TOL_M})
                kind, by = ("BEAM", beams) if beams else ("OPEN", [])
            ends.append({"storey": st, "parent": par, "marks": marks, "end": side, "closed_by": kind, "by": by})
    column_strips = []
    drawn_all = R.union([r["drawn"] for r in live.values()])
    lids = sorted(live)
    crossings = R.union([R.inter(live[a]["drawn"], live[b]["drawn"]) for x, a in enumerate(lids)
                         for b in lids[x + 1:] if live[a]["drawn"].intersects(live[b]["drawn"])])
    for i in sorted(col_acc):
        ca = col_acc[i]
        X = R.minus(R.union(ca["X"]), R.union(col_list))
        if X.area <= R.EPS_M2:
            continue
        bl = {}
        for k, g in billed.items():
            g2 = R.union([g] + ca["extra_bill"].get(k, []))
            g2 = R.minus(g2, R.union(ca["model_only"].get(k, [])))
            a = R.inter(X, g2)
            if a.area > R.EPS_M2:
                bl[k] = a
        bu = R.union(list(bl.values()))
        held_d = R.minus(R.inter(X, R.union(held)), bu)
        in_drawn = R.minus(R.minus(R.inter(X, drawn_all), bu), held_d)
        undrawn = R.minus(R.minus(R.minus(X, drawn_all), bu), held_d)
        depths = sorted({b[3] for b in ca["bands"] if b[3] is not None})
        d_own = depths[0] if len(depths) == 1 else None
        rec = {"storey": st, "column": f"C{i}", "bands": [b[0] for b in ca["bands"]],
               "marks": sorted({m for b in ca["bands"] for m in b[1]}),
               "cover_across_m": sorted({r6(b[4]) for b in ca["bands"]}),
               "band_width_m": sorted({r6(b[5]) for b in ca["bands"]}),
               "strip_m2": r6(X.area),
               "billed_by": {f"{live[k].get('mark')} {k}": r6(v.area) for k, v in sorted(bl.items())},
               "billed_twice_m2": r6(sum(v.area for v in bl.values()) - bu.area),
               "in_crossing_zone_m2": r6(R.inter(X, crossings).area),
               "held_line_m2": r6(held_d.area), "drawn_unbilled_m2": r6(in_drawn.area),
               "undrawn_unbilled_m2": r6(undrawn.area), "own_depth_m": d_own}
        rec["drawn_unbilled_m3"] = r6(in_drawn.area * d_own) if d_own else None
        rec["undrawn_bound_m3"] = r6(undrawn.area * d_own) if d_own else None
        if abs(bu.area + held_d.area + in_drawn.area + undrawn.area - X.area) > 1e-7:
            raise AssertionError(rec)
        column_strips.append(rec)
    # unmapped ledger runs: a run whose value equals an unowned piece's area x its depth is taken to bill that piece
    for row in pairs:
        row["unmapped_explains"] = None
        for lid in row.get("unmapped_runs_same_mark") or []:
            x = next(v for v in unmapped if v["line_id"] == lid)
            if row.get("unowned_m2") and abs(row["unowned_m2"] * x["depth_m"] - x["value_m3"]) <= VALUE_MATCH_M3:
                row["unmapped_explains"] = {"line_id": lid, "run": x["run"], "value_m3": r6(x["value_m3"]),
                                            "piece_x_depth_m3": r6(row["unowned_m2"] * x["depth_m"])}
    n_straight = sum(1 for h in hulls.values() if h["u"] is not None)
    n_arc = len(hulls) - n_straight
    assert len([e for e in ends if e["end"] != "ARC"]) == 2 * n_straight and \
        len([e for e in ends if e["end"] == "ARC"]) == n_arc, "an end was not examined"
    return {"pairs": pairs, "ends": ends, "unmapped_runs": unmapped, "column_strips": column_strips, "columns": len(col_list),
            "carried_columns": n_carried, "parents": len(hulls)}


def classify(row):
    """Final verdict per pair after the model checks (who-is-right proposal)."""
    v = row["verdict"]
    if v != "ENGINE_WRONG_OMISSION":
        return v
    if row.get("unmapped_explains"):
        return "ENGINE_RIGHT_UNMAPPED_RUN"
    if row.get("line_model_state") == "MODEL_RESIDUAL" and row["line_model_residual_m3"] is not None and \
            row["line_model_residual_m3"] >= row["omission_m3"] - 0.001:
        return "MODEL_DEPENDENT"
    return v


def build(dxf):
    sha = hashlib.sha256(Path(dxf).read_bytes()).hexdigest()
    assert sha == DXF_SHA, sha
    G = T610.route_g(dxf)["generic"]
    lines, ledger = T610.load_lines(), T610.load_ledger()
    per, pairs, ends, unmapped, strips = {}, [], [], [], []
    for st, sid in SHEETS.items():
        c = storey_census(G, sid, st, lines, ledger)
        for p in c["pairs"]:
            p["final_verdict"] = classify(p)
        pairs += c["pairs"]
        ends += c["ends"]
        strips += c["column_strips"]
        unmapped += [{"storey": st, **{k: v for k, v in x.items() if k != "pieces_text"}} for x in c["unmapped_runs"]]
        cnt = defaultdict(int)
        for p in c["pairs"]:
            cnt[p["final_verdict"]] += 1
        ec = defaultdict(int)
        for e in c["ends"]:
            ec[e["closed_by"]] += 1
        om = [p for p in c["pairs"] if p["final_verdict"] == "ENGINE_WRONG_OMISSION"]
        per[st] = {"sheet": sid, "parent_bands": c["parents"], "support_columns": c["columns"],
                   "carried_columns_kept_in_beams": c["carried_columns"], "band_column_pairs": len(c["pairs"]),
                   "pairs_by_verdict": dict(sorted(cnt.items())), "drawn_ends": len(c["ends"]),
                   "ends_by_closure": dict(sorted(ec.items())), "ends_unexamined": 0,
                   "omission_m2": r6(sum(p["unowned_m2"] for p in om)),
                   "omission_m3": r6(sum(p["omission_m3"] for p in om)),
                   "partial_columns_with_strip": len(c["column_strips"]),
                   "strip_m2": r6(sum(x["strip_m2"] for x in c["column_strips"])),
                   "strip_drawn_unbilled_m2": r6(sum(x["drawn_unbilled_m2"] for x in c["column_strips"])),
                   "strip_undrawn_unbilled_HELD_m2": r6(sum(x["undrawn_unbilled_m2"] for x in c["column_strips"])),
                   "strip_held_line_m2": r6(sum(x["held_line_m2"] for x in c["column_strips"]))}
    fixes, n = [], 0
    for p in pairs:
        if p["final_verdict"] != "ENGINE_WRONG_OMISSION":
            continue
        n += 1
        fixes.append({"id": f"FR-T614-{n}", "storey": p["storey"], "mark": p["line_mark"], "line_id": p["line_id"],
                      "column": p["column"], "position": p["position"], "piece_m2": p["unowned_m2"],
                      "depth_m": p["depth_m"], "change_m3": p["omission_m3"],
                      "cover_across_m": p["cover_across_m"], "band_width_m": p["band_width_m"]})
    held_rows, n = [], 0
    for x in strips:
        if x["undrawn_unbilled_m2"] > R.EPS_M2:
            n += 1
            held_rows.append({"id": f"FR-T614-H{n}", "storey": x["storey"], "column": x["column"],
                              "marks": x["marks"], "undrawn_unbilled_m2": x["undrawn_unbilled_m2"],
                              "own_depth_m": x["own_depth_m"], "bound_m3": x["undrawn_bound_m3"],
                              "state": "HELD (R-T614-1 (f): band face not drawn beside the column; never 0)"})
    cb8 = {x["column"]: x for x in strips if x["storey"] == "GF" and "CB8" in x["marks"]}
    fcp025 = {"checker": {"col2_strip_m2": 0.055, "col3_strip_m2": 0.025, "col4_strip_m2": 0.035,
                          "gap_m2": 0.00744, "credit_m3": 0.0184, "omission_claim_m3": 0.073430,
                          "col3_verified_m3": 0.018750, "col2_col4_gap_unresolved_m3": 0.054680},
              "census_by_column": cb8}
    cb11 = [p for p in pairs if p["storey"] == "1F" and p["line_mark"] == "CB11" and
            p["final_verdict"] == "ENGINE_WRONG_OMISSION" and p["position"].startswith("END")]
    out = {"schema": "T614_BEAM_END_CENSUS_V1", "rule": R.RULE_ID,
           "candidate": "ARCH_TAKEOFF_V3.0.57 (= V3.0.58 for STR.CONC.BEAM)",
           "source": "Drive 'Alsenan chalet project' / 'ST7757 dxf.dxf' (sha256 9f9d1179..)",
           "per_storey": per, "pairs": pairs, "ends": ends, "unmapped_ledger_runs": unmapped, "fix_rows": fixes,
           "column_strips": strips, "held_rows": held_rows, "F_C_P02_5": fcp025,
           "F_C_P02_3": {"checker": CHECKER_CB11, "reproduced": [{k: p[k] for k in (
               "parent", "column", "position", "cover_across_m", "band_width_m", "unowned_m2", "depth_m",
               "omission_m3", "line_id")} for p in cb11]},
           "note": "areas m2, volumes m3, depths m (schedule, full depth to the slab top as the candidate bills); no "
                   "coordinate. piece = drawn band n column span - column outlines (R-T614-1 (a)); the part in "
                   "another beam's drawn band is R-T610-1's and excluded; HELD = owning line not valued."}
    return out


def render_md(d):
    L = ["# T-614 beam band x column census (R-T614-1, research, unwired)", "",
         f"Candidate {d['candidate']}; {d['source']}. Areas m2, volumes m3.", "",
         "| storey | parent bands | support columns | band x column pairs | verdicts | drawn ends | ends by closure "
         "| unexamined | omission m2 | omission m3 |", "|---|---|---|---|---|---|---|---|---|---|"]
    for st, p in d["per_storey"].items():
        L.append(f"| {st} | {p['parent_bands']} | {p['support_columns']} | {p['band_column_pairs']} | "
                 f"{', '.join(f'{k} {v}' for k, v in p['pairs_by_verdict'].items())} | {p['drawn_ends']} | "
                 f"{', '.join(f'{k} {v}' for k, v in p['ends_by_closure'].items())} | {p['ends_unexamined']} | "
                 f"{p['omission_m2']} | {p['omission_m3']} |")
    L += ["", "## Pairs with an uncovered piece (piece > 1 mm2 x 1000)", "",
          "| storey | marks | line (class) | column | position | cover / band m | off axis m | piece m2 | other band "
          "| billed | held | unowned | depth | omission m3 | verdict |", "|" + "---|" * 15]
    for p in d["pairs"]:
        if p["piece_m2"] <= R.EPS_M2:
            continue
        L.append(f"| {p['storey']} | {'/'.join(p['marks'])} | {p['line_id']} ({p['line_class']}) | {p['column']} | "
                 f"{p['position']} | {p['cover_across_m']} / {p['band_width_m']} | {p['column_off_axis_m']} | "
                 f"{p['piece_m2']} | {p['in_other_band_m2']} | {p['billed_m2']} | {p['held_m2']} | "
                 f"{p['unowned_m2']} | {p.get('depth_m')} | {p.get('omission_m3')} | {p['final_verdict']} |")
    L += ["", "## Strip beside each partial column (one record per column, all bands at it merged; clipped to the "
          "drawn band, bridged where the band resumes beyond the column)", "",
          "| storey | column | marks | cover / band m | strip m2 | billed by (mark line m2) | billed twice | in "
          "R-T610 zone | held line | drawn unbilled | undrawn unbilled (HELD) | depth | drawn unbilled m3 | HELD bound "
          "m3 |", "|" + "---|" * 14]
    for x in d["column_strips"]:
        L.append(f"| {x['storey']} | {x['column']} | {'/'.join(x['marks'])} | {x['cover_across_m']} / "
                 f"{x['band_width_m']} | {x['strip_m2']} | {'; '.join(f'{k} {v}' for k, v in x['billed_by'].items())}"
                 f" | {x['billed_twice_m2']} | {x['in_crossing_zone_m2']} | {x['held_line_m2']} | "
                 f"{x['drawn_unbilled_m2']} | {x['undrawn_unbilled_m2']} | {x['own_depth_m']} | "
                 f"{x['drawn_unbilled_m3']} | {x['undrawn_bound_m3']} |")
    L += ["", "## Fix rows (the beam owns the piece, R-T614-1 (b))", ""]
    for f in d["fix_rows"]:
        L.append(f"- {f['id']} {f['storey']} {f['mark']} ({f['line_id']}) at {f['column']} {f['position']}: column "
                 f"covers {f['cover_across_m']} of the {f['band_width_m']} m band; piece {f['piece_m2']} m2 x "
                 f"{f['depth_m']} = +{f['change_m3']} m3")
    L += ["", "## HELD rows (R-T614-1 (f))", ""]
    for h in d["held_rows"]:
        L.append(f"- {h['id']} {h['storey']} {h['column']} {'/'.join(h['marks'])}: {h['undrawn_unbilled_m2']} m2 not "
                 f"inside any drawn band and billed by no line; bound {h['bound_m3']} m3 at {h['own_depth_m']} m; "
                 f"{h['state']}")
    L += ["", "## End closure by storey", ""]
    for st in d["per_storey"]:
        op = [f"{e['parent']} {'/'.join(e['marks'])} {e['end']}" for e in d["ends"]
              if e["storey"] == st and e["closed_by"] == "OPEN"]
        L.append(f"- {st}: open ends (no column, no other beam within {R.END_TOL_M} m: wall / slab edge / "
                 f"cantilever): {', '.join(op) or 'none'}")
    L += ["", "## Ledger runs with no route G plan (checked by value against unowned pieces)", ""]
    for x in d["unmapped_ledger_runs"]:
        L.append(f"- {x['storey']} {x['mark']} {x['line_id']} {x['run']} ({x['class']}): {x['value_m3']} m3, depth "
                 f"{x['depth_m']}")
    L += ["", "## F-C-P02-3", "", "```", json.dumps(d["F_C_P02_3"], indent=1), "```", "",
          "## F-C-P02-5 (GF CB8, census by column)", "", "```", json.dumps(d["F_C_P02_5"], indent=1, sort_keys=True),
          "```", ""]
    return "\n".join(L)


def main(argv):
    d = build(argv[0])
    js = json.dumps(d, indent=1, sort_keys=True) + "\n"
    md = render_md(d) + "\n"
    if "--write" in argv:
        OUT.mkdir(exist_ok=True)
        JSON_OUT.write_text(js, encoding="utf-8")
        MD_OUT.write_text(md, encoding="utf-8")
    elif "--check" in argv:
        if JSON_OUT.read_text(encoding="utf-8") != js or MD_OUT.read_text(encoding="utf-8") != md:
            print("T-614 census differs from out/")
            return 1
    if "--top" in argv:
        for p in d["pairs"]:
            if p["piece_m2"] > R.EPS_M2 or p.get("undrawn_strip_m2"):
                print(p["storey"], p["marks"], p["line_mark"], p["line_id"], p["line_class"], p["line_kind"],
                      p["column"], p["position"], "cov", p["cover_across_m"], "/", p["band_width_m"], "off",
                      p["column_off_axis_m"], "| piece", p["piece_m2"], "oth", p["in_other_band_m2"], "bil",
                      p["billed_m2"], p["billed_by"], "held", p["held_m2"], "un", p["unowned_m2"], "d",
                      p.get("depth_m"), p["final_verdict"], p["line_model_state"], p["line_model_residual_m3"],
                      p.get("unmapped_explains"), "| facegap", p["face_gap_m"], "full", p["beside_full_span_m2"], p["beside_full_span_in_other_band_billed_m2"], "bridge", p["collinear_continuation"], "beside", p["beside_strip_m2"], p["beside_in_other_band_m2"], p["beside_in_other_band_billed_m2"], "undrawn", p["undrawn_strip_m2"],
                      p["support_cut_beside_adds"])
        for e in d["ends"]:
            if e["closed_by"] == "OPEN":
                print("OPEN END", e)
    print(json.dumps({"per_storey": d["per_storey"], "fix_rows": d["fix_rows"], "F_C_P02_3": d["F_C_P02_3"]},
                     indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
