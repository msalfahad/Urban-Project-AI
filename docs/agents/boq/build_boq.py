import json,sys,collections
from openpyxl import Workbook
from openpyxl.styles import Font,PatternFill,Alignment,Border,Side
from openpyxl.utils import get_column_letter
m=json.load(open(sys.argv[1])); L=json.load(open(sys.argv[2])); out=sys.argv[3]; ver=L.get('candidate_version','ARCH_TAKEOFF_V3.0.x')
FILL=json.load(open(sys.argv[7])) if len(sys.argv)>7 else None
if FILL:  # apply a main-chat fix-row set as an overlay before aggregation (shows the 'after fill' state; labels kept)
    fr={r['line_id']:r for r in FILL['rows']}; applied=0
    for l in L['lines']:
        r=fr.get(l['line_id'])
        if not r: continue
        a=r['after']
        if 'net' in a: l['class']='RELEASED'; l['measured_net']=a['net']; l['held_low']=l['held_high']=None
        else: l['class']='HELD'; l['held_low']=a['low']; l['held_high']=a['high']
        l['fill_label']=r['label']; applied+=1
    ver=ver+' + '+FILL['schema'].replace('_V1','')+f' ({applied} rows)'
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

# Compare sheet: candidate vs freelancer per trade section (owner 2026-11-13: reference comparison, never verification)
if STMT and KEYMAP and BENCH:
    by_code=collections.defaultdict(lambda:dict(rel=0.0,lo=0.0,hi=0.0,nb=0,blank=0,lo1=0.0,n1=0,n=0))
    for l in L['lines']:
        if l['class']=='EXCLUDED': continue
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
