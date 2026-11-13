import json,sys,collections
from openpyxl import Workbook
from openpyxl.styles import Font,PatternFill,Alignment,Border,Side
from openpyxl.utils import get_column_letter
m=json.load(open(sys.argv[1])); L=json.load(open(sys.argv[2])); out=sys.argv[3]; ver=L.get('candidate_version','ARCH_TAKEOFF_V3.0.77')
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
hdr=['Trade','Family','Item','البند','Item code','Unit','Calculated qty','Held range low','Held range high','Held lines (range)','Min-only lines','Min-only total (at least)','Blank held lines','Status','Note']
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
        ws.append([trade,fam,f['item_en'] if f else '',f.get('item_ar','') if f else '',k[1],k[2],round(a['rel'],3),round(a['lo'],3) if a['nb'] else None,round(a['hi'],3) if a['nb'] else None,a['nb'],a['n1'],round(a['lo1'],3) if a['n1'] else None,a['blank'],status,note])
        r+=1
    if fam.startswith('B10'):
        pass
# safety allowance
ws.append(['B10 Concrete','B10-SAFETY','Safety allowance for ignored small pieces (< 0.1 m3 each)','احتياطي للكميات الصغيرة المهملة','SAFETY.CONC','m3',1.0,None,None,0,0,None,0,'OWNER RULE','Owner 13 Nov: max(1.0 m3, sum of ignored pieces); ignored register starts now, so 1.0 m3 applies.'])
last=ws.max_row
for row in ws.iter_rows(min_row=2,max_row=last):
    for c in row: c.font=F; c.border=BR
    if row[13].value in('HELD','PARTLY HELD'): row[13].fill=YF
    if row[13].value=='OWNER RULE': 
        for c in row: c.fill=GF
widths=[16,10,34,26,30,6,13,13,13,10,9,13,10,13,48]
for i,w in enumerate(widths,1): ws.column_dimensions[get_column_letter(i)].width=w
for col in 'GHIL':
    for c in ws[col][1:]: c.number_format='#,##0.00;-#,##0.00;-'
ws.freeze_panes='C2'; ws.auto_filter.ref=f"A1:O{last}"
# Summary by trade x unit with formulas
s=wb.create_sheet('Summary',0)
s.append([f'Urban Projects trial BOQ, development villa, built from {ver} (not released). Ranges and blanks are never added into the calculated column.'])
s['A1'].font=FB
s.append([])
s.append(['Trade','Unit','Calculated qty','Held range low','Held range high','Min-only total (at least)','Blank held lines','Lines'])
for c in s[3]: c.font=FH; c.fill=HF; c.border=BR
pairs=sorted({(ws.cell(i,1).value,ws.cell(i,6).value) for i in range(2,last+1)},key=lambda p:(p[0].startswith('Ref'),int(p[0].split()[0][1:]) if p[0][0]=='B' else 99,p[1]))
for t,u in pairs:
    i=s.max_row+1
    cr=f"BOQ!$A$2:$A${last},$A{i},BOQ!$F$2:$F${last},$B{i}"
    s.append([t,u,f"=SUMIFS(BOQ!$G$2:$G${last},{cr})",f"=SUMIFS(BOQ!$H$2:$H${last},{cr})",f"=SUMIFS(BOQ!$I$2:$I${last},{cr})",f"=SUMIFS(BOQ!$L$2:$L${last},{cr})",f"=SUMIFS(BOQ!$M$2:$M${last},{cr})",f"=COUNTIFS({cr})"])
for row in s.iter_rows(min_row=4,max_row=s.max_row):
    for c in row: c.font=F; c.border=BR
    for c in row[2:6]: c.number_format='#,##0.00;-#,##0.00;-'
for i,w in enumerate([26,7,15,15,15,18,14,8],1): s.column_dimensions[get_column_letter(i)].width=w
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
# Notes
n=wb.create_sheet('Notes')
for t in [f'Source: candidate line index {ver}, committed by the agent team; BOQ_FAMILY_MASTER 1.78.0 groups the item codes. NOT released; released default V2.9 + route G unchanged.',
 'Calculated qty = lines with a measured figure. Held range = lines bounded low .. high. Min-only = lines with only a lower bound (at least). Blank = held, no figure yet (cause on the board).',
 'Ranges, min-only and blank are never added into Calculated. A held line is never 0.',
 'Owner rule 13 Nov: concrete pieces below 0.1 m3 are not chased; one safety allowance line = max(1.0 m3, sum of ignored pieces).',
 'Owner rule 12 Nov: paint area = plaster area of the same faces minus the band above false ceilings and tiled faces; edges and corners in lm.',
 'Rebar parked (owner 11 Nov): detailed figure shown for information only; approximate tons at the end of the project.',
 'No pricing. Freelancer comparison is not in this workbook (reference only, kept apart).',
 'Missing sheet: BOQ families with no line in the candidate yet (MEP last).']:
    n.append([t]); n.cell(n.max_row,1).font=F
n.column_dimensions['A'].width=140
wb.save(out); print('rows',last-1,'pairs',len(pairs),'missing',mi.max_row-1)
