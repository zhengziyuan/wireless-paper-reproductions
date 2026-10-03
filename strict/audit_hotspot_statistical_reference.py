"""Read-only, unfitted comparison to all nine supplied Fig3-10 EPS curves.

This parser is deliberately specific to the author MATLAB EPS axes/legend.
It neither runs an optimizer nor supplies reference values to one. Unknown
layouts fail explicitly instead of guessing a transformation or fitting gain.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import re
import numpy as np

LABELS=[f'{name}_kS{beta}' for beta in (0,10,20) for name in ('AO','TwoStage','NoRIS')]
NUM=r'[+-]?(?:\d+(?:\.\d*)?|\.\d+)'


def extract(text):
    ticks=[int(v) for v in re.findall(r'\((\d+)\) t',text)]
    if ticks!=list(range(1,7))+list(range(2,14)):
        raise ValueError('Unsupported EPS tick layout; no fitted axis transformation')
    if any(text.count(f'({name}, ) t')!=3 for name in ('AO','Two-Stage','No-RIS')):
        raise ValueError('All nine original legends must be explicitly present')
    for beta in (1,10,100):
        if text.count(f'(={beta}) t')!=3:
            raise ValueError('Original linear-Rician legend groups changed')
    # Original axes: six HU ticks x=52:103.2:568 and y=2 at479,
    # y=13 at98, both verified from the numeric EPS axes, not curve fitting.
    if '52 479 M' not in text or '568 98 L' not in text:
        raise ValueError('Original EPS plot bounds changed')
    pattern=rf'N\s+({NUM})\s+({NUM})\s+M\s+((?:{NUM}\s+{NUM}\s+L\s+){{5}})S'
    lines=[]
    for match in re.finditer(pattern,text):
        points=[(float(match[1]),float(match[2]))]
        points.extend((float(a),float(b)) for a,b in re.findall(rf'({NUM})\s+({NUM})\s+L',match[3]))
        points=np.asarray(points)
        if np.allclose(points[:,0],52+103.2*np.arange(6),rtol=0,atol=1e-8):
            lines.append(points)
    if len(lines)!=9:
        raise ValueError('Exactly nine six-point original paths required; no omitted curves')
    return [dict(label=name,x=list(range(1,7)),y=(2+(479-line[:,1])*11/381).tolist(),
                 original_EPS_path_xy=line.tolist()) for name,line in zip(LABELS,lines)]


def compare(reference,computed):
    if computed.get('paper_id')!='hotspot-satcom' or computed.get('figure')!=10:
        raise ValueError('A computed complete Fig3-10, not a component, is required')
    if computed.get('full_execution_verified') is not True or len(computed.get('panels',[]))!=1:
        raise ValueError('All18 actual points must be verified before reference comparison')
    curves=computed['panels'][0]['curves']
    if len(curves)!=9 or {c['label'] for c in curves}!=set(LABELS):
        raise ValueError('All nine uniquely labelled computed curves required')
    errors=[]
    for ref in reference:
        item=next(c for c in curves if c['label']==ref['label'])
        if item['x']!=ref['x'] or len(item['y'])!=6 or not np.all(np.isfinite(item['y'])):
            raise ValueError('Exact original HU grid and finite values required; no interpolation')
        delta=np.asarray(item['y'])-np.asarray(ref['y'])
        errors.append(dict(label=ref['label'],x=ref['x'],reference_y=ref['y'],computed_y=item['y'],
                           signed_error=delta.tolist(),maximum_absolute_error=float(np.max(abs(delta))),
                           rmse=float(np.sqrt(np.mean(delta**2)))))
    return dict(scope='unfitted_all9_curves_all54_points_reference_comparison_NOT_figure_agreement_certificate',
                all_reference_curves_present=True,all54_points_compared=True,curve_fitting_used=False,
                simulation_used_reference_ordinates=False,original_curve_closeness_verified=False,
                acceptance_tolerance_invented=False,errors=errors,
                maximum_absolute_error=max(e['maximum_absolute_error'] for e in errors),
                EPS_coordinate_rounding_y_resolution=11/381*0.001,
                hotspot_HU_pair_distance_contract_declared=computed.get('hotspot_HU_pair_distance_contract_declared'),
                scenario_source_constraints_verified=computed.get('scenario_source_constraints_verified',False))


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--reference-eps',type=Path,required=True)
    p.add_argument('--computed',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();raw=a.reference_eps.read_bytes();computed_raw=a.computed.read_bytes()
    result=compare(extract(raw.decode('utf-8-sig')),json.loads(computed_raw))
    result['reference_EPS_sha256']=hashlib.sha256(raw).hexdigest()
    result['computed_curve_file_sha256']=hashlib.sha256(computed_raw).hexdigest()
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    print(json.dumps({k:result[k] for k in ('all54_points_compared','maximum_absolute_error','original_curve_closeness_verified')}))


if __name__=='__main__':main()
