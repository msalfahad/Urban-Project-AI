import json,math,re,csv,sys
G=json.load(open('data/geom.json'));T=json.load(open('data/texts.json'));B=json.load(open('data/bands.json'));SC=json.load(open('data/sched.json'))
skip={'REIN','S-REIN-SLAB','S-REIN.D','S-TEXT.SCH','S-LINE.SCH','S-TEXT.D','LEVEL','S-REIN-CORNER','DEFPOINTS','S-TEXT-SLAB','S-SEC.LINE','S-HAT'}
FR={'2F':(-25,0),'1F':(12,36),'GF':(41,76)}
lab=[o for o in T if re.fullmatch(r'(C?B\d+|CA|B\.W)',o['t'].strip()) and o['y']>30]
def frame(x):
    for k,(a,b) in FR.items():
        if a<=x<=b: return k
rows=[]
for k,v in B.items():
    bid,st=k.split('@');p=v['pts']
    if len(p)!=4: rows.append(dict(id=k,shape='poly%d'%len(p),title=v['title']));continue
    e=[(p[i],p[(i+1)%4]) for i in range(4)]
    L=[math.dist(a,b) for a,b in e]
    i=max(range(4),key=lambda j:L[j]);(a,b)=e[i]
    ang=math.degrees(math.atan2(b[1]-a[1],b[0]-a[0]))%180
    cx=sum(q[0] for q in p)/4;cy=sum(q[1] for q in p)/4
    width=min(L);length=max(L)
    ux,uy=math.cos(math.radians(ang)),math.sin(math.radians(ang));nx,ny=-uy,ux
    offs=[]
    for l,x1,y1,x2,y2 in G['segs']:
        if l in skip: continue
        LL=math.hypot(x2-x1,y2-y1)
        if LL<0.1: continue
        a2=math.degrees(math.atan2(y2-y1,x2-x1))%180
        if min(abs(a2-ang),180-abs(a2-ang))>1.0: continue
        t1=(x1-cx)*ux+(y1-cy)*uy;t2=(x2-cx)*ux+(y2-cy)*uy
        if not(min(t1,t2)-0.01<=0<=max(t1,t2)+0.01): continue
        o=(x1-cx)*nx+(y1-cy)*ny
        if abs(o)<width/2+0.06: offs.append(round(o,3))
    offs=sorted(set(offs))
    drawn=round(max(offs)-min(offs),3) if len(offs)>=2 else None
    # labels parallel to the band axis within 0.8 m of the axis and inside its length
    near=[]
    for o in lab:
        if frame(o['x'])!=st: continue
        t=(o['x']-cx)*ux+(o['y']-cy)*uy; d=(o['x']-cx)*nx+(o['y']-cy)*ny
        ra=o['r']%180; da=min(abs(ra-ang),180-abs(ra-ang))
        if abs(t)<=length/2+0.3 and abs(d)<0.9 and da<15: near.append((o['t'].strip(),round(d,2)))
    rows.append(dict(id=k,title=v['title'],cx=round(cx,3),cy=round(cy,3),ang=round(ang,1),w=round(width,3),len=round(length,3),drawn=drawn,offs=offs,labels=near))
json.dump(rows,open('data/check.json','w'))
for r in sorted(rows,key=lambda r:r['id']):
    print(r)
