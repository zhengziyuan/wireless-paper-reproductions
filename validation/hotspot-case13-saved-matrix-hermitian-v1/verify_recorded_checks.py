"""Inspect retained Case 13 matrix-check records; no solver or input replay.

This checks record identities, status, rational encodings and counts only. It
does not independently reconstruct the matrices or prove the arithmetic.
"""
from fractions import Fraction
import json
from pathlib import Path

ORDINALS=(1327666,1327713,1327755,1327778,1327876,1327926,1327964,1328004)
QREF=(0,1,2,2,3,4,5,6)

def need(x,message):
    if x is not True:raise ValueError(message)

def fraction(o):
    need(type(o) is dict and set(o)=={'numerator','denominator'},'fraction shape')
    n,d=o['numerator'],o['denominator']
    need(type(n) is str and type(d) is str and len(n)<=2500 and len(d)<=2500,'fraction encoding')
    need(n.isascii() and d.isascii() and n.isdigit() and d.isdigit(),'nonnegative decimal fraction')
    n,d=int(n),int(d);need(d>0,'positive denominator')
    return Fraction(n,d)

def main():
    p=Path(__file__).with_name('recorded-matrix-checks.jsonl')
    raw=p.read_bytes();need(len(raw)<=512*1024 and raw.endswith(b'\n'),'bounded complete stream')
    lines=raw.splitlines();need(len(lines)==24 and all(len(x)<=16384 for x in lines),'23 records and terminal')
    rows=[json.loads(x) for x in lines]
    matrix=rows[:-1];end=rows[-1]
    need(all(x.get('kind')=='matrix' for x in matrix),'matrix records')
    need([r.get('user_one_based') for r in matrix[:15]]==list(range(1,16)) and
         all(r.get('matrix')=='Psi' for r in matrix[:15]),'15 shared Psi records')
    q=matrix[15:];need(all(r.get('matrix')=='Q' for r in q) and
        tuple(r.get('ordinal') for r in q)==ORDINALS and
        tuple(r.get('q_array_ref') for r in q)==QREF,'8 saved Q event records')
    need(all(r.get('status')=='psd_exact_hermitian_part' and
             r.get('positive_pivots_before_stop')==16 and r.get('witness') is None for r in matrix),
         'positive-pivot recorded status')
    keys=('max_abs_antihermitian_real_component','max_abs_antihermitian_imag_component')
    maxima={k:max(fraction(row[k]) for row in matrix) for k in keys}
    nonzero=lambda row:any(fraction(row[k])!=0 for k in keys)
    psi_nonzero=sum(nonzero(row) for row in matrix[:15])
    q_nonzero=sum(nonzero(row) for row in q)
    need(psi_nonzero==0 and q_nonzero==8,'group residual counts')
    need(end.get('kind')=='terminal' and end.get('completed') is True and
         end.get('records_completed')==23 and end.get('failure') is None and
         end.get('historical_source_authenticated') is False and
         end.get('full_physical_convergence_reference_or_paper_pass') is False,'terminal boundaries')
    print(json.dumps({'schema':'case13_saved_matrix_record_inspection_v1','records':len(matrix),
         'Psi_records':15,'Q_event_records':8,'positive_pivots_per_record':16,
         'Psi_nonzero_residual_records':psi_nonzero,'Q_nonzero_residual_records':q_nonzero,
         'max_real_antihermitian_component':str(maxima[keys[0]]),
         'max_imag_antihermitian_component':str(maxima[keys[1]]),
         'matrix_arithmetic_independently_recomputed':False,'historical_source_authenticated':False,
         'scientific_or_paper_pass':False},sort_keys=True))

if __name__=='__main__':main()
