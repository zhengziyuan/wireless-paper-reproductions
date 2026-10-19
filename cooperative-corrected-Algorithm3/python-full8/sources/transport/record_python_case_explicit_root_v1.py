"""One complete original Python v3 case with read-only state/phase/QT recording.

Intended for the two preserved old failed audits, not a duplicate183 campaign.
All original eight chains, dimensions, controls and1000 moment draws remain.
Wrappers copy returned states/arguments without changing any numerical return.
"""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import sys
import time
import numpy as np
from scipy.io import savemat


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def cells(values):
    out=np.empty((1,len(values)),dtype=object)
    for i,value in enumerate(values):out[0,i]=value
    return out


def execute(configuration,output):
    if output.exists():raise FileExistsError('Preserve every prior original/corrected result')
    package=Path(_PORTABLE_EXPLICIT_BASE_ROOT);sys.path.insert(0,str(package))
    import run_cooperative_v3_configured as entry
    import algorithms as alg
    original=entry.original
    config=json.loads(configuration.read_bytes());settings=config['tuned_not_reported']
    assert settings['monte_carlo_realizations']==1000 and settings['rmo_max_iterations']==100000 and settings['gradient_tolerance']==1e-6
    entry._install_original_v3_controls()
    def identity():return dict(entry.actual_hashes(configuration),record_python_case_py=sha(Path(__file__)))
    before=identity();original.source_hashes=identity;original.unchanged=lambda old:old==identity()
    tape=dict(input={},final_states=[],phase_endpoints=[],QT_candidates=[]);phase_initial=None;ap_phi=None;power_call=0
    factory=original.make_scenario
    def scenario(c):
        data,power,limit=factory(c)
        tape['input']=copy.deepcopy(dict(configuration=c,data=data,power_limit=power,interference_limit=limit))
        return data,power,limit
    original.make_scenario=scenario
    no_ris=alg.ap_no_ris
    def ap_no_ris(*args,**kwargs):
        nonlocal phase_initial
        value=no_ris(*args,**kwargs);phase_initial=np.array(args[1],copy=True)
        tape['final_states'].append(dict(scheme='AP-NoRIS',W=np.array(value[0],copy=True),phi=phase_initial.copy(),no_ris=True))
        return value
    alg.ap_no_ris=ap_no_ris
    ao=alg.ap_ao
    def ap_ao(*args,**kwargs):
        nonlocal ap_phi
        value=ao(*args,**kwargs);ap_phi=np.array(value[0],copy=True)
        tape['final_states'].append(dict(scheme='AP-AO',W=np.array(value[1],copy=True),phi=ap_phi.copy(),no_ris=False))
        return value
    alg.ap_ao=ap_ao
    mr_power_original=alg.mr_power
    power_names=('MR-S-NoRIS','MR-S-PA','MR-S-TS','MR-TTS-NoRIS','MR-TTS-PA','MR-TTS-TS')
    def mr_power(*args,**kwargs):
        nonlocal power_call
        value=mr_power_original(*args,**kwargs);name=power_names[power_call];power_call+=1
        phase=phase_initial if name.endswith('NoRIS') else ap_phi
        tape['final_states'].append(dict(scheme=name,p=np.array(value[0],copy=True),phi=np.array(phase,copy=True),no_ris=name.endswith('NoRIS')))
        return value
    alg.mr_power=mr_power
    two_stage=alg.mr_two_stage
    def mr_two_stage(*args,**kwargs):
        value=two_stage(*args,**kwargs)
        assert tape['final_states'][-1]['scheme'].endswith('-TS')
        tape['final_states'][-1]['phi']=np.array(value[0],copy=True)
        assert np.array_equal(tape['final_states'][-1]['p'],value[1])
        return value
    alg.mr_two_stage=mr_two_stage
    phase_original=alg.rmo_ascent
    def rmo(phi,value_gradient,max_iterations,gradient_tolerance,vector_objective=False,status=None,increment=None):
        result=phase_original(phi,value_gradient,max_iterations,gradient_tolerance,vector_objective,status,increment)
        closure={name:cell.cell_contents for name,cell in zip(value_gradient.__code__.co_freevars,value_gradient.__closure__ or ())}
        if vector_objective:context=dict(data=closure['data'],W=closure['W'])
        else:context=dict(data=closure['data'],p0=closure['p0'],mu=closure['mu'],interferenceLimit=closure['interference_limit'],tts=closure['tts'])
        value,gradient=value_gradient(result[0])
        tape['phase_endpoints'].append(copy.deepcopy(dict(context=context,final_phi=result[0],gradient=gradient,value=value,
            vector_objective=bool(vector_objective),original_stop=status or {})))
        return result
    alg.rmo_ascent=rmo
    def record_qt(function,kind,count):
        def call(*args,**kwargs):
            candidate,info=function(*args,**kwargs)
            keep={key:info[key] for key in ('before','after','surrogate_minimum_sinr','solver_status','qt_bound_max_violation','qt_tightness_error')}
            tape['QT_candidates'].append(copy.deepcopy(dict(kind=kind,input=cells(args[:count]),candidate=candidate,info=keep)))
            return candidate,info
        return call
    alg.ap_qt_update=record_qt(alg.ap_qt_update,'ap_qt_update',7)
    alg.mr_qt_update=record_qt(alg.mr_qt_update,'mr_qt_update',8)
    output.mkdir(parents=True);started=time.perf_counter()
    (output/'execution-start.json').write_text(json.dumps(dict(scope='One cold original full8 Python case with equivalent positive-Wick phase evaluation and read-only recording',source_before=before,
        configuration_sha256=sha(configuration),original_controls=settings,new_full183_claimed=False),indent=2)+'\n',encoding='utf-8')
    try:result=original.full_run(config,'base',None)
    except BaseException as error:
        partial={**tape,'final_states':cells(tape['final_states']),'phase_endpoints':cells(tape['phase_endpoints']),'QT_candidates':cells(tape['QT_candidates'])}
        if tape['input']:savemat(output/'partial-actual-recording.mat',dict(recording=partial),do_compression=True,long_field_names=True)
        (output/'execution-error.json').write_text(json.dumps(dict(error_type=type(error).__name__,error=str(error),source_unchanged=before==identity(),full_case_pass=False),indent=2)+'\n',encoding='utf-8')
        raise
    assert before==identity() and len(tape['final_states'])==8 and power_call==6
    (output/'actual-result.json').write_text(json.dumps(result,indent=2,default=original.numerical_json)+'\n',encoding='utf-8')
    matrix=output/'actual-python-recording.mat'
    recording={**tape,'final_states':cells(tape['final_states']),'phase_endpoints':cells(tape['phase_endpoints']),'QT_candidates':cells(tape['QT_candidates'])}
    savemat(matrix,dict(recording=recording),do_compression=True,long_field_names=True)
    view=copy.deepcopy(result);point=view['results'][0]
    point['schemes']=[dict(scheme=name,**scheme) for name,scheme in point['schemes'].items()]
    view.update(scope='Actual Python numerical output in common saved-state container; not native MATLAB execution',language='python',
        state_recording=dict(filename=matrix.name,sha256=sha(matrix),final_scheme_states=8,phase_endpoints=len(tape['phase_endpoints']),QT_candidates=len(tape['QT_candidates'])),
        unchanged_original_result_sha256=sha(output/'actual-result.json'),recording_source_sha256=sha(Path(__file__)))
    (output/'case-python-recorded.json').write_text(json.dumps(view,indent=2,default=original.numerical_json)+'\n',encoding='utf-8')
    summary=dict(source_unchanged=before==identity(),elapsed_seconds=time.perf_counter()-started,original_checks=result['checks'],
        original_scope_success=result['overall_implemented_scope_success'],states=8,phase_endpoints=len(tape['phase_endpoints']),QT_candidates=len(tape['QT_candidates']),
        result_sha256=sha(output/'actual-result.json'),state_sha256=sha(matrix),independent_physics_or_full183_or_original_reference_pass=False)
    (output/'execution-summary.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(summary),flush=True)
    if not result['overall_implemented_scope_success']:raise SystemExit(1)
    return summary


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--configuration',type=Path,required=True);p.add_argument('--output-dir',type=Path,required=True);a=p.parse_args();execute(a.configuration,a.output_dir)
