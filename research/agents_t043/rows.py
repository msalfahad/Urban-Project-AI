import sys, json
sys.path.insert(0, sys.argv[0].rsplit('/',1)[0])
import dxfscan as S
ents=[S.simplify(e) for e in S.entities(sys.argv[1]) if e['t']!='BLOCKDEF']
T=[d for d in ents if d['blk'] is None and d['t'] in ('TEXT','ATTRIB','MTEXT') and d.get('s')]
mode=sys.argv[2]
if mode=='row':   # same y band, x range
    y=float(sys.argv[3]); x0,x1=float(sys.argv[4]),float(sys.argv[5]); tol=float(sys.argv[6]) if len(sys.argv)>6 else 200
    r=sorted([d for d in T if abs(d['p'][1]-y)<tol and x0<=d['p'][0]<=x1], key=lambda d:d['p'][0])
    print(' | '.join('%s@%d'%(d['s'],d['p'][0]) for d in r))
elif mode=='col': # same x band
    x=float(sys.argv[3]); y0,y1=float(sys.argv[4]),float(sys.argv[5]); tol=float(sys.argv[6]) if len(sys.argv)>6 else 200
    r=sorted([d for d in T if abs(d['p'][0]-x)<tol and y0<=d['p'][1]<=y1], key=lambda d:d['p'][1])
    print(' | '.join('%s@%d'%(d['s'],d['p'][1]) for d in r))
