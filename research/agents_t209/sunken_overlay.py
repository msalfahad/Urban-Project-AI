"""T-209 hand-measurement aid (research only, NOT engine code): which Alsenan rooms sit UNDER a sunken wet-slab panel.

T-206 (MERGED d5df7d1f) found 6 "Sunken slab." hatches on the structural roof-slab plans (DXF HATCH ANSI31 scale 2000 on
layer S-HAT.BAT: 275, 276, 280, 287, 298 on the GF roof slab = 1F floor; 5BF on the 1F roof slab = 2F floor) with the drop
printed nowhere, and flagged every ceiling / wall height of a room below one as WRONG_REFERENCE (datum HELD). This script
measures, per room, the share of its plan area under such a panel, on the slab plan ABOVE the room:
  room region  = the T-128 r3 walk region (T-147 rooms.py regions, checker-verified, reused by citation: walk_r2.py seeds)
  arch -> ST   = the T-147 align.py column translation per floor (all columns matched, spread 0.00 m)
  panel        = the hatch boundary paths of the six handles above
Writes areas and shares only (no coordinates) to <out.json>.
Usage: python -I sunken_overlay.py <t147 rooms.py> <arch.dxf> <st.dxf> <align.json> <out.json>"""
import sys, json, io, contextlib
import ezdxf
from shapely.geometry import Polygon
from shapely.ops import unary_union

SUNKEN = {'GF': ('275', '276', '280', '287', '298'), '1F': ('5BF',)}   # slab plan above the room's floor
ROOM_IDS = ['GF-02', 'GF-03', 'GF-05', 'GF-06', 'GF-07', 'GF-10', 'GF-11', 'GF-12', 'GF-13', 'GF-14', 'GF-16',
            'GF-01', 'GF-04', 'GF-08', 'GF-15', 'ST-GF',
            '1F-02', '1F-03', '1F-07', '1F-08', '1F-09', '1F-12', '1F-01', '1F-04', '1F-10', '1F-11', '1F-13', 'ST-1F']


def hatch_polys(st, handles):
    out = []
    for h in handles:
        e = st.entitydb[h]
        for p in e.paths:
            if hasattr(p, 'vertices'):
                v = [(q[0] / 1000, q[1] / 1000) for q in p.vertices]
            else:
                v = []
                for ed in p.edges:
                    v.append((ed.start[0] / 1000, ed.start[1] / 1000))
            if len(v) >= 3:
                out.append(Polygon(v).buffer(0))
    return unary_union(out)


def main(rooms_py, arch, stp, align_json, out):
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'agents_t128', 'scripts'))
    import walk_r2 as W
    W.DXF, W.SRC = arch, open(rooms_py).read()
    # the room list is built inside walk_r2's __main__; re-run it with output captured, keeping only R
    src = open(W.__file__).read()
    head, tail = src.split("if __name__ == '__main__':", 1)
    body = tail.split("    R = [(rid, F, unary_union", 1)[0]
    body = '\n'.join(l[4:] if l.startswith('    ') else l for l in body.splitlines())
    ns = dict(W.__dict__)
    ns['sys'] = sys
    sys_argv = sys.argv
    sys.argv = ['walk_r2.py', rooms_py, arch, '/dev/null']
    with contextlib.redirect_stdout(io.StringIO()):
        exec(compile(body.replace("ROOMS_PY, DXF, OUT = sys.argv[1:4]\nSRC = open(ROOMS_PY).read()\n", ''), 'walk_r2', 'exec'), ns)
    sys.argv = sys_argv
    R = {rid: poly for rid, F, poly in ns['R']}
    T = json.load(open(align_json))
    st = ezdxf.readfile(stp)
    res = {}
    for fl, handles in SUNKEN.items():
        pan = hatch_polys(st, handles)
        tx, ty = T[fl]
        from shapely import affinity
        for rid in ROOM_IDS:
            if not (rid.startswith(fl) or rid == 'ST-' + fl):
                continue
            if rid not in R:
                continue
            poly = affinity.translate(R[rid], tx, ty)
            under = poly.intersection(pan).area
            res[rid] = {'room_m2': round(poly.area, 4), 'under_sunken_m2': round(under, 4),
                        'share': round(under / poly.area, 4) if poly.area else None,
                        'slab_plan_above': f'{fl} roof slab', 'panels': list(handles)}
    # cross-check of the registration: a wet room's OWN floor panel. The upper arch plan is moved onto the lower one by
    # the column translation between the two arch plans (STACK, measured: 15 of 20 1F columns and 6 of 9 2F columns
    # vote 44.85 m, the rest 44.83 or no partner), then onto the slab plan of the lower floor's roof.
    STACK = 44.85
    for fl_up, fl_slab in (('1F', 'GF'), ('2F', '1F')):
        pan = hatch_polys(st, SUNKEN[fl_slab])
        tx, ty = T[fl_slab]
        for rid in ROOM_IDS + ['2F-02', '2F-01', '2F-03']:
            if not rid.startswith(fl_up) or rid not in R:
                continue
            poly = affinity.translate(R[rid], STACK + tx, ty)
            under = poly.intersection(pan).area
            res.setdefault('own_floor', {})[rid] = {
                'room_m2': round(poly.area, 4), 'on_sunken_m2': round(under, 4),
                'share': round(under / poly.area, 4) if poly.area else None, 'slab_plan': f'{fl_slab} roof slab'}
    json.dump(res, open(out, 'w'), indent=1)
    # which room of the storey above stands over each wet room (plan overlap, m2), same stacking translation
    for fl_lo, fl_up in (('GF', '1F'), ('1F', '2F')):
        ups = {u: affinity.translate(p, STACK, 0) for u, p in R.items() if u.startswith(fl_up)}
        for rid in ROOM_IDS:
            if not rid.startswith(fl_lo) or rid not in R:
                continue
            ov = {u: round(R[rid].intersection(p).area, 4) for u, p in ups.items()}
            res.setdefault('room_above', {})[rid] = {u: a for u, a in sorted(ov.items()) if a > 0.01}
    json.dump(res, open(out, 'w'), indent=1)
    for k, v in res.get('own_floor', {}).items():
        print('own floor', k, v['room_m2'], v['on_sunken_m2'], v['share'])
    for k, v in res.get('room_above', {}).items():
        print('above', k, v)
    for k, v in res.items():
        if 'room_m2' in v:
            print(k, v['room_m2'], v['under_sunken_m2'], v['share'])


if __name__ == '__main__':
    main(*sys.argv[1:6])
