import json,sys,collections
from openpyxl import Workbook
from openpyxl.styles import Font,PatternFill,Alignment,Border,Side
from openpyxl.utils import get_column_letter
m=json.load(open(sys.argv[1])); L=json.load(open(sys.argv[2])); out=sys.argv[3]; ver=L.get('candidate_version','ARCH_TAKEOFF_V3.0.x')
FILL=json.load(open(sys.argv[7])) if len(sys.argv)>7 else None
if FILL:  # apply a main-chat fix-row set as an overlay before aggregation (shows the 'after fill' state; labels kept)
    # T-796 R-T796-1: a row applies only where the index line still carries the row's 'before' state and no later
    # fill_basis; a newer wired value is never overridden (skips are printed to stderr with their reason)
    import importlib.util as _iu, pathlib as _pl
    _s=_iu.spec_from_file_location('boq_overlay',_pl.Path(__file__).resolve().parent/'overlay.py'); _O=_iu.module_from_spec(_s); _s.loader.exec_module(_O)
    _log=_O.apply_overlay(L['lines'],FILL); _sm=_O.summary(_log); applied=_sm.get('APPLY',0)
    for _e in _log:
        if _e['action'].startswith('SKIP'): print('OVERLAY SKIP',_e['action'],_e['line_id'],_e['item_code'],'index',_e['index'],'row',_e['row_after'],file=sys.stderr)
    print('OVERLAY',json.dumps(_sm),file=sys.stderr)
    ver=ver+' + '+FILL['schema'].replace('_V1','')+f' ({applied} rows applied, {sum(v for k,v in _sm.items() if k.startswith("SKIP"))} skipped as older than the index)'
STMT=json.load(open(sys.argv[4])) if len(sys.argv)>4 else None; KEYMAP=json.load(open(sys.argv[5])) if len(sys.argv)>5 else None; BENCH=json.load(open(sys.argv[6])) if len(sys.argv)>6 else None
fams={f['code']:f for f in m['families']}
ic={c:f['code'] for f in m['families'] for c in f.get('item_codes',[])}
agg=collections.OrderedDict()
for l in L['lines']:
    if l['class']=='EXCLUDED': continue
    k=(ic.get(l['item_code'],'REF'),l['item_code'],l['unit'])
    a=agg.setdefault(k,dict(rel=0.0,nrel=0,lo=0.0,hi=0.0,nb=0,n1=0,lo1=0.0,blank=0))
    if l['class']=='RELEASED': a['rel']+=l['measured_net'] or 0; a['nrel']+=1
    elif l['class']=='HELD':
        lo,hi=l['held_low'],l['held_high']
        if lo is None and hi is None: a['blank']+=1
        elif hi is None: a['n1']+=1; a['lo1']+=float(lo)
        else: a['nb']+=1; a['lo']+=float(lo); a['hi']+=float(hi)
def gkey(code): 
    if code=='REF': return (99,code)
    g,n=code[1:].split('-'); return (int(g),int(n))
F=Font(name='Arial',size=10); FB=Font(name='Arial',size=10,bold=True); FH=Font(name='Arial',size=10,bold=True,color='FFFFFF')
HF=PatternFill('solid',fgColor='1F4E78'); GF=PatternFill('solid',fgColor='D9E1F2'); YF=PatternFill('solid',fgColor='FFF2CC')
thin=Side(style='thin',color='BFBFBF'); BR=Border(top=thin,bottom=thin,left=thin,right=thin)
wb=Workbook(); ws=wb.active; ws.title='BOQ'
hdr=['Trade','Family','Item','البند','Item code','Unit','Calculated qty','Held range low','Held range high','Held lines (range)','Min-only lines','Min-only total (at least)','Blank held lines','Status','Note','Closest estimate','Estimate method']
ws.append(hdr)
for c in ws[1]: c.font=FH; c.fill=HF; c.alignment=Alignment(wrap_text=True,vertical='center'); c.border=BR
groups=collections.OrderedDict()
for k in sorted(agg,key=lambda k:(gkey(k[0]),k[1],k[2])): groups.setdefault(k[0],[]).append(k)
r=2
for fam,keys in groups.items():
    f=fams.get(fam); trade=f['group'] if f else 'Reference (not BOQ lines)'
    for k in keys:
        a=agg[k]
        status=('CALCULATED' if a['nrel'] and not(a['nb'] or a['n1'] or a['blank']) else 'PARTLY HELD' if a['nrel'] else 'HELD')
        note=''
        if fam.startswith('B11'): status='PARKED'; note='Rebar parked by owner decision 11 Nov: approximate tons at the end of the project.'
        if fam=='REF': status='REFERENCE'; note='Geometry reference, not a BOQ line.'
        mid=(a['lo']+a['hi'])/2 if a['nb'] else 0.0
        known=a['nrel']+a['nb']
        avg=(a['rel']+mid)/known if known else 0.0
        if fam.startswith('B11') or fam=='REF': est=None; meth='not estimated (parked / reference)'
        elif a['blank'] and not known: est=None; meth='NO BASIS on this villa: needs a default, a manual PDF read or an area allowance'
        else:
            est=a['rel']+mid+a['blank']*avg+a['lo1']
            parts=['measured']+(['range midpoints'] if a['nb'] else [])+([f"{a['blank']} blank lines x average of the measured lines ({avg:.3f})"] if a['blank'] else [])
            meth=' + '.join(parts) if (a['nb'] or a['blank']) else 'measured'
        ws.append([trade,fam,f['item_en'] if f else '',f.get('item_ar','') if f else '',k[1],k[2],round(a['rel'],3),round(a['lo'],3) if a['nb'] else None,round(a['hi'],3) if a['nb'] else None,a['nb'],a['n1'],round(a['lo1'],3) if a['n1'] else None,a['blank'],status,note,round(est,3) if est is not None else None,meth])
        r+=1
    if fam.startswith('B10'):
        pass
# safety allowance
ws.append(['B10 Concrete','B10-SAFETY','Safety allowance for ignored small pieces (< 0.1 m3 each)','احتياطي للكميات الصغيرة المهملة','SAFETY.CONC','m3',1.0,None,None,0,0,None,0,'OWNER RULE','Owner 13 Nov: max(1.0 m3, sum of ignored pieces); ignored register starts now, so 1.0 m3 applies.',1.0,'owner safety allowance'])
last=ws.max_row
for row in ws.iter_rows(min_row=2,max_row=last):
    for c in row: c.font=F; c.border=BR
    if row[13].value in('HELD','PARTLY HELD'): row[13].fill=YF
    if row[16].value and row[16].value.startswith('NO BASIS'): row[16].fill=PatternFill('solid',fgColor='F8CBAD')
    if row[13].value=='OWNER RULE': 
        for c in row: c.fill=GF
widths=[16,10,34,26,30,6,13,13,13,10,9,13,10,13,40,14,60]
for i,w in enumerate(widths,1): ws.column_dimensions[get_column_letter(i)].width=w
for col in 'GHILP':
    for c in ws[col][1:]: c.number_format='#,##0.00;-#,##0.00;-'
ws.freeze_panes='C2'; ws.auto_filter.ref=f"A1:Q{last}"
# Summary by trade x unit with formulas
s=wb.create_sheet('Summary',0)
s.append([f'Urban Projects trial BOQ, development villa, built from {ver} (not released). Ranges and blanks are never added into the calculated column.'])
s['A1'].font=FB
s.append([])
s.append(['Trade','Unit','Calculated qty','Held range low','Held range high','Min-only total (at least)','Blank held lines','Lines','Closest estimate','Measured share'])
for c in s[3]: c.font=FH; c.fill=HF; c.border=BR
pairs=sorted({(ws.cell(i,1).value,ws.cell(i,6).value) for i in range(2,last+1)},key=lambda p:(p[0].startswith('Ref'),int(p[0].split()[0][1:]) if p[0][0]=='B' else 99,p[1]))
for t,u in pairs:
    i=s.max_row+1
    cr=f"BOQ!$A$2:$A${last},$A{i},BOQ!$F$2:$F${last},$B{i}"
    s.append([t,u,f"=SUMIFS(BOQ!$G$2:$G${last},{cr})",f"=SUMIFS(BOQ!$H$2:$H${last},{cr})",f"=SUMIFS(BOQ!$I$2:$I${last},{cr})",f"=SUMIFS(BOQ!$L$2:$L${last},{cr})",f"=SUMIFS(BOQ!$M$2:$M${last},{cr})",f"=COUNTIFS({cr})",f"=SUMIFS(BOQ!$P$2:$P${last},{cr})",f"=IFERROR(C{i}/I{i},0)"])
for row in s.iter_rows(min_row=4,max_row=s.max_row):
    for c in row: c.font=F; c.border=BR
    for c in row[2:6]: c.number_format='#,##0.00;-#,##0.00;-'
    row[8].number_format='#,##0.00;-#,##0.00;-'; row[9].number_format='0%'
for i,w in enumerate([26,7,15,15,15,18,14,8,16,10],1): s.column_dimensions[get_column_letter(i)].width=w
# Missing families
mi=wb.create_sheet('Missing')
mi.append(['Family','Trade','Item','البند','Unit','Why missing','Source needed'])
for c in mi[1]: c.font=FH; c.fill=HF
present={k[0] for k in agg}
for f in m['families']:
    if f['code'] not in present:
        mi.append([f['code'],f['group'],f['item_en'],f.get('item_ar',''),f.get('unit',''),f.get('missing',''),f.get('source_needed','')])
for row in mi.iter_rows(min_row=2):
    for c in row: c.font=F
for i,w in enumerate([8,16,34,26,6,50,30],1): mi.column_dimensions[get_column_letter(i)].width=w

# Key quantities sheet (shape of the QS office samples, owner upload 2026-11-13) + plausibility ratios
def _agg(pred):
    t=dict(rel=0.0,lo=0.0,hi=0.0,blank=0,n=0)
    for l in L['lines']:
        if l['class']=='EXCLUDED' or not pred(l): continue
        t['n']+=1
        if l['class']=='RELEASED': t['rel']+=l['measured_net'] or 0
        elif l['class']=='HELD':
            if l['held_low'] is None and l['held_high'] is None: t['blank']+=1
            else: t['lo']+=float(l['held_low'] or 0); t['hi']+=float(l['held_high'] or l['held_low'] or 0)
    return t
KQ=[('Concrete (structural, all elements)','m3',lambda l:l['item_code'].startswith('STR.CONC')),
    ('Rebar (detailed takeoff only; parked, approximate tons at the end)','kg',lambda l:l['item_code']=='STR.REBAR'),
    ('Formwork','m2',lambda l:l['item_code'].startswith('STR.FORMWORK')),
    ('Blockwork walls (net)','m2',lambda l:l['item_code']=='MAS.BLOCK'),
    ('Blocks (black, count)','pcs',lambda l:l['item_code']=='MAS.UNITS.BLACK'),
    ('Block mortar','m3',lambda l:l['item_code'].startswith('MAS.MORTAR')),
    ('Floor finishes internal (porcelain + wet tile + marble)','m2',lambda l:l['item_code'] in ('FIN.FLOOR.PORCELAIN','FIN.FLOOR.WET_TILE','FIN.FLOOR.FINISH_HELD') or l['item_code'].startswith('FIN.MARBLE.') and l['unit']=='m2'),
    ('Wall tiles','m2',lambda l:l['item_code']=='FIN.WALL.TILE'),
    ('External floors (paving, porcelain, outdoor)','m2',lambda l:l['item_code'].startswith('EXT.FLOOR') or l['item_code']=='EXT.PAVING.INTERLOCK'),
    ('Skirting (floor + stair)','lm',lambda l:l['item_code']=='FIN.SKIRTING' or l['item_code'].startswith('FIN.STAIR.SKIRTING')),
    ('Plaster internal (dry rooms + wet-room backing + bands + reveals)','m2',lambda l:l['item_code']=='FIN.PLASTER' and l['unit']=='m2'),
    ('Plaster / render external (facade + plinth + fence)','m2',lambda l:l['item_code'] in ('FIN.EXT.FINISH','EXT.FENCE.PLASTER') or (l['item_code']=='ARCH.FACADE' and 'plinth' in str(l.get('element_id')))),
    ('Corners and edges (beads, paint edges, exterior edges)','lm',lambda l:l['item_code'] in ('FIN.PLASTER.BEAD','FIN.PAINT.EDGE','FIN.EXT.PAINT.EDGE')),
    ('Paint walls internal','m2',lambda l:l['item_code']=='FIN.PAINT'),
    ('Paint ceilings','m2',lambda l:l['item_code']=='FIN.PAINT.CEILING'),
    ('Ceilings (gypsum / decor)','m2',lambda l:l['item_code'] in ('FIN.CEILING','FIN.CEILING.BULKHEAD')),
    ('Waterproofing membranes (wet rooms + roofs + foundations + pool)','m2',lambda l:(l['item_code'].startswith('FIN.WP') or l['item_code'].startswith('WP.')) and l['unit']=='m2'),
    ('Roof layers (insulation + protection)','m2',lambda l:l['item_code'] in ('FIN.ROOF.INSULATION','FIN.ROOF.PROTECTION')),
    ('Earthworks excavation','m3',lambda l:l['item_code']=='STR.EARTH.EXCAVATION'),
    ('Earthworks backfill','m3',lambda l:l['item_code']=='STR.EARTH.BACKFILL'),
    ('Openings: windows','m2',lambda l:l['item_code']=='ARCH.WINDOW' and l['unit']=='m2'),
    ('Openings: doors (all kinds)','pcs',lambda l:l['item_code'].startswith('DOOR.') and l['unit']=='pcs'),
    ('Sanitary fixtures (count)','pcs',lambda l:l['item_code'].startswith('MEP.') or 'SANITARY' in l['item_code'])]
k=wb.create_sheet('Key quantities',1)
k.append([f'Key quantities of {ver} in the shape of the QS office samples (owner upload 2026-11-13). Calculated = measured or filled with a label; held = ranges; blank = still no figure. Nothing priced.']); k['A1'].font=FB
k.append([])
k.append(['Quantity','Unit','Calculated','Held low','Held high','Blank lines','Lines','Per m2 internal floor','Sample band (OUTPUT_FORMAT_REFERENCE.md)'])
for x in k[3]: x.font=FH; x.fill=HF; x.border=BR; x.alignment=Alignment(wrap_text=True,vertical='center')
floor=_agg(KQ[6][2])['rel'] or 1.0
BAND={'Concrete (structural, all elements)':'0.5 .. 0.9 m3/m2','Blockwork walls (net)':'2.5 .. 3.2','Plaster internal (dry rooms + wet-room backing + bands + reveals)':'with external: 5 .. 7','Paint walls internal':'3 .. 4 (walls + ceilings)','Corners and edges (beads, paint edges, exterior edges)':'about 2.5','Waterproofing membranes (wet rooms + roofs + foundations + pool)':'0.6 .. 0.9','Skirting (floor + stair)':'0.75 .. 1.0','Rebar (detailed takeoff only; parked, approximate tons at the end)':'120 .. 140 kg per m3 concrete (3 Kuwait villas)'}
for name,unit,pred in KQ:
    t=_agg(pred); i=k.max_row+1
    k.append([name,unit,round(t['rel'],2),round(t['lo'],2) if t['lo'] else None,round(t['hi'],2) if t['hi'] else None,t['blank'],t['n'],f"=IFERROR(C{i}/{floor:.4f},0)",BAND.get(name,'')])
k.append(['Rebar ratio check (detailed kg per m3 of calculated concrete)','kg/m3',f"=IFERROR(C5/C4,0)",None,None,None,None,None,'120 .. 140 expected; a low figure = the detailed takeoff is still partial'])
k.append(['REBAR BY RATIO (owner 2026-11-13: the BOQ figure; ESTIMATE) = concrete (calc + held mid) x 130 kg/m3','t',f"=ROUND((C4+(D4+E4)/2)*130/1000,2)",f"=ROUND((C4+D4)*120/1000,2)",f"=ROUND((C4+E4)*140/1000,2)",None,None,None,'three Kuwait villas 120 .. 140 kg/m3; the detailed takeoff (row above) continues as the parallel check and must converge on this'])
for rw in k.iter_rows(min_row=4,max_row=k.max_row):
    for x in rw: x.font=F; x.border=BR
    for x in rw[2:5]: x.number_format='#,##0.00;-#,##0.00;-'
    rw[7].number_format='0.00'
for i,w in enumerate([58,6,13,12,12,10,7,16,44],1): k.column_dimensions[get_column_letter(i)].width=w

# Cross-check sheet: our figure vs the owner's parallel run of the same engine (13 Nov 2026, "blind BOQ" PDF) vs the freelancer
XC=[('Concrete total (all elements)','m3',lambda l:l['item_code'].startswith('STR.CONC'),323.20,'+14.6..42.5 range',352.44),
    ('Blinding','m3',lambda l:l['item_code']=='STR.CONC.BLINDING',None,'7.28..16.89 range (footings only)',47.06),
    ('Footings','m3',lambda l:l['item_code']=='STR.CONC.FOOTING',66.26,'',77.63),
    ('Suspended beams','m3',lambda l:l['item_code']=='STR.CONC.BEAM',69.00,'+4.27..10.25 range',65.97),
    ('Suspended slabs','m3',lambda l:l['item_code']=='STR.CONC.SLAB',64.29,'',59.82),
    ('Rebar (detailed, t)','t',lambda l:l['item_code']=='STR.REBAR',16.39,'partial extract; see the ratio row in Key quantities (owner: ratio is the BOQ figure)',44.19),
    ('Blockwork net','m2',lambda l:l['item_code']=='MAS.BLOCK',1092.1,'wall band x height - openings, all walls',1260.7),
    ('Floor tiles internal (+ unallocated)','m2',lambda l:l['item_code'] in ('FIN.FLOOR.PORCELAIN','FIN.FLOOR.WET_TILE','FIN.FLOOR.FINISH_HELD') or l['item_code'].startswith('FIN.MARBLE.') and l['unit']=='m2',376.3,'254.8 + 121.5 unallocated',409.6),
    ('Skirting','lm',lambda l:l['item_code']=='FIN.SKIRTING',185.5,'',282.9),
    ('Wet-wall porcelain','m2',lambda l:l['item_code']=='FIN.WALL.TILE',308.3,'at 2.70 m (ours now at 3.00 m, owner 2026-11-13)',433.8),
    ('Wet floor membrane','m2',lambda l:l['item_code']=='FIN.WP.FLOOR',62.8,'',72.0),
    ('Roof membrane','m2',lambda l:l['item_code']=='FIN.WP.ROOF',138.6,'main roof +9.70 only',285.0),
    ('Windows area','m2',lambda l:l['item_code']=='ARCH.WINDOW' and l['unit']=='m2',48.7,'default heights',116.9),
    ('Internal dry plaster','m2',lambda l:l['item_code']=='FIN.PLASTER' and l['unit']=='m2',732.8,'clear height (lower than the owner rule)',1209.4),
    ('External render','m2',lambda l:l['item_code']=='FIN.EXT.FINISH' or (l['item_code']=='ARCH.FACADE' and 'plinth' in str(l.get('element_id'))),769.2,'primary facade, no plinth / parapets',1502.8),
    ('Internal wall paint','m2',lambda l:l['item_code']=='FIN.PAINT',553.8,'dry rooms only',1249.4)]
x=wb.create_sheet('Cross-check',2)
x.append([f'Three-way check: this workbook ({ver} with fills) vs the parallel run of the same engine on 13 Nov 2026 vs the freelancer. Nothing here is verified; a difference is a question, not an error.']); x['A1'].font=FB
x.append([])
x.append(['Item','Unit','Ours calculated','Ours held low','Ours held high','Ours blank lines','Parallel run 13 Nov','Parallel run note','Freelancer','Ours vs freelancer %','Parallel vs freelancer %'])
for c in x[3]: c.font=FH; c.fill=HF; c.border=BR; c.alignment=Alignment(wrap_text=True,vertical='center')
for name,unit,pred,par,note,fr in XC:
    t=_agg(pred); i=x.max_row+1; div=1000.0 if unit=='t' else 1.0
    x.append([name,unit,round(t['rel']/div,2),round(t['lo']/div,2) if t['lo'] else None,round(t['hi']/div,2) if t['hi'] else None,t['blank'],par,note,fr,f"=IFERROR((C{i}-I{i})/I{i},\"\")",f"=IFERROR((G{i}-I{i})/I{i},\"\")"])
for rw in x.iter_rows(min_row=4,max_row=x.max_row):
    for c in rw: c.font=F; c.border=BR
    for c in (rw[2],rw[3],rw[4],rw[6],rw[8]): c.number_format='#,##0.00;-#,##0.00;-'
    rw[9].number_format='0%'; rw[10].number_format='0%'
for i,w in enumerate([36,6,13,12,12,10,14,36,12,14,14],1): x.column_dimensions[get_column_letter(i)].width=w

# Compare sheet: candidate vs freelancer per trade section (owner 2026-11-13: reference comparison, never verification)
if STMT and KEYMAP and BENCH:
    by_code=collections.defaultdict(lambda:dict(rel=0.0,lo=0.0,hi=0.0,nb=0,blank=0,lo1=0.0,n1=0,n=0))
    for l in L['lines']:
        if l['class']=='EXCLUDED': continue
        if l['item_code']=='ARCH.FACADE' and 'plinth' not in str(l.get('element_id')): continue  # same faces as FIN.EXT.FINISH: count once (plinth only)
        a=by_code[(l['item_code'],l['unit'])]; a['n']+=1
        if l['class']=='RELEASED': a['rel']+=l['measured_net'] or 0
        elif l['class']=='HELD':
            lo,hi=l['held_low'],l['held_high']
            if lo is None and hi is None: a['blank']+=1
            elif hi is None: a['n1']+=1; a['lo1']+=float(lo)
            else: a['nb']+=1; a['lo']+=float(lo); a['hi']+=float(hi)
    AR_UNIT={'م2':'m2','م٢':'m2','م.ط':'lm','م.ط.':'lm','مط':'lm','م3':'m3','م٣':'m3','عدد':'pcs','طن':'t','كجم':'kg','كغ':'kg'}
    def eng(codes,unit):
        t=dict(rel=0.0,lo=0.0,hi=0.0,nb=0,blank=0,lo1=0.0,n1=0,n=0); t['units']=set()
        for c in codes:
            c=c.split(' ')[0]
            a=by_code.get((c,unit))
            if not a:  # the statement's unit can differ from the index unit (e.g. upturn lm vs m2): take the code's own unit and say so
                cands=[(k,v) for k,v in by_code.items() if k[0]==c]
                if cands: a=cands[0][1]; t['units'].add(cands[0][0][1])
            if a:
                for k in ('rel','lo','hi','nb','blank','lo1','n1','n'): t[k]+=a[k]
        return t
    bench={r['id']:r for r in BENCH['records']}
    c=wb.create_sheet('Compare',1)
    c.append([f'Candidate {ver} vs the freelancer workbooks (REFERENCE ONLY, never engineering verification; his own trade labels). Classes from the reconciled statement V12 (T-635): ENGINE_RIGHT = engine shown right by hand calculation, RULE_DIFFERENCE = his rule differs from the owner rule, HELD = engine lines still held, UNRESOLVED = not yet explained, ENGINE_WRONG = engine corrected.'])
    c['A1'].font=FB
    c.append([])
    c.append(['Section','Trade (freelancer label)','Unit','Item codes','Freelancer','Engine now: calculated','Engine now: held low','Engine now: held high','Engine now: min-only (at least)','Blank lines now','Difference (calc - freelancer)','% of freelancer (calc only)','Engine at statement V12','ENGINE_RIGHT','ENGINE_WRONG','RULE_DIFFERENCE','HELD (V12)','UNRESOLVED (V12)','Reading'])
    for x in c[3]: x.font=FH; x.fill=HF; x.border=BR; x.alignment=Alignment(wrap_text=True,vertical='center')
    secs=STMT['sections']; secs=list(secs.values()) if isinstance(secs,dict) else secs
    seen=set()
    def reading(ref,t,bc,unit=''):
        if ref is None: return 'no freelancer row'
        if t['blank'] or t['nb'] or t['n1']: 
            lo=t['rel']+t['lo']+t['lo1']; hi=t['rel']+t['hi']+t['lo1']
            return (f" [engine unit {'/'.join(sorted(t['units']))}: not like for like] " if t.get('units') else '')+f"engine {lo:,.1f} .. {hi:,.1f}+ against his {ref:,.1f}: " + ('inside the range' if lo<=ref<=hi*1.0001 else ('his figure above the range' if ref>hi else 'his figure below the range')) + ("; blank lines still open" if t['blank'] else '')
        d=t['rel']-ref
        return (f"{'engine higher' if d>0 else 'engine lower'} by {abs(d):,.1f} ({abs(d)/ref*100:.1f} %)" if ref else '')+(f" [engine unit {'/'.join(sorted(t['units']))}, his {unit}: not like for like]" if t.get('units') else '')
    for sct in secs:
        unit=sct['unit']; codes=[x.split(' ')[0] for x in sct['item_codes']]; seen.update(codes)
        ref=float(sct['freelancer_total']) if sct.get('freelancer_total') not in (None,'') else None
        t=eng(codes,unit); bc={k:float(v) for k,v in sct['by_class'].items()}
        diff=(t['rel']-ref) if ref is not None else None
        c.append([sct['section_id'],sct['trade'],unit,', '.join(codes),ref,round(t['rel'],2),round(t['lo'],2) if t['nb'] else None,round(t['hi'],2) if t['nb'] else None,round(t['lo1'],2) if t['n1'] else None,t['blank'],round(diff,2) if diff is not None else None,(round(diff/ref*100,1) if ref else None),float(sct['engine_valued']),bc.get('ENGINE_RIGHT'),bc.get('ENGINE_WRONG'),bc.get('RULE_DIFFERENCE'),bc.get('HELD'),bc.get('UNRESOLVED'),reading(ref,t,bc,unit)])
    for k in KEYMAP['keys']:
        codes=k['item_codes']
        if set(codes)<=seen: continue
        r=bench.get(k['reference_id']); unit=(k.get('reference_unit') or (AR_UNIT.get((r or {}).get('unit','').strip(),'') if r else '') or {'CONCRETE':'m3','DOORS':'pcs','WINDOWS':'pcs','FLOOR_AREA':'m2'}.get(k['trade'],'m2'))
        ref=float(r['qty']) if r and r.get('qty') is not None else None
        t=eng(codes,unit); diff=(t['rel']-ref) if ref is not None else None
        c.append([k['key'],k['trade']+' (key map T001C; '+(r['label_en'] if r else k['reference_id'])+')',unit,', '.join(codes),ref,round(t['rel'],2),round(t['lo'],2) if t['nb'] else None,round(t['hi'],2) if t['nb'] else None,round(t['lo1'],2) if t['n1'] else None,t['blank'],round(diff,2) if diff is not None else None,(round(diff/ref*100,1) if ref else None),None,None,None,None,None,None,reading(ref,t,{},unit)])
    for rw in c.iter_rows(min_row=4,max_row=c.max_row):
        for x in rw: x.font=F; x.border=BR
        for x in rw[4:18]: x.number_format='#,##0.00;-#,##0.00;-'
        rw[11].number_format='0.0;-0.0;-'
    for i,w in enumerate([20,34,6,34,12,13,12,12,13,8,14,11,13,11,11,13,11,12,60],1): c.column_dimensions[get_column_letter(i)].width=w
    c.freeze_panes='C4'

# Notes
n=wb.create_sheet('Notes')
for t in [f'Source: candidate line index {ver}, committed by the agent team; BOQ_FAMILY_MASTER 1.78.0 groups the item codes. NOT released; released default V2.9 + route G unchanged.',
 'Calculated qty = lines with a measured figure. Held range = lines bounded low .. high. Min-only = lines with only a lower bound (at least). Blank = held, no figure yet (cause on the board).',
 'Ranges, min-only and blank are never added into Calculated. A held line is never 0.',
 'Owner rule 13 Nov: concrete pieces below 0.1 m3 are not chased; one safety allowance line = max(1.0 m3, sum of ignored pieces).',
 'Owner rule 12 Nov: paint area = plaster area of the same faces minus the band above false ceilings and tiled faces; edges and corners in lm.',
 'Rebar parked (owner 11 Nov): detailed figure shown for information only; approximate tons at the end of the project.',
 'No pricing. Freelancer comparison is not in this workbook (reference only, kept apart).',
 'Missing sheet: BOQ families with no line in the candidate yet (MEP last).',
 'Closest estimate (owner 13 Nov: never stop; get as close as possible): measured + midpoint of each held range + each blank line valued at the average of the measured / ranged lines of the same item. Labelled ESTIMATE, never verified. It is replaced line by line as the team applies the company defaults, manual PDF reads and area allowances.',
 'Compare sheet: freelancer totals from the reconciled statement V12 (T-635) and the T001C key map / BENCHMARK_NORMALISED; engine now from this line index; classes as the Checker merged them at V12 (not recomputed). A difference is a reference comparison, never a verdict.',
 'NO BASIS rows: no measured line of that item exists on this villa; they get a default, a manual PDF read or an area-based allowance next.']:
    n.append([t]); n.cell(n.max_row,1).font=F
n.column_dimensions['A'].width=140
wb.save(out); print('rows',last-1,'pairs',len(pairs),'missing',mi.max_row-1)
