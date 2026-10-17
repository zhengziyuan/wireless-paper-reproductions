"""Independently replay the actual saved1000-draw Python channel-moment stream.

Uses the recorded PCG64 state in a separate reference generator, reconstructs
the shared-r physical channel by elementwise contractions, checks all saved h,
and evaluates finite-Rician expected moments at MP80/MP100. This is configured
moment validation, not additional optimized-performance Monte Carlo data.
"""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import time

import mpmath as mp
import numpy as np

from audit_native_case import sha
from build_power_curve_views import read,require,write
import mp_phase_reference as ref


def canonical(value):
    return json.dumps(value,sort_keys=True,separators=(',',':'),default=lambda x:int(x))


def load_case(case_dir):
    paths=[case_dir/name for name in ('configuration.json','actual-result.json','actual-state.json','actual-state.npz')]
    before={p.name:sha(p) for p in paths}
    configuration,result,metadata=map(read,paths[:3])
    require(len(metadata['cases'])==1 and before['actual-state.npz']==metadata['actual_saved_array_bank_sha256'],
            'One actual original recording and its saved NumPy bank digest required')
    case=metadata['cases'][0];mc=result['results'][0]['monte_carlo']
    require(mc['count']==len(case['effective_channel_draws'])==1000,'All actual1000 recorded draws required')
    with np.load(paths[3],allow_pickle=False) as arrays:
        def decode(value):
            if isinstance(value,dict) and 'recorded_array' in value:
                a=arrays[value['recorded_array']]
                require(list(a.shape)==value['shape'] and a.dtype.str==value['dtype'],
                        'Actual saved array differs from its recorded descriptor')
                return a.copy()
            if isinstance(value,dict):return {k:decode(v) for k,v in value.items()}
            return value
        data=decode(case['data']);phi=decode(case['actual_MC_phi'])
        samples=np.stack([decode(x) for x in case['effective_channel_draws']])
    J,U,N,M=(int(configuration['reported'][k]) for k in ('J','U','N','M'))
    require(len(data)==11 and all(np.isfinite(a).all() for a in data.values()) and
            data['d_mean'].shape==(J,U,N) and phi.shape==(U,M) and samples.shape==(1000,J,U,N),
            'Every actual original physical dimension/array/draw required')
    require(np.max(abs(abs(phi)-1))<=1e-10,'Actual moment-check phase must retain its original circle domain')
    require(all(np.all(data[key]>=0) for key in ('d_var','G_var','r_var')),
            'Actual finite-Rician variances must remain nonnegative')
    require(case['actual_MC_rng_state_before']['bit_generator']=='PCG64',
            'Only the explicitly recorded Python PCG64 protocol is supported')
    signature=hashlib.sha256()
    for name,a in sorted(data.items()):
        signature.update(name.encode());signature.update(a.dtype.str.encode());signature.update(str(a.shape).encode());signature.update(a.tobytes(order='C'))
    signature.update(phi.dtype.str.encode());signature.update(str(phi.shape).encode());signature.update(phi.tobytes(order='C'))
    signature.update(canonical(case['actual_MC_rng_state_before']).encode())
    signature.update(canonical(dict(count=1000,sampler_source=result['executed_source_hashes'].get('models.py'))).encode())
    sample_hash=hashlib.sha256(samples.dtype.str.encode()+str(samples.shape).encode()+samples.tobytes(order='C')).hexdigest()
    return dict(case_dir=case_dir,paths=paths,source_SHA256=before,configuration=configuration,data=data,phi=phi,
        samples=samples,original_MC=mc,RNG_before=case['actual_MC_rng_state_before'],RNG_after=case['actual_MC_rng_state_after'],
        dimensions=(J,U,N,M),input_signature=signature.hexdigest(),actual_sample_bank_SHA256=sample_hash,
        recorded_sampler_source=result['executed_source_hashes'].get('models.py'))


def evaluate(loaded,output):
    require(not output.exists(),'Preserve a previous independent moment reference')
    started=time.perf_counter();data=loaded['data'];phi=loaded['phi'];samples=loaded['samples']
    J,U,N,M=loaded['dimensions']
    code_before={str(p):sha(p) for p in (Path(__file__),Path(ref.__file__))}
    bitgen=np.random.PCG64(0)
    bitgen.state=copy.deepcopy(loaded['RNG_before'])
    rng=np.random.Generator(bitgen)
    reconstructed=np.empty_like(samples)
    for draw in range(1000):
        for u in range(U):
            zr=(rng.standard_normal(M)+1j*rng.standard_normal(M))/np.sqrt(2.)
            surface=data['r_mean'][u]+np.sqrt(data['r_var'][u])*zr
            for j in range(J):
                zg=(rng.standard_normal((N,M))+1j*rng.standard_normal((N,M)))/np.sqrt(2.)
                zd=(rng.standard_normal(N)+1j*rng.standard_normal(N))/np.sqrt(2.)
                G=data['G_mean'][j,u]+np.sqrt(data['G_var'][j,u])*zg
                direct=data['d_mean'][j,u]+np.sqrt(data['d_var'][j,u])*zd
                # Independent elementwise contraction; never the producer's sampler.
                reconstructed[draw,j,u]=direct+np.sum(G*(phi[u]*surface)[None,:],axis=1)
    sample_errors=abs(samples-reconstructed)
    all_samples=bool(np.isfinite(samples).all() and np.all(sample_errors<=1e-9+1e-10*abs(reconstructed)))
    rng_pass=canonical(rng.bit_generator.state)==canonical(loaded['RNG_after'])
    powers=np.sum(abs(samples)**2,axis=3);fourth=powers*powers
    moments={}
    for digits in (80,100):
        with mp.workdps(digits):
            context=ref.FixedContext(data,phi,np.zeros((J,U)),1.,np.zeros(data['gt_second'].shape[1]),True)
            e2=[[ref.norm2(context.mean[j][u])+ref.tr(context.C[j][u]) for u in range(U)] for j in range(J)]
            e4=[[context.fourth(j,u,context.mean[j][u]) for u in range(U)] for j in range(J)]
            moments[str(digits)]=dict(second=[[mp.nstr(x,digits) for x in row] for row in e2],
                                     fourth=[[mp.nstr(x,digits) for x in row] for row in e4])
    with mp.workdps(110):
        gap=max(abs(mp.mpf(a)-mp.mpf(b)) for key in ('second','fourth')
            for x,y in zip(moments['80'][key],moments['100'][key]) for a,b in zip(x,y))
    expected2=np.asarray(moments['100']['second'],float);expected4=np.asarray(moments['100']['fourth'],float)
    require(np.all(expected2>0) and np.all(expected4>0),'Finite-Rician expected powers must stay positive')
    error2=float(np.max(abs(powers.mean(axis=0)-expected2)/expected2))
    error4=float(np.max(abs(fourth.mean(axis=0)-expected4)/expected4))
    original=loaded['original_MC']
    original_errors_pass=abs(error2-original['second_moment_max_relative_error'])<=1e-9 and abs(error4-original['fourth_moment_max_relative_error'])<=1e-9
    unchanged=(all(sha(p)==loaded['source_SHA256'][p.name] for p in loaded['paths']) and
        code_before=={str(Path(p)):sha(Path(p)) for p in code_before})
    checks=dict(all_actual1000_complex_received_channel_draws_match_independent_physics=all_samples,
        exact_recorded_PCG64_after_state_matches_independent_reference=rng_pass,
        expected_second_and_fourth_moments_MP80_MP100_stable=bool(gap<=mp.mpf('1e-40')),
        actual_original_reported_MC_relative_errors_reproduced=bool(original_errors_pass),
        source_recorded_inputs_and_math_unchanged=unchanged)
    report=dict(scope='Actual saved Python1000-draw moment stream: all h, exact recorded RNG states and independent finite-Rician moments',
        actual_original_case_folder=loaded['case_dir'].name,dimensions=dict(J=J,U=U,N=N,M=M),
        actual_original_draws=1000,complex_received_channel_coordinates=1000*J*U*N,
        actual_power_and_fourth_sample_values=2*1000*J*U,
        input_signature=loaded['input_signature'],actual_sample_bank_SHA256=loaded['actual_sample_bank_SHA256'],
        source_input_SHA256=loaded['source_SHA256'],recorded_sampler_source=loaded['recorded_sampler_source'],
        independent_auditor_and_reference_SHA256=code_before,checks=checks,
        all_independent_moment_stream_checks_pass=all(checks.values()),
        maximum_complex_sample_error=float(np.max(sample_errors)),
        second_moment_max_relative_error=error2,fourth_moment_max_relative_error=error4,
        independent_MP_expected_moments=moments,maximum_MP80_MP100_difference=mp.nstr(gap,105),
        recorded_RNG_before=loaded['RNG_before'],recorded_RNG_after=loaded['RNG_after'],
        actual_independent_reference_RNG_replay_realizations=1000,
        original_production_RNG_stream_or_array_files_modified=False,
        new_original_optimizer_or_production_evaluator_calls=0,new_optimized_performance_MC_populations=0,
        configured1000_count_is_author_reported_optimized_performance_MC=False,
        GEO_GT_sample_histories_or_original_reference_or_paper_pass=False,
        elapsed_seconds=time.perf_counter()-started)
    write(output,report)
    print(dict(actual_draws=1000,all_independent_moment_stream_checks_pass=report['all_independent_moment_stream_checks_pass'],
        maximum_complex_sample_error=report['maximum_complex_sample_error'],actual_reference_replay_realizations=1000),flush=True)
    return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--case-dir',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();report=evaluate(load_case(a.case_dir),a.output)
    if not report['all_independent_moment_stream_checks_pass']:raise SystemExit(1)
