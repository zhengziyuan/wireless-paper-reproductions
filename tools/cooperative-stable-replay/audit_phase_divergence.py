"""Capture/replay the saved case047 first MR-TTS phase divergence, no solver.

Two actual fixed contexts and three stored phases are cross-evaluated with
independent MP80/100 formulas. This does not prove a basin cause or global
optimality, and never changes the original curve or historical failed flags.
"""
import argparse
from pathlib import Path
import time

import mpmath as mp
import numpy as np
from scipy.io import loadmat, savemat

from audit_native_case import channel_data, sequence, sha
from build_power_curve_views import read, require, state_array, write
import mp_phase_reference as ref


def cells(values):
    result=np.empty((1,len(values)),object)
    for i,value in enumerate(values):result[0,i]=value
    return result


def capture(legacy, native_path, output):
    require(not output.exists(), 'Preserve the previous witness')
    paths=[legacy/'actual-state.json',legacy/'actual-state.npz',native_path,legacy/'configuration.json']
    result=read(native_path);native_state=native_path.parent/result['state_recording']['filename'];paths.append(native_state)
    require(sha(native_state)==result['state_recording']['sha256'],'Actual native tape differs')
    before={str(p):sha(p) for p in paths}
    raw=read(paths[0])['cases'][0]
    with np.load(paths[1],allow_pickle=False) as arrays:
        def unpack(value):
            if isinstance(value,dict) and 'recorded_array' in value:return state_array(value,arrays)
            if isinstance(value,dict):return {k:unpack(v) for k,v in value.items()}
            if isinstance(value,list):return [unpack(v) for v in value]
            return value
        py=unpack(raw)
    native=loadmat(native_state,simplify_cells=True)['recording']
    scene=native['input']['configuration']['reported']
    require(tuple(int(scene[k]) for k in ('J','U','N','M'))==(3,2,16,25) and scene['kappa_leo_db']==0
            and read(legacy/'configuration.json')['reported']['interference_to_noise_ratio']==.12,
            'The diagnostic only supports the recorded full-dimension scene')
    np0=next(p for p in sequence(native['phase_endpoints']) if not p['vector_objective'] and bool(p['context']['tts']))
    pp0=next(p for p in py['phase_stages'] if p['original_FG_closure_context'].get('tts') is True)
    entry=next(b for b in py['boundary_calls'] if b['function']=='mr_two_stage' and b['original_inputs'][6])
    pc=pp0['original_FG_closure_context'];nc=np0['context']
    require(pc['mu']==nc['mu']==1 and np.array_equal(entry['original_inputs'][1],np0['initial_phi']),
            'The two first-stage starts and smoothing parameters must match exactly')
    require(np.asarray(nc['interferenceLimit']).reshape(-1).tolist()==[.12], 'Exact final original interference slot required')
    contexts=[]
    for label,c,phase in (('python',pc,pp0),('matlab',nc,np0)):
        contexts.append(dict(label=label,data=channel_data(c['data'],3,2,16,25),
            p0=np.asarray(c['p0']).reshape(3,2),mu=float(c['mu']),tts=True,
            interferenceLimit=np.asarray(c.get('interferenceLimit',c.get('interference_limit'))).reshape(-1),
            original_value=float(phase['original_final_fg_call']['original_value'] if label=='python' else phase['value']),
            original_gradient=np.asarray(phase['original_final_fg_call']['original_gradient'] if label=='python' else phase['gradient']).reshape(2,25)))
    phases=dict(initial=np.asarray(np0['initial_phi']),python=np.asarray(pp0['original_final_phi']),matlab=np.asarray(np0['final_phi']))
    output.mkdir(parents=True)
    matrix=output/'first-TTS-stage-actual-inputs-and-phases.mat'
    savemat(matrix,dict(witness=dict(contexts=cells(contexts),phases=phases)),do_compression=True,long_field_names=True)
    report=dict(scope='Two actual fixed contexts and identical initial/actual first MR-TTS phase endpoints, source case047 only',
        source_files_sha256=before,witness_sha256=sha(matrix),witness_file=matrix.name,
        capture_source_sha256=sha(Path(__file__)),initial_phase_bitwise_equal=True,
        phase_context_count=2,phase_count=3,original_first_phase_iterations=dict(python=pp0['original_phase_status']['iterations'],matlab=int(np0['status']['iterations'])),
        original_gradient_tolerance=1e-6,original_rmo_max_iterations=100000,
        new_optimizer_calls=0,full_case_or_cause_or_original_reference_pass=False,
        source_and_inputs_unchanged=before=={str(p):sha(p) for p in paths})
    require(report['source_and_inputs_unchanged'],'Input bytes changed during capture')
    write(output/'witness-index.json',report)
    return report


def load_witness(directory):
    index=read(directory/'witness-index.json');matrix=directory/index['witness_file']
    require(sha(matrix)==index['witness_sha256'],'Actual phase witness changed')
    return loadmat(matrix,simplify_cells=True)['witness'],index


def audit(directory,output):
    require(not output.exists(),'Preserve previous independent phase cross-evaluation')
    witness,index=load_witness(directory)
    paths=[directory/'witness-index.json',directory/index['witness_file'],Path(__file__),Path(ref.__file__)]
    before={str(p):sha(p) for p in paths};lanes={};numbers={};started=time.perf_counter()
    for digits in (80,100):
        rows=[];numeric=[]
        with mp.workdps(digits):
            for c in sequence(witness['contexts']):
                data=channel_data(c['data'],3,2,16,25);label=c['label']
                for phase_label in ('initial','python','matlab'):
                    phi=np.asarray(witness['phases'][phase_label]).reshape(2,25)
                    v=ref.FixedContext(data,phi,np.asarray(c['p0']).reshape(3,2),float(c['mu']),np.asarray(c['interferenceLimit']).reshape(-1),True).gradient()
                    grad=[z for row in v['complex_gradient'] for z in row]
                    own=label==phase_label;comparison=None
                    if own:
                        ge=max(abs(ref.scalar(actual)-expected) for actual,expected in zip(np.asarray(c['original_gradient']).reshape(-1),grad))
                        gp=all(abs(ref.scalar(actual)-expected)<=ref.real(1e-9)+ref.real(1e-10)*abs(expected) for actual,expected in zip(np.asarray(c['original_gradient']).reshape(-1),grad))
                        ve=abs(ref.real(c['original_value'])-v['criterion'])
                        comparison=dict(maximum_gradient_error=mp.nstr(ge,105),criterion_error=mp.nstr(ve,105),
                            fields_pass=bool(gp and ve<=ref.real(1e-9)+ref.real(1e-10)*abs(v['criterion'])),
                            strict_original_gradient_stop_pass=bool(v['norm']<ref.real(1e-6)))
                    row=dict(context=label,phase=phase_label,criterion=mp.nstr(v['criterion'],105),
                        gradient_norm=mp.nstr(v['norm'],105),SINR=[mp.nstr(x,105) for x in v['sinr']],
                        full_complex_gradient=[dict(real=mp.nstr(z.real,105),imag=mp.nstr(z.imag,105)) for z in grad],own_saved_fields=comparison)
                    rows.append(row);numeric.extend([v['criterion'],v['norm'],*v['sinr'],*grad])
        lanes[str(digits)]=rows;numbers[digits]=numeric
    with mp.workdps(110):
        gap=max(abs(a-b) for a,b in zip(numbers[80],numbers[100]));stable=gap<mp.mpf('1e-40')
        objective_gaps={label:mp.nstr(next(mp.mpf(r['criterion']) for r in lanes['100'] if r['context']==label and r['phase']=='python')-
            next(mp.mpf(r['criterion']) for r in lanes['100'] if r['context']==label and r['phase']=='matlab'),105) for label in ('python','matlab')}
    own=all(r['own_saved_fields']['fields_pass'] and r['own_saved_fields']['strict_original_gradient_stop_pass']
            for lane in lanes.values() for r in lane if r['own_saved_fields'] is not None)
    report=dict(scope='MP80/100 full50-coordinate cross-evaluation of both actual first MR-TTS phase endpoints under both saved contexts and identical initial phase',
        source_inputs_sha256=before,source_and_inputs_unchanged=before=={str(p):sha(p) for p in paths},
        precisions=[80,100],evaluations_per_precision=6,complex_gradient_coordinates_per_precision=300,
        all_original_own_context_fields_and_strict_stops_pass=own,maximum_crossprecision_difference=mp.nstr(gap,105),
        crossprecision_absolute_bound='1e-40',all_precision_checks_pass=bool(stable),
        higher_Python_endpoint_objective_minus_MATLAB_endpoint_at_same_fixed_context=objective_gaps,
        lanes=lanes,original_case_curve_values_replaced=False,
        unique_cause_basin_or_global_optimum_proved=False,new_optimization_or_MC_calls=0,
        original_reference_or_full_case_or_paper_pass=False,elapsed_seconds=time.perf_counter()-started)
    report['all_saved_phase_and_precision_checks_pass']=bool(own and stable and report['source_and_inputs_unchanged'])
    write(output,report)
    print({k:v for k,v in report.items() if k not in ('lanes','source_inputs_sha256')})
    return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='command',required=True)
    c=sub.add_parser('capture');c.add_argument('--legacy-python-directory',type=Path,required=True);c.add_argument('--native-result',type=Path,required=True);c.add_argument('--output-dir',type=Path,required=True)
    c=sub.add_parser('audit');c.add_argument('--directory',type=Path,required=True);c.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    if a.command=='capture':capture(a.legacy_python_directory,a.native_result,a.output_dir)
    elif not audit(a.directory,a.output)['all_saved_phase_and_precision_checks_pass']:raise SystemExit(1)
