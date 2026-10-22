"""Hand-measurement aid (research only): room regions of one architectural plan from the DXF.
Barriers: layer 1 walls, S-COL.BON columns, W windows; each door block closed on BOTH wall faces
(closed-leaf line from the hinge, and its copy moved across the jamb). Regions = plan box minus barriers.
Usage: python -I rooms.py <dxf> x0 x1 y0 y1 <out.json> [<png>]"""
import ezdxf,sys,json,math
from ezdxf import path as zpath
from shapely.geometry import LineString,Polygon,Point,box,MultiLineString
from shapely.ops import unary_union,polygonize
d=ezdxf.readfile(sys.argv[1]);m=d.modelspace()
x0,x1,y0,y1=[float(v) for v in sys.argv[2:6]]
B=box(x0,y0,x1,y1)
def pts(e):
    try: p=zpath.make_path(e)
    except Exception: return []
    return [(q.x/1000,q.y/1000) for q in p.flattening(5)]
segs=[];wall1=[]
for e in m:
    if e.dxftype() in('RTEXT',): continue
    L=e.dxf.layer
    if L in('1','S-COL.BON','W') and e.dxftype() in('LINE','LWPOLYLINE','ARC','POLYLINE','CIRCLE'):
        v=pts(e)
        if len(v)>=2 and any(B.contains(Point(q)) for q in v):
            segs.append(LineString(v))
            if L=='1' and e.dxftype()=='LINE': wall1.append(LineString(v))
doors=[]; closures=[]
for e in m.query('INSERT'):
    x,y=e.dxf.insert.x/1000,e.dxf.insert.y/1000
    if not B.contains(Point(x,y)): continue
    ves=list(e.virtual_entities())
    arcs=[v for v in ves if v.dxftype()=='ARC' and v.dxf.radius>400]
    if not arcs: continue
    lines=[LineString(pts(v)) for v in ves if v.dxftype() in('LINE','LWPOLYLINE') and len(pts(v))>=2]
    for a in arcs:
        c=a.ocs().to_wcs(a.dxf.center); c=(c.x/1000,c.y/1000); r=a.dxf.radius/1000
        v=pts(a); ends=[v[0],v[-1]]
        # the open leaf touches one arc end; the closed position is the other end
        def touched(p): return min((ln.distance(Point(p)) for ln in lines),default=9)
        tq=sorted(ends,key=touched)
        closed=tq[1] if touched(tq[0])<0.02 else None
        if closed is None:
            # leaf not drawn: take the end lying on a wall line
            closed=min(ends,key=lambda p:min(w.distance(Point(p)) for w in wall1))
        ux,uy=(closed[0]-c[0])/r,(closed[1]-c[1])/r
        p0=(c[0]-0.12*ux,c[1]-0.12*uy); p1=(closed[0]+0.12*ux,closed[1]+0.12*uy)
        cl=LineString([p0,p1])
        # jamb: a wall line near the hinge perpendicular to the leaf
        best=None
        for w in wall1:
            if w.distance(Point(c))>0.2 or w.length<0.07 or w.length>0.5: continue
            (ax,ay),(bx,by)=w.coords[0],w.coords[-1]; dx,dy=(bx-ax)/w.length,(by-ay)/w.length
            if abs(dx*ux+dy*uy)>0.1: continue
            if best is None or w.distance(Point(c))<best[0]: best=(w.distance(Point(c)),w,dx,dy)
        closures.append(cl)
        rec={'name':e.dxf.name,'x':round(x,3),'y':round(y,3),'r':round(r,3),'jamb':None}
        if best:
            _,w,dx,dy=best
            # move the closure to the other face: project the far jamb end
            a0,a1=w.coords[0],w.coords[-1]
            # which end is near the closure line
            n0=cl.distance(Point(a0)); n1=cl.distance(Point(a1))
            far=a1 if n0<n1 else a0
            off=cl.distance(Point(far))
            sgn=1 if ((far[0]-c[0])*(-uy)+(far[1]-c[1])*ux)>0 else -1
            nx,ny=-uy*sgn*off,ux*sgn*off
            closures.append(LineString([(p0[0]+nx,p0[1]+ny),(p1[0]+nx,p1[1]+ny)]))
            rec['jamb']=round(off,3)
        doors.append(rec)
# collinear face-line gaps (openings) closed on both faces: p-q with p,q ends of two collinear layer-1 lines
GAPMAX=float(__import__('os').environ.get('GAPMAX','2.25'))
import itertools
W1=[(w.coords[0],w.coords[-1]) for w in wall1 if w.length>0.05]
gaps=[]
for i,(a,b) in enumerate(W1):
    L=math.dist(a,b); u=((b[0]-a[0])/L,(b[1]-a[1])/L)
    for end,dirn in ((b,u),(a,(-u[0],-u[1]))):
        best=None
        for j,(c,e2) in enumerate(W1):
            if j==i: continue
            L2=math.dist(c,e2); v=((e2[0]-c[0])/L2,(e2[1]-c[1])/L2)
            if abs(u[0]*v[1]-u[1]*v[0])>0.017: continue
            for q,far in ((c,e2),(e2,c)):
                dx,dy=q[0]-end[0],q[1]-end[1]
                t=dx*dirn[0]+dy*dirn[1]; off=abs(dx*dirn[1]-dy*dirn[0])
                if off>0.006 or not (0.25<t<GAPMAX): continue
                # the other line must continue away from the gap
                if ((far[0]-q[0])*dirn[0]+(far[1]-q[1])*dirn[1])<0: continue
                if best is None or t<best[0]: best=(t,q)
        if best: gaps.append(LineString([end,best[1]]))
closures+=gaps
print('gap closures',len(gaps))
BUF=float(__import__("os").environ.get("BUF","0.015"))
bar=unary_union([g.buffer(BUF,cap_style=2,join_style=2) for g in segs+closures])
free=B.buffer(-0.05).difference(bar); print("segs",len(segs),"bar",round(bar.area,2),bar.geom_type,"free",free.geom_type,len(getattr(free,"geoms",[1])))
faces=list(free.geoms) if hasattr(free,'geoms') else [free]
# grow back by BUF so faces sit on the drawn lines (mitre keeps corners)
faces=[f.buffer(BUF,join_style=2) for f in faces]
# regions = faces not inside barrier material: drop faces that are wall/column/window strips (thin) and keep by label
labels=[]
for e in m.query('INSERT[layer=="4"]'):
    x,y=e.dxf.insert.x/1000,e.dxf.insert.y/1000
    if B.contains(Point(x,y)): labels.append((e.dxf.name,x,y))
out=[]
for i,f in enumerate(faces):
    if f.area<0.3: continue
    mrr=f.minimum_rotated_rectangle; xs=mrr.exterior.coords
    e1=math.dist(xs[0],xs[1]); e2=math.dist(xs[1],xs[2])
    if min(e1,e2)<0.35: continue
    labs=[n for n,x,y in labels if f.contains(Point(x,y))]
    out.append({'i':i,'area':round(f.area,4),'perim':round(f.exterior.length,3),'holes':len(f.interiors),'labels':labs,
                'rep':[round(f.representative_point().x,3),round(f.representative_point().y,3)],
                'bounds':[round(v,3) for v in f.bounds],'wkt':f.wkt})
json.dump({'doors':doors,'faces':out},open(sys.argv[6],'w'),indent=0)
for o in sorted(out,key=lambda o:o['rep']): print(o['i'],o['area'],o['perim'],o['labels'],o['rep'])
print('doors',len(doors),'no jamb',[dd['name'] for dd in doors if dd['jamb'] is None])
if len(sys.argv)>7:
    import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
    fig,ax=plt.subplots(figsize=(24,24*(y1-y0)/(x1-x0)))
    for s in segs: ax.plot(*s.xy,'k',lw=0.4)
    for s in closures: ax.plot(*s.xy,'r',lw=0.8)
    for o in out:
        from shapely import wkt
        g=wkt.loads(o['wkt']); ax.fill(*g.exterior.xy,alpha=0.25)
        ax.text(o['rep'][0],o['rep'][1],f"{o['i']}:{o['area']:.2f}\n{','.join(o['labels'])}",fontsize=7)
    ax.set_aspect('equal'); plt.savefig(sys.argv[7],dpi=100,bbox_inches='tight')
