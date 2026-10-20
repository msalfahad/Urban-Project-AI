import json,csv,re,math,sys
S=sys.argv[2] if len(sys.argv)>2 else '.'  # scratch folder holding data/*.json and the repo clone as work/
RG=S+'/work/research/urban_engine_m4_correctness/st7757_route_g'
CH={r['id']:r for r in json.load(open(S+'/data/check.json'))}
SC=json.load(open(S+'/data/sched.json'))
SPANS={'CB3':'3.4 / 3.3 / 3.8','CB8':'3.7 / 6.4 / 6.8','CB9':'4.1 / 4.0 / 3.7','CB11':'7.1 / 3.2 / 3.7'}
SHEET={'2F':'SECOND FLOOR ROOF SLAB','1F':'FIRST FLOOR ROOF SLAB','GF':'GROUND FLOOR ROOF SLAB'}
def sch(m):
    if m not in SC: return ''
    b,h=SC[m][0][:2]
    if m.startswith('CB'):
        sp=SPANS.get(m,' / '.join(str(x) for x in SC[m][0][2]))
        tab='continuous 3-span' if m in SPANS else 'continuous 2-span'
        return f'{m} {int(b*100)}x{int(h*100)} ({tab} schedule, printed spans {sp} m)'
    return f'{m} {int(b*100)}x{int(h*100)} (simple-beam schedule)'
rows=[]
def add(**k): rows.append(k)
P=[r for r in csv.DictReader(open(RG+'/PROVISIONAL_REGISTER.csv')) if r['COMPONENT_ID'].startswith('BEAMS:') and r['UNIT']=='m3']
# replaced by drawing evidence / owner rules (T-043 hand, T-085, T-097 hand, verified ring geometry this run)
REPL={'BEAMS:GF:BAND0047.2','BEAMS:GF:BAND0048.1','BEAMS:1F:BAND0033','BEAMS:1F:BAND0034'}
CONF={'BEAMS:GF:BAND0008':'B29','BEAMS:GF:BAND0036.1':'CB2','BEAMS:GF:BAND0036.2':'CB2','BEAMS:GF:BAND0042':'B21','BEAMS:1F:BAND0009':'B6'}
for r in P:
    cid=r['COMPONENT_ID'];st=r['STOREY'];bid=cid.split(':')[2]
    d=json.loads(r['DIMENSIONS']);m=re.search(r'mark (\S+)',r['SOURCE']).group(1)
    c=CH.get(bid+'@'+st,{})
    if cid in REPL: continue
    base=float(r['BASE'])
    if cid in CONF:
        b,h=SC[m][0][:2];dw=c['drawn'];L=d['length_m']
        alt=round(dw*h*L,4)
        add(floor=st,component=cid,mark=m,type='beam span',status='CONFLICT',width_m=f'{b} schedule / {dw} drawn',depth_m=h,length_m=L,
            m3=f'{base:.4f} (schedule width) / {alt:.4f} (drawn width)',m3_low=min(base,alt),m3_high=max(base,alt),m3_calc='',
            section='schedule row only (no section cuts it)',schedule=sch(m),
            evidence=f"{SHEET[st]}: label {m} bound (worker 3 check); edge lines {dw:.3f} m apart over the span vs schedule {b}; engine released it at the schedule width",
            conflict=f'schedule width {b} vs drawn {dw}: same kind as CB10 (owner Q-61 C(1): never pick the schedule only because it is printed)',
            x=c.get('cx'),y=c.get('cy'))
        continue
    add(floor=st,component=cid,mark=m,type='beam span' if not bid in('BAND0049','BAND0050','BAND0051','BAND0052') else 'void ring arc piece',status='CALCULATED',
        width_m=d['width_m'],depth_m=d['depth_m'],length_m=d['length_m'],m3=f'{base:.4f}',m3_low=base,m3_high=base,m3_calc=base,
        section='schedule row (no section cuts it)',schedule=sch(m),
        evidence=f"{SHEET[st]}: label {m} parallel to the span (worker 3 check, offset {c.get('labels')}); drawn width {c.get('drawn')} = schedule; net plan {d['net_plan_m2']} m2 x {d['depth_m']} (route G, length not re-measured)",
        conflict='',x=c.get('cx'),y=c.get('cy'))
def man(**k):
    k.setdefault('conflict','');k.setdefault('m3_calc','');add(**k)
man(floor='GF',component='BEAMS:GF:BAND0047.1+.2',mark='B26',type='beam span (one span; planted column P.C 20x50 carried)',status='CALCULATED',width_m=0.65,depth_m=0.85,length_m=7.0675,m3='3.9048',m3_low=3.9048,m3_high=3.9048,m3_calc=3.9048,section='schedule row',schedule=sch('B26'),evidence='edge lines single from end column to B28 / column; the split outline is the planted column of P.C 20x50 (T-043, T-085 leader trace); 7.0675 x 0.65 x 0.85 (T-097 hand)',x=71.66,y=40.6)
man(floor='GF',component='BEAMS:GF:BAND0048.1+.2',mark='B27',type='beam span (one span; planted column P.C 20x70 carried)',status='CALCULATED',width_m=0.90,depth_m=0.85,length_m=4.9505,m3='3.7872',m3_low=3.7872,m3_high=3.7872,m3_calc=3.7872,section='schedule row',schedule=sch('B27'),evidence='two single edge lines 0.900 apart end column to end column; split outline = planted column of P.C 20x70 (T-043, T-085); 4.9505 x 0.90 x 0.85 (T-097 hand)',x=56.3,y=39.1)
man(floor='GF',component='BEAMS:GF:BAND0006',mark='B7',type='beam strip at the void',status='CALCULATED',width_m=0.20,depth_m=0.75,length_m=1.70,m3='0.2550',m3_low=0.255,m3_high=0.255,m3_calc=0.255,section='schedule row',schedule=sch('B7'),evidence="text B7 0.064 m above the 1.70 m strip, parallel (T-043, T-085 binder fix); worker 3 check: label parallel at 0.16 m; 1.70 x 0.20 x 0.75",x=72.263,y=48.628)
man(floor='GF',component='BEAMS:GF:BAND0043.1',mark='B20',type='beam span (west of the column)',status='CALCULATED',width_m=0.40,depth_m=0.75,length_m=3.00,m3='0.9000',m3_low=0.9,m3_high=0.9,m3_calc=0.9,section='Section A-A (cut x ~54.75): 40 / 75 cm, 11 T18 top and bottom = B20 row',schedule=sch('B20'),evidence='printed section on the span (T-043; T-102 builds the reader); 3.00 x 0.40 x 0.75',x=54.193,y=45.148)
man(floor='1F',component='BEAMS:1F:BAND0031.1',mark='B23',type='beam span (west of the column)',status='CALCULATED',width_m=0.45,depth_m=0.75,length_m=3.00,m3='1.0125',m3_low=1.0125,m3_high=1.0125,m3_calc=1.0125,section='Section B-B (cut x 15.667): 45 / 75 cm, 11 T18 top and bottom = B23 row',schedule=sch('B23'),evidence='printed section on the span (T-043; T-102); 3.00 x 0.45 x 0.75',x=15.469,y=45.123)
man(floor='GF',component='UPSTAND:GF:B20',mark='B20 upstand',type='upstand on top of B20 (not in the engine)',status='CALCULATED',width_m=0.20,depth_m=0.20,length_m=3.00,m3='0.1200',m3_low=0.12,m3_high=0.12,m3_calc=0.12,section='Section A-A: 20 / 20 cm on the beam',schedule='-',evidence='section drawing outline 0.80 x 0.80 at the 4x scale (worker 3 re-read: outline 43.03-44.63 x 46.39-50.19, upstand 43.83-44.63 x 49.39-50.19); plan line 0.20 inside the north face over 3.00 m',x=54.193,y=45.25)
man(floor='1F',component='UPSTAND:1F:B23',mark='B23 upstand',type='upstand on top of B23 (not in the engine)',status='CALCULATED',width_m=0.20,depth_m=0.20,length_m=3.00,m3='0.1200',m3_low=0.12,m3_high=0.12,m3_calc=0.12,section='Section B-B: 20 / 20 cm on the beam',schedule='-',evidence='section B-B (T-043); plan line 0.20 inside the north face over 3.00 m',x=15.469,y=45.25)
man(floor='1F',component='RING:1F:WEST (BAND0033-0036)',mark='B4',type='dome-opening ring beam (west opening)',status='CALCULATED',width_m=0.20,depth_m=0.50,length_m='arc pieces',m3='0.7553',m3_low=0.7553,m3_high=0.7553,m3_calc=0.7553,section='plan mark B4 (two B4 texts on the ring); dome detail ring "AS PER ARCH" dropped with the dome (owner Q-44 A)',schedule=sch('B4'),evidence='worker 3 geometry: annulus R 2.211 / 2.411 m (centre 16.380, 41.651) inside the box of CB10 inner face 14.269, CB13 face 18.369, B6 faces 39.440 / 43.862 = 1.5105 m2 x 0.50 = 0.7553 (= T-097); replaces the four arc pieces (0.281 released + 0.225 held)',x=16.38,y=41.651)
man(floor='1F',component='RING:1F:EAST',mark='(none printed)',type='dome-opening ring (east opening)',status='HELD',width_m=0.20,depth_m='not printed for this ring',length_m='arc pieces',m3='candidate 0.8997 at the B4 size',m3_low=0.8997,m3_high=0.8997,section='none on the plan; dome detail ring "AS PER ARCH"',schedule='-',evidence='worker 3 geometry: annulus R 2.211 / 2.411 (centre 30.828, 41.651) inside B25 face 28.617, CB12 face 32.989, B6 faces 39.440 / 43.862 = 1.7993 m2; NO B4 (or any) mark within 3.2 m of this ring (only B6, B25 and SEE DETAIL texts); the engine has no band for it; T-097 gave it B4 0.900 by passing the Q-44 A rule',conflict='owner Q-61 C(3): B4 only where the element is identified as B4; this ring is not',x=30.828,y=41.651)
# held items from T-043 (one row each), re-read this run where noted
H=[('2F','BEAMS:2F:BAND0001.3','(none)','unlabelled span past a column','0.090 - 0.271','east end span 1.13 m of the top band that carries B3 (west) and B8 (middle): no mark of its own; candidates B8 20x75 0.1695 / B3 20x40 0.0904','D-04'),
('2F','BEAMS:2F:BAND0006.1','(none)','unlabelled span past a column','0.248 - 0.744','west band south span 3.10 m; B15 printed only on the north span; candidates B15 20x120 0.744 or a 20x40 type','D-04'),
('2F','BEAMS:2F:BAND0008.1','(none)','unlabelled span past a column','0.112 - 0.336','vertical piece 1.40 m below the column; B1 on the span above; candidate B1 0.112','D-04'),
('2F','BEAMS:2F:BAND0011.1','(none)','unlabelled span past a column','0.112 - 0.336','vertical piece 1.40 m below the column; B1 on the span above; candidate B1 0.112','D-04'),
('1F','BEAMS:1F:BAND0005.1','(none)','unlabelled span past a column','0.064 - 0.192','0.80 m from the B23 face to the column; B2 on the north span only; candidate B2 0.064','D-04'),
('GF','BEAMS:GF:BAND0046.2','(none)','unlabelled span past a column','0.375 - 0.5625','east span 1.50 m past the column; drawn 0.50 = B24 width; candidate B24 0.5625','D-04'),
('GF','BEAMS:GF:BAND0019.2','CB3 and B3 (With Stair)','two marks on one span','0.212 / 0.3975','span 2 (2.65 m clear) of the 3-span band; CB3 printed under each of its 3 spans (the CB3 row prints 3 spans 3.4 / 3.3 / 3.8 m) and B3 + (With Stair) printed 0.15 m above span 2; B3 20x40 0.212, CB3 20x75 0.3975; counting both (0.610) is forbidden','D-03'),
('GF','BEAMS:GF:BAND0053','(B7, contested)','void ring arc piece','0.035 - 0.105','0.4377 m arc of the GF void ring; the rot-306 B7 text is parallel by the binder tangent rule (T-085: 0.0657 at B7) but not by the nearest-point tangent (T-043); 4 rotated B7 texts on 5 arc pieces','D-04'),
('1F','BEAMS:1F:BAND0026.1','CB10','inner west strip span 1','0.2875 / 0.3450','schedule 25x50, drawn 0.30; CB10 printed outside the outer 0.20 strip','D-02'),
('1F','BEAMS:1F:BAND0026.2','CB10','inner west strip span 2','0.4563 / 0.5475','as span 1; 3.65 m to the B23 face','D-02'),
('1F','BEAMS:1F:BAND0013.1','(none)','0.20 strip north of B23','0.240 - 0.720','north strip 3.00 m outside B23; Section B-B draws the beam outline only (no slab either side), so it neither shows nor excludes the strip','D-05'),
('1F','BEAMS:1F:BAND0013.2','(none)','0.20 strip north of B23 (east piece)','0.042 - 0.126','0.525 m east of the column; not cut by B-B','D-05'),
('GF','BEAMS:GF:BAND0031.1','(none)','0.20 strip north of B20','0.240 - 0.720','north strip 3.00 m outside B20, continuous with the GF outer west strip by a rounded corner; Section A-A draws the beam outline only','D-05'),
('GF','BEAMS:GF:BAND0031.2','(none)','0.20 strip north of B20 (east piece)','0.042 - 0.126','0.525 m east of the column','D-05'),
('1F','BEAMS:1F:BAND0014','(none)','outer west strip 0.20','0.600 - 1.800','7.50 m outside the CB10 inner strip, continuous with the north strip by a rounded corner','D-05'),
('1F','BEAMS:1F:BAND0023','(none)','south-east box 0.30','0.135 - 0.2025','0.90 x 0.30 box outside the south edge below CB11, joined by a rounded corner to the 0.10 east strip','D-05'),
('1F','BEAMS:1F:BAND0025','(none)','strip outside CB12 0.30','0.676 - 1.015','4.51 m outside CB12 (CB12 itself bound, 25 = drawn), rounded NE corner, a further line 0.05 m out','D-05')]
for st,cid,mk,ty,rng,ev,dc in H:
    c=CH.get(cid.split(':')[2]+'@'+st,{})
    lo,hi=[float(v) for v in re.split(r' - | / ',rng)]
    status='CONFLICT' if dc=='D-02' else 'HELD'
    man(floor=st,component=cid,mark=mk,type=ty,status=status,width_m=c.get('drawn',''),depth_m='see candidates',length_m=c.get('len',''),m3=('both '+rng if '/' in rng else 'range '+rng),m3_low=lo,m3_high=hi,
        section='none' if dc!='D-05' else 'section A-A / B-B outline only',schedule=sch('CB10') if dc=='D-02' else ('CB3 / B3 rows' if dc=='D-03' else '-'),evidence=ev+' (T-043 SPANS.csv; drawn width re-measured this run)',conflict='schedule 0.25 vs drawn 0.30' if dc=='D-02' else ('two marks' if dc=='D-03' else ''),designer=dc,x=c.get('cx'),y=c.get('cy'))
# projections the engine has no band for (silent today), found by the uncovered-line check of this run
man(floor='GF',component='NEW:GF:OUTER-WEST-STRIP',mark='(none)',type='outer west strip 0.20 (projection band)',status='HELD',width_m=0.20,depth_m='not printed',length_m=4.10,m3='plan 0.820 m2, depth not printed',m3_low='',m3_high='',section='none',schedule='-',evidence='lines x 52.493 and 52.693, y 41.248 - 45.348, cross lines at 41.87 / 44.32 / 44.96, rounded corner into the 0.20 strip north of B20; no engine band (0 % of the outer line inside any band); the GF analogue of the 1F outer west strip',conflict='',designer='D-26',x=52.593,y=43.3)
man(floor='1F',component='NEW:1F:EAST-STRIP-0.10',mark='(none)',type='0.10 strip outside CB12, south part',status='HELD',width_m=0.10,depth_m='not printed',length_m=5.69,m3='plan about 0.569 m2, depth not printed',m3_low='',m3_high='',section='none',schedule='-',evidence='line x 33.339 from 37.748 to 43.535 (5.787 m) 0.10 m outside the CB12 face 33.239, rounded into the SE box; no engine band',designer='D-26',x=33.289,y=40.64)
man(floor='1F',component='NEW:1F:EAST-BOX',mark='(none)',type='rounded box outside CB12 at mid length',status='HELD',width_m=0.40,depth_m='not printed',length_m=1.00,m3='plan about 0.39 m2 (corner radii not dimensioned), depth not printed',m3_low='',m3_high='',section='none',schedule='-',evidence='lines 33.239-33.639 x 43.535-44.535 with two rounded outer corners; no engine band',designer='D-26',x=33.44,y=44.04)
for r in rows:
    r.setdefault('designer','D-02' if r['status']=='CONFLICT' and r['mark']!='CB10' else r.get('designer',''))
for r in rows:
    if r['status']=='CONFLICT' and r['mark'] in ('B29','CB2','B21','B6'): r['designer']='D-27'
rows.sort(key=lambda r:({'GF':0,'1F':1,'2F':2}[r['floor']],{'CALCULATED':0,'CONFLICT':1,'HELD':2}[r['status']],r['component']))
F=['floor','component','mark','type','status','width_m','depth_m','length_m','m3','m3_low','m3_high','m3_calc','section','schedule','evidence','conflict','designer','x','y']
with open(sys.argv[1],'w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=F,extrasaction='ignore');w.writeheader()
    for i,r in enumerate(rows,1): r['component']=r['component']; w.writerow(r)
import collections
agg=collections.defaultdict(lambda:[0,0.0,0.0,0.0])
for r in rows:
    a=agg[(r['floor'],r['status'])];a[0]+=1
    a[1]+=float(r['m3_low'] or 0);a[2]+=float(r['m3_high'] or 0);a[3]+=float(r['m3_calc'] or 0)
for k in sorted(agg): print(k,agg[k][0],'low %.4f high %.4f calc %.4f'%tuple(agg[k][1:]))
tot=collections.defaultdict(lambda:[0,0.0,0.0,0.0])
for (fl,s),a in agg.items():
    t=tot[s];t[0]+=a[0];t[1]+=a[1];t[2]+=a[2];t[3]+=a[3]
for s,t in tot.items(): print(s,t[0],'low %.4f high %.4f calc %.4f'%tuple(t[1:]))
print(len(rows))
