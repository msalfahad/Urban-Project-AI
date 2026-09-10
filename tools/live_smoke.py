"""Usage: ANTHROPIC_API_KEY=... URBAN_SCRATCH=<dir with st_all_09.png + Alsenan_Quotation_AR.md> python3 -m tools.live_smoke
"""LIVE smoke test of every agent on real Urban Projects inputs. Cheap models for
chat/classification, reasoning models where it matters, vision for the drawing.
Writes results + timing + errors to smoke_results.json. Never prints secrets."""
import json, time, base64, os, sys, traceback
sys.path.insert(0,"/home/user/Urban-Project-AI")
import anthropic
from agents.base import anthropic_model
SP=os.environ.get("URBAN_SCRATCH","data/smoke")
client=anthropic.Anthropic()
CHEAP="claude-haiku-4-5-20251001"; MID="claude-sonnet-5"; TOP="claude-opus-5"
def m(model,effort=None):
    return lambda s,u: anthropic_model(s,u,model=model,effort=effort)
def vision(model, img_path):
    b64=base64.standard_b64encode(open(img_path,"rb").read()).decode()
    def f(system,user):
        r=client.messages.create(model=model,max_tokens=16000,output_config={"effort":"high"},system=system,
            messages=[{"role":"user","content":[{"type":"image","source":{"type":"base64","media_type":"image/png","data":b64}},{"type":"text","text":user}]}])
        return "".join(b.text for b in r.content if b.type=="text")
    return f
def asdict(o):
    if hasattr(o,"__dict__"): return {k:asdict(v) for k,v in o.__dict__.items()}
    if isinstance(o,list): return [asdict(x) for x in o]
    if isinstance(o,dict): return {k:asdict(v) for k,v in o.items()}
    return o
R={}
def step(key,model_name,fn):
    t=time.time()
    try:
        out=fn(); R[key]={"ok":True,"model":model_name,"secs":round(time.time()-t,1),"out":asdict(out)}
        print(f"✓ {key:8} {model_name:28} {R[key]['secs']:>6}s",flush=True)
    except Exception as e:
        R[key]={"ok":False,"model":model_name,"secs":round(time.time()-t,1),"error":f"{type(e).__name__}: {str(e)[:300]}"}
        print(f"✗ {key:8} {model_name:28} {R[key]['error'][:120]}",flush=True)

from agents.a1_extractor.schema import ExtractInput
from agents.a2_reviewer.agent import run as a2
from agents.a3_client.agent import run as a3; from agents.a3_client.schema import Message
from agents.a4_followup.agent import run as a4; from agents.a4_followup.schema import FollowupInput
from agents.a5_faq.agent import run as a5; from agents.a5_faq.schema import FAQInput
from agents.a6_planner.agent import run as a6; from agents.a6_planner.schema import PlanInput
from agents.a8_briefer.agent import run as a8; from agents.a8_briefer.schema import BriefInput
from agents.a9_orchestrator.agent import run as a9; from agents.a9_orchestrator.schema import Event
from agents.a10_content.agent import run as a10; from agents.a10_content.schema import ContentInput
from agents.a11_site_progress.agent import run as a11; from agents.a11_site_progress.schema import SiteInput
from agents.a12_call_summariser.agent import run as a12; from agents.a12_call_summariser.schema import CallInput
from agents.a13_contract_reader.agent import run as a13; from agents.a13_contract_reader.schema import ContractInput
from agents.a14_ig_analyst.agent import run as a14; from agents.a14_ig_analyst.schema import IGAnalysisInput
from agents.a15_marketing.agent import run as a15; from agents.a15_marketing.schema import MarketingInput
from agents.a16_post_designer.agent import run as a16; from agents.a16_post_designer.schema import PostBrief

# quick cheap ones first
step("a5",CHEAP,lambda: a5(FAQInput(question="كم تستغرق مدة بناء شاليه هيكل أسود ٤٠٠ متر؟",language="ar"),model=m(CHEAP)))
step("a3",CHEAP,lambda: a3(Message(text="السلام عليكم، عندي أرض بالخيران ٥٠٠ متر وأبي أبني شاليه دورين مع مسبح، هيكل أسود بس. كم تقريباً وكم المدة؟"),model=m(CHEAP)))
step("a4",CHEAP,lambda: a4(FollowupInput(days_silent=5,last_stage="awaiting_drawings",lead_summary="شاليه الخيران ٥٠٠م دورين مسبح، هيكل أسود — طلبنا المخططات",client_replied_since=False),model=m(CHEAP)))
step("a10",CHEAP,lambda: a10(ContentInput(topic="Alsenan Chalet — foundations poured this week (17 footings)",surface="feed",date="2026-09-12"),model=m(CHEAP)))
step("a11",CHEAP,lambda: a11(SiteInput(observation="Photo from Alsenan site: excavation complete, blinding concrete poured for footings F1–F8, steel cages for F9–F15 being fixed, no formwork yet. Water pooling near the pool pit.",timestamp="2026-09-10",known_activities=["excavation","blinding","footings","columns","ground beams"]),model=m(CHEAP)))
step("a12",CHEAP,lambda: a12(CallInput(transcript="العميل: أبي الشاليه يخلص قبل الصيف الجاي. الأسعار عندكم غالية شوي. المهندس: نقدر نبدأ الهيكل الأسود خلال أسبوعين إذا اعتمدتوا العرض. العميل: خلاص أرسل لي جدول الدفعات وأنا أشوف."),model=m(CHEAP)))
step("a9",CHEAP,lambda: a9(Event(type="quotation_ready",record={"project":"Alsenan Chalet","total_kwd":121626,"open_questions":4},state="awaiting_owner_approval"),model=m(CHEAP)))
step("a14",CHEAP,lambda: a14(IGAnalysisInput(period="last_30_days",account={"followers":4820,"reach":31200,"profile_visits":640,"website_taps":58},
   posts=[{"id":"p1","type":"reel","topic":"villa handover walkthrough","likes":412,"comments":38,"saves":71,"shares":54,"reach":9800,"posted":"2026-08-14 19:30"},
          {"id":"p2","type":"carousel","topic":"before/after kitchen","likes":268,"comments":21,"saves":95,"shares":12,"reach":6100,"posted":"2026-08-20 13:00"},
          {"id":"p3","type":"image","topic":"team at site","likes":96,"comments":4,"saves":3,"shares":2,"reach":2100,"posted":"2026-08-25 09:00"},
          {"id":"p4","type":"reel","topic":"concrete pour timelapse","likes":530,"comments":44,"saves":88,"shares":97,"reach":14200,"posted":"2026-09-02 20:15"}]),model=m(CHEAP)))
step("a16",CHEAP,lambda: a16(PostBrief(type="poll",topic="Which chalet façade style: modern white, stone, or wood accents?",goal="engagement + enquiries",cta="صوّت واكتب لنا",photo_refs=["alsenan_render.jpg"]),model=m(CHEAP)))
# reasoning
step("a6",MID,lambda: a6(PlanInput(contract_form="black_structure",area_m2=420,floors=2,pool=True,lift=False,notes="Khairan chalet, 17 footings, pool pit, dome roof detail"),model=m(MID,"medium")))
step("a13",MID,lambda: a13(ContractInput(text=open(f"{SP}/Alsenan_Quotation_AR.md",encoding="utf-8").read()[:9000]),model=m(MID,"medium")))
step("a8",MID,lambda: a8(BriefInput(period="weekly",snapshot={"projects":[{"name":"Alsenan Chalet","value_kwd":131221,"progress":0,"stage":"foundations"},{"name":"Fahad AlAsousi Apartment","value_kwd":19500,"progress":85,"remaining_kwd":2627},{"name":"Almasaad Villah","value_kwd":2773,"progress":0},{"name":"شاليه القديري","value_kwd":0,"progress":0,"stage":"planning"}],
   "quotes":[{"client":"Alsenan","total_kwd":121626,"status":"awaiting owner approval","open_items":4}],"leads":[{"source":"WhatsApp","summary":"Khairan chalet 500m2 2 floors pool"}],"alerts":["Firebase billing closed: project photos unavailable"]}),model=m(MID,"medium")))
step("a15",MID,lambda: a15(MarketingInput(date_range="Oct 2026",goal="more turnkey villa enquiries in Kuwait",analysis=R.get("a14",{}).get("out",{})),model=m(MID,"medium")))
# vision second reader on the real drawing
step("a2",TOP,lambda: a2(ExtractInput(drawing_number="ST7757",sheet="p9 — Schedule of Columns & Footings",revision="May 2026",trade="structure"),drawing_text="(image attached — read the schedules)",model=vision(TOP,f"{SP}/st_all_09.png")))
json.dump(R,open(f"{SP}/smoke_results.json","w"),ensure_ascii=False,indent=1)
ok=sum(1 for v in R.values() if v["ok"]); print(f"\nDONE: {ok}/{len(R)} agents passed live")
