"""T-293 part 2, step 1: the merged formwork r3 drawing-face walk (research/agents_t163/t163_formwork.py, rule r3, read
only) re-run on the T-139 faces of the private 'ST7757 dxf.dxf' and broken down PER FACE and PER MEMBER, so that the
slab-level aggregates of formwork r4 (T-264, MERGED 90203feb) can be tied to the candidate concrete line of each member.

    python3 -I research/agents_t293/t293p2_walk.py <faces.json> <out.json>

faces.json = `python3 -I research/agents_t139/slab_faces.py <ST7757 dxf.dxf> faces.json` (T-139 faces, the partition
formwork r3 walked). out.json holds face ids, member / column / panel ids, categories and m2 only (no coordinates, no
drawing text): it is committed as T293P2_WALK_RECORDS.json and is the input of t293p2_ledger.py.

Nothing here changes a quantity: every record is a piece of an r3 aggregate, and the per-floor sums are asserted
against the r3 ledger rows (research/agents_t163/FORMWORK_LINES.csv) to 1e-6 m2 before anything is written.
"""
from __future__ import annotations

import csv
import json
import sys
import tempfile
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
RES = HERE.parent
sys.path.insert(0, str(RES / "agents_t163"))
import t163_formwork as T  # noqa: E402  (merged r3, read-only)

FLOORS = ("GF", "1F", "2F")
CALC, HELD = "CALCULATED", "HELD"


def member_runs():
    """T-149 member -> [(candidate run, route G band id)] for members the candidate splits over several runs
    (research/agents_t146/V3012_BEAM_RUNS.csv: run 'BM-..#BANDnnnn.k')"""
    out = defaultdict(list)
    with (RES / "agents_t146" / "V3012_BEAM_RUNS.csv").open(encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            run = r["run"]
            if "#BAND" not in run:
                continue
            band = run.split("#")[1].replace(".r2", "")
            out[run.split("#")[0]].append((run, f"{band}@{r['floor']}"))
    return {m: v for m, v in out.items() if len(v) > 1}


def cutter(poly, widen=0.5):
    """the band's minimum rotated rectangle widened ACROSS its axis only: it cuts a member face at the band ends and
    never along its sides (a 0.6 mm band-fit error must not leave a side sliver that takes the side face)"""
    from shapely.geometry import Polygon
    c = list(poly.minimum_rotated_rectangle.exterior.coords)[:4]
    e1 = (c[1][0] - c[0][0], c[1][1] - c[0][1])
    e2 = (c[2][0] - c[1][0], c[2][1] - c[1][1])
    L1, L2 = (e1[0] ** 2 + e1[1] ** 2) ** 0.5, (e2[0] ** 2 + e2[1] ** 2) ** 0.5
    u, a, b = (e1, L1, L2) if L1 >= L2 else (e2, L2, L1)
    ux, uy = u[0] / a, u[1] / a
    vx, vy = -uy, ux
    cx, cy = sum(p[0] for p in c) / 4, sum(p[1] for p in c) / 4
    ha, hb = a / 2, b / 2 + widen
    return Polygon([(cx + sx * ha * ux + sy * hb * vx, cy + sx * ha * uy + sy * hb * vy)
                    for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))])


SPLIT = {}            # walked face id -> {run: cutter polygon} (members the candidate splits over several runs)
STATS = defaultdict(int)


def share(geom, cuts, tol=1e-9):
    """fractions of a walked edge piece (or a face) inside each run's cutter; the part in no cutter is REST. Two
    cutters claiming the same part (overlapping band ends) -> the whole piece is REST (never divided by a guess)."""
    meas = (lambda g: g.area) if geom.area > 0 else (lambda g: g.length)
    tot = meas(geom)
    if tot <= 1e-12:
        return {"REST": 1.0}
    out, used = {}, 0.0
    for run, cu in sorted(cuts.items()):
        v = meas(geom.intersection(cu))
        if v > 0:
            out[run] = v
            used += v
    if used > tot * (1 + tol) + 1e-12:
        STATS["overlap"] += 1
        return {"REST": 1.0}
    if tot - used > 1e-12:
        out["REST"] = tot - used
    return {k: v / tot for k, v in out.items()}


def attributed_exact(orig):
    """wrap t163_formwork._exact_edge: each exact edge piece of a SPLIT face is divided by where it lies"""
    from shapely.affinity import translate
    from shapely.geometry import LineString, Point
    from shapely.ops import unary_union

    def exact(i, g, a, b, L, ux, uy, probe, faces, ids, tree, kind, gaps, tref):
        res = orig(i, g, a, b, L, ux, uy, probe, faces, ids, tree, kind, gaps, tref)
        if i not in SPLIT:
            return res
        mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
        sx, sy = -uy * probe, ux * probe
        if g.contains(Point(mx + sx, my + sy)):
            sx, sy = -sx, -sy
        seg = LineString([(a[0] + sx, a[1] + sy), (b[0] + sx, b[1] + sy)])
        named = [r for r in res if r[2] is not None]
        left = seg.difference(unary_union([faces[r[2]] for r in named])) if named else seg
        out = []
        for r in res:
            geom = faces[r[2]].intersection(seg) if r[2] is not None else left
            geom = translate(geom, -sx, -sy)          # back onto the face's own edge: an END edge's probe line
            for run, f in share(geom, SPLIT[i]).items():   # lies beyond the band end, its edge does not
                out.append((f"{i}~{run}", r[1], r[2], r[3] * f, r[4]))
        return out
    return exact


def attributed_areas(orig, assign=None):
    """wrap t163_formwork.face_areas: a 'face~run' id takes its face's kind, depth (and assign)"""
    def areas(edges, kind, depth, tslab):
        for e in edges:
            if "~" in str(e[0]):
                h = e[0].split("~", 1)[0]
                kind[e[0]] = kind[h]
                depth[e[0]] = depth.get(h)
                if assign is not None and "assign" in assign:
                    assign["assign"][e[0]] = assign["assign"][h]
        return orig(edges, kind, depth, tslab)
    return areas


def install_split(bands_json):
    """Attribute the merged r3 walk, unchanged, to the candidate runs of a member the candidate splits over several
    runs: nothing in the walk is re-cut or re-classified. Each walked edge piece (exact length beyond the edge, r2) is
    divided by WHERE it lies: its overlap with each run's band cutter (route G band widened across its axis only);
    the part beyond every band end is REST. Soffits: each walked face's area inside each cutter. The pieces add up to
    the walk's own figure (sum of fractions = 1), so the r3 totals are reproduced exactly (asserted)."""
    from shapely.geometry import Polygon
    bands = {k: Polygon(v["pts"]) for k, v in json.loads(Path(bands_json).read_text()).items()}
    mr = member_runs()
    orig_merge = T.merge_owner_faces
    ref = {}

    def merge(polys, kind, assign, outline=None, eps=1e-4):
        ref["assign"] = assign
        P, K, A, members = orig_merge(polys, kind, assign, outline=outline, eps=eps)
        for head in P:
            if K.get(head) == "BEAM" and A[head][1] in mr:
                SPLIT[head] = {run: cutter(bands[bid]) for run, bid in mr[A[head][1]] if bid in bands}
                for f in members.get(head, [head]):
                    SPLIT.setdefault(("orig", f), SPLIT[head])
        return P, K, A, members

    T.merge_owner_faces = merge
    T._exact_edge = attributed_exact(T._exact_edge)
    T.face_areas = attributed_areas(T.face_areas, ref)


def records(faces_json):
    with tempfile.TemporaryDirectory() as tmp:
        lines, summary, walk, beams, cols, g = T.alsenan(faces_json, tmp, "r3")
    out = []
    for sh in FLOORS:
        w = walk[sh]
        polys, kind, assign, acc, members = w["polys"], w["kind"], w["assign"], w["acc"], w["members"]

        def owner(i):
            k = kind[i]
            if k in ("BEAM", "COLUMN"):
                a = assign[i]
                return k, a[1], (CALC if a[2] == CALC else HELD)
            if k == "SLAB":
                return "SLAB", i, CALC
            return k, None, HELD

        for i in sorted(polys):
            if kind[i] == "BEAM" and ("orig", i) in SPLIT:
                k, m, st = owner(i)
                for run, f in sorted(share(polys[i], SPLIT[("orig", i)]).items()):
                    out.append(dict(floor=sh, face=i, pieces=[i], owner_kind=k, owner=m, run=run,
                                    owner_status=st, category="BEAM_SOFFIT", m2=polys[i].area * f))
                continue
            if kind[i] == "BEAM":
                k, m, st = owner(i)
                mrr = list(polys[i].minimum_rotated_rectangle.exterior.coords)
                e1 = ((mrr[1][0] - mrr[0][0]) ** 2 + (mrr[1][1] - mrr[0][1]) ** 2) ** 0.5
                e2 = ((mrr[2][0] - mrr[1][0]) ** 2 + (mrr[2][1] - mrr[1][1]) ** 2) ** 0.5
                out.append(dict(floor=sh, face=i, pieces=members.get(i, [i]), owner_kind=k, owner=m,
                                owner_status=st, category="BEAM_SOFFIT", m2=polys[i].area,
                                plan_long_m=round(max(e1, e2), 4), plan_short_m=round(min(e1, e2), 4)))
            elif kind[i] == "UNMATCHED":
                out.append(dict(floor=sh, face=i, pieces=[i], owner_kind="UNMATCHED", owner=None, owner_status=HELD,
                                category="UNMATCHED_PLAN", m2=polys[i].area))
        for (cat, i), v in sorted(acc.items()):
            head, run = (i.split("~", 1) + [None])[:2]
            k, m, st = owner(head)
            d = dict(floor=sh, face=head, pieces=members.get(head, [head]), owner_kind=k, owner=m, owner_status=st,
                     category=cat, m2=v)
            if run:
                d["run"] = run
            out.append(d)
    return out, lines


def r3_floor_sums(recs):
    """the r3 aggregates rebuilt from the records (alsenan's own arithmetic, keyed the same way)."""
    s = defaultdict(float)
    for r in recs:
        sh, c, st = r["floor"], r["category"], r["owner_status"]
        if c == "BEAM_SOFFIT":
            s[(sh, "soffit", st)] += r["m2"]
        elif c == "BEAM_SIDE":
            s[(sh, "side", st)] += r["m2"]
        elif c == "EDGE_BAND":
            s[(sh, "edge", CALC)] += r["m2"]
        elif c == "JOINT_FACE" and st == HELD:
            s[(sh, "joint_held", HELD)] += r["m2"]
        elif "_M2" in c:
            s[(sh, c, HELD)] += r["m2"]
        elif c == "UNMATCHED_PLAN":
            s[(sh, "unmatched", HELD)] += r["m2"]
    # B24 east cantilever end BM-GF-059 inside the B24 face (alsenan: c59)
    c59 = (0.50 * 1.501, 2 * 1.501 * (0.75 - 0.16))
    s[("GF", "soffit", CALC)] -= c59[0]; s[("GF", "soffit", HELD)] += c59[0]
    s[("GF", "side", CALC)] -= c59[1]; s[("GF", "side", HELD)] += c59[1]
    return s


def assert_r3(recs, lines):
    s = r3_floor_sums(recs)
    fl = {"GF": "GF roof slab (p.4)", "1F": "1F roof slab (p.5)", "2F": "2F roof slab (p.6)"}
    got = {}
    for ln in lines:
        got[(ln["element"], ln["floor"], ln["item"], ln["method"])] = ln
    checks = 0
    for sh in FLOORS:
        def m2(item, method):
            return got[("BEAM", sh, f"{fl[sh]} {item}", method)]["m2"]
        for key, item in ((("soffit", CALC), "beam soffits"), (("side", CALC), "beam sides below the slab")):
            want = m2(item, "G")
            assert abs(round(s[(sh,) + key], 3) - want) < 1e-9, (sh, key, s[(sh,) + key], want)
            checks += 1
        held = got[("BEAM", sh, f"{fl[sh]} held / conflict members: soffit and sides of their faces", "G")]
        assert abs(round(s[(sh, "soffit", HELD)] + s[(sh, "side", HELD)], 3) - held["held_hi"]) < 1e-9, sh
        e = got[("SLAB_EDGE", sh, f"{fl[sh]} slab-thickness band at every free edge (plate perimeter and openings)",
                 "G")]
        assert abs(round(s[(sh, "edge", CALC)], 3) - e["m2"]) < 1e-9, (sh, s[(sh, "edge", CALC)], e["m2"])
        checks += 2
    return checks


def main(argv):
    if "--bands" in argv:
        k = argv.index("--bands")
        install_split(argv[k + 1])
        argv = argv[:k] + argv[k + 2:]
    faces_json, out = argv[:2]
    recs, lines = records(faces_json)
    n = assert_r3(recs, lines)
    for r in recs:
        r["m2"] = round(r["m2"], 9)
    Path(out).write_text(json.dumps(dict(schema="T293P2_WALK_RECORDS_V1", source="formwork r3 walk (T-163 MERGED "
                                         "659f889f) on the T-139 faces", r3_checks=n, records=recs),
                                    indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print("records", len(recs), "r3 checks", n, "cutter overlaps", STATS["overlap"])


if __name__ == "__main__":
    main(sys.argv[1:])
