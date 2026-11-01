"""Compare a synthetic MATLAB helper result with the Python helper.

No paper input, channel, physical solver, production admission or reference
figure is involved. The caller must supply an existing, uniquely created JSON.
"""
from __future__ import annotations
import importlib.util
import json
import math
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
HELPER = REPO / 'strict/rotatable-isac/isac_iota_update_v1.py'

CASES = [
    ([1.,2.],[1.,1.],1.5,'exact',None,None),
    ([1.,2.],[1.,1.],1.5,'safeguarded',.25,'synthetic epsilon'),
    ([1.,0.],[0.,1.],1.,'exact',None,None),
    ([1.,0.],[0.,1.],1.,'safeguarded',.5,'synthetic epsilon'),
    ([0.,0.],[1.,0.],1.,'exact',None,None),
    ([1.,2.],[0.,0.],1.,'exact',None,None),
    ([1.,2.],[1.,1.],1.,'safeguarded',None,None),
    ([1.,2.],[1.,1.],1.,'safeguarded',float('inf'),'synthetic epsilon'),
    ([1e-15,1.],[1.,0.],1.,'exact',None,None),
    ([-1.,1.],[1.,1.],1.,'exact',None,None),
    ([1.,2.],[1.,1.],1.,'exact',.1,'synthetic epsilon'),
]
NUMERIC_FIELDS = ('pattern_energy','overlap','desired_energy','previous_iota',
                  'new_iota','nmse_before','nmse_after')


def python_helper():
    spec = importlib.util.spec_from_file_location('_isac_iota_reference', HELPER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def check(payload):
    if (type(payload) is not dict or payload.get('schema') != 'ISAC_IOTA_SYNTHETIC_MATLAB_RESULTS_V1'
            or payload.get('case_count') != len(CASES) or payload.get('uses_paper_data') is not False
            or payload.get('scientific_acceptance') is not False):
        raise ValueError('invalid synthetic result envelope')
    rows=payload.get('results')
    if type(rows) is not list or len(rows)!=len(CASES):
        raise ValueError('invalid result list')
    helper=python_helper()
    report=[]
    for i, ((p,d,previous,mode,eps,src), native) in enumerate(zip(CASES,rows)):
        py=helper.analyze(p,d,previous_iota=previous,mode=mode,epsilon=eps,epsilon_source=src)
        if type(native) is not dict or native.get('status')!=py['status'] or native.get('mode')!=mode:
            raise ValueError(f'case {i}: status or mode differs')
        if native.get('full_scientific_acceptance') is not False or native.get('source_provenance_verified') is not False:
            raise ValueError(f'case {i}: boundary missing')
        if py['status']=='failed':
            if native.get('reason') != py.get('reason'):
                raise ValueError(f'case {i}: failure reason differs')
            report.append({'index':i,'status':'failed_as_expected','reason':py['reason']})
            continue
        max_abs=0.0
        for key in NUMERIC_FIELDS:
            a=py[key]; b=native.get(key)
            if type(b) not in (int,float) or not math.isfinite(b) or not math.isclose(a,b,rel_tol=5e-14,abs_tol=1e-300):
                raise ValueError(f'case {i}: numerical mismatch {key}')
            max_abs=max(max_abs,abs(a-b))
        if native.get('observed_change')!=py['observed_change']:
            raise ValueError(f'case {i}: change label differs')
        if mode=='safeguarded' and native.get('epsilon_addition_rounded_away')!=py['epsilon_addition_rounded_away']:
            raise ValueError(f'case {i}: epsilon rounding differs')
        report.append({'index':i,'status':'matched','max_absolute_difference':max_abs})
    return {'schema':'ISAC_IOTA_SYNTHETIC_CROSS_LANGUAGE_REVIEW_V1','cases':report,
            'matched_cases':sum(x['status']=='matched' for x in report),
            'matched_expected_failures':sum(x['status']=='failed_as_expected' for x in report),
            'is_original_paper_reproduction':False,'uses_real_saved_states':False,
            'source_provenance_verified':False,'full_scientific_acceptance':False}


def main():
    if len(sys.argv)!=2:
        raise SystemExit('usage: python compare_fixed_states.py synthetic-result.json')
    path=Path(sys.argv[1]); data=path.read_bytes()
    if len(data)>64*1024: raise ValueError('input cap exceeded')
    print(json.dumps(check(json.loads(data)),allow_nan=False,separators=(',',':')))


if __name__=='__main__': main()
