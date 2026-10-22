import ezdxf,json,sys,numpy as np
S=sys.argv[1]
d=ezdxf.readfile(S+'/data/st.dxf');m=d.modelspace()
B=json.load(open(S+'/bands.json'))
ext={}
for st in ('GF','1F','2F'):
    P=np.array([p for k,v in B.items() if k.endswith(st) for p in v['pts']]); ext[st]=(P.min(0)-1,P.max(0)+1)
cols={st:[] for st in ext}
for e in m.query('LWPOLYLINE[layer=="S-COL.BON"]'):
    p=np.array([(x/1000,y/1000) for x,y,*_ in e.get_points()])
    if len(p)<3: continue
    c=p.mean(0); sz=p.max(0)-p.min(0)
    for st,(a,b) in ext.items():
        if (c>a).all() and (c<b).all() and sz.max()<1.2: cols[st].append((c.round(3).tolist(),sz.round(3).tolist()))
A=json.load(open(S+'/t117.json'))
out={}
for st in ('GF','1F','2F'):
    f=A['floors'][st]; o=np.array(f['origin_drawing'])*0.001
    ac=[np.array(q).mean(0)+o for q in f['columns_local_m']]
    sc=[np.array(c) for c,_ in cols[st]]
    # dedupe structural col centres
    U=[]
    for c in sc:
        if all(np.linalg.norm(c-u)>0.05 for u in U): U.append(c)
    sc=U
    print(st,'arch cols',len(ac),'struct cols',len(sc))
    best=None
    for a in ac:
        for s in sc:
            t=s-a
            n=sum(min(np.linalg.norm(x+t-y) for y in sc)<0.06 for x in ac)
            if best is None or n>best[0]: best=(n,t)
    n,t=best
    pairs=[(x,min(sc,key=lambda y:np.linalg.norm(x+t-y))) for x in ac]
    pairs=[(x,y) for x,y in pairs if np.linalg.norm(x+t-y)<0.06]
    t=np.mean([y-x for x,y in pairs],0)
    res=max(np.linalg.norm(x+t-y) for x,y in pairs)
    print(st,'matched',len(pairs),'shift',t.round(4),'max resid',round(res,4))
    out[st]=dict(shift=t.tolist(),matched=len(pairs),arch_cols=len(ac),struct_cols=len(sc),resid=res)
json.dump(out,open(S+'/align.json','w'))
