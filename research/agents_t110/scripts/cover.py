import json,math
from shapely.geometry import Polygon,LineString,Point
from shapely.ops import unary_union
G=json.load(open('data/geom.json'));B=json.load(open('data/bands.json'))
FR={'2F':(-25,0,34,52),'1F':(12,36,34,52),'GF':(41,76,34,52)}
for st,(x0,x1,y0,y1) in FR.items():
    polys=unary_union([Polygon(v['pts']).buffer(0.03) for k,v in B.items() if k.endswith('@'+st)])
    unc=[]
    for l,a,b,c,d in G['segs']:
        if l not in('1','2','5','S-BEAM'): continue
        if not(x0<a<x1 and y0<b<y1): continue
        ln=LineString([(a,b),(c,d)])
        if ln.length<0.3: continue
        cov=ln.intersection(polys).length/ln.length
        if cov<0.5: unc.append((l,round(a,2),round(b,2),round(c,2),round(d,2),round(ln.length,2),round(cov,2)))
    print(st,len(unc))
    for u in sorted(unc): print('  ',u)
