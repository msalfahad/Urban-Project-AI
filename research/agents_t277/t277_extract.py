"""T-277 extractor: private 'ST7757 dxf.dxf' (Drive "Alsenan chalet project", sha256 9f9d1179...38079) -> the census
input (labels, edge geometry, schedule rows) in a SCRATCH file outside the repository, and the coordinate-free census
result ALSENAN_T277_INPUT.json in this folder (handles, widths, distances; no coordinates, no drawing content).

    .work/venv/bin/python -I research/agents_t277/t277_extract.py <ST7757 dxf.dxf> <scratch dir> [--write]

Engine-independent: it reads only the drawing (no route G band, no T-110 register, no ledger). Labels: TEXT on S-TEXT
inside the three roof-slab windows (= research/agents_t139/slab_faces.py SHEETS) matching a beam mark; edges: every
LINE / LWPOLYLINE segment / ARC on the member-edge layers of the slab sheets (1, 2, 5, S-BEAM, S-BOUN), blocks
exploded; schedule: the attributes of the SBT (simple beams, 'W' / 'H' in cm under the header 'B-(Bredth)' /
'D-(Depth)') and C-BEAM2 / C-BEAM3 (continuous beams) inserts. Two stations per label: the label's own (its centre
on the beam axis direction) and +/- 0.40 m along it, so a width that changes beside the label is seen.
"""
from __future__ import annotations

import hashlib
import json
import math
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import beam_width_census as C  # noqa: E402

SHA = "9f9d1179a5d2a6635f9b412915a72184b7db1ff7729f4ab39a72dc3391738079"
SHEETS = {"GF": (40500, 74500, 35500, 51000), "1F": (11500, 36000, 35500, 51000), "2F": (-27000, -2000, 35500, 51000)}
EDGE_LAYERS = {"1", "2", "5", "S-BEAM", "S-BOUN"}
MARK = re.compile(r"\s*(C?B\d+|CA|B\.W)\s*")
CHAR_W = 0.75            # ROMANC glyph advance / height (label centre estimate along the text; station only)
STATIONS = (0.0, -0.40, 0.40)
RUN_STATIONS = (0.0, -0.5, 0.5)   # along the run from its register centre, as fractions of half its length
LABEL_RUN_M = 8.0                  # a run takes its direction from the nearest label of its own mark within 8 m


def _sheet(x, y):
    for k, (a, b, c, d) in SHEETS.items():
        if a <= x <= b and c <= y <= d:
            return k
    return None


def read(dxf):
    import ezdxf
    if hashlib.sha256(Path(dxf).read_bytes()).hexdigest() != SHA:
        raise SystemExit("not the T-277 input (sha256 differs)")
    doc = ezdxf.readfile(str(dxf))
    msp = doc.modelspace()
    lines = {k: [] for k in SHEETS}
    arcs = {k: [] for k in SHEETS}
    labels = []
    sched = []

    def add(e, h, layer):
        t = e.dxftype()
        if layer not in EDGE_LAYERS:
            return
        if t == "LINE":
            p, q = e.dxf.start, e.dxf.end
            sh = _sheet((p.x + q.x) / 2, (p.y + q.y) / 2)
            if sh:
                lines[sh].append((h, (p.x / 1000, p.y / 1000), (q.x / 1000, q.y / 1000), layer))
        elif t == "LWPOLYLINE":
            pts = [(p[0], p[1]) for p in e.get_points("xy")]
            if e.closed:
                pts.append(pts[0])
            for i, (p, q) in enumerate(zip(pts, pts[1:])):
                sh = _sheet((p[0] + q[0]) / 2, (p[1] + q[1]) / 2)
                if sh:
                    lines[sh].append(("%s.%d" % (h, i), (p[0] / 1000, p[1] / 1000), (q[0] / 1000, q[1] / 1000),
                                      layer))
        elif t in ("ARC", "CIRCLE"):
            c = e.dxf.center
            sh = _sheet(c.x, c.y)
            if sh:
                a0, a1 = (e.dxf.start_angle, e.dxf.end_angle) if t == "ARC" else (0.0, 359.999)
                arcs[sh].append((h, (c.x / 1000, c.y / 1000), e.dxf.radius / 1000, a0, a1, layer))

    for e in msp:
        t = e.dxftype()
        if t == "RTEXT":
            continue
        if t == "INSERT":
            if e.dxf.name in ("SBT", "C-BEAM2", "C-BEAM3"):
                a = {x.dxf.tag: x.dxf.text for x in e.attribs}
                mk = a.get("BEAM") or a.get("BEAM-NAME")
                sched.append((mk.strip(), a.get("W"), a.get("H"), "cm", e.dxf.handle, e.dxf.name))
                continue
            try:
                for v in e.virtual_entities():
                    lay = v.dxf.layer if v.dxf.layer != "0" else e.dxf.layer
                    add(v, e.dxf.handle, lay)
                    if v.dxftype() == "TEXT" and MARK.fullmatch(v.dxf.text) and v.dxf.layer == "S-TEXT":
                        labels.append(_label(v, e.dxf.handle, True))
            except Exception:
                pass
            continue
        if t == "TEXT" and e.dxf.layer == "S-TEXT" and MARK.fullmatch(e.dxf.text):
            labels.append(_label(e, e.dxf.handle, False))
            continue
        add(e, e.dxf.handle, e.dxf.layer)
    labels = [l for l in labels if l["sheet"]]
    cols = {k: [] for k in SHEETS}
    for e in msp.query('LWPOLYLINE[layer=="S-COL.BON"]'):
        pts = [(p[0], p[1]) for p in e.get_points("xy")]
        if len(pts) < 3:
            continue
        cx, cy = sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts)
        sh = _sheet(cx, cy)
        if sh and all(math.hypot(cx / 1000 - c[0], cy / 1000 - c[1]) > 0.05 for c in cols[sh]):
            cols[sh].append((cx / 1000, cy / 1000))
    read.columns = cols
    return lines, arcs, labels, sched


def _label(e, h, in_block):
    p = e.dxf.insert
    r = (e.dxf.get("rotation", 0.0) or 0.0) % 360.0
    hgt = e.dxf.get("height", 0.0) / 1000.0
    u = (math.cos(math.radians(r)), math.sin(math.radians(r)))
    n = (-u[1], u[0])
    txt = e.dxf.text.strip()
    w = len(txt) * hgt * CHAR_W
    cx = p.x / 1000 + u[0] * w / 2 + n[0] * hgt / 2
    cy = p.y / 1000 + u[1] * w / 2 + n[1] * hgt / 2
    return dict(h=h, mark=txt, rot=round(r, 4), c=(cx, cy), half_len=w / 2, half_h=hgt / 2, in_block=in_block,
                sheet=_sheet(p.x, p.y))


def census(lines, arcs, labels, sched):
    table = C.schedule_table([(m, w, hh, u, src) for m, w, hh, u, src, _n in sched])
    out = []
    for lab in sorted(labels, key=lambda l: (l["sheet"], l["h"])):
        sh = lab["sheet"]
        u = (math.cos(math.radians(lab["rot"])), math.sin(math.radians(lab["rot"])))
        st = []
        for s in STATIONS:
            c = (lab["c"][0] + u[0] * s, lab["c"][1] + u[1] * s)
            b = C.bind_label(c, lab["rot"], lines[sh], arcs[sh], hh=lab["half_h"])
            rd = b["readings"]
            st.append(dict(station_m=s, status=b["status"], placement=b.get("placement"), dist_m=b.get("dist_m"),
                           readings=[dict(width_m=r[2], edges=[r[3], r[4]], kind=r[5], interior=r[6],
                                          dist_m=round(C._dist(r, lab["half_h"]), 4)) for r in rd],
                           skew=[(s_[0], s_[1]) for s_ in b["skew"]]))
        out.append(dict(sheet=sh, label=lab["h"], mark=lab["mark"], rot=lab["rot"], in_block=lab["in_block"],
                        stations=st, schedule=table.get(lab["mark"])))
    return out, table


def _nearest_direction(c, lines, arcs):
    """direction (deg) of the drawn edge nearest to point c: a straight edge's own direction, an arc's tangent."""
    best = None
    for ln in lines:
        h, p, q = ln[0], ln[1], ln[2]
        dx, dy = q[0] - p[0], q[1] - p[1]
        L2 = dx * dx + dy * dy
        if L2 < 1e-12:
            continue
        t = max(0.0, min(1.0, ((c[0] - p[0]) * dx + (c[1] - p[1]) * dy) / L2))
        d = math.hypot(c[0] - p[0] - t * dx, c[1] - p[1] - t * dy)
        if best is None or d < best[0]:
            best = (d, math.degrees(math.atan2(dy, dx)) % 180.0, h)
    for ar in arcs:
        h, cc, R = ar[0], ar[1], ar[2]
        r = math.hypot(c[0] - cc[0], c[1] - cc[1])
        if r < 1e-9:
            continue
        d = abs(r - R)
        if best is None or d < best[0]:
            a = math.degrees(math.atan2(c[1] - cc[1], c[0] - cc[0]))
            best = (d, (a + 90.0) % 180.0, h)
    return best


def run_centres(lines, arcs, register_csv, labels=()):
    """Width at the CENTRE of every register span (T-110 x, y: a station only; the width is measured from the drawn
    edges here). Direction from the nearest drawn edge; the centre lies inside its own band, so hh = 0."""
    import csv
    out = []
    for r in csv.DictReader(open(register_csv, encoding="utf-8")):
        try:
            c = (float(r["x"]), float(r["y"]))
        except (TypeError, ValueError):
            out.append(dict(member=r["member_id"], component=r["component"], floor=r["floor"], mark=r["mark"],
                            status="NO_STATION", stations=[]))
            continue
        sh = r["floor"]
        same = sorted((math.hypot(l["c"][0] - c[0], l["c"][1] - c[1]), l["h"], l["rot"]) for l in labels
                      if l["sheet"] == sh and l["mark"] == r["mark"])
        if same and same[0][0] <= LABEL_RUN_M:
            nd = (same[0][0], same[0][2] % 180.0, "label " + same[0][1])
        else:
            nd = _nearest_direction(c, lines[sh], arcs[sh])
            nd = (nd[0], nd[1], "edge " + nd[2])
        u = (math.cos(math.radians(nd[1])), math.sin(math.radians(nd[1])))
        try:
            half = float(r["length_m"]) / 2.0
        except (TypeError, ValueError):
            half = 0.0
        st = []
        for f in RUN_STATIONS:
            s_ = round(f * half, 4)
            cc = (c[0] + u[0] * s_, c[1] + u[1] * s_)
            b = C.bind_label(cc, nd[1], lines[sh], arcs[sh], hh=0.0)
            st.append(dict(station_m=s_, status=b["status"], placement=b.get("placement"),
                           readings=[dict(width_m=x[2], edges=[x[3], x[4]], interior=x[6]) for x in b["readings"]]))
        basis = "register centre"
        if not any(x["status"] == "BOUND" for x in st) and same and same[0][0] <= LABEL_RUN_M:
            # the register centre is a hand-typed point off the band (T-110 manual rows): step along the run from
            # the nearest label of the run's own mark instead, within half the run length
            lab = [l for l in labels if l["h"] == same[0][1]][0]
            st = []
            for s_ in (0.0, -0.6, 0.6, -1.2, 1.2, -2.0, 2.0):
                if abs(s_) > half:
                    continue
                cc = (lab["c"][0] + u[0] * s_, lab["c"][1] + u[1] * s_)
                b = C.bind_label(cc, nd[1], lines[sh], arcs[sh], hh=0.0)
                st.append(dict(station_m=s_, status=b["status"], placement=b.get("placement"),
                               readings=[dict(width_m=x[2], edges=[x[3], x[4]], interior=x[6]) for x in b["readings"]]))
            basis = "label %s stations (register centre off the band)" % lab["h"]
        out.append(dict(member=r["member_id"], component=r["component"], floor=sh, mark=r["mark"],
                        dir_edge=nd[2], station_basis=basis, stations=st))
    return out


def main(argv):
    if len(argv) < 2:
        raise SystemExit(__doc__)
    dxf, scratch = Path(argv[0]), Path(argv[1])
    lines, arcs, labels, sched = read(dxf)
    scratch.mkdir(parents=True, exist_ok=True)
    (scratch / "t277_geometry.json").write_text(json.dumps(dict(lines=lines, arcs=arcs, labels=labels,
                                                                columns=read.columns)),
                                                encoding="utf-8")
    rows, table = census(lines, arcs, labels, sched)
    runs = run_centres(lines, arcs, HERE.parent / "agents_t110" / "BEAM_MEMBER_REGISTER.csv", labels)
    data = dict(schema="T277_CENSUS_INPUT_V1", source_dxf_sha256=SHA, labels=rows, run_centres=runs,
                schedule=[dict(mark=m, W=w, H=hh, unit=u, handle=src, block=nm) for m, w, hh, u, src, nm in sched],
                edge_counts={k: dict(lines=len(lines[k]), arcs=len(arcs[k])) for k in SHEETS})
    print("labels", {k: sum(1 for r in rows if r["sheet"] == k) for k in SHEETS}, "schedule rows", len(sched))
    if "--write" in argv:
        (HERE / "ALSENAN_T277_INPUT.json").write_text(json.dumps(data, indent=0), encoding="utf-8")
        print("written", HERE / "ALSENAN_T277_INPUT.json")
    else:
        (scratch / "ALSENAN_T277_INPUT.json").write_text(json.dumps(data, indent=0), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
