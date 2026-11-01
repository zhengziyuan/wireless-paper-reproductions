"""All54000 stored native rate samples replayed from complete exported channels.

Only fixed saved designs are evaluated. No optimizer/reference ordinates are
called. Agreement validates these declared native RNG/sample returns, rather
than the unobserved author geometry or every old inner solver iterate.
"""
import argparse
import json
from pathlib import Path
import time
import numpy as np

from audit_saved_native import read,sha,decode,write


def unpack(row,entry):
    count=entry['complex_values_per_draw'];values=row[:count]+1j*row[count:]
    n=int(np.prod(entry['direct_shape']));m=int(np.prod(entry['cascade_shape']))
    return (values[:n].reshape(entry['direct_shape'],order='F'),
            values[n:n+m].reshape(entry['cascade_shape'],order='F'),
            values[n+m:].reshape(entry['nhu_shape'],order='F'))


def physical_draw(direct,cascade,nhu,phi,W,no_ris,noise):
    hu=direct.copy()
    if not no_ris:
        # Direct expansion by subpanel, independent of either producer helper.
        for m in range(cascade.shape[1]):hu+=phi[m]*cascade[:,m,:]
    received=abs(np.vstack([hu,nhu])@W)**2
    desired=np.diag(received)
    interference=received.copy();np.fill_diagonal(interference,0)
    sinr=desired/(interference.sum(axis=1)+noise)
    return float(np.log2(1+sinr[:len(hu)]).sum()),received


def audit(bank,channels,output):
    if output.exists():raise ValueError('Preserve previous replay; use a fresh directory')
    index=read(channels/'index.json');entries=index['cases']
    if len(entries)!=18 or {(r['U'],r['beta_db']) for r in entries}!={(u,b) for u in range(1,7) for b in (0,10,20)}:
        raise ValueError('All18 original cases required')
    output.mkdir(parents=True);cases=[];checked=0;begin=time.perf_counter()
    for entry in entries:
        path=channels/entry['file'];source=bank/entry['result_filename']
        if sha(source)!=entry['result_sha256'] or path.stat().st_size!=entry['bytes'] or sha(path)!=entry['sha256']:
            raise ValueError('Changed original result or replay input')
        raw=read(source);case=raw['cases'][0];U=entry['U'];noise=1.;states={}
        if entry['draws']!=1000 or entry['direct_shape']!=[U,16] or entry['cascade_shape']!=[U,25,16] or entry['nhu_shape']!=[16-U,16]:
            raise ValueError('Original full draw count/dimensions changed')
        for name in ('NoRIS','TwoStage','AO'):
            scheme=case['schemes'][name];starts=scheme['all_start_records']
            if [r['start_id'] for r in starts]!=list(range(U+1)):raise ValueError('Missing start ensemble')
            winner=max(starts,key=lambda r:(r['evaluation']['hu_sum_rate'],-r['start_id']))
            if winner['start_id']!=scheme['ensemble']['selected_start_id'] or winner['evaluation']!=scheme['evaluation']:
                raise ValueError('Selected fixed design does not match original winner')
            state=winner['final_state'];states[name]=(decode(state['phi']).reshape(-1),decode(state['W']),state['no_ris'])
        data=np.memmap(path,dtype='<f8',mode='r',shape=(1000,2*entry['complex_values_per_draw']))
        values={name:[] for name in states};powers={name:np.zeros((16,16)) for name in states}
        for draw in range(1000):
            direct,cascade,nhu=unpack(data[draw],entry)
            for name,(phi,W,no_ris) in states.items():
                rate,received=physical_draw(direct,cascade,nhu,phi,W,no_ris,noise)
                values[name].append(rate);powers[name]+=received;checked+=1
        records=[]
        for name in states:
            samples=np.asarray(values[name]);saved=case['schemes'][name]['independent_MC']
            original=np.asarray(saved['hu_rate_samples']).reshape(-1)
            if saved['count']!=1000 or len(original)!=1000:raise ValueError('Missing actual1000 original samples')
            maximum=float(np.max(abs(samples-original)));mean=float(samples.mean());se=float(samples.std(ddof=1)/np.sqrt(1000))
            received=powers[name]/1000;desired=np.diag(received);interference=received.copy();np.fill_diagonal(interference,0)
            ratio_rate=float(np.log2(1+desired[:U]/(interference.sum(axis=1)[:U]+noise)).sum())
            errors={'maximum_sample_error':maximum,'mean_error':abs(mean-saved['exact_ergodic_sum_rate_estimate']),
                    'standard_error_error':abs(se-saved['standard_error']),
                    'ratio_of_empirical_powers_rate_error':abs(ratio_rate-saved['ratio_of_empirical_expected_powers_sum_rate'])}
            passed=max(errors.values())<=1e-9
            records.append(dict(scheme=name,draws=1000,passed=passed,errors=errors,replayed_mean=mean,replayed_standard_error=se,
                                replayed_ratio_of_empirical_expected_powers_sum_rate=ratio_rate))
        case_result=dict(U=U,beta_db=entry['beta_db'],selected_design_evaluations=3000,schemes=records,
                         passed=all(r['passed'] for r in records))
        cases.append(case_result);write(output/f'U{U}-beta{entry["beta_db"]}.json',case_result)
        write(output/'progress.json',dict(cases_completed=len(cases),selected_design_evaluations=checked,failed_cases=sum(not c['passed'] for c in cases)))
        print(json.dumps({k:case_result[k] for k in ('U','beta_db','selected_design_evaluations','passed')}),flush=True)
        del data
    if checked!=54000:raise ValueError('Full original selected-design MC population missing')
    summary=dict(scope='all18_native_1000_paired_draws_and_all54000_saved_selected_design_rate_samples',cases_checked=18,
                 selected_design_evaluations=54000,failed_cases=sum(not c['passed'] for c in cases),
                 maximum_absolute_sample_error=max(r['errors']['maximum_sample_error'] for c in cases for r in c['schemes']),
                 maximum_mean_SE_empirical_ratio_error=max(max(r['errors'].values()) for c in cases for r in c['schemes']),
                 all_sample_replay_checks_passed=all(c['passed'] for c in cases),comparison_absolute_tolerance=1e-9,
                 optimizers_called=0,reference_ordinates_used=False,exact_ergodic_rate_not_relabelled_source_approximation=True,
                 original_historical_geometry_and_curves_certified=False,full_inner_trajectory_replay=False,full_reproduction_pass=False,
                 elapsed_seconds=time.perf_counter()-begin)
    write(output/'summary.json',summary);return summary


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--bank',type=Path,required=True)
    p.add_argument('--channels',type=Path,required=True);p.add_argument('--output-dir',type=Path,required=True)
    a=p.parse_args();s=audit(a.bank,a.channels,a.output_dir);print(json.dumps(s));raise SystemExit(0 if s['all_sample_replay_checks_passed'] else 1)
