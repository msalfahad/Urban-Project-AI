# engine band polygons from the committed route-G overlay (svg), mapped to drawing metres by a fit on the
# 24 unresolved rows that carry metre centres
import re,csv,json,sys
import numpy as np
R=sys.argv[1]
U={r['COMPONENT_ID'].split(':')[2]+'@'+r['STOREY']:(float(r['X_M']),float(r['Y_M'])) for r in csv.DictReader(open(R+'/UNRESOLVED_CONCRETE_EXCEPTIONS.csv')) if r['COMPONENT_ID'].startswith('BEAMS')}
out={}
for sh,st in (('SH02_SLAB_PLAN_2F','2F'),('SH04_SLAB_PLAN_1F','1F'),('SH06_SLAB_PLAN_GF','GF')):
    s=open(f'{R}/overlays/{sh}.svg').read()
    P=[]
    for pts,title in re.findall(r'<polygon points="([^"]+)"[^>]*><title>([^<]*)',s):
        xy=np.array([[float(v) for v in p.split(',')] for p in pts.split()])
        t=title.split()
        if not t[0].startswith('BAND'): continue
        P.append((t[0],' '.join(t[1:]),xy))
    A=[];B=[]
    for bid,ti,xy in P:
        k=bid+'@'+st
        if k in U: c=xy.mean(0); A.append([c[0],c[1],1]); B.append(U[k])
    A=np.array(A);B=np.array(B)
    if len(A)<3: print(st,'not enough',len(A)); continue
    M,res,_,_=np.linalg.lstsq(A,B,rcond=None)
    err=np.abs(A@M-B).max()
    print(st,len(A),'fit max err m',round(err,4),'scale',M[0,0],M[1,1])
    for bid,ti,xy in P:
        w=np.c_[xy,np.ones(len(xy))]@M
        out[bid+'@'+st]=dict(title=ti,pts=w.round(4).tolist())
json.dump(out,open(sys.argv[2],'w'))
print(len(out))
