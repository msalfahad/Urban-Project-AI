import sys,re,collections,json
import ezdxf
doc=ezdxf.readfile(sys.argv[1]); msp=doc.modelspace()
out=[]
def walk(ents,depth=0,xf=None):
    for e in ents:
        t=e.dxftype()
        if t in('TEXT','MTEXT','ATTRIB'):
            s=e.plain_text() if t=='MTEXT' else e.dxf.text
            p=e.dxf.insert
            out.append(dict(t=s,x=round(p.x/1000,3),y=round(p.y/1000,3),l=e.dxf.layer,r=round(getattr(e.dxf,'rotation',0) or 0,1),h=round((e.dxf.char_height if t=='MTEXT' else e.dxf.height)/1000,3)))
        elif t=='INSERT' and depth<8:
            try: walk(e.virtual_entities(),depth+1)
            except Exception as ex: pass
            for a in e.attribs: walk([a],depth+1)
walk(msp)
json.dump(out,open(sys.argv[2],'w'),ensure_ascii=False)
print(len(out))
c=collections.Counter(o['l'] for o in out);print(c.most_common(30))
