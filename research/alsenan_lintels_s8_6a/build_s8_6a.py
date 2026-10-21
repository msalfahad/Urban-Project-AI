"""S8.6A - lintel bearing, release authority and quantity reconciliation: a dated correction layer over the frozen
S8.6 package (which is never rebuilt or written).

    python3 -I research/alsenan_lintels_s8_6a/build_s8_6a.py

Every one of the 14 lintels S8.6 released is re-audited from independent evidence:
- the registered architectural DXF (P7757), read directly with ezdxf: the wall faces, crossing walls and column
  outlines beyond each jamb, measured outward from the jamb (no S8.6 code is imported);
- the registered structural DXF (ST7757) through the frozen S1 reader: the beam bands over each lintel footprint, on
  the slab sheet above, under the S8.6 translation (whose column-vote registration is re-checked here);
- the frozen S1 rules (P13-LINTEL, P8-N22, P8-N09, P8-N20) for what the source actually states.
A lintel keeps its release only when both bearings exist as drawn masonry of at least the stated minimum, nothing
structural stands over its opening and the opening's type gives the lintel a wall to carry. Every other lintel moves
to a blocked lane with its reason; its frozen figure is kept as history and as conditional geometry. The opening
census is verified unchanged. No post-freeze reference selects any quantity here: the post-freeze comparison is read
for its reference-population ids only (census question 6).
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import math
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
for p in (ROOT, ROOT / "research" / "external_engine_lab"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from engine.source import delta_release as DR  # noqa: E402
from engine.source import lintel_release_audit as LA  # noqa: E402
from engine.source import rebar_unit_mass as UM  # noqa: E402

ROUND = "S8_6A"
DATE = "2026-10-10"
BASELINE_HEAD = "974bff2"
POLICY = "S8_6A_LINTEL_RELEASE_AUTHORITY_V1"
R = ROOT / "research"
S86 = R / "alsenan_lintels_s8_6"
S86_MANIFEST = S86 / "15_S8_6_FREEZE_MANIFEST.json"
BY_SHA = ROOT / "data/inputs/by_sha256"
ARCH_SHA = "ab54dd554c31fe4a6a63ff773dc6d034159a736c7dd78158483b473a4ed31cc4"
STRUCT_SHA = "9f9d1179a5d2a6635f9b412915a72184b7db1ff7729f4ab39a72dc3391738079"
S1_RULES = R / "alsenan_structural_census_s1/STRUCTURAL_PROJECT_RULE_REGISTER.json"
MANIFESTS = {"S4": R / "alsenan_footing_rebar_s4/S4_FREEZE_MANIFEST.json",
             "S4.1": R / "alsenan_footing_rebar_s4_1/S4_1_FREEZE_MANIFEST.json",
             "S5": R / "alsenan_ground_system_rebar_s5/S5_FREEZE_MANIFEST.json",
             "S5.1": R / "alsenan_ground_system_rebar_s5_1/S5_1_FREEZE_MANIFEST.json",
             "S6": R / "alsenan_superstructure_beam_rebar_s6/S6_FREEZE_MANIFEST.json",
             "S6.1": R / "alsenan_superstructure_beam_rebar_s6_1/S6_1_FREEZE_MANIFEST.json",
             "AD1": R / "ad1_authority_decisions/AD1_FREEZE_MANIFEST.json",
             "D1.1": R / "d1_1_stirrup_authority_audit/D1_1_FREEZE_MANIFEST.json",
             "D1.2": R / "d1_2_footing_cover_audit/D1_2_FREEZE_MANIFEST.json",
             "PRE-S7": R / "alsenan_slab_rebar_pre_s7/PRE_S7_FREEZE_MANIFEST.json",
             "PRE-S7.1": R / "alsenan_slab_rebar_pre_s7_1/PRE_S7_1_FREEZE_MANIFEST.json",
             "S7": R / "alsenan_slab_rebar_s7/12_S7_FREEZE_MANIFEST.json",
             "S7A": R / "alsenan_slab_rebar_s7a_qa/11_S7A_FREEZE_MANIFEST.json",
             "PRE-S8": R / "pre_s8_structural_completeness/13_PRE_S8_FREEZE_MANIFEST.json",
             "S8.1": R / "alsenan_ground_slab_s8_1/11_S8_1_FREEZE_MANIFEST.json",
             "S8.1A": R / "alsenan_ground_slab_s8_1a/14_S8_1A_FREEZE_MANIFEST.json",
             "S8.2": R / "alsenan_swimming_pool_s8_2/18_S8_2_FREEZE_MANIFEST.json",
             "S8.2A": R / "alsenan_swimming_pool_s8_2a/12_S8_2A_FREEZE_MANIFEST.json",
             "S8.3": R / "alsenan_dome_ring_s8_3/16_S8_3_FREEZE_MANIFEST.json",
             "S8.3A": R / "alsenan_dome_mesh_s8_3a/09_S8_3A_FREEZE_MANIFEST.json",
             "S8.4": R / "alsenan_water_tank_s8_4/15_S8_4_FREEZE_MANIFEST.json",
             "S8.5": R / "alsenan_special_columns_s8_5/17_S8_5_FREEZE_MANIFEST.json"}
POST_FREEZE_IDS = S86 / "post_freeze/01_POST_FREEZE_COMPARISON.csv"   # reference-population ids only
READ = {"S86_CENSUS": S86 / "01_OPENING_CENSUS.csv", "S86_SCHEDULE": S86 / "02_LINTEL_SCHEDULE_TRANSCRIPTION.csv",
        "S86_REGISTRATION": S86 / "03_ARCH_STRUCTURAL_REGISTRATION.csv",
        "S86_BINDING": S86 / "04_OPENING_LINTEL_BINDING_MATRIX.csv", "S86_BEAMS": S86 / "05_BEAM_OVERLAP_AUDIT.csv",
        "S86_CONCRETE": S86 / "06_LINTEL_CONCRETE_QTO.csv", "S86_REBAR": S86 / "07_LINTEL_REBAR_QTO.csv",
        "S86_SUMMARY": S86 / "14_S8_6_SUMMARY.json", "S86_MANIFEST": S86_MANIFEST, "S1_RULES": S1_RULES,
        "POST_FREEZE_IDS": POST_FREEZE_IDS}
CODE = ["engine/source/lintel_release_audit.py", "engine/source/rebar_unit_mass.py", "engine/source/delta_release.py",
        "research/alsenan_lintels_s8_6a/build_s8_6a.py", "research/external_engine_lab/alsenan_structural_s1.py"]
OUTPUTS = ["00_README.md", "01_RELEASE_AUTHORITY_REGISTER.csv", "02_SIX_CASE_INVESTIGATION.csv",
           "03_BEARING_AND_COLUMN_CONNECTION_AUDIT.csv", "04_COVER_AND_STIRRUP_AUTHORITY.csv",
           "05_CORRECTED_ELIGIBLE_RELEASE_VIEW.csv", "06_CONCRETE_OWNERSHIP_AND_OVERLAP.csv",
           "07_REINFORCEMENT_RECLASSIFICATION.csv", "08_OPENING_CENSUS_VERIFICATION.csv",
           "09_QUANTITY_RECONCILIATION.csv", "10_PREVIOUS_FREEZE_VERIFICATION.csv", "11_S8_6A_SUMMARY.json"]
MANIFEST_NAME = "12_S8_6A_CORRECTION_MANIFEST.json"
UNIT_MASS = {"method": UM.D2_OVER_162, "authority": "project-wide method used by S3.1 / S6.1 / S7 / S8",
             "selected_by": "Urban (project basis)"}
SIX = ("LT-OP-GF-005", "LT-OP-GF-021", "LT-OP-GF-029", "LT-OP-1F-017", "LT-OP-GF-013", "LT-OP-GF-018")
FROZEN = {"lintels": 14, "m3": 0.745261681, "kg": 96.427279858}   # the S8.6 release, checked against its files
MIN_BEARING_MM = 400.0             # p.13 LINTEL DETAIL 'MIN.40cm' (S1 rule P13-LINTEL)
TRACE_REACH_MM = 1200.0
JUNCTION_MAX_MM = 250.0            # a hole in both faces shorter than the census's smallest opening is a crossing
CROSS_MAX_MM = 400.0               # a cross wall is at most one maximum wall thickness deep
COVER_CASES_MM = (20.0, 25.0, 30.0, 40.0, 50.0)
NOMINAL_COVER_MM = 25.0
WALL_LAYER, COLUMN_LAYER = "1", "S-COL.BON"
SLAB_ABOVE = {"GF": "GFRS", "1F": "FFRS", "2F": "SFRS"}
# release states of the correction layer
RETAINED = "RETAINED_PROJECT_BASIS_QTO"
WITHHELD_HEAD = "BLOCKED_HEAD_FUNCTION_UNRESOLVED"
BOUNDED_HEAD_TYPES = {"1_INTERNAL_DOOR": "door symbol (a swing leaf in the gap)",
                      "7_OPEN_ARCHWAY_OR_PASSAGE": "arch block or header lines drawn over both faces"}
HYGIENE = re.compile(r"YEARS 2013|7757-[A-Z]|[؀-ۿ]{3,}")


class Stop(Exception):
    pass


def check(cond, msg):
    if not cond:
        raise Stop(msg)


def _sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def _j(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def _rows(p):
    with open(p, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def _r(v, nd=9):
    return None if v is None else round(float(v) + 0.0, nd) + 0.0


def _full(v, nd=9):
    s = f"{v:.{nd}f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def _cell(v):
    if v is None:
        return ""
    if isinstance(v, bool):
        return str(v)
    if isinstance(v, float):
        return _full(v)
    if isinstance(v, (list, tuple, dict)):
        return json.dumps(v, ensure_ascii=False, sort_keys=True)
    return str(v)


def _csv(name, rows, fields=None):
    fields = fields or list(rows[0])
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=fields, lineterminator="\n", extrasaction="raise")
    w.writeheader()
    for r in rows:
        w.writerow({k: _cell(r.get(k)) for k in fields})
    (HERE / name).write_text(buf.getvalue(), encoding="utf-8")


def _json(name, obj):
    (HERE / name).write_text(json.dumps(obj, indent=1, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def code_digest():
    h = hashlib.sha256()
    for c in CODE:
        h.update(c.encode())
        h.update((ROOT / c).read_bytes())
    return h.hexdigest()[:16]


def kg(length_mm, dia_mm):
    return length_mm / 1000.0 * UM.kg_per_m(dia_mm, UNIT_MASS)


def F(v):
    return None if v in ("", None) else float(v)


def dot(p, v):
    return p[0] * v[0] + p[1] * v[1]


# ------------------------------------------------------------------ frozen inputs
def verify_previous():
    """the 22 freezes S8.6 verified (its frozen_baselines) and the S8.6 freeze itself."""
    base = _j(S86 / "14_S8_6_SUMMARY.json")["frozen_baselines"]
    check(set(base) == set(MANIFESTS), f"the S8.6 baseline list ({sorted(base)})")
    rows = []
    for k, mp in list(MANIFESTS.items()) + [("S8.6", S86_MANIFEST)]:
        m = _j(mp)
        v = DR.verify_frozen(mp, ROOT)
        if k in base:
            check(v["manifest_sha256"] == base[k], f"{k}: manifest unchanged since S8.6")
        rows.append({"MANIFEST": str(mp.relative_to(ROOT)), "ROUND": k,
                     "MANIFEST_SHA256": v["manifest_sha256"], "OUTPUTS_VERIFIED": len(m.get("outputs", {})),
                     "RESULT": "VERIFIED"})
    errata = _j(R / "alsenan_dome_mesh_s8_3a/07_FROZEN_VERIFICATION.json")["s8_3_errata_sha256"]
    for name, h in sorted(errata.items()):
        check(_sha(R / "alsenan_dome_ring_s8_3/errata" / name) == h, f"S8.3 errata {name} unchanged")
        rows.append({"MANIFEST": f"research/alsenan_dome_ring_s8_3/errata/{name}", "ROUND": "S8.3 errata",
                     "MANIFEST_SHA256": h, "OUTPUTS_VERIFIED": 1, "RESULT": "VERIFIED"})
    for k, (p, key) in {"S1": (R / "alsenan_structural_census_s1/INDEX.json", "registers"),
                        "S2": (R / "alsenan_structural_s2/INDEX.json", "outputs"),
                        "S3": (R / "alsenan_column_rebar_s3/INDEX.json", "outputs"),
                        "S3.1": (R / "alsenan_column_rebar_s3_1/INDEX.json", "outputs")}.items():
        n = 0
        for name, v in _j(p)[key].items():
            h = v["sha256"] if isinstance(v, dict) else v
            f = p.parent / (v["file"] if isinstance(v, dict) else name)
            check(_sha(f) == h, f"{k} register {name} unchanged")
            n += 1
        rows.append({"MANIFEST": str(p.relative_to(ROOT)), "ROUND": f"{k} register index", "MANIFEST_SHA256": _sha(p),
                     "OUTPUTS_VERIFIED": n, "RESULT": "VERIFIED"})
    return rows


def frozen_s86():
    DR.verify_frozen(S86_MANIFEST, ROOT)
    m = _j(S86_MANIFEST)
    for o, h in m["outputs"].items():
        check(_sha(S86 / o) == h, f"S8.6 output {o} unchanged")
    cen = {r["OPENING_ID"]: r for r in _rows(READ["S86_CENSUS"])}
    conc = {r["LINTEL_ID"]: r for r in _rows(READ["S86_CONCRETE"])}
    rel = {k: v for k, v in conc.items() if v["LANE"] == "PROJECT_BASIS_QTO"}
    reb = [r for r in _rows(READ["S86_REBAR"])]
    sched = {r["ROW_ID"]: r for r in _rows(READ["S86_SCHEDULE"]) if r["RECORD"] == "SCHEDULE_ROW"}
    bind = {r["OPENING_ID"]: r for r in _rows(READ["S86_BINDING"])}
    beams = _rows(READ["S86_BEAMS"])
    reg = {r["FLOOR"]: r for r in _rows(READ["S86_REGISTRATION"]) if r["RECORD"] == "FLOOR"}
    s = _j(READ["S86_SUMMARY"])
    check(len(rel) == FROZEN["lintels"], f"S8.6 released {len(rel)} lintels")
    check(abs(sum(F(r["M3"]) for r in rel.values()) - FROZEN["m3"]) < 1e-8 and
          abs(s["released"]["concrete_m3"] - FROZEN["m3"]) < 1e-9, "S8.6 released m3")
    check(abs(s["released"]["kg"] - FROZEN["kg"]) < 1e-8, "S8.6 released kg")
    return {"manifest": m, "census": cen, "conc": conc, "released": rel, "rebar": reb, "sched": sched, "bind": bind,
            "beams": beams, "reg": reg, "summary": s}


def s1_rules():
    rows = {r["rule_id"]: r for r in _j(S1_RULES)["rows"]}
    for k in ("P13-LINTEL", "P8-N22", "P8-N09", "P8-N20", "P8-N04"):
        check(k in rows, f"S1 rule {k}")
    conn = [r["rule_id"] for r in rows.values()
            if "LINTEL" in json.dumps(r.get("element_scope")) and re.search(r"column|dowel|anchor|connect",
                                                                              (r.get("english_interpretation") or "") +
                                                                              (r.get("raw_text") or ""), re.I)]
    return rows, conn


# ------------------------------------------------------------------ independent drawing evidence
def arch_geometry():
    import ezdxf
    f = BY_SHA / f"{ARCH_SHA}.dxf"
    check(f.exists() and _sha(f) == ARCH_SHA, "private input P7757.dxf restored and unchanged")
    msp = ezdxf.readfile(str(f)).modelspace()
    segs, cols = [], []
    for e in msp:
        t = e.dxftype()
        if t == "LINE" and e.dxf.layer == WALL_LAYER:
            segs.append((e.dxf.handle, (e.dxf.start.x, e.dxf.start.y), (e.dxf.end.x, e.dxf.end.y)))
        elif t == "LWPOLYLINE":
            p = [(q[0], q[1]) for q in e.get_points("xy")]
            if e.dxf.layer == WALL_LAYER:
                pr = list(zip(p, p[1:] + ([p[0]] if e.closed else [])))
                segs += [(f"{e.dxf.handle}:{k}", a, b) for k, (a, b) in enumerate(pr)]
            elif e.dxf.layer == COLUMN_LAYER and e.closed:
                cols.append((e.dxf.handle, p))
    return segs, cols


def frame_of(o):
    ang = math.radians(float(o["WALL_ANGLE_DEG"]))
    u = (math.cos(ang), math.sin(ang))
    n = (-u[1], u[0])
    cx, cy = json.loads(o["CENTRE_ARCH_XY"])
    s0, s1 = json.loads(o["ALONG_WALL_MM"])
    t = float(o["WALL_THICKNESS_MM"])
    om = cx * n[0] + cy * n[1]
    return u, n, s0, s1, om - t / 2.0, om + t / 2.0, t


def trace_end(o, side, segs, cols, reach=TRACE_REACH_MM):
    """the drawn evidence beyond one jamb, outward, in the opening's wall frame."""
    u, n, s0, s1, lo, hi, t = frame_of(o)
    sj, sg = (s0, -1.0) if side == "start" else (s1, 1.0)
    fa, fb, cr, ob_at, handles = [], [], [], [], {"faces": set(), "crossings": [], "columns": []}
    for h, a, b in segs:
        sa, sb, oa, ob = dot(a, u), dot(b, u), dot(a, n), dot(b, n)
        da, db = sg * (sa - sj), sg * (sb - sj)
        if abs(oa - ob) < 0.5:
            for f, off in ((fa, lo), (fb, hi)):
                if abs(oa - off) < 2.0:
                    x0, x1 = sorted((da, db))
                    if x1 > -5.0 and x0 < reach:
                        f.append((max(x0, 0.0), min(x1, reach)))
                        handles["faces"].add(h)
        elif abs(sa - sb) >= 0.5 and abs(oa - ob) >= 0.5:
            for d_, o_ in ((da, oa), (db, ob)):          # an oblique wall line meeting a face beyond the jamb
                if -5.0 < d_ < reach and (abs(o_ - lo) < 2.0 or abs(o_ - hi) < 2.0):
                    ob_at.append(max(d_, 0.0))
        elif abs(sa - sb) < 0.5 and -5.0 < da < reach:
            o0, o1 = sorted((oa, ob))
            if max(0.0, min(o1, hi) - max(o0, lo)) / t > 0.5:
                cr.append((max(da, 0.0), o0 < lo - 5.0, o1 > hi + 5.0))
                handles["crossings"].append(h)
    cl = []
    for h, p in cols:
        ss = [sg * (dot(q, u) - sj) for q in p]
        oo = [dot(q, n) for q in p]
        if max(oo) > lo + 5.0 and min(oo) < hi - 5.0 and max(ss) > -5.0 and min(ss) < reach:
            cl.append((max(min(ss), 0.0), max(ss)))
            handles["columns"].append(h)
    res = LA.bearing_reach(fa, fb, cr, cl, cap=reach, junction_max=JUNCTION_MAX_MM, cross_max=CROSS_MAX_MM,
                           oblique_at=ob_at)
    res.update(face_a=[[_r(a, 1), _r(b, 1)] for a, b in LA._union(fa)],
               face_b=[[_r(a, 1), _r(b, 1)] for a, b in LA._union(fb)],
               crossings=sorted([[_r(x, 1), ba, bb] for x, ba, bb in cr]),
               columns=sorted([[_r(a, 1), _r(b, 1)] for a, b in cl]), oblique=sorted(set(_r(v, 1) for v in ob_at)),
               handles={k: sorted(v) for k, v in handles.items()})
    return res


def beams_over_footprint(o, lintel, T, lines, sheet):
    """S1 beam bands (sheet-local) meeting the lintel footprint (arch coordinates + T): over the opening span and over
    each bearing zone. Lengths along the wall, mm."""
    from shapely.geometry import Polygon
    u, n, s0, s1, lo, hi, t = frame_of(o)
    du, dn = dot(T, u), dot(T, n)
    t0 = s0 - F(lintel["BEARING_START_MM"])
    t1 = s1 + F(lintel["BEARING_END_MM"])

    def rect(uu, nn, a0, a1, b0, b1):
        P = lambda s_, o_: (s_ * uu[0] + o_ * nn[0], s_ * uu[1] + o_ * nn[1])  # noqa: E731
        return Polygon([P(a0, b0), P(a1, b0), P(a1, b1), P(a0, b1)])

    zones = {"OPENING_SPAN": (s0, s1), "START_BEARING": (t0, s0), "END_BEARING": (s1, t1)}
    out = []
    for lid, l in sorted(lines[sheet].items()):
        bp = rect(l["dir"], l["normal"], l["t0"], l["t1"], l["offset"] - l["width_mm"] / 2.0,
                  l["offset"] + l["width_mm"] / 2.0)
        for z, (a, b) in zones.items():
            if b - a <= 0.5:
                continue
            inter = rect(u, n, a + du, b + du, lo + dn, hi + dn).intersection(bp)
            if inter.is_empty or inter.area <= 1.0:
                continue
            xs = [dot(q, u) for q in inter.exterior.coords]
            ys = [dot(q, n) for q in inter.exterior.coords]
            if max(xs) - min(xs) < 20.0 or max(ys) - min(ys) < 20.0:
                continue
            out.append({"zone": z, "line_id": lid, "along_mm": _r(max(xs) - min(xs), 1),
                        "lateral_mm": _r(max(ys) - min(ys), 1), "beam_width_mm": l["width_mm"]})
    return out


def structural_lines():
    import alsenan_structural_s1 as S1
    f = BY_SHA / f"{STRUCT_SHA}.dxf"
    check(f.exists() and _sha(f) == STRUCT_SHA, "private input ST7757.dxf restored and unchanged")
    src = S1.Source()
    lines = {}
    for sh in SLAB_ABOVE.values():
        segs, _, _ = S1.beam_linework(src, sh)
        lines[sh] = {l["line_id"]: l for l in S1.beam_lines(S1.straight_bands(segs))}
    return src, lines


def reverify_registration(src, segs_cols, reg):
    """the S8.6 translations are re-derived by an independent vote of equal-size column outlines."""
    import ezdxf  # noqa: F401
    _, cols = segs_cols
    E = src.entities()
    out = {}
    rect = lambda pts: (min(p[0] for p in pts), min(p[1] for p in pts), max(p[0] for p in pts),  # noqa: E731
                        max(p[1] for p in pts))
    frames = {"GF": (-164712.8, -811916.5), "1F": (-209565.5, -811916.5), "2F": (-254418.1, -811916.5)}
    for fl, sh in SLAB_ABOVE.items():
        x0, y0 = frames[fl]
        a = [rect(p) for _, p in cols if x0 <= p[0][0] <= x0 + 40314.0 and y0 <= p[0][1] <= y0 + 28030.0]
        s = [rect([tuple(q) for q in e["pts"]]) for e in E[sh] if e["type"] == "LWPOLYLINE" and
             e["layer"] == COLUMN_LAYER and e.get("closed")]
        votes = Counter()
        for x in a:
            for y in s:
                if round(x[2] - x[0]) == round(y[2] - y[0]) and round(x[3] - x[1]) == round(y[3] - y[1]):
                    votes[(round(y[0] - x[0], 3), round(y[1] - x[1], 3))] += 1
        (tx, ty), nv = votes.most_common(1)[0]
        frozen = (F(reg[fl]["TX_MM"]), F(reg[fl]["TY_MM"]))
        check(abs(tx - frozen[0]) < 0.01 and abs(ty - frozen[1]) < 0.01, f"{fl}: registration re-derived")
        out[fl] = {"T": (float(tx), float(ty)), "votes": nv}
    return out


# ------------------------------------------------------------------ build
def build():
    prev = verify_previous()
    S = frozen_s86()
    rules, conn_rules = s1_rules()
    segs, cols = arch_geometry()
    src, lines = structural_lines()
    reg = reverify_registration(src, (segs, cols), S["reg"])
    rel = S["released"]
    released_ids = set(rel)
    rows_sched = {k: {"lo": int(v["WIDTH_LO_CM"]), "hi": int(v["WIDTH_HI_CM"])} for k, v in S["sched"].items()}
    audit, ends_rows, six_rows = [], [], []
    for lid in sorted(rel):
        x = rel[lid]
        oid = x["OPENING_ID"]
        o = S["census"][oid]
        b = S["bind"][oid]
        fl = x["FLOOR"]
        w = float(o["WIDTH_MM"])
        row = [k for k, v in rows_sched.items() if v["lo"] <= w / 10.0 <= v["hi"]]
        check(row == [x["ROW"]], f"{lid}: one schedule row, the frozen one ({row})")
        check(abs(float(o["WALL_THICKNESS_MM"]) - F(x["B_MM"])) < 0.05, f"{lid}: lintel width = wall thickness")
        check(abs(F(x["OPENING_W_MM"]) - w) < 0.2, f"{lid}: opening width")
        ends = {}
        for side in ("start", "end"):
            tr = trace_end(o, side, segs, cols)
            frozen_bearing = F(x[f"BEARING_{side.upper()}_MM"])
            st = LA.classify_end(tr["available"], tr["terminator"], MIN_BEARING_MM,
                                 column_connection=bool(conn_rules))
            ends[side] = (st, tr)
            ends_rows.append({"LINTEL_ID": lid, "OPENING_ID": oid, "END": side.upper(),
                              "FROZEN_SUPPORT": x[f"{side.upper()}_SUPPORT"],
                              "FROZEN_BEARING_MM": frozen_bearing, "INDEPENDENT_AVAILABLE_MM": tr["available"],
                              "TERMINATOR": tr["terminator"], "TERMINATOR_AT_MM": tr["at"],
                              "REQUIRED_MIN_MM": MIN_BEARING_MM, "END_STATE": st,
                              "FACE_A_DRAWN": tr["face_a"], "FACE_B_DRAWN": tr["face_b"],
                              "CROSSINGS": tr["crossings"], "COLUMNS": tr["columns"], "HANDLES": tr["handles"],
                              "AGREES_WITH_FROZEN": abs(min(tr["available"], MIN_BEARING_MM) - frozen_bearing) < 1.0,
                              "OBLIQUE_MEETS_MM": sorted(_r(v, 1) for v in tr.get("oblique", [])),
                              "COLUMN_CONNECTION_DETAIL": conn_rules or "none stated (P13-LINTEL gives masonry "
                                                                       "bearing only; P8-N09 is for starters)"})
        cls = LA.classify_lintel([ends["start"][0], ends["end"][0]])
        bo = beams_over_footprint(o, x, reg[fl]["T"], lines, SLAB_ABOVE[fl])
        over = [q for q in bo if q["zone"] == "OPENING_SPAN"]
        check(not over, f"{lid}: no beam band over the opening span ({over})")
        head_basis = BOUNDED_HEAD_TYPES.get(o["TYPE"])
        if cls != LA.CONFIRMED:
            state = cls
        elif head_basis is None:
            state = WITHHELD_HEAD
        else:
            state = RETAINED
        audit.append({"lid": lid, "oid": oid, "floor": fl, "x": x, "o": o, "b": b, "ends": ends, "cls": cls,
                      "state": state, "beams": bo, "head_basis": head_basis})
    by = {a["lid"]: a for a in audit}
    check(set(SIX) <= set(by), "the six named lintels are among the released")
    return {"prev": prev, "S": S, "rules": rules, "conn_rules": conn_rules, "audit": audit, "by": by,
            "ends_rows": ends_rows, "reg": reg, "released_ids": released_ids}


def run():
    L = build()
    S, audit, by = L["S"], L["audit"], L["by"]
    retained = {a["lid"] for a in audit if a["state"] == RETAINED}
    # ------------------------------------------------------------ concrete ownership: one owner per shared volume
    owners, overlap_rows = {}, []
    for a in audit:
        for f in json.loads(a["x"]["FLAGS"] or "[]"):
            m = re.match(r"CORNER_OVERLAP_WITH:(LT-[^:]+):([\d.]+)mm2", f)
            if m:
                other, mm2 = m.group(1), float(m.group(2))
                pair = tuple(sorted((a["lid"], other)))
                vol = mm2 * min(F(a["x"]["D_MM"]), F(by[other]["x"]["D_MM"]) if other in by else 1e9) / 1e9
                owners[pair] = {"mm2": mm2, "m3": vol, "frozen_owner": other,
                                "corrected_owner": LA.assign_overlap(pair[0], pair[1], retained)}
    net = {}
    for a in audit:
        x = a["x"]
        gross = F(x["B_MM"]) * F(x["D_MM"]) * F(x["LENGTH_MM"]) / 1e9
        check(abs(gross - F(x["GROSS_M3"])) < 2e-9, f"{a['lid']}: gross volume re-derived")
        ded = 0.0
        for pair, v in owners.items():
            if a["lid"] in pair and v["corrected_owner"] not in (None, a["lid"]):
                ded += v["m3"]
            if a["lid"] in pair and v["corrected_owner"] is None and a["lid"] != pair[0]:
                ded += v["m3"]        # conditional geometry: the shared block stays with the first id
        a["gross_m3"], a["net_m3"] = gross, gross - ded
    for pair, v in sorted(owners.items()):
        overlap_rows.append({"SHARED_BETWEEN": list(pair), "AREA_MM2": v["mm2"], "M3": _r(v["m3"]),
                             "FROZEN_OWNER": v["frozen_owner"], "CORRECTED_OWNER": v["corrected_owner"],
                             "STATE": "RELEASED_WITH_OWNER" if v["corrected_owner"] else "CONDITIONAL_GEOMETRY_ONLY",
                             "NOTE": "one physical prism, one released owner; the blocked partner's conditional "
                                     "geometry excludes it"})
    # ------------------------------------------------------------ rebar with authority tags
    bars = [r for r in S["rebar"] if r["VIEW"] == "PROJECT_BASIS_QTO"]
    reb_rows = []
    for r in bars:
        a = by[r["LINTEL_ID"]]
        x = a["x"]
        L_ = F(x["LENGTH_MM"])
        d = int(r["DIA_MM"])
        each = F(r["EACH_MM"])
        if r["ROLE"] in ("BOTTOM", "TOP"):
            check(abs(each - (L_ - 2 * NOMINAL_COVER_MM)) < 1e-4, f"{r['LINTEL_ID']} {r['ROLE']}: straight length")
        else:
            check(abs(each - (2 * (F(x["B_MM"]) - 2 * NOMINAL_COVER_MM - d) + 2 * (F(x["D_MM"]) - 2 * NOMINAL_COVER_MM -
                                                                                  d))) < 1e-4, "core path")
            check(int(r["COUNT"]) == LA.stirrup_counts(L_, 5)["RATE_COUNT"], f"{r['LINTEL_ID']}: ceil(5 x L)")
        k = int(r["COUNT"]) * each / 1000.0 * UM.kg_per_m(d, UNIT_MASS)
        check(abs(k - F(r["KG"])) < 1e-6, f"{r['LINTEL_ID']} {r['ROLE']}: kg re-derived")
        reb_rows.append({"LINTEL_ID": r["LINTEL_ID"], "FLOOR": r["FLOOR"], "ROLE": r["ROLE"], "DIA_MM": d,
                         "COUNT": int(r["COUNT"]), "EACH_MM": each, "KG": F(r["KG"]),
                         "FROZEN_LANE": "PROJECT_BASIS_QTO",
                         "CORRECTED_LANE": "PROJECT_BASIS_QTO" if a["state"] == RETAINED else "SENSITIVITY_ONLY",
                         "LANE_REASON": "lintel retained" if a["state"] == RETAINED else f"lintel {a['state']}",
                         "COUNT_AUTHORITY": ("EXPLICIT_PROJECT_DETAIL (p.13 row " + x["ROW"] + ")"
                                             if r["ROLE"] != "STIRRUP" else
                                             "URBAN_CONVENTION ceil(rate x L) over an EXPLICIT rate '5Ø8/M'"),
                         "LENGTH_AUTHORITY": ("URBAN_CONVENTION: lintel length - 2 x nominal cover (P8-N22 minimum "
                                              "for beams, scope not confirmed for lintels); end bends UNRESOLVED"
                                              if r["ROLE"] != "STIRRUP" else
                                              "URBAN_CONVENTION: core path 2(B-2c-d)+2(D-2c-d), sharp corners; "
                                              "hooks UNRESOLVED (drawn on SECT 2-2, no length)"),
                         "UNIT_MASS": "URBAN_PROJECT_METHOD D2/162"})
    return write(L, owners, overlap_rows, reb_rows, retained)


def stirrup_and_cover_review(audit, retained):
    rows = [
        ("BAR_COUNT_AND_DIAMETER", "EXPLICIT_PROJECT_DETAIL", "p.13 LINTEL SCHEDULE rows (2Ø12 / 2Ø10, 2Ø14 / 2Ø12 ...)",
         "exact"),
        ("SECTION_B_X_D", "EXPLICIT_PROJECT_DETAIL", "p.13: 'B x 20' etc.; 'B-WIDTH OF THE BLOCK WALL'", "exact"),
        ("MIN_BEARING", "EXPLICIT_PROJECT_DETAIL", "p.13 LINTEL DETAIL 'MIN.40cm' each side",
         "a minimum: the measured lintel uses exactly 400 (Urban convention: measure at the stated minimum)"),
        ("COVER", "PROJECT_WIDE_RULE_SCOPE_NOT_CONFIRMED", "P8-N22 'Cover >= 2.5 cm columns / slabs / beams'",
         "a minimum for beams; lintels are not named. 25 mm is used as the NOMINAL measurement cover (Urban "
         "convention); the physical lintel cover is UNRESOLVED"),
        ("LONGITUDINAL_LENGTH", "URBAN_MEASUREMENT_CONVENTION", "LINTEL DETAIL draws continuous bars bent at the ends",
         "straight portion = lintel length - 2 x nominal cover; the bent ends are UNRESOLVED (no length printed)"),
        ("STIRRUP_RATE", "EXPLICIT_PROJECT_DETAIL", "'5Ø8/M' (schedule)",
         "a rate: 5 per metre, equivalent spacing 200 mm; NO count, start / end position or zone is stated"),
        ("STIRRUP_COUNT", "URBAN_MEASUREMENT_CONVENTION", "S3.1 RATE_COUNT policy: ceil(rate x length)",
         "over the full lintel length; the LINTEL DETAIL draws stirrups near the ends only (schematic)"),
        ("STIRRUP_SHAPE", "URBAN_MEASUREMENT_CONVENTION", "S6.1 core-path convention",
         "closed rectangle on the bar centreline, sharp corners; hooks UNRESOLVED"),
        ("UNIT_MASS", "URBAN_PROJECT_METHOD", "D2/162 (S3.1 / S6.1 / S7 / S8)", "method, not a source value"),
        ("HOOKS_BENDS_LAPS_ANCHORAGE", "UNRESOLVED_FABRICATION_DETAIL", "LINTEL DETAIL / SECT (2-2) drawn only",
         "none measured, none fabricated")]
    out = [{"RECORD": "COMPONENT", "COMPONENT": a, "AUTHORITY": b, "SOURCE": c, "NOTE": d} for a, b, c, d in rows]
    # cover sensitivity over the retained lintels (nominal straight / core lengths only)
    for c in COVER_CASES_MM:
        tot = 0.0
        for a in audit:
            if a["lid"] not in retained:
                continue
            x = a["x"]
            L_, B, D = F(x["LENGTH_MM"]), F(x["B_MM"]), F(x["D_MM"])
            n = LA.stirrup_counts(L_, 5)["RATE_COUNT"]
            sched = a["sched"]
            for cnt, dia in ((sched["bn"], sched["bd"]), (sched["tn"], sched["td"])):
                tot += kg(cnt * (L_ - 2 * c), dia)
            tot += kg(n * (2 * (B - 2 * c - 8) + 2 * (D - 2 * c - 8)), 8)
        out.append({"RECORD": "COVER_SENSITIVITY", "COMPONENT": f"cover {_full(c, 1)} mm", "AUTHORITY":
                    "SENSITIVITY_ONLY" if c != NOMINAL_COVER_MM else "NOMINAL (as released)", "KG": _r(tot, 6)})
    for method in ("EQUIVALENT_RATE", "RATE_COUNT", "SPACING_WITH_ENDS", "CLEAR_SPAN_RATE"):
        n_tot, k_tot = 0.0, 0.0
        for a in audit:
            if a["lid"] not in retained:
                continue
            x = a["x"]
            L_, B, D, W = F(x["LENGTH_MM"]), F(x["B_MM"]), F(x["D_MM"]), F(x["OPENING_W_MM"])
            n = LA.stirrup_counts(L_, 5, W)[method]
            n_tot += n
            k_tot += kg(n * (2 * (B - 2 * NOMINAL_COVER_MM - 8) + 2 * (D - 2 * NOMINAL_COVER_MM - 8)), 8)
        out.append({"RECORD": "STIRRUP_COUNT_READING", "COMPONENT": method,
                    "AUTHORITY": "AS_RELEASED" if method == "RATE_COUNT" else "SENSITIVITY_ONLY",
                    "COUNT": _r(n_tot, 6), "KG": _r(k_tot, 6)})
    return out


def write(L, owners, overlap_rows, reb_rows, retained):
    S, audit, by = L["S"], L["audit"], L["by"]
    for a in audit:
        r = S["sched"][a["x"]["ROW"]]
        bn, bd = [int(v) for v in re.match(r"(\d+)Ø(\d+)", r["BOTTOM_PRINTED"]).groups()]
        tn, td = [int(v) for v in re.match(r"(\d+)Ø(\d+)", r["TOP_PRINTED"]).groups()]
        a["sched"] = {"bn": bn, "bd": bd, "tn": tn, "td": td}
    kg_of = defaultdict(float)
    for r in reb_rows:
        kg_of[r["LINTEL_ID"]] += r["KG"]
    # ------------------------------------------------------------ 01 register
    reg = []
    for a in audit:
        x, o = a["x"], a["o"]
        reg.append({"LINTEL_ID": a["lid"], "OPENING_ID": a["oid"], "FLOOR": a["floor"], "OPENING_TYPE": o["TYPE"],
                    "SCHEDULE_ROW": x["ROW"], "SCHEDULE_ROW_CHECK": "one row; equals frozen",
                    "WALL_THICKNESS_MM": F(o["WALL_THICKNESS_MM"]), "LINTEL_B_MM": F(x["B_MM"]),
                    "LINTEL_D_MM": F(x["D_MM"]), "OPENING_W_MM": F(x["OPENING_W_MM"]),
                    "START_SUPPORT": a["ends"]["start"][1]["terminator"],
                    "START_AVAILABLE_MM": a["ends"]["start"][1]["available"],
                    "START_STATE": a["ends"]["start"][0], "END_SUPPORT": a["ends"]["end"][1]["terminator"],
                    "END_AVAILABLE_MM": a["ends"]["end"][1]["available"], "END_STATE": a["ends"]["end"][0],
                    "REQUIRED_MIN_BEARING_MM": MIN_BEARING_MM,
                    "BEAMS_OVER_OPENING": [q["line_id"] for q in a["beams"] if q["zone"] == "OPENING_SPAN"],
                    "BEAMS_OVER_BEARING_ZONES": [f"{q['zone']}:{q['line_id']}" for q in a["beams"]
                                                 if q["zone"] != "OPENING_SPAN"],
                    "COLUMNS_WITHIN_TRACE": sorted(set(a["ends"]["start"][1]["handles"]["columns"] +
                                                       a["ends"]["end"][1]["handles"]["columns"])),
                    "HEAD_SOFFIT": "NOT_ESTABLISHED (no head printed); " +
                                   (f"bounded-height opening: {a['head_basis']}" if a["head_basis"] else
                                    "glazing: window or full-height not separable"),
                    "CONCRETE_OVERLAP": [f"{'/'.join(p)}:{_full(v['mm2'], 1)}mm2->{v['corrected_owner']}"
                                         for p, v in owners.items() if a["lid"] in p],
                    "BAR_AUTHORITY": "rows: EXPLICIT; lengths, stirrup count and shape: URBAN_CONVENTION; "
                                     "hooks / bends / anchorage: UNRESOLVED",
                    "BEARING_CLASS": a["cls"], "CORRECTED_STATE": a["state"]})
    _csv(OUTPUTS[1], reg)
    # ------------------------------------------------------------ 02 six cases
    six = []
    why = {
        LA.T_JUNCTION: "the wall runs into a cross wall and stops at its far face; nothing continues beyond it and no "
                       "column or beam supports the end: the full 'MIN.40cm' is not physically available as drawn",
        LA.L_CORNER: "the wall turns a corner; the masonry ends at the corner's outer face: the full 'MIN.40cm' is not "
                     "physically available as drawn",
        LA.OBLIQUE_JUNCTION: "the faces stop where 45-degree walls meet them; the masonry beyond is not read on this "
                             "axis, so the bearing is NOT VERIFIED here (never assumed); the lintel is blocked by its "
                             "other end in any case",
        LA.COLUMN: "about 100 mm of masonry, then an RC column face. No drawing states a lintel-to-column connection "
                   "(P13-LINTEL gives masonry bearing only; P8-N09 is a starter-bar length; P8-N20 is wall "
                   "thickness): a column beside the opening is not anchorage"}
    for lid in SIX:
        a = by[lid]
        short = [s for s in ("start", "end") if a["ends"][s][0] != LA.MASONRY_OK]
        for s in short:
            tr = a["ends"][s][1]
            six.append({"LINTEL_ID": lid, "OPENING_ID": a["oid"], "END": s.upper(),
                        "FROZEN_BEARING_MM": F(a["x"][f"BEARING_{s.upper()}_MM"]),
                        "INDEPENDENT_AVAILABLE_MM": tr["available"], "TERMINATOR": tr["terminator"],
                        "EVIDENCE": f"face A drawn {tr['face_a']}, face B drawn {tr['face_b']}, crossings "
                                    f"{tr['crossings']}, columns {tr['columns']}",
                        "OTHER_SUPPORT_SEARCHED": "columns in the strip: " + (str(tr["columns"]) if tr["columns"]
                                                                              else "none") +
                                                  "; beams over the bearing zone: " +
                                                  (", ".join(q["line_id"] for q in a["beams"]
                                                             if q["zone"] == ("START_BEARING" if s == "start" else
                                                                              "END_BEARING")) or "none") +
                                                  " (a beam at slab level is not a bearing at lintel level)",
                        "CLASSIFICATION": a["cls"], "REASON": why[tr["terminator"]]})
    _csv(OUTPUTS[2], six)
    _csv(OUTPUTS[3], L["ends_rows"])
    _csv(OUTPUTS[4], stirrup_and_cover_review(audit, retained),
         ["RECORD", "COMPONENT", "AUTHORITY", "SOURCE", "NOTE", "COUNT", "KG"])
    # ------------------------------------------------------------ 05 corrected view, 06 ownership
    view = []
    for a in audit:
        x = a["x"]
        view.append({"LINTEL_ID": a["lid"], "FLOOR": a["floor"], "FROZEN_LANE": "PROJECT_BASIS_QTO",
                     "FROZEN_M3": F(x["M3"]), "FROZEN_KG": _r(kg_of[a["lid"]]),
                     "CORRECTED_STATE": a["state"],
                     "CORRECTED_LANE": "PROJECT_BASIS_QTO" if a["state"] == RETAINED else "BLOCKED_UNQUANTIFIED",
                     "CORRECTED_M3": _r(a["net_m3"]) if a["state"] == RETAINED else 0.0,
                     "CORRECTED_KG": _r(kg_of[a["lid"]]) if a["state"] == RETAINED else 0.0,
                     "CONDITIONAL_M3": _r(a["net_m3"]) if a["state"] != RETAINED else None,
                     "CONDITIONAL_KG": _r(kg_of[a["lid"]]) if a["state"] != RETAINED else None,
                     "REASON": lane_reason(a)})
    _csv(OUTPUTS[5], view)
    own = overlap_rows + [{"SHARED_BETWEEN": [a["lid"]], "M3": _r(a["net_m3"]), "FROZEN_OWNER": a["lid"],
                           "CORRECTED_OWNER": a["lid"] if a["state"] == RETAINED else None,
                           "STATE": "RELEASED" if a["state"] == RETAINED else "CONDITIONAL_GEOMETRY_ONLY",
                           "AREA_MM2": None, "NOTE": f"gross {_full(a['gross_m3'], 9)} m3; net of shared volumes "
                                                     f"owned elsewhere"} for a in audit]
    _csv(OUTPUTS[6], own, ["SHARED_BETWEEN", "AREA_MM2", "M3", "FROZEN_OWNER", "CORRECTED_OWNER", "STATE", "NOTE"])
    _csv(OUTPUTS[7], reb_rows)
    # ------------------------------------------------------------ 08 census verification
    cen = S["census"]
    ops = [k for k, v in cen.items() if v["RECORD"] == "OPENING"]
    kinds = Counter(cen[k]["KIND"] for k in ops)
    r5_missed = sorted(k for k in ops if cen[k]["KIND"] in ("WALL_GAP", "GLAZING_RUN", "ARC_GAP") and
                       not json.loads(cen[k]["R5_IDS"] or "[]"))
    pf = _rows(POST_FREEZE_IDS)
    v3b_missed = sorted(r["S8_6_OPENING"] for r in pf if r["CLASS"] == "MISSED_OBJECT")
    v3b_refs = {r["V3B_REF"] for r in pf if r["V3B_REF"]}
    r5_unused = sorted({x for k in ops for x in json.loads(cen[k]["R5_IDS"] or "[]")} - v3b_refs)
    cv = [{"RECORD": "OPENING", "OPENING_ID": k, "FLOOR": cen[k]["FLOOR"], "KIND": cen[k]["KIND"],
           "TYPE": cen[k]["TYPE"], "STATE": "UNCHANGED"} for k in sorted(ops)]
    cv.append({"RECORD": "COUNT", "OPENING_ID": "ALL", "KIND": json.dumps(dict(sorted(kinds.items()))),
               "STATE": f"{len(ops)} ids; 01_OPENING_CENSUS.csv sha256 {_sha(READ['S86_CENSUS'])} = S8.6 manifest"})
    cv.append({"RECORD": "R5_MISSED", "OPENING_ID": ";".join(r5_missed), "STATE": f"{len(r5_missed)} villa wall "
               "openings with no R5 row (S8.6 summary r5_missed: population = the 65 wall openings vs R5)"})
    cv.append({"RECORD": "V3B_MISSED", "OPENING_ID": ";".join(v3b_missed), "STATE":
               f"{len(v3b_missed)} non-slab census openings with no V3b C-LINT detail (post-freeze MISSED_OBJECT: "
               "population = the 66 wall + boundary openings vs V3b's lintel details)"})
    cv.append({"RECORD": "DIFFERENCE", "OPENING_ID": ";".join(sorted(set(v3b_missed) - set(r5_missed))),
               "STATE": "in V3b-missed but not R5-missed: the boundary-wall gate, which is outside the villa wall "
                        "population R5 records (it is not a villa wall opening), so it can be missed by V3b without "
                        "being an R5 miss"})
    cv.append({"RECORD": "R5_ROWS_WITHOUT_V3B_DETAIL", "OPENING_ID": ";".join(r5_unused),
               "STATE": "R5 rows matched to a census opening that V3b gives no lintel detail (no width in R5): their "
                        "openings are still covered by V3b through the paired glazed-door row, so they are neither "
                        "missed nor double counted"})
    _csv(OUTPUTS[8], cv, ["RECORD", "OPENING_ID", "FLOOR", "KIND", "TYPE", "STATE"])
    L["census_check"] = {"ids": len(ops), "kinds": dict(kinds), "r5_missed": r5_missed, "v3b_missed": v3b_missed,
                         "difference": sorted(set(v3b_missed) - set(r5_missed)), "r5_unused": r5_unused}
    return reconcile(L, view, reb_rows, owners, retained)


def lane_reason(a):
    if a["state"] == RETAINED:
        return ("both bearings are drawn masonry >= 400 mm (independent trace); no beam band over the opening; "
                f"{a['head_basis']} gives a wall to carry (head not printed: Q-HEAD-GENERAL stands)")
    if a["state"] == WITHHELD_HEAD:
        return ("bearings confirmed, but the opening is glazing whose function (window or full-height) is unresolved "
                "and no head is printed: on this project printed sills show full-height glazing exists, so a wall "
                "above the head is not established. Not released automatically.")
    s = [f"{k} {_full(a['ends'][k][1]['available'], 1)} mm ({a['ends'][k][1]['terminator']})"
         for k in ("start", "end") if a["ends"][k][0] != LA.MASONRY_OK]
    return f"{a['cls']}: " + "; ".join(s) + " against MIN.40cm"


def reconcile(L, view, reb_rows, owners, retained):
    audit = L["audit"]
    floors = ("GF", "1F", "2F")
    rec = []

    fz = {v["LINTEL_ID"]: v for v in view}

    def add(stage, lids, m3_by_floor, kg_by_floor, note):
        rec.append({"STAGE": stage, "LINTELS": len(lids), "LINTEL_IDS": sorted(lids),
                    "M3": _r(sum(m3_by_floor.values())), "KG": _r(sum(kg_by_floor.values())),
                    **{f"M3_{f}": _r(m3_by_floor.get(f, 0.0)) for f in floors},
                    **{f"KG_{f}": _r(kg_by_floor.get(f, 0.0)) for f in floors}, "NOTE": note})

    def per_floor(ids, key, sign=1.0):
        m = defaultdict(float)
        for i in ids:
            m[fz[i]["FLOOR"]] += sign * fz[i][key]
        return m

    add("FROZEN", list(fz), per_floor(fz, "FROZEN_M3"), per_floor(fz, "FROZEN_KG"),
        "S8.6 released figures (history; unchanged)")
    for state in (LA.BLOCKED_BEARING, LA.BLOCKED_COLUMN, WITHHELD_HEAD):
        ids = [a["lid"] for a in audit if a["state"] == state]
        add(f"NEWLY_BLOCKED:{state}", ids, per_floor(ids, "FROZEN_M3", -1.0), per_floor(ids, "FROZEN_KG", -1.0),
            "frozen figures leave the released lane: " + "; ".join(f"{i} {fz[i]['REASON'][:90]}" for i in ids))
    for pair, v in owners.items():
        if v["corrected_owner"] != v["frozen_owner"] and v["corrected_owner"]:
            add("OVERLAP_REALLOCATION", list(pair), {fz[v["corrected_owner"]]["FLOOR"]: v["m3"]}, {},
                f"shared corner prism ({_full(v['mm2'], 1)} mm2 x {_full(v['m3'] / v['mm2'] * 1e9, 1)} mm) left the "
                f"release with {v['frozen_owner']} and returns with {v['corrected_owner']}, which also contains it")
    corr = [v for v in view if v["CORRECTED_LANE"] == "PROJECT_BASIS_QTO"]
    cm, ck = defaultdict(float), defaultdict(float)
    for v in corr:
        cm[v["FLOOR"]] += v["CORRECTED_M3"]
        ck[v["FLOOR"]] += v["CORRECTED_KG"]
    add("CORRECTED_RETAINED", [v["LINTEL_ID"] for v in corr], cm, ck, "eligible release after S8.6A")
    s = sum(r["M3"] for r in rec if r["STAGE"] != "CORRECTED_RETAINED")
    check(abs(s - rec[-1]["M3"]) < 1e-8, f"reconciliation closes ({s} vs {rec[-1]['M3']})")
    sk = sum(r["KG"] for r in rec if r["STAGE"] != "CORRECTED_RETAINED")
    check(abs(sk - rec[-1]["KG"]) < 1e-6, "kg reconciliation closes")
    by_floor = {}
    for f in floors:
        by_floor[f] = {"m3": _r(sum(v["CORRECTED_M3"] for v in corr if v["FLOOR"] == f)),
                       "kg_by_dia": {str(d): _r(sum(r["KG"] for r in reb_rows if r["FLOOR"] == f and
                                                    r["CORRECTED_LANE"] == "PROJECT_BASIS_QTO" and r["DIA_MM"] == d))
                                     for d in sorted({r["DIA_MM"] for r in reb_rows})}}
    for f in floors:
        check(abs(sum(r[f"M3_{f}"] for r in rec[:-1]) - rec[-1][f"M3_{f}"]) < 1e-8, f"{f} m3 reconciliation closes")
        check(abs(sum(r[f"KG_{f}"] for r in rec[:-1]) - rec[-1][f"KG_{f}"]) < 1e-6, f"{f} kg reconciliation closes")
    _csv(OUTPUTS[9], rec, ["STAGE", "LINTELS", "LINTEL_IDS", "M3", "KG", "M3_GF", "M3_1F", "M3_2F", "KG_GF", "KG_1F",
                           "KG_2F", "NOTE"])
    # a cross-check only: the eight-lintel view if the glazed opening were kept (not adopted)
    alt = [a for a in audit if a["cls"] == LA.CONFIRMED]
    alt_m3 = sum(a["gross_m3"] - sum(v["m3"] for p, v in owners.items() if a["lid"] in p and
                                     LA.assign_overlap(p[0], p[1], {b["lid"] for b in alt}) != a["lid"])
                 for a in alt)
    alt_kg = sum(r["KG"] for r in reb_rows if r["LINTEL_ID"] in {a["lid"] for a in alt})
    _csv(OUTPUTS[10], L["prev"], ["MANIFEST", "ROUND", "MANIFEST_SHA256", "OUTPUTS_VERIFIED", "RESULT"])
    summary = {
        "round": ROUND, "date": DATE, "baseline": BASELINE_HEAD, "policy": POLICY,
        "engine_commit": f"{BASELINE_HEAD}+code:{code_digest()}",
        "frozen": FROZEN, "s8_6_manifest_sha256": _sha(S86_MANIFEST),
        "states": dict(sorted(Counter(a["state"] for a in audit).items())),
        "six_cases": {lid: L["by"][lid]["cls"] for lid in SIX},
        "retained": sorted(retained),
        "corrected": {"lintels": len(retained), "m3": rec[-1]["M3"], "kg": rec[-1]["KG"], "by_floor": by_floor},
        "overlap": [{"pair": list(p), "m3": _r(v["m3"]), "frozen_owner": v["frozen_owner"],
                     "corrected_owner": v["corrected_owner"]} for p, v in sorted(owners.items())],
        "cross_check_not_adopted": {"bearing_confirmed_lintels": len(alt), "m3": _r(alt_m3), "kg": _r(alt_kg),
                                    "note": "all bearing-confirmed lintels incl. the glazed opening; not released"},
        "cover_and_stirrups": "25 mm is a nominal measurement cover (P8-N22 minimum, scope unconfirmed for lintels); "
                              "'5Ø8/M' is a rate only; counts, shapes and lengths are Urban conventions",
        "column_connection_rules_found": L["conn_rules"],
        "census": L["census_check"],
        "previous_freezes_verified": len(L["prev"]), "references_read": [],
        "post_freeze_use": "reference-population ids only (census question); no quantity selected from it"}
    _json(OUTPUTS[11], summary)
    (HERE / OUTPUTS[0]).write_text(readme(summary, view), encoding="utf-8")
    bad = [o for o in OUTPUTS if HYGIENE.search((HERE / o).read_text(encoding="utf-8"))]
    check(not bad, f"hygiene {bad}")
    manifest = {"round": ROUND, "date": DATE, "baseline": BASELINE_HEAD, "state": "DATED_CORRECTION_LAYER",
                "corrects": "research/alsenan_lintels_s8_6 (frozen; unchanged)",
                "s8_6_manifest_sha256": summary["s8_6_manifest_sha256"],
                "engine_commit_stamp": summary["engine_commit"], "references_read": [],
                "code": {c: _sha(ROOT / c) for c in CODE},
                "inputs": {str(p.relative_to(ROOT)): _sha(p) for p in READ.values()},
                "drawing_sha256": {"P7757.dxf": ARCH_SHA, "ST7757.dxf": STRUCT_SHA},
                "outputs": {o: _sha(HERE / o) for o in OUTPUTS}, "corrected": summary["corrected"],
                "rule": "the frozen S8.6 figures stay as history; this layer changes lanes only, with a reason for "
                        "each, and never selects a quantity from a post-freeze reference"}
    _json(MANIFEST_NAME, manifest)
    DR.verify_frozen(S86_MANIFEST, ROOT)
    return summary


def readme(s, view):
    c = s["corrected"]
    L = ["# S8.6A - lintel bearing, release authority and quantity reconciliation (dated correction layer)", "",
         f"Baseline `{BASELINE_HEAD}`, date {DATE}, stamp `{s['engine_commit']}`. The frozen S8.6 package is verified "
         "and never written.", "", "## Result", "",
         f"- Frozen S8.6 release: {s['frozen']['lintels']} lintels, {_full(s['frozen']['m3'])} m3, "
         f"{_full(s['frozen']['kg'])} kg (history).",
         f"- Corrected eligible release: **{c['lintels']} lintels, {_full(c['m3'])} m3, {_full(c['kg'])} kg**.",
         "- By floor: " + ", ".join(f"{f} {_full(v['m3'])} m3" for f, v in c["by_floor"].items()), "",
         "## Every lintel", "", "| Lintel | Frozen m3 | Corrected state | Corrected m3 | Reason |", "|---|---|---|---|---|"]
    for v in view:
        L.append(f"| {v['LINTEL_ID']} | {_full(v['FROZEN_M3'])} | {v['CORRECTED_STATE']} | "
                 f"{_full(v['CORRECTED_M3'])} | {v['REASON']} |")
    L += ["", "## Outputs", ""] + [f"- `{o}`" for o in OUTPUTS] + [f"- `{MANIFEST_NAME}`", "",
          "Rebuild: `python3 -I research/alsenan_lintels_s8_6a/build_s8_6a.py` (byte-identical)."]
    return "\n".join(L) + "\n"


if __name__ == "__main__":
    try:
        s = run()
    except Stop as e:
        print(f"STOP: {e}")
        sys.exit(1)
    print(json.dumps({k: s[k] for k in ("states", "six_cases", "retained", "corrected", "overlap",
                                        "cross_check_not_adopted", "census")}, indent=1, ensure_ascii=False))
