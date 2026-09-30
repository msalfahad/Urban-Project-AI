"""Read-only defect-exposure census of a LibreDWG JSON decode.

Counts SOURCE CLASSES only (mirrored placements, OCS normals, base points,
MINSERT, XREF, skipped kinds). It never reads a quantity and nothing it
reports may set a tolerance, formula or digest precision.

Usage: python3 -m tests.r8_0.exposure_census <decode.json> [...]
"""
import json, collections, hashlib, sys
def census(p):
    raw=open(p,'rb').read(); d=json.loads(raw); objs=d['OBJECTS']
    H=lambda x: x[-1] if isinstance(x,list) and x else None
    bh={H(o.get('handle')):o for o in objs if o.get('object')=='BLOCK_HEADER' or o.get('type')==49}
    layers={H(o.get('handle')):o.get('name') for o in objs if o.get('object')=='LAYER' or o.get('type')==51}
    owned=collections.defaultdict(list); top=[]
    for o in objs:
        if 'entity' not in o or o.get('type') in (4,5): continue
        oh=H(o.get('ownerhandle')); name=str(bh.get(oh,{}).get('name','')) if oh in bh else None
        if name is None or name.upper()=='*MODEL_SPACE': top.append(o)
        elif name.upper().startswith('*PAPER'): continue
        else: owned[oh].append(o)
    C=collections.Counter(); arc_layers=collections.Counter(); ins_layers=collections.Counter()
    def walk(ents, sign, depth):
        for o in ents:
            t=o.get('type')
            if t in (7,8):
                sc=o.get('scale') or [1,1,1]; ns=sign*(1 if sc[0]*sc[1]>=0 else -1)
                C['INSERT_REALISED']+=1
                if ns<0: C['INSERT_REALISED_MIRRORED']+=1; ins_layers[layers.get(H(o.get('layer')))]+=1
                if depth<16: walk(owned.get(H(o.get('block_header')),[]), ns, depth+1)
            elif t==17:
                C['ARC_REALISED']+=1
                if sign<0: C['ARC_REALISED_IN_MIRRORED']+=1; arc_layers[layers.get(H(o.get('layer')))]+=1
            elif t==77:
                nb=sum(1 for b in (o.get('bulges') or []) if abs(b)>1e-12); C['BULGE_SPAN_REALISED']+=nb
                if sign<0: C['BULGE_SPAN_REALISED_IN_MIRRORED']+=nb
    walk(top,1,0)
    ents=[o for o in objs if 'entity' in o]
    tc=collections.Counter(o.get('type') for o in ents)
    def ocs_bad(o):
        e=o.get('extrusion')
        return isinstance(e,list) and len(e)==3 and (abs(e[0])>1e-12 or abs(e[1])>1e-12 or abs(e[2]-1)>1e-12)
    return {"source": p, "sha256_16": hashlib.sha256(raw).hexdigest()[:16], "INSUNITS": d.get('HEADER',{}).get('INSUNITS'),
        **dict(C), "MIRRORED_INSERTS_BY_LAYER": dict(ins_layers), "ARCS_IN_MIRRORED_BY_LAYER": dict(arc_layers),
        "ENTITIES_NON_DEFAULT_EXTRUSION": sum(1 for o in ents if ocs_bad(o)),
        "ENTITIES_EXTRUSION_UNREADABLE": sum(1 for o in ents if 'extrusion' in o and not (isinstance(o['extrusion'],list) and len(o['extrusion'])==3)),
        "BLOCK_HEADERS": len(bh), "BLOCK_BASE_POINT_NON_ZERO": sum(1 for o in bh.values() if o.get('base_pt') and any(abs(v)>1e-9 for v in o['base_pt'])),
        "XREF_BLOCK_HEADERS": sum(1 for o in bh.values() if o.get('blkisxref') or o.get('xrefoverlaid') or o.get('xref_pname')),
        "MINSERT": tc.get(8,0), "OLE2FRAME": tc.get(74,0), "ACAD_PROXY_ENTITY": tc.get(498,0),
        "CUSTOM_CLASS_ENTITIES": sum(v for k,v in tc.items() if isinstance(k,int) and k>=500),
        "ELLIPSE": tc.get(35,0), "SPLINE": tc.get(36,0), "MTEXT": tc.get(44,0),
        "DIMENSIONS": sum(tc.get(k,0) for k in (20,21,22,23,24,25,26)), "DIMENSION_LINEAR_ROTATED_TYPE": tc.get(21,0)}
if __name__=='__main__':
    out=[census(p) for p in sys.argv[1:]]
    print(json.dumps(out,indent=1))
