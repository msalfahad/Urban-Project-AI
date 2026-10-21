import sys,json,collections,math
import ezdxf
doc=ezdxf.readfile(sys.argv[1]); msp=doc.modelspace()
segs=[];arcs=[]
def add(e,layer):
    t=e.dxftype()
    if t=='LINE':
        a,b=e.dxf.start,e.dxf.end; segs.append((layer,a.x/1000,a.y/1000,b.x/1000,b.y/1000))
    elif t in('LWPOLYLINE','POLYLINE'):
        pts=[(p[0],p[1]) for p in (e.get_points('xy') if t=='LWPOLYLINE' else [(v.dxf.location.x,v.dxf.location.y) for v in e.vertices])]
        closed=e.closed if t=='LWPOLYLINE' else e.is_closed
        if closed: pts=pts+[pts[0]]
        for p,q in zip(pts,pts[1:]): segs.append((layer,p[0]/1000,p[1]/1000,q[0]/1000,q[1]/1000))
    elif t in('ARC','CIRCLE'):
        c=e.dxf.center; r=e.dxf.radius
        s,en=(e.dxf.start_angle,e.dxf.end_angle) if t=='ARC' else (0,360)
        arcs.append((layer,c.x/1000,c.y/1000,r/1000,s,en))
def walk(ents,d=0):
    for e in ents:
        if e.dxftype()=='INSERT' and d<8:
            try: walk(list(e.virtual_entities()),d+1)
            except Exception: pass
        else:
            try: add(e,e.dxf.layer)
            except Exception: pass
walk(msp)
json.dump({'segs':segs,'arcs':arcs},open(sys.argv[2],'w'))
c=collections.Counter(s[0] for s in segs if s[2]>-30 and s[2]<120 and 30<s[2+1]<60)
print(len(segs),len(arcs)); print(c.most_common(25))
