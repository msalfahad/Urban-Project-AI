"""T-128 calc: plaster / paint / wet-wall tile per Alsenan room, owner manual method (G1) and drawing-derived method,
side by side. Standard library only. Every input typed here with its source; wall-face lengths come from the
hand-checked raster trace of the Drive architectural DXF (trace_lengths.json, produced in the scratchpad)."""
import csv, json, sys
DEC, SLAB, OWNER_FLOOR = 0.15, 0.16, 0.10   # Q-48 A decor depth; ST general note slab 16 cm; owner Q-43 floor allowance
ZONE = {  # floor-to-floor on the printed marks, owner manual height (G1 / G2), status of the owner height
 'GF_MAIN': (4.50, 3.65, 'OWNER MANUAL'), 'GF_ANNEX': (4.00, 3.15, 'OWNER MANUAL - PROVISIONAL (G2: +4.30 datum held)'),
 '1F': (4.20, 3.35, 'OWNER MANUAL'), '2F': (4.20, 3.35, 'OWNER MANUAL'),
 'LEVEL_UNCLEAR': (None, None, 'HELD: room level +0.30 or +1.00 not drawn (T-088)'),
 'SHAFT': (None, None, 'HELD: owner formula is a room-storey rule; no owner rule for a stair-shaft wall (T-090)')}
DOOR_H, MAIN_H = 2.20, 2.50   # Q-55: 2.20 m ASSUMED fallback; main entrance 2.00 x 2.50 printed (SE p.6)
def D(w, name, h=DOOR_H, tag='door, head 2.20 ASSUMED (Q-55)'): return dict(id=name, w=w, sill=0.0, head=h, tag=tag)
def W(w, name, sill=None, head=None, tag=''): return dict(id=name, w=w, sill=sill, head=head, tag=tag)
def ARCH(w, name): return dict(id=name, w=w, sill=0.0, head=None, tag='arch opening, head not printed')
L = json.load(open(sys.argv[1]))
# id, room, kind, zone, length key, openings, crossing beams (T-112 / T-110), freelancer gross m2 for the same room (his rows)
ROOMS = [
 ('GF-01','dewaneya','DRY','GF_ANNEX','GF dewaneya',[D(1.00,'D120'),ARCH(1.00,'arch to wash'),W(1.95,'W11'),W(1.95,'W12')],'CB6 0.75',72.00),
 ('GF-02','wash by the dewaneya','WET','GF_ANNEX','GF wash by dewaneya',[ARCH(1.00,'arch to dewaneya'),D(0.80,'D315')],'',24.30),
 ('GF-03','W.C. by the dewaneya','WET','GF_ANNEX','GF WC by dewaneya',[D(0.80,'D315')],'',None),
 ('GF-04','driver room','DRY','GF_ANNEX','GF driver',[D(0.90,'d220'),D(0.80,'D315'),W(0.60,'W04')],'',45.00),
 ('GF-05','driver W.C.','WET','GF_ANNEX','GF driver WC',[D(0.80,'D315')],'',None),
 ('GF-06','kitchen','WET','GF_ANNEX','GF kitchen',[D(1.00,'D120'),W(1.50,'W08')],'',None),
 ('GF-07','pantry (open side 4.46 m not a wall)','WET','GF_MAIN','GF pantry',[D(1.00,'D120'),W(1.50,'W09'),W(1.00,'W10')],'B27 0.85',None),
 ('GF-08','open room: dining / entrance / reception / saloon','DRY','GF_MAIN','GF open room (din)',[D(2.00,'D01 main entrance',MAIN_H,'door, 2.50 PRINTED'),D(1.00,'D120 to stair hall'),D(1.00,'D115 to master bed'),W(6.33,'W02 saloon glazing'),W(0.93,'other glazing (plan)')],'B26 0.85; B27 0.85',195.30),
 ('GF-15','master bed room','DRY','GF_MAIN','GF master bed',[D(1.00,'D115'),D(0.68,'bath door (loose arc, D15)'),W(3.96,'W03 pool-side glazing',0.0,4.30,'PRINTED +1.00 to +5.30 (T-083, PROBABLE)')],'',75.78),
 ('GF-16','bath of the master bed room','WET','GF_MAIN','GF master bath',[D(0.80,'bath door'),W(0.60,'W05-07')],'',None),
 ('GF-10','W.C. 175 x 135 by the stair','WET','LEVEL_UNCLEAR','GF WC 175x135 by stair',[D(0.80,'D315'),W(0.60,'W05-07')],'',None),
 ('GF-12','W.C. core wedge A','WET','GF_MAIN','GF WC wedge A',[D(0.80,'D315'),W(0.60,'W05-07')],'',None),
 ('GF-13','W.C. core wedge B','WET','GF_MAIN','GF WC wedge B',[D(0.80,'D315')],'',None),
 ('GF-14','wash lobby, 2 basins (open side 1.21 m)','WET','GF_MAIN','GF wash lobby',[D(0.80,'D315'),D(0.80,'D315')],'B11 0.75',None),
 ('GF-11','basin space 110 x 135 + stair passage','WET','LEVEL_UNCLEAR','GF basin 110x135',[D(0.80,'D315 W.C.'),D(1.00,'D120 to open room')],'',None),
 ('1F-01','master bed room west 425 x 450','DRY','1F','1F mbed W 425x450',[D(1.00,'D115'),D(0.80,'D315'),W(2.45,'W14',1.20,2.80,'PRINTED sill +6.70, 1.60 high')],'B6 0.50',59.50),
 ('1F-04','master bed room 500 x 365','DRY','1F','1F mbed 500x365',[D(1.00,'D115'),D(0.80,'D315'),W(1.55,'W24')],'',58.82),
 ('1F-10','master bed room 380 x 430','DRY','1F','1F mbed 380x430',[D(0.90,'D215'),ARCH(1.00,'arch120 to the dressing passage')],'B19 0.75; B6 0.50',75.82),
 ('1F-11','master bed room east (curved W17)','DRY','1F','1F mbed E',[D(0.90,'D215'),D(0.80,'D315'),W(3.32,'W17 (inner face)',0.20,3.70,'PRINTED NW chain 20/305/45')],'',74.46),
 ('1F-07','laundry','WET','1F','1F laundry',[D(0.90,'d220'),D(0.80,'D315'),W(0.60,'W19-23')],'',None),
 ('1F-08','W.C. 147 x 180','WET','1F','1F WC 147x180',[D(0.80,'D315'),W(0.60,'W19-23')],'',None),
 ('1F-02','bath west upper 245 x 205','WET','1F','1F bath W upper',[D(0.80,'D315'),W(0.60,'W19-23')],'',None),
 ('1F-03','bath west lower 245 x 205','WET','1F','1F bath W lower',[D(0.80,'D315'),W(0.60,'W19-23')],'',None),
 ('1F-12','bath east 210 x 225','WET','1F','1F bath E 210x225',[D(0.80,'D315'),W(0.50,'W18',0.84,3.00,'PRINTED sill +6.34 head +8.50')],'',None),
 ('1F-09','bath by the laundry 200 x 180','WET','1F','1F bath by laundry',[D(0.80,'D315'),W(0.60,'W19-23')],'',None),
 ('1F-13','living area + corridor + landing + connector (open zone)','DRY','1F','1F living zone',[D(0.90,'D215'),D(0.90,'D215'),D(0.90,'d220'),D(1.00,'D115'),W(1.55,'W15 (sill not printed)'),W(1.55,'W16')],'B25 / CB12 0.75 on edges',140.875+31.79),
 ('2F-03','maid room 300 x 645','DRY','2F','2F maid',[D(0.90,'d220'),D(0.80,'D315'),W(1.20,'W29')],'B2 0.40',64.26),
 ('2F-02','W.C. 300 x 185','WET','2F','2F WC 300x185',[D(0.80,'D315'),W(0.60,'W28')],'',None),
 ('2F-01','2F stair lobby (outside the shaft)','DRY','2F','2F lobby',[D(1.00,'D26 roof door'),D(0.90,'d220')],'B15 1.20',30.60),
]
SHAFTS = [ # main dog-leg stair shaft faces per storey (inside the shaft rectangle), storey interval on the marks
 ('ST-GF','stair shaft, GF part','GF basin 110x135',4.50,[D(1.00,'D120 north door'),W(1.20,'W01',None,None,'PRINTED +2.00 to +4.00')],40.50),
 ('ST-1F','stair shaft, 1F part','1F living zone',4.20,[D(1.00,'D115 to bed room'),W(1.20,'W13',None,None,'PRINTED +6.50 to +8.80'),W(1.00,'north window')],None),
 ('ST-2F','stair shaft, 2F part (to the roof)','2F lobby',4.20,[W(1.20,'W26 arched'),W(1.00,'W27')],None),
]
def face(key, zone):
    v=L[key]; p=v['parts'].get(zone,{})
    f=sum(x for k,x in p.items() if k not in('VIRT','REVEAL'))
    tot=v['face_m_raw']
    return round(f + v['corr_m']*(f/tot if tot else 0), 3), v
def ded(op, H):
    if op['head'] is None or op['sill'] is None or H is None: return None
    return op['w']*max(0.0, min(op['head'],H)-max(op['sill'],0.0))
def nets(gross, ops, H):
    if gross is None: return None, None, None, 'HELD'
    known=sum(d for d in (ded(o,H) for o in ops) if d is not None)
    unk=[o for o in ops if ded(o,H) is None]
    if not unk: return round(gross-known,3), round(gross-known,3), round(known,3), 'PROVISIONAL (door heights ASSUMED, Q-55)'
    lo=gross-known-sum(o['w']*H for o in unk)
    return round(lo,3), round(gross-known,3), round(known,3), 'HELD: '+', '.join(o['id'] for o in unk)+' height not printed'
rows=[]
for rid,name,kind,zone,key,ops,beams,fl in ROOMS:
    Lf,v=face(key,'ROOM')
    ftf,Ho,ost=ZONE[zone]
    datum=v.get('datum_split_m',{}); roof_share=datum.get('ROOF',0)/max(1e-9,sum(datum.values()))
    g_own=round(Lf*Ho,3) if Ho else None
    if ftf:
        paint_lo,paint_hi=ftf-SLAB-OWNER_FLOOR-DEC, ftf-SLAB-DEC
        plast_hi=ftf-SLAB
    else: paint_lo=paint_hi=plast_hi=None
    dst=('PROVISIONAL-DATUM (above is a finished roof mark; roof build-up not printed; G2 logic)' if zone=='GF_ANNEX' or roof_share>0.5
         else 'PROVISIONAL (floor build-up not printed: 0 .. 0.10 m)') if ftf else 'HELD: level not drawn'
    if zone=='GF_ANNEX': dst='PROVISIONAL-DATUM (+4.30 not the structural slab, Q-54 B / G2)'
    g_dlo=round(Lf*paint_lo,3) if ftf else None; g_dhi=round(Lf*paint_hi,3) if ftf else None
    n_own=nets(g_own,ops,Ho)
    n_dlo=nets(g_dlo,ops,paint_lo); n_dhi=nets(g_dhi,ops,paint_hi)
    rows.append(dict(ROW=rid,ROOM=name,KIND=kind,ZONE=zone,FACE_LENGTH_M=Lf,
        UNDER_ROOF_SHARE=round(roof_share,2),OWNER_H_M=Ho,OWNER_STATUS=ost,OWNER_GROSS_M2=g_own,
        OWNER_NET_M2=(n_own[1] if n_own[0]==n_own[1] else f"{n_own[0]:.2f} .. {n_own[1]:.2f}") if g_own else 'HELD',OWNER_NET_STATUS=n_own[3] if g_own else 'HELD',
        DWG_PAINT_TILE_H_M=f"{paint_lo:.2f} .. {paint_hi:.2f}" if ftf else 'HELD',DWG_PLASTER_H_M=f"{paint_lo:.2f} .. {plast_hi:.2f}" if ftf else 'HELD',
        DWG_STATUS=dst,DWG_GROSS_M2=f"{g_dlo:.2f} .. {g_dhi:.2f}" if ftf else 'HELD',
        DWG_PLASTER_GROSS_M2=f"{g_dlo:.2f} .. {Lf*plast_hi:.2f}" if (ftf and kind=='DRY') else '',
        DIFF_H_M=f"+{paint_lo-Ho:.2f} .. +{paint_hi-Ho:.2f}" if (ftf and Ho) else '-',
        DIFF_M2=f"+{g_dlo-g_own:.2f} .. +{g_dhi-g_own:.2f}" if (ftf and Ho) else '-',
        CROSSING_BEAMS=beams, OPENINGS='; '.join(f"{o['id']} {o['w']:.2f}" + (f" [{o['tag']}]" if o['tag'] else '') for o in ops),
        KNOWN_DEDUCTION_OWNER_M2=n_own[2] if g_own else '',FREELANCER_GROSS_M2=fl if fl is not None else ''))
for rid,name,key,ftf,ops,fl in SHAFTS:
    Lf,v=face(key,'STAIR_SHAFT')
    rows.append(dict(ROW=rid,ROOM=name,KIND='SHAFT',ZONE='SHAFT',FACE_LENGTH_M=Lf,UNDER_ROOF_SHARE='',OWNER_H_M='HELD',OWNER_STATUS=ZONE['SHAFT'][2],
        OWNER_GROSS_M2='HELD',OWNER_NET_M2='HELD',OWNER_NET_STATUS='HELD',
        DWG_PAINT_TILE_H_M=(f"{ftf-SLAB-OWNER_FLOOR-DEC:.2f} .. {ftf-SLAB-DEC:.2f} (top storey, to the decor ceiling)" if rid=='ST-2F' else f"{ftf:.2f} (storey interval, shaft wall continuous)"),
        DWG_PLASTER_H_M=(f"{ftf-SLAB-OWNER_FLOOR-DEC:.2f} .. {ftf-SLAB:.2f}" if rid=='ST-2F' else f"{ftf:.2f}"),
        DWG_STATUS='PROVISIONAL-DATUM (roof +13.90 drawn on the roof band top)' if rid=='ST-2F' else 'PROVISIONAL (landing-slab edge bands not deducted)',
        DWG_GROSS_M2=(f"{Lf*(ftf-SLAB-OWNER_FLOOR-DEC):.2f} .. {Lf*(ftf-SLAB-DEC):.2f}" if rid=='ST-2F' else f"{Lf*ftf:.2f}"),
        DWG_PLASTER_GROSS_M2=(f"{Lf*(ftf-SLAB-OWNER_FLOOR-DEC):.2f} .. {Lf*(ftf-SLAB):.2f}" if rid=='ST-2F' else f"{Lf*ftf:.2f}"),
        DIFF_H_M='-',DIFF_M2='-',CROSSING_BEAMS='',OPENINGS='; '.join(f"{o['id']} {o['w']:.2f}" + (f" [{o['tag']}]" if o['tag'] else '') for o in ops),
        KNOWN_DEDUCTION_OWNER_M2='',FREELANCER_GROSS_M2=fl if fl is not None else ''))
w=csv.DictWriter(open(sys.argv[2],'w',newline=''),fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
# summaries
def rng(s):
    if isinstance(s,(int,float)): return (s,s)
    if ' .. ' not in s: return float(s),float(s)
    a,b=s.split(' .. '); return float(a),float(b)
S={}
for r in rows:
    fl=r['ROW'][:2] if r['KIND']!='SHAFT' else 'ST'
    grp=(fl,r['KIND'] if r['KIND']!='SHAFT' else 'DRY')
    s=S.setdefault(grp,dict(n=0,L=0,own=0,own_held=0,dlo=0,dhi=0,plhi=0,fl=0,ann=0))
    s['n']+=1; s['L']+=r['FACE_LENGTH_M']
    if isinstance(r['OWNER_GROSS_M2'],float): s['own']+=r['OWNER_GROSS_M2']
    else: s['own_held']+=1
    if r['DWG_GROSS_M2']!='HELD':
        a,b=rng(r['DWG_GROSS_M2']); s['dlo']+=a; s['dhi']+=b
        if r['DWG_PLASTER_GROSS_M2']: s['plhi']+=rng(r['DWG_PLASTER_GROSS_M2'])[1]
    if r['FREELANCER_GROSS_M2']!='': s['fl']+=float(r['FREELANCER_GROSS_M2'])
    if r['ZONE']=='GF_ANNEX' and isinstance(r['OWNER_GROSS_M2'],float): s['ann']+=r['OWNER_GROSS_M2']
json.dump({f"{k[0]}|{k[1]}":{kk:round(vv,3) for kk,vv in v.items()} for k,v in S.items()},open(sys.argv[3],'w'),indent=1)
for k,v in sorted(S.items()): print(k,{kk:round(vv,2) for kk,vv in v.items()})
