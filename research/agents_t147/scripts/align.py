"""Translation from architectural plan metres to structural roof-slab plan metres, per floor, from column outlines."""
import ezdxf,sys,json,numpy as np,collections
A=ezdxf.readfile(sys.argv[1]).modelspace(); T=ezdxf.readfile(sys.argv[2]).modelspace()
AW={'GF':(-162,-127,-807,-789),'1F':(-196,-173,-806,-790),'2F':(-237,-224,-799,-790)}
SW={"GF": (40.5, 74.5, 35.5, 51.0), "1F": (11.5, 36.0, 35.5, 51.0), "2F": (-27.0, -2.0, 35.5, 51.0)}
def cents(m,w):
    out=[]
    for e in m.query('LWPOLYLINE[layer=="S-COL.BON"]'):
        p=np.array([(x/1000,y/1000) for x,y,*_ in e.get_points()])
        if len(p)<3: continue
        c=p.mean(0); s=p.max(0)-p.min(0)
        if w[0]<c[0]<w[1] and w[2]<c[1]<w[3] and s.max()<1.5:
            if all(np.linalg.norm(c-u)>0.05 for u in out): out.append(c)
    return out
res={}
for f in AW:
    a=cents(A,AW[f]); s=cents(T,SW[f])
    votes=collections.Counter()
    for p in a:
        for q in s: votes[tuple(np.round(q-p,2))]+=1
    t,n=votes.most_common(1)[0]
    t=np.array(t)
    # refine: mean offset of matched pairs
    pr=[(q-p) for p in a for q in s if np.linalg.norm(q-p-t)<0.03]
    t2=np.mean(pr,0)
    res[f]=[float(t2[0]),float(t2[1])]
    print(f,'arch cols',len(a),'struct cols',len(s),'matched',len(pr),'t',np.round(t2,4),'spread',np.round(np.std(pr,0),4))
json.dump(res,open(sys.argv[3],'w'))
