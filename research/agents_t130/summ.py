import json,collections,sys
Q=("MEASURED","SOURCE_DERIVED","PROVISIONAL")
def summ(run):
    L=json.load(open(f"{run}/BOQ_LINES.json"))
    out=collections.defaultdict(lambda: {"n":0,"rel":0,"rel_qty":0.0,"held":0,"excl":0,"states":collections.Counter(),"unit":set(),"lo":0.0,"hi":0.0,"bounded":0})
    for x in L:
        o=out[x["item_code"]]; o["n"]+=1; o["unit"].add(x["unit"]); s=x["evidence_state"]; o["states"][s]+=1
        if s in Q and x.get("measured_net") is not None: o["rel"]+=1; o["rel_qty"]+=x["measured_net"]
        elif s in ("NOT_APPLICABLE_WITH_EVIDENCE","EXCLUDED_WITH_REASON"): o["excl"]+=1
        else:
            o["held"]+=1; b=x.get("bounded_range") or {}
            if b.get("low") is not None: o["bounded"]+=1; o["lo"]+=b["low"]; o["hi"]+=b.get("high") or 0
    return out
if __name__=="__main__":
    for run in sys.argv[1:]:
        print("==",run)
        for k,o in sorted(summ(run).items()):
            print(f"{k:28s} n={o['n']:4d} rel={o['rel']:4d} qty={o['rel_qty']:10.3f} {','.join(o['unit'])} held={o['held']:3d} bnd={o['bounded']} [{o['lo']:.2f}..{o['hi']:.2f}] excl={o['excl']} {dict(o['states'])}")
        c=json.load(open(f"{run}/COVERAGE.json")); print(c["summary"])
