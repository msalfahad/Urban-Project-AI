"""TRACE REVIEW UI (§26) - a self-contained HTML page over the frozen register.

Layered overlays with per-claim-type and per-status toggles, click-to-
inspect, zoom and pan, and a processed <-> original coordinate readout
from each trace's stored ORIGINAL_PAGE_COORDINATE_TRANSFORM. Only text
labels and their leaders move (greedy collision avoidance); every trace
geometry is drawn exactly where the reader stored it. The page reads
nothing back and writes nothing: it is a viewer.

The output lives with the other artifacts (gitignored client data); this
generator is the tracked deliverable.

    python3 -m research.qs_wall_treatment_01.review_ui
"""

from __future__ import annotations

import base64
import hashlib
import json
from pathlib import Path

from research.qs_wall_treatment_01 import protocol as P

KEEP = ("TRACE_ID", "CASE_ID", "SHEET_ID", "CLAIM_TYPE", "EFFECTIVE_CLAIM_TYPE",
        "DESCRIPTION", "NOTES", "PIXEL_BBOX", "PIXEL_POINT", "PIXEL_POLYLINE",
        "PIXEL_POLYGON", "TEXT_BBOX", "DIMENSION_LINE_TRACE", "EXTENSION_LINE_A",
        "EXTENSION_LINE_B", "LEADER_TRACE", "SUPPORTED_BY", "HOSTED_IN",
        "VALUE_M", "VALUES_M", "LENGTH_M", "VISUAL_TRACE_STATUS", "GEOMETRY_STATUS",
        "IDENTITY_STATUS", "DIMENSION_STATUS", "TREATMENT_STATUS",
        "PARAMETER_STATUS", "TRACE_RECORD_STATUS", "TRACE_LOCATABILITY_STATUS",
        "ORIGINAL_PDF_PAGE", "ORIGINAL_PAGE_COORDINATE_TRANSFORM")

HTML = r"""<!doctype html>
<html><head><meta charset="utf-8"><title>P7757 trace review</title>
<style>
body{margin:0;font:13px system-ui,sans-serif;background:#1b1d22;color:#e8e8e8;display:flex;height:100vh}
#side{width:360px;overflow:auto;padding:10px;border-right:1px solid #444;background:#24262c}
#main{flex:1;position:relative;overflow:hidden}
canvas{position:absolute;left:0;top:0;cursor:crosshair}
h3{margin:8px 0 4px;font-size:13px;color:#9cf}
label{display:block;margin:2px 0;cursor:pointer}
select{width:100%;margin:4px 0}
#info{font-size:12px;white-space:pre-wrap;background:#15161a;padding:8px;border-radius:4px;max-height:40vh;overflow:auto}
.sw{display:inline-block;width:12px;height:12px;margin-right:6px;vertical-align:middle;border-radius:2px}
#coords{position:absolute;right:8px;top:8px;background:#000a;padding:6px 8px;border-radius:4px;font-size:12px}
small{color:#aaa}
</style></head><body>
<div id="side">
<h3>Case / sheet</h3>
<select id="case"></select><select id="sheet"></select>
<h3>Layers by claim type</h3><div id="types"></div>
<h3>Layers by trace status</h3><div id="statuses"></div>
<label><input type="checkbox" id="labels" checked> labels (labels move; geometry never)</label>
<label><input type="checkbox" id="dims" checked> dimension geometry (text box, dimension line, extension lines)</label>
<h3>Selected trace</h3><div id="info">click a trace</div>
<h3>Related</h3><div id="rel"><small>overlap relations and dimension owner records appear here</small></div>
<p><small>Source: frozen TRACE_REGISTER (sha256 %REGSHA%). Viewer only - nothing is edited.</small></p>
</div>
<div id="main"><canvas id="c"></canvas><div id="coords">processed: - / original page: -</div></div>
<script>
const DATA=%DATA%;
const COLORS={WALL_SEGMENT:'#ff5252',PARAPET:'#ff9800',BALUSTRADE:'#ffeb3b',COLUMN:'#e040fb',GLAZING:'#40c4ff',DOOR:'#69f0ae',WINDOW:'#69f0ae',OPEN_EDGE:'#8bc34a',UNRESOLVED_FEATURE:'#bdbdbd',STAIR:'#ce93d8',ROOM_IDENTITY:'#fff176',LEVEL_MARK:'#80deea',PRINTED_DIMENSION:'#f48fb1',HEIGHT_DIMENSION:'#f06292',SECTION_REFERENCE:'#a1887f',ELEVATION_REFERENCE:'#a1887f',VERTICAL_RELATION:'#b0bec5',CROSS_SHEET_RELATION:'#b0bec5'};
const STATUS_DASH={TRACE_ESTABLISHED:[],TRACE_PROVISIONAL:[8,4],TRACE_AMBIGUOUS:[3,3],TRACE_NOT_ESTABLISHED:[1,4]};
let cur={case:null,sheet:null},img=null,view={s:0.5,x:0,y:0},sel=null,drag=null;
const cv=document.getElementById('c'),ctx=cv.getContext('2d');
const $=id=>document.getElementById(id);
function traces(){return DATA.traces.filter(t=>t.CASE_ID===cur.case&&t.SHEET_ID===cur.sheet);}
function init(){
 const cases=[...new Set(DATA.traces.map(t=>t.CASE_ID))];
 $('case').innerHTML=cases.map(c=>`<option>${c}</option>`).join('');
 const types=[...new Set(DATA.traces.map(t=>t.EFFECTIVE_CLAIM_TYPE))].sort();
 $('types').innerHTML=types.map(t=>`<label><input type="checkbox" data-type="${t}" checked><span class="sw" style="background:${COLORS[t]||'#fff'}"></span>${t}</label>`).join('');
 const sts=Object.keys(STATUS_DASH);
 $('statuses').innerHTML=sts.map(s=>`<label><input type="checkbox" data-status="${s}" checked>${s}</label>`).join('');
 $('case').onchange=()=>{cur.case=$('case').value;fillSheets();};
 $('sheet').onchange=()=>{cur.sheet=$('sheet').value;loadImg();};
 document.querySelectorAll('#side input').forEach(i=>i.addEventListener('change',draw));
 cur.case=cases[0];fillSheets();
 window.onresize=resize;resize();
 cv.onwheel=e=>{e.preventDefault();const k=e.deltaY<0?1.15:1/1.15;const mx=e.offsetX,my=e.offsetY;view.x=mx-(mx-view.x)*k;view.y=my-(my-view.y)*k;view.s*=k;draw();};
 cv.onmousedown=e=>{drag={x:e.offsetX,y:e.offsetY,vx:view.x,vy:view.y,moved:false};};
 cv.onmousemove=e=>{if(drag){const dx=e.offsetX-drag.x,dy=e.offsetY-drag.y;if(Math.abs(dx)+Math.abs(dy)>3)drag.moved=true;view.x=drag.vx+dx;view.y=drag.vy+dy;draw();}
   const p=toProc(e.offsetX,e.offsetY);$('coords').textContent=`processed: ${p[0].toFixed(0)}, ${p[1].toFixed(0)} / original page: ${orig(p)}`;};
 cv.onmouseup=e=>{if(drag&&!drag.moved)pick(toProc(e.offsetX,e.offsetY));drag=null;};
}
function fillSheets(){const sh=[...new Set(DATA.traces.filter(t=>t.CASE_ID===cur.case).map(t=>t.SHEET_ID))];
 $('sheet').innerHTML=sh.map(s=>`<option>${s}</option>`).join('');cur.sheet=sh[0];loadImg();}
function loadImg(){const key=cur.case+'/'+cur.sheet;img=new Image();img.onload=()=>{view={s:Math.min(cv.width/img.width,cv.height/img.height),x:0,y:0};draw();};img.src='data:image/jpeg;base64,'+DATA.images[key];sel=null;}
function resize(){cv.width=$('main').clientWidth;cv.height=$('main').clientHeight;draw();}
function toScreen(x,y){return [x*view.s+view.x,y*view.s+view.y];}
function toProc(sx,sy){return [(sx-view.x)/view.s,(sy-view.y)/view.s];}
function orig(p){const t=traces()[0];if(!t||!t.ORIGINAL_PAGE_COORDINATE_TRANSFORM)return '-';const T=t.ORIGINAL_PAGE_COORDINATE_TRANSFORM;
 const xr=p[0]/T.scale+T.trim_x0,yr=p[1]/T.scale+T.trim_y0;return `x=${((T.W_orig-1)-yr).toFixed(0)}, y=${xr.toFixed(0)} (page ${t.ORIGINAL_PDF_PAGE})`;}
function on(sel_,attr,val){const el=document.querySelector(`${sel_}[data-${attr}="${val}"]`);return !el||el.checked;}
function geoms(t){const g=[];if(t.PIXEL_POLYGON)g.push({k:'poly',p:t.PIXEL_POLYGON,close:true});if(t.PIXEL_POLYLINE)g.push({k:'poly',p:t.PIXEL_POLYLINE});
 if(t.PIXEL_BBOX)g.push({k:'box',p:t.PIXEL_BBOX});if(t.PIXEL_POINT)g.push({k:'pt',p:t.PIXEL_POINT});
 if($('dims').checked){if(t.TEXT_BBOX)g.push({k:'box',p:t.TEXT_BBOX,thin:true});if(t.DIMENSION_LINE_TRACE)g.push({k:'poly',p:t.DIMENSION_LINE_TRACE,thin:true});
  if(t.EXTENSION_LINE_A)g.push({k:'poly',p:t.EXTENSION_LINE_A,thin:true});if(t.EXTENSION_LINE_B)g.push({k:'poly',p:t.EXTENSION_LINE_B,thin:true});if(t.LEADER_TRACE)g.push({k:'poly',p:t.LEADER_TRACE,thin:true});}
 return g;}
function anchor(t){const g=geoms(t)[0];if(!g)return null;if(g.k==='pt')return g.p;if(g.k==='box')return [(g.p[0]+g.p[2])/2,g.p[1]];const p=g.p;return p[Math.floor(p.length/2)];}
function draw(){ctx.clearRect(0,0,cv.width,cv.height);if(!img)return;ctx.save();ctx.setTransform(view.s,0,0,view.s,view.x,view.y);ctx.drawImage(img,0,0);ctx.restore();
 const placed=[];
 for(const t of traces()){if(!on('#types input','type',t.EFFECTIVE_CLAIM_TYPE)||!on('#statuses input','status',t.VISUAL_TRACE_STATUS))continue;
  const col=COLORS[t.EFFECTIVE_CLAIM_TYPE]||'#fff';const isSel=sel&&sel.TRACE_ID===t.TRACE_ID;
  for(const g of geoms(t)){ctx.strokeStyle=isSel?'#fff':col;ctx.lineWidth=(g.thin?1:2)*(isSel?2:1);ctx.setLineDash(STATUS_DASH[t.VISUAL_TRACE_STATUS]||[]);ctx.beginPath();
   if(g.k==='poly'){g.p.forEach((q,i)=>{const s=toScreen(q[0],q[1]);i?ctx.lineTo(s[0],s[1]):ctx.moveTo(s[0],s[1]);});if(g.close)ctx.closePath();ctx.stroke();}
   else if(g.k==='box'){const a=toScreen(g.p[0],g.p[1]),b=toScreen(g.p[2],g.p[3]);ctx.strokeRect(a[0],a[1],b[0]-a[0],b[1]-a[1]);}
   else{const s=toScreen(g.p[0],g.p[1]);ctx.arc(s[0],s[1],5,0,7);ctx.stroke();}}
  ctx.setLineDash([]);
  if($('labels').checked){const a=anchor(t);if(!a)continue;let s=toScreen(a[0],a[1]);let lx=s[0]+6,ly=s[1]-6;const w=ctx.measureText(t.TRACE_ID).width+6,h=12;
   let tries=0;while(placed.some(b=>lx<b.x+b.w&&lx+w>b.x&&ly-h<b.y+b.h&&ly>b.y)&&tries<30){ly+=h+2;tries++;}
   placed.push({x:lx,y:ly-h,w:w,h:h});
   if(tries>0){ctx.strokeStyle='#888';ctx.lineWidth=1;ctx.beginPath();ctx.moveTo(s[0],s[1]);ctx.lineTo(lx,ly);ctx.stroke();}
   ctx.fillStyle='#000a';ctx.fillRect(lx-2,ly-h,w,h+2);ctx.fillStyle=col;ctx.font='11px monospace';ctx.fillText(t.TRACE_ID,lx,ly-2);}}
}
function distPoly(p,pts,close){let d=1e9;const n=pts.length;for(let i=0;i<n-(close?0:1);i++){const a=pts[i],b=pts[(i+1)%n];const vx=b[0]-a[0],vy=b[1]-a[1];const L=vx*vx+vy*vy||1;let u=((p[0]-a[0])*vx+(p[1]-a[1])*vy)/L;u=Math.max(0,Math.min(1,u));d=Math.min(d,Math.hypot(p[0]-a[0]-u*vx,p[1]-a[1]-u*vy));}return d;}
function pick(p){let best=null,bd=12/view.s;for(const t of traces()){if(!on('#types input','type',t.EFFECTIVE_CLAIM_TYPE)||!on('#statuses input','status',t.VISUAL_TRACE_STATUS))continue;
 for(const g of geoms(t)){let d;if(g.k==='poly')d=distPoly(p,g.p,g.close);else if(g.k==='box')d=distPoly(p,[[g.p[0],g.p[1]],[g.p[2],g.p[1]],[g.p[2],g.p[3]],[g.p[0],g.p[3]]],true);else d=Math.hypot(p[0]-g.p[0],p[1]-g.p[1]);if(d<bd){bd=d;best=t;}}}
 sel=best;draw();show();}
function show(){if(!sel){$('info').textContent='click a trace';return;}const t=sel;const keys=['TRACE_ID','EFFECTIVE_CLAIM_TYPE','VISUAL_TRACE_STATUS','GEOMETRY_STATUS','IDENTITY_STATUS','DIMENSION_STATUS','TREATMENT_STATUS','PARAMETER_STATUS','TRACE_LOCATABILITY_STATUS','VALUE_M','LENGTH_M','SUPPORTED_BY','HOSTED_IN','ORIGINAL_PDF_PAGE'];
 $('info').textContent=keys.filter(k=>t[k]!==undefined&&t[k]!==null).map(k=>`${k}: ${JSON.stringify(t[k])}`).join('\n')+'\n\n'+(t.DESCRIPTION||'')+(t.NOTES?'\n\nNOTES: '+t.NOTES:'');
 const rel=(DATA.overlaps[t.CASE_ID]||[]).filter(r=>r.A===t.TRACE_ID||r.B===t.TRACE_ID).map(r=>`${r.A} x ${r.B}: ${r.OVERLAP_RELATION}${r.JUNCTION_LIKE?' (junction-like)':''}`);
 const own=(DATA.owners[t.CASE_ID]||[]).filter(o=>o.TRACE_ID===t.TRACE_ID).map(o=>`DIMENSION_OWNER_STATUS: ${o.DIMENSION_OWNER_STATUS} -> ${JSON.stringify(o.OWNER_OBJECTS)} (text read: ${o.TEXT_READ_STATUS})`);
 const obj=(DATA.objects[t.CASE_ID]||[]).filter(o=>o.TRACE_ID===t.TRACE_ID).map(o=>`PHYSICAL_OBJECT: ${o.PHYSICAL_OBJECT_ID} | MATERIAL_ROLE: ${o.MATERIAL_ROLE} (${o.ROLE_ASSIGNED_BY}) | contributes: ${o.TRADE_CONTRIBUTION_ROLE}`);
 $('rel').innerHTML='<pre style="white-space:pre-wrap;font-size:11px">'+[...obj,...own,...rel].join('\n')+'</pre>';}
init();
</script></body></html>
"""


def build() -> dict:
    reg_p = Path(P.TRACE_REGISTER)
    reg = json.loads(reg_p.read_text("utf-8"))
    out_dir = Path(P.OUT_DIR)
    ov = json.loads((out_dir / "OVERLAP_AUDIT.json").read_text("utf-8"))
    own = json.loads((out_dir / "DIMENSION_OWNER_REGISTER.json").read_text("utf-8"))
    traces = [{k: t.get(k) for k in KEEP if t.get(k) is not None} for t in reg["TRACES"]]
    images = {}
    for cid in P.CASES:
        for f in (Path(P.CASE_SANDBOX) / cid).glob("*.jpeg"):
            images[f"{cid}/{f.stem}"] = base64.b64encode(f.read_bytes()).decode()
    data = {
        "traces": traces, "images": images,
        "overlaps": {c: v["OVERLAP_RELATIONS"] for c, v in ov["PER_CASE"].items()},
        "objects": {c: v["PHYSICAL_OBJECTS"] for c, v in ov["PER_CASE"].items()},
        "owners": own["PER_CASE"],
    }
    html = HTML.replace("%DATA%", json.dumps(data, ensure_ascii=False)).replace(
        "%REGSHA%", hashlib.sha256(reg_p.read_bytes()).hexdigest()[:16])
    p = out_dir / "TRACE_REVIEW_UI.html"
    p.write_text(html, encoding="utf-8")
    return {"TRACE_REVIEW_UI_SHA256": hashlib.sha256(p.read_bytes()).hexdigest(),
            "SIZE_BYTES": p.stat().st_size, "TRACES": len(traces), "IMAGES": len(images)}


if __name__ == "__main__":
    print(json.dumps(build(), indent=2))
