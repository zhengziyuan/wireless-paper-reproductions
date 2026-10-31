"""Independent all91 saved native/Python endpoints versus retained MP80 values."""
import argparse
from decimal import Decimal, localcontext
import hashlib
import json
from pathlib import Path
import numpy as np
from scipy.io import loadmat


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def decimal_checks(gradient, criterion, reference):
    rows=[]; values=[]
    coordinates=reference['all_coordinates']
    if gradient.shape!=(2,45) or [(r['user'],r['coordinate']) for r in coordinates]!=[(u,m) for u in range(2) for m in range(45)]:
        raise ValueError('All90 ordered complex gradient coordinates required')
    if not np.isfinite(gradient).all() or len(criterion)!=len(reference['MP80_criterion']):
        raise ValueError('Complete finite criterion and gradient required')
    with localcontext() as ctx:
        ctx.prec=110; square=Decimal(0)
        for r in coordinates:
            g=gradient[r['user'],r['coordinate']]
            gr=Decimal.from_float(float(g.real)); gi=Decimal.from_float(float(g.imag))
            rr=Decimal(r['MP80_complex_gradient']['real']); ri=Decimal(r['MP80_complex_gradient']['imag'])
            error=((gr-rr)**2+(gi-ri)**2).sqrt()
            allowance=Decimal.from_float(1e-9)+Decimal.from_float(1e-10)*(rr*rr+ri*ri).sqrt()
            square+=gr*gr+gi*gi
            rows.append(dict(user=r['user'],coordinate=r['coordinate'],absolute_error=str(error),allowance=str(allowance),passed=error<=allowance))
        for actual,ref in zip(criterion,reference['MP80_criterion']):
            actual=Decimal.from_float(float(actual)); ref=Decimal(ref)
            error=abs(actual-ref); allowance=Decimal.from_float(1e-9)+Decimal.from_float(1e-10)*abs(ref)
            values.append(dict(absolute_error=str(error),allowance=str(allowance),passed=error<=allowance))
        norm=square.sqrt(); stopped=norm<Decimal.from_float(1e-6)
    return dict(gradient=rows,criterion=values,gradient_norm=str(norm),original_strict_stop_pass=stopped,
                passed=stopped and all(r['passed'] for r in rows+values))


def python_input(x):
    """Explicit shapes of the full J3/U2/N16/M45/K1 fixture, including singleton K."""
    shapes=dict(d_mean=(3,2,16),d_var=(3,2),G_mean=(3,2,16,45),G_var=(3,2),
        r_mean=(2,45),r_var=(2,),gt_second=(3,1,16,16),geo_d_mean=(2,),geo_d_var=(2,),
        geo_G_mean=(2,45),geo_G_var=(2,))
    return {k:np.asarray(x.data[0,0].__dict__[k]).reshape(shape) for k,shape in shapes.items()}


def audit(fixture, references, output, native=None):
    if output.exists():raise FileExistsError('Preserve prior evidence')
    packet=json.loads(references.read_bytes())
    if sha(fixture)!=packet['fixture_sha256']:raise ValueError('Saved input fixture differs')
    expected=[(c,s) for c,n in ((56,46),(65,45)) for s in range(n)]
    if [(r['case'],r['phase_stage']) for r in packet['records']]!=expected:raise ValueError('All91 original endpoints required')
    inputs=loadmat(fixture,struct_as_record=False,squeeze_me=False)['stage_inputs']
    if inputs.shape!=(91,1):raise ValueError('Complete fixture required')
    native_values=None
    if native is not None:
        summary=json.loads((native/'summary.json').read_bytes())
        if not(summary['all91_returned'] and summary['source_and_input_unchanged'] and summary['RNG_unchanged']):raise ValueError('Native execution failed')
        if summary['fixture_SHA256']!=packet['fixture_sha256']:raise ValueError('Native input differs')
        native_values=loadmat(native/'native-all91-original-components.mat',struct_as_record=False,squeeze_me=False)['outputs']
        if native_values.shape!=(91,1):raise ValueError('Complete native output required')
    else:
        import sys
        sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"strict/cooperative-satcom"))
        from positive_wick import evaluate_ap,evaluate_mr
    rows=[]
    for i,ref in enumerate(packet['records']):
        x=inputs[i,0][0,0]; mode=''.join(x.mode.reshape(-1).tolist())
        if (int(x.case_ordinal[0,0]),int(x.phase_stage[0,0]),mode)!=(ref['case'],ref['phase_stage'],ref['mode']):raise ValueError('Stage identity differs')
        if native_values is not None:
            value=native_values[i,0][0,0]
            if ''.join(value.mode.reshape(-1).tolist())!=mode:raise ValueError('Native mode differs')
            gradient=value.gradient; criterion=value.criterion.reshape(-1)
        else:
            data=python_input(x)
            if mode=='ap':value=evaluate_ap(data,x.phi,x.W)
            else:value=evaluate_mr(data,x.phi,x.p,float(x.smoothing[0,0]),x.limit.reshape(-1),mode=='mr_tts')
            gradient=value['gradient']; criterion=np.atleast_1d(value['criterion'])
        result=decimal_checks(gradient,criterion,ref)
        rows.append(dict(case=ref['case'],phase_stage=ref['phase_stage'],mode=mode,**result))
    production=Path(__file__).resolve().parents[2]/'strict/cooperative-satcom'
    provider=production/('evaluate_positive_wick.m' if native is not None else 'positive_wick.py')
    if native is not None and sha(provider)!=summary['provider_SHA256']:raise ValueError('Native provider differs from executed source')
    result=dict(scope='All91 saved fullsize endpoint criteria and8190 complex gradients versus retained MP80; no new optimizer',
        language='MATLAB' if native is not None else 'Python',fixture_sha256=sha(fixture),references_sha256=sha(references),
        evaluator_sha256=sha(provider),
        native_output_sha256=sha(native/'native-all91-original-components.mat') if native is not None else None,
        stages=91,gradient_coordinates=8190,all_endpoint_checks_pass=all(r['passed'] for r in rows),
        maximum_gradient_absolute_error=max(float(g['absolute_error']) for r in rows for g in r['gradient']),
        maximum_criterion_absolute_error=max(float(g['absolute_error']) for r in rows for g in r['criterion']),
        maximum_gradient_norm=max(float(r['gradient_norm']) for r in rows),records=rows,
        tolerance_or_original_stopping_rule_changed=False,new_optimization_or_new_MC_or_new_MP_reference=False,
        complete183_optimization_or_original_reference_pass=False)
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    print(json.dumps({k:result[k] for k in ('language','stages','gradient_coordinates','all_endpoint_checks_pass','maximum_gradient_absolute_error','maximum_criterion_absolute_error','maximum_gradient_norm')}))
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--fixture',type=Path,required=True)
    p.add_argument('--references',type=Path,required=True);p.add_argument('--native-dir',type=Path)
    p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    if not audit(a.fixture,a.references,a.output,a.native_dir)['all_endpoint_checks_pass']:raise SystemExit(1)
