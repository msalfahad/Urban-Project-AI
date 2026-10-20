# lines parallel to angle a (deg) near point: offset (signed, perpendicular), layer, length
import json,sys,math
G=json.load(open(sys.argv[1]));x,y,a=map(float,sys.argv[2:5]);R=float(sys.argv[5]) if len(sys.argv)>5 else 1.0
skip={'REIN','S-REIN-SLAB','S-REIN.D','S-TEXT.SCH','S-LINE.SCH','S-TEXT.D','LEVEL','S-REIN-CORNER','DEFPOINTS'}
ux,uy=math.cos(math.radians(a)),math.sin(math.radians(a));nx,ny=-uy,ux
out=set()
for l,x1,y1,x2,y2 in G['segs']:
    if l in skip: continue
    L=math.hypot(x2-x1,y2-y1)
    if L<0.05: continue
    ang=math.degrees(math.atan2(y2-y1,x2-x1))%180
    if min(abs(ang-a%180),180-abs(ang-a%180))>3: continue
    t1=(x1-x)*ux+(y1-y)*uy;t2=(x2-x)*ux+(y2-y)*uy
    if not (min(t1,t2)-0.01<=0<=max(t1,t2)+0.01): continue
    off=(x1-x)*nx+(y1-y)*ny
    if abs(off)<R: out.add((round(off,3),l,round(L,3),round(x1,3),round(y1,3),round(x2,3),round(y2,3),round(ang,2)))
for o in sorted(out): print(o)
