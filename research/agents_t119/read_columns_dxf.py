"""T-119 hand-reading helper (research only): every S-COL* polyline (drawing metres) and every TEXT / MTEXT of a
structural DXF, blocks exploded to depth 6. Decides nothing. Usage: python -I read_columns_dxf.py <ST.dxf> <dump.json>"""
import sys,json,re
import ezdxf
doc=ezdxf.readfile(sys.argv[1]); msp=doc.modelspace()
R=[];T=[]
def walk(ents,d=0):
    for e in ents:
        t=e.dxftype()
        if t=='INSERT' and d<6:
            try: walk(list(e.virtual_entities()),d+1)
            except Exception: pass
            continue
        try: L=e.dxf.layer
        except: continue
        if t=='LWPOLYLINE' and L.startswith('S-COL'):
            pts=[(p[0]/1000,p[1]/1000) for p in e.get_points()]
            R.append(dict(layer=L,closed=bool(e.closed),pts=pts,d=d))
        elif t in('TEXT','MTEXT'):
            s=e.dxf.text if t=='TEXT' else e.text
            p=e.dxf.insert
            T.append(dict(s=s.strip(),x=p.x/1000,y=p.y/1000,layer=L,h=getattr(e.dxf,'height',0) or getattr(e.dxf,'char_height',0),rot=getattr(e.dxf,'rotation',0)))
walk(msp)
json.dump(dict(R=R,T=T),open(sys.argv[2],'w'))
print(len(R),len(T))
