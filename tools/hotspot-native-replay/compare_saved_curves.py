"""Unfitted all54 native points against the retained original-EPS extraction."""
import argparse
import json
from pathlib import Path
import sys
import numpy as np
from audit_saved_native import read,sha,write


def compare(native_path,python_path,reference_path,output):
    strict=Path(__file__).resolve().parents[2]/'strict';sys.path.insert(0,str(strict))
    from audit_hotspot_statistical_reference import compare as original_comparison
    native,python,stored=map(read,(native_path,python_path,reference_path))
    reference=[dict(label=row['label'],x=row['x'],y=row['reference_y']) for row in stored['errors']]
    result=original_comparison(reference,native)
    result.update(reference_provenance='Previously source-verified original EPS extraction retained in public evidence; no fresh EPS access claimed',
                  reference_EPS_sha256=stored['reference_EPS_sha256'],retained_reference_packet_sha256=sha(reference_path),
                  native_computed_curve_sha256=sha(native_path),python_computed_curve_sha256=sha(python_path))
    left={c['label']:c for c in native['panels'][0]['curves']};right={c['label']:c for c in python['panels'][0]['curves']}
    if left.keys()!=right.keys() or len(left)!=9:raise ValueError('All9 source curves required in both languages')
    differences=[]
    for label in left:
        a,b=left[label],right[label]
        if a['x']!=b['x'] or len(a['y'])!=6:raise ValueError('Original exact HU grid required')
        error=np.asarray(a['y'])-np.asarray(b['y'])
        differences.append(dict(label=label,x=a['x'],native_y=a['y'],python_y=b['y'],signed_difference=error.tolist(),maximum_absolute_difference=float(abs(error).max())))
    result['separate_converged_language_bank_differences']=differences
    result['maximum_native_vs_python_curve_difference']=max(r['maximum_absolute_difference'] for r in differences)
    result['identical_optimizer_initialization_and_MC_draws_claimed']=False
    result['same_nonconvex_endpoint_or_full_trajectory_parity_certified']=False
    if output.exists():raise ValueError('Preserve prior comparison')
    write(output,result);return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--native',type=Path,required=True)
    p.add_argument('--python',type=Path,required=True);p.add_argument('--reference-packet',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    r=compare(a.native,a.python,a.reference_packet,a.output)
    print(json.dumps({k:r[k] for k in ('all54_points_compared','maximum_absolute_error','maximum_native_vs_python_curve_difference','original_curve_closeness_verified')}))
