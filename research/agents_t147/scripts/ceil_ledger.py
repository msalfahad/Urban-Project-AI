"""T-147 hand-measurement aid (research only, NOT engine code): Alsenan ceilings per room.
Room polygons: architectural DXF regions (rooms.py), with named clips where a room is open to another.
Above each room: the roof-slab faces of the same floor (T-139 faces + classes, PANELS.csv), moved onto the plan by the
column-fit translation (align.json). Beam depth: the T-110 beam member register (span whose midpoint lies in the face).
Writes <out>/rooms_geom.json. Decides nothing about finishes: that is done by rule in t147_calc.py.
Usage: python -I ceil_ledger.py <scratch> <panels.csv> <register.csv> <out_dir>"""
import json,csv,sys,math,os
from shapely import wkt
from shapely.affinity import translate
from shapely.geometry import box,Polygon
from shapely.ops import unary_union
S,PAN,REGF,OUT=sys.argv[1:5]; os.makedirs(OUT,exist_ok=True)
AL=json.load(open(f'{S}/align.json')); SF=json.load(open(f'{S}/st_faces.json'))
CLS={r['id']:r for r in csv.DictReader(open(PAN))}
REG=list(csv.DictReader(open(REGF)))
RJ={f:{o['i']:wkt.loads(o['wkt']) for o in json.load(open(f'{S}/{j}'))['faces']} for f,j in (('GF','gf_rooms.json'),('1F','f1_rooms.json'),('2F','f2_rooms.json'))}
def U(fl,ids): return unary_union([RJ[fl][i] for i in ids])
# --- open zones -----------------------------------------------------------------------------------------------
GF0=RJ['GF'][0]
gclip=Polygon([(-148.2,-805.094),(-129.07,-805.094),(-129.07,-797.594),(-131.0,-797.594),(-131.0,-795.9),(-145.05,-795.9),(-145.05,-800.45),(-148.2,-800.45)])
lobby=unary_union([GF0.intersection(box(-140.6,-796.0,-137.85,-793.0)),RJ['GF'][168]])
gopen=GF0.intersection(gclip).difference(lobby)
pantry=gopen.intersection(box(-148.2,-805.2,-145.05,-800.45))
dining=gopen.difference(pantry)
F1=RJ['1F'][8]; sh1=F1.intersection(box(-189.893,-797.194,-187.393,-791.994)); open1=F1.difference(sh1)
F2=RJ['2F'][12]; sh2=F2.intersection(box(-234.745,-797.194,-232.245,-791.994)); lob2=F2.difference(sh2)
# --- room list: id, floor, name, kind (DRY / WET / STAIR / SHAFT / EXT), polygon, reference area and its source -------
R=[
 ('GF-01','GF','dewaneya','DRY',U('GF',[20]),24.94,'printed 400 x 630 less R1.10 corner (T-088)'),
 ('GF-02','GF','wash by the dewaneya','WET',U('GF',[13]),3.1325,'T-074 hand table'),
 ('GF-03','GF','W.C. by the dewaneya','WET',U('GF',[15]),3.375,'T-074'),
 ('GF-04','GF','driver room','DRY',U('GF',[44]),7.875,'printed 175 x 450'),
 ('GF-05','GF','driver W.C.','WET',U('GF',[11]),1.95,'T-074'),
 ('GF-06','GF','kitchen','WET',U('GF',[9]),9.63,'T-074'),
 ('GF-07','GF','pantry (open side to the dining)','WET',pantry,13.5,'printed 450 x 300 (owner Q-37 A)'),
 ('GF-08','GF','open room: dining / entrance / reception / saloon / hall to the master bed room','DRY',dining,None,'-'),
 ('GF-10','GF','W.C. 175 x 135 by the stair','WET',U('GF',[130]),2.3625,'T-074'),
 ('GF-11','GF','basin space 110 x 135','WET',U('GF',[131]),1.485,'T-074'),
 ('GF-12','GF','W.C. core wedge A','WET',U('GF',[149]),2.6752,'T-074'),
 ('GF-13','GF','W.C. core wedge B','WET',U('GF',[121]),2.3676,'T-074'),
 ('GF-14','GF','wash lobby, 2 basins','WET',lobby,4.7321,'T-074'),
 ('GF-15','GF','master bed room','DRY',U('GF',[164]),None,'-'),
 ('GF-16','GF','bath of the master bed room','WET',U('GF',[163]),3.7173,'T-074'),
 ('GF-X1','GF','unlabelled face between the wedge W.C.s','HELD',U('GF',[123]),None,'-'),
 ('ST-GF','GF','main stair shaft, GF part','STAIR',U('GF',[2]),12.475,'engine V2.9 face'),
 ('LIFT-GF','GF','lift shaft','SHAFT',U('GF',[132]),3.24,'printed 180 x 180'),
 ('1F-01','1F','master bed room west 425 x 450','DRY',U('1F',[20]),19.125,'printed 425 x 450'),
 ('1F-02','1F','bath west upper 245 x 205','WET',U('1F',[28]),5.0225,'T-074'),
 ('1F-03','1F','bath west lower 245 x 205','WET',U('1F',[22]),5.0225,'T-074'),
 ('1F-04','1F','master bed room 500 x 365','DRY',U('1F',[13]),18.25,'printed 500 x 365'),
 ('1F-07','1F','laundry','WET',U('1F',[3,99]),10.151,'T-074'),
 ('1F-08','1F','W.C. 147 x 180','WET',U('1F',[125]),2.646,'T-074'),
 ('1F-09','1F','bath by the laundry 200 x 180','WET',U('1F',[136]),3.5775,'T-074'),
 ('1F-10','1F','master bed room 380 x 430','DRY',U('1F',[128]),16.34,'printed 380 x 430'),
 ('1F-11','1F','master bed room east (curved W17) with its entry','DRY',U('1F',[113,115]),None,'-'),
 ('1F-12','1F','bath east 210 x 225','WET',U('1F',[166]),4.725,'T-074'),
 ('1F-X1','1F','unlabelled space by arch120 (no label)','HELD',U('1F',[140]),None,'-'),
 ('1F-13','1F','living + corridor + landing + connector + light well (open zone)','DRY',open1,None,'-'),
 ('ST-1F','1F','main stair shaft, 1F part','STAIR',sh1,None,'-'),
 ('LIFT-1F','1F','lift shaft','SHAFT',U('1F',[77]),3.24,'printed 180 x 180'),
 ('2F-01','2F','2F stair lobby (outside the shaft box)','DRY',lob2,None,'printed lobby 450 x 195 = 8.775 includes the 4.875 arrival inside the shaft box (owner Q-70)'),
 ('2F-02','2F','W.C. 300 x 185','WET',U('2F',[8]),5.55,'T-074'),
 ('2F-03','2F','maid room 300 x 645','DRY',U('2F',[49]),19.35,'printed 300 x 645'),
 ('ST-2F','2F','main stair shaft, 2F part (to the roof)','STAIR',sh2,None,'-'),
 ('LIFT-2F','2F','lift shaft','SHAFT',U('2F',[10]),3.24,'printed 180 x 180'),
]
def regmatch(fl,face):
    """register span the face belongs to: the span midpoint on the face's long axis (offset < 0.12 m), the face within
    half the span length (+0.15 m) of that midpoint along the axis, drawn width = register width (+-0.06 m or a CONFLICT
    row naming the drawn width); nearest such span wins. None = no register row (depth unknown)."""
    from shapely.geometry import Point
    c=list(face.minimum_rotated_rectangle.exterior.coords)
    e1=(c[1][0]-c[0][0],c[1][1]-c[0][1]); e2=(c[2][0]-c[1][0],c[2][1]-c[1][1])
    L1,L2=math.hypot(*e1),math.hypot(*e2)
    ax=e1 if L1>=L2 else e2; La=max(L1,L2); nw=min(L1,L2)
    ux,uy=ax[0]/La,ax[1]/La; cx,cy=face.centroid.x,face.centroid.y
    best=None
    for r in REG:
        if r['floor']!=fl: continue
        try: x,y=float(r['x']),float(r['y']); Ls=float(r['length_m'])
        except: continue
        dx,dy=x-cx,y-cy; along=abs(dx*ux+dy*uy); off=abs(-dx*uy+dy*ux)
        if off>0.12 or along>Ls/2+La/2+0.15: continue
        ws=[]
        for tok in r['width_m'].replace('schedule','').replace('drawn','').split('/'):
            try: ws.append(float(tok))
            except: pass
        if ws and min(abs(w-nw) for w in ws)>0.06 and nw>0.12: continue
        k=(off+along*0.01)
        if best is None or k<best[0]: best=(k,r)
    return best[1] if best else None
out=[]
for rid,fl,name,kind,g,ref,refsrc in R:
    t=AL[fl]; gs=translate(g,t[0],t[1])
    rec={'id':rid,'floor':fl,'name':name,'kind':kind,'dxf_area':round(g.area,4),'ref_area':ref,'ref_src':refsrc,
         'perimeter':round(g.length,3),'above':{},'beams':[],'openings':[]}
    for f in SF[fl]:
        fg=wkt.loads(f['wkt'])
        if not fg.intersects(gs): continue
        x=fg.intersection(gs)
        if x.area<0.005: continue
        cls=CLS.get(f['id'],{}).get('cls','?')
        rec['above'][cls]=round(rec['above'].get(cls,0)+x.area,4)
        if cls in('BEAM_OR_COLUMN','BEAM','BEAM_HELD','EDGE_HELD'):
            c=x.minimum_rotated_rectangle.exterior.coords; e=sorted([math.dist(c[0],c[1]),math.dist(c[1],c[2])])
            free=x.boundary.difference(gs.boundary.buffer(0.012)).length
            r=regmatch(fl,fg)
            rec['beams'].append({'face':f['id'],'cls':cls,'piece_m2':round(x.area,4),'w':round(e[0],3),'l':round(e[1],3),
                'free_edge_m':round(free,3),'member':r['member_id'] if r else None,'mark':(r['mark'] if r else None),
                'b':(r['width_m'] if r else None),'D':(r['depth_m'] if r else None),'status':(r['status'] if r else 'NO REGISTER ROW'),
                'texts':f['texts']})
        if cls in('OPENING','VOID+STAIR','DOME_OPENING+RING','OPENING+RING','STAIR','NOT_THIS_SLAB','EDGE_HELD','NOT_SLAB','DETAIL'):
            edge=x.boundary.difference(gs.boundary.buffer(0.012)).length
            o={'face':f['id'],'cls':cls,'m2':round(x.area,4),'edge_in_room_m':round(edge,3),'texts':f['texts']}
            if cls.startswith('DOME'):
                from shapely.geometry import Point as _P
                # T-110 ring geometry (drawing metres): west centre (16.380, 41.651), east (30.828, 41.651); R 2.211 / 2.411
                dome=[_P(16.380,41.651).buffer(2.2111,256),_P(30.828,41.651).buffer(2.2111,256)]
                op=unary_union([x.intersection(d) for d in dome])
                o['open_m2']=round(op.area,4); o['ring_m2']=round(x.area-op.area,4)
                o['open_edge_in_room_m']=round(op.boundary.difference(gs.boundary.buffer(0.012)).length,3) if op.area>0.05 else 0.0
            rec['openings'].append(o)
    rec['covered_m2']=round(sum(rec['above'].values()),4)
    out.append(rec)
json.dump(out,open(f'{OUT}/rooms_geom.json','w'),indent=1)
for r in out:
    print(r['id'],r['dxf_area'],r['ref_area'],'cov',r['covered_m2'],{k:v for k,v in r['above'].items()})
    for b in r['beams']:
        if b['w']>=0.06: print('   beam',b['face'],b['mark'],b['b'],b['D'],b['status'],'piece',b['piece_m2'],b['w'],'x',b['l'],'free',b['free_edge_m'])
    for o in r['openings']: print('   open',o)
