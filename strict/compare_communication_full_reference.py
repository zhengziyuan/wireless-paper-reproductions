"""Independent physical and original-vector comparison of a full Fig7 bank.

Reference ordinates never enter a solver. Two beam labels may be permuted, but
no phase, angle, spacing, gain or ordinate is fitted. This is one corrected-axis
figure, not a certificate for all paper figures or literal contradictory text.
"""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np

HERE=Path(__file__).resolve().parent
NUMERIC_ATOL=NUMERIC_RTOL=1e-10
REFERENCE_ABSOLUTE_GATE=1e-5  # linear SNR; 0.025 percent of the 0.04 peak


def require(value,message):
    if not value:raise ValueError(message)


def numeric(actual,expected,label):
    a,b=np.asarray(actual),np.asarray(expected)
    require(a.shape==b.shape and np.all(np.isfinite(a)) and np.all(np.isfinite(b)),label+' incomplete/nonfinite')
    require(np.all(abs(a-b)<=NUMERIC_ATOL+NUMERIC_RTOL*abs(b)),label+' fixed physical gate failed')
    return float(np.max(abs(a-b))) if a.size else 0.


def phases(value,key,count):
    v=value[key];z=np.asarray(v['real'],float).reshape(-1)+1j*np.asarray(v['imag'],float).reshape(-1)
    require(z.shape==(count,) and np.all(np.isfinite(z)),key+' full phase count required')
    require(np.all(abs(abs(z)-1)<=1e-10),key+' unit-modulus failed')
    return z


def pattern(state,baseline,azimuth):
    phi=phases(state,'phi',2);theta=phases(state,'theta',1 if baseline=='MIS' else 0)
    if baseline=='MIS':weights=np.column_stack(([phi[0]*theta[0],phi[1]],[phi[0],phi[1]*theta[0]]))
    else:weights=phi[:,None]
    az=np.deg2rad(np.asarray(azimuth,float))
    steering=np.column_stack((np.ones(len(az)),np.exp(1j*np.pi*np.sin(np.pi/4)*np.sin(az))))
    return .01*abs(steering@weights)**2


def compare(document,reference):
    require(document['paper_id']=='mis-communications' and document['figure']=='fig7'
        and document['full_figure_execution_complete'] is True and document['overall_full_success'] is True,
        'Actual complete successful Fig7 execution required')
    require(len(document['points'])==1,'Exactly one full Fig7 source scene required')
    settings=document['settings'];point=document['points'][0]
    require(settings['number_of_starts']==6000 and settings['rcg_max_iterations']==4000
        and settings['reference_snr']==.01 and settings['spacing_over_wavelength']==.5
        and settings['incidence_direction_cosines']==[0,0],'Complete disclosed bank/physical settings required')
    configuration=point['configuration']
    require(configuration['ms1']==[1,2] and configuration['ms2']==[1,1] and configuration['K']==4
        and configuration['source_ms1_shape']==[2,1]
        and configuration['source_correction_id']=='COMM-GEOMETRY-FIG7','Original dimensional domain and explicit axis erratum required')
    require(reference['paper_id']=='mis-communications' and reference['figure']==7
        and reference['data_kind']=='original_plot_vector_reference_NOT_simulation'
        and len(reference['curves'])==3,'Three authentic comparison-only vector paths required')
    checks=[];states={}
    for baseline,key in (('MIS','result'),('SMS','SMS')):
        run=point[key];summaries=run['all_start_summaries'];best=run['best_feasible']
        require(run['full_start_budget_execution_complete'] is True and run['overall_full_success'] is True
            and run['number_of_starts']==6000 and len(summaries)==6000
            and [s['start'] for s in summaries]==list(range(1,6001)), 'All6000 unique actual starts per baseline required')
        require(all(s['feasible'] is True and s['solver_status']['convergence_verified'] is True
            and np.isfinite(s['score']) for s in summaries),'No failed start deletion or false stop certificate')
        chosen=max(summaries,key=lambda s:s['score'])
        require(best['start']==chosen['start'] and best['score']==chosen['score'], 'Original first-tie best-feasible rule required')
        states[baseline]=best['state'];X=np.asarray(best['state']['X'],float)
        require(X.shape==(4,2 if baseline=='MIS' else 1) and np.all(np.isfinite(X))
            and np.min(X)>=-1e-10 and np.max(X)<=1+1e-10,'Complete feasible four-user scheduling required')
        numeric(X.sum(axis=1),np.ones(4),'schedule row sums')
        user_snr=pattern(states[baseline],baseline,[-60,-20,20,60])
        selected=np.argmax(X,axis=1);score=float(np.min(user_snr[np.arange(4),selected]))
        score_error=numeric(best['score'],score,'selected actual best score')
        numeric(best['metrics']['min_binary_snr'],score,'stored binary physical SNR')
        samples=point['beampattern_samples'] if baseline=='MIS' else run['beampattern_samples']
        numeric(samples['azimuth_deg'],np.arange(-90.,90.5,.5),'complete361-angle grid')
        grid_error=numeric(samples['pattern_snr'],pattern(states[baseline],baseline,samples['azimuth_deg']), 'all actual beam samples')
        numeric(samples['user_snr_by_pattern'],user_snr,'all user-by-pattern physical values')
        checks.append(dict(baseline=baseline,actual_starts=6000,all_stops_and_feasibility_passed=True,
            actual_selected_start=best['start'],fresh_physical_score=score,saved_score_error=score_error,
            all361_beam_samples_error=grid_error))
    curves=reference['curves'];require([c['label'] for c in curves]==['MIS pattern1','MIS pattern2','SMS'],'Original ordered legend paths required')
    for curve in curves:
        x,y=np.asarray(curve['x'],float),np.asarray(curve['y'],float)
        require(x.shape==y.shape==(360,) and np.all(np.isfinite(x)) and np.all(np.isfinite(y))
            and np.all(np.diff(x)>0) and abs(x[0]+90)<1e-3 and abs(x[-1]-90)<1e-3,'All360 original axis-calibrated samples required')
    assignments=[]
    for order in ((0,1),(1,0)):
        errors=[]
        for k in range(2):
            actual=pattern(states['MIS'],'MIS',curves[k]['x'])[:,order[k]]
            delta=actual-np.asarray(curves[k]['y'])
            errors.append(dict(original_label=curves[k]['label'],actual_position_index=order[k],
                maximum_absolute_error=float(np.max(abs(delta))),rmse=float(np.sqrt(np.mean(delta**2)))))
        assignments.append(dict(order=list(order),errors=errors,maximum_absolute_error=max(e['maximum_absolute_error'] for e in errors)))
    # Pure two-label relabeling only; actual state and displacement indices remain intact.
    selected=min(assignments,key=lambda a:a['maximum_absolute_error'])
    delta=pattern(states['SMS'],'SMS',curves[2]['x'])[:,0]-np.asarray(curves[2]['y'])
    sms_error=float(np.max(abs(delta)))
    maximum=max(selected['maximum_absolute_error'],sms_error)
    return dict(scope='one_actual12000_start_corrected_axis_Fig7_independent_physics_and_unfitted_all1080_vector_samples',
        original_reference_source_sha256=reference['source_sha256'],actual_physical_checks=checks,
        all12000_starts_individually_feasible_and_verified=True,all_actual_saved_beams_independently_verified=True,
        MIS_label_assignments=assignments,selected_original_label_to_actual_position_index=selected['order'],
        SMS_reference_error=dict(maximum_absolute_error=sms_error,rmse=float(np.sqrt(np.mean(delta**2)))),
        maximum_absolute_reference_error=maximum,predeclared_linear_SNR_reference_absolute_gate=REFERENCE_ABSOLUTE_GATE,
        all_three_corrected_axis_paths_close_under_declared_gate=maximum<=REFERENCE_ABSOLUTE_GATE,
        fitted_phases_angles_gain_spacing_or_reference_ordinates=False,production_solver_imported=False,
        literal2x1_source_text_recovered=False,publisher_erratum_or_all_paper_reproduction_claimed=False,
        original_figure_reproduction_certified=False)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--computed',type=Path,required=True);parser.add_argument('--reference',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    paths={'computed':args.computed,'reference':args.reference}
    raw={k:p.read_bytes() for k,p in paths.items()};source=Path(__file__);before=hashlib.sha256(source.read_bytes()).hexdigest()
    result=compare(json.loads(raw['computed']),json.loads(raw['reference']))
    require(before==hashlib.sha256(source.read_bytes()).hexdigest() and all(p.read_bytes()==raw[k] for k,p in paths.items()),'Actual independent evaluation inputs/source changed')
    result['input_file_sha256']={k:hashlib.sha256(v).hexdigest() for k,v in raw.items()}
    result['independent_evaluator_sha256']=before;result['independent_evaluation_inputs_and_source_unchanged']=True
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    print(json.dumps({k:result[k] for k in ('all12000_starts_individually_feasible_and_verified','maximum_absolute_reference_error','all_three_corrected_axis_paths_close_under_declared_gate')}))


if __name__=='__main__':main()
