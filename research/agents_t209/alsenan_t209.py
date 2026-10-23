"""T-209 runner for the development villa (Alsenan): wet-room wall tile m2 per room, owner manual method (A) and
drawing-derived method (B) side by side, the Q-48 rough-sum column, the freelancer reconstructed per room and the
reconciliation in units. Inputs: ALSENAN_T209_INPUT.json (lengths only, merged sources). Outputs: WET_WALL_TILES_T209.csv,
RECONCILIATION_T209.csv, summary.json. `--check` rebuilds in memory and compares with the committed files (exit 0 / 1)."""
from __future__ import annotations

import csv
import io
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import wet_wall_tiles as T                                               # noqa: E402

FL_H = 3.00
COLS = ['ROOM', 'NAME', 'ZONE', 'FACE_M', 'DOORS', 'WINDOWS',
        'A_H_M', 'A_GROSS_M2', 'A_DOORS_M2', 'A_WINDOWS_M2', 'A_NET_M2', 'A_NET_HI_M2', 'A_STATUS',
        'Q48_ROUGH_M2', 'OVER_DOOR_BAND_M2',
        'B_H_M', 'B_GROSS_M2', 'B_NET_M2', 'B_STATUS',
        'FL_LM', 'FL_M2', 'A_MINUS_FL_M2',
        'A_MORTAR_M3', 'A_CEMENT_BAGS_OWNER', 'A_SAND_M3_OWNER', 'A_ADHESIVE_BAGS', 'WINDOW_REVEAL_LM']


def fmt(v):
    if v is None:
        return ''
    if isinstance(v, float):
        return f'{v:.4f}'.rstrip('0').rstrip('.') if v != int(v) else f'{v:.1f}'
    return str(v)


def build():
    inp = json.loads((HERE / 'ALSENAN_T209_INPUT.json').read_text(encoding='utf-8'))
    rows, rec = [], []
    tot = {k: 0.0 for k in ('a_ok', 'a_held_candidate', 'b_ok_lo', 'b_ok_hi', 'fl', 'fl_matched', 'q48', 'over')}
    held_a, held_b = [], []
    for r in inp['rooms']:
        face = round(r['contour_m'] - r['open_m'], 4)
        Ha = r['owner_H']
        a = T.room_tile(face, Ha, r['doors'], r['windows'], r['open_m'])
        a_held = a['status'] == 'HELD' or r['owner_status'].startswith('HELD') or Ha is None
        q48 = T.q48_rough(face, Ha, r['doors'], r['windows']) if Ha is not None else None
        over = T.over_door_band(Ha, r['doors']) if Ha is not None else None
        bH = r['dwg_H']
        b_lo = T.room_tile(face, bH[0], r['doors'], r['windows']) if bH else None
        b_hi = T.room_tile(face, bH[1], r['doors'], r['windows']) if bH else None
        b_held = (not bH) or r['dwg_status'].startswith('HELD') or b_lo['status'] == 'HELD'
        fl_m2 = round(r['fl_lm'] * FL_H, 4) if r['fl_lm'] is not None else None
        a_net = a['net_lo'] if a['net_lo'] == a['net_hi'] else None
        mat = T.materials(a_net) if (a_net is not None) else None
        if any(w.get('sill') is None for w in r['windows']):
            reveal = None                       # a reveal of a window with no sill / head is HELD, never 0
        else:
            reveal = round(sum(2 * (w['head'] - w['sill']) + w['w'] for w in r['windows']), 4)
        rows.append(dict(
            ROOM=r['id'], NAME=r['name'], ZONE=r['zone'], FACE_M=face,
            DOORS='; '.join(f"{d['id']} {d['w']:.2f}" + (' (head 2.20 Q-55 C)' if d['fallback'] else ' (head not printed)')
                            for d in r['doors']),
            WINDOWS='; '.join(f"{w['id']} {w['w']:.2f} sill {fmt(w.get('sill'))} head {fmt(w.get('head'))}"
                              for w in r['windows']),
            A_H_M=Ha, A_GROSS_M2=a['gross'], A_DOORS_M2=a.get('doors_lo'), A_WINDOWS_M2=a.get('windows'),
            A_NET_M2=a['net_lo'], A_NET_HI_M2=a['net_hi'] if a['net_hi'] != a['net_lo'] else None,
            A_STATUS=(r['owner_status'] if r['owner_status'].startswith('HELD') else 'HELD: ' + (a['why'] or ''))
            if a_held else r['owner_status'],
            Q48_ROUGH_M2=q48, OVER_DOOR_BAND_M2=over,
            B_H_M=(f'{bH[0]:.2f} .. {bH[1]:.2f}' if bH else None),
            B_GROSS_M2=(f"{b_lo['gross']} .. {b_hi['gross']}" if bH else None),
            B_NET_M2=(f"{b_lo['net_lo']} .. {b_hi['net_hi']}" if bH else None),
            B_STATUS=r['dwg_status'],
            FL_LM=r['fl_lm'], FL_M2=fl_m2,
            A_MINUS_FL_M2=(round(a_net - fl_m2, 4) if (a_net is not None and fl_m2 is not None) else None),
            A_MORTAR_M3=mat and mat['mortar_m3'], A_CEMENT_BAGS_OWNER=mat and mat['cement_bags_owner'],
            A_SAND_M3_OWNER=mat and mat['sand_m3_owner'], A_ADHESIVE_BAGS=mat and mat['adhesive_bags'],
            WINDOW_REVEAL_LM=reveal))
        if fl_m2 is not None:
            tot['fl'] += fl_m2
        if a_net is not None and not a_held:
            tot['a_ok'] += a_net
            tot['q48'] += q48
            tot['over'] += over
            if fl_m2 is not None:
                tot['fl_matched'] += fl_m2
                # reconciliation in units: freelancer -> length -> height -> doors -> windows -> own
                d_len = (face - r['fl_lm']) * FL_H
                d_h = face * (Ha - FL_H)
                d_doors = -a['doors_lo']
                d_win = -a['windows']
                rec.append(dict(ROOM=r['id'], FL_M2=fl_m2, LENGTH_M2=round(d_len, 4), HEIGHT_M2=round(d_h, 4),
                                DOORS_M2=round(d_doors, 4), WINDOWS_M2=round(d_win, 4),
                                OWN_A_M2=a_net, RESIDUAL_M2=round(a_net - (fl_m2 + d_len + d_h + d_doors + d_win), 6),
                                CAUSES=f"length {face:.3f} vs his {r['fl_lm']:.2f} lm; height {Ha:.2f} vs his 3.00; "
                                       f"openings not deducted by him"))
        else:
            held_a.append(r['id'])
            if a['gross'] is not None:
                tot['a_held_candidate'] += a['net_lo']
        if bH and not b_held:
            tot['b_ok_lo'] += b_lo['net_lo']
            tot['b_ok_hi'] += b_hi['net_hi']
        else:
            held_b.append(r['id'])
    ok_rooms = [x['ROOM'] for x in rows if x['ROOM'] not in held_a]
    mat_tot = T.materials(tot['a_ok'])
    summary = dict(
        task='T-209', rooms=len(rows),
        method_a=dict(rooms_assumed_owner_approved=ok_rooms, net_m2=round(tot['a_ok'], 4),
                      held_rooms=held_a, held_candidate_net_m2=round(tot['a_held_candidate'], 4),
                      q48_rough_m2=round(tot['q48'], 4), over_door_band_m2=round(tot['over'], 4)),
        method_b=dict(drawing_confirmed_rooms=[x['ROOM'] for x in rows if x['ROOM'] not in held_b],
                      net_m2=[round(tot['b_ok_lo'], 4), round(tot['b_ok_hi'], 4)], held_rooms=held_b),
        freelancer=dict(total_m2=round(tot['fl'], 4), stated_total_m2=inp['freelancer_total_m2'],
                        matched_rooms_m2=round(tot['fl_matched'], 4)),
        like_for_like=dict(rooms=len(rec), own_a_m2=round(sum(x['OWN_A_M2'] for x in rec), 4),
                           freelancer_m2=round(sum(x['FL_M2'] for x in rec), 4),
                           length_m2=round(sum(x['LENGTH_M2'] for x in rec), 4),
                           height_m2=round(sum(x['HEIGHT_M2'] for x in rec), 4),
                           doors_m2=round(sum(x['DOORS_M2'] for x in rec), 4),
                           windows_m2=round(sum(x['WINDOWS_M2'] for x in rec), 4),
                           max_abs_residual_m2=max(abs(x['RESIDUAL_M2']) for x in rec)),
        materials_method_a=dict(mat_tot, cement_bags_owner_buy=T.buy(mat_tot['cement_bags_owner']),
                                cement_bags_owner_with_waste_buy=T.buy(mat_tot['cement_bags_owner_with_waste']),
                                adhesive_bags_buy=T.buy(mat_tot['adhesive_bags']),
                                status='PROVISIONAL (Q-45 B practice values; G4 owner 8 bags / 1.10 m3, theory beside)'))
    lf = summary['like_for_like']
    lf['diff_m2'] = round(lf['own_a_m2'] - lf['freelancer_m2'], 4)
    lf['diff_pct'] = round(100 * lf['diff_m2'] / lf['freelancer_m2'], 2)
    return rows, rec, summary


def to_csv(rows, cols):
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=cols, lineterminator='\n')
    w.writeheader()
    for r in rows:
        w.writerow({k: fmt(r.get(k)) for k in cols})
    return buf.getvalue()


REC_COLS = ['ROOM', 'FL_M2', 'LENGTH_M2', 'HEIGHT_M2', 'DOORS_M2', 'WINDOWS_M2', 'OWN_A_M2', 'RESIDUAL_M2', 'CAUSES']


def outputs():
    rows, rec, summary = build()
    return {'WET_WALL_TILES_T209.csv': to_csv(rows, COLS), 'RECONCILIATION_T209.csv': to_csv(rec, REC_COLS),
            'summary.json': json.dumps(summary, indent=1, ensure_ascii=False) + '\n'}


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    out = outputs()
    if '--check' in argv:
        bad = [n for n, t in out.items() if not (HERE / n).exists() or (HERE / n).read_text(encoding='utf-8') != t]
        print('T-209 check:', 'OK' if not bad else f'DIFFERS {bad}')
        return 1 if bad else 0
    for n, t in out.items():
        (HERE / n).write_text(t, encoding='utf-8')
    print(json.dumps(json.loads(out['summary.json']), indent=1))
    return 0


if __name__ == '__main__':
    sys.exit(main())
