"""T-387 Alsenan census (research only): the candidate of record's structural concrete lines bound to elements and
owner trades (acceptance a) and every intersecting family pair checked for shared volume billed once (acceptance b).

    python3 -I research/agents_t387/t387_alsenan.py --lines <run>/V3_0_29_BOQ_LINES.json \
        --geometry <private>/geometry.json --downgrades <board>/docs/agents/verdicts/V3.0.29/DOWNGRADES.json \
        --out research/agents_t387

--geometry is the private export of t387_geometry.py (route G's own plan records the line element ids rest on). The
outputs carry engine ids, item codes, states and m2 / m3 only: no coordinate, no polygon, no name.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import t387_rules as R  # noqa: E402

CANDIDATE = "ARCH_TAKEOFF_V3.0.29"
PLAN_SHEETS = {"2F": ("BEAMS", "SLABS"), "1F": ("BEAMS", "SLABS"), "GF": ("BEAMS", "SLABS"),
               "GROUND": ("GROUND_BEAMS", "GROUND_SLAB")}
T347_BINDING = ROOT / "research/agents_t347/BINDING_T347.csv"
# storey heights and levels the column / neck lines are billed on (route G profile values, printed: see
# research/urban_engine_m4_correctness/profile_st7757_m4.json); used only for the stacked check R-T387-4
PROFILE = ROOT / "research/urban_engine_m4_correctness/profile_st7757_m4.json"


def _sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def _lines(p):
    d = json.loads(Path(p).read_text(encoding="utf-8"))
    return d if isinstance(d, list) else d["lines"]


def flat(ln):
    loc = ln.get("location") or {}
    dims = ((ln.get("calculation") or {}).get("inputs") or {}).get("dimensions") or {}
    return {"line_id": ln["line_id"], "item_code": ln.get("item_code") or "", "element_id": loc.get("element_id"),
            "floor": loc.get("floor"), "measured_net": ln.get("measured_net"),
            "evidence_state": ln.get("evidence_state") or "", "dims": dims,
            "formula": ((ln.get("calculation") or {}).get("formula") or ""), "notes": ln.get("notes") or "",
            "inputs": (ln.get("calculation") or {}).get("inputs") or {}}


def cid_of(eid):
    """'P-C:BEAMS:GF:BAND0016.1' -> 'BEAMS:GF:BAND0016.1' (the route G component id)."""
    return eid.split(":", 1)[1] if eid and eid[:4] in ("P-C:", "U-C:") else eid


def level_bands(geom, lines_by_cid, status_by_line, rows_out, col_status, live_beams, lines_by_id):
    """R-T387-3 on every plan sheet: members from route G's plan records, billed plan from the CANDIDATE line."""
    results = {}
    for sid, rec in sorted(geom["sheets"].items()):
        st = (rec.get("sheet") or {}).get("storey")
        if st not in PLAN_SHEETS or "bands" not in rec:
            continue
        bfam, sfam = PLAN_SHEETS[st]
        M, unlined, not_members, successor = [], [], [], {}
        boxes = [tuple(c) for c in rec.get("column_boxes", [])]
        # the vertical members through this level band: the storey's columns (the necks on the ground-beam plan).
        # Their lines are not bound to an outline by position here, so the outlines are VALUED owners only when every
        # line of that storey is valued; otherwise HELD (their pairs UNDETERMINED, never 0)
        cst = col_status.get("NECK" if st == "GROUND" else st, Counter())
        col_valued = bool(cst) and set(cst) == {"VALUED"}
        for k, c in enumerate(boxes):
            x0, y0, x1, y1 = c
            M.append({"id": f"{st}:COLBOX{k:02d}", "kind": "COLUMN",
                      "polygon": [(x0, y0), (x1, y0), (x1, y1), (x0, y1)],
                      "billed_m2": (x1 - x0) * (y1 - y0) * 1e-6 if col_valued else None, "depth_m": None,
                      "line_ids": [], "why": f"vertical members of {st}: lines {dict(cst)}"})
        # beams: a live line (not NOT_APPLICABLE) bills one or more drawn bands: its own route G band, or the bands a
        # ledger run names ('#BANDxxxx', 'pieces FL:BANDxxxx|...', 'supersedes'); bands billed by one line or chained
        # by shared lines form ONE member (the group's billed plan = the sum of its lines' plans)
        bpoly = {b["band_id"]: b["polygon"] for b in rec["bands"] if b.get("polygon")}
        groups = _beam_groups(st, bfam, bpoly, live_beams.get(st, []), status_by_line)
        grouped = set()
        for gid, (bands, lns) in sorted(groups.items()):
            grouped |= set(bands)
            from shapely.ops import unary_union
            from shapely.geometry import Polygon
            geom_ = unary_union([Polygon(bpoly[x]).buffer(0) for x in bands])
            billed, depth, why = _group_billed(lns, status_by_line)
            M.append({"id": gid, "kind": "BEAM", "polygon": geom_, "billed_m2": billed, "depth_m": depth,
                      "line_ids": [x["line_id"] for x in lns], "why": why, "bands": bands})
        for bid in sorted(set(bpoly) - grouped):
            unlined.append((bid, "BEAM", bpoly[bid]))
            na = lines_by_cid.get(f"{bfam}:{st}:{bid}") or lines_by_cid.get(f"{bfam}:{st}:{bid}.1")
            if na is not None:
                successor[bid] = f"{na['line_id']} {status_by_line.get(na['line_id'])}: " + _note(na)
        for f in (rec.get("slab") or {}).get("faces", []):
            if f["class"] != "PANEL":
                continue
            cid = f"{sfam}:{st}:{f['face_id']}"
            ln = lines_by_cid.get(cid)
            if ln is None:
                unlined.append((f["face_id"], "SLAB", f.get("polygon")))
                stl = [x for k, x in lines_by_cid.items() if k.startswith(f"STAIRS:{st}:{f['face_id']}")]
                if stl:
                    successor[f["face_id"]] = "face carried by STAIR lines: " + "; ".join(
                        f"{x['line_id']} {status_by_line.get(x['line_id'])}" + (
                            "" if status_by_line.get(x["line_id"]) == "VALUED" else ": " + _note(x)) for x in stl)
                continue
            if status_by_line.get(ln["line_id"]) == "NOT_APPLICABLE":
                not_members.append((f["face_id"], "SLAB", ln["line_id"]))
                continue
            billed, depth, why = _billed_plan(ln, "SLAB", status_by_line)
            holes = sum(_area(h) for h in (f.get("hole_polygons") or []) if len(h) >= 3) * 1e-6
            exact = f.get("area_gross_m2", f["area_m2"] + f.get("member_overlap_m2", 0.0))
            M.append({"id": f["face_id"], "kind": "SLAB", "polygon": f["polygon"], "billed_m2": billed,
                      "depth_m": depth, "line_ids": [ln["line_id"]], "why": why,
                      "drawn_m2": exact + holes,           # the outer ring's exact area; holes go out below
                      "holes_m2": holes, "chord": bool(f.get("arc_edges"))})
        res = R.level_band_check(M, scale=0.001)
        # the holes of a face are not in the face: its owned plan loses them (members inside a hole are not in it)
        for m in res["members"]:
            src = next(x for x in M if x["id"] == m["id"])
            if src.get("holes_m2"):
                m["owned_m2"] -= src["holes_m2"]
                m["residual_m2"] = m["billed_m2"] - m["owned_m2"]
                m["residual_m3"] = m["residual_m2"] * m["depth_m"] if m["depth_m"] is not None else None
        # a face with an arc edge is given as a chord polygon whose excess over the face's exact area lies across the
        # arc it stops at; when that arc is an ARC band face, the polygon 'overlaps' the band by up to the excess. The
        # true overlap with the arc bands is max(0, overlap - excess) (R-T387-3a); the residual is re-taken on it.
        from shapely.geometry import Polygon
        arcs = [Polygon(b["polygon"]).buffer(0) for b in rec["bands"] if b["kind"] == "ARC" and b.get("polygon")
                and b["band_id"] in grouped]
        for m in res["members"]:
            src = next(x for x in M if x["id"] == m["id"])
            m["verdict"] = None
            if src.get("chord") and arcs:
                g = Polygon(src["polygon"]).buffer(0)
                ov = sum(g.intersection(x).area for x in arcs) * 1e-6
                excess = m["polygon_m2"] - (src["drawn_m2"] - src.get("holes_m2", 0.0))
                if ov > R.TOL_M2 and excess > R.TOL_M2:
                    ring = src["drawn_m2"] - src.get("holes_m2", 0.0)
                    loss = src["drawn_m2"] - (m["owned_m2"] + src.get("holes_m2", 0.0))
                    try:
                        m["owned_m2"], true_ov = R.arc_chord_owned(ring, m["polygon_m2"] - src.get("holes_m2", 0.0),
                                                                   loss, ov)
                    except R.Refused as e:
                        m["verdict"], m["verdict_note"] = "ARC_CHORD_UNRESOLVED", str(e)
                        continue
                    m["residual_m2"] = m["billed_m2"] - m["owned_m2"]
                    m["residual_m3"] = m["residual_m2"] * m["depth_m"] if m["depth_m"] is not None else None
                    m["arc_chord"] = {"chord_excess_m2": excess, "polygon_arc_overlap_m2": ov, "true_arc_overlap_m2": true_ov}
                    m["verdict_note"] = (f"arc chord: polygon excess {excess:.4f} m2, polygon / arc band {ov:.4f} m2, "
                                         f"true overlap {true_ov:.4f} m2")
        chord = []
        res["chord_resolved"] = sum(1 for m in res["members"] if m.get("arc_chord"))
        # R-T387-6: a beam group's residual against the route G band is reconciled to the adjustments its merged
        # ledger documents (T-229 / T-252: end square-cut, support cut beside, column owns ...); what remains is either
        # inside unbilled plan beside the band (a drawn extension no other member bills: RECHECK on the run geometry,
        # bounded) or over another member (DOUBLE)
        from shapely.ops import unary_union as _uu
        allm = _uu([R._poly(x["polygon"]) for x in M])
        for m in res["members"]:
            src = next(x for x in M if x["id"] == m["id"])
            if m["kind"] != "BEAM" or m["residual_m3"] is None:
                continue
            adj, items = _documented_adjustment(src["line_ids"], lines_by_id)
            m["documented_m3"], m["documented"] = adj, items
            m["unexplained_m3"] = m["residual_m3"] - adj
            if abs(m["unexplained_m3"]) > R.TOL_M3 and m["unexplained_m3"] > 0:
                g = R._poly(src["polygon"])
                free = g.buffer(1500.0).difference(allm).area * 1e-6      # unbilled plan within 1.5 m of the band
                m["free_beside_m2"] = free
        for m in res["members"]:
            m["within_tol"] = m["residual_m3"] is not None and abs(m["residual_m3"]) <= R.TOL_M3
            if m["verdict"] is None and m["within_tol"] and abs(m["residual_m2"]) > R.TOL_M2:
                m["verdict"] = "OK_ROUNDING"
            elif m["verdict"] is None and m.get("documented_m3") is not None and m["documented"] and \
                    abs(m["unexplained_m3"]) <= R.TOL_M3:
                m["verdict"] = "LEDGER_ADJUSTED"
                m["verdict_note"] = "residual = merged ledger adjustments: " + "; ".join(m["documented"])
            elif m["verdict"] is None and m.get("unexplained_m3") is not None and m["unexplained_m3"] > R.TOL_M3:
                dm = m["depth_m"] or 1.0
                if m.get("free_beside_m2", 0.0) * dm >= m["unexplained_m3"]:
                    m["verdict"] = "RECHECK_BOUNDED"
                    m["verdict_note"] = (f"{m['unexplained_m3']:.4f} m3 beyond the route G band and the documented "
                                         f"adjustments {m['documented_m3']:.4f}; unbilled plan beside the band "
                                         f"{m['free_beside_m2']:.4f} m2 can hold it: a drawn extension (no double) or "
                                         f"a double count of at most {m['unexplained_m3']:.4f} m3")
        live = [m for m in res["members"] if m["verdict"] is None]
        res["recheck_bound_m3"] = sum(m["unexplained_m3"] for m in res["members"] if m["verdict"] == "RECHECK_BOUNDED")
        res["ledger_adjusted_m3"] = sum(m["residual_m3"] for m in res["members"] if m["verdict"] == "LEDGER_ADJUSTED")
        res["double_m2"] = sum(m["residual_m2"] for m in live if m["residual_m2"] > R.TOL_M2)
        res["gap_m2"] = -sum(m["residual_m2"] for m in live if m["residual_m2"] < -R.TOL_M2)
        res["double_m3"] = sum(m["residual_m3"] or 0 for m in live if m["residual_m2"] > R.TOL_M2)
        res["gap_m3"] = -sum(m["residual_m3"] or 0 for m in live if m["residual_m2"] < -R.TOL_M2)
        res["status"] = ("PASS" if res["double_m2"] <= R.TOL_M2 and res["gap_m2"] <= R.TOL_M2 else "FAIL") + \
            ("_HELD" if res["held_members"] or chord or res["recheck_bound_m3"] else "")
        res["unlined_members"] = [(i, k) for i, k, _ in unlined]
        res["not_members"] = not_members
        res["successor"] = successor
        res["column_boxes"] = len(boxes)
        results[st] = (sid, res, {x["id"]: x for x in M})
    return results


def _note(ln):
    """the line's own supersession / retirement note (first 160 characters of the last version note)."""
    n = str(ln.get("notes") or "")
    return n[:160]


def _documented_adjustment(line_ids, lines_by_id):
    """sum of the signed m3 a beam line's merged ledger documents (inputs.info ledger_adds / ledger_deducts; the last
    signed figure of each ';' item), with the items."""
    import re
    adj, items = 0.0, []
    for lid in line_ids:
        info = ((lines_by_id.get(lid) or {}).get("inputs") or {}).get("info") or {}
        for k in ("ledger_adds", "ledger_deducts"):
            for it in [i.strip() for i in str(info.get(k) or "").split(";") if i.strip()]:
                nums = re.findall(r"[+-]\d+\.\d+", it)
                if nums:
                    adj += float(nums[-1])
                    items.append(it[:90])
    return adj, items


def _pieces(ln, st, bfam):
    """the drawn bands a beam line bills (band ids on this floor)."""
    import re
    eid = ln["element_id"] or ""
    c = cid_of(eid)
    pre = f"{bfam}:{st}:"
    if c.startswith(pre):
        return [c[len(pre):]]
    out = []
    pr = str((ln.get("inputs") or {}).get("printed") or "")
    m = re.search(r"pieces ([^)]*)", pr)
    if m:
        out += [t.split(":", 1)[1] for t in re.split(r"[|+,\s]+", m.group(1)) if t.startswith(st + ":BAND")]
    if not out and "#BAND" in eid:
        out = [eid.split("#", 1)[1]]
    if not out:
        for sup in (ln.get("inputs") or {}).get("supersedes") or []:
            c2 = cid_of(sup)
            if c2.startswith(pre):
                out.append(c2[len(pre):])
    return out


def _beam_groups(st, bfam, bpoly, lines, status_by_line):
    """union-find over (band, line): {group id: (bands, lines)}; a band id with a span suffix '.1' also matches the
    unsplit band and the reverse."""
    def norm(b):
        if b in bpoly:
            return b
        if b + ".1" in bpoly:
            return b + ".1"
        if b.endswith(".1") and b[:-2] in bpoly:
            return b[:-2]
        return None
    parent = {}

    def find(x):
        while parent.setdefault(x, x) != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x
    attach = defaultdict(list)
    for ln in lines:
        bs = [norm(b) for b in _pieces(ln, st, bfam)]
        bs = [b for b in bs if b]
        if not bs:
            continue
        for b in bs:
            parent[find("B:" + b)] = find("L:" + ln["line_id"])
        attach[ln["line_id"]] = bs
    groups = defaultdict(lambda: (set(), []))
    by_id = {ln["line_id"]: ln for ln in lines}
    for lid, bs in attach.items():
        r = find("L:" + lid)
        groups[r][0].update(bs)
        groups[r][1].append(by_id[lid])
    out = {}
    for r, (bands, lns) in groups.items():
        out["+".join(sorted(bands))] = (sorted(bands), sorted(lns, key=lambda x: x["line_id"]))
    return out


def _group_billed(lns, status_by_line):
    """a group's billed plan = sum of its lines' plans; any HELD line holds the group (None, never 0)."""
    plans, m3, whys = 0.0, 0.0, []
    for ln in lns:
        b, d, why = _billed_plan(ln, "BEAM", status_by_line)
        if b is None:
            return None, None, f"{ln['line_id']} {why}"
        plans += b
        m3 += b * d
        whys.append(why)
    return plans, (m3 / plans if plans else None), "; ".join(sorted(set(whys)))


def _area(p):
    return abs(sum(x0 * y1 - x1 * y0 for (x0, y0), (x1, y1) in zip(p, p[1:] + p[:1]))) / 2.0


def _billed_plan(ln, kind, status_by_line):
    """the plan m2 a valued line bills: the line's own stated plan (beam net plan, slab face area); the depth is then
    the line's figure / that plan (route G beams bill 'net plan x H | x (H + t)': the depth used is read back from the
    figure, never assumed). No stated plan: figure / the line's depth. HELD lines bill None."""
    d = _depth(ln, kind)
    if status_by_line.get(ln["line_id"]) != "VALUED":
        return None, d, "HELD"
    v = float(ln["measured_net"])
    plan = ln["dims"].get("net_plan_m2") if kind == "BEAM" else ln["dims"].get("area_m2")
    if plan:
        dep = v / plan
        why = "line plan" + ("" if d is None or abs(dep - d) <= 1e-4 else f"; figure / plan = {dep:.4f} m (line depth {d:.4f})")
        return plan, dep, why
    if not d:
        return None, None, "valued but neither a plan nor a depth on the line"
    return v / d, d, "figure / depth (no plan on the line)"


def _depth(ln, kind):
    dm = ln["dims"]
    d = dm.get("depth_m") if kind == "BEAM" else dm.get("t_m")
    if d is None:
        d = ((ln.get("inputs") or {}).get("info") or {}).get("depth_m")
    return d


def stacked(lines, prof):
    """R-T387-4: neck top vs GF column bottom; each storey column top vs the next storey column bottom."""
    pv = {c["id"]: c.get("base") for c in prof["conventions"]}
    neck_top = pv.get("NECK_TOP_LEVEL_M")
    gf = pv.get("GF_FLOOR_LEVEL_M")
    h = {"GF": pv.get("STOREY_HEIGHT_GF"), "1F": pv.get("STOREY_HEIGHT_1F"), "2F": pv.get("STOREY_HEIGHT_2F")}
    out = []
    chk = R.stacked_check(neck_top, gf, 1.0)
    out.append({"pair": "NECK / COLUMN GF", "lower_top_m": neck_top, "upper_bottom_m": gf,
                "status": chk["status"], "m3_per_m2_section": chk["m3"],
                "basis": "neck = section x (NECK_TOP_LEVEL_M + FOUNDING_DEPTH_M - footing depth); GF column = B x H x "
                         "STOREY_HEIGHT_GF from GF_FLOOR_LEVEL_M"})
    lv = gf
    for a, b in (("GF", "1F"), ("1F", "2F")):
        top = None if lv is None or h[a] is None else lv + h[a]
        chk = R.stacked_check(top, top, 1.0)       # the next column is billed from the same printed floor level
        out.append({"pair": f"COLUMN {a} / COLUMN {b}", "lower_top_m": top, "upper_bottom_m": top,
                    "status": chk["status"], "m3_per_m2_section": chk["m3"],
                    "basis": f"column {a} = storey height floor to floor; column {b} from that floor level"})
        lv = top
    cols = Counter((r["floor"], r["status"]) for r in lines if r["family"] == "COLUMN")
    return out, cols


def column_outlines(geom, lines):
    """COLUMN / COLUMN and NECK / NECK: every pair of drawn column outlines on the column plan (SH12-type sheet) and
    on the foundation plan; a shared outline area is a possible double count of the column lines that sit there."""
    from shapely.geometry import box
    out = []
    for sid, rec in sorted(geom["sheets"].items()):
        cols = [c for c in rec.get("columns") or [] if c.get("box")]
        if not cols:
            continue
        n = 0
        for i, a in enumerate(cols):
            for b in cols[i + 1:]:
                ov = box(*a["box"]).intersection(box(*b["box"])).area * 1e-6
                if ov > R.TOL_M2:
                    n += 1
                    out.append({"sheet": sid, "a": a["member_id"], "b": b["member_id"], "shared_m2": ov})
        out.append({"sheet": sid, "outlines": len(cols), "overlapping_pairs": n})
    return out


T192_REV3 = ROOT / "research/agents_t192/T192_STAIR_LEDGER_REV3.json"


def _by_eid(L, pat):
    return [x for x in L if pat in (x["element_id"] or "")]


def _v(x):
    return None if x is None or x.get("measured_net") is None else float(x["measured_net"])


def pair_register(L, rows, lb, stk, colov, t347, n347):
    """acceptance (b): one row per intersecting FAMILY pair: shared volume billed once (0.000 within 0.001 m3), or the
    named DOUBLE / GAP / RECHECK / UNDETERMINED with its m3 and line ids. Plan pairs come from the level-band check;
    pairs whose geometry is in a merged ledger are re-checked line by line (R-T387-5)."""
    st = {r["line_id"]: r["status"] for r in rows}
    out = []

    def add(pair, scope, method, status, m3, lines, cause):
        out.append({"pair": pair, "scope": scope, "method": method, "status": status,
                    "m3": "" if m3 is None else f"{m3:.6f}", "line_ids": " ".join(lines), "cause": cause})
    for fl, (sid, res, M) in lb.items():
        kinds = Counter(p["kind"] for p in res["pairs"])
        und = [p for p in res["pairs"] if p["status"] == "UNDETERMINED"]
        led = [m for m in res["members"] if m.get("verdict") == "LEDGER_ADJUSTED"]
        rec = [m for m in res["members"] if m.get("verdict") == "RECHECK_BOUNDED"]
        dbl = [m for m in res["members"] if m.get("verdict") is None and m["residual_m2"] > R.TOL_M2 and not m["within_tol"]]
        gap = [m for m in res["members"] if m.get("verdict") is None and m["residual_m2"] < -R.TOL_M2 and not m["within_tol"]]
        add(f"COLUMN / BEAM / SLAB / BEAM-BEAM ({fl} level band, {sid})", f"{len(M)} members, plan pairs {dict(kinds)}",
            "R-T387-3 on route G plan records; billed plan from the candidate line",
            "DOUBLE" if dbl else ("GAP" if gap else ("RECHECK" if rec else ("PASS_HELD" if res["held_members"] else "PASS"))),
            res["double_m3"] if dbl else (res["gap_m3"] if gap else 0.0),
            [i for m in dbl + gap for i in m["line_ids"]],
            f"double {res['double_m3']:.6f} m3, gap {res['gap_m3']:.6f} m3; merged-ledger adjustments "
            f"{res['ledger_adjusted_m3']:.6f} m3 on {len(led)} beam groups (reconciled to 0.001); RECHECK bound "
            f"{res['recheck_bound_m3']:.6f} m3 on {len(rec)} groups; {len(res['held_members'])} held members, "
            f"{len(und)} pairs UNDETERMINED (a held member)")
        for m in rec:
            add(f"BEAM run / neighbours ({fl})", m["id"], "R-T387-6", "RECHECK", m["unexplained_m3"], m["line_ids"],
                m.get("verdict_note", ""))
        for m in gap:
            add(f"BEAM run / band ({fl})", m["id"], "R-T387-3", "GAP", -m["residual_m3"], m["line_ids"],
                "the line bills less than its drawn band and documents no deduction")
    for x in stk:
        add(x["pair"], "every column chain", "R-T387-4 levels of the line formulas", x["status"],
            0.0 if x["status"] == "OK" else None, [], x["basis"])
    for c in colov:
        if "outlines" in c:
            add("COLUMN / COLUMN (drawn outlines)", c["sheet"], "outline pairs", "OK" if not c["overlapping_pairs"]
                else "DOUBLE?", 0.0 if not c["overlapping_pairs"] else None, [],
                f"{c['outlines']} outlines, {c['overlapping_pairs']} overlapping pairs")
    add("FOOTING / NECK / STRAP / GROUND BEAM / BLINDING / POOL (buried)", f"{n347} STR.CONC lines bound by T-347",
        "R-T387-5 carried from T-347 (MERGED 509f90c2: 256 components, double count 0, 30 overlap pairs, F9 / FN and "
        "F8 / FN netted to FN)", t347["status"], 0.0 if t347["status"] == "CARRIED_OK" else None,
        [m[0] for m in t347["moved"]], "every bound line present with its T-347 figure" if not t347["moved"] else
        f"moved: {t347['moved']}")
    # stair / beam (B20, B23) and stair / slab: T-192 rev3 pieces and the full-section beam lines
    rev3 = {p["piece"]: p["rev3_net_m3"] for p in json.loads(T192_REV3.read_text(encoding="utf-8"))["st01_rows"]}
    ms2u = [x for x in L if (x["element_id"] or "").endswith("ST-01:MS2_U")]
    ms2l = [x for x in L if (x["element_id"] or "").endswith("ST-01:MS2_L")]
    ms1 = [x for x in _by_eid(L, "#CLOSABLE:VERIFIED_MS1_LD") if x["item_code"] == "STR.CONC.STAIR"]
    b20 = [x for x in L if cid_of(x["element_id"] or "") == "BEAMS:GF:BAND0043.2"]
    b23 = [x for x in L if cid_of(x["element_id"] or "") == "BEAMS:1F:BAND0031.2"]
    ok = (len(ms2u) == len(ms2l) == len(ms1) == len(b20) == len(b23) == 1
          and abs(_v(ms2u[0]) - rev3["MS2-U"]) <= 1e-6 and abs(_v(ms2l[0]) - rev3["MS2-L"]) <= 1e-6
          and abs(_v(ms1[0]) - (rev3["MS1-U"] + rev3["MS1-LD"])) <= 1e-6
          and abs(_v(b20[0]) - 0.40 * 0.75 * 3.30) <= 1e-6 and abs(_v(b23[0]) - 0.45 * 0.75 * 3.30) <= 1e-6)
    add("STAIR / BEAM (flight heads in B20 / B23, foot of MS2-L in B20)", "ST-01",
        "R-T387-5 carried from T-192 rev3 (MERGED 86fd5f42): stair pieces net of the beam band, beams at full section",
        "CARRIED_OK" if ok else "RECHECK", 0.0 if ok else None,
        [x["line_id"] for x in ms2u + ms2l + ms1 + b20 + b23],
        "MS1-U 0.997552 (inside the MS1 closable line 1.227952 = MS1-U + MS1-LD 0.2304), MS2-U 1.001373, MS2-L "
        "1.033445 = rev3; B20 span 2 0.40 x 0.75 x 3.30 = 0.990, B23 span 2 0.45 x 0.75 x 3.30 = 1.11375 (full section)")
    # held family pairs: listed, never 0
    fam_lines = defaultdict(list)
    for r in rows:
        fam_lines[r["family"]].append(r)
    for fam, pair, why in (
            ("PARAPET", "PARAPET RC / BEAM, SLAB", "4 parapet RC lines HELD blank (T-319: upstand measured ABOVE the beam's "
                                                    "scheduled depth, so no shared volume by its basis; its height is open)"),
            ("NECK", "NECK / GROUND BEAM, GROUND SLAB", "36 neck lines HELD (Q-21 C formation); the ground beams and the "
                                                       "ground slab are billed net of the neck outlines (GROUND level band "
                                                       "PASS on the valued members): the shared volume is in the necks, HELD"),
            ("DOME", "DOME SHELL / DOME RING / SLAB ZONE", "T-160 ring (in-bay) and T-185 shells carried by merged ledgers; "
                                                         "DOME-3 and the east ring HELD; the 1F ring-zone face retired "
                                                         "(not a stair, not a slab)"),
            ("POOL", "POOL BASE / WALLS / STEPS, POOL / F8", "base = outer footprint x 0.40, walls 1.20 above it (T-342 / "
                                                          "T-385, wall foot once); steps HELD; F8 / pool collision 0 .. "
                                                          "1.121 m3 CONFLICT (T-320), never netted"),
            ("STRAP", "STRAP / FOOTING (strap inside a footing outline)", "SB1 / SB3 parts inside F10 / F3 HELD (bounded "
                                                                       "0 .. 0.385 and 0.0295 .. 0.2683, T-347 finding)"),
            ("BLINDING", "BLINDING / FOOTING, GROUND BEAM, STRAP", "all 4 blinding lines HELD (DG-3521554d2fd011b9 and "
                                                                 "blank); plan overlaps of the pits netted in T-347")):
        ls = fam_lines.get(fam, [])
        held = [r for r in ls if r["status"] == "HELD"]
        add(pair, f"{len(ls)} lines, {len(held)} HELD", "listed (held lines never 0)",
            "UNDETERMINED" if held else "OK", None if held else 0.0, [r["line_id"] for r in held], why)
    return out


def carried_t347(cand_by_id):
    """R-T387-5 on the buried pairs: every T-347 bound line (V3.0.24 figure) re-read on the candidate."""
    rows = list(csv.DictReader(open(T347_BINDING, encoding="utf-8")))
    led = {}
    for r in rows:
        if r["binding"] != "BOUND" or not r["line_id"] or not r["line_item_code"].startswith("STR.CONC"):
            continue
        v = r["line_measured"]
        led[r["line_id"]] = float(v) if v not in ("", None) else None
    return R.carried_pair(led, cand_by_id), len(led)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--lines", required=True)
    ap.add_argument("--geometry", required=True)
    ap.add_argument("--downgrades", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    raw = _lines(a.lines)
    L = [flat(x) for x in raw if (x.get("item_code") or "").startswith("STR.CONC")]
    dg = json.loads(Path(a.downgrades).read_text(encoding="utf-8"))["downgrades"]
    rows = R.bind(L, dg)
    status = {r["line_id"]: r["status"] for r in rows}
    by_cid = {cid_of(x["element_id"]): x for x in L if x["element_id"]}
    cand_by_id = {x["line_id"]: x for x in L}
    geom = json.loads(Path(a.geometry).read_text(encoding="utf-8"))
    route_g_cids = {i["component_id"] for i in geom["items"]}
    for r in rows:
        r["geometry"] = "ROUTE_G_PLAN" if cid_of(r["element_id"]) in route_g_cids else "LEDGER_ONLY"
    col_status = defaultdict(Counter)
    for r in rows:
        if r["family"] == "COLUMN":
            col_status[r["floor"]][r["status"]] += 1
        elif r["family"] == "NECK":
            col_status["NECK"][r["status"]] += 1
    live_beams = defaultdict(list)
    for x, r in zip(L, rows):
        if r["family"] == "BEAM" and r["status"] != "NOT_APPLICABLE":
            fl = r["floor"] or (cid_of(x["element_id"] or "").split(":") + ["", ""])[1]
            live_beams[fl].append(x)
        elif r["family"] == "GROUND_BEAM" and r["status"] != "NOT_APPLICABLE":
            live_beams["GROUND"].append(x)
    lb = level_bands(geom, by_cid, status, rows, col_status, live_beams, cand_by_id)
    prof = json.loads(PROFILE.read_text(encoding="utf-8"))
    stk, colcount = stacked(rows, prof)
    t347, n347 = carried_t347(cand_by_id)
    colov = column_outlines(geom, rows)
    reg = pair_register(L, rows, lb, stk, colov, t347, n347)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    with open(out / "BINDING_T387.csv", "w", newline="", encoding="utf-8") as fh:
        k = ["line_id", "item_code", "element_id", "family", "owner_trade", "floor", "binding", "binding_reason",
             "status", "status_reason", "valued_m3", "audit_m3", "geometry"]
        w = csv.DictWriter(fh, fieldnames=k, lineterminator="\n")
        w.writeheader()
        for r in sorted(rows, key=lambda r: (r["family"], r["element_id"], r["line_id"])):
            w.writerow({x: ("" if r[x] is None else (f"{r[x]:.6f}" if isinstance(r[x], float) else r[x])) for x in k})
    pair_rows, member_rows = [], []
    for st, (sid, res, M) in lb.items():
        for p in res["pairs"]:
            pair_rows.append({"floor": st, "a": p["a"], "b": p["b"], "kind": p["kind"],
                              "shared_m2": f"{p['shared_m2']:.6f}",
                              "shared_m3": "" if p["shared_m3"] is None else f"{p['shared_m3']:.6f}",
                              "owner": p["owner"] or "", "status": p["status"],
                              "lines_a": " ".join(p["lines_a"]), "lines_b": " ".join(p["lines_b"])})
        for m in res["members"]:
            if m["kind"] == "COLUMN":
                continue
            member_rows.append({"floor": st, "member": m["id"], "kind": m["kind"], "drawn_m2": f"{m['drawn_m2']:.6f}",
                                "owned_m2": f"{m['owned_m2']:.6f}", "billed_m2": f"{m['billed_m2']:.6f}",
                                "residual_m2": f"{m['residual_m2']:.6f}",
                                "residual_m3": "" if m["residual_m3"] is None else f"{m['residual_m3']:.6f}",
                                "depth_m": "" if m["depth_m"] is None else f"{m['depth_m']:.4f}",
                                "verdict": m["verdict"] or ("DOUBLE" if m["residual_m2"] > R.TOL_M2 else
                                            "GAP" if m["residual_m2"] < -R.TOL_M2 else "OK"),
                                "documented_m3": "" if m.get("documented_m3") is None else f"{m['documented_m3']:.6f}",
                                "unexplained_m3": "" if m.get("unexplained_m3") is None else f"{m['unexplained_m3']:.6f}",
                                "line_ids": " ".join(m["line_ids"]),
                                "basis": "; ".join(x for x in (M[m["id"]].get("why", ""), m.get("verdict_note", "")) if x)})
        for mid in res["held_members"]:
            x = M[mid]
            member_rows.append({"floor": st, "member": mid, "kind": x["kind"], "drawn_m2": "", "owned_m2": "",
                                "billed_m2": "", "residual_m2": "", "residual_m3": "",
                                "depth_m": "" if x["depth_m"] is None else f"{x['depth_m']:.4f}", "verdict": "HELD",
                                "documented_m3": "", "unexplained_m3": "",
                                "line_ids": " ".join(x["line_ids"]), "basis": "line HELD: never 0, pairs UNDETERMINED"})
        for mid, kind in res["unlined_members"]:
            member_rows.append({"floor": st, "member": mid, "kind": kind, "drawn_m2": "", "owned_m2": "",
                                "billed_m2": "", "residual_m2": "", "residual_m3": "", "depth_m": "",
                                "verdict": "SUPERSEDED_OR_CARRIED" if mid in res["successor"] else "NO_LINE",
                                "documented_m3": "", "unexplained_m3": "", "line_ids": "",
                                "basis": res["successor"].get(mid, "route G member with no live candidate line")})
    for name, rr in (("PAIRS_T387.csv", pair_rows), ("MEMBERS_T387.csv", member_rows),
                     ("PAIR_REGISTER_T387.csv", reg)):
        with open(out / name, "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=list(rr[0].keys()), lineterminator="\n")
            w.writeheader()
            w.writerows(rr)
    summ = {"schema": "T387_SUMMARY_V1", "candidate": CANDIDATE, "lines_json_sha256": _sha(a.lines),
            "downgrades_sha256": _sha(a.downgrades), "geometry": geom.get("schema"),
            "structural_concrete_lines": len(rows),
            "binding": Counter(r["binding"] for r in rows), "status": Counter(r["status"] for r in rows),
            "geometry_source": Counter(r["geometry"] for r in rows),
            "unbound": [(r["line_id"], r["binding_reason"]) for r in rows if r["binding"] == "UNBOUND"],
            "families": R.totals(rows),
            "level_bands": {st: {"sheet": sid, "status": res["status"], "column_boxes": res["column_boxes"],
                                 "double_m2": round(res["double_m2"], 6), "double_m3": round(res["double_m3"], 6),
                                 "gap_m2": round(res["gap_m2"], 6), "gap_m3": round(res["gap_m3"], 6),
                                 "arc_chord_faces_resolved": res["chord_resolved"],
                                 "ledger_adjusted_m3": round(res["ledger_adjusted_m3"], 6),
                                 "recheck_bounded_m3": round(res["recheck_bound_m3"], 6),
                                 "held_members": len(res["held_members"]),
                                 "unlined_members": res["unlined_members"],
                                 "not_members_na": len(res["not_members"]),
                                 "pairs": Counter(p["status"] for p in res["pairs"])}
                            for st, (sid, res, M) in lb.items()},
            "stacked": stk, "column_lines_by_floor_status": {f"{a}|{b}": n for (a, b), n in sorted(colcount.items())},
            "t347_carried": {"lines": n347, **t347}, "column_outlines": colov,
            "pair_register": Counter(r["status"] for r in reg)}
    (out / "summary_t387.json").write_text(json.dumps(summ, indent=1, sort_keys=True, default=str) + "\n",
                                           encoding="utf-8")
    print(json.dumps({k: summ[k] for k in ("structural_concrete_lines", "binding", "status", "level_bands")},
                     indent=1, default=str))


if __name__ == "__main__":
    main()
