"""T-154 reproduction on the development villa (reads the private drawings; prints areas and term names only).

    python3 -I research/agents_t154/t154_alsenan_run.py <plan.dxf> <structural.dxf> <v2_9_run_dir>

<v2_9_run_dir>: output of `tools/urban_boq_m9.py arch --method ARCH_TAKEOFF_V2.9 --drawings <plan.dxf>`.
1. T-121's census steps (agents/task-T-121 slab_over_air_census.py, not merged), restated here: route G (conventions V6)
   slab faces of each SLAB_PLAN sheet, placed on its storey's plan by the column translation most columns agree on;
   CAD set = (PANEL / BEAM / JUNCTION_GAP / OPEN_BOUNDARY faces) outside the V2.9 facade outline, less plan columns,
   cleaned by an erosion / dilation of 0.05 m (strips < 0.10 m dropped).
2. The pool-court piece (the CAD piece with a route G VOID face) is put in T-127's local frame: X = 0 at the court face
   of the west pier line = the piece's east bound (outer face of the east wall) less the printed 2000; Y = 0 at the court
   face of the south wall = the piece's south bound.
3. research/agents_t127/pool_court_hand.py gives the hand gross and void; t154_reconcile.decompose names every term.
"""
from __future__ import annotations

import collections
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "research/agents_t127"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from shapely import affinity                                     # noqa: E402
from shapely.geometry import Polygon, box as B                   # noqa: E402
from shapely.ops import unary_union                               # noqa: E402

import pool_court_hand as H                                       # noqa: E402
import t154_reconcile as R                                        # noqa: E402

PLATE_CLASSES = ("PANEL", "BEAM", "JUNCTION_GAP", "OPEN_BOUNDARY")


def route_g_slab_sheets(structural):
    from tools import urban_boq_m2 as M2
    cap = {}
    orig = M2.route_generic

    def rg(*a, **k):
        cap["res"] = orig(*a, **k)
        return cap["res"]
    M2.route_generic = rg
    try:
        M2.compute([structural], conventions=str(ROOT / "engine/profiles/URBAN_M8_GENERIC_CONVENTIONS_V6.json"),
                   route="G", completeness=True)
    finally:
        M2.route_generic = orig
    D = cap["res"]["generic"]["D"]
    return {sid: {"storey": rec["sheet"]["storey"], "faces": (rec.get("slab") or {}).get("faces", [])}
            for sid, rec in D["sheets"].items() if rec["sheet"]["role"] == "SLAB_PLAN"}


def plan_columns(dxf, layer="S-COL.BON"):
    import ezdxf
    cols = []

    def walk(ents, d=0):
        for e in ents:
            if e.dxftype() == "INSERT" and d < 4:
                try:
                    walk(e.virtual_entities(), d + 1)
                except Exception:                                # noqa: BLE001
                    pass
            elif e.dxftype() == "LWPOLYLINE" and e.dxf.layer == layer:
                p = list(e.get_points("xy"))
                cols.append((min(q[0] for q in p), min(q[1] for q in p), max(q[0] for q in p), max(q[1] for q in p)))
    walk(ezdxf.readfile(str(dxf)).modelspace())
    return cols


def court_piece(plan, structural, run):
    run = Path(run)
    fac = {f["floor"]: f for f in json.loads((run / "FACADE.json").read_text())["floors"]}
    regions = {r["floor"]: r["box"] for r in json.loads((run / "ARCH_PLAN.json").read_text())["regions"]}
    cols = plan_columns(plan)
    u = 0.001
    for sid, sh in sorted(route_g_slab_sheets(structural).items()):
        fl = sh["storey"]
        if fl not in regions:
            continue
        b = regions[fl]
        pc = [c for c in cols if b[0] <= c[0] <= b[2] and b[1] <= c[1] <= b[3]]
        sc = []
        for f in sh["faces"]:
            if f["class"] == "COLUMN" and len(f["polygon"]) >= 3:
                xs, ys = [p[0] for p in f["polygon"]], [p[1] for p in f["polygon"]]
                sc.append((min(xs), min(ys), max(xs), max(ys)))
        votes = collections.Counter()
        for p in pc:
            for s in sc:
                if abs((p[2] - p[0]) - (s[2] - s[0])) < 5 and abs((p[3] - p[1]) - (s[3] - s[1])) < 5:
                    votes[(round(p[0] - s[0]), round(p[1] - s[1]))] += 1
        if not votes:
            continue
        (dx, dy), n = votes.most_common(1)[0]
        faces = []
        for f in sh["faces"]:
            if len(f["polygon"]) >= 3:
                P = Polygon([((x + dx) * u, (y + dy) * u) for x, y in f["polygon"]])
                faces.append((f, P if P.is_valid else P.buffer(0)))
        use = [(f, P) for f, P in faces if f["class"] in PLATE_CLASSES]
        plate = unary_union([P.buffer(0.002) for _, P in use]).buffer(-0.002)
        air = B(*[v * u for v in b]).buffer(50).difference(Polygon(fac[fl]["outlines"][0]["ring_m"]))
        air = air.difference(unary_union([B(*[v * u for v in c]) for c in pc]))
        A = plate.intersection(air)
        core = R.opening(A, 0.10)
        voids = unary_union([P for f, P in use if "VOID" in (f.get("opening_labels") or [])] or [B(0, 0, 0, 0)])
        for g in getattr(core, "geoms", [core]):
            if g.area > 0.01 and g.intersection(voids).area > 0.5:
                opened = max((a for a in getattr(A, "geoms", [A]) if a.intersects(g)), key=lambda a: a.intersection(g).area)
                cols_sheet = [(f["face_id"], P) for f, P in faces if f["class"] == "COLUMN" and P.intersects(g.envelope)]
                return dict(sheet=sid, storey=fl, columns_agreeing=n, piece=g, opened=opened, void=g.intersection(voids),
                            sheet_columns=cols_sheet)
    raise SystemExit("no slab-sheet piece with a VOID face found")


def main(plan, structural, run):
    c = court_piece(plan, structural, run)
    X0, Y0 = c["piece"].bounds[2] - H.W_OUT, c["piece"].bounds[1]          # printed 2000 to the outer east face

    def L(g):
        return affinity.translate(g, -X0, -Y0)
    cad, opened, gvoid = L(c["piece"]), L(c["opened"]), L(c["void"])
    hand = H.court_clear().difference(B(0, 5.35, 0.5, 5.40))
    hvoid = H.void_and_ring()[0]
    zones = {"E  east wall top Y 0..5.40 (incl. the 4.521 opening head SX-01)": B(1.8, 0, 2.0, 5.4),
             "NE wall corner X 1.80..2.00, Y 5.40..5.60": B(1.8, 5.4, 2.0, 5.6),
             "N  north wall top X < 1.80 (incl. the 1.00 opening head SX-03)": B(-3, 5.4, 1.8, 7),
             "W  frame recess between the printed 657 line and the frame line (SX-02)": B(-3, 0, 0, 5.4).union(
                 B(-3, 0, 1.8, 5.4).difference(hand))}
    planted = [P for fid, P in c["sheet_columns"] if L(P).intersects(hand) and L(P).intersection(hand).area > 1e-4]
    hz = {"COLUMN face drawn on the slab sheet over the court (T.C column above, dropped by the census)":
          unary_union([L(P) for P in planted]) if planted else B(0, 0, 0, 0)}
    rows = R.decompose(hand, cad, zones, opened=opened, hand_only_zones=hz)
    resid = R.reconcile(hand, cad, rows, tol=0.005)
    print(f"sheet {c['sheet']} on {c['storey']} ({c['columns_agreeing']} columns agree); CAD piece {cad.area:.4f}, "
          f"route G void {gvoid.area:.4f}, CAD net {cad.area - gvoid.area:.4f}")
    print(f"hand gross {hand.area:.4f}, hand void {hvoid.area:.4f}, hand net {hand.area - hvoid.area:.4f}")
    for k, a, s in rows:
        print(f"  {'+' if s > 0 else '-'} {a:.4f}  {k}")
    print(f"  residual {resid:+.5f} m2 (tolerance 0.005)")
    # T-127's rebuilt table (reconcile_t121_basis.py pieces) against the CAD set: the 0.088 m2
    t127 = {"pocket": 0.5607, "east": 1.0800, "north": 0.3160}
    north_w = B(-0.08, 5.4, 2.0, 5.6).difference(B(0, 5.35, 0.5, 5.6)).intersection(B(-3, 5.3, 0, 7)).area
    print(f"T-127 north strip west of the court face (X -0.08..0, Y 5.40..5.60): {north_w:.4f}; CAD set there: "
          f"{opened.intersection(B(-3, 5.4, 0, 7)).area:.4f}")
    print(f"T-127 rebuilt {hand.area + sum(t127.values()):.4f} - CAD {cad.area:.4f} = "
          f"{hand.area + sum(t127.values()) - cad.area:.4f} m2")


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print(__doc__)
        sys.exit(2)
    main(*sys.argv[1:])
