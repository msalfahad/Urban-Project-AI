"""T-610 development-villa census (research, unwired): every beam-beam band intersection on the GF / 1F / 2F roof-slab
plans, measured once under R-T610-1 (t610_rules.py), against the candidate of record's STR.CONC.BEAM lines.

    .work/venv/bin/python -I research/agents_t610/t610_alsenan.py <structural.dxf> [--write | --check]

Inputs: Drive 'Alsenan chalet project' / 'ST7757 dxf.dxf' (sha256 9f9d1179..; decoded to .work/private only), read by
route G exactly as ARCH_TAKEOFF_V3.0.x does (tools/urban_boq_m2.compute, M8 V6 conventions, M4 profile); candidate
lines research/agents_t507/out/LINE_INDEX_V3_0_57.json (beam values equal in V3.0.58, R-T507-1 (e)); ledger runs
research/agents_t252/LEDGER_T252.csv (HL:BEAM_LEDGER lines). Tracked output (out/): band ids, marks, line ids, areas,
depths and volumes only; no coordinate, no drawing content.

Member plans:
  DRAWN   per route G band: the hull of its drawn face segments (straight bands; the drawn end edges kept), the
          route G polygon for an ARC band (its faces are arcs); split between the band's pieces at the mid point of
          each column cut; net of every column outline that is not wholly inside the band (a column wholly inside
          the band is CARRIED: the beam runs under it, T-229 / ST p.15).
  BILLED  a route G line (P-C): its rectangle minus the junction squares route G deducts from it (beam_quantities:
          the square goes to the longer band), applied geometrically; a ledger line (HL, T-229 / T-252 runs): the
          union of its pieces' billed plans and the drawn band beyond them up to every other member's plan (the
          T-229 _beyond construction), checked against the ledger value (residual reported per line).
"""
from __future__ import annotations

import csv
import hashlib
import json
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(HERE))

import t610_rules as R  # noqa: E402

LINE_INDEX = ROOT / "research/agents_t507/out/LINE_INDEX_V3_0_57.json"
LEDGER = ROOT / "research/agents_t252/LEDGER_T252.csv"
CONV = ROOT / "engine/profiles/URBAN_M8_GENERIC_CONVENTIONS_V6.json"
M4 = ROOT / "research/urban_engine_m4_correctness/profile_st7757_m4.json"
OUT = HERE / "out"
JSON_OUT = OUT / "T610_BEAM_OVERLAP_CENSUS.json"
MD_OUT = OUT / "T610_BEAM_OVERLAP_CENSUS.md"
DXF_SHA = "9f9d1179a5d2a6635f9b412915a72184b7db1ff7729f4ab39a72dc3391738079"
SHEETS = {"GF": "SH06", "1F": "SH04", "2F": "SH02"}
CAP_FACTOR = 1.0                     # oblique drawn end: a face may run on by at most this x the band width
LEDGER_TOL_M3 = 0.01                 # a ledger plan model within this of the ledger value is MODEL_MATCHES


def r6(x):
    return None if x is None else round(float(x), 6)


def load_lines():
    d = json.loads(LINE_INDEX.read_text(encoding="utf-8"))
    assert d["candidate_version"] == "ARCH_TAKEOFF_V3.0.57"
    return [ln for ln in d["lines"] if ln["item_code"] == "STR.CONC.BEAM"]


def load_ledger():
    rows = {}
    for r in csv.DictReader(LEDGER.open(encoding="utf-8")):
        if r["status"] == "SUPERSEDED_R2":
            continue
        rows[r["run"]] = r
    return rows


def route_g(dxf):
    from tools import urban_boq_m2 as M2
    return M2.compute([str(dxf)], conventions=str(CONV), profile=str(M4), route="G", completeness=False)


def _t(pt, u):
    return pt[0] * u[0] + pt[1] * u[1]


def _face_quad(b, segs):
    """The drawn band in its own frame: face A's drawn extent on the lo offset line, face B's on the hi offset line
    (each face's segments projected on the band axis), joined by the drawn end edges (oblique where the two faces stop
    at different stations, e.g. one at a column corner and the other at the column face)."""
    from shapely.geometry import Polygon
    u, lo, hi = b["u"], b["lo_off"], b["hi_off"]
    n = (-u[1], u[0])

    def ext(hs):
        ts = [_t(segs[h][k], u) for h in hs for k in ("a", "b")]
        return min(ts), max(ts)

    offa = sum(segs[h]["a"][0] * n[0] + segs[h]["a"][1] * n[1] for h in b["faces_a"]) / len(b["faces_a"])
    la, lb = (lo, hi) if abs(offa - lo) <= abs(offa - hi) else (hi, lo)
    a0, a1 = ext(b["faces_a"])
    b0, b1 = ext(b["faces_b"])
    # where both faces are drawn the band is certain; past that, a face that runs on by no more than one band width
    # is the oblique drawn end (one face stops at a column / member face, the other at its corner); a face that runs
    # on further is a longer line (slab edge, a face shared with the next member) and the band ends with its partner
    cap = CAP_FACTOR * abs(hi - lo) + 1.0
    t0, t1 = max(a0, b0), min(a1, b1)
    a0, b0 = [x if t0 - x <= cap else t0 for x in (a0, b0)]
    a1, b1 = [x if x - t1 <= cap else t1 for x in (a1, b1)]

    def P(t, o):
        return (u[0] * t + n[0] * o, u[1] * t + n[1] * o)
    return Polygon([P(a0, la), P(a1, la), P(b1, lb), P(b0, lb)]).buffer(0)


def storey_members(G, sid, st):
    """Per route G piece: drawn plan (metres, sheet-local), billed rectangle plan, depth, mark."""
    from shapely.geometry import Polygon, box
    from shapely.affinity import affine_transform
    from shapely.ops import unary_union
    rec = G["D"]["sheets"][sid]
    u_m = G["D"]["unit_m"]
    ox, oy = rec["sheet"]["origin"]
    segs = {s["id"]: s for s in G["intake"]["segments"]}
    to_m = [u_m, 0, 0, u_m, -ox * u_m, -oy * u_m]

    def M(g):
        return R.snap(affine_transform(g, to_m))

    bands = {b["band_id"]: b for b in rec["bands"]}
    beams = {b["band_id"]: b for b in rec["beams"]}
    cols_native = [box(*c[:4]) for c in sorted(set(tuple(c[:4]) for c in
                                                   list(rec["column_boxes"]) + list(rec.get("slab_column_boxes") or [])))]
    # the slab arrangement's COLUMN faces (column outlines the slab reads, also those not in the box lists)
    seen = {tuple(round(v, 1) for v in c.bounds) for c in cols_native}
    for f in (rec.get("slab") or {}).get("faces", []):
        if f.get("class") == "COLUMN" and len(f["polygon"]) >= 3:
            c = Polygon(f["polygon"]).buffer(0)
            key = tuple(round(v, 1) for v in c.bounds)
            if key not in seen:
                seen.add(key)
                cols_native.append(c)
    # a column outline with a PATTERN hatch (S-COL.HAT ANSI35) is a member that STARTS on this slab (T-229 census;
    # ST p.15 'beam carrying planted column': the beam runs at full depth under it); a SOLID hatch is a column below
    carried_hatches = [Polygon(h["ring"]).buffer(0) for h in G["intake"]["hatches"]
                       if h.get("layer") == "S-COL.HAT" and h.get("pattern") == "ANSI35" and len(h["ring"]) >= 3]
    # parents: drawn hull per parent band
    parents = defaultdict(list)
    for bid, b in bands.items():
        parents[b.get("parent") or bid].append(bid)
    drawn_parent, carried = {}, set()
    for par, kids in parents.items():
        b0 = bands[kids[0]]
        if b0["kind"] == "STRAIGHT":
            hull = _face_quad(b0, segs)
        else:
            hull = Polygon(b0["polygon"]).buffer(0)
        for k, c in enumerate(cols_native):
            if c.area and any(c.intersection(h).area / c.area > 0.9 for h in carried_hatches) and \
                    hull.intersection(c).area / c.area > 0.999:
                carried.add(k)
        drawn_parent[par] = hull
    support_cols = unary_union([c for k, c in enumerate(cols_native) if k not in carried])
    # split each parent hull between its pieces at the mid point of each cut along the band axis
    drawn = {}
    for par, kids in parents.items():
        hull = drawn_parent[par]
        if len(kids) == 1:
            drawn[kids[0]] = hull
            continue
        b0 = bands[kids[0]]
        u = b0["u"]
        ks = sorted(kids, key=lambda k: bands[k]["t0"])
        bounds = [-1e12] + [(bands[a]["t1"] + bands[b]["t0"]) / 2 for a, b in zip(ks, ks[1:])] + [1e12]
        n = (-u[1], u[0])
        for k, lo, hi in zip(ks, bounds, bounds[1:]):
            big = 1e7
            slab = Polygon([(u[0] * lo + n[0] * -big, u[1] * lo + n[1] * -big),
                            (u[0] * hi + n[0] * -big, u[1] * hi + n[1] * -big),
                            (u[0] * hi + n[0] * big, u[1] * hi + n[1] * big),
                            (u[0] * lo + n[0] * big, u[1] * lo + n[1] * big)])
            drawn[k] = hull.intersection(slab)
    rect = {bid: Polygon(b["polygon"]).buffer(0) for bid, b in beams.items()}
    billed = {}
    for bid, b in beams.items():
        g = rect[bid]
        for dd in b.get("junction_deductions") or []:
            g = g.difference(rect[dd["owner"]])
        billed[bid] = g
    out = {}
    for bid, b in beams.items():
        out[bid] = {"band": bid, "parent": bands[bid].get("parent") or bid, "kind": b["kind"],
                    "mark": b.get("mark"), "state": b["state"], "depth_m": b.get("depth_m"),
                    "drawn": M(drawn[bid].difference(support_cols)), "rect": M(rect[bid]), "billed": M(billed[bid]),
                    "engine_net_plan_m2": b.get("net_plan_m2"), "engine_v_m3": b.get("v_total_depth")}
    return out, M(support_cols), len(carried)


def slab_panels(G, sid):
    """The route G slab faces of class PANEL (the slab line's plan), metres, sheet-local."""
    from shapely.geometry import Polygon
    from shapely.affinity import affine_transform
    rec = G["D"]["sheets"][sid]
    u_m = G["D"]["unit_m"]
    ox, oy = rec["sheet"]["origin"]
    to_m = [u_m, 0, 0, u_m, -ox * u_m, -oy * u_m]
    fs = [Polygon(f["polygon"]).buffer(0) for f in (rec.get("slab") or {}).get("faces", [])
          if f.get("class") == "PANEL"]
    return R.snap(affine_transform(R.union(fs), to_m))


def line_members(lines, ledger, members, st):
    """Candidate line -> (pieces, depth, billed plan, valued m3, class); piece -> line."""
    from shapely.ops import unary_union
    piece_line, recs = {}, {}
    for ln in lines:
        eid = ln["element_id"]
        parts = eid.split(":")
        if eid.startswith(("P-C:BEAMS:", "U-C:BEAMS:")) and parts[2] == st:
            band = parts[3]
            if band in members:
                recs[ln["line_id"]] = {"line_id": ln["line_id"], "element_id": eid, "class": ln["class"],
                                       "pieces": [band], "kind": "ROUTE_G", "value_m3": ln["measured_net"]}
        elif eid.startswith("HL:BEAM_LEDGER:") and parts[2] == st:
            run = eid.split(":", 3)[3]
            row = ledger[run]
            pcs = [p.split(":")[1] for p in row["pieces"].split("|") if p.startswith(st + ":")]
            recs[ln["line_id"]] = {"line_id": ln["line_id"], "element_id": eid, "class": ln["class"],
                                   "pieces": [p for p in pcs if p in members], "kind": "LEDGER",
                                   "value_m3": ln["measured_net"], "ledger_depth_m": float(row["depth_m"]) if row["depth_m"] else None,
                                   "mark": row["mark"]}
    # a piece belongs to its RELEASED / HELD line first (a ledger run replaces the EXCLUDED route G piece line)
    for pref in ("RELEASED", "HELD", "EXCLUDED"):
        for lid, r in sorted(recs.items()):
            if r["class"] != pref:
                continue
            for p in r["pieces"]:
                piece_line.setdefault(p, lid)
    for lid, r in recs.items():
        own = [p for p in r["pieces"] if piece_line.get(p) == lid]
        r["own_pieces"] = own
        if not own:
            r["billed"], r["drawn"] = None, None
            continue
        r["drawn"] = R.union([members[p]["drawn"] for p in own])
        if r["kind"] == "ROUTE_G":
            m = members[own[0]]
            r["depth_m"] = m["depth_m"]
            r["mark"] = m["mark"]
            r["billed"] = m["billed"] if r["class"] == "RELEASED" else None
        else:
            r["depth_m"] = r["ledger_depth_m"]
            others = R.union([m["rect"] for k, m in members.items() if k not in own])
            beyond = R.minus(r["drawn"], others)
            r["billed"] = R.union([members[p]["billed"] for p in own] + [beyond]) if r["class"] == "RELEASED" \
                else None
            if r["billed"] is not None and r["value_m3"] is not None:
                model = r["billed"].area * r["depth_m"]
                r["ledger_model_m3"] = model
                r["ledger_residual_m3"] = r["value_m3"] - model
                r["ledger_model_state"] = "MODEL_MATCHES" if abs(r["ledger_residual_m3"]) <= LEDGER_TOL_M3 \
                    else "MODEL_RESIDUAL"
    return recs, piece_line


def census(G, lines, ledger):
    from shapely.ops import unary_union
    zones, line_checks, per_storey, billed_twice = [], [], {}, []
    for st, sid in SHEETS.items():
        members, cols, n_carried = storey_members(G, sid, st)
        slab = slab_panels(G, sid)
        recs, piece_line = line_members(lines, ledger, members, st)
        live = {lid: r for lid, r in recs.items() if r.get("drawn") is not None}
        ids = sorted(live)
        tot = defaultdict(float)
        cnt = defaultdict(int)
        for i, a in enumerate(ids):
            for b in ids[i + 1:]:
                A, B = live[a], live[b]
                MA = {"id": a, "depth_m": A["depth_m"] if A["class"] == "RELEASED" else None,
                      "billed_poly": A["billed"]}
                MB = {"id": b, "depth_m": B["depth_m"] if B["class"] == "RELEASED" else None,
                      "billed_poly": B["billed"]}
                z = R.zone(A["drawn"], B["drawn"], [cols]) if A["drawn"].intersects(B["drawn"]) else None
                outside = R.billed_outside_zone(z if z is not None else R.Polygon(), MA, MB) \
                    if (A["billed"] is not None and B["billed"] is not None) else None
                if outside:
                    billed_twice.append({"storey": st, "A": a, "B": b, "marks": [A.get("mark"), B.get("mark")],
                                         **{k: (r6(v) if isinstance(v, float) else v) for k, v in outside.items()}})
                if z is None or z.area < R.EPS_M2:
                    continue
                rec = R.account_zone(z, MA, MB)
                if rec["in_neither_m2"] > R.EPS_M2:
                    nb = R.minus(z, R.union([MA["billed_poly"], MB["billed_poly"]]))
                    rec["neither_in_slab_panel_m2"] = R.inter(nb, slab).area
                own = R.owner_split(rec, MA, MB)
                third = [k for k in ids if k not in (a, b) and R.inter(live[k]["drawn"], z).area > R.EPS_M2]
                row = {"storey": st, "sheet": sid,
                       "A": {"line_id": a, "element_id": A["element_id"], "class": A["class"], "mark": A.get("mark"),
                             "pieces": A["own_pieces"], "depth_m": A.get("depth_m")},
                       "B": {"line_id": b, "element_id": B["element_id"], "class": B["class"], "mark": B.get("mark"),
                             "pieces": B["own_pieces"], "depth_m": B.get("depth_m")},
                       **{k: (r6(v) if isinstance(v, float) else v) for k, v in rec.items()},
                       "third_member_in_zone": third}
                if own:
                    row["owner_deeper"] = {"owner": own["owner"],
                                           "lines": {k: {kk: r6(vv) for kk, vv in v.items()}
                                                     for k, v in own["lines"].items()}}
                zones.append(row)
                cnt[rec["verdict"]] += 1
                if rec["state"] == "MEASURED":
                    for k in ("zone_m2", "physical_m3", "engine_m3", "engine_minus_physical_m3", "DOUBLE_m3",
                              "DEPTH_m3", "OMISSION_m3"):
                        tot[k] += rec[k]
                else:
                    tot["held_zone_m2"] += rec["zone_m2"]
        for lid, r in sorted(recs.items()):
            if r["kind"] == "LEDGER" and "ledger_model_m3" in r:
                line_checks.append({"storey": st, "line_id": lid, "element_id": r["element_id"],
                                    "mark": r["mark"], "value_m3": r6(r["value_m3"]),
                                    "plan_model_m3": r6(r["ledger_model_m3"]),
                                    "residual_m3": r6(r["ledger_residual_m3"]), "state": r["ledger_model_state"]})
        per_storey[st] = {"sheet": sid, "lines": len(recs), "lines_with_plan": len(live),
                          "carried_columns_kept_in_beams": n_carried, "zones": sum(cnt.values()),
                          "zones_by_verdict": dict(sorted(cnt.items())),
                          **{k: r6(v) for k, v in sorted(tot.items())}}
    return zones, line_checks, per_storey, billed_twice


def fix_rows(zones):
    rows, n = [], 0
    for z in zones:
        if z["state"] != "MEASURED" or abs(z["engine_minus_physical_m3"]) <= 1e-6:
            continue
        n += 1
        own = z["owner_deeper"]
        rows.append({"id": f"FR-T610-{n}", "storey": z["storey"],
                     "pair": f"{z['A']['mark']} ({z['A']['line_id']}) x {z['B']['mark']} ({z['B']['line_id']})",
                     "verdict": z["verdict"], "zone_m2": z["zone_m2"], "engine_minus_physical_m3":
                         z["engine_minus_physical_m3"], "DOUBLE_m3": z["DOUBLE_m3"], "DEPTH_m3": z["DEPTH_m3"],
                     "OMISSION_m3": z["OMISSION_m3"], "owner_deeper": own["owner"],
                     "line_changes_m3": {k: v["change_m3"] for k, v in own["lines"].items()}})
    return rows


def fcp032(zones):
    """F-C-P03-2 (Checker 16:57): GF B1 BAND0029.4 against the B27 run; reproduced to 1e-6."""
    z = [z for z in zones if z["storey"] == "GF" and
         {"BAND0029.4"} & set(z["A"]["pieces"] + z["B"]["pieces"]) and
         "B27" in (z["A"]["mark"], z["B"]["mark"])]
    assert len(z) == 1, z
    z = z[0]
    b1 = "A" if z["A"]["mark"] == "B1" else "B"
    b27 = "B" if b1 == "A" else "A"
    b1_in = z["in_A_only_m2"] if b1 == "A" else z["in_B_only_m2"]
    b27_in = z["in_B_only_m2"] if b1 == "A" else z["in_A_only_m2"]
    return {"zone_m2": z["zone_m2"], "checker_overlap_m2": 0.014761, "B1_bills_m2": b1_in,
            "B27_run_bills_m2": b27_in, "both_m2": z["in_both_m2"], "neither_m2": z["in_neither_m2"],
            "B1_line_excess_vs_net_m3": r6(b1_in * z[b1]["depth_m"]), "checker_B1_m3": 0.005295,
            "physical_m3": z["physical_m3"], "engine_m3": z["engine_m3"],
            "engine_minus_physical_m3": z["engine_minus_physical_m3"], "verdict": z["verdict"],
            "owner_deeper": z["owner_deeper"]}


def build(dxf):
    sha = hashlib.sha256(Path(dxf).read_bytes()).hexdigest()
    assert sha == DXF_SHA, sha
    G = route_g(dxf)["generic"]
    global CAP_FACTOR
    lines, ledger = load_lines(), load_ledger()
    sens = {}
    for cf in (0.0, 2.0):
        CAP_FACTOR = cf
        zs, _, pr, tw = census(G, lines, ledger)
        sens[f"cap {cf:g} x width"] = {
            "per_storey_engine_minus_physical_m3": {st: p.get("engine_minus_physical_m3") for st, p in pr.items()},
            "fix_rows": [f"{f['storey']} {f['pair'].split(' (')[0]} x {f['pair'].split(' x ')[1].split(' (')[0]} "
                         f"{f['engine_minus_physical_m3']}" for f in fix_rows(zs)],
            "billed_twice_outside": len(tw)}
    CAP_FACTOR = 1.0
    zones, checks, per, twice = census(G, lines, ledger)
    out = {"schema": "T610_BEAM_OVERLAP_CENSUS_V1", "rule": R.RULE_ID, "candidate": "ARCH_TAKEOFF_V3.0.57 (= V3.0.58 "
           "for STR.CONC.BEAM)", "source": "Drive 'Alsenan chalet project' / 'ST7757 dxf.dxf' (sha256 9f9d1179..)",
           "per_storey": per, "ledger_plan_checks": checks, "billed_twice_outside_drawn_zones": twice, "zones": zones, "fix_rows": fix_rows(zones),
           "F_C_P03_2": fcp032(zones),
           "sensitivity_oblique_end_cap": {"base": "cap 1 x width (the census above)", **sens},
           "note": "areas m2, volumes m3, depths m (schedule, full depth to slab top as the candidate bills); no "
                   "coordinate. engine = the candidate line's billed plan in the zone x its depth; physical = zone x "
                   "deeper depth (R-T610-1 (b)); HELD = a member line not valued (depth not released)."}
    return out


def render_md(d):
    L = ["# T-610 beam band overlap census (R-T610-1, research, unwired)", "",
         f"Candidate {d['candidate']}; {d['source']}. Areas m2, volumes m3.", "",
         "| storey | lines | zones | verdicts | zone m2 | engine m3 | physical m3 | engine - physical | DOUBLE | DEPTH "
         "| OMISSION | HELD zone m2 |", "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for st, p in d["per_storey"].items():
        L.append(f"| {st} | {p['lines_with_plan']} | {p['zones']} | "
                 f"{', '.join(f'{k} {v}' for k, v in p['zones_by_verdict'].items())} | {p.get('zone_m2')} | "
                 f"{p.get('engine_m3')} | {p.get('physical_m3')} | {p.get('engine_minus_physical_m3')} | "
                 f"{p.get('DOUBLE_m3')} | {p.get('DEPTH_m3')} | {p.get('OMISSION_m3')} | {p.get('held_zone_m2')} |")
    L += ["", "## Zones (pair by pair)", "",
          "| storey | A mark (line, class) | B mark (line, class) | zone m2 | dA / dB | A only | B only | both | "
          "neither | engine m3 | physical m3 | diff | verdict | owner (deeper) |", "|" + "---|" * 14]
    for z in d["zones"]:
        L.append(f"| {z['storey']} | {z['A']['mark']} ({z['A']['line_id']}, {z['A']['class']}) | {z['B']['mark']} "
                 f"({z['B']['line_id']}, {z['B']['class']}) | {z['zone_m2']} | {z['A']['depth_m']} / "
                 f"{z['B']['depth_m']} | {z['in_A_only_m2']} | {z['in_B_only_m2']} | {z['in_both_m2']} | "
                 f"{z['in_neither_m2']} | {z.get('engine_m3')} | {z.get('physical_m3')} | "
                 f"{z.get('engine_minus_physical_m3')} | {z['verdict']} | "
                 f"{(z.get('owner_deeper') or {}).get('owner', '-')} |")
    L += ["", "## Fix rows", ""]
    for f in d["fix_rows"]:
        L.append(f"- {f['id']} {f['storey']} {f['pair']}: {f['verdict']}, zone {f['zone_m2']} m2, engine - physical "
                 f"{f['engine_minus_physical_m3']} m3 (DOUBLE {f['DOUBLE_m3']}, DEPTH {f['DEPTH_m3']}, OMISSION "
                 f"{f['OMISSION_m3']}); owner {f['owner_deeper']}; line changes {f['line_changes_m3']}")
    L += ["", "## Plan billed by two lines outside every drawn common block", "",
          f"{len(d['billed_twice_outside_drawn_zones'])} pair(s): "
          + ("; ".join(f"{x['storey']} {x['marks']} {x['billed_twice_outside_zone_m2']} m2"
                       for x in d["billed_twice_outside_drawn_zones"]) or "none (route G junction squares are "
                                                                            "deducted once; ledger runs stop at "
                                                                            "other members' plans)")]
    L += ["", "## Sensitivity: oblique drawn end cap (a face running on past its partner)", ""]
    for k, v in d["sensitivity_oblique_end_cap"].items():
        L.append(f"- {k}: {v}")
    L += ["", "## Ledger plan checks (HL lines)", ""]
    for c in d["ledger_plan_checks"]:
        L.append(f"- {c['storey']} {c['mark']} {c['line_id']}: ledger {c['value_m3']} vs plan model "
                 f"{c['plan_model_m3']} (residual {c['residual_m3']}) {c['state']}")
    L += ["", "## F-C-P03-2", "", "```", json.dumps(d["F_C_P03_2"], indent=1), "```", ""]
    return "\n".join(L)


def main(argv):
    dxf = argv[0]
    d = build(dxf)
    js = json.dumps(d, indent=1, sort_keys=True) + "\n"
    md = render_md(d) + "\n"
    if "--write" in argv:
        OUT.mkdir(exist_ok=True)
        JSON_OUT.write_text(js, encoding="utf-8")
        MD_OUT.write_text(md, encoding="utf-8")
    elif "--check" in argv:
        if JSON_OUT.read_text(encoding="utf-8") != js or MD_OUT.read_text(encoding="utf-8") != md:
            print("T-610 census differs from out/")
            return 1
    if "--top" in argv:
        for z in sorted(d["zones"], key=lambda z: -abs(z.get("engine_minus_physical_m3") or 0))[:200]:
            print(z["storey"], z["A"]["mark"], z["A"]["pieces"], z["A"]["class"], z["A"]["element_id"][:22], "|",
                  z["B"]["mark"], z["B"]["pieces"], z["B"]["class"], z["B"]["element_id"][:22], "| zone",
                  z["zone_m2"], "Aonly", z["in_A_only_m2"], "Bonly", z["in_B_only_m2"], "both", z["in_both_m2"],
                  "none", z["in_neither_m2"], "diff", z.get("engine_minus_physical_m3"), z["verdict"], z["A"]["depth_m"], z["B"]["depth_m"],
                  z["third_member_in_zone"][:3])
        for c in d["ledger_plan_checks"]:
            print(c)
    print(json.dumps({"per_storey": d["per_storey"], "F_C_P03_2": d["F_C_P03_2"],
                      "fix_rows": len(d["fix_rows"])}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
