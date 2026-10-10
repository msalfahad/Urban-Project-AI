"""ALSENAN STRUCTURAL CENSUS S1 - source rules + occurrence census on ST7757 (no reinforcement quantities).

Reads ST7757.dxf (model space: seven plan sheets side by side, each inside a DEFPOINTS frame named by its title insert)
and the transcribed PDF pages (8-16) and builds the census through engine.source.structural_census:

    sheets   CAP column & axis plan (p.1) | FP foundation (p.2) | GBP ground beams (p.3) | GFRS ground-floor roof slab
             (p.4) | FFRS first-floor roof slab (p.5) | SFRS second-floor roof slab (p.6) | DET pool + dome (p.7)
    columns  closed S-COL.BON outlines per sheet; types from the tags of the axis plan (one-to-one assignment, the
             schedule never creates a column); positions followed sheet by sheet (vertical chains)
    footings S-FOOTINGS outlines + 'F' block inserts on FP, tags 'Cx/Fy', 'F8' ...
    beams    double lines on layer '1' (beam edges) paired into bands; every beam tag binds to one band
    slabs    faces of the beam / column / boundary linework (PLANAR_SHADOW_TOPOLOGY_V1)

No human / freelancer quantity is read (benchmark firewall, tested).
"""

from __future__ import annotations

import hashlib
import math
import re
from collections import Counter, defaultdict
from pathlib import Path

from engine.source import planar_shadow_topology as PT
from engine.source import structural_census as SC

ROOT = Path(__file__).resolve().parents[2]
DXF = ROOT / "data/inputs/by_sha256/9f9d1179a5d2a6635f9b412915a72184b7db1ff7729f4ab39a72dc3391738079.dxf"
DRAWING = "ST7757.dxf"
PDF = "ST7757.pdf"
PDF_SHA = "74da1523f05eb3c6a4fe3ddebaef2c3d841891f003efc03bc32a3fb4553337e3"
TITLE_INSERTS = {"CAP": ("COLUMN & AXIS PLAN", 1), "FP": ("FOUNDATION PLAN", 2), "GBP": ("GROUND BEAMS PLAN", 3),
                 "GFRS": ("GROUND FLOOR ROOF SLAB", 4), "FFRS": ("FIRST FLOOR ROOF SLAB", 5),
                 "SFRS": ("SECOND FLOOR ROOF SLAB", 6)}
SKIP_INSERTS = {"SBT", "FT", "CGT", "C-BEAM2", "C-BEAM3", "FTB", "CAP", "FP", "GBP", "GFRS", "FFRS", "SFRS",
                "A$C662819C0", "A$C7BD10DAB", "A$C60883738"}
COL_TAG = re.compile(r"^(C\d{0,2}|CN)$")
FOOT_TAG = re.compile(r"^(?:(?P<c>C\d{0,2}|CN)/)?(?P<f>F\d{0,2}|FF|FN)$")
BEAM_TAG = re.compile(r"^(B\d{1,2}|CB\d{1,2}|CA|S\.?B\d|B\.W|GB\d*)$")
# storey levels (column chain order, bottom -> top) and the storey each slab sheet closes
CHAIN_SHEETS = ["FP", "CAP", "GBP", "GFRS", "FFRS", "SFRS"]
STOREY_OF_SHEET = {"FP": "FOUNDATION", "CAP": "FOUNDATION", "GBP": "FOUNDATION", "GFRS": "GF", "FFRS": "1F",
                   "SFRS": "2F"}
FLOORS = ["FOUNDATION", "GF", "1F", "2F"]
SCHEDULE_FLOOR_KEY = {"FOUNDATION": "FOUNDATION", "GF": "GF", "1F": "1F", "2F": "2F_TOP"}


def _sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


# ===================================================================================================== source model
class Source:
    """The DXF split into sheets (local coordinates = model coordinates - frame origin)."""

    def __init__(self, path=DXF):
        import ezdxf
        from ezdxf import bbox as BB
        self.path = Path(path)
        self.sha256 = _sha(path)
        self.doc = ezdxf.readfile(str(path))
        msp = self.doc.modelspace()
        self.msp = msp
        frames = []
        for e in msp.query('LWPOLYLINE[layer=="DEFPOINTS"]'):
            b = BB.extents([e])
            if b.extmax.x - b.extmin.x > 20000 and b.extmax.y - b.extmin.y > 10000:
                frames.append((e.dxf.handle, (b.extmin.x, b.extmin.y, b.extmax.x, b.extmax.y)))
        self.sheets = {}
        for name in TITLE_INSERTS:
            ins = list(msp.query(f'INSERT[name=="{name}"]'))
            if len(ins) != 1:
                raise ValueError(f"title insert {name}: {len(ins)}")
            p = ins[0].dxf.insert
            hit = [f for f in frames if f[1][0] <= p.x <= f[1][2] and f[1][1] <= p.y <= f[1][3]]
            if len(hit) != 1:
                raise ValueError(f"sheet frame for {name}: {len(hit)}")
            self.sheets[name] = {"name": name, "title": TITLE_INSERTS[name][0], "pdf_page": TITLE_INSERTS[name][1],
                                 "frame_handle": hit[0][0], "frame": hit[0][1], "title_insert": ins[0].dxf.handle}
        used = {s["frame_handle"] for s in self.sheets.values()}
        # the details sheet (pool / dome) is the frame holding the S-TEXT.D 'DETAIL OF SWIMMING POOL' text
        for h, f in frames:
            if h in used:
                continue
            for t in msp.query("TEXT"):
                if "SWIMMING POOL" in (t.dxf.text or "").upper() and f[0] <= t.dxf.insert.x <= f[2] \
                        and f[1] <= t.dxf.insert.y <= f[3] and t.dxf.layer == "S-TEXT.D":
                    self.sheets["DET"] = {"name": "DET", "title": "DETAILS (pool / dome)", "pdf_page": 7,
                                          "frame_handle": h, "frame": f, "title_insert": None}
                    break
        self._ents = None

    def sheet_of(self, x, y):
        for k, s in self.sheets.items():
            a, b, c, d = s["frame"]
            if a <= x <= c and b <= y <= d:
                return k
        return None

    def local(self, sheet, x, y):
        f = self.sheets[sheet]["frame"]
        return (round(x - f[0], 3), round(y - f[1], 3))

    # ---------------------------------------------------------------------------------------------------- entities
    def entities(self):
        """All primitives with sheet, local geometry and provenance (model space + exploded non-schedule inserts)."""
        if self._ents is not None:
            return self._ents
        from ezdxf import bbox as BB
        out = defaultdict(list)

        def lay(e):
            try:
                return e.dxf.layer
            except Exception:
                return None

        def add(e, via=None):
            t = e.dxftype()
            L = lay(e)
            if L is None:
                return
            rec = {"handle": e.dxf.handle if via is None else f"{via}>{e.dxf.handle or 'v'}", "type": t, "layer": L,
                   "via": via}
            if t == "LINE":
                a, b = e.dxf.start, e.dxf.end
                s = self.sheet_of(a.x, a.y)
                if s is None:
                    return
                rec.update(sheet=s, a=self.local(s, a.x, a.y), b=self.local(s, b.x, b.y))
            elif t in ("TEXT", "MTEXT"):
                p = e.dxf.insert
                s = self.sheet_of(p.x, p.y)
                if s is None:
                    return
                txt = e.dxf.text if t == "TEXT" else e.text
                rec.update(sheet=s, p=self.local(s, p.x, p.y), text=(txt or "").strip(),
                           rotation=round(float(e.dxf.get("rotation", 0.0)) % 360.0, 3),
                           height=float((e.dxf.get("height", 0.0) if t == "TEXT" else e.dxf.get("char_height", 0.0))
                                        or 0.0))
            elif t == "LWPOLYLINE":
                pts = [(p[0], p[1]) for p in e.get_points("xy")]
                if not pts:
                    return
                s = self.sheet_of(sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts))
                if s is None:
                    return
                bul = [p[4] for p in e.get_points("xyseb")]
                rec.update(sheet=s, pts=[self.local(s, *p) for p in pts], closed=bool(e.closed),
                           has_bulge=any(abs(b) > 1e-9 for b in bul))
                segs = []
                for v in e.virtual_entities():
                    if v.dxftype() == "LINE":
                        segs.append((self.local(s, v.dxf.start.x, v.dxf.start.y), self.local(s, v.dxf.end.x, v.dxf.end.y)))
                    elif v.dxftype() == "ARC":
                        c = v.dxf.center
                        cl = self.local(s, c.x, c.y)
                        segs.append(("ARC", cl, v.dxf.radius, math.radians(v.dxf.start_angle), math.radians(v.dxf.end_angle)))
                rec["segs"] = segs
            elif t in ("ARC", "CIRCLE"):
                c = e.dxf.center
                s = self.sheet_of(c.x, c.y)
                if s is None:
                    return
                rec.update(sheet=s, c=self.local(s, c.x, c.y), r=e.dxf.radius,
                           a0=math.radians(e.dxf.get("start_angle", 0.0)) if t == "ARC" else 0.0,
                           a1=math.radians(e.dxf.get("end_angle", 360.0)) if t == "ARC" else 2 * math.pi)
            elif t in ("HATCH", "SOLID", "INSERT", "DIMENSION"):
                try:
                    b = BB.extents([e])
                except Exception:
                    return
                if not b.has_data:
                    return
                s = self.sheet_of((b.extmin.x + b.extmax.x) / 2, (b.extmin.y + b.extmax.y) / 2)
                if s is None:
                    return
                lo = self.local(s, b.extmin.x, b.extmin.y)
                hi = self.local(s, b.extmax.x, b.extmax.y)
                rec.update(sheet=s, bbox=(lo[0], lo[1], hi[0], hi[1]))
                if t == "INSERT":
                    rec["name"] = e.dxf.name
                    rec["scale"] = (round(e.dxf.xscale, 6), round(e.dxf.yscale, 6))
                    rec["rotation"] = round(e.dxf.rotation, 6)
                if t == "DIMENSION":
                    try:
                        rec["measurement"] = round(e.get_measurement(), 3)
                    except Exception:
                        rec["measurement"] = None
                    rec["text_override"] = e.dxf.get("text", "")
            else:
                return
            out[rec["sheet"]].append(rec)

        for e in self.msp:
            add(e)
            if e.dxftype() == "INSERT" and e.dxf.name not in SKIP_INSERTS:
                for v in e.virtual_entities():
                    add(v, via=f"{e.dxf.handle}:{e.dxf.name}")
        self._ents = out
        return out

    def texts(self, sheet, layers=None):
        return [e for e in self.entities()[sheet] if e["type"] in ("TEXT", "MTEXT")
                and (layers is None or e["layer"] in layers)]

    def lines(self, sheet, layers):
        return [e for e in self.entities()[sheet] if e["type"] == "LINE" and e["layer"] in layers]

    def polys(self, sheet, layers):
        return [e for e in self.entities()[sheet] if e["type"] == "LWPOLYLINE" and e["layer"] in layers]


# ===================================================================================================== axes / grid
def axes(src, sheet="CAP"):
    """Grid axes (layer S-AXIS) of the axis plan: X (vertical lines) numbered left -> right, Y bottom -> top."""
    vx, hy = [], []
    for e in src.lines(sheet, {"S-AXIS"}):
        (x0, y0), (x1, y1) = e["a"], e["b"]
        if abs(x0 - x1) < 1:
            vx.append({"pos": round(x0, 1), "span": (min(y0, y1), max(y0, y1)), "handle": e["handle"]})
        elif abs(y0 - y1) < 1:
            hy.append({"pos": round(y0, 1), "span": (min(x0, x1), max(x0, x1)), "handle": e["handle"]})
    vx.sort(key=lambda a: a["pos"])
    hy.sort(key=lambda a: a["pos"])
    for i, a in enumerate(vx):
        a["axis_id"] = f"X{i + 1:02d}"
    for i, a in enumerate(hy):
        a["axis_id"] = f"Y{i + 1:02d}"
    return {"X": vx, "Y": hy}


def grid_ref(ax, x, y, tol=450.0):
    """Nearest X axis covering y and nearest Y axis covering x (within tol of the column centre)."""
    def pick(lst, coord, other):
        best = None
        for a in lst:
            if a["span"][0] - 600 <= other <= a["span"][1] + 600:
                d = abs(a["pos"] - coord)
                if d <= tol and (best is None or d < best[0]):
                    best = (d, a["axis_id"])
        return best[1] if best else None
    return pick(ax["X"], x, y), pick(ax["Y"], y, x)


# ===================================================================================================== columns
def column_outlines(src, sheet):
    out = []
    hatches = [e for e in src.entities()[sheet] if e["type"] in ("HATCH", "SOLID") and e["layer"] == "S-COL.HAT"]
    for e in src.polys(sheet, {"S-COL.BON"}):
        xs = [p[0] for p in e["pts"]]
        ys = [p[1] for p in e["pts"]]
        bb = (min(xs), min(ys), max(xs), max(ys))
        w, h = bb[2] - bb[0], bb[3] - bb[1]
        hatched = any(SC.bbox_overlap(bb, hb["bbox"], 5.0) > 0.5 * w * h for hb in hatches)
        out.append({"id": f"{sheet}:{e['handle']}", "handle": e["handle"], "sheet": sheet, "bbox": tuple(round(v, 1) for v in bb),
                    "centre": (round((bb[0] + bb[2]) / 2, 1), round((bb[1] + bb[3]) / 2, 1)),
                    "dx_mm": round(w, 1), "dy_mm": round(h, 1), "long_mm": round(max(w, h), 1),
                    "short_mm": round(min(w, h), 1), "orientation": "X" if w >= h else "Y", "closed": e["closed"],
                    "hatched": hatched, "vertices": len(e["pts"])})
    out.sort(key=lambda o: (o["centre"][1], o["centre"][0]))
    return out


def _text_centre(t):
    h = t.get("height") or 200.0
    w = len(t["text"]) * h * 0.8
    r = math.radians(t.get("rotation") or 0.0)
    return (t["p"][0] + math.cos(r) * w / 2 - math.sin(r) * h / 2, t["p"][1] + math.sin(r) * w / 2 + math.cos(r) * h / 2)


def assign_tags(outlines, tags, *, max_d=2600.0):
    """One-to-one tag -> outline assignment minimising total distance (scipy Hungarian). A pair farther than max_d is
    rejected (tag stays UNBOUND, outline stays UNTAGGED)."""
    from scipy.optimize import linear_sum_assignment
    if not outlines or not tags:
        return {}, [t["handle"] for t in tags]
    cost = [[math.dist(_text_centre(t), o["centre"]) for o in outlines] for t in tags]
    ri, ci = linear_sum_assignment(cost)
    out, unbound = {}, []
    for i, j in zip(ri, ci):
        if cost[i][j] <= max_d:
            out[outlines[j]["id"]] = {"tag": tags[i]["text"], "tag_handle": tags[i]["handle"],
                                      "distance_mm": round(cost[i][j], 1)}
        else:
            unbound.append(tags[i]["handle"])
    unbound += [tags[i]["handle"] for i in range(len(tags)) if i not in set(ri)]
    return out, unbound


def size_labels(src, sheet):
    """'30X50' size texts beside the axis-plan tags (cm, B x D)."""
    out = []
    for t in src.texts(sheet, {"S-TEXT"}):
        m = re.fullmatch(r"(\d+)\s*[Xx]\s*(\d+)", t["text"])
        if m:
            out.append({"handle": t["handle"], "b_cm": int(m.group(1)), "d_cm": int(m.group(2)), "p": t["p"],
                        "raw": t["text"]})
    return out


# ===================================================================================================== schedules
def schedules():
    """Typed schedule definitions from the DXF schedule blocks (control-plane reader V2) + the CN row (loose texts)."""
    import alsenan_structural_source_v2 as SRC
    raw = SRC.read(DXF)
    d = SRC.definitions(raw)
    return raw, d


def cn_schedule_row(src):
    """CN row of the column schedule: separate TEXT entities on S-TEXT.SCH in one row (y within 60 units of 'CN')."""
    texts = [e for e in src.msp.query("TEXT") if e.dxf.layer == "S-TEXT.SCH"]
    cn = [t for t in texts if t.dxf.text.strip() == "CN"]
    if len(cn) != 1:
        return None
    y = cn[0].dxf.insert.y
    x0 = cn[0].dxf.insert.x
    row = sorted([t for t in texts if abs(t.dxf.insert.y - y) < 60 and 0 < t.dxf.insert.x - x0 < 6000],
                 key=lambda t: t.dxf.insert.x)
    vals = [t.dxf.text.strip() for t in row]
    hs = [cn[0].dxf.handle] + [t.dxf.handle for t in row]
    try:
        b, d, n, sym, dia = vals[:5]
        assert sym.upper() == "%%C"
        return {"type": "CN", "band": "FOUNDATION", "B_cm": float(b), "D_cm": float(d), "bars": int(n),
                "dia_mm": int(dia), "handles": hs, "raw": vals, "other_bands": "dash (absent) in the PDF row"}
    except Exception:
        return {"type": "CN", "state": "BLOCKED_INTERPRETATION", "raw": vals, "handles": hs}


# ===================================================================================================== column census
def _norm_tag(t):
    t = t.strip().upper()
    m = FOOT_TAG.match(t)
    if m and m.group("c"):
        return m.group("c")
    return t if COL_TAG.match(t) else None


def column_census(src):
    ax = axes(src)
    out = {"axes": ax, "sheets": {}, "outlines": {}, "tags": {}}
    for sh in CHAIN_SHEETS:
        out["outlines"][sh] = column_outlines(src, sh)
    # tags: axis plan (authority), foundation plan and ground-beam plan (corroboration)
    tag_sheets = {"CAP": None, "FP": None, "GBP": None}
    for sh in tag_sheets:
        tags = [t for t in src.texts(sh, {"S-TEXT"}) if _norm_tag(t["text"])]
        tags = [dict(t, text=_norm_tag(t["text"])) for t in tags]
        asg, unbound = assign_tags(out["outlines"][sh], tags)
        out["tags"][sh] = {"assigned": asg, "unbound": unbound, "n_tags": len(tags)}
    # size labels on the axis plan, each bound to the nearest tag above-right of it
    sizes = size_labels(src, "CAP")
    cap_tags = {t["handle"]: t for t in src.texts("CAP", {"S-TEXT"}) if _norm_tag(t["text"])}
    tag_size = {}
    if sizes and cap_tags:
        from scipy.optimize import linear_sum_assignment
        tl = sorted(cap_tags.values(), key=lambda t: t["handle"])
        cost = [[math.dist(t["p"], (s_["p"][0] + 360, s_["p"][1] + 420)) for s_ in sizes] for t in tl]
        ri, ci = linear_sum_assignment(cost)
        for i, j in zip(ri, ci):
            if cost[i][j] < 900:
                tag_size[tl[i]["handle"]] = dict(sizes[j], offset_mm=round(cost[i][j], 1))
    out["size_labels"] = {"bound": {k: v for k, v in tag_size.items()}, "n": len(sizes)}
    # slab-sheet labels: P.C (planted), T.C (turn / twisted), D.C (dead)
    labels = []
    for sh in ("GFRS", "FFRS", "SFRS"):
        for t in src.texts(sh):
            u = t["text"].upper().replace(" ", "")
            if re.match(r"^P[./]C\d", u) or u in ("T.C", "D.C", "P.C", "P/C") or re.match(r"^P[./]C", u):
                labels.append(dict(t, label=u))
    out["slab_labels"] = labels
    # vertical chains on the plan outlines
    occ = {sh: [dict(o) for o in out["outlines"][sh]] for sh in CHAIN_SHEETS}
    chains = SC.vertical_chains(CHAIN_SHEETS, occ)
    viol = SC.chain_check(chains, CHAIN_SHEETS, occ)
    byid = {o["id"]: o for sh in occ for o in occ[sh]}
    # TURN merge: a chain that starts on a slab sheet overlapping (same sheet) the top outline of a chain that stops
    # on that sheet is the rotated upper part of the same physical column (T.C / twisted column)
    merged = []
    for ch in chains:
        ch["_dead"] = False
    for ch in chains:
        start = min(ch["members"], key=CHAIN_SHEETS.index)
        if start not in ("GFRS", "FFRS") or not any(e["event"] == "OVERLAPS_BELOW_NOT_LINKED" for e in ch["events"]):
            continue
        so = byid[ch["members"][start]]
        for other in chains:
            if other is ch or other["_dead"]:
                continue
            top = max(other["members"], key=CHAIN_SHEETS.index)
            if top != start:
                continue
            to = byid[other["members"][top]]
            if SC.bbox_overlap(so["bbox"], to["bbox"]) > 1.0 and so["orientation"] != to["orientation"]:
                other["turn"] = {"sheet": start, "lower_outline": to["id"], "upper_outline": so["id"],
                                 "lower_orientation": to["orientation"], "upper_orientation": so["orientation"]}
                for lv, oid in ch["members"].items():
                    if lv == start:
                        other.setdefault("transition_outlines", {})[lv] = oid
                    else:
                        other["members"][lv] = oid
                other["events"] = [e for e in other["events"] if e["event"] != "AMBIGUOUS_LINK"]
                other["events"].append({"level": start, "event": "TURN_ORIENTATION_CHANGE",
                                        "from": to["orientation"], "to": so["orientation"]})
                ch["_dead"] = True
                merged.append((other, ch))
                break
    chains = [c for c in chains if not c["_dead"]]
    out["chain_violations"] = viol
    out["chains_raw"] = chains
    out["byid"] = byid
    return out


# ----------------------------------------------------------------------------------------------- tie topology rules
TIE_BANDS = [
    {"band_id": "TIE_L_LE_50", "lo": None, "lo_incl": False, "hi": 50, "hi_incl": True,
     "printed": "L ≤ 50cm"},
    {"band_id": "TIE_50_LT_L_LT_80", "lo": 50, "lo_incl": False, "hi": 80, "hi_incl": False,
     "printed": "50cm < L < 80cm"},
    {"band_id": "TIE_80_LT_L_LT_120", "lo": 80, "lo_incl": False, "hi": 120, "hi_incl": False,
     "printed": "80cm < L < 120cm"},
]
MIN_T_TABLE = [  # p.9 'DETAILS OF COLUMN REINFORCEMENT' box: H = height of floor, T = thickness of column
    {"lo": None, "lo_incl": False, "hi": 4.3, "hi_incl": True, "t_min_cm": 20, "printed": "H ≤ 4.3 m -> T min = 20 cm"},
    {"lo": 4.3, "lo_incl": True, "hi": 4.7, "hi_incl": True, "t_min_cm": 25,
     "printed": "4.7 m ≥ H ≥ 4.3 m -> T min = 25 cm"},
    {"lo": 4.7, "lo_incl": True, "hi": 5.0, "hi_incl": True, "t_min_cm": 30,
     "printed": "5 m ≥ H ≥ 4.7 m -> T min = 30 cm"},
]


def tie_topology(src):
    """Deterministic reading of the p.9 detail: per band row the concrete outline (S-EXTL.D), the closed ties
    (S-REIN.D rectangles, section + exploded sketch) and the bar dots (2-vertex closed polylines with width)."""
    rows = []
    det = []
    for e in src.msp:
        try:
            L = e.dxf.layer
        except Exception:
            continue
        if e.dxftype() == "LWPOLYLINE" and L in ("S-REIN.D", "S-EXTL.D"):
            pts = [(p[0], p[1]) for p in e.get_points("xy")]
            xs, ys = [p[0] for p in pts], [p[1] for p in pts]
            det.append({"handle": e.dxf.handle, "layer": L, "bbox": (min(xs), min(ys), max(xs), max(ys)),
                        "n": len(pts), "closed": bool(e.closed), "width": float(e.dxf.get("const_width", 0.0))})
    # anchor: the 'ST. OF COLUMN' note; the detail lies below it within 13 m to the right
    note = [t for t in src.msp.query("TEXT") if "ST. OF COLUMN" in (t.dxf.text or "")]
    if len(note) != 1:
        return {"state": "BLOCKED", "why": "column tie note not found once"}
    nx, ny = note[0].dxf.insert.x, note[0].dxf.insert.y
    det = [d for d in det if nx - 2000 < d["bbox"][0] < nx + 16000 and ny - 8000 < d["bbox"][1] < ny]
    outlines = sorted([d for d in det if d["layer"] == "S-EXTL.D" and d["closed"] and d["n"] == 4],
                      key=lambda d: -d["bbox"][3])
    for band, o in zip(TIE_BANDS, outlines):
        ob = o["bbox"]
        W, H = ob[2] - ob[0], ob[3] - ob[1]
        in_sec = [d for d in det if d["layer"] == "S-REIN.D" and d["n"] == 4 and d["closed"]
                  and ob[0] - 10 <= d["bbox"][0] and d["bbox"][2] <= ob[2] + 10 and ob[1] - 10 <= d["bbox"][1]
                  and d["bbox"][3] <= ob[3] + 10]
        sketch = [d for d in det if d["layer"] == "S-REIN.D" and d["n"] == 4 and d["closed"]
                  and d["bbox"][0] > ob[2] + 50 and abs((d["bbox"][1] + d["bbox"][3]) / 2 - (ob[1] + ob[3]) / 2) < H]
        dots = [d for d in det if d["layer"] == "S-REIN.D" and d["n"] == 2 and d["closed"] and d["width"] > 0
                and ob[0] <= d["bbox"][0] <= ob[2] and ob[1] <= d["bbox"][1] <= ob[3]]
        ties = sorted(in_sec, key=lambda d: d["bbox"][0])
        rows.append({
            "band_id": band["band_id"], "printed_condition": band["printed"],
            "detail_concrete_outline": {"handle": o["handle"], "L_units": round(W, 1), "T_units": round(H, 1),
                                        "aspect_L_over_T": round(W / H, 2)},
            "closed_ties_in_section": len(ties),
            "closed_ties_in_sketch": len(sketch),
            "tie_spans_as_fraction_of_L": [round((d["bbox"][2] - d["bbox"][0]) / W, 3) for d in ties],
            "tie_offsets_as_fraction_of_L": [round((d["bbox"][0] - ob[0]) / W, 3) for d in ties],
            "tie_handles": [d["handle"] for d in ties], "sketch_handles": [d["handle"] for d in sketch],
            "bars_drawn": len(dots), "bars_per_long_face_drawn": len(dots) // 2 if len(dots) % 2 == 0 else None,
            "state": "EXACT_RULE" if len(ties) == len(sketch) and ties else "SOURCE_CONFLICT",
            "topology": {1: "one closed perimeter tie", 2: "two overlapping closed ties (each spans part of L)",
                         3: "two overlapping closed ties + one small central closed tie"}.get(len(ties), "unknown"),
            "corroboration": ["DXF geometry (this count)", "ST7757.pdf p.9 raster (same drawing)",
                              "DXF condition text"],
        })
    return {"state": "READ", "ties_rule": {"raw": "ST. OF COLUMN- 6Ø8/m", "normalised": "column ties Ø8, 6 per metre",
                                           "source_handle": note[0].dxf.handle,
                                           "per_metre_semantics": "BLOCKED_METHOD - 6 tie SETS per metre (all closed "
                                                                  "ties of the band at each level) or 6 single ties "
                                                                  "per metre is not stated"},
            "L_definition": "L = LENGTH OF COLUMN (long side of the section)",
            "bands": rows,
            "gaps": [{"value_cm": 80, "state": "BOUNDARY_GAP",
                      "why": "printed bands are 50 < L < 80 and 80 < L < 120 - L = 80 cm is in neither"},
                     {"value_cm": 120, "state": "OUT_OF_RANGE_AT_AND_ABOVE",
                      "why": "no band for L ≥ 120 cm (no column in the schedule reaches it)"}],
            "min_thickness_table": MIN_T_TABLE}


# ----------------------------------------------------------------------------------------------- column registers
def _band_key(storey):
    return {"FOUNDATION": "FOU", "GF": "GR", "1F": "1ST", "2F": "2ND"}[storey]


def column_registers(src, C, defs, levels):
    """Occurrence rows (one per column per storey), vertical chains, type x floor matrix, definitions."""
    byid = C["byid"]
    ax = C["axes"]
    cdefs = {d["type"]: d for d in defs["definitions"] if d["element"] == "COLUMN"}
    cn = cn_schedule_row(src)
    tag_of = {}
    for sh, t in C["tags"].items():
        for oid, rec in t["assigned"].items():
            tag_of[oid] = dict(rec, sheet=sh)
    size_of_tag = C["size_labels"]["bound"]
    storey_h = {lv["storey"]: lv.get("floor_to_floor_m") for lv in levels if lv.get("storey")}
    # label binding (planted / turn / dead)
    starts = {}
    for ch in C["chains_raw"]:
        st = min(ch["members"], key=CHAIN_SHEETS.index)
        starts.setdefault(st, []).append(ch)
    label_bind = []
    for lab in C["slab_labels"]:
        sh = lab["sheet"]
        if lab["label"].startswith(("P.C", "P/C")):
            cands = [(math.dist(lab["p"], byid[ch["members"][sh]]["centre"]), ch) for ch in starts.get(sh, [])]
        elif lab["label"] == "T.C":
            cands = [(math.dist(lab["p"], byid[ch["turn"]["lower_outline"]]["centre"]), ch) for ch in C["chains_raw"]
                     if ch.get("turn", {}).get("sheet") == sh]
        else:  # D.C dead column: a chain stopping on this sheet
            cands = [(math.dist(lab["p"], byid[ch["members"][sh]]["centre"]), ch) for ch in C["chains_raw"]
                     if max(ch["members"], key=CHAIN_SHEETS.index) == sh and sh in ch["members"]]
        cands.sort(key=lambda c: c[0])
        ok = cands and cands[0][0] < 4500 and (len(cands) == 1 or cands[1][0] - cands[0][0] > 400)
        label_bind.append({"label": lab["label"], "sheet": sh, "handle": lab["handle"], "text": lab["text"],
                           "position": lab["p"], "bound_chain": id(cands[0][1]) if ok else None,
                           "distance_mm": round(cands[0][0], 1) if cands else None,
                           "state": "BOUND" if ok else ("AMBIGUOUS" if cands else "UNBOUND")})
    chains, occ_rows = [], []
    for ch in sorted(C["chains_raw"], key=lambda c: (byid[list(c["members"].values())[0]]["centre"][1],
                                                     byid[list(c["members"].values())[0]]["centre"][0])):
        mem = ch["members"]
        first = byid[mem[min(mem, key=CHAIN_SHEETS.index)]]
        gx, gy = grid_ref(ax, *first["centre"])
        labels = [lb for lb in label_bind if lb["bound_chain"] == id(ch)]
        # type evidence
        tags = {}
        for sh in ("CAP", "FP", "GBP"):
            if sh in mem and mem[sh] in tag_of:
                tags[sh] = tag_of[mem[sh]]
        tvals = sorted({t["tag"] for t in tags.values()})
        planted = [lb for lb in labels if lb["label"].startswith(("P.C", "P/C"))]
        if planted:
            m = re.search(r"(\d+)X(\d+)", planted[0]["label"])
            ctype = "P.C"
            type_state = "PLAN_LABEL"
            pc_size = (int(m.group(1)), int(m.group(2))) if m else None
        elif len(tvals) == 1:
            ctype, type_state, pc_size = tvals[0], ("AXIS_PLAN_TAG" if "CAP" in tags else "FOUNDATION_PLAN_TAG"), None
        elif len(tvals) > 1:
            ctype, type_state, pc_size = (tags["CAP"]["tag"] if "CAP" in tags else None), "TAG_CONFLICT", None
        else:
            ctype, type_state, pc_size = None, "UNTAGGED", None
        start_sheet = min(mem, key=CHAIN_SHEETS.index)
        top_sheet = max(mem, key=CHAIN_SHEETS.index)
        storeys = []
        if any(s in mem for s in ("FP", "CAP", "GBP")):
            storeys.append("FOUNDATION")
        for sh, st, below in (("GFRS", "GF", ("FP", "CAP", "GBP")), ("FFRS", "1F", ("GFRS",)), ("SFRS", "2F", ("FFRS",))):
            if sh in mem and any(b in mem for b in below):
                storeys.append(st)
        planted_on = None
        if start_sheet in ("GFRS", "FFRS"):
            planted_on = {"GFRS": "GF_ROOF_SLAB", "FFRS": "1F_ROOF_SLAB"}[start_sheet]
        pos = f"{gx or 'X?'}-{gy or 'Y?'}"
        chain_id = f"COLPOS-{pos}-{first['centre'][0]:.0f}-{first['centre'][1]:.0f}"
        for lb in labels:
            lb["bound_chain_id"] = chain_id
        ev = list(ch["events"])
        if "CAP" not in mem and any(s in mem for s in ("FP", "GBP")):
            ev.append({"event": "MISSING_ON_AXIS_PLAN", "levels": ["CAP"]})
        rows_here = []
        for st in storeys:
            sheet_members = [sh for sh in CHAIN_SHEETS if STOREY_OF_SHEET[sh] == st and sh in mem]
            o = byid[mem[sheet_members[-1]]] if st != "FOUNDATION" else byid[mem[[s for s in ("CAP", "FP", "GBP")
                                                                                   if s in mem][0]]]
            d = cdefs.get(ctype)
            band = d["fields"]["bands"].get(_band_key(st)) if d else None
            if ctype == "CN" and st == "FOUNDATION" and cn and "B_cm" in cn:
                band = {"B_cm": cn["B_cm"], "H_cm": cn["D_cm"], "bars": {"count": cn["bars"], "dia_mm": cn["dia_mm"]}}
            if ctype == "P.C":
                pb = None
                for lb in planted:
                    # the bar text printed under the P.C label (S-TEXT-SLAB, within 700 mm below)
                    near = [t for t in src.texts(lb["sheet"], {"S-TEXT-SLAB"})
                            if re.fullmatch(r"\d+%%[cC]\d+", t["text"]) and 0 < lb["position"][1] - t["p"][1] < 700
                            and abs(lb["position"][0] - t["p"][0]) < 700]
                    if len(near) == 1:
                        mm = re.fullmatch(r"(\d+)%%[cC](\d+)", near[0]["text"])
                        pb = {"count": int(mm.group(1)), "dia_mm": int(mm.group(2)), "text_handle": near[0]["handle"]}
                if pc_size:
                    band = {"B_cm": pc_size[0], "H_cm": pc_size[1], "bars": pb or {"state": "BLOCKED"}}
            def_state = "FULL" if band and band.get("bars", {}).get("count") else ("NONE" if not band else "PARTIAL")
            sched_L = max(band["B_cm"], band["H_cm"]) if band else None
            sched_T = min(band["B_cm"], band["H_cm"]) if band else None
            drawn_L, drawn_T = o["long_mm"] / 10.0, o["short_mm"] / 10.0
            size_match = None if band is None else (abs(drawn_L - sched_L) <= 2.5 and abs(drawn_T - sched_T) <= 2.5)
            tb = SC.tie_band(sched_L, TIE_BANDS) if sched_L else {"state": "BLOCKED", "band": None}
            h = storey_h.get(st)
            tmin = SC.min_thickness_check(h, sched_T, MIN_T_TABLE) if (h and sched_T and st != "FOUNDATION") else None
            if type_state == "TAG_CONFLICT":
                term = "COUNTED_DEFINITION_PARTIAL"
            else:
                term = SC.terminal_state(counted=True, definition=def_state)
            rows_here.append({
                "column_id": f"COL-{ctype or 'UNTYPED'}-{pos if '?' not in pos else pos + '@' + chain_id.split('-', 3)[3]}-{st}",
                "chain_id": chain_id, "floor": st,
                "column_type": ctype, "type_authority": type_state,
                "type_inheritance": "AXIS_PLAN_TAG_INHERITED_UP_THE_CHAIN" if st not in ("FOUNDATION",) and
                                    type_state in ("AXIS_PLAN_TAG", "FOUNDATION_PLAN_TAG") else None,
                "grid": {"X": gx, "Y": gy}, "plan_centre_mm": o["centre"],
                "plan_source": {"drawing": DRAWING, "sheets": sheet_members if st != "FOUNDATION" else
                                [s for s in ("FP", "CAP", "GBP") if s in mem],
                                "handles": [mem[s].split(":")[1] for s in CHAIN_SHEETS if STOREY_OF_SHEET[s] == st
                                            and s in mem]},
                "drawn_section_cm": [round(o["dx_mm"] / 10, 1), round(o["dy_mm"] / 10, 1)],
                "orientation": o["orientation"],
                "schedule_section_cm": [band["B_cm"], band["H_cm"]] if band else None,
                "drawn_vs_schedule": None if size_match is None else ("MATCH" if size_match else "MISMATCH"),
                "longitudinal_bars": band.get("bars") if band else None,
                "tie_rule": "6Ø8/m (p.9 general note)",
                "tie_topology_band": tb,
                "min_thickness_check": tmin,
                "definition_state": def_state,
                "terminal_state": term,
                "status": "SOURCE_CONFLICT" if type_state == "TAG_CONFLICT" else ("PROVISIONAL" if def_state != "FULL"
                                                                                 else "COUNTED"),
            })
        for i, r in enumerate(rows_here):
            r["continues_from_below"] = i > 0 or planted_on is None and r["floor"] != "FOUNDATION"
            r["continues_above"] = i < len(rows_here) - 1
            r["type_below"] = rows_here[i - 1]["column_type"] if i > 0 else None
            r["type_above"] = rows_here[i + 1]["column_type"] if i < len(rows_here) - 1 else None
            r["planted_on"] = planted_on if i == 0 else None
        occ_rows += rows_here
        chains.append({
            "chain_id": chain_id, "grid": {"X": gx, "Y": gy}, "column_type": ctype, "type_authority": type_state,
            "tags_by_plan": {k: {"tag": v["tag"], "handle": v["tag_handle"], "distance_mm": v["distance_mm"]}
                             for k, v in tags.items()},
            "axis_plan_size_label": size_of_tag.get(tags["CAP"]["tag_handle"], {}).get("raw") if "CAP" in tags else None,
            "members_by_sheet": {k: v.split(":")[1] for k, v in mem.items()},
            "transition_outlines": {k: v.split(":")[1] for k, v in ch.get("transition_outlines", {}).items()},
            "turn": ch.get("turn"), "labels": [{k: v for k, v in lb.items() if k != "bound_chain"} for lb in labels],
            "starts_at": "FOUNDATION" if storeys and storeys[0] == "FOUNDATION" else (storeys[0] if storeys else None),
            "planted_on": planted_on, "continues_through": storeys,
            "terminates_at": storeys[-1] if storeys else None,
            "changes_type_at": [e for e in ev if e["event"] in ("TYPE_CHANGE", "TURN_ORIENTATION_CHANGE")],
            "events": ev,
            "source_evidence": {"drawing": DRAWING, "sha256": src.sha256,
                                "sheets": {k: src.sheets[k]["pdf_page"] for k in mem}},
        })
    for lb in label_bind:  # the object identity was only a binding key; never export it
        lb.pop("bound_chain", None)
        lb.setdefault("bound_chain_id", None)
    unbound_labels = [lb for lb in label_bind if lb["state"] != "BOUND"]
    return {"occurrences": occ_rows, "chains": chains, "labels": label_bind, "unbound_labels": unbound_labels,
            "cn_row": cn, "definitions": cdefs}


# ===================================================================================================== beam bands
BEAM_LAYERS = {"1", "S-BEAM"}
BEAM_W_MM = (120.0, 1050.0)


def detail_zones(src, sheet):
    """Rectangles holding section / detail drawings inside a plan sheet (around 'SECTION x-x' titles and the
    S-REIN.D section geometry): excluded from plan member extraction."""
    zones = []
    titles = [t for t in src.texts(sheet) if "SECTION" in t["text"].upper()]
    rein = [e for e in src.entities()[sheet] if e["layer"] == "S-REIN.D" and e["type"] in ("LWPOLYLINE", "LINE")]
    for t in titles:
        x, y = t["p"]
        pts = []
        for e in rein:
            for p in (e.get("pts") or [e["a"], e["b"]]):
                if x - 1500 <= p[0] <= x + 4500 and y - 200 <= p[1] <= y + 6500:
                    pts.append(p)
        if pts:
            xs, ys = [p[0] for p in pts], [p[1] for p in pts]
            zones.append((min(xs) - 600, min(ys) - 600, max(xs) + 600, max(ys) + 600))
    return zones


def _in_zone(p, zones):
    return any(z[0] <= p[0] <= z[2] and z[1] <= p[1] <= z[3] for z in zones)


def beam_linework(src, sheet, layers=BEAM_LAYERS):
    zones = detail_zones(src, sheet)
    segs, arcs = [], []
    for e in src.entities()[sheet]:
        if e["layer"] not in layers:
            continue
        if e["type"] == "LINE":
            if not (_in_zone(e["a"], zones) and _in_zone(e["b"], zones)):
                segs.append((e["handle"], tuple(e["a"]), tuple(e["b"])))
        elif e["type"] == "LWPOLYLINE":
            for i, sg in enumerate(e["segs"]):
                if sg[0] == "ARC":
                    arcs.append({"handle": f"{e['handle']}#{i}", "c": sg[1], "r": sg[2], "a0": sg[3], "a1": sg[4]})
                elif not (_in_zone(sg[0], zones) and _in_zone(sg[1], zones)):
                    segs.append((f"{e['handle']}#{i}", tuple(sg[0]), tuple(sg[1])))
        elif e["type"] in ("ARC", "CIRCLE"):
            if not _in_zone(e["c"], zones):
                arcs.append({"handle": e["handle"], "c": e["c"], "r": e["r"], "a0": e["a0"], "a1": e["a1"]})
    return segs, arcs, zones


def straight_bands(segs, *, wmin=BEAM_W_MM[0], wmax=BEAM_W_MM[1], merge_gap=40.0):
    """Pair parallel edge lines into beam bands (nearest partner), then merge collinear pieces of equal width.
    Returns [{band_id, dir, normal, offset, width_mm, t0, t1, centre_a, centre_b, edges}]"""
    from engine.source import arch_quantity_truth as AQ
    pieces = [p for p in AQ.pair_wall_faces(segs, min_mm=wmin, max_mm=wmax, angle_tol=0.01, min_overlap=60.0)
              if p["partner"] is not None]
    groups = defaultdict(list)
    for p in pieces:
        (x0, y0), (x1, y1) = p["centre_a"], p["centre_b"]
        L = math.hypot(x1 - x0, y1 - y0)
        if L < 1:
            continue
        ux, uy = (x1 - x0) / L, (y1 - y0) / L
        if ux < -1e-9 or (abs(ux) < 1e-9 and uy < 0):
            ux, uy, x0, y0, x1, y1 = -ux, -uy, x1, y1, x0, y0
        ang = round(math.degrees(math.atan2(uy, ux)) % 180.0, 1)
        nx, ny = -uy, ux
        off = x0 * nx + y0 * ny
        t0, t1 = sorted((x0 * ux + y0 * uy, x1 * ux + y1 * uy))
        groups[(ang, round(off / 20.0), round(p["width"] / 10.0))].append(
            {"t0": t0, "t1": t1, "u": (ux, uy), "n": (nx, ny), "off": off, "w": p["width"],
             "edges": {p["seg"], p["partner"]}})
    bands = []
    for key, ps in groups.items():
        ps.sort(key=lambda q: q["t0"])
        cur = None
        for q in ps:
            if cur and q["t0"] <= cur["t1"] + merge_gap:
                cur["t1"] = max(cur["t1"], q["t1"])
                cur["edges"] |= q["edges"]
            else:
                if cur:
                    bands.append(cur)
                cur = dict(q, edges=set(q["edges"]))
        if cur:
            bands.append(cur)
    out = []
    for b in bands:
        ux, uy = b["u"]
        nx, ny = b["n"]
        ca = (b["t0"] * ux + b["off"] * nx, b["t0"] * uy + b["off"] * ny)
        cb = (b["t1"] * ux + b["off"] * nx, b["t1"] * uy + b["off"] * ny)
        out.append({"dir": (round(ux, 6), round(uy, 6)), "normal": (round(nx, 6), round(ny, 6)),
                    "offset": round(b["off"], 1), "width_mm": round(b["w"], 1), "t0": round(b["t0"], 1),
                    "t1": round(b["t1"], 1), "length_mm": round(b["t1"] - b["t0"], 1),
                    "centre_a": (round(ca[0], 1), round(ca[1], 1)), "centre_b": (round(cb[0], 1), round(cb[1], 1)),
                    "edges": sorted(b["edges"]), "kind": "STRAIGHT"})
    # drop exact duplicates (two collinear groups differing only by rounding)
    out.sort(key=lambda b: (-b["length_mm"], b["offset"]))
    keep = []
    for b in out:
        dup = False
        for k in keep:
            if abs(b["dir"][0] * k["dir"][1] - b["dir"][1] * k["dir"][0]) < 0.01 and abs(b["offset"] - k["offset"]) < 30 \
                    and abs(b["width_mm"] - k["width_mm"]) < 30 and b["t0"] >= k["t0"] - 30 and b["t1"] <= k["t1"] + 30:
                dup = True
                break
        if not dup:
            keep.append(b)
    keep.sort(key=lambda b: (b["centre_a"][1], b["centre_a"][0], b["centre_b"][1]))
    for i, b in enumerate(keep):
        b["band_id"] = f"BD{i + 1:03d}"
    return keep


def arc_bands(arcs, *, wmin=BEAM_W_MM[0], wmax=BEAM_W_MM[1], ctol=30.0):
    """Concentric arcs whose radii differ by a beam width and whose angular ranges overlap -> curved bands."""
    out = []
    used = set()
    for i, a in enumerate(arcs):
        for j, b in enumerate(arcs):
            if j <= i or (i, j) in used:
                continue
            if math.dist(a["c"], b["c"]) > ctol:
                continue
            w = abs(a["r"] - b["r"])
            if not (wmin <= w <= wmax):
                continue
            # angular overlap (ccw ranges)
            def rng(x):
                s = x["a0"] % (2 * math.pi)
                e = x["a1"] % (2 * math.pi)
                sweep = (e - s) % (2 * math.pi) or 2 * math.pi
                return s, sweep
            sa, wa = rng(a)
            sb, wb = rng(b)
            d = (sb - sa) % (2 * math.pi)
            lo = max(0.0, d) if d < wa else None
            ov = min(wa, d + wb) - d if d < wa else min(wb, (sa - sb) % (2 * math.pi) + wa) - (sa - sb) % (2 * math.pi)
            if ov is None or ov <= math.radians(3):
                continue
            rm = (a["r"] + b["r"]) / 2.0
            out.append({"kind": "ARC", "centre": (round(a["c"][0], 1), round(a["c"][1], 1)), "r_mid_mm": round(rm, 1),
                        "width_mm": round(w, 1), "sweep_deg": round(math.degrees(ov), 2),
                        "length_mm": round(rm * ov, 1), "start_deg": round(math.degrees(max(sa, sb)) % 360, 2),
                        "edges": sorted([a["handle"], b["handle"]])})
            used.add((i, j))
    out.sort(key=lambda b: (b["centre"], b["r_mid_mm"], b["start_deg"]))
    for i, b in enumerate(out):
        b["band_id"] = f"BA{i + 1:03d}"
    return out


def _proj(b, p):
    """(along, across) of point p in band b's frame."""
    ux, uy = b["dir"]
    nx, ny = b["normal"]
    return p[0] * ux + p[1] * uy, p[0] * nx + p[1] * ny - b["offset"]


def beam_lines(bands, *, off_tol=40.0, w_tol=40.0, gap_max=1600.0):
    """Collinear bands of equal width separated by short gaps (a column or a crossing beam) form one beam LINE."""
    parent = list(range(len(bands)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
    for i, a in enumerate(bands):
        for j in range(i + 1, len(bands)):
            b = bands[j]
            if abs(a["dir"][0] * b["dir"][1] - a["dir"][1] * b["dir"][0]) > 0.01 or a["dir"][0] * b["dir"][0] + \
                    a["dir"][1] * b["dir"][1] < 0:
                continue
            if abs(a["offset"] - b["offset"]) > off_tol or abs(a["width_mm"] - b["width_mm"]) > w_tol:
                continue
            gap = max(b["t0"] - a["t1"], a["t0"] - b["t1"])
            if gap <= gap_max:
                parent[find(i)] = find(j)
    groups = defaultdict(list)
    for i, b in enumerate(bands):
        groups[find(i)].append(b)
    out = []
    for k, bs in groups.items():
        bs.sort(key=lambda b: b["t0"])
        out.append({"line_id": None, "bands": [b["band_id"] for b in bs], "dir": bs[0]["dir"],
                    "normal": bs[0]["normal"], "offset": round(sum(b["offset"] for b in bs) / len(bs), 1),
                    "width_mm": round(sum(b["width_mm"] for b in bs) / len(bs), 1), "t0": bs[0]["t0"],
                    "t1": max(b["t1"] for b in bs), "kind": "STRAIGHT"})
    out.sort(key=lambda l: (round(l["t0"]), l["offset"]))
    for i, l in enumerate(out):
        l["line_id"] = f"BL{i + 1:03d}"
        l["length_mm"] = round(l["t1"] - l["t0"], 1)
        for bid in l["bands"]:
            pass
    return out


def supports_on_line(line, columns, lines, footings=None):
    """Support intervals along a beam line: columns (outline intersects the line's strip), crossing beam lines
    (centrelines intersect inside both extents) and, for straps / ground beams, footings."""
    sup = []
    hw = line["width_mm"] / 2.0
    for c in columns:
        x0, y0, x1, y1 = c["bbox"]
        corners = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
        pr = [_proj(line, p) for p in corners]
        acr = [q[1] for q in pr]
        if min(acr) <= hw + 10 and max(acr) >= -hw - 10:
            al = [q[0] for q in pr]
            if max(al) >= line["t0"] - 60 and min(al) <= line["t1"] + 60:
                sup.append({"kind": "COLUMN", "ref": c["id"], "lo": min(al), "hi": max(al),
                            "centre": (min(al) + max(al)) / 2.0})
    for o in lines:
        if o is line:
            continue
        cr = line["dir"][0] * o["dir"][1] - line["dir"][1] * o["dir"][0]
        if abs(cr) < 0.2:
            continue
        # intersection of the two centrelines
        p0 = (line["t0"] * line["dir"][0] + line["offset"] * line["normal"][0],
              line["t0"] * line["dir"][1] + line["offset"] * line["normal"][1])
        q0 = (o["t0"] * o["dir"][0] + o["offset"] * o["normal"][0], o["t0"] * o["dir"][1] + o["offset"] * o["normal"][1])
        r, s_ = line["dir"], o["dir"]
        den = r[0] * s_[1] - r[1] * s_[0]
        t = ((q0[0] - p0[0]) * s_[1] - (q0[1] - p0[1]) * s_[0]) / den
        u = ((q0[0] - p0[0]) * r[1] - (q0[1] - p0[1]) * r[0]) / den
        L1 = line["t1"] - line["t0"]
        L2 = o["t1"] - o["t0"]
        tol1 = o["width_mm"] / 2 / abs(cr) + 80
        tol2 = line["width_mm"] / 2 / abs(cr) + 80
        if -tol1 <= t <= L1 + tol1 and -tol2 <= u <= L2 + tol2:
            s0 = line["t0"] + t
            half = o["width_mm"] / 2.0 / abs(cr)
            we_end = t <= tol1 or t >= L1 - tol1
            they_end = u <= tol2 or u >= L2 - tol2
            rel = ("CORNER" if we_end and they_end else "CARRIED_BY" if we_end else "CARRIES" if they_end
                   else "CROSSING")
            sup.append({"kind": "BEAM", "ref": o["line_id"], "lo": s0 - half, "hi": s0 + half, "centre": s0,
                        "relation": rel})
    for f in footings or []:
        pr = [_proj(line, p) for p in f["ring"]]
        acr = [q[1] for q in pr]
        if min(acr) <= hw and max(acr) >= -hw:
            al = [q[0] for q in pr]
            if max(al) >= line["t0"] - 60 and min(al) <= line["t1"] + 60:
                sup.append({"kind": "FOOTING", "ref": f["id"], "lo": min(al), "hi": max(al),
                            "centre": (min(al) + max(al)) / 2.0})
    sup.sort(key=lambda s: s["centre"])
    carried = [s_ for s_ in sup if s_.get("relation") == "CARRIES"]
    sup = [s_ for s_ in sup if s_.get("relation") != "CARRIES"]   # a beam framing INTO this line is not a support
    # merge overlapping support intervals (a column at a beam crossing)
    merged = []
    for s_ in sup:
        if merged and s_["lo"] <= merged[-1]["hi"] + 20:
            m = merged[-1]
            m["hi"] = max(m["hi"], s_["hi"])
            m["refs"].append({"kind": s_["kind"], "ref": s_["ref"], "relation": s_.get("relation")})
            if s_["kind"] == "COLUMN" and m["kind"] != "COLUMN":
                m["kind"], m["centre"] = "COLUMN", s_["centre"]
        else:
            merged.append(dict(s_, refs=[{"kind": s_["kind"], "ref": s_["ref"], "relation": s_.get("relation")}]))
    for m in merged:
        m["support_kind"] = ("COLUMN" if any(r["kind"] == "COLUMN" for r in m["refs"]) else
                             "FOOTING" if any(r["kind"] == "FOOTING" for r in m["refs"]) else
                             "BEAM_" + "/".join(sorted({r["relation"] for r in m["refs"] if r.get("relation")})))
    return merged, carried


def spans_of_line(line, sups):
    """Support-to-support spans along a line; a line end without support is a FREE_END span limit."""
    pts = []
    if not sups or sups[0]["lo"] > line["t0"] + 50:
        pts.append({"kind": "FREE_END", "lo": line["t0"], "hi": line["t0"], "centre": line["t0"], "refs": []})
    pts += sups
    if not sups or sups[-1]["hi"] < line["t1"] - 50:
        pts.append({"kind": "FREE_END", "lo": line["t1"], "hi": line["t1"], "centre": line["t1"], "refs": []})
    spans = []
    for a, b in zip(pts, pts[1:]):
        spans.append({"start": a, "end": b, "cc_mm": round(b["centre"] - a["centre"], 1),
                      "clear_mm": round(b["lo"] - a["hi"], 1), "s0": a["centre"], "s1": b["centre"]})
    return spans


def bind_beam_tags(tags, lines, arcs, *, max_d=950.0, angle_tol_deg=10.0):
    """Each beam tag -> one beam line (parallel, nearest centreline, along-position inside the line) or one arc band.
    Returns {tag_handle: {state, line_id|arc_id, distance_mm, along}}."""
    out = {}
    for t in tags:
        c = _text_centre(t)
        th = math.radians(t.get("rotation") or 0.0)
        td = (math.cos(th), math.sin(th))
        cands = []
        for l in lines:
            cr = abs(td[0] * l["dir"][1] - td[1] * l["dir"][0])
            if cr > math.sin(math.radians(angle_tol_deg)):
                continue
            s, d = _proj(l, c)
            if l["t0"] - 500 <= s <= l["t1"] + 500 and abs(d) <= max(max_d, l["width_mm"] / 2 + 700):
                cands.append((abs(d), l["line_id"], s, "LINE"))
        for a in arcs:
            dd = abs(math.dist(c, a["centre"]) - a["r_mid_mm"])
            if dd <= max_d:
                ang = math.degrees(math.atan2(c[1] - a["centre"][1], c[0] - a["centre"][0])) % 360
                rel = (ang - a["start_deg"]) % 360
                if rel <= a["sweep_deg"] + 25 or rel >= 360 - 25:
                    cands.append((dd, a["band_id"], None, "ARC"))
        cands.sort(key=lambda x: x[0])
        if not cands:
            out[t["handle"]] = {"state": "TAG_WITH_NO_MEMBER", "candidates": []}
        elif len(cands) > 1 and cands[1][0] - cands[0][0] < 100 and cands[1][1] != cands[0][1]:
            out[t["handle"]] = {"state": "AMBIGUOUS", "candidates": [c_[1] for c_ in cands[:3]],
                                "distances_mm": [round(c_[0], 1) for c_ in cands[:3]]}
        else:
            out[t["handle"]] = {"state": "BOUND", "member": cands[0][1], "member_kind": cands[0][3],
                                "distance_mm": round(cands[0][0], 1),
                                "along_mm": round(cands[0][2], 1) if cands[0][2] is not None else None}
    return out


def beam_family(tag):
    t = tag.upper()
    if t.startswith("CB"):
        return "CONTINUOUS_BEAM"
    if t.startswith(("S.B", "SB")):
        return "STRAP_BEAM"
    if t == "CA":
        return "CANTILEVER_BEAM"
    if t == "B.W":
        return "BEARING_WALL_BEAM"
    if t.startswith("GB"):
        return "GROUND_BEAM"
    return "SIMPLE_BEAM"


def beam_census_sheet(src, sheet, support_columns, *, min_member_mm=600.0):
    """Bands / lines / arcs on one plan sheet; every beam tag -> one occurrence; untagged lines -> MEMBER_WITH_NO_TAG."""
    segs, arcs, zones = beam_linework(src, sheet)
    bands = straight_bands(segs)
    abands = arc_bands(arcs)
    lines = beam_lines(bands)
    members = [l for l in lines if l["length_mm"] >= min_member_mm]
    fragments = [l for l in lines if l["length_mm"] < min_member_mm]
    tags = []
    for t in src.texts(sheet, {"S-TEXT"}):
        tt = t["text"].strip().upper().replace(" ", "")
        if BEAM_TAG.match(tt):
            tags.append(dict(t, text=tt))
    bind = bind_beam_tags(tags, members, abands)
    # an AMBIGUOUS tag whose candidate member already carries a bound tag of the same name binds there (same-type
    # evidence); otherwise it stays AMBIGUOUS
    for t in tags:
        b = bind[t["handle"]]
        if b["state"] != "AMBIGUOUS":
            continue
        same = {bind[o["handle"]]["member"] for o in tags if o is not t and o["text"] == t["text"]
                and bind[o["handle"]]["state"] == "BOUND"}
        hit = [c for c in b["candidates"] if c in same]
        if len(hit) == 1:
            kind = "ARC" if hit[0].startswith("BA") else "LINE"
            along = None
            if kind == "LINE":
                l = next(l for l in members if l["line_id"] == hit[0])
                along = round(_proj(l, _text_centre(t))[0], 1)
            bind[t["handle"]] = {"state": "BOUND", "member": hit[0], "member_kind": kind, "along_mm": along,
                                 "distance_mm": None, "resolved_by": "SAME_TYPE_TAG_ON_CANDIDATE_MEMBER",
                                 "candidates": b["candidates"]}
    sup = {}
    carried = {}
    for l in members:
        sup[l["line_id"]], carried[l["line_id"]] = supports_on_line(l, support_columns, members)
    lmap = {l["line_id"]: l for l in members}
    # tag evidence: two tags of different members inside one support-to-support span are separated at the framing
    # beam (CARRIES node) nearest to their midpoint - the drawing tags them as separate members
    tag_along = defaultdict(list)
    for t in tags:
        b = bind[t["handle"]]
        if b["state"] == "BOUND" and b["member_kind"] == "LINE":
            tag_along[b["member"]].append((b["along_mm"], t["text"]))
    split_nodes = defaultdict(list)
    for lid, tl in tag_along.items():
        tl.sort()
        base = spans_of_line(lmap[lid], sup[lid])
        for (a1, n1), (a2, n2) in zip(tl, tl[1:]):
            if n1 == n2 and n1.startswith("CB"):
                continue
            same = [sp for sp in base if sp["s0"] - 1 <= a1 <= sp["s1"] + 1 and sp["s0"] - 1 <= a2 <= sp["s1"] + 1]
            if not same:
                continue
            mid = (a1 + a2) / 2.0
            cands = [c for c in carried[lid] if a1 < c["centre"] < a2]
            if cands:
                c = min(cands, key=lambda c: abs(c["centre"] - mid))
                split_nodes[lid].append(dict(c, refs=[{"kind": "BEAM", "ref": c["ref"], "relation": "CARRIES"}],
                                             support_kind="BEAM_CARRIES_SPLIT_BY_TAG_EVIDENCE"))
    for lid, nodes in split_nodes.items():
        sup[lid] = sorted(sup[lid] + nodes, key=lambda s_: s_["centre"])
    spans = {l["line_id"]: spans_of_line(l, sup[l["line_id"]]) for l in members}
    amap = {a["band_id"]: a for a in abands}
    occ = []
    for t in sorted(tags, key=lambda t: (t["p"][1], t["p"][0])):
        b = bind[t["handle"]]
        fam = beam_family(t["text"])
        row = {"sheet": sheet, "tag": t["text"], "family": fam, "tag_handle": t["handle"],
               "tag_position_mm": t["p"], "tag_rotation_deg": t["rotation"], "binding": b["state"]}
        if b["state"] == "BOUND" and b["member_kind"] == "LINE":
            l = lmap[b["member"]]
            sp = [s_ for s_ in spans[l["line_id"]] if s_["s0"] - 1 <= b["along_mm"] <= s_["s1"] + 1]
            if not sp:   # tag beyond the drawn line: nearest span
                sp = sorted(spans[l["line_id"]], key=lambda s_: min(abs(s_["s0"] - b["along_mm"]),
                                                                      abs(s_["s1"] - b["along_mm"])))[:1]
            s_ = sp[0] if sp else None
            row.update(member=l["line_id"], member_kind="STRAIGHT", width_drawn_mm=l["width_mm"],
                       orientation_deg=round(math.degrees(math.atan2(l["dir"][1], l["dir"][0])) % 180, 2),
                       line_extent_mm=[l["t0"], l["t1"]], bands=l["bands"])
            if s_:
                row.update(span=s_, start_support=s_["start"], end_support=s_["end"],
                           support_centreline_length_m=round(s_["cc_mm"] / 1000, 3),
                           clear_length_m=round(s_["clear_mm"] / 1000, 3),
                           drawn_length_m=round(s_["cc_mm"] / 1000, 3))
        elif b["state"] == "BOUND":
            a = amap[b["member"]]
            row.update(member=a["band_id"], member_kind="ARC", width_drawn_mm=a["width_mm"],
                       arc={k: a[k] for k in ("centre", "r_mid_mm", "sweep_deg", "start_deg")},
                       drawn_length_m=round(a["length_mm"] / 1000, 3), support_centreline_length_m=None,
                       clear_length_m=None, start_support=None, end_support=None)
        occ.append(row)
    # two tags on one span of one line: keep both, flag
    seen = defaultdict(list)
    for r in occ:
        if r.get("span"):
            seen[(r["member"], round(r["span"]["s0"]), round(r["span"]["s1"]))].append(r)
    for k, rs in seen.items():
        names = {r["tag"] for r in rs}
        if len(rs) > 1 and not (len(names) == 1 and next(iter(names)).startswith("CB")):
            for r in rs:
                r["same_span_conflict"] = sorted(r2["tag"] for r2 in rs if r2 is not r)
    tagged_lines = {r["member"] for r in occ if r.get("member")}
    untagged = []
    for l in members:
        if l["line_id"] in tagged_lines:
            continue
        for s_ in spans[l["line_id"]]:
            untagged.append({"sheet": sheet, "member": l["line_id"], "width_drawn_mm": l["width_mm"],
                             "span": s_, "support_centreline_length_m": round(s_["cc_mm"] / 1000, 3),
                             "clear_length_m": round(s_["clear_mm"] / 1000, 3), "bands": l["bands"]})
    tagged_arcs = {r["member"] for r in occ if r.get("member_kind") == "ARC"}
    for a in abands:
        if a["band_id"] not in tagged_arcs:
            untagged.append({"sheet": sheet, "member": a["band_id"], "width_drawn_mm": a["width_mm"],
                             "arc": a, "support_centreline_length_m": None, "clear_length_m": None,
                             "drawn_length_m": round(a["length_mm"] / 1000, 3)})
    return {"sheet": sheet, "segments": len(segs), "arcs": len(arcs), "detail_zones": zones, "bands": bands,
            "arc_bands": abands, "lines": members, "fragments": fragments, "supports": sup, "carried": carried,
            "spans": spans, "tags": tags, "binding": bind, "occurrences": occ, "untagged": untagged}


# ===================================================================================================== slab panels
PANEL_EDGE_LAYERS = {"1", "S-BEAM", "S-COL.BON", "S-BOUN"}
SLAB_FLOOR = {"GFRS": "GF_ROOF_SLAB", "FFRS": "1F_ROOF_SLAB", "SFRS": "2F_ROOF_SLAB"}
PROJECT_SLAB_T = {"value": 160, "source": "ST7757.pdf p.8 note 18 + p.1 note: normal suspended slabs 16 cm unless "
                                          "otherwise stated"}


def min_rect(ring):
    """Minimum-area enclosing rectangle (edge directions of the convex hull): (short, long, angle_deg)."""
    pts = sorted(set((round(x, 3), round(y, 3)) for x, y in ring))
    if len(pts) < 3:
        return None

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lower, upper = [], []
    for p in pts:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)
    for p in reversed(pts):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)
    hull = lower[:-1] + upper[:-1]
    best = None
    for i in range(len(hull)):
        a, b = hull[i], hull[(i + 1) % len(hull)]
        L = math.dist(a, b)
        if L < 1e-6:
            continue
        ux, uy = (b[0] - a[0]) / L, (b[1] - a[1]) / L
        xs = [p[0] * ux + p[1] * uy for p in hull]
        ys = [-p[0] * uy + p[1] * ux for p in hull]
        w, h = max(xs) - min(xs), max(ys) - min(ys)
        if best is None or w * h < best[0]:
            best = (w * h, min(w, h), max(w, h), math.degrees(math.atan2(uy, ux)) % 180)
    return best[1:] if best else None


def slab_panels(src, sheet, beam_sheet, support_columns):
    """Faces of beam / column / boundary linework -> slab panels with class, dims, thickness note, edges."""
    zones = detail_zones(src, sheet)
    segs, arcs = [], []
    for e in src.entities()[sheet]:
        if e["layer"] == "S-OPENING" and e["type"] == "LINE" and (abs(e["a"][0] - e["b"][0]) < 1
                                                                  or abs(e["a"][1] - e["b"][1]) < 1):
            segs.append((*e["a"], *e["b"], f"{e['layer']}|{e['handle']}"))   # opening outline (X diagonals excluded)
            continue
        if e["layer"] not in PANEL_EDGE_LAYERS:
            continue
        if e["type"] == "LINE":
            if not (_in_zone(e["a"], zones) and _in_zone(e["b"], zones)):
                segs.append((*e["a"], *e["b"], f"{e['layer']}|{e['handle']}"))
        elif e["type"] == "LWPOLYLINE":
            for sg in e["segs"]:
                if sg[0] == "ARC":
                    arcs.append((sg[1][0], sg[1][1], sg[2], sg[3], sg[4], f"{e['layer']}|{e['handle']}"))
                elif not (_in_zone(sg[0], zones) and _in_zone(sg[1], zones)):
                    segs.append((*sg[0], *sg[1], f"{e['layer']}|{e['handle']}"))
        elif e["type"] in ("ARC", "CIRCLE"):
            if not _in_zone(e["c"], zones):
                arcs.append((e["c"][0], e["c"][1], e["r"], e["a0"], e["a1"], f"{e['layer']}|{e['handle']}"))
    T = PT.build(segs, eps=3.0, arcs=arcs)
    texts = src.texts(sheet)
    opening_lines = [e for e in src.entities()[sheet] if e["layer"] == "S-OPENING" and e["type"] == "LINE"]
    tread_lines = [e for e in src.entities()[sheet] if e["layer"] == "2" and e["type"] == "LINE"]
    void_texts = [t for t in texts if t["text"].upper() in ("VOID",)]
    dome_texts = [t for t in texts if t["text"].upper() == "SEE DETAIL"]
    tmarks = []
    tt = [t for t in texts if t["text"] == "T"]
    for t in tt:
        num = [n for n in texts if re.fullmatch(r"\d{2}", n["text"]) and abs(n["p"][0] - t["p"][0]) < 300
               and 0 < t["p"][1] - n["p"][1] < 500]
        if len(num) == 1:
            tmarks.append({"handle": t["handle"], "value_cm": int(num[0]["text"]), "p": t["p"],
                           "raw": f"T {num[0]['text']}", "num_handle": num[0]["handle"]})
    lines = beam_sheet["lines"]

    def in_face(pt, f):
        return SC.point_in_ring(pt, f["ring"]) and not any(SC.point_in_ring(pt, h) for h in f.get("holes") or [])

    def in_strip(pt):
        for l in lines:
            s_, d = _proj(l, pt)
            if l["t0"] - 20 <= s_ <= l["t1"] + 20 and abs(d) <= l["width_mm"] / 2 + 15:
                return l["line_id"]
        return None
    panels = []
    for f in T["faces"]:
        A = f["net_area_m2"]
        P = f["perimeter_m"]
        th = 2 * A / P if P else 0.0
        ring = f["ring"]
        ip = f["interior_point"]
        srcs = set(f.get("boundary_sources") or [])
        layers = {s_.split("|")[0] for s_ in srcs}
        if A < 0.6 or th < 0.45 or in_strip(ip):
            continue          # beam strips, column cores, slivers
        inside_col = any(c["bbox"][0] <= ip[0] <= c["bbox"][2] and c["bbox"][1] <= ip[1] <= c["bbox"][3]
                         for c in support_columns)
        if inside_col:
            continue
        x_lines = [o for o in opening_lines if in_face(((o["a"][0] + o["b"][0]) / 2, (o["a"][1] + o["b"][1]) / 2), f)]
        diag = [o for o in x_lines if abs(o["a"][0] - o["b"][0]) > 100 and abs(o["a"][1] - o["b"][1]) > 100]
        treads = [o for o in tread_lines if in_face(((o["a"][0] + o["b"][0]) / 2, (o["a"][1] + o["b"][1]) / 2), f)]
        vt = [t for t in void_texts if in_face(t["p"], f)]
        notes = [m for m in tmarks if in_face(m["p"], f)]
        if "S-BOUN" in layers and A > 40:
            cls = "OUTSIDE_BUILDING_OR_COURT"
        elif dome_texts and min(math.dist(t["p"], q) for t in dome_texts for q in ring) < 900 and A < 6:
            cls = "DOME_ZONE"
        elif len(diag) >= 2 or vt:
            cls = "OPEN_TO_BELOW"
        elif len(treads) >= 4:
            cls = "STAIR_FLIGHT_ZONE"
        else:
            cls = "SLAB_PANEL"
        mr = min_rect(ring)
        xs, ys = [p[0] for p in ring], [p[1] for p in ring]
        panels.append({"face_id": f["face_id"], "sheet": sheet, "class": cls, "ring": ring,
                       "holes": f.get("holes") or [],
                       "interior_point": ip, "area_m2": round(A, 3), "perimeter_m": round(P, 3),
                       "bbox_mm": [round(min(xs)), round(min(ys)), round(max(xs)), round(max(ys))],
                       "Lx_m": round(mr[0] / 1000, 3) if mr else None, "Ly_m": round(mr[1] / 1000, 3) if mr else None,
                       "orientation_deg": round(mr[2], 2) if mr else None,
                       "rectangularity": round(A / (mr[0] * mr[1] / 1e6), 3) if mr and mr[0] * mr[1] > 0 else None,
                       "vertices": len(ring), "thickness_notes": notes,
                       "void_evidence": {"x_lines": [o["handle"] for o in diag], "void_texts": [t["handle"] for t in vt]},
                       "stair_treads": len(treads), "boundary_sources": sorted(srcs)})
    panels.sort(key=lambda p: (-p["interior_point"][1], p["interior_point"][0]))
    floor = SLAB_FLOOR.get(sheet, sheet)
    for i, p in enumerate(panels):
        p["panel_id"] = f"SP-{floor}-{i + 1:02d}"
    # edges: support + continuity (probe outward from each ring edge)
    slab = [p for p in panels if p["class"] == "SLAB_PANEL"]
    for p in panels:
        ring = p["ring"]
        area_sign = sum(ring[i][0] * ring[(i + 1) % len(ring)][1] - ring[(i + 1) % len(ring)][0] * ring[i][1]
                        for i in range(len(ring)))
        edges = []
        for i in range(len(ring)):
            a, b = ring[i], ring[(i + 1) % len(ring)]
            L = math.dist(a, b)
            if L < 250:
                continue
            ux, uy = (b[0] - a[0]) / L, (b[1] - a[1]) / L
            nx, ny = (uy, -ux) if area_sign > 0 else (-uy, ux)          # outward normal
            m = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
            q = (m[0] + nx * 120, m[1] + ny * 120)
            sup = None
            for l in lines:
                s_, d = _proj(l, q)
                if l["t0"] - 50 <= s_ <= l["t1"] + 50 and abs(d) <= l["width_mm"] / 2 + 80:
                    if abs(l["dir"][0] * uy - l["dir"][1] * ux) < 0.2:
                        sup = ("BEAM", l["line_id"], l["width_mm"])
                        break
            if sup is None:
                for c in support_columns:
                    if c["bbox"][0] - 30 <= q[0] <= c["bbox"][2] + 30 and c["bbox"][1] - 30 <= q[1] <= c["bbox"][3] + 30:
                        sup = ("COLUMN", c["id"], c["short_mm"])
                        break
            reach = (sup[2] if sup else 0) + 350
            q2 = (m[0] + nx * reach, m[1] + ny * reach)
            hit = [o for o in panels if o is not p and SC.point_in_ring(q2, o["ring"])
                   and not any(SC.point_in_ring(q2, h) for h in o["holes"])]
            nb = [o["panel_id"] for o in hit]
            nb_cls = [o["class"] for o in hit]
            cont = ("CONTINUOUS" if nb and nb_cls[0] == "SLAB_PANEL" else
                    f"ADJACENT_{nb_cls[0]}" if nb else "DISCONTINUOUS")
            edges.append({"edge_index": i, "length_m": round(L / 1000, 3), "support": sup[0] if sup else "NONE_FOUND",
                          "support_ref": sup[1] if sup else None, "neighbour_panel": nb[0] if nb else None,
                          "continuity": cont})
        p["edges"] = edges
        p["support_summary"] = dict(Counter(e["support"] for e in edges))
        p["continuity_summary"] = dict(Counter(e["continuity"] for e in edges))
    return {"sheet": sheet, "floor": floor, "topology_counts": T["counts"], "panels": panels, "t_marks": tmarks,
            "detail_zones": zones}


# ----------------------------------------------------------------------------------------------- slab annotations
SLAB_TEXT_LAYERS = {"S-TEXT-SLAB", "S-TEXT-CORNER", "S-TITLE TEXT"}


def slab_annotations(src, sheet, panels, beam_lines_=None):
    """Every bar-like text on a slab sheet -> parsed annotation bound to one panel (or UNBOUND / AMBIGUOUS / a
    non-slab owner such as a planted-column label or a section detail)."""
    zones = detail_zones(src, sheet)
    texts = [t for t in src.texts(sheet) if t["layer"] in SLAB_TEXT_LAYERS]
    qual = [t for t in texts if t["text"].upper().replace(" ", "") == "(T&B)"]
    pc_labels = [t for t in texts if re.match(r"^P[./]C", t["text"].upper())]
    rein_lines = [e for e in src.entities()[sheet] if e["layer"] in ("S-REIN-SLAB", "S-REIN-CORNER")
                  and e["type"] in ("LINE", "LWPOLYLINE")]
    slab_like = [p for p in panels if p["class"] in ("SLAB_PANEL", "STAIR_FLIGHT_ZONE", "OPEN_TO_BELOW", "DOME_ZONE")]
    # the plan note box (top right of the sheet): 'CHECK ARCHITECTURAL DETAIL OF PARAPET...' + Arabic notes 1-2
    anchor = [t for t in src.texts(sheet) if "CHECK" in t["text"].upper() and "ARCHITECTURAL" in t["text"].upper()]
    notes_box = None
    if anchor:
        ax_, ay_ = anchor[0]["p"]
        notes_box = (ax_ - 2500, ay_ - 2600, ax_ + 9000, ay_ + 800)
    out = []
    for t in texts:
        parsed = SC.parse_slab_rebar(t["text"].replace("Ø", "%%c"))
        if parsed is None:
            continue
        rec = {"sheet": sheet, "text_handle": t["handle"], "raw": t["text"], "layer": t["layer"],
               "position_mm": t["p"], "rotation_deg": t["rotation"], "parsed": parsed}
        if _in_zone(t["p"], zones):
            rec.update(owner="SECTION_DETAIL", binding="NOT_A_PANEL_ANNOTATION", panel=None)
            out.append(rec)
            continue
        near_pc = [l for l in pc_labels if abs(l["p"][0] - t["p"][0]) < 700 and 0 < l["p"][1] - t["p"][1] < 700]
        if near_pc and parsed["count_mode"] == "ABSOLUTE_COUNT" and parsed["layer_qualifier"] is None:
            rec.update(owner="PLANTED_COLUMN_LABEL", binding="NOT_A_PANEL_ANNOTATION", panel=None,
                       owner_handle=near_pc[0]["handle"])
            out.append(rec)
            continue
        c = _text_centre(t)
        if notes_box and notes_box[0] <= t["p"][0] <= notes_box[2] and notes_box[1] <= t["p"][1] <= notes_box[3]:
            rec.update(owner="PLAN_NOTE", binding="NOT_A_PANEL_ANNOTATION", panel=None,
                       note="bar size quoted inside the plan note box (rule R-PLAN-02, top bars over beams)")
            out.append(rec)
            continue
        st, ids = SC.bind_to_panel(c, [{"id": p["panel_id"], "ring": p["ring"]} for p in slab_like], near=450)
        if parsed["layer_qualifier"] == "TOP" and not (st.startswith("BOUND") and len(ids) == 1) and beam_lines_:
            best = None
            for l in beam_lines_:
                s_, d = _proj(l, c)
                if l["t0"] - 300 <= s_ <= l["t1"] + 300:
                    if best is None or abs(d) < best[0]:
                        best = (abs(d), l["line_id"])
            if best and best[0] <= 1200:
                rec.update(owner="SLAB_SUPPORT_TOP_BAR", binding="BOUND_TO_BEAM_LINE", panel=None,
                           panel_candidates=ids, beam_line=best[1], distance_mm=round(best[0], 1),
                           direction="ACROSS_SUPPORT", layer="TOP", status="BOUND_TO_SUPPORT",
                           layer_note="explicit '/Top' suffix; drawn across / along a beam line between panels")
                out.append(rec)
                continue
        rot = (t["rotation"] or 0.0) % 180.0
        direction = "X" if rot < 20 or rot > 160 else ("Y" if 70 < rot < 110 else f"DIAGONAL_{rot:.0f}")
        q = [x for x in qual if math.dist(x["p"], t["p"]) < 900 and abs(((x["rotation"] or 0) - (t["rotation"] or 0))
                                                                        % 180) < 20]
        layer_q = parsed["layer_qualifier"] or ("T&B" if q else None)
        # the bar line drawn under the text (S-REIN-SLAB) - evidence of the graphic
        bar = None
        for e in rein_lines:
            pts = e.get("pts") or [e["a"], e["b"]]
            if any(math.dist(p_, c) < 1500 for p_ in pts):
                bar = e["handle"]
                break
        rec.update(owner="SLAB", binding=st, panel=ids[0] if len(ids) == 1 and st.startswith("BOUND") else None,
                   panel_candidates=ids, direction=direction, layer=layer_q or "NOT_STATED",
                   layer_note=("explicit '/Top' suffix" if parsed["layer_qualifier"] == "TOP" else
                               "(T&B) qualifier text beside the callout" if q else
                               "no TOP / BOTTOM word: legend 'Normal Slab Reinforcement' graphic - layer not "
                               "asserted"),
                   tb_text_handle=q[0]["handle"] if q else None, bar_graphic_handle=bar,
                   corner_reinforcement=t["layer"] == "S-TEXT-CORNER",
                   status="BOUND" if st.startswith("BOUND") and len(ids) == 1 else st)
        out.append(rec)
    # qualifiers that no bar text claimed
    claimed = {r.get("tb_text_handle") for r in out}
    orphans = [{"text_handle": x["handle"], "raw": x["text"], "position_mm": x["p"], "status": "QUALIFIER_UNCLAIMED"}
               for x in qual if x["handle"] not in claimed]
    return out, orphans


# ===================================================================================================== footings
def footing_outlines(src, sheet="FP"):
    """Footing outlines on the foundation plan: S-FOOTINGS closed / open polylines (incl. 'F' block inserts) and
    4-line rectangles (planar faces of the remaining S-FOOTINGS lines that are not strap-beam pairs)."""
    E = src.entities()[sheet]
    outs = []
    for e in E:
        if e["layer"] == "S-FOOTINGS" and e["type"] == "LWPOLYLINE":
            xs, ys = [p[0] for p in e["pts"]], [p[1] for p in e["pts"]]
            bb = (min(xs), min(ys), max(xs), max(ys))
            ring = [(bb[0], bb[1]), (bb[2], bb[1]), (bb[2], bb[3]), (bb[0], bb[3])] if not e["closed"] else e["pts"]
            outs.append({"id": f"FT:{e['handle']}", "handle": e["handle"], "via": e.get("via"), "ring": ring,
                         "bbox": tuple(round(v, 1) for v in bb), "closed_in_source": e["closed"],
                         "drawn_L_cm": round(max(bb[2] - bb[0], bb[3] - bb[1]) / 10, 1),
                         "drawn_W_cm": round(min(bb[2] - bb[0], bb[3] - bb[1]) / 10, 1),
                         "geometry": "POLYLINE" if not e.get("via") else "BLOCK_F_INSERT",
                         "note": None if e["closed"] else "open outline - gap where a strap beam enters; ring = bbox"})
    lines = [e for e in E if e["layer"] == "S-FOOTINGS" and e["type"] == "LINE"]
    segs = [(*e["a"], *e["b"], e["handle"]) for e in lines]
    T = PT.build(segs, eps=3.0)
    for f in T["faces"]:
        xs, ys = [p[0] for p in f["ring"]], [p[1] for p in f["ring"]]
        bb = (min(xs), min(ys), max(xs), max(ys))
        w, h = bb[2] - bb[0], bb[3] - bb[1]
        if len(f["ring"]) == 4 and abs(f["gross_area_m2"] - w * h / 1e6) < 0.01 and min(w, h) >= 500:
            outs.append({"id": f"FT:{f['face_id']}", "handle": "+".join(sorted(f["boundary_sources"])), "via": None,
                         "ring": f["ring"], "bbox": tuple(round(v, 1) for v in bb), "closed_in_source": True,
                         "drawn_L_cm": round(max(w, h) / 10, 1), "drawn_W_cm": round(min(w, h) / 10, 1),
                         "geometry": "FOUR_LINES", "note": None})
    outs.sort(key=lambda o: (o["bbox"][1], o["bbox"][0]))
    return outs


def strap_beams(src, sheet="FP"):
    """Strap beams: pairs of long parallel S-FOOTINGS lines (not footing edges) + the strap tags (S.B1 / sb2 / S.B3)."""
    E = src.entities()[sheet]
    lines = [(e["handle"], tuple(e["a"]), tuple(e["b"])) for e in E if e["layer"] == "S-FOOTINGS" and e["type"] == "LINE"
             and math.dist(e["a"], e["b"]) > 3000]
    bands = straight_bands(lines, wmin=300, wmax=1200)
    tags = []
    for t in src.texts(sheet):
        u = t["text"].upper().replace(" ", "")
        if re.fullmatch(r"S\.?B\d", u):
            tags.append(dict(t, text="SB" + u[-1]))
    out = []
    for b in bands:
        mid = ((b["centre_a"][0] + b["centre_b"][0]) / 2, (b["centre_a"][1] + b["centre_b"][1]) / 2)
        near = sorted(tags, key=lambda t: math.dist(_text_centre(t), mid))
        tag = near[0] if near and math.dist(_text_centre(near[0]), mid) < 1500 else None
        out.append({"band": b, "tag": tag["text"] if tag else None, "tag_handle": tag["handle"] if tag else None,
                    "tag_distance_mm": round(math.dist(_text_centre(tag), mid), 1) if tag else None,
                    "drawn_width_mm": b["width_mm"], "drawn_length_m": round(b["length_mm"] / 1000, 3)})
    used = {o["tag_handle"] for o in out}
    return out, [t for t in tags if t["handle"] not in used]


def footing_census(src, defs, column_chains_foundation):
    """column_chains_foundation: [{chain_id, type, centre}] (foundation members)."""
    outs = footing_outlines(src)
    tags = []
    for t in src.texts("FP"):
        u = t["text"].strip().upper()
        m = FOOT_TAG.match(u)
        if m:
            tags.append(dict(t, text=u, ftype=m.group("f"), ctype=m.group("c")))
    # tag -> outline: a tag inside exactly one outline binds there; else one-to-one by distance (Hungarian)
    from scipy.optimize import linear_sum_assignment

    def dist_to(o, p):
        x0, y0, x1, y1 = o["bbox"]
        dx = max(x0 - p[0], 0, p[0] - x1)
        dy = max(y0 - p[1], 0, p[1] - y1)
        return math.hypot(dx, dy)
    cost = [[dist_to(o, _text_centre(t)) for o in outs] for t in tags]
    ri, ci = linear_sum_assignment(cost)
    tag_of = {}
    tag_unbound = []
    for i, j in zip(ri, ci):
        if cost[i][j] <= 1500:
            tag_of[outs[j]["id"]] = tags[i]
        else:
            tag_unbound.append(tags[i])
    tag_unbound += [tags[i] for i in range(len(tags)) if i not in set(ri)]
    fdefs = {d["type"]: d for d in defs["definitions"] if d["element"] in ("FOOTING", "FOOTING_2_LAYER")}
    cols = [{"id": c["chain_id"], "centre": c["centre"], "needs_footing": True, "type": c["type"]}
            for c in column_chains_foundation]
    fts = [{"id": o["id"], "ring": o["ring"], "type": (tag_of.get(o["id"]) or {}).get("ftype")} for o in outs]
    col_f, f_col, mis = SC.footing_column_check(fts, cols)
    # overlapping outlines (two footings drawn over each other)
    for i, a in enumerate(outs):
        for b in outs[i + 1:]:
            ov = SC.bbox_overlap(a["bbox"], b["bbox"])
            if ov > 1000:
                mis.append({"kind": "FOOTING_OUTLINES_OVERLAP", "footings": [a["id"], b["id"]],
                            "overlap_m2": round(ov / 1e6, 3)})
    rows = []
    claimed = {t["handle"] for t in tag_of.values()}
    for o in outs:
        t = tag_of.get(o["id"])
        x0, y0, x1, y1 = o["bbox"]
        competing = [u for u in tags if u["handle"] not in claimed and x0 - 300 <= _text_centre(u)[0] <= x1 + 300
                     and y0 - 300 <= _text_centre(u)[1] <= y1 + 300 and (not t or u["ftype"] != t["ftype"])]
        if competing:
            for u in competing:
                claimed.add(u["handle"])
                tag_unbound = [v for v in tag_unbound if v["handle"] != u["handle"]]
        ftype = t["ftype"] if t else None
        if competing:
            ftype = None
        d = fdefs.get(ftype)
        sizes = None
        if d:
            L, W = d["fields"]["L_cm"], d["fields"]["W_cm"]
            sizes = {"schedule_L_cm": L, "schedule_W_cm": W, "drawn_L_cm": o["drawn_L_cm"], "drawn_W_cm": o["drawn_W_cm"],
                     "match": bool(abs(max(L, W) - o["drawn_L_cm"]) <= 5 and abs(min(L, W) - o["drawn_W_cm"]) <= 5)}
        supported = f_col.get(o["id"], [])
        tcol = t["ctype"] if t else None
        sup_types = sorted({c["type"] for c in cols if c["id"] in supported})
        state = "COUNTED_AND_DEFINED" if (d and sizes and sizes["match"]) else (
            "COUNTED_DEFINITION_PARTIAL" if d else "COUNTED_BLOCKED")
        issues = []
        if sizes and not sizes["match"]:
            issues.append("DRAWN_SIZE_DIFFERS_FROM_SCHEDULE")
        if not supported:
            issues.append("FOOTING_WITHOUT_COLUMN")
        if tcol and tcol not in sup_types:
            issues.append(f"TAG_COLUMN_{tcol}_NOT_AMONG_SUPPORTED_{sup_types}")
        if not t:
            issues.append("OUTLINE_WITHOUT_TAG")
        if competing:
            issues.append("SOURCE_CONFLICT_COMPETING_TAGS_ON_ONE_OUTLINE")
            state = "COUNTED_DEFINITION_PARTIAL"
        cand_types = sorted({t["ftype"]} | {u["ftype"] for u in competing}) if t else sorted({u["ftype"] for u in competing})
        rows.append({"footing_id": f"FTG-{ftype or ('CONFLICT_' + '_'.join(cand_types) if competing else 'UNTAGGED')}"
                                   f"-{o['bbox'][0]:.0f}-{o['bbox'][1]:.0f}", "type": ftype,
                     "candidate_types": cand_types if competing else None,
                     "competing_tags": [{"text": u["text"], "handle": u["handle"], "position_mm": u["p"]}
                                        for u in competing],
                     "outline": {k: o[k] for k in ("handle", "via", "geometry", "closed_in_source", "bbox", "note")},
                     "tag": ({"text": t["text"], "handle": t["handle"], "position_mm": t["p"]} if t else None),
                     "supported_columns": supported, "supported_column_types": sup_types,
                     "sizes": sizes, "definition_element": d["element"] if d else None,
                     "plan_source": {"drawing": DRAWING, "sheet": "FP", "pdf_page": 2},
                     "issues": issues, "terminal_state": state if not issues or state != "COUNTED_AND_DEFINED"
                     else "COUNTED_DEFINITION_PARTIAL"})
    tag_only = []
    for t in tag_unbound:
        tag_only.append({"footing_id": f"FTG-{t['ftype']}-TAG-{t['handle']}", "type": t["ftype"], "outline": None,
                         "tag": {"text": t["text"], "handle": t["handle"], "position_mm": t["p"]},
                         "issues": ["TAG_WITHOUT_SEPARATE_OUTLINE"], "terminal_state": "COUNTED_BLOCKED"})
    return {"rows": rows, "tag_only": tag_only, "mismatches": mis, "col_to_footing": col_f, "definitions": fdefs}


# ===================================================================================================== levels
def level_register(src):
    """Structural levels: printed level marks on ST7757 + the architectural section levels (P7757 SECTION A-A,
    transcribed in phase A2 as VE-AA-01..10). Floor-to-floor height, slab thickness, column clear height, main-bar
    length and tie-zone length are SEPARATE quantities; only the first two are established here."""
    marks = []
    for sh in ("GBP", "SFRS"):
        for t in src.texts(sh, {"LEVEL"}):
            marks.append({"sheet": sh, "handle": t["handle"], "raw": t["text"], "position_mm": t["p"]})
    ffl = {"GF": 1.00, "1F": 5.50, "2F": 9.70, "ROOF": 13.90}
    rows = [
        {"level": "FOUNDATION", "kind": "FOUNDATION_LEVEL", "value_m": None, "status": "BLOCKED",
         "source": "ST7757.pdf p.9 note 1: excavation >= 1.5 m below the existing plot level; plot level ±0.00 "
                   "(P7757 SECTION A-A VE-AA-01) -> founding level <= -1.50 (minimum, not a printed level)",
         "bound_m": {"max": -1.50}, "why": "no printed founding level; footing depths (H) from the schedule"},
        {"level": "GROUND_BEAMS / NATURAL GROUND", "kind": "LEVEL_MARK", "value_m": 0.00, "status": "PRINTED",
         "source": "ST7757 p.3 level marks ±0.00 / +0.15 / +0.30 (court, landings) + VE-AA-01..03",
         "printed_marks": sorted({m["raw"] for m in marks if m["sheet"] == "GBP"})},
        {"level": "GF", "kind": "FFL", "value_m": 1.00, "status": "PRINTED", "source": "ST7757 p.3 '+1.00' marks "
                                                                                     "inside the building + VE-AA-04"},
        {"level": "1F", "kind": "FFL", "value_m": 5.50, "status": "PRINTED_ARCH", "source": "P7757 SECTION A-A VE-AA-05"},
        {"level": "2F / 1F ROOF", "kind": "FFL / ROOF", "value_m": 9.70, "status": "PRINTED",
         "source": "ST7757 p.6 '+9.70' roof marks (" + ", ".join(m["handle"] for m in marks if m["sheet"] == "SFRS")
                   + ") + VE-AA-06"},
        {"level": "ROOF (2F roof)", "kind": "ROOF_LEVEL", "value_m": 13.90, "status": "PRINTED_ARCH",
         "source": "P7757 SECTION A-A VE-AA-07"},
    ]
    intervals = []
    for (lo, hi, storey, sheet) in (("GF", "1F", "GF", "GFRS"), ("1F", "2F", "1F", "FFRS"), ("2F", "ROOF", "2F", "SFRS")):
        h = round(ffl[hi] - ffl[lo], 3)
        intervals.append({
            "storey": storey, "lower_level": lo, "upper_level": hi, "lower_ffl_m": ffl[lo], "upper_ffl_m": ffl[hi],
            "floor_to_floor_m": h, "floor_to_floor_status": "PRINTED (P7757 VE-AA-09: 450 / 420 / 420 cm)",
            "closing_slab_sheet": sheet,
            "slab_thickness_default_mm": 160, "slab_thickness_authority": "PROJECT_DEFAULT (p.8 n.18 + p.1 note)",
            "slab_thickness_local_notes": "see SLAB_PANEL_REGISTER (T 16 / T 18 marks)",
            "column_clear_height_m": None, "column_clear_height_status": "BLOCKED - needs beam depths per column face "
                                                                      "(member geometry round)",
            "main_bar_length_m": None, "main_bar_length_status": "NOT_IN_THIS_ROUND (lap / starter rules)",
            "tie_zone_length_m": None, "tie_zone_status": "NOT_IN_THIS_ROUND",
            "structural_level_basis": "FFL interval; structural slab top = FFL - floor build-up (build-up not printed)",
            "status": "ESTABLISHED"})
    intervals.insert(0, {"storey": "FOUNDATION", "lower_level": "FOUNDATION", "upper_level": "GF",
                         "floor_to_floor_m": None, "status": "BLOCKED",
                         "why": "founding level not printed (>= 1.5 m below plot level); GF FFL +1.00",
                         "bound_m": {"min_height_m": 2.50}})
    return {"levels": rows, "intervals": intervals, "printed_marks": marks,
            "lift_tie_beam_rule_check": [{"storey": i["storey"], "floor_to_floor_m": i.get("floor_to_floor_m"),
                                          "required": (i.get("floor_to_floor_m") or 0) > 4.30,
                                          "rule": "P8-N19 (> 4.30 m -> tie beams at +3.00 m around the lift)"}
                                         for i in intervals if i.get("floor_to_floor_m")]}


# ===================================================================================================== ground beams
GB_CATEGORIES = [("GB_LT_2_5M", None, 2.5), ("GB_LT_5M", 2.5, 5.0), ("GB_GT_5M", 5.0, None)]


def gb_category(L):
    for k, lo, hi in GB_CATEGORIES:
        if (lo is None or L >= lo) and (hi is None or L < hi):
            return k
    return None


def ground_beam_rows(gb_sheet, gf_panels):
    """Every ground-beam span on the GB plan (no tags: typed by the p.13 rules). Length category is evaluated on the
    support-centreline AND the clear length; disagreement -> AMBIGUOUS_LENGTH_BASIS. Exterior = one side inside the
    GF roof-slab footprint and the other outside it (probe 600 mm beyond the beam face)."""
    inside = [p for p in gf_panels if p["class"] in ("SLAB_PANEL", "STAIR_FLIGHT_ZONE", "OPEN_TO_BELOW")]

    def in_fp(pt):
        return any(SC.point_in_ring(pt, p["ring"]) for p in inside)
    lmap = {l["line_id"]: l for l in gb_sheet["lines"]}
    rows = []
    for u in gb_sheet["untagged"]:
        if "arc" in u:
            a = u["arc"]
            rows.append({"gb_id": f"GB-{a['band_id']}", "member": a["band_id"], "kind": "CURVED",
                         "width_drawn_mm": a["width_mm"], "drawn_length_m": round(a["length_mm"] / 1000, 3),
                         "support_centreline_length_m": None, "clear_length_m": None,
                         "category_cc": None, "category_clear": None, "category_state": "BLOCKED_CURVED_SPAN",
                         "exterior": "UNRESOLVED", "terminal_state": "COUNTED_DEFINITION_PARTIAL"})
            continue
        l = lmap[u["member"]]
        sp = u["span"]
        cc, cl = u["support_centreline_length_m"], u["clear_length_m"]
        c1, c2 = gb_category(cc), gb_category(max(cl, 0.0))
        mid_s = (sp["s0"] + sp["s1"]) / 2
        ux, uy = l["dir"]
        nx, ny = l["normal"]
        base = (mid_s * ux + l["offset"] * nx, mid_s * uy + l["offset"] * ny)
        d = l["width_mm"] / 2 + 600
        sides = [in_fp((base[0] + nx * d, base[1] + ny * d)), in_fp((base[0] - nx * d, base[1] - ny * d))]
        ext = "EXTERIOR_CANDIDATE" if sides.count(True) == 1 else ("INTERIOR" if all(sides) else "OUTSIDE_FOOTPRINT")
        rows.append({"gb_id": f"GB-{u['member']}-{round(sp['s0'])}", "member": u["member"], "kind": "STRAIGHT",
                     "width_drawn_mm": u["width_drawn_mm"],
                     "orientation_deg": round(math.degrees(math.atan2(l["dir"][1], l["dir"][0])) % 180, 2),
                     "start_support": {k: sp["start"].get(k) for k in ("support_kind", "refs")} if sp["start"]["kind"] != "FREE_END" else {"support_kind": "FREE_END"},
                     "end_support": {k: sp["end"].get(k) for k in ("support_kind", "refs")} if sp["end"]["kind"] != "FREE_END" else {"support_kind": "FREE_END"},
                     "support_centreline_length_m": cc, "clear_length_m": cl, "drawn_length_m": cc,
                     "category_cc": c1, "category_clear": c2,
                     "category_state": "CATEGORY_BY_LENGTH" if c1 == c2 else "AMBIGUOUS_LENGTH_BASIS",
                     "exterior": ext, "terminal_state": "COUNTED_DEFINITION_PARTIAL"})
    return rows


# ===================================================================================================== continuous beams
def cb_register(beam_occ_by_sheet, beam_sheets, cdefs):
    """Dedicated CB census: every schedule CB row x every plan occurrence. A CB occurrence = the same CB tag on one
    straight line (collinear tags grouped); its plan spans = the tagged support-to-support spans plus, when the
    schedule has more spans, the adjacent untagged spans on the same line (recorded, never forced)."""
    rows = []
    seen_types = set()
    for sheet, occ in beam_occ_by_sheet.items():
        bs = beam_sheets[sheet]
        groups = defaultdict(list)
        for r in occ:
            if r["family"] != "CONTINUOUS_BEAM":
                continue
            key = (r["tag"], r.get("member") if r["binding"] == "BOUND" else f"UNBOUND:{r['tag_handle']}")
            groups[key].append(r)
        # merge groups of the same tag on parallel, collinear lines (offset within 150 mm)
        lmap = {l["line_id"]: l for l in bs["lines"]}
        keys = sorted(groups)
        merged = []
        used = set()
        for k in keys:
            if k in used:
                continue
            cluster = [k]
            used.add(k)
            if k[1] in lmap:
                for k2 in keys:
                    if k2 in used or k2[0] != k[0] or k2[1] not in lmap:
                        continue
                    a, b = lmap[k[1]], lmap[k2[1]]
                    if abs(a["dir"][0] * b["dir"][1] - a["dir"][1] * b["dir"][0]) < 0.02 and abs(a["offset"] - b["offset"]) < 150:
                        cluster.append(k2)
                        used.add(k2)
            merged.append(cluster)
        for cl in merged:
            tag = cl[0][0]
            seen_types.add(tag)
            rs = [r for k in cl for r in groups[k]]
            d = cdefs.get(tag)
            sched = d["fields"]["spans_m"] if d else None
            spans = []
            for r in sorted(rs, key=lambda r: (r.get("span") or {}).get("s0", 0)):
                if r.get("span"):
                    spans.append({"tag_handle": r["tag_handle"], "member": r["member"], "s0": r["span"]["s0"],
                                  "s1": r["span"]["s1"], "cc_m": r["support_centreline_length_m"],
                                  "clear_m": r["clear_length_m"], "start": r["start_support"].get("support_kind"),
                                  "end": r["end_support"].get("support_kind")})
            # unique spans (two tags in one span count once)
            uniq = []
            for s_ in spans:
                if not any(abs(s_["s0"] - u["s0"]) < 1 and abs(s_["s1"] - u["s1"]) < 1 and s_["member"] == u["member"]
                           for u in uniq):
                    uniq.append(s_)
            plan_cc = [u["cc_m"] for u in uniq]
            has_member = bool(uniq)
            st = SC.cb_match_state(sched, plan_cc, has_member=has_member, has_tag=True)
            ext = None
            if st == "SPAN_COUNT_CONFLICT" and sched and len(uniq) < len(sched) and uniq:
                # adjacent untagged spans on the same line(s)
                mems = {u["member"] for u in uniq}
                cands = []
                for m in mems:
                    for sp in bs["spans"].get(m, []):
                        if not any(abs(sp["s0"] - u["s0"]) < 1 and abs(sp["s1"] - u["s1"]) < 1 for u in uniq):
                            touching = any(abs(sp["s1"] - u["s0"]) < 1 or abs(sp["s0"] - u["s1"]) < 1 for u in uniq)
                            if touching:
                                cands.append({"member": m, "s0": sp["s0"], "s1": sp["s1"],
                                              "cc_m": round(sp["cc_mm"] / 1000, 3), "clear_m": round(sp["clear_mm"] / 1000, 3)})
                if len(uniq) + len(cands) == len(sched):
                    ext_spans = sorted(uniq + cands, key=lambda z: z["s0"])
                    st2 = SC.cb_match_state(sched, [z["cc_m"] for z in ext_spans])
                    ext = {"with_adjacent_untagged_spans": [c["cc_m"] for c in cands], "state_if_extended": st2,
                           "extended_spans_cc_m": [z["cc_m"] for z in ext_spans]}
            rows.append({"cb_id": f"CBO-{sheet}-{tag}-{cl[0][1]}", "type": tag, "sheet": sheet,
                         "floor": {"GFRS": "GF_ROOF", "FFRS": "1F_ROOF", "SFRS": "2F_ROOF"}.get(sheet, sheet),
                         "schedule_definition_exists": d is not None,
                         "schedule_row": d["insert_handle"] if d else None, "schedule_spans_m": sched,
                         "schedule_B_cm": d["fields"]["B_cm"] if d else None, "schedule_H_cm": d["fields"]["H_cm"] if d else None,
                         "tags": [{"handle": r["tag_handle"], "binding": r["binding"], "member": r.get("member")} for r in rs],
                         "plan_span_count": len(uniq), "plan_spans": uniq,
                         "drawn_width_mm": sorted({r.get("width_drawn_mm") for r in rs if r.get("width_drawn_mm")}),
                         "match_state": st, "extension_check": ext,
                         "terminal_state": "COUNTED_AND_DEFINED" if st == "MATCH_CONFIRMED" else
                         ("COUNTED_BLOCKED" if st in ("BLOCKED", "TAG_WITH_NO_MEMBER") else "COUNTED_DEFINITION_PARTIAL")})
    for t, d in sorted(cdefs.items()):
        if t not in seen_types:
            rows.append({"cb_id": f"CBO-NONE-{t}", "type": t, "sheet": None, "floor": None,
                         "schedule_definition_exists": True, "schedule_row": d["insert_handle"],
                         "schedule_spans_m": d["fields"]["spans_m"], "plan_span_count": 0, "plan_spans": [],
                         "match_state": "SCHEDULE_ROW_WITHOUT_PLAN_OCCURRENCE",
                         "terminal_state": "NOT_IN_SCOPE",
                         "note": "a schedule row never creates an occurrence (no CB tag on any plan)"})
    return rows


# ===================================================================================================== build
STOREY_SHEETS = {"GFRS": "GF_ROOF", "FFRS": "1F_ROOF", "SFRS": "2F_ROOF", "GBP": "GROUND_BEAMS"}


def _support_columns(C, sheet):
    excl = set()
    for ch in C["chains_raw"]:
        st = min(ch["members"], key=CHAIN_SHEETS.index)
        if st in ("GFRS", "FFRS"):
            excl.add(ch["members"][st])
        for v in ch.get("transition_outlines", {}).values():
            excl.add(v)
    return [o for o in C["outlines"][sheet] if o["id"] not in excl]


def build():
    src = Source()
    raw, defs = schedules()
    LV = level_register(src)
    C = column_census(src)
    CR = column_registers(src, C, defs, [{"storey": i["storey"], "floor_to_floor_m": i.get("floor_to_floor_m")}
                                         for i in LV["intervals"]])
    TT = tie_topology(src)
    # footings
    fc = []
    for ch in CR["chains"]:
        if "FOUNDATION" in ch["continues_through"]:
            m = ch["members_by_sheet"]
            sh = "FP" if "FP" in m else ("CAP" if "CAP" in m else "GBP")
            fc.append({"chain_id": ch["chain_id"], "centre": C["byid"][f"{sh}:{m[sh]}"]["centre"], "type": ch["column_type"]})
    FT = footing_census(src, defs, fc)
    straps, strap_unbound = strap_beams(src)
    # beams + slabs per sheet
    BS, SL, AN = {}, {}, {}
    for sh in ("GBP", "GFRS", "FFRS", "SFRS"):
        cols = _support_columns(C, sh)
        BS[sh] = beam_census_sheet(src, sh, cols)
        if sh != "GBP":
            SL[sh] = slab_panels(src, sh, BS[sh], cols)
            AN[sh] = slab_annotations(src, sh, SL[sh]["panels"], BS[sh]["lines"])
    GBP_PANELS = slab_panels(src, "GBP", BS["GBP"], _support_columns(C, "GBP"))
    GB = ground_beam_rows(BS["GBP"], SL["GFRS"]["panels"])
    cdefs = {d["type"]: d for d in defs["definitions"] if d["element"] == "CONTINUOUS_BEAM"}
    CB = cb_register({sh: BS[sh]["occurrences"] for sh in ("GFRS", "FFRS", "SFRS")}, BS, cdefs)
    return {"src": src, "raw": raw, "defs": defs, "levels": LV, "C": C, "CR": CR, "ties": TT, "footings": FT,
            "straps": straps, "strap_unbound": strap_unbound, "beams": BS, "slabs": SL, "annotations": AN,
            "gbp_panels": GBP_PANELS, "ground_beams": GB, "cb": CB}
