"""T-145 helper: for each sunken slab panel, walk its outline in 0.05 m steps and classify what lies 0.03 m outside
each step (the face class from the T-139 ledger: beam band / column, another slab face, sunken or not, edge, void)."""
import csv,json,sys
from shapely import wkt
from shapely.geometry import Point
faces=json.load(open(sys.argv[1])); P={r['id']:r for r in csv.DictReader(open(sys.argv[2]))}
SUNK=['GF-015','GF-016','GF-081','GF-128','GF-141','1F-018']
sunk=set(SUNK)
for sid in SUNK:
    fl=sid[:2]; F={f['id']:wkt.loads(f['wkt']) for f in faces[fl]}
    poly=F[sid]; ring=poly.exterior; L=ring.length; n=int(L/0.01)
    tally={}
    for i in range(n):
        a=ring.interpolate(i*L/n); b=ring.interpolate((i+1)*L/n)
        m=Point((a.x+b.x)/2,(a.y+b.y)/2)
        dx,dy=b.x-a.x,b.y-a.y; d=(dx*dx+dy*dy)**.5 or 1
        best=None
        for s in (1,-1):
            q=Point(m.x+s*dy/d*0.03,m.y-s*dx/d*0.03)
            if poly.contains(q): continue
            hit=[k for k,g in F.items() if k!=sid and g.contains(q)]
            best=hit[0] if hit else 'OUTSIDE'
        cls='OUTSIDE' if best in (None,'OUTSIDE') else ('SUNKEN_SLAB' if best in sunk else P[best]['cls'])
        key=(cls, best if cls in('SLAB','SUNKEN_SLAB') else '')
        tally[key]=tally.get(key,0)+L/n
    print(sid, f"area {poly.area:.4f} perimeter {L:.3f}", {f"{k[0]} {k[1]}".strip():round(v,3) for k,v in sorted(tally.items(),key=lambda x:-x[1])})
