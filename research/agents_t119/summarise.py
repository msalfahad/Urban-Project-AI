"""T-119: totals, causes and re-add checks from COLUMNS_TO_CONTROLLING_MEMBER.csv (research only)."""
import csv, json, sys
R = list(csv.DictReader(open(sys.argv[1])))
ENGINE = {'GF': 20.247, '1F': 10.668, '2F': 5.796}            # released route G run B (T-100 / T-044 table), total 36.711
SCOPE = {'GF': 20.250, '1F': 10.248, '2F': 3.948}             # after T-126 scope (merged, opt-in), total 34.446
FREEL = {'GF': 17.438, '1F': 7.728, '2F': 3.381}              # freelancer rows (interval - 0.75), total 28.547
def f(r, k): return float(r[k])
# r2: status = WORKFLOW_CONTROLS section 5 evidence status; hold_cause = why a row is HELD (empty when DRAWING-CONFIRMED)
CAUSES = ['DRAWING-CONFIRMED', 'FRAMING_MEMBER_HELD_D_SETTLED', 'FRAMING_MEMBER_HELD_D_OPEN', 'UPSTAND_DOWNSTAND_D44',
          'LEVEL_Q54B', 'CONFLICT_SECTION_D16']
def cause(r):
    assert r['status'] in ('DRAWING-CONFIRMED', 'HELD') and r['release'] == 'NOT RELEASED', r['id']
    assert (r['status'] == 'DRAWING-CONFIRMED') == (r['hold_cause'] == ''), r['id']
    return r['hold_cause'] or 'DRAWING-CONFIRMED'
out = {}
for sh in ['GF', '1F', '2F', 'ALL']:
    L = [r for r in R if sh == 'ALL' or r['storey'] == sh]
    d = {'columns': len(L)}
    for c in CAUSES:
        M = [r for r in L if cause(r) == c]
        d[c] = dict(n=len(M), col_lo=round(sum(f(r, 'col_m3_lo') for r in M), 3), col_hi=round(sum(f(r, 'col_m3_hi') for r in M), 3),
                    joint_lo=round(sum(f(r, 'joint_m3_lo') for r in M), 3), joint_hi=round(sum(f(r, 'joint_m3_hi') for r in M), 3))
    d['hand_rule_lo'] = round(sum(f(r, 'col_m3_lo') for r in L), 3); d['hand_rule_hi'] = round(sum(f(r, 'col_m3_hi') for r in L), 3)
    d['joint_lo'] = round(sum(f(r, 'joint_m3_lo') for r in L), 3); d['joint_hi'] = round(sum(f(r, 'joint_m3_hi') for r in L), 3)
    d['full_interval'] = round(sum(f(r, 'full_interval_m3') for r in L), 3)
    keys = ['GF', '1F', '2F'] if sh == 'ALL' else [sh]
    for nm, ref in (('engine_released', ENGINE), ('engine_after_T126_scope', SCOPE), ('freelancer', FREEL)):
        v = round(sum(ref[k] for k in keys), 3)
        d[nm] = dict(m3=v, hand_minus_lo=round(d['hand_rule_lo'] - v, 3), hand_minus_hi=round(d['hand_rule_hi'] - v, 3),
                     pct_lo=round(100 * (d['hand_rule_lo'] - v) / v, 2), pct_hi=round(100 * (d['hand_rule_hi'] - v) / v, 2))
    # where the column height differs from the freelancer's uniform interval - 0.75
    # r2: a D_ctrl range (D-44) gives the two readings: lo = deepest D (downstand), hi = shallowest D (upstand)
    d['A_x_(0.75-Dctrl)'] = dict(at_deepest_D=round(sum(f(r, 'A_m2') * (0.75 - float(r['D_ctrl'].split('..')[-1])) for r in L if r['D_ctrl']), 3),
                                 at_shallowest_D=round(sum(f(r, 'A_m2') * (0.75 - float(r['D_ctrl'].split('..')[0])) for r in L if r['D_ctrl']), 3))
    out[sh] = d
# re-add checks
for r in R:
    A, iv = f(r, 'A_m2'), f(r, 'interval')
    D = float(r['D_ctrl'].split('..')[0])
    h = float(r['height'].split('..')[-1])
    assert abs(h - (iv - D)) < 1e-6, r['id']
    if r['hold_cause'] != 'CONFLICT_SECTION_D16':
        assert abs(f(r, 'col_m3_hi') - A * h) < 1e-3, r['id']
        t = r['slab_t']
        if t.startswith('none'): assert abs(f(r, 'col_m3_hi') + f(r, 'joint_m3_hi') - A * iv) < 1e-3, r['id']
        elif '..' not in t:
            assert abs(f(r, 'col_m3_hi') + f(r, 'joint_m3_lo') + A * float(t) - A * iv) < 1e-3, r['id']
a = out['ALL']
assert abs(sum(out[s]['hand_rule_lo'] for s in ['GF', '1F', '2F']) - a['hand_rule_lo']) < 1e-6
assert sum(a[c]['n'] for c in CAUSES) == a['columns']
json.dump(out, open(sys.argv[2], 'w'), indent=1)
print(json.dumps(out, indent=1))
