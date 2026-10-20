# beam schedule rows read from the drawing text (simple beams x105.84; CB rows by label y + 0.80)
import json,sys,re
T=json.load(open(sys.argv[1]))
S={}
simple=[o for o in T if abs(o['x']-105.84)<0.05 and re.fullmatch(r'(B\d+|CA|B\.W|SB\d)',o['t'].strip())]
for o in simple:
    near=[p for p in T if abs(p['y']-o['y'])<0.12 or (abs(p['y']-o['y'])<0.12)]
    b=[p for p in T if abs(p['x']-107.22)<0.05 and abs(p['y']-o['y'])<0.1]
    d=[p for p in T if abs(p['x']-108.69)<0.05 and abs(p['y']-o['y'])<0.1]
    S.setdefault(o['t'].strip(),[]).append((int(b[0]['t'])/100 if b else None,int(d[0]['t'])/100 if d else None,round(o['y'],2)))
for o in T:
    t=o['t'].strip()
    if re.fullmatch(r'CB\d+',t) and o['r']==90 and o['y']<20:
        bx={-0.29:14.21,21.46:35.97,59.70:79.83}[min((-0.29,21.46,59.70),key=lambda v:abs(v-o['x']))]
        b=[p for p in T if abs(p['x']-bx)<0.05 and abs(p['y']-(o['y']+0.8))<0.15]
        d=[p for p in T if abs(p['x']-(bx+1.52 if bx!=79.83 else 81.26))<0.06 and abs(p['y']-(o['y']+0.8))<0.15]
        # spans: text row at label y + 2.07
        sp=[p for p in T if abs(p['y']-(o['y']+2.07))<0.12 and bx-11<p['x']<bx-3 and re.fullmatch(r'\d+\.\d',p['t'].strip())]
        S[t]=[(int(b[0]['t'])/100,int(d[0]['t'])/100,[float(p['t']) for p in sorted(sp,key=lambda p:p['x'])])]
json.dump(S,open(sys.argv[2],'w'))
for k in sorted(S,key=lambda k:(k[:2],int(re.sub(r'\D','',k) or 0))): print(k,S[k])
